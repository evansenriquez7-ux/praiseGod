"""
DNA: Geometric Lines (Measurement & Geometry)

Covers MATATAG grade 2-3 lines/surfaces competencies.
  G2 (mat_g2_mg_q4_3): straight vs. curved lines; flat vs. curved surfaces
    of 3-dimensional objects (solid figures).
  G3: points, lines, line segments, rays; parallel / intersecting /
    perpendicular lines.

dna_type="static_bank": generate_params() samples from an inline item pool.

Every node bound to this DNA (registry.py's geometric_lines branch of
_parse_competency_bounds) sets an explicit concept_type bound, and
generate_params() never silently substitutes a different concept_type's
items when the requested one has no grade-eligible candidates — it raises
instead (AGENTS.md rule #3, no graceful fallbacks). A prior version fell
through to whatever concept_type happened to have grade-eligible items,
which silently served G1 rotation-degree trivia to G2 students on the
straight/curved-lines node; see docs/pgen_hardening.md judgment findings.
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
    # ── straight vs. curved lines / flat vs. curved surfaces (G2-MG-Q4) ───────
    {
        "question": "It never bends or changes direction. Is it a straight line or a curved line?",
        "answer": "straight line",
        "distractors": ["curved line", "flat surface", "curved surface"],
        "concept_type": "straight_curved",
        "task_type": "identify_name",
        "grade_min": 2,
    },
    {
        "question": "It bends smoothly and changes direction. Is it a straight line or a curved line?",
        "answer": "curved line",
        "distractors": ["straight line", "flat surface", "curved surface"],
        "concept_type": "straight_curved",
        "task_type": "identify_name",
        "grade_min": 2,
    },
    {
        "question": "The edge of a ruler never bends. Is it a straight line or a curved line?",
        "answer": "straight line",
        "distractors": ["curved line", "flat surface", "curved surface"],
        "concept_type": "straight_curved",
        "task_type": "identify_property",
        "grade_min": 2,
    },
    {
        "question": "The rim of a circle bends all the way around. Is it a straight line or a curved line?",
        "answer": "curved line",
        "distractors": ["straight line", "flat surface", "curved surface"],
        "concept_type": "straight_curved",
        "task_type": "identify_property",
        "grade_min": 2,
    },
    {
        "question": "A solid figure has a surface with no bumps or curves, like a tabletop. What kind of surface is that?",
        "answer": "flat surface",
        "distractors": ["curved surface", "straight line", "curved line"],
        "concept_type": "straight_curved",
        "task_type": "identify_name",
        "grade_min": 2,
    },
    {
        "question": "A solid figure has a surface that bends all the way around, like a ball. What kind of surface is that?",
        "answer": "curved surface",
        "distractors": ["flat surface", "straight line", "curved line"],
        "concept_type": "straight_curved",
        "task_type": "identify_name",
        "grade_min": 2,
    },
    {
        "question": "A box has six faces that are each a flat square. What kind of surface does a box have?",
        "answer": "flat surface",
        "distractors": ["curved surface", "straight line", "curved line"],
        "concept_type": "straight_curved",
        "task_type": "identify_property",
        "grade_min": 2,
    },
    {
        "question": "A ball has a surface that bends smoothly in every direction. What kind of surface does a ball have?",
        "answer": "curved surface",
        "distractors": ["flat surface", "straight line", "curved line"],
        "concept_type": "straight_curved",
        "task_type": "identify_property",
        "grade_min": 2,
    },
    {
        "question": "A can has both flat surfaces (its ends) and one other kind of surface. What kind is it?",
        "answer": "curved surface",
        "distractors": ["flat surface", "straight line", "curved line"],
        "concept_type": "straight_curved",
        "task_type": "identify_property",
        "grade_min": 2,
    },
    {
        "question": "Which best describes the side of a solid figure that you could trace with a straight ruler?",
        "answer": "flat surface",
        "distractors": ["curved surface", "straight line", "curved line"],
        "concept_type": "straight_curved",
        "task_type": "identify_property",
        "grade_min": 2,
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
        # Relax only task_type -- concept_type is the node's bound curriculum
        # scope (registry.py's _parse_competency_bounds) and must never be
        # silently swapped for a different one. A prior version of this
        # function fell through to "any concept_type at this grade", which
        # silently served mat_g2_mg_q4_3 (straight/curved lines) unrelated
        # G1 rotation-degree trivia whenever no exact task_type match
        # existed. Fail loud instead (AGENTS.md rule #3).
        candidates = [
            item for item in _ITEM_POOL
            if item["grade_min"] <= grade and item["concept_type"] == concept_type
        ]
    if not candidates:
        raise ValueError(
            f"geometric_lines: no item pool entries for concept_type={concept_type!r} "
            f"at grade<={grade} (seed={seed}). This is a content-coverage gap in "
            f"_ITEM_POOL, not a condition to silently substitute a different "
            f"concept_type's content for."
        )

    item = dict(rng.choice(candidates))
    item["result"] = item["answer"]
    return item


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    concept_type = values.get("concept_type", "point_line_segment_ray")
    if concept_type == "straight_curved":
        return [
            "A straight line never bends.",
            "A curved line bends smoothly.",
            "A flat surface has no bumps or curves, like a tabletop.",
            "A curved surface bends, like the outside of a ball or a can.",
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
        "g2": {},
        "g3": {},
    },
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "categorize"],
    requires_context=False,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
