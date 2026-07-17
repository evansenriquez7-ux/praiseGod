"""
DNA: Comparing and Ordering Numbers (Number & Algebra)

Covers MATATAG grades 1–3 comparison competencies:
  G1 — compare two numbers up to 20; order sets up to 100
  G2 — compare/order up to 1000
  G3 — compare/order up to 10000; explicit >, <, = symbol use
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
    "g1": {"max_value": 100,   "set_size": (2, 4)},
    "g2": {"max_value": 1000,  "set_size": (2, 5)},
    "g3": {"max_value": 10000, "set_size": (3, 6)},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="numbers[1]",
        required_concept="comparing_ordering",
        label="cnt_ord_off",
        description="Off by one position when ordering — picked the adjacent value.",
    ),
    ErrorPattern(
        formula="numbers[0] % 10",
        required_concept="comparing_ordering",
        label="pv_dig_val",
        description="Compared the ones digit only instead of full place value.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {"number_difficulty": "continuous"}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_GT    = VocabGated(requires_vocab="greater than", preferred="greater than", fallback="bigger than")
VOCAB_LT    = VocabGated(requires_vocab="less than",    preferred="less than",    fallback="smaller than")
VOCAB_EQ    = VocabGated(requires_vocab="equal to",     preferred="equal to",     fallback="the same as")
VOCAB_GT_SY = VocabGated(requires_vocab=">",            preferred=">",            fallback="is more")
VOCAB_LT_SY = VocabGated(requires_vocab="<",            preferred="<",            fallback="is less")
VOCAB_EQ_SY = VocabGated(requires_vocab="=",            preferred="=",            fallback="equals")


# ─── helpers ──────────────────────────────────────────────────────────────────

def _compare_symbol(a: int, b: int) -> str:
    if a > b:
        return ">"
    if a < b:
        return "<"
    return "="


def _close_pair(rng: random.Random, max_val: int) -> tuple:
    """Return two numbers that differ by at most 5% of max_val (min gap 1)."""
    gap = max(1, max_val // 20)
    a = rng.randint(1, max_val - gap)
    b = a + rng.randint(1, gap)
    return (a, b) if rng.random() < 0.5 else (b, a)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate a comparison/ordering problem.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]

    context = profile.get("context", "pure")
    spine = profile.get("spine", None)

    max_val_prof = profile.get("max_value")
    if max_val_prof is None:
        from backend.app.practice_gen.dna.base import log_interpolate
        diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
        effective_max = int(log_interpolate(10, bounds["max_value"], diff_scalar))
    elif isinstance(max_val_prof, (int, float)):
        effective_max = int(max_val_prof)
    elif isinstance(max_val_prof, str):
        range_caps = {"up_to_20": 20, "up_to_100": 100, "up_to_1000": 1000, "up_to_10000": 10000}
        effective_max = range_caps.get(max_val_prof, 100)
    else:
        effective_max = 100

    effective_max = max(2, min(effective_max, 10000))
    raw_task_type = profile.get("task_type", "compare_pair")
    task_type = raw_task_type
    if task_type == "compare_pair":
        task_type = "compare_two"
    elif task_type == "order_sequence":
        task_type = "order_set"

    proximity = profile.get("proximity", "far_apart")
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    if task_type == "compare_two":
        candidates = []
        for _ in range(500):
            if proximity == "close_together":
                a, b = _close_pair(rng, effective_max)
            else:
                a = rng.randint(1, effective_max)
                b = rng.randint(1, effective_max)
            candidates.append((a, b))
        
        from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
        a, b = generate_pair_by_window(candidates, num_diff_scalar, d=5, rng=rng)
        numbers = [a, b]
        answer = _compare_symbol(a, b)
        distractors = [o for o in [">", "<", "="] if o != answer]
        distractors.append("cannot be determined")

    elif task_type == "order_set":
        sz_lo, sz_hi = bounds["set_size"]
        n = rng.randint(sz_lo, sz_hi)
        if proximity == "close_together":
            max_base = max(1, effective_max - n * 5)
            base = int(max_base * num_diff_scalar)
            base = max(1, min(max_base, base + rng.randint(-5, 5)))
            numbers = [base + rng.randint(0, 5) for _ in range(n)]
        else:
            numbers = []
            for _ in range(n):
                val = int(effective_max * num_diff_scalar) + rng.randint(-10, 10)
                numbers.append(max(1, min(effective_max, val)))
        
        numbers = list(sorted(set(numbers)))
        if len(numbers) < 3:
            while len(numbers) < 3:
                numbers.append(rng.randint(1, effective_max))
            numbers = list(sorted(set(numbers)))
            
        answer = ", ".join(map(str, sorted(numbers)))
        d1 = ", ".join(map(str, sorted(numbers, reverse=True)))
        
        shuffles = set()
        for _ in range(50):
            shuf = list(numbers)
            rng.shuffle(shuf)
            shuf_str = ", ".join(map(str, shuf))
            if shuf_str != answer and shuf_str != d1:
                shuffles.add(shuf_str)
            if len(shuffles) >= 2:
                break
        shuffles_list = list(shuffles)
        while len(shuffles_list) < 2:
            shuffles_list.append(f"{answer} (reversed)")
            
        distractors = [d1] + shuffles_list[:2]

    else:  # find_between
        effective_max = max(3, effective_max)
        candidates = []
        for _ in range(500):
            a = rng.randint(1, effective_max - 2)
            b = rng.randint(a + 2, effective_max)
            candidates.append((a, b))
        from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
        a, b = generate_pair_by_window(candidates, num_diff_scalar, d=5, rng=rng)
        
        between = rng.randint(a + 1, b - 1)
        numbers = [a, b]
        answer = between
        
        d1 = a - rng.randint(1, 5)
        if d1 < 0:
            d1 = b + rng.randint(1, 5)
        d2 = b + rng.randint(1, 5)
        d3 = rng.choice([a, b])
        distractors = [d1, d2, d3]

    result_dict = {
        "blank_target": "answer",
        "numbers": numbers,
        "numbers_str": ", ".join(map(str, numbers)),
        "answer": answer,
        "task_type": raw_task_type,
        "context": context,
        "a": numbers[0] if len(numbers) > 0 else None,
        "b": numbers[1] if len(numbers) > 1 else None,
        "distractors": distractors,
    }

    return result_dict


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hints for a comparison/ordering problem."""
    numbers   = values["numbers"]
    answer    = values["answer"]
    task_type = values["task_type"]

    gt = VOCAB_GT.resolve(cumulative_vocab)
    lt = VOCAB_LT.resolve(cumulative_vocab)
    eq = VOCAB_EQ.resolve(cumulative_vocab)

    hints: List[str] = []

    if task_type in ("compare_two", "compare_pair"):
        a, b = numbers[0], numbers[1]
        hints.append(f"Compare {a} and {b}.")
        hints.append(f"Start from the largest place value and compare each digit.")
        if a > b:
            hints.append(f"{a} is {gt} {b}, so we write {a} > {b}.")
        elif a < b:
            hints.append(f"{a} is {lt} {b}, so we write {a} < {b}.")
        else:
            hints.append(f"{a} is {eq} {b}, so we write {a} = {b}.")

    elif task_type in ("order_set", "order_sequence"):
        hints.append(f"Numbers to order: {numbers}.")
        hints.append(f"Find the smallest number first, then the next smallest.")
        hints.append(f"Ordered from least to greatest: {sorted(numbers)}.")

    else:  # find_between
        a, b = numbers[0], numbers[1]
        hints.append(f"Find a number between {a} and {b}.")
        hints.append(f"Any number {gt} {a} and {lt} {b} works.")
        hints.append(f"One correct answer is {answer}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

COMPARING_ORDERING_DNA = DNA(
    concept="comparing_ordering",
    dna_type="formula",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "ordering",
        "sort_order",
        "true_false",
    ],
    requires_context=True,
    visual_home="SortOrder",
    difficulty_axes=_DIFFICULTY_AXES,
)
