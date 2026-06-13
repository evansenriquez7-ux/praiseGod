"""
MATATAG MCQ Skeleton Generators

Generates deterministic, auto-validatable MCQ problems for MATATAG Math curriculum.
Each skeleton includes:
  - stem: Question text in pure elementary math notation
  - correct_answer: Computed deterministically
  - options: 4 choices with trap names for wrong answers

Usage:
    skeleton = get_matatag_skeleton(competency_text, grade=3, difficulty=0.5)
    
    # Stateless regeneration from ID:
    skeleton = regenerate_matatag_skeleton("mat_3_arithmetic_12345")
    
    # Validate student answer:
    result = validate_matatag_answer("mat_3_arithmetic_12345", "405")

Author: CCMed Team
"""

import random
import re
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from math import gcd
from functools import reduce

# Handle both relative and absolute imports for flexibility
try:
    from .constraint_extractor import extract_constraints
    from .curriculum_context import get_curriculum_context
    from .matatag_dimensions import (
        DIFFICULTY_LEVEL_MAP,
        GENERATOR_DIMENSIONS,
        get_dimension_values,
        interpolate_dimension,
    )
except ImportError:
    from constraint_extractor import extract_constraints
    from curriculum_context import get_curriculum_context
    from matatag_dimensions import (
        DIFFICULTY_LEVEL_MAP,
        GENERATOR_DIMENSIONS,
        get_dimension_values,
        interpolate_dimension,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

MAX_RETRIES = 5

# Generator type codes for skeleton IDs
GENERATOR_CODES = {
    "counting": "cnt",
    "place_value": "pv",
    "arithmetic": "ar",
    "fractions": "fr",
    "decimals": "dc",
    "ratios_percent": "rp",
    "algebra": "alg",
    "geometry_props": "gp",
    "measurement": "ms",
    "data_probability": "dp",
    "conceptual": "con",
    "compose_decompose": "cd",
    "compare_order": "co",
}

GENERATOR_CODES_REVERSE = {v: k for k, v in GENERATOR_CODES.items()}

# ═══════════════════════════════════════════════════════════════════════════════
# VISUAL SKELETON MAPPING
# Maps competency patterns to visual_skeletons types
# When a competency matches, the question can use either MCQ or visual rendering
# ═══════════════════════════════════════════════════════════════════════════════

VISUAL_COMPETENCY_ROUTES = [
    # Number Line - fractions, decimals, plotting numbers
    {
        "pattern": r"(?i)(number line|plot.*fraction|locate.*fraction|mark.*number|position.*number|plot.*decimal)",
        "visual_type": "NumberLine",
        "grades": [1, 2, 3, 4, 5, 6],
        "mcq_fallback": True,  # Can also use MCQ
    },
    # Bar Chart / Pictograph - data representation
    {
        "pattern": r"(?i)(pictograph|bar graph|bar chart|present data|interpret.*graph|organize data.*table|read.*graph)",
        "visual_type": "BarChart",
        "grades": [1, 2, 3, 4, 5, 6],
        "mcq_fallback": False,  # Visual strongly preferred
    },
    # Clock - time telling
    {
        "pattern": r"(?i)(read.*time|write.*time|clock|hour|half hour|quarter hour|elapsed time|time.*analog|time.*digital)",
        "visual_type": "ClockSet",
        "grades": [1, 2, 3, 4],
        "mcq_fallback": True,
    },
    # Money - peso/centavo problems (more specific patterns to avoid false positives like "change the order")
    {
        "pattern": r"(?i)(₱|peso|centavo|money|coin|bill(?!s)|currency|price|cost|buy|pay|value of.*bill|denominations?)",
        "visual_type": "PesoMoney",
        "grades": [1, 2, 3, 4, 5],
        "mcq_fallback": True,
    },
    # Grid Area - area and perimeter with grids
    {
        "pattern": r"(?i)(area.*grid|count.*square|square units|shade.*area|grid.*area|perimeter.*grid)",
        "visual_type": "GridArea",
        "grades": [2, 3, 4, 5],
        "mcq_fallback": True,
    },
    # Sort Order - ordering numbers (visual only - MCQ ordering doesn't work well)
    {
        "pattern": r"(?i)(order.*number|arrange.*smallest|arrange.*largest|sort.*number|ascending|descending)",
        "visual_type": "SortOrder",
        "grades": [1, 2, 3, 4],
        "mcq_fallback": False,  # Visual only - ordering as MCQ options is confusing
    },
    # Fill In Table - patterns and tables
    {
        "pattern": r"(?i)(complete.*table|fill.*table|pattern.*table|number pattern|missing.*table)",
        "visual_type": "FillInTable",
        "grades": [1, 2, 3, 4, 5],
        "mcq_fallback": True,
    },
    # Rule Discovery - finding patterns
    {
        "pattern": r"(?i)(find.*pattern|rule.*pattern|next.*pattern|continue.*pattern|what comes next)",
        "visual_type": "RuleDiscovery",
        "grades": [1, 2, 3, 4],
        "mcq_fallback": True,
    },
    # Calendar - days, weeks, months
    {
        "pattern": r"(?i)(calendar|days.*week|months.*year|date|day.*month|week.*month)",
        "visual_type": "Calendar",
        "grades": [1, 2, 3],
        "mcq_fallback": True,
    },
    # Categorize - sorting objects by attributes
    {
        "pattern": r"(?i)(sort.*shape|group.*by|categorize|classify|sort by|same.*different)",
        "visual_type": "Categorize",
        "grades": [1, 2, 3],
        "mcq_fallback": True,
    },
]


def get_visual_type_for_competency(competency_text: str, grade: int) -> Optional[Dict[str, Any]]:
    """
    Check if a competency can use visual skeleton rendering.
    
    Returns:
        None if no visual type matches
        Dict with 'visual_type', 'mcq_fallback' if match found
    """
    for route in VISUAL_COMPETENCY_ROUTES:
        if re.search(route["pattern"], competency_text):
            # Check grade appropriateness
            if grade in route.get("grades", range(1, 11)):
                return {
                    "visual_type": route["visual_type"],
                    "mcq_fallback": route.get("mcq_fallback", True),
                }
    return None


# Routing patterns - priority order (first match wins)
COMPETENCY_ROUTES = [
    # Estimation of arithmetic results (BEFORE arithmetic - "estimate the sum" should not generate exact computation)
    # NOTE: Does NOT match "estimate the area" or "estimate length" (those go to measurement)
    {
        "pattern": r"(?i)estimat(e|ion)\b.*(sum|difference|product|quotient|addend)",
        "generator": "arithmetic",
        "grades": [2, 3, 4, 5, 6],
        "flags": {"is_estimation": True},
    },
    # Place value (includes rounding and read/write)
    {
        "pattern": r"(?i)(place value|value of a digit|digit of|expanded form|read and write numerals|read and write numbers|decompose.*into tens|round.*nearest|rounding)",
        "generator": "place_value",
        "grades": [1, 2, 3, 4, 5, 6],
    },
    # Decimals (BEFORE arithmetic - "add decimal" should use decimals, not arithmetic)
    {
        "pattern": r"(?i)decimal|tenths?|hundredths?|thousandths?",
        "generator": "decimals",
        "grades": [4, 5, 6],
    },
    # Fractions
    {
        "pattern": r"(?i)fraction|numerator|denominator|similar fraction|dissimilar|improper|mixed number|half|quarter|thirds?|equivalent|\b\d+/\d+\b",
        "generator": "fractions",
        "grades": [1, 2, 3, 4, 5, 6],
    },
    # Measurement with shape names (BEFORE geometry - "perimeter of rectangles" is measurement, not geometry)
    {
        "pattern": r"(?i)(perimeter|area).*(triangle|square|rectangle|plane figure)|measure.*(length|mass|capacity)|(length|mass|capacity).*measure",
        "generator": "measurement",
        "grades": [1, 2, 3, 4, 5, 6, 7],
    },
    # Arithmetic (higher priority - "properties of addition" should be arithmetic, not geometry)
    {
        "pattern": r"(?i)(add|subtract|multiply|divide|addition|subtraction|multiplication|division).*propert|propert.*(add|subtract|multiply|divide)|sums? (up )?to|regrouping|missing number|find the missing|number sentence|even\b|odd\b",
        "generator": "arithmetic",
        "grades": [1, 2, 3, 4, 5, 6],
    },
    # Geometry with shapes (specific shape names, not just "properties")
    {
        "pattern": r"(?i)(triangle|quadrilateral|polygon|circle|angle|parallel|perpendicular|2-dimensional|3-dimensional|shape|sides? and corners?|vertices|edges?|faces?|line segment|ray\b|symmetr|translation|slide\b|straight.*curved|curved.*straight|flat.*curved)",
        "generator": "geometry_props",
        "grades": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    },
    # Compose/decompose numbers (specific - excludes shapes)
    {
        "pattern": r"(?i)(compose|decompose).*number",
        "generator": "compose_decompose",
        "grades": [1, 2, 3],
    },
    # Compare numbers (specific)
    {
        "pattern": r"(?i)compare.*(number|two|values?)|order.*(number|from)|symbol.*(>|<|=)",
        "generator": "compare_order",
        "grades": [1, 2, 3, 4, 5, 6],
    },
    # Counting and patterns (most specific patterns first)
    {
        "pattern": r"(?i)count (up to|by|halves|quarters)|1 more|1 less|skip.?count|ordinal|next term|increasing.*pattern|decreasing.*pattern|pattern.*repeating|pattern.*increasing|determine.*pattern|create.*pattern",
        "generator": "counting",
        "grades": [1, 2, 3],
    },
    # Ratios and percent (before decimals and arithmetic - "percent to decimal" should use this)
    {
        "pattern": r"(?i)ratio|proportion|percent|percentage|\d+%",
        "generator": "ratios_percent",
        "grades": [5, 6, 7, 8],
    },
    # Arithmetic (fallback pattern)
    {
        "pattern": r"(?i)(add|subtract|multiply|divide).*number|sums? (up )?to",
        "generator": "arithmetic",
        "grades": [1, 2, 3, 4, 5, 6],
    },
    # Algebra
    {
        "pattern": r"(?i)(expression|equation|variable|polynomial|exponent|factor|laws? of|algebraic|simplify.*expression)",
        "generator": "algebra",
        "grades": [7, 8, 9, 10],
    },
    # Measurement (expanded for time/duration/mass/capacity)
    {
        "pattern": r"(?i)(length|width|height|mass|capacity|volume|perimeter|area|convert.*unit|elapsed|meter|centimeter|kilogram|gram|liter|milliliter|milligram|duration|days?.*week|hour|minute|weigh|balance|measure.*time)",
        "generator": "measurement",
        "grades": [1, 2, 3, 4, 5, 6, 7],
    },
    # Data and probability
    {
        "pattern": r"(?i)(data|graph|pictograph|bar graph|mean|median|mode|probability|outcome|chance|likely|table|frequency)",
        "generator": "data_probability",
        "grades": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    },
    # Fallback: conceptual
    {
        "pattern": r".*",
        "generator": "conceptual",
        "grades": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# TRAP DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

TRAP_CATALOG = {
    # Counting traps
    "cnt_prev": {"name": "Previous Number", "description": "Gave number before instead of after"},
    "cnt_skip": {"name": "Skipped One", "description": "Skipped to n+2 instead of n+1"},
    "cnt_back": {"name": "Counted Backwards", "description": "Subtracted instead of added"},
    "cnt_wrong_interval": {"name": "Wrong Skip Interval", "description": "Used wrong skip count"},
    "cnt_ord_off": {"name": "Ordinal Off-by-One", "description": "Confused position by 1"},
    "cnt_card_ord": {"name": "Cardinal/Ordinal Confusion", "description": "Gave count instead of position"},
    
    # Place value traps
    "pv_adj_place": {"name": "Adjacent Place", "description": "Identified wrong place column"},
    "pv_dig_val": {"name": "Digit vs Value", "description": "Gave digit without place multiplier"},
    "pv_val_dig": {"name": "Value vs Digit", "description": "Gave value instead of just digit"},
    "pv_reverse": {"name": "Reversed Number", "description": "Read digits in reverse order"},
    "pv_zero_exp": {"name": "Zero in Expanded", "description": "Included unnecessary +0 term"},
    "pv_place_shift": {"name": "Place Shift", "description": "Off by factor of 10"},
    
    # Arithmetic traps
    "ar_wrong_op": {"name": "Wrong Operation", "description": "Used opposite operation"},
    "ar_no_regroup": {"name": "Forgot Regrouping", "description": "Didn't carry or borrow"},
    "ar_double_regroup": {"name": "Double Regrouped", "description": "Carried/borrowed twice"},
    "ar_off_one": {"name": "Off By One", "description": "Simple computation error"},
    "ar_off_ten": {"name": "Off By Ten", "description": "Missed or extra carry"},
    "ar_reverse_sub": {"name": "Reversed Subtraction", "description": "Computed smaller - larger"},
    "ar_mul_add": {"name": "Multiply as Add", "description": "Added instead of multiplied"},
    "ar_div_sub": {"name": "Divide as Subtract", "description": "Subtracted instead of divided"},
    "ar_rem_drop": {"name": "Dropped Remainder", "description": "Forgot remainder in division"},
    "ar_rem_swap": {"name": "Remainder as Answer", "description": "Gave remainder instead of quotient"},
    "ar_zero_prop": {"name": "Zero Property Error", "description": "Wrong application of zero property"},
    
    # Fractions traps
    "fr_swap_nd": {"name": "Swapped N/D", "description": "Wrote numerator as denominator"},
    "fr_add_both": {"name": "Added Both Parts", "description": "Added numerators AND denominators"},
    "fr_big_num": {"name": "Bigger Numerator Wins", "description": "Compared numerators only"},
    "fr_big_den": {"name": "Bigger Denominator Wins", "description": "Thinks larger denom = larger fraction"},
    "fr_not_simp": {"name": "Not Simplified", "description": "Didn't reduce to lowest terms"},
    "fr_wrong_lcd": {"name": "Wrong LCD", "description": "Used incorrect common denominator"},
    "fr_num_unchanged": {"name": "Numerator Unchanged", "description": "Forgot to adjust numerator"},
    "fr_imp_mix": {"name": "Improper/Mixed Error", "description": "Wrong conversion"},
    "fr_unit_rev": {"name": "Unit Fraction Reversed", "description": "Thinks 1/3 > 1/2"},
    
    # Decimals traps
    "dc_place_err": {"name": "Place Value Error", "description": "Wrong decimal place name"},
    "dc_longer_bigger": {"name": "Longer is Bigger", "description": "More digits = larger value"},
    "dc_whole_cmp": {"name": "Whole Number Compare", "description": "Compared as if integers"},
    "dc_trail_zero": {"name": "Trailing Zero Matters", "description": "Thinks 0.5 != 0.50"},
    "dc_round_dir": {"name": "Round Wrong Direction", "description": "Rounded wrong way"},
    "dc_round_place": {"name": "Round Wrong Place", "description": "Wrong precision"},
    "dc_frac_conv": {"name": "Fraction Conversion Error", "description": "Wrong decimal equivalent"},
    
    # Algebra traps
    "alg_unlike": {"name": "Combined Unlike Terms", "description": "Added unlike terms"},
    "alg_exp_mul": {"name": "Exponent Multiply Error", "description": "Multiplied exponents on multiplication"},
    "alg_exp_add": {"name": "Exponent Add Error", "description": "Added exponents on addition"},
    "alg_distrib": {"name": "Distribute Error", "description": "Incomplete distribution"},
    "alg_sign_neg": {"name": "Sign Error Negative", "description": "Wrong sign with negatives"},
    "alg_middle": {"name": "Forgot Middle Term", "description": "Missing 2ab in (a+b)^2"},
    "alg_factor": {"name": "Factoring Sign Error", "description": "Wrong signs in factors"},
    "alg_coef_var": {"name": "Coefficient/Variable Confusion", "description": "Mixed up coefficient and variable"},
    "alg_wrong_inv": {"name": "Wrong Inverse", "description": "Used same operation to solve"},
    
    # Ratios/percent traps
    "rp_order": {"name": "Ratio Order Swapped", "description": "Reversed ratio terms"},
    "rp_ratio_frac": {"name": "Ratio as Fraction Error", "description": "Wrong fraction from ratio"},
    "rp_pct_dec": {"name": "Percent to Decimal Error", "description": "Wrong decimal from percent"},
    "rp_dec_pct": {"name": "Decimal to Percent Error", "description": "Wrong percent from decimal"},
    "rp_wrong_base": {"name": "Wrong Base", "description": "Used wrong number as base"},
    "rp_additive": {"name": "Additive Reasoning", "description": "Added instead of multiplied by percent"},
    
    # Geometry traps
    "gp_wrong_prop": {"name": "Wrong Property", "description": "Incorrect shape property"},
    "gp_angle_180": {"name": "Used 180 for Quad", "description": "Quad angles sum to 180"},
    "gp_angle_360": {"name": "Used 360 for Triangle", "description": "Triangle angles sum to 360"},
    "gp_rad_diam": {"name": "Radius/Diameter Confusion", "description": "Mixed up r and d"},
    "gp_parallel_perp": {"name": "Parallel/Perpendicular Swap", "description": "Confused definitions"},
    
    # Measurement traps
    "ms_conv_dir": {"name": "Conversion Direction", "description": "Multiplied instead of divided or vice versa"},
    "ms_wrong_factor": {"name": "Wrong Conversion Factor", "description": "Used incorrect conversion"},
    "ms_perim_area": {"name": "Perimeter vs Area", "description": "Used wrong formula type"},
    "ms_area_perim": {"name": "Area vs Perimeter", "description": "Used wrong formula type"},
    "ms_time_conv": {"name": "Time Conversion Error", "description": "Wrong time unit conversion"},
    
    # Data/probability traps
    "dp_mean_median": {"name": "Mean/Median Confusion", "description": "Computed wrong measure"},
    "dp_mode_mean": {"name": "Mode/Mean Confusion", "description": "Computed wrong measure"},
    "dp_prob_impossible": {"name": "Impossible Probability", "description": "P > 1 or P < 0"},
    "dp_complement": {"name": "Complement Error", "description": "P(not A) computed wrong"},
    "dp_sum_avg": {"name": "Sum vs Average", "description": "Gave sum instead of mean"},
}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINTS
# ═══════════════════════════════════════════════════════════════════════════════

def get_matatag_skeleton_with_visual_option(
    competency_text: str,
    grade: int,
    difficulty: float = 0.5,
    seed: Optional[int] = None,
    content_area: Optional[str] = None,
    quarter: Optional[int] = None,
    visual_probability: float = 0.5,
    axis_values: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a skeleton that may be MCQ or visual, depending on competency.
    
    If the competency supports visual rendering AND MCQ:
        - Randomly choose based on visual_probability
    If the competency only supports visual:
        - Return visual skeleton
    If the competency only supports MCQ:
        - Return MCQ skeleton
    
    Args:
        competency_text: Full competency text from MATATAG curriculum
        grade: Grade level 1-10
        difficulty: Scalar difficulty 0.0-1.5+
        seed: Random seed for reproducibility
        content_area: Optional content area override
        quarter: Optional quarter override
        visual_probability: Probability (0-1) of choosing visual when both available
    
    Returns:
        Skeleton dict with 'is_visual' flag indicating which type was chosen
    """
    if seed is None:
        seed = random.randint(10000, 99999)
    
    rng = random.Random(seed)
    
    # Check if visual skeleton is available for this competency
    visual_match = get_visual_type_for_competency(competency_text, grade)
    
    if visual_match:
        visual_type = visual_match["visual_type"]
        mcq_fallback = visual_match["mcq_fallback"]
        
        # Decide whether to use visual or MCQ
        use_visual = True
        if mcq_fallback:
            # Both options available - randomly choose
            use_visual = rng.random() < visual_probability
        
        if use_visual:
            # Generate visual skeleton
            try:
                # Import here to avoid circular imports
                from backend.app import visual_skeletons

                visual_result = visual_skeletons.get_visual_skeleton(
                    visual_type=visual_type,
                    grade=grade,
                    seed=seed,
                    difficulty=int(difficulty * 2) + 1,  # Convert 0-1 to 1-3
                    competency_text=competency_text,
                    axis_values=axis_values,
                )
                
                stem_text = visual_result.get("stem_template") or visual_result.get("stem") or competency_text
                
                # Get context for content area and quarter
                context = get_curriculum_context(competency_text)
                if content_area is None:
                    content_area = context.get("strand", "Number and Algebra")
                if quarter is None:
                    quarter = context.get("quarter", 1)
                
                return {
                    "skeleton_id": visual_result.get("skeleton_id", f"vis_{grade}_{seed}"),
                    "competency_text": competency_text,
                    "grade": grade,
                    "content_area": content_area,
                    "quarter": quarter,
                    "generator_type": "visual",
                    
                    "stem": stem_text,
                    "correct_answer": str(visual_result.get("correct_answer", "")),
                    "correct_key": visual_result.get("correct_key", "A"),
                    "options": visual_result.get("options", {}),
                    
                    "visual_type": visual_type,
                    "visual_params": visual_result.get("visual_params", {}),
                    "question_mode": visual_result.get("question_mode", "interactive"),
                    "all_traps": visual_result.get("all_traps", {}),
                    
                    "is_visual": True,
                    "seed": seed,
                    "difficulty_scalar": difficulty,
                }
            except Exception as e:
                # Visual generation failed - fall back to MCQ if possible
                if mcq_fallback:
                    pass  # Will fall through to MCQ generation below
                else:
                    raise Exception(f"Visual generation failed and no MCQ fallback: {e}")
    
    # Generate MCQ skeleton (either no visual available, or randomly chose MCQ, or visual failed)
    mcq_skeleton = get_matatag_skeleton(
        competency_text=competency_text,
        grade=grade,
        difficulty=difficulty,
        seed=seed,
        content_area=content_area,
        quarter=quarter,
        axis_values=axis_values,
    )
    mcq_skeleton["is_visual"] = False
    return mcq_skeleton


def _apply_axis_overrides(dimensions: Dict[str, Any], axis_values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate UI axis selections into dimension-dict overrides so that generators
    actually honour the chosen difficulty option.

    axis_values keys come from axes_catalog.py (e.g. 'regrouping', 'direction', 'range').
    dimensions keys come from matatag_dimensions.py (e.g. 'regrouping_required', 'max_number').
    """
    d = dict(dimensions)  # shallow copy — don't mutate caller's dict

    # ── regrouping ────────────────────────────────────────────────────────────
    rg = axis_values.get("regrouping")
    if rg == "none":
        d["regrouping_required"] = False
        d["regrouping_probability"] = 0.0
        d["regrouping_type"] = "none"
    elif rg == "ones":
        d["regrouping_required"] = True
        d["regrouping_probability"] = 1.0
        d["regrouping_type"] = "ones"
    elif rg == "tens":
        d["regrouping_required"] = True
        d["regrouping_probability"] = 1.0
        d["regrouping_type"] = "tens"
    elif rg == "double":
        d["regrouping_required"] = True
        d["regrouping_probability"] = 1.0
        d["regrouping_type"] = "double"

    # ── structure (blank position in equation) ────────────────────────────────
    st = axis_values.get("structure")
    if st == "result_unknown":
        d["structure"] = "result_unknown"
    elif st == "change_unknown":
        d["structure"] = "change_unknown"
    elif st == "start_unknown":
        d["structure"] = "start_unknown"
    elif st == "factor_unknown":
        d["structure"] = "factor_unknown"
        d["include_remainder"] = 0.0   # factor_unknown requires clean division
    elif st == "divisor_unknown":
        d["structure"] = "divisor_unknown"
        d["include_remainder"] = 0.0   # divisor_unknown requires clean division

    # ── blank_position (alias used by some concepts) ──────────────────────────
    bp = axis_values.get("blank_position")
    if bp and "structure" not in axis_values:
        d["structure"] = bp + "_unknown" if not bp.endswith("_unknown") else bp

    # ── number_type ───────────────────────────────────────────────────────────
    nt = axis_values.get("number_type")
    if nt == "round":
        d["number_type"] = "round"
    elif nt == "non_round":
        d["number_type"] = "non_round"
    elif nt == "single_digit":
        d["number_type"] = "single_digit"
        d["operand_max"] = min(d.get("operand_max", 9), 9)
    elif nt == "multi_digit":
        d["number_type"] = "multi_digit"
        d["operand_max"] = max(d.get("operand_max", 10), 10)

    # ── range ─────────────────────────────────────────────────────────────────
    range_map = {
        "0_20": 20, "0_100": 100, "0_1000": 1000,
        "up_to_20": 20, "up_to_100": 100, "up_to_1000": 1000, "up_to_10000": 10000,
        "1_to_20": 20, "21_to_100": 100, "101_to_1000": 1000, "1001_to_10000": 10000,
        "1st_to_10th": 10, "11th_to_20th": 20, "21st_to_100th": 100,
    }
    rv = axis_values.get("range")
    if rv and rv in range_map:
        d["max_number"] = range_map[rv]
        d["operand_max"] = range_map[rv]

    # ── direction ─────────────────────────────────────────────────────────────
    dv = axis_values.get("direction")
    if dv == "forward":
        d["direction"] = "forward"
        d["direction_complexity"] = 0.0   # 0 = always forward
    elif dv == "backward":
        d["direction"] = "backward"
        d["direction_complexity"] = 1.0   # force backward path
    elif dv in ("numeral_to_word", "word_to_numeral", "numeral_to_expanded"):
        d["direction"] = dv  # pass through for number_reading generator

    # ── skip_interval ─────────────────────────────────────────────────────────
    si = axis_values.get("skip_interval")
    skip_map = {"by_1": 1, "by_2_5_10": 5, "by_20_50_100": 20}
    if si and si in skip_map:
        d["skip_interval"] = skip_map[si]

    # ── digit_count ───────────────────────────────────────────────────────────
    dc = axis_values.get("digit_count")
    digit_max = {"2_digit": 99, "3_digit": 999, "4_digit": 9999}
    if dc and dc in digit_max:
        d["operand_max"] = digit_max[dc]

    # ── amount_range (peso) ───────────────────────────────────────────────────
    ar = axis_values.get("amount_range")
    amount_max = {"up_to_100": 100, "up_to_1000": 1000, "up_to_10000": 10000}
    if ar and ar in amount_max:
        d["amount_max"] = amount_max[ar]
        d["amount_range"] = ar   # Pass to visual generator for range enforcement

    # ── denomination_type ─────────────────────────────────────────────────────
    dt = axis_values.get("denomination_type")
    if dt:
        d["denomination_type"] = dt

    # ── fraction_type ─────────────────────────────────────────────────────────
    ft = axis_values.get("fraction_type")
    ftype_map = {"unit_fraction": 0.0, "similar_proper": 0.3, "mixed_number": 0.8}
    if ft and ft in ftype_map:
        d["fraction_type_index"] = ftype_map[ft]
        d["fraction_type"] = ft

    # ── precision (time/rounding) ─────────────────────────────────────────────
    pv = axis_values.get("precision")
    if pv:
        d["precision"] = pv
        time_granularity = {
            "hour": 60, "half_hour": 30, "quarter_hour": 15,
            "five_minutes": 5, "one_minute": 1,
        }
        if pv in time_granularity:
            d["time_granularity"] = time_granularity[pv]

    # ── mode (clock: read vs set) ─────────────────────────────────────────────
    mv = axis_values.get("mode")
    if mv:
        d["clock_mode"] = mv

    # ── include_ampm ──────────────────────────────────────────────────────────
    ampm = axis_values.get("include_ampm")
    if ampm == "with_ampm":
        d["include_ampm"] = True
    elif ampm == "no_ampm":
        d["include_ampm"] = False

    # ── include_zeros ─────────────────────────────────────────────────────────
    iz = axis_values.get("include_zeros")
    if iz == "with_zeros":
        d["include_zeros"] = True
    elif iz == "no_zeros":
        d["include_zeros"] = False

    # ── task_type ─────────────────────────────────────────────────────────────
    ttv = axis_values.get("task_type")
    if ttv:
        d["task_type"] = ttv

    # ── remainder ─────────────────────────────────────────────────────────────
    rem = axis_values.get("remainder")
    if rem == "none":
        d["include_remainder"] = 0.0
    elif rem == "with_remainder":
        d["include_remainder"] = 1.0

    # ── measurement_type ──────────────────────────────────────────────────────
    mt = axis_values.get("measurement_type")
    if mt:
        d["measurement_type"] = mt

    # ── scale / scale_type ────────────────────────────────────────────────────
    sv = axis_values.get("scale") or axis_values.get("scale_type")
    scale_val = {"scale_2": 2, "scale_5": 5, "scale_10": 10, "scale_20": 20}
    if sv and sv in scale_val:
        d["y_scale"] = scale_val[sv]

    # ── pattern_type ──────────────────────────────────────────────────────────
    pt = axis_values.get("pattern_type")
    if pt:
        d["pattern_type"] = pt

    # ── proximity ─────────────────────────────────────────────────────────────
    pxv = axis_values.get("proximity")
    if pxv == "close_together":
        d["proximity"] = "close"
    elif pxv == "far_apart":
        d["proximity"] = "far"

    # ── boundary_proximity ────────────────────────────────────────────────────
    bpv = axis_values.get("boundary_proximity")
    if bpv:
        d["boundary_proximity"] = bpv

    return d


def get_matatag_skeleton(
    competency_text: str,
    grade: int,
    difficulty: float = 0.5,
    seed: Optional[int] = None,
    content_area: Optional[str] = None,
    quarter: Optional[int] = None,
    axis_values: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a complete MCQ skeleton for a MATATAG competency.
    
    Args:
        competency_text: Full competency text from MATATAG curriculum
        grade: Grade level 1-10
        difficulty: Scalar difficulty 0.0-1.5+ (default 0.5 = medium)
        seed: Random seed for reproducibility
        content_area: Optional content area override
        quarter: Optional quarter override
    
    Returns:
        Complete skeleton dict with stem, options, correct_answer, analytics data
    """
    if seed is None:
        seed = random.randint(10000, 99999)
    
    # Extract constraints from competency text
    constraints = extract_constraints(competency_text)
    
    # Get curriculum context (for neighboring nodes)
    context = get_curriculum_context(competency_text)
    if content_area is None:
        content_area = context.get("strand", "Number and Algebra")
    if quarter is None:
        quarter = context.get("quarter", 1)
    
    # Route to appropriate generator
    generator_type = _route_competency(competency_text, grade)

    # Get dimension values for this difficulty
    dimensions = get_dimension_values(generator_type, difficulty, constraints)

    # Override dimensions with explicit axis selections from the UI
    if axis_values:
        dimensions = _apply_axis_overrides(dimensions, axis_values)

    for attempt in range(MAX_RETRIES):
        actual_seed = seed + attempt * 1000
        rng = random.Random(actual_seed)
        
        try:
            # Generate the skeleton
            skeleton = _generate_skeleton(
                generator_type, competency_text, grade, dimensions, constraints, rng
            )
            
            if _validate_skeleton(skeleton):
                # Build skeleton ID
                skeleton_id = f"mat_{grade}_{GENERATOR_CODES[generator_type]}_{actual_seed}"
                
                return {
                    # Identification
                    "skeleton_id": skeleton_id,
                    "competency_text": competency_text,
                    "grade": grade,
                    "content_area": content_area,
                    "quarter": quarter,
                    "generator_type": generator_type,
                    
                    # Problem content
                    "stem": skeleton["stem"],
                    "correct_answer": skeleton["correct_answer"],
                    "options": skeleton["options"],
                    
                    # For regeneration
                    "variables": skeleton.get("variables", {}),
                    "seed": actual_seed,
                    
                    # Difficulty
                    "difficulty_scalar": difficulty,
                    "difficulty_dimensions": dimensions,
                    "constraints_extracted": constraints,
                    
                    # Analytics (populated after student answers)
                    "analytics": {
                        "time_to_answer_ms": None,
                        "trap_triggered": None,
                        "is_correct": None,
                    },
                }
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise Exception(f"Failed to generate {generator_type} skeleton after {MAX_RETRIES} attempts: {e}")
            continue
    
    raise Exception(f"Could not generate valid {generator_type} skeleton")


def regenerate_matatag_skeleton(skeleton_id: str) -> Dict[str, Any]:
    """
    Regenerate a skeleton from its ID (for stateless validation).
    
    Args:
        skeleton_id: Skeleton ID like "mat_3_ar_12345"
    
    Returns:
        Regenerated skeleton dict
    """
    # Parse skeleton ID: mat_{grade}_{type_code}_{seed}
    parts = skeleton_id.split("_")
    if len(parts) != 4 or parts[0] != "mat":
        raise ValueError(f"Invalid skeleton ID format: {skeleton_id}")
    
    grade = int(parts[1])
    generator_code = parts[2]
    seed = int(parts[3])
    
    if generator_code not in GENERATOR_CODES_REVERSE:
        raise ValueError(f"Unknown generator code: {generator_code}")
    
    generator_type = GENERATOR_CODES_REVERSE[generator_code]
    
    # Create a generic competency text based on generator type
    # This enables regeneration without stored competency text
    generic_competencies = {
        "counting": "Count objects and numbers",
        "place_value": "Determine the place value of digits",
        "arithmetic": "Perform arithmetic operations",
        "fractions": "Work with fractions",
        "decimals": "Work with decimal numbers",
        "ratios_percent": "Calculate ratios and percentages",
        "algebra": "Solve algebraic expressions",
        "geometry_props": "Identify geometric properties",
        "measurement": "Measure and calculate units",
        "data_probability": "Analyze data and probability",
        "conceptual": "Understand mathematical concepts",
    }
    
    competency_text = generic_competencies.get(generator_type, "General math problem")
    
    # Use the standard generator to regenerate with the same seed
    rng = random.Random(seed)
    
    # Get dimension values for medium difficulty
    constraints = extract_constraints(competency_text)
    dimensions = get_dimension_values(generator_type, 0.5, constraints)
    
    try:
        skeleton = _generate_skeleton(
            generator_type, competency_text, grade, dimensions, constraints, rng
        )
        
        # Build complete skeleton response
        return {
            "skeleton_id": skeleton_id,
            "competency_text": competency_text,
            "grade": grade,
            "generator_type": generator_type,
            "stem": skeleton["stem"],
            "correct_answer": skeleton["correct_answer"],
            "options": skeleton["options"],
            "variables": skeleton.get("variables", {}),
            "seed": seed,
            "is_visual": False,  # Regenerated skeletons are MCQ
            "question_mode": "mcq",
        }
    except Exception as e:
        raise ValueError(f"Could not regenerate skeleton {skeleton_id}: {e}")


def validate_matatag_answer(
    skeleton_id: str,
    student_answer: str,
    correct_answer: str,
    options: Dict[str, Dict],
) -> Dict[str, Any]:
    """
    Validate a student's answer and identify any triggered trap.
    
    Args:
        skeleton_id: Skeleton ID
        student_answer: Student's selected answer
        correct_answer: The correct answer
        options: Options dict with trap info
    
    Returns:
        {
            "is_correct": bool,
            "trap_triggered": str or None,
            "trap_info": dict or None
        }
    """
    is_correct = student_answer.strip() == correct_answer.strip()
    trap_triggered = None
    trap_info = None
    
    if not is_correct:
        # Find which trap was triggered
        for key, opt in options.items():
            if opt["value"].strip() == student_answer.strip() and opt.get("trap"):
                trap_triggered = opt["trap"]
                trap_info = TRAP_CATALOG.get(trap_triggered)
                break
    
    return {
        "is_correct": is_correct,
        "trap_triggered": trap_triggered,
        "trap_info": trap_info,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTING
# ═══════════════════════════════════════════════════════════════════════════════

def _route_competency(competency_text: str, grade: int) -> str:
    """
    Route a competency to the appropriate generator based on text patterns.
    """
    for route in COMPETENCY_ROUTES:
        if grade not in route["grades"]:
            continue
        if re.search(route["pattern"], competency_text):
            return route["generator"]
    
    return "conceptual"  # Fallback


def _generate_skeleton(
    generator_type: str,
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Route to the appropriate generator function.
    """
    generators = {
        "counting": _gen_counting,
        "place_value": _gen_place_value,
        "arithmetic": _gen_arithmetic,
        "fractions": _gen_fractions,
        "decimals": _gen_decimals,
        "ratios_percent": _gen_ratios_percent,
        "algebra": _gen_algebra,
        "geometry_props": _gen_geometry_props,
        "measurement": _gen_measurement,
        "data_probability": _gen_data_probability,
        "conceptual": _gen_conceptual,
        "compose_decompose": _gen_compose_decompose,
        "compare_order": _gen_compare_order,
    }
    
    gen_func = generators.get(generator_type, _gen_conceptual)
    return gen_func(competency_text, grade, dimensions, constraints, rng)


def _validate_skeleton(skeleton: Dict[str, Any]) -> bool:
    """
    Validate that a skeleton is well-formed.
    """
    required = ["stem", "correct_answer", "options"]
    for key in required:
        if key not in skeleton:
            return False
    
    options = skeleton["options"]
    if len(options) < 4:
        return False
    
    # Check all options are unique
    values = [opt["value"] for opt in options.values()]
    if len(values) != len(set(values)):
        return False
    
    # Check correct answer is in options
    correct = skeleton["correct_answer"]
    if not any(opt["value"] == correct and opt.get("trap") is None for opt in options.values()):
        return False
    
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _shuffle_options(options_list: List[Tuple[str, Optional[str]]], rng: random.Random) -> Dict[str, Dict]:
    """
    Shuffle options and assign A, B, C, D keys.
    Automatically deduplicates — keeps only unique values.
    If fewer than 4 unique options remain after dedup, pads with offset values.
    
    Args:
        options_list: List of (value, trap_name_or_None) tuples
        rng: Random number generator
    
    Returns:
        Dict with keys A, B, C, D
    """
    # Deduplicate while preserving the correct answer (trap=None)
    seen = set()
    unique_options = []
    for value, trap in options_list:
        val_str = str(value)
        if val_str not in seen:
            seen.add(val_str)
            unique_options.append((val_str, trap))
    
    # Pad if we lost options to deduplication
    while len(unique_options) < 4:
        # Try to generate a filler value that's not a duplicate
        # Find the correct answer to base offsets on
        correct_val = next((v for v, t in unique_options if t is None), unique_options[0][0])
        try:
            base = int(correct_val)
            for offset in [1, -1, 2, -2, 3, -3, 5, -5, 10, -10]:
                filler = str(base + offset)
                if filler not in seen and int(filler) > 0:
                    seen.add(filler)
                    unique_options.append((filler, "padding_trap"))
                    break
            else:
                unique_options.append((str(base + rng.randint(1, 20)), "padding_trap"))
        except (ValueError, TypeError):
            unique_options.append((f"{correct_val}_alt", "padding_trap"))
        
    rng.shuffle(unique_options)
    keys = ["A", "B", "C", "D"]
    result = {}
    for i, (value, trap) in enumerate(unique_options[:4]):
        result[keys[i]] = {"value": str(value), "trap": trap}
    return result


def _format_number(n: int) -> str:
    """Format a number with proper spacing for readability (no commas for elementary)."""
    return str(n)


def _ordinal(n: int) -> str:
    """Convert number to ordinal string (1st, 2nd, 3rd, etc.)."""
    if 11 <= n % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _simplify_fraction(n: int, d: int) -> Tuple[int, int]:
    """Simplify a fraction to lowest terms."""
    g = gcd(n, d)
    return (n // g, d // g)


def _lcm(a: int, b: int) -> int:
    """Compute least common multiple."""
    return abs(a * b) // gcd(a, b)


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATOR: COUNTING
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_counting(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Generate counting problems.
    
    Types:
    - What comes after N?
    - What comes before N?
    - Skip counting: N, N+k, N+2k, ?
    - Ordinal: What is the Nth item?
    """
    max_num = dimensions.get("max_number", 100)
    skip_interval = dimensions.get("skip_interval", 1)
    direction_complexity = dimensions.get("direction_complexity", 0.0)
    ordinal_max = dimensions.get("ordinal_max", 10)
    direction_override = dimensions.get("direction")
    pattern_type_override = dimensions.get("pattern_type")

    text_lower = competency_text.lower()

    if "ordinal" in text_lower:
        return _gen_counting_ordinal(ordinal_max, rng)
    elif any(w in text_lower for w in ["pattern", "next term", "increasing", "decreasing", "sequence"]):
        return _gen_counting_pattern(max_num, rng, text_lower, pattern_type=pattern_type_override)
    elif "skip" in text_lower or "by 2" in text_lower or "by 5" in text_lower or "by 10" in text_lower:
        if skip_interval == 1:
            return _gen_counting_after(max_num, rng) if direction_override != "backward" else _gen_counting_before(max_num, rng)
        return _gen_counting_skip(max_num, skip_interval, rng)
    else:
        # Direction override takes priority over text detection
        if direction_override == "backward":
            return _gen_counting_before(max_num, rng)
        elif direction_override == "forward":
            return _gen_counting_after(max_num, rng)
        # Fall back to text-based detection
        elif "1 less" in text_lower:
            return _gen_counting_before(max_num, rng)
        elif rng.random() < direction_complexity:
            return _gen_counting_before(max_num, rng)
        return _gen_counting_after(max_num, rng)


def _gen_counting_after(max_num: int, rng: random.Random) -> Dict[str, Any]:
    """What number comes after N?"""
    n = rng.randint(1, max(1, max_num - 1))
    correct = n + 1
    
    traps = [
        (n - 1, "cnt_prev"),      # Previous number
        (n + 2, "cnt_skip"),      # Skipped one
        (n, "cnt_back"),          # Same number
    ]
    
    options_list = [(correct, None)] + traps
    
    return {
        "stem": f"What number comes after {n}?",
        "correct_answer": str(correct),
        "options": _shuffle_options(options_list, rng),
        "variables": {"n": n, "correct": correct},
    }


def _gen_counting_before(max_num: int, rng: random.Random) -> Dict[str, Any]:
    """What number comes before N?"""
    n = rng.randint(2, max_num)
    correct = n - 1
    
    traps = [
        (n + 1, "cnt_prev"),      # Added instead of subtracted
        (n - 2, "cnt_skip"),      # Went back 2
        (n, "cnt_back"),          # Same number
    ]
    
    options_list = [(correct, None)] + traps
    
    return {
        "stem": f"What number comes before {n}?",
        "correct_answer": str(correct),
        "options": _shuffle_options(options_list, rng),
        "variables": {"n": n, "correct": correct},
    }


def _gen_counting_skip(max_num: int, skip_interval: int, rng: random.Random) -> Dict[str, Any]:
    """Skip counting: fill in the next number."""
    if isinstance(skip_interval, list):
        skip = rng.choice(skip_interval)
    else:
        skip = skip_interval if skip_interval > 1 else rng.choice([2, 5, 10])
    
    # Generate starting point
    max_start = max(skip, max_num - 4 * skip)
    start = rng.randint(0, max_start // skip) * skip
    
    # Generate sequence with 3 visible terms, 4th is blank
    seq = [start + i * skip for i in range(4)]
    correct = seq[3]
    
    traps = [
        (seq[2] + 1, "cnt_wrong_interval"),    # Used +1 instead
        (seq[2] + skip * 2, "cnt_skip"),       # Skipped one term
        (seq[2] - skip, "cnt_back"),           # Went backwards
    ]
    
    options_list = [(correct, None)] + traps
    
    return {
        "stem": f"What comes next? {seq[0]}, {seq[1]}, {seq[2]}, ___",
        "correct_answer": str(correct),
        "options": _shuffle_options(options_list, rng),
        "variables": {"sequence": seq, "skip": skip, "correct": correct},
    }


def _gen_counting_ordinal(ordinal_max: int, rng: random.Random) -> Dict[str, Any]:
    """Ordinal number questions."""
    position = rng.randint(1, min(ordinal_max, 20))
    
    # Generate a simple list context
    items = ["apple", "banana", "orange", "grape", "mango", "pear", "peach", "plum", "cherry", "melon"]
    items = items * 3  # Extend if needed
    
    correct = items[position - 1]
    
    # Traps: adjacent positions and count confusion
    trap_positions = [
        (position - 1 if position > 1 else position + 2, "cnt_ord_off"),
        (position + 1 if position < len(items) else position - 2, "cnt_ord_off"),
    ]
    
    traps = []
    for pos, trap_name in trap_positions:
        if 1 <= pos <= len(items) and items[pos - 1] != correct:
            traps.append((items[pos - 1], trap_name))
    
    # Add a distractor
    other = rng.choice([i for i in items[:10] if i != correct and i not in [t[0] for t in traps]])
    traps.append((other, "cnt_card_ord"))
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"In a row of fruits, what is the {_ordinal(position)} item?\nFruits: {', '.join(items[:max(10, position+2)])}",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"position": position, "correct": correct},
    }


def _gen_counting_pattern(max_num: int, rng: random.Random, text_lower: str,
                           pattern_type: str = None) -> Dict[str, Any]:
    """Generate number pattern / sequence problems, honouring pattern_type axis."""
    # Explicit axis override takes precedence over text detection
    if pattern_type == "arithmetic_increasing":
        is_decreasing = False
        ptype = "arithmetic"
    elif pattern_type == "arithmetic_decreasing":
        is_decreasing = True
        ptype = "arithmetic"
    else:
        is_decreasing = "decreasing" in text_lower or "decreas" in text_lower
        is_create = "create" in text_lower

        # Choose pattern type
        pattern_types = ["arithmetic", "skip_count", "doubling"]
        if max_num <= 100:
            pattern_types = ["arithmetic", "skip_count"]
        ptype = rng.choice(pattern_types)
    
    if ptype == "arithmetic":
        # Constant difference pattern
        if is_decreasing:
            step = -rng.choice([2, 3, 5, 10, 20])
            start = rng.randint(abs(step) * 5, min(max_num, abs(step) * 10))
        else:
            step = rng.choice([2, 3, 4, 5, 10, 20, 25, 50])
            start = rng.randint(0, min(max_num // 4, 100))
        
        seq = [start + i * step for i in range(5)]
        # Ensure all non-negative
        if any(x < 0 for x in seq):
            step = abs(step)
            seq = [start + i * step for i in range(5)]
        
        correct = seq[4]
        visible = seq[:4]
        
        stems = [
            f"What comes next? {visible[0]}, {visible[1]}, {visible[2]}, {visible[3]}, ___",
            f"Find the next number in the pattern: {', '.join(map(str, visible))}, ___",
            f"Continue the pattern: {', '.join(map(str, visible))}, ___",
        ]
        traps = [
            (visible[3] + 1 if step > 0 else visible[3] - 1, "cnt_off_by_one"),
            (visible[3] + step * 2, "cnt_skipped_one"),
            (visible[3] - step, "cnt_wrong_direction"),
        ]
    
    elif ptype == "skip_count":
        # Skip counting pattern (same as arithmetic but framed differently)
        skip = rng.choice([2, 5, 10, 20, 50, 100])
        start = rng.randint(0, skip * 3) * skip // skip * skip  # Align to skip
        seq = [start + i * skip for i in range(5)]
        
        if is_decreasing:
            seq = list(reversed(seq))
        
        correct = seq[4]
        visible = seq[:4]
        
        stems = [
            f"What comes next? {', '.join(map(str, visible))}, ___",
            f"Count by {skip}s: {', '.join(map(str, visible))}, ___",
            f"The pattern is: {', '.join(map(str, visible))}. What is next?",
        ]
        step = skip if not is_decreasing else -skip
        traps = [
            (visible[3] + 1, "cnt_wrong_interval"),
            (visible[3] + step * 2, "cnt_skipped_one"),
            (visible[3] - step, "cnt_wrong_direction"),
        ]
    
    else:  # doubling
        start = rng.choice([2, 3, 5])
        seq = [start * (2 ** i) for i in range(5)]
        correct = seq[4]
        visible = seq[:4]
        
        stems = [
            f"What comes next? {', '.join(map(str, visible))}, ___",
            f"Find the pattern: {', '.join(map(str, visible))}, ___",
            f"Each number doubles. Continue: {', '.join(map(str, visible))}, ___",
        ]
        traps = [
            (visible[3] + visible[3] // 2, "cnt_wrong_rule"),
            (visible[3] + visible[2], "cnt_added_prev"),
            (visible[3] * 3, "cnt_tripled"),
        ]
    
    stem = rng.choice(stems)
    options_list = [(str(correct), None)] + [(str(t), name) for t, name in traps[:3]]
    
    return {
        "stem": stem,
        "correct_answer": str(correct),
        "options": _shuffle_options(options_list, rng),
        "variables": {"sequence": seq, "sub_type": "pattern"},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATOR: PLACE VALUE
# ═══════════════════════════════════════════════════════════════════════════════

PLACE_NAMES = ["ones", "tens", "hundreds", "thousands", "ten thousands", "hundred thousands"]
PLACE_VALUES = [1, 10, 100, 1000, 10000, 100000]


def _gen_place_value(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Generate place value problems.
    
    Types:
    - What digit is in the X place?
    - What is the value of the digit N?
    - Write in expanded form
    """
    digit_count = dimensions.get("digit_count", 3)
    target_place = min(dimensions.get("target_place", 1), digit_count - 1)
    include_zeros = dimensions.get("include_zeros", 0.0)
    question_type = dimensions.get("question_type", 0.5)
    # max_number_cap bounds all number generation within competency range
    max_number_cap = dimensions.get("max_number") or dimensions.get("operand_max")
    
    # Determine question type first
    text_lower = competency_text.lower()
    
    # Rounding branch — respect precision axis override
    precision_override = dimensions.get("precision")
    if "round" in text_lower:
        return _gen_pv_round(digit_count, rng, text_lower, precision_override=precision_override)

    # Read/write in words branch
    direction_override = dimensions.get("direction")  # from axis selection
    if "read and write" in text_lower or "in words" in text_lower or "write numerals" in text_lower:
        return _gen_pv_read_write(digit_count, rng, max_number_cap=max_number_cap, direction_override=direction_override)
    
    is_value_question = "value of" in text_lower or (question_type > 0.3 and question_type <= 0.7)
    is_expanded_question = "expanded form" in text_lower or question_type > 0.7

    # If include_zeros is explicitly requested, use expanded form (zeros in value questions are confusing)
    if include_zeros is True:
        is_value_question = False
        is_expanded_question = True
    
    # For "value of digit" questions, ensure all digits are unique to avoid ambiguity
    # e.g., "In 4575, what is the VALUE of the digit 5?" is confusing (5 appears twice)
    if is_value_question:
        # Generate number with unique digits
        for attempt in range(20):
            min_val = 10 ** (digit_count - 1)
            max_val = 10 ** digit_count - 1
            if max_number_cap:
                max_val = min(max_val, int(max_number_cap))
                min_val = min(min_val, max_val)
            number = rng.randint(min_val, max_val)
            digits = str(number)
            
            # Check if all digits are unique (no duplicates)
            if len(set(digits)) == len(digits):
                break
        else:
            # Fallback: construct a number with unique digits
            available_digits = list(range(1, 10))  # Start with 1-9 (no leading zero)
            rng.shuffle(available_digits)
            first_digit = available_digits.pop()
            
            remaining = [0] + list(range(1, 10))
            remaining.remove(first_digit)
            rng.shuffle(remaining)
            
            chosen_digits = [first_digit] + remaining[:digit_count - 1]
            number = int(''.join(str(d) for d in chosen_digits))
            digits = str(number)
    else:
        # For other question types, regular generation is fine
        min_val = 10 ** (digit_count - 1)
        max_val = 10 ** digit_count - 1
        if max_number_cap:
            max_val = min(max_val, int(max_number_cap))
            min_val = min(min_val, max_val)
        number = rng.randint(min_val, max_val)

        # Apply include_zeros: True=always insert zero, 0.0=never, float=probability
        include_zeros_val = float(include_zeros) if include_zeros is not None else 0.0
        if include_zeros_val >= 1.0 or (include_zeros_val > 0 and rng.random() < include_zeros_val):
            if digit_count >= 3:
                digits_list = list(str(number))
                zero_pos = rng.randint(1, len(digits_list) - 2)  # Not first or last
                digits_list[zero_pos] = '0'
                candidate = int(''.join(digits_list))
                if candidate >= min_val:
                    number = candidate

        digits = str(number)

    # Determine question type and generate
    if is_expanded_question:
        return _gen_pv_expanded(number, str(number), rng)
    elif is_value_question:
        return _gen_pv_value(number, digits, target_place, digit_count, rng)
    else:
        return _gen_pv_digit(number, digits, target_place, digit_count, rng)


def _gen_pv_digit(number: int, digits: str, target_place: int, digit_count: int, rng: random.Random) -> Dict[str, Any]:
    """What digit is in the X place?"""
    # Ensure target_place is valid
    target_place = min(target_place, digit_count - 1)
    
    # Get digit at target place (from right)
    digit_index = len(digits) - 1 - target_place
    correct_digit = int(digits[digit_index])
    place_name = PLACE_NAMES[target_place]
    
    # Build unique traps
    used_values = {correct_digit}
    traps = []
    
    # Adjacent place digits (one place left and right)
    if target_place > 0:
        adj_idx = len(digits) - target_place  # Next place to the right
        if 0 <= adj_idx < len(digits):
            adj_digit = int(digits[adj_idx])
            if adj_digit not in used_values:
                traps.append((adj_digit, "pv_adj_place"))
                used_values.add(adj_digit)
    
    if target_place < len(digits) - 1:
        adj_idx = len(digits) - 2 - target_place  # Next place to the left
        if 0 <= adj_idx < len(digits):
            adj_digit = int(digits[adj_idx])
            if adj_digit not in used_values:
                traps.append((adj_digit, "pv_adj_place"))
                used_values.add(adj_digit)
    
    # Value instead of digit (common misconception)
    value = correct_digit * PLACE_VALUES[target_place]
    if value not in used_values and value != correct_digit and value < 10000:
        traps.append((value, "pv_val_dig"))
        used_values.add(value)
    
    # Fill remaining traps with other digits from the number
    other_digits = [int(d) for d in digits if int(d) not in used_values]
    rng.shuffle(other_digits)
    for d in other_digits:
        if len(traps) >= 3:
            break
        traps.append((d, "pv_other_dig"))
        used_values.add(d)
    
    # Ensure we have enough traps with random digits
    while len(traps) < 3:
        trap_val = rng.randint(0, 9)
        if trap_val not in used_values:
            traps.append((trap_val, "pv_random"))
            used_values.add(trap_val)
    
    options_list = [(correct_digit, None)] + traps[:3]
    
    return {
        "stem": f"In {number}, what digit is in the {place_name} place?",
        "correct_answer": str(correct_digit),
        "options": _shuffle_options(options_list, rng),
        "variables": {"number": number, "target_place": target_place, "correct": correct_digit},
    }


def _gen_pv_value(number: int, digits: str, target_place: int, digit_count: int, rng: random.Random) -> Dict[str, Any]:
    """What is the VALUE of the digit N in this number?"""
    target_place = min(target_place, digit_count - 1)
    digit_index = len(digits) - 1 - target_place
    digit = int(digits[digit_index])
    
    # Handle zero digit - pick a different place
    if digit == 0:
        for i, d in enumerate(digits):
            if d != '0':
                digit_index = i
                target_place = len(digits) - 1 - i
                digit = int(d)
                break
    
    place_name = PLACE_NAMES[target_place]
    correct_value = digit * PLACE_VALUES[target_place]
    
    # Build unique traps
    used_values = {correct_value}
    traps = []
    
    # Trap 1: Gave digit instead of value
    if digit not in used_values:
        traps.append((digit, "pv_dig_val"))
        used_values.add(digit)
    
    # Trap 2: One place too high
    too_high = correct_value * 10
    if too_high not in used_values:
        traps.append((too_high, "pv_place_shift"))
        used_values.add(too_high)
    
    # Trap 3: One place too low
    too_low = correct_value // 10 if correct_value >= 10 else 0
    if too_low not in used_values and too_low > 0:
        traps.append((too_low, "pv_place_shift"))
        used_values.add(too_low)
    
    # Fill remaining traps with plausible wrong values
    while len(traps) < 3:
        # Try adjacent digit values
        candidates = [
            digit + 1 if digit < 9 else digit - 1,
            (digit + 1) * PLACE_VALUES[target_place],
            (digit - 1) * PLACE_VALUES[target_place] if digit > 1 else 2 * PLACE_VALUES[target_place],
            correct_value + PLACE_VALUES[target_place],
            correct_value - PLACE_VALUES[target_place] if correct_value > PLACE_VALUES[target_place] else correct_value + 2 * PLACE_VALUES[target_place],
        ]
        for candidate in candidates:
            if candidate not in used_values and candidate > 0:
                traps.append((candidate, "pv_wrong_val"))
                used_values.add(candidate)
                break
        else:
            # Fallback: random nearby value
            fallback = correct_value + rng.choice([1, 10, -1, 11, 100])
            while fallback in used_values or fallback <= 0:
                fallback = correct_value + rng.randint(1, 100)
            traps.append((fallback, "pv_wrong_val"))
            used_values.add(fallback)
    
    options_list = [(correct_value, None)] + traps[:3]
    
    return {
        "stem": f"In {number}, what is the VALUE of the digit {digit}?",
        "correct_answer": str(correct_value),
        "options": _shuffle_options(options_list, rng),
        "variables": {"number": number, "digit": digit, "correct": correct_value},
    }


def _gen_pv_expanded(number: int, digits: str, rng: random.Random) -> Dict[str, Any]:
    """Write in expanded form."""
    # Build correct expanded form
    terms = []
    for i, d in enumerate(digits):
        if d != '0':
            place = len(digits) - 1 - i
            value = int(d) * PLACE_VALUES[place]
            terms.append(str(value))
    
    correct = " + ".join(terms)
    
    # Build unique traps
    used_values = {correct}
    traps = []
    
    # Trap 1: Include zero terms (if number has zeros)
    if '0' in digits:
        terms_with_zero = []
        for i, d in enumerate(digits):
            place = len(digits) - 1 - i
            value = int(d) * PLACE_VALUES[place]
            terms_with_zero.append(str(value))
        zero_trap = " + ".join(terms_with_zero)
        if zero_trap not in used_values:
            traps.append((zero_trap, "pv_zero_exp"))
            used_values.add(zero_trap)
    
    # Trap 2: Reversed order (only if different from correct)
    reversed_exp = " + ".join(reversed(terms))
    if reversed_exp not in used_values:
        traps.append((reversed_exp, "pv_reverse"))
        used_values.add(reversed_exp)
    
    # Trap 3: Wrong place value (shift one place down)
    wrong_terms = []
    for i, d in enumerate(digits):
        if d != '0':
            place = len(digits) - 2 - i  # Shifted down by 1
            if place >= 0:
                value = int(d) * PLACE_VALUES[place]
                wrong_terms.append(str(value))
    if wrong_terms:
        shifted_exp = " + ".join(wrong_terms)
        if shifted_exp not in used_values:
            traps.append((shifted_exp, "pv_place_shift"))
            used_values.add(shifted_exp)
    
    # Fill remaining traps
    while len(traps) < 3:
        # Modify one term in the correct answer
        wrong = terms.copy()
        if wrong:
            idx = rng.randint(0, len(wrong) - 1)
            val = int(wrong[idx])
            modification = rng.choice([10, -10, 100, -100, 1, -1])
            new_val = val + modification
            if new_val > 0:
                wrong[idx] = str(new_val)
                modified_exp = " + ".join(wrong)
                if modified_exp not in used_values:
                    traps.append((modified_exp, "pv_wrong_val"))
                    used_values.add(modified_exp)
                    continue
        # Fallback: just change a digit
        wrong = terms.copy()
        if wrong:
            idx = rng.randint(0, len(wrong) - 1)
            val = int(wrong[idx])
            wrong[idx] = str(val * 10)
            fallback_exp = " + ".join(wrong)
            if fallback_exp not in used_values:
                traps.append((fallback_exp, "pv_wrong_val"))
                used_values.add(fallback_exp)
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"Write {number} in expanded form.",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"number": number, "correct": correct},
    }


def _gen_pv_round(digit_count: int, rng: random.Random, text_lower: str,
                  precision_override: str = None) -> Dict[str, Any]:
    """Round numbers to the nearest ten, hundred, or thousand."""
    # Determine rounding target — precision override takes priority over text
    precision_map = {
        'nearest_ten':      (10, 'ten',      2),
        'nearest_hundred':  (100, 'hundred', 3),
        'nearest_thousand': (1000, 'thousand', 4),
    }

    if precision_override and precision_override in precision_map:
        round_to, round_name, min_digits = precision_map[precision_override]
        digit_count = max(digit_count, min_digits)
    elif "thousand" in text_lower:
        round_to = 1000
        round_name = "thousand"
        digit_count = max(digit_count, 4)
    elif "hundred" in text_lower:
        round_to = 100
        round_name = "hundred"
        digit_count = max(digit_count, 3)
    else:
        round_to = 10
        round_name = "ten"
        digit_count = max(digit_count, 2)
    
    # Generate appropriate number
    min_val = 10 ** (digit_count - 1)
    max_val = 10 ** digit_count - 1
    number = rng.randint(min_val, max_val)
    
    # Avoid numbers that are already rounded (end in 0s)
    while number % round_to == 0:
        number = rng.randint(min_val, max_val)
    
    # Calculate rounded value
    rounded = round(number / round_to) * round_to
    
    # Determine the two nearest multiples
    lower = (number // round_to) * round_to
    upper = lower + round_to
    
    stems = [
        f"Round {_format_number(number)} to the nearest {round_name}.",
        f"What is {_format_number(number)} rounded to the nearest {round_name}?",
        f"{_format_number(number)} rounded to the nearest {round_name} is:",
    ]
    
    correct = str(rounded)
    # Traps: rounded wrong direction, rounded to wrong place, didn't round
    wrong_direction = str(lower if rounded == upper else upper)
    wrong_place = str(round(number / (round_to * 10)) * (round_to * 10)) if round_to * 10 <= max_val else str(number)
    
    traps = [
        (wrong_direction, "pv_rounded_wrong_dir"),
        (wrong_place, "pv_wrong_place"),
        (str(number), "pv_no_round"),
    ]
    
    # Ensure unique traps
    seen = {correct}
    final_traps = []
    for t_val, t_name in traps:
        if t_val not in seen:
            final_traps.append((t_val, t_name))
            seen.add(t_val)
    while len(final_traps) < 3:
        filler = str(rng.randint(lower - round_to, upper + round_to))
        if filler not in seen:
            final_traps.append((filler, "pv_off_by"))
            seen.add(filler)
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + final_traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"number": number, "rounded": rounded, "round_to": round_to, "sub_type": "rounding"},
    }


def _gen_pv_read_write(digit_count: int, rng: random.Random,
                        max_number_cap: int = None, direction_override: str = None) -> Dict[str, Any]:
    """Read and write numbers in words or convert words to numerals."""
    # Word mappings
    ones_words = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    teens_words = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
                   "sixteen", "seventeen", "eighteen", "nineteen"]
    tens_words = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    def number_to_words(n: int) -> str:
        if n <= 0:
            return str(n)
        parts = []
        if n >= 1000:
            parts.append(f"{ones_words[n // 1000]} thousand")
            n %= 1000
        if n >= 100:
            parts.append(f"{ones_words[n // 100]} hundred")
            n %= 100
        if n >= 20:
            t = tens_words[n // 10]
            o = ones_words[n % 10]
            parts.append(f"{t}-{o}" if o else t)
        elif n >= 10:
            parts.append(teens_words[n - 10])
        elif n > 0:
            parts.append(ones_words[n])
        return " ".join(parts)

    def _make_expanded(n: int) -> str:
        """Return expanded form, e.g. '200 + 40 + 3'."""
        parts = []
        place = 1
        tmp = n
        while tmp:
            d = (tmp % 10) * place
            if d:
                parts.append(d)
            tmp //= 10
            place *= 10
        return " + ".join(str(d) for d in reversed(parts)) if parts else "0"

    # Generate number based on digit count, capped by range axis if specified
    min_val = 10 ** (digit_count - 1)
    max_val = min(10 ** digit_count - 1, 9999)  # Cap at 4 digits for words
    if max_number_cap:
        max_val = min(max_val, int(max_number_cap))
    # For 1-digit numbers (range 1-20 with digit_count=2 clamped), allow single digits
    if max_number_cap and max_number_cap <= 20:
        min_val = max(1, min(min_val, max_val))
    else:
        min_val = min(min_val, max_val)  # Ensure min <= max
    number = rng.randint(min_val, max_val)
    words = number_to_words(number)

    # Determine direction from override or random
    if direction_override == "word_to_numeral":
        use_word_to_numeral = True
    elif direction_override == "numeral_to_word":
        use_word_to_numeral = False
    elif direction_override == "numeral_to_expanded":
        # Expanded form direction
        expanded = _make_expanded(number)
        stems = [
            f"Write {_format_number(number)} in expanded form.",
            f"What is the expanded form of {_format_number(number)}?",
        ]
        correct = expanded
        # Distractors: wrong expanded forms
        wrong_expanded = []
        # Swap two place values
        if number >= 100:
            wrong_expanded.append(_make_expanded(number + 10))
        if number >= 10:
            wrong_expanded.append(_make_expanded(number - 1) if number > min_val else _make_expanded(number + 1))
        # Omit a place (e.g., leave out tens)
        parts_list = [int(p) for p in expanded.split(" + ")]
        if len(parts_list) > 1:
            partial = " + ".join(str(p) for p in parts_list[:-1])
            wrong_expanded.append(partial)

        seen = {correct}
        final_traps = []
        for we in wrong_expanded:
            if we not in seen and we:
                final_traps.append((we, "pv_wrong_expanded"))
                seen.add(we)
        while len(final_traps) < 3:
            filler_num = rng.randint(min_val, max_val)
            filler = _make_expanded(filler_num)
            if filler not in seen:
                final_traps.append((filler, "pv_random_expanded"))
                seen.add(filler)

        stem = rng.choice(stems)
        options_list = [(correct, None)] + final_traps[:3]
        return {
            "stem": stem,
            "correct_answer": correct,
            "options": _shuffle_options(options_list, rng),
            "variables": {"number": number, "expanded": expanded, "sub_type": "expanded_form"},
        }
    else:
        # Random direction
        use_word_to_numeral = rng.random() < 0.5

    if use_word_to_numeral:
        # Words to numeral
        stems = [
            f"Write '{words}' as a numeral.",
            f"What number is '{words}'?",
            f"'{words}' in digits is:",
        ]
        correct = str(number)
        # Common mistakes: misplacing digits, literal interpretation
        digits = str(number)
        wrong1 = str(min(number + 10, max_val)) if len(digits) <= 3 else digits[0] + "0" + digits[2:]
        if number > min_val + 10:
            wrong2 = str(number - 10)
        elif number + 20 <= max_val:
            wrong2 = str(number + 20)
        else:
            wrong2 = str(max(1, number - 5) if number - 5 >= 1 else number + 5)
        wrong3 = str(int(digits[::-1])) if digits != digits[::-1] and int(digits[::-1]) > 0 else str(max(1, number + 1))
        
        traps = [
            (wrong1, "pv_misplaced_digit"),
            (wrong2, "pv_wrong_value"),
            (wrong3, "pv_reversed"),
        ]
    else:
        # Numeral to words
        stems = [
            f"Write {_format_number(number)} in words.",
            f"How do you write {_format_number(number)} in words?",
            f"The number {_format_number(number)} written in words is:",
        ]
        correct = words
        # Generate distractors that stay within [1, max_val]
        wrong_number = min(number + 10, max_val) if number + 10 != number else number + 1
        wrong1 = number_to_words(wrong_number)
        if number > min_val + 10:
            wrong_number2 = number - 10
        elif number + 20 <= max_val:
            wrong_number2 = number + 20
        else:
            wrong_number2 = max(1, number - 5) if number - 5 >= 1 else number + 5
        wrong2 = number_to_words(wrong_number2)
        # Nearby number (avoid going negative or exceeding max_val)
        if number + 5 <= max_val:
            wrong_number3 = number + 5
        elif number - 5 >= 1:
            wrong_number3 = number - 5
        else:
            wrong_number3 = max(1, number + 3)
        wrong3 = number_to_words(wrong_number3)
        
        traps = [
            (wrong1, "pv_wrong_words"),
            (wrong2, "pv_wrong_words"),
            (wrong3, "pv_wrong_place_words"),
        ]
    
    # Ensure unique traps
    seen = {correct}
    final_traps = []
    for t_val, t_name in traps:
        if str(t_val) not in seen:
            final_traps.append((str(t_val), t_name))
            seen.add(str(t_val))
    while len(final_traps) < 3:
        filler_num = rng.randint(min_val, max_val)
        filler = str(filler_num) if rng.random() < 0.5 else number_to_words(filler_num)
        if filler not in seen:
            final_traps.append((filler, "pv_random"))
            seen.add(filler)
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + final_traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"number": number, "words": words, "sub_type": "read_write"},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATOR: ARITHMETIC
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_arithmetic(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Generate arithmetic problems.
    
    Types:
    - Addition
    - Subtraction
    - Multiplication
    - Division
    - Missing number
    """
    # Use numeric_limit from constraints if available (e.g., "sums up to 20")
    # Scale by difficulty so easy mode uses smaller numbers even within the curriculum limit
    raw_limit = constraints.get("numeric_limit", dimensions.get("operand_max", 100))
    operand_max = dimensions.get("operand_max", raw_limit)
    # Use operand_max from dimensions (difficulty-scaled) but cap at raw_limit
    result_limit = min(operand_max, raw_limit) if operand_max else raw_limit
    regrouping_prob = dimensions.get("regrouping_probability", 0.5)
    regrouping_required = dimensions.get("regrouping_required", False)
    include_remainder = dimensions.get("include_remainder", 0.0)
    structure = dimensions.get("structure", "result_unknown")
    number_type = dimensions.get("number_type", None)

    # For tens/double regrouping we need at least 2-digit operands.
    # If the curriculum constrains result_limit to e.g. 20 we can't do tens-carry,
    # so silently raise the floor to 200.
    regrouping_type = dimensions.get("regrouping_type", "none")
    if regrouping_type in ("tens", "double") and result_limit < 200:
        result_limit = 200
        operand_max = 200

    text_lower = competency_text.lower()

    # Estimation branch
    if "estimat" in text_lower:
        return _gen_arithmetic_estimate(operand_max, rng, text_lower)

    # Even/odd identification
    if "even" in text_lower or "odd" in text_lower:
        return _gen_arithmetic_even_odd(operand_max, rng)

    operations = constraints.get("operations", [])

    with_regrouping = regrouping_required or rng.random() < regrouping_prob

    if "missing" in text_lower or "find the" in text_lower or structure in ("change_unknown", "start_unknown"):
        return _gen_arithmetic_missing(result_limit, operations, rng, structure=structure)
    elif "divid" in text_lower or structure == "divisor_unknown" or "div" in operations:
        # Check division BEFORE multiplication so "divide...multiplication tables" routes to division
        return _gen_arithmetic_divide(result_limit, include_remainder > 0.5, rng, structure=structure)
    elif "multipl" in text_lower or structure == "factor_unknown" or "mul" in operations:
        return _gen_arithmetic_multiply(result_limit, rng, structure=structure)
    elif "subtract" in text_lower or "sub" in operations:
        return _gen_arithmetic_subtract(result_limit, with_regrouping, rng,
                                        number_type=number_type, regrouping_type=regrouping_type)
    else:
        return _gen_arithmetic_add(result_limit, with_regrouping, rng,
                                   is_sum_limit=True, structure=structure,
                                   number_type=number_type, regrouping_type=regrouping_type)


def _gen_arithmetic_add(operand_max: int, with_regrouping: bool, rng: random.Random,
                        is_sum_limit: bool = False, structure: str = "result_unknown",
                        number_type: str = None, regrouping_type: str = "none") -> Dict[str, Any]:
    """Generate addition problem respecting regrouping, structure, and number_type."""
    max_sum = max(3, operand_max)

    # ── Pick operands a, b ────────────────────────────────────────────────────
    for _attempt in range(100):
        if is_sum_limit:
            a = rng.randint(1, max(1, max_sum - 1))
            b = rng.randint(1, max(1, max_sum - a))
        else:
            half = max(2, operand_max // 2)
            a = rng.randint(1, half)
            b = rng.randint(1, half)

        # Apply number_type constraint
        if number_type == "round":
            a = (round(a / 5) * 5) or 5
            b = (round(b / 5) * 5) or 5
        elif number_type == "non_round":
            # Ensure at least one operand is NOT divisible by 5
            # Adjust last digit to be non-zero, non-five
            if a % 5 == 0:
                a = a - 1 or 1
            if b % 5 == 0:
                b = b - 1 or 1
        elif number_type == "single_digit":
            a = max(1, a % 10)
            b = max(1, b % 10)
        elif number_type == "multi_digit":
            a = max(10, a)
            b = max(10, b)

        ones_carry = (a % 10) + (b % 10) >= 10
        tens_carry = (a // 10 % 10) + (b // 10 % 10) + (1 if ones_carry else 0) >= 10

        # Apply exact regrouping constraint
        if regrouping_type == "none":
            if ones_carry or tens_carry:
                continue
        elif regrouping_type == "ones":
            if not ones_carry or tens_carry:
                continue
        elif regrouping_type == "tens":
            if not tens_carry:
                continue
        elif regrouping_type == "double":
            if not (ones_carry and tens_carry):
                continue
        elif with_regrouping and not ones_carry and not tens_carry:
            continue
        elif not with_regrouping and (ones_carry or tens_carry):
            continue

        break

    correct = a + b

    # ── Build stem based on structure ─────────────────────────────────────────
    if structure == "change_unknown":
        stem = f"{a} + ___ = {correct}"
        correct_val = b
    elif structure == "start_unknown":
        stem = f"___ + {b} = {correct}"
        correct_val = a
    else:  # result_unknown
        stem = f"{a} + {b} = ?"
        correct_val = correct

    # ── Traps ─────────────────────────────────────────────────────────────────
    traps = [
        (abs(a - b), "ar_wrong_op"),
        (correct_val + 1, "ar_off_one"),
    ]
    if with_regrouping:
        no_carry = (a % 10 + b % 10) % 10 + (a // 10 + b // 10) * 10
        traps.append((no_carry if no_carry != correct_val else correct_val - 10, "ar_no_regroup"))
    else:
        traps.append((correct_val + 10, "ar_off_ten"))

    options_list = [(correct_val, None)] + traps[:3]

    return {
        "stem": stem,
        "correct_answer": str(correct_val),
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b, "correct": correct, "operation": "add", "structure": structure},
    }


def _gen_arithmetic_subtract(operand_max: int, with_regrouping: bool, rng: random.Random,
                              number_type: str = None, regrouping_type: str = "none") -> Dict[str, Any]:
    """Generate subtraction problem respecting regrouping and number_type."""
    operand_max = max(20, operand_max)

    for _attempt in range(100):
        a = rng.randint(max(5, operand_max // 4), operand_max)
        b = rng.randint(1, max(1, a - 1))

        if number_type == "round":
            a = (round(a / 5) * 5) or 5
            b = (round(b / 5) * 5) or 5
            b = max(1, min(b, a - 1))
        elif number_type == "single_digit":
            a = max(2, a % 10)
            b = max(1, b % 10)
            if b >= a:
                b = a - 1

        needs_borrow_ones = (a % 10) < (b % 10)
        needs_borrow_tens = (a // 10 % 10) - (1 if needs_borrow_ones else 0) < (b // 10 % 10)

        if regrouping_type == "none":
            if needs_borrow_ones or needs_borrow_tens:
                continue
        elif regrouping_type == "ones":
            if not needs_borrow_ones or needs_borrow_tens:
                continue
        elif regrouping_type == "tens":
            if not needs_borrow_tens:
                continue
        elif regrouping_type == "double":
            if not (needs_borrow_ones and needs_borrow_tens):
                continue
        elif with_regrouping and not needs_borrow_ones and not needs_borrow_tens:
            continue
        elif not with_regrouping and (needs_borrow_ones or needs_borrow_tens):
            continue

        if b >= a:
            continue
        break

    b = max(1, min(b, a - 1))
    correct = a - b

    traps = [
        (a + b, "ar_wrong_op"),
        (correct + 1, "ar_off_one"),
        (b - a if b > a else correct - 1, "ar_reverse_sub"),
    ]
    options_list = [(correct, None)] + traps[:3]

    return {
        "stem": f"{a} - {b} = ?",
        "correct_answer": str(correct),
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b, "correct": correct, "operation": "subtract"},
    }


def _gen_arithmetic_multiply(operand_max: int, rng: random.Random,
                              structure: str = "result_unknown") -> Dict[str, Any]:
    """Generate multiplication problem respecting structure."""
    max_factor = min(12, max(2, int(operand_max ** 0.5)))
    a = rng.randint(2, max_factor)
    b = rng.randint(2, max_factor)
    correct = a * b

    if structure == "factor_unknown":
        stem = f"{a} × ___ = {correct}"
        correct_val = b
    elif structure == "start_unknown":
        stem = f"___ × {b} = {correct}"
        correct_val = a
    else:
        stem = f"{a} × {b} = ?"
        correct_val = correct

    traps = [
        (a + b, "ar_mul_add"),
        (correct_val + a, "ar_off_one"),
        (max(1, correct_val - b), "ar_off_one"),
    ]
    options_list = [(correct_val, None)] + traps[:3]

    return {
        "stem": stem,
        "correct_answer": str(correct_val),
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b, "correct": correct, "operation": "multiply", "structure": structure},
    }


def _gen_arithmetic_divide(operand_max: int, with_remainder: bool, rng: random.Random,
                            structure: str = "result_unknown") -> Dict[str, Any]:
    """Generate division problem respecting structure."""
    operand_max = max(20, operand_max)

    if with_remainder:
        divisor = rng.randint(2, 9)
        quotient = rng.randint(2, max(3, operand_max // divisor))
        remainder = rng.randint(1, divisor - 1)
        dividend = divisor * quotient + remainder
        correct = f"{quotient} R {remainder}"
        traps = [
            (str(quotient), "ar_rem_drop"),
            (str(remainder), "ar_rem_swap"),
            (f"{quotient + 1} R {remainder}", "ar_off_one"),
        ]
        stem = f"{dividend} ÷ {divisor} = ?"
        correct_val = correct
    else:
        # Ensure dividend is cleanly divisible
        divisor = rng.randint(2, 9)
        quotient = rng.randint(2, min(20, max(3, operand_max // divisor)))
        dividend = divisor * quotient
        # Sanity check: dividend must be divisible
        assert dividend % divisor == 0, f"{dividend} not divisible by {divisor}"

        if structure == "divisor_unknown":
            stem = f"{dividend} ÷ ___ = {quotient}"
            correct_val = str(divisor)
        elif structure == "start_unknown":
            stem = f"___ ÷ {divisor} = {quotient}"
            correct_val = str(dividend)
        else:
            stem = f"{dividend} ÷ {divisor} = ?"
            correct_val = str(quotient)

        cv = int(correct_val)
        traps = [
            (str(max(1, cv - divisor)), "ar_div_sub"),
            (str(cv + 1), "ar_off_one"),
            (str(max(1, cv - 1)), "ar_off_one"),
        ]
        correct = correct_val

    options_list = [(correct_val, None)] + traps[:3]

    return {
        "stem": stem,
        "correct_answer": str(correct_val),
        "options": _shuffle_options(options_list, rng),
        "variables": {"dividend": dividend, "divisor": divisor, "correct": correct_val, "operation": "divide"},
    }


def _gen_arithmetic_missing(operand_max: int, operations: List[str], rng: random.Random,
                             structure: str = "change_unknown") -> Dict[str, Any]:
    """Generate missing-number problem respecting structure (blank position)."""
    op = rng.choice(operations) if operations else rng.choice(["add", "sub"])
    op_is_add = op in ("add", "addition")

    a = rng.randint(1, max(1, operand_max // 2))
    c = rng.randint(a + 1, max(a + 2, operand_max))
    b = c - a if op_is_add else a - c

    if op_is_add:
        if structure == "start_unknown":
            stem = f"___ + {b} = {c}"
            correct = a
        elif structure == "result_unknown":
            stem = f"{a} + {b} = ___"
            correct = c
        else:  # change_unknown (default)
            stem = f"{a} + ___ = {c}"
            correct = b
        traps = [correct + 1, abs(correct - 1), a + c]
    else:
        a2 = rng.randint(max(5, operand_max // 4), operand_max)
        c2 = rng.randint(1, max(1, a2 - 1))
        b2 = a2 - c2
        if structure == "start_unknown":
            stem = f"___ - {b2} = {c2}"
            correct = a2
        elif structure == "result_unknown":
            stem = f"{a2} - {b2} = ___"
            correct = c2
        else:  # change_unknown
            stem = f"{a2} - ___ = {c2}"
            correct = b2
        traps = [correct + 1, c2, a2 + c2]

    options_list = [(correct, None)] + [(t, "ar_off_one") for t in traps[:3] if t != correct]
    if len(options_list) < 4:
        options_list.append((correct + 2, "ar_off_two"))

    return {
        "stem": stem,
        "correct_answer": str(correct),
        "options": _shuffle_options(options_list[:4], rng),
        "variables": {"correct": correct, "structure": structure},
    }


def _gen_arithmetic_estimate(operand_max: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Estimate sums, differences, products, or quotients by rounding first."""
    # Determine operation
    if "product" in text_lower or "multipl" in text_lower:
        op = "multiply"
    elif "quotient" in text_lower or "divid" in text_lower:
        op = "divide"
    elif "difference" in text_lower or "subtract" in text_lower:
        op = "subtract"
    else:
        op = "add"
    
    # Determine rounding level based on operand size
    if operand_max <= 100:
        round_to = 10
        a = rng.randint(11, 99)
        b = rng.randint(11, 99)
    elif operand_max <= 1000:
        round_to = 100
        a = rng.randint(101, 999)
        b = rng.randint(101, 999)
    else:
        round_to = 1000
        a = rng.randint(1001, 9999)
        b = rng.randint(1001, 9999)
    
    # Round values
    a_rounded = round(a / round_to) * round_to
    b_rounded = round(b / round_to) * round_to
    
    # Calculate estimated and exact results
    if op == "add":
        estimated = a_rounded + b_rounded
        exact = a + b
        op_symbol = "+"
    elif op == "subtract":
        if a < b:
            a, b = b, a
            a_rounded, b_rounded = round(a / round_to) * round_to, round(b / round_to) * round_to
        estimated = a_rounded - b_rounded
        exact = a - b
        op_symbol = "-"
    elif op == "multiply":
        # Use smaller numbers for multiplication
        a = rng.randint(11, 99)
        b = rng.randint(2, 9)
        a_rounded = round(a / 10) * 10
        estimated = a_rounded * b
        exact = a * b
        op_symbol = "x"
        round_to = 10
    else:  # divide
        b = rng.randint(2, 9)
        a = b * rng.randint(11, 99)
        a_rounded = round(a / 10) * 10
        estimated = a_rounded // b
        exact = a // b
        op_symbol = "/"
        round_to = 10
    
    stems = [
        f"Estimate {a} {op_symbol} {b} by rounding to the nearest {round_to}.",
        f"Round each number to the nearest {round_to}, then compute: {a} {op_symbol} {b}.",
        f"What is the best estimate for {a} {op_symbol} {b}?",
    ]
    
    correct = str(estimated)
    traps = [
        (str(exact), "ar_exact_not_estimate"),
        (str(estimated + round_to), "ar_rounded_wrong"),
        (str(abs(estimated - round_to)), "ar_rounded_wrong"),
    ]
    
    # Ensure unique traps
    seen = {correct}
    final_traps = []
    for t_val, t_name in traps:
        if t_val not in seen:
            final_traps.append((t_val, t_name))
            seen.add(t_val)
    while len(final_traps) < 3:
        filler = str(estimated + rng.choice([-2, 2, -1, 1]) * round_to)
        if filler not in seen:
            final_traps.append((filler, "ar_off_by_round"))
            seen.add(filler)
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + final_traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b, "estimated": estimated, "exact": exact, "sub_type": "estimation"},
    }


def _gen_arithmetic_even_odd(operand_max: int, rng: random.Random) -> Dict[str, Any]:
    """Identify even/odd numbers or explain the concept."""
    question_type = rng.choice(["identify", "which_is", "division_rule"])
    
    if question_type == "identify":
        n = rng.randint(2, min(operand_max, 100))
        is_even = n % 2 == 0
        correct = "even" if is_even else "odd"
        wrong = "odd" if is_even else "even"
        
        stems = [
            f"Is {n} even or odd?",
            f"The number {n} is:",
            f"Classify {n}: even or odd?",
        ]
        traps = [
            (wrong, "ar_even_odd_swap"),
            ("neither", "ar_no_category"),
            ("both", "ar_no_category"),
        ]
    elif question_type == "which_is":
        # Generate 4 numbers, some even some odd
        target = rng.choice(["even", "odd"])
        if target == "even":
            correct_n = rng.randint(1, min(operand_max // 2, 50)) * 2
            wrongs = [correct_n + 1, correct_n + 3, correct_n - 1]
        else:
            correct_n = rng.randint(1, min(operand_max // 2, 50)) * 2 + 1
            wrongs = [correct_n + 1, correct_n - 1, correct_n + 3]
        
        stems = [
            f"Which number is {target}?",
            f"Identify the {target} number:",
            f"Select the {target} number from the choices.",
        ]
        correct = str(correct_n)
        traps = [(str(w), "ar_even_odd_swap") for w in wrongs[:3]]
    else:
        # Division rule
        n = rng.randint(2, min(operand_max, 50)) * 2
        stems = [
            f"Why is {n} an even number?",
            f"{n} is even because:",
            f"How do we know {n} is even?",
        ]
        correct = f"it can be divided by 2 with no remainder"
        traps = [
            ("it ends in 0", "ar_partial_rule"),
            ("it is greater than 1", "ar_wrong_rule"),
            ("it cannot be divided by 2", "ar_opposite"),
        ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "even_odd"},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATOR: FRACTIONS (Basic implementation)
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_fractions(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """Generate fraction problems."""
    denom_max = dimensions.get("denominator_max", 8)
    allowed_denoms = dimensions.get("allowed_denominators", [2, 3, 4, 5, 6, 8])
    fraction_type_idx = dimensions.get("fraction_type_index", 0.3)
    fraction_type_name = dimensions.get("fraction_type", None)  # explicit axis override

    if isinstance(allowed_denoms, int):
        allowed_denoms = [d for d in [2, 3, 4, 5, 6, 8, 10, 12] if d <= allowed_denoms]

    text_lower = competency_text.lower()

    structure = dimensions.get("structure", "result_unknown")

    if "compare" in text_lower or "order" in text_lower:
        return _gen_fractions_compare(allowed_denoms, rng)
    elif "subtract" in text_lower:
        return _gen_fractions_subtract(allowed_denoms, rng, structure=structure)
    elif "add" in text_lower:
        return _gen_fractions_add(allowed_denoms, rng, structure=structure)
    elif "equivalent" in text_lower:
        return _gen_fractions_equivalent(allowed_denoms, rng)
    else:
        return _gen_fractions_identify(allowed_denoms, rng, fraction_type=fraction_type_name)


def _gen_fractions_identify(allowed_denoms: List[int], rng: random.Random,
                             fraction_type: str = None) -> Dict[str, Any]:
    """Identify a fraction from description, honouring fraction_type axis."""
    d = rng.choice(allowed_denoms)

    if fraction_type == "unit_fraction":
        n = 1
    elif fraction_type == "mixed_number":
        whole = rng.randint(1, 4)
        n = rng.randint(1, d - 1)
        correct = f"{whole} {n}/{d}"
        traps = [
            (f"{whole + 1} {n}/{d}", "fr_off_whole"),
            (f"{n}/{d}", "fr_drop_whole"),
            (f"{whole} {d}/{n}", "fr_swap_nd"),
        ]
        options_list = [(correct, None)] + traps[:3]
        return {
            "stem": f"Write the mixed number: {whole} whole(s) and {n}/{d}.",
            "correct_answer": correct,
            "options": _shuffle_options(options_list, rng),
            "variables": {"whole": whole, "numerator": n, "denominator": d},
        }
    else:
        # similar_proper or default
        n = rng.randint(1, max(1, d - 1))

    correct = f"{n}/{d}"
    traps = [
        (f"{d}/{n}" if n != d else f"{d}/{d+1}", "fr_swap_nd"),
        (f"{n}/{d+1}", "fr_big_den"),
        (f"{n+1}/{d}", "fr_big_num"),
    ]
    options_list = [(correct, None)] + traps[:3]

    return {
        "stem": f"A shape is divided into {d} equal parts. {n} parts are shaded. What fraction is shaded?",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"numerator": n, "denominator": d},
    }


def _gen_fractions_compare(allowed_denoms: List[int], rng: random.Random) -> Dict[str, Any]:
    """Compare two fractions."""
    d1 = rng.choice(allowed_denoms)
    d2 = rng.choice(allowed_denoms)
    n1 = rng.randint(1, d1 - 1)
    n2 = rng.randint(1, d2 - 1)
    
    # Ensure they're different
    while n1/d1 == n2/d2:
        n2 = rng.randint(1, d2 - 1)
    
    f1 = f"{n1}/{d1}"
    f2 = f"{n2}/{d2}"
    
    if n1/d1 > n2/d2:
        correct = f1
        wrong = f2
    else:
        correct = f2
        wrong = f1
    
    traps = [
        (wrong, "fr_big_num" if n1 > n2 else "fr_big_den"),
        ("equal", "fr_unit_rev"),
        (f"{n1+n2}/{d1+d2}", "fr_add_both"),
    ]
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"Which fraction is larger: {f1} or {f2}?",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"f1": f1, "f2": f2},
    }


def _gen_fractions_add(allowed_denoms: List[int], rng: random.Random,
                        structure: str = "result_unknown") -> Dict[str, Any]:
    """Add two fractions with like denominators, respecting structure."""
    d = rng.choice(allowed_denoms)
    n1 = rng.randint(1, d - 2)
    n2 = rng.randint(1, d - n1 - 1)
    result_n = n1 + n2
    correct = f"{result_n}/{d}"
    g = gcd(result_n, d)
    simplified = f"{result_n//g}/{d//g}" if g > 1 else correct

    if structure == "change_unknown":
        stem = f"{n1}/{d} + ___ = {simplified}"
        correct_val = f"{n2}/{d}"
    elif structure == "start_unknown":
        stem = f"___ + {n2}/{d} = {simplified}"
        correct_val = f"{n1}/{d}"
    else:
        stem = f"{n1}/{d} + {n2}/{d} = ?"
        correct_val = simplified

    traps = [
        (f"{n1 + n2}/{d + d}", "fr_add_both"),
        (f"{n1 * n2}/{d}", "ar_mul_add"),
        (f"{result_n}/{d-1}", "fr_wrong_lcd"),
    ]
    options_list = [(correct_val, None)] + traps[:3]

    return {
        "stem": stem,
        "correct_answer": correct_val,
        "options": _shuffle_options(options_list, rng),
        "variables": {"n1": n1, "n2": n2, "d": d},
    }


def _gen_fractions_subtract(allowed_denoms: List[int], rng: random.Random,
                              structure: str = "result_unknown") -> Dict[str, Any]:
    """Subtract two fractions with like denominators, respecting structure."""
    d = rng.choice(allowed_denoms)
    n1 = rng.randint(2, d - 1)
    n2 = rng.randint(1, n1 - 1)
    result_n = n1 - n2
    correct = f"{result_n}/{d}"
    g = gcd(result_n, d)
    simplified = f"{result_n//g}/{d//g}" if g > 1 else correct

    if structure == "change_unknown":
        stem = f"{n1}/{d} - ___ = {simplified}"
        correct_val = f"{n2}/{d}"
    elif structure == "start_unknown":
        stem = f"___ - {n2}/{d} = {simplified}"
        correct_val = f"{n1}/{d}"
    else:
        stem = f"{n1}/{d} - {n2}/{d} = ?"
        correct_val = simplified

    used = {correct_val}
    traps = []
    for cand, trap_name in [
        (f"{n1 + n2}/{d}", "ar_wrong_op"),
        (f"{result_n}/{d - 1}" if d > 1 else f"{result_n}/2", "fr_sub_both"),
        (f"{n1 - n2 + 1}/{d}", "fr_swap_order"),
    ]:
        if cand not in used:
            traps.append((cand, trap_name))
            used.add(cand)

    while len(traps) < 3:
        wrong_n = result_n + rng.choice([1, -1, 2])
        if 0 < wrong_n < d:
            trap = f"{wrong_n}/{d}"
            if trap not in used:
                traps.append((trap, "fr_calc_err"))
                used.add(trap)
        else:
            traps.append((f"{result_n}/{d+1}", "fr_calc_err"))
            break

    options_list = [(correct_val, None)] + traps[:3]

    return {
        "stem": stem,
        "correct_answer": correct_val,
        "options": _shuffle_options(options_list, rng),
        "variables": {"n1": n1, "n2": n2, "d": d},
    }


def _gen_fractions_equivalent(allowed_denoms: List[int], rng: random.Random) -> Dict[str, Any]:
    """Find equivalent fraction."""
    d1 = rng.choice([d for d in allowed_denoms if d <= 6])
    n1 = rng.randint(1, d1 - 1)
    
    # Make sure fraction is in lowest terms
    g = gcd(n1, d1)
    n1, d1 = n1 // g, d1 // g
    
    multiplier = rng.randint(2, 4)
    n2 = n1 * multiplier
    d2 = d1 * multiplier
    
    correct = f"{n2}/{d2}"
    
    traps = [
        (f"{n1 + multiplier}/{d1 + multiplier}", "fr_num_unchanged"),  # Added instead of multiplied
        (f"{n2}/{d1}", "fr_num_unchanged"),  # Only changed numerator
        (f"{n1}/{d2}", "fr_num_unchanged"),  # Only changed denominator
    ]
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"Which fraction is equivalent to {n1}/{d1}?",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"n1": n1, "d1": d1, "multiplier": multiplier},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PLACEHOLDER GENERATORS (to be implemented)
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_decimals(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Generate decimal problems.
    
    Types:
    - Place value identification: "In 3.45, what place is 5 in?"
    - Decimal arithmetic: "2.5 + 1.3 = ?"
    - Decimal comparison: "Which is greater: 3.14 or 3.41?"
    - Decimal conversion: "Write 0.25 as a fraction"
    """
    decimal_places = dimensions.get("decimal_places", 2)
    whole_max = dimensions.get("whole_part_max", 10)
    text_lower = competency_text.lower()
    
    # Detect operation type from competency text
    has_operation = any(op in text_lower for op in ["add", "subtract", "multiply", "divide", "+", "-", "×", "÷"])
    has_compare = any(word in text_lower for word in ["compare", "order", "greater", "less", "arrange"])
    has_conversion = any(word in text_lower for word in ["convert", "fraction", "percent"])
    
    if has_operation:
        return _gen_decimal_arithmetic(decimal_places, whole_max, text_lower, rng)
    elif has_compare:
        return _gen_decimal_compare(decimal_places, whole_max, rng)
    elif has_conversion:
        return _gen_decimal_conversion(decimal_places, rng)
    else:
        return _gen_decimal_place_value(decimal_places, whole_max, rng)


def _gen_decimal_arithmetic(decimal_places: int, whole_max: int, text_lower: str, rng: random.Random) -> Dict[str, Any]:
    """Generate decimal arithmetic problems."""
    # Determine operation
    if "subtract" in text_lower or "-" in text_lower:
        op = "-"
        op_func = lambda a, b: a - b
    elif "multiply" in text_lower or "×" in text_lower:
        op = "×"
        op_func = lambda a, b: a * b
    elif "divide" in text_lower or "÷" in text_lower:
        op = "÷"
        op_func = lambda a, b: a / b if b != 0 else 0
    else:
        op = "+"
        op_func = lambda a, b: a + b
    
    # Generate operands with decimals
    divisor = 10 ** decimal_places
    
    a_whole = rng.randint(1, whole_max)
    a_frac = rng.randint(1, divisor - 1)
    a = a_whole + a_frac / divisor
    
    b_whole = rng.randint(1, whole_max)
    b_frac = rng.randint(1, divisor - 1)
    b = b_whole + b_frac / divisor
    
    # For subtraction, ensure a > b
    if op == "-" and a < b:
        a, b = b, a
    
    # For division, make it come out nicely
    if op == "÷":
        # Make b a divisor that produces clean decimals
        multipliers = [2, 4, 5, 10]
        b = rng.choice(multipliers)
        a = b * rng.randint(1, 5) + rng.choice([0, 0.5, 0.25, 0.1, 0.2])
    
    result = op_func(a, b)
    
    # Format numbers
    def fmt(n):
        if decimal_places == 1:
            return f"{n:.1f}"
        elif decimal_places == 2:
            return f"{n:.2f}"
        else:
            return f"{n:.{decimal_places}f}"
    
    correct = fmt(result)
    
    # Generate traps
    used_values = {correct}
    traps = []
    
    # Off by 0.1 (place value error)
    off_by_tenth = fmt(result + 0.1)
    if off_by_tenth not in used_values:
        traps.append((off_by_tenth, "dc_place_err"))
        used_values.add(off_by_tenth)
    
    # Forgot to carry/borrow
    wrong_carry = fmt(result + 1) if op == "+" else fmt(result - 1)
    if wrong_carry not in used_values:
        traps.append((wrong_carry, "dc_carry_err"))
        used_values.add(wrong_carry)
    
    # Wrong decimal place alignment
    misalign = fmt(result * 10)
    if misalign not in used_values:
        traps.append((misalign, "dc_align_err"))
        used_values.add(misalign)
    
    # Fill if needed
    while len(traps) < 3:
        offset = rng.choice([0.01, -0.01, 0.11, -0.11, 1.0, -1.0])
        trap_val = fmt(result + offset)
        if trap_val not in used_values and float(trap_val) > 0:
            traps.append((trap_val, "dc_calc_err"))
            used_values.add(trap_val)
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"{fmt(a)} {op} {fmt(b)} = ?",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b, "op": op, "result": result},
    }


def _gen_decimal_compare(decimal_places: int, whole_max: int, rng: random.Random) -> Dict[str, Any]:
    """Generate decimal comparison problems."""
    divisor = 10 ** decimal_places
    
    # Generate two close decimals
    base_whole = rng.randint(1, whole_max)
    a_frac = rng.randint(10, divisor - 1)
    b_frac = rng.randint(10, divisor - 1)
    
    # Make them have same whole part for challenge
    a = base_whole + a_frac / divisor
    b = base_whole + b_frac / divisor
    
    if a == b:
        b_frac += 10
        b = base_whole + b_frac / divisor
    
    def fmt(n):
        return f"{n:.{decimal_places}f}"
    
    greater = fmt(max(a, b))
    lesser = fmt(min(a, b))
    
    correct = greater
    
    # Trap: chose lesser
    traps = [
        (lesser, "dc_compare_err"),
    ]
    
    # Generate other close numbers
    used_values = {correct, lesser}
    other_vals = [
        fmt(base_whole + 0.1),
        fmt(base_whole + 0.9),
        fmt(base_whole + 1),
    ]
    for v in other_vals:
        if v not in used_values and len(traps) < 3:
            traps.append((v, "dc_compare_err"))
            used_values.add(v)
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"Which is greater: {fmt(a)} or {fmt(b)}?",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b},
    }


def _gen_decimal_conversion(decimal_places: int, rng: random.Random) -> Dict[str, Any]:
    """Generate decimal-fraction conversion problems."""
    # Simple conversions
    conversions = [
        (0.5, "1/2"),
        (0.25, "1/4"),
        (0.75, "3/4"),
        (0.1, "1/10"),
        (0.2, "1/5"),
        (0.4, "2/5"),
        (0.6, "3/5"),
        (0.8, "4/5"),
    ]
    
    decimal, correct_frac = rng.choice(conversions)
    
    # Build traps
    wrong_fracs = [c[1] for c in conversions if c[1] != correct_frac]
    rng.shuffle(wrong_fracs)
    
    traps = [(f, "dc_conv_err") for f in wrong_fracs[:3]]
    
    options_list = [(correct_frac, None)] + traps[:3]
    
    return {
        "stem": f"Write {decimal} as a fraction.",
        "correct_answer": correct_frac,
        "options": _shuffle_options(options_list, rng),
        "variables": {"decimal": decimal},
    }


def _gen_decimal_place_value(decimal_places: int, whole_max: int, rng: random.Random) -> Dict[str, Any]:
    """Generate decimal place value identification problems."""
    whole = rng.randint(0, whole_max)
    decimal_part = rng.randint(1, 10**decimal_places - 1)
    decimal_str = str(decimal_part).zfill(decimal_places)
    
    number = f"{whole}.{decimal_str}"
    
    # Pick a digit position to ask about
    position = rng.randint(0, decimal_places - 1)
    digit = decimal_str[position]
    
    place_names = ["tenths", "hundredths", "thousandths"]
    correct_place = place_names[position]
    
    # Build traps
    used = {correct_place}
    traps = []
    for name in place_names:
        if name not in used and len(traps) < 3:
            traps.append((name, "dc_place_err"))
            used.add(name)
    
    if len(traps) < 3:
        traps.append(("ones", "dc_place_err"))
    
    options_list = [(correct_place, None)] + traps[:3]
    
    return {
        "stem": f"In {number}, the digit {digit} is in which place?",
        "correct_answer": correct_place,
        "options": _shuffle_options(options_list, rng),
        "variables": {"number": number, "digit": digit},
    }


def _gen_ratios_percent(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Generate ratio/percent problems.
    
    Types:
    - Percent of a number: "What is 25% of 80?"
    - Percent to decimal/fraction: "Write 25% as a decimal"
    - Ratio problems: "Simplify the ratio 12:8"
    - Proportion problems: "If 2:5 = x:20, find x"
    """
    text_lower = competency_text.lower()
    
    # Check for percent patterns (handle both "percent" and "%")
    has_percent = "percent" in text_lower or "%" in competency_text
    has_of = " of " in text_lower
    
    if "ratio" in text_lower and "simplif" in text_lower:
        return _gen_ratio_simplify(rng)
    elif "ratio" in text_lower:
        return _gen_ratio_basic(rng)
    elif has_percent and has_of:
        return _gen_percent_of(rng)
    elif "proportion" in text_lower:
        return _gen_proportion(rng)
    else:
        return _gen_percent_convert(rng)


def _gen_percent_of(rng: random.Random) -> Dict[str, Any]:
    """What is X% of Y?"""
    percent = rng.choice([10, 20, 25, 50, 75, 100])
    whole = rng.choice([20, 40, 50, 60, 80, 100, 200])
    
    correct_val = (percent / 100) * whole
    correct = str(int(correct_val)) if correct_val == int(correct_val) else str(correct_val)
    
    # Build traps
    used = {correct}
    traps = []
    
    # Forgot to divide by 100
    wrong1 = str(int(percent * whole / 10))
    if wrong1 not in used:
        traps.append((wrong1, "rp_forgot_100"))
        used.add(wrong1)
    
    # Wrong calculation
    wrong2 = str(int(correct_val + whole * 0.1))
    if wrong2 not in used:
        traps.append((wrong2, "rp_calc_err"))
        used.add(wrong2)
    
    # Adjacent percent
    wrong3 = str(int(((percent + 10) / 100) * whole))
    if wrong3 not in used:
        traps.append((wrong3, "rp_pct_err"))
        used.add(wrong3)
    
    while len(traps) < 3:
        offset = rng.choice([5, 10, -5, -10])
        trap_val = str(int(correct_val + offset))
        if trap_val not in used and int(trap_val) > 0:
            traps.append((trap_val, "rp_calc_err"))
            used.add(trap_val)
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"What is {percent}% of {whole}?",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"percent": percent, "whole": whole},
    }


def _gen_percent_convert(rng: random.Random) -> Dict[str, Any]:
    """Convert percent to decimal."""
    percent = rng.choice([10, 20, 25, 50, 75])
    decimal = percent / 100
    
    correct = str(decimal)
    
    # Build unique traps
    used = {correct}
    traps = []
    
    # Didn't divide by 100
    wrong1 = str(percent)
    if wrong1 not in used:
        traps.append((wrong1, "rp_forgot_100"))
        used.add(wrong1)
    
    # Wrong decimal shift
    wrong2 = str(decimal * 10)
    if wrong2 not in used:
        traps.append((wrong2, "rp_decimal_shift"))
        used.add(wrong2)
    
    # Complement
    wrong3 = str(1 - decimal)
    if wrong3 not in used:
        traps.append((wrong3, "rp_complement"))
        used.add(wrong3)
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"Write {percent}% as a decimal.",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"percent": percent},
    }


def _gen_ratio_basic(rng: random.Random) -> Dict[str, Any]:
    """Basic ratio: Express as ratio."""
    a = rng.randint(2, 10)
    b = rng.randint(2, 10)
    
    correct = f"{a}:{b}"
    
    traps = [
        (f"{b}:{a}", "rp_ratio_swap"),  # Swapped
        (f"{a}:{b+1}", "rp_ratio_err"),
        (f"{a+1}:{b}", "rp_ratio_err"),
    ]
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"In a class with {a} boys and {b} girls, what is the ratio of boys to girls?",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b},
    }


def _gen_ratio_simplify(rng: random.Random) -> Dict[str, Any]:
    """Simplify a ratio."""
    # Generate a ratio that can be simplified
    gcd_val = rng.choice([2, 3, 4, 5])
    a = rng.randint(1, 5)
    b = rng.randint(1, 5)
    if a == b:
        b = a + 1
    
    # Original ratio (not simplified)
    orig_a = a * gcd_val
    orig_b = b * gcd_val
    
    correct = f"{a}:{b}"
    
    # Build unique traps
    used = {correct}
    traps = []
    
    # Not simplified (original)
    trap1 = f"{orig_a}:{orig_b}"
    if trap1 not in used:
        traps.append((trap1, "rp_not_simplified"))
        used.add(trap1)
    
    # Partially simplified
    if gcd_val >= 4:
        half_gcd = gcd_val // 2
        trap2 = f"{orig_a // half_gcd}:{orig_b // half_gcd}"
        if trap2 not in used:
            traps.append((trap2, "rp_partial_simplify"))
            used.add(trap2)
    
    # Swapped
    trap3 = f"{b}:{a}"
    if trap3 not in used:
        traps.append((trap3, "rp_ratio_swap"))
        used.add(trap3)
    
    # Wrong simplification
    while len(traps) < 3:
        wrong_a = a + rng.choice([1, -1]) if a > 1 else a + 1
        wrong_b = b
        trap = f"{wrong_a}:{wrong_b}"
        if trap not in used:
            traps.append((trap, "rp_simplify_err"))
            used.add(trap)
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"Simplify the ratio {orig_a}:{orig_b}",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"orig_a": orig_a, "orig_b": orig_b, "a": a, "b": b},
    }


def _gen_proportion(rng: random.Random) -> Dict[str, Any]:
    """Solve a proportion: a:b = x:d"""
    a = rng.randint(2, 5)
    b = rng.randint(2, 5)
    multiplier = rng.randint(2, 4)
    
    d = b * multiplier
    x = a * multiplier  # Correct answer
    
    correct = str(x)
    
    # Build unique traps
    used = {correct}
    traps = []
    
    # Added instead of multiplied
    trap1 = str(a + (d - b))
    if trap1 not in used:
        traps.append((trap1, "rp_add_not_mult"))
        used.add(trap1)
    
    # Off by one
    trap2 = str(x + 1)
    if trap2 not in used:
        traps.append((trap2, "rp_off_one"))
        used.add(trap2)
    
    trap3 = str(x - 1)
    if trap3 not in used and x > 1:
        traps.append((trap3, "rp_off_one"))
        used.add(trap3)
    
    while len(traps) < 3:
        offset = rng.choice([2, -2, multiplier])
        trap = str(x + offset)
        if trap not in used and int(trap) > 0:
            traps.append((trap, "rp_calc_err"))
            used.add(trap)
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"If {a}:{b} = x:{d}, find x.",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b, "d": d, "x": x},
    }


def _gen_algebra(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """Generate algebra problems - placeholder."""
    a = rng.randint(2, 10)
    b = rng.randint(1, 10)
    x = rng.randint(1, 10)
    result = a * x + b
    
    correct = str(x)
    
    traps = [
        (str(x + 1), "alg_wrong_inv"),
        (str(result - a), "alg_wrong_inv"),
        (str(x - 1), "ar_off_one"),
    ]
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": f"Solve for x: {a}x + {b} = {result}",
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b, "x": x},
    }


def _gen_geometry_props(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Generate geometry property problems based on competency.
    
    Sub-generators:
    - Circles / half circles / quarter circles (curved vs straight)
    - Compose and decompose shapes
    - Translations (slides) on a grid
    - Line types: point, line, line segment, ray
    - Line relations: parallel, intersecting, perpendicular
    - Symmetry identification and counting
    - 3D surfaces: straight/curved, flat/curved
    - Shape properties (sides, corners) — default
    """
    text_lower = competency_text.lower()
    
    # Compose/decompose takes priority (even if text mentions circles)
    if "compose" in text_lower or "decompose" in text_lower:
        return _gen_geo_compose_shapes(grade, rng)
    elif "circle" in text_lower and ("half" in text_lower or "quarter" in text_lower):
        return _gen_geo_circles(grade, rng)
    elif "translation" in text_lower or "slide" in text_lower:
        return _gen_geo_translations(grade, rng, text_lower)
    elif "symmetr" in text_lower:
        return _gen_geo_symmetry(grade, rng, text_lower)
    elif "line segment" in text_lower or "ray" in text_lower or ("point" in text_lower and "line" in text_lower):
        return _gen_geo_line_types(grade, rng)
    elif "parallel" in text_lower or "perpendicular" in text_lower or "intersect" in text_lower:
        return _gen_geo_line_relations(grade, rng)
    elif ("straight" in text_lower and "curved" in text_lower) or ("flat" in text_lower and "curved" in text_lower):
        return _gen_geo_surfaces(grade, rng, text_lower)
    elif "compare" in text_lower and "distinguish" in text_lower:
        return _gen_geo_compare_shapes(grade, rng)
    elif "identify" in text_lower:
        return _gen_geo_identify(grade, rng)
    else:
        return _gen_geo_properties_default(grade, rng)


def _gen_geo_circles(grade: int, rng: random.Random) -> Dict[str, Any]:
    """Circles, half circles, quarter circles — curved vs straight edges."""
    question_bank = [
        {
            "stems": [
                "How many straight edges does a circle have?",
                "A circle has ___ straight sides.",
                "Count the straight edges of a circle.",
            ],
            "correct": "0",
            "traps": [("1", "gp_curve_as_side"), ("2", "gp_wrong_count"), ("infinite", "gp_confused")],
        },
        {
            "stems": [
                "How many straight edges does a half circle have?",
                "A half circle (semicircle) has ___ straight edge(s).",
                "Count the straight edges of a semicircle.",
            ],
            "correct": "1",
            "traps": [("0", "gp_forgot_diameter"), ("2", "gp_counted_curve"), ("3", "gp_wrong_count")],
        },
        {
            "stems": [
                "How many straight edges does a quarter circle have?",
                "A quarter circle has ___ straight edge(s).",
                "Count the straight sides of a quarter circle.",
            ],
            "correct": "2",
            "traps": [("1", "gp_forgot_one"), ("0", "gp_forgot_all"), ("4", "gp_quarter_of_four")],
        },
        {
            "stems": [
                "Which shape has NO straight edges?",
                "Which of these shapes has only curved edges?",
                "Identify the shape with zero straight sides.",
            ],
            "correct": "circle",
            "traps": [("half circle", "gp_has_diameter"), ("quarter circle", "gp_has_radii"), ("oval", "gp_not_circle")],
        },
        {
            "stems": [
                "A quarter circle looks like a slice of:",
                "Which everyday object looks like a quarter circle?",
                "A quarter circle resembles a:",
            ],
            "correct": "pizza slice",
            "traps": [("full pie", "gp_whole_not_quarter"), ("rectangle", "gp_wrong_shape"), ("triangle", "gp_close_but_curved")],
        },
        {
            "stems": [
                "How many curved edges does a half circle have?",
                "A semicircle has ___ curved edge(s).",
                "Count the curved edges of a half circle.",
            ],
            "correct": "1",
            "traps": [("2", "gp_counted_straight"), ("0", "gp_forgot_curve"), ("3", "gp_wrong_count")],
        },
    ]
    
    q = rng.choice(question_bank)
    stem = rng.choice(q["stems"])
    options_list = [(q["correct"], None)] + q["traps"][:3]
    
    return {
        "stem": stem,
        "correct_answer": q["correct"],
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "circles"},
    }


def _gen_geo_compose_shapes(grade: int, rng: random.Random) -> Dict[str, Any]:
    """Compose and decompose composite figures."""
    question_bank = [
        {
            "stems": [
                "Two triangles can be put together to make a:",
                "If you join two identical right triangles, you can form a:",
                "Combining two equal triangles along their longest side makes a:",
            ],
            "correct": "rectangle",
            "traps": [("circle", "gp_wrong_shape"), ("triangle", "gp_same_shape"), ("pentagon", "gp_wrong_shape")],
        },
        {
            "stems": [
                "A rectangle can be cut into two equal:",
                "If you cut a rectangle diagonally, you get two:",
                "Dividing a rectangle with a diagonal line gives:",
            ],
            "correct": "triangles",
            "traps": [("squares", "gp_wrong_shape"), ("circles", "gp_wrong_shape"), ("rectangles", "gp_wrong_decomp")],
        },
        {
            "stems": [
                "Four small squares can be arranged to make a:",
                "Putting 4 equal squares together (2 by 2) forms a:",
                "If you combine 4 unit squares in a 2x2 grid, you get a:",
            ],
            "correct": "larger square",
            "traps": [("rectangle", "gp_close_shape"), ("triangle", "gp_wrong_shape"), ("circle", "gp_wrong_shape")],
        },
        {
            "stems": [
                "How many triangles can a square be divided into by cutting both diagonals?",
                "If you draw both diagonals of a square, how many triangles are formed?",
                "Cutting a square along both diagonals creates ___ triangles.",
            ],
            "correct": "4",
            "traps": [("2", "gp_one_diagonal"), ("3", "gp_off_one"), ("6", "gp_too_many")],
        },
        {
            "stems": [
                "A square and a triangle placed side by side can look like a:",
                "Combining a square with a triangle on top makes the shape of a:",
                "A triangle on top of a square resembles a:",
            ],
            "correct": "house (pentagon)",
            "traps": [("rectangle", "gp_wrong_shape"), ("hexagon", "gp_too_many_sides"), ("triangle", "gp_wrong_shape")],
        },
        {
            "stems": [
                "Two rectangles placed end-to-end make a:",
                "Joining two identical rectangles along their shorter side creates a:",
                "Combine two equal rectangles side by side to form a:",
            ],
            "correct": "longer rectangle",
            "traps": [("square", "gp_not_always"), ("L-shape", "gp_wrong_arrangement"), ("triangle", "gp_wrong_shape")],
        },
        {
            "stems": [
                "An L-shape can be decomposed into:",
                "An L-shaped figure is made up of:",
                "You can break an L-shape into:",
            ],
            "correct": "2 rectangles",
            "traps": [("1 rectangle", "gp_too_few"), ("3 rectangles", "gp_too_many"), ("2 triangles", "gp_wrong_shape")],
        },
        {
            "stems": [
                "How many squares make up a 2x3 rectangle?",
                "A rectangle that is 2 squares wide and 3 squares long contains ___ squares.",
                "Count the unit squares inside a 2 by 3 rectangle.",
            ],
            "correct": "6",
            "traps": [("5", "gp_off_one"), ("8", "gp_added_perimeter"), ("10", "gp_wrong_mult")],
        },
    ]
    
    q = rng.choice(question_bank)
    stem = rng.choice(q["stems"])
    options_list = [(q["correct"], None)] + q["traps"][:3]
    
    return {
        "stem": stem,
        "correct_answer": q["correct"],
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "compose_shapes"},
    }


def _gen_geo_translations(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Describe the effect of slides (translations) on shapes."""
    is_two_direction = "two" in text_lower or "multi" in text_lower
    
    # Generate starting position
    start_x = rng.randint(1, 6)
    start_y = rng.randint(1, 6)
    
    directions = ["right", "left", "up", "down"]
    
    if is_two_direction:
        # Two-direction slide
        dx = rng.randint(1, 4)
        dy = rng.randint(1, 4)
        dir_h = rng.choice(["right", "left"])
        dir_v = rng.choice(["up", "down"])
        
        end_x = start_x + dx if dir_h == "right" else start_x - dx
        end_y = start_y + dy if dir_v == "up" else start_y - dy
        
        stems = [
            f"A shape is at ({start_x}, {start_y}). It slides {dx} units {dir_h} and {dy} units {dir_v}. Where is it now?",
            f"Start at ({start_x}, {start_y}). Move {dx} {dir_h}, then {dy} {dir_v}. New position?",
            f"Translate the point ({start_x}, {start_y}) by {dx} {dir_h} and {dy} {dir_v}. Result?",
        ]
        correct = f"({end_x}, {end_y})"
        traps = [
            (f"({start_x + dx}, {start_y + dy})", "gp_ignored_direction"),
            (f"({end_y}, {end_x})", "gp_swapped_xy"),
            (f"({start_x}, {start_y})", "gp_no_move"),
        ]
    else:
        # Single-direction slide
        direction = rng.choice(directions)
        distance = rng.randint(1, 5)
        
        if direction == "right":
            end_x, end_y = start_x + distance, start_y
        elif direction == "left":
            end_x, end_y = start_x - distance, start_y
        elif direction == "up":
            end_x, end_y = start_x, start_y + distance
        else:
            end_x, end_y = start_x, start_y - distance
        
        stems = [
            f"A shape is at ({start_x}, {start_y}). It slides {distance} units {direction}. Where is it now?",
            f"Start at position ({start_x}, {start_y}). Move {distance} squares {direction}. New position?",
            f"After sliding {distance} units {direction} from ({start_x}, {start_y}), the shape is at:",
        ]
        correct = f"({end_x}, {end_y})"
        
        # Generate plausible wrong answers
        wrong_opposite = f"({start_x - distance if direction == 'right' else start_x + distance}, {start_y})" if direction in ["right", "left"] else f"({start_x}, {start_y - distance if direction == 'up' else start_y + distance})"
        wrong_both = f"({start_x + distance}, {start_y + distance})"
        
        traps = [
            (wrong_opposite, "gp_wrong_direction"),
            (wrong_both, "gp_moved_both_axes"),
            (f"({start_x}, {start_y})", "gp_no_move"),
        ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"start": (start_x, start_y), "sub_type": "translations"},
    }


def _gen_geo_line_types(grade: int, rng: random.Random) -> Dict[str, Any]:
    """Identify point, line, line segment, and ray."""
    question_bank = [
        {
            "stems": [
                "Which has exactly two endpoints?",
                "This has a start point and an end point. It is a:",
                "A straight path with two endpoints is called a:",
            ],
            "correct": "line segment",
            "traps": [("ray", "gp_one_endpoint"), ("line", "gp_no_endpoints"), ("point", "gp_confused")],
        },
        {
            "stems": [
                "Which extends forever in ONE direction from a single point?",
                "This starts at a point and goes on forever in one direction. It is a:",
                "A ___ has one endpoint and extends infinitely in one direction.",
            ],
            "correct": "ray",
            "traps": [("line", "gp_both_directions"), ("line segment", "gp_two_endpoints"), ("point", "gp_confused")],
        },
        {
            "stems": [
                "Which extends forever in BOTH directions?",
                "This has no endpoints and goes on forever. It is a:",
                "A ___ extends infinitely in both directions.",
            ],
            "correct": "line",
            "traps": [("ray", "gp_one_direction"), ("line segment", "gp_has_endpoints"), ("point", "gp_confused")],
        },
        {
            "stems": [
                "Which has no length, width, or height?",
                "An exact location in space with no size is called a:",
                "A ___ marks a position but has no dimensions.",
            ],
            "correct": "point",
            "traps": [("line segment", "gp_has_length"), ("ray", "gp_has_length"), ("line", "gp_has_length")],
        },
        {
            "stems": [
                "How many endpoints does a ray have?",
                "A ray has ___ endpoint(s).",
                "Count the endpoints of a ray.",
            ],
            "correct": "1",
            "traps": [("0", "gp_no_endpoints"), ("2", "gp_confused_segment"), ("infinite", "gp_confused")],
        },
        {
            "stems": [
                "How many endpoints does a line have?",
                "A line has ___ endpoint(s).",
                "Count the endpoints of a line.",
            ],
            "correct": "0",
            "traps": [("1", "gp_confused_ray"), ("2", "gp_confused_segment"), ("infinite", "gp_confused")],
        },
    ]
    
    q = rng.choice(question_bank)
    stem = rng.choice(q["stems"])
    options_list = [(q["correct"], None)] + q["traps"][:3]
    
    return {
        "stem": stem,
        "correct_answer": q["correct"],
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "line_types"},
    }


def _gen_geo_line_relations(grade: int, rng: random.Random) -> Dict[str, Any]:
    """Parallel, intersecting, and perpendicular lines."""
    question_bank = [
        {
            "stems": [
                "Lines that never meet (no matter how far extended) are called:",
                "Two lines that stay the same distance apart and never cross are:",
                "Railroad tracks are an example of ___ lines.",
            ],
            "correct": "parallel",
            "traps": [("perpendicular", "gp_perp_parallel"), ("intersecting", "gp_inter_parallel"), ("diagonal", "gp_wrong_term")],
        },
        {
            "stems": [
                "Lines that cross at a right angle (90 degrees) are called:",
                "Two lines that intersect and form a square corner are:",
                "The corner of a book shows ___ lines.",
            ],
            "correct": "perpendicular",
            "traps": [("parallel", "gp_parallel_perp"), ("intersecting", "gp_too_general"), ("diagonal", "gp_wrong_term")],
        },
        {
            "stems": [
                "Lines that cross at any point are called:",
                "Two lines that share a common point are:",
                "When two lines meet at a point, they are ___ lines.",
            ],
            "correct": "intersecting",
            "traps": [("parallel", "gp_parallel_inter"), ("perpendicular", "gp_too_specific"), ("adjacent", "gp_wrong_term")],
        },
        {
            "stems": [
                "Which is an example of parallel lines?",
                "Which shows parallel lines in real life?",
                "Identify the pair of parallel lines:",
            ],
            "correct": "opposite edges of a ruler",
            "traps": [("the letter X", "gp_intersecting"), ("the corner of a wall", "gp_perpendicular"), ("a zigzag path", "gp_wrong_example")],
        },
        {
            "stems": [
                "Are perpendicular lines also intersecting?",
                "All perpendicular lines are also:",
                "Perpendicular lines always ___ each other.",
            ],
            "correct": "yes, they intersect at 90 degrees",
            "traps": [("no, they are different", "gp_exclusive"), ("only sometimes", "gp_partial"), ("they are parallel", "gp_confused")],
        },
        {
            "stems": [
                "The plus sign (+) shows two lines that are:",
                "In the symbol +, the lines are:",
                "What type of lines does the + symbol show?",
            ],
            "correct": "perpendicular",
            "traps": [("parallel", "gp_parallel_perp"), ("intersecting but not perpendicular", "gp_too_general"), ("curved", "gp_wrong_type")],
        },
    ]
    
    q = rng.choice(question_bank)
    stem = rng.choice(q["stems"])
    options_list = [(q["correct"], None)] + q["traps"][:3]
    
    return {
        "stem": stem,
        "correct_answer": q["correct"],
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "line_relations"},
    }


def _gen_geo_symmetry(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Line symmetry identification and counting."""
    is_complete = "complete" in text_lower
    is_count = "how many" in text_lower or "number" in text_lower
    
    if is_complete:
        # "Complete a symmetric figure" — MCQ version
        question_bank = [
            {
                "stems": [
                    "A shape has the left half: a vertical line with a bump on the left. What does the right half look like?",
                    "If a figure is symmetric about a vertical line, the right side is a ___ of the left side.",
                    "To complete a symmetric figure, you create a ___ image.",
                ],
                "correct": "mirror image of the left",
                "traps": [("copy of the left (same direction)", "gp_not_reflected"), ("rotated version", "gp_rotation_not_reflection"), ("blank (nothing)", "gp_no_completion")],
            },
        ]
    else:
        question_bank = [
            {
                "stems": [
                    "How many lines of symmetry does a square have?",
                    "A square has ___ line(s) of symmetry.",
                    "Count the lines of symmetry in a square.",
                ],
                "correct": "4",
                "traps": [("2", "gp_only_hv"), ("1", "gp_only_one"), ("8", "gp_counted_corners")],
            },
            {
                "stems": [
                    "How many lines of symmetry does a rectangle (not square) have?",
                    "A rectangle has ___ line(s) of symmetry.",
                    "Count the lines of symmetry in a non-square rectangle.",
                ],
                "correct": "2",
                "traps": [("4", "gp_thought_square"), ("1", "gp_only_one"), ("0", "gp_no_sym")],
            },
            {
                "stems": [
                    "How many lines of symmetry does an equilateral triangle have?",
                    "An equilateral triangle has ___ line(s) of symmetry.",
                    "Count the lines of symmetry in an equilateral triangle.",
                ],
                "correct": "3",
                "traps": [("1", "gp_only_vertical"), ("2", "gp_off_one"), ("6", "gp_counted_sides_and_vertices")],
            },
            {
                "stems": [
                    "Does a scalene triangle have any lines of symmetry?",
                    "How many lines of symmetry does a scalene triangle have?",
                    "A triangle with all different side lengths has ___ line(s) of symmetry.",
                ],
                "correct": "0",
                "traps": [("1", "gp_assumed_one"), ("2", "gp_wrong"), ("3", "gp_confused_equilateral")],
            },
            {
                "stems": [
                    "How many lines of symmetry does a circle have?",
                    "A circle has ___ line(s) of symmetry.",
                    "The number of lines of symmetry in a circle is:",
                ],
                "correct": "infinite",
                "traps": [("1", "gp_only_one"), ("4", "gp_limited"), ("0", "gp_no_sym")],
            },
            {
                "stems": [
                    "Which letter has exactly one line of symmetry: A, H, S, or N?",
                    "Identify the letter with exactly 1 line of symmetry:",
                    "Which of these has only one line of symmetry?",
                ],
                "correct": "A",
                "traps": [("H", "gp_has_two"), ("S", "gp_rotational_not_line"), ("N", "gp_no_line_sym")],
            },
            {
                "stems": [
                    "Which shape does NOT have line symmetry?",
                    "Identify the shape with no lines of symmetry:",
                    "Which has zero lines of symmetry?",
                ],
                "correct": "a parallelogram (not rectangle)",
                "traps": [("square", "gp_has_four"), ("circle", "gp_has_infinite"), ("equilateral triangle", "gp_has_three")],
            },
        ]
    
    q = rng.choice(question_bank)
    stem = rng.choice(q["stems"])
    options_list = [(q["correct"], None)] + q["traps"][:3]
    
    return {
        "stem": stem,
        "correct_answer": q["correct"],
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "symmetry"},
    }


def _gen_geo_surfaces(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Identify straight/curved lines and flat/curved surfaces of 3D objects."""
    question_bank = [
        {
            "stems": [
                "How many flat surfaces does a sphere (ball) have?",
                "A ball has ___ flat surface(s).",
                "Count the flat faces of a sphere.",
            ],
            "correct": "0",
            "traps": [("1", "gp_one_face"), ("2", "gp_two_faces"), ("infinite", "gp_confused")],
        },
        {
            "stems": [
                "How many flat surfaces does a cylinder (can) have?",
                "A can has ___ flat surface(s).",
                "Count the flat faces of a cylinder.",
            ],
            "correct": "2",
            "traps": [("1", "gp_forgot_bottom"), ("0", "gp_only_curved"), ("3", "gp_counted_curved")],
        },
        {
            "stems": [
                "How many curved surfaces does a cylinder have?",
                "A cylinder has ___ curved surface(s).",
                "Count the curved faces of a can.",
            ],
            "correct": "1",
            "traps": [("2", "gp_counted_flat"), ("0", "gp_forgot_curved"), ("3", "gp_all_surfaces")],
        },
        {
            "stems": [
                "How many curved surfaces does a cube have?",
                "A cube (like a box) has ___ curved surface(s).",
                "Does a cube have any curved faces?",
            ],
            "correct": "0",
            "traps": [("1", "gp_edge_curved"), ("6", "gp_counted_flat"), ("4", "gp_wrong_count")],
        },
        {
            "stems": [
                "A cone has how many flat surface(s)?",
                "Count the flat faces of a cone.",
                "How many flat surfaces does an ice cream cone shape have?",
            ],
            "correct": "1",
            "traps": [("0", "gp_only_curved"), ("2", "gp_counted_tip"), ("3", "gp_wrong_count")],
        },
        {
            "stems": [
                "Which 3D shape has ONLY flat surfaces?",
                "Which solid has no curved surfaces at all?",
                "Identify the shape with only flat faces:",
            ],
            "correct": "cube",
            "traps": [("cylinder", "gp_has_curved"), ("sphere", "gp_all_curved"), ("cone", "gp_has_curved")],
        },
        {
            "stems": [
                "The edge of a coin is an example of a:",
                "The rim of a plate shows a:",
                "The outline of a wheel is a:",
            ],
            "correct": "curved line",
            "traps": [("straight line", "gp_wrong_type"), ("point", "gp_confused"), ("flat surface", "gp_confused_2d_3d")],
        },
        {
            "stems": [
                "The edge of a ruler is an example of a:",
                "The side of a book shows a:",
                "A door frame contains examples of:",
            ],
            "correct": "straight line",
            "traps": [("curved line", "gp_wrong_type"), ("point", "gp_confused"), ("curved surface", "gp_confused_2d_3d")],
        },
    ]
    
    q = rng.choice(question_bank)
    stem = rng.choice(q["stems"])
    options_list = [(q["correct"], None)] + q["traps"][:3]
    
    return {
        "stem": stem,
        "correct_answer": q["correct"],
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "surfaces"},
    }


def _gen_geo_compare_shapes(grade: int, rng: random.Random) -> Dict[str, Any]:
    """Compare and distinguish shapes by sides/corners."""
    shapes_2d = [
        ("triangle", 3, 3),
        ("square", 4, 4),
        ("rectangle", 4, 4),
        ("pentagon", 5, 5),
        ("hexagon", 6, 6),
        ("circle", 0, 0),
    ]
    
    shape1, sides1, corners1 = rng.choice(shapes_2d)
    shape2, sides2, corners2 = rng.choice([s for s in shapes_2d if s[0] != shape1])
    
    if rng.random() < 0.5 and sides1 != sides2:
        # Compare sides
        if sides1 > sides2:
            correct = shape1
        else:
            correct = shape2
        
        stems = [
            f"Which shape has more sides: a {shape1} or a {shape2}?",
            f"Between a {shape1} and a {shape2}, which has more sides?",
            f"Compare: Does a {shape1} or {shape2} have more sides?",
        ]
        other = shape2 if correct == shape1 else shape1
        traps = [
            (other, "gp_wrong_compare"),
            ("they have the same", "gp_wrong_equal"),
            ("cannot tell", "gp_no_answer"),
        ]
    else:
        # Compare corners
        if corners1 > corners2:
            correct = shape1
        elif corners2 > corners1:
            correct = shape2
        else:
            correct = "they have the same"
        
        stems = [
            f"Which shape has more corners: a {shape1} or a {shape2}?",
            f"Between a {shape1} and a {shape2}, which has more corners (vertices)?",
            f"Compare corners: {shape1} vs {shape2}. Which has more?",
        ]
        if correct == "they have the same":
            traps = [
                (shape1, "gp_wrong_compare"),
                (shape2, "gp_wrong_compare"),
                ("neither", "gp_wrong_term"),
            ]
        else:
            other = shape2 if correct == shape1 else shape1
            traps = [
                (other, "gp_wrong_compare"),
                ("they have the same", "gp_wrong_equal"),
                ("cannot tell", "gp_no_answer"),
            ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"shape1": shape1, "shape2": shape2, "sub_type": "compare_shapes"},
    }


def _gen_geo_identify(grade: int, rng: random.Random) -> Dict[str, Any]:
    """Identify shapes by their properties."""
    shapes_2d = [
        ("triangle", 3, 3),
        ("square", 4, 4),
        ("rectangle", 4, 4),
        ("pentagon", 5, 5),
        ("hexagon", 6, 6),
    ]
    
    shape, sides, corners = rng.choice(shapes_2d)
    
    stems = [
        f"Which shape has {sides} sides and {corners} corners?",
        f"Name the shape with exactly {sides} sides.",
        f"A shape with {sides} straight sides is called a:",
    ]
    
    correct = shape
    other_shapes = [s[0] for s in shapes_2d if s[0] != shape]
    traps = [(s, "gp_wrong_shape") for s in rng.sample(other_shapes, min(3, len(other_shapes)))]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"shape": shape, "sides": sides, "sub_type": "identify"},
    }


def _gen_geo_properties_default(grade: int, rng: random.Random) -> Dict[str, Any]:
    """Default: ask about shape properties (sides/corners)."""
    shapes_2d = [
        ("triangle", 3, 3),
        ("square", 4, 4),
        ("rectangle", 4, 4),
        ("pentagon", 5, 5),
        ("hexagon", 6, 6),
    ]
    
    shape, sides, corners = rng.choice(shapes_2d)
    
    if rng.random() < 0.5:
        # Ask about sides
        stems = [
            f"How many sides does a {shape} have?",
            f"Count the sides of a {shape}.",
            f"A {shape} has ___ sides.",
        ]
        correct = str(sides)
        traps = [
            (str(sides + 1), "gp_off_one_up"),
            (str(sides - 1), "gp_off_one_down"),
            (str(sides + 2), "gp_wrong_shape_sides"),
        ]
    else:
        # Ask about corners
        stems = [
            f"How many corners (vertices) does a {shape} have?",
            f"Count the corners of a {shape}.",
            f"A {shape} has ___ corners.",
        ]
        correct = str(corners)
        traps = [
            (str(corners + 1), "gp_off_one_up"),
            (str(corners - 1), "gp_off_one_down"),
            (str(corners * 2), "gp_doubled"),
        ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"shape": shape, "sides": sides, "sub_type": "properties_default"},
    }


def _gen_measurement(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Generate measurement problems based on competency.
    
    Sub-generators:
    - Length conversion (m ↔ cm)
    - Unit selection (appropriate unit for object)
    - Length comparison
    - Length word problems
    - Perimeter (triangles, squares, rectangles)
    - Area (squares, rectangles) — Grade 3+
    - Mass (g, kg, mg)
    - Capacity (L, mL)
    - Time/Duration (days, weeks, elapsed time)
    - Estimation (reasonable estimates for real objects)
    """
    text_lower = competency_text.lower()

    # Honour explicit measurement_type axis override before text routing
    mt_override = dimensions.get("measurement_type")
    if mt_override == "mass":
        return _gen_meas_mass(grade, rng, text_lower)
    elif mt_override == "capacity":
        return _gen_meas_capacity(grade, rng, text_lower)

    if "perimeter" in text_lower:
        return _gen_meas_perimeter(grade, rng, text_lower)
    elif "area" in text_lower:
        return _gen_meas_area(grade, rng, text_lower)
    elif any(w in text_lower for w in ["mass", "kilogram", "gram", "milligram", "weigh", "balance"]):
        return _gen_meas_mass(grade, rng, text_lower)
    elif any(w in text_lower for w in ["capacity", "liter", "milliliter"]):
        return _gen_meas_capacity(grade, rng, text_lower)
    elif any(w in text_lower for w in ["duration", "elapsed", "hour", "minute", "day", "week", "timetable"]):
        return _gen_meas_time(grade, rng, text_lower)
    elif "estimate" in text_lower:
        return _gen_meas_estimation(grade, rng, text_lower)
    elif "appropriate" in text_lower or "identify.*unit" in text_lower:
        return _gen_meas_unit_selection(grade, rng, text_lower)
    elif "compare" in text_lower:
        return _gen_meas_compare(grade, rng, text_lower)
    elif "solve" in text_lower or "problem" in text_lower:
        return _gen_meas_word_problem(grade, rng, text_lower)
    else:
        return _gen_meas_length_convert(grade, rng)


def _gen_meas_length_convert(grade: int, rng: random.Random) -> Dict[str, Any]:
    """Convert between meters and centimeters."""
    stems = [
        lambda m, cm: f"Convert {m} meters to centimeters.",
        lambda m, cm: f"How many centimeters are in {m} meters?",
        lambda m, cm: f"{m} m = ___ cm",
    ]
    
    meters = rng.randint(1, 10)
    cm = meters * 100
    correct = str(cm)
    
    traps = [
        (str(meters * 10), "ms_wrong_factor"),
        (str(meters * 1000), "ms_wrong_factor"),
        (str(meters), "ms_no_convert"),
    ]
    
    stem_fn = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem_fn(meters, cm),
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"meters": meters, "cm": cm, "sub_type": "length_convert"},
    }


def _gen_meas_unit_selection(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Choose appropriate unit (m or cm) for measuring an object."""
    # Objects with their appropriate units
    objects_cm = [
        ("a pencil", 15), ("an eraser", 5), ("a book", 25),
        ("a hand span", 20), ("a crayon", 10), ("a spoon", 18),
    ]
    objects_m = [
        ("a classroom", 8), ("a swimming pool", 25), ("a basketball court", 28),
        ("a hallway", 15), ("a flagpole", 10), ("a school bus", 12),
    ]
    
    stems = [
        lambda obj, unit: f"Which unit is better for measuring the length of {obj}: meters or centimeters?",
        lambda obj, unit: f"To measure {obj}, should you use meters (m) or centimeters (cm)?",
        lambda obj, unit: f"The most appropriate unit for measuring {obj} is:",
    ]
    
    if rng.random() < 0.5:
        obj, _ = rng.choice(objects_cm)
        correct = "centimeters"
        wrong = "meters"
    else:
        obj, _ = rng.choice(objects_m)
        correct = "meters"
        wrong = "centimeters"
    
    traps = [
        (wrong, "ms_wrong_unit"),
        ("kilometers", "ms_unit_too_big"),
        ("millimeters", "ms_unit_too_small"),
    ]
    
    stem_fn = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem_fn(obj, correct),
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"object": obj, "correct_unit": correct, "sub_type": "unit_selection"},
    }


def _gen_meas_compare(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Compare lengths that require unit conversion."""
    stems = [
        lambda a, au, b, bu: f"Which is longer: {a} {au} or {b} {bu}?",
        lambda a, au, b, bu: f"Compare: {a} {au} and {b} {bu}. Which is greater?",
        lambda a, au, b, bu: f"A ribbon is {a} {au} long. A rope is {b} {bu} long. Which is longer?",
    ]
    
    # Generate values where conversion is needed
    cm_val = rng.randint(50, 300)
    m_val = rng.randint(1, 4)
    m_in_cm = m_val * 100
    
    if cm_val > m_in_cm:
        correct = f"{cm_val} cm"
        wrong = f"{m_val} m"
    else:
        correct = f"{m_val} m"
        wrong = f"{cm_val} cm"
    
    traps = [
        (wrong, "ms_no_convert"),
        ("they are equal", "ms_wrong_equal"),
        ("cannot tell", "ms_no_answer"),
    ]
    
    stem_fn = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem_fn(cm_val, "cm", m_val, "m"),
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"cm_val": cm_val, "m_val": m_val, "sub_type": "compare"},
    }


def _gen_meas_word_problem(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Solve word problems involving length and distance."""
    max_val = 100 if grade <= 2 else 1000
    
    problem_templates = [
        {
            "stem": "A rope is {total} cm long. You cut off {part} cm. How much is left?",
            "gen": lambda rng, mx: (rng.randint(20, mx), rng.randint(5, 0)),
            "op": "subtract",
        },
        {
            "stem": "A path is {a} m long. Another path is {b} m long. What is the total distance?",
            "op": "add",
        },
        {
            "stem": "A garden is {total} m around. One side is {part} m. The other 3 sides together are how many meters?",
            "op": "subtract",
        },
    ]
    
    # Generate add or subtract problem
    if rng.random() < 0.5:
        # Addition
        a = rng.randint(10, max_val // 2)
        b = rng.randint(10, max_val // 2)
        total = a + b
        unit = "cm" if max_val <= 100 else rng.choice(["cm", "m"])
        
        stems = [
            f"A path is {a} {unit} long. Another path is {b} {unit} long. What is the total distance?",
            f"A piece of string is {a} {unit}. Another piece is {b} {unit}. How long are they together?",
            f"You walk {a} {unit} then {b} {unit} more. How far did you walk in total?",
        ]
        correct = str(total)
        traps = [
            (str(abs(a - b)), "ms_wrong_op"),
            (str(total + 10), "ms_off_by"),
            (str(max(a, b)), "ms_partial"),
        ]
    else:
        # Subtraction
        total = rng.randint(20, max_val)
        part = rng.randint(5, total - 5)
        remaining = total - part
        unit = "cm" if max_val <= 100 else rng.choice(["cm", "m"])
        
        stems = [
            f"A rope is {total} {unit} long. You cut off {part} {unit}. How much is left?",
            f"A board is {total} {unit}. After cutting {part} {unit}, what length remains?",
            f"You have {total} {unit} of ribbon. You use {part} {unit}. How much is left?",
        ]
        correct = str(remaining)
        traps = [
            (str(total + part), "ms_wrong_op"),
            (str(remaining + 1), "ms_off_one"),
            (str(part), "ms_partial"),
        ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "word_problem"},
    }


def _gen_meas_perimeter(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Find perimeter of triangles, squares, and rectangles."""
    # Determine if it's a "find missing side" problem
    is_missing_side = "missing" in text_lower or "solve" in text_lower
    
    shape_type = rng.choice(["rectangle", "square", "triangle"])
    
    if shape_type == "square":
        side = rng.randint(2, 15)
        perimeter = 4 * side
        
        if is_missing_side:
            # Given perimeter, find side
            stems = [
                f"A square has a perimeter of {perimeter} cm. What is the length of one side?",
                f"The perimeter of a square is {perimeter} cm. Find the side length.",
                f"If a square's perimeter is {perimeter} cm, each side measures ___ cm.",
            ]
            correct = str(side)
            traps = [
                (str(perimeter // 2), "ms_div_by_2"),
                (str(perimeter), "ms_no_divide"),
                (str(side + 1), "ms_off_one"),
            ]
        else:
            stems = [
                f"Find the perimeter of a square with side length {side} cm.",
                f"A square has sides of {side} cm each. What is its perimeter?",
                f"What is the perimeter of a square with side = {side} cm?",
            ]
            correct = str(perimeter)
            traps = [
                (str(side * side), "ms_used_area"),
                (str(side * 2), "ms_only_two_sides"),
                (str(perimeter + side), "ms_extra_side"),
            ]
    
    elif shape_type == "rectangle":
        length = rng.randint(3, 15)
        width = rng.randint(2, length - 1) if length > 2 else rng.randint(1, 2)
        perimeter = 2 * (length + width)
        
        if is_missing_side:
            stems = [
                f"A rectangle has a perimeter of {perimeter} cm and a length of {length} cm. Find the width.",
                f"The perimeter of a rectangle is {perimeter} cm. One side is {length} cm. What is the other side?",
                f"Perimeter = {perimeter} cm, length = {length} cm. Width = ?",
            ]
            correct = str(width)
            traps = [
                (str(perimeter - length), "ms_forgot_double"),
                (str(perimeter // 2), "ms_half_perim"),
                (str(width + 1), "ms_off_one"),
            ]
        else:
            stems = [
                f"Find the perimeter of a rectangle with length {length} cm and width {width} cm.",
                f"A rectangle is {length} cm long and {width} cm wide. What is its perimeter?",
                f"What is the perimeter of a rectangle: L = {length} cm, W = {width} cm?",
            ]
            correct = str(perimeter)
            traps = [
                (str(length * width), "ms_used_area"),
                (str(length + width), "ms_only_once"),
                (str(2 * length + width), "ms_forgot_one_width"),
            ]
    
    else:  # triangle
        # Generate a valid triangle (sum of any two sides > third)
        a = rng.randint(3, 12)
        b = rng.randint(3, 12)
        c = rng.randint(abs(a - b) + 1, a + b - 1)
        perimeter = a + b + c
        
        stems = [
            f"A triangle has sides of {a} cm, {b} cm, and {c} cm. What is its perimeter?",
            f"Find the perimeter of a triangle with sides {a}, {b}, and {c} cm.",
            f"The sides of a triangle measure {a} cm, {b} cm, and {c} cm. Perimeter = ?",
        ]
        correct = str(perimeter)
        traps = [
            (str(a + b), "ms_forgot_side"),
            (str(perimeter + a), "ms_counted_extra"),
            (str(max(a, b, c) * 3), "ms_used_max_side"),
        ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"shape": shape_type, "sub_type": "perimeter"},
    }


def _gen_meas_area(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Find area of squares and rectangles (Grade 3+)."""
    is_word_problem = "solve" in text_lower or "problem" in text_lower
    shape_type = rng.choice(["rectangle", "square"])
    
    if shape_type == "square":
        side = rng.randint(2, 12)
        area = side * side
        unit = rng.choice(["sq. cm", "sq. m"]) if grade >= 3 else "square units"
        
        if is_word_problem:
            stems = [
                f"A garden is shaped like a square with sides of {side} m. How many square meters of soil are needed to cover it?",
                f"A square room has sides of {side} m. How much carpet is needed to cover the floor?",
                f"A square tile has sides of {side} cm. What is its area?",
            ]
        else:
            stems = [
                f"Find the area of a square with side length {side} cm.",
                f"A square has sides of {side} cm. What is its area in {unit}?",
                f"What is the area of a square with side = {side}?",
            ]
        correct = str(area)
        traps = [
            (str(4 * side), "ms_used_perimeter"),
            (str(side * (side + 1)), "ms_off_by_side"),
            (str(side * 2), "ms_doubled_not_squared"),
        ]
    
    else:  # rectangle
        length = rng.randint(3, 12)
        width = rng.randint(2, length)
        area = length * width
        unit = rng.choice(["sq. cm", "sq. m"]) if grade >= 3 else "square units"
        
        if is_word_problem:
            stems = [
                f"A room is {length} m long and {width} m wide. How many square meters of carpet are needed?",
                f"A rectangular garden is {length} m by {width} m. What is its area?",
                f"A wall is {length} m wide and {width} m tall. How much paint is needed to cover {area} sq. m?",
            ]
        else:
            stems = [
                f"Find the area of a rectangle with length {length} cm and width {width} cm.",
                f"A rectangle is {length} cm long and {width} cm wide. What is its area?",
                f"What is the area? Length = {length}, Width = {width}.",
            ]
        correct = str(area)
        traps = [
            (str(2 * (length + width)), "ms_used_perimeter"),
            (str(length + width), "ms_added_not_mult"),
            (str(area + width), "ms_off_by_width"),
        ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"shape": shape_type, "area": area, "sub_type": "area"},
    }


def _gen_meas_mass(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Measure, compare, and convert mass in g, kg, mg."""
    is_compare = "compare" in text_lower
    is_convert = "convert" in text_lower or "measure" in text_lower
    is_estimate = "estimate" in text_lower
    
    if is_compare:
        # Compare two masses (may require conversion)
        kg_val = rng.randint(1, 5)
        g_val = rng.randint(100, 2000)
        kg_in_g = kg_val * 1000
        
        if g_val > kg_in_g:
            correct = f"{g_val} g"
            wrong = f"{kg_val} kg"
        else:
            correct = f"{kg_val} kg"
            wrong = f"{g_val} g"
        
        stems = [
            f"Which is heavier: {kg_val} kg or {g_val} g?",
            f"Compare: {kg_val} kg and {g_val} g. Which has more mass?",
            f"A bag weighs {kg_val} kg. A box weighs {g_val} g. Which is heavier?",
        ]
        traps = [
            (wrong, "ms_no_convert"),
            ("they are equal", "ms_wrong_equal"),
            ("cannot tell", "ms_no_answer"),
        ]
    elif is_estimate:
        # Estimate mass of common objects
        objects_g = [
            ("an apple", 150, "g"), ("a pencil", 10, "g"), ("a textbook", 500, "g"),
            ("a coin", 5, "g"), ("a banana", 120, "g"), ("a phone", 200, "g"),
        ]
        objects_kg = [
            ("a bicycle", 12, "kg"), ("a bag of rice", 5, "kg"),
            ("a chair", 8, "kg"), ("a dog", 15, "kg"),
        ]
        
        all_objects = objects_g + objects_kg
        obj, approx, unit = rng.choice(all_objects)
        
        stems = [
            f"About how much does {obj} weigh?",
            f"Estimate the mass of {obj}.",
            f"Which is the best estimate for the mass of {obj}?",
        ]
        correct = f"about {approx} {unit}"
        traps = [
            (f"about {approx * 10} {unit}", "ms_est_too_high"),
            (f"about {max(1, approx // 10)} {unit}", "ms_est_too_low"),
            (f"about {approx} {'kg' if unit == 'g' else 'g'}", "ms_wrong_unit"),
        ]
    else:
        # Convert between units
        direction = rng.choice(["kg_to_g", "g_to_kg"])
        
        if direction == "kg_to_g":
            kg = rng.randint(1, 10)
            g = kg * 1000
            stems = [
                f"Convert {kg} kg to grams.",
                f"How many grams are in {kg} kg?",
                f"{kg} kg = ___ g",
            ]
            correct = str(g)
            traps = [
                (str(kg * 100), "ms_wrong_factor"),
                (str(kg * 10), "ms_wrong_factor"),
                (str(kg), "ms_no_convert"),
            ]
        else:
            g = rng.choice([1000, 2000, 3000, 4000, 5000])
            kg = g // 1000
            stems = [
                f"Convert {g} g to kilograms.",
                f"How many kilograms is {g} g?",
                f"{g} g = ___ kg",
            ]
            correct = str(kg)
            traps = [
                (str(g // 100), "ms_wrong_factor"),
                (str(g), "ms_no_convert"),
                (str(kg * 10), "ms_wrong_dir"),
            ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "mass"},
    }


def _gen_meas_capacity(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Measure, compare, and convert capacity in L and mL."""
    is_compare = "compare" in text_lower
    is_estimate = "estimate" in text_lower
    
    if is_compare:
        l_val = rng.randint(1, 3)
        ml_val = rng.randint(200, 2000)
        l_in_ml = l_val * 1000
        
        if ml_val > l_in_ml:
            correct = f"{ml_val} mL"
            wrong = f"{l_val} L"
        else:
            correct = f"{l_val} L"
            wrong = f"{ml_val} mL"
        
        stems = [
            f"Which holds more: {l_val} L or {ml_val} mL?",
            f"Compare: a jug with {l_val} L and a bottle with {ml_val} mL. Which has more?",
            f"Container A: {l_val} L. Container B: {ml_val} mL. Which holds more?",
        ]
        traps = [
            (wrong, "ms_no_convert"),
            ("they are equal", "ms_wrong_equal"),
            ("cannot tell", "ms_no_answer"),
        ]
    elif is_estimate:
        objects = [
            ("a glass of water", 250, "mL"), ("a bucket", 10, "L"),
            ("a teaspoon", 5, "mL"), ("a bathtub", 150, "L"),
            ("a water bottle", 500, "mL"), ("a fish tank", 40, "L"),
        ]
        obj, approx, unit = rng.choice(objects)
        
        stems = [
            f"About how much does {obj} hold?",
            f"Estimate the capacity of {obj}.",
            f"Which is the best estimate for {obj}?",
        ]
        correct = f"about {approx} {unit}"
        traps = [
            (f"about {approx * 10} {unit}", "ms_est_too_high"),
            (f"about {max(1, approx // 10)} {unit}", "ms_est_too_low"),
            (f"about {approx} {'L' if unit == 'mL' else 'mL'}", "ms_wrong_unit"),
        ]
    else:
        # Conversion
        direction = rng.choice(["l_to_ml", "ml_to_l"])
        
        if direction == "l_to_ml":
            liters = rng.randint(1, 10)
            ml = liters * 1000
            stems = [
                f"How many milliliters are in {liters} liters?",
                f"Convert {liters} L to mL.",
                f"{liters} L = ___ mL",
            ]
            correct = str(ml)
            traps = [
                (str(liters * 100), "ms_wrong_factor"),
                (str(liters * 10), "ms_wrong_factor"),
                (str(liters), "ms_no_convert"),
            ]
        else:
            ml = rng.choice([1000, 2000, 3000, 4000, 5000])
            liters = ml // 1000
            stems = [
                f"Convert {ml} mL to liters.",
                f"How many liters is {ml} mL?",
                f"{ml} mL = ___ L",
            ]
            correct = str(liters)
            traps = [
                (str(ml // 100), "ms_wrong_factor"),
                (str(ml), "ms_no_convert"),
                (str(liters * 10), "ms_wrong_dir"),
            ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "capacity"},
    }


def _gen_meas_time(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Duration and elapsed time problems."""
    is_elapsed = "elapsed" in text_lower or "how much time" in text_lower
    is_calendar = "day" in text_lower or "week" in text_lower or "duration" in text_lower
    
    if is_calendar:
        # Days/weeks duration problems
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        start_idx = rng.randint(0, 5)
        end_idx = rng.randint(start_idx + 1, 6)
        duration = end_idx - start_idx
        start_day = days_of_week[start_idx]
        end_day = days_of_week[end_idx]
        
        stems = [
            f"How many days are there from {start_day} to {end_day}?",
            f"An event starts on {start_day} and ends on {end_day}. How many days is that?",
            f"Count the days from {start_day} to {end_day} (not including {start_day}).",
        ]
        stem = rng.choice(stems)
        correct = str(duration)
        traps = [
            (str(duration + 1), "ms_inclusive_count"),
            (str(duration - 1), "ms_off_one"),
            (str(7 - duration), "ms_complement"),
        ]
    elif is_elapsed:
        # Elapsed time in hours and minutes
        start_h = rng.randint(1, 10)
        start_m = rng.choice([0, 15, 30, 45])
        elapsed_min = rng.choice([15, 30, 45, 60, 90, 120])
        
        end_total_min = start_h * 60 + start_m + elapsed_min
        end_h = end_total_min // 60
        end_m = end_total_min % 60
        
        start_str = f"{start_h}:{start_m:02d}"
        end_str = f"{end_h}:{end_m:02d}"
        
        stems = [
            f"A movie starts at {start_str} and lasts {elapsed_min} minutes. When does it end?",
            f"You begin reading at {start_str}. After {elapsed_min} minutes, what time is it?",
            f"Class starts at {start_str} and is {elapsed_min} minutes long. What time does it end?",
        ]
        stem = rng.choice(stems)
        correct = end_str
        # Generate traps
        wrong_add_to_hour = f"{start_h + elapsed_min // 60 + 1}:{start_m:02d}"
        wrong_no_carry = f"{start_h}:{(start_m + elapsed_min) % 100:02d}" if start_m + elapsed_min < 100 else f"{start_h + 1}:{start_m:02d}"
        
        traps = [
            (wrong_add_to_hour, "ms_time_no_min"),
            (wrong_no_carry, "ms_time_no_carry"),
            (f"{end_h}:{(end_m + 5) % 60:02d}", "ms_off_five_min"),
        ]
    else:
        # General time problems — minutes in an hour, hours in a day, days in a week
        facts = [
            ("How many minutes are in 1 hour?", "60", [("100", "ms_wrong_fact"), ("30", "ms_half"), ("24", "ms_confused_unit")]),
            ("How many hours are in 1 day?", "24", [("12", "ms_half"), ("60", "ms_confused_unit"), ("30", "ms_wrong_fact")]),
            ("How many days are in 1 week?", "7", [("5", "ms_weekdays_only"), ("10", "ms_wrong_fact"), ("14", "ms_doubled")]),
            ("How many minutes are in 2 hours?", "120", [("60", "ms_only_one"), ("200", "ms_wrong_fact"), ("20", "ms_confused_unit")]),
            ("How many days are in 2 weeks?", "14", [("7", "ms_only_one"), ("10", "ms_wrong_fact"), ("12", "ms_confused_unit")]),
        ]
        
        stem, correct, traps = rng.choice(facts)
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"sub_type": "time"},
    }


def _gen_meas_estimation(grade: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """Estimate length, mass, or capacity using real-world context."""
    # Determine what to estimate based on text
    if "mass" in text_lower or "gram" in text_lower or "kilogram" in text_lower:
        return _gen_meas_mass(grade, rng, "estimate mass")
    elif "capacity" in text_lower or "liter" in text_lower:
        return _gen_meas_capacity(grade, rng, "estimate capacity")
    
    # Default: estimate length
    objects = [
        ("a door's height", 2, "m"),
        ("a pencil", 18, "cm"),
        ("a classroom", 10, "m"),
        ("a finger width", 1, "cm"),
        ("a car", 4, "m"),
        ("a table's height", 75, "cm"),
        ("an ant", 3, "mm"),
        ("a basketball court", 28, "m"),
    ]
    
    obj, approx, unit = rng.choice(objects)
    
    stems = [
        f"Which is the best estimate for the length of {obj}?",
        f"About how long is {obj}?",
        f"Estimate: The length of {obj} is closest to:",
    ]
    
    correct = f"about {approx} {unit}"
    traps = [
        (f"about {approx * 10} {unit}", "ms_est_too_high"),
        (f"about {max(1, approx // 5)} {unit}", "ms_est_too_low"),
        (f"about {approx} {'m' if unit == 'cm' else 'cm'}", "ms_wrong_unit"),
    ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"object": obj, "sub_type": "estimation"},
    }


def _gen_data_probability(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Generate data/probability problems based on grade-appropriate competencies.
    
    Grade 1-2: Pictographs (without/with scale) - requires visual rendering
    Grade 3-4: Bar graphs, simple tables, basic probability
    Grade 5+: Mean, median, mode, complex graphs
    """
    text_lower = competency_text.lower()
    
    # Check if this competency requires visual rendering (pictographs, bar graphs)
    # These should be flagged to use the visual_skeletons system instead
    needs_visual = any(term in text_lower for term in [
        "pictograph", "bar graph", "line graph", "pie chart", 
        "present data", "construct", "draw", "create graph"
    ])
    
    if needs_visual:
        # Return a placeholder that signals visual rendering is needed
        # The frontend/API should detect this and use visual_skeletons instead
        return {
            "stem": f"[VISUAL REQUIRED] This competency requires interactive visual rendering: {competency_text[:60]}...",
            "correct_answer": "visual",
            "options": _shuffle_options([
                ("visual", None),
                ("text", "dp_wrong"),
                ("none", "dp_wrong"),
                ("skip", "dp_wrong"),
            ], rng),
            "variables": {"needs_visual": True, "competency": competency_text},
            "requires_visual": True,  # Flag for API to handle
        }
    
    # Grade 1-2: Simple data interpretation (reading pictographs, counting)
    if grade <= 2:
        # For Grade 1-2, focus on simple counting and comparison from data
        items = ["apples", "bananas", "oranges", "dogs", "cats", "birds"]
        item = rng.choice(items)
        counts = [rng.randint(1, 5) for _ in range(3)]
        
        # Simple "how many" questions
        question_types = [
            (f"There are {counts[0]} red {item} and {counts[1]} green {item}. How many {item} in total?",
             str(counts[0] + counts[1]),
             [(str(counts[0]), "dp_partial"), (str(counts[1]), "dp_partial"), (str(abs(counts[0] - counts[1])), "dp_sub_add")]),
            
            (f"Ana has {counts[0]} {item}. Ben has {counts[1]} {item}. Who has more?",
             "Ana" if counts[0] > counts[1] else "Ben" if counts[1] > counts[0] else "Same",
             [("Ben" if counts[0] > counts[1] else "Ana", "dp_compare"), ("Same" if counts[0] != counts[1] else "Ana", "dp_compare"), ("Cannot tell", "dp_compare")]),
            
            (f"If you have {counts[0]} {item} and get {counts[1]} more, how many do you have?",
             str(counts[0] + counts[1]),
             [(str(counts[0]), "dp_partial"), (str(abs(counts[0] - counts[1])), "dp_wrong_op"), (str(counts[0] + counts[1] + 1), "dp_off_one")]),
        ]
        
        stem, correct, traps = rng.choice(question_types)
        options_list = [(correct, None)] + traps[:3]
        
        return {
            "stem": stem,
            "correct_answer": correct,
            "options": _shuffle_options(options_list, rng),
            "variables": {"item": item, "counts": counts},
        }
    
    # Grade 3-4: Tables, simple graphs interpretation, basic probability
    elif grade <= 4:
        if "probability" in text_lower or "chance" in text_lower or "likely" in text_lower:
            # Simple probability
            outcomes = ["red", "blue", "green", "yellow"]
            total = rng.randint(6, 12)
            target_count = rng.randint(1, total // 2)
            target_color = rng.choice(outcomes)
            
            stem = f"A bag has {total} marbles. {target_count} are {target_color}. What fraction of the marbles are {target_color}?"
            correct = f"{target_count}/{total}"
            
            # Simplify if possible
            from math import gcd
            g = gcd(target_count, total)
            if g > 1:
                correct = f"{target_count // g}/{total // g}"
            
            traps = [
                (f"{total}/{target_count}", "dp_frac_flip"),
                (f"{target_count}/{total - target_count}", "dp_wrong_denom"),
                (f"{total - target_count}/{total}", "dp_complement"),
            ]
            options_list = [(correct, None)] + traps[:3]
            
            return {
                "stem": stem,
                "correct_answer": correct,
                "options": _shuffle_options(options_list, rng),
                "variables": {"total": total, "target": target_count, "color": target_color},
            }
        else:
            # Table/data reading
            items = ["apples", "books", "pencils", "coins"]
            item = rng.choice(items)
            days = ["Monday", "Tuesday", "Wednesday"]
            values = [rng.randint(3, 15) for _ in days]
            
            total = sum(values)
            max_day = days[values.index(max(values))]
            
            question_types = [
                (f"The table shows {item} collected each day. Monday: {values[0]}, Tuesday: {values[1]}, Wednesday: {values[2]}. How many total?",
                 str(total),
                 [(str(max(values)), "dp_max_total"), (str(values[0]), "dp_partial"), (str(total + 1), "dp_off_one")]),
                
                (f"Monday: {values[0]} {item}, Tuesday: {values[1]} {item}, Wednesday: {values[2]} {item}. Which day had the most?",
                 max_day,
                 [(d, "dp_wrong_day") for d in days if d != max_day]),
            ]
            
            stem, correct, traps = rng.choice(question_types)
            options_list = [(correct, None)] + traps[:3]
            
            return {
                "stem": stem,
                "correct_answer": correct,
                "options": _shuffle_options(options_list, rng),
                "variables": {"item": item, "values": values},
            }
    
    # Grade 5+: Mean, median, mode, range
    else:
        data_size = 5 if grade <= 6 else 7
        data = sorted([rng.randint(1, 20) for _ in range(data_size)])
        
        total = sum(data)
        mean_val = total / len(data)
        median_val = data[len(data) // 2]
        
        # Count frequencies for mode
        from collections import Counter
        freq = Counter(data)
        mode_val = max(freq, key=freq.get) if max(freq.values()) > 1 else data[0]
        range_val = max(data) - min(data)
        
        if "mean" in text_lower or "average" in text_lower:
            correct = str(round(mean_val, 1) if mean_val != int(mean_val) else int(mean_val))
            stem = f"Find the mean of: {', '.join(map(str, data))}"
            traps = [
                (str(total), "dp_sum_avg"),
                (str(median_val), "dp_mean_median"),
                (str(mode_val), "dp_mean_mode"),
            ]
        elif "median" in text_lower:
            correct = str(median_val)
            stem = f"Find the median of: {', '.join(map(str, data))}"
            traps = [
                (str(round(mean_val)), "dp_median_mean"),
                (str(data[0]), "dp_first_median"),
                (str(data[-1]), "dp_last_median"),
            ]
        elif "mode" in text_lower:
            correct = str(mode_val)
            stem = f"Find the mode of: {', '.join(map(str, data))}"
            traps = [
                (str(median_val), "dp_mode_median"),
                (str(round(mean_val)), "dp_mode_mean"),
                (str(data[-1]), "dp_wrong_mode"),
            ]
        elif "range" in text_lower:
            correct = str(range_val)
            stem = f"Find the range of: {', '.join(map(str, data))}"
            traps = [
                (str(max(data)), "dp_max_range"),
                (str(min(data)), "dp_min_range"),
                (str(max(data) + min(data)), "dp_sum_range"),
            ]
        else:
            # Default to mean for Grade 5+
            correct = str(round(mean_val, 1) if mean_val != int(mean_val) else int(mean_val))
            stem = f"Find the mean of: {', '.join(map(str, data))}"
            traps = [
                (str(total), "dp_sum_avg"),
                (str(median_val), "dp_mean_median"),
                (str(mode_val), "dp_mean_mode"),
            ]
        
        options_list = [(correct, None)] + traps[:3]
        
        return {
            "stem": stem,
            "correct_answer": correct,
            "options": _shuffle_options(options_list, rng),
            "variables": {"data": data},
        }


def _gen_compose_decompose(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """Generate compose/decompose number problems matching the competency."""
    text_lower = competency_text.lower()
    
    # Extract the max number from competency (e.g., "up to 10")
    import re
    max_match = re.search(r"up to (\d+)", text_lower)
    max_num = int(max_match.group(1)) if max_match else 10
    
    # Choose a target number
    target = rng.randint(2, min(max_num, 10))
    
    if "compose" in text_lower and "decompose" not in text_lower:
        # Compose: show parts, ask for whole
        part1 = rng.randint(0, target)
        part2 = target - part1
        stem = f"{part1} and {part2} is the same as what number?"
        correct = str(target)
        traps = [
            (str(target + 1), "cd_off_one"),
            (str(target - 1), "cd_off_one") if target > 1 else (str(target + 2), "cd_off_one"),
            (str(part1 * part2) if part1 * part2 != target else str(target + rng.randint(2, 4)), "cd_wrong_op"),
        ]
    elif "decompose" in text_lower:
        # Decompose: show whole, ask for parts
        part1 = rng.randint(0, target)
        part2 = target - part1
        stem = f"Break apart {target} into two numbers. Which shows {target}?"
        correct = f"{part1} and {part2}"
        
        # Generate wrong decompositions
        wrong1 = f"{part1 + 1} and {part2}" if part1 + 1 + part2 != target else f"{part1} and {part2 + 1}"
        wrong2 = f"{part1} and {part2 + 1}" if part1 + part2 + 1 != target else f"{part1 - 1} and {part2}"
        wrong3 = f"{target} and 1" if target != target + 1 else f"{target - 1} and 2"
        
        traps = [
            (wrong1, "cd_wrong_sum"),
            (wrong2, "cd_wrong_sum"),
            (wrong3, "cd_wrong_decomp"),
        ]
    else:
        # Generic compose/decompose
        part1 = rng.randint(0, target)
        part2 = target - part1
        stem = f"{target} is the same as {part1} and what number?"
        correct = str(part2)
        traps = [
            (str(part2 + 1), "cd_off_one"),
            (str(part2 - 1) if part2 > 0 else str(part2 + 2), "cd_off_one"),
            (str(target), "cd_used_whole"),
        ]
    
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"target": target, "part1": part1, "part2": part2},
    }


def _gen_compare_order(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """Generate compare number problems, now respecting dimensions (max_number, proximity)."""
    text_lower = competency_text.lower()

    # Prefer dimensions over text extraction so axis overrides take effect
    import re as _re
    text_max_match = _re.search(r"up to (\d[\d, ]*\d*)", text_lower)
    text_max = int(text_max_match.group(1).replace(",", "").replace(" ", "")) if text_max_match else None
    default_max = 100 if grade <= 2 else 1000 if grade <= 3 else 10000
    max_num = dimensions.get("max_number") or dimensions.get("operand_max") or text_max or default_max

    # Determine sub-type
    proximity_pref = dimensions.get("proximity")  # "close" | "far" | None

    if "symbol" in text_lower or ">" in text_lower or "<" in text_lower or "=" in text_lower:
        return _gen_compare_symbol(max_num, rng)
    elif "order" in text_lower or "arrange" in text_lower or "smallest" in text_lower or "largest" in text_lower:
        return _gen_compare_ordering_mcq(max_num, rng, text_lower)
    else:
        return _gen_compare_which_greater(max_num, rng, proximity=proximity_pref)



def _gen_compare_symbol(max_num: int, rng: random.Random) -> Dict[str, Any]:
    """Fill in the correct comparison symbol (>, <, =)."""
    a = rng.randint(1, max_num)
    b = rng.randint(1, max_num)
    
    # Allow some equal cases
    if rng.random() < 0.15:
        b = a
    
    if a > b:
        correct = ">"
    elif a < b:
        correct = "<"
    else:
        correct = "="
    
    a_str = _format_number(a)
    b_str = _format_number(b)
    
    stems = [
        f"Fill in the blank: {a_str} ___ {b_str}",
        f"Compare: {a_str} ___ {b_str}. Use >, <, or =.",
        f"Which symbol goes between {a_str} and {b_str}?",
    ]
    
    all_symbols = [">", "<", "="]
    traps = [(s, "co_wrong_symbol") for s in all_symbols if s != correct]
    # Add a common misconception trap
    traps.append((">=", "co_wrong_symbol"))
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b, "sub_type": "symbol"},
    }


def _gen_compare_ordering_mcq(max_num: int, rng: random.Random, text_lower: str) -> Dict[str, Any]:
    """MCQ fallback for ordering problems (visual SortOrder is preferred)."""
    is_descending = "largest" in text_lower and "smallest" not in text_lower[:text_lower.find("largest")]
    
    # Generate 4 numbers
    numbers = sorted(rng.sample(range(1, max_num), min(4, max_num - 1)))
    
    if is_descending:
        correct_order = list(reversed(numbers))
        direction = "largest to smallest"
    else:
        correct_order = numbers
        direction = "smallest to largest"
    
    correct = ", ".join(map(str, correct_order))
    
    # Generate wrong orderings
    wrong1 = list(reversed(correct_order))
    wrong2 = correct_order.copy()
    wrong2[1], wrong2[2] = wrong2[2], wrong2[1]  # Swap middle pair
    wrong3 = correct_order.copy()
    wrong3[0], wrong3[-1] = wrong3[-1], wrong3[0]  # Swap endpoints
    
    stems = [
        f"Arrange from {direction}: {', '.join(map(str, rng.sample(numbers, len(numbers))))}",
        f"Order these numbers from {direction}: {', '.join(map(str, rng.sample(numbers, len(numbers))))}",
        f"Put in order ({direction}): {', '.join(map(str, rng.sample(numbers, len(numbers))))}",
    ]
    
    traps = [
        (", ".join(map(str, wrong1)), "co_reversed"),
        (", ".join(map(str, wrong2)), "co_middle_swap"),
        (", ".join(map(str, wrong3)), "co_endpoint_swap"),
    ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"numbers": numbers, "sub_type": "ordering"},
    }


def _gen_compare_which_greater(max_num: int, rng: random.Random,
                                proximity: str = None) -> Dict[str, Any]:
    """Which number is greater/lesser, honouring proximity axis."""
    threshold = max(2, max_num // 10)  # close = within 10% of range

    for _attempt in range(50):
        a = rng.randint(1, max_num)
        b = rng.randint(1, max_num)
        if a == b:
            continue
        diff = abs(a - b)
        if proximity == "close" and diff > threshold * 2:
            continue
        if proximity == "far" and diff < threshold * 2:
            continue
        break
    
    greater = max(a, b)
    lesser = min(a, b)
    
    stems = [
        f"Which number is greater: {_format_number(a)} or {_format_number(b)}?",
        f"Compare {_format_number(a)} and {_format_number(b)}. Which is larger?",
        f"Which is bigger: {_format_number(a)} or {_format_number(b)}?",
    ]
    
    correct = str(greater)
    traps = [
        (str(lesser), "co_lesser"),
        (str(a + b), "co_sum"),
        (str(abs(a - b)), "co_diff"),
    ]
    
    stem = rng.choice(stems)
    options_list = [(correct, None)] + traps[:3]
    
    return {
        "stem": stem,
        "correct_answer": correct,
        "options": _shuffle_options(options_list, rng),
        "variables": {"a": a, "b": b, "sub_type": "which_greater"},
    }


def _gen_conceptual(
    competency_text: str,
    grade: int,
    dimensions: Dict[str, Any],
    constraints: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """Generate conceptual/definition problems - fallback."""
    # Extract key concepts from competency
    text_lower = competency_text.lower()
    
    concepts = {
        "addition": ("putting together", "taking away", "multiplying", "dividing"),
        "subtraction": ("taking away", "putting together", "multiplying", "dividing"),
        "multiplication": ("repeated addition", "repeated subtraction", "taking away", "putting together"),
        "division": ("splitting into equal groups", "putting together", "adding", "multiplying"),
        "fraction": ("part of a whole", "a whole number", "more than one", "less than zero"),
        "even": ("divisible by 2", "divisible by 3", "divisible by 5", "not divisible by anything"),
        "odd": ("not divisible by 2", "divisible by 2", "divisible by 10", "always negative"),
    }
    
    for concept, (correct, *wrong) in concepts.items():
        if concept in text_lower:
            traps = [(w, "gp_wrong_prop") for w in wrong[:3]]
            options_list = [(correct, None)] + traps
            
            return {
                "stem": f"What does {concept} mean?",
                "correct_answer": correct,
                "options": _shuffle_options(options_list, rng),
                "variables": {"concept": concept},
            }
    
    # Default fallback - randomized number comparison
    # Scale max based on grade level
    max_num = min(10 + (grade - 1) * 10, 100)  # Grade 1: 10, Grade 2: 20, ..., Grade 6+: 100
    
    a = rng.randint(1, max_num)
    b = rng.randint(1, max_num)
    while a == b:
        b = rng.randint(1, max_num)
    
    greater = max(a, b)
    lesser = min(a, b)
    
    # Generate plausible distractors
    trap1 = str(lesser)
    trap2 = str(a + b) if a + b <= 999 else str(abs(a - b) + 1)
    trap3 = str(abs(a - b)) if abs(a - b) != greater else str(greater + rng.randint(1, 5))
    
    # Ensure all traps are unique and different from correct answer
    traps = []
    for t in [trap1, trap2, trap3]:
        if t != str(greater) and t not in traps:
            traps.append(t)
    while len(traps) < 3:
        filler = str(rng.randint(1, max_num))
        if filler != str(greater) and filler not in traps:
            traps.append(filler)
    
    return {
        "stem": f"Which number is greater: {a} or {b}?",
        "correct_answer": str(greater),
        "options": _shuffle_options([(str(greater), None), (traps[0], "compare_wrong"), (traps[1], "ar_mul_add"), (traps[2], "ar_wrong_op")], rng),
        "variables": {"a": a, "b": b},
    }
