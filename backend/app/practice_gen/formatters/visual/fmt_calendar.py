"""
fmt_calendar.py — Calendar visual formatter

Produces a FormattedProblem with calendar visual_params.
Carves generation logic from visual_skeletons.py _gen_calendar /
_traps_calendar; does NOT import from that module.

visual_params:
    month              — int (1–12)
    year               — int
    highlighted_dates  — list[int]
    question_date      — int | None   (target date for "select" tasks)
    show_day_names     — bool
    task_type          — "select_date" | "measure_duration"
    correct_date       — int | None
    correct_duration   — int | None

interaction_mode:
    "read" — calendar shown; student identifies the day of week for a date
             OR counts days between two dates
    "set"  — student clicks a date on the calendar

answer_collection:
    "mcq"            — 4 choices (day-name strings or integer counts)
    "fill_in_blank"  — student types the day name or integer count

Day-of-week calculation uses Python's datetime (stdlib only, no extra deps).
School-year months preferred: Aug–Dec, Jan–Apr for Philippine context.
"""

import calendar as calendar_module
import random
from datetime import datetime
from typing import List, Optional

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors
from backend.app.practice_gen.formatters._option_order import shuffle_options
from backend.app.practice_gen.slots import S, derived, fill
from backend.app.practice_gen.formatters._answer_slots import (correct_option_key, distractors_field, member_text)


# ─────────────────────────────────────────────────────────────────────────────
# Day-of-week helpers
# ─────────────────────────────────────────────────────────────────────────────

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
_SCHOOL_MONTHS = [8, 9, 10, 11, 12, 1, 2, 3, 4]   # Philippine school year


def _weekday_name(year: int, month: int, day: int) -> str:
    """Return English day-of-week name for a date using stdlib datetime."""
    return datetime(year, month, day).strftime("%A")


def _days_in_month(year: int, month: int) -> int:
    return calendar_module.monthrange(year, month)[1]


# ─────────────────────────────────────────────────────────────────────────────
# Visual-params builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_visual_params(
    grade: int, diff_level: int, rng: random.Random
) -> dict:
    """
    Build Calendar visual_params.

    Grade 1–2: date-selection tasks only (click the correct date).
    Grade 3+:  date-selection OR duration tasks (count days between dates).
    """
    year = 2025
    month = rng.choice(_SCHOOL_MONTHS)
    max_day = _days_in_month(year, month)

    # Choose task type
    use_duration = (grade >= 3) and (diff_level >= 2) and rng.choice([True, False])

    if use_duration:
        day1 = rng.randint(1, max_day - 5)
        span = rng.randint(3, min(10, max_day - day1))
        day2 = day1 + span
        duration = day2 - day1 + 1   # inclusive
        return {
            "month": month,
            "year": year,
            "highlighted_dates": list(range(day1, day2 + 1)),
            "question_date": None,
            "show_day_names": True,
            "task_type": "measure_duration",
            "correct_date": None,
            "correct_duration": duration,
            # Extra context for question text
            "_day1": day1,
            "_day2": day2,
        }
    else:
        day = rng.randint(1, max_day)
        return {
            "month": month,
            "year": year,
            "highlighted_dates": [],
            "question_date": day,
            "show_day_names": True,
            "task_type": "select_date",
            "correct_date": day,
            "correct_duration": None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Trap builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(params: dict, rng: random.Random) -> dict:
    traps: dict = {}
    task_type = params["task_type"]

    if task_type == "select_date":
        correct_date = params["correct_date"]
        max_day = _days_in_month(params["year"], params["month"])
        if correct_date > 1:
            traps["one_day_before"] = {
                "value": correct_date - 1,
                "description": "Selected one day before",
            }
        if correct_date < max_day:
            traps["one_day_after"] = {
                "value": correct_date + 1,
                "description": "Selected one day after",
            }
        if correct_date > 7:
            traps["one_week_before"] = {
                "value": correct_date - 7,
                "description": "Selected one week before",
            }
        if correct_date <= max_day - 7:
            traps["one_week_after"] = {
                "value": correct_date + 7,
                "description": "Selected one week after",
            }

    else:  # measure_duration
        correct_dur = params["correct_duration"]
        traps["exclusive_count"] = {
            "value": correct_dur - 1,
            "description": "Counted exclusively instead of inclusively",
        }
        traps["off_by_one"] = {
            "value": correct_dur + 1,
            "description": "Counting error",
        }

    return traps


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_calendar(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a Calendar FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Calendar is displayed; student answers a question about it.
        Questions:
          - "What day of the week is [date]?"
          - "How many days from [day1] to [day2], inclusive?"
    interaction_mode "set":
        Student clicks the target date on the calendar.

    answer_collection "mcq":
        Four day-name OR count choices.
    answer_collection "fill_in_blank":
        Student types the day name or integer.
    """
    # ── 1. Resolve visual_params ───────────────────────────────────────────────
    if ctx.visual_params and "task_type" in ctx.visual_params:
        vp = ctx.visual_params.copy()
    else:
        diff_profile = ctx.difficulty_profile or {}
        diff_level = min(len(diff_profile) + 1, 4) if diff_profile else 2
        vp = _build_visual_params(ctx.grade, diff_level, random.Random(ctx.seed))

    task_type = vp["task_type"]
    month = vp["month"]
    year = vp["year"]
    month_name = datetime(year, month, 1).strftime("%B")
    cal_word = fill("calendar") if "calendar" in ctx.cumulative_vocab else fill("date chart")

    traps = _build_traps(vp, rng)

    # ── 2. Compute correct answer ─────────────────────────────────────────────
    if ctx.values and ctx.values.get("task_type") == "read_month":
        raw_correct = month_name
        question_text = fill("Look at the {cal_word} page shown. What month of the year is shown on this {cal_word}?", _src=('task_type',), cal_word=S(cal_word, "fill"))
    elif task_type == "select_date":
        date = vp["correct_date"]
        weekday = _weekday_name(year, month, date)

        if interaction_mode in ("read", "set"):
            question_text = (
                fill("Look at the {month_name} {year} {cal_word}. What day of the week is {month_name} {date}?", month_name=S(month_name, "enum:backend.app.practice_gen.formatters.visual.fmt_calendar._MONTH_NAMES"), year=S(year, "value:year"), cal_word=S(cal_word, "fill"), date=S(date, "value:target_date"))
            )
        raw_correct = weekday

    else:  # measure_duration
        day1 = vp.get("_day1") or next(
            (d for d in vp.get("highlighted_dates", []) if d), 1
        )
        day2 = vp.get("_day2") or (day1 + vp["correct_duration"] - 1)
        duration = vp["correct_duration"]
        # "unit" lets a caller ask this in weeks instead of days (e.g.
        # calendar.py's task_type="elapsed_weeks") -- omitted, this
        # defaults to the original days-only phrasing.
        unit_word = vp.get("unit", "days")

        question_text = (
            fill("Look at the {month_name} {year} {cal_word}. How many {unit_word} are there from {month_name} {day1} to {month_name} {day2}, inclusive?", month_name=S(month_name, "enum:backend.app.practice_gen.formatters.visual.fmt_calendar._MONTH_NAMES"), year=S(year, "value:year"), cal_word=S(cal_word, "fill"), unit_word=derived(unit_word), day1=S(day1, "value:target_date"), day2=S(day2, "value:end_date"))
        )
        raw_correct = duration

    # ── 3. Answer collection ──────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        if ctx.values and ctx.values.get("task_type") == "read_month":
            other_months = [m for m in _MONTH_NAMES if m != raw_correct]
            rng.shuffle(other_months)
            all_opts = [raw_correct] + other_months[:3]
        elif task_type == "select_date":
            # Day-name options: correct + 3 other day names
            other_days = [d for d in _DAY_NAMES if d != raw_correct]
            rng.shuffle(other_days)
            all_opts = [raw_correct] + other_days[:3]
        else:
            # Duration options
            dur = raw_correct
            seen = {dur}
            distractor_vals: List[int] = []
            for t in traps.values():
                v = t.get("value")
                if v is not None and v not in seen and v > 0:
                    seen.add(v)
                    distractor_vals.append(v)
            if len(distractor_vals) < 3:
                distractor_vals = augment_distractors(distractor_vals, dur, target=3, max_delta=5)
                if len(distractor_vals) < 3:
                    raise ValueError(f"Formatter 'calendar' requires at least 3 unique distractors, but got {len(distractor_vals)}")
            all_opts = [dur] + distractor_vals[:3]

        # Structured slots (H3-R2): a name option is one of this formatter's month/day names.
        all_opts = [member_text(v, tuple(_MONTH_NAMES) + tuple(_DAY_NAMES), "fmt_calendar month and day names")
                    for v in all_opts]
        shuffle_options(all_opts, ctx.node_id, ctx.seed)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == raw_correct}
            for i, v in enumerate(all_opts)
        ]
        correct_answer = correct_option_key(mcq_options)
    else:
        correct_answer = raw_correct

    # Strip internal keys and answer leaks before returning vp
    clean_vp = {k: v for k, v in vp.items() if not k.startswith("_")}
    clean_vp.pop("correct_date", None)
    clean_vp.pop("correct_duration", None)

    format_data: dict = {"visual_params": clean_vp}
    if mcq_options is not None:
        format_data["mcq_options"] = mcq_options

    fmt = f"{interaction_mode}_{answer_collection}"

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_calendar",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=correct_answer,
        distractors=distractors_field(ctx),
        hints=ctx.hints,
        format=fmt,
        format_data=format_data,
        is_visual=True,
        visual_type="Calendar",
        visual_params=clean_vp,
        interaction_mode=interaction_mode,
        answer_collection=answer_collection,
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
        given_values={k: v for k, v in ctx.values.items() if k != ctx.blank_target} if ctx.values else None,
        blank_target=ctx.blank_target,
    )
