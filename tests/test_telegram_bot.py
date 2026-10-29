import pytest
from app.config import settings
from app.services.telegram_bot import bot_service

def test_telegram_info_endpoint(client, test_db_path):
    """
    Test diagnostic status of Telegram bot and WebApp config.
    """
    res = client.get("/api/v1/telegram/info")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["bot_configured"] is True
    assert "Mini App" in data["supported_features"][0]
    assert data["webhook_url"].endswith("/api/v1/telegram/webhook")

def test_telegram_webhook_start_command(client, test_db_path):
    """
    Test /start command handling via webhook:
    Registers user and returns welcome text with Mini App WebApp button.
    """
    payload = {
        "update_id": 10001,
        "message": {
            "message_id": 1,
            "from": {
                "id": 99123456,
                "first_name": "Sardor",
                "last_name": "Toshmatov",
                "username": "sardor_travel"
            },
            "chat": {
                "id": 99123456,
                "type": "private"
            },
            "date": 1729000000,
            "text": "/start"
        }
    }

    res = client.post("/api/v1/telegram/webhook", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    result = body["result"]
    assert "Sardor" in result["text"]
    assert "Mini App" in result["text"] or "Dacha" in result["text"]
    # Check inline keyboard has WebApp button
    reply_markup = result.get("reply_markup", {})
    keyboard = reply_markup.get("inline_keyboard", [])
    assert len(keyboard) > 0
    assert "web_app" in keyboard[0][0]

def test_telegram_webhook_my_bookings_callback(client, test_db_path):
    """
    Test 'Mening bronlarim' callback query.
    """
    payload = {
        "update_id": 10002,
        "callback_query": {
            "id": "cb_query_123",
            "from": {
                "id": 99123456,
                "first_name": "Sardor"
            },
            "data": "cmd_my_bookings"
        }
    }

    res = client.post("/api/v1/telegram/webhook", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "bron" in body["result"]["text"].lower()

def test_telegram_webhook_gate_check_flow(client, test_db_path):
    """
    Test Caretaker Gate check by Car Plate:
    1. Caretaker clicks 'cmd_gate_check' -> bot asks for car plate.
    2. Caretaker sends '01 A 777 AA' -> bot verifies access.
    """
    chat_id = 88776655

    # 1. Click Gate Check
    res1 = client.post("/api/v1/telegram/webhook", json={
        "update_id": 10003,
        "callback_query": {
            "id": "cb_gate_1",
            "from": {"id": chat_id, "first_name": "Rustam Tog'a"},
            "data": "cmd_gate_check"
        }
    })
    assert res1.status_code == 200
    assert "Darvoza Tekshiruvi" in res1.json()["result"]["text"]

    # 2. Caretaker sends plate that is not in database -> access denied
    res2 = client.post("/api/v1/telegram/webhook", json={
        "update_id": 10004,
        "message": {
            "message_id": 2,
            "from": {"id": chat_id, "first_name": "Rustam Tog'a"},
            "chat": {"id": chat_id, "type": "private"},
            "text": "99 Z 999 ZZ"
        }
    })
    assert res2.status_code == 200
    assert "topilmadi" in res2.json()["result"]["text"]

def test_telegram_webhook_support_and_about(client, test_db_path):
    """
    Test support and about Zaamin callbacks.
    """
    # Support
    res1 = client.post("/api/v1/telegram/webhook", json={
        "update_id": 10005,
        "callback_query": {
            "id": "cb_supp",
            "from": {"id": 12345, "first_name": "Aziz"},
            "data": "cmd_support"
        }
    })
    assert res1.status_code == 200
    assert "+998 78 120 00 21" in res1.json()["result"]["text"]

    # About
    res2 = client.post("/api/v1/telegram/webhook", json={
        "update_id": 10006,
        "callback_query": {
            "id": "cb_about",
            "from": {"id": 12345, "first_name": "Aziz"},
            "data": "cmd_about"
        }
    })
    assert res2.status_code == 200
    assert "Zomin Osma Ko'prigi" in res2.json()["result"]["text"]
