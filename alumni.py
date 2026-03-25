from pydantic import BaseModel
from typing import Optional

# Ensure this name is AlumniProfileResponse
class AlumniProfileResponse(BaseModel):
    id: int
    email: Optional[str] = None
    full_name: str
    graduation_year: Optional[int] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    company: Optional[str] = None
    skills: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    connection_status: Optional[str] = None

    class Config:
        from_attributes = True