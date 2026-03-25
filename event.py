from pydantic import BaseModel, Field, field_validator, HttpUrl
from datetime import datetime
from typing import Optional

# -------------------------
# Event Creation (Input)
# -------------------------
class EventCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    location: str = Field(..., min_length=2, max_length=300)
    event_date: datetime
    
    # NEW FIELDS FOR UI DETAILING
    category: Optional[str] = Field("General", max_length=50) # e.g., Workshop, Reunion
    image_url: Optional[str] = None                           # URL for banner
    max_attendees: Optional[int] = Field(None, ge=1)          # Capacity limit
   

# -------------------------
# Event Update (Partial Input)
# -------------------------
class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    location: Optional[str] = Field(None, min_length=2, max_length=300)
    event_date: Optional[datetime] = None
    
    # NEW FIELDS FOR UI DETAILING
    category: Optional[str] = Field(None, max_length=50)
    image_url: Optional[str] = None
    max_attendees: Optional[int] = Field(None, ge=1)

    class Config:
        from_attributes = True

# -------------------------
# Event Owner Detail
# -------------------------
class EventOwner(BaseModel):
    id: int
    full_name: Optional[str] = "Alumni Member"
    email: str
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True

# -------------------------
# Event Response (Output to Flutter)
# -------------------------
class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str
    event_date: datetime
    
    # NEW FIELDS
    category: Optional[str] = "General"
    image_url: Optional[str] = None
    max_attendees: Optional[int] = None
    
    created_at: Optional[datetime]
    creator: EventOwner

    class Config:
        from_attributes = True