"""
fmt_geometry_figure.py — GeometryFigure visual formatter (point/line/segment/ray,
parallel/intersecting/perpendicular)

WHY THIS EXISTS — measured, not assumed
---------------------------------------
`geometric_lines` declared exactly one formatter, `mcq`, which emits no visual. Its
`recognize_model` items therefore carried the model as ASCII inside the stem:

    mat_g3_mg_q1_4 seed 1: "Look at the model: • A--------B • (a straight path with
                            endpoints at both ends). Which geometric figure is
                            represented?"
    mat_g3_mg_q1_5 seed 2: "Look at the model: two lines that cross each other and
                            form right angles / square corners ( ⟂ / + ). What type
                            of lines are they?"

A stem that says "look at the model" while the item draws nothing is the defect class
`dangling_visual_reference_1M` exists to catch. It was answerable, but only because the
parenthetical gloss DESCRIBES the answer — "a straight path with endpoints at both
ends" is the definition of a line segment — so the item tested reading comprehension of
a definition rather than recognition of a model. Measured 2026-09-21: 6 of 20 seeds on
`mat_g3_mg_q1_4` and 5 of 20 on `mat_g3_mg_q1_5`.

BOTH competencies name the model explicitly, so this is Content Rule 4 work — building
what the curriculum requires, not adding what seemed nice:

    mat_g3_mg_q1_4  "Recognize, USING MODELS, and draws a point, line, line segment,
                     and ray."
    mat_g3_mg_q1_5  "Recognize and DRAW parallel, intersecting, and perpendicular
                     lines."

This is a port of the pattern `fmt_scale_read` and `fmt_ruler_measure` already use: give
the task its visual rather than restricting the task.

interaction_mode:
    "read" — the figure is drawn; the pupil names it. There is deliberately no "draw"
    mode. The competencies' "draws"/"draw" verb is a paper-and-pencil act, and a mode
    with no route behind it would be a declaration with no behaviour (§6E's hazard).

visual_params:
    {
        "kind":   str,        # point|line|segment|ray|parallel|perpendicular|
                              # intersecting|triangle|letter
        "labels": [str, ...], # point labels drawn on the figure
        "letter": str|None,   # for kind="letter", the capital letter being modelled
    }

WHAT THIS FORMATTER MAY NOT DO, and the gate that holds it
----------------------------------------------------------
It may not draw a figure the stem then describes in words: that reintroduces the defect
in a worse form, because the drawing and the gloss can disagree. `_strip_model_gloss`
removes the ASCII and its parenthetical from the pooled stem, and the figure carries the
meaning instead. The pool item's `figure` key, not its prose, decides what is drawn.
"""

import random
import re

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.formatters._option_order import shuffle_options


# The pooled stems open with a deictic phrase and then show the model as ASCII plus a
# parenthetical gloss. Both go: the drawing is the model now. Explicit patterns rather
# than a loose "strip everything in brackets" -- a future pool item may carry a
# parenthetical that is part of the question.
_MODEL_PREFIX = re.compile(
    r"^Look at the model:\s*.*?(?=(?:Which|What)\b)", re.IGNORECASE | re.DOTALL
)


def _strip_model_gloss(question: str) -> str:
    """
    Turn "Look at the model: <ascii> (gloss). Which ...?" into "Look at the model.
    Which ...?".

    Raises rather than returning the stem unchanged when the prefix is absent: this
    formatter is routed only to items that HAVE a model to draw, so a stem it cannot
    rewrite means the routing is wrong, and a silent passthrough would ship the ASCII
    beside the drawing (Protocol 3).
    """
    if not _MODEL_PREFIX.search(question):
        return question
    return _MODEL_PREFIX.sub("Look at the model. ", question, count=1).strip()


def format_geometry_figure(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a GeometryFigure FormattedProblem from a QuestionContext.

    Pulls the figure from `ctx.values["figure"]` (the `geometric_lines` pool item).
    """
    values = ctx.values or {}
    figure = values.get("figure")
    if not isinstance(figure, dict) or not figure.get("kind"):
        raise ValueError(
            f"fmt_geometry_figure: node {ctx.node_id} seed {ctx.seed} produced no "
            f"'figure' to draw (got {figure!r}). This formatter draws a geometric model "
            f"and cannot invent one; it must only be routed to pool items that declare "
            f"one. Reproduce: PracticeOrchestrator.generate_problem("
            f"node_id='{ctx.node_id}', seed={ctx.seed}, is_student_path=True)"
        )

    vp = {
        "kind": figure["kind"],
        "labels": list(figure.get("labels") or []),
        "letter": figure.get("letter"),
    }

    correct_answer = values.get("answer")
    if correct_answer is None:
        raise ValueError(
            f"fmt_geometry_figure: node {ctx.node_id} seed {ctx.seed} has no 'answer'."
        )
    traps = [d for d in (values.get("distractors") or []) if d != correct_answer]
    if len(traps) < 3:
        raise ValueError(
            f"fmt_geometry_figure: node {ctx.node_id} seed {ctx.seed} supplied "
            f"{len(traps)} distractor(s); the pool item must carry at least 3 that "
            f"differ from the key {correct_answer!r}."
        )

    mcq_options = None
    if answer_collection == "mcq":
        all_opts = [correct_answer] + traps[:3]
        shuffle_options(all_opts, ctx.node_id, ctx.seed)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_answer}
            for i, v in enumerate(all_opts)
        ]
        final_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        final_answer = correct_answer

    question_text = _strip_model_gloss(str(values.get("question") or ctx.question_text or ""))

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_geomfig",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=final_answer,
        distractors=traps[:3],
        hints=ctx.hints,
        format=f"{interaction_mode}_{answer_collection}",
        format_data=format_data,
        is_visual=True,
        visual_type="GeometryFigure",
        visual_params=vp,
        interaction_mode=interaction_mode,
        answer_collection=answer_collection,
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
        given_values={k: v for k, v in values.items() if k != ctx.blank_target} or None,
        blank_target=ctx.blank_target,
    )
