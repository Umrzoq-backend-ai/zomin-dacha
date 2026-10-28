from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException

from app.config import settings
from app.database import get_db
from app.models import QuoteRequest, QuoteResponse, QuoteBreakdown
from app.security import create_quote_token
from app.services.booking_service import normalize_datetime_input, UZ_TZ

def calculate_quote(request: QuoteRequest, db_path: Optional[str] = None) -> QuoteResponse:
    try:
        checkin_dt = normalize_datetime_input(request.checkin_time)
        checkout_dt = normalize_datetime_input(request.checkout_time)
        if checkout_dt <= checkin_dt:
            raise HTTPException(status_code=400, detail="Ketish vaqti kirish vaqtidan keyin bo'lishi shart")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Sanalar ISO8601 formatida bo'lishi shart")

    checkin_local = checkin_dt.astimezone(UZ_TZ)
    checkout_local = checkout_dt.astimezone(UZ_TZ)

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM rental_units WHERE id = ? AND is_active = 1", (request.rental_unit_id,))
        unit = cursor.fetchone()
        if not unit:
            raise HTTPException(status_code=404, detail="Bunday turar joy birligi (rental unit) topilmadi")

        unit_category = unit["unit_category"]
        accommodation_total = 0.0
        units_count = 1

        if unit_category == "OVERNIGHT_STAY":
            # Count nights in Uzbekistan local time
            nights = (checkout_local.date() - checkin_local.date()).days
            if nights < 1:
                nights = 1  # Minimum 1 night
            units_count = nights
            
            # Calculate price per night based on weekday (Mon-Thu: 0,1,2,3) vs weekend (Fri-Sun: 4,5,6)
            current_date = checkin_local.date()
            for _ in range(nights):
                weekday = current_date.weekday()
                if weekday in (4, 5, 6): # Friday, Saturday, Sunday
                    accommodation_total += float(unit["base_price_weekend"])
                else: # Monday - Thursday
                    accommodation_total += float(unit["base_price_weekday"])
                current_date += timedelta(days=1)
                
            booking_type = "OVERNIGHT"

        else: # DAY_USE_TAPCHAN
            weekday = checkin_local.date().weekday()
            is_weekend = weekday in (4, 5, 6)
            
            if request.day_use_slot_name:
                cursor.execute("""
                    SELECT * FROM day_use_slots 
                    WHERE rental_unit_id = ? AND slot_name = ?
                """, (request.rental_unit_id, request.day_use_slot_name))
                slot = cursor.fetchone()
                if slot:
                    accommodation_total = float(slot["price_weekend"] if is_weekend else slot["price_weekday"])
                else:
                    accommodation_total = float(unit["base_price_weekend"] if is_weekend else unit["base_price_weekday"])
            else:
                accommodation_total = float(unit["base_price_weekend"] if is_weekend else unit["base_price_weekday"])
            
            units_count = 1
            booking_type = "DAY_USE"

        # Tandir pre-order
        tandir_kg = max(0.0, float(request.tandir_preorder_kg or 0.0))
        tandir_meat_total = round(tandir_kg * settings.TANDIR_PRICE_PER_KG, 2)

        grand_total = accommodation_total + tandir_meat_total
        platform_fee_percent = settings.PLATFORM_FEE_PERCENTAGE / 100.0
        platform_fee = round(grand_total * platform_fee_percent, 2)
        payable_on_arrival = round(grand_total - platform_fee, 2)

        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

        payload = {
            "rental_unit_id": request.rental_unit_id,
            "checkin_time": checkin_dt.isoformat(),
            "checkout_time": checkout_dt.isoformat(),
            "guests_count": request.guests_count,
            "booking_type": booking_type,
            "day_use_slot_name": request.day_use_slot_name,
            "tandir_preorder_kg": tandir_kg,
            "accommodation_total": accommodation_total,
            "tandir_meat_total": tandir_meat_total,
            "grand_total": grand_total,
            "platform_fee_online": platform_fee,
            "payable_on_arrival": payable_on_arrival,
            "expires_at": expires_at,
        }

        quote_token = create_quote_token(payload)

        return QuoteResponse(
            quote_token=quote_token,
            expires_at=expires_at,
            nights_or_days=units_count,
            booking_type=booking_type,
            breakdown=QuoteBreakdown(
                accommodation_total=accommodation_total,
                tandir_meat_total=tandir_meat_total,
                grand_total=grand_total,
                platform_fee_online=platform_fee,
                payable_on_arrival_to_owner=payable_on_arrival
            )
        )
