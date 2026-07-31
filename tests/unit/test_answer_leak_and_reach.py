"""
Unit tests for the two contract checks added on 2026-07-27:
  §1F  — a question stem may not give away its own answer
  §1A-reach — supporting helpers for "scalar 1.0 reaches the competency maximum"

These exist so the boundaries of §1F can be re-verified in a second rather than by
sitting through a full 151-node matrix run. §1F is deliberately narrow: its first
version fired on 3,702 samples because it conflated answer leakage with
legitimate commutativity items and with degenerate-but-valid identity facts. The
"OK" cases below are that boundary, and they are the part most likely to regress
if someone widens the rule.
"""

from __future__ import annotations

import pytest

from backend.app.practice_gen.validation.validate_matrix import (
    MAGNITUDE_CAP_AXES,
    _answer_leaks_into_stem,
    _numeric_payload_values,
    _option_in_stem,
)


def _problem(question: str, answer, options):
    return {
        "question_text": question,
        "correct_answer": answer,
        "format_data": {
            "options": [{"value": v, "is_correct": v == answer} for v in options]
        },
    }


# ── §1F: stems that genuinely give away their answer ─────────────────────────

LEAKING = [
    ("clock restates the time",
     "Jose has lunch at 1:30. What time is that?", "1:30",
     ["1:30", "2:30", "12:30", "0:13"]),
    ("fraction displayed then asked for",
     r"What fraction does \(\frac{2}{5}\) equal parts represent?", "2/5",
     ["5/2", "2/5", "3/5", "4/10"]),
    ("measurement stated then asked for",
     "Ben used paperclips to measure a book. It measured 10 paperclips long. "
     "How long is a book in paperclips?", 10,
     [10, 9, 12, 11]),
]


@pytest.mark.parametrize("label,question,answer,options", LEAKING)
def test_detects_answer_leak(label, question, answer, options):
    assert _answer_leaks_into_stem(_problem(question, answer, options)) is not None, label


# ── §1F: items that legitimately restate a value ─────────────────────────────

NOT_LEAKING = [
    # Comparison items name every candidate they ask about.
    ("shape comparison",
     "Which shape has more sides — a triangle or a rectangle?", "rectangle",
     ["rectangle", "they are equal", "neither", "triangle"]),
    # The task *is* restating an operand under an operation.
    ("commutativity",
     "Complete the equivalent expression: 2 + 1 = 1 + ___", 2, [2, 3, 1, 4]),
    ("additive identity", "2 + 0 = ___", 2, [2, 3, 1, 0]),
    ("multiplicative identity",
     "4 × 1 = ___. What is the missing number?", 4, [4, 5, 3, 1]),
    # A second datum means the student has to combine them.
    ("money with a zero part",
     "Ate Cara has ₱0 in bills and ₱46 in coins. How much money in all?", 46,
     [46, 45, 47, 0]),
    # Ordinary computation.
    ("plain arithmetic", "What is 8500 + 225?", 8725, [8724, 8275, 8725, 8735]),
    ("next term", "What number comes next when counting: 4, 5, 6, 7, ___?", 8,
     [8, 9, 7, 6]),
    ("subtraction", "12 − 2 = ___", 10, [10, 14, 9, -10]),
    # Symmetry: answer == given is the correct mathematics, not a leak.
    ("symmetry mirrors its input",
     "A symmetric figure has a horizontal line of symmetry. If the top half has "
     "6 squares, how many squares are in the bottom half?", 6, [6, 5, 7, 12]),
]


@pytest.mark.parametrize("label,question,answer,options", NOT_LEAKING)
def test_ignores_legitimate_restatement(label, question, answer, options):
    assert _answer_leaks_into_stem(_problem(question, answer, options)) is None, label


def test_ordering_answers_are_exempt():
    """Ordering restates every value it asks the student to sort."""
    p = _problem("Arrange from smallest to largest: 502, 507, 495", [495, 502, 507], [])
    assert _answer_leaks_into_stem(p) is None


def test_true_false_answers_are_exempt():
    p = _problem("3 + 10 = 13. True or False?", True, [True, False])
    assert _answer_leaks_into_stem(p) is None


# ── token matching: the part that makes the rule usable at all ───────────────

def test_option_matching_respects_token_boundaries():
    # "11" must not match inside "0:11", and "1" must not match inside "1.5",
    # or nearly every arithmetic item would look like a leak.
    assert not _option_in_stem("11", "the answer is 0:11")
    assert not _option_in_stem("1", "a stick is 1.5 m long")
    # ...but a value ending a sentence still matches.
    assert _option_in_stem("11:00", "maria wakes up at 11:00.")
    assert _option_in_stem("46", "she has 46 pesos")


# ── §1A-reach supporting helpers ─────────────────────────────────────────────

def test_numeric_payload_skips_booleans_and_collects_nested():
    p = {
        "given_values": {"a": 3, "flag": True, "sequence": [4, 5]},
        "correct_answer": 12,
    }
    labelled = dict(_numeric_payload_values(p))
    assert labelled["given_values.a"] == 3.0
    assert labelled["given_values.sequence[1]"] == 5.0
    assert labelled["correct_answer"] == 12.0
    # True == 1 in Python; a true/false answer carries no magnitude.
    assert "given_values.flag" not in labelled


def test_magnitude_cap_axes_exclude_non_magnitude_axes():
    # number_difficulty is a 0-1 scalar and num_categories is a count; asserting
    # a magnitude ceiling against either is meaningless.
    assert "number_difficulty" not in MAGNITUDE_CAP_AXES
    assert "num_categories" not in MAGNITUDE_CAP_AXES
    assert {"max_sum", "max_product", "range"} <= MAGNITUDE_CAP_AXES
