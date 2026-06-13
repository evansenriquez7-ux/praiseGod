"""
Practice Generation — Scaffolded Experience Wrapper

Ascending-difficulty sequence along a single difficulty axis.
The student works through each level of the axis from easiest to hardest.

Usage:
    sequence = build_scaffold_sequence(dna, grade=2, axis_name="regrouping")
    # → [{"regrouping": "none"}, {"regrouping": "ones"}, ...]
    for step_idx, profile in enumerate(sequence):
        problem = generate_for_profile(dna, node_id, grade, seed, profile)
        problem = wrap_scaffolded(problem, step_idx, len(sequence))
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..dna.base import DNA, FormattedProblem

EXPERIENCE_NAME = "scaffolded"


def wrap_scaffolded(
    problem: FormattedProblem,
    step_index: int,
    total_steps: int,
) -> FormattedProblem:
    """
    Apply the scaffolded experience wrapper.

    Sets problem.experience to "scaffolded" and embeds step position
    so the frontend can render a progress bar.

    Args:
        problem: A fully constructed FormattedProblem.
        step_index: Zero-based index of the current step (0 = easiest).
        total_steps: Total number of steps in the scaffold sequence.

    Returns:
        The same problem instance with experience fields updated.
    """
    total = max(total_steps, 1)
    step = max(0, min(step_index, total - 1))

    problem.experience = EXPERIENCE_NAME
    problem.experience_config = {
        "step_index": step,
        "total_steps": total,
        "is_final_step": step >= total - 1,
        "progress_fraction": step / max(total - 1, 1),
    }
    return problem


def build_scaffold_sequence(
    dna: DNA,
    grade: int,
    axis_name: Optional[str],
) -> List[Dict[str, str]]:
    """
    Build an ordered list of difficulty profiles for a scaffold sequence.

    Each profile contains a single axis key mapped to one level, ordered
    from easiest (index 0) to hardest (last index).

    If axis_name is None, the first axis declared in dna.difficulty_axes
    is used.  If the DNA has no difficulty axes at all, returns a single
    empty profile (one unconstrained step).

    Args:
        dna: DNA specification whose difficulty_axes define the levels.
        grade: Student grade level (used for future per-grade axis filtering;
               currently passed through for caller convenience).
        axis_name: Name of the axis to scaffold over (e.g. "regrouping").
            Pass None to use the DNA's first declared axis.

    Returns:
        Ordered list of profile dicts, one per level.

    Examples:
        >>> build_scaffold_sequence(addition_dna, grade=2, axis_name="regrouping")
        [
            {"regrouping": "none"},
            {"regrouping": "ones"},
            {"regrouping": "tens"},
            {"regrouping": "double"},
        ]
    """
    if not dna.difficulty_axes:
        return [{}]

    # Resolve axis name: use first declared axis if None provided.
    if axis_name is None:
        axis_name = next(iter(dna.difficulty_axes))

    levels = dna.difficulty_axes.get(axis_name)
    if not levels:
        # Axis name not found — fall back to first axis.
        first_axis = next(iter(dna.difficulty_axes))
        levels = dna.difficulty_axes[first_axis]
        axis_name = first_axis

    return [{axis_name: level} for level in levels]
