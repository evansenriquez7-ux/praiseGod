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
