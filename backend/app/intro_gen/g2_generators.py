"""
Grade 2 Intro Content Generators
Covers: G2 NA Q1-Q4, G2 MG Q1/Q2/Q4, G2 DP Q3

Visual types used:
  Existing (implemented): NumberLine, PlaceValueBlocks, ObjectGroup, NumberCards,
                          TenFrame, Comparison, PesoMoney, ClockSet, Calendar
  New (need frontend):    SkipCountLine, ArrayGrid, FractionBar, PatternRow,
                          PictographDisplay, LengthCompare, RulerDisplay, ShapeDisplay
"""

import random
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# G2 NA Q1 — Numbers to 1000, Place Value (Hundreds), Addition to 1000
# ---------------------------------------------------------------------------

def _gen_g2_na_q1_numbers(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Numbers to 1000, skip counting, ordering (_0–_5)."""
    slides = []

    # Strategy 1: show 1000 as 10 hundreds
    slides.append({
        "type": "worked_example",
        "title": "Numbers to 1 000",
        "strategy": "place_value",
        "steps": [
            {"text": "Numbers go past 100.\n10 hundreds make 1 000.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": 1000, "mode": "show_hundreds"}},
            {"text": "The numeral 1 000 has 4 digits.\nThe 1 is in the thousands place.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": 1000, "highlight_place": "thousands"}},
            {"text": "We can count: 100, 200, 300... all the way to 1 000.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 2: skip counting by 100s
    start = rng.choice([100, 200, 300])
    seq = [start + 100 * i for i in range(5)]
    slides.append({
        "type": "worked_example",
        "title": "Skip Counting by 100s",
        "strategy": "skip_count",
        "steps": [
            {"text": f"Skip count by 100s starting at {seq[0]}.",
             "visual_type": "SkipCountLine",
             "visual_params": {"start": 0, "end": 1050, "step": 100, "from": seq[0], "highlight": seq}},
            {"text": f"{', '.join(str(x) for x in seq)}...\nEach jump is 100.",
             "visual_type": "SkipCountLine",
             "visual_params": {"start": 0, "end": 1050, "step": 100, "from": seq[0], "highlight": seq}},
            {"text": f"What comes after {seq[-1]}? $\\goldE{{{seq[-1] + 100}}}$.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 3: ordinal numbers to 20th
    slides.append({
        "type": "worked_example",
        "title": "Ordinal Numbers to 20th",
        "strategy": "ordinal_position",
        "steps": [
            {"text": "1st, 2nd, 3rd... 10th show position in a line.\nOrdinal numbers keep going.",
             "visual_type": "OrderedLine",
             "visual_params": {"items": list(range(1, 11)), "ordinals": True}},
            {"text": "After 10th comes 11th, 12th, 13th... all the way to 20th.",
             "visual_type": "OrderedLine",
             "visual_params": {"items": list(range(11, 21)), "ordinals": True}},
            {"text": "20th means position 20 in a line.",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g2_na_q1_hundreds(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Place Value: Hundreds (_6)."""
    slides = []

    num = rng.randint(102, 899)
    while len(set(str(num))) < 3:
        num = rng.randint(102, 899)
    h = num // 100
    t = (num % 100) // 10
    o = num % 10

    slides.append({
        "type": "worked_example",
        "title": "Hundreds, Tens and Ones",
        "strategy": "place_value",
        "steps": [
            {"text": f"The numeral $\\blueE{{{num}}}$ has 3 digits.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": num}},
            {"text": f"$\\blueE{{{h}}}$ hundreds = $\\blueE{{{h * 100}}}$\n$\\maroonD{{{t}}}$ tens = $\\maroonD{{{t * 10}}}$\n$\\goldE{{{o}}}$ ones = $\\goldE{{{o}}}$",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": num, "highlight_all": True}},
            {"text": f"$\\blueE{{{num}}}$ = $\\blueE{{{h * 100}}}$ + $\\maroonD{{{t * 10}}}$ + $\\goldE{{{o}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Expanded form
    num2 = rng.randint(213, 785)
    h2 = num2 // 100
    t2 = (num2 % 100) // 10
    o2 = num2 % 10
    slides.append({
        "type": "worked_example",
        "title": "Expanded Form to 1 000",
        "strategy": "expanded_form",
        "steps": [
            {"text": f"Write $\\blueE{{{num2}}}$ in expanded form.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": num2}},
            {"text": f"$\\blueE{{{num2}}}$ = $\\blueE{{{h2 * 100}}}$ + $\\maroonD{{{t2 * 10}}}$ + $\\goldE{{{o2}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g2_na_q1_addition(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Addition to 1000 with/without regrouping (_7–_10)."""
    slides = []

    # Strategy 1: addition without regrouping
    a_h = rng.randint(1, 4)
    b_h = rng.randint(1, 4 - a_h + 1)
    a_t = rng.randint(0, 4)
    b_t = rng.randint(0, min(4, 9 - a_t))
    a_o = rng.randint(0, 4)
    b_o = rng.randint(0, 4 - a_o)
    a = a_h * 100 + a_t * 10 + a_o
    b = b_h * 100 + b_t * 10 + b_o
    result = a + b

    slides.append({
        "type": "worked_example",
        "title": "Adding to 1 000",
        "strategy": "place_value_addition",
        "steps": [
            {"text": f"Add $\\blueE{{{a}}}$ + $\\maroonD{{{b}}}$.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number_a": a, "number_b": b, "mode": "add"}},
            {"text": f"Add hundreds: {a_h} + {b_h} = {a_h + b_h}\nAdd tens: {a_t} + {b_t} = {a_t + b_t}\nAdd ones: {a_o} + {b_o} = {a_o + b_o}",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number_a": a, "number_b": b, "mode": "add", "show_steps": True}},
            {"text": f"$\\blueE{{{a}}}$ + $\\maroonD{{{b}}}$ = $\\goldE{{{result}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 2: regrouping
    c_t = rng.randint(5, 9)
    d_t = rng.randint(10 - c_t, 9)  # ones will regroup
    c_o = rng.randint(5, 9)
    d_o = rng.randint(10 - c_o, 9)
    c = 100 + c_t * 10 + c_o
    d = 100 + d_t * 10 + d_o
    result2 = c + d

    slides.append({
        "type": "worked_example",
        "title": "Adding with Regrouping",
        "strategy": "regrouping",
        "steps": [
            {"text": f"Add $\\blueE{{{c}}}$ + $\\maroonD{{{d}}}$.\nThe ones add up to more than 9.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number_a": c, "number_b": d, "mode": "add"}},
            {"text": f"Ones: {c_o} + {d_o} = {c_o + d_o}. Regroup 10 ones as 1 ten.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number_a": c, "number_b": d, "mode": "add", "show_regroup": True}},
            {"text": f"$\\blueE{{{c}}}$ + $\\maroonD{{{d}}}$ = $\\goldE{{{result2}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G2 NA Q2 — Money to 1000, Subtraction, Increasing/Decreasing Patterns
# ---------------------------------------------------------------------------

def _gen_g2_na_q2_money(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Money to 1000, centavo (_0, _1, _2)."""
    slides = []

    slides.append({
        "type": "worked_example",
        "title": "Centavo Coins",
        "strategy": "money_identification",
        "steps": [
            {"text": "100 centavos make 1 peso.\nCentavo coins are smaller than pesos.",
             "visual_type": "PesoMoney",
             "visual_params": {"coins": [25, 10, 5, 1], "unit": "centavo", "mode": "display"}},
            {"text": "25 centavos + 25 centavos = 50 centavos = half a peso.",
             "visual_type": "PesoMoney",
             "visual_params": {"coins": [25, 25], "unit": "centavo", "mode": "count"}},
            {"text": "100 centavos = ₱1.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Money word problem
    price = rng.randint(50, 200)
    paid = rng.choice([200, 250, 300, 500])
    while paid < price:
        paid = rng.choice([200, 250, 300, 500])
    change = paid - price
    obj = rng.choice(interest_ctx["objects"]) if interest_ctx else "item"
    actor = rng.choice(interest_ctx["actors"]) if interest_ctx else "a student"

    slides.append({
        "type": "worked_example",
        "title": "Money Word Problem",
        "strategy": "money_word_problem",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": f"{actor} wants to buy {obj} for ₱{price}.\n{actor} pays ₱{paid}.",
             "visual_type": "PesoMoney",
             "visual_params": {"amount_paid": paid, "price": price, "mode": "change"}},
            {"text": f"Change = ₱{paid} − ₱{price} = $\\goldE{{₱{change}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g2_na_q2_subtraction(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Subtraction to 1000 with/without regrouping (_3–_7)."""
    slides = []

    # Strategy 1: subtraction on number line as inverse of addition
    a = rng.randint(15, 30)
    b = rng.randint(4, 12)
    slides.append({
        "type": "worked_example",
        "title": "Subtraction is the Opposite of Addition",
        "strategy": "inverse_operations",
        "steps": [
            {"text": f"$\\blueE{{{b}}}$ + ? = $\\goldE{{{a}}}$",
             "visual_type": "NumberLine",
             "visual_params": {"start": 0, "end": a + 3, "markers": [b, a]}},
            {"text": f"To find the missing number, count forward from {b} to {a}.",
             "visual_type": "NumberLine",
             "visual_params": {"start": 0, "end": a + 3, "hop_from": b, "hop_by": a - b}},
            {"text": f"$\\goldE{{{a}}}$ − $\\blueE{{{b}}}$ = $\\maroonD{{{a - b}}}$\nSubtraction undoes addition.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 2: subtract 3-digit numbers using place value
    a3 = rng.randint(400, 900)
    b3 = rng.randint(100, a3 - 100)
    result3 = a3 - b3
    slides.append({
        "type": "worked_example",
        "title": "Subtracting to 1 000",
        "strategy": "place_value_subtraction",
        "steps": [
            {"text": f"Subtract $\\blueE{{{a3}}}$ − $\\maroonD{{{b3}}}$.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": a3}},
            {"text": f"Take away {b3 // 100} hundreds, {(b3 % 100) // 10} tens, {b3 % 10} ones.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": a3, "subtract": b3, "mode": "subtract"}},
            {"text": f"$\\blueE{{{a3}}}$ − $\\maroonD{{{b3}}}$ = $\\goldE{{{result3}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g2_na_q2_patterns(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Increasing and Decreasing Patterns (_8, _9)."""
    slides = []

    # Increasing number pattern
    start = rng.randint(2, 10)
    step_inc = rng.randint(2, 5)
    inc_seq = [start + step_inc * i for i in range(6)]

    slides.append({
        "type": "worked_example",
        "title": "Increasing Pattern",
        "strategy": "number_pattern",
        "steps": [
            {"text": f"Look at this pattern: {', '.join(str(x) for x in inc_seq[:5])}...",
             "visual_type": "PatternRow",
             "visual_params": {"items": [str(x) for x in inc_seq[:5]], "type": "increasing"}},
            {"text": f"Each number is {step_inc} more than the one before. The pattern is increasing.",
             "visual_type": "PatternRow",
             "visual_params": {"items": [str(x) for x in inc_seq[:5]], "type": "increasing", "show_rule": True}},
            {"text": f"What comes next? $\\goldE{{{inc_seq[5]}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Decreasing number pattern
    start_dec = rng.randint(30, 60)
    step_dec = rng.randint(2, 5)
    dec_seq = [start_dec - step_dec * i for i in range(6)]

    slides.append({
        "type": "worked_example",
        "title": "Decreasing Pattern",
        "strategy": "number_pattern",
        "steps": [
            {"text": f"Look at this pattern: {', '.join(str(x) for x in dec_seq[:5])}...",
             "visual_type": "PatternRow",
             "visual_params": {"items": [str(x) for x in dec_seq[:5]], "type": "decreasing"}},
            {"text": f"Each number is {step_dec} less than the one before. The pattern is decreasing.",
             "visual_type": "PatternRow",
             "visual_params": {"items": [str(x) for x in dec_seq[:5]], "type": "decreasing", "show_rule": True}},
            {"text": f"What comes next? $\\goldE{{{dec_seq[5]}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G2 NA Q3 — Multiplication, Division, Even and Odd
# ---------------------------------------------------------------------------

def _gen_g2_na_q3_multiplication(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Multiplication as repeated addition, tables 2-5 and 10 (_0–_3)."""
    slides = []

    # Strategy 1: equal groups → repeated addition → multiplication
    groups = rng.randint(2, 5)
    per_group = rng.randint(2, 5)
    total = groups * per_group
    obj = rng.choice(interest_ctx["objects"]) if interest_ctx else "dots"

    slides.append({
        "type": "worked_example",
        "title": "Equal Groups",
        "strategy": "equal_groups",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": f"There are $\\blueE{{{groups}}}$ groups of $\\maroonD{{{per_group}}}$ {obj}.",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": groups, "cols": per_group, "object": obj}},
            {"text": f"Add equal groups: {' + '.join([str(per_group)] * groups)} = $\\goldE{{{total}}}$",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": groups, "cols": per_group, "object": obj, "show_addition": True}},
            {"text": f"$\\blueE{{{groups}}}$ × $\\maroonD{{{per_group}}}$ = $\\goldE{{{total}}}$\nMultiplication is a fast way to add equal groups.",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": groups, "cols": per_group, "object": obj, "show_equation": True}},
        ]
    })

    # Strategy 2: multiplication table fact
    a = rng.randint(2, 5)
    b = rng.randint(2, 10)
    slides.append({
        "type": "worked_example",
        "title": "Multiplication Table Fact",
        "strategy": "times_table",
        "steps": [
            {"text": f"$\\blueE{{{a}}}$ × $\\maroonD{{{b}}}$ = ?",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": a, "cols": b}},
            {"text": f"Count {a} rows of {b}: {' + '.join([str(b)] * a)} = $\\goldE{{{a * b}}}$",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": a, "cols": b, "show_count": True}},
            {"text": f"$\\blueE{{{a}}}$ × $\\maroonD{{{b}}}$ = $\\goldE{{{a * b}}}$",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": a, "cols": b, "show_equation": True}},
        ]
    })

    return slides


def _gen_g2_na_q3_division(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Division through equal sharing, quotient, tables 2-5 and 10 (_4–_7, _9)."""
    slides = []

    # Strategy 1: equal sharing
    divisor = rng.randint(2, 5)
    quotient = rng.randint(2, 6)
    dividend = divisor * quotient
    obj = rng.choice(interest_ctx["objects"]) if interest_ctx else "items"
    actor = rng.choice(interest_ctx["actors"]) if interest_ctx else "students"

    slides.append({
        "type": "worked_example",
        "title": "Sharing Equally",
        "strategy": "equal_sharing",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": f"Share $\\blueE{{{dividend}}}$ {obj} equally among $\\maroonD{{{divisor}}}$ {actor}.",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": obj, "count": dividend, "groups": divisor}},
            {"text": f"Each person gets $\\goldE{{{quotient}}}$ {obj}.",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": obj, "count": dividend, "groups": divisor, "show_groups": True}},
            {"text": f"$\\blueE{{{dividend}}}$ ÷ $\\maroonD{{{divisor}}}$ = $\\goldE{{{quotient}}}$",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": obj, "count": dividend, "groups": divisor, "show_groups": True, "show_equation": True}},
        ]
    })

    # Strategy 2: division fact
    a = rng.randint(2, 5)
    b = rng.randint(2, 6)
    product = a * b
    slides.append({
        "type": "worked_example",
        "title": "Division Fact",
        "strategy": "division_fact",
        "steps": [
            {"text": f"$\\blueE{{{product}}}$ ÷ $\\maroonD{{{a}}}$ = ?",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": a, "cols": b, "mode": "divide", "known": "rows"}},
            {"text": f"Put {product} into groups of {a}. How many groups? $\\goldE{{{b}}}$.",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": a, "cols": b, "mode": "divide", "show_groups": True}},
            {"text": f"$\\blueE{{{product}}}$ ÷ $\\maroonD{{{a}}}$ = $\\goldE{{{b}}}$",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": a, "cols": b, "mode": "divide", "show_equation": True}},
        ]
    })

    return slides


def _gen_g2_na_q3_even_odd(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Even and Odd numbers (_8)."""
    slides = []

    n_even = rng.choice([4, 6, 8, 10, 12])
    n_odd = rng.choice([3, 5, 7, 9, 11])

    slides.append({
        "type": "worked_example",
        "title": "Even Numbers",
        "strategy": "even_odd",
        "steps": [
            {"text": f"Can we split $\\blueE{{{n_even}}}$ into 2 equal groups?",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": "dots", "count": n_even, "groups": 2}},
            {"text": f"Yes! $\\blueE{{{n_even}}}$ ÷ 2 = $\\goldE{{{n_even // 2}}}$. No leftovers.",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": "dots", "count": n_even, "groups": 2, "show_groups": True}},
            {"text": f"$\\blueE{{{n_even}}}$ is even. Even numbers can be split into 2 equal groups.",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": "dots", "count": n_even, "groups": 2, "show_groups": True}},
        ]
    })

    slides.append({
        "type": "worked_example",
        "title": "Odd Numbers",
        "strategy": "even_odd",
        "steps": [
            {"text": f"Can we split $\\blueE{{{n_odd}}}$ into 2 equal groups?",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": "dots", "count": n_odd, "groups": 2}},
            {"text": f"No — there is 1 left over. $\\blueE{{{n_odd}}}$ ÷ 2 has a remainder of 1.",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": "dots", "count": n_odd, "groups": 2, "remainder": 1}},
            {"text": f"$\\blueE{{{n_odd}}}$ is odd. Odd numbers always have 1 left over when split in 2.",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": "dots", "count": n_odd, "groups": 2, "remainder": 1, "highlight_remainder": True}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G2 NA Q4 — Fractions
# ---------------------------------------------------------------------------

def _gen_g2_na_q4_unit_fractions(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Unit fractions with denominators 2, 3, 4, 5, 6, 8 (_0–_2)."""
    slides = []

    denom = rng.choice([3, 4, 5, 6, 8])

    # Strategy 1: show a unit fraction
    slides.append({
        "type": "worked_example",
        "title": f"The Fraction 1/{denom}",
        "strategy": "unit_fraction",
        "steps": [
            {"text": f"Divide a whole into $\\blueE{{{denom}}}$ equal parts.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": denom, "shaded": 0}},
            {"text": f"Shade 1 part. That is $\\goldE{{\\frac{{1}}{{{denom}}}}}$.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": denom, "shaded": 1, "label": f"1/{denom}"}},
            {"text": f"The $\\blueE{{{denom}}}$ is the denominator — how many equal parts.\nThe 1 is the numerator — how many parts we have.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": denom, "shaded": 1, "label": f"1/{denom}", "label_parts": True}},
        ]
    })

    # Strategy 2: compare two unit fractions
    d1 = rng.choice([2, 3, 4])
    d2 = d1 + rng.randint(1, 4)
    bigger = d1  # smaller denominator = bigger fraction

    slides.append({
        "type": "worked_example",
        "title": "Comparing Unit Fractions",
        "strategy": "fraction_comparison",
        "steps": [
            {"text": f"Which is bigger — $\\frac{{1}}{{{d1}}}$ or $\\frac{{1}}{{{d2}}}$?",
             "visual_type": "Comparison",
             "visual_params": {
                 "left": {"visual": "FractionBar", "parts": d1, "shaded": 1, "label": f"1/{d1}"},
                 "right": {"visual": "FractionBar", "parts": d2, "shaded": 1, "label": f"1/{d2}"}
             }},
            {"text": f"More equal parts means each part is smaller.\n$\\frac{{1}}{{{d1}}}$ > $\\frac{{1}}{{{d2}}}$",
             "visual_type": "Comparison",
             "visual_params": {
                 "left": {"visual": "FractionBar", "parts": d1, "shaded": 1, "label": f"1/{d1}"},
                 "right": {"visual": "FractionBar", "parts": d2, "shaded": 1, "label": f"1/{d2}"}
             }},
        ]
    })

    return slides


def _gen_g2_na_q4_similar_fractions(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Similar fractions (same denominator) (_3–_5)."""
    slides = []

    denom = rng.choice([3, 4, 5, 6, 8])
    n1 = rng.randint(1, denom - 2)
    n2 = n1 + rng.randint(1, denom - n1 - 1)

    slides.append({
        "type": "worked_example",
        "title": "Similar Fractions",
        "strategy": "similar_fractions",
        "steps": [
            {"text": f"$\\frac{{{n1}}}{{{denom}}}$ and $\\frac{{{n2}}}{{{denom}}}$ have the same denominator.\nThey are similar fractions.",
             "visual_type": "Comparison",
             "visual_params": {
                 "left": {"visual": "FractionBar", "parts": denom, "shaded": n1, "label": f"{n1}/{denom}"},
                 "right": {"visual": "FractionBar", "parts": denom, "shaded": n2, "label": f"{n2}/{denom}"}
             }},
            {"text": f"Compare the numerators: $\\blueE{{{n1}}}$ parts vs $\\maroonD{{{n2}}}$ parts.\nMore shaded = bigger fraction.",
             "visual_type": "Comparison",
             "visual_params": {
                 "left": {"visual": "FractionBar", "parts": denom, "shaded": n1, "label": f"{n1}/{denom}"},
                 "right": {"visual": "FractionBar", "parts": denom, "shaded": n2, "label": f"{n2}/{denom}"}
             }},
            {"text": f"$\\frac{{{n2}}}{{{denom}}}$ > $\\frac{{{n1}}}{{{denom}}}$ because $\\maroonD{{{n2}}}$ > $\\blueE{{{n1}}}$.",
             "visual_type": "Comparison",
             "visual_params": {
                 "left": {"visual": "FractionBar", "parts": denom, "shaded": n1, "label": f"{n1}/{denom}"},
                 "right": {"visual": "FractionBar", "parts": denom, "shaded": n2, "label": f"{n2}/{denom}"}
             }},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G2 MG Q1 — Circles, Composite Shapes, Slides
# ---------------------------------------------------------------------------

def _gen_g2_mg_q1_circles(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Circles, half circles, quarter circles, composite shapes (_0, _1)."""
    slides = []

    slides.append({
        "type": "worked_example",
        "title": "Circles",
        "strategy": "shape_identification",
        "steps": [
            {"text": "A circle is perfectly round. It has no sides or corners.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["circle"], "show_labels": True}},
            {"text": "Cut a circle in half — you get 2 half circles.\nCut a circle into 4 equal parts — you get 4 quarter circles.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["half_circle", "quarter_circle"], "show_labels": True}},
            {"text": "2 half circles make a whole circle.\n4 quarter circles make a whole circle.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["half_circle", "half_circle"], "compose": "circle"}},
        ]
    })

    slides.append({
        "type": "worked_example",
        "title": "Composite Shapes",
        "strategy": "compose_shapes",
        "steps": [
            {"text": "We can combine shapes to make new shapes.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["square", "triangle"], "compose": "house"}},
            {"text": "A square and a triangle on top make a house shape.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["square", "triangle"], "compose": "house", "label": True}},
            {"text": "Two rectangles can form an L-shape.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["rectangle", "rectangle"], "compose": "L-shape"}},
        ]
    })

    return slides


def _gen_g2_mg_q1_slides(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Slide (translation) in one direction (_2)."""
    slides = []

    slides.append({
        "type": "worked_example",
        "title": "Sliding a Shape",
        "strategy": "translation",
        "steps": [
            {"text": "A slide moves a shape to a new place without turning or flipping it.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["rectangle"], "mode": "slide_before"}},
            {"text": "The shape slides to the right. It looks exactly the same — just in a new position.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["rectangle"], "mode": "slide_after", "direction": "right", "steps": 3}},
            {"text": "A slide changes the position. It does not change the shape or size.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["rectangle"], "mode": "slide_after", "direction": "right", "steps": 3}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G2 MG Q2 — Standard Measurement (cm, m)
# ---------------------------------------------------------------------------

def _gen_g2_mg_q2_measurement(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Measure in cm and m, ruler, estimate (_0–_3)."""
    slides = []

    # Strategy 1: measure in centimeters
    length_cm = rng.randint(5, 15)
    obj_names = ["pencil", "eraser", "book", "crayon"]
    obj_name = rng.choice(obj_names)

    slides.append({
        "type": "worked_example",
        "title": "Measuring in Centimeters",
        "strategy": "ruler_measure",
        "steps": [
            {"text": f"Use a ruler to measure the {obj_name}.",
             "visual_type": "RulerDisplay",
             "visual_params": {"object": obj_name, "length_cm": length_cm, "unit": "cm"}},
            {"text": f"Line up the ruler at 0. Read where the {obj_name} ends.",
             "visual_type": "RulerDisplay",
             "visual_params": {"object": obj_name, "length_cm": length_cm, "unit": "cm", "highlight_end": True}},
            {"text": f"The {obj_name} is $\\goldE{{{length_cm}}}$ cm long.",
             "visual_type": "RulerDisplay",
             "visual_params": {"object": obj_name, "length_cm": length_cm, "unit": "cm", "highlight_end": True}},
        ]
    })

    # Strategy 2: meters for larger distances
    distance_m = rng.randint(2, 8)
    slides.append({
        "type": "worked_example",
        "title": "When to Use Meters",
        "strategy": "unit_selection",
        "steps": [
            {"text": "We use centimeters for small things.\nWe use meters for bigger distances.",
             "visual_type": "RulerDisplay",
             "visual_params": {"mode": "comparison", "items": [
                 {"label": "pencil", "length": 15, "unit": "cm"},
                 {"label": "classroom", "length": 8, "unit": "m"}
             ]}},
            {"text": "100 cm = 1 m.\nA classroom door is about 2 m tall.",
             "visual_type": "RulerDisplay",
             "visual_params": {"mode": "conversion", "cm": 100, "m": 1}},
        ]
    })

    # Strategy 3: estimate
    true_len = rng.randint(4, 12)
    estimate = true_len + rng.choice([-2, -1, 1, 2])
    slides.append({
        "type": "worked_example",
        "title": "Estimating Length",
        "strategy": "estimate_length",
        "steps": [
            {"text": "Before measuring, we can make a careful guess — an estimate.",
             "visual_type": "RulerDisplay",
             "visual_params": {"object": "pencil", "length_cm": true_len, "show_ruler": False}},
            {"text": f"Estimate: about {estimate} cm.\nNow measure — the real length is $\\goldE{{{true_len}}}$ cm.",
             "visual_type": "RulerDisplay",
             "visual_params": {"object": "pencil", "length_cm": true_len, "highlight_end": True}},
            {"text": f"A good estimate is close to the real answer. {abs(estimate - true_len)} cm off is close.",
             "visual_type": "RulerDisplay",
             "visual_params": {"object": "pencil", "length_cm": true_len, "highlight_end": True}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G2 MG Q4 — Time (minutes), Solid Figures, Perimeter
# ---------------------------------------------------------------------------

def _gen_g2_mg_q4_time(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Time in hours and minutes, a.m./p.m., elapsed time (_0–_2)."""
    slides = []

    hour = rng.randint(1, 11)
    minute = rng.choice([5, 10, 15, 20, 25, 30, 35, 40, 45])
    period = rng.choice(["a.m.", "p.m."])

    slides.append({
        "type": "worked_example",
        "title": "Reading Minutes",
        "strategy": "clock_reading",
        "steps": [
            {"text": f"What time does this clock show?",
             "visual_type": "ClockSet",
             "visual_params": {"hour": hour, "minute": minute}},
            {"text": f"The short hand shows the hour: {hour}.\nThe long hand shows {minute} minutes.",
             "visual_type": "ClockSet",
             "visual_params": {"hour": hour, "minute": minute, "highlight": "both"}},
            {"text": f"The time is $\\goldE{{{hour}:{minute:02d}}}$ {period}.",
             "visual_type": "ClockSet",
             "visual_params": {"hour": hour, "minute": minute, "highlight": "answer"}},
        ]
    })

    # Elapsed time
    start_h = rng.randint(8, 10)
    start_m = rng.choice([0, 15, 30])
    duration_m = rng.choice([30, 45, 60, 90])
    total_m = start_h * 60 + start_m + duration_m
    end_h = total_m // 60
    end_m = total_m % 60
    dur_h = duration_m // 60
    dur_m = duration_m % 60

    slides.append({
        "type": "worked_example",
        "title": "How Long Did It Take?",
        "strategy": "elapsed_time",
        "steps": [
            {"text": f"Start: {start_h}:{start_m:02d} a.m.\nEnd: {end_h}:{end_m:02d} a.m.",
             "visual_type": "ClockSet",
             "visual_params": {"hour": start_h, "minute": start_m, "second_hour": end_h, "second_minute": end_m}},
            {"text": f"Count from {start_h}:{start_m:02d} to {end_h}:{end_m:02d}.",
             "visual_type": "ClockSet",
             "visual_params": {"hour": start_h, "minute": start_m, "second_hour": end_h, "second_minute": end_m, "show_elapsed": True}},
            {"text": f"The elapsed time is $\\goldE{{{duration_m}}}$ minutes" +
                     (f" ({dur_h} hour {dur_m} min)" if dur_h > 0 and dur_m > 0 else
                      f" ({dur_h} hour)" if dur_h > 0 else "") + ".",
             "visual_type": "ClockSet",
             "visual_params": {"hour": start_h, "minute": start_m, "second_hour": end_h, "second_minute": end_m, "show_elapsed": True}},
        ]
    })

    return slides


def _gen_g2_mg_q4_solid_figures(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Solid (3D) figures — straight and curved (_3)."""
    slides = []

    slides.append({
        "type": "worked_example",
        "title": "Flat and Curved Surfaces",
        "strategy": "shape_properties",
        "steps": [
            {"text": "Some shapes have only flat sides. A box has 6 flat sides.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["cube"], "show_labels": True}},
            {"text": "Some shapes have curved surfaces. A can has 2 flat circles and 1 curved side.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["cylinder"], "show_labels": True}},
            {"text": "A ball has only 1 curved surface — no flat sides at all.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["sphere"], "show_labels": True}},
        ]
    })

    return slides


def _gen_g2_mg_q4_perimeter(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Perimeter of triangles, squares, rectangles (_4–_6)."""
    slides = []

    # Strategy 1: perimeter of a rectangle
    length = rng.randint(3, 8)
    width = rng.randint(2, length - 1)
    perimeter = 2 * (length + width)

    slides.append({
        "type": "worked_example",
        "title": "Perimeter of a Rectangle",
        "strategy": "perimeter",
        "steps": [
            {"text": f"Find the perimeter of this rectangle.\nLength = {length} cm, Width = {width} cm.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["rectangle"],
                               "dimensions": {"length": length, "width": width},
                               "show_labels": True}},
            {"text": f"Add all the sides:\n{length} + {width} + {length} + {width} = $\\goldE{{{perimeter}}}$ cm",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["rectangle"],
                               "dimensions": {"length": length, "width": width},
                               "highlight": "sides"}},
            {"text": f"Perimeter = $\\goldE{{{perimeter}}}$ cm",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["rectangle"],
                               "dimensions": {"length": length, "width": width},
                               "show_perimeter": True}},
        ]
    })

    # Strategy 2: perimeter of a square
    side = rng.randint(3, 7)
    p_sq = 4 * side
    slides.append({
        "type": "worked_example",
        "title": "Perimeter of a Square",
        "strategy": "perimeter",
        "steps": [
            {"text": f"A square has 4 equal sides. Each side = {side} cm.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["square"],
                               "dimensions": {"side": side},
                               "show_labels": True}},
            {"text": f"Perimeter = {side} + {side} + {side} + {side} = 4 × {side} = $\\goldE{{{p_sq}}}$ cm",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["square"],
                               "dimensions": {"side": side},
                               "show_perimeter": True}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G2 DP Q3 — Pictograph with Scale
# ---------------------------------------------------------------------------

def _gen_g2_dp_q3_pictograph(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Pictograph with scale of 2 (_0, _1)."""
    slides = []

    if interest_ctx:
        categories = rng.sample(interest_ctx["objects"], min(4, len(interest_ctx["objects"])))
    else:
        categories = ["cats", "dogs", "birds", "fish"]
    scale = 2
    counts = [rng.randint(1, 5) * scale for _ in categories]
    data = [{"label": cat, "count": cnt} for cat, cnt in zip(categories, counts)]
    most = max(data, key=lambda x: x["count"])

    slides.append({
        "type": "worked_example",
        "title": "Pictograph with Scale",
        "strategy": "pictograph_scale",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": f"In this pictograph, each picture stands for $\\blueE{{{scale}}}$ students.",
             "visual_type": "PictographDisplay",
             "visual_params": {"data": data, "scale": scale, "mode": "pictograph"}},
            {"text": f"{most['label'].capitalize()} has {most['count'] // scale} pictures.\n{most['count'] // scale} × {scale} = $\\goldE{{{most['count']}}}$ students.",
             "visual_type": "PictographDisplay",
             "visual_params": {"data": data, "scale": scale, "mode": "pictograph", "highlight": most["label"]}},
            {"text": "Always check the scale before reading a pictograph.",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register():
    """Register all G2 node groups into MINI_LESSON_GROUPS and _INTRODUCTIONS."""
    from backend.app.intro_gen.generator import MINI_LESSON_GROUPS
    from backend.app.intro_gen import _INTRODUCTIONS

    # G2 NA Q1
    MINI_LESSON_GROUPS["g2_na_q1"] = {
        "node_label": "Grade 2 - Numbers to 1 000 & Addition",
        "grade": 2,
        "groups": [
            {
                "title": "Numbers to 1 000",
                "node_key": "g2_na_q1",
                "competencies": ["mat_g2_na_q1_0", "mat_g2_na_q1_1", "mat_g2_na_q1_2",
                                  "mat_g2_na_q1_3", "mat_g2_na_q1_4", "mat_g2_na_q1_5"],
                "vocab_terms": ["thousand"],
                "generator": _gen_g2_na_q1_numbers,
            },
            {
                "title": "Place Value: Hundreds",
                "node_key": "g2_na_q1",
                "competencies": ["mat_g2_na_q1_6"],
                "vocab_terms": ["hundreds"],
                "generator": _gen_g2_na_q1_hundreds,
            },
            {
                "title": "Addition to 1 000",
                "node_key": "g2_na_q1",
                "competencies": ["mat_g2_na_q1_7", "mat_g2_na_q1_8",
                                  "mat_g2_na_q1_9", "mat_g2_na_q1_10"],
                "vocab_terms": ["regrouping"],
                "generator": _gen_g2_na_q1_addition,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g2_na_q1::Numbers to 1 000": (
            "You can count to 100.\n"
            "Now let's go further — all the way to 1 000.\n"
            "We can skip count by 100s to get there fast."
        ),
        "g2_na_q1::Place Value: Hundreds": (
            "Tens and ones show place value.\n"
            "Bigger numbers have one more place — the hundreds place.\n"
            "Let's look at what each digit in a 3-digit number is worth."
        ),
        "g2_na_q1::Addition to 1 000": (
            "You can add numbers to 100.\n"
            "Now let's add bigger numbers — up to 1 000.\n"
            "Sometimes ones or tens need to be regrouped."
        ),
    })

    # G2 NA Q2
    MINI_LESSON_GROUPS["g2_na_q2"] = {
        "node_label": "Grade 2 - Money, Subtraction & Patterns",
        "grade": 2,
        "groups": [
            {
                "title": "Money to 1 000",
                "node_key": "g2_na_q2",
                "competencies": ["mat_g2_na_q2_0", "mat_g2_na_q2_1", "mat_g2_na_q2_2"],
                "vocab_terms": ["centavo"],
                "generator": _gen_g2_na_q2_money,
            },
            {
                "title": "Subtraction to 1 000",
                "node_key": "g2_na_q2",
                "competencies": ["mat_g2_na_q2_3", "mat_g2_na_q2_4",
                                  "mat_g2_na_q2_5", "mat_g2_na_q2_6", "mat_g2_na_q2_7"],
                "vocab_terms": [],
                "generator": _gen_g2_na_q2_subtraction,
            },
            {
                "title": "Increasing & Decreasing Patterns",
                "node_key": "g2_na_q2",
                "competencies": ["mat_g2_na_q2_8", "mat_g2_na_q2_9"],
                "vocab_terms": ["increasing pattern", "decreasing pattern"],
                "generator": _gen_g2_na_q2_patterns,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g2_na_q2::Money to 1 000": (
            "Pesos come in coins and bills.\n"
            "Now let's learn about centavos — the smaller coins.\n"
            "100 centavos make 1 peso."
        ),
        "g2_na_q2::Subtraction to 1 000": (
            "You can subtract up to 100.\n"
            "Now let's subtract bigger numbers.\n"
            "Addition and subtraction are opposites — they undo each other."
        ),
        "g2_na_q2::Increasing & Decreasing Patterns": (
            "Patterns repeat by a rule.\n"
            "Some patterns go up. Some patterns go down.\n"
            "Let's find the rule."
        ),
    })

    # G2 NA Q3
    MINI_LESSON_GROUPS["g2_na_q3"] = {
        "node_label": "Grade 2 - Multiplication, Division & Even/Odd",
        "grade": 2,
        "groups": [
            {
                "title": "Multiplication",
                "node_key": "g2_na_q3",
                "competencies": ["mat_g2_na_q3_0", "mat_g2_na_q3_1",
                                  "mat_g2_na_q3_2", "mat_g2_na_q3_3"],
                "vocab_terms": ["equal groups", "multiplication", "product"],
                "generator": _gen_g2_na_q3_multiplication,
            },
            {
                "title": "Division",
                "node_key": "g2_na_q3",
                "competencies": ["mat_g2_na_q3_4", "mat_g2_na_q3_5",
                                  "mat_g2_na_q3_6", "mat_g2_na_q3_7", "mat_g2_na_q3_9"],
                "vocab_terms": ["division", "quotient"],
                "generator": _gen_g2_na_q3_division,
            },
            {
                "title": "Even and Odd",
                "node_key": "g2_na_q3",
                "competencies": ["mat_g2_na_q3_8"],
                "vocab_terms": ["even", "odd"],
                "generator": _gen_g2_na_q3_even_odd,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g2_na_q3::Multiplication": (
            "You can add equal groups.\n"
            "What if there are many groups?\n"
            "Multiplication is a faster way to add equal groups."
        ),
        "g2_na_q3::Division": (
            "You can multiply to make equal groups.\n"
            "What if you need to split a total into equal groups?\n"
            "That is what division does."
        ),
        "g2_na_q3::Even and Odd": (
            "Can every number be split into 2 equal groups?\n"
            "Let's find out which numbers can and which cannot."
        ),
    })

    # G2 NA Q4
    MINI_LESSON_GROUPS["g2_na_q4"] = {
        "node_label": "Grade 2 - Fractions",
        "grade": 2,
        "groups": [
            {
                "title": "Unit Fractions",
                "node_key": "g2_na_q4",
                "competencies": ["mat_g2_na_q4_0", "mat_g2_na_q4_1", "mat_g2_na_q4_2"],
                "vocab_terms": ["denominator", "numerator"],
                "generator": _gen_g2_na_q4_unit_fractions,
            },
            {
                "title": "Similar Fractions",
                "node_key": "g2_na_q4",
                "competencies": ["mat_g2_na_q4_3", "mat_g2_na_q4_4", "mat_g2_na_q4_5"],
                "vocab_terms": ["similar fractions"],
                "generator": _gen_g2_na_q4_similar_fractions,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g2_na_q4::Unit Fractions": (
            "Half means 2 equal parts. Quarter means 4.\n"
            "Now let's look at fractions with other denominators — thirds, fifths, eighths.\n"
            "Every fraction has two numbers that tell us the story."
        ),
        "g2_na_q4::Similar Fractions": (
            "You can compare unit fractions.\n"
            "What if fractions have the same denominator?\n"
            "Similar fractions are easy to compare."
        ),
    })

    # G2 MG Q1
    MINI_LESSON_GROUPS["g2_mg_q1"] = {
        "node_label": "Grade 2 - Shapes & Slides",
        "grade": 2,
        "groups": [
            {
                "title": "Circles and Composite Shapes",
                "node_key": "g2_mg_q1",
                "competencies": ["mat_g2_mg_q1_0", "mat_g2_mg_q1_1"],
                "vocab_terms": ["circle"],
                "generator": _gen_g2_mg_q1_circles,
            },
            {
                "title": "Slides",
                "node_key": "g2_mg_q1",
                "competencies": ["mat_g2_mg_q1_2"],
                "vocab_terms": ["slide", "translation"],
                "generator": _gen_g2_mg_q1_slides,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g2_mg_q1::Circles and Composite Shapes": (
            "Triangles have 3 sides. Rectangles have 4.\n"
            "Now let's meet a new shape — the circle.\n"
            "We can also combine shapes to make new, bigger shapes."
        ),
        "g2_mg_q1::Slides": (
            "Shapes can move.\n"
            "A slide moves a shape to a new place without turning it.\n"
            "Let's see what stays the same and what changes."
        ),
    })

    # G2 MG Q2
    MINI_LESSON_GROUPS["g2_mg_q2"] = {
        "node_label": "Grade 2 - Standard Measurement",
        "grade": 2,
        "groups": [
            {
                "title": "Measuring in cm and m",
                "node_key": "g2_mg_q2",
                "competencies": ["mat_g2_mg_q2_0", "mat_g2_mg_q2_1",
                                  "mat_g2_mg_q2_2", "mat_g2_mg_q2_3"],
                "vocab_terms": ["centimeter", "meter", "cm", "m", "ruler", "estimate"],
                "generator": _gen_g2_mg_q2_measurement,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g2_mg_q2::Measuring in cm and m": (
            "You measured length with non-standard units like paperclips.\n"
            "Now let's use standard units that everyone agrees on.\n"
            "Centimeters and meters are used all over the world."
        ),
    })

    # G2 MG Q4
    MINI_LESSON_GROUPS["g2_mg_q4"] = {
        "node_label": "Grade 2 - Time, Solid Figures & Perimeter",
        "grade": 2,
        "groups": [
            {
                "title": "Time in Minutes",
                "node_key": "g2_mg_q4",
                "competencies": ["mat_g2_mg_q4_0", "mat_g2_mg_q4_1", "mat_g2_mg_q4_2"],
                "vocab_terms": ["minute", "a.m.", "p.m.", "elapsed time"],
                "generator": _gen_g2_mg_q4_time,
            },
            {
                "title": "Solid Figures",
                "node_key": "g2_mg_q4",
                "competencies": ["mat_g2_mg_q4_3"],
                "vocab_terms": ["solid figure"],
                "generator": _gen_g2_mg_q4_solid_figures,
            },
            {
                "title": "Perimeter",
                "node_key": "g2_mg_q4",
                "competencies": ["mat_g2_mg_q4_4", "mat_g2_mg_q4_5", "mat_g2_mg_q4_6"],
                "vocab_terms": ["perimeter"],
                "generator": _gen_g2_mg_q4_perimeter,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g2_mg_q4::Time in Minutes": (
            "You can read time to the hour and half hour.\n"
            "Now let's read the minutes too.\n"
            "We also need to know if it is morning or afternoon."
        ),
        "g2_mg_q4::Solid Figures": (
            "Squares and circles are flat (2D) shapes.\n"
            "Real objects take up space — they are solid.\n"
            "Let's look at the surfaces of solid shapes."
        ),
        "g2_mg_q4::Perimeter": (
            "You can measure one side of a shape.\n"
            "What if we measure all the way around?\n"
            "The total distance around a shape is its perimeter."
        ),
    })

    # G2 DP Q3
    MINI_LESSON_GROUPS["g2_dp_q3"] = {
        "node_label": "Grade 2 - Pictographs with Scale",
        "grade": 2,
        "groups": [
            {
                "title": "Pictographs with Scale",
                "node_key": "g2_dp_q3",
                "competencies": ["mat_g2_dp_q3_0", "mat_g2_dp_q3_1"],
                "vocab_terms": ["scale"],
                "generator": _gen_g2_dp_q3_pictograph,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g2_dp_q3::Pictographs with Scale": (
            "Pictographs use pictures to show data.\n"
            "What if each picture stands for more than 1?\n"
            "That is called a scale."
        ),
    })
