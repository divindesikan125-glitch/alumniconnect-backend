from datetime import datetime
from pydantic import BaseModel, EmailStr # EmailStr validates email format
from typing import Optional

# -------------------------
# Job Creation (Input from Flutter)
# -------------------------
class JobCreate(BaseModel):
    title: str
    description: str
    company: str
    location: str
    job_type: Optional[str] = "Full-time"
    salary_range: Optional[str] = "Negotiable"
    graduation_year: Optional[int] = None
    contact_email: Optional[EmailStr] = None # Added for validation

# -------------------------
# Job Update (Editing)
# -------------------------
class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None
    graduation_year: Optional[int] = None
    contact_email: Optional[EmailStr] = None # Added here too

# -------------------------
# Job Response (Output to Flutter)
# -------------------------
class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    company: str
    location: str
    job_type: Optional[str] = "Full-time"
    salary_range: Optional[str] = "Negotiable"
    graduation_year: Optional[int] = None
    contact_email: Optional[str] = None 
    owner_id: int
    posted_at: datetime

    class Config:
        from_attributes = True