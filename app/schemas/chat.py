from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# -------------------------
# Send Message (Input)
# -------------------------
class ChatMessageCreate(BaseModel):
    receiver_id: int
    message: str = Field(..., min_length=1, max_length=2000)

# -------------------------
# Message Response (The Bubbles)
# -------------------------
class ChatMessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    message: str
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True

# -------------------------
# NEW: Conversation List (The Chat List)
# -------------------------
# This matches the modified API we just wrote
class ConversationResponse(BaseModel):
    user_id: int
    full_name: str
    profile_image: Optional[str] = None
    last_message: str
    last_message_time: datetime
    unread_count: int

    class Config:
        from_attributes = True
