"""
operand_guard.py — Prevent semantic leaks in fill-in-the-blank problems.

A semantic leak occurs when a fill-in-the-blank problem lets the student
read the answer directly from a non-blank operand in the prompt. For
example, "2 + 2 = ___" with answer 4 has no leak (the answer is not
visible), but "9 + 0 = ___" with answer 9 leaks (the answer 9 is the
non-blank operand). Similarly, "5 - ___ = 0" with answer 5 leaks
because the answer equals the minuend.

This helper is called by every DNA's `generate_params` after a candidate
pair is selected, to ensure the chosen pair does not produce a leaky
problem under any reasonable blank position.

MATATAG's "Strict Vocabulary Gating" principle and the auditor's
"Semantic Leak" check both rely on this guarantee.
"""

from __future__ import annotations

from typing import List, Optional


def is_duplicate_operand_pair(a: int, b: int, blank_target: str) -> bool:
    """Return True if (a, b) with the given blank_target would let the
    student read the answer from a non-blank operand.

    For fill-in-the-blank problems, the answer is one of {a, b, a+b} (or
    a-b / a*b / a/b depending on operation); the other two are visible.
    A leak happens when the answer is identical to one of the visible
    operands.

    Args:
        a: first operand.
        b: second operand.
        blank_target: which value is the blank — one of
            {"result", "a", "b", "start", "change", "minuend",
            "subtrahend", "factor", "product", "dividend", "divisor",
            "quotient"}.
    """
    if a < 0 or b < 0:
        return False

    # result is the computed answer (a+b, a-b, a*b, a/b). The visible
    # operands are a and b. Leak if either operand equals result.
    if blank_target == "result":
        # Caller passes (a, b, result) via the more specific helpers
        # below; this branch is a no-op for the pair-only signature.
        return False

    # blank is "a" — answer is a. Visible operand is b. Leak if a == b.
    if blank_target == "a":
        return a == b

    # blank is "b" — answer is b. Visible operand is a. Leak if a == b.
    if blank_target == "b":
        return a == b

    return False


def is_addition_leak(a: int, b: int, blank_target: str) -> bool:
    """Return True if (a, b) with blank_target would leak for addition.

    For addition: a + b = result.
    - blank = "result": visible = {a, b}. Leak if a == 0 (then result = b)
      or b == 0 (then result = a). Already excluded at the (0, 0)/(X, 0)
      filter, but called here for safety.
    - blank = "a": answer is a. visible = b, result. Leak if a == b or
      a == a + b (only when b == 0, already excluded).
    - blank = "b": answer is b. visible = a, result. Leak if a == b or
      b == a + b (only when a == 0, already excluded).
    """
    if a < 0 or b < 0:
        return False
    if a == 0 or b == 0:
        return True
    if blank_target in ("a", "b"):
        return a == b
    return False


def is_subtraction_leak(a: int, b: int, blank_target: str) -> bool:
    """Return True if (a, b) with blank_target would leak for subtraction.

    For subtraction: a - b = result.
    - blank = "result": visible = {a, b}. Leak if b == 0 (then result = a,
      already excluded) or a == 2*b (then result = b, visible).
    - blank = "a" (minuend): answer is a. visible = b, result.
      Leak if a == result (only if b == 0, already excluded) or a == b
      (then result = 0, and answer a == visible b).
    - blank = "b" (subtrahend): answer is b. visible = a, result.
      Leak if b == result (only if a == 0) or a == 2*b (then result = b,
      visible).
    """
    if a < 0 or b < 0:
        return False
    if b == 0:
        return True  # already excluded at the (X, 0) filter
    if blank_target == "result":
        # a - b = result. result == b iff a == 2*b. Exclude.
        return a == 2 * b
    if blank_target == "a":
        # answer is a. visible = b, a-b. a == b means result = 0; answer a
        # equals visible b.
        return a == b
    if blank_target == "b":
        # answer is b. visible = a, a-b. a == 2*b means result == b.
        return a == 2 * b
    return False


def is_multiplication_leak(a: int, b: int, blank_target: str) -> bool:
    """Return True if (a, b) with blank_target would leak for multiplication.

    For multiplication: a * b = result.
    - blank = "result": visible = {a, b}. Leak if a == 1 (result = b) or
      b == 1 (result = a).
    - blank = "a" (factor): answer is a. visible = b, result. Leak if
      a == b or a == 1 (then result = b, and a == b).
    - blank = "b" (factor): answer is b. visible = a, result. Leak if
      a == b or b == 1.
    """
    if a < 0 or b < 0:
        return False
    if a == 1 or b == 1:
        return True
    if blank_target in ("a", "b"):
        return a == b
    return False


def is_division_leak(a: int, b: int, blank_target: str) -> bool:
    """Return True if (a, b) with blank_target would leak for division.

    For division: a / b = result.
    - blank = "result" (quotient): visible = {a, b}. Leak if b == 1
      (result = a) or a == b (result = 1, degenerate) or a == b^2
      (result = b, leaks the visible divisor).
    - blank = "a" (dividend): answer is a. visible = b, result.
      Leak if a == b (then result = 1) or a == b^2 (then a == result).
    - blank = "b" (divisor): answer is b. visible = a, result.
      Leak if a == b^2 (then result == b) or b == 1 (then a == result).
    """
    if a < 0 or b <= 0:
        return False
    if b == 1:
        return True
    if blank_target == "result":
        return a == b or a == b * b
    if blank_target == "a":
        return a == b or a == b * b
    if blank_target == "b":
        return a == b or a == b * b
    return False
