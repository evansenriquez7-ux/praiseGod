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
from typing import Any, Dict, List, Optional, Set, Tuple

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
    "2_3_4_5_10": [0, 1, 2, 3, 4, 5, 10],
    "6_7_8_9":    [0, 1, 6, 7, 8, 9],
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_PRODUCT  = VocabGated(requires_vocab="product",  preferred="the product",  fallback="the answer")
VOCAB_FACTOR   = VocabGated(requires_vocab="factor",   preferred="factor",       fallback="number")
VOCAB_MULTIPLY = VocabGated(requires_vocab="multiply", preferred="multiply",     fallback="find the total of equal groups")
VOCAB_TIMES    = VocabGated(requires_vocab="times",    preferred="times",        fallback="groups of")


# ─── constraint predicates ────────────────────────────────────────────────────

def _table_for_level(level: str, grade: int) -> List[int]:
    """Return the allowed factor-b values for the given table axis level.

    Includes 0 (multiplicative identity) and 1 for all grades.
    """
    if grade <= 2:
        # Grade 2 uses 0, 1, 2, 3, 4, 5, 10 tables
        return [0, 1, 2, 3, 4, 5, 10]
    return _TABLE_SETS.get(level, [0, 1, 2, 3, 4, 5, 10])


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
    # An *unbound* number_type is not the same as an explicit "single_digit"
    # selection. Defaulting to single_digit capped every G3 competency at
    # a<=9, so "Solve 1- to 2-step multiplication problems" could never produce
    # a product above max(table)*9 = 90 however high its ceiling
    # (validate_matrix §1A-reach). None means "unrestricted — let max_product
    # govern"; an explicit value is still honoured exactly.
    # A competency that names specific tables ("the 6, 7, 8, and 9 tables") is
    # about single-digit facts, so single_digit stays the default there. Where no
    # table is bound the ceiling governs instead.
    num_level   = profile.get("number_type") or (
        "single_digit" if profile.get("table") else "any"
    )
    structure   = profile.get("structure", "result_unknown")
    context     = profile.get("context", "pure")
    task_type   = profile.get("task_type")
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    allowed_tables = _table_for_level(table_level, grade)
    # NOTE on task_type == "repeated_addition" (mat_g2_na_q3_1): restricting
    # `allowed_tables` here to exclude trivial (0, 1) facts or cap the top end
    # was tried and reverted -- both broke real §1A/§1A-reach contracts this
    # DNA must keep: max_product=1 at the low end needs a 1x1-shaped product
    # to exist, and the competency's stated ceiling (100) needs a_hi*max(table)
    # to reach it. The candidate pool stays exactly what it always was; the
    # repeated-addition framing is applied at render time instead (see the
    # b <= 5 gate in the formatters and base_generator._build_symbolic_question),
    # which does not change what this DNA is able to generate or its reach.
    a_lo = bounds["a"][0]
    if num_level == "multi_digit":
        a_lo = max(10, a_lo)
    a_hi = max(a_lo, bounds["a"][1])

    max_prod_val = profile.get("max_product")
    if max_prod_val is not None:
        max_prod_val = int(max_prod_val)
    else:
        max_prod_val = 999999 # Rely on bounds["a"]

    if task_type == "estimate":
        # "Estimate the product of 2- to 3-digit numbers by 1- to 2-digit
        # numbers by estimating the factors using multiples of 10"
        # (mat_g3_na_q3_3): round EACH factor to the nearest 10 (the
        # competency names "multiples of 10" explicitly, not front-end
        # rounding to varying precision like addition/subtraction's
        # estimate), then multiply the rounded factors. The co-mapped
        # `rounding` DNA rounds ONE number, not two factors of a product,
        # so it cannot express this competency regardless of which node
        # maps to it (see registry.py's "estimate" text match).
        # Both factors are preferably drawn from >=10 rather than the full
        # "1- to 2-digit" range: rounding a single-digit factor (1-9) to
        # the nearest 10 collapses it to 0 or 10, and a 0 factor makes the
        # "estimate" trivially 0 -- not a meaningful exercise of this
        # skill. Restricting both factors to >=10 keeps every generated
        # item a genuine two-multi-digit-factor estimate whenever the
        # ceiling allows it (the minimum non-degenerate rounded product
        # with both factors >=10 is 10*10=100).
        def _round_half_up(n: int, precision: int = 10) -> int:
            remainder = n % precision
            if remainder >= precision / 2:
                return n - remainder + precision
            return n - remainder

        from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window

        def _build_estimate_candidates(min_a: int, min_b: int) -> List[Tuple[int, int]]:
            cands: List[Tuple[int, int]] = []
            attempts = 0
            while len(cands) < 500 and attempts < 5000:
                attempts += 1
                x = rng.randint(min_a, 999)
                y = rng.randint(min_b, 99)
                if _round_half_up(x) * _round_half_up(y) > max_prod_val:
                    continue
                cands.append((x, y))
            return cands

        candidates = _build_estimate_candidates(10, 10)
        if not candidates:
            # max_prod_val < 100: no two-multi-digit-factor product can fit
            # under the ceiling at all (the harness's own default-scalar
            # interpolation can drive max_product this low for some node/
            # combination pairs). Fall back to the full 1- to 2-digit
            # range -- a factor rounding to 0 is a legitimate, if less
            # illustrative, front-end-rounding example, and the only way
            # to serve *any* item under such a tight ceiling. Same "thin,
            # don't exclude; fall back to the full pool only when the
            # preferred subset is empty" convention as addition.py/
            # subtraction.py's 0-operand handling.
            candidates = _build_estimate_candidates(1, 1)
        if not candidates:
            raise RuntimeError(
                f"generate_params (multiplication): no valid estimate pair "
                f"for grade={grade}, profile={difficulty_profile}."
            )

        # A pair where BOTH factors already sit on a multiple of 10 (e.g.
        # 20 x 30 -> rounds to itself, "estimate" == exact product) renders
        # as a front-end-rounding item that never exercises rounding -- the
        # same shape addition.py's identical fix thins (~4% of samples
        # here). Same convention: thin to a ~10% cap of the meaningful pool
        # rather than exclude, so it stays reachable when it's the only
        # option a tight max_prod_val leaves.
        def _is_degenerate_estimate(pair: tuple) -> bool:
            x, y = pair
            return _round_half_up(x) == x and _round_half_up(y) == y

        _meaningful = [p for p in candidates if not _is_degenerate_estimate(p)]
        _degenerate = [p for p in candidates if _is_degenerate_estimate(p)]
        if _meaningful and _degenerate:
            cap = max(1, len(_meaningful) // 10)
            candidates = _meaningful + _degenerate[:cap]
        elif _meaningful:
            candidates = _meaningful

        real_a, real_b = generate_pair_by_window(candidates, num_diff_scalar, d=5, rng=rng)

        rounded_a = _round_half_up(real_a)
        rounded_b = _round_half_up(real_b)

        return {
            "a": rounded_a,
            "b": rounded_b,
            "result": rounded_a * rounded_b,
            "real_a": real_a,
            "real_b": real_b,
            "task_type": "estimate",
            "blank_target": "result",
            "context": "pure",
            "structure": "result_unknown",
            "groups": rounded_a,
            "n": rounded_b,
            "total": rounded_a * rounded_b,
        }

    candidate_pairs = []
    for b in allowed_tables:
        for a in range(a_lo, a_hi + 1):
            if a * b > max_prod_val:
                continue
            # b of 0 or 1 makes the product test vacuous, letting a multiplicand
            # sail past the competency's own magnitude ceiling (92 x 0 = 0 slips
            # through a "products up to 90" bound). Hold those operands to the
            # ceiling too — but only for b <= 1, since for b >= 2 the product
            # test already implies it, and applying it unconditionally emptied
            # the pool for multi-digit competencies at low scalars.
            if b <= 1 and a > max_prod_val and num_level != "multi_digit":
                continue
            if _satisfies_number_type(a, num_level):
                candidate_pairs.append((a, b))

    # "... and 2- to 4-digit numbers by a number whose leading digit is the only
    # non-zero digit, with products up to 10 000" (mat_g3_na_q3_2). Multiplying by
    # a round number (20, 300, 2000) is a sub-skill the competency names outright,
    # and it is the only way products reach that stated ceiling: the table list
    # tops out at 10 and `a` at 99, so the pool above could never exceed 990.
    ceiling_from_tables = max(allowed_tables) * a_hi if allowed_tables else 0
    if num_level in ("any", "multi_digit") and max_prod_val > ceiling_from_tables:
        round_multipliers = [d * (10 ** k) for k in (1, 2, 3) for d in range(1, 10)]
        for b in round_multipliers:
            a_max_for_b = min(9999, max_prod_val // b)
            if a_max_for_b < 10:
                continue
            # Sample the range rather than enumerating it — a few dozen
            # candidates per multiplier is plenty for the windowed picker and
            # keeps the pool from exploding into six figures.
            step = max(1, (a_max_for_b - 10) // 40)
            for a in range(10, a_max_for_b + 1, step):
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
        "task_type": task_type,
        # Aliases for the mul_* word-problem spines (spines.py), whose
        # templates use "groups"/"n"/"total" rather than this DNA's own
        # "a"/"b"/"result" -- Spine.render() does a raw str.format() over
        # {**slots, **values}, so a missing alias raises KeyError and
        # silently falls back to the plain symbolic question, even though
        # a spine was already selected (spine_id would say otherwise).
        "groups": a,
        "n": b,
        "total": a * b,
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
