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
    difficulty_profile: Optional[Dict[str, Any]],
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

    # No silent default. `profile.get("shape", "rectangle")` meant that every node
    # which never binds `shape` -- which is all of them -- rendered a rectangle and
    # nothing else: 200 of 200 samples on mat_g2_mg_q4_5, whose competency is "Find
    # the perimeter of TRIANGLES, SQUARES, AND RECTANGLES". Two of the three shapes
    # its own sentence names were unreachable. Same defect shape as area.py's, and
    # the same fix: vary per seed unless a profile pins it.
    shape     = profile.get("shape") or rng.choice(["rectangle", "square", "triangle"])
    task_type = profile.get("task_type", "find_perimeter")
    num_size  = profile.get("number_size", "small_numbers")
    scalar    = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))

    if task_type == "identify_and_measure":
        task_type = rng.choice(["identify_definition", "measure_tools", "find_perimeter"])

    if task_type == "identify_definition":
        item = rng.choice([
            {
                "question": "What is the perimeter of a plane figure?",
                "answer": "the total distance around the outside boundary of the figure",
                "distractors": [
                    "the amount of flat surface covered inside the figure",
                    "the length of only its longest side",
                    "the number of corners the figure has",
                ],
            },
            {
                "question": "To find the perimeter of a polygon or flat shape, what should you do?",
                "answer": "add the lengths of all its sides",
                "distractors": [
                    "multiply its length by its width",
                    "measure only the bottom side",
                    "subtract the shortest side from the longest side",
                ],
            },
            {
                "question": "Which statement correctly describes perimeter?",
                "answer": "It is the distance all the way around the outside edge of a shape.",
                "distractors": [
                    "It is the space occupied inside a 3D solid.",
                    "It is the weight of an object measured in grams.",
                    "It is the number of square units inside a rectangle.",
                ],
            },
        ])
        return {
            "blank_target": "answer",
            "task_type": "identify_definition",
            "question": item["question"],
            "answer": item["answer"],
            "distractors": item["distractors"],
            "shape": "rectangle",
            "context": "pure",
        }

    if task_type == "measure_tools":
        item_kind = rng.choice(["tool_choice", "ruler_measure"])
        if item_kind == "tool_choice":
            tool_q = rng.choice([
                {
                    "question": "Which measuring tool is most appropriate to measure the perimeter of a notebook cover?",
                    "answer": "a ruler",
                    "distractors": ["a thermometer", "a bathroom scale", "a clock"],
                },
                {
                    "question": "Which tool is best suited to measure the perimeter of a small picture frame in centimeters?",
                    "answer": "a ruler",
                    "distractors": ["a kitchen scale", "a measuring cup", "a calendar"],
                },
                {
                    "question": "To measure the perimeter of a classroom desk top, which tool should you use?",
                    "answer": "a ruler or measuring tape",
                    "distractors": ["a thermometer", "a weighing scale", "a beaker"],
                },
            ])
            return {
                "blank_target": "answer",
                "task_type": "measure_tools",
                "question": tool_q["question"],
                "answer": tool_q["answer"],
                "distractors": tool_q["distractors"],
                "shape": "rectangle",
                "context": "pure",
            }
        else:
            meas_shape = rng.choice(["square", "rectangle", "triangle"])
            if meas_shape == "square":
                s = rng.randint(3, 10)
                perim = 4 * s
                q = f"A student uses a ruler to measure the four sides of a square card. Each side is {s} cm. What is the perimeter?"
                return {
                    "blank_target": "answer",
                    "task_type": "measure_tools",
                    "shape": "square",
                    "question": q,
                    "answer": perim,
                    "distractors": sorted({d for d in [perim + 2, max(1, perim - 2), s * s, s + 4] if d != perim and d > 0}),
                    "sides": {"s": s},
                    "context": "word_problem",
                }
            elif meas_shape == "rectangle":
                l = rng.randint(4, 10)
                w = rng.randint(2, l - 1)
                perim = 2 * (l + w)
                q = f"Using a ruler, a student measures a rectangular photo card as {l} cm long and {w} cm wide. What is its perimeter?"
                return {
                    "blank_target": "answer",
                    "task_type": "measure_tools",
                    "shape": "rectangle",
                    "question": q,
                    "answer": perim,
                    "distractors": sorted({d for d in [perim + 2, max(1, perim - 2), l * w, l + w] if d != perim and d > 0}),
                    "sides": {"l": l, "w": w},
                    "context": "word_problem",
                }
            else:
                a = rng.randint(3, 6)
                b = rng.randint(3, 6)
                c_lo = max(2, abs(a - b) + 1)
                c_hi = min(8, a + b - 1)
                c = rng.randint(c_lo, c_hi)
                perim = a + b + c
                q = f"Using a ruler, the three sides of a triangular bookmark are measured as {a} cm, {b} cm, and {c} cm. What is its perimeter?"
                return {
                    "blank_target": "answer",
                    "task_type": "measure_tools",
                    "shape": "triangle",
                    "question": q,
                    "answer": perim,
                    "distractors": sorted({d for d in [perim + 1, max(1, perim - 1), perim + 2, max(1, perim - 2)] if d != perim and d > 0}),
                    "sides": {"a": a, "b": b, "c": c},
                    "context": "word_problem",
                }

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
                "blank_target": "answer",
                "shape": "square",
                "perimeter": perimeter,
                "task_type": "find_missing_side",
                "answer": s,
                "answer_formula": "perimeter / 4",
                "sides": sides,
            }
        return {
            "blank_target": "answer",
            "shape": "square",
            "sides": sides,
            "task_type": "find_perimeter",
            "answer": perimeter,
            "answer_formula": answer_formula_used,
            "context": profile.get("context", "pure"),
        }

    if shape == "rectangle":
        l = rng.randint(lo + 1, hi)
        w = rng.randint(lo, l - 1)
        perimeter = 2 * (l + w)
        sides = {"l": l, "w": w}
        if task_type == "find_missing_side" and grade >= 3:
            # Give perimeter and one side; find the other
            known = rng.choice(["l", "w"])
            missing = "w" if known == "l" else "l"
            known_val = sides[known]
            missing_val = sides[missing]
            return {
                "blank_target": "answer",
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
            "blank_target": "answer",
            "shape": "rectangle",
            "sides": sides,
            "task_type": "find_perimeter",
            "answer": perimeter,
            "answer_formula": "2 * (l + w)",
            "context": profile.get("context", "pure"),
        }

    # triangle
    # Three independent draws do not make a triangle. Nothing here enforced the
    # triangle inequality, so the DNA emitted figures that cannot exist -- a blind
    # reviewer caught "A triangle has sides 2 cm, 4 cm, and 7 cm. What is its
    # perimeter?" (2 + 4 < 7) and scored the node FAIL for asking the perimeter of
    # something that is not a plane figure. The arithmetic was right and the shape
    # was impossible, which is the sort of defect only a reader notices.
    #
    # The third side is drawn from the window the first two leave open:
    # |a - b| < c < a + b, intersected with the grade's own bounds.
    a = rng.randint(lo, hi)
    b = rng.randint(lo, hi)
    c_lo = max(lo, abs(a - b) + 1)
    c_hi = min(hi, a + b - 1)
    attempts = 0
    while c_lo > c_hi:
        # The window can close when the first two sides are far apart relative to the
        # bounds. Redraw them rather than clamping to an endpoint, which would bias
        # every such case onto the same degenerate triangle.
        attempts += 1
        if attempts > 20:
            raise ValueError(
                f"perimeter: cannot draw a valid triangle within bounds "
                f"[{lo}, {hi}] (grade={grade}, seed={seed}) after {attempts} attempts; "
                f"the side range is too narrow for the triangle inequality to hold."
            )
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        c_lo = max(lo, abs(a - b) + 1)
        c_hi = min(hi, a + b - 1)
    c = rng.randint(c_lo, c_hi)
    if not (a + b > c and a + c > b and b + c > a):
        raise ValueError(
            f"perimeter: triangle inequality violated by sides {a}, {b}, {c} "
            f"(grade={grade}, seed={seed}). The draw above is supposed to make this "
            f"unreachable; if it fires, the window arithmetic is wrong."
        )
    perimeter = a + b + c
    sides = {"a": a, "b": b, "c": c}
    if task_type == "find_missing_side" and grade >= 3:
        missing_side = rng.choice(["a", "b", "c"])
        known_sides = {k: v for k, v in sides.items() if k != missing_side}
        missing_val = sides[missing_side]
        return {
        "blank_target": "answer",
            "shape": "triangle",
            "perimeter": perimeter,
            "known_sides": known_sides,
            "task_type": "find_missing_side",
            "answer": missing_val,
            "answer_formula": "perimeter - sum(known_sides)",
            "sides": sides,
        }
    return {
        "blank_target": "answer",
        "shape": "triangle",
        "sides": sides,
        "task_type": "find_perimeter",
        "answer": perimeter,
        "answer_formula": "a + b + c",
        "context": profile.get("context", "pure"),
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
    dna_type="algorithmic",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "cloze", "numeric_input"],
    requires_context=True,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
