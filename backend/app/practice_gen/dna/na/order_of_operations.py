"""
DNA: Order of Operations (Number & Algebra)

G3 only — addition and subtraction of 3–4 terms, left to right (MDAS subset).

MATATAG G3 Q2: "Perform addition and subtraction of 3 to 4 numbers of up to
2 digits, observing correct order of operations."

At G3 the rule is simply left-to-right evaluation of + and − only.
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
# Order of operations is G3-only.
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g3": {"min_operand": 1, "max_operand": 99, "min_terms": 3, "max_terms": 4},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="operands[0] + operands[-1]",
        required_concept="order_of_operations",
        label="alg_distrib",
        description="Only added the first and last operand, ignoring the middle terms.",
    ),
    ErrorPattern(
        formula="answer + operands[0]",
        required_concept="order_of_operations",
        label="ar_wrong_op",
        description="Applied the wrong operation — added the first operand to the result instead of evaluating correctly.",
    ),
    ErrorPattern(
        formula="answer - 1",
        required_concept="order_of_operations",
        label="ar_off_one",
        description="Off by one in the final result.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, List[str]] = {
    "num_operands":   ["three_terms", "four_terms"],
    "operation_mix":  ["add_only", "mixed_add_sub"],
    "number_size":    ["1_digit", "2_digit"],
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_ORDER = VocabGated(
    requires_vocab="order of operations",
    preferred="order of operations",
    fallback="the correct order of steps",
)
VOCAB_EXPR  = VocabGated(
    requires_vocab="expression",
    preferred="expression",
    fallback="number sentence",
)
VOCAB_MDAS  = VocabGated(
    requires_vocab="MDAS",
    preferred="MDAS",
    fallback="left-to-right rule",
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _evaluate_left_to_right(operands: List[int], operators: List[str]) -> int:
    """Evaluate an expression left to right given operands and operator list."""
    result = operands[0]
    for op, val in zip(operators, operands[1:]):
        if op == "+":
            result += val
        else:
            result -= val
    return result


def _build_expression_str(operands: List[int], operators: List[str]) -> str:
    parts = [str(operands[0])]
    for op, val in zip(operators, operands[1:]):
        parts.append(op)
        parts.append(str(val))
    return " ".join(parts)


# ─── parameter generator ──────────────────────────────────────────────────────

# Word-problem narration is self-built here (not via generators/spines.py):
# this DNA has requires_context=False and no registered spine, matching
# missing_number.py's "equivalent" branch precedent of setting "question"
# directly in the returned dict. base_generator.py picks up values["question"]
# ahead of both the spine path and _build_symbolic_question's generic
# fallback -- which has no branch at all for this concept, and previously
# rendered "What is the value of None + None?" for every seed once this DNA
# was actually wired to a node (it had never been reachable before).
_WP_ACTORS = ["Ana", "Ben", "Carlo", "Dina", "Elena", "Fidel"]
_WP_OBJECTS = ["mangoes", "notebooks", "stickers", "marbles", "eggs", "storybooks"]
_WP_VERBS = {"+": "receives", "-": "gives away"}


def _build_word_problem(actor: str, obj: str, operands: List[int], operators: List[str], money: bool) -> str:
    unit = f"₱{operands[0]}" if money else f"{operands[0]} {obj}"
    parts = [f"{actor} starts with {unit}."]
    for op, val in zip(operators, operands[1:]):
        verb = _WP_VERBS[op]
        amount = f"₱{val}" if money else f"{val} {obj}"
        parts.append(f"Then {actor} {verb} {amount}.")
    question = f"How much money does {actor} have now?" if money else f"How many {obj} does {actor} have now?"
    parts.append(question)
    return " ".join(parts)


def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate an order-of-operations problem (G3 only, + and − left to right).

    Returns:
        {
            "operands":        list of ints,
            "operators":       list of "+" or "-" strings,
            "expression_str":  str (e.g. "12 + 7 - 4 + 3"),
            "answer":          int,
            "question":        str (the rendered stem — pure or word problem),
        }
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    # Clamp to G3 bounds
    bounds = _PARAM_BOUNDS["g3"]
    min_op = bounds["min_operand"]

    # "3 to 4 numbers" names a range, not a fixed count -- defaulting to a
    # single hardcoded value ("three_terms") when unbound would mean every
    # unbound generation is 3 terms and 4-term items never appear at all.
    # Randomize via this call's own seeded rng so an unbound request still
    # covers both, the same way a continuous axis's own candidate pool spans
    # its whole range instead of collapsing to one point.
    num_operands_label = profile.get("num_operands") or rng.choice(["three_terms", "four_terms"])
    operation_mix      = profile.get("operation_mix", "mixed_add_sub")
    number_size        = profile.get("number_size", "2_digit")
    context            = profile.get("context", "pure")
    # "including problems involving money" (mat_g3_na_q2_7) -- money framing
    # is a sub-case of word_problem context, not its own axis; roughly half
    # of word-problem items use it so the money sub-case is exercised without
    # making every non-money "3 to 4 numbers" item disappear.
    money = profile.get("money")
    if money is None:
        money = context == "word_problem" and rng.random() < 0.5

    n_terms  = 3 if num_operands_label == "three_terms" else 4
    max_op   = 9 if number_size == "1_digit" else 99

    def _finish(operands: List[int], operators: List[str], result: int) -> Dict[str, Any]:
        expression_str = _build_expression_str(operands, operators)
        if context == "word_problem":
            actor = rng.choice(_WP_ACTORS)
            obj = rng.choice(_WP_OBJECTS)
            question = _build_word_problem(actor, obj, operands, operators, money)
        else:
            question = f"{expression_str} = ___"
        return {
            "blank_target":   "answer",
            "operands":       operands,
            "operators":      operators,
            "expression_str": expression_str,
            "answer":         result,
            "context":        context,
            "money":          money,
            "question":       question,
        }

    for _ in range(200):
        operands = [rng.randint(min_op, max_op) for _ in range(n_terms)]

        if operation_mix == "add_only":
            operators = ["+"] * (n_terms - 1)
        else:
            operators = [rng.choice(["+", "-"]) for _ in range(n_terms - 1)]

        result = _evaluate_left_to_right(operands, operators)
        # Reject negative intermediate/final results (G3 students don't use negatives)
        if result < 0:
            continue

        # Verify no negative intermediate
        ok = True
        running = operands[0]
        for op, val in zip(operators, operands[1:]):
            running = running + val if op == "+" else running - val
            if running < 0:
                ok = False
                break
        if not ok:
            continue

        return _finish(operands, operators, result)

    # Fallback: safe add-only expression
    operands = [rng.randint(min_op, 9) for _ in range(n_terms)]
    operators = ["+"] * (n_terms - 1)
    return _finish(operands, operators, _evaluate_left_to_right(operands, operators))


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hints for an order-of-operations problem."""
    operands   = values["operands"]
    operators  = values["operators"]
    expr_str   = values["expression_str"]
    answer     = values["answer"]

    order_label = VOCAB_ORDER.resolve(cumulative_vocab)
    expr_label  = VOCAB_EXPR.resolve(cumulative_vocab)

    hints: List[str] = []
    hints.append(f"Evaluate the {expr_label}: {expr_str}.")
    hints.append(f"Use the {order_label}: work left to right for + and −.")

    # Show step-by-step working
    running = operands[0]
    for i, (op, val) in enumerate(zip(operators, operands[1:]), start=1):
        prev = running
        running = running + val if op == "+" else running - val
        hints.append(f"Step {i}: {prev} {op} {val} = {running}.")

    hints.append(f"The answer is {answer}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

ORDER_OF_OPERATIONS_DNA = DNA(
    concept="order_of_operations",
    dna_type="algorithmic",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
    ],
    requires_context=False,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
