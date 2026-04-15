from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from uuid import UUID

from database import get_db
from models import User, Appointment, Booking, Vital, Notification, VideoSession
from schemas import UserResponse
from auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied: admin role required")
    return current_user


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    total_elders = db.query(User).filter(User.role == "elder").count()
    total_families = db.query(User).filter(User.role == "family").count()
    total_caregivers = db.query(User).filter(User.role == "caregiver").count()
    total_appointments = db.query(Appointment).count()
    total_bookings = db.query(Booking).count()
    total_video_sessions = db.query(VideoSession).count()

    return {
        "total_elders": total_elders,
        "total_families": total_families,
        "total_caregivers": total_caregivers,
        "total_users": total_elders + total_families + total_caregivers,
        "total_appointments": total_appointments,
        "total_bookings": total_bookings,
        "total_video_sessions": total_video_sessions,
    }


@router.get("/users", response_model=list[UserResponse])
def list_users(
    role: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.order_by(desc(User.created_at)).limit(100).all()
    return [UserResponse.model_validate(u) for u in users]


@router.delete("/users/{user_id}")
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
