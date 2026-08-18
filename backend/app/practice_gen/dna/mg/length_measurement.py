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
            answer = max(val_a, val_b)
            unit_a = unit[:-1] if val_a == 1 and unit.endswith("s") and unit not in ("cm", "m") else unit
            unit_b = unit[:-1] if val_b == 1 and unit.endswith("s") and unit not in ("cm", "m") else unit
            return {
                "blank_target": "answer",
                "value_a": val_a,
                "value_b": val_b,
                "unit": unit,
                "unit_type": unit_mode,
                "task_type": "compare_distance",
                "answer": answer,
                "distractors": [val_a, val_b, min(val_a, val_b)],
                "question": (
                    f"The distance from the bench to the tree is {val_a} {unit_a}. "
                    f"The distance from the gate to the tree is {val_b} {unit_b}. "
                    f"Which distance is longer?"
                ),
            }

    if task_type == "choose_unit":
        # "Identify and use the appropriate unit (m or cm)" (mat_g2_mg_q2_1)
        # had no matching task_type at all -- this DNA only ever measured
        # in a unit already chosen for it, never asked the student to
        # choose one. cm-scale items are short objects; m-scale items are
        # longer distances/rooms -- picking between them is the actual
        # skill this competency names.
        cm_scale_items = ["a pencil", "a crayon", "a book", "a shoe", "a spoon"]
        m_scale_items = ["a classroom", "a hallway", "a garden", "a basketball court", "a road"]
        # The competency names TWO scenarios -- "the length of an object AND the
        # distance between two locations" -- and only the object half was ever
        # rendered: a blind reviewer found "the two-location distance scenario that
        # the same sentence of the competency requires does not show up once".
        # Half the items now ask about a distance between places, which is always
        # a metre-scale judgment at this grade.
        if rng.random() < 0.5:
            pair = rng.choice([
                "the school and the market", "your house and the church",
                "the classroom and the canteen", "the barangay hall and the plaza",
            ])
            return {
                "blank_target": "answer",
                "item": pair,
                "unit_type": "non_standard",
                "task_type": "choose_unit",
                "answer": "m",
                "distractors": ["cm", "either works", "neither works"],
                "question": (
                    f"Which unit would you use to measure the distance between "
                    f"{pair}: centimeters or meters?"
                ),
            }
        use_cm = rng.random() < 0.5
        item = rng.choice(cm_scale_items if use_cm else m_scale_items)
        answer_unit = "cm" if use_cm else "m"
        return {
            "blank_target": "answer",
            "item": item,
            "unit_type": "non_standard",  # no numeric measurement generated for this task
            "task_type": "choose_unit",
            "answer": answer_unit,
            # fmt_mcq requires 3 distractors and has no numeric fallback for
            # string answers -- the only genuine wrong unit choice here is
            # the other of cm/m, so pad with plausible-sounding but
            # non-numeric "reasoning" distractors rather than inventing
            # additional units this curriculum hasn't introduced yet.
            "distractors": [
                "cm" if answer_unit == "m" else "m",
                "either works",
                "neither works",
            ],
            "question": f"Which unit would you use to measure the length of {item}: centimeters or meters?",
        }

    if task_type == "convert":
        # VARIANTS_BY_DNA declares "convert" and the grade<2 guard above
        # already gates it, but no branch ever built its params -- the
        # DNA fell straight through to the read_measurement default at the
        # bottom, which sets "length"/"unit", not the "value"/"from_unit"/
        # "to_unit" keys _build_symbolic_question's convert stem reads, so
        # every convert render literally said "Convert None None to None."
        # (blind review of mat_g2_mg_q2_3 seed 604). m->cm is always exact
        # (x100); cm->m only draws cm values that are already a multiple of
        # 100, since K-3 hasn't met decimal lengths, so the answer stays a
        # whole number of meters either direction.
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
        # "Estimate length using meters or centimeters" (mat_g2_mg_q2_2)
        # also had no matching task_type -- same rounding-based estimation
        # framing already used for mass_capacity.py's fix this session.
        lo, hi = _standard_unit_bounds(bounds, unit_mode, scalar)
        # The label, not the enum. Every other branch resolves a real unit name for
        # non-standard mode; this one printed `unit_mode` straight into the stem, so
        # a Grade 1 sample read "An object measures 2 non_standard. About how many
        # non_standard is that...". The curriculum gate above now keeps this task at
        # Grade 2+, where unit_mode is always "cm" or "m", but the resolution stays
        # so the enum cannot leak again if that gate ever moves.
        # An estimate that rounds away the whole quantity is not an estimate: at
        # length 2 rounding to the nearest 10 gives 0, which a blind reviewer flagged
        # twice ("rounds 'An object measures 2 m' to the nearest 10, which collapses
        # to zero and does not model a realistic estimation scenario"). The rounding
        # unit is chosen from the magnitude instead, and the length floored, so the
        # rounded answer is always a real quantity.
        # "Estimate length using meters or centimeters, AND DISTANCE USING METERS"
        # (mat_g2_mg_q2_2). Only the object-length half was ever rendered -- a blind
        # reviewer found the distance clause had "zero items ... all 11 seeds are the
        # single template". Half the items now estimate a distance, and the
        # competency names metres for that case specifically, so the unit is fixed.
        estimate_distance = grade >= 2 and rng.random() < 0.5
        if estimate_distance:
            unit_mode = "m"
        elif grade >= 2 and requested_unit_type is None and rng.random() < 0.4:
            # "Estimate length using METERS OR CENTIMETERS, and distance using
            # meters" names three parts and the length half was always centimetres:
            # pinning metres to distances left "estimate length using meters"
            # with no item at all, which a blind reviewer scored as a coverage
            # FAIL -- "every metre item is a gate-to-flagpole distance". Only when
            # no unit is explicitly requested, so a pinned unit still wins.
            unit_mode = "m"
        # Resolved AFTER the distance override above, so the label follows the unit
        # actually in play. Every other branch resolves a real name for non-standard
        # mode; this one used to print the enum straight into the stem.
        unit_label = rng.choice(_NON_STANDARD_UNITS) if unit_mode == "non_standard" else unit_mode
        length = max(10, rng.randint(lo, hi))
        round_unit = 50 if length >= 100 else (10 if length >= 20 else 5)
        # A value already on the rounding boundary makes the estimate a no-op:
        # "An object measures 10 m. About how many m is that, rounded to the nearest
        # 5?" keys 10, and nothing was estimated. mass_capacity.py hit the same thing
        # and solved it the same way -- shift the value one off the boundary so there
        # is a real judgment to make.
        if length % round_unit == 0:
            length += 1
        # A `max(round_unit, ...)` floor here was mathematically wrong:
        # small values (e.g. 2 cm, rounding to the nearest 10) correctly
        # round DOWN to 0, not up to the rounding unit itself. Found by a
        # blind judgment review hand-verifying the rounding arithmetic
        # (seeds where length=2 and length=3 both wrongly gave 10).
        #
        # Python's round() uses round-half-to-even, not the round-half-up
        # convention elementary curricula teach (an exact-midpoint value
        # like 5, rounding to the nearest 10, must round UP to 10 -- round()
        # silently gives 0). The identical bug was caught in
        # mass_capacity.py's copy of this logic by a blind review hand-
        # verifying an exact-5 sample; fixed the same way here pre-emptively
        # rather than waiting to hit it by chance.
        import math
        rounded = math.floor(length / round_unit + 0.5) * round_unit
        return {
            "blank_target": "answer",
            "length": length,
            "unit": unit_label,
            "unit_type": unit_mode,
            "task_type": "estimate",
            "round_to": round_unit,
            "answer": rounded,
            "question": (
                (f"The distance from the gate to the flagpole is {length} {unit_label}. "
                 f"About how many {unit_label} is that, rounded to the nearest {round_unit}?")
                if estimate_distance else
                (f"An object measures {length} {unit_label}. "
                 f"About how many {unit_label} is that, rounded to the nearest {round_unit}?")
            ),
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
        length = rng.randint(lo, hi)
        result = {
            "blank_target": "answer",
            "length": length,
            "unit": unit_mode,
            "unit_type": unit_mode,
            "task_type": task_type,
            "answer": length,
        }
        if profile.get("context") == "word_problem":
            # Same fix as the non_standard branch above, applied to the
            # G2 standard-units (cm/m) path -- "Solve problems involving
            # length and distance" (mat_g2_mg_q2_3) is G2-only (standard
            # units), so it never reached the non_standard branch's fix.
            # Same self-answering defect as the non_standard branch above, and
            # the same fix: two measured objects and a difference to compute.
            obj_a, obj_b = rng.sample(sorted(_object_pool(unit_mode)), 2)
            # Small classroom objects (pencil, book, notebook, ruler, crayon)
            # are realistically 5-50cm; "a garden path" gets its own,
            # higher floor (30cm) but no cap, since it plausibly reaches
            # this unit's full difficulty-scaled ceiling (no cap/floor for
            # the "m" unit at all). Applied per-object and via an
            # INDEPENDENT second draw rather than deriving obj_b's length
            # from obj_a's (a prior version drew "shorter = randint(1,
            # length-1)", which ties obj_b's scale to obj_a's and breaks
            # down whenever obj_a is the uncapped garden path) -- blind
            # review round 2 found an oversized ruler this way, round 3 an
            # undersized notebook, round 4 an undersized garden path
            # ("6 cm long", shorter than a pencil).
            def _plausible(v: int, obj: str) -> int:
                # Per-object bands, not one shared clamp. The old rule floored every
                # classroom object at 5 and capped it at 50, so "a crayon" rendered
                # at 5, 8, 10, 21 and 49 cm across one sample set -- arithmetically
                # fine, but it trains wrong size benchmarks, which a blind reviewer
                # flagged as the one systematic defect left in this DNA. A pupil
                # meeting a 49 cm crayon learns the wrong thing about crayons.
                lo_b, hi_b = _object_pool(unit_mode).get(obj, (5, 50))
                return min(max(v, lo_b), hi_b)

            val_a = _plausible(length, obj_a)
            val_b = _plausible(rng.randint(lo, hi), obj_b)
            if val_a == val_b:
                # Step within obj_b's own band, not below it. `max(1, val_b - 1)`
                # walked straight past the floor -- a book at 17 cm and a ruler at
                # 14 cm, both a centimetre under their band, purely because the two
                # draws happened to tie.
                b_lo, b_hi = _object_pool(unit_mode).get(obj_b, (5, 50))
                val_b = val_b + 1 if val_b < b_hi else val_b - 1
                val_b = min(max(val_b, b_lo), b_hi)
            result["length"] = val_a
            result["length_b"] = val_b
            # "Solve problems involving length and distance" names both a
            # difference sub-case ("how many cm longer") and an additive one
            # implicitly (combining two measured lengths) -- 12/16 samples
            # reusing the identical difference template was flagged as a
            # variant_comprehensiveness FAIL (blind review, round 2/3).
            # Alternate between the two framings instead of always asking
            # for the difference.
            if rng.random() < 0.5:
                result["answer"] = val_a + val_b
                result["question"] = (
                    f"{obj_a[0].upper()}{obj_a[1:]} is {val_a} {unit_mode} long. "
                    f"{obj_b[0].upper()}{obj_b[1:]} is {val_b} {unit_mode} long. "
                    f"If they are placed end to end, what is their combined length in {unit_mode}?"
                )
            else:
                longer_obj, longer_val, shorter_obj, shorter_val = (
                    (obj_a, val_a, obj_b, val_b) if val_a > val_b else (obj_b, val_b, obj_a, val_a)
                )
                result["answer"] = longer_val - shorter_val
                result["question"] = (
                    f"{longer_obj[0].upper()}{longer_obj[1:]} is {longer_val} {unit_mode} long. "
                    f"{shorter_obj[0].upper()}{shorter_obj[1:]} is {shorter_val} {unit_mode} long. "
                    f"How many {unit_mode} longer is {longer_obj} than {shorter_obj}?"
                )
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
