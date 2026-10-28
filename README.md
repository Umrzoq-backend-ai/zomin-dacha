# ZominStay — Zomin Tog' Turizmi, Dacha va Dam Olish Ekotizimi

ZominStay — Jizzax viloyati Zomin tumanidagi barcha turar joylar (dala hovlilar / dachalar, tog‘ kottejlari, mehmon uylari), dam olish maskanlari (soy bo‘yidagi tapchanlar, choyxonalar) va mashhur Zomin archa tandiri gastronomik xizmatlarini yagona raqamli platformaga birlashtiruvchi zamonaviy ekotizimdir.

Loyihaning to'liq texnik spetsifikatsiyasi: [ZOMINSTAY_MUKAMMAL_TZ.md](file:///home/zoltanma/zomin%20dacha/ZOMINSTAY_MUKAMMAL_TZ.md).

---

## 🏔️ Zomin Mikro-Hududlari va Xususiyatlari
- **Duoba MFY:** Zomin dacha va choyxonalarining 75% o'rni, soy bo'yi, basseynli dachalar.
- **O'riklisoy & Pishag'or:** Shifobaxsh buloqlar, archazorlar, kunduzgi soy bo'yi tapchanlari.
- **Suffa Platosi (2400 m):** Shveysariya Bartholet osma dor yo'li (2.1 km), 305 metrli osma ko'prik, panoramik kottejlar.
- **Zomin Sanatoriysi (1800 m):** Qarag'ayzorlar, sog'lomlashtirish va oilaviy pansionatlar.
- **Dashtobod stansiyasi:** Toshkent va Samarqanddan Afrosiyob tezyurar poyezdi kirish darvozasi.

---

## ⚡ Asosiy Imkoniyatlar va Arxitektura

1. **Double-Bookingga qarshi Concurrency Himoyasi (AC-01, AC-02, AC-05, AC-06):**
   - Vaqt oraliqlari to'qnashuvini atomik tekshirish (`inventory_allocations`).
   - Kunduzgi tapchanlar (LUNCH: 10:00-16:00 va DINNER: 17:00-23:00) bir kunda bir nechta mehmon tomonidan to'qnashuvsiz bron qilinadi.
   - 15 daqiqalik qulf (PLATFORM_HOLD) va avtomatik Lazy Invalidation mexanizmi.
   - Kechikkan to'lov (Late payment) joy boshqa mehmonga o'tib ketgan taqdirda kartaga 100% avtomatik qaytariladi (`CONFLICTED_EXPIRED`).

2. **Frictionless Qonuniy Monetizatsiya (0% Escrow Xatari):**
   - Sayyoh platformada 10% kafolat xizmat haqini to'laydi (Click / Payme).
   - Qolgan 90% summani Zominga yetib borib dacha egasiga joyida topshiradi.
   - Soliq OFD elektron fiskal chek QR integratsiyasi.

3. **Telegram Mini App & HMAC-SHA256 Xavfsiz Autentifikatsiya (AC-08):**
   - Telegram WebApp SDK bilan integratsiya qilingan chiroyli mobil UI.
   - `verify_telegram_init_data` funksiyasi `WebAppData` maxfiy kaliti orqali soxtalashtirish va Replay hujumlarini (24 soatdan eski auth_date) to'xtatadi.

4. **Tog'da Internet Yo'qolganda Ishlovchi Oflayn Safar Vaucheri (AC-09):**
   - Ega va bog'bonning to'g'ridan-to'g'ri GSM aloqa raqamlari (`tel:+998...`).
   - Aniq GPS nuqta va Yandex Navigator havolalari.
   - Zomin relyefiga mos matnli marshrut ("Duoba ko'prigidan o'tgach, chapdagi archazor yo'lidan 300 metr yuqoriga").
   - Yo'l sharoiti ogohlantirishlari: "🚗 Asfalt (Spark/Cobalt bemalol chiqadi)" yoki "🚙 4WD / Shag'al yo'l".
   - Oflayn QR kod matni.

5. **Qarovchi (Bog'bon) Portali va RBAC Ruxsatlari (AC-14):**
   - Bog'bonga faqat mehmon ismi, telefoni, kelish vaqti, mashina raqami va "Kalit topshirildi (Check-in)" tugmasi ko'rinadi.
   - Barcha moliyaviy ma'lumotlar (summalar, daromadlar) bog'bondan qat'iy yashiriladi.

6. **Zomin Archa Tandiri Oldindan Buyurtmasi (AC-12):**
   - Bron vaqtida go'sht miqdorini (kg) kiritish.
   - 150,000 so'm/kg hisob-kitobi va oshxonaga uzatish.

---

7. **To'liq SuperAdmin Boshqaruv Portali:**
   - Real vaqtli biznes metrikalari: umumiy bronlar, faol foydalanuvchilar, jami tushum va sof platforma daromadi.
   - Dacha va kottejlarni tekshirish va moderatsiyadan o'tkazish (VERIFIED / REJECTED).
   - Bronlarni boshqarish va nizoli holatlarda ma'muriy bekor qilish (Force-Cancel).
   - Click va Payme to'lovlar tranzaksiyalari reestrini nazorat qilish va Soliq OFD fiskal cheklari rekonssilyatsiyasi.
   - Foydalanuvchilarni bloklash / faollashtirish va harakatlar audit tarixi (Audit Logs).

---

## 🚀 Ishga Tushirish va O'rnatish

```bash
# 1. Virtual muhitni faollashtirish
source .venv/bin/activate

# 2. Serverni ishga tushirish (Uvicorn)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Brauzer yoki Telegram WebApp orqali oching:
- Veb-ilova & Mini App: `http://localhost:8000/`
- Interaktiv Swagger API hujjatlari: `http://localhost:8000/docs`
- ReDoc hujjatlari: `http://localhost:8000/redoc`

---

## 🧪 Avtomatlashtirilgan Testlar

Loyiha barcha asosiy talablar, concurrency, to'lovlar, admin boshqaruvi va chekka holatlar bo'yicha 34 ta avtomatlashtirilgan test bilan to'liq qoplangan:

```bash
source .venv/bin/activate
pytest tests/ -v
```

Barcha test to'plamlari:
- `test_concurrency_double_booking.py` (AC-01, AC-02, AC-05)
- `test_race_conditions_and_edge_cases.py` (20-thread stress test, Idempotency replay)
- `test_quotes.py` (AC-03, ish/dam olish kunlari narxlash, tandir kalkulyatori)
- `test_booking_fsm.py` (AC-07 BOLA himoyasi, AC-14 bog'bon roli, AC-16 sharhlar)
- `test_payments_click_payme.py` (AC-04 idempotency, AC-06 late auto-refund, AC-15 OFD chek)
- `test_telegram_auth.py` (AC-08 HMAC tekshiruvi va Replay attack himoyasi)
- `test_filters_and_search.py` (AC-11 Spark yo'li & Generator, AC-13 boshlang'ich narx)
- `test_offline_voucher.py` (AC-09 oflayn vaucher va GSM havolalari)
- `test_ivr_call_reminder.py` (AC-10 egaga 10 daqiqadan so'ng avtomatlashtirilgan qo'ng'iroq)
- `test_admin_portal.py` (Superadmin dashboard, moderatsiya, tranzatsiyalar va audit loglar)
