from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer

# This matches your existing Event schema
class EventDetail(BaseModel):
    id: int
    title: str
    location: str
    event_date: datetime
    description: str
    category: Optional[str] = "General"
    image_url: Optional[str] = None
    max_attendees: Optional[int] = None

    class Config:
        from_attributes = True

class EventRegistrationResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    event: Optional[EventDetail] = None
    registered_at: datetime


    class Config:
        from_attributes = True