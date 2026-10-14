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

from backend.app.practice_gen.dna.base import (FormattedProblem, QuestionContext, count_noun,
                                                 number_group_name)
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors
from backend.app.practice_gen.formatters._option_order import shuffle_options
from backend.app.practice_gen.formatters._answer_slots import answer_text, distractor_text
from backend.app.practice_gen.slots import E, G, S, carried, derived, fill, join


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
            return fill("Estimate: {real_a} + {real_b} ≈ ___", _src=('task_type',), real_a=S(real_a, f"value:{carried(values, 'real_a', 'a')}", src=('real_a', 'a',)), real_b=S(real_b, f"value:{carried(values, 'real_b', 'b')}", src=('real_b', 'b',)))
        if values.get("task_type") == "expanded_form" and "a_tens" in values:
            # Bare "{a} + {b} = ___" drops the place-value decomposition
            # this task_type exists to demonstrate -- same root cause as the
            # identical fix in fmt_true_false.py (see that file's comment).
            from backend.app.practice_gen.dna.na.addition import decompose_to_places
            return (
                fill("{decompose_to_places} {decompose_to_places2} Add the place values, then find the total: {a} + {b} = ___", _src=('task_type',), decompose_to_places=S(decompose_to_places(a, "value:a"), "fill"), decompose_to_places2=S(decompose_to_places(b, "value:b"), "fill"), a=S(a, "value:a"), b=S(b, "value:b"))
            )
        if values.get("task_type") == "putting_together":
            a_p = fill("{a} item", _src=('a', 'task_type',), a=S(a, "value:a")) if a == 1 else fill("{a} items", _src=('task_type',), a=S(a, "value:a"))
            b_p = fill("{b} item", _src=('b', 'task_type',), b=S(b, "value:b")) if b == 1 else fill("{b} items", _src=('task_type',), b=S(b, "value:b"))
            return fill("One group has {a_p} and another group has {b_p}. Putting them together makes ___ items in all.", _src=('task_type',), a_p=S(a_p, "fill"), b_p=S(b_p, "fill"))
        if values.get("task_type") == "counting_up" and blank_target == "result":
            # Same root cause as expanded_form above -- drops the "start at /
            # count up" narration values["question"] states.
            return fill("Start at {a}. Count up {b} more. You land on ___", _src=('task_type',), a=S(a, "value:a"), b=S(b, "value:b"))
        if blank_target == "result":
            return fill("{a} + {b} = ___", a=S(a, "value:a"), b=S(b, "value:b"))
        elif blank_target == "b":
            return fill("{a} + ___ = {result}", a=S(a, "value:a"), result=S(result, "value:result"))
        else:  # blank_target == "a"
            return fill("___ + {b} = {result}", b=S(b, "value:b"), result=S(result, "value:result"))
    
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
            return fill("Estimate: {real_a} − {real_b} ≈ ___", _src=('task_type',),
                        real_a=S(real_a, "value:real_a"), real_b=S(real_b, "value:real_b"))
        # Structured slots (H3-R1, owner ruling 28) for every subtraction sentence below.
        A, B, RES = S(a, "value:a"), S(b, "value:b"), S(result, "value:result")
        if values.get("task_type") == "expanded_form" and "a_tens" in values:
            # Same root cause as addition's identical fix (see that
            # branch's comment).
            from backend.app.practice_gen.dna.na.addition import decompose_to_places
            return fill(
                "{da} {db} Subtract the place values, then find what's left: {a} − {b} = ___", _src=('task_type',),
                da=S(decompose_to_places(a, "value:a"), "fill"),
                db=S(decompose_to_places(b, "value:b"), "fill"), a=A, b=B)
        if values.get("task_type") in ("illustrate_number_line_or_inverse", "inverse_of_addition", "number_line_subtraction") and values.get("question"):
            q = values["question"]
            if "___" in q:
                return q
            return fill("{q} Answer: ___", _src=('question', 'task_type',), q=S(q, "fill"))
        if values.get("task_type") in ("one_or_two_step_subtraction", "one_step_subtraction", "two_step_subtraction") and values.get("question"):
            q = values["question"]
            if "___" in q:
                return q
            return fill("{q} Answer: ___", _src=('question', 'task_type',), q=S(q, "fill"))
        if values.get("task_type") == "counting_back" and blank_target == "result":
            return fill("Start at {a}. Count back {b}. You land on ___", _src=('task_type',), a=A, b=B)
        if values.get("task_type") == "taking_away" and blank_target == "result":
            item = values.get("item_name", "items")
            forms = E((item, count_noun(1, item)), "values['item_name'] in either number")
            return fill("There are {a} {n_a}. Taking away {b} {n_b} leaves ___ {item}.", _src=('task_type',),
                        a=A, n_a=S(count_noun(a, item), forms), b=B,
                        n_b=S(count_noun(b, item), forms), item=S(item, "value:item_name"))
        if blank_target == "result":
            return fill("{a} − {b} = ___", a=A, b=B)
        elif blank_target == "b":
            return fill("{a} − ___ = {result}", a=A, result=RES)
        else:
            return fill("___ − {b} = {result}", b=B, result=RES)
    
    elif concept == "multiplication":
        a = values.get("a", values.get("groups"))
        b = values.get("b", values.get("n"))
        result = values.get("result", values.get("total"))
        if values.get("task_type") == "estimate":
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return fill("Estimate: {real_a} × {real_b} ≈ ___", _src=('task_type',), real_a=S(real_a, "value:real_a"), real_b=S(real_b, "value:real_b", src=('real_b', 'b', 'n',)))
        if values.get("task_type") == "equal_groups" and blank_target in ("result", "total"):
            group_form = values.get("group_form")
            plural_name = values.get("plural_name")
            if not plural_name:
                plural_name = number_group_name(a, b)
            terms = join(" + ", [S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',))] * b) if b <= 5 else fill("{a} added {b} times", _src=('task_type',), a=S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',)), b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)))
            if group_form == "plural_name":
                return fill("Count {b} {count_noun} ({terms}) = ___", _src=('group_form', 'task_type',), b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)), count_noun=S(count_noun(b, plural_name), "value:plural_name"), terms=S(terms, "fill", src=('b', 'n', 'a', 'groups',)))
            unit = "group" if b == 1 else "groups"
            return fill("{b} {unit} of {a} ({terms}) makes ___ in all", _src=('task_type', 'group_form',), b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)), unit=S(unit, E(("group", "groups"), "group or groups, by the count"), src=('b', 'n',)), a=S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',)), terms=S(terms, "fill", src=('b', 'n', 'a', 'groups',)))
        if values.get("task_type") == "repeated_addition" and blank_target in ("result", "total"):
            terms = join(" + ", [S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',))] * b)
            return fill("{terms} = ___", _src=('task_type',), terms=S(terms, "fill", src=('b', 'n', 'a', 'groups',)))
        if values.get("task_type") == "skip_counting" and blank_target in ("result", "total"):
            seq = join(", ", [derived(a * i, src=(carried(values, 'a', 'groups'), carried(values, 'b', 'n')), why="arithmetic") for i in range(1, b + 1)])
            return fill("Count by {a}s: {seq}. {a} × {b} = ___", _src=('task_type',), a=S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',)), seq=S(seq, "fill", src=('a', 'groups', 'b', 'n',)), b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)))
        if values.get("task_type") == "number_line_jumps" and blank_target in ("result", "total"):
            return fill("Starting at 0, {b} equal jumps of {a} on the number line lands on ___", _src=('task_type',), b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)), a=S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',)))
        if values.get("task_type") == "commutative":
            return fill("{a} × {b} = ___ × {a}", _src=('task_type',), a=S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',)), b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)))
        if values.get("task_type") == "associative":
            c = values.get("c", 3)
            return fill("({a} × {b}) × {c} = {a} × (___ × {c})", _src=('task_type',), a=S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',)), b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)), c=S(c, "value:c", src=('c',)))
        if values.get("task_type") == "distributive":
            c = values.get("c", 5)
            return fill("{a} × ({b} + {c}) = ({a} × {b}) + ({a} × ___)", _src=('task_type',), a=S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',)), b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)), c=S(c, "value:c", src=('c',)))
        if values.get("task_type") == "two_step":
            return fill("({a} × {b}) + 5 = ___", _src=('task_type',), a=S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',)), b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)))
        if blank_target in ("result", "total"):
            return fill("{a} × {b} = ___", a=S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',)), b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)))
        elif blank_target in ("b", "n"):
            return fill("{a} × ___ = {result}", a=S(a, f"value:{carried(values, 'a', 'groups')}", src=('a', 'groups',)), result=S(result, f"value:{carried(values, 'result', 'total')}", src=('result', 'total',)))
        else:
            return fill("___ × {b} = {result}", b=S(b, f"value:{carried(values, 'b', 'n')}", src=('b', 'n',)), result=S(result, f"value:{carried(values, 'result', 'total')}", src=('result', 'total',)))
    
    elif concept == "division":
        dividend = values.get("dividend", values.get("a"))
        divisor = values.get("divisor", values.get("b"))
        quotient = values.get("quotient", values.get("result"))
        if values.get("task_type") == "estimate":
            real_a = values.get("real_a", dividend)
            real_b = values.get("real_b", divisor)
            return fill("Estimate: {real_a} ÷ {real_b} ≈ ___", _src=('task_type',), real_a=S(real_a, "value:real_a"), real_b=S(real_b, "value:real_b", src=('real_b', 'divisor', 'b',)))
        if values.get("task_type") == "even_odd":
            return fill("Divide {dividend} by 2. {dividend} is an ___ number.", _src=('task_type',), dividend=S(dividend, f"value:{carried(values, 'dividend', 'a')}", src=('dividend', 'a',)))
        if values.get("task_type") == "number_line_jumps":
            return fill("Start at {dividend} on a number line and take equal jumps back of {divisor} to reach 0: {dividend} ÷ {divisor} = ___", _src=('task_type',), dividend=S(dividend, "value:a", src=('dividend', 'a',)), divisor=S(divisor, "value:b", src=('divisor', 'b',)))
        if values.get("task_type") == "repeated_subtraction":
            return fill("Start with {dividend}. Subtract {divisor} repeatedly until reaching 0: you subtract ___ times.", _src=('task_type',), dividend=S(dividend, "value:a", src=('dividend', 'a',)), divisor=S(divisor, "value:b", src=('divisor', 'b',)))
        if values.get("task_type") == "inverse_of_multiplication":
            return fill("Since {divisor} × {quotient} = {dividend}, {dividend} ÷ {divisor} = ___", _src=('task_type',), divisor=S(divisor, f"value:{carried(values, 'divisor', 'b')}", src=('divisor', 'b',)), quotient=S(quotient, f"value:{carried(values, 'quotient', 'result')}", src=('quotient', 'result',)), dividend=S(dividend, "value:a", src=('dividend', 'a',)))
        if blank_target in ("result", "quotient"):
            return fill("{dividend} ÷ {divisor} = ___", dividend=S(dividend, "value:a", src=('dividend', 'a',)), divisor=S(divisor, "value:b", src=('divisor', 'b',)))
        elif blank_target in ("b", "divisor", "n"):
            return fill("{dividend} ÷ ___ = {quotient}", dividend=S(dividend, f"value:{carried(values, 'dividend', 'a')}", src=('dividend', 'a',)), quotient=S(quotient, f"value:{carried(values, 'quotient', 'result')}", src=('quotient', 'result',)))
        else:
            return fill("___ ÷ {divisor} = {quotient}", divisor=S(divisor, f"value:{carried(values, 'divisor', 'b')}", src=('divisor', 'b',)), quotient=S(quotient, "value:result", src=('quotient', 'result',)))
    
    elif concept == "counting":
        seq = values.get("sequence") or []
        if seq:
            stem = fill("Find the missing number") if "missing number" in ctx.cumulative_vocab else fill("What comes next")
            # Structured slots (H5, owner rulings 28 and 35): the sequence exhibits the step.
            return fill("{stem}: {seq}, ___",
                        stem=S(stem, G(("Find the missing number", "What comes next"),
                                       "vocab gate 'missing number'", "missing number")),
                        seq=S(join(", ", [S(x, E(tuple(seq), "values['sequence']")) for x in seq]), "fill",
                              src=("sequence", "skip_by", "direction")))
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
            nums_str = join(", ", [S(x, E(tuple(nums), "values['numbers']")) for x in nums])
            return fill("Order these numbers from least to greatest: {nums_str} ___", _src=('task_type',), nums_str=S(nums_str, "fill", src=('numbers',)))
        elif task_type == "find_between":
            return fill("What number is between {a} and {b}? ___", _src=('task_type',), a=S(a, "value:a"), b=S(b, "value:b"))
        else:
            # compare_two is keyed to a relation symbol; asking "which is
            # greater" invites a numeric answer and marks the correct one
            # wrong. Same defect and same fix as base_generator's copy of
            # this stem (three copies of one sentence — see doc_rem.md R2).
            return fill("Compare the numbers: {a} ___ {b}. Which sign is correct: >, <, or =?", a=S(a, "value:a"), b=S(b, "value:b"))
    elif concept == "missing_number":
        op_name = values.get("operation", "addition")
        op_symbols = {"addition": "+", "subtraction": "−",
                      "multiplication": "×", "division": "÷",
                      "equivalent": values.get("equivalent_symbol", "+")}
        op_symbol = op_symbols.get(op_name, "+")
        blank_pos = values.get("blank_position", "result")
        res = values.get("result", values.get("total"))
        a_val = values.get("a")
        b_val = values.get("b")
        if op_name == "equivalent":
            c_val = values.get("c", 1)
            eq_sym = values.get("equivalent_symbol", "+")
            if eq_sym == "+":
                return fill("{a_val} + {b_val} = {c_val} + ___", _src=('equivalent_symbol', 'operation',), a_val=S(a_val, "value:a"), b_val=S(b_val, "value:b"), c_val=S(c_val, "value:c", src=('c',)))
            else:
                return fill("{a_val} − {b_val} = {c_val} − ___", _src=('operation',), a_val=S(a_val, "value:a"), b_val=S(b_val, "value:b"), c_val=S(c_val, "value:c", src=('c',)))
        if blank_pos == "start":
            return fill("___ {op_symbol} {b_val} = {res}", _src=('blank_position',), op_symbol=S(op_symbol, E(tuple(op_symbols.values()), "the operation symbols"), src=('operation', 'equivalent_symbol',)), b_val=S(b_val, "value:b"), res=S(res, "value:result", src=('result', 'total',)))
        elif blank_pos == "change":
            return fill("{a_val} {op_symbol} ___ = {res}", _src=('blank_position',), a_val=S(a_val, "value:a"), op_symbol=S(op_symbol, E(tuple(op_symbols.values()), "the operation symbols"), src=('operation', 'equivalent_symbol',)), res=S(res, f"value:{carried(values, 'result', 'total')}", src=('result', 'total',)))
        else:
            return fill("{a_val} {op_symbol} {b_val} = ___", a_val=S(a_val, "value:a"), op_symbol=S(op_symbol, E(tuple(op_symbols.values()), "the operation symbols"), src=('operation', 'equivalent_symbol',)), b_val=S(b_val, "value:b"))
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
            return fill("Compare the fractions: \\(\\frac{{{a_num}}}{{{a_den}}}\\) ___ \\(\\frac{{{b_num}}}{{{b_den}}}\\). Which sign is correct: >, <, or =?", _src=('operation',), a_num=S(a_num, f"value:{carried(values, 'a_num', 'numerator', 'a')}", src=('a_num', 'numerator', 'a',)), a_den=S(a_den, f"value:{carried(values, 'a_den', 'denominator', 'b')}", src=('a_den', 'denominator', 'b',)), b_num=S(b_num, f"value:{carried(values, 'b_num', 'numerator', 'a')}", src=('b_num', 'numerator', 'a',)), b_den=S(b_den, f"value:{carried(values, 'b_den', 'denominator', 'b')}", src=('b_den', 'denominator', 'b',)))
        if operation in ("add_subtract", "add", "subtract"):
            a_num = values.get("a_num", numer)
            b_num = values.get("b_num", 0)
            a_den = values.get("a_den", denom)
            b_den = values.get("b_den", denom)
            a_part = fill("1 part is") if a_num == 1 else fill("{a_num} parts are", _src=('operation',), a_num=S(a_num, f"value:{carried(values, 'a_num', 'numerator', 'a')}", src=('a_num', 'numerator', 'a',)))
            if operation == "subtract":
                b_part = fill("1 shaded part is") if b_num == 1 else fill("{b_num} shaded parts are", _src=('operation',), b_num=S(b_num, "value:b_num", src=('b_num',)))
                return fill("A shape is divided into {a_den} equal parts. {a_part} shaded. If {b_part} taken away: \\(\\frac{{{a_num}}}{{{a_den}}} - \\frac{{{b_num}}}{{{b_den}}} = ___\\)", _src=('operation',), a_den=S(a_den, f"value:{carried(values, 'a_den', 'denominator', 'b')}", src=('a_den', 'denominator', 'b',)), a_part=S(a_part, "fill", src=('a_num', 'numerator', 'a',)), b_part=S(b_part, "fill", src=('b_num',)), a_num=S(a_num, f"value:{carried(values, 'a_num', 'numerator', 'a')}", src=('a_num', 'numerator', 'a',)), b_num=S(b_num, "value:b_num", src=('b_num',)), b_den=S(b_den, f"value:{carried(values, 'b_den', 'denominator', 'b')}", src=('b_den', 'denominator', 'b',)))
            b_part = fill("1 more part is") if b_num == 1 else fill("{b_num} more parts are", _src=('operation',), b_num=S(b_num, "value:b_num", src=('b_num',)))
            return fill("A shape is divided into {a_den} equal parts. {a_part} shaded and {b_part} shaded: \\(\\frac{{{a_num}}}{{{a_den}}} + \\frac{{{b_num}}}{{{b_den}}} = ___\\)", _src=('operation',), a_den=S(a_den, f"value:{carried(values, 'a_den', 'denominator', 'b')}", src=('a_den', 'denominator', 'b',)), a_part=S(a_part, "fill", src=('a_num', 'numerator', 'a',)), b_part=S(b_part, "fill", src=('b_num',)), a_num=S(a_num, f"value:{carried(values, 'a_num', 'numerator', 'a')}", src=('a_num', 'numerator', 'a',)), b_num=S(b_num, "value:b_num", src=('b_num',)), b_den=S(b_den, f"value:{carried(values, 'b_den', 'denominator', 'b')}", src=('b_den', 'denominator', 'b',)))
        return fill("A shape is divided into {denom} equal parts with {numer} parts shaded. The fraction shaded is ___.", denom=S(denom, f"value:{carried(values, 'denominator', 'b')}", src=('denominator', 'b',)), numer=S(numer, f"value:{carried(values, 'numerator', 'a')}", src=('numerator', 'a',)))
    elif concept == "money_peso":
        if values.get("question"):
            return values["question"]
        if ctx.question_text_with_blank:
            return ctx.question_text_with_blank
        return fill("{question_text}", question_text=S(values.get('question_text', ctx.question_text), "value:question_text" if "question_text" in values else "fill", src=('question_text',)))
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
    # Structured slots (H3-R2): the keyed answer and the generator's distractors, recorded.
    correct = answer_text(ctx.correct_answer, ctx)
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
    for d in [distractor_text(d, ctx) for d in ctx.distractors]:
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
        
        shuffle_options(pool, ctx.node_id, ctx.seed)
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
