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
        "distractors": ["line", "ray", "point"],
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
    # ── point / line / segment / ray: recognize_model ──────────────────────────
    {
        "question": "Look at the model: • P (a single dot with a label). Which geometric figure is represented?",
        "answer": "point",
        "distractors": ["line", "ray", "line segment"],
        "concept_type": "point_line_segment_ray",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    {
        "question": "Look at the model: <---A--------B---> (a straight path with arrowheads on both ends). Which geometric figure is represented?",
        "answer": "line",
        "distractors": ["line segment", "ray", "point"],
        "concept_type": "point_line_segment_ray",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    {
        "question": "Look at the model: • A--------B • (a straight path with endpoints at both ends). Which geometric figure is represented?",
        "answer": "line segment",
        "distractors": ["line", "ray", "point"],
        "concept_type": "point_line_segment_ray",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    {
        "question": "Look at the model: • A--------B---> (starts at endpoint A and extends past B with an arrowhead). Which geometric figure is represented?",
        "answer": "ray",
        "distractors": ["line", "line segment", "point"],
        "concept_type": "point_line_segment_ray",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    {
        "question": "Look at the diagram of a triangle. Each of its straight sides with two endpoints is an example of a ___.",
        "answer": "line segment",
        "distractors": ["line", "ray", "point"],
        "concept_type": "point_line_segment_ray",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    {
        "question": "A beam of light starting from a flashlight and travelling outward in one direction is a real-world model of a ___.",
        "answer": "ray",
        "distractors": ["line", "line segment", "point"],
        "concept_type": "point_line_segment_ray",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    # ── point / line / segment / ray: draw_construct ───────────────────────────
    {
        "question": "To draw a straight line segment between two points on paper, which tool should you use?",
        "answer": "ruler",
        "distractors": ["clock", "set square only", "thermometer"],
        "concept_type": "point_line_segment_ray",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "When drawing a ray, what symbol is placed at one end to show that it extends forever in that direction?",
        "answer": "arrowhead",
        "distractors": ["endpoint dot", "circle", "square"],
        "concept_type": "point_line_segment_ray",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "When drawing a line, what symbols are placed at both ends to show it extends forever in both directions?",
        "answer": "arrowheads",
        "distractors": ["endpoints", "dots", "numbers"],
        "concept_type": "point_line_segment_ray",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "To draw a line segment measuring 4 cm, you start at the 0 cm mark on a ruler and draw until which mark?",
        "answer": "4 cm",
        "distractors": ["0 cm", "8 cm", "10 cm"],
        "concept_type": "point_line_segment_ray",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "Which is the correct way to draw a point?",
        "answer": "Make a small dot on paper and label it with a letter.",
        "distractors": [
            "Draw a long line with arrows on both ends.",
            "Draw a path with one endpoint and one arrow.",
            "Draw two crossing paths.",
        ],
        "concept_type": "point_line_segment_ray",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    # ── parallel / intersecting / perpendicular: recognize_model ───────────────
    {
        "question": "Look at the model: two straight lines that run side by side and never meet ( || ). What type of lines are they?",
        "answer": "parallel lines",
        "distractors": ["perpendicular lines", "intersecting lines", "rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    {
        "question": "Look at the model: two lines that cross each other and form right angles / square corners ( ⟂ / + ). What type of lines are they?",
        "answer": "perpendicular lines",
        "distractors": ["parallel lines", "intersecting lines", "line segments"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    {
        "question": "Look at the model: two lines that cross at a single point without forming square corners ( X ). What type of lines are they?",
        "answer": "intersecting lines",
        "distractors": ["parallel lines", "perpendicular lines", "rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    {
        "question": "Look at the letter 'H'. The two vertical side segments are an example of ___.",
        "answer": "parallel lines",
        "distractors": ["perpendicular lines", "intersecting lines", "rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    {
        "question": "Look at the letter 'T'. The vertical and horizontal segments meet to form ___.",
        "answer": "perpendicular lines",
        "distractors": ["parallel lines", "intersecting lines", "curved lines"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    {
        "question": "Look at the letter 'X'. The two crossing line segments form ___.",
        "answer": "intersecting lines",
        "distractors": ["parallel lines", "perpendicular lines", "flat surfaces"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "recognize_model",
        "grade_min": 3,
    },
    # ── parallel / intersecting / perpendicular: draw_construct ────────────────
    {
        "question": "To draw perpendicular lines forming a square right angle, which tools can you use together?",
        "answer": "ruler and set square",
        "distractors": ["thermometer and clock", "clock and ruler", "ruler only"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "To draw parallel lines using a ruler and a set square, what is the correct technique?",
        "answer": "Slide the set square along the straight edge of the ruler and draw along its side.",
        "distractors": [
            "Cross the two edges at a 45 degree angle.",
            "Draw along the corner of the set square without moving it.",
            "Draw a single point and connect it in a circle.",
        ],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "When you draw a vertical line meeting a horizontal line to form a square corner, what type of lines have you drawn?",
        "answer": "perpendicular lines",
        "distractors": ["parallel lines", "curved lines", "rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "To draw two parallel lines using a ruler, you must make sure the lines ___.",
        "answer": "stay the same distance apart and never meet",
        "distractors": [
            "cross at a single point",
            "form a square right angle",
            "bend toward each other",
        ],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "To draw two intersecting lines, you draw two straight paths that ___.",
        "answer": "cross at a single point",
        "distractors": [
            "never meet",
            "run side by side",
            "stay the same distance apart",
        ],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "When drawing the two straight sides of a ladder, which type of lines should you draw?",
        "answer": "parallel lines",
        "distractors": ["perpendicular lines", "intersecting lines", "curved lines"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "When drawing a plus sign (+), which type of lines are being drawn?",
        "answer": "perpendicular lines",
        "distractors": ["parallel lines", "curved lines", "rays"],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "draw_construct",
        "grade_min": 3,
    },
    {
        "question": "To draw intersecting lines that are not perpendicular, what should you draw?",
        "answer": "Two straight lines that cross each other at a slanted angle.",
        "distractors": [
            "Two lines that never meet.",
            "Two lines that meet at a square right angle.",
            "A single ray with one endpoint.",
        ],
        "concept_type": "parallel_intersecting_perpendicular",
        "task_type": "draw_construct",
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
    profile = difficulty_profile or {}

    concept_type = profile.get("concept_type", "point_line_segment_ray")
    # task_type is enumerable (VARIANTS_BY_DNA) but a plain seed-only call
    # (no explicit profile, e.g. the judgment reviewer or adaptive default
    # serving) never picked one, silently defaulting to "identify_name"
    # every time -- blind review of mat_g3_mg_q1_4 found all five samples
    # were "what do we call" identify_name MCQs, with identify_property
    # ("how many endpoints does X have?") never once exercised.
    task_type = profile.get("task_type") or random.Random(seed).choice(
        ["identify_name", "identify_property", "recognize_model", "draw_construct"]
        if grade >= 3 else
        ["identify_name", "identify_property"]
    )

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

    # Deterministic round-robin instead of choice-with-replacement: a small
    # item pool (as few as 4-5 entries once concept_type/task_type narrow
    # it) sampled uniformly at random over only 5-6 review seeds clusters
    # badly by chance -- blind review of mat_g3_mg_q1_4 found the "point"
    # item 3 of 5 times while "line segment" never appeared once, though
    # it's in the same pool. Order the pool with a fixed internal shuffle
    # (independent of the sample seed, so it's stable across runs) and
    # cycle through it by seed -- every item in an eligible pool gets a
    # turn before any repeats.
    ordered = list(candidates)
    random.Random(0).shuffle(ordered)
    # A plain `seed % len(ordered)` collides for any two seeds that are a
    # multiple of len(ordered) apart -- with a 4-item pool, fixed review
    # seeds 42 and 46 are both index 2, rendering the identical item twice
    # (blind review caught this on parallel_intersecting_perpendicular).
    # Multiplicative hashing spreads nearby seeds across the pool instead.
    index = (seed * 2654435761) % len(ordered)
    item = dict(ordered[index])
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
