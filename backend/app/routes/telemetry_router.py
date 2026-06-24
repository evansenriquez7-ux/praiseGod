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
router = APIRouter(tags=['telemetry'])

@router.post("/api/telemetry/start", response_model=schemas.TelemetrySessionStartResponse)
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


@router.post("/api/telemetry/update", response_model=schemas.TelemetrySessionResponse)
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


