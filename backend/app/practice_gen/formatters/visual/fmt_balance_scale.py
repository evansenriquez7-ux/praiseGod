"""
fmt_balance_scale.py — BalanceScale visual formatter

NEW formatter — no existing analog in visual_skeletons.py.

Shows a balance scale with an expression on each side.
Used for missing_number DNA (balance expression type) and equivalence.

interaction_mode:
    "read" — scale shown with one blank; student finds the missing value to balance

visual_params:
    {
        "left_side":  str | list,           # e.g. "5 + 3" or ["5", "+", "3"]
        "right_side": str | list,           # e.g. "? + 2"
        "blank_side": "left" | "right" | "none",
        "is_balanced": bool,
    }

Example: left="5 + 3", right="? + 2" → answer = 6

answer_collection: "mcq" or "numeric_input"

Traps derived from missing_number DNA error patterns:
    wrong_op    — applied addition instead of subtraction to find missing value
    off_by_one  — missing value ± 1
    sum_both    — added both known values
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# ─────────────────────────────────────────────────────────────────────────────
# Expression parser / builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_balance_params(ctx: QuestionContext, rng: random.Random) -> dict:
    """
    Derive balance-scale parameters from ctx.values.

    Expects keys: a, b, result, blank_target ("a" | "b" | "result").
    Falls back to generating a simple addition/subtraction balance.
    """
    vals = ctx.values or {}
    a = vals.get("a")
    b = vals.get("b")
    result = vals.get("result")
    blank_target = vals.get("blank_target", "result")

    # If values are missing, generate grade-appropriate numbers
    if a is None or b is None or result is None:
        max_val = 20 if ctx.grade <= 1 else (100 if ctx.grade == 2 else 1000)
        a = rng.randint(1, max_val // 2)
        b = rng.randint(1, max_val // 2)
        result = a + b
        blank_target = rng.choice(["a", "b", "result"])

    # Build the two sides
    if blank_target == "result":
        left_side = f"{a} + {b}"
        right_side = "?"
        blank_side = "right"
        missing_value = result
    elif blank_target == "a":
        left_side = "?"
        right_side = f"{b} + {result - b}" if result > b else f"{result} - {b - result}"
        # Simpler: left side is blank, right side is the total
        right_side = str(result)
        blank_side = "left"
        missing_value = a
    else:  # blank_target == "b"
        left_side = f"{a} + ?"
        right_side = str(result)
        blank_side = "left"
        missing_value = b

    return {
        "left_side": left_side,
        "right_side": right_side,
        "blank_side": blank_side,
        "is_balanced": True,
        "missing_value": missing_value,
        "a": a,
        "b": b,
        "result": result,
        "blank_target": blank_target,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Traps
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(params: dict, rng: random.Random) -> list:
    """
    Return up to 3 distractor values.

    Traps:
        wrong_op     — adds instead of subtracts (or vice versa)
        off_by_one_high — missing_value + 1
        off_by_one_low  — missing_value - 1
        sum_both        — a + b (adds both known values)
    """
    mv = params["missing_value"]
    a = params["a"]
    b = params["b"]
    result = params["result"]
    traps = []
    seen = {mv}

    # Off by one
    for delta in (1, -1):
        candidate = mv + delta
        if candidate > 0 and candidate not in seen:
            traps.append(candidate)
            seen.add(candidate)

    # Wrong operation: add both knowns
    sum_both = a + b
    if sum_both not in seen and sum_both != mv:
        traps.append(sum_both)
        seen.add(sum_both)

    # result itself (if not already the answer)
    if result not in seen and result != mv:
        traps.append(result)

    rng.shuffle(traps)
    return traps[:3]


# ─────────────────────────────────────────────────────────────────────────────
# Question text
# ─────────────────────────────────────────────────────────────────────────────

def _stem(params: dict) -> str:
    left = params["left_side"]
    right = params["right_side"]
    return f"The scale is balanced. {left} = {right}. What is the missing value?"


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_balance_scale(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a BalanceScale FormattedProblem from a QuestionContext.

    interaction_mode is always "read" for this visual type (the scale is shown;
    student solves for the missing value).

    answer_collection: "mcq" or "numeric_input".
    """
    # ── 1. Resolve params ─────────────────────────────────────────────────────
    if ctx.visual_params and "left_side" in ctx.visual_params:
        params = ctx.visual_params.copy()
        if "missing_value" not in params:
            # Derive from stored sides — best effort
            params["missing_value"] = ctx.correct_answer
            params.setdefault("a", 0)
            params.setdefault("b", 0)
            params.setdefault("result", ctx.correct_answer)
            params.setdefault("blank_target", "result")
    else:
        params = _build_balance_params(ctx, rng)

    missing_value = params["missing_value"]

    vp = {
        "left_side": params["left_side"],
        "right_side": params["right_side"],
        "blank_side": params["blank_side"],
        "is_balanced": params["is_balanced"],
    }

    # ── 2. Traps ──────────────────────────────────────────────────────────────
    traps = _build_traps(params, rng)

    # ── 3. MCQ options ────────────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        all_opts = [missing_value] + traps[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == missing_value}
            for i, v in enumerate(all_opts)
        ]
        final_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        final_answer = missing_value

    question_text = _stem(params)

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_balancescale",
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
        visual_type="BalanceScale",
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
