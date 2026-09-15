"""
test_attestation_freshness.py
=============================
§6F freshness at §5 parity: stem, adjudicability, keyed VALUE, offered options.

Why this file exists alongside `tests/mutation_harness.py`. Three of §6F's four
branches WIDEN the gate and are proven by mutations caught by name
(`attestation_answer_drift`, `attestation_option_drift`, `attestation_drops_options`).
The fourth part is a NARROWING -- resolving an A-D key through the record's own
option table, so a letter moving between slots is not read as content drift -- and a
narrowing cannot be proven by the mutation harness, which scores a plant by making
the validator FAIL. `tests/unit/test_judgment_answer_resolution.py` pins that
narrowing for §5; this file pins it where §6F consumes it, and pins the ORDER of the
branches, which is load-bearing: an answer cannot be resolved without its option
table, so a record that does not carry one must be reported as unadjudicable rather
than as an answer-drift symptom.

It also pins the falsy collapse that `_answer_value` was written to stop.
`_normalize` is `str(x or "")`, which maps `False`, `0` and `None` to the same empty
string. `true_false` items key a bool. `docs/pgen_contract.md` carried
"b11_mat_g2_na_q3_5 seed 11 was attested against a key of False and now renders an
empty key" as this gate's motivating example; re-rendered 2026-09-10 that seed still
keys `False`, and the "empty key" was `_normalize(False)` reporting on itself.
Ten such would-be false positives were in that population.

Nothing here names a formatter. Whether an item is a choice item is decided by the
live render carrying an option table, so a grade-7 formatter that does not exist yet
is covered on the day it is written (Scaling Mandate 4).
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)

from backend.app.practice_gen.validation import judgment_packets  # noqa: E402
from backend.app.practice_gen.validation.validate_capability import (  # noqa: E402
    _attestation_staleness,
)
from backend.app.practice_gen.validation.validate_judgment import _answer_value  # noqa: E402

_NODE = "mat_test_node_q1_0"
_SEED = 11


def _opts(correct_key, values):
    return [{"key": k, "value": v, "is_correct": k == correct_key}
            for k, v in zip("ABCD", values)]


def _record(sample):
    """One live attestation record carrying one judged sample."""
    return {
        "batch": "unit_fixture",
        "packet": {"node_id": _NODE, "samples_judged": [dict(sample, seed=_SEED)]},
        "verdicts": [{"node_id": _NODE, "capability_id": "unit_capability",
                      "clause": "unit clause", "verdict": "PROVIDED"}],
    }


def _run(monkeypatch, recorded, live):
    monkeypatch.setattr(judgment_packets, "_render_sample",
                        lambda node_id, seed: dict(live, seed=seed))
    return _attestation_staleness([_record(recorded)])


# --- _answer_value: the falsy collapse ----------------------------------------

def test_a_recorded_false_matches_a_rendered_false():
    """The record stores the string 'False'; the pipeline keys the bool. Same content."""
    assert _answer_value("False") == _answer_value(False) == "False"


def test_false_and_a_missing_answer_are_not_the_same_thing():
    """An item that STOPS producing an answer must not read as unchanged."""
    assert _answer_value(False) != _answer_value(None)


def test_zero_survives_normalisation():
    assert _answer_value(0) == "0" and _answer_value(0) != _answer_value(None)


# --- the branches, in order ---------------------------------------------------

def test_a_drifted_stem_is_reported_first(monkeypatch):
    errs = _run(monkeypatch,
                {"question_text": "What is 2 + 1?", "correct_answer": "3"},
                {"question_text": "What is 9 + 1?", "correct_answer": "10"})
    assert len(errs) == 1 and "STALE (§6F)" in errs[0] and "The Attester judged" in errs[0]


def test_a_record_without_the_options_it_was_shown_is_unadjudicable(monkeypatch):
    """
    And this must precede the answer comparison: 'C' names nothing without a table.
    Reported as unadjudicable, never as an answer that "changed" from C to 5.
    """
    errs = _run(monkeypatch,
                {"question_text": "What is 2 + 3?", "correct_answer": "C"},
                {"question_text": "What is 2 + 3?", "correct_answer": "C",
                 "options": _opts("C", [3, 4, 5, 6])})
    assert len(errs) == 1
    assert "records no 'options'" in errs[0]
    assert "no longer keys the same answer" not in errs[0]


def test_an_item_that_stopped_being_a_choice_item_is_reported(monkeypatch):
    errs = _run(monkeypatch,
                {"question_text": "What is 2 + 3?", "correct_answer": "C",
                 "options": _opts("C", [3, 4, 5, 6])},
                {"question_text": "What is 2 + 3?", "correct_answer": "5"})
    assert len(errs) == 1 and "stopped being a selection task" in errs[0]


# --- the narrowing: placement-only drift must NOT be reported -----------------

def test_a_letter_moving_between_slots_is_not_drift(monkeypatch):
    """Same stem, same option multiset, same correct VALUE, different letter."""
    errs = _run(monkeypatch,
                {"question_text": "What time is it?", "correct_answer": "C",
                 "options": _opts("C", ["3:15", "2:10", "2:15", "1:15"])},
                {"question_text": "What time is it?", "correct_answer": "B",
                 "options": _opts("B", ["3:15", "2:15", "2:10", "1:15"])})
    assert errs == []


def test_a_recorded_false_against_a_rendered_false_is_not_drift(monkeypatch):
    """The `_normalize` false positive this gate would otherwise have inherited."""
    errs = _run(monkeypatch,
                {"question_text": "Is 90 - 10 x 10 equal to 0? True or False?",
                 "correct_answer": "False"},
                {"question_text": "Is 90 - 10 x 10 equal to 0? True or False?",
                 "correct_answer": False})
    assert errs == []


# --- the widening: real drift MUST be reported --------------------------------

def test_same_key_different_value_is_reported(monkeypatch):
    errs = _run(monkeypatch,
                {"question_text": "What is 490 + 1?", "correct_answer": "C",
                 "options": _opts("C", [493, 490, 491, 492])},
                {"question_text": "What is 490 + 1?", "correct_answer": "C",
                 "options": _opts("C", [7843, 7846, 7844, 7845])})
    assert len(errs) == 1 and "no longer keys the same answer" in errs[0]


def test_an_answer_that_disappears_is_reported(monkeypatch):
    errs = _run(monkeypatch,
                {"question_text": "Is this true? True or False?", "correct_answer": False},
                {"question_text": "Is this true? True or False?", "correct_answer": None})
    assert len(errs) == 1 and "no longer keys the same answer" in errs[0]


def test_a_moved_distractor_under_an_unchanged_key_is_reported(monkeypatch):
    """What the answer comparison structurally cannot see: only the offer moved."""
    errs = _run(monkeypatch,
                {"question_text": "What is 2 + 3?", "correct_answer": "5",
                 "options": _opts("C", [3, 4, 5, 6])},
                {"question_text": "What is 2 + 3?", "correct_answer": "5",
                 "options": _opts("C", [3, 9, 5, 6])})
    assert len(errs) == 1 and "no longer offered the same options" in errs[0]


def test_a_clean_record_reports_nothing(monkeypatch):
    errs = _run(monkeypatch,
                {"question_text": "What is 2 + 3?", "correct_answer": "5",
                 "options": _opts("C", [3, 4, 5, 6])},
                {"question_text": "What is 2 + 3?", "correct_answer": "5",
                 "options": _opts("C", [3, 4, 5, 6])})
    assert errs == []


def _attach_visual(rows):
    out = []
    for row in rows:
        rendered = dict(row)
        if rendered.get("visual_type"):
            rendered["visual_render"] = {
                "visual_type": rendered["visual_type"],
                "renderer_input_digest": "live-render-digest",
                "description": {
                    "source": "rendered_static_markup",
                    "element_count": 17,
                    "role_counts": {"number-line-jump": 2},
                },
            }
        rendered.pop("_visual_params", None)
        out.append(rendered)
    return out


def test_a_visual_attestation_without_rendered_evidence_is_unadjudicable(monkeypatch):
    from tests import frontend_renderer

    monkeypatch.setattr(frontend_renderer, "attach_rendered_visual_descriptions", _attach_visual)
    base = {"question_text": "Use the number line.", "correct_answer": 6}
    live = {**base, "visual_type": "NumberLine",
            "_visual_params": {"start": 0, "end": 10, "jump_count": 2, "jump_size": 3}}
    errs = _run(monkeypatch, base, live)
    assert len(errs) == 1 and "records no render-derived visual evidence" in errs[0]


def test_a_changed_rendered_visual_makes_attestation_stale(monkeypatch):
    from tests import frontend_renderer

    monkeypatch.setattr(frontend_renderer, "attach_rendered_visual_descriptions", _attach_visual)
    base = {"question_text": "Use the number line.", "correct_answer": 6}
    recorded = {**base, "visual_render": {
        "visual_type": "NumberLine",
        "renderer_input_digest": "old-render-digest",
        "description": {"source": "rendered_static_markup", "element_count": 2},
    }}
    live = {**base, "visual_type": "NumberLine",
            "_visual_params": {"start": 0, "end": 10, "jump_count": 2, "jump_size": 3}}
    errs = _run(monkeypatch, recorded, live)
    assert len(errs) == 1 and "render-derived visual description" in errs[0]
