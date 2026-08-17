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
    # "2_3_4_5_10" is this DNA's own bare default (profile.get("table",
    # "2_3_4_5_10")), used whenever nothing binds "table" at all -- e.g.
    # mat_g2_na_q3_1's repeated-addition intro, which relies on a b=1 pair
    # being reachable to satisfy a max_product floor as low as 1 (see the
    # "NOTE on task_type == repeated_addition" comment below). 0/1 stay in
    # this set for that reason.
    "2_3_4_5_10": [0, 1, 2, 3, 4, 5, 10],
    # "2_3_4_5_10_named" is registry.py's binding for a competency whose
    # text explicitly names "the 2, 3, 4, 5, and 10 multiplication tables"
    # (mat_g2_na_q3_2/_3) -- unlike the bare default above, no node relying
    # on this sentinel ever needs a b=1/b=0 pair (registry.py floors those
    # nodes' max_product well above what a table<2 fact could reach), and
    # 0/1 aren't among the named tables anyway. Including them let those
    # two facts crowd out genuine 2-3-4-5-10 content the same way "6_7_8_9"
    # did (verified live: table 10 appeared 0/499 times, table 2 dominated
    # ~50%, before this split).
    "2_3_4_5_10_named": [2, 3, 4, 5, 10],
    # "6_7_8_9" is only ever grade-3-bound directly from a competency whose
    # text names exactly "the 6, 7, 8, and 9 multiplication tables"
    # (mat_g3_na_q3_0/_1) -- unlike "2_3_4_5_10" it's never the DNA's own
    # unbound default, so there is no low-difficulty-scalar node relying on
    # a b=1 pair to reach a tiny max_product floor here. 0 and 1 are not
    # among the named tables, and including them let those two facts crowd
    # out genuine 6-9 content (blind review of mat_g3_na_q3_0: "~31% of
    # samples...don't touch 6-9 at all"; 7's table never appeared once in
    # 16 samples). division.py's identical "6_7_8_9" entry already excludes
    # them -- this brings multiplication.py in line with that precedent.
    # Dedicated 0/1 (zero/identity property) content now has its own
    # task_type branch below instead of leaking in incidentally here.
    "6_7_8_9":    [6, 7, 8, 9],
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_PRODUCT  = VocabGated(requires_vocab="product",  preferred="the product",  fallback="the answer")
VOCAB_FACTOR   = VocabGated(requires_vocab="factor",   preferred="factor",       fallback="number")
VOCAB_MULTIPLY = VocabGated(requires_vocab="multiply", preferred="multiply",     fallback="find the total of equal groups")
VOCAB_TIMES    = VocabGated(requires_vocab="times",    preferred="times",        fallback="groups of")


# ─── constraint predicates ────────────────────────────────────────────────────

def _table_for_level(level: str, grade: int) -> List[int]:
    """Return the allowed factor-b values for the given table axis level.

    A recognized `level` (see _TABLE_SETS) always wins, regardless of
    grade -- this used to hard-override to [0,1,2,3,4,5,10] for any grade
    <=2 request, which ignored "2_3_4_5_10_named" (see that entry's
    comment) and defeated the whole point of the named/bare-default split.
    Only a genuinely unrecognized level falls back to the grade-2 default.
    """
    if level in _TABLE_SETS:
        return _TABLE_SETS[level]
    return [0, 1, 2, 3, 4, 5, 10]


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
    # validate_matrix's §1C exhaustive sweep has no per-node scoping for
    # VARIANTS_BY_DNA["multiplication"]["number_type"] -- it requests
    # number_type="multi_digit" against every multiplication node,
    # including these two named-single-digit-tables sentinels. A "6, 7, 8,
    # and 9 multiplication tables" competency has no multi-digit
    # multiplicand in its own scope at all (a two-digit-by-one-digit fact
    # belongs to mat_g3_na_q3_2's own, separate, unbound-table competency),
    # and forcing a>=10 against a table floor of 6-10 pushes the minimum
    # possible product (60-100) straight past this node's own max_product
    # ceiling at ordinary scalars, emptying the candidate pool outright
    # (§1C crash: "no valid pair found", array_grid_set/read, seed 43+).
    # single_digit is what the competency actually names, so it wins
    # regardless of what the sweep asks for -- this isn't a silent
    # fallback, it's enforcing the curriculum's own explicit scope.
    if table_level in ("6_7_8_9", "2_3_4_5_10_named"):
        num_level = "single_digit"
    structure   = profile.get("structure", "result_unknown")
    context     = profile.get("context", "pure")
    task_type   = profile.get("task_type")
    if isinstance(task_type, list):
        # registry.py binds a rotation list (not a single value) for the
        # dedicated "illustrate and apply properties of multiplication"
        # node (mat_g3_na_q3_1) -- that node left task_type completely
        # unbound before, so it had no auto-vary of its own (unlike other
        # DNAs' task_type dimensions) and silently rendered the exact same
        # plain table-fact content as its sibling table-facts node
        # (blind review: competency_alignment FAIL, "text-for-text
        # identical to sibling node mat_g3_na_q3_0's plain-facts packet").
        # Orchestrator-level list resolution only fires for CALLER-supplied
        # difficulty_profile keys, not ones injected later from registry
        # bounds, so this DNA has to resolve it itself (same pattern as
        # probability_language.py's identical fix).
        task_type = rng.choice(task_type)
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    max_prod_val = profile.get("max_product")
    if max_prod_val is not None:
        max_prod_val = int(max_prod_val)
    else:
        max_prod_val = 999999 # Rely on bounds["a"]

    # registry.py sentinel for mat_g3_na_q3_2's compound competency: "2- to
    # 3-digit numbers by a 1-digit number" AND, separately, "2- to 4-digit
    # numbers by a number whose leading digit is the only non-zero digit".
    # These are two different (multiplicand, multiplier) shapes -- resolve
    # per-seed which one this render is, same pattern as fractions.py's
    # "add_subtract" -> rng.choice(["add","subtract"]). The leading-digit
    # shape's floor is 10*10=100 (smallest multi_digit multiplicand times
    # smallest leading-digit multiplier) -- §1A sweeps max_product down to
    # single digits to test the scalar contract, where that shape has no
    # feasible pair at all, so it can only be chosen when the ceiling
    # actually admits its floor.
    if table_level == "one_digit_or_leading_digit" and max_prod_val >= 20:
        family = rng.choice(["by_1d", "by_lead"]) if max_prod_val >= 100 else "by_1d"
        if family == "by_1d":
            digits = rng.choice(["2d", "3d"]) if max_prod_val >= 200 else "2d"
            if digits == "2d":
                max_b = min(9, max_prod_val // 10)
                if max_b >= 2:
                    b = rng.randint(2, max_b)
                    a = rng.randint(10, min(99, max_prod_val // b))
                else:
                    b = 2
                    a = 10
            else:  # 3d
                max_b = min(9, max_prod_val // 100)
                if max_b >= 2:
                    b = rng.randint(2, max_b)
                    a = rng.randint(100, min(999, max_prod_val // b))
                else:
                    b = 2
                    a = 100
        else:  # by_lead
            available_digits = ["2d"]
            if max_prod_val >= 1000:
                available_digits.append("3d")
            if max_prod_val >= 10000:
                available_digits.append("4d")
            digits = rng.choice(available_digits)
            if digits == "2d":
                lead_tables = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900]
                valid_leads = [t for t in lead_tables if t * 10 <= max_prod_val]
                b = rng.choice(valid_leads) if valid_leads else 10
                a = rng.randint(10, min(99, max_prod_val // b))
            elif digits == "3d":
                lead_tables = [10, 20, 30, 40, 50, 60, 70, 80, 90]
                valid_leads = [t for t in lead_tables if t * 100 <= max_prod_val]
                b = rng.choice(valid_leads) if valid_leads else 10
                a = rng.randint(100, min(999, max_prod_val // b))
            else:  # 4d
                b = 10
                a = min(1000, max_prod_val // 10)
        
        result_dict = {
            "a": a,
            "b": b,
            "result": a * b,
            "blank_target": "result",
            "context": context,
            "structure": structure,
            "task_type": task_type,
            "groups": a,
            "n": b,
            "total": a * b,
        }
        return result_dict

    leading_digit_4digit = None
    if table_level == "one_digit_or_leading_digit":
        leading_digit_4digit = max_prod_val >= 100 and rng.choice([False, True])
        if leading_digit_4digit:
            allowed_tables = [
                10, 20, 30, 40, 50, 60, 70, 80, 90,
                100, 200, 300, 400, 500, 600, 700, 800, 900,
                1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000,
            ]
        else:
            allowed_tables = list(range(0, 10))
    else:
        allowed_tables = _table_for_level(table_level, grade)

    a_lo = bounds["a"][0]
    if num_level == "multi_digit":
        a_lo = max(10, a_lo)
    if leading_digit_4digit:
        a_hi = 9999
    else:
        a_hi = 999 if num_level == "multi_digit" else max(a_lo, bounds["a"][1])

    if task_type == "zero_identity":
        other = rng.choice(allowed_tables) if allowed_tables else rng.randint(2, 9)
        is_zero = rng.choice([True, False])
        zero_first = rng.choice([True, False])
        if is_zero:
            a_val, b_val = (0, other) if zero_first else (other, 0)
            result = 0
        else:
            a_val, b_val = (1, other) if zero_first else (other, 1)
            result = other
        return {
            "a": a_val, "b": b_val, "result": result,
            "task_type": "zero_identity",
            "blank_target": "result",
            "context": "pure",
            "structure": "result_unknown",
            "groups": a_val, "n": b_val, "total": result,
        }

    if task_type in ("commutative", "associative", "distributive"):
        small_max = max(2, min(9, int(max_prod_val ** 0.5) if max_prod_val < 999999 else 9))
        table_pool = [t for t in allowed_tables if t >= 2] or list(range(2, small_max + 1))
        b_val = rng.choice(table_pool)
        a_val = rng.randint(2, small_max)
        if task_type == "commutative" and a_val == b_val:
            a_val = a_val - 1 if a_val > 2 else a_val + 1
        c_val = None
        if task_type == "commutative":
            question = f"Is {a_val} × {b_val} the same as {b_val} × {a_val}?"
            missing_val = b_val
        elif task_type == "associative":
            c_val = rng.randint(2, small_max)
            question = f"Is ({a_val} × {b_val}) × {c_val} the same as {a_val} × ({b_val} × {c_val})?"
            missing_val = b_val
        else:  # distributive
            c_val = rng.randint(2, small_max)
            question = (
                f"Is {a_val} × ({b_val} + {c_val}) the same as "
                f"({a_val} × {b_val}) + ({a_val} × {c_val})?"
            )
            missing_val = c_val
        return {
            "a": a_val, "b": b_val, "c": c_val,
            "result": missing_val,
            "task_type": task_type,
            "blank_target": "answer",
            "context": "pure",
            "answer": True,
            "distractors": [False],
            "question": question,
            "missing_val": missing_val,
            "groups": a_val, "n": b_val, "total": a_val * b_val,
        }

    if task_type == "two_step":
        g_val = rng.randint(2, 6)
        n_val = rng.randint(2, 8)
        a_val = g_val * n_val
        b_val = rng.choice([2, 3, 4, 5, 10, 15, 20]) if max_prod_val >= 200 else rng.randint(2, 5)
        # Cap to max_product
        if a_val * b_val > max_prod_val:
            b_val = max(2, max_prod_val // a_val)
        ans = a_val * b_val

        if context == "pure":
            return {
                "a": a_val,
                "b": b_val,
                "g": g_val,
                "n_val": n_val,
                "result": ans,
                "blank_target": "result",
                "context": "pure",
                "structure": "result_unknown",
                "task_type": "two_step",
                "question": f"What is ({g_val} × {n_val}) × {b_val}?",
                "groups": a_val,
                "n": b_val,
                "total": ans,
            }

        step_case = rng.choice(["money_items", "money_packs", "objects_shelves", "objects_trays"])
        actors = ["Maria", "Juan", "Carlo", "Riza", "Lito", "Grace", "Bianca", "Rico"]
        actor = rng.choice(actors)

        if step_case == "money_items":
            items_map = {
                "notebooks": "notebook",
                "pens": "pen",
                "pencils": "pencil",
                "markers": "marker",
                "erasers": "eraser",
                "apples": "apple",
                "mangoes": "mango",
            }
            item_plur = rng.choice(list(items_map.keys()))
            item_sing = items_map[item_plur]
            question = (
                f"{actor} bought {g_val} packs with {n_val} {item_plur} in each pack. "
                f"Each {item_sing} costs ₱{b_val}. "
                f"How much did {actor} pay in all?"
            )
        elif step_case == "money_packs":
            items = ["biscuits", "crayons", "stickers", "envelopes", "ribbons"]
            item = rng.choice(items)
            question = (
                f"{actor} bought {g_val} boxes of {item}. "
                f"Each box contains {n_val} packs, and each pack costs ₱{b_val}. "
                f"How much did {actor} spend in all?"
            )
        elif step_case == "objects_shelves":
            items = ["books", "jars", "cans", "bottles", "toy cars", "figurines"]
            item = rng.choice(items)
            question = (
                f"{actor} arranged {g_val} shelves with {n_val} boxes on each shelf. "
                f"Each box has {b_val} {item}. "
                f"How many {item} are there in all?"
            )
        else:  # objects_trays
            items = ["eggs", "muffins", "cupcakes", "pandesal", "cookies"]
            item = rng.choice(items)
            question = (
                f"{actor} prepared {g_val} large trays. "
                f"Each tray holds {n_val} plates, and each plate has {b_val} {item}. "
                f"How many {item} are there altogether?"
            )

        return {
            "a": a_val,
            "b": b_val,
            "g": g_val,
            "n_val": n_val,
            "result": ans,
            "blank_target": "result",
            "context": "word_problem",
            "structure": "result_unknown",
            "task_type": "two_step",
            "question": question,
            "groups": a_val,
            "n": b_val,
            "total": ans,
        }

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

    # b in (0, 1) (the identity/zero-property factors) has NO product-ceiling
    # constraint narrowing its `a` range the way b>=2 does (see the loop
    # above), so its candidate pool is proportionally far larger than any
    # genuine table fact's -- observed at 60-90% of sampled items across
    # every multiplication node in blind review, even for "6, 7, 8, 9
    # tables" competencies where 0/1 aren't the named tables at all. Same
    # ~10%-of-meaningful-pool thinning convention already applied to
    # addition.py's 0-operand pairs and this DNA's own estimate-degenerate
    # case above.
    _meaningful_pairs = [p for p in candidate_pairs if p[0] not in (0, 1) and p[1] not in (0, 1)]
    _degenerate_pairs = [p for p in candidate_pairs if p[0] in (0, 1) or p[1] in (0, 1)]
    if _meaningful_pairs and _degenerate_pairs:
        cap = max(1, len(_meaningful_pairs) // 10)
        candidate_pairs = _meaningful_pairs + _degenerate_pairs[:cap]
    elif _meaningful_pairs:
        candidate_pairs = _meaningful_pairs

    from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
    # The "2_3_4_5_10_named" pool is small and coarse-scored compared to
    # the generic pool this windowing was tuned for -- d=5's narrower
    # window (width 0.2) can miss 1-2 of the named tables entirely at the
    # default scalar even though the pool contains every table (verified
    # live: at scalar=0.5 the d=5 window held only tables {2,3,10}; d=3's
    # wider window (0.333) captured all five). "6_7_8_9" doesn't need this
    # widening (its 4-table pool already gets full coverage at d=5) and
    # widening it too measurably hurt mat_g3_na_q3_1's max-product reach at
    # scalar 1.0 (§1A-reach: only 5/5 task_type rotation slots are
    # find_product, so few of a small sample land on it, and d=3's wider
    # top-of-range window pulls in more sub-ceiling pairs alongside the
    # true max) -- so this widening is scoped to the one table set that
    # actually needs it.
    pair_d = 3 if table_level == "2_3_4_5_10_named" else 5
    a, b = generate_pair_by_window(candidate_pairs, num_diff_scalar, d=pair_d, rng=rng)

    blank_target = {
        "result_unknown": "result",
        "factor_unknown": "b",
    }.get(structure, "result")

    group_form = None
    plural_name = None
    if task_type == "equal_groups":
        _number_plurals = {
            1: "ones",
            2: "twos",
            3: "threes",
            4: "fours",
            5: "fives",
            6: "sixes",
            7: "sevens",
            8: "eights",
            9: "nines",
            10: "tens",
        }
    if context == "word_problem":
        if b <= 0:
            b = rng.randint(2, 10)
        if a <= 0:
            a = rng.randint(2, 10)

    result_dict = {
        "a": a,
        "b": b,
        "result": a * b,
        "blank_target": blank_target,
        "context": context,
        "structure": structure,
        "task_type": task_type,
        "group_form": group_form,
        "plural_name": plural_name,
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

    if values.get("task_type") == "two_step":
        g = values.get("g", 2)
        n = values.get("n_val", a // g if g else 2)
        hints.append(f"Step 1: First find the total items in the groups: {g} × {n} = {a}.")
        hints.append(f"Step 2: Multiply the total items by {b}: {a} × {b} = {result}.")
        return hints

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
