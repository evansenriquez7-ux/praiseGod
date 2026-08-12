"""
DNA: Area (Measurement & Geometry)

Covers MATATAG grade 3 area competencies only.
  G3: area of squares and rectangles in sq cm and sq m
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
    linear_interpolate,
)


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    # Minimum side is 2, not 1: a 1x1 square has an area numerically equal to its
    # own side, so "A square has a side of 1 m. What is its area in sq m?" prints
    # its answer in the stem (validate_matrix §1F), and the tiled phrasing renders
    # the ungrammatical "arranged in 1 rows and 1 columns". A single tile is not
    # an area exercise in any case.
    "g3": {
        "side_cm_min": 2,
        "side_cm_max": 50,
        "side_m_min":  2,
        "side_m_max":  20,
        # illustrate_tiles/derive_formula ask the student to visually tile-count
        # or trace rows × columns one tile at a time (mat_g3_mg_q1_0/_1) -- the
        # standard 2-50 cm range lets a rectangle reach e.g. 22x5=110 tiles,
        # blind review flagged that as too large to tile-count or trace at
        # first exposure. Keep those two task types near 10x10 or below.
        "side_cm_max_tiling": 12,
    },
}


# ─── error patterns ───────────────────────────────────────────────────────────
# Formulas are shape-conditional by construction: "l"/"w" exist only in
# rectangle samples' values and "s" only in square samples' (area.py never
# sets both), so _eval_error_formula's NameError on the wrong shape is caught
# by base_generator.py's error-pattern loop and that pattern simply doesn't
# fire for that sample -- exactly the intended per-shape gating, with no
# conditional needed here.
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="l + w",
        required_concept="area",
        label="ms_perim_area",
        description="Added side lengths instead of multiplying (used perimeter logic for area).",
    ),
    ErrorPattern(
        formula="2 * (l + w)",
        required_concept="area",
        label="ms_area_perim",
        description="Gave 2*(l+w) instead of l*w (computed perimeter instead of area).",
    ),
    ErrorPattern(
        formula="s + s",
        required_concept="area",
        label="ms_perim_area_square",
        description="Added the two sides instead of multiplying (used perimeter logic for area) on a square.",
    ),
    ErrorPattern(
        formula="4 * s",
        required_concept="area",
        label="ms_area_perim_square",
        description="Gave 4*s instead of s*s (computed perimeter instead of area) on a square.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {
    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_AREA = VocabGated(
    requires_vocab="area",
    preferred="area",
    fallback="the number of square units that cover the shape",
)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Returns side dimensions and the area answer.
    For find_missing_dimension tasks: gives area and one side, answer is the other.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}
    bounds = _PARAM_BOUNDS["g3"]

    # No silent default. This key used to fall back to "find_area", which meant a
    # node the registry never bound still generated -- plausibly, and wrongly --
    # instead of saying so. mat_g3_mg_q1_2 and mat_g3_mg_q1_3 both rode that
    # default and collapsed onto each other. If this raises, the fix is a binding
    # in registry.py's _parse_competency_bounds, never a default here.
    task_type = profile.get("task_type")
    if not task_type:
        raise ValueError(
            f"area: 'task_type' is not bound for this node "
            f"(grade={grade}, seed={seed}, profile={profile!r}); "
            f"bind it in registry.py _parse_competency_bounds for the competency "
            f"that maps to this node. Expected one of: find_area, "
            f"find_missing_dimension, illustrate_tiles, derive_formula."
        )
    # mat_g3_mg_q1_3 ("Solve problems involving areas") wants both the direct and
    # the inverse task, varying per seed. The registry binds a sentinel because it
    # computes bounds once per node; resolving the choice there would freeze every
    # seed to one task forever. Resolved here against this call's own rng so the
    # split is deterministic per seed.
    if task_type == "find_area_or_missing_dimension":
        task_type = rng.choice(["find_area", "find_missing_dimension"])

    context   = profile.get("context", "pure")
    scalar    = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))

    # Every one of the four area competencies names "a square or rectangle" /
    # "squares and rectangles" explicitly. Without an explicit override, vary
    # shape per seed instead of silently defaulting to rectangle every time --
    # blind review found zero square samples across any node because nothing
    # ever selected one.
    shape = profile.get("shape") or rng.choice(["rectangle", "square"])
    # "Given the area and one side, find the other" is a division for a rectangle
    # but a square ROOT for a square, and square roots are not a Grade 3 skill --
    # they appear nowhere in this grade's cumulative vocabulary. The square branch
    # below also never set known_dimension/known_value, so the stem builder fell
    # back to its "?" placeholder and rendered "A square has an area of 25 sq m and
    # a length of ? m. What is its width?" (mat_g3_mg_q1_3, seed 45). Both problems
    # have the same answer: this task is a rectangle task.
    if task_type == "find_missing_dimension":
        shape = "rectangle"
    # mat_g3_mg_q1_2's competency names "sq. cm and sq. m" explicitly; vary
    # unit for find_area/word-problem framings. illustrate_tiles/derive_formula
    # are tile-by-tile counting exercises -- keep those cm-scale, not metres.
    unit = profile.get("unit")
    if unit is None:
        if task_type in ("illustrate_tiles", "derive_formula"):
            unit = "square_cm"
        else:
            unit = rng.choice(["square_cm", "square_m"])

    if unit == "square_cm":
        lo, hi = bounds["side_cm_min"], bounds["side_cm_max"]
        if task_type in ("illustrate_tiles", "derive_formula"):
            hi = bounds["side_cm_max_tiling"]
        unit_label = "sq cm"
    else:
        lo, hi = bounds["side_m_min"], bounds["side_m_max"]
        unit_label = "sq m"

    hi = max(lo, int(linear_interpolate(lo, hi, scalar)))

    if shape == "square":
        s = rng.randint(lo, hi)
        area = s * s
        # No find_missing_dimension branch here: it is redirected to the rectangle
        # path above, because recovering a square's side from its area is a square
        # root. The branch that used to live here returned answer_formula
        # "sqrt(area)" and omitted known_dimension/known_value entirely.
        # illustrate_tiles / derive_formula reuse find_area's computation --
        # they differ only in framing (tile-counting vs. formula-derivation
        # narration), not in the underlying math, matching the competency
        # wording exactly (mat_g3_mg_q1_0: "Illustrate and estimate the area
        # ... using square tile units"; mat_g3_mg_q1_1: "Explore inductively
        # the derivation of the formula[] ... using square tile units").
        return {
            "blank_target": "answer",
            "shape": "square",
            "sides": {"s": s},
            "s": s,  # top-level alias for the area_solve spine template
            "shape_noun": "square",
            "dims_phrase": f"measuring {s} {unit_label.replace('sq ', '')} on each side",
            "length_unit": unit_label.replace("sq ", ""),
            "unit": unit_label,
            "task_type": task_type if task_type in ("illustrate_tiles", "derive_formula") else "find_area",
            "answer": area,
            "answer_formula": "s * s",
            "context": context,
        }

    # rectangle
    l = rng.randint(lo, hi)
    w = rng.randint(lo, hi)
    # A "rectangle" sample with l == w renders identically to a square (e.g.
    # "6 rows and 6 columns") -- undermining the very distinction the shape
    # variance above exists to test, and blind review caught it happening
    # (mat_g3_mg_q1_0 seed 44). Redraw until genuinely unequal, same pattern
    # already used by this DNA's own "compare" task_type for value_a/value_b.
    while w == l and hi > lo:
        w = rng.randint(lo, hi)
    area = l * w
    if task_type == "find_missing_dimension":
        known = rng.choice(["l", "w"])
        known_val = l if known == "l" else w
        missing_val = w if known == "l" else l
        return {
            "blank_target": "answer",
            "shape": "rectangle",
            "area": area,
            "unit": unit_label,
            "known_dimension": known,
            "known_value": known_val,
            "task_type": "find_missing_dimension",
            "answer": missing_val,
            "answer_formula": "area / known_value",
            "sides": {"l": l, "w": w},
            "l": l, "w": w,
            "context": context,
        }
    return {
        "blank_target": "answer",
        "shape": "rectangle",
        "sides": {"l": l, "w": w},
        "l": l, "w": w, "s": l,  # top-level aliases for spine templates & error formulas
        "shape_noun": "rectangular",
        "dims_phrase": f"that is {l} {unit_label.replace('sq ', '')} long and {w} {unit_label.replace('sq ', '')} wide",
        "length_unit": unit_label.replace("sq ", ""),
        "unit": unit_label,
        "task_type": task_type if task_type in ("illustrate_tiles", "derive_formula") else "find_area",
        "answer": area,
        "answer_formula": "l * w",
        "context": context,
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    area_label = VOCAB_AREA.resolve(cumulative_vocab)
    shape      = values.get("shape", "shape")
    unit       = values.get("unit", "sq cm")
    task_type  = values.get("task_type", "find_area")

    if task_type == "find_missing_dimension":
        known_val = values.get("known_value", "?")
        area      = values.get("area", "?")
        return [
            f"The {area_label} = length × width.",
            f"We know the area is {area} {unit} and one side is {known_val}.",
            f"Divide: {area} ÷ {known_val} = {values['answer']}.",
        ]

    sides = values.get("sides", {})
    hints = [f"The {area_label} tells us how many unit squares cover the shape."]

    if shape == "square":
        s = sides.get("s", "?")
        hints.append(f"Area of a square = side × side = {s} × {s} = {values['answer']} {unit}.")
    else:
        l, w = sides.get("l", "?"), sides.get("w", "?")
        hints.append(f"Area of a rectangle = length × width = {l} × {w} = {values['answer']} {unit}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

AREA_DNA = DNA(
    concept="area",
    dna_type="algorithmic",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "cloze", "numeric_input", "grid_area"],
    requires_context=True,
    visual_home="GridArea",
    difficulty_axes=_DIFFICULTY_AXES,
)
