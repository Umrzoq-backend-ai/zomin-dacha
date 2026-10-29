import json
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from app.database import get_db
from app.models import PropertyListItem, PropertyDetailResponse, RentalUnitResponse, DayUseSlotResponse
from app.services.booking_service import lazy_invalidate_expired_holds, check_overlapping_allocation

router = APIRouter(prefix="/properties", tags=["Properties & Search"])

@router.get("", response_model=List[PropertyListItem])
def list_properties(
    micro_district: Optional[str] = Query(None, description="DUOBA, ORIKLISOY, SUFFA, SANATORIY, DASHTOBOD"),
    property_type: Optional[str] = Query(None, description="VILLA, COTTAGE, GUEST_HOUSE, CHOYXONA_TAPCHAN"),
    road_condition: Optional[str] = Query(None, description="ASPHALT_SEDAN, HIGH_CLEARANCE, 4WD_ONLY"),
    has_generator: Optional[bool] = Query(None, description="Generator bor dachalar"),
    min_guests: Optional[int] = Query(None, ge=1),
    checkin_time: Optional[str] = Query(None, description="ISO8601 format e.g. 2026-07-15T14:00:00"),
    checkout_time: Optional[str] = Query(None, description="ISO8601 format e.g. 2026-07-17T12:00:00"),
    search_query: Optional[str] = Query(None)
):
    """
    Dachalar va tapchanlarni qidirish va filtrlash (AC-11 & AC-13).
    """
    with get_db() as conn:
        lazy_invalidate_expired_holds(conn)
        cursor = conn.cursor()

        sql = "SELECT * FROM properties WHERE is_published = 1 AND verification_status = 'VERIFIED'"
        params = []

        if micro_district and micro_district.upper() != "ALL":
            sql += " AND micro_district = ?"
            params.append(micro_district.upper())

        if property_type and property_type.upper() != "ALL":
            sql += " AND property_type = ?"
            params.append(property_type.upper())

        if road_condition:
            sql += " AND road_condition = ?"
            params.append(road_condition.upper())

        if has_generator is not None:
            sql += " AND has_generator = ?"
            params.append(1 if has_generator else 0)

        if search_query:
            sql += " AND (title LIKE ? OR description LIKE ? OR address_text LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term])

        sql += " ORDER BY created_at DESC"
        cursor.execute(sql, params)
        properties = cursor.fetchall()

        result = []
        for p in properties:
            prop_id = p["id"]
            
            # Fetch units
            cursor.execute("SELECT * FROM rental_units WHERE property_id = ? AND is_active = 1", (prop_id,))
            units = cursor.fetchall()
            
            matched_units = []
            min_price = float('inf')

            for u in units:
                unit_id = u["id"]
                capacity = int(u["max_capacity"])
                
                if min_guests and capacity < min_guests:
                    continue

                # If dates are provided, check real-time availability via inventory_allocations
                if checkin_time and checkout_time:
                    if check_overlapping_allocation(conn, unit_id, checkin_time, checkout_time):
                        continue # Unit is booked, skip

                # Fetch slots if any
                cursor.execute("SELECT * FROM day_use_slots WHERE rental_unit_id = ?", (unit_id,))
                slots_rows = cursor.fetchall()
                slots = [
                    DayUseSlotResponse(
                        id=s["id"],
                        rental_unit_id=s["rental_unit_id"],
                        slot_name=s["slot_name"],
                        start_time=s["start_time"],
                        end_time=s["end_time"],
                        price_weekday=s["price_weekday"],
                        price_weekend=s["price_weekend"]
                    ) for s in slots_rows
                ]

                unit_min = min(float(u["base_price_weekday"]), float(u["base_price_weekend"]))
                if slots:
                    for s in slots:
                        unit_min = min(unit_min, s.price_weekday, s.price_weekend)

                if unit_min < min_price:
                    min_price = unit_min

                matched_units.append(
                    RentalUnitResponse(
                        id=u["id"],
                        property_id=u["property_id"],
                        name=u["name"],
                        unit_category=u["unit_category"],
                        standard_capacity=u["standard_capacity"],
                        max_capacity=u["max_capacity"],
                        base_price_weekday=u["base_price_weekday"],
                        base_price_weekend=u["base_price_weekend"],
                        is_active=bool(u["is_active"]),
                        slots=slots
                    )
                )

            # If searching with dates and no units available, skip this property
            if (checkin_time and checkout_time) and len(matched_units) == 0:
                continue

            # Fallback price if no units matched guests filter
            if min_price == float('inf'):
                min_price = 0.0

            result.append(
                PropertyListItem(
                    id=p["id"],
                    owner_id=p["owner_id"],
                    title=p["title"],
                    slug=p["slug"],
                    description=p["description"],
                    property_type=p["property_type"],
                    region=p["region"],
                    micro_district=p["micro_district"],
                    address_text=p["address_text"],
                    latitude=p["latitude"],
                    longitude=p["longitude"],
                    location_precision=p["location_precision"],
                    road_condition=p["road_condition"],
                    has_generator=bool(p["has_generator"]),
                    water_source=p["water_source"],
                    heating_type=p["heating_type"],
                    mobile_coverage=p["mobile_coverage"],
                    verification_status=p["verification_status"],
                    is_published=bool(p["is_published"]),
                    photos=json.loads(p["photos_json"] or "[]"),
                    amenities=json.loads(p["amenities_json"] or "[]"),
                    min_price=min_price,
                    rental_units=matched_units
                )
            )

        return result

@router.get("/{id_or_slug}", response_model=PropertyDetailResponse)
def get_property_detail(id_or_slug: str):
    """
    Dachaning to'liq profili, rasmlari, birliklari va qulayliklari.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, u.full_name as owner_name, u.phone_number as owner_phone
            FROM properties p
            LEFT JOIN users u ON p.owner_id = u.id
            WHERE p.id = ? OR p.slug = ?
        """, (id_or_slug, id_or_slug))
        p = cursor.fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Dacha yoki tapchan topilmadi")

        prop_id = p["id"]
        
        # Caretakers count
        cursor.execute("SELECT COUNT(*) FROM property_caretakers WHERE property_id = ?", (prop_id,))
        caretakers_count = cursor.fetchone()[0]

        # Rental Units
        cursor.execute("SELECT * FROM rental_units WHERE property_id = ? AND is_active = 1", (prop_id,))
        units_rows = cursor.fetchall()
        
        units = []
        min_price = float('inf')
        for u in units_rows:
            unit_id = u["id"]
            cursor.execute("SELECT * FROM day_use_slots WHERE rental_unit_id = ?", (unit_id,))
            slots_rows = cursor.fetchall()
            slots = [
                DayUseSlotResponse(
                    id=s["id"],
                    rental_unit_id=s["rental_unit_id"],
                    slot_name=s["slot_name"],
                    start_time=s["start_time"],
                    end_time=s["end_time"],
                    price_weekday=s["price_weekday"],
                    price_weekend=s["price_weekend"]
                ) for s in slots_rows
            ]

            unit_min = min(float(u["base_price_weekday"]), float(u["base_price_weekend"]))
            if slots:
                for s in slots:
                    unit_min = min(unit_min, s.price_weekday, s.price_weekend)

            if unit_min < min_price:
                min_price = unit_min

            units.append(
                RentalUnitResponse(
                    id=u["id"],
                    property_id=u["property_id"],
                    name=u["name"],
                    unit_category=u["unit_category"],
                    standard_capacity=u["standard_capacity"],
                    max_capacity=u["max_capacity"],
                    base_price_weekday=u["base_price_weekday"],
                    base_price_weekend=u["base_price_weekend"],
                    is_active=bool(u["is_active"]),
                    slots=slots
                )
            )

        if min_price == float('inf'):
            min_price = 0.0

        return PropertyDetailResponse(
            id=p["id"],
            owner_id=p["owner_id"],
            title=p["title"],
            slug=p["slug"],
            description=p["description"],
            property_type=p["property_type"],
            region=p["region"],
            micro_district=p["micro_district"],
            address_text=p["address_text"],
            latitude=p["latitude"],
            longitude=p["longitude"],
            location_precision=p["location_precision"],
            road_condition=p["road_condition"],
            has_generator=bool(p["has_generator"]),
            water_source=p["water_source"],
            heating_type=p["heating_type"],
            mobile_coverage=p["mobile_coverage"],
            verification_status=p["verification_status"],
            is_published=bool(p["is_published"]),
            photos=json.loads(p["photos_json"] or "[]"),
            amenities=json.loads(p["amenities_json"] or "[]"),
            min_price=min_price,
            rental_units=units,
            owner_name=p["owner_name"] or "Umrzoq (Superadmin)",
            owner_phone=p["owner_phone"] or "+998 90 123 45 67",
            caretakers_count=caretakers_count
        )
