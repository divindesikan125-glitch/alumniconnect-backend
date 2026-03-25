from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Boolean,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class AlumniRecord(Base):
    __tablename__ = "alumni_records"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- Identification Pillars ---
    # Essential for matching records during registration
    enrollment_id = Column(String, unique=True, index=True, nullable=True) 
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)

    # --- Academic Pillars ---
    graduation_year = Column(Integer, nullable=True, index=True)
    department = Column(String, nullable=True, index=True)
    degree_type = Column(String, nullable=True) # e.g., B.Tech, MBA

    # --- Professional Pillars (Added for Stats) ---
    current_company = Column(String, nullable=True)
    current_designation = Column(String, nullable=True)
    location_city = Column(String, nullable=True)

    # --- System & Relationships ---
    institution_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    linked_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True
    )

    is_claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "enrollment_id", "institution_id", name="unique_enrollment_per_inst"
        ),
    )

    institution = relationship("User", foreign_keys=[institution_id])
    user = relationship("User", foreign_keys=[linked_user_id])
