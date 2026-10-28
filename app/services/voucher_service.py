import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException

from app.database import get_db
from app.models import OfflineVoucher, VoucherNavigation

ROAD_ADVICE_MAP = {
    "ASPHALT_SEDAN": "Yo'l to'liq asfalt qilingan. Spark, Cobalt, Gentra va boshqa barcha yengil avtomobillar bemalol yetib boradi.",
    "HIGH_CLEARANCE": "Tog' shag'al yo'li. Baland klirensli Tracker, Malibu, Kaptiva yoki krossoverlar tavsiya etiladi. Past osilgan mashinalar ehtiyotkorlik bilan yurishi lozim.",
    "4WD_ONLY": "Tik tog' qiyaliklari. Faqat 4x4 to'liq uzatmali avtomobillar (Niva, UAZ, SUV) chiqishi mumkin.",
    "WINTER_CHAINS": "Qish mavsumida qor va muzlama. G'ildiraklarga zanjir (seplar) taqish shart."
}

def generate_offline_voucher(booking_reference_or_id: str, db_path: Optional[str] = None) -> OfflineVoucher:
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.*, u.name as unit_name, p.*,
                   ow.full_name as owner_name, ow.phone_number as owner_phone,
                   f.quantity_kg as tandir_kg, f.total_food_amount as tandir_amount,
                   c.notes as caretaker_notes,
                   cu.full_name as caretaker_name, cu.phone_number as caretaker_phone
            FROM bookings b
            JOIN rental_units u ON b.rental_unit_id = u.id
            JOIN properties p ON u.property_id = p.id
            JOIN users ow ON p.owner_id = ow.id
            LEFT JOIN booking_food_orders f ON b.id = f.booking_id
            LEFT JOIN property_caretakers c ON p.id = c.property_id
            LEFT JOIN users cu ON c.caretaker_id = cu.id
            WHERE b.id = ? OR b.booking_reference = ?
        """, (booking_reference_or_id, booking_reference_or_id))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Vaucher uchun bron topilmadi")

        lat = float(row["latitude"])
        lon = float(row["longitude"])
        title = row["title"]
        micro_dist = row["micro_district"]
        road_cond = row["road_condition"]

        # Turn by turn directions tailored to Zomin geography
        if micro_dist == "DUOBA":
            directions = f"Dashtobod stansiyasidan Zomin markaziga (25 km), so'ng Duoba MFY tomon (18 km) harakatlaning. Duoba markaziy ko'prigidan o'tgach, so'l tarafdagi archazor ichki ko'chasiga buriling. 300 metr yuqoriga yurgach: {row['address_text']}."
        elif micro_dist == "SUFFA":
            directions = f"Zomin shahar markazidan Suffa platosi (2400 m) tomon tog' serpantini bo'ylab ko'tariling. Bartholet Shveysariya osma dor yo'li (2.1 km) pastki stansiyasidan 1.2 km o'tgach, {row['address_text']} ga yetasiz."
        elif micro_dist == "ORIKLISOY":
            directions = f"Zomin tuman markazidan O'riklisoy dam olish hududiga qarab buriling. Shifobaxsh buloqlar so'qmog'i bo'ylab 2 km tog' ichiga yuring: {row['address_text']}."
        else:
            directions = f"Zomin tumani, {micro_dist} hududi bo'ylab harakatlaning. Manzil: {row['address_text']}."

        geo_uri = f"geo:{lat},{lon}?q={lat},{lon}({title.replace(' ', '+')})"
        yandex_maps = f"yandexmaps://build_route_on_map?lat_to={lat}&lon_to={lon}"
        google_maps = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

        tandir_info = None
        if row["tandir_kg"] and float(row["tandir_kg"]) > 0:
            tandir_info = f"{row['tandir_kg']} kg Zomin archa tandiri ({int(row['tandir_amount']):,} so'm) — safar vaqtiga tayyor qilinadi."

        qr_text = f"ZOMINSTAY:{row['booking_reference']}:{row['guest_phone']}:{row['checkin_time'][:10]}"

        return OfflineVoucher(
            booking_reference=row["booking_reference"],
            booking_status=row["booking_status"],
            property_title=title,
            micro_district=micro_dist,
            address_text=row["address_text"],
            road_condition=road_cond,
            road_condition_advice=ROAD_ADVICE_MAP.get(road_cond, "Ehtiyotkorlik bilan harakatlaning."),
            has_generator=bool(row["has_generator"]),
            water_source=row["water_source"],
            mobile_coverage=row["mobile_coverage"],
            guest_name=row["guest_name"],
            guest_phone=row["guest_phone"],
            car_plate=row["car_plate"],
            guest_count=row["guest_count"],
            checkin_time=row["checkin_time"],
            checkout_time=row["checkout_time"],
            owner_phone=row["owner_phone"],
            owner_name=row["owner_name"],
            caretaker_phone=row["caretaker_phone"] or "+998917778899",
            caretaker_name=row["caretaker_name"] or "Rustam Tog'a (Qarovchi)",
            payable_on_arrival_to_owner=float(row["pay_on_arrival_amount"]),
            step_by_step_directions=directions,
            navigation=VoucherNavigation(
                geo_uri=geo_uri,
                yandex_maps_url=yandex_maps,
                google_maps_url=google_maps,
                latitude=lat,
                longitude=lon
            ),
            tandir_order=tandir_info,
            offline_qr_data=qr_text
        )
