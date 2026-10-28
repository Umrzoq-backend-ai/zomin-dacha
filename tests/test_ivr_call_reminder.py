from datetime import datetime, timezone, timedelta
from app.database import get_db

def test_ivr_call_reminder_lifecycle(client, test_db_path):
    """
    AC-10: Dacha egasi yangi bronga 10 daqiqa javob bermasa:
    IVR ovozli robot egaga telefon qilib botni tekshirishni eslatadi.
    """
    props = client.get("/api/v1/properties").json()
    unit = props[0]["rental_units"][0]
    unit_id = unit["id"]
    owner_id = props[0]["owner_id"]

    # 1. Create a booking
    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-11-20T14:00:00+05:00",
        "checkout_time": "2026-11-22T12:00:00+05:00",
        "guests_count": 2
    }).json()

    b = client.post("/api/v1/bookings/create", json={
        "quote_token": q["quote_token"],
        "guest_name": "Sayyoh IVR Test",
        "guest_phone": "+998909876543"
    }).json()

    booking_id = b["id"]
    assert b["status"] == "PENDING_OWNER"

    # Check right now: 0 minutes passed -> delay_minutes=10 should NOT trigger call
    res_early = client.post("/api/v1/owner/ivr-check?delay_minutes=10")
    assert res_early.status_code == 200
    assert res_early.json()["dispatched_count"] == 0

    # 2. Simulate 12 minutes elapsed since booking creation
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=12)).isoformat()
    with get_db(test_db_path) as conn:
        conn.execute("UPDATE bookings SET created_at = ? WHERE id = ?", (past_time, booking_id))

    # Now run IVR check with delay_minutes=10: should trigger call!
    res_due = client.post("/api/v1/owner/ivr-check?delay_minutes=10")
    assert res_due.status_code == 200
    due_data = res_due.json()
    assert due_data["dispatched_count"] >= 1

    call = [c for c in due_data["dispatched_calls"] if c["booking_id"] == booking_id][0]
    assert call["call_status"] == "COMPLETED"
    assert "ZominStay: Sizda yangi bron so'rovi bor" in call["spoken_message"]
    assert call["owner_phone"].startswith("+998")

    # 3. Second run should be idempotent: duplicate call is NOT dispatched!
    res_duplicate = client.post("/api/v1/owner/ivr-check?delay_minutes=10")
    assert res_duplicate.status_code == 200
    dup_calls = [c for c in res_duplicate.json()["dispatched_calls"] if c["booking_id"] == booking_id]
    assert len(dup_calls) == 0

    # 4. Check IVR logs endpoint
    logs_res = client.get("/api/v1/owner/ivr-logs")
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert len(logs) >= 1
    assert any(l["booking_id"] == booking_id for l in logs)

def test_ivr_not_triggered_for_accepted_or_rejected_booking(client, test_db_path):
    """
    Agar dacha egasi bronni 10 daqiqa ichida qabul qilsa yoki rad etsa,
    IVR ovozli robot bezovta qilmaydi.
    """
    props = client.get("/api/v1/properties").json()
    unit = props[0]["rental_units"][0]
    owner_id = props[0]["owner_id"]

    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit["id"],
        "checkin_time": "2026-11-25T14:00:00+05:00",
        "checkout_time": "2026-11-26T12:00:00+05:00",
        "guests_count": 2
    }).json()

    b = client.post("/api/v1/bookings/create", json={
        "quote_token": q["quote_token"],
        "guest_name": "Tezkor Ega Mehmoni",
        "guest_phone": "+998901114433"
    }).json()

    # Owner accepts booking right away
    client.post(f"/api/v1/owner/bookings/{b['id']}/transition?owner_id={owner_id}", json={"action": "ACCEPT"})

    # Simulate 15 minutes passed
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    with get_db(test_db_path) as conn:
        conn.execute("UPDATE bookings SET created_at = ? WHERE id = ?", (past_time, b["id"]))

    res = client.post("/api/v1/owner/ivr-check?delay_minutes=10")
    assert res.status_code == 200
    matching = [c for c in res.json()["dispatched_calls"] if c["booking_id"] == b["id"]]
    assert len(matching) == 0
