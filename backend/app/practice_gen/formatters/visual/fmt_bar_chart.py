"""
fmt_bar_chart.py — BarChart visual formatter

Produces a FormattedProblem with bar-chart visual_params.
Carves generation logic from visual_skeletons.py _gen_bar_chart /
_traps_bar_chart; does NOT import from that module.

Filipino contexts (school activities, favourite things, sports, etc.) are
used for category labels as appropriate for the MATATAG curriculum.

interaction_mode:
    "read" — chart is pre-filled; student reads / interprets values
    "set"  — student fills in bar values given the raw data

answer_collection:
    "mcq"            — 4 choices for the queried value
    "fill_in_blank"  — student types the value
"""

import random
from typing import List, Optional

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# ─────────────────────────────────────────────────────────────────────────────
# Filipino category-label banks
# ─────────────────────────────────────────────────────────────────────────────

_CATEGORY_BANKS = {
    "low": [          # G1–G2
        ["Mansanas", "Saging", "Mangga"],
        ["Aso", "Pusa", "Ibon"],
        ["Pula", "Asul", "Berde", "Dilaw"],
        ["Lalaki", "Babae"],
        ["Maliwanag", "Maulap", "Maulan"],
    ],
    "mid": [          # G3–G4
        ["Lunes", "Martes", "Miyerkules", "Huwebes", "Biyernes"],
        ["Grade 1", "Grade 2", "Grade 3", "Grade 4"],
        ["Matematika", "Agham", "Ingles", "Filipino"],
        ["Linggo 1", "Linggo 2", "Linggo 3", "Linggo 4"],
        ["Basketbol", "Volleyball", "Badminton", "Swimming"],
    ],
    "high": [         # G5+
        ["Ene", "Peb", "Mar", "Abr", "Mayo"],
        ["Tindahan A", "Tindahan B", "Tindahan C", "Tindahan D"],
        ["2021", "2022", "2023", "2024"],
        ["Koponan 1", "Koponan 2", "Koponan 3", "Koponan 4"],
        ["Basketball", "Volleyball", "Soccer", "Swimming", "Running"],
    ],
}


def _pick_categories(grade: int, num_categories: int, rng: random.Random) -> List[str]:
    bank_key = "low" if grade <= 2 else ("mid" if grade <= 4 else "high")
    bank = _CATEGORY_BANKS[bank_key]
    eligible = [b for b in bank if len(b) >= num_categories]
    if not eligible:
        eligible = bank
    chosen_bank = rng.choice(eligible)
    return chosen_bank[:num_categories]


# ─────────────────────────────────────────────────────────────────────────────
# Grade-appropriate scale / range
# ─────────────────────────────────────────────────────────────────────────────

def _grade_scale(grade: int, diff_level: int) -> dict:
    """Return {"max_y": int, "scale": int, "num_categories": int}."""
    if grade <= 2:
        return {
            "max_y": 5 if diff_level == 1 else 10,
            "scale": 1,
            "num_categories": 2 if diff_level == 1 else 3,
        }
    if grade <= 4:
        return {
            "max_y": 10 if diff_level == 1 else 20,
            "scale": 2 if diff_level == 1 else 5,
            "num_categories": 3 if diff_level == 1 else 4,
        }
    return {
        "max_y": 20 if diff_level == 1 else 50,
        "scale": 5 if diff_level == 1 else 10,
        "num_categories": 4 if diff_level == 1 else 5,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Visual-params builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_visual_params(
    grade: int,
    diff_level: int,
    rng: random.Random,
    is_double: bool = False,
    orientation: str = "vertical",
) -> dict:
    """
    Build BarChart visual_params.

    visual_params keys:
        categories     — list[str]
        values         — list[int]
        values2        — list[int] | None  (double-bar only)
        series_labels  — list[str] | None
        scale          — int
        orientation    — "vertical" | "horizontal"
        title          — str
        y_axis_label   — str
        max_y          — int
        ask_category   — str | None  (read mode: which category is queried)
        ask_series     — str | None  (read mode: which series is queried)
    """
    gs = _grade_scale(grade, diff_level)
    n = gs["num_categories"]
    scale = gs["scale"]
    max_y = gs["max_y"]

    categories = _pick_categories(grade, n, rng)
    values = [rng.randint(1, max_y // scale) * scale for _ in range(n)]

    values2 = None
    series_labels = None
    if is_double:
        values2 = [rng.randint(1, max_y // scale) * scale for _ in range(n)]
        series_labels = ["Grupong A", "Grupong B"] if grade <= 4 else ["Ngayong Taon", "Nakaraang Taon"]

    return {
        "categories": categories,
        "labels": categories,
        "values": values,
        "values2": values2,
        "series_labels": series_labels,
        "scale": scale,
        "orientation": orientation,
        "title": "Datos",
        "y_axis_label": "Bilang",
        "max_y": max_y,
        "ask_category": None,
        "ask_series": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Trap builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(params: dict, rng: random.Random) -> dict:
    traps: dict = {}
    values = params["values"]

    if len(values) >= 2:
        swapped = values[:]
        idx = rng.randint(0, len(values) - 2)
        swapped[idx], swapped[idx + 1] = swapped[idx + 1], swapped[idx]
        traps["swapped_adjacent"] = {"values": swapped, "description": "Two adjacent bars swapped"}

    mean_val = sum(values) // len(values)
    traps["all_same_height"] = {
        "values": [mean_val] * len(values),
        "description": "Made all bars the same height",
    }
    off = [v + 1 if rng.choice([True, False]) else max(0, v - 1) for v in values]
    traps["off_by_grid_line"] = {"values": off, "description": "One grid line off for some bars"}

    doubled = values[:]
    doubled[0] *= 2
    traps["doubled_value"] = {"values": doubled, "description": "Doubled one category's value"}

    traps["reversed_order"] = {"values": list(reversed(values)), "description": "Bar order reversed"}

    return traps


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_bar_chart(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a BarChart FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Chart is pre-filled with data; student reads/interprets a specific value.
    interaction_mode "set":
        Student is given raw data values and must fill in the chart bars.

    answer_collection "mcq":
        Four choices for the queried category value.
    answer_collection "fill_in_blank":
        Student types the value.
    """
    # ── 1. Resolve visual_params ───────────────────────────────────────────────
    if ctx.visual_params and "categories" in ctx.visual_params:
        vp = ctx.visual_params.copy()
        if "labels" not in vp:
            vp["labels"] = vp["categories"]
        if "max_y" not in vp:
            all_vals = vp.get("values", []) + (vp.get("values2") or [])
            max_v = max(all_vals) if all_vals else 10
            scale = vp.get("scale", 1)
            vp["max_y"] = ((max_v // scale) + 1) * scale
    elif ctx.values and "number" in ctx.values:
        # Represent a single number as a bar
        val = int(ctx.values["number"])
        interval = 10 if val > 20 else (5 if val > 10 else 2)
        if val <= 10:
            interval = 1
            max_val = 10
        elif val <= 20:
            interval = 2
            max_val = 20
        else:
            max_val = ((val // 10) + 1) * 10
        vp = {
            "categories": ["Value"],
            "labels": ["Value"],
            "values": [val],
            "max_val": max_val,
            "max_y": max_val,
            "scale": interval,
            "y_interval": interval,
            "x_label": "Category",
            "y_label": "Amount",
            "orientation": "vertical"
        }
    else:
        diff_profile = ctx.difficulty_profile or {}
        diff_level = min(len(diff_profile) + 1, 4) if diff_profile else 2
        is_double = ctx.grade >= 5 and diff_level >= 2
        vp = _build_visual_params(
            ctx.grade, diff_level, random.Random(ctx.seed), is_double=is_double
        )

    categories: List[str] = vp["categories"]
    values: List[int] = vp["values"]
    values2 = vp.get("values2")
    series_labels = vp.get("series_labels")

    task_type = vp.get("task_type", ctx.values.get("task_type", "read_value"))
    traps = _build_traps(vp, rng)
    ask_idx = 0
    ask_series = series_labels[0] if series_labels else None

    if interaction_mode == "read":
        vp["is_read_mode"] = True
        if task_type in ("compare_bars", "compare"):
            comp_a = ctx.values.get("compare_a", categories[0])
            comp_b = ctx.values.get("compare_b", categories[1])
            correct_value = ctx.correct_answer if ctx.correct_answer is not None else (comp_a if values[categories.index(comp_a)] >= values[categories.index(comp_b)] else comp_b)
            question_text = f"Look at the bar graph. Which is greater: {comp_a} or {comp_b}?"
        elif task_type == "find_total":
            correct_value = ctx.correct_answer if ctx.correct_answer is not None else sum(values)
            question_text = "Look at the bar graph. What is the total value of all categories?"
        elif task_type == "find_difference":
            comp_a = ctx.values.get("compare_a", categories[0])
            comp_b = ctx.values.get("compare_b", categories[1])
            correct_value = ctx.correct_answer if ctx.correct_answer is not None else abs(values[categories.index(comp_a)] - values[categories.index(comp_b)])
            question_text = f"Look at the bar graph. What is the difference between {comp_a} and {comp_b}?"
        elif task_type == "find_most_least":
            direction = ctx.values.get("direction", "most")
            correct_value = ctx.correct_answer if ctx.correct_answer is not None else (categories[values.index(max(values))] if direction == "most" else categories[values.index(min(values))])
            question_text = f"Look at the bar graph. Which category has the {direction}?"
        else:
            if ctx.values and "question_category" in ctx.values and ctx.values["question_category"] in categories:
                ask_cat = ctx.values["question_category"]
                ask_idx = categories.index(ask_cat)
            else:
                ask_idx = rng.randint(0, len(categories) - 1)
                ask_cat = categories[ask_idx]
            vp["ask_category"] = ask_cat
            vp["ask_series"] = ask_series
            if values2 and ask_series:
                correct_value = values[ask_idx] if ask_series == series_labels[0] else values2[ask_idx]
                question_text = f"Look at the double bar graph. What is the value for {ask_cat} in {ask_series}?"
            else:
                correct_value = values[ask_idx]
                question_text = f"Look at the bar graph. What is the value for {ask_cat}?"
    else:
        vp["is_read_mode"] = False
        correct_value = values if not values2 else [values, values2]
        data_str = ", ".join(f"{categories[i]}: {values[i]}" for i in range(len(categories)))
        orient_hint = " (horizontal bars)" if vp.get("orientation") == "horizontal" else ""
        question_text = f"Create a bar graph{orient_hint} to show: {data_str}."

    # ── 4. Answer collection ──────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq" and interaction_mode == "read":
        seen = {correct_value}
        distractor_vals = []
        
        if isinstance(correct_value, str):
            for cat in categories:
                if cat != correct_value and len(distractor_vals) < 3:
                    distractor_vals.append(cat)
                    seen.add(cat)
            
            # Find a bank of categories to draw extra distractors from
            flat_bank = []
            for grade_list in _CATEGORY_BANKS.values():
                for sublist in grade_list:
                    flat_bank.extend(sublist)
            # Add English names as well just in case they are used
            flat_bank.extend(["cats", "dogs", "birds", "fish", "rabbits", "turtles", "apples", "bananas", "mangoes", "grapes", "oranges", "strawberries"])
            
            # De-duplicate flat_bank while preserving order
            clean_bank = []
            for item in flat_bank:
                if item not in clean_bank:
                    clean_bank.append(item)
            
            # Shuffle to draw randomly
            shuffled_bank = clean_bank[:]
            rng.shuffle(shuffled_bank)
            
            for item in shuffled_bank:
                if len(distractor_vals) >= 3:
                    break
                if item not in seen and item.lower() != correct_value.lower():
                    distractor_vals.append(item)
                    seen.add(item)

            if len(distractor_vals) < 3:
                raise ValueError(
                    f"Bar chart MCQ formatter requires 3 distractors, but only found {len(distractor_vals)} for correct_value={correct_value}."
                )
        else:
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
            scale = vp.get("scale", 1)
            offsets_steps = [1, 2, 3, -1, -2]
            for off in offsets_steps:
                if len(distractor_vals) >= 3:
                    break
                candidate = correct_value + off * scale
                if candidate >= 0 and candidate not in seen:
                    seen.add(candidate)
                    distractor_vals.append(candidate)

        all_opts = [correct_value] + distractor_vals[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_value}
            for i, v in enumerate(all_opts)
        ]
        correct_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        correct_answer = correct_value

    format_data: dict = {"visual_params": vp}
    if mcq_options is not None:
        format_data["mcq_options"] = mcq_options

    fmt = f"{interaction_mode}_{answer_collection}"

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_barchart",
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
