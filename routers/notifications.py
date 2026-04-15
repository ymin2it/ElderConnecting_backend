from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID

from database import get_db
from models import User, Notification
from schemas import NotificationCreate, NotificationUpdate, NotificationResponse
from auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/{user_id}", response_model=list[NotificationResponse])
def get_notifications(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifs = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .limit(50)
        .all()
    )
    return [NotificationResponse.model_validate(n) for n in notifs]


@router.post("/", response_model=NotificationResponse)
def create_notification(
    data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = Notification(
        user_id=data.user_id,
        type=data.type,
        message=data.message,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return NotificationResponse.model_validate(notif)


@router.put("/{notif_id}", response_model=NotificationResponse)
def update_notification(
    notif_id: UUID,
    data: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(notif, key, value)

    db.commit()
    db.refresh(notif)
    return NotificationResponse.model_validate(notif)


@router.put("/mark-all-read/{user_id}")
def mark_all_read(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.user_id == user_id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
