def test_offline_voucher_generation(client, test_db_path):
    """
    AC-09: Sayyoh Zomin tog'ining chuqur soylarida internet yo'q joyga tushib qolganda:
    Vaucherda GSM aloqa raqamlari, GPS koordinata, Yandex xarita havolasi va
    matnli marshrut ko'rsatmasi to'liq bo'lishi shart.
    """
    props = client.get("/api/v1/properties").json()
    unit_id = props[0]["rental_units"][0]["id"]

    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": "2026-11-10T14:00:00+05:00",
        "checkout_time": "2026-11-12T12:00:00+05:00",
        "guests_count": 4,
        "tandir_preorder_kg": 2.0
    }).json()

    b = client.post("/api/v1/bookings/create", json={
        "quote_token": q["quote_token"],
        "guest_name": "Tohir Rahimov",
        "guest_phone": "+998901234455",
        "car_plate": "01 Z 777 ZZ"
    }).json()

    ref = b["booking_reference"]

    # 1. JSON offline voucher
    v_res = client.get(f"/api/v1/vouchers/{ref}")
    assert v_res.status_code == 200
    v = v_res.json()

    assert v["booking_reference"] == ref
    assert v["guest_name"] == "Tohir Rahimov"
    assert v["car_plate"] == "01 Z 777 ZZ"
    assert v["owner_phone"].startswith("+998")
    assert v["caretaker_phone"].startswith("+998")
    assert v["navigation"]["latitude"] > 30.0
    assert v["navigation"]["longitude"] > 60.0
    assert "yandexmaps://" in v["navigation"]["yandex_maps_url"]
    assert "geo:" in v["navigation"]["geo_uri"]
    assert len(v["step_by_step_directions"]) > 20
    assert "ZOMINSTAY:" in v["offline_qr_data"]
    assert "2.0 kg" in v["tandir_order"]

    # 2. HTML printable voucher
    html_res = client.get(f"/api/v1/vouchers/{ref}/html")
    assert html_res.status_code == 200
    assert "text/html" in html_res.headers["content-type"]
    assert ref in html_res.text
    assert "tel:" in html_res.text
