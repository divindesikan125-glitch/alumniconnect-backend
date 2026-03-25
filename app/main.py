# app/main.py
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .db.database import engine, Base
# --- CRITICAL: Added alumni to models so the table is created ---
from .models import user, alumni, job, event, chat as chat_model 
from .models.user import User
from .models.alumni import Connection
from .models.alumni_record import AlumniRecord

# Routers
from .api.auth import router as auth_router
from .api.jobs import router as jobs_router
from .api.users import router as users_router
from .api.dashboard import router as dashboard_router
from .api.alumni_records import router as alumni_records_router
from .api import alumni as alumni_api
from .api.events import router as events_router
from .api import chat as chat_api

# Security
from .core.security import get_current_user, get_db

# -------------------------
# Setup Directories
# -------------------------
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("static/events"):
    os.makedirs("static/events")

# Initialize app
app = FastAPI(title="Alumni Connect API")

# -------------------------
# Static Files
# -------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------
# CORS middleware
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Create all tables (Includes the new AlumniProfile table)
# -------------------------
Base.metadata.create_all(bind=engine)

# -------------------------
# Include routers
# -------------------------
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(users_router)
app.include_router(dashboard_router)
app.include_router(alumni_records_router)
app.include_router(alumni_api.router)
app.include_router(events_router)
app.include_router(chat_api.router)

# -------------------------
# Root endpoint
# -------------------------
@app.get("/")
def root():
    return {"message": "Alumni Connect API Running"}

# -------------------------
# Get current logged-in user (Updated for Two-Table Logic)
# -------------------------
@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Root level /me endpoint. Note: It's better to use /users/me, 
    but we've updated this to pull from the 'profile' relationship.
    """
    profile = current_user.profile
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "full_name": profile.full_name if profile else None,
        "graduation_year": profile.graduation_year if profile else None,
        "department": profile.department if profile else None,
        "designation": profile.designation if profile else None, 
        "company": profile.company if profile else None,
        "profile_image_url": profile.profile_image_url if profile else None,
    }

@app.get("/debug-user")
def debug_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "has_profile": current_user.profile is not None
    }
