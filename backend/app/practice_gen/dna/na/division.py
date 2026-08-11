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
    # "...by A 1-DIGIT number..." (mat_g3_na_q4_5): the bare default
    # [2,3,4,5,10] includes 10, a 2-digit divisor, directly outside this
    # competency's own stated scope.
    "one_digit_2_9": [2, 3, 4, 5, 6, 7, 8, 9],
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

    from backend.app.practice_gen.dna.base import extract_discrete_level, extract_continuous_scalar

    # Quotient bound: the per-grade `_PARAM_BOUNDS[grade]["q_max"]`
    # already aligns with the LCs' operand-bound language (g2: 50,
    # g3: 100, bounded by table-level). The `max_quotient` axis was
    # removed from the catalog on 2026-07-01 because no MATATAG K-3
    # LC specifies a result ceiling for division — see
    # axes_catalog.py header.
    q_max = bounds["q_max"]
    q_min = 0

    # "Divide numbers using the 6, 7, 8, and 9 multiplication tables" (and the
    # equivalent grade-2 2/3/4/5/10-table competencies) is a table-facts
    # competency: the quotient must itself be a single-digit table number, the
    # same restriction multiplication.py already applies to its multiplier
    # when `table` is bound (`number_type="single_digit"`, 1-9). Without this,
    # q_max stayed at the grade default (g3: 99) even when a table was
    # requested, so mat_g3_na_q4_1 served quotients like 15, 30, 80 that are
    # not table facts, with dividends (b * q, up to 9*99) that had nothing to
    # do with the named tables. `profile.get("table")` is None for nodes that
    # never bind a table (the general 2-to-3-digit-by-1-digit competencies),
    # so this narrows only the table-restricted nodes.
    if profile.get("table") is not None:
        q_max = min(q_max, 9)
        q_min = 1

    rem_level    = extract_discrete_level(profile, "remainder", ["none", "with_remainder"], "none")
    table_level  = extract_discrete_level(profile, "table", ["2_3_4_5_10", "6_7_8_9"], "2_3_4_5_10")
    structure    = extract_discrete_level(profile, "structure", ["result_unknown", "divisor_unknown"], "result_unknown")
    if structure == "divisor_or_dividend_unknown":
        # "Find the missing number in a ... sentence" (mat_g3_na_q4_2/
        # mat_g2_na_q3_7): the missing number can be in ANY position --
        # divisor_unknown alone never produces a missing-DIVIDEND item
        # (e.g. "__ ÷ 8 = 9"), which this DNA has no structure value for
        # at all (blind review: "no sample shows the 'dividend-missing'
        # blank position"). Alternate between the two.
        structure = rng.choice(["divisor_unknown", "dividend_unknown"])
    context      = extract_discrete_level(profile, "context", ["pure", "word_problem"], "pure")
    num_diff_scalar = extract_continuous_scalar(profile, "number_difficulty", extract_continuous_scalar(profile, "difficulty_scalar", 0.5))
    task_type    = profile.get("task_type")
    if task_type == "repeated_subtraction_or_default":
        # registry.py sentinel for mat_g2_na_q3_5's "...equal sharing or
        # formation of equal groups of objects, and repeated subtraction"
        # -- repeated subtraction is one of three named models, not the
        # only one, so mix it with the DNA's normal rendering rather than
        # replacing it outright.
        task_type = rng.choice(["repeated_subtraction", None, None])

    if task_type == "estimate":
        # "Estimate the quotient of 2- to 3-digit numbers divided by 1- to
        # 2-digit numbers, using multiples of 10 or 100 as appropriate"
        # (mat_g3_na_q4_4): round the DIVIDEND to the nearest 10 (if it is
        # 2-digit) or nearest 100 (if 3-digit) -- "as appropriate" maps
        # directly to the dividend's own magnitude, matching
        # addition/subtraction's front-end-rounding convention. The
        # divisor (1- to 2-digit) is left unrounded: rounding a small
        # divisor to the nearest 10 can hit 0 (divide-by-zero) and real
        # elementary quotient-estimation technique rounds the larger
        # number, not the small one. The co-mapped `rounding` DNA rounds
        # ONE number in isolation with no division step attached at all,
        # so it cannot express this competency regardless of which node
        # maps to it (see registry.py's "estimate" text match). The DNA's
        # own answer_formula "a // b" (floor division, remainder dropped)
        # governs the served answer, exactly as it does for the exact
        # (non-estimate) path -- an estimate is not expected to divide
        # evenly.
        from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
        candidates = []
        attempts = 0
        while len(candidates) < 500 and attempts < 5000:
            attempts += 1
            x = rng.randint(10, 999)
            y = rng.randint(2, 99)
            candidates.append((x, y))
        if not candidates:
            raise RuntimeError(
                f"generate_params (division): no valid estimate pair for "
                f"grade={grade}, profile={difficulty_profile}."
            )

        def _round_half_up(n: int, precision: int) -> int:
            remainder = n % precision
            if remainder >= precision / 2:
                return n - remainder + precision
            return n - remainder

        # A dividend that already sits on its own rounding boundary (e.g.
        # 300, already a multiple of 100) rounds to itself, so the served
        # "estimate" is identical to the exact-division answer -- the
        # divisor is deliberately never rounded (see above), so this is the
        # ONLY source of degeneracy here, and it's the worst-affected of the
        # four estimate DNAs (~16% of samples, since a 2-digit dividend need
        # only be a multiple of 10 to collide). Same thin-don't-exclude
        # convention as addition/subtraction/multiplication's identical fix.
        def _is_degenerate_estimate(pair: tuple) -> bool:
            x, _y = pair
            rt = 10 if x < 100 else 100
            return _round_half_up(x, rt) == x

        _meaningful = [p for p in candidates if not _is_degenerate_estimate(p)]
        _degenerate = [p for p in candidates if _is_degenerate_estimate(p)]
        if _meaningful and _degenerate:
            cap = max(1, len(_meaningful) // 10)
            candidates = _meaningful + _degenerate[:cap]
        elif _meaningful:
            candidates = _meaningful

        real_a, real_b = generate_pair_by_window(candidates, num_diff_scalar, d=5, rng=rng)

        round_to = 10 if real_a < 100 else 100
        rounded_a = max(round_to, _round_half_up(real_a, round_to))
        # Leaving a 2-digit divisor completely unrounded while the dividend
        # rounds to the nearest 10/100 can swing the quotient far from the
        # true value -- e.g. real 150÷16=9.375 rounded only the dividend to
        # 200, then floor-divided by the untouched 16 to give "≈12", a 28%
        # error from a technique meant to produce a plausible ballpark
        # (blind review of mat_g3_na_q4_4: "no standard tens/hundreds
        # rounding path reaches 12"). Real "compatible numbers" estimation
        # rounds BOTH operands -- rounding a 2-digit divisor to the nearest
        # 10 too (a 1-digit divisor is already as simple as it gets, so
        # left alone) keeps the estimate proportionally honest: the same
        # example now rounds to 200÷20=10, much closer to 9.375.
        rounded_b = _round_half_up(real_b, 10) if real_b >= 10 else real_b
        rounded_b = max(10, rounded_b) if real_b >= 10 else rounded_b

        # An "estimate" is the served value itself, not a quotient+
        # remainder pair -- flooring rounded_a/rounded_b (a // b) silently
        # discards however close the true rounded ratio sits to the NEXT
        # whole number, which can be the majority of it (blind review of
        # mat_g3_na_q4_4 seed 601: rounds to 300÷80=3.75, floor-served as
        # "3" even though 3.75 is closer to 4 -- a worse estimate than the
        # rounding step that produced it). Round the quotient itself
        # half-up instead, matching this DNA's own _round_half_up
        # convention rather than Python's implicit floor division.
        est_q, est_r = divmod(rounded_a, rounded_b)
        if est_r * 2 >= rounded_b:
            est_q += 1

        return {
            "a": rounded_a,
            "b": rounded_b,
            "result": est_q,
            "remainder": rounded_a % rounded_b,
            "real_a": real_a,
            "real_b": real_b,
            "task_type": "estimate",
            "blank_target": "result",
            "context": "pure",
            "structure": "result_unknown",
        }

    if task_type == "even_odd":
        # "Distinguish even and odd numbers using division by 2"
        # (mat_g2_na_q3_8) is a classification skill, not a quotient-finding
        # one -- nothing in this DNA produced it before (blind review: 0 of
        # 19 samples ever classified a number as even/odd; content was
        # generic ÷2/÷3/÷10 facts and unrelated whole-number comparisons
        # from a co-mapped comparing_ordering DNA).
        n_max = max(20, q_max * bounds["b"][1])
        n = rng.randint(1, n_max)
        is_even = (n % 2 == 0)
        label = "even" if is_even else "odd"
        other = "odd" if is_even else "even"
        return {
            # Deliberately NOT "a"/"b"/"result" -- those are the exact
            # variable names step (h) of generate_context's shared
            # error-pattern distractor computation evals this DNA's
            # formulas against ("a - b", "a // b", "a % b + b", "a * b").
            # A first attempt using "a"/"b" here let those numeric
            # formulas evaluate successfully and get appended to
            # ctx.distractors alongside "odd"/"even", so true_false could
            # render a fill_value like "80" instead of the category label
            # ("82 is an 80 number"). "dividend" isn't a formula variable
            # name, so _eval_error_formula raises (safely caught) instead.
            "dividend": n, "divisor": 2,
            "task_type": "even_odd",
            "blank_target": "answer",
            "context": "pure",
            "answer": label,
            "distractors": [other],
            "question": f"Divide {n} by 2. Is {n} an even or an odd number?",
        }

    if table_level == "one_digit_mixed_or_power_of_ten":
        # "2- to 3-digit numbers by 1-digit number WITHOUT remainder,
        # 2-digit numbers by 1-digit number WITH remainder, and 2- to
        # 4-digit numbers by 10, 100, and 1000" (mat_g3_na_q4_3): three
        # genuinely different (dividend, divisor, remainder) shapes under
        # one competency, none of which the DNA's single table_level/
        # rem_level pair can express together. Built directly as one
        # combined candidate pool (rather than routed through the shared
        # rem_level-filtered loop below, which can only ever apply ONE
        # remainder policy to ONE divisor pool at a time) so a single
        # difficulty-scalar window sees all three shapes at once.
        from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
        candidate_pairs = []
        for b in range(2, 10):
            for q in range(2, 100):
                a = b * q
                if 10 <= a <= 999:
                    candidate_pairs.append((a, b))
        for b in range(2, 10):
            for q in range(1, 20):
                for r in range(1, b):
                    a = b * q + r
                    if 10 <= a <= 99:
                        candidate_pairs.append((a, b))
        for b in (10, 100, 1000):
            for q in range(1, 999):
                a = b * q
                if 10 <= a <= 9999:
                    candidate_pairs.append((a, b))
        a, b = generate_pair_by_window(candidate_pairs, num_diff_scalar, d=5, rng=rng)
        blank_target = {
            "result_unknown":   "result",
            "divisor_unknown":  "b",
            "dividend_unknown": "a",
        }.get(structure, "result")
        return {
            "a":           a,
            "b":           b,
            "result":      a // b,
            "remainder":   a % b,
            "blank_target": blank_target,
            "context":     context,
            "structure":   structure,
        }

    allowed_divisors = _table_for_level(table_level, grade)

    candidate_pairs = []
    for b in allowed_divisors:
        for q in range(q_min, q_max + 1):
            if rem_level == "none":
                a = b * q
                if _satisfies_remainder(a, b, rem_level):
                    candidate_pairs.append((a, b))
            else:
                for r in range(0 if q == 0 else 1, b):
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

    if task_type == "repeated_subtraction" and structure == "result_unknown" and a % b == 0:
        # "...modelling division as equal sharing or formation of equal
        # groups of objects, AND REPEATED SUBTRACTION" (mat_g2_na_q3_5):
        # one of three explicitly named models, but nothing in this DNA
        # ever produced it -- every sample rendered a bare "a / b" fact,
        # an array, or a sharing word problem (blind review: "repeated
        # subtraction... is modeled in zero of 18 samples"). Only applies
        # when the pair divides evenly (a % b == 0): repeated subtraction
        # as taught at this grade counts subtractions down to exactly 0,
        # not to a leftover remainder.
        result_dict["question"] = (
            f"Start with {a}. How many times can you subtract {b} in a "
            f"row before reaching 0?"
        )
        # Must be present for the formatters' own task_type checks (fmt_
        # true_false.py etc.) to detect this case at all -- it was
        # previously omitted here (unlike the even_odd/estimate/
        # zero_identity early-return branches above, which always include
        # it in their own dicts), so those checks silently never matched
        # even though "question" itself was set correctly. This also
        # naturally routes rendering through true_false only, mirroring
        # even_odd's identical, deliberate mcq/cloze exclusion (see
        # compatibility.py's FORMATTER_VARIANT_SUPPORT["division"] comment):
        # mcq/cloze/error_detect/array_grid are all scoped to task_type=
        # ["find_quotient"], so a present-but-mismatching "repeated_
        # subtraction" value correctly excludes them instead of exposing
        # this new task_type to validate_matrix's exhaustive per-node
        # sweep the way adding it to their allow-lists would.
        result_dict["task_type"] = "repeated_subtraction"

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
        if "remainder" in cumulative_vocab:
            hints.append(
                f"{quotient_label.capitalize()} is {result} remainder {remainder} "
                f"(written as {result} R{remainder})."
            )
        else:
            hints.append(
                f"{quotient_label.capitalize()} is {result} with {remainder} left over."
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
