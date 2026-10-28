import uuid
from datetime import datetime, timezone, timedelta
from app.database import get_db

def test_click_webhook_idempotency_and_ofd(client, test_db_path):
    """
    AC-04: Click bir xil to'lov webhookini bir necha marta yuborsa, idempotent ishlaydi.
    AC-15: Muvaffaqiyatli to'lovdan so'ng Soliq OFD elektron chek havolasi shakllanadi.
    """
    props = client.get("/api/v1/properties").json()
    unit_id = props[0]["rental_units"][0]["id"]

    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-10-01T14:00:00+05:00",
        "checkout_time": "2026-10-02T12:00:00+05:00",
        "guests_count": 2
    }).json()

    b = client.post("/api/v1/bookings/create", json={
        "quote_token": q["quote_token"],
        "guest_name": "Farhod",
        "guest_phone": "+998901119988"
    }).json()

    fee = b["platform_fee_amount"]
    click_trans = f"click_{uuid.uuid4().hex[:8]}"

    # Prepare (action 0)
    prep_res = client.post("/api/v1/payments/click/webhook", json={
        "click_trans_id": click_trans,
        "service_id": "19827",
        "merchant_trans_id": b["booking_reference"],
        "amount": fee,
        "action": 0,
        "sign_time": "2026-10-01 12:00:00",
        "error": 0
    })
    assert prep_res.status_code == 200
    assert prep_res.json()["error"] == 0

    # Complete (action 1) - First time
    comp1 = client.post("/api/v1/payments/click/webhook", json={
        "click_trans_id": click_trans,
        "service_id": "19827",
        "merchant_trans_id": b["booking_reference"],
        "amount": fee,
        "action": 1,
        "sign_time": "2026-10-01 12:00:00",
        "error": 0
    })
    assert comp1.status_code == 200
    data1 = comp1.json()
    assert data1["error"] == 0
    assert "fiscal_receipt_url" in data1
    assert "ofd.soliq.uz" in data1["fiscal_receipt_url"] # AC-15

    # Complete (action 1) - Second duplicate delivery (AC-04 Idempotency)
    comp2 = client.post("/api/v1/payments/click/webhook", json={
        "click_trans_id": click_trans,
        "service_id": "19827",
        "merchant_trans_id": b["booking_reference"],
        "amount": fee,
        "action": 1,
        "sign_time": "2026-10-01 12:00:00",
        "error": 0
    })
    assert comp2.status_code == 200
    assert comp2.json()["error"] == 0
    assert "Idempotent" in comp2.json()["error_note"]

def test_late_payment_conflict_auto_refund(client, test_db_path):
    """
    AC-06: To'lov hold muddati tugagandan so'ng kelsa va joy boshqa mehmonga o'tib ketgan bo'lsa:
    Tizim to'lovni CONFLICTED_EXPIRED deb belgilaydi va mijozga 100% pul avtomatik qaytariladi.
    """
    props = client.get("/api/v1/properties").json()
    unit_id = props[0]["rental_units"][0]["id"]
    checkin = "2026-10-15T14:00:00+05:00"
    checkout = "2026-10-17T12:00:00+05:00"

    # 1. Guest 1 books
    q1 = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": checkin,
        "checkout_time": checkout,
        "guests_count": 2
    }).json()

    b1 = client.post("/api/v1/bookings/create", json={
        "quote_token": q1["quote_token"],
        "guest_name": "Kechikkan Mehmon",
        "guest_phone": "+998901237777"
    }).json()

    # Guest 1 hold expires
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    with get_db(test_db_path) as conn:
        conn.execute("UPDATE inventory_allocations SET expires_at = ? WHERE booking_id = ?", (past_time, b1["id"]))
        conn.execute("UPDATE bookings SET hold_expires_at = ? WHERE id = ?", (past_time, b1["id"]))

    # 2. Guest 2 swoops in and takes the slot
    q2 = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": checkin,
        "checkout_time": checkout,
        "guests_count": 2
    }).json()

    b2 = client.post("/api/v1/bookings/create", json={
        "quote_token": q2["quote_token"],
        "guest_name": "Tezkor Mehmon",
        "guest_phone": "+998908886655"
    }).json()

    # Guest 2 confirms payment
    client.post("/api/v1/payments/simulate-success", json={"booking_id": b2["id"]})

    # 3. Guest 1's Click payment webhook arrives late!
    late_click_trans = f"late_{uuid.uuid4().hex[:8]}"
    late_res = client.post("/api/v1/payments/click/webhook", json={
        "click_trans_id": late_click_trans,
        "service_id": "19827",
        "merchant_trans_id": b1["booking_reference"],
        "amount": b1["platform_fee_amount"],
        "action": 1,
        "sign_time": "2026-10-15 12:00:00",
        "error": 0
    })
    assert late_res.status_code == 200
    late_data = late_res.json()
    assert late_data["error"] != 0
    assert late_data.get("auto_refund") is True # AC-06 Auto-refund initiated!

def test_payme_json_rpc_lifecycle(client, test_db_path):
    """
    Test Payme JSON-RPC 2.0 lifecycle:
    CheckPerformTransaction -> CreateTransaction -> PerformTransaction -> CancelTransaction.
    """
    props = client.get("/api/v1/properties").json()
    unit_id = props[0]["rental_units"][0]["id"]

    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-10-20T14:00:00+05:00",
        "checkout_time": "2026-10-22T12:00:00+05:00",
        "guests_count": 2
    }).json()

    b = client.post("/api/v1/bookings/create", json={
        "quote_token": q["quote_token"],
        "guest_name": "Payme Mehmoni",
        "guest_phone": "+998909990011"
    }).json()

    fee_tiyin = int(b["platform_fee_amount"] * 100)
    payme_trans_id = f"payme_tr_{uuid.uuid4().hex[:10]}"

    # 1. CheckPerformTransaction
    res1 = client.post("/api/v1/payments/payme/webhook", json={
        "method": "CheckPerformTransaction",
        "params": {
            "amount": fee_tiyin,
            "account": { "order_id": b["booking_reference"] }
        },
        "id": 101
    }).json()
    assert res1["result"]["allow"] is True

    # 2. CreateTransaction
    res2 = client.post("/api/v1/payments/payme/webhook", json={
        "method": "CreateTransaction",
        "params": {
            "id": payme_trans_id,
            "time": 1700000000000,
            "amount": fee_tiyin,
            "account": { "order_id": b["booking_reference"] }
        },
        "id": 102
    }).json()
    assert res2["result"]["state"] == 1

    # 3. PerformTransaction
    res3 = client.post("/api/v1/payments/payme/webhook", json={
        "method": "PerformTransaction",
        "params": { "id": payme_trans_id },
        "id": 103
    }).json()
    assert res3["result"]["state"] == 2

    # Check booking is CONFIRMED
    detail = client.get(f"/api/v1/bookings/{b['id']}").json()
    assert detail["booking_status"] == "CONFIRMED"

    # 4. CancelTransaction
    res4 = client.post("/api/v1/payments/payme/webhook", json={
        "method": "CancelTransaction",
        "params": { "id": payme_trans_id, "reason": 1 },
        "id": 104
    }).json()
    assert res4["result"]["state"] == -2

    # Check booking is CANCELLED
    detail_cancelled = client.get(f"/api/v1/bookings/{b['id']}").json()
    assert detail_cancelled["booking_status"] == "CANCELLED"
