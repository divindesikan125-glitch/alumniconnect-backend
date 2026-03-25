from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from .schemas.user import AlumniProfileResponse # Import your existing profile schema

class AlumniRecordCreate(BaseModel):
    full_name: str
    email: EmailStr
    enrollment_id: Optional[str] = None
    graduation_year: Optional[int] = None
    department: Optional[str] = None
    degree_type: Optional[str] = None

# app/schemas/alumni_record.py

class AlumniRecordResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    enrollment_id: Optional[str] = None
    graduation_year: Optional[int] = None
    department: Optional[str] = None
    
    # --- ADD THESE FOR PRIVATE DATA ---
    phone_number: Optional[str] = None
    address: Optional[str] = None
    
    # --- ADD THIS FOR PUBLIC PROFESSIONAL DATA ---
    profile: Optional[AlumniProfileResponse] = None 
    
    is_claimed: bool
    linked_user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
