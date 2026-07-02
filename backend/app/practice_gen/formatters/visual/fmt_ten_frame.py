"""
fmt_ten_frame.py — TenFrame visual formatter

NEW formatter — gap analysis addition (Grade 1-2 number sense).
Does NOT import from visual_skeletons.py.

Shows a 2×5 ten-frame grid with some circles filled.

    frame_count=1 for numbers 1–10
    frame_count=2 for numbers 11–20 (double ten-frame, stacked)

interaction_mode:
    "read" — ten frame shown; student counts and answers
    "set"  — student clicks/fills circles to show a given number

visual_params:
    {
        "filled":       int,         # number of filled circles
        "frame_count":  1 | 2,
        "color_split":  bool,        # True → two colours highlight the split (e.g. 5+3)
        "query_type":   "count_filled" | "count_empty" | "make_ten" | "show_number",
    }

query_type answers:
    count_filled  → filled
    count_empty   → 10 * frame_count - filled
    make_ten      → 10 - filled  (only valid for frame_count=1)
    show_number   → filled  (set mode — student produces the frame)

Grade band: (1, 2)

Traps:
    count_all     — counts total cells (10 or 20) instead of filled
    off_by_one    — answer ± 1
    count_unshaded— counts empty cells instead of filled (or vice versa)
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

_FRAME_CAPACITY = 10  # each ten-frame holds 10


def _build_params(grade: int, diff_level: int, rng: random.Random) -> dict:
    """
    Generate ten-frame parameters.

    G1: single frame (1-10), simple count_filled / make_ten
    G2: may use double frame (11-20) at higher difficulty
    """
    use_double = (grade >= 2) and (diff_level >= 2) and rng.choice([True, False])
    frame_count = 2 if use_double else 1
    capacity = frame_count * _FRAME_CAPACITY

    filled = rng.randint(1, capacity - 1)  # never 0 or full (boring corners)
    color_split = diff_level >= 2 and rng.choice([True, False])

    # query_type selection (set mode is applied later at the call site)
    if frame_count == 1 and diff_level >= 2:
        query_type = rng.choice(["count_filled", "count_empty", "make_ten"])
    elif frame_count == 2:
        query_type = rng.choice(["count_filled", "count_empty"])
    else:
        query_type = "count_filled"

    return {
        "filled": filled,
        "frame_count": frame_count,
        "color_split": color_split,
        "query_type": query_type,
    }


def _correct_answer(params: dict) -> int:
    filled = params["filled"]
    frame_count = params["frame_count"]
    capacity = frame_count * _FRAME_CAPACITY
    qt = params["query_type"]
    if qt == "count_filled":
        return filled
    if qt == "count_empty":
        return capacity - filled
    if qt == "make_ten":
        return _FRAME_CAPACITY - filled
    # show_number
    return filled


# ─────────────────────────────────────────────────────────────────────────────
# Traps
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(params: dict, answer: int, rng: random.Random) -> list:
    """
    Return up to 3 distractor values.

    Traps:
        count_all      — total cell count (10 or 20)
        off_by_one     — answer ± 1
        count_unshaded — opposite count (empty vs filled)
    """
    traps = []
    seen = {answer}
    filled = params["filled"]
    frame_count = params["frame_count"]
    capacity = frame_count * _FRAME_CAPACITY
    qt = params["query_type"]

    # Count all cells
    if capacity not in seen:
        traps.append(capacity)
        seen.add(capacity)

    # Off by one
    for delta in (1, -1):
        candidate = answer + delta
        if 0 < candidate <= capacity and candidate not in seen:
            traps.append(candidate)
            seen.add(candidate)
        if len(traps) >= 3:
            break

    # Opposite count
    opposite = capacity - filled  # empty cells
    if qt == "count_empty":
        opposite = filled  # student counts filled instead
    if opposite not in seen and 0 < opposite <= capacity:
        traps.append(opposite)

    # Pad traps if needed
    offset_mult = 1
    while len(traps) < 3:
        for sign in [1, -1]:
            candidate = answer + (offset_mult * sign)
            # Expand capacity bounds if we really need to find 3 traps, 
            # but ideally keep it > 0. A ten-frame answer might be 10, so candidate 11 is ok as a trap.
            if candidate >= 0 and candidate not in seen:
                traps.append(candidate)
                seen.add(candidate)
                if len(traps) >= 3:
                    break
        offset_mult += 1

    rng.shuffle(traps)
    return traps[:3]


# ─────────────────────────────────────────────────────────────────────────────
# Question text
# ─────────────────────────────────────────────────────────────────────────────

def _stem(params: dict, interaction_mode: str) -> str:
    qt = params["query_type"]
    frame_count = params["frame_count"]
    capacity = frame_count * _FRAME_CAPACITY

    if interaction_mode == "set" or qt == "show_number":
        return f"Fill in the ten-frame to show {params['filled']}."
    if qt == "count_filled":
        return "How many circles are filled?"
    if qt == "count_empty":
        return f"How many circles are empty? (There are {capacity} circles total.)"
    if qt == "make_ten":
        return "How many more circles do you need to fill to make 10?"
    return "Answer the question about the ten-frame."


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_ten_frame(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a TenFrame FormattedProblem from a QuestionContext.

    Grade band: G1-G2 only. If grade > 2, the formatter still works but content
    is capped at double ten-frame (20).

    interaction_mode "read":
        Ten-frame shown; student answers a counting question.
    interaction_mode "set":
        Student fills circles to represent a number (query_type="show_number").

    Pulls from ctx.values when available.
    Keys used: number (for filled count), query_type.
    """
    diff_level = 2
    if ctx.difficulty_profile:
        diff_level = min(len(ctx.difficulty_profile) + 1, 4)

    # ── 1. Resolve params ─────────────────────────────────────────────────────
    if ctx.visual_params and "filled" in ctx.visual_params:
        params = ctx.visual_params.copy()
    elif ctx.values and "number" in ctx.values:
        number = int(ctx.values["number"])
        frame_count = 2 if number > 10 else 1
        query_type = ctx.values.get("query_type", "count_filled")
        params = {
            "filled": min(number, frame_count * _FRAME_CAPACITY),
            "frame_count": frame_count,
            "color_split": False,
            "query_type": query_type,
        }
    else:
        params = _build_params(ctx.grade, diff_level, rng)

    if interaction_mode == "set":
        params["query_type"] = "show_number"

    vp = {
        "filled": params["filled"],
        "frame_count": params["frame_count"],
        "color_split": params["color_split"],
        "query_type": params["query_type"],
    }

    # ── 2. Correct answer ─────────────────────────────────────────────────────
    correct_answer = _correct_answer(params)

    # ── 3. Traps ──────────────────────────────────────────────────────────────
    traps = _build_traps(params, correct_answer, rng)

    # ── 4. MCQ options ────────────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq" and params["query_type"] != "show_number":
        if len(traps) < 3:
            traps = augment_distractors(traps, correct_answer, target=3, max_delta=5)
            if len(traps) < 3:
                raise ValueError(f"Formatter 'ten_frame' requires at least 3 unique distractors, but got {len(traps)}")
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
        problem_id=f"{ctx.node_id}_{ctx.seed}_tenframe",
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
        visual_type="TenFrame",
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
