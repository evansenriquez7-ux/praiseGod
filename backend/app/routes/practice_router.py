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
router = APIRouter(tags=['practice'])

@router.get("/api/practice/question", response_model=schemas.QuestionResponse)
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
        try:
            if subject == "Verbal":
                placement_history = db.query(models.Attempt).join(models.SkillNode).filter(
                    models.Attempt.student_id == student_id,
                    models.Attempt.telemetry_flagged == False,
                    models.SkillNode.subject.in_([
                        "Reading: Literature",
                        "Reading: Informational Text",
                        "Reading Foundations",
                        "Speaking & Listening",
                        "Writing",
                        "Language"
                    ])
                ).all()
            else:
                placement_history = db.query(models.Attempt).join(models.SkillNode).filter(
                    models.Attempt.student_id == student_id,
                    models.Attempt.telemetry_flagged == False,
                    models.SkillNode.subject.like(f"%{subject}%")
                ).all()
        except Exception as db_err:
            print(f"[DB Warning] Placement history query failed: {db_err}. Proceeding without placement history.")
            placement_history = []
        
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
                    try:
                        student_g = int(student.grade)
                    except Exception:
                        student_g = 1
                    skill_id = f"mat_g{student_g}_na_q1_0" if student_g > 0 else "mat_g1_na_q1_0"

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
                    skill_id = f"mat_g{student_g}_na_q1_0" if student_g > 0 else "mat_g1_na_q1_0"
                
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
        _allowed_diff = None
        _allowed_ctx = None
        if is_matatag:
            try:
                _cfg = db.query(models.CompetencyConfiguration).filter_by(node_id=skill_id).first()
                if _cfg:
                    _allowed_fmt = _cfg.allowed_formatters
                    _allowed_diff = _cfg.allowed_difficulties
                    _allowed_ctx = _cfg.allowed_contexts
            except Exception as db_err:
                print(f"[DB Warning] Unable to fetch CompetencyConfiguration: {db_err}. Using defaults.")
                _cfg = None
        
        interest_theme = _combined_interests(student, "math")
        
        # Parse grade level from node ID or default to student's nominal grade
        # This prevents the generator from downgrading a 3rd grade node if a 1st grader is playing it!
        import re
        grade_match = re.search(r"mat_g(\d+)", skill_id)
        effective_grade = int(grade_match.group(1)) if grade_match else (student.grade if student else 1)
        
        try:
            problem_dict = _pg_run(
                node_id=skill_id,
                student_interest=interest_theme,
                allowed_formatters=_allowed_fmt,
                allowed_difficulties=_allowed_diff,
                allowed_contexts=_allowed_ctx,
                experience="standard"
            )
            # Normalise to legacy keys for router compatibility
            skeleton = problem_dict
            skeleton["skeleton_id"] = problem_dict.get("problem_id")
            skeleton["stem_template"] = problem_dict.get("question_text")
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
    fmt_data = skeleton.get("format_data") or {}
    raw_opts = fmt_data.get("mcq_options") or fmt_data.get("options") or skeleton.get("options") or []
    
    if isinstance(raw_opts, list):
        for o in raw_opts:
            options_list.append(schemas.QuestionOption(
                key=o.get("key", "A"),
                text=str(o.get("value", o.get("text", ""))) if o.get("value") is not None else str(o.get("text", ""))
            ))
    elif isinstance(raw_opts, dict):
        for k, v in raw_opts.items():
            opt_text = str(v.get("text", v.get("value", ""))) if isinstance(v, dict) else str(v)
            options_list.append(schemas.QuestionOption(key=k, text=opt_text))

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
        answer_collection=skeleton.get("answer_collection", "mcq"),
        interaction_mode=skeleton.get("interaction_mode", "read")
    )


@router.get("/api/practice/{student_id}/batch", response_model=List[schemas.QuestionResponse])
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
    # Step 1: generate Q1 via the full pipeline (handles both ELA and Math correctly).
    # Q1 is always generated first so we can derive routing from the actual skill node
    # selected — not the subject string from the frontend, which may be a raw DB subject
    # name ("Language", "Writing", "Reading: Literature", etc.) rather than the
    # normalised "Verbal" sentinel value.
    try:
        q1 = get_practice_question(student_id, subject, subdomain, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate question: {e}")

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
    _allowed_diff = None
    _allowed_ctx = None
    if is_matatag:
        _cfg = db.query(models.CompetencyConfiguration).filter_by(node_id=q1.skill_id).first()
        if _cfg:
            _allowed_fmt = _cfg.allowed_formatters
            _allowed_diff = _cfg.allowed_difficulties
            _allowed_ctx = _cfg.allowed_contexts
    
    try:
        # We already have q1, so we generate count-1 more problems
        additional_count = max(0, count - 1)
        batch = [q1]
        
        if additional_count > 0:
            new_problems = _pg_batch(
                node_id=q1.skill_id,
                count=additional_count,
                student_interest=interest_theme,
                experience="standard",
                allowed_formatters=_allowed_fmt,
                allowed_difficulties=_allowed_diff,
                allowed_contexts=_allowed_ctx,
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
                    answer_collection=p.get("answer_collection", "mcq"),
                    interaction_mode=p.get("interaction_mode", "read")
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


@router.post("/api/practice/placement/skip")
def skip_placement(req: schemas.PlacementSkipRequest, db: Session = Depends(get_db)):
    """
    Bypasses placement for a subject and seeds based on student grade.
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    placement.PlacementEngine.skip_placement(student, req.subject, db)
    return {"success": True}


@router.post("/api/practice/submit", response_model=schemas.AnswerSubmitResponse)
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
            match = re.search(r"_(\d+)(?:_[a-z_]+)?$", req.skeleton_id)
            seed_val = int(match.group(1)) if match else None
            node_id = req.skeleton_id.rsplit('_', 1)[0] if match else req.skill_id
            
            # If the node_id ends with _pictograph (etc) due to rsplit taking only the suffix, we need to extract the actual node_id
            if node_id.endswith("_pictograph") or not node_id.startswith("mat_"):
                # robust extraction
                node_match = re.match(r"(mat_g\d+_.*?_q\d+_\d+)", req.skeleton_id)
                if node_match:
                    node_id = node_match.group(1)
            
            from backend.app.practice_gen.pipeline import run as _pg_run
            try:
                skeleton = _pg_run(node_id=node_id, seed=seed_val)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"MATATAG question session expired or invalid: {e}")
    elif req.skeleton_id.startswith("ai_"):
        # AI-generated Math fallback is deprecated
        raise HTTPException(status_code=400, detail="Math AI question session expired or invalid.")
    else:
        # Reconstruct from seed via unified v2 pipeline
        seed_val = None
        # Extract seed from format "{node_id}_{seed}" or "{node_id}_{seed}_{format}"
        match = re.search(r"_(\d+)(?:_[a-z_]+)?$", req.skeleton_id)
        if match:
            seed_val = int(match.group(1))

        # Extract grade from skill_id to prevent generator downgrading
        import re
        grade_match = re.search(r"mat_g(\d+)", req.skill_id)
        effective_grade = int(grade_match.group(1)) if grade_match else (student.grade if student else 1)

        from backend.app.practice_gen.pipeline import run as _pg_run
        skeleton = _pg_run(
            node_id=req.skill_id,
            seed=seed_val,
            student_interest=_combined_interests(student, "math")
        )

    # Normalize skeleton dictionary to support both legacy and native v2 formats
    if skeleton:
        # 1. Format and mode
        fmt = skeleton.get("format", "mcq")
        if "question_mode" not in skeleton:
            skeleton["question_mode"] = fmt
            
        # 2. Correct Key
        if "correct_key" not in skeleton:
            correct_key = skeleton.get("format_data", {}).get("correct_key")
            if not correct_key:
                # Find from mcq_options list
                mcq_opts = skeleton.get("format_data", {}).get("mcq_options") or []
                for opt in mcq_opts:
                    if opt.get("is_correct"):
                        correct_key = opt.get("key")
                        break
            skeleton["correct_key"] = correct_key or "A"
            
        # 3. Options Dictionary
        if "options" not in skeleton or not isinstance(skeleton.get("options"), dict):
            # Build options dictionary
            options_dict = {}
            raw_opts = skeleton.get("format_data", {}).get("mcq_options") or skeleton.get("format_data", {}).get("options") or skeleton.get("options") or []
            if isinstance(raw_opts, list):
                for o in raw_opts:
                    key = o.get("key", "A")
                    options_dict[key] = {
                        "text": o.get("text", ""),
                        "value": o.get("value", o.get("text", "")),
                        "trap_name": o.get("trap")
                    }
            elif isinstance(raw_opts, dict):
                for k, v in raw_opts.items():
                    options_dict[k] = {
                        "text": v.get("text", str(v)) if isinstance(v, dict) else str(v),
                        "value": v.get("value", v.get("text", str(v))) if isinstance(v, dict) else v,
                        "trap_name": v.get("trap_name") if isinstance(v, dict) else None
                    }
            skeleton["options"] = options_dict

    # Grading
    if is_ela or req.skeleton_id.startswith("ai_"):
        # Key comparison for ELA and AI-generated Math
        is_correct = (str(req.selected_answer).upper() == skeleton.get("correct_key", "A").upper())
    elif is_matatag:
        # MATATAG — check format type
        fmt = skeleton.get("format", "mcq")
        if fmt == "mcq":
            is_correct = (str(req.selected_answer).upper() == skeleton.get("correct_key", "A").upper())
        elif fmt in ["cloze", "numeric_input", "ordering", "true_false", "error_detect", "fill_in_blank"]:
            student_answer = req.selected_answer
            correct_answer = skeleton.get("correct_answer")
            
            if fmt == "numeric_input":
                try:
                    student_val = float(str(student_answer).strip().replace(",", "").replace("₱", ""))
                    correct_val = float(str(correct_answer).replace(",", "").replace("₱", ""))
                    is_correct = abs(student_val - correct_val) < 0.001
                except (ValueError, TypeError):
                    is_correct = str(student_answer).strip() == str(correct_answer)
            elif fmt in ["cloze", "fill_in_blank"]:
                is_correct = str(student_answer).strip().lower() == str(correct_answer).lower()
            elif fmt == "ordering":
                try:
                    student_seq = json.loads(student_answer) if isinstance(student_answer, str) else student_answer
                    correct_seq = correct_answer
                    if isinstance(correct_seq, str):
                        correct_seq = json.loads(correct_seq)
                    is_correct = [str(x) for x in student_seq] == [str(x) for x in correct_seq]
                except:
                    is_correct = str(student_answer).strip() == str(correct_answer)
            elif fmt == "true_false":
                student_bool = str(student_answer).strip().lower() in ("true", "yes", "t", "1")
                correct_bool = str(correct_answer).lower() in ("true", "yes", "t", "1")
                is_correct = student_bool == correct_bool
            elif fmt == "error_detect":
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
                    try:
                        student_answer = json.loads(req.selected_answer) if isinstance(req.selected_answer, str) else req.selected_answer
                    except:
                        student_answer = req.selected_answer
                    correct_answer = visual_params.get("correct_answer")
                    is_correct = student_answer == correct_answer
                elif question_mode == "currency_picker":
                    try:
                        student_answer = json.loads(req.selected_answer) if isinstance(req.selected_answer, str) else req.selected_answer
                        target_amount = visual_params.get("target_amount", 0)
                        student_total = student_answer.get("total", 0)
                        is_correct = student_total == target_amount
                    except:
                        is_correct = False
                elif question_mode == "clock_set":
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
                    is_correct = (str(req.selected_answer).upper() == skeleton.get("correct_key", "A").upper())
            else:
                is_correct = (str(req.selected_answer).upper() == skeleton.get("correct_key", "A").upper())
    else:
        # SymPy Math — VALUE comparison (robust against narration shuffles and worked examples)
        selected_key = str(req.selected_answer).upper()
        if selected_key in skeleton["options"]:
            selected_opt = skeleton["options"][selected_key]
            is_correct = validate_math_answer(skeleton["correct_answer"], selected_opt["value"])
        else:
            # Worked example: student typed a raw value (e.g. "5/6")
            is_correct = validate_math_answer(skeleton["correct_answer"], req.selected_answer)
            
    # Identify Trap engineered misconception
    trap_selected = None
    if isinstance(skeleton.get("options"), dict):
        opt_data = skeleton["options"].get(str(req.selected_answer).upper())
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


@router.post("/api/practice/flag")
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


