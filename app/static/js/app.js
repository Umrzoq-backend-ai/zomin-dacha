// ZominStay Master Application Logic & Real-Time State
let currentPortal = 'guest';
let propertiesCache = [];
let selectedProperty = null;
let currentQuote = null;
let currentBooking = null;
let currentTandirKg = 0;
let currentDayUseSlot = null; // 'FULL_DAY', 'LUNCH', 'DINNER'
let currentBookingMode = 'OVERNIGHT'; // 'OVERNIGHT' or 'DAY_USE'
let holdTimerInterval = null;

// Filter & Sort State
let activeDistrict = 'ALL';
let filterRoad = null;
let filterGenerator = null;
let filterType = null;
let currentSort = 'RECOMMENDED';

// Demo Profiles Matrix
const DEMO_PROFILES = {
  guest: { phone: '+998935551122', name: 'Jasur Mamadaliyev', role: 'GUEST', label: '🏕️ Jasur M. (Sayyoh)' },
  owner1: { phone: '+998901112233', name: 'Alisher Zokirov', role: 'OWNER', label: '🏡 Alisher Z. (Duoba Dacha Egasi)' },
  owner2: { phone: '+998904445566', name: 'Muzaffar Raimov', role: 'OWNER', label: '🏡 Muzaffar R. (Suffa & O\'riklisoy Egasi)' },
  caretaker: { phone: '+998917778899', name: 'Rustam Tog\'a', role: 'CARETAKER', label: '🔑 Rustam Tog\'a (Duoba Bog\'boni)' },
  admin: { phone: '+998900000001', name: 'Sanjar Karimov', role: 'ADMIN', label: '🛡️ Sanjar K. (Platforma Admini)' }
};

let currentUser = null;

// Toast Helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? '✅' : (type === 'error' ? '❌' : 'ℹ️');
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Initialize on DOM load
window.addEventListener('DOMContentLoaded', async () => {
  // Telegram Mini App SDK integration
  if (window.Telegram && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor('#064e3b');
      tg.setBackgroundColor('#f8fafc');
    } catch (e) {}

    if (tg.initData) {
      try {
        const r = await fetch('/api/v1/auth/telegram-webapp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ init_data: tg.initData })
        });
        if (r.ok) {
          currentUser = await r.json();
          updateHeaderUserInfo();
        }
      } catch (err) {
        console.log('Telegram auth fallback:', err);
      }
    }
  }

  // Default demo user: Guest
  if (!currentUser) {
    await switchUserProfile('guest', false);
  }

  initDefaultDates();
  await loadProperties();
  refreshBadges();
});

// Update Header User Info Display
function updateHeaderUserInfo() {
  if (!currentUser) return;
  const nameEl = document.getElementById('header-user-name');
  const roleEl = document.getElementById('header-user-role');
  const avatarEl = document.getElementById('header-user-avatar');
  
  if (nameEl) nameEl.innerText = currentUser.full_name;
  if (roleEl) roleEl.innerText = currentUser.role;
  if (avatarEl) {
    avatarEl.innerText = currentUser.role === 'ADMIN' ? '🛡️' : (currentUser.role === 'OWNER' ? '🏡' : (currentUser.role === 'CARETAKER' ? '🔑' : '👤'));
  }
}

// User Profile Switching
async function switchUserProfile(profileKey, reloadData = true) {
  const profile = DEMO_PROFILES[profileKey];
  if (!profile) return;

  try {
    const res = await fetch('/api/v1/auth/quick-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone_number: profile.phone,
        full_name: profile.name,
        role: profile.role
      })
    });
    if (res.ok) {
      currentUser = await res.json();
      const sel = document.getElementById('user-profile-select');
      if (sel) sel.value = profileKey;
      updateHeaderUserInfo();

      if (reloadData) {
        showToast(`Profil faollashtirildi: ${currentUser.full_name}`, 'info');
        if (currentPortal === 'owner') loadOwnerData();
        else if (currentPortal === 'caretaker') loadCaretakerArrivals();
        else if (currentPortal === 'trips') loadMyTrips();
        refreshBadges();
      }
    }
  } catch (e) {
    console.error('Failed to switch profile:', e);
  }
}

function initDefaultDates() {
  const now = new Date();
  const tomorrow = new Date(now);
  tomorrow.setDate(now.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split('T')[0];

  const checkoutDate = new Date(tomorrow);
  checkoutDate.setDate(tomorrow.getDate() + 2);
  const checkoutStr = checkoutDate.toISOString().split('T')[0];

  const inField = document.getElementById('search-checkin');
  const outField = document.getElementById('search-checkout');
  if (inField && outField) {
    inField.value = tomorrowStr;
    outField.value = checkoutStr;
  }
}

// Switching Portal Views
function switchPortal(portal) {
  currentPortal = portal;

  // Update desktop navigation tabs
  document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
  const activeDesktopTab = document.getElementById(
    portal === 'guest' ? 'tab-guest-dachas' : 
    (portal === 'owner' ? 'tab-owner-portal' : 
    (portal === 'caretaker' ? 'tab-caretaker-portal' : 
    (portal === 'trips' ? 'tab-my-trips' : 
    (portal === 'admin' ? 'tab-admin-portal' : 'tab-map-guide'))))
  );
  if (activeDesktopTab) activeDesktopTab.classList.add('active');

  // Update mobile bottom nav items
  document.querySelectorAll('.mobile-nav-item').forEach(b => b.classList.remove('active'));
  const mobItem = document.getElementById(
    portal === 'guest' ? 'mob-nav-guest' : 
    (portal === 'owner' ? 'mob-nav-owner' : 
    (portal === 'trips' ? 'mob-nav-trips' : 
    (portal === 'admin' ? 'mob-nav-admin' : 'mob-nav-tapchan')))
  );
  if (mobItem) mobItem.classList.add('active');

  // Hide all portal views
  document.querySelectorAll('.portal-view').forEach(p => p.classList.add('hidden'));

  // Show target view
  const targetView = document.getElementById(`portal-${portal}`);
  if (targetView) targetView.classList.remove('hidden');

  if (portal === 'guest') {
    loadProperties();
  } else if (portal === 'owner') {
    if (currentUser && currentUser.role !== 'OWNER') {
      switchUserProfile('owner1', true);
    } else {
      loadOwnerData();
    }
  } else if (portal === 'caretaker') {
    if (currentUser && currentUser.role !== 'CARETAKER') {
      switchUserProfile('caretaker', true);
    } else {
      loadCaretakerArrivals();
    }
  } else if (portal === 'trips') {
    loadMyTrips();
  } else if (portal === 'admin') {
    if (currentUser && currentUser.role !== 'ADMIN') {
      switchUserProfile('admin', true);
    } else {
      loadAdminStats();
    }
  }
}

// Quick filter helper for Tapchans
function filterToTapchans() {
  document.querySelectorAll('.pill-chip').forEach(c => c.classList.remove('active'));
  const tapchanBtn = document.getElementById('toggle-tapchan');
  if (tapchanBtn) {
    document.querySelectorAll('.toggle-pill').forEach(b => b.classList.remove('active'));
    tapchanBtn.classList.add('active');
  }
  filterType = 'CHOYXONA_TAPCHAN';
  loadProperties();
}

// Fetch Properties from API
async function loadProperties() {
  const grid = document.getElementById('properties-grid');
  grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:50px; color:#64748b; font-size:15px;">🌲 Zomin dachalari saralanmoqda...</div>';

  const params = new URLSearchParams();
  if (activeDistrict && activeDistrict !== 'ALL') {
    params.append('micro_district', activeDistrict);
  }
  if (filterRoad) {
    params.append('road_condition', filterRoad);
  }
  if (filterGenerator !== null) {
    params.append('has_generator', filterGenerator);
  }
  if (filterType) {
    params.append('property_type', filterType);
  }

  const checkinVal = document.getElementById('search-checkin')?.value;
  const checkoutVal = document.getElementById('search-checkout')?.value;
  if (checkinVal && checkoutVal) {
    params.append('checkin_time', `${checkinVal}T14:00:00`);
    params.append('checkout_time', `${checkoutVal}T12:00:00`);
  }

  const guests = document.getElementById('search-guests')?.value;
  if (guests) {
    params.append('min_guests', guests);
  }

  try {
    const res = await fetch(`/api/v1/properties?${params.toString()}`);
    let properties = await res.json();

    // Client-side sorting
    if (currentSort === 'PRICE_ASC') {
      properties.sort((a, b) => a.min_price - b.min_price);
    } else if (currentSort === 'PRICE_DESC') {
      properties.sort((a, b) => b.min_price - a.min_price);
    }

    propertiesCache = properties;
    const countEl = document.getElementById('results-count-text');
    if (countEl) countEl.innerText = `${properties.length} ta tekshirilgan dacha va tapchan topildi`;

    if (!properties || properties.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding:60px 20px; background:white; border-radius:20px; border:1px solid var(--border);">
          <div style="font-size:42px; margin-bottom:10px;">🔍</div>
          <h3 style="color:#0f172a; font-size:18px; margin-bottom:6px;">Ushbu filtr bo'yicha dacha topilmadi</h3>
          <p style="color:#64748b; font-size:14px; margin-bottom:18px;">Filtrlarni tozalab yoki boshqa hududni tanlab ko'ring.</p>
          <button class="btn-card-select" onclick="resetAllFilters()">Filtrlarni Tozalash</button>
        </div>
      `;
      return;
    }

    grid.innerHTML = properties.map(p => {
      const photo = p.photos && p.photos.length > 0 ? p.photos[0] : 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80';
      const isSedan = p.road_condition === 'ASPHALT_SEDAN';
      const roadBadge = isSedan ? 
        '<span class="tag-badge road-sedan">🚗 Asfalt (Spark/Cobalt)</span>' : 
        '<span class="tag-badge road-4wd">🚙 Tog\' yo\'li / 4WD</span>';
      const genBadge = p.has_generator ? '<span class="tag-badge generator">⚡ Generator bor</span>' : '';
      const typeText = p.property_type === 'VILLA' ? 'Villa / Dacha' : 
                       (p.property_type === 'COTTAGE' ? 'Tog\' Kotteji' : 
                       (p.property_type === 'CHOYXONA_TAPCHAN' ? 'Choyxona & Tapchan' : 'Mehmon Uyi'));
      const rating = (4.8 + (p.title.length % 3) * 0.1).toFixed(1);
      const reviewsCount = 20 + (p.title.length * 3);

      return `
        <div class="prop-card" onclick="openPropertyModal('${p.id}')">
          <div class="prop-img-box">
            <img class="prop-img" src="${photo}" alt="${p.title}" loading="lazy">
            <span class="badge-location-chip">${p.micro_district}</span>
            <span class="badge-type-chip">${typeText}</span>
            <span class="badge-verified-float">✓ Verified</span>
            <span class="badge-rating-float">⭐ ${rating} (${reviewsCount})</span>
          </div>
          <div class="prop-body">
            <h4 class="prop-title">${p.title}</h4>
            <div class="prop-address">📍 ${p.address_text}</div>
            <div class="prop-tags-row">
              ${roadBadge}
              ${genBadge}
              <span class="tag-badge">💧 ${p.water_source === 'SPRING_WATER' ? 'Buloq suvi' : 'Vodoprovod'}</span>
              <span class="tag-badge">📶 ${p.mobile_coverage}</span>
            </div>
            <div class="prop-footer">
              <div>
                <span class="price-sub">boshlang'ich narx</span>
                <span class="price-val">${Number(p.min_price).toLocaleString()} so'm</span>
              </div>
              <button class="btn-card-select">Tanlash &gt;</button>
            </div>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    grid.innerHTML = `<div style="grid-column:1/-1; color:red; text-align:center; padding:30px;">Yuklashda xatolik: ${err.message}</div>`;
  }
}

function selectDistrictPill(el, district) {
  document.querySelectorAll('.pill-chip').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  activeDistrict = district;
  const sel = document.getElementById('search-district');
  if (sel) sel.value = district;
  loadProperties();
}

function toggleFilterChip(el, type, value) {
  const isActive = el.classList.contains('active');
  if (type === 'type') {
    document.querySelectorAll('.toggle-pill[id^="toggle-tapchan"], .toggle-pill[id^="toggle-villa"]').forEach(c => c.classList.remove('active'));
    if (!isActive) {
      el.classList.add('active');
      filterType = value;
    } else {
      filterType = null;
    }
  } else if (type === 'road') {
    el.classList.toggle('active');
    filterRoad = !isActive ? value : null;
  } else if (type === 'generator') {
    el.classList.toggle('active');
    filterGenerator = !isActive ? value : null;
  }
  loadProperties();
}

function applyFilters() {
  const sel = document.getElementById('search-district');
  if (sel) activeDistrict = sel.value;
  loadProperties();
}

function sortProperties(sortBy) {
  currentSort = sortBy;
  loadProperties();
}

function resetAllFilters() {
  activeDistrict = 'ALL';
  filterRoad = null;
  filterGenerator = null;
  filterType = null;
  document.querySelectorAll('.pill-chip').forEach(c => c.classList.remove('active'));
  document.querySelector('.pill-chip')?.classList.add('active');
  document.querySelectorAll('.toggle-pill').forEach(b => b.classList.remove('active'));
  const distSelect = document.getElementById('search-district');
  if (distSelect) distSelect.value = 'ALL';
  loadProperties();
}

// Property Detail & Quote Modal Logic
function openPropertyModal(propId) {
  const p = propertiesCache.find(item => item.id === propId);
  if (!p) return;
  selectedProperty = p;
  currentTandirKg = 0;
  currentDayUseSlot = null;
  document.getElementById('tandir-kg-val').innerText = '0 kg';

  document.getElementById('m-prop-title').innerText = p.title;
  document.getElementById('m-prop-address').innerText = `📍 ${p.address_text}`;
  document.getElementById('m-prop-desc').innerText = p.description;
  const imgUrl = p.photos && p.photos.length > 0 ? p.photos[0] : 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80';
  document.getElementById('m-prop-img').src = imgUrl;

  // Badges
  const badgesArea = document.getElementById('m-prop-badges');
  badgesArea.innerHTML = `
    <span class="tag-badge road-sedan">📍 ${p.micro_district}</span>
    <span class="tag-badge">${p.road_condition}</span>
    ${p.has_generator ? '<span class="tag-badge generator">⚡ Generator bor</span>' : ''}
    <span class="tag-badge">📶 ${p.mobile_coverage}</span>
    <span class="tag-badge">💧 ${p.water_source}</span>
  `;

  // Amenities
  const amenitiesArea = document.getElementById('m-prop-amenities');
  const amenities = p.amenities || ["Isitiladigan basseyn", "Sauna/Fin hammomi", "Zomin archa tandiri", "Wi-Fi 4G", "Soy bo'yi tapchani"];
  amenitiesArea.innerHTML = amenities.map(a => `
    <div class="amenity-chip">✓ ${a}</div>
  `).join('');

  // Units
  const unitSelect = document.getElementById('m-unit-select');
  unitSelect.innerHTML = p.rental_units.map(u => {
    return `<option value="${u.id}">${u.name} (Sig'im: ${u.standard_capacity}–${u.max_capacity} kishi)</option>`;
  }).join('');

  // Default dates
  const inVal = document.getElementById('search-checkin')?.value || new Date().toISOString().split('T')[0];
  const outVal = document.getElementById('search-checkout')?.value || inVal;
  document.getElementById('m-checkin').value = `${inVal}T14:00`;
  document.getElementById('m-checkout').value = `${outVal}T12:00`;

  // Pre-fill guest data if logged in
  if (currentUser) {
    const nameEl = document.getElementById('m-guest-name');
    const phoneEl = document.getElementById('m-guest-phone');
    if (nameEl) nameEl.value = currentUser.full_name;
    if (phoneEl) phoneEl.value = currentUser.phone_number;
  }

  // Set booking mode based on property type
  if (p.property_type === 'CHOYXONA_TAPCHAN') {
    switchBookingMode('DAY_USE');
  } else {
    switchBookingMode('OVERNIGHT');
  }

  document.getElementById('prop-modal').classList.remove('hidden');
  onUnitSelectionChanged();
}

function switchBookingMode(mode) {
  currentBookingMode = mode;
  document.getElementById('btn-mode-stay')?.classList.toggle('active', mode === 'OVERNIGHT');
  document.getElementById('btn-mode-tapchan')?.classList.toggle('active', mode === 'DAY_USE');

  const slotBox = document.getElementById('m-slot-container');
  if (mode === 'DAY_USE') {
    if (slotBox) slotBox.classList.remove('hidden');
    selectDaySlot('FULL_DAY', '10:00', '22:00');
  } else {
    if (slotBox) slotBox.classList.add('hidden');
    currentDayUseSlot = null;
    initDefaultDates();
    const inVal = document.getElementById('search-checkin')?.value;
    const outVal = document.getElementById('search-checkout')?.value;
    document.getElementById('m-checkin').value = `${inVal}T14:00`;
    document.getElementById('m-checkout').value = `${outVal}T12:00`;
    calculateLiveQuote();
  }
}

function onUnitSelectionChanged() {
  const unitId = document.getElementById('m-unit-select').value;
  const unit = selectedProperty?.rental_units?.find(u => u.id === unitId);
  if (unit && unit.unit_category === 'DAY_USE_TAPCHAN') {
    switchBookingMode('DAY_USE');
  } else {
    calculateLiveQuote();
  }
}

function selectDaySlot(slotName, startTime, endTime) {
  currentDayUseSlot = slotName;
  document.querySelectorAll('.slot-choice-pill').forEach(b => b.classList.remove('active'));
  const btnId = slotName === 'FULL_DAY' ? 'slot-full' : (slotName === 'LUNCH' ? 'slot-lunch' : 'slot-dinner');
  const btn = document.getElementById(btnId);
  if (btn) btn.classList.add('active');

  const inVal = document.getElementById('search-checkin')?.value || new Date().toISOString().split('T')[0];
  document.getElementById('m-checkin').value = `${inVal}T${startTime}`;
  document.getElementById('m-checkout').value = `${inVal}T${endTime}`;

  calculateLiveQuote();
}

function changeTandirKg(delta) {
  currentTandirKg = Math.max(0, currentTandirKg + delta);
  document.getElementById('tandir-kg-val').innerText = `${currentTandirKg} kg`;
  calculateLiveQuote();
}

async function calculateLiveQuote() {
  const unitId = document.getElementById('m-unit-select')?.value;
  const checkin = document.getElementById('m-checkin')?.value;
  const checkout = document.getElementById('m-checkout')?.value;

  if (!unitId || !checkin || !checkout) return;

  const payload = {
    rental_unit_id: unitId,
    checkin_time: checkin.includes('T') ? (checkin.length === 16 ? `${checkin}:00+05:00` : checkin) : `${checkin}T14:00:00+05:00`,
    checkout_time: checkout.includes('T') ? (checkout.length === 16 ? `${checkout}:00+05:00` : checkout) : `${checkout}T12:00:00+05:00`,
    guests_count: 4,
    day_use_slot_name: currentDayUseSlot,
    tandir_preorder_kg: currentTandirKg
  };

  try {
    const res = await fetch('/api/v1/quotes/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const quote = await res.json();
    if (!res.ok) {
      showToast(quote.detail || 'Kotirovka hisoblashda xatolik', 'error');
      return;
    }
    currentQuote = quote;

    document.getElementById('q-nights').innerText = quote.nights_or_days;
    document.getElementById('q-acc-total').innerText = `${Number(quote.breakdown.accommodation_total).toLocaleString()} so'm`;
    document.getElementById('q-tandir-total').innerText = `${Number(quote.breakdown.tandir_meat_total).toLocaleString()} so'm`;
    document.getElementById('q-grand-total').innerText = `${Number(quote.breakdown.grand_total).toLocaleString()} so'm`;
    document.getElementById('q-platform-fee').innerText = `${Number(quote.breakdown.platform_fee_online).toLocaleString()} so'm`;
    document.getElementById('q-owner-arrival').innerText = `${Number(quote.breakdown.payable_on_arrival_to_owner).toLocaleString()} so'm`;

  } catch (err) {
    console.error('Quote calculation error:', err);
  }
}

// Submit Booking
async function submitBooking() {
  if (!currentQuote) {
    showToast('Iltimos, avval sanalarni to\'g\'ri tanlang', 'error');
    return;
  }

  const guestName = document.getElementById('m-guest-name').value.trim();
  const guestPhone = document.getElementById('m-guest-phone').value.trim();
  const carPlate = document.getElementById('m-car-plate').value.trim();

  if (!guestName || !guestPhone) {
    showToast('Ism va telefon raqamingizni kiriting', 'error');
    return;
  }

  const payload = {
    quote_token: currentQuote.quote_token,
    guest_name: guestName,
    guest_phone: guestPhone,
    car_plate: carPlate
  };

  const idempotencyKey = `idemp_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
  const submitBtn = document.getElementById('btn-submit-booking');
  submitBtn.disabled = true;
  submitBtn.innerText = 'Kafolatli bron yaratilmoqda...';

  try {
    const res = await fetch('/api/v1/bookings/create', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Idempotency-Key': idempotencyKey
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    submitBtn.disabled = false;
    submitBtn.innerText = 'Kafolatlangan Bron Yaratish (15 daqiqaga qulflash) →';

    if (!res.ok) {
      showToast(data.detail || 'Bron qilishda xatolik (Double-booking himoyasi)', 'error');
      return;
    }

    currentBooking = data;
    closeModal('prop-modal');
    showToast('🎉 Bron muvaffaqiyatli yaratildi va 15 daqiqaga qulflandi!', 'success');

    // Open Payment Modal & start countdown
    document.getElementById('pay-ref').innerText = data.booking_reference;
    document.getElementById('pay-fee-val').innerText = `${Number(data.platform_fee_amount).toLocaleString()} so'm`;
    document.getElementById('pay-arrival-val').innerText = `${Number(data.pay_on_arrival_amount).toLocaleString()} so'm`;
    document.getElementById('pay-success-area').classList.add('hidden');

    startHoldCountdown(15 * 60);
    document.getElementById('payment-modal').classList.remove('hidden');
    refreshBadges();

  } catch (err) {
    submitBtn.disabled = false;
    submitBtn.innerText = 'Kafolatlangan Bron Yaratish →';
    showToast(`Xatolik: ${err.message}`, 'error');
  }
}

// Hold Countdown Timer
function startHoldCountdown(durationSeconds) {
  if (holdTimerInterval) clearInterval(holdTimerInterval);
  let timeLeft = durationSeconds;
  const timerEl = document.getElementById('hold-timer-clock');

  function update() {
    const mins = Math.floor(timeLeft / 60);
    const secs = timeLeft % 60;
    if (timerEl) timerEl.innerText = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    if (timeLeft <= 0) {
      clearInterval(holdTimerInterval);
      if (timerEl) timerEl.innerText = 'Muddati tugadi';
    }
    timeLeft--;
  }
  update();
  holdTimerInterval = setInterval(update, 1000);
}

// Payment Simulation
async function simulatePayment(provider) {
  if (!currentBooking) return;

  try {
    const res = await fetch('/api/v1/payments/simulate-success', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ booking_id: currentBooking.id, provider })
    });
    const result = await res.json();
    if (result.error === 0) {
      if (holdTimerInterval) clearInterval(holdTimerInterval);
      showToast(`${provider} to'lovi muvaffaqiyatli qabul qilindi! Bron CONFIRMED`, 'success');
      document.getElementById('pay-success-area').classList.remove('hidden');
      if (result.fiscal_receipt_url) {
        document.getElementById('btn-ofd-link').href = result.fiscal_receipt_url;
      }
      refreshBadges();
    } else {
      showToast(`To'lovda muammo: ${result.error_note}`, 'error');
    }
  } catch (err) {
    showToast('To\'lov xatosi: ' + err.message, 'error');
  }
}

// Offline Trip Voucher (AC-09)
async function openOfflineVoucher(ref) {
  const bookingRef = ref || currentBooking?.booking_reference;
  if (!bookingRef) return;

  try {
    const res = await fetch(`/api/v1/vouchers/${bookingRef}`);
    const v = await res.json();

    const voucherHtml = `
      <div style="border-bottom: 2px dashed #bbf7d0; padding-bottom: 12px; margin-bottom: 14px; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <b style="color:#166534; font-size:17px;">🌲 ${v.property_title}</b>
          <div style="color:#64748b; font-size:12px;">Bron raqami: <b>${v.booking_reference}</b></div>
        </div>
        <span style="background:#15803d; color:white; padding:4px 10px; border-radius:6px; font-size:12px; font-weight:800;">${v.booking_status}</span>
      </div>

      <div style="background:#f8fafc; padding:14px; border-radius:10px; margin-bottom:14px; font-size:13px; line-height:1.6; border-left:4px solid #16a34a;">
        <b>🚗 Yo'l sharoiti:</b> ${v.road_condition_advice}<br><br>
        <b>🗺️ Matnli yo'l ko'rsatmasi:</b> ${v.step_by_step_directions}
      </div>

      <div style="background:#ecfdf5; padding:12px 16px; border-radius:10px; margin-bottom:14px; display:flex; justify-content:space-between; align-items:center; font-size:14px;">
        <span style="color:#065f46; font-weight:600;">Joyida dacha egasiga to'lanadi (90%):</span>
        <b style="color:#15803d; font-size:18px;">${Number(v.payable_on_arrival_to_owner).toLocaleString()} so'm</b>
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:14px;">
        <a href="tel:${v.owner_phone}" class="btn-owner-action" style="background:#16a34a; color:white; text-align:center; padding:12px; text-decoration:none; display:block;">
          📞 Ega bilan aloqa<br><small style="font-size:11px;">${v.owner_phone}</small>
        </a>
        <a href="tel:${v.caretaker_phone}" class="btn-owner-action" style="background:#0f766e; color:white; text-align:center; padding:12px; text-decoration:none; display:block;">
          🔑 Bog'bonga qo'ng'iroq<br><small style="font-size:11px;">${v.caretaker_phone}</small>
        </a>
      </div>

      <div style="margin-bottom:14px;">
        <a href="${v.navigation.yandex_maps_url}" target="_blank" class="btn-owner-action" style="display:block; background:#0284c7; color:white; text-align:center; padding:12px; text-decoration:none; margin-bottom:8px;">
          🧭 Yandex Navigatorda Marshrut Olish
        </a>
        <a href="${v.navigation.geo_uri}" class="btn-owner-action" style="display:block; background:#475569; color:white; text-align:center; padding:8px; text-decoration:none; font-size:12px;">
          📍 GPS Nuqta: ${v.navigation.latitude}, ${v.navigation.longitude}
        </a>
      </div>

      <div style="background:#f1f5f9; padding:12px; text-align:center; border-radius:8px;">
        <span style="font-size:11px; color:#475569;">Oflayn QR kod tokeni:</span>
        <div style="font-weight:bold; font-family:monospace; color:#0f172a; font-size:12px; margin-top:4px;">${v.offline_qr_data}</div>
      </div>
    `;

    document.getElementById('voucher-content').innerHTML = voucherHtml;
    closeModal('payment-modal');
    document.getElementById('voucher-modal').classList.remove('hidden');

  } catch (err) {
    showToast('Vaucher yuklashda xatolik: ' + err.message, 'error');
  }
}

// My Trips (Mening Safarlarim) Logic
async function loadMyTrips() {
  const container = document.getElementById('my-trips-list');
  container.innerHTML = '<div style="text-align:center; padding:40px; color:#64748b;">Safarlar yuklanmoqda...</div>';

  const phone = currentUser?.phone_number || '+998935551122';
  try {
    const res = await fetch(`/api/v1/bookings/my-bookings?phone_or_id=${encodeURIComponent(phone)}`);
    const trips = await res.json();

    if (!trips || trips.length === 0) {
      container.innerHTML = `
        <div class="card-box" style="text-align:center; padding:50px 20px;">
          <div style="font-size:42px; margin-bottom:10px;">🏕️</div>
          <h3 style="color:#0f172a; font-size:18px; margin-bottom:6px;">Sizda hozircha faol safarlar yo'q</h3>
          <p style="color:#64748b; font-size:14px; margin-bottom:20px;">Zomin dachalari yoki choyxona tapchanlarini tanlang va bron qiling.</p>
          <button class="btn-primary-action" style="max-width:240px; margin:0 auto;" onclick="switchPortal('guest')">
            Dachalarni Ko'rish →
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = trips.map(t => {
      const isConfirmed = t.booking_status === 'CONFIRMED';
      const statusColor = isConfirmed ? '#15803d' : (t.booking_status === 'PENDING_OWNER' ? '#d97706' : '#64748b');

      return `
        <div class="card-box" style="margin-bottom:16px;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; flex-wrap:wrap; gap:8px;">
            <div>
              <h3 style="color:var(--primary); font-size:18px;">${t.property_title} — ${t.unit_name}</h3>
              <div style="font-size:13px; color:#64748b; margin-top:2px;">Bron raqami: <b>${t.booking_reference}</b></div>
            </div>
            <span style="font-size:12px; font-weight:800; background:#f1f5f9; color:${statusColor}; padding:6px 12px; border-radius:var(--radius-full);">
              ${t.booking_status}
            </span>
          </div>

          <div style="font-size:14px; color:#475569; line-height:1.7; margin-bottom:14px;">
            📅 Sanalar: <b>${t.checkin_time.slice(0, 16).replace('T', ' ')}</b> — <b>${t.checkout_time.slice(0, 16).replace('T', ' ')}</b> (${t.guest_count} kishi)<br>
            🛡️ Kafolat haqi (10%): <b>${Number(t.platform_fee_amount).toLocaleString()} so'm</b> (To'langan)<br>
            💵 Joyida dacha egasiga to'lanadi (90%): <b style="color:#15803d; font-size:16px;">${Number(t.pay_on_arrival_amount).toLocaleString()} so'm</b>
          </div>

          <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <button class="btn-primary-action" style="width:auto; padding:8px 18px; font-size:13px;" onclick="openOfflineVoucher('${t.booking_reference}')">
              📄 Oflayn Safar Vaucheri (AC-09)
            </button>
            <a href="tel:${t.owner_phone}" class="btn-card-select" style="text-decoration:none; padding:8px 16px;">
              📞 Dacha Egasi bilan Bog'lanish
            </a>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    container.innerHTML = `<div style="color:red; text-align:center;">Xatolik: ${err.message}</div>`;
  }
}

// OWNER PORTAL LOGIC
async function loadOwnerData() {
  if (!currentUser) return;
  loadOwnerUnits();
  loadOwnerBookings();
}

async function loadOwnerUnits() {
  const container = document.getElementById('owner-units-list');
  container.innerHTML = '<div style="color:#64748b; padding:16px;">Dachalar yuklanmoqda...</div>';

  try {
    const res = await fetch(`/api/v1/owner/properties?owner_id=${currentUser.id}`);
    const properties = await res.json();

    if (!properties || properties.length === 0) {
      container.innerHTML = '<p style="color:#64748b; padding:12px;">Sizda ro\'yxatdan o\'tgan dachalar topilmadi.</p>';
      return;
    }

    container.innerHTML = properties.map(p => {
      const unitsHtml = (p.rental_units || []).map(u => `
        <div style="display:flex; justify-content:space-between; align-items:center; background:#f8fafc; padding:12px 16px; border-radius:10px; margin-top:8px; border:1px solid var(--border);">
          <div>
            <b style="font-size:15px; color:#0f172a;">${u.name}</b> 
            <div style="color:#64748b; font-size:13px; margin-top:2px;">
              Hafta ichi: <b>${Number(u.base_price_weekday).toLocaleString()} so'm</b> | Dam olish: <b>${Number(u.base_price_weekend).toLocaleString()} so'm</b>
            </div>
          </div>
          <button class="btn-owner-action" style="background:#0284c7; color:white; padding:6px 14px; font-size:12px;" onclick="openPriceEditModal('${u.id}', '${u.name}', ${u.base_price_weekday}, ${u.base_price_weekend})">
            ✏️ Narxni o'zgartirish
          </button>
        </div>
      `).join('');

      return `
        <div style="border-bottom:1px solid var(--border); padding-bottom:16px; margin-bottom:16px;">
          <h4 style="color:var(--primary); font-size:16px;">${p.title} (${p.micro_district})</h4>
          <div style="font-size:13px; color:#64748b; margin-top:2px;">📍 ${p.address_text}</div>
          ${unitsHtml}
        </div>
      `;
    }).join('');

    // Populate Block Unit Dropdown
    const blockSelect = document.getElementById('block-unit-select');
    if (blockSelect) {
      let options = '';
      properties.forEach(p => {
        (p.rental_units || []).forEach(u => {
          options += `<option value="${u.id}">${p.title} — ${u.name}</option>`;
        });
      });
      blockSelect.innerHTML = options;
    }

  } catch (err) {
    container.innerHTML = `<div style="color:red; padding:12px;">Xatolik: ${err.message}</div>`;
  }
}

async function loadOwnerBookings() {
  const container = document.getElementById('owner-bookings-list');
  container.innerHTML = '<div style="color:#64748b; padding:16px;">Buyurtmalar tekshirilmoqda...</div>';

  try {
    const res = await fetch(`/api/v1/owner/bookings?owner_id=${currentUser.id}`);
    const bookings = await res.json();

    const pending = (bookings || []).filter(b => b.booking_status === 'PENDING_OWNER');
    const badgeEl = document.getElementById('badge-owner-pending');
    const statPendingEl = document.getElementById('stat-pending-count');
    if (badgeEl) {
      badgeEl.innerText = pending.length;
      badgeEl.classList.toggle('hidden', pending.length === 0);
    }
    if (statPendingEl) statPendingEl.innerText = `${pending.length} ta`;

    if (!bookings || bookings.length === 0) {
      container.innerHTML = `
        <div style="background:#f8fafc; padding:30px; border-radius:12px; text-align:center; border:1px dashed #cbd5e1;">
          <div style="font-size:36px; margin-bottom:8px;">🔔</div>
          <h4 style="color:#334155; margin-bottom:4px;">Hozircha yangi bron so'rovlari yo'q</h4>
          <p style="color:#64748b; font-size:13px; margin:0;">Sayyohlar sizning dachangizni bron qilganda bu yerda tezkor tasdiqlash xabarnomasi paydo bo'ladi.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = bookings.map(b => {
      const isPending = b.booking_status === 'PENDING_OWNER';
      const statusColor = b.booking_status === 'CONFIRMED' ? '#15803d' : (isPending ? '#d97706' : '#64748b');

      return `
        <div style="background:#f8fafc; padding:18px; border-radius:12px; border:1px solid var(--border); margin-bottom:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
            <b style="font-size:16px; color:#0f172a;">${b.property_title} — ${b.unit_name}</b>
            <span style="font-size:12px; font-weight:800; color:${statusColor}; background:white; padding:4px 10px; border-radius:6px; border:1px solid #cbd5e1;">
              ${b.booking_status}
            </span>
          </div>
          <div style="font-size:13px; color:#475569; margin-bottom:12px; line-height:1.7;">
            👤 Mehmon: <b>${b.guest_name}</b> (📞 <a href="tel:${b.guest_phone}" style="color:#0284c7; text-decoration:none;">${b.guest_phone}</a>)<br>
            🚗 Mashina raqami: <b style="background:#fef3c7; padding:2px 6px; border-radius:4px;">${b.car_plate || 'Kiritilmagan'}</b><br>
            📅 Sanalar: <b>${b.checkin_time.slice(0, 16).replace('T', ' ')}</b> — <b>${b.checkout_time.slice(0, 16).replace('T', ' ')}</b> (${b.guest_count} kishi)<br>
            💰 Joyida olasiz (90%): <b style="color:#15803d; font-size:16px;">${Number(b.pay_on_arrival_amount).toLocaleString()} so'm</b>
          </div>
          ${isPending ? `
            <div style="display:flex; gap:10px;">
              <button class="btn-owner-action" style="background:#16a34a; color:white; flex:1;" onclick="respondBooking('${b.id}', 'ACCEPT')">
                ✅ Qabul Qilish (Tasdiqlash)
              </button>
              <button class="btn-owner-action" style="background:#dc2626; color:white; flex:1;" onclick="respondBooking('${b.id}', 'REJECT')">
                ❌ Rad Etish
              </button>
            </div>
          ` : ''}
        </div>
      `;
    }).join('');

  } catch (err) {
    container.innerHTML = `<div style="color:red;">Xatolik: ${err.message}</div>`;
  }
}

async function respondBooking(bookingId, action) {
  try {
    const res = await fetch(`/api/v1/owner/bookings/${bookingId}/transition?owner_id=${currentUser.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
    const result = await res.json();
    if (!res.ok) {
      showToast(result.detail || 'Amalni bajarishda xatolik', 'error');
      return;
    }
    showToast(result.message, 'success');
    loadOwnerBookings();
    refreshBadges();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// IVR voice call manual trigger (AC-10)
async function runIvrCheckNow() {
  try {
    const res = await fetch('/api/v1/owner/ivr-check?delay_minutes=0', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast(`IVR Ovozli Eslatma: ${data.dispatched_count} ta dacha egasiga robot qo'ng'iroq qildi`, 'success');
    } else {
      showToast('IVR tekshirishda xatolik', 'error');
    }
  } catch (e) {
    showToast('IVR xatolik: ' + e.message, 'error');
  }
}

// Price Edit Modal
function openPriceEditModal(unitId, unitName, weekdayPrice, weekendPrice) {
  document.getElementById('price-edit-unit-id').value = unitId;
  document.getElementById('price-edit-unit-name').innerText = unitName;
  document.getElementById('price-edit-weekday').value = weekdayPrice;
  document.getElementById('price-edit-weekend').value = weekendPrice;
  document.getElementById('price-edit-modal').classList.remove('hidden');
}

async function submitPriceUpdate() {
  const unitId = document.getElementById('price-edit-unit-id').value;
  const weekday = parseFloat(document.getElementById('price-edit-weekday').value);
  const weekend = parseFloat(document.getElementById('price-edit-weekend').value);

  if (!unitId || weekday <= 0 || weekend <= 0) {
    showToast('Narxlarni to\'g\'ri kiriting', 'error');
    return;
  }

  try {
    const res = await fetch(`/api/v1/owner/units/${unitId}/prices`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        owner_id: currentUser.id,
        base_price_weekday: weekday,
        base_price_weekend: weekend
      })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.detail || 'Narxni yangilashda xatolik (BOLA)', 'error');
      return;
    }
    showToast('Narxlar muvaffaqiyatli yangilandi (AC-03 daxlsiz)', 'success');
    closeModal('price-edit-modal');
    loadOwnerUnits();
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// Calendar Block Modal
function openCalendarBlockModal() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split('T')[0];
  document.getElementById('block-start').value = `${tomorrowStr}T14:00`;
  document.getElementById('block-end').value = `${tomorrowStr}T22:00`;
  document.getElementById('calendar-block-modal').classList.remove('hidden');
}

async function submitCalendarBlock() {
  const unitId = document.getElementById('block-unit-select').value;
  const start = document.getElementById('block-start').value;
  const end = document.getElementById('block-end').value;
  const notes = document.getElementById('block-notes').value;

  if (!unitId || !start || !end) {
    showToast('Barcha maydonlarni to\'ldiring', 'error');
    return;
  }

  try {
    const res = await fetch('/api/v1/owner/calendar/block', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rental_unit_id: unitId,
        owner_id: currentUser.id,
        start_time: `${start}:00+05:00`,
        end_time: `${end}:00+05:00`,
        notes: notes
      })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.detail || 'Kalendarni yopishda xatolik', 'error');
      return;
    }
    showToast('Kalendar sanasi muvaffaqiyatli yopildi!', 'success');
    closeModal('calendar-block-modal');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// CARETAKER PORTAL LOGIC (AC-14)
async function loadCaretakerArrivals() {
  const container = document.getElementById('caretaker-arrivals-list');
  container.innerHTML = '<div style="color:#64748b; padding:20px;">Kutilayotgan mehmonlar yuklanmoqda...</div>';

  try {
    const cRes = await fetch(`/api/v1/owner/caretaker/arrivals?caretaker_id=${currentUser.id}`);
    const arrivals = await cRes.json();

    if (!arrivals || arrivals.length === 0) {
      container.innerHTML = `
        <div style="background:#f8fafc; padding:30px; border-radius:12px; text-align:center; border:1px dashed #cbd5e1;">
          <p style="color:#64748b; margin:0;">Hozircha biriktirilgan dachalar bo'yicha kutilayotgan mehmonlar yo'q.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = arrivals.map(a => {
      const isCheckedIn = a.booking_status === 'CHECKED_IN';

      return `
        <div style="background:#f8fafc; padding:18px; border-radius:12px; border:1px solid #bbf7d0; margin-bottom:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <b style="color:#166534; font-size:16px;">${a.property_title} — ${a.unit_name}</b>
            <span style="font-size:12px; font-weight:800; background:#dcfce7; color:#15803d; padding:4px 10px; border-radius:6px;">
              ${a.booking_status}
            </span>
          </div>
          <div style="font-size:14px; margin-bottom:14px; line-height:1.7;">
            👤 Mehmon: <b>${a.guest_name}</b><br>
            📞 Telefon: <a href="tel:${a.guest_phone}" style="color:#0284c7; font-weight:bold; text-decoration:none;">${a.guest_phone}</a><br>
            🚗 Mashina raqami: <b style="background:#fef3c7; color:#92400e; padding:3px 8px; border-radius:6px; font-size:15px;">${a.car_plate || 'Kiritilmagan'}</b><br>
            ⏰ Kelish vaqti: <b>${a.checkin_time.slice(0, 16).replace('T', ' ')}</b> (${a.guest_count} kishi)
            ${a.tandir_preorder_kg > 0 ? `<br>🍗 Zomin archa tandiri: <b>${a.tandir_preorder_kg} kg</b> (Oshxonaga xabar bering)` : ''}
          </div>
          ${!isCheckedIn ? `
            <button class="btn-primary-action" style="background:#16a34a; padding:12px;" onclick="confirmCheckIn('${a.id}')">
              🔑 Mehmon Keldi — Kalit Topshirildi (Check-in)
            </button>
          ` : `
            <div style="color:#15803d; font-weight:bold; font-size:13px; text-align:center; padding:10px; background:#f0fdf4; border-radius:8px; border:1px solid #bbf7d0;">
              ✅ Mehmon kutib olingan va kalit topshirilgan
            </div>
          `}
        </div>
      `;
    }).join('');

  } catch (err) {
    container.innerHTML = `<div style="color:red; padding:16px;">Xatolik: ${err.message}</div>`;
  }
}

async function confirmCheckIn(bookingId) {
  try {
    const res = await fetch(`/api/v1/bookings/${bookingId}/check-in?user_id=${currentUser.id}&user_role=CARETAKER`, {
      method: 'POST'
    });
    const result = await res.json();
    if (!res.ok) {
      showToast(result.detail || 'Xatolik yuz berdi', 'error');
      return;
    }
    showToast(result.message, 'success');
    loadCaretakerArrivals();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Badges Refresh
async function refreshBadges() {
  try {
    // Trips badge
    const phone = currentUser?.phone_number || '+998935551122';
    const tripsRes = await fetch(`/api/v1/bookings/my-bookings?phone_or_id=${encodeURIComponent(phone)}`);
    if (tripsRes.ok) {
      const trips = await tripsRes.json();
      const badgeTrips = document.getElementById('badge-my-trips');
      if (badgeTrips) {
        badgeTrips.innerText = trips.length;
        badgeTrips.classList.toggle('hidden', trips.length === 0);
      }
    }

    // Owner pending badge
    const ownerId = DEMO_PROFILES.owner1.phone;
    const bRes = await fetch(`/api/v1/owner/bookings?owner_id=${currentUser?.id || ''}`);
    if (bRes.ok) {
      const bList = await bRes.json();
      const pendingCount = (bList || []).filter(b => b.booking_status === 'PENDING_OWNER').length;
      const bOwnerBadge = document.getElementById('badge-owner-pending');
      if (bOwnerBadge) {
        bOwnerBadge.innerText = pendingCount;
        bOwnerBadge.classList.toggle('hidden', pendingCount === 0);
      }
    }
  } catch (e) {}
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('hidden');
}

// ================= ADMIN OPERATIONS (TZ 9) =================
let currentAdminTab = 'dash';

async function loadAdminStats() {
  try {
    const res = await fetch('/api/v1/admin/dashboard-stats');
    const s = await res.json();

    document.getElementById('adm-stat-gmv').innerText = `${Number(s.total_gmv).toLocaleString()} so'm`;
    document.getElementById('adm-stat-fee').innerText = `${Number(s.total_platform_fee).toLocaleString()} so'm`;
    document.getElementById('adm-stat-props').innerText = `${s.verified_properties} / ${s.total_properties} ta`;
    document.getElementById('adm-stat-bookings').innerText = `${s.total_bookings} ta (${s.confirmed_bookings} tasdiqlangan)`;
    const ivrEl = document.getElementById('adm-ivr-stat');
    if (ivrEl) ivrEl.innerText = `${s.ivr_calls_count} ta qo'ng'iroq yuborildi`;

    // Load active subtab data
    if (currentAdminTab === 'moderation') loadAdminProperties();
    else if (currentAdminTab === 'bookings') loadAdminBookings();
    else if (currentAdminTab === 'payments') loadAdminPayments();
    else if (currentAdminTab === 'users') loadAdminUsers();
    else if (currentAdminTab === 'audit') loadAdminAuditLogs();

  } catch (err) {
    showToast('Admin statistikasini olishda xatolik: ' + err.message, 'error');
  }
}

function switchAdminTab(tab) {
  currentAdminTab = tab;
  document.querySelectorAll('.admin-subnav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`adm-tab-${tab}`)?.classList.add('active');

  document.querySelectorAll('.admin-subview').forEach(v => v.classList.add('hidden'));
  document.getElementById(`adm-view-${tab}`)?.classList.remove('hidden');

  if (tab === 'moderation') loadAdminProperties();
  else if (tab === 'bookings') loadAdminBookings();
  else if (tab === 'payments') loadAdminPayments();
  else if (tab === 'users') loadAdminUsers();
  else if (tab === 'audit') loadAdminAuditLogs();
}

async function loadAdminProperties() {
  const container = document.getElementById('adm-props-table-wrap');
  container.innerHTML = '<div style="padding:20px; color:#64748b;">Obyektlar yuklanmoqda...</div>';

  const filterStatus = document.getElementById('adm-mod-filter')?.value || '';
  try {
    const url = filterStatus ? `/api/v1/admin/properties?status=${filterStatus}` : '/api/v1/admin/properties';
    const res = await fetch(url);
    const props = await res.json();

    if (!props || props.length === 0) {
      container.innerHTML = '<p style="padding:16px; color:#64748b;">Hech qanday dacha topilmadi.</p>';
      return;
    }

    container.innerHTML = `
      <table class="admin-table">
        <thead>
          <tr>
            <th>Dacha / Maskan</th>
            <th>Hudud</th>
            <th>Turi</th>
            <th>Birliklar</th>
            <th>Holati</th>
            <th>Nashr</th>
            <th>Amallar</th>
          </tr>
        </thead>
        <tbody>
          ${props.map(p => `
            <tr>
              <td>
                <b>${p.title}</b><br>
                <small style="color:#64748b;">${p.address_text}</small>
              </td>
              <td><span class="tag-badge">${p.micro_district}</span></td>
              <td>${p.property_type}</td>
              <td><b>${p.units_count} ta</b></td>
              <td>
                <span class="badge-status ${p.verification_status.toLowerCase()}">${p.verification_status}</span>
              </td>
              <td>${p.is_published ? '✅ Ha' : '❌ Yo\'q'}</td>
              <td>
                <div style="display:flex; gap:6px;">
                  ${p.verification_status !== 'VERIFIED' ? `
                    <button class="btn-action-sm" style="background:#16a34a; color:white;" onclick="adminVerifyProperty('${p.id}', 'VERIFIED')">
                      ✓ Tasdiqlash
                    </button>
                  ` : `
                    <button class="btn-action-sm" style="background:#ea580c; color:white;" onclick="adminVerifyProperty('${p.id}', 'REJECTED')">
                      Rad etish
                    </button>
                  `}
                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:red; padding:16px;">Xatolik: ${err.message}</div>`;
  }
}

async function adminVerifyProperty(propertyId, status) {
  try {
    const res = await fetch(`/api/v1/admin/properties/${propertyId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        admin_id: currentUser?.id || 'admin_user',
        status: status,
        notes: `Admin tomonidan ${status} deb belgilandi.`
      })
    });
    const result = await res.json();
    if (res.ok) {
      showToast(result.message, 'success');
      loadAdminProperties();
      loadAdminStats();
    } else {
      showToast(result.detail || 'Xatolik', 'error');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadAdminBookings() {
  const container = document.getElementById('adm-bookings-table-wrap');
  container.innerHTML = '<div style="padding:20px; color:#64748b;">Bronlar monitoringi yuklanmoqda...</div>';

  const filterStatus = document.getElementById('adm-book-filter')?.value || '';
  try {
    const url = filterStatus ? `/api/v1/admin/bookings?status=${filterStatus}` : '/api/v1/admin/bookings';
    const res = await fetch(url);
    const bookings = await res.json();

    if (!bookings || bookings.length === 0) {
      container.innerHTML = '<p style="padding:16px; color:#64748b;">Bronlar topilmadi.</p>';
      return;
    }

    container.innerHTML = `
      <table class="admin-table">
        <thead>
          <tr>
            <th>Bron Ref</th>
            <th>Obyekt & Birlik</th>
            <th>Mehmon & Telefon</th>
            <th>Sanalar</th>
            <th>Jami Summa</th>
            <th>Xizmat Haqi (10%)</th>
            <th>Status</th>
            <th>Amal</th>
          </tr>
        </thead>
        <tbody>
          ${bookings.map(b => `
            <tr>
              <td><b>${b.booking_reference}</b></td>
              <td>${b.property_title} — ${b.unit_name}</td>
              <td>
                ${b.guest_name}<br>
                <small style="color:#0284c7;">${b.guest_phone}</small>
              </td>
              <td><small>${b.checkin_time.slice(0, 10)} / ${b.checkout_time.slice(0, 10)}</small></td>
              <td><b>${Number(b.total_amount).toLocaleString()} so'm</b></td>
              <td><span style="color:#059669; font-weight:700;">${Number(b.platform_fee_amount).toLocaleString()} so'm</span></td>
              <td><span class="badge-status ${b.booking_status.toLowerCase()}">${b.booking_status}</span></td>
              <td>
                ${b.booking_status !== 'CANCELLED' ? `
                  <button class="btn-action-sm" style="background:#dc2626; color:white;" onclick="adminForceCancel('${b.id}', '${b.booking_reference}')">
                    🚫 Bekor Qilish
                  </button>
                ` : '<span style="color:#64748b; font-size:11px;">Bekor qilingan</span>'}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:red; padding:16px;">Xatolik: ${err.message}</div>`;
  }
}

async function adminForceCancel(bookingId, ref) {
  const reason = prompt(`${ref} raqamli bronni majburiy bekor qilish sababini kiriting:`, 'Sayyoh iltimosiga binoan');
  if (!reason) return;

  try {
    const res = await fetch(`/api/v1/admin/bookings/${bookingId}/force-cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        admin_id: currentUser?.id || 'admin_user',
        reason: reason
      })
    });
    const result = await res.json();
    if (res.ok) {
      showToast(result.message, 'success');
      loadAdminBookings();
      loadAdminStats();
    } else {
      showToast(result.detail || 'Bekor qilishda xatolik', 'error');
    }
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function loadAdminPayments() {
  const container = document.getElementById('adm-payments-table-wrap');
  container.innerHTML = '<div style="padding:20px; color:#64748b;">To\'lovlar tarixi yuklanmoqda...</div>';

  try {
    const res = await fetch('/api/v1/admin/payments');
    const payments = await res.json();

    if (!payments || payments.length === 0) {
      container.innerHTML = '<p style="padding:16px; color:#64748b;">Hozircha to\'lovlar qayd etilmagan.</p>';
      return;
    }

    container.innerHTML = `
      <table class="admin-table">
        <thead>
          <tr>
            <th>Provayder</th>
            <th>Bron Ref</th>
            <th>Mehmon</th>
            <th>Summa (UZS)</th>
            <th>Tiyinda</th>
            <th>Holati</th>
            <th>OFD Elektron Chek</th>
            <th>Vaqti</th>
          </tr>
        </thead>
        <tbody>
          ${payments.map(p => `
            <tr>
              <td>
                <b style="color:${p.provider === 'CLICK' ? '#0284c7' : '#059669'};">${p.provider}</b>
              </td>
              <td><b>${p.booking_reference}</b></td>
              <td>${p.guest_name} (${p.guest_phone})</td>
              <td><b>${Number(p.amount_uzs).toLocaleString()} so'm</b></td>
              <td><small>${p.amount_in_tiyin}</small></td>
              <td><span class="badge-status ${p.status.toLowerCase()}">${p.status}</span></td>
              <td>
                ${p.fiscal_receipt_url ? `
                  <a href="${p.fiscal_receipt_url}" target="_blank" class="btn-action-sm" style="background:#059669; color:white; text-decoration:none; display:inline-block;">
                    🧾 Soliq Chek
                  </a>
                ` : '<span style="color:#94a3b8;">Yo\'q</span>'}
              </td>
              <td><small>${p.created_at.slice(0, 16).replace('T', ' ')}</small></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:red; padding:16px;">Xatolik: ${err.message}</div>`;
  }
}

async function loadAdminUsers() {
  const container = document.getElementById('adm-users-table-wrap');
  container.innerHTML = '<div style="padding:20px; color:#64748b;">Foydalanuvchilar ro\'yxati yuklanmoqda...</div>';

  try {
    const res = await fetch('/api/v1/admin/users');
    const users = await res.json();

    container.innerHTML = `
      <table class="admin-table">
        <thead>
          <tr>
            <th>F.I.SH</th>
            <th>Telefon Raqam</th>
            <th>Roli</th>
            <th>Telegram ID</th>
            <th>Holati</th>
            <th>Amallar</th>
          </tr>
        </thead>
        <tbody>
          ${users.map(u => `
            <tr>
              <td><b>${u.full_name || 'Noma\'lum'}</b></td>
              <td><code>${u.phone_number}</code></td>
              <td><span class="tag-badge">${u.role}</span></td>
              <td>${u.telegram_id || '—'}</td>
              <td>${u.is_active ? '✅ Faol' : '🚫 Bloklangan'}</td>
              <td>
                <button class="btn-action-sm" style="background:${u.is_active ? '#dc2626' : '#16a34a'}; color:white;" onclick="adminToggleUser('${u.id}', ${u.is_active})">
                  ${u.is_active ? 'Bloklash' : 'Faollashtirish'}
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:red; padding:16px;">Xatolik: ${err.message}</div>`;
  }
}

async function adminToggleUser(userId, currentActive) {
  const newActive = !currentActive;
  try {
    const res = await fetch(`/api/v1/admin/users/${userId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        admin_id: currentUser?.id || 'admin_user',
        is_active: newActive
      })
    });
    if (res.ok) {
      showToast('Foydalanuvchi holati yangilandi', 'success');
      loadAdminUsers();
    }
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function loadAdminAuditLogs() {
  const container = document.getElementById('adm-audit-table-wrap');
  container.innerHTML = '<div style="padding:20px; color:#64748b;">Audit jurnali yuklanmoqda...</div>';

  try {
    const res = await fetch('/api/v1/admin/audit-logs');
    const logs = await res.json();

    if (!logs || logs.length === 0) {
      container.innerHTML = '<p style="padding:16px; color:#64748b;">Audit yozuvlari hali mavjud emas.</p>';
      return;
    }

    container.innerHTML = `
      <table class="admin-table">
        <thead>
          <tr>
            <th>Amal (Action)</th>
            <th>Obyekt Turi</th>
            <th>ID</th>
            <th>Tafsilotlar</th>
            <th>Vaqt</th>
          </tr>
        </thead>
        <tbody>
          ${logs.map(l => `
            <tr>
              <td><b>${l.action}</b></td>
              <td><span class="tag-badge">${l.target_type}</span></td>
              <td><code>${(l.target_id || '').slice(0, 8)}...</code></td>
              <td>${l.details || '—'}</td>
              <td><small>${l.created_at.slice(0, 16).replace('T', ' ')}</small></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:red; padding:16px;">Xatolik: ${err.message}</div>`;
  }
}
