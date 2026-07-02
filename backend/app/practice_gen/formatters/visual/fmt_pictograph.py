"""
fmt_pictograph.py — Pictograph (picture graph) visual formatter

Produces a FormattedProblem with pictograph visual_params.
Adapted from the BarChart generator in visual_skeletons.py (pictograph mode);
does NOT import from that module.

Grade progression (MATATAG):
    G1: scale=1 (each symbol = 1 item; no scale legend needed)
    G2: scale=2, 5, or 10 (each symbol = N items)

interaction_mode:
    "read" — pictograph shown; student counts/interprets values
    "set"  — student fills in the number of symbols for each category

answer_collection:
    "mcq"            — 4 count choices
    "fill_in_blank"  — student types the count
"""

import random
from typing import List, Optional

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors


# ─────────────────────────────────────────────────────────────────────────────
# Symbol and category banks
# ─────────────────────────────────────────────────────────────────────────────

# Each entry: (symbol, title_hint, categories)
_PICTOGRAPH_THEMES = [
    ("🍎", "Paboritong Prutas", ["Mansanas", "Saging", "Mangga", "Ubas"]),
    ("⭐", "Mga Bituin sa Laro", ["Lunes", "Martes", "Miyerkules", "Huwebes", "Biyernes"]),
    ("🐟", "Mga Isdang Nahuli", ["Buwaya", "Isda", "Hipon", "Pusit"]),
    ("📚", "Mga Librong Nabasa", ["Grade 1", "Grade 2", "Grade 3"]),
    ("🌧️", "Mga Ulan sa Buwan", ["Enero", "Pebrero", "Marso", "Abril"]),
    ("🏀", "Mga Puntong Nakuha", ["Lunes", "Martes", "Miyerkules"]),
    ("🌸", "Mga Buklaklak sa Hardin", ["Pula", "Dilaw", "Asul", "Rosas"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# Visual-params builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_visual_params(
    grade: int, diff_level: int, rng: random.Random
) -> dict:
    """
    Build pictograph visual_params.

    visual_params keys:
        categories   — list[str]
        counts       — list[int]  (actual item counts; divide by scale for # symbols)
        scale        — int (items per symbol)
        symbol       — str (emoji or ASCII char)
        title        — str
        ask_category — str | None  (which category is queried in read mode)
        has_scale    — bool
    """
    # Scale selection
    if grade <= 1:
        scale = 1
    elif grade == 2:
        scale = rng.choice([2, 5, 10]) if diff_level >= 2 else rng.choice([2, 5])
    else:
        scale = rng.choice([2, 5, 10])

    # Number of categories
    num_cats = 2 if diff_level == 1 else 3 if diff_level == 2 else 4

    # Theme selection
    theme = rng.choice(_PICTOGRAPH_THEMES)
    symbol, title, cat_pool = theme
    cats = cat_pool[:num_cats]

    # Generate counts that are multiples of scale (so whole symbols)
    max_symbols = 5 if grade <= 2 else 8
    counts = [rng.randint(1, max_symbols) * scale for _ in cats]

    return {
        "categories": cats,
        "counts": counts,
        "scale": scale,
        "symbol": symbol,
        "title": title,
        "ask_category": None,
        "has_scale": scale > 1,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Trap builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(params: dict, rng: random.Random) -> dict:
    traps: dict = {}
    counts: List[int] = params["counts"]
    scale: int = params["scale"]

    if len(counts) >= 2:
        swapped = counts[:]
        idx = rng.randint(0, len(counts) - 2)
        swapped[idx], swapped[idx + 1] = swapped[idx + 1], swapped[idx]
        traps["swapped_adjacent"] = {"values": swapped, "description": "Two adjacent bars swapped"}

    # Forgot scale: student counts symbols instead of items
    if scale > 1:
        raw_symbols = [c // scale for c in counts]
        traps["forgot_scale"] = {
            "values": raw_symbols,
            "description": "Counted symbols, forgot to multiply by scale",
        }

    # Off by one scale step
    off = [max(scale, c - scale) for c in counts]
    traps["off_by_one_symbol"] = {"values": off, "description": "Undercounted by one symbol"}

    return traps


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_pictograph(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a Pictograph FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Pictograph is shown; student reads the count for a specific category.
    interaction_mode "set":
        Student is given data and must draw the correct number of symbols.

    answer_collection "mcq":
        Four count choices.
    answer_collection "fill_in_blank":
        Student types the item count.
    """
    # ── 1. Resolve visual_params ───────────────────────────────────────────────
    if ctx.visual_params and "counts" in ctx.visual_params:
        vp = ctx.visual_params.copy()
        if "symbol" not in vp:
            vp["symbol"] = "🍎"
            vp["title"] = "Pictograph"
            vp["has_scale"] = vp.get("scale", 1) > 1
    else:
        diff_profile = ctx.difficulty_profile or {}
        diff_level = min(len(diff_profile) + 1, 4) if diff_profile else 2
        vp = _build_visual_params(ctx.grade, diff_level, random.Random(ctx.seed))

    categories: List[str] = vp["categories"]
    counts: List[int] = vp["counts"]
    scale: int = vp["scale"]

    task_type = vp.get("task_type", ctx.values.get("task_type", "read_value"))
    traps = _build_traps(vp, rng)
    ask_idx = 0
    
    if interaction_mode == "read":
        vp["is_read_mode"] = True
        if task_type in ("compare_two", "compare"):
            comp_a = ctx.values.get("compare_a", categories[0])
            comp_b = ctx.values.get("compare_b", categories[1])
            correct_count = ctx.correct_answer if ctx.correct_answer is not None else (comp_a if counts[categories.index(comp_a)] >= counts[categories.index(comp_b)] else comp_b)
            question_text = f"Look at the picture graph. Which has more: {comp_a} or {comp_b}?"
        elif task_type == "find_total":
            correct_count = ctx.correct_answer if ctx.correct_answer is not None else sum(counts)
            question_text = "Look at the picture graph. What is the total number of items shown?"
        elif task_type == "find_difference":
            comp_a = ctx.values.get("compare_a", categories[0])
            comp_b = ctx.values.get("compare_b", categories[1])
            correct_count = ctx.correct_answer if ctx.correct_answer is not None else abs(counts[categories.index(comp_a)] - counts[categories.index(comp_b)])
            question_text = f"Look at the picture graph. What is the difference between {comp_a} and {comp_b}?"
        else: # read_value
            ask_idx = rng.randint(0, len(categories) - 1)
            ask_cat = categories[ask_idx]
            correct_count = counts[ask_idx]
            vp["ask_category"] = ask_cat
            if scale > 1:
                question_text = f"Look at the picture graph. Each {vp['symbol']} = {scale}. How many are in {ask_cat}?"
            else:
                question_text = f"Look at the picture graph. How many are in {ask_cat}?"
    else:
        vp["is_read_mode"] = False
        data_str = ", ".join(f"{categories[i]}: {counts[i]}" for i in range(len(categories)))
        if scale > 1:
            question_text = (
                f"Make a picture graph to show: {data_str}. "
                f"Each {vp['symbol']} equals {scale}."
            )
        else:
            question_text = (
                f"Make a picture graph to show: {data_str}. "
                f"Draw one {vp['symbol']} for each item."
            )

    # ── 4. Answer collection ──────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq" and interaction_mode == "read":
        seen = {correct_count}
        distractor_vals = []
        
        if isinstance(correct_count, str):
            # The answer is a category name
            for cat in categories:
                if cat != correct_count and len(distractor_vals) < 3:
                    distractor_vals.append(cat)
                    seen.add(cat)
            if len(distractor_vals) < 3:
                distractor_vals = augment_distractors(distractor_vals, correct_count, target=3, max_delta=5)
                if len(distractor_vals) < 3:
                    raise ValueError(f"Formatter 'pictograph' requires at least 3 unique distractors, but got {len(distractor_vals)}")
        else:
            # The answer is a number
            for t in traps.values():
                tv = t.get("values")
                if isinstance(tv, list) and len(tv) > ask_idx:
                    d = tv[ask_idx]
                    if task_type == "find_total":
                        d = sum(tv)
                    elif task_type == "find_difference":
                        comp_a = ctx.values.get("compare_a", categories[0])
                        comp_b = ctx.values.get("compare_b", categories[1])
                        d = abs(tv[categories.index(comp_a)] - tv[categories.index(comp_b)])
                    
                    if d not in seen and d >= 0:
                        seen.add(d)
                        distractor_vals.append(d)
                if len(distractor_vals) == 3:
                    break
            # Pad
            for off in [scale, scale * 2, -scale, scale * 3]:
                if len(distractor_vals) >= 3:
                    break
                candidate = correct_count + off
                if candidate >= 0 and candidate not in seen:
                    seen.add(candidate)
                    distractor_vals.append(candidate)

        all_opts = [correct_count] + distractor_vals[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_count}
            for i, v in enumerate(all_opts)
        ]
        correct_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        correct_answer = correct_count if interaction_mode == "read" else counts

    vp["is_pictograph"] = True
    
    # Calculate max_y for BarChartInteractive
    if vp.get("counts"):
        vp["max_y"] = max(vp["counts"]) + (vp.get("scale", 1) * 2)
    elif vp.get("values"):
        vp["max_y"] = max(vp["values"]) + (vp.get("scale", 1) * 2)
    else:
        vp["max_y"] = 10

    format_data: dict = {"visual_params": vp}
    if mcq_options is not None:
        format_data["mcq_options"] = mcq_options

    fmt = f"{interaction_mode}_{answer_collection}"

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_pictograph",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=correct_answer,
        distractors=ctx.distractors,
        hints=ctx.hints,
        format=fmt,
        format_data=format_data,
        is_visual=True,
        visual_type="BarChart",
        visual_params=vp,
        interaction_mode=interaction_mode,
        answer_collection=answer_collection,
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
        given_values={k: v for k, v in ctx.values.items() if k != ctx.blank_target} if ctx.values else None,
        blank_target=ctx.blank_target,
    )
