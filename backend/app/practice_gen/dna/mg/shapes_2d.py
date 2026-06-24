"""
DNA: 2D Shapes (Measurement & Geometry)

Covers MATATAG grades 1–2 2D shape competencies.
  G1: triangle, rectangle, square — identify, count sides/corners, compose/decompose
  G2: adds circles, half-circles, quarter-circles, 3D object faces, slides/translations

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
        required_concept="shapes_2d",
        label="gp_wrong_prop",
        description="Identified an incorrect property of the shape (wrong side or corner count).",
    ),
    ErrorPattern(
        formula="None",
        required_concept="shapes_2d",
        label="gp_parallel_perp",
        description="Confused shape attributes such as parallel vs perpendicular sides.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {
    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_SIDES    = VocabGated(requires_vocab="sides",    preferred="sides",    fallback="straight edges")
VOCAB_CORNERS  = VocabGated(requires_vocab="corners",  preferred="corners",  fallback="points")
VOCAB_VERTICES = VocabGated(requires_vocab="vertices", preferred="vertices", fallback="corners")


# ─── static item pool ─────────────────────────────────────────────────────────
# Each item: {question, answer, distractors, shape_set, task_type, orientation, grade_min}
_ITEM_POOL: List[Dict[str, Any]] = [
    # ── identify_name ──────────────────────────────────────────────────────────
    {
        "question": "What shape has 3 sides and 3 corners?",
        "answer": "triangle",
        "distractors": ["rectangle", "square", "circle"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "What shape has 4 equal sides and 4 corners?",
        "answer": "square",
        "distractors": ["triangle", "rectangle", "circle"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "What shape has 4 sides where opposite sides are equal?",
        "answer": "rectangle",
        "distractors": ["triangle", "square", "circle"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "What shape has no corners and no straight sides?",
        "answer": "circle",
        "distractors": ["triangle", "rectangle", "square"],
        "shape_set": "extended_with_circles",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "A shape is made from exactly half of a circle. What is it called?",
        "answer": "half-circle",
        "distractors": ["quarter-circle", "triangle", "rectangle"],
        "shape_set": "extended_with_circles",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "A shape is made from exactly one quarter of a circle. What is it called?",
        "answer": "quarter-circle",
        "distractors": ["half-circle", "triangle", "square"],
        "shape_set": "extended_with_circles",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 2,
    },
    # ── count_sides_corners ────────────────────────────────────────────────────
    {
        "question": "How many corners does a triangle have?",
        "answer": "3",
        "distractors": ["4", "2", "5"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "count_sides_corners",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "How many sides does a rectangle have?",
        "answer": "4",
        "distractors": ["3", "6", "5"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "count_sides_corners",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "How many sides does a square have?",
        "answer": "4",
        "distractors": ["3", "5", "6"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "count_sides_corners",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "How many corners does a rectangle have?",
        "answer": "4",
        "distractors": ["2", "3", "6"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "count_sides_corners",
        "orientation": "standard",
        "grade_min": 1,
    },
    # ── rotated orientation ────────────────────────────────────────────────────
    {
        "question": "A triangle is tilted on its side. How many sides does it still have?",
        "answer": "3",
        "distractors": ["4", "2", "5"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "count_sides_corners",
        "orientation": "rotated",
        "grade_min": 1,
    },
    {
        "question": "A square is rotated so it looks like a diamond. How many corners does it have?",
        "answer": "4",
        "distractors": ["3", "8", "6"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "count_sides_corners",
        "orientation": "rotated",
        "grade_min": 1,
    },
    # ── compare_shapes ─────────────────────────────────────────────────────────
    {
        "question": "Which shape has more sides — a triangle or a rectangle?",
        "answer": "rectangle",
        "distractors": ["triangle", "they are equal", "neither"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compare_shapes",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "Which shape has fewer corners — a square or a triangle?",
        "answer": "triangle",
        "distractors": ["square", "they are equal", "neither"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compare_shapes",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "Which shape has the same number of sides as a square?",
        "answer": "rectangle",
        "distractors": ["triangle", "circle", "pentagon"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compare_shapes",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A circle and a square: which one has straight sides?",
        "answer": "square",
        "distractors": ["circle", "both", "neither"],
        "shape_set": "extended_with_circles",
        "task_type": "compare_shapes",
        "orientation": "standard",
        "grade_min": 2,
    },
    # ── compose_decompose ──────────────────────────────────────────────────────
    {
        "question": "Two triangles are placed together along their longest side. What shape do they form?",
        "answer": "rectangle",
        "distractors": ["square", "circle", "pentagon"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A rectangle is cut in half along its length. What two shapes are made?",
        "answer": "two squares",
        "distractors": ["two triangles", "two rectangles", "two circles"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A square is cut from one corner to the opposite corner. What two shapes are made?",
        "answer": "two triangles",
        "distractors": ["two rectangles", "two squares", "two circles"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "Two half-circles are put together to make one shape. What shape is formed?",
        "answer": "circle",
        "distractors": ["rectangle", "square", "triangle"],
        "shape_set": "extended_with_circles",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "Four quarter-circles are arranged around a center point. What shape do they make?",
        "answer": "circle",
        "distractors": ["square", "rectangle", "triangle"],
        "shape_set": "extended_with_circles",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    # ── composite figures ──────────────────────────────────────────────────────
    {
        "question": "A figure is made of a rectangle with a triangle on top. How many shapes make up this figure?",
        "answer": "2",
        "distractors": ["1", "3", "4"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
]


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Sample one item from the static pool filtered by grade and difficulty_profile.
    Returns the item dict directly (used as both params and question content).
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    shape_set   = profile.get("shape_set", "basic_triangles_rectangles_squares")
    task_type   = profile.get("task_type", "identify_name")
    orientation = profile.get("orientation", "standard")

    candidates = [
        item for item in _ITEM_POOL
        if item["grade_min"] <= grade
        and item["shape_set"] == shape_set
        and item["task_type"] == task_type
        and item["orientation"] == orientation
    ]

    # Progressively relax filters if too narrow
    if not candidates:
        candidates = [
            item for item in _ITEM_POOL
            if item["grade_min"] <= grade
            and item["task_type"] == task_type
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
    sides_label   = VOCAB_SIDES.resolve(cumulative_vocab)
    corners_label = VOCAB_CORNERS.resolve(cumulative_vocab)
    hints = [
        f"Think about the {sides_label} and {corners_label} of each shape.",
        "A triangle has 3 sides and 3 corners.",
        "A square has 4 equal sides and 4 corners.",
        "A rectangle has 4 sides (opposite sides are equal) and 4 corners.",
        "A circle has no straight sides and no corners.",
    ]
    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

SHAPES_2D_DNA = DNA(
    concept="shapes_2d",
    dna_type="static_bank",
    answer_formula=None,
    param_bounds={
        "g1": {},
        "g2": {},
    },
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "categorize", "shape_board"],
    requires_context=False,
    visual_home="ShapeBoard",
    difficulty_axes=_DIFFICULTY_AXES,
)
