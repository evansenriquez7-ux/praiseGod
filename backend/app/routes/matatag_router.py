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
router = APIRouter(tags=['matatag'])

@router.get("/api/matatag/competencies")
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



@router.get("/api/matatag/nodes")
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



@router.get("/api/matatag/difficulty-axes/{node_id}")
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



@router.get("/api/matatag/lab/config/{node_id}")
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



@router.get("/api/matatag/lab/interests")
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



@router.get("/api/matatag/lab/generate")
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
    competency = info.get("competency", "")

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



@router.post("/api/matatag/lab/submit")
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
    formatter: Optional[str] = "mcq"
    difficulty_profile: Optional[Dict[str, Any]] = None  # {axis: level_or_value}
    variant_values: Optional[Dict[str, Any]] = None      # {variant: value}
    interest_theme: Optional[str] = None                 # Interest ID for word problem personalization
    seed: Optional[int] = None

class LabV2SubmitRequest(PydanticBaseModel):
    """Request body for /api/matatag/lab/v2/submit"""
    problem_id: str
    student_answer: Any

class LabV2ConfigSaveRequest(PydanticBaseModel):
    allowed_difficulties: Optional[Dict[str, List[Any]]] = None
    allowed_contexts: Optional[Dict[str, List[Any]]] = None
    allowed_formatters: Optional[List[str]] = None


@router.get("/api/matatag/node/{node_id}/capabilities")
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


@router.post("/api/matatag/node/{node_id}/config")
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


@router.get("/api/matatag/node/{node_id}/config")
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


@router.post("/api/matatag/lab/v2/generate")
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



@router.post("/api/matatag/lab/v2/submit")
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



@router.get("/api/matatag/progress/{student_id}")
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



@router.get("/api/matatag/intro/nodes")
def list_intro_nodes():
    """List all nodes that have intro content available."""
    return {"nodes": get_available_intro_nodes()}



@router.get("/api/matatag/intro/interests")
def list_intro_interests(grade: int = 1):
    """List interest themes available for a grade level."""
    return {"interests": get_interest_themes(grade)}



@router.get("/api/matatag/intro/{node_key}")
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



@router.post("/api/matatag/intro/{node_key}/viewed")
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



@router.get("/api/matatag/intro/{node_key}/status")
def get_intro_status(node_key: str, student_id: int, db: Session = Depends(get_db)):
    """Check whether a student has viewed the intro for a node."""
    record = db.query(models.NodeIntroView).filter_by(
        student_id=student_id, node_key=node_key
    ).first()
    if record:
        return {"viewed": True, "viewed_at": record.viewed_at.isoformat()}
    return {"viewed": False, "viewed_at": None}



