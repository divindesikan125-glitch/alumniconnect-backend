from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import secrets

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    InstitutionRegister,
    AlumniRegister,
    ActivateAccount,
)
from app.core.security import get_current_user, hash_password, verify_password, create_access_token
from app.utils.send_email import send_activation_email
from app.models.alumni_record import AlumniRecord

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# 🏫 Institution Registration
# ============================================================
@router.post("/register-institution")
async def register_institution(data: InstitutionRegister, db: Session = Depends(get_db)):

    existing = db.query(User).filter(
        User.email == data.email,
        User.is_deleted == False
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    institution_code = secrets.token_hex(4)

    new_institution = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role="institution",
        institution_code=institution_code,
        is_active=True
    )

    db.add(new_institution)
    db.commit()
    db.refresh(new_institution)

    return {
        "message": "Institution registered successfully",
        "institution_code": institution_code
    }


# ============================================================
# 🎓 Alumni Registration
# ============================================================
@router.post("/register-alumni")
async def register_alumni(user: AlumniRegister, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
        User.email == user.email,
        User.is_deleted == False
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    token = secrets.token_hex(16)

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        role="alumni",
        institution_code=user.institution_code,
        graduation_year=user.graduation_year,
        department=user.department,
        activation_token=token,
        activation_expires=datetime.utcnow() + timedelta(hours=24),
        is_active=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    await send_activation_email(new_user.email, token)

    return {
        "message": "Registered successfully. Check your email to activate your account."
    }


# ============================================================
# 🔓 Activate Account
# ============================================================
@router.post("/activate")
def activate_account(data: ActivateAccount, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.activation_token == data.token,
        User.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid activation token")

    if user.is_active:
        raise HTTPException(status_code=400, detail="Account already activated")

    if user.activation_expires and user.activation_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Activation token expired")

    user.hashed_password = hash_password(data.password)
    user.is_active = True
    user.activation_token = None
    user.activation_expires = None

    db.commit()

    return {"message": "Account activated successfully"}


# ============================================================
# 🔐 Login
# ============================================================
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == form_data.username,
        User.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not activated")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name, # Added this
        "user_id": user.id  # <--- Add this line!
}
