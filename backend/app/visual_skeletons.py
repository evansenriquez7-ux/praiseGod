"""
Visual problem skeleton generators for MATATAG Math curriculum.

Generates deterministic, auto-validatable problems with snap-to-grid validation.
Each skeleton includes:
  - visual_params: Parameters defining the visual representation
  - correct_answer: Computed deterministically from visual_params
  - all_traps: Comprehensive catalog of misconception-based wrong answers

Usage:
    skeleton = get_visual_skeleton("NumberLine", grade=4, seed=12345)
    
    # Stateless regeneration from ID:
    skeleton = regenerate_skeleton("nl_4_12345_m")
    
    # Validate student answer:
    result = validate_student_answer("nl_4_12345_m", student_answer=3)
"""

import random
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import calendar as calendar_module

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

TYPE_CODES = {
    "fit": "FillInTable",
    "rd": "RuleDiscovery",
    "cs": "ConstraintSatisfaction",
    "pm": "PesoMoney",
    "bc": "BarChart",
    "nl": "NumberLine",
    "clk": "ClockSet",
    "so": "SortOrder",
    "ga": "GridArea",
    "cat": "Categorize",
    "cal": "Calendar",
}

TYPE_CODES_REVERSE = {v: k for k, v in TYPE_CODES.items()}

DIFFICULTY_CODES = {"1": 1, "2": 2, "3": 3, "4": 4}
DIFFICULTY_CODES_REVERSE = {v: k for k, v in DIFFICULTY_CODES.items()}


def _normalize_difficulty_for_comparison(difficulty: Any) -> float:
    """
    Convert difficulty to scalar for comparisons.
    Handles legacy int (1-4), float (0.0-1.5), and string ("easy", "medium", "hard").
    """
    from .difficulty_engine import normalize_difficulty
    return normalize_difficulty(difficulty)


def _difficulty_level(difficulty: Any) -> int:
    """
    Convert any difficulty format to integer level 1-4.
    
    Handles:
    - int (1-4): pass through
    - float (0.0-1.5): map to 1-4
    - str ("easy", "medium", "hard", "advanced"): map to 1-4
    
    Returns: 1 (easy), 2 (medium), 3 (hard), or 4 (advanced)
    """
    if isinstance(difficulty, str):
        mapping = {"easy": 1, "medium": 2, "hard": 3, "advanced": 4}
        return mapping.get(difficulty.lower(), 2)
    elif isinstance(difficulty, float):
        # Map 0.0-1.5 to 1-4
        if difficulty < 0.3:
            return 1
        elif difficulty < 0.7:
            return 2
        elif difficulty < 1.0:
            return 3
        else:
            return 4
    else:
        # Already an int, clamp to 1-4
        return max(1, min(4, int(difficulty)))


MAX_RETRIES = 3

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINTS
# ═══════════════════════════════════════════════════════════════════════════════

def get_visual_skeleton(
    visual_type: str,
    grade: int,
    seed: Optional[int] = None,
    difficulty: int = 2,
    competency_text: Optional[str] = None,
    question_mode: Optional[str] = None,
    axis_values: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Generate a complete visual skeleton with all traps.
    
    Args:
        visual_type: One of the TYPE_CODES values (e.g., "NumberLine", "FillInTable")
        grade: Grade level 1-10
        seed: Random seed for reproducibility
        difficulty: 1 (easy), 2 (medium), 3 (hard), 4 (advanced)
        competency_text: Optional MATATAG competency text for context-aware generation
        question_mode: How to present the question:
            - "interactive" (default): student manipulates the visual
            - "mcq": visual shown, student picks from 4 options
            - "true_false": visual shown with a claim
            - "fill_in": visual shown, student enters answer
    
    Returns:
        Complete skeleton dict with visual_params, correct_answer, all_traps
    """
    if seed is None:
        seed = random.randint(1000, 99999)
    
    # Default question mode
    if question_mode is None:
        question_mode = "interactive"
    
    for attempt in range(MAX_RETRIES):
        actual_seed = seed + attempt * 10000
        rng = random.Random(actual_seed)
        
        try:
            skeleton = _generate_skeleton(visual_type, grade, actual_seed, difficulty, rng,
                                          competency_text, axis_values=axis_values)
            
            if validate_skeleton(skeleton):
                # Transform based on question_mode
                skeleton = _transform_for_question_mode(skeleton, question_mode, rng)
                return skeleton
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise Exception(f"Failed to generate valid {visual_type} after {MAX_RETRIES} attempts: {e}")
            continue
    
    raise Exception(f"Could not generate valid {visual_type} skeleton")


def _transform_for_question_mode(skeleton: Dict, question_mode: str, rng: random.Random) -> Dict:
    """
    Transform a skeleton for different question modes.
    
    MCQ mode: Generate 4 options including correct answer
    True/False mode: Generate a claim that may be true or false
    Fill-in mode: Set visual as read-only, expect typed answer
    Interactive mode: Default, no transformation
    """
    if question_mode == "interactive":
        return skeleton
    
    visual_type = skeleton.get("visual_type", "")
    correct_answer = skeleton.get("correct_answer")
    all_traps = skeleton.get("all_traps", {})
    
    if question_mode == "mcq":
        # Generate 4 options: 1 correct + 3 traps (or generated distractors)
        options = []
        
        # Add correct answer
        options.append({
            "key": "A",
            "value": correct_answer,
            "is_correct": True
        })
        
        # Add trap values as distractors
        trap_values = []
        for trap_name, trap_data in all_traps.items():
            trap_val = trap_data.get("value") or trap_data.get("position") or trap_data.get("values")
            if trap_val is not None and trap_val != correct_answer:
                trap_values.append(trap_val)
        
        # Use up to 3 traps as distractors
        rng.shuffle(trap_values)
        for i, trap_val in enumerate(trap_values[:3]):
            options.append({
                "key": chr(ord("B") + i),
                "value": trap_val,
                "is_correct": False
            })
        
        # If we don't have enough traps, generate some
        while len(options) < 4:
            # Generate a distractor based on type
            if isinstance(correct_answer, (int, float)):
                distractor = correct_answer + rng.choice([-2, -1, 1, 2, 3]) * (1 if correct_answer < 10 else 10)
            elif isinstance(correct_answer, list):
                # For lists (like SortOrder), shuffle differently
                distractor = correct_answer.copy()
                rng.shuffle(distractor)
            else:
                distractor = str(correct_answer) + "?"
            
            # Avoid duplicates
            if distractor not in [o["value"] for o in options]:
                options.append({
                    "key": chr(ord("A") + len(options)),
                    "value": distractor,
                    "is_correct": False
                })
        
        # Shuffle options
        rng.shuffle(options)
        for i, opt in enumerate(options):
            opt["key"] = chr(ord("A") + i)
        
        skeleton["mcq_options"] = options
        skeleton["question_mode"] = "mcq"
        skeleton["correct_answer"] = next(o["key"] for o in options if o["is_correct"])
        
        # Mark visual as read-only (pre-filled)
        skeleton["visual_params"]["is_read_only"] = True
        skeleton["visual_params"]["show_answer"] = True  # Show the correct configuration
        
    elif question_mode == "true_false":
        # Generate a claim - 50% chance it's correct
        is_true = rng.choice([True, False])
        
        if is_true:
            claim_answer = correct_answer
        else:
            # Use a trap value for the false claim
            trap_values = [t.get("value") or t.get("position") for t in all_traps.values()]
            trap_values = [v for v in trap_values if v is not None and v != correct_answer]
            claim_answer = rng.choice(trap_values) if trap_values else correct_answer
        
        skeleton["tf_claim"] = _generate_claim(visual_type, claim_answer, skeleton)
        skeleton["tf_is_true"] = is_true
        skeleton["question_mode"] = "true_false"
        skeleton["correct_answer"] = is_true
        skeleton["visual_params"]["is_read_only"] = True
        
    elif question_mode == "fill_in":
        # Visual is shown, student types the answer
        skeleton["question_mode"] = "fill_in"
        skeleton["visual_params"]["is_read_only"] = True
        skeleton["visual_params"]["show_answer"] = True
    
    return skeleton


def _generate_claim(visual_type: str, answer_value: Any, skeleton: Dict) -> str:
    """Generate a claim statement for true/false questions."""
    params = skeleton.get("visual_params", {})
    
    if visual_type == "NumberLine":
        return f"The marked position represents {answer_value}."
    elif visual_type == "ClockSet":
        h, m = answer_value if isinstance(answer_value, tuple) else (answer_value, 0)
        return f"The clock shows {h}:{m:02d}."
    elif visual_type == "PesoMoney":
        return f"The total amount is ₱{answer_value}."
    elif visual_type == "SortOrder":
        return f"These numbers are arranged from smallest to largest."
    elif visual_type == "GridArea":
        return f"The shaded area is {answer_value} square units."
    elif visual_type == "BarChart":
        return f"The bar graph correctly represents the data."
    else:
        return f"The answer is {answer_value}."


def regenerate_skeleton(skeleton_id: str) -> Dict[str, Any]:
    """
    Stateless regeneration from encoded skeleton_id.
    
    Args:
        skeleton_id: Encoded ID like "nl_4_12345_m"
    
    Returns:
        Same skeleton that was originally generated with these params
    """
    params = decode_skeleton_id(skeleton_id)
    return get_visual_skeleton(
        visual_type=params["visual_type"],
        grade=params["grade"],
        seed=params["seed"],
        difficulty=params["difficulty"]
    )


def encode_skeleton_id(visual_type: str, grade: int, seed: int, difficulty: int) -> str:
    """Encode parameters into skeleton_id string."""
    type_code = TYPE_CODES_REVERSE.get(visual_type, "unk")
    diff_code = DIFFICULTY_CODES_REVERSE.get(difficulty, "2")
    return f"{type_code}_{grade}_{seed}_{diff_code}"


def decode_skeleton_id(skeleton_id: str) -> Dict[str, Any]:
    """Decode skeleton_id back to parameters."""
    parts = skeleton_id.split("_")
    if len(parts) != 4:
        raise ValueError(f"Invalid skeleton_id format: {skeleton_id}")
    
    type_code, grade_str, seed_str, diff_code = parts
    
    return {
        "visual_type": TYPE_CODES.get(type_code, "NumberLine"),
        "grade": int(grade_str),
        "seed": int(seed_str),
        "difficulty": DIFFICULTY_CODES.get(diff_code, 2)
    }


def _generate_skeleton(visual_type: str, grade: int, seed: int, difficulty: int,
                       rng: random.Random, competency_text: Optional[str] = None,
                       axis_values: Optional[dict] = None) -> Dict[str, Any]:
    """Route to appropriate generator based on visual_type."""
    # BarChart, PesoMoney, ClockSet support axis_values overrides
    if visual_type == "BarChart":
        return _gen_bar_chart(grade, seed, difficulty, rng, competency_text, axis_values=axis_values)
    if visual_type == "PesoMoney":
        return _gen_peso_money(grade, seed, difficulty, rng, competency_text, axis_values=axis_values)
    if visual_type == "ClockSet":
        return _gen_clock_set(grade, seed, difficulty, rng, competency_text, axis_values=axis_values)

    generators = {
        "FillInTable": _gen_fill_in_table,
        "RuleDiscovery": _gen_rule_discovery,
        "ConstraintSatisfaction": _gen_constraint_satisfaction,
        "NumberLine": _gen_number_line,
        "SortOrder": _gen_sort_order,
        "GridArea": _gen_grid_area,
        "Categorize": _gen_categorize,
        "Calendar": _gen_calendar,
    }

    generator = generators.get(visual_type)
    if not generator:
        raise ValueError(f"Unknown visual_type: {visual_type}")

    return generator(grade, seed, difficulty, rng, competency_text)


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_skeleton(skeleton: Dict) -> bool:
    """
    Validate 3-condition contract:
    1. Invariant check - visual_params pass shape-specific assertions
    2. Answer derivability - compute_answer(visual_params) == correct_answer
    3. Trap validity - all distractors distinct from correct and each other
    """
    vtype = skeleton.get("visual_type")
    params = skeleton.get("visual_params", {})
    correct = skeleton.get("correct_answer")
    all_traps = skeleton.get("all_traps", {})
    
    # 1. Invariant check
    invariant_checker = INVARIANT_CHECKS.get(vtype)
    if invariant_checker and not invariant_checker(params):
        return False
    
    # 2. Answer derivability
    computed = compute_answer(vtype, params)
    if computed != correct:
        return False
    
    # 3. Trap validity - filter duplicates and validate
    # We accept some duplicate trap values since they may target same misconception
    # Just ensure we have SOME distinct traps and none equal to correct
    trap_values = []
    for trap_name, trap_data in all_traps.items():
        trap_val = trap_data.get("value") or trap_data.get("position") or trap_data.get("values")
        if trap_val is not None and trap_val != correct:
            trap_values.append(trap_val)
    
    # Ensure correct answer is not in traps
    if correct in trap_values:
        return False
    
    # Ensure we have at least some distinct trap values
    # For very simple problems (like 1/2 on number line), we may only have 1 distinct trap
    # which is still valid for learning purposes
    if len(trap_values) > 0:
        unique_traps = set(str(v) for v in trap_values)
        # Need at least 1 distinct trap for minimal distractors
        if len(unique_traps) < 1:
            return False
    
    return True


def compute_answer(visual_type: str, params: Dict) -> Any:
    """Deterministic answer computation from visual_params."""
    
    if visual_type == "NumberLine":
        return params.get("correct_position")
    
    elif visual_type == "FillInTable":
        # The correct answers are pre-computed and stored
        return params.get("correct_fills")
    
    elif visual_type == "RuleDiscovery":
        # Answer is the SymPy expression
        return params.get("rule_expression")
    
    elif visual_type == "ConstraintSatisfaction":
        # Answer is any value satisfying all constraints
        return params.get("valid_answers", [])[0] if params.get("valid_answers") else None
    
    elif visual_type == "PesoMoney":
        # Answer is a list of denominations summing to target
        return params.get("target_amount")
    
    elif visual_type == "BarChart":
        # For read_bar with ask_category, return that specific value
        if params.get("ask_category") and params.get("labels") and params.get("values"):
            try:
                idx = params["labels"].index(params["ask_category"])
                if params.get("ask_series") and params.get("values2"):
                    series_labels = params.get("series_labels", [])
                    if params["ask_series"] == series_labels[0]:
                        return params["values"][idx]
                    else:
                        return params["values2"][idx]
                return params["values"][idx]
            except (ValueError, IndexError):
                pass
        # For double bar charts, return both value sets
        if params.get("values2"):
            return [params.get("values", []), params.get("values2", [])]
        return params.get("values", [])
    
    elif visual_type == "ClockSet":
        return (params.get("hours"), params.get("minutes"))
    
    elif visual_type == "SortOrder":
        return params.get("correct_sequence", [])
    
    elif visual_type == "GridArea":
        return params.get("correct_count")
    
    elif visual_type == "Categorize":
        return params.get("correct_categories", {})
    
    elif visual_type == "Calendar":
        return params.get("correct_date") or params.get("correct_duration")
    
    return None


def validate_student_answer(skeleton_id: str, student_answer: Any) -> Dict:
    """
    Grade student answer against regenerated skeleton.
    
    Returns:
        {
            "is_correct": bool,
            "trap_triggered": str or None,
            "correct_answer": Any
        }
    """
    skeleton = regenerate_skeleton(skeleton_id)
    correct = skeleton["correct_answer"]
    vtype = skeleton["visual_type"]
    
    # Type-specific comparison with type coercion
    is_correct = False
    
    if vtype == "RuleDiscovery":
        # SymPy symbolic equivalence
        try:
            student_expr = sp.sympify(student_answer)
            correct_expr = sp.sympify(correct)
            is_correct = sp.simplify(student_expr - correct_expr) == 0
        except:
            is_correct = False
    
    elif vtype == "PesoMoney":
        # Handle various input formats (defense in depth)
        if isinstance(student_answer, dict):
            student_val = student_answer.get("total", 0)
        elif isinstance(student_answer, str):
            try:
                student_val = int(student_answer)
            except ValueError:
                student_val = -1  # Invalid
        else:
            student_val = student_answer
        is_correct = student_val == correct
    
    elif vtype == "NumberLine":
        # Ensure integer comparison
        if isinstance(student_answer, str):
            try:
                student_val = int(student_answer)
            except ValueError:
                student_val = -1
        else:
            student_val = student_answer
        is_correct = student_val == correct
    
    elif vtype == "ClockSet":
        # Handle tuple or dict format
        if isinstance(student_answer, dict):
            student_val = (student_answer.get("hours", 0), student_answer.get("minutes", 0))
        else:
            student_val = student_answer
        is_correct = student_val == correct
    
    elif vtype == "SortOrder":
        # Handle potential type mismatches between string and numeric values
        # Convert both to comparable format
        def normalize_sort_item(item):
            # If it's a string that looks like a number, keep as string for consistency
            # This handles fractions like "1/4" correctly
            if isinstance(item, str):
                return item
            # Convert numbers to their string representation for comparison
            # But actually, we want to compare values, not strings
            return item
        
        # Compare element by element with type coercion
        if isinstance(student_answer, list) and isinstance(correct, list):
            if len(student_answer) != len(correct):
                is_correct = False
            else:
                # Compare each element, handling numeric type coercion
                is_correct = True
                for s, c in zip(student_answer, correct):
                    # Both are strings (fractions)
                    if isinstance(s, str) and isinstance(c, str):
                        if s != c:
                            is_correct = False
                            break
                    # Both are numbers (int or float)
                    elif isinstance(s, (int, float)) and isinstance(c, (int, float)):
                        if abs(float(s) - float(c)) > 0.001:  # Float tolerance
                            is_correct = False
                            break
                    else:
                        # Type mismatch - try string comparison
                        if str(s) != str(c):
                            is_correct = False
                            break
        else:
            is_correct = student_answer == correct
    
    else:
        # Exact comparison for other types
        is_correct = student_answer == correct
    
    # Find which trap was triggered
    trap_triggered = None
    if not is_correct:
        for trap_name, trap_data in skeleton["all_traps"].items():
            trap_val = trap_data.get("value") or trap_data.get("position") or trap_data.get("values")
            
            # For PesoMoney, compare against extracted value
            if vtype == "PesoMoney" and isinstance(student_answer, dict):
                student_compare = student_answer.get("total", 0)
            else:
                student_compare = student_answer
            
            if trap_val == student_compare:
                trap_triggered = trap_name
                break
    
    return {
        "is_correct": is_correct,
        "trap_triggered": trap_triggered,
        "correct_answer": correct
    }


# ═══════════════════════════════════════════════════════════════════════════════
# INVARIANT CHECKERS
# ═══════════════════════════════════════════════════════════════════════════════

INVARIANT_CHECKS = {
    "NumberLine": lambda p: (
        p.get("correct_position") is not None and
        0 <= p.get("correct_position", 0) <= p.get("divisions", 1)
    ),
    "ClockSet": lambda p: (
        # Support both 12-hour (1-12) and 24-hour (0-23) formats
        (0 <= p.get("hours", 1) <= 23 if p.get("use_24_hour", False) else 1 <= p.get("hours", 1) <= 12) and
        0 <= p.get("minutes", 0) <= 59
    ),
    "FillInTable": lambda p: (
        len(p.get("blank_inputs", [])) > 0 and
        len(p.get("correct_fills", [])) > 0
    ),
    "PesoMoney": lambda p: (
        p.get("target_amount", 0) > 0
    ),
    "BarChart": lambda p: (
        len(p.get("values", [])) > 0 and
        all(v >= 0 for v in p.get("values", []))
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 1: FILL-IN-TABLE
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_fill_in_table(grade: int, seed: int, difficulty: int, rng: random.Random, competency_text: Optional[str] = None) -> Dict:
    """
    Generate table with blanks for patterns, multiplication tables, function tables.
    """
    
    # Normalize difficulty to int level
    diff_level = _difficulty_level(difficulty)
    
    # Check if competency mentions specific multiplication tables
    force_multiplication = False
    allowed_multipliers = None
    if competency_text:
        import re
        # Check for multiplication table mentions
        mult_match = re.search(r'multiplication table[s]?', competency_text, re.IGNORECASE)
        if mult_match:
            force_multiplication = True
            # Extract specific multipliers like "2, 3, 4, 5, and 10"
            nums_match = re.search(r'(?:the\s+)?([\d,\s]+(?:and\s+\d+)?)\s+multiplication', competency_text, re.IGNORECASE)
            if nums_match:
                nums_str = nums_match.group(1)
                nums = re.findall(r'\d+', nums_str)
                if nums:
                    allowed_multipliers = [int(n) for n in nums]
    
    # Grade-based pattern selection
    if force_multiplication or grade in [2, 3, 4]:
        # Multiplication tables - honor competency-specified multipliers
        if allowed_multipliers:
            multiplier = rng.choice(allowed_multipliers)
        elif grade == 2:
            multiplier = rng.choice([2, 3, 4, 5, 10])
        elif grade == 3:
            multiplier = rng.choice([6, 7, 8, 9])
        else:
            multiplier = rng.choice([2, 3, 4, 5, 6, 7, 8, 9, 10])
        rule = lambda n, m=multiplier: n * m
        rule_desc = f"Multiply by {multiplier}"
        pattern_type = "multiplication"
    
    elif grade <= 2:
        # Simple counting patterns (only if not forced to multiplication)
        if rng.choice([True, False]):
            # Skip counting (2s, 5s, 10s)
            step = rng.choice([2, 5, 10])
            start = rng.randint(0, step)
            rule = lambda n, st=start, s=step: st + s * n
            rule_desc = f"Add {step} each time"
            pattern_type = "skip_count"
        else:
            # Repeating pattern
            pattern = [rng.randint(1, 5) for _ in range(3)]
            rule = lambda n, p=pattern: p[n % len(p)]
            rule_desc = f"Pattern repeats: {pattern}"
            pattern_type = "repeating"
    
    elif grade <= 6:
        # Linear patterns (easier)
        a = rng.choice([2, 3, 4, 5])
        b = rng.randint(0, 10)
        rule = lambda n, a_=a, b_=b: a_ * n + b_
        rule_desc = f"Multiply input by {a}, then add {b}"
        pattern_type = "linear"
    
    else:
        # More complex linear or quadratic
        if diff_level >= 3:  # hard or advanced
            # Quadratic
            a = rng.choice([1, 2, -1, -2])
            rule = lambda n, a_=a: a_ * n * n
            rule_desc = f"Square the input, then multiply by {a}"
            pattern_type = "quadratic"
        else:
            # Linear with negative
            a = rng.choice([-3, -2, -1, 2, 3, 4, 5])
            b = rng.randint(-5, 10)
            rule = lambda n, a_=a, b_=b: a_ * n + b_
            rule_desc = f"Multiply input by {a}, then add {b}"
            pattern_type = "linear"
    
    # Generate table rows
    num_rows = 5 if diff_level == 1 else (6 if diff_level == 2 else 7)
    start_n = 0 if grade <= 3 else 1
    inputs = list(range(start_n, start_n + num_rows))
    
    # Determine which cells are blank
    num_blanks = 2 if diff_level == 1 else (3 if diff_level == 2 else 4)
    blank_indices = rng.sample(range(2, num_rows), num_blanks)  # Never blank first 2 rows
    
    blank_inputs = [inputs[i] for i in blank_indices]
    correct_fills = [rule(n) for n in blank_inputs]
    
    # Build table data
    rows = []
    for i, n in enumerate(inputs):
        if i in blank_indices:
            rows.append([n, None])  # None = blank cell
        else:
            rows.append([n, rule(n)])
    
    params = {
        "columns": ["Input", "Output"],
        "rows": rows,
        "rule": rule,  # Temporarily store for trap generation
        "rule_description": rule_desc,
        "blank_inputs": blank_inputs,
        "correct_fills": correct_fills,  # Store computed answers for validation
        "pattern_type": pattern_type,
    }
    
    # Generate traps
    all_traps = _traps_fill_in_table(params, rng)
    
    # Remove the function before returning (not JSON serializable)
    del params["rule"]
    
    return {
        "skeleton_id": encode_skeleton_id("FillInTable", grade, seed, difficulty),
        "visual_type": "FillInTable",
        "visual_params": params,
        "stem_template": f"Complete the table. {rule_desc}.",
        "correct_answer": correct_fills,
        "all_traps": all_traps,
        "question_mode": "cloze",
        "math_expression": rule_desc,
    }


def _traps_fill_in_table(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for fill-in-table problems."""
    traps = {}
    rule = params["rule"]
    blank_inputs = params["blank_inputs"]
    pattern_type = params.get("pattern_type")
    
    # Universal traps
    for n in blank_inputs:
        correct_val = rule(n)
        
        # Off by one
        traps[f"off_by_one_up_{n}"] = {
            "value": correct_val + 1,
            "description": "Added 1 to correct answer"
        }
        traps[f"off_by_one_down_{n}"] = {
            "value": correct_val - 1,
            "description": "Subtracted 1 from correct answer"
        }
    
    # Pattern-specific traps
    if pattern_type == "multiplication":
        # Extract multiplier
        multiplier = rule(1)
        for n in blank_inputs:
            traps[f"added_instead_{n}"] = {
                "value": n + multiplier,
                "description": "Added instead of multiplied"
            }
            if multiplier > 2:
                traps[f"wrong_times_table_{n}"] = {
                    "value": n * (multiplier - 1),
                    "description": "Used adjacent times table"
                }
    
    elif pattern_type == "linear":
        # Extract a and b from rule
        a = rule(1) - rule(0)
        b = rule(0)
        for n in blank_inputs:
            traps[f"forgot_constant_{n}"] = {
                "value": a * n,
                "description": "Forgot to add constant term"
            }
            traps[f"added_instead_multiplied_{n}"] = {
                "value": a + n + b,
                "description": "Added coefficient instead of multiplying"
            }
    
    # Used previous output
    rows = params.get("rows", [])
    for i, n in enumerate(blank_inputs):
        # Find previous non-blank row
        prev_val = None
        for j in range(len(rows)):
            if rows[j][0] == n:
                # Look back
                for k in range(j - 1, -1, -1):
                    if rows[k][1] is not None:
                        prev_val = rows[k][1]
                        break
                break
        
        if prev_val is not None:
            traps[f"used_previous_{n}"] = {
                "value": prev_val,
                "description": "Copied previous output instead of computing"
            }
    
    return traps


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 2: RULE DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_rule_discovery(grade: int, seed: int, difficulty: int, rng: random.Random, competency_text: Optional[str] = None) -> Dict:
    """
    Show complete input→output table, student types the algebraic rule.
    """

    # Normalize difficulty to int level
    diff_level = _difficulty_level(difficulty)
    
    # Grade-based complexity
    if grade <= 3:
        # Simple multiplication or addition
        if rng.choice([True, False]):
            k = rng.choice([2, 3, 5, 10])
            rule = lambda n: k * n
            rule_expr = f"{k}*n"
        else:
            k = rng.randint(1, 5)
            rule = lambda n: n + k
            rule_expr = f"n+{k}"
    
    elif grade <= 6:
        # Linear: an + b
        a = rng.choice([2, 3, 4, 5])
        b = rng.randint(1, 10)
        rule = lambda n: a * n + b
        rule_expr = f"{a}*n+{b}"
    
    else:
        # More complex
        if diff_level >= 3:
            a = rng.choice([1, 2])
            b = rng.randint(-5, 5)
            c = rng.randint(1, 5)
            rule = lambda n: a * n * n + b * n + c
            rule_expr = f"{a}*n**2+{b}*n+{c}" if b != 0 else f"{a}*n**2+{c}"
        else:
            a = rng.choice([2, 3, 4, 5, -2, -3])
            b = rng.randint(-5, 10)
            rule = lambda n: a * n + b
            rule_expr = f"{a}*n+{b}" if b >= 0 else f"{a}*n{b}"
    
    # Generate complete table
    num_rows = 4 if diff_level == 1 else 5
    start_n = 1
    table = [(n, rule(n)) for n in range(start_n, start_n + num_rows)]
    
    params = {
        "table": table,
        "rule": rule,  # Temporarily store for trap generation
        "rule_expression": rule_expr,
        "variable_name": "n",
    }
    
    all_traps = _traps_rule_discovery(params, rng)
    
    # Remove the function before returning (not JSON serializable)
    del params["rule"]
    
    # Build table display
    table_str = "| n | output |\n|---|---|\n"
    for n, out in table:
        table_str += f"| {n} | {out} |\n"
    
    stem = f"{table_str}\nWhat is the rule? Write it in terms of n."
    
    return {
        "skeleton_id": encode_skeleton_id("RuleDiscovery", grade, seed, difficulty),
        "visual_type": "RuleDiscovery",
        "visual_params": params,
        "stem_template": stem,
        "correct_answer": rule_expr,
        "all_traps": all_traps,
        "question_mode": "expression",
        "math_expression": rule_expr,
    }


def _traps_rule_discovery(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for rule discovery problems."""
    traps = {}
    rule = params["rule"]
    table = params["table"]
    
    # Try to extract linear coefficients
    if len(table) >= 2:
        n1, out1 = table[0]
        n2, out2 = table[1]
        
        # Estimate slope and intercept
        if n2 != n1:
            a_estimate = (out2 - out1) // (n2 - n1)
            b_estimate = out1 - a_estimate * n1
            
            # Coefficient off by one
            traps["coefficient_off_by_one_up"] = {
                "value": f"{a_estimate + 1}*n+{b_estimate}",
                "description": "Multiplier too high by 1"
            }
            traps["coefficient_off_by_one_down"] = {
                "value": f"{a_estimate - 1}*n+{b_estimate}",
                "description": "Multiplier too low by 1"
            }
            
            # Constant off by one
            traps["constant_off_by_one_up"] = {
                "value": f"{a_estimate}*n+{b_estimate + 1}",
                "description": "Constant term too high by 1"
            }
            traps["constant_off_by_one_down"] = {
                "value": f"{a_estimate}*n+{b_estimate - 1}",
                "description": "Constant term too low by 1"
            }
            
            # Forgot constant
            traps["forgot_constant_term"] = {
                "value": f"{a_estimate}*n",
                "description": "Forgot to add constant term"
            }
            
            # Swapped coefficient and constant
            traps["swapped_coefficient_and_constant"] = {
                "value": f"{b_estimate}*n+{a_estimate}",
                "description": "Swapped multiplier and constant"
            }
            
            # Additive instead of multiplicative
            traps["additive_instead"] = {
                "value": f"n+{out2 - n2}",
                "description": "Used constant difference instead of multiplier"
            }
    
    # Used first output as constant rule
    if len(table) > 0:
        first_output = table[0][1]
        traps["constant_rule"] = {
            "value": str(first_output),
            "description": "Thought output is always the same"
        }
    
    return traps


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 3: NUMBER LINE
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_number_line(grade: int, seed: int, difficulty: int, rng: random.Random, competency_text: Optional[str] = None) -> Dict:
    """Generate number line skeleton based on grade-appropriate content."""

    # Normalize difficulty to int level
    diff_level = _difficulty_level(difficulty)
    
    # Grade-based content selection
    if grade <= 2:
        # Whole numbers 0-20
        max_val = 10 if diff_level == 1 else 20
        value = rng.randint(1, max_val - 1)
        divisions = max_val
        params = {
            "value": value,
            "range": [0, max_val],
            "divisions": divisions,
            "content_type": "whole_number"
        }
        correct_position = value
        
    elif grade <= 4:
        # Fractions - check if competency specifies improper/mixed or specific denominators
        allowed_denoms = None
        allow_improper = False
        allow_mixed = False
        
        if competency_text:
            import re
            # Parse for specific denominator mentions like "denominators 2, 4, 5, and 10"
            denom_match = re.search(r'denominators?\s+([\d,\s]+(?:and\s+\d+)?)', competency_text, re.IGNORECASE)
            if denom_match:
                denom_str = denom_match.group(1)
                nums = re.findall(r'\d+', denom_str)
                if nums:
                    allowed_denoms = [int(n) for n in nums]
            
            # Check for improper/mixed fraction mentions
            if re.search(r'improper', competency_text, re.IGNORECASE):
                allow_improper = True
            if re.search(r'mixed', competency_text, re.IGNORECASE):
                allow_mixed = True
        
        if allowed_denoms:
            denominator = rng.choice(allowed_denoms)
        else:
            denominator = rng.choice([2, 3, 4] if diff_level == 1 else [2, 3, 4, 5, 6, 8])
        
        # Decide fraction type based on competency
        if allow_improper or allow_mixed:
            # Generate improper fraction or mixed number
            fraction_type = rng.choice(['improper', 'mixed'] if (allow_improper and allow_mixed) else 
                                       ['improper'] if allow_improper else ['mixed'])
            
            if fraction_type == 'improper':
                # Improper: numerator > denominator (e.g., 5/4, 7/3)
                max_whole = 2 if diff_level == 1 else 3
                whole_part = rng.randint(1, max_whole)
                extra_numerator = rng.randint(1, denominator - 1)
                numerator = whole_part * denominator + extra_numerator
                
                params = {
                    "numerator": numerator,
                    "denominator": denominator,
                    "range": [0, max_whole + 1],
                    "divisions": (max_whole + 1) * denominator,
                    "content_type": "improper_fraction",
                    "fraction_display": f"{numerator}/{denominator}"
                }
                correct_position = numerator
                
            else:  # mixed
                # Mixed: whole and proper fraction (e.g., 1 3/4)
                whole_part = rng.randint(1, 2 if diff_level == 1 else 3)
                proper_numerator = rng.randint(1, denominator - 1)
                
                params = {
                    "whole_part": whole_part,
                    "numerator": proper_numerator,
                    "denominator": denominator,
                    "range": [0, whole_part + 1],
                    "divisions": (whole_part + 1) * denominator,
                    "content_type": "mixed_number",
                    "fraction_display": f"{whole_part} {proper_numerator}/{denominator}"
                }
                # Position is whole_part * denominator + proper_numerator
                correct_position = whole_part * denominator + proper_numerator
        else:
            # Proper fraction (original behavior)
            numerator = rng.randint(1, denominator - 1)
            params = {
                "numerator": numerator,
                "denominator": denominator,
                "range": [0, 1],
                "divisions": denominator,
                "content_type": "fraction"
            }
            correct_position = numerator
        
    elif grade <= 6:
        # Decimals
        decimal_places = 1 if diff_level == 1 else 2
        divisions = 10 if decimal_places == 1 else 100
        value = rng.randint(1, divisions - 1) / divisions
        params = {
            "decimal_value": value,
            "range": [0, 1],
            "divisions": divisions,
            "content_type": "decimal"
        }
        correct_position = int(value * divisions)
        
    else:
        # Integers including negatives
        range_size = 10 if diff_level == 1 else 20
        value = rng.randint(-range_size // 2, range_size // 2)
        while value == 0:
            value = rng.randint(-range_size // 2, range_size // 2)
        params = {
            "value": value,
            "range": [-range_size // 2, range_size // 2],
            "divisions": range_size,
            "content_type": "integer"
        }
        correct_position = value + range_size // 2
    
    params["correct_position"] = correct_position
    params["is_interactive"] = True
    params["labels"] = [str(params["range"][0]), str(params["range"][1])]
    
    # Generate stem based on content type
    content_type = params.get("content_type", "")
    if content_type == "improper_fraction":
        stem = f"Move the dot to show {params['fraction_display']} on the number line."
    elif content_type == "mixed_number":
        stem = f"Move the dot to show {params['fraction_display']} on the number line."
    elif "numerator" in params and "denominator" in params:
        stem = f"Move the dot to show {params['numerator']}/{params['denominator']} on the number line."
    elif "decimal_value" in params:
        stem = f"Move the dot to show {params['decimal_value']} on the number line."
    else:
        stem = f"Move the dot to show {params['value']} on the number line."
    
    all_traps = _traps_number_line(params, rng)
    
    return {
        "skeleton_id": encode_skeleton_id("NumberLine", grade, seed, difficulty),
        "visual_type": "NumberLine",
        "visual_params": params,
        "stem_template": stem,
        "correct_answer": correct_position,
        "all_traps": all_traps,
        "question_mode": "number_line",
    }


def _traps_number_line(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for number line problems."""
    traps = {}
    correct_pos = params["correct_position"]
    divisions = params["divisions"]
    content_type = params.get("content_type")
    
    # Universal traps
    if correct_pos > 0:
        traps["off_by_one_left"] = {
            "position": correct_pos - 1,
            "description": "One division to the left"
        }
    if correct_pos < divisions:
        traps["off_by_one_right"] = {
            "position": correct_pos + 1,
            "description": "One division to the right"
        }
    
    # Fraction-specific traps
    if content_type == "fraction":
        n = params["numerator"]
        d = params["denominator"]
        
        # Numerator only
        if n <= divisions and n != correct_pos:
            traps["numerator_only"] = {
                "position": n,
                "description": "Used only numerator, ignored denominator"
            }
        
        # Denominator only
        if d <= divisions and d != correct_pos:
            traps["denominator_only"] = {
                "position": d,
                "description": "Used only denominator, ignored numerator"
            }
        
        # Larger denominator = larger value misconception
        if d > 2:
            wrong_pos = round(n / (d * 2) * divisions)
            if wrong_pos != correct_pos and 0 <= wrong_pos <= divisions:
                traps["larger_denom_larger_value"] = {
                    "position": wrong_pos,
                    "description": "Thinks larger denominator means larger fraction"
                }
        
        # Inverted fraction
        if n != d and n != 0:
            inverted_pos = round((d / n) * divisions)
            if inverted_pos != correct_pos and 0 <= inverted_pos <= divisions:
                traps["inverted_fraction"] = {
                    "position": inverted_pos,
                    "description": "Flipped numerator and denominator"
                }
    
    # Integer-specific traps (with negatives)
    elif content_type == "integer":
        value = params["value"]
        range_min = params["range"][0]
        
        if value < 0:
            # Ignore negative sign
            positive_pos = -value + divisions // 2
            if positive_pos != correct_pos and 0 <= positive_pos <= divisions:
                traps["ignore_negative"] = {
                    "position": positive_pos,
                    "description": "Ignored negative sign"
                }
            
            # Negative magnitude confusion: -5 > -3 because 5 > 3
            if abs(value) > 2:
                confused_pos = (-abs(value) + 2) + divisions // 2
                if confused_pos != correct_pos and 0 <= confused_pos <= divisions:
                    traps["negative_magnitude_confusion"] = {
                        "position": confused_pos,
                        "description": "Compared absolute values incorrectly"
                    }
    
    # Decimal-specific traps
    elif content_type == "decimal":
        dec_val = params["decimal_value"]
        # Whole number thinking: 0.25 > 0.3 because 25 > 3
        if divisions == 100:
            # Extract digits
            digits_str = str(dec_val).replace("0.", "")
            if len(digits_str) == 2:
                wrong_val = int(digits_str[0]) / 10  # Use only first digit
                wrong_pos = int(wrong_val * divisions)
                if wrong_pos != correct_pos and 0 <= wrong_pos <= divisions:
                    traps["whole_number_decimal_thinking"] = {
                        "position": wrong_pos,
                        "description": "Compared decimal digits as whole numbers"
                    }
    
    return traps


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 4: CONSTRAINT SATISFACTION
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_constraint_satisfaction(grade: int, seed: int, difficulty: int, rng: random.Random, competency_text: Optional[str] = None) -> Dict:
    """
    Student must enter ANY value satisfying multiple constraints.
    """
    
    # Normalize difficulty to int level
    diff_level = _difficulty_level(difficulty)
    
    # Grade-based constraint complexity
    if grade <= 3:
        # Simple numeric constraints
        constraints = [
            ("greater than", rng.randint(5, 15)),
            ("less than", rng.randint(20, 30)),
        ]
        if diff_level != 1:
            constraints.append(("even" if rng.choice([True, False]) else "odd", None))
    
    elif grade <= 6:
        # Add divisibility
        min_val = rng.randint(10, 30)
        max_val = rng.randint(50, 100)
        divisor = rng.choice([2, 3, 5])
        
        constraints = [
            ("greater than", min_val),
            ("less than", max_val),
            ("multiple of", divisor),
        ]
        if diff_level >= 3:
            constraints.append(("odd" if divisor != 2 else "even", None))
    
    else:
        # More complex (grades 7+)
        min_val = rng.randint(20, 50)
        max_val = rng.randint(80, 150)
        divisor = rng.choice([3, 5, 7])
        
        constraints = [
            ("greater than", min_val),
            ("less than", max_val),
            ("multiple of", divisor),
        ]
        
        # For higher difficulties, add a property constraint
        # But be careful not to make it impossible
        if diff_level >= 3:
            # Instead of prime/composite with divisibility (too restrictive),
            # use even/odd which is more compatible with divisibility
            if divisor % 2 == 0:
                # If divisor is even (won't happen with 3,5,7), require even
                constraints.append(("even", None))
            else:
                # For odd divisors, we can add either even or odd
                # But odd + multiple of odd is more solvable
                constraints.append(("odd", None))
    
    # Compute valid answers
    valid_answers = []
    # Wider search range to ensure we find valid answers
    search_range = range(1, 300)
    
    for x in search_range:
        passes_all = True
        for constraint_type, value in constraints:
            if constraint_type == "greater than" and not (x > value):
                passes_all = False
            elif constraint_type == "less than" and not (x < value):
                passes_all = False
            elif constraint_type == "multiple of" and not (x % value == 0):
                passes_all = False
            elif constraint_type == "even" and not (x % 2 == 0):
                passes_all = False
            elif constraint_type == "odd" and not (x % 2 == 1):
                passes_all = False
            elif constraint_type == "prime" and not _is_prime(x):
                passes_all = False
            elif constraint_type == "composite" and not (_is_composite(x)):
                passes_all = False
        
        if passes_all:
            valid_answers.append(x)
    
    if not valid_answers:
        raise ValueError("No valid answers for constraints")
    
    # Build constraint descriptions
    constraint_descs = []
    for ctype, val in constraints:
        if val is not None:
            constraint_descs.append(f"{ctype} {val}")
        else:
            constraint_descs.append(ctype)
    
    params = {
        "constraints": constraints,
        "valid_answers": valid_answers,
        "constraint_descriptions": constraint_descs,
    }
    
    all_traps = _traps_constraint_satisfaction(params, rng)
    
    stem = "Enter a number that is: " + ", ".join(constraint_descs) + "."
    
    return {
        "skeleton_id": encode_skeleton_id("ConstraintSatisfaction", grade, seed, difficulty),
        "visual_type": "ConstraintSatisfaction",
        "visual_params": params,
        "stem_template": stem,
        "correct_answer": valid_answers[0],  # Any valid answer
        "all_traps": all_traps,
        "question_mode": "constraint",
    }


def _traps_constraint_satisfaction(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for constraint satisfaction problems."""
    traps = {}
    constraints = params["constraints"]
    valid_answers = params["valid_answers"]
    
    if not valid_answers:
        return traps
    
    first_valid = valid_answers[0]
    
    # Boundary violations
    for ctype, val in constraints:
        if ctype == "greater than":
            traps["boundary_violation_low"] = {
                "value": val,
                "description": "Used boundary value, not greater than it"
            }
        elif ctype == "less than":
            traps["boundary_violation_high"] = {
                "value": val,
                "description": "Used boundary value, not less than it"
            }
    
    # Satisfies n-1 constraints
    # Pick one constraint to violate
    if len(constraints) > 1:
        for i, (ctype, val) in enumerate(constraints):
            # Find a number that satisfies all BUT this constraint
            for x in range(1, 200):
                satisfies_others = True
                for j, (ctype2, val2) in enumerate(constraints):
                    if i == j:
                        continue
                    if ctype2 == "greater than" and not (x > val2):
                        satisfies_others = False
                    elif ctype2 == "less than" and not (x < val2):
                        satisfies_others = False
                    elif ctype2 == "multiple of" and not (x % val2 == 0):
                        satisfies_others = False
                    elif ctype2 == "even" and not (x % 2 == 0):
                        satisfies_others = False
                    elif ctype2 == "odd" and not (x % 2 == 1):
                        satisfies_others = False
                
                # Now check it FAILS constraint i
                fails_this = False
                if ctype == "greater than" and not (x > val):
                    fails_this = True
                elif ctype == "less than" and not (x < val):
                    fails_this = True
                elif ctype == "multiple of" and not (x % val == 0):
                    fails_this = True
                elif ctype == "even" and not (x % 2 == 0):
                    fails_this = True
                elif ctype == "odd" and not (x % 2 == 1):
                    fails_this = True
                
                if satisfies_others and fails_this and x not in valid_answers:
                    traps[f"missing_constraint_{i}"] = {
                        "value": x,
                        "description": f"Satisfies all but '{ctype}' constraint"
                    }
                    break
    
    # Wrong parity
    for ctype, val in constraints:
        if ctype in ["even", "odd"]:
            # Find a valid answer with wrong parity
            opposite_parity = "odd" if ctype == "even" else "even"
            for x in range(1, 200):
                if opposite_parity == "even" and x % 2 == 0:
                    # Check if this passes other constraints
                    passes_others = True
                    for ctype2, val2 in constraints:
                        if ctype2 == ctype:
                            continue
                        if ctype2 == "greater than" and not (x > val2):
                            passes_others = False
                        elif ctype2 == "less than" and not (x < val2):
                            passes_others = False
                        elif ctype2 == "multiple of" and not (x % val2 == 0):
                            passes_others = False
                    
                    if passes_others and x not in valid_answers:
                        traps["wrong_parity"] = {
                            "value": x,
                            "description": f"Should be {ctype}, not {opposite_parity}"
                        }
                        break
                elif opposite_parity == "odd" and x % 2 == 1:
                    passes_others = True
                    for ctype2, val2 in constraints:
                        if ctype2 == ctype:
                            continue
                        if ctype2 == "greater than" and not (x > val2):
                            passes_others = False
                        elif ctype2 == "less than" and not (x < val2):
                            passes_others = False
                        elif ctype2 == "multiple of" and not (x % val2 == 0):
                            passes_others = False
                    
                    if passes_others and x not in valid_answers:
                        traps["wrong_parity"] = {
                            "value": x,
                            "description": f"Should be {ctype}, not {opposite_parity}"
                        }
                        break
    
    return traps


def _is_prime(n: int) -> bool:
    """Check if n is prime."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def _is_composite(n: int) -> bool:
    """Check if n is composite."""
    return n > 1 and not _is_prime(n)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 5: PESO MONEY
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_peso_money(grade: int, seed: int, difficulty: int, rng: random.Random,
                    competency_text: Optional[str] = None,
                    axis_values: Optional[dict] = None) -> Dict:
    """
    Drag peso coins and bills to make a target amount.
    Uses SCALAR CURRICULUM-DRIVEN DIFFICULTY with independent dimension scaling.
    """
    from .curriculum_context import get_curriculum_context, TRADITIONAL_DEFAULTS
    from .difficulty_engine import (
        normalize_difficulty,
        compute_dimension_context,
        select_denominations
    )
    from .divisibility import select_number_by_divisibility
    
    # Normalize difficulty to scalar with randomization within ranges
    # Difficulty windows:
    # 1 (Easy): 0.0-0.3
    # 2 (Medium): 0.3-0.7
    # 3 (Hard): 0.7-1.0
    # 4 (Advanced): 1.0-1.2
    
    base_difficulty = normalize_difficulty(difficulty)
    
    # Map to difficulty windows and randomize within range
    if isinstance(difficulty, int):
        if difficulty == 1:
            # Easy: randomize 0.0-0.3
            scalar_difficulty = rng.uniform(0.0, 0.3)
        elif difficulty == 2:
            # Medium: randomize 0.3-0.7
            scalar_difficulty = rng.uniform(0.3, 0.7)
        elif difficulty == 3:
            # Hard: randomize 0.7-1.0
            scalar_difficulty = rng.uniform(0.7, 1.0)
        elif difficulty == 4:
            # Advanced: randomize 1.0-1.2
            scalar_difficulty = rng.uniform(1.0, 1.2)
        else:
            scalar_difficulty = base_difficulty
    else:
        # Already a float, use as-is
        scalar_difficulty = base_difficulty
    
    # Get curriculum context
    if competency_text:
        context = get_curriculum_context(competency_text)
    else:
        # Fallback: use grade-based defaults
        context = {
            "grade": grade,
            "strand": "Number and Algebra",
            "quarter": 1,
            "explicit_limit": None,
            "explicit_denominations": None,
            "exclude_centavos": True,
            "prev_node": None,
            "next_node": None,
            "traditional_defaults": TRADITIONAL_DEFAULTS.get(grade, TRADITIONAL_DEFAULTS[5]),
            "competency": {"text": ""}
        }
    
    # Compute all dimension values
    dims = compute_dimension_context(context, "PesoMoney", scalar_difficulty)
    
    # Get dimension values (with fallbacks if dims incomplete)
    amount_percentile = dims.get("amount_percentile", scalar_difficulty)
    divisibility_target = dims.get("divisibility", scalar_difficulty)
    denom_ratio = dims.get("denom_ratio", 1.0 - scalar_difficulty * 0.6)
    require_optimal_threshold = dims.get("require_optimal", scalar_difficulty)
    min_pieces = dims.get("min_pieces", int(1 + scalar_difficulty * 5))
    
    # Select available denominations (using legacy function for now)
    available = select_denominations(context, difficulty, rng)

    # Honour denomination_type axis override
    if axis_values:
        dt = axis_values.get('denomination_type')
        if dt == 'coins_only':
            available = [d for d in available if d <= 20]
            if not available:
                available = [1, 5, 10, 20]
        elif dt == 'bills_only':
            available = [d for d in available if d >= 50]
            if not available:
                available = [50, 100, 200]
        # 'mixed' keeps available as-is
    
    # Compute amount range from curriculum (or axis_values override)
    explicit_limit = context.get("explicit_limit")
    prev_node = context.get("prev_node")

    # Honour explicit amount_range axis override
    if axis_values:
        ar_map = {'up_to_100': 100, 'up_to_1000': 1000, 'up_to_10000': 10000}
        ar_key = axis_values.get('amount_range')
        if ar_key and ar_key in ar_map:
            explicit_limit = ar_map[ar_key]
    
    if explicit_limit:
        ceiling = explicit_limit
        if prev_node and prev_node.get("limit") and prev_node["limit"] < ceiling:
            floor = prev_node["limit"]
        else:
            floor = max(int(ceiling * 0.1), 10)
    else:
        defaults = context.get("traditional_defaults", TRADITIONAL_DEFAULTS[5])
        ceiling = defaults.get("max_amount", 1000)
        floor = defaults.get("min_amount", 10)
    
    # Interpolate target amount based on amount_percentile
    # Use logarithmic scaling when range is large (ratio >= 10)
    # This ensures gradual progression at lower difficulties
    target_range = ceiling - floor
    use_log_scale = floor > 0 and ceiling / floor >= 10
    
    if use_log_scale:
        # Log scaling: floor * (ceiling/floor)^t
        # Example: floor=100, ceiling=10000, t=0.5 → 100 * (100)^0.5 = 1000
        target_base = int(floor * pow(ceiling / floor, amount_percentile))
    else:
        # Linear scaling for small ranges
        target_base = floor + int(amount_percentile * target_range)
    
    # Select target using divisibility difficulty
    # Window size should be proportional to target_base, not full range
    # This preserves the log scaling behavior at low difficulties
    if use_log_scale:
        # Window is ±30% of target_base (maintains proportional variety)
        window_size = max(int(target_base * 0.3), 20)
    else:
        # Linear: fixed percentage of range
        window_size = max(int(target_range * 0.3), 20)
    
    # Add randomness to window position for more variety
    window_offset = rng.randint(-window_size // 4, window_size // 4)
    target_center = target_base + window_offset
    
    target_min = max(floor, target_center - window_size // 2)
    target_max = min(ceiling, target_center + window_size // 2)
    
    target = select_number_by_divisibility(
        target_min,
        target_max,
        divisibility_target,
        rng
    )
    
    # Ensure target is reachable with available denominations (greedy check)
    def greedy_change(amount, denoms):
        result = []
        remaining = amount
        for d in sorted(denoms, reverse=True):
            while remaining >= d:
                result.append(d)
                remaining -= d
        return result if remaining == 0 else None
    
    solution = greedy_change(target, available)
    if not solution:
        # Fallback: pick a reachable target from available denominations
        reachable = [d for d in available if target_min <= d <= target_max]
        if reachable:
            target = rng.choice(reachable)
            solution = [target]
        else:
            # Last resort: use smallest denomination
            target = available[0]
            solution = [target]
    
    # Determine if optimal solution is required
    require_fewest = scalar_difficulty >= require_optimal_threshold
    
    params = {
        "target_amount": target,
        "available_denominations": available,
        "greedy_solution": solution,
        "require_fewest": require_fewest,
        "difficulty_scalar": scalar_difficulty,  # Include for debugging
    }
    
    all_traps = _traps_peso_money(params, rng)
    
    # Stem based on difficulty
    stem = f"Use coins and bills to make exactly ₱{target}."
    if require_fewest:
        stem += " Use the fewest pieces possible."
    
    return {
        "skeleton_id": encode_skeleton_id("PesoMoney", grade, seed, difficulty),
        "visual_type": "PesoMoney",
        "visual_params": params,
        "stem_template": stem,
        "correct_answer": target,  # Sum must equal this
        "all_traps": all_traps,
        "question_mode": "currency_picker",
    }


def _traps_peso_money(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for peso money problems."""
    traps = {}
    target = params["target_amount"]
    available = params["available_denominations"]
    
    # Overcounted
    traps["overcounted"] = {
        "value": target + rng.choice([1, 5, 10]),
        "description": "Total is more than target"
    }
    
    # Undercounted
    traps["undercounted"] = {
        "value": target - rng.choice([1, 5, 10]),
        "description": "Total is less than target"
    }
    
    # Wrong denomination count (e.g., 3×₱20 instead of 2×₱20)
    if target >= 20:
        traps["wrong_denomination_count"] = {
            "value": target + 20,
            "description": "Used too many of one denomination"
        }
    
    # Doubled a denomination
    if target >= 10:
        traps["doubled_denomination"] = {
            "value": target + 10,
            "description": "Counted one denomination twice"
        }
    
    return traps


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 6: BAR CHART
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_bar_chart(grade: int, seed: int, difficulty: int, rng: random.Random,
                   competency_text: Optional[str] = None,
                   axis_values: Optional[dict] = None) -> Dict:
    """
    Build a bar chart or pictograph based on grade-appropriate data visualization.
    
    Supports two modes:
    - CREATE mode (plotter_bar): Student builds chart from given data
    - READ mode (read_bar): Chart is pre-filled, student reports values
    
    Grade progression (based on MATATAG):
    - Grade 1-2: Pictographs (simple icons, scale of 1 or simple scale)
    - Grade 3: Single bar graphs (horizontal or vertical)
    - Grade 4: Focus shifts to line graphs (bar chart less common)
    - Grade 5+: Double bar graphs (comparing two data sets)
    """
    import re

    # Normalize difficulty to int level
    diff_level = _difficulty_level(difficulty)
    
    # Parse competency for specific requirements
    is_pictograph = False
    is_double_bar = False
    is_horizontal = False
    has_scale = True
    is_read_mode = False  # READ mode: chart is pre-filled, student reads values
    
    if competency_text:
        # Determine if this is a READ (interpret) or CREATE (present/construct) task
        # "organize...into a table" means READ the graph and output to table
        if re.search(r'interpret|read|analyze|into.*table|organize.*into', competency_text, re.IGNORECASE):
            is_read_mode = True
        
        if re.search(r'pictograph', competency_text, re.IGNORECASE):
            is_pictograph = True
            if re.search(r'without.*scale', competency_text, re.IGNORECASE):
                has_scale = False
        if re.search(r'double.*bar', competency_text, re.IGNORECASE):
            is_double_bar = True
        if re.search(r'horizontal', competency_text, re.IGNORECASE):
            is_horizontal = True
    
    # Grade-based defaults if competency doesn't specify
    if not competency_text:
        if grade <= 2:
            is_pictograph = True
            has_scale = (grade == 2)  # G1: no scale, G2: with scale
        elif grade >= 5:
            is_double_bar = (diff_level >= 2)  # Higher difficulty = double bar
    
    # Number of categories based on grade and difficulty
    if grade <= 2:
        num_categories = 2 if diff_level == 1 else 3
    elif grade <= 4:
        num_categories = 3 if diff_level == 1 else 4
    else:
        num_categories = 4 if diff_level == 1 else 5
    
    # Value range based on grade
    if grade <= 2:
        max_y = 5 if diff_level == 1 else 10
        scale = 1 if not has_scale else (1 if grade == 1 else 2)
    elif grade <= 4:
        max_y = 10 if diff_level == 1 else 20
        scale = 2 if diff_level == 1 else 5
    else:
        max_y = 20 if diff_level == 1 else 50
        scale = 5 if diff_level == 1 else 10

    # Honour explicit scale axis override
    if axis_values:
        scale_map = {'scale_2': 2, 'scale_5': 5, 'scale_10': 10, 'scale_20': 20}
        sv = axis_values.get('scale') or axis_values.get('scale_type')
        if sv and sv in scale_map:
            scale = scale_map[sv]
            max_y = scale * 10  # adjust max to match scale
    
    # Generate age-appropriate category labels
    if grade <= 2:
        # Simple, concrete categories for young learners
        category_sets = [
            ["Apples", "Bananas", "Oranges"],
            ["Dogs", "Cats", "Birds"],
            ["Red", "Blue", "Green", "Yellow"],
            ["Boys", "Girls"],
            ["Sunny", "Rainy", "Cloudy"],
        ]
    elif grade <= 4:
        category_sets = [
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            ["Grade 1", "Grade 2", "Grade 3", "Grade 4"],
            ["Math", "Science", "English", "Filipino"],
            ["Week 1", "Week 2", "Week 3", "Week 4"],
        ]
    else:
        category_sets = [
            ["Jan", "Feb", "Mar", "Apr", "May"],
            ["Store A", "Store B", "Store C", "Store D", "Store E"],
            ["2020", "2021", "2022", "2023", "2024"],
            ["Team 1", "Team 2", "Team 3", "Team 4"],
        ]
    
    labels = rng.choice([c[:num_categories] for c in category_sets if len(c) >= num_categories])
    
    # Generate values (multiples of scale for cleaner reading)
    if is_pictograph and not has_scale:
        # No scale = small whole numbers
        values = [rng.randint(1, 5) for _ in range(num_categories)]
    else:
        # Round to scale multiples
        values = [rng.randint(1, max_y // scale) * scale for _ in range(num_categories)]
    
    # Double bar chart: add second data set
    if is_double_bar:
        values2 = [rng.randint(1, max_y // scale) * scale for _ in range(num_categories)]
        series_labels = ["Group A", "Group B"] if grade <= 4 else ["This Year", "Last Year"]
    else:
        values2 = None
        series_labels = None
    
    params = {
        "labels": labels,
        "values": values,
        "values2": values2,  # For double bar charts
        "series_labels": series_labels,
        "title": "Data",
        "max_y": max_y,
        "scale": scale,
        "orientation": "horizontal" if is_horizontal else "vertical",
        "is_pictograph": is_pictograph,
        "has_scale": has_scale,
        "is_read_mode": is_read_mode,  # True = chart pre-filled, student reads values
        "is_interactive": not is_read_mode,  # Read mode = not interactive (just display)
    }
    
    all_traps = _traps_bar_chart(params, rng)
    
    # Build grade-appropriate stem based on mode
    if is_read_mode:
        # READ MODE: Chart is shown, student reports values
        if is_pictograph:
            if not has_scale:
                stem = "Look at the picture graph. How many are in each category? Enter the values."
            else:
                stem = f"Look at the picture graph. Each symbol equals {scale}. How many are in each category?"
        elif is_double_bar:
            # For read mode, ask about specific comparisons
            ask_idx = rng.randint(0, num_categories - 1)
            stem = f"Look at the double bar graph. What is the value for {labels[ask_idx]} in {series_labels[0]}?"
            # For read mode with specific question, correct answer is just that value
            params["ask_category"] = labels[ask_idx]
            params["ask_series"] = series_labels[0]
        else:
            # Single bar - ask for all values or specific value
            if diff_level == 1:
                # Easy: ask for one specific value
                ask_idx = rng.randint(0, num_categories - 1)
                stem = f"Look at the bar graph. What is the value for {labels[ask_idx]}?"
                params["ask_category"] = labels[ask_idx]
            else:
                # Harder: ask for all values
                stem = "Look at the bar graph. What is the value for each category?"
    else:
        # CREATE MODE: Student builds the chart
        if is_pictograph:
            if not has_scale:
                # Grade 1: Simple pictograph without scale
                data_str = ", ".join([f"{labels[i]}: {values[i]}" for i in range(len(labels))])
                stem = f"Make a picture graph to show: {data_str}. Draw one picture for each item."
            else:
                # Grade 2: Pictograph with scale
                data_str = ", ".join([f"{labels[i]}: {values[i]}" for i in range(len(labels))])
                stem = f"Make a picture graph to show: {data_str}. Each picture equals {scale}."
        elif is_double_bar:
            # Grade 5+: Double bar chart
            data1_str = ", ".join([f"{labels[i]}: {values[i]}" for i in range(len(labels))])
            data2_str = ", ".join([f"{labels[i]}: {values2[i]}" for i in range(len(labels))])
            stem = f"Create a double bar graph. {series_labels[0]}: {data1_str}. {series_labels[1]}: {data2_str}."
        else:
            # Grade 3-4: Single bar chart
            data_str = ", ".join([f"{labels[i]}: {values[i]}" for i in range(len(labels))])
            orientation_hint = " (horizontal bars)" if is_horizontal else ""
            stem = f"Create a bar graph{orientation_hint} to show: {data_str}"
    
    # Determine correct answer based on mode
    if is_read_mode:
        if params.get("ask_category"):
            # Specific question - answer is single value
            ask_idx = labels.index(params["ask_category"])
            if params.get("ask_series") and values2:
                correct_answer = values[ask_idx] if params["ask_series"] == series_labels[0] else values2[ask_idx]
            else:
                correct_answer = values[ask_idx]
        else:
            # All values question
            correct_answer = values if not is_double_bar else [values, values2]
    else:
        correct_answer = values if not is_double_bar else [values, values2]
    
    # Determine question mode
    question_mode = "read_bar" if is_read_mode else "plotter_bar"
    
    return {
        "skeleton_id": encode_skeleton_id("BarChart", grade, seed, difficulty),
        "visual_type": "BarChart",
        "visual_params": params,
        "stem_template": stem,
        "correct_answer": correct_answer,
        "all_traps": all_traps,
        "question_mode": question_mode,
    }


def _traps_bar_chart(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for bar chart problems."""
    traps = {}
    values = params["values"]
    
    # Swapped adjacent bars
    if len(values) >= 2:
        swapped = values.copy()
        idx = rng.randint(0, len(values) - 2)
        swapped[idx], swapped[idx + 1] = swapped[idx + 1], swapped[idx]
        traps["swapped_adjacent"] = {
            "values": swapped,
            "description": "Two adjacent bars swapped"
        }
    
    # All bars same height (mean or mode)
    mean_val = sum(values) // len(values)
    traps["all_same_height"] = {
        "values": [mean_val] * len(values),
        "description": "Made all bars the same height"
    }
    
    # Off by one grid line
    off_by_one = [v + 1 if rng.choice([True, False]) else v - 1 for v in values]
    traps["off_by_grid_line"] = {
        "values": off_by_one,
        "description": "One grid line off for some bars"
    }
    
    # Doubled one value
    if len(values) >= 1:
        doubled = values.copy()
        doubled[0] = doubled[0] * 2
        traps["doubled_value"] = {
            "values": doubled,
            "description": "Doubled one category's value"
        }
    
    # Reversed order
    traps["reversed_order"] = {
        "values": list(reversed(values)),
        "description": "Bar order reversed"
    }
    
    return traps


# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 7: CLOCK SET
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_clock_set(grade: int, seed: int, difficulty: int, rng: random.Random,
                   competency_text: Optional[str] = None,
                   axis_values: Optional[dict] = None) -> Dict:
    """
    Drag clock hands to show a specified time.
    Supports both 12-hour and 24-hour formats.
    Grade 5+ automatically uses 24-hour time (matches MATATAG curriculum).
    """
    use_24_hour = (grade >= 5)

    # Normalize difficulty
    if isinstance(difficulty, int):
        diff_level = difficulty
    else:
        diff_level = 2

    # Honour explicit precision axis override
    precision_override = (axis_values or {}).get('precision')
    precision_minute_choices = {
        'hour':         [0],
        'half_hour':    [0, 30],
        'quarter_hour': [0, 15, 30, 45],
        'five_minutes': [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
        'one_minute':   list(range(60)),
    }

    if precision_override and precision_override in precision_minute_choices:
        minute_choices = precision_minute_choices[precision_override]
        snap_interval = {
            'hour': 60, 'half_hour': 30, 'quarter_hour': 15,
            'five_minutes': 5, 'one_minute': 1,
        }.get(precision_override, 5)
    elif diff_level == 1:
        minute_choices = [0, 30]
        snap_interval = 30
    elif diff_level == 2:
        minute_choices = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
        snap_interval = 5
    else:
        minute_choices = list(range(60))
        snap_interval = 1

    hours = rng.randint(1, 12)
    if use_24_hour:
        hours = rng.randint(0, 23)
    minutes = rng.choice(minute_choices)

    display_hours = hours % 12 or 12

    minute_angle = (minutes / 60) * 360
    hour_angle = ((display_hours % 12) / 12) * 360 + (minutes / 60) * 30

    params = {
        "target_time": f"{hours:02d}:{minutes:02d}" if use_24_hour else f"{hours}:{minutes:02d}",
        "use_24_hour": use_24_hour,
        "hours": hours,
        "minutes": minutes,
        "display_hours": display_hours,
        "minute_angle": minute_angle,
        "hour_angle": hour_angle,
        "minute_snap_interval": snap_interval,
    }
    
    all_traps = _traps_clock_set(params, rng)
    
    # Format time string
    if use_24_hour:
        time_str = f"{hours:02d}:{minutes:02d}"
        stem = f"Set the clock to show {time_str} (24-hour time)."
    else:
        if minutes == 0:
            time_str = f"{hours}:00"
        else:
            time_str = f"{hours}:{minutes:02d}"
        stem = f"Set the clock to show {time_str}."
    
    return {
        "skeleton_id": encode_skeleton_id("ClockSet", grade, seed, difficulty),
        "visual_type": "ClockSet",
        "visual_params": params,
        "stem_template": stem,
        "correct_answer": (hours, minutes),
        "all_traps": all_traps,
        "question_mode": "clock_set",
    }


def _traps_clock_set(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for clock setting problems."""
    traps = {}
    hours = params["hours"]
    minutes = params["minutes"]
    use_24_hour = params.get("use_24_hour", False)
    
    # For trap generation, we need the 12-hour display version
    display_hours = hours % 12
    if display_hours == 0:
        display_hours = 12
    
    # Hour-minute swap (only if minutes could be a valid hour)
    if minutes <= 12:
        traps["hour_minute_swap"] = {
            "value": (minutes if not use_24_hour else minutes, hours),
            "description": "Swapped hour and minute hands"
        }
    
    # Off by one hour on the clock face
    hour_up = (display_hours % 12) + 1
    hour_down = display_hours - 1 if display_hours > 1 else 12
    
    # Convert back to 24-hour if needed
    if use_24_hour:
        # Keep in same half of day
        is_afternoon = hours >= 12
        hour_up_24 = hour_up if not is_afternoon else (hour_up if hour_up == 12 else hour_up + 12)
        hour_down_24 = hour_down if not is_afternoon else (hour_down if hour_down == 12 else hour_down + 12)
        
        # Handle wraparound at midnight/noon
        if is_afternoon and hour_up == 1:
            hour_up_24 = 13
        if not is_afternoon and hour_down == 12:
            hour_down_24 = 23
            
        traps["off_by_one_hour_up"] = {
            "value": (hour_up_24, minutes),
            "description": "Hour hand one position ahead"
        }
        traps["off_by_one_hour_down"] = {
            "value": (hour_down_24, minutes),
            "description": "Hour hand one position behind"
        }
    else:
        traps["off_by_one_hour_up"] = {
            "value": (hour_up, minutes),
            "description": "Hour hand one position ahead"
        }
        traps["off_by_one_hour_down"] = {
            "value": (hour_down, minutes),
            "description": "Hour hand one position behind"
        }
    
    # Off by 5 minutes
    if minutes >= 5:
        traps["off_by_five_minutes_down"] = {
            "value": (hours, minutes - 5),
            "description": "Minute hand 5 minutes behind"
        }
    if minutes <= 54:
        traps["off_by_five_minutes_up"] = {
            "value": (hours, minutes + 5),
            "description": "Minute hand 5 minutes ahead"
        }
    
    # Forgot hour hand movement - hour hand exactly on the hour mark
    # This should be different from the correct answer
    if minutes != 0:
        # Student puts hour hand exactly on the display hour, not accounting for minute movement
        # The hour hand should actually be between hours
        # So the trap is: user might round to nearest hour
        nearest_hour = display_hours if minutes < 30 else (display_hours % 12) + 1
        if nearest_hour == 0:
            nearest_hour = 12
        
        # Convert to 24-hour if needed
        if use_24_hour:
            is_afternoon = hours >= 12
            trap_hour = nearest_hour if not is_afternoon else (nearest_hour if nearest_hour == 12 else nearest_hour + 12)
            if is_afternoon and nearest_hour == 1:
                trap_hour = 13
        else:
            trap_hour = nearest_hour
            
        # Only add if different from correct
        if trap_hour != hours:
            traps["hour_hand_rounded"] = {
                "value": (trap_hour, minutes),
                "description": "Hour hand rounded to nearest hour mark"
            }
    
    return traps


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 9: SORT/ORDER
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_sort_order(grade: int, seed: int, difficulty: int, rng: random.Random, competency_text: Optional[str] = None) -> Dict:
    """
    Drag items into correct order (smallest to largest, or vice versa).
    Respects competency text for content type, direction, and number range.
    """
    import re

    # Normalize difficulty to int level
    diff_level = _difficulty_level(difficulty)
    
    # Number of items
    num_items = 3 if diff_level == 1 else (4 if diff_level == 2 else 5)
    
    # Parse competency for content type and direction
    content_type = None
    direction = "ascending"  # default
    max_value = None
    
    if competency_text:
        # Extract max value FIRST (e.g., "up to 20", "up to 10 000", "up to 1000")
        # Handle spaces in numbers like "10 000"
        max_match = re.search(r'up to (\d[\d\s]*\d|\d+)', competency_text, re.IGNORECASE)
        if max_match:
            max_str = max_match.group(1).replace(' ', '').replace(',', '')
            max_value = int(max_str)
        
        # Determine content type from competency text
        if re.search(r'\bfraction', competency_text, re.IGNORECASE):
            content_type = "fraction"
        elif re.search(r'\bdecimal', competency_text, re.IGNORECASE):
            content_type = "decimal"
        elif re.search(r'\binteger|negative', competency_text, re.IGNORECASE):
            content_type = "integer"
        elif re.search(r'\bnumber|whole number', competency_text, re.IGNORECASE) or max_value:
            # If it says "numbers" or has a max value, use whole numbers
            content_type = "whole"
        
        # Determine direction
        if re.search(r'largest.*smallest|descending', competency_text, re.IGNORECASE):
            direction = "descending"
        elif re.search(r'vice versa', competency_text, re.IGNORECASE):
            # "vice versa" means both directions are valid - randomly choose
            direction = rng.choice(["ascending", "descending"])
    
    # Generate items based on content type
    # PRIORITY: explicit content_type from competency > grade-based default
    
    if content_type == "fraction":
        # Fractions with same denominator - ensure unique numerators
        d = rng.choice([2, 3, 4, 5, 6, 8])
        max_numerators = min(d, num_items + 2)
        available_numerators = list(range(1, max_numerators + 1))
        chosen_numerators = rng.sample(available_numerators, min(num_items, len(available_numerators)))
        while len(chosen_numerators) < num_items and len(available_numerators) > len(chosen_numerators):
            remaining = [n for n in available_numerators if n not in chosen_numerators]
            if remaining:
                chosen_numerators.append(rng.choice(remaining))
            else:
                break
        if len(chosen_numerators) < num_items:
            # Fallback to whole numbers
            items = rng.sample(range(1, 50), num_items)
            correct_sequence = sorted(items, reverse=(direction == "descending"))
        else:
            items = [f"{n}/{d}" for n in chosen_numerators]
            correct_sequence = sorted(items, key=lambda x: int(x.split('/')[0]), reverse=(direction == "descending"))
    
    elif content_type == "decimal":
        # Decimals - ensure uniqueness
        items = set()
        attempts = 0
        while len(items) < num_items and attempts < 100:
            val = round(rng.uniform(0.1, 9.9), 1)
            items.add(val)
            attempts += 1
        items = list(items)[:num_items]
        correct_sequence = sorted(items, reverse=(direction == "descending"))
    
    elif content_type == "integer":
        # Integers including negatives
        items = rng.sample(range(-20, 20), num_items)
        correct_sequence = sorted(items, reverse=(direction == "descending"))
    
    elif content_type == "whole" or max_value:
        # Whole numbers with specified range
        max_val = max_value or (20 if grade <= 1 else 100 if grade <= 2 else 1000)
        # Generate well-spaced numbers
        min_val = 1
        items = []
        attempts = 0
        while len(items) < num_items and attempts < 100:
            val = rng.randint(min_val, max_val)
            if val not in items:
                items.append(val)
            attempts += 1
        correct_sequence = sorted(items, reverse=(direction == "descending"))
    
    else:
        # Grade-based defaults (no competency text)
        if 3 <= grade <= 4:
            # Default to fractions for grades 3-4
            d = rng.choice([2, 3, 4, 5, 6, 8])
            max_numerators = min(d, num_items + 2)
            available_numerators = list(range(1, max_numerators + 1))
            chosen_numerators = rng.sample(available_numerators, min(num_items, len(available_numerators)))
            if len(chosen_numerators) >= num_items:
                items = [f"{n}/{d}" for n in chosen_numerators]
                correct_sequence = sorted(items, key=lambda x: int(x.split('/')[0]), reverse=(direction == "descending"))
            else:
                items = rng.sample(range(1, 100), num_items)
                correct_sequence = sorted(items, reverse=(direction == "descending"))
        elif grade >= 5:
            # Default to decimals for grade 5+
            items = set()
            attempts = 0
            while len(items) < num_items and attempts < 100:
                val = round(rng.uniform(0.1, 9.9), 1)
                items.add(val)
                attempts += 1
            items = list(items)[:num_items]
            correct_sequence = sorted(items, reverse=(direction == "descending"))
        else:
            # Whole numbers for grades 1-2
            max_val = 20 if grade <= 1 else 100
            items = rng.sample(range(1, max_val), num_items)
            correct_sequence = sorted(items, reverse=(direction == "descending"))
    
    # Shuffle for display
    display_items = items.copy()
    rng.shuffle(display_items)
    
    params = {
        "items": display_items,
        "correct_sequence": correct_sequence,
        "direction": direction,
    }
    
    all_traps = _traps_sort_order(params, rng)
    
    # Generate stem - just the instruction, numbers are shown in the interactive boxes
    if direction == "descending":
        stem = "Arrange the numbers from largest to smallest."
    else:
        stem = "Arrange the numbers from smallest to largest."
    
    return {
        "skeleton_id": encode_skeleton_id("SortOrder", grade, seed, difficulty),
        "visual_type": "SortOrder",
        "visual_params": params,
        "stem_template": stem,
        "correct_answer": correct_sequence,
        "all_traps": all_traps,
        "question_mode": "ordering",
    }


def _traps_sort_order(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for sorting problems."""
    traps = {}
    correct = params["correct_sequence"]
    
    # Completely reversed
    traps["completely_reversed"] = {
        "value": list(reversed(correct)),
        "description": "Sorted in descending instead of ascending order"
    }
    
    # Adjacent swap
    if len(correct) >= 2:
        swapped = correct.copy()
        idx = rng.randint(0, len(correct) - 2)
        swapped[idx], swapped[idx + 1] = swapped[idx + 1], swapped[idx]
        traps["adjacent_swap"] = {
            "value": swapped,
            "description": "Two adjacent items swapped"
        }
    
    # First and last correct, middle wrong
    if len(correct) >= 3:
        middle_wrong = correct.copy()
        # Shuffle middle elements
        middle = middle_wrong[1:-1]
        rng.shuffle(middle)
        middle_wrong[1:-1] = middle
        traps["endpoints_correct_only"] = {
            "value": middle_wrong,
            "description": "First and last correct, middle scrambled"
        }
    
    return traps


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 10: GRID AREA
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_grid_area(grade: int, seed: int, difficulty: int, rng: random.Random, competency_text: Optional[str] = None) -> Dict:
    """
    Click grid squares to shade them. Count fills a shape.
    """
    
    # Normalize difficulty to int level
    diff_level = _difficulty_level(difficulty)
    
    # Grid size and shape complexity
    if grade <= 3:
        # Small rectangle
        width = rng.randint(2, 5)
        height = rng.randint(2, 4)
        shape_type = "rectangle"
        correct_count = width * height
    
    elif grade <= 5:
        # Rectangle or L-shape
        if diff_level >= 3:
            # L-shape
            width1, height1 = rng.randint(3, 6), rng.randint(2, 4)
            width2, height2 = rng.randint(2, 4), rng.randint(2, 4)
            correct_count = width1 * height1 + width2 * height2
            shape_type = "L_shape"
        else:
            width = rng.randint(3, 8)
            height = rng.randint(2, 6)
            correct_count = width * height
            shape_type = "rectangle"
    
    else:
        # More complex shapes
        width = rng.randint(4, 10)
        height = rng.randint(3, 8)
        correct_count = width * height
        shape_type = "rectangle"
    
    params = {
        "grid_size": [10, 10],  # Overall grid
        "shape_type": shape_type,
        "correct_count": correct_count,
        "width": width if shape_type == "rectangle" else None,
        "height": height if shape_type == "rectangle" else None,
    }
    
    all_traps = _traps_grid_area(params, rng)
    
    if shape_type == "rectangle":
        stem = f"Shade all the squares inside the {width}×{height} rectangle. How many square units is the area?"
    else:
        stem = f"Shade all the squares inside the shape. How many square units is the area?"
    
    return {
        "skeleton_id": encode_skeleton_id("GridArea", grade, seed, difficulty),
        "visual_type": "GridArea",
        "visual_params": params,
        "stem_template": stem,
        "correct_answer": correct_count,
        "all_traps": all_traps,
        "question_mode": "grid_area",
    }


def _traps_grid_area(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for grid area problems."""
    traps = {}
    correct = params["correct_count"]
    width = params.get("width")
    height = params.get("height")
    
    # Trap 1: Off by a few squares (always applicable)
    off_by = rng.randint(1, 3)
    traps["off_by_few_under"] = {
        "value": max(1, correct - off_by),
        "description": f"Missed {off_by} squares"
    }
    
    # Trap 2: Off by a few squares over (always applicable)
    traps["off_by_few_over"] = {
        "value": correct + rng.randint(1, 3),
        "description": "Counted a few extra squares"
    }
    
    # For simple rectangles, add more specific traps
    if width and height:
        # Counted perimeter instead
        perimeter = 2 * (width + height)
        if perimeter != correct:
            traps["counted_perimeter"] = {
                "value": perimeter,
                "description": "Counted perimeter instead of area"
            }
        
        # Off by one row
        if height > 1:
            row_trap = width * (height - 1)
            if row_trap != correct:
                traps["missed_one_row"] = {
                    "value": row_trap,
                    "description": "Missed one entire row"
                }
        
        # Off by one column
        if width > 1:
            col_trap = (width - 1) * height
            if col_trap != correct:
                traps["missed_one_column"] = {
                    "value": col_trap,
                    "description": "Missed one entire column"
                }
    
    return traps


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 11: CATEGORIZE
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_categorize(grade: int, seed: int, difficulty: int, rng: random.Random, competency_text: Optional[str] = None) -> Dict:
    """
    Assign each item to a labeled category.
    """
    
    # Normalize difficulty to int level
    diff_level = _difficulty_level(difficulty)
    
    # Number of categories and items
    num_categories = 2 if diff_level == 1 else 3
    num_items = 6 if diff_level == 1 else (8 if diff_level == 2 else 10)
    
    # Grade-based content
    if grade <= 3:
        # Even/odd
        categories = ["Even", "Odd"]
        items = rng.sample(range(1, 30), num_items)
        correct_categories = {item: "Even" if item % 2 == 0 else "Odd" for item in items}
    
    elif grade <= 5:
        # Shapes or number types
        if rng.choice([True, False]):
            categories = ["Triangle", "Quadrilateral", "Other"]
            items = ["Triangle A", "Square", "Rectangle", "Pentagon", "Triangle B", "Hexagon", "Trapezoid", "Circle"][:num_items]
            correct_categories = {
                "Triangle A": "Triangle",
                "Triangle B": "Triangle",
                "Square": "Quadrilateral",
                "Rectangle": "Quadrilateral",
                "Trapezoid": "Quadrilateral",
                "Pentagon": "Other",
                "Hexagon": "Other",
                "Circle": "Other",
            }
        else:
            categories = ["Prime", "Composite"]
            items = rng.sample(range(2, 30), num_items)
            correct_categories = {item: "Prime" if _is_prime(item) else "Composite" for item in items}
    
    else:
        # More complex classification
        categories = ["Linear", "Quadratic", "Neither"]
        items = ["2x + 3", "x² + 1", "5", "x² - 4x", "3x", "2x² + x + 1", "7x - 2", "10"][:num_items]
        # This is complex; simplified for demo
        correct_categories = {item: "Linear" if "x²" not in item and "x" in item else ("Quadratic" if "x²" in item else "Neither") for item in items}
    
    params = {
        "categories": categories,
        "items": items,
        "correct_categories": correct_categories,
    }
    
    all_traps = _traps_categorize(params, rng)
    
    stem = f"Sort each item into the correct category: {', '.join(categories)}"
    
    return {
        "skeleton_id": encode_skeleton_id("Categorize", grade, seed, difficulty),
        "visual_type": "Categorize",
        "visual_params": params,
        "stem_template": stem,
        "correct_answer": correct_categories,
        "all_traps": all_traps,
        "question_mode": "categorize",
    }


def _traps_categorize(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for categorization problems."""
    traps = {}
    correct = params["correct_categories"]
    categories = params["categories"]
    items = list(correct.keys())
    
    # Trap 1: Swap one or two items
    swapped_few = correct.copy()
    items_to_swap = rng.sample(items, min(2, len(items)))
    for item in items_to_swap:
        # Get a different category
        other_cats = [c for c in categories if c != correct[item]]
        if other_cats:
            swapped_few[item] = rng.choice(other_cats)
    
    if swapped_few != correct:
        traps["swapped_few_items"] = {
            "value": swapped_few,
            "description": "A few items placed in wrong categories"
        }
    
    # Trap 2: Swap many items (different from trap 1)
    if len(items) >= 4:
        swapped_many = correct.copy()
        items_to_swap_many = rng.sample(items, min(len(items) // 2 + 1, len(items)))
        for item in items_to_swap_many:
            other_cats = [c for c in categories if c != correct[item]]
            if other_cats:
                swapped_many[item] = rng.choice(other_cats)
        
        if swapped_many != correct and swapped_many != swapped_few:
            traps["swapped_many_items"] = {
                "value": swapped_many,
                "description": "Many items placed in wrong categories"
            }
    
    # Trap 3: All in one category (for 2-category problems)
    if len(categories) == 2:
        all_first = {item: categories[0] for item in items}
        if all_first != correct:
            traps["all_in_one_category"] = {
                "value": all_first,
                "description": f"All items placed in {categories[0]}"
            }
    
    return traps


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 12: CALENDAR
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_calendar(grade: int, seed: int, difficulty: int, rng: random.Random, competency_text: Optional[str] = None) -> Dict:
    """
    Click a specific date or measure duration on a calendar.
    """

    # Normalize difficulty to int level
    diff_level = _difficulty_level(difficulty)
    
    # Pick a year and month
    year = 2024
    month = rng.randint(1, 12)
    
    # Calendar type: date selection or duration
    if rng.choice([True, False]) or diff_level == 1:
        # Date selection
        day = rng.randint(1, calendar_module.monthrange(year, month)[1])
        task_type = "select_date"
        
        date_obj = datetime(year, month, day)
        weekday = date_obj.strftime("%A")
        
        stem = f"Click on {month}/{day}/{year} ({weekday})."
        correct_answer = day
    
    else:
        # Duration calculation
        day1 = rng.randint(1, calendar_module.monthrange(year, month)[1] - 5)
        day2 = day1 + rng.randint(3, 10)
        if day2 > calendar_module.monthrange(year, month)[1]:
            day2 = calendar_module.monthrange(year, month)[1]
        
        task_type = "measure_duration"
        duration = day2 - day1 + 1  # Inclusive
        
        stem = f"How many days are there from {month}/{day1} to {month}/{day2}, inclusive?"
        correct_answer = duration
    
    params = {
        "year": year,
        "month": month,
        "task_type": task_type,
        "correct_date": day if task_type == "select_date" else None,
        "correct_duration": duration if task_type == "measure_duration" else None,
    }
    
    all_traps = _traps_calendar(params, rng)
    
    return {
        "skeleton_id": encode_skeleton_id("Calendar", grade, seed, difficulty),
        "visual_type": "Calendar",
        "visual_params": params,
        "stem_template": stem,
        "correct_answer": correct_answer,
        "all_traps": all_traps,
        "question_mode": "calendar",
    }


def _traps_calendar(params: Dict, rng: random.Random) -> Dict:
    """Generate traps for calendar problems."""
    traps = {}
    task_type = params["task_type"]
    
    if task_type == "select_date":
        correct_date = params["correct_date"]
        
        # Off by one day
        if correct_date > 1:
            traps["one_day_before"] = {
                "value": correct_date - 1,
                "description": "Selected one day before"
            }
        
        max_day = calendar_module.monthrange(params["year"], params["month"])[1]
        if correct_date < max_day:
            traps["one_day_after"] = {
                "value": correct_date + 1,
                "description": "Selected one day after"
            }
        
        # Off by one week
        if correct_date > 7:
            traps["one_week_before"] = {
                "value": correct_date - 7,
                "description": "Selected one week before"
            }
        if correct_date <= max_day - 7:
            traps["one_week_after"] = {
                "value": correct_date + 7,
                "description": "Selected one week after"
            }
    
    else:  # measure_duration
        correct_duration = params["correct_duration"]
        
        # Inclusive vs exclusive confusion
        traps["exclusive_count"] = {
            "value": correct_duration - 1,
            "description": "Counted exclusively instead of inclusively"
        }
        
        # Off by one
        traps["off_by_one"] = {
            "value": correct_duration + 1,
            "description": "Counting error"
        }
    
    return traps


# ═══════════════════════════════════════════════════════════════════════════════
# TRAP METADATA
# ═══════════════════════════════════════════════════════════════════════════════

TRAP_METADATA = {
    # Fill-in-Table traps
    "off_by_one_up": {
        "description": "Added 1 to the correct answer",
        "remediation": "Double-check your calculation. Count carefully.",
        "misconception_category": "calculation_error",
    },
    "off_by_one_down": {
        "description": "Subtracted 1 from the correct answer",
        "remediation": "Double-check your calculation. Count carefully.",
        "misconception_category": "calculation_error",
    },
    "added_instead": {
        "description": "Added when should have multiplied",
        "remediation": "Multiplication means repeated addition. 3 × 4 means three groups of 4.",
        "misconception_category": "operation_confusion",
    },
    "forgot_constant_term": {
        "description": "Forgot to add the constant term",
        "remediation": "Linear rules have two parts: multiply then add. Don't forget the second step.",
        "misconception_category": "incomplete_rule",
    },
    
    # Number Line traps
    "numerator_only": {
        "description": "Used only the numerator, ignored the denominator",
        "remediation": "A fraction shows parts of a whole. 3/4 means 3 out of 4 equal parts.",
        "misconception_category": "fraction_representation",
    },
    "denominator_only": {
        "description": "Used only the denominator, ignored the numerator",
        "remediation": "The numerator tells you how many parts to count.",
        "misconception_category": "fraction_representation",
    },
    "larger_denom_larger_value": {
        "description": "Thinks larger denominator means larger fraction",
        "remediation": "More pieces means each piece is smaller. 1/8 of a pizza is smaller than 1/4.",
        "misconception_category": "fraction_magnitude",
    },
    "inverted_fraction": {
        "description": "Flipped the numerator and denominator",
        "remediation": "In a/b, 'a' is the numerator (top) and 'b' is the denominator (bottom).",
        "misconception_category": "fraction_representation",
    },
    "ignore_negative": {
        "description": "Ignored the negative sign",
        "remediation": "Negative numbers are to the LEFT of zero on the number line.",
        "misconception_category": "integer_representation",
    },
    "negative_magnitude_confusion": {
        "description": "Compared absolute values instead of considering negative direction",
        "remediation": "-5 is LESS than -3 because it's farther left from zero.",
        "misconception_category": "integer_ordering",
    },
    
    # Constraint Satisfaction traps
    "boundary_violation": {
        "description": "Used boundary value instead of value beyond it",
        "remediation": "'Greater than 5' means 6, 7, 8... not 5 itself.",
        "misconception_category": "inequality_interpretation",
    },
    "wrong_parity": {
        "description": "Used even number when odd required, or vice versa",
        "remediation": "Even numbers end in 0, 2, 4, 6, 8. Odd numbers end in 1, 3, 5, 7, 9.",
        "misconception_category": "number_properties",
    },
}
