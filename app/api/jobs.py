from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from .models.job import Job
from .models.job_application import JobApplication
from .models.user import User

from .schemas.job import JobCreate, JobResponse, JobUpdate
from .schemas.job_application import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationWithApplicant,
    JobApplicationStatusUpdate,
)

from .core.security import get_db, get_current_user

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# =========================================================
# 📝 POST A JOB
# =========================================================
@router.post("/", response_model=JobResponse)
def post_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["alumni", "institution"]:
        raise HTTPException(status_code=403, detail="Not allowed to post jobs")

    new_job = Job(
        title=data.title,
        description=data.description,
        company=data.company,
        location=data.location,
        job_type=data.job_type,           # Match Flutter Tag
        salary_range=data.salary_range,   # Match Flutter Tag
        graduation_year=data.graduation_year,
        owner_id=current_user.id
    )

    try:
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
    except Exception as e:
        db.rollback()
        print(f"DEBUG: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")

    return new_job

# =========================================================
# 🔍 GET JOBS (With Detailed Filters)
# =========================================================
@router.get("/", response_model=List[JobResponse])
def get_jobs(
    location: Optional[str] = None,
    company: Optional[str] = None,
    job_type: Optional[str] = None,
    graduation_year: Optional[int] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Invalid pagination values")

    # Only show active jobs on the main feed
    query = db.query(Job).filter(Job.is_active == True)

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if company:
        query = query.filter(Job.company.ilike(f"%{company}%"))
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if graduation_year:
        query = query.filter(Job.graduation_year == graduation_year)

    offset = (page - 1) * limit

    return (
        query.order_by(Job.posted_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

# =========================================================
# 🔄 UPDATE JOB
# =========================================================
@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to edit this job")

    # Dynamic update for all fields including new ones
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return job

# =========================================================
# 🗑️ DELETE JOB
# =========================================================
@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(job)
    db.commit()

    return {"message": "Job deleted successfully"}

# =========================================================
# 📩 APPLY TO JOB
# =========================================================
@router.post("/{job_id}/apply", response_model=JobApplicationResponse)
def apply_to_job(
    job_id: int,
    data: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "alumni":
        raise HTTPException(status_code=403, detail="Only alumni can apply")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot apply to your own job")

    application = JobApplication(
        job_id=job_id,
        applicant_id=current_user.id,
        cover_letter=data.cover_letter,
        resume_url=data.resume_url,
    )

    db.add(application)

    try:
        db.commit()
        db.refresh(application)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="You have already applied to this job."
        )

    return application

# =========================================================
# 📋 VIEW MY APPLICATIONS
# =========================================================
@router.get("/my/applications", response_model=List[JobApplicationResponse])
def get_my_applications(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offset = (page - 1) * limit

    # 1. Get the applications from the DB
    apps = (
        db.query(JobApplication)
        .filter(JobApplication.applicant_id == current_user.id)
        .order_by(JobApplication.applied_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # 2. THIS IS THE PART YOU NEED TO ADD/CHANGE:
    # We loop through the apps and "grab" the title/company from the linked Job
    for app in apps:
        app.job_title = app.job.title      # Accessing the relationship
        app.company_name = app.job.company # Accessing the relationship

    # 3. Now when this returns, the Schema will be full of data!
    return apps


