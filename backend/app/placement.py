from sqlalchemy.orm import Session
from backend.app.models import StudentProfile, MasteryState, SkillNode
import random

# MATATAG (Philippine K-10 Math Curriculum) placement milestones
# Uses Number and Algebra strand as primary placement path
MATATAG_PLACEMENT_MILESTONES = [
    "mat_g1_na_q1_1",   # Grade 1: Count up to 100
    "mat_g2_na_q1_1",   # Grade 2: Count up to 1000
    "mat_g3_na_q1_1",   # Grade 3: Represent numbers up to 10,000
    "mat_g4_na_q1_1",   # Grade 4: Read/write numbers up to 1,000,000
    "mat_g5_na_q1_1",   # Grade 5: GMDAS operations
    "mat_g6_na_q1_1",   # Grade 6: Decimals with 4 decimal places
    "mat_g7_na_q1_1",   # Grade 7: Percentage increase/decrease
    "mat_g8_na_q1_1",   # Grade 8: Algebraic expressions
    "mat_g9_na_q1_1",   # Grade 9: Functions and relations
    "mat_g10_na_q1_1",  # Grade 10: Quadratic inequalities
]

class PlacementEngine:
    """
    Implements a Binary Search Onboarding Placement Engine.
    Pinpoints student's academic frontier in under 8 questions.
    """
    
    @staticmethod
    def initialize_placement(student: StudentProfile, db: Session):
        """
        Initializes placement state for a new student.
        Seeds grade-appropriate mastery states for all DB standard nodes in Math, Reading, Writing, Language, Matatag domains.
        Note: We keep this minimal now as the placement test will override and properly seed the subject frontier.
        """
        student.elo_rating = 1000.0 + (student.grade * 50.0)
        # We don't bulk seed all masteries here anymore to allow the placement test to be the source of truth.
        # But we do need to make sure the student has a baseline ELO for each subject.
        student.elo_math = 1000.0 + (student.grade * 100.0)
        student.elo_reading = 1000.0 + (student.grade * 100.0)
        student.elo_writing = 1000.0 + (student.grade * 100.0)
        student.elo_language = 1000.0 + (student.grade * 100.0)
        student.elo_matatag = 1000.0 + (student.grade * 100.0)
        
        # Kindergarten students automatically start with onboarding completed since they are at baseline.
        if student.grade in [0, "0", "K"]:
            student.placement_done_math = True
            student.placement_done_reading = True
            student.placement_done_writing = True
            student.placement_done_language = True
            student.placement_done_matatag = True
            
        db.commit()

    @staticmethod
    def get_milestones(subject: str) -> list:
        return MATATAG_PLACEMENT_MILESTONES

    @staticmethod
    def is_in_placement(subject: str, student: StudentProfile, history: list) -> bool:
        """
        Checks if the student is currently in placement mode for the given subject.
        Uses explicit completion flags on the student profile.
        """
        # Kindergarten students are never in placement mode as they start from scratch.
        if student.grade in [0, "0", "K"]:
            return False

        if subject == "Math":
            if student.placement_done_math: return False
        elif subject in ["Reading", "Reading: Literature", "Reading: Informational Text", "Reading Foundations", "Speaking & Listening", "Verbal"]:
            if student.placement_done_reading: return False
        elif subject == "Writing":
            if student.placement_done_writing: return False
        elif subject in ["Language", "Grammar"]:
            if student.placement_done_language: return False
        elif subject in ["Matatag", "MATATAG", "matatag"]:
            if student.placement_done_matatag: return False
            
        # If flag is false, we check history to see if they've converged
        milestones = PlacementEngine.get_milestones(subject)
        
        # Filter milestones by student's grade level so they are never tested above their grade
        filtered_milestones = []
        for m_id in milestones:
            # Simple check if there's database session available. If not, fallback to parsing prefix
            parts = m_id.split('.')
            if parts and (parts[0].isdigit() or parts[0] == "K"):
                try:
                    m_grade = int(parts[0]) if parts[0].isdigit() else 0
                except Exception:
                    m_grade = 0
            else:
                m_grade = 9 # HS default for ELA standards or others
            
            try:
                student_g = int(student.grade)
            except Exception:
                student_g = 0
                
            if m_grade <= student_g:
                filtered_milestones.append(m_id)
        
        milestones = filtered_milestones
        if not milestones:
            return False
            
        low = 0
        high = len(milestones) - 1
        
        for attempt in history:
            milestone_id = attempt.skill_id
            if milestone_id in milestones:
                idx = milestones.index(milestone_id)
                if attempt.is_correct:
                    low = idx + 1
                else:
                    high = idx - 1
                    
        return low <= high and low < len(milestones)

    @staticmethod
    def get_next_placement_question(subject: str, student: StudentProfile, db: Session, history: list) -> dict:
        """
        Calculates the active search bounds from the student's attempt history.
        Returns the next core milestone standard to test.
        """
        milestones = PlacementEngine.get_milestones(subject)
        
        # Filter milestones by student's grade level so they are never tested above their grade
        filtered_milestones = []
        for m_id in milestones:
            skill = db.query(SkillNode).filter(SkillNode.id == m_id).first()
            if skill:
                try:
                    m_grade = int(skill.grade_level) if skill.grade_level.isdigit() else (0 if skill.grade_level in ["K", "0"] else 9)
                except Exception:
                    m_grade = 0
                
                try:
                    student_g = int(student.grade)
                except Exception:
                    student_g = 0
                    
                if m_grade <= student_g:
                    filtered_milestones.append(m_id)
            else:
                # Fallback to parsing milestone prefix if SkillNode is not found
                parts = m_id.split('.')
                if parts and (parts[0].isdigit() or parts[0] == "K"):
                    try:
                        m_grade = int(parts[0]) if parts[0].isdigit() else 0
                    except Exception:
                        m_grade = 0
                else:
                    m_grade = 9
                
                try:
                    student_g = int(student.grade)
                except Exception:
                    student_g = 0
                    
                if m_grade <= student_g:
                    filtered_milestones.append(m_id)
        
        milestones = filtered_milestones
        
        low = 0
        high = len(milestones) - 1
        
        for attempt in history:
            milestone_id = attempt.skill_id
            if milestone_id in milestones:
                idx = milestones.index(milestone_id)
                if attempt.is_correct:
                    low = idx + 1
                else:
                    high = idx - 1
                    
        if low > high or low >= len(milestones):
            # Converged!
            final_grade = min(low, len(milestones))
            
            # Map index to approximate grade level
            # milestones are approx Grade 1 to 12. 
            # If low=0, Grade 0/K. If low=len, Grade 12.
            highest_mastered_grade = final_grade
            
            PlacementEngine.finalize_placement(student, highest_mastered_grade, subject, db)
            return None
            
        mid = (low + high) // 2
        target_skill_id = milestones[mid]
        
        skill = db.query(SkillNode).filter(SkillNode.id == target_skill_id).first()
        if not skill:
            # Fallback to any node in that subject if milestone missing (safety)
            skill = db.query(SkillNode).filter(SkillNode.subject.like(f"%{subject}%")).first()
            
        return {
            "skill_id": skill.id if skill else target_skill_id,
            "grade_level": skill.grade_level if skill else "1",
            "title": skill.title if skill else "Placement Node",
            "progress": len(history) + 1,
            "is_placement": True
        }

    @staticmethod
    def finalize_placement(student: StudentProfile, highest_mastered_grade: int, subject: str, db: Session):
        """
        Concludes placement onboarding, calculates baseline ELO and populates mastery states.
        """
        new_elo = 1000.0 + (highest_mastered_grade * 100.0)
        
        if subject == "Math":
            student.elo_math = new_elo
            student.elo_rating = new_elo
            student.placement_done_math = True
            db_subject_filter = "Math"
        elif subject in ["Reading", "Reading: Literature", "Reading: Informational Text", "Reading Foundations", "Speaking & Listening", "Verbal"]:
            student.elo_reading = new_elo
            student.elo_writing = new_elo
            student.elo_language = new_elo
            student.placement_done_reading = True
            student.placement_done_writing = True
            student.placement_done_language = True
            db_subject_filter = ["Reading: Literature", "Reading: Informational Text", "Reading Foundations", "Speaking & Listening", "Writing", "Language"]
        elif subject == "Writing":
            student.elo_writing = new_elo
            student.placement_done_writing = True
            db_subject_filter = "Writing"
        elif subject in ["Language", "Grammar"]:
            student.elo_language = new_elo
            student.placement_done_language = True
            db_subject_filter = "Language"
        elif subject in ["Matatag", "MATATAG", "matatag"]:
            student.elo_matatag = new_elo
            student.placement_done_matatag = True
            db_subject_filter = "Matatag"
        else:
            # Fallback
            student.placement_done_reading = True
            db_subject_filter = "Reading: Literature"
            
        # Bulk update mastery states for this subject
        query = db.query(SkillNode)
        if isinstance(db_subject_filter, list):
            query = query.filter(SkillNode.subject.in_(db_subject_filter))
        else:
            query = query.filter(SkillNode.subject == db_subject_filter)
            
        all_skills = query.all()
        
        for skill in all_skills:
            try:
                if skill.grade_level == "HS":
                    g_level = 10
                elif skill.grade_level == "K":
                    g_level = 0
                else:
                    g_level = int(skill.grade_level)
            except ValueError:
                g_level = 0
                
            if g_level <= highest_mastered_grade:
                status = "mastered"
            elif g_level == highest_mastered_grade + 1:
                status = "active"
            else:
                status = "locked"
                
            state = db.query(MasteryState).filter(
                MasteryState.student_id == student.id,
                MasteryState.skill_id == skill.id
            ).first()
            
            if not state:
                state = MasteryState(
                    student_id=student.id,
                    skill_id=skill.id,
                    status=status,
                    elo_rating=1200.0
                )
                db.add(state)
            else:
                state.status = status
                
        db.commit()
        print(f"Placement finalized for student {student.name} in {subject}. Highest mastered grade: Grade {highest_mastered_grade}. New ELO: {new_elo}")

    @staticmethod
    def skip_placement(student: StudentProfile, subject: str, db: Session):
        """
        Bypasses the placement test and seeds mastery based on the student's claimed grade.
        """
        highest_mastered_grade = student.grade - 1 if student.grade > 0 else 0
        PlacementEngine.finalize_placement(student, highest_mastered_grade, subject, db)


