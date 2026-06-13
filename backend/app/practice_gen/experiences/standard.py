"""
Practice Generation — Standard Experience Wrapper

Simple pass-through wrapper that labels a problem with the "standard"
experience type without altering any other fields.
"""

from __future__ import annotations

from ..dna.base import FormattedProblem

EXPERIENCE_NAME = "standard"


def wrap_standard(problem: FormattedProblem) -> FormattedProblem:
    """
    Apply the standard (no-op) experience wrapper.

    Sets problem.experience to "standard" and returns the problem
    unchanged in all other respects.

    Args:
        problem: A fully constructed FormattedProblem from a formatter.

    Returns:
        The same problem instance with experience = "standard".
    """
    problem.experience = EXPERIENCE_NAME
    return problem
