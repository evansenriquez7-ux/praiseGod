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


# ─────────────────────────────────────────────────────────────────────────────
# Day-of-week helpers
# ─────────────────────────────────────────────────────────────────────────────

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
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

    traps = _build_traps(vp, rng)

    # ── 2. Compute correct answer ─────────────────────────────────────────────
    if task_type == "select_date":
        date = vp["correct_date"]
        weekday = _weekday_name(year, month, date)

        if interaction_mode in ("read", "set"):
            question_text = (
                f"Look at the {month_name} {year} calendar. "
                f"What day of the week is {month_name} {date}?"
            )
        raw_correct = weekday

    else:  # measure_duration
        day1 = vp.get("_day1") or next(
            (d for d in vp.get("highlighted_dates", []) if d), 1
        )
        day2 = vp.get("_day2") or (day1 + vp["correct_duration"] - 1)
        duration = vp["correct_duration"]

        question_text = (
            f"Look at the {month_name} {year} calendar. "
            f"How many days are there from {month_name} {day1} "
            f"to {month_name} {day2}, inclusive?"
        )
        raw_correct = duration

    # ── 3. Answer collection ──────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        if task_type == "select_date":
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
            for off in [2, 3, -2]:
                if len(distractor_vals) >= 3:
                    break
                c = dur + off
                if c > 0 and c not in seen:
                    seen.add(c)
                    distractor_vals.append(c)
            all_opts = [dur] + distractor_vals[:3]

        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == raw_correct}
            for i, v in enumerate(all_opts)
        ]
        correct_answer = next(o["key"] for o in mcq_options if o["is_correct"])
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
        distractors=ctx.distractors,
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
    )
