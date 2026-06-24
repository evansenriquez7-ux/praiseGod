"""
DNA: Geometric Lines (Measurement & Geometry)

Covers MATATAG grade 3 lines competencies, plus G1-MG-Q4 rotation.
  G3: points, lines, line segments, rays; parallel / intersecting / perpendicular lines
  G1-MG-Q4: half/quarter turns, clockwise/counter-clockwise rotation

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
        required_concept="geometric_lines",
        label="gp_parallel_perp",
        description="Confused parallel and perpendicular lines.",
    ),
    ErrorPattern(
        formula="None",
        required_concept="geometric_lines",
        label="gp_wrong_prop",
        description="Identified incorrect property of a line type (e.g., called a ray a line segment).",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {
    "number_difficulty": "continuous",
}


# ─── static item pool ─────────────────────────────────────────────────────────
_ITEM_POOL: List[Dict[str, Any]] = [
    # ── point / line / segment / ray ───────────────────────────────────────────
    {
        "question": "What do we call an exact location in space with no length or width?",
        "answer": "point",
        "distractors": ["line", "ray", "line segment"],
        "concept_type": "point_line_segment_ray",
        "task_type": "identify_name",
        "grade_min": 3,
    },
    {
        "question": "What figure has two endpoints and a definite length?",
        "answer": "line segment",
        "distractors": ["line", "ray", "point"],
        "concept_type": "point_line_segment_ray",
        "task_type": "identify_name",
        "grade_min": 3,
    },
    {
        "question": "What figure has one endpoint and extends forever in one direction?",
        "answer": "ray",
        "distractors": ["line", "line segment", "point"],
        "concept_type": "point_line_segment_ray",
        "task_type": "identify_name",
        "grade_min": 3,
    },
    {
        "question": "What figure has no endpoints and extends forever in both directions?",
        "answer": "line",
        "distractors": ["ray", "line segment", "point"],
        "concept_type": "point_line_segment_ray",
        "task_type": "identify_name",
        "grade_min": 3,
    },
    {
        "question": "How many endpoints does a line segment have?",
        "answer": "2",
        "distractors": ["0", "1", "3"],
        "concept_type": "point_line_segment_ray",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    {
        "question": "How many endpoints does a ray have?",
        "answer": "1",
        "distractors": ["0", "2", "3"],
        "concept_type": "point_line_segment_ray",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    {
        "question": "How many endpoints does a line have?",
        "answer": "0",
        "distractors": ["1", "2", "infinite"],
        "concept_type": "point_line_segment_ray",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    {
        "question": "Which figure can be measured because it has a definite length?",
        "answer": "line segment",
        "distractors": ["line", "ray", "plane"],
        "concept_type": "point_line_segment_ray",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    # ── parallel / intersecting / perpendicular ────────────────────────────────
    {
        "question": "Two lines that never meet, no matter how far they extend, are called ___.",
        "answer": "parallel lines",
        "distractors": ["perpendicular lines", "intersecting lines", "rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "identify_name",
        "grade_min": 3,
    },
    {
        "question": "Two lines that cross at exactly one point are called ___.",
        "answer": "intersecting lines",
        "distractors": ["parallel lines", "perpendicular lines", "rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "identify_name",
        "grade_min": 3,
    },
    {
        "question": "Two lines that meet at a right angle (90°) are called ___.",
        "answer": "perpendicular lines",
        "distractors": ["parallel lines", "intersecting lines", "line segments"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "identify_name",
        "grade_min": 3,
    },
    {
        "question": "The edges of a ruler's two long sides are an example of what type of lines?",
        "answer": "parallel lines",
        "distractors": ["perpendicular lines", "intersecting lines", "rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    {
        "question": "The corner of a square shows which type of lines meeting?",
        "answer": "perpendicular lines",
        "distractors": ["parallel lines", "intersecting lines", "line segments"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    {
        "question": "Do parallel lines ever intersect?",
        "answer": "No, they never intersect.",
        "distractors": [
            "Yes, they intersect at one point.",
            "Yes, they intersect at a right angle.",
            "Only if they are line segments.",
        ],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    {
        "question": "Are all perpendicular lines also intersecting lines?",
        "answer": "Yes",
        "distractors": ["No", "Only sometimes", "Only if they are rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    # ── rotation turns (G1-MG-Q4) ─────────────────────────────────────────────
    {
        "question": "A shape is turned a half turn clockwise. How many degrees is that?",
        "answer": "180°",
        "distractors": ["90°", "270°", "360°"],
        "concept_type": "rotation_turns",
        "task_type": "identify_property",
        "grade_min": 1,
    },
    {
        "question": "A shape is turned a quarter turn. How many degrees is that?",
        "answer": "90°",
        "distractors": ["45°", "180°", "360°"],
        "concept_type": "rotation_turns",
        "task_type": "identify_property",
        "grade_min": 1,
    },
    {
        "question": "A shape is turned a full turn. How many degrees is that?",
        "answer": "360°",
        "distractors": ["90°", "180°", "270°"],
        "concept_type": "rotation_turns",
        "task_type": "identify_property",
        "grade_min": 1,
    },
    {
        "question": "If you turn a shape clockwise a quarter turn, which direction does it move?",
        "answer": "to the right",
        "distractors": ["to the left", "upward", "downward"],
        "concept_type": "rotation_turns",
        "task_type": "apply_rotation",
        "grade_min": 1,
    },
    {
        "question": "A square is turned half a turn counter-clockwise. What does it look like now?",
        "answer": "It looks the same as before.",
        "distractors": [
            "It now looks like a diamond.",
            "It is flipped upside down.",
            "One side is now longer.",
        ],
        "concept_type": "rotation_turns",
        "task_type": "apply_rotation",
        "grade_min": 1,
    },
    {
        "question": "How many quarter turns equal one full turn?",
        "answer": "4",
        "distractors": ["2", "3", "6"],
        "concept_type": "rotation_turns",
        "task_type": "identify_property",
        "grade_min": 1,
    },
    {
        "question": "How many half turns equal one full turn?",
        "answer": "2",
        "distractors": ["3", "4", "1"],
        "concept_type": "rotation_turns",
        "task_type": "identify_property",
        "grade_min": 1,
    },
    {
        "question": "A shape pointing right is given a quarter turn counter-clockwise. Where does it point now?",
        "answer": "upward",
        "distractors": ["downward", "to the left", "to the right"],
        "concept_type": "rotation_turns",
        "task_type": "apply_rotation",
        "grade_min": 1,
    },
    {
        "question": "Clockwise rotation is the same direction as ___.",
        "answer": "the hands of a clock moving",
        "distractors": [
            "the sun rising in the east",
            "counter-clockwise",
            "a straight line",
        ],
        "concept_type": "rotation_turns",
        "task_type": "identify_name",
        "grade_min": 1,
    },
    {
        "question": "A shape is turned three quarter turns clockwise. This is the same as how many quarter turns counter-clockwise?",
        "answer": "1",
        "distractors": ["2", "3", "4"],
        "concept_type": "rotation_turns",
        "task_type": "apply_rotation",
        "grade_min": 1,
    },
    # extra G3 items to reach 30+
    {
        "question": "A street crossing where roads meet at right angles shows which line relationship?",
        "answer": "perpendicular lines",
        "distractors": ["parallel lines", "intersecting lines", "rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    {
        "question": "Train tracks that run side by side without meeting are an example of ___.",
        "answer": "parallel lines",
        "distractors": ["perpendicular lines", "intersecting lines", "segments"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    {
        "question": "A figure starts at point A and passes through point B, then continues forever past B. What is it?",
        "answer": "ray",
        "distractors": ["line", "line segment", "point"],
        "concept_type": "point_line_segment_ray",
        "task_type": "identify_name",
        "grade_min": 3,
    },
    {
        "question": "Which of these can be measured with a ruler?",
        "answer": "line segment",
        "distractors": ["line", "ray", "point"],
        "concept_type": "point_line_segment_ray",
        "task_type": "identify_property",
        "grade_min": 3,
    },
    {
        "question": "Two intersecting lines that do NOT form a right angle are called ___.",
        "answer": "intersecting lines (not perpendicular)",
        "distractors": ["parallel lines", "perpendicular lines", "rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "identify_name",
        "grade_min": 3,
    },
]


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """Sample one item from the static pool filtered by grade and difficulty profile."""
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    concept_type = profile.get("concept_type", "point_line_segment_ray")
    task_type    = profile.get("task_type", "identify_name")

    candidates = [
        item for item in _ITEM_POOL
        if item["grade_min"] <= grade
        and item["concept_type"] == concept_type
        and item["task_type"] == task_type
    ]
    if not candidates:
        candidates = [
            item for item in _ITEM_POOL
            if item["grade_min"] <= grade and item["concept_type"] == concept_type
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
    concept_type = values.get("concept_type", "point_line_segment_ray")
    if concept_type == "rotation_turns":
        return [
            "A quarter turn = 90°. A half turn = 180°. A full turn = 360°.",
            "Clockwise follows the direction of clock hands.",
            "Counter-clockwise is the opposite direction.",
        ]
    if concept_type == "parallel_intersecting_perpendicular":
        return [
            "Parallel lines never meet — they stay the same distance apart.",
            "Intersecting lines cross at one point.",
            "Perpendicular lines intersect at exactly a right angle (90°).",
        ]
    return [
        "A point is a dot — no length, no width.",
        "A line segment has two endpoints and a measurable length.",
        "A ray has one endpoint and goes on forever in one direction.",
        "A line has no endpoints — it goes on forever in both directions.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

GEOMETRIC_LINES_DNA = DNA(
    concept="geometric_lines",
    dna_type="static_bank",
    answer_formula=None,
    param_bounds={
        "g1": {},
        "g3": {},
    },
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "categorize"],
    requires_context=False,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
