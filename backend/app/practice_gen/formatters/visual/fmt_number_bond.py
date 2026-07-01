"""
fmt_number_bond.py — NumberBond visual formatter

NEW formatter — gap analysis addition (Part-Part-Whole visual).
Does NOT import from visual_skeletons.py.

Shows a number bond: whole circle at top, two part circles branching below.

    [  whole  ]
    /          \\
[part1]    [part2]

One circle is blank; student finds the missing value.

interaction_mode:
    "read" — number bond shown with one blank; student identifies the missing value
    "set"  — student fills in the blank circle

visual_params:
    {
        "whole":          int | None,
        "part1":          int | None,
        "part2":          int | None,
        "blank_position": "whole" | "part1" | "part2",
    }

Correct answer:
    blank "whole"  → part1 + part2
    blank "part1"  → whole - part2
    blank "part2"  → whole - part1

Grade bounds:
    G1 — whole ≤ 20
    G2 — whole ≤ 100
    G3 — whole ≤ 1000

Traps:
    wrong_op   — adds instead of subtracts (or vice versa)
    off_by_one — answer ± 1
    use_whole  — uses whole value as answer (when blank is a part)
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors


# ─────────────────────────────────────────────────────────────────────────────
# Grade bounds
# ─────────────────────────────────────────────────────────────────────────────

_WHOLE_MAX = {1: 20, 2: 100, 3: 1000}


def _max_whole(grade: int) -> int:
    return _WHOLE_MAX.get(grade, _WHOLE_MAX[3])


# ─────────────────────────────────────────────────────────────────────────────
# Bond generator
# ─────────────────────────────────────────────────────────────────────────────

def _build_bond(grade: int, diff_level: int, rng: random.Random, blank_position: str) -> dict:
    """
    Generate a number bond for the given grade and blank position.
    """
    max_w = _max_whole(grade)
    # Keep numbers small enough at low difficulty
    if diff_level == 1:
        max_w = max(10, max_w // 4)
    elif diff_level == 2:
        max_w = max(20, max_w // 2)

    whole = rng.randint(2, max_w)
    part1 = rng.randint(1, whole - 1)
    part2 = whole - part1

    if blank_position == "whole":
        return {"whole": None, "part1": part1, "part2": part2, "blank_position": "whole",
                "_whole": whole, "_part1": part1, "_part2": part2}
    if blank_position == "part1":
        return {"whole": whole, "part1": None, "part2": part2, "blank_position": "part1",
                "_whole": whole, "_part1": part1, "_part2": part2}
    return {"whole": whole, "part1": part1, "part2": None, "blank_position": "part2",
            "_whole": whole, "_part1": part1, "_part2": part2}


def _answer_from_bond(bond: dict) -> int:
    bp = bond["blank_position"]
    w, p1, p2 = bond["_whole"], bond["_part1"], bond["_part2"]
    if bp == "whole":
        return w
    if bp == "part1":
        return p1
    return p2


# ─────────────────────────────────────────────────────────────────────────────
# Traps
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(bond: dict, answer: int, rng: random.Random) -> list:
    """
    Return up to 3 distractor values.

    Traps:
        wrong_op   — student adds both known values regardless of position
        off_by_one — answer ± 1
        use_whole  — uses whole as answer when blank is a part
    """
    traps = []
    seen = {answer}
    w = bond["_whole"]
    p1 = bond["_part1"]
    p2 = bond["_part2"]
    bp = bond["blank_position"]

    # Wrong operation: adds both known values
    if bp in ("part1", "part2"):
        # Student adds instead of subtracts
        known_part = p2 if bp == "part1" else p1
        wrong_op = w + known_part
        if wrong_op not in seen and wrong_op > 0:
            traps.append(wrong_op)
            seen.add(wrong_op)
    else:
        # blank is whole; student subtracts instead of adds
        wrong_op = abs(p1 - p2)
        if wrong_op not in seen and wrong_op > 0:
            traps.append(wrong_op)
            seen.add(wrong_op)

    # Off by one
    for delta in (1, -1):
        candidate = answer + delta
        if candidate > 0 and candidate not in seen:
            traps.append(candidate)
            seen.add(candidate)
        if len(traps) >= 3:
            break

    # Use whole as answer (when blank is a part)
    if bp != "whole" and w not in seen:
        traps.append(w)

    rng.shuffle(traps)
    return traps[:3]


# ─────────────────────────────────────────────────────────────────────────────
# Question text
# ─────────────────────────────────────────────────────────────────────────────

def _stem(bond: dict, interaction_mode: str) -> str:
    bp = bond["blank_position"]
    if interaction_mode == "set":
        return "Fill in the missing number in the number bond."
    if bp == "whole":
        return f"The two parts are {bond['part1']} and {bond['part2']}. What is the whole?"
    known_whole = bond["whole"]
    known_part = bond["part2"] if bp == "part1" else bond["part1"]
    return f"The whole is {known_whole} and one part is {known_part}. What is the missing part?"


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_number_bond(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a NumberBond FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Number bond shown with one blank; student identifies the missing value.
    interaction_mode "set":
        Student fills in the blank circle.

    Pulls from ctx.values (addition / missing_number DNAs) when available.
    Keys used: a, b, result, blank_target ("a" | "b" | "result").
    """
    diff_level = 2
    if ctx.difficulty_profile:
        diff_level = min(len(ctx.difficulty_profile) + 1, 4)

    # ── 1. Resolve bond ───────────────────────────────────────────────────────
    if ctx.visual_params and "blank_position" in ctx.visual_params:
        vp_in = ctx.visual_params
        bond = {
            "whole": vp_in.get("whole"),
            "part1": vp_in.get("part1"),
            "part2": vp_in.get("part2"),
            "blank_position": vp_in["blank_position"],
        }
        # Reconstruct private fields for trap generation
        bond["_whole"] = bond["whole"] or (
            (bond["part1"] or 0) + (bond["part2"] or 0)
        )
        bond["_part1"] = bond["part1"] or (bond["_whole"] - (bond["part2"] or 0))
        bond["_part2"] = bond["part2"] or (bond["_whole"] - (bond["part1"] or 0))
    elif ctx.values and "a" in ctx.values:
        a = ctx.values["a"]
        b = ctx.values["b"]
        result = ctx.values.get("result", a + b)
        blank_target = ctx.values.get("blank_target", "result")
        
        # Check if it's subtraction (a - b = result implies a is the whole)
        # We can safely assume if result < a, it's subtraction, but better to check exactly
        is_subtraction = (result == a - b) and (result != a + b or (b == 0 and ctx.node_id and "sub" in ctx.spine_id))
        if not is_subtraction and ctx.spine_id and "sub" in ctx.spine_id:
             is_subtraction = True
             
        if is_subtraction:
            # For subtraction: a is whole, b is part1, result is part2
            pos_map = {"a": "whole", "b": "part1", "result": "part2"}
            blank_position = pos_map.get(blank_target, "part2")
            bond = {
                "whole": None if blank_position == "whole" else a,
                "part1": None if blank_position == "part1" else b,
                "part2": None if blank_position == "part2" else result,
                "blank_position": blank_position,
                "_whole": a, "_part1": b, "_part2": result,
            }
        else:
            # For addition: result is whole, a is part1, b is part2
            pos_map = {"result": "whole", "a": "part1", "b": "part2"}
            blank_position = pos_map.get(blank_target, "whole")
            bond = {
                "whole": None if blank_position == "whole" else result,
                "part1": None if blank_position == "part1" else a,
                "part2": None if blank_position == "part2" else b,
                "blank_position": blank_position,
                "_whole": result, "_part1": a, "_part2": b,
            }
    else:
        blank_position = rng.choice(["whole", "part1", "part2"])
        bond = _build_bond(ctx.grade, diff_level, rng, blank_position)

    answer = _answer_from_bond(bond)

    # ── 2. Build visual_params (no private _keys) ─────────────────────────────
    vp = {
        "whole": bond["whole"],
        "part1": bond["part1"],
        "part2": bond["part2"],
        "blank_position": bond["blank_position"],
    }

    # ── 3. Traps ──────────────────────────────────────────────────────────────
    traps = _build_traps(bond, answer, rng)

    # ── 4. MCQ options ────────────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        if len(traps) < 3:
            traps = augment_distractors(traps, answer, target=3, max_delta=5)
            if len(traps) < 3:
                raise ValueError(f"Formatter 'number_bond' requires at least 3 unique distractors, but got {len(traps)}")
        all_opts = [answer] + traps[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == answer}
            for i, v in enumerate(all_opts)
        ]
        final_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        final_answer = answer

    question_text = _stem(bond, interaction_mode)

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_numberbond",
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
        visual_type="NumberBond",
        visual_params=vp,
        interaction_mode=interaction_mode,
        answer_collection=answer_collection,
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
    )
