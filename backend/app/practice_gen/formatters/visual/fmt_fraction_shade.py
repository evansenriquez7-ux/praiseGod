"""
fmt_fraction_shade.py — FractionShade visual formatter

NEW formatter — gap analysis addition.
Does NOT import from visual_skeletons.py.

Shows a shape divided into equal parts, some of which are shaded.

interaction_mode:
    "read" — shaded shape shown; student identifies the fraction (e.g. "3/4")
    "set"  — student shades the correct number of parts (answer_collection="click")

visual_params:
    {
        "shape":        "bar" | "circle" | "rectangle",
        "total_parts":  int,
        "shaded_parts": int,
        "fraction_str": str,    # e.g. "3/4"
        "ask_type":     "identify_fraction" | "shade_this_fraction" | "compare",
    }

Traps:
    swap_nd       — numerator and denominator swapped (e.g. 4/3 instead of 3/4)
    count_total   — total_parts as numerator (ignores shaded vs total distinction)
    count_unshaded— (total - shaded) / total
    off_by_one_num— (shaded ± 1) / total
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# ─────────────────────────────────────────────────────────────────────────────
# Grade-gated denominator pools (mirrors fractions DNA)
# ─────────────────────────────────────────────────────────────────────────────

_DENOM_POOLS = {
    1: [2, 4],
    2: [2, 3, 4, 5, 6, 8],
    3: [2, 3, 4, 5, 6, 8, 10],
}

_SHAPES = ["bar", "circle", "rectangle"]


def _pick_params(grade: int, diff_level: int, rng: random.Random) -> dict:
    pool = _DENOM_POOLS.get(grade, _DENOM_POOLS[3])
    denom = rng.choice(pool)
    if grade <= 1:
        numer = 1
    else:
        numer = rng.randint(1, denom - 1)
    shape = rng.choice(_SHAPES)
    return {
        "shape": shape,
        "total_parts": denom,
        "shaded_parts": numer,
        "fraction_str": f"{numer}/{denom}",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Traps
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(numer: int, denom: int) -> list:
    """
    Return up to 3 distractor fraction strings.

    Traps:
        swap_nd        — denom/numer
        count_total    — denom/denom  (student counts all parts)
        count_unshaded — (denom-numer)/denom
        off_by_one_num — (numer-1)/denom
    """
    correct = f"{numer}/{denom}"
    traps = []
    seen = {correct}

    # Swap
    swap = f"{denom}/{numer}"
    if swap not in seen and numer != denom:
        traps.append(swap)
        seen.add(swap)

    # Total parts
    total_trap = f"{denom}/{denom}"
    if total_trap not in seen:
        traps.append(total_trap)
        seen.add(total_trap)

    # Unshaded
    unshaded = denom - numer
    unshaded_str = f"{unshaded}/{denom}"
    if unshaded_str not in seen and unshaded != numer and unshaded > 0:
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

def _stem(ask_type: str, fraction_str: str, interaction_mode: str) -> str:
    if interaction_mode == "set" or ask_type == "shade_this_fraction":
        return f"Shade {fraction_str} of the shape."
    if ask_type == "compare":
        return "Which fraction is larger?"
    return "What fraction of the shape is shaded?"


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_fraction_shade(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a FractionShade FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Shaded shape displayed; student identifies the fraction.
    interaction_mode "set":
        Student clicks/taps parts of the shape to shade the correct fraction.
        answer_collection is overridden to "click".

    Pulls from ctx.values (fractions DNA) when available.
    Keys used: numerator, denominator, model_type (for shape).
    """
    diff_level = 2
    if ctx.difficulty_profile:
        diff_level = min(len(ctx.difficulty_profile) + 1, 4)

    # ── 1. Resolve params ─────────────────────────────────────────────────────
    if ctx.visual_params and "total_parts" in ctx.visual_params:
        vp_in = ctx.visual_params
        numer = vp_in["shaded_parts"]
        denom = vp_in["total_parts"]
        shape = vp_in.get("shape", "bar")
        ask_type = vp_in.get("ask_type", "identify_fraction")
    elif ctx.values and "numerator" in ctx.values:
        numer = ctx.values["numerator"]
        denom = ctx.values["denominator"]
        shape = ctx.values.get("shape", rng.choice(_SHAPES))
        ask_type = ctx.values.get("ask_type", "identify_fraction")
    else:
        raw = _pick_params(ctx.grade, diff_level, rng)
        numer = raw["shaded_parts"]
        denom = raw["total_parts"]
        shape = raw["shape"]
        ask_type = "identify_fraction" if interaction_mode == "read" else "shade_this_fraction"

    if interaction_mode == "set":
        ask_type = "shade_this_fraction"
        answer_collection = "click"

    fraction_str = f"{numer}/{denom}"

    vp = {
        "shape": shape,
        "total_parts": denom,
        "shaded_parts": numer,
        "fraction_str": fraction_str,
        "ask_type": ask_type,
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

    question_text = _stem(ask_type, fraction_str, interaction_mode)

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_fractionshade",
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
        visual_type="FractionShade",
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
