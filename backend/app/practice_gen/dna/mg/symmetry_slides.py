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
_DIFFICULTY_AXES: Dict[str, List[str]] = {
    }


# ─── static item pool ─────────────────────────────────────────────────────────
_ITEM_POOL: List[Dict[str, Any]] = [
    # ── slide / translation ────────────────────────────────────────────────────
    {
        "question": "A shape moves 3 spaces to the right without turning or flipping. What is this called?",
        "answer": "slide (translation)",
        "distractors": ["flip (reflection)", "turn (rotation)", "stretch"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "When a shape slides, does its size or shape change?",
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
        "question": "A triangle slides 4 spaces down. Which direction did it move?",
        "answer": "downward",
        "distractors": ["upward", "to the right", "to the left"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
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
        "question": "After a slide, the shape looks exactly the same — only its position changed. True or false?",
        "answer": "True",
        "distractors": ["False", "Only sometimes true", "Only for squares"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    {
        "question": "Which word means the same as 'slide' in geometry?",
        "answer": "translation",
        "distractors": ["rotation", "reflection", "dilation"],
        "concept": "slide_translation",
        "directions": "one_direction",
        "grade_min": 2,
    },
    # ── line symmetry ──────────────────────────────────────────────────────────
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
        "distractors": [
            "horizontal (left and right)",
            "diagonal",
            "It has no line of symmetry.",
        ],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "The letter 'B' has a line of symmetry. In which direction does it run?",
        "answer": "horizontal (left and right)",
        "distractors": [
            "vertical (up and down)",
            "diagonal",
            "It has no line of symmetry.",
        ],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "Does a scalene triangle (all sides different) have a line of symmetry?",
        "answer": "No",
        "distractors": ["Yes, one line", "Yes, two lines", "Yes, three lines"],
        "concept": "line_symmetry",
        "directions": "one_direction",
        "grade_min": 3,
    },
    # ── complete_symmetric_figure ──────────────────────────────────────────────
    {
        "question": "Half of a shape is shown. The line of symmetry is vertical. To complete the shape, what do you do?",
        "answer": "Draw the mirror image on the other side of the line.",
        "distractors": [
            "Draw a copy directly below the shape.",
            "Rotate the half shape 90°.",
            "Slide the shape to the right.",
        ],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "A symmetric figure has a horizontal line of symmetry. If the top half has 3 squares, how many squares are in the bottom half?",
        "answer": "3",
        "distractors": ["6", "2", "4"],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
    {
        "question": "When completing a symmetric figure, the two halves must be ___.",
        "answer": "mirror images of each other",
        "distractors": [
            "identical in position",
            "different sizes",
            "rotated copies",
        ],
        "concept": "complete_symmetric_figure",
        "directions": "one_direction",
        "grade_min": 3,
    },
]


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """Sample one item from the static pool filtered by grade and difficulty profile."""
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
        candidates = [item for item in _ITEM_POOL if item["grade_min"] <= grade]
    if not candidates:
        candidates = _ITEM_POOL

    return dict(rng.choice(candidates))


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
        "g2": {},
        "g3": {},
    },
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "shape_board"],
    requires_context=False,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
