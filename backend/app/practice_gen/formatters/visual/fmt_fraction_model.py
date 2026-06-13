"""
fmt_fraction_model.py — FractionModel visual formatter

NEW formatter — no existing analog in visual_skeletons.py.

Shows a fraction as one of three model types:
    area     — rectangle divided into equal parts, some shaded
    set      — circle groups (objects in groups, some highlighted)
    number_line — fraction marked on a 0–1 or 0–2 number line

interaction_mode:
    "read" — model is shown; student identifies the fraction
    "set"  — student shades the correct number of parts (answer_collection="click")

visual_params:
    {
        "model_type":    "area" | "set" | "number_line",
        "numerator":     int,
        "denominator":   int,
        "total_parts":   int,   # == denominator for area/set
        "shaded_parts":  int,   # == numerator
        "fraction_str":  str,   # e.g. "3/4"
    }

Grade limits:
    G1 — only 1/2 and 1/4 (unit fractions of halves/fourths)
    G2 — unit fractions, denominators 2–8
    G3+ — any proper fraction with denominators 2–10

Traps: swap numerator/denominator, count total parts, count unshaded parts.
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# ─────────────────────────────────────────────────────────────────────────────
# Grade-gated fraction pools
# ─────────────────────────────────────────────────────────────────────────────

def _pick_fraction(grade: int, rng: random.Random) -> tuple:
    """
    Return (numerator, denominator) appropriate for the grade.

    G1: unit fractions of halves and fourths (1/2, 1/4) only.
    G2: unit fractions with denominator 2–8.
    G3+: any proper fraction, denominator 2–10.
    """
    if grade <= 1:
        denom = rng.choice([2, 4])
        return 1, denom

    if grade == 2:
        denom = rng.choice([2, 3, 4, 5, 6, 8])
        return 1, denom

    denom = rng.choice([2, 3, 4, 5, 6, 8, 10])
    numer = rng.randint(1, denom - 1)
    return numer, denom


def _pick_model_type(grade: int, rng: random.Random) -> str:
    if grade <= 1:
        return "area"
    return rng.choice(["area", "set", "number_line"])


# ─────────────────────────────────────────────────────────────────────────────
# Traps
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(numer: int, denom: int) -> list:
    """
    Return up to 3 pedagogically meaningful wrong answers (fraction strings).

    Traps:
        swap_nd        — denominator/numerator (swap)
        count_total    — total parts = denominator (ignores shading)
        count_unshaded — unshaded parts / denominator
        off_by_one_num — (numer ± 1) / denom
    """
    traps = []
    correct = f"{numer}/{denom}"
    seen = {correct}

    # Swap numerator and denominator
    swap = f"{denom}/{numer}"
    if swap not in seen and numer != denom:
        traps.append(swap)
        seen.add(swap)

    # Count all parts (use denom as "answer")
    total_trap = f"{denom}/{denom}"
    if total_trap not in seen:
        traps.append(total_trap)
        seen.add(total_trap)

    # Count unshaded parts
    unshaded = denom - numer
    unshaded_str = f"{unshaded}/{denom}"
    if unshaded_str not in seen and unshaded != numer:
        traps.append(unshaded_str)
        seen.add(unshaded_str)

    # Off by one in numerator
    if numer > 1:
        ob1 = f"{numer - 1}/{denom}"
        if ob1 not in seen:
            traps.append(ob1)

    return traps[:3]


# ─────────────────────────────────────────────────────────────────────────────
# Question text
# ─────────────────────────────────────────────────────────────────────────────

def _stem(model_type: str, fraction_str: str, interaction_mode: str) -> str:
    if interaction_mode == "set":
        return f"Shade the model to show {fraction_str}."
    model_names = {"area": "area model", "set": "set model", "number_line": "number line"}
    name = model_names.get(model_type, "model")
    return f"What fraction does the {name} show?"


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_fraction_model(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a FractionModel FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Model pre-drawn; student identifies the fraction shown.
    interaction_mode "set":
        Student shades parts of the model to match a given fraction.
        answer_collection is overridden to "click".

    Pulls numerator / denominator from ctx.values when available.
    """
    diff_level = 2
    if ctx.difficulty_profile:
        diff_level = min(len(ctx.difficulty_profile) + 1, 4)

    # ── 1. Resolve fraction ───────────────────────────────────────────────────
    if ctx.visual_params and "numerator" in ctx.visual_params:
        numer = ctx.visual_params["numerator"]
        denom = ctx.visual_params["denominator"]
        model_type = ctx.visual_params.get("model_type", "area")
    elif ctx.values and "numerator" in ctx.values:
        numer = ctx.values["numerator"]
        denom = ctx.values["denominator"]
        model_type = ctx.values.get("model_type") or _pick_model_type(ctx.grade, rng)
    else:
        numer, denom = _pick_fraction(ctx.grade, rng)
        model_type = _pick_model_type(ctx.grade, rng)

    # Enforce grade limits
    if ctx.grade <= 1:
        denom = min(denom, 4) if denom in (2, 4) else 4
        numer = 1
        model_type = "area"

    fraction_str = f"{numer}/{denom}"

    if interaction_mode == "set":
        answer_collection = "click"

    vp = {
        "model_type": model_type,
        "numerator": numer,
        "denominator": denom,
        "total_parts": denom,
        "shaded_parts": numer,
        "fraction_str": fraction_str,
    }

    # ── 2. Correct answer ─────────────────────────────────────────────────────
    correct_answer = fraction_str

    # ── 3. Traps ──────────────────────────────────────────────────────────────
    traps = _build_traps(numer, denom)

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

    question_text = _stem(model_type, fraction_str, interaction_mode)

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_fractionmodel",
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
        visual_type="FractionModel",
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
