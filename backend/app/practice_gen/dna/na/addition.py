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


def regrouping_is_feasible(level: Any, max_result: int, grade: Optional[int] = None) -> bool:
    """True if `level` can be satisfied by some (a, b) with a + b <= max_result."""
    if level is False:
        level = "none"
    elif level is True:
        level = "ones"
    if grade == 1 or (grade is None and max_result <= 100):
        # For Grade 1, a and b are bounded by 50, so tens/double regrouping are not feasible
        return level in ("none", "ones")
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
    if reg_level is False:
        reg_level = "none"
    elif reg_level is True:
        reg_level = "ones"
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

    task_type = profile.get("task_type")
    if task_type == "estimate":
        # "Estimate the sum of addends with up to 4 digits" (mat_g3_na_q2_2)
        # is a distinct skill from exact addition -- round EACH addend to
        # its OWN leading place value (front-end rounding), then add the
        # rounded values. Unlike subtraction's estimate (which rounds both
        # operands to the SAME precision to guarantee a non-negative
        # result), addition has no such constraint, so each addend rounds
        # independently -- the standard technique taught for sum
        # estimation. The co-mapped `rounding` DNA rounds ONE number, not a
        # sum of two, so it cannot express this competency regardless of
        # which node maps to it (see registry.py's "estimate" text match).
        # "regrouping" is a declared discrete axis for this DNA and the
        # harness's §1B discrete-integrity sweep explicitly tests every
        # option value (including "none") by passing it in the profile.
        # Carry-counting is not a meaningful, controllable property of a
        # round-then-add estimate (rounding each addend independently to
        # its own leading place can still carry above that place, e.g.
        # 90 + 20 = 110), so any EXPLICIT regrouping request is infeasible
        # here -- raising lets the harness's existing "infeasible
        # combination, skip" handling apply (mirrors subtraction's
        # task_type='estimate' guard). A profile that simply omits
        # "regrouping" (the normal/default rendering path) is unaffected.
        if "regrouping" in profile:
            raise RuntimeError(
                f"generate_params (addition): task_type='estimate' rounds "
                f"each addend to its own leading place before adding, which "
                f"is not a regrouping-controllable operation -- an explicit "
                f"regrouping='{profile['regrouping']}' request is infeasible "
                f"for task_type='estimate' (grade={grade}, seed={seed})."
            )

        def _round_half_up(n: int, precision: int) -> int:
            remainder = n % precision
            if remainder >= precision / 2:
                return n - remainder + precision
            return n - remainder

        from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
        # est_min=1 (not 10): front-end rounding to each addend's OWN
        # leading place already no-ops naturally for single-digit values
        # (round_to=10**0=1), so no artificial floor is needed -- and one
        # is actively harmful at a low max_sum ceiling (the §1A scalar-0.0
        # sweep can drive max_result down to single digits, where a
        # floor of 10 makes every candidate's rounded sum structurally
        # exceed the ceiling).
        est_min = 1
        est_max = max(est_min + 1, min(max_result, 9999))
        candidates = []
        attempts = 0
        while len(candidates) < 500 and attempts < 5000:
            attempts += 1
            x = rng.randint(est_min, est_max)
            y = rng.randint(est_min, est_max)
            # The competency's own max_sum ceiling bounds the SUM (this is
            # the pre-existing ground truth the exact-addition path on this
            # same node already enforced) -- filter on the ROUNDED sum, not
            # the real one, since rounding can push a borderline pair over.
            rt_x = 10 ** (len(str(x)) - 1)
            rt_y = 10 ** (len(str(y)) - 1)
            if _round_half_up(x, rt_x) + _round_half_up(y, rt_y) > max_result:
                continue
            candidates.append((x, y))
        if not candidates:
            raise RuntimeError(
                f"generate_params (addition): no valid estimate pair for "
                f"max_result={max_result} (grade={grade}, profile={difficulty_profile})."
            )

        # A pair where BOTH addends already sit on their own leading-place
        # boundary (e.g. 20 + 2 -> rounds to itself, "estimate" == exact sum,
        # observed at ~6% of samples) renders as a front-end-rounding item
        # that never exercises rounding at all -- the same "structurally
        # valid but pedagogically vacuous" shape as the 0-operand pattern
        # thinned above. Same convention: thin to a ~10% cap of the
        # meaningful pool rather than exclude outright, so it stays
        # reachable when it's the only option a tight max_result leaves.
        def _is_degenerate_estimate(pair: tuple) -> bool:
            x, y = pair
            rt_x = 10 ** (len(str(x)) - 1)
            rt_y = 10 ** (len(str(y)) - 1)
            return _round_half_up(x, rt_x) == x and _round_half_up(y, rt_y) == y

        _meaningful = [p for p in candidates if not _is_degenerate_estimate(p)]
        _degenerate = [p for p in candidates if _is_degenerate_estimate(p)]
        if _meaningful and _degenerate:
            cap = max(1, len(_meaningful) // 10)
            candidates = _meaningful + _degenerate[:cap]
        elif _meaningful:
            candidates = _meaningful

        real_a, real_b = generate_pair_by_window(candidates, num_diff_scalar, d=5, rng=rng)

        round_to_a = 10 ** (len(str(real_a)) - 1)
        round_to_b = 10 ** (len(str(real_b)) - 1)
        rounded_a = _round_half_up(real_a, round_to_a)
        rounded_b = _round_half_up(real_b, round_to_b)

        return {
            # "a"/"b" carry the ROUNDED values (see subtraction.py's
            # identical convention) so this DNA's answer_formula "a + b"
            # recomputes to the same value the auditor's answer-key
            # integrity check independently derives from given_values.
            "a": rounded_a,
            "b": rounded_b,
            "result": rounded_a + rounded_b,
            "real_a": real_a,
            "real_b": real_b,
            "task_type": "estimate",
            "blank_target": "result",
            "context": "pure",
            "structure": "result_unknown",
            "max_sum": max_result,
            "strategy": "standard",
        }

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
    if not regrouping_is_feasible(reg_level, max_result, grade=grade):
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

    # A 0 operand ("What is 4 + 0?") is a legitimate MATATAG fact (the
    # identity property) but was 30-70% of sampled items at the default
    # profile across addition/subtraction nodes -- an artifact of how the
    # pool is built and scored, not a deliberate identity-property lesson
    # (that is a distinct, currently-unbuilt task type; see
    # HARDENING_EVIDENCE.md). Prefer the non-zero-operand subset so a 0
    # operand stays reachable (still in the full pool, and the sole option
    # when max_result/regrouping leaves nothing else) without dominating
    # ordinary practice. This does not touch which (a, b) pairs are valid --
    # only which of the already-valid pairs get first refusal.
    # A hard exclusion (drop every 0-operand pair whenever an alternative
    # exists) overcorrects: 0 becomes reachable only when the non-zero subset
    # is completely empty, which for any normal max_result/regrouping
    # combination it never is -- so a 0 operand stopped being generated at
    # all, not just stopped dominating. subtraction.py's identical fix hit
    # this exact regression against tests/unit/test_semantic_leak_guards.py,
    # which exists specifically to keep 0-operand pairs reachable (legitimate
    # identity-property content). Thin instead of exclude: 0-operand pairs
    # are capped at ~10% of the non-zero pool rather than dropped.
    # (0, 0) is a distinct, structural case, not just another 0-operand pair:
    # "0 + 0 = ___" (or its word-problem phrasing, "has 0 ... gets 0 ...")
    # has exactly ONE distinct number in the entire stem, and that number IS
    # the answer -- an unconditional §1F answer-leak for every possible
    # rendering, not a render-choice mistake. Excluded outright; every other
    # 0-operand pair ("4 + 0", "0 + 4") has a second, different number in the
    # stem and is not structurally leaky, so it's only thinned, not excluded.
    _without_00 = [p for p in candidate_pairs if p != (0, 0)]
    if _without_00:
        candidate_pairs = _without_00
    zero_pairs = [p for p in candidate_pairs if p[0] == 0 or p[1] == 0]
    nonzero_pairs = [p for p in candidate_pairs if p[0] != 0 and p[1] != 0]
    if nonzero_pairs and zero_pairs:
        cap = max(1, len(nonzero_pairs) // 10)
        candidate_pairs = nonzero_pairs + zero_pairs[:cap]
    elif nonzero_pairs:
        candidate_pairs = nonzero_pairs

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

    # Whether place-value column terminology is known to the student
    knows_place_value = "ones" in cumulative_vocab and "tens" in cumulative_vocab

    hints: List[str] = []

    # Step 1: identify the operation
    hints.append(f"We are adding two numbers: {a} and {b}.")

    # Step 2: ones column (rightmost digit)
    ones_a, ones_b = a % 10, b % 10
    ones_sum = ones_a + ones_b
    if knows_place_value:
        if ones_sum >= 10:
            hints.append(
                f"Add the ones: {ones_a} + {ones_b} = {ones_sum}. "
                f"Write {ones_sum % 10} in the ones place and {reg_phrase} 1 ten."
            )
        else:
            hints.append(f"Add the ones: {ones_a} + {ones_b} = {ones_sum}. Write {ones_sum} in the ones place.")
    else:
        # Position-neutral language for students who haven't learned place value yet
        if ones_sum >= 10:
            hints.append(
                f"Add the last digits: {ones_a} + {ones_b} = {ones_sum}. "
                f"Write {ones_sum % 10} and {reg_phrase} 1."
            )
        else:
            hints.append(f"Add the last digits: {ones_a} + {ones_b} = {ones_sum}.")

    # Step 3: leading column (only shown when both numbers have more than one digit)
    if a >= 10 or b >= 10:
        carry    = 1 if ones_sum >= 10 else 0
        tens_a   = a // 10 % 10
        tens_b   = b // 10 % 10
        tens_sum = tens_a + tens_b + carry
        if knows_place_value:
            hints.append(
                f"Add the tens: {tens_a} + {tens_b}"
                + (f" + {carry} (carried)" if carry else "")
                + f" = {tens_sum}."
            )
        else:
            hints.append(
                f"Add the first digits: {tens_a} + {tens_b}"
                + (f" + {carry}" if carry else "")
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
