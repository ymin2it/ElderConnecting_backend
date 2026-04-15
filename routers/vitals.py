from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID

from database import get_db
from models import User, Vital
from schemas import VitalCreate, VitalResponse
from auth import get_current_user

router = APIRouter(prefix="/api/vitals", tags=["Vitals"])


@router.post("/", response_model=VitalResponse)
def create_vital(
    data: VitalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vital = Vital(
        user_id=current_user.id,
        blood_pressure=data.blood_pressure,
        heart_rate=data.heart_rate,
        temperature=data.temperature,
        sugar=data.sugar,
        date=data.date,
    )
    db.add(vital)
    db.commit()
    db.refresh(vital)
    return VitalResponse.model_validate(vital)


@router.get("/{user_id}", response_model=list[VitalResponse])
def get_vitals(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vitals = (
        db.query(Vital)
        .filter(Vital.user_id == user_id)
        .order_by(desc(Vital.date))
        .limit(50)
        .all()
    )
    return [VitalResponse.model_validate(v) for v in vitals]
