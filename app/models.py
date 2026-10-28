from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    phone_number: str
    full_name: Optional[str] = None
    telegram_id: Optional[int] = None
    role: str = "GUEST"

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: str
    updated_at: str

class DayUseSlotResponse(BaseModel):
    id: str
    rental_unit_id: str
    slot_name: str
    start_time: str
    end_time: str
    price_weekday: float
    price_weekend: float

class RentalUnitResponse(BaseModel):
    id: str
    property_id: str
    name: str
    unit_category: str  # 'OVERNIGHT_STAY', 'DAY_USE_TAPCHAN'
    standard_capacity: int
    max_capacity: int
    base_price_weekday: float
    base_price_weekend: float
    is_active: bool
    slots: List[DayUseSlotResponse] = []

class PropertyBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    property_type: str
    region: str = "ZOMIN"
    micro_district: str
    address_text: str
    latitude: float
    longitude: float
    location_precision: str = "APPROXIMATE"
    road_condition: str
    has_generator: bool = False
    water_source: str
    heating_type: str
    mobile_coverage: str

class PropertyListItem(PropertyBase):
    id: str
    owner_id: str
    verification_status: str
    is_published: bool
    photos: List[str] = []
    amenities: List[str] = []
    min_price: float
    rental_units: List[RentalUnitResponse] = []

class PropertyDetailResponse(PropertyListItem):
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    caretakers_count: int = 0

class QuoteRequest(BaseModel):
    rental_unit_id: str
    checkin_time: str   # ISO string e.g. "2026-07-15T14:00:00+05:00"
    checkout_time: str  # ISO string e.g. "2026-07-17T12:00:00+05:00"
    guests_count: int = 2
    day_use_slot_name: Optional[str] = None # e.g. 'FULL_DAY', 'LUNCH', 'DINNER' for tapchans
    tandir_preorder_kg: float = 0.0

class QuoteBreakdown(BaseModel):
    accommodation_total: float
    tandir_meat_total: float
    grand_total: float
    platform_fee_online: float
    payable_on_arrival_to_owner: float

class QuoteResponse(BaseModel):
    quote_token: str
    expires_at: str
    nights_or_days: int
    booking_type: str
    breakdown: QuoteBreakdown

class BookingCreateRequest(BaseModel):
    quote_token: str
    guest_phone: str
    guest_name: str
    car_plate: Optional[str] = None
    special_notes: Optional[str] = None

class BookingResponse(BaseModel):
    id: str
    booking_reference: str
    status: str
    hold_expires_at: Optional[str] = None
    total_amount: float
    platform_fee_amount: float
    pay_on_arrival_amount: float
    message: str

class BookingDetailResponse(BaseModel):
    id: str
    booking_reference: str
    rental_unit_id: str
    unit_name: str
    property_id: str
    property_title: str
    micro_district: str
    property_type: str
    guest_id: str
    guest_name: str
    guest_phone: str
    car_plate: Optional[str] = None
    booking_type: str
    checkin_time: str
    checkout_time: str
    guest_count: int
    currency: str
    unit_base_amount: Optional[float] = None
    platform_fee_amount: Optional[float] = None
    pay_on_arrival_amount: Optional[float] = None
    total_amount: Optional[float] = None
    booking_status: str
    hold_expires_at: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: str
    tandir_preorder_kg: float = 0.0
    tandir_amount: float = 0.0
    fiscal_receipt_url: Optional[str] = None

class VoucherNavigation(BaseModel):
    geo_uri: str
    yandex_maps_url: str
    google_maps_url: str
    latitude: float
    longitude: float

class OfflineVoucher(BaseModel):
    booking_reference: str
    booking_status: str
    property_title: str
    micro_district: str
    address_text: str
    road_condition: str
    road_condition_advice: str
    has_generator: bool
    water_source: str
    mobile_coverage: str
    guest_name: str
    guest_phone: str
    car_plate: Optional[str] = None
    guest_count: int
    checkin_time: str
    checkout_time: str
    owner_phone: str
    owner_name: str
    caretaker_phone: Optional[str] = None
    caretaker_name: Optional[str] = None
    payable_on_arrival_to_owner: float
    step_by_step_directions: str
    navigation: VoucherNavigation
    tandir_order: Optional[str] = None
    offline_qr_data: str

class ReviewCreateRequest(BaseModel):
    booking_id: str
    rating_cleanliness: int = Field(..., ge=1, le=5)
    rating_accuracy: int = Field(..., ge=1, le=5)
    rating_communication: int = Field(..., ge=1, le=5)
    rating_comfort: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: str
    property_id: str
    guest_name: str
    rating_cleanliness: int
    rating_accuracy: int
    rating_communication: int
    rating_comfort: int
    overall_rating: float
    comment: Optional[str]
    owner_reply: Optional[str]
    created_at: str

# Admin Panel Schemas (TZ 9)
class AdminDashboardStats(BaseModel):
    total_gmv: float
    total_platform_fee: float
    total_bookings: int
    confirmed_bookings: int
    pending_bookings: int
    total_properties: int
    verified_properties: int
    total_users: int
    ivr_calls_count: int

class AdminPropertyVerifyRequest(BaseModel):
    admin_id: str
    status: str # 'VERIFIED', 'REJECTED'
    notes: Optional[str] = None

class AdminForceCancelRequest(BaseModel):
    admin_id: str
    reason: str

class AdminUserStatusRequest(BaseModel):
    admin_id: str
    is_active: bool
    role: Optional[str] = None

