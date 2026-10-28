from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.models import OfflineVoucher
from app.services.voucher_service import generate_offline_voucher

router = APIRouter(prefix="/vouchers", tags=["Offline Trip Voucher"])

@router.get("/{id_or_ref}", response_model=OfflineVoucher)
def get_voucher_json(id_or_ref: str):
    """
    Oflayn safar vaucheri (AC-09):
    Tog'da internet yo'qolganda ishlaydigan vaucher ma'lumotlari:
    GSM telefon raqamlari, yo'l yo'riqnomasi, GPS havolalari va QR kod.
    """
    return generate_offline_voucher(id_or_ref)

@router.get("/{id_or_ref}/html", response_class=HTMLResponse)
def get_voucher_html(id_or_ref: str):
    """
    Chiroyli oflayn saqlanadigan yoki chop etiladigan HTML vaucher formati.
    """
    v = generate_offline_voucher(id_or_ref)
    
    html_content = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZominStay Vaucher — {v.booking_reference}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f0fdf4; color: #1e293b;
        }}
        .card {{
            max-width: 600px; margin: 0 auto; background: white; border-radius: 16px;
            padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); border: 1px solid #bbf7d0;
        }}
        .header {{
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 2px dashed #bbf7d0; padding-bottom: 16px; margin-bottom: 16px;
        }}
        .badge {{
            background: #15803d; color: white; padding: 6px 12px; border-radius: 9999px;
            font-size: 13px; font-weight: bold; text-transform: uppercase;
        }}
        .section-title {{
            font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #166534;
            font-weight: bold; margin-top: 16px; margin-bottom: 8px;
        }}
        .field {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 15px; }}
        .field-label {{ color: #64748b; }}
        .field-val {{ font-weight: 600; text-align: right; }}
        .call-box {{
            display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 20px 0;
        }}
        .btn-call {{
            display: block; text-align: center; background: #16a34a; color: white;
            text-decoration: none; padding: 12px; border-radius: 10px; font-weight: bold;
        }}
        .btn-map {{
            display: block; text-align: center; background: #0284c7; color: white;
            text-decoration: none; padding: 12px; border-radius: 10px; font-weight: bold; margin-top: 8px;
        }}
        .directions-box {{
            background: #f8fafc; border-left: 4px solid #16a34a; padding: 12px;
            border-radius: 4px; font-size: 14px; line-height: 1.5; margin: 12px 0;
        }}
        .qr-box {{
            text-align: center; margin-top: 20px; padding: 12px; background: #ecfdf5; border-radius: 10px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <div>
                <h2 style="margin:0; color:#166534;">🌲 ZominStay</h2>
                <small style="color:#64748b;">Kafolatlangan Sayohat Vaucheri</small>
            </div>
            <span class="badge">{v.booking_status}</span>
        </div>

        <div class="section-title">Turar Joy & Hudud</div>
        <div class="field"><span class="field-label">Dacha nomi:</span><span class="field-val">{v.property_title}</span></div>
        <div class="field"><span class="field-label">Mikro-hudud:</span><span class="field-val">{v.micro_district}</span></div>
        <div class="field"><span class="field-label">Aniq manzil:</span><span class="field-val">{v.address_text}</span></div>

        <div class="section-title">Yo'l va Infratuzilma</div>
        <div class="directions-box">
            <b>🚗 Yo'l sharoiti:</b> {v.road_condition_advice}<br><br>
            <b>🗺️ Matnli yo'l ko'rsatmasi:</b> {v.step_by_step_directions}
        </div>

        <div class="section-title">Mehmon va Sanalar</div>
        <div class="field"><span class="field-label">Bron raqami:</span><span class="field-val">{v.booking_reference}</span></div>
        <div class="field"><span class="field-label">Mehmon ismi:</span><span class="field-val">{v.guest_name}</span></div>
        <div class="field"><span class="field-label">Mehmon telefoni:</span><span class="field-val">{v.guest_phone}</span></div>
        <div class="field"><span class="field-label">Mashina raqami:</span><span class="field-val">{v.car_plate or "Belgilanmagan"}</span></div>
        <div class="field"><span class="field-label">Kirish (Check-in):</span><span class="field-val">{v.checkin_time[:16].replace('T', ' ')}</span></div>
        <div class="field"><span class="field-label">Chiqish (Check-out):</span><span class="field-val">{v.checkout_time[:16].replace('T', ' ')}</span></div>
        <div class="field"><span class="field-label">Mehmonlar soni:</span><span class="field-val">{v.guest_count} kishi</span></div>
        
        {f'<div class="field"><span class="field-label">🍗 Zomin tandiri:</span><span class="field-val" style="color:#b45309;">{v.tandir_order}</span></div>' if v.tandir_order else ''}

        <div class="section-title">Moliyaviy Hisob-kitob</div>
        <div class="field">
            <span class="field-label">Joyida dacha egasiga to'lanadi:</span>
            <span class="field-val" style="font-size:18px; color:#15803d;">{int(v.payable_on_arrival_to_owner):,} so'm</span>
        </div>

        <div class="section-title">Aloqa (Internet yo'qolganda GSM orqali bog'lanish)</div>
        <div class="call-box">
            <a href="tel:{v.owner_phone}" class="btn-call">📞 Dacha Egasi<br><small>{v.owner_phone}</small></a>
            <a href="tel:{v.caretaker_phone}" class="btn-call" style="background:#0f766e;">🔑 Bog'bon (Qarovchi)<br><small>{v.caretaker_phone}</small></a>
        </div>

        <a href="{v.navigation.yandex_maps_url}" class="btn-map">🧭 Yandex Navigatorda Marshrut Olish</a>
        <a href="{v.navigation.geo_uri}" class="btn-map" style="background:#475569;">📍 Oflayn GPS Koordinata ({v.navigation.latitude}, {v.navigation.longitude})</a>

        <div class="qr-box">
            <code style="font-weight:bold; font-size:14px; letter-spacing:1px; color:#065f46;">{v.offline_qr_data}</code>
            <p style="margin:4px 0 0; font-size:12px; color:#64748b;">Oflayn tekshiruv va kutib olish uchun taqdim etiladi</p>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
