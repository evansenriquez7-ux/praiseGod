"""
fmt_ruler_measure.py — RulerMeasure visual formatter

NEW formatter — partial analog exists in GridArea (visual_skeletons.py).
Does NOT import from visual_skeletons.py.

Shows a ruler with an object placed on it.

interaction_mode:
    "read" — ruler and object shown; student reads the measurement
    "set"  — student drags the object's end point to a given length

visual_params:
    {
        "ruler_start":  int,            # usually 0
        "ruler_end":    int,            # e.g. 20 for a 20 cm ruler
        "unit":         "cm" | "m" | "non_standard",
        "object_start": int,            # where the object begins on the ruler
        "object_end":   int,            # where the object ends
        "length":       int,            # object_end - object_start
        "unit_name":    str,            # "cm", "m", "paperclips", "hand spans", "steps"
    }

For non-standard units the unit_name is "paperclips", "hand spans", or "steps".

Traps:
    misread_start   — reads from 0 even when object_start ≠ 0 (off by object_start)
    off_by_one      — length ± 1
    ruler_end_value — reads ruler_end as the length
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# ─────────────────────────────────────────────────────────────────────────────
# Grade-appropriate ruler configuration
# ─────────────────────────────────────────────────────────────────────────────

_NON_STANDARD_UNITS = ["paperclips", "hand spans", "steps"]


def _build_ruler_params(grade: int, diff_level: int, rng: random.Random) -> dict:
    """
    Generate ruler + object placement for the given grade.

    G1:   non-standard units (paperclips), object always starts at 0
    G2:   cm ruler 0-20, object may start at 0
    G3+:  cm ruler with offset start (measures from non-zero); or m ruler
    """
    if grade <= 1:
        unit = "non_standard"
        unit_name = rng.choice(_NON_STANDARD_UNITS)
        ruler_end = 10
        object_start = 0
        length = rng.randint(1, 8)
        object_end = length
    elif grade == 2:
        unit = "cm"
        unit_name = "cm"
        ruler_end = 20
        object_start = 0 if diff_level == 1 else rng.randint(1, 5)
        length = rng.randint(2, ruler_end - object_start - 1)
        object_end = object_start + length
    else:
        # G3+: cm with offset, or m
        use_m = diff_level >= 3 and rng.choice([True, False])
        if use_m:
            unit = "m"
            unit_name = "m"
            ruler_end = 10
            object_start = rng.randint(0, 3)
            length = rng.randint(1, ruler_end - object_start - 1)
        else:
            unit = "cm"
            unit_name = "cm"
            ruler_end = 30
            object_start = rng.randint(1, 10)
            length = rng.randint(2, ruler_end - object_start - 1)
        object_end = object_start + length

    return {
        "ruler_start": 0,
        "ruler_end": ruler_end,
        "unit": unit,
        "object_start": object_start,
        "object_end": object_end,
        "length": length,
        "unit_name": unit_name,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Traps
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(params: dict, rng: random.Random) -> list:
    """
    Return up to 3 distractor values.

    Traps:
        misread_start   — student reads object_end instead of length
                          (only when object_start != 0)
        off_by_one_high — length + 1
        off_by_one_low  — length - 1
        ruler_end_value — uses ruler_end as answer
    """
    length = params["length"]
    object_end = params["object_end"]
    ruler_end = params["ruler_end"]
    object_start = params["object_start"]
    traps = []
    seen = {length}

    # Misread start: student reads object_end as the length
    if object_start != 0 and object_end not in seen:
        traps.append(object_end)
        seen.add(object_end)

    # Off by one
    for delta in (1, -1):
        candidate = length + delta
        if candidate > 0 and candidate not in seen:
            traps.append(candidate)
            seen.add(candidate)
        if len(traps) >= 3:
            break

    # Ruler end value
    if ruler_end not in seen and ruler_end != length:
        traps.append(ruler_end)

    rng.shuffle(traps)
    return traps[:3]


# ─────────────────────────────────────────────────────────────────────────────
# Question text
# ─────────────────────────────────────────────────────────────────────────────

def _stem(params: dict, interaction_mode: str) -> str:
    unit_name = params["unit_name"]
    length = params["length"]
    if interaction_mode == "set":
        return f"Drag the end of the object to show a length of {length} {unit_name}."
    return f"How long is the object? Give your answer in {unit_name}."


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_ruler_measure(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a RulerMeasure FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Ruler shown with object placed; student reads the measurement.
    interaction_mode "set":
        Student drags the object's end point to represent a given length.

    Pulls from ctx.values (length_measurement DNA) when available.
    Keys used: length, unit, ruler_end, object_start.
    """
    diff_level = 2
    if ctx.difficulty_profile:
        diff_level = min(len(ctx.difficulty_profile) + 1, 4)

    # ── 1. Resolve params ─────────────────────────────────────────────────────
    if ctx.visual_params and "length" in ctx.visual_params:
        params = ctx.visual_params.copy()
    elif ctx.values and "length" in ctx.values:
        length = int(ctx.values["length"])
        unit = ctx.values.get("unit", "cm")
        unit_name = ctx.values.get("unit_name", unit)
        ruler_end = ctx.values.get("ruler_end", max(20, length + 5))
        object_start = ctx.values.get("object_start", 0)
        params = {
            "ruler_start": 0,
            "ruler_end": int(ruler_end),
            "unit": unit,
            "object_start": int(object_start),
            "object_end": int(object_start) + length,
            "length": length,
            "unit_name": unit_name,
        }
    else:
        params = _build_ruler_params(ctx.grade, diff_level, rng)

    vp = {k: params[k] for k in ("ruler_start", "ruler_end", "unit", "object_start", "object_end", "length", "unit_name")}

    # ── 2. Correct answer ─────────────────────────────────────────────────────
    correct_answer = params["length"]

    # ── 3. Traps ──────────────────────────────────────────────────────────────
    traps = _build_traps(params, rng)

    # ── 4. MCQ options ────────────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        all_opts = [correct_answer] + traps[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_answer}
            for i, v in enumerate(all_opts)
        ]
        final_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        final_answer = correct_answer

    question_text = _stem(params, interaction_mode)

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_rulermeasure",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=final_answer,
        distractors=traps,
        hints=ctx.hints,
        format=f"{interaction_mode}_{answer_collection}",
        format_data=format_data,
        is_visual=True,
        visual_type="RulerMeasure",
        visual_params=vp,
        interaction_mode=interaction_mode,
        answer_collection=answer_collection,
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
    )
