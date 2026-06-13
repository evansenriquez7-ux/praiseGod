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
    "mode":         ["read", "set"],
    "include_ampm": ["no_ampm", "with_ampm"],
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
    difficulty_profile: Optional[Dict[str, str]],
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
    precision = profile.get("precision", "hour")

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

    include_ampm = profile.get("include_ampm", "no_ampm") == "with_ampm"
    if include_ampm:
        period = rng.choice(["a.m.", "p.m."])
        time_str = f"{time_str} {period}"
    else:
        period = None

    return {
        "hour": hour,
        "minute": minute,
        "time_str": time_str,
        "precision": precision,
        "period": period,
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    hints = [
        "The short hand shows the hour. The long hand shows the minutes.",
        f"The short (hour) hand points near {values['hour']}.",
    ]
    minute = values.get("minute", 0)
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
