import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from app.database import get_db
from app.security import verify_telegram_init_data
from app.models import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

class TelegramAuthRequest(BaseModel):
    init_data: str

class QuickLoginRequest(BaseModel):
    phone_number: str
    role: Optional[str] = None
    full_name: Optional[str] = None

@router.post("/telegram-webapp", response_model=UserResponse)
def authenticate_telegram_webapp(req: TelegramAuthRequest):
    """
    Telegram Mini App initData xavfsiz validatsiyasi (AC-08).
    HMAC-SHA256 xeshini tekshiradi va foydalanuvchini bazadan topadi yoki ro'yxatdan o'tkazadi.
    """
    verified_data = verify_telegram_init_data(req.init_data)
    if not verified_data:
        raise HTTPException(status_code=401, detail="Telegram initData yaroqsiz, soxtalashtirilgan yoki muddati tugagan")

    user_info = verified_data.get("user")
    if not user_info or not isinstance(user_info, dict):
        raise HTTPException(status_code=400, detail="Telegram user ma'lumotlari topilmadi")

    telegram_id = user_info.get("id")
    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip() or "Telegram Foydalanuvchisi"
    username = user_info.get("username", "")

    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()

        if row:
            return UserResponse(
                id=row["id"],
                phone_number=row["phone_number"],
                full_name=row["full_name"],
                telegram_id=row["telegram_id"],
                role=row["role"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

        # Create new guest user
        new_id = str(uuid.uuid4())
        phone = f"+998{telegram_id % 1000000000:09d}" # fallback if phone not shared
        cursor.execute("""
            INSERT INTO users (id, phone_number, full_name, telegram_id, role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'GUEST', 1, ?, ?)
        """, (new_id, phone, full_name, telegram_id, now_iso, now_iso))

        return UserResponse(
            id=new_id,
            phone_number=phone,
            full_name=full_name,
            telegram_id=telegram_id,
            role="GUEST",
            is_active=True,
            created_at=now_iso,
            updated_at=now_iso
        )

@router.post("/quick-login", response_model=UserResponse)
def quick_login(req: QuickLoginRequest):
    """
    Tezkor kirish (Sayyoh, Ega, Bog'bon va Admin rejimlari o'rtasida o'tish uchun).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE phone_number = ?", (req.phone_number,))
        row = cursor.fetchone()

        if row:
            if req.role and req.role != row["role"]:
                cursor.execute("UPDATE users SET role = ?, updated_at = ? WHERE id = ?", (req.role, now_iso, row["id"]))
                cursor.execute("SELECT * FROM users WHERE id = ?", (row["id"],))
                row = cursor.fetchone()

            return UserResponse(
                id=row["id"],
                phone_number=row["phone_number"],
                full_name=row["full_name"],
                telegram_id=row["telegram_id"],
                role=row["role"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

        new_id = str(uuid.uuid4())
        role = req.role or "GUEST"
        name = req.full_name or f"Foydalanuvchi {req.phone_number[-4:]}"
        cursor.execute("""
            INSERT INTO users (id, phone_number, full_name, role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
        """, (new_id, req.phone_number, name, role, now_iso, now_iso))

        return UserResponse(
            id=new_id,
            phone_number=req.phone_number,
            full_name=name,
            telegram_id=None,
            role=role,
            is_active=True,
            created_at=now_iso,
            updated_at=now_iso
        )
