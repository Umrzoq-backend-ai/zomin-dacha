from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.config import settings
from app.services.telegram_bot import bot_service

router = APIRouter(prefix="/telegram", tags=["Telegram Bot & Mini App"])

class NotifyOwnerRequest(BaseModel):
    booking_id: str
    owner_telegram_id: Optional[int] = None

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Telegram Bot API Webhook Handler:
    Receives messages, callbacks, and inline button actions.
    """
    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    res = await bot_service.dispatch_update(update)
    return {"ok": True, "result": res}

@router.get("/info")
def telegram_info():
    """
    Status of the Telegram Bot & Mini App Configuration.
    """
    token_preview = f"{settings.TELEGRAM_BOT_TOKEN[:8]}...***" if settings.TELEGRAM_BOT_TOKEN else "NOT_CONFIGURED"
    return {
        "status": "online",
        "bot_configured": bool(settings.TELEGRAM_BOT_TOKEN),
        "bot_token_preview": token_preview,
        "webapp_url": settings.WEBAPP_URL,
        "webhook_url": f"{settings.WEBAPP_URL}{settings.API_V1_PREFIX}/telegram/webhook",
        "supported_features": [
            "Telegram Mini App (TMA) One-Click HMAC-SHA256 Auth",
            "Persistent Menu Button integration",
            "Caretaker Gate Check by Car Plate / Voucher Code",
            "Guest My Bookings with Offline Voucher & Navigation",
            "Host 10-minute Instant Confirmation & Automated IVR Fallback"
        ]
    }

@router.post("/notify-owner")
async def notify_owner_of_booking(req: NotifyOwnerRequest, background_tasks: BackgroundTasks):
    """
    Notifies a dacha owner in Telegram when a new booking is submitted.
    """
    from app.database import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, p.title as prop_title, p.owner_id, u.telegram_id, u.phone_number, ru.name as unit_name
            FROM bookings b
            JOIN rental_units ru ON b.rental_unit_id = ru.id
            JOIN properties p ON ru.property_id = p.id
            LEFT JOIN users u ON p.owner_id = u.id
            WHERE b.id = ?
        """, (req.booking_id,))
        b = cursor.fetchone()

    if not b:
        raise HTTPException(status_code=404, detail="Bron topilmadi")

    chat_id = req.owner_telegram_id or b["telegram_id"] or 99887766  # sample ID if not set

    text = (
        f"🔔 <b>YANGI BRON TUSHDI!</b>\n\n"
        f"🏡 <b>Dacha:</b> {b['prop_title']}\n"
        f"🛏 <b>Xona / Kottej:</b> {b['unit_name']}\n"
        f"📅 <b>Sanalar:</b> {b['checkin_time'][:10]} — {b['checkout_time'][:10]}\n"
        f"👤 <b>Mehmon:</b> {b['guest_name']}\n"
        f"📞 <b>Telefon:</b> {b['guest_phone']}\n"
        f"👥 <b>Mehmonlar:</b> {b['guest_count']} kishi\n\n"
        f"💳 <b>Avans to'landi (15%):</b> {int(b['platform_fee_amount']):,} so'm\n"
        f"💵 <b>Kelganda to'lanadi (85%):</b> {int(b['pay_on_arrival_amount']):,} so'm\n\n"
        f"<i>Iltimos, 10 daqiqa ichida bronni tasdiqlang:</i>"
    )

    buttons = {
        "inline_keyboard": [
            [
                {"text": "✅ Tasdiqlash", "callback_data": f"host_confirm_{b['id']}"},
                {"text": "❌ Rad etish", "callback_data": f"host_reject_{b['id']}"}
            ]
        ]
    }

    res = await bot_service.send_message(chat_id, text, reply_markup=buttons)
    return {"status": "dispatched", "chat_id": chat_id, "result": res}
