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
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors


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
    if len(traps) < 3:
        traps = augment_distractors(traps, length, target=3, max_delta=5)
        if len(traps) < 3:
            raise ValueError(f"Formatter 'ruler_measure' requires at least 3 unique distractors, but got {len(traps)}")
    return traps[:3]


# ─────────────────────────────────────────────────────────────────────────────
# Question text
# ─────────────────────────────────────────────────────────────────────────────

def _stem(params: dict, interaction_mode: str, custom_question: str = None) -> str:
    unit_name = params["unit_name"]
    length = params["length"]
    if interaction_mode == "set":
        return f"Drag the end of the object to show a length of {length} {unit_name}."
    if custom_question:
        # The DNA already computed a specific question (e.g. word-problem
        # framing for "solve problems involving lengths" nodes) -- the
        # generic ruler-reading stem below discarded it unconditionally,
        # so a "solve problems" node could still render a bare "how long
        # is the object" reading task with no problem-solving content
        # whenever this formatter got picked (blind review of
        # mat_g1_mg_q2_2 seed 55).
        return custom_question
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

    custom_question = (ctx.values or {}).get("question")
    dna_answer = (ctx.values or {}).get("answer")

    # ── 2. Correct answer ─────────────────────────────────────────────────────
    # A custom question (word-problem framing, e.g. "how many longer is a
    # book than a notebook?") can ask something other than "how long is the
    # object" -- params["length"] is always the raw ruler reading, not
    # necessarily what that question is asking for. When the DNA has already
    # computed a different answer for its own question, that answer is the
    # one actually being asked about (found by blind review: the "book is 5,
    # notebook is 1, how many longer" question kept serving 5 as "correct"
    # instead of the true 5-1=4).
    uses_dna_answer = (
        custom_question is not None
        and dna_answer is not None
        and dna_answer != params["length"]
    )
    correct_answer = dna_answer if uses_dna_answer else params["length"]

    # ── 3. Traps ──────────────────────────────────────────────────────────────
    # The ruler-specific traps (misread the start, read the ruler's end
    # value) are misreadings of *the ruler*, meaningless for a question that
    # isn't "how long is the object" -- fall back to generic near-neighbor
    # distractors around the actual answer instead.
    if uses_dna_answer:
        traps = augment_distractors([], correct_answer, target=3, max_delta=5)
    else:
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

    question_text = _stem(params, interaction_mode, custom_question=custom_question)

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
        given_values={k: v for k, v in ctx.values.items() if k != ctx.blank_target} if ctx.values else None,
        blank_target=ctx.blank_target,
    )
