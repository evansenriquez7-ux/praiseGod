"""
fmt_place_value_blocks.py — PlaceValueBlocks visual formatter

NEW formatter — no existing analog in visual_skeletons.py.

Base-10 block representation:
    ones     — unit cubes
    tens     — rods (10 cubes)
    hundreds — flats (10 rods)
    thousands— large cubes (10 flats)

interaction_mode:
    "read" — blocks are shown; student counts/identifies the number
    "set"  — student arranges blocks to represent a given number

visual_params:
    {
        "thousands":     int,
        "hundreds":      int,
        "tens":          int,
        "ones":          int,
        "total_value":   int,
        "question_type": "read_blocks" | "build_number" | "identify_place",
    }

Grade constraints:
    G1 — tens + ones only (max 99)
    G2 — hundreds + tens + ones (max 999)
    G3 — thousands + hundreds + tens + ones (max 9999)
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors


# ─────────────────────────────────────────────────────────────────────────────
# Block decomposition
# ─────────────────────────────────────────────────────────────────────────────

def _decompose(number: int, grade: int) -> dict:
    """
    Break number into place-value blocks appropriate for the grade.
    Returns dict with keys: thousands, hundreds, tens, ones, total_value.
    """
    n = int(number)
    if grade >= 3:
        thousands, remainder = divmod(n, 1000)
    else:
        thousands, remainder = 0, n

    if grade >= 2:
        hundreds, remainder = divmod(remainder, 100)
    else:
        hundreds, remainder = 0, remainder

    tens, ones = divmod(remainder, 10)
    return {
        "thousands": thousands,
        "hundreds": hundreds,
        "tens": tens,
        "ones": ones,
        "total_value": n,
    }


def _grade_max(grade: int) -> int:
    if grade <= 1:
        return 99
    if grade == 2:
        return 999
    return 9999


def _grade_min(grade: int) -> int:
    """Return a minimum that guarantees at least one tens digit."""
    return 10 if grade <= 1 else 100 if grade == 2 else 1000


# ─────────────────────────────────────────────────────────────────────────────
# Traps
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(blocks: dict, rng: random.Random) -> list:
    """
    Return up to 3 distractor values.

    Traps:
        swap_tens_ones      — swap tens and ones digit values
        off_by_ten          — add or subtract one ten
        off_by_hundred      — add or subtract one hundred (G2+)
        count_blocks_not_value — total block count instead of place value
    """
    total = blocks["total_value"]
    traps = set()

    # Swap tens and ones
    swapped = (blocks["thousands"] * 1000
               + blocks["hundreds"] * 100
               + blocks["ones"] * 10
               + blocks["tens"])
    if swapped != total and swapped > 0:
        traps.add(swapped)

    # Off by one ten
    for delta in (-10, 10):
        candidate = total + delta
        if candidate > 0 and candidate != total:
            traps.add(candidate)
            break

    # Off by one hundred
    if blocks["hundreds"] > 0 or blocks["thousands"] > 0:
        for delta in (-100, 100):
            candidate = total + delta
            if candidate > 0 and candidate != total and candidate not in traps:
                traps.add(candidate)
                break

    # Total block count (sum of all block quantities)
    block_count = blocks["thousands"] + blocks["hundreds"] + blocks["tens"] + blocks["ones"]
    if block_count != total and block_count > 0:
        traps.add(block_count)

    traps_list = [t for t in traps if t != total]
    
    # Fill in if we don't have enough traps
    # Fill in if we don't have enough traps
    offset_mult = 1
    while len(traps_list) < 3:
        for sign in [1, -1]:
            candidate = total + offset_mult * sign
            if candidate > 0 and candidate != total and candidate not in traps_list:
                traps_list.append(candidate)
                if len(traps_list) >= 3:
                    break
        offset_mult += 1
            
    rng.shuffle(traps_list)
    return traps_list[:3]


# ─────────────────────────────────────────────────────────────────────────────
# Question text
# ─────────────────────────────────────────────────────────────────────────────

def _stem(blocks: dict, question_type: str, interaction_mode: str) -> str:
    total = blocks["total_value"]
    if interaction_mode == "set" or question_type == "build_number":
        return f"Use base-10 blocks to show the number {total}."
    if question_type == "identify_place":
        # Ask about a specific digit's place value
        return "What is the value of the underlined digit in the number shown by the blocks?"
    # read_blocks — default
    return "What number do the blocks show?"


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_place_value_blocks(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a PlaceValueBlocks FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Blocks are displayed; student identifies the total value (or a digit's
        place value).
    interaction_mode "set":
        Student arranges blocks to represent a given number.

    Derives block counts from ctx.values["number"] when available; otherwise
    generates a grade-appropriate number.
    """
    diff_level = 2
    if ctx.difficulty_profile:
        diff_level = min(len(ctx.difficulty_profile) + 1, 4)

    # ── 1. Resolve the number ─────────────────────────────────────────────────
    if ctx.visual_params and "total_value" in ctx.visual_params:
        blocks = {k: ctx.visual_params[k] for k in ("thousands", "hundreds", "tens", "ones", "total_value")}
        question_type = ctx.visual_params.get("question_type", "read_blocks")
    elif ctx.values:
        target_num = None
        for key in ["number", "answer", "result", "value"]:
            if key in ctx.values:
                try:
                    target_num = int(ctx.values[key])
                    break
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid numeric value for '{key}': {ctx.values[key]}") from e
        if target_num is not None:
            blocks = _decompose(target_num, ctx.grade)
            question_type = ctx.values.get("question_type", ctx.values.get("task_type", "read_blocks"))
        else:
            limit = None
            if ctx.difficulty_profile:
                for limit_key in ["max_sum", "max_difference", "max_value", "max_total", "range"]:
                    val = ctx.difficulty_profile.get(limit_key)
                    if val is not None:
                        try:
                            limit = int(float(val))
                            break
                        except (ValueError, TypeError) as e:
                            raise ValueError(f"Invalid limit value for '{limit_key}': {val}") from e
            lo = _grade_min(ctx.grade)
            hi = _grade_max(ctx.grade)
            if limit is not None:
                hi = min(hi, limit)
                lo = min(lo, hi)
            number = rng.randint(lo, hi)
            blocks = _decompose(number, ctx.grade)
            if diff_level >= 3:
                question_type = rng.choice(["read_blocks", "identify_place"])
            else:
                question_type = "read_blocks"
    else:
        limit = None
        if ctx.difficulty_profile:
            for limit_key in ["max_sum", "max_difference", "max_value", "max_total", "range"]:
                val = ctx.difficulty_profile.get(limit_key)
                if val is not None:
                    try:
                        limit = int(float(val))
                        break
                    except (ValueError, TypeError) as e:
                        raise ValueError(f"Invalid limit value for '{limit_key}': {val}") from e
        lo = _grade_min(ctx.grade)
        hi = _grade_max(ctx.grade)
        if limit is not None:
            hi = min(hi, limit)
            lo = min(lo, hi)
        number = rng.randint(lo, hi)
        blocks = _decompose(number, ctx.grade)
        if diff_level >= 3:
            question_type = rng.choice(["read_blocks", "identify_place"])
        else:
            question_type = "read_blocks"

    if interaction_mode == "set":
        question_type = "build_number"

    vp = {
        "thousands": blocks["thousands"],
        "hundreds": blocks["hundreds"],
        "tens": blocks["tens"],
        "ones": blocks["ones"],
        "total_value": blocks["total_value"],
        "number": blocks["total_value"],
        "question_type": question_type,
        "is_interactive": interaction_mode == "set",
    }

    # ── 2. Correct answer ─────────────────────────────────────────────────────
    correct_answer = blocks["total_value"]

    # ── 3. Traps ──────────────────────────────────────────────────────────────
    traps = _build_traps(blocks, rng)

    # ── 4. MCQ options ────────────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        if len(traps) < 3:
            traps = augment_distractors(traps, correct_answer, target=3, max_delta=5)
            if len(traps) < 3:
                raise ValueError(f"PlaceValueBlocks MCQ requires at least 3 unique traps, but got {len(traps)}")
        all_opts = [correct_answer] + traps[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_answer}
            for i, v in enumerate(all_opts)
        ]
        final_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        final_answer = correct_answer

    question_text = _stem(blocks, question_type, interaction_mode)

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_placevalueblocks",
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
        visual_type="PlaceValueBlocks",
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
