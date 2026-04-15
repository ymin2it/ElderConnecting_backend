from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID

from database import get_db
from models import User, Appointment
from schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from auth import get_current_user

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("/", response_model=AppointmentResponse)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = Appointment(
        user_id=current_user.id,
        doctor=data.doctor,
        clinic=data.clinic,
        date=data.date,
        time=data.time,
        notes=data.notes,
        status="scheduled",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return AppointmentResponse.model_validate(appt)


@router.get("/{user_id}", response_model=list[AppointmentResponse])
def get_appointments(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appts = (
        db.query(Appointment)
        .filter(Appointment.user_id == user_id)
        .order_by(desc(Appointment.date))
        .all()
    )
    return [AppointmentResponse.model_validate(a) for a in appts]


@router.put("/{appt_id}", response_model=AppointmentResponse)
def update_appointment(
    appt_id: UUID,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if str(appt.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(appt, key, value)

    db.commit()
    db.refresh(appt)
    return AppointmentResponse.model_validate(appt)


@router.delete("/{appt_id}")
def delete_appointment(
    appt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if str(appt.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(appt)
    db.commit()
    return {"message": "Appointment deleted"}
