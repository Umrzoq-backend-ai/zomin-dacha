import pytest

def test_register_and_login_email(client):
    # 1. Register new email user
    email = "sayyoh_test@gmail.com"
    reg_res = client.post("/api/v1/auth/register-email", json={
        "full_name": "Sayyoh Test",
        "email": email,
        "password": "Password123!",
        "phone_number": "+998901239988"
    })
    assert reg_res.status_code == 200
    user = reg_res.json()
    assert user["email"] == email
    assert user["full_name"] == "Sayyoh Test"
    assert user["role"] == "GUEST"

    # 2. Duplicate email should fail
    dup_res = client.post("/api/v1/auth/register-email", json={
        "full_name": "Another Sayyoh",
        "email": email,
        "password": "Password123!"
    })
    assert dup_res.status_code == 400

    # 3. Login with correct password
    login_res = client.post("/api/v1/auth/login-email", json={
        "email": email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    logged_user = login_res.json()
    assert logged_user["id"] == user["id"]

    # 4. Login with wrong password
    wrong_res = client.post("/api/v1/auth/login-email", json={
        "email": email,
        "password": "WrongPassword!"
    })
    assert wrong_res.status_code == 401

def test_google_auth_and_profile_update(client):
    # 1. Google sign-in
    g_res = client.post("/api/v1/auth/google-auth", json={
        "email": "umurzoq_google@gmail.com",
        "full_name": "Umrzoq Google",
        "avatar_url": "/static/assets/avatar.jpg"
    })
    assert g_res.status_code == 200
    g_user = g_res.json()
    assert g_user["email"] == "umurzoq_google@gmail.com"
    assert g_user["auth_provider"] == "GOOGLE"

    # 2. Update profile
    up_res = client.post("/api/v1/auth/update-profile", json={
        "id": g_user["id"],
        "full_name": "Umrzoq Yulchiyev (Updated)",
        "phone_number": "+998991234567",
        "car_number": "01 A 777 AA"
    })
    assert up_res.status_code == 200
    updated = up_res.json()
    assert updated["full_name"] == "Umrzoq Yulchiyev (Updated)"
    assert updated["car_number"] == "01 A 777 AA"

def test_forgot_and_reset_password(client):
    # 1. Create account
    email = "reset_user@gmail.com"
    client.post("/api/v1/auth/register-email", json={
        "full_name": "Reset User",
        "email": email,
        "password": "OldPassword123"
    })

    # 2. Request forgot password code
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    data = forgot_res.json()
    assert "code_hint" in data
    code = data["code_hint"]

    # 3. Reset password using code
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "email": email,
        "code": code,
        "new_password": "NewSecretPassword2026!"
    })
    assert reset_res.status_code == 200

    # 4. Login with new password
    login_new = client.post("/api/v1/auth/login-email", json={
        "email": email,
        "password": "NewSecretPassword2026!"
    })
    assert login_new.status_code == 200

def test_authenticated_wishlist(client):
    # 1. Register a user
    user_res = client.post("/api/v1/auth/register-email", json={
        "full_name": "Wishlist User",
        "email": "wishlist_user@gmail.com",
        "password": "WishlistPass123"
    })
    user_id = user_res.json()["id"]

    # 2. Toggle add to wishlist
    add_res = client.post("/api/v1/auth/wishlist/toggle", json={
        "user_id": user_id,
        "property_slug": "shox-dacha-zomin"
    })
    assert add_res.status_code == 200
    assert add_res.json()["status"] == "added"
    assert "shox-dacha-zomin" in add_res.json()["wishlist"]

    # 3. Fetch wishlist
    get_res = client.get(f"/api/v1/auth/wishlist/{user_id}")
    assert get_res.status_code == 200
    assert "shox-dacha-zomin" in get_res.json()["wishlist"]

    # 4. Toggle remove from wishlist
    remove_res = client.post("/api/v1/auth/wishlist/toggle", json={
        "user_id": user_id,
        "property_slug": "shox-dacha-zomin"
    })
    assert remove_res.status_code == 200
    assert remove_res.json()["status"] == "removed"
    assert "shox-dacha-zomin" not in remove_res.json()["wishlist"]
