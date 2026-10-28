import uuid
import random
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException

from app.config import settings
from app.database import get_db, _db_lock
from app.models import BookingCreateRequest, BookingResponse, BookingDetailResponse
from app.security import verify_quote_token

UZ_TZ = timezone(timedelta(hours=5))

def normalize_datetime_input(dt_str: str) -> datetime:
    """
    Parses ISO8601 string, treating naive times as Uzbekistan local time (UTC+5),
    returning timezone-aware datetime.
    """
    cleaned = dt_str.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UZ_TZ)
    return dt

def normalize_to_utc_iso(dt_str: str) -> str:
    """
    Normalizes any datetime representation (aware or naive) into canonical UTC ISO format
    YYYY-MM-DDTHH:MM:SSZ so that lexicographical string comparison in SQLite is identical
    to chronological comparison.
    """
    dt = normalize_datetime_input(dt_str)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def generate_booking_reference() -> str:
    year = datetime.now(timezone.utc).year
    rand_digits = random.randint(1000, 9999)
    return f"ZS-{year}-{rand_digits}"

def lazy_invalidate_expired_holds(conn, rental_unit_id: Optional[str] = None):
    """
    Lazy Invalidation (TZ 3.2 & AC-05):
    Muddati o'tgan PLATFORM_HOLD larni avtomatik EXPIRED holatiga o'tkazadi.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    cursor = conn.cursor()
    
    query = """
        UPDATE inventory_allocations
        SET status = 'EXPIRED'
        WHERE status = 'ACTIVE' 
          AND allocation_type = 'PLATFORM_HOLD' 
          AND expires_at IS NOT NULL 
          AND expires_at < ?
    """
    params = [now_iso]
    if rental_unit_id:
        query += " AND rental_unit_id = ?"
        params.append(rental_unit_id)
        
    cursor.execute(query, params)
    
    # Also update corresponding bookings if they were in PENDING_OWNER or AWAITING_PAYMENT
    cursor.execute("""
        UPDATE bookings
        SET booking_status = 'EXPIRED'
        WHERE booking_status IN ('PENDING_OWNER', 'AWAITING_PAYMENT')
          AND hold_expires_at IS NOT NULL
          AND hold_expires_at < ?
    """, (now_iso,))

def check_overlapping_allocation(conn, rental_unit_id: str, start_time: str, end_time: str, exclude_booking_id: Optional[str] = None) -> bool:
    """
    Checks if there is an overlapping ACTIVE allocation for this unit.
    Normalizes both bounds to UTC ISO strings for deterministic comparison.
    Two intervals [s1, e1) and [s2, e2) overlap if s1 < e2 AND s2 < e1.
    """
    start_utc = normalize_to_utc_iso(start_time)
    end_utc = normalize_to_utc_iso(end_time)
    
    cursor = conn.cursor()
    query = """
        SELECT COUNT(*) FROM inventory_allocations
        WHERE rental_unit_id = ?
          AND status = 'ACTIVE'
          AND start_time < ?
          AND end_time > ?
    """
    params = [rental_unit_id, end_utc, start_utc]
    if exclude_booking_id:
        query += " AND (booking_id != ? OR booking_id IS NULL)"
        params.append(exclude_booking_id)
        
    cursor.execute(query, params)
    return cursor.fetchone()[0] > 0

def create_booking(request: BookingCreateRequest, idempotency_key: Optional[str] = None, db_path: Optional[str] = None) -> BookingResponse:
    # 1. Verify Quote Token (AC-03: snapshot daxlsiz)
    payload = verify_quote_token(request.quote_token)
    if not payload:
        raise HTTPException(status_code=400, detail="Kotirovka tokeni yaroqsiz yoki muddati tugagan")

    unit_id = payload["rental_unit_id"]
    checkin_time = payload["checkin_time"]
    checkout_time = payload["checkout_time"]
    guests_count = payload.get("guests_count", 2)
    booking_type = payload.get("booking_type", "OVERNIGHT")
    grand_total = payload["grand_total"]
    platform_fee = payload["platform_fee_online"]
    payable_on_arrival = payload["payable_on_arrival"]
    accommodation_total = payload["accommodation_total"]
    tandir_preorder_kg = float(payload.get("tandir_preorder_kg", 0.0))
    tandir_meat_total = float(payload.get("tandir_meat_total", 0.0))

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    hold_expires_at = (now + timedelta(minutes=settings.HOLD_DURATION_MINUTES)).isoformat()

    with get_db(db_path) as conn:
        cursor = conn.cursor()

        # Idempotency check if idempotency_key provided
        if idempotency_key:
            cursor.execute("SELECT provider_payload FROM payment_attempts WHERE idempotency_key = ?", (idempotency_key,))
            existing = cursor.fetchone()
            if existing and existing["provider_payload"]:
                import json
                saved_booking = json.loads(existing["provider_payload"])
                return BookingResponse(**saved_booking)

        # 2. Lazy cleanup of expired holds (AC-05)
        lazy_invalidate_expired_holds(conn, rental_unit_id=unit_id)

        # 3. Double-Booking Concurrency Check (AC-01, AC-02)
        if check_overlapping_allocation(conn, unit_id, checkin_time, checkout_time):
            raise HTTPException(
                status_code=409,
                detail="Ushbu sana va vaqt oralig'i allaqachon boshqa mehmon tomonidan band qilingan yoki to'lov kutilmoqda (Double-booking himoyasi)"
            )

        # 4. Find or create guest user
        cursor.execute("SELECT id FROM users WHERE phone_number = ?", (request.guest_phone,))
        user_row = cursor.fetchone()
        if user_row:
            guest_id = user_row["id"]
        else:
            guest_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, phone_number, full_name, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 'GUEST', 1, ?, ?)
            """, (guest_id, request.guest_phone, request.guest_name, now_iso, now_iso))

        # 5. Create Booking
        booking_id = str(uuid.uuid4())
        booking_ref = generate_booking_reference()

        cursor.execute("""
            INSERT INTO bookings (
                id, booking_reference, rental_unit_id, guest_id, guest_name, guest_phone, car_plate,
                booking_type, checkin_time, checkout_time, guest_count, currency,
                unit_base_amount, platform_fee_amount, pay_on_arrival_amount, total_amount,
                booking_status, hold_expires_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'UZS', ?, ?, ?, ?, 'PENDING_OWNER', ?, ?, ?)
        """, (
            booking_id, booking_ref, unit_id, guest_id, request.guest_name, request.guest_phone,
            request.car_plate or "Mavjud emas", booking_type, checkin_time, checkout_time,
            guests_count, accommodation_total, platform_fee, payable_on_arrival, grand_total,
            hold_expires_at, now_iso, now_iso
        ))

        # 6. Create Active Inventory Allocation (Hold with DB engine exclusion constraint)
        allocation_id = str(uuid.uuid4())
        start_utc = normalize_to_utc_iso(checkin_time)
        end_utc = normalize_to_utc_iso(checkout_time)
        try:
            cursor.execute("""
                INSERT INTO inventory_allocations (
                    id, rental_unit_id, booking_id, allocation_type, start_time, end_time,
                    status, expires_at, created_at
                ) VALUES (?, ?, ?, 'PLATFORM_HOLD', ?, ?, 'ACTIVE', ?, ?)
            """, (
                allocation_id, unit_id, booking_id, start_utc, end_utc,
                hold_expires_at, now_iso
            ))
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail="Ushbu sana va vaqt oralig'i allaqachon boshqa mehmon tomonidan band qilingan yoki to'lov kutilmoqda (Double-booking himoyasi)"
            )

        # 7. Pre-order Tandir meat if requested (AC-12)
        if tandir_preorder_kg > 0:
            food_order_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO booking_food_orders (
                    id, booking_id, dish_name, quantity_kg, target_serving_time,
                    price_per_kg, total_food_amount, special_notes
                ) VALUES (?, ?, 'Zomin Archa Tandiri', ?, ?, ?, ?, ?)
            """, (
                food_order_id, booking_id, tandir_preorder_kg, checkin_time,
                settings.TANDIR_PRICE_PER_KG, tandir_meat_total, request.special_notes or ""
            ))

        response = BookingResponse(
            id=booking_id,
            booking_reference=booking_ref,
            status="PENDING_OWNER",
            hold_expires_at=hold_expires_at,
            total_amount=grand_total,
            platform_fee_amount=platform_fee,
            pay_on_arrival_amount=payable_on_arrival,
            message="Bron dacha egasiga tasdiqlash uchun yuborildi. 15 daqiqa ichida javob beriladi."
        )

        if idempotency_key:
            import json
            cursor.execute("""
                INSERT INTO payment_attempts (
                    id, booking_id, provider, amount_in_tiyin, amount_uzs, status,
                    idempotency_key, provider_payload, created_at, updated_at
                ) VALUES (?, ?, 'CLICK', ?, ?, 'INITIATED', ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), booking_id, int(platform_fee * 100), platform_fee,
                idempotency_key, json.dumps(response.model_dump()), now_iso, now_iso
            ))

        return response

def get_booking_detail(booking_id_or_ref: str, current_user_role: str = "GUEST", db_path: Optional[str] = None) -> BookingDetailResponse:
    with get_db(db_path) as conn:
        lazy_invalidate_expired_holds(conn)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.*, u.name as unit_name, p.id as property_id, p.title as property_title,
                   p.micro_district, p.property_type,
                   f.quantity_kg as tandir_kg, f.total_food_amount as tandir_amount,
                   pay.fiscal_receipt_url
            FROM bookings b
            JOIN rental_units u ON b.rental_unit_id = u.id
            JOIN properties p ON u.property_id = p.id
            LEFT JOIN booking_food_orders f ON b.id = f.booking_id
            LEFT JOIN payment_attempts pay ON b.id = pay.booking_id AND pay.status = 'SUCCESS'
            WHERE b.id = ? OR b.booking_reference = ?
        """, (booking_id_or_ref, booking_id_or_ref))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Bron topilmadi")

        # AC-14: Caretaker sees guest name, phone, arrival date, car plate, but NOT financial info!
        is_caretaker = (current_user_role == "CARETAKER")

        return BookingDetailResponse(
            id=row["id"],
            booking_reference=row["booking_reference"],
            rental_unit_id=row["rental_unit_id"],
            unit_name=row["unit_name"],
            property_id=row["property_id"],
            property_title=row["property_title"],
            micro_district=row["micro_district"],
            property_type=row["property_type"],
            guest_id=row["guest_id"],
            guest_name=row["guest_name"],
            guest_phone=row["guest_phone"],
            car_plate=row["car_plate"],
            booking_type=row["booking_type"],
            checkin_time=row["checkin_time"],
            checkout_time=row["checkout_time"],
            guest_count=row["guest_count"],
            currency=row["currency"],
            unit_base_amount=None if is_caretaker else row["unit_base_amount"],
            platform_fee_amount=None if is_caretaker else row["platform_fee_amount"],
            pay_on_arrival_amount=None if is_caretaker else row["pay_on_arrival_amount"],
            total_amount=None if is_caretaker else row["total_amount"],
            booking_status=row["booking_status"],
            hold_expires_at=row["hold_expires_at"],
            cancellation_reason=row["cancellation_reason"],
            created_at=row["created_at"],
            tandir_preorder_kg=float(row["tandir_kg"] or 0.0),
            tandir_amount=0.0 if is_caretaker else float(row["tandir_amount"] or 0.0),
            fiscal_receipt_url=row["fiscal_receipt_url"]
        )

def owner_transition_booking(booking_id: str, action: str, owner_id: str, rejection_reason: Optional[str] = None, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Owner accept or reject action with BOLA check (AC-07) and FSM transitions.
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        # Verify ownership (BOLA protection)
        cursor.execute("""
            SELECT b.*, p.owner_id 
            FROM bookings b
            JOIN rental_units u ON b.rental_unit_id = u.id
            JOIN properties p ON u.property_id = p.id
            WHERE b.id = ?
        """, (booking_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Bron topilmadi")

        if row["owner_id"] != owner_id:
            raise HTTPException(status_code=403, detail="BOLA cheklovi: Siz ushbu dacha egasi emassiz")

        current_status = row["booking_status"]

        if action == "ACCEPT":
            if current_status != "PENDING_OWNER":
                raise HTTPException(status_code=400, detail=f"Bronni bu holatda qabul qilib bo'lmaydi: {current_status}")
            
            # Extend hold for 15 minutes to allow payment
            new_hold_expires = (now + timedelta(minutes=settings.HOLD_DURATION_MINUTES)).isoformat()
            
            cursor.execute("""
                UPDATE bookings 
                SET booking_status = 'AWAITING_PAYMENT', hold_expires_at = ?, updated_at = ?
                WHERE id = ?
            """, (new_hold_expires, now_iso, booking_id))
            
            cursor.execute("""
                UPDATE inventory_allocations
                SET expires_at = ?
                WHERE booking_id = ? AND status = 'ACTIVE'
            """, (new_hold_expires, booking_id))
            
            return {"status": "AWAITING_PAYMENT", "message": "Bron tasdiqlandi. Mehmon to'lovini kutish rejimi faollashdi."}

        elif action == "REJECT":
            if current_status not in ("PENDING_OWNER", "AWAITING_PAYMENT"):
                raise HTTPException(status_code=400, detail="Faqat kutilayotgan bronlarni rad etish mumkin")

            cursor.execute("""
                UPDATE bookings 
                SET booking_status = 'DECLINED', cancellation_reason = ?, updated_at = ?
                WHERE id = ?
            """, (rejection_reason or "Ega tomonidan rad etildi", now_iso, booking_id))

            cursor.execute("""
                UPDATE inventory_allocations
                SET status = 'CANCELLED'
                WHERE booking_id = ?
            """, (booking_id,))

            return {"status": "DECLINED", "message": "Bron rad etildi va kalendar bo'shatildi."}
            
        else:
            raise HTTPException(status_code=400, detail="Noma'lum amal")

def check_in_guest(booking_id: str, user_id: str, user_role: str = "CARETAKER", db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    AC-14: Caretaker or Owner marks guest arrival / handover key.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        # Resolve user
        cursor.execute("SELECT * FROM users WHERE id = ? OR telegram_id = ? OR phone_number = ?", (user_id, user_id, user_id))
        user_row = cursor.fetchone()
        actual_user_id = user_row["id"] if user_row else user_id
        effective_role = user_row["role"] if user_row else user_role

        cursor.execute("""
            SELECT b.*, p.owner_id, p.id as property_id
            FROM bookings b
            JOIN rental_units u ON b.rental_unit_id = u.id
            JOIN properties p ON u.property_id = p.id
            WHERE b.id = ?
        """, (booking_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Bron topilmadi")

        # Verify role: either owner of property, or assigned caretaker
        is_owner = (row["owner_id"] == actual_user_id)
        is_caretaker = False
        
        cursor.execute("""
            SELECT 1 FROM property_caretakers 
            WHERE property_id = ? AND caretaker_id = ?
        """, (row["property_id"], actual_user_id))
        if cursor.fetchone():
            is_caretaker = True

        if not (is_owner or is_caretaker or effective_role in ("ADMIN", "MODERATOR")):
            raise HTTPException(status_code=403, detail="Sizda mehmonni kutib olish va kalit topshirish huquqi yo'q")

        if row["booking_status"] != "CONFIRMED":
            raise HTTPException(status_code=400, detail=f"Faqat tasdiqlangan (CONFIRMED) bronlar kutib olinishi mumkin. Joriy holat: {row['booking_status']}")

        cursor.execute("""
            UPDATE bookings
            SET booking_status = 'CHECKED_IN', updated_at = ?
            WHERE id = ?
        """, (now_iso, booking_id))

        return {"status": "CHECKED_IN", "message": "Kalit topshirildi, mehmon kutib olindi!"}

def complete_booking(booking_id: str, user_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Completes stay after guest leaves. Enables reviews (AC-16).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Bron topilmadi")

        if row["booking_status"] not in ("CONFIRMED", "CHECKED_IN"):
            raise HTTPException(status_code=400, detail="Faqat tasdiqlangan yoki kirgan safarlarni yakunlash mumkin")

        cursor.execute("""
            UPDATE bookings
            SET booking_status = 'COMPLETED', updated_at = ?
            WHERE id = ?
        """, (now_iso, booking_id))

        return {"status": "COMPLETED", "message": "Safar muvaffaqiyatli yakunlandi. Endi sharh qoldirish mumkin."}
