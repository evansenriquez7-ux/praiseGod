from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app import schemas, models
from backend.app.database import get_db
from backend.app.services import placement
from backend.app.services.telemetry import clear_student_history as _clear_student_history

router = APIRouter(prefix="/api/students", tags=["student"])

@router.get("/profiles", response_model=List[schemas.StudentProfileResponse])
def get_student_profiles(db: Session = Depends(get_db)):
    """
    Lists all active student profiles.
    """
    return db.query(models.StudentProfile).all()

@router.patch("/{student_id}/interests", response_model=schemas.StudentProfileResponse)
def update_student_interests(student_id: int, req: schemas.UpdateInterestsRequest, db: Session = Depends(get_db)):
    """
    Student-facing endpoint: updates the student's own interest tags.
    These are stored separately from parent-set interest_tags and combined
    at question-generation time so both sets influence AI prompts.
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    student.student_interest_tags = req.interest_tags.strip()
    db.commit()
    db.refresh(student)
    return student

@router.post("/register", response_model=schemas.StudentProfileResponse)
def register_student(req: schemas.StudentRegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new student profile and triggers binary placement onboarding initialization.
    """
    new_student = models.StudentProfile(
        name=req.name,
        pin_hash=req.pin, # Saved directly for testing convenience
        age=req.age,
        grade=req.grade,
        language_preference=req.language_preference,
        interest_tags=req.interest_tags
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    # Initialize placement onboarding
    placement.PlacementEngine.initialize_placement(new_student, db)
    return new_student

@router.post("/login", response_model=schemas.StudentProfileResponse)
def student_login(req: schemas.StudentLoginRequest, db: Session = Depends(get_db)):
    """
    PIN-based Student login endpoint.
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    if student.pin_hash == req.pin:
        # Clear this student's Math and ELA question history so the new session
        # starts fresh — no repeated story contexts or passages from prior sessions.
        _clear_student_history(req.student_id)
        return student
        
    raise HTTPException(status_code=401, detail="Invalid student numeric PIN.")

@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"success": True}
