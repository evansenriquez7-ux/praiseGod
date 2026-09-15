from types import SimpleNamespace

import pytest

from backend.app.practice_gen.generators.interest import get_interest_emoji
from backend.app.practice_gen.validation import validate_interest
from backend.app.services.orchestrator import PracticeOrchestrator


def test_interest_emoji_is_grade_gated_and_has_no_silent_fallback():
    assert get_interest_emoji("bible", 1) == "✝️"
    with pytest.raises(ValueError, match="Unknown interest theme"):
        get_interest_emoji("not-a-theme", 1)
    with pytest.raises(ValueError, match="not supported for grade=1"):
        get_interest_emoji("ppop", 1)


def test_theme_survives_a_formatter_that_rebuilds_the_question():
    problem = PracticeOrchestrator.generate_problem(
        node_id="mat_g1_na_q1_0",
        seed=731,
        interest_theme="bible",
        formatter="cloze",
        is_student_path=True,
        forced_dna="counting",
    )

    assert problem.interest_theme == "bible"
    assert "✝️" in problem.question_text


def test_emoji_pictorial_uses_the_requested_theme_emoji():
    problem = PracticeOrchestrator.generate_problem(
        node_id="mat_g1_na_q1_0",
        seed=731,
        interest_theme="bible",
        formatter="emoji_pictorial",
        is_student_path=True,
        forced_dna="counting",
    )

    assert problem.visual_type == "EmojiPictorial"
    assert problem.visual_params["emoji"] == "✝️"


def test_visibility_gate_rejects_metadata_only_interest(monkeypatch):
    dna = SimpleNamespace(requires_context=True, concept="addition")

    def metadata_only_problem(**kwargs):
        return SimpleNamespace(
            node_id=kwargs["node_id"],
            dna_name="addition",
            interest_theme=kwargs["interest_theme"],
            correct_answer=3,
            model_dump=lambda: {
                "question_text": "What is 1 + 2?",
                "correct_answer": 3,
            },
        )

    monkeypatch.setattr(
        validate_interest.PracticeOrchestrator,
        "generate_problem",
        metadata_only_problem,
    )

    errors = validate_interest.validate_interest_invariance(
        dna,
        grade=1,
        node_id="mat_g1_na_q1_7",
        trials=1,
    )

    assert errors
    assert all("interest_theme_visibility" in error for error in errors)
