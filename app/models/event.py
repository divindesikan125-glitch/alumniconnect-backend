from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .db.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    # Core Info
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=False, index=True)
    
    # --- NEW FIELDS FOR PREMIUM UI ---
    # e.g., "Workshop", "Reunion", "Webinar"
    category = Column(String, nullable=True, default="General")
    
    # URL for the event banner image
    image_url = Column(String, nullable=True)
    
    # For "Only 5 spots left!" logic in Flutter
    max_attendees = Column(Integer, nullable=True)
    # ----------------------------------

    event_date = Column(DateTime, nullable=False, index=True)

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    creator = relationship(
        "User",
        back_populates="created_events",
        passive_deletes=True
    )

    registrations = relationship(
        "EventRegistration",
        back_populates="event",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    is_deleted = Column(Boolean, default=False)
