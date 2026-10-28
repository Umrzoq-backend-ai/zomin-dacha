import hmac
import hashlib
import time
import json
import base64
from typing import Optional, Dict, Any
from urllib.parse import parse_qsl, unquote

from app.config import settings

def verify_telegram_init_data(init_data: str, bot_token: Optional[str] = None, max_age_seconds: int = 86400) -> Optional[Dict[str, Any]]:
    """
    Telegram Mini App initData xavfsiz validatsiyasi (TZ 5.1 & AC-08):
    1. URL-unquote qiladi.
    2. auth_date bo'yicha Replay attackni to'xtatadi.
    3. HMAC-SHA256 xeshini tekshiradi.
    """
    token = bot_token or settings.TELEGRAM_BOT_TOKEN
    try:
        # Handles raw or URL-encoded query string
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return None

    if "hash" not in parsed_data:
        return None

    received_hash = parsed_data.pop("hash")

    # Replay attack tekshiruvi: auth_date eskirgan bo'lmasligi shart
    try:
        auth_date = int(parsed_data.get("auth_date", 0))
    except (ValueError, TypeError):
        return None

    current_time = int(time.time())
    if abs(current_time - auth_date) > max_age_seconds:
        return None

    # Ma'lumotlarni alifbo tartibida k=v ko'rinishida birlashtirish
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if hmac.compare_digest(calculated_hash, received_hash):
        # Parse user json if present
        if "user" in parsed_data and isinstance(parsed_data["user"], str):
            try:
                parsed_data["user"] = json.loads(parsed_data["user"])
            except Exception:
                pass
        return parsed_data
    return None

def create_quote_token(payload: Dict[str, Any]) -> str:
    """
    Generates a cryptographically signed tamper-proof token for price quotations (AC-03).
    """
    json_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    b64_payload = base64.urlsafe_b64encode(json_bytes).decode('utf-8')
    
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        b64_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"{b64_payload}.{signature}"

def verify_quote_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies that quote token is untampered and not expired.
    """
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        b64_payload, signature = parts
        
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            b64_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_sig, signature):
            return None
            
        json_bytes = base64.urlsafe_b64decode(b64_payload.encode('utf-8'))
        payload = json.loads(json_bytes.decode('utf-8'))
        
        # Check expiry
        expires_at_str = payload.get("expires_at")
        if expires_at_str:
            from datetime import datetime, timezone
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now(timezone.utc) > expires_at:
                return None
                
        return payload
    except Exception:
        return None
