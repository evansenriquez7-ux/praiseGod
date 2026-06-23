"""
DNA: Mass and Capacity (Measurement & Geometry)

Covers MATATAG grade 3 mass and capacity competencies.
  Mass:     grams (g), kilograms (kg), milligrams (mg)
  Capacity: liters (L), milliliters (mL)
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
    "g3": {
        "mass_g_min":     1,
        "mass_g_max":     5000,
        "capacity_ml_min": 1,
        "capacity_ml_max": 5000,
    },
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="mass_capacity",
        label="ms_conv_dir",
        description="Conversion direction error: multiplied instead of divided (or vice versa) between g and kg, or mL and L.",
    ),
    ErrorPattern(
        formula="None",
        required_concept="mass_capacity",
        label="ms_wrong_factor",
        description="Used wrong conversion factor (e.g., 100 instead of 1000 between g and kg).",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, List[str]] = {
    }


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_GRAM     = VocabGated(requires_vocab="gram",      preferred="gram (g)",       fallback="small unit of mass")
VOCAB_KILOGRAM = VocabGated(requires_vocab="kilogram",  preferred="kilogram (kg)",  fallback="larger unit of mass")
VOCAB_LITER    = VocabGated(requires_vocab="liter",     preferred="liter (L)",      fallback="unit of liquid volume")
VOCAB_MILLI    = VocabGated(requires_vocab="milliliter", preferred="milliliter (mL)", fallback="small unit of liquid volume")
VOCAB_MASS     = VocabGated(requires_vocab="mass",      preferred="mass",           fallback="how heavy something is")
VOCAB_CAPACITY = VocabGated(requires_vocab="capacity",  preferred="capacity",       fallback="how much liquid a container holds")


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """
    Returns measurement value(s) and the answer.
    For 'convert' task: produces value in one unit, answer in the other.
    For 'compare': produces two values, answer is the heavier/larger one.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}
    bounds = _PARAM_BOUNDS["g3"]

    mtype     = profile.get("measurement_type", "mass")
    unit      = profile.get("unit", "grams_kilograms")
    task_type = profile.get("task_type", "read_measurement")
    scalar = float(profile.get("difficulty_scalar", 0.5))

    if mtype == "mass":
        g_min, g_max = bounds["mass_g_min"], bounds["mass_g_max"]
        g_max = max(g_min, int(log_interpolate(g_min, g_max, scalar)))
        val_g = rng.randint(g_min, g_max)

        if task_type == "convert":
            # g to kg (always divide by 1000)
            if unit == "grams_kilograms":
                # Pick a clean multiple of 1000 for clean conversion
                val_g = rng.randint(1, 5) * 1000
                val_kg = val_g // 1000
                return {
                    "measurement_type": "mass",
                    "task_type": "convert",
                    "value": val_g,
                    "from_unit": "g",
                    "to_unit": "kg",
                    "answer": val_kg,
                    "answer_formula": "value_g / 1000",
                    "conversion_factor": 1000,
                }
            # kg to g
            val_kg = rng.randint(1, 5)
            return {
                "measurement_type": "mass",
                "task_type": "convert",
                "value": val_kg,
                "from_unit": "kg",
                "to_unit": "g",
                "answer": val_kg * 1000,
                "answer_formula": "value_kg * 1000",
                "conversion_factor": 1000,
            }

        if task_type == "compare":
            val_g2 = rng.randint(g_min, g_max)
            heavier = max(val_g, val_g2)
            return {
                "measurement_type": "mass",
                "task_type": "compare",
                "value_a": val_g,
                "value_b": val_g2,
                "unit": "g",
                "answer": heavier,
                "answer_label": f"{heavier} g",
            }

        # read_measurement or estimate
        return {
            "measurement_type": "mass",
            "task_type": task_type,
            "value": val_g,
            "unit": "g",
            "answer": val_g,
        }

    # capacity
    ml_min, ml_max = bounds["capacity_ml_min"], bounds["capacity_ml_max"]
    ml_max = max(ml_min, int(log_interpolate(ml_min, ml_max, scalar)))
    val_ml = rng.randint(ml_min, ml_max)

    if task_type == "convert":
        val_ml = rng.randint(1, 5) * 1000
        val_l  = val_ml // 1000
        return {
            "measurement_type": "capacity",
            "task_type": "convert",
            "value": val_ml,
            "from_unit": "mL",
            "to_unit": "L",
            "answer": val_l,
            "answer_formula": "value_ml / 1000",
            "conversion_factor": 1000,
        }

    if task_type == "compare":
        val_ml2 = rng.randint(ml_min, ml_max)
        larger = max(val_ml, val_ml2)
        return {
            "measurement_type": "capacity",
            "task_type": "compare",
            "value_a": val_ml,
            "value_b": val_ml2,
            "unit": "mL",
            "answer": larger,
            "answer_label": f"{larger} mL",
        }

    return {
        "measurement_type": "capacity",
        "task_type": task_type,
        "value": val_ml,
        "unit": "mL",
        "answer": val_ml,
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    g_label   = VOCAB_GRAM.resolve(cumulative_vocab)
    kg_label  = VOCAB_KILOGRAM.resolve(cumulative_vocab)
    l_label   = VOCAB_LITER.resolve(cumulative_vocab)
    ml_label  = VOCAB_MILLI.resolve(cumulative_vocab)
    task_type = values.get("task_type", "read_measurement")
    mtype     = values.get("measurement_type", "mass")

    if task_type == "convert":
        from_unit = values.get("from_unit", "g")
        to_unit   = values.get("to_unit", "kg")
        factor    = values.get("conversion_factor", 1000)
        val       = values.get("value", "?")
        ans       = values.get("answer", "?")
        if from_unit in ("g",):
            return [
                f"1 {kg_label} = 1000 {g_label}.",
                f"To convert {g_label} to {kg_label}, divide by 1000.",
                f"{val} ÷ {factor} = {ans} kg.",
            ]
        if from_unit in ("kg",):
            return [
                f"1 {kg_label} = 1000 {g_label}.",
                f"To convert {kg_label} to {g_label}, multiply by 1000.",
                f"{val} × {factor} = {ans} g.",
            ]
        if from_unit == "mL":
            return [
                f"1 {l_label} = 1000 {ml_label}.",
                f"To convert {ml_label} to {l_label}, divide by 1000.",
                f"{val} ÷ {factor} = {ans} L.",
            ]
        return [
            f"1 {l_label} = 1000 {ml_label}.",
            f"Multiply by 1000 to convert L to mL.",
            f"{val} × {factor} = {ans} mL.",
        ]

    if task_type == "compare":
        a = values.get("value_a", "?")
        b = values.get("value_b", "?")
        unit = values.get("unit", "g")
        return [
            f"Compare the two measurements: {a} {unit} and {b} {unit}.",
            f"The larger number is heavier (or holds more): {values['answer']} {unit}.",
        ]

    if mtype == "mass":
        return [
            f"Read the scale carefully.",
            f"The mass shown is {values['value']} g.",
            f"Remember: 1000 {g_label} = 1 {kg_label}.",
        ]
    return [
        f"Read the container's measurement carefully.",
        f"The capacity shown is {values['value']} mL.",
        f"Remember: 1000 {ml_label} = 1 {l_label}.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

MASS_CAPACITY_DNA = DNA(
    concept="mass_capacity",
    dna_type="formula",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "cloze", "numeric_input"],
    requires_context=True,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
