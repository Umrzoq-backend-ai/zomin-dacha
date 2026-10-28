import concurrent.futures
import threading
from app.database import get_db

def test_multi_threaded_race_condition_exact_single_winner(client, test_db_path):
    """
    Stress-test race conditions:
    20 ta oqim bir vaqtning o'zida ayni bir sanaga bitta dachani bron qilishga urinadi.
    NATIJA: Aniq 1 ta bron muvaffaqiyatli (201) bo'lishi, qolgan 19 tasi esa 409 Conflict olishi shart.
    """
    props = client.get("/api/v1/properties").json()
    unit_id = props[0]["rental_units"][0]["id"]
    checkin = "2026-12-01T14:00:00+05:00"
    checkout = "2026-12-03T12:00:00+05:00"

    q_res = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": checkin,
        "checkout_time": checkout,
        "guests_count": 4
    })
    token = q_res.json()["quote_token"]

    status_codes = []
    lock = threading.Lock()

    def try_booking(i):
        res = client.post("/api/v1/bookings/create", json={
            "quote_token": token,
            "guest_name": f"Raqobatchi {i}",
            "guest_phone": f"+9989011122{i:02d}"
        })
        with lock:
            status_codes.append(res.status_code)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(try_booking, i) for i in range(20)]
        concurrent.futures.wait(futures)

    assert status_codes.count(201) == 1
    assert status_codes.count(409) == 19

def test_idempotency_key_replay(client, test_db_path):
    """
    AC-04: Idempotency-Key bilan bir xil so'rov qayta yuborilganda,
    qayta bron yaratilmaydi va avvalgi natija qaytariladi.
    """
    props = client.get("/api/v1/properties").json()
    unit_id = props[0]["rental_units"][0]["id"]

    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-12-10T14:00:00+05:00",
        "checkout_time": "2026-12-11T12:00:00+05:00",
        "guests_count": 2
    }).json()

    key = "unique-client-session-key-999"
    payload = {
        "quote_token": q["quote_token"],
        "guest_name": "Idempotent Mehmon",
        "guest_phone": "+998907654321"
    }

    # First request
    res1 = client.post("/api/v1/bookings/create", headers={"Idempotency-Key": key}, json=payload)
    assert res1.status_code == 201
    booking1 = res1.json()

    # Second duplicate request with same key
    res2 = client.post("/api/v1/bookings/create", headers={"Idempotency-Key": key}, json=payload)
    assert res2.status_code == 201
    booking2 = res2.json()

    assert booking1["id"] == booking2["id"]
    assert booking1["booking_reference"] == booking2["booking_reference"]

def test_invalid_dates_and_nonexistent_unit(client, test_db_path):
    """
    Boundary conditions: checkout <= checkin, nonexistent unit.
    """
    props = client.get("/api/v1/properties").json()
    unit_id = props[0]["rental_units"][0]["id"]

    # Checkout earlier than checkin
    res_bad_dates = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-12-15T14:00:00+05:00",
        "checkout_time": "2026-12-14T12:00:00+05:00",
        "guests_count": 2
    })
    assert res_bad_dates.status_code == 400

    # Nonexistent unit
    res_fake_unit = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": "00000000-0000-0000-0000-000000000000",
        "checkin_time": "2026-12-15T14:00:00+05:00",
        "checkout_time": "2026-12-16T12:00:00+05:00",
        "guests_count": 2
    })
    assert res_fake_unit.status_code == 404

def test_owner_manual_calendar_block_prevents_booking(client, test_db_path):
    """
    Ega dacha kalendarini qo'lda yopsa (OWNER_MANUAL), sayyohlar bron qila olmaydi.
    """
    props = client.get("/api/v1/properties").json()
    prop = props[0]
    unit_id = prop["rental_units"][0]["id"]
    owner_id = prop["owner_id"]

    start = "2026-12-20T14:00:00+05:00"
    end = "2026-12-25T12:00:00+05:00"

    # Owner manually blocks date
    block_res = client.post("/api/v1/owner/calendar/block", json={
        "rental_unit_id": unit_id,
        "owner_id": owner_id,
        "start_time": start,
        "end_time": end,
        "notes": "Qarindoshlar mehmondorchiligi"
    })
    assert block_res.status_code == 200
    assert block_res.json()["status"] == "SUCCESS"

    # Tourist gets quote and tries to book during blocked period
    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-12-21T14:00:00+05:00",
        "checkout_time": "2026-12-23T12:00:00+05:00",
        "guests_count": 4
    }).json()

    b_res = client.post("/api/v1/bookings/create", json={
        "quote_token": q["quote_token"],
        "guest_name": "Sayyoh",
        "guest_phone": "+998901230000"
    })
    assert b_res.status_code == 409
    assert "Double-booking" in b_res.json()["detail"] or "band qilingan" in b_res.json()["detail"]
