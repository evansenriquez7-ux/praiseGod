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
VOCAB_SIDES    = VocabGated(requires_vocab="side",    preferred="sides",    fallback="straight edges")
VOCAB_CORNERS  = VocabGated(requires_vocab="corner",  preferred="corners",  fallback="corners")
VOCAB_VERTICES = VocabGated(requires_vocab="vertices", preferred="vertices", fallback="corners")


# ─── static item pool ─────────────────────────────────────────────────────────
# Each item: {question, answer, distractors, shape_set, task_type, orientation, grade_min}
_ITEM_POOL: List[Dict[str, Any]] = [
    # ── G1: basic_triangles_rectangles_squares ─────────────────────────────────
    # ── identify_name (mat_g1_mg_q1_0: triangles, rectangles, squares of different size and orientation) ──
    {
        "question": "A party hat is shaped with 3 straight edges. What 2D shape is it?",
        "answer": "triangle",
        "distractors": ["rectangle", "square", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A flat floor tile has 4 equal straight edges. What shape is the tile?",
        "answer": "square",
        "distractors": ["triangle", "rectangle", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A classroom chalkboard has 4 straight edges and opposite edges are equal. What shape is the chalkboard?",
        "answer": "rectangle",
        "distractors": ["triangle", "square", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A small flat shape with 3 straight edges is shown. What shape is it?",
        "answer": "triangle",
        "distractors": ["rectangle", "square", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A large flat shape with 4 equal straight edges is shown. What shape is it?",
        "answer": "square",
        "distractors": ["triangle", "rectangle", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A slice of pizza with 3 straight edges is turned sideways. What shape is it?",
        "answer": "triangle",
        "distractors": ["square", "rectangle", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "rotated",
        "grade_min": 1,
    },
    {
        "question": "A square tile is tilted like a diamond. What shape is the tile?",
        "answer": "square",
        "distractors": ["triangle", "rectangle", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "rotated",
        "grade_min": 1,
    },
    {
        "question": "A small triangular sign is turned upside down. What shape is it?",
        "answer": "triangle",
        "distractors": ["rectangle", "square", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "rotated",
        "grade_min": 1,
    },
    {
        "question": "A tall doorway has 4 straight edges and is standing upright. What shape is it?",
        "answer": "rectangle",
        "distractors": ["triangle", "square", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "rotated",
        "grade_min": 1,
    },
    {
        "question": "A large square picture frame is tilted on one of its tips. What shape is the frame?",
        "answer": "square",
        "distractors": ["triangle", "rectangle", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "identify_name",
        "orientation": "rotated",
        "grade_min": 1,
    },

    # ── count_sides_corners ──
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
    {
        "question": "A triangle is turned at an angle. How many sides does it still have?",
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

    # ── compare_shapes (mat_g1_mg_q1_1: compare & distinguish according to sides and corners) ──
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
        "distractors": ["triangle", "they are different", "neither"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compare_shapes",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A tilted square and a flat rectangle: do they have the same number of corners?",
        "answer": "Yes, both have 4 corners.",
        "distractors": ["No, the square has more.", "No, the rectangle has more.", "Neither has corners."],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compare_shapes",
        "orientation": "rotated",
        "grade_min": 1,
    },

    # ── compose_decompose (mat_g1_mg_q1_2: compose and decompose triangles, squares, and rectangles) ──
    {
        "question": "Two triangles are placed together, matching their longest straight edges. What shape do they form?",
        "answer": "rectangle",
        "distractors": ["square", "triangle", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A rectangle is cut into two equal pieces down the middle. What two shapes are made?",
        "answer": "two rectangles",
        "distractors": ["two triangles", "two squares", "one triangle and one square"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A square is cut on a slant, from one corner to the opposite corner. What two shapes are made?",
        "answer": "two triangles",
        "distractors": ["two rectangles", "two squares", "one triangle and one square"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "Two identical squares are placed side by side. What shape do they form?",
        "answer": "rectangle",
        "distractors": ["triangle", "square", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "Two identical triangles are joined along their matching straight edges to make a 4-sided shape with equal sides. What shape is formed?",
        "answer": "square",
        "distractors": ["rectangle", "triangle", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "A long rectangle is cut across its width into two equal squares. What two shapes are made?",
        "answer": "two squares",
        "distractors": ["two triangles", "two rectangles", "one triangle and one square"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 1,
    },
    {
        "question": "Two identical triangles are rotated and joined along their matching sides. What shape do they form?",
        "answer": "rectangle",
        "distractors": ["square", "triangle", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "rotated",
        "grade_min": 1,
    },
    {
        "question": "A square is rotated and cut from corner to corner along a slant. What two shapes are produced?",
        "answer": "two triangles",
        "distractors": ["two rectangles", "two squares", "one triangle and one square"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "rotated",
        "grade_min": 1,
    },
    {
        "question": "Two identical triangles are rotated to fit together into a rectangle. What shape is made?",
        "answer": "rectangle",
        "distractors": ["triangle", "square", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "rotated",
        "grade_min": 1,
    },
    {
        "question": "A square is turned sideways and cut on a slant into two pieces. What two shapes are formed?",
        "answer": "two triangles",
        "distractors": ["two squares", "two rectangles", "one triangle and one square"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "rotated",
        "grade_min": 1,
    },
    {
        "question": "Two identical rectangles are turned on their sides and placed together to make a larger square. What shape was formed?",
        "answer": "square",
        "distractors": ["triangle", "rectangle", "none of these"],
        "shape_set": "basic_triangles_rectangles_squares",
        "task_type": "compose_decompose",
        "orientation": "rotated",
        "grade_min": 1,
    },

    # ── G2: extended_with_circles (mat_g2_mg_q1_0) ─────────────────────────────
    # "Represent and describe circles, half circles and quarter circles."
    # ── identify_name ──
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
    {
        "question": "A circle is divided into 2 equal parts. What is each part called?",
        "answer": "half-circle",
        "distractors": ["quarter-circle", "whole circle", "triangle"],
        "shape_set": "extended_with_circles",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "A circle is divided into 4 equal parts. What is each part called?",
        "answer": "quarter-circle",
        "distractors": ["half-circle", "whole circle", "rectangle"],
        "shape_set": "extended_with_circles",
        "task_type": "identify_name",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "A half-circle is turned upside down. What shape is it still?",
        "answer": "half-circle",
        "distractors": ["quarter-circle", "circle", "triangle"],
        "shape_set": "extended_with_circles",
        "task_type": "identify_name",
        "orientation": "rotated",
        "grade_min": 2,
    },
    {
        "question": "A quarter-circle is rotated to face another direction. What shape is it?",
        "answer": "quarter-circle",
        "distractors": ["half-circle", "circle", "square"],
        "shape_set": "extended_with_circles",
        "task_type": "identify_name",
        "orientation": "rotated",
        "grade_min": 2,
    },

    # ── count_sides_corners (describing circles, half circles, quarter circles) ──
    {
        "question": "How many straight sides does a circle have?",
        "answer": "0",
        "distractors": ["1", "2", "4"],
        "shape_set": "extended_with_circles",
        "task_type": "count_sides_corners",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "How many corners does a circle have?",
        "answer": "0",
        "distractors": ["1", "2", "4"],
        "shape_set": "extended_with_circles",
        "task_type": "count_sides_corners",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "How many straight edges does a half-circle have?",
        "answer": "1",
        "distractors": ["0", "2", "3"],
        "shape_set": "extended_with_circles",
        "task_type": "count_sides_corners",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "How many curved edges does a half-circle have?",
        "answer": "1",
        "distractors": ["0", "2", "3"],
        "shape_set": "extended_with_circles",
        "task_type": "count_sides_corners",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "How many straight edges does a quarter-circle have?",
        "answer": "2",
        "distractors": ["1", "0", "3"],
        "shape_set": "extended_with_circles",
        "task_type": "count_sides_corners",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "How many curved edges does a quarter-circle have?",
        "answer": "1",
        "distractors": ["0", "2", "3"],
        "shape_set": "extended_with_circles",
        "task_type": "count_sides_corners",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "A half-circle is tilted sideways. How many straight edges does it have?",
        "answer": "1",
        "distractors": ["0", "2", "3"],
        "shape_set": "extended_with_circles",
        "task_type": "count_sides_corners",
        "orientation": "rotated",
        "grade_min": 2,
    },
    {
        "question": "A quarter-circle is rotated. How many straight edges meet at its corner?",
        "answer": "2",
        "distractors": ["1", "0", "4"],
        "shape_set": "extended_with_circles",
        "task_type": "count_sides_corners",
        "orientation": "rotated",
        "grade_min": 2,
    },

    # ── compare_shapes ──
    {
        "question": "A circle and a square: which one has straight sides?",
        "answer": "square",
        "distractors": ["circle", "both", "neither"],
        "shape_set": "extended_with_circles",
        "task_type": "compare_shapes",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "Which has more straight edges: a half-circle or a quarter-circle?",
        "answer": "quarter-circle",
        "distractors": ["half-circle", "they are equal", "neither"],
        "shape_set": "extended_with_circles",
        "task_type": "compare_shapes",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "Which shape has no corners: a triangle or a circle?",
        "answer": "circle",
        "distractors": ["triangle", "both", "neither"],
        "shape_set": "extended_with_circles",
        "task_type": "compare_shapes",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "Which shape has fewer straight edges: a half-circle or a triangle?",
        "answer": "half-circle",
        "distractors": ["triangle", "they are equal", "neither"],
        "shape_set": "extended_with_circles",
        "task_type": "compare_shapes",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "When comparing a rotated quarter-circle and a rotated half-circle, which has fewer straight edges?",
        "answer": "half-circle",
        "distractors": ["quarter-circle", "they are equal", "neither"],
        "shape_set": "extended_with_circles",
        "task_type": "compare_shapes",
        "orientation": "rotated",
        "grade_min": 2,
    },

    # ── compose_decompose (representing circles, half circles, quarter circles) ──
    {
        "question": "How many half-circles make 1 whole circle?",
        "answer": "2",
        "distractors": ["4", "3", "1"],
        "shape_set": "extended_with_circles",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "How many quarter-circles make 1 whole circle?",
        "answer": "4",
        "distractors": ["2", "3", "8"],
        "shape_set": "extended_with_circles",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "How many quarter-circles make 1 half-circle?",
        "answer": "2",
        "distractors": ["4", "1", "3"],
        "shape_set": "extended_with_circles",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
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
        "question": "Four quarter-circles are put together to make one shape. What shape do they make?",
        "answer": "circle",
        "distractors": ["square", "rectangle", "triangle"],
        "shape_set": "extended_with_circles",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "A circular paper is cut in half. How many half-circles are created?",
        "answer": "2",
        "distractors": ["4", "1", "3"],
        "shape_set": "extended_with_circles",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "A circular paper is cut into quarters. How many quarter-circles are created?",
        "answer": "4",
        "distractors": ["2", "1", "8"],
        "shape_set": "extended_with_circles",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "Two quarter-circles are joined along their flat sides. What shape do they make together?",
        "answer": "half-circle",
        "distractors": ["whole circle", "square", "rectangle"],
        "shape_set": "extended_with_circles",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "Two matching half-circles are rotated and joined along their flat edges. What shape is formed?",
        "answer": "circle",
        "distractors": ["square", "rectangle", "triangle"],
        "shape_set": "extended_with_circles",
        "task_type": "compose_decompose",
        "orientation": "rotated",
        "grade_min": 2,
    },

    # ── G2: composite_figures (mat_g2_mg_q1_1) ─────────────────────────────────
    # "Compose and decompose composite figures made up of squares, rectangles,
    # triangles, circles, half circles, and quarter circles, using cut-outs and square grids."
    # ── Cut-outs ──
    {
        "question": "Using cut-outs, two identical triangles are placed together along their matching edges. What shape can they form?",
        "answer": "rectangle",
        "distractors": ["circle", "half-circle", "quarter-circle"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "Using cut-outs, two half-circles are joined along their flat straight edges. What shape is formed?",
        "answer": "circle",
        "distractors": ["rectangle", "square", "triangle"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "Using cut-outs, four quarter-circles of the same size are joined together. What complete shape do they make?",
        "answer": "circle",
        "distractors": ["square", "rectangle", "triangle"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "Using cut-outs, a square is cut along a slant from one corner to the opposite corner. What two shapes are made?",
        "answer": "two triangles",
        "distractors": ["two rectangles", "two circles", "two squares"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "A composite figure is made of a rectangle with a half-circle attached on top. How many simple shapes form this figure?",
        "answer": "2",
        "distractors": ["1", "3", "4"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "A composite figure is made of a square with a triangle on top. How many simple shapes form this figure?",
        "answer": "2",
        "distractors": ["1", "3", "4"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    # ── Square grids ──
    {
        "question": "On a square grid, a composite figure is made by joining 2 squares of 4 grid units each side by side. What shape is formed?",
        "answer": "rectangle",
        "distractors": ["triangle", "circle", "quarter-circle"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "On a square grid, a 4-by-2 rectangle is cut straight down the middle into two 2-by-2 parts. What shape is each part?",
        "answer": "square",
        "distractors": ["circle", "triangle", "half-circle"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "On a square grid, a composite figure is made of 1 square, 1 half-circle, and 1 rectangle. How many shapes form this composite figure?",
        "answer": "3",
        "distractors": ["1", "2", "4"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "On a square grid, how many 1-by-1 unit squares are needed to compose a 2-by-2 square?",
        "answer": "4",
        "distractors": ["2", "3", "6"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "On a square grid, a composite shape has 1 square, 1 triangle, and 1 rectangle joined together. How many simple shapes were used to compose it?",
        "answer": "3",
        "distractors": ["2", "4", "5"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "standard",
        "grade_min": 2,
    },
    {
        "question": "Using cut-outs, two identical triangles are rotated and placed together. What shape can they form?",
        "answer": "rectangle",
        "distractors": ["circle", "half-circle", "quarter-circle"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "rotated",
        "grade_min": 2,
    },
    {
        "question": "On a square grid, a rotated composite shape is made of a square and a triangle. How many simple shapes make up this figure?",
        "answer": "2",
        "distractors": ["1", "3", "4"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "rotated",
        "grade_min": 2,
    },
    {
        "question": "On a square grid, combining two 2x2 squares side by side forms which shape?",
        "answer": "rectangle",
        "distractors": ["circle", "triangle", "half-circle"],
        "shape_set": "composite_figures",
        "task_type": "compose_decompose",
        "orientation": "rotated",
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

    # Progressively relax filters if too narrow (preserving shape_set and task_type)
    if not candidates:
        candidates = [
            item for item in _ITEM_POOL
            if item["grade_min"] <= grade
            and item["shape_set"] == shape_set
            and item["task_type"] == task_type
        ]
    if not candidates and "task_type" not in profile:
        candidates = [
            item for item in _ITEM_POOL
            if item["grade_min"] <= grade
            and item["shape_set"] == shape_set
        ]
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

    item = dict(rng.choice(candidates))
    item["result"] = item["answer"]
    return item


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    sides_label = "sides" if "side" in cumulative_vocab else "straight edges"
    if "corner" in cumulative_vocab:
        hints = [
            f"Think about the {sides_label} and corners of each shape.",
            f"A triangle has 3 {sides_label} and 3 corners.",
            f"A square has 4 equal {sides_label} and 4 corners.",
            f"A rectangle has 4 {sides_label} (opposite {sides_label} are equal) and 4 corners.",
        ]
        if "circle" in cumulative_vocab:
            hints.append(f"A circle has no straight {sides_label} and no corners.")
        return hints
    hints = [
        f"Look at each shape and its {sides_label}.",
        f"A triangle has 3 {sides_label}.",
        f"A square has 4 equal {sides_label}.",
        f"A rectangle has 4 {sides_label} (opposite {sides_label} are equal).",
    ]
    if "circle" in cumulative_vocab:
        hints.append(f"A circle has no straight {sides_label}.")
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
