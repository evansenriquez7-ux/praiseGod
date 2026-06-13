"""
Grade 3 Intro Content Generators
Covers: G3 NA Q1-Q4, G3 MG Q1/Q2/Q4, G3 DP Q3

Visual types used:
  Existing (implemented): NumberLine, PlaceValueBlocks, ObjectGroup, NumberCards,
                          Comparison, PesoMoney
  New (need frontend):    SkipCountLine, FractionBar, PatternRow, ArrayGrid,
                          BarGraph, ProbabilityDisplay, AreaGrid, LineDisplay,
                          BalanceScale, CapacityDisplay, SymmetryDisplay
"""

import random
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# G3 NA Q1 — Numbers to 10 000, Rounding, Comparing
# ---------------------------------------------------------------------------

def _gen_g3_na_q1_numbers(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Numbers to 10 000, ordinals to 100th, place value (_0–_3)."""
    slides = []

    num = rng.randint(1234, 9876)
    th = num // 1000
    h = (num % 1000) // 100
    t = (num % 100) // 10
    o = num % 10

    slides.append({
        "type": "worked_example",
        "title": "Numbers to 10 000",
        "strategy": "place_value",
        "steps": [
            {"text": f"The numeral $\\blueE{{{num:,}}}$ has 4 digits.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": num}},
            {"text": (f"$\\blueE{{{th}}}$ thousands = {th * 1000}\n"
                      f"$\\maroonD{{{h}}}$ hundreds = {h * 100}\n"
                      f"{t} tens = {t * 10}\n"
                      f"{o} ones = {o}"),
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": num, "highlight_all": True}},
            {"text": f"$\\blueE{{{num:,}}}$ = {th * 1000} + {h * 100} + {t * 10} + {o}",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Skip count by 1000s
    start = rng.choice([1000, 2000, 3000])
    seq = [start + 1000 * i for i in range(5)]
    slides.append({
        "type": "worked_example",
        "title": "Counting by 1 000s",
        "strategy": "skip_count",
        "steps": [
            {"text": f"Skip count by 1 000s: {seq[0]}, {seq[1]}, {seq[2]}...",
             "visual_type": "SkipCountLine",
             "visual_params": {"start": 0, "end": 11000, "step": 1000,
                               "from": seq[0], "highlight": seq}},
            {"text": f"Each jump is 1 000. What comes after {seq[-1]}? $\\goldE{{{seq[-1] + 1000:,}}}$.",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g3_na_q1_rounding(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Rounding to nearest ten, hundred, thousand (_4)."""
    slides = []

    # Round to nearest ten
    n_ten = rng.randint(23, 87)
    rounded_ten = round(n_ten / 10) * 10
    lower_ten = (n_ten // 10) * 10
    upper_ten = lower_ten + 10
    closer = "up" if n_ten >= (lower_ten + 5) else "down"

    slides.append({
        "type": "worked_example",
        "title": "Rounding to the Nearest Ten",
        "strategy": "rounding",
        "steps": [
            {"text": f"Round $\\blueE{{{n_ten}}}$ to the nearest ten.\nIt is between {lower_ten} and {upper_ten}.",
             "visual_type": "NumberLine",
             "visual_params": {"start": lower_ten, "end": upper_ten + 1,
                               "markers": [lower_ten, n_ten, upper_ten]}},
            {"text": f"$\\blueE{{{n_ten}}}$ is closer to $\\goldE{{{rounded_ten}}}$.",
             "visual_type": "NumberLine",
             "visual_params": {"start": lower_ten, "end": upper_ten + 1,
                               "markers": [lower_ten, upper_ten], "highlight": n_ten}},
            {"text": f"$\\blueE{{{n_ten}}}$ rounded to the nearest ten = $\\goldE{{{rounded_ten}}}$.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Round to nearest hundred
    n_hun = rng.randint(123, 876)
    rounded_hun = round(n_hun / 100) * 100
    lower_hun = (n_hun // 100) * 100
    upper_hun = lower_hun + 100

    slides.append({
        "type": "worked_example",
        "title": "Rounding to the Nearest Hundred",
        "strategy": "rounding",
        "steps": [
            {"text": f"Round $\\blueE{{{n_hun}}}$ to the nearest hundred.\nIt is between {lower_hun} and {upper_hun}.",
             "visual_type": "NumberLine",
             "visual_params": {"start": lower_hun, "end": upper_hun + 10,
                               "markers": [lower_hun, n_hun, upper_hun]}},
            {"text": f"Look at the tens digit: {(n_hun % 100) // 10}.\nIf it is 5 or more, round up.",
             "visual_type": None, "visual_params": None},
            {"text": f"$\\blueE{{{n_hun}}}$ rounded to the nearest hundred = $\\goldE{{{rounded_hun}}}$.",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g3_na_q1_comparing(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Compare and order numbers to 10 000 using >, <, = (_5, _6)."""
    slides = []

    a = rng.randint(1000, 9000)
    b = rng.randint(1000, 9000)
    while a == b:
        b = rng.randint(1000, 9000)
    symbol = ">" if a > b else "<"

    slides.append({
        "type": "worked_example",
        "title": "Comparing with > and <",
        "strategy": "comparison",
        "steps": [
            {"text": f"Compare $\\blueE{{{a:,}}}$ and $\\maroonD{{{b:,}}}$.",
             "visual_type": "Comparison",
             "visual_params": {"left": a, "right": b}},
            {"text": (f"Compare thousands first: {a // 1000} vs {b // 1000}.\n"
                      f"The bigger thousands digit shows the bigger number."),
             "visual_type": None, "visual_params": None},
            {"text": f"$\\blueE{{{a:,}}}$ $\\goldE{{{symbol}}}$ $\\maroonD{{{b:,}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Order 4 numbers
    nums = sorted(random.sample(range(1000, 9999), 4))
    shuffled = nums[:]
    random.shuffle(shuffled)

    slides.append({
        "type": "worked_example",
        "title": "Ordering Numbers to 10 000",
        "strategy": "ordering",
        "steps": [
            {"text": f"Put these in order from smallest to largest:\n{', '.join(f'{x:,}' for x in shuffled)}",
             "visual_type": "NumberCards",
             "visual_params": {"numbers": shuffled, "ordered": False}},
            {"text": f"In order: {', '.join(f'{x:,}' for x in nums)}",
             "visual_type": "NumberCards",
             "visual_params": {"numbers": nums, "ordered": True}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G3 NA Q2 — Money, Addition/Subtraction to 10 000, Order of Operations
# ---------------------------------------------------------------------------

def _gen_g3_na_q2_money(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Money notation in words and symbols (_0)."""
    slides = []

    amount = rng.randint(150, 5000)
    hundreds = amount // 100
    tens = (amount % 100) // 10
    ones = amount % 10

    slides.append({
        "type": "worked_example",
        "title": "Writing Money",
        "strategy": "money_notation",
        "steps": [
            {"text": f"₱{amount} can also be written as PhP {amount}.",
             "visual_type": "PesoMoney",
             "visual_params": {"amount": amount, "mode": "notation"}},
            {"text": (f"In words: "
                      f"{amount} pesos"),
             "visual_type": None, "visual_params": None},
            {"text": f"₱{amount} = PhP {amount} = {amount} pesos",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g3_na_q2_add_subtract(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Addition and subtraction to 10 000, estimation (_1–_5, _7)."""
    slides = []

    # Strategy 1: addition to 10 000
    a = rng.randint(1000, 5000)
    b = rng.randint(1000, 9999 - a)
    result = a + b
    est_a = round(a / 1000) * 1000
    est_b = round(b / 1000) * 1000

    slides.append({
        "type": "worked_example",
        "title": "Adding to 10 000",
        "strategy": "place_value_addition",
        "steps": [
            {"text": f"Estimate first: {a:,} ≈ {est_a:,}, {b:,} ≈ {est_b:,}\nEstimate: {est_a:,} + {est_b:,} = {est_a + est_b:,}",
             "visual_type": None, "visual_params": None},
            {"text": f"Now add exactly: $\\blueE{{{a:,}}}$ + $\\maroonD{{{b:,}}}$",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number_a": a, "number_b": b, "mode": "add"}},
            {"text": f"$\\blueE{{{a:,}}}$ + $\\maroonD{{{b:,}}}$ = $\\goldE{{{result:,}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 2: subtraction from 10 000
    c = rng.randint(3000, 9000)
    d = rng.randint(1000, c - 1000)
    result2 = c - d

    slides.append({
        "type": "worked_example",
        "title": "Subtracting from 10 000",
        "strategy": "place_value_subtraction",
        "steps": [
            {"text": f"$\\blueE{{{c:,}}}$ − $\\maroonD{{{d:,}}}$ = ?",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": c}},
            {"text": f"Subtract place by place. Regroup if needed.",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": c, "subtract": d, "mode": "subtract"}},
            {"text": f"$\\blueE{{{c:,}}}$ − $\\maroonD{{{d:,}}}$ = $\\goldE{{{result2:,}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g3_na_q2_order_ops(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Order of operations (_6)."""
    slides = []

    a = rng.randint(10, 30)
    b = rng.randint(5, 15)
    c = rng.randint(2, 8)

    # left to right: (a + b) - c
    result = a + b - c

    slides.append({
        "type": "worked_example",
        "title": "Order of Operations",
        "strategy": "order_of_operations",
        "steps": [
            {"text": f"Calculate: $\\blueE{{{a}}}$ + $\\maroonD{{{b}}}$ − $\\goldE{{{c}}}$",
             "visual_type": None, "visual_params": None},
            {"text": f"Work left to right.\nFirst: $\\blueE{{{a}}}$ + $\\maroonD{{{b}}}$ = {a + b}",
             "visual_type": None, "visual_params": None},
            {"text": f"Then: {a + b} − $\\goldE{{{c}}}$ = $\\goldE{{{result}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    # With brackets
    d = rng.randint(5, 15)
    e = rng.randint(2, 8)
    f = rng.randint(2, 6)
    bracket_result = (d + e) * f

    slides.append({
        "type": "worked_example",
        "title": "Brackets First",
        "strategy": "order_of_operations",
        "steps": [
            {"text": f"Calculate: ($\\blueE{{{d}}}$ + $\\maroonD{{{e}}}$) × $\\goldE{{{f}}}$",
             "visual_type": None, "visual_params": None},
            {"text": f"Brackets first: $\\blueE{{{d}}}$ + $\\maroonD{{{e}}}$ = {d + e}",
             "visual_type": None, "visual_params": None},
            {"text": f"Then: {d + e} × $\\goldE{{{f}}}$ = $\\goldE{{{bracket_result}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G3 NA Q3 — Multiplication (6-9 tables), Patterns with Missing Terms
# ---------------------------------------------------------------------------

def _gen_g3_na_q3_multiplication(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Multiply using 6, 7, 8, 9 tables; multi-digit × 1-digit (_0–_4)."""
    slides = []

    a = rng.randint(6, 9)
    b = rng.randint(2, 9)
    product = a * b

    slides.append({
        "type": "worked_example",
        "title": f"The {a} Times Table",
        "strategy": "times_table",
        "steps": [
            {"text": f"$\\blueE{{{a}}}$ × $\\maroonD{{{b}}}$ = ?",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": a, "cols": b}},
            {"text": f"Count {a} rows of {b}. Total: $\\goldE{{{product}}}$.",
             "visual_type": "ArrayGrid",
             "visual_params": {"rows": a, "cols": b, "show_count": True}},
            {"text": f"$\\blueE{{{a}}}$ × $\\maroonD{{{b}}}$ = $\\goldE{{{product}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Multi-digit × 1-digit
    multi = rng.randint(12, 49)
    single = rng.randint(2, 9)
    m_result = multi * single
    m_tens = (multi // 10) * single
    m_ones = (multi % 10) * single

    slides.append({
        "type": "worked_example",
        "title": "Multiplying Bigger Numbers",
        "strategy": "multi_digit_multiplication",
        "steps": [
            {"text": f"$\\blueE{{{multi}}}$ × $\\maroonD{{{single}}}$ = ?",
             "visual_type": "PlaceValueBlocks",
             "visual_params": {"number": multi, "multiply_by": single}},
            {"text": (f"Multiply ones: {multi % 10} × {single} = {m_ones}\n"
                      f"Multiply tens: {multi // 10} × {single} = {m_tens}\n"
                      f"Add: {m_tens} + {m_ones} = {m_result}"),
             "visual_type": None, "visual_params": None},
            {"text": f"$\\blueE{{{multi}}}$ × $\\maroonD{{{single}}}$ = $\\goldE{{{m_result}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _gen_g3_na_q3_patterns(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Patterns with repeating and increasing components, missing term (_5, _6)."""
    slides = []

    # Increasing component embedded in repeating pattern
    # e.g. 1, 2, 1, 3, 1, 4, 1, 5 — "A, B, A, B+1, A, B+2..."
    base = rng.randint(1, 5)
    inc_start = rng.randint(2, 6)
    # Interleaved pattern: base, inc_start, base, inc_start+1, ...
    interleaved = []
    for i in range(5):
        interleaved.append(base)
        interleaved.append(inc_start + i)
    shown = interleaved[:8]
    missing_pos = 7  # hide last
    answer = interleaved[8]

    slides.append({
        "type": "worked_example",
        "title": "Finding the Missing Term",
        "strategy": "pattern_missing",
        "steps": [
            {"text": f"Find the missing term in this pattern:\n{', '.join(str(x) for x in shown[:6])}, ?, ...",
             "visual_type": "PatternRow",
             "visual_params": {"items": [str(x) for x in shown[:6]], "hide_last": 1}},
            {"text": (f"The pattern repeats {base} and an increasing number.\n"
                      f"After {shown[-1]}, the next increasing number is {shown[-1] + 1 if shown[-1] != base else inc_start + (len(shown) // 2)}."),
             "visual_type": "PatternRow",
             "visual_params": {"items": [str(x) for x in shown[:6]], "show_rule": True}},
            {"text": f"The missing term is $\\goldE{{{shown[6] if len(shown) > 6 else answer}}}$.",
             "visual_type": None, "visual_params": None},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G3 NA Q4 — Division with Remainder, Improper Fractions
# ---------------------------------------------------------------------------

def _gen_g3_na_q4_division(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Division with remainder, 6-9 tables (_0–_5)."""
    slides = []

    # Strategy 1: equal jumps on number line
    divisor = rng.randint(3, 9)
    quotient = rng.randint(3, 6)
    dividend = divisor * quotient
    slides.append({
        "type": "worked_example",
        "title": "Division on a Number Line",
        "strategy": "number_line_division",
        "steps": [
            {"text": f"$\\blueE{{{dividend}}}$ ÷ $\\maroonD{{{divisor}}}$ = ?",
             "visual_type": "NumberLine",
             "visual_params": {"start": 0, "end": dividend + 2, "markers": [0]}},
            {"text": f"Jump {divisor} at a time from 0 to {dividend}.",
             "visual_type": "NumberLine",
             "visual_params": {"start": 0, "end": dividend + 2,
                               "equal_jumps": {"step": divisor, "end": dividend}}},
            {"text": f"We made $\\goldE{{{quotient}}}$ jumps.\n$\\blueE{{{dividend}}}$ ÷ $\\maroonD{{{divisor}}}$ = $\\goldE{{{quotient}}}$",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 2: division with remainder
    div_b = rng.randint(3, 9)
    quot_b = rng.randint(2, 5)
    rem_b = rng.randint(1, div_b - 1)
    dividend_b = div_b * quot_b + rem_b
    obj = rng.choice(interest_ctx["objects"]) if interest_ctx else "items"
    actor = rng.choice(interest_ctx["actors"]) if interest_ctx else "students"

    slides.append({
        "type": "worked_example",
        "title": "Division with Remainder",
        "strategy": "division_remainder",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": f"Share $\\blueE{{{dividend_b}}}$ {obj} equally among $\\maroonD{{{div_b}}}$ {actor}.",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": obj, "count": dividend_b, "groups": div_b}},
            {"text": f"Each gets $\\goldE{{{quot_b}}}$ {obj}. There are $\\goldE{{{rem_b}}}$ left over.",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": obj, "count": dividend_b,
                               "groups": div_b, "remainder": rem_b}},
            {"text": f"$\\blueE{{{dividend_b}}}$ ÷ $\\maroonD{{{div_b}}}$ = $\\goldE{{{quot_b}}}$ remainder $\\goldE{{{rem_b}}}$",
             "visual_type": "ObjectGroup",
             "visual_params": {"object": obj, "count": dividend_b,
                               "groups": div_b, "remainder": rem_b, "highlight_remainder": True}},
        ]
    })

    return slides


def _gen_g3_na_q4_fractions(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Improper fractions, adding/subtracting similar fractions (_6, _7)."""
    slides = []

    denom = rng.choice([2, 3, 4])
    numer = denom + rng.randint(1, denom)  # numerator > denominator

    slides.append({
        "type": "worked_example",
        "title": "Fractions Greater than 1",
        "strategy": "improper_fraction",
        "steps": [
            {"text": f"$\\frac{{{numer}}}{{{denom}}}$ — the numerator is bigger than the denominator.\nThis is an improper fraction.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": denom, "shaded": numer, "allow_overflow": True,
                               "label": f"{numer}/{denom}"}},
            {"text": f"$\\frac{{{numer}}}{{{denom}}}$ = more than 1 whole.",
             "visual_type": "FractionBar",
             "visual_params": {"parts": denom, "shaded": numer, "allow_overflow": True,
                               "show_wholes": True}},
            {"text": f"$\\frac{{{numer}}}{{{denom}}}$ = {numer // denom} whole(s) and $\\frac{{{numer % denom}}}{{{denom}}}$",
             "visual_type": "FractionBar",
             "visual_params": {"parts": denom, "shaded": numer, "allow_overflow": True,
                               "show_wholes": True, "show_mixed": True}},
        ]
    })

    # Adding similar fractions
    n1 = rng.randint(1, denom - 1)
    n2 = rng.randint(1, denom - 1)
    frac_sum = n1 + n2
    result_whole = frac_sum // denom
    result_rem = frac_sum % denom

    slides.append({
        "type": "worked_example",
        "title": "Adding Similar Fractions",
        "strategy": "fraction_addition",
        "steps": [
            {"text": f"$\\frac{{{n1}}}{{{denom}}}$ + $\\frac{{{n2}}}{{{denom}}}$ = ?",
             "visual_type": "Comparison",
             "visual_params": {
                 "left": {"visual": "FractionBar", "parts": denom, "shaded": n1, "label": f"{n1}/{denom}"},
                 "right": {"visual": "FractionBar", "parts": denom, "shaded": n2, "label": f"{n2}/{denom}"}
             }},
            {"text": f"Same denominator — add the numerators: {n1} + {n2} = {frac_sum}",
             "visual_type": "FractionBar",
             "visual_params": {"parts": denom, "shaded": frac_sum, "allow_overflow": True}},
            {"text": (f"$\\frac{{{n1}}}{{{denom}}}$ + $\\frac{{{n2}}}{{{denom}}}$ = $\\frac{{{frac_sum}}}{{{denom}}}$" +
                      (f" = {result_whole} and $\\frac{{{result_rem}}}{{{denom}}}$" if result_whole > 0 else "")),
             "visual_type": "FractionBar",
             "visual_params": {"parts": denom, "shaded": frac_sum, "allow_overflow": True, "show_wholes": True}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G3 MG Q1 — Area, Lines and Points
# ---------------------------------------------------------------------------

def _gen_g3_mg_q1_area(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Area of squares and rectangles in sq cm (_0–_3)."""
    slides = []

    rows = rng.randint(3, 6)
    cols = rng.randint(3, 6)
    area = rows * cols

    slides.append({
        "type": "worked_example",
        "title": "Counting Square Units",
        "strategy": "area_counting",
        "steps": [
            {"text": f"This rectangle is {rows} units tall and {cols} units wide.\nHow many squares fit inside?",
             "visual_type": "AreaGrid",
             "visual_params": {"rows": rows, "cols": cols, "mode": "count"}},
            {"text": f"Count the squares: {rows} rows × {cols} squares each = $\\goldE{{{area}}}$ squares.",
             "visual_type": "AreaGrid",
             "visual_params": {"rows": rows, "cols": cols, "show_count": True}},
            {"text": f"Area = $\\goldE{{{area}}}$ square units.",
             "visual_type": "AreaGrid",
             "visual_params": {"rows": rows, "cols": cols, "show_total": True}},
        ]
    })

    # Area formula
    l = rng.randint(4, 8)
    w = rng.randint(3, l)
    a2 = l * w

    slides.append({
        "type": "worked_example",
        "title": "Area Formula",
        "strategy": "area_formula",
        "steps": [
            {"text": f"Rectangle: length = {l} cm, width = {w} cm.",
             "visual_type": "AreaGrid",
             "visual_params": {"rows": w, "cols": l, "unit": "cm"}},
            {"text": f"Area = length × width = {l} × {w} = $\\goldE{{{a2}}}$ sq. cm",
             "visual_type": "AreaGrid",
             "visual_params": {"rows": w, "cols": l, "unit": "cm", "show_formula": True}},
            {"text": f"Area = $\\goldE{{{a2}}}$ sq. cm",
             "visual_type": "AreaGrid",
             "visual_params": {"rows": w, "cols": l, "unit": "cm", "show_formula": True, "show_total": True}},
        ]
    })

    return slides


def _gen_g3_mg_q1_lines(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Points, lines, line segments, rays, parallel, perpendicular, intersecting (_4–_6)."""
    slides = []

    slides.append({
        "type": "worked_example",
        "title": "Points, Lines and Segments",
        "strategy": "geometric_figures",
        "steps": [
            {"text": "A point is an exact location. We show it as a dot.",
             "visual_type": "LineDisplay",
             "visual_params": {"type": "point", "label": "A"}},
            {"text": "A line goes on forever in both directions.\nA line segment has two endpoints — it stops.",
             "visual_type": "LineDisplay",
             "visual_params": {"type": "line_and_segment"}},
            {"text": "A ray starts at one point and goes on forever in one direction.",
             "visual_type": "LineDisplay",
             "visual_params": {"type": "ray"}},
        ]
    })

    slides.append({
        "type": "worked_example",
        "title": "Parallel and Perpendicular Lines",
        "strategy": "line_relationships",
        "steps": [
            {"text": "Parallel lines never meet. They are always the same distance apart.",
             "visual_type": "LineDisplay",
             "visual_params": {"type": "parallel"}},
            {"text": "Perpendicular lines meet at a right angle (a square corner).",
             "visual_type": "LineDisplay",
             "visual_params": {"type": "perpendicular"}},
            {"text": "Intersecting lines cross each other at one point.",
             "visual_type": "LineDisplay",
             "visual_params": {"type": "intersecting"}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G3 MG Q2 — Mass and Capacity
# ---------------------------------------------------------------------------

def _gen_g3_mg_q2_mass(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Mass in grams and kilograms, balance scale (_0–_2)."""
    slides = []

    heavy_g = rng.randint(800, 2000)
    light_g = rng.randint(50, 400)
    obj_heavy = rng.choice(["book", "bottle", "brick"])
    obj_light = rng.choice(["eraser", "pencil", "leaf"])

    slides.append({
        "type": "worked_example",
        "title": "Measuring Mass",
        "strategy": "mass_measurement",
        "steps": [
            {"text": "We measure mass in grams (g) and kilograms (kg).\n1 000 g = 1 kg.",
             "visual_type": "BalanceScale",
             "visual_params": {"left": {"label": obj_heavy, "mass_g": heavy_g},
                               "right": {"label": "1 kg weight", "mass_g": 1000},
                               "mode": "compare"}},
            {"text": (f"A {obj_heavy} has a mass of about {heavy_g} g.\n"
                      f"A {obj_light} has a mass of about {light_g} g."),
             "visual_type": "BalanceScale",
             "visual_params": {"left": {"label": obj_heavy, "mass_g": heavy_g},
                               "right": {"label": obj_light, "mass_g": light_g},
                               "mode": "compare"}},
        ]
    })

    # Balance scale comparison
    a_mass = rng.randint(200, 600)
    b_mass = rng.randint(200, 600)
    heavier = obj_heavy if a_mass > b_mass else obj_light
    lighter = obj_light if a_mass > b_mass else obj_heavy

    slides.append({
        "type": "worked_example",
        "title": "Using a Balance Scale",
        "strategy": "balance_scale",
        "steps": [
            {"text": f"Which is heavier — the {obj_heavy} or the {obj_light}?",
             "visual_type": "BalanceScale",
             "visual_params": {"left": {"label": obj_heavy, "mass_g": a_mass},
                               "right": {"label": obj_light, "mass_g": b_mass},
                               "mode": "balance"}},
            {"text": f"The heavier side goes down.\n{obj_heavy}: {a_mass} g, {obj_light}: {b_mass} g.",
             "visual_type": "BalanceScale",
             "visual_params": {"left": {"label": obj_heavy, "mass_g": a_mass},
                               "right": {"label": obj_light, "mass_g": b_mass},
                               "mode": "result"}},
            {"text": (f"{'The ' + obj_heavy if a_mass > b_mass else 'The ' + obj_light} is heavier."),
             "visual_type": "BalanceScale",
             "visual_params": {"left": {"label": obj_heavy, "mass_g": a_mass},
                               "right": {"label": obj_light, "mass_g": b_mass},
                               "mode": "result"}},
        ]
    })

    return slides


def _gen_g3_mg_q2_capacity(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Capacity in liters and milliliters (_3–_5)."""
    slides = []

    cap_ml = rng.randint(200, 900)
    cap_l = rng.randint(1, 5)
    container_a = rng.choice(["glass", "cup", "small bottle"])
    container_b = rng.choice(["jug", "large bottle", "bucket"])

    slides.append({
        "type": "worked_example",
        "title": "Liters and Milliliters",
        "strategy": "capacity_measure",
        "steps": [
            {"text": "We measure capacity in liters (L) and milliliters (mL).\n1 000 mL = 1 L.",
             "visual_type": "CapacityDisplay",
             "visual_params": {"containers": [
                 {"label": container_a, "capacity_mL": cap_ml, "unit": "mL"},
                 {"label": container_b, "capacity_mL": cap_l * 1000, "unit": "L"}
             ]}},
            {"text": (f"A {container_a} holds about {cap_ml} mL.\n"
                      f"A {container_b} holds about {cap_l} L = {cap_l * 1000} mL."),
             "visual_type": "CapacityDisplay",
             "visual_params": {"containers": [
                 {"label": container_a, "capacity_mL": cap_ml, "unit": "mL"},
                 {"label": container_b, "capacity_mL": cap_l * 1000, "unit": "L"}
             ], "show_comparison": True}},
        ]
    })

    # Compare capacities
    cap_x = rng.randint(300, 900)
    cap_y = rng.randint(300, 900)
    while cap_x == cap_y:
        cap_y = rng.randint(300, 900)
    bigger_cap = max(cap_x, cap_y)
    bigger_name = container_a if cap_x > cap_y else container_b

    slides.append({
        "type": "worked_example",
        "title": "Comparing Capacities",
        "strategy": "compare_capacity",
        "steps": [
            {"text": f"Which holds more — {container_a} ({cap_x} mL) or {container_b} ({cap_y} mL)?",
             "visual_type": "CapacityDisplay",
             "visual_params": {"containers": [
                 {"label": container_a, "capacity_mL": cap_x},
                 {"label": container_b, "capacity_mL": cap_y}
             ], "mode": "compare"}},
            {"text": f"$\\goldE{{{bigger_cap}}}$ mL > {min(cap_x, cap_y)} mL.\n{bigger_name.capitalize()} holds more.",
             "visual_type": "CapacityDisplay",
             "visual_params": {"containers": [
                 {"label": container_a, "capacity_mL": cap_x},
                 {"label": container_b, "capacity_mL": cap_y}
             ], "mode": "result", "highlight": bigger_name}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G3 MG Q4 — Symmetry
# ---------------------------------------------------------------------------

def _gen_g3_mg_q4_symmetry(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Two-direction slide and line symmetry (_0–_2)."""
    slides = []

    # Two-direction slide
    slides.append({
        "type": "worked_example",
        "title": "Sliding in Two Directions",
        "strategy": "translation",
        "steps": [
            {"text": "A shape can slide left or right, and up or down.",
             "visual_type": "SymmetryDisplay",
             "visual_params": {"shape": "rectangle", "mode": "slide_2d",
                               "x_steps": 3, "y_steps": 2}},
            {"text": "The shape moves to a new position. Its size and look do not change.",
             "visual_type": None, "visual_params": None},
        ]
    })

    # Line symmetry
    sym_shape = rng.choice(["butterfly", "square", "isosceles_triangle"])
    axis = rng.choice(["vertical", "horizontal"])

    slides.append({
        "type": "worked_example",
        "title": "Line of Symmetry",
        "strategy": "symmetry",
        "steps": [
            {"text": f"Does this shape have a line of symmetry?",
             "visual_type": "SymmetryDisplay",
             "visual_params": {"shape": sym_shape, "mode": "show_shape"}},
            {"text": f"Fold along the line. Both halves match exactly.",
             "visual_type": "SymmetryDisplay",
             "visual_params": {"shape": sym_shape, "mode": "show_axis", "axis": axis}},
            {"text": f"The {axis} line is the line of symmetry.",
             "visual_type": "SymmetryDisplay",
             "visual_params": {"shape": sym_shape, "mode": "show_axis", "axis": axis, "highlight": True}},
        ]
    })

    # Complete a symmetric figure
    slides.append({
        "type": "worked_example",
        "title": "Completing a Symmetric Figure",
        "strategy": "symmetry_completion",
        "steps": [
            {"text": "Here is half of a symmetric shape.",
             "visual_type": "SymmetryDisplay",
             "visual_params": {"shape": "half_figure", "mode": "incomplete"}},
            {"text": "Mirror the other half across the line of symmetry.",
             "visual_type": "SymmetryDisplay",
             "visual_params": {"shape": "half_figure", "mode": "complete"}},
            {"text": "Both halves are equal — the shape is symmetric.",
             "visual_type": "SymmetryDisplay",
             "visual_params": {"shape": "half_figure", "mode": "complete", "highlight": True}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# G3 DP Q3 — Bar Graphs and Probability
# ---------------------------------------------------------------------------

def _gen_g3_dp_q3_bar_graphs(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Collect data, bar graphs horizontal and vertical, interpret (_0–_3)."""
    slides = []

    if interest_ctx:
        categories = rng.sample(interest_ctx["objects"], min(4, len(interest_ctx["objects"])))
    else:
        categories = ["reading", "sports", "music", "art"]
    values = [rng.randint(2, 12) for _ in categories]
    data = [{"label": cat, "value": val} for cat, val in zip(categories, values)]
    most = max(data, key=lambda x: x["value"])
    least = min(data, key=lambda x: x["value"])

    slides.append({
        "type": "worked_example",
        "title": "Reading a Bar Graph",
        "strategy": "bar_graph",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": "A bar graph uses bars to show data.\nThe longer the bar, the bigger the number.",
             "visual_type": "BarGraph",
             "visual_params": {"data": data, "orientation": "vertical",
                               "x_label": "Category", "y_label": "Students"}},
            {"text": f"{most['label'].capitalize()} has the most: $\\goldE{{{most['value']}}}$ students.",
             "visual_type": "BarGraph",
             "visual_params": {"data": data, "orientation": "vertical",
                               "highlight": most["label"]}},
            {"text": f"{least['label'].capitalize()} has the least: {least['value']} students.",
             "visual_type": "BarGraph",
             "visual_params": {"data": data, "orientation": "vertical",
                               "highlight": least["label"]}},
        ]
    })

    # Horizontal bar graph
    slides.append({
        "type": "worked_example",
        "title": "Horizontal Bar Graph",
        "strategy": "bar_graph",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": "The same data can be shown with horizontal bars.",
             "visual_type": "BarGraph",
             "visual_params": {"data": data, "orientation": "horizontal",
                               "x_label": "Students", "y_label": "Category"}},
            {"text": "Longer bar = bigger number. Same data, different look.",
             "visual_type": "BarGraph",
             "visual_params": {"data": data, "orientation": "horizontal"}},
        ]
    })

    return slides


def _gen_g3_dp_q3_probability(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Probability: likely, unlikely, certain, impossible (_4)."""
    slides = []

    # Generate random bag contents
    red_count = rng.randint(3, 5)
    blue_count = rng.randint(1, 2)

    slides.append({
        "type": "worked_example",
        "title": "Will It Happen?",
        "strategy": "probability",
        "steps": [
            {"text": "Some things will always happen. Some things will never happen.\nSome things might happen.",
             "visual_type": "ProbabilityBag",
             "visual_params": {"items": [{"color": "red", "count": red_count}, {"color": "blue", "count": blue_count}], "show_counts": False}},
            {"text": "CERTAIN: the sun will rise tomorrow.\nIMPOSSIBLE: a cow can fly.\nLIKELY: it will rain this week.",
             "visual_type": "ProbabilityBag",
             "visual_params": {"items": [{"color": "red", "count": red_count}, {"color": "blue", "count": blue_count}], "show_counts": False}},
            {"text": "We describe how likely something is using these words:\ncertain, more likely, equally likely, less likely, impossible.",
             "visual_type": "ProbabilityBag",
             "visual_params": {"items": [{"color": "red", "count": red_count}, {"color": "blue", "count": blue_count}], "show_counts": True}},
        ]
    })

    # Experiment — coin flip
    slides.append({
        "type": "worked_example",
        "title": "Heads or Tails?",
        "strategy": "probability_experiment",
        "steps": [
            {"text": "Flip a coin. It can land on heads or tails.",
             "visual_type": "CoinDisplay",
             "visual_params": {"show_both": True}},
            {"text": "Heads and tails are equally likely — each has the same chance.",
             "visual_type": "CoinDisplay",
             "visual_params": {"show_both": True}},
        ]
    })

    # Bag experiment
    slides.append({
        "type": "worked_example",
        "title": "Picking from a Bag",
        "strategy": "probability_bag",
        "steps": [
            {"text": f"A bag has {red_count} red balls and {blue_count} blue ball{'s' if blue_count > 1 else ''}.\nIf you pick one without looking, which color are you more likely to get?",
             "visual_type": "ProbabilityBag",
             "visual_params": {"items": [{"color": "red", "count": red_count}, {"color": "blue", "count": blue_count}], "show_counts": True}},
            {"text": f"There are more red balls ({red_count}) than blue balls ({blue_count}).\nRed is MORE LIKELY.",
             "visual_type": "ProbabilityBag",
             "visual_params": {"items": [{"color": "red", "count": red_count}, {"color": "blue", "count": blue_count}], "highlight": "red", "show_counts": True}},
            {"text": f"Blue is LESS LIKELY because there are fewer blue balls.\nRed: {red_count}  |  Blue: {blue_count}",
             "visual_type": "ProbabilityBag",
             "visual_params": {"items": [{"color": "red", "count": red_count}, {"color": "blue", "count": blue_count}], "highlight": "blue", "show_counts": True}},
        ]
    })

    return slides


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register():
    """Register all G3 node groups into MINI_LESSON_GROUPS and _INTRODUCTIONS."""
    from backend.app.intro_gen.generator import MINI_LESSON_GROUPS
    from backend.app.intro_gen import _INTRODUCTIONS

    # G3 NA Q1
    MINI_LESSON_GROUPS["g3_na_q1"] = {
        "node_label": "Grade 3 - Numbers to 10 000 & Rounding",
        "grade": 3,
        "groups": [
            {
                "title": "Numbers to 10 000",
                "node_key": "g3_na_q1",
                "competencies": ["mat_g3_na_q1_0", "mat_g3_na_q1_1",
                                  "mat_g3_na_q1_2", "mat_g3_na_q1_3"],
                "vocab_terms": ["ten thousand", "ten-thousands place"],
                "generator": _gen_g3_na_q1_numbers,
            },
            {
                "title": "Rounding",
                "node_key": "g3_na_q1",
                "competencies": ["mat_g3_na_q1_4"],
                "vocab_terms": ["round", "nearest ten", "nearest hundred", "nearest thousand"],
                "generator": _gen_g3_na_q1_rounding,
            },
            {
                "title": "Comparing and Ordering to 10 000",
                "node_key": "g3_na_q1",
                "competencies": ["mat_g3_na_q1_5", "mat_g3_na_q1_6"],
                "vocab_terms": [],
                "generator": _gen_g3_na_q1_comparing,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g3_na_q1::Numbers to 10 000": (
            "You can count to 1 000.\n"
            "Now let's go even further — all the way to 10 000.\n"
            "A 4-digit number has a new place: the thousands place."
        ),
        "g3_na_q1::Rounding": (
            "Exact numbers are useful. But sometimes we just need an easy number.\n"
            "Rounding gives us the nearest ten, hundred, or thousand.\n"
            "Let's see which direction to round."
        ),
        "g3_na_q1::Comparing and Ordering to 10 000": (
            "You can compare numbers.\n"
            "Now let's use the symbols >, <, and = with big numbers.\n"
            "Start from the left — the biggest place value."
        ),
    })

    # G3 NA Q2
    MINI_LESSON_GROUPS["g3_na_q2"] = {
        "node_label": "Grade 3 - Money, Add/Subtract to 10 000 & Order of Operations",
        "grade": 3,
        "groups": [
            {
                "title": "Money Notation",
                "node_key": "g3_na_q2",
                "competencies": ["mat_g3_na_q2_0"],
                "vocab_terms": [],
                "generator": _gen_g3_na_q2_money,
            },
            {
                "title": "Addition and Subtraction to 10 000",
                "node_key": "g3_na_q2",
                "competencies": ["mat_g3_na_q2_1", "mat_g3_na_q2_2",
                                  "mat_g3_na_q2_3", "mat_g3_na_q2_4",
                                  "mat_g3_na_q2_5", "mat_g3_na_q2_7"],
                "vocab_terms": [],
                "generator": _gen_g3_na_q2_add_subtract,
            },
            {
                "title": "Order of Operations",
                "node_key": "g3_na_q2",
                "competencies": ["mat_g3_na_q2_6"],
                "vocab_terms": ["order of operations"],
                "generator": _gen_g3_na_q2_order_ops,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g3_na_q2::Money Notation": (
            "100 centavos = 1 peso.\n"
            "There are different ways to write the same amount of money.\n"
            "Let's learn the symbols used in the Philippines."
        ),
        "g3_na_q2::Addition and Subtraction to 10 000": (
            "You can add and subtract up to 1 000.\n"
            "Now let's work with numbers up to 10 000.\n"
            "Estimating first helps us check our answer."
        ),
        "g3_na_q2::Order of Operations": (
            "When there are multiple operations in one calculation, what do we do first?\n"
            "There is a rule — and brackets tell us to go first."
        ),
    })

    # G3 NA Q3
    MINI_LESSON_GROUPS["g3_na_q3"] = {
        "node_label": "Grade 3 - Multiplication (6-9) & Patterns",
        "grade": 3,
        "groups": [
            {
                "title": "Multiplying with 6, 7, 8, and 9",
                "node_key": "g3_na_q3",
                "competencies": ["mat_g3_na_q3_0", "mat_g3_na_q3_1",
                                  "mat_g3_na_q3_2", "mat_g3_na_q3_3", "mat_g3_na_q3_4"],
                "vocab_terms": [],
                "generator": _gen_g3_na_q3_multiplication,
            },
            {
                "title": "Patterns with Missing Terms",
                "node_key": "g3_na_q3",
                "competencies": ["mat_g3_na_q3_5", "mat_g3_na_q3_6"],
                "vocab_terms": ["missing term"],
                "generator": _gen_g3_na_q3_patterns,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g3_na_q3::Multiplying with 6, 7, 8, and 9": (
            "Times tables help us multiply quickly.\n"
            "Now let's complete the set: 6, 7, 8, and 9.\n"
            "We can also multiply bigger numbers."
        ),
        "g3_na_q3::Patterns with Missing Terms": (
            "Patterns can grow or shrink by a rule.\n"
            "Some patterns mix repeating and increasing parts.\n"
            "Can you find what is missing?"
        ),
    })

    # G3 NA Q4
    MINI_LESSON_GROUPS["g3_na_q4"] = {
        "node_label": "Grade 3 - Division with Remainder & Fractions",
        "grade": 3,
        "groups": [
            {
                "title": "Division with Remainder",
                "node_key": "g3_na_q4",
                "competencies": ["mat_g3_na_q4_0", "mat_g3_na_q4_1", "mat_g3_na_q4_2",
                                  "mat_g3_na_q4_3", "mat_g3_na_q4_4", "mat_g3_na_q4_5"],
                "vocab_terms": ["remainder"],
                "generator": _gen_g3_na_q4_division,
            },
            {
                "title": "Improper Fractions",
                "node_key": "g3_na_q4",
                "competencies": ["mat_g3_na_q4_6", "mat_g3_na_q4_7"],
                "vocab_terms": ["improper fraction"],
                "generator": _gen_g3_na_q4_fractions,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g3_na_q4::Division with Remainder": (
            "Division splits a number into equal groups.\n"
            "Now let's divide using bigger tables — 6, 7, 8, and 9.\n"
            "Sometimes things do not divide evenly. What is left over?"
        ),
        "g3_na_q4::Improper Fractions": (
            "Fractions show parts of a whole.\n"
            "What if the numerator is bigger than the denominator?\n"
            "That means we have more than one whole."
        ),
    })

    # G3 MG Q1
    MINI_LESSON_GROUPS["g3_mg_q1"] = {
        "node_label": "Grade 3 - Area & Geometric Lines",
        "grade": 3,
        "groups": [
            {
                "title": "Area",
                "node_key": "g3_mg_q1",
                "competencies": ["mat_g3_mg_q1_0", "mat_g3_mg_q1_1",
                                  "mat_g3_mg_q1_2", "mat_g3_mg_q1_3"],
                "vocab_terms": ["area", "square centimeter", "sq. cm"],
                "generator": _gen_g3_mg_q1_area,
            },
            {
                "title": "Lines and Points",
                "node_key": "g3_mg_q1",
                "competencies": ["mat_g3_mg_q1_4", "mat_g3_mg_q1_5", "mat_g3_mg_q1_6"],
                "vocab_terms": ["point", "line", "line segment", "ray",
                                "parallel", "perpendicular", "intersecting"],
                "generator": _gen_g3_mg_q1_lines,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g3_mg_q1::Area": (
            "You can find the perimeter — the distance around a shape.\n"
            "Now let's find the area — the space inside a shape.\n"
            "We count square units to measure area."
        ),
        "g3_mg_q1::Lines and Points": (
            "Shapes have sides and corners.\n"
            "Now let's look at the building blocks: points, lines, and rays.\n"
            "Lines can be parallel, perpendicular, or intersecting."
        ),
    })

    # G3 MG Q2
    MINI_LESSON_GROUPS["g3_mg_q2"] = {
        "node_label": "Grade 3 - Mass and Capacity",
        "grade": 3,
        "groups": [
            {
                "title": "Mass",
                "node_key": "g3_mg_q2",
                "competencies": ["mat_g3_mg_q2_0", "mat_g3_mg_q2_1", "mat_g3_mg_q2_2"],
                "vocab_terms": ["mass", "gram", "kilogram", "g", "kg", "balance scale"],
                "generator": _gen_g3_mg_q2_mass,
            },
            {
                "title": "Capacity",
                "node_key": "g3_mg_q2",
                "competencies": ["mat_g3_mg_q2_3", "mat_g3_mg_q2_4", "mat_g3_mg_q2_5"],
                "vocab_terms": ["capacity", "liter", "milliliter", "L", "mL"],
                "generator": _gen_g3_mg_q2_capacity,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g3_mg_q2::Mass": (
            "You can measure length.\n"
            "Now let's measure how heavy something is — its mass.\n"
            "We use grams for light things and kilograms for heavy things."
        ),
        "g3_mg_q2::Capacity": (
            "Mass tells how heavy something is.\n"
            "Now let's measure how much liquid a container holds.\n"
            "That is called capacity."
        ),
    })

    # G3 MG Q4
    MINI_LESSON_GROUPS["g3_mg_q4"] = {
        "node_label": "Grade 3 - Slides and Symmetry",
        "grade": 3,
        "groups": [
            {
                "title": "Slides and Symmetry",
                "node_key": "g3_mg_q4",
                "competencies": ["mat_g3_mg_q4_0", "mat_g3_mg_q4_1", "mat_g3_mg_q4_2"],
                "vocab_terms": ["symmetry", "line of symmetry"],
                "generator": _gen_g3_mg_q4_symmetry,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g3_mg_q4::Slides and Symmetry": (
            "Sliding moves a shape without turning it.\n"
            "Now let's slide in two directions at once.\n"
            "We will also look at shapes that have a perfect mirror line."
        ),
    })

    # G3 DP Q3
    MINI_LESSON_GROUPS["g3_dp_q3"] = {
        "node_label": "Grade 3 - Bar Graphs and Probability",
        "grade": 3,
        "groups": [
            {
                "title": "Bar Graphs",
                "node_key": "g3_dp_q3",
                "competencies": ["mat_g3_dp_q3_0", "mat_g3_dp_q3_1",
                                  "mat_g3_dp_q3_2", "mat_g3_dp_q3_3"],
                "vocab_terms": ["outcome", "bar graph", "axis"],
                "generator": _gen_g3_dp_q3_bar_graphs,
            },
            {
                "title": "Probability",
                "node_key": "g3_dp_q3",
                "competencies": ["mat_g3_dp_q3_4"],
                "vocab_terms": ["equally likely", "more likely", "less likely", "certain", "impossible"],
                "generator": _gen_g3_dp_q3_probability,
            },
        ]
    }
    _INTRODUCTIONS.update({
        "g3_dp_q3::Bar Graphs": (
            "Pictographs use pictures to show data.\n"
            "Now let's use bars to show data.\n"
            "A bar graph makes it easy to compare numbers at a glance."
        ),
        "g3_dp_q3::Probability": (
            "Some things will definitely happen. Some things never will.\n"
            "Most things are somewhere in between.\n"
            "Let's learn words for describing how likely something is."
        ),
    })
