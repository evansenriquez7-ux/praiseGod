"""
fmt_array_grid.py — ArrayGrid (GridArea) visual formatter

Produces a FormattedProblem with array/grid visual_params for
multiplication and division concepts.
Carves generation logic from visual_skeletons.py _gen_grid_area /
_traps_grid_area; does NOT import from that module.

visual_params:
    rows              — int
    cols              — int
    shaded            — bool (True = array is shaded)
    highlight_groups  — list of {"row_start", "col_start", "row_end", "col_end"}
    shape_type        — "rectangle" | "L_shape"
    correct_count     — int (total shaded squares / product)
    grid_size         — [int, int]

interaction_mode:
    "read" — array shown; student identifies total or equation
    "set"  — student shades squares to form the array

answer_collection:
    "mcq"            — 4 choices
    "fill_in_blank"  — student types the product / quotient
"""

import random
from typing import List, Optional

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# ─────────────────────────────────────────────────────────────────────────────
# Visual-params builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_visual_params(
    grade: int, diff_level: int, rng: random.Random
) -> dict:
    """
    Build ArrayGrid visual_params.

    Grade 2: arrays up to 10×10 (multiplication intro).
    Grade 3: same, harder numbers; equal-groups division framing.
    Grade 4+: larger or L-shaped arrays.
    """
    if grade <= 3:
        if diff_level <= 2:
            rows = rng.randint(2, 5)
            cols = rng.randint(2, 5)
        else:
            rows = rng.randint(2, 10)
            cols = rng.randint(2, 10)
        shape_type = "rectangle"
        correct_count = rows * cols
        params = {
            "rows": rows,
            "cols": cols,
            "shaded": True,
            "highlight_groups": [],
            "shape_type": shape_type,
            "correct_count": correct_count,
            "grid_size": [max(rows, 5), max(cols, 5)],
        }

    elif grade <= 5:
        if diff_level >= 3:
            # L-shape: two rectangles
            r1 = rng.randint(3, 6)
            c1 = rng.randint(2, 4)
            r2 = rng.randint(2, 4)
            c2 = rng.randint(2, 4)
            correct_count = r1 * c1 + r2 * c2
            shape_type = "L_shape"
            params = {
                "rows": r1 + r2,
                "cols": max(c1, c2),
                "shaded": True,
                "highlight_groups": [
                    {"row_start": 0, "col_start": 0, "row_end": r1, "col_end": c1},
                    {"row_start": r1, "col_start": 0, "row_end": r1 + r2, "col_end": c2},
                ],
                "shape_type": shape_type,
                "correct_count": correct_count,
                "grid_size": [r1 + r2 + 1, max(c1, c2) + 1],
            }
        else:
            rows = rng.randint(3, 8)
            cols = rng.randint(2, 6)
            shape_type = "rectangle"
            correct_count = rows * cols
            params = {
                "rows": rows,
                "cols": cols,
                "shaded": True,
                "highlight_groups": [],
                "shape_type": shape_type,
                "correct_count": correct_count,
                "grid_size": [max(rows + 1, 6), max(cols + 1, 6)],
            }

    else:
        rows = rng.randint(4, 10)
        cols = rng.randint(3, 8)
        shape_type = "rectangle"
        correct_count = rows * cols
        params = {
            "rows": rows,
            "cols": cols,
            "shaded": True,
            "highlight_groups": [],
            "shape_type": shape_type,
            "correct_count": correct_count,
            "grid_size": [rows + 1, cols + 1],
        }

    return params


# ─────────────────────────────────────────────────────────────────────────────
# Trap builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(params: dict, rng: random.Random) -> dict:
    traps: dict = {}
    correct = params["correct_count"]
    rows = params.get("rows")
    cols = params.get("cols")
    shape_type = params.get("shape_type")

    off = rng.randint(1, 3)
    traps["off_by_few_under"] = {
        "value": max(1, correct - off),
        "description": f"Missed {off} squares",
    }
    traps["off_by_few_over"] = {
        "value": correct + rng.randint(1, 3),
        "description": "Counted a few extra squares",
    }

    if shape_type == "rectangle" and rows and cols:
        perimeter = 2 * (rows + cols)
        if perimeter != correct:
            traps["counted_perimeter"] = {
                "value": perimeter,
                "description": "Counted perimeter instead of area",
            }
        if rows > 1:
            row_trap = cols * (rows - 1)
            if row_trap != correct:
                traps["missed_one_row"] = {
                    "value": row_trap,
                    "description": "Missed one entire row",
                }
        if cols > 1:
            col_trap = (cols - 1) * rows
            if col_trap != correct:
                traps["missed_one_column"] = {
                    "value": col_trap,
                    "description": "Missed one entire column",
                }
        # Added instead of multiplied
        add_trap = rows + cols
        if add_trap != correct:
            traps["added_instead_of_multiplied"] = {
                "value": add_trap,
                "description": "Added rows and cols instead of multiplying",
            }

    return traps


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_array_grid(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build an ArrayGrid FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Array is pre-shaded; student identifies the product (or area).
    interaction_mode "set":
        Student shades squares to build the specified array.

    answer_collection "mcq":
        Four product/area choices.
    answer_collection "fill_in_blank":
        Student types the product or area.
    """
    # ── 1. Resolve visual_params ───────────────────────────────────────────────
    if ctx.visual_params and "correct_count" in ctx.visual_params:
        vp = ctx.visual_params.copy()
    else:
        diff_profile = ctx.difficulty_profile or {}
        diff_level = min(len(diff_profile) + 1, 4) if diff_profile else 2
        vp = _build_visual_params(ctx.grade, diff_level, random.Random(ctx.seed))

    correct_count: int = vp["correct_count"]
    rows = vp.get("rows")
    cols = vp.get("cols")
    shape_type = vp.get("shape_type", "rectangle")

    traps = _build_traps(vp, rng)

    # ── 2. Question text ──────────────────────────────────────────────────────
    if interaction_mode == "read":
        if shape_type == "rectangle" and rows and cols:
            question_text = (
                f"Look at the {rows}×{cols} array. "
                f"How many squares are shaded in all?"
            )
        else:
            question_text = (
                "Look at the shaded shape. How many square units is the area?"
            )
    else:
        if shape_type == "rectangle" and rows and cols:
            question_text = (
                f"Shade all the squares inside the {rows}×{cols} rectangle. "
                f"How many square units is the area?"
            )
        else:
            question_text = (
                "Shade all the squares inside the shape. "
                "How many square units is the area?"
            )

    # ── 3. Answer collection ──────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        seen = {correct_count}
        distractor_vals = []
        for t in traps.values():
            v = t.get("value")
            if v is not None and v not in seen and v > 0:
                seen.add(v)
                distractor_vals.append(v)
            if len(distractor_vals) == 3:
                break
        # Pad if needed
        for off in [1, 2, 3, -1, -2, -3]:
            if len(distractor_vals) >= 3:
                break
            candidate = correct_count + off
            if candidate > 0 and candidate not in seen:
                seen.add(candidate)
                distractor_vals.append(candidate)

        all_opts = [correct_count] + distractor_vals[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_count}
            for i, v in enumerate(all_opts)
        ]
        correct_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        correct_answer = correct_count

    format_data: dict = {"visual_params": vp}
    if mcq_options is not None:
        format_data["mcq_options"] = mcq_options

    fmt = f"{interaction_mode}_{answer_collection}"

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_arraygrid",
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
        visual_type="GridArea",
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
