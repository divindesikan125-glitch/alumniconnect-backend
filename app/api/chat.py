from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict
import json

from .models.chat import ChatMessage
from .models.user import User
from .schemas.chat import ChatMessageCreate, ChatMessageResponse
from .core.security import get_current_user, get_db, get_user_from_token # Added get_user_from_token

router = APIRouter(prefix="/chat", tags=["Chat"])

# ============================================================
# 🌐 WebSocket Connection Manager
# ============================================================
class ConnectionManager:
    def __init__(self):
        # Maps user_id -> WebSocket object
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            # This sends the message instantly if the user is online
            await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

# ============================================================
# 🔌 WebSocket Endpoint
# ============================================================
@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    # Authenticate user from the token in the URL
    user = await get_user_from_token(token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user.id, websocket)
    
    try:
        while True:
            # Keeps the connection open and waits for client data (heartbeats)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user.id)

# ============================================================
# 📩 Send Message (Modified to include Real-time Push)
# ============================================================
@router.post("/send", response_model=ChatMessageResponse)
async def send_message( # Changed to async
    data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")

    receiver = db.query(User).filter(User.id == data.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    new_msg = ChatMessage(
        sender_id=current_user.id,
        receiver_id=data.receiver_id,
        message=data.message
    )

    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    # --- REAL-TIME PUSH LOGIC ---
    # Prepare the payload for the frontend
    payload = {
        "id": new_msg.id,
        "sender_id": new_msg.sender_id,
        "receiver_id": new_msg.receiver_id,
        "message": new_msg.message,
        "created_at": new_msg.created_at.isoformat(),
        "is_read": new_msg.is_read
    }
    
    # Push to receiver instantly if they are online
    await manager.send_personal_message(payload, data.receiver_id)

    return new_msg

# ============================================================
# 📥 Conversation List (Optimized for Frontend UI)
# ============================================================
@router.get("/conversations")
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch all messages involving the current user
    messages = (
        db.query(ChatMessage)
        .filter(
            (ChatMessage.sender_id == current_user.id) |
            (ChatMessage.receiver_id == current_user.id)
        )
        .order_by(ChatMessage.created_at.desc())
        .all()
    )

    conversations = {}
    
    for msg in messages:
        other_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        
        if other_id not in conversations:
            # 2. Fetch the other user AND their profile
            other_user = db.query(User).filter(User.id == other_id).first()
            
            # CRITICAL: Access the profile relationship
            profile = other_user.profile if other_user else None

            # 3. Count unread messages
            unread_count = db.query(ChatMessage).filter(
                ChatMessage.sender_id == other_id,
                ChatMessage.receiver_id == current_user.id,
                ChatMessage.is_read == False
            ).count()

            conversations[other_id] = {
                "user_id": other_id,
                # Use profile fields to match your /me endpoint logic
                "full_name": profile.full_name if profile else "Unknown User",
                "profile_image": profile.profile_image_url if profile else None,
                "last_message": msg.message,
                "last_message_time": msg.created_at.isoformat(),
                "unread_count": unread_count
            }

    return list(conversations.values())

# ============================================================
# 💬 Get Chat History (Marks as Read Automatically)
# ============================================================
@router.get("/history/{user_id}", response_model=List[ChatMessageResponse])
def get_chat_history(
    user_id: int,
    page: int = 1,
    limit: int = 50, # Increased limit for better scrolling
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    offset = (page - 1) * limit

    messages = (
        db.query(ChatMessage)
        .filter(
            or_(
                and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == user_id),
                and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == current_user.id)
            )
        )
        .order_by(ChatMessage.created_at.asc()) # Ascending so newest is at bottom
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Automatically mark messages from the other user as "read"
    db.query(ChatMessage).filter(
        ChatMessage.sender_id == user_id,
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False
    ).update({"is_read": True}, synchronize_session=False)

    db.commit()
    return messages

# ============================================================
# 🔔 Global Unread Count (For AppBar Badge)
# ============================================================
@router.get("/unread")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    count = db.query(ChatMessage).filter(
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False
    ).count()

    return {"unread_count": count}

@router.post("/read/{sender_id}")
def mark_as_read(
    sender_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    db.query(ChatMessage).filter(
        ChatMessage.sender_id == sender_id,
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "Read"}
