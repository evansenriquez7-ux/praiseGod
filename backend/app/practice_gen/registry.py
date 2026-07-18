"""
Practice Generation — Node Registry
======================================

Maps MATATAG node IDs to DNA concept names and provides lookups
used by the pipeline to select generators and formatters.

Responsibilities:
  1. Load knowledge_graph_g1_3.json at import time.
  2. Load data/ph/matatagmath.json at import time.
  3. Define NODE_TO_DNA: static mapping node_id → List[str] (DNA names).
  4. Expose get_node_dnas(), get_node_formatters(), get_node_info(),
     find_node_id(), get_all_node_ids().

Node ID format: mat_g{grade}_{branch}_q{quarter}_{index}
  branch: na (Number & Algebra), mg (Measurement & Geometry),
          dp (Data & Probability)

DNA concept names exactly match the "concept" field of each DNA instance.

Refactored from:
  - matatag_skeletons.py  COMPETENCY_ROUTES (lines 175–274)
  - curriculum_context.py find_competency_in_curriculum
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from .compatibility import COMPATIBILITY


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING — once at import time
# ═══════════════════════════════════════════════════════════════════════════════

# practice_gen/ → app/ → backend/ → ccmed/ (project root)
_ROOT: Path = Path(__file__).parent.parent.parent.parent

_KG_PATH: Path = _ROOT / "data" / "knowledge_graph_g1_3.json"
_MATATAG_PATH: Path = _ROOT / "data" / "ph" / "matatagmath.json"

_KG_NODES: Dict[str, Dict] = {}
_MATATAG_DATA: Dict = {}

try:
    with _KG_PATH.open(encoding="utf-8") as _f:
        _KG_NODES = json.load(_f).get("nodes", {})
except (FileNotFoundError, json.JSONDecodeError):
    _KG_NODES = {}

try:
    with _MATATAG_PATH.open(encoding="utf-8") as _f:
        _MATATAG_DATA = json.load(_f).get("Mathematics", {})
except (FileNotFoundError, json.JSONDecodeError):
    _MATATAG_DATA = {}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPETENCY BOUNDS PARSING
# Extract numeric bounds from competency text for difficulty dimensions.
# ═══════════════════════════════════════════════════════════════════════════════

import re
from typing import Tuple

# ── MATATAG grade-appropriate ceiling per DNA concept ────────────────────────
# When a competency text has no explicit numeric bound (e.g. "Illustrate
# addition of 2-digit and 1-digit numbers as counting up on the number
# line"), we fall back to the MATATAG curriculum's per-grade ceiling.
# These values are derived directly from the official K-3 MATATAG scope:
#   G1 addition/subtraction: sums/differences ≤ 20 (Q1-Q2), ≤ 100 (Q3-Q4)
#   G2 addition/subtraction: sums/differences ≤ 1000
#   G3 addition/subtraction: sums/differences ≤ 10000
#   G1-G3 comparing/ordering: same number ceiling as their grade range
_GRADE_DEFAULT_BOUNDS: Dict[str, Dict[int, Dict[str, int]]] = {
    "addition": {
        1: {"max_sum": 20},
        2: {"max_sum": 1000},
        3: {"max_sum": 10000},
    },
    "comparing_ordering": {
        1: {"max_value": 100},
        2: {"max_value": 1000},
        3: {"max_value": 10000},
    },
    "counting": {
        1: {"range_max": 100},
        2: {"range_max": 1000},
        3: {"range_max": 10000},
    },
    "number_reading": {
        1: {"range_max": 100},
        2: {"range_max": 10000},
        3: {"range_max": 10000},
    },
    "multiplication": {
        2: {"max_product": 100},
        3: {"max_product": 1000},
    },
    "money_peso": {
        1: {"max_total": 20},
        2: {"max_total": 1000},
        3: {"max_total": 10000},
    },
}


def _parse_competency_bounds(
    competency: str,
    dna_name: str,
    grade: int = 1,
) -> Dict[str, Tuple[int, int]]:
    """
    Parse competency text to extract bounds for difficulty dimensions.

    Returns dict mapping dimension names to (min, max) tuples.
    Scalar 0.0 maps to min, scalar 1.0 maps to max.

    Min values are curriculum-appropriate:
    - addition: min=0 (allows 0+0, 0+X, etc. as valid addition problems)
    - multiplication: min=1 (allows 1×1, 1×2, etc. as valid multiplication problems)
    - other: min=1

    When no explicit numeric bound is found in the LC text, a
    grade-appropriate MATATAG curriculum ceiling is applied as a
    fallback (see _GRADE_DEFAULT_BOUNDS). This guarantees that scalar
    1.0 ALWAYS maps to a sensible maximum — never to the raw float 1.0
    which would crash the DNA.

    Examples:
        "sums up to 20" → {"max_sum": (0, 20)}
        "sums up to 100 without regrouping" → {"max_sum": (0, 100)}
        "products up to 100" → {"max_product": (1, 100)}
    """
    bounds = {}
    # Strip spaces between digits (e.g. "10 000" -> "10000")
    text = re.sub(r'(\d)\s+(\d)', r'\1\2', competency.lower())

    # Addition: "sums up to X", "sums of up to X", "sums to X"
    if dna_name == "addition":
        match = re.search(r'sums?\s+(?:up\s+to|of\s+up\s+to|to)\s+(\d+)', text)
        if match:
            max_val = int(match.group(1))
            bounds["max_sum"] = (0, max_val)
        else:
            # Special case: "X-digit and Y-digit numbers" (e.g., "2-digit and 1-digit")
            # Max sum is (10^X - 1) + (10^Y - 1)
            # e.g., 2-digit and 1-digit → (99 + 9) = 108, round to 100
            digit_match = re.search(r'(\d)-digit\s+and\s+(\d)-digit', text)
            if digit_match:
                larger_digits = int(digit_match.group(1))
                smaller_digits = int(digit_match.group(2))
                max_larger = (10 ** larger_digits) - 1
                max_smaller = (10 ** smaller_digits) - 1
                max_val = max_larger + max_smaller
                # Round to nearest 10 for cleaner bounds
                max_val = ((max_val + 5) // 10) * 10
                bounds["max_sum"] = (3, max_val)
    
    # Subtraction: operand bound is enforced by the DNA's per-grade
    # _PARAM_BOUNDS[grade] (g1: a<100, g2: a<1000, g3: a<10000). All
    # MATATAG K-3 subtraction LCs use operand-bound language
    # ("both numbers are less than N"), not result-bound language
    # ("differences up to N"). The `max_difference` axis was removed
    # from the catalog on 2026-07-01 — see axes_catalog.py header.
    # However, we still parse and store max_minuend for UI purposes
    # (to show a discrete "max_minuend" axis when the LC has an explicit bound).
    elif dna_name == "subtraction":
        # Parse explicit operand bounds
        match = re.search(r'(?:less than|up to)\s+(\d+)', text)
        if match:
            max_val = int(match.group(1))
            bounds["max_minuend"] = (1, max_val)
    
    # Multiplication: "products up to X"
    elif dna_name == "multiplication":
        match = re.search(r'products?\s+(?:up\s+to|of\s+up\s+to|to)\s+(\d+)', text)
        if match:
            max_val = int(match.group(1))
            bounds["max_product"] = (0, max_val)
        
        # Parse table level
        if "6, 7, 8, and 9" in text or "6, 7, 8, 9" in text or "6, 7, 8, or 9" in text:
            bounds["table"] = "6_7_8_9"
        elif "2, 3, 4, 5, and 10" in text or "2, 3, 4, 5, 10" in text:
            bounds["table"] = "2_3_4_5_10"
            
        # Parse number type
        if "2- to 3-digit" in text or "2- to 4-digit" in text:
            bounds["number_type"] = "multi_digit"
        elif "2-digit" in text or "3-digit" in text:
            bounds["number_type"] = "multi_digit"

        # Parse missing structure
        if "missing number" in text or "missing term" in text:
            bounds["structure"] = "factor_unknown"
    
    # Division: operand bound is enforced by the DNA's per-grade
    # _PARAM_BOUNDS[grade] (q_max: g2=50, g3=100). All MATATAG K-3
    # division LCs use operand-bound language ("2,3,4,5,10 tables" or
    # "2- to 3-digit numbers"), not result-bound language
    # ("quotients up to N"). The `max_quotient` axis was removed from
    # the catalog on 2026-07-01 — see axes_catalog.py header.
    elif dna_name == "division":
        # Parse table level
        if "6, 7, 8, and 9" in text or "6, 7, 8, 9" in text or "6, 7, 8, or 9" in text:
            bounds["table"] = "6_7_8_9"
        elif "2, 3" in text and "5, and 10" in text:
            bounds["table"] = "2_3_4_5_10"
        elif "2, 3, 4, 5, and 10" in text or "2, 3, 4, 5, 10" in text:
            bounds["table"] = "2_3_4_5_10"
            
        # Parse remainder
        if "without remainder" in text:
            bounds["remainder"] = "none"
        elif "with remainder" in text:
            bounds["remainder"] = "with_remainder"

        # Parse missing structure
        if "missing number" in text or "missing term" in text:
            bounds["structure"] = "divisor_unknown"
    
    # Counting: "count up to X", "numbers up to X"
    elif dna_name == "counting":
        match = re.search(r'(?:count|numbers?)\s+(?:up\s+to|to)\s+(\d+)', text)
        if match:
            max_val = int(match.group(1))
            min_val = 10
            bounds["range"] = (min_val, max_val)
        
        # Parse skip pool from text
        allowed = []
        if "1 more or 1 less" in text:
            allowed = [1]
        elif not any(f"{x}s" in text for x in [2, 5, 10, 20, 50, 100]):
            allowed = [1]
        else:
            if "1s" in text or "count" in text:
                allowed.append(1)
            for skip in [2, 5, 10, 20, 50, 100]:
                if f"{skip}s" in text:
                    allowed.append(skip)
        bounds["skip_pool"] = allowed
    
    # Missing Number: "missing number in addition or subtraction... / multiplication or division..."
    elif dna_name == "missing_number":
        # Parse operation
        if "multiplication" in text or "division" in text:
            bounds["operation"] = "multiplication_division"
        elif "addition" in text or "subtraction" in text:
            bounds["operation"] = "addition_subtraction"

        # Parse limit / max_result
        match = re.search(r'(?:numbers|sums?|differences?|up\s+to|to)\s+(\d+)', text)
        if match:
            bounds["max_result"] = int(match.group(1))

        # Parse tables
        if "6, 7, 8, and 9" in text or "6, 7, 8, 9" in text or "6, 7, 8, or 9" in text:
            bounds["tables"] = [6, 7, 8, 9]
        elif "2, 3, 4, 5, and 10" in text or "2, 3, 4, 5, 10" in text or "2, 3, 4, 5, or 10" in text:
            bounds["tables"] = [2, 3, 4, 5, 10]
            
    # Place value: "X-digit numbers"
    elif dna_name == "place_value":
        match = re.search(r'(\d+)-digit', text)
        if match:
            digits = int(match.group(1))
            bounds["num_digits"] = (1, digits)
            
    # Number reading: "numerals/numbers up to X"
    elif dna_name == "number_reading":
        match = re.search(r'(?:numerals?|numbers?)\s+(?:up\s+to|to)\s+(\d+)', text)
        if match:
            max_val = int(match.group(1))
            bounds["range"] = (10, max_val)

    # Symmetry and slides: restrict to slides if symmetry isn't mentioned
    elif dna_name == "symmetry_slides":
        if "symmetry" in text or "symmetric" in text:
            pass
        else:
            bounds["concept"] = "slide_translation"

    # Mass and capacity: restrict to mass if capacity/volume/liter is not mentioned
    elif dna_name == "mass_capacity":
        if "capacity" in text or "liter" in text or "milliliter" in text or "volume" in text:
            pass
        else:
            bounds["measurement_type"] = "mass"

    # Geometric lines: restrict to point/line/segment/ray if parallel/intersecting/perpendicular is not mentioned
    elif dna_name == "geometric_lines":
        if "parallel" in text or "intersecting" in text or "perpendicular" in text:
            pass
        else:
            bounds["concept_type"] = "point_line_segment_ray"
            
    # Generic text-scrape fallback if no primary limit key was found.
    # Attempt to extract any number >= 10 from the LC text and use it
    # as the bound for dimension-bearing DNA concepts.
    # NOTE: `max_difference` was removed from this list on 2026-07-01.
    # Subtraction LCs are all operand-bound ("both numbers are less
    # than N"), not result-bound, so the DNA's per-grade bounds suffice.
    limit_keys = ["range", "max_value", "max_total", "max_sum", "max_product", "num_digits"]
    if not any(key in bounds for key in limit_keys):
        limits = []
        
        # Check for digit limits first (e.g. "up to 4 digits")
        digit_match = re.search(r'(?:up\s+to|to)\s+(\d+)\s+digits?', text)
        if digit_match:
            digits = int(digit_match.group(1))
            val = (10 ** digits) - 1
            limits.append(val)
        else:
            for match in re.finditer(r'\b\d+\b', text):
                val = int(match.group(0))
                if val >= 10:
                    limits.append(val)
                    
        if limits:
            limit = max(limits)
            if dna_name in ("comparing_ordering", "rounding"):
                bounds["max_value"] = (1, limit)
            elif dna_name in ("counting", "number_reading"):
                bounds["range"] = (10, limit)
            elif dna_name == "money_peso":
                bounds["max_total"] = (1, limit)
            elif dna_name == "addition":
                bounds["max_sum"] = (0, limit)
            elif dna_name == "place_value":
                if limit >= 1000:
                    bounds["num_digits"] = (1, 4)
                elif limit >= 100:
                    bounds["num_digits"] = (1, 3)
                elif limit >= 10:
                    bounds["num_digits"] = (1, 2)

    # ── Grade-aware curriculum fallback ──────────────────────────────────────
    # If after all text parsing we STILL have no primary bound for a
    # dimension-bearing DNA concept, apply the MATATAG per-grade ceiling.
    # This ensures scalar 1.0 ALWAYS resolves to a curriculum-valid integer
    # and never crashes the DNA with an impossibly small max.
    if not any(key in bounds for key in limit_keys):
        grade_defaults = _GRADE_DEFAULT_BOUNDS.get(dna_name, {}).get(grade, {})
        if "max_sum" in grade_defaults and dna_name == "addition":
            bounds["max_sum"] = (0, grade_defaults["max_sum"])
        elif "max_value" in grade_defaults and dna_name in ("comparing_ordering", "rounding"):
            bounds["max_value"] = (1, grade_defaults["max_value"])
        elif "range_max" in grade_defaults and dna_name in ("counting", "number_reading"):
            bounds["range"] = (10, grade_defaults["range_max"])
        elif "max_product" in grade_defaults and dna_name == "multiplication":
            bounds["max_product"] = (0, grade_defaults["max_product"])
        elif "max_total" in grade_defaults and dna_name == "money_peso":
            bounds["max_total"] = (1, grade_defaults["max_total"])

    # Extract regrouping booleans
    if "without regrouping" in text:
        bounds["regrouping"] = False
    elif "with regrouping" in text:
        bounds["regrouping"] = True
    elif dna_name == "fractions" and ("add" in text or "subtract" in text or "sum" in text or "difference" in text):
        bounds["operation"] = "add_subtract"
    elif "with and without regrouping" in text:
        # Don't strictly bound it, let the catalog dictate options
        pass
        
    return bounds


def get_node_competency_bounds(node_id: str, dna_name: Optional[str] = None) -> Dict[str, Tuple[int, int]]:
    """
    Get competency-specific bounds for a node's difficulty dimensions.
    
    Returns dict mapping dimension names to (min, max) tuples, derived
    from the LC text. When the LC text has no explicit numeric ceiling,
    falls back to the MATATAG grade-appropriate default so that scalar
    1.0 always maps to a valid maximum (never crashes the DNA).
    
    Returns empty dict if node not found or no DNA mappings exist.
    """
    node_info = _KG_NODES.get(node_id)
    if not node_info:
        return {}
    
    competency = node_info.get("competency", "")
    grade = node_info.get("grade", 1)
    dnas = NODE_TO_DNA.get(node_id, [])
    if not dnas:
        return {}
    
    # Use selected DNA if provided and valid, otherwise fallback to primary DNA
    selected_dna = dna_name if (dna_name and dna_name in dnas) else dnas[0]
    return _parse_competency_bounds(competency, selected_dna, grade)


# ═══════════════════════════════════════════════════════════════════════════════
# NODE_TO_DNA
# Static mapping of node_id → list of DNA concept names.
#
# Construction rationale:
#   - Each node covers 1–3 closely related competency aspects.
#   - DNA names are the exact concept strings from each DNA file.
#   - When a node spans two concepts (e.g. add + subtract in the same
#     problem-solving context), both are listed so the pipeline can pick
#     the most appropriate one for a given formatter.
# ═══════════════════════════════════════════════════════════════════════════════

from backend.app.practice_gen.schemas.visuals import VisualSchemaRegistry

# New Binding Registry (Phase 2 Migration)
BINDINGS = {
    "mat_g1_na_q1_0": {
        "dna": "counting",
        "visual": "emoji_pictorial"
    },
    "mat_g1_na_q1_1": {
        "dna": "number_reading",
        "visual": "emoji_pictorial"
    },
    "mat_g1_na_q1_2": {
        "dna": "number_reading",
        "visual": "emoji_pictorial"
    },
    "mat_g1_na_q1_3": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g1_na_q1_4": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g1_na_q1_5": {
        "dna": "ordinal_numbers",
        "visual": "sort_order"
    },
    "mat_g1_na_q1_6": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q1_7": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q1_8": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q1_9": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q2_0": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g1_na_q2_1": {
        "dna": "counting",
        "visual": "emoji_pictorial"
    },
    "mat_g1_na_q2_2": {
        "dna": "place_value",
        "visual": "place_value_blocks_read"
    },
    "mat_g1_na_q2_3": {
        "dna": "place_value",
        "visual": "place_value_blocks_read"
    },
    "mat_g1_na_q2_4": {
        "dna": "place_value",
        "visual": "place_value_blocks_read"
    },
    "mat_g1_na_q2_5": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q2_6": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q3_0": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g1_na_q3_1": {
        "dna": "missing_number",
        "visual": "NumberBond"
    },
    "mat_g1_na_q3_2": {
        "dna": "missing_number",
        "visual": "NumberBond"
    },
    "mat_g1_na_q3_3": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g1_na_q3_4": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g1_na_q3_5": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g1_na_q3_6": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g1_na_q3_7": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g1_na_q4_0": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g1_na_q4_1": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g1_na_q4_2": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g1_na_q4_3": {
        "dna": "money_peso",
        "visual": "peso_money_read"
    },
    "mat_g1_na_q4_4": {
        "dna": "money_peso",
        "visual": "peso_money_build"
    },
    "mat_g1_na_q4_5": {
        "dna": "money_peso",
        "visual": "peso_money_build"
    },
    "mat_g1_na_q4_6": {
        "dna": "money_peso",
        "visual": "peso_money_build"
    },
    "mat_g1_mg_q1_0": {
        "dna": "shapes_2d",
        "visual": "shape_board"
    },
    "mat_g1_mg_q1_1": {
        "dna": "shapes_2d",
        "visual": "shape_board"
    },
    "mat_g1_mg_q1_2": {
        "dna": "shapes_2d",
        "visual": "shape_board"
    },
    "mat_g1_mg_q2_0": {
        "dna": "length_measurement",
        "visual": "ruler_measure"
    },
    "mat_g1_mg_q2_1": {
        "dna": "length_measurement",
        "visual": "ruler_measure"
    },
    "mat_g1_mg_q2_2": {
        "dna": "length_measurement",
        "visual": "ruler_measure"
    },
    "mat_g1_mg_q4_0": {
        "dna": "symmetry_slides",
        "visual": "shape_board"
    },
    "mat_g1_mg_q4_1": {
        "dna": "time_reading",
        "visual": "clock_set"
    },
    "mat_g1_mg_q4_2": {
        "dna": "calendar",
        "visual": "Calendar"
    },
    "mat_g1_mg_q4_3": {
        "dna": "calendar",
        "visual": "Calendar"
    },
    "mat_g1_mg_q4_4": {
        "dna": "time_reading",
        "visual": "clock_set"
    },
    "mat_g1_dp_q3_0": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g1_dp_q3_1": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g1_dp_q3_2": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g1_dp_q3_3": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g2_na_q1_0": {
        "dna": "counting",
        "visual": "number_line_read"
    },
    "mat_g2_na_q1_1": {
        "dna": "number_reading",
        "visual": "place_value_blocks_read"
    },
    "mat_g2_na_q1_2": {
        "dna": "number_reading",
        "visual": "place_value_blocks_read"
    },
    "mat_g2_na_q1_3": {
        "dna": "counting",
        "visual": "bar_chart_read"
    },
    "mat_g2_na_q1_4": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g2_na_q1_5": {
        "dna": "ordinal_numbers",
        "visual": "mcq"
    },
    "mat_g2_na_q1_6": {
        "dna": "place_value",
        "visual": "place_value_blocks_read"
    },
    "mat_g2_na_q1_7": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g2_na_q1_8": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g2_na_q1_9": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g2_na_q1_10": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_0": {
        "dna": "money_peso",
        "visual": "peso_money_read"
    },
    "mat_g2_na_q2_1": {
        "dna": "money_peso",
        "visual": "peso_money_read"
    },
    "mat_g2_na_q2_2": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_3": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_4": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_5": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_6": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_7": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_8": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g2_na_q2_9": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g2_na_q3_0": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_1": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_2": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_3": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_4": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_5": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_6": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_7": {
        "dna": "missing_number",
        "visual": "mcq"
    },
    "mat_g2_na_q3_8": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_9": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q4_0": {
        "dna": "fractions",
        "visual": "fraction_shade"
    },
    "mat_g2_na_q4_1": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g2_na_q4_2": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g2_na_q4_3": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g2_na_q4_4": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g2_na_q4_5": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g2_mg_q1_0": {
        "dna": "shapes_2d",
        "visual": "shape_board"
    },
    "mat_g2_mg_q1_1": {
        "dna": "shapes_2d",
        "visual": "shape_board"
    },
    "mat_g2_mg_q1_2": {
        "dna": "symmetry_slides",
        "visual": "shape_board"
    },
    "mat_g2_mg_q2_0": {
        "dna": "length_measurement",
        "visual": "ruler_measure"
    },
    "mat_g2_mg_q2_1": {
        "dna": "length_measurement",
        "visual": "mcq"
    },
    "mat_g2_mg_q2_2": {
        "dna": "length_measurement",
        "visual": "mcq"
    },
    "mat_g2_mg_q2_3": {
        "dna": "length_measurement",
        "visual": "mcq"
    },
    "mat_g2_mg_q4_0": {
        "dna": "time_reading",
        "visual": "clock_set"
    },
    "mat_g2_mg_q4_1": {
        "dna": "time_reading",
        "visual": "clock_set"
    },
    "mat_g2_mg_q4_2": {
        "dna": "time_reading",
        "visual": "clock_set"
    },
    "mat_g2_mg_q4_3": {
        "dna": "geometric_lines",
        "visual": "mcq"
    },
    "mat_g2_mg_q4_4": {
        "dna": "perimeter",
        "visual": "mcq"
    },
    "mat_g2_mg_q4_5": {
        "dna": "perimeter",
        "visual": "mcq"
    },
    "mat_g2_mg_q4_6": {
        "dna": "perimeter",
        "visual": "mcq"
    },
    "mat_g2_dp_q3_0": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g2_dp_q3_1": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g3_na_q1_0": {
        "dna": "number_reading",
        "visual": "number_line_read"
    },
    "mat_g3_na_q1_1": {
        "dna": "number_reading",
        "visual": "place_value_blocks_read"
    },
    "mat_g3_na_q1_2": {
        "dna": "ordinal_numbers",
        "visual": "mcq"
    },
    "mat_g3_na_q1_3": {
        "dna": "place_value",
        "visual": "place_value_blocks_read"
    },
    "mat_g3_na_q1_4": {
        "dna": "rounding",
        "visual": "number_line_read"
    },
    "mat_g3_na_q1_5": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g3_na_q1_6": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g3_na_q2_0": {
        "dna": "money_peso",
        "visual": "peso_money_read"
    },
    "mat_g3_na_q2_1": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_2": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_3": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_4": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_5": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_6": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_7": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g3_na_q3_0": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q3_1": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q3_2": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q3_3": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q3_4": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q3_5": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g3_na_q3_6": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g3_na_q4_0": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q4_1": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q4_2": {
        "dna": "missing_number",
        "visual": "mcq"
    },
    "mat_g3_na_q4_3": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q4_4": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q4_5": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q4_6": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g3_na_q4_7": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g3_mg_q1_0": {
        "dna": "area",
        "visual": "shape_board"
    },
    "mat_g3_mg_q1_1": {
        "dna": "area",
        "visual": "grid_area"
    },
    "mat_g3_mg_q1_2": {
        "dna": "area",
        "visual": "grid_area"
    },
    "mat_g3_mg_q1_3": {
        "dna": "area",
        "visual": "grid_area"
    },
    "mat_g3_mg_q1_4": {
        "dna": "geometric_lines",
        "visual": "mcq"
    },
    "mat_g3_mg_q1_5": {
        "dna": "geometric_lines",
        "visual": "mcq"
    },
    "mat_g3_mg_q1_6": {
        "dna": "geometric_lines",
        "visual": "mcq"
    },
    "mat_g3_mg_q2_0": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q2_1": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q2_2": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q2_3": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q2_4": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q2_5": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q4_0": {
        "dna": "symmetry_slides",
        "visual": "shape_board"
    },
    "mat_g3_mg_q4_1": {
        "dna": "symmetry_slides",
        "visual": "shape_board"
    },
    "mat_g3_mg_q4_2": {
        "dna": "symmetry_slides",
        "visual": "shape_board"
    },
    "mat_g3_dp_q3_0": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g3_dp_q3_1": {
        "dna": "bar_graphs",
        "visual": "bar_chart_read"
    },
    "mat_g3_dp_q3_2": {
        "dna": "bar_graphs",
        "visual": "bar_chart_read"
    },
    "mat_g3_dp_q3_3": {
        "dna": "bar_graphs",
        "visual": "bar_chart_read"
    },
    "mat_g3_dp_q3_4": {
        "dna": "probability_language",
        "visual": "mcq"
    }
}

NODE_TO_DNA: Dict[str, List[str]] = {

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 1 — Number & Algebra
    # ────────────────────────────────────────────────────────────────────────

    # Q1: Counting, reading, representing, comparing, ordering, ordinals,
    #     compose/decompose, addition intro, properties of addition
    "mat_g1_na_q1_0": ["counting"],
    "mat_g1_na_q1_1": ["number_reading"],
    "mat_g1_na_q1_2": ["number_reading", "counting"],
    "mat_g1_na_q1_3": ["comparing_ordering"],
    "mat_g1_na_q1_4": ["comparing_ordering"],
    "mat_g1_na_q1_5": ["ordinal_numbers"],
    "mat_g1_na_q1_6": ["missing_number", "addition"],
    "mat_g1_na_q1_7": ["addition"],
    "mat_g1_na_q1_8": ["addition"],
    "mat_g1_na_q1_9": ["addition"],

    # Q2: Ordering to 100, skip counting, place value (2-digit),
    #     decompose, expanded form addition, addition to 100
    "mat_g1_na_q2_0": ["comparing_ordering"],
    "mat_g1_na_q2_1": ["counting"],
    "mat_g1_na_q2_2": ["place_value"],
    "mat_g1_na_q2_3": ["place_value"],
    "mat_g1_na_q2_4": ["place_value", "addition"],
    "mat_g1_na_q2_5": ["addition"],
    "mat_g1_na_q2_6": ["addition"],

    # Q3: Subtraction intro, missing number, patterns
    "mat_g1_na_q3_0": ["subtraction"],
    "mat_g1_na_q3_1": ["missing_number"],
    "mat_g1_na_q3_2": ["missing_number", "addition"],
    "mat_g1_na_q3_3": ["subtraction"],
    "mat_g1_na_q3_4": ["subtraction"],
    "mat_g1_na_q3_5": ["subtraction", "place_value"],
    "mat_g1_na_q3_6": ["patterns"],
    "mat_g1_na_q3_7": ["patterns"],

    # Q4: Fractions (1/2, 1/4), money (coins/bills to ₱100)
    "mat_g1_na_q4_0": ["fractions"],
    "mat_g1_na_q4_1": ["fractions", "comparing_ordering"],
    "mat_g1_na_q4_2": ["fractions", "counting"],
    "mat_g1_na_q4_3": ["money_peso"],
    "mat_g1_na_q4_4": ["money_peso"],
    "mat_g1_na_q4_5": ["money_peso", "comparing_ordering"],
    "mat_g1_na_q4_6": ["money_peso", "addition"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 1 — Measurement & Geometry
    # ────────────────────────────────────────────────────────────────────────

    # Q1: 2D shapes
    "mat_g1_mg_q1_0": ["shapes_2d"],
    "mat_g1_mg_q1_1": ["shapes_2d", "comparing_ordering"],
    "mat_g1_mg_q1_2": ["shapes_2d"],

    # Q2: Length with non-standard units
    "mat_g1_mg_q2_0": ["length_measurement"],
    "mat_g1_mg_q2_1": ["length_measurement", "comparing_ordering"],
    "mat_g1_mg_q2_2": ["length_measurement", "addition"],

    # Q4: Symmetry/slides, time, calendar
    "mat_g1_mg_q4_0": ["symmetry_slides"],
    "mat_g1_mg_q4_1": ["time_reading"],
    "mat_g1_mg_q4_2": ["calendar"],
    "mat_g1_mg_q4_3": ["calendar"],
    "mat_g1_mg_q4_4": ["time_reading", "addition"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 1 — Data & Probability
    # ────────────────────────────────────────────────────────────────────────

    "mat_g1_dp_q3_0": ["pictographs"],
    "mat_g1_dp_q3_1": ["pictographs"],
    "mat_g1_dp_q3_2": ["pictographs"],
    "mat_g1_dp_q3_3": ["pictographs"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 2 — Number & Algebra
    # ────────────────────────────────────────────────────────────────────────

    # Q1: Count/read/represent to 1000, skip count, ordinals, place value (3-digit),
    #     addition (expanded form, to 1000, properties)
    "mat_g2_na_q1_0":  ["counting"],
    "mat_g2_na_q1_1":  ["number_reading"],
    "mat_g2_na_q1_2":  ["number_reading", "counting"],
    "mat_g2_na_q1_3":  ["counting"],
    "mat_g2_na_q1_4":  ["comparing_ordering"],
    "mat_g2_na_q1_5":  ["ordinal_numbers"],
    "mat_g2_na_q1_6":  ["place_value"],
    "mat_g2_na_q1_7":  ["addition", "counting"],
    "mat_g2_na_q1_8":  ["addition", "place_value"],
    "mat_g2_na_q1_9":  ["addition"],
    "mat_g2_na_q1_10": ["addition"],

    # Q2: Money (to ₱1000), addition problems, subtraction (to 1000),
    #     patterns (increasing/decreasing)
    "mat_g2_na_q2_0": ["money_peso"],
    "mat_g2_na_q2_1": ["money_peso", "comparing_ordering"],
    "mat_g2_na_q2_2": ["addition", "money_peso"],
    "mat_g2_na_q2_3": ["subtraction"],
    "mat_g2_na_q2_4": ["subtraction"],
    "mat_g2_na_q2_5": ["subtraction"],
    "mat_g2_na_q2_6": ["subtraction"],
    "mat_g2_na_q2_7": ["subtraction", "addition"],
    "mat_g2_na_q2_8": ["patterns"],
    "mat_g2_na_q2_9": ["patterns"],

    # Q3: Repeated addition → multiplication, tables 2-5-10,
    #     division intro, missing number in mult/div, even/odd
    "mat_g2_na_q3_0": ["multiplication", "counting"],
    "mat_g2_na_q3_1": ["multiplication", "addition"],
    "mat_g2_na_q3_2": ["multiplication"],
    "mat_g2_na_q3_3": ["multiplication"],
    "mat_g2_na_q3_4": ["division"],
    "mat_g2_na_q3_5": ["division"],
    "mat_g2_na_q3_6": ["division"],
    "mat_g2_na_q3_7": ["missing_number", "multiplication"],
    "mat_g2_na_q3_8": ["division", "comparing_ordering"],
    "mat_g2_na_q3_9": ["division"],

    # Q4: Fractions (unit, similar) with denominators 2-4
    "mat_g2_na_q4_0": ["fractions"],
    "mat_g2_na_q4_1": ["fractions", "number_reading"],
    "mat_g2_na_q4_2": ["fractions", "comparing_ordering"],
    "mat_g2_na_q4_3": ["fractions"],
    "mat_g2_na_q4_4": ["fractions", "number_reading"],
    "mat_g2_na_q4_5": ["fractions", "comparing_ordering"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 2 — Measurement & Geometry
    # ────────────────────────────────────────────────────────────────────────

    # Q1: Circles/composite shapes, slides
    "mat_g2_mg_q1_0": ["shapes_2d"],
    "mat_g2_mg_q1_1": ["shapes_2d"],
    "mat_g2_mg_q1_2": ["symmetry_slides"],

    # Q2: Length in m/cm
    "mat_g2_mg_q2_0": ["length_measurement"],
    "mat_g2_mg_q2_1": ["length_measurement"],
    "mat_g2_mg_q2_2": ["length_measurement"],
    "mat_g2_mg_q2_3": ["length_measurement", "addition"],

    # Q4: Duration/elapsed time, time in hours+minutes,
    #     straight vs curved lines, perimeter
    "mat_g2_mg_q4_0": ["time_reading", "calendar"],
    "mat_g2_mg_q4_1": ["time_reading"],
    "mat_g2_mg_q4_2": ["time_reading", "subtraction"],
    "mat_g2_mg_q4_3": ["geometric_lines"],
    "mat_g2_mg_q4_4": ["perimeter", "length_measurement"],
    "mat_g2_mg_q4_5": ["perimeter"],
    "mat_g2_mg_q4_6": ["perimeter", "addition"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 2 — Data & Probability
    # ────────────────────────────────────────────────────────────────────────

    "mat_g2_dp_q3_0": ["pictographs"],
    "mat_g2_dp_q3_1": ["pictographs", "comparing_ordering"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 3 — Number & Algebra
    # ────────────────────────────────────────────────────────────────────────

    # Q1: Numbers to 10 000, ordinals, place value (4-digit),
    #     rounding, comparing/ordering to 10 000
    "mat_g3_na_q1_0": ["number_reading"],
    "mat_g3_na_q1_1": ["number_reading"],
    "mat_g3_na_q1_2": ["ordinal_numbers"],
    "mat_g3_na_q1_3": ["place_value"],
    "mat_g3_na_q1_4": ["rounding"],
    "mat_g3_na_q1_5": ["comparing_ordering"],
    "mat_g3_na_q1_6": ["comparing_ordering"],

    # Q2: Money (write in words/symbols), addition to 10 000
    #     (with regroup, estimate), subtraction, combined ops
    "mat_g3_na_q2_0": ["money_peso", "number_reading"],
    "mat_g3_na_q2_1": ["addition"],
    "mat_g3_na_q2_2": ["addition", "rounding"],
    "mat_g3_na_q2_3": ["addition"],
    "mat_g3_na_q2_4": ["subtraction"],
    "mat_g3_na_q2_5": ["subtraction", "rounding"],
    "mat_g3_na_q2_6": ["addition", "subtraction"],
    "mat_g3_na_q2_7": ["addition", "subtraction"],

    # Q3: Multiplication tables 6-9, properties, 2-3 digit × 1-2 digit,
    #     estimate product, patterns (repeating + increasing)
    "mat_g3_na_q3_0": ["multiplication"],
    "mat_g3_na_q3_1": ["multiplication"],
    "mat_g3_na_q3_2": ["multiplication"],
    "mat_g3_na_q3_3": ["multiplication", "rounding"],
    "mat_g3_na_q3_4": ["multiplication"],
    "mat_g3_na_q3_5": ["patterns"],
    "mat_g3_na_q3_6": ["patterns"],

    # Q4: Division with tables 6-9, missing term, 2-3 digit ÷ 1 digit,
    #     estimate quotient, fractions ≥ 1, add/sub similar fractions
    "mat_g3_na_q4_0": ["division"],
    "mat_g3_na_q4_1": ["division"],
    "mat_g3_na_q4_2": ["missing_number", "division"],
    "mat_g3_na_q4_3": ["division"],
    "mat_g3_na_q4_4": ["division", "rounding"],
    "mat_g3_na_q4_5": ["division"],
    "mat_g3_na_q4_6": ["fractions"],
    "mat_g3_na_q4_7": ["fractions"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 3 — Measurement & Geometry
    # ────────────────────────────────────────────────────────────────────────

    # Q1: Area (sq, rect), geometric lines, equal-length segments
    "mat_g3_mg_q1_0": ["area"],
    "mat_g3_mg_q1_1": ["area"],
    "mat_g3_mg_q1_2": ["area", "multiplication"],
    "mat_g3_mg_q1_3": ["area", "multiplication"],
    "mat_g3_mg_q1_4": ["geometric_lines"],
    "mat_g3_mg_q1_5": ["geometric_lines"],
    "mat_g3_mg_q1_6": ["geometric_lines", "length_measurement"],

    # Q2: Mass (g/kg/mg), capacity (L/mL)
    "mat_g3_mg_q2_0": ["mass_capacity"],
    "mat_g3_mg_q2_1": ["mass_capacity"],
    "mat_g3_mg_q2_2": ["mass_capacity", "comparing_ordering"],
    "mat_g3_mg_q2_3": ["mass_capacity"],
    "mat_g3_mg_q2_4": ["mass_capacity"],
    "mat_g3_mg_q2_5": ["mass_capacity", "comparing_ordering"],

    # Q4: Slides (2-direction), symmetry
    "mat_g3_mg_q4_0": ["symmetry_slides"],
    "mat_g3_mg_q4_1": ["symmetry_slides"],
    "mat_g3_mg_q4_2": ["symmetry_slides"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 3 — Data & Probability
    # ────────────────────────────────────────────────────────────────────────

    "mat_g3_dp_q3_0": ["pictographs", "bar_graphs"],
    "mat_g3_dp_q3_1": ["bar_graphs"],
    "mat_g3_dp_q3_2": ["bar_graphs"],
    "mat_g3_dp_q3_3": ["bar_graphs", "addition"],
    "mat_g3_dp_q3_4": ["probability_language"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def get_node_dnas(node_id: str) -> List[str]:
    """
    Return the list of DNA concept names for a node.

    Args:
        node_id: MATATAG node identifier, e.g. "mat_g1_na_q1_7".

    Returns:
        List of DNA concept name strings, or an empty list if the node
        is not in NODE_TO_DNA.
    """
    return NODE_TO_DNA.get(node_id, [])


def get_node_formatters(node_id: str) -> List[str]:
    """
    Return the union of compatible formatters from all DNAs for a node.

    Looks up each DNA concept in COMPATIBILITY and unions the results.
    Preserves insertion order of the first occurrence of each formatter.

    Args:
        node_id: MATATAG node identifier.

    Returns:
        Ordered list of formatter name strings.
    """
    seen: Set[str] = set()
    result: List[str] = []
    for concept in get_node_dnas(node_id):
        for fmt in COMPATIBILITY.get(concept, []):
            if fmt not in seen:
                seen.add(fmt)
                result.append(fmt)
    return result


def get_node_info(node_id: str) -> Optional[Dict]:
    """
    Return the full knowledge-graph node dict for a node.

    Args:
        node_id: MATATAG node identifier.

    Returns:
        Node dict from knowledge_graph_g1_3.json, or None if not found.
    """
    return _KG_NODES.get(node_id)


def find_node_id(grade: int, branch: str, quarter: int, index: int) -> str:
    """
    Construct a node_id from its components.

    Args:
        grade: Grade level (1–3).
        branch: Branch code: "na", "mg", or "dp".
        quarter: Quarter number (1–4).
        index: Zero-based index within that quarter.

    Returns:
        Formatted node ID string, e.g. "mat_g2_na_q3_5".
    """
    return f"mat_g{grade}_{branch}_q{quarter}_{index}"


def get_all_node_ids(
    grade: Optional[int] = None,
    branch: Optional[str] = None,
) -> List[str]:
    """
    Return all node IDs from NODE_TO_DNA, optionally filtered.

    Nodes are returned in the order they appear in NODE_TO_DNA (insertion
    order, which follows the knowledge-graph branch ordering).

    Args:
        grade: If given, only return nodes for this grade.
        branch: If given (e.g. "na", "mg", "dp"), only return nodes in
            that branch.

    Returns:
        List of node ID strings.
    """
    result: List[str] = []
    for node_id in NODE_TO_DNA:
        parts = node_id.split("_")
        # Expected format: mat_g{grade}_{branch}_q{quarter}_{index}
        if len(parts) < 5:
            continue
        node_grade_str = parts[1]   # "g1", "g2", "g3"
        node_branch = parts[2]      # "na", "mg", "dp"

        if grade is not None:
            if node_grade_str != f"g{grade}":
                continue
        if branch is not None:
            if node_branch != branch:
                continue

        result.append(node_id)

    return result
