import sqlite3
import json
import uuid
import threading
from datetime import datetime, timezone, timedelta
from typing import Iterator, Optional, Dict, Any, List
from contextlib import contextmanager

from app.config import settings

_db_lock = threading.RLock()

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or settings.DATABASE_PATH
    conn = sqlite3.connect(path, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db(db_path: Optional[str] = None) -> Iterator[sqlite3.Connection]:
    with _db_lock:
        conn = get_connection(db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

def init_db(db_path: Optional[str] = None) -> None:
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Users
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            phone_number TEXT UNIQUE NOT NULL,
            full_name TEXT,
            telegram_id INTEGER UNIQUE,
            role TEXT NOT NULL DEFAULT 'GUEST',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id);")

        # 2. Properties
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            property_type TEXT NOT NULL, -- 'VILLA', 'COTTAGE', 'GUEST_HOUSE', 'CHOYXONA_TAPCHAN'
            region TEXT NOT NULL DEFAULT 'ZOMIN',
            micro_district TEXT NOT NULL, -- 'DUOBA', 'ORIKLISOY', 'SUFFA', 'SANATORIY', 'DASHTOBOD'
            address_text TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            location_precision TEXT NOT NULL DEFAULT 'APPROXIMATE',
            
            -- Mountain infrastructure
            road_condition TEXT NOT NULL, -- 'ASPHALT_SEDAN', 'HIGH_CLEARANCE', '4WD_ONLY', 'WINTER_CHAINS'
            has_generator INTEGER NOT NULL DEFAULT 0,
            water_source TEXT NOT NULL, -- 'SPRING_WATER', 'TAP_WATER', 'TANKER'
            heating_type TEXT NOT NULL, -- 'GAS_CENTRAL', 'WOOD_STOVE', 'ELECTRIC_FLOOR', 'AC'
            mobile_coverage TEXT NOT NULL, -- '4G_EXCELLENT', '3G_MEDIUM', 'VOICE_ONLY', 'NO_SIGNAL'
            
            verification_status TEXT NOT NULL DEFAULT 'VERIFIED',
            is_published INTEGER NOT NULL DEFAULT 1,
            photos_json TEXT NOT NULL DEFAULT '[]',
            amenities_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_district ON properties(micro_district);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_type ON properties(property_type);")

        # 3. Rental Units
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rental_units (
            id TEXT PRIMARY KEY,
            property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            unit_category TEXT NOT NULL, -- 'OVERNIGHT_STAY', 'DAY_USE_TAPCHAN'
            standard_capacity INTEGER NOT NULL DEFAULT 8,
            max_capacity INTEGER NOT NULL DEFAULT 12,
            base_price_weekday REAL NOT NULL,
            base_price_weekend REAL NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_units_property ON rental_units(property_id);")

        # 4. Day Use Slots
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS day_use_slots (
            id TEXT PRIMARY KEY,
            rental_unit_id TEXT NOT NULL REFERENCES rental_units(id) ON DELETE CASCADE,
            slot_name TEXT NOT NULL, -- 'FULL_DAY', 'LUNCH', 'DINNER'
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            price_weekday REAL NOT NULL,
            price_weekend REAL NOT NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_slots_unit ON day_use_slots(rental_unit_id);")

        # 5. Bookings
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            booking_reference TEXT UNIQUE NOT NULL,
            rental_unit_id TEXT NOT NULL REFERENCES rental_units(id) ON DELETE RESTRICT,
            guest_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            guest_name TEXT NOT NULL,
            guest_phone TEXT NOT NULL,
            car_plate TEXT,
            booking_type TEXT NOT NULL, -- 'OVERNIGHT', 'DAY_USE'
            checkin_time TEXT NOT NULL,
            checkout_time TEXT NOT NULL,
            guest_count INTEGER NOT NULL,
            currency TEXT NOT NULL DEFAULT 'UZS',
            unit_base_amount REAL NOT NULL,
            platform_fee_amount REAL NOT NULL,
            pay_on_arrival_amount REAL NOT NULL,
            total_amount REAL NOT NULL,
            booking_status TEXT NOT NULL DEFAULT 'PENDING_OWNER',
            hold_expires_at TEXT,
            cancellation_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_ref ON bookings(booking_reference);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(booking_status);")

        # 6. Inventory Allocations (Concurrency & Double-Booking engine)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_allocations (
            id TEXT PRIMARY KEY,
            rental_unit_id TEXT NOT NULL REFERENCES rental_units(id) ON DELETE CASCADE,
            booking_id TEXT REFERENCES bookings(id) ON DELETE CASCADE,
            allocation_type TEXT NOT NULL, -- 'PLATFORM_HOLD', 'CONFIRMED_BOOKING', 'OWNER_MANUAL', 'MAINTENANCE'
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT NOT NULL, -- 'ACTIVE', 'EXPIRED', 'CANCELLED'
            expires_at TEXT,
            created_at TEXT NOT NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_allocations_unit_status ON inventory_allocations(rental_unit_id, status);")

        # 7. Food Pre-orders
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS booking_food_orders (
            id TEXT PRIMARY KEY,
            booking_id TEXT NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
            dish_name TEXT NOT NULL DEFAULT 'Zomin Archa Tandiri',
            quantity_kg REAL NOT NULL,
            target_serving_time TEXT NOT NULL,
            price_per_kg REAL NOT NULL,
            total_food_amount REAL NOT NULL,
            special_notes TEXT
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_food_orders_booking ON booking_food_orders(booking_id);")

        # 8. Payment Attempts
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_attempts (
            id TEXT PRIMARY KEY,
            booking_id TEXT NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
            provider TEXT NOT NULL, -- 'CLICK', 'PAYME', 'UZUM'
            provider_transaction_id TEXT,
            amount_in_tiyin INTEGER NOT NULL,
            amount_uzs REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'INITIATED',
            idempotency_key TEXT UNIQUE NOT NULL,
            provider_payload TEXT,
            fiscal_receipt_url TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_trans ON payment_attempts(provider, provider_transaction_id);")

        # 9. Caretakers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS property_caretakers (
            id TEXT PRIMARY KEY,
            property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
            caretaker_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            can_confirm_arrival INTEGER NOT NULL DEFAULT 1,
            notes TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(property_id, caretaker_id)
        );
        """)

        # 10. Reviews
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            booking_id TEXT UNIQUE NOT NULL REFERENCES bookings(id) ON DELETE RESTRICT,
            property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
            guest_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            rating_cleanliness INTEGER NOT NULL,
            rating_accuracy INTEGER NOT NULL,
            rating_communication INTEGER NOT NULL,
            rating_comfort INTEGER NOT NULL,
            overall_rating REAL NOT NULL,
            comment TEXT,
            owner_reply TEXT,
            is_verified_stay INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        """)

        # 11. IVR Call Logs (AC-10: 10-minute owner reminder)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ivr_call_logs (
            id TEXT PRIMARY KEY,
            booking_id TEXT NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
            owner_phone TEXT NOT NULL,
            call_status TEXT NOT NULL DEFAULT 'COMPLETED',
            spoken_message TEXT NOT NULL,
            dispatched_at TEXT NOT NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ivr_booking ON ivr_call_logs(booking_id);")

        # 12. Audit Logs (TZ 9.2: Operation Audit Trail)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT,
            details TEXT,
            created_at TEXT NOT NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at);")

        # Database Engine Exclusion Constraints (Triggers emulating PostgreSQL GiST exclusion)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_prevent_double_booking_insert
        BEFORE INSERT ON inventory_allocations
        FOR EACH ROW
        WHEN NEW.status = 'ACTIVE'
        BEGIN
            SELECT RAISE(ABORT, 'Double-booking violation: Active allocation already exists for this unit and time range')
            WHERE EXISTS (
                SELECT 1 FROM inventory_allocations
                WHERE rental_unit_id = NEW.rental_unit_id
                  AND status = 'ACTIVE'
                  AND start_time < NEW.end_time
                  AND end_time > NEW.start_time
            );
        END;
        """)

        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_prevent_double_booking_update
        BEFORE UPDATE ON inventory_allocations
        FOR EACH ROW
        WHEN NEW.status = 'ACTIVE'
        BEGIN
            SELECT RAISE(ABORT, 'Double-booking violation: Active allocation already exists for this unit and time range')
            WHERE EXISTS (
                SELECT 1 FROM inventory_allocations
                WHERE id != NEW.id
                  AND rental_unit_id = NEW.rental_unit_id
                  AND status = 'ACTIVE'
                  AND start_time < NEW.end_time
                  AND end_time > NEW.start_time
            );
        END;
        """)

def seed_initial_data(db_path: Optional[str] = None) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            return  # Already seeded
            
        # Demo Users
        admin_id = str(uuid.uuid4())
        owner1_id = str(uuid.uuid4())
        owner2_id = str(uuid.uuid4())
        caretaker1_id = str(uuid.uuid4())
        guest1_id = str(uuid.uuid4())
        
        users_data = [
            (admin_id, "+998900000001", "ZominStay Platform Admin", 10001, "ADMIN", 1, now_iso, now_iso),
            (owner1_id, "+998901112233", "Alisher Zokirov (Duoba Dacha Egasi)", 20002, "OWNER", 1, now_iso, now_iso),
            (owner2_id, "+998904445566", "Muzaffar Raimov (Suffa & O'riklisoy Egasi)", 20003, "OWNER", 1, now_iso, now_iso),
            (caretaker1_id, "+998917778899", "Rustam Tog'a (Duoba Qarovchisi)", 30001, "CARETAKER", 1, now_iso, now_iso),
            (guest1_id, "+998935551122", "Jasur Mamadaliyev (Sayyoh)", 40001, "GUEST", 1, now_iso, now_iso),
        ]
        cursor.executemany("""
            INSERT INTO users (id, phone_number, full_name, telegram_id, role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, users_data)
        
        # Properties
        prop1_id = str(uuid.uuid4()) # Duoba Villa
        prop2_id = str(uuid.uuid4()) # Suffa Chalet
        prop3_id = str(uuid.uuid4()) # O'riklisoy Choyxona & Tapchanlar
        prop4_id = str(uuid.uuid4()) # Sanatoriy Family Guest House
        
        properties_data = [
            (
                prop1_id, owner1_id,
                "Mountain Chalet Zomin",
                "mountain-chalet-zomin",
                "Tog‘ manzarali, yog‘och uy. Oila va do‘stlar uchun ideal. Zomin tog'larining baland archazorlarida, toza havo va tinch tabiat qo'ynida joylashgan zamonaviy yog'och kottej.",
                "COTTAGE", "ZOMIN", "SUFFA",
                "Suffa platosi, Dor yo'li yaqinida, Zomin",
                39.8715, 68.4520, "EXACT",
                "ASPHALT_SEDAN", 1, "SPRING_WATER", "WOOD_STOVE", "4G_EXCELLENT",
                "VERIFIED", 1,
                json.dumps([
                    "/static/assets/chalet.jpg",
                    "https://images.unsplash.com/photo-1542718610-a1d656d1884c?auto=format&fit=crop&w=1200&q=80"
                ]),
                json.dumps(["Tog' manzarasi", "Kamin", "Balkon/Ayvon", "Wi-Fi", "Oila uchun shinam", "Mangal"]),
                now_iso, now_iso
            ),
            (
                prop2_id, owner2_id,
                "Zomin Villa",
                "zomin-villa",
                "Shaxsiy hovuz, zamonaviy qulayliklar va betakror manzara. Duoba soyi bo'yida joylashgan hashamatli 2 qavatli villa. Qishki va yozgi isitiladigan basseyn, fin saunasi, keng shiypon.",
                "VILLA", "ZOMIN", "DUOBA",
                "Duoba MFY, Soy bo'yi ko'chasi 14-uy, Zomin",
                39.9612, 68.4231, "EXACT",
                "ASPHALT_SEDAN", 1, "SPRING_WATER", "GAS_CENTRAL", "4G_EXCELLENT",
                "VERIFIED", 1,
                json.dumps([
                    "/static/assets/villa.jpg",
                    "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80"
                ]),
                json.dumps(["Shaxsiy hovuz (Basseyn)", "Sauna", "Bilyard", "Smart TV", "Tandir & Mangal", "Wi-Fi 4G"]),
                now_iso, now_iso
            ),
            (
                prop3_id, owner1_id,
                "Forest Lodge",
                "forest-lodge",
                "Tabiat bag‘rida, sokin va qulay dam olish maskani. Qarag'ayzor va archazorlar o'rtasida joylashgan yog'och eko-lodge. Tinchlik, toza buloq suvi va oilaviy osoyishtalik.",
                "GUEST_HOUSE", "ZOMIN", "SANATORIY",
                "Sanatoriy ko'chasi 8-uy, Zomin",
                39.9450, 68.4110, "APPROXIMATE",
                "ASPHALT_SEDAN", 1, "SPRING_WATER", "GAS_CENTRAL", "4G_EXCELLENT",
                "VERIFIED", 1,
                json.dumps([
                    "/static/assets/lodge.jpg",
                    "https://images.unsplash.com/photo-1510798831971-661eb04b3739?auto=format&fit=crop&w=1200&q=80"
                ]),
                json.dumps(["Qarag'ayzor", "Oshxona barcha jihozlar bilan", "Wi-Fi", "Buloq suvi", "Tinch hordiq"]),
                now_iso, now_iso
            ),
            (
                prop4_id, owner2_id,
                "O'riklisoy Buloq Bo'yi Choyxonasi & Tapchanlari",
                "oriklisoy-buloq-boyi-tapchanlar",
                "O'riklisoyning salqin tog' suvlari ustida qurilgan milliy tapchanlar majmuasi. Kunduzgi hordiq, oilaviy dam olish, archa tandiri va muzdek buloq tarvuzi uchun ideal go'sha. Spark va yengil mashinalar bemalol boradi.",
                "CHOYXONA_TAPCHAN", "ZOMIN", "ORIKLISOY",
                "O'riklisoy dam olish hududi, Buloqboshi, Zomin",
                39.9210, 68.3980, "APPROXIMATE",
                "ASPHALT_SEDAN", 0, "SPRING_WATER", "AC", "4G_EXCELLENT",
                "VERIFIED", 1,
                json.dumps([
                    "/static/assets/hiking.jpg",
                    "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=1200&q=80"
                ]),
                json.dumps(["Suv ustidagi tapchan", "Zomin archa tandiri (buyurtmaga)", "Samovar choy", "Buloq suvi", "Soyda suzish"]),
                now_iso, now_iso
            )
        ]
        
        cursor.executemany("""
            INSERT INTO properties (
                id, owner_id, title, slug, description, property_type, region, micro_district,
                address_text, latitude, longitude, location_precision, road_condition,
                has_generator, water_source, heating_type, mobile_coverage,
                verification_status, is_published, photos_json, amenities_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, properties_data)
        
        # Caretaker link for Property 1
        cursor.execute("""
            INSERT INTO property_caretakers (id, property_id, caretaker_id, can_confirm_arrival, notes, created_at)
            VALUES (?, ?, ?, 1, 'Duoba qarovchisi Rustam tog''a. Darvoza kaliti unda.', ?)
        """, (str(uuid.uuid4()), prop1_id, caretaker1_id, now_iso))
        
        # Rental Units
        unit1_id = str(uuid.uuid4()) # Duoba Full Villa
        unit2_id = str(uuid.uuid4()) # Suffa Chalet
        unit3_id = str(uuid.uuid4()) # O'riklisoy Tapchan 1
        unit4_id = str(uuid.uuid4()) # O'riklisoy Tapchan 2
        unit5_id = str(uuid.uuid4()) # Sanatoriy Guest House
        
        rental_units_data = [
            (unit1_id, prop1_id, "Butun Tog' Chaleti", "OVERNIGHT_STAY", 6, 8, 1200000.0, 1600000.0, 1, now_iso),
            (unit2_id, prop2_id, "Hashamatli Basseynli Villa", "OVERNIGHT_STAY", 8, 14, 2500000.0, 3200000.0, 1, now_iso),
            (unit3_id, prop3_id, "Shinam Yog'och Lodge", "OVERNIGHT_STAY", 4, 6, 900000.0, 1200000.0, 1, now_iso),
            (unit4_id, prop4_id, "Soy Ustidagi 1-Katta Tapchan", "DAY_USE_TAPCHAN", 8, 12, 150000.0, 250000.0, 1, now_iso),
            (unit5_id, prop4_id, "Sharshara Yonidagi 2-Tapchan", "DAY_USE_TAPCHAN", 6, 10, 150000.0, 200000.0, 1, now_iso),
        ]
        
        cursor.executemany("""
            INSERT INTO rental_units (
                id, property_id, name, unit_category, standard_capacity, max_capacity,
                base_price_weekday, base_price_weekend, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rental_units_data)
        
        # Day Use Slots for Tapchans
        slots_data = [
            (str(uuid.uuid4()), unit4_id, "FULL_DAY", "10:00:00", "22:00:00", 300000.0, 450000.0),
            (str(uuid.uuid4()), unit4_id, "LUNCH", "10:00:00", "16:00:00", 180000.0, 250000.0),
            (str(uuid.uuid4()), unit4_id, "DINNER", "17:00:00", "23:00:00", 200000.0, 280000.0),
            
            (str(uuid.uuid4()), unit5_id, "FULL_DAY", "10:00:00", "22:00:00", 250000.0, 350000.0),
            (str(uuid.uuid4()), unit5_id, "LUNCH", "10:00:00", "16:00:00", 150000.0, 200000.0),
            (str(uuid.uuid4()), unit5_id, "DINNER", "17:00:00", "23:00:00", 160000.0, 220000.0),
        ]
        
        cursor.executemany("""
            INSERT INTO day_use_slots (
                id, rental_unit_id, slot_name, start_time, end_time, price_weekday, price_weekend
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, slots_data)
