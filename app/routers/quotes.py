from fastapi import APIRouter
from app.models import QuoteRequest, QuoteResponse
from app.services.quote_service import calculate_quote

router = APIRouter(prefix="/quotes", tags=["Quotation Engine"])

@router.post("/calculate", response_model=QuoteResponse)
def get_quotation(request: QuoteRequest):
    """
    Aniq narx kalkulyatori (TZ 5.2.1):
    Hafta kunlari (ish kunlari va dam olish kunlari), tapchan slotlari,
    va Zomin archa tandiri qo'shimcha buyurtmasini hisoblab,
    xavfsiz raqamli imzolangan quote_token qaytaradi.
    """
    return calculate_quote(request)
