from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# In your User model
@property
def is_verified(self):
    # Check if there is any claimed record linked to this user ID
    return any(record.is_claimed for record in self.alumni_records)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    role = Column(String, nullable=False, index=True)
    is_verified = Column(Boolean, default=False)
    institution_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    institution_code = Column(String, nullable=True)
    graduation_year = Column(Integer, nullable=True) # This fixes your current error
    department = Column(String, nullable=True)      # Add this now to prevent the next error

    # Private fields we discussed (Staying here)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    # Relationship to the "Business Card"
    profile = relationship("AlumniProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # ==========================
    # Account Status
    # ==========================

    is_active = Column(Boolean, default=False)

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    activation_token = Column(String, nullable=True)
    activation_expires = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # ==========================
    # Relationships
    # ==========================

    # Alumni → Institution (self relationship)
    institution = relationship(
        "User",
        remote_side=[id],
        back_populates="alumni_members"
    )

    alumni_members = relationship(
        "User",
        back_populates="institution"
    )

    # ==========================
    # Jobs posted
    # ==========================

    jobs = relationship(
        "Job",
        back_populates="owner",
        foreign_keys="Job.owner_id",
        cascade="all, delete-orphan"
    )

    # ==========================
    # Events created
    # ==========================

    created_events = relationship(
        "Event",
        back_populates="creator",
        cascade="all, delete-orphan"
    )

    # ==========================
    # Job applications
    # ==========================

    job_applications = relationship(
        "JobApplication",
        back_populates="applicant",
        cascade="all, delete-orphan"
    )

    # ==========================
    # Event registrations
    # ==========================

    event_registrations = relationship(
        "EventRegistration",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # ==========================
    # Alumni records
    # ==========================

    alumni_records = relationship(
        "AlumniRecord",
        back_populates="user",
        foreign_keys="AlumniRecord.linked_user_id"
    )

    # ==========================
    # Chat system
    # ==========================

    sent_messages = relationship(
        "ChatMessage",
        foreign_keys="ChatMessage.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )

    received_messages = relationship(
        "ChatMessage",
        foreign_keys="ChatMessage.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )

    # ==========================
    # Soft Delete Helper
    # ==========================

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.is_active = False
