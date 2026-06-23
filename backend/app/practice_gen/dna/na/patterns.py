"""
DNA: Patterns (Number & Algebra)

Covers MATATAG grades 1–3 pattern competencies:
  G1 — repeating patterns (cycles of 2–3 elements, numbers up to 20)
  G2 — increasing/decreasing arithmetic patterns (step 1–10, up to 100)
  G3 — combined repeating+increasing/decreasing patterns (up to 1000)
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"max_value": 20,   "cycle_length": (2, 3), "step": (1, 3)},
    "g2": {"max_value": 100,  "cycle_length": (2, 4), "step": (1, 10)},
    "g3": {"max_value": 1000, "cycle_length": (2, 5), "step": (1, 50)},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="answer - common_difference",
        required_concept="patterns",
        label="cnt_wrong_interval",
        description="Used wrong step size when extending the pattern.",
    ),
    ErrorPattern(
        formula="answer + common_difference",
        required_concept="patterns",
        label="cnt_skip",
        description="Skipped a term, giving the value two steps ahead.",
    ),
    ErrorPattern(
        formula="first + (position - 1) * common_difference",
        required_concept="patterns",
        label="ar_wrong_op",
        description="Subtracted instead of added when the pattern is increasing.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_PATTERN    = VocabGated(requires_vocab="pattern",    preferred="pattern",    fallback="repeating group")
VOCAB_RULE       = VocabGated(requires_vocab="rule",       preferred="rule",       fallback="what it does")
VOCAB_TERM       = VocabGated(requires_vocab="term",       preferred="term",       fallback="number in the pattern")
VOCAB_INCREASING = VocabGated(requires_vocab="increasing", preferred="increasing", fallback="going up")
VOCAB_DECREASING = VocabGated(requires_vocab="decreasing", preferred="decreasing", fallback="going down")
VOCAB_REPEATING  = VocabGated(requires_vocab="repeating",  preferred="repeating",  fallback="same group again")


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_repeating_sequence(start: int, cycle: List[int], length: int) -> List[int]:
    """Build a sequence by repeating the cycle starting at start offset."""
    return [cycle[i % len(cycle)] for i in range(length)]


def _make_arithmetic_sequence(first: int, step: int, length: int, increasing: bool) -> List[int]:
    direction = 1 if increasing else -1
    return [first + direction * step * i for i in range(length)]


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate a pattern sequence based on grade and difficulty profile.

    Returns:
        {
            "sequence":        list of ints shown to student (with one slot masked),
            "missing_index":   index of the missing/next term,
            "answer":          correct int value,
            "rule_description": human-readable rule string,
            "common_difference": step size (0 for pure repeating),
            "first":           first term,
            "position":        1-based position of answer,
        }
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]
    diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
    from backend.app.practice_gen.dna.base import log_interpolate, linear_interpolate
    
    max_val_bound = int(log_interpolate(10, bounds["max_value"], diff_scalar))
    max_val = int(profile.get("max_value", max_val_bound))
    
    step_lo_bound, step_hi_bound = bounds["step"]
    step_hi_bound = int(linear_interpolate(step_lo_bound, step_hi_bound, diff_scalar))
    step_lo = int(profile.get("step_lo", step_lo_bound))
    step_hi = int(profile.get("step_hi", step_hi_bound))

    cyc_lo_bound, cyc_hi_bound  = bounds["cycle_length"]
    cyc_hi_bound = int(linear_interpolate(cyc_lo_bound, cyc_hi_bound, diff_scalar))
    cyc_lo = int(profile.get("cycle_lo", cyc_lo_bound))
    cyc_hi = int(profile.get("cycle_hi", cyc_hi_bound))

    num_diff_scalar = diff_scalar

    pattern_type = profile.get("pattern_type", "arithmetic_increasing")
    ask_type     = profile.get("ask_type", "next_term")

    seq_length = 6  # always show 6-term window

    from backend.app.practice_gen.generators.number_difficulty import generate_number_by_window, generate_pair_by_window

    if pattern_type == "repeating":
        cycle_len = rng.randint(cyc_lo, cyc_hi)
        candidates = list(range(1, max_val + 1))
        cycle = [generate_number_by_window(candidates, num_diff_scalar, d=5, rng=rng) for _ in range(cycle_len)]
        sequence = _make_repeating_sequence(0, cycle, seq_length + 1)
        step = 0
        rule = f"Repeat the group: {cycle}"
    elif pattern_type == "arithmetic_decreasing":
        pairs = []
        for s in range(step_lo, step_hi + 1):
            for f in range(s * seq_length + 1, max_val + 1):
                pairs.append((f, s))
        if not pairs:
            pairs = [(max_val, step_lo)]
        first, step = generate_pair_by_window(pairs, num_diff_scalar, d=5, rng=rng)
        sequence = _make_arithmetic_sequence(first, step, seq_length + 1, increasing=False)
        rule = f"Subtract {step} each time"
    elif pattern_type == "combined":
        pairs = []
        c_step_hi = min(step_hi, 10)
        for s in range(step_lo, c_step_hi + 1):
            for f in range(1, max(2, max_val // 2) + 1):
                pairs.append((f, s))
        if not pairs:
            pairs = [(1, step_lo)]
        first, step = generate_pair_by_window(pairs, num_diff_scalar, d=5, rng=rng)
        base = _make_arithmetic_sequence(first, step, seq_length + 1, increasing=True)
        offsets = [0, rng.randint(1, 3)] * (seq_length + 1)
        sequence = [base[i] + offsets[i] for i in range(seq_length + 1)]
        rule = f"Add {step}, with alternating offset"
    else:  # arithmetic_increasing (default)
        pairs = []
        for s in range(step_lo, step_hi + 1):
            for f in range(1, max(2, max_val - s * seq_length) + 1):
                pairs.append((f, s))
        if not pairs:
            pairs = [(1, step_lo)]
        first, step = generate_pair_by_window(pairs, num_diff_scalar, d=5, rng=rng)
        sequence = _make_arithmetic_sequence(first, step, seq_length + 1, increasing=True)
        rule = f"Add {step} each time"

    if ask_type == "next_term":
        missing_index = seq_length  # last position
        visible = sequence[:seq_length]
        answer = sequence[seq_length]
    elif ask_type == "missing_middle":
        missing_index = rng.randint(1, seq_length - 2)
        visible = sequence[:seq_length]
        answer = visible[missing_index]
        visible = visible[:]  # copy; caller masks missing_index
    else:  # state_rule
        missing_index = -1
        visible = sequence[:seq_length]
        answer = step if pattern_type != "repeating" else 0

    first_val = sequence[0]
    position = missing_index + 1 if missing_index >= 0 else seq_length + 1

    return {
        "sequence":          visible,
        "missing_index":     missing_index,
        "answer":            answer,
        "rule_description":  rule,
        "common_difference": step if pattern_type != "repeating" else 0,
        "first":             first_val,
        "position":          position,
        "pattern_kind":      pattern_type,
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hints for the given pattern problem."""
    seq   = values["sequence"]
    diff  = values["common_difference"]
    rule  = values["rule_description"]
    ans   = values["answer"]
    m_idx = values["missing_index"]

    term_label = VOCAB_TERM.resolve(cumulative_vocab)
    rule_label = VOCAB_RULE.resolve(cumulative_vocab)

    hints: List[str] = []
    hints.append(f"Look at the pattern: {seq}.")

    if diff != 0:
        direction = VOCAB_INCREASING.resolve(cumulative_vocab) if diff > 0 else VOCAB_DECREASING.resolve(cumulative_vocab)
        hints.append(f"The pattern is {direction} by {abs(diff)} each step.")
    else:
        rep = VOCAB_REPEATING.resolve(cumulative_vocab)
        hints.append(f"This is a {rep} {VOCAB_PATTERN.resolve(cumulative_vocab)}. Find the repeating group.")

    if m_idx >= 0:
        hints.append(f"The missing {term_label} is at position {m_idx + 1}.")
    hints.append(f"The {rule_label} is: {rule}. The answer is {ans}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

PATTERNS_DNA = DNA(
    concept="patterns",
    dna_type="formula",
    answer_formula="first + (position * common_difference)",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "pattern_sequence",
        "fill_in_table",
    ],
    requires_context=False,
    visual_home="PatternSequence",
    difficulty_axes=_DIFFICULTY_AXES,
)
