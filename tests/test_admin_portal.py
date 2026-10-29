import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, seed_initial_data

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    seed_initial_data()

def test_admin_dashboard_stats():
    client = TestClient(app)
    res = client.get("/api/v1/admin/dashboard-stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_gmv" in data
    assert "total_platform_fee" in data
    assert "total_properties" in data
    assert data["total_properties"] >= 4

def test_admin_properties_moderation():
    client = TestClient(app)
    # Get all properties
    res = client.get("/api/v1/admin/properties")
    assert res.status_code == 200
    props = res.json()
    assert len(props) >= 4
    prop_id = props[0]["id"]

    # Reject
    res_mod = client.post(f"/api/v1/admin/properties/{prop_id}/verify", json={
        "admin_id": "test_admin",
        "status": "REJECTED",
        "notes": "Hujjatlar yetarli emas"
    })
    assert res_mod.status_code == 200
    assert res_mod.json()["is_published"] is False

    # Verify again
    res_verify = client.post(f"/api/v1/admin/properties/{prop_id}/verify", json={
        "admin_id": "test_admin",
        "status": "VERIFIED",
        "notes": "Hujjatlar to'liq va joyida tekshirildi"
    })
    assert res_verify.status_code == 200
    assert res_verify.json()["is_published"] is True

def test_admin_users_and_audit():
    client = TestClient(app)
    res_users = client.get("/api/v1/admin/users")
    assert res_users.status_code == 200
    users = res_users.json()
    assert len(users) >= 4

    # Audit logs
    res_audit = client.get("/api/v1/admin/audit-logs")
    assert res_audit.status_code == 200
    logs = res_audit.json()
    assert isinstance(logs, list)

def test_admin_auth_login_and_property_crud():
    client = TestClient(app)

    # 1. Invalid login attempt
    bad_login = client.post("/api/v1/admin/auth/login", json={
        "username": "Umrzoq",
        "password": "wrong_password_xyz"
    })
    assert bad_login.status_code == 401

    # 2. Valid login with user's credentials: Umrzoq / pdp.university
    good_login = client.post("/api/v1/admin/auth/login", json={
        "username": "Umrzoq",
        "password": "pdp.university"
    })
    assert good_login.status_code == 200
    login_data = good_login.json()
    assert login_data["ok"] is True
    assert login_data["user"]["name"] == "Umrzoq"
    token = login_data["token"]
    assert token.startswith("admin_sec_")

    # 3. Create a brand new property via admin
    new_prop_res = client.post("/api/v1/admin/properties", json={
        "title": "Zomin Shoxona Dacha Yangi",
        "description": "Eng so'nggi dizayndagi zamonaviy tog' kotteji",
        "property_type": "VILLA",
        "micro_district": "DUOBA",
        "address_text": "Zomin, Duoba MFY, Soy bo'yi 12",
        "road_condition": "ASPHALT_SEDAN",
        "base_price_weekday": 2500000.0,
        "base_price_weekend": 3000000.0,
        "standard_capacity": 10,
        "max_capacity": 15,
        "owner_name": "Umrzoq Super",
        "owner_phone": "+998909998877",
        "photos": ["/static/assets/villa.jpg"],
        "amenities": ["Filtrli Hovuz", "Playstation 5", "Wi-Fi 5G", "Archa tandiri"]
    })
    assert new_prop_res.status_code == 200
    new_prop = new_prop_res.json()
    assert new_prop["ok"] is True
    created_id = new_prop["id"]

    # 4. Fetch full details
    detail_res = client.get(f"/api/v1/admin/properties/{created_id}/full")
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == "Zomin Shoxona Dacha Yangi"
    assert detail_res.json()["base_price_weekday"] == 2500000.0

    # 5. Update property
    update_res = client.put(f"/api/v1/admin/properties/{created_id}", json={
        "title": "Zomin Shoxona Dacha (Yangilandi)",
        "description": "Narxi arzonlashtirildi",
        "property_type": "VILLA",
        "micro_district": "DUOBA",
        "address_text": "Zomin, Duoba MFY, Soy bo'yi 12",
        "road_condition": "ASPHALT_SEDAN",
        "base_price_weekday": 2000000.0,
        "base_price_weekend": 2400000.0,
        "standard_capacity": 10,
        "max_capacity": 15,
        "owner_name": "Umrzoq Super",
        "owner_phone": "+998909998877",
        "photos": ["/static/assets/villa.jpg"],
        "amenities": ["Filtrli Hovuz", "Playstation 5", "Wi-Fi 5G", "Archa tandiri", "Sauna"]
    })
    assert update_res.status_code == 200
    assert update_res.json()["ok"] is True

    # Verify updated
    detail_res2 = client.get(f"/api/v1/admin/properties/{created_id}/full")
    assert detail_res2.json()["title"] == "Zomin Shoxona Dacha (Yangilandi)"
    assert detail_res2.json()["base_price_weekday"] == 2000000.0

    # 6. Delete property
    del_res = client.delete(f"/api/v1/admin/properties/{created_id}")
    assert del_res.status_code == 200
    assert del_res.json()["ok"] is True

    # 7. Check deleted
    get_del = client.get(f"/api/v1/admin/properties/{created_id}/full")
    assert get_del.status_code == 404

def test_admin_change_password():
    client = TestClient(app)

    # 1. Bad current password
    bad_req = client.post("/api/v1/admin/auth/change-password", json={
        "current_password": "wrong_password",
        "new_password": "new_secret_123"
    })
    assert bad_req.status_code == 400

    # 2. Too short new password
    short_req = client.post("/api/v1/admin/auth/change-password", json={
        "current_password": "pdp.university",
        "new_password": "123"
    })
    assert short_req.status_code == 400

    # 3. Successful change
    ok_req = client.post("/api/v1/admin/auth/change-password", json={
        "current_password": "pdp.university",
        "new_password": "new_secret_password_2026"
    })
    assert ok_req.status_code == 200
    assert ok_req.json()["ok"] is True

    # 4. Old password fails
    old_fail = client.post("/api/v1/admin/auth/login", json={
        "username": "Umrzoq",
        "password": "pdp.university"
    })
    assert old_fail.status_code == 401

    # 5. New password succeeds
    new_ok = client.post("/api/v1/admin/auth/login", json={
        "username": "Umrzoq",
        "password": "new_secret_password_2026"
    })
    assert new_ok.status_code == 200

    # Revert back to pdp.university for consistency
    revert_req = client.post("/api/v1/admin/auth/change-password", json={
        "current_password": "new_secret_password_2026",
        "new_password": "pdp.university"
    })
    assert revert_req.status_code == 200
