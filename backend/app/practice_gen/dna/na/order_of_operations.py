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

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
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
        }
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    # Clamp to G3 bounds
    bounds = _PARAM_BOUNDS["g3"]
    min_op = bounds["min_operand"]

    num_operands_label = profile.get("num_operands", "three_terms")
    operation_mix      = profile.get("operation_mix", "mixed_add_sub")
    number_size        = profile.get("number_size", "2_digit")

    n_terms  = 3 if num_operands_label == "three_terms" else 4
    max_op   = 9 if number_size == "1_digit" else 99

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

        expression_str = _build_expression_str(operands, operators)

        return {
        "blank_target": "answer",
            "operands":       operands,
            "operators":      operators,
            "expression_str": expression_str,
            "answer":         result,
        }

    # Fallback: safe add-only expression
    operands = [rng.randint(min_op, 9) for _ in range(n_terms)]
    operators = ["+"] * (n_terms - 1)
    return {
        "blank_target": "answer",
        "operands":       operands,
        "operators":      operators,
        "expression_str": _build_expression_str(operands, operators),
        "answer":         _evaluate_left_to_right(operands, operators),
    }


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
    dna_type="formula",
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
