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
    """Build a pure equation string for the actor's work display."""
    values = ctx.values or {}
    concept = ctx.dna_concept
    blank_target = ctx.blank_target or "result"

    if concept == "addition":
        a = values.get("a")
        b = values.get("b")
        return f"{a} + {b}"
    elif concept == "subtraction":
        a = values.get("a")
        b = values.get("b")
        return f"{a} − {b}"
    elif concept == "multiplication":
        a = values.get("a", values.get("groups"))
        b = values.get("b", values.get("n"))
        return f"{a} × {b}"
    elif concept == "division":
        dividend = values.get("dividend", values.get("a"))
        divisor = values.get("divisor", values.get("b"))
        return f"{dividend} ÷ {divisor}"
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

    # Build display text
    if context_variant == "pure":
        question_text = (
            f"{actor} says: {problem_text} = {actors_answer}. "
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
