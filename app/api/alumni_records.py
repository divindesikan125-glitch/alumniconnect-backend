from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from .db.database import get_db
from .models.alumni_record import AlumniRecord
from .schemas.alumni_record import AlumniRecordCreate, AlumniRecordResponse
from .core.security import get_current_institution, get_current_user
from .models.user import User
import csv
from io import StringIO

router = APIRouter(prefix="/alumni-records", tags=["Alumni Records"])

# =========================================================
# ADD ALUMNI RECORD (Institution Only)
# =========================================================
@router.post("/", response_model=AlumniRecordResponse)
def add_alumni_record(
    data: AlumniRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_institution)
):
    # Map the new fields (enrollment_id and degree_type) from the request
    new_record = AlumniRecord(
        enrollment_id=data.enrollment_id, # New field
        full_name=data.full_name,
        email=data.email,
        graduation_year=data.graduation_year,
        department=data.department,
        degree_type=data.degree_type,     # New field
        institution_id=current_user.id
    )

    db.add(new_record)

    try:
        db.commit()
        db.refresh(new_record)
    except IntegrityError:
        db.rollback()
        # Since we have multiple constraints, we provide a more helpful error
        raise HTTPException(
            status_code=400,
            detail="A record with this Enrollment ID or Email already exists for your institution."
        )

    return new_record

@router.post("/claim/{enrollment_id}")
def claim_alumni_record(
    enrollment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.merge(current_user)
    
    record = db.query(AlumniRecord).filter(
        AlumniRecord.enrollment_id == enrollment_id,
        AlumniRecord.is_claimed == False
    ).first()

    if not record:
        print(f"DEBUG: Record {enrollment_id} not found or already claimed")
        raise HTTPException(status_code=404, detail="ID not found")

    # --- ADD THESE PRINTS ---
    print(f"DEBUG: Record Email: '{record.email.lower()}'")
    print(f"DEBUG: User Email:   '{user.email.lower()}'")

    if record.email.strip().lower() != user.email.strip().lower():
        print("DEBUG: Email Mismatch Triggered!")
        raise HTTPException(status_code=403, detail="Email mismatch")
    
    # 4. Update the data
    record.is_claimed = True
    record.linked_user_id = user.id
    user.is_verified = True 
    
    # 5. Save everything
    db.commit()
    db.refresh(record)
    
    return {"status": "success", "message": "Profile verified successfully"}


@router.post("/upload-csv")
async def upload_alumni_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_institution)
):
    contents = await file.read()
    decoded = contents.decode('utf-8')
    reader = csv.DictReader(StringIO(decoded))
    
    new_records = []
    for row in reader:
        try:
            # Basic validation: Skip rows missing mandatory data
            if not row.get('enrollment_id') or not row.get('email'):
                continue
                
            new_rec = AlumniRecord(
                enrollment_id=row['enrollment_id'],
                full_name=row['full_name'],
                email=row['email'],
                graduation_year=int(row.get('graduation_year', 0)),
                department=row.get('department'),
                institution_id=current_user.id
            )
            new_records.append(new_rec)
        except (ValueError, KeyError) as e:
            # Skip rows with bad data format (e.g. text in year column)
            print(f"Skipping row due to error: {e}")
            continue
    
    if not new_records:
        raise HTTPException(status_code=400, detail="No valid records found in CSV.")

    db.add_all(new_records)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="CSV contains duplicate Enrollment IDs or Emails that already exist."
        )
        
    return {"message": f"Successfully imported {len(new_records)} alumni records."}

# =========================================================
# VIEW ALL ALUMNI RECORDS (With Search & Pagination)
# =========================================================

@router.get("/", response_model=List[AlumniRecordResponse])
def get_my_alumni_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_institution)
):
    # Fetch records with a double join: Record -> User -> Profile
    records = db.query(AlumniRecord).options(
        joinedload(AlumniRecord.user).joinedload(User.profile)
    ).filter(AlumniRecord.institution_id == current_user.id).all()

    # Crucial Step: Transfer 'private' data from User model to the Record response
    for record in records:
        if record.user:
            record.phone_number = record.user.phone_number
            record.address = record.user.address
            # Note: record.profile is already handled by the nested schema mapping
            
    return records
