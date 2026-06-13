"""
DNA: Subtraction (Number & Algebra)

Refactored from:
  - matatag_skeletons.py  (arithmetic generator + ar_* traps)
  - matatag_dimensions.py (ARITHMETIC_DIMENSIONS)

Covers MATATAG grades 1–3 subtraction competencies.

Structure variants align with competency:
"Illustrate subtraction... and describe subtraction as 'taking away' 
 and 'counting back' and 'comparing'."
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DIFFICULTY_LEVEL_MAP,
    DNA,
    DimensionSpec,
    ErrorPattern,
    VocabGated,
)


# ─── param bounds ─────────────────────────────────────────────────────────────
# g1: a,b both < 20 (easy half), then < 100 no regroup
# g2: < 1000 with regrouping
# g3: < 10000
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"a": (1, 99),   "b": (1, 99),   "min_a_minus_b": 0},
    "g2": {"a": (1, 999),  "b": (1, 999),  "min_a_minus_b": 0},
    "g3": {"a": (1, 9999), "b": (1, 9999), "min_a_minus_b": 0},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="a + b",
        required_concept="addition",
        label="ar_wrong_op",
        description="Used addition instead of subtraction.",
    ),
    ErrorPattern(
        formula="b - a",
        required_concept="subtraction",
        label="ar_reverse_sub",
        description="Subtracted the larger from the smaller (b − a).",
    ),
    ErrorPattern(
        formula="(a % 10 - b % 10) + (a // 10 - b // 10) * 10",
        required_concept="subtraction",
        label="ar_no_regroup",
        description="Subtracted each column independently without borrowing.",
    ),
    ErrorPattern(
        formula="a - b - 1",
        required_concept="subtraction",
        label="ar_off_one_low",
        description="Off-by-one: result is one too low.",
    ),
    ErrorPattern(
        formula="a - b + 1",
        required_concept="subtraction",
        label="ar_off_one_high",
        description="Off-by-one: result is one too high.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, List[str]] = {
    "regrouping": ["none", "ones", "tens", "double"],
    "number_type": ["round", "non_round"],
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_DIFFERENCE   = VocabGated(requires_vocab="difference",  preferred="the difference",  fallback="the answer")
VOCAB_MINUEND      = VocabGated(requires_vocab="minuend",     preferred="the minuend",     fallback="the starting number")
VOCAB_SUBTRAHEND   = VocabGated(requires_vocab="subtrahend",  preferred="the subtrahend",  fallback="the number being subtracted")
VOCAB_REGROUP      = VocabGated(requires_vocab="regroup",     preferred="regroup",         fallback="borrow")





# ─── constraint predicates ────────────────────────────────────────────────────

def _satisfies_regrouping(a: int, b: int, level: str) -> bool:
    """
    For subtraction, regrouping (borrowing) occurs when a digit in b > corresponding digit in a.
    We check the ones and tens columns.
    """
    ones_needs_borrow = (a % 10) < (b % 10)
    # After potential ones borrow, adjusted tens digit of a
    a_tens = (a // 10 % 10) - (1 if ones_needs_borrow else 0)
    tens_needs_borrow = a_tens < (b // 10 % 10)

    if level == "none":
        return not ones_needs_borrow and not tens_needs_borrow
    if level == "ones":
        return ones_needs_borrow and not tens_needs_borrow
    if level == "tens":
        return not ones_needs_borrow and tens_needs_borrow
    if level == "double":
        return ones_needs_borrow and tens_needs_borrow
    return True


def _satisfies_number_type(a: int, b: int, level: str) -> bool:
    if level == "round":
        return a % 10 == 0 and b % 10 == 0
    if level == "non_round":
        return not (a % 10 == 0 and b % 10 == 0)
    return True


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate (a, b) with a >= b that satisfy the difficulty_profile constraints.

    Uses smart candidate generation:
    1. Build candidate pool based on max_difference and number_type
    2. Filter pairs by regrouping constraint
    3. Randomly select from valid pairs

    Supports difficulty dimensions:
    - max_difference: numeric value (e.g., 20) - continuous dimension
    - regrouping: "none", "ones", "tens", "double" - discrete
    - number_type: "non_round", "round" - discrete

    Supports contextual variants:
    - context: "pure" (default) or "word_problem"
    - structure: "result_unknown", "change_unknown", "start_unknown"

    Note: "taking_away", "counting_back", "comparing" are NOT structures -
    they are narrative spines randomly chosen for word problems.

    Returns {"a": int, "b": int, "result": int, "blank_target": str,
             "context": str, "structure": str, "question": str (for word problems)}.
    Raises RuntimeError if no valid pair found.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    # Get max_difference from profile (parallel to addition's max_sum)
    max_diff_value = profile.get("max_difference") or profile.get("max_sum")
    if max_diff_value is None:
        # Default based on grade
        if grade == 1:
            max_minuend = 20
        elif grade == 2:
            max_minuend = 100
        else:
            max_minuend = 1000
    elif isinstance(max_diff_value, (int, float)):
        max_minuend = int(max_diff_value)
    elif isinstance(max_diff_value, str):
        legacy_map = {"up_to_10": 10, "up_to_20": 20, "up_to_50": 50, "up_to_100": 100, "up_to_1000": 1000}
        max_minuend = legacy_map.get(max_diff_value, 20)
    else:
        max_minuend = 20

    # Ensure reasonable bounds
    max_minuend = max(2, min(max_minuend, 10000))

    reg_level = profile.get("regrouping", "none")
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    # Contextual variants
    context = profile.get("context", "pure")
    spine = profile.get("spine", None)
    
    # Structure determines which value is unknown (algebraic position):
    # - "result_unknown": a - b = ? (default)
    # - "change_unknown": a - ? = result (for missing number competencies)
    # - "start_unknown": ? - b = result (for missing number competencies)
    structure = profile.get("structure", "result_unknown")

    # Build candidate pool
    candidates_a = list(range(1, max_minuend + 1))

    # Build valid pairs with rejection sampling
    candidate_pairs = []
    if max_minuend <= 100:
        for a in candidates_a:
            for b in range(0, a + 1):
                if _satisfies_regrouping(a, b, reg_level):
                    candidate_pairs.append((a, b))
    else:
        attempts = 0
        while len(candidate_pairs) < 2000 and attempts < 50000:
            attempts += 1
            a = rng.randint(1, max_minuend)
            b = rng.randint(0, a)
            if _satisfies_regrouping(a, b, reg_level):
                candidate_pairs.append((a, b))

    if not candidate_pairs:
        # Fallback: simple pair
        a = rng.randint(2, max_minuend)
        b = rng.randint(0, a)
        candidate_pairs = [(a, b)]

    # Sample a pair from the candidate pool using the continuous difficulty window
    from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
    a, b = generate_pair_by_window(candidate_pairs, num_diff_scalar, d=5, rng=rng)

    # Determine blank_target based on structure
    blank_target = {
        "result_unknown": "result",
        "change_unknown": "b",
        "start_unknown": "a",
    }.get(structure, "result")

    result_dict = {
        "a": a,
        "b": b,
        "result": a - b,
        "blank_target": blank_target,
        "context": context,
        "structure": structure,
        "max_difference": max_minuend,
    }

    # Generate question text based on context and structure
    if context == "word_problem":
        from backend.app.practice_gen.spines import select_spine, format_spine
        
        narrative_logic = spine if spine and spine != "random" else None
        interest_id = profile.get("interest_id")
        
        selected_spine = select_spine(
            grade=grade,
            concept="subtraction",
            rng=rng,
            blank_target=blank_target,
            narrative_logic=narrative_logic
        )

        if selected_spine:
            math_vars = {"a": a, "b": b, "result": a - b}
            question = format_spine(
                spine=selected_spine,
                math_vars=math_vars,
                rng=rng,
                grade=grade,
                interest_id=interest_id
            )
            result_dict["question"] = question

    return result_dict


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hint strings for the given subtraction problem."""
    a = values["a"]
    b = values["b"]
    result = values["result"]

    diff_label  = VOCAB_DIFFERENCE.resolve(cumulative_vocab)
    reg_phrase  = VOCAB_REGROUP.resolve(cumulative_vocab)

    hints: List[str] = []

    # Step 1: identify the operation
    hints.append(f"We are subtracting {b} from {a}.")

    # Step 2: ones column
    ones_a, ones_b = a % 10, b % 10
    if ones_a < ones_b:
        hints.append(
            f"The ones digit {ones_a} is less than {ones_b}, so we need to {reg_phrase}. "
            f"Borrow 1 ten: {ones_a + 10} − {ones_b} = {ones_a + 10 - ones_b}."
        )
    else:
        hints.append(f"Subtract the ones: {ones_a} − {ones_b} = {ones_a - ones_b}.")

    # Step 3: tens column (only when numbers have tens)
    if a >= 10 or b >= 10:
        borrow   = 1 if ones_a < ones_b else 0
        tens_a   = a // 10 % 10 - borrow
        tens_b   = b // 10 % 10
        hints.append(
            f"Subtract the tens: {tens_a} − {tens_b} = {tens_a - tens_b}."
            + (" (after borrowing)" if borrow else "")
        )

    # Step 4: final answer
    hints.append(f"{diff_label.capitalize()} of {a} − {b} = {result}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

SUBTRACTION_DNA = DNA(
    concept="subtraction",
    dna_type="formula",
    answer_formula="a - b",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "ordering",
        "true_false",
        "error_detect",
        "number_line_read",
        "number_line_set",
        "number_bond",
    ],
    requires_context=True,
    visual_home="NumberLine",
    difficulty_axes=_DIFFICULTY_AXES,
)
