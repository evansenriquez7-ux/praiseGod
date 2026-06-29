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
    ["apples", "bananas", "mangoes", "grapes", "oranges", "strawberries"],
    ["cats", "dogs", "birds", "fish", "rabbits", "turtles"],
    ["Math", "Science", "English", "Art", "PE", "Music"],
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    ["basketball", "volleyball", "swimming", "running", "cycling", "tennis"],
    ["roses", "sunflowers", "tulips", "daisies", "lilies", "orchids"],
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
    difficulty_profile: Optional[Dict[str, Any]],
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

    from backend.app.practice_gen.dna.base import linear_interpolate, extract_discrete_level, extract_continuous_scalar
    
    orientation = extract_discrete_level(profile, "orientation", ["vertical", "horizontal"], "vertical")
    task_type   = extract_discrete_level(profile, "task_type", ["read_value", "compare_bars", "find_total", "find_difference", "find_most_least"], "read_value")
    scale_level = extract_discrete_level(profile, "scale", ["scale_5", "scale_10", "scale_20"], "scale_5")

    scale_map = {"scale_5": 5, "scale_10": 10, "scale_20": 20}
    scale = scale_map.get(scale_level, 5)

    # Number of categories
    num_cats = int(profile.get("num_categories", extract_continuous_scalar(profile, "difficulty_scalar", 0.5) * (bounds["num_categories_max"] - bounds["num_categories_min"]) + bounds["num_categories_min"]))
    num_cats = max(3, min(num_cats, 6))

    cat_set  = rng.choice(_CATEGORY_SETS)
    categories = cat_set[:num_cats] if len(cat_set) >= num_cats else (cat_set * 2)[:num_cats]

    val_lo = max(bounds["value_min"], scale)
    val_hi_bound = bounds["value_max"]

    val_hi = int(profile.get("value_max", extract_continuous_scalar(profile, "difficulty_scalar", 0.5) * (val_hi_bound - val_lo) + val_lo))
    val_hi = max(val_lo, min(val_hi, val_hi_bound))
    
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
        return {
        "blank_target": "answer",**base, "question_category": categories[q_idx], "answer": values[q_idx]}

    if task_type == "compare_bars":
        idx_a, idx_b = rng.sample(range(len(categories)), 2)
        answer_cat = categories[idx_a] if values[idx_a] >= values[idx_b] else categories[idx_b]
        return {
        "blank_target": "answer",
            **base,
            "compare_a": categories[idx_a],
            "compare_b": categories[idx_b],
            "answer": answer_cat,
        }

    if task_type == "find_total":
        return {
        "blank_target": "answer",**base, "question_category": "total", "answer": sum(values)}

    if task_type == "find_difference":
        idx_a, idx_b = rng.sample(range(len(categories)), 2)
        diff = abs(values[idx_a] - values[idx_b])
        return {
        "blank_target": "answer",
            **base,
            "compare_a": categories[idx_a],
            "compare_b": categories[idx_b],
            "answer": diff,
        }

    # find_most_least
    direction = rng.choice(["most", "least"])
    if direction == "most":
        m_val = max(values)
        if values.count(m_val) > 1:
            idx = values.index(m_val)
            values[idx] += scale
        best_idx = values.index(max(values))
        return {
        "blank_target": "answer",**base, "direction": "most", "answer": categories[best_idx]}
    else:
        m_val = min(values)
        if values.count(m_val) > 1:
            idx = values.index(m_val)
            if m_val - scale >= 0:
                values[idx] -= scale
            else:
                for i in range(len(values)):
                    if i != idx and values[i] == m_val:
                        values[i] += scale
        best_idx = values.index(min(values))
        return {
        "blank_target": "answer",**base, "direction": "least", "answer": categories[best_idx]}


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    bg_label    = VOCAB_BAR_GRAPH.resolve(cumulative_vocab)
    scale_label = VOCAB_SCALE.resolve(cumulative_vocab)
    vp          = values.get("visual_params", {})
    scale       = vp.get("scale", 5)
    task_type   = values.get("task_type", "read_value")
    orientation = vp.get("orientation", "vertical")

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
        if orientation == "vertical":
            adj = "tallest" if direction == "most" else "shortest"
        else:
            adj = "longest" if direction == "most" else "shortest"
        hints.append(f"Look for the {adj} bar.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

BAR_GRAPHS_DNA = DNA(
    concept="bar_graphs",
    dna_type="visual_read",
    answer_formula=None,
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["bar_chart_read", "bar_chart_set"],
    requires_context=False,
    visual_home="BarChart",
    difficulty_axes=_DIFFICULTY_AXES,
)
