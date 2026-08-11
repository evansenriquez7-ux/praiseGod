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
import re
from typing import List

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext

_FRACTION_STR_RE = re.compile(r"^\d+/\d+$")


def _fraction_sort_key(item):
    """
    Numeric sort key for "N/D" fraction-notation strings.

    Plain `sorted(sequence)` on fraction strings compares them
    lexicographically ("1/10" < "1/2" as text, since '1' < '2'), which
    never raises -- Python strings ARE comparable -- so the formatter's
    own TypeError-triggered fallback never fires and the "correct" order
    is silently wrong. fractions.py needs a real ordering DNA feature
    (mat_g2_na_q4_2/mat_g2_na_q4_5: "order unit/similar fractions") but a
    live fractions.Fraction object isn't JSON-serializable through the
    rest of the pipeline, so it passes plain "N/D" strings instead and
    this formatter has to know how to compare them.
    """
    if isinstance(item, str) and _FRACTION_STR_RE.match(item):
        num, den = item.split("/")
        return int(num) / int(den)
    return item


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
        if len(sequence) >= 2 and _fraction_sort_key(sequence[0]) > _fraction_sort_key(sequence[-1]):
            return "descending"
    except TypeError:
        pass
    return "ascending"


def format_ordering(ctx: QuestionContext, rng: random.Random, format_name: str = "ordering") -> FormattedProblem:
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

    # Determine direction. Only trust ctx.values["direction"] when it's
    # literally "ascending"/"descending" -- this formatter is shared by
    # both comparing_ordering (which uses that exact vocabulary) and
    # counting (whose own "direction" key means "forward"/"backward"
    # sequence traversal, an unrelated concept that happens to share the
    # key name). Trusting the raw value regardless of source let
    # counting's "forward" leak through as this formatter's direction:
    # "forward" != "descending" so the sort fell through to ascending, but
    # "forward" != "ascending" so the question text's own separate check
    # fell through to "largest to smallest" -- two inconsistent-default
    # comparisons on the same unrecognized value produced a genuinely
    # wrong answer key (sorted ascending, but asked for largest-to-
    # smallest). Found by blind review of mat_g1_na_q1_0 seed 72.
    if isinstance(ctx.values, dict) and ctx.values.get("direction") in ("ascending", "descending"):
        direction = ctx.values["direction"]
    else:
        direction = _infer_direction(sequence)

    # Compute correct order. "N/D" fraction strings sort lexicographically
    # under plain sorted() ("1/10" < "1/2"), which never raises TypeError
    # -- strings ARE comparable -- so the fallback below never catches
    # this case; _fraction_sort_key is a no-op for every other item type,
    # so this is safe to apply unconditionally.
    try:
        if direction == "descending":
            correct_order = sorted(sequence, key=_fraction_sort_key, reverse=True)
        else:
            correct_order = sorted(sequence, key=_fraction_sort_key)
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

    # Generate appropriate question text for ordering. A DNA-supplied
    # "question" (comparing_ordering.py's word-problem narrative, which
    # already states what the numbers represent) takes priority over the
    # generic bare-list stem -- this formatter previously always built its
    # own text regardless of context, so "context": "word_problem" never
    # actually changed anything rendered (blind review: variant_
    # comprehensiveness FAIL/CONCERN, "identical bare stem" across every
    # order_set sample).
    if isinstance(ctx.values, dict) and ctx.values.get("question"):
        question_text = ctx.values["question"]
    else:
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
        format=format_name,
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
        given_values={k: v for k, v in ctx.values.items() if k != ctx.blank_target} if ctx.values else None,
        blank_target=ctx.blank_target,
        analytics={
            "time_to_answer_ms": None,
            "trap_triggered": None,
            "is_correct": None,
        },
    )
