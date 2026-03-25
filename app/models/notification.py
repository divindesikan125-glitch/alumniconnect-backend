from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.db.database import Base  # Ensure this path matches your project structure
import datetime

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    notification_type = Column(String) # e.g., "chat", "event"
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
