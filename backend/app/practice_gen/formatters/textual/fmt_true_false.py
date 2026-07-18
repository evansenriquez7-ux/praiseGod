"""
Textual Formatter — True / False

Presents a declarative statement like "5 + 3 = 8" and asks the student
to judge it as True or False.

50% of statements are correct (True), 50% use a distractor (False).
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


def format_true_false(ctx: QuestionContext, rng: random.Random) -> FormattedProblem:
    """
    Format a QuestionContext as a True/False judgment problem.

    Builds a statement like "5 + 3 = 8" (True) or "5 + 3 = 9" (False).

    format_data:
        statement      — the declarative sentence to evaluate
        is_true        — bool; whether the statement is correct
        correct_answer — bool; the expected student response
    """
    values = ctx.values
    concept = ctx.dna_concept
    blank_target = ctx.blank_target or "result"
    
    # Decide if this should be a True or False statement
    is_true: bool = rng.choice([True, False])
    
    if is_true:
        fill_value = ctx.correct_answer
    else:
        # Pick a distractor
        distractors = [d for d in ctx.distractors if d != ctx.correct_answer]
        if distractors:
            fill_value = rng.choice(distractors)
        else:
            if isinstance(ctx.correct_answer, (int, float)):
                # Force a positive offset when correct_answer is small enough
                # that a negative offset would clamp back to it at 0 (e.g.
                # correct_answer=0, offset=-3 -> 0), which would silently
                # turn a "False" statement into a numerically true one.
                sign = 1 if ctx.correct_answer < 10 else rng.choice([-1, 1])
                offset = rng.randint(1, 10) * sign
                fill_value = ctx.correct_answer + offset
                if fill_value < 0: fill_value = 0
            else:
                fill_value = f"not {ctx.correct_answer}"
    
    # Get context variant
    context_variant = values.get("context")
    if context_variant is None and ctx.difficulty_profile:
        context_variant = ctx.difficulty_profile.get("context")
    if context_variant is None:
        context_variant = "pure"  # default to pure
    
    # Build equation-style statement based on concept and context
    if context_variant == "word_problem":
        statement = f"{ctx.question_text} The answer is {fill_value}."
    else:
        # Pure: use symbolic/equation format
        if concept == "addition":
            a = values.get("a")
            b = values.get("b")
            result = values.get("result")
            if blank_target == "result":
                statement = f"{a} + {b} = {fill_value}"
            elif blank_target == "b":
                statement = f"{a} + {fill_value} = {result}"
            else:
                statement = f"{fill_value} + {b} = {result}"
        elif concept == "subtraction":
            a = values.get("a")
            b = values.get("b")
            result = values.get("result")
            if blank_target == "result":
                statement = f"{a} − {b} = {fill_value}"
            elif blank_target == "b":
                statement = f"{a} − {fill_value} = {result}"
            else:
                statement = f"{fill_value} − {b} = {result}"
        elif concept == "multiplication":
            a = values.get("a", values.get("groups"))
            b = values.get("b", values.get("n"))
            result = values.get("result", values.get("total"))
            if blank_target in ("result", "total"):
                statement = f"{a} × {b} = {fill_value}"
            else:
                statement = f"{fill_value} × {b} = {result}"
        elif concept == "division":
            dividend = values.get("dividend", values.get("a"))
            divisor = values.get("divisor", values.get("b"))
            quotient = values.get("quotient", values.get("result"))
            if blank_target in ("result", "quotient"):
                statement = f"{dividend} ÷ {divisor} = {fill_value}"
            else:
                statement = f"{fill_value} ÷ {divisor} = {quotient}"
        elif concept == "number_reading":
            number = values.get("number")
            task_type = values.get("task_type", "numeral_to_word")
            if task_type == "numeral_to_word":
                statement = f"The number {number} is written in words as '{fill_value}'"
            elif task_type == "numeral_to_expanded":
                statement = f"The expanded form of {number} is {fill_value}"
            else:
                word = values.get("word_form")
                statement = f"The number written as '{word}' is {fill_value}"
        elif concept == "comparing_ordering":
            task_type = values.get("task_type", "compare_pair")
            a = values.get("a")
            b = values.get("b")
            if task_type == "find_between":
                statement = f"The number {fill_value} is between {a} and {b}"
            else:
                statement = f"{a} {fill_value} {b}"
        elif concept == "place_value" and values.get("task_type") == "identify_value":
            # Only "identify_value" has a statement worth specializing: the DNA's
            # blank_target is always value_at_position (see place_value.py), so
            # for other task_types (identify_place/compose/decompose) fill_value
            # wouldn't correspond to what a task-specific phrasing implies —
            # fall through to the generic statement below instead.
            _place_names = ["ones", "tens", "hundreds", "thousands"]
            number = values.get("number")
            digit = values.get("digit_at_position")
            pos = values.get("target_digit_position", 0)
            place = _place_names[pos] if pos < len(_place_names) else f"10^{pos}"
            statement = f"In the number {number}, the value of the digit {digit} in the {place} place is {fill_value}"
        else:
            statement = f"{ctx.question_text} The answer is {fill_value}."

    format_data = {
        "statement": statement,
        "is_true": is_true,
        "correct_answer": is_true,
    }

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_true_false",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=f"{statement}. True or False?",
        correct_answer=is_true,
        distractors=ctx.distractors,
        hints=ctx.hints,
        format="true_false",
        format_data=format_data,
        is_visual=(ctx.visual_type is not None),
        visual_type=ctx.visual_type,
        visual_params=ctx.visual_params,
        interaction_mode=None,
        answer_collection="true_false",
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
