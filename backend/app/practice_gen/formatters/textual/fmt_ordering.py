"""
Textual Formatter — Ordering

Refactored from visual_skeletons.py SortOrder generator (partial).

Presents a shuffled list of numbers and asks the student to place them in
ascending or descending order.

Sequence resolution priority:
  1. ctx.values["sequence"] — explicit list from the DNA generator
  2. [ctx.correct_answer] + ctx.distractors — assembled from available values
"""

import random
from typing import List

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


def _resolve_sequence(ctx: QuestionContext) -> List:
    """Return the sequence to be ordered, from context values or fallback."""
    if isinstance(ctx.values, dict) and "sequence" in ctx.values:
        seq = ctx.values["sequence"]
        if isinstance(seq, list) and len(seq) >= 2:
            return list(seq)

    # Fallback: combine correct answer with distractors
    items = [ctx.correct_answer] + list(ctx.distractors)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for item in items:
        key = str(item)
        if key not in seen:
            unique.append(item)
            seen.add(key)
    return unique


def _infer_direction(sequence: List) -> str:
    """
    Infer the intended sort direction from the sequence.

    Returns "descending" if the sorted-descending order equals sorted-ascending
    reversed, and the context signals descending (heuristic: first item of
    unsorted > last item). Defaults to "ascending".
    """
    try:
        if len(sequence) >= 2 and sequence[0] > sequence[-1]:
            return "descending"
    except TypeError:
        pass
    return "ascending"


def format_ordering(ctx: QuestionContext, rng: random.Random) -> FormattedProblem:
    """
    Format a QuestionContext as an ordering problem.

    The student is shown a shuffled list and must rearrange it into the
    correct order. direction is inferred from the sequence unless
    ctx.values supplies an explicit "direction" key.

    format_data:
        items         — shuffled list shown to student
        direction     — "ascending" | "descending"
        correct_order — correctly sorted list (ground truth)
    """
    sequence = _resolve_sequence(ctx)

    # Determine direction
    direction = "ascending"
    if isinstance(ctx.values, dict) and "direction" in ctx.values:
        direction = ctx.values["direction"]
    else:
        direction = _infer_direction(sequence)

    # Compute correct order
    try:
        if direction == "descending":
            correct_order = sorted(sequence, reverse=True)
        else:
            correct_order = sorted(sequence)
    except TypeError:
        # Non-comparable types: preserve sequence as correct order
        correct_order = sorted(sequence, key=lambda x: str(x.get("value") if isinstance(x, dict) else x))

    # Shuffle for display — ensure it's actually shuffled (retry if identical)
    items = list(sequence)
    for _ in range(10):
        rng.shuffle(items)
        if items != correct_order:
            break

    format_data = {
        "items": items,
        "direction": direction,
        "correct_order": correct_order,
    }
    format_data.pop("correct_order", None)

    # Generate appropriate question text for ordering
    direction_word = "smallest to largest" if direction == "ascending" else "largest to smallest"
    question_text = f"Arrange these numbers from {direction_word}: {', '.join(str(x) for x in items)}"

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_ordering",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=correct_order,
        distractors=ctx.distractors,
        hints=ctx.hints,
        format="ordering",
        format_data=format_data,
        is_visual=bool(ctx.visual_params),
        visual_type=ctx.visual_type,
        visual_params=ctx.visual_params,
        interaction_mode=None,
        answer_collection="drag",
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
