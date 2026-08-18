"""
DNA: Symmetry and Slides (Measurement & Geometry)

Covers MATATAG grades 2–3 symmetry and translation competencies.
  G2: one-direction slide (translation)
  G3: two-direction slide, line symmetry, completing symmetric figures

dna_type="static_bank": generate_params() samples from an inline item pool.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="symmetry_slides",
        label="gp_wrong_prop",
        description="Identified incorrect property: confused a line of symmetry with a slide direction, or vice versa.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {
    "number_difficulty": "continuous",
}


# ─── static item pool ─────────────────────────────────────────────────────────
_ITEM_POOL: List[Dict[str, Any]] = [
    # ── rotation / turn (Grade 1) ─────────────────────────────────────────────
    {
        "question": "An arrow faces UP. It does a quarter turn clockwise. Which direction does it face now?",
        "answer": "right",
        "distractors": ["left", "down", "up"],
        "concept": "rotation",
        "directions": "one_direction",
        "grade_min": 1,
    },
    {
        "question": "An arrow faces UP. It does a half turn. Which direction does it face now?",
        "answer": "down",
        "distractors": ["up", "left", "right"],
        "concept": "rotation",
        "directions": "one_direction",
        "grade_min": 1,
    },
    {
        "question": "An arrow faces UP. It does a quarter turn counter-clockwise. Which direction does it face now?",
        "answer": "left",
        "distractors": ["right", "down", "up"],
        "concept": "rotation",
        "directions": "one_direction",
        "grade_min": 1,
    },
    {
        "question": "Which direction is clockwise?",
        "answer": "the direction clock hands move",
        "distractors": [
            "the opposite direction clock hands move",
            "straight up",
            "to the left",
        ],
        "concept": "rotation",
        "directions": "one_direction",
        "grade_min": 1,
    },
    {
        "question": "An arrow faces DOWN. It does a quarter turn clockwise. Which direction does it face now?",
        "answer": "left",
        "distractors": ["right", "up", "down"],
        "concept": "rotation",
        "directions": "one_direction",
        "grade_min": 1,
    },
    {
        "question": "An arrow faces LEFT. It does a quarter turn clockwise. Which direction does it face now?",
        "answer": "up",
        "distractors": ["down", "right", "left"],
        "concept": "rotation",
        "directions": "one_direction",
        "grade_min": 1,
    },
    {
        "question": "An arrow faces RIGHT. It does a quarter turn counter-clockwise. Which direction does it face now?",
        "answer": "up",
        "distractors": ["down", "left", "right"],
        "concept": "rotation",
        "directions": "one_direction",
        "grade_min": 1,
    },
    {
        "question": "An arrow faces LEFT. It does a half turn. Which direction does it face now?",
        "answer": "right",
        "distractors": ["left", "up", "down"],
        "concept": "rotation",
        "directions": "one_direction",
        "grade_min": 1,
    },
    {
        "question": "An arrow faces RIGHT. It does a half turn. Which direction does it face now?",
        "answer": "left",
        "distractors": ["right", "up", "down"],
        "concept": "rotation",
        "directions": "one_direction",
        "grade_min": 1,
    },

    # ── slide / translation (Grade 2: one-direction multi-step slide - mat_g2_mg_q1_2) ─────
    {
        "question": "A shape slides 2 spaces right, then slides 1 more space right in the same direction without turning. What is this multi-step movement called?",
        "answer": "one-direction multi-step slide (translation)",
        "distractors": ["flip (reflection)", "turn (rotation)", "two-direction slide"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "After a shape undergoes a multi-step slide in one direction, does its size or shape change?",
        "answer": "No, the size and shape stay the same.",
        "distractors": [
            "Yes, it gets bigger.",
            "Yes, it gets smaller.",
            "Yes, it changes shape.",
        ],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "A triangle slides 2 spaces down, then slides 2 more spaces down. In which single direction did the multi-step slide move?",
        "answer": "downward",
        "distractors": ["upward", "to the right", "to the left"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "A shape slides 2 spaces right, then slides 3 more spaces right. How far did it move in all?",
        "answer": "5 spaces to the right",
        "distractors": ["2 spaces to the right", "3 spaces to the right", "6 spaces to the right"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "A shape slides 4 spaces down, then slides 1 more space down. Is this still a one-direction slide?",
        "answer": "Yes, both steps moved the same direction.",
        "distractors": [
            "No, two steps means two directions.",
            "No, this is a turn (rotation).",
            "No, this is a flip (reflection).",
        ],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "After a multi-step slide, the shape looks exactly the same — only its position changed. True or false?",
        "answer": "True",
        "distractors": ["False", "Only sometimes true", "Only for squares"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "A figure undergoes a multi-step slide: 2 spaces up, then 3 more spaces up. What is another mathematical name for a slide?",
        "answer": "translation",
        "distractors": ["rotation", "reflection", "dilation"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "To draw the result of sliding a square 4 spaces to the right in one direction, where should you draw the new square?",
        "answer": "4 spaces to the right of the original square",
        "distractors": ["4 spaces to the left", "4 spaces upward", "in the same place"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "A triangle is drawn at space 2. It undergoes a multi-step slide: 3 spaces right, then 2 more spaces right. At which space should you draw the final triangle?",
        "answer": "space 7",
        "distractors": ["space 5", "space 4", "space 6"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "A circle is at grid mark 1. It is slid 2 marks right, then another 4 marks right in the same direction. At what grid mark will the circle be drawn?",
        "answer": "mark 7",
        "distractors": ["mark 6", "mark 5", "mark 8"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "A rectangle at mark 8 slides 3 spaces left, then slides 2 more spaces left in the same direction. At what mark should the rectangle be drawn?",
        "answer": "mark 3",
        "distractors": ["mark 5", "mark 6", "mark 2"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "To draw a multi-step slide of 2 units down followed by 3 units down in one direction, what is the total distance to draw the shift?",
        "answer": "5 units down",
        "distractors": ["6 units down", "1 unit down", "3 units down"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "A shape starts at position 3. It slides 1 space right, then 4 spaces right. Describe the total slide in one direction.",
        "answer": "5 spaces to the right",
        "distractors": ["4 spaces to the right", "1 space to the right", "3 spaces to the right"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },

    # ── slide / translation (Grade 3: two-direction slide - mat_g3_mg_q4_0) ───
    {
        "question": "A shape moves 2 spaces right AND 3 spaces up. How many directions did it slide?",
        "answer": "2",
        "distractors": ["1", "3", "5"],
        "concept": "slide_translation",
        "directions": "two_directions",
        "grade_min": 3,
    },
    {
        "question": "A shape slides 5 spaces to the left and 2 spaces down. What type of movement is this?",
        "answer": "two-direction slide (translation)",
        "distractors": ["one-direction slide", "flip (reflection)", "turn (rotation)"],
        "concept": "slide_translation",
        "directions": "two_directions",
        "grade_min": 3,
    },
    {
        "question": "A triangle at grid mark (1, 2) slides 3 units to the right and 4 units up. Where is its new position?",
        "answer": "(4, 6)",
        "distractors": ["(3, 4)", "(4, 2)", "(1, 6)"],
        "concept": "slide_translation",
        "directions": "two_directions",
        "grade_min": 3,
    },
    {
        "question": "A shape starts at position (5, 5). It undergoes a two-direction slide: 2 spaces left and 3 spaces down. What is the new position?",
        "answer": "(3, 2)",
        "distractors": ["(7, 8)", "(3, 5)", "(5, 2)"],
        "concept": "slide_translation",
        "directions": "two_directions",
        "grade_min": 3,
    },
    {
        "question": "A circle at grid coordinate (2, 4) slides 5 spaces right and 1 space down. At what grid point will the circle be drawn?",
        "answer": "(7, 3)",
        "distractors": ["(7, 5)", "(2, 3)", "(3, 9)"],
        "concept": "slide_translation",
        "directions": "two_directions",
        "grade_min": 3,
    },
    {
        "question": "To draw the result of a two-direction slide: 3 units right and 2 units down, what should you do to each corner of the shape?",
        "answer": "shift each corner 3 units right and 2 units down",
        "distractors": [
            "shift each corner 3 units left and 2 units up",
            "turn the shape 90 degrees",
            "make each corner 3 times larger",
        ],
        "concept": "slide_translation",
        "directions": "two_directions",
        "grade_min": 3,
    },
    {
        "question": "A figure slides 2 spaces left, then 1 more space left, then 4 spaces up. What is the total movement in the two directions?",
        "answer": "3 spaces left and 4 spaces up",
        "distractors": ["2 spaces left and 4 spaces up", "3 spaces left and 1 space up", "7 spaces left"],
        "concept": "slide_translation",
        "directions": "two_directions",
        "grade_min": 3,
    },
    {
        "question": "A rectangle undergoes a two-direction slide: 4 units right and 2 units up. Does the orientation or shape of the rectangle change?",
        "answer": "No, only its position changes.",
        "distractors": [
            "Yes, it turns upside down.",
            "Yes, it becomes a square.",
            "Yes, it gets smaller.",
        ],
        "concept": "slide_translation",
        "directions": "two_directions",
        "grade_min": 3,
    },
    {
        "question": "A point moves from (1, 1) to (4, 5). How many units right and how many units up did it slide?",
        "answer": "3 units right and 4 units up",
        "distractors": ["4 units right and 5 units up", "1 unit right and 1 unit up", "3 units right and 5 units up"],
        "concept": "slide_translation",
        "directions": "two_directions",
        "grade_min": 3,
    },
    {
        "question": "A star at point (0, 0) slides 4 spaces right, then 3 spaces up. Where should the star be drawn?",
        "answer": "(4, 3)",
        "distractors": ["(3, 4)", "(4, 0)", "(0, 3)"],
        "concept": "slide_translation",
        "directions": "two_directions",
        "grade_min": 3,
    },

    # ── line symmetry (Grade 3 - mat_g3_mg_q4_1) ──────────────────────────────
    {
        "question": "A line of symmetry divides a shape into two ___.",
        "answer": "equal halves that are mirror images",
        "distractors": [
            "unequal parts",
            "halves that are different sizes",
            "triangles",
        ],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "How many lines of symmetry does a square have?",
        "answer": "4",
        "distractors": ["1", "2", "0"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "How many lines of symmetry does a rectangle (non-square) have?",
        "answer": "2",
        "distractors": ["1", "4", "0"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "How many lines of symmetry does an equilateral triangle have?",
        "answer": "3",
        "distractors": ["1", "2", "0"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "How many lines of symmetry does an isosceles triangle (two equal sides) have?",
        "answer": "1",
        "distractors": ["2", "3", "0"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "How many lines of symmetry does a scalene triangle (all sides different) have?",
        "answer": "0",
        "distractors": ["1", "2", "3"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "A circle has how many lines of symmetry?",
        "answer": "Infinite (unlimited)",
        "distractors": ["1", "4", "0"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "The letter 'A' has a line of symmetry. In which direction does it run?",
        "answer": "vertical (up and down)",
        "distractors": ["horizontal (side to side)", "diagonal", "no lines of symmetry"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "The letter 'H' has how many lines of symmetry?",
        "answer": "2",
        "distractors": ["1", "3", "0"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "The letter 'M' has a line of symmetry. In which direction does it run?",
        "answer": "vertical (up and down)",
        "distractors": ["horizontal (side to side)", "diagonal", "no lines of symmetry"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "The letter 'B' has a line of symmetry. In which direction does it run?",
        "answer": "horizontal (side to side)",
        "distractors": ["vertical (up and down)", "diagonal", "no lines of symmetry"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "Which of these shapes has NO line of symmetry?",
        "answer": "a scalene triangle",
        "distractors": ["a square", "a rectangle", "an equilateral triangle"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "If you draw a vertical line down the center of a heart shape, do both sides match?",
        "answer": "Yes, it shows line symmetry.",
        "distractors": [
            "No, the sides are different.",
            "Only if the heart is tilted.",
            "No, hearts have 4 lines of symmetry.",
        ],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },

    # ── complete symmetric figure (Grade 3 - mat_g3_mg_q4_2) ──────────────────
    {
        "question": "To complete a symmetric figure across a vertical line of symmetry, the other half must be ___.",
        "answer": "drawn as a mirror image of the first half",
        "distractors": [
            "drawn upside down",
            "drawn twice as large",
            "drawn as a triangle",
        ],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "A point is 3 grid units to the left of a vertical line of symmetry. Where is its mirror-image point?",
        "answer": "3 grid units to the right of the line",
        "distractors": [
            "3 grid units above the line",
            "6 grid units to the right of the line",
            "on the line itself",
        ],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "If a shape is symmetrical across a line, folding along that line makes both halves match exactly. True or false?",
        "answer": "True",
        "distractors": ["False", "Only for circles", "Only for squares"],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "A point is 4 grid units to the right of a vertical line of symmetry. Where should its matching point be drawn to complete the figure?",
        "answer": "4 grid units to the left of the line",
        "distractors": [
            "4 grid units to the right of the line",
            "2 grid units to the left of the line",
            "on the line of symmetry",
        ],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "A point is 2 grid units above a horizontal line of symmetry. Where must the matching point be drawn to complete the symmetric figure?",
        "answer": "2 grid units below the line of symmetry",
        "distractors": [
            "2 grid units above the line of symmetry",
            "4 grid units below the line of symmetry",
            "2 grid units to the right of the line",
        ],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "One side of a symmetric butterfly drawing has 3 dots on the left wing. How many dots must be drawn on the right wing to complete the figure?",
        "answer": "3 dots in matching positions",
        "distractors": [
            "6 dots in matching positions",
            "1 dot on the wing",
            "0 dots",
        ],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "When completing a symmetric figure on grid paper, each vertex on the second half must be the same distance from the line of symmetry as its partner on the first half. True or false?",
        "answer": "True",
        "distractors": ["False", "Only for rectangles", "Only for circles"],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "A vertex of a polygon is 5 units to the left of a vertical line of symmetry. Where is the corresponding vertex of the completed symmetric polygon?",
        "answer": "5 units to the right of the line",
        "distractors": [
            "5 units to the left of the line",
            "10 units to the right of the line",
            "on the line of symmetry",
        ],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
]


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Sample one item from the static pool filtered by grade, concept, and directions.
    Returns the item dict directly.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    concept    = profile.get("concept", "slide_translation")
    directions = profile.get("directions", "one_direction")

    candidates = [
        item for item in _ITEM_POOL
        if item["grade_min"] <= grade
        and item["concept"] == concept
        and item["directions"] == directions
    ]

    if not candidates:
        candidates = [
            item for item in _ITEM_POOL
            if item["grade_min"] <= grade and item["concept"] == concept
        ]
    if not candidates:
        raise ValueError(
            f"symmetry_slides: no item pool entries for concept={concept!r} "
            f"at grade<={grade} (seed={seed}). This is a content-coverage gap in "
            f"_ITEM_POOL, not a condition to silently substitute a different "
            f"concept's content for."
        )

    item = dict(rng.choice(candidates))
    item["result"] = item["answer"]
    return item


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    concept = values.get("concept", "slide_translation")
    if concept == "slide_translation":
        return [
            "A slide (translation) moves a shape without turning or flipping it.",
            "The shape looks the same — only its position changes.",
            "Count how many spaces it moved in each direction.",
        ]
    if concept == "rotation":
        return [
            "A turn (rotation) spins a shape in place without sliding it.",
            "A quarter turn moves it like 15 minutes on a clock.",
            "A half turn faces it the opposite way.",
        ]
    if concept == "line_symmetry":
        return [
            "A line of symmetry splits a shape into two mirror-image halves.",
            "Fold the shape along the line — both halves should match exactly.",
        ]
    return [
        "Find the line of symmetry first.",
        "Each point on one side has a matching point the same distance on the other side.",
        "Draw the mirror image to complete the figure.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

SYMMETRY_SLIDES_DNA = DNA(
    concept="symmetry_slides",
    dna_type="static_bank",
    answer_formula=None,
    param_bounds={
        "g1": {},
        "g2": {},
        "g3": {},
    },
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "shape_board"],
    requires_context=False,
    visual_home="ShapeBoard",
    difficulty_axes=_DIFFICULTY_AXES,
)
