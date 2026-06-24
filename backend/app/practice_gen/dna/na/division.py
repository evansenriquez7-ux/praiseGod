"""
DNA: Division (Number & Algebra)

Refactored from:
  - matatag_skeletons.py  (arithmetic generator + ar_* traps)
  - matatag_dimensions.py (ARITHMETIC_DIMENSIONS)

Covers MATATAG grades 2–3 division competencies.
  g2: tables 2, 3, 4, 5, 10 (integer division only)
  g3: tables 2–9, 2–3 digit dividend by 1-digit divisor (with/without remainder)

answer_formula: "a // b"  (integer quotient)
For remainder variant, the remainder is available as "a % b".
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
# a = dividend, b = divisor (always 1-digit, from allowed tables)
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g2": {
        "tables":  [2, 3, 4, 5, 10],
        "b":       (2, 10),           # divisor drawn from allowed tables
        "q_max":   10,                # max quotient (keeps product in table range)
    },
    "g3": {
        "tables":  [2, 3, 4, 5, 6, 7, 8, 9, 10],
        "b":       (2, 9),
        "q_max":   99,                # allows 2–3 digit dividends
    },
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="a - b",
        required_concept="subtraction",
        label="ar_div_sub",
        description="Subtracted instead of divided.",
    ),
    ErrorPattern(
        formula="a // b",
        required_concept="division",
        label="ar_rem_drop",
        description="Gave the quotient but forgot to include the remainder.",
    ),
    ErrorPattern(
        formula="a % b + b",
        required_concept="division",
        label="ar_rem_swap",
        description="Reported remainder plus divisor instead of the quotient.",
    ),
    ErrorPattern(
        formula="a * b",
        required_concept="multiplication",
        label="ar_wrong_op",
        description="Multiplied instead of divided.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {    "number_difficulty": "continuous",
}

_TABLE_SETS: Dict[str, List[int]] = {
    "2_3_4_5_10": [2, 3, 4, 5, 10],
    "6_7_8_9":    [6, 7, 8, 9],
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_QUOTIENT   = VocabGated(requires_vocab="quotient",   preferred="the quotient",   fallback="the answer")
VOCAB_DIVISOR    = VocabGated(requires_vocab="divisor",    preferred="the divisor",    fallback="the number we divide by")
VOCAB_DIVIDEND   = VocabGated(requires_vocab="dividend",   preferred="the dividend",   fallback="the number being divided")
VOCAB_REMAINDER  = VocabGated(requires_vocab="remainder",  preferred="the remainder",  fallback="what is left over")


# ─── constraint predicates ────────────────────────────────────────────────────

def _table_for_level(level: str, grade: int) -> List[int]:
    if grade <= 2:
        return [2, 3, 4, 5, 10]
    return _TABLE_SETS.get(level, [2, 3, 4, 5, 10])


def _satisfies_remainder(a: int, b: int, level: str) -> bool:
    has_remainder = (a % b) != 0
    if level == "none":
        return not has_remainder
    if level == "with_remainder":
        return has_remainder
    return True


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Rejection-sample (a, b) that satisfy the difficulty_profile constraints.

    For remainder=="none":  a is constructed as b * q (exact division).
    For remainder=="with_remainder": a = b * q + r, r in [1, b-1].

    Returns {
        "a": int,           # dividend
        "b": int,           # divisor
        "result": int,      # quotient  (a // b)
        "remainder": int,   # a % b
        "blank_target": str,
    }.
    Raises RuntimeError if no valid pair found in 100 attempts.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key        = f"g{max(2, min(grade, 3))}"
    bounds       = _PARAM_BOUNDS[g_key]
    
    q_max_override = profile.get("max_quotient")
    diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
    if q_max_override is None:
        from backend.app.practice_gen.dna.base import log_interpolate
        q_max = int(log_interpolate(2, bounds["q_max"], diff_scalar))
    else:
        q_max = int(q_max_override)

    rem_level    = profile.get("remainder", "none")
    table_level  = profile.get("table", "2_3_4_5_10")
    structure    = profile.get("structure", "result_unknown")
    context      = profile.get("context", "pure")
    num_diff_scalar = diff_scalar

    allowed_divisors = _table_for_level(table_level, grade)

    candidate_pairs = []
    for b in allowed_divisors:
        for q in range(1, q_max + 1):
            if rem_level == "none":
                a = b * q
                if _satisfies_remainder(a, b, rem_level):
                    candidate_pairs.append((a, b))
            else:
                for r in range(1, b):
                    a = b * q + r
                    if _satisfies_remainder(a, b, rem_level):
                        candidate_pairs.append((a, b))

    if not candidate_pairs:
        raise RuntimeError(
            f"generate_params (division): no valid pair found for grade={grade}, "
            f"profile={difficulty_profile}."
        )

    from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
    a, b = generate_pair_by_window(candidate_pairs, num_diff_scalar, d=5, rng=rng)

    blank_target = {
        "result_unknown":  "result",
        "divisor_unknown": "b",
    }.get(structure, "result")

    result_dict = {
        "a":           a,
        "b":           b,
        "result":      a // b,
        "remainder":   a % b,
        "blank_target": blank_target,
        "context":     context,
        "structure":   structure,
    }

    return result_dict


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hint strings for the given division problem."""
    a         = values["a"]
    b         = values["b"]
    result    = values["result"]
    remainder = values.get("remainder", a % b)

    quotient_label  = VOCAB_QUOTIENT.resolve(cumulative_vocab)
    dividend_label  = VOCAB_DIVIDEND.resolve(cumulative_vocab)
    divisor_label   = VOCAB_DIVISOR.resolve(cumulative_vocab)
    rem_label       = VOCAB_REMAINDER.resolve(cumulative_vocab)

    hints: List[str] = []

    # Step 1: restate the problem
    hints.append(
        f"We need to divide {a} by {b}. "
        f"{dividend_label.capitalize()} is {a}; {divisor_label} is {b}."
    )

    # Step 2: think in terms of multiplication
    hints.append(
        f"Ask: how many times does {b} fit into {a}? "
        f"{b} × {result} = {b * result}."
    )

    # Step 3: remainder (if any)
    if remainder > 0:
        hints.append(
            f"{a} − {b * result} = {remainder}. "
            f"{rem_label.capitalize()} is {remainder}."
        )

    # Step 4: final answer
    if remainder > 0:
        hints.append(
            f"{quotient_label.capitalize()} is {result} remainder {remainder} "
            f"(written as {result} R{remainder})."
        )
    else:
        hints.append(f"{quotient_label.capitalize()} of {a} ÷ {b} = {result}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

DIVISION_DNA = DNA(
    concept="division",
    dna_type="formula",
    answer_formula="a // b",
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
