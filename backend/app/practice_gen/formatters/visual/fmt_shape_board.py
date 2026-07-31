"""
fmt_shape_board.py — ShapeBoard visual formatter

Refactored from visual_skeletons.py Categorize generator.
Does NOT import from visual_skeletons.py.

interaction_mode:
    "read" — shapes are shown; student answers a question about them
    "set"  — student categorises shapes by dragging them to the correct group

visual_params:
    {
        "shapes": [
            {
                "type":         str,    # "triangle" | "square" | "rectangle" | ...
                "sides":        int,
                "corners":      int,
                "is_regular":   bool,
                "orientation_deg": int, # 0 | 45 | 90 | 135
            },
            ...
        ],
        "question_type": "identify" | "count_property" | "sort_by" | "compare",
    }

Traps: misidentify by side count, confuse regular/irregular, orientation confusion.
"""

import random
import re
from typing import List, Optional

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# ─────────────────────────────────────────────────────────────────────────────
# Shape catalogue
# ─────────────────────────────────────────────────────────────────────────────

_SHAPE_CATALOGUE = [
    {"type": "triangle",   "sides": 3, "corners": 3, "is_regular": True},
    {"type": "triangle",   "sides": 3, "corners": 3, "is_regular": False},
    {"type": "square",     "sides": 4, "corners": 4, "is_regular": True},
    {"type": "rectangle",  "sides": 4, "corners": 4, "is_regular": False},
    {"type": "rhombus",    "sides": 4, "corners": 4, "is_regular": False},
    {"type": "trapezoid",  "sides": 4, "corners": 4, "is_regular": False},
    {"type": "pentagon",   "sides": 5, "corners": 5, "is_regular": True},
    {"type": "hexagon",    "sides": 6, "corners": 6, "is_regular": True},
    {"type": "octagon",    "sides": 8, "corners": 8, "is_regular": True},
    {"type": "circle",     "sides": 0, "corners": 0, "is_regular": True},
]

_ORIENTATIONS = [0, 45, 90, 135]


_SHAPE_WORDS = {
    "triangle": "triangle", "triangles": "triangle",
    "square": "square", "squares": "square",
    "rectangle": "rectangle", "rectangles": "rectangle",
    "rhombus": "rhombus", "diamond": "rhombus",
    "trapezoid": "trapezoid",
    "pentagon": "pentagon", "pentagons": "pentagon",
    "hexagon": "hexagon", "hexagons": "hexagon",
    "octagon": "octagon", "octagons": "octagon",
    "circle": "circle", "circles": "circle",
    "half-circle": "circle", "half-circles": "circle",
    "quarter-circle": "circle", "quarter-circles": "circle",
}


def _catalogue_entry(type_name: str) -> Optional[dict]:
    for s in _SHAPE_CATALOGUE:
        if s["type"] == type_name:
            return s
    return None


def _shapes_from_item(values: dict, rng: random.Random) -> List[dict]:
    """
    Build the board out of the shapes the DNA's own item talks about.

    shapes_2d emits a text item -- {question, answer, distractors, orientation} --
    and never a `shapes` list, so this formatter's `_build_shapes` fallback fired
    on 20 of 20 forced generations and rendered a board of randomly chosen shapes
    with a question of its own invention, discarding the DNA's. A Grade 1 node
    whose competency names "triangle, rectangle, square" was serving boards
    containing circles, under the stem "Look at the shapes. Tell how many corners
    does the highlighted shape have." -- content the competency never asked for,
    in broken English.

    Every item in the pool names its shapes in the question text ("How many sides
    does a rectangle have?", "Which shape has more sides -- a triangle or a
    rectangle?"), and the shape-valued options name more, so the board is
    assembled from both: question first (that is what the item is about), then
    any option that is itself a shape name.
    """
    found: List[str] = []
    text = str(values.get("question", "")).lower()
    for word, type_name in _SHAPE_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", text) and type_name not in found:
            found.append(type_name)
    for opt in [values.get("answer")] + list(values.get("distractors") or []):
        type_name = _SHAPE_WORDS.get(str(opt).strip().lower())
        if type_name and type_name not in found:
            found.append(type_name)

    shapes: List[dict] = []
    # "rotated" is the DNA's own orientation field; it is the difficulty knob the
    # competency names ("of different size and in different orientation"), so it
    # drives the rendered angle rather than a formatter-local difficulty guess.
    varied = str(values.get("orientation", "standard")).lower() != "standard"
    for i, type_name in enumerate(found):
        entry = _catalogue_entry(type_name)
        if entry is None:
            continue
        shapes.append({
            "id": f"shape_{i}",
            "type": entry["type"],
            "sides": entry["sides"],
            "corners": entry["corners"],
            "is_regular": entry["is_regular"],
            "orientation_deg": rng.choice(_ORIENTATIONS[1:]) if varied else 0,
        })
    return shapes


def _build_shapes(grade: int, diff_level: int, rng: random.Random, count: int = 4) -> List[dict]:
    """
    Sample `count` shapes appropriate for the grade.

    G1-2: triangles, squares, rectangles, circles only
    G3-4: all 4-sided shapes + pentagon/hexagon
    G5+:  full catalogue
    """
    if grade <= 2:
        eligible = [s for s in _SHAPE_CATALOGUE if s["sides"] in (0, 3, 4) and s["type"] in ("triangle", "square", "rectangle", "circle")]
    elif grade <= 4:
        eligible = [s for s in _SHAPE_CATALOGUE if s["sides"] <= 6]
    else:
        eligible = _SHAPE_CATALOGUE[:]

    chosen = rng.choices(eligible, k=count)
    shapes = []
    for i, s in enumerate(chosen):
        orientation = rng.choice(_ORIENTATIONS) if diff_level >= 2 else 0
        shapes.append({
            "id": f"shape_{i}",
            "type": s["type"],
            "sides": s["sides"],
            "corners": s["corners"],
            "is_regular": s["is_regular"],
            "orientation_deg": orientation,
        })
    return shapes


def _select_question_type(grade: int, diff_level: int, rng: random.Random) -> str:
    if grade <= 2:
        return rng.choice(["identify", "count_property"])
    if diff_level == 1:
        return rng.choice(["identify", "count_property"])
    return rng.choice(["identify", "count_property", "sort_by", "compare"])


# ─────────────────────────────────────────────────────────────────────────────
# Answer + traps
# ─────────────────────────────────────────────────────────────────────────────

def _correct_answer_and_traps(shapes: List[dict], question_type: str, rng: random.Random):
    """
    Return (correct_answer, traps_list, question_detail).

    question_detail: extra string embedded in the question text.
    """
    if question_type == "identify":
        target = rng.choice(shapes)
        correct = target["type"]
        # Traps: shapes with same side count, or adjacent side counts
        same_sides = [s["type"] for s in _SHAPE_CATALOGUE if s["sides"] == target["sides"] and s["type"] != correct]
        off_sides = [s["type"] for s in _SHAPE_CATALOGUE if abs(s["sides"] - target["sides"]) == 1]
        traps = list(dict.fromkeys(same_sides + off_sides))[:3]
        detail = f"the highlighted shape"
        return correct, traps, detail, target

    if question_type == "count_property":
        property_name = rng.choice(["sides", "corners"])
        target = rng.choice(shapes)
        correct = target[property_name]
        traps = [correct - 1, correct + 1, correct + 2]
        traps = [t for t in traps if t >= 0][:3]
        detail = f"how many {property_name} does the highlighted shape have"
        return correct, traps, detail, target

    if question_type == "sort_by":
        # Sort shapes by side count — answer is the sorted type list
        sorted_shapes = sorted(shapes, key=lambda s: s["sides"])
        correct_list = [s["type"] for s in sorted_shapes]
        correct = ", ".join(correct_list)
        # Traps: reversed, or adjacent swap
        reversed_order = list(reversed(correct_list))
        swapped = correct_list.copy()
        if len(swapped) >= 2:
            swapped[0], swapped[1] = swapped[1], swapped[0]
        traps = [", ".join(reversed_order), ", ".join(swapped)]
        # Add a random shuffle trap if there are more than 2 shapes
        if len(correct_list) > 2:
            shuffled = correct_list.copy()
            rng.shuffle(shuffled)
            traps.append(", ".join(shuffled))
            
        detail = "sort the shapes by number of sides (fewest first)"
        return correct, list(dict.fromkeys(traps))[:3], detail, None

    # compare
    if len(shapes) >= 2:
        a, b = shapes[0], shapes[1]
        correct = "more" if a["sides"] > b["sides"] else ("fewer" if a["sides"] < b["sides"] else "equal")
        traps = [x for x in ["more", "fewer", "equal"] if x != correct]
        detail = f"does shape A have more, fewer, or equal sides compared to shape B"
        return correct, traps, detail, None

    correct = shapes[0]["type"]
    traps = []
    return correct, traps, "identify the shape", shapes[0]


# ─────────────────────────────────────────────────────────────────────────────
# Question text
# ─────────────────────────────────────────────────────────────────────────────

def _stem(question_type: str, detail: str, interaction_mode: str) -> str:
    if interaction_mode == "set":
        return "Drag each shape into the correct group."
    return f"Look at the shapes. Tell {detail}."


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_shape_board(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a ShapeBoard FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Shapes displayed; student answers a question about their properties.
    interaction_mode "set":
        Student drags shapes into labelled category bins.

    Pulls shape data from ctx.values when available (shapes_2d generate_params),
    otherwise generates fresh shape data.
    """
    diff_level = 2
    if ctx.difficulty_profile:
        diff_level = min(len(ctx.difficulty_profile) + 1, 4)

    # ── 0. A DNA-authored item is rendered as itself, not replaced ────────────
    # When ctx.values carries shapes_2d's item contract, this formatter's job is
    # to *illustrate* that item: its question is the stem, its answer is the key,
    # and the board shows the shapes it names. Previously this path did not
    # exist, so the fallback below invented an unrelated board and stem and threw
    # the DNA's item away on every single generation.
    _vals = ctx.values or {}
    if _vals.get("question") and _vals.get("answer") is not None and "distractors" in _vals:
        shapes = _shapes_from_item(_vals, rng)
        if len(shapes) < 1:
            raise ValueError(
                f"shape_board cannot illustrate this item: no catalogue shape is named in "
                f"question={_vals.get('question')!r} or in its options "
                f"{[_vals.get('answer')] + list(_vals.get('distractors') or [])!r}. "
                f"Either the item belongs on a text formatter or the shape vocabulary needs "
                f"extending — it is not something to paper over with an invented board. "
                f"Reproduce: node={ctx.node_id} seed={ctx.seed}."
            )
        correct_answer = _vals["answer"]
        traps = [d for d in (_vals.get("distractors") or []) if d != correct_answer]
        vp = {
            "shapes": shapes,
            # The board is an illustration of a stated question, so it carries no
            # question_type of its own for the frontend to re-interrogate.
            "question_type": "illustrate",
            # Deliberately unhighlighted. The board's shapes include the answer
            # ("What shape has 4 equal sides and 4 corners?" is drawn alongside a
            # square), so highlighting the correct one would hand the answer to
            # the student visually -- §1F's leak, in a form §1F cannot see
            # because it only reads the stem text. The question names its own
            # subject, so no highlight is needed to make it answerable.
            "highlighted_shape": None,
        }
        mcq_options = None
        final_answer = correct_answer
        if answer_collection == "mcq":
            all_opts = [correct_answer] + traps[:3]
            rng.shuffle(all_opts)
            mcq_options = [
                {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_answer}
                for i, v in enumerate(all_opts)
            ]
            final_answer = next(o["key"] for o in mcq_options if o["is_correct"])
        format_data: dict = {"visual_params": vp}
        if mcq_options:
            format_data["mcq_options"] = mcq_options
        return FormattedProblem(
            problem_id=f"{ctx.node_id}_{ctx.seed}_shapeboard",
            node_id=ctx.node_id,
            competency_text=ctx.competency_text,
            grade=ctx.grade,
            seed=ctx.seed,
            question_text=str(_vals["question"]),
            correct_answer=final_answer,
            distractors=traps,
            hints=ctx.hints,
            format=f"{interaction_mode}_{answer_collection}",
            format_data=format_data,
            is_visual=True,
            visual_type="ShapeBoard",
            visual_params=vp,
            interaction_mode=interaction_mode,
            answer_collection="mcq" if mcq_options else answer_collection,
            difficulty_profile=ctx.difficulty_profile or {},
            difficulty_axes_served=ctx.difficulty_axes_served,
            experience="standard",
            experience_config=None,
            interest_theme=ctx.interest_theme,
            spine_id=ctx.spine_id,
            given_values={k: v for k, v in _vals.items() if k != ctx.blank_target},
            blank_target=ctx.blank_target,
        )

    # ── 1. Resolve shapes ─────────────────────────────────────────────────────
    if ctx.visual_params and "shapes" in ctx.visual_params:
        shapes = ctx.visual_params["shapes"]
        question_type = ctx.visual_params.get("question_type", "identify")
    elif ctx.values and "shapes" in ctx.values:
        shapes = ctx.values["shapes"]
        question_type = ctx.values.get("question_type", "identify")
    else:
        count = 4 if diff_level <= 2 else 6
        shapes = _build_shapes(ctx.grade, diff_level, rng, count)
        question_type = _select_question_type(ctx.grade, diff_level, rng)

    if interaction_mode == "set":
        question_type = "sort_by"

    # ── 2. Answer + traps ─────────────────────────────────────────────────────
    # Normalize question_type so fallthroughs are correctly labeled for the frontend
    if "identify" in question_type:
        question_type = "identify"
    elif "count" in question_type:
        question_type = "count_property"
    elif "sort" in question_type or interaction_mode == "set":
        question_type = "sort_by"
    else:
        question_type = "compare"

    correct_answer, traps, detail, highlighted = _correct_answer_and_traps(shapes, question_type, rng)

    vp = {
        "shapes": shapes,
        "question_type": question_type,
        "highlighted_shape": highlighted,
    }

    # ── 3. MCQ options ────────────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq" and not isinstance(correct_answer, list):
        all_opts = [correct_answer] + traps[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_answer}
            for i, v in enumerate(all_opts)
        ]
        final_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        final_answer = correct_answer

    question_text = _stem(question_type, detail, interaction_mode)

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_shapeboard",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=final_answer,
        distractors=traps,
        hints=ctx.hints,
        format=f"{interaction_mode}_{answer_collection}",
        format_data=format_data,
        is_visual=True,
        visual_type="ShapeBoard",
        visual_params=vp,
        interaction_mode=interaction_mode,
        answer_collection="mcq" if mcq_options else answer_collection,
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
        given_values={k: v for k, v in ctx.values.items() if k != ctx.blank_target} if ctx.values else None,
        blank_target=ctx.blank_target,
    )
