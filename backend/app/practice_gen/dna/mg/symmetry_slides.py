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

    # ── slide / translation (Grade 3: two-direction slide) ─────────────────────
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

    # ── line symmetry (Grade 3) ────────────────────────────────────────────────
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

    # ── complete symmetric figure (Grade 3) ───────────────────────────────────
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
