import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.services.payment_service import process_click_webhook, process_payme_rpc

router = APIRouter(prefix="/payments", tags=["Payment Webhooks & Processing"])

class SimulatePaymentRequest(BaseModel):
    booking_id: str
    provider: str = "CLICK" # CLICK or PAYME

@router.post("/click/webhook")
async def click_webhook(request: Request):
    """
    Click to'lov tizimi webhook handleri (AC-04 & AC-06):
    Action 0 (Prepare) va Action 1 (Complete) ni qabul qiladi.
    """
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)
    return process_click_webhook(payload)

@router.post("/payme/webhook")
async def payme_webhook(request: Request):
    """
    Payme JSON-RPC 2.0 webhook handleri:
    CheckPerformTransaction, CreateTransaction, PerformTransaction, CancelTransaction.
    """
    try:
        data = await request.json()
    except Exception:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
    auth_header = request.headers.get("Authorization")
    return process_payme_rpc(data, auth_header=auth_header)

@router.post("/simulate-success")
def simulate_instant_payment(req: SimulatePaymentRequest):
    """
    Frontend va testlar uchun xizmat haqini to'lash simulyatori.
    Click webhook Action 1 orqali to'lovni avtomatik tasdiqlaydi.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE id = ? OR booking_reference = ?", (req.booking_id, req.booking_id))
        b = cursor.fetchone()
        if not b:
            raise HTTPException(status_code=404, detail="Bron topilmadi")

        click_payload = {
            "click_trans_id": f"sim_{uuid.uuid4().hex[:8]}",
            "service_id": "19827",
            "merchant_trans_id": b["booking_reference"],
            "amount": float(b["platform_fee_amount"]),
            "action": 1,
            "sign_time": "2026-07-15 12:00:00",
            "error": 0
        }
        return process_click_webhook(click_payload)
