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

from backend.app.practice_gen.dna.base import (FormattedProblem, QuestionContext, count_noun,
                                                 number_group_name)
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors
from backend.app.practice_gen.formatters._option_order import shuffle_options
from backend.app.practice_gen.formatters._answer_slots import (answer_text, distractor_text,
                                                           member_text)
from backend.app.practice_gen.slots import S, derived, fill


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
            return fill("Estimate the sum: {real_a} + {real_b}", _src=('task_type',), real_a=S(real_a, "value:real_a"), real_b=S(real_b, "value:real_b"))
        if values.get("question"):
            return values["question"]
        if blank_target == "result":
            return fill("What is {a} + {b}?", a=S(a, "value:a"), b=S(b, "value:b"))
        elif blank_target == "b":
            return fill("What number plus {a} equals {result}?", a=S(a, "value:a"), result=S(result, "value:result"))
        else:  # blank_target == "a"
            return fill("What number plus {b} equals {result}?", b=S(b, "value:b"), result=S(result, "value:result"))
    
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
            return fill("Estimate the difference: {real_a} − {real_b}", _src=('task_type',),
                        real_a=S(real_a, "value:real_a"), real_b=S(real_b, "value:real_b"))
        if values.get("task_type") in ("expanded_form", "counting_back", "taking_away", "illustrate_number_line_or_inverse", "inverse_of_addition", "number_line_subtraction", "one_or_two_step_subtraction", "one_step_subtraction", "two_step_subtraction") and values.get("question"):
            # Same root cause as addition's identical fix: this formatter
            # rebuilds its own pure-context question independently of
            # base_generator's values["question"] preference.
            return values["question"]
        # Structured slots (H3-R1, owner ruling 28).
        if blank_target == "result":
            return fill("What is {a} − {b}?", a=S(a, "value:a"), b=S(b, "value:b"))
        elif blank_target == "b":
            return fill("What number subtracted from {a} equals {result}?",
                        a=S(a, "value:a"), result=S(result, "value:result"))
        else:
            return fill("What minus {b} equals {result}?",
                        b=S(b, "value:b"), result=S(result, "value:result"))
    
    elif concept == "multiplication":
        a = values.get("a", values.get("groups"))
        b = values.get("b", values.get("n"))
        result = values.get("result", values.get("total"))
        mul_task_type = values.get("task_type")
        if mul_task_type == "estimate":
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return fill("Estimate the product: {real_a} × {real_b}", _src=('task_type',), real_a=S(real_a, "value:real_a"), real_b=S(real_b, "value:real_b", src=('real_b', 'b', 'n',)))
        if mul_task_type in ("commutative", "associative", "distributive") and values.get("question"):
            # These render a yes/no claim (blank_target="answer", no
            # "result"/"total" key set at all) -- falling through to the
            # blank_target branches below substituted the missing result as
            # the literal string "None" ("What times 2 equals None?"), the
            # same root cause as addition.py's identical task types (see
            # that fix for the full explanation).
            return values["question"]
        if values.get("task_type") == "equal_groups" and blank_target in ("result", "total"):
            group_form = values.get("group_form")
            plural_name = values.get("plural_name")
            if not plural_name:
                plural_name = number_group_name(a, b)
            terms = " + ".join([str(a)] * b) if b <= 5 else fill("{a} added {b} times", _src=('task_type',), a=derived(a, src=('a', 'groups',)), b=derived(b, src=('b', 'n',)))
            if group_form == "plural_name":
                return fill("Count {b} {count_noun} by repeated addition ({terms}): how many in all?", _src=('group_form', 'task_type',), b=derived(b, src=('b', 'n',)), count_noun=derived(count_noun(b, plural_name), src=('b', 'n',)), terms=derived(terms, src=('b', 'n', 'a', 'groups',)))
            unit = "group" if b == 1 else "groups"
            # "There are 1 group of 1" -- the noun was pluralized and the verb was not.
            # One sentence, four copies (doc_rem.md R2); all four say it the same way.
            was = "is" if b == 1 else "are"
            return fill("There {was} {b} {unit} of {a} ({terms}). How many in all?", _src=('task_type', 'group_form',), was=derived(was, src=('b', 'n',)), b=derived(b, src=('b', 'n',)), unit=derived(unit, src=('b', 'n',)), a=derived(a, src=('a', 'groups',)), terms=derived(terms, src=('b', 'n', 'a', 'groups',)))
        if values.get("task_type") == "repeated_addition" and blank_target in ("result", "total"):
            terms = " + ".join([str(a)] * b)
            return fill("{terms} = ___. What is {a} × {b}?", _src=('task_type',), terms=derived(terms, src=('b', 'n', 'a', 'groups',)), a=derived(a, src=('a', 'groups',)), b=derived(b, src=('b', 'n',)))
        if values.get("task_type") == "skip_counting" and blank_target in ("result", "total"):
            seq = ", ".join(str(a * i) for i in range(1, b + 1))
            return fill("Count by {a}s: {seq}. What is {a} × {b}?", _src=('task_type',), a=derived(a, src=('a', 'groups',)), seq=derived(seq, src=('a', 'groups', 'b', 'n',)), b=derived(b, src=('b', 'n',)))
        if values.get("task_type") == "number_line_jumps" and blank_target in ("result", "total"):
            return fill("Starting at 0, take {b} equal jumps of {a} on the number line. What is {a} × {b}?", _src=('task_type',), b=derived(b, src=('b', 'n',)), a=derived(a, src=('a', 'groups',)))
        if blank_target in ("result", "total"):
            return fill("What is {a} × {b}?", a=derived(a, src=('a', 'groups',)), b=derived(b, src=('b', 'n',)))
        elif blank_target in ("b", "n"):
            return fill("What times {a} equals {result}?", a=derived(a, src=('a', 'groups',)), result=derived(result, src=('result', 'total',)))
        else:
            return fill("What times {b} equals {result}?", b=derived(b, src=('b', 'n',)), result=derived(result, src=('result', 'total',)))
    
    elif concept == "division":
        dividend = values.get("dividend", values.get("a"))
        divisor = values.get("divisor", values.get("b"))
        quotient = values.get("quotient", values.get("result"))
        if values.get("task_type") == "estimate":
            real_a = values.get("real_a", dividend)
            real_b = values.get("real_b", divisor)
            stem = fill("Estimate the quotient", _src=('task_type',)) if "quotient" in ctx.cumulative_vocab else fill("Estimate the answer", _src=('task_type',))
            return fill("{stem}: {real_a} ÷ {real_b}", _src=('task_type',), stem=S(stem, "fill"), real_a=S(real_a, "value:real_a"), real_b=S(real_b, "value:real_b", src=('real_b', 'divisor', 'b',)))
        if values.get("task_type") in ("even_odd", "number_line_jumps", "inverse_of_multiplication") and values.get("question"):
            # blank_target="answer" or custom narrative question doesn't fit the bare equations below.
            return values["question"]
        if blank_target in ("result", "quotient"):
            return fill("What is {dividend} ÷ {divisor}?", dividend=S(dividend, "value:a", src=('dividend', 'a',)), divisor=S(divisor, "value:b", src=('divisor', 'b',)))
        elif blank_target in ("b", "divisor", "n"):
            return fill("{dividend} divided by what equals {quotient}?", dividend=derived(dividend, src=('dividend', 'a',)), quotient=derived(quotient, src=('quotient', 'result',)))
        else:
            return fill("What divided by {divisor} equals {quotient}?", divisor=derived(divisor, src=('divisor', 'b',)), quotient=S(quotient, "value:result", src=('quotient', 'result',)))
    
    elif concept == "missing_number":
        op_name = values.get("operation", "addition")
        op_symbol = {"addition": "+", "subtraction": "−",
                     "multiplication": "×", "division": "÷",
                     "equivalent": values.get("equivalent_symbol", "+")}.get(op_name, "+")
        blank_pos = values.get("blank_position", "result")
        res = values.get("result", values.get("total"))
        a_val = values.get("a")
        b_val = values.get("b")
        if op_name == "equivalent":
            c_val = values.get("c", 1)
            eq_sym = values.get("equivalent_symbol", "+")
            if eq_sym == "+":
                return fill("What number completes the expression: {a_val} + {b_val} = {c_val} + ___?", _src=('equivalent_symbol', 'operation',), a_val=S(a_val, "value:a"), b_val=S(b_val, "value:b"), c_val=S(c_val, "value:c", src=('c',)))
            else:
                return fill("What number completes the expression: {a_val} − {b_val} = {c_val} − ___?", _src=('operation',), a_val=S(a_val, "value:a"), b_val=S(b_val, "value:b"), c_val=S(c_val, "value:c", src=('c',)))
        if blank_pos == "start":
            return fill("What number goes in the blank: ___ {op_symbol} {b_val} = {res}?", _src=('blank_position',), op_symbol=derived(op_symbol, src=('operation', 'equivalent_symbol',)), b_val=S(b_val, "value:b"), res=S(res, "value:result", src=('result', 'total',)))
        elif blank_pos == "change":
            return fill("What number goes in the blank: {a_val} {op_symbol} ___ = {res}?", _src=('blank_position',), a_val=S(a_val, "value:a"), op_symbol=derived(op_symbol, src=('operation', 'equivalent_symbol',)), res=S(res, "value:result", src=('result', 'total',)))
        else:
            return fill("What number goes in the blank: {a_val} {op_symbol} {b_val} = ___?", a_val=S(a_val, "value:a"), op_symbol=derived(op_symbol, src=('operation', 'equivalent_symbol',)), b_val=S(b_val, "value:b"))

    elif concept == "fractions":
        if values.get("question"):
            return values["question"]
        numer = values.get("numerator", values.get("a", 1))
        denom = values.get("denominator", values.get("b", 2))
        operation = values.get("operation")
        if operation == "compare":
            a_num = values.get("a_num", numer)
            a_den = values.get("a_den", denom)
            b_num = values.get("b_num", numer)
            b_den = values.get("b_den", denom)
            return fill("Compare the fractions: \\(\\frac{{{a_num}}}{{{a_den}}}\\) ___ \\(\\frac{{{b_num}}}{{{b_den}}}\\). Which sign is correct: >, <, or =?", _src=('operation',), a_num=derived(a_num, src=('a_num', 'numerator', 'a',)), a_den=derived(a_den, src=('a_den', 'denominator', 'b',)), b_num=derived(b_num, src=('b_num', 'numerator', 'a',)), b_den=derived(b_den, src=('b_den', 'denominator', 'b',)))
        if operation in ("add_subtract", "add", "subtract"):
            a_num = values.get("a_num", numer)
            b_num = values.get("b_num", 0)
            a_den = values.get("a_den", denom)
            b_den = values.get("b_den", denom)
            a_part = "1 part is" if a_num == 1 else fill("{a_num} parts are", _src=('operation',), a_num=derived(a_num, src=('a_num', 'numerator', 'a',)))
            if operation == "subtract":
                b_part = "1 shaded part is" if b_num == 1 else fill("{b_num} shaded parts are", _src=('operation',), b_num=derived(b_num, src=('b_num',)))
                return fill("A shape is divided into {a_den} equal parts. {a_part} shaded. If {b_part} taken away, what fraction of the shape remains shaded: \\(\\frac{{{a_num}}}{{{a_den}}} - \\frac{{{b_num}}}{{{b_den}}}\\)?", _src=('operation',), a_den=derived(a_den, src=('a_den', 'denominator', 'b',)), a_part=derived(a_part, src=('a_num', 'numerator', 'a',)), b_part=derived(b_part, src=('b_num',)), a_num=derived(a_num, src=('a_num', 'numerator', 'a',)), b_num=derived(b_num, src=('b_num',)), b_den=derived(b_den, src=('b_den', 'denominator', 'b',)))
            b_part = "1 more part is" if b_num == 1 else fill("{b_num} more parts are", _src=('operation',), b_num=derived(b_num, src=('b_num',)))
            return fill("A shape is divided into {a_den} equal parts. {a_part} shaded and {b_part} shaded. What fraction of the shape is shaded in all: \\(\\frac{{{a_num}}}{{{a_den}}} + \\frac{{{b_num}}}{{{b_den}}}\\)?", _src=('operation',), a_den=derived(a_den, src=('a_den', 'denominator', 'b',)), a_part=derived(a_part, src=('a_num', 'numerator', 'a',)), b_part=derived(b_part, src=('b_num',)), a_num=derived(a_num, src=('a_num', 'numerator', 'a',)), b_num=derived(b_num, src=('b_num',)), b_den=derived(b_den, src=('b_den', 'denominator', 'b',)))
        part_word = "part is" if numer == 1 else "parts are"
        return fill("A shape is divided into {denom} equal parts. {numer} {part_word} shaded. What fraction of the shape is shaded?", denom=derived(denom, src=('denominator', 'b',)), numer=derived(numer, src=('numerator', 'a',)), part_word=derived(part_word, src=('numerator', 'a',)))

    elif concept == "counting":
        seq = values.get("sequence") or []
        direction = values.get("direction", "forward")
        seq_str = ", ".join(str(x) for x in seq)
        # Structured slots (H5, owner rulings 28 and 35): the sequence exhibits the step.
        SEQ = S(seq_str, "text.derived", src=("sequence", "skip_by", "direction"))
        if direction == "backward":
            return fill("What number comes next when counting backward: {seq}, ___?", _src=('direction',), seq=SEQ)
        else:
            return fill("What number comes next when counting: {seq}, ___?", seq=SEQ)
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
            return fill("Order these numbers from least to greatest: {nums_str}", _src=('task_type',), nums_str=derived(nums_str, src=('numbers',)))
        elif task_type == "find_between":
            return fill("What number is between {a} and {b}?", _src=('task_type',), a=S(a, "value:a"), b=S(b, "value:b"))
        elif values.get("statement") is not None:
            # compare_pair is offered as four whole comparison statements under MCQ
            # (owner ruling 2026-09-11, see comparing_ordering.py), so the stem asks
            # which of them is true. The numbers live in the options; repeating them
            # here would make one option a copy of the stem.
            return fill("Which statement is true?", _src=('statement',))
        else:
            # compare_two is keyed to a relation symbol; asking "which is
            # greater" invites a numeric answer and marks the correct one
            # wrong. Same defect and same fix as base_generator's copy of
            # this stem (three copies of one sentence — see doc_rem.md R2).
            return fill("Compare the numbers: {a} ___ {b}. Which sign is correct: >, <, or =?", a=S(a, "value:a"), b=S(b, "value:b"))
    elif concept == "money_peso":
        if values.get("question"):
            return values["question"]
        return ctx.question_text
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

    # comparing_ordering's compare_pair items are offered as four whole comparison
    # statements ("10 < 12", "10 > 12", "10 = 12", "12 < 10"), exactly one of which is
    # true -- owner ruling 2026-09-11, replacing the permanent "cannot be determined"
    # fourth option. Only this formatter shows four whole options, so only this
    # formatter switches presentation; the DNA still keys the sign for cloze and
    # true_false.
    use_statements = (
        ctx.dna_concept == "comparing_ordering"
        and values.get("statement") is not None
        and bool(values.get("statement_distractors"))
    )
    distractor_pool = ctx.distractors
    if use_statements:
        correct = values["statement"]
        distractor_pool = values["statement_distractors"]
    # Structured slots (H3-R2, owner rulings 28 and 33): the option text is the generator's
    # keyed answer and its own distractors, recorded as such. Strings only; same values.
    if use_statements:
        correct = fill("{statement}", statement=S(correct, "value:statement"))
        distractor_pool = [member_text(d, values["statement_distractors"], "values['statement_distractors']")
                           for d in distractor_pool]
    else:
        correct = answer_text(correct, ctx)
        distractor_pool = [distractor_text(d, ctx) for d in distractor_pool]

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

    if use_statements and context_variant == "word_problem":
        # The word-problem narrative reaches here ending on "Which sign correctly
        # compares the two amounts?", which four whole statements do not answer. The
        # DNA supplies the same narrative ending on the question these options DO
        # answer. Absent, that is a contradiction between the item's own stem and its
        # own options, so it fails rather than serving one.
        question_statement = values.get("question_statement")
        if not question_statement:
            raise ValueError(
                f"comparing_ordering served a word-problem compare_pair item with no "
                f"'question_statement' (node={ctx.node_id}, seed={ctx.seed}). MCQ offers "
                f"four comparison STATEMENTS; a stem asking which SIGN is correct asks a "
                f"question its own options cannot answer."
            )
        question_text = question_statement

    # Collect candidate distractors — deduplicate and exclude correct answer
    if isinstance(correct, bool):
        cannot, only_zero = fill("Cannot be determined"), fill("Only when both are 0")
        distractors = [not correct, cannot, only_zero]
        pool = [
            {"value": True, "is_correct": correct is True},
            {"value": False, "is_correct": correct is False},
            {"value": cannot, "is_correct": False},
            {"value": only_zero, "is_correct": False},
        ]
        shuffle_options(pool, ctx.node_id, ctx.seed)
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
    for d in distractor_pool:
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
    shuffle_options(pool, ctx.node_id, ctx.seed)
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
        correct_answer=correct,
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
