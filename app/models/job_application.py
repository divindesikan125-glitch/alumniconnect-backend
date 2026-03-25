from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    DateTime,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class JobApplication(Base):
    __tablename__ = "job_applications"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "applicant_id",
            name="unique_job_application"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    applicant_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    cover_letter = Column(String, nullable=True)
    resume_url = Column(String, nullable=True)

    status = Column(
        Enum(ApplicationStatus),
        default=ApplicationStatus.pending,
        nullable=False,
        index=True
    )

    applied_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    job = relationship(
        "Job",
        back_populates="applications",
        passive_deletes=True
    )

    applicant = relationship(
        "User",
        back_populates="job_applications",
        passive_deletes=True
    )
