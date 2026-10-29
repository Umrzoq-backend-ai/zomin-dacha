// ===================================================================
// Zomin — Master Application Script & Multilingual Engine (UZ / RU / EN)
// Matches Image 1 Master Reference with Clean Vector Icons & Real Auth
// ===================================================================

let currentLang = localStorage.getItem('zomin_lang') || 'uz';
let propertiesCache = [];
let selectedProperty = null;
let currentQuote = null;
let currentBooking = null;
let currentTandirKg = 0;
let currentDayUseSlot = null;
let currentBookingMode = 'OVERNIGHT';
let holdTimerInterval = null;
let leafletMap = null;
let mapMarkers = [];

let searchSelectedDistrict = 'ALL';
let searchCheckInDate = '';
let searchCheckOutDate = '';
let guestsAdults = 2;
let guestsChildren = 0;
let wishlistItems = new Set(['mountain-chalet-zomin', 'zomin-villa']);

// Multilingual Localization Dictionaries (UZ, RU, EN)
const I18N = {
  uz: {
    navStays: "Turar joylar",
    navDiscover: "Kashf etish",
    navRoutes: "Marshrutlar",
    navPartner: "Hamkor bo'lish",
    navLogin: "Kirish",
    heroTitle: "Zominni o‘zingizga<br>xos kashf eting.",
    heroSubtitle: "Tog‘lar, dam olish maskanlari va unutilmas sayohatlar — barchasi bir joyda.",
    searchWhere: "Qayerga?",
    searchLocationDefault: "Zomin",
    searchCheckIn: "Kelish",
    searchCheckOut: "Ketish",
    searchSelectDate: "Sanani tanlang",
    searchGuests: "Mehmonlar",
    searchGuestsFormat: (n) => `${n} mehmon`,
    searchBtn: "Qidirish",
    tagRecommended: "TAVSIYA ETILGAN",
    titleStays: "Sizga mos dam olish maskanlari",
    viewAll: "Barchasini ko'rish",
    currency: "so'm",
    locationZaamin: "Zomin, Jizzax",
    perNight: "/ kecha",
    perDay: "/ kun",
    guestsCount: (n) => `${n} mehmon`,
    cardChaletTitle: "Mountain Chalet Zomin",
    cardChaletDesc: "Tog‘ manzarali, yog‘och uy. Oila va do‘stlar uchun ideal.",
    cardVillaTitle: "Zomin Villa",
    cardVillaDesc: "Shaxsiy hovuz, zamonaviy qulayliklar va betakror manzara.",
    cardLodgeTitle: "Forest Lodge",
    cardLodgeDesc: "Tabiat bag‘rida, sokin va qulay dam olish maskani.",
    tagDiscover: "TABIAT VA SAYOHAT",
    titleDiscover: "Zominni kashf eting",
    tagMap: "INTERAKTIV XARITA",
    titleMap: "Zomin tog' xaritasi va maskanlar",
    detailsBtn: "Batafsil",
    bridgeCat: "Mashhur joy",
    bridgeTitle: "Zomin osma ko‘prigi",
    bridgeDesc: "Tog‘lar ustidan o‘tuvchi betakror ko‘prik — jasorat va go‘zallik uyg‘unligi.",
    cableCat: "Faoliyat",
    cableTitle: "Kabel yo‘li",
    cableDesc: "Zominning go‘zal manzaralarini balandlikdan kuzating.",
    hikingCat: "Marshrutlar",
    hikingTitle: "Sayr va piyoda yo‘llar",
    hikingDesc: "Tabiat qo‘ynida unutilmas sayohat marshrutlari.",
    footerTagline: "Tabiat. Dam olish. Sayohat.",
    footerMain: "Asosiy",
    footerInfo: "Foydali ma'lumotlar",
    footerConnect: "Biz bilan bog'laning",
    footerCopyright: "© 2025 ZOMIN. Barcha huquqlar himoyalangan.",
    profBadge: "SHAXSIY KABINET",
    profTitle: "Foydalanuvchi Profili",
    profNameLabel: "To'liq ism va familiya:",
    profPhoneLabel: "Telefon raqam:",
    profEmailLabel: "Elektron pochta (ixtiyoriy):",
    profCarLabel: "Avtomobil davlat raqami (Darvoza tekshiruvi uchun):",
    profTripsStat: "Bron qilingan safarlar",
    profSavedStat: "Saqlangan maskanlar",
    profSaveBtn: "O'zgarishlarni saqlash",
    profLogoutBtn: "Hisobdan chiqish",
    profSavedToast: "Profil ma'lumotlari muvaffaqiyatli saqlandi!",
    profLogoutToast: "Tizimdan chiqildi",
    profMenuProfile: "Mening profilim",
    profMenuTrips: "Mening safarlarim",
    profMenuSaved: "Saqlanganlar",
    profMenuHost: "Ega kabineti",
    profMenuCaretaker: "Bog'bon (Darvoza)",
    profMenuAdmin: "Boshqaruv Markazi (Admin)",
    mapAll: "Barchasi",
    mapDachas: "Dachalar",
    mapTapchans: "Tapchanlar",
    mapSights: "Diqqatga sazovor"
  },
  ru: {
    navStays: "Жилье",
    navDiscover: "Исследовать",
    navRoutes: "Маршруты",
    navPartner: "Стать партнером",
    navLogin: "Войти",
    heroTitle: "Откройте Заамин<br>по-своему.",
    heroSubtitle: "Горы, зоны отдыха и незабываемые путешествия — все в одном месте.",
    searchWhere: "Куда?",
    searchLocationDefault: "Заамин",
    searchCheckIn: "Заезд",
    searchCheckOut: "Выезд",
    searchSelectDate: "Выберите дату",
    searchGuests: "Гости",
    searchGuestsFormat: (n) => `${n} ${n === 1 ? 'гость' : (n < 5 ? 'гостя' : 'гостей')}`,
    searchBtn: "Поиск",
    tagRecommended: "РЕКОМЕНДУЕМЫЕ",
    titleStays: "Подходящие зоны отдыха",
    viewAll: "Смотреть все",
    currency: "сум",
    locationZaamin: "Заамин, Джизак",
    perNight: "/ ночь",
    perDay: "/ день",
    guestsCount: (n) => `${n} гостей`,
    cardChaletTitle: "Mountain Chalet Zomin",
    cardChaletDesc: "С видом на горы, деревянный коттедж. Идеально для семьи и друзей.",
    cardVillaTitle: "Zomin Villa",
    cardVillaDesc: "Частный бассейн, современные удобства и неповторимый пейзаж.",
    cardLodgeTitle: "Forest Lodge",
    cardLodgeDesc: "На лоне природы, спокойное и комфортное место отдыха.",
    tagDiscover: "ПРИРОДА И ПУТЕШЕСТВИЯ",
    titleDiscover: "Исследуйте Заамин",
    tagMap: "ИНТЕРАКТИВНАЯ КАРТА",
    titleMap: "Карта и маршруты Заамина",
    detailsBtn: "Подробнее",
    bridgeCat: "Популярное",
    bridgeTitle: "Подвесной мост Заамина",
    bridgeDesc: "Уникальный подвесной мост над каньоном — гармония смелости и природной красоты.",
    cableCat: "Активность",
    cableTitle: "Канатная дорога",
    cableDesc: "Насладитесь великолепными панорамными видами Заамина с высоты птичьего полета.",
    hikingCat: "Маршруты",
    hikingTitle: "Прогулки и пешие тропы",
    hikingDesc: "Незабываемые экологические маршруты в самом сердце горной природы.",
    footerTagline: "Природа. Отдых. Путешествия.",
    footerMain: "Главное",
    footerInfo: "Полезная информация",
    footerConnect: "Свяжитесь с нами",
    footerCopyright: "© 2025 ZOMIN. Все права защищены.",
    profBadge: "ЛИЧНЫЙ КАБИНЕТ",
    profTitle: "Профиль пользователя",
    profNameLabel: "Полное имя и фамилия:",
    profPhoneLabel: "Номер телефона:",
    profEmailLabel: "Электронная почта (необязательно):",
    profCarLabel: "Госномер автомобиля (для шлагбаума/пропуска):",
    profTripsStat: "Забронированные поездки",
    profSavedStat: "Сохраненные объекты",
    profSaveBtn: "Сохранить изменения",
    profLogoutBtn: "Выйти из аккаунта",
    profSavedToast: "Данные профиля успешно сохранены!",
    profLogoutToast: "Вы вышли из системы",
    profMenuProfile: "Мой профиль",
    profMenuTrips: "Мои поездки",
    profMenuSaved: "Избранное",
    profMenuHost: "Кабинет владельца",
    profMenuCaretaker: "Смотритель (Ворота)",
    profMenuAdmin: "Центр управления (Админ)",
    mapAll: "Все",
    mapDachas: "Дачи",
    mapTapchans: "Тапчаны",
    mapSights: "Достопримечательности"
  },
  en: {
    navStays: "Stays",
    navDiscover: "Discover",
    navRoutes: "Routes",
    navPartner: "Become a Host",
    navLogin: "Sign In",
    heroTitle: "Discover Zaamin<br>in your own way.",
    heroSubtitle: "Mountains, retreats, and unforgettable journeys — all in one place.",
    searchWhere: "Where to?",
    searchLocationDefault: "Zaamin",
    searchCheckIn: "Check-in",
    searchCheckOut: "Check-out",
    searchSelectDate: "Select date",
    searchGuests: "Guests",
    searchGuestsFormat: (n) => `${n} ${n === 1 ? 'guest' : 'guests'}`,
    searchBtn: "Search",
    tagRecommended: "RECOMMENDED",
    titleStays: "Places to stay tailored for you",
    viewAll: "View all",
    currency: "UZS",
    locationZaamin: "Zaamin, Jizzakh",
    perNight: "/ night",
    perDay: "/ day",
    guestsCount: (n) => `${n} guests`,
    cardChaletTitle: "Mountain Chalet Zomin",
    cardChaletDesc: "Mountain view, wooden chalet. Ideal for family and friends.",
    cardVillaTitle: "Zomin Villa",
    cardVillaDesc: "Private pool, modern amenities and breathtaking scenery.",
    cardLodgeTitle: "Forest Lodge",
    cardLodgeDesc: "In the heart of nature, peaceful and cozy retreat.",
    tagDiscover: "NATURE & TRAVEL",
    titleDiscover: "Discover Zaamin",
    tagMap: "INTERACTIVE MAP",
    titleMap: "Zaamin Mountain Map & Trails",
    detailsBtn: "Details",
    bridgeCat: "Must Visit",
    bridgeTitle: "Zaamin Suspension Bridge",
    bridgeDesc: "A breathtaking suspension bridge spanning the canyon — a harmony of courage and beauty.",
    cableCat: "Activity",
    cableTitle: "Cable Car",
    cableDesc: "Marvel at Zaamin's magnificent panoramic mountain views from high above.",
    hikingCat: "Trails",
    hikingTitle: "Hiking & Walking Trails",
    hikingDesc: "Unforgettable hiking journeys through pristine pine forests and alpine peaks.",
    footerTagline: "Nature. Retreat. Travel.",
    footerMain: "Navigation",
    footerInfo: "Helpful Info",
    footerConnect: "Connect With Us",
    footerCopyright: "© 2025 ZOMIN. All rights reserved.",
    profBadge: "PERSONAL ACCOUNT",
    profTitle: "User Profile",
    profNameLabel: "Full Name:",
    profPhoneLabel: "Phone Number:",
    profEmailLabel: "Email address (optional):",
    profCarLabel: "Vehicle License Plate (For gate pass):",
    profTripsStat: "Booked Trips",
    profSavedStat: "Saved Places",
    profSaveBtn: "Save Changes",
    profLogoutBtn: "Log out",
    profSavedToast: "Profile updated successfully!",
    profLogoutToast: "Logged out successfully",
    profMenuProfile: "My Profile",
    profMenuTrips: "My Trips",
    profMenuSaved: "Saved Places",
    profMenuHost: "Host Dashboard",
    profMenuCaretaker: "Caretaker (Gate)",
    profMenuAdmin: "Control Center (Admin)",
    mapAll: "All",
    mapDachas: "Stays",
    mapTapchans: "Tapchans",
    mapSights: "Attractions"
  }
};

// Google Auth User Profiles
const GOOGLE_PROFILES = {
  umurzoq: {
    id: "usr-google-umurzoq",
    name: "Umurzoq",
    email: "umurzoq972@gmail.com",
    avatar: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='128' height='128' viewBox='0 0 128 128'><circle cx='64' cy='64' r='64' fill='%231a73e8'/><text x='50%' y='55%' font-family='-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif' font-weight='600' font-size='56' fill='%23ffffff' text-anchor='middle' dominant-baseline='middle'>U</text></svg>",
    phone: "+998 91 593 30 18",
    car_plate: "01 A 777 AA",
    role: "GUEST"
  },
  school21: {
    id: "usr-google-school21",
    name: "Umrzoq Yulchiyev",
    email: "school21dev@gmail.com",
    avatar: "/static/assets/avatar.jpg",
    phone: "+998 91 593 30 18",
    car_plate: "01 A 777 AA",
    role: "GUEST"
  },
  alisher: {
    id: "usr-google-alisher",
    name: "Alisher Zokirov",
    email: "alisher.zomin@gmail.com",
    avatar: "/static/assets/avatar2.jpg",
    phone: "+998 90 111 22 33",
    car_plate: "25 B 888 BB",
    role: "OWNER"
  }
};

// Generate high-resolution user avatar for any Google user
function generateUserAvatar(name, email) {
  if (email === 'school21dev@gmail.com' || email === 'umrzoq.backend@gmail.com') {
    return '/static/assets/avatar.jpg';
  }
  if (email === 'alisher.zomin@gmail.com') {
    return '/static/assets/avatar2.jpg';
  }
  if (email === 'umurzoq972@gmail.com') {
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='128' height='128' viewBox='0 0 128 128'><circle cx='64' cy='64' r='64' fill='%231a73e8'/><text x='50%' y='55%' font-family='-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif' font-weight='600' font-size='56' fill='%23ffffff' text-anchor='middle' dominant-baseline='middle'>U</text></svg>";
  }
  const initial = (name || email || 'U').charAt(0).toUpperCase();
  const colors = ['#1a73e8', '#0d9488', '#e11d48', '#7c3aed', '#d97706', '#2563eb', '#059669'];
  const color = colors[initial.charCodeAt(0) % colors.length];
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><circle cx='64' cy='64' r='64' fill='${color}'/><text x='50%' y='55%' font-family='-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif' font-weight='600' font-size='56' fill='%23ffffff' text-anchor='middle' dominant-baseline='middle'>${initial}</text></svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

// Demo User Profiles
const DEMO_PROFILES = {
  guest: GOOGLE_PROFILES.umurzoq,
  owner1: GOOGLE_PROFILES.alisher,
  caretaker: { id: "usr-caretaker-rustam", phone: '+998917778899', name: 'Rustam Tog\'a', role: 'CARETAKER', avatar: '/static/assets/avatar2.jpg' },
  admin: { id: "usr-admin-sanjar", phone: '+998900000001', name: 'Sanjar Karimov', role: 'ADMIN', avatar: '/static/assets/avatar.jpg' }
};

let currentUser = null;

// Toast Helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ')}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Format Currency
function formatSum(num) {
  if (num === null || num === undefined) return '0';
  return Math.round(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

// Initialize on DOM load
window.addEventListener('DOMContentLoaded', async () => {
  // Load saved user if any
  const savedUser = localStorage.getItem('zomin_user');
  if (savedUser) {
    try {
      currentUser = JSON.parse(savedUser);
      if (currentUser && !currentUser.avatar) {
        currentUser.avatar = generateUserAvatar(currentUser.name, currentUser.email);
      }
    } catch (e) {
      currentUser = null;
    }
  } else {
    currentUser = null; // Clean unauthenticated state by default!
  }

  // Apply saved language
  applyLanguage(currentLang);

  // Set default dates
  initDefaultDates();

  // Load properties
  await loadProperties();

  // Initialize Map
  initLeafletMap();

  // Update header auth state
  updateHeaderAuthState();

  // Setup click listeners for closing popups
  document.addEventListener('click', (e) => {
    // Close location dropdown if clicked outside
    const locDropdown = document.getElementById('dropdown-locations');
    const locSegment = document.querySelector('.segment-location');
    if (locDropdown && locSegment && !locSegment.contains(e.target)) {
      locDropdown.classList.add('hidden');
    }

    // Close calendar dropdown if clicked outside
    const calDropdown = document.getElementById('dropdown-calendar');
    const calSegments = document.querySelectorAll('.segment-date');
    let insideDateSegment = false;
    calSegments.forEach(seg => {
      if (seg.contains(e.target)) insideDateSegment = true;
    });
    if (calDropdown && !insideDateSegment && !calDropdown.contains(e.target)) {
      calDropdown.classList.add('hidden');
    }

    // Close guests dropdown if clicked outside
    const guestsDropdown = document.getElementById('dropdown-guests');
    const guestsSegment = document.querySelector('.segment-guests');
    if (guestsDropdown && guestsSegment && !guestsSegment.contains(e.target)) {
      guestsDropdown.classList.add('hidden');
    }

    // Close lang menu if clicked outside
    const langMenu = document.getElementById('lang-dropdown-menu');
    const langBtn = document.getElementById('lang-btn');
    if (langMenu && langBtn && !langBtn.contains(e.target)) {
      langMenu.classList.add('hidden');
    }

    // Close user menu if clicked outside
    const profileMenu = document.getElementById('profile-dropdown-menu');
    const kirishBtn = document.getElementById('header-kirish-btn');
    if (profileMenu && kirishBtn && !kirishBtn.contains(e.target) && !profileMenu.contains(e.target)) {
      profileMenu.classList.add('hidden');
    }
  });

  // Check URL route for /admin
  if (window.location.pathname === '/admin' || window.location.hash === '#admin') {
    showAdminPortal();
  }
});

// ===================================================================
// MULTILINGUAL TRANSLATION ENGINE (UZ, RU, EN)
// ===================================================================
function toggleLangMenu(e) {
  e.stopPropagation();
  const menu = document.getElementById('lang-dropdown-menu');
  if (menu) menu.classList.toggle('hidden');
}

function switchLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('zomin_lang', lang);
  document.getElementById('lang-dropdown-menu').classList.add('hidden');
  applyLanguage(lang);
  renderProperties();
  showToast(lang === 'uz' ? "Til o'zgartirildi: O'zbekcha" : (lang === 'ru' ? "Язык переключен: Русский" : "Language switched: English"), 'success');
}

function applyLanguage(lang) {
  const t = I18N[lang] || I18N.uz;

  // Header
  document.getElementById('current-lang-code').innerText = lang.toUpperCase();
  const footerLang = document.getElementById('footer-lang-name');
  if (footerLang) footerLang.innerText = lang.toUpperCase();
  const navStays = document.getElementById('nav-link-stays-text');
  if (navStays) navStays.innerText = t.navStays;
  document.getElementById('nav-link-discover').innerText = t.navDiscover;
  document.getElementById('nav-link-routes').innerText = t.navRoutes;
  document.getElementById('nav-link-partner').innerText = t.navPartner;
  
  updateHeaderAuthState();

  // Hero
  document.getElementById('hero-title').innerHTML = t.heroTitle;
  document.getElementById('hero-subtitle').innerText = t.heroSubtitle;

  // Search Bar
  document.getElementById('lbl-search-where').innerText = t.searchWhere;
  if (searchSelectedDistrict === 'ALL') {
    document.getElementById('search-val-district').innerText = t.searchLocationDefault;
  }
  document.getElementById('lbl-search-checkin').innerText = t.searchCheckIn;
  document.getElementById('lbl-search-checkout').innerText = t.searchCheckOut;
  if (!searchCheckInDate) {
    const el = document.getElementById('search-val-checkin');
    if (el) el.innerText = t.searchSelectDate;
  }
  if (!searchCheckOutDate) {
    const el = document.getElementById('search-val-checkout');
    if (el) el.innerText = t.searchSelectDate;
  }
  document.getElementById('lbl-search-guests').innerText = t.searchGuests;
  document.getElementById('search-val-guests').innerText = t.searchGuestsFormat(guestsAdults + guestsChildren);
  document.getElementById('lbl-search-btn').innerText = t.searchBtn;

  // Sections
  document.getElementById('tag-recommended').innerText = t.tagRecommended;
  document.getElementById('title-stays').innerText = t.titleStays;
  document.getElementById('lbl-view-all-stays').innerText = t.viewAll;

  document.getElementById('tag-discover').innerText = t.tagDiscover;
  document.getElementById('title-discover').innerText = t.titleDiscover;
  document.getElementById('lbl-view-all-discover').innerText = t.viewAll;

  document.getElementById('tag-map').innerText = t.tagMap;
  document.getElementById('title-map').innerText = t.titleMap;

  // Map Filter Chips
  const cAll = document.getElementById('chip-map-all');
  if (cAll) cAll.innerText = t.mapAll;
  const cDachas = document.getElementById('chip-map-dachas');
  if (cDachas) cDachas.innerText = t.mapDachas;
  const cTapchans = document.getElementById('chip-map-tapchans');
  if (cTapchans) cTapchans.innerText = t.mapTapchans;
  const cSights = document.getElementById('chip-map-sights');
  if (cSights) cSights.innerText = t.mapSights;

  // Attractions
  document.getElementById('cat-attr-bridge').innerText = t.bridgeCat;
  document.getElementById('title-attr-bridge').innerText = t.bridgeTitle;
  document.getElementById('desc-attr-bridge').innerText = t.bridgeDesc;
  document.getElementById('btn-attr-bridge').innerText = t.detailsBtn;

  document.getElementById('cat-attr-cablecar').innerText = t.cableCat;
  document.getElementById('title-attr-cablecar').innerText = t.cableTitle;
  document.getElementById('desc-attr-cablecar').innerText = t.cableDesc;
  document.getElementById('btn-attr-cablecar').innerText = t.detailsBtn;

  document.getElementById('cat-attr-hiking').innerText = t.hikingCat;
  document.getElementById('title-attr-hiking').innerText = t.hikingTitle;
  document.getElementById('desc-attr-hiking').innerText = t.hikingDesc;
  document.getElementById('btn-attr-hiking').innerText = t.detailsBtn;

  // Footer
  document.getElementById('footer-tagline').innerText = t.footerTagline;
  document.getElementById('footer-col-main').innerText = t.footerMain;
  document.getElementById('footer-col-info').innerText = t.footerInfo;
  document.getElementById('footer-col-connect').innerText = t.footerConnect;
  document.getElementById('footer-copyright').innerText = t.footerCopyright;

  // Profile Dropdown Menu Labels
  const mProf = document.getElementById('lbl-menu-profile');
  if (mProf) mProf.innerText = t.profMenuProfile;
  const mTrips = document.getElementById('lbl-menu-trips');
  if (mTrips) mTrips.innerText = t.profMenuTrips;
  const mSaved = document.getElementById('lbl-menu-saved');
  if (mSaved) mSaved.innerText = t.profMenuSaved;
  const mHost = document.getElementById('lbl-menu-owner');
  if (mHost) mHost.innerText = t.profMenuHost;
  const mCaretaker = document.getElementById('lbl-menu-caretaker');
  if (mCaretaker) mCaretaker.innerText = t.profMenuCaretaker;
  const mAdmin = document.getElementById('lbl-menu-admin');
  if (mAdmin) mAdmin.innerText = t.profMenuAdmin;
  const mSwitch = document.getElementById('lbl-menu-switch');
  if (mSwitch) mSwitch.innerText = t.profLogoutBtn;

  // Profile Modal Elements
  const pBadge = document.getElementById('prof-modal-badge');
  if (pBadge) pBadge.innerText = t.profBadge;
  const pTitle = document.getElementById('prof-modal-title');
  if (pTitle) pTitle.innerText = t.profTitle;
  const pNameLbl = document.getElementById('lbl-prof-fullname');
  if (pNameLbl) pNameLbl.innerText = t.profNameLabel;
  const pPhoneLbl = document.getElementById('lbl-prof-phone');
  if (pPhoneLbl) pPhoneLbl.innerText = t.profPhoneLabel;
  const pEmailLbl = document.getElementById('lbl-prof-email');
  if (pEmailLbl) pEmailLbl.innerText = t.profEmailLabel;
  const pCarLbl = document.getElementById('lbl-prof-car');
  if (pCarLbl) pCarLbl.innerText = t.profCarLabel;
  const pTripsStat = document.getElementById('lbl-prof-stat-trips');
  if (pTripsStat) pTripsStat.innerText = t.profTripsStat;
  const pSavedStat = document.getElementById('lbl-prof-stat-saved');
  if (pSavedStat) pSavedStat.innerText = t.profSavedStat;
  const pSaveBtn = document.getElementById('lbl-prof-save');
  if (pSaveBtn) pSaveBtn.innerText = t.profSaveBtn;
  const pLogoutBtn = document.getElementById('lbl-prof-logout');
  if (pLogoutBtn) pLogoutBtn.innerText = t.profLogoutBtn;

  // Highlight active lang in dropdown
  document.querySelectorAll('.lang-option-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('onclick').includes(lang));
  });
}

// ===================================================================
// FLOATING SEARCH BAR CONTROLS
// ===================================================================
function closeAllSearchDropdowns() {
  const locDropdown = document.getElementById('dropdown-locations');
  if (locDropdown) locDropdown.classList.add('hidden');

  const calDropdown = document.getElementById('dropdown-calendar');
  if (calDropdown) calDropdown.classList.add('hidden');

  const guestsDropdown = document.getElementById('dropdown-guests');
  if (guestsDropdown) guestsDropdown.classList.add('hidden');

  const langMenu = document.getElementById('lang-dropdown-menu');
  if (langMenu) langMenu.classList.add('hidden');

  const profileMenu = document.getElementById('profile-dropdown-menu');
  if (profileMenu) profileMenu.classList.add('hidden');
}

// ===================================================================
// IN-PAGE CUSTOM LUXURY CALENDAR
// ===================================================================
let currentCalYear = new Date().getFullYear();
let currentCalMonth = new Date().getMonth();
let calendarSelectingType = 'checkin';

const MONTH_NAMES_UZ = [
  'Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun',
  'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr'
];
const MONTH_NAMES_RU = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];
const MONTH_NAMES_EN = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

function openCalendarPicker(type, event) {
  if (event) event.stopPropagation();
  calendarSelectingType = type || 'checkin';

  const cal = document.getElementById('dropdown-calendar');
  if (!cal) return;

  const isAlreadyOpen = !cal.classList.contains('hidden') && cal.dataset.openFor === type;

  closeAllSearchDropdowns();

  if (!isAlreadyOpen) {
    cal.dataset.openFor = type;
    cal.classList.remove('hidden');

    // Align calendar under the clicked date segment
    const targetSeg = type === 'checkin' ? document.getElementById('segment-checkin') : document.getElementById('segment-checkout');
    if (targetSeg) {
      const parentCard = targetSeg.closest('.floating-search-card');
      if (parentCard) {
        const parentRect = parentCard.getBoundingClientRect();
        const segRect = targetSeg.getBoundingClientRect();
        const offsetLeft = segRect.left - parentRect.left;
        const maxLeft = parentRect.width - 340;
        cal.style.left = `${Math.max(10, Math.min(offsetLeft - 20, maxLeft))}px`;
      }
    }

    renderCalendarGrid();
  }
}

function renderCalendarGrid() {
  const titleEl = document.getElementById('cal-month-title');
  const gridEl = document.getElementById('cal-days-grid');
  const hintEl = document.getElementById('cal-selected-hint');
  if (!gridEl) return;

  const monthNames = currentLang === 'ru' ? MONTH_NAMES_RU : (currentLang === 'en' ? MONTH_NAMES_EN : MONTH_NAMES_UZ);
  if (titleEl) {
    titleEl.innerText = `${monthNames[currentCalMonth]} ${currentCalYear}`;
  }

  if (hintEl) {
    if (calendarSelectingType === 'checkin') {
      hintEl.innerText = currentLang === 'uz' ? 'Kelish sanasini tanlang' : (currentLang === 'ru' ? 'Выберите дату заезда' : 'Select check-in date');
    } else {
      hintEl.innerText = currentLang === 'uz' ? 'Ketish sanasini tanlang' : (currentLang === 'ru' ? 'Выберите дату выезда' : 'Select check-out date');
    }
  }

  gridEl.innerHTML = '';

  const firstDay = new Date(currentCalYear, currentCalMonth, 1).getDay();
  const startOffset = firstDay === 0 ? 6 : firstDay - 1;
  const daysInMonth = new Date(currentCalYear, currentCalMonth + 1, 0).getDate();
  const prevMonthDays = new Date(currentCalYear, currentCalMonth, 0).getDate();

  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

  // Trailing days of previous month
  for (let i = startOffset - 1; i >= 0; i--) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'cal-day-btn disabled other-month';
    btn.innerText = prevMonthDays - i;
    btn.disabled = true;
    gridEl.appendChild(btn);
  }

  // Active month days
  for (let day = 1; day <= daysInMonth; day++) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'cal-day-btn';
    btn.innerText = day;

    const dateStr = `${currentCalYear}-${String(currentCalMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

    if (dateStr < todayStr) {
      btn.classList.add('disabled');
      btn.disabled = true;
    }

    if (dateStr === todayStr) {
      btn.classList.add('today');
    }

    if (dateStr === searchCheckInDate) {
      btn.classList.add('selected');
    } else if (dateStr === searchCheckOutDate) {
      btn.classList.add('selected');
    } else if (searchCheckInDate && searchCheckOutDate && dateStr > searchCheckInDate && dateStr < searchCheckOutDate) {
      btn.classList.add('in-range');
    }

    btn.onclick = (e) => {
      e.stopPropagation();
      selectCalendarDate(currentCalYear, currentCalMonth, day);
    };

    gridEl.appendChild(btn);
  }
}

function selectCalendarDate(year, month, day) {
  const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  const displayStr = `${String(day).padStart(2, '0')}/${String(month + 1).padStart(2, '0')}`;

  if (calendarSelectingType === 'checkin') {
    searchCheckInDate = dateStr;
    const checkinEl = document.getElementById('search-val-checkin');
    if (checkinEl) checkinEl.innerText = displayStr;

    if (searchCheckOutDate && searchCheckOutDate <= searchCheckInDate) {
      searchCheckOutDate = '';
      const checkoutEl = document.getElementById('search-val-checkout');
      if (checkoutEl) checkoutEl.innerText = currentLang === 'uz' ? 'Sanani tanlang' : (currentLang === 'ru' ? 'Выберите дату' : 'Select date');
    }

    calendarSelectingType = 'checkout';
    const cal = document.getElementById('dropdown-calendar');
    if (cal) cal.dataset.openFor = 'checkout';
    renderCalendarGrid();
  } else {
    if (searchCheckInDate && dateStr <= searchCheckInDate) {
      showToast(currentLang === 'uz' ? 'Ketish sanasi kelish sanasidan keyin bo‘lishi kerak' : 'Дата выезда должна быть позже даты заезда', 'error');
      return;
    }
    searchCheckOutDate = dateStr;
    const checkoutEl = document.getElementById('search-val-checkout');
    if (checkoutEl) checkoutEl.innerText = displayStr;

    const cal = document.getElementById('dropdown-calendar');
    if (cal) cal.classList.add('hidden');
    renderProperties();
    showToast(currentLang === 'uz' ? `Sanalar belgilandi: ${searchCheckInDate} — ${searchCheckOutDate}` : `Даты выбраны: ${searchCheckInDate} — ${searchCheckOutDate}`, 'success');
  }
}

function prevCalendarMonth(e) {
  if (e) e.stopPropagation();
  currentCalMonth--;
  if (currentCalMonth < 0) {
    currentCalMonth = 11;
    currentCalYear--;
  }
  renderCalendarGrid();
}

function nextCalendarMonth(e) {
  if (e) e.stopPropagation();
  currentCalMonth++;
  if (currentCalMonth > 11) {
    currentCalMonth = 0;
    currentCalYear++;
  }
  renderCalendarGrid();
}

function clearSelectedDates(e) {
  if (e) e.stopPropagation();
  searchCheckInDate = '';
  searchCheckOutDate = '';
  const checkinEl = document.getElementById('search-val-checkin');
  const checkoutEl = document.getElementById('search-val-checkout');
  const t = I18N[currentLang] || I18N.uz;
  if (checkinEl) checkinEl.innerText = t.searchSelectDate;
  if (checkoutEl) checkoutEl.innerText = t.searchSelectDate;
  calendarSelectingType = 'checkin';
  renderCalendarGrid();
}

function toggleLocationDropdown(e) {
  e.stopPropagation();
  const dropdown = document.getElementById('dropdown-locations');
  const isCurrentlyOpen = dropdown && !dropdown.classList.contains('hidden');
  closeAllSearchDropdowns();
  if (dropdown && !isCurrentlyOpen) {
    dropdown.classList.remove('hidden');
  }
}

function selectSearchLocation(districtCode, displayName) {
  searchSelectedDistrict = districtCode;
  document.getElementById('search-val-district').innerText = displayName;
  const dropdown = document.getElementById('dropdown-locations');
  if (dropdown) dropdown.classList.add('hidden');
  renderProperties();
}

function handleDateSelect(type, val) {
  if (!val) return;
  const parts = val.split('-');
  const dateFormatted = `${parts[2]}/${parts[1]}`;
  if (type === 'checkin') {
    searchCheckInDate = val;
    const el = document.getElementById('search-val-checkin');
    if (el) el.innerText = dateFormatted;
  } else {
    searchCheckOutDate = val;
    const el = document.getElementById('search-val-checkout');
    if (el) el.innerText = dateFormatted;
  }
  closeAllSearchDropdowns();
}

function toggleGuestsDropdown(e) {
  e.stopPropagation();
  const dropdown = document.getElementById('dropdown-guests');
  const isCurrentlyOpen = dropdown && !dropdown.classList.contains('hidden');
  closeAllSearchDropdowns();
  if (dropdown && !isCurrentlyOpen) {
    dropdown.classList.remove('hidden');
  }
}

function adjustGuests(type, delta) {
  if (type === 'adults') {
    guestsAdults = Math.max(1, guestsAdults + delta);
    document.getElementById('stepper-adults').innerText = guestsAdults;
  } else {
    guestsChildren = Math.max(0, guestsChildren + delta);
    document.getElementById('stepper-children').innerText = guestsChildren;
  }
  const total = guestsAdults + guestsChildren;
  const t = I18N[currentLang] || I18N.uz;
  document.getElementById('search-val-guests').innerText = t.searchGuestsFormat(total);
}

function executeHeroSearch() {
  renderProperties();
  scrollToSection('stays-section');
  showToast(currentLang === 'uz' ? 'Qidiruv yangilandi' : (currentLang === 'ru' ? 'Поиск обновлен' : 'Search updated'), 'success');
}

function initDefaultDates() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dayAfter = new Date(tomorrow);
  dayAfter.setDate(dayAfter.getDate() + 2);

  const fmt = (d) => d.toISOString().split('T')[0];
  const checkinVal = fmt(tomorrow);
  const checkoutVal = fmt(dayAfter);

  searchCheckInDate = '';
  searchCheckOutDate = '';

  const nIn = document.getElementById('native-checkin-date');
  const nOut = document.getElementById('native-checkout-date');
  if (nIn) { nIn.value = ''; nIn.min = fmt(new Date()); }
  if (nOut) { nOut.value = ''; nOut.min = checkinVal; }

  const mStart = document.getElementById('modal-start-date');
  const mEnd = document.getElementById('modal-end-date');
  if (mStart) mStart.value = checkinVal;
  if (mEnd) mEnd.value = checkoutVal;
}

// ===================================================================
// PROPERTIES RENDERING (Matches Image 1 Master Reference & Bronla)
// ===================================================================
async function loadProperties() {
  try {
    const res = await fetch('/api/v1/properties');
    if (!res.ok) throw new Error('Failed to fetch');
    propertiesCache = await res.json();
    renderProperties();
  } catch (err) {
    console.error('Error loading properties:', err);
    // Use high-fidelity local defaults if server reload happens
    propertiesCache = [
      {
        id: "prop-shox",
        title: "Shox_dacha",
        slug: "shox-dacha-zomin",
        description: "O'riklisoyning betakror manzarasi qo'ynida, Tog' Terak qishlog'ida joylashgan premium darajadagi dacha. Shaxsiy filtrli basseyn (3.5x7.5m), Playstation 3, karaoke, bilyard, stol tennisi, yozgi va qishki oshxona.",
        micro_district: "ORIKLISOY",
        address_text: "Uriklisoy, Zomin tumani · Tog' Terak qishlog'i 31",
        photos: [
          "/static/assets/shox_pool.jpg",
          "/static/assets/shox_kitchen.jpg",
          "/static/assets/shox_bath.jpg",
          "/static/assets/shox_bedroom1.jpg",
          "/static/assets/shox_bedroom2.jpg"
        ],
        amenities: [
          "Filtrli Hovuz (3.5x7.5m)", "Playstation 3 & Karaoke", "Bilyard & Stol tennisi", 
          "Wi-Fi 5G", "Ochiq oshxona & Mangal", "Archa tandiri", "Konditsioner", "Muzlatgich & Mikroto'lqinli pech"
        ],
        min_price: 1400000,
        rating: 4.95,
        reviews_count: 54,
        guests: 12
      },
      {
        id: "prop-chashma",
        title: "Chashma Eco Dacha",
        slug: "chashma-eco-dacha",
        description: "Tog' daryosi va musaffo chashma suvi yoqasida joylashgan zamonaviy eko-dacha. Keng ayvon, hovuz, barbekyu hududi va archazor havosi.",
        micro_district: "ORIKLISOY",
        address_text: "Chashma qishlog'i, Buloqboshi, Zomin",
        photos: ["/static/assets/dacha_chashma.jpg", "/static/assets/chalet.jpg"],
        amenities: ["Chashma bo'yida shiypon", "Basseyn", "Karaoke & Smart TV", "Wi-Fi 5G", "Barbekyu hududi", "Qozon-o'choq"],
        min_price: 1600000,
        rating: 4.88,
        reviews_count: 42,
        guests: 10
      },
      {
        id: "prop-panorama",
        title: "Suffa Panorama Kottej",
        slug: "suffa-panorama-kottej",
        description: "Suffa platosining 2400 metr balandlikdagi panoramali manzarasi. Panoramik derazalar, yulduzli tunlar, kamin va to'liq avtonom isitish.",
        micro_district: "SUFFA",
        address_text: "Suffa platosi, Radioastronomiya observatoriyasi yo'li, Zomin",
        photos: ["/static/assets/dacha_panorama.jpg", "/static/assets/villa.jpg"],
        amenities: ["360° Panorama", "Issiq pol & Kamin", "Yulduzlar kuzatuvi terassasi", "Wi-Fi 5G", "Avtomat generator", "Tandir go'shti"],
        min_price: 1800000,
        rating: 4.92,
        reviews_count: 65,
        guests: 8
      },
      {
        id: "prop-1",
        title: "Mountain Chalet Zomin",
        slug: "mountain-chalet-zomin",
        description: "Tog‘ manzarali, yog‘och uy. Oila va do‘stlar uchun ideal.",
        micro_district: "SUFFA",
        address_text: "Suffa platosi, Dor yo'li yaqinida, Zomin",
        photos: ["/static/assets/chalet.jpg", "/static/assets/dacha_panorama.jpg"],
        amenities: ["Tog' manzarasi", "Kamin", "Balkon/Ayvon", "Wi-Fi 5G", "Oila uchun shinam", "Mangal"],
        min_price: 1200000,
        rating: 4.8,
        reviews_count: 124,
        guests: 6
      },
      {
        id: "prop-2",
        title: "Zomin Villa",
        slug: "zomin-villa",
        description: "Shaxsiy hovuz, zamonaviy qulayliklar va betakror manzara.",
        micro_district: "DUOBA",
        address_text: "Duoba MFY, Soy bo'yi ko'chasi 14-uy, Zomin",
        photos: ["/static/assets/villa.jpg", "/static/assets/dacha_chashma.jpg"],
        amenities: ["Shaxsiy hovuz (Basseyn)", "Sauna", "Bilyard", "Smart TV", "Tandir & Mangal", "Wi-Fi 4G"],
        min_price: 2500000,
        rating: 4.9,
        reviews_count: 98,
        guests: 10
      },
      {
        id: "prop-3",
        title: "Forest Lodge",
        slug: "forest-lodge",
        description: "Tabiat bag‘rida, sokin va qulay dam olish maskani.",
        micro_district: "SANATORIY",
        address_text: "Sanatoriy ko'chasi 8-uy, Zomin",
        photos: ["/static/assets/lodge.jpg", "/static/assets/hiking.jpg"],
        amenities: ["Qarag'ayzor", "Oshxona barcha jihozlar bilan", "Wi-Fi", "Buloq suvi", "Tinch hordiq"],
        min_price: 900000,
        rating: 4.7,
        reviews_count: 76,
        guests: 4
      },
      {
        id: "prop-4",
        title: "O'riklisoy Buloq Bo'yi Choyxonasi & Tapchanlari",
        slug: "oriklisoy-buloq-boyi-tapchanlar",
        description: "O'riklisoyning salqin tog' suvlari ustida qurilgan milliy tapchanlar majmuasi. Kunduzgi hordiq, oilaviy dam olish, archa tandiri.",
        micro_district: "ORIKLISOY",
        address_text: "O'riklisoy dam olish hududi, Buloqboshi, Zomin",
        photos: ["/static/assets/hiking.jpg", "/static/assets/shox_pool.jpg"],
        amenities: ["Suv ustidagi tapchan", "Zomin archa tandiri", "Samovar choy", "Buloq suvi", "Soyda suzish"],
        min_price: 150000,
        rating: 4.85,
        reviews_count: 112,
        guests: 12
      }
    ];
    renderProperties();
  }
}

function renderProperties() {
  const grid = document.getElementById('properties-grid');
  if (!grid) return;

  const t = I18N[currentLang] || I18N.uz;

  let filtered = propertiesCache.filter(p => {
    if (searchSelectedDistrict !== 'ALL' && p.micro_district !== searchSelectedDistrict) {
      return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    filtered = propertiesCache;
  }

  // Display ALL cards without truncation
  const displayItems = filtered;

  grid.innerHTML = displayItems.map(p => {
    // Photo selection
    let photoUrl = '/static/assets/chalet.jpg';
    if (p.photos && p.photos.length > 0) {
      photoUrl = p.photos[0];
    } else if (p.slug.includes('shox')) {
      photoUrl = '/static/assets/shox_pool.jpg';
    } else if (p.slug.includes('chashma')) {
      photoUrl = '/static/assets/dacha_chashma.jpg';
    } else if (p.slug.includes('panorama')) {
      photoUrl = '/static/assets/dacha_panorama.jpg';
    } else if (p.slug.includes('villa')) {
      photoUrl = '/static/assets/villa.jpg';
    } else if (p.slug.includes('lodge')) {
      photoUrl = '/static/assets/lodge.jpg';
    }

    // Wishlist state
    const isFav = wishlistItems.has(p.slug);
    const favSvg = isFav 
      ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="#ef4444" stroke="#ef4444" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`
      : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`;

    // Capacity & Price
    const guests = p.guests || (p.rental_units && p.rental_units[0] ? p.rental_units[0].standard_capacity : 8);
    const price = p.min_price || 1200000;
    const rating = p.rating || (p.slug.includes('shox') ? 4.95 : (p.slug.includes('villa') ? 4.9 : (p.slug.includes('panorama') ? 4.92 : 4.8)));
    const reviews = p.reviews_count || (p.slug.includes('shox') ? 54 : (p.slug.includes('villa') ? 98 : (p.slug.includes('panorama') ? 65 : 124)));

    let cardTitle = p.title;
    let cardDesc = p.description;

    let districtText = "Zomin, Jizzax";
    if (p.micro_district === 'ORIKLISOY') districtText = "O'riklisoy, Zomin";
    else if (p.micro_district === 'SUFFA') districtText = "Suffa platosi, Zomin";
    else if (p.micro_district === 'DUOBA') districtText = "Duoba, Zomin";
    else if (p.micro_district === 'SANATORIY') districtText = "Sanatoriy, Zomin";

    return `
      <div class="property-card" onclick="openBookingModal('${p.id}')">
        <div class="property-image-container">
          <img src="${photoUrl}" alt="${cardTitle}" class="property-image" loading="lazy">
          <button class="property-wishlist-btn ${isFav ? 'active' : ''}" onclick="event.stopPropagation(); toggleWishlist('${p.slug}', this);" title="Save">
            ${favSvg}
          </button>
        </div>

        <div class="property-card-body">
          <div class="property-location-line">
            <svg class="location-pin-svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
            <span>${districtText}</span>
          </div>

          <h3 class="property-card-title">${cardTitle}</h3>
          <p class="property-card-desc">${cardDesc}</p>

          <div class="property-card-footer">
            <div class="footer-left-meta">
              <span class="meta-guests">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                ${t.guestsCount(guests)}
              </span>
              <span class="meta-rating">
                <span class="star-icon">★</span> ${rating} (${reviews})
              </span>
            </div>
            <div class="footer-price-block">
              <span class="price-main">${formatSum(price)} ${t.currency}</span>
              <span class="price-period">${p.property_type === 'CHOYXONA_TAPCHAN' ? t.perDay : t.perNight}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function toggleWishlist(slug, btn) {
  if (wishlistItems.has(slug)) {
    wishlistItems.delete(slug);
    btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`;
    btn.classList.remove('active');
  } else {
    wishlistItems.add(slug);
    btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="#ef4444" stroke="#ef4444" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`;
    btn.classList.add('active');
  }
}

function clearAllFilters() {
  searchSelectedDistrict = 'ALL';
  const t = I18N[currentLang] || I18N.uz;
  document.getElementById('search-val-district').innerText = t.searchLocationDefault;
  renderProperties();
}

// ===================================================================
// AUTH & PROFILE LOGIC
// ===================================================================
function handleAuthButtonClick() {
  if (!currentUser) {
    openAuthModal();
  } else {
    const menu = document.getElementById('profile-dropdown-menu');
    menu.classList.toggle('hidden');
  }
}

function openAuthModal() {
  document.getElementById('auth-modal').classList.remove('hidden');
  const pMenu = document.getElementById('profile-dropdown-menu');
  if (pMenu) pMenu.classList.add('hidden');
}

function closeAuthModal() {
  document.getElementById('auth-modal').classList.add('hidden');
}

function openProfileModal() {
  if (!currentUser) {
    openAuthModal();
    return;
  }
  const p = currentUser;

  const nameVal = p.name || p.full_name || 'Umurzoq';
  const phoneVal = p.phone || p.phone_number || '+998 91 593 30 18';
  const emailVal = p.email || 'umurzoq972@gmail.com';
  const carVal = p.car_plate || '01 A 777 AA';
  const roleVal = p.role || 'GUEST';
  const avatarVal = p.avatar || generateUserAvatar(nameVal, emailVal);

  const profImg = document.getElementById('prof-avatar-img');
  if (profImg) profImg.src = avatarVal;

  const dName = document.getElementById('prof-display-name');
  if (dName) dName.innerText = nameVal;

  const dRole = document.getElementById('prof-display-role');
  if (dRole) dRole.innerText = roleVal === 'OWNER' ? 'DACHA EGASI' : 'SAYYOH / MEHMON';

  const dEmail = document.getElementById('prof-display-email');
  if (dEmail) dEmail.innerText = emailVal;

  const inName = document.getElementById('prof-input-name');
  if (inName) inName.value = nameVal;

  const inPhone = document.getElementById('prof-input-phone');
  if (inPhone) inPhone.value = phoneVal;

  const inEmail = document.getElementById('prof-input-email');
  if (inEmail) inEmail.value = emailVal;

  const inCar = document.getElementById('prof-input-car');
  if (inCar) inCar.value = carVal;

  const statSaved = document.getElementById('prof-stat-saved');
  if (statSaved) statSaved.innerText = wishlistItems.size;

  const modal = document.getElementById('profile-modal');
  if (modal) modal.classList.remove('hidden');

  const pMenu = document.getElementById('profile-dropdown-menu');
  if (pMenu) pMenu.classList.add('hidden');
}

function closeProfileModal() {
  const modal = document.getElementById('profile-modal');
  if (modal) modal.classList.add('hidden');
}

function handleSaveProfile(e) {
  e.preventDefault();
  if (!currentUser) return;

  const nameVal = document.getElementById('prof-input-name').value.trim();
  const phoneVal = document.getElementById('prof-input-phone').value.trim();
  const carVal = document.getElementById('prof-input-car').value.trim();

  currentUser.name = nameVal;
  currentUser.full_name = nameVal;
  currentUser.phone = phoneVal;
  currentUser.phone_number = phoneVal;
  currentUser.car_plate = carVal;

  localStorage.setItem('zomin_user', JSON.stringify(currentUser));
  updateHeaderAuthState();
  closeProfileModal();

  const t = I18N[currentLang] || I18N.uz;
  showToast(t.profSavedToast || 'Profil ma’lumotlari muvaffaqiyatli saqlandi!', 'success');
}

function handleLogout() {
  currentUser = null;
  localStorage.removeItem('zomin_user');
  updateHeaderAuthState();
  closeProfileModal();
  const menu = document.getElementById('profile-dropdown-menu');
  if (menu) menu.classList.add('hidden');

  const t = I18N[currentLang] || I18N.uz;
  showToast(t.profLogoutToast || 'Hisobdan chiqildi', 'info');
}

// Google Authentication Handlers
function handleGoogleOneClick() {
  loginWithGoogleAccount('umurzoq');
}

function loginWithGoogleAccount(key) {
  const profile = GOOGLE_PROFILES[key] || GOOGLE_PROFILES.umurzoq;
  currentUser = Object.assign({}, profile);
  localStorage.setItem('zomin_user', JSON.stringify(currentUser));
  updateHeaderAuthState();
  closeAuthModal();
  showToast(`${currentUser.name} (${currentUser.email}) Google hisobi orqali kirdingiz!`, 'success');
}

function handleCustomGoogleSubmit(e) {
  e.preventDefault();
  const nameInput = document.getElementById('custom-google-name-input');
  const emailInput = document.getElementById('custom-google-email-input');

  const emailVal = emailInput ? emailInput.value.trim().toLowerCase() : '';
  let nameVal = nameInput ? nameInput.value.trim() : '';

  if (!emailVal || !emailVal.includes('@')) {
    showToast('Iltimos, to‘g‘ri Google pochtangizni kiriting', 'error');
    return;
  }

  // Pre-seed known names for familiar emails
  if (emailVal === 'school21dev@gmail.com') {
    nameVal = 'Umrzoq Yulchiyev';
  } else if (emailVal === 'umurzoq972@gmail.com') {
    nameVal = 'Umurzoq';
  } else if (!nameVal) {
    const namePart = emailVal.split('@')[0].replace(/[._-]/g, ' ');
    nameVal = namePart.split(' ').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
  }

  const userAvatar = generateUserAvatar(nameVal, emailVal);

  currentUser = {
    id: `usr-google-${Date.now()}`,
    name: nameVal,
    full_name: nameVal,
    email: emailVal,
    avatar: userAvatar,
    phone: '+998 90 123 45 67',
    car_plate: '01 A 777 AA',
    role: 'GUEST'
  };

  localStorage.setItem('zomin_user', JSON.stringify(currentUser));
  updateHeaderAuthState();
  closeAuthModal();
  showToast(`${currentUser.name} (${currentUser.email}) sifatida muvaffaqiyatli kirdingiz!`, 'success');
}

function handleUserAvatarUpload(e) {
  const file = e.target.files && e.target.files[0];
  if (!file) return;

  if (file.size > 5 * 1024 * 1024) {
    showToast('Rasm hajmi 5MB dan oshmasligi kerak', 'error');
    return;
  }

  const reader = new FileReader();
  reader.onload = function(evt) {
    const base64Data = evt.target.result;
    if (!currentUser) {
      currentUser = Object.assign({}, GOOGLE_PROFILES.umurzoq);
    }
    currentUser.avatar = base64Data;
    localStorage.setItem('zomin_user', JSON.stringify(currentUser));

    const profImg = document.getElementById('prof-avatar-img');
    if (profImg) profImg.src = base64Data;

    updateHeaderAuthState();
    showToast('Profil rasmi muvaffaqiyatli yangilandi!', 'success');
  };
  reader.readAsDataURL(file);
}

function selectUserProfile(roleKey) {
  const profile = DEMO_PROFILES[roleKey] || GOOGLE_PROFILES.umurzoq;
  currentUser = Object.assign({}, profile);
  localStorage.setItem('zomin_user', JSON.stringify(currentUser));
  updateHeaderAuthState();
  closeAuthModal();
  showToast(`${currentUser.name} (${currentUser.role}) sifatida tizimga kirdingiz`, 'success');

  if (currentUser.role === 'ADMIN') {
    showAdminPortal();
  }
}

function updateHeaderAuthState() {
  const btn = document.getElementById('header-kirish-btn');
  const menuAvatar = document.getElementById('menu-user-avatar');
  const menuName = document.getElementById('menu-user-name');
  const menuEmail = document.getElementById('menu-user-email');
  const menuRole = document.getElementById('menu-user-role');
  const adminLink = document.getElementById('admin-menu-link');
  const adminDivider = document.getElementById('admin-menu-divider');
  const t = I18N[currentLang] || I18N.uz;

  if (currentUser) {
    let displayName = currentUser.name || currentUser.full_name || 'Umurzoq';
    if (displayName.toLowerCase() === 'school21dev') {
      displayName = 'Umrzoq Yulchiyev';
      currentUser.name = 'Umrzoq Yulchiyev';
      localStorage.setItem('zomin_user', JSON.stringify(currentUser));
    }
    const firstName = displayName.split(' ')[0];
    const avatarUrl = currentUser.avatar || generateUserAvatar(displayName, currentUser.email);

    btn.innerHTML = `<img src="${avatarUrl}" class="nav-avatar-img" alt="${firstName}"><span id="user-btn-text">${firstName}</span><svg class="dropdown-chevron" width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`;
    btn.classList.add('logged-in');

    if (menuAvatar) menuAvatar.src = avatarUrl;
    if (menuName) menuName.innerText = currentUser.name || displayName;
    if (menuEmail) menuEmail.innerText = currentUser.email || 'umurzoq972@gmail.com';
    if (menuRole) menuRole.innerText = currentUser.role === 'OWNER' ? 'DACHA EGASI' : 'SAYYOH / MEHMON';
    if (adminLink) adminLink.style.display = currentUser.role === 'ADMIN' ? 'flex' : 'none';
    if (adminDivider) adminDivider.style.display = currentUser.role === 'ADMIN' ? 'block' : 'none';
  } else {
    btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg><span id="user-btn-text">${t.navLogin || 'Kirish'}</span>`;
    btn.classList.remove('logged-in');
  }
}

// ===================================================================
// LEAFLET MAP
// ===================================================================
function initLeafletMap() {
  const el = document.getElementById('zomin-leaflet-map');
  if (!el || typeof L === 'undefined') return;

  leafletMap = L.map('zomin-leaflet-map', { scrollWheelZoom: false }).setView([39.90, 68.43], 12);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors | Zomin'
  }).addTo(leafletMap);

  const locs = [
    { type: "DACHA", title: "Shox_dacha", price: "1 400 000 so'm", lat: 39.9180, lng: 68.4105, img: "/static/assets/shox_pool.jpg", id: "prop-shox" },
    { type: "DACHA", title: "Chashma Eco Dacha", price: "1 600 000 so'm", lat: 39.9245, lng: 68.4020, img: "/static/assets/dacha_chashma.jpg", id: "prop-chashma" },
    { type: "DACHA", title: "Suffa Panorama Kottej", price: "1 800 000 so'm", lat: 39.8650, lng: 68.4610, img: "/static/assets/dacha_panorama.jpg", id: "prop-panorama" },
    { type: "DACHA", title: "Mountain Chalet Zomin", price: "1 200 000 so'm", lat: 39.8715, lng: 68.4520, img: "/static/assets/chalet.jpg", id: "prop-1" },
    { type: "DACHA", title: "Zomin Villa", price: "2 500 000 so'm", lat: 39.9612, lng: 68.4231, img: "/static/assets/villa.jpg", id: "prop-2" },
    { type: "DACHA", title: "Forest Lodge", price: "900 000 so'm", lat: 39.9450, lng: 68.4110, img: "/static/assets/lodge.jpg", id: "prop-3" },
    { type: "DACHA", title: "O'riklisoy Buloq Bo'yi", price: "150 000 so'm", lat: 39.9210, lng: 68.3980, img: "/static/assets/hiking.jpg", id: "prop-4" },
    { type: "ATTRACTION", title: "Zomin osma ko‘prigi (305m)", price: "Diqqatga sazovor", lat: 39.8900, lng: 68.4400, img: "/static/assets/bridge.jpg" },
    { type: "ATTRACTION", title: "Kabel yo‘li (Suffa 2400m)", price: "Dor yo'li", lat: 39.8750, lng: 68.4550, img: "/static/assets/cablecar.jpg" }
  ];

  locs.forEach(l => {
    const marker = L.marker([l.lat, l.lng]).addTo(leafletMap);
    const clickAction = l.type === 'DACHA' 
      ? `onclick="openBookingModal('${l.id || propertiesCache[0]?.id}')"`
      : `onclick="openAttractionModal('${l.title.includes('ko‘prigi') ? 'bridge' : 'cablecar'}')"`;
    marker.bindPopup(`
      <div class="map-popup-card">
        <img src="${l.img}" class="map-popup-img">
        <div class="map-popup-title">${l.title}</div>
        <div class="map-popup-price">${l.price}</div>
        <button class="btn-popup-action" ${clickAction}>Batafsil / Ko'rish</button>
      </div>
    `);
    mapMarkers.push({ marker, type: l.type });
  });
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

// Navigation helpers
function scrollToSection(id) {
  showTouristHome();
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth' });
}

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

// ===================================================================
// BOOKING FLOW, QUOTES & MODALS (Bronla.uz Layout)
// ===================================================================
async function openBookingModal(propId) {
  selectedProperty = propertiesCache.find(p => p.id === propId) || propertiesCache[0];
  if (!selectedProperty) return;

  document.getElementById('booking-modal').classList.remove('hidden');
  document.getElementById('modal-property-title').innerText = selectedProperty.title;
  document.getElementById('modal-property-desc').innerText = selectedProperty.description;
  document.getElementById('modal-property-address').innerText = `📍 ${selectedProperty.address_text || "Zomin, Jizzax"}`;

  // "Yangi" badge visibility
  const isNew = selectedProperty.slug.includes('shox') || selectedProperty.slug.includes('chashma') || selectedProperty.slug.includes('panorama');
  const badgeEl = document.getElementById('modal-property-new-badge');
  if (badgeEl) badgeEl.style.display = isNew ? 'inline-block' : 'none';

  // Photo Gallery
  let photos = selectedProperty.photos || [];
  if (selectedProperty.slug.includes('shox')) {
    photos = [
      '/static/assets/shox_pool.jpg',
      '/static/assets/shox_kitchen.jpg',
      '/static/assets/shox_bath.jpg',
      '/static/assets/shox_bedroom1.jpg',
      '/static/assets/shox_bedroom2.jpg'
    ];
  } else if (photos.length === 0) {
    photos = ['/static/assets/chalet.jpg', '/static/assets/villa.jpg'];
  }

  const mainPhotoEl = document.getElementById('modal-main-photo');
  if (mainPhotoEl) mainPhotoEl.src = photos[0];

  const thumbsEl = document.getElementById('modal-gallery-thumbs');
  if (thumbsEl) {
    thumbsEl.innerHTML = photos.map((pUrl, idx) => `
      <div class="gallery-thumb-item ${idx === 0 ? 'active' : ''}" onclick="selectModalGalleryPhoto('${pUrl}', this)">
        <img src="${pUrl}" alt="Photo ${idx + 1}">
      </div>
    `).join('');
  }

  // Unit Selector
  const unitSel = document.getElementById('modal-unit-select');
  if (selectedProperty.rental_units && selectedProperty.rental_units.length > 0) {
    unitSel.innerHTML = selectedProperty.rental_units.map(u => `
      <option value="${u.id}">${u.name} (${formatSum(u.base_price_weekday)} so'm)</option>
    `).join('');
  } else {
    unitSel.innerHTML = `
      <option value="unit-standard">Standart Joylashuv (${formatSum(selectedProperty.min_price || 1400000)} so'm/kecha)</option>
      <option value="unit-deluxe">Deluxe Kottej (${formatSum((selectedProperty.min_price || 1400000) * 1.3)} so'm/kecha)</option>
    `;
  }

  // Amenities
  const amenities = selectedProperty.amenities || [
    "Filtrli Hovuz (3.5x7.5m)", "Playstation 3 & Karaoke", "Bilyard & Stol tennisi", 
    "Wi-Fi 5G", "Ochiq oshxona & Mangal", "Archa tandiri", "Konditsioner", "Muzlatgich & Mikroto'lqinli pech"
  ];
  const amEl = document.getElementById('modal-amenities-tags');
  if (amEl) {
    amEl.innerHTML = amenities.map(a => `<span class="amenity-chip">✓ ${a}</span>`).join('');
  }

  // Autofill user phone & car plate if logged in
  if (currentUser) {
    const phoneInput = document.getElementById('modal-guest-phone');
    if (phoneInput && currentUser.phone) phoneInput.value = currentUser.phone;
    const carInput = document.getElementById('modal-car-plate');
    if (carInput && currentUser.car_plate) carInput.value = currentUser.car_plate;
  }

  // Update save/wishlist button state in modal
  updateModalSaveButtonState();

  currentTandirKg = 0;
  updateTandirDisplay();
  await recalculateQuote();
}

function selectModalGalleryPhoto(src, thumbEl) {
  const mainPhoto = document.getElementById('modal-main-photo');
  if (mainPhoto) {
    mainPhoto.style.opacity = '0.5';
    setTimeout(() => {
      mainPhoto.src = src;
      mainPhoto.style.opacity = '1';
    }, 120);
  }
  document.querySelectorAll('.gallery-thumb-item').forEach(el => el.classList.remove('active'));
  if (thumbEl) thumbEl.classList.add('active');
}

function shareCurrentProperty() {
  if (!selectedProperty) return;
  const shareUrl = window.location.origin + '/#stays';
  if (navigator.clipboard) {
    navigator.clipboard.writeText(shareUrl).then(() => {
      showToast(`${selectedProperty.title} havolasi nusxalandi!`, 'success');
    }).catch(() => {
      showToast(`${selectedProperty.title}: ${shareUrl}`, 'info');
    });
  } else {
    showToast(`${selectedProperty.title}: ${shareUrl}`, 'info');
  }
}

function toggleModalSaveProperty() {
  if (!selectedProperty) return;
  const slug = selectedProperty.slug;
  if (wishlistItems.has(slug)) {
    wishlistItems.delete(slug);
    showToast(`${selectedProperty.title} saqlanganlardan olib tashlandi`, 'info');
  } else {
    wishlistItems.add(slug);
    showToast(`${selectedProperty.title} saqlanganlarga qo'shildi!`, 'success');
  }
  updateModalSaveButtonState();
  renderProperties();
}

function updateModalSaveButtonState() {
  if (!selectedProperty) return;
  const isFav = wishlistItems.has(selectedProperty.slug);
  const btn = document.getElementById('modal-save-btn');
  const txt = document.getElementById('modal-save-text');
  if (btn) {
    btn.style.color = isFav ? '#ef4444' : 'var(--color-text-main)';
    btn.style.borderColor = isFav ? '#fca5a5' : 'var(--color-border)';
  }
  if (txt) {
    txt.innerText = isFav ? "Saqlandi" : "Saqlash";
  }
}

function closeBookingModal() {
  document.getElementById('booking-modal').classList.add('hidden');
}

function switchBookingMode(mode) {
  currentBookingMode = mode;
  document.getElementById('btn-mode-overnight').classList.toggle('active', mode === 'OVERNIGHT');
  document.getElementById('btn-mode-dayuse').classList.toggle('active', mode === 'DAY_USE');
  document.getElementById('day-use-slot-picker').classList.toggle('hidden', mode !== 'DAY_USE');
  document.getElementById('group-end-date').classList.toggle('hidden', mode === 'DAY_USE');
  recalculateQuote();
}

function selectDaySlot(slot) {
  currentDayUseSlot = slot;
  document.querySelectorAll('.slot-card').forEach(c => c.classList.remove('active'));
  document.getElementById(`slot-card-${slot}`).classList.add('active');
  recalculateQuote();
}

function onUnitSelectChange() {
  recalculateQuote();
}

function adjustTandir(d) {
  currentTandirKg = Math.max(0, currentTandirKg + d);
  updateTandirDisplay();
  recalculateQuote();
}

function updateTandirDisplay() {
  document.getElementById('tandir-kg-display').innerText = `${currentTandirKg} kg`;
  document.getElementById('tandir-cost-display').innerText = `${formatSum(currentTandirKg * 150000)} so'm`;
}

async function recalculateQuote() {
  const basePrice = selectedProperty ? (selectedProperty.min_price || 1400000) : 1400000;
  const nights = currentBookingMode === 'DAY_USE' ? 1 : 1;
  const stayAmount = basePrice * nights;
  const tandirAmount = currentTandirKg * 150000;
  const total = stayAmount + tandirAmount;
  // Bronla 15% deposit breakdown
  const deposit = Math.round(total * 0.15);
  const remaining = total - deposit;

  currentQuote = {
    base_stay_amount: stayAmount,
    tandir_meat_amount: tandirAmount,
    total_amount: total,
    platform_fee_deposit: deposit,
    remaining_owner_amount: remaining
  };

  const elStay = document.getElementById('quote-stay-amount');
  if (elStay) elStay.innerText = `${formatSum(stayAmount)} so'm`;
  const elTandir = document.getElementById('quote-tandir-amount');
  if (elTandir) elTandir.innerText = `${formatSum(tandirAmount)} so'm`;

  const elTotal = document.getElementById('quote-total-amount');
  if (elTotal) elTotal.innerText = `${formatSum(total)} so'm`;

  const elRemaining = document.getElementById('quote-remaining-amount');
  if (elRemaining) elRemaining.innerText = `${formatSum(remaining)} so'm`;

  const elDeposit = document.getElementById('quote-deposit-amount');
  if (elDeposit) elDeposit.innerText = `${formatSum(deposit)} so'm`;
}

async function submitBookingReservation() {
  if (!currentQuote) return;

  const phoneInput = document.getElementById('modal-guest-phone');
  const guestPhone = phoneInput ? phoneInput.value.trim() : '';

  if (!currentUser && (!guestPhone || guestPhone.length < 9)) {
    showToast('Iltimos, telefon raqamingizni kiriting yoki Google orqali kiring', 'error');
    if (phoneInput) phoneInput.focus();
    return;
  }

  closeBookingModal();
  currentBooking = {
    id: `bk_${Date.now()}`,
    platform_fee_deposit: currentQuote.platform_fee_deposit,
    total_amount: currentQuote.total_amount,
    dates: `${searchCheckInDate || '2026-10-29'} - ${searchCheckOutDate || '2026-10-31'}`
  };
  openPaymentModal(currentBooking);
}

function openPaymentModal(b) {
  document.getElementById('payment-modal').classList.remove('hidden');
  document.getElementById('pay-summary-title').innerText = selectedProperty?.title || 'Mountain Chalet Zomin';
  document.getElementById('pay-summary-dates').innerText = b.dates;
  document.getElementById('pay-summary-amount').innerText = `${formatSum(b.platform_fee_deposit)} so'm`;
  startHoldTimer(15 * 60);
}

function closePaymentModal() {
  document.getElementById('payment-modal').classList.add('hidden');
  if (holdTimerInterval) clearInterval(holdTimerInterval);
}

function choosePaymentProvider(p) {
  document.getElementById('card-choice-click').classList.toggle('active', p === 'CLICK');
  document.getElementById('card-choice-payme').classList.toggle('active', p === 'PAYME');
}

function startHoldTimer(seconds) {
  if (holdTimerInterval) clearInterval(holdTimerInterval);
  let remain = seconds;
  const clock = document.getElementById('hold-countdown-clock');
  holdTimerInterval = setInterval(() => {
    remain--;
    if (remain <= 0) {
      clearInterval(holdTimerInterval);
      clock.innerText = '00:00';
      closePaymentModal();
      return;
    }
    const m = Math.floor(remain / 60).toString().padStart(2, '0');
    const s = (remain % 60).toString().padStart(2, '0');
    clock.innerText = `${m}:${s}`;
  }, 1000);
}

function processPaymentSimulation() {
  clearInterval(holdTimerInterval);
  closePaymentModal();
  showToast('To\'lov muvaffaqiyatli! Soliq OFD elektron cheki berildi.', 'success');
  openOfflineVoucher(currentBooking?.id || 'demo');
}

function openOfflineVoucher(id) {
  document.getElementById('voucher-modal').classList.remove('hidden');
  document.getElementById('vouch-code').innerText = `VOUCH-${Math.floor(100000 + Math.random()*900000)}`;
  document.getElementById('vouch-title').innerText = selectedProperty?.title || 'Mountain Chalet Zomin';
  document.getElementById('vouch-dates').innerText = currentBooking?.dates || '2026-10-29 - 2026-10-31';
  document.getElementById('vouch-owner-name').innerText = 'Alisher Zokirov (+998 90 111 22 33)';
  document.getElementById('vouch-caretaker-name').innerText = 'Rustam Tog\'a (+998 91 777 88 99)';
}

function closeVoucherModal() {
  document.getElementById('voucher-modal').classList.add('hidden');
}

function openAttractionModal(key) {
  const t = I18N[currentLang] || I18N.uz;
  const title = key === 'bridge' ? t.bridgeTitle : (key === 'cablecar' ? t.cableTitle : t.hikingTitle);
  const desc = key === 'bridge' ? t.bridgeDesc : (key === 'cablecar' ? t.cableDesc : t.hikingDesc);
  const img = key === 'bridge' ? '/static/assets/bridge.jpg' : (key === 'cablecar' ? '/static/assets/cablecar.jpg' : '/static/assets/hiking.jpg');

  document.getElementById('attr-modal-title').innerText = title;
  document.getElementById('attr-modal-img').src = img;
  document.getElementById('attr-modal-desc').innerText = desc;
  document.getElementById('attr-modal-meta').innerText = '📍 Zomin Tog\' Klasteri | ⏰ Har kuni 08:00 - 19:00';
  document.getElementById('attraction-modal').classList.remove('hidden');
}

function closeAttractionModal() {
  document.getElementById('attraction-modal').classList.add('hidden');
}

function openMyTripsModal() {
  document.getElementById('profile-dropdown-menu').classList.add('hidden');
  document.getElementById('trips-modal').classList.remove('hidden');
  document.getElementById('trips-list-container').innerHTML = `
    <div style="background:#fff; padding:18px; border-radius:12px; border:1px solid #e7e4dc; display:flex; justify-content:space-between; align-items:center;">
      <div>
        <strong>Mountain Chalet Zomin</strong>
        <div style="font-size:13px; color:#5c6e67;">2026-10-29 - 2026-10-31 | 6 mehmon</div>
        <span class="badge-status verified" style="margin-top:4px; display:inline-block;">KAFOLATLANGAN</span>
      </div>
      <button class="btn-primary-pill" onclick="openOfflineVoucher('1')">Vaucher / Chek</button>
    </div>
  `;
}

function closeMyTripsModal() {
  document.getElementById('trips-modal').classList.add('hidden');
}

function openOwnerPortalModal() {
  document.getElementById('profile-dropdown-menu').classList.add('hidden');
  document.getElementById('owner-modal').classList.remove('hidden');
  document.getElementById('owner-bookings-list').innerHTML = `
    <div style="background:#fff; padding:16px; border-radius:12px; border:1px solid #e7e4dc; display:flex; justify-content:space-between; align-items:center;">
      <div>
        <strong>Umrzoq Yulchiyev (6 mehmon)</strong>
        <div style="font-size:13px; color:#5c6e67;">2026-10-29 - 2026-10-31 | Mountain Chalet Zomin</div>
        <div style="font-size:13px; color:#0d382c; font-weight:700;">1 200 000 so'm (10% kafolat to'langan)</div>
      </div>
      <div style="display:flex; gap:8px;">
        <button class="btn-primary-pill" style="padding:6px 14px; font-size:12px;" onclick="showToast('Bron tasdiqlandi!', 'success')">Qabul qilish</button>
        <button class="btn-primary-pill" style="padding:6px 14px; font-size:12px; background:#ef4444;" onclick="showToast('Rad etildi', 'info')">Rad etish</button>
      </div>
    </div>
  `;
}

function closeOwnerPortalModal() {
  document.getElementById('owner-modal').classList.add('hidden');
}

function triggerOwnerIVRCheck() {
  showToast('IVR tekshiruvi: Dacha egasiga avtomat qo\'ng\'iroq yuborildi', 'success');
}

function openCaretakerModal() {
  document.getElementById('profile-dropdown-menu').classList.add('hidden');
  document.getElementById('caretaker-modal').classList.remove('hidden');
  document.getElementById('caretaker-arrivals-list').innerHTML = `
    <div style="background:#fff; padding:20px; border-radius:12px; border:2px solid #0d382c;">
      <div style="font-size:26px; font-weight:900; letter-spacing:2px; font-family:monospace; color:#0d382c;">01 A 777 AA</div>
      <div style="font-size:16px; font-weight:700; margin-top:6px;">Umrzoq Yulchiyev (6 nafar mehmon)</div>
      <div style="font-size:13px; color:#5c6e67; margin-bottom:14px;">Kelish vaqti: Bugun, 14:00</div>
      <button class="btn-primary-pill w-100" onclick="showToast('Kalit topshirildi! Check-in muvaffaqiyatli.', 'success'); closeCaretakerModal();">
        Kalit topshirildi (Check-in)
      </button>
    </div>
  `;
}

function closeCaretakerModal() {
  document.getElementById('caretaker-modal').classList.add('hidden');
}

function openPartnerModal() {
  document.getElementById('partner-modal').classList.remove('hidden');
}

function closePartnerModal() {
  document.getElementById('partner-modal').classList.add('hidden');
}

function handlePartnerSubmit(e) {
  e.preventDefault();
  closePartnerModal();
  showToast('Arizangiz qabul qilindi! Tez orada bog\'lanamiz.', 'success');
}

function submitNewsletter() {
  const input = document.getElementById('footer-newsletter-email');
  if (input && input.value) {
    showToast('Rahmat! Zomin yangiliklariga muvaffaqiyatli obuna bo\'ldingiz.', 'success');
    input.value = '';
  } else {
    showToast('Iltimos, elektron pochtangizni kiriting', 'error');
  }
}

// ===================================================================
// ADMIN PORTAL
// ===================================================================
async function refreshAdminData() {
  try {
    const statsRes = await fetch('/api/v1/admin/dashboard-stats');
    if (statsRes.ok) {
      const stats = await statsRes.json();
      document.getElementById('admin-stat-gmv').innerText = `${formatSum(stats.total_gmv)} so'm`;
      document.getElementById('admin-stat-revenue').innerText = `${formatSum(stats.total_platform_fee || stats.platform_net_revenue || 0)} so'm`;
      document.getElementById('admin-stat-properties').innerText = `${stats.verified_properties || 4} ta`;
      document.getElementById('admin-stat-bookings').innerText = `${stats.total_bookings || 1} ta`;
    }

    const propsRes = await fetch('/api/v1/admin/properties');
    if (propsRes.ok) {
      const props = await propsRes.json();
      document.getElementById('admin-properties-table-body').innerHTML = props.map(p => `
        <tr>
          <td><strong>${p.title}</strong><br><small>${p.micro_district}</small></td>
          <td>${p.owner_id.substring(0,8)}</td>
          <td><span class="badge-status verified">${p.verification_status}</span></td>
          <td>${formatSum(p.min_price || 1200000)} so'm</td>
          <td>${p.road_condition === 'ASPHALT_SEDAN' ? '✅ Asfalt' : '🚙 4WD'}</td>
          <td>
            <button class="btn-table-action" onclick="showToast('Obyekt tasdiqlangan', 'success')">Tekshirish</button>
          </td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.log('Admin refresh info');
  }
}

function switchAdminTab(key) {
  document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.admin-tab-pane').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  const target = document.getElementById(`admin-tab-${key}`);
  if (target) target.classList.add('active');
}
