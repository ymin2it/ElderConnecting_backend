from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, timedelta
from dotenv import load_dotenv
import os

from database import SessionLocal
from models import User, Vital, Medication, Appointment, Booking, VideoSession, Notification
from jose import JWTError, jwt

load_dotenv()

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SECRET_KEY = os.getenv("JWT_SECRET", "fallback-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# ─── System prompts ──────────────────────────────────────────────────

GUEST_SYSTEM_PROMPT = """You are ElderConnect Assistant, a friendly and helpful AI chatbot for the ElderConnecting platform — a smart elderly care web application.

About ElderConnecting:
- It connects elderly individuals with verified caregivers, healthcare clinics, and home service providers
- Features: Telemedicine/Video Consultations, Medication Reminders, Appointment Booking, Health Records, Caregiver Booking, Family Monitoring
- Roles: Elder (patient), Family Member, Caregiver, Admin
- Built with React frontend and FastAPI backend

Key features you can guide visitors about:
1. Registration & Login — Users can register as Elder, Family, Caregiver, or Admin
2. Elder Dashboard — View health vitals (BP, heart rate, temperature, blood sugar), upcoming appointments, medication schedule
3. Health Records — Upload and manage prescriptions, lab reports, medical documents
4. Medication Reminders — Track daily medications (morning/afternoon/night), mark as taken/missed
5. Appointments — Book doctor appointments with clinic, date, time
6. Video Consultation — Schedule and join video calls with doctors
7. Notifications — Alerts, reminders, SOS notifications
8. Family Dashboard — Monitor elderly loved ones' vitals, alerts, appointments, Call/SOS buttons
9. Caregiver Dashboard — View stats, manage booking requests (accept/reject)
10. Booking Management — Caregivers manage patient bookings
11. Admin Dashboard — Platform stats, user management

Guidelines:
- You are greeting a visitor who may NOT be logged in yet. Encourage them to register or log in.
- Keep responses concise and friendly (2-4 sentences max)
- Use simple language suitable for elderly users
- If asked about emergencies, always advise calling local emergency services first
- If asked about technical issues, suggest contacting support@elderconnecting.com
- You can use relevant emojis sparingly to be warm and approachable
- Don't make up features that don't exist on the platform
- You can help visitors navigate: "Click on Services in the top menu" or "Go to the Register page to create your account"
"""


def build_personalized_prompt(user: User, db: Session) -> str:
    """Build an AI system prompt enriched with the user's real data."""
    today = date.today()

    # ── Fetch user-specific data ────────────────────────────────
    # Latest vitals
    latest_vital = (
        db.query(Vital)
        .filter(Vital.user_id == user.id)
        .order_by(desc(Vital.date))
        .first()
    )

    # Today's medications
    todays_meds = (
        db.query(Medication)
        .filter(Medication.user_id == user.id, Medication.date == today)
        .all()
    )

    # Upcoming appointments (next 7 days)
    upcoming_appts = (
        db.query(Appointment)
        .filter(
            Appointment.user_id == user.id,
            Appointment.date >= today,
            Appointment.date <= today + timedelta(days=7),
            Appointment.status == "scheduled",
        )
        .order_by(Appointment.date)
        .limit(5)
        .all()
    )

    # Today's video sessions
    todays_sessions = (
        db.query(VideoSession)
        .filter(VideoSession.user_id == user.id, VideoSession.date == today)
        .all()
    )

    # Unread notifications
    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read == False)
        .count()
    )

    # Bookings (for caregivers)
    pending_bookings = []
    if user.role == "caregiver":
        pending_bookings = (
            db.query(Booking)
            .filter(Booking.caregiver_id == user.id, Booking.status == "pending")
            .all()
        )

    # ── Build the data summary ──────────────────────────────────
    data_lines = []

    if latest_vital:
        data_lines.append(f"Latest Vitals (recorded {latest_vital.date}):")
        if latest_vital.blood_pressure:
            data_lines.append(f"  - Blood Pressure: {latest_vital.blood_pressure}")
        if latest_vital.heart_rate:
            data_lines.append(f"  - Heart Rate: {latest_vital.heart_rate} bpm")
        if latest_vital.temperature:
            data_lines.append(f"  - Temperature: {latest_vital.temperature}°C")
        if latest_vital.sugar:
            data_lines.append(f"  - Blood Sugar: {latest_vital.sugar} mg/dL")

    if todays_meds:
        pending = [m for m in todays_meds if m.status == "pending"]
        taken = [m for m in todays_meds if m.status == "taken"]
        missed = [m for m in todays_meds if m.status == "missed"]
        data_lines.append(f"Today's Medications: {len(todays_meds)} total — {len(taken)} taken, {len(pending)} pending, {len(missed)} missed")
        for m in todays_meds:
            data_lines.append(f"  - {m.name} ({m.dosage or 'no dosage'}) — {m.time_of_day or ''} at {m.schedule_time or 'N/A'} — Status: {m.status}")

    if upcoming_appts:
        data_lines.append(f"Upcoming Appointments (next 7 days): {len(upcoming_appts)}")
        for a in upcoming_appts:
            data_lines.append(f"  - {a.doctor} at {a.clinic or 'N/A'} on {a.date} at {a.time or 'N/A'}")

    if todays_sessions:
        data_lines.append(f"Today's Video Consultations: {len(todays_sessions)}")
        for s in todays_sessions:
            data_lines.append(f"  - {s.doctor} at {s.time or 'N/A'} ({s.duration or '30 min'}) — Status: {s.status}")

    if unread_count > 0:
        data_lines.append(f"Unread Notifications: {unread_count}")

    if pending_bookings:
        data_lines.append(f"Pending Booking Requests: {len(pending_bookings)}")
        for b in pending_bookings:
            patient = db.query(User).filter(User.id == b.patient_id).first()
            patient_name = patient.name if patient else "Unknown"
            data_lines.append(f"  - Patient: {patient_name} on {b.date} at {b.time or 'N/A'}")

    user_data_block = "\n".join(data_lines) if data_lines else "No recent data available."

    # ── Construct the prompt ────────────────────────────────────
    prompt = f"""You are ElderConnect Assistant, a personalized AI assistant for the ElderConnecting elderly care platform.

You are speaking to a LOGGED-IN user. Here is their profile:
- Name: {user.name}
- Role: {user.role}
- Email: {user.email}
- Phone: {user.phone or 'Not set'}
- Date of Birth: {user.dob or 'Not set'}
- Emergency Contact: {user.emergency_contact or 'Not set'}

Here is their current real-time data from the platform (today is {today}):
{user_data_block}

Guidelines:
- Address the user by their first name ({user.name.split()[0]})
- Answer questions using the REAL DATA above — don't make up numbers
- If they ask about their vitals, medications, or appointments, use the actual data provided
- Keep responses concise, warm, and friendly (2-4 sentences max)
- Use simple language suitable for elderly users
- If asked about emergencies, ALWAYS advise calling local emergency services first
- If asked about technical issues, suggest contacting support@elderconnecting.com
- You can use relevant emojis sparingly to be warm and approachable
- Don't make up features that don't exist on the platform
- For elders: you can remind them to take medications, mention upcoming appointments, or comment on their vitals
- For caregivers: you can mention pending bookings they need to review
- For family members: you can help them understand the monitoring features
- For admins: you can help them navigate the admin dashboard
"""
    return prompt


class ChatMessage(BaseModel):
    message: str
    history: Optional[list] = []


@router.post("/chat")
async def chat(data: ChatMessage, authorization: Optional[str] = Header(default=None)):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    # ── Try to identify the user from the optional token ────────
    system_prompt = GUEST_SYSTEM_PROMPT
    db = None

    try:
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ", 1)[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                db = SessionLocal()
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    system_prompt = build_personalized_prompt(user, db)
    except (JWTError, Exception):
        # Token invalid or DB error — fall back to guest prompt
        pass

    try:
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last 10 messages max)
        for msg in (data.history or [])[-10:]:
            role = "assistant" if msg.get("from") == "bot" else "user"
            messages.append({"role": role, "content": msg.get("text", "")})

        # Add current message
        messages.append({"role": "user", "content": data.message})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=400,
            temperature=0.7,
        )

        reply = response.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        return {"reply": "I'm having trouble connecting right now. Please try again or contact support@elderconnecting.com for help. 😊"}

    finally:
        if db:
            db.close()
