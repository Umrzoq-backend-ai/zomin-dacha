# ZOMINSTAY — ZOMIN TOG‘ TURIZMI, DACHA VA DAM OLISH EKOTIZIMI
## Mukammal Texnik Topshiriq (TZ), Tizim Arxitekturasi va Bozor Tahlili

---

## 1. LOYIHA HAQIDA VA BOZOR TAHLILI (EXECUTIVE SUMMARY)

### 1.1. Loyiha Missiyasi
**ZominStay** — Jizzax viloyati Zomin tumanidagi barcha turar joylar (dala hovlilar / dachalar, tog‘ kottejlari, mehmon uylari), dam olish maskanlari (soy bo‘yidagi tapchanlar, choyxonalar) va mahalliy gastronomik xizmatlarni (mashhur Zomin archa tandiri) yagona raqamli platformaga birlashtiruvchi zamonaviy ekotizimdir.

Platforma sayyohlarga qidiruv, haqqoniy narx, real vaqt rejimidagi kalendar, kafolatlangan band qilish (double-bookingga qarshi) va xavfsiz to‘lovni taqdim etadi. Dacha egalari va choyxona boshqaruvchilari uchun esa soddalashtirilgan Telegram bot va admin paneli orqali buyurtmalarni qabul qilish imkonini beradi.

---

### 1.2. Zomin Turizm Bozorining Real Geografiyasi
Zomin relyefi va infratuzilmasi o‘ziga xos 5 ta asosiy klasterga bo‘linadi:

```
                  ┌──────────────────────────────────────────────┐
                  │   Dashtobod (Transport Habi / Afrosiyob)    │
                  └──────────────────────┬───────────────────────┘
                                         │ (25 km tog' yo'li)
                  ┌──────────────────────▼───────────────────────┐
                  │   Zomin Markazi (Shahar, Bozor, Tandir)      │
                  └──────────────────────┬───────────────────────┘
                                         │ (18 km)
                  ┌──────────────────────▼───────────────────────┐
                  │   Duoba MFY (Dachalar, Kottejlar, Soylar)   │
                  │   * Dachalar va Choyxonalarning 75% o'rni    │
                  └──────────┬───────────────────────┬───────────┘
                             │                       │
              ┌──────────────┴───────┐      ┌────────┴──────────────┐
              ▼                      ▼      ▼                       ▼
      [ O‘riklisoy & Pishag‘or ]       [ Zomin Sanatoriysi ]     [ Suffa Platosi (2400 m) ]
      - Buloqlar, archazorlar           - Shifobaxsh qarag‘ay     - Bartholet osma dor yo‘li (2.1 km)
      - Sokin oilaviy dam olish         - Pansionatlar            - 305 m osma ko‘prik
                                                                 - Qishki turizm / Qor
```

1. **Dashtobod stansiyasi:** Toshkent va Samarqanddan "Afrosiyob" tezyurar poyezdida keluvchi sayyohlarning kirish darvozasi. Bu yerdan tog‘ taksilari (Cobalt, Nexia) sayyohlarni Duoba va tog‘ zonasiga tashiydi.
2. **Duoba MFY (Dachalar o‘zagi):** Dengiz sathidan 1100–1400 metr balandlikda. Barcha yirik dacha majmualari, soy bo‘yidagi tapchanlar shu yerda. Relyefi tor soy bo‘ylab cho‘zilgan.
3. **O‘riklisoy va Pishag‘or:** Ekologik toza zona, buloq suvlari, shovqindan xoli tabiat qo‘yni.
4. **Zomin Sanatoriysi (1800 m):** Asosan sog‘lomlashtirish turizmi, keksalar va oilalar.
5. **Suffa platosi (2400 m):** Shveysariyaning *Bartholet AG* kompaniyasi (Porsche Design Studio kabinalari) tomonidan qurilgan 2 102 metrlik osma dor yo‘li, 305 metrli osma ko‘prik, Wyndham mehmonxonalari. Yozda salqin, qishda qor zonalari.

---

### 1.3. Mavjud Raqobatchilar va Telegram Kanallarning 6 Ta O‘tkir Muammosi

Hozirgi vaqtda bozorda quyidagi muammolar mavjud:

1. **Feyk suratlar va aldov:** Telegram kanallar va noqonuniy maklerlar Chorvoq yoki chet el dachalari suratlarini Zominniki deb ko‘rsatadi.
2. **Avans firibgarligi (Scam):** "Joyni saqlab qo‘yaman" deb karta raqamiga 300 000 – 1 000 000 so‘m o‘tkaztirib, so‘ng aloqani uzish holatlari ko‘p.
3. **Double Booking (Bir vaqtda ikki kishiga sotish):** Telegramda yagona kalendar yo‘qligi sababli, telefon orqali gaplashgan boshqa mijozga berib yuboriladi. Mehmon oilasi bilan borib ko‘chada qoladi.
4. **Kutilmagan narx oshishi:** "Dam olish kunlari narx oshdi", "basseyn isitilishi alohida pul", "bilyard alohida" deb joyida narx 30–50% oshiriladi.
5. **Lokatsiya va yo‘l noaniqligi:** Tog‘ ichidagi tor yo‘llarda internet yo‘qolib, dachani topib borish qiyinlashadi. Oddiy yengil mashina (Spark, Nexia) chiqa olmaydigan qiyaliklar oldindan ogohlantirilmaydi.
6. **Mavjud platformalarning (Bronla, Damda, OLX) nochorligi:** Toshkent viloyatiga ixtisoslashgan, Zomin bo‘yicha e’lonlar kam, kalendarlar yangilanmaydi va eng asosiysi — **kunduzgi tapchan va choyxonalar** umuman qamrab olinmagan.

---

## 2. BIZNES MODELI VA MOLIYAVIY SXEMA

### 2.1. Ikki Qavatli Xizmat Modeli
Zomin turizmining o‘ziga xosligi shundaki, sayyohlarning 50% dan ortig‘i yotib qolmaydi — ular kunduzgi dam olishga keladi.

```
                             ZOMINSTAY PLATFORMASI
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
   【 1. SUTKALIK TURAR JOY 】                           【 2. KUNDUZGI DAM OLISH 】
   - Butun hovli dachalar                                - Soy bo‘yidagi tapchanlar
   - Tog‘ kottejlari                                     - Choyxonalar va so‘rilar
   - Mehmon uylari / Xonalar                             - O‘tovlar (yurtlar)
   - Bron: [Check-in 14:00, Check-out 12:00)             - Bron: 10:00 - 22:00 (yoki 2 slot)
   - Narx: Tunlar soni bo‘yicha                          - Qo‘shimcha: Zomin tandiri (kg)
```

### 2.2. Legal & Frictionless Monetizatsiya: "Platforma Xizmat Haqi" Modeli (0% Escrow Xatari)
Startap O‘zbekiston Respublikasi qonunlariga to‘liq mos ishlashi uchun mablag‘ni depozitda saqlash (Escrow) litsenziyasini talab qilmaydigan model qo‘llaniladi:

1. **Sayyoh to‘lovi:** Sayyoh dacha/tapchan narxining **10% – 12% ini** platformada Click / Payme / Uzum orqali to‘laydi. Bu mablag‘ — **"ZominStay Kafolatlangan Bron Xizmati"** haqi sifatida startap hisob raqamiga to‘liq qonuniy tushadi. Mijozga Soliq OFD integratsiyasi orqali avtomatik QR-kodli elektron chek beriladi.
2. **Qolgan summa (88% – 90%):** Sayyoh Zominga yetib borib, dacha holatini ko‘rgach, qolgan summani to‘g‘ridan-to‘g‘ri dacha egasiga (naqd yoki kartasiga) to‘laydi.
3. **Afzalliklari:**
   - Startap bank litsenziyasi va omonat talablaridan ozod.
   - Jismoniy shaxslarga P2P karta orqali pul o‘tkazish (va buning soliq muammolari) xavfi 0 ga teng.
   - Sayyoh uchun 100% emas, atigi 10% avans to‘lash psixologik jihatdan juda yengil va ishonchli.

### 2.3. Low-Tech Dacha Egalari va "Qarovchi" (Bog‘bon) Arxitekturasi
Zomin dacha egalarining ko‘pchiligi Toshkent yoki Jizzaxda yashaydi, joyda esa keksaroq qarovchi (bog‘bon) qaraydi. Ular murakkab veb-sayt ishlatmaydi.
- **Telegram Ega Boti (@ZominStayOwnerBot):**
  Ega yangi bron so‘rovlarini inline tugmalar orqali tasdiqlaydi:  
  `"🔔 Yangi bron! 15–17 Iyul (2 tun), 8 kishi. Xizmat haqi to‘landi. Joyida olasiz: 2,700,000 so‘m. [✅ Tasdiqlash] [❌ Rad etish]"`
  Kalendarni tezkor yopish: `[📅 Bugun band] [📅 Ertaga band] [📅 Sanani tanlab yopish]`.
- **Qarovchi (Bog‘bon) Rejimi:** Ega o‘z botida bog‘bonining telefon raqamini kiritadi. Bog‘bonga moliyaviy ma’lumotlar ko‘rinmaydi — unga faqat:
  - Mehmonning ismi va mashina raqami,
  - Kelish kuni va soati,
  - Mehmonni kutib olish tugmasi `[🔑 Kalit topshirildi / Mehmon keldi]` ko‘rinadi.
- **Ovozli Robot Qo‘ng‘iroq (IVR Fallback):** Agar dacha egasi 10 daqiqa ichida Telegram botdagi so‘rovga javob bermasa, robot telefoniga qo‘ng‘iroq qiladi: *"ZominStay: Sizda yangi bron so‘rovi bor, iltimos Telegram botni tekshiring"*.

---

## 3. TIZIM ARXITEKTURASI VA CONCURRENCY MUHANDISLIGI

### 3.1. Texnologik Stek
- **Backend:** Python 3.12 + **Django Ninja** (yoki DRF). Yuqori unumdorlik, avtomatik OpenAPI hujjatlash, Django ORM va GeoDjango imkoniyatlari.
- **Ma’lumotlar bazasi:** PostgreSQL 16 + PostGIS + `btree_gist` kengaytmasi.
- **Keshlash va Qulflar:** Redis 7 (Distributed lock va tezkor qidiruv).
- **Asinxron Fon Jarayonlari:** Celery + Redis (Hold muddati tugashini tozalash, SMS yuborish, eslatish).
- **Frontend & TMA:** Next.js 14 (App Router) + TailwindCSS + Zustand + Telegram WebApp SDK.
- **Fayllar va Media:** Cloudflare R2 / AWS S3 (Rasmlarni WebP formatida siqish bilan).

```
  [ Sayyoh: Veb Sayt ]      [ Sayyoh: Telegram Mini App ]     [ Dacha Egasi: Telegram Bot ]
       (Next.js)                     (React TMA)                      (Aiogram 3.x)
            │                             │                                   │
            └─────────────────────────────┼───────────────────────────────────┘
                                          ▼
                                ┌───────────────────┐
                                │   Nginx / Caddy   │
                                └─────────┬─────────┘
                                          │
                                          ▼
                       ┌──────────────────────────────────────┐
                       │   ZominStay Modular Monolith Core    │
                       │   (Python 3.12 + Django Ninja/DRF)   │
                       └──────────────────┬───────────────────┘
                                          │
      ┌──────────────────────┬────────────┴─────────────┬─────────────────────┐
      ▼                      ▼                          ▼                     ▼
┌──────────────┐      ┌──────────────┐           ┌──────────────┐      ┌──────────────┐
│  PostgreSQL  │      │    Redis     │           │    Celery    │      │ Cloudflare R2│
│ 16 + PostGIS │      │ Cache & Lock │           │ Background & │      │ (WebP Media) │
│(TSTZRANGE    │      │              │           │ Cron Workers │      │              │
│ Exclusion)   │      │              │           │              │      │              │
└──────────────┘      └──────────────┘           └──────────────┘      └──────────────┘
```

---

### 3.2. Double-Bookingga Qarshi `TSTZRANGE` GiST Cheklovi va Lazy Hold Invalidation
Sutkalik dacha va kunduzgi tapchanlarni yagona jadvalda xatolarsiz boshqarish uchun `inventory_allocations` jadvalida vaqt zonali timestamp diapazoni (`TSTZRANGE`) qo‘llaniladi:

```sql
CONSTRAINT exclude_overlapping_allocations 
    EXCLUDE USING gist (
        rental_unit_id WITH =,
        time_range WITH &&
    )
    WHERE (status = 'ACTIVE');
```

#### Lazy Invalidation mexanizmi (Celery kechikishidan himoya):
Agar Celery navbati tiqilib qolsa yoki worker kechiksa ham, yangi mijoz tranzaksiyasi eskirgan hold sababli to‘xtab qolmaydi:
```python
with transaction.atomic():
    # 1. Avval muddati o'tgan holdlarni bekor qilish (Lazy cleanup)
    InventoryAllocation.objects.filter(
        rental_unit_id=unit_id,
        status='ACTIVE',
        allocation_type='PLATFORM_HOLD',
        expires_at__lt=timezone.now()
    ).update(status='EXPIRED')

    # 2. Yangi hold yaratish (Baza GiST exclusion orqali to'qnashuvni to'xtatadi)
    allocation = InventoryAllocation.objects.create(
        rental_unit_id=unit_id,
        booking_id=new_booking.id,
        allocation_type='PLATFORM_HOLD',
        time_range=(start_time, end_time),
        status='ACTIVE',
        expires_at=timezone.now() + timedelta(minutes=15)
    )
```

---

### 3.3. Poyga Holatlari va AC-07 (Late Payment Auto-Refund) Arxitekturasi
Agar mijoz to‘lov oynasini ochib, 15 daqiqadan keyin pul to‘lasa (bu vaqtda dacha boshqa odamga sotilgan bo‘lsa):
1. Click/Payme webhooki keladi.
2. Server bron statusini `CONFIRMED` ga o‘tkazishga urinadi.
3. PostgreSQL `exclusion_violation` xatosini beradi.
4. Tizim xatoni ushlaydi, to‘lovni `CONFLICTED_EXPIRED` deb belgilaydi.
5. Payme `CancelTransaction` yoki Click `action=-1` orqali **pul 100% mijoz kartasiga zudlik bilan qaytariladi**.
6. Mehmonning Telegramiga va SMS orqali xabar yuboriladi:  
   *"Kechirasiz, 15 daqiqalik to‘lov muddati tugagani sababli joy boshqa mehmonga berildi. Sizdan yechilgan mablag‘ kartangizga to‘liq qaytarildi."*

---

### 3.4. Oflayn Rejim (Tog‘da Internet Yo‘qolganda Ishlash)
Sayyoh Zomin tog‘larining chuqur soylariga tushganda 4G yo‘qolishi mumkin.
1. **Next.js PWA Service Worker:** `Cache-First` strategiyasi orqali tasdiqlangan bron vaucherini (`/me/bookings/{id}/voucher`) mahalliy IndexedDB ga saqlaydi.
2. **Vaucher tarkibi:**
   - Ega va bog‘bonning bevosita telefon raqamlari (to‘g‘ridan-to‘g‘ri GSM qo‘ng‘iroq uchun).
   - Aniq GPS nuqta va matnli yo‘l ko‘rsatmasi (*"Duoba ko‘prigidan o‘tgach, chapdagi archazor yo‘lidan 300 metr yuqoriga"*).
   - Oflayn xarita ilovalariga yo‘naltirish: `geo:39.9612,68.4231?q=ZominStay+Dacha` va `yandexmaps://build_route_on_map?lat_to=...&lon_to=...` havolalari.

---

## 4. MA’LUMOTLAR BAZASI DDL SXEMASI (PRODUCTION POSTGRESQL + POSTGIS)

```sql
-- Kengaytmalarni faollashtirish
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- 1. Foydalanuvchilar va Rollar
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(150),
    telegram_id BIGINT UNIQUE,
    role VARCHAR(30) NOT NULL DEFAULT 'GUEST', -- 'GUEST', 'OWNER', 'CARETAKER', 'MODERATOR', 'ADMIN'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_telegram ON users(telegram_id);

-- 2. Dacha / Dam olish obyekti (Property)
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    property_type VARCHAR(50) NOT NULL, -- 'VILLA', 'COTTAGE', 'GUEST_HOUSE', 'CHOYXONA_TAPCHAN'
    region VARCHAR(50) NOT NULL DEFAULT 'ZOMIN',
    micro_district VARCHAR(100) NOT NULL, -- 'DUOBA', 'ORIKLISOY', 'SUFFA', 'SANATORIY', 'DASHTOBOD'
    address_text TEXT NOT NULL,
    coordinates GEOMETRY(Point, 4326) NOT NULL,
    location_precision VARCHAR(20) NOT NULL DEFAULT 'APPROXIMATE', -- 'APPROXIMATE' (katalogda), 'EXACT' (brondan keyin)
    
    -- Zomin tog' infratuzilmasi parametrlari:
    road_condition VARCHAR(50) NOT NULL, -- 'ASPHALT_SEDAN', 'HIGH_CLEARANCE', '4WD_ONLY', 'WINTER_CHAINS'
    has_generator BOOLEAN NOT NULL DEFAULT FALSE,
    water_source VARCHAR(50) NOT NULL, -- 'SPRING_WATER', 'TAP_WATER', 'TANKER'
    heating_type VARCHAR(50) NOT NULL, -- 'GAS_CENTRAL', 'WOOD_STOVE', 'ELECTRIC_FLOOR', 'AC'
    mobile_coverage VARCHAR(50) NOT NULL, -- '4G_EXCELLENT', '3G_MEDIUM', 'VOICE_ONLY', 'NO_SIGNAL'
    
    verification_status VARCHAR(30) NOT NULL DEFAULT 'DRAFT', -- 'DRAFT', 'PENDING', 'VERIFIED', 'REJECTED'
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_properties_geo ON properties USING GIST(coordinates);
CREATE INDEX idx_properties_district ON properties(micro_district);

-- 3. Bron birligi (Rental Unit)
CREATE TABLE rental_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL, -- "Butun Dacha", "1-kottej", "Soy bo'yidagi 3-tapchan"
    unit_category VARCHAR(50) NOT NULL, -- 'OVERNIGHT_STAY', 'DAY_USE_TAPCHAN'
    standard_capacity INT NOT NULL DEFAULT 8,
    max_capacity INT NOT NULL DEFAULT 12,
    base_price_weekday DECIMAL(12, 2) NOT NULL, -- Dushanba-Payshanba narxi
    base_price_weekend DECIMAL(12, 2) NOT NULL, -- Juma-Yakshanba narxi
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Kunduzgi Tapchan Slotlari (Choyxonalar uchun)
CREATE TABLE day_use_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rental_unit_id UUID NOT NULL REFERENCES rental_units(id) ON DELETE CASCADE,
    slot_name VARCHAR(50) NOT NULL, -- 'FULL_DAY' (10:00-22:00), 'LUNCH' (10:00-16:00), 'DINNER' (17:00-23:00)
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    price_weekday DECIMAL(12, 2) NOT NULL,
    price_weekend DECIMAL(12, 2) NOT NULL
);

-- 5. Bronlar (Bookings)
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_reference VARCHAR(16) UNIQUE NOT NULL, -- 'ZS-2026-9812'
    rental_unit_id UUID NOT NULL REFERENCES rental_units(id) ON DELETE RESTRICT,
    guest_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    booking_type VARCHAR(30) NOT NULL, -- 'OVERNIGHT', 'DAY_USE'
    checkin_time TIMESTAMPTZ NOT NULL,
    checkout_time TIMESTAMPTZ NOT NULL,
    guest_count INT NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'UZS',
    
    -- Moliyaviy snapshot:
    unit_base_amount DECIMAL(12, 2) NOT NULL,
    platform_fee_amount DECIMAL(12, 2) NOT NULL, -- 10-12% onlayn to'lanadigan xizmat haqi
    pay_on_arrival_amount DECIMAL(12, 2) NOT NULL, -- 88-90% joyida to'lanadigan summa
    total_amount DECIMAL(12, 2) NOT NULL,
    
    booking_status VARCHAR(40) NOT NULL DEFAULT 'PENDING_OWNER',
    -- 'PENDING_OWNER', 'AWAITING_PAYMENT', 'CONFIRMED', 'CHECKED_IN', 'COMPLETED', 'CANCELLED', 'EXPIRED'
    
    hold_expires_at TIMESTAMPTZ,
    cancellation_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_bookings_ref ON bookings(booking_reference);
CREATE INDEX idx_bookings_status ON bookings(booking_status);

-- 6. Kalendar va Bandlik Nazorati (Inventory Allocations) - CRITICAL ENGINE
CREATE TABLE inventory_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rental_unit_id UUID NOT NULL REFERENCES rental_units(id) ON DELETE CASCADE,
    booking_id UUID REFERENCES bookings(id) ON DELETE CASCADE,
    allocation_type VARCHAR(30) NOT NULL, -- 'PLATFORM_HOLD', 'CONFIRMED_BOOKING', 'OWNER_MANUAL', 'MAINTENANCE'
    time_range TSTZRANGE NOT NULL,
    status VARCHAR(30) NOT NULL, -- 'ACTIVE', 'EXPIRED', 'CANCELLED'
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT exclude_overlapping_allocations 
        EXCLUDE USING gist (
            rental_unit_id WITH =,
            time_range WITH &&
        )
        WHERE (status = 'ACTIVE')
);

-- 7. Zomin Tandiri va Qo'shimcha Buyurtmalar (Food Pre-orders)
CREATE TABLE booking_food_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    dish_name VARCHAR(100) NOT NULL DEFAULT 'Zomin Archa Tandiri',
    quantity_kg DECIMAL(4, 2) NOT NULL,
    target_serving_time TIMESTAMPTZ NOT NULL,
    price_per_kg DECIMAL(12, 2) NOT NULL,
    total_food_amount DECIMAL(12, 2) NOT NULL,
    special_notes TEXT
);

-- 8. To'lov Urinishlari va Tranzaksiyalar (Click, Payme, Uzum)
CREATE TABLE payment_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    provider VARCHAR(30) NOT NULL, -- 'CLICK', 'PAYME', 'UZUM'
    provider_transaction_id VARCHAR(100),
    amount_in_tiyin BIGINT NOT NULL, -- Payme uchun tiyinda (1 UZS = 100 tiyin)
    amount_uzs DECIMAL(12, 2) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'INITIATED', 
    -- 'INITIATED', 'PENDING', 'SUCCESS', 'FAILED', 'REFUNDED', 'CONFLICTED_EXPIRED'
    idempotency_key VARCHAR(100) NOT NULL UNIQUE,
    provider_payload JSONB,
    fiscal_receipt_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_payments_trans ON payment_attempts(provider, provider_transaction_id);

-- 9. Dacha Qarovchilari (Caretakers / Bog'bonlar)
CREATE TABLE property_caretakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    caretaker_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    can_confirm_arrival BOOLEAN NOT NULL DEFAULT TRUE,
    notes VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(property_id, caretaker_id)
);

-- 10. Sharhlar va Ishonch Reytingi (Reviews)
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID UNIQUE NOT NULL REFERENCES bookings(id) ON DELETE RESTRICT,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    guest_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    rating_cleanliness SMALLINT NOT NULL CHECK (rating_cleanliness BETWEEN 1 AND 5),
    rating_accuracy SMALLINT NOT NULL CHECK (rating_accuracy BETWEEN 1 AND 5),
    rating_communication SMALLINT NOT NULL CHECK (rating_communication BETWEEN 1 AND 5),
    rating_comfort SMALLINT NOT NULL CHECK (rating_comfort BETWEEN 1 AND 5),
    overall_rating DECIMAL(3, 2) NOT NULL,
    comment TEXT,
    owner_reply TEXT,
    is_verified_stay BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 5. API SHARTNOMALARI VA INTEGRATSIYALAR

### 5.1. Telegram WebApp `initData` Xavfsiz Validatsiyasi
```python
import hmac
import hashlib
import time
from urllib.parse import parse_qsl

def verify_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict | None:
    """
    Telegram Mini App initData ni to'liq va xavfsiz validatsiya qiladi:
    1. URL-unquote qiladi.
    2. auth_date bo'yicha Replay attackni to'xtatadi.
    3. HMAC-SHA256 xeshini tekshiradi.
    """
    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return None

    if "hash" not in parsed_data:
        return None

    received_hash = parsed_data.pop("hash")

    # Replay attack tekshiruvi: auth_date eskirgan bo'lmasligi shart
    auth_date = int(parsed_data.get("auth_date", 0))
    current_time = int(time.time())
    if abs(current_time - auth_date) > max_age_seconds:
        return None

    # Ma'lumotlarni alifbo tartibida birlashtirish
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if hmac.compare_digest(calculated_hash, received_hash):
        return parsed_data
    return None
```

### 5.2. Asosiy REST API Endpointlari

#### 1. Kotirovka olish (Aniq narx kalkulyatori):
- **POST** `/api/v1/quotes/calculate`
- **Request:**
  ```json
  {
    "rental_unit_id": "b78b0a99-9d51-4d37-8854-9345c26b8b1a",
    "checkin_time": "2026-07-15T14:00:00+05:00",
    "checkout_time": "2026-07-17T12:00:00+05:00",
    "guests_count": 8,
    "tandir_preorder_kg": 3.0
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "quote_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_at": "2026-07-15T12:30:00Z",
    "nights": 2,
    "breakdown": {
      "accommodation_total": 3000000,
      "tandir_meat_total": 450000,
      "grand_total": 3450000,
      "platform_fee_online": 350000,
      "payable_on_arrival_to_owner": 3100000
    }
  }
  ```

#### 2. Bron yaratish (Idempotent):
- **POST** `/api/v1/bookings/create`
- **Header:** `Idempotency-Key: e4b6c867-27b0-4573-a621-e2307ef50123`
- **Request:**
  ```json
  {
    "quote_token": "eyJhbGciOiJIUzI1NiIs...",
    "guest_phone": "+998901234567",
    "guest_name": "Sardor Aliyev"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "booking_reference": "ZS-2026-8812",
    "status": "PENDING_OWNER",
    "hold_expires_at": "2026-07-15T12:45:00Z",
    "message": "Bron dacha egasiga tasdiqlash uchun yuborildi."
  }
  ```

---

## 6. FINITE STATE MACHINE (FSM) VA RBAC MATRITSASI

### 6.1. Bron Jarayoni Holatlar Mashinasi
```
               [FOYDALANUVCHI SO'ROVI]
                         │
                         ▼
                  [PENDING_OWNER]
                   │           │
   (Ega rad etdi / │           │ (Ega 15 daqiqada tasdiqladi)
   15 daqiqa o'tdi)│           ▼
                   │   [AWAITING_PAYMENT] ──(15 daqiqada to'lanmadi)──► [PAYMENT_EXPIRED]
                   │           │
                   │           │ (Click/Payme 10% xizmat haqi to'landi)
                   ▼           ▼
           [DECLINED/EXPIRED] [CONFIRMED]
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
         [CHECKED_IN]                   [CANCELLED]
         (Bog'bon kalit topshirdi)      (Bekor qilish siyosati bo'yicha)
                │
                ▼
          [COMPLETED] ──► (Haqiqiy sharh va reyting yozish ochiladi)
```

### 6.2. Granular RBAC Ruxsatlar Matritsasi

| Amallar va Huquqlar | Mehmon (Guest) | Dacha Egasi (Owner) | Bog‘bon (Caretaker) | Moderator | Moliyachi (Finance) | SuperAdmin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Dacha va tapchanlarni qidirish/ko‘rish | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bron so‘rovi yuborish | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| O‘z dachasi narx va kalendarini yopish | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Bronni tasdiqlash / rad etish | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Mehmon kelganini tasdiqlash (Check-in) | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| E’lonni tekshirish va tasdiqlash | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| To‘lov callbacklari va solishtirish | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Avtomatik pul qaytarish (Auto-refund) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## 7. SINOV VA QABUL QILISH MEZONLARI (ACCEPTANCE CRITERIA)

| ID | Sinov Ssenariysi | Kutilgan Texnik Natija |
| :--- | :--- | :--- |
| **AC-01** | Ikki mijoz bir vaqtda (1 ms farq) bitta dachani ayni bir sanaga bron qilishga urinsa | PostgreSQL `TSTZRANGE` GiST exclusion constraint bittasini qabul qiladi, ikkinchisiga 409 Conflict qaytaradi. |
| **AC-02** | Choyxona tapchanini kunduzi 10:00–16:00 ga bir mijoz, 17:00–23:00 ga boshqa mijoz olsa | Ikkala bron ham muvaffaqiyatli o‘tadi (vaqt oraliqlari ustma-ust tushmaydi). |
| **AC-03** | Ega narxni 2 mln dan 3 mln ga oshirsa | Avvalroq yaratilgan bronning summasi mutlaqo o‘zgarmaydi (`quotes` snapshot daxlsiz). |
| **AC-04** | Click/Payme bir xil to‘lov webhookini tarmoq uzilishi sababli 3 marta yuborsa | Idempotency kaliti sababli faqat 1-marta qayta ishlanadi, ortiqcha amal bajarilmaydi. |
| **AC-05** | Sayyoh 15 daqiqada xizmat haqini to‘lamasa | Celery worker va Lazy Invalidation joyni bo‘shatadi (`HOLD` -> `EXPIRED`), kalendar ochiladi. |
| **AC-06** | To‘lov hold muddati tugagandan so‘ng kelsa va joy boshqa mehmonga o‘tib ketgan bo‘lsa | GiST constraint xatoni ushlaydi, to‘lov `CONFLICTED_EXPIRED` bo‘ladi, provayder orqali mijoz kartasiga **100% pul avtomatik qaytariladi**. |
| **AC-07** | Ega begona dacha identifikatorini manipulyatsiya qilsa | Backend 403 Forbidden qaytaradi (BOLA himoyasi). |
| **AC-08** | Telegram `initData` soxtalashtirilsa yoki `auth_date` 24 soatdan eski bo‘lsa | Backend 401 Unauthorized qaytaradi (HMAC va Replay tekshiruvi). |
| **AC-09** | Sayyoh Zomin tog‘ining chuqur soylarida internet yo‘q joyga tushib qolsa | PWA Service Worker vaucher va marshrutni ochadi, aloqa va GPS koordinata ko‘rinadi. |
| **AC-10** | Dacha egasi yangi bronga 10 daqiqa javob bermasa | IVR ovozli robot egaga telefon qilib botni tekshirishni eslatadi. |
| **AC-11** | Foydalanuvchi "Spark chiqadigan yo‘l" va "Generator bor" filtrini tanlasa | Faqat `ASPHALT_SEDAN` va `has_generator=True` bo‘lgan dachalar filtrlanadi. |
| **AC-12** | Mehmon "Zomin tandiri" buyurtmasini qo‘shsa | Tandir buyurtmasi kg miqdori va tayyor bo‘lish vaqti bilan birga oshxonaga yuboriladi. |
| **AC-13** | Qidiruv sanasiz amalga oshirilsa | Katalog narxlarni "boshlang‘ich narx" sifatida ko‘rsatadi, yolg‘on "bo‘sh" belgisi berilmaydi. |
| **AC-14** | Bog‘bon o‘z akkaunti bilan kirsa | Bog‘bonga faqat mehmonni kutib olish tugmasi ko‘rinadi, moliyaviy hisobotlar yashiriladi. |
| **AC-15** | To‘lov muvaffaqiyatli o‘tgach | Soliq OFD elektron chek havolasi shakllanadi va mijozga taqdim etiladi. |
| **AC-16** | Mehmon safarni yakunlagach | Faqat tasdiqlangan bron egasiga 5 mezon bo‘yicha haqqoniy sharh qoldirish ruxsati beriladi. |

---

## 8. ISHLAB CHIQISH VA AMALGA OSHIRISH REJASI (ROADMAP)

- **1-Bosqich (Hafta 1–3):** Baza sxemasi (PostgreSQL + PostGIS), Django Ninja API va Double-Bookingga qarshi GiST mexanizmini joriy etish.
- **2-Bosqich (Hafta 4–5):** Dacha egalari uchun `@ZominStayOwnerBot` (Telegram Bot) va Qarovchi (Bog‘bon) interfeysini ishga tushirish.
- **3-Bosqich (Hafta 6–7):** Next.js veb-sayt va Telegram Mini App (sayyohlar uchun qidiruv, xarita, filtrlar, Click/Payme to‘lov).
- **4-Bosqich (Hafta 8):** Zomin Duoba hududidagi 30 ta dacha va 10 ta choyxonani shaxsan tekshiruvdan o‘tkazib, bazaga kiritish (ZominStay Verified) va pilot start.
