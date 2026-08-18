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

def decompose_to_places(n: int) -> str:
    """
    "N is H hundreds, T tens, and O ones." (place values whose digit is 0
    are omitted, except ones which always shows -- "23 is 2 tens and 3
    ones", not "23 is 0 hundreds, 2 tens, and 3 ones"). Shared by
    task_type="expanded_form" (this file) and the fmt_true_false.py/
    fmt_cloze.py formatters that independently rebuild question text for
    it, so the decomposition wording stays identical everywhere it's used.
    """
    hundreds, rem = divmod(n, 100)
    tens, ones = divmod(rem, 10)

    def _place(count: int, word: str) -> str:
        # "1 tens"/"1 ones" reads as a grammar error a Grade 1-2 reader
        # stumbles on -- singularize whenever the count is exactly 1
        # (blind review of mat_g2_na_q1_8).
        return f"{count} {word if count != 1 else word[:-1]}"

    parts = []
    if hundreds:
        parts.append(_place(hundreds, "hundreds"))
    if hundreds or tens:
        parts.append(_place(tens, "tens"))
    parts.append(_place(ones, "ones"))
    if len(parts) == 1:
        return f"{n} is {parts[0]}."
    if len(parts) == 2:
        return f"{n} is {parts[0]} and {parts[1]}."
    return f"{n} is {parts[0]}, {parts[1]}, and {parts[2]}."


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
    max_result = max(2, max_result)

    # Difficulty axes
    if "regrouping" in profile:
        reg_level = profile.get("regrouping", "none")
        if reg_level is False:
            reg_level = "none"
        elif reg_level is True:
            reg_level = "ones"
    else:
        # Truly unbound (key absent, not merely set to "none"/False):
        # registry.py now correctly leaves "with and without regrouping"
        # competencies unbound rather than wrongly forcing regrouping=False,
        # but this DNA's own default here was still the fixed string
        # "none" -- so those competencies still never demonstrated a
        # single carry, just via a different mechanism (blind review
        # confirmed 0 regrouping cases across dozens of samples for
        # several "with and without regrouping" nodes). Vary across every
        # level actually feasible at this max_result instead.
        # "three_places"/"four_places" excluded even when
        # regrouping_is_feasible's arithmetic bound allows them -- at large
        # max_result the pair-builder below falls back to rejection
        # sampling with a fixed attempt cap, and a 3-or-4-place-carry pair
        # is rare enough within that cap to intermittently raise "no valid
        # pair exists" for some seeds (a pre-existing sampling-density
        # limitation, not a feasibility one; reproduced by the matrix
        # validator's own scalar=1.0 sweep, same pattern as subtraction.py).
        # "two_places" is exercised by that same exhaustive sweep clean.
        feasible_levels = [
            lvl for lvl in ("none", "one_place", "two_places")
            if regrouping_is_feasible(lvl, max_result, grade)
        ]
        reg_level = rng.choice(feasible_levels) if feasible_levels else "none"
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

    if task_type == "models_strategies":
        task_type = rng.choice(["counting_up", "putting_together"])

    if task_type == "properties":
        # The registry binds this sentinel for the two "properties of addition"
        # competencies (mat_g1_na_q1_8, mat_g2_na_q1_10). Those competencies
        # name several properties each, so pinning one task_type would leave
        # the others untested; cycle them by seed instead, so a node's sample
        # set covers every property its own competency names.
        #
        # Grade gates the set: G1 names the zero identity and commutativity,
        # G2 adds associativity ("changing the grouping of the addends"), which
        # is not a G1 concept -- the associative branch below already refuses
        # grade < 2, so offering it here would silently fall through to plain
        # addition and reintroduce exactly the defect this fixes.
        property_tasks = ["zero_identity", "commutative"]
        if grade >= 2:
            property_tasks.append("associative")
        task_type = property_tasks[rng.randrange(len(property_tasks))]

    def _carry_free_addends(count: int, max_total: int) -> List[int]:
        """
        Pick `count` positive addends whose column sums never carry.

        The properties nodes pin regrouping to "none" (the property is about
        structure, not carrying), so the addends these tasks show must actually
        be carry-free or validate_matrix's discrete integrity check rejects the
        item -- it caught "Is (18 + 18) + 14 the same as 18 + (18 + 14)?", where
        18 + 18 carries. Reserving one unit of the ones column per addend keeps
        every addend >= 1, and capping the tens budget by what the ones column
        already spent keeps the total inside max_total.
        """
        # Ones: reserve one unit per addend so every addend is >= 1.
        ones_budget = max(0, 9 - count)
        ones = [1] * count
        for i in range(count):
            take = rng.randint(0, ones_budget)
            ones[i] += take
            ones_budget -= take

        # Each higher column gets its own budget of 9 -- a column whose digits
        # sum to 9 or less cannot carry -- capped by what the lower columns have
        # already spent so the total stays inside max_total.
        #
        # The hundreds column matters: budgeting ones and tens alone caps every
        # addend at 99, which silently shrank mat_g2_na_q1_10 ("...properties of
        # addition using sums up to 1000") to a largest sum of 97. A blind
        # re-review caught that as a scale_appropriateness CONCERN.
        columns: List[List[int]] = [ones]
        running = sum(ones)
        for place in (10, 100):
            budget = min(9, max(0, (max_total - running) // place))
            column = []
            for _ in range(count):
                take = rng.randint(0, budget)
                column.append(take)
                budget -= take
            columns.append(column)
            running += place * sum(column)

        return [
            ones[i] + 10 * columns[1][i] + 100 * columns[2][i]
            for i in range(count)
        ]

    if task_type in ("zero_identity", "commutative", "associative"):
        # Regrouping is not a dimension these tasks can vary. "n + 0 = n"
        # cannot carry at all, and "Is a + b the same as b + a?" is answered
        # from the structure of the sentence rather than by computing a sum, so
        # forcing a carry into it changes nothing a pupil does. Requesting a
        # specific regrouping level here is therefore an infeasible
        # combination, in the same sense as regrouping="two_places" with
        # max_sum=20 -- which validate_matrix already accepts as expected for
        # constrained nodes (it catches RuntimeError from generation and skips
        # the pair). Raise rather than silently emitting an item that ignores
        # the requested level, which is what made the matrix's discrete
        # integrity check fail on one_place and two_places.
        # "No regrouping" is spelled three ways across the codebase: absent,
        # the string "none" (the difficulty axis level), and the boolean False
        # (how registry bounds encode "...without regrouping" competencies,
        # e.g. mat_g1_na_q2_5). All three are satisfiable; only a positive
        # request for a specific carry depth is not.
        requested_regrouping = profile.get("regrouping")
        if requested_regrouping not in (None, False, 0, "none"):
            raise RuntimeError(
                f"addition: regrouping={requested_regrouping!r} is not expressible by the "
                f"{task_type!r} property task (grade={grade}, seed={seed}, max_sum={max_result}); "
                f"property demonstrations do not vary by carrying."
            )

    if task_type == "zero_identity":
        # "Adding zero leaves a number unchanged" (mat_g1_na_q1_8,
        # mat_g2_na_q1_10) was never a distinct, deliberately-generated
        # case -- a 0 operand only ever appeared as an incidental,
        # ~10%-thinned byproduct of the general candidate pool below
        # (see "A 0 operand..." comment), never as a task explicitly
        # isolating the identity property itself.
        other = rng.randint(1, max(1, max_result - 1))
        zero_first = rng.choice([True, False])
        a_val, b_val = (0, other) if zero_first else (other, 0)
        return {
            "a": a_val, "b": b_val, "result": other,
            "task_type": "zero_identity",
            "blank_target": "result",
            "context": "pure",
            "structure": "result_unknown",
            "max_sum": max_result,
            "strategy": "standard",
        }

    if task_type == "commutative":
        # "Swapping addend order preserves the sum" (mat_g1_na_q1_8, mat_g2_na_q1_10)
        a_val, b_val = _carry_free_addends(2, max_result)
        if a_val == b_val and max_result > 2:
            b_val = b_val - 1 if b_val > 1 else b_val + 1
        return {
            "a": a_val, "b": b_val,
            "task_type": "commutative",
            "blank_target": "answer",
            "context": "pure",
            "max_sum": max_result,
            "answer": True,
            "distractors": [False],
            "question": f"Is {a_val} + {b_val} the same as {b_val} + {a_val}?",
        }

    if task_type == "associative" and grade >= 2:
        # "Grouping-changing" (mat_g2_na_q1_10): (a+b)+c == a+(b+c).
        # Grade-2+ only -- the competency names this alongside
        # zero-identity/commutative for the G2 "properties" node
        # specifically, and 3-operand grouping is not a G1 concept.
        a_val, b_val, c_val = _carry_free_addends(3, max_result)
        return {
            "a": a_val, "b": b_val, "c": c_val,
            "task_type": "associative",
            "blank_target": "answer",
            "context": "pure",
            "max_sum": max_result,
            "answer": True,
            "distractors": [False],
            "question": f"Is ({a_val} + {b_val}) + {c_val} the same as {a_val} + ({b_val} + {c_val})?",
        }

    if task_type == "expanded_form":
        max_result = max(11, max_result)
        # Threshold is the branch's own structural minimum, not an arbitrary
        # round number: lo=10 below always requires a two-digit `a`, so the
        # smallest representable sum is 10+1=11. The previous ">= 20" guard
        # silently fell through to the plain/default branch below whenever
        # this task_type was registry-bound but max_result (the per-seed
        # windowed ceiling, not the node's absolute cap) came in under 20 --
        # for mat_g1_na_q2_4 (competency ceiling is only 20 to begin with),
        # that made the *default* scalar (0.5) miss the branch entirely,
        # so a node whose whole competency IS expanded-form decomposition
        # silently rendered plain, undecomposed facts most of the time
        # (blind review, post task_type-binding: still "1+2=___" at seed 45).
        # "Adding numbers by expressing addends as tens and ones"
        # (mat_g1_na_q2_4, mat_g2_na_q1_8) -- "strategy" was a declared
        # VARIANTS_BY_DNA option that was never implemented, so every
        # sample silently fell through to a bare, undecomposed sum
        # regardless of which strategy was requested.
        from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
        lo = 10
        # Capping hi at 99 meant a and b could never exceed 2 digits even
        # when max_result's own ceiling was far higher (mat_g2_na_q1_8:
        # "sums up to 1000") -- every render stayed tens-and-ones no matter
        # the difficulty scalar, so the packet's max-difficulty seeds (which
        # pin max_result near the true ceiling) topped out at ~151, nowhere
        # near demonstrating the competency's own stated 1000 ceiling
        # (blind review: scale_appropriateness FAIL). Uncapped (bar the
        # overall max_result-1 ceiling) now lets a/b run into 3 digits,
        # exercised by the hundreds decomposition added below.
        hi = max(lo + 1, max_result - 1)
        if hi <= 200:
            candidates = [(x, y) for x in range(lo, hi + 1) for y in range(1, hi + 1) if x + y <= max_result]
        else:
            # Full O(hi^2) enumeration is fine up to a few hundred, but a
            # 1000-ceiling node's hi can approach 999 -- ~1M pairs per call
            # is wasted work when rejection sampling reaches the same
            # windowed distribution for a fraction of the cost (same
            # pattern as this file's own task_type="estimate" branch above).
            candidates = []
            attempts = 0
            seen_pairs = set()
            while len(candidates) < 500 and attempts < 5000:
                attempts += 1
                x = rng.randint(lo, hi)
                y = rng.randint(1, hi)
                if x + y <= max_result and (x, y) not in seen_pairs:
                    seen_pairs.add((x, y))
                    candidates.append((x, y))
        if not candidates:
            candidates = [(lo, 1)]
        if "regrouping" in profile:
            # This branch returns before the default path's own regrouping
            # filter (further down) ever runs, so a requested regrouping
            # level was silently ignored here -- caught by the matrix
            # validator's exhaustive discrete-integrity sweep once task_type
            # was registry-bound to expanded_form for mat_g1_na_q2_4/
            # mat_g2_na_q1_8 (§1E: "does not reflect discrete option
            # 'one_place'"). Same feasibility contract as the default path:
            # raise rather than silently substitute a pair that doesn't
            # satisfy what was explicitly requested.
            reg_level = profile.get("regrouping", "none")
            if reg_level is False:
                reg_level = "none"
            elif reg_level is True:
                reg_level = "ones"
            reg_candidates = [(x, y) for x, y in candidates if _satisfies_regrouping(x, y, reg_level)]
            if not reg_candidates:
                raise RuntimeError(
                    f"generate_params (addition, task_type=expanded_form): regrouping "
                    f"level '{reg_level}' has no satisfying pair within max_result="
                    f"{max_result} (grade={grade}, seed={seed})."
                )
            candidates = reg_candidates
        a_val, b_val = generate_pair_by_window(candidates, num_diff_scalar, d=5, rng=rng)
        a_hundreds, a_rem = divmod(a_val, 100)
        a_tens, a_ones = divmod(a_rem, 10)
        b_hundreds, b_rem = divmod(b_val, 100)
        b_tens, b_ones = divmod(b_rem, 10)
        return {
            "a": a_val, "b": b_val, "result": a_val + b_val,
            "a_tens": a_tens, "a_ones": a_ones, "b_tens": b_tens, "b_ones": b_ones,
            "a_hundreds": a_hundreds, "b_hundreds": b_hundreds,
            "task_type": "expanded_form",
            "blank_target": "result",
            "context": "pure",
            "structure": "result_unknown",
            "max_sum": max_result,
            "strategy": "expanded_form",
            "question": (
                f"{decompose_to_places(a_val)} {decompose_to_places(b_val)} "
                f"Add the place values, then find the total: what is {a_val} + {b_val}?"
            ),
        }

    if task_type == "counting_up":
        # Explicit start-and-count narration (mat_g1_na_q1_7), distinct
        # from putting-together -- "spine" was a declared VARIANTS_BY_DNA
        # option that was never implemented, so every sample rendered a
        # static sum regardless of which spine was requested.
        from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
        # "Illustrate addition of 2-digit and 1-digit numbers as 'counting
        # up'..." (mat_g2_na_q1_7) names a specific operand SHAPE, not just
        # a sum ceiling -- drawing both operands freely up to max_result
        # let roughly half the samples use two 2-digit numbers (e.g. "11 +
        # 10", some even summing to 3 digits like "93 + 13 = 106"),
        # violating the competency's own wording (blind review, most
        # severe finding: "8/16 samples violate the '2-digit and 1-digit'
        # operand rule"). registry.py binds operand_digits=(big,small)
        # when the competency names an explicit digit-count pair.
        operand_digits = profile.get("operand_digits")
        candidates = []
        attempts = 0
        if operand_digits:
            big_digits, small_digits = (int(x) for x in str(operand_digits).split("_"))
            big_lo, big_hi = 10 ** (big_digits - 1), min(max_result - 1, (10 ** big_digits) - 1)
            small_lo, small_hi = 10 ** (small_digits - 1) if small_digits > 1 else 1, (10 ** small_digits) - 1
            while len(candidates) < 500 and attempts < 5000:
                attempts += 1
                big_val = rng.randint(big_lo, max(big_lo, big_hi))
                small_val = rng.randint(small_lo, small_hi)
                if big_val + small_val > max_result:
                    continue
                # Always start at the larger-digit operand when counting up
                # on a number line (e.g. "Start at 32. Count up 2 more.").
                pair = (big_val, small_val)
                candidates.append(pair)
            if not candidates:
                raise RuntimeError(
                    f"generate_params (addition, task_type=counting_up): operand_digits="
                    f"{operand_digits} has no satisfying pair within max_result={max_result} "
                    f"(grade={grade}, seed={seed})."
                )
        else:
            while len(candidates) < 500 and attempts < 5000:
                attempts += 1
                start = rng.randint(1, max(1, max_result - 1))
                count_by = rng.randint(1, max(1, max_result - start))
                pair = (max(start, count_by), min(start, count_by))
                candidates.append(pair)
        if "regrouping" in profile:
            # Same "this early-return branch skips the default path's own
            # regrouping filter" defect as expanded_form's identical fix
            # above -- once task_type=counting_up was registry-bound
            # (mat_g2_na_q1_7), §1C's exhaustive discrete-integrity sweep
            # caught it directly ("does not reflect discrete option
            # 'none'": a=18, b=7, ones digits 8+7=15 carries).
            reg_level = profile.get("regrouping", "none")
            if reg_level is False:
                reg_level = "none"
            elif reg_level is True:
                reg_level = "ones"
            reg_candidates = [(x, y) for x, y in candidates if _satisfies_regrouping(x, y, reg_level)]
            if not reg_candidates:
                raise RuntimeError(
                    f"generate_params (addition, task_type=counting_up): regrouping "
                    f"level '{reg_level}' has no satisfying pair within max_result="
                    f"{max_result} (grade={grade}, seed={seed})."
                )
            candidates = reg_candidates
        if not candidates:
            candidates = [(1, 1)]
        start, count_by = generate_pair_by_window(candidates, num_diff_scalar, d=5, rng=rng)
        return {
            "a": start, "b": count_by, "result": start + count_by,
            "task_type": "counting_up",
            "blank_target": "result",
            "context": "pure",
            "structure": "result_unknown",
            "max_sum": max_result,
            "strategy": "standard",
            "question": f"Start at {start}. Count up {count_by} more. What number do you land on?",
        }

    if task_type == "putting_together":
        candidates = []
        for a_cand in range(1, max_result):
            for b_cand in range(1, max_result - a_cand + 1):
                candidates.append((a_cand, b_cand))
        if "regrouping" in profile:
            reg_level = profile.get("regrouping", "none")
            if reg_level is False:
                reg_level = "none"
            elif reg_level is True:
                reg_level = "ones"
            reg_candidates = [(x, y) for x, y in candidates if _satisfies_regrouping(x, y, reg_level)]
            if not reg_candidates:
                raise RuntimeError(
                    f"generate_params (addition, task_type=putting_together): regrouping "
                    f"level '{reg_level}' has no satisfying pair within max_result="
                    f"{max_result} (grade={grade}, seed={seed})."
                )
            candidates = reg_candidates
        if not candidates:
            candidates = [(1, 1)]
        from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
        a_val, b_val = generate_pair_by_window(candidates, num_diff_scalar, d=5, rng=rng)
        a_phrase = f"{a_val} item" if a_val == 1 else f"{a_val} items"
        b_phrase = f"{b_val} item" if b_val == 1 else f"{b_val} items"
        return {
            "a": a_val, "b": b_val, "result": a_val + b_val,
            "task_type": "putting_together",
            "blank_target": "result",
            "context": "pure",
            "structure": "result_unknown",
            "max_sum": max_result,
            "strategy": "putting_together",
            "question": f"One group has {a_phrase} and another group has {b_phrase}. If you put them together, how many items are there in all?",
        }

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
        # est_min=10 when max_result >= 20: below 10, "round to the nearest ten"
        # is a no-op that produces degenerate 1-digit addends. For scalar sweeps
        # with tiny max_result, fall back to 1.
        est_min = 10 if max_result >= 20 else 1
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
    min_a = int(profile.get("min_a", 0))
    if grade >= 3 and max_result >= 100:
        min_a = max(min_a, 10)
    if grade >= 4 and max_result >= 1000:
        min_a = max(min_a, 100)
        
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
    candidates_b = list(range(0, a_hi + 1))

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
