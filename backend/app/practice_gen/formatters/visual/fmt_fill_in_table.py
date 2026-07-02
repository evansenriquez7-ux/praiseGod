import random
from typing import Any, Dict

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext

def format_fill_in_table(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "set",
    answer_collection: str = "fill_in_blank",
) -> FormattedProblem:
    vp = ctx.visual_params or {}
    categories = vp.get("categories", ctx.values.get("categories", []))
    values = vp.get("values", ctx.values.get("values", []))
    
    if not categories or not values:
        categories = ["A", "B", "C"]
        values = [1, 2, 3]

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
        question_text = f"Fill in the table. Note: Each symbol meant {vp['scale']} items."
    else:
        question_text = "Fill in the table with the correct counts."

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
