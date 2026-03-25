from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.alumni import AlumniProfile # <--- New Import
from app.schemas.user import UserResponse, UserUpdate 
from app.core.security import get_current_user, get_db
import cloudinary.uploader

router = APIRouter(prefix="/users", tags=["Users"])

# =========================================================
# 👤 GET CURRENT USER (The "Me" Endpoint)
# =========================================================
@router.get("/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if a profile exists for this user
    if not current_user.profile:
        print(f"DEBUG: Creating missing profile for {current_user.full_name}")
        new_profile = AlumniProfile(
            user_id=current_user.id,
            full_name=current_user.full_name,
            # Pull these from the User table so the Directory isn't empty
            graduation_year=current_user.graduation_year,
            department=current_user.department
        )
        db.add(new_profile)
        db.commit()
        db.refresh(current_user)
    
    return current_user

# =========================================================
# 📝 UPDATE PROFILE INFO
# =========================================================
@router.put("/me", response_model=UserUpdate)
def update_profile(
    profile_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        update_dict = profile_data.model_dump(exclude_unset=True)
        account_fields = ["phone_number", "address", "full_name"]
        
        # 1. Ensure Profile exists and is attached
        profile = current_user.profile
        if not profile:
            profile = AlumniProfile(user_id=current_user.id, full_name=current_user.full_name)
            db.add(profile)
            db.flush() # Give it an ID before updating fields
            current_user.profile = profile

        # 2. Update the fields
        for key, value in update_dict.items():
            if key in account_fields:
                setattr(current_user, key, value)
            
            # FIX: Handle nested profile data correctly
            elif key == "profile" and value:
                # Convert Pydantic object to dict if necessary
                p_data = value if isinstance(value, dict) else value.model_dump(exclude_unset=True)
                for p_key, p_value in p_data.items():
                    if hasattr(profile, p_key):
                        setattr(profile, p_key, p_value)

        db.commit()
        db.refresh(current_user)
        return current_user

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
    
# =========================================================
# 📸 UPLOAD PROFILE IMAGE
# =========================================================
@router.put("/me/profile-image")
def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Upload to Cloudinary
        result = cloudinary.uploader.upload(file.file)
        image_url = result["secure_url"]
        print(f"DEBUG: Cloudinary Upload Successful: {image_url}")

        # 2. Find the profile explicitly by user_id
        profile = db.query(AlumniProfile).filter(AlumniProfile.user_id == current_user.id).first()

        if not profile:
            # Create the profile if it somehow doesn't exist yet
            profile = AlumniProfile(user_id=current_user.id, full_name=current_user.full_name)
            db.add(profile)
        
        # 3. Save the URL to the database
        profile.profile_image_url = image_url
        db.commit()
        db.refresh(profile)

        return {"profile_image_url": image_url}
        
    except Exception as e:
        db.rollback()
        print(f"DATABASE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Image upload failed")
# =========================================================
# 🗑️ DELETE PROFILE IMAGE
# =========================================================
@router.delete("/me/profile-image")
def delete_profile_image(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.profile:
        current_user.profile.profile_image_url = None
        db.commit()

    return {"message": "Profile image removed"}
