import os
from pydantic import BaseModel

def get_default_db_path() -> str:
    if os.getenv("VERCEL"):
        return "/tmp/zominstay.db"
    return "zominstay.db"

class Settings(BaseModel):
    PROJECT_NAME: str = "ZominStay — Zomin Tog' Turizmi va Dam Olish Ekotizimi"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "zominstay-mountain-ultra-secret-key-2026")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "7123456789:AAH_zominstay_mountain_bot_sample_token")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "http://localhost:8000")
    
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", get_default_db_path())
    PLATFORM_FEE_PERCENTAGE: float = 10.0  # 10% onlayn kafolat haqi
    HOLD_DURATION_MINUTES: int = 15        # 15 daqiqalik qulf
    TANDIR_PRICE_PER_KG: float = 150000.0  # 150,000 UZS / kg Zomin archa tandiri
    
    CLICK_SERVICE_ID: str = os.getenv("CLICK_SERVICE_ID", "19827")
    CLICK_SECRET_KEY: str = os.getenv("CLICK_SECRET_KEY", "click_secret_key_zomin_2026")
    PAYME_SECRET_KEY: str = os.getenv("PAYME_SECRET_KEY", "payme_secret_key_zomin_2026")

settings = Settings()
