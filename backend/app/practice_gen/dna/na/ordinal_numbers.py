"""
DNA: Ordinal Numbers (Number & Algebra)

Static-bank DNA. Item pool is authored inline as templates.

Covers MATATAG grades 1–3 ordinal competencies:
  G1 — 1st through 10th
  G2 — up to 20th
  G3 — up to 100th
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
# For static_bank the bounds document the ordinal range, not numeric operands.
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"min_ordinal": 1,  "max_ordinal": 10},
    "g2": {"min_ordinal": 1,  "max_ordinal": 20},
    "g3": {"min_ordinal": 1,  "max_ordinal": 100},
}


# ─── ordinal utilities ────────────────────────────────────────────────────────

def _ordinal_suffix(n: int) -> str:
    """Return '1st', '2nd', '3rd', '4th', … for any positive integer."""
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]}"


_ORDINAL_WORDS = {
    1: "first",  2: "second",  3: "third",   4: "fourth",  5: "fifth",
    6: "sixth",  7: "seventh", 8: "eighth",  9: "ninth",  10: "tenth",
    11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth",
    15: "fifteenth", 16: "sixteenth", 17: "seventeenth", 18: "eighteenth",
    19: "nineteenth", 20: "twentieth",
}

_TENS_ORDINAL = {
    2: "twentieth", 3: "thirtieth", 4: "fortieth", 5: "fiftieth",
    6: "sixtieth",  7: "seventieth", 8: "eightieth", 9: "ninetieth",
}


def _ordinal_word(n: int) -> str:
    """Return 'first', 'second', … 'one hundredth' for 1–100."""
    if n in _ORDINAL_WORDS:
        return _ORDINAL_WORDS[n]
    if n == 100:
        return "one hundredth"
    tens, ones = n // 10, n % 10
    if ones == 0:
        return _TENS_ORDINAL.get(tens, f"{n}th")
    # e.g. twenty-first
    _tens_prefix = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty",
                    6: "sixty", 7: "seventy", 8: "eighty", 9: "ninety"}
    prefix = _tens_prefix.get(tens, "")
    return f"{prefix}-{_ORDINAL_WORDS.get(ones, _ordinal_suffix(ones))}"


# ─── item template pool ───────────────────────────────────────────────────────
# Each template has:
#   "range_key": which grade/range this template suits
#   "template":  f-string with {ordinal}, {word}, {symbol} slots
#   "task_type": which difficulty axis task_type it addresses

_ITEM_TEMPLATES = [
    # identify_ordinal — symbol given, choose word
    {
        "range_key": "1st_to_10th",
        "template":  "Which word describes the {symbol} position?",
        "task_type": "identify_ordinal",
        "answer_key": "word",
        "choices_type": "words",
    },
    # identify_ordinal — word given, choose symbol
    {
        "range_key": "1st_to_10th",
        "template":  "Write the symbol for the {word} position.",
        "task_type": "identify_ordinal",
        "answer_key": "symbol",
        "choices_type": "symbols",
    },
    # find_position — ordinal given, pick position number
    {
        "range_key": "11th_to_20th",
        "template":  "A runner finished in {word} place. What position number is that?",
        "task_type": "find_position",
        "answer_key": "n",
        "choices_type": "numbers",
    },
    # find_position — position number given, pick ordinal symbol
    {
        "range_key": "11th_to_20th",
        "template":  "What ordinal describes position number {n}?",
        "task_type": "find_position",
        "answer_key": "symbol",
        "choices_type": "symbols",
    },
    # compare_positions — two ordinals, which comes first
    {
        "range_key": "21st_to_100th",
        "template":  "Who arrived earlier: the student in {symbol} place or {symbol2} place?",
        "task_type": "compare_positions",
        "answer_key": "earlier_symbol",
        "choices_type": "symbols",
    },
    # compare_positions — between two ordinals, which is later
    {
        "range_key": "21st_to_100th",
        "template":  "Which position comes after {symbol}?",
        "task_type": "compare_positions",
        "answer_key": "next_symbol",
        "choices_type": "symbols",
    },
]


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="n",
        required_concept="ordinal_numbers",
        label="cnt_card_ord",
        description="Gave the cardinal count instead of the ordinal position.",
    ),
    ErrorPattern(
        formula="n + 1",
        required_concept="ordinal_numbers",
        label="cnt_ord_off",
        description="Off by one — gave the next ordinal position instead.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {    "range":     ["1st_to_10th", "11th_to_20th", "21st_to_100th"],
    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_FIRST   = VocabGated(requires_vocab="1st",      preferred="1st",      fallback="number one")
VOCAB_ORDINAL = VocabGated(requires_vocab="ordinal",  preferred="ordinal",  fallback="position word")
VOCAB_POSITION= VocabGated(requires_vocab="position", preferred="position", fallback="place in line")


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """
    Static-bank generator: pick a template and fill in a random ordinal value.

    Returns:
        {
            "n":             int (ordinal position),
            "symbol":        str ("1st", "2nd", …),
            "word":          str ("first", "second", …),
            "question_text": str (rendered template),
            "answer":        Any (depends on template answer_key),
            "task_type":     str,
        }
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]
    min_ord = bounds["min_ordinal"]
    diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
    from backend.app.practice_gen.dna.base import log_interpolate
    max_ord = int(log_interpolate(10, bounds["max_ordinal"], diff_scalar))

    range_level = profile.get("range", "1st_to_10th")
    task_type   = profile.get("task_type", "identify_ordinal")

    # Filter templates matching task_type and grade range
    candidates = [t for t in _ITEM_TEMPLATES if t["task_type"] == task_type]
    if not candidates:
        candidates = _ITEM_TEMPLATES

    template_def = rng.choice(candidates)

    min_ord = int(profile.get("min_ordinal", min_ord))
    max_ord = int(profile.get("max_ordinal", max_ord))
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))
    
    number_candidates = list(range(min_ord, max_ord + 1))
    from backend.app.practice_gen.generators.number_difficulty import generate_number_by_window
    n = generate_number_by_window(number_candidates, num_diff_scalar, d=5, rng=rng, num_type="ordinal")
    symbol  = _ordinal_suffix(n)
    word    = _ordinal_word(n)

    # Resolve answer based on answer_key
    answer_key = template_def["answer_key"]
    if answer_key == "n":
        answer = n
    elif answer_key == "word":
        answer = word
    elif answer_key == "symbol":
        answer = symbol
    elif answer_key == "earlier_symbol":
        n2      = rng.randint(min_ord, max_ord)
        symbol2 = _ordinal_suffix(n2)
        answer  = symbol if n < n2 else symbol2
    elif answer_key == "next_symbol":
        answer = _ordinal_suffix(n + 1)
        n2, symbol2 = None, None
    else:
        answer = symbol

    # Render question text
    tpl = template_def["template"]
    ctx: Dict[str, Any] = {"n": n, "symbol": symbol, "word": word}
    if "symbol2" in tpl:
        n2 = n2 if "n2" in dir() else rng.randint(min_ord, max_ord)
        symbol2 = _ordinal_suffix(n2)
        ctx["symbol2"] = symbol2
    try:
        question_text = tpl.format(**ctx)
    except KeyError:
        question_text = tpl

    return {
        "blank_target": "answer",
        "n":             n,
        "symbol":        symbol,
        "word":          word,
        "question_text": question_text,
        "answer":        answer,
        "task_type":     task_type,
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hints for an ordinal number problem."""
    n         = values["n"]
    symbol    = values["symbol"]
    word      = values["word"]
    task_type = values["task_type"]

    ord_label = VOCAB_ORDINAL.resolve(cumulative_vocab)
    pos_label = VOCAB_POSITION.resolve(cumulative_vocab)

    hints: List[str] = []

    if task_type == "identify_ordinal":
        hints.append(f"Ordinal numbers describe {pos_label} in order.")
        hints.append(f"The number {n} in a line is called the {symbol} ({word}).")
        hints.append(f"Remember: 1st = first, 2nd = second, 3rd = third, then add -th.")

    elif task_type == "find_position":
        hints.append(f"'{word.capitalize()}' is an {ord_label} word.")
        hints.append(f"Count positions starting from 1: 1st, 2nd, 3rd, … until you reach {word}.")
        hints.append(f"{word.capitalize()} = position {n}, written as {symbol}.")

    else:  # compare_positions
        hints.append(f"Smaller ordinal numbers come earlier (closer to the start).")
        hints.append(f"Compare the numbers: the smaller ordinal position is earlier.")
        hints.append(f"{symbol} means position {n}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

ORDINAL_NUMBERS_DNA = DNA(
    concept="ordinal_numbers",
    dna_type="static_bank",
    answer_formula=None,
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
    ],
    requires_context=True,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
