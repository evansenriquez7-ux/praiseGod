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
    count_noun,
)
from backend.app.practice_gen.slots import E, R, S, derived, derives, fill, join


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
            return fill("{h}:{m:02d}{v}", h=S(h, R(1, 12, "an hour on a 12-hour clock")), m=S(m, R(0, 59, "a minute of the hour")), v=S(f" {p}" if p else "", E(("", " a.m.", " p.m."), "no period, a.m. or p.m.")))

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

            activities = [
                "family road trip", "school library schedule",
                "community sports festival", "museum tour", "train journey"
            ]
            activity = rng.choice(activities)
            ask = profile.get("elapsed_ask") or rng.choice(["duration", "end_time", "start_time"])
            if ask == "duration":
                trailing = "" if end_str.endswith(".") else "."
                question = fill("The {activity} started at {start_str} and ended at {end_str}{trailing} How many hours did it last?", _src=('elapsed_unit',), activity=S(activity, E(tuple(activities), "the activities bank")), start_str=S(start_str, "fill"), end_str=S(end_str, "value:end_time_str"), trailing=S(trailing, E(("", "."), "a full stop unless the time already ends in one")))
                answer = duration_hours
                distractors = sorted({
                    d for d in [
                        duration_hours + 1, max(1, duration_hours - 1),
                        duration_hours + 2, max(1, duration_hours - 2)
                    ] if d != duration_hours and d > 0
                })
            elif ask == "end_time":
                question = fill("The {activity} started at {start_str} and lasted for {duration_hours} hours. What time did it end?", _src=('elapsed_unit',), activity=S(activity, E(tuple(activities), "the activities bank")), start_str=S(start_str, "fill"), duration_hours=S(duration_hours, "value:duration_hours"))
                answer = end_str
                off_hour1 = 12 if end_hour == 11 else (end_hour % 12) + 1
                off_hour2 = 12 if end_hour == 1 else end_hour - 1
                distractors = sorted(
                    s for s in {
                        _fmt_time(off_hour1, 0, end_period if use_ampm else None),
                        _fmt_time(off_hour2, 0, end_period if use_ampm else None),
                        _fmt_time(start_hour, 0, start_period if use_ampm else None),
                    } if s != end_str
                )
            else:
                question = fill("The {activity} ended at {end_str} after running for {duration_hours} hours. What time did it start?", _src=('elapsed_unit',), activity=S(activity, E(tuple(activities), "the activities bank")), end_str=S(end_str, "fill"), duration_hours=S(duration_hours, "value:duration_hours"))
                answer = start_str
                off_start1 = 12 if start_hour == 1 else start_hour - 1
                off_start2 = (start_hour % 12) + 1
                distractors = sorted(
                    s for s in {
                        _fmt_time(off_start1, 0, start_period if use_ampm else None),
                        _fmt_time(off_start2, 0, start_period if use_ampm else None),
                        _fmt_time(end_hour, 0, end_period if use_ampm else None),
                    } if s != start_str
                )

            return {
                "blank_target": "answer",
                "task_type": "elapsed_time",
                "elapsed_unit": "hours",
                "elapsed_ask": ask,
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
            activities = [
                "science fair", "reading camp", "school sports meet", "art workshop", "gardening project"
            ]
            activity = rng.choice(activities)
            art = "an" if activity.startswith(("a", "e", "i", "o", "u")) else "a"
            ask = profile.get("elapsed_ask") or rng.choice(["duration", "end_day"])
            if ask == "duration":
                question = fill("{capitalize} {activity} begins on {start_day} and finishes on {end_day} of the same week. How many days does the {activity} run?", _src=('elapsed_unit',), capitalize=S(art.capitalize(), E(("A", "An"), "the article, sentence-initial")), activity=S(activity, E(tuple(activities), "the activities bank")), start_day=S(start_day, "value:start_day"), end_day=S(end_day, "value:end_day"))
                answer = duration_days
                distractors = sorted({
                    d for d in [duration_days + 1, max(1, duration_days - 1), duration_days + 2, 7]
                    if d != duration_days and d > 0
                })
            else:
                question = fill("A {duration_days}-day {activity} starts on {start_day}. On what day of the week does it end?", _src=('elapsed_unit',), duration_days=S(duration_days, "value:duration_days"), activity=S(activity, E(tuple(activities), "the activities bank")), start_day=S(start_day, "value:start_day"))
                answer = end_day
                distractors = [
                    d for d in days_of_week if d != end_day and d != start_day
                ][:3]

            return {
                "blank_target": "answer",
                "task_type": "elapsed_time",
                "elapsed_unit": "days",
                "elapsed_ask": ask,
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

                buses = [1, 2]
                target_bus = rng.choice(buses)
                ans_min = b1_dur if target_bus == 1 else b2_dur
                timetable_target = fill("Bus {target_bus}", _src=('elapsed_unit',), target_bus=S(target_bus, E(tuple(buses), "the buses on the timetable")))

                # The timetable is DRAWN (visual_type="Timetable") rather than
                # bulleted into the stem. "Look at the bus timetable:" followed by no
                # timetable is the defect `dangling_visual_reference_1M` names, and the
                # competency asks for elapsed time "including TIMETABLES" -- a timetable
                # is a display, so drawing it is what the LC says (Content Rule 4).
                timetable_kind = "bus"
                timetable_columns = ["Bus", "Departs", "Arrives"]
                timetable_rows = [
                    {"label": "Bus 1", "start": b1_start_str, "end": b1_end_str},
                    {"label": "Bus 2", "start": b2_start_str, "end": b2_end_str},
                ]
                question = (
                    fill("Look at the bus timetable. According to the timetable, how many minutes is the travel time for Bus {target_bus}?", _src=('elapsed_unit',), target_bus=S(target_bus, E(tuple(buses), "the buses on the timetable")))
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
                timetable_target = subj
                # As above: the schedule is drawn, not bulleted into the stem.
                timetable_kind = "class"
                timetable_columns = ["Subject", "Starts", "Ends"]
                timetable_rows = [
                    {"label": "Math", "start": m_start_str, "end": m_end_str},
                    {"label": "English", "start": e_start_str, "end": e_end_str},
                ]
                if subj == "Math":
                    question = (
                        fill("Look at the class schedule. How many hours long is the Math class?", _src=('elapsed_unit',))
                    )
                    answer = 1
                    distractors = [2, 3, 4]
                else:
                    question = (
                        fill("Look at the class schedule. How many minutes long is the English class?", _src=('elapsed_unit',))
                    )
                    answer = 45
                    distractors = [30, 40, 50]

            return {
                "blank_target": "answer",
                "task_type": "elapsed_time",
                "elapsed_unit": "timetable",
                # What `timetable_read` draws. Carried in values rather than composed in
                # the formatter so the DNA stays the single source of the times the key
                # is computed from -- a formatter that rebuilt them could disagree with
                # the answer, which is the "two copies of one rule" trap.
                "timetable_kind": timetable_kind,
                "timetable_columns": timetable_columns,
                "timetable_rows": timetable_rows,
                # The row the question asks about, declared so `generate_hints` reads
                # it instead of re-deriving it from the question's wording.
                "timetable_target": timetable_target,
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

            activities = [
                "a recess", "a class", "a movie", "a bus ride",
                "a study session", "a swimming lesson", "a soccer practice",
            ]
            activity = rng.choice(activities)
            ask = profile.get("elapsed_ask") or rng.choice(["duration", "end_time"])
            if ask == "duration":
                trailing = "" if end_str.endswith(".") else "."
                question = (
                    fill("{capitalize} started at {start_str} and ended at {end_str}{trailing} How many minutes did it last?", _src=('elapsed_unit',), capitalize=S(activity.capitalize(), E(tuple(a.capitalize() for a in activities), "the activities bank, capitalized")), start_str=S(start_str, "fill"), end_str=S(end_str, "value:end_time_str"), trailing=S(trailing, E(("", "."), "a full stop unless the time already ends in one")))
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
                    fill("{capitalize} started at {start_str} and lasted {duration_minutes} minutes. What time did it end?", _src=('elapsed_unit',), capitalize=S(activity.capitalize(), E(tuple(a.capitalize() for a in activities), "the activities bank, capitalized")), start_str=S(start_str, "fill"), duration_minutes=S(duration_minutes, "value:duration_minutes"))
                )
                answer = end_str
                off_hour = 12 if end_hour == 11 else (end_hour % 12) + 1
                off_hour = 12 if off_hour == 0 else off_hour
                off_minute = (end_minute + 10) % 60
                distractors = sorted(
                    s for s in {
                        _fmt_time(off_hour, end_minute, end_period),
                        _fmt_time(end_hour, off_minute, end_period),
                        _fmt_time(start_hour, start_minute, start_period),
                    } if s != end_str
                )

            return {
                "blank_target": "answer",
                "task_type": "elapsed_time",
                "elapsed_unit": "minutes",
                "elapsed_ask": ask,
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
        time_str = fill("{hour}:00", _src=('minute',), hour=S(hour, R(bounds["hour"][0], bounds["hour"][1], "bounds['hour']")))
    else:
        time_str = fill("{hour}:{minute:02d}", hour=S(hour, R(bounds["hour"][0], bounds["hour"][1], "bounds['hour']")), minute=S(minute, R(0, 59, "a minute of the hour")))

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
        time_str = fill("{time_str} {period}", time_str=S(time_str, "fill"), period=S(period, "value:period"))
    else:
        period = None

    # Owner ruling 41: the minute (and so the time shown) is drawn at the chosen precision.
    derives("minute", src=("precision",))
    derives("time_str", src=("precision",))
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
            actors = ["Maria", "Jose", "Ana", "Ben", "Liza", "Sam", "Leo", "Mia"]
            actor = rng.choice(actors)
            if mode == "hours_duration":
                sh_lo, sh_hi = 7, 10
                start_h = rng.randint(sh_lo, sh_hi)
                dur_lo, dur_hi = 1, 2
                dur = rng.randint(dur_lo, dur_hi)
                end_h = start_h + dur
                activities = ["a class", "a workshop", "art time", "study time"]
                activity = rng.choice(activities)
                start_dom = R(sh_lo, sh_hi, "the start hour's draw bounds")
                ans_str = fill("{end_h}:00", end_h=S(end_h, "value:hour"))
                dists = list(dict.fromkeys([d for d in [fill("{start_h}:00", start_h=S(start_h, start_dom)), fill("{v}:00", v=derived(end_h + 1, src=('hour',), why="arithmetic")), fill("{max}:00", max=S(max(1, start_h - 1), R(max(1, sh_lo - 1), sh_hi - 1, "the hour before the start"))), fill("{v}:00", v=derived(end_h + 2, src=('hour',), why="arithmetic"))] if d != ans_str]))[:3]
                return {
                    "blank_target": "answer",
                    "task_type": "clock_reading",
                    "hour": end_h,
                    "minute": 0,
                    "time_str": ans_str,
                    "answer": ans_str,
                    "distractors": dists,
                    "question": fill("{capitalize} starts at {start_h}:00 and lasts for {dur} {v}. What time does it end?", capitalize=S(activity.capitalize(), E(tuple(a.capitalize() for a in activities), "the activities bank, capitalized")), start_h=S(start_h, start_dom), dur=S(dur, R(dur_lo, dur_hi, "the duration's draw bounds")), v=S('hour' if dur == 1 else 'hours', E(("hour", "hours"), "hour or hours, by the count"))),
                }
            elif mode == "half_hour_duration":
                start_h = rng.randint(8, 11)
                ans_str = fill("{start_h}:30", start_h=S(start_h, "value:hour"))
                activities = ["Lunch", "Recess", "Story time", "Play time"]
                activity = rng.choice(activities)
                dists = [fill("{start_h}:00", start_h=S(start_h, "value:hour")), fill("{v}:00", v=derived(start_h + 1, src=('hour',), why="arithmetic")), fill("{v}:30", v=derived(start_h + 1, src=('hour',), why="arithmetic"))]
                return {
                    "blank_target": "answer",
                    "task_type": "clock_reading",
                    "hour": start_h,
                    "minute": 30,
                    "time_str": ans_str,
                    "answer": ans_str,
                    "distractors": dists,
                    "question": fill("{activity} starts at {start_h}:00 and lasts half an hour (30 minutes). What time does it end?", activity=S(activity, E(tuple(activities), "the activities bank")), start_h=S(start_h, "value:hour")),
                }
            elif mode == "quarter_hour_duration":
                start_h = rng.randint(8, 11)
                ans_str = fill("{start_h}:15", start_h=S(start_h, "value:hour"))
                activities = ["A short break", "Morning exercise", "Reading time"]
                activity = rng.choice(activities)
                dists = [fill("{start_h}:00", start_h=S(start_h, "value:hour")), fill("{start_h}:30", start_h=S(start_h, "value:hour")), fill("{start_h}:45", start_h=S(start_h, "value:hour"))]
                return {
                    "blank_target": "answer",
                    "task_type": "clock_reading",
                    "hour": start_h,
                    "minute": 15,
                    "time_str": ans_str,
                    "answer": ans_str,
                    "distractors": dists,
                    "question": fill("{activity} starts at {start_h}:00 and lasts a quarter of an hour (15 minutes). What time does it end?", activity=S(activity, E(tuple(activities), "the activities bank")), start_h=S(start_h, "value:hour")),
                }
            elif mode == "elapsed_hours":
                start_h = rng.randint(7, 9)
                dur = rng.randint(1, 3)
                end_h = start_h + dur
                activities = ["read books", "draw pictures", "play games", "help in the garden"]
                activity = rng.choice(activities)
                ans_num = dur
                dists = [d for d in [dur + 1, max(1, dur - 1), dur + 2] if d != ans_num][:3]
                return {
                    "blank_target": "answer",
                    "task_type": "clock_reading",
                    "hour": start_h,
                    "minute": 0,
                    "time_str": fill("{start_h}:00", start_h=S(start_h, "value:hour")),
                    "answer": ans_num,
                    "distractors": dists,
                    "question": fill("{actor} started to {activity} at {start_h}:00 and finished at {end_h}:00. How many hours did {actor} spend?", actor=S(actor, E(tuple(actors), "the actors bank")), activity=S(activity, E(tuple(activities), "the activities bank")), start_h=S(start_h, "value:hour"), end_h=derived(end_h, src=('hour', 'answer'), why="arithmetic")),
                }
            else:  # elapsed_minutes
                start_h = rng.randint(8, 11)
                ans_num = 30
                activities = ["recess", "snack time", "clean-up time"]
                activity = rng.choice(activities)
                return {
                    "blank_target": "answer",
                    "task_type": "clock_reading",
                    "hour": start_h,
                    "minute": 30,
                    "time_str": fill("{start_h}:30", start_h=S(start_h, "value:hour")),
                    "answer": ans_num,
                    "distractors": [15, 45, 60],
                    "question": fill("The {activity} began at {start_h}:00 and finished at {start_h}:30. How many minutes did it last?", activity=S(activity, E(tuple(activities), "the activities bank")), start_h=S(start_h, "value:hour")),
                }
        else:
            activities = [
                "wakes up", "eats breakfast", "leaves for school",
                "starts homework", "goes to sleep", "has lunch",
            ]
            activity = rng.choice(activities)
            actors = ["Maria", "Jose", "Ana", "Ben", "Liza"]
            actor = rng.choice(actors)
            result["question"] = fill("{actor} {activity} at {time_str}. What time is that?", actor=S(actor, E(tuple(actors), "the actors bank")), activity=S(activity, E(tuple(activities), "the activities bank")), time_str=S(time_str, "fill"))
    return result


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    # The hints explain THE ITEM THAT WAS GENERATED. Until 2026-09-25 every item
    # got the clock-face chain below -- including elapsed-time word problems,
    # day-of-the-week spans and timetables, none of which shows a clock (blind
    # review of mat_g2_mg_q4_2: 20 of 27 samples; hint contract, `medium`). The
    # branch is the one `generate_params` took, read from the values it declared.
    if values.get("task_type") == "elapsed_time":
        return _elapsed_hints(values)
    return _clock_hints(values, cumulative_vocab)


def _say(text: str) -> str:
    """End a hint with one full stop -- a time like '9:15 a.m.' already has one."""
    return text if text.endswith(".") else fill("{text}.", text=S(text, "fill"))


def _elapsed_hints(values: Dict[str, Any]) -> List[str]:
    unit = values["elapsed_unit"]
    if unit == "timetable":
        target = values["timetable_target"]
        row = next((r for r in values["timetable_rows"] if r["label"] == target), None)
        if row is None:
            raise ValueError(
                f"time_reading.generate_hints: timetable_target {target!r} is not a row "
                f"of {values['timetable_rows']!r}"
            )
        answer = values["answer"]
        noun = "hours" if "hours" in values["question"] else "minutes"
        return [
            fill("Find the row for {target} in the {timetable_kind} {v}.", _src=('elapsed_unit',), target=S(target, "value:timetable_target"), timetable_kind=S(values['timetable_kind'], "value:timetable_kind"), v=S('timetable' if values['timetable_kind'] == 'bus' else 'schedule', E(("timetable", "schedule"), "the bus timetable or the class schedule"), src=('timetable_kind',))),
            _say(fill("It starts at {start} and ends at {end}", _src=('elapsed_unit',), start=S(row['start'], "fill"), end=S(row['end'], "fill"))),
            fill("Count on from the start time to the end time: that is {answer} {count_noun}.", _src=('elapsed_unit',), answer=S(answer, "value:answer"), count_noun=S(count_noun(answer, noun), E((count_noun(1, noun), noun), "the noun or its singular (dna.base.count_noun)"), src=('answer', 'question',))),
        ]

    ask = values["elapsed_ask"]
    if unit == "days":
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        start, end, n = values["start_day"], values["end_day"], values["duration_days"]
        span = order[order.index(start):order.index(end) + 1]
        if len(span) != n:
            raise ValueError(
                f"time_reading.generate_hints: {start} to {end} spans {len(span)} days, "
                f"not the declared duration {n}"
            )
        if ask == "duration":
            return [
                fill("Count the days from {start} to {end}. Count both {start} and {end}.", _src=('elapsed_ask', 'elapsed_unit',), start=S(start, "value:start_day"), end=S(end, "value:end_day")),
                fill("{join}: that is {n} {count_noun}.", _src=('elapsed_ask', 'elapsed_unit',), join=S(join(", ", [S(d, E(tuple(order), "the days of the week")) for d in span]), "fill"), n=S(n, "value:duration_days"), count_noun=S(count_noun(n, 'days'), "value:elapsed_unit")),
            ]
        return [
            fill("Start on {start} and call it day 1.", _src=('elapsed_unit',), start=S(start, "value:start_day")),
            fill("Count on: {join}.", _src=('elapsed_unit',), join=S(join(", ", [fill("day {i} is {d}", i=S(i, R(1, n, "the day count, 1 to duration_days")), d=S(d, E(tuple(order), "the days of the week"))) for i, d in enumerate(span, 1)]), "fill")),
            fill("Day {n} is {end}.", _src=('elapsed_unit',), n=S(n, "value:duration_days"), end=S(end, "fill")),
        ]

    start, end = values["start_time_str"], values["end_time_str"]
    if unit == "hours":
        n = values["duration_hours"]
        if ask == "duration":
            return [
                fill("Count the hours from {start} to {end}, one hour at a time.", _src=('elapsed_ask', 'elapsed_unit',), start=S(start, "fill"), end=S(end, "value:end_time_str")),
                fill("From {start} to {end} is {n} {count_noun}.", _src=('elapsed_ask', 'elapsed_unit',), start=S(start, "fill"), end=S(end, "value:end_time_str"), n=S(n, "value:duration_hours"), count_noun=S(count_noun(n, 'hours'), "value:elapsed_unit")),
            ]
        if ask == "end_time":
            return [
                fill("Start at {start} and count on {n} {count_noun}, one hour at a time.", _src=('elapsed_ask', 'elapsed_unit',), start=S(start, "fill"), n=S(n, "value:duration_hours"), count_noun=S(count_noun(n, 'hours'), "value:elapsed_unit")),
                _say(fill("{n} {count_noun} after {start} is {end}", _src=('elapsed_ask', 'elapsed_unit',), n=S(n, "value:duration_hours"), count_noun=S(count_noun(n, 'hours'), "value:elapsed_unit"), start=S(start, "fill"), end=S(end, "fill"))),
            ]
        return [
            fill("Start at {end} and count back {n} {count_noun}, one hour at a time.", _src=('elapsed_unit',), end=S(end, "fill"), n=S(n, "value:duration_hours"), count_noun=S(count_noun(n, 'hours'), E((count_noun(1, 'hours'), 'hours'), "the noun or its singular (dna.base.count_noun)"), src=('duration_hours',))),
            _say(fill("{n} {count_noun} before {end} is {start}", _src=('elapsed_unit',), n=S(n, "value:duration_hours"), count_noun=S(count_noun(n, 'hours'), E((count_noun(1, 'hours'), 'hours'), "the noun or its singular (dna.base.count_noun)"), src=('duration_hours',)), end=S(end, "fill"), start=S(start, "fill"))),
        ]

    n = values["duration_minutes"]
    if ask == "duration":
        return [
            _say(fill("Start at {start} and count on by 5 minutes until you reach {end}", _src=('elapsed_ask',), start=S(start, "fill"), end=S(end, "value:end_time_str"))),
            fill("From {start} to {end} is {n} {count_noun}.", _src=('elapsed_ask',), start=S(start, "fill"), end=S(end, "value:end_time_str"), n=S(n, "value:duration_minutes"), count_noun=S(count_noun(n, 'minutes'), "value:elapsed_unit")),
        ]
    return [
        fill("Start at {start} and count on {n} {count_noun}, 5 minutes at a time.", start=S(start, "fill"), n=S(n, "value:duration_minutes"), count_noun=S(count_noun(n, 'minutes'), "value:elapsed_unit")),
        _say(fill("{n} {count_noun} after {start} is {end}", n=S(n, "value:duration_minutes"), count_noun=S(count_noun(n, 'minutes'), "value:elapsed_unit"), start=S(start, "fill"), end=S(end, "fill"))),
    ]


def _clock_hints(values: Dict[str, Any], cumulative_vocab: Set[str]) -> List[str]:
    minute_known = "minute" in cumulative_vocab
    hour = values["hour"]
    minute = values.get("minute", 0)

    if minute_known:
        hints = [
            fill("The short hand shows the hour. The long hand shows the minutes."),
            fill("The short (hour) hand points near {hour}.", hour=S(hour, "value:hour")),
        ]
        if minute == 0:
            hints.append(fill("The long (minute) hand points to 12, so the minutes are 00.", _src=('minute',)))
        elif minute == 30:
            hints.append(fill("The long (minute) hand points to 6, so the minutes are 30.", _src=('minute',)))
        elif minute == 15:
            hints.append(fill("The long (minute) hand points to 3, so the minutes are 15.", _src=('minute',)))
        elif minute == 45:
            hints.append(fill("The long (minute) hand points to 9, so the minutes are 45.", _src=('minute',)))
        elif minute % 5 == 0:
            marks = minute // 5
            hints.append(
                fill("Count by 5s from 12: the long hand has passed {marks} {count_noun}, so the minutes are {minute}.", _src=('minute',), marks=derived(marks, src=('minute',), why="arithmetic"), count_noun=S(count_noun(marks, 'marks'), E((count_noun(1, 'marks'), 'marks'), "the noun or its singular (dna.base.count_noun)"), src=('minute',)), minute=S(minute, "value:minute", src=('minute',)))
            )
        else:
            # A minute that is not a multiple of 5 used to be reported as "passed 4
            # marks, so the minutes are 23" -- 4 fives are 20, and no count of
            # five-minute marks reaches 23 (blind review of mat_g2_mg_q4_1). Count
            # the fives, then the single minutes after them.
            marks, extra = divmod(minute, 5)
            hints.append(
                fill("Count by 5s from 12 to the last number the long hand has passed: {marks} {count_noun} make {v} minutes.", marks=derived(marks, src=("minute",), why="arithmetic"), count_noun=S(count_noun(marks, 'fives'), E((count_noun(1, 'fives'), 'fives'), "the noun or its singular (dna.base.count_noun)")), v=derived(marks * 5, src=("minute",), why="arithmetic"))
            )
            hints.append(
                fill("Then count on the small marks one at a time: {v} + {extra} = {minute}, so the minutes are {minute}.", v=derived(marks * 5, src=("minute",), why="arithmetic"), extra=derived(extra, src=("minute",), why="arithmetic"), minute=S(minute, "value:minute"))
            )
    else:
        # G1: 'minute' hasn't been introduced yet — describe hand position with
        # 'half'/'quarter' (already known) instead of naming minutes directly.
        hints = [
            fill("The short hand shows the hour. The long hand shows how far past the hour it is."),
            fill("The short (hour) hand points near {hour}.", hour=S(hour, "value:hour")),
        ]
        if minute == 0:
            hints.append(fill("The long hand points to 12, so it is exactly on the hour.", _src=('minute',)))
        elif minute == 30:
            hints.append(fill("The long hand points to 6 — that is half past the hour.", _src=('minute',)))
        elif minute == 15:
            hints.append(fill("The long hand points to 3 — that is a quarter past the hour.", _src=('minute',)))
        elif minute == 45:
            hints.append(fill("The long hand points to 9 — that is a quarter before the next hour.", _src=('minute',)))
        else:
            marks = minute // 5
            hints.append(
                fill("Count by 5s from 12: the long hand has passed {marks} {count_noun}.", marks=derived(marks, src=('minute',), why="arithmetic"), count_noun=S(count_noun(marks, 'marks'), E((count_noun(1, 'marks'), 'marks'), "the noun or its singular (dna.base.count_noun)"), src=('minute',)))
            )

    hints.append(_say(fill("The time is {time_str}", time_str=S(values['time_str'], "value:time_str"))))
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
