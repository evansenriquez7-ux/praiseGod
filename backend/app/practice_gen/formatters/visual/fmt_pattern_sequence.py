"""
fmt_pattern_sequence.py — PatternSequence visual formatter

Refactored from visual_skeletons.py RuleDiscovery + FillInTable generators.
Does NOT import from visual_skeletons.py.

interaction_mode:
    "read" — partial sequence shown; student identifies the next/missing term (mcq or numeric_input)
    "set"  — student fills blank boxes in the sequence

visual_params:
    {
        "sequence":        list,                     # full sequence (all terms)
        "missing_indices": list[int],                # 0-based indices of blanked terms
        "element_type":    "number" | "shape_code" | "mixed",
        "rule":            str,                      # human-readable rule description
    }

Traps: wrong skip interval, reversed direction.
"""

import random
from typing import List, Optional

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors


# ─────────────────────────────────────────────────────────────────────────────
# Sequence builders
# ─────────────────────────────────────────────────────────────────────────────

def _build_sequence(grade: int, diff_level: int, rng: random.Random) -> dict:
    """
    Return dict with keys: sequence, rule, element_type, step.

    Grade bands:
        G1-2: skip-count by 2/5/10, or simple repeating shape codes
        G3-4: multiplication / linear rule
        G5+:  linear with larger coefficients, or shape-code alternating
    """
    if grade <= 2:
        # 50/50: number skip-count or shape-code repeating pattern
        if rng.choice([True, False]):
            step = rng.choice([2, 5, 10])
            start = rng.randint(0, step)
            length = 6 if diff_level <= 2 else 8
            seq = [start + step * i for i in range(length)]
            return {
                "sequence": seq,
                "rule": f"Add {step} each time",
                "element_type": "number",
                "step": step,
                "start": start,
                "pattern_kind": "skip_count",
            }
        else:
            # Shape codes: A/B or A/B/C repeating
            shapes = ["circle", "triangle", "square", "star"]
            period = 2 if diff_level == 1 else 3
            pattern = rng.sample(shapes, period)
            length = 8
            seq = [pattern[i % period] for i in range(length)]
            return {
                "sequence": seq,
                "rule": f"Repeating pattern: {' → '.join(pattern)}",
                "element_type": "shape_code",
                "period": period,
                "base_pattern": pattern,
                "pattern_kind": "repeating",
            }

    if grade <= 4:
        # Multiplication table rows or simple linear
        if rng.choice([True, False]):
            multiplier = rng.choice([2, 3, 4, 5, 10])
            length = 6 if diff_level <= 2 else 8
            seq = [multiplier * i for i in range(1, length + 1)]
            return {
                "sequence": seq,
                "rule": f"Multiply by {multiplier} (×{multiplier} table)",
                "element_type": "number",
                "multiplier": multiplier,
                "pattern_kind": "multiplication",
            }
        else:
            a = rng.choice([2, 3, 4, 5])
            b = rng.randint(0, 10)
            length = 6 if diff_level <= 2 else 7
            seq = [a * n + b for n in range(1, length + 1)]
            return {
                "sequence": seq,
                "rule": f"Multiply position by {a}, then add {b}",
                "element_type": "number",
                "a": a,
                "b": b,
                "pattern_kind": "linear",
            }

    # Grade 5+: linear with larger values or mixed
    a = rng.choice([3, 4, 5, 6, 7])
    b = rng.randint(-10, 20)
    length = 7 if diff_level <= 2 else 9
    seq = [a * n + b for n in range(1, length + 1)]
    return {
        "sequence": seq,
        "rule": f"Rule: {a}n + {b}" if b >= 0 else f"Rule: {a}n {b}",
        "element_type": "number",
        "a": a,
        "b": b,
        "pattern_kind": "linear",
    }


def _choose_missing_indices(length: int, diff_level: int, rng: random.Random) -> List[int]:
    """
    Select which indices to blank out.
    Never blank the first two terms (anchors).
    diff_level 1 → 1 blank, 2 → 2 blanks, 3+ → 3 blanks.
    """
    num_blanks = min(diff_level, 3, length - 2)
    eligible = list(range(2, length))
    return sorted(rng.sample(eligible, num_blanks))


# ─────────────────────────────────────────────────────────────────────────────
# Trap builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_traps(seq_info: dict, missing_indices: List[int]) -> List:
    """
    Return list of distractor values for the primary missing term.

    Traps:
        wrong_step_up   — used step+1 instead of step
        wrong_step_down — used step-1
        reversed_step   — subtracted instead of added
        adjacent_value  — copied the preceding term
    """
    traps = []
    if not missing_indices:
        return traps

    seq = seq_info["sequence"]
    kind = seq_info.get("pattern_kind", "skip_count")
    idx = missing_indices[0]

    if kind in ("skip_count", "multiplication", "linear") and seq_info.get("element_type") == "number":
        correct = seq[idx]
        step = seq_info.get("step") or seq_info.get("a", 1)

        wrong_up = correct + step if (correct + step) != correct else correct + 1
        wrong_down = correct - step if (correct - step) != correct else correct - 1
        reversed_val = seq[idx - 1] - step if idx > 0 else correct - step

        seen = {correct}
        for v in [wrong_up, wrong_down, reversed_val]:
            if v not in seen and v > 0:
                traps.append(v)
                seen.add(v)
            if len(traps) >= 3:
                break

        # Adjacent value trap
        if idx > 0 and seq[idx - 1] not in seen:
            traps.append(seq[idx - 1])

    elif kind == "repeating":
        pattern = seq_info.get("base_pattern", [])
        period = seq_info.get("period", 2)
        correct = seq[idx]
        # Offer other shapes in the pattern
        for shape in pattern:
            if shape != correct and len(traps) < 3:
                traps.append(shape)
        # Fill with off-by-one in cycle
        next_in_cycle = pattern[(idx + 1) % period]
        if next_in_cycle not in traps and next_in_cycle != correct:
            traps.append(next_in_cycle)

    return traps[:3]


# ─────────────────────────────────────────────────────────────────────────────
# Question text
# ─────────────────────────────────────────────────────────────────────────────

def _stem(seq_info: dict, missing_indices: List[int], interaction_mode: str) -> str:
    rule = seq_info["rule"]
    if interaction_mode == "set":
        return f"Fill in the missing terms. Pattern: {rule}."
    # read mode
    if len(missing_indices) == 1:
        pos_label = missing_indices[0] + 1  # 1-indexed for students
        return f"What is the missing term (position {pos_label}) in the pattern?"
    return "What are the missing terms in the pattern?"


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_pattern_sequence(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a PatternSequence FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Partial sequence displayed; student identifies the missing term.
    interaction_mode "set":
        Student fills blank boxes in the sequence.

    Pulls from ctx.values["sequence"] / ctx.values["missing_indices"] when
    available; otherwise generates fresh sequence data.
    """
    # ── 1. Resolve visual_params ───────────────────────────────────────────────
    diff_level = 2
    if ctx.difficulty_profile:
        diff_level = min(len(ctx.difficulty_profile) + 1, 4)

    if ctx.visual_params and "sequence" in ctx.visual_params:
        vp = ctx.visual_params.copy()
        seq_info = vp
    elif ctx.values and "sequence" in ctx.values:
        seq = ctx.values["sequence"]
        missing_indices = ctx.values.get("missing_indices", [len(seq) - 1])
        element_type = ctx.values.get("element_type", "number")
        rule = ctx.values.get("rule", "Follow the pattern")
        seq_info = {
            "sequence": seq,
            "missing_indices": missing_indices,
            "rule": rule,
            "element_type": element_type,
            "pattern_kind": "skip_count" if element_type == "number" else "repeating",
        }
        vp = seq_info
    else:
        seq_info = _build_sequence(ctx.grade, diff_level, rng)
        missing_indices = _choose_missing_indices(len(seq_info["sequence"]), diff_level, rng)
        seq_info["missing_indices"] = missing_indices
        vp = {
            "sequence": seq_info["sequence"],
            "missing_indices": missing_indices,
            "element_type": seq_info["element_type"],
            "rule": seq_info["rule"],
        }
        # Keep aux keys for trap generation
        seq_info.update(vp)

    sequence = vp["sequence"]
    missing_indices = vp.get("missing_indices", [len(sequence) - 1])

    # ── 2. Correct answer ────────────────────────────────────────────────────
    if len(missing_indices) == 1:
        correct_answer = sequence[missing_indices[0]]
    else:
        correct_answer = [sequence[i] for i in missing_indices]

    # ── 3. Traps / distractors ───────────────────────────────────────────────
    traps = _build_traps(seq_info, missing_indices)

    # ── 4. MCQ options ───────────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq" and len(missing_indices) == 1:
        if len(traps) < 3:
            traps = augment_distractors(traps, correct_answer, target=3, max_delta=5)
            if len(traps) < 3:
                raise ValueError(f"Formatter 'pattern_sequence' requires at least 3 unique distractors, but got {len(traps)}")
        all_opts = [correct_answer] + traps[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_answer}
            for i, v in enumerate(all_opts)
        ]
        final_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        final_answer = correct_answer

    question_text = _stem(seq_info, missing_indices, interaction_mode)

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_patternsequence",
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
        visual_type="PatternSequence",
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
