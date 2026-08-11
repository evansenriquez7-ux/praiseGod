"""
DNA: Fractions (Number & Algebra)

Refactored from:
  - matatag_skeletons.py  (fractions generator + fr_* traps)
  - matatag_dimensions.py (FRACTIONS_DIMENSIONS)

Covers MATATAG grades 1–3 fractions competencies:
  G1 — halves and fourths only; area model identification
  G2 — unit fractions and similar proper fractions (denominators 2–8)
  G3 — fractions ≥ 1 (improper / mixed numbers); add/subtract similar fractions
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


# ─── grade-gated denominator pools ───────────────────────────────────────────
_DENOM_POOLS: Dict[str, List[int]] = {
    "g1": [2, 4],
    "g2": [2, 3, 4, 5, 6, 8],
    "g3": [2, 3, 4, 5, 6, 8, 10],
}


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"denom_pool": [2, 4],          "max_numerator": 1,  "allow_mixed": False, "allow_ops": False},
    "g2": {"denom_pool": [2, 3, 4, 5, 6, 8], "max_numerator": 7, "allow_mixed": False, "allow_ops": False},
    "g3": {"denom_pool": [2, 3, 4, 5, 6, 8, 10], "max_numerator": 9, "allow_mixed": True,  "allow_ops": True},
}


_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="f'{denominator}/{numerator}'",
        required_concept="fractions",
        label="fr_swap_nd",
        description="Swapped numerator and denominator.",
    ),
    ErrorPattern(
        formula="f'{a_num + b_num}/{a_den + b_den}'",
        required_concept="fractions",
        label="fr_add_both",
        description="Added numerators AND denominators separately.",
    ),
    ErrorPattern(
        formula="f'{(a_num if a_num > b_num else b_num)}/{a_den}'",
        required_concept="fractions",
        label="fr_big_num",
        description="Compared only numerators; chose the larger numerator as the bigger fraction.",
    ),
    ErrorPattern(
        formula="f'1/{(a_den if a_den < b_den else b_den)}'",
        required_concept="fractions",
        label="fr_big_den",
        description="Assumed a larger denominator means a larger fraction.",
    ),
    ErrorPattern(
        formula="f'{a_num + b_num}/{a_den + 1}'",
        required_concept="fractions",
        label="fr_not_simp",
        description="Added numerators correctly but used wrong denominator (off by one).",
    ),
    ErrorPattern(
        formula="f'{numerator + denominator}/{denominator}'",
        required_concept="fractions",
        label="fr_unit_rev",
        description="Confused unit fraction ordering; added numerator and denominator instead of computing correctly.",
    ),
    ErrorPattern(
        formula="f'{numerator - 1}/{denominator}'",
        required_concept="mixed_number",
        label="fr_imp_mix",
        description="Wrong improper-to-mixed conversion; subtracted 1 from numerator.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_NUMERATOR   = VocabGated(requires_vocab="numerator",        preferred="numerator",        fallback="top number")
VOCAB_DENOMINATOR = VocabGated(requires_vocab="denominator",      preferred="denominator",      fallback="bottom number")
VOCAB_FRACTION    = VocabGated(requires_vocab="fraction",         preferred="fraction",         fallback="part of a whole")
VOCAB_UNIT_FRAC   = VocabGated(requires_vocab="unit fraction",    preferred="unit fraction",    fallback="fraction with 1 on top")
VOCAB_MIXED       = VocabGated(requires_vocab="mixed number",     preferred="mixed number",     fallback="whole number and a fraction part")
VOCAB_IMPROPER    = VocabGated(requires_vocab="improper fraction",preferred="improper fraction",fallback="fraction where the top number is bigger than the bottom")


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fraction_str(num: int, den: int) -> str:
    return f"{num}/{den}"


_ORDINAL_WORDS = {
    2: "half", 3: "third", 4: "fourth", 5: "fifth",
    6: "sixth", 7: "seventh", 8: "eighth", 10: "tenth",
}
_CARDINAL_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}


def _fraction_words(num: int, den: int) -> str:
    """Spell out a fraction in words, e.g. (3, 4) -> 'three fourths'."""
    ordinal = _ORDINAL_WORDS.get(den, f"{den}th")
    if num != 1:
        ordinal += "s"
    return f"{_CARDINAL_WORDS.get(num, str(num))} {ordinal}"


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Rejection-sample a fraction (or pair of fractions) matching difficulty_profile.

    Returns:
        numerator   : int
        denominator : int
        fraction_str: str          e.g. "3/4"
        model_type  : str          "area_model" | "set_model" | "number_line"
        # For add/subtract operations, also:
        a_num, a_den, b_num, b_den, result_num, result_den: int
        operation   : str
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key      = f"g{max(1, min(grade, 3))}"
    bounds     = _PARAM_BOUNDS[g_key]
    denom_pool = bounds["denom_pool"]
    allow_mixed = bounds["allow_mixed"]
    allow_ops   = bounds["allow_ops"]

    frac_type  = profile.get("fraction_type",  "unit_fraction")
    model_type = profile.get("fraction_model", "area_model")
    operation  = profile.get("operation",      "identify_name")
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    # Grade guard: demote unsupported axes
    if not allow_mixed and frac_type in ("mixed", "improper", "mixed_number"):
        frac_type = "proper"
    if not allow_ops and operation in ("add", "subtract", "add_subtract"):
        operation = "compare"

    if operation == "add_subtract":
        # registry.py binds the combined sentinel "add_subtract" for "Add
        # AND subtract similar fractions" (mat_g3_na_q4_7), but every
        # branch below only ever checks `operation == "subtract"` --
        # "add_subtract" never equals that, so it always fell through to
        # the addition branch and "subtract" never appeared in this DNA's
        # output at all (blind review: "every sample that names an
        # operation uses '+' ... 'subtract' is never enacted"). Resolve to
        # one concrete operation per call, same pattern as multiplication.py/
        # probability_language.py's identical list-resolution fix.
        operation = rng.choice(["add", "subtract"])

    if operation == "order":
        # "Order unit/similar fractions from smallest to largest, and vice
        # versa" (mat_g2_na_q4_2/mat_g2_na_q4_5) had no operation for this
        # at all -- operation only ever resolved to identify_name/compare/
        # add_subtract, so the co-mapped comparing_ordering DNA (a bare
        # whole-number ordering skill) filled the gap with off-topic
        # content instead (blind review: "ordering unit fractions...
        # never appears anywhere in the 18 samples").
        n_items = 4
        if frac_type in ("unit_fraction", "unit"):
            # Unit fractions: numerator always 1, distinct denominators.
            chosen_dens = rng.sample(denom_pool, min(n_items, len(denom_pool)))
            pairs = [(1, d) for d in chosen_dens]
        else:
            # Similar (same-denominator) fractions: distinct numerators at
            # one denominator. A denominator needs at least 3 valid
            # numerators (1..den-1) to make a meaningful ordering set --
            # small denominators like 2 (only numerator 1) can't.
            viable_dens = [d for d in denom_pool if d - 1 >= 3] or [max(denom_pool)]
            den = rng.choice(viable_dens)
            max_num = den - 1
            n_items = min(n_items, max_num)
            nums = rng.sample(range(1, den), n_items)
            pairs = [(n, den) for n in nums]

        direction = rng.choice(["ascending", "descending"])
        seq_strs = [_fraction_str(n, d) for n, d in pairs]
        return {
            "numerator":    pairs[0][0],
            "denominator":  pairs[0][1],
            "fraction_str": seq_strs[0],
            "model_type":   model_type,
            "operation":    "order",
            "sequence":     seq_strs,
            "direction":    direction,
            "blank_target": "sequence",
        }

    if operation == "count_sequence":
        # "Count halves and quarters" (mat_g1_na_q4_2) has no operation
        # for this at all -- identify_name/compare/add_subtract/order all
        # produce a single fraction or fraction PAIR, never a counting
        # SEQUENCE, so the co-mapped `counting` DNA (a bare whole-number
        # skip-counting skill with no fraction concept whatsoever) filled
        # the gap with off-topic whole-number sequences instead (blind
        # review: "10/17 samples (59%) are plain whole-number counting
        # with zero fraction content... this is active off-topic
        # substitution"). Counts by a fixed unit fraction (1/2 or 1/4,
        # chosen per the node's own denom_pool) the same way counting.py
        # counts by a fixed whole-number skip interval -- 4 visible terms,
        # asking for the 5th. Terms stay as raw "N/D" (e.g. "4/4") rather
        # than simplifying to a whole number, since the point is
        # continuing the counting PATTERN, not fraction simplification (a
        # later competency).
        # Two independent blind reviews confirmed a genuine G1 scope
        # violation here: the original fixed 5-term window (start_n in
        # 1..3, always +4 past it) made the ANSWER exceed the whole
        # (numerator > denominator) on every single seed, e.g. "1/2, 2/2,
        # 3/2, 4/2, ___? -> 5/2" -- improper fractions are explicitly a
        # later grade in this DNA's own docstring ("G3 -- fractions >= 1
        # (improper / mixed numbers)"), and a G1 "count halves/quarters"
        # competency has no basis for exceeding one whole at all. A
        # denominator of 2 or 4 only HAS 2 or 4 valid terms total (1/2..
        # 2/2, or 1/4..4/4), too few to fit the old 5-term window inside
        # one whole regardless of start point -- so the window itself has
        # to shrink to match the denominator: count from 1 up to exactly
        # the whole, with the whole itself (N/N) always the final/asked-
        # for term.
        count_denom = rng.choice([d for d in denom_pool if d in (2, 4)] or [2])
        seq_fracs = [(n, count_denom) for n in range(1, count_denom + 1)]
        visible = seq_fracs[:-1]
        next_frac = seq_fracs[-1]
        seq_strs = [_fraction_str(n, d) for n, d in visible]
        answer_str = _fraction_str(*next_frac)
        # A string answer skips the shared numeric-offset distractor
        # padding (base_generator's type-consistency guard correctly
        # skips it for non-numeric correct_answer values), so explicit
        # distractors are required here: one step too far, one step short
        # (a repeat of the last visible term), and a denominator swap
        # (a plausible "used the wrong fraction" trap).
        over_shoot = _fraction_str(next_frac[0] + 1, count_denom)
        short_fall = seq_strs[-1]
        wrong_denom = _fraction_str(next_frac[0], 2 if count_denom == 4 else 4)
        distractors = [d for d in (over_shoot, short_fall, wrong_denom) if d != answer_str]
        # "numerator"/"denominator" are set to the ANSWER (next_frac), not
        # the first visible term: the DNA's shared answer_formula
        # ("numerator / denominator") is what validate_matrix's §1E
        # answer-key-integrity check recomputes against given_values to
        # verify the served correct_answer, and count_sequence has no
        # single "given" fraction the way identify_name does -- the given
        # is a 4-term sequence, not a scalar. Anchoring numerator/denominator
        # to the answer keeps that generic recompute honest (it was
        # previously anchored to visible[0], which made every seed fail
        # answer_key_integrity: "recomputed '0.5' != served '5/2'").
        return {
            "numerator":    next_frac[0],
            "denominator":  next_frac[1],
            "fraction_str": seq_strs[0],
            "model_type":   model_type,
            "operation":    "count_sequence",
            "sequence":     seq_strs,
            "answer":       answer_str,
            "distractors":  distractors,
            "blank_target": "answer",
            "question":     f"What comes next in the pattern: {', '.join(seq_strs)}, ___?",
        }

    candidate_params = []

    for den in denom_pool:
        # Gather possibilities for num
        if frac_type in ("unit_fraction", "unit"):
            num_choices = [1]
        elif frac_type in ("similar_proper", "proper"):
            num_choices = list(range(1, den))
        else:  # mixed or improper
            num_choices = []
            for whole in range(1, 4):  # keeping max whole 3
                if den > 1:
                    # part starting at 0 (not 1) includes the num == den
                    # case at whole=1 (e.g. 4/4), i.e. a fraction "equal to
                    # one" -- mat_g3_na_q4_6 names this as one of its two
                    # required sub-cases ("equal to one AND greater than
                    # one"), and the previous part range (1, den) could
                    # only ever produce num > den (strictly greater than
                    # one), never num == den.
                    for part in range(0, den):
                        num_choices.append(whole * den + part)
                else:
                    num_choices.append(whole * den)
        
        for num in num_choices:
            if num == 0:
                continue

            frac_s = _fraction_str(num, den)

            if operation not in ("add", "subtract", "add_subtract"):
                b_num = min(den - 1, num + 1) if den > 1 else num + 1
                b_den = den
                if operation == "compare" and b_num == num:
                    if num > 1:
                        # num already sits at the top of its proper-
                        # fraction range (e.g. 3/4: den-1 == num+1 == num),
                        # so the +1-neighbor construction above degenerates
                        # to comparing a fraction to itself -- always "=",
                        # never a genuine size comparison (blind review of
                        # mat_g1_na_q4_1: "1/2 vs 1/4" never differed).
                        b_num = num - 1
                    else:
                        # num == 1 (a unit fraction, e.g. 1/2): no smaller
                        # valid numerator exists at this denominator at
                        # all, so compare against a different denominator
                        # instead. Must come from this grade's own
                        # denom_pool, not an arbitrary den+1 -- G1's pool is
                        # exactly [2, 4] (mat_g1_na_q4_1: "Compare 1/2 and
                        # 1/4"), and den+1 previously produced denominator
                        # 3, outside G1's curriculum scope entirely.
                        larger_denoms = [d for d in denom_pool if d > den]
                        b_den = min(larger_denoms) if larger_denoms else max(denom_pool)
                cmp_distractors = None
                if operation == "compare":
                    ans = "=" if (num, den) == (b_num, b_den) else (">" if num / den > b_num / b_den else "<")
                    # The comparison answer domain is exactly {">", "<", "="}
                    # -- base_generator's generic error-pattern distractor
                    # loop evaluates this DNA's fraction-VALUE formulas
                    # (fr_swap_nd etc.) against numerator/denominator
                    # regardless of operation, and since those formulas also
                    # happen to produce strings, they pass the weak
                    # str-vs-str type check and get offered as "sign"
                    # options -- e.g. "2/1" or "2/6" alongside the real sign
                    # (blind review of mat_g1_na_q4_1: MCQ options were
                    # "2/1", "1/2", ">", "2/6" for a "which sign?" question,
                    # three of which are not signs at all). Supplying the
                    # only two OTHER valid signs explicitly, combined with
                    # base_generator's shape-guard for comparison answers,
                    # keeps every offered option a genuine sign. Only 2 other
                    # signs exist, one short of MCQ's fixed 4-option
                    # requirement (validate_matrix's mcq_option_count check)
                    # -- comparing_ordering.py's identical compare_two
                    # task_type already solved this exact cardinality gap by
                    # padding with "cannot be determined", a genuinely
                    # plausible wrong answer for a student who hasn't yet
                    # learned to compare unlike fractions, not a nonsense
                    # filler; reuse that established convention rather than
                    # inventing a second one.
                    cmp_distractors = [s for s in (">", "<", "=") if s != ans] + ["cannot be determined"]
                else:
                    ans = frac_s

                # "Read and write unit/similar fractions in fraction
                # notation" (mat_g2_na_q4_1/_4) is co-mapped with a
                # "Represent and identify..." sibling (mat_g2_na_q4_0/_3)
                # that shares this exact same identify_name operation --
                # compatibility.py now routes the two to different
                # formatters (visual model-shade vs text mcq/cloze), but
                # both fall back to base_generator's SAME generic "A shape
                # is divided into..." symbolic text when no DNA-supplied
                # "question" overrides it, so the two nodes still rendered
                # byte-identical text despite using different formatters
                # (blind review: "byte-identical duplicate of q4_3's
                # packet"). A genuine notation task doesn't need a shape
                # description at all -- give the word form and ask for the
                # symbol, the actual "notation" skill this node names.
                notation_question = None
                if operation == "identify_name" and profile.get("fraction_task_mode") == "notation":
                    notation_question = f"Write {_fraction_words(num, den)} in fraction notation."

                candidate_params.append({
                    "numerator":    num,
                    "denominator":  den,
                    "fraction_str": frac_s,
                    "model_type":   model_type,
                    "operation":    operation,
                    "a_num":        num,
                    "a_den":        den,
                    "b_num":        b_num,
                    "b_den":        b_den,
                    "result":       ans,
                    **({"distractors": cmp_distractors} if cmp_distractors is not None else {}),
                    **({"question": notation_question} if notation_question else {}),
                    # Must be echoed back into the returned dict (which
                    # becomes ctx.values), not just read from `profile` --
                    # the orchestrator's FORMATTER_VARIANT_SUPPORT filter
                    # checks ctx.values.get("fraction_task_mode"), and a
                    # value that exists only in the input profile is
                    # invisible to it (the filter never sees it, so the
                    # "exclude fraction_shade/fraction_model_read from
                    # notation nodes" restriction was silently a no-op --
                    # confirmed live: those two formatters kept getting
                    # picked for mat_g2_na_q4_1/_4 and ignored the
                    # "question" override above entirely, rendering their
                    # own generic "Shade X of the shape" stem instead).
                    **({"fraction_task_mode": profile.get("fraction_task_mode")} if profile.get("fraction_task_mode") else {}),
                })
            else:
                for b_num in range(1, den):
                    if b_num == 0:
                        continue
                    
                    if operation == "subtract":
                        # For subtract, a_num must be larger than b_num to avoid negative fractions in early grades
                        if num <= b_num:
                            continue
                        result_num_raw = num - b_num
                    else:
                        result_num_raw = num + b_num

                    # Adding/subtracting SIMILAR (like-denominator) fractions
                    # keeps the common denominator: 1/6 + 3/6 = 4/6, NOT 2/3.
                    # Reducing to lowest terms is a later competency (G4) and
                    # would (a) change the denominator the student works in and
                    # (b) redraw the visual model in a different number of
                    # parts than the operation shows. Leave the result over the
                    # common denominator.
                    r_num, r_den = result_num_raw, den

                    candidate_params.append({
                        "numerator":    num,
                        "denominator":  den,
                        "fraction_str": frac_s,
                        "model_type":   model_type,
                        "operation":    operation,
                        "a_num":        num,
                        "a_den":        den,
                        "b_num":        b_num,
                        "b_den":        den,
                        "result_num":   r_num,
                        "result_den":   r_den,
                        "result":       f"{r_num}/{r_den}" if r_den != 1 else str(r_num),
                    })

    if not candidate_params:
        raise RuntimeError(
            f"generate_params (fractions): no valid fraction found for grade={grade}, "
            f"profile={difficulty_profile}."
        )

    # Convert candidate_params to formats for window sampling
    from backend.app.practice_gen.generators.number_difficulty import generate_number_by_window, generate_pair_by_window
    
    if operation != "add_subtract":
        candidates = [(cp["numerator"], cp["denominator"]) for cp in candidate_params]
        max_den = max(denom_pool)
        # "Represent fractions that are equal to one and greater than one"
        # (mat_g3_na_q4_6, fraction_type="improper"): the candidate pool's
        # numeric VALUE spans from exactly 1.0 (num==den, "equal to one")
        # up to ~3.9 (whole=3 + near-max part) -- d=5's narrower window
        # (width 0.2) never reaches all the way down to the pool's own
        # minimum at the default scalar, so "equal to one" essentially
        # never appeared even though it's a real, valid candidate (blind
        # review: "not a single one represents a fraction exactly equal
        # to one"; verified live: 0/200 seeds at default scalar reach
        # num==den, vs. 27/100 once the scalar is pushed to 0.0). Same
        # fix and same magnitude as the earlier missing_number.py/
        # multiplication.py table-window narrowness fixes this session.
        d = 3 if frac_type in ("improper", "mixed", "mixed_number") else 5
        # d=3 alone still left "equal to one" reachable only at the
        # scalar's extremes, not the default -- verified live, still 0
        # hits across 100 seeds at the default scalar after the d=3
        # widening alone (blind review, twice: "not a single one
        # represents a fraction exactly equal to one"). Force it directly
        # a third of the time, the same probability-boost pattern already
        # used elsewhere in this DNA/session (patterns.py's use_letters,
        # this file's own count_sequence denominator choice) for a named
        # sub-case the general windowing algorithm under-samples.
        equal_to_one_candidates = [c for c in candidates if c[0] == c[1]]
        if equal_to_one_candidates and rng.random() < 0.33:
            selected_frac = rng.choice(equal_to_one_candidates)
        else:
            selected_frac = generate_number_by_window(candidates, num_diff_scalar, d=d, rng=rng, num_type="fraction", max_den=max_den)
        for cp in candidate_params:
            if (cp["numerator"], cp["denominator"]) == selected_frac:
                return cp
    else:
        candidate_pairs = [((cp["a_num"], cp["a_den"]), (cp["b_num"], cp["b_den"])) for cp in candidate_params]
        max_den = max(denom_pool)
        selected_pair = generate_pair_by_window(candidate_pairs, num_diff_scalar, d=5, rng=rng, num_type="fraction", max_den=max_den)
        for cp in candidate_params:
            if ((cp["a_num"], cp["a_den"]), (cp["b_num"], cp["b_den"])) == selected_pair:
                return cp

    return candidate_params[0]


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hint strings for the given fractions problem."""
    num       = values["numerator"]
    den       = values["denominator"]
    operation = values.get("operation", "identify_name")
    model     = values.get("model_type", "area_model")

    frac_lbl  = VOCAB_FRACTION.resolve(cumulative_vocab)
    num_lbl   = VOCAB_NUMERATOR.resolve(cumulative_vocab)
    den_lbl   = VOCAB_DENOMINATOR.resolve(cumulative_vocab)

    if operation == "identify_name":
        return [
            f"A {frac_lbl} shows how many equal parts are shaded out of the total.",
            f"The {den_lbl} (bottom number) tells the total equal parts: {den}.",
            f"The {num_lbl} (top number) tells how many parts are taken: {num}.",
            f"So the {frac_lbl} is {num}/{den}.",
        ]

    if operation == "compare":
        other_num = values.get("b_num", num - 1 if num > 1 else num + 1)
        other_den = values.get("b_den", den)
        return [
            f"To compare {num}/{den} and {other_num}/{other_den}, check if the {den_lbl}s are equal.",
            f"When {den_lbl}s are the same, the {frac_lbl} with the bigger {num_lbl} is larger.",
            f"{num} vs {other_num}: the larger top number gives the larger {frac_lbl}.",
        ]

    # add_subtract
    a_num = values.get("a_num", num)
    b_num = values.get("b_num", 0)
    r_num = values.get("result_num", a_num + b_num)
    r_den = values.get("result_den", den)
    return [
        f"When adding {frac_lbl}s with the same {den_lbl}, keep the {den_lbl} the same.",
        f"Add only the {num_lbl}s: {a_num} + {b_num} = {a_num + b_num}.",
        f"Write the result over the same {den_lbl}: {a_num + b_num}/{den}.",
        f"The answer is {r_num}/{r_den}.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

FRACTIONS_DNA = DNA(
    concept="fractions",
    dna_type="formula",
    answer_formula="numerator / denominator",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "fraction_model_read",
        "fraction_shade",
        # "ordering" is NOT listed here even though fractions.py has a
        # working "order" operation and registry.py's binding for it
        # (guarded off with `False and`) -- see that guard's comment.
        # validate_matrix's §1C exhaustive sweep tries every DNA-declared
        # compatible formatter against every node regardless of what
        # operation that node actually binds, so merely disabling the
        # operation binding wasn't enough to stop §1E's naive (non-
        # fraction-aware) sort check from firing against ordinary
        # identify_name renders too, once "ordering" became a declared
        # compatible formatter at all.
    ],
    requires_context=False,
    visual_home="FractionModel",
    difficulty_axes=_DIFFICULTY_AXES,
)
