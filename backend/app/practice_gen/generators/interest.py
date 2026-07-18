"""
Practice Generation — Interest Bank
=====================================

Loads interest_bank.json at import time and exposes helpers for
story-spine slot filling.

Responsibilities:
  1. Load interest_bank.json once at module import.
  2. Return interest IDs appropriate for a given grade band.
  3. Build a single slot dict (actor, objects, place, item1, item2)
     for one problem from a specific interest theme.
  4. Pick the best available interest for a student, falling back
     to a grade-appropriate random choice or the neutral fallback.

Source data:
    data/interest_bank.json
    (relative path from project root)
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# Load interest_bank.json at import time.
# generators/ → practice_gen/ → app/ → backend/ → ccmed/ (project root)
# ---------------------------------------------------------------------------
_INTEREST_BANK_PATH: Path = (
    Path(__file__).parent.parent.parent.parent.parent
    / "data"
    / "interest_bank.json"
)

with _INTEREST_BANK_PATH.open(encoding="utf-8") as _f:
    _BANK: Dict = json.load(_f)
_INTERESTS: Dict[str, Dict] = _BANK.get("interests", {})


def _contains_forbidden_term(text: str, not_yet_known: Set[str]) -> bool:
    """
    Whole-word, case-insensitive check of `text` against `not_yet_known` terms.

    Also checks the naive singular form (trailing "s" stripped) because
    Spine.render() collapses "1 {objects}" to its singular ("1 coins" ->
    "1 coin") — an option that looks safe in plural form can still leak
    a forbidden singular term once rendered.
    """
    candidates = [text]
    if text.endswith("s"):
        candidates.append(text[:-1])
    for candidate in candidates:
        candidate_lower = candidate.lower()
        for term in not_yet_known:
            pattern = r"(?<![A-Za-z])" + re.escape(term.lower()) + r"(?![A-Za-z])"
            if re.search(pattern, candidate_lower):
                return True
    return False


# ---------------------------------------------------------------------------
# Neutral fallback slots used when no interest matches.
# ---------------------------------------------------------------------------
NEUTRAL_SLOTS: Dict[str, str] = {
    "actor":   "Maria",
    "objects": "stickers",
    "place":   "classroom",
    "item1":   "pencil",
    "item2":   "eraser",
}


# ---------------------------------------------------------------------------
# get_grade_appropriate_interests
# ---------------------------------------------------------------------------

def get_grade_appropriate_interests(grade: int) -> List[str]:
    """
    Return all interest IDs whose grade_band covers the given grade.

    An interest is appropriate when:
        grade_band[0] <= grade <= grade_band[1]

    Args:
        grade: Student grade level (1–10).

    Returns:
        List of interest ID strings (keys in the bank), possibly empty.

    Example:
        >>> ids = get_grade_appropriate_interests(3)
        >>> "basketball" in ids    # grade_band [1,10]
        True
        >>> "competitive_gaming" in ids   # grade_band [5,10]
        False
    """
    result: List[str] = []
    for interest_id, data in _INTERESTS.items():
        band = data.get("grade_band", [1, 10])
        if len(band) >= 2 and band[0] <= grade <= band[1]:
            result.append(interest_id)
    return result


# ---------------------------------------------------------------------------
# get_interest_slots
# ---------------------------------------------------------------------------

def get_interest_slots(
    interest_id: str,
    grade: int,
    rng: random.Random,
    not_yet_known: Optional[Set[str]] = None,
) -> Dict[str, str]:
    """
    Build a single-problem slot dict for the given interest theme.

    Randomly selects one value from each slot list (actors, objects,
    places, item1, item2) using the provided RNG, giving each problem
    a fresh surface-level variation while staying on-theme.

    Falls back to NEUTRAL_SLOTS when interest_id is not in the bank.

    Note: Grade bands are ignored - all interests are available for all grades.

    Args:
        interest_id: Key from interest_bank.json, e.g. "basketball".
        grade: Student grade level (unused, kept for API compatibility).
        rng: Seeded Random instance for reproducibility.
        not_yet_known: Vocabulary terms the node hasn't introduced yet. Any
            slot option containing one of these terms (e.g. "coins" when
            "coin" is a later money_peso term) is excluded from selection.

    Returns:
        Dict with keys: "actor", "objects", "place", "item1", "item2".

    Example:
        >>> slots = get_interest_slots("basketball", grade=3,
        ...                            rng=random.Random(0))
        >>> slots["place"] in ["barangay court", "school gym", ...]
        True
    """
    data = _INTERESTS.get(interest_id)
    if data is None:
        return dict(NEUTRAL_SLOTS)

    def _pick(key: str) -> str:
        options = data.get(key, [])
        if not_yet_known:
            options = [o for o in options if not _contains_forbidden_term(o, not_yet_known)]
        if not options:
            return NEUTRAL_SLOTS.get(key, "")
        return rng.choice(options)

    return {
        "actor":   _pick("actors"),
        "objects": _pick("objects"),
        "place":   _pick("places"),
        "item1":   _pick("item1"),
        "item2":   _pick("item2"),
    }


# ---------------------------------------------------------------------------
# pick_interest
# ---------------------------------------------------------------------------

def pick_interest(
    student_interest_id: Optional[str],
    grade: int,
    rng: random.Random,
) -> str:
    """
    Choose the best available interest ID for a student.

    Selection logic (in priority order):
      1. If student_interest_id is provided AND exists in the bank, return it.
      2. Otherwise, pick a random interest from the bank.
      3. If no interests exist, return "neutral".

    Note: Grade bands are ignored - all interests are available for all grades.

    Args:
        student_interest_id: The student's stored preference, or None.
        grade: Student grade level (unused, kept for API compatibility).
        rng: Seeded Random instance.

    Returns:
        An interest ID string, or "neutral" when nothing else applies.
    """
    all_interests = list(_INTERESTS.keys())

    # If student has a preference and it exists in the bank, use it
    if student_interest_id and student_interest_id in _INTERESTS:
        return student_interest_id

    # Otherwise pick random from all available
    if all_interests:
        return rng.choice(all_interests)

    return "neutral"
