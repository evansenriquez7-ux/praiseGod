"""
DNA: Perimeter (Measurement & Geometry)

Covers MATATAG grades 2–3 perimeter competencies.
  G2: perimeter of triangle, square, rectangle
  G3: extended with missing-side problems
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
    "g2": {"side_min": 1, "side_max": 50},
    "g3": {"side_min": 1, "side_max": 100},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="perimeter",
        label="ms_perim_area",
        description="Multiplied sides instead of adding them (used area formula for perimeter).",
    ),
    ErrorPattern(
        formula="None",
        required_concept="perimeter",
        label="ms_area_perim",
        description="Added only two sides instead of all sides (incomplete perimeter).",
    ),
    ErrorPattern(
        formula="None",
        required_concept="perimeter",
        label="ms_wrong_factor",
        description="For rectangle: added all four sides but used wrong opposite-side relationship.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, List[str]] = {
    "number_size": ["small_numbers", "larger_numbers"],
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_PERIMETER = VocabGated(
    requires_vocab="perimeter",
    preferred="perimeter",
    fallback="the total distance around the shape",
)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """
    Returns sides dict and the answer (perimeter or missing side).
    For missing_side tasks (G3+), one side is withheld and the answer is that side.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}
    g_key = f"g{max(2, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]

    shape     = profile.get("shape", "rectangle")
    task_type = profile.get("task_type", "find_perimeter")
    num_size  = profile.get("number_size", "small_numbers")
    scalar    = float(profile.get("difficulty_scalar", 0.5))

    lo = bounds["side_min"]
    hi_bound = bounds["side_max"] // 2 if num_size == "small_numbers" else bounds["side_max"]
    hi = max(lo, int(linear_interpolate(lo, hi_bound, scalar)))
    lo = max(1, lo)
    hi = max(lo + 1, hi)

    if shape == "square":
        s = rng.randint(lo, hi)
        perimeter = 4 * s
        sides = {"s": s}
        answer_formula_used = "4 * s"
        if task_type == "find_missing_side" and grade >= 3:
            return {
                "shape": "square",
                "perimeter": perimeter,
                "task_type": "find_missing_side",
                "answer": s,
                "answer_formula": "perimeter / 4",
                "sides": sides,
            }
        return {
            "shape": "square",
            "sides": sides,
            "task_type": "find_perimeter",
            "answer": perimeter,
            "answer_formula": answer_formula_used,
        }

    if shape == "rectangle":
        l = rng.randint(lo, hi)
        w = rng.randint(lo, hi)
        perimeter = 2 * (l + w)
        sides = {"l": l, "w": w}
        if task_type == "find_missing_side" and grade >= 3:
            # Give perimeter and one side; find the other
            known = rng.choice(["l", "w"])
            missing = "w" if known == "l" else "l"
            known_val = sides[known]
            missing_val = sides[missing]
            return {
                "shape": "rectangle",
                "perimeter": perimeter,
                "known_side": known,
                "known_value": known_val,
                "task_type": "find_missing_side",
                "answer": missing_val,
                "answer_formula": "(perimeter / 2) - known_value",
                "sides": sides,
            }
        return {
            "shape": "rectangle",
            "sides": sides,
            "task_type": "find_perimeter",
            "answer": perimeter,
            "answer_formula": "2 * (l + w)",
        }

    # triangle
    a = rng.randint(lo, hi)
    b = rng.randint(lo, hi)
    c = rng.randint(lo, hi)
    perimeter = a + b + c
    sides = {"a": a, "b": b, "c": c}
    if task_type == "find_missing_side" and grade >= 3:
        missing_side = rng.choice(["a", "b", "c"])
        known_sides = {k: v for k, v in sides.items() if k != missing_side}
        missing_val = sides[missing_side]
        return {
            "shape": "triangle",
            "perimeter": perimeter,
            "known_sides": known_sides,
            "task_type": "find_missing_side",
            "answer": missing_val,
            "answer_formula": "perimeter - sum(known_sides)",
            "sides": sides,
        }
    return {
        "shape": "triangle",
        "sides": sides,
        "task_type": "find_perimeter",
        "answer": perimeter,
        "answer_formula": "a + b + c",
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    perim_label = VOCAB_PERIMETER.resolve(cumulative_vocab)
    shape = values.get("shape", "shape")
    task_type = values.get("task_type", "find_perimeter")

    if task_type == "find_missing_side":
        known_sum = values["perimeter"] - values["answer"]
        return [
            f"The {perim_label} is the total distance around the shape.",
            f"Perimeter = sum of ALL sides. We know the perimeter is {values['perimeter']}.",
            f"The sides we know add up to {known_sum}.",
            f"Subtract: {values['perimeter']} - {known_sum} = {values['answer']}.",
        ]

    sides = values.get("sides", {})
    hints = [f"The {perim_label} is the total distance around the {shape}."]

    if shape == "square":
        s = sides.get("s", "?")
        hints.append(f"A square has 4 equal sides, each {s} units long.")
        hints.append(f"Perimeter = 4 × {s} = {values['answer']}.")
    elif shape == "rectangle":
        l, w = sides.get("l", "?"), sides.get("w", "?")
        hints.append(f"A rectangle has two sides of length {l} and two sides of width {w}.")
        hints.append(f"Perimeter = 2 × ({l} + {w}) = 2 × {l + w} = {values['answer']}.")
    else:
        a, b, c = sides.get("a", "?"), sides.get("b", "?"), sides.get("c", "?")
        hints.append(f"Add all three sides: {a} + {b} + {c} = {values['answer']}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

PERIMETER_DNA = DNA(
    concept="perimeter",
    dna_type="formula",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "cloze", "numeric_input"],
    requires_context=True,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
