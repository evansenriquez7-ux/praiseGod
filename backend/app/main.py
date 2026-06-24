import datetime
import os
import math
import json
import re
import random as _random
import hashlib
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
import concurrent.futures
import subprocess
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr



from backend.app.database import get_db, engine, Base
from backend.app import models, schemas, subagents, placement
from backend.app.practice_gen import pipeline

from backend.app.practice_gen import registry as _pg_registry

def validate_math_answer(expected: Any, student_ans: str) -> bool:
    """
    Deterministic validation using SymPy solver.
    Verifies if the student_ans is mathematically equivalent to expected.
    """
    try:
        expr_solved = parse_expr(str(expected))
        ans_solved = parse_expr(str(student_ans))
        return sp.simplify(expr_solved - ans_solved) == 0
    except Exception:
        return str(expected).strip() == str(student_ans).strip()
from backend.app.practice_gen.axes_catalog import (
    get_axes_for_concept as _get_axes_for_concept,
    compute_difficulty_scalar as _compute_difficulty_scalar,
)

# Initialize FastAPI app
app = FastAPI(
    title="CCMed Adaptive Mastery Engine API",
    description="Adaptive K-12 math mastery engine with deterministic SymPy validation and Socratic split tutoring.",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Enable CORS for tablet local LAN sync and external tunnels
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://mellow-mirage-jhc3.here.now",
    ],
    allow_origin_regex=r"https://.*\.web\.app|https://.*\.firebaseapp\.com|https://.*\.here\.now|https://.*\.trycloudflare\.com|https://.*\.loca\.lt|https://.*\.ts\.net|https://edu\.enrichmentcap\.com|http://.*\.local:.*|http://192\.168\..*|http://10\..*|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Global in-memory cache for LLM-generated ELA skeletons
ELA_SKELETON_CACHE = {}
# Global in-memory cache for narrated Math skeletons to retrieve their stems/options/explanations
MATH_NARRATED_CACHE = {}
# Global in-memory cache for AI-generated Math skeletons (ai_ prefix skeleton_ids)
# Used when SymPy exhausts variety or generates a visual-reference question
MATH_AI_CACHE = {}
# Global in-memory cache for pre-generated questions to eliminate latency
QUESTION_CACHE = {} # key: f"{student_id}_{subject}_{subdomain}"
# Global in-memory cache for MATATAG skeleton problems
MATATAG_SKELETON_CACHE = {}  # key: skeleton_id (mat_grade_gen_seed format)
# Global in-memory cache for practice_gen v2 pipeline problems
PRACTICE_GEN_CACHE = {}  # key: problem_id

# Path to the shared dedup scratch file (same file testy CLI uses)
_SCRATCH_FILE = Path(__file__).parent.parent.parent / "scratch" / "gen_problems.jsonl"

def _combined_interests(student, fallback: str = "general") -> str:
    """
    Merge parent-set interest_tags and student-set student_interest_tags into a
    single comma-separated string for AI prompts.  Parent tags come first so the
    parent's preferences anchor the theme; student additions extend it.
    """
    parent = (student.interest_tags or "").strip()
    child  = (student.student_interest_tags or "").strip()
    combined = ", ".join(filter(None, [parent, child]))
    return combined or fallback

def _load_previous_questions(student_id: int, node_id: str) -> list:
    """
    Return all full question records already served to this student on node_id
    from gen_problems.jsonl.  Used by both Math and ELA batch generators so the
    LLM knows exactly what to avoid.  Mirrors testy.load_previous_problems().
    """
    if not _SCRATCH_FILE.exists():
        return []
    records = []
    try:
        with open(_SCRATCH_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if (obj.get("node_id") == node_id
                            and obj.get("student_id") == student_id
                            and obj.get("source") == "live_practice"):
                        records.append(obj)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return records

def _save_practice_question(
    student_id: int,
    node_id: str,
    problem_text: str,
    answer: str = "",
    subject: str = "Verbal",
    question_mode: str = "mcq",
) -> None:
    """
    Append a served question to gen_problems.jsonl so the next batch's LLM
    sees exactly what this student has already encountered and avoids it.
    Works for both Math and ELA.
    """
    problem_text = problem_text.strip()
    if not problem_text:
        return
    record = {
        "student_id":    student_id,
        "node_id":       node_id,
        "subject":       subject,
        "question_mode": question_mode,
        "problem_text":  problem_text,
        "answer":        answer,
        "generated_at":  datetime.datetime.utcnow().isoformat(),
        "source":        "live_practice",
    }
    _SCRATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_SCRATCH_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def _clear_student_history(student_id: int) -> None:
    """
    Remove all live_practice entries for this student from gen_problems.jsonl.
    Called on student login so each new session starts fresh (both Math and ELA).
    Testy entries (source != 'live_practice') are never touched.
    """
    if not _SCRATCH_FILE.exists():
        return
    try:
        kept = []
        with open(_SCRATCH_FILE, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                    if obj.get("source") == "live_practice" and obj.get("student_id") == student_id:
                        continue
                    kept.append(stripped)
                except json.JSONDecodeError:
                    kept.append(stripped)
        _SCRATCH_FILE.write_text("\n".join(kept) + ("\n" if kept else ""))
        print(f"[Dedup] Cleared session history for student {student_id}")
    except OSError as e:
        print(f"[ELA Dedup] Could not clear history: {e}")

# The startup event is called explicitly at module load time below
def _startup_migrate_and_configure():
    """
    Zero-downtime column migrations + load AI backend config into subagents.
    Runs once when uvicorn boots, before any request is handled.
    """
    # Add new columns to parent_accounts if they don't already exist
    with engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE parent_accounts "
            "ADD COLUMN IF NOT EXISTS ai_backend VARCHAR DEFAULT 'gemini'"
        ))
        conn.execute(text(
            "ALTER TABLE parent_accounts "
            "ADD COLUMN IF NOT EXISTS opencode_model VARCHAR DEFAULT 'gemini-2.5-flash'"
        ))
        conn.commit()

    # Ensure node_intro_views table exists (idempotent)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS node_intro_views (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
                node_key VARCHAR(20) NOT NULL,
                viewed_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE(student_id, node_key)
            )
        """))
        conn.commit()

    # Seed the in-memory AI routing config from whatever's already stored
    from backend.app.database import SessionLocal
    with SessionLocal() as db:
        parent = db.query(models.ParentAccount).first()
        if parent:
            subagents.set_ai_config(
                parent.opencode_model or "gemini-2.5-flash"
            )


def replenish_question_cache(student_id: int, subject: str, subdomain: Optional[str], count: int):
    """
    Background task to pre-generate questions into the cache.
    Uses parallel execution for high-speed generation.
    """
    from backend.app.database import SessionLocal
    db = SessionLocal()
    cache_key = f"{student_id}_{subject}_{subdomain}"
    
    try:
        def generate_one():
            inner_db = SessionLocal()
            try:
                return get_practice_question(student_id, subject, subdomain, inner_db)
            finally:
                inner_db.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(generate_one) for _ in range(count)]
            new_questions = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    new_questions.append(future.result())
                except Exception as e:
                    print(f"Background generation error: {e}")
            
            if cache_key not in QUESTION_CACHE:
                QUESTION_CACHE[cache_key] = []
            QUESTION_CACHE[cache_key].extend(new_questions)
            print(f"Replenished cache for {cache_key} with {len(new_questions)} items (Total: {len(QUESTION_CACHE[cache_key])})")
    finally:
        db.close()

def get_clean_node_title(node):
    """
    Returns a child-friendly, descriptive title for a skill node,
    cleaning up raw CCSS codes and generic fallback 'Math Standard' titles.
    """
    import re
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
        if grade_str == "HS":
            return 10
        elif grade_str == "K":
            return 0
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

# --- Elo Rating Helper ---
def update_elo(student_elo: float, skill_elo: float, is_correct: bool, k_factor: float = 32.0):
    """
    Standard Elo update matchmaking formula.
    Adjusts student ELO and skill/question ELO based on performance.
    """
    expected_student = 1.0 / (1.0 + math.pow(10.0, (skill_elo - student_elo) / 400.0))
    actual_student = 1.0 if is_correct else 0.0
    
    new_student_elo = student_elo + k_factor * (actual_student - expected_student)
    
    # Skill difficulty increases on student failure, decreases on success
    expected_skill = 1.0 - expected_student
    actual_skill = 0.0 if is_correct else 1.0
    new_skill_elo = skill_elo + k_factor * (actual_skill - expected_skill)
    
    return round(new_student_elo, 1), round(new_skill_elo, 1)

# --- PARENT ENDPOINTS ---

@app.post("/api/parent/login", response_model=schemas.ParentLoginResponse)
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

@app.get("/api/parent/config")
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

@app.post("/api/parent/config")
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

@app.get("/api/parent/gemini-models")
@app.get("/api/parent/opencode-models")
def get_gemini_models():
    """
    Returns the list of Gemini models available with the free tier API key.
    (Endpoint decorated with both paths for frontend compatibility).
    """
    try:
        from google import genai
        import os
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        models = client.models.list()
        
        models_list = [m.name.replace("models/", "") for m in models if (m.name.startswith("models/gemini") or m.name.startswith("models/gemma")) and "embedding" not in m.name]
        return {"models": models_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list Gemini models: {e}")

@app.get("/api/parent/analytics/{student_id}", response_model=schemas.ParentAnalyticsResponse)
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




@app.post("/api/admin/load-matatag")
def load_matatag_curriculum_endpoint(clear: bool = False, db: Session = Depends(get_db)):
    """
    Load MATATAG (Philippine K-10 Math) curriculum into the skill_nodes table.
    
    Args:
        clear: If true, delete all existing MATATAG nodes before loading
        
    Returns:
        Stats about loaded, skipped, and errored nodes
    """
    from backend.app import matatag_loader
    
    stats = matatag_loader.load_matatag_curriculum(db, clear_existing=clear)
    return {
        "success": True,
        "message": f"MATATAG curriculum loaded: {stats['loaded']} nodes added, {stats['skipped']} skipped, {stats['errors']} errors",
        "stats": stats
    }


@app.get("/api/parent/graph/{student_id}", response_model=schemas.StudentParentGraphResponse)
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

@app.post("/api/parent/settings", response_model=schemas.StudentProfileResponse)
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

# --- STUDENT PROFILE ENDPOINTS ---

@app.get("/api/students/profiles", response_model=List[schemas.StudentProfileResponse])
def get_student_profiles(db: Session = Depends(get_db)):
    """
    Lists all active student profiles.
    """
    return db.query(models.StudentProfile).all()

@app.patch("/api/students/{student_id}/interests", response_model=schemas.StudentProfileResponse)
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

@app.post("/api/students/register", response_model=schemas.StudentProfileResponse)
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

@app.post("/api/students/login", response_model=schemas.StudentProfileResponse)
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

@app.delete("/api/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"success": True}

# --- TELEMETRY ENDPOINTS ---

@app.post("/api/telemetry/start", response_model=schemas.TelemetrySessionStartResponse)
def start_telemetry_session(req: schemas.TelemetrySessionStartRequest, db: Session = Depends(get_db)):
    """
    Initiates a telemetry tracking session for window defense telemetry.
    """
    # Deactivate any previous active session
    db.query(models.TelemetrySession).filter(
        models.TelemetrySession.student_id == req.student_id,
        models.TelemetrySession.is_active == True
    ).update({"is_active": False, "ended_at": datetime.datetime.utcnow()})
    
    new_session = models.TelemetrySession(
        student_id=req.student_id,
        started_at=datetime.datetime.utcnow(),
        is_active=True
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {"session_id": new_session.id, "success": True}

@app.post("/api/telemetry/update", response_model=schemas.TelemetrySessionResponse)
def update_telemetry_session(req: schemas.TelemetrySessionUpdateRequest, db: Session = Depends(get_db)):
    """
    Updates statistics in the telemetry logs database.
    """
    session = db.query(models.TelemetrySession).filter(models.TelemetrySession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Telemetry session not found.")
        
    session.tab_switch_count += req.tab_switch_count
    session.idle_seconds += req.idle_seconds
    session.spam_click_count += req.spam_click_count
    session.guess_count += req.guess_count
    
    if req.ended:
        session.is_active = False
        session.ended_at = datetime.datetime.utcnow()
        
    db.commit()
    return {"success": True}

# --- PRACTICE ENGINE ENDPOINTS ---

@app.get("/api/practice/question", response_model=schemas.QuestionResponse)
def get_practice_question(student_id: int, subject: str = "Math", subdomain: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Onboarding Placement / Elo Match practice question dispatch router.
    Integrates SymPy skeleton templates and wraps them in Gemini Narratives.
    """
    def apply_subdomain_filter(query, sub_val):
        if not sub_val:
            return query
        if sub_val == "K_FOUNDATIONS":
            from sqlalchemy import or_
            conditions = [models.SkillNode.id.like("K.%")]
            conditions.extend([models.SkillNode.id == i for i in ["1", "2", "3", "4", "5", "6", "7", "8", "K"]])
            return query.filter(or_(*conditions))
        else:
            return query.filter(
                models.SkillNode.id.like(f"%.{sub_val}.%") | 
                models.SkillNode.id.like(f"{sub_val}-%") | 
                models.SkillNode.id.like(f"%{sub_val}%")
            )

    def filter_by_max_grade(query, student_grade):
        try:
            max_g = int(student_grade)
        except ValueError:
            max_g = 0
            
        if max_g == 0:
            return query.filter(models.SkillNode.grade_level.in_(["0", "K"]))
        
        allowed_grades = ["0", "K"] + [str(i) for i in range(1, max_g + 1)]
        return query.filter(models.SkillNode.grade_level.in_(allowed_grades))

    def get_matatag_skill_for_quarter(student_id: int, student_grade: int, subdomain: str, db_session) -> str:
        """
        Select a MATATAG skill from the current quarter, cycling through all competencies.
        
        Logic:
        1. Determine content area from subdomain (NA, MG, DP)
        2. Find current quarter position (first non-mastered quarter at or below student grade)
        3. Select a random non-mastered competency from that quarter
        4. If all mastered, advance to next quarter
        """
        import re
        import random as rnd  # Use different name to avoid scope issues

        # Check if subdomain is already an explicit node_id
        if subdomain and subdomain.startswith("mat_g") and "_q" in subdomain:
            return subdomain
        
        # Map subdomain to content area code
        area_map = {
            "MATATAG_NA": "na", "NA": "na", "na": "na",
            "MATATAG_MG": "mg", "MG": "mg", "mg": "mg", 
            "MATATAG_DP": "dp", "DP": "dp", "dp": "dp",
        }
        area_code = area_map.get(subdomain, "na")
        grade = max(1, student_grade)
        
        # Get all nodes for this content area at or below student grade
        all_nodes = db_session.query(models.SkillNode).filter(
            models.SkillNode.id.like(f"mat_g%_{area_code}_%")
        ).all()
        
        if not all_nodes:
            return f"mat_g{grade}_{area_code}_q1_0"
        
        # Parse and organize nodes
        node_info = []
        for n in all_nodes:
            match = re.match(r"mat_g(\d+)_([a-z]+)_q(\d+)_(\d+)", n.id)
            if match:
                node_grade = int(match.group(1))
                if node_grade <= grade:
                    node_info.append({
                        "id": n.id,
                        "grade": node_grade,
                        "quarter": int(match.group(3)),
                        "num": int(match.group(4)),
                    })
        
        if not node_info:
            return f"mat_g{grade}_{area_code}_q1_0"
        
        # Sort by grade, quarter, num
        node_info.sort(key=lambda x: (x["grade"], x["quarter"], x["num"]))
        
        # Get mastery states
        node_ids = [n["id"] for n in node_info]
        mastery_states = db_session.query(models.MasteryState).filter(
            models.MasteryState.student_id == student_id,
            models.MasteryState.skill_id.in_(node_ids)
        ).all()
        mastery_map = {m.skill_id: m.status for m in mastery_states}
        
        # Find current quarter (first non-mastered node's grade+quarter)
        current_grade = grade
        current_quarter = 1
        for n in node_info:
            status = mastery_map.get(n["id"], "not_started")
            if status != "mastered":
                current_grade = n["grade"]
                current_quarter = n["quarter"]
                break
        
        # Get all non-mastered competencies in current quarter
        quarter_nodes = [
            n for n in node_info 
            if n["grade"] == current_grade and n["quarter"] == current_quarter
            and mastery_map.get(n["id"], "not_started") != "mastered"
        ]
        
        if quarter_nodes:
            # Randomly select one for variety
            return rnd.choice(quarter_nodes)["id"]
        else:
            # All mastered in current quarter - find next available
            for n in node_info:
                if (n["grade"], n["quarter"]) > (current_grade, current_quarter):
                    status = mastery_map.get(n["id"], "not_started")
                    if status != "mastered":
                        return n["id"]
            
            # All mastered - return first node to allow continued practice
            return node_info[0]["id"]

    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    is_placement = False
    progress = None
    skill_id = None
    
    # 1. Check if student is in placement onboarding stage
    if not subdomain:
        # Get placement history for this specific subject
        if subject == "Verbal":
            placement_history = db.query(models.Attempt).join(models.SkillNode).filter(
                models.Attempt.student_id == student_id,
                models.Attempt.telemetry_flagged == False,
                models.SkillNode.subject.in_(["Reading: Literature", "Reading: Informational Text", "Reading Foundations", "Speaking & Listening", "Writing", "Language"])
            ).all()
        else:
            placement_history = db.query(models.Attempt).join(models.SkillNode).filter(
                models.Attempt.student_id == student_id,
                models.Attempt.telemetry_flagged == False,
                models.SkillNode.subject.like(f"%{subject}%")
            ).all()
        
        is_placement = placement.PlacementEngine.is_in_placement(subject, student, placement_history)
        if is_placement:
            placement_meta = placement.PlacementEngine.get_next_placement_question(subject, student, db, placement_history)
            if placement_meta:
                skill_id = placement_meta["skill_id"]
                progress = placement_meta["progress"]
            else:
                is_placement = False
    
    # Special handling for MATATAG: use quarter-based skill selection
    if not skill_id and subject in ["Matatag", "MATATAG", "matatag"]:
        skill_id = get_matatag_skill_for_quarter(student_id, student.grade, subdomain, db)
            
    if not skill_id:
        # Active Practice Stage
        import random
        now = datetime.datetime.utcnow()
        sr_query = db.query(models.SpacedRepetition).join(models.SkillNode).filter(
            models.SpacedRepetition.student_id == student_id,
            models.SpacedRepetition.due_date <= now
        )
        if subject == "Math":
            sr_query = sr_query.filter(models.SkillNode.subject == "Math")
        elif subject == "Verbal":
            sr_query = sr_query.filter(models.SkillNode.subject.in_(["Reading: Literature", "Reading: Informational Text", "Reading Foundations", "Speaking & Listening", "Writing", "Language"]))
        else:
            sr_query = sr_query.filter(models.SkillNode.subject == subject)
            
        sr_query = filter_by_max_grade(sr_query, student.grade)
        sr_query = apply_subdomain_filter(sr_query, subdomain)
        due_card = sr_query.first()
        
        roll = random.random()
        
        if roll < 0.20 and due_card:
            skill_id = due_card.skill_id
        else:
            active_query = db.query(models.MasteryState).join(models.SkillNode).filter(
                models.MasteryState.student_id == student_id,
                models.MasteryState.status == "active"
            )
            if subject == "Math":
                active_query = active_query.filter(models.SkillNode.subject == "Math")
            elif subject == "Verbal":
                active_query = active_query.filter(models.SkillNode.subject.in_(["Reading: Literature", "Reading: Informational Text", "Reading Foundations", "Speaking & Listening", "Writing", "Language"]))
            else:
                active_query = active_query.filter(models.SkillNode.subject == subject)
                
            active_query = filter_by_max_grade(active_query, student.grade)
            active_query = apply_subdomain_filter(active_query, subdomain)
            
            # Interleaving: pick a random active skill instead of always the first one
            active_states = active_query.all()
            if active_states:
                skill_id = random.choice(active_states).skill_id
            elif due_card:
                skill_id = due_card.skill_id
                
            # Fallback if no active skills
            if not skill_id:
                # Find grade-appropriate standard node for this subject in DB
                grade_str = str(student.grade)
                if grade_str == "0":
                    grade_str = "K"
                
                # Apply high school CCSS groupings mapping
                if subject == "Math":
                    if grade_str in ["9", "10", "11", "12", "13", "HS"]:
                        grade_str = "HS"
                else:
                    if grade_str in ["9", "10"]:
                        grade_str = "9"
                    elif grade_str in ["11", "12", "13", "HS"]:
                        grade_str = "11"
                        
                grade_search = ["0", "K"] if grade_str == "K" else [grade_str]
                fallback_query = db.query(models.SkillNode).filter(
                    models.SkillNode.grade_level.in_(grade_search)
                )
                if subject == "Math":
                    fallback_query = fallback_query.filter(models.SkillNode.subject == "Math")
                elif subject == "Verbal":
                    fallback_query = fallback_query.filter(models.SkillNode.subject.in_(["Reading: Literature", "Reading: Informational Text", "Reading Foundations", "Speaking & Listening", "Writing", "Language"]))
                else:
                    fallback_query = fallback_query.filter(models.SkillNode.subject == subject)
                    
                fallback_query = apply_subdomain_filter(fallback_query, subdomain)
                all_nodes_1 = fallback_query.all()
                fallback_node = random.choice(all_nodes_1) if all_nodes_1 else None
                
                if not fallback_node:
                    # General fallback in that subject
                    fallback_query = db.query(models.SkillNode)
                    if subject == "Math":
                        fallback_query = fallback_query.filter(models.SkillNode.subject == "Math")
                    elif subject == "Verbal":
                        fallback_query = fallback_query.filter(models.SkillNode.subject.in_(["Reading: Literature", "Reading: Informational Text", "Reading Foundations", "Speaking & Listening", "Writing", "Language"]))
                    else:
                        fallback_query = fallback_query.filter(models.SkillNode.subject == subject)
                        
                    fallback_query = filter_by_max_grade(fallback_query, student.grade)
                    fallback_query = apply_subdomain_filter(fallback_query, subdomain)
                    all_nodes_2 = fallback_query.all()
                    fallback_node = random.choice(all_nodes_2) if all_nodes_2 else None
                    
                if fallback_node:
                    skill_id = fallback_node.id
                else:
                    skill_id = "5.NF.A.1" if subject == "Math" else "RL.5.1"

    # Grade Guard: Ensure selected skill_id does not exceed student's claimed grade level under any circumstances.
    # Bypass Grade Guard if the user explicitly requested a specific node (subdomain starts with mat_g or matches skill_id)
    is_explicit_subdomain = subdomain and (subdomain == skill_id or (subdomain.startswith("mat_g") and "_q" in subdomain))
    if skill_id and not is_explicit_subdomain:
        node = db.query(models.SkillNode).filter(models.SkillNode.id == skill_id).first()
        if node:
            try:
                node_g = int(node.grade_level) if node.grade_level.isdigit() else (0 if node.grade_level in ["K", "0"] else 9)
            except Exception:
                node_g = 0
                
            try:
                student_g = int(student.grade)
            except Exception:
                student_g = 0
                
            if node_g > student_g:
                # Emergency override: find a grade-appropriate fallback node!
                print(f"[Grade Guard] Overriding skill {skill_id} (Grade {node.grade_level}) for student grade {student.grade}")
                grade_str = str(student.grade)
                if grade_str == "0":
                    grade_str = "K"
                grade_search = ["0", "K"] if grade_str == "K" else [grade_str]
                fallback_query = db.query(models.SkillNode).filter(
                    models.SkillNode.grade_level.in_(grade_search)
                )
                if subject == "Math":
                    fallback_query = fallback_query.filter(models.SkillNode.subject == "Math")
                elif subject in ["Matatag", "MATATAG", "matatag"]:
                    fallback_query = fallback_query.filter(models.SkillNode.subject == "Matatag")
                else:
                    fallback_query = fallback_query.filter(models.SkillNode.subject.in_(["Reading: Literature", "Reading: Informational Text", "Reading Foundations", "Speaking & Listening", "Writing", "Language"]))
                fallback_query = apply_subdomain_filter(fallback_query, subdomain)
                all_nodes_guard = fallback_query.all()
                fallback_node = random.choice(all_nodes_guard) if all_nodes_guard else None
                if fallback_node:
                    skill_id = fallback_node.id
                else:
                    if subject in ["Matatag", "MATATAG", "matatag"]:
                        skill_id = f"mat_g{student_g}_na_q1_0" if student_g > 0 else "mat_g1_na_q1_0"
                    else:
                        skill_id = "K.CC.A.1" if student_g == 0 else "5.NF.A.1" if subject == "Math" else "RL.5.1"
                
    # 2. Check Domain (ELA vs Math vs MATATAG)
    is_ela = skill_id.startswith(("RL", "RI", "W", "L", "SL", "RF"))
    is_matatag = skill_id.startswith("mat_") or subject in ["Matatag", "MATATAG", "matatag"]
    
    if is_ela:
        question_mode = "mcq"

        # Load questions this student has already answered on this node — feed into
        # the LLM prompt so it knows exactly what to avoid (full question text, not just topics).
        _previous = _load_previous_questions(student_id, skill_id)

        # Retry logic for ELA MCQ to ensure correct_key matches correct_answer
        skeleton = None
        for _ in range(3):
            skeleton = subagents.generate_ela_skeleton_subagent(
                skill_id=skill_id,
                grade_level=student.grade,
                student_interest=_combined_interests(student, "reading"),
                language=student.language_preference,
                student_age=student.age,
                question_mode=question_mode,
                previous_questions=_previous if _previous else None,
            )


            # Validate correct_key alignment
            ck = skeleton.get("correct_key", "A").upper()
            ca = skeleton.get("correct_answer", "").strip()
            opt_val = skeleton.get("options", {}).get(ck, {}).get("value", "").strip()

            if ca and opt_val and (ca in opt_val or opt_val in ca):
                break
            print(f"[ELA Validation] Mismatch! Key {ck} has '{opt_val}' but expected '{ca}'. Retrying...")

        # NOTE: do NOT write to gen_problems.jsonl here.
        # We only record questions the student actually *answers* (in submit_practice_answer)
        # so that background pre-generation never pollutes the dedup history.

        ELA_SKELETON_CACHE[skeleton["skeleton_id"]] = skeleton
    else:
        # Unified v2 pipeline for MATATAG and Math
        from backend.app.practice_gen.pipeline import run as _pg_run
        
        # Load saved portal config for this node (allowed formatters etc.)
        _allowed_fmt = None
        if is_matatag:
            _cfg = db.query(models.CompetencyConfiguration).filter_by(node_id=skill_id).first()
            _allowed_fmt = _cfg.allowed_formatters if _cfg else None
        
        interest_theme = _combined_interests(student, "math")
        
        try:
            problem_dict = _pg_run(
                node_id=skill_id,
                student_grade=student.grade,
                student_interest=interest_theme,
                allowed_formatters=_allowed_fmt,
                experience="standard"
            )
            # Normalise to legacy format
            skeleton = problem_dict
            question_mode = problem_dict.get("format", "mcq")
            is_visual = problem_dict.get("is_visual", False)
            
            # Map complex formats to legacy question_mode for frontend compatibility
            if question_mode == "numeric_input":
                question_mode = "mcq"
            
        except Exception as _e:
            print(f"[V2 Pipeline Error] Node {skill_id} failed: {_e}. Falling back to minimal.")
            skeleton = {
                "skill_id": skill_id,
                "skeleton_id": f"fallback_{skill_id}",
                "stem_template": f"Practice problem for {skill_id}",
                "options": {"A": {"text": "No options available", "value": "N/A"}},
                "correct_key": "A",
                "correct_answer": "N/A",
                "is_visual": False
            }
            question_mode = "mcq"
            is_visual = False
            
        # Cache for answer validation
        if is_matatag:
            MATATAG_SKELETON_CACHE[skeleton["skeleton_id"]] = skeleton
        
        skeleton["standard_description"] = skeleton.get("competency_text", skill_id)

    # 3. Build options list (empty for writing prompts)
    options_list = []
    if skeleton.get("options"):
        for k, v in skeleton["options"].items():
            opt_text = str(v.get("text", v.get("value", ""))) if isinstance(v, dict) else str(v)
            options_list.append(schemas.QuestionOption(
                key=k,
                text=opt_text
            ))

    # 4. Check for Worked Examples (alternates for struggling students, Math only)
    consec_incorrect = 0
    m_state = db.query(models.MasteryState).filter(
        models.MasteryState.student_id == student_id,
        models.MasteryState.skill_id == skill_id
    ).first()
    if m_state:
        consec_incorrect = m_state.consecutive_incorrect

    is_worked_example = (not is_ela) and (consec_incorrect >= 1)
    worked_steps = skeleton.get("hints")

    # Check if this is a visual skeleton question
    is_visual = skeleton.get("is_visual", False)
    visual_type = skeleton.get("visual_type") if is_visual else None
    visual_params = skeleton.get("visual_params") if is_visual else None

    return schemas.QuestionResponse(
        skill_id=skill_id,
        skeleton_id=skeleton["skeleton_id"],
        stem=skeleton.get("stem_template", skeleton.get("stem", "")),
        options=options_list,
        is_worked_example=is_worked_example,
        worked_example_steps=worked_steps,
        is_placement=is_placement,
        placement_progress=progress if is_placement else None,
        question_mode=question_mode,
        standard_description=skeleton.get("standard_description"),
        domain=skeleton.get("domain"),
        visual_type=visual_type,
        visual_params=visual_params,
        is_visual=is_visual,
    )

@app.get("/api/practice/{student_id}/batch", response_model=List[schemas.QuestionResponse])
def get_practice_question_batch(
    student_id: int,
    count: int = 3,
    subject: str = "Math",
    subdomain: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Returns a batch of 3 questions.

    ELA/Verbal — batch-of-3 LLM strategy:
      Q1 is generated individually (runs full mastery/spaced-rep/ELO logic).
      Q2 and Q3 are generated in ONE additional LLM call that sees Q1 and the
      student's full answered-question history, so all three are guaranteed
      distinct.  All three are logged to gen_problems.jsonl at serve time.

    Math — cache-backed strategy (unchanged):
      SymPy skeletons are served from a pre-generated cache; the cache is
      replenished in the background after each batch is served.
      Cache target and worker count are scaled to the active AI backend so
      OpenCode-powered narration doesn't create a pile-up.
    """
    from backend.app.database import SessionLocal

    # Step 1: generate Q1 via the full pipeline (handles both ELA and Math correctly).
    # Q1 is always generated first so we can derive routing from the actual skill node
    # selected — not the subject string from the frontend, which may be a raw DB subject
    # name ("Language", "Writing", "Reading: Literature", etc.) rather than the
    # normalised "Verbal" sentinel value.
    db_q1 = SessionLocal()
    try:
        q1 = get_practice_question(student_id, subject, subdomain, db_q1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate question: {e}")
    finally:
        db_q1.close()

    # Placement questions are always delivered one at a time
    if q1.is_placement:
        return [q1]

    # Route based on the actual skill node selected by Q1, not the subject parameter.
    is_verbal = q1.skill_id.startswith(("RL", "RI", "W", "L", "SL", "RF"))

    # ── ELA / Verbal path ────────────────────────────────────────────────────
    if is_verbal:
        questions = [q1]

        # Step 2: build context for the batch call
        skill_id   = q1.skill_id
        q1_skeleton = ELA_SKELETON_CACHE.get(q1.skeleton_id, {})
        previous   = _load_previous_questions(student_id, skill_id)

        # Include Q1 so the batch LLM won't repeat it
        all_context = list(previous)
        if q1_skeleton:
            all_context.append({
                "problem_text": q1_skeleton.get("stem_template", ""),
                "answer":       q1_skeleton.get("correct_key", ""),
            })

        # Step 3: generate Q2 & Q3 in one LLM call
        student = db.query(models.StudentProfile).filter(
            models.StudentProfile.id == student_id
        ).first()
        q_mode = "mcq"

        batch_skeletons = subagents.generate_ela_batch_subagent(
            skill_id=skill_id,
            grade_level=student.grade if student else 5,
            student_interest=_combined_interests(student, "reading") if student else "reading",
            language=student.language_preference or "en" if student else "en",
            student_age=student.age or 10 if student else 10,
            n=2,
            question_mode=q_mode,
            previous_questions=all_context if all_context else None,
        )

        # Step 4: build QuestionResponse objects for Q2 & Q3
        for sk in batch_skeletons:
            ELA_SKELETON_CACHE[sk["skeleton_id"]] = sk
            opts = []
            for k, v in sk.get("options", {}).items():
                opts.append(schemas.QuestionOption(
                    key=k,
                    text=str(v.get("text", v.get("value", "")))
                ))
            questions.append(schemas.QuestionResponse(
                skill_id=skill_id,
                skeleton_id=sk["skeleton_id"],
                stem=sk.get("stem_template", ""),
                options=opts,
                is_worked_example=False,
                worked_example_steps=None,
                is_placement=False,
                placement_progress=None,
                question_mode=q_mode,
                standard_description=sk.get("standard_description"),
                domain=sk.get("domain"),
            ))

        # Step 5: log ALL questions at serve time so the next batch sees them
        all_skeletons = ([q1_skeleton] if q1_skeleton else []) + batch_skeletons
        for sk in all_skeletons:
            _save_practice_question(
                student_id, skill_id,
                sk.get("stem_template", ""),
                sk.get("correct_key", ""),
                "Verbal",
                sk.get("question_mode", "mcq"),
            )
        if all_skeletons:
            print(f"[ELA Batch] student={student_id} node={skill_id} "
                  f"→ served & logged {len(all_skeletons)} questions")

        return questions

    # ── Math / Matatag path (Unified v2 Pipeline) ────────────────────────────
    from backend.app.practice_gen.pipeline import run_batch as _pg_batch
    
    # Identify student
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    interest_theme = _combined_interests(student, "math") if student else "math"
    
    # Load config for MATATAG nodes
    is_matatag = q1.skill_id.startswith("mat_") or subject in ["Matatag", "MATATAG", "matatag"]
    _allowed_fmt = None
    if is_matatag:
        _cfg = db.query(models.CompetencyConfiguration).filter_by(node_id=q1.skill_id).first()
        _allowed_fmt = _cfg.allowed_formatters if _cfg else None
    
    try:
        # We already have q1, so we generate count-1 more problems
        additional_count = max(0, count - 1)
        batch = [q1]
        
        if additional_count > 0:
            new_problems = _pg_batch(
                node_id=q1.skill_id,
                grade=student.grade if student else 5,
                count=additional_count,
                student_interest=interest_theme,
                experience="standard"
            )
            
            for p in new_problems:
                # Normalise options
                options_list = []
                fmt_data = p.get("format_data", {})
                raw_opts = fmt_data.get("mcq_options") or fmt_data.get("options") or []
                
                if isinstance(raw_opts, list):
                    for o in raw_opts:
                        options_list.append(schemas.QuestionOption(
                            key=o.get("key", "A"), 
                            text=str(o.get("value", o.get("text", "")))
                        ))
                elif isinstance(raw_opts, dict):
                    for k, v in raw_opts.items():
                        opt_text = str(v.get("text", v.get("value", ""))) if isinstance(v, dict) else str(v)
                        options_list.append(schemas.QuestionOption(key=k, text=opt_text))

                is_vis = p.get("is_visual", False)
                q_mode = p.get("format", "mcq")
                if q_mode == "numeric_input": q_mode = "mcq"

                batch.append(schemas.QuestionResponse(
                    skill_id=q1.skill_id,
                    skeleton_id=p.get("problem_id"),
                    stem=p.get("question_text"),
                    options=options_list,
                    is_worked_example=False,
                    worked_example_steps=p.get("hints"),
                    is_placement=False,
                    placement_progress=None,
                    question_mode=q_mode,
                    standard_description=p.get("competency_text"),
                    domain=None,
                    visual_type=p.get("visual_type"),
                    visual_params=p.get("visual_params"),
                    is_visual=is_vis,
                ))
                
                if is_matatag:
                    MATATAG_SKELETON_CACHE[p["problem_id"]] = p
        
        # Log batch
        for q in batch:
            _save_practice_question(
                student_id, q1.skill_id, q.stem,
                answer="", subject=subject, question_mode=q.question_mode,
            )
        print(f"[V2 Batch] student={student_id} node={q1.skill_id} → served {len(batch)} questions")
        return batch
        
    except Exception as _e:
        print(f"[Batch Pipeline Error] Node {q1.skill_id} failed: {_e}. Falling back to single q1.")
        return [q1]

@app.post("/api/practice/placement/skip")
def skip_placement(req: schemas.PlacementSkipRequest, db: Session = Depends(get_db)):
    """
    Bypasses placement for a subject and seeds based on student grade.
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    placement.PlacementEngine.skip_placement(student, req.subject, db)
    return {"success": True}

@app.post("/api/practice/submit", response_model=schemas.AnswerSubmitResponse)
def submit_practice_answer(req: schemas.AnswerSubmitRequest, db: Session = Depends(get_db)):
    """
    Verifies student answers using SymPy, adjusts Elo, updates mastery state, and schedules reviews.
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    # Check Domain (ELA vs Math vs MATATAG)
    is_ela = req.skill_id.startswith(("RL", "RI", "W", "L", "SL", "RF"))
    # MATATAG: skeleton_id from v2 pipeline starts with mat_ (e.g. mat_g2_na_q2_0_12345_mcq)
    # Fallback skeletons start with "fallback_mat_". Also detect via skill_id prefix.
    is_matatag = (
        req.skeleton_id.startswith("mat_")
        or req.skeleton_id.startswith("fallback_mat_")
        or req.skill_id.startswith("mat_")
    )
    
    if is_ela:
        skeleton = ELA_SKELETON_CACHE.get(req.skeleton_id)
        if not skeleton:
            raise HTTPException(status_code=400, detail="ELA question session expired or invalid.")
        # Logging now happens at serve time in get_practice_question_batch(),
        # so the next batch's LLM has full context before the student even answers.
    elif is_matatag:
        # MATATAG skeleton — use cached skeleton or regenerate from skeleton_id
        skeleton = MATATAG_SKELETON_CACHE.get(req.skeleton_id)
        if not skeleton:
            # Reconstruct from seed via unified v2 pipeline
            import re
            match = re.search(r"_(\d+)$", req.skeleton_id)
            seed_val = int(match.group(1)) if match else None
            node_id = req.skeleton_id.rsplit('_', 1)[0] if match else req.skill_id
            
            from backend.app.practice_gen.pipeline import run as _pg_run
            try:
                # Parse grade level from node ID or default to student's grade
                grade_match = re.search(r"mat_g(\d+)", node_id)
                grade_val = int(grade_match.group(1)) if grade_match else (student.grade if student else 1)
                skeleton = _pg_run(node_id=node_id, student_grade=grade_val, seed=seed_val)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"MATATAG question session expired or invalid: {e}")
    elif req.skeleton_id.startswith("ai_"):
        # AI-generated Math fallback — graded by key comparison (like ELA)
        skeleton = MATH_AI_CACHE.get(req.skeleton_id)
        if not skeleton:
            raise HTTPException(status_code=400, detail="Math AI question session expired or invalid.")
    else:
        # Reconstruct from seed via unified v2 pipeline
        import re
        seed_val = None
        # Extract seed from format "{node_id}_{seed}"
        match = re.search(r"_(\d+)$", req.skeleton_id)
        if match:
            seed_val = int(match.group(1))

        from backend.app.practice_gen.pipeline import run as _pg_run
        skeleton = _pg_run(
            node_id=req.skill_id,
            student_grade=student.grade,
            seed=seed_val,
            student_interest=_combined_interests(student, "math")
        )

    # Grading
    if is_ela or req.skeleton_id.startswith("ai_"):
        # Key comparison for ELA and AI-generated Math
        is_correct = (req.selected_answer.upper() == skeleton.get("correct_key", "A").upper())
    elif is_matatag:
        # MATATAG — check format type
        fmt = skeleton.get("format", "mcq")
        if fmt == "mcq":
            is_correct = (req.selected_answer.upper() == skeleton.get("correct_key", "A").upper())
        elif fmt in ["cloze", "numeric_input", "ordering", "true_false", "error_detect", "fill_in_blank"]:
            student_answer = req.selected_answer.strip()
            correct_answer = skeleton.get("correct_answer")
            
            if fmt == "numeric_input":
                try:
                    student_val = float(student_answer.replace(",", "").replace("₱", ""))
                    correct_val = float(str(correct_answer).replace(",", "").replace("₱", ""))
                    is_correct = abs(student_val - correct_val) < 0.001
                except (ValueError, TypeError):
                    is_correct = str(student_answer) == str(correct_answer)
            elif fmt in ["cloze", "fill_in_blank"]:
                is_correct = student_answer.lower() == str(correct_answer).lower()
            elif fmt == "ordering":
                import json
                try:
                    student_seq = json.loads(student_answer) if isinstance(student_answer, str) else student_answer
                    correct_seq = correct_answer
                    if isinstance(correct_seq, str):
                        correct_seq = json.loads(correct_seq)
                    is_correct = [str(x) for x in student_seq] == [str(x) for x in correct_seq]
                except:
                    is_correct = str(student_answer) == str(correct_answer)
            elif fmt == "true_false":
                student_bool = student_answer.lower() in ("true", "yes", "t", "1")
                correct_bool = str(correct_answer).lower() in ("true", "yes", "t", "1")
                is_correct = student_bool == correct_bool
            elif fmt == "error_detect":
                import json
                try:
                    student_parsed = json.loads(student_answer) if isinstance(student_answer, str) else student_answer
                except:
                    student_parsed = {"has_error": True, "correct_value": student_answer}
                expected_has_error = correct_answer.get("has_error", True) if isinstance(correct_answer, dict) else True
                expected_value = correct_answer.get("correct_value") if isinstance(correct_answer, dict) else correct_answer
                student_has_error = student_parsed.get("has_error", True) if isinstance(student_parsed, dict) else True
                student_value = student_parsed.get("correct_value", student_answer) if isinstance(student_parsed, dict) else student_answer
                if expected_has_error:
                    if student_has_error:
                        try:
                            is_correct = abs(float(str(student_value)) - float(str(expected_value))) < 0.001
                        except:
                            is_correct = str(student_value) == str(expected_value)
                    else:
                        is_correct = False
                else:
                    is_correct = not student_has_error
            else:
                is_correct = str(student_answer) == str(correct_answer)
        else:
            is_visual = skeleton.get("is_visual", False)
            if is_visual:
                question_mode = skeleton.get("question_mode", "")
                visual_params = skeleton.get("visual_params", {})
                
                if question_mode == "ordering":
                    import json
                    try:
                        student_order = json.loads(req.selected_answer)
                    except:
                        student_order = req.selected_answer
                    correct_order = visual_params.get("correct_sequence", [])
                    student_order_str = [str(x) for x in student_order]
                    correct_order_str = [str(x) for x in correct_order]
                    is_correct = student_order_str == correct_order_str
                elif question_mode == "number_line":
                    try:
                        student_val = float(req.selected_answer)
                        correct_val = float(visual_params.get("correct_answer", visual_params.get("target", 0)))
                        tolerance = visual_params.get("tolerance", 0.5)
                        is_correct = abs(student_val - correct_val) <= tolerance
                    except:
                        is_correct = False
                elif question_mode in ["plotter_bar", "read_bar"]:
                    import json
                    try:
                        student_answer = json.loads(req.selected_answer) if isinstance(req.selected_answer, str) else req.selected_answer
                    except:
                        student_answer = req.selected_answer
                    correct_answer = visual_params.get("correct_answer")
                    is_correct = student_answer == correct_answer
                elif question_mode == "currency_picker":
                    import json
                    try:
                        student_answer = json.loads(req.selected_answer) if isinstance(req.selected_answer, str) else req.selected_answer
                        target_amount = visual_params.get("target_amount", 0)
                        student_total = student_answer.get("total", 0)
                        is_correct = student_total == target_amount
                    except:
                        is_correct = False
                elif question_mode == "clock_set":
                    import json
                    try:
                        student_answer = json.loads(req.selected_answer) if isinstance(req.selected_answer, str) else req.selected_answer
                        correct_time = visual_params.get("correct_time", {})
                        is_correct = (
                            student_answer.get("hour") == correct_time.get("hour") and
                            student_answer.get("minute") == correct_time.get("minute")
                        )
                    except:
                        is_correct = False
                else:
                    is_correct = (req.selected_answer.upper() == skeleton.get("correct_key", "A").upper())
            else:
                is_correct = (req.selected_answer.upper() == skeleton.get("correct_key", "A").upper())
    else:
        # SymPy Math — VALUE comparison (robust against narration shuffles and worked examples)
        selected_key = req.selected_answer.upper()
        if selected_key in skeleton["options"]:
            selected_opt = skeleton["options"][selected_key]
            is_correct = validate_math_answer(skeleton["correct_answer"], selected_opt["value"])
        else:
            # Worked example: student typed a raw value (e.g. "5/6")
            is_correct = validate_math_answer(skeleton["correct_answer"], req.selected_answer)
            
    # Identify Trap engineered misconception
    trap_selected = None
    if isinstance(skeleton.get("options"), dict):
        opt_data = skeleton["options"].get(req.selected_answer.upper())
        if isinstance(opt_data, dict):
            trap_selected = opt_data.get("trap_name")
            if trap_selected == "distractor":
                trap_selected = None
        elif isinstance(opt_data, tuple) and len(opt_data) > 1:
            trap_selected = opt_data[1]
            
    # Save the Attempt log in PostgreSQL
    new_attempt = models.Attempt(
        student_id=req.student_id,
        skill_id=req.skill_id,
        skeleton_id=req.skeleton_id,
        stem=req.stem,
        correct_answer=skeleton["correct_key"],
        selected_answer=req.selected_answer,
        is_correct=is_correct,
        response_time_ms=req.response_time_ms,
        trap_selected=trap_selected,
        telemetry_flagged=req.telemetry_flagged
    )
    db.add(new_attempt)
    
    # Fetch mastery state
    state = db.query(models.MasteryState).filter(
        models.MasteryState.student_id == req.student_id,
        models.MasteryState.skill_id == req.skill_id
    ).first()
    
    if not state:
        # Baseline mastery if not initialized
        state = models.MasteryState(
            student_id=req.student_id,
            skill_id=req.skill_id,
            status="active",
            elo_rating=1200.0,
            consecutive_correct=0,
            consecutive_incorrect=0
        )
        db.add(state)
    
    if state.consecutive_correct is None:
        state.consecutive_correct = 0
    if state.consecutive_incorrect is None:
        state.consecutive_incorrect = 0
        
    # ELO calculations
    if req.skill_id.startswith(("RL", "RI", "RF", "SL")):
        old_student_elo = student.elo_reading
    elif req.skill_id.startswith("W"):
        old_student_elo = student.elo_writing
    elif req.skill_id.startswith("L"):
        old_student_elo = student.elo_language
    else:
        old_student_elo = student.elo_math
        
    old_skill_elo = state.elo_rating
    
    # ELO update
    new_student_elo, new_skill_elo = update_elo(old_student_elo, old_skill_elo, is_correct)
    
    # Save Elo updates
    if req.skill_id.startswith(("RL", "RI", "RF", "SL")):
        student.elo_reading = new_student_elo
    elif req.skill_id.startswith("W"):
        student.elo_writing = new_student_elo
    elif req.skill_id.startswith("L"):
        student.elo_language = new_student_elo
    else:
        student.elo_math = new_student_elo
        student.elo_rating = new_student_elo # keep legacy updated too
        
    state.elo_rating = new_skill_elo
    
    # Consecutive trackers & Mastery status checks
    if is_correct:
        # Telemetry thinking-time guard (Finding 2.2)
        MIN_THINKING_TIME_MS = 3000
        if student.telemetry_enabled and req.response_time_ms < MIN_THINKING_TIME_MS:
            # Answer was correct, but submitted too fast (suspiciously like a guess).
            # Do NOT increment the consecutive correct streak.
            new_attempt.telemetry_flagged = True
            print(f"[Telemetry Guard] Student {req.student_id} answered {req.skill_id} correctly too fast ({req.response_time_ms}ms < {MIN_THINKING_TIME_MS}ms). Telemetry flagged, streak not advanced.")
        else:
            state.consecutive_correct += 1
            state.consecutive_incorrect = 0
            
            # 3 consecutive correct standard answers triggers MASTERY!
            if state.consecutive_correct >= 3:
                state.status = "mastered"
                
                # Unlock next skills linked by prerequisite edges!
                edges = db.query(models.SkillEdge).filter(models.SkillEdge.source_id == req.skill_id).all()
                for edge in edges:
                    target_state = db.query(models.MasteryState).filter(
                        models.MasteryState.student_id == req.student_id,
                        models.MasteryState.skill_id == edge.target_id
                    ).first()
                    if target_state and target_state.status == "locked":
                        target_state.status = "active"
                
                db.commit()
                
                # Automatically advance the subject frontier (Finding 2.5)
                current_node = db.query(models.SkillNode).filter(models.SkillNode.id == req.skill_id).first()
                if current_node:
                    check_and_advance_subject_frontier(req.student_id, current_node.subject, db)
                    
            # Schedule Spaced Repetition review!
            sr_card = db.query(models.SpacedRepetition).filter(
                models.SpacedRepetition.student_id == req.student_id,
                models.SpacedRepetition.skill_id == req.skill_id
            ).first()
            
            # Standard SM-2 Spaced Repetition formula
            if not sr_card:
                sr_card = models.SpacedRepetition(
                    student_id=req.student_id,
                    skill_id=req.skill_id,
                    repetitions=1,
                    interval_days=4.0, # 4 days baseline interval on first master
                    ease_factor=2.5,
                    due_date=datetime.datetime.utcnow() + datetime.timedelta(days=4)
                )
                db.add(sr_card)
            else:
                sr_card.repetitions += 1
                sr_card.interval_days *= 2.0 # Double review interval
                sr_card.due_date = datetime.datetime.utcnow() + datetime.timedelta(days=sr_card.interval_days)
    else:
        state.consecutive_incorrect += 1
        state.consecutive_correct = 0
        
        # If active student struggles (2 incorrect attempts), trigger REVIEW status
        if state.consecutive_incorrect >= 2:
            state.status = "review"
            
            # Shorten Spaced Repetition card review interval
            sr_card = db.query(models.SpacedRepetition).filter(
                models.SpacedRepetition.student_id == req.student_id,
                models.SpacedRepetition.skill_id == req.skill_id
            ).first()
            if sr_card:
                sr_card.repetitions = 0
                sr_card.interval_days = 1.0
                sr_card.due_date = datetime.datetime.utcnow() + datetime.timedelta(days=1)
                
    db.commit()
    
    # Generate Direct Subject-Aware Explanation
    is_ela = any(req.skill_id.startswith(p) for p in ["RL", "RI", "W", "L", "SL", "RF"])
    is_matatag = req.skeleton_id.startswith("mat_")
    
    if is_ela:
        std_desc = skeleton.get("standard_description", "")
        desc_suffix = f" (Focus standard: {std_desc})" if std_desc else ""
        ans_val = skeleton.get("correct_answer") or skeleton.get("correct_key") or ""
        if student.language_preference == "tl":
            explanation_text = f"Ang tamang sagot ay '{ans_val}'.{desc_suffix}"
        else:
            explanation_text = f"The correct answer is '{ans_val}'.{desc_suffix}"
    elif is_matatag:
        # MATATAG explanation - use stem as the expression
        stem = skeleton.get("stem_template") or skeleton.get("stem") or "the problem"
        correct_ans = skeleton.get("correct_answer", "")
        if student.language_preference == "tl":
            explanation_text = f"Ang tamang sagot sa '{stem}' ay {correct_ans}."
        else:
            explanation_text = f"The correct answer to '{stem}' is {correct_ans}."
    else:
        # Check cache first for custom narrative explanation (Finding 3.2)
        narrated_data = MATH_NARRATED_CACHE.get(req.skeleton_id)
        if narrated_data and "explanation" in narrated_data:
            explanation_text = narrated_data["explanation"]
        else:
            math_expr = skeleton.get('math_expression') or skeleton.get('stem_template') or 'the expression'
            correct_ans = skeleton.get('correct_answer', '')
            if student.language_preference == "tl":
                explanation_text = f"Ang math expression na {math_expr} ay nagreresulta sa {correct_ans}."
            else:
                explanation_text = f"The math expression {math_expr} simplifies to {correct_ans}."
    
    return schemas.AnswerSubmitResponse(
        is_correct=is_correct,
        correct_answer=skeleton["correct_key"],
        selected_answer=req.selected_answer,
        explanation=explanation_text,
        trap_selected=trap_selected,
        new_student_elo=new_student_elo,
        new_skill_elo=new_skill_elo,
        mastery_status=state.status
    )

@app.post("/api/practice/flag")
def flag_question(req: schemas.QuestionFlagRequest, db: Session = Depends(get_db)):
    """
    Stores a flagged question for post-mortem review.
    """
    new_flag = models.QuestionFlag(
        student_id=req.student_id,
        skill_id=req.skill_id,
        skeleton_id=req.skeleton_id,
        stem=req.stem,
        correct_answer=req.correct_answer,
        selected_answer=req.selected_answer,
        reason=req.reason,
        comment=req.comment
    )
    db.add(new_flag)
    db.commit()
    return {"success": True}

# --- SOCRATIC SPLIT ENDPOINTS ---

@app.post("/api/socratic/chat", response_model=schemas.SocraticChatResponse)
def socratic_chat_exchange(req: schemas.SocraticChatRequest, db: Session = Depends(get_db)):
    """
    Socratic Tutor split-screen dialog endpoint.
    Guides the student out of their misconception using active dialog.
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    # Prefer live context sent by the frontend (the actual question the student sees).
    # Fall back to the last DB attempt only when live context is not provided.
    if req.question_text:
        stem         = req.question_text
        selected_ans = req.student_answer or "not yet answered"
        correct_ans  = None   # Never expose — tutor must not reveal it
        trap_name    = "general_misconception"
    else:
        last_attempt = db.query(models.Attempt).filter(
            models.Attempt.student_id == req.student_id,
            models.Attempt.skill_id   == req.skill_id
        ).order_by(models.Attempt.created_at.desc()).first()
        trap_name    = last_attempt.trap_selected if last_attempt else "general_misconception"
        stem         = last_attempt.stem          if last_attempt else "Math problem"
        correct_ans  = None   # Never expose
        selected_ans = last_attempt.selected_answer if last_attempt else "not yet answered"

    # Append the newest message so the tutor actually sees what the student typed!
    full_history = list(req.history)
    full_history.append(schemas.SocraticChatMessage(role="user", content=req.message))

    result = subagents.socratic_tutor_subagent(
        skill_id=req.skill_id,
        stem=stem,
        correct_answer=correct_ans,
        selected_answer=selected_ans,
        trap_name=trap_name,
        chat_history=full_history,
        language=student.language_preference,
        student_interest=_combined_interests(student),
        student_age=student.age,
        student_grade=student.grade,
        is_intro=req.is_intro or False,
    )
    
    # If Socratic tutor marks the misconception as fully resolved, update student state!
    if result.get("resolved"):
        state = db.query(models.MasteryState).filter(
            models.MasteryState.student_id == req.student_id,
            models.MasteryState.skill_id == req.skill_id
        ).first()
        if state:
            state.status = "active" # Reset from review to active practice
            state.consecutive_incorrect = 0
            db.commit()
            
    return schemas.SocraticChatResponse(
        reply=result["reply"],
        resolved=result["resolved"]
    )




# ============================================================================
#  VISUAL SKELETONS ENDPOINTS (Problem Lab)
# ============================================================================

# Load MATATAG competencies and visual mappings (cached at module load)
_MATATAG_PATH = Path(__file__).parent.parent.parent / "data" / "ph" / "matatagmath.json"
_VISUAL_MAPPING_PATH = Path(__file__).parent.parent.parent / "data" / "ph" / "competency_visual_mapping.json"

_MATATAG_DATA = {}
_VISUAL_MAPPINGS = []

if _MATATAG_PATH.exists():
    with open(_MATATAG_PATH, encoding="utf-8") as f:
        _MATATAG_DATA = json.load(f).get("Mathematics", {})

if _VISUAL_MAPPING_PATH.exists():
    with open(_VISUAL_MAPPING_PATH, encoding="utf-8") as f:
        _VISUAL_MAPPINGS = json.load(f).get("mappings", [])


def _match_competency_to_visual_type(competency_text: str, grade: int) -> Optional[Dict[str, Any]]:
    """
    Match a MATATAG competency to a visual skeleton type using regex patterns.
    Returns the first matching mapping that supports the grade, or None.
    Also extracts sub_pattern hints for the generator.
    """
    # Sort by priority (lower = higher priority)
    sorted_mappings = sorted(_VISUAL_MAPPINGS, key=lambda x: x.get("priority", 999))
    
    for mapping in sorted_mappings:
        if grade not in mapping.get("grades", []):
            continue
        pattern = mapping.get("pattern", "")
        if re.search(pattern, competency_text, re.IGNORECASE):
            # Found a match - now extract sub_pattern hints
            result = mapping.copy()
            hints = []
            for sub in mapping.get("sub_patterns", []):
                sub_pattern = sub.get("match", "")
                if sub_pattern and re.search(sub_pattern, competency_text, re.IGNORECASE):
                    hints.append(sub.get("hint", ""))
            result["matched_hints"] = hints
            return result
    return None



@app.get("/api/matatag/competencies")
def get_matatag_competencies(
    grade: Optional[int] = Query(None, description="Filter by grade (1-10)"),
    strand: Optional[str] = Query(None, description="Filter by strand"),
    quarter: Optional[str] = Query(None, description="Filter by quarter"),
):
    """
    Return MATATAG competencies for dropdown selection in Problem Lab.
    
    Response structure:
    {
      "grades": [1, 2, ..., 10],
      "strands": ["Number and Algebra", "Measurement and Geometry", ...],
      "quarters": ["Quarter 1", "Quarter 2", ...],
      "competencies": [
        {
          "grade": 4,
          "strand": "Number and Algebra",
          "quarter": "Quarter 2",
          "text": "Plot fractions on the number line...",
          "visual_type": "NumberLine",
          "question_mode": "number_line"
        },
        ...
      ]
    }
    """
    result = {
        "grades": [],
        "strands": set(),
        "quarters": set(),
        "competencies": []
    }
    
    for grade_key, grade_data in _MATATAG_DATA.items():
        grade_num = int(grade_key.split()[1]) if "Grade" in grade_key else 0
        if grade_num == 0:
            continue
            
        result["grades"].append(grade_num)
        
        for strand_name, strand_data in grade_data.items():
            result["strands"].add(strand_name)
            
            for quarter_name, competencies in strand_data.items():
                result["quarters"].add(quarter_name)
                
                # Apply filters
                if grade and grade_num != grade:
                    continue
                if strand and strand_name != strand:
                    continue
                if quarter and quarter_name != quarter:
                    continue
                
                for comp_text in competencies:
                    # Check if this competency matches a visual type
                    mapping = _match_competency_to_visual_type(comp_text, grade_num)
                    if mapping:
                        result["competencies"].append({
                            "grade": grade_num,
                            "strand": strand_name,
                            "quarter": quarter_name,
                            "text": comp_text,
                            "visual_type": mapping["visual_type"],
                            "question_mode": mapping["question_mode"]
                        })
    
    # Convert sets to sorted lists
    result["grades"] = sorted(set(result["grades"]))
    result["strands"] = sorted(result["strands"])
    result["quarters"] = sorted(result["quarters"])
    
    return result


def _get_available_formats(node_id: str) -> list:
    """Return which formats are available for a node: ['mcq'], ['visual'], or ['mcq','visual']."""
    from backend.app.practice_gen.registry import get_node_dnas
    from backend.app.practice_gen.compatibility import get_formatters_for_dna
    
    dnas = get_node_dnas(node_id)
    if not dnas:
        return ["mcq"]
        
    fmts = get_formatters_for_dna(dnas[0])
    has_visual = any(f not in ["mcq", "numeric_input", "cloze"] for f in fmts)
    has_mcq = "mcq" in fmts or "numeric_input" in fmts
    
    res = []
    if has_mcq: res.append("mcq")
    if has_visual: res.append("visual")
    return res if res else ["mcq"]


@app.get("/api/matatag/nodes")
def get_matatag_nodes(
    grade: Optional[int] = Query(None, description="Filter by grade (1–3)"),
    branch: Optional[str] = Query(None, description="Filter by branch: na, mg, dp"),
):
    try:
        node_ids = _pg_registry.get_all_node_ids(grade=grade, branch=branch)
        nodes = []
        for nid in node_ids:
            info = _pg_registry.get_node_info(nid)
            if not info:
                continue
            dnas = _pg_registry.get_node_dnas(nid)
            primary_concept = dnas[0] if dnas else ""
            parts = nid.split("_")
            # mat_g{grade}_{branch}_q{quarter}_{index}
            n_grade  = int(parts[1][1:])
            n_branch = parts[2].upper()
            n_quarter = int(parts[3][1:])
            n_index   = int(parts[4])
            comp = info.get("competency", "")
            # Build a short label: first 90 chars of competency with context prefix
            short = comp[:90] + ("…" if len(comp) > 90 else "")
            label = f"G{n_grade} {n_branch} Q{n_quarter} · {primary_concept} — {short}"
            nodes.append({
                "node_id": nid,
                "grade": n_grade,
                "branch": parts[2],
                "quarter": n_quarter,
                "index": n_index,
                "competency": comp,
                "primary_concept": primary_concept,
                "label": label,
                "available_formats": _get_available_formats(nid),
            })
        return {"nodes": nodes}
    except Exception as e:
        print(f"CRITICAL ERROR in get_matatag_nodes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load nodes: {str(e)}")


@app.get("/api/matatag/difficulty-axes/{node_id}")
def get_matatag_difficulty_axes(node_id: str):
    """
    Return the difficulty axes for a specific MATATAG node.

    Axes are specific to the primary DNA concept of the node.
    Each axis has ordered options (easy → hard) with human-readable labels.

    Response:
    {
      "node_id": "mat_g1_na_q1_8",
      "primary_concept": "addition",
      "axes": [
        {
          "name": "regrouping",
          "label": "Regrouping (Carrying)",
          "options": [
            {"value": "none",   "label": "No Regrouping"},
            {"value": "ones",   "label": "Regroup Ones"},
            ...
          ],
          "default": "none"
        },
        ...
      ]
    }
    """
    dnas = _pg_registry.get_node_dnas(node_id)
    if not dnas:
        raise HTTPException(
            status_code=404,
            detail=f"Node '{node_id}' not found in G1–3 registry."
        )
    primary_concept = dnas[0]
    axes = _get_axes_for_concept(primary_concept)
    competency_bounds = _pg_registry.get_node_competency_bounds(node_id)

    resolved_axes = []
    for axis in axes:
        axis_name = axis["name"]
        
        # Dynamic axis filtering: Drop discrete axes that are strictly locked by curriculum constraints
        if axis_name in competency_bounds and isinstance(competency_bounds[axis_name], bool):
            continue

        dim_type = axis.get("dim_type", "discrete")
        
        if dim_type == "continuous":
            bounds = competency_bounds.get(axis_name)
            if bounds:
                min_val, max_val = bounds
            else:
                min_val = axis.get("default_min", 1)
                max_val = axis.get("default_max", 100)
            
            divisions = axis.get("divisions", 5)
            options = []
            for i in range(divisions):
                scalar = i / (divisions - 1) if divisions > 1 else 0.0
                if isinstance(min_val, float) or isinstance(max_val, float) or (max_val - min_val <= 2):
                    value = round(min_val + scalar * (max_val - min_val), 2)
                else:
                    value = int(min_val + scalar * (max_val - min_val))
                options.append({
                    "value": value,
                    "label": f"Up to {value} (scalar={scalar:.2f})",
                })
            # Add advanced (bridge zone) scalar of 1.25 for max_sum
            if axis_name == "max_sum":
                bridge_scalar = 1.25
                bridge_value = int(min_val + bridge_scalar * (max_val - min_val))
                options.append({
                    "value": bridge_value,
                    "label": f"Up to {bridge_value} (scalar={bridge_scalar:.2f}) [Bridge]",
                })
            
            resolved_axes.append({
                "name": axis_name,
                "label": axis["label"],
                "options": options,
                "default": axis.get("default", 0.5),
            })
        else:
            options = axis.get("options", [])
            if axis_name == "skip_interval" and "skip_pool" in competency_bounds:
                skip_pool = competency_bounds["skip_pool"]
                filtered_options = []
                for opt in options:
                    val = opt["value"]
                    if val == "by_1" and 1 in skip_pool:
                        filtered_options.append(opt)
                    elif val == "by_2_5_10" and any(x in skip_pool for x in (2, 5, 10)):
                        filtered_options.append(opt)
                    elif val == "by_20_50_100" and any(x in skip_pool for x in (20, 50, 100)):
                        filtered_options.append(opt)
                options = filtered_options

            resolved_axes.append({
                "name": axis_name,
                "label": axis["label"],
                "options": options,
                "default": axis.get("default", "none"),
            })

    return {
        "node_id": node_id,
        "primary_concept": primary_concept,
        "axes": resolved_axes,
    }


@app.get("/api/matatag/lab/config/{node_id}")
def get_matatag_lab_config(node_id: str):
    """
    Return full lab configuration for a MATATAG node.

    Includes:
    - difficulty_dimensions: Each has d options showing scalar and output range
    - contextual_variants: Random selection options (not difficulty)
    - formatters: Compatible problem types with variant restrictions

    Response example for "addition":
    {
      "node_id": "mat_g1_na_q1_8",
      "primary_concept": "addition",
      "grade": 1,
      "difficulty_dimensions": [
        {
          "name": "regrouping",
          "label": "Regrouping (Carrying)",
          "dim_type": "discrete",
          "options": [
            {"scalar": 0.0, "level": "none", "label": "No Regrouping (scalar=0.0)"},
            {"scalar": 0.33, "level": "ones", "label": "Regroup Ones (scalar=0.33)"},
            {"scalar": 0.67, "level": "tens", "label": "Regroup Tens (scalar=0.67)"},
            {"scalar": 1.0, "level": "double", "label": "Regroup Both (scalar=1.0)"}
          ],
          "default_scalar": 0.0
        },
        ...
      ],
      "contextual_variants": [
        {
          "name": "task_type",
          "label": "Task Type",
          "options": ["find_sum", "find_addend"],
          "default": "find_sum"
        },
        ...
      ],
      "formatters": [
        {
          "name": "mcq",
          "label": "Multiple Choice",
          "supports_all_variants": true
        },
        {
          "name": "number_line_read",
          "label": "Number Line (Read)",
          "variant_restrictions": {"task_type": ["find_sum"]}
        },
        ...
      ]
    }
    """
    import math
    from backend.app.practice_gen.compatibility import (
        COMPATIBILITY,
        VARIANTS_BY_DNA,
        FORMATTER_VARIANT_SUPPORT,
        get_supported_variants,
    )

    # Resolve node info
    info = _pg_registry.get_node_info(node_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    dnas = _pg_registry.get_node_dnas(node_id)
    if not dnas:
        raise HTTPException(status_code=404, detail=f"No DNA found for node '{node_id}'.")

    primary_concept = dnas[0]
    grade = info.get("grade", 1)
    competency = info.get("competency", "")

    # Get competency-specific bounds from parsed competency text
    competency_bounds = _pg_registry.get_node_competency_bounds(node_id)

    # Get axes from existing catalog (these are the difficulty dimensions)
    axes = _get_axes_for_concept(primary_concept)

    # Build difficulty_dimensions with proper handling of continuous vs discrete
    difficulty_dimensions = []
    for axis in axes:
        axis_name = axis["name"]
        
        # Dynamic axis filtering: Drop discrete axes that are strictly locked by curriculum constraints
        if axis_name in competency_bounds and isinstance(competency_bounds[axis_name], bool):
            continue
            
        dim_type = axis.get("dim_type", "discrete")
        
        if dim_type == "continuous":
            # Continuous dimension: scalar 0-1 maps to numeric range
            # Use competency bounds if available, otherwise use defaults
            bounds = competency_bounds.get(axis_name)
            if bounds:
                min_val, max_val = bounds
            else:
                min_val = axis.get("default_min", 1)
                max_val = axis.get("default_max", 100)
            
            divisions = axis.get("divisions", 5)
            
            scale_type = axis.get("scale", "linear")
            options = []
            for i in range(divisions):
                scalar = i / (divisions - 1) if divisions > 1 else 0.0
                
                if scale_type == "logarithmic":
                    import math
                    # Use a shifted log scale to handle 0
                    shift = 1 if min_val == 0 else 0
                    log_min = math.log10(min_val + shift)
                    log_max = math.log10(max_val + shift)
                    log_val = log_min + scalar * (log_max - log_min)
                    value = int(math.pow(10, log_val)) - shift
                else:
                    if isinstance(min_val, float) or isinstance(max_val, float) or (max_val - min_val <= 2):
                        value = round(min_val + scalar * (max_val - min_val), 2)
                    else:
                        value = int(min_val + scalar * (max_val - min_val))
                        
                options.append({
                    "scalar": round(scalar, 2),
                    "value": value,
                    "label": f"Up to {value} (scalar={scalar:.2f})",
                })
            
            # Add advanced (bridge zone) scalar of 1.25 for max_sum
            if axis_name == "max_sum":
                bridge_scalar = 1.25
                bridge_value = int(min_val + bridge_scalar * (max_val - min_val))
                options.append({
                    "scalar": bridge_scalar,
                    "value": bridge_value,
                    "label": f"Up to {bridge_value} (scalar={bridge_scalar:.2f}) [Bridge]",
                })
            
            difficulty_dimensions.append({
                "name": axis_name,
                "label": axis["label"],
                "dim_type": "continuous",
                "min_value": min_val,
                "max_value": max_val,
                "divisions": divisions,
                "options": options,
                "default_scalar": axis.get("default", 0.0),
            })
        else:
            # Discrete dimension: filter by competency bounds if applicable
            all_levels = axis.get("options", [])
            levels = all_levels  # Default to all levels
            
            if axis_name == "skip_interval" and "skip_pool" in competency_bounds:
                skip_pool = competency_bounds["skip_pool"]
                filtered_options = []
                for opt in levels:
                    val = opt["value"]
                    if val == "by_1" and 1 in skip_pool:
                        filtered_options.append(opt)
                    elif val == "by_2_5_10" and any(x in skip_pool for x in (2, 5, 10)):
                        filtered_options.append(opt)
                    elif val == "by_20_50_100" and any(x in skip_pool for x in (20, 50, 100)):
                        filtered_options.append(opt)
                levels = filtered_options
            
            d = len(levels)
            options = []

            for i, opt in enumerate(levels):
                scalar = i / (d - 1) if d > 1 else 0.0
                options.append({
                    "scalar": round(scalar, 2),
                    "level": opt["value"],
                    "label": f"{opt['label']} (scalar={scalar:.2f})",
                })

            difficulty_dimensions.append({
                "name": axis_name,
                "label": axis["label"],
                "dim_type": "discrete",
                "options": options,
                "default_scalar": 0.0,
            })

    # Build contextual_variants from compatibility.py
    variants = VARIANTS_BY_DNA.get(primary_concept, {})
    contextual_variants = []
    for var_name, var_options in variants.items():
        # Skip if this is already a difficulty dimension
        if any(d["name"] == var_name for d in difficulty_dimensions):
            continue
        contextual_variants.append({
            "name": var_name,
            "label": var_name.replace("_", " ").title(),
            "options": var_options,
            "default": var_options[0] if var_options else None,
        })

    # Build formatters list from compatibility table
    available_formatters = COMPATIBILITY.get(primary_concept, ["mcq"])
    formatters = []

    # Formatter display names
    FORMATTER_LABELS = {
        "mcq": "Multiple Choice",
        "cloze": "Fill in the Blank (Cloze)",
        "numeric_input": "Numeric Input",
        "ordering": "Ordering",
        "true_false": "True/False",
        "error_detect": "Error Detection",
        "number_line_read": "Number Line (Read)",
        "number_line_set": "Number Line (Set)",
        "number_bond": "Number Bond",
        "array_grid_read": "Array Grid (Read)",
        "array_grid_set": "Array Grid (Set)",
        "place_value_blocks_read": "Place Value Blocks (Read)",
        "place_value_blocks_set": "Place Value Blocks (Set)",
        "peso_money_read": "Money (Read)",
        "peso_money_build": "Money (Build)",
        "clock_read": "Clock (Read)",
        "clock_set": "Clock (Set)",
        "bar_chart_read": "Bar Chart (Read)",
        "bar_chart_set": "Bar Chart (Set)",
        "pictograph_read": "Pictograph (Read)",
        "fraction_model_read": "Fraction Model (Read)",
        "fraction_shade": "Fraction Model (Shade)",
        "ruler_measure": "Ruler Measurement",
        "grid_area": "Grid Area",
        "sort_order": "Sort Order",
        "shape_board": "Shape Board",
        "ten_frame": "Ten Frame",
        "balance_scale": "Balance Scale",
        "pattern_sequence": "Pattern Sequence",
        "calendar_read": "Calendar (Read)",
        "categorize": "Categorize",
        "fill_in_table": "Fill in Table",
    }

    dna_restrictions = FORMATTER_VARIANT_SUPPORT.get(primary_concept, {})

    for fmt in available_formatters:
        fmt_restrictions = dna_restrictions.get(fmt)
        if fmt_restrictions is None:
            # No restrictions - supports all variants
            formatters.append({
                "name": fmt,
                "label": FORMATTER_LABELS.get(fmt, fmt),
                "supports_all_variants": True,
            })
        else:
            # Has restrictions
            formatters.append({
                "name": fmt,
                "label": FORMATTER_LABELS.get(fmt, fmt),
                "supports_all_variants": len(fmt_restrictions) == 0,
                "variant_restrictions": fmt_restrictions if fmt_restrictions else None,
            })

    return {
        "node_id": node_id,
        "primary_concept": primary_concept,
        "grade": grade,
        "competency": competency,
        "difficulty_dimensions": difficulty_dimensions,
        "contextual_variants": contextual_variants,
        "formatters": formatters,
    }


@app.get("/api/matatag/lab/interests")
def get_matatag_lab_interests():
    """
    Return ALL available interest themes for word problem personalization.
    
    All data comes from data/interest_bank.json - the single source of truth.
    Update that file to add/modify interests without code changes.
    
    Note: Grade bands are ignored - all interests are available for all grades.
    
    Returns:
        - interest_id: Key for the interest (matches key in interest_bank.json)
        - name: Display name
        - emoji: Visual indicator
    """
    from backend.app.practice_gen.generators.interest import _INTERESTS
    
    interests = []
    
    # Return ALL interests from the JSON file (no grade filtering)
    for interest_id, data in _INTERESTS.items():
        interests.append({
            "interest_id": interest_id,
            "name": data.get("name", interest_id.replace("_", " ").title()),
            "emoji": data.get("emoji", "📦"),
        })
    
    # Sort by name for consistent display
    interests.sort(key=lambda x: x["name"])
    
    # Add "Random" option at the beginning
    interests.insert(0, {
        "interest_id": None,
        "name": "Random (any theme)",
        "emoji": "🎲",
    })
    
    return {
        "interests": interests,
        "source": "data/interest_bank.json",
        "total_count": len(_INTERESTS),
    }


@app.get("/api/matatag/lab/generate")
def matatag_lab_generate(
    node_id: str = Query(..., description="MATATAG node_id, e.g. mat_g1_na_q1_8"),
    axis_values: Optional[str] = Query(None, description="JSON-encoded axis selections"),
    seed: Optional[int] = Query(None, description="Optional seed for reproducibility"),
    difficulty: Optional[float] = Query(None, description="Difficulty scalar 0.0-1.0"),
    format_preference: Optional[str] = Query("auto", description="'visual', 'mcq', or 'auto'"),
):
    """
    Generate a practice problem for the MATATAG Problem Lab.

    Works for ALL 151 G1-3 nodes.
    format_preference controls which type is returned:
      'visual' → always visual (error if unavailable)
      'mcq'    → always MCQ
      'auto'   → random 50/50 when both available, otherwise whichever is available
    """
    # Resolve node info
    info = _pg_registry.get_node_info(node_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")
    grade = info.get("grade", 1)

    # Compute effective difficulty from axis values
    dnas = _pg_registry.get_node_dnas(node_id)
    primary_concept = dnas[0] if dnas else ""
    parsed_axes = {}
    if axis_values:
        try:
            parsed_axes = json.loads(axis_values)
        except (json.JSONDecodeError, ValueError):
            parsed_axes = {}

    if difficulty is not None:
        effective_difficulty = max(0.0, min(1.0, difficulty))
    else:
        effective_difficulty = _compute_difficulty_scalar(primary_concept, parsed_axes)

    if seed is None:
        import random as _rand
        seed = _rand.randint(10000, 999999)

    # Determine allowed formatters based on format_preference
    allowed_fmt = None
    if format_preference == "visual":
        # Filter for non-textual formatters
        from backend.app.practice_gen.compatibility import get_formatters_for_dna
        dnas = _pg_registry.get_node_dnas(node_id)
        if dnas:
            all_fmts = get_formatters_for_dna(dnas[0])
            allowed_fmt = [f for f in all_fmts if f not in ["mcq", "numeric_input", "cloze"]]
    elif format_preference == "mcq":
        allowed_fmt = ["mcq"]

    try:
        skeleton = pipeline.run(
            node_id=node_id,
            student_grade=grade,
            difficulty_profile=parsed_axes if parsed_axes else {"range": effective_difficulty},
            seed=seed,
            allowed_formatters=allowed_fmt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    # Cache for answer submission
    MATATAG_SKELETON_CACHE[skeleton["skeleton_id"]] = skeleton

    # Build unified response
    is_visual = skeleton.get("is_visual", False)

    # For MCQ, normalise options to a list [{key, text}]
    mcq_options = []
    correct_key = None
    if not is_visual:
        raw_opts = skeleton.get("options", {})
        correct_key = skeleton.get("correct_key")
        if not correct_key:
            # Derive correct_key from options where trap is None
            for k, v in raw_opts.items():
                if isinstance(v, dict) and v.get("trap") is None:
                    correct_key = k
                    break
        for k in ["A", "B", "C", "D"]:
            if k in raw_opts:
                opt = raw_opts[k]
                if isinstance(opt, dict):
                    mcq_options.append({"key": k, "text": str(opt.get("text", opt.get("value", "")))})
                else:
                    mcq_options.append({"key": k, "text": str(opt)})

    return {
        "skeleton_id": skeleton["skeleton_id"],
        "node_id": node_id,
        "competency_text": competency,
        "grade": grade,
        "difficulty": effective_difficulty,
        "axis_values": parsed_axes,
        "primary_concept": primary_concept,
        "available_formats": available_formats,
        "format_used": "visual" if is_visual else "mcq",

        # Question content
        "stem": skeleton.get("stem", ""),
        "is_visual": is_visual,

        # Visual fields (only when is_visual=True)
        "visual_type": skeleton.get("visual_type"),
        "visual_params": skeleton.get("visual_params"),
        "question_mode": skeleton.get("question_mode"),
        "all_traps": skeleton.get("all_traps"),

        # MCQ fields (only when is_visual=False)
        "mcq_options": mcq_options,
    }


@app.post("/api/matatag/lab/submit")
def matatag_lab_submit(
    skeleton_id: str = Query(..., description="Skeleton ID from /api/matatag/lab/generate"),
    student_answer: str = Query(..., description="Student answer: option key (A/B/C/D) for MCQ, or JSON for visual"),
):
    """
    Grade a MATATAG Lab answer.  Handles both visual and MCQ skeleton types.

    Returns:
    {
        "is_correct": bool,
        "correct_answer": str,
        "trap_triggered": str | null,
        "explanation": str
    }
    """
    skeleton = MATATAG_SKELETON_CACHE.get(skeleton_id)
    if not skeleton:
        # Attempt to regenerate from skeleton_id using v2 pipeline
        try:
            import re
            # Extract seed from format "{node_id}_{seed}"
            match = re.search(r"_(\d+)$", skeleton_id)
            seed_val = int(match.group(1)) if match else None
            node_id = skeleton_id.rsplit('_', 1)[0] if match else skeleton_id
            
            from backend.app.practice_gen.pipeline import run as _pg_run
            # Parse grade level from node ID
            grade_match = re.search(r"mat_g(\d+)", node_id)
            grade_val = int(grade_match.group(1)) if grade_match else 1
            skeleton = _pg_run(node_id=node_id, student_grade=grade_val, seed=seed_val)
        except Exception:
            raise HTTPException(status_code=404, detail="Question session expired. Please generate a new problem.")

    is_visual = skeleton.get("is_visual", False)
    is_correct = False
    correct_answer_str = ""
    trap_triggered = None

    if is_visual:
        # Delegate to the existing visual submit logic
        visual_params = skeleton.get("visual_params", {})
        question_mode = skeleton.get("question_mode", "")

        try:
            parsed = json.loads(student_answer)
        except (json.JSONDecodeError, ValueError):
            parsed = student_answer

        # Validate against the CACHED skeleton's correct_answer (not a regenerated one)
        # Regeneration without axis_values would produce a different problem
        correct_raw = skeleton.get("correct_answer")
        visual_type = skeleton.get("visual_type", "")

        if visual_type == "PesoMoney":
            # Student submits the total amount as a number
            try:
                student_val = int(str(parsed).replace("₱", "").strip())
            except (ValueError, TypeError):
                student_val = -1
            is_correct = student_val == int(str(correct_raw))
            correct_answer_str = str(correct_raw)

        elif visual_type == "ClockSet":
            # Student submits {"hours": h, "minutes": m}
            try:
                if isinstance(parsed, dict):
                    sh, sm = int(parsed.get("hours", -1)), int(parsed.get("minutes", -1))
                elif isinstance(parsed, str) and ":" in parsed:
                    sh, sm = [int(x) for x in parsed.split(":")]
                else:
                    sh, sm = -1, -1

                # correct_raw may be (h, m) tuple, [h, m] list, or "(h, m)" string
                if isinstance(correct_raw, (list, tuple)) and len(correct_raw) == 2:
                    ch, cm = int(correct_raw[0]), int(correct_raw[1])
                elif isinstance(correct_raw, str):
                    # Parse "(3, 20)" or "3:20" or "[3, 20]"
                    nums = [int(x) for x in re.findall(r'\d+', correct_raw)]
                    ch, cm = (nums[0], nums[1]) if len(nums) >= 2 else (-1, -1)
                else:
                    ch, cm = -1, -1
                is_correct = (sh == ch and sm == cm)
            except (ValueError, TypeError, AttributeError):
                is_correct = False
            correct_answer_str = str(correct_raw)

        elif visual_type == "SortOrder":
            import ast as _ast
            try:
                if isinstance(parsed, str):
                    try:
                        parsed = json.loads(parsed)
                    except json.JSONDecodeError:
                        parsed = _ast.literal_eval(parsed)
                if isinstance(correct_raw, str):
                    try:
                        correct_raw = json.loads(correct_raw)
                    except json.JSONDecodeError:
                        correct_raw = _ast.literal_eval(correct_raw)
                # Compare element by element with type coercion
                if isinstance(parsed, list) and isinstance(correct_raw, list):
                    is_correct = (len(parsed) == len(correct_raw) and
                                  all(str(a) == str(b) for a, b in zip(parsed, correct_raw)))
                else:
                    is_correct = str(parsed) == str(correct_raw)
            except (json.JSONDecodeError, ValueError, TypeError):
                is_correct = str(parsed) == str(correct_raw)
            correct_answer_str = str(correct_raw)

        elif visual_type == "Categorize":
            import ast as _ast
            try:
                if isinstance(parsed, str):
                    try:
                        parsed = json.loads(parsed)
                    except json.JSONDecodeError:
                        parsed = _ast.literal_eval(parsed)
                if isinstance(correct_raw, str):
                    try:
                        correct_raw = json.loads(correct_raw)
                    except json.JSONDecodeError:
                        correct_raw = _ast.literal_eval(correct_raw)
                # Normalize keys to strings for comparison
                if isinstance(parsed, dict) and isinstance(correct_raw, dict):
                    parsed_norm = {str(k): str(v) for k, v in parsed.items()}
                    correct_norm = {str(k): str(v) for k, v in correct_raw.items()}
                    is_correct = parsed_norm == correct_norm
                else:
                    is_correct = str(parsed) == str(correct_raw)
            except (json.JSONDecodeError, TypeError):
                is_correct = str(parsed) == str(correct_raw)
            correct_answer_str = str(correct_raw)

        else:
            # Fallback: direct comparison
            is_correct = str(parsed) == str(correct_raw)
            correct_answer_str = str(correct_raw)
    else:
        # MCQ: compare selected key to correct_key
        raw_opts = skeleton.get("options", {})
        correct_key = skeleton.get("correct_key")
        if not correct_key:
            for k, v in raw_opts.items():
                if isinstance(v, dict) and v.get("trap") is None:
                    correct_key = k
                    break
        is_correct = student_answer.upper() == (correct_key or "A").upper()

        # Get the text of the correct option for display
        correct_opt = raw_opts.get(correct_key, {})
        if isinstance(correct_opt, dict):
            correct_answer_str = str(correct_opt.get("text", correct_opt.get("value", correct_key)))
        else:
            correct_answer_str = str(correct_opt)

        # Check if student triggered a trap
        selected_opt = raw_opts.get(student_answer.upper(), {})
        if not is_correct and isinstance(selected_opt, dict):
            trap_triggered = selected_opt.get("trap")

    explanation = (
        f"Correct! The answer is {correct_answer_str}."
        if is_correct
        else f"Not quite. The correct answer is {correct_answer_str}."
    )

    return {
        "is_correct": is_correct,
        "correct_answer": correct_answer_str,
        "trap_triggered": trap_triggered,
        "explanation": explanation,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MATATAG LAB V2 — New Practice Gen Pipeline
# Uses the new DNA → Context → Formatter pipeline with full formatter control
# ═══════════════════════════════════════════════════════════════════════════════

from pydantic import BaseModel as PydanticBaseModel

class LabV2GenerateRequest(PydanticBaseModel):
    """Request body for /api/matatag/lab/v2/generate"""
    node_id: str
    formatter: str = "mcq"
    difficulty_profile: Optional[Dict[str, Any]] = None  # {axis: level_or_value}
    variant_values: Optional[Dict[str, str]] = None      # {variant: value}
    interest_theme: Optional[str] = None                 # Interest ID for word problem personalization
    seed: Optional[int] = None

class LabV2SubmitRequest(PydanticBaseModel):
    """Request body for /api/matatag/lab/v2/submit"""
    problem_id: str
    student_answer: str

class LabV2ConfigSaveRequest(PydanticBaseModel):
    allowed_difficulties: Optional[Dict[str, List[Any]]] = None
    allowed_contexts: Optional[Dict[str, List[str]]] = None
    allowed_formatters: Optional[List[str]] = None

@app.get("/api/matatag/node/{node_id}/capabilities")
def get_node_capabilities(node_id: str):
    """Introspect DNA to return available axes, variants, and formatters."""
    from backend.app.practice_gen.registry import NODE_TO_DNA
    from backend.app.practice_gen.generators.base_generator import _import_dna_module
    
    dnas = NODE_TO_DNA.get(node_id)
    if not dnas:
        raise HTTPException(status_code=404, detail="Node not found in registry")
        
    primary_dna_name = dnas[0]
    try:
        dna_module = _import_dna_module(primary_dna_name)
        dna_instance = getattr(dna_module, f"{primary_dna_name.upper()}_DNA", None)
    except Exception:
        dna_instance = None
    
    if not dna_instance:
        return {"difficulty_axes": {}, "compatible_formatters": []}
        
    return {
        "difficulty_axes": getattr(dna_instance, "difficulty_axes", {}),
        "compatible_formatters": getattr(dna_instance, "compatible_formatters", [])
    }

@app.post("/api/matatag/node/{node_id}/config")
def save_node_config(node_id: str, req: LabV2ConfigSaveRequest, db: Session = Depends(get_db)):
    """Save the enabled checkboxes for a node."""
    from backend.app.models import CompetencyConfiguration
    config = db.query(CompetencyConfiguration).filter_by(node_id=node_id).first()
    if not config:
        config = CompetencyConfiguration(node_id=node_id)
        db.add(config)
    
    if req.allowed_difficulties is not None:
        config.allowed_difficulties = req.allowed_difficulties
    if req.allowed_contexts is not None:
        config.allowed_contexts = req.allowed_contexts
    if req.allowed_formatters is not None:
        config.allowed_formatters = req.allowed_formatters
        
    db.commit()
    return {"status": "success"}

@app.get("/api/matatag/node/{node_id}/config")
def get_node_config(node_id: str, db: Session = Depends(get_db)):
    """Read the enabled checkboxes for a node."""
    from backend.app.models import CompetencyConfiguration
    config = db.query(CompetencyConfiguration).filter_by(node_id=node_id).first()
    if not config:
        return {"allowed_difficulties": {}, "allowed_contexts": [], "allowed_formatters": []}
    return {
        "allowed_difficulties": config.allowed_difficulties or {},
        "allowed_contexts": config.allowed_contexts or [],
        "allowed_formatters": config.allowed_formatters or []
    }

@app.post("/api/matatag/lab/v2/generate")
def matatag_lab_v2_generate(req: LabV2GenerateRequest, db: Session = Depends(get_db)):
    """
    Generate a practice problem using the new practice_gen pipeline.
    """
    with open("/tmp/last_request.json", "w") as f:
        f.write(req.json())

    from backend.app.practice_gen.pipeline import run
    from backend.app.practice_gen.registry import get_node_info

    # Get node info for grade
    info = get_node_info(req.node_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Node '{req.node_id}' not found.")
    grade = info.get("grade", 1)

    # Merge difficulty_profile and variant_values into combined profile
    # The DNA's generate_params will read both difficulty axes and variants from this dict
    combined_profile = {}
    if req.difficulty_profile:
        combined_profile.update(req.difficulty_profile)
    if req.variant_values:
        combined_profile.update(req.variant_values)

    # Generate seed if not provided
    seed = req.seed
    if seed is None:
        import random as _rand
        seed = _rand.randint(10000, 999999)
    from backend.app.models import CompetencyConfiguration
    config = db.query(CompetencyConfiguration).filter_by(node_id=req.node_id).first()
    allowed_formatters = config.allowed_formatters if config else None

    try:
        problem_dict = run(
            node_id=req.node_id,
            student_grade=grade,
            formatter=req.formatter,
            difficulty_profile=combined_profile if combined_profile else None,
            seed=seed,
            student_interest=req.interest_theme,
            allowed_formatters=allowed_formatters,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    # Cache for answer submission
    problem_id = problem_dict.get("problem_id")
    if problem_id:
        PRACTICE_GEN_CACHE[problem_id] = problem_dict

    return problem_dict


@app.post("/api/matatag/lab/v2/submit")
def matatag_lab_v2_submit(req: LabV2SubmitRequest):
    """
    Grade an answer from the v2 pipeline.

    Handles all formatter types:
    - mcq: Compare selected key (A/B/C/D) to correct_key
    - numeric_input: Compare numeric value to correct_answer
    - cloze: Compare filled text to correct_answer
    - Visual formats: Compare based on visual_type

    Returns:
    {
        "is_correct": bool,
        "correct_answer": str,
        "trap_triggered": str | null,
        "explanation": str
    }
    """
    problem = PRACTICE_GEN_CACHE.get(req.problem_id)
    if not problem:
        raise HTTPException(
            status_code=404,
            detail="Problem session expired. Please generate a new problem."
        )

    fmt = problem.get("format", "mcq")
    correct_answer = problem.get("correct_answer")
    format_data = problem.get("format_data", {})
    answer_collection = problem.get("answer_collection", "")
    is_correct = False
    trap_triggered = None

    # Normalize student answer
    student_answer = req.student_answer.strip()

    if fmt == "mcq" or answer_collection == "mcq":
        # MCQ: compare selected key OR value to correct answer
        # Also handles visual formats with MCQ answer collection (e.g., read_mcq)
        mcq_options = format_data.get("options") or format_data.get("mcq_options") or []
        correct_key = format_data.get("correct_key", "")
        
        # If no correct_key in format_data, derive from correct_answer
        if not correct_key and isinstance(correct_answer, str) and len(correct_answer) == 1:
            correct_key = correct_answer
        
        # Accept either:
        # 1. The key (A/B/C/D)
        # 2. The value itself
        if correct_key and student_answer.upper() == correct_key.upper():
            is_correct = True
        elif str(student_answer) == str(correct_answer):
            is_correct = True
        else:
            # Check if student submitted the value directly
            for opt in mcq_options:
                if opt.get("is_correct"):
                    correct_value = opt.get("value")
                    if str(student_answer) == str(correct_value):
                        is_correct = True
                    break

        # Check if student triggered a trap (distractor)
        if not is_correct:
            for opt in mcq_options:
                opt_key = opt.get("key", "").upper()
                opt_val = str(opt.get("value", ""))
                if opt_key == student_answer.upper() or opt_val == str(student_answer):
                    trap_triggered = opt.get("trap")
                    break

    elif fmt == "numeric_input":
        # Numeric: compare numeric values
        try:
            student_val = float(student_answer.replace(",", "").replace("₱", ""))
            correct_val = float(str(correct_answer).replace(",", "").replace("₱", ""))
            is_correct = abs(student_val - correct_val) < 0.001
        except (ValueError, TypeError):
            is_correct = str(student_answer) == str(correct_answer)

    elif fmt == "cloze" or fmt == "fill_in_blank":
        # Cloze: compare text (case-insensitive)
        is_correct = student_answer.lower() == str(correct_answer).lower()

    elif fmt == "ordering":
        # Ordering: compare sequence
        import ast
        try:
            if isinstance(student_answer, str):
                student_seq = json.loads(student_answer)
            else:
                student_seq = student_answer
            correct_seq = correct_answer
            if isinstance(correct_seq, str):
                correct_seq = json.loads(correct_seq)
            is_correct = student_seq == correct_seq
        except (json.JSONDecodeError, ValueError):
            is_correct = str(student_answer) == str(correct_answer)

    elif fmt == "true_false":
        # True/False: compare boolean-like values
        student_bool = student_answer.lower() in ("true", "yes", "t", "1")
        correct_bool = str(correct_answer).lower() in ("true", "yes", "t", "1")
        is_correct = student_bool == correct_bool

    elif fmt == "error_detect":
        # Error detect: two-step answer
        # correct_answer is {"has_error": bool, "correct_value": int}
        # student_answer is JSON: {"has_error": bool, "correct_value": str/int}
        try:
            student_parsed = json.loads(student_answer) if isinstance(student_answer, str) else student_answer
        except (json.JSONDecodeError, ValueError):
            student_parsed = {"has_error": True, "correct_value": student_answer}

        expected_has_error = correct_answer.get("has_error", True) if isinstance(correct_answer, dict) else True
        expected_value = correct_answer.get("correct_value") if isinstance(correct_answer, dict) else correct_answer

        student_has_error = student_parsed.get("has_error", True) if isinstance(student_parsed, dict) else True
        student_value = student_parsed.get("correct_value", student_answer) if isinstance(student_parsed, dict) else student_answer

        if expected_has_error:
            # There IS an error: student must say has_error=True AND give correct value
            if student_has_error:
                try:
                    is_correct = abs(float(str(student_value)) - float(str(expected_value))) < 0.001
                except (ValueError, TypeError):
                    is_correct = str(student_value) == str(expected_value)
            else:
                is_correct = False  # Student said no error, but there is one
        else:
            # There is NO error: student must say has_error=False
            is_correct = not student_has_error

    else:
        # Visual formats or unknown - try direct comparison
        # For visual formats, the answer might be in various formats
        is_visual = problem.get("is_visual", False)
        if is_visual:
            visual_type = problem.get("visual_type", "")
            try:
                parsed = json.loads(student_answer)
            except (json.JSONDecodeError, ValueError):
                parsed = student_answer

            # Handle specific visual types
            if visual_type == "NumberLine":
                try:
                    student_val = int(str(parsed))
                    correct_val = int(str(correct_answer))
                    is_correct = student_val == correct_val
                except (ValueError, TypeError):
                    is_correct = str(parsed) == str(correct_answer)
            else:
                # Generic comparison
                is_correct = str(parsed) == str(correct_answer)
        else:
            # Fallback: string comparison
            is_correct = str(student_answer) == str(correct_answer)

    # Build explanation
    correct_display = str(correct_answer)
    if fmt == "mcq" or answer_collection == "mcq":
        # Show the text of the correct option
        all_options = format_data.get("options") or format_data.get("mcq_options") or []
        c_key = format_data.get("correct_key", "")
        if not c_key and isinstance(correct_answer, str) and len(correct_answer) == 1:
            c_key = correct_answer
        for opt in all_options:
            if opt.get("key") == c_key or opt.get("is_correct"):
                correct_display = f"{opt.get('key', c_key)}: {opt.get('value', opt.get('text', correct_answer))}"
                break
    elif fmt == "error_detect":
        has_error = format_data.get("has_error", True)
        correct_value = format_data.get("correct_value")
        actor = format_data.get("actor_name", "the student")
        actors_answer = format_data.get("actors_answer")
        if has_error:
            correct_display = f"No, {actor} is wrong. The correct answer is {correct_value}."
        else:
            correct_display = f"Yes, {actor} is correct! The answer is {correct_value}."

    explanation = (
        f"Correct! {correct_display}"
        if is_correct
        else f"Not quite. {correct_display}"
    ) if fmt == "error_detect" else (
        f"Correct! The answer is {correct_display}."
        if is_correct
        else f"Not quite. The correct answer is {correct_display}."
    )

    return {
        "is_correct": is_correct,
        "correct_answer": correct_display,
        "trap_triggered": trap_triggered,
        "explanation": explanation,
    }


@app.get("/api/matatag/progress/{student_id}")
def get_matatag_progress(student_id: int, db: Session = Depends(get_db)):
    """
    Get a student's MATATAG progress organized by content area with grade/quarter position.
    
    Returns:
    {
        "student_grade": 1,
        "content_areas": [
            {
                "key": "NA",
                "title": "Number and Algebra",
                "color": "#8b5cf6",
                "emoji": "🔢",
                "current_grade": 1,
                "current_quarter": 1,
                "quarter_competencies": 10,
                "quarter_mastered": 3,
                "quarter_active": 1,
                "total_competencies": 45,
                "total_mastered": 3
            },
            ...
        ]
    }
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student_grade = student.grade if student.grade > 0 else 1
    
    # Content area mapping
    content_areas = {
        "na": {"key": "NA", "title": "Number and Algebra", "color": "#8b5cf6", "emoji": "🔢"},
        "mg": {"key": "MG", "title": "Measurement and Geometry", "color": "#f59e0b", "emoji": "📐"},
        "dp": {"key": "DP", "title": "Data and Probability", "color": "#10b981", "emoji": "📊"},
    }
    
    result = {
        "student_grade": student_grade,
        "content_areas": []
    }
    
    for area_code, area_info in content_areas.items():
        # Find all nodes for this content area
        # Node ID pattern: mat_g{grade}_{area}_{quarter}_{num}
        nodes = db.query(models.SkillNode).filter(
            models.SkillNode.id.like(f"mat_g%_{area_code}_%")
        ).all()
        
        if not nodes:
            # No nodes in DB yet - use defaults
            result["content_areas"].append({
                **area_info,
                "current_grade": student_grade,
                "current_quarter": 1,
                "quarter_competencies": 0,
                "quarter_mastered": 0,
                "quarter_active": 0,
                "total_competencies": 0,
                "total_mastered": 0
            })
            continue
        
        # Parse node IDs to organize by grade and quarter
        # e.g., mat_g1_na_q2_3 -> grade=1, quarter=2, num=3
        import re
        node_info = []
        for n in nodes:
            match = re.match(r"mat_g(\d+)_([a-z]+)_q(\d+)_(\d+)", n.id)
            if match:
                node_info.append({
                    "id": n.id,
                    "grade": int(match.group(1)),
                    "area": match.group(2),
                    "quarter": int(match.group(3)),
                    "num": int(match.group(4)),
                    "title": n.title
                })
        
        # Get mastery states for this student
        node_ids = [n["id"] for n in node_info]
        mastery_states = db.query(models.MasteryState).filter(
            models.MasteryState.student_id == student_id,
            models.MasteryState.skill_id.in_(node_ids)
        ).all()
        mastery_map = {m.skill_id: m.status for m in mastery_states}
        
        # Determine current position (first non-mastered node at or below student's grade)
        # Sort by grade, then quarter, then num
        node_info.sort(key=lambda x: (x["grade"], x["quarter"], x["num"]))
        
        # Filter to nodes at or below student's grade level
        eligible_nodes = [n for n in node_info if n["grade"] <= student_grade]
        
        # Find current position - first node that's not mastered
        current_grade = student_grade
        current_quarter = 1
        for n in eligible_nodes:
            status = mastery_map.get(n["id"], "not_started")
            if status != "mastered":
                current_grade = n["grade"]
                current_quarter = n["quarter"]
                break
        else:
            # All mastered - move to next available
            if eligible_nodes:
                last = eligible_nodes[-1]
                current_grade = last["grade"]
                current_quarter = min(last["quarter"] + 1, 4)
                if current_quarter > 4:
                    current_grade = min(last["grade"] + 1, 10)
                    current_quarter = 1
        
        # Count competencies in current quarter
        quarter_nodes = [n for n in node_info if n["grade"] == current_grade and n["quarter"] == current_quarter]
        quarter_mastered = sum(1 for n in quarter_nodes if mastery_map.get(n["id"]) == "mastered")
        quarter_active = sum(1 for n in quarter_nodes if mastery_map.get(n["id"]) == "active")
        
        # Total counts
        total_mastered = sum(1 for n in node_info if mastery_map.get(n["id"]) == "mastered")
        
        result["content_areas"].append({
            **area_info,
            "current_grade": current_grade,
            "current_quarter": current_quarter,
            "quarter_competencies": len(quarter_nodes),
            "quarter_mastered": quarter_mastered,
            "quarter_active": quarter_active,
            "total_competencies": len(node_info),
            "total_mastered": total_mastered
        })
    
    return result





# ===========================================================================
# INTRO CONTENT ENDPOINTS
# ===========================================================================

from backend.app.intro_gen import generate_intro_content, get_available_intro_nodes, get_interest_themes


@app.get("/api/matatag/intro/nodes")
def list_intro_nodes():
    """List all nodes that have intro content available."""
    return {"nodes": get_available_intro_nodes()}


@app.get("/api/matatag/intro/interests")
def list_intro_interests(grade: int = 1):
    """List interest themes available for a grade level."""
    return {"interests": get_interest_themes(grade)}


@app.get("/api/matatag/intro/{node_key}")
def get_intro_content(node_key: str, interest: str = None, seed: int = None, student_id: int = None, db: Session = Depends(get_db)):
    """
    Generate intro content for a MATATAG node.
    
    - node_key: e.g., "g1_na_q1"
    - interest: optional interest theme key (e.g., "basketball", "pets")
    - seed: optional seed for reproducibility
    - student_id: optional student ID to load interest preference dynamically
    """
    if student_id and not interest:
        student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
        if student:
            interests_str = _combined_interests(student).lower()
            available_interests = get_interest_themes(student.grade or 1)
            for item in available_interests:
                key = item["key"].lower()
                if key in interests_str:
                    interest = item["key"]
                    break
                    
    result = generate_intro_content(node_key, interest_key=interest, seed=seed)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/api/matatag/intro/{node_key}/viewed")
def mark_intro_viewed(node_key: str, student_id: int, db: Session = Depends(get_db)):
    """Mark the intro for a node as viewed by a student."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    stmt = pg_insert(models.NodeIntroView).values(
        student_id=student_id,
        node_key=node_key,
    ).on_conflict_do_nothing(constraint="uq_student_node_intro")
    db.execute(stmt)
    db.commit()
    record = db.query(models.NodeIntroView).filter_by(
        student_id=student_id, node_key=node_key
    ).first()
    return {"status": "ok", "viewed_at": record.viewed_at.isoformat() if record else None}


@app.get("/api/matatag/intro/{node_key}/status")
def get_intro_status(node_key: str, student_id: int, db: Session = Depends(get_db)):
    """Check whether a student has viewed the intro for a node."""
    record = db.query(models.NodeIntroView).filter_by(
        student_id=student_id, node_key=node_key
    ).first()
    if record:
        return {"viewed": True, "viewed_at": record.viewed_at.isoformat()}
    return {"viewed": False, "viewed_at": None}

# Removed lazy_startup_middleware to prevent first-request timeout.
# Database tables and migrations have already been applied previously.
# Fri Jun 19 06:17:36 PST 2026
