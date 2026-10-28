import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, seed_initial_data
from app.routers import (
    auth, properties, quotes, bookings, payments, vouchers, owner, admin
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB & Seed data
    init_db()
    seed_initial_data()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Zomin tog' turizmi, dacha va dam olish ekotizimi — Double-booking himoyasi, Click/Payme to'lovlari, Telegram Mini App integratsiyasi va Oflayn safar vaucheri.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(properties.router, prefix=settings.API_V1_PREFIX)
app.include_router(quotes.router, prefix=settings.API_V1_PREFIX)
app.include_router(bookings.router, prefix=settings.API_V1_PREFIX)
app.include_router(payments.router, prefix=settings.API_V1_PREFIX)
app.include_router(vouchers.router, prefix=settings.API_V1_PREFIX)
app.include_router(owner.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}

@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "ZominStay API is running. Go to /docs for Swagger UI."}

@app.api_route("/admin", methods=["GET", "HEAD"])
def serve_admin():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Admin portal"}
