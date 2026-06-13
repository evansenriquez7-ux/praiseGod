"""
Grade 1 Intro Content Generators
Covers: G1 NA Q2-Q4, G1 MG Q1/Q2/Q4, G1 DP Q3

Each generator function produces worked example slides for one mini-lesson group.
Visual types used:
  Existing (implemented): NumberLine, PlaceValueBlocks, NumberBond, ObjectGroup,
                          NumberCards, TenFrame, OrderedLine, Comparison
  New (need frontend):    SkipCountLine, ShapeDisplay, FractionBar, PatternRow,
                          PictographDisplay, LengthCompare, TurnDisplay
"""

import random
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# G1 NA Q2 — Skip Counting, Place Value, Expanded Form, Adding to 100
# ---------------------------------------------------------------------------

def _gen_g1_na_q2_counting(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Counting to 100 & Skip Counting (_0, _1)."""
    slides = []

    # Strategy 1: count to 100 — show a number near 100 on number line
    n = rng.randint(90, 99)
    slides.append({
        "type": "worked_example",
        "title": "Counting to 100",
        "strategy": "number_line",
        "steps": [
            {"text": f"Numbers go all the way to 100.\nHere is $\\blueE{{{n}}}$ on the number line.",
             "visual_type": "NumberLine",
             "visual_params": {"start": max(0, n - 4), "end": 100, "markers": [n]}},
            {"text": f"1 more than $\\blueE{{{n}}}$ is $\\goldE{{{n + 1}}}$.",
             "visual_type": "NumberLine",
             "visual_params": {"start": max(0, n - 4), "end": 100, "hop_from": n, "hop_by": 1}},
            {"text": f"$\\goldE{{{n + 1}}}$ is the last number before we start again at 101.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 2: skip counting by 2s
    start2 = rng.choice([2, 4, 6, 8])
    seq2 = [start2 + 2 * i for i in range(5)]
    slides.append({
        "type": "worked_example",
        "title": "Skip Counting by 2s",
        "strategy": "skip_count",
        "steps": [
            {"text": f"Skip count by 2s: start at $\\blueE{{{seq2[0]}}}$.",
             "visual_type": "SkipCountLine",
             "visual_params": {"start": 0, "end": seq2[-1] + 4, "step": 2, "from": seq2[0]}},
            {"text": f"Count: $\\blueE{{{seq2[0]}}}$, $\\goldE{{{seq2[1]}}}$, $\\goldE{{{seq2[2]}}}$, $\\goldE{{{seq2[3]}}}$, $\\goldE{{{seq2[4]}}}$...",
             "visual_type": "SkipCountLine",
             "visual_params": {"start": 0, "end": seq2[-1] + 4, "step": 2, "from": seq2[0], "highlight": seq2}},
            {"text": f"Each jump is 2. The next number after {seq2[4]} is $\\goldE{{{seq2[4] + 2}}}$.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 3: skip counting by 5s
    seq5 = [5 * i for i in range(1, 7)]
    slides.append({
        "type": "worked_example",
        "title": "Skip Counting by 5s",
        "strategy": "skip_count",
        "steps": [
            {"text": "Skip count by 5s: 5, 10, 15, 20...",
             "visual_type": "SkipCountLine",
             "visual_params": {"start": 0, "end": 35, "step": 5, "from": 5, "highlight": seq5[:5]}},
            {"text": f"Each jump is 5.\nWhat comes after 25? $\\goldE{{30}}$.",
             "visual_type": "SkipCountLine",
             "visual_params": {"start": 0, "end": 35, "step": 5, "from": 5, "highlight": seq5}},
            {"text": "Count by 5s: 5, 10, 15, 20, 25, 30...",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 4: skip counting by 10s
    slides.append({
        "type": "worked_example",
        "title": "Skip Counting by 10s",
        "strategy": "skip_count",
        "steps": [
            {"text": "Skip count by 10s: 10, 20, 30...",
             "visual_type": "SkipCountLine",
             "visual_params": {"start": 0, "end": 105, "step": 10, "from": 10, "highlight": [10, 20, 30, 40, 50]}},
            {"text": "Each jump is 10. Count to 100:\n10, 20, 30, 40, 50, 60, 70, 80, 90, 100.",
             "visual_type": "SkipCountLine",
             "visual_params": {"start": 0, "end": 105, "step": 10, "from": 10,
                                "highlight": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]}},
            {"text": "There are 10 jumps of 10 in 100.",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g1_na_q2_place_value(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Place Value: Tens and Ones, Decompose, Expanded Form (_2, _3, _4)."""
    slides = []

    # Strategy 1: identify tens and ones in a 2-digit number
    num = rng.randint(13, 89)
    while len(set(str(num))) < 2:  # avoid same-digit numbers like 33
        num = rng.randint(13, 89)
    tens = num // 10
    ones = num % 10

    slides.append({
        "type": "worked_example",
        "title": "Tens and Ones",
        "strategy": "place_value",
        "steps": [
            {"text": f"The numeral $\\blueE{{{num}}}$ has two digits.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": num}},
            {"text": f"The $\\blueE{{{tens}}}$ is in the tens place. It stands for $\\blueE{{{tens * 10}}}$.\nThe $\\maroonD{{{ones}}}$ is in the ones place. It stands for $\\maroonD{{{ones}}}$.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": num, "highlight_tens": True, "highlight_ones": True}},
            {"text": f"$\\blueE{{{tens}}}$ tens and $\\maroonD{{{ones}}}$ ones = $\\goldE{{{num}}}$.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 2: expanded form
    num2 = rng.randint(21, 79)
    while len(set(str(num2))) < 2:
        num2 = rng.randint(21, 79)
    t2 = num2 // 10
    o2 = num2 % 10

    slides.append({
        "type": "worked_example",
        "title": "Expanded Form",
        "strategy": "expanded_form",
        "steps": [
            {"text": f"Write $\\blueE{{{num2}}}$ in expanded form.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": num2}},
            {"text": f"$\\blueE{{{num2}}}$ = $\\blueE{{{t2 * 10}}}$ + $\\maroonD{{{o2}}}$",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": num2, "show_expanded": True}},
            {"text": f"$\\goldE{{{num2}}}$ = $\\blueE{{{t2}}}$ tens + $\\maroonD{{{o2}}}$ ones = $\\blueE{{{t2 * 10}}}$ + $\\maroonD{{{o2}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g1_na_q2_addition(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Adding to 100 Without Regrouping (_5, _6)."""
    slides = []

    # Strategy: add two 2-digit numbers without regrouping, using place value
    a_tens = rng.randint(1, 5)
    b_tens = rng.randint(1, 9 - a_tens)
    a_ones = rng.randint(0, 4)
    b_ones = rng.randint(0, 9 - a_ones)
    a = a_tens * 10 + a_ones
    b = b_tens * 10 + b_ones
    result = a + b

    slides.append({
        "type": "worked_example",
        "title": "Adding Tens and Ones",
        "strategy": "place_value_addition",
        "steps": [
            {"text": f"Add $\\blueE{{{a}}}$ + $\\maroonD{{{b}}}$.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number_a": a, "number_b": b, "mode": "add"}},
            {"text": f"Add the tens: $\\blueE{{{a_tens}}}$ tens + $\\maroonD{{{b_tens}}}$ tens = $\\goldE{{{a_tens + b_tens}}}$ tens.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number_a": a, "number_b": b, "mode": "add", "highlight": "tens"}},
            {"text": f"Add the ones: $\\blueE{{{a_ones}}}$ ones + $\\maroonD{{{b_ones}}}$ ones = $\\goldE{{{a_ones + b_ones}}}$ ones.\n\n$\\blueE{{{a}}}$ + $\\maroonD{{{b}}}$ = $\\goldE{{{result}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Word problem (interest-wrapped)
    if interest_ctx:
        actor = rng.choice(interest_ctx["actors"])
        obj = rng.choice(interest_ctx["objects"])
        slides.append({
            "type": "worked_example",
            "title": "Adding to 100 — Word Problem",
            "strategy": "word_problem",
            "interest_wrapped": True,
            "steps": [
                {"text": f"{actor} has $\\blueE{{{a}}}$ {obj}.\n{actor} gets $\\maroonD{{{b}}}$ more {obj}.",
                 "visual_type": "ObjectGroup",
                 "visual_params": {"object": obj, "count": a, "adding": b}},
                {"text": f"$\\blueE{{{a}}}$ + $\\maroonD{{{b}}}$ = $\\goldE{{{result}}}$\n\n{actor} has $\\goldE{{{result}}}$ {obj} in total.",
                 "visual_type": None, "visual_params": None},
            ]
        })

    return slides


# ---------------------------------------------------------------------------
# G1 NA Q3 — Subtraction, Missing Number, Patterns
# ---------------------------------------------------------------------------

def _gen_g1_na_q3_subtraction(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Subtraction, Missing Number (_0, _1, _2, _3)."""
    slides = []

    # Strategy 1: subtraction on number line
    a = rng.randint(8, 20)
    b = rng.randint(2, min(a - 1, 9))
    result = a - b

    slides.append({
        "type": "worked_example",
        "title": "Subtraction on a Number Line",
        "strategy": "number_line",
        "steps": [
            {"text": f"$\\blueE{{{a}}}$ − $\\maroonD{{{b}}}$ = ?",
             "visual_type": "NumberLine",
             "visual_params": {"start": max(0, result - 2), "end": a + 2, "markers": [a]}},
            {"text": f"Start at $\\blueE{{{a}}}$. Jump back $\\maroonD{{{b}}}$.",
             "visual_type": "NumberLine",
             "visual_params": {"start": max(0, result - 2), "end": a + 2, "hop_from": a, "hop_by": -b}},
            {"text": f"We land on $\\goldE{{{result}}}$.\n\n$\\blueE{{{a}}}$ − $\\maroonD{{{b}}}$ = $\\goldE{{{result}}}$",
             "visual_type": "NumberLine",
             "visual_params": {"start": max(0, result - 2), "end": a + 2, "highlight": result}},
        ]
    })

    # Strategy 2: subtraction with objects (take away) — interest-wrapped
    c = rng.randint(5, 15)
    d = rng.randint(2, min(c - 1, 8))
    result2 = c - d
    obj = rng.choice(interest_ctx["objects"]) if interest_ctx else "stars"
    actor = rng.choice(interest_ctx["actors"]) if interest_ctx else ""

    if interest_ctx:
        step1 = f"{actor} has $\\blueE{{{c}}}$ {obj}."
        step2 = f"{actor} gives away $\\maroonD{{{d}}}$ {obj}."
        step3 = f"{actor} has $\\goldE{{{result2}}}$ {obj} left."
    else:
        step1 = f"There are $\\blueE{{{c}}}$ {obj}."
        step2 = f"Take away $\\maroonD{{{d}}}$ {obj}."
        step3 = f"$\\goldE{{{result2}}}$ {obj} are left."

    slides.append({
        "type": "worked_example",
        "title": "Taking Away",
        "strategy": "take_away",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": step1,
             "visual_type": "ObjectGroup",
             "visual_params": {"object": obj, "count": c}},
            {"text": step2,
             "visual_type": "ObjectGroup",
             "visual_params": {"object": obj, "count": c, "remove": d}},
            {"text": step3 + f"\n\n$\\blueE{{{c}}}$ − $\\maroonD{{{d}}}$ = $\\goldE{{{result2}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 3: missing number — part-whole relationship
    whole = rng.randint(8, 18)
    part1 = rng.randint(3, whole - 3)
    part2 = whole - part1

    slides.append({
        "type": "worked_example",
        "title": "Finding the Missing Number",
        "strategy": "missing_number",
        "steps": [
            {"text": f"$\\blueE{{{part1}}}$ + ? = $\\goldE{{{whole}}}$\nWhat is the missing number?",
             "visual_type": "NumberBond",
             "visual_params": {"whole": whole, "parts": [part1, None]}},
            {"text": f"The whole is $\\goldE{{{whole}}}$. One part is $\\blueE{{{part1}}}$.\nThe other part = $\\goldE{{{whole}}}$ − $\\blueE{{{part1}}}$ = $\\maroonD{{{part2}}}$.",
             "visual_type": "NumberBond",
             "visual_params": {"whole": whole, "parts": [part1, part2]}},
            {"text": f"$\\blueE{{{part1}}}$ + $\\maroonD{{{part2}}}$ = $\\goldE{{{whole}}}$\nThe missing number is $\\maroonD{{{part2}}}$.",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g1_na_q3_subtraction_100(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Subtracting to 100 (_4, _5)."""
    slides = []

    # Strategy: subtract 2-digit numbers using place value (no regrouping)
    a_tens = rng.randint(3, 9)
    b_tens = rng.randint(1, a_tens - 1)
    a_ones = rng.randint(1, 9)
    b_ones = rng.randint(0, a_ones)
    a = a_tens * 10 + a_ones
    b = b_tens * 10 + b_ones
    result = a - b

    slides.append({
        "type": "worked_example",
        "title": "Subtracting Tens and Ones",
        "strategy": "place_value_subtraction",
        "steps": [
            {"text": f"Subtract $\\blueE{{{a}}}$ − $\\maroonD{{{b}}}$.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": a}},
            {"text": f"Take away $\\maroonD{{{b_tens}}}$ tens and $\\maroonD{{{b_ones}}}$ ones.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": a, "subtract": b, "mode": "subtract"}},
            {"text": f"$\\goldE{{{a_tens - b_tens}}}$ tens and $\\goldE{{{a_ones - b_ones}}}$ ones remain.\n\n$\\blueE{{{a}}}$ − $\\maroonD{{{b}}}$ = $\\goldE{{{result}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g1_na_q3_patterns(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Repeating Patterns (_6, _7)."""
    slides = []

    # Strategy 1: identify and continue a shape/color pattern
    units = rng.choice([
        ["A", "B"],
        ["A", "B", "C"],
        ["A", "A", "B"],
    ])
    pattern = units * 3
    shown = pattern[:6]
    hidden = pattern[6:8]

    slides.append({
        "type": "worked_example",
        "title": "What Comes Next?",
        "strategy": "pattern_continue",
        "steps": [
            {"text": "Look at this pattern:",
             "visual_type": "PatternRow",
             "visual_params": {"items": shown, "hide_last": 0}},
            {"text": f"The pattern unit is: {', '.join(units)}. It repeats.",
             "visual_type": "PatternRow",
             "visual_params": {"items": shown, "highlight_unit": len(units)}},
            {"text": f"What comes next? {' → '.join(hidden)}",
             "visual_type": "PatternRow",
             "visual_params": {"items": pattern[:8], "hide_last": 0}},
        ]
    })

    # Strategy 2: number repeating pattern
    step = rng.randint(1, 3)
    base = rng.randint(1, 5)
    # e.g. 1, 2, 1, 2 or 1, 2, 3, 1, 2, 3
    num_unit = list(range(base, base + len(units)))
    num_pattern = num_unit * 4

    slides.append({
        "type": "worked_example",
        "title": "Number Patterns",
        "strategy": "number_pattern",
        "steps": [
            {"text": f"Here is a number pattern: {', '.join(str(x) for x in num_pattern[:6])}...",
             "visual_type": "PatternRow",
             "visual_params": {"items": [str(x) for x in num_pattern[:6]], "hide_last": 0}},
            {"text": f"The pattern unit is: {', '.join(str(x) for x in num_unit)}.",
             "visual_type": "PatternRow",
             "visual_params": {"items": [str(x) for x in num_pattern[:6]], "highlight_unit": len(num_unit)}},
            {"text": f"The next two numbers are $\\goldE{{{num_pattern[6]}}}$ and $\\goldE{{{num_pattern[7]}}}$.",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G1 NA Q4 — Fractions, Money
# ---------------------------------------------------------------------------

def _gen_g1_na_q4_fractions(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Fractions: 1/2 and 1/4 (_0, _1, _2)."""
    slides = []

    # Strategy 1: half of a shape
    slides.append({
        "type": "worked_example",
        "title": "One Half",
        "strategy": "fraction_model",
        "steps": [
            {"text": "Cut a shape into 2 equal parts.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": 2, "shaded": 0, "label": "1/2"}},
            {"text": "Shade 1 part. That is $\\goldE{\\frac{1}{2}}$ — one half.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": 2, "shaded": 1, "label": "1/2"}},
            {"text": "One half means 1 out of 2 equal parts.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": 2, "shaded": 1, "label": "1/2"}},
        ]
    })

    # Strategy 2: quarter of a shape
    slides.append({
        "type": "worked_example",
        "title": "One Quarter",
        "strategy": "fraction_model",
        "steps": [
            {"text": "Cut a shape into 4 equal parts.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": 4, "shaded": 0, "label": "1/4"}},
            {"text": "Shade 1 part. That is $\\goldE{\\frac{1}{4}}$ — one quarter.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": 4, "shaded": 1, "label": "1/4"}},
            {"text": "One quarter means 1 out of 4 equal parts.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": 4, "shaded": 1, "label": "1/4"}},
        ]
    })

    # Strategy 3: compare 1/2 and 1/4
    slides.append({
        "type": "worked_example",
        "title": "Half vs Quarter",
        "strategy": "fraction_comparison",
        "steps": [
            {"text": "Which is bigger — one half or one quarter?",
             "visual_type": "Comparison",
             "visual_params": {
                 "left": {"visual": "FractionBar", "parts": 2, "shaded": 1, "label": "1/2"},
                 "right": {"visual": "FractionBar", "parts": 4, "shaded": 1, "label": "1/4"}
             }},
            {"text": "$\\frac{1}{2}$ is bigger than $\\frac{1}{4}$.\nMore equal parts means each part is smaller.",
             "visual_type": "Comparison",
             "visual_params": {
                 "left": {"visual": "FractionBar", "parts": 2, "shaded": 1, "label": "1/2"},
                 "right": {"visual": "FractionBar", "parts": 4, "shaded": 1, "label": "1/4"}
             }},
        ]
    })

    return slides


def _gen_g1_na_q4_money(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Money: Pesos, Coins, Bills (_3, _4, _5, _6)."""
    slides = []

    # Strategy 1: identify coins and bills
    slides.append({
        "type": "worked_example",
        "title": "Peso Coins and Bills",
        "strategy": "money_identification",
        "steps": [
            {"text": "These are Philippine peso coins.",
             "visual_type": "PesoMoney",
             "visual_params": {"coins": [1, 5, 10], "bills": [], "mode": "display"}},
            {"text": "These are peso bills.",
             "visual_type": "PesoMoney",
             "visual_params": {"coins": [], "bills": [20, 50, 100], "mode": "display"}},
            {"text": "We use coins and bills to buy things.",
             "visual_type": "PesoMoney",
             "visual_params": {"coins": [1, 5, 10], "bills": [20], "mode": "display"}},
        ]
    })

    # Strategy 2: total value of coins
    coin_vals = rng.sample([1, 5, 10, 25], rng.randint(2, 3))
    total = sum(coin_vals)
    slides.append({
        "type": "worked_example",
        "title": "Total Value of Coins",
        "strategy": "money_counting",
        "steps": [
            {"text": f"What is the total value of these coins?",
             "visual_type": "PesoMoney",
             "visual_params": {"coins": coin_vals, "bills": [], "mode": "count"}},
            {"text": f"{' + '.join(f'₱{v}' for v in coin_vals)} = $\\goldE{{₱{total}}}$",
             "visual_type": "PesoMoney",
             "visual_params": {"coins": coin_vals, "bills": [], "mode": "count", "show_total": True}},
        ]
    })

    # Strategy 3: simple word problem (interest-wrapped if possible)
    price = rng.randint(5, 30)
    paid = rng.randint(price, price + 20)
    change = paid - price
    obj = rng.choice(interest_ctx["objects"]) if interest_ctx else "item"
    actor = rng.choice(interest_ctx["actors"]) if interest_ctx else "a student"

    slides.append({
        "type": "worked_example",
        "title": "Adding Money",
        "strategy": "money_word_problem",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": f"{actor} pays ₱{paid} for {obj} that costs ₱{price}.",
             "visual_type": "PesoMoney",
             "visual_params": {"amount_paid": paid, "price": price, "mode": "change"}},
            {"text": f"₱{paid} − ₱{price} = $\\goldE{{₱{change}}}$ change.",
             "visual_type": "PesoMoney",
             "visual_params": {"amount_paid": paid, "price": price, "change": change, "mode": "change"}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G1 MG Q1 — 2D Shapes
# ---------------------------------------------------------------------------

def _gen_g1_mg_q1_shapes(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """2D Shapes: triangle, rectangle, square, sides, corners (_0, _1, _2)."""
    slides = []

    # Strategy 1: identify shapes
    slides.append({
        "type": "worked_example",
        "title": "Shapes Around Us",
        "strategy": "shape_identification",
        "steps": [
            {"text": "Here are three shapes.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["triangle", "rectangle", "square"]}},
            {"text": "A triangle has 3 sides and 3 corners.\nA rectangle has 4 sides and 4 corners.\nA square has 4 equal sides and 4 corners.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["triangle", "rectangle", "square"], "show_labels": True}},
            {"text": "Squares are special rectangles — all 4 sides are the same.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["rectangle", "square"], "show_labels": True, "highlight_equal_sides": True}},
        ]
    })

    # Strategy 2: count sides and corners
    shape = rng.choice(["triangle", "rectangle", "square"])
    sides = {"triangle": 3, "rectangle": 4, "square": 4}[shape]
    corners = sides

    slides.append({
        "type": "worked_example",
        "title": "Sides and Corners",
        "strategy": "shape_properties",
        "steps": [
            {"text": f"How many sides does a {shape} have?",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": [shape]}},
            {"text": f"Count the sides: $\\goldE{{{sides}}}$ sides.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": [shape], "highlight": "sides"}},
            {"text": f"Count the corners: $\\goldE{{{corners}}}$ corners.\nA {shape} has {sides} sides and {corners} corners.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": [shape], "highlight": "corners"}},
        ]
    })

    # Strategy 3: compose shapes
    slides.append({
        "type": "worked_example",
        "title": "Putting Shapes Together",
        "strategy": "compose_shapes",
        "steps": [
            {"text": "Two triangles can make a rectangle.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["triangle", "triangle"], "compose": "rectangle"}},
            {"text": "Four small squares can make a bigger square.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["square"] * 4, "compose": "big_square"}},
            {"text": "Big shapes are made from smaller shapes.",
             "visual_type": "ShapeDisplay",
             "visual_params": {"shapes": ["triangle", "triangle", "square", "square"], "compose": "house"}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G1 MG Q2 — Measuring Length (Non-Standard)
# ---------------------------------------------------------------------------

def _gen_g1_mg_q2_length(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Length measurement with non-standard units (_0, _1, _2)."""
    slides = []

    # Strategy 1: measure with non-standard unit (paperclip)
    obj_lengths = {
        "pencil": rng.randint(7, 12),
        "book": rng.randint(12, 18),
        "eraser": rng.randint(3, 6),
    }
    obj_name = rng.choice(list(obj_lengths.keys()))
    length = obj_lengths[obj_name]
    unit = "paperclip"

    slides.append({
        "type": "worked_example",
        "title": "Measuring with Non-Standard Units",
        "strategy": "measure_length",
        "steps": [
            {"text": f"How long is the {obj_name}?\nWe can use a {unit} to measure.",
             "visual_type": "LengthCompare",
             "visual_params": {"object": obj_name, "unit": unit, "length": length}},
            {"text": f"Line up {unit}s from one end to the other.",
             "visual_type": "LengthCompare",
             "visual_params": {"object": obj_name, "unit": unit, "length": length, "show_units": True}},
            {"text": f"The {obj_name} is $\\goldE{{{length}}}$ {unit}s long.",
             "visual_type": "LengthCompare",
             "visual_params": {"object": obj_name, "unit": unit, "length": length, "show_units": True, "highlight_result": True}},
        ]
    })

    # Strategy 2: compare lengths
    len_a = rng.randint(5, 10)
    len_b = rng.randint(3, len_a - 1)
    obj_a = "pencil"
    obj_b = "crayon"
    comparison = "longer" if len_a > len_b else "shorter"

    slides.append({
        "type": "worked_example",
        "title": "Comparing Lengths",
        "strategy": "compare_length",
        "steps": [
            {"text": f"Which is longer — the {obj_a} or the {obj_b}?",
             "visual_type": "LengthCompare",
             "visual_params": {
                 "items": [{"label": obj_a, "length": len_a}, {"label": obj_b, "length": len_b}],
                 "unit": "paperclip"
             }},
            {"text": f"The {obj_a} is {len_a} paperclips long.\nThe {obj_b} is {len_b} paperclips long.",
             "visual_type": "LengthCompare",
             "visual_params": {
                 "items": [{"label": obj_a, "length": len_a}, {"label": obj_b, "length": len_b}],
                 "unit": "paperclip", "show_units": True
             }},
            {"text": f"The {obj_a} is {comparison} than the {obj_b}.",
             "visual_type": "LengthCompare",
             "visual_params": {
                 "items": [{"label": obj_a, "length": len_a}, {"label": obj_b, "length": len_b}],
                 "unit": "paperclip", "show_units": True, "highlight_result": True
             }},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G1 MG Q4 — Turns, Time, Calendar
# ---------------------------------------------------------------------------

def _gen_g1_mg_q4_turns(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Half turn and quarter turn, clockwise and counter-clockwise (_0)."""
    slides = []

    slides.append({
        "type": "worked_example",
        "title": "Quarter Turn Clockwise",
        "strategy": "turn_demo",
        "steps": [
            {"text": "This arrow is pointing up.",
             "visual_type": "TurnDisplay",
             "visual_params": {"start_angle": 0, "direction": "clockwise", "amount": 0}},
            {"text": "A quarter turn clockwise: the arrow turns to the right.",
             "visual_type": "TurnDisplay",
             "visual_params": {"start_angle": 0, "direction": "clockwise", "amount": 90}},
            {"text": "A quarter turn = $\\goldE{90}$ degrees. Clockwise is the same direction as clock hands.",
             "visual_type": "TurnDisplay",
             "visual_params": {"start_angle": 0, "direction": "clockwise", "amount": 90, "show_clock_reference": True}},
        ]
    })

    slides.append({
        "type": "worked_example",
        "title": "Half Turn",
        "strategy": "turn_demo",
        "steps": [
            {"text": "This arrow is pointing up.",
             "visual_type": "TurnDisplay",
             "visual_params": {"start_angle": 0, "direction": "clockwise", "amount": 0}},
            {"text": "A half turn: the arrow now points down — the opposite direction.",
             "visual_type": "TurnDisplay",
             "visual_params": {"start_angle": 0, "direction": "clockwise", "amount": 180}},
            {"text": "A half turn = 2 quarter turns. It faces the opposite way.",
             "visual_type": "TurnDisplay",
             "visual_params": {"start_angle": 0, "direction": "clockwise", "amount": 180}},
        ]
    })

    return slides


def _gen_g1_mg_q4_time(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Telling Time, Days of Week, Calendar (_1, _2, _3, _4)."""
    slides = []

    # Strategy 1: read clock to the hour
    hour = rng.randint(1, 12)
    slides.append({
        "type": "worked_example",
        "title": "Reading the Clock",
        "strategy": "clock_reading",
        "steps": [
            {"text": f"What time does this clock show?",
             "visual_type": "ClockSet",
             "visual_params": {"hour": hour, "minute": 0}},
            {"text": f"The short hand points to $\\blueE{{{hour}}}$. The long hand points to 12.",
             "visual_type": "ClockSet",
             "visual_params": {"hour": hour, "minute": 0, "highlight": "hour_hand"}},
            {"text": f"The time is $\\goldE{{{hour}}}$:00 — {hour} o'clock.",
             "visual_type": "ClockSet",
             "visual_params": {"hour": hour, "minute": 0, "highlight": "answer"}},
        ]
    })

    # Strategy 2: half hour
    hour2 = rng.randint(1, 12)
    slides.append({
        "type": "worked_example",
        "title": "Half Hour",
        "strategy": "clock_reading",
        "steps": [
            {"text": f"What time does this clock show?",
             "visual_type": "ClockSet",
             "visual_params": {"hour": hour2, "minute": 30}},
            {"text": f"The long hand points to 6 — that means 30 minutes past.\nThe short hand is between {hour2} and {hour2 % 12 + 1}.",
             "visual_type": "ClockSet",
             "visual_params": {"hour": hour2, "minute": 30, "highlight": "both"}},
            {"text": f"The time is $\\goldE{{{hour2}}}$:30 — {hour2} thirty, or half past {hour2}.",
             "visual_type": "ClockSet",
             "visual_params": {"hour": hour2, "minute": 30, "highlight": "answer"}},
        ]
    })

    # Strategy 3: calendar
    slides.append({
        "type": "worked_example",
        "title": "Reading a Calendar",
        "strategy": "calendar_reading",
        "steps": [
            {"text": "A calendar shows all the days in a month.",
             "visual_type": "Calendar",
             "visual_params": {"month": rng.randint(1, 12), "year": 2025, "highlight_day": rng.randint(1, 28)}},
            {"text": "There are 7 days in a week:\nMonday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday.",
             "visual_type": "Calendar",
             "visual_params": {"month": rng.randint(1, 12), "year": 2025, "show_week_header": True}},
            {"text": "We can use a calendar to find any day of the month.",
             "visual_type": "Calendar",
             "visual_params": {"month": rng.randint(1, 12), "year": 2025, "highlight_day": rng.randint(1, 28)}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G1 DP Q3 — Data, Pictograph, Table
# ---------------------------------------------------------------------------

def _gen_g1_dp_q3_data(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Collecting data, pictograph without scale, table (_0, _1, _2, _3)."""
    slides = []

    # Generate simple data — use interest context if available
    if interest_ctx:
        categories = rng.sample(interest_ctx["objects"], min(3, len(interest_ctx["objects"])))
    else:
        categories = ["cats", "dogs", "birds"]
    counts = [rng.randint(1, 6) for _ in categories]
    data = [{"label": cat, "count": cnt} for cat, cnt in zip(categories, counts)]

    # Strategy 1: collect data (tally)
    slides.append({
        "type": "worked_example",
        "title": "Collecting Data",
        "strategy": "data_collection",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": f"We asked students: which do you like best?\n{', '.join(categories)}",
             "visual_type": "PictographDisplay",
             "visual_params": {"data": data, "scale": 1, "mode": "tally"}},
            {"text": f"We count the votes for each choice.",
             "visual_type": "PictographDisplay",
             "visual_params": {"data": data, "scale": 1, "mode": "tally", "show_totals": True}},
            {"text": "Counting answers is called collecting data.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 2: make a pictograph
    most = max(data, key=lambda x: x["count"])
    slides.append({
        "type": "worked_example",
        "title": "Making a Pictograph",
        "strategy": "pictograph",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": "A pictograph uses pictures to show data.",
             "visual_type": "PictographDisplay",
             "visual_params": {"data": data, "scale": 1, "mode": "pictograph"}},
            {"text": f"Each picture stands for 1 student.\n{most['label'].capitalize()} got the most votes: $\\goldE{{{most['count']}}}$ students.",
             "visual_type": "PictographDisplay",
             "visual_params": {"data": data, "scale": 1, "mode": "pictograph", "highlight": most["label"]}},
            {"text": "We can read a pictograph to answer questions about data.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 3: organize into a table
    slides.append({
        "type": "worked_example",
        "title": "Data in a Table",
        "strategy": "data_table",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": "We can also show data in a table.",
             "visual_type": "PictographDisplay",
             "visual_params": {"data": data, "scale": 1, "mode": "table"}},
            {"text": "A table has rows and columns.\nEach row shows one category and its count.",
             "visual_type": "PictographDisplay",
             "visual_params": {"data": data, "scale": 1, "mode": "table", "show_labels": True}},
            {"text": "Tables make it easy to compare numbers.",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# Registration — called by __init__.py
# ---------------------------------------------------------------------------

def register():
    """Register all G1 node groups into MINI_LESSON_GROUPS and _INTRODUCTIONS."""
    from backend.app.intro_gen.generator import MINI_LESSON_GROUPS
    from backend.app.intro_gen import _INTRODUCTIONS

    # -----------------------------------------------------------------------
    # G1 NA Q2
    # -----------------------------------------------------------------------
    MINI_LESSON_GROUPS["g1_na_q2"] = {
        "node_label": "Grade 1 - Counting to 100, Place Value & Addition",
        "grade": 1,
        "groups": [
            {
                "title": "Counting to 100 & Skip Counting",
                "node_key": "g1_na_q2",
                "competencies": ["mat_g1_na_q2_0", "mat_g1_na_q2_1"],
                "vocab_terms": ["skip counting"],
                "generator": _gen_g1_na_q2_counting,
            },
            {
                "title": "Place Value: Tens and Ones",
                "node_key": "g1_na_q2",
                "competencies": ["mat_g1_na_q2_2", "mat_g1_na_q2_3", "mat_g1_na_q2_4"],
                "vocab_terms": ["place value", "digit", "tens", "ones", "expanded form"],
                "generator": _gen_g1_na_q2_place_value,
            },
            {
                "title": "Adding to 100",
                "node_key": "g1_na_q2",
                "competencies": ["mat_g1_na_q2_5", "mat_g1_na_q2_6"],
                "vocab_terms": [],
                "generator": _gen_g1_na_q2_addition,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g1_na_q2::Counting to 100 & Skip Counting": (
            "You can count to 20. Numbers keep going.\n"
            "Let's count all the way to 100.\n"
            "And instead of counting by 1s, let's try jumping by 2s, 5s, and 10s."
        ),
        "g1_na_q2::Place Value: Tens and Ones": (
            "You can count to 100. Now let's look inside bigger numbers.\n"
            "The digits in a number each have a special meaning.\n"
            "Where a digit sits tells you how much it is worth."
        ),
        "g1_na_q2::Adding to 100": (
            "You can add numbers up to 20.\n"
            "Now let's add bigger numbers — all the way to 100.\n"
            "Tens and ones make it easy."
        ),
    })

    # -----------------------------------------------------------------------
    # G1 NA Q3
    # -----------------------------------------------------------------------
    MINI_LESSON_GROUPS["g1_na_q3"] = {
        "node_label": "Grade 1 - Subtraction & Patterns",
        "grade": 1,
        "groups": [
            {
                "title": "Subtraction",
                "node_key": "g1_na_q3",
                "competencies": ["mat_g1_na_q3_0", "mat_g1_na_q3_1",
                                  "mat_g1_na_q3_2", "mat_g1_na_q3_3"],
                "vocab_terms": ["subtraction", "difference", "missing number"],
                "generator": _gen_g1_na_q3_subtraction,
            },
            {
                "title": "Subtracting to 100",
                "node_key": "g1_na_q3",
                "competencies": ["mat_g1_na_q3_4", "mat_g1_na_q3_5"],
                "vocab_terms": [],
                "generator": _gen_g1_na_q3_subtraction_100,
            },
            {
                "title": "Repeating Patterns",
                "node_key": "g1_na_q3",
                "competencies": ["mat_g1_na_q3_6", "mat_g1_na_q3_7"],
                "vocab_terms": ["pattern", "repeating pattern"],
                "generator": _gen_g1_na_q3_patterns,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g1_na_q3::Subtraction": (
            "You can put groups together to add.\n"
            "Now let's take groups apart.\n"
            "What's left when we take some away?"
        ),
        "g1_na_q3::Subtracting to 100": (
            "You can subtract numbers up to 20.\n"
            "Now let's use tens and ones to subtract bigger numbers."
        ),
        "g1_na_q3::Repeating Patterns": (
            "Look around you — patterns are everywhere.\n"
            "A tile floor. A song. A row of beads.\n"
            "Let's find what repeats."
        ),
    })

    # -----------------------------------------------------------------------
    # G1 NA Q4
    # -----------------------------------------------------------------------
    MINI_LESSON_GROUPS["g1_na_q4"] = {
        "node_label": "Grade 1 - Fractions & Money",
        "grade": 1,
        "groups": [
            {
                "title": "Fractions",
                "node_key": "g1_na_q4",
                "competencies": ["mat_g1_na_q4_0", "mat_g1_na_q4_1", "mat_g1_na_q4_2"],
                "vocab_terms": ["fraction", "half", "quarter", "whole"],
                "generator": _gen_g1_na_q4_fractions,
            },
            {
                "title": "Money",
                "node_key": "g1_na_q4",
                "competencies": ["mat_g1_na_q4_3", "mat_g1_na_q4_4",
                                  "mat_g1_na_q4_5", "mat_g1_na_q4_6"],
                "vocab_terms": ["peso", "₱", "coin", "bill"],
                "generator": _gen_g1_na_q4_money,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g1_na_q4::Fractions": (
            "You can count whole numbers.\n"
            "What if we cut something into equal parts?\n"
            "Let's look at parts of a whole."
        ),
        "g1_na_q4::Money": (
            "You can count numbers.\n"
            "Money uses special numbers called pesos.\n"
            "Let's learn about coins and bills."
        ),
    })

    # -----------------------------------------------------------------------
    # G1 MG Q1
    # -----------------------------------------------------------------------
    MINI_LESSON_GROUPS["g1_mg_q1"] = {
        "node_label": "Grade 1 - 2D Shapes",
        "grade": 1,
        "groups": [
            {
                "title": "2D Shapes",
                "node_key": "g1_mg_q1",
                "competencies": ["mat_g1_mg_q1_0", "mat_g1_mg_q1_1", "mat_g1_mg_q1_2"],
                "vocab_terms": ["triangle", "rectangle", "square", "side", "corner"],
                "generator": _gen_g1_mg_q1_shapes,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g1_mg_q1::2D Shapes": (
            "Look at a door. A window. A slice of pizza.\n"
            "These are all different shapes.\n"
            "Let's learn the names of flat shapes and what makes each one special."
        ),
    })

    # -----------------------------------------------------------------------
    # G1 MG Q2
    # -----------------------------------------------------------------------
    MINI_LESSON_GROUPS["g1_mg_q2"] = {
        "node_label": "Grade 1 - Measuring Length",
        "grade": 1,
        "groups": [
            {
                "title": "Measuring Length",
                "node_key": "g1_mg_q2",
                "competencies": ["mat_g1_mg_q2_0", "mat_g1_mg_q2_1", "mat_g1_mg_q2_2"],
                "vocab_terms": ["length", "measure"],
                "generator": _gen_g1_mg_q2_length,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g1_mg_q2::Measuring Length": (
            "Is your pencil longer or shorter than your eraser?\n"
            "Let's find out — by measuring.\n"
            "We can use any object as a unit to measure length."
        ),
    })

    # -----------------------------------------------------------------------
    # G1 MG Q4
    # -----------------------------------------------------------------------
    MINI_LESSON_GROUPS["g1_mg_q4"] = {
        "node_label": "Grade 1 - Turns, Time & Calendar",
        "grade": 1,
        "groups": [
            {
                "title": "Turns",
                "node_key": "g1_mg_q4",
                "competencies": ["mat_g1_mg_q4_0"],
                "vocab_terms": ["clockwise", "counter-clockwise", "half turn", "quarter turn"],
                "generator": _gen_g1_mg_q4_turns,
            },
            {
                "title": "Telling Time & Calendar",
                "node_key": "g1_mg_q4",
                "competencies": ["mat_g1_mg_q4_1", "mat_g1_mg_q4_2",
                                  "mat_g1_mg_q4_3", "mat_g1_mg_q4_4"],
                "vocab_terms": ["hour", "half hour", "quarter hour", "analog clock", "calendar"],
                "generator": _gen_g1_mg_q4_time,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g1_mg_q4::Turns": (
            "When you spin in a circle, you are turning.\n"
            "Some turns are small. Some turns are big.\n"
            "Let's learn to describe how much something has turned."
        ),
        "g1_mg_q4::Telling Time & Calendar": (
            "We use a clock to know what time it is.\n"
            "We use a calendar to know what day it is.\n"
            "Let's learn how to read both."
        ),
    })

    # -----------------------------------------------------------------------
    # G1 DP Q3
    # -----------------------------------------------------------------------
    MINI_LESSON_GROUPS["g1_dp_q3"] = {
        "node_label": "Grade 1 - Data & Pictographs",
        "grade": 1,
        "groups": [
            {
                "title": "Collecting & Showing Data",
                "node_key": "g1_dp_q3",
                "competencies": ["mat_g1_dp_q3_0", "mat_g1_dp_q3_1",
                                  "mat_g1_dp_q3_2", "mat_g1_dp_q3_3"],
                "vocab_terms": ["data", "pictograph", "table"],
                "generator": _gen_g1_dp_q3_data,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g1_dp_q3::Collecting & Showing Data": (
            "What is your class's favourite colour? Favourite food?\n"
            "We can find out by asking and counting.\n"
            "Collecting and showing answers is called working with data."
        ),
    })
