from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from .models.user import User
from .models.alumni import AlumniProfile, Connection
from .schemas.user import UserResponse
from .schemas.alumni import AlumniProfileResponse
from .core.security import get_current_alumni, get_current_institution, get_current_user, get_db

router = APIRouter(prefix="/alumni", tags=["Alumni"])

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_alumni)):
    # SQLAlchemy automatically loads the 'profile' relationship here
    return current_user


@router.post("/connect/{target_id}")
def send_request(target_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_alumni)):
    if target_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot connect with yourself")

    # Check for existing connection
    existing = db.query(Connection).filter(
        ((Connection.sender_id == current_user.id) & (Connection.receiver_id == target_id)) |
        ((Connection.sender_id == target_id) & (Connection.receiver_id == current_user.id))
    ).first()

    if existing:
        return {"message": "Already exists", "status": existing.status}

    # CREATE NEW CONNECTION
    new_conn = Connection(
        sender_id=current_user.id, 
        receiver_id=target_id, 
        status="pending" # Matches your Flutter logic
    )
    db.add(new_conn)
    db.commit()
    
    return {"message": "Request sent"}


@router.get("/connect/status/{target_id}")
def get_connection_status(
    target_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_alumni)
):
    conn = db.query(Connection).filter(
        ((Connection.sender_id == current_user.id) & (Connection.receiver_id == target_id)) |
        ((Connection.sender_id == target_id) & (Connection.receiver_id == current_user.id))
    ).first()

    if not conn:
        return {"status": "none"}
    
    # NEW LOGIC: Tell the frontend if they are the one who needs to ACCEPT
    if conn.status == "pending":
        if conn.receiver_id == current_user.id:
            return {"status": "request_received", "connection_id": conn.id}
        else:
            return {"status": "request_sent", "connection_id": conn.id}
    
    return {"status": conn.status, "connection_id": conn.id}


@router.get("/connect/pending")
def get_pending_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_alumni)):
    # 1. Fetch the raw connection records
    requests = db.query(Connection).filter(
        Connection.receiver_id == current_user.id,
        Connection.status == "pending"
    ).all()

    output = []
    for r in requests:
        # 2. Find the sender's name to build the 'content' string
        sender = db.query(User).filter(User.id == r.sender_id).first()
        sender_name = sender.full_name if sender else "Someone"

        # 3. Build the exact JSON structure the Flutter UI expects
        output.append({
            "connection_id": r.id,
            "type": "connection_request", # REQUIRED by your Flutter logic
            "content": f"{sender_name} wants to connect with you.", # REQUIRED by your Flutter logic
            "sender_id": r.sender_id
        })
    
    return output


@router.put("/connect/accept/{connection_id}")
def accept_connection(
    connection_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_alumni)
):
    # Only the receiver can accept the request
    conn = db.query(Connection).filter(
        Connection.id == connection_id, 
        Connection.receiver_id == current_user.id,
        Connection.status == "pending"
    ).first()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    conn.status = "accepted"
    db.commit()
    return {"message": "Connection accepted", "status": "accepted"}

@router.delete("/connect/reject/{connection_id}")
def reject_connection(
    connection_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_alumni)
):
    # Only the receiver can reject/delete the request
    conn = db.query(Connection).filter(
        Connection.id == connection_id, 
        Connection.receiver_id == current_user.id
    ).first()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    db.delete(conn)
    db.commit()
    return {"message": "Connection request declined"}

@router.get("/connect/status/{target_id}")
def get_connection_status(
    target_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_alumni)
):
    conn = db.query(Connection).filter(
        ((Connection.sender_id == current_user.id) & (Connection.receiver_id == target_id)) |
        ((Connection.sender_id == target_id) & (Connection.receiver_id == current_user.id))
    ).first()

    if not conn:
        return {"status": "none"}
    
    return {"status": conn.status, "connection_id": conn.id}

@router.get("/public", response_model=List[AlumniProfileResponse])
def get_public_directory(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_alumni)
):
    # 1. Fetch all alumni users
    users = db.query(User).filter(
        User.role == "alumni", 
        User.id != current_user.id
    ).all()

    output = []
    for u in users:
        # 2. Get the related profile (where the image lives)
        p = u.profile 
        
        # 3. Construct the merged response
        output.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name or "New Member",
            "graduation_year": u.graduation_year,  # From User table
            "department": u.department,            # From User table
            "profile_image_url": p.profile_image_url if p else None, # From Profile table
            "designation": p.designation if p else "Alumni",
            "company": p.company if p else "Not specified",
            "bio": p.bio if p else "No bio added yet",
            "skills": p.skills if p else ""
        })
    
    return output
    

@router.get("/institution", response_model=List[UserResponse])
def get_institution_alumni(
    db: Session = Depends(get_db),
    institution: User = Depends(get_current_institution)
):
    # Admins see the Full User object (including private fields + profile)
    return db.query(User).filter(
        User.institution_id == institution.id,
        User.role == "alumni"
    ).all()
