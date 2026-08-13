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
    ["apples", "bananas", "mangoes", "grapes", "oranges", "strawberries"],
    ["cats", "dogs", "birds", "fish", "rabbits", "turtles"],
    ["red", "blue", "green", "yellow", "purple", "orange"],
    ["Math", "Science", "English", "Art", "PE", "Music"],
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    ["basketball", "volleyball", "swimming", "running", "soccer", "tennis"],
    ["roses", "sunflowers", "tulips", "daisies", "orchids", "lilies"],
    ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"],
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
    from backend.app.practice_gen.dna.base import linear_interpolate, extract_discrete_level, extract_continuous_scalar
    
    # G2's own default ("scale_2") was fixed regardless of what the node's
    # profile requested, so "...with or without scale" (mat_g2_dp_q3_1) and
    # "...using a scale" (mat_g2_dp_q3_0) both silently rendered scale=2
    # every single sample (blind review: 0 of 5+ samples ever varied the
    # scale factor). Vary across the declared scale options when unbound --
    # extract_discrete_level only falls back to this default when
    # "scale_type" is absent from profile entirely, so an explicit request
    # still wins.
    _scale_default = "no_scale" if grade == 1 else random.Random(seed).choice(["scale_2", "scale_5", "scale_10"])
    scale_type    = extract_discrete_level(profile, "scale_type", ["no_scale", "scale_2", "scale_5", "scale_10"], _scale_default)
    if scale_type == "with_or_without_scale":
        # registry.py sentinel for "...in a pictograph WITH OR WITHOUT scale"
        # (mat_g2_dp_q3_1). Leaving it unbound did not cover both cases: the
        # G2 default above only ever draws from scale_2/5/10, so the "without"
        # half of the node's own sentence was unreachable no matter the seed.
        scale_type = rng.choice(["no_scale", "scale_2", "scale_5", "scale_10"])
    # "read_table" is deliberately NOT in this list. extract_discrete_level maps a
    # float scalar onto it by index -- idx = round(scalar * (len - 1)) -- so adding
    # a seventh entry silently re-points every scalar-driven node: 0.5 moves from
    # find_total to find_difference, and 1.0 from present_data to read_table.
    # read_table only ever arrives as a STRING (from the registry sentinel below,
    # or from VARIANTS_BY_DNA during the exhaustive sweep), and strings are
    # returned verbatim, so it stays reachable without disturbing the ladder.
    task_type     = extract_discrete_level(profile, "task_type", ["read_single", "compare_two", "find_total", "find_difference", "organize_table", "present_data"], "read_value")
    if task_type == "present_or_organize":
        # registry.py sentinel for "Present raw data ... in a pictograph with a
        # scale, or vice versa" (mat_g2_dp_q3_0): the sentence names both
        # directions, so alternate between building the pictograph from raw data
        # and reading a pictograph back into a table, per seed.
        task_type = rng.choice(["present_data", "organize_table"])
    if task_type == "tabular_and_pictograph":
        # registry.py sentinel for "Interpret data IN TABULAR FORM AND in a
        # pictograph with or without scale" (mat_g2_dp_q3_1). The sentence names
        # two displays, and only the pictograph one was ever rendered -- a blind
        # reviewer: "Every one of the twelve sampled items opens with 'Look at the
        # picture graph'; none references reading a table."
        # "read_table" shows a completed table and asks for one count back; it is
        # served by the new "read" mode of fill_in_table (the only formatter in
        # the pipeline that draws a data table at all -- until now it could only
        # blank one out, which is the "organize" skill, not the "interpret" one).
        task_type = rng.choice(["read_table", "read_value", "compare_two"])
    if task_type == "read_or_compare":
        # registry.py sentinel for "Interpret data in tabular form and in
        # a pictograph..." (mat_g2_dp_q3_1): alternate between reading a
        # single category and genuinely comparing two, per seed.
        # "read_value" (not VARIANTS_BY_DNA's declared "read_single",
        # which no formatter in FORMATTER_VARIANT_SUPPORT actually
        # recognizes -- a separate pre-existing name mismatch) is this
        # DNA's real default/fallthrough branch.
        task_type = rng.choice(["read_value", "compare_two"])

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
    num_cats = int(profile.get("num_categories", extract_continuous_scalar(profile, "difficulty_scalar", 0.5) * (bounds["num_categories_max"] - bounds["num_categories_min"]) + bounds["num_categories_min"]))
    num_cats = max(3, min(num_cats, 6))

    # Pick categories
    cat_set = rng.choice(_CATEGORY_SETS)
    categories = cat_set[:num_cats] if len(cat_set) >= num_cats else (cat_set * 2)[:num_cats]

    # Generate values (multiples of scale so pictograph pictures are whole numbers)
    val_lo = bounds["value_min"]
    val_hi_bound = bounds["value_max"]

    val_hi = int(profile.get("value_max", extract_continuous_scalar(profile, "difficulty_scalar", 0.5) * (val_hi_bound - val_lo) + val_lo))
    val_hi = max(val_lo, min(val_hi, val_hi_bound))


    import math
    min_mult = math.ceil(val_lo / scale) if scale > 0 else val_lo
    max_mult = val_hi // scale if scale > 0 else val_hi
    if max_mult < min_mult:
        max_mult = min_mult

    # The upper value bound is interpolated from the difficulty scalar, but the
    # counts must be whole multiples of the scale -- so a large scale against a
    # modest bound leaves exactly one usable multiple (scale 10 with val_hi 19
    # gives min_mult == max_mult == 1) and EVERY category renders the same count.
    # That is a flat graph: one picture per row, nothing to compare, and the scale
    # itself never exercised. A blind reviewer caught it as "every category the
    # value 10 at a scale of 10". Widen to the grade's own hard ceiling, which is
    # the bound the curriculum sets, rather than the interpolated one.
    if max_mult <= min_mult:
        hard_ceiling = val_hi_bound // scale if scale > 0 else val_hi_bound
        if hard_ceiling > min_mult:
            max_mult = min(min_mult + 2, hard_ceiling)


    values = [rng.randint(min_mult, max_mult) * scale for _ in categories]

    # "Which has more: A or B?" has no correct answer when A and B hold the same
    # count, and 51 of 249 comparison items rendered exactly that -- the keyed
    # category was simply whichever the sampler drew first (the branch below used
    # >=), so a pupil who read the graph correctly was marked wrong. A comparison
    # needs at least two distinct counts to compare; if the value range is too
    # narrow to give one, that is a parameter error and must be loud, not silently
    # served to a student.
    if task_type in ("compare", "compare_two") and len(set(values)) == 1:
        bumped = values[0] + scale
        if bumped > val_hi:
            bumped = values[0] - scale
        if bumped < val_lo or bumped == values[0]:
            raise ValueError(
                f"pictographs: cannot build a comparison for node grade {grade} -- every "
                f"category must take the same value {values[0]} (val range {val_lo}..{val_hi}, "
                f"scale {scale}), so 'which has more' has no answer. seed={seed}"
            )
        values[rng.randrange(len(values))] = bumped
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
            # "scale" was missing from this branch (and only this class of branch),
            # so generate_hints fell back to values.get("scale", 1) and told the
            # pupil "Each picture stands for 1 item" on 76 items whose own stem
            # announced "Each 🍎 = 5", spelling out "× 1 =" in the worked count.
            "scale": scale,
            "question_category": question_category,
            "answer": answer,
            "task_type": task_type,
        }

    if task_type in ("compare", "compare_two"):
        # Only pairs that actually differ: a tie makes the stem unanswerable, and
        # rng.sample() alone had no way to exclude one.
        distinct = [
            (i, j)
            for i in range(len(values))
            for j in range(len(values))
            if i < j and values[i] != values[j]
        ]
        idx_a, idx_b = rng.choice(distinct)
        if rng.random() < 0.5:
            idx_a, idx_b = idx_b, idx_a
        answer_cat = categories[idx_a] if values[idx_a] > values[idx_b] else categories[idx_b]
        return {
        "blank_target": "answer",
            "visual_params": vp,
            "scale": scale,
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
            "scale": scale,
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
        
    if task_type == "read_table":
        # The data is displayed as a completed TABLE, not a pictograph, and the
        # student reads one category's count back out of it. "values" is repeated
        # at the top level because fill_in_table reads counts from that key,
        # while the pictograph formatters read them from visual_params["counts"].
        q_idx = rng.randint(0, len(categories) - 1)
        return {
            "blank_target": "answer",
            "visual_params": vp,
            "categories": categories,
            "values": values,
            "scale": scale,
            "question_category": categories[q_idx],
            "answer": values[q_idx],
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

    if task_type == "read_table":
        # A table carries no symbol and no scale, so the pictograph hints below
        # (count the pictures, each picture stands for N) would describe a
        # display this item never shows.
        chart_word = "table" if "table" in cumulative_vocab else "chart"
        cat = values.get("question_category", "the category")
        return [
            f"Look at the {chart_word} carefully.",
            f"Find the row labelled '{cat}'.",
            f"Read the number written next to it in the Count column.",
        ]

    hints = [f"Look at the {pg_label} carefully."]

    if scale > 1:
        # Both vocab fallbacks are noun PHRASES, not nouns, and this template
        # wrapped them in "the ... ( ... = N)": pupils who had not met "key" or
        # "scale" were served "Each picture in the the legend that shows what each
        # picture means stands for 5 items (what each picture stands for = 5)."
        # When the words are known the technical phrasing is the point; when they
        # are not, say it plainly instead of splicing a definition into a slot.
        if "key" in cumulative_vocab and "scale" in cumulative_vocab:
            hints.append(
                f"Each picture in the {key_label} stands for {scale} items ({scale_label} = {scale})."
            )
        else:
            hints.append(f"Each picture stands for {scale} items.")
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
        chart_word = "table" if "table" in cumulative_vocab else "chart"
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
