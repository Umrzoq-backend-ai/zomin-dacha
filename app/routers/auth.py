import uuid
import hashlib
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.security import verify_telegram_init_data
from app.models import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

SALT = b"zomin_secure_salt_2026_auth"

def hash_password(password: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), SALT, 100000).hex()

def verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    return hash_password(password) == hashed

def map_user_row(row) -> UserResponse:
    keys = row.keys()
    return UserResponse(
        id=row["id"],
        phone_number=row["phone_number"],
        full_name=row["full_name"],
        telegram_id=row["telegram_id"] if "telegram_id" in keys else None,
        role=row["role"],
        is_active=bool(row["is_active"]),
        email=row["email"] if "email" in keys else None,
        avatar_url=row["avatar_url"] if "avatar_url" in keys else None,
        car_number=row["car_number"] if "car_number" in keys else None,
        auth_provider=row["auth_provider"] if "auth_provider" in keys else "LOCAL",
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

class TelegramAuthRequest(BaseModel):
    init_data: str

class QuickLoginRequest(BaseModel):
    phone_number: str
    role: Optional[str] = None
    full_name: Optional[str] = None

class EmailRegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    phone_number: Optional[str] = None

class EmailLoginRequest(BaseModel):
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    id: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    car_number: Optional[str] = None
    avatar_url: Optional[str] = None

class WishlistToggleRequest(BaseModel):
    user_id: str
    property_slug: str

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

    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()

        if row:
            return map_user_row(row)

        new_id = str(uuid.uuid4())
        phone = f"+998{telegram_id % 1000000000:09d}"
        cursor.execute("""
            INSERT INTO users (id, phone_number, full_name, telegram_id, role, is_active, created_at, updated_at, auth_provider)
            VALUES (?, ?, ?, ?, 'GUEST', 1, ?, ?, 'TELEGRAM')
        """, (new_id, phone, full_name, telegram_id, now_iso, now_iso))

        cursor.execute("SELECT * FROM users WHERE id = ?", (new_id,))
        return map_user_row(cursor.fetchone())

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

            return map_user_row(row)

        new_id = str(uuid.uuid4())
        role = req.role or "GUEST"
        name = req.full_name or f"Foydalanuvchi {req.phone_number[-4:]}"
        cursor.execute("""
            INSERT INTO users (id, phone_number, full_name, role, is_active, created_at, updated_at, auth_provider)
            VALUES (?, ?, ?, ?, 1, ?, ?, 'LOCAL')
        """, (new_id, req.phone_number, name, role, now_iso, now_iso))

        cursor.execute("SELECT * FROM users WHERE id = ?", (new_id,))
        return map_user_row(cursor.fetchone())

@router.post("/register-email", response_model=UserResponse)
def register_email(req: EmailRegisterRequest):
    """
    Email va parol orqali yangi hisob yaratish (Ro'yxatdan o'tish).
    """
    email_clean = req.email.strip().lower()
    if not email_clean or "@" not in email_clean:
        raise HTTPException(status_code=400, detail="Yaroqli email manzilini kiriting")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Parol kamida 6 ta belgidan iborat bo'lishi kerak")

    now_iso = datetime.now(timezone.utc).isoformat()
    phone = req.phone_number.strip() if req.phone_number else f"+99890{random.randint(1000000, 9999999)}"
    pwd_hash = hash_password(req.password)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ushbu email manzili allaqachon ro'yxatdan o'tgan")

        new_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, phone_number, full_name, email, password_hash, role, is_active, created_at, updated_at, auth_provider)
            VALUES (?, ?, ?, ?, ?, 'GUEST', 1, ?, ?, 'LOCAL')
        """, (new_id, phone, req.full_name.strip(), email_clean, pwd_hash, now_iso, now_iso))

        cursor.execute("SELECT * FROM users WHERE id = ?", (new_id,))
        return map_user_row(cursor.fetchone())

@router.post("/login-email", response_model=UserResponse)
def login_email(req: EmailLoginRequest):
    """
    Email va parol orqali tizimga kirish (TopHand andozasidagi xavfsiz kirish).
    """
    email_clean = req.email.strip().lower()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
        row = cursor.fetchone()

        if not row:
            # Agar email topilmasa, lekin foydalanuvchi birinchi marta kiritayotgan bo'lsa yoki parol kiritgan bo'lsa
            raise HTTPException(status_code=401, detail="Email yoki parol noto'g'ri kiritildi")

        if not row["password_hash"]:
            # Google hisobi orqali ro'yxatdan o'tgan bo'lishi mumkin
            raise HTTPException(status_code=400, detail="Bu hisob Google orqali ochilgan. Iltimos, Google orqali kiring")

        if not verify_password(req.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Email yoki parol noto'g'ri kiritildi")

        return map_user_row(row)

@router.post("/google-auth", response_model=UserResponse)
def google_auth(req: GoogleAuthRequest):
    """
    Google SSO (One-Click / OAuth 2.0) orqali tizimga darhol kirish.
    Foydalanuvchi bazada bo'lmasa, avtomatik yaratiladi; bo'lsa, ma'lumotlari yangilanadi.
    """
    email_clean = req.email.strip().lower()
    now_iso = datetime.now(timezone.utc).isoformat()
    name = req.full_name.strip() if req.full_name else email_clean.split("@")[0].capitalize()
    avatar = req.avatar_url or "/static/assets/avatar.jpg"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
        row = cursor.fetchone()

        if row:
            cursor.execute("""
                UPDATE users SET full_name = ?, avatar_url = ?, auth_provider = 'GOOGLE', updated_at = ?
                WHERE id = ?
            """, (name or row["full_name"], avatar, now_iso, row["id"]))
            cursor.execute("SELECT * FROM users WHERE id = ?", (row["id"],))
            return map_user_row(cursor.fetchone())

        new_id = str(uuid.uuid4())
        phone = f"+99890{random.randint(1000000, 9999999)}"
        cursor.execute("""
            INSERT INTO users (id, phone_number, full_name, email, avatar_url, role, is_active, created_at, updated_at, auth_provider)
            VALUES (?, ?, ?, ?, ?, 'GUEST', 1, ?, ?, 'GOOGLE')
        """, (new_id, phone, name, email_clean, avatar, now_iso, now_iso))

        cursor.execute("SELECT * FROM users WHERE id = ?", (new_id,))
        return map_user_row(cursor.fetchone())

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    """
    Parolni unutganda 6 xonali tasdiqlash kodini yuborish.
    """
    email_clean = req.email.strip().lower()
    code = f"{random.randint(100000, 999999)}"
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=15)).isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
        row = cursor.fetchone()

        if not row:
            # Xavfsizlik maqsadida foydalanuvchiga email mavjud emasligini bildirmaslik mumkin,
            # ammo bu platformada qulaylik uchun xabar beramiz
            raise HTTPException(status_code=404, detail="Ushbu email bilan ro'yxatdan o'tgan hisob topilmadi")

        cursor.execute("""
            UPDATE users SET reset_code = ?, reset_code_expires_at = ? WHERE id = ?
        """, (code, expires_at, row["id"]))

    return {
        "success": True,
        "message": "Tasdiqlash kodi emailingizga yuborildi",
        "code_hint": code  # Demo va tezkor sinov uchun qaytariladi
    }

@router.post("/reset-password", response_model=UserResponse)
def reset_password(req: ResetPasswordRequest):
    """
    Tasdiqlash kodi orqali yangi parol o'rnatish.
    """
    email_clean = req.email.strip().lower()
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yangi parol kamida 6 ta belgidan iborat bo'lishi kerak")

    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        if not row["reset_code"] or row["reset_code"] != req.code.strip():
            raise HTTPException(status_code=400, detail="Kiritilgan tasdiqlash kodi noto'g'ri")

        if row["reset_code_expires_at"] and row["reset_code_expires_at"] < now_iso:
            raise HTTPException(status_code=400, detail="Tasdiqlash kodining amal qilish muddati tugagan")

        pwd_hash = hash_password(req.new_password)
        cursor.execute("""
            UPDATE users SET password_hash = ?, reset_code = NULL, reset_code_expires_at = NULL, updated_at = ?
            WHERE id = ?
        """, (pwd_hash, now_iso, row["id"]))

        cursor.execute("SELECT * FROM users WHERE id = ?", (row["id"],))
        return map_user_row(cursor.fetchone())

@router.post("/update-profile", response_model=UserResponse)
def update_profile(req: UpdateProfileRequest):
    """
    Foydalanuvchi profili ma'lumotlarini (ism, telefon, avtomobil raqami, rasm) yangilash.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (req.id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        full_name = req.full_name if req.full_name is not None else row["full_name"]
        phone = req.phone_number if req.phone_number is not None else row["phone_number"]
        car_number = req.car_number if req.car_number is not None else row["car_number"]
        avatar = req.avatar_url if req.avatar_url is not None else row["avatar_url"]

        cursor.execute("""
            UPDATE users SET full_name = ?, phone_number = ?, car_number = ?, avatar_url = ?, updated_at = ?
            WHERE id = ?
        """, (full_name, phone, car_number, avatar, now_iso, req.id))

        cursor.execute("SELECT * FROM users WHERE id = ?", (req.id,))
        return map_user_row(cursor.fetchone())

@router.post("/wishlist/toggle")
def toggle_wishlist_endpoint(req: WishlistToggleRequest):
    """
    Faqat tizimga kirgan foydalanuvchilar uchun dachalarni saqlanganlarga qo'shish yoki o'chirish.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (req.user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=401, detail="Foydalanuvchi tizimda topilmadi")

        cursor.execute("""
            SELECT id FROM user_wishlists WHERE user_id = ? AND property_slug = ?
        """, (req.user_id, req.property_slug))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("DELETE FROM user_wishlists WHERE id = ?", (existing["id"],))
            status = "removed"
        else:
            w_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO user_wishlists (id, user_id, property_slug, created_at)
                VALUES (?, ?, ?, ?)
            """, (w_id, req.user_id, req.property_slug, now_iso))
            status = "added"

        cursor.execute("SELECT property_slug FROM user_wishlists WHERE user_id = ?", (req.user_id,))
        items = [r["property_slug"] for r in cursor.fetchall()]

    return {"status": status, "slug": req.property_slug, "wishlist": items}

@router.get("/wishlist/{user_id}")
def get_user_wishlist(user_id: str):
    """
    Foydalanuvchining saqlangan dachalar ro'yxatini olish.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT property_slug FROM user_wishlists WHERE user_id = ?", (user_id,))
        items = [r["property_slug"] for r in cursor.fetchall()]
    return {"user_id": user_id, "wishlist": items}

