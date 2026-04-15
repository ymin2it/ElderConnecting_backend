from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID

from database import get_db
from models import User, Booking
from schemas import BookingCreate, BookingUpdate, BookingResponse
from auth import get_current_user

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])


@router.get("/", response_model=list[BookingResponse])
def get_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get bookings relevant to the current user (as caregiver or patient)."""
    bookings = (
        db.query(Booking)
        .filter(
            (Booking.caregiver_id == current_user.id) | (Booking.patient_id == current_user.id)
        )
        .order_by(desc(Booking.created_at))
        .all()
    )

    result = []
    for b in bookings:
        caregiver = db.query(User).filter(User.id == b.caregiver_id).first()
        patient = db.query(User).filter(User.id == b.patient_id).first()
        resp = BookingResponse.model_validate(b)
        resp.caregiver_name = caregiver.name if caregiver else "Unknown"
        resp.patient_name = patient.name if patient else "Unknown"
        result.append(resp)

    return result


@router.post("/", response_model=BookingResponse)
def create_booking(
    data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify caregiver exists and has role caregiver
    caregiver = db.query(User).filter(User.id == data.caregiver_id, User.role == "caregiver").first()
    if not caregiver:
        raise HTTPException(status_code=404, detail="Caregiver not found")

    booking = Booking(
        caregiver_id=data.caregiver_id,
        patient_id=data.patient_id,
        date=data.date,
        time=data.time,
        notes=data.notes,
        status="pending",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    resp = BookingResponse.model_validate(booking)
    resp.caregiver_name = caregiver.name
    patient = db.query(User).filter(User.id == data.patient_id).first()
    resp.patient_name = patient.name if patient else "Unknown"
    return resp


@router.put("/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: UUID,
    data: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Only caregiver or patient can update
    if str(booking.caregiver_id) != str(current_user.id) and str(booking.patient_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(booking, key, value)

    db.commit()
    db.refresh(booking)

    caregiver = db.query(User).filter(User.id == booking.caregiver_id).first()
    patient = db.query(User).filter(User.id == booking.patient_id).first()
    resp = BookingResponse.model_validate(booking)
    resp.caregiver_name = caregiver.name if caregiver else "Unknown"
    resp.patient_name = patient.name if patient else "Unknown"
    return resp
