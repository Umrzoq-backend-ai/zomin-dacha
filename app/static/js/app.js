// ZominStay Frontend & Telegram Mini App Logic
let currentPortal = 'guest';
let propertiesCache = [];
let selectedProperty = null;
let currentQuote = null;
let currentBooking = null;
let currentTandirKg = 0;
let currentDayUseSlot = null; // 'FULL_DAY', 'LUNCH', 'DINNER'

// Filter state
let activeDistrict = 'ALL';
let filterRoad = null;
let filterGenerator = null;
let filterType = null;

// User Profile state
const DEMO_PROFILES = {
  guest: { phone: '+998935551122', name: 'Jasur Mamadaliyev (Sayyoh)', role: 'GUEST' },
  owner1: { phone: '+998901112233', name: 'Alisher Zokirov (Duoba Dacha Egasi)', role: 'OWNER' },
  owner2: { phone: '+998904445566', name: 'Muzaffar Raimov (Suffa & O\'riklisoy Egasi)', role: 'OWNER' },
  caretaker: { phone: '+998917778899', name: 'Rustam Tog\'a (Duoba Bog\'boni)', role: 'CARETAKER' }
};

let currentUser = null;

// Toast helper
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
    toast.style.transform = 'translateX(100%)';
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
      tg.setHeaderColor('#065f46');
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
          console.log('Telegram WebApp user authenticated:', currentUser);
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
  loadProperties();
});

async function switchUserProfile(profileKey, reloadPortal = true) {
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

      if (reloadPortal) {
        showToast(`Profil almashtirildi: ${currentUser.full_name}`, 'info');
        if (currentPortal === 'owner') loadOwnerData();
        else if (currentPortal === 'caretaker') loadCaretakerArrivals();
      }
    }
  } catch (e) {
    console.error('Failed to switch user profile:', e);
  }
}

function initDefaultDates() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split('T')[0];

  const nextDay = new Date();
  nextDay.setDate(nextDay.getDate() + 3);
  const nextDayStr = nextDay.toISOString().split('T')[0];

  const inField = document.getElementById('search-checkin');
  const outField = document.getElementById('search-checkout');
  if (inField && outField) {
    inField.value = tomorrowStr;
    outField.value = nextDayStr;
  }
}

// Switching portals
function switchPortal(portal) {
  currentPortal = portal;
  document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById(`btn-portal-${portal}`);
  if (btn) btn.classList.add('active');

  document.getElementById('portal-guest').classList.add('hidden');
  document.getElementById('portal-owner').classList.add('hidden');
  document.getElementById('portal-caretaker').classList.add('hidden');

  if (portal === 'guest') {
    document.getElementById('portal-guest').classList.remove('hidden');
    loadProperties();
  } else if (portal === 'owner') {
    document.getElementById('portal-owner').classList.remove('hidden');
    // Auto switch to Owner 1 if currently guest
    if (currentUser && currentUser.role !== 'OWNER') {
      switchUserProfile('owner1', true);
    } else {
      loadOwnerData();
    }
  } else if (portal === 'caretaker') {
    document.getElementById('portal-caretaker').classList.remove('hidden');
    if (currentUser && currentUser.role !== 'CARETAKER') {
      switchUserProfile('caretaker', true);
    } else {
      loadCaretakerArrivals();
    }
  }
}

// Load properties from backend
async function loadProperties() {
  const grid = document.getElementById('properties-grid');
  grid.innerHTML = '<div style="text-align:center; padding:40px; color:#64748b;">Dachalar yuklanmoqda...</div>';

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
    const properties = await res.json();
    propertiesCache = properties;

    if (!properties || properties.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding:40px; background:white; border-radius:16px; border:1px solid var(--border);">
          <h3 style="color:#64748b; margin-bottom:8px;">Hech qanday dacha yoki tapchan topilmadi</h3>
          <p style="color:#94a3b8; font-size:14px;">Filtr parametrlarini o'zgartirib qayta qidirib ko'ring.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = properties.map(p => {
      const photo = p.photos && p.photos.length > 0 ? p.photos[0] : 'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=800&q=80';
      const isSedan = p.road_condition === 'ASPHALT_SEDAN';
      const roadBadge = isSedan ? 
        '<span class="tag-badge road-sedan">🚗 Asfalt (Spark/Cobalt)</span>' : 
        '<span class="tag-badge road-4wd">🚙 Tog\' yo\'li / 4WD</span>';
      const genBadge = p.has_generator ? '<span class="tag-badge generator">⚡ Generator bor</span>' : '';
      const typeText = p.property_type === 'VILLA' ? 'Villa / Dacha' : 
                       (p.property_type === 'COTTAGE' ? 'Tog\' Kotteji' : 
                       (p.property_type === 'CHOYXONA_TAPCHAN' ? 'Choyxona & Tapchan' : 'Mehmon Uyi'));

      return `
        <div class="prop-card" onclick="openPropertyModal('${p.id}')">
          <div class="prop-img-box">
            <img class="prop-img" src="${photo}" alt="${p.title}" loading="lazy">
            <span class="prop-badge-top">${p.micro_district}</span>
            <span class="prop-type-badge">${typeText}</span>
          </div>
          <div class="prop-body">
            <h4 class="prop-title">${p.title}</h4>
            <div class="prop-address">📍 ${p.address_text}</div>
            <div class="prop-tags">
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
              <button class="btn-book-card">Tanlash &gt;</button>
            </div>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    grid.innerHTML = `<div style="color:red; text-align:center; padding:20px;">Xatolik yuz berdi: ${err.message}</div>`;
  }
}

function selectDistrictPill(el, district) {
  document.querySelectorAll('.district-pill').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  activeDistrict = district;
  const sel = document.getElementById('search-district');
  if (sel) sel.value = district;
  loadProperties();
}

function toggleFilterChip(el, type, value) {
  const isActive = el.classList.contains('active');

  // Handle mutual exclusivity for property type
  if (type === 'type') {
    document.querySelectorAll('.toggle-chip[id^="toggle-tapchan"], .toggle-chip[id^="toggle-villa"]').forEach(c => c.classList.remove('active'));
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

// Property Detail & Quote Modal
function openPropertyModal(propId) {
  const p = propertiesCache.find(item => item.id === propId);
  if (!p) return;
  selectedProperty = p;
  currentTandirKg = 0;
  currentDayUseSlot = null;
  document.getElementById('tandir-kg-val').innerText = '0 kg';

  document.getElementById('m-prop-title').innerText = p.title;
  document.getElementById('m-prop-desc').innerText = p.description;
  const imgUrl = p.photos && p.photos.length > 0 ? p.photos[0] : '';
  document.getElementById('m-prop-img').src = imgUrl;

  const badgesArea = document.getElementById('m-prop-badges');
  badgesArea.innerHTML = `
    <span class="tag-badge road-sedan">📍 ${p.micro_district}</span>
    <span class="tag-badge">${p.road_condition}</span>
    ${p.has_generator ? '<span class="tag-badge generator">⚡ Generator bor</span>' : ''}
    <span class="tag-badge">📶 ${p.mobile_coverage}</span>
  `;

  // Populate Units
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

  document.getElementById('prop-modal').classList.remove('hidden');
  onUnitSelectionChanged();
}

function onUnitSelectionChanged() {
  const unitId = document.getElementById('m-unit-select').value;
  const unit = selectedProperty?.rental_units?.find(u => u.id === unitId);
  const slotContainer = document.getElementById('m-slot-container');

  if (unit && unit.unit_category === 'DAY_USE_TAPCHAN') {
    slotContainer.classList.remove('hidden');
    // Default to FULL_DAY
    selectDaySlot('FULL_DAY', '10:00', '22:00');
  } else {
    slotContainer.classList.add('hidden');
    currentDayUseSlot = null;
    calculateLiveQuote();
  }
}

function selectDaySlot(slotName, startTime, endTime) {
  currentDayUseSlot = slotName;
  document.querySelectorAll('.slot-pill').forEach(b => b.classList.remove('active'));
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
  const unitId = document.getElementById('m-unit-select').value;
  const checkin = document.getElementById('m-checkin').value;
  const checkout = document.getElementById('m-checkout').value;

  if (!unitId || !checkin || !checkout) return;

  const payload = {
    rental_unit_id: unitId,
    checkin_time: checkin.includes('T') ? `${checkin}:00+05:00` : `${checkin}T14:00:00+05:00`,
    checkout_time: checkout.includes('T') ? `${checkout}:00+05:00` : `${checkout}T12:00:00+05:00`,
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
    console.error('Quote error:', err);
  }
}

async function submitBooking() {
  if (!currentQuote) {
    showToast('Iltimos, avval sanalarni to\'g\'ri tanlang', 'error');
    return;
  }

  const guestName = document.getElementById('m-guest-name').value;
  const guestPhone = document.getElementById('m-guest-phone').value;
  const carPlate = document.getElementById('m-car-plate').value;

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
    if (!res.ok) {
      showToast(data.detail || 'Bron yaratishda xatolik yuz berdi (Double booking himoyasi)', 'error');
      return;
    }

    currentBooking = data;
    closeModal('prop-modal');
    showToast('Bron yaratildi va 15 daqiqaga qulflandi!', 'success');

    // Open Payment Modal
    document.getElementById('pay-ref').innerText = data.booking_reference;
    document.getElementById('pay-fee-val').innerText = `${Number(data.platform_fee_amount).toLocaleString()} so'm`;
    document.getElementById('pay-arrival-val').innerText = `${Number(data.pay_on_arrival_amount).toLocaleString()} so'm`;
    document.getElementById('pay-success-area').classList.add('hidden');

    document.getElementById('payment-modal').classList.remove('hidden');

  } catch (err) {
    showToast(`Xatolik: ${err.message}`, 'error');
  }
}

// Payment simulation (Click & Payme)
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
      showToast(`${provider} to'lovi muvaffaqiyatli o'tdi! Bron CONFIRMED`, 'success');
      document.getElementById('pay-success-area').classList.remove('hidden');
      if (result.fiscal_receipt_url) {
        document.getElementById('btn-ofd-link').href = result.fiscal_receipt_url;
      }
    } else {
      showToast(`To'lovda muammo: ${result.error_note}`, 'error');
    }
  } catch (err) {
    showToast('To\'lovda xatolik: ' + err.message, 'error');
  }
}

// Offline Trip Voucher (AC-09)
async function openOfflineVoucher() {
  if (!currentBooking) return;
  try {
    const res = await fetch(`/api/v1/vouchers/${currentBooking.booking_reference}`);
    const v = await res.json();

    const voucherHtml = `
      <div style="border-bottom: 2px dashed #bbf7d0; padding-bottom: 12px; margin-bottom: 12px; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <b style="color:#166534; font-size:16px;">🌲 ${v.property_title}</b>
          <div style="color:#64748b; font-size:12px;">Bron raqami: <b>${v.booking_reference}</b></div>
        </div>
        <span style="background:#15803d; color:white; padding:4px 8px; border-radius:6px; font-size:12px; font-weight:bold;">${v.booking_status}</span>
      </div>

      <div style="background:#f8fafc; padding:12px; border-radius:8px; margin-bottom:12px; font-size:13px; line-height:1.5; border-left:4px solid #16a34a;">
        <b>🚗 Yo'l sharoiti:</b> ${v.road_condition_advice}<br><br>
        <b>🗺️ Matnli yo'l ko'rsatmasi:</b> ${v.step_by_step_directions}
      </div>

      <div style="background:#ecfdf5; padding:10px 14px; border-radius:8px; margin-bottom:12px; display:flex; justify-content:space-between; font-size:14px;">
        <span style="color:#065f46;">Joyida to'lanadi (90%):</span>
        <b style="color:#15803d; font-size:16px;">${Number(v.payable_on_arrival_to_owner).toLocaleString()} so'm</b>
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:14px;">
        <a href="tel:${v.owner_phone}" class="role-btn" style="background:#16a34a; color:white; text-align:center; padding:10px; text-decoration:none;">
          📞 Ega bilan aloqa<br><small>${v.owner_phone}</small>
        </a>
        <a href="tel:${v.caretaker_phone}" class="role-btn" style="background:#0f766e; color:white; text-align:center; padding:10px; text-decoration:none;">
          🔑 Bog'bonga qo'ng'iroq<br><small>${v.caretaker_phone}</small>
        </a>
      </div>

      <div style="margin-bottom:14px;">
        <a href="${v.navigation.yandex_maps_url}" class="role-btn" style="display:block; background:#0284c7; color:white; text-align:center; padding:10px; text-decoration:none; margin-bottom:8px;">
          🧭 Yandex Navigatorda Marshrut
        </a>
        <a href="${v.navigation.geo_uri}" class="role-btn" style="display:block; background:#475569; color:white; text-align:center; padding:8px; text-decoration:none;">
          📍 GPS Koordinata (${v.navigation.latitude}, ${v.navigation.longitude})
        </a>
      </div>

      <div style="background:#f1f5f9; padding:12px; text-align:center; border-radius:8px;">
        <span style="font-size:11px; color:#475569;">Oflayn QR kod tokeni:</span>
        <div style="font-weight:bold; font-family:monospace; color:#0f172a; font-size:13px; margin-top:4px;">${v.offline_qr_data}</div>
      </div>
    `;

    document.getElementById('voucher-content').innerHTML = voucherHtml;
    closeModal('payment-modal');
    document.getElementById('voucher-modal').classList.remove('hidden');

  } catch (err) {
    showToast('Vaucher yuklashda xatolik: ' + err.message, 'error');
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
  container.innerHTML = '<div style="color:#64748b;">Dachalar yuklanmoqda...</div>';

  try {
    const res = await fetch(`/api/v1/owner/properties?owner_id=${currentUser.id}`);
    const properties = await res.json();

    if (!properties || properties.length === 0) {
      container.innerHTML = '<p style="color:#64748b;">Sizda ro\'yxatdan o\'tgan dachalar topilmadi.</p>';
      return;
    }

    container.innerHTML = properties.map(p => {
      const unitsHtml = (p.rental_units || []).map(u => `
        <div style="display:flex; justify-content:space-between; align-items:center; background:#f8fafc; padding:10px 14px; border-radius:8px; margin-top:8px;">
          <div>
            <b>${u.name}</b> <small style="color:#64748b;">(Hafta ichi: ${Number(u.base_price_weekday).toLocaleString()} so'm | Dam olish: ${Number(u.base_price_weekend).toLocaleString()} so'm)</small>
          </div>
          <button class="role-btn" style="background:#0284c7; color:white; padding:4px 10px; font-size:12px;" onclick="openPriceEditModal('${u.id}', '${u.name}', ${u.base_price_weekday}, ${u.base_price_weekend})">
            ✏️ Narxni o'zgartirish
          </button>
        </div>
      `).join('');

      return `
        <div style="border-bottom:1px solid var(--border); padding-bottom:12px; margin-bottom:12px;">
          <h4 style="color:var(--primary);">${p.title} (${p.micro_district})</h4>
          <div style="font-size:13px; color:#64748b; margin-top:4px;">📍 ${p.address_text}</div>
          ${unitsHtml}
        </div>
      `;
    }).join('');

    // Update block modal unit dropdown
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
    container.innerHTML = `<div style="color:red;">Xatolik: ${err.message}</div>`;
  }
}

async function loadOwnerBookings() {
  const container = document.getElementById('owner-bookings-list');
  container.innerHTML = '<div style="color:#64748b;">Buyurtmalar yuklanmoqda...</div>';

  try {
    const res = await fetch(`/api/v1/owner/bookings?owner_id=${currentUser.id}`);
    const bookings = await res.json();

    if (!bookings || bookings.length === 0) {
      container.innerHTML = '<div style="background:white; padding:20px; border-radius:12px; text-align:center; color:#64748b;">Hozircha yangi bronlar yo\'q.</div>';
      return;
    }

    container.innerHTML = bookings.map(b => {
      const isPending = b.booking_status === 'PENDING_OWNER';
      const statusColor = b.booking_status === 'CONFIRMED' ? '#15803d' : (isPending ? '#d97706' : '#64748b');

      return `
        <div style="background:white; padding:16px; border-radius:12px; border:1px solid var(--border); margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <b>${b.property_title} — ${b.unit_name}</b>
            <span style="font-size:12px; font-weight:bold; color:${statusColor}; background:#f1f5f9; padding:4px 8px; border-radius:6px;">${b.booking_status}</span>
          </div>
          <div style="font-size:13px; color:#475569; margin-bottom:10px; line-height:1.6;">
            👤 Mehmon: <b>${b.guest_name}</b> (${b.guest_phone}) | 🚗 Mashina: <b>${b.car_plate || 'Yo\'q'}</b><br>
            📅 Sanalar: <b>${b.checkin_time.slice(0, 16).replace('T', ' ')}</b> — <b>${b.checkout_time.slice(0, 16).replace('T', ' ')}</b> (${b.guest_count} kishi)<br>
            💰 Joyida olasiz: <b style="color:#15803d; font-size:15px;">${Number(b.pay_on_arrival_amount).toLocaleString()} so'm</b>
          </div>
          ${isPending ? `
            <div style="display:flex; gap:8px;">
              <button class="role-btn" style="background:#16a34a; color:white;" onclick="respondBooking('${b.id}', 'ACCEPT')">
                ✅ Qabul qilish (Tasdiqlash)
              </button>
              <button class="role-btn" style="background:#dc2626; color:white;" onclick="respondBooking('${b.id}', 'REJECT')">
                ❌ Rad etish
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
      showToast(`IVR tekshiruv yakunlandi: ${data.dispatched_count} ta qo'ng'iroq yuborildi`, 'success');
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
    showToast('Narxlar muvaffaqiyatli saqlandi (AC-03 daxlsiz)', 'success');
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
  container.innerHTML = '<div style="color:#64748b;">Kutilayotgan mehmonlar yuklanmoqda...</div>';

  try {
    const cRes = await fetch(`/api/v1/owner/caretaker/arrivals?caretaker_id=${currentUser.id}`);
    const arrivals = await cRes.json();

    if (!arrivals || arrivals.length === 0) {
      container.innerHTML = `
        <div style="background:white; padding:24px; border-radius:12px; text-align:center; border:1px solid var(--border);">
          <p style="color:#64748b; margin:0;">Hozircha biriktirilgan dachalar bo'yicha kutilayotgan mehmonlar yo'q.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = arrivals.map(a => {
      const isCheckedIn = a.booking_status === 'CHECKED_IN';

      return `
        <div style="background:white; padding:16px; border-radius:12px; border:1px solid #bbf7d0; margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <b style="color:#166534;">${a.property_title} — ${a.unit_name}</b>
            <span style="font-size:12px; font-weight:bold; background:#dcfce7; color:#15803d; padding:4px 8px; border-radius:6px;">${a.booking_status}</span>
          </div>
          <div style="font-size:14px; margin-bottom:12px; line-height:1.6;">
            👤 Mehmon: <b>${a.guest_name}</b><br>
            📞 Telefon: <a href="tel:${a.guest_phone}" style="color:#0284c7; font-weight:bold;">${a.guest_phone}</a><br>
            🚗 Mashina raqami: <b style="background:#fef3c7; padding:2px 6px; border-radius:4px;">${a.car_plate || 'Kiritilmagan'}</b><br>
            ⏰ Kelish vaqti: <b>${a.checkin_time.slice(0, 16).replace('T', ' ')}</b> (${a.guest_count} kishi)
            ${a.tandir_preorder_kg > 0 ? `<br>🍗 Zomin archa tandiri: <b>${a.tandir_preorder_kg} kg</b> buyurtma qilingan (oshxonaga xabar bering)` : ''}
          </div>
          ${!isCheckedIn ? `
            <button class="btn-search" style="background:#16a34a; margin-top:0; padding:10px 16px; width:100%;" onclick="confirmCheckIn('${a.id}')">
              🔑 Mehmon Keldi / Kalit Topshirildi (Check-in)
            </button>
          ` : `
            <div style="color:#15803d; font-weight:bold; font-size:13px; text-align:center; padding:8px; background:#f0fdf4; border-radius:8px;">
              ✅ Mehmon kutib olingan va kalit topshirilgan
            </div>
          `}
        </div>
      `;
    }).join('');

  } catch (err) {
    container.innerHTML = `<div style="color:red;">Xatolik: ${err.message}</div>`;
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

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('hidden');
}
