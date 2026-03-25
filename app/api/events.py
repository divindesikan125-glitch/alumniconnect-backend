from email.mime import image
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
import shutil
import os
import cloudinary.uploader  # Add this
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime, timezone

from app.models.event import Event
from app.models.event_registration import EventRegistration
from app.models.user import User

# Ensure EventUpdate is imported from your schemas
from app.schemas.event import EventCreate, EventUpdate, EventResponse
from app.schemas.event_registration import EventRegistrationResponse

from app.core.security import get_db, get_current_user


router = APIRouter(prefix="/events", tags=["Events"])

# =========================================================
# CREATE EVENT
# =========================================================
import cloudinary.uploader # Ensure this is at the top

import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime, timezone

# Ensure this is exactly how your route starts
@router.post("/", response_model=EventResponse)
async def create_event(
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    category: str = Form(...),
    event_date: str = Form(...),
    max_attendees: str = Form(...),
    image: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Permission Check
    if current_user.role not in ["alumni", "institution"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    
    if event_date < datetime.now(timezone.utc).date():
        raise HTTPException(
            status_code=400, 
            detail="Cannot create an event in the past"
        )

    try:
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            image.file, 
            folder="alumni_events"
        )
        secure_url = upload_result.get("secure_url")

        # Create Database Object
        new_event = Event(
            title=title,
            description=description,
            location=location,
            category=category,
            image_url=secure_url,
            max_attendees=int(max_attendees),
            event_date=datetime.fromisoformat(event_date),
            owner_id=current_user.id
        )
        
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return new_event

    except Exception as e:
        db.rollback()
        print(f"Error: {e}") # Log the error to your terminal
        raise HTTPException(status_code=500, detail=str(e))


        
# =========================================================
# GET ALL EVENTS (Paginated + Creator Info)
# =========================================================
@router.get("/", response_model=List[EventResponse])
def get_events(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    return (
        db.query(Event)
        .options(joinedload(Event.creator).joinedload(User.profile))
        .filter(Event.is_deleted == False)
        .order_by(Event.event_date.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


# =========================================================
# UPDATE EVENT (Owner Only - Partial Updates Supported)
# =========================================================
@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    max_attendees: Optional[int] = Form(None),
    event_date: Optional[datetime] = Form(None),
    image: Optional[UploadFile] = File(None), # This receives the actual file
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 1. Handle File Saving (If a new file is uploaded)
    if image:
        try:
            upload_result = cloudinary.uploader.upload(
                image.file, 
                folder="alumni_events",
                transformation=[{"width": 800, "height": 450, "crop": "fill"}]
            )
            # This replaces the old /static/ local path logic
            event.image_url = upload_result.get("secure_url")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image update failed: {str(e)}")

    # 2. Update Text Fields
    if title: event.title = title
    if description: event.description = description
    if location: event.location = location
    if category: event.category = category
    if max_attendees: event.max_attendees = max_attendees
    if event_date: event.event_date = event_date

    db.commit()
    db.refresh(event)
    return event


# =========================================================
# DELETE EVENT (Owner Only)
# =========================================================
@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this event")

    db.delete(event)
    db.commit()
    return {"message": "Event deleted successfully"}


# =========================================================
# REGISTER FOR EVENT (With Capacity Check)
# =========================================================
@router.post("/{event_id}/register", response_model=EventRegistrationResponse)
def register_for_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot register for your own event")

    # Capacity Logic
    if event.max_attendees:
        current_registrations = db.query(EventRegistration).filter(
            EventRegistration.event_id == event_id
        ).count()
        
        if current_registrations >= event.max_attendees:
            raise HTTPException(status_code=400, detail="This event is fully booked.")

    registration = EventRegistration(
        event_id=event_id,
        user_id=current_user.id,
    )

    db.add(registration)
    try:
        db.commit()
        db.refresh(registration)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Already registered for this event.")

    return registration

# Move this ABOVE @router.get("/{event_id}") or other dynamic routes

@router.get("/registrations/me", response_model=List[EventRegistrationResponse])
def get_my_registrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    registrations = (
        db.query(EventRegistration)
        .options(joinedload(EventRegistration.event))
        .filter(EventRegistration.user_id == current_user.id)
        .order_by(EventRegistration.registered_at.desc())
        .all()
    )
    return registrations


# =========================================================
# VIEW EVENT ATTENDEES (Owner Only)
# =========================================================
@router.get("/{event_id}/attendees", response_model=List[EventRegistrationResponse])
def event_attendees(
    event_id: int,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event or event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view these attendees")

    offset = (page - 1) * limit
    return (
        db.query(EventRegistration)
        .filter(EventRegistration.event_id == event_id)
        .order_by(EventRegistration.registered_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

# =========================================================
# VIEW MY REGISTRATIONS (Current User Only)
# =========================================================
@router.get("/registrations/me", response_model=List[EventRegistrationResponse])
def get_my_registrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # This fetches all registrations for the logged-in user
    # joinedload(EventRegistration.event) ensures the event details are included in the JSON
    registrations = (
        db.query(EventRegistration)
        .options(joinedload(EventRegistration.event))
        .filter(EventRegistration.user_id == current_user.id)
        .order_by(EventRegistration.registered_at.desc())
        .all()
    )
    
    return registrations
