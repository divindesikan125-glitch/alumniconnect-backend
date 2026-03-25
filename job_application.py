from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
import enum


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class JobApplicationBase(BaseModel):
    cover_letter: Optional[str] = None
    resume_url: Optional[HttpUrl] = None


class JobApplicationCreate(JobApplicationBase):
    pass


class JobApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus 


class ApplicantInfo(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True


class JobApplicationResponse(BaseModel):
    id: int
    job_id: int
    applicant_id: int
    cover_letter: Optional[str]
    resume_url: Optional[str]
    status: str
    applied_at: datetime
    job_title: Optional[str] = None
    company_name: Optional[str] = None

    class Config:
        from_attributes = True


class JobApplicationWithApplicant(JobApplicationResponse):
    applicant: ApplicantInfo