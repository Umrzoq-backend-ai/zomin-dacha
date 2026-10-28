from app.database import get_db

def test_full_booking_lifecycle_and_fsm(client, test_db_path):
    """
    Test full FSM lifecycle: PENDING_OWNER -> AWAITING_PAYMENT -> CONFIRMED -> CHECKED_IN -> COMPLETED.
    """
    props = client.get("/api/v1/properties").json()
    prop = props[0]
    unit_id = prop["rental_units"][0]["id"]
    owner_id = prop["owner_id"]

    # 1. Quote & Create Booking
    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-09-10T14:00:00+05:00",
        "checkout_time": "2026-09-11T12:00:00+05:00",
        "guests_count": 2
    }).json()

    b = client.post("/api/v1/bookings/create", json={
        "quote_token": q["quote_token"],
        "guest_name": "Aziz Qosimov",
        "guest_phone": "+998901239876",
        "car_plate": "01 A 123 AA"
    }).json()

    booking_id = b["id"]
    assert b["status"] == "PENDING_OWNER"

    # 2. Owner accepts booking
    accept_res = client.post(f"/api/v1/owner/bookings/{booking_id}/transition?owner_id={owner_id}", json={
        "action": "ACCEPT"
    })
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "AWAITING_PAYMENT"

    # 3. Payment simulation -> CONFIRMED
    pay_res = client.post("/api/v1/payments/simulate-success", json={
        "booking_id": booking_id,
        "provider": "CLICK"
    })
    assert pay_res.status_code == 200
    assert pay_res.json()["error"] == 0

    detail = client.get(f"/api/v1/bookings/{booking_id}").json()
    assert detail["booking_status"] == "CONFIRMED"

    # 4. Caretaker marks guest arrival -> CHECKED_IN
    checkin_res = client.post(f"/api/v1/bookings/{booking_id}/check-in?user_id=30001&user_role=CARETAKER")
    assert checkin_res.status_code == 200
    assert checkin_res.json()["status"] == "CHECKED_IN"

    # 5. Complete stay -> COMPLETED
    comp_res = client.post(f"/api/v1/bookings/{booking_id}/complete?user_id={owner_id}")
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"

    # 6. Guest leaves verified review (AC-16)
    rev_res = client.post(f"/api/v1/bookings/{booking_id}/reviews", json={
        "booking_id": booking_id,
        "rating_cleanliness": 5,
        "rating_accuracy": 5,
        "rating_communication": 4,
        "rating_comfort": 5,
        "comment": "Zomin tabiati ajoyib, dacha toza va shinam ekan!"
    })
    assert rev_res.status_code == 201
    rev_data = rev_res.json()
    assert rev_data["overall_rating"] == 4.75
    assert rev_data["guest_name"] == "Aziz Qosimov"

def test_bola_protection(client, test_db_path):
    """
    AC-07: Begona dacha identifikatorini manipulyatsiya qilgan foydalanuvchiga 403 Forbidden.
    """
    props = client.get("/api/v1/properties").json()
    prop1 = props[0]
    unit1_id = prop1["rental_units"][0]["id"]
    fake_owner_id = "00000000-0000-0000-0000-000000000999"

    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit1_id,
        "checkin_time": "2026-09-15T14:00:00+05:00",
        "checkout_time": "2026-09-16T12:00:00+05:00",
        "guests_count": 2
    }).json()

    b = client.post("/api/v1/bookings/create", json={
        "quote_token": q["quote_token"],
        "guest_name": "Test Guest",
        "guest_phone": "+998901230000"
    }).json()

    # Fake owner attempts to accept/reject booking
    bad_res = client.post(f"/api/v1/owner/bookings/{b['id']}/transition?owner_id={fake_owner_id}", json={
        "action": "ACCEPT"
    })
    assert bad_res.status_code == 403
    assert "BOLA" in bad_res.json()["detail"]

def test_caretaker_role_financial_masking(client, test_db_path):
    """
    AC-14: Bog'bon o'z akkaunti bilan kirganda, barcha moliyaviy ma'lumotlar yashiriladi.
    """
    props = client.get("/api/v1/properties").json()
    unit_id = props[0]["rental_units"][0]["id"]

    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-09-20T14:00:00+05:00",
        "checkout_time": "2026-09-22T12:00:00+05:00",
        "guests_count": 6
    }).json()

    b = client.post("/api/v1/bookings/create", json={
        "quote_token": q["quote_token"],
        "guest_name": "Nodir",
        "guest_phone": "+998907770000",
        "car_plate": "25 B 777 BB"
    }).json()

    # View as Guest / Owner
    guest_view = client.get(f"/api/v1/bookings/{b['id']}?user_role=GUEST").json()
    assert guest_view["total_amount"] is not None
    assert guest_view["platform_fee_amount"] is not None

    # View as Caretaker (AC-14)
    caretaker_view = client.get(f"/api/v1/bookings/{b['id']}?user_role=CARETAKER").json()
    assert caretaker_view["total_amount"] is None
    assert caretaker_view["unit_base_amount"] is None
    assert caretaker_view["platform_fee_amount"] is None
    assert caretaker_view["pay_on_arrival_amount"] is None
    assert caretaker_view["tandir_amount"] == 0.0
    # But caretaker still sees guest name, phone, car plate, arrival time!
    assert caretaker_view["guest_name"] == "Nodir"
    assert caretaker_view["guest_phone"] == "+998907770000"
    assert caretaker_view["car_plate"] == "25 B 777 BB"
