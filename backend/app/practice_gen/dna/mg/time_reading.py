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
        # mg_q4_2) had no matching task_type at all -- every other branch
        # in this DNA reads/sets a SINGLE clock time, never computes a
        # duration between two, so the co-mapped `subtraction` DNA (a bare
        # whole-number subtraction skill with no time/clock awareness)
        # filled the gap with off-topic content instead (blind review: "9
        # of 17 samples are off-topic pictograph subtraction-comparison
        # word problems... zero connection to minutes/hours/days/
        # timetables"). Picks a start time and a whole-minutes duration
        # (capped at 120 so at most one a.m./p.m. boundary is ever
        # crossed, keeping the modular hour math exact), computes the end
        # time, and asks for whichever of duration/end-time the profile
        # doesn't already fix -- covering both "how long did it last?" and
        # "what time will it end?" problem shapes.
        start_hour = rng.randint(1, 12)
        start_minute = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
        duration_minutes = rng.choice([5, 10, 15, 20, 25, 30, 40, 45, 50, 60, 75, 90, 120])
        # validate_matrix's §1C exhaustive sweep force-tests every
        # formatter this DNA declares compatible (now including mcq/cloze
        # for this task_type) against EVERY node mapped to time_reading,
        # not just the one node (mat_g2_mg_q4_2, grade 2) this task_type
        # is registry-bound to -- so this branch must stay correct even
        # when called for a grade-1 node. a.m./p.m. is NOT_YET_KNOWN
        # vocabulary at G1 (same gate the default path below already
        # applies), so it silently leaked through here unconditionally
        # (blind review/harness: "[NOT_YET_KNOWN] Forbidden term 'p.m.'").
        use_ampm = grade >= 2
        start_period = rng.choice(["a.m.", "p.m."]) if use_ampm else None

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

        def _fmt_time(h: int, m: int, p: Optional[str]) -> str:
            return f"{h}:{m:02d}" + (f" {p}" if p else "")

        start_str = _fmt_time(start_hour, start_minute, start_period)
        end_str = _fmt_time(end_hour, end_minute, end_period)

        activity = rng.choice([
            "a recess", "a class", "a movie", "a bus ride",
            "a study session", "a swimming lesson", "a soccer practice",
        ])
        ask = profile.get("elapsed_ask") or rng.choice(["duration", "end_time"])
        if ask == "duration":
            # end_str sometimes ends in "a.m."/"p.m." (its own trailing
            # period) -- appending a sentence-final "." unconditionally
            # produced "...ended at 11:10 p.m.. How many..." (double
            # period), the same defect already fixed once in fmt_clock.py's
            # "set" stem for the identical reason.
            trailing = "" if end_str.endswith(".") else "."
            question = (
                f"{activity.capitalize()} started at {start_str} and ended "
                f"at {end_str}{trailing} How many minutes did it last?"
            )
            answer: Any = duration_minutes
            blank_target = "duration_minutes"
            # base_generator's shared error-pattern loop can't derive
            # distractors here (this DNA's error_patterns are all
            # formula="None", hour/minute misconception LABELS with no
            # computable formula), so a numeric-answer task_type would
            # reach fmt_mcq.py with zero candidates and rely entirely on
            # its own +-1/+-10 padding fallback -- fine for a duration
            # value, but explicit plausible minute-arithmetic traps are
            # more pedagogically meaningful than arbitrary offsets.
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
            blank_target = "end_time_str"
            # A string correct_answer gives fmt_mcq.py no numeric fallback
            # path at all (it raises immediately if candidates run short),
            # so explicit distractors are mandatory here, not just
            # nice-to-have: off-by-one-hour and off-by-ten-minutes are
            # exactly the "read the wrong hand" and "miscounted minutes"
            # errors this DNA's own error_patterns already name.
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
            "task_type": "elapsed_time",
            "start_time_str": start_str,
            "end_time_str": end_str,
            "duration_minutes": duration_minutes,
            "question": question,
            "blank_target": blank_target,
            "answer": answer,
            "distractors": distractors,
            # Populated for any shared consumer (generate_hints, base_
            # generator fallbacks) that expects the usual single-clock keys.
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

    hour = rng.randint(bounds["hour"][0], bounds["hour"][1])

    if precision == "hour":
        minute = 0
    elif precision == "half_hour":
        minute = rng.choice([0, 30])
    elif precision == "quarter_hour":
        minute = rng.choice([0, 15, 30, 45])
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
        # "Solve problems involving time" (mat_g1_mg_q4_4) previously had
        # no word-problem framing at all -- this DNA has no "context"
        # handling anywhere, so it always rendered the bare clock-reading
        # stem ("What time does the clock show?") regardless of the
        # competency asking for solved *problems*. A self-contained
        # narrative here (as with length_measurement's equivalent fix)
        # avoids routing through the shared spine system for a single-value
        # read that has no second quantity to combine/compare.
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
