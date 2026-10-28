import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_db
from app.models import BookingDetailResponse
from app.services.booking_service import owner_transition_booking, lazy_invalidate_expired_holds, check_overlapping_allocation

router = APIRouter(prefix="/owner", tags=["Owner & Caretaker Operations"])

class OwnerBookingTransitionRequest(BaseModel):
    action: str  # 'ACCEPT' or 'REJECT'
    rejection_reason: Optional[str] = None

class ManualBlockRequest(BaseModel):
    rental_unit_id: str
    owner_id: str
    start_time: str
    end_time: str
    notes: Optional[str] = None

@router.get("/properties")
def list_owner_properties(owner_id: str = Query(...)):
    """
    Eganing o'z dachalarini ko'rish.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM properties WHERE owner_id = ?", (owner_id,))
        properties = cursor.fetchall()
        
        result = []
        for p in properties:
            cursor.execute("SELECT * FROM rental_units WHERE property_id = ?", (p["id"],))
            units = [dict(u) for u in cursor.fetchall()]
            
            p_dict = dict(p)
            p_dict["rental_units"] = units
            result.append(p_dict)
            
        return result

@router.get("/bookings")
def list_owner_bookings(owner_id: str = Query(...)):
    """
    Dacha egasiga kelgan barcha bron so'rovlari va tasdiqlangan buyurtmalar ro'yxati.
    """
    with get_db() as conn:
        lazy_invalidate_expired_holds(conn)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.*, u.name as unit_name, p.title as property_title, p.micro_district
            FROM bookings b
            JOIN rental_units u ON b.rental_unit_id = u.id
            JOIN properties p ON u.property_id = p.id
            WHERE p.owner_id = ?
            ORDER BY b.created_at DESC
        """, (owner_id,))
        
        return [dict(row) for row in cursor.fetchall()]

@router.post("/bookings/{booking_id}/transition")
def transition_booking_status(
    booking_id: str,
    req: OwnerBookingTransitionRequest,
    owner_id: str = Query(..., description="Dacha egasining User ID si")
):
    """
    Ega bronni qabul qilishi yoki rad etishi (BOLA himoyasi AC-07).
    """
    return owner_transition_booking(
        booking_id=booking_id,
        action=req.action.upper(),
        owner_id=owner_id,
        rejection_reason=req.rejection_reason
    )

@router.post("/calendar/block")
def manual_calendar_block(req: ManualBlockRequest):
    """
    Ega o'z kalendarini tezkor yopishi (masalan, telefon orqali tanishiga berganda yoki ta'mirda).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        lazy_invalidate_expired_holds(conn)

        # BOLA protection
        cursor.execute("""
            SELECT p.owner_id 
            FROM rental_units u
            JOIN properties p ON u.property_id = p.id
            WHERE u.id = ?
        """, (req.rental_unit_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Birlik topilmadi")

        if row["owner_id"] != req.owner_id:
            raise HTTPException(status_code=403, detail="BOLA cheklovi: Siz ushbu dacha egasi emassiz")

        if check_overlapping_allocation(conn, req.rental_unit_id, req.start_time, req.end_time):
            raise HTTPException(status_code=409, detail="Tanlangan sanada allaqachon faol bron mavjud")

        alloc_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO inventory_allocations (
                id, rental_unit_id, booking_id, allocation_type, start_time, end_time,
                status, expires_at, created_at
            ) VALUES (?, ?, NULL, 'OWNER_MANUAL', ?, ?, 'ACTIVE', NULL, ?)
        """, (alloc_id, req.rental_unit_id, req.start_time, req.end_time, now_iso))

        return {"status": "SUCCESS", "message": "Kalendar sanasi muvaffaqiyatli yopildi"}

@router.get("/caretaker/arrivals", response_model=List[BookingDetailResponse])
def get_caretaker_arrivals(caretaker_id: str = Query(...)):
    """
    AC-14: Bog'bon (Qarovchi) portali:
    Faqat biriktirilgan dachalar bo'yicha mehmon ismi, telefoni, mashina raqami va kelish vaqti ko'rinadi.
    BARCHA MOLIYAVIY RAQAMLAR (NARXLAR, DAROMAD) QAT'IY YASHIRILADI.
    """
    with get_db() as conn:
        lazy_invalidate_expired_holds(conn)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE id = ? OR telegram_id = ? OR phone_number = ?", (caretaker_id, caretaker_id, caretaker_id))
        user_row = cursor.fetchone()
        actual_cid = user_row["id"] if user_row else caretaker_id

        cursor.execute("""
            SELECT b.*, u.name as unit_name, p.id as property_id, p.title as property_title,
                   p.micro_district, p.property_type,
                   f.quantity_kg as tandir_kg, f.total_food_amount as tandir_amount,
                   pay.fiscal_receipt_url
            FROM bookings b
            JOIN rental_units u ON b.rental_unit_id = u.id
            JOIN properties p ON u.property_id = p.id
            JOIN property_caretakers c ON p.id = c.property_id
            LEFT JOIN booking_food_orders f ON b.id = f.booking_id
            LEFT JOIN payment_attempts pay ON b.id = pay.booking_id AND pay.status = 'SUCCESS'
            WHERE c.caretaker_id = ? AND b.booking_status IN ('CONFIRMED', 'CHECKED_IN')
            ORDER BY b.checkin_time ASC
        """, (actual_cid,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(
                BookingDetailResponse(
                    id=row["id"],
                    booking_reference=row["booking_reference"],
                    rental_unit_id=row["rental_unit_id"],
                    unit_name=row["unit_name"],
                    property_id=row["property_id"],
                    property_title=row["property_title"],
                    micro_district=row["micro_district"],
                    property_type=row["property_type"],
                    guest_id=row["guest_id"],
                    guest_name=row["guest_name"],
                    guest_phone=row["guest_phone"],
                    car_plate=row["car_plate"],
                    booking_type=row["booking_type"],
                    checkin_time=row["checkin_time"],
                    checkout_time=row["checkout_time"],
                    guest_count=row["guest_count"],
                    currency=row["currency"],
                    unit_base_amount=None,        # AC-14: strictly masked
                    platform_fee_amount=None,     # AC-14: strictly masked
                    pay_on_arrival_amount=None,   # AC-14: strictly masked
                    total_amount=None,            # AC-14: strictly masked
                    booking_status=row["booking_status"],
                    hold_expires_at=row["hold_expires_at"],
                    cancellation_reason=row["cancellation_reason"],
                    created_at=row["created_at"],
                    tandir_preorder_kg=float(row["tandir_kg"] or 0.0),
                    tandir_amount=0.0,            # AC-14: strictly masked
                    fiscal_receipt_url=None
                )
            )
        return results
