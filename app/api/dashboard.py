from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from .db.database import get_db
from .models.alumni_record import AlumniRecord # Import your record model
from .models.user import User
from .models.job import Job
from .models.event import Event
from .models.job_application import JobApplication, ApplicationStatus
from .models.event_registration import EventRegistration
from .core.security import (
    get_current_user,
    get_current_institution,
    get_current_alumni,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# ===========================================================
# 👤 Any logged-in user

# ============================================================

@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):

    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
    }

# ============================================================
# 🏫 Institution Dashboard
# ============================================================
@router.get("/institution")
def institution_dashboard(
    current_user: User = Depends(get_current_institution),
    db: Session = Depends(get_db),
):
    total_jobs = db.query(Job).filter(
        Job.posted_by_id == current_user.id
    ).count()
    total_applications = (
        db.query(JobApplication)
        .join(Job)
        .filter(Job.owner_id== current_user.id)
        .count()
    )
    accepted = (
        db.query(JobApplication)
        .join(Job)
        .filter(
            Job.owner_id == current_user.id,
            JobApplication.status == ApplicationStatus.accepted,
        )
        .count()
    )
    pending = (
        db.query(JobApplication)
        .join(Job)
        .filter(
            Job.owner_id == current_user.id,
            JobApplication.status == ApplicationStatus.pending,
        )
        .count()
    )
    rejected = (
        db.query(JobApplication)
        .join(Job)
        .filter(
            Job.owner_id == current_user.id,
            JobApplication.status == ApplicationStatus.rejected,
        )
        .count()
    )
    total_events = db.query(Event).filter(
        Event.owner_id == current_user.id
    ).count()
    total_registrations = (
        db.query(EventRegistration)
        .join(Event)
        .filter(Event.owner_id == current_user.id)
        .count()
    )
    upcoming_events = (
        db.query(Event)
        .filter(
            Event.owner_id == current_user.id,
            Event.event_date > datetime.utcnow(),
        )
        .count()
    )

    return {
        "message": f"Welcome Institution {current_user.full_name}",
        "jobs": {
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "accepted": accepted,
            "pending": pending,
            "rejected": rejected,
        },
        "events": {
            "total_events": total_events,
            "total_registrations": total_registrations,
            "upcoming_events": upcoming_events,
        },
    }
# ============================================================
# 🎓 Alumni Dashboard
# ============================================================
@router.get("/alumni")
def alumni_dashboard(
    current_user: User = Depends(get_current_alumni),
    db: Session = Depends(get_db),
):
    recent_jobs = (
        db.query(Job)
        .filter(Job.graduation_year == current_user.graduation_year)
        .order_by(Job.posted_at.desc())
        .limit(5)
        .all()
    )
    recent_events = (
        db.query(Event)
        .order_by(Event.event_date.desc())
        .limit(5)
        .all()
    )
    return {
        "message": f"Welcome Alumni {current_user.full_name}",
        "recent_jobs": recent_jobs,
        "recent_events": recent_events,
    }

# ============================================================
# 📊 Institution Analytics (Scoped Properly)
# ============================================================
@router.get("/institution/analytics-v2")
def get_comprehensive_analytics(
    current_user: User = Depends(get_current_institution),
    db: Session = Depends(get_db),
):
    # 1. Verification Funnel
    total_records = db.query(AlumniRecord).filter(
        AlumniRecord.institution_id == current_user.id
    ).count()
    
    verified_alumni = db.query(AlumniRecord).filter(
        AlumniRecord.institution_id == current_user.id,
        AlumniRecord.is_claimed == True
    ).count()

    # 2. Jobs Breakdown
    inst_jobs = db.query(Job).filter(Job.owner_id == current_user.id).count()
    
    alumni_jobs = db.query(Job).join(User, Job.owner_id == User.id).filter(
        User.role == "alumni",
        User.institution_id == current_user.id
    ).count()

    # 3. Events Breakdown
    inst_events = db.query(Event).filter(Event.owner_id == current_user.id).count()
    
    alumni_events = db.query(Event).join(User, Event.owner_id == User.id).filter(
        User.role == "alumni",
        User.institution_id == current_user.id
    ).count()

    # 4. Top 5 Power Alumni (Leaderboard) - FIXED SQL LOGIC
    # We use subqueries to prevent counts from multiplying due to multiple joins
    job_counts = db.query(
        Job.owner_id, 
        func.count(Job.id).label('j_count')
    ).group_by(Job.owner_id).subquery()

    event_counts = db.query(
        Event.owner_id, 
        func.count(Event.id).label('e_count')
    ).group_by(Event.owner_id).subquery()

    top_contributors_raw = db.query(
        User.full_name,
        User.id,
        (func.coalesce(job_counts.c.j_count, 0) + 
         func.coalesce(event_counts.c.e_count, 0)).label('total_activity')
    ).outerjoin(job_counts, User.id == job_counts.c.owner_id)\
     .outerjoin(event_counts, User.id == event_counts.c.owner_id)\
     .filter(
         User.institution_id == current_user.id, 
         User.role == "alumni"
     )\
     .order_by(
         (func.coalesce(job_counts.c.j_count, 0) + 
          func.coalesce(event_counts.c.e_count, 0)).desc()
     )\
     .limit(5).all()

    return {
        "verification_stats": {
            "total_records": total_records,
            "verified": verified_alumni,
            "pending": total_records - verified_alumni,
            "percentage": (verified_alumni / total_records * 100) if total_records > 0 else 0
        },
        "jobs_analytics": {
            "posted_by_institution": inst_jobs,
            "posted_by_alumni": alumni_jobs,
            "total": inst_jobs + alumni_jobs
        },
        "events_analytics": {
            "posted_by_institution": inst_events,
            "posted_by_alumni": alumni_events,
            "total": inst_events + alumni_events
        },
        "top_contributors": [
            {"name": row[0], "user_id": row[1], "posts": row[2]} 
            for row in top_contributors_raw if row[2] > 0
        ]
    }

@router.post("/broadcast")
def send_broadcast(
    message: str, 
    current_user: User = Depends(get_current_institution), 
    db: Session = Depends(get_db)
):
    # Here you would typically save to a 'Notices' table
    # For now, we'll return success to test the UI
    return {"status": "success", "detail": f"Message sent to all alumni of {current_user.full_name}"}
