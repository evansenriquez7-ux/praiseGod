"""
Practice Generation — Hint-Gated Experience Wrapper

Hints unlock one at a time.  Each revealed hint reduces the problem's
score weight by 25 percentage points (floor: 0.25).

Usage pattern:
    problem = wrap_hint_gated(problem)          # initial: no hints shown
    problem = reveal_next_hint(problem)         # student asks for hint 1
    problem = reveal_next_hint(problem)         # student asks for hint 2
"""

from __future__ import annotations

from typing import Dict, Any

from ..dna.base import FormattedProblem

EXPERIENCE_NAME = "hint_gated"


def wrap_hint_gated(
    problem: FormattedProblem,
    hints_revealed: int = 0,
) -> FormattedProblem:
    """
    Apply the hint-gated experience wrapper.

    Sets problem.experience to "hint_gated" and populates
    problem.experience_config with hint state.

    Score weight degrades by 25% per hint revealed, with a floor of 0.25:
        0 hints → 1.00 weight
        1 hint  → 0.75 weight
        2 hints → 0.50 weight
        3 hints → 0.25 weight
        4+ hints → 0.25 weight (floor)

    Args:
        problem: A fully constructed FormattedProblem.
        hints_revealed: Number of hints already shown to the student.
            Clamped to [0, len(problem.hints)] internally.

    Returns:
        The same problem instance with experience fields updated.
    """
    total = len(problem.hints)
    revealed = max(0, min(hints_revealed, total))

    problem.experience = EXPERIENCE_NAME
    problem.experience_config = {
        "total_hints": total,
        "hints_revealed": revealed,
        "visible_hints": problem.hints[:revealed],
        "next_hint_available": revealed < total,
        "score_weight": max(0.25, 1.0 - (revealed * 0.25)),
    }
    return problem


def reveal_next_hint(problem: FormattedProblem) -> FormattedProblem:
    """
    Increment hints_revealed by 1 and return the updated problem.

    If the problem has already shown all available hints, returns the
    problem unchanged.

    Args:
        problem: A hint_gated-wrapped FormattedProblem.

    Returns:
        The same problem instance with hints_revealed incremented (if possible).

    Raises:
        ValueError: If problem.experience_config is None (not hint-gated).
    """
    if problem.experience_config is None:
        # Auto-wrap with current state if somehow called without prior wrap.
        return wrap_hint_gated(problem, hints_revealed=1)

    current = problem.experience_config.get("hints_revealed", 0)
    return wrap_hint_gated(problem, hints_revealed=current + 1)
