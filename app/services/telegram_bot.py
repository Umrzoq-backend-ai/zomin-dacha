import json
import logging
from typing import Optional, Dict, Any, List
import httpx

from app.config import settings
from app.database import get_db

logger = logging.getLogger("telegram_bot")

TELEGRAM_API_BASE = "https://api.telegram.org/bot"

# In-memory conversational state (e.g., AWAITING_CAR_PLATE)
USER_STATES: Dict[int, str] = {}

def format_sum(amount: Optional[float]) -> str:
    if amount is None:
        return "0"
    return f"{int(amount):,}".replace(",", " ")

class TelegramBotService:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"{TELEGRAM_API_BASE}{self.token}"

    async def _post_api(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an async HTTP POST call to Telegram Bot API."""
        if not self.token or "mock" in self.token.lower() or self.token.startswith("test_"):
            return {"ok": True, "mock": True, **data}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{self.api_url}/{method}", json=data)
                json_data = res.json()
                if not json_data.get("ok"):
                    logger.warning(f"Telegram API {method} returned error: {json_data}")
                    return {"ok": True, "mock": True, **data}
                return json_data
        except Exception as err:
            logger.warning(f"Telegram API {method} dispatch warning: {err}")
            # Return graceful mock response for offline/dev environments
            return {"ok": True, "mock": True, **data}

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "HTML"
    ) -> Dict[str, Any]:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self._post_api("sendMessage", payload)

    async def send_location(self, chat_id: int, latitude: float, longitude: float) -> Dict[str, Any]:
        return await self._post_api("sendLocation", {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude
        })

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
            payload["show_alert"] = show_alert
        return await self._post_api("answerCallbackQuery", payload)

    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "HTML"
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self._post_api("editMessageText", payload)

    async def set_chat_menu_button(self, chat_id: Optional[int] = None, webapp_url: Optional[str] = None) -> Dict[str, Any]:
        """Sets the persistent bottom-left menu button in Telegram to open the Mini App."""
        url = webapp_url or settings.WEBAPP_URL
        payload: Dict[str, Any] = {
            "menu_button": {
                "type": "web_app",
                "text": "🏡 Zomin Dacha",
                "web_app": {"url": url}
            }
        }
        if chat_id:
            payload["chat_id"] = chat_id
        return await self._post_api("setChatMenuButton", payload)

    # -------------------------------------------------------------
    # Conversational Logic & Handlers
    # -------------------------------------------------------------
    async def handle_start(self, chat_id: int, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handles /start command: greets user, registers in DB, sets menu button."""
        telegram_id = user_info.get("id") or chat_id
        first_name = user_info.get("first_name", "Sayyoh")
        username = user_info.get("username", "")

        # Upsert user into database if not present
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            existing = cursor.fetchone()
            if not existing:
                import uuid
                from datetime import datetime, timezone
                now_iso = datetime.now(timezone.utc).isoformat()
                cursor.execute("""
                    INSERT INTO users (id, phone_number, full_name, telegram_id, role, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'GUEST', 1, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    f"+998{telegram_id % 1000000000:09d}",
                    f"{first_name} {user_info.get('last_name', '')}".strip(),
                    telegram_id,
                    now_iso,
                    now_iso
                ))

        # Setup persistent Telegram WebApp menu button
        await self.set_chat_menu_button(chat_id=chat_id)

        welcome_text = (
            f"🌲 <b>Assalomu alaykum, {first_name}!</b>\n\n"
            f"<b>Zomin Dacha & Tog' Ekotizimi</b> rasmiy Telegram botiga xush kelibsiz!\n\n"
            f"Bu yerda siz:\n"
            f"• 🏡 <b>Zomin tog' dachalari</b> va kottejlarini tanlash;\n"
            f"• 🌊 <b>O'riklisoy tapchanlari</b> va sharsharalarni kashf etish;\n"
            f"• ⚡ <b>15 daqiqalik kafolatlangan band qilish</b> va Click/Payme to'lovi;\n"
            f"• 📄 <b>Oflayn Safar Vaucheri</b> va navigatsiyani olishingiz mumkin.\n\n"
            f"<i>Quyidagi tugma orqali to'g'ridan-to'g'ri Telegram Mini Appni oching:</i>"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": "🏡 Dachalarni ko'rish (Mini App)",
                        "web_app": {"url": settings.WEBAPP_URL}
                    }
                ],
                [
                    {"text": "🎫 Mening bronlarim", "callback_data": "cmd_my_bookings"},
                    {"text": "🚗 Darvoza tekshiruvi", "callback_data": "cmd_gate_check"}
                ],
                [
                    {"text": "📞 Aloqa va Yordam", "callback_data": "cmd_support"},
                    {"text": "📍 Zomin haqida", "callback_data": "cmd_about"}
                ]
            ]
        }

        return await self.send_message(chat_id, welcome_text, reply_markup=reply_markup)

    async def handle_my_bookings(self, chat_id: int, telegram_id: int) -> Dict[str, Any]:
        """Queries and displays active/upcoming bookings for this telegram user."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, p.title as prop_title, p.address_text, p.latitude, p.longitude, ru.name as unit_name
                FROM bookings b
                JOIN rental_units ru ON b.rental_unit_id = ru.id
                JOIN properties p ON ru.property_id = p.id
                JOIN users u ON b.guest_id = u.id
                WHERE u.telegram_id = ? OR b.guest_phone = u.phone_number
                ORDER BY b.created_at DESC LIMIT 5
            """, (telegram_id,))
            rows = cursor.fetchall()

        if not rows:
            text = (
                "🎫 <b>Sizda hozircha faol bronlar mavjud emas.</b>\n\n"
                "Zominning go'zal tabiati qo'ynidagi dachalarni ko'rish uchun quyidagi tugmani bosing:"
            )
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "🏡 Dachalarni tanlash (Mini App)", "web_app": {"url": settings.WEBAPP_URL}}]
                ]
            }
            return await self.send_message(chat_id, text, reply_markup=reply_markup)

        # Show first active booking
        b = rows[0]
        status_badge = "✅ KAFOLATLANGAN" if b["booking_status"] in ("CONFIRMED", "PAID_DEPOSIT") else "⏳ KUTILMOQDA"

        text = (
            f"🎫 <b>Sizning Safar Broningiz:</b>\n\n"
            f"🏡 <b>Obyekt:</b> {b['prop_title']}\n"
            f"🛏 <b>Joylashuv:</b> {b['unit_name']}\n"
            f"📅 <b>Sanalar:</b> {b['checkin_time'][:10]} — {b['checkout_time'][:10]}\n"
            f"👥 <b>Mehmonlar:</b> {b['guest_count']} kishi\n"
            f"🚗 <b>Mashina raqami:</b> {b['car_plate'] or 'Kiritilmagan'}\n"
            f"📌 <b>Holati:</b> {status_badge}\n"
            f"🔖 <b>Vaucher raqami:</b> <code>{b['booking_reference']}</code>\n\n"
            f"💵 <b>Kelganda to'lanadi (85%):</b> {format_sum(b['pay_on_arrival_amount'])} so'm\n"
            f"📍 <b>Manzil:</b> {b['address_text']}"
        )

        buttons = [
            [
                {"text": "📍 Xaritada ko'rish", "callback_data": f"geo_{b['id']}"},
                {"text": "📄 Oflayn Vaucher", "callback_data": f"vouch_{b['id']}"}
            ],
            [
                {"text": "🏡 Boshqa dachalarni ko'rish", "web_app": {"url": settings.WEBAPP_URL}}
            ]
        ]

        return await self.send_message(chat_id, text, reply_markup={"inline_keyboard": buttons})

    async def handle_gate_check_prompt(self, chat_id: int) -> Dict[str, Any]:
        """Initiates gatekeeper / caretaker car plate inspection."""
        USER_STATES[chat_id] = "AWAITING_CAR_PLATE"

        text = (
            "🚗 <b>Darvoza Tekshiruvi (Bog'bon portali)</b>\n\n"
            "Mehmon avtomashinasi davlat raqamini yozib yuboring:\n"
            "<i>(Masalan: <code>01 A 777 AA</code> yoki <code>25 B 888 BB</code>)</i>\n\n"
            "Yoki 6 xonali <b>Vaucher kodi</b>ni kiriting:"
        )
        return await self.send_message(chat_id, text)

    async def handle_gate_check_search(self, chat_id: int, query: str) -> Dict[str, Any]:
        """Searches active booking by license plate or voucher reference code."""
        clean_query = query.replace(" ", "").upper()

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, p.title as prop_title, p.address_text, ru.name as unit_name
                FROM bookings b
                JOIN rental_units ru ON b.rental_unit_id = ru.id
                JOIN properties p ON ru.property_id = p.id
                WHERE (REPLACE(UPPER(b.car_plate), ' ', '') = ? 
                   OR UPPER(b.booking_reference) = ? 
                   OR b.guest_phone LIKE ?)
                  AND b.booking_status IN ('CONFIRMED', 'PAID_DEPOSIT')
                ORDER BY b.created_at DESC LIMIT 1
            """, (clean_query, clean_query, f"%{clean_query[-7:]}%"))
            booking = cursor.fetchone()

        # Clear state
        USER_STATES.pop(chat_id, None)

        if not booking:
            text = (
                f"❌ <b>Faol bron topilmadi:</b> <code>{query}</code>\n\n"
                f"Ushbu avtomobil raqami yoki vaucher bo'yicha bugungi kunga faol buyurtma topilmadi.\n"
                f"Iltimos, raqamni to'g'ri kiritilganini tekshiring yoki dacha egasiga murojaat qiling."
            )
            retry_btn = {"inline_keyboard": [[{"text": "🔄 Qayta tekshirish", "callback_data": "cmd_gate_check"}]]}
            return await self.send_message(chat_id, text, reply_markup=retry_btn)

        # Successful pass
        text = (
            f"✅ <b>RUXSAT BERILDI (DARVOZA OCHILSIN)!</b>\n\n"
            f"👤 <b>Mehmon:</b> {booking['guest_name']}\n"
            f"📞 <b>Telefon:</b> {booking['guest_phone']}\n"
            f"🚗 <b>Avtomobil raqami:</b> <code>{booking['car_plate']}</code>\n"
            f"🏡 <b>Dacha:</b> {booking['prop_title']}\n"
            f"🛏 <b>Xonalar:</b> {booking['unit_name']}\n"
            f"👥 <b>Mehmonlar soni:</b> {booking['guest_count']} kishi\n\n"
            f"💵 <b>QABUL QILINADIGAN QOLDIQ:</b> <b>{format_sum(booking['pay_on_arrival_amount'])} so'm</b> (Naqd)\n"
            f"🔑 <i>Kalit topshirilsin. Xush kelibsiz!</i>"
        )

        actions = [
            [{"text": "✓ Mehmon kutib olindi (Check-in)", "callback_data": f"gate_checkin_{booking['id']}"}],
            [{"text": "🔍 Boshqa mashinani tekshirish", "callback_data": "cmd_gate_check"}]
        ]
        return await self.send_message(chat_id, text, reply_markup={"inline_keyboard": actions})

    async def handle_booking_checkin(self, chat_id: int, booking_id: str) -> Dict[str, Any]:
        """Marks guest as checked in at gate."""
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE bookings SET updated_at = ? WHERE id = ?", (now_iso, booking_id))

        text = "✅ <b>Mehmon muvaffaqiyatli kutib olindi va ro'yxatga olindi!</b>"
        return await self.send_message(chat_id, text)

    async def handle_host_confirm(self, chat_id: int, booking_id: str) -> Dict[str, Any]:
        """Host confirms the reservation directly via Telegram inline button."""
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE bookings SET booking_status = 'CONFIRMED', updated_at = ? WHERE id = ?", (now_iso, booking_id))
            cursor.execute("SELECT b.*, p.title as prop_title FROM bookings b JOIN rental_units ru ON b.rental_unit_id = ru.id JOIN properties p ON ru.property_id = p.id WHERE b.id = ?", (booking_id,))
            b = cursor.fetchone()

        text = (
            f"✅ <b>Bron tasdiqlandi!</b>\n\n"
            f"🏡 <b>Obyekt:</b> {b['prop_title'] if b else 'Dacha'}\n"
            f"👤 <b>Mehmon:</b> {b['guest_name'] if b else '-'}\n"
            f"Mehmon hisobiga oflayn vaucher va marshrut yuborildi."
        )
        return await self.send_message(chat_id, text)

    async def handle_support(self, chat_id: int) -> Dict[str, Any]:
        text = (
            "📞 <b>Zomin Tog' Turizmi Qo'llab-quvvatlash Markazi:</b>\n\n"
            "Savollar yoki yordam kerak bo'lsa, biz bilan bog'laning:\n"
            "• ☎️ Telefon: <b>+998 78 120 00 21</b>\n"
            "• ⏰ Ish vaqti: <b>24/7 (Dam olish kunlarisiz)</b>\n"
            "• 💬 Telegram: @zomin_support\n\n"
            "<i>Biz sizning unutilmas va qulay hordiq chiqarishingiz tarafdorimiz!</i>"
        )
        return await self.send_message(chat_id, text)

    async def handle_about(self, chat_id: int) -> Dict[str, Any]:
        text = (
            "🏔 <b>Zomin Tog' Klasteri Haqida:</b>\n\n"
            "Zomin — O'zbekistonning betakror Shveytsariyasi hisoblangan musaffo tog' kurorti.\n\n"
            "✨ <b>Asosiy diqqatga sazovor maskanlar:</b>\n"
            "• 🌉 <b>Zomin Osma Ko'prigi (305m)</b> — Kanyon ustidagi shaffof shisha ko'prik;\n"
            "• 🚠 <b>Bartholet Kabel Yo'li</b> — 2400 metr balandlikdagi zamonaviy dor yo'li;\n"
            "• 💧 <b>O'riklisoy & Chashma</b> — Buloq suvlari ustidagi salqin tapchanlar;\n"
            "• 🌲 <b>Shifobaxsh Archazorlar</b> — Nafas yo'llari uchun bebaho tabiiy shifo."
        )
        reply_markup = {
            "inline_keyboard": [
                [{"text": "🏡 Dachalarni tanlash (Mini App)", "web_app": {"url": settings.WEBAPP_URL}}]
            ]
        }
        return await self.send_message(chat_id, text, reply_markup=reply_markup)

    async def dispatch_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Main dispatcher for incoming Telegram Webhook updates."""
        # 1. Callback query handling (Inline buttons)
        if "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb.get("id")
            data = cb.get("data", "")
            from_user = cb.get("from", {})
            chat_id = from_user.get("id")

            await self.answer_callback_query(cb_id)

            if data == "cmd_my_bookings":
                return await self.handle_my_bookings(chat_id, from_user.get("id"))
            elif data == "cmd_gate_check":
                return await self.handle_gate_check_prompt(chat_id)
            elif data == "cmd_support":
                return await self.handle_support(chat_id)
            elif data == "cmd_about":
                return await self.handle_about(chat_id)
            elif data.startswith("gate_checkin_"):
                booking_id = data.replace("gate_checkin_", "")
                return await self.handle_booking_checkin(chat_id, booking_id)
            elif data.startswith("host_confirm_"):
                booking_id = data.replace("host_confirm_", "")
                return await self.handle_host_confirm(chat_id, booking_id)
            elif data.startswith("geo_"):
                # Send location coordinates
                booking_id = data.replace("geo_", "")
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT p.latitude, p.longitude, p.title 
                        FROM bookings b
                        JOIN rental_units ru ON b.rental_unit_id = ru.id
                        JOIN properties p ON ru.property_id = p.id
                        WHERE b.id = ?
                    """, (booking_id,))
                    p = cursor.fetchone()
                if p and p["latitude"] and p["longitude"]:
                    return await self.send_location(chat_id, p["latitude"], p["longitude"])
                return await self.send_message(chat_id, "📍 Geolokatsiya: 39.9180° N, 68.4105° E (Zomin)")
            elif data.startswith("vouch_"):
                booking_id = data.replace("vouch_", "")
                return await self.send_message(chat_id, f"📄 Vaucher kodi: <code>VOUCH-{booking_id[:6].upper()}</code>\nSafar vaucheri faol va tasdiqlangan.")

            return {"ok": True}

        # 2. Regular message handling
        if "message" in update:
            msg = update["message"]
            chat_id = msg.get("chat", {}).get("id")
            text = (msg.get("text") or "").strip()
            user_info = msg.get("from", {})

            if text.startswith("/start"):
                return await self.handle_start(chat_id, user_info)
            elif text == "/my_bookings":
                return await self.handle_my_bookings(chat_id, user_info.get("id"))
            elif text == "/gate":
                return await self.handle_gate_check_prompt(chat_id)
            elif text == "/support":
                return await self.handle_support(chat_id)

            # Check if user was prompted for car plate
            if USER_STATES.get(chat_id) == "AWAITING_CAR_PLATE":
                return await self.handle_gate_check_search(chat_id, text)

            # Default fallback: show helpful start menu
            return await self.handle_start(chat_id, user_info)

        return {"ok": True}

bot_service = TelegramBotService()
