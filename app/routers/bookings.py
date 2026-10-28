import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query

from app.database import get_db
from app.models import (
    BookingCreateRequest, BookingResponse, BookingDetailResponse,
    ReviewCreateRequest, ReviewResponse
)
from app.services.booking_service import (
    create_booking, get_booking_detail, check_in_guest, complete_booking
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("/create", response_model=BookingResponse, status_code=201)
def api_create_booking(
    request: BookingCreateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Bron yaratish (Idempotent, TZ 5.2.2):
    15 daqiqalik hold va to'qnashuvga qarshi exclusion himoyasi.
    """
    return create_booking(request, idempotency_key=idempotency_key)

@router.get("/{id_or_ref}", response_model=BookingDetailResponse)
def api_get_booking(
    id_or_ref: str,
    user_role: Optional[str] = Query("GUEST", description="GUEST, OWNER, CARETAKER, ADMIN")
):
    """
    Bron tafsilotlarini olish.
    Agar rolingiz CARETAKER (bog'bon) bo'lsa, moliyaviy ma'lumotlar yashiriladi (AC-14).
    """
    return get_booking_detail(id_or_ref, current_user_role=user_role)

@router.post("/{booking_id}/check-in")
def api_check_in_guest(
    booking_id: str,
    user_id: str = Query(..., description="Ega yoki Qarovchining User ID si"),
    user_role: str = Query("CARETAKER", description="CARETAKER yoki OWNER")
):
    """
    Mehmon yetib kelganda kalit topshirish va kutib olish (AC-14).
    """
    return check_in_guest(booking_id, user_id=user_id, user_role=user_role)

@router.post("/{booking_id}/complete")
def api_complete_booking(
    booking_id: str,
    user_id: str = Query(..., description="Foydalanuvchi yoki Ega ID si")
):
    """
    Safar yakunlangach bronni COMPLETED holatiga o'tkazish (AC-16).
    """
    return complete_booking(booking_id, user_id=user_id)

@router.post("/{booking_id}/reviews", response_model=ReviewResponse, status_code=201)
def create_review(booking_id: str, request: ReviewCreateRequest):
    """
    Faqat haqiqatda tashrif buyurgan va safarni yakunlagan mehmondan 5 mezonli sharh (AC-16).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        b = cursor.fetchone()
        if not b:
            raise HTTPException(status_code=404, detail="Bron topilmadi")

        if b["booking_status"] != "COMPLETED":
            raise HTTPException(status_code=400, detail="Faqat yakunlangan (COMPLETED) safar bo'yicha sharh qoldirish mumkin (AC-16)")

        # Check existing review
        cursor.execute("SELECT id FROM reviews WHERE booking_id = ?", (booking_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ushbu safar uchun allaqachon sharh qoldirilgan")

        cursor.execute("""
            SELECT u.property_id FROM rental_units u WHERE u.id = ?
        """, (b["rental_unit_id"],))
        prop = cursor.fetchone()
        prop_id = prop["property_id"] if prop else ""

        overall = round(
            (request.rating_cleanliness + request.rating_accuracy + request.rating_communication + request.rating_comfort) / 4.0,
            2
        )

        review_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO reviews (
                id, booking_id, property_id, guest_id,
                rating_cleanliness, rating_accuracy, rating_communication, rating_comfort,
                overall_rating, comment, is_verified_stay, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            review_id, booking_id, prop_id, b["guest_id"],
            request.rating_cleanliness, request.rating_accuracy, request.rating_communication,
            request.rating_comfort, overall, request.comment or "", now_iso
        ))

        return ReviewResponse(
            id=review_id,
            property_id=prop_id,
            guest_name=b["guest_name"],
            rating_cleanliness=request.rating_cleanliness,
            rating_accuracy=request.rating_accuracy,
            rating_communication=request.rating_communication,
            rating_comfort=request.rating_comfort,
            overall_rating=overall,
            comment=request.comment,
            owner_reply=None,
            created_at=now_iso
        )

@router.get("/property/{property_id}/reviews", response_model=List[ReviewResponse])
def get_property_reviews(property_id: str):
    """
    Dacha bo'yicha tasdiqlangan sharhlar ro'yxati.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, b.guest_name 
            FROM reviews r
            JOIN bookings b ON r.booking_id = b.id
            WHERE r.property_id = ?
            ORDER BY r.created_at DESC
        """, (property_id,))
        rows = cursor.fetchall()
        return [
            ReviewResponse(
                id=row["id"],
                property_id=row["property_id"],
                guest_name=row["guest_name"],
                rating_cleanliness=row["rating_cleanliness"],
                rating_accuracy=row["rating_accuracy"],
                rating_communication=row["rating_communication"],
                rating_comfort=row["rating_comfort"],
                overall_rating=row["overall_rating"],
                comment=row["comment"],
                owner_reply=row["owner_reply"],
                created_at=row["created_at"]
            ) for row in rows
        ]
