import datetime
import os
import math
import json
import re
import random as _random
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
import concurrent.futures
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr



from backend.app.database import get_db, engine, Base
from backend.app import models, schemas, subagents
from backend.app.services import placement
from backend.app.practice_gen import pipeline

from backend.app.practice_gen import registry as _pg_registry

from backend.app.services.scoring import validate_math_answer
from backend.app.practice_gen.axes_catalog import (
    get_axes_for_concept as _get_axes_for_concept,
    compute_difficulty_scalar as _compute_difficulty_scalar,
)

# Initialize FastAPI app


# Enable CORS for tablet local LAN sync and external tunnels

from backend.app.services.cache import get_cache, set_cache, delete_cache

class RedisDict:
    def __init__(self, prefix: str):
        self.prefix = prefix
    
    def _k(self, key): return f"{self.prefix}:{key}"
    
    def __getitem__(self, key):
        val = get_cache(self._k(key))
        if val is None: raise KeyError(key)
        return val
        
    def __setitem__(self, key, value):
        set_cache(self._k(key), value)
        
    def __contains__(self, key):
        return get_cache(self._k(key)) is not None
        
    def get(self, key, default=None):
        val = get_cache(self._k(key))
        return val if val is not None else default
        
    def setdefault(self, key, default=None):
        val = get_cache(self._k(key))
        if val is None:
            set_cache(self._k(key), default)
            return default
        return val
        
    def extend(self, key, values):
        val = self.get(key, [])
        val.extend(values)
        set_cache(self._k(key), val)

# Global cache for LLM-generated ELA skeletons
ELA_SKELETON_CACHE = RedisDict("ela")

# Global cache for pre-generated questions to eliminate latency
QUESTION_CACHE = RedisDict("question")

# Global cache for MATATAG skeleton problems
MATATAG_SKELETON_CACHE = RedisDict("matatag")

# Global cache for practice_gen v2 pipeline problems
PRACTICE_GEN_CACHE = RedisDict("practice_gen_v2")

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

from backend.app.services.telemetry import load_previous_questions as _load_previous_questions, save_practice_question as _save_practice_question, clear_student_history as _clear_student_history

def replenish_question_cache(student_id: int, subject: str, subdomain: Optional[str], count: int):
    """
    Background task to pre-generate questions into the cache.
    Uses parallel execution for high-speed generation.
    """
    cache_key = f"{student_id}_{subject}_{subdomain}"
    
    def generate_one():
        from backend.app.database import SessionLocal
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
        
        QUESTION_CACHE.extend(cache_key, new_questions)
        print(f"Replenished cache for {cache_key} with {len(new_questions)} items")

from backend.app.services.curriculum import get_clean_node_title

from backend.app.services.curriculum import check_and_advance_subject_frontier

# --- Elo Rating Helper ---
from backend.app.services.scoring import update_elo

# --- ROUTERS ---
from backend.app.routes import parent


# --- PARENT ENDPOINTS ---

from fastapi import APIRouter
router = APIRouter(tags=['socratic'])

@router.post("/api/socratic/chat", response_model=schemas.SocraticChatResponse)
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




