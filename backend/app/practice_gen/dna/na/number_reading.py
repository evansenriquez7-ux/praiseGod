"""
DNA: Number Reading / Writing (Number & Algebra)

Covers MATATAG grades 1–3 numeral/word-form competencies:
  G1 — 1–100
  G2 — 1–1000
  G3 — 1–10000
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)
from backend.app.practice_gen.slots import E, S, derived, fill, join, transform


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"min_value": 1,  "max_value": 100},
    "g2": {"min_value": 1,  "max_value": 1000},
    "g3": {"min_value": 1,  "max_value": 10000},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = []


_DIFFICULTY_AXES: Dict[str, Any] = {
    "range": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_EXPANDED_FORM = VocabGated("expanded form", "expanded form", "broken apart form")
VOCAB_PLACE_VALUE   = VocabGated("place value", "place value", "value of each part")


# ─── number-to-words helper ───────────────────────────────────────────────────

_ONES = [
    "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen",
]
_TENS = [
    "", "", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety",
]


def num_to_tagalog_style_english_words(n: int) -> str:
    """
    Convert a positive integer (1–10000) to Filipino math word style English.

    Examples:
        243   → "two hundred forty-three"
        1005  → "one thousand five"
        10000 → "ten thousand"
    """
    if n <= 0 or n > 10000:
        return str(n)

    if n == 10000:
        return "ten thousand"

    # Each part is a slot (`enum:` over this module's own word tables, or a nested fill) and the
    # sentence is `slots.join`, so the words are recorded with strict domains (ruling 42).
    ones_words = "enum:backend.app.practice_gen.dna.na.number_reading._ONES"
    tens_words = "enum:backend.app.practice_gen.dna.na.number_reading._TENS"
    parts: List[Any] = []

    thousands = n // 1000
    remainder = n % 1000
    if thousands:
        parts.append(S(fill("{v} thousand", v=S(_ONES[thousands], ones_words)), "fill"))

    hundreds = remainder // 100
    remainder = remainder % 100
    if hundreds:
        parts.append(S(fill("{v} hundred", v=S(_ONES[hundreds], ones_words)), "fill"))

    if remainder > 0:
        if remainder < 20:
            parts.append(S(_ONES[remainder], ones_words))
        else:
            tens  = remainder // 10
            ones  = remainder % 10
            chunk = S(_TENS[tens], tens_words)
            if ones:
                chunk = S(fill("{chunk}-{v}", chunk=chunk, v=S(_ONES[ones], ones_words)), "fill")
            parts.append(chunk)

    return join(" ", parts)


def _make_expanded_form(n: int) -> str:
    """Return expanded form string, e.g. '200 + 40 + 3'."""
    digits = []
    place  = 1
    tmp    = n
    while tmp:
        d = (tmp % 10) * place
        if d:
            digits.append(d)
        tmp //= 10
        place *= 10
    return " + ".join(str(d) for d in reversed(digits)) if digits else "0"


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate a number reading/writing problem.

    Returns:
        {
            "number":        int,
            "word_form":     str,
            "expanded_form": str,
            "direction":     str ("numeral_to_word" | "word_to_numeral"),
        }
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]

    # Map range level to a tighter bound if specified
    range_level = profile.get("range", None)
    range_bounds = {
        "1_to_20":        (1,    20),
        "21_to_100":      (21,   100),
        "101_to_1000":    (101,  1000),
        "1001_to_10000":  (1001, 10000),
    }
    if range_level and range_level in range_bounds:
        lo, hi = range_bounds[range_level]
        lo = max(lo, bounds["min_value"])
        hi = min(hi, bounds["max_value"])
    else:
        lo, hi = bounds["min_value"], bounds["max_value"]

    lo = int(profile.get("min_value", lo))
    hi = int(profile.get("max_value", hi))
    # Respect the display ceiling of the chosen formatter (e.g. emoji_pictorial
    # can only render groups <= 100). The orchestrator injects
    # `formatter_max_val` from FORMATTER_NUMERIC_LIMITS; clamp `hi` to it so a
    # number-reading value never exceeds what the formatter can show.
    if "formatter_max_val" in profile:
        hi = min(hi, int(profile["formatter_max_val"]))
    if lo > hi:
        lo = hi

    # "Read AND write numbers ... in numerals and in words" (most nodes
    # mapped to this DNA) names both directions, but an unbound task_type
    # always defaulted to "numeral_to_word" -- the reverse (given a word
    # form, produce/select the numeral) was never once demonstrated across
    # any node in blind review, even at seeds specifically added to probe
    # alternate rendering paths. Vary between the two "read and write"
    # directions when not explicitly requested; "numeral_to_expanded" stays
    # opt-in only (it belongs to a different, expanded-form-specific
    # competency, not the generic read/write pairing).
    task_type = profile.get("task_type") or rng.choice(["numeral_to_word", "word_to_numeral"])
    if isinstance(task_type, list):
        # registry.py binds a rotation list (not a single value) for
        # "represent numbers using... concrete and pictorial models"
        # (mat_g1_na_q1_2/mat_g2_na_q1_2/mat_g3_na_q1_0) -- same
        # list-resolution pattern as multiplication.py/patterns.py/
        # probability_language.py's identical fix; the orchestrator only
        # auto-resolves CALLER-supplied difficulty_profile list values,
        # not ones injected later from registry bounds.
        task_type = rng.choice(task_type)
    if task_type == "read_and_write":
        task_type = rng.choice(["numeral_to_word", "word_to_numeral"])
    elif task_type == "model_representation":
        task_type = rng.choice(["identify_value", "number_line"])
    if grade == 1 and task_type == "numeral_to_expanded":
        task_type = "numeral_to_word"

    # If no range difficulty is specified, use full grade-appropriate range (scalar=1.0)
    # A scalar of 0.0 would pin every question to the minimum of the range (e.g. 1-9),
    # producing Grade 1 level problems regardless of the node's grade.
    range_val = profile.get("range", 1.0)
    try:
        range_val = float(range_val)
    except (TypeError, ValueError):
        range_val = 1.0

    import math
    shift = 1 if lo == 0 else 0
    log_min = math.log10(lo + shift)
    log_max = math.log10(hi + shift)

    if range_val > 1.0:
        if log_max > log_min:
            num_diff_scalar = (math.log10(range_val + shift) - log_min) / (log_max - log_min)
            num_diff_scalar = max(0.0, min(num_diff_scalar, 1.0))
        else:
            num_diff_scalar = 0.0
    else:
        num_diff_scalar = range_val

    from ...axes_catalog import log_scale_value
    max_target = log_scale_value(lo, hi, num_diff_scalar)
    
    current_hi = min(hi, max_target)
    
    current_lo = lo
    if num_diff_scalar > 0:
        prev_scalar = max(0.0, num_diff_scalar - 0.25)
        prev_log_val = log_min + prev_scalar * (log_max - log_min)
        prev_target = int(math.pow(10, prev_log_val)) - shift
        current_lo = min(current_hi, max(lo, prev_target + 1))
        
    candidates = sorted(list(range(current_lo, current_hi + 1)))
    number = rng.choice(candidates)

    word_form     = num_to_tagalog_style_english_words(number)
    expanded_form = _make_expanded_form(number)

    blank_target = "word_form"
    if task_type in ("word_to_numeral", "identify_value", "number_line"):
        blank_target = "number"
    elif task_type == "numeral_to_expanded":
        blank_target = "expanded_form"

    # Generate appropriate distractors
    distractors = []
    
    # helper to add distinct items
    def _add_distractor(d_val):
        # "number * 10" (a place-value-shift misconception distractor) was
        # never range-checked -- for a number already near the competency
        # ceiling (e.g. 9337 with hi=10000), it produces 93370, over 9x the
        # stated maximum. Invisible for numeral_to_word (whose distractors
        # get word-formatted, not exposed as raw numeric values) but a real
        # §1B leaky-window violation for word_to_numeral, which was simply
        # never selected before to expose it.
        if d_val != number and 0 < d_val <= hi and d_val not in distractors:
            distractors.append(d_val)
            
    # common numeric errors
    _add_distractor(int(str(number)[::-1])) # pv_reverse
    _add_distractor(number * 10)            # pv_place_shift
    if number > 10:
        _add_distractor(number - 10)
    else:
        _add_distractor(number + 1)
        
    # pad with random adjacent values if we don't have 3 yet
    offset = 1
    while len(distractors) < 3:
        _add_distractor(number + offset)
        _add_distractor(number - offset)
        offset += 1
        
    # Format distractors based on task_type
    formatted_distractors = []
    for d in distractors:
        if task_type == "word_to_numeral":
            formatted_distractors.append(d)
        elif task_type == "numeral_to_expanded":
            formatted_distractors.append(_make_expanded_form(d))
        else: # numeral_to_word
            formatted_distractors.append(num_to_tagalog_style_english_words(d))

    if blank_target == "number":
        answer = number
    elif blank_target == "expanded_form":
        answer = expanded_form
    else:
        answer = word_form

    return {
        "number":        number,
        "word_form":     word_form,
        "expanded_form": expanded_form,
        "task_type":     task_type,
        "blank_target":  blank_target,
        "distractors":   formatted_distractors[:3],
        "answer":        answer,
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hints for a number reading/writing problem."""
    number        = values["number"]
    word_form     = values["word_form"]
    expanded_form = values["expanded_form"]
    task_type     = values["task_type"]

    hints: List[str] = []

    if task_type == "identify_value":
        # "hundreds"/"ones" as bare place-value TERMS, and ordinal
        # fallbacks like "3rd"/"1st", aren't introduced at every grade
        # this task_type can be requested at (G1's own "read and write
        # numerals up to 100" competency has BOTH still on its own
        # NOT_YET_KNOWN list) -- naming either unconditionally tripped
        # §1D vocabulary_gating the moment §1C's exhaustive sweep tried
        # this task_type against a G1 node. Stay fully generic instead of
        # trying to label individual places at all.
        hints = [
            fill("Count how many of each size of block there are.", _src=('task_type',)),
            fill("Multiply each block's own value by how many there are, then add all the totals together.", _src=('task_type',)),
        ]
        place_terms = [
            (number // 1000, "thousands"),
            ((number % 1000) // 100, "hundreds"),
            ((number % 100) // 10, "tens"),
            (number % 10, "ones"),
        ]
        for digit, term in place_terms:
            if digit > 0 and term in cumulative_vocab:
                hints.append(fill("{capitalize}: {digit} block{v}.", _src=('task_type',), capitalize=S(term.capitalize(), E(tuple(t.capitalize() for _d, t in place_terms), "the four place names")), digit=derived(digit, src=("number",), why="arithmetic"), v=S('s' if digit != 1 else '', E(("s", ""), "the plural suffix"))))
        hints.append(fill("Add the value of every block together to get the total, {number}.", _src=('task_type',), number=S(number, "value:number")))
        return hints

    if task_type == "numeral_to_word":
        hints.append(fill("Read the number {number} one place at a time, starting from the largest place.", _src=('task_type',), number=S(number, "value:number")))
        if number >= 1000:
            th = number // 1000
            hints.append(fill("Thousands: {th} → '{num_to_tagalog_style_english_words} thousand'.", _src=('number', 'task_type',), th=derived(th, src=('number',), why="arithmetic"), num_to_tagalog_style_english_words=S(num_to_tagalog_style_english_words(th), "fill", src=('number',))))
        if (number % 1000) >= 100:
            hd = (number % 1000) // 100
            hundreds_label = "Hundreds" if "hundreds" in cumulative_vocab else "The 3rd part from the right"
            hints.append(fill("{hundreds_label}: {hd} → '{num_to_tagalog_style_english_words} hundred'.", _src=('number', 'task_type',), hundreds_label=S(hundreds_label, E(("Hundreds", "The 3rd part from the right"), "'hundreds' gated by cumulative_vocab")), hd=derived(hd, src=('number',), why="arithmetic"), num_to_tagalog_style_english_words=S(num_to_tagalog_style_english_words(hd), "fill", src=('number',))))
        hints.append(fill("The full word form is: '{word_form}'.", _src=('task_type',), word_form=S(word_form, "value:word_form")))
    else:
        pv_label = VOCAB_PLACE_VALUE.resolve(cumulative_vocab)
        hints.append(fill("Identify each word part and its {pv_label}.", pv_label=S(pv_label, "fill")))
        expanded_label = VOCAB_EXPANDED_FORM.resolve(cumulative_vocab)
        hints.append(fill("{capitalize}: {expanded_form}.", capitalize=S(transform("capitalize", expanded_label), "fill"), expanded_form=S(expanded_form, "value:expanded_form")))
        hints.append(fill("Add the parts together to get {number}.", number=S(number, "value:number")))

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

NUMBER_READING_DNA = DNA(
    concept="number_reading",
    dna_type="formula",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "place_value_blocks_read",
        "place_value_blocks_set",
    ],
    requires_context=False,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
