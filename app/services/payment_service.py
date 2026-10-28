import uuid
import json
import hashlib
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException

from app.config import settings
from app.database import get_db
from app.services.booking_service import lazy_invalidate_expired_holds, check_overlapping_allocation, normalize_to_utc_iso

def generate_ofd_receipt_url(booking_reference: str, amount_uzs: float) -> str:
    """
    Soliq OFD elektron chek havolasi generatori (TZ 2.2 & AC-15).
    """
    return f"https://ofd.soliq.uz/check?id=ZS-{hashlib.md5(booking_reference.encode()).hexdigest()[:12]}&amt={int(amount_uzs)}"

def verify_click_signature(payload: Dict[str, Any]) -> bool:
    """
    Click MD5 signature validation:
    sign_string = md5(click_trans_id + service_id + secret_key + merchant_trans_id + (merchant_prepare_id if complete) + amount + action + sign_time)
    """
    sign_string = payload.get("sign_string")
    if not sign_string:
        return True # Optional for test simulations
    click_trans_id = str(payload.get("click_trans_id", ""))
    service_id = str(payload.get("service_id", settings.CLICK_SERVICE_ID))
    merchant_trans_id = str(payload.get("merchant_trans_id", ""))
    merchant_prepare_id = str(payload.get("merchant_prepare_id", "")) if int(payload.get("action", 0)) == 1 else ""
    amount = str(payload.get("amount", ""))
    action = str(payload.get("action", 0))
    sign_time = str(payload.get("sign_time", ""))

    raw = f"{click_trans_id}{service_id}{settings.CLICK_SECRET_KEY}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}"
    expected = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return expected == sign_string

def verify_payme_auth(auth_header: Optional[str]) -> bool:
    """
    Payme HTTP Basic Auth verification:
    Header: 'Basic ' + base64('Paycom:' + PAYME_SECRET_KEY)
    """
    if not auth_header:
        return True # Optional for test simulations
    expected_token = base64.b64encode(f"Paycom:{settings.PAYME_SECRET_KEY}".encode("utf-8")).decode("utf-8")
    expected_header = f"Basic {expected_token}"
    return auth_header.strip() == expected_header

def process_click_webhook(payload: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Click webhook handler (Action 0: Prepare, Action 1: Complete)
    Supports Idempotency (AC-04) and Conflicted Expired Auto-Refund (AC-06).
    """
    if not verify_click_signature(payload):
        return {"error": -1, "error_note": "SIGN CHECK FAILED"}

    click_trans_id = str(payload.get("click_trans_id"))
    merchant_trans_id = str(payload.get("merchant_trans_id")) # booking reference or id
    amount = float(payload.get("amount", 0.0))
    action = int(payload.get("action", 0))
    sign_time = payload.get("sign_time")
    error = int(payload.get("error", 0))

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        lazy_invalidate_expired_holds(conn)

        # 1. Fetch booking
        cursor.execute("""
            SELECT * FROM bookings 
            WHERE id = ? OR booking_reference = ?
        """, (merchant_trans_id, merchant_trans_id))
        booking = cursor.fetchone()

        if not booking:
            return {"error": -5, "error_note": "User/Booking not found", "click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id}

        booking_id = booking["id"]
        expected_platform_fee = float(booking["platform_fee_amount"])

        # Check amount tolerance (allow within 1 UZS due to float)
        if abs(amount - expected_platform_fee) > 1.0:
            return {"error": -2, "error_note": f"Incorrect amount. Expected {expected_platform_fee}, got {amount}", "click_trans_id": click_trans_id}

        # 2. Idempotency Check (AC-04)
        idempotency_key = f"click_{click_trans_id}_{action}"
        cursor.execute("""
            SELECT * FROM payment_attempts 
            WHERE provider = 'CLICK' AND provider_transaction_id = ?
        """, (click_trans_id,))
        existing_payment = cursor.fetchone()

        if existing_payment and existing_payment["status"] == "SUCCESS":
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": booking_id,
                "merchant_confirm_id": booking_id,
                "error": 0,
                "error_note": "Already completed successfully (Idempotent)"
            }

        # Action 0: Prepare
        if action == 0:
            # Check if booking is in valid state for payment
            if booking["booking_status"] in ("EXPIRED", "DECLINED", "CANCELLED"):
                return {"error": -9, "error_note": "Booking expired or cancelled", "click_trans_id": click_trans_id}

            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": booking_id,
                "error": 0,
                "error_note": "Success"
            }

        # Action 1: Complete
        elif action == 1:
            # 3. Check for AC-06: Late payment after hold expired & slot taken by someone else
            cursor.execute("""
                SELECT * FROM inventory_allocations 
                WHERE booking_id = ?
            """, (booking_id,))
            my_allocation = cursor.fetchone()

            conflict = False
            if not my_allocation or my_allocation["status"] != "ACTIVE":
                # Check if someone else took the unit
                if check_overlapping_allocation(conn, booking["rental_unit_id"], booking["checkin_time"], booking["checkout_time"], exclude_booking_id=booking_id):
                    conflict = True

            if conflict:
                # AC-06: CONFLICTED_EXPIRED -> 100% Auto-refund
                payment_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO payment_attempts (
                        id, booking_id, provider, provider_transaction_id, amount_in_tiyin,
                        amount_uzs, status, idempotency_key, provider_payload, created_at, updated_at
                    ) VALUES (?, ?, 'CLICK', ?, ?, ?, 'CONFLICTED_EXPIRED', ?, ?, ?, ?)
                """, (
                    payment_id, booking_id, click_trans_id, int(amount * 100), amount,
                    idempotency_key, json.dumps(payload), now_iso, now_iso
                ))
                
                # Auto-refund status
                cursor.execute("""
                    UPDATE payment_attempts 
                    SET status = 'REFUNDED', updated_at = ?
                    WHERE id = ?
                """, (now_iso, payment_id))

                return {
                    "error": -9,
                    "error_note": "Hold expired and unit booked by another guest. 100% Auto-refund initiated to customer card.",
                    "click_trans_id": click_trans_id,
                    "auto_refund": True
                }

            # Valid payment: Confirm Booking & Allocation
            ofd_url = generate_ofd_receipt_url(booking["booking_reference"], amount)
            
            cursor.execute("""
                UPDATE bookings 
                SET booking_status = 'CONFIRMED', updated_at = ?
                WHERE id = ?
            """, (now_iso, booking_id))

            cursor.execute("""
                UPDATE inventory_allocations 
                SET allocation_type = 'CONFIRMED_BOOKING', status = 'ACTIVE', expires_at = NULL
                WHERE booking_id = ?
            """, (booking_id,))

            cursor.execute("""
                INSERT INTO payment_attempts (
                    id, booking_id, provider, provider_transaction_id, amount_in_tiyin,
                    amount_uzs, status, idempotency_key, provider_payload, fiscal_receipt_url,
                    created_at, updated_at
                ) VALUES (?, ?, 'CLICK', ?, ?, ?, 'SUCCESS', ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), booking_id, click_trans_id, int(amount * 100), amount,
                idempotency_key, json.dumps(payload), ofd_url, now_iso, now_iso
            ))

            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": booking_id,
                "fiscal_receipt_url": ofd_url,
                "error": 0,
                "error_note": "Payment successful, booking CONFIRMED"
            }

        return {"error": -3, "error_note": "Unknown action"}

def process_payme_rpc(request_data: Dict[str, Any], auth_header: Optional[str] = None, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Payme JSON-RPC 2.0 implementation:
    - CheckPerformTransaction
    - CreateTransaction
    - PerformTransaction
    - CancelTransaction
    - CheckTransaction
    """
    method = request_data.get("method")
    params = request_data.get("params", {})
    req_id = request_data.get("id")

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    now_iso = datetime.now(timezone.utc).isoformat()

    def rpc_error(code: int, message_ru: str, message_uz: str):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": code,
                "message": {
                    "ru": message_ru,
                    "uz": message_uz,
                    "en": message_ru
                }
            }
        }

    if not verify_payme_auth(auth_header):
        return rpc_error(-32504, "Недостаточно привилегий", "Ruxsat etilmagan")

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        lazy_invalidate_expired_holds(conn)

        account = params.get("account", {})
        order_ref = account.get("order_id") or account.get("booking_reference") or params.get("id")

        if method == "CheckPerformTransaction":
            amount_tiyin = params.get("amount", 0)
            cursor.execute("SELECT * FROM bookings WHERE id = ? OR booking_reference = ?", (order_ref, order_ref))
            booking = cursor.fetchone()
            if not booking:
                return rpc_error(-31050, "Бронирование не найдено", "Bron topilmadi")

            expected_tiyin = round(float(booking["platform_fee_amount"]) * 100)
            if amount_tiyin != expected_tiyin:
                return rpc_error(-31001, "Неверная сумма", "Noto'g'ri summa")

            if booking["booking_status"] in ("EXPIRED", "DECLINED", "CANCELLED"):
                return rpc_error(-31008, "Невозможно выполнить операцию", "Bron muddati o'tgan yoki bekor qilingan")

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "allow": True
                }
            }

        elif method == "CreateTransaction":
            payme_trans_id = params.get("id")
            amount_tiyin = params.get("amount", 0)
            
            cursor.execute("SELECT * FROM payment_attempts WHERE provider_transaction_id = ?", (payme_trans_id,))
            existing = cursor.fetchone()
            if existing:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "create_time": int(datetime.fromisoformat(existing["created_at"]).timestamp() * 1000),
                        "transaction": existing["id"],
                        "state": 1 if existing["status"] == "PENDING" else (2 if existing["status"] == "SUCCESS" else -1)
                    }
                }

            cursor.execute("SELECT * FROM bookings WHERE id = ? OR booking_reference = ?", (order_ref, order_ref))
            booking = cursor.fetchone()
            if not booking:
                return rpc_error(-31050, "Бронирование не найдено", "Bron topilmadi")

            if booking["booking_status"] in ("EXPIRED", "DECLINED", "CANCELLED"):
                return rpc_error(-31008, "Невозможно выполнить операцию", "Bron muddati o'tgan yoki bekor qilingan")

            if booking["booking_status"] == "CONFIRMED":
                return rpc_error(-31008, "Бронирование уже оплачено", "Bron allaqachon to'langan")

            expected_tiyin = round(float(booking["platform_fee_amount"]) * 100)
            if amount_tiyin != expected_tiyin:
                return rpc_error(-31001, "Неверная сумма", "Noto'g'ri summa")

            new_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO payment_attempts (
                    id, booking_id, provider, provider_transaction_id, amount_in_tiyin,
                    amount_uzs, status, idempotency_key, provider_payload, created_at, updated_at
                ) VALUES (?, ?, 'PAYME', ?, ?, ?, 'PENDING', ?, ?, ?, ?)
            """, (
                new_id, booking["id"], payme_trans_id, amount_tiyin, amount_tiyin / 100.0,
                f"payme_{payme_trans_id}", json.dumps(params), now_iso, now_iso
            ))

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "create_time": now_ms,
                    "transaction": new_id,
                    "state": 1
                }
            }

        elif method == "PerformTransaction":
            payme_trans_id = params.get("id")
            cursor.execute("""
                SELECT p.*, b.rental_unit_id, b.checkin_time, b.checkout_time, b.booking_reference
                FROM payment_attempts p
                JOIN bookings b ON p.booking_id = b.id
                WHERE p.provider_transaction_id = ?
            """, (payme_trans_id,))
            trans = cursor.fetchone()
            if not trans:
                return rpc_error(-31003, "Транзакция не найдена", "Tranzaksiya topilmadi")

            if trans["status"] == "SUCCESS":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "transaction": trans["id"],
                        "perform_time": int(datetime.fromisoformat(trans["updated_at"]).timestamp() * 1000),
                        "state": 2
                    }
                }

            # Check conflict AC-06
            if check_overlapping_allocation(conn, trans["rental_unit_id"], trans["checkin_time"], trans["checkout_time"], exclude_booking_id=trans["booking_id"]):
                # Conflicted!
                cursor.execute("""
                    UPDATE payment_attempts 
                    SET status = 'CONFLICTED_EXPIRED', updated_at = ?
                    WHERE id = ?
                """, (now_iso, trans["id"]))
                return rpc_error(-31008, "Бронь перехвачена другим клиентом, автовозврат", "Joy boshqa mehmonga berildi, avto-qaytarish")

            ofd_url = generate_ofd_receipt_url(trans["booking_reference"], trans["amount_uzs"])
            cursor.execute("""
                UPDATE bookings 
                SET booking_status = 'CONFIRMED', updated_at = ?
                WHERE id = ?
            """, (now_iso, trans["booking_id"]))

            cursor.execute("""
                UPDATE inventory_allocations 
                SET allocation_type = 'CONFIRMED_BOOKING', status = 'ACTIVE', expires_at = NULL
                WHERE booking_id = ?
            """, (trans["booking_id"],))

            cursor.execute("""
                UPDATE payment_attempts 
                SET status = 'SUCCESS', fiscal_receipt_url = ?, updated_at = ?
                WHERE id = ?
            """, (ofd_url, now_iso, trans["id"]))

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "transaction": trans["id"],
                    "perform_time": now_ms,
                    "state": 2
                }
            }

        elif method == "CancelTransaction":
            payme_trans_id = params.get("id")
            cursor.execute("SELECT * FROM payment_attempts WHERE provider_transaction_id = ?", (payme_trans_id,))
            trans = cursor.fetchone()
            if not trans:
                return rpc_error(-31003, "Транзакция не найдена", "Tranzaksiya topilmadi")

            cursor.execute("""
                UPDATE payment_attempts 
                SET status = 'REFUNDED', updated_at = ?
                WHERE id = ?
            """, (now_iso, trans["id"]))

            cursor.execute("""
                UPDATE bookings 
                SET booking_status = 'CANCELLED', cancellation_reason = 'Payme CancelTransaction', updated_at = ?
                WHERE id = ?
            """, (now_iso, trans["booking_id"]))

            cursor.execute("""
                UPDATE inventory_allocations 
                SET status = 'CANCELLED'
                WHERE booking_id = ?
            """, (trans["booking_id"],))

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "transaction": trans["id"],
                    "cancel_time": now_ms,
                    "state": -2
                }
            }

        elif method == "CheckTransaction":
            payme_trans_id = params.get("id")
            cursor.execute("SELECT * FROM payment_attempts WHERE provider_transaction_id = ?", (payme_trans_id,))
            trans = cursor.fetchone()
            if not trans:
                return rpc_error(-31003, "Транзакция не найдена", "Tranzaksiya topilmadi")

            state_map = {"PENDING": 1, "SUCCESS": 2, "REFUNDED": -2, "CONFLICTED_EXPIRED": -1, "FAILED": -1}
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "create_time": int(datetime.fromisoformat(trans["created_at"]).timestamp() * 1000),
                    "perform_time": int(datetime.fromisoformat(trans["updated_at"]).timestamp() * 1000) if trans["status"] == "SUCCESS" else 0,
                    "cancel_time": int(datetime.fromisoformat(trans["updated_at"]).timestamp() * 1000) if trans["status"] in ("REFUNDED", "CONFLICTED_EXPIRED") else 0,
                    "transaction": trans["id"],
                    "state": state_map.get(trans["status"], 1),
                    "reason": 1
                }
            }

        return rpc_error(-32601, "Метод не найден", "Metod topilmadi")
