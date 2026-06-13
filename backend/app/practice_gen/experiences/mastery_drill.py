"""
Practice Generation — Mastery Drill Experience Wrapper

Rapid-fire practice until the student achieves N correct answers in a row.
Used for G1–3 fact fluency (e.g. addition to 20, multiplication tables).

Typical loop:
    state = {}
    while not is_mastered(state):
        problem = wrap_mastery_drill(next_problem, state)
        # ... student answers ...
        state = update_drill_state(state, is_correct=True)
"""

from __future__ import annotations

from typing import Dict

from ..dna.base import FormattedProblem

EXPERIENCE_NAME = "mastery_drill"

# 3 consecutive correct responses = mastery for G1–3.
MASTERY_THRESHOLD: int = 3


def wrap_mastery_drill(
    problem: FormattedProblem,
    session_state: Dict,
) -> FormattedProblem:
    """
    Apply the mastery-drill experience wrapper.

    Sets problem.experience to "mastery_drill" and embeds the current
    drill session state so the frontend can render progress indicators.

    Args:
        problem: A fully constructed FormattedProblem.
        session_state: Mutable session dict with keys:
            "consecutive_correct"  (int, default 0)
            "total_attempted"      (int, default 0)
            "total_correct"        (int, default 0)
            "is_mastered"          (bool, default False)

    Returns:
        The same problem instance with experience fields updated.
    """
    consecutive = session_state.get("consecutive_correct", 0)

    problem.experience = EXPERIENCE_NAME
    problem.experience_config = {
        "consecutive_correct": consecutive,
        "needed_for_mastery": MASTERY_THRESHOLD,
        "is_mastered": consecutive >= MASTERY_THRESHOLD,
        "total_attempted": session_state.get("total_attempted", 0),
    }
    return problem


def update_drill_state(session_state: Dict, is_correct: bool) -> Dict:
    """
    Return an updated session state after one answer.

    Correct answer  → consecutive_correct +1, total_correct +1.
    Incorrect answer → consecutive_correct reset to 0.
    Either case     → total_attempted +1.
    is_mastered is set to True once consecutive_correct >= MASTERY_THRESHOLD.

    Args:
        session_state: Current drill session dict (not mutated).
        is_correct: Whether the student's last answer was correct.

    Returns:
        New session state dict with updated counts.
    """
    state = dict(session_state)  # shallow copy — don't mutate caller's dict

    state.setdefault("consecutive_correct", 0)
    state.setdefault("total_attempted", 0)
    state.setdefault("total_correct", 0)
    state.setdefault("is_mastered", False)

    state["total_attempted"] += 1

    if is_correct:
        state["consecutive_correct"] += 1
        state["total_correct"] += 1
    else:
        state["consecutive_correct"] = 0

    state["is_mastered"] = state["consecutive_correct"] >= MASTERY_THRESHOLD

    return state


def is_mastered(session_state: Dict) -> bool:
    """
    Return True if the student has reached mastery.

    Args:
        session_state: Current drill session dict.

    Returns:
        True if consecutive_correct >= MASTERY_THRESHOLD.
    """
    return session_state.get("consecutive_correct", 0) >= MASTERY_THRESHOLD
