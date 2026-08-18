"""
Textual Formatter — Cloze (Fill-in-the-Blank)

Unified formatter for fill-in-the-blank problems.
Respects the 'context' variant:
  - "pure": Shows equation "5 + 3 = ___"
  - "word_problem": Shows story with blank "Maria has 5 apples... She has ___ apples."

For arithmetic: "5 + 3 = ___" or "___ + 3 = 8" (pure)
For word problems: Uses spine-generated text with blank inserted
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors


def _build_equation_sentence(ctx: QuestionContext) -> str:
    """Build pure equation with blank based on concept and blank_target."""
    values = ctx.values
    concept = ctx.dna_concept
    blank_target = ctx.blank_target or "result"
    
    if concept == "addition":
        a = values.get("a")
        b = values.get("b")
        result = values.get("result")
        if values.get("task_type") == "estimate":
            # See fmt_cloze.py's subtraction branch below (this DNA's
            # original estimate-aware fix) and fmt_mcq.py's copy of the
            # same fix -- this formatter also rebuilds its own pure-context
            # text independently.
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return f"Estimate: {real_a} + {real_b} ≈ ___"
        if values.get("task_type") == "expanded_form" and "a_tens" in values:
            # Bare "{a} + {b} = ___" drops the place-value decomposition
            # this task_type exists to demonstrate -- same root cause as the
            # identical fix in fmt_true_false.py (see that file's comment).
            from backend.app.practice_gen.dna.na.addition import decompose_to_places
            return (
                f"{decompose_to_places(a)} {decompose_to_places(b)} "
                f"Add the place values, then find the total: {a} + {b} = ___"
            )
        if values.get("task_type") == "putting_together":
            a_p = f"{a} item" if a == 1 else f"{a} items"
            b_p = f"{b} item" if b == 1 else f"{b} items"
            return f"One group has {a_p} and another group has {b_p}. Putting them together makes ___ items in all."
        if values.get("task_type") == "counting_up" and blank_target == "result":
            # Same root cause as expanded_form above -- drops the "start at /
            # count up" narration values["question"] states.
            return f"Start at {a}. Count up {b} more. You land on ___"
        if blank_target == "result":
            return f"{a} + {b} = ___"
        elif blank_target == "b":
            return f"{a} + ___ = {result}"
        else:  # blank_target == "a"
            return f"___ + {b} = {result}"
    
    elif concept == "subtraction":
        a = values.get("a")
        b = values.get("b")
        result = values.get("result")
        if values.get("task_type") == "estimate":
            # See fmt_mcq.py's identical fix and base_generator's copy of the
            # same branch (this formatter also rebuilds its own pure-context
            # text independently).
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return f"Estimate: {real_a} − {real_b} ≈ ___"
        if values.get("task_type") == "expanded_form" and "a_tens" in values:
            # Same root cause as addition's identical fix (see that
            # branch's comment).
            from backend.app.practice_gen.dna.na.addition import decompose_to_places
            return (
                f"{decompose_to_places(a)} {decompose_to_places(b)} "
                f"Subtract the place values, then find what's left: {a} − {b} = ___"
            )
        if values.get("task_type") == "counting_back" and blank_target == "result":
            return f"Start at {a}. Count back {b}. You land on ___"
        if values.get("task_type") == "taking_away" and blank_target == "result":
            item = values.get("item_name", "items")
            return f"There are {a} {item}. Taking away {b} {item} leaves ___ {item}."
        if blank_target == "result":
            return f"{a} − {b} = ___"
        elif blank_target == "b":
            return f"{a} − ___ = {result}"
        else:
            return f"___ − {b} = {result}"
    
    elif concept == "multiplication":
        a = values.get("a", values.get("groups"))
        b = values.get("b", values.get("n"))
        result = values.get("result", values.get("total"))
        if values.get("task_type") == "estimate":
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return f"Estimate: {real_a} × {real_b} ≈ ___"
        if values.get("task_type") == "equal_groups" and blank_target in ("result", "total"):
            group_form = values.get("group_form")
            plural_name = values.get("plural_name")
            if not plural_name:
                _plurals = {1: "ones", 2: "twos", 3: "threes", 4: "fours", 5: "fives", 6: "sixes", 7: "sevens", 8: "eights", 9: "nines", 10: "tens"}
                plural_name = _plurals.get(a, f"{a}s")
            terms = " + ".join([str(a)] * b) if b <= 5 else f"{a} added {b} times"
            if group_form == "plural_name":
                return f"Count {b} {plural_name} ({terms}) = ___"
            unit = "group" if b == 1 else "groups"
            return f"{b} {unit} of {a} ({terms}) makes ___ in all"
        if values.get("task_type") == "repeated_addition" and blank_target in ("result", "total"):
            terms = " + ".join([str(a)] * b)
            return f"{terms} = ___"
        if values.get("task_type") == "skip_counting" and blank_target in ("result", "total"):
            seq = ", ".join(str(a * i) for i in range(1, b + 1))
            return f"Count by {a}s: {seq}. {a} × {b} = ___"
        if values.get("task_type") == "number_line_jumps" and blank_target in ("result", "total"):
            return f"Starting at 0, {b} equal jumps of {a} on the number line lands on ___"
        if values.get("task_type") == "commutative":
            return f"{a} × {b} = ___ × {a}"
        if values.get("task_type") == "associative":
            c = values.get("c", 3)
            return f"({a} × {b}) × {c} = {a} × (___ × {c})"
        if values.get("task_type") == "distributive":
            c = values.get("c", 5)
            return f"{a} × ({b} + {c}) = ({a} × {b}) + ({a} × ___)"
        if values.get("task_type") == "two_step":
            return f"({a} × {b}) + 5 = ___"
        if blank_target in ("result", "total"):
            return f"{a} × {b} = ___"
        elif blank_target in ("b", "n"):
            return f"{a} × ___ = {result}"
        else:
            return f"___ × {b} = {result}"
    
    elif concept == "division":
        dividend = values.get("dividend", values.get("a"))
        divisor = values.get("divisor", values.get("b"))
        quotient = values.get("quotient", values.get("result"))
        if values.get("task_type") == "estimate":
            real_a = values.get("real_a", dividend)
            real_b = values.get("real_b", divisor)
            return f"Estimate: {real_a} ÷ {real_b} ≈ ___"
        if values.get("task_type") == "number_line_jumps":
            return f"Start at {dividend} on a number line and take equal jumps back of {divisor} to reach 0: {dividend} ÷ {divisor} = ___"
        if values.get("task_type") == "inverse_of_multiplication":
            return f"Since {divisor} × {quotient} = {dividend}, {dividend} ÷ {divisor} = ___"
        if blank_target in ("result", "quotient"):
            return f"{dividend} ÷ {divisor} = ___"
        elif blank_target in ("b", "divisor", "n"):
            return f"{dividend} ÷ ___ = {quotient}"
        else:
            return f"___ ÷ {divisor} = {quotient}"
    
    elif concept == "counting":
        seq = values.get("sequence") or []
        if seq:
            stem = "Find the missing number" if "missing number" in ctx.cumulative_vocab else "What comes next"
            return f"{stem}: {', '.join(str(x) for x in seq)}, ___"
        if ctx.question_text_with_blank:
            return ctx.question_text_with_blank
        raise ValueError("Formatter 'cloze' has no sequence for counting.")
    elif concept == "comparing_ordering":
        task_type = values.get("task_type", "compare_pair")
        a = values.get("a")
        b = values.get("b")
        if values.get("context") == "word_problem" and values.get("question"):
            # Same "formatter rebuilds its own text, discarding
            # values['question']" defect as fmt_mcq.py's identical fix --
            # this branch always built a bare stem regardless of context.
            return values["question"]
        if task_type in ("order_set", "order_sequence"):
            nums = values.get("numbers", [])
            nums_str = ", ".join(str(x) for x in nums)
            return f"Order these numbers from least to greatest: {nums_str} ___"
        elif task_type == "find_between":
            return f"What number is between {a} and {b}? ___"
        else:
            # compare_two is keyed to a relation symbol; asking "which is
            # greater" invites a numeric answer and marks the correct one
            # wrong. Same defect and same fix as base_generator's copy of
            # this stem (three copies of one sentence — see doc_rem.md R2).
            return f"Compare the numbers: {a} ___ {b}. Which sign is correct: >, <, or =?"
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
                return f"{a_val} + {b_val} = {c_val} + ___"
            else:
                return f"{a_val} − {b_val} = {c_val} − ___"
        if blank_pos == "start":
            return f"___ {op_symbol} {b_val} = {res}"
        elif blank_pos == "change":
            return f"{a_val} {op_symbol} ___ = {res}"
        else:
            return f"{a_val} {op_symbol} {b_val} = ___"
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
            return f"Compare the fractions: \\(\\frac{{{a_num}}}{{{a_den}}}\\) ___ \\(\\frac{{{b_num}}}{{{b_den}}}\\). Which sign is correct: >, <, or =?"
        if operation in ("add_subtract", "add", "subtract"):
            a_num = values.get("a_num", numer)
            b_num = values.get("b_num", 0)
            a_den = values.get("a_den", denom)
            b_den = values.get("b_den", denom)
            a_part = "1 part is" if a_num == 1 else f"{a_num} parts are"
            if operation == "subtract":
                b_part = "1 shaded part is" if b_num == 1 else f"{b_num} shaded parts are"
                return f"A shape is divided into {a_den} equal parts. {a_part} shaded. If {b_part} taken away: \\(\\frac{{{a_num}}}{{{a_den}}} - \\frac{{{b_num}}}{{{b_den}}} = ___\\)"
            b_part = "1 more part is" if b_num == 1 else f"{b_num} more parts are"
            return f"A shape is divided into {a_den} equal parts. {a_part} shaded and {b_part} shaded: \\(\\frac{{{a_num}}}{{{a_den}}} + \\frac{{{b_num}}}{{{b_den}}} = ___\\)"
        return f"A shape is divided into {denom} equal parts with {numer} parts shaded. The fraction shaded is ___."
    elif concept == "money_peso":
        if values.get("question"):
            return values["question"]
        if ctx.question_text_with_blank:
            return ctx.question_text_with_blank
        return f"{values.get('question_text', ctx.question_text)}"
    else:
        if ctx.question_text_with_blank:
            return ctx.question_text_with_blank
        raise ValueError(f"Formatter 'cloze' cannot build pure equation for concept '{concept}'.")


def format_cloze(ctx: QuestionContext, rng: random.Random) -> FormattedProblem:
    """
    Format a QuestionContext as a cloze (fill-in-the-blank) problem.

    Respects the 'context' variant in ctx.values or ctx.difficulty_profile:
    - "pure": Shows equation with blank (e.g., "5 + 3 = ___")
    - "word_problem": Shows story with blank (e.g., "Maria has 5 apples and gets 3 more. She has ___ apples.")

    format_data:
        sentence           — the equation/story with ___ in place of the answer
        answer_length_hint — character count of the correct answer
        context            — "pure" or "word_problem"
    """
    values = ctx.values or {}

    # Get context variant - check values first, then difficulty_profile
    context_variant = values.get("context") 
    if context_variant is None and ctx.difficulty_profile:
        context_variant = ctx.difficulty_profile.get("context")
    if context_variant is None:
        context_variant = "pure"  # default
    
    # Build sentence based on context
    if context_variant == "word_problem":
        # Use word problem from values (generated by spine) with blank
        # First check if values has a pre-built "question_with_blank" or "question"
        if "question_with_blank" in values:
            sentence = values["question_with_blank"]
        elif ctx.question_text_with_blank:
            sentence = ctx.question_text_with_blank
        else:
            raise ValueError("Formatter 'cloze' requires 'question_with_blank' or 'question_text_with_blank' for word problems.")
    else:
        # Pure equation: "5 + 3 = ___"
        sentence = _build_equation_sentence(ctx)
    
    answer_str = str(ctx.correct_answer)
    answer_length_hint = len(answer_str)

    format_data = {
        "sentence": sentence,
        "answer_length_hint": answer_length_hint,
        "context": context_variant,
    }

    # Attempt to build MCQ options
    correct = ctx.correct_answer
    candidates = []
    seen = {correct}
    # Same out-of-grade guard as fmt_mcq: a Grade 1-3 pupil has not met numbers
    # below zero, so a negative ErrorPattern value (reversed operands, "b - a")
    # is unreadable rather than tempting. This copy was missed on the first pass
    # and blind reviewers duly found "-14" still on offer for "0 + 14 = ___".
    correct_is_non_negative = (
        isinstance(correct, (int, float))
        and not isinstance(correct, bool)
        and correct >= 0
    )
    for d in ctx.distractors:
        if d is None or str(d).strip().lower() in ("none", "null"):
            continue
        if (
            correct_is_non_negative
            and isinstance(d, (int, float))
            and not isinstance(d, bool)
            and d < 0
        ):
            continue
        if d not in seen:
            candidates.append(d)
            seen.add(d)

    # Pad distractors if needed
    offset_mult = 1
    while len(candidates) < 3:
        if isinstance(correct, (int, float)):
            for sign in [1, -1]:
                candidate = correct + (offset_mult * sign)
                if candidate >= 0 and candidate not in seen:
                    candidates.append(candidate)
                    seen.add(candidate)
                    if len(candidates) >= 3:
                        break
            offset_mult += 1
        else:
            # Non-numeric string answer (e.g. place names): use available distractors
            break

    if len(candidates) < 3 and isinstance(correct, (int, float)) and not isinstance(correct, bool):
        candidates = augment_distractors(candidates, correct, target=3, max_delta=5)
        if len(candidates) < 3:
            raise ValueError(f"Formatter 'cloze' requires at least 3 unique distractors, but got {len(candidates)}. Correct answer: {correct}")

    mcq_options = None
    if len(candidates) > 0:
        distractors = candidates[:3]
        pool = [{"value": correct, "is_correct": True}] + [
            {"value": d, "is_correct": False} for d in distractors
        ]
        
        rng.shuffle(pool)
        keys = ["A", "B", "C", "D"][:len(pool)]
        mcq_options = []
        for key, opt in zip(keys, pool):
            mcq_options.append({"key": key, "value": opt["value"], "text": str(opt["value"]), "is_correct": opt["is_correct"]})
            if opt["is_correct"]:
                format_data["correct_key"] = key
        format_data["mcq_options"] = mcq_options

    # Set format properties
    format_type = "cloze"
    answer_collection = "fill_in_blank"

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_cloze",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=sentence,
        correct_answer=ctx.correct_answer,
        distractors=candidates[:3],
        hints=ctx.hints,
        format=format_type,
        format_data=format_data,
        is_visual=bool(ctx.visual_params),
        visual_type=ctx.visual_type,
        visual_params=ctx.visual_params,
        interaction_mode=None,
        answer_collection=answer_collection,
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
