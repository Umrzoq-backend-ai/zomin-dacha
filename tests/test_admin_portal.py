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
