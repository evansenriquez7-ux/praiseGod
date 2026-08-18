"""
DNA: Time Reading (Measurement & Geometry)

Covers MATATAG grades 1–2 time-telling competencies.
  G1: hour, half-hour, quarter-hour on analog clocks
  G2: hours + minutes, a.m./p.m. distinction, elapsed time
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
    "g1": {
        "hour": (1, 12),
        "minute_choices": [0, 30, 15, 45],   # hour, half, quarter-hour only
    },
    "g2": {
        "hour": (1, 12),
        "minute_choices": list(range(0, 60, 5)),  # any 5-minute interval
    },
}


# ─── error patterns ───────────────────────────────────────────────────────────
# No direct trap-catalog codes for time; these are inferred misconceptions.
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="time_reading",
        label="hour_minute_swap",
        description="Read the minute hand as hours and the hour hand as minutes.",
    ),
    ErrorPattern(
        formula="None",
        required_concept="time_reading",
        label="off_five_minutes",
        description="Off by 5 minutes — misread the nearest 5-minute mark.",
    ),
    ErrorPattern(
        formula="None",
        required_concept="time_reading",
        label="am_pm_swap",
        description="Swapped a.m. and p.m. when context requires the distinction.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, List[str]] = {
    "precision":    ["hour", "half_hour", "quarter_hour", "five_minutes", "one_minute"],
    }


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_ELAPSED = VocabGated(
    requires_vocab="elapsed",
    preferred="elapsed time",
    fallback="how much time passed",
)
VOCAB_AMPM = VocabGated(
    requires_vocab="a.m./p.m.",
    preferred="a.m. or p.m.",
    fallback="morning or afternoon",
)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Returns visual_params for the ClockSet formatter:
      {"hour": int, "minute": int, "time_str": str, "precision": str}
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}
    g_key = f"g{max(1, min(grade, 2))}"
    bounds = _PARAM_BOUNDS[g_key]

    if profile.get("task_type") == "elapsed_time":
        # "Solve problems involving elapsed time (minutes in an hour,
        # hours in a day, days in a week), including timetables" (mat_g2_
        # mg_q4_2). Supports all 4 sub-cases:
        # 1. minutes in an hour / duration & end time
        # 2. hours in a day (whole hour durations & start/end times)
        # 3. days in a week (day durations & start/end day names)
        # 4. timetables (bus and class schedules)
        use_ampm = grade >= 2

        def _fmt_time(h: int, m: int, p: Optional[str]) -> str:
            return f"{h}:{m:02d}" + (f" {p}" if p else "")

        elapsed_unit = profile.get("elapsed_unit") or rng.choice(["minutes", "hours", "days", "timetable"])

        if elapsed_unit == "hours":
            start_hour = rng.randint(6, 11)
            duration_hours = rng.randint(2, 6)
            total_end_hour = start_hour + duration_hours
            start_period = "a.m."
            if total_end_hour < 12:
                end_hour = total_end_hour
                end_period = "a.m."
            elif total_end_hour == 12:
                end_hour = 12
                end_period = "p.m."
            else:
                end_hour = total_end_hour - 12
                end_period = "p.m."

            start_str = _fmt_time(start_hour, 0, start_period if use_ampm else None)
            end_str = _fmt_time(end_hour, 0, end_period if use_ampm else None)

            activity = rng.choice([
                "family road trip", "school library schedule",
                "community sports festival", "museum tour", "train journey"
            ])
            ask = profile.get("elapsed_ask") or rng.choice(["duration", "end_time", "start_time"])
            if ask == "duration":
                trailing = "" if end_str.endswith(".") else "."
                question = f"The {activity} started at {start_str} and ended at {end_str}{trailing} How many hours did it last?"
                answer = duration_hours
                distractors = sorted({
                    d for d in [
                        duration_hours + 1, max(1, duration_hours - 1),
                        duration_hours + 2, max(1, duration_hours - 2)
                    ] if d != duration_hours and d > 0
                })
            elif ask == "end_time":
                question = f"The {activity} started at {start_str} and lasted for {duration_hours} hours. What time did it end?"
                answer = end_str
                off_hour1 = 12 if end_hour == 11 else (end_hour % 12) + 1
                off_hour2 = 12 if end_hour == 1 else end_hour - 1
                distractors = [
                    s for s in {
                        _fmt_time(off_hour1, 0, end_period if use_ampm else None),
                        _fmt_time(off_hour2, 0, end_period if use_ampm else None),
                        _fmt_time(start_hour, 0, start_period if use_ampm else None),
                    } if s != end_str
                ]
            else:
                question = f"The {activity} ended at {end_str} after running for {duration_hours} hours. What time did it start?"
                answer = start_str
                off_start1 = 12 if start_hour == 1 else start_hour - 1
                off_start2 = (start_hour % 12) + 1
                distractors = [
                    s for s in {
                        _fmt_time(off_start1, 0, start_period if use_ampm else None),
                        _fmt_time(off_start2, 0, start_period if use_ampm else None),
                        _fmt_time(end_hour, 0, end_period if use_ampm else None),
                    } if s != start_str
                ]

            return {
                "blank_target": "answer",
                "task_type": "elapsed_time",
                "elapsed_unit": "hours",
                "start_time_str": start_str,
                "end_time_str": end_str,
                "duration_hours": duration_hours,
                "question": question,
                "answer": answer,
                "distractors": distractors,
                "hour": start_hour,
                "minute": 0,
                "time_str": start_str,
                "precision": "hour",
                "period": start_period if use_ampm else None,
            }

        elif elapsed_unit == "days":
            days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            start_idx = rng.randint(0, 3)
            start_day = days_of_week[start_idx]
            duration_days = rng.randint(2, 4)
            end_idx = start_idx + duration_days - 1
            end_day = days_of_week[end_idx]
            activity = rng.choice([
                "science fair", "reading camp", "school sports meet", "art workshop", "gardening project"
            ])
            art = "an" if activity.startswith(("a", "e", "i", "o", "u")) else "a"
            ask = profile.get("elapsed_ask") or rng.choice(["duration", "end_day"])
            if ask == "duration":
                question = f"{art.capitalize()} {activity} begins on {start_day} and finishes on {end_day} of the same week. How many days does the {activity} run?"
                answer = duration_days
                distractors = sorted({
                    d for d in [duration_days + 1, max(1, duration_days - 1), duration_days + 2, 7]
                    if d != duration_days and d > 0
                })
            else:
                question = f"A {duration_days}-day {activity} starts on {start_day}. On what day of the week does it end?"
                answer = end_day
                distractors = [
                    d for d in days_of_week if d != end_day and d != start_day
                ][:3]

            return {
                "blank_target": "answer",
                "task_type": "elapsed_time",
                "elapsed_unit": "days",
                "start_day": start_day,
                "end_day": end_day,
                "duration_days": duration_days,
                "question": question,
                "answer": answer,
                "distractors": distractors,
                "hour": 8,
                "minute": 0,
                "time_str": _fmt_time(8, 0, "a.m." if use_ampm else None),
                "precision": "hour",
                "period": "a.m." if use_ampm else None,
            }

        elif elapsed_unit == "timetable":
            tt_type = rng.choice(["bus", "class"])
            if tt_type == "bus":
                b1_dur = rng.choice([30, 45, 60])
                b2_dur = rng.choice([35, 40, 45, 50, 60])
                b1_start_h = 7
                b1_start_m = 0
                b1_end_h = 7 if b1_dur < 60 else 8
                b1_end_m = b1_dur % 60

                b2_start_h = 8
                b2_start_m = 15
                b2_total = 8 * 60 + 15 + b2_dur
                b2_end_h = b2_total // 60
                b2_end_m = b2_total % 60

                b1_start_str = _fmt_time(b1_start_h, b1_start_m, "a.m." if use_ampm else None)
                b1_end_str = _fmt_time(b1_end_h, b1_end_m, "a.m." if use_ampm else None)
                b2_start_str = _fmt_time(b2_start_h, b2_start_m, "a.m." if use_ampm else None)
                b2_end_str = _fmt_time(b2_end_h, b2_end_m, "a.m." if use_ampm else None)

                target_bus = rng.choice([1, 2])
                ans_min = b1_dur if target_bus == 1 else b2_dur

                question = (
                    f"Look at the bus timetable:\n"
                    f"• Bus 1: Departs {b1_start_str}, Arrives {b1_end_str}\n"
                    f"• Bus 2: Departs {b2_start_str}, Arrives {b2_end_str}\n"
                    f"According to the timetable, how many minutes is the travel time for Bus {target_bus}?"
                )
                answer = ans_min
                distractors = sorted({
                    d for d in [ans_min + 10, max(5, ans_min - 10), ans_min + 15, ans_min * 2]
                    if d != ans_min and d > 0
                })
            else:
                m_start_str = _fmt_time(8, 0, "a.m." if use_ampm else None)
                m_end_str = _fmt_time(9, 0, "a.m." if use_ampm else None)
                e_start_str = _fmt_time(9, 0, "a.m." if use_ampm else None)
                e_end_str = _fmt_time(9, 45, "a.m." if use_ampm else None)

                subj = rng.choice(["Math", "English"])
                if subj == "Math":
                    question = (
                        f"Look at the class schedule:\n"
                        f"• Math: {m_start_str} – {m_end_str}\n"
                        f"• English: {e_start_str} – {e_end_str}\n"
                        f"How many hours long is the Math class?"
                    )
                    answer = 1
                    distractors = [2, 3, 4]
                else:
                    question = (
                        f"Look at the class schedule:\n"
                        f"• Math: {m_start_str} – {m_end_str}\n"
                        f"• English: {e_start_str} – {e_end_str}\n"
                        f"How many minutes long is the English class?"
                    )
                    answer = 45
                    distractors = [30, 40, 50]

            return {
                "blank_target": "answer",
                "task_type": "elapsed_time",
                "elapsed_unit": "timetable",
                "question": question,
                "answer": answer,
                "distractors": distractors,
                "hour": 8,
                "minute": 0,
                "time_str": _fmt_time(8, 0, "a.m." if use_ampm else None),
                "precision": "hour",
                "period": "a.m." if use_ampm else None,
            }

        else:
            # minutes in an hour
            if use_ampm:
                start_period = rng.choice(["a.m.", "p.m."])
                if start_period == "a.m.":
                    start_hour = rng.randint(7, 11)
                else:
                    start_hour = rng.choice([12, 1, 2, 3, 4, 5, 6])
            else:
                start_period = None
                start_hour = rng.randint(7, 11)
            start_minute = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
            duration_minutes = rng.choice([5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60])

            total_start = (start_hour % 12) * 60 + start_minute
            total_end = total_start + duration_minutes
            period_flips = total_end >= 12 * 60
            total_end_in_day = total_end % (12 * 60)
            end_hour = total_end_in_day // 60
            end_hour = 12 if end_hour == 0 else end_hour
            end_minute = total_end_in_day % 60
            end_period = None
            if use_ampm:
                end_period = (
                    ("p.m." if start_period == "a.m." else "a.m.") if period_flips else start_period
                )

            start_str = _fmt_time(start_hour, start_minute, start_period)
            end_str = _fmt_time(end_hour, end_minute, end_period)

            activity = rng.choice([
                "a recess", "a class", "a movie", "a bus ride",
                "a study session", "a swimming lesson", "a soccer practice",
            ])
            ask = profile.get("elapsed_ask") or rng.choice(["duration", "end_time"])
            if ask == "duration":
                trailing = "" if end_str.endswith(".") else "."
                question = (
                    f"{activity.capitalize()} started at {start_str} and ended "
                    f"at {end_str}{trailing} How many minutes did it last?"
                )
                answer: Any = duration_minutes
                distractors = sorted({
                    d for d in (
                        duration_minutes + 5, max(1, duration_minutes - 5),
                        60 - duration_minutes if duration_minutes < 60 else duration_minutes + 60,
                        duration_minutes * 2,
                    ) if d != duration_minutes and d > 0
                })
            else:
                question = (
                    f"{activity.capitalize()} started at {start_str} and "
                    f"lasted {duration_minutes} minutes. What time did it end?"
                )
                answer = end_str
                off_hour = 12 if end_hour == 11 else (end_hour % 12) + 1
                off_hour = 12 if off_hour == 0 else off_hour
                off_minute = (end_minute + 10) % 60
                distractors = [
                    s for s in {
                        _fmt_time(off_hour, end_minute, end_period),
                        _fmt_time(end_hour, off_minute, end_period),
                        _fmt_time(start_hour, start_minute, start_period),
                    } if s != end_str
                ]

            return {
                "blank_target": "answer",
                "task_type": "elapsed_time",
                "elapsed_unit": "minutes",
                "start_time_str": start_str,
                "end_time_str": end_str,
                "duration_minutes": duration_minutes,
                "question": question,
                "answer": answer,
                "distractors": distractors,
                "hour": start_hour,
                "minute": start_minute,
                "time_str": start_str,
                "precision": "one_minute",
                "period": start_period,
            }

    # "Read and write time in hours and minutes, with a.m. and p.m."
    # (mat_g2_mg_q4_1) always defaulted to "hour" precision and no a.m./
    # p.m. when unbound -- neither ever auto-varied, so half-hour,
    # quarter-hour, and minute-level readings, plus a.m./p.m. labeling,
    # never appeared regardless of seed (blind review: comprehensive_
    # coverage FAIL, "Half-hour and quarter-hour... completely absent").
    # "one_minute" is G2+ only per this function's own minute-generation
    # branches below.
    precision_choices = ["hour", "half_hour", "quarter_hour"]
    if grade >= 2:
        precision_choices += ["five_minutes", "one_minute"]
    precision = profile.get("precision") or rng.choice(precision_choices)
    if grade < 2 and precision not in ("hour", "half_hour", "quarter_hour"):
        precision = "quarter_hour"

    hour = rng.randint(bounds["hour"][0], bounds["hour"][1])

    if precision == "hour":
        minute = 0
    elif precision == "half_hour":
        minute = 30
    elif precision == "quarter_hour":
        minute = rng.choice([15, 45])
    elif precision == "five_minutes":
        minute = rng.choice(list(range(0, 60, 5)))
    else:  # one_minute — G2+ only
        minute = rng.randint(0, 59)

    # Build human-readable time string
    if minute == 0:
        time_str = f"{hour}:00"
    else:
        time_str = f"{hour}:{minute:02d}"

    # VARIANTS_BY_DNA declares this axis's values as "yes"/"no"
    # (compatibility.py), but this line compared against "with_ampm"/
    # "no_ampm" -- neither of which is ever a real value anything sends,
    # so even an explicit Lab request for include_ampm="yes" silently
    # resolved to False. Combined with no auto-vary when unbound, a.m./
    # p.m. never appeared in this DNA's output at all regardless of
    # caller (blind review of mat_g2_mg_q4_1: "none labels a time as
    # a.m. or p.m.").
    #
    # compatibility.py declares include_ampm=["yes","no"] with no per-node
    # scoping, so validate_matrix's §1C exhaustive sweep requests
    # include_ampm="yes" against G1 nodes (mat_g1_mg_q4_1/_4) too -- but
    # this DNA's own docstring scopes "a.m./p.m. distinction" to G2, and
    # G1's cumulative_vocab marks "a.m."/"p.m." NOT_YET_KNOWN. Force it
    # off below grade 2 regardless of what's requested, matching the
    # curriculum's vocabulary gate rather than the raw request.
    include_ampm = grade >= 2 and (profile.get("include_ampm") or rng.choice(["yes", "no"])) == "yes"
    if include_ampm:
        period = rng.choice(["a.m.", "p.m."])
        time_str = f"{time_str} {period}"
    else:
        period = None

    result = {
        "blank_target": "time_str",
        # Explicit marker so compatibility.py's FORMATTER_VARIANT_SUPPORT
        # can distinguish this default single-clock reading/setting path
        # from the elapsed_time branch above -- the orchestrator's variant
        # filter only ever EXCLUDES a formatter when the axis value is
        # PRESENT and mismatching (an absent/None value always passes),
        # so leaving this path's task_type unset would have let the new
        # mcq/cloze formatters (added for elapsed_time's word-problem
        # text) also get picked here, where ctx.values has none of
        # elapsed_time's fields and no "question" narrative to show.
        "task_type": "clock_reading",
        "hour": hour,
        "minute": minute,
        "time_str": time_str,
        "precision": precision,
        "period": period,
    }
    if profile.get("context") == "word_problem":
        if grade < 2:
            mode = rng.choice(["hours_duration", "half_hour_duration", "quarter_hour_duration", "elapsed_hours", "elapsed_minutes"])
            actor = rng.choice(["Maria", "Jose", "Ana", "Ben", "Liza", "Sam", "Leo", "Mia"])
            if mode == "hours_duration":
                start_h = rng.randint(7, 10)
                dur = rng.randint(1, 2)
                end_h = start_h + dur
                activity = rng.choice(["a class", "a workshop", "art time", "study time"])
                ans_str = f"{end_h}:00"
                dists = list(dict.fromkeys([d for d in [f"{start_h}:00", f"{end_h + 1}:00", f"{max(1, start_h - 1)}:00", f"{end_h + 2}:00"] if d != ans_str]))[:3]
                return {
                    "blank_target": "answer",
                    "task_type": "clock_reading",
                    "hour": end_h,
                    "minute": 0,
                    "time_str": ans_str,
                    "answer": ans_str,
                    "distractors": dists,
                    "question": f"{activity.capitalize()} starts at {start_h}:00 and lasts for {dur} {'hour' if dur == 1 else 'hours'}. What time does it end?",
                }
            elif mode == "half_hour_duration":
                start_h = rng.randint(8, 11)
                ans_str = f"{start_h}:30"
                activity = rng.choice(["Lunch", "Recess", "Story time", "Play time"])
                dists = [f"{start_h}:00", f"{start_h + 1}:00", f"{start_h + 1}:30"]
                return {
                    "blank_target": "answer",
                    "task_type": "clock_reading",
                    "hour": start_h,
                    "minute": 30,
                    "time_str": ans_str,
                    "answer": ans_str,
                    "distractors": dists,
                    "question": f"{activity} starts at {start_h}:00 and lasts half an hour (30 minutes). What time does it end?",
                }
            elif mode == "quarter_hour_duration":
                start_h = rng.randint(8, 11)
                ans_str = f"{start_h}:15"
                activity = rng.choice(["A short break", "Morning exercise", "Reading time"])
                dists = [f"{start_h}:00", f"{start_h}:30", f"{start_h}:45"]
                return {
                    "blank_target": "answer",
                    "task_type": "clock_reading",
                    "hour": start_h,
                    "minute": 15,
                    "time_str": ans_str,
                    "answer": ans_str,
                    "distractors": dists,
                    "question": f"{activity} starts at {start_h}:00 and lasts a quarter of an hour (15 minutes). What time does it end?",
                }
            elif mode == "elapsed_hours":
                start_h = rng.randint(7, 9)
                dur = rng.randint(1, 3)
                end_h = start_h + dur
                activity = rng.choice(["read books", "draw pictures", "play games", "help in the garden"])
                ans_num = dur
                dists = [d for d in [dur + 1, max(1, dur - 1), dur + 2] if d != ans_num][:3]
                return {
                    "blank_target": "answer",
                    "task_type": "clock_reading",
                    "hour": start_h,
                    "minute": 0,
                    "time_str": f"{start_h}:00",
                    "answer": ans_num,
                    "distractors": dists,
                    "question": f"{actor} started to {activity} at {start_h}:00 and finished at {end_h}:00. How many hours did {actor} spend?",
                }
            else:  # elapsed_minutes
                start_h = rng.randint(8, 11)
                ans_num = 30
                activity = rng.choice(["recess", "snack time", "clean-up time"])
                return {
                    "blank_target": "answer",
                    "task_type": "clock_reading",
                    "hour": start_h,
                    "minute": 30,
                    "time_str": f"{start_h}:30",
                    "answer": ans_num,
                    "distractors": [15, 45, 60],
                    "question": f"The {activity} began at {start_h}:00 and finished at {start_h}:30. How many minutes did it last?",
                }
        else:
            activity = rng.choice([
                "wakes up", "eats breakfast", "leaves for school",
                "starts homework", "goes to sleep", "has lunch",
            ])
            actor = rng.choice(["Maria", "Jose", "Ana", "Ben", "Liza"])
            result["question"] = f"{actor} {activity} at {time_str}. What time is that?"
    return result


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    minute_known = "minute" in cumulative_vocab
    hour = values["hour"]
    minute = values.get("minute", 0)

    if minute_known:
        hints = [
            "The short hand shows the hour. The long hand shows the minutes.",
            f"The short (hour) hand points near {hour}.",
        ]
        if minute == 0:
            hints.append("The long (minute) hand points to 12, so the minutes are 00.")
        elif minute == 30:
            hints.append("The long (minute) hand points to 6, so the minutes are 30.")
        elif minute == 15:
            hints.append("The long (minute) hand points to 3, so the minutes are 15.")
        elif minute == 45:
            hints.append("The long (minute) hand points to 9, so the minutes are 45.")
        else:
            marks = minute // 5
            hints.append(
                f"Count by 5s from 12: the long hand has passed {marks} marks, "
                f"so the minutes are {minute}."
            )
    else:
        # G1: 'minute' hasn't been introduced yet — describe hand position with
        # 'half'/'quarter' (already known) instead of naming minutes directly.
        hints = [
            "The short hand shows the hour. The long hand shows how far past the hour it is.",
            f"The short (hour) hand points near {hour}.",
        ]
        if minute == 0:
            hints.append("The long hand points to 12, so it is exactly on the hour.")
        elif minute == 30:
            hints.append("The long hand points to 6 — that is half past the hour.")
        elif minute == 15:
            hints.append("The long hand points to 3 — that is a quarter past the hour.")
        elif minute == 45:
            hints.append("The long hand points to 9 — that is a quarter before the next hour.")
        else:
            marks = minute // 5
            hints.append(f"Count by 5s from 12: the long hand has passed {marks} marks.")

    hints.append(f"The time shown is {values['time_str']}.")
    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

TIME_READING_DNA = DNA(
    concept="time_reading",
    dna_type="visual_read",
    answer_formula=None,
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "fill_in_blank", "clock_read", "clock_set"],
    requires_context=False,
    visual_home="ClockSet",
    difficulty_axes=_DIFFICULTY_AXES,
)
