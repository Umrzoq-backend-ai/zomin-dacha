import hmac
import hashlib
import time
import json
from urllib.parse import urlencode

from app.config import settings

def create_valid_telegram_init_data(user_dict: dict, bot_token: str, auth_date: int = None) -> str:
    date_val = auth_date if auth_date is not None else int(time.time())
    data = {
        "auth_date": str(date_val),
        "query_id": "AAHdF6IQAAAAAN0XohDhrPzY",
        "user": json.dumps(user_dict, separators=(',', ':'))
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    data["hash"] = calc_hash
    return urlencode(data)

def test_telegram_webapp_auth_valid(client, test_db_path):
    """
    AC-08: To'g'ri Telegram HMAC xeshi orqali autentifikatsiya.
    """
    user_payload = {
        "id": 99881122,
        "first_name": "Bobur",
        "last_name": "Mirzo",
        "username": "bmirzo"
    }
    init_data = create_valid_telegram_init_data(user_payload, settings.TELEGRAM_BOT_TOKEN)

    res = client.post("/api/v1/auth/telegram-webapp", json={"init_data": init_data})
    assert res.status_code == 200
    user = res.json()
    assert user["telegram_id"] == 99881122
    assert "Bobur Mirzo" in user["full_name"]

def test_telegram_webapp_auth_tampered_hash(client, test_db_path):
    """
    AC-08: Soxtalashtirilgan xesh 401 Unauthorized qaytaradi.
    """
    user_payload = {"id": 112233, "first_name": "Hacker"}
    init_data = create_valid_telegram_init_data(user_payload, settings.TELEGRAM_BOT_TOKEN)
    # Tamper with query string
    tampered = init_data.replace("112233", "999999")

    res = client.post("/api/v1/auth/telegram-webapp", json={"init_data": tampered})
    assert res.status_code == 401

def test_telegram_webapp_auth_replay_attack_expired(client, test_db_path):
    """
    AC-08: auth_date 24 soatdan eski bo'lsa (Replay attack), 401 Unauthorized qaytaradi.
    """
    user_payload = {"id": 445566, "first_name": "Eski Foydalanuvchi"}
    two_days_ago = int(time.time()) - (2 * 86400)
    expired_init_data = create_valid_telegram_init_data(user_payload, settings.TELEGRAM_BOT_TOKEN, auth_date=two_days_ago)

    res = client.post("/api/v1/auth/telegram-webapp", json={"init_data": expired_init_data})
    assert res.status_code == 401
