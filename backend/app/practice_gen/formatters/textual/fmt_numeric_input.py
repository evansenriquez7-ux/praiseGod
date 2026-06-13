"""
Textual Formatter — Numeric Input (Free-Entry)

Refactored from visual_skeletons.py fill_in mode.

Presents the question as a free-entry numeric field. The frontend renders
a plain text input; answer validation happens server-side.

input_type detection:
    "fraction"  — correct_answer is a string containing "/"
    "decimal"   — correct_answer is a float (not a whole number)
    "integer"   — everything else
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


def _detect_input_type(correct_answer) -> str:
    """Classify the correct answer into integer, decimal, or fraction."""
    if isinstance(correct_answer, str) and "/" in correct_answer:
        return "fraction"
    if isinstance(correct_answer, float) and correct_answer != int(correct_answer):
        return "decimal"
    return "integer"


def _numeric_bounds(correct_answer, distractors) -> tuple:
    """
    Derive min_value / max_value from correct answer and available distractors.

    Returns (min_value, max_value) as numbers. Falls back to a symmetric
    ±50% window when no numeric distractors exist.
    """
    candidates = [correct_answer] + [
        d for d in distractors if isinstance(d, (int, float))
    ]
    try:
        nums = [float(v) for v in candidates]
        lo = min(nums)
        hi = max(nums)
        # Guarantee a non-trivial window around the correct answer
        if lo == hi:
            lo = lo - max(1, abs(lo) * 0.5)
            hi = hi + max(1, abs(hi) * 0.5)
        return lo, hi
    except (TypeError, ValueError):
        return 0, 100


def format_numeric_input(ctx: QuestionContext, rng: random.Random) -> FormattedProblem:
    """
    Format a QuestionContext as a free-entry numeric input problem.

    format_data:
        input_type  — "integer" | "decimal" | "fraction"
        min_value   — lowest plausible answer (for frontend range validation)
        max_value   — highest plausible answer
    """
    input_type = _detect_input_type(ctx.correct_answer)
    min_value, max_value = _numeric_bounds(ctx.correct_answer, ctx.distractors)

    format_data = {
        "input_type": input_type,
        "min_value": min_value,
        "max_value": max_value,
    }

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_numeric_input",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=ctx.question_text,
        correct_answer=ctx.correct_answer,
        distractors=ctx.distractors,
        hints=ctx.hints,
        format="numeric_input",
        format_data=format_data,
        is_visual=False,
        visual_type=None,
        visual_params=None,
        interaction_mode=None,
        answer_collection="numeric_input",
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
        analytics={
            "time_to_answer_ms": None,
            "trap_triggered": None,
            "is_correct": None,
        },
    )
