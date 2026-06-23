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
            # No distractors available - make it True
            fill_value = ctx.correct_answer
            is_true = True
    
    # Build equation-style statement based on concept
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
    else:
        # Fallback
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
        analytics={
            "time_to_answer_ms": None,
            "trap_triggered": None,
            "is_correct": None,
        },
    )
