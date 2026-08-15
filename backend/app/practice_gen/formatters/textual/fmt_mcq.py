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
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors


def _build_pure_question(ctx: QuestionContext) -> str:
    """Build a pure equation question based on concept."""
    values = ctx.values or {}
    concept = ctx.dna_concept
    blank_target = ctx.blank_target or "result"
    
    if concept == "addition":
        a = values.get("a")
        b = values.get("b")
        result = values.get("result")
        task_type = values.get("task_type")
        if task_type == "estimate":
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return f"Estimate the sum: {real_a} + {real_b}"
        if values.get("question"):
            return values["question"]
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
        if values.get("task_type") == "estimate":
            # See base_generator._build_symbolic_question's identical branch:
            # this formatter rebuilds its own pure-context question text
            # independently (a pre-existing duplication -- see doc_rem.md
            # R2), so the same estimate-aware fix has to be applied here too.
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return f"Estimate the difference: {real_a} − {real_b}"
        if values.get("task_type") == "expanded_form" and values.get("question"):
            # Same root cause as addition's identical fix: this formatter
            # rebuilds its own pure-context question independently of
            # base_generator's values["question"] preference.
            return values["question"]
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
        mul_task_type = values.get("task_type")
        if mul_task_type == "estimate":
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return f"Estimate the product: {real_a} × {real_b}"
        if mul_task_type in ("commutative", "associative", "distributive") and values.get("question"):
            # These render a yes/no claim (blank_target="answer", no
            # "result"/"total" key set at all) -- falling through to the
            # blank_target branches below substituted the missing result as
            # the literal string "None" ("What times 2 equals None?"), the
            # same root cause as addition.py's identical task types (see
            # that fix for the full explanation).
            return values["question"]
        if values.get("task_type") == "equal_groups" and blank_target in ("result", "total"):
            # See base_generator._build_symbolic_question's identical branch.
            # mat_g2_na_q3_0's competency states the skill in group language
            # ("create equal groups, using ... '5 groups of 3'"), and this
            # formatter rebuilds its own pure-context question text
            # independently of that function, so the same framing has to be
            # applied here too -- mcq is the majority formatter for this node,
            # so without this copy the group language never reaches a student.
            unit = "group" if b == 1 else "groups"
            return f"There are {b} {unit} of {a}. How many in all?"
        if values.get("task_type") == "repeated_addition" and blank_target in ("result", "total") and 2 <= b <= 5:
            # See base_generator._build_symbolic_question's identical branch:
            # "What is 4 x 3?" doesn't illustrate repeated addition, it just
            # states the fact. This formatter rebuilds its own pure-context
            # question text independently of that function (a pre-existing
            # duplication -- see doc_rem.md R2), so the same fix has to be
            # applied here too or "pure"-context mcq items (the majority
            # formatter for this node) never show it.
            terms = " + ".join([str(a)] * b)
            return f"{terms} = ___. What is {a} × {b}?"
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
        if values.get("task_type") == "estimate":
            real_a = values.get("real_a", dividend)
            real_b = values.get("real_b", divisor)
            return f"Estimate the quotient: {real_a} ÷ {real_b}"
        if values.get("task_type") == "even_odd" and values.get("question"):
            # blank_target="answer" (a categorical "even"/"odd" string, not
            # a quotient) doesn't fit any of the branches below -- same root
            # cause as addition/multiplication's identical fix: this
            # formatter rebuilds its own pure-context question independently
            # of base_generator's values["question"] preference.
            return values["question"]
        if blank_target in ("result", "quotient"):
            return f"What is {dividend} ÷ {divisor}?"
        elif blank_target in ("b", "divisor", "n"):
            return f"{dividend} divided by what equals {quotient}?"
        else:
            return f"What divided by {divisor} equals {quotient}?"
    
    elif concept == "counting":
        seq = values.get("sequence") or []
        direction = values.get("direction", "forward")
        seq_str = ", ".join(str(x) for x in seq)
        if direction == "backward":
            return f"What number comes next when counting backward: {seq_str}, ___?"
        else:
            return f"What number comes next when counting: {seq_str}, ___?"
    elif concept == "comparing_ordering":
        task_type = values.get("task_type", "compare_pair")
        a = values.get("a")
        b = values.get("b")
        if values.get("context") == "word_problem" and values.get("question"):
            # This branch always built its own bare "Compare the numbers:
            # X ___ Y"/"Order these numbers..." stem, ignoring
            # values["question"] entirely -- comparing_ordering.py's new
            # word-problem narrative (set only when context==
            # "word_problem") was silently discarded, so every sample
            # rendered the identical template regardless of context
            # (blind review: variant_comprehensiveness FAIL/CONCERN
            # across mat_g1_na_q1_3/_4, mat_g1_na_q2_0, mat_g2_na_q1_4,
            # mat_g3_na_q1_5/_6, "11 of 12 samples reuse the identical
            # bare stem").
            return values["question"]
        if task_type in ("order_set", "order_sequence"):
            nums = values.get("numbers", [])
            nums_str = ", ".join(str(x) for x in nums)
            return f"Order these numbers from least to greatest: {nums_str}"
        elif task_type == "find_between":
            return f"What number is between {a} and {b}?"
        else:
            # compare_two is keyed to a relation symbol; asking "which is
            # greater" invites a numeric answer and marks the correct one
            # wrong. Same defect and same fix as base_generator's copy of
            # this stem (three copies of one sentence — see doc_rem.md R2).
            return f"Compare the numbers: {a} ___ {b}. Which sign is correct: >, <, or =?"
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
    if isinstance(correct, bool):
        distractors = [not correct, "Cannot be determined", "Only when both are 0"]
        pool = [
            {"value": True, "is_correct": correct is True},
            {"value": False, "is_correct": correct is False},
            {"value": "Cannot be determined", "is_correct": False},
            {"value": "Only when both are 0", "is_correct": False},
        ]
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
            is_visual=bool(ctx.visual_params),
            visual_type=ctx.visual_type,
            visual_params=ctx.visual_params,
            interaction_mode=None,
            answer_collection="mcq",
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

    candidates: List = []
    seen = {str(correct).strip().lower()}
    correct_is_non_negative = (
        isinstance(correct, (int, float))
        and not isinstance(correct, bool)
        and correct >= 0
    )
    for d in ctx.distractors:
        if d is None:
            continue
        d_str = str(d).strip().lower()
        if d_str in ("none", "null"):
            continue
        # Drop negative distractors when the answer itself is non-negative. Some
        # ErrorPattern misconceptions (reversed operands, "b - a") legitimately
        # evaluate below zero, but a Grade 1-3 pupil has not met negative numbers,
        # so the option is unreadable rather than tempting — blind reviewers
        # flagged -34, -14 and -3 across money, addition and multiplication items.
        # The padding below refills the slot with an in-range value.
        if (
            correct_is_non_negative
            and isinstance(d, (int, float))
            and not isinstance(d, bool)
            and d < 0
        ):
            continue
        if d_str not in seen:
            candidates.append(d)
            seen.add(d_str)

    # Pad distractors if needed (arithmetic fallbacks)
    offset_mult = 1
    while len(candidates) < 3:
        if isinstance(correct, (int, float)):
            for sign in [1, -1]:
                candidate = correct + (offset_mult * sign)
                # Keep numeric fallbacks >= 0 if possible, but allow negatives if needed to reach 3
                if candidate >= 0 and str(candidate) not in seen:
                    candidates.append(candidate)
                    seen.add(str(candidate))
                    if len(candidates) >= 3:
                        break
            offset_mult += 1
        else:
            # Non-numeric string answer (e.g. place names): use available distractors
            break

    if len(candidates) < 3 and isinstance(correct, (int, float)) and not isinstance(correct, bool):
        candidates = augment_distractors(candidates, correct, target=3, max_delta=5)
        if len(candidates) < 3:
            raise ValueError(f"MCQ formatter requires at least 3 unique distractors, but got {len(candidates)}: {candidates}")

    if not candidates:
        raise ValueError(f"MCQ formatter requires at least 1 distractor, but got none for {correct!r}")

    distractors = candidates[:3]

    # Build option pool: correct first, then distractors
    pool = [{"value": correct, "is_correct": True}] + [
        {"value": d, "is_correct": False} for d in distractors
    ]

    # Shuffle and assign keys
    rng.shuffle(pool)
    keys = ["A", "B", "C", "D"][:len(pool)]
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
        is_visual=bool(ctx.visual_params),
        visual_type=ctx.visual_type,
        visual_params=ctx.visual_params,
        interaction_mode=None,
        answer_collection="mcq",
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
