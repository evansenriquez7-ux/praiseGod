"""
DNA: Place Value (Number & Algebra)

Refactored from:
  - matatag_skeletons.py  (place_value generator + pv_* traps)
  - matatag_dimensions.py (PLACE_VALUE_DIMENSIONS)

Covers MATATAG grades 1–3 place value competencies:
  G1 — 2-digit numbers (tens, ones)
  G2 — 3-digit numbers (hundreds, tens, ones)
  G3 — 4-digit numbers (thousands, hundreds, tens, ones)
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


# ─── constants ────────────────────────────────────────────────────────────────

PLACE_NAMES  = ["ones", "tens", "hundreds", "thousands"]
PLACE_VALUES = [1, 10, 100, 1000]


# ─── param bounds ─────────────────────────────────────────────────────────────
# target_digit_position is 0-indexed from the right (0=ones, 1=tens, …)
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"number_min": 10,   "number_max": 99,   "max_place": 1},
    "g2": {"number_min": 100,  "number_max": 999,  "max_place": 2},
    "g3": {"number_min": 1000, "number_max": 9999, "max_place": 3},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="target_digit_position",
        required_concept="place_value",
        label="pv_adj_place",
        description="Gave the position index (0, 1, 2, 3) instead of the actual place value.",
    ),
    ErrorPattern(
        formula="digit_at_position",
        required_concept="place_value",
        label="pv_dig_val",
        description="Gave the bare digit instead of multiplying by its place value.",
    ),
    ErrorPattern(
        formula="value_at_position + digit_at_position",
        required_concept="place_value",
        label="pv_val_dig",
        description="Added the digit to the place value instead of computing the value correctly.",
    ),
    ErrorPattern(
        formula="int(str(number)[::-1])",
        required_concept="place_value",
        label="pv_reverse",
        description="Read the digits in reverse order.",
    ),
    ErrorPattern(
        formula="value_at_position * 10",
        required_concept="place_value",
        label="pv_place_shift",
        description="Shifted the value by one extra place (×10 error).",
    ),
    ErrorPattern(
        formula="number - digit_at_position",
        required_concept="expanded_form",
        label="pv_zero_exp",
        description="Subtracted the digit from the number instead of isolating the place value (zeroed out position incorrectly).",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {"number_difficulty": "continuous"}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_TENS          = VocabGated(requires_vocab="tens",          preferred="tens place",     fallback="second column from the right")
VOCAB_ONES          = VocabGated(requires_vocab="ones",          preferred="ones place",     fallback="last column on the right")
VOCAB_HUNDREDS      = VocabGated(requires_vocab="hundreds",      preferred="hundreds place", fallback="third column from the right")
VOCAB_THOUSANDS     = VocabGated(requires_vocab="thousands",     preferred="thousands place",fallback="fourth column from the right")
VOCAB_PLACE_VALUE   = VocabGated(requires_vocab="place value",   preferred="place value",    fallback="the position of a digit")
VOCAB_VALUE         = VocabGated(requires_vocab="value",         preferred="value",          fallback="worth")
VOCAB_EXPANDED_FORM = VocabGated(requires_vocab="expanded form", preferred="expanded form",  fallback="broken apart form")


# ─── helpers ──────────────────────────────────────────────────────────────────

def _expanded_form(number: int) -> str:
    """Return expanded form string, e.g. 3_digit 253 → '200 + 50 + 3'."""
    parts = []
    digits_str = str(number)
    length = len(digits_str)
    for i, ch in enumerate(digits_str):
        d = int(ch)
        if d == 0:
            continue
        place = length - 1 - i
        parts.append(str(d * PLACE_VALUES[place]))
    return " + ".join(parts) if parts else "0"


def _with_zero_in_middle(number: int, rng: random.Random) -> int:
    """Insert a zero into a middle position (not leading, not trailing)."""
    digits = list(str(number))
    if len(digits) < 3:
        return number
    # positions that are neither index 0 nor the last index
    mid_positions = list(range(1, len(digits) - 1))
    if not mid_positions:
        return number
    pos = rng.choice(mid_positions)
    digits[pos] = "0"
    result = int("".join(digits))
    # Guard: must stay within the original bounds
    if result < 10 ** (len(digits) - 1):
        return number  # would create leading-zero situation; bail out
    return result


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Rejection-sample a number and target position that satisfy difficulty_profile.

    Returns:
        number                : int
        target_digit_position : int  (0=ones, 1=tens, 2=hundreds, 3=thousands)
        task_type             : str
        digit_at_position     : int
        value_at_position     : int
        expanded_form         : str
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key  = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]
    n_lo   = bounds["number_min"]
    diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
    from backend.app.practice_gen.dna.base import log_interpolate
    n_hi   = int(log_interpolate(n_lo, bounds["number_max"], diff_scalar))
    n_hi   = max(n_hi, n_lo)
    max_pl = bounds["max_place"]

    # Map difficulty axes to constraints
    digit_count_level = profile.get("digit_count", "2_digit")
    task_type         = profile.get("task_type", "identify_place")
    if task_type == "any_place_value_skill":
        # Composite scope value (registry.py binds this for competencies
        # that explicitly name all three sub-skills: place-value naming,
        # digit value, and reverse digit lookup) -- resolved here via the
        # generation seed, same pattern as missing_number.py's
        # "addition_subtraction" and patterns.py's
        # "increasing_or_decreasing" composite scope values.
        task_type = rng.choice(["identify_place", "identify_value", "identify_digit"])
    include_zeros     = profile.get("include_zeros", "no_zeros") == "with_zeros"

    # Override range when digit_count axis is explicit
    if digit_count_level == "2_digit":
        n_lo, n_hi, max_pl = 10, 99, 1
    elif digit_count_level == "3_digit":
        n_lo, n_hi, max_pl = 100, 999, 2
    elif digit_count_level == "4_digit":
        n_lo, n_hi, max_pl = 1000, 9999, 3

    # For value questions, require all-unique digits to avoid ambiguity
    # Every task_type except "decompose" phrases its question as "the digit
    # X in NUMBER" (referencing the target digit by its face VALUE, not its
    # position) -- if that digit value appears more than once in NUMBER at
    # different place values (e.g. "the digit 5 in 255": 5 is both the tens
    # digit worth 50 and the ones digit worth 5), the question is genuinely
    # ambiguous about which occurrence is meant. This was previously only
    # guarded for "identify_value"; with 3-4 digit numbers now reachable
    # (digit_count fix elsewhere in this session), repeated digits are much
    # more common than with 2-digit numbers, so the gap became a real bug
    # rather than a rare edge case.
    need_unique = task_type != "decompose"

    n_lo = int(profile.get("number_min", n_lo))
    n_hi = int(profile.get("number_max", n_hi))

    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    candidates = []
    for num in range(n_lo, n_hi + 1):
        digits_str = str(num)
        
        if include_zeros and len(digits_str) >= 3:
            if "0" not in digits_str[1:-1]:
                continue
                
        if need_unique and len(set(digits_str)) != len(digits_str):
            continue
            
        candidates.append(num)

    if not candidates:
        # Fallback if over-constrained
        candidates = list(range(n_lo, n_hi + 1))

    from backend.app.practice_gen.generators.number_difficulty import generate_number_by_window
    number = generate_number_by_window(candidates, num_diff_scalar, d=5, rng=rng)
    digits_str = str(number)

    actual_max_place = len(digits_str) - 1
    target_pos = rng.randint(0, min(max_pl, actual_max_place))

    digit_index       = len(digits_str) - 1 - target_pos
    digit_at_position = int(digits_str[digit_index])
    value_at_position = digit_at_position * PLACE_VALUES[target_pos]
    exp_form          = _expanded_form(number)

    if task_type == "decompose":
        # task_type was previously pure metadata here -- generate_params()
        # always returned the same blank_target/answer regardless of its
        # value, so "decompose any 2-digit number into tens and ones"
        # (mat_g1_na_q2_3) rendered identically to the separate
        # "determine the place value" node (mat_g1_na_q2_2), with no
        # tens+ones expansion ever shown. _expanded_form() was already
        # computed but never used for anything.
        #
        # _expanded_form() itself skips zero digits (e.g. 10 -> "10", not
        # "10 + 0"), which is fine for a generic expanded-form reading but
        # degenerates a "decompose into tens and ones" exercise into a
        # non-decomposition whenever the ones digit is 0. Build an explicit
        # tens+ones expansion here instead that always shows both terms.
        exp_form = " + ".join(
            str(int(ch) * PLACE_VALUES[len(digits_str) - 1 - i])
            for i, ch in enumerate(digits_str)
        )
        distractors = set()
        digits = [int(c) for c in digits_str]
        # Distractor 1: swap two adjacent digit values in the expansion
        # (e.g. 45 -> "50 + 4" instead of "40 + 5").
        if len(digits) >= 2:
            swapped = list(digits)
            swapped[0], swapped[1] = swapped[1], swapped[0]
            swapped_num = int("".join(map(str, swapped)))
            if swapped_num != number:
                distractors.add(_expanded_form(swapped_num))
        # Distractor 2: expand as if every digit were in the ones place
        # (a common regrouping-confusion error).
        plain_sum = " + ".join(str(d) for d in digits if d != 0) or "0"
        if plain_sum != exp_form:
            distractors.add(plain_sum)
        # Distractor 3: off-by-one-place expansion (shift the leading
        # digit's place value down by one).
        if len(digits) >= 2 and digits[0] != 0:
            off_by_place = list(exp_form.split(" + "))
            off_by_place[0] = str(digits[0] * PLACE_VALUES[len(digits) - 2])
            candidate = " + ".join(off_by_place)
            if candidate != exp_form:
                distractors.add(candidate)
        distractors_list = list(distractors)[:3]
        while len(distractors_list) < 3:
            filler = f"{rng.randint(1, 9) * 10} + {rng.randint(1, 9)}"
            if filler != exp_form and filler not in distractors_list:
                distractors_list.append(filler)
        return {
            "blank_target": "expanded_form",
            "number":                number,
            "target_digit_position": target_pos,
            "task_type":             "decompose",
            "digit_at_position":     digit_at_position,
            "value_at_position":     value_at_position,
            "expanded_form":         exp_form,
            "answer":                exp_form,
            "distractors":           distractors_list,
        }

    place_name = PLACE_NAMES[target_pos] if target_pos < len(PLACE_NAMES) else f"10^{target_pos}"

    if task_type == "identify_place":
        # This competency names 3 distinct sub-skills: "the place value of
        # a digit" (name the POSITION, e.g. "tens"), "the value of a
        # digit" (compute its numeric worth, e.g. 40), and "the digit of a
        # number given its place value" (reverse lookup). Previously
        # "identify_place" and "identify_value" produced byte-identical
        # output (same numeric-value question and answer) despite the
        # different names -- "identify_place" is fixed here to actually
        # ask for and grade the POSITION NAME, matching what its own name
        # (and the competency's "place value of a digit" wording) implies.
        # Distractors bounded to max_pl+1 (this node's own vocab-gated
        # ceiling, e.g. a 2-digit-only node never has "hundreds"/
        # "thousands" as cumulative vocab yet) -- using the full 4-name
        # list unconditionally leaked NOT_YET_KNOWN place names into
        # distractor text for lower-grade nodes. When that leaves fewer
        # than 3 (2-digit numbers only have ones/tens), pad with safe,
        # non-vocabulary filler options rather than reaching for a place
        # name this node hasn't earned yet.
        other_places = [p for p in PLACE_NAMES[: max_pl + 1] if p != place_name]
        return {
            "blank_target": "place_name",
            "number":                number,
            "target_digit_position": target_pos,
            "task_type":             "identify_place",
            "digit_at_position":     digit_at_position,
            "value_at_position":     value_at_position,
            "place_name":            place_name,
            "answer":                place_name,
            "distractors":           other_places,
        }

    if task_type == "identify_digit":
        # Reverse-lookup sub-skill ("the digit of a number given its place
        # value") -- previously had no matching task_type at all, so this
        # direction was never exercised despite being explicitly named in
        # the competency.
        other_digits = [d for d in range(10) if d != digit_at_position]
        rng.shuffle(other_digits)
        return {
            "blank_target": "digit_at_position",
            "number":                number,
            "target_digit_position": target_pos,
            "task_type":             "identify_digit",
            "digit_at_position":     digit_at_position,
            "value_at_position":     value_at_position,
            "place_name":            place_name,
            "answer":                digit_at_position,
            "distractors":           other_digits[:3],
        }

    if task_type == "identify_value":
        val_distractors = []
        if digit_at_position != value_at_position:
            val_distractors.append(digit_at_position)
        for cand in [digit_at_position * 10, digit_at_position + 10, number, digit_at_position + 1]:
            if cand != value_at_position and 0 <= cand < (10 ** (max_pl + 1)) and cand not in val_distractors:
                val_distractors.append(cand)
        return {
            "blank_target": "value_at_position",
            "number":                number,
            "target_digit_position": target_pos,
            "task_type":             "identify_value",
            "digit_at_position":     digit_at_position,
            "value_at_position":     value_at_position,
            "place_name":            place_name,
            "answer":                value_at_position,
            "distractors":           val_distractors[:3],
        }

    return {
        "blank_target": "value_at_position",
        "number":                number,
        "target_digit_position": target_pos,
        "task_type":             task_type,
        "digit_at_position":     digit_at_position,
        "value_at_position":     value_at_position,
        "expanded_form":         exp_form,
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hint strings for the given place value problem."""
    number    = values["number"]
    pos       = values["target_digit_position"]
    task      = values["task_type"]
    digit     = values["digit_at_position"]
    value     = values["value_at_position"]
    exp_form  = values["expanded_form"]

    place_name = PLACE_NAMES[pos] if pos < len(PLACE_NAMES) else f"10^{pos} place"
    pv_phrase  = VOCAB_PLACE_VALUE.resolve(cumulative_vocab)
    val_phrase = VOCAB_VALUE.resolve(cumulative_vocab)
    ef_phrase  = VOCAB_EXPANDED_FORM.resolve(cumulative_vocab)

    if task == "identify_place":
        relevant_places = ", ".join(PLACE_NAMES[:pos + 1])
        return [
            f"Write out {number} with each digit in its own column.",
            f"Count from the right: {relevant_places}.",
            f"The digit in the {place_name} column is {digit}.",
        ]

    if task == "identify_value":
        return [
            f"Find the digit in the {place_name} {pv_phrase} of {number}.",
            f"That digit is {digit}.",
            f"Multiply it by its place: {digit} × {PLACE_VALUES[pos]} = {value}.",
            f"The {val_phrase} of {digit} in {number} is {value}.",
        ]

    if task == "compose":
        parts = exp_form.split(" + ")
        return [
            f"Look at each part: {exp_form}.",
            f"Add all the parts together.",
            f"{exp_form} = {number}.",
        ]

    # decompose
    return [
        f"Write the {ef_phrase} of {number}.",
        f"Break each digit into its place value: {exp_form}.",
        f"Each term shows how much that digit is {val_phrase} in its position.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

PLACE_VALUE_DNA = DNA(
    concept="place_value",
    dna_type="algorithmic",
    answer_formula="value_at_position",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "true_false",
        "place_value_blocks_read",
        "place_value_blocks_set",
    ],
    requires_context=False,
    visual_home="PlaceValueBlocks",
    difficulty_axes=_DIFFICULTY_AXES,
)
