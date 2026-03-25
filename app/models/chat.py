from sqlalchemy import Boolean, Column, Index, Integer,String, ForeignKey, DateTime,Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    
    __table_args__ = (
        Index("idx_chat_users", "sender_id", "receiver_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    sender_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    receiver_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    message = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_read = Column(Boolean, default=False)

    sender = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_messages"
    )

    receiver = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_messages"
    )
