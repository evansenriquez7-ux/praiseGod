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
    if lo > hi:
        lo = hi

    task_type = profile.get("task_type", "numeral_to_word")
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
        if d_val != number and d_val > 0 and d_val not in distractors:
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

    if task_type == "numeral_to_word":
        hints.append(f"Read the number {number} one place at a time, starting from the largest place.")
        if number >= 1000:
            th = number // 1000
            hints.append(f"Thousands: {th} → '{num_to_tagalog_style_english_words(th)} thousand'.")
        if (number % 1000) >= 100:
            hd = (number % 1000) // 100
            hints.append(f"Hundreds: {hd} → '{num_to_tagalog_style_english_words(hd)} hundred'.")
        hints.append(f"The full word form is: '{word_form}'.")
    else:
        hints.append(f"Identify each word part and its place value.")
        hints.append(f"Expanded form: {expanded_form}.")
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
    ],
    requires_context=False,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
