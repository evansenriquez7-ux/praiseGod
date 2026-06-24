import re
from sqlalchemy.orm import Session
from backend.app import models

def get_clean_node_title(node):
    """
    Returns a child-friendly, descriptive title for a skill node,
    cleaning up raw CCSS codes and generic fallback 'Math Standard' titles.
    """
    title = node.title or ""
    
    # Check if the title is generic (e.g. 'Math Standard...' or starts with ELA domain codes)
    is_generic = (
        "Standard" in title or 
        title.strip().startswith("Math") or 
        title.strip().startswith("Reading") or
        node.id in title or
        not title.strip()
    )
    
    if is_generic and node.description:
        desc = node.description.strip()
        if desc.endswith("."):
            desc = desc[:-1]
        
        # If it's short, use it completely
        if len(desc) <= 65:
            return desc
            
        # If it has a semicolon, colon, or comma early on, truncate there
        for char in [";", ":", "—"]:
            if char in desc and desc.index(char) < 65:
                return desc[:desc.index(char)].strip()
                
        # Split by sentence and take the first one
        sentences = desc.split(". ")
        first_sentence = sentences[0].strip()
        if len(first_sentence) <= 65:
            return first_sentence
            
        # Graceful word truncation
        words = first_sentence.split(" ")
        truncated = []
        char_count = 0
        for w in words:
            if char_count + len(w) + 1 > 60:
                break
            truncated.append(w)
            char_count += len(w) + 1
        return " ".join(truncated) + "..."
        
    # Clean up standard code prefix from the existing title if no description
    cleaned_title = re.sub(r"^(Math Standard|ELA Standard|Reading Literature Standard|Reading Informational Standard|Writing Standard|Language Standard)\s*", "", title, flags=re.IGNORECASE)
    if not cleaned_title.strip():
        cleaned_title = node.id
    return cleaned_title.strip()

def check_and_advance_subject_frontier(student_id: int, subject: str, db: Session):
    """
    Checks if all skill nodes at the current frontier grade for a given subject are mastered.
    If so, automatically unlocks the next grade's nodes (changing them from 'locked' to 'active').
    """
    # 1. Get all mastery states for this subject
    states = db.query(models.MasteryState).join(models.SkillNode).filter(
        models.MasteryState.student_id == student_id,
        models.SkillNode.subject == subject
    ).all()
    
    if not states:
        return
        
    def get_grade_num(grade_str):
        special_grades = {"K": 0, "HS": 10}
        if grade_str in special_grades:
            return special_grades[grade_str]
        try:
            return int(grade_str)
        except ValueError:
            return 0
            
    active_grades = set()
    for s in states:
        if s.status in ("active", "review"):
            node = db.query(models.SkillNode).filter(models.SkillNode.id == s.skill_id).first()
            if node:
                active_grades.add(get_grade_num(node.grade_level))
                
    if not active_grades:
        # If there are no active/review states at all, find the highest mastered grade and activate the next one!
        mastered_grades = set()
        for s in states:
            if s.status == "mastered":
                node = db.query(models.SkillNode).filter(models.SkillNode.id == s.skill_id).first()
                if node:
                    mastered_grades.add(get_grade_num(node.grade_level))
        if not mastered_grades:
            return
        highest_mastered = max(mastered_grades)
        next_grade = highest_mastered + 1
    else:
        current_working_grade = min(active_grades)
        
        remaining_active = 0
        for s in states:
            if s.status in ("active", "review"):
                node = db.query(models.SkillNode).filter(models.SkillNode.id == s.skill_id).first()
                if node and get_grade_num(node.grade_level) == current_working_grade:
                    remaining_active += 1
                    
        if remaining_active > 0:
            return
            
        next_grade = current_working_grade + 1
        
    if next_grade == 0:
        next_grade_str = "K"
    elif next_grade >= 10:
        next_grade_str = "HS"
    else:
        next_grade_str = str(next_grade)
        
    grade_search = ["0", "K"] if next_grade_str == "K" else [next_grade_str]
    locked_skills = db.query(models.MasteryState).join(models.SkillNode).filter(
        models.MasteryState.student_id == student_id,
        models.MasteryState.status == "locked",
        models.SkillNode.subject == subject,
        models.SkillNode.grade_level.in_(grade_search)
    ).all()
    
    if locked_skills:
        for s in locked_skills:
            s.status = "active"
        db.commit()
        print(f"[Frontier Advancement] Student {student_id} has advanced to {subject} Grade {next_grade_str}! Unlocked {len(locked_skills)} skills.")
