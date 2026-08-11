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
            if values.get("task_type") == "estimate":
                # Show the REAL (unrounded) operands with "≈" -- showing the
                # already-rounded a/b as if they were the literal operands
                # ("100 + 100 = 200") loses the estimate framing entirely
                # and reads as an ordinary round-number fact. fill_value
                # still keys against the rounded computation (ctx.correct_answer
                # / distractors), which is the correct "estimate" answer.
                real_a = values.get("real_a", a)
                real_b = values.get("real_b", b)
                statement = f"{real_a} + {real_b} ≈ {fill_value}"
            elif values.get("task_type") == "expanded_form" and "a_tens" in values:
                # Bare "{a} + {b} = {fill_value}" drops the tens-and-ones
                # decomposition this task_type exists to demonstrate --
                # FORMATTER_VARIANT_SUPPORT allows expanded_form on
                # true_false (it has a real blank_target="result", unlike
                # commutative/associative's yes/no claim), but this branch
                # never carried the decomposition prefix values["question"]
                # states, so the competency's actual named procedure (tens-
                # and-ones addition) never appeared even when the formatter
                # rendered successfully (found rendering mat_g1_na_q2_4/
                # mat_g2_na_q1_8 after binding task_type to expanded_form).
                from backend.app.practice_gen.dna.na.addition import decompose_to_places
                statement = (
                    f"{decompose_to_places(a)} {decompose_to_places(b)} "
                    f"Add the place values, then find the total: {a} + {b} = {fill_value}"
                )
            elif values.get("task_type") == "counting_up" and blank_target == "result":
                # Same root cause as expanded_form above -- "{a} + {b} =
                # {fill_value}" drops the "start at / count up" narration
                # values["question"] states, losing the counting-up framing
                # this task_type exists to demonstrate.
                statement = f"Start at {a}. Count up {b} more. You land on {fill_value}"
            elif blank_target == "result":
                statement = f"{a} + {b} = {fill_value}"
            elif blank_target == "b":
                statement = f"{a} + {fill_value} = {result}"
            else:
                statement = f"{fill_value} + {b} = {result}"
        elif concept == "subtraction":
            a = values.get("a")
            b = values.get("b")
            result = values.get("result")
            if values.get("task_type") == "estimate":
                # Same rationale as addition's estimate branch above --
                # this formatter had no estimate-aware branch at all before
                # (a pre-existing gap, not introduced here; see doc_rem.md R2
                # on this duplication pattern across formatters).
                real_a = values.get("real_a", a)
                real_b = values.get("real_b", b)
                statement = f"{real_a} − {real_b} ≈ {fill_value}"
            elif values.get("task_type") == "expanded_form" and "a_tens" in values:
                # Same root cause as addition's identical fix (see that
                # branch's comment).
                from backend.app.practice_gen.dna.na.addition import decompose_to_places
                statement = (
                    f"{decompose_to_places(a)} {decompose_to_places(b)} "
                    f"Subtract the place values, then find what's left: {a} − {b} = {fill_value}"
                )
            elif blank_target == "result":
                statement = f"{a} − {b} = {fill_value}"
            elif blank_target == "b":
                statement = f"{a} − {fill_value} = {result}"
            else:
                statement = f"{fill_value} − {b} = {result}"
        elif concept == "multiplication":
            a = values.get("a", values.get("groups"))
            b = values.get("b", values.get("n"))
            result = values.get("result", values.get("total"))
            if values.get("task_type") == "estimate":
                real_a = values.get("real_a", a)
                real_b = values.get("real_b", b)
                statement = f"{real_a} × {real_b} ≈ {fill_value}"
            elif blank_target in ("result", "total"):
                statement = f"{a} × {b} = {fill_value}"
            else:
                statement = f"{fill_value} × {b} = {result}"
        elif concept == "division":
            dividend = values.get("dividend", values.get("a"))
            divisor = values.get("divisor", values.get("b"))
            quotient = values.get("quotient", values.get("result"))
            if values.get("task_type") == "estimate":
                real_a = values.get("real_a", dividend)
                real_b = values.get("real_b", divisor)
                statement = f"{real_a} ÷ {real_b} ≈ {fill_value}"
            elif values.get("task_type") == "even_odd":
                # fill_value is "even"/"odd" (a category, not a quotient) --
                # "an" is grammatically correct for both ("an even number",
                # "an odd number"), so no a/an branching is needed. "comes
                # out exactly" avoids the word "remainder", which this
                # node's own NOT_YET_KNOWN vocabulary list forbids at this
                # grade/quarter (caught by §1D vocabulary_gating).
                statement = f"{dividend} ÷ 2 {'comes out exactly' if fill_value == 'even' else 'does not come out exactly'}, so {dividend} is an {fill_value} number"
            elif values.get("task_type") == "repeated_subtraction":
                # Same root cause as even_odd above: "{dividend} ÷
                # {divisor} = {fill_value}" reads identically whether this
                # came from a repeated-subtraction narration or a plain
                # fact, silently discarding the "start with N, subtract M
                # repeatedly" framing (blind review of mat_g2_na_q3_5:
                # "repeated subtraction... is modeled in zero of 18
                # samples"). Built as its own claim (not values["question"]
                # reworded, which is phrased as a question and reads
                # awkwardly forced into a statement) using the same a/b
                # this task_type's own generate_params computed.
                statement = (
                    f"Starting from {dividend} and subtracting {divisor} "
                    f"repeatedly, you subtract {fill_value} times before "
                    f"reaching 0."
                )
            elif blank_target in ("result", "quotient"):
                statement = f"{dividend} ÷ {divisor} = {fill_value}"
            else:
                # blank_target == "b" (divisor_unknown, e.g. "Find the
                # missing number... 54 ÷ ___ = 6"): fill_value is the
                # candidate DIVISOR being tested, not the dividend. The
                # previous version substituted it into the dividend slot
                # while still printing the real divisor and quotient
                # unchanged, so a wrong-divisor trap collapsed to a
                # self-consistent-looking but nonsensical statement (e.g.
                # divisor=9, quotient=9, fill_value=9 all coincidentally
                # equal -> "9 ÷ 9 = 9" keyed True; blind review of
                # mat_g3_na_q4_2 seed 501, actual 9÷9=1).
                statement = f"{dividend} ÷ {fill_value} = {quotient}"
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
                # compare_two's own distractor set includes "cannot be
                # determined" -- a legitimate MCQ trap option, but not a
                # symbol that can grammatically fill "{a} ___ {b}"; picked
                # here it renders "20 cannot be determined 13" (blind
                # review of mat_g1_na_q1_3 and others). Restrict this
                # template's fill slot to an actual comparison symbol.
                sign_fill = fill_value
                if sign_fill not in (">", "<", "="):
                    correct_sign = ctx.correct_answer if ctx.correct_answer in (">", "<", "=") else None
                    wrong_signs = [s for s in (">", "<", "=") if s != correct_sign]
                    sign_fill = rng.choice(wrong_signs) if wrong_signs else "="
                statement = f"{a} {sign_fill} {b}"
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
        # The word_problem/context fallback branches above already end
        # `statement` in its own period ("...The answer is 700."), so
        # unconditionally appending ". True or False?" produced a doubled
        # period ("...700.. True or False?") -- strip any trailing
        # punctuation `statement` already supplied before adding ours.
        question_text=f"{statement.rstrip('.')}. True or False?",
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
