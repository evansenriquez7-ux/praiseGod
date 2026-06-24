
from typing import Dict, Any, List, Optional
import os
from backend.app import subagents
from backend.app.services.curriculum import get_clean_node_title
import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app import schemas, models
from backend.app.database import get_db

router = APIRouter(prefix="/api/parent", tags=["parent"])

@router.post("/login", response_model=schemas.ParentLoginResponse)
def parent_login(req: schemas.ParentLoginRequest, db: Session = Depends(get_db)):
    """
    Parent Login. Auto-registers alphanumeric password on first run for developer comfort!
    """
    parent = db.query(models.ParentAccount).first()
    if not parent:
        # First-time run: save this password as canonical, default to password-free
        new_parent = models.ParentAccount(password_hash=req.password, password_auth_required=False)
        db.add(new_parent)
        db.commit()
        return {"success": True, "token": "ccmed_parent_session_active"}
    
    # Bypass password verification if disabled by parent
    if not parent.password_auth_required:
        return {"success": True, "token": "ccmed_parent_session_active"}
    
    if parent.password_hash == req.password:
        return {"success": True, "token": "ccmed_parent_session_active"}
    
    raise HTTPException(status_code=401, detail="Invalid parent alphanumeric password.")


@router.get("/config")
def get_parent_config(db: Session = Depends(get_db)):
    """
    Fetch global parent portal settings.
    """
    parent = db.query(models.ParentAccount).first()
    if not parent:
        return {
            "password_auth_required": False,
            "ai_backend": "gemini",
            "opencode_model": "gemini-2.5-flash",
        }
    return {
        "password_auth_required": parent.password_auth_required,
        "ai_backend": "gemini",
        "opencode_model": parent.opencode_model or "gemini-2.5-flash",
    }

@router.post("/config")
def update_parent_config(req: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Updates parent portal security configuration and AI backend selection.
    """
    parent = db.query(models.ParentAccount).first()
    if not parent:
        parent = models.ParentAccount(password_hash="admin", password_auth_required=False)
        db.add(parent)

    if "password_auth_required" in req:
        parent.password_auth_required = req["password_auth_required"]

    if "password" in req and req["password"]:
        parent.password_hash = req["password"]

    if "ai_backend" in req:
        parent.ai_backend = "gemini" # Always gemini now

    if "gemini_model" in req:
        parent.opencode_model = req["gemini_model"]

    db.commit()

    # Keep in-memory routing in sync
    effective_model = parent.opencode_model or "gemini-2.5-flash"
    subagents.set_ai_config(effective_model)
    print(f"[Config Update] Gemini model={effective_model!r}", flush=True)

    return {
        "password_auth_required": parent.password_auth_required,
        "ai_backend": "gemini",
        "gemini_model": effective_model,
    }

@router.get("/gemini-models")
@router.get("/opencode-models")
def get_gemini_models():
    """
    Returns the list of Gemini models available with the free tier API key.
    (Endpoint decorated with both paths for frontend compatibility).
    """
    try:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        models = client.models.list()
        
        models_list = [m.name.replace("models/", "") for m in models if (m.name.startswith("models/gemini") or m.name.startswith("models/gemma")) and "embedding" not in m.name]
        return {"models": models_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list Gemini models: {e}")

@router.get("/analytics/{student_id}", response_model=schemas.ParentAnalyticsResponse)
def get_parent_analytics(student_id: int, db: Session = Depends(get_db)):
    """
    Parent Dashboard compiling telemetry statistics, Elo progress, and skills mastery.
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    attempts = db.query(models.Attempt).filter(models.Attempt.student_id == student_id).all()
    sessions = db.query(models.TelemetrySession).filter(models.TelemetrySession.student_id == student_id).all()
    mastery_states = db.query(models.MasteryState).filter(models.MasteryState.student_id == student_id).all()
    
    total_skills = len(mastery_states)
    mastered_skills = sum(1 for m in mastery_states if m.status == "mastered")
    mastery_ratio = mastered_skills / total_skills if total_skills > 0 else 0.0
    
    skills_summary = []
    for m in mastery_states:
        # Fetch standard info
        skill_info = db.query(models.SkillNode).filter(models.SkillNode.id == m.skill_id).first()
        if skill_info:
            skills_summary.append(schemas.SkillMasterySummary(
                skill_id=m.skill_id,
                title=get_clean_node_title(skill_info),
                code=skill_info.statement_code or m.skill_id,
                grade_level=skill_info.grade_level or "5",
                status=m.status,
                elo_rating=m.elo_rating,
                consecutive_correct=m.consecutive_correct
            ))
            
    sessions_summary = []
    for s in sessions:
        duration = 0.0
        if s.ended_at:
            duration = (s.ended_at - s.started_at).total_seconds() / 60.0
        sessions_summary.append(schemas.SessionSummary(
            id=s.id,
            started_at=s.started_at,
            ended_at=s.ended_at,
            duration_minutes=round(duration, 1),
            tab_switch_count=s.tab_switch_count,
            idle_seconds=s.idle_seconds,
            spam_click_count=s.spam_click_count,
            guess_count=s.guess_count
        ))
        
    total_att = len(attempts)
    correct_att = sum(1 for a in attempts if a.is_correct)
    
    return schemas.ParentAnalyticsResponse(
        student_id=student.id,
        name=student.name,
        elo_rating=student.elo_rating,
        age=student.age,
        grade=student.grade,
        interest_tags=student.interest_tags,
        telemetry_enabled=student.telemetry_enabled,
        mastery_ratio=round(mastery_ratio, 2),
        skills=skills_summary,
        sessions=sessions_summary,
        total_attempts=total_att,
        correct_attempts=correct_att
    )




@router.get("/graph/{student_id}", response_model=schemas.StudentParentGraphResponse)
def get_parent_graph(student_id: int, grade: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Returns highly granular parallel linear tracks and their exact masteries
    matching all standard nodes dynamically seeded for the specified grade level.
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    target_grade = grade if grade else str(student.grade)
    if target_grade == "0":
        target_grade = "K"
    
    # 1. Fetch all nodes for the target grade with smart high school CCSS groupings
    ela_grade = target_grade
    math_grade = target_grade
    
    # Map High School Math
    if math_grade in ["9", "10", "11", "12", "13", "HS"]:
        math_grade = "HS"
        
    # Map High School ELA
    if ela_grade in ["9", "10"]:
        ela_grade = "9"
    elif ela_grade in ["11", "12", "13", "HS"]:
        ela_grade = "11"
        
    math_grades = ["0", "K"] if math_grade == "K" else [math_grade]
    ela_grades = ["0", "K"] if ela_grade == "K" else [ela_grade]

    math_nodes = db.query(models.SkillNode).filter(
        models.SkillNode.grade_level.in_(math_grades),
        models.SkillNode.subject == "Math"
    ).all()
    
    ela_nodes = db.query(models.SkillNode).filter(
        models.SkillNode.grade_level.in_(ela_grades),
        models.SkillNode.subject != "Math",
        models.SkillNode.subject != "Matatag"
    ).all()
    
    # Fetch MATATAG nodes for the student's grade
    matatag_grades = [str(student.grade)] if student.grade > 0 else ["1"]
    matatag_nodes = db.query(models.SkillNode).filter(
        models.SkillNode.grade_level.in_(matatag_grades),
        models.SkillNode.subject == "Matatag"
    ).all()
    
    nodes = math_nodes + ela_nodes + matatag_nodes
    
    # 2. Fetch all mastery states for the student
    mastery_states = {m.skill_id: m for m in db.query(models.MasteryState).filter(models.MasteryState.student_id == student_id).all()}
    
    # Define Math subdomain details
    math_domain_titles = {
        # K-8 Standard Domains
        "CC": "Counting & Cardinality",
        "OA": "Operations & Algebraic Thinking",
        "NBT": "Numbers & Operations in Base Ten",
        "NF": "Fractions & Decimals",
        "MD": "Measurement & Data",
        "G": "Geometry",
        "RP": "Ratios & Proportions",
        "NS": "The Number System",
        "EE": "Expressions & Equations",
        "SP": "Statistics & Probability",
        "F": "Functions",
        
        # Standards for Mathematical Practice (Processes)
        "MP1": "Mathematical Practice: Perseverance & Problem Solving",
        "MP2": "Mathematical Practice: Abstract & Quantitative Reasoning",
        "MP3": "Mathematical Practice: Viable Arguments & Constructive Critique",
        "MP4": "Mathematical Practice: Mathematical Modeling",
        "MP5": "Mathematical Practice: Strategic Tool Usage",
        "MP6": "Mathematical Practice: Precision & Accuracy",
        "MP7": "Mathematical Practice: Structure & Pattern Recognition",
        "MP8": "Mathematical Practice: Regularity & Repeated Reasoning",
        
        # High School / Advanced Domains
        "N-RN": "The Real Number System",
        "HSN-RN": "The Real Number System",
        "N-Q": "Quantities & Measurements",
        "HSN-Q": "Quantities & Measurements",
        "N-CN": "Complex Number System",
        "HSN-CN": "Complex Number System",
        "N-VM": "Vector & Matrix Quantities",
        "HSN-VM": "Vector & Matrix Quantities",
        "A-SSE": "Algebra: Seeing Structure in Expressions",
        "HSA-SSE": "Algebra: Seeing Structure in Expressions",
        "A-APR": "Algebra: Arithmetic with Polynomials",
        "HSA-APR": "Algebra: Arithmetic with Polynomials",
        "A-CED": "Algebra: Creating Equations",
        "HSA-CED": "Algebra: Creating Equations",
        "A-REI": "Algebra: Reasoning with Equations & Inequalities",
        "HSA-REI": "Algebra: Reasoning with Equations & Inequalities",
        "F-IF": "Functions: Interpreting Functions",
        "HSF-IF": "Functions: Interpreting Functions",
        "F-BF": "Functions: Building Functions",
        "HSF-BF": "Functions: Building Functions",
        "F-LE": "Functions: Linear, Quadratic, & Exponential Models",
        "HSF-LE": "Functions: Linear, Quadratic, & Exponential Models",
        "F-TF": "Functions: Trigonometric Functions",
        "HSF-TF": "Functions: Trigonometric Functions",
        "G-CO": "Geometry: Congruence",
        "HSG-CO": "Geometry: Congruence",
        "G-SRT": "Geometry: Similarity & Right Triangles",
        "HSG-SRT": "Geometry: Similarity & Right Triangles",
        "G-C": "Geometry: Circles",
        "HSG-C": "Geometry: Circles",
        "G-GPE": "Geometry: Expressing Geometric Properties",
        "HSG-GPE": "Geometry: Expressing Geometric Properties",
        "G-GMD": "Geometry: Geometric Measurement & Dimension",
        "HSG-GMD": "Geometry: Geometric Measurement & Dimension",
        "G-MG": "Geometry: Modeling with Geometry",
        "HSG-MG": "Geometry: Modeling with Geometry",
        "S-ID": "Statistics: Interpreting Data",
        "HSS-ID": "Statistics: Interpreting Data",
        "S-IC": "Statistics: Making Inferences & Conclusions",
        "HSS-IC": "Statistics: Making Inferences & Conclusions",
        "S-CP": "Statistics: Conditional Probability",
        "HSS-CP": "Statistics: Conditional Probability",
        "S-MD": "Statistics: Probability in Decisions",
        "HSS-MD": "Statistics: Probability in Decisions",
        
        # Structural & High School Category Baselines
        "HSN": "High School: Number & Quantity",
        "HSA": "High School: Algebra & Algebraic Reasoning",
        "HSF": "High School: Functions",
        "HSG": "High School: Geometry",
        "HSS": "High School: Statistics & Probability",
        "HSM": "High School Mathematics Foundations",
        
        # Custom Groupings
        "K12_PRACTICE": "Interactive Math Practice Activities",
        "K_FOUNDATIONS": "Early Math Foundations",
    }
    
    # Group nodes by subject/domain
    grouped_tracks = {}
    
    for node in nodes:
        # Determine track key and track meta details
        track_key = ""
        if node.subject == "Math":
            import re
            if "MP" in node.id:
                # E.g. '1.MP1' -> 'MP1', 'MP.1' -> 'MP1'
                match = re.search(r"MP\.?(\d+)", node.id)
                domain_code = f"MP{match.group(1)}" if match else "MP"
            elif node.id.startswith("math_") or node.id.startswith("math-"):
                # Clean consolidation of individual exercises into a single unified practice track
                domain_code = "K12_PRACTICE"
            else:
                parts = node.id.split('.')
                if len(parts) >= 2:
                    domain_code = parts[1] if (parts[0].isdigit() or parts[0] == "K") else parts[0]
                else:
                    domain_code = node.id.split('-')[0]
            
            # Group single-digit and Kindergarten structural baseline codes together
            if domain_code in ["1", "2", "3", "4", "5", "6", "7", "8", "K"]:
                domain_code = "K_FOUNDATIONS"
                
            track_key = domain_code
            track_title = f"🧮 Math: {math_domain_titles.get(domain_code, f'Advanced Algebra ({domain_code})')}"
            
            if domain_code.startswith("MP"):
                color = "#a78bfa"  # Lavender/purple for Mathematical Practices
            elif domain_code == "K12_PRACTICE":
                color = "#ec4899"  # Vibrant pink for K12 exercises
            elif domain_code == "K_FOUNDATIONS":
                color = "#34d399"  # Emerald green for early childhood foundations
            elif domain_code in ["NF", "NS", "RP"]:
                color = "#38bdf8"
            elif domain_code in ["OA", "EE", "F"]:
                color = "#fbbf24"
            else:
                color = "#c084fc"
                
            subject_key = f"Math_{domain_code}"
            
        else:
            # Handle MATATAG nodes
            if node.subject == "Matatag" or node.id.startswith("mat_"):
                # Parse content area from node ID: mat_g{grade}_{area_code}_q{quarter}_{index}
                parts = node.id.split("_")
                if len(parts) >= 3:
                    area_code = parts[2]  # na, mg, or dp
                else:
                    area_code = "na"
                
                if area_code == "na":
                    track_title = "🔢 MATATAG: Number and Algebra"
                    color = "#8b5cf6"
                    subject_key = "MATATAG_NA"
                elif area_code == "mg":
                    track_title = "📐 MATATAG: Measurement and Geometry"
                    color = "#f59e0b"
                    subject_key = "MATATAG_MG"
                elif area_code == "dp":
                    track_title = "📊 MATATAG: Data and Probability"
                    color = "#10b981"
                    subject_key = "MATATAG_DP"
                else:
                    track_title = f"🇵🇭 MATATAG: {area_code.upper()}"
                    color = "#f59e0b"
                    subject_key = f"MATATAG_{area_code.upper()}"
                
                track_key = subject_key
            elif node.id.startswith("RL"):
                track_title = "📖 ELA: Reading Literature (RL)"
                color = "#34d399"
                subject_key = "ELA_RL"
            elif node.id.startswith("RI"):
                track_title = "📰 ELA: Reading Informational (RI)"
                color = "#059669"
                subject_key = "ELA_RI"
            elif node.id.startswith("RF"):
                track_title = "🧩 ELA: Foundational Reading Skills (RF)"
                color = "#38bdf8"
                subject_key = "ELA_RF"
            elif node.id.startswith("SL"):
                track_title = "🗣️ ELA: Speaking & Listening (SL)"
                color = "#8b5cf6"
                subject_key = "ELA_SL"
            elif node.id.startswith("W"):
                track_title = "✍️ ELA: Essay & Argumentative Writing (W)"
                color = "#fbbf24"
                subject_key = "ELA_W"
            elif node.id.startswith("L"):
                track_title = "✨ ELA: Grammar & Language Mechanics (L)"
                color = "#ec4899"
                subject_key = "ELA_L"
            else:
                track_title = f"📚 ELA: {node.subject or 'Core Studies'}"
                color = "#6366f1"
                subject_key = f"ELA_{node.subject or 'Core'}"
            
            track_key = subject_key
                
        # Resolve status
        m_state = mastery_states.get(node.id)
        if m_state:
            status = m_state.status
            elo = m_state.elo_rating
        else:
            try:
                node_g = 10 if target_grade == "HS" else (0 if target_grade == "K" else int(target_grade))
                student_g = student.grade
            except ValueError:
                node_g = student_g = 0
                
            if node_g < student_g:
                status = "mastered"
            elif node_g == student_g:
                status = "active"
            else:
                status = "locked"
            elo = 1200.0
            
        graph_node = schemas.GraphNode(
            id=node.id,
            title=get_clean_node_title(node),
            description=node.description or "",
            subject=node.subject,
            status=status,
            elo_rating=elo
        )
        
        if subject_key not in grouped_tracks:
            grouped_tracks[subject_key] = {
                "key": track_key,
                "title": track_title,
                "color": color,
                "subject": node.subject,
                "nodes": []
            }
        grouped_tracks[subject_key]["nodes"].append(graph_node)
        
    # Build sorted response tracks
    response_tracks = []
    for k, track_data in sorted(grouped_tracks.items()):
        track_data["nodes"] = sorted(track_data["nodes"], key=lambda x: x.id)
            
        response_tracks.append(schemas.GraphTrack(
            key=track_data["key"],
            title=track_data["title"],
            color=track_data["color"],
            subject=track_data["subject"],
            nodes=track_data["nodes"]
        ))
        
    return schemas.StudentParentGraphResponse(
        student_id=student.id,
        name=student.name,
        grade_level=target_grade,
        tracks=response_tracks
    )

@router.post("/settings", response_model=schemas.StudentProfileResponse)
def update_parent_settings(req: schemas.ParentSettingsUpdateRequest, db: Session = Depends(get_db)):
    """
    Allows parent to update student profiles, interest tags, and base ELO manually.
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    student.name = req.name
    student.age = req.age
    student.grade = req.grade
    student.language_preference = req.language_preference
    student.interest_tags = req.interest_tags
    if req.elo_rating is not None:
        student.elo_rating = req.elo_rating
    if req.telemetry_enabled is not None:
        student.telemetry_enabled = req.telemetry_enabled
        
    db.commit()
    db.refresh(student)
    return student

