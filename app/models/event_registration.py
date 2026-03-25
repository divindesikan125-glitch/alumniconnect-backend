from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .db.database import Base


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "user_id",
            name="unique_event_registration"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    registered_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    event = relationship(
        "Event",
        back_populates="registrations",
        passive_deletes=True
    )

    user = relationship(
        "User",
        back_populates="event_registrations",
        passive_deletes=True
    )
