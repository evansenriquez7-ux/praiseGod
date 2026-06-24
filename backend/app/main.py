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
app.include_router(parent.router)

from backend.app.routes import matatag_router, practice_router, telemetry_router, socratic_router, admin_router, student
app.include_router(matatag_router.router)
app.include_router(practice_router.router)
app.include_router(telemetry_router.router)
app.include_router(socratic_router.router)
app.include_router(admin_router.router)
app.include_router(student.router)


# --- PARENT ENDPOINTS ---








# --- TELEMETRY ENDPOINTS ---



# --- PRACTICE ENGINE ENDPOINTS ---






# --- SOCRATIC SPLIT ENDPOINTS ---



















