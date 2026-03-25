from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from .models.user import User
from .schemas.user import UserResponse
from .core.security import get_db

router = APIRouter(prefix="/public/alumni", tags=["Public Alumni"])


# =========================================================
# PUBLIC ALUMNI DIRECTORY (With Filters + Pagination)
# =========================================================
@router.get("/", response_model=List[UserResponse])
def public_alumni_view(
    graduation_year: Optional[int] = None,
    department: Optional[str] = None,
    company: Optional[str] = None,
    job_title: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Invalid pagination values")

    query = db.query(User).filter(
        User.role == "alumni",
        User.is_active == True,
    )

    if graduation_year:
        query = query.filter(User.graduation_year == graduation_year)

    if department:
        query = query.filter(User.department.ilike(f"%{department}%"))

    if company:
        query = query.filter(User.company.ilike(f"%{company}%"))

    if job_title:
        query = query.filter(User.job_title.ilike(f"%{job_title}%"))

    offset = (page - 1) * limit

    return (
        query.order_by(User.graduation_year.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
