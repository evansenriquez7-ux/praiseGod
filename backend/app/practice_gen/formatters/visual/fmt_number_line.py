"""
fmt_number_line.py — NumberLine visual formatter

Produces a FormattedProblem with number-line visual_params.
Carves generation logic from visual_skeletons.py _gen_number_line /
_traps_number_line; does NOT import from that module.

interaction_mode:
    "read" — number line shown with a marked point; student identifies the value
    "set"  — student places a point on the number line to show a given value

answer_collection:
    "mcq"            — 4 value choices
    "fill_in_blank"  — student types the value

Grade-appropriate scales
    G1: 0–20, whole numbers, intervals of 1 or 2
    G2: 0–100 / 0–1000, intervals of 5 or 10
    G3: whole numbers up to 10 000; hop visualisation for +/−
    G4+: fractions (proper, improper, mixed), decimals, integers with negatives
"""

import random
from typing import Optional

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# ─────────────────────────────────────────────────────────────────────────────
# Trap builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(params: dict, rng: random.Random) -> dict:
    """Return trap dict mirroring visual_skeletons._traps_number_line."""
    traps: dict = {}
    correct_pos = params["correct_position"]
    divisions = params["divisions"]
    content_type = params.get("content_type", "whole_number")

    if correct_pos > 0:
        traps["off_by_one_left"] = {
            "position": correct_pos - 1,
            "description": "One division to the left",
        }
    if correct_pos < divisions:
        traps["off_by_one_right"] = {
            "position": correct_pos + 1,
            "description": "One division to the right",
        }

    if content_type == "fraction":
        n = params["numerator"]
        d = params["denominator"]
        if n <= divisions and n != correct_pos:
            traps["numerator_only"] = {
                "position": n,
                "description": "Used only numerator, ignored denominator",
            }
        if d <= divisions and d != correct_pos:
            traps["denominator_only"] = {
                "position": d,
                "description": "Used only denominator, ignored numerator",
            }
        if d > 2:
            wrong_pos = round(n / (d * 2) * divisions)
            if wrong_pos != correct_pos and 0 <= wrong_pos <= divisions:
                traps["larger_denom_larger_value"] = {
                    "position": wrong_pos,
                    "description": "Thinks larger denominator means larger fraction",
                }
        if n != d and n != 0:
            inverted_pos = round((d / n) * divisions)
            if inverted_pos != correct_pos and 0 <= inverted_pos <= divisions:
                traps["inverted_fraction"] = {
                    "position": inverted_pos,
                    "description": "Flipped numerator and denominator",
                }

    elif content_type == "integer":
        value = params["value"]
        if value < 0:
            positive_pos = -value + divisions // 2
            if positive_pos != correct_pos and 0 <= positive_pos <= divisions:
                traps["ignore_negative"] = {
                    "position": positive_pos,
                    "description": "Ignored negative sign",
                }
            if abs(value) > 2:
                confused_pos = (-abs(value) + 2) + divisions // 2
                if confused_pos != correct_pos and 0 <= confused_pos <= divisions:
                    traps["negative_magnitude_confusion"] = {
                        "position": confused_pos,
                        "description": "Compared absolute values incorrectly",
                    }

    elif content_type == "decimal":
        digits_str = str(params["decimal_value"]).replace("0.", "")
        if len(digits_str) == 2:
            wrong_val = int(digits_str[0]) / 10
            wrong_pos = int(wrong_val * divisions)
            if wrong_pos != correct_pos and 0 <= wrong_pos <= divisions:
                traps["whole_number_decimal_thinking"] = {
                    "position": wrong_pos,
                    "description": "Compared decimal digits as whole numbers",
                }

    return traps


# ─────────────────────────────────────────────────────────────────────────────
# Visual-params builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_visual_params(
    grade: int, diff_level: int, rng: random.Random, competency_text: Optional[str] = None
) -> dict:
    """
    Build number-line visual_params for a given grade / difficulty.

    Returns dict suitable for the frontend NumberLine renderer.
    Fields: start, end, interval, divisions, correct_position, content_type,
            labels, is_interactive, and type-specific keys.
    """
    import re

    # ── Grade 1–2: whole numbers ──────────────────────────────────────────────
    if grade <= 2:
        max_val = 10 if diff_level == 1 else 20
        value = rng.randint(1, max_val - 1)
        interval = 1
        if value <= 15:
            start_val = 0
            end_val = max(10, ((value // 10) + 1) * 10)
        else:
            start_val = (value // 10) * 10
            end_val = start_val + 10
            if value == start_val and start_val > 0:
                start_val -= 10
            if value == end_val:
                end_val += 10

        return {
            "value": value,
            "start": start_val,
            "end": end_val,
            "interval": interval,
            "divisions": (end_val - start_val) // interval,
            "correct_position": value,
            "content_type": "whole_number",
            "labels": [str(start_val), str(end_val)],
            "is_interactive": True,
            "marked_points": [],
            "question_mark_at": None,
        }

    # ── Grade 3: larger whole numbers; hop visualisation ─────────────────────
    if grade == 3:
        max_val = 100 if diff_level <= 2 else 1000
        interval = 10 if max_val == 100 else 100
        value = rng.randint(1, max_val // interval - 1) * interval
        hop_from = rng.randint(0, value - interval)
        hop_by = value - hop_from
        
        # Window around the target value
        start_val = max(0, value - interval * 4)
        end_val = start_val + interval * 8
        if hop_from < start_val:
            start_val = max(0, hop_from - interval)
            end_val = start_val + interval * 8

        return {
            "value": value,
            "start": start_val,
            "end": end_val,
            "interval": interval,
            "divisions": (end_val - start_val) // interval,
            "correct_position": value // interval,
            "content_type": "whole_number",
            "labels": [str(start_val), str(end_val)],
            "is_interactive": True,
            "marked_points": [],
            "question_mark_at": None,
            # hop visualisation (addition / subtraction on number line)
            "hop_from": hop_from,
            "hop_by": hop_by,
        }

    # ── Grade 4–5: fractions ──────────────────────────────────────────────────
    if grade <= 5:
        allow_improper = False
        allow_mixed = False
        allowed_denoms = None

        if competency_text:
            denom_match = re.search(
                r"denominators?\s+([\d,\s]+(?:and\s+\d+)?)", competency_text, re.IGNORECASE
            )
            if denom_match:
                nums = re.findall(r"\d+", denom_match.group(1))
                allowed_denoms = [int(n) for n in nums] if nums else None
            if re.search(r"improper", competency_text, re.IGNORECASE):
                allow_improper = True
            if re.search(r"mixed", competency_text, re.IGNORECASE):
                allow_mixed = True

        denominator = rng.choice(allowed_denoms) if allowed_denoms else rng.choice(
            [2, 3, 4] if diff_level == 1 else [2, 3, 4, 5, 6, 8]
        )

        if allow_improper or allow_mixed:
            fraction_type = rng.choice(
                ["improper", "mixed"] if (allow_improper and allow_mixed)
                else ["improper"] if allow_improper else ["mixed"]
            )
            if fraction_type == "improper":
                max_whole = 2 if diff_level == 1 else 3
                whole_part = rng.randint(1, max_whole)
                extra_num = rng.randint(1, denominator - 1)
                numerator = whole_part * denominator + extra_num
                return {
                    "numerator": numerator,
                    "denominator": denominator,
                    "start": 0,
                    "end": whole_part + 1,
                    "interval": 1,
                    "divisions": (whole_part + 1) * denominator,
                    "correct_position": numerator,
                    "content_type": "improper_fraction",
                    "fraction_display": f"{numerator}/{denominator}",
                    "labels": ["0", str(whole_part + 1)],
                    "is_interactive": True,
                    "marked_points": [],
                    "question_mark_at": None,
                }
            else:  # mixed
                whole_part = rng.randint(1, 2 if diff_level == 1 else 3)
                proper_num = rng.randint(1, denominator - 1)
                return {
                    "whole_part": whole_part,
                    "numerator": proper_num,
                    "denominator": denominator,
                    "start": 0,
                    "end": whole_part + 1,
                    "interval": 1,
                    "divisions": (whole_part + 1) * denominator,
                    "correct_position": whole_part * denominator + proper_num,
                    "content_type": "mixed_number",
                    "fraction_display": f"{whole_part} {proper_num}/{denominator}",
                    "labels": ["0", str(whole_part + 1)],
                    "is_interactive": True,
                    "marked_points": [],
                    "question_mark_at": None,
                }

        # Proper fraction
        numerator = rng.randint(1, denominator - 1)
        return {
            "numerator": numerator,
            "denominator": denominator,
            "start": 0,
            "end": 1,
            "interval": 1,
            "divisions": denominator,
            "correct_position": numerator,
            "content_type": "fraction",
            "labels": ["0", "1"],
            "is_interactive": True,
            "marked_points": [],
            "question_mark_at": None,
        }

    # ── Grade 6: decimals ─────────────────────────────────────────────────────
    if grade == 6:
        decimal_places = 1 if diff_level == 1 else 2
        divisions = 10 if decimal_places == 1 else 100
        value = rng.randint(1, divisions - 1) / divisions
        return {
            "decimal_value": value,
            "start": 0,
            "end": 1,
            "interval": 1,
            "divisions": divisions,
            "correct_position": int(value * divisions),
            "content_type": "decimal",
            "labels": ["0", "1"],
            "is_interactive": True,
            "marked_points": [],
            "question_mark_at": None,
        }

    # ── Grade 7+: integers with negatives ────────────────────────────────────
    range_size = 10 if diff_level == 1 else 20
    value = rng.randint(-range_size // 2, range_size // 2)
    while value == 0:
        value = rng.randint(-range_size // 2, range_size // 2)
    return {
        "value": value,
        "start": -range_size // 2,
        "end": range_size // 2,
        "interval": 1,
        "divisions": range_size,
        "correct_position": value + range_size // 2,
        "content_type": "integer",
        "labels": [str(-range_size // 2), str(range_size // 2)],
        "is_interactive": True,
        "marked_points": [],
        "question_mark_at": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Question-text builder
# ─────────────────────────────────────────────────────────────────────────────

def _stem(params: dict, interaction_mode: str) -> str:
    ct = params.get("content_type", "whole_number")
    if interaction_mode == "set":
        if ct == "improper_fraction":
            return f"Move the dot to show {params['fraction_display']} on the number line."
        if ct == "mixed_number":
            return f"Move the dot to show {params['fraction_display']} on the number line."
        if ct == "fraction":
            return f"Move the dot to show {params['numerator']}/{params['denominator']} on the number line."
        if ct == "decimal":
            return f"Move the dot to show {params['decimal_value']} on the number line."
        return f"Move the dot to show {params['value']} on the number line."
    else:  # read
        return "What number is marked on the number line?"


# ─────────────────────────────────────────────────────────────────────────────
# Correct-answer extractor
# ─────────────────────────────────────────────────────────────────────────────

def _correct_value(params: dict):
    ct = params.get("content_type", "whole_number")
    if ct == "fraction":
        return f"{params['numerator']}/{params['denominator']}"
    if ct == "improper_fraction":
        return params["fraction_display"]
    if ct == "mixed_number":
        return params["fraction_display"]
    if ct == "decimal":
        return params["decimal_value"]
    return params.get("value", params.get("correct_position"))


def _build_addition_params(values: dict, grade: int, rng: random.Random) -> dict:
    """
    Build number line params for addition problems.
    
    Places a dot at position 'a'. Student must determine where it lands
    after moving 'b' spaces forward.
    """
    a = values.get("a", 0)
    b = values.get("b", 0)
    result = values.get("result", a + b)
    
    # Choose a clean end value that fits the result with room
    if result <= 10:
        end = 10
    elif result <= 20:
        end = 20
    elif result <= 50:
        end = ((result // 10) + 2) * 10
    else:
        end = ((result // 50) + 1) * 50
    
    # Major interval (labeled ticks)
    if end <= 10:
        major_interval = 1
    elif end <= 20:
        major_interval = 5
    else:
        major_interval = 10
    
    # Minor interval (unlabeled small ticks between majors)
    if end <= 10:
        minor_interval = 1
    elif end <= 20:
        minor_interval = 1
    else:
        minor_interval = 5
    
    return {
        "start": 0,
        "end": end,
        "major_interval": major_interval,
        "minor_interval": minor_interval,
        "dot_value": a,           # dot is placed here
        "move_by": b,             # how many spaces to move forward
        "content_type": "whole_number",
        "value": result,
        "correct_position": result,
        "divisions": end,
    }


def _build_subtraction_params(values: dict, grade: int, rng: random.Random) -> dict:
    """
    Build number line params for subtraction problems.
    
    Places a dot at position 'a'. Student must determine where it lands
    after moving 'b' spaces backward.
    """
    a = values.get("a", 0)
    b = values.get("b", 0)
    result = values.get("result", a - b)
    
    # Choose a clean end value based on the minuend
    if a <= 10:
        end = 10
    elif a <= 20:
        end = 20
    elif a <= 50:
        end = ((a // 10) + 2) * 10
    else:
        end = ((a // 50) + 1) * 50
    
    if end <= 10:
        major_interval = 1
        minor_interval = 1
    elif end <= 20:
        major_interval = 5
        minor_interval = 1
    else:
        major_interval = 10
        minor_interval = 5
    
    return {
        "start": 0,
        "end": end,
        "major_interval": major_interval,
        "minor_interval": minor_interval,
        "dot_value": a,           # dot is placed here
        "move_by": -b,            # negative = move backward
        "content_type": "whole_number",
        "value": result,
        "correct_position": result,
        "divisions": end,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_number_line(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a NumberLine FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Number line pre-set with a marked point; student identifies the value.
    interaction_mode "set":
        Student places a point to represent a given value.

    answer_collection "mcq":
        Four choices derived from trap positions.
    answer_collection "fill_in_blank":
        Student types the answer.
    """
    values = ctx.values or {}
    
    # Find if we have a numeric target in values
    target_num = None
    if "number" in values:
        try:
            target_num = int(values["number"])
        except (ValueError, TypeError):
            pass
    elif "answer" in values:
        try:
            target_num = int(values["answer"])
        except (ValueError, TypeError):
            pass

    # ── 1. Resolve visual_params ───────────────────────────────────────────────
    if ctx.visual_params and "correct_position" in ctx.visual_params:
        vp = ctx.visual_params.copy()
    elif ctx.dna_concept == "addition" and "a" in values and "b" in values:
        # Build addition-specific number line with hops
        vp = _build_addition_params(values, ctx.grade, rng)
    elif ctx.dna_concept == "subtraction" and "a" in values and "b" in values:
        # Build subtraction-specific number line with hops
        vp = _build_subtraction_params(values, ctx.grade, rng)
    elif target_num is not None:
        # Handle static number payload (e.g. from number_reading, place_value, or counting)
        value = target_num
        if value <= 15:
            start_val = 0
            end_val = max(10, ((value // 10) + 1) * 10)
            interval = 1
        else:
            start_val = (value // 10) * 10
            end_val = start_val + 10
            if value == start_val and start_val > 0:
                start_val -= 10
            if value == end_val:
                end_val += 10
            interval = 1

        vp = {
            "value": value,
            "start": start_val,
            "end": end_val,
            "interval": interval,
            "divisions": (end_val - start_val) // interval,
            "correct_position": value,
            "dot_value": value,
            "content_type": "whole_number",
            "labels": [str(start_val), str(end_val)],
            "marked_points": [],
            "question_mark_at": None,
        }
    else:
        diff_profile = ctx.difficulty_profile or {}
        diff_level = min(len(diff_profile) + 1, 4) if diff_profile else 2
        vp = _build_visual_params(
            ctx.grade,
            diff_level,
            random.Random(ctx.seed),
            getattr(ctx, "competency_text", None),
        )

    vp["is_interactive"] = (interaction_mode == "set")
    vp.setdefault("show_labels", True)
    if "dot_value" not in vp:
        vp["dot_value"] = vp.get("value", vp.get("correct_position"))

    correct_val = _correct_value(vp)
    
    # For addition/subtraction, use context distractors; otherwise build from traps
    if ctx.dna_concept in ("addition", "subtraction") and ctx.distractors:
        distractor_vals = [d for d in ctx.distractors if d != correct_val][:3]
    else:
        traps = _build_traps(vp, rng)
        distractor_vals = []
        seen = {str(correct_val)}
        for t in traps.values():
            pos = t.get("position")
            if pos is None:
                continue
            ct = vp.get("content_type", "whole_number")
            if ct == "fraction":
                d = vp["denominator"]
                display = f"{pos}/{d}"
            elif ct == "decimal":
                divs = vp["divisions"]
                display = pos / divs
            elif ct == "integer":
                display = pos - vp["divisions"] // 2
            else:
                display = pos
            sv = str(display)
            if sv not in seen:
                seen.add(sv)
                distractor_vals.append(display)
            if len(distractor_vals) == 3:
                break

    # ── 2. Answer collection ──────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        # Pad distractors if needed
        if len(distractor_vals) < 3 and isinstance(correct_val, (int, float)):
            fallbacks = [correct_val - 1, correct_val + 1, correct_val - 2, correct_val + 2]
            for fb in fallbacks:
                if fb not in distractor_vals and fb != correct_val and fb >= 0:
                    distractor_vals.append(fb)
                if len(distractor_vals) >= 3:
                    break
        
        all_opts = [correct_val] + distractor_vals[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_val}
            for i, v in enumerate(all_opts)
        ]
        correct_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        correct_answer = correct_val

    # Build question text - special handling for addition/subtraction
    # Use "counting up/back" language aligned with Grade 1 competency
    if ctx.dna_concept == "addition" and "a" in values and "b" in values:
        a, b = values["a"], values["b"]
        num_word = "number" if b == 1 else "numbers"
        if interaction_mode == "read":
            question_text = f"The dot is at {a} and it moves forward {b} {num_word}. Starting from {a}, just count up {b} {num_word}. Which number will the dot land on?"
        else:
            question_text = f"Show {a} + {b} on the number line."
    elif ctx.dna_concept == "subtraction" and "a" in values and "b" in values:
        a, b = values["a"], values["b"]
        num_word = "number" if b == 1 else "numbers"
        if interaction_mode == "read":
            question_text = f"The dot is at {a} and it moves backward {b} {num_word}. Starting from {a}, just count back {b} {num_word}. Which number will the dot land on?"
        else:
            question_text = f"Show {a} − {b} on the number line."
    else:
        question_text = _stem(vp, interaction_mode)

    format_data: dict = {"visual_params": vp}
    if mcq_options is not None:
        format_data["mcq_options"] = mcq_options

    fmt = f"{interaction_mode}_{answer_collection}"

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_numberline",
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
        visual_type="NumberLine",
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
