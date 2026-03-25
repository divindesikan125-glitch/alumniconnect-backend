from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

from .schemas.alumni import AlumniProfileResponse

# ============================================================
# 🏫 Institution Registration Schema
# ============================================================
class InstitutionRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


# ============================================================
# 🎓 Alumni Self Registration Schema
# ============================================================
class AlumniRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    institution_code: str
    graduation_year: Optional[int] = None
    department: Optional[str] = None


# ============================================================
# 🔓 Activation Schema
# ============================================================
class ActivateAccount(BaseModel):
    token: str
    password: str = Field(..., min_length=8, max_length=128)


# ============================================================
# 🔐 Login Schema
# ============================================================
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


# ============================================================
# 📝 Profile Update Schema (New)
# ============================================================
# This allows users to update their professional info after login
# 1. This handles the data INSIDE the "profile" block
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    graduation_year: Optional[int] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    company: Optional[str] = None
    skills: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    profile_image_url: Optional[str] = None

# 2. This is the main box that Flutter sends
class UserUpdate(BaseModel):
    phone_number: Optional[str] = None
    address: Optional[str] = None
    # CRITICAL: You MUST have this line to accept the "profile" key from Flutter
    profile: Optional[ProfileUpdate] = None

# ============================================================
# 👤 Response Schema (Updated)
# ============================================================
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    is_verified: bool = False
    created_at: datetime
    
    # --- PRIVATE DATA (Account Table) ---
    phone_number: Optional[str] = None
    address: Optional[str] = None
    
    # --- NESTED PROFESSIONAL DATA ---
    # This automatically maps the 'profile' relationship from your model
    profile: Optional[AlumniProfileResponse] = None 

    class Config:
        from_attributes = True
