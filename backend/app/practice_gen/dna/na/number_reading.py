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

    parts: List[str] = []

    thousands = n // 1000
    remainder = n % 1000
    if thousands:
        parts.append(f"{_ONES[thousands]} thousand")

    hundreds = remainder // 100
    remainder = remainder % 100
    if hundreds:
        parts.append(f"{_ONES[hundreds]} hundred")

    if remainder > 0:
        if remainder < 20:
            parts.append(_ONES[remainder])
        else:
            tens  = remainder // 10
            ones  = remainder % 10
            chunk = _TENS[tens]
            if ones:
                chunk = f"{chunk}-{_ONES[ones]}"
            parts.append(chunk)

    return " ".join(parts)


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
    if grade == 1 and task_type == "numeral_to_expanded":
        task_type = "numeral_to_word"

    if task_type == "identify_value":
        # "...using a variety of concrete and pictorial models (e.g.,
        # number line, block or bar models, and numerals)" names a
        # representation this DNA never had at all -- reading a number's
        # magnitude from base-10 blocks, as opposed to converting between
        # numeral/word/expanded forms (blind review: "block/bar models...
        # never appear anywhere"). Reuses place_value.py's own task_type
        # name for the identical underlying skill; fmt_place_value_blocks.py
        # is wired to this DNA's compatible_formatters for it (see
        # compatibility.py).
        number = rng.randint(lo, hi)
        return {
            "number":        number,
            "word_form":     num_to_tagalog_style_english_words(number),
            "expanded_form": _make_expanded_form(number),
            "task_type":     "identify_value",
            "blank_target":  "number",
            "answer":        number,
        }

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

    log_val = log_min + num_diff_scalar * (log_max - log_min)
    max_target = int(math.pow(10, log_val)) - shift
    
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
    if task_type == "word_to_numeral":
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
            "Count how many of each size of block there are.",
            "Multiply each block's own value by how many there are, then add all the totals together.",
        ]
        place_terms = [
            (number // 1000, "thousands"),
            ((number % 1000) // 100, "hundreds"),
            ((number % 100) // 10, "tens"),
            (number % 10, "ones"),
        ]
        for digit, term in place_terms:
            if digit > 0 and term in cumulative_vocab:
                hints.append(f"{term.capitalize()}: {digit} block{'s' if digit != 1 else ''}.")
        hints.append(f"Add the value of every block together to get the total, {number}.")
        return hints

    if task_type == "numeral_to_word":
        hints.append(f"Read the number {number} one place at a time, starting from the largest place.")
        if number >= 1000:
            th = number // 1000
            hints.append(f"Thousands: {th} → '{num_to_tagalog_style_english_words(th)} thousand'.")
        if (number % 1000) >= 100:
            hd = (number % 1000) // 100
            hundreds_label = "Hundreds" if "hundreds" in cumulative_vocab else "The 3rd part from the right"
            hints.append(f"{hundreds_label}: {hd} → '{num_to_tagalog_style_english_words(hd)} hundred'.")
        hints.append(f"The full word form is: '{word_form}'.")
    else:
        pv_label = VOCAB_PLACE_VALUE.resolve(cumulative_vocab)
        hints.append(f"Identify each word part and its {pv_label}.")
        expanded_label = VOCAB_EXPANDED_FORM.resolve(cumulative_vocab)
        hints.append(f"{expanded_label.capitalize()}: {expanded_form}.")
        hints.append(f"Add the parts together to get {number}.")

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
