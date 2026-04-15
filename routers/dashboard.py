from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, timedelta

from database import get_db
from models import User, Vital, Medication, Appointment, Notification, Booking
from schemas import VitalResponse, MedicationResponse, AppointmentResponse, NotificationResponse, BookingResponse
from auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/elder")
def elder_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "elder":
        raise HTTPException(status_code=403, detail="Access denied: elder role required")

    uid = current_user.id

    # Latest vitals
    latest_vital = db.query(Vital).filter(Vital.user_id == uid).order_by(desc(Vital.date)).first()

    # Upcoming appointments
    upcoming = (
        db.query(Appointment)
        .filter(Appointment.user_id == uid, Appointment.status == "scheduled", Appointment.date >= date.today())
        .order_by(Appointment.date)
        .limit(5)
        .all()
    )

    # Today's medications
    today_meds = (
        db.query(Medication)
        .filter(Medication.user_id == uid)
        .order_by(desc(Medication.created_at))
        .limit(10)
        .all()
    )

    # Recent vitals for chart (last 7 days)
    week_ago = date.today() - timedelta(days=7)
    weekly_vitals = (
        db.query(Vital)
        .filter(Vital.user_id == uid, Vital.date >= week_ago)
        .order_by(Vital.date)
        .all()
    )

    # Unread notifications count
    unread_count = db.query(Notification).filter(
        Notification.user_id == uid, Notification.is_read == False
    ).count()

    return {
        "user": {"name": current_user.name, "role": current_user.role},
        "latest_vitals": VitalResponse.model_validate(latest_vital) if latest_vital else None,
        "upcoming_appointments": [AppointmentResponse.model_validate(a) for a in upcoming],
        "medications": [MedicationResponse.model_validate(m) for m in today_meds],
        "weekly_vitals": [VitalResponse.model_validate(v) for v in weekly_vitals],
        "unread_notifications": unread_count,
    }


@router.get("/family")
def family_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "family":
        raise HTTPException(status_code=403, detail="Access denied: family role required")

    # Get all elders (in a real app, would be linked elders)
    elders = db.query(User).filter(User.role == "elder").all()

    elder_summaries = []
    for elder in elders:
        latest_vital = db.query(Vital).filter(Vital.user_id == elder.id).order_by(desc(Vital.date)).first()
        recent_appointments = (
            db.query(Appointment)
            .filter(Appointment.user_id == elder.id)
            .order_by(desc(Appointment.date))
            .limit(3)
            .all()
        )
        # Recent alerts/SOS
        alerts = (
            db.query(Notification)
            .filter(Notification.user_id == elder.id, Notification.type.in_(["alert", "sos"]))
            .order_by(desc(Notification.created_at))
            .limit(5)
            .all()
        )
        elder_summaries.append({
            "elder": {"id": str(elder.id), "name": elder.name, "phone": elder.phone},
            "latest_vitals": VitalResponse.model_validate(latest_vital) if latest_vital else None,
            "recent_appointments": [AppointmentResponse.model_validate(a) for a in recent_appointments],
            "alerts": [NotificationResponse.model_validate(n) for n in alerts],
        })

    # Family notifications
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(10)
        .all()
    )

    return {
        "user": {"name": current_user.name, "role": current_user.role},
        "elders": elder_summaries,
        "notifications": [NotificationResponse.model_validate(n) for n in notifications],
    }


@router.get("/caregiver")
def caregiver_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "caregiver":
        raise HTTPException(status_code=403, detail="Access denied: caregiver role required")

    uid = current_user.id

    # Total patients (accepted bookings)
    total_patients = db.query(Booking).filter(
        Booking.caregiver_id == uid, Booking.status == "accepted"
    ).count()

    # Pending bookings
    pending_bookings = (
        db.query(Booking)
        .filter(Booking.caregiver_id == uid, Booking.status == "pending")
        .order_by(desc(Booking.created_at))
        .all()
    )

    # All bookings
    all_bookings = (
        db.query(Booking)
        .filter(Booking.caregiver_id == uid)
        .order_by(desc(Booking.created_at))
        .limit(20)
        .all()
    )

    # Enrich with patient names
    booking_responses = []
    for b in all_bookings:
        patient = db.query(User).filter(User.id == b.patient_id).first()
        resp = BookingResponse.model_validate(b)
        resp.patient_name = patient.name if patient else "Unknown"
        resp.caregiver_name = current_user.name
        booking_responses.append(resp)

    pending_responses = []
    for b in pending_bookings:
        patient = db.query(User).filter(User.id == b.patient_id).first()
        resp = BookingResponse.model_validate(b)
        resp.patient_name = patient.name if patient else "Unknown"
        resp.caregiver_name = current_user.name
        pending_responses.append(resp)

    return {
        "user": {"name": current_user.name, "role": current_user.role},
        "stats": {
            "total_patients": total_patients,
            "pending_bookings": len(pending_bookings),
            "total_bookings": len(all_bookings),
        },
        "pending_bookings": pending_responses,
        "all_bookings": booking_responses,
    }
