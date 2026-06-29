"""
fmt_clock.py — ClockSet visual formatter

Produces a FormattedProblem with clock visual_params.
Carves all generation logic from visual_skeletons.py _gen_clock_set /
_traps_clock_set; does NOT import from that module.

interaction_mode:
    "read" — clock is pre-set; student identifies the time
    "set"  — student drags hands to show a given time

answer_collection:
    "mcq"            — 4 time-string options (correct + 3 trap times)
    "fill_in_blank"  — student types "H:MM" or "HH:MM"
"""

import random
from typing import Optional

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _time_str(hours: int, minutes: int, use_24: bool) -> str:
    if use_24:
        return f"{hours:02d}:{minutes:02d}"
    return f"{hours}:{minutes:02d}"


def _build_traps(hours: int, minutes: int, use_24: bool, rng: random.Random) -> dict:
    """
    Return trap dict mirroring visual_skeletons._traps_clock_set logic.

    Keys: hour_minute_swap, off_by_one_hour_up, off_by_one_hour_down,
          off_by_five_minutes_down, off_by_five_minutes_up, hour_hand_rounded
    """
    traps = {}
    display_hours = hours % 12 or 12  # 1-12 face value

    # Hour-minute swap (only when minutes ≤ 12)
    if minutes <= 12:
        traps["hour_minute_swap"] = (minutes, hours)

    # Off by one hour on the clock face
    hour_up_face = (display_hours % 12) + 1      # 12 → 1, 1..11 → 2..12
    hour_down_face = display_hours - 1 if display_hours > 1 else 12

    if use_24:
        is_pm = hours >= 12
        def _to_24(face_h):
            if face_h == 12:
                return 12 if is_pm else 0
            return face_h + 12 if is_pm else face_h

        traps["off_by_one_hour_up"] = (_to_24(hour_up_face), minutes)
        traps["off_by_one_hour_down"] = (_to_24(hour_down_face), minutes)
    else:
        traps["off_by_one_hour_up"] = (hour_up_face, minutes)
        traps["off_by_one_hour_down"] = (hour_down_face, minutes)

    # Off by 5 minutes
    if minutes >= 5:
        traps["off_by_five_minutes_down"] = (hours, minutes - 5)
    if minutes <= 54:
        traps["off_by_five_minutes_up"] = (hours, minutes + 5)

    # Hour hand rounded to nearest hour mark (only meaningful when minutes != 0)
    if minutes != 0:
        nearest_face = display_hours if minutes < 30 else (display_hours % 12) + 1
        if nearest_face == 0:
            nearest_face = 12
        if use_24:
            is_pm = hours >= 12
            trap_h = _to_24(nearest_face)
        else:
            trap_h = nearest_face
        if trap_h != hours:
            traps["hour_hand_rounded"] = (trap_h, minutes)

    return traps


def _trap_time_strings(
    traps: dict, use_24: bool, correct_tuple: tuple, rng: random.Random
) -> list:
    """
    Extract up to 3 distinct trap time-strings (excluding the correct answer).
    """
    seen = {_time_str(*correct_tuple, use_24)}
    options = []
    for h, m in traps.values():
        if not (0 <= m <= 59):
            continue
        s = _time_str(h, m, use_24)
        if s not in seen:
            seen.add(s)
            options.append(s)
        if len(options) == 3:
            break
    # Pad with synthetic distractors if needed
    h0, m0 = correct_tuple
    offsets = [(-1, 0), (1, 0), (0, -5), (0, 5), (-2, 0), (2, 0)]
    for dh, dm in offsets:
        if len(options) >= 3:
            break
        nh = (h0 + dh) % (24 if use_24 else 12)
        if not use_24 and nh == 0:
            nh = 12
        nm = m0 + dm
        if not (0 <= nm <= 59):
            continue
        s = _time_str(nh, nm, use_24)
        if s not in seen:
            seen.add(s)
            options.append(s)
    return options


# ─────────────────────────────────────────────────────────────────────────────
# Visual-params builder (pure, no QuestionContext dependency)
# ─────────────────────────────────────────────────────────────────────────────

def _build_visual_params(
    grade: int, diff_level: int, rng: random.Random
) -> dict:
    """
    Generate clock visual_params deterministically from (grade, diff_level, rng).

    Returns a dict with keys:
        hours, minutes, display_hours, minute_angle, hour_angle,
        target_time, use_24_hour, minute_snap_interval
    """
    use_24 = grade >= 5

    if diff_level == 1:
        hours = rng.randint(0, 23) if use_24 else rng.randint(1, 12)
        minutes = rng.choice([0, 30])
    elif diff_level == 2:
        hours = rng.randint(0, 23) if use_24 else rng.randint(1, 12)
        minutes = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    else:
        hours = rng.randint(0, 23) if use_24 else rng.randint(1, 12)
        minutes = rng.randint(0, 59)

    display_hours = hours % 12 or 12

    minute_angle = (minutes / 60) * 360
    hour_angle = ((display_hours % 12) / 12) * 360 + (minutes / 60) * 30

    return {
        "hours": hours,
        "minutes": minutes,
        "display_hours": display_hours,
        "target_time": _time_str(hours, minutes, use_24),
        "use_24_hour": use_24,
        "minute_angle": minute_angle,
        "hour_angle": hour_angle,
        "minute_snap_interval": 5,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_clock(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a ClockSet FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Clock is shown in a pre-set position; student identifies the time.
    interaction_mode "set":
        Student is given a time string and must drag clock hands to match.

    answer_collection "mcq":
        Four time-string choices (1 correct + 3 trap-derived distractors).
    answer_collection "fill_in_blank":
        Student types the time in H:MM or HH:MM format.
    """
    # ── 1. Resolve time values ────────────────────────────────────────────────
    # Prefer values already in ctx (pre-generated by context generator), else
    # synthesise from ctx.seed and ctx.grade.
    if ctx.visual_params and "hours" in ctx.visual_params:
        vp = ctx.visual_params.copy()
        hours = vp["hours"]
        minutes = vp["minutes"]
        use_24 = vp.get("use_24_hour", ctx.grade >= 5)
    elif ctx.values and "hour" in ctx.values:
        hours = ctx.values["hour"]
        minutes = ctx.values.get("minute", 0)
        use_24 = False
        vp = {
            "hours": hours,
            "minutes": minutes,
            "display_hours": hours,
            "target_time": f"{hours}:{minutes:02d}",
            "use_24_hour": use_24,
            "minute_angle": (minutes / 60) * 360,
            "hour_angle": ((hours % 12) / 12) * 360 + (minutes / 60) * 30,
            "minute_snap_interval": 5,
        }
    else:
        # Derive difficulty level from ctx (1–4 int scale)
        _difficulty_map = {1: 1, 2: 2, 3: 3, 4: 4}
        diff_profile = ctx.difficulty_profile or {}
        # Use seed-seeded RNG to produce a stable visual for this ctx
        _local_rng = random.Random(ctx.seed)
        diff_level = _difficulty_map.get(
            len(diff_profile), 2
        )
        vp = _build_visual_params(ctx.grade, diff_level, _local_rng)
        hours = vp["hours"]
        minutes = vp["minutes"]
        use_24 = vp["use_24_hour"]

    correct_tuple = (hours, minutes)
    time_str = _time_str(hours, minutes, use_24)
    traps = _build_traps(hours, minutes, use_24, rng)

    # ── 2. Build question text ────────────────────────────────────────────────
    if interaction_mode == "read":
        if use_24:
            question_text = "What time does the clock show? Give the time in 24-hour format."
        else:
            question_text = "What time does the clock show?"
    else:  # "set"
        if use_24:
            question_text = f"Set the clock to show {time_str} (24-hour time)."
        else:
            question_text = f"Set the clock to show {time_str}."

    # ── 3. Answer collection ──────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        distractor_strings = _trap_time_strings(traps, use_24, correct_tuple, rng)
        all_options = [time_str] + distractor_strings[:3]
        rng.shuffle(all_options)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": opt, "is_correct": opt == time_str}
            for i, opt in enumerate(all_options)
        ]
        correct_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        correct_answer = time_str

    # ── 4. Assemble visual_params ─────────────────────────────────────────────
    visual_params = {
        "hours": hours,
        "minutes": minutes,
        "correct_time": {"hour": hours, "minute": minutes},
        "display_hours": vp.get("display_hours", hours % 12 or 12),
        "target_time": time_str,
        "use_24_hour": use_24,
        "minute_angle": vp.get("minute_angle", (minutes / 60) * 360),
        "hour_angle": vp.get("hour_angle", ((hours % 12) / 12) * 360 + (minutes / 60) * 30),
        "minute_snap_interval": 5,
        "interaction_mode": interaction_mode,
        "is_read_only": interaction_mode == "read",
        "show_labels": True,
        "precision": "5min" if minutes % 5 == 0 else "1min",
    }

    # ── 5. format_data ────────────────────────────────────────────────────────
    format_data: dict = {
        "visual_params": visual_params,
        "time_str": time_str,
    }
    if mcq_options is not None:
        format_data["mcq_options"] = mcq_options

    fmt = f"{interaction_mode}_{answer_collection}"

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_clockset",
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
        visual_type="ClockSet",
        visual_params=visual_params,
        interaction_mode=interaction_mode,
        answer_collection=answer_collection,
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
    )
