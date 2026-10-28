// ===================================================================
// Zomin — Master Application Logic & Real-Time Ecotourism State
// Matches Image 3 Luxury Alpine UI, Interactive Leaflet Map & Modals
// ===================================================================

let propertiesCache = [];
let selectedProperty = null;
let currentQuote = null;
let currentBooking = null;
let currentTandirKg = 0;
let currentDayUseSlot = null; // 'FULL_DAY', 'LUNCH', 'DINNER'
let currentBookingMode = 'OVERNIGHT'; // 'OVERNIGHT' or 'DAY_USE'
let holdTimerInterval = null;
let leafletMap = null;
let mapMarkers = [];

// Filter & Sort State
let activeMicroDistrict = 'ALL';
let filterRoadOnly = false;
let filterGeneratorOnly = false;
let wishlistItems = new Set(['suffa-panoramik-tog-kotteji']);

// Demo Profiles Matrix (AC-08, AC-14)
const DEMO_PROFILES = {
  guest: { phone: '+998935551122', name: 'Jasur Mamadaliyev', role: 'GUEST', label: '🏕️ Jasur M. (Sayyoh)' },
  owner1: { phone: '+998901112233', name: 'Alisher Zokirov', role: 'OWNER', label: '🏡 Alisher Z. (Duoba Dacha Egasi)' },
  owner2: { phone: '+998904445566', name: 'Muzaffar Raimov', role: 'OWNER', label: '🏡 Muzaffar R. (Suffa & O\'riklisoy Egasi)' },
  caretaker: { phone: '+998917778899', name: 'Rustam Tog\'a', role: 'CARETAKER', label: '🔑 Rustam Tog\'a (Duoba Bog\'boni)' },
  admin: { phone: '+998900000001', name: 'Sanjar Karimov', role: 'ADMIN', label: '🛡️ Sanjar K. (Platforma Admini)' }
};

let currentUser = null;

// Attraction Details Database
const ATTRACTIONS = {
  bridge: {
    title: "Zomin osma ko‘prigi (305m)",
    cat: "🌉 Mashhur joy",
    img: "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1200&q=80",
    desc: "Zomin milliy bog‘i kanyoni ustidan o‘tuvchi 305 metr uzunlikdagi shaffof osma ko‘prik. Dengiz sathidan 2000 metrdan balandda joylashgan bo‘lib, chuqur daraning ustidan unutilmas panoramik manzara taqdim etadi.",
    meta: "📍 Joylashuv: Suffa yo'li | ⏰ Ish vaqti: 08:00 - 19:00 | 🎫 Kirish: 50,000 so'm | 🚗 Asfalt yo'l va parkovka mavjud"
  },
  cablecar: {
    title: "Kabel yo‘li — Bartholet Shveysariya Dor Yo'li",
    cat: "🚠 Faoliyat",
    img: "https://images.unsplash.com/photo-1516431883659-655d41c09bf9?auto=format&fit=crop&w=1200&q=80",
    desc: "Shveysariyaning dunyoga mashhur Bartholet kompaniyasi tomonidan qurilgan 2100 metrli tezyurar osma dor yo'li. Suffa platosiga ko'tarilishda qorli cho'qqilar, archazor vodiylar va burgutlar parvozini balandlikdan tomosha qiling.",
    meta: "📍 Joylashuv: Suffa platosi (2400m) | ⏰ Ish vaqti: 09:00 - 18:00 | 🎫 Chipta: 40,000 so'm | ❄️ Yil bo'yi faoliyat yuritadi"
  },
  hiking: {
    title: "Zomin milliy tabiat bog'i sayr yo'llari",
    cat: "🥾 Marshrutlar",
    img: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
    desc: "Zominning eng go'zal tabiiy yodgorliklari sari ekologik piyoda sayohat yo'llari. 1000 yillik 'Boboong'oq' yong'oq daraxti, Pishag'or g'ori, Sharshara va toza buloqlarga olib boruvchi xavfsiz so'qmoqlar.",
    meta: "📍 Marshrut: Duoba - Pishag'or - Suffa | ⏱️ Davomiyligi: 2 - 4 soat | 🎒 Tavsiya: Qulay sport poyabzali va iliq kiyim"
  }
};

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

// Format Currency UZS
function formatSum(num) {
  if (num === null || num === undefined) return '0';
  return Math.round(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

// Initialize on DOM load
window.addEventListener('DOMContentLoaded', async () => {
  // Telegram Mini App SDK integration
  if (window.Telegram && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor('#0d382c');
      tg.setBackgroundColor('#fbfaf6');
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
    await selectUserProfile('guest', false);
  }

  initDefaultDates();
  await loadProperties();
  initLeafletMap();

  // Check if admin portal requested via URL (/admin or #admin)
  if (window.location.pathname === '/admin' || window.location.hash === '#admin') {
    showAdminPortal();
  }
});

// Set default check-in / check-out dates
function initDefaultDates() {
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dayAfter = new Date(today);
  dayAfter.setDate(dayAfter.getDate() + 3);

  const checkinInput = document.getElementById('search-checkin-date');
  const checkoutInput = document.getElementById('search-checkout-date');
  const modalStart = document.getElementById('modal-start-date');
  const modalEnd = document.getElementById('modal-end-date');

  const fmt = (d) => d.toISOString().split('T')[0];

  if (checkinInput) checkinInput.value = fmt(tomorrow);
  if (checkoutInput) checkoutInput.value = fmt(dayAfter);
  if (modalStart) modalStart.value = fmt(tomorrow);
  if (modalEnd) modalEnd.value = fmt(dayAfter);
}

// User Profile Selection
async function selectUserProfile(profileKey, reloadUI = true) {
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
      updateHeaderUserInfo();
      closeProfileSwitcherModal();
      showToast(`${currentUser.full_name} sifatida tizimga kirdingiz (${currentUser.role})`, 'success');

      if (reloadUI) {
        if (currentUser.role === 'ADMIN') {
          showAdminPortal();
        } else if (currentUser.role === 'OWNER') {
          openOwnerPortalModal();
        } else if (currentUser.role === 'CARETAKER') {
          openCaretakerModal();
        }
      }
    }
  } catch (err) {
    console.error('Login error:', err);
  }
}

function updateHeaderUserInfo() {
  if (!currentUser) return;
  const labelEl = document.getElementById('user-btn-label');
  const avatarEl = document.getElementById('user-btn-avatar');
  const menuName = document.getElementById('menu-user-name');
  const menuRole = document.getElementById('menu-user-role');
  const adminLink = document.getElementById('admin-menu-link');

  if (labelEl) labelEl.innerText = currentUser.full_name.split(' ')[0];
  if (avatarEl) {
    avatarEl.innerText = currentUser.role === 'ADMIN' ? '🛡️' : (currentUser.role === 'OWNER' ? '🏡' : (currentUser.role === 'CARETAKER' ? '🔑' : '👤'));
  }
  if (menuName) menuName.innerText = currentUser.full_name;
  if (menuRole) menuRole.innerText = currentUser.role;

  // Show or hide admin link based on role
  if (adminLink) {
    adminLink.style.display = (currentUser.role === 'ADMIN') ? 'flex' : 'none';
  }
}

// Navigation & View Switching
function showTouristHome() {
  document.getElementById('portal-tourist').classList.remove('hidden');
  document.getElementById('portal-admin').classList.add('hidden');
  document.getElementById('site-header').classList.remove('hidden');
  window.history.pushState(null, '', '/');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showAdminPortal() {
  document.getElementById('portal-tourist').classList.add('hidden');
  document.getElementById('portal-admin').classList.remove('hidden');
  document.getElementById('site-header').classList.add('hidden');
  window.history.pushState(null, '', '/admin');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  refreshAdminData();
}

function scrollToSection(sectionId) {
  showTouristHome();
  const el = document.getElementById(sectionId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' });
  }
}

// ===================================================================
// PROPERTIES FETCHING & RENDERING (Matches Image 3)
// ===================================================================
async function loadProperties() {
  const grid = document.getElementById('properties-grid');
  const emptyState = document.getElementById('properties-empty-state');

  try {
    const res = await fetch('/api/v1/properties');
    if (!res.ok) throw new Error('Failed to fetch properties');
    propertiesCache = await res.json();
    renderFilteredProperties();
  } catch (err) {
    console.error('Properties load error:', err);
    if (grid) {
      grid.innerHTML = `
        <div class="empty-state-box" style="grid-column: 1 / -1;">
          <div class="empty-icon">⚠️</div>
          <div class="empty-title">Server bilan aloqa vaqtincha uzildi</div>
          <p class="empty-subtitle">Iltimos, qayta urinib ko'ring yoki sahifani yangilang.</p>
          <button class="btn-primary-pill" onclick="loadProperties()">Qayta yuklash</button>
        </div>
      `;
    }
  }
}

function renderFilteredProperties() {
  const grid = document.getElementById('properties-grid');
  const emptyState = document.getElementById('properties-empty-state');
  if (!grid) return;

  let filtered = propertiesCache.filter(p => {
    // Micro-district filter
    if (activeMicroDistrict !== 'ALL' && p.micro_district !== activeMicroDistrict) {
      return false;
    }
    // Road condition filter
    if (filterRoadOnly && p.road_condition !== 'ASPHALT_SEDAN') {
      return false;
    }
    // Generator filter
    if (filterGeneratorOnly && !p.has_generator) {
      return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    grid.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');

  grid.innerHTML = filtered.map(p => {
    // Parse photos
    let photos = [];
    try { photos = typeof p.photos_json === 'string' ? JSON.parse(p.photos_json) : p.photos_json; } catch(e) {}
    const thumb = (photos && photos.length > 0) ? photos[0] : 'https://images.unsplash.com/photo-1542718610-a1d656d1884c?auto=format&fit=crop&w=800&q=80';

    // Parse amenities
    let amenities = [];
    try { amenities = typeof p.amenities_json === 'string' ? JSON.parse(p.amenities_json) : p.amenities_json; } catch(e) {}
    const miniBadges = (amenities || []).slice(0, 3).map(a => `<span class="mini-badge">${a}</span>`).join('');

    // Min price from units
    let minPrice = 1200000;
    let maxGuests = 6;
    if (p.units && p.units.length > 0) {
      minPrice = Math.min(...p.units.map(u => u.base_price_weekday));
      maxGuests = Math.max(...p.units.map(u => u.capacity_standard));
    }

    const isFav = wishlistItems.has(p.slug);
    const favClass = isFav ? 'active' : '';

    return `
      <div class="property-card" onclick="openBookingModal('${p.id}')">
        <div class="property-image-container">
          <img src="${thumb}" alt="${p.title}" class="property-image" loading="lazy">
          <span class="property-badge-tag">${p.micro_district}</span>
          <button class="property-wishlist-btn ${favClass}" onclick="event.stopPropagation(); toggleWishlist('${p.slug}', this);" title="Saqlash">
            ${isFav ? '❤️' : '🤍'}
          </button>
        </div>

        <div class="property-card-body">
          <div class="property-location-line">
            <span>📍</span>
            <span>Zomin, ${p.micro_district === 'DUOBA' ? 'Duoba' : (p.micro_district === 'SUFFA' ? 'Suffa Platosi' : (p.micro_district === 'ORIKLISOY' ? 'O\'riklisoy' : 'Sanatoriy'))}</span>
          </div>

          <h3 class="property-card-title">${p.title}</h3>
          <p class="property-card-desc">${p.description}</p>

          <div class="property-amenities-mini">
            ${miniBadges}
          </div>

          <div class="property-card-footer">
            <div class="footer-left-meta">
              <span>👥 ${maxGuests} mehmon</span>
              <span class="meta-rating"><span class="star-icon">⭐</span> 4.8 (124)</span>
            </div>
            <div class="footer-price-block">
              <span class="price-main">${formatSum(minPrice)} so‘m</span>
              <span class="price-period">/ ${p.property_type === 'CHOYXONA_TAPCHAN' ? 'kun' : 'kecha'}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// Quick Filters
function applyQuickFilter(district) {
  activeMicroDistrict = district;
  document.querySelectorAll('.chip-filter').forEach(btn => btn.classList.remove('active'));
  
  const mapBtn = {
    'ALL': 'filter-chip-all',
    'DUOBA': 'filter-chip-duoba',
    'SUFFA': 'filter-chip-suffa',
    'ORIKLISOY': 'filter-chip-tapchan',
    'SANATORIY': 'filter-chip-sanatoriy'
  };
  const activeBtn = document.getElementById(mapBtn[district]);
  if (activeBtn) activeBtn.classList.add('active');

  const sel = document.getElementById('search-micro-district');
  if (sel) sel.value = district;

  renderFilteredProperties();
}

function toggleRoadFilter() {
  filterRoadOnly = !filterRoadOnly;
  const btn = document.getElementById('filter-chip-spark');
  if (btn) btn.classList.toggle('active', filterRoadOnly);
  renderFilteredProperties();
}

function toggleGeneratorFilter() {
  filterGeneratorOnly = !filterGeneratorOnly;
  const btn = document.getElementById('filter-chip-generator');
  if (btn) btn.classList.toggle('active', filterGeneratorOnly);
  renderFilteredProperties();
}

function clearAllFilters() {
  activeMicroDistrict = 'ALL';
  filterRoadOnly = false;
  filterGeneratorOnly = false;
  document.querySelectorAll('.chip-filter').forEach(b => b.classList.remove('active'));
  const allBtn = document.getElementById('filter-chip-all');
  if (allBtn) allBtn.classList.add('active');
  const sel = document.getElementById('search-micro-district');
  if (sel) sel.value = 'ALL';
  renderFilteredProperties();
}

function triggerSearchFilter() {
  const sel = document.getElementById('search-micro-district');
  if (sel) {
    applyQuickFilter(sel.value);
  }
}

function executeHeroSearch() {
  triggerSearchFilter();
  scrollToSection('properties-section');
  showToast('Qidiruv natijalari yangilandi', 'success');
}

function toggleWishlist(slug, btn) {
  if (wishlistItems.has(slug)) {
    wishlistItems.delete(slug);
    btn.innerHTML = '🤍';
    btn.classList.remove('active');
    showToast('Saralanganlardan chiqarildi', 'info');
  } else {
    wishlistItems.add(slug);
    btn.innerHTML = '❤️';
    btn.classList.add('active');
    showToast('Saralanganlarga saqlandi', 'success');
  }
}

// ===================================================================
// LEAFLET INTERACTIVE MAP SECTION
// ===================================================================
function initLeafletMap() {
  const mapEl = document.getElementById('zomin-leaflet-map');
  if (!mapEl || typeof L === 'undefined') return;

  // Center of Zaamin Tourism District
  leafletMap = L.map('zomin-leaflet-map', {
    scrollWheelZoom: false
  }).setView([39.90, 68.43], 12);

  // Modern Clean Tile Layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors | Zomin Tourism'
  }).addTo(leafletMap);

  // Seed Map Markers
  const locations = [
    {
      id: "prop-duoba-villa",
      type: "DACHA",
      title: "Duoba Soy Bo'yi Premium Villa",
      price: "1 500 000 so'm",
      lat: 39.9612,
      lng: 68.4231,
      img: "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=600&q=80"
    },
    {
      id: "prop-suffa-chalet",
      type: "DACHA",
      title: "Suffa Panoramik Tog' Kotteji (2400m)",
      price: "1 800 000 so'm",
      lat: 39.8715,
      lng: 68.4520,
      img: "https://images.unsplash.com/photo-1542718610-a1d656d1884c?auto=format&fit=crop&w=600&q=80"
    },
    {
      id: "prop-oriklisoy-tapchan",
      type: "TAPCHAN",
      title: "O'riklisoy Buloq Bo'yi Choyxonasi",
      price: "150 000 so'm",
      lat: 39.9210,
      lng: 68.3980,
      img: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=600&q=80"
    },
    {
      id: "prop-sanatoriy-lodge",
      type: "DACHA",
      title: "Zomin Sanatoriy Yonidagi Mehmon Uyi",
      price: "1 000 000 so'm",
      lat: 39.9450,
      lng: 68.4110,
      img: "https://images.unsplash.com/photo-1587061949409-02df41d5e562?auto=format&fit=crop&w=600&q=80"
    },
    {
      id: "attraction-bridge",
      type: "ATTRACTION",
      title: "Zomin osma ko‘prigi (305m)",
      price: "Diqqatga sazovor",
      lat: 39.8900,
      lng: 68.4400,
      img: "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=600&q=80"
    },
    {
      id: "attraction-cablecar",
      type: "ATTRACTION",
      title: "Bartholet Dor Yo'li (2400m)",
      price: "Kabel yo'li",
      lat: 39.8750,
      lng: 68.4550,
      img: "https://images.unsplash.com/photo-1516431883659-655d41c09bf9?auto=format&fit=crop&w=600&q=80"
    }
  ];

  locations.forEach(loc => {
    const marker = L.marker([loc.lat, loc.lng]).addTo(leafletMap);
    
    const popupContent = `
      <div class="map-popup-card">
        <img src="${loc.img}" alt="${loc.title}" class="map-popup-img">
        <div class="map-popup-title">${loc.title}</div>
        <div class="map-popup-price">${loc.price}</div>
        <button class="btn-popup-action" onclick="handleMapPinAction('${loc.id}', '${loc.type}')">
          ${loc.type === 'ATTRACTION' ? 'Batafsil' : 'Bron qilish'}
        </button>
      </div>
    `;
    marker.bindPopup(popupContent);
    mapMarkers.push({ marker, type: loc.type });
  });
}

function handleMapPinAction(id, type) {
  if (type === 'ATTRACTION') {
    openAttractionModal(id.replace('attraction-', ''));
  } else {
    // Find matching property in cache
    const match = propertiesCache.find(p => p.id === id || p.slug.includes(id.replace('prop-', '')));
    if (match) {
      openBookingModal(match.id);
    } else if (propertiesCache.length > 0) {
      openBookingModal(propertiesCache[0].id);
    }
  }
}

function filterMapMarkers(type) {
  document.querySelectorAll('.map-ctrl-chip').forEach(c => c.classList.remove('active'));
  event.target.classList.add('active');

  mapMarkers.forEach(item => {
    if (type === 'ALL' || item.type === type) {
      leafletMap.addLayer(item.marker);
    } else {
      leafletMap.removeLayer(item.marker);
    }
  });
}

// ===================================================================
// BOOKING FLOW & RESERVATION MODAL
// ===================================================================
async function openBookingModal(propertyId) {
  selectedProperty = propertiesCache.find(p => p.id === propertyId);
  if (!selectedProperty) {
    selectedProperty = propertiesCache[0];
  }
  if (!selectedProperty) return;

  const modal = document.getElementById('booking-modal');
  modal.classList.remove('hidden');

  // Fill Header & Details
  document.getElementById('modal-property-badge').innerText = selectedProperty.micro_district;
  document.getElementById('modal-property-title').innerText = selectedProperty.title;
  document.getElementById('modal-property-address').innerText = `📍 ${selectedProperty.address_text || 'Zomin'}`;
  document.getElementById('modal-property-desc').innerText = selectedProperty.description;

  // Photos
  let photos = [];
  try { photos = typeof selectedProperty.photos_json === 'string' ? JSON.parse(selectedProperty.photos_json) : selectedProperty.photos_json; } catch(e) {}
  const mainPhoto = (photos && photos.length > 0) ? photos[0] : 'https://images.unsplash.com/photo-1542718610-a1d656d1884c?auto=format&fit=crop&w=1200&q=80';
  document.getElementById('modal-main-photo').src = mainPhoto;

  const thumbsContainer = document.getElementById('modal-gallery-thumbs');
  thumbsContainer.innerHTML = (photos || []).map((p, idx) => `
    <img src="${p}" class="gallery-thumb-item ${idx === 0 ? 'active' : ''}" onclick="changeMainGalleryPhoto('${p}', this)">
  `).join('');

  // Amenities
  let amenities = [];
  try { amenities = typeof selectedProperty.amenities_json === 'string' ? JSON.parse(selectedProperty.amenities_json) : selectedProperty.amenities_json; } catch(e) {}
  document.getElementById('modal-amenities-tags').innerHTML = (amenities || []).map(a => `
    <span class="amenity-chip">✓ ${a}</span>
  `).join('');

  // Road & Generator Trust
  document.getElementById('modal-road-info').innerText = selectedProperty.road_condition === 'ASPHALT_SEDAN' ? '🚗 Asfalt (Spark/Cobalt bemalol chiqadi)' : '🚙 4WD / Yuqori klirens talab etiladi';
  document.getElementById('modal-generator-info').innerText = selectedProperty.has_generator ? '⚡ Avtomat generator mavjud (Elektr kafolat)' : '⚠️ Oddiy tarmoq';
  document.getElementById('modal-water-info').innerText = selectedProperty.water_source === 'SPRING_WATER' ? '💧 Toza muzdek tog\' buloq suvi' : '🚰 Markaziy suv';

  // Unit Selector
  const unitSelect = document.getElementById('modal-unit-select');
  unitSelect.innerHTML = (selectedProperty.units || []).map(u => `
    <option value="${u.id}">${u.name} (${formatSum(u.base_price_weekday)} so'm/${selectedProperty.property_type === 'CHOYXONA_TAPCHAN' ? 'kun' : 'kecha'})</option>
  `).join('');

  // Auto-switch mode based on property type
  if (selectedProperty.property_type === 'CHOYXONA_TAPCHAN') {
    switchBookingMode('DAY_USE');
  } else {
    switchBookingMode('OVERNIGHT');
  }

  currentTandirKg = 0;
  updateTandirDisplay();
  await recalculateQuote();
}

function closeBookingModal() {
  document.getElementById('booking-modal').classList.add('hidden');
}

function changeMainGalleryPhoto(src, thumbEl) {
  document.getElementById('modal-main-photo').src = src;
  document.querySelectorAll('.gallery-thumb-item').forEach(t => t.classList.remove('active'));
  thumbEl.classList.add('active');
}

function switchBookingMode(mode) {
  currentBookingMode = mode;
  document.getElementById('btn-mode-overnight').classList.toggle('active', mode === 'OVERNIGHT');
  document.getElementById('btn-mode-dayuse').classList.toggle('active', mode === 'DAY_USE');

  const slotPicker = document.getElementById('day-use-slot-picker');
  const groupEnd = document.getElementById('group-end-date');
  const labelStart = document.getElementById('label-start-date');

  if (mode === 'DAY_USE') {
    slotPicker.classList.remove('hidden');
    groupEnd.classList.add('hidden');
    labelStart.innerText = 'Tashrif sanasi:';
    if (!currentDayUseSlot) selectDaySlot('FULL_DAY');
  } else {
    slotPicker.classList.add('hidden');
    groupEnd.classList.remove('hidden');
    labelStart.innerText = 'Kirish sanasi:';
  }

  recalculateQuote();
}

function selectDaySlot(slot) {
  currentDayUseSlot = slot;
  document.querySelectorAll('.slot-card').forEach(c => c.classList.remove('active'));
  const card = document.getElementById(`slot-card-${slot}`);
  if (card) card.classList.add('active');
  recalculateQuote();
}

function onUnitSelectChange() {
  recalculateQuote();
}

function adjustTandir(delta) {
  currentTandirKg = Math.max(0, currentTandirKg + delta);
  updateTandirDisplay();
  recalculateQuote();
}

function updateTandirDisplay() {
  document.getElementById('tandir-kg-display').innerText = `${currentTandirKg} kg`;
  document.getElementById('tandir-cost-display').innerText = `${formatSum(currentTandirKg * 150000)} so'm`;
}

// Live Quote Calculation API (AC-03, AC-12)
async function recalculateQuote() {
  if (!selectedProperty) return;
  const unitId = document.getElementById('modal-unit-select').value;
  if (!unitId) return;

  const startDate = document.getElementById('modal-start-date').value;
  let endDate = document.getElementById('modal-end-date').value;

  let checkinIso = '';
  let checkoutIso = '';

  if (currentBookingMode === 'DAY_USE') {
    endDate = startDate;
    if (currentDayUseSlot === 'LUNCH') {
      checkinIso = `${startDate}T10:00:00+05:00`;
      checkoutIso = `${startDate}T16:00:00+05:00`;
    } else if (currentDayUseSlot === 'DINNER') {
      checkinIso = `${startDate}T17:00:00+05:00`;
      checkoutIso = `${startDate}T23:00:00+05:00`;
    } else {
      checkinIso = `${startDate}T10:00:00+05:00`;
      checkoutIso = `${startDate}T22:00:00+05:00`;
    }
  } else {
    checkinIso = `${startDate}T14:00:00+05:00`;
    checkoutIso = `${endDate}T12:00:00+05:00`;
  }

  try {
    const res = await fetch('/api/v1/quotes/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        unit_id: unitId,
        check_in_date: checkinIso,
        check_out_date: checkoutIso,
        guests_count: 4,
        booking_mode: currentBookingMode,
        day_use_slot: currentBookingMode === 'DAY_USE' ? currentDayUseSlot : null,
        tandir_meat_kg: currentTandirKg
      })
    });

    if (res.ok) {
      currentQuote = await res.json();
      renderQuoteSummary(currentQuote);
    }
  } catch (err) {
    console.error('Quote calculation error:', err);
  }
}

function renderQuoteSummary(q) {
  document.getElementById('quote-stay-amount').innerText = `${formatSum(q.base_stay_amount)} so'm`;
  
  const tandirRow = document.getElementById('quote-tandir-row');
  if (q.tandir_meat_amount > 0) {
    tandirRow.style.display = 'flex';
    document.getElementById('quote-tandir-amount').innerText = `${formatSum(q.tandir_meat_amount)} so'm`;
  } else {
    tandirRow.style.display = 'none';
  }

  document.getElementById('quote-total-amount').innerText = `${formatSum(q.total_amount)} so'm`;
  document.getElementById('quote-deposit-amount').innerText = `${formatSum(q.platform_fee_deposit)} so'm`;
  document.getElementById('quote-remaining-amount').innerText = `${formatSum(q.remaining_owner_amount)} so'm`;
}

// Booking Reservation Submission (AC-01 15-Minute Hold)
async function submitBookingReservation() {
  if (!currentQuote) {
    showToast('Iltimos, narx hisoblanishini kuting', 'error');
    return;
  }

  const carPlate = document.getElementById('modal-car-plate').value || '01 A 777 AA';
  const unitId = document.getElementById('modal-unit-select').value;
  const startDate = document.getElementById('modal-start-date').value;
  let endDate = document.getElementById('modal-end-date').value;

  let checkinIso = '';
  let checkoutIso = '';

  if (currentBookingMode === 'DAY_USE') {
    endDate = startDate;
    if (currentDayUseSlot === 'LUNCH') {
      checkinIso = `${startDate}T10:00:00+05:00`;
      checkoutIso = `${startDate}T16:00:00+05:00`;
    } else if (currentDayUseSlot === 'DINNER') {
      checkinIso = `${startDate}T17:00:00+05:00`;
      checkoutIso = `${startDate}T23:00:00+05:00`;
    } else {
      checkinIso = `${startDate}T10:00:00+05:00`;
      checkoutIso = `${startDate}T22:00:00+05:00`;
    }
  } else {
    checkinIso = `${startDate}T14:00:00+05:00`;
    checkoutIso = `${endDate}T12:00:00+05:00`;
  }

  try {
    const res = await fetch('/api/v1/bookings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        property_id: selectedProperty.id,
        unit_id: unitId,
        guest_id: currentUser ? currentUser.id : "usr-guest-jasur",
        check_in_date: checkinIso,
        check_out_date: checkoutIso,
        guests_count: 4,
        booking_mode: currentBookingMode,
        day_use_slot: currentBookingMode === 'DAY_USE' ? currentDayUseSlot : null,
        tandir_meat_kg: currentTandirKg,
        car_plate_number: carPlate,
        base_stay_amount: currentQuote.base_stay_amount,
        tandir_meat_amount: currentQuote.tandir_meat_amount,
        total_amount: currentQuote.total_amount,
        platform_fee_deposit: currentQuote.platform_fee_deposit,
        remaining_owner_amount: currentQuote.remaining_owner_amount
      })
    });

    if (res.ok) {
      currentBooking = await res.json();
      closeBookingModal();
      openPaymentModal(currentBooking);
      showToast('Joy 15 daqiqaga muvaffaqiyatli band qilindi!', 'success');
    } else {
      const err = await res.json();
      showToast(`Xatolik: ${err.detail || 'Ushbu vaqtda joy band'}`, 'error');
    }
  } catch (err) {
    showToast('Bron qilishda xatolik yuz berdi', 'error');
  }
}

// ===================================================================
// PAYMENT MODAL & SIMULATION (Click / Payme & Soliq OFD Chek)
// ===================================================================
let selectedPaymentProvider = 'CLICK';

function openPaymentModal(booking) {
  document.getElementById('payment-modal').classList.remove('hidden');
  document.getElementById('pay-summary-title').innerText = selectedProperty ? selectedProperty.title : 'Dacha';
  document.getElementById('pay-summary-dates').innerText = `${booking.check_in_date.split('T')[0]} - ${booking.check_out_date.split('T')[0]}`;
  document.getElementById('pay-summary-amount').innerText = `${formatSum(booking.platform_fee_deposit)} so'm`;

  startHoldTimer(15 * 60);
}

function closePaymentModal() {
  document.getElementById('payment-modal').classList.add('hidden');
  if (holdTimerInterval) clearInterval(holdTimerInterval);
}

function choosePaymentProvider(provider) {
  selectedPaymentProvider = provider;
  document.getElementById('card-choice-click').classList.toggle('active', provider === 'CLICK');
  document.getElementById('card-choice-payme').classList.toggle('active', provider === 'PAYME');
}

function startHoldTimer(seconds) {
  if (holdTimerInterval) clearInterval(holdTimerInterval);
  let remain = seconds;
  const clock = document.getElementById('hold-countdown-clock');

  holdTimerInterval = setInterval(() => {
    remain--;
    if (remain <= 0) {
      clearInterval(holdTimerInterval);
      clock.innerText = '00:00 (Muddati o\'tdi)';
      showToast('15 daqiqalik qulf muddati tugadi', 'error');
      closePaymentModal();
      return;
    }
    const m = Math.floor(remain / 60).toString().padStart(2, '0');
    const s = (remain % 60).toString().padStart(2, '0');
    clock.innerText = `${m}:${s}`;
  }, 1000);
}

// Simulate Successful Payment
async function processPaymentSimulation() {
  if (!currentBooking) return;
  const btn = document.getElementById('btn-execute-payment');
  btn.innerText = 'To\'lov amalga oshirilmoqda...';

  try {
    let res = null;
    if (selectedPaymentProvider === 'CLICK') {
      // Click Complete
      res = await fetch('/api/v1/payments/click/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          click_trans_id: Date.now(),
          service_id: 19827,
          merchant_trans_id: currentBooking.id,
          merchant_prepare_id: 1001,
          amount: currentBooking.platform_fee_deposit,
          action: 1,
          error: 0,
          error_note: "Success",
          sign_time: new Date().toISOString(),
          sign_string: "demo_sign"
        })
      });
    } else {
      // Payme Perform
      res = await fetch('/api/v1/payments/payme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          method: 'PerformTransaction',
          params: {
            id: `payme_sim_${Date.now()}`
          }
        })
      });
    }

    clearInterval(holdTimerInterval);
    closePaymentModal();
    showToast('To\'lov muvaffaqiyatli! Soliq OFD elektron chek yaratildi.', 'success');
    await openOfflineVoucher(currentBooking.id);
  } catch (err) {
    showToast('To\'lovda xatolik yuz berdi', 'error');
  } finally {
    btn.innerText = '💳 To\'lovni tasdiqlash';
  }
}

// ===================================================================
// OFFLINE TRAVEL VOUCHER (AC-09)
// ===================================================================
async function openOfflineVoucher(bookingId) {
  try {
    const res = await fetch(`/api/v1/vouchers/offline/${bookingId}`);
    if (!res.ok) throw new Error('Voucher fetch failed');
    const v = await res.json();

    document.getElementById('voucher-modal').classList.remove('hidden');
    document.getElementById('vouch-code').innerText = v.voucher_code;
    document.getElementById('vouch-title').innerText = v.property_title;
    document.getElementById('vouch-dates').innerText = `${v.check_in_date.split('T')[0]} - ${v.check_out_date.split('T')[0]}`;
    document.getElementById('vouch-coords').innerText = `${v.latitude}, ${v.longitude}`;
    document.getElementById('vouch-yandex-link').href = v.yandex_navigator_url;

    document.getElementById('vouch-owner-name').innerText = v.owner_contact.name;
    document.getElementById('vouch-owner-phone').href = v.owner_contact.phone_link;

    document.getElementById('vouch-caretaker-name').innerText = v.caretaker_contact.name;
    document.getElementById('vouch-caretaker-phone').href = v.caretaker_contact.phone_link;

    document.getElementById('vouch-directions-text').innerText = v.mountain_directions_uz;
    document.getElementById('vouch-ofd-receipt').innerText = `Chek: ${v.fiscal_receipt.ofd_receipt_id}`;
  } catch (err) {
    showToast('Vaucher yuklashda xatolik', 'error');
  }
}

function closeVoucherModal() {
  document.getElementById('voucher-modal').classList.add('hidden');
}

// ===================================================================
// ATTRACTION DETAILS MODAL
// ===================================================================
function openAttractionModal(attrKey) {
  const item = ATTRACTIONS[attrKey];
  if (!item) return;

  document.getElementById('attr-modal-title').innerText = item.title;
  document.getElementById('attr-modal-img').src = item.img;
  document.getElementById('attr-modal-desc').innerText = item.desc;
  document.getElementById('attr-modal-meta').innerText = item.meta;

  document.getElementById('attraction-modal').classList.remove('hidden');
}

function closeAttractionModal() {
  document.getElementById('attraction-modal').classList.add('hidden');
}

// ===================================================================
// USER MODALS (My Trips, Owner, Caretaker, Switcher, Partner)
// ===================================================================
function openProfileSwitcherModal() {
  const menu = document.getElementById('profile-dropdown-menu');
  if (menu && !menu.classList.contains('hidden')) {
    menu.classList.add('hidden');
    return;
  }
  document.getElementById('profile-switcher-modal').classList.remove('hidden');
}

function closeProfileSwitcherModal() {
  document.getElementById('profile-switcher-modal').classList.add('hidden');
}

// Profile button click handler (toggles dropdown)
document.addEventListener('click', (e) => {
  const container = document.querySelector('.user-action-container');
  const menu = document.getElementById('profile-dropdown-menu');
  if (container && menu && !container.contains(e.target)) {
    menu.classList.add('hidden');
  }
});

const headerKirishBtn = document.getElementById('header-kirish-btn');
if (headerKirishBtn) {
  headerKirishBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const menu = document.getElementById('profile-dropdown-menu');
    if (menu) menu.classList.toggle('hidden');
  });
}

// My Trips
async function openMyTripsModal() {
  document.getElementById('profile-dropdown-menu').classList.add('hidden');
  document.getElementById('trips-modal').classList.remove('hidden');

  const container = document.getElementById('trips-list-container');
  container.innerHTML = '<div class="text-center p-4">Safarlar yuklanmoqda...</div>';

  try {
    const res = await fetch(`/api/v1/bookings/my-bookings?user_id=${currentUser ? currentUser.id : 'usr-guest-jasur'}`);
    if (!res.ok) throw new Error('Fetch failed');
    const bookings = await res.json();

    if (bookings.length === 0) {
      container.innerHTML = '<div class="empty-state-box"><div class="empty-title">Sizda hali bronlar mavjud emas</div></div>';
      return;
    }

    container.innerHTML = bookings.map(b => `
      <div class="summary-line" style="background:#fff; padding:16px; border-radius:12px; margin-bottom:12px; border:1px solid #e7e4dc;">
        <div>
          <strong style="display:block; font-size:15px;">Bron #${b.id.substring(0,8)}</strong>
          <span style="font-size:13px; color:#5c6e67;">${b.check_in_date.split('T')[0]} - ${b.check_out_date.split('T')[0]}</span>
          <div style="margin-top:4px;"><span class="badge-status ${b.booking_status.toLowerCase()}">${b.booking_status}</span></div>
        </div>
        <div style="text-align:right;">
          <div style="font-weight:800; font-size:15px; color:#0d382c;">${formatSum(b.total_amount)} so'm</div>
          <button class="btn-primary-pill" style="padding:6px 14px; font-size:12px; margin-top:8px;" onclick="openOfflineVoucher('${b.id}')">
            📄 Vaucher / Chek
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = '<div class="text-center text-danger p-4">Yuklashda xatolik yuz berdi</div>';
  }
}

function closeMyTripsModal() {
  document.getElementById('trips-modal').classList.add('hidden');
}

// Owner Portal Modal
async function openOwnerPortalModal() {
  document.getElementById('profile-dropdown-menu').classList.add('hidden');
  document.getElementById('owner-modal').classList.remove('hidden');

  const ownerId = currentUser ? currentUser.id : "usr-owner-alisher";
  document.getElementById('owner-modal-name').innerText = currentUser ? currentUser.full_name : "Alisher Zokirov";
  document.getElementById('owner-modal-phone').innerText = currentUser ? currentUser.phone_number : "+998 90 111 22 33";

  const listEl = document.getElementById('owner-bookings-list');
  listEl.innerHTML = '<div class="text-center p-3">Yuklanmoqda...</div>';

  try {
    const res = await fetch(`/api/v1/owner/properties/${selectedProperty ? selectedProperty.id : 'prop-duoba-villa'}/bookings?owner_id=${ownerId}`);
    if (!res.ok) throw new Error('Fetch failed');
    const bookings = await res.json();

    if (bookings.length === 0) {
      listEl.innerHTML = '<div class="p-3 text-center text-muted">Hozircha yangi so\'rovlar yo\'q</div>';
      return;
    }

    listEl.innerHTML = bookings.map(b => `
      <div style="background:#fff; padding:16px; border-radius:12px; border:1px solid #e7e4dc; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <strong>Mehmon bron so'rovi</strong>
          <div style="font-size:13px; color:#5c6e67;">Muddat: ${b.check_in_date.split('T')[0]} - ${b.check_out_date.split('T')[0]}</div>
          <div style="font-size:13px; color:#0d382c; font-weight:700;">Jami: ${formatSum(b.total_amount)} so'm (Kafolat to'langan)</div>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn-table-action" style="background:#10b981; color:#fff;" onclick="ownerDecision('${b.id}', 'ACCEPT')">Qabul qilish</button>
          <button class="btn-table-action danger" onclick="ownerDecision('${b.id}', 'REJECT')">Rad etish</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    listEl.innerHTML = '<div class="p-3 text-center text-danger">So\'rovlarni yuklashda xatolik</div>';
  }
}

async function ownerDecision(bookingId, decision) {
  try {
    const res = await fetch(`/api/v1/owner/bookings/${bookingId}/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        owner_id: currentUser ? currentUser.id : "usr-owner-alisher",
        decision: decision
      })
    });
    if (res.ok) {
      showToast(`So'rov ${decision === 'ACCEPT' ? 'qabul qilindi' : 'rad etildi'}!`, 'success');
      openOwnerPortalModal();
    }
  } catch (err) {
    showToast('Amalda xatolik', 'error');
  }
}

async function triggerOwnerIVRCheck() {
  try {
    const res = await fetch(`/api/v1/owner/check-unanswered-ivr`, { method: 'POST' });
    const data = await res.json();
    showToast(`IVR tekshiruvi: ${data.calls_dispatched} ta dacha egasiga avtomat qo'ng'iroq yo'llandi`, 'success');
  } catch (err) {
    showToast('IVR xizmatida xatolik', 'error');
  }
}

function closeOwnerPortalModal() {
  document.getElementById('owner-modal').classList.add('hidden');
}

// Caretaker Gate Modal
async function openCaretakerModal() {
  document.getElementById('profile-dropdown-menu').classList.add('hidden');
  document.getElementById('caretaker-modal').classList.remove('hidden');

  const listEl = document.getElementById('caretaker-arrivals-list');
  listEl.innerHTML = `
    <div style="background:#fff; padding:18px; border-radius:12px; border:2px solid #0d382c; margin-bottom:14px;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:12px; font-weight:800; background:#fef3c7; color:#b45309; padding:4px 8px; border-radius:6px;">KUTILYAPTI</span>
        <span style="font-size:13px; color:#5c6e67;">Bugun, 14:00</span>
      </div>
      <div style="margin:12px 0;">
        <div style="font-size:24px; font-weight:900; letter-spacing:2px; font-family:monospace; color:#0d382c;">01 A 777 AA</div>
        <div style="font-size:15px; font-weight:700;">Jasur Mamadaliyev</div>
        <div style="font-size:13px; color:#5c6e67;">4 nafar mehmon</div>
      </div>
      <button class="btn-primary-pill w-100" style="padding:12px;" onclick="showToast('Kalit topshirildi! Check-in muvaffaqiyatli amalga oshirildi.', 'success'); closeCaretakerModal();">
        🔑 Kalit topshirildi (Check-in)
      </button>
    </div>
  `;
}

function closeCaretakerModal() {
  document.getElementById('caretaker-modal').classList.add('hidden');
}

// Partner Modal
function openPartnerModal() {
  document.getElementById('partner-modal').classList.remove('hidden');
}

function closePartnerModal() {
  document.getElementById('partner-modal').classList.add('hidden');
}

function handlePartnerSubmit(e) {
  e.preventDefault();
  closePartnerModal();
  showToast('Arizangiz qabul qilindi! Menejerimiz tez orada bog\'lanadi.', 'success');
}

function submitNewsletter() {
  const emailInput = document.getElementById('footer-newsletter-email');
  if (emailInput && emailInput.value) {
    showToast('Rahmat! Zomin yangiliklariga muvaffaqiyatli obuna bo\'ldingiz.', 'success');
    emailInput.value = '';
  } else {
    showToast('Iltimos, elektron pochtangizni kiriting', 'error');
  }
}

// ===================================================================
// DEDICATED ADMIN PORTAL OPERATIONS (Matches TZ & AC criteria)
// ===================================================================
async function refreshAdminData() {
  try {
    // 1. Dashboard Stats
    const statsRes = await fetch('/api/v1/admin/dashboard-stats');
    if (statsRes.ok) {
      const stats = await statsRes.json();
      document.getElementById('admin-stat-gmv').innerText = `${formatSum(stats.total_gmv)} so'm`;
      document.getElementById('admin-stat-revenue').innerText = `${formatSum(stats.total_platform_fee ?? stats.platform_net_revenue)} so'm`;
      document.getElementById('admin-stat-properties').innerText = `${stats.verified_properties ?? stats.verified_properties_count ?? 4} ta`;
      document.getElementById('admin-stat-bookings').innerText = `${stats.total_bookings ?? stats.total_bookings_count ?? 0} ta`;
    }

    // 2. Admin Properties
    const propsRes = await fetch('/api/v1/admin/properties');
    if (propsRes.ok) {
      const props = await propsRes.json();
      const tbody = document.getElementById('admin-properties-table-body');
      tbody.innerHTML = props.map(p => `
        <tr>
          <td><strong>${p.title}</strong><br><span style="font-size:11px; color:#5c6e67;">${p.micro_district}</span></td>
          <td>${p.owner_id}</td>
          <td><span class="badge-status ${p.verification_status.toLowerCase()}">${p.verification_status}</span></td>
          <td>${formatSum(p.starting_price_weekday || 1200000)} so'm</td>
          <td>${p.road_condition === 'ASPHALT_SEDAN' ? '✅ Spark chiqadi' : '🚙 4WD'}</td>
          <td>
            <button class="btn-table-action" onclick="verifyAdminProperty('${p.id}', 'VERIFIED')">Tasdiqlash</button>
            <button class="btn-table-action danger" onclick="verifyAdminProperty('${p.id}', 'REJECTED')">Rad etish</button>
          </td>
        </tr>
      `).join('');
    }

    // 3. Admin Bookings
    const bookingsRes = await fetch('/api/v1/admin/bookings');
    if (bookingsRes.ok) {
      const bookings = await bookingsRes.json();
      const tbody = document.getElementById('admin-bookings-table-body');
      tbody.innerHTML = bookings.map(b => `
        <tr>
          <td><code>${b.id.substring(0,8)}</code></td>
          <td>${b.guest_id}</td>
          <td>${b.property_id}</td>
          <td>${b.check_in_date.split('T')[0]}</td>
          <td><strong>${formatSum(b.total_amount)} so'm</strong></td>
          <td><span class="badge-status ${b.booking_status.toLowerCase()}">${b.booking_status}</span></td>
          <td>
            <button class="btn-table-action danger" onclick="forceCancelAdminBooking('${b.id}')">Bekor qilish</button>
          </td>
        </tr>
      `).join('');
    }

    // 4. Admin Payments
    const payRes = await fetch('/api/v1/admin/payments');
    if (payRes.ok) {
      const payments = await payRes.json();
      const tbody = document.getElementById('admin-payments-table-body');
      tbody.innerHTML = payments.map(p => `
        <tr>
          <td><code>${p.id.substring(0,8)}</code></td>
          <td><strong>${p.provider}</strong></td>
          <td>${p.booking_id.substring(0,8)}</td>
          <td>${formatSum(p.amount)} so'm</td>
          <td><code>${p.ofd_receipt_id || 'OFD-998811'}</code></td>
          <td>${p.created_at.split('T')[0]}</td>
          <td><span class="badge-status verified">${p.payment_status}</span></td>
        </tr>
      `).join('');
    }

    // 5. Admin Users
    const usersRes = await fetch('/api/v1/admin/users');
    if (usersRes.ok) {
      const users = await usersRes.json();
      const tbody = document.getElementById('admin-users-table-body');
      tbody.innerHTML = users.map(u => `
        <tr>
          <td><strong>${u.full_name}</strong></td>
          <td>${u.phone_number}</td>
          <td><span class="badge-status verified">${u.role}</span></td>
          <td>${u.created_at ? u.created_at.split('T')[0] : '2026-10-28'}</td>
          <td><span class="badge-status ${u.is_active ? 'verified' : 'rejected'}">${u.is_active ? 'Faol' : 'Bloklangan'}</span></td>
          <td>
            <button class="btn-table-action ${u.is_active ? 'danger' : ''}" onclick="toggleUserStatus('${u.id}', ${!u.is_active})">
              ${u.is_active ? 'Bloklash' : 'Faollashtirish'}
            </button>
          </td>
        </tr>
      `).join('');
    }

    // 6. Admin Audit Logs
    const auditRes = await fetch('/api/v1/admin/audit-logs');
    if (auditRes.ok) {
      const logs = await auditRes.json();
      const tbody = document.getElementById('admin-audit-table-body');
      tbody.innerHTML = logs.map(l => `
        <tr>
          <td>${l.created_at.replace('T', ' ').substring(0, 19)}</td>
          <td><strong>${l.action}</strong></td>
          <td><code>${l.entity_type}:${l.entity_id.substring(0,8)}</code></td>
          <td>${l.performed_by}</td>
          <td><small>${l.details_json || '{}'}</small></td>
        </tr>
      `).join('');
    }

  } catch (err) {
    console.error('Admin data refresh error:', err);
    showToast('Admin ma\'lumotlarini yuklashda xatolik', 'error');
  }
}

function switchAdminTab(tabKey) {
  document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.admin-tab-pane').forEach(p => p.classList.remove('active'));

  event.target.classList.add('active');
  const targetPane = document.getElementById(`admin-tab-${tabKey}`);
  if (targetPane) targetPane.classList.add('active');
}

async function verifyAdminProperty(propId, status) {
  try {
    const res = await fetch(`/api/v1/admin/properties/${propId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: status })
    });
    if (res.ok) {
      showToast(`Obyekt ${status} qilindi!`, 'success');
      refreshAdminData();
      loadProperties();
    }
  } catch (err) {
    showToast('Xatolik', 'error');
  }
}

async function forceCancelAdminBooking(bookingId) {
  if (!confirm('Ushbu bronni bekor qilishga ishonchingiz komilmi?')) return;
  try {
    const res = await fetch(`/api/v1/admin/bookings/${bookingId}/force-cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: 'Admin tomonidan bekor qilindi' })
    });
    if (res.ok) {
      showToast('Bron majburiy bekor qilindi!', 'success');
      refreshAdminData();
    }
  } catch (err) {
    showToast('Bekor qilishda xatolik', 'error');
  }
}

async function toggleUserStatus(userId, newActive) {
  try {
    const res = await fetch(`/api/v1/admin/users/${userId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: newActive })
    });
    if (res.ok) {
      showToast('Foydalanuvchi holati yangilandi', 'success');
      refreshAdminData();
    }
  } catch (err) {
    showToast('Xatolik', 'error');
  }
}
