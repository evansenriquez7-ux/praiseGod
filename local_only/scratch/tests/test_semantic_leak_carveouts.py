"""
test_semantic_leak_carveouts.py
================================
Verifies that the new PROMPT_TARGET_STEM_PATTERNS carve-outs in
exhaustive_checklist_auditor correctly identify stem templates where
the answer is in the stem by design (not a semantic leak).

Per AGENTS.md rule #4: these carve-outs are explicit, named, and
narrow — they apply to specific stem templates, not to whole formatter
classes. The test verifies both positive matches (carve-out applies)
and negative matches (carve-out does NOT apply to unrelated stems).
"""

import pytest

from exhaustive_checklist_auditor import (
    stem_is_prompt_target,
    PROMPT_TARGET_STEM_PATTERNS,
)


@pytest.mark.parametrize("stem", [
    "Use coins and bills to make exactly ₱50. Use the fewest pieces possible.",
    "Use coins and bills to make exactly ₱100. Use the fewest pieces possible.",
    "Use coins and bills to make exactly ₱75. Use the fewest pieces possible.",
    "Use coins and bills to make exactly ₱ 25 . Use the fewest pieces possible.",
    "use coins and bills to make exactly ₱10. use the fewest pieces possible.",
])
def test_money_prompt_target_carveout_positive(stem):
    assert stem_is_prompt_target(stem), f"Expected carve-out for: {stem!r}"


@pytest.mark.parametrize("stem", [
    "What is 6 × 6?",
    "What is 7 × 3?",
    "What is 4 × 8?",
    "What is 9 ÷ 3?",
    "What is 5 x 5?",
    "What is 2 * 2?",
    "What is 10 / 2?",
    # Cloze-format variants (no question mark)
    "6 × 6 = ___",
    "5 + 3 = ___",
    "9 - 4 = ___",
    "12 ÷ 3 = ___",
    # Fill-in-the-blank with one operand missing
    "5 × ___ = 15",
    "___ × 3 = 15",
    "5 + ___ = 8",
    "___ + 3 = 8",
    # Verbal fill-in
    "What times 5 equals 15?",
])
def test_single_digit_arith_carveout_positive(stem):
    assert stem_is_prompt_target(stem), f"Expected carve-out for: {stem!r}"


@pytest.mark.parametrize("stem", [
    "What number comes after 2 when counting by 1?",
    "What number comes after 10 when counting by 5?",
    "What number comes after 0?",
])
def test_what_number_comes_after_carveout_positive(stem):
    assert stem_is_prompt_target(stem), f"Expected carve-out for: {stem!r}"


@pytest.mark.parametrize("stem", [
    "What is the value of the digit 2 in 20?",
    "What is the value of the digit 5 in 357?",
    "What is the value of the digit 1 in 100?",
])
def test_place_value_carveout_positive(stem):
    assert stem_is_prompt_target(stem), f"Expected carve-out for: {stem!r}"


@pytest.mark.parametrize("stem", [
    "The number 50 is written in words as ___",
    "The number 226 is written in words as ___",
])
def test_number_to_words_carveout_positive(stem):
    assert stem_is_prompt_target(stem), f"Expected carve-out for: {stem!r}"


@pytest.mark.parametrize("stem", [
    "Round 47 to the nearest 10.",
    "Round 125 to the nearest 100.",
])
def test_rounding_carveout_positive(stem):
    assert stem_is_prompt_target(stem), f"Expected carve-out for: {stem!r}"


@pytest.mark.parametrize("stem", [
    "Which is heavier: 50 g or 30 g?",
    "Which is lighter: 100 g or 200 g?",
    "Which is more: 250 mL or 100 mL?",
    "Which is less: 50 mL or 75 mL?",
    "Which is longer: 10 m or 5 m?",
])
def test_comparing_measurement_carveout_positive(stem):
    assert stem_is_prompt_target(stem), f"Expected carve-out for: {stem!r}"


@pytest.mark.parametrize("stem", [
    # Real semantic leaks — should NOT be carved out
    "How many apples are there?",
    "Maria has 5 apples and gives 2 to Juan. How many are left?",
    "What is 6 + 7?",
    "Solve: 3 × 4 = ___",
    "Arrange these numbers from largest to smallest: 8, 2, 5, 1",
    "What is the next number: 2, 4, 6, 8, ___?",
    "If you have 5 apples and eat 2, how many are left?",
    "Find the sum of 3 and 4",
])
def test_carveout_does_not_apply_to_real_leaks(stem):
    # These are real semantic leak candidates (or at least not
    # prompt-target templates). The carve-out must NOT match them.
    assert not stem_is_prompt_target(stem), (
        f"Carve-out incorrectly applied to: {stem!r}"
    )


def test_carveout_empty_stem():
    assert not stem_is_prompt_target("")


def test_carveout_set_is_nonempty():
    # Regression net: if someone accidentally clears the set, fail loud.
    assert len(PROMPT_TARGET_STEM_PATTERNS) >= 6


"""
Standalone-number semantic-leak check (separate from PROMPT_TARGET_STEM_PATTERNS).
The audit's check uses `(?<!\d)N(?!\d)` to ensure N is a standalone number in
the stem, not a digit within a multi-digit number like "12" or "100".
"""

import re


def _is_standalone_number_in_stem(answer, stem):
    """Re-implements the audit's semantic-leak check."""
    pattern = rf"(?<!\d){re.escape(str(answer))}(?!\d)"
    return bool(re.search(pattern, stem))


def test_standalone_number_check_positive_when_actually_standalone():
    # "3" appears as a standalone number (not part of a larger number)
    stem = "Maria has 3 apples. She buys 2 more. How many in all?"
    assert _is_standalone_number_in_stem(3, stem) is True


def test_standalone_number_check_negative_when_part_of_larger_number():
    # "2" is part of "12" (the blank) — should NOT be flagged
    stem = "Mika has 1___ colored pencils. Mika gives away 10 colored pencils. How many colored pencils does Mika have left?"
    assert _is_standalone_number_in_stem(2, stem) is False


def test_standalone_number_check_negative_when_part_of_larger_number_2():
    # "5" is part of "15" — should NOT be flagged
    stem = "There are 15 mystery novels on the table. Kuya Dex takes away 1. How many are left?"
    # answer is 14, not 5; this is just testing the pattern
    assert _is_standalone_number_in_stem(5, "There are 15 mystery novels. She gives away 1. How many are left?") is False


def test_standalone_number_check_positive_for_larger_answer():
    # "12" is the answer and appears standalone in the stem
    stem = "Maria has 5 apples and gets 7 more. How many in all? 12"
    assert _is_standalone_number_in_stem(12, stem) is True


def test_standalone_number_check_negative_for_larger_answer_part_of_larger():
    # "12" is part of "120" — should NOT be flagged
    stem = "The number is 120. Subtract 108. What is the result."
    assert _is_standalone_number_in_stem(12, stem) is False


def test_standalone_number_check_handles_negative_answer():
    # Negative numbers (e.g. -3) — the dash is a non-digit, so the check works
    stem = "The temperature is -3 degrees."
    assert _is_standalone_number_in_stem(-3, stem) is True


def test_standalone_number_check_handles_zero():
    stem = "0 apples are left."
    assert _is_standalone_number_in_stem(0, stem) is True
    stem = "100 apples are left."
    assert _is_standalone_number_in_stem(0, stem) is False


def test_standalone_number_check_word_boundary_at_punctuation():
    # "3" at the end of a sentence (followed by period) should still match
    stem = "The answer is 3."
    assert _is_standalone_number_in_stem(3, stem) is True
    # "3" followed by another number "3" — should NOT match
    stem = "The answer is 33."
    assert _is_standalone_number_in_stem(3, stem) is False
