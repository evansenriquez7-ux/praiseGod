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
        "length_max": 12,
        "units": ["paperclips", "hands", "steps", "blocks"],
    },
    "g2": {
        "cm_min": 1,
        # 100, not 500. A 500 cm ceiling let the compare branch render
        # "Which is longer: 409 cm or 237 cm?" -- four metres stated in
        # centimetres, which a blind reviewer flagged twice. A metre stick is the
        # largest tool this grade measures with, so a centimetre reading past 100
        # is a metre reading wearing the wrong unit; the m bounds below cover
        # everything larger.
        "cm_max": 100,
        "m_min": 1,
        "m_max": 100,
    },
}

# Non-standard unit objects used at G1
_NON_STANDARD_UNITS = ["paperclips", "hands", "steps", "blocks", "crayons"]

# Roughly how big each non-standard unit and each measured object is, in cm. Nothing
# renders these numbers -- they exist so a COUNT can be derived rather than drawn.
# Objects and units used to be picked independently, which produced "A shoe is 10
# steps long." and "A book is 60 crayons long.", and in one sample "A crayon is 90
# blocks long. A shoe is 33 blocks long." -- a crayon three shoes long. The count of
# units spanning an object is not free: it is the object divided by the unit.
_NON_STANDARD_UNIT_CM = {
    "paperclips": 3,
    "blocks": 5,
    "crayons": 9,
    "hands": 15,
    "steps": 60,
}
_G1_OBJECT_CM = {
    "a crayon": 9,
    "a pencil": 17,
    "a book": 24,
    "a notebook": 26,
    "a shoe": 26,
}


def _units_spanning(obj: str, unit: str) -> int:
    """How many of `unit` lie along `obj`, never fewer than one."""
    return max(1, round(_G1_OBJECT_CM[obj] / _NON_STANDARD_UNIT_CM[unit]))

# Plausible centimetre ranges for the objects the word problems name. A measured
# length is only believable if it matches the thing being measured, and the numbers
# a child meets here are the size benchmarks they carry forward.
_OBJECT_CM_BANDS = {
    "a crayon":   (6, 12),
    "a pencil":   (10, 20),
    "a spoon":    (12, 20),
    "a ruler":    (15, 30),
    "a book":     (18, 30),
    "a notebook": (20, 30),
    "a shoe":     (20, 30),
}

# Metre-scale objects, kept in their own pool rather than measured in centimetres.
# "a garden path" used to sit in the centimetre table at (30, 100), which is how a
# blind reviewer found "A garden path is 30 cm long." next to a 6 cm crayon: the band
# made the number defensible while the unit stayed wrong. A path is metres.
_OBJECT_M_BANDS = {
    "a rope":         (2, 10),
    "a garden path":  (3, 20),
    "a hallway":      (5, 30),
    "a school fence": (10, 40),
}


def _object_pool(unit_mode: str) -> Dict[str, tuple]:
    """The objects worth measuring in this unit. A pencil is not metres long and a
    hallway is not centimetres long, so the noun follows the unit rather than being
    drawn from one pool and clamped afterwards."""
    return _OBJECT_CM_BANDS if unit_mode == "cm" else _OBJECT_M_BANDS


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
    if task_type not in (
        "read_measurement", "compare", "convert", "estimate", "choose_unit",
        "distance_between", "equal_length", "length_or_distance",
        "compare_distance", "compare_length_or_distance",
        "measure_compare_or_distance", "solve_problems_non_standard", "solve_word_problem",
    ):
        raise ValueError(
            f"generate_params (length_measurement): unknown task_type '{task_type}'."
        )
    if task_type == "length_or_distance":
        # registry.py sentinel for "measure the length of an object AND
        # the distance between two objects" (mat_g1_mg_q2_0): the
        # competency names two sub-tasks, so alternate between them per
        # seed rather than locking to one.
        task_type = random.Random(seed).choice(["read_measurement", "distance_between"])
    if task_type == "measure_compare_or_distance":
        # registry.py sentinel for "Measure AND compare lengths ... and distance in
        # meters" (mat_g2_mg_q2_0): three named sub-tasks, so rotate across all
        # three per seed rather than locking to the read_measurement default.
        task_type = random.Random(seed).choice(
            ["read_measurement", "compare", "distance_between"]
        )
    if task_type == "compare_length_or_distance":
        # registry.py sentinel for "Compare lengths AND distances"
        # (mat_g1_mg_q2_1): alternate between the two framings per seed.
        task_type = random.Random(seed).choice(["compare", "compare_distance"])
    # MOVED UP from below the compare_distance branch, where it could never take
    # effect: the redirect ran *after* the branch that handles compare_distance, so a
    # redirected distance_between fell past every handler to the read_measurement
    # return at the bottom. mat_g2_mg_q2_0 rendered "Measure the object. Its length
    # is ___ cm." for 125 of 200 seeds and never once mentioned a distance, though
    # its competency names "distance in meters". Resolving it here, alongside the
    # other sentinels, is the whole fix.
    #
    # Why redirect at all: the distance_between branch below is hardcoded to
    # non-standard units ("hands", "paperclips"), a G1-only framing per MATATAG.
    # compare_distance is the standard-units G2+ version of the same
    # "distance between two objects" skill. Raising instead would fail
    # validate_matrix's §1C sweep, which requires every declared task_type to render
    # for every node mapped to this DNA regardless of grade.
    if task_type == "distance_between" and grade >= 2:
        task_type = "compare_distance"

    if task_type == "convert" and grade < 2:
        raise ValueError(
            f"generate_params (length_measurement): task_type='convert' is not available for grade={grade}."
        )
    if task_type == "choose_unit" and grade < 2:
        raise ValueError(
            f"generate_params (length_measurement): task_type='choose_unit' (m vs cm) is not available for grade={grade}."
        )

    scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
    unit_mode = "non_standard" if grade < 2 else (requested_unit_type or "cm")

    if task_type == "compare":
        # Comparing two lengths needs at least two distinct values to draw from.
        if unit_mode == "non_standard":
            unit = rng.choice(_NON_STANDARD_UNITS)
            l_min, l_max = 2, 9
            val_a = rng.randint(l_min, l_max)
            val_b = rng.randint(l_min, l_max)
            while val_b == val_a:
                val_b = rng.randint(l_min, l_max)
            ask_shorter = rng.random() < 0.5
            answer = min(val_a, val_b) if ask_shorter else max(val_a, val_b)
            other = max(val_a, val_b) if ask_shorter else min(val_a, val_b)
            unit_a = unit[:-1] if val_a == 1 and unit.endswith("s") else unit
            unit_b = unit[:-1] if val_b == 1 and unit.endswith("s") else unit
            dists = [other, answer + 1, max(1, answer - 1)]
            dists = [d for d in dists if d != answer][:3]
            comp_word = "shorter" if ask_shorter else "longer"
            return {
                "blank_target": "answer",
                "value_a": val_a,
                "value_b": val_b,
                "unit": unit,
                "unit_type": unit_mode,
                "task_type": "compare",
                "answer": answer,
                "distractors": dists,
                "question": f"Which is {comp_word}: {val_a} {unit_a} or {val_b} {unit_b}?",
            }
        else:
            unit = unit_mode
            lo, hi = _standard_unit_bounds(bounds, unit_mode, scalar)
            hi = max(hi, lo + 1)
            obj_a, obj_b = rng.sample(sorted(_object_pool(unit_mode)), 2)
            def _plausible_val(v: int, obj: str) -> int:
                lo_b, hi_b = _object_pool(unit_mode).get(obj, (5, 50))
                return min(max(v, lo_b), hi_b)
            val_a = _plausible_val(rng.randint(lo, hi), obj_a)
            val_b = _plausible_val(rng.randint(lo, hi), obj_b)
            if val_a == val_b:
                b_lo, b_hi = _object_pool(unit_mode).get(obj_b, (5, 50))
                val_b = val_b + 1 if val_b < b_hi else val_b - 1
                val_b = min(max(val_b, b_lo), b_hi)
            ask_shorter = rng.random() < 0.5
            ans_val = min(val_a, val_b) if ask_shorter else max(val_a, val_b)
            other_val = max(val_a, val_b) if ask_shorter else min(val_a, val_b)
            comp_word = "shorter" if ask_shorter else "longer"
            dists = [other_val, ans_val + 5, max(1, ans_val - 5)]
            dists = [d for d in dists if d != ans_val][:3]
            return {
                "blank_target": "answer",
                "value_a": val_a,
                "value_b": val_b,
                "unit": unit,
                "unit_type": unit_mode,
                "task_type": "compare",
                "answer": ans_val,
                "distractors": dists,
                "question": (
                    f"{obj_a[0].upper()}{obj_a[1:]} is {val_a} {unit} long. "
                    f"{obj_b[0].upper()}{obj_b[1:]} is {val_b} {unit} long. "
                    f"Which length is {comp_word} in {unit}?"
                ),
            }

    if task_type == "compare_distance":
        # "Compare lengths AND distances" (mat_g1_mg_q2_1)
        if unit_mode == "non_standard":
            unit = rng.choice(["steps", "blocks", "hands"])
            l_min, l_max = 2, 9
            val_a = rng.randint(l_min, l_max)
            val_b = rng.randint(l_min, l_max)
            while val_b == val_a:
                val_b = rng.randint(l_min, l_max)
            ask_shorter = rng.random() < 0.5
            answer = min(val_a, val_b) if ask_shorter else max(val_a, val_b)
            other = max(val_a, val_b) if ask_shorter else min(val_a, val_b)
            unit_a = unit[:-1] if val_a == 1 and unit.endswith("s") and unit not in ("cm", "m") else unit
            unit_b = unit[:-1] if val_b == 1 and unit.endswith("s") and unit not in ("cm", "m") else unit
            dists = [other, answer + 1, max(1, answer - 1)]
            dists = [d for d in dists if d != answer][:3]
            comp_word = "shorter" if ask_shorter else "longer"
            return {
                "blank_target": "answer",
                "value_a": val_a,
                "value_b": val_b,
                "unit": unit,
                "unit_type": unit_mode,
                "task_type": "compare_distance",
                "answer": answer,
                "distractors": dists,
                "question": (
                    f"The distance from the bench to the tree is {val_a} {unit_a}. "
                    f"The distance from the gate to the tree is {val_b} {unit_b}. "
                    f"Which distance is {comp_word}?"
                ),
            }
        else:
            unit = "m"
            lo, hi = _standard_unit_bounds(bounds, "m", scalar)
            hi = max(hi, lo + 1)
            val_a = rng.randint(lo, hi)
            val_b = rng.randint(lo, hi)
            while val_b == val_a:
                val_b = rng.randint(lo, hi)
            ask_shorter = rng.random() < 0.5
            ans_val = min(val_a, val_b) if ask_shorter else max(val_a, val_b)
            other_val = max(val_a, val_b) if ask_shorter else min(val_a, val_b)
            comp_word = "shorter" if ask_shorter else "longer"
            dists = [other_val, ans_val + 5, max(1, ans_val - 5)]
            dists = [d for d in dists if d != ans_val][:3]
            return {
                "blank_target": "answer",
                "value_a": val_a,
                "value_b": val_b,
                "unit": unit,
                "unit_type": unit_mode,
                "task_type": "compare_distance",
                "answer": ans_val,
                "distractors": dists,
                "question": (
                    f"The distance from the bench to the tree is {val_a} m. "
                    f"The distance from the gate to the tree is {val_b} m. "
                    f"Which distance is {comp_word} in meters?"
                ),
            }

    if task_type == "choose_unit":
        # "Identify and use the appropriate unit (m or cm)" (mat_g2_mg_q2_1)
        cm_scale_items = [
            ("a pencil", 15), ("a crayon", 8), ("a book", 25),
            ("a shoe", 22), ("a spoon", 16), ("an eraser", 5),
            ("a notebook", 24), ("a pencil case", 20)
        ]
        m_scale_items = [
            ("a classroom", 8), ("a hallway", 20), ("a garden", 15),
            ("a basketball court", 28), ("a road", 50), ("a school fence", 30),
            ("a swimming pool", 25), ("a flagpole", 10)
        ]
        distance_pairs = [
            ("the school and the market", 200),
            ("your house and the church", 150),
            ("the classroom and the canteen", 40),
            ("the barangay hall and the plaza", 100),
            ("the gate and the library", 50),
            ("the bench and the playground", 30),
        ]
        
        mode = rng.choice(["item_unit", "distance_unit", "reasonableness_item", "reasonableness_dist"])
        if mode == "distance_unit":
            pair, dist_val = rng.choice(distance_pairs)
            return {
                "blank_target": "answer",
                "item": pair,
                "unit_type": "non_standard",
                "task_type": "choose_unit",
                "answer": "m",
                "distractors": ["cm", "either works", "neither works"],
                "question": f"Which unit is best to measure the distance between {pair}: centimeters (cm) or meters (m)?",
            }
        elif mode == "reasonableness_dist":
            pair, dist_val = rng.choice(distance_pairs)
            return {
                "blank_target": "answer",
                "item": pair,
                "unit_type": "non_standard",
                "task_type": "choose_unit",
                "answer": "m",
                "distractors": ["cm", "either works", "neither works"],
                "question": f"The distance between {pair} is about {dist_val} ___. Which unit makes the measurement reasonable: cm or m?",
            }
        elif mode == "reasonableness_item":
            use_cm = rng.random() < 0.5
            item, item_len = rng.choice(cm_scale_items if use_cm else m_scale_items)
            ans_u = "cm" if use_cm else "m"
            wrong_u = "m" if use_cm else "cm"
            return {
                "blank_target": "answer",
                "item": item,
                "unit_type": "non_standard",
                "task_type": "choose_unit",
                "answer": ans_u,
                "distractors": [wrong_u, "either works", "neither works"],
                "question": f"{item.capitalize()} has a length of about {item_len} ___. Which unit is correct: cm or m?",
            }
        else: # item_unit
            use_cm = rng.random() < 0.5
            item, _ = rng.choice(cm_scale_items if use_cm else m_scale_items)
            ans_u = "cm" if use_cm else "m"
            wrong_u = "m" if use_cm else "cm"
            q_frame = rng.choice([
                f"Which unit would you use to measure the length of {item}: centimeters (cm) or meters (m)?",
                f"Would you measure the length of {item} in centimeters (cm) or meters (m)?",
                f"What is the appropriate unit to measure the length of {item}: cm or m?"
            ])
            return {
                "blank_target": "answer",
                "item": item,
                "unit_type": "non_standard",
                "task_type": "choose_unit",
                "answer": ans_u,
                "distractors": [wrong_u, "either works", "neither works"],
                "question": q_frame,
            }

    if task_type == "convert":
        m_to_cm = rng.random() < 0.5
        lo, hi = 1, max(2, int(log_interpolate(1, 20, scalar)))
        if m_to_cm:
            val = rng.randint(lo, hi)
            from_u, to_u, answer = "m", "cm", val * 100
        else:
            val_m = rng.randint(lo, hi)
            val, from_u, to_u, answer = val_m * 100, "cm", "m", val_m
        return {
            "blank_target": "answer",
            "value": val,
            "from_unit": from_u,
            "to_unit": to_u,
            "unit_type": from_u,
            "task_type": "convert",
            "answer": answer,
            "question": f"Convert {val} {from_u} to {to_u}.",
        }

    if task_type == "estimate":
        # "Estimate length using meters or centimeters, and distance using meters" (mat_g2_mg_q2_2)
        estimate_distance = grade >= 2 and rng.random() < 0.5
        if estimate_distance:
            unit_mode = "m"
            unit_label = "m"
            pair = rng.choice([
                "the gate to the flagpole", "the classroom to the canteen",
                "the bench to the mango tree", "the front door to the school fence",
                "the library to the garden"
            ])
            lo, hi = 10, max(20, int(log_interpolate(10, 60, scalar)))
            length = rng.randint(lo, hi)
            round_unit = 10 if length >= 20 else 5
            if length % round_unit == 0:
                length += 1
            import math
            rounded = math.floor(length / round_unit + 0.5) * round_unit
            dists = [rounded + round_unit, max(round_unit, rounded - round_unit), rounded + 2 * round_unit]
            dists = [d for d in dists if d != rounded][:3]
            return {
                "blank_target": "answer",
                "length": length,
                "unit": unit_label,
                "unit_type": unit_mode,
                "task_type": "estimate",
                "round_to": round_unit,
                "answer": rounded,
                "distractors": dists,
                "question": f"The distance from {pair} is {length} m. About how many meters is that, rounded to the nearest {round_unit} m?",
            }
        else:
            use_cm = (requested_unit_type == "cm") or (requested_unit_type is None and rng.random() < 0.6)
            unit_mode = "cm" if use_cm else "m"
            unit_label = unit_mode
            if use_cm:
                obj_spec = rng.choice([
                    ("a piece of ribbon", 15, 30),
                    ("a notebook", 18, 26),
                    ("a wooden ruler", 15, 30),
                    ("a pencil case", 16, 22),
                    ("a storybook", 20, 28)
                ])
                obj, o_lo, o_hi = obj_spec
                length = rng.randint(o_lo, o_hi)
                round_unit = 10 if length >= 20 else 5
                if length % round_unit == 0:
                    length += 1
                import math
                rounded = math.floor(length / round_unit + 0.5) * round_unit
                dists = [rounded + round_unit, max(round_unit, rounded - round_unit), rounded + 2 * round_unit]
                dists = [d for d in dists if d != rounded][:3]
                return {
                    "blank_target": "answer",
                    "length": length,
                    "unit": unit_label,
                    "unit_type": unit_mode,
                    "task_type": "estimate",
                    "round_to": round_unit,
                    "answer": rounded,
                    "distractors": dists,
                    "question": f"{obj[0].upper()}{obj[1:]} measures {length} cm. About how many centimeters is that, rounded to the nearest {round_unit} cm?",
                }
            else:
                obj_spec = rng.choice([
                    ("a garden hose", 10, 25),
                    ("a school fence", 15, 35),
                    ("a garden path", 8, 22),
                    ("a classroom hallway", 12, 30)
                ])
                obj, o_lo, o_hi = obj_spec
                length = rng.randint(o_lo, o_hi)
                round_unit = 10 if length >= 20 else 5
                if length % round_unit == 0:
                    length += 1
                import math
                rounded = math.floor(length / round_unit + 0.5) * round_unit
                dists = [rounded + round_unit, max(round_unit, rounded - round_unit), rounded + 2 * round_unit]
                dists = [d for d in dists if d != rounded][:3]
                return {
                    "blank_target": "answer",
                    "length": length,
                    "unit": unit_label,
                    "unit_type": unit_mode,
                    "task_type": "estimate",
                    "round_to": round_unit,
                    "answer": rounded,
                    "distractors": dists,
                    "question": f"{obj[0].upper()}{obj[1:]} measures {length} m. About how many meters is that, rounded to the nearest {round_unit} m?",
                }

    if task_type == "distance_between":
        # "the distance between two objects" (mat_g1_mg_q2_0's second named sub-task)
        unit = rng.choice(["steps", "blocks", "hands", "paperclips"])
        max_u = {"steps": 8, "hands": 8, "blocks": 10, "paperclips": 12, "crayons": 6}.get(unit, 8)
        length = rng.randint(2, max_u)
        obj_a, obj_b = rng.sample(["a ball", "a box", "a chair", "a bag", "a desk", "a shelf"], 2)
        unit_word = unit[:-1] if length == 1 and unit.endswith("s") else unit
        dists = [d for d in [length + 1, max(1, length - 1), length + 2, length + 3] if d != length][:3]
        return {
            "blank_target": "answer",
            "length": length,
            "unit": unit,
            "unit_type": "non_standard",
            "task_type": "distance_between",
            "answer": length,
            "distractors": dists,
            "question": (
                f"{obj_a[0].upper()}{obj_a[1:]} and {obj_b} are placed apart. "
                f"The distance between them is ___ {unit_word}."
            ),
        }

    if task_type in ("solve_problems_non_standard", "solve_word_problem") and grade < 2:
        # "Solve problems involving lengths and distances using non-standard units" (mat_g1_mg_q2_2)
        problem_mode = rng.choice(["length_diff", "length_sum", "dist_diff", "dist_sum"])
        if problem_mode == "length_diff":
            obj_a, obj_b = rng.choice([
                ("a notebook", "a pencil"), ("a book", "a crayon"),
                ("a shoe", "an eraser"), ("a long ribbon", "a short ribbon"),
                ("a stick", "a spoon")
            ])
            unit = rng.choice(["paperclips", "blocks", "hands"])
            len_a = rng.randint(4, 9)
            len_b = rng.randint(1, len_a - 1)
            unit_b = unit[:-1] if len_b == 1 and unit.endswith("s") else unit
            ans = len_a - len_b
            q = f"{obj_a.capitalize()} is {len_a} {unit} long. {obj_b.capitalize()} is {len_b} {unit_b} long. How many {unit} longer is {obj_a} than {obj_b}?"
        elif problem_mode == "length_sum":
            obj_a, obj_b = rng.choice([
                ("a pencil", "an eraser"), ("a red ribbon", "a blue ribbon"),
                ("a stick", "a marker"), ("a spoon", "a fork")
            ])
            unit = rng.choice(["paperclips", "blocks"])
            len_a = rng.randint(2, 5)
            len_b = rng.randint(2, 5)
            ans = len_a + len_b
            q = f"{obj_a.capitalize()} is {len_a} {unit} long and {obj_b} is {len_b} {unit} long. If they are placed end to end, what is their total length in {unit}?"
        elif problem_mode == "dist_diff":
            loc_a, loc_b = rng.choice([
                ("the door", "the window"), ("the chair", "the bookshelf"),
                ("the reading corner", "the chalkboard"), ("the gate", "the bench")
            ])
            unit = "steps"
            len_a = rng.randint(5, 9)
            len_b = rng.randint(1, len_a - 1)
            unit_b = "step" if len_b == 1 else "steps"
            ans = len_a - len_b
            q = f"From the teacher's desk, it is {len_a} steps to {loc_a} and {len_b} {unit_b} to {loc_b}. How many steps farther is {loc_a} than {loc_b}?"
        else:  # dist_sum
            loc_a, loc_b = rng.choice([
                ("the desk to the door", "the door to the window"),
                ("the chair to the desk", "the desk to the shelf"),
                ("the gate to the tree", "the tree to the bench")
            ])
            unit = "steps"
            len_a = rng.randint(2, 5)
            len_b = rng.randint(2, 5)
            ans = len_a + len_b
            name = rng.choice(["Ana", "Ben", "Carlo", "Dan", "Elena", "Mia", "Leo"])
            q = f"{name} walked {len_a} steps from {loc_a}, and then {len_b} steps from {loc_b}. How many steps did {name} walk in all?"

        dists = [d for d in [ans + 1, max(1, ans - 1), ans + 2, ans + 3] if d != ans][:3]
        return {
            "blank_target": "answer",
            "length": ans,
            "unit": unit,
            "unit_type": "non_standard",
            "task_type": task_type,
            "answer": ans,
            "distractors": dists,
            "question": q,
        }

    if task_type == "equal_length":
        # "Identify and draw line segments of equal length using a ruler" (mat_g3_mg_q1_6)
        # Constrain to classroom ruler scale: 2 cm to 12 cm, strictly in cm.
        unit = "cm"
        sub_type = rng.choice(["ruler_read_equality", "draw_from_zero", "draw_from_offset", "identify_matching_segment"])
        len_a = rng.randint(2, 9)
        start_b = rng.randint(1, 5)

        if sub_type == "ruler_read_equality":
            is_equal = rng.random() < 0.5
            len_b = len_a if is_equal else (len_a + rng.choice([-2, -1, 1, 2]))
            if len_b < 1:
                len_b = len_a + 1
            is_equal = (len_a == len_b)
            end_b = start_b + len_b
            answer = "Yes" if is_equal else "No"
            return {
                "blank_target": "answer",
                "length": len_a,
                "value_a": len_a,
                "value_b": len_b,
                "unit": unit,
                "unit_type": "cm",
                "task_type": "equal_length",
                "sub_task": "ruler_read_equality",
                "answer": answer,
                "distractors": [
                    "No" if answer == "Yes" else "Yes",
                    "Only if both segments start at 0 cm",
                    "Cannot be determined without a set square",
                ],
                "question": (
                    f"On a ruler, Segment A starts at 0 cm and ends at {len_a} cm. "
                    f"Segment B starts at {start_b} cm and ends at {end_b} cm. "
                    f"Are Segment A and Segment B equal in length?"
                ),
            }

        if sub_type == "draw_from_zero":
            answer = len_a
            dists = [d for d in [len_a + 1, max(1, len_a - 1), len_a + 2, len_a + 3] if d != answer][:3]
            return {
                "blank_target": "answer",
                "length": len_a,
                "unit": unit,
                "unit_type": "cm",
                "task_type": "equal_length",
                "sub_task": "draw_from_zero",
                "answer": answer,
                "distractors": dists,
                "question": (
                    f"Segment A has a length of {len_a} cm. To draw Segment B equal in length "
                    f"using a ruler starting at the 0 cm mark, at which centimeter mark must Segment B end?"
                ),
            }

        if sub_type == "draw_from_offset":
            end_b = start_b + len_a
            answer = end_b
            dists = [d for d in [len_a, start_b, end_b + 1, end_b - 1] if d != answer][:3]
            return {
                "blank_target": "answer",
                "length": len_a,
                "unit": unit,
                "unit_type": "cm",
                "task_type": "equal_length",
                "sub_task": "draw_from_offset",
                "answer": answer,
                "distractors": dists,
                "question": (
                    f"Segment A is {len_a} cm long. If you use a ruler to draw Segment B equal in length "
                    f"starting at the {start_b} cm mark, at which centimeter mark on the ruler must Segment B end?"
                ),
            }

        # identify_matching_segment
        end_match = start_b + len_a
        answer = f"A segment starting at {start_b} cm and ending at {end_match} cm"
        distractors = [
            f"A segment starting at {start_b} cm and ending at {end_match + 2} cm",
            f"A segment starting at {start_b} cm and ending at {max(start_b + 1, end_match - 2)} cm",
            f"A segment starting at {start_b + 1} cm and ending at {end_match + 2} cm",
        ]
        return {
            "blank_target": "answer",
            "length": len_a,
            "unit": unit,
            "unit_type": "cm",
            "task_type": "equal_length",
            "sub_task": "identify_matching_segment",
            "answer": answer,
            "distractors": distractors,
            "question": (
                f"Segment A measures {len_a} cm on a ruler. Which of the following describes a line segment "
                f"that is equal in length to Segment A?"
            ),
        }

    if unit_mode == "non_standard":
        obj = rng.choice(["a pencil", "a spoon", "a notebook", "a ribbon", "a shoe", "a paintbrush"])
        unit = rng.choice(["paperclips", "blocks", "hands", "crayons"])
        max_u = {"paperclips": 10, "blocks": 8, "crayons": 5, "hands": 4}[unit]
        length = rng.randint(2, max_u)
        dists = [d for d in [length + 1, max(1, length - 1), length + 2, length + 3] if d != length][:3]
        return {
            "blank_target": "answer",
            "length": length,
            "unit": unit,
            "item": obj,
            "unit_type": "non_standard",
            "task_type": task_type,
            "answer": length,
            "distractors": dists,
            "question": f"How long is {obj}? Give your answer in {unit}.",
        }

    if task_type != "convert":
        lo, hi = _standard_unit_bounds(bounds, unit_mode, scalar)
        if unit_mode == "cm":
            lo = max(5, lo)
            hi = min(30, max(15, hi))
        length = rng.randint(lo, hi)
        result = {
            "blank_target": "answer",
            "length": length,
            "unit": unit_mode,
            "unit_type": unit_mode,
            "task_type": task_type,
            "answer": length,
        }
        if profile.get("context") == "word_problem" or task_type == "solve_word_problem":
            # "Solve problems involving length and distance" (mat_g2_mg_q2_3)
            # Alternate across 4 modes: length_sum, length_diff, dist_sum, dist_diff
            mode = rng.choice(["length_sum", "length_diff", "dist_sum", "dist_diff"])
            if mode in ("dist_sum", "dist_diff"):
                loc_a, loc_b, loc_c = rng.sample([
                    "the classroom", "the library", "the canteen",
                    "the playground", "the school gate", "the gym"
                ], 3)
                name = rng.choice(["Carlo", "Mia", "Ben", "Liza", "Dan", "Elena", "Renz"])
                dist_a = rng.randint(10, 45)
                dist_b = rng.randint(10, 45)
                if mode == "dist_sum":
                    loc_a, loc_b, loc_c = rng.sample([
                        "the classroom", "the library", "the canteen",
                        "the playground", "the school gate", "the gym"
                    ], 3)
                    ans = dist_a + dist_b
                    q = (
                        f"{name} walked {dist_a} m from {loc_a} to {loc_b}, and then walked {dist_b} m "
                        f"from {loc_b} to {loc_c}. What is the total distance {name} walked in meters?"
                    )
                else:
                    dest_a, dest_b = rng.sample([
                        "the classroom", "the library", "the canteen",
                        "the playground", "the gym", "the science lab", "the garden"
                    ], 2)
                    longer_val = max(dist_a, dist_b)
                    shorter_val = min(dist_a, dist_b)
                    if longer_val == shorter_val:
                        longer_val += 5
                    ans = longer_val - shorter_val
                    q = (
                        f"The distance from the school gate to {dest_a} is {longer_val} m. "
                        f"The distance from the school gate to {dest_b} is {shorter_val} m. "
                        f"How many meters farther is {dest_a} than {dest_b}?"
                    )
                dists = [ans + 5, max(1, ans - 5), ans + 10]
                dists = [d for d in dists if d != ans][:3]
                result.update({
                    "blank_target": "answer",
                    "length": ans,
                    "unit": "m",
                    "unit_type": "m",
                    "task_type": "solve_word_problem",
                    "answer": ans,
                    "distractors": dists,
                    "question": q,
                })
            else:
                obj_a, obj_b = rng.sample(sorted(_object_pool(unit_mode)), 2)
                def _plausible(v: int, obj: str) -> int:
                    lo_b, hi_b = _object_pool(unit_mode).get(obj, (5, 50))
                    return min(max(v, lo_b), hi_b)

                val_a = _plausible(length, obj_a)
                val_b = _plausible(rng.randint(lo, hi), obj_b)
                if val_a == val_b:
                    b_lo, b_hi = _object_pool(unit_mode).get(obj_b, (5, 50))
                    val_b = val_b + 1 if val_b < b_hi else val_b - 1
                    val_b = min(max(val_b, b_lo), b_hi)
                result["length"] = val_a
                result["length_b"] = val_b
                if mode == "length_sum":
                    ans = val_a + val_b
                    q = (
                        f"{obj_a[0].upper()}{obj_a[1:]} is {val_a} {unit_mode} long. "
                        f"{obj_b[0].upper()}{obj_b[1:]} is {val_b} {unit_mode} long. "
                        f"If they are placed end to end, what is their combined length in {unit_mode}?"
                    )
                else:
                    longer_obj, longer_val, shorter_obj, shorter_val = (
                        (obj_a, val_a, obj_b, val_b) if val_a > val_b else (obj_b, val_b, obj_a, val_a)
                    )
                    ans = longer_val - shorter_val
                    q = (
                        f"{longer_obj[0].upper()}{longer_obj[1:]} is {longer_val} {unit_mode} long. "
                        f"{shorter_obj[0].upper()}{shorter_obj[1:]} is {shorter_val} {unit_mode} long. "
                        f"How many {unit_mode} longer is {longer_obj} than {shorter_obj}?"
                    )
                dists = [ans + 5, max(1, ans - 5), ans + 10]
                dists = [d for d in dists if d != ans][:3]
                result.update({
                    "blank_target": "answer",
                    "answer": ans,
                    "distractors": dists,
                    "question": q,
                })
        return result

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
    task_type = values.get("task_type")
    cm_label = VOCAB_CENTIMETER.resolve(cumulative_vocab)
    m_label  = VOCAB_METER.resolve(cumulative_vocab)
    unit_label = {"cm": cm_label, "m": m_label}

    def _sing(unit: str, count: Any) -> str:
        """Non-standard units are all regular '-s' plurals; singularize for count==1."""
        return unit[:-1] if count == 1 and isinstance(unit, str) and unit.endswith("s") and unit not in ("cm", "m") else unit

    # task_type-specific branches must be checked before the generic
    # unit_type=="non_standard" fallback below -- "compare"/"equal_length"/
    # "distance_between" can all report unit_type="non_standard" (G1) too,
    # and the generic branch's "Count how many X fit along the object..."
    # hint doesn't match what those task types actually ask.
    if task_type in ("compare", "compare_distance"):
        val_a, val_b = values["value_a"], values["value_b"]
        unit_word = unit_label.get(unit_type, values.get("unit", "units"))
        return [
            f"Compare {val_a} {_sing(unit_word, val_a)} and {val_b} {_sing(unit_word, val_b)}.",
            f"{max(val_a, val_b)} is more than {min(val_a, val_b)}.",
            f"The longer {'distance' if task_type == 'compare_distance' else 'length'} is {values['answer']} {_sing(unit_word, values['answer'])}.",
        ]

    if task_type == "equal_length":
        val_a, val_b = values["value_a"], values["value_b"]
        unit_word = unit_label.get(unit_type, values.get("unit", "units"))
        return [
            f"Compare {val_a} {_sing(unit_word, val_a)} and {val_b} {_sing(unit_word, val_b)}.",
            "Equal length means the same number of units, not just a similar look.",
            f"{val_a} {_sing(unit_word, val_a)} {'equals' if val_a == val_b else 'does not equal'} {val_b} {_sing(unit_word, val_b)}, so the answer is {values['answer']}.",
        ]

    if task_type == "distance_between":
        unit = values.get("unit", "units")
        return [
            f"Count how many {unit} fit in the gap between the two objects.",
            "Make sure no gaps or overlaps between the units.",
            f"The distance between them is {values['answer']} {_sing(unit, values['answer'])}.",
        ]

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
