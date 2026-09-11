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
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors
from backend.app.practice_gen.formatters._option_order import shuffle_options


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

def _stem(params: dict, interaction_mode: str, cumulative_vocab: set) -> str:
    # "number line" (and its bare substring "line") may not be introduced yet at
    # early nodes. Rather than guess a fallback phrase that could itself collide
    # with some other gated term, drop the visual's name entirely when unknown —
    # the visual itself is self-explanatory without it.
    known = "number line" in cumulative_vocab
    suffix = " on the number line" if known else ""

    ct = params.get("content_type", "whole_number")
    if interaction_mode == "set":
        if ct == "improper_fraction":
            return f"Move the dot to show {params['fraction_display']}{suffix}."
        if ct == "mixed_number":
            return f"Move the dot to show {params['fraction_display']}{suffix}."
        if ct == "fraction":
            return f"Move the dot to show {params['numerator']}/{params['denominator']}{suffix}."
        if ct == "decimal":
            return f"Move the dot to show {params['decimal_value']}{suffix}."
        return f"Move the dot to show {params['value']}{suffix}."
    else:  # read
        return f"What number is marked{suffix}?"


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
    
    range_span = max(b, 10)
    
    if result <= 20:
        start = 0
        end = 20
        major_interval = 5
        minor_interval = 1
    elif result <= 50:
        start = 0
        end = ((result // 10) + 2) * 10
        major_interval = 10
        minor_interval = 5
    else:
        if range_span <= 100:
            minor_interval = 5
            major_interval = 10
        elif range_span <= 1000:
            minor_interval = 50
            major_interval = 100
        else:
            minor_interval = 100
            major_interval = 500
            
        start = (max(0, a - major_interval) // major_interval) * major_interval
        end = ((result + major_interval) // major_interval) * major_interval
        
    divisions = (end - start) // minor_interval
    if divisions > 50:
        minor_interval = major_interval
        major_interval = major_interval * 5
        start = (max(0, a - major_interval) // major_interval) * major_interval
        end = ((result + major_interval) // major_interval) * major_interval
        divisions = (end - start) // minor_interval

    return {
        "start": start,
        "end": end,
        "major_interval": major_interval,
        "minor_interval": minor_interval,
        "interval": minor_interval,
        "dot_value": a,
        "move_by": b,
        "content_type": "whole_number",
        "value": result,
        "correct_position": result,
        "divisions": divisions,
    }

def _build_multiplication_params(values: dict, seed: int) -> dict:
    """
    Build number-line params for multiplication drawn as EQUAL JUMPS.

    mat_g2_na_q3_1 names four media -- "concrete and pictorial models and numerals,
    ... groups of equal quantities, arrays, counting by multiples, and equal jumps on
    a number line". Arrays were served by GridArea; the jumps were described in words
    over a line that never showed them ("Starting at 0, taking 2 equal jumps of 9 on
    the number line lands on ___", drawn as a bare dot). The picture IS what the
    clause names, so the payload declares the jumps and the component draws one arc
    each.

    `a` is the size of one jump and `b` how many are taken, matching this DNA's own
    group wording ("There are {b} groups of {a}"). The axis carries one tick per jump
    -- so the line itself counts by multiples of `a`, the same clause's "counting by
    multiples" -- and runs one jump past the landing point, so the answer is never
    simply the end of the line.
    """
    a = int(values["a"])
    b = int(values["b"])
    if a < 1 or b < 1:
        # Fail loudly rather than drawing an empty axis: start == end would also trip
        # §1G, but with a message about an axis rather than about the jumps.
        raise ValueError(
            f"number_line cannot draw {b} equal jump(s) of {a} (seed {seed}): a jump of "
            f"nothing, or no jumps at all, renders an empty line."
        )
    start = 0
    end = a * (b + 1)
    return {
        "start": start,
        "end": end,
        "interval": a,
        "minor_interval": a,
        "major_interval": a,
        "divisions": b + 1,
        # The dot stays at the start. Pre-marking the landing point would answer the
        # question the stem asks.
        "dot_value": start,
        "value": a * b,
        "correct_position": a * b,
        "content_type": "whole_number",
        "jump_from": start,
        "jump_size": a,
        "jump_count": b,
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
    
    range_span = max(b, 10)
    
    if a <= 20:
        start = 0
        end = 20
        major_interval = 5
        minor_interval = 1
    elif a <= 50:
        start = 0
        end = ((a // 10) + 2) * 10
        major_interval = 10
        minor_interval = 5
    else:
        if range_span <= 100:
            minor_interval = 5
            major_interval = 10
        elif range_span <= 1000:
            minor_interval = 50
            major_interval = 100
        else:
            minor_interval = 100
            major_interval = 500
            
        start = (max(0, result - major_interval) // major_interval) * major_interval
        end = ((a + major_interval) // major_interval) * major_interval
        
    divisions = (end - start) // minor_interval
    if divisions > 50:
        minor_interval = major_interval
        major_interval = major_interval * 5
        start = (max(0, result - major_interval) // major_interval) * major_interval
        end = ((a + major_interval) // major_interval) * major_interval
        divisions = (end - start) // minor_interval
    
    return {
        "start": start,
        "end": end,
        "major_interval": major_interval,
        "minor_interval": minor_interval,
        "interval": minor_interval,
        "dot_value": a,
        "move_by": -b,
        "content_type": "whole_number",
        "value": result,
        "correct_position": result,
        "divisions": divisions,
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
    
    # Find if we have a numeric target in values.
    #
    # FAILS WHERE THE VALUE IS NEEDED, not here. This parse used to raise the moment an
    # `answer` would not survive int(), which is right for the generic "mark this number"
    # path below -- that path cannot work without it -- and wrong for every concept
    # branch that builds its line from `a` and `b` and never reads `target_num` at all.
    #
    # The difference is not academic: `money_peso` legitimately keys a STRING on its
    # notation and denomination competencies ("1 P5 coin", "P10", "two thousand four
    # hundred sixty-three pesos"), while keying a plain integer on its add/subtract ones.
    # So the eager raise turned "this formatter cannot serve this ITEM" into a crash on
    # any node that does both, and the empirical exclusions file could not save it --
    # that file probes 12 fixed seeds and is documented as guarding against false
    # REFUSALS, not against a pair that serves at those seeds and raises at others.
    # Found 2026-09-11 on mat_g1_na_q4_3 the moment number_line_read was declared for
    # money_peso.
    #
    # `_unparseable_target` carries the reason forward so the generic branch can raise
    # exactly the message it used to, naming the offending value. Nothing is swallowed:
    # a numeric path that needs the value and cannot get it still fails loudly.
    target_num = None
    _unparseable_target = None
    for _key in ("number", "answer"):
        if _key in values:
            try:
                target_num = int(values[_key])
            except (ValueError, TypeError):
                _unparseable_target = (_key, values[_key])
            break

    # ── 1. Resolve visual_params ───────────────────────────────────────────────
    if ctx.visual_params and "correct_position" in ctx.visual_params:
        vp = ctx.visual_params.copy()
    elif ctx.dna_concept == "addition" and "a" in values and "b" in values:
        # Build addition-specific number line with hops
        vp = _build_addition_params(values, ctx.grade, rng)
    elif ctx.dna_concept == "subtraction" and "a" in values and "b" in values:
        # Build subtraction-specific number line with hops
        vp = _build_subtraction_params(values, ctx.grade, rng)
    elif ctx.dna_concept == "multiplication" and "a" in values and "b" in values:
        # Equal jumps. Like the money branch below, this has to exist BEFORE the
        # formatter may be declared compatible with the DNA: without it multiplication
        # falls through to the generic "mark this number" path, which takes its target
        # from values["answer"] -- a line with the product already marked on it.
        vp = _build_multiplication_params(values, ctx.seed)
    elif ctx.dna_concept == "money_peso" and "a" in values and "b" in values:
        # Money on a number line. `money_peso` computes either an addition
        # ("add_amounts") or a subtraction ("find_change"), and a peso amount is a
        # VALUE, so the hop builders above render it correctly as-is: a dot at the
        # starting amount and a hop of the second amount, with the pupil reading off
        # where it lands.
        #
        # This branch has to exist before the formatter may be declared compatible with
        # money_peso. Without it the concept falls through to the generic
        # "mark target_num" path at the bottom, which takes its target from
        # values["answer"] -- so a stem asking "Marco had P20 and spent P5, how much is
        # left?" would render a line with 15 already marked on it. Declaring a visual
        # formatter compatible with a DNA it has no branch for does not make it render
        # that DNA; it makes it render a fallback, and here the fallback leaks the
        # answer (found 2026-09-11 before the declaration was made, not after).
        if str(values.get("operation", "")).startswith("find_change") or \
                values.get("operation") == "subtract":
            vp = _build_subtraction_params(values, ctx.grade, rng)
        else:
            vp = _build_addition_params(values, ctx.grade, rng)
    elif ctx.dna_concept == "rounding" and ("number" in values or target_num is not None):
        value = values.get("number", target_num)
        round_to = values.get("round_to", 10)
        interval = max(1, round_to // 10)
        start_val = (value // round_to) * round_to - round_to
        if start_val < 0:
            start_val = 0
        end_val = ((value // round_to) + 2) * round_to
        divisions = (end_val - start_val) // interval
        vp = {
            "value": value,
            "start": start_val,
            "end": end_val,
            "interval": interval,
            "divisions": divisions,
            "correct_position": value,
            "dot_value": value,
            "content_type": "whole_number",
            "labels": [str(start_val), str(end_val)],
            "marked_points": [],
            "question_mark_at": None,
        }
    elif target_num is None and _unparseable_target is not None:
        _k, _v = _unparseable_target
        raise ValueError(
            f"Invalid {_k!r} value in context: {_v}. `number_line` reached its generic "
            f"'mark this number' path, which needs a numeric target, and {ctx.dna_concept!r} "
            f"supplies none for this item. Either this formatter should not be reachable "
            f"for this (node, item) -- add the concept branch that renders it -- or the "
            f"DNA should not key a non-numeric answer here."
        )
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

    if ctx.dna_concept == "rounding" and "answer" in values:
        correct_val = values["answer"]
    else:
        correct_val = _correct_value(vp)

    # Compute correct float value for grading compatibility in practice_router.py
    ct = vp.get("content_type", "whole_number")
    if ctx.dna_concept == "rounding" and "answer" in values:
        target_val = float(values["answer"])
    elif ct == "fraction":
        target_val = vp["numerator"] / vp["denominator"]
    elif ct == "improper_fraction":
        parts = vp["fraction_display"].split("/")
        target_val = int(parts[0]) / int(parts[1])
    elif ct == "mixed_number":
        whole, frac = vp["fraction_display"].split(" ")
        num, den = frac.split("/")
        target_val = int(whole) + int(num) / int(den)
    elif ct == "decimal":
        target_val = float(vp["decimal_value"])
    else:
        target_val = float(vp.get("value", vp.get("correct_position", 0)))

    vp["correct_answer"] = target_val
    vp["target"] = target_val

    if interaction_mode == "set":
        # In set mode, start the dot at the start of the range to prevent answer leak
        vp["dot_value"] = vp.get("start", 0)
        # Same reason, for the same payload: a drawn run of jumps ENDS on the value the
        # pupil is being asked to place, so a "set" item may not carry one. (Only
        # `number_line_read` is declared for multiplication today; this keeps the
        # invariant with the payload rather than with the declaration table, which is
        # where it would be lost the day `number_line_set` is declared too.)
        for _jump_key in ("jump_from", "jump_size", "jump_count"):
            vp.pop(_jump_key, None)
    else:
        if "dot_value" not in vp:
            vp["dot_value"] = vp.get("value", vp.get("correct_position"))
    
    # For addition/subtraction/multiplication/rounding, use context distractors;
    # otherwise build from traps. Multiplication joins the list because its
    # ErrorPatterns are the misconceptions this item is actually about -- added
    # instead of multiplied (a + b), one group short (a*b - b), one group too many
    # (a*b + b) -- while the trap builder below only knows about positions one
    # division either side of the mark.
    seen = {str(correct_val)}
    if ctx.dna_concept in ("addition", "subtraction", "multiplication", "rounding") and ctx.distractors:
        # A Grade 1-3 pupil has not met numbers below zero, so a negative ErrorPattern
        # value ("a - b" when b > a) is unreadable rather than tempting. fmt_mcq and
        # fmt_cloze have each carried this guard for their own option pools since blind
        # review flagged -34/-14/-3 across money, addition and multiplication; this
        # formatter never had it, and offered -1 on mat_g1_na_q3_0 and -50/-500 on
        # mat_g3_na_q2_5 (measured 2026-09-11). The padding loop below refills the slot
        # from the axis.
        distractor_vals = [
            d for d in ctx.distractors
            if d != correct_val and not (isinstance(d, (int, float))
                                         and not isinstance(d, bool) and d < 0)
        ][:3]
        for d in distractor_vals:
            seen.add(str(d))
    else:
        traps = _build_traps(vp, rng)
        distractor_vals = []
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
                
    # Fill in if we don't have enough distractors
    offset_mult = 1
    while len(distractor_vals) < 3:
        for sign in [1, -1]:
            offset = offset_mult * sign
            ct = vp.get("content_type", "whole_number")
            
            if ct == "fraction":
                d = vp.get("denominator", 1)
                pos = vp.get("correct_position", 0) + offset
                if pos < 0: pos = 0
                display = f"{pos}/{d}"
            elif ct == "decimal":
                divs = vp.get("divisions", 10)
                pos = vp.get("correct_position", 0) + offset
                if pos < 0: pos = 0
                display = pos / divs
            elif ct == "integer":
                display = vp.get("correct_position", 0) - vp.get("divisions", 10) // 2 + offset
            else:
                display = vp.get("correct_position", 0) + offset * vp.get("interval", 1)
                
            sv = str(display)
            if sv not in seen and display != correct_val:
                seen.add(sv)
                distractor_vals.append(display)
                if len(distractor_vals) >= 3:
                    break
        offset_mult += 1

    # ── 2. Answer collection ──────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        # Check distractor count
        if len(distractor_vals) < 3:
            distractor_vals = augment_distractors(distractor_vals, correct_val, target=3, max_delta=5)
            if len(distractor_vals) < 3:
                raise ValueError(f"NumberLine MCQ requires at least 3 unique distractors, but got {len(distractor_vals)}")
        
        all_opts = [correct_val] + distractor_vals[:3]
        shuffle_options(all_opts, ctx.node_id, ctx.seed)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_val}
            for i, v in enumerate(all_opts)
        ]
        correct_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        correct_answer = correct_val

    # Build question text - special handling for addition/subtraction
    # Use "counting up/back" language aligned with Grade 1 competency
    if ctx.dna_concept == "money_peso" and "a" in values and "b" in values:
        # A money item's own wording survives; the line ILLUSTRATES it.
        #
        # Without this branch the concept fell through to the generic stem at the
        # bottom, "What number is marked on the number line?", which replaced the word
        # problem outright -- "Ate Bea bought a pencil for P40 and an eraser for P20.
        # How much did Ate Bea spend?" became a bare number-line reading with the money
        # gone. That is the identical defect fmt_peso_money carried until earlier today
        # (a formatter's own stem displacing the narrative it was handed), which is why
        # it is worth naming twice: a visual formatter declared compatible with a new
        # DNA needs a stem branch as well as a params branch, or it silently re-asks a
        # different question.
        a, b = values["a"], values["b"]
        subtractive = (str(values.get("operation", "")) in ("find_change", "subtract"))
        if values.get("context") == "word_problem" and ctx.question_text:
            question_text = ctx.question_text
        elif interaction_mode == "read":
            direction = "back" if subtractive else "forward"
            question_text = (
                f"The dot is at \u20b1{a} and it moves {direction} \u20b1{b}. "
                f"Which amount will the dot land on?"
            )
        else:
            sign = "\u2212" if subtractive else "+"
            question_text = f"Show \u20b1{a} {sign} \u20b1{b} on the number line."
    elif ctx.dna_concept == "addition" and "a" in values and "b" in values:
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
    elif ctx.dna_concept == "multiplication" and "a" in values and "b" in values:
        # A visual formatter declared for a new DNA needs a STEM branch as well as a
        # params branch, or the generic "What number is marked?" below silently
        # replaces the question the item was generated to ask (fmt_peso_money and this
        # formatter's own money branch each paid for that lesson on 2026-09-11).
        a, b = values["a"], values["b"]
        # "number line" is not introduced vocabulary at every node this can reach, and
        # the picture is self-explanatory without its name -- same treatment as _stem().
        where = " on the number line" if "number line" in set(ctx.cumulative_vocab) else ""
        _mul_task_type = values.get("task_type")
        if interaction_mode == "read":
            # A jump count of 1 is rare but reachable (the DNA thins, rather than
            # bans, its degenerate operands), and "After 1 jumps" is the same missing
            # pluralization blind reviewers flagged across the tree.
            jump_word = "jump" if b == 1 else "jumps"
            if _mul_task_type == "skip_counting":
                question_text = (
                    f"The arrows show counting by {a}s{where}. "
                    f"After {b} {jump_word}, which number do you land on?"
                )
            elif _mul_task_type == "repeated_addition":
                terms = " + ".join([str(a)] * b) if b <= 5 else f"{a} added {b} times"
                question_text = (
                    f"The arrows show {terms}{where}. "
                    f"Which number {'does the jump' if b == 1 else 'do the jumps'} land on?"
                )
            else:
                question_text = (
                    f"Start at 0 and take {b} equal {jump_word} of {a}{where}. "
                    f"Which number do you land on?"
                )
        else:
            # Unreachable today (only `number_line_read` is declared for
            # multiplication) but the jumps are stripped from a "set" payload above,
            # so the pupil is placing the landing point, not reading it.
            question_text = f"Show {b} equal {'jump' if b == 1 else 'jumps'} of {a}{where}."
    elif ctx.dna_concept == "rounding":
        num = values.get("number", vp.get("value"))
        precision = values.get("round_to", 10)
        if interaction_mode == "read":
            question_text = f"The number {num} is marked on the number line. Round {num} to the nearest {precision}."
        else:
            question_text = f"Round {num} to the nearest {precision}."
    else:
        question_text = _stem(vp, interaction_mode, set(ctx.cumulative_vocab))

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
        given_values={k: v for k, v in ctx.values.items() if k != ctx.blank_target} if ctx.values else None,
        blank_target=ctx.blank_target,
    )
