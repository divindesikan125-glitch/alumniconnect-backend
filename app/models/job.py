from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .db.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Core Info
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    company = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False, index=True)

    # --- NEW FIELDS FOR DETAILED UI ---
    # e.g., "Full-time", "Remote", "Contract"
    job_type = Column(String, nullable=True, default="Full-time") 
    
    # e.g., "$100k - $120k" or "Negotiable"
    salary_range = Column(String, nullable=True) 
    
    # Allows users to close a job without deleting it
    is_active = Column(Boolean, default=True, nullable=False)
    # ----------------------------------

    graduation_year = Column(Integer, nullable=True, index=True)
    posted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # User who posted the job
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # ==========================
    # Relationships
    # ==========================

    owner = relationship(
        "User",
        back_populates="jobs",
        foreign_keys=[owner_id]
    )

    applications = relationship(
        "JobApplication",
        back_populates="job",
        cascade="all, delete-orphan"
    )
