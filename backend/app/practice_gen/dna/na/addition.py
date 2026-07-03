"""
DNA: Addition (Number & Algebra)

Refactored from:
  - matatag_skeletons.py  (arithmetic generator + ar_* traps)
  - matatag_dimensions.py (ARITHMETIC_DIMENSIONS)

Covers MATATAG grades 1–3 addition competencies.
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
# g1: sums up to 20 (easy half), then sums up to 100 no regroup (harder half)
# g2: operands up to 1000, regrouping expected
# g3: operands up to 10000
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"a": (1, 50),  "b": (1, 50),  "max_result": 100},
    "g2": {"a": (1, 500), "b": (1, 500), "max_result": 1000},
    "g3": {"a": (1, 5000), "b": (1, 5000), "max_result": 10000},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="a - b",
        required_concept="subtraction",
        label="ar_wrong_op",
        description="Used subtraction instead of addition.",
    ),
    ErrorPattern(
        formula="(a % 10 + b % 10) + (a // 10 + b // 10) * 10",
        required_concept="addition",
        label="ar_no_regroup",
        description="Added ones and tens separately without carrying.",
    ),
    ErrorPattern(
        formula="a + b + 10",
        required_concept="addition",
        label="ar_double_regroup",
        description="Carried twice, adding an extra 10 to the result.",
    ),
    ErrorPattern(
        formula="a + b - 1",
        required_concept="addition",
        label="ar_off_one_low",
        description="Off-by-one: result is one too low.",
    ),
    ErrorPattern(
        formula="a + b + 1",
        required_concept="addition",
        label="ar_off_one_high",
        description="Off-by-one: result is one too high.",
    ),
    ErrorPattern(
        formula="a + b - b",
        required_concept="addition",
        label="ar_zero_prop",
        description="Misapplied zero property; result equals one operand.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
# NOTE: "structure" is a contextual variant, not a difficulty dimension.
# max_sum is now continuous: accepts numeric value directly (e.g., 20) not level string
_DIFFICULTY_AXES: Dict[str, Any] = {    "max_sum": "continuous",  # Accepts numeric value (2-1000)
    "regrouping": ["none", "ones", "tens", "double"],
    "number_difficulty": "continuous",  # Continuous axis based on divisibility, digits, and magnitude
}

# Map max_sum level to actual numeric bounds
_MAX_SUM_BOUNDS: Dict[str, int] = {
    "up_to_10": 10,
    "up_to_20": 20,
    "up_to_50": 50,
    "up_to_100": 100,
    "up_to_1000": 1000,
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_SUM       = VocabGated(requires_vocab="sum",     preferred="the sum",     fallback="the answer")
VOCAB_ADDEND    = VocabGated(requires_vocab="addend",  preferred="addend",      fallback="number")
VOCAB_REGROUP   = VocabGated(requires_vocab="regroup", preferred="regroup",     fallback="carry over")


# ─── constraint predicates ────────────────────────────────────────────────────

def _satisfies_regrouping(a: int, b: int, level: str) -> bool:
    """Check if a pair satisfies regrouping difficulty based on COUNT of places.

    Counts carries across all digit places (ones, tens, hundreds, thousands, etc).

    Difficulty levels:
    - "none": 0 places require regrouping
    - "one_place": exactly 1 place requires regrouping
    - "two_places": exactly 2 places require regrouping
    - "three_places": exactly 3 places require regrouping
    - "four_places": 4+ places require regrouping
    """
    carry_count = 0
    carry = 0

    # Process each digit place from ones to ten-thousands
    for place_value in [1, 10, 100, 1000]:
        digit_a = (a // place_value) % 10
        digit_b = (b // place_value) % 10
        digit_sum = digit_a + digit_b + carry

        if digit_sum >= 10:
            carry_count += 1
            carry = 1
        else:
            carry = 0

    if level == "none":
        return carry_count == 0
    if level == "one_place":
        return carry_count == 1
    if level == "two_places":
        return carry_count == 2
    if level == "three_places":
        return carry_count == 3
    if level == "four_places":
        return carry_count >= 4
    # Legacy support for old naming
    if level == "ones":
        ones_needs = ((a % 10) + (b % 10)) >= 10
        tens_needs = ((a // 10 % 10) + (b // 10 % 10)) >= 10
        return carry_count == 1 and ones_needs
    if level == "tens":
        ones_needs = ((a % 10) + (b % 10)) >= 10
        tens_needs = ((a // 10 % 10) + (b // 10 % 10)) >= 10
        return carry_count == 1 and tens_needs
    if level == "double":
        return carry_count == 2
    return True


# Number of carry places each regrouping level *requires*. Used to decide
# whether a level is feasible for a given number range (see
# max_regrouping_places) so we never ask the generator to search for a pair
# that cannot exist.
REGROUP_LEVEL_PLACES = {
    "none": 0,
    "one_place": 1,
    "two_places": 2,
    "three_places": 3,
    "four_places": 4,
    # legacy names
    "ones": 1,
    "tens": 1,
    "double": 2,
}


def max_regrouping_places(max_result: int) -> int:
    """Largest carry count physically achievable for any (a, b) with a + b <= max_result.

    Adding two operands whose sum is bounded by an N-digit `max_result` can carry
    at most N-1 times: each carry propagates one place left, and the final carry
    is what creates the top (Nth) digit. Verified exhaustively against
    `_satisfies_regrouping`:
        max_result   20 (2 digits) -> 1
        max_result  100 (3 digits) -> 2
        max_result  999 (3 digits) -> 2
        max_result 1000 (4 digits) -> 3

    This is the single source of truth for regrouping feasibility; the lab-config
    builder, orchestrator pre-filter, auditor mirror, and the DNA guard all defer
    to it so an infeasible (range, regrouping) combination is never generated.
    """
    if max_result < 10:
        return 0
    return len(str(int(max_result))) - 1


def regrouping_is_feasible(level: str, max_result: int) -> bool:
    """True if `level` can be satisfied by some (a, b) with a + b <= max_result."""
    return REGROUP_LEVEL_PLACES.get(level, 0) <= max_regrouping_places(max_result)


# ─── parameter generator ──────────────────────────────────────────────────────

# Word problem templates for context="word_problem"
# These are narrative variations (spines) for result_unknown problems.
# They align with competency language: "counting up" and "putting together"
#
# Template placeholders:



def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate (a, b) that satisfy the difficulty_profile constraints.

    Uses smart candidate generation instead of random rejection sampling:
    1. Build candidate pool based on number_type constraint
    2. Filter pairs by regrouping constraint
    3. Filter pairs by max_sum constraint
    4. Randomly select from valid pairs

    Supports difficulty dimensions:
    - max_sum: numeric value (e.g., 20) - continuous dimension
    - regrouping: "none", "ones", "tens", "double" - discrete
    - number_type: "non_round", "round" - discrete

    Supports contextual variants:
    - context: "pure" (default) or "word_problem"
    - structure: "result_unknown", "change_unknown", "start_unknown"

    Returns {"a": int, "b": int, "result": int, "blank_target": str, 
             "context": str, "structure": str, "max_sum": int, "question": str (for word problems)}.
    Raises RuntimeError if no valid pair exists for the given constraints.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]
    max_result_bound = bounds["max_result"]
    
    # Retrieve explicitly set maximum bound from profile, fallback to curriculum absolute maximum
    max_sum_value = profile.get("max_sum")
    if max_sum_value is not None:
        if isinstance(max_sum_value, (int, float)):
            max_result = int(max_sum_value)
        elif isinstance(max_sum_value, str):
            legacy_map = {"up_to_10": 10, "up_to_20": 20, "up_to_50": 50, "up_to_100": 100, "up_to_1000": 1000}
            max_result = legacy_map.get(max_sum_value, max_result_bound)
    else:
        max_result = max_result_bound
    
    # Ensure reasonable bounds (allow min=0 for 0+0, but cap at 10000)
    max_result = min(max_result, 10000)
    if "formatter_max_val" in profile:
        max_result = min(max_result, profile["formatter_max_val"])

    # Difficulty axes
    reg_level  = profile.get("regrouping", "none")
    # Note: Regrouping constraint is now based on COUNT of places,
    # not which place. No min_result enforcement needed; the constraint
    # itself ensures sufficient variety (one_place and two_places require
    # multi-digit operands naturally).
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    # Contextual variants
    context = profile.get("context", "pure")
    
    # Since this DNA specifically maps to the basic addition competency
    # (result unknown), we only use the default structure.
    structure = profile.get("structure", "result_unknown")
    spine = profile.get("spine", None)

    # Build candidate operand pool with grade-appropriate floor
    min_a = 0
    if grade >= 3 and max_result >= 100:
        min_a = 10
    if grade >= 4 and max_result >= 1000:
        min_a = 100
        
    # Fail fast on infeasible (range, regrouping) combinations instead of
    # discovering it by exhausting the rejection loop below. A sum bounded by
    # `max_result` can carry at most `max_regrouping_places(max_result)` times,
    # so a level demanding more places has no valid pair — raise immediately.
    # (The orchestrator/auditor pre-filter should keep such profiles from ever
    # reaching here; this guard is defense in depth.)
    if not regrouping_is_feasible(reg_level, max_result):
        raise RuntimeError(
            f"generate_params (addition): regrouping level '{reg_level}' requires "
            f"{REGROUP_LEVEL_PLACES.get(reg_level, 0)} carry places but max_result="
            f"{max_result} allows at most {max_regrouping_places(max_result)}. "
            f"Infeasible combination (grade={grade}, profile={difficulty_profile})."
        )

    a_hi = max(1, max_result - 1)
    candidates_a = list(range(min_a, a_hi + 1))
    candidates_b = candidates_a.copy()

    # Build all valid pairs satisfying sum and regrouping
    candidate_pairs = []
    if max_result <= 100:
        for a in candidates_a:
            for b in candidates_b:
                if a + b > max_result:
                    continue
                if _satisfies_regrouping(a, b, reg_level):
                    candidate_pairs.append((a, b))
    else:
        # Feasible level (guard above): a satisfiable constraint fills the pool
        # in far fewer than 2000 draws, so a low cap suffices. If the pool is
        # still empty after the cap, treat it as infeasible and raise rather
        # than silently returning a degraded pair.
        attempts = 0
        while len(candidate_pairs) < 2000 and attempts < 5000:
            attempts += 1
            a = rng.randint(min_a, a_hi)
            b = rng.randint(0, max_result - a)
            if _satisfies_regrouping(a, b, reg_level):
                candidate_pairs.append((a, b))

    if not candidate_pairs:
        raise RuntimeError(
            f"generate_params (addition): no valid pair exists for grade={grade}, "
            f"profile={difficulty_profile}. Constraints are incompatible."
        )

    # Sample a pair from the candidate pool using the continuous difficulty window
    from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
    a, b = generate_pair_by_window(candidate_pairs, num_diff_scalar, d=5, rng=rng)

    # Determine blank_target from structure
    blank_target = {
        "result_unknown": "result",
        "change_unknown": "b",
        "start_unknown":  "a",
    }.get(structure, "result")

    strategy = profile.get("strategy", "standard")

    result_dict = {
        "a": a,
        "b": b,
        "result": a + b,
        "blank_target": blank_target,
        "context": context,
        "structure": structure,
        "max_sum": max_result,  # Numeric value
        "strategy": strategy,
    }

    return result_dict


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hint strings for the given addition problem."""
    a = values["a"]
    b = values["b"]
    result = values["result"]

    sum_label  = VOCAB_SUM.resolve(cumulative_vocab)
    add_label  = VOCAB_ADDEND.resolve(cumulative_vocab)
    reg_phrase = VOCAB_REGROUP.resolve(cumulative_vocab)

    hints: List[str] = []

    # Step 1: identify the operation
    hints.append(f"We are adding two numbers: {a} and {b}.")

    # Step 2: ones column
    ones_a, ones_b = a % 10, b % 10
    ones_sum = ones_a + ones_b
    if ones_sum >= 10:
        hints.append(
            f"Add the ones: {ones_a} + {ones_b} = {ones_sum}. "
            f"Write {ones_sum % 10} in the ones place and {reg_phrase} 1 ten."
        )
    else:
        hints.append(f"Add the ones: {ones_a} + {ones_b} = {ones_sum}. Write {ones_sum} in the ones place.")

    # Step 3: tens column (only shown when both numbers have tens)
    if a >= 10 or b >= 10:
        carry    = 1 if ones_sum >= 10 else 0
        tens_a   = a // 10 % 10
        tens_b   = b // 10 % 10
        tens_sum = tens_a + tens_b + carry
        hints.append(
            f"Add the tens: {tens_a} + {tens_b}"
            + (f" + {carry} (carried)" if carry else "")
            + f" = {tens_sum}."
        )

    # Step 4: final answer
    hints.append(f"{sum_label.capitalize()} is {a} + {b} = {result}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

ADDITION_DNA = DNA(
    concept="addition",
    dna_type="formula",
    answer_formula="a + b",
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
        "emoji_pictorial",
    ],
    requires_context=True,
    visual_home="NumberLine",
    difficulty_axes=_DIFFICULTY_AXES,
)
