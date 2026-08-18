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
VOCAB_CALENDAR = VocabGated(
    requires_vocab="calendar",
    preferred="calendar",
    fallback="date chart",
)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
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
    if task_type == "elapsed_days_or_weeks":
        # registry.py sentinel for "duration... in terms of number of days
        # and/or weeks" (mat_g2_mg_q4_0): the competency names both units,
        # so alternate between them per seed rather than locking to one.
        task_type = rng.choice(["elapsed_days", "elapsed_weeks"])
    elif task_type == "day_and_month_calendar":
        # registry.py sentinel for "Determine the day and month of the
        # year using a calendar" (mat_g1_mg_q4_3): rotate across day-of-week
        # reading, calendar-month reading, and date-lookup.
        task_type = rng.choice(["read_day", "read_month", "find_date"])
    elif task_type == "days_and_months":
        # registry.py sentinel for "Solve problems involving time (...
        # days in a week, and months in a year)" (mat_g1_mg_q4_4):
        task_type = rng.choice(["problem_days", "problem_months", "read_day"])

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

    if task_type == "problem_days":
        mode = rng.choice(["after_days", "before_days", "duration_days"])
        if mode == "after_days":
            idx = rng.randint(0, 6)
            day = DAYS_OF_WEEK[idx]
            add_d = rng.randint(1, 3)
            ans = DAYS_OF_WEEK[(idx + add_d) % 7]
            q = f"Today is {day}. What day of the week will it be in {add_d} {'day' if add_d == 1 else 'days'}?"
        elif mode == "before_days":
            idx = rng.randint(0, 6)
            day = DAYS_OF_WEEK[idx]
            sub_d = rng.randint(1, 2)
            ans = DAYS_OF_WEEK[(idx - sub_d) % 7]
            q = f"If today is {day}, what day of the week was it {sub_d} {'day' if sub_d == 1 else 'days'} ago?"
        else:
            start_idx = rng.randint(1, 3)
            dur = rng.randint(2, 4)
            end_idx = start_idx + dur - 1
            s_day = DAYS_OF_WEEK[start_idx]
            e_day = DAYS_OF_WEEK[end_idx]
            ans = dur
            q = f"A school event starts on {s_day} and finishes on {e_day} of the same week. How many days does the event run?"

        dists = [d for d in (DAYS_OF_WEEK if isinstance(ans, str) else [ans + 1, max(1, ans - 1), ans + 2]) if d != ans][:3]
        return {
            "blank_target": "answer",
            "task_type": "problem_days",
            "answer": ans,
            "distractors": dists,
            "question": q,
            "visual_params": vp,
            "month": month,
            "year": year,
        }

    if task_type == "problem_months":
        mode = rng.choice(["after_months", "month_diff"])
        if mode == "after_months":
            idx = rng.randint(0, 11)
            m_name = MONTHS_OF_YEAR[idx]
            add_m = rng.randint(1, 3)
            ans = MONTHS_OF_YEAR[(idx + add_m) % 12]
            q = f"This month is {m_name}. What month will it be in {add_m} {'month' if add_m == 1 else 'months'}?"
        else:
            m1_idx = rng.randint(0, 7)
            diff = rng.randint(2, 4)
            m2_idx = m1_idx + diff
            m1_name = MONTHS_OF_YEAR[m1_idx]
            m2_name = MONTHS_OF_YEAR[m2_idx]
            ans = diff
            q = f"The school program begins in {m1_name} and an exhibit happens in {m2_name}. How many months later is the exhibit?"

        dists = [d for d in (MONTHS_OF_YEAR if isinstance(ans, str) else [ans + 1, max(1, ans - 1), ans + 2]) if d != ans][:3]
        return {
            "blank_target": "answer",
            "task_type": "problem_months",
            "answer": ans,
            "distractors": dists,
            "question": q,
            "visual_params": vp,
            "month": month,
            "year": year,
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
            "question": f"Look at the {MONTHS_OF_YEAR[month - 1]} {year} calendar. What day of the week is {MONTHS_OF_YEAR[month - 1]} {target_date}?",
        }

    if task_type == "read_month":
        month_num = rng.randint(1, 12)
        answer = MONTHS_OF_YEAR[month_num - 1]
        vp["month"] = month_num
        vp["highlighted_dates"] = [1]
        vp["correct_date"] = 1
        dists = [m for m in MONTHS_OF_YEAR if m != answer][:3]
        return {
            "blank_target": "answer",
            "visual_params": vp,
            "month": month_num,
            "year": year,
            "target_date": 1,
            "answer": answer,
            "distractors": dists,
            "task_type": task_type,
            "question": f"Look at the calendar page shown. What month of the year is shown on this calendar?",
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
        # base_generator.py only pulls visual_params from values["visual_params"]
        # (see its "j. Visual type / params" step) -- this branch never set
        # that key, so fmt_calendar.py's own ctx.visual_params check always
        # found nothing and silently fell back to ITS OWN independent
        # _build_visual_params generator instead (which gates duration
        # questions to grade>=3, so this G2 "elapsed_days"/"elapsed_weeks"
        # task_type could never actually reach a student regardless of what
        # this function computed -- found while fixing mat_g2_mg_q4_0's
        # "duration... in days and/or weeks" competency: every rendered
        # sample was plain day-of-week reading, not duration, despite this
        # branch existing and being correctly selected).
        # Counted inclusively (day1 through day2 both count), matching
        # fmt_calendar.py's own "...inclusive?" question phrasing exactly --
        # an earlier version of this branch counted exclusively (elapsed =
        # end-start), which would have served an answer one day short of
        # what that phrasing asks for.
        start_date = rng.randint(1, days_in_this_month - 7)
        span       = rng.randint(1, min(6, days_in_this_month - start_date))
        end_date   = start_date + span
        elapsed    = end_date - start_date + 1
        return {
            "blank_target": "answer",
            "month": month,
            "year": year,
            "target_date": start_date,
            "end_date": end_date,
            "answer": elapsed,
            "task_type": task_type,
            "question": (
                f"Look at the {MONTHS_OF_YEAR[month - 1]} {year} calendar. "
                f"How many days are there from {MONTHS_OF_YEAR[month - 1]} {start_date} "
                f"to {MONTHS_OF_YEAR[month - 1]} {end_date}, inclusive?"
            ),
            "visual_params": {
                "month": month,
                "year": year,
                "highlighted_dates": list(range(start_date, end_date + 1)),
                "question_date": None,
                "show_day_names": True,
                "task_type": "measure_duration",
                "correct_date": None,
                "correct_duration": elapsed,
                "_day1": start_date,
                "_day2": end_date,
            },
        }

    if task_type == "sequence":
        # "Give the days of the week and months of the year in the correct
        # order" (mat_g1_mg_q4_2) has no matching task_type at all -- every
        # existing task_type reads a specific date FROM a calendar grid,
        # none test reciting/sequencing the day or month names themselves.
        # Direction ("next"/"previous") and unit (days vs. months) are both
        # varied by seed so a Lab-forced sample set still shows both.
        use_days = rng.random() < 0.5
        names = DAYS_OF_WEEK if use_days else MONTHS_OF_YEAR
        unit_label = "day of the week" if use_days else "month of the year"
        idx = rng.randint(0, len(names) - 1)
        forward = rng.random() < 0.5
        if forward:
            answer = names[(idx + 1) % len(names)]
            question = f"What {unit_label} comes right after {names[idx]}?"
        else:
            answer = names[(idx - 1) % len(names)]
            question = f"What {unit_label} comes right before {names[idx]}?"
        return {
            "blank_target": "answer",
            "month": month,
            "year": year,
            "reference_name": names[idx],
            "direction": "next" if forward else "previous",
            "unit": "days" if use_days else "months",
            "answer": answer,
            "task_type": "sequence",
            "question": question,
            "distractors": [n for n in names if n != answer and n != names[idx]][:3],
        }

    # elapsed_weeks
    # Same visual_params wiring as elapsed_days above (see that branch's
    # comment) -- without it, fmt_calendar.py's calendar_read formatter
    # (the DOMINANT one for this DNA) fell back to its own independent,
    # grade>=3-gated generator, so at G2 this task_type rendered as plain
    # day-of-week reading via calendar_read even though generate_params had
    # already correctly resolved it (blind review round 2 confirmed: 7 of
    # 14 samples were still "what day of the week", tracing to exactly the
    # elapsed_weeks-selected seeds). end_date is start_date + weeks*7 - 1
    # (not start_date + weeks*7) so an INCLUSIVE day count spans exactly
    # weeks*7 days, keeping "weeks" and the inclusive day range consistent
    # with each other -- fmt_calendar.py's own "unit" param (added
    # alongside this fix) renders the question in weeks instead of days.
    start_date = rng.randint(1, days_in_this_month - 14)
    weeks      = rng.randint(1, min(4, (days_in_this_month - start_date + 1) // 7))
    end_date   = start_date + weeks * 7 - 1
    return {
        "blank_target": "answer",
        "month": month,
        "year": year,
        "target_date": start_date,
        "end_date": end_date,
        "answer": weeks,
        "task_type": task_type,
        "question": (
            f"Look at the {MONTHS_OF_YEAR[month - 1]} {year} calendar. "
            f"How many weeks are there from {MONTHS_OF_YEAR[month - 1]} {start_date} "
            f"to {MONTHS_OF_YEAR[month - 1]} {end_date}, inclusive?"
        ),
        "visual_params": {
            "month": month,
            "year": year,
            "highlighted_dates": list(range(start_date, end_date + 1)),
            "question_date": None,
            "show_day_names": True,
            "task_type": "measure_duration",
            "correct_date": None,
            "correct_duration": weeks,
            "unit": "weeks",
            "_day1": start_date,
            "_day2": end_date,
        },
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
    cal_label     = VOCAB_CALENDAR.resolve(cumulative_vocab)

    if task_type == "read_day_of_week":
        return [
            f"The {days_label} are: Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday.",
            f"Find the date on the {cal_label} and look at which column it is in.",
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
            f"Count the {unit} between {start} and {end} on the {cal_label}.",
            f"Subtract: {end} - {start} = {values.get('answer', '?')} {unit}.",
        ]
    return [
        f"Use the {cal_label} to find the answer.",
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
