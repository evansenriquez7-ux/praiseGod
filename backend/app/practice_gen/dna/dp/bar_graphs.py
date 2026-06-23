"""
DNA: Bar Graphs (Data & Probability)

Covers MATATAG grade 3 bar graph competencies.
  G3: horizontal and vertical bar graphs, solve problems using bar graph data
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
    "g3": {
        "num_categories_min": 3,
        "num_categories_max": 6,
        "value_min": 5,
        "value_max": 100,
        "scale_choices": [5, 10, 20],
    },
}

_CATEGORY_SETS = [
    ["apples", "bananas", "mangoes", "grapes", "oranges"],
    ["cats", "dogs", "birds", "fish", "rabbits"],
    ["Math", "Science", "English", "Art", "PE"],
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    ["basketball", "volleyball", "swimming", "running", "cycling"],
    ["roses", "sunflowers", "tulips", "daisies", "lilies"],
    ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"],
    ["January", "February", "March", "April", "May", "June"],
]


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="bar_graphs",
        label="dp_sum_avg",
        description="Summed all bar values instead of reading the single requested bar.",
    ),
    ErrorPattern(
        formula="None",
        required_concept="bar_graphs",
        label="dp_mean_median",
        description="Computed the mean instead of reading the actual bar value.",
    ),
    ErrorPattern(
        formula="None",
        required_concept="bar_graphs",
        label="dp_mode_mean",
        description="Identified the most frequent value (mode) instead of reading the bar for the target category.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES = [
    {
        "name": "num_categories",
        "label": "Number of Categories",
        "dim_type": "continuous",
        "default_min": 3,
        "default_max": 6,
        "divisions": 3,
    },
    {
        "name": "value_max",
        "label": "Maximum Value",
        "dim_type": "continuous",
        "default_min": 20,
        "default_max": 100,
        "divisions": 4,
    },
]


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_BAR_GRAPH = VocabGated(
    requires_vocab="bar graph",
    preferred="bar graph",
    fallback="graph with bars",
)
VOCAB_SCALE = VocabGated(
    requires_vocab="scale",
    preferred="scale",
    fallback="the numbers along the axis",
)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """
    Returns visual_params for the BarChart formatter (G3 only).
    {"categories": list, "values": list, "scale": int,
     "orientation": str, "task_type": str, "answer": int_or_str, ...}
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}
    bounds  = _PARAM_BOUNDS["g3"]

    orientation = profile.get("orientation", "vertical")
    task_type   = profile.get("task_type", "read_value")
    scale_level = profile.get("scale", "scale_5")

    scale_map = {"scale_5": 5, "scale_10": 10, "scale_20": 20}
    scale = scale_map.get(scale_level, 5)

    # Number of categories
    cat_min = bounds["num_categories_min"]
    cat_max = bounds["num_categories_max"]
    from backend.app.practice_gen.dna.base import linear_interpolate
    
    if "num_categories" in profile:
        num_cats = int(linear_interpolate(cat_min, cat_max, float(profile["num_categories"])))
    else:
        num_cats = rng.randint(cat_min, cat_max)
    
    num_cats = max(3, min(num_cats, 6))

    cat_set  = rng.choice(_CATEGORY_SETS)
    categories = cat_set[:num_cats] if len(cat_set) >= num_cats else (cat_set * 2)[:num_cats]

    val_lo = max(bounds["value_min"], scale)
    val_hi = bounds["value_max"]

    if "value_max" in profile:
        val_hi = max(val_lo, int(linear_interpolate(val_lo, val_hi, float(profile["value_max"]))))
    
    scalar = float(profile.get("difficulty_scalar", 0.5))
    if "value_max" not in profile:
        val_hi = max(val_lo, int(linear_interpolate(val_lo, val_hi, scalar)))
    
    import math
    min_mult = math.ceil(val_lo / scale) if scale > 0 else val_lo
    max_mult = val_hi // scale if scale > 0 else val_hi
    if max_mult < min_mult:
        max_mult = min_mult
    
    # Values are multiples of scale
    values = [rng.randint(min_mult, max_mult) * scale for _ in categories]

    vp = {
        "categories": categories,
        "values": values,
        "scale": scale,
        "orientation": orientation,
    }

    base = {
        "visual_params": vp,
        "task_type": task_type,
    }

    if task_type == "read_value":
        q_idx = rng.randint(0, len(categories) - 1)
        return {**base, "question_category": categories[q_idx], "answer": values[q_idx]}

    if task_type == "compare_bars":
        idx_a, idx_b = rng.sample(range(len(categories)), 2)
        answer_cat = categories[idx_a] if values[idx_a] >= values[idx_b] else categories[idx_b]
        return {
            **base,
            "compare_a": categories[idx_a],
            "compare_b": categories[idx_b],
            "answer": answer_cat,
        }

    if task_type == "find_total":
        return {**base, "question_category": "total", "answer": sum(values)}

    if task_type == "find_difference":
        idx_a, idx_b = rng.sample(range(len(categories)), 2)
        diff = abs(values[idx_a] - values[idx_b])
        return {
            **base,
            "compare_a": categories[idx_a],
            "compare_b": categories[idx_b],
            "answer": diff,
        }

    # find_most_least
    direction = rng.choice(["most", "least"])
    if direction == "most":
        best_idx = values.index(max(values))
        return {**base, "direction": "most", "answer": categories[best_idx]}
    else:
        best_idx = values.index(min(values))
        return {**base, "direction": "least", "answer": categories[best_idx]}


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    bg_label    = VOCAB_BAR_GRAPH.resolve(cumulative_vocab)
    scale_label = VOCAB_SCALE.resolve(cumulative_vocab)
    scale       = values.get("scale", 5)
    task_type   = values.get("task_type", "read_value")
    orientation = values.get("orientation", "vertical")

    axis = "vertical (y-axis)" if orientation == "vertical" else "horizontal (x-axis)"
    hints = [
        f"Look at the {bg_label} carefully.",
        f"The {scale_label} on the {axis} goes up by {scale}.",
    ]

    if task_type == "read_value":
        cat = values.get("question_category", "the category")
        hints.append(f"Find the bar for '{cat}' and read across to the scale.")
        hints.append(f"Answer: {values.get('answer', '?')}")
    elif task_type == "find_total":
        hints.append("Read each bar's value, then add them all together.")
    elif task_type in ("compare_bars", "find_difference"):
        a = values.get("compare_a", "A")
        b = values.get("compare_b", "B")
        hints.append(f"Read the bar for '{a}' and the bar for '{b}'.")
        if task_type == "find_difference":
            hints.append("Subtract the smaller value from the larger value.")
        else:
            hints.append("Compare: which bar is taller (or longer)?")
    elif task_type == "find_most_least":
        direction = values.get("direction", "most")
        hints.append(
            f"Look for the {'tallest' if direction == 'most' else 'shortest'} bar."
        )

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

BAR_GRAPHS_DNA = DNA(
    concept="bar_graphs",
    dna_type="visual_read",
    answer_formula=None,
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "numeric_input", "bar_chart_read", "bar_chart_set"],
    requires_context=False,
    visual_home="BarChart",
    difficulty_axes=_DIFFICULTY_AXES,
)
