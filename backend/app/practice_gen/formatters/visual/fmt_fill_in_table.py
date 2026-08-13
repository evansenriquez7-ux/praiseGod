import random
from typing import Any, Dict

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext

def format_fill_in_table(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "set",
    answer_collection: str = "fill_in_blank",
) -> FormattedProblem:
    """
    interaction_mode "set"  — every count is blanked; the student fills the table in.
    interaction_mode "read" — the table is shown WITH its counts and the student reads
                              one back out of it.

    The read mode exists because "Interpret data in tabular form and in a pictograph"
    (mat_g2_dp_q3_1) names the table as something to be *read*, and this formatter --
    the only one in the pipeline that renders a data table at all -- could previously
    only blank it out. Filling a table in and interpreting a filled one are different
    skills, and only the first of them was buildable.
    """
    vp = ctx.visual_params or {}
    categories = vp.get("categories", ctx.values.get("categories", []))
    values = vp.get("values", ctx.values.get("values", []))

    if not categories or not values:
        categories = ["A", "B", "C"]
        values = [1, 2, 3]

    table_known = "table" in ctx.cumulative_vocab
    scale_known = "scale" in ctx.cumulative_vocab
    table_word = "table" if table_known else "chart"

    if interaction_mode == "read":
        return _format_read(
            ctx, rng, categories, values, table_word, answer_collection
        )

    # Create rows, leaving some values blank
    rows = []
    correct_answers = []

    # Hide all values for organize_table task
    for cat, val in zip(categories, values):
        rows.append([cat, None])
        correct_answers.append(val)

    visual_params = {
        "columns": ["Category", "Count"],
        "rows": rows,
    }

    if "scale" in vp and vp["scale"] > 1:
        if scale_known:
            question_text = f"Fill in the {table_word}. Note: Each symbol meant {vp['scale']} items."
        else:
            question_text = f"Fill in the {table_word}. Note: Each symbol stands for {vp['scale']} items."
    else:
        question_text = f"Fill in the {table_word} with the correct counts."

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_table",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=correct_answers,
        distractors=[],
        hints=ctx.hints,
        format=f"{interaction_mode}_{answer_collection}",
        format_data={"visual_params": visual_params},
        is_visual=True,
        visual_type="FillInTable",
        visual_params=visual_params,
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


def _format_read(
    ctx: QuestionContext,
    rng: random.Random,
    categories: list,
    values: list,
    table_word: str,
    answer_collection: str,
) -> FormattedProblem:
    """Show the completed table; ask the student to read one count out of it."""
    ask_cat = ctx.values.get("question_category")
    if ask_cat not in categories:
        ask_cat = categories[rng.randint(0, len(categories) - 1)]
    ask_idx = categories.index(ask_cat)
    correct = values[ask_idx]

    visual_params = {
        "columns": ["Category", "Count"],
        "rows": [[cat, val] for cat, val in zip(categories, values)],
        "ask_category": ask_cat,
        "is_read_mode": True,
    }

    question_text = f"Look at the {table_word}. How many are in {ask_cat}?"

    mcq_options = None
    correct_answer: Any = correct
    if answer_collection == "mcq":
        seen = {correct}
        distractors = []
        # Misreading the table means reading the wrong ROW, so every other
        # count in this same table is a genuine distractor.
        for i, v in enumerate(values):
            if len(distractors) >= 3:
                break
            if i != ask_idx and v not in seen:
                seen.add(v)
                distractors.append(v)
        for off in (1, 2, -1, 3, -2, 5, 10):
            if len(distractors) >= 3:
                break
            cand = correct + off
            if cand >= 0 and cand not in seen:
                seen.add(cand)
                distractors.append(cand)
        if len(distractors) < 3:
            raise ValueError(
                f"Formatter 'table_read' requires 3 unique distractors, got "
                f"{len(distractors)} for correct={correct} values={values} "
                f"(node={ctx.node_id}, seed={ctx.seed})"
            )
        all_opts = [correct] + distractors[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct}
            for i, v in enumerate(all_opts)
        ]
        correct_answer = next(o["key"] for o in mcq_options if o["is_correct"])

    format_data: dict = {"visual_params": visual_params}
    if mcq_options is not None:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_table_read",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=correct_answer,
        distractors=[],
        hints=ctx.hints,
        format=f"read_{answer_collection}",
        format_data=format_data,
        is_visual=True,
        visual_type="FillInTable",
        visual_params=visual_params,
        interaction_mode="read",
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
