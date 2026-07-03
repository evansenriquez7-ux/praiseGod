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
_DIFFICULTY_AXES: Dict[str, Any] = {"number_difficulty": "continuous"}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_DIFFERENCE   = VocabGated(requires_vocab="difference",  preferred="the difference",  fallback="the answer")
VOCAB_MINUEND      = VocabGated(requires_vocab="minuend",     preferred="the minuend",     fallback="the starting number")
VOCAB_SUBTRAHEND   = VocabGated(requires_vocab="subtrahend",  preferred="the subtrahend",  fallback="the number being subtracted")
VOCAB_REGROUP      = VocabGated(requires_vocab="regroup",     preferred="regroup",         fallback="borrow")





# ─── constraint predicates ────────────────────────────────────────────────────

def _satisfies_regrouping(a: int, b: int, level: str) -> bool:
    """Check if a pair satisfies borrowing difficulty based on COUNT of places.

    For subtraction, borrowing (regrouping) occurs when a digit in b > corresponding digit in a.
    Counts borrows across all digit places (ones, tens, hundreds, thousands, etc).

    Difficulty levels:
    - "none": 0 places require borrowing
    - "one_place": exactly 1 place requires borrowing
    - "two_places": exactly 2 places require borrowing
    - "three_places": exactly 3 places require borrowing
    - "four_places": 4+ places require borrowing
    """
    borrow_count = 0
    borrow = 0

    # Process each digit place from ones to ten-thousands
    for place_value in [1, 10, 100, 1000]:
        digit_a = (a // place_value) % 10 - borrow
        digit_b = (b // place_value) % 10

        if digit_a < digit_b:
            borrow_count += 1
            borrow = 1
        else:
            borrow = 0

    if level == "none":
        return borrow_count == 0
    if level == "one_place":
        return borrow_count == 1
    if level == "two_places":
        return borrow_count == 2
    if level == "three_places":
        return borrow_count == 3
    if level == "four_places":
        return borrow_count >= 4
    # Legacy support for old naming
    if level == "ones":
        ones_needs = (a % 10) < (b % 10)
        return borrow_count == 1 and ones_needs
    if level == "tens":
        ones_needs = (a % 10) < (b % 10)
        a_tens = (a // 10 % 10) - (1 if ones_needs else 0)
        tens_needs = a_tens < (b // 10 % 10)
        return borrow_count == 1 and tens_needs
    if level == "double":
        return borrow_count == 2
    return True


# Number of borrow places each regrouping level *requires*. Mirror of the
# addition table; used by max_regrouping_places to decide feasibility.
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


def max_regrouping_places(max_minuend: int) -> int:
    """Largest borrow count achievable for any (a, b) with a <= max_minuend, a >= b.

    A subtraction whose minuend is bounded by an N-digit `max_minuend` can borrow
    at most N-1 times: the top digit has no higher place to borrow from. Verified
    exhaustively against `_satisfies_regrouping`:
        max_minuend   20 (2 digits) -> 1
        max_minuend  100 (3 digits) -> 2
        max_minuend  999 (3 digits) -> 2
        max_minuend 1000 (4 digits) -> 3

    Single source of truth for borrow feasibility (mirrors addition's carry
    version). The lab-config builder, orchestrator pre-filter, auditor mirror,
    and the DNA guard all defer to it.
    """
    if max_minuend < 10:
        return 0
    return len(str(int(max_minuend))) - 1


def regrouping_is_feasible(level: str, max_minuend: int) -> bool:
    """True if `level` can be satisfied by some (a, b) with a <= max_minuend."""
    return REGROUP_LEVEL_PLACES.get(level, 0) <= max_regrouping_places(max_minuend)


def _satisfies_number_type(a: int, b: int, level: str) -> bool:
    if level == "round":
        return a % 10 == 0 and b % 10 == 0
    if level == "non_round":
        return not (a % 10 == 0 and b % 10 == 0)
    return True


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate (a, b) with a >= b that satisfy the difficulty_profile constraints.

    Uses smart candidate generation:
    1. Build candidate pool from per-grade _PARAM_BOUNDS (operand ceiling)
    2. Filter pairs by regrouping constraint
    3. Randomly select from valid pairs

    Supports difficulty dimensions:
    - regrouping: "none", "ones", "tens", "double" - discrete
    - number_type: "non_round", "round" - discrete
    - number_difficulty: continuous (0.0-1.0)

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

    g_key = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]
    max_minuend_bound = bounds["a"][1]

    # Operand bound: the per-grade `_PARAM_BOUNDS[grade]["a"][1]` already
    # aligns with the LCs' operand-bound language ("both numbers are
    # less than N" → g1: a<100, g2: a<1000, g3: a<10000). The
    # `max_difference` axis was removed from the catalog on 2026-07-01
    # because no MATATAG K-3 LC specifies a result ceiling for
    # subtraction — see axes_catalog.py header.
    max_minuend = max_minuend_bound

    # Ensure reasonable bounds
    max_minuend = max(2, min(max_minuend, 10000))
    if "formatter_max_val" in profile:
        max_minuend = min(max_minuend, profile["formatter_max_val"])

    reg_level = profile.get("regrouping", "none")
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    # Fail fast on infeasible (range, regrouping) combinations. A minuend bounded
    # by `max_minuend` can borrow at most `max_regrouping_places(max_minuend)`
    # times, so a level demanding more places has no valid pair. Raise instead of
    # exhausting the rejection loop below (defense in depth — the
    # orchestrator/auditor pre-filter should keep these from reaching here).
    if not regrouping_is_feasible(reg_level, max_minuend):
        raise RuntimeError(
            f"generate_params (subtraction): regrouping level '{reg_level}' requires "
            f"{REGROUP_LEVEL_PLACES.get(reg_level, 0)} borrow places but max_minuend="
            f"{max_minuend} allows at most {max_regrouping_places(max_minuend)}. "
            f"Infeasible combination (grade={grade}, profile={difficulty_profile})."
        )

    # Contextual variants
    context = profile.get("context", "pure")
    spine = profile.get("spine", None)
    
    # Structure determines which value is unknown (algebraic position):
    # - "result_unknown": a - b = ? (default)
    # - "change_unknown": a - ? = result (for missing number competencies)
    # - "start_unknown": ? - b = result (for missing number competencies)
    structure = profile.get("structure", "result_unknown")

    # Build candidate pool with a grade-appropriate floor
    min_a = 1
    if grade >= 3 and max_minuend >= 100:
        min_a = 10  # Enforce at least 2-digit minuends for Grade 3+ large bounds
    if grade >= 4 and max_minuend >= 1000:
        min_a = 100 # Enforce at least 3-digit minuends for Grade 4+ large bounds
        
    candidates_a = list(range(min_a, max_minuend + 1))

    # Build valid pairs with rejection sampling
    candidate_pairs = []
    # Generate the full, curriculum-accurate pair space (b in [0, a] so the
    # result a-b is non-negative — K-3 has no negative results). Pairs like
    # (a, 0) = "a - 0 = a", (a, a) = "a - a = 0", and (2b, b) = "a - b = b" are
    # LEGITIMATE MATATAG problems (subtracting zero, subtracting a number from
    # itself, etc.) and are NOT excluded here. Whether the answer appears
    # verbatim in the stem is a SEMANTIC-LEAK concern handled at render time via
    # FormattedProblem.given_values / blank_target and the auditor's
    # explainable-count check — not by dropping valid number pairs.
    if max_minuend <= 100:
        for a in candidates_a:
            for b in range(0, a + 1):
                if _satisfies_regrouping(a, b, reg_level):
                    candidate_pairs.append((a, b))
    else:
        # Feasible level (guard above): the pool fills in far fewer than 2000
        # draws, so a low cap suffices.
        attempts = 0
        while len(candidate_pairs) < 2000 and attempts < 5000:
            attempts += 1
            a = rng.randint(min_a, max_minuend)
            b = rng.randint(0, a)
            if _satisfies_regrouping(a, b, reg_level):
                candidate_pairs.append((a, b))

    if not candidate_pairs:
        # No pair satisfies the requested regrouping constraint within the
        # range. Fail fast — do NOT silently return a pair that ignores the
        # constraint (that was the previous behaviour and it emitted off-spec
        # problems, violating AGENTS.md #4 / fail-fast). The feasibility guard
        # above already rejects structurally-impossible levels; reaching here
        # means the constraint is satisfiable in principle but not for this
        # exact range/exclusion set, which is still a real incompatibility.
        raise RuntimeError(
            f"generate_params (subtraction): no valid (a, b) pair exists for "
            f"max_minuend={max_minuend}, regrouping='{reg_level}' with the "
            f"non-degenerate exclusions (b>=1, a!=2b, a!=b). "
            f"Constraints are incompatible (grade={grade}, profile={difficulty_profile})."
        )

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
        "max_minuend": max_minuend,
    }

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
