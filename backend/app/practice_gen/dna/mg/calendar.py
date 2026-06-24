"""
DNA: Calendar (Measurement & Geometry)

Covers MATATAG grades 1–2 calendar competencies.
  G1: days of the week (order), months of the year (order), read a calendar
  G2: duration in days/weeks using a calendar, timetables, elapsed time
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
DAYS_OF_WEEK = [
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
]
MONTHS_OF_YEAR = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
# Days in each month (non-leap year, 1-indexed)
DAYS_IN_MONTH = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Any] = {
    "g1": {
        "month": (1, 12),
        "year":  2025,
    },
    "g2": {
        "month":         (1, 12),
        "year":          2025,
        "elapsed_days":  (1, 28),
        "elapsed_weeks": (1, 4),
    },
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="calendar",
        label="ms_time_conv",
        description="Confused days and weeks (e.g., said 14 days = 2 months instead of 2 weeks).",
    ),
    ErrorPattern(
        formula="None",
        required_concept="calendar",
        label="ar_off_one",
        description="Off-by-one error when counting days or weeks on a calendar.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {
    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_DAYS_WEEK = VocabGated(
    requires_vocab="days of the week",
    preferred="days of the week",
    fallback="the 7 days",
)
VOCAB_MONTHS = VocabGated(
    requires_vocab="months of the year",
    preferred="months of the year",
    fallback="the 12 months",
)
VOCAB_ELAPSED = VocabGated(
    requires_vocab="elapsed",
    preferred="elapsed time",
    fallback="how much time has passed",
)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """
    Returns visual_params for the Calendar formatter and an answer value.
      {"month": int, "year": int, "target_date": int, "answer": str_or_int}
    # The answer may be a string (day of week) or an integer (date/month)
    # We always return the components so the formatter can reconstruct the exact scenario.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}
    g_key = f"g{max(1, min(grade, 2))}"
    bounds = _PARAM_BOUNDS[g_key]
    task_type = profile.get("task_type", "read_day")

    month = rng.randint(bounds["month"][0], bounds["month"][1])
    year  = bounds.get("year", 2025)
    days_in_this_month = DAYS_IN_MONTH[month]

    # day-of-week anchor: January 1 2025 is a Wednesday (index 3)
    FIRST_DAY_2025 = [0, 3, 6, 6, 2, 4, 0, 2, 5, 1, 3, 6, 1]
    first_dow = FIRST_DAY_2025[month]

    vp = {
        "month": month,
        "year": year,
        "task_type": "select_date" if task_type in ("read_day", "find_date", "read_month") else "measure_duration",
        "show_day_names": True,
    }

    if task_type == "read_day":
        target_date = rng.randint(1, days_in_this_month)
        dow_index = (first_dow + target_date - 1) % 7
        answer = DAYS_OF_WEEK[dow_index]
        vp["highlighted_dates"] = [target_date]
        vp["correct_date"] = target_date
        return {
        "blank_target": "answer",
            "visual_params": vp,
            "month": month,
            "year": year,
            "target_date": target_date,
            "answer": answer,
            "task_type": task_type,
            "question": f"What day of the week is {MONTHS_OF_YEAR[month - 1]} {target_date}, {year}?",
        }

    if task_type == "read_month":
        month_num = rng.randint(1, 12)
        answer = MONTHS_OF_YEAR[month_num - 1]
        vp["month"] = month_num
        vp["highlighted_dates"] = [1]
        vp["correct_date"] = 1
        return {
        "blank_target": "answer",
            "visual_params": vp,
            "month": month_num,
            "year": year,
            "target_date": 1,
            "answer": answer,
            "task_type": task_type,
            "question": f"Which month is the {month_num}{'st' if month_num == 1 else 'nd' if month_num == 2 else 'rd' if month_num == 3 else 'th'} month of the year?",
        }

    if task_type == "find_date":
        target_date = rng.randint(1, days_in_this_month)
        dow_index   = (first_dow + target_date - 1) % 7
        day_name    = DAYS_OF_WEEK[dow_index]
        vp["question_date"] = target_date
        vp["correct_date"] = target_date
        return {
        "blank_target": "answer",
            "visual_params": vp,
            "month": month,
            "year": year,
            "target_date": target_date,
            "day_name": day_name,
            "answer": target_date,
            "task_type": task_type,
            "question": (
                f"In {MONTHS_OF_YEAR[month - 1]} {year}, the first day is "
                f"{DAYS_OF_WEEK[first_dow]}. What date is the first {day_name} of the month?"
            ),
        }

    if task_type == "elapsed_days":
        start_date  = rng.randint(1, days_in_this_month - 7)
        elapsed     = rng.randint(1, min(7, days_in_this_month - start_date))
        end_date    = start_date + elapsed
        return {
        "blank_target": "answer",
            "month": month,
            "year": year,
            "target_date": start_date,
            "end_date": end_date,
            "answer": elapsed,
            "task_type": task_type,
            "question": (
                f"From {MONTHS_OF_YEAR[month - 1]} {start_date} to "
                f"{MONTHS_OF_YEAR[month - 1]} {end_date}, how many days have passed?"
            ),
        }

    # elapsed_weeks
    start_date = rng.randint(1, days_in_this_month - 14)
    weeks      = rng.randint(1, min(4, (days_in_this_month - start_date) // 7))
    end_date   = start_date + weeks * 7
    return {
        "blank_target": "answer",
        "month": month,
        "year": year,
        "target_date": start_date,
        "end_date": end_date,
        "answer": weeks,
        "task_type": task_type,
        "question": (
            f"From {MONTHS_OF_YEAR[month - 1]} {start_date} to "
            f"{MONTHS_OF_YEAR[month - 1]} {end_date}, how many weeks have passed?"
        ),
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    task_type = values.get("task_type", "read_day_of_week")
    days_label    = VOCAB_DAYS_WEEK.resolve(cumulative_vocab)
    months_label  = VOCAB_MONTHS.resolve(cumulative_vocab)
    elapsed_label = VOCAB_ELAPSED.resolve(cumulative_vocab)

    if task_type == "read_day_of_week":
        return [
            f"The {days_label} are: Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday.",
            "Find the date on the calendar and look at which column it is in.",
            f"Answer: {values.get('answer', '?')}",
        ]
    if task_type == "read_month":
        return [
            f"The {months_label} go from January (1st) to December (12th).",
            f"Count to the {values.get('month', '?')}th month.",
            f"Answer: {values.get('answer', '?')}",
        ]
    if task_type in ("elapsed_days", "elapsed_weeks"):
        start = values.get("target_date", "?")
        end   = values.get("end_date", "?")
        unit  = "days" if task_type == "elapsed_days" else "weeks"
        return [
            f"Count the {unit} between {start} and {end} on the calendar.",
            f"Subtract: {end} - {start} = {values.get('answer', '?')} {unit}.",
        ]
    return [
        "Use the calendar to find the answer.",
        f"The {elapsed_label} is the number of days or weeks that have passed.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

CALENDAR_DNA = DNA(
    concept="calendar",
    dna_type="visual_read",
    answer_formula=None,
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "fill_in_blank", "calendar_read"],
    requires_context=False,
    visual_home="Calendar",
    difficulty_axes=_DIFFICULTY_AXES,
)
