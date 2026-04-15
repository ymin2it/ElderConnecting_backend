from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID

from database import get_db
from models import User, Medication
from schemas import MedicationCreate, MedicationUpdate, MedicationResponse
from auth import get_current_user

router = APIRouter(prefix="/api/medications", tags=["Medications"])


@router.post("/", response_model=MedicationResponse)
def create_medication(
    data: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    med = Medication(
        user_id=current_user.id,
        name=data.name,
        dosage=data.dosage,
        time_of_day=data.time_of_day,
        schedule_time=data.schedule_time,
        status=data.status or "pending",
        date=data.date,
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return MedicationResponse.model_validate(med)


@router.get("/{user_id}", response_model=list[MedicationResponse])
def get_medications(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meds = (
        db.query(Medication)
        .filter(Medication.user_id == user_id)
        .order_by(desc(Medication.created_at))
        .all()
    )
    return [MedicationResponse.model_validate(m) for m in meds]


@router.put("/{med_id}", response_model=MedicationResponse)
def update_medication(
    med_id: UUID,
    data: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    med = db.query(Medication).filter(Medication.id == med_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    if str(med.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(med, key, value)

    db.commit()
    db.refresh(med)
    return MedicationResponse.model_validate(med)


@router.delete("/{med_id}")
def delete_medication(
    med_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    med = db.query(Medication).filter(Medication.id == med_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    if str(med.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(med)
    db.commit()
    return {"message": "Medication deleted"}
