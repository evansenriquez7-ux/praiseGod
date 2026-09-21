"""
fmt_timetable.py — Timetable visual formatter (class schedules and bus timetables)

WHY THIS EXISTS — measured, not assumed
---------------------------------------
`time_reading`'s `elapsed_unit="timetable"` items opened with a deictic phrase and then
listed the timetable as bullets inside the stem:

    mat_g2_mg_q4_2 seed 9: "Look at the class schedule:
                            • Math: 8:00 a.m. – 9:00 a.m.
                            • English: 9:00 a.m. – 9:45 a.m.
                            How many minutes long is the English class?"

The item was answerable, because the rows were in the sentence — but nothing on the page
was a timetable, so "look at the class schedule" pointed at a display that did not exist,
which is the class `dangling_visual_reference_1M` gates. Measured 2026-09-21: 4 of 20
seeds on mat_g2_mg_q4_2.

MATATAG names the display outright — "Solve problems involving elapsed time (minutes in
an hour, hours in a day, days in a week), including TIMETABLES" — so drawing one is
Content Rule 4 work, not decoration. Reading a timetable is a different skill from
reading a sentence that happens to contain times, and it is the skill the clause names.

WHY THE ROWS COME FROM THE DNA
------------------------------
`values["timetable_rows"]` is built by the same branch that computes the key. A formatter
that re-derived the times from `hour`/`minute` would be a second copy of that rule and
free to disagree with the answer — the trap the `_number_plurals` register cost six sites
to learn. This formatter draws what it is given and computes nothing.

interaction_mode:
    "read" — the timetable is shown; the pupil reads two times and subtracts. There is
    no "set" mode: the competency is about SOLVING elapsed-time problems, and a mode
    with no route behind it would be a declaration with no behaviour (§6E's hazard).

visual_params:
    {
        "kind":    str,   # "class" | "bus"
        "columns": [str], # header row, e.g. ["Subject", "Starts", "Ends"]
        "rows":    [{"label": str, "start": str, "end": str}, ...],
    }
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.formatters._option_order import shuffle_options


def format_timetable(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """Build a Timetable FormattedProblem from a QuestionContext."""
    values = ctx.values or {}

    rows = values.get("timetable_rows")
    columns = values.get("timetable_columns")
    kind = values.get("timetable_kind")
    if not rows or not columns or kind not in ("class", "bus"):
        raise ValueError(
            f"fmt_timetable: node {ctx.node_id} seed {ctx.seed} carries no timetable to "
            f"draw (kind={kind!r}, columns={columns!r}, rows={rows!r}). This formatter "
            f"draws a timetable and cannot invent one; it must only be routed to "
            f"elapsed_unit='timetable' items. Reproduce: "
            f"PracticeOrchestrator.generate_problem(node_id='{ctx.node_id}', "
            f"seed={ctx.seed}, is_student_path=True)"
        )

    vp = {"kind": kind, "columns": list(columns), "rows": list(rows)}

    correct_answer = values.get("answer")
    if correct_answer is None:
        raise ValueError(
            f"fmt_timetable: node {ctx.node_id} seed {ctx.seed} has no 'answer'."
        )
    traps = [d for d in (values.get("distractors") or []) if d != correct_answer]
    if len(traps) < 3:
        raise ValueError(
            f"fmt_timetable: node {ctx.node_id} seed {ctx.seed} supplied {len(traps)} "
            f"distractor(s) differing from the key {correct_answer!r}; at least 3 are "
            f"required."
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

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_timetable",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=str(values.get("question") or ctx.question_text or ""),
        correct_answer=final_answer,
        distractors=traps[:3],
        hints=ctx.hints,
        format=f"{interaction_mode}_{answer_collection}",
        format_data=format_data,
        is_visual=True,
        visual_type="Timetable",
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
