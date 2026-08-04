"""
Textual Formatter — Error Detection ("Check the Work")

Presents a worked problem attributed to a named Filipino student.
The learner must first decide if the answer is correct (Yes/No).
If incorrect, the learner provides the correct answer.

~50% of problems show the correct answer (student picks "Yes").
~50% plant a wrong answer from distractors (student picks "No" + corrects).

This teaches students to verify work, not just assume errors exist.

Actor names rotate deterministically via seed.
"""

import random
from typing import Any

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# Rotating cast of Filipino student names for the "actor" role.
_FILIPINO_NAMES = [
    "Noel",
    "Maria",
    "Jose",
    "Ana",
    "Carlo",
    "Liza",
    "Manny",
    "Grace",
    "Rico",
    "Pia",
    "Dante",
    "Rosa",
]


def _pick_actor(seed: int) -> str:
    """Deterministically pick an actor name from the rotation using the seed."""
    return _FILIPINO_NAMES[seed % len(_FILIPINO_NAMES)]


def _distractor_label(distractor: Any) -> str:
    if hasattr(distractor, "label"):
        return distractor.label
    return "unknown_error"


def _distractor_value(distractor: Any) -> Any:
    if hasattr(distractor, "value"):
        return distractor.value
    return distractor


def _build_pure_equation(ctx: QuestionContext) -> str:
    """
    Build a full "a op b = result" equation string for the actor's work
    display, with the ONE slot ctx.blank_target names rendered as "___" and
    every other slot (including the result) shown as its real value.

    For the ordinary case (blank_target == "result"/"total"/"quotient") this
    is equivalent to the old "{a} op {b}" text plus format_error_detect's own
    "= {actors_answer}" suffix, since the result slot is exactly where that
    suffix went. But a co-mapped DNA can bind a different structure (e.g.
    missing_number's "divisor_unknown" text match on division.py, when
    division -- not missing_number -- ends up the concept actually
    generating a given item): blank_target becomes "b", and the old code
    showed "56 / 8" (the divisor's real value, with the true quotient 7
    nowhere in the string) then unconditionally appended "= {actors_answer}"
    after it -- producing "Jose says: 56 / 8 = 7", a TRUE statement, while
    correct_value stayed 8 (the divisor) and the item was marked wrong. The
    reader had no way to know 8, not 7, was the actual unknown being quizzed.
    Now the blank tracks the real unknown and the given result stays visible:
    "56 / ___ = 7", filled with the actor's claimed divisor.
    """
    values = ctx.values or {}
    concept = ctx.dna_concept
    blank_target = ctx.blank_target or "result"

    def slot(*keys, value):
        return "___" if blank_target in keys else value

    # For task_type=="estimate" (addition/subtraction/multiplication/
    # division), "a"/"b" carry the ROUNDED values used for the answer key,
    # not the numbers being estimated -- showing them directly as the
    # "actor's work" ("Rico says: 100 + 100 = 200") loses the estimate
    # framing and reads as an ordinary round-number fact. Show the REAL
    # (unrounded) operands with "≈" before the blank instead; the blank
    # still fills with the actor's claimed answer, still keyed against the
    # rounded computation (ctx.correct_answer), so grading is unaffected.
    is_estimate = values.get("task_type") == "estimate"

    if concept == "addition":
        a, b, r = values.get("a"), values.get("b"), values.get("result")
        if is_estimate:
            real_a, real_b = values.get("real_a", a), values.get("real_b", b)
            return f"{real_a} + {real_b} ≈ {slot('result', value=r)}"
        return f"{slot('a', value=a)} + {slot('b', value=b)} = {slot('result', value=r)}"
    elif concept == "subtraction":
        a, b, r = values.get("a"), values.get("b"), values.get("result")
        if is_estimate:
            real_a, real_b = values.get("real_a", a), values.get("real_b", b)
            return f"{real_a} − {real_b} ≈ {slot('result', value=r)}"
        return f"{slot('a', value=a)} − {slot('b', value=b)} = {slot('result', value=r)}"
    elif concept == "multiplication":
        a = values.get("a", values.get("groups"))
        b = values.get("b", values.get("n"))
        r = values.get("result", values.get("total"))
        if is_estimate:
            real_a, real_b = values.get("real_a", a), values.get("real_b", b)
            return f"{real_a} × {real_b} ≈ {slot('result', 'total', value=r)}"
        return (
            f"{slot('a', 'groups', value=a)} × {slot('b', 'n', value=b)} "
            f"= {slot('result', 'total', value=r)}"
        )
    elif concept == "division":
        dividend = values.get("dividend", values.get("a"))
        divisor = values.get("divisor", values.get("b"))
        quotient = values.get("quotient", values.get("result"))
        if is_estimate:
            real_a = values.get("real_a", dividend)
            real_b = values.get("real_b", divisor)
            return f"{real_a} ÷ {real_b} ≈ {slot('result', 'quotient', value=quotient)}"
        return (
            f"{slot('a', 'dividend', value=dividend)} ÷ {slot('b', 'divisor', value=divisor)} "
            f"= {slot('result', 'quotient', value=quotient)}"
        )
    else:
        return ctx.question_text


def format_error_detect(ctx: QuestionContext, rng: random.Random) -> FormattedProblem:
    """
    Format a QuestionContext as a two-step error-detection problem.

    Step 1: "Did [actor] get it correct?" → Yes / No
    Step 2 (only if No): "What is the correct answer?" → numeric input

    ~50% of problems have no error (actor's answer IS correct).
    ~50% plant a distractor (actor's answer is wrong).

    format_data:
        actor_name           — Filipino name of the fictional student
        problem_expression   — the equation/problem shown (e.g., "3 + 6")
        actors_answer        — what the actor answered (correct or wrong)
        has_error            — bool: whether the actor's answer is wrong
        correct_value        — the actual correct answer
        error_label          — trap identifier (or "none" if no error)
        context              — "pure" or "word_problem"
    
    correct_answer format:
        {"has_error": bool, "correct_value": int/str}
    """
    actor = _pick_actor(ctx.seed)
    values = ctx.values or {}

    # Get context variant
    context_variant = values.get("context")
    if context_variant is None and ctx.difficulty_profile:
        context_variant = ctx.difficulty_profile.get("context")
    if context_variant is None:
        context_variant = "pure"

    # Build problem expression
    if context_variant == "word_problem":
        problem_text = ctx.question_text
    else:
        problem_text = _build_pure_equation(ctx)

    # Decide if actor's answer is correct or wrong (50/50)
    has_error: bool = rng.choice([True, False])

    if has_error:
        # Plant a wrong answer from distractors
        candidates = [d for d in ctx.distractors if _distractor_value(d) != ctx.correct_answer]
        if candidates:
            planted_distractor = rng.choice(candidates)
            actors_answer = _distractor_value(planted_distractor)
            error_label = _distractor_label(planted_distractor)
        else:
            # No usable distractors — force correct (no error)
            has_error = False
            actors_answer = ctx.correct_answer
            error_label = "none"
    else:
        actors_answer = ctx.correct_answer
        error_label = "none"

    # problem_text is now a full "a op b = result" equation with exactly one
    # slot (whichever ctx.blank_target names) rendered as "___" -- fill it
    # with the actor's claimed answer. For a plain word_problem context (no
    # equation), _build_pure_equation returns ctx.question_text unchanged,
    # which never contains "___"; keep the old append behaviour for that case.
    if "___" in problem_text:
        actor_statement = problem_text.replace("___", str(actors_answer), 1)
    else:
        actor_statement = f"{problem_text} = {actors_answer}"

    if context_variant == "pure":
        question_text = (
            f"{actor} says: {actor_statement}. "
            f"Is {actor} correct?"
        )
    else:
        question_text = (
            f'{actor} solved this problem: "{problem_text}" '
            f'{actor} says the answer is {actors_answer}. '
            f'Is {actor} correct?'
        )

    # correct_answer encodes both parts
    correct_answer = {
        "has_error": has_error,
        "correct_value": ctx.correct_answer,
    }

    format_data = {
        "actor_name": actor,
        "problem_expression": problem_text,
        "actors_answer": actors_answer,
        "has_error": has_error,
        "correct_value": ctx.correct_answer,
        "error_label": error_label,
        "context": context_variant,
    }

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_error_detect",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=correct_answer,
        distractors=ctx.distractors,
        hints=ctx.hints,
        format="error_detect",
        format_data=format_data,
        is_visual=bool(ctx.visual_params),
        visual_type=ctx.visual_type,
        visual_params=ctx.visual_params,
        interaction_mode=None,
        answer_collection="error_detect",
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
            "trap_triggered": error_label if has_error else None,
            "is_correct": None,
        },
    )
