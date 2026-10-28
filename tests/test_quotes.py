from app.database import get_db

def test_quote_weekday_vs_weekend_calculation(client, test_db_path):
    """
    Test weekday vs weekend pricing difference and tandir pre-order.
    """
    props = client.get("/api/v1/properties").json()
    unit = props[0]["rental_units"][0]
    unit_id = unit["id"]
    base_weekday = float(unit["base_price_weekday"])
    base_weekend = float(unit["base_price_weekend"])
    assert base_weekend > base_weekday

    # 1. Weekday booking: Monday 2026-08-03 to Wednesday 2026-08-05 (2 nights: Mon, Tue)
    res_wd = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-08-03T14:00:00+05:00",
        "checkout_time": "2026-08-05T12:00:00+05:00",
        "guests_count": 4,
        "tandir_preorder_kg": 0
    })
    assert res_wd.status_code == 200
    data_wd = res_wd.json()
    assert data_wd["nights_or_days"] == 2
    assert data_wd["breakdown"]["accommodation_total"] == base_weekday * 2
    assert data_wd["breakdown"]["tandir_meat_total"] == 0

    # 2. Weekend booking: Friday 2026-08-07 to Sunday 2026-08-09 (2 nights: Fri, Sat)
    res_we = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-08-07T14:00:00+05:00",
        "checkout_time": "2026-08-09T12:00:00+05:00",
        "guests_count": 4,
        "tandir_preorder_kg": 2.5
    })
    assert res_we.status_code == 200
    data_we = res_we.json()
    assert data_we["nights_or_days"] == 2
    assert data_we["breakdown"]["accommodation_total"] == base_weekend * 2
    expected_tandir = 2.5 * 150000.0
    assert data_we["breakdown"]["tandir_meat_total"] == expected_tandir
    expected_grand = (base_weekend * 2) + expected_tandir
    assert data_we["breakdown"]["grand_total"] == expected_grand
    assert data_we["breakdown"]["platform_fee_online"] == round(expected_grand * 0.10, 2)
    assert data_we["breakdown"]["payable_on_arrival_to_owner"] == round(expected_grand * 0.90, 2)

def test_quote_immutability_and_tampering(client, test_db_path):
    """
    AC-03: Ega narxni oshirsa ham, avvalroq yaratilgan quote token summasi daxlsiz qoladi.
    Token manipulyatsiya qilinsa 400 qaytariladi.
    """
    props = client.get("/api/v1/properties").json()
    unit = props[0]["rental_units"][0]
    unit_id = unit["id"]

    # 1. Get quote
    res = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-08-20T14:00:00+05:00",
        "checkout_time": "2026-08-21T12:00:00+05:00",
        "guests_count": 2
    })
    token = res.json()["quote_token"]
    original_total = res.json()["breakdown"]["grand_total"]

    # 2. Owner changes price in DB to 10x higher
    with get_db(test_db_path) as conn:
        conn.execute("UPDATE rental_units SET base_price_weekday = 99000000 WHERE id = ?", (unit_id,))

    # 3. Create booking with original token: original quoted price is strictly preserved!
    b_res = client.post("/api/v1/bookings/create", json={
        "quote_token": token,
        "guest_name": "Test Mehmon",
        "guest_phone": "+998909998877"
    })
    assert b_res.status_code == 201
    assert b_res.json()["total_amount"] == original_total

    # 4. Tampered token should fail
    tampered_token = token[:-4] + "abcd"
    bad_res = client.post("/api/v1/bookings/create", json={
        "quote_token": tampered_token,
        "guest_name": "Hacker",
        "guest_phone": "+998901234567"
    })
    assert bad_res.status_code == 400
