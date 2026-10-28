import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from app.database import get_db

IVR_DEFAULT_MESSAGE = "ZominStay: Sizda yangi bron so'rovi bor, iltimos Telegram botni tekshiring"

def dispatch_ivr_call(
    booking_id: str,
    owner_phone: str,
    owner_name: str,
    booking_reference: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Simulates automated IVR voice phone call to dacha owner (TZ 2.3 & AC-10).
    Spoken text: 'ZominStay: Sizda yangi bron so'rovi bor, iltimos Telegram botni tekshiring'
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    log_id = str(uuid.uuid4())

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ivr_call_logs (
                id, booking_id, owner_phone, call_status, spoken_message, dispatched_at
            ) VALUES (?, ?, ?, 'COMPLETED', ?, ?)
        """, (log_id, booking_id, owner_phone, IVR_DEFAULT_MESSAGE, now_iso))

    return {
        "ivr_call_id": log_id,
        "booking_id": booking_id,
        "booking_reference": booking_reference,
        "owner_name": owner_name,
        "owner_phone": owner_phone,
        "spoken_message": IVR_DEFAULT_MESSAGE,
        "call_status": "COMPLETED",
        "dispatched_at": now_iso
    }

def check_and_trigger_ivr_reminders(
    db_path: Optional[str] = None,
    delay_minutes: int = 10
) -> List[Dict[str, Any]]:
    """
    AC-10: Dacha egasi yangi bronga 10 daqiqa javob bermasa:
    IVR ovozli robot egaga telefon qilib botni tekshirishni eslatadi.
    """
    cutoff_time = (datetime.now(timezone.utc) - timedelta(minutes=delay_minutes)).isoformat()
    dispatched_calls = []

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        # Find pending bookings older than cutoff that haven't received an IVR reminder
        cursor.execute("""
            SELECT b.id as booking_id, b.booking_reference, b.created_at,
                   u.phone_number as owner_phone, u.full_name as owner_name
            FROM bookings b
            JOIN rental_units ru ON b.rental_unit_id = ru.id
            JOIN properties p ON ru.property_id = p.id
            JOIN users u ON p.owner_id = u.id
            WHERE b.booking_status = 'PENDING_OWNER'
              AND b.created_at <= ?
              AND b.id NOT IN (SELECT booking_id FROM ivr_call_logs)
            ORDER BY b.created_at ASC
        """, (cutoff_time,))

        pending_bookings = cursor.fetchall()

    for row in pending_bookings:
        call_res = dispatch_ivr_call(
            booking_id=row["booking_id"],
            owner_phone=row["owner_phone"],
            owner_name=row["owner_name"] or "Dacha Egasi",
            booking_reference=row["booking_reference"],
            db_path=db_path
        )
        dispatched_calls.append(call_res)

    return dispatched_calls

def get_ivr_logs(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns IVR reminder call dispatch history.
    """
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.*, b.booking_reference
            FROM ivr_call_logs l
            JOIN bookings b ON l.booking_id = b.id
            ORDER BY l.dispatched_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
