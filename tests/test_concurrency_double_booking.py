import concurrent.futures
from datetime import datetime, timezone, timedelta
from app.database import get_db

def test_double_booking_concurrency_prevention(client, test_db_path):
    """
    AC-01: Ikki mijoz bir vaqtda bitta dachani ayni bir sanaga bron qilishga urinsa:
    Biri muvaffaqiyatli o'tadi, ikkinchisiga 409 Conflict qaytariladi.
    """
    # 1. Fetch properties to get a rental unit
    props_res = client.get("/api/v1/properties")
    assert props_res.status_code == 200
    props = props_res.json()
    unit = props[0]["rental_units"][0]
    unit_id = unit["id"]

    # 2. Both clients get quotes for overlapping dates
    checkin = "2026-08-10T14:00:00+05:00"
    checkout = "2026-08-12T12:00:00+05:00"

    q_res1 = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": checkin,
        "checkout_time": checkout,
        "guests_count": 4
    })
    assert q_res1.status_code == 200
    token1 = q_res1.json()["quote_token"]

    q_res2 = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-08-11T14:00:00+05:00", # Overlaps with 10-12
        "checkout_time": "2026-08-13T12:00:00+05:00",
        "guests_count": 4
    })
    assert q_res2.status_code == 200
    token2 = q_res2.json()["quote_token"]

    # 3. Client 1 books
    b1_res = client.post("/api/v1/bookings/create", json={
        "quote_token": token1,
        "guest_name": "Sayyoh 1",
        "guest_phone": "+998901111111"
    })
    assert b1_res.status_code == 201
    assert b1_res.json()["status"] == "PENDING_OWNER"

    # 4. Client 2 tries to book overlapping period
    b2_res = client.post("/api/v1/bookings/create", json={
        "quote_token": token2,
        "guest_name": "Sayyoh 2",
        "guest_phone": "+998902222222"
    })
    # Must fail with 409 Conflict
    assert b2_res.status_code == 409
    assert "Double-booking" in b2_res.json()["detail"] or "band qilingan" in b2_res.json()["detail"]

def test_day_use_tapchan_non_overlapping_slots(client, test_db_path):
    """
    AC-02: Choyxona tapchanini kunduzi 10:00-16:00 ga bir mijoz, 
    17:00-23:00 ga boshqa mijoz olsa:
    Ikkala bron ham muvaffaqiyatli o'tadi (vaqt oraliqlari ustma-ust tushmaydi).
    """
    # Find tapchan unit
    props_res = client.get("/api/v1/properties?property_type=CHOYXONA_TAPCHAN")
    assert props_res.status_code == 200
    tapchan_props = props_res.json()
    assert len(tapchan_props) > 0
    tapchan_unit = tapchan_props[0]["rental_units"][0]
    unit_id = tapchan_unit["id"]

    # Slot 1: Lunch 10:00 - 16:00
    q1 = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-08-15T10:00:00+05:00",
        "checkout_time": "2026-08-15T16:00:00+05:00",
        "day_use_slot_name": "LUNCH",
        "guests_count": 6
    })
    assert q1.status_code == 200

    # Slot 2: Dinner 17:00 - 23:00
    q2 = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-08-15T17:00:00+05:00",
        "checkout_time": "2026-08-15T23:00:00+05:00",
        "day_use_slot_name": "DINNER",
        "guests_count": 6
    })
    assert q2.status_code == 200

    # Book Slot 1
    b1 = client.post("/api/v1/bookings/create", json={
        "quote_token": q1.json()["quote_token"],
        "guest_name": "Oila 1 (Tushlik)",
        "guest_phone": "+998903333333"
    })
    assert b1.status_code == 201

    # Book Slot 2
    b2 = client.post("/api/v1/bookings/create", json={
        "quote_token": q2.json()["quote_token"],
        "guest_name": "Oila 2 (Kechki ovqat)",
        "guest_phone": "+998904444444"
    })
    assert b2.status_code == 201
    assert b1.json()["id"] != b2.json()["id"]

def test_lazy_hold_invalidation(client, test_db_path):
    """
    AC-05: Sayyoh 15 daqiqada to'lamasa va hold muddati tugasa:
    Lazy Invalidation joyni bo'shatadi (HOLD -> EXPIRED), kalendar yangi mijozga ochiladi.
    """
    props = client.get("/api/v1/properties").json()
    unit_id = props[0]["rental_units"][0]["id"]

    checkin = "2026-09-01T14:00:00+05:00"
    checkout = "2026-09-03T12:00:00+05:00"

    q1 = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": checkin,
        "checkout_time": checkout,
        "guests_count": 4
    })
    assert q1.status_code == 200

    # Client 1 makes booking
    b1 = client.post("/api/v1/bookings/create", json={
        "quote_token": q1.json()["quote_token"],
        "guest_name": "Eski Mehmon",
        "guest_phone": "+998905555555"
    })
    assert b1.status_code == 201
    b1_id = b1.json()["id"]

    # Artificially expire the hold in DB (simulate 20 minutes passed)
    expired_time = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
    with get_db(test_db_path) as conn:
        conn.execute("UPDATE inventory_allocations SET expires_at = ? WHERE booking_id = ?", (expired_time, b1_id))
        conn.execute("UPDATE bookings SET hold_expires_at = ? WHERE id = ?", (expired_time, b1_id))

    # Client 2 now books the exact same dates
    q2 = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": checkin,
        "checkout_time": checkout,
        "guests_count": 4
    })
    assert q2.status_code == 200

    b2 = client.post("/api/v1/bookings/create", json={
        "quote_token": q2.json()["quote_token"],
        "guest_name": "Yangi Mehmon",
        "guest_phone": "+998906666666"
    })
    # Must succeed because Client 1's expired hold was automatically cleaned up
    assert b2.status_code == 201
    assert b2.json()["status"] == "PENDING_OWNER"
