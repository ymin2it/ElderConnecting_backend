from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date as Date, datetime
from uuid import UUID


# ─── Auth ────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str  # elder, family, caregiver
    phone: Optional[str] = None
    dob: Optional[Date] = None
    emergency_contact: Optional[str] = None
    caregiver_credentials: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    dob: Optional[Date] = None
    emergency_contact: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[Date] = None
    emergency_contact: Optional[str] = None


# ─── Vitals ──────────────────────────────────────────────────────────

class VitalCreate(BaseModel):
    blood_pressure: Optional[str] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    sugar: Optional[float] = None
    date: Date


class VitalResponse(BaseModel):
    id: UUID
    user_id: UUID
    blood_pressure: Optional[str] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    sugar: Optional[float] = None
    date: Date
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Health Records ──────────────────────────────────────────────────

class HealthRecordCreate(BaseModel):
    doctor: Optional[str] = None
    diagnosis: Optional[str] = None
    date: Date


class HealthRecordResponse(BaseModel):
    id: UUID
    user_id: UUID
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    doctor: Optional[str] = None
    diagnosis: Optional[str] = None
    date: Date
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Medications ─────────────────────────────────────────────────────

class MedicationCreate(BaseModel):
    name: str
    dosage: Optional[str] = None
    time_of_day: Optional[str] = None  # morning, afternoon, night
    schedule_time: Optional[str] = None  # e.g. "08:00"
    status: Optional[str] = "pending"
    date: Optional[Date] = None


class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    time_of_day: Optional[str] = None
    schedule_time: Optional[str] = None
    status: Optional[str] = None
    date: Optional[Date] = None


class MedicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    dosage: Optional[str] = None
    time_of_day: Optional[str] = None
    schedule_time: Optional[str] = None
    status: Optional[str] = None
    date: Optional[Date] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Appointments ────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    doctor: str
    clinic: Optional[str] = None
    date: Date
    time: Optional[str] = None
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    doctor: Optional[str] = None
    clinic: Optional[str] = None
    date: Optional[Date] = None
    time: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: UUID
    user_id: UUID
    doctor: str
    clinic: Optional[str] = None
    date: Date
    time: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Notifications ───────────────────────────────────────────────────

class NotificationCreate(BaseModel):
    user_id: UUID
    type: str  # alert, reminder, sos
    message: str


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    message: str
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Bookings ────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    caregiver_id: UUID
    patient_id: UUID
    date: Date
    time: Optional[str] = None
    notes: Optional[str] = None


class BookingUpdate(BaseModel):
    status: Optional[str] = None  # pending, accepted, rejected
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: UUID
    caregiver_id: UUID
    patient_id: UUID
    date: Date
    time: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    caregiver_name: Optional[str] = None
    patient_name: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Video Sessions ──────────────────────────────────────────────────

class VideoSessionCreate(BaseModel):
    doctor: str
    date: Date
    time: Optional[str] = None
    duration: Optional[str] = "30 min"
    notes: Optional[str] = None


class VideoSessionUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    duration: Optional[str] = None


class VideoSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    doctor: str
    room_id: str
    date: Date
    time: Optional[str] = None
    duration: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
