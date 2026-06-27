"""
DNA: Rounding (Number & Algebra)

G3 only — rounding 4-digit numbers to nearest 10, 100, or 1000.

MATATAG G3 Q1 introduces rounding as a prerequisite for estimation.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


# ─── param bounds ─────────────────────────────────────────────────────────────
# Rounding is G3-only; g1/g2 fallback to g3 via param_bounds_for_grade.
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g3": {"min_value": 1000, "max_value": 9999},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="(number // round_to) * round_to",
        required_concept="rounding",
        label="dc_round_dir",
        description="Always rounded down regardless of the digit after the rounding place.",
    ),
    ErrorPattern(
        formula="(number // (round_to * 10)) * (round_to * 10)",
        required_concept="rounding",
        label="dc_round_place",
        description="Rounded to the next larger precision (e.g., hundreds instead of tens).",
    ),
    ErrorPattern(
        formula="answer + 10",
        required_concept="rounding",
        label="ar_off_ten",
        description="Off by ten — misread the boundary digit.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {"number_difficulty": "continuous"}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_ROUND    = VocabGated(requires_vocab="round",    preferred="round",    fallback="find the closest")
VOCAB_NEAREST  = VocabGated(requires_vocab="nearest",  preferred="nearest",  fallback="closest")
VOCAB_ESTIMATE = VocabGated(requires_vocab="estimate", preferred="estimate", fallback="approximate")


# ─── helpers ──────────────────────────────────────────────────────────────────

def _round_standard(n: int, precision: int) -> int:
    """Round n to the nearest precision (10, 100, 1000) using round-half-up."""
    remainder = n % precision
    if remainder >= precision / 2:
        return n - remainder + precision
    return n - remainder


def _boundary_distance(n: int, precision: int) -> int:
    """Return how far n is from the nearest rounding boundary."""
    remainder = n % precision
    return min(remainder, precision - remainder)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate a rounding problem (G3 only).

    Returns:
        {
            "number":           int (4-digit),
            "round_to":         int (10 | 100 | 1000),
            "answer":           int (rounded result),
            "boundary_distance": int (distance from nearest .5 boundary),
        }
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    bounds = _PARAM_BOUNDS["g3"]
    min_val = int(profile.get("min_value", bounds["min_value"]))
    from backend.app.practice_gen.dna.base import log_interpolate
    diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
    max_val_bound = int(log_interpolate(10, bounds["max_value"], diff_scalar))
    max_val = int(profile.get("max_value", max_val_bound))
    if min_val >= max_val:
        min_val = max(10, max_val // 10)

    precision_map = {
        "nearest_ten":      10,
        "nearest_hundred":  100,
        "nearest_thousand": 1000,
    }
    precision_label = profile.get("precision", "nearest_ten")
    round_to = precision_map.get(precision_label, 10)

    boundary_prox = profile.get("boundary_proximity", "far_from_boundary")
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    candidates = []
    half = round_to // 2
    for number in range(min_val, max_val + 1):
        dist = _boundary_distance(number, round_to)

        # Do not present numbers that are already perfectly rounded
        if dist == 0:
            continue

        if boundary_prox == "near_boundary":
            # Within 10% of the half-way point
            if abs(dist - half) > max(1, half // 5):
                continue
        else:  # far_from_boundary
            # At least 20% away from the half-way point
            if abs(dist - half) < max(1, half // 5):
                continue
        candidates.append(number)

    if not candidates:
        # Fallback: any number
        candidates = list(range(min_val, max_val + 1))

    from backend.app.practice_gen.generators.number_difficulty import generate_number_by_window
    number = generate_number_by_window(candidates, num_diff_scalar, d=5, rng=rng)
    answer = _round_standard(number, round_to)

    return {
        "blank_target": "answer",
        "number":            number,
        "round_to":          round_to,
        "answer":            answer,
        "boundary_distance": _boundary_distance(number, round_to),
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hints for a rounding problem."""
    number   = values["number"]
    round_to = values["round_to"]
    answer   = values["answer"]

    round_label   = VOCAB_ROUND.resolve(cumulative_vocab)
    nearest_label = VOCAB_NEAREST.resolve(cumulative_vocab)

    place_names = {10: "tens", 100: "hundreds", 1000: "thousands"}
    place       = place_names.get(round_to, str(round_to))

    # Identify the key digit
    remainder    = number % round_to
    check_digit  = remainder // (round_to // 10)

    hints: List[str] = []
    if round_label.lower() == "round":
        hints.append(f"Round {number} to the {nearest_label} {place}.")
    else:
        hints.append(f"Find the {nearest_label} {place} to {number}.")
    hints.append(
        f"Look at the digit just to the right of the {place} place: it is {check_digit}."
    )
    if check_digit >= 5:
        hints.append(f"Since {check_digit} ≥ 5, round up.")
    else:
        hints.append(f"Since {check_digit} < 5, round down (keep the {place} digit the same).")
    hints.append(f"{number} rounded to the {nearest_label} {place} is {answer}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

ROUNDING_DNA = DNA(
    concept="rounding",
    dna_type="formula",
    answer_formula="((number + (round_to // 2)) // round_to) * round_to",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "number_line_read",
    ],
    requires_context=False,
    visual_home="NumberLine",
    difficulty_axes=_DIFFICULTY_AXES,
)
