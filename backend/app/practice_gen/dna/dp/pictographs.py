"""
DNA: Pictographs (Data & Probability)

Covers MATATAG grades 1–2 pictograph competencies.
  G1: pictograph WITHOUT scale (each picture = 1 item)
  G2: pictograph WITH scale (each picture = N items)
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
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {
        "num_categories_min": 3,
        "num_categories_max": 5,
        "value_min": 1,
        "value_max": 10,
        "scale": 1,
    },
    "g2": {
        "num_categories_min": 3,
        "num_categories_max": 6,
        "value_min": 2,
        "value_max": 50,
        "scale_choices": [2, 5, 10],
    },
}

# Sample category sets for variety
_CATEGORY_SETS = [
    ["apples", "bananas", "mangoes", "grapes"],
    ["cats", "dogs", "birds", "fish"],
    ["red", "blue", "green", "yellow"],
    ["Math", "Science", "English", "Art", "PE"],
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    ["basketball", "volleyball", "swimming", "running"],
    ["roses", "sunflowers", "tulips", "daisies"],
    ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"],
]


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="pictographs",
        label="dp_sum_avg",
        description="Gave the total of all values instead of reading the single requested category.",
    ),
    ErrorPattern(
        formula="None",
        required_concept="pictographs",
        label="dp_mean_median",
        description="Computed the mean (average) instead of reading the actual value from the graph.",
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
        "divisions": 4,
    },
    {
        "name": "value_max",
        "label": "Maximum Value per Category",
        "dim_type": "continuous",
        "default_min": 5,
        "default_max": 50,
        "divisions": 5,
    },
]


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_PICTOGRAPH = VocabGated(
    requires_vocab="pictograph",
    preferred="pictograph",
    fallback="picture graph",
)
VOCAB_SCALE = VocabGated(
    requires_vocab="scale",
    preferred="scale",
    fallback="what each picture stands for",
)
VOCAB_KEY = VocabGated(
    requires_vocab="key",
    preferred="key",
    fallback="the legend that shows what each picture means",
)
VOCAB_TALLY = VocabGated(
    requires_vocab="tally",
    preferred="tally",
    fallback="count marks",
)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Returns visual_params for the BarChart (pictograph) formatter.
    {"categories": list, "values": list, "scale": int,
     "question_category": str, "answer": int, "task_type": str}
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}
    g_key = f"g{max(1, min(grade, 2))}"
    bounds = _PARAM_BOUNDS[g_key]

    scale_type    = profile.get("scale_type", "no_scale" if grade == 1 else "scale_2")
    task_type     = profile.get("task_type", "read_value")

    # Determine scale
    if scale_type == "no_scale" or grade == 1:
        scale = 1
    elif scale_type == "scale_2":
        scale = 2
    elif scale_type == "scale_5":
        scale = 5
    elif scale_type == "scale_10":
        scale = 10
    else:
        scale = 1

    # Number of categories
    cat_min = bounds["num_categories_min"]
    cat_max = bounds["num_categories_max"]
    from backend.app.practice_gen.dna.base import linear_interpolate
    
    if "num_categories" in profile:
        num_cats = int(linear_interpolate(cat_min, cat_max, float(profile["num_categories"])))
    else:
        num_cats = rng.randint(cat_min, cat_max)

    num_cats = max(3, min(num_cats, 6))

    # Pick categories
    cat_set = rng.choice(_CATEGORY_SETS)
    categories = cat_set[:num_cats] if len(cat_set) >= num_cats else (cat_set * 2)[:num_cats]

    # Generate values (multiples of scale so pictograph pictures are whole numbers)
    val_lo = bounds["value_min"]
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
    
    values = [rng.randint(min_mult, max_mult) * scale for _ in categories]
    vp = {
        "categories": categories,
        "counts": values,
        "scale": scale,
    }

    # Choose question target
    if task_type in ("read_value", "read_single", "present_data"):
        q_idx = rng.randint(0, len(categories) - 1)
        answer = values[q_idx]
        question_category = categories[q_idx]
        vp["ask_category"] = question_category
        return {
        "blank_target": "answer",
            "visual_params": vp,
            "question_category": question_category,
            "answer": answer,
            "task_type": task_type,
        }

    if task_type in ("compare", "compare_two"):
        idx_a, idx_b = rng.sample(range(len(categories)), 2)
        # answer is the category name with more items
        answer_cat = categories[idx_a] if values[idx_a] >= values[idx_b] else categories[idx_b]
        return {
        "blank_target": "answer",
            "visual_params": vp,
            "question_category": f"{categories[idx_a]} vs {categories[idx_b]}",
            "compare_a": categories[idx_a],
            "compare_b": categories[idx_b],
            "answer": answer_cat,
            "task_type": task_type,
        }

    if task_type == "find_total":
        return {
        "blank_target": "answer",
            "visual_params": vp,
            "question_category": "total",
            "answer": sum(values),
            "task_type": task_type,
        }

    if task_type == "find_difference":
        idx_a, idx_b = rng.sample(range(len(categories)), 2)
        diff = abs(values[idx_a] - values[idx_b])
        return {
        "blank_target": "answer",
            "visual_params": vp,
            "categories": categories,
            "values": values,
            "scale": scale,
            "question_category": f"{categories[idx_a]} and {categories[idx_b]}",
            "compare_a": categories[idx_a],
            "compare_b": categories[idx_b],
            "answer": diff,
            "task_type": task_type,
        }
        
    if task_type == "organize_table":
        # Table expects all values or something similar, answer can just be the entire dict of categories/values
        # Or an interaction where they fill in the entire table
        return {
        "blank_target": "answer",
            "visual_params": vp,
            "categories": categories,
            "values": values,
            "scale": scale,
            "question_category": "all",
            "answer": values,
            "task_type": task_type,
        }
    
    # fallback
    return {
        "blank_target": "answer",
        "visual_params": vp,
        "categories": categories,
        "values": values,
        "scale": scale,
        "question_category": categories[0],
        "answer": values[0],
        "task_type": task_type,
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    pg_label    = VOCAB_PICTOGRAPH.resolve(cumulative_vocab)
    scale_label = VOCAB_SCALE.resolve(cumulative_vocab)
    key_label   = VOCAB_KEY.resolve(cumulative_vocab)
    scale       = values.get("scale", 1)
    task_type   = values.get("task_type", "read_value")

    hints = [f"Look at the {pg_label} carefully."]

    if scale > 1:
        hints.append(
            f"Each picture in the {key_label} stands for {scale} items ({scale_label} = {scale})."
        )
    else:
        hints.append("Each picture stands for 1 item.")

    if task_type in ("read_value", "read_single", "present_data"):
        cat = values.get("question_category", "the category")
        count = values.get("answer", "?")
        pics = count // scale if scale > 0 else count
        hints.append(
            f"Count the pictures for '{cat}': there are {pics} picture(s) × {scale} = {count}."
        )
    elif task_type == "find_total":
        hints.append("Add up the values for ALL categories to find the total.")
    elif task_type == "find_difference":
        hints.append("Read each category's value, then subtract the smaller from the larger.")
    elif task_type in ("compare", "compare_two"):
        hints.append("Compare the two category values. The one with more pictures has more items.")
    elif task_type == "organize_table":
        hints.append(f"Count the items for each category and record them in the table.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

PICTOGRAPHS_DNA = DNA(
    concept="pictographs",
    dna_type="visual_read",
    answer_formula=None,
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "numeric_input", "bar_chart_read", "pictograph_read", "pictograph_set", "fill_in_table"],
    requires_context=False,
    visual_home="BarChart",
    difficulty_axes=_DIFFICULTY_AXES,
)
