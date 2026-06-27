"""
DNA: Multiplication (Number & Algebra)

Refactored from:
  - matatag_skeletons.py  (arithmetic generator + ar_* traps)
  - matatag_dimensions.py (ARITHMETIC_DIMENSIONS)

Covers MATATAG grades 2–3 multiplication competencies.
  g2: tables 2, 3, 4, 5, 10 only
  g3: tables 2–9, then 2–3 digit by 1-digit
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
# b = the table being drilled; a = the multiplier drawn from that table
# For g3 multi_digit: a can be 2–3 digit, b is 1-digit
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g2": {
        "tables":    [2, 3, 4, 5, 10],
        "a":         (1, 10),           # multiplier
        "b_single":  (1, 10),           # factor (from allowed tables)
    },
    "g3": {
        "tables":    [2, 3, 4, 5, 6, 7, 8, 9, 10],
        "a":         (1, 99),           # up to 2-digit for multi_digit
        "b_single":  (1, 9),
    },
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="a + b",
        required_concept="addition",
        label="ar_mul_add",
        description="Added instead of multiplied.",
    ),
    ErrorPattern(
        formula="a - b",
        required_concept="subtraction",
        label="ar_wrong_op",
        description="Subtracted instead of multiplied.",
    ),
    ErrorPattern(
        formula="a * b - b",
        required_concept="multiplication",
        label="ar_zero_prop",
        description="Dropped one group; result is one factor short.",
    ),
    ErrorPattern(
        formula="a * b - 1",
        required_concept="multiplication",
        label="ar_off_one_low",
        description="Off-by-one: product is one too low.",
    ),
    ErrorPattern(
        formula="a * b + b",
        required_concept="multiplication",
        label="ar_off_one_high",
        description="Off-by-one group: counted one extra group.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {"number_difficulty": "continuous"}

# Tables allowed per axis level
_TABLE_SETS: Dict[str, List[int]] = {
    "2_3_4_5_10": [2, 3, 4, 5, 10],
    "6_7_8_9":    [6, 7, 8, 9],
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_PRODUCT  = VocabGated(requires_vocab="product",  preferred="the product",  fallback="the answer")
VOCAB_FACTOR   = VocabGated(requires_vocab="factor",   preferred="factor",       fallback="number")
VOCAB_MULTIPLY = VocabGated(requires_vocab="multiply", preferred="multiply",     fallback="find the total of equal groups")
VOCAB_TIMES    = VocabGated(requires_vocab="times",    preferred="times",        fallback="groups of")


# ─── constraint predicates ────────────────────────────────────────────────────

def _table_for_level(level: str, grade: int) -> List[int]:
    """Return the allowed factor-b values for the given table axis level."""
    if grade <= 2:
        # Grade 2 always restricts to basic tables regardless of level
        return [2, 3, 4, 5, 10]
    return _TABLE_SETS.get(level, [2, 3, 4, 5, 10])


def _satisfies_number_type(a: int, level: str) -> bool:
    if level == "single_digit":
        return 1 <= a <= 9
    if level == "multi_digit":
        return a >= 10
    return True


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Rejection-sample (a, b) that satisfy the difficulty_profile constraints.

    Returns {"a": int, "b": int, "result": int, "blank_target": str}.
    b is always the table factor (1-digit); a is the multiplier.
    Raises RuntimeError if no valid pair found in 100 attempts.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key = f"g{max(2, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]

    table_level = profile.get("table", "2_3_4_5_10")
    num_level   = profile.get("number_type", "single_digit")
    structure   = profile.get("structure", "result_unknown")
    context     = profile.get("context", "pure")
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    allowed_tables = _table_for_level(table_level, grade)
    a_lo = bounds["a"][0]
    if num_level == "multi_digit":
        a_lo = max(10, a_lo)
    a_hi = max(a_lo, bounds["a"][1])

    max_prod_val = profile.get("max_product")
    if max_prod_val is not None:
        min_possible = (10 if num_level == "multi_digit" else 1) * min(allowed_tables)
        max_prod_val = max(int(max_prod_val), min_possible)
    else:
        max_prod_val = 999999 # Rely on bounds["a"]

    candidate_pairs = []
    for b in allowed_tables:
        for a in range(a_lo, a_hi + 1):
            if a * b > max_prod_val:
                continue
            if _satisfies_number_type(a, num_level):
                candidate_pairs.append((a, b))

    if not candidate_pairs:
        raise RuntimeError(
            f"generate_params (multiplication): no valid pair found for grade={grade}, "
            f"profile={difficulty_profile}."
        )

    from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
    a, b = generate_pair_by_window(candidate_pairs, num_diff_scalar, d=5, rng=rng)

    blank_target = {
        "result_unknown": "result",
        "factor_unknown": "b",
    }.get(structure, "result")

    result_dict = {
        "a": a,
        "b": b,
        "result": a * b,
        "blank_target": blank_target,
        "context": context,
        "structure": structure,
    }

    return result_dict


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hint strings for the given multiplication problem."""
    a = values["a"]
    b = values["b"]
    result = values["result"]

    product_label  = VOCAB_PRODUCT.resolve(cumulative_vocab)
    times_phrase   = VOCAB_TIMES.resolve(cumulative_vocab)
    mul_phrase     = VOCAB_MULTIPLY.resolve(cumulative_vocab)

    hints: List[str] = []

    # Step 1: restate as repeated addition / groups
    hints.append(f"We need to {mul_phrase} {a} {times_phrase} {b}.")

    # Step 2: repeated addition breakdown (only practical for small b)
    if b <= 5:
        groups = " + ".join(str(a) for _ in range(b))
        hints.append(f"Think of it as {b} groups of {a}: {groups}.")
    else:
        hints.append(f"Use the {b} times table: {b} × {a}.")

    # Step 3: partial products for multi-digit a
    if a >= 10:
        tens_a = (a // 10) * 10
        ones_a = a % 10
        hints.append(
            f"Break {a} into {tens_a} + {ones_a}: "
            f"({tens_a} × {b}) + ({ones_a} × {b}) = {tens_a * b} + {ones_a * b} = {result}."
        )

    # Step 4: final answer
    hints.append(f"{product_label.capitalize()} of {a} × {b} = {result}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

MULTIPLICATION_DNA = DNA(
    concept="multiplication",
    dna_type="formula",
    answer_formula="a * b",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "ordering",
        "true_false",
        "error_detect",
        "array_grid_read",
        "array_grid_set",
    ],
    requires_context=True,
    visual_home="ArrayGrid",
    difficulty_axes=_DIFFICULTY_AXES,
)
