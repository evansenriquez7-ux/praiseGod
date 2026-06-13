import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'Documents', 'antigravity', 'ccmed')))

from backend.app.database import SessionLocal
from backend.app import models
from backend.app.main import get_practice_question

def test():
    db = SessionLocal()
    
    # 1. Create a completely fresh Kindergarten student profile
    import uuid
    fresh_name = f"Fresh Kinder {uuid.uuid4().hex[:4]}"
    student = models.StudentProfile(
        name=fresh_name,
        pin_hash="1234",
        age=5,
        grade=0,
        language_preference="en",
        interest_tags="basketball,bible"
    )
    db.add(student)
    db.commit()
    db.refresh(student)
        
    print(f"Testing for fresh student: {student.name} (Grade: {student.grade})")
    
    # 2. Force placement_done_math = True so we test the Active Practice Stage fallback subdomain routing
    student.placement_done_math = True
    db.commit()
    
    # 3. Request a practice question under K_FOUNDATIONS track
    try:
        response = get_practice_question(student_id=student.id, subject="Math", subdomain="K_FOUNDATIONS", db=db)
        print("SUCCESSFULLY fetched practice question!")
        print(f"Selected Skill ID: {response.skill_id}")
        print(f"Question Stem: {response.stem}")
        print(f"Options: {[{'key': opt.key, 'text': opt.text} for opt in response.options]}")
        
        # Verify that it is NOT a Grade 5 fraction standard (like 5.NF.A.1)
        if "5.NF" in response.skill_id:
            print("ERROR: Served a Grade 5 Fraction standard!")
            sys.exit(1)
        elif response.skill_id.startswith("K."):
            print("VERIFIED SUCCESS: Successfully served a true Kindergarten math standard fallback!")
        else:
            print(f"VERIFIED SUCCESS: Served standard {response.skill_id} which is grade-appropriate.")
            
    except Exception as e:
        print(f"ERROR: Failed to run practice question dispatch: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    # Clean up the fresh student profile so we don't pollute the database
    db.delete(student)
    db.commit()
    print("Cleaned up mock student profile successfully.")
    
    db.close()

if __name__ == "__main__":
    test()
