"""
test_emoji_pictorial_max_val.py
================================
Verifies that the emoji_pictorial formatter raises ValueError when
any of (a, b, number, answer, start) > 100.

This check was moved from backend/app/practice_gen/adapter.py
(where it was a hard-coded special case for emoji_pictorial) into
the formatter itself (format_emoji_pictorial), where the formatter
owns its own numeric constraints.

Per AGENTS.md rule #4: the formatter fails fast — it does NOT
silently degrade to a placeholder when a value exceeds its
displayable range. The audit catches the ValueError as a Pipeline
Crash, which is the correct outcome (the orchestrator should
pre-filter profiles that produce values > 100 for emoji_pictorial).
"""

import os
import random
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)


def _make_ctx(values, dna_concept="addition", grade=1, seed=1):
    from backend.app.practice_gen.dna.base import QuestionContext
    return QuestionContext(
        values=values,
        correct_answer=values.get("a", 0) + values.get("b", 0),
        distractors=[],
        answer_formula="a + b",
        question_text="Test",
        question_text_with_blank="a + b = ___",
        blank_target="result",
        hints=[],
        competency_text="Test competency",
        cumulative_vocab=[],
        visual_type="EmojiPictorial",
        visual_params=None,
        node_id="mat_g1_na_q1_0",
        grade=grade,
        seed=seed,
        interest_theme=None,
        spine_id=None,
        difficulty_profile={},
        difficulty_axes_served={},
        dna_concept=dna_concept,
        dna_type="formula",
    )


def test_emoji_pictorial_raises_on_large_a():
    from backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial import format_emoji_pictorial
    ctx = _make_ctx({"a": 150, "b": 2})
    with pytest.raises(ValueError, match="max_val.*150.*>.*100"):
        format_emoji_pictorial(ctx, random.Random(1))


def test_emoji_pictorial_raises_on_large_b():
    from backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial import format_emoji_pictorial
    ctx = _make_ctx({"a": 5, "b": 200})
    with pytest.raises(ValueError, match="max_val.*200.*>.*100"):
        format_emoji_pictorial(ctx, random.Random(1))


def test_emoji_pictorial_raises_on_large_answer():
    from backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial import format_emoji_pictorial
    # Use a non-arithmetic DNA concept so the value is taken from `answer`
    ctx = _make_ctx({"answer": 500}, dna_concept="counting")
    with pytest.raises(ValueError, match="max_val.*500.*>.*100"):
        format_emoji_pictorial(ctx, random.Random(1))


def test_emoji_pictorial_accepts_small_values():
    from backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial import format_emoji_pictorial
    ctx = _make_ctx({"a": 5, "b": 3})
    result = format_emoji_pictorial(ctx, random.Random(1))
    assert result.is_visual is True
    assert result.visual_type == "EmojiPictorial"


def test_emoji_pictorial_accepts_exactly_100():
    from backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial import format_emoji_pictorial
    ctx = _make_ctx({"a": 100, "b": 1})
    # 100 is the boundary; should NOT raise
    result = format_emoji_pictorial(ctx, random.Random(1))
    assert result.is_visual is True
