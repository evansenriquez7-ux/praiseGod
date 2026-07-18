"""
Practice Generation — Difficulty Engine
========================================

Central difficulty module for the new pipeline.

Responsibilities:
  1. Convert a difficulty_profile dict to a scalar 0.0–1.0
     (normalize_difficulty)
  2. Compute per-dimension (floor, ceiling, bridge_target) ranges
     from a competency text + grade (get_dimension_ranges)
  3. Rejection-sample a param dict that satisfies a profile
     (sample_for_difficulty)
  4. Enumerate all axis-level combinations for a DNA
     (enumerate_profiles)
  5. Measure acceptance rate for a profile (measure_acceptance_rate)

Refactored from:
  - matatag_dimensions.py  (get_dimension_values, interpolate_dimension)
  - difficulty_dimensions.py (log_interpolate)
  - dimension_ranges.py (DimensionRange, compute_dimension_ranges)
  - curriculum_context.py (get_neighboring_nodes, TRADITIONAL_DEFAULTS,
                           extract_numerical_limits)

No imports from those legacy modules — everything needed is re-implemented
inline or imported from practice_gen.dna.base.
"""

from __future__ import annotations

import itertools
import random
import re
from typing import Any, Dict, List, Optional, Tuple

from ..dna.base import DNA, DIFFICULTY_LEVEL_MAP, interpolate, log_interpolate  # noqa: F401


# ---------------------------------------------------------------------------
# Minimum acceptance-rate threshold used by the validation suite.
# ---------------------------------------------------------------------------
MIN_ACCEPTANCE_RATE: float = 0.05


# ---------------------------------------------------------------------------
# Grade-based traditional defaults
# Mirrors TRADITIONAL_DEFAULTS / GRADE_DEFAULTS from the legacy modules.
# ---------------------------------------------------------------------------
_GRADE_DEFAULTS: Dict[int, Dict[str, Any]] = {
    1:  {"min": 1,   "max": 100},
    2:  {"min": 1,   "max": 1_000},
    3:  {"min": 1,   "max": 10_000},
    4:  {"min": 1,   "max": 1_000_000},
    5:  {"min": 1,   "max": 1_000_000},
    6:  {"min": 1,   "max": 1_000_000},
    7:  {"min": 1,   "max": 1_000_000},
    8:  {"min": 1,   "max": 1_000_000},
    9:  {"min": 1,   "max": 1_000_000},
    10: {"min": 1,   "max": 1_000_000},
}


# ---------------------------------------------------------------------------
# extract_numerical_limits (inline — no legacy import)
# ---------------------------------------------------------------------------

def extract_numerical_limits(text: str) -> List[int]:
    """
    Extract numerical limits from a competency text string.

    Recognises patterns like:
      "up to ₱100"         → [100]
      "numbers up to 10 000" → [10000]
      "between ₱50 and ₱200" → [50, 200]
      "less than 1000"      → [1000]

    Only values ≥ 10 are returned (filters out small ordinals / step counts).

    Args:
        text: Competency description string.

    Returns:
        Sorted, deduplicated list of integer limits found in the text.
    """
    patterns = [
        r'₱\s*([\d,\s]+)',
        r'up\s+to\s+([\d,\s]+)',
        r'less\s+than\s+([\d,\s]+)',
        r'between\s+([\d,\s]+)\s+and\s+([\d,\s]+)',
    ]

    limits: List[int] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            for group in match.groups():
                cleaned = group.replace(',', '').replace(' ', '')
                try:
                    val = int(cleaned)
                    if val >= 10:
                        limits.append(val)
                except ValueError:
                    continue

    return sorted(set(limits))


# ---------------------------------------------------------------------------
# normalize_difficulty
# ---------------------------------------------------------------------------

def normalize_difficulty(
    difficulty_profile: Dict[str, Any],
    dna: DNA,
) -> float:
    """
    Convert a difficulty_profile dict to a scalar in [0.0, 1.0].

    Each axis present in the profile contributes an independent scalar
    via dna.axis_scalar().  The result is the unweighted average.

    If the profile is empty or contains no recognised axes, returns 0.5.

    Args:
        difficulty_profile: Mapping of axis_name → level string,
            e.g. {"regrouping": "ones", "number_type": "non_round"}.
        dna: The DNA object whose difficulty_axes define valid levels.

    Returns:
        Float in [0.0, 1.0].

    Examples:
        >>> normalize_difficulty({"regrouping": "none"}, addition_dna)
        0.0
        >>> normalize_difficulty({"regrouping": "double"}, addition_dna)
        1.0
    """
    if not difficulty_profile:
        return 0.5

    scalars = [
        dna.axis_scalar(axis, level)
        for axis, level in difficulty_profile.items()
        if axis in dna.difficulty_axes
    ]

    if not scalars:
        return 0.5

    return sum(scalars) / len(scalars)


# ---------------------------------------------------------------------------
# get_dimension_ranges
# ---------------------------------------------------------------------------

def get_dimension_ranges(
    competency_text: str,
    grade: int,
) -> Dict[str, Tuple[float, float, float]]:
    """
    Compute numeric (floor, ceiling, bridge_target) ranges for a competency.

    The ceiling is the largest explicit numerical limit found in the
    competency text, or the grade-appropriate default maximum.

    The floor is the grade-appropriate default minimum.

    The bridge_target is ceiling × 1.5 (preview of the next level).

    Args:
        competency_text: Raw competency description, e.g.
            "Add numbers up to 1 000 with regrouping."
        grade: Student grade level (1–10).

    Returns:
        Dict of dimension names to (floor, ceiling, bridge_target) tuples.
        Currently returns a single "numeric_limit" key plus derived
        per-digit and per-amount keys used by samplers.

    Example:
        >>> get_dimension_ranges("numbers up to 100", grade=2)
        {
            "numeric_limit": (1.0, 100.0, 150.0),
            "operand_max":   (1.0, 100.0, 150.0),
        }
    """
    grade_default = _GRADE_DEFAULTS.get(grade, _GRADE_DEFAULTS[5])
    floor: float = float(grade_default["min"])
    fallback_ceiling: float = float(grade_default["max"])

    limits = extract_numerical_limits(competency_text)
    if limits:
        ceiling = float(max(limits))
    else:
        ceiling = fallback_ceiling

    # Ensure floor < ceiling
    if floor >= ceiling:
        floor = max(1.0, ceiling * 0.1)

    bridge = ceiling * 1.5

    return {
        "numeric_limit": (floor, ceiling, bridge),
        "operand_max":   (floor, ceiling, bridge),
    }


# ---------------------------------------------------------------------------
# _CONSTRAINT_PREDICATES
# Axis-level constraint predicates for the rejection sampler.
# Each predicate receives the sampled params dict and returns bool.
# ---------------------------------------------------------------------------

def _make_predicates(
    difficulty_profile: Dict[str, Any],
) -> List:
    """
    Build a list of constraint predicate callables for a difficulty_profile.

    Args:
        difficulty_profile: e.g. {"regrouping": "ones", "structure": "result_unknown"}

    Returns:
        List of callables (params: Dict) → bool.
    """
    predicates = []

    for axis, level in difficulty_profile.items():

        # ── addition regrouping (carry) ───────────────────────────────────
        # param_bounds only samples raw "a"/"b" — decompose digits here rather
        # than expecting precomputed "ones_a"/"tens_a" keys the sampler never produces.
        if axis == "regrouping":
            def _ones_sum(p: Dict[str, Any]) -> int:
                return (p.get("a", 0) % 10) + (p.get("b", 0) % 10)

            def _tens_sum(p: Dict[str, Any]) -> int:
                return ((p.get("a", 0) // 10) % 10) + ((p.get("b", 0) // 10) % 10)

            if level == "none":
                predicates.append(lambda p: _ones_sum(p) < 10 and _tens_sum(p) < 10)
            elif level == "ones":
                predicates.append(lambda p: _ones_sum(p) >= 10 and _tens_sum(p) < 10)
            elif level == "tens":
                predicates.append(lambda p: _ones_sum(p) < 10 and _tens_sum(p) >= 10)
            elif level == "double":
                predicates.append(lambda p: _ones_sum(p) >= 10 and _tens_sum(p) >= 10)

        # ── number_type ───────────────────────────────────────────────────
        elif axis == "number_type":
            if level == "round":
                predicates.append(
                    lambda p: (
                        p.get("a", 1) % 10 == 0
                        and p.get("b", 1) % 10 == 0
                    )
                )
            elif level == "non_round":
                predicates.append(
                    lambda p: not (
                        p.get("a", 1) % 10 == 0
                        and p.get("b", 1) % 10 == 0
                    )
                )

        # ── structure (unknown position) ──────────────────────────────────
        elif axis == "structure":
            if level == "result_unknown":
                predicates.append(
                    lambda p: p.get("blank_target") == "result"
                )
            elif level == "change_unknown":
                predicates.append(
                    lambda p: p.get("blank_target") == "b"
                )
            elif level == "start_unknown":
                predicates.append(
                    lambda p: p.get("blank_target") == "a"
                )

    return predicates


def _sample_params(
    bounds: Dict[str, Tuple],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Draw one uniform sample from param_bounds.

    Args:
        bounds: Mapping of param_name → (min, max) for sample-able ranges.
                Supports int and float bounds. Entries that are not a
                2-tuple of numbers (scalar constants, lists of allowed
                values, etc.) are not sampled — they pass through as-is,
                since DNA param_bounds dicts mix true ranges with fixed
                generation constants (e.g. "max_result": 100).
        rng: Seeded Random instance.

    Returns:
        Dict of param_name → sampled (or passed-through) value.
    """
    params: Dict[str, Any] = {}
    for name, bound in bounds.items():
        if not (isinstance(bound, tuple) and len(bound) == 2 and all(isinstance(v, (int, float)) for v in bound)):
            params[name] = bound
            continue
        lo, hi = bound
        if isinstance(lo, int) and isinstance(hi, int):
            params[name] = rng.randint(lo, hi)
        else:
            params[name] = rng.uniform(float(lo), float(hi))
    return params


# ---------------------------------------------------------------------------
# sample_for_difficulty
# ---------------------------------------------------------------------------

def sample_for_difficulty(
    dna: DNA,
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    rng: random.Random,
    max_tries: int = 200,
) -> Dict[str, Any]:
    """
    Rejection-sample a param dict that satisfies the difficulty_profile.

    Draws params uniformly from dna.param_bounds_for_grade(grade) until
    all predicates derived from difficulty_profile are satisfied, or
    max_tries is exhausted (in which case the last draw is returned as-is).

    If difficulty_profile is None, a single uniform draw is returned
    without any constraint checking.

    Does NOT modify the DNA object.

    Args:
        dna: DNA specification for the concept being generated.
        grade: Student grade level (1–10).
        difficulty_profile: Axis → level mapping, e.g.
            {"regrouping": "ones", "number_type": "non_round"}.
            Pass None for unconstrained sampling.
        rng: Seeded Random instance for reproducibility.
        max_tries: Maximum rejection-sampling attempts before giving up.

    Returns:
        Sampled params dict, e.g. {"a": 34, "b": 21, "result": 55}.

    Notes:
        - The returned params contain only keys present in param_bounds.
        - Callers are responsible for any post-processing (e.g. computing
          derived fields like ones_a from a).
    """
    bounds = dna.param_bounds_for_grade(grade)

    if not difficulty_profile:
        return _sample_params(bounds, rng)

    predicates = _make_predicates(difficulty_profile)

    last_sample: Dict[str, Any] = {}
    for _ in range(max_tries):
        candidate = _sample_params(bounds, rng)
        if all(pred(candidate) for pred in predicates):
            return candidate
        last_sample = candidate

    # Exhausted tries — return last draw rather than raising.
    return last_sample


# ---------------------------------------------------------------------------
# enumerate_profiles
# ---------------------------------------------------------------------------

def enumerate_profiles(dna: DNA) -> List[Dict[str, Any]]:
    """
    Return every combination of difficulty axis levels for a DNA.

    Iterates over all axes in dna.difficulty_axes and produces the
    Cartesian product of their level lists.

    Args:
        dna: DNA specification.

    Returns:
        List of profile dicts, one per combination.
        E.g. for addition with regrouping × number_type × structure
        (4 × 2 × 3 = 24 levels), returns 24 dicts.

    Example:
        >>> profiles = enumerate_profiles(addition_dna)
        >>> len(profiles)
        24
        >>> profiles[0]
        {"regrouping": "none", "number_type": "round", "structure": "result_unknown"}
    """
    if not dna.difficulty_axes or not isinstance(dna.difficulty_axes, dict):
        # Non-dict schemas (e.g. pictographs/bar_graphs' list-of-descriptor
        # axes) are entirely continuous and have no discrete levels to enumerate.
        return [{}]

    # Only genuinely discrete axes (a list of level strings) participate in
    # profile enumeration. Continuous axes are marked with the sentinel string
    # "continuous" and are sampled via log_interpolate elsewhere, not through
    # discrete rejection-sampling profiles — itertools.product over a raw
    # string would silently iterate its characters instead.
    discrete_axes = {
        name: levels for name, levels in dna.difficulty_axes.items()
        if isinstance(levels, list)
    }
    if not discrete_axes:
        return [{}]

    axes = list(discrete_axes.keys())
    level_lists = [discrete_axes[ax] for ax in axes]

    return [
        dict(zip(axes, combo))
        for combo in itertools.product(*level_lists)
    ]


# ---------------------------------------------------------------------------
# measure_acceptance_rate
# ---------------------------------------------------------------------------

def measure_acceptance_rate(
    dna: DNA,
    grade: int,
    profile: Dict[str, str],
    rng: random.Random,
    trials: int = 500,
) -> float:
    """
    Estimate the fraction of uniform draws that satisfy a profile's constraints.

    Used by the validation suite to confirm that MIN_ACCEPTANCE_RATE is met
    for every profile so the rejection sampler is viable.

    Args:
        dna: DNA specification.
        grade: Student grade level (1–10).
        profile: Axis → level mapping to evaluate.
        rng: Seeded Random instance.
        trials: Number of uniform draws to test.

    Returns:
        Float in [0.0, 1.0] — acceptance fraction.

    Example:
        >>> rate = measure_acceptance_rate(addition_dna, grade=2,
        ...     profile={"regrouping": "ones"}, rng=random.Random(42))
        >>> rate >= MIN_ACCEPTANCE_RATE
        True
    """
    if not profile:
        return 1.0

    bounds = dna.param_bounds_for_grade(grade)
    predicates = _make_predicates(profile)

    if not predicates:
        return 1.0

    accepted = sum(
        1
        for _ in range(trials)
        if all(pred(_sample_params(bounds, rng)) for pred in predicates)
    )

    return accepted / trials
