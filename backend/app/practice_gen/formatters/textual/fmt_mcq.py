"""
Textual Formatter — Multiple Choice (MCQ)

Refactored from matatag_skeletons.py options-building logic.

Builds 4 shuffled MCQ options (1 correct + up to 3 distractors) and assigns
A/B/C/D keys. Falls back to arithmetic offsets when fewer than 3 distractors
are available on the context.

Respects the 'context' variant:
  - "pure": Shows equation "What is 5 + 3?"
  - "word_problem": Shows story problem
"""

import random
from typing import List

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


def _build_pure_question(ctx: QuestionContext) -> str:
    """Build a pure equation question based on concept."""
    values = ctx.values or {}
    concept = ctx.dna_concept
    blank_target = ctx.blank_target or "result"
    
    if concept == "addition":
        a = values.get("a")
        b = values.get("b")
        result = values.get("result")
        if blank_target == "result":
            return f"What is {a} + {b}?"
        elif blank_target == "b":
            return f"What number plus {a} equals {result}?"
        else:  # blank_target == "a"
            return f"What number plus {b} equals {result}?"
    
    elif concept == "subtraction":
        a = values.get("a")
        b = values.get("b")
        result = values.get("result")
        if blank_target == "result":
            return f"What is {a} − {b}?"
        elif blank_target == "b":
            return f"What number subtracted from {a} equals {result}?"
        else:
            return f"What minus {b} equals {result}?"
    
    elif concept == "multiplication":
        a = values.get("a", values.get("groups"))
        b = values.get("b", values.get("n"))
        result = values.get("result", values.get("total"))
        if blank_target in ("result", "total"):
            return f"What is {a} × {b}?"
        elif blank_target in ("b", "n"):
            return f"What times {a} equals {result}?"
        else:
            return f"What times {b} equals {result}?"
    
    elif concept == "division":
        dividend = values.get("dividend", values.get("a"))
        divisor = values.get("divisor", values.get("b"))
        quotient = values.get("quotient", values.get("result"))
        if blank_target in ("result", "quotient"):
            return f"What is {dividend} ÷ {divisor}?"
        elif blank_target in ("b", "divisor", "n"):
            return f"{dividend} divided by what equals {quotient}?"
        else:
            return f"What divided by {divisor} equals {quotient}?"
    
    else:
        # Fallback: use the question_text
        return ctx.question_text


def format_mcq(ctx: QuestionContext, rng: random.Random) -> FormattedProblem:
    """
    Format a QuestionContext as a 4-option MCQ.

    Respects the 'context' variant:
    - "pure": Shows equation question "What is 5 + 3?"
    - "word_problem": Shows story problem

    Distractor priority:
      1. ctx.distractors (pedagogically meaningful ErrorPattern values)
      2. Arithmetic fallbacks: correct ± 1, ± 2, ± 10

    Returns a FormattedProblem with format="mcq" and format_data containing
    a shuffled options list plus correct_key.
    """
    correct = ctx.correct_answer
    values = ctx.values or {}
    
    # Get context variant
    context_variant = values.get("context")
    if context_variant is None and ctx.difficulty_profile:
        context_variant = ctx.difficulty_profile.get("context")
    if context_variant is None:
        context_variant = "pure"  # default to pure for MCQ
    
    # Build question text based on context
    if context_variant == "word_problem":
        question_text = ctx.question_text
    else:
        # Pure: use equation format
        question_text = _build_pure_question(ctx)

    # Collect candidate distractors — deduplicate and exclude correct answer
    candidates: List = []
    seen = {correct}
    for d in ctx.distractors:
        if d not in seen:
            candidates.append(d)
            seen.add(d)

    # Fill up to 3 using arithmetic fallbacks when candidates are insufficient
    if len(candidates) < 3 and isinstance(correct, (int, float)):
        fallback_offsets = [-1, 1, 2, -2, 10, -10]
        for offset in fallback_offsets:
            if len(candidates) >= 3:
                break
            candidate = correct + offset
            if candidate not in seen:
                candidates.append(candidate)
                seen.add(candidate)

    distractors = candidates[:3]

    # Build option pool: correct first, then distractors
    pool = [{"value": correct, "is_correct": True}] + [
        {"value": d, "is_correct": False} for d in distractors
    ]

    # Pad to exactly 4 if still short (edge case: non-numeric correct with few distractors)
    pad_index = 1
    while len(pool) < 4:
        if isinstance(correct, (int, float)):
            pad_val = correct + pad_index * 3
        else:
            pad_val = f"{correct} (alt {pad_index})"
        if pad_val not in seen:
            pool.append({"value": pad_val, "is_correct": False})
            seen.add(pad_val)
        pad_index += 1

    # Shuffle and assign keys
    rng.shuffle(pool)
    keys = ["A", "B", "C", "D"]
    options = []
    correct_key = "A"
    for key, opt in zip(keys, pool):
        entry = {"key": key, "value": opt["value"], "is_correct": opt["is_correct"]}
        options.append(entry)
        if opt["is_correct"]:
            correct_key = key

    format_data = {
        "options": options,
        "correct_key": correct_key,
        "context": context_variant,
    }

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_mcq",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=ctx.correct_answer,
        distractors=distractors,
        hints=ctx.hints,
        format="mcq",
        format_data=format_data,
        is_visual=False,
        visual_type=None,
        visual_params=None,
        interaction_mode=None,
        answer_collection="mcq",
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
