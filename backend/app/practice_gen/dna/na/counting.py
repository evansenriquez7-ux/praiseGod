"""
DNA: Counting (Number & Algebra)

Refactored from:
  - matatag_skeletons.py  (counting generator + cnt_* traps)
  - matatag_dimensions.py (COUNTING_DIMENSIONS)

Covers MATATAG grades 1–3 counting competencies:
  G1 — count to 100; skip by 1, 2, 5, 10
  G2 — count to 1000; skip by 2, 5, 10, 20, 50, 100
  G3 — count to 10 000; skip by larger intervals
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


# ─── grade-gated skip pools ───────────────────────────────────────────────────
_SKIP_POOLS: Dict[str, List[int]] = {
    "g1": [1, 2, 5, 10],
    "g2": [2, 5, 10, 20, 50, 100],
    "g3": [2, 5, 10, 25, 50, 100, 250, 1000],
}

_RANGE_MAX: Dict[str, int] = {
    "g1": 100,
    "g2": 1000,
    "g3": 10000,
}


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"max_num": 100,   "skip_pool": [1, 2, 5, 10]},
    "g2": {"max_num": 1000,  "skip_pool": [2, 5, 10, 20, 50, 100]},
    "g3": {"max_num": 10000, "skip_pool": [2, 5, 10, 25, 50, 100, 250, 1000]},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="start - skip_by",
        required_concept="counting",
        label="cnt_prev",
        description="Went backward instead of forward (subtracted skip interval).",
    ),
    ErrorPattern(
        formula="start + 1",
        required_concept="counting",
        label="cnt_skip",
        description="Used +1 instead of the actual skip interval.",
    ),
    ErrorPattern(
        formula="start - skip_by * 2",
        required_concept="counting",
        label="cnt_back",
        description="Subtracted two skip intervals instead of adding one (went backward by double).",
    ),
    ErrorPattern(
        formula="start + skip_by * 2",
        required_concept="counting",
        label="cnt_wrong_interval",
        description="Applied the skip interval twice (doubled jump).",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {    "range":           "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_SKIP_COUNT  = VocabGated(requires_vocab="skip count",  preferred="skip count",   fallback="count by a number")
VOCAB_COUNTING_BY = VocabGated(requires_vocab="counting by", preferred="counting by",  fallback="jumping by")
VOCAB_SEQUENCE    = VocabGated(requires_vocab="sequence",    preferred="number pattern",     fallback="number pattern")


# ─── helpers ──────────────────────────────────────────────────────────────────

_NUMBER_WORDS = {
    0:"zero",1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",
    8:"eight",9:"nine",10:"ten",11:"eleven",12:"twelve",13:"thirteen",
    14:"fourteen",15:"fifteen",16:"sixteen",17:"seventeen",18:"eighteen",
    19:"nineteen",20:"twenty",30:"thirty",40:"forty",50:"fifty",60:"sixty",
    70:"seventy",80:"eighty",90:"ninety",100:"one hundred",
}

def _to_number_word(n: int) -> str:
    if n in _NUMBER_WORDS:
        return _NUMBER_WORDS[n]
    if 20 < n < 100:
        tens, ones = (n // 10) * 10, n % 10
        if ones == 0:
            return _NUMBER_WORDS.get(tens, str(n))
        return f"{_NUMBER_WORDS[tens]}-{_NUMBER_WORDS[ones]}"
    return str(n)


def _select_skip(grade: int, interval_level: str, pool: List[int], rng: random.Random) -> int:
    if interval_level == "by_1":
        return 1 if 1 in pool else rng.choice(pool)
    if interval_level == "by_2_5_10":
        candidates = [s for s in pool if s in (2, 5, 10)]
        return rng.choice(candidates) if candidates else rng.choice(pool)
    if interval_level == "by_20_50_100":
        candidates = [s for s in pool if s >= 20]
        return rng.choice(candidates) if candidates else rng.choice(pool)
    return rng.choice(pool)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate counting parameters satisfying difficulty_profile.
    """
    rng     = random.Random(seed)
    profile = difficulty_profile or {}

    g_key   = f"g{max(1, min(grade, 3))}"
    bounds  = _PARAM_BOUNDS[g_key]

    context = profile.get("context", "pure")
    spine = profile.get("spine", None)

    from backend.app.practice_gen.dna.base import log_interpolate

    diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))

    max_num_limit = int(log_interpolate(10, bounds["max_num"], diff_scalar))
    lo = bounds.get("min_value", 1)

    range_val = profile.get("range", 0.0)
    try:
        range_val = float(range_val)
    except (TypeError, ValueError):
        range_val = 0.0

    import math
    shift = 0
    log_min = math.log10(lo + shift)
    log_max = math.log10(max_num_limit + shift)

    if range_val > 1.0:
        if log_max > log_min:
            num_diff_scalar = (math.log10(range_val + shift) - log_min) / (log_max - log_min)
            num_diff_scalar = max(0.0, min(num_diff_scalar, 1.0))
        else:
            num_diff_scalar = 0.0
    else:
        num_diff_scalar = range_val

    log_val = log_min + num_diff_scalar * (log_max - log_min)
    max_target = int(math.pow(10, log_val)) - shift
    
    max_num = max(10, min(max_num_limit, max_target))

    current_lo = lo
    if num_diff_scalar > 0:
        prev_scalar = max(0.0, num_diff_scalar - 0.25)
        prev_log_val = log_min + prev_scalar * (log_max - log_min)
        prev_target = int(math.pow(10, prev_log_val)) - shift
        current_lo = min(max_num, max(lo, prev_target + 1))

    direction      = profile.get("direction", "forward")
    interval_level = profile.get("skip_interval", "by_1")

    skip_pool = profile.get("skip_pool", bounds["skip_pool"])
    skip_by = _select_skip(grade, interval_level, skip_pool, rng)

    candidates = []
    if direction == "forward":
        max_start = max(0, max_num - 4 * skip_by)
        min_start = max(0, current_lo - 4 * skip_by)
        for i in range((min_start // max(1, skip_by)), (max_start // max(1, skip_by)) + 1):
            val = i * skip_by
            if current_lo <= val + 4 * skip_by <= max_num:
                candidates.append(val)
        if not candidates:
            candidates.append(max_start)
    else:
        min_start = max(4 * skip_by, current_lo)
        for v in range(min_start, max_num + 1):
            if v % skip_by == 0:
                candidates.append(v)
        if not candidates:
            candidates.append(max(4 * skip_by, max_num))

    start_val = rng.choice(candidates)
    if direction == "forward":
        sequence = [start_val + i * skip_by for i in range(5)]
    else:
        sequence = [start_val - i * skip_by for i in range(5)]

    answer = sequence[4]
    visible = sequence[:4]
    last_visible = sequence[3]

    result_dict = {
        "start":          last_visible,
        "skip_by":        skip_by,
        "direction":      direction,
        "answer":         answer,
        "sequence":       visible,
        "context":        context,
    }

    return result_dict


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hint strings for the given counting problem."""
    sequence  = values["sequence"]
    skip_by   = values["skip_by"]
    direction = values["direction"]
    answer    = values["answer"]

    skip_lbl = VOCAB_SKIP_COUNT.resolve(cumulative_vocab)
    seq_lbl  = VOCAB_SEQUENCE.resolve(cumulative_vocab)
    cnt_lbl  = VOCAB_COUNTING_BY.resolve(cumulative_vocab)

    visible_str = ", ".join(str(n) for n in sequence)
    action = "add" if direction == "forward" else "subtract"

    return [
        f"Look at the {seq_lbl}: {visible_str}, ___",
        f"Find the rule by comparing neighbours: {sequence[1]} − {sequence[0]} = {abs(sequence[1] - sequence[0])}.",
        f"The pattern is {cnt_lbl} {skip_by}s ({action} {skip_by} each time).",
        f"{action.capitalize()} {skip_by} to {sequence[3]}: {sequence[3]} {'+ ' if direction == 'forward' else '- '}{skip_by} = {answer}.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

COUNTING_DNA = DNA(
    concept="counting",
    dna_type="formula",
    answer_formula="start + skip_by",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "ordering",
        "number_line_read",
        "ten_frame",
    ],
    requires_context=True,
    visual_home="NumberLine",
    difficulty_axes=_DIFFICULTY_AXES,
)
