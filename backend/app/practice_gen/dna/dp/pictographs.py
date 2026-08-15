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

# Thematic category sets with matched symbol, title, subject noun, and stem template
_THEMES = [
    {
        "categories": ["apples", "bananas", "mangoes", "grapes", "oranges", "strawberries"],
        "symbol": "🍎",
        "title": "Favorite Fruits",
        "subject": "fruits",
        "question_stem": "How many {cat} were counted?",
    },
    {
        "categories": ["cats", "dogs", "birds", "fish", "rabbits", "turtles"],
        "symbol": "🐾",
        "title": "Favorite Pets",
        "subject": "pets",
        "question_stem": "How many pupils chose {cat}?",
    },
    {
        "categories": ["red", "blue", "green", "yellow", "purple", "orange"],
        "symbol": "🎨",
        "title": "Favorite Colors",
        "subject": "colors",
        "question_stem": "How many pupils chose {cat}?",
    },
    {
        "categories": ["Math", "Science", "English", "Art", "PE", "Music"],
        "symbol": "📚",
        "title": "Favorite Subjects",
        "subject": "subjects",
        "question_stem": "How many pupils voted for {cat}?",
    },
    {
        "categories": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        "symbol": "📖",
        "title": "Books Read",
        "subject": "books read",
        "question_stem": "How many books were read on {cat}?",
    },
    {
        "categories": ["basketball", "volleyball", "swimming", "running", "soccer", "tennis"],
        "symbol": "⚽",
        "title": "Favorite Sports",
        "subject": "sports",
        "question_stem": "How many pupils play {cat}?",
    },
    {
        "categories": ["roses", "sunflowers", "tulips", "daisies", "orchids", "lilies"],
        "symbol": "🌸",
        "title": "Flowers in the Garden",
        "subject": "flowers",
        "question_stem": "How many {cat} are in the garden?",
    },
    {
        "categories": ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"],
        "symbol": "⭐",
        "title": "Stars Earned",
        "subject": "stars earned",
        "question_stem": "How many stars were earned by {cat}?",
    },
]
_CATEGORY_SETS = [t["categories"] for t in _THEMES]


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
    from backend.app.practice_gen.dna.base import extract_discrete_level, extract_continuous_scalar
    
    _scale_default = "no_scale" if grade == 1 else random.Random(seed).choice(["scale_2", "scale_5", "scale_10"])
    scale_type = extract_discrete_level(profile, "scale_type", ["no_scale", "scale_2", "scale_5", "scale_10"], _scale_default)
    if isinstance(profile.get("scale_type"), list):
        scale_type = rng.choice(profile["scale_type"])
    if scale_type == "with_or_without_scale":
        scale_type = rng.choice(["no_scale", "scale_2", "scale_5", "scale_10"])

    task_type = extract_discrete_level(profile, "task_type", ["read_single", "compare_two", "find_total", "find_difference", "organize_table", "present_data"], "read_value")
    if task_type == "present_or_organize":
        task_type = rng.choice(["present_data", "organize_table"])
    if task_type == "tabular_and_pictograph":
        task_type = rng.choice(["read_table", "read_value", "compare_two", "find_total", "find_difference"])
    if task_type == "read_or_compare":
        task_type = rng.choice(["read_value", "compare_two", "find_total", "find_difference"])

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

    # Number of categories: Grade 1 uses 3-4 categories; Grade 2 uses 4-6 categories
    if grade == 1:
        num_cats = 4 if profile.get("num_categories", 0) > 3 else 4
    else:
        num_cats = int(profile.get("num_categories", extract_continuous_scalar(profile, "difficulty_scalar", 0.5) * (bounds["num_categories_max"] - bounds["num_categories_min"]) + bounds["num_categories_min"]))
        num_cats = max(4, min(num_cats, 6))

    # Pick thematic set
    theme = rng.choice(_THEMES)
    cat_set = theme["categories"]
    categories = cat_set[:num_cats] if len(cat_set) >= num_cats else (cat_set * 2)[:num_cats]
    symbol = theme["symbol"]
    title = theme["title"]
    subject = theme["subject"]
    stem_template = theme["question_stem"]

    # Generate values (multiples of scale so pictograph pictures are whole numbers)
    val_lo = bounds["value_min"]
    val_hi_bound = bounds["value_max"]

    val_hi = int(profile.get("value_max", extract_continuous_scalar(profile, "difficulty_scalar", 0.5) * (val_hi_bound - val_lo) + val_lo))
    val_hi = max(val_lo, min(val_hi, val_hi_bound))

    # Cap unscaled pictograph values: Grade 1 max 5 per row; Grade 2 unscaled max 8 per row
    if grade == 1:
        val_hi = min(5, val_hi)
    elif scale == 1:
        val_hi = min(8, val_hi)

    import math
    min_mult = math.ceil(val_lo / scale) if scale > 0 else val_lo
    max_mult = val_hi // scale if scale > 0 else val_hi
    if max_mult < min_mult:
        max_mult = min_mult

    if max_mult <= min_mult:
        hard_ceiling = (5 if grade == 1 else (8 if scale == 1 else val_hi_bound // scale)) if scale > 0 else val_hi_bound
        if hard_ceiling > min_mult:
            max_mult = min(min_mult + 2, hard_ceiling)

    values = [rng.randint(min_mult, max_mult) * scale for _ in categories]

    # For Grade 1 finding total, ensure total sum is within Grade 1 addition range (<= 15)
    if grade == 1 and task_type == "find_total":
        while sum(values) > 15:
            max_i = values.index(max(values))
            if values[max_i] > 1:
                values[max_i] -= 1
            else:
                break

    # If all values are identical, vary one
    if len(set(values)) == 1:
        bumped = values[0] + scale
        if bumped > val_hi:
            bumped = max(val_lo, values[0] - scale)
        if bumped != values[0]:
            values[rng.randrange(len(values))] = bumped

    # If task_type is compare / compare_two, make sure there is a strictly unique maximum
    if task_type in ("compare", "compare_two"):
        max_v = max(values)
        if values.count(max_v) > 1:
            max_indices = [i for i, v in enumerate(values) if v == max_v]
            chosen_idx = rng.choice(max_indices)
            values[chosen_idx] += scale

    vp = {
        "categories": categories,
        "counts": values,
        "values": values,
        "scale": scale,
        "symbol": symbol,
        "title": title,
        "subject": subject,
        "stem_template": stem_template,
    }

    # Choose question target
    if task_type in ("read_value", "read_single"):
        q_idx = rng.randint(0, len(categories) - 1)
        answer = values[q_idx]
        question_category = categories[q_idx]
        vp["ask_category"] = question_category
        return {
            "blank_target": "answer",
            "visual_params": vp,
            "scale": scale,
            "question_category": question_category,
            "answer": answer,
            "stem_template": stem_template,
            "task_type": task_type,
        }

    if task_type in ("compare", "compare_two"):
        max_idx = values.index(max(values))
        answer_cat = categories[max_idx]
        return {
            "blank_target": "answer",
            "visual_params": vp,
            "scale": scale,
            "question_category": answer_cat,
            "answer": answer_cat,
            "stem_template": stem_template,
            "task_type": task_type,
        }

    if task_type == "find_total":
        return {
            "blank_target": "answer",
            "visual_params": vp,
            "scale": scale,
            "question_category": "total",
            "answer": sum(values),
            "stem_template": stem_template,
            "task_type": task_type,
        }

    if task_type == "find_difference":
        distinct = [
            (i, j)
            for i in range(len(values))
            for j in range(len(values))
            if i < j and values[i] != values[j]
        ]
        if not distinct:
            distinct = [(0, 1)]
            values[1] = values[0] + scale
        idx_a, idx_b = rng.choice(distinct)
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
            "stem_template": stem_template,
            "task_type": task_type,
        }

    if task_type == "present_data":
        # Present raw data into pictograph: the student draws symbols, so the keyed answer is the row symbol counts
        row_symbols = [v // scale for v in values]
        return {
            "blank_target": "answer",
            "visual_params": vp,
            "categories": categories,
            "values": values,
            "counts": values,
            "scale": scale,
            "question_category": "all",
            "answer": row_symbols,
            "stem_template": stem_template,
            "task_type": task_type,
        }

    if task_type == "read_table":
        # The data is displayed as a completed TABLE, not a pictograph, and the
        # student reads one category's count back out of it.
        q_idx = rng.randint(0, len(categories) - 1)
        return {
            "blank_target": "answer",
            "visual_params": vp,
            "categories": categories,
            "values": values,
            "scale": scale,
            "question_category": categories[q_idx],
            "answer": values[q_idx],
            "stem_template": stem_template,
            "task_type": task_type,
        }

    if task_type == "organize_table":
        # Given a pictograph, student fills in the table with counts
        return {
            "blank_target": "answer",
            "visual_params": vp,
            "categories": categories,
            "values": values,
            "scale": scale,
            "question_category": "all",
            "answer": values,
            "stem_template": stem_template,
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
        "stem_template": stem_template,
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

    if task_type == "read_table":
        chart_word = "table" if "table" in cumulative_vocab else "chart"
        cat = values.get("question_category", "the category")
        return [
            f"Look at the {chart_word} carefully.",
            f"Find the row labelled '{cat}'.",
            f"Read the number written next to it in the Count column.",
        ]

    hints = [f"Look at the {pg_label} carefully."]

    if scale > 1:
        if "key" in cumulative_vocab and "scale" in cumulative_vocab:
            hints.append(
                f"Each picture in the {key_label} stands for {scale} items ({scale_label} = {scale})."
            )
        else:
            hints.append(f"Each picture stands for {scale} items.")
    else:
        hints.append("Each picture stands for 1 item.")

    if task_type in ("read_value", "read_single"):
        cat = values.get("question_category", "the category")
        count = values.get("answer", "?")
        pics = count // scale if scale > 0 else count
        if scale > 1:
            hints.append(
                f"Count the pictures for '{cat}': there are {pics} picture(s) × {scale} = {count}."
            )
        else:
            hints.append(
                f"Count the pictures for '{cat}': there are {count} picture(s)."
            )
    elif task_type == "present_data":
        if scale > 1:
            hints.append(
                f"For each category, divide the number of items by {scale} to find how many pictures to draw."
            )
        else:
            hints.append("Draw 1 picture for each item in each category.")
    elif task_type == "find_total":
        hints.append("Add up the values for ALL categories to find the total.")
    elif task_type == "find_difference":
        hints.append("Read each category's value, then subtract the smaller from the larger.")
    elif task_type in ("compare", "compare_two"):
        hints.append("Compare the number of pictures in each row. The row with the most pictures has the greatest count.")
    elif task_type == "organize_table":
        chart_word = "table" if "table" in cumulative_vocab else "chart"
        if scale > 1:
            hints.append(f"Count the pictures in each row and multiply by {scale} to record each count in the {chart_word}.")
        else:
            hints.append(f"Count the items for each category and record them in the {chart_word}.")

    return hints



# ─── DNA instance ─────────────────────────────────────────────────────────────

PICTOGRAPHS_DNA = DNA(
    concept="pictographs",
    dna_type="visual_read",
    answer_formula=None,
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["bar_chart_read", "pictograph_read", "pictograph_set", "fill_in_table", "table_read"],
    requires_context=False,
    visual_home="BarChart",
    difficulty_axes=_DIFFICULTY_AXES,
)
