"""
DNA: Length Measurement (Measurement & Geometry)

Covers MATATAG grades 1–2 length measurement competencies.
  G1: non-standard units only (paperclips, hands, steps)
  G2: meters and centimeters, simple conversion, comparisons
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
    linear_interpolate,
    log_interpolate,
)


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {
        "length_min": 1,
        "length_max": 20,
        "units": ["paperclips", "hands", "steps", "blocks"],
    },
    "g2": {
        "cm_min": 1,
        "cm_max": 500,
        "m_min": 1,
        "m_max": 100,
    },
}

# Non-standard unit objects used at G1
_NON_STANDARD_UNITS = ["paperclips", "hands", "steps", "blocks", "crayons"]


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="length_measurement",
        label="ms_conv_dir",
        description="Confused conversion direction: multiplied instead of divided (or vice versa) between m and cm.",
    ),
    ErrorPattern(
        formula="None",
        required_concept="length_measurement",
        label="ms_wrong_factor",
        description="Used wrong conversion factor (e.g., 10 instead of 100 between m and cm).",
    ),
    ErrorPattern(
        formula="None",
        required_concept="length_measurement",
        label="ms_perim_area",
        description="Confused measurement of length with area.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {
    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_CENTIMETER = VocabGated(
    requires_vocab="centimeter",
    preferred="centimeter (cm)",
    fallback="small unit of length",
)
VOCAB_METER = VocabGated(
    requires_vocab="meter",
    preferred="meter (m)",
    fallback="larger unit of length",
)
VOCAB_ESTIMATE = VocabGated(
    requires_vocab="estimate",
    preferred="estimate",
    fallback="make a good guess",
)
VOCAB_LENGTH = VocabGated(
    requires_vocab="length",
    preferred="length",
    fallback="how long",
)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """
    Returns numeric params used by the ruler_measure formatter or word-problem spine.
    For G1 (non-standard), returns a unit name and integer count.
    For G2, returns cm or m values with optional conversion.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}
    g_key = f"g{max(1, min(grade, 2))}"
    bounds = _PARAM_BOUNDS[g_key]
    unit_type = profile.get("unit_type", "non_standard" if grade == 1 else "centimeters")
    task_type = profile.get("task_type", "read_measurement")
    scalar = float(profile.get("difficulty_scalar", 0.5))

    if unit_type == "non_standard":
        unit = rng.choice(_NON_STANDARD_UNITS)
        l_min, l_max = bounds.get("length_min", 1), bounds.get("length_max", 20)
        l_max = max(l_min, int(linear_interpolate(l_min, l_max, scalar)))
        length = rng.randint(l_min, l_max)
        return {
            "length": length,
            "unit": unit,
            "unit_type": "non_standard",
            "task_type": task_type,
            "answer": length,
        }

    if unit_type == "centimeters":
        lo, hi = bounds.get("cm_min", 1), bounds.get("cm_max", 500)
        hi = max(lo, int(log_interpolate(lo, hi, scalar)))
        length = rng.randint(lo, hi)
        return {
            "length": length,
            "unit": "cm",
            "unit_type": "centimeters",
            "task_type": task_type,
            "answer": length,
        }

    if unit_type == "meters":
        lo, hi = bounds.get("m_min", 1), bounds.get("m_max", 100)
        hi = max(lo, int(linear_interpolate(lo, hi, scalar)))
        length = rng.randint(lo, hi)
        return {
            "length": length,
            "unit": "m",
            "unit_type": "meters",
            "task_type": task_type,
            "answer": length,
        }

    # convert_between: give meters, ask for centimeters (or vice versa)
    lo, hi = bounds.get("m_min", 1), min(bounds.get("m_max", 100), 20)
    hi = max(lo, int(linear_interpolate(lo, hi, scalar)))
    length_m = rng.randint(lo, hi)
    direction = rng.choice(["m_to_cm", "cm_to_m"])
    if direction == "m_to_cm":
        return {
            "length": length_m,
            "unit": "m",
            "target_unit": "cm",
            "unit_type": "convert_between",
            "task_type": task_type,
            "answer": length_m * 100,
            "conversion_factor": 100,
            "direction": "m_to_cm",
        }
    else:
        length_cm = length_m * 100
        return {
            "length": length_cm,
            "unit": "cm",
            "target_unit": "m",
            "unit_type": "convert_between",
            "task_type": task_type,
            "answer": length_m,
            "conversion_factor": 100,
            "direction": "cm_to_m",
        }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    unit_type = values.get("unit_type", "non_standard")
    cm_label = VOCAB_CENTIMETER.resolve(cumulative_vocab)
    m_label  = VOCAB_METER.resolve(cumulative_vocab)

    if unit_type == "non_standard":
        unit = values.get("unit", "units")
        return [
            f"Count how many {unit} fit along the object from end to end.",
            "Make sure no gaps or overlaps between the units.",
            f"The length is {values['answer']} {unit}.",
        ]

    if unit_type == "convert_between":
        direction = values.get("direction", "m_to_cm")
        if direction == "m_to_cm":
            return [
                f"1 {m_label} = 100 {cm_label}.",
                f"Multiply {values['length']} × 100 to convert meters to centimeters.",
                f"Answer: {values['answer']} cm.",
            ]
        else:
            return [
                f"100 {cm_label} = 1 {m_label}.",
                f"Divide {values['length']} ÷ 100 to convert centimeters to meters.",
                f"Answer: {values['answer']} m.",
            ]

    return [
        f"Read the measurement on the ruler carefully.",
        f"The length is {values['answer']} {values.get('unit', 'units')}.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

LENGTH_MEASUREMENT_DNA = DNA(
    concept="length_measurement",
    dna_type="formula",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "cloze", "numeric_input", "ruler_measure"],
    requires_context=True,
    visual_home="RulerMeasure",
    difficulty_axes=_DIFFICULTY_AXES,
)
