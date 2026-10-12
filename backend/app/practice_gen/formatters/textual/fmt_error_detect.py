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

from backend.app.practice_gen.dna.base import (FormattedProblem, QuestionContext, count_noun,
                                                 number_group_name)
from backend.app.practice_gen.slots import E, S, derived, fill, transform
from backend.app.practice_gen.formatters._answer_slots import distractors_field


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


def _distractor_label(distractor: Any, provenance: Any = None) -> str:
    """
    The trap identifier of a planted distractor: the ErrorPattern label that produced it.

    The generator records which pattern produced each distractor VALUE in
    `QuestionContext.distractors_provenance` (base_generator step h); distractors reach this
    formatter as bare values, so the label is read from there (owner ruling 39, 2026-10-11).
    Until then every planted answer was labelled "unknown_error". A value no pattern produced
    (provenance "base": supplied by the DNA itself) has no misconception to name.
    """
    if hasattr(distractor, "label"):
        return distractor.label
    label = (provenance or {}).get(_distractor_value(distractor))
    if label and label != "base":
        return label
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

    # The same position as a structured slot (H3-R2, owner ruling 35): the blank when the
    # position is the unknown, otherwise the value with the `values` keys it shows as `src`.
    def slot_s(*keys, value):
        if blank_target in keys:
            return S("___", E(("___",), "the blank for the unknown blank_target"))
        # Batch H4-0 (ruling 42): the value repeats the first of `keys` the generator's
        # values carry (each call site reads them in that chain), so its domain is that
        # value -- checked against `values`, so a read that took another key escapes loudly.
        present = [k for k in keys if k in values]
        if present:
            return S(value, f"value:{present[0]}", src=tuple(keys))
        return derived(value, src=tuple(keys))

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
            return fill("{real_a} + {real_b} ≈ {slot}", real_a=derived(real_a), real_b=derived(real_b), slot=slot_s('result', value=r))
        if values.get("task_type") == "expanded_form" and "a_tens" in values:
            # Bare "{a} + {b} = {slot}" drops the place-value decomposition
            # this task_type exists to demonstrate -- same root cause as
            # the identical fix in fmt_true_false.py/fmt_cloze.py (see
            # those files' comments). FORMATTER_VARIANT_SUPPORT already
            # allows expanded_form on error_detect (blank_target="result"
            # is a real numeric slot, unlike commutative/associative's
            # yes/no claim), so this was reachable and silently dropping
            # the decomposition rather than being rejected outright.
            from backend.app.practice_gen.dna.na.addition import decompose_to_places
            return (
                fill("{decompose_to_places} {decompose_to_places2} Add the place values, then find the total: {slot} + {slot2} = {slot3}", _src=('task_type',), decompose_to_places=S(decompose_to_places(a, "value:a"), "fill"), decompose_to_places2=S(decompose_to_places(b, "value:b"), "fill"), slot=slot_s('a', value=a), slot2=slot_s('b', value=b), slot3=slot_s('result', value=r))
            )
        if values.get("task_type") == "counting_up" and blank_target == "result":
            # Same root cause as expanded_form above.
            return fill("Start at {slot}. Count up {slot2} more. You land on {slot3}", _src=('task_type',), slot=S(slot('a', value=a), "value:a"), slot2=slot_s('b', value=b), slot3=slot_s('result', value=r))
        return fill("{slot} + {slot2} = {slot3}", slot=slot_s('a', value=a), slot2=slot_s('b', value=b), slot3=slot_s('result', value=r))
    elif concept == "subtraction":
        a, b, r = values.get("a"), values.get("b"), values.get("result")

        # Structured slots (H3-R1, owner ruling 28): a position prints the generated value
        # ("value:<key>") or, when it is the unknown, the blank.
        def sv(key, value):
            if blank_target == key:
                return S("___", E(("___",), "the blank for the unknown blank_target"))
            return S(value, f"value:{key}")

        if is_estimate:
            real_a, real_b = values.get("real_a", a), values.get("real_b", b)
            return fill("{real_a} − {real_b} ≈ {r}", real_a=S(real_a, "value:real_a"),
                        real_b=S(real_b, "value:real_b"), r=sv("result", r))
        if values.get("task_type") == "expanded_form" and "a_tens" in values:
            # Same root cause as addition's identical fix (see that
            # branch's comment).
            from backend.app.practice_gen.dna.na.addition import decompose_to_places
            return fill(
                "{da} {db} Subtract the place values, then find what's left: {a} − {b} = {r}", _src=('task_type',),
                da=S(decompose_to_places(a, "value:a"), "fill"),
                db=S(decompose_to_places(b, "value:b"), "fill"),
                a=sv("a", a), b=sv("b", b), r=sv("result", r))
        if values.get("task_type") in ("illustrate_number_line_or_inverse", "inverse_of_addition", "number_line_subtraction") and values.get("question"):
            q = values["question"]
            if "___" in q:
                return transform("fill_blank", q, value=sv("result", r))
            return fill("{q} (Answer: {r})", _src=('question', 'task_type',), q=S(q, "fill"), r=sv("result", r))
        if values.get("task_type") in ("one_or_two_step_subtraction", "one_step_subtraction", "two_step_subtraction") and values.get("question"):
            return fill("{q} (Answer: {r})", _src=('question', 'task_type',), q=S(values["question"], "fill"), r=sv("result", r))
        if values.get("task_type") == "counting_back" and blank_target == "result":
            return fill("Start at {a}. Count back {b}. You land on {r}", _src=('task_type',),
                        a=sv("a", a), b=sv("b", b), r=sv("result", r))
        if values.get("task_type") == "taking_away" and blank_target == "result":
            item = values.get("item_name", "items")
            forms = E((item, count_noun(1, item)), "values['item_name'] in either number")
            # A blanked slot prints "___", so its noun stays plural: the quantity is the
            # thing the pupil has to supply and "___ cookie" would give it away.
            def noun(key, value):
                return S(item if blank_target == key else count_noun(value, item), forms)
            return fill("There are {a} {n_a}. Taking away {b} {n_b} leaves {r} {n_r}.", _src=('task_type',),
                        a=sv("a", a), n_a=noun("a", a), b=sv("b", b), n_b=noun("b", b),
                        r=sv("result", r), n_r=noun("result", r))
        return fill("{a} − {b} = {r}", a=sv("a", a), b=sv("b", b), r=sv("result", r))
    elif concept == "multiplication":
        a = values.get("a", values.get("groups"))
        b = values.get("b", values.get("n"))
        r = values.get("result", values.get("total"))
        if is_estimate:
            real_a, real_b = values.get("real_a", a), values.get("real_b", b)
            return fill("{real_a} × {real_b} ≈ {slot}", real_a=S(real_a, "value:real_a"), real_b=S(real_b, "value:real_b"), slot=slot_s('result', 'total', value=r))
        if values.get("task_type") == "equal_groups" and blank_target in ("result", "total"):
            group_form = values.get("group_form")
            plural_name = values.get("plural_name")
            if not plural_name:
                plural_name = number_group_name(a, b)
            terms = " + ".join([str(a)] * b) if b <= 5 else fill("{a} added {b} times", _src=('task_type',), a=derived(a, src=('a', 'groups',)), b=derived(b, src=('b', 'n',)))
            if group_form == "plural_name":
                return fill("Count {b} {count_noun} by repeated addition: {terms} = {slot}", _src=('group_form', 'task_type',), b=derived(b, src=('b', 'n',)), count_noun=derived(count_noun(b, plural_name), src=('b', 'n',)), terms=derived(terms, src=('b', 'n', 'a', 'groups',)), slot=slot_s('result', 'total', value=r))
            unit = "group" if b == 1 else "groups"
            # "There are 1 group of 1" -- the noun was pluralized and the verb was not.
            # One sentence, four copies (doc_rem.md R2); all four say it the same way.
            was = "is" if b == 1 else "are"
            return fill("There {was} {b} {unit} of {a} ({terms}), so there are {slot} in all.", _src=('task_type',), was=derived(was, src=('b', 'n',)), b=derived(b, src=('b', 'n',)), unit=derived(unit, src=('b', 'n',)), a=derived(a, src=('a', 'groups',)), terms=derived(terms, src=('b', 'n', 'a', 'groups',)), slot=slot_s('result', 'total', value=r))
        if values.get("task_type") == "repeated_addition" and blank_target in ("result", "total"):
            terms = " + ".join([str(a)] * b)
            return fill("{terms} = {slot}", _src=('task_type',), terms=derived(terms, src=('b', 'n', 'a', 'groups',)), slot=slot_s('result', 'total', value=r))
        if values.get("task_type") == "skip_counting" and blank_target in ("result", "total"):
            seq = ", ".join(str(a * i) for i in range(1, b + 1))
            return fill("Counting by {a}s: {seq}, so {a} × {b} = {slot}", _src=('task_type',), a=derived(a, src=('a', 'groups',)), seq=derived(seq, src=('a', 'groups', 'b', 'n',)), b=derived(b, src=('b', 'n',)), slot=slot_s('result', 'total', value=r))
        if values.get("task_type") == "number_line_jumps" and blank_target in ("result", "total"):
            return fill("Starting at 0, taking {b} equal jumps of {a} on the number line lands on {slot}", _src=('task_type',), b=derived(b, src=('b', 'n',)), a=derived(a, src=('a', 'groups',)), slot=slot_s('result', 'total', value=r))
        if values.get("task_type") == "commutative":
            return fill("{a} × {b} = {slot} × {a}", _src=('task_type',), a=derived(a, src=('a', 'groups',)), b=derived(b, src=('b', 'n',)), slot=slot_s('b', value=b))
        if values.get("task_type") == "associative":
            c = values.get("c", 3)
            return fill("({a} × {b}) × {c} = {a} × ({slot} × {c})", _src=('task_type',), a=derived(a, src=('a', 'groups',)), b=derived(b, src=('b', 'n',)), c=derived(c, src=('c',)), slot=slot_s('b', value=b))
        if values.get("task_type") == "distributive":
            c = values.get("c", 5)
            return fill("{a} × ({b} + {c}) = ({a} × {b}) + ({a} × {slot})", _src=('task_type',), a=derived(a, src=('a', 'groups',)), b=derived(b, src=('b', 'n',)), c=derived(c, src=('c',)), slot=slot_s('c', value=c))
        if values.get("task_type") == "two_step":
            return fill("({a} × {b}) + 5 = {slot}", _src=('task_type',), a=derived(a, src=('a', 'groups',)), b=derived(b, src=('b', 'n',)), slot=slot_s('result', 'total', value=r))
        return (
            fill("{slot} × {slot2} = {slot3}", slot=slot_s('a', 'groups', value=a), slot2=slot_s('b', 'n', value=b), slot3=slot_s('result', 'total', value=r))
        )
    elif concept == "division":
        dividend = values.get("dividend", values.get("a"))
        divisor = values.get("divisor", values.get("b"))
        quotient = values.get("quotient", values.get("result"))
        if is_estimate:
            real_a = values.get("real_a", dividend)
            real_b = values.get("real_b", divisor)
            return fill("{real_a} ÷ {real_b} ≈ {slot}", real_a=S(real_a, "value:real_a"), real_b=S(real_b, "value:real_b", src=('real_b', 'divisor', 'b',)), slot=slot_s('result', 'quotient', value=quotient))
        if values.get("task_type") == "even_odd":
            return fill("Divide {dividend} by 2. {dividend} is an {slot} number.", _src=('task_type',), dividend=derived(dividend, src=('dividend', 'a',)), slot=slot_s('answer', value=values.get('answer')))
        if values.get("task_type") == "number_line_jumps":
            return fill("Starting at {dividend} on a number line, taking equal jumps back of {divisor} takes {slot} jumps to reach 0", _src=('task_type',), dividend=S(dividend, "value:a", src=('dividend', 'a',)), divisor=S(divisor, "value:b", src=('divisor', 'b',)), slot=slot_s('result', 'quotient', value=quotient))
        if values.get("task_type") == "repeated_subtraction":
            return fill("Starting from {dividend} and subtracting {divisor} repeatedly, you subtract {slot} times before reaching 0", _src=('task_type',), dividend=S(dividend, "value:a", src=('dividend', 'a',)), divisor=S(divisor, "value:b", src=('divisor', 'b',)), slot=slot_s('result', 'quotient', value=quotient))
        if values.get("task_type") == "inverse_of_multiplication":
            return fill("Since {divisor} × {quotient} = {dividend}, then {dividend} ÷ {divisor} = {slot}", _src=('task_type',), divisor=derived(divisor, src=('divisor', 'b',)), quotient=derived(quotient, src=('quotient', 'result',)), dividend=derived(dividend, src=('dividend', 'a',)), slot=slot_s('result', 'quotient', value=quotient))
        return (
            fill("{slot} ÷ {slot2} = {slot3}", slot=slot_s('a', 'dividend', value=dividend), slot2=slot_s('b', 'divisor', value=divisor), slot3=slot_s('result', 'quotient', value=quotient))
        )
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
                return fill("{a_val} + {b_val} = {c_val} + ___", _src=('equivalent_symbol', 'operation',), a_val=S(a_val, "value:a"), b_val=S(b_val, "value:b"), c_val=derived(c_val, src=('c',)))
            else:
                return fill("{a_val} − {b_val} = {c_val} − ___", _src=('operation',), a_val=S(a_val, "value:a"), b_val=S(b_val, "value:b"), c_val=derived(c_val, src=('c',)))
        if blank_pos == "start":
            return fill("___ {op_symbol} {b_val} = {res}", _src=('blank_position',), op_symbol=derived(op_symbol, src=('operation', 'equivalent_symbol',)), b_val=S(b_val, "value:b"), res=derived(res, src=('result', 'total',)))
        elif blank_pos == "change":
            return fill("{a_val} {op_symbol} ___ = {res}", _src=('blank_position',), a_val=S(a_val, "value:a"), op_symbol=derived(op_symbol, src=('operation', 'equivalent_symbol',)), res=derived(res, src=('result', 'total',)))
        else:
            return fill("{a_val} {op_symbol} {b_val} = ___", a_val=S(a_val, "value:a"), op_symbol=derived(op_symbol, src=('operation', 'equivalent_symbol',)), b_val=S(b_val, "value:b"))
    elif concept == "fractions":
        if values.get("question"):
            res_str = values.get("result", values.get("fraction_str", ""))
            return fill("{question} (Answer: {slot})", _src=('question',), question=S(values['question'], "value:question"), slot=slot_s('result', 'fraction', value=res_str))
        numer = values.get("numerator", values.get("a", 1))
        denom = values.get("denominator", values.get("b", 2))
        operation = values.get("operation")
        res_str = values.get("result", fill("{numer}/{denom}", numer=derived(numer, src=('numerator', 'a',)), denom=derived(denom, src=('denominator', 'b',))))
        if operation == "compare":
            a_num = values.get("a_num", numer)
            a_den = values.get("a_den", denom)
            b_num = values.get("b_num", numer)
            b_den = values.get("b_den", denom)
            return fill("\\(\\frac{{{a_num}}}{{{a_den}}}\\) {slot} \\(\\frac{{{b_num}}}{{{b_den}}}\\)", _src=('operation',), a_num=derived(a_num, src=('a_num', 'numerator', 'a',)), a_den=derived(a_den, src=('a_den', 'denominator', 'b',)), slot=slot_s('result', 'sign', value=res_str), b_num=derived(b_num, src=('b_num', 'numerator', 'a',)), b_den=derived(b_den, src=('b_den', 'denominator', 'b',)))
        if operation in ("add_subtract", "add", "subtract"):
            a_num = values.get("a_num", numer)
            b_num = values.get("b_num", 0)
            a_den = values.get("a_den", denom)
            b_den = values.get("b_den", denom)
            op_sym = "+" if operation in ("add_subtract", "add") else "−"
            return fill("\\(\\frac{{{a_num}}}{{{a_den}}} {op_sym} \\frac{{{b_num}}}{{{b_den}}} = {slot}\\)", _src=('operation',), a_num=derived(a_num, src=('a_num', 'numerator', 'a',)), a_den=derived(a_den, src=('a_den', 'denominator', 'b',)), op_sym=derived(op_sym, src=('operation',)), b_num=derived(b_num, src=('b_num',)), b_den=derived(b_den, src=('b_den', 'denominator', 'b',)), slot=slot_s('result', 'fraction', value=res_str))
        return fill("A shape is divided into {denom} equal parts with {numer} parts shaded, representing {slot}", denom=derived(denom, src=('denominator', 'b',)), numer=derived(numer, src=('numerator', 'a',)), slot=slot_s('result', 'fraction', value=res_str))
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
            error_label = _distractor_label(planted_distractor, ctx.distractors_provenance)
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
    # Structured slots (H3-R1, owner ruling 28). The actor is one of this file's names;
    # the claimed answer is the keyed answer or one of the distractor candidates it was
    # drawn from; the label is one of those candidates' labels, or "none".
    ACTOR = S(actor, "enum:backend.app.practice_gen.formatters.textual.fmt_error_detect._FILIPINO_NAMES")
    ANSWER = S(actors_answer, E((ctx.correct_answer,) + tuple(_distractor_value(d) for d in ctx.distractors),
                                "the keyed answer and the distractor candidates"))
    PROBLEM = S(problem_text, "fill")
    if "___" in problem_text:
        miss_lbl = "missing number" if "missing number" in ctx.cumulative_vocab else "blank"
        question_text = fill(
            '{actor} solved: "{problem}". {actor} says the {miss} is {answer}. Is {actor} correct?',
            actor=ACTOR, problem=PROBLEM, answer=ANSWER,
            miss=S(miss_lbl, E(("missing number", "blank"), "vocab gate 'missing number'")))
    elif problem_text.strip().endswith("?") or context_variant != "pure":
        question_text = fill(
            '{actor} solved this problem: "{problem}" {actor} says the answer is {answer}. '
            'Is {actor} correct?',
            actor=ACTOR, problem=PROBLEM, answer=ANSWER)
    else:
        question_text = fill("{actor} says: {problem} = {answer}. Is {actor} correct?",
                             actor=ACTOR, problem=PROBLEM, answer=ANSWER)

    # correct_answer encodes both parts
    correct_answer = {
        "has_error": has_error,
        "correct_value": ctx.correct_answer,
    }

    format_data = {
        "actor_name": fill("{actor}", actor=ACTOR),
        "problem_expression": problem_text,
        "actors_answer": actors_answer,
        "has_error": has_error,
        "correct_value": ctx.correct_answer,
        # A trap identifier, not learner text (owner ruling 38): classed as metadata by §1J/§14.
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
        distractors=distractors_field(ctx),
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
