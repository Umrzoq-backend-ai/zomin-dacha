import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from app.database import get_db
from app.models import (
    AdminDashboardStats, AdminPropertyVerifyRequest, AdminForceCancelRequest,
    AdminUserStatusRequest, PropertyListItem, BookingDetailResponse
)
from app.services.booking_service import get_booking_detail

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

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
        query = "SELECT * FROM properties WHERE 1=1"
        params = []
        if status:
            query += " AND verification_status = ?"
            params.append(status)
        if micro_district:
            query += " AND micro_district = ?"
            params.append(micro_district)
        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for r in rows:
            cursor.execute("SELECT * FROM rental_units WHERE property_id = ?", (r["id"],))
            units = cursor.fetchall()
            results.append({
                "id": r["id"],
                "owner_id": r["owner_id"],
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

@router.get("/audit-logs")
def get_audit_logs_admin(limit: int = 50):
    """
    Audit va xavfsizlik jurnali (TZ 9.2).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
