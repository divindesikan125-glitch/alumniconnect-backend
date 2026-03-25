from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

# Define the status options for a connection
class ConnectionStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Connection(Base):
    """This table tracks the relationship between two alumni"""
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(String, default="pending") # pending, accepted, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    # 🎓 Identity Info
    full_name = Column(String, nullable=False)
    profile_image_url = Column(String, nullable=True)
    graduation_year = Column(Integer, nullable=True)
    department = Column(String, nullable=True)

    # 💼 Professional Info
    designation = Column(String, nullable=True) 
    company = Column(String, nullable=True)      
    skills = Column(String, nullable=True)      
    bio = Column(String, nullable=True)

    # 🌐 Social Networking
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)

    # Relationship back to the User model
    user = relationship("User", back_populates="profile")
