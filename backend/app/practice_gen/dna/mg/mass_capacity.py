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
_DIFFICULTY_AXES: Dict[str, Any] = {
    "number_difficulty": "continuous",
}


# ─── units ────────────────────────────────────────────────────────────────────
# The units each measurement type may be read in, in the order the MATATAG
# competency names them. `generate_params` cycles these by seed so a node's
# sample set covers every unit its competency names.
#
# Before this existed, `generate_params` read a `unit` key off the difficulty
# profile that no axis ever declared and no registry binding ever set, so it was
# pinned to its default forever: every mass item rendered in grams and every
# capacity item in millilitres, and the kg->g branch of `convert` was dead code.
# Blind review caught it on both nodes -- "kilograms and milligrams never
# appear" (mat_g3_mg_q2_0) and "liters never appear" (mat_g3_mg_q2_3).
_UNITS_FOR: Dict[str, tuple] = {
    "mass":     ("g", "kg", "mg"),
    "capacity": ("mL", "L"),
}

# Sensible Grade 3 reading magnitudes per unit. Every range sits inside the
# numeric envelope declared in _PARAM_BOUNDS, so unit variation cannot push a
# value past the bounds the harness checks.
_UNIT_RANGE: Dict[str, tuple] = {
    "g":  (1, 5000),
    "kg": (1, 500),
    "mg": (1, 5000),
    "mL": (1, 5000),
    "L":  (1, 500),
}

# Conversion partners, for the `convert` task only.
_CONVERSION_PAIRS: Dict[str, tuple] = {
    "mass":     ("g", "kg"),
    "capacity": ("mL", "L"),
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_GRAM     = VocabGated(requires_vocab="gram",      preferred="gram (g)",       fallback="small unit of mass")
VOCAB_KILOGRAM = VocabGated(requires_vocab="kilogram",  preferred="kilogram (kg)",  fallback="larger unit of mass")
VOCAB_LITER    = VocabGated(requires_vocab="liter",     preferred="liter (L)",      fallback="unit of liquid volume")
VOCAB_MILLI    = VocabGated(requires_vocab="milliliter", preferred="milliliter (mL)", fallback="small unit of liquid volume")
VOCAB_MASS     = VocabGated(requires_vocab="mass",      preferred="mass",           fallback="how heavy something is")
VOCAB_CAPACITY = VocabGated(requires_vocab="capacity",  preferred="capacity",       fallback="how much liquid a container holds")


# ─── parameter generator ──────────────────────────────────────────────────────

def _round_unit_for(val: int) -> int:
    """
    Pick a sensible rounding granularity for an estimate task by magnitude.

    Every granularity must be a place-value column. This returned 500 for
    values >= 1000, which is not a column any elementary curriculum rounds to --
    "rounded to the nearest 500" is not an instruction a Grade 3 pupil has been
    taught to follow. It was unreachable while readings were capped low enough,
    and became visible once a node started reading in milligrams; a blind review
    caught it on `An object's mass measures 1927 mg. About how many mg is that,
    rounded to the nearest 500?`.
    """
    if val < 100:
        return 10
    if val < 1000:
        return 100
    return 1000


def _nudge_off_round(val: int) -> int:
    """
    Shift a value that is already an exact multiple of its rounding unit.

    "An object's mass measures 10 g. About how many g is that, rounded to the
    nearest 10?" answers itself — the value is printed in the stem and rounding
    changes nothing (validate_matrix §1F). Estimation is only a skill when there
    is something to estimate, so an already-round reading is moved one unit off
    the boundary (upward, so the value stays positive and inside its range).
    """
    unit = _round_unit_for(val)
    if unit and val % unit == 0:
        return val + 1
    return val


def _round_for_estimate(val: int) -> int:
    # A bare `max(unit, ...)` floor here was mathematically wrong: small
    # values (e.g. 2, rounding to the nearest 10) correctly round DOWN to
    # 0, not up to the rounding unit itself. Found by a blind judgment
    # review hand-verifying the rounding arithmetic.
    #
    # Python's builtin round() uses round-half-to-even ("banker's
    # rounding"): round(0.5) == 0, round(3.5) == 4. Elementary curricula
    # teach round-half-UP unconditionally (a value exactly at the midpoint
    # always rounds up), so round(5, nearest 10) must be 10, not 0 --
    # round() silently gave 0 for exactly this case. A second blind review
    # caught this: 5g rounded to 0 while 35g rounded to 40 in the same
    # sample set, an inconsistency traceable to 5 and 35 landing on
    # opposite sides of Python's even/odd tie-breaking.
    unit = _round_unit_for(val)
    import math
    return math.floor(val / unit + 0.5) * unit


def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Returns measurement value(s) and the answer.
    For 'convert' task: produces value in one unit, answer in the other.
    For 'compare': produces two values, answer is the heavier/larger one.
    """
    profile = difficulty_profile or {}
    bounds = _PARAM_BOUNDS["g3"]

    # No silent defaults. Both of these are bound by the registry for every
    # mapped node; if one is missing the binding is broken and a default would
    # hide it (Ground Rule 3 / CLAUDE.md Protocol 3). Failing loudly here is
    # what makes a missing binding findable instead of silently serving mass
    # content for a capacity competency.
    mtype = profile.get("measurement_type")
    if mtype not in _UNITS_FOR:
        raise ValueError(
            f"mass_capacity: 'measurement_type' must be bound to one of "
            f"{sorted(_UNITS_FOR)}, got {mtype!r} (grade={grade}, seed={seed}). "
            f"The registry competency bounds for this node do not pin it."
        )
    task_type = profile.get("task_type")
    if not task_type:
        raise ValueError(
            f"mass_capacity: 'task_type' is not bound for this node "
            f"(measurement_type={mtype!r}, grade={grade}, seed={seed}); "
            f"a default would silently serve the wrong competency."
        )
    scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))

    # Decorrelate the mass and capacity streams. They previously shared one
    # `random.Random(seed)` over identical bounds (1..5000 for both), so the
    # same seed produced the same number on both sides and the mass and
    # capacity nodes rendered identical readings that differed only in the unit
    # label -- blind review found mat_g3_mg_q2_0 and mat_g3_mg_q2_3 identical
    # on all nine shared seeds.
    rng = random.Random(f"{seed}:{mtype}")

    units = _UNITS_FOR[mtype]
    base_unit = units[0]

    if task_type == "convert":
        small, large = _CONVERSION_PAIRS[mtype]
        if rng.random() < 0.5:
            # small -> large (divide): pick a clean multiple for a clean answer
            val = rng.randint(1, 5) * 1000
            return {
                "blank_target": "answer",
                "measurement_type": mtype,
                "task_type": "convert",
                "value": val,
                "from_unit": small,
                "to_unit": large,
                "answer": val // 1000,
                "answer_formula": f"value_{small} / 1000",
                "conversion_factor": 1000,
            }
        # large -> small (multiply)
        val = rng.randint(1, 5)
        return {
            "blank_target": "answer",
            "measurement_type": mtype,
            "task_type": "convert",
            "value": val,
            "from_unit": large,
            "to_unit": small,
            "answer": val * 1000,
            "answer_formula": f"value_{large} * 1000",
            "conversion_factor": 1000,
        }

    # Every remaining task reads a magnitude in one of the competency's named
    # units. Cycling the unit by seed is what gives a node's sample set
    # coverage of all of them.
    unit = units[rng.randrange(len(units))]
    u_min, u_max = _UNIT_RANGE[unit]
    u_max = max(u_min, int(log_interpolate(u_min, u_max, scalar)))
    val = rng.randint(u_min, u_max)

    if task_type == "compare":
        # The two readings must differ. A tie renders "Which is heavier: 4 mg or
        # 4 mg?", which has no correct answer, yet the MCQ formatter still marks
        # one option correct -- an unanswerable item presented as answerable.
        # Ties were always possible here (two draws from one range) and became
        # likely once readings were drawn from the narrower per-unit ranges.
        #
        # A comparison also needs a range at least two values wide. At
        # scalar 0.0 the log interpolation collapses the upper bound onto the
        # lower one, so the easiest setting had nothing to compare; widening by
        # one keeps the easiest item well-formed (compare the two smallest
        # magnitudes) rather than ungenerable.
        hi = max(u_max, u_min + 1)
        val_a = rng.randint(u_min, hi)
        val_b = rng.randint(u_min, hi)
        if val_b == val_a:
            val_b = val_a + 1 if val_a < hi else val_a - 1
        winner = max(val_a, val_b)
        return {
            "blank_target": "answer",
            "measurement_type": mtype,
            "task_type": "compare",
            "value_a": val_a,
            "value_b": val_b,
            "unit": unit,
            "answer": winner,
            "answer_label": f"{winner} {unit}",
        }

    if task_type == "estimate":
        # "read_measurement" and "estimate" previously returned byte-identical
        # structure (only the task_type label differed, which nothing
        # downstream branched on) -- the two competencies ("measure mass using
        # appropriate tools" vs. "estimate mass") rendered indistinguishable
        # content. Estimation is framed here as rounding a precise reading to
        # the nearest round unit (a legitimate G3 interpretation that doesn't
        # require an external object-reference database the way "estimate a
        # paperclip's mass" would).
        val = _nudge_off_round(val)
        return {
            "blank_target": "answer",
            "measurement_type": mtype,
            "task_type": "estimate",
            "value": val,
            "round_to": _round_unit_for(val),
            "unit": unit,
            "answer": _round_for_estimate(val),
        }

    # read_measurement
    return {
        "blank_target": "answer",
        "measurement_type": mtype,
        "task_type": task_type,
        "value": val,
        "unit": unit,
        "answer": val,
        "base_unit": base_unit,
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

    # The reading hints must name the unit the item actually used. They used to
    # say "g" and "mL" unconditionally, which was harmless only while every
    # item was generated in those two units; now that a node cycles through the
    # units its competency names, a hardcoded label would contradict the stem.
    unit = values.get("unit")
    if not unit:
        raise ValueError(
            f"mass_capacity.generate_hints: no 'unit' in values for a "
            f"{task_type!r} {mtype!r} item; cannot write a hint without knowing "
            f"the unit shown. values={values!r}"
        )

    if mtype == "mass":
        return [
            f"Read the scale carefully.",
            f"The mass shown is {values['value']} {unit}.",
            f"Remember: 1000 {g_label} = 1 {kg_label}.",
        ]
    return [
        f"Read the container's measurement carefully.",
        f"The capacity shown is {values['value']} {unit}.",
        f"Remember: 1000 {ml_label} = 1 {l_label}.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

MASS_CAPACITY_DNA = DNA(
    concept="mass_capacity",
    dna_type="algorithmic",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "cloze", "numeric_input"],
    requires_context=True,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
