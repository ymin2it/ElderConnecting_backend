import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import User, HealthRecord
from schemas import HealthRecordResponse
from auth import get_current_user

router = APIRouter(prefix="/api/records", tags=["Health Records"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=HealthRecordResponse)
async def upload_record(
    file: UploadFile = File(...),
    doctor: str = Form(default=""),
    diagnosis: str = Form(default=""),
    record_date: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import date as date_type, datetime

    # Save file locally
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    saved_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse date
    try:
        parsed_date = datetime.strptime(record_date, "%Y-%m-%d").date() if record_date else date_type.today()
    except ValueError:
        parsed_date = date_type.today()

    record = HealthRecord(
        user_id=current_user.id,
        file_url=f"/uploads/{saved_name}",
        file_name=file.filename or saved_name,
        doctor=doctor or None,
        diagnosis=diagnosis or None,
        date=parsed_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return HealthRecordResponse.model_validate(record)


@router.get("/{user_id}", response_model=list[HealthRecordResponse])
def get_records(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user_id)
        .order_by(desc(HealthRecord.date))
        .all()
    )
    return [HealthRecordResponse.model_validate(r) for r in records]


@router.delete("/{record_id}")
def delete_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if str(record.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete file if it exists
    file_path = os.path.join(UPLOAD_DIR, os.path.basename(record.file_url or ""))
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(record)
    db.commit()
    return {"message": "Record deleted"}
