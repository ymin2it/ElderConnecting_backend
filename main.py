from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
from routers import auth, users, dashboard, records, vitals, medications, appointments, notifications, bookings, video, admin, chatbot

# Create all tables — wrap in try/except so app starts even offline
if engine:
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created / verified successfully")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("   The app will start, but DB operations will fail until connection is restored.")
else:
    print("⚠️  Database engine not initialized - check DATABASE_URL in .env")
    print("   The app will start, but DB operations will fail.")

app = FastAPI(
    title="ElderConnecting API",
    description="Backend API for ElderConnecting — Smart Elderly Care Platform",
    version="1.0.0",
)

# CORS — allow frontend (local dev + Netlify production)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
allowed_origins = [o.strip() for o in CORS_ORIGINS if o.strip()] or DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all origins — fine since API uses JWT auth
    allow_credentials=False,      # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include all routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(records.router)
app.include_router(vitals.router)
app.include_router(medications.router)
app.include_router(appointments.router)
app.include_router(notifications.router)
app.include_router(bookings.router)
app.include_router(video.router)
app.include_router(admin.router)
app.include_router(chatbot.router)


@app.get("/")
def root():
    return {"message": "ElderConnecting API is running", "docs": "/docs"}
