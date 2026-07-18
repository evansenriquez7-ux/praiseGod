"""
DNA: Length Measurement (Measurement & Geometry)

Covers MATATAG grades 1–2 length measurement competencies.
  G1: non-standard units only (paperclips, hands, steps)
  G2: meters and centimeters, simple conversion, comparisons
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set, Tuple

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
        "length_max": 100,
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

def _standard_unit_bounds(bounds: Dict[str, Any], unit: str, scalar: float) -> Tuple[int, int]:
    lo_key, hi_key = ("cm_min", "cm_max") if unit == "cm" else ("m_min", "m_max")
    lo, hi = bounds.get(lo_key, 1), bounds.get(hi_key, 100)
    hi = max(lo, int(log_interpolate(lo, hi, scalar)))
    return lo, hi


def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
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

    # unit_type variant values are "cm" / "m" (see VARIANTS_BY_DNA) — standard
    # units are a G2+ competency; requesting them at G1 must fail loudly rather
    # than silently falling through to a mismatched branch (the previous bug:
    # "centimeters"/"meters" never matched "cm"/"m" and fell through to
    # convert_between regardless of what was requested).
    requested_unit_type = profile.get("unit_type")
    if requested_unit_type is not None and requested_unit_type not in ("cm", "m"):
        raise ValueError(
            f"generate_params (length_measurement): unknown unit_type '{requested_unit_type}'."
        )
    if requested_unit_type is not None and grade < 2:
        raise ValueError(
            f"generate_params (length_measurement): unit_type='{requested_unit_type}' (standard units) "
            f"is not available for grade={grade} (G1 uses non-standard units only)."
        )

    task_type = profile.get("task_type", "read_measurement")
    if task_type not in ("read_measurement", "compare", "convert"):
        raise ValueError(
            f"generate_params (length_measurement): unknown task_type '{task_type}'."
        )
    if task_type == "convert" and grade < 2:
        raise ValueError(
            f"generate_params (length_measurement): task_type='convert' is not available for grade={grade}."
        )

    scalar = float(profile.get("difficulty_scalar", 0.5))
    unit_mode = "non_standard" if grade < 2 else (requested_unit_type or "cm")

    if task_type == "compare":
        if unit_mode == "non_standard":
            unit = rng.choice(_NON_STANDARD_UNITS)
            l_min, l_max = bounds.get("length_min", 1), bounds.get("length_max", 100)
            l_max_current = max(l_min, int(log_interpolate(l_min, l_max, scalar)))
            val_a = rng.randint(l_min, l_max_current)
            val_b = rng.randint(l_min, l_max_current)
            while val_b == val_a:
                val_b = rng.randint(l_min, l_max_current)
        else:
            unit = unit_mode
            lo, hi = _standard_unit_bounds(bounds, unit_mode, scalar)
            val_a = rng.randint(lo, hi)
            val_b = rng.randint(lo, hi)
            while val_b == val_a:
                val_b = rng.randint(lo, hi)
        answer = max(val_a, val_b)
        return {
            "blank_target": "answer",
            "value_a": val_a,
            "value_b": val_b,
            "unit": unit,
            "unit_type": unit_mode,
            "task_type": "compare",
            "answer": answer,
            "distractors": [val_a, val_b, min(val_a, val_b)],
        }

    if unit_mode == "non_standard":
        unit = rng.choice(_NON_STANDARD_UNITS)
        l_min, l_max = bounds.get("length_min", 1), bounds.get("length_max", 100)

        # We use log interpolate so we spend a good amount of time in 1-20 range before jumping to 100
        l_max_current = max(l_min, int(log_interpolate(l_min, l_max, scalar)))

        # Calculate tick step based on difficulty (1 to 10)
        tick_options = [1, 2, 5, 10]
        tick_step = tick_options[min(3, int(scalar * 4))]

        # Ensure UX is visually clear for larger numbers (prevent too many tiny ticks)
        if l_max_current > 50:
            tick_step = max(tick_step, 10)
        elif l_max_current > 20:
            tick_step = max(tick_step, 5)

        # Snap the length to a multiple of tick_step so it always lands exactly on a tick mark
        min_mult = max(1, (l_min + tick_step - 1) // tick_step)
        max_mult = max(min_mult, l_max_current // tick_step)
        length = rng.randint(min_mult, max_mult) * tick_step

        return {
            "blank_target": "answer",
            "length": length,
            "unit": unit,
            "unit_type": "non_standard",
            "task_type": task_type,
            "tick_step": tick_step,
            "answer": length,
        }

    if task_type != "convert":
        lo, hi = _standard_unit_bounds(bounds, unit_mode, scalar)
        length = rng.randint(lo, hi)
        return {
            "blank_target": "answer",
            "length": length,
            "unit": unit_mode,
            "unit_type": unit_mode,
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
        "blank_target": "answer",
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
        "blank_target": "answer",
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
    unit_label = {"cm": cm_label, "m": m_label}

    if unit_type == "non_standard":
        unit = values.get("unit", "units")
        return [
            f"Count how many {unit} fit along the object from end to end.",
            "Make sure no gaps or overlaps between the units.",
            f"The length is {values['answer']} {unit}.",
        ]

    if values.get("task_type") == "compare":
        val_a, val_b = values["value_a"], values["value_b"]
        unit_word = unit_label.get(unit_type, values.get("unit", "units"))
        return [
            f"Compare {val_a} {unit_word} and {val_b} {unit_word}.",
            f"{max(val_a, val_b)} is more than {min(val_a, val_b)}.",
            f"The longer length is {values['answer']} {unit_word}.",
        ]

    if unit_type == "convert_between":
        direction = values.get("direction", "m_to_cm")
        if direction == "m_to_cm":
            return [
                f"1 {m_label} = 100 {cm_label}.",
                f"Multiply {values['length']} × 100 to convert {m_label} to {cm_label}.",
                f"Answer: {values['answer']} {cm_label}.",
            ]
        else:
            return [
                f"100 {cm_label} = 1 {m_label}.",
                f"Divide {values['length']} ÷ 100 to convert {cm_label} to {m_label}.",
                f"Answer: {values['answer']} {m_label}.",
            ]

    return [
        f"Read the measurement on the ruler carefully.",
        f"The length is {values['answer']} {values.get('unit', 'units')}.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

LENGTH_MEASUREMENT_DNA = DNA(
    concept="length_measurement",
    dna_type="algorithmic",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "cloze", "numeric_input", "ruler_measure"],
    requires_context=True,
    visual_home="RulerMeasure",
    difficulty_axes=_DIFFICULTY_AXES,
)
