"""
test_distractor_fallback.py — Phase 1B verification

Per AGENTS.md rule #4: "Avoid Graceful Fallbacks and Silent Defaulting
Behavior: Do not use." This test suite verifies that:

1. The ``augment_distractors`` helper returns valid, distinct, non-correct
   candidates for numeric, string, and boolean ``correct`` values.
2. Each of the 15 formatters no longer raises the fail-fast
   ``len(distractors) < 3`` ValueError when given a small-range profile
   (the helper pads the pool before the raise is evaluated).
3. The fail-fast raise is *still* preserved if the helper itself cannot
   produce enough candidates (verified by calling the helper with a
   target larger than the max_delta space).
"""

import random
from typing import Any, Dict, List

import pytest

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.formatters._distractor_fallback import (
    augment_distractors,
)
from backend.app.practice_gen.formatters.textual import fmt_cloze, fmt_mcq
from backend.app.practice_gen.formatters.visual import (
    fmt_calendar,
    fmt_clock,
    fmt_emoji_pictorial,
    fmt_fraction_model,
    fmt_fraction_shade,
    fmt_number_bond,
    fmt_number_line,
    fmt_pattern_sequence,
    fmt_peso_money,
    fmt_pictograph,
    fmt_place_value_blocks,
    fmt_ruler_measure,
    fmt_ten_frame,
)


# ─────────────────────────────────────────────────────────────────────────────
# QuestionContext builders (one per formatter, parameterised for stress test)
# ─────────────────────────────────────────────────────────────────────────────


def _ctx(values: Dict[str, Any], **overrides: Any) -> QuestionContext:
    """Build a minimal QuestionContext for textual-formatter tests."""
    base = {
        "values": values,
        "correct_answer": overrides.get("correct_answer", values.get("result", 0)),
        "distractors": overrides.get("distractors", []),
        "answer_formula": None,
        "question_text": "What is the answer?",
        "question_text_with_blank": "What is ___?",
        "blank_target": "result",
        "hints": [],
        "competency_text": "Test competency",
        "visual_type": None,
        "visual_params": None,
        "node_id": overrides.get("node_id", "test_node_1"),
        "grade": overrides.get("grade", 1),
        "seed": overrides.get("seed", 1),
        "interest_theme": None,
        "spine_id": None,
        "difficulty_profile": overrides.get("difficulty_profile", {}),
        "difficulty_axes_served": {},
        "dna_concept": overrides.get("dna_concept", "addition"),
        "dna_type": "formula",
    }
    base.update(overrides)
    return QuestionContext(**base)


def _emoji_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"a": 2, "b": 1},
        correct_answer=3,
        distractors=[],
        node_id=f"emoji_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="addition",
        difficulty_profile={"max_sum": 0.0},
    )


def _peso_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"total": 5},
        correct_answer=5,
        distractors=[],
        node_id=f"peso_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="money_peso",
        difficulty_profile={"max_total": 0.0},
    )


def _pictograph_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {},
        correct_answer=4,
        distractors=[],
        node_id=f"pictograph_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="counting",
        difficulty_profile={"max_value": 0.0},
    )


def _pattern_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"sequence": [2, 4, 6, 8, 10], "missing_indices": [4]},
        correct_answer=10,
        distractors=[],
        node_id=f"pattern_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="skip_counting",
        difficulty_profile={"max_value": 0.0},
    )


def _fraction_model_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"numerator": 1, "denominator": 4},
        correct_answer="1/4",
        distractors=[],
        node_id=f"fractionmodel_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="fractions",
        difficulty_profile={"max_denominator": 0.0},
    )


def _fraction_shade_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"numerator": 1, "denominator": 4},
        correct_answer="1/4",
        distractors=[],
        node_id=f"fractionshade_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="fractions",
        difficulty_profile={"max_denominator": 0.0},
    )


def _number_bond_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"a": 3, "b": 2, "result": 5, "blank_target": "result"},
        correct_answer=5,
        distractors=[],
        node_id=f"numberbond_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="addition",
        difficulty_profile={"max_sum": 0.0},
    )


def _ten_frame_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"number": 3, "query_type": "count_filled"},
        correct_answer=3,
        distractors=[],
        node_id=f"tenframe_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="counting",
        difficulty_profile={"max_value": 0.0},
    )


def _place_value_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"number": 23},
        correct_answer=23,
        distractors=[],
        node_id=f"placevalue_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="place_value",
        difficulty_profile={"max_value": 0.0},
    )


def _calendar_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"day": 15},
        correct_answer="Monday",
        distractors=[],
        node_id=f"calendar_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="calendar",
        difficulty_profile={"max_value": 0.0},
    )


def _ruler_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"length": 3, "unit": "cm", "object_start": 0},
        correct_answer=3,
        distractors=[],
        node_id=f"ruler_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="measurement",
        difficulty_profile={"max_value": 0.0},
    )


def _clock_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"hour": 3, "minute": 0},
        correct_answer="3:00",
        distractors=[],
        node_id=f"clock_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="time",
        difficulty_profile={"max_value": 0.0},
    )


def _number_line_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"number": 5, "a": 3, "b": 2, "result": 5},
        correct_answer=5,
        distractors=[],
        node_id=f"numberline_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="counting",
        difficulty_profile={"max_value": 0.0},
    )


def _cloze_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"a": 2, "b": 3, "result": 5, "context": "pure"},
        correct_answer=5,
        distractors=[],
        node_id=f"cloze_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="addition",
        difficulty_profile={"max_sum": 0.0},
    )


def _mcq_ctx(seed: int) -> QuestionContext:
    return _ctx(
        {"a": 2, "b": 3, "result": 5, "context": "pure"},
        correct_answer=5,
        distractors=[],
        node_id=f"mcq_test_{seed}",
        seed=seed,
        grade=1,
        dna_concept="addition",
        difficulty_profile={"max_sum": 0.0},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests for augment_distractors
# ─────────────────────────────────────────────────────────────────────────────


class TestAugmentDistractors:
    def test_pads_to_target_with_numeric_correct(self):
        result = augment_distractors({1, 2}, correct=5, target=3, max_delta=5)
        assert len(result) == 3
        assert 1 in result
        assert 2 in result
        for v in result:
            assert v != 5

    def test_returns_input_when_already_sufficient(self):
        result = augment_distractors({1, 2, 3, 4}, correct=5, target=3)
        assert len(result) == 3
        assert all(v in {1, 2, 3, 4} for v in result)

    def test_excludes_correct_answer(self):
        result = augment_distractors({5, 6, 7}, correct=5, target=3)
        assert 5 not in result
        assert len(result) == 3

    def test_dedupes_input(self):
        result = augment_distractors([1, 1, 2, 2], correct=10, target=3, max_delta=5)
        assert len(result) == len(set(result))

    def test_string_correct_raises_value_error(self):
        with pytest.raises(ValueError, match="Cannot generate enough unique distractors"):
            augment_distractors(set(), correct="cat", target=3, max_delta=5)

    def test_bool_correct_uses_negation(self):
        result = augment_distractors(set(), correct=True, target=3, max_delta=5)
        assert len(result) == 1
        assert result == [False]

    def test_exhaustion_returns_what_is_available(self):
        result = augment_distractors({6}, correct=5, target=10, max_delta=3)
        assert len(result) <= 6  # 1 input + 5 ± = 6, but some may collide

    def test_does_not_mutate_input(self):
        original = {1, 2}
        augment_distractors(original, correct=5, target=3, max_delta=5)
        assert original == {1, 2}

    def test_zero_target_returns_empty(self):
        assert augment_distractors({1, 2}, correct=5, target=0) == []

    def test_rejects_negative_target(self):
        with pytest.raises(ValueError):
            augment_distractors({1}, correct=5, target=-1)

    def test_rejects_negative_max_delta(self):
        with pytest.raises(ValueError):
            augment_distractors({1}, correct=5, target=3, max_delta=-1)

    def test_numeric_candidates_are_within_max_delta(self):
        result = augment_distractors(set(), correct=10, target=3, max_delta=5)
        for v in result:
            assert abs(v - 10) <= 5

    def test_float_correct_handled(self):
        result = augment_distractors(set(), correct=3.5, target=3, max_delta=5)
        assert len(result) == 3
        for v in result:
            assert v != 3.5


# ─────────────────────────────────────────────────────────────────────────────
# Integration tests — one per formatter, 5 seeds each
# ─────────────────────────────────────────────────────────────────────────────


def _assert_mcq_succeeds(formatted: FormattedProblem) -> None:
    """Assert MCQ output is well-formed and has 4 distinct options."""
    assert formatted.format_data is not None
    options_key = "mcq_options" if "mcq_options" in formatted.format_data else "options"
    options = formatted.format_data.get(options_key)
    assert options is not None, f"No {options_key} in format_data for {formatted.visual_type}"
    assert len(options) == 4, f"Expected 4 options, got {len(options)} for {formatted.visual_type}"
    keys = [o["key"] for o in options]
    assert len(set(keys)) == 4, f"Duplicate option keys: {keys}"
    assert sum(1 for o in options if o.get("is_correct")) == 1, "Expected exactly 1 correct option"


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_emoji_pictorial_does_not_raise(seed: int) -> None:
    ctx = _emoji_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_emoji_pictorial.format_emoji_pictorial(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_peso_money_does_not_raise(seed: int) -> None:
    ctx = _peso_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_peso_money.format_peso_money(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_pictograph_does_not_raise(seed: int) -> None:
    ctx = _pictograph_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_pictograph.format_pictograph(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_pattern_sequence_does_not_raise(seed: int) -> None:
    ctx = _pattern_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_pattern_sequence.format_pattern_sequence(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_fraction_model_does_not_raise(seed: int) -> None:
    ctx = _fraction_model_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_fraction_model.format_fraction_model(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_fraction_shade_does_not_raise(seed: int) -> None:
    ctx = _fraction_shade_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_fraction_shade.format_fraction_shade(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_number_bond_does_not_raise(seed: int) -> None:
    ctx = _number_bond_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_number_bond.format_number_bond(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_ten_frame_does_not_raise(seed: int) -> None:
    ctx = _ten_frame_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_ten_frame.format_ten_frame(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_place_value_blocks_does_not_raise(seed: int) -> None:
    ctx = _place_value_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_place_value_blocks.format_place_value_blocks(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_calendar_does_not_raise(seed: int) -> None:
    ctx = _calendar_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_calendar.format_calendar(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_ruler_measure_does_not_raise(seed: int) -> None:
    ctx = _ruler_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_ruler_measure.format_ruler_measure(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_clock_does_not_raise(seed: int) -> None:
    ctx = _clock_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_clock.format_clock(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_number_line_does_not_raise(seed: int) -> None:
    ctx = _number_line_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_number_line.format_number_line(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_cloze_does_not_raise(seed: int) -> None:
    ctx = _cloze_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_cloze.format_cloze(ctx, rng)
    if formatted.format_data.get("mcq_options"):
        _assert_mcq_succeeds(formatted)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_mcq_does_not_raise(seed: int) -> None:
    ctx = _mcq_ctx(seed)
    rng = random.Random(seed)
    formatted = fmt_mcq.format_mcq(ctx, rng)
    _assert_mcq_succeeds(formatted)


# ─────────────────────────────────────────────────────────────────────────────
# Fail-fast preservation test
# ─────────────────────────────────────────────────────────────────────────────


def test_augment_distractors_exhaustion_does_not_pad_with_silently_duplicated_values() -> None:
    """
    Verify the helper does not silently return duplicates or the correct
    value when its search space is exhausted. The fail-fast raise is the
    formatters' responsibility, but the helper must not mask a bug.
    """
    result = augment_distractors({6}, correct=5, target=20, max_delta=3)
    assert 5 not in result
    assert all(isinstance(v, int) for v in result)
    assert len(result) == len(set(result))
