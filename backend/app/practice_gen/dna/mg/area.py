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
    "g3": {
        "side_cm_min": 1,
        "side_cm_max": 50,
        "side_m_min":  1,
        "side_m_max":  20,
    },
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="area",
        label="ms_perim_area",
        description="Added side lengths instead of multiplying (used perimeter logic for area).",
    ),
    ErrorPattern(
        formula="None",
        required_concept="area",
        label="ms_area_perim",
        description="Gave 2*(l+w) instead of l*w (computed perimeter instead of area).",
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

    shape     = profile.get("shape", "rectangle")
    unit      = profile.get("unit", "square_cm")
    task_type = profile.get("task_type", "find_area")
    scalar    = float(profile.get("difficulty_scalar", 0.5))

    if unit == "square_cm":
        lo, hi = bounds["side_cm_min"], bounds["side_cm_max"]
        unit_label = "sq cm"
    else:
        lo, hi = bounds["side_m_min"], bounds["side_m_max"]
        unit_label = "sq m"
        
    hi = max(lo, int(linear_interpolate(lo, hi, scalar)))

    if shape == "square":
        s = rng.randint(lo, hi)
        area = s * s
        if task_type == "find_missing_dimension":
            # Give area (a perfect square), find side length
            # Re-pick s to keep it a clean integer root
            s = rng.randint(lo, min(hi, 10))  # keep sq roots manageable
            area = s * s
            return {
        "blank_target": "answer",
                "shape": "square",
                "area": area,
                "unit": unit_label,
                "task_type": "find_missing_dimension",
                "answer": s,
                "answer_formula": "sqrt(area)",
                "sides": {"s": s},
            }
        return {
        "blank_target": "answer",
            "shape": "square",
            "sides": {"s": s},
            "unit": unit_label,
            "task_type": "find_area",
            "answer": area,
            "answer_formula": "s * s",
        }

    # rectangle
    l = rng.randint(lo, hi)
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
        }
    return {
        "blank_target": "answer",
        "shape": "rectangle",
        "sides": {"l": l, "w": w},
        "unit": unit_label,
        "task_type": "find_area",
        "answer": area,
        "answer_formula": "l * w",
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
    dna_type="formula",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "cloze", "numeric_input", "grid_area"],
    requires_context=True,
    visual_home="GridArea",
    difficulty_axes=_DIFFICULTY_AXES,
)
