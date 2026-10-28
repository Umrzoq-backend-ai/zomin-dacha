def test_filters_road_condition_and_generator(client, test_db_path):
    """
    AC-11: Foydalanuvchi "Spark chiqadigan yo'l" va "Generator bor" filtrini tanlasa:
    Faqat ASPHALT_SEDAN va has_generator=True bo'lgan dachalar filtrlanadi.
    """
    res = client.get("/api/v1/properties?road_condition=ASPHALT_SEDAN&has_generator=true")
    assert res.status_code == 200
    props = res.json()
    assert len(props) > 0
    for p in props:
        assert p["road_condition"] == "ASPHALT_SEDAN"
        assert p["has_generator"] is True

def test_filter_by_micro_district(client, test_db_path):
    """
    Mikro-hudud bo'yicha saralash (DUOBA, ORIKLISOY, SUFFA, SANATORIY).
    """
    res_duoba = client.get("/api/v1/properties?micro_district=DUOBA")
    assert res_duoba.status_code == 200
    for p in res_duoba.json():
        assert p["micro_district"] == "DUOBA"

    res_suffa = client.get("/api/v1/properties?micro_district=SUFFA")
    assert res_suffa.status_code == 200
    for p in res_suffa.json():
        assert p["micro_district"] == "SUFFA"

def test_dateless_search_shows_starting_price(client, test_db_path):
    """
    AC-13: Qidiruv sanasiz amalga oshirilsa, katalog boshlang'ich narxni ko'rsatadi.
    """
    res = client.get("/api/v1/properties")
    assert res.status_code == 200
    props = res.json()
    assert len(props) > 0
    for p in props:
        assert p["min_price"] > 0
        assert len(p["rental_units"]) > 0

def test_date_availability_search_filtering(client, test_db_path):
    """
    Sana kiritilganda faqat bo'sh bo'lgan dachalar chiqadi, band qilinganlari filtrlanadi.
    """
    props = client.get("/api/v1/properties").json()
    unit_id = props[0]["rental_units"][0]["id"]
    prop_id = props[0]["id"]

    checkin = "2026-11-01T14:00:00"
    checkout = "2026-11-03T12:00:00"

    # Book unit
    q = client.post("/api/v1/quotes/calculate", json={
        "rental_unit_id": unit_id,
        "checkin_time": f"{checkin}+05:00",
        "checkout_time": f"{checkout}+05:00",
        "guests_count": 2
    }).json()

    client.post("/api/v1/bookings/create", json={
        "quote_token": q["quote_token"],
        "guest_name": "Band Qiluvchi",
        "guest_phone": "+998901112255"
    })

    # Search covering that date range
    search_res = client.get(f"/api/v1/properties?checkin_time={checkin}&checkout_time={checkout}")
    assert search_res.status_code == 200
    available_props = search_res.json()
    available_prop_ids = [p["id"] for p in available_props]
    
    # Booked property unit should not be available
    for p in available_props:
        if p["id"] == prop_id:
            available_unit_ids = [u["id"] for u in p["rental_units"]]
            assert unit_id not in available_unit_ids
