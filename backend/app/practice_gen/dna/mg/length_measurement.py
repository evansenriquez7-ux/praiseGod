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
    if task_type not in ("read_measurement", "compare", "convert", "estimate", "choose_unit"):
        raise ValueError(
            f"generate_params (length_measurement): unknown task_type '{task_type}'."
        )
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
        # At the bottom of the difficulty window the mapped ceiling collapses onto
        # the floor (log_interpolate(1, 100, 0.0) == 1), and the "keep drawing
        # until they differ" loops below then spin forever — a real hang, not a
        # slow path. One unit of headroom is the domain minimum for the task.
        if unit_mode == "non_standard":
            unit = rng.choice(_NON_STANDARD_UNITS)
            l_min, l_max = bounds.get("length_min", 1), bounds.get("length_max", 100)
            l_max_current = max(l_min + 1, int(log_interpolate(l_min, l_max, scalar)))
            val_a = rng.randint(l_min, l_max_current)
            val_b = rng.randint(l_min, l_max_current)
            while val_b == val_a:
                val_b = rng.randint(l_min, l_max_current)
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

    if task_type == "choose_unit":
        # "Identify and use the appropriate unit (m or cm)" (mat_g2_mg_q2_1)
        # had no matching task_type at all -- this DNA only ever measured
        # in a unit already chosen for it, never asked the student to
        # choose one. cm-scale items are short objects; m-scale items are
        # longer distances/rooms -- picking between them is the actual
        # skill this competency names.
        cm_scale_items = ["a pencil", "a crayon", "a book", "a shoe", "a spoon"]
        m_scale_items = ["a classroom", "a hallway", "a garden", "a basketball court", "a road"]
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

    if task_type == "estimate":
        # "Estimate length using meters or centimeters" (mat_g2_mg_q2_2)
        # also had no matching task_type -- same rounding-based estimation
        # framing already used for mass_capacity.py's fix this session.
        lo, hi = _standard_unit_bounds(bounds, unit_mode, scalar)
        length = rng.randint(lo, hi)
        round_unit = 10 if length < 100 else 50
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
            "unit": unit_mode,
            "unit_type": unit_mode,
            "task_type": "estimate",
            "round_to": round_unit,
            "answer": rounded,
            "question": (
                f"An object measures {length} {unit_mode}. "
                f"About how many {unit_mode} is that, rounded to the nearest {round_unit}?"
            ),
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

        result = {
            "blank_target": "answer",
            "length": length,
            "unit": unit,
            "unit_type": "non_standard",
            "task_type": task_type,
            "tick_step": tick_step,
            "answer": length,
        }
        if profile.get("context") == "word_problem":
            # "Solve problems involving lengths ... using non-standard
            # units" (mat_g1_mg_q2_2) previously had no word-problem
            # framing at all -- this DNA has no "context" handling
            # anywhere, so it always rendered the bare read-measurement
            # stem ("Measure the object. Its length is ___ paperclips.")
            # regardless of the competency asking for solved *problems*.
            # A self-contained narrative here (rather than routing through
            # the shared spine system, whose length spines expect a second
            # compared/summed value this single-measurement task doesn't
            # have) keeps this fix narrow and avoids the blank_target /
            # slot-alias mismatches that pattern has caused elsewhere this
            # session.
            # "a table" deliberately excluded: "table" is reserved
            # NOT_YET_KNOWN vocabulary (data-table terminology introduced
            # later), unrelated to this furniture sense but still caught by
            # the vocab-gating checker's literal word match.
            # "a ruler" excluded for a stronger reason: this branch is the G1
            # non-standard-units path, and "ruler" is genuinely NOT_YET_KNOWN
            # at mat_g1_mg_q2_0 — a G1 pupil measuring in steps/paperclips has
            # not met the ruler yet. It stays available on the G2 standard-units
            # branch below, where the node introduces it.
            # The first version of this narrative stated the measurement and then
            # asked for it back ("It measured 5 paperclips long. How long is a
            # book in paperclips?"), so the answer was the only number on the
            # page and could be copied without measuring or reasoning
            # (validate_matrix §1F). Give the student two measured objects and
            # ask for the difference: that needs the stated lengths *and* an
            # operation, and "solve problems involving lengths" is what the
            # competency asks for in the first place.
            obj_a, obj_b = rng.sample(
                ["a pencil", "a book", "a notebook", "a shoe", "a crayon"], 2
            )
            if length < 2:
                length = 2
                result["length"] = length
            shorter = rng.randint(1, length - 1)
            result["length_b"] = shorter
            result["answer"] = length - shorter
            result["question"] = (
                f"{obj_a[0].upper()}{obj_a[1:]} is {length} {unit} long. "
                f"{obj_b[0].upper()}{obj_b[1:]} is {shorter} {unit} long. "
                f"How many {unit} longer is {obj_a} than {obj_b}?"
            )
        return result

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
            obj_a, obj_b = rng.sample(
                ["a pencil", "a book", "a notebook", "a ruler", "a garden path", "a crayon"], 2
            )
            if length < 2:
                length = 2
                result["length"] = length
            shorter = rng.randint(1, length - 1)
            result["length_b"] = shorter
            result["answer"] = length - shorter
            result["question"] = (
                f"{obj_a[0].upper()}{obj_a[1:]} is {length} {unit_mode} long. "
                f"{obj_b[0].upper()}{obj_b[1:]} is {shorter} {unit_mode} long. "
                f"How many {unit_mode} longer is {obj_a} than {obj_b}?"
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
