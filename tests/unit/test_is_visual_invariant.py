"""
test_is_visual_invariant.py
===========================
Pins the FormattedProblem invariant `is_visual == bool(visual_params)`.

Why it exists
-------------
Three fields describe one fact, and they answer different questions:

  * `visual_type`   -- which visual family the NODE belongs to (a category label,
                       inherited from the registry; a Calendar node may still serve
                       "What month comes after August?" as plain text)
  * `visual_params` -- the payload for THIS problem, or None
  * `is_visual`     -- does THIS problem carry a picture?

Twenty formatters used to each set `is_visual` themselves, and they disagreed:
nineteen used `bool(ctx.visual_params)`, while fmt_true_false.py used
`ctx.visual_type is not None`. That one would ship is_visual=True with
visual_params=None -- and QuestionRenderer.jsx:44 gates its visual branch on
is_visual alone, so the student would get an empty visual instead of the text
question.

Measured at the time of the fix: 0 violations across 755 samples. The gate was
added while its baseline was clean (Scaling Mandate #5) precisely so a grade 4-10
formatter cannot reintroduce the divergence -- the model derives the field, so a
formatter that gets it wrong is corrected rather than believed.
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)

from backend.app.practice_gen.dna.base import FormattedProblem  # noqa: E402


def _problem(**overrides):
    base = dict(
        problem_id="t_1", node_id="t", competency_text="c", grade=1, seed=1,
        question_text="q", correct_answer="a", distractors=[], hints=[],
        format="true_false", format_data={},
        is_visual=False, visual_type="Calendar", visual_params=None,
        interaction_mode=None, answer_collection="mcq",
        difficulty_profile={}, difficulty_axes_served={},
        experience="standard", experience_config=None,
        interest_theme=None, spine_id=None,
    )
    base.update(overrides)
    return FormattedProblem(**base)


def test_claiming_visual_without_a_payload_is_corrected():
    """The fmt_true_false bug: category label mistaken for a payload."""
    p = _problem(is_visual=True, visual_params=None)
    assert p.is_visual is False


def test_claiming_not_visual_with_a_payload_is_corrected():
    p = _problem(is_visual=False, visual_params={"month": 9, "year": 2026})
    assert p.is_visual is True


def test_empty_payload_is_not_visual():
    """An empty dict is not a picture -- the component would render nothing."""
    assert _problem(is_visual=True, visual_params={}).is_visual is False


def test_visual_type_alone_never_makes_a_problem_visual():
    """
    A Calendar node serving a text question is legitimate. visual_type is the NODE's
    category; only a payload makes a given problem visual.
    """
    assert _problem(visual_type="Calendar", visual_params=None).is_visual is False
    assert _problem(visual_type=None, visual_params={"a": 1}).is_visual is True


@pytest.mark.parametrize("payload,expected", [
    (None, False),
    ({}, False),
    ({"k": 1}, True),
    ({"a": 1, "b": 2}, True),
])
def test_invariant_holds_for_every_payload_shape(payload, expected):
    assert _problem(visual_params=payload).is_visual is expected


def test_invariant_holds_across_the_live_tree():
    """Every node/seed the pipeline can serve must satisfy the invariant."""
    from backend.app.practice_gen.registry import get_all_node_ids
    from backend.app.services.orchestrator import PracticeOrchestrator

    violations = []
    for node_id in get_all_node_ids():
        for seed in (11, 42):
            try:
                p = PracticeOrchestrator.generate_problem(
                    node_id=node_id, seed=seed, is_student_path=True
                )
            except Exception:
                continue
            d = p if isinstance(p, dict) else p.model_dump()
            vp = d.get("visual_params")
            has_payload = isinstance(vp, dict) and len(vp) > 0
            if bool(d.get("is_visual")) != has_payload:
                violations.append((node_id, seed, d.get("format"), d.get("is_visual"), type(vp).__name__))

    assert not violations, (
        f"{len(violations)} problem(s) where is_visual disagrees with visual_params: "
        f"{violations[:5]}"
    )
