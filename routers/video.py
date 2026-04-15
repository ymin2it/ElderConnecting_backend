import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID

from database import get_db
from models import User, VideoSession
from schemas import VideoSessionCreate, VideoSessionUpdate, VideoSessionResponse
from auth import get_current_user

router = APIRouter(prefix="/api/video", tags=["Video Consultation"])


@router.post("/session", response_model=VideoSessionResponse)
def create_session(
    data: VideoSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room_id = f"ec-room-{uuid.uuid4().hex[:12]}"
    session = VideoSession(
        user_id=current_user.id,
        doctor=data.doctor,
        room_id=room_id,
        date=data.date,
        time=data.time,
        duration=data.duration,
        status="scheduled",
        notes=data.notes,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return VideoSessionResponse.model_validate(session)


@router.get("/history/{user_id}", response_model=list[VideoSessionResponse])
def get_history(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(VideoSession)
        .filter(VideoSession.user_id == user_id)
        .order_by(desc(VideoSession.created_at))
        .limit(50)
        .all()
    )
    return [VideoSessionResponse.model_validate(s) for s in sessions]


@router.put("/session/{session_id}", response_model=VideoSessionResponse)
def update_session(
    session_id: UUID,
    data: VideoSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(VideoSession).filter(VideoSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)

    db.commit()
    db.refresh(session)
    return VideoSessionResponse.model_validate(session)
