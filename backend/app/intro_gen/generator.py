"""
Intro Content Generator

Produces structured intro slides for MATATAG nodes using:
- Type A: Parameterized Perseus-derived worked examples (dynamic numbers, interest-wrappable)
- Type B: Authored definitions and explanations (constrained by knowledge graph vocab)
"""

import json
import os
import random
from typing import Dict, List, Optional


# --------------------------------------------------------------------------
# Interest Bank Loader
# --------------------------------------------------------------------------

_INTEREST_BANK = None

def _load_interest_bank() -> Dict:
    global _INTEREST_BANK
    if _INTEREST_BANK is not None:
        return _INTEREST_BANK
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "interest_bank.json")
    with open(os.path.abspath(path)) as f:
        _INTEREST_BANK = json.load(f)
    return _INTEREST_BANK


def get_interest_themes(grade: int = None) -> List[Dict]:
    """Return all interest themes. Grade parameter is ignored (kept for API compatibility)."""
    bank = _load_interest_bank()
    themes = []
    for key, theme in bank["interests"].items():
        themes.append({
            "key": key,
            "name": theme["name"],
            "interest_id": theme["interest_id"],
        })
    return sorted(themes, key=lambda t: t["interest_id"])


# --------------------------------------------------------------------------
# Definition Bank (G1 NA Q1 vocabulary)
# --------------------------------------------------------------------------

DEFINITION_BANK = {
    # G1 NA Q1: Counting
    "1 more": {"definition": "the next number when you count up", "example": "1 more than 7 is 8"},
    "1 less": {"definition": "the next number when you count down", "example": "1 less than 7 is 6"},
    # G1 NA Q1: Numerals
    "numeral": {"definition": "a written symbol for a number", "example": "5, 12, and 23 are numerals"},
    # G1 NA Q1: Number line
    "number line": {"definition": "a line with numbers placed in order", "example": None},
    # G1 NA Q1: Compare
    "compare": {"definition": "look at two numbers to find which is bigger or smaller", "example": None},
    # G1 NA Q1: Ordinal positions (the words themselves are the definitions)
    "1st": {"definition": "first — the one at the front", "example": None},
    "2nd": {"definition": "second — the one right after 1st", "example": None},
    "3rd": {"definition": "third — the one right after 2nd", "example": None},
    "4th": {"definition": "fourth — the one right after 3rd", "example": None},
    "5th": {"definition": "fifth — the one right after 4th", "example": None},
    "6th": {"definition": "sixth — the one right after 5th", "example": None},
    "7th": {"definition": "seventh — the one right after 6th", "example": None},
    "8th": {"definition": "eighth — the one right after 7th", "example": None},
    "9th": {"definition": "ninth — the one right after 8th", "example": None},
    "10th": {"definition": "tenth — the one right after 9th", "example": None},
    # G1 NA Q1: Addition
    "addition": {"definition": "putting two groups together to find the total", "example": "3 + 5 = 8"},
    "sum": {"definition": "the answer you get when you add", "example": "the sum of 3 and 5 is 8"},
    # G1 NA Q2: Place value
    "skip counting": {"definition": "counting by jumps — like 2, 4, 6, 8 instead of 1 by 1", "example": None},
    "place value": {"definition": "the value of a digit based on where it sits in a number", "example": "in 35, the 3 is in the tens place"},
    "digit": {"definition": "any of the symbols 0 through 9 used to write numbers", "example": "73 has two digits: 7 and 3"},
    "tens": {"definition": "groups of ten — the second place from the right in a number", "example": "in 34, the 3 means 3 tens"},
    "ones": {"definition": "single units — the first place from the right in a number", "example": "in 34, the 4 means 4 ones"},
    "expanded form": {"definition": "writing a number as tens and ones added together", "example": "34 = 30 + 4"},
    # G1 NA Q3: Subtraction
    "subtraction": {"definition": "taking away one amount from another", "example": "8 - 3 = 5"},
    "difference": {"definition": "the answer you get when you subtract", "example": "the difference between 8 and 3 is 5"},
    "missing number": {"definition": "the unknown value in a number sentence", "example": "3 + ? = 7"},
    "pattern": {"definition": "something that repeats in the same order", "example": "2, 4, 2, 4, 2, 4..."},
    "repeating pattern": {"definition": "a pattern where the same group of things repeats over and over", "example": None},
    # G1 NA Q4: Fractions
    "fraction": {"definition": "a part of a whole thing", "example": "half a pizza is a fraction"},
    "half": {"definition": "one of two equal parts", "example": "cut a shape in half and each piece is the same size"},
    "quarter": {"definition": "one of four equal parts", "example": "a quarter is one piece when you cut something into 4 equal parts"},
    "whole": {"definition": "all of something, with no parts missing", "example": None},
    # G1 NA Q4: Money
    "peso": {"definition": "the main unit of money in the Philippines", "example": None},
    "₱": {"definition": "the symbol for Philippine pesos", "example": "₱10 means ten pesos"},
    "coin": {"definition": "a small round piece of metal used as money", "example": None},
    "bill": {"definition": "a flat piece of paper used as money", "example": None},
    # G1 MG Q1: Shapes
    "triangle": {"definition": "a flat shape with 3 sides and 3 corners", "example": None},
    "rectangle": {"definition": "a flat shape with 4 sides and 4 corners, where opposite sides are equal", "example": None},
    "square": {"definition": "a flat shape with 4 equal sides and 4 corners", "example": None},
    "side": {"definition": "one straight edge of a shape", "example": "a triangle has 3 sides"},
    "corner": {"definition": "the point where two sides of a shape meet", "example": "a square has 4 corners"},
    # G1 MG Q2: Measurement
    "length": {"definition": "how long something is from one end to the other", "example": None},
    "measure": {"definition": "find out how long, heavy, or big something is", "example": None},
    # G1 MG Q4: Turns and time
    "clockwise": {"definition": "turning in the same direction as clock hands move", "example": None},
    "counter-clockwise": {"definition": "turning in the opposite direction of clock hands", "example": None},
    "half turn": {"definition": "turning all the way around to face the opposite direction", "example": None},
    "quarter turn": {"definition": "turning one quarter of the way around", "example": None},
    "hour": {"definition": "a unit of time — there are 24 hours in a day", "example": None},
    "half hour": {"definition": "30 minutes — half of one hour", "example": None},
    "quarter hour": {"definition": "15 minutes — one quarter of an hour", "example": None},
    "analog clock": {"definition": "a clock with hands that point to the numbers", "example": None},
    "calendar": {"definition": "a chart showing all the days and months of the year", "example": None},
    # G1 DP Q3: Data
    "data": {"definition": "information you collect, often as numbers", "example": "how many students like each color"},
    "pictograph": {"definition": "a chart that uses pictures to show data", "example": None},
    "table": {"definition": "a grid of rows and columns used to organise information", "example": None},
    # G2 NA Q1
    "thousand": {"definition": "the number 1 000 — ten hundreds", "example": None},
    "hundreds": {"definition": "groups of one hundred — the third place from the right", "example": "in 345, the 3 means 3 hundreds"},
    "regrouping": {"definition": "trading 10 ones for 1 ten (or 10 tens for 1 hundred) when adding or subtracting", "example": None},
    # G2 NA Q2
    "centavo": {"definition": "a small unit of Philippine money — 100 centavos make 1 peso", "example": None},
    "increasing pattern": {"definition": "a pattern where the numbers or shapes get bigger", "example": "2, 4, 6, 8..."},
    "decreasing pattern": {"definition": "a pattern where the numbers or shapes get smaller", "example": "10, 8, 6, 4..."},
    # G2 NA Q3: Multiplication and division
    "equal groups": {"definition": "groups that all have the same number of things", "example": "3 groups of 4"},
    "multiplication": {"definition": "a quick way to add equal groups", "example": "3 × 4 means 3 groups of 4"},
    "product": {"definition": "the answer you get when you multiply", "example": "the product of 3 and 4 is 12"},
    "division": {"definition": "splitting a total into equal groups", "example": "12 ÷ 3 means split 12 into 3 equal groups"},
    "quotient": {"definition": "the answer you get when you divide", "example": "the quotient of 12 ÷ 3 is 4"},
    "even": {"definition": "a number that can be split into two equal groups with nothing left over", "example": "2, 4, 6, 8 are even"},
    "odd": {"definition": "a number that cannot be split into two equal groups evenly", "example": "1, 3, 5, 7 are odd"},
    # G2 NA Q4: Fractions
    "denominator": {"definition": "the bottom number of a fraction — how many equal parts in the whole", "example": "in 1/4, the denominator is 4"},
    "numerator": {"definition": "the top number of a fraction — how many parts you have", "example": "in 3/4, the numerator is 3"},
    "similar fractions": {"definition": "fractions that have the same denominator", "example": "1/4 and 3/4 are similar fractions"},
    # G2 MG Q1: Shapes
    "circle": {"definition": "a perfectly round flat shape with no sides or corners", "example": None},
    "slide": {"definition": "moving a shape to a new position without turning or flipping it", "example": None},
    "translation": {"definition": "another word for slide — moving a shape without changing it", "example": None},
    # G2 MG Q2: Standard measurement
    "centimeter": {"definition": "a small unit of length — about the width of your fingernail", "example": None},
    "meter": {"definition": "a unit of length equal to 100 centimeters", "example": None},
    "cm": {"definition": "short for centimeter", "example": None},
    "m": {"definition": "short for meter", "example": None},
    "ruler": {"definition": "a straight tool used to measure length", "example": None},
    "estimate": {"definition": "make a careful guess at a measurement without using a tool", "example": None},
    # G2 MG Q4: Time and shapes
    "minute": {"definition": "a unit of time — there are 60 minutes in one hour", "example": None},
    "a.m.": {"definition": "the hours from midnight to noon", "example": "school starts at 8 a.m."},
    "p.m.": {"definition": "the hours from noon to midnight", "example": "lunch is at 12 p.m."},
    "elapsed time": {"definition": "the amount of time that passes from start to finish", "example": None},
    "solid figure": {"definition": "a 3D shape that takes up space, like a box or a ball", "example": None},
    "perimeter": {"definition": "the total distance around the outside of a shape", "example": None},
    # G2 DP Q3
    "scale": {"definition": "in a pictograph, how many things each picture stands for", "example": "if the scale is 2, each picture stands for 2"},
    # G3 NA Q1
    "ten thousand": {"definition": "the number 10 000 — ten thousands", "example": None},
    "ten-thousands place": {"definition": "the fifth place from the right in a number", "example": "in 12 345, the 1 is in the ten-thousands place"},
    "round": {"definition": "change a number to the nearest ten, hundred, or thousand to make it easier to work with", "example": "37 rounded to the nearest ten is 40"},
    "nearest ten": {"definition": "the multiple of 10 closest to a given number", "example": "the nearest ten to 37 is 40"},
    "nearest hundred": {"definition": "the multiple of 100 closest to a given number", "example": "the nearest hundred to 347 is 300"},
    "nearest thousand": {"definition": "the multiple of 1000 closest to a given number", "example": None},
    # G3 NA Q2
    "order of operations": {"definition": "the agreed order for doing calculations — work left to right, doing all operations in the correct sequence", "example": None},
    # G3 NA Q3
    "missing term": {"definition": "the unknown value missing from a pattern", "example": "2, 4, ?, 8 — the missing term is 6"},
    # G3 NA Q4
    "remainder": {"definition": "the amount left over after dividing as evenly as possible", "example": "11 ÷ 3 = 3 remainder 2"},
    "improper fraction": {"definition": "a fraction where the numerator is bigger than or equal to the denominator", "example": "5/3 is an improper fraction"},
    # G3 MG Q1: Geometry
    "area": {"definition": "the amount of space inside a flat shape, measured in square units", "example": None},
    "square centimeter": {"definition": "a square that is 1 cm on each side, used to measure area", "example": None},
    "sq. cm": {"definition": "short for square centimeter", "example": None},
    "point": {"definition": "an exact location in space, shown as a dot", "example": None},
    "line": {"definition": "a straight path that goes on forever in both directions", "example": None},
    "line segment": {"definition": "a straight path between two endpoints", "example": None},
    "ray": {"definition": "a straight path that starts at one point and goes on forever in one direction", "example": None},
    "parallel": {"definition": "lines that are always the same distance apart and never meet", "example": None},
    "perpendicular": {"definition": "lines that meet at a right angle (a square corner)", "example": None},
    "intersecting": {"definition": "lines that cross each other at a point", "example": None},
    # G3 MG Q2: Mass and capacity
    "mass": {"definition": "how much matter is in an object — measured in grams or kilograms", "example": None},
    "gram": {"definition": "a small unit of mass", "example": "a paperclip weighs about 1 gram"},
    "kilogram": {"definition": "a unit of mass equal to 1000 grams", "example": None},
    "g": {"definition": "short for gram", "example": None},
    "kg": {"definition": "short for kilogram", "example": None},
    "balance scale": {"definition": "a tool that compares the mass of two objects by balancing them", "example": None},
    "capacity": {"definition": "how much liquid a container can hold", "example": None},
    "liter": {"definition": "a unit for measuring how much liquid something holds", "example": None},
    "milliliter": {"definition": "a very small unit of liquid — 1000 milliliters make 1 liter", "example": None},
    "L": {"definition": "short for liter", "example": None},
    "mL": {"definition": "short for milliliter", "example": None},
    # G3 MG Q4: Symmetry
    "symmetry": {"definition": "when both halves of a shape look exactly the same", "example": None},
    "line of symmetry": {"definition": "the line that divides a shape into two matching halves", "example": None},
    # G3 DP Q3
    "outcome": {"definition": "one possible result of an experiment", "example": "when you flip a coin, heads is one outcome"},
    "bar graph": {"definition": "a chart that uses bars of different lengths to show data", "example": None},
    "axis": {"definition": "one of the lines along the edge of a graph that shows the scale", "example": None},
    "equally likely": {"definition": "two outcomes that have the same chance of happening", "example": "heads and tails are equally likely"},
    "more likely": {"definition": "has a greater chance of happening", "example": None},
    "less likely": {"definition": "has a smaller chance of happening", "example": None},
    "certain": {"definition": "will definitely happen", "example": None},
    "impossible": {"definition": "cannot happen at all", "example": None},
}


# --------------------------------------------------------------------------
# Mini-Lesson Groupings for G1_NA_Q1
# --------------------------------------------------------------------------

MINI_LESSON_GROUPS = {
    "g1_na_q1": {
        "node_label": "Grade 1 - Numbers, Counting & Addition",
        "grade": 1,
        "groups": [
            {
                "title": "Counting & Numerals",
                "node_key": "g1_na_q1",
                "competencies": ["mat_g1_na_q1_0", "mat_g1_na_q1_1", "mat_g1_na_q1_2"],
                "vocab_terms": ["1 more", "1 less", "numeral", "number line"],
                "generator": None,  # set after function definitions below
            },
            {
                "title": "Comparing & Ordering",
                "node_key": "g1_na_q1",
                "competencies": ["mat_g1_na_q1_3", "mat_g1_na_q1_4", "mat_g1_na_q1_5"],
                "vocab_terms": ["compare", "1st", "2nd", "3rd", "4th", "5th",
                                 "6th", "7th", "8th", "9th", "10th"],
                "generator": None,
            },
            {
                "title": "Breaking Apart Numbers",
                "node_key": "g1_na_q1",
                "competencies": ["mat_g1_na_q1_6"],
                "vocab_terms": [],
                "generator": None,
            },
            {
                "title": "Addition",
                "node_key": "g1_na_q1",
                "competencies": ["mat_g1_na_q1_7", "mat_g1_na_q1_8", "mat_g1_na_q1_9"],
                "vocab_terms": ["addition", "sum"],
                "generator": None,
            },
        ]
    }
}


# --------------------------------------------------------------------------
# Worked Example Templates (Parameterized from Perseus)
# --------------------------------------------------------------------------

def _generate_counting_examples(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Generate worked examples for Counting & Numerals mini-lesson."""
    slides = []

    # Strategy 1: Number line - "1 more than" (_0)
    a = rng.randint(2, 50)
    result = a + 1
    slides.append({
        "type": "worked_example",
        "title": "Finding 1 More (Number Line)",
        "strategy": "number_line",
        "steps": [
            {"text": f"Let's find 1 more than $\\blueE{{{a}}}$.", "visual_type": "NumberLine", "visual_params": {"start": max(0, a-3), "end": a+5, "markers": [a]}},
            {"text": f"Start at $\\blueE{{{a}}}$. Count up 1.", "visual_type": "NumberLine", "visual_params": {"start": max(0, a-3), "end": a+5, "hop_from": a, "hop_by": 1}},
            {"text": f"We land on $\\goldE{{{result}}}$. So 1 more than {a} is $\\goldE{{{result}}}$.", "visual_type": "NumberLine", "visual_params": {"start": max(0, a-3), "end": a+5, "highlight": result}},
        ]
    })

    # Strategy 2: Number line - "1 less than" (_0)
    b = rng.randint(3, 50)
    result_b = b - 1
    slides.append({
        "type": "worked_example",
        "title": "Finding 1 Less (Number Line)",
        "strategy": "number_line",
        "steps": [
            {"text": f"Let's find 1 less than $\\blueE{{{b}}}$.", "visual_type": "NumberLine", "visual_params": {"start": max(0, b-5), "end": b+3, "markers": [b]}},
            {"text": f"Start at $\\blueE{{{b}}}$. Count down 1.", "visual_type": "NumberLine", "visual_params": {"start": max(0, b-5), "end": b+3, "hop_from": b, "hop_by": -1}},
            {"text": f"We land on $\\goldE{{{result_b}}}$. So 1 less than {b} is $\\goldE{{{result_b}}}$.", "visual_type": "NumberLine", "visual_params": {"start": max(0, b-5), "end": b+3, "highlight": result_b}},
        ]
    })

    # Strategy 3: Numeral on number line — addresses competency _1 (read/write numerals)
    # Uses only cumulative_vocab at this point: number, numeral, 1 more, 1 less, number line
    n = rng.randint(12, 40)
    slides.append({
        "type": "worked_example",
        "title": "Reading a Numeral",
        "strategy": "numeral_recognition",
        "steps": [
            {"text": f"The numeral $\\blueE{{{n}}}$ is a symbol for the number {n}.",
             "visual_type": "NumberLine",
             "visual_params": {"start": max(0, n - 4), "end": n + 4, "markers": []}},
            {"text": f"Find $\\blueE{{{n}}}$ on the number line.",
             "visual_type": "NumberLine",
             "visual_params": {"start": max(0, n - 4), "end": n + 4, "highlight": n}},
            {"text": f"1 more than $\\blueE{{{n}}}$ is $\\goldE{{{n + 1}}}$.\n1 less than $\\blueE{{{n}}}$ is $\\goldE{{{n - 1}}}$.",
             "visual_type": "NumberLine",
             "visual_params": {"start": max(0, n - 4), "end": n + 4, "highlight": n, "markers": [n - 1, n + 1]}},
        ]
    })

    # Strategy 4: Counting objects — addresses competency _2 (represent numbers)
    count = rng.randint(5, 15)
    obj_name = "objects"
    if interest_ctx:
        obj_name = rng.choice(interest_ctx["objects"])
    slides.append({
        "type": "worked_example",
        "title": "Counting Objects",
        "strategy": "groups_of_objects",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": f"How many {obj_name} are there?", "visual_type": "ObjectGrid", "visual_params": {"object": obj_name, "count": count, "numbered": False}},
            {"text": f"We count each one: 1, 2, 3... {count}.\nThe last number we say is $\\goldE{{{count}}}$.", "visual_type": "ObjectGrid", "visual_params": {"object": obj_name, "count": count, "numbered": True}},
            {"text": f"There are $\\goldE{{{count}}}$ {obj_name}.", "visual_type": None, "visual_params": None},
        ]
    })

    return slides


def _generate_comparing_examples(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Generate worked examples for Comparing & Ordering mini-lesson."""
    slides = []

    # Strategy 1: Number line comparison
    # Numbers up to 20, matching competency. Uses only "compare" and "number line"
    # which are both in cumulative_vocab at this point. No tens/ones language.
    a = rng.randint(1, 20)
    b = rng.randint(1, 20)
    while b == a:
        b = rng.randint(1, 20)
    comparison = "more than" if a > b else "less than"

    slides.append({
        "type": "worked_example",
        "title": "Comparing Two Numbers",
        "strategy": "number_line_comparison",
        "steps": [
            {"text": f"Compare $\\blueE{{{a}}}$ and $\\maroonD{{{b}}}$.",
             "visual_type": "NumberLine",
             "visual_params": {"start": 0, "end": 20, "markers": [a, b]}},
            {"text": f"Find each number on the number line.\nThe number further to the right is bigger.",
             "visual_type": "NumberLine",
             "visual_params": {"start": 0, "end": 20, "markers": [a, b]}},
            {"text": f"$\\blueE{{{a}}}$ is {comparison} $\\maroonD{{{b}}}$.",
             "visual_type": None,
             "visual_params": None},
        ]
    })

    # Strategy 2: Ordering numbers
    nums = sorted(rng.sample(range(1, 20), 4))
    slides.append({
        "type": "worked_example",
        "title": "Ordering Numbers",
        "strategy": "ordering",
        "steps": [
            {"text": f"Put these numbers in order from smallest to largest:\n\n${nums[2]}, {nums[0]}, {nums[3]}, {nums[1]}$",
             "visual_type": "NumberCards",
             "visual_params": {"numbers": [nums[2], nums[0], nums[3], nums[1]], "ordered": False}},
            {"text": f"Find the smallest: $\\goldE{{{nums[0]}}}$.\nThen: $\\goldE{{{nums[1]}}}$, $\\goldE{{{nums[2]}}}$, $\\goldE{{{nums[3]}}}$.",
             "visual_type": "NumberCards",
             "visual_params": {"numbers": nums, "ordered": True}},
            {"text": f"In order: ${nums[0]}, {nums[1]}, {nums[2]}, {nums[3]}$",
             "visual_type": None,
             "visual_params": None},
        ]
    })

    # Strategy 3: Position in a line (ordinal words)
    items = ["cat", "dog", "bird", "fish", "frog"]
    if interest_ctx:
        items = rng.sample(interest_ctx["objects"], min(5, len(interest_ctx["objects"])))
    ordinals = ["1st", "2nd", "3rd", "4th", "5th"]
    slides.append({
        "type": "worked_example",
        "title": "Where Things Are in a Line",
        "strategy": "ordinal_position",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": f"These are in a line:\n{', '.join(items[:5])}",
             "visual_type": "OrderedLine",
             "visual_params": {"items": items[:5], "highlighted": None}},
            {"text": f"The {ordinals[0]} is **{items[0]}**.\nThe {ordinals[1]} is **{items[1]}**.\nThe {ordinals[2]} is **{items[2]}**.",
             "visual_type": "OrderedLine",
             "visual_params": {"items": items[:5], "highlighted": [0, 1, 2]}},
            {"text": f"1st, 2nd, 3rd... these words tell where something is in a line.",
             "visual_type": None,
             "visual_params": None},
        ]
    })

    return slides


def _generate_decompose_examples(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Generate worked examples for Breaking Apart Numbers mini-lesson."""
    slides = []

    # Strategy 1: Ten frame — finding the other part of 10
    # Framed purely as "what goes with X to fill the frame" — no + notation
    a = rng.randint(1, 9)
    complement = 10 - a
    slides.append({
        "type": "worked_example",
        "title": "Parts of 10",
        "strategy": "ten_frame",
        "steps": [
            {"text": f"Here is a ten frame. Fill $\\blueE{{{a}}}$ dots.",
             "visual_type": "TenFrame",
             "visual_params": {"filled": a, "total": 10, "highlight_empty": False}},
            {"text": f"How many spaces are empty?",
             "visual_type": "TenFrame",
             "visual_params": {"filled": a, "total": 10, "highlight_empty": True, "empty_count": complement}},
            {"text": f"$\\blueE{{{a}}}$ and $\\redD{{{complement}}}$ make 10.",
             "visual_type": "TenFrame",
             "visual_params": {"filled": a, "total": 10, "highlight_empty": True, "empty_count": complement}},
        ]
    })

    # Strategy 2: Number bonds — show two different ways to break apart the same number
    target = rng.randint(5, 10)
    part1 = rng.randint(1, target - 1)
    part2 = target - part1
    # Pick a second distinct split
    alt1 = rng.randint(1, target - 1)
    while alt1 == part1 or alt1 == part2:
        alt1 = rng.randint(1, target - 1)
        if target <= 2:
            alt1 = part1  # fallback for tiny targets
            break
    alt2 = target - alt1

    slides.append({
        "type": "worked_example",
        "title": "Breaking Apart a Number",
        "strategy": "number_bonds",
        "steps": [
            {"text": f"Let's look at $\\blueE{{{target}}}$.",
             "visual_type": "NumberBond",
             "visual_params": {"whole": target, "parts": [None, None]}},
            {"text": f"One way: $\\blueE{{{target}}}$ is $\\greenD{{{part1}}}$ and $\\maroonD{{{part2}}}$.",
             "visual_type": "NumberBond",
             "visual_params": {"whole": target, "parts": [part1, part2]}},
            {"text": f"Another way: $\\blueE{{{target}}}$ is $\\greenD{{{alt1}}}$ and $\\maroonD{{{alt2}}}$.",
             "visual_type": "NumberBond",
             "visual_params": {"whole": target, "parts": [alt1, alt2]}},
            {"text": f"$\\blueE{{{target}}}$ can be broken apart in many ways.",
             "visual_type": None,
             "visual_params": None},
        ]
    })

    return slides


def _generate_addition_examples(rng: random.Random, interest_ctx: Optional[Dict]) -> List[Dict]:
    """Generate worked examples for Addition mini-lesson."""
    slides = []

    # Strategy 1: Number line (from Perseus "Add within 20" items 1-6)
    a = rng.randint(2, 9)
    b = rng.randint(1, min(9, 20 - a))
    result = a + b
    slides.append({
        "type": "worked_example",
        "title": "Addition on a Number Line",
        "strategy": "number_line",
        "steps": [
            {"text": f"Let's add $\\blueE{{{a}}} + \\maroonD{{{b}}}$.", "visual_type": "NumberLine", "visual_params": {"start": 0, "end": 20, "markers": []}},
            {"text": f"First, jump to $\\blueE{{{a}}}$ on the number line.", "visual_type": "NumberLine", "visual_params": {"start": 0, "end": 20, "hop_to": a}},
            {"text": f"Next, jump $\\maroonD{{{b}}}$ more.", "visual_type": "NumberLine", "visual_params": {"start": 0, "end": 20, "hop_from": a, "hop_by": b}},
            {"text": f"The jumps end at $\\goldE{{{result}}}$.\n\n$\\blueE{{{a}}} + \\maroonD{{{b}}} = \\goldE{{{result}}}$", "visual_type": "NumberLine", "visual_params": {"start": 0, "end": 20, "highlight": result}},
        ]
    })

    # Strategy 2: Ten frame (from Perseus "Add within 20" items 7-11)
    c = rng.randint(4, 9)
    d = rng.randint(1, min(9, 20 - c))
    result_cd = c + d
    slides.append({
        "type": "worked_example",
        "title": "Addition with a Ten Frame",
        "strategy": "ten_frame",
        "steps": [
            {"text": f"Let's add $\\blueE{{{c}}} + \\maroonD{{{d}}}$ using a ten frame.", "visual_type": "TenFrame", "visual_params": {"filled": 0, "total": 10, "highlight_empty": False}},
            {"text": f"First, show $\\blueE{{{c}}}$ dots.", "visual_type": "TenFrame", "visual_params": {"filled": c, "total": 10, "color": "blue"}},
            {"text": f"Next, add $\\maroonD{{{d}}}$ more dots.", "visual_type": "TenFrame", "visual_params": {"filled": result_cd, "total": max(10, result_cd), "added": d, "color_split": c}},
            {"text": f"Count all the dots: $\\goldE{{{result_cd}}}$.\n\n$\\blueE{{{c}}} + \\maroonD{{{d}}} = \\goldE{{{result_cd}}}$", "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 3: Groups of objects - interest wrappable (from Perseus items 16-20)
    e = rng.randint(3, 10)
    f_val = rng.randint(2, min(8, 20 - e))
    result_ef = e + f_val
    obj_name = "stars"
    actor_name = ""
    if interest_ctx:
        obj_name = rng.choice(interest_ctx["objects"])
        actor_name = rng.choice(interest_ctx["actors"])
        step1_text = f"{actor_name} has $\\blueE{{{e}}}$ {obj_name}."
        step2_text = f"{actor_name} gets $\\maroonD{{{f_val}}}$ more {obj_name}."
        step3_text = f"Now {actor_name} has $\\goldE{{{result_ef}}}$ {obj_name} total."
    else:
        step1_text = f"First, show $\\blueE{{{e}}}$ {obj_name}."
        step2_text = f"Next, add $\\maroonD{{{f_val}}}$ more {obj_name}."
        step3_text = f"Now there are $\\goldE{{{result_ef}}}$ {obj_name} total."

    slides.append({
        "type": "worked_example",
        "title": "Addition with Groups",
        "strategy": "groups_of_objects",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": step1_text, "visual_type": "ObjectGroup", "visual_params": {"object": obj_name, "count": e}},
            {"text": step2_text, "visual_type": "ObjectGroup", "visual_params": {"object": obj_name, "count": e, "adding": f_val}},
            {"text": step3_text + f"\n\n$\\blueE{{{e}}} + \\maroonD{{{f_val}}} = \\goldE{{{result_ef}}}$", "visual_type": "ObjectGroup", "visual_params": {"object": obj_name, "count": result_ef}},
        ]
    })

    # Strategy 4: Adding zero — identity property (_8)
    # Apply interest wrapping when available for consistency with groups-of-objects slide
    g = rng.randint(1, 20)
    if interest_ctx:
        obj_name_g = rng.choice(interest_ctx["objects"])
        actor_name_g = rng.choice(interest_ctx["actors"])
        step1_text_g = f"{actor_name_g} has $\\blueE{{{g}}}$ {obj_name_g}. {actor_name_g} gets 0 more."
        step2_text_g = f"Nothing was added. {actor_name_g} still has $\\blueE{{{g}}}$ {obj_name_g}."
        step3_obj = obj_name_g
    else:
        step1_text_g = f"What is $\\blueE{{{g}}} + 0$?"
        step2_text_g = f"We add 0. Nothing is added."
        step3_obj = "dots"
    slides.append({
        "type": "worked_example",
        "title": "Adding Zero",
        "strategy": "identity_property",
        "interest_wrapped": interest_ctx is not None,
        "steps": [
            {"text": step1_text_g, "visual_type": "ObjectGroup", "visual_params": {"object": step3_obj, "count": g}},
            {"text": step2_text_g, "visual_type": "ObjectGroup", "visual_params": {"object": step3_obj, "count": g, "adding": 0}},
            {"text": f"$\\blueE{{{g}}} + 0 = \\goldE{{{g}}}$\n\nAdding zero keeps the number the same.", "visual_type": None, "visual_params": None},
        ]
    })

    # Strategy 5: Flipping the order — commutative property (_8)
    # Step 1 poses the problem WITHOUT revealing the answer.
    # Answer is revealed only after both orderings are shown.
    h = rng.randint(1, 8)
    i = rng.randint(h+1, 9)
    result_hi = h + i
    slides.append({
        "type": "worked_example",
        "title": "Flipping the Order",
        "strategy": "commutative_property",
        "steps": [
            {"text": f"Let's add $\\blueE{{{h}}}$ and $\\maroonD{{{i}}}$.",
             "visual_type": "ObjectGroup",
             "visual_params": {"groups": [{"count": h, "color": "blue"}, {"count": i, "color": "maroon"}]}},
            {"text": f"$\\blueE{{{h}}} + \\maroonD{{{i}}} = \\goldE{{{result_hi}}}$\n\nNow flip the order: $\\maroonD{{{i}}}$ and $\\blueE{{{h}}}$.",
             "visual_type": "ObjectGroup",
             "visual_params": {"groups": [{"count": i, "color": "maroon"}, {"count": h, "color": "blue"}]}},
            {"text": f"$\\maroonD{{{i}}} + \\blueE{{{h}}} = \\goldE{{{result_hi}}}$\n\nSame answer! The order does not change the sum.",
             "visual_type": None,
             "visual_params": None},
        ]
    })

    return slides


# --------------------------------------------------------------------------
# Main Generator
# --------------------------------------------------------------------------

def _wire_g1_na_q1():
    """Bind the G1_NA_Q1 generator functions after they are defined."""
    g = MINI_LESSON_GROUPS["g1_na_q1"]["groups"]
    g[0]["generator"] = _generate_counting_examples
    g[1]["generator"] = _generate_comparing_examples
    g[2]["generator"] = _generate_decompose_examples
    g[3]["generator"] = _generate_addition_examples

_wire_g1_na_q1()


def get_available_intro_nodes() -> List[Dict]:
    """Return list of nodes that have intro content available."""
    nodes = []
    for node_key, data in MINI_LESSON_GROUPS.items():
        nodes.append({
            "node_key": node_key,
            "label": data["node_label"],
            "grade": data["grade"],
            "mini_lesson_count": len(data["groups"]),
        })
    return nodes


def generate_intro_content(
    node_key: str,
    interest_key: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict:
    """
    Generate full intro content for a node.
    
    Returns structured mini-lessons with slides (explanations, definitions, worked examples).
    """
    if node_key not in MINI_LESSON_GROUPS:
        return {"error": f"No intro content available for node: {node_key}"}

    node_data = MINI_LESSON_GROUPS[node_key]
    seed = seed or random.randint(1, 999999)
    rng = random.Random(seed)

    # Load interest context if specified
    interest_ctx = None
    if interest_key:
        bank = _load_interest_bank()
        if interest_key in bank["interests"]:
            interest_ctx = bank["interests"][interest_key]

    # Build mini-lessons
    mini_lessons = []

    for group in node_data["groups"]:
        slides = []

        # Type B: Introduction slide
        introduction = _get_introduction(group["title"], group.get("node_key", node_key))
        slides.append({
            "type": "introduction",
            "content": introduction,
        })

        # Type B: Definitions slide
        terms = []
        for term_name in group["vocab_terms"]:
            if term_name in DEFINITION_BANK:
                entry = DEFINITION_BANK[term_name]
                terms.append({
                    "term": term_name,
                    "definition": entry["definition"],
                    "example": entry.get("example"),
                })
        if terms:
            slides.append({
                "type": "definitions",
                "terms": terms,
            })

        # Type A: Worked examples — use generator function stored directly on group
        generator_fn = group.get("generator")
        if generator_fn:
            worked_examples = generator_fn(rng, interest_ctx)
            slides.extend(worked_examples)

        mini_lessons.append({
            "title": group["title"],
            "competencies": group["competencies"],
            "slides": slides,
        })

    return {
        "node_key": node_key,
        "node_label": node_data["node_label"],
        "grade": node_data["grade"],
        "seed": seed,
        "interest_applied": interest_key,
        "can_skip": True,
        "mini_lessons": mini_lessons,
    }


def _get_introduction(group_title: str, node_key: str = "") -> str:
    """Return Type B introduction text for a mini-lesson group.

    Introduction text motivates and connects to prior learning.
    It MUST NOT define vocabulary terms — that is the definitions slide's job.

    Keyed by "node_key::group_title" for uniqueness across nodes.
    Falls back to group_title alone for backward compatibility.
    """
    # Import all node introductions (populated by grade-specific modules)
    from backend.app.intro_gen import _INTRODUCTIONS  # noqa: F401 — populated at import time

    key_full = f"{node_key}::{group_title}"
    return _INTRODUCTIONS.get(key_full) or _INTRODUCTIONS.get(group_title, "")
