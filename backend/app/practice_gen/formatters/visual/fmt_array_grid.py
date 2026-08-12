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

def _repeated_sum(terms: int, addend: int) -> str:
    """
    Write `terms` copies of `addend` as a repeated sum, or describe it when
    writing it out would be unwieldy.

    Grade-2 arrays reach 10 rows, and "3 + 3 + 3 + 3 + 3 + 3 + 3 + 3 + 3 + 3"
    stops being a readable illustration well before that, so past five terms the
    stem states the repetition instead of spelling it out.
    """
    if terms <= 5:
        return " + ".join([str(addend)] * terms)
    return f"{addend} added {terms} times"


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
    elif ctx.values and "sides" in ctx.values and "l" in ctx.values["sides"]:
        l = ctx.values["sides"]["l"]
        w = ctx.values["sides"]["w"]
        vp = {
            "rows": l,
            "cols": w,
            "shaded": True,
            "highlight_groups": [],
            "shape_type": "rectangle",
            "correct_count": l * w,
            "grid_size": [l + 1, w + 1],
        }
    elif ctx.values and "groups" in ctx.values and "n" in ctx.values:
        rows = ctx.values["groups"]
        cols = ctx.values["n"]
        vp = {
            "rows": rows,
            "cols": cols,
            "shaded": True,
            "highlight_groups": [],
            "shape_type": "rectangle",
            "correct_count": rows * cols,
            "grid_size": [rows + 1, cols + 1],
        }
    elif ctx.dna_concept == "division" and ctx.values and "a" in ctx.values and "b" in ctx.values:
        # Division's own branch, checked before the generic a/b fallback
        # below (which multiplies them together -- correct for multiplication,
        # but for division a=dividend and b=divisor, so "rows=a, cols=b,
        # correct_count=a*b" fabricated e.g. a 1080-square array for
        # "180 / 6" with no connection to the actual quotient). Divisor equal
        # rows of quotient-per-row makes correct_count the real dividend.
        # Deliberately NOT reusing the "groups"/"n" keys the multiplication
        # branch above reads: base_generator._build_symbolic_question's own
        # division branch already treats "n" as an alias for the DIVISOR (b)
        # and "groups" as an alias for the RESULT -- an earlier version of
        # this fix stored the quotient under "n" and the divisor under
        # "groups", which collided with that and silently swapped the
        # divisor shown in the question text with the quotient (e.g. "What
        # is 15 / 3?" for the fact 15 / 5 = 3). A concept-gated branch here
        # avoids the shared-key collision entirely.
        divisor = ctx.values["b"]
        quotient = ctx.values["a"] // divisor if divisor else 0
        vp = {
            "rows": divisor,
            "cols": quotient,
            "shaded": True,
            "highlight_groups": [],
            "shape_type": "rectangle",
            "correct_count": ctx.values["a"],
            "grid_size": [divisor + 1, quotient + 1],
        }
    elif ctx.values and "a" in ctx.values and "b" in ctx.values:
        rows = ctx.values["a"]
        cols = ctx.values["b"]
        vp = {
            "rows": rows,
            "cols": cols,
            "shaded": True,
            "highlight_groups": [],
            "shape_type": "rectangle",
            "correct_count": rows * cols,
            "grid_size": [rows + 1, cols + 1],
        }
    else:
        diff_profile = ctx.difficulty_profile or {}
        diff_level = min(len(diff_profile) + 1, 4) if diff_profile else 2
        vp = _build_visual_params(ctx.grade, diff_level, random.Random(ctx.seed))

    rows = vp.get("rows")
    cols = vp.get("cols")
    shape_type = vp.get("shape_type", "rectangle")
    is_division_array = (
        ctx.dna_concept == "division" and shape_type == "rectangle" and rows and cols
    )

    # For division, rows=divisor and cols=quotient (see the vp branch
    # above), and the real answer is the quotient (cols), not vp's own
    # "correct_count" (rows*cols, the dividend). This must happen BEFORE
    # _build_traps runs: traps are built from params["correct_count"], so
    # building them first and only overwriting the local `correct_count`
    # variable afterward (the previous shape of this fix) left every MCQ
    # distractor computed as an offset from the DIVIDEND while the
    # question asked for the much smaller QUOTIENT -- structurally valid
    # (still 3 unique non-equal numbers) but numerically nonsensical
    # distractors, e.g. quotient=5 offered alongside dividend-sized
    # options like 27 or 32.
    if is_division_array:
        vp["correct_count"] = cols

    correct_count: int = vp["correct_count"]
    traps = _build_traps(vp, rng)

    # Which multiplication sub-skill this array is illustrating, if any. Only
    # meaningful for the multiplication DNA; division arrays are handled by
    # their own branch below.
    _mul_task_type = (
        ctx.values.get("task_type") if ctx.dna_concept == "multiplication" else None
    )

    # ── 2. Question text ──────────────────────────────────────────────────────
    # The generic "how many squares in all" stem below reads identically
    # whether this array came from a multiplication or a division DNA --
    # nothing in the text ever named the divisor/quotient roles, so the
    # item tested array-counting, not division (blind review across the
    # division node group: "asks for a total... not a division
    # computation"). Name the divisor/quotient roles explicitly instead.
    if is_division_array:
        total = rows * cols
        if interaction_mode == "read":
            # A genuine division item gives the TOTAL and the number of
            # equal rows (the divisor) and asks for how many go in each
            # row (the quotient) -- the array is still shown in full so
            # the student can see/count the same total, but the value
            # they must produce is the quotient.
            question_text = (
                f"This array has {total} squares split into {rows} equal rows. "
                f"How many squares are in each row?"
            )
        else:
            # Same division-vs-multiplication defect as "read", in its
            # "set" sibling (blind review of the division node group's
            # "set_fill_in_blank" samples: "asks for the total... a
            # division node secretly testing multiplication"). "set"
            # mode's own contract is an active construction task (student
            # shades an empty grid), so keep it empty and have the
            # construction itself BE the division: split a given total
            # into the stated number of equal rows, then state the
            # quotient -- how many go in each row.
            vp["shaded"] = False
            question_text = (
                f"Shade {total} squares into {rows} equal rows. "
                f"How many squares are in each row?"
            )
    elif interaction_mode == "read":
        if shape_type == "rectangle" and rows and cols:
            # An array is the shared picture behind three different grade-2
            # competencies, so the stem has to name which one it is illustrating
            # or the sibling nodes render identical items. mat_g2_na_q3_0 is
            # stated in group language ("5 groups of 3"); mat_g2_na_q3_1 asks
            # for the repeated sum itself; a plain product node wants neither.
            if _mul_task_type == "equal_groups":
                question_text = (
                    f"Look at the array. It shows {rows} groups of {cols}. "
                    f"How many squares are shaded in all?"
                )
            elif _mul_task_type == "repeated_addition":
                question_text = (
                    f"Look at the {rows}×{cols} array. It shows "
                    f"{_repeated_sum(rows, cols)}. "
                    f"How many squares are shaded in all?"
                )
            else:
                question_text = (
                    f"Look at the {rows}×{cols} array. "
                    f"How many squares are shaded in all?"
                )
        else:
            question_text = (
                "Look at the shaded shape. How many squares are shaded in all?"
            )
    else:
        vp["shaded"] = False
        if shape_type == "rectangle" and rows and cols:
            if _mul_task_type == "equal_groups":
                question_text = (
                    f"Shade {rows} groups of {cols} squares. "
                    f"How many squares did you shade in all?"
                )
            elif _mul_task_type == "repeated_addition":
                question_text = (
                    f"Shade {rows} rows of {cols} squares to show "
                    f"{_repeated_sum(rows, cols)}. "
                    f"How many squares did you shade in all?"
                )
            else:
                question_text = (
                    f"Shade all the squares inside the {rows}×{cols} rectangle. "
                    f"How many squares did you shade in all?"
                )
        else:
            question_text = (
                "Shade all the squares inside the shape. "
                "How many squares did you shade in all?"
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
        given_values={k: v for k, v in ctx.values.items() if k != ctx.blank_target} if ctx.values else None,
        blank_target=ctx.blank_target,
    )
