import re
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Header

from app.database import get_db
from app.models import (
    AdminDashboardStats, AdminPropertyVerifyRequest, AdminForceCancelRequest,
    AdminUserStatusRequest, PropertyListItem, BookingDetailResponse,
    AdminLoginRequest, PropertyCreateUpdateRequest, AdminChangePasswordRequest
)
from app.services.booking_service import get_booking_detail

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

ADMIN_CREDENTIALS = {
    "password": "pdp.university"
}

def log_audit(conn, user_id: str, action: str, target_type: str, target_id: str, details: str):
    now_iso = datetime.now(timezone.utc).isoformat()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (id, user_id, action, target_type, target_id, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), user_id, action, target_type, target_id, details, now_iso))

@router.get("/dashboard-stats", response_model=AdminDashboardStats)
def get_admin_dashboard_stats():
    """
    Admin Operatsion Dashboard Metriklari (TZ 9.1):
    GMV, sof xizmat haqi komissiyasi (10%), dacha va bronlar statistikasi.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Financials
        cursor.execute("""
            SELECT 
                COALESCE(SUM(total_amount), 0) as gmv,
                COALESCE(SUM(platform_fee_amount), 0) as platform_fee
            FROM bookings
            WHERE booking_status IN ('CONFIRMED', 'CHECKED_IN', 'COMPLETED')
        """)
        fin = cursor.fetchone()
        gmv = float(fin["gmv"])
        platform_fee = float(fin["platform_fee"])

        # Bookings count
        cursor.execute("SELECT COUNT(*) FROM bookings")
        total_bookings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_status IN ('CONFIRMED', 'CHECKED_IN', 'COMPLETED')")
        confirmed_bookings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_status = 'PENDING_OWNER'")
        pending_bookings = cursor.fetchone()[0]

        # Properties
        cursor.execute("SELECT COUNT(*) FROM properties")
        total_properties = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM properties WHERE verification_status = 'VERIFIED'")
        verified_properties = cursor.fetchone()[0]

        # Users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        # IVR logs
        cursor.execute("SELECT COUNT(*) FROM ivr_call_logs")
        ivr_calls = cursor.fetchone()[0]

        return AdminDashboardStats(
            total_gmv=gmv,
            total_platform_fee=platform_fee,
            total_bookings=total_bookings,
            confirmed_bookings=confirmed_bookings,
            pending_bookings=pending_bookings,
            total_properties=total_properties,
            verified_properties=verified_properties,
            total_users=total_users,
            ivr_calls_count=ivr_calls
        )

@router.get("/properties")
def get_all_properties_admin(
    status: Optional[str] = Query(None, description="VERIFIED, PENDING, REJECTED, DRAFT"),
    micro_district: Optional[str] = None
):
    """
    Barcha dacha va maskanlar (Admin moderatsiya ro'yxati).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT p.*, u.full_name as owner_name, u.phone_number as owner_phone
            FROM properties p
            LEFT JOIN users u ON p.owner_id = u.id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND p.verification_status = ?"
            params.append(status)
        if micro_district:
            query += " AND p.micro_district = ?"
            params.append(micro_district)
        query += " ORDER BY p.created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for r in rows:
            cursor.execute("SELECT * FROM rental_units WHERE property_id = ?", (r["id"],))
            units = cursor.fetchall()
            photos = json.loads(r["photos_json"]) if r["photos_json"] else []
            cover = photos[0] if (photos and len(photos) > 0) else "/static/assets/villa.jpg"
            min_price = units[0]["base_price_weekday"] if units else 1200000.0
            capacity = units[0]["standard_capacity"] if units else 8

            results.append({
                "id": r["id"],
                "owner_id": r["owner_id"],
                "owner_name": r["owner_name"] or "Umrzoq (Superadmin)",
                "owner_phone": r["owner_phone"] or "+998 90 123 45 67",
                "cover_photo": cover,
                "min_price": min_price,
                "capacity": capacity,
                "title": r["title"],
                "slug": r["slug"],
                "description": r["description"],
                "property_type": r["property_type"],
                "micro_district": r["micro_district"],
                "address_text": r["address_text"],
                "verification_status": r["verification_status"],
                "is_published": bool(r["is_published"]),
                "road_condition": r["road_condition"],
                "has_generator": bool(r["has_generator"]),
                "water_source": r["water_source"],
                "heating_type": r["heating_type"],
                "mobile_coverage": r["mobile_coverage"],
                "units_count": len(units),
                "created_at": r["created_at"]
            })
        return results

@router.post("/properties/{property_id}/verify")
def verify_property(property_id: str, request: AdminPropertyVerifyRequest):
    """
    Dachani moderatsiyadan o'tkazish (VERIFIED yoki REJECTED, TZ 9.1).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
        p = cursor.fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Obyekt topilmadi")

        is_published = 1 if request.status == "VERIFIED" else 0
        cursor.execute("""
            UPDATE properties
            SET verification_status = ?, is_published = ?, updated_at = ?
            WHERE id = ?
        """, (request.status, is_published, datetime.now(timezone.utc).isoformat(), property_id))

        log_audit(
            conn, request.admin_id, f"PROPERTY_{request.status}",
            "PROPERTY", property_id, f"Status o'zgartirildi: {request.status}. Izoh: {request.notes or ''}"
        )

        return {
            "status": "success",
            "message": f"Obyekt holati '{request.status}' deb belgilandi.",
            "is_published": bool(is_published)
        }

@router.get("/bookings")
def get_all_bookings_admin(
    status: Optional[str] = Query(None, description="PENDING_OWNER, CONFIRMED, CHECKED_IN, CANCELLED"),
    limit: int = 50
):
    """
    Barcha bronlar monitoringi (Admin).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT id FROM bookings WHERE 1=1"
        params = []
        if status:
            query += " AND booking_status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [get_booking_detail(r["id"], current_user_role="ADMIN") for r in rows]

@router.post("/bookings/{booking_id}/force-cancel")
def admin_force_cancel_booking(booking_id: str, request: AdminForceCancelRequest):
    """
    Majburiy bekor qilish (Admin / Murojaat bo'yicha, TZ 9.2).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        b = cursor.fetchone()
        if not b:
            raise HTTPException(status_code=404, detail="Bron topilmadi")

        # Update booking
        cursor.execute("""
            UPDATE bookings
            SET booking_status = 'CANCELLED', cancellation_reason = ?, updated_at = ?
            WHERE id = ?
        """, (f"ADMIN_FORCE_CANCEL: {request.reason}", now_iso, booking_id))

        # Free inventory allocations
        cursor.execute("""
            UPDATE inventory_allocations
            SET status = 'CANCELLED'
            WHERE booking_id = ?
        """, (booking_id,))

        log_audit(
            conn, request.admin_id, "BOOKING_FORCE_CANCEL",
            "BOOKING", booking_id, f"Admin tomonidan bekor qilindi. Sabab: {request.reason}"
        )

        return {
            "status": "success",
            "booking_reference": b["booking_reference"],
            "message": "Bron admin tomonidan muvaffaqiyatli bekor qilindi va kalendar bo'shatildi."
        }

@router.get("/payments")
def get_all_payments_admin(limit: int = 50):
    """
    To'lovlar va Solishtirish (Reconciliation, TZ 9.1).
    Click va Payme tranzaksiyalari, Soliq OFD cheklari.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, b.booking_reference, b.guest_name, b.guest_phone
            FROM payment_attempts p
            JOIN bookings b ON p.booking_id = b.id
            ORDER BY p.created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

@router.get("/users")
def get_all_users_admin(role: Optional[str] = None):
    """
    Barcha foydalanuvchilar va rollar boshqaruvi (Admin).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE 1=1"
        params = []
        if role:
            query += " AND role = ?"
            params.append(role)
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

@router.post("/users/{user_id}/status")
def update_user_status_admin(user_id: str, request: AdminUserStatusRequest):
    """
    Foydalanuvchini bloklash / faollashtirish yoki rolni o'zgartirish (Admin).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        u = cursor.fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        new_role = request.role if request.role else u["role"]
        is_active_val = 1 if request.is_active else 0

        cursor.execute("""
            UPDATE users
            SET is_active = ?, role = ?, updated_at = ?
            WHERE id = ?
        """, (is_active_val, new_role, now_iso, user_id))

        log_audit(
            conn, request.admin_id, "USER_STATUS_CHANGE",
            "USER", user_id, f"Faollik: {request.is_active}, Rol: {new_role}"
        )

        return {
            "status": "success",
            "user_id": user_id,
            "is_active": request.is_active,
            "role": new_role
        }

@router.post("/auth/login")
def admin_login(req: AdminLoginRequest):
    """
    Maxfiy Superadmin Kirish (Umrzoq / pdp.university).
    """
    clean_user = req.username.strip().lower()
    valid_usernames = ["umrzoq", "admin", "school21dev", "umrzoq972@gmail.com", "school21dev@example.com"]
    
    if clean_user in valid_usernames and req.password.strip() == ADMIN_CREDENTIALS["password"]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE role = 'ADMIN' LIMIT 1")
            admin_user = cursor.fetchone()
            now_iso = datetime.now(timezone.utc).isoformat()
            if not admin_user:
                admin_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO users (id, phone_number, full_name, role, is_active, created_at, updated_at)
                    VALUES (?, '+998901234567', 'Umrzoq (Superadmin)', 'ADMIN', 1, ?, ?)
                """, (admin_id, now_iso, now_iso))
            else:
                admin_id = admin_user["id"]

        session_token = f"admin_sec_{uuid.uuid4().hex}"
        return {
            "ok": True,
            "token": session_token,
            "user": {
                "id": admin_id,
                "name": "Umrzoq",
                "role": "ADMIN",
                "phone": "+998 90 123 45 67",
                "email": "umrzoq972@gmail.com"
            },
            "message": "Superadmin xush kelibsiz!"
        }

    raise HTTPException(status_code=401, detail="Login yoki parol noto'g'ri! Iltimos, qaytadan tekshiring.")

@router.post("/auth/change-password")
def admin_change_password(req: AdminChangePasswordRequest):
    """
    Superadmin parolini yangilash.
    """
    if req.current_password.strip() != ADMIN_CREDENTIALS["password"]:
        raise HTTPException(status_code=400, detail="Joriy parol noto'g'ri kiritildi!")
    if len(req.new_password.strip()) < 6:
        raise HTTPException(status_code=400, detail="Yangi parol kamida 6 ta belgidan iborat bo'lishi shart!")
    ADMIN_CREDENTIALS["password"] = req.new_password.strip()
    return {"ok": True, "message": "Parol muvaffaqiyatli o'zgartirildi!"}

@router.get("/auth/check")
def admin_auth_check(authorization: Optional[str] = Header(None)):
    """
    Superadmin sessiya tokenini tekshirish.
    """
    if authorization and authorization.startswith("Bearer admin_sec_"):
        return {"authenticated": True, "user": {"name": "Umrzoq", "role": "ADMIN"}}
    return {"authenticated": False}

@router.get("/audit-logs")
def get_audit_logs_admin(limit: int = 50):
    """
    Audit va xavfsizlik jurnali (TZ 9.2).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]

@router.post("/properties")
def create_property_admin(req: PropertyCreateUpdateRequest):
    """
    Yangi dacha / e'lon joylash (Admin orqali to'g'ridan-to'g'ri saytga chiqarish).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        prop_id = f"prop_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Ensure owner user exists
        owner_phone = req.owner_phone or "+998901234567"
        owner_name = req.owner_name or "Dacha Egasi"
        cursor.execute("SELECT id FROM users WHERE phone_number = ? LIMIT 1", (owner_phone,))
        owner = cursor.fetchone()
        if owner:
            owner_id = owner["id"]
        else:
            owner_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, phone_number, full_name, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 'OWNER', 1, ?, ?)
            """, (owner_id, owner_phone, owner_name, now_iso, now_iso))

        # Generate unique URL slug
        base_slug = re.sub(r'[^a-z0-9]+', '-', req.title.lower()).strip('-')
        slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

        photos = req.photos if (req.photos and len(req.photos) > 0) else ["/static/assets/villa.jpg"]
        amenities = req.amenities if (req.amenities and len(req.amenities) > 0) else [
            "Filtrli Hovuz", "Wi-Fi 5G", "Playstation", "Archa tandiri", "Mangal"
        ]

        coords = {
            "DUOBA": (39.7350, 68.4200),
            "SUFFA": (39.6800, 68.4400),
            "ORIKLISOY": (39.7100, 68.4100),
            "SANATORIY": (39.7200, 68.4250),
            "DASHTOBOD": (39.9500, 68.3500)
        }
        lat, lon = coords.get(req.micro_district.upper(), (39.7250, 68.4200))

        cursor.execute("""
            INSERT INTO properties (
                id, owner_id, title, slug, description, property_type,
                region, micro_district, address_text, latitude, longitude,
                location_precision, road_condition, has_generator, water_source,
                heating_type, mobile_coverage, verification_status, is_published,
                photos_json, amenities_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'ZOMIN', ?, ?, ?, ?, 'EXACT', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prop_id, owner_id, req.title, slug, req.description, req.property_type,
            req.micro_district.upper(), req.address_text, lat, lon,
            req.road_condition, 1 if req.has_generator else 0, req.water_source,
            req.heating_type, req.mobile_coverage, req.verification_status,
            1 if req.is_published else 0, json.dumps(photos), json.dumps(amenities),
            now_iso, now_iso
        ))

        unit_id = f"unit_{uuid.uuid4().hex[:12]}"
        weekend_price = req.base_price_weekend or (req.base_price_weekday * 1.25)
        cursor.execute("""
            INSERT INTO rental_units (
                id, property_id, name, unit_category, standard_capacity,
                max_capacity, base_price_weekday, base_price_weekend, is_active, created_at
            ) VALUES (?, ?, ?, 'OVERNIGHT_STAY', ?, ?, ?, ?, 1, ?)
        """, (
            unit_id, prop_id, f"{req.title} Asosiy Bino",
            req.standard_capacity, req.max_capacity, req.base_price_weekday,
            weekend_price, now_iso
        ))

        if req.day_use_price and req.day_use_price > 0:
            slot_id = f"slot_{uuid.uuid4().hex[:12]}"
            cursor.execute("""
                INSERT INTO day_use_slots (
                    id, rental_unit_id, slot_name, start_time, end_time, price_weekday, price_weekend
                ) VALUES (?, ?, 'FULL_DAY', '10:00', '22:00', ?, ?)
            """, (slot_id, unit_id, req.day_use_price, req.day_use_price * 1.2))

        log_audit(conn, "admin_umrzoq", "PROPERTY_CREATE", "PROPERTY", prop_id, f"Yangi dacha yaratildi: {req.title}")

        return {
            "ok": True,
            "id": prop_id,
            "slug": slug,
            "title": req.title,
            "message": "Dacha muvaffaqiyatli saqlandi va saytga joylandi!"
        }

@router.get("/properties/{property_id}/full")
def get_property_admin_full(property_id: str):
    """
    Dachaning barcha tahrirlanadigan ma'lumotlarini olish (Edit modal uchun).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, u.full_name as owner_name, u.phone_number as owner_phone
            FROM properties p
            LEFT JOIN users u ON p.owner_id = u.id
            WHERE p.id = ?
        """, (property_id,))
        p = cursor.fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Dacha topilmadi")

        cursor.execute("SELECT * FROM rental_units WHERE property_id = ? LIMIT 1", (property_id,))
        unit = cursor.fetchone()

        photos = json.loads(p["photos_json"]) if p["photos_json"] else []
        amenities = json.loads(p["amenities_json"]) if p["amenities_json"] else []

        return {
            "id": p["id"],
            "title": p["title"],
            "description": p["description"] or "",
            "property_type": p["property_type"],
            "micro_district": p["micro_district"],
            "address_text": p["address_text"],
            "road_condition": p["road_condition"],
            "has_generator": bool(p["has_generator"]),
            "water_source": p["water_source"],
            "heating_type": p["heating_type"],
            "mobile_coverage": p["mobile_coverage"],
            "verification_status": p["verification_status"],
            "is_published": bool(p["is_published"]),
            "photos": photos,
            "amenities": amenities,
            "base_price_weekday": unit["base_price_weekday"] if unit else 1200000.0,
            "base_price_weekend": unit["base_price_weekend"] if unit else 1500000.0,
            "standard_capacity": unit["standard_capacity"] if unit else 8,
            "max_capacity": unit["max_capacity"] if unit else 12,
            "owner_name": p["owner_name"] or "Dacha Egasi",
            "owner_phone": p["owner_phone"] or "+998 90 123 45 67"
        }

@router.put("/properties/{property_id}")
def update_property_admin(property_id: str, req: PropertyCreateUpdateRequest):
    """
    Dacha ma'lumotlarini tahrirlash va saqlash.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
        p = cursor.fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Dacha topilmadi")

        now_iso = datetime.now(timezone.utc).isoformat()
        photos = req.photos if (req.photos and len(req.photos) > 0) else (json.loads(p["photos_json"]) if p["photos_json"] else [])
        amenities = req.amenities if (req.amenities and len(req.amenities) > 0) else (json.loads(p["amenities_json"]) if p["amenities_json"] else [])

        cursor.execute("""
            UPDATE properties
            SET title = ?, description = ?, property_type = ?, micro_district = ?,
                address_text = ?, road_condition = ?, has_generator = ?,
                verification_status = ?, is_published = ?,
                photos_json = ?, amenities_json = ?, updated_at = ?
            WHERE id = ?
        """, (
            req.title, req.description, req.property_type, req.micro_district.upper(),
            req.address_text, req.road_condition, 1 if req.has_generator else 0,
            req.verification_status, 1 if req.is_published else 0,
            json.dumps(photos), json.dumps(amenities), now_iso, property_id
        ))

        if req.owner_phone and p["owner_id"]:
            cursor.execute("""
                UPDATE users SET full_name = ?, phone_number = ?, updated_at = ?
                WHERE id = ?
            """, (req.owner_name or "Dacha Egasi", req.owner_phone, now_iso, p["owner_id"]))

        cursor.execute("""
            UPDATE rental_units
            SET standard_capacity = ?, max_capacity = ?,
                base_price_weekday = ?, base_price_weekend = ?
            WHERE property_id = ?
        """, (
            req.standard_capacity, req.max_capacity,
            req.base_price_weekday, req.base_price_weekend or (req.base_price_weekday * 1.25),
            property_id
        ))

        log_audit(conn, "admin_umrzoq", "PROPERTY_UPDATE", "PROPERTY", property_id, f"Dacha yangilandi: {req.title}")

        return {
            "ok": True,
            "id": property_id,
            "message": "Dacha ma'lumotlari muvaffaqiyatli yangilandi!"
        }

@router.delete("/properties/{property_id}")
def delete_property_admin(property_id: str):
    """
    Dachani tizimdan o'chirish (Admin).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM properties WHERE id = ?", (property_id,))
        p = cursor.fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Dacha topilmadi")

        cursor.execute("DELETE FROM rental_units WHERE property_id = ?", (property_id,))
        cursor.execute("DELETE FROM properties WHERE id = ?", (property_id,))
        log_audit(conn, "admin_umrzoq", "PROPERTY_DELETE", "PROPERTY", property_id, f"Dacha o'chirildi: {p['title']}")

        return {"ok": True, "message": f"'{p['title']}' muvaffaqiyatli o'chirildi."}
