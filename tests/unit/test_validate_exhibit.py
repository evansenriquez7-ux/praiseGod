"""
§2L's classification, pinned against stubbed renders (fast; no generator runs).

The live check renders the tree in ~5 minutes and its mutations prove it on two real nodes;
these pin the decision table itself, so a refactor that quietly turns "every sibling" into
"any sibling" -- the reading that would certify 8 recorded substitutions -- fails here first.
"""

from __future__ import annotations

from collections import defaultdict

import pytest

from backend.app.practice_gen.validation import judgment_packets as JP
from backend.app.practice_gen.validation import validate_exhibit as VE


def _install(monkeypatch, candidates, render, direct=None):
    """candidates: [(axis, value)]; render(profile, seed) -> sample dict or raise."""
    monkeypatch.setattr(JP, "_variant_coverage_candidates", lambda node_id: list(candidates))
    monkeypatch.setattr(JP, "_render_sample",
                        lambda node_id, seed, profile=None, include_private_variant_evidence=False:
                        render(profile, seed))
    monkeypatch.setattr(VE, "_direct_path_records",
                        lambda node_id, axis, value: (direct, []))


def _sample(text, evidence=None):
    return {"question_text": text, "correct_answer": 1,
            "_provider_variant_evidence": evidence or {}}


def _run():
    stats = defaultdict(int)
    return VE.exhibit_findings("mat_test_lc", stats), stats


def test_recorded_value_is_exhibited(monkeypatch):
    _install(monkeypatch, [("mode", "a"), ("mode", "b")],
             lambda prof, seed: _sample("same", {"mode": (prof or {}).get("mode")}))
    findings, stats = _run()
    assert findings == [] and stats["exhibited_recorded"] == 2


def test_unrecorded_value_that_changes_the_render_is_exhibited(monkeypatch):
    _install(monkeypatch, [("mode", "a"), ("mode", "b")],
             lambda prof, seed: _sample(f"item {(prof or {}).get('mode')}"))
    findings, stats = _run()
    assert findings == [] and stats["exhibited_rendered"] == 2


def test_distinct_from_one_sibling_is_not_enough(monkeypatch):
    """'b' and 'c' alias; 'a' differs from both. EVERY sibling, so b and c are findings."""
    text = {"a": "A", "b": "BC", "c": "BC"}
    _install(monkeypatch, [("mode", "a"), ("mode", "b"), ("mode", "c")],
             lambda prof, seed: _sample(text[(prof or {}).get("mode")]))
    findings, _ = _run()
    assert len(findings) == 2
    assert all("[class D]" in f for f in findings)
    assert any("mode='b'" in f and "['c']" in f for f in findings)


def test_substitution_is_class_b(monkeypatch):
    _install(monkeypatch, [("shape_set", "x"), ("shape_set", "y")],
             lambda prof, seed: _sample("same", {"shape_set": "x"}))
    findings, _ = _run()
    assert len(findings) == 1
    assert "shape_set='y'" in findings[0] and "[class B]" in findings[0]
    assert "recorded shape_set='x'" in findings[0]


def test_single_value_equal_to_default_is_class_e(monkeypatch):
    _install(monkeypatch, [("scale_type", "no_scale")], lambda prof, seed: _sample("same"))
    findings, _ = _run()
    assert len(findings) == 1 and "[class E]" in findings[0]


def test_single_value_that_changes_the_default_is_exhibited(monkeypatch):
    _install(monkeypatch, [("scale_type", "no_scale")],
             lambda prof, seed: _sample("asked" if prof else "default"))
    findings, stats = _run()
    assert findings == [] and stats["exhibited_rendered"] == 1


def test_direct_path_record_is_class_a(monkeypatch):
    _install(monkeypatch, [("task_type", "m"), ("task_type", "n")],
             lambda prof, seed: _sample("same"), direct=VE.SEEDS[0])
    findings, _ = _run()
    assert len(findings) == 2 and all("[class A]" in f for f in findings)


def test_every_seed_raising_is_class_r_and_names_the_error(monkeypatch):
    def render(prof, seed):
        raise ValueError("boundary violation")
    _install(monkeypatch, [("mode", "a")], render)
    findings, _ = _run()
    assert len(findings) == 1 and "[class R]" in findings[0]
    assert "boundary violation" in findings[0]


def test_every_finding_names_node_value_and_a_reproducible_seed(monkeypatch):
    _install(monkeypatch, [("mode", "a"), ("mode", "b")], lambda prof, seed: _sample("same"))
    findings, _ = _run()
    for f in findings:
        assert f.startswith("mat_test_lc: declared variant mode=")
        assert f"_render_sample('mat_test_lc', {VE.SEEDS[0]}," in f
        assert "Owed:" in f


@pytest.mark.parametrize("report_only,expected", [(True, True), (False, False)])
def test_report_only_prints_but_does_not_fail(monkeypatch, capsys, report_only, expected):
    monkeypatch.setattr(VE, "collect_findings", lambda node_ids=None: (
        {"variant_not_exhibited_2L": ["mat_x: declared variant ..."],
         "attester_packet_refused_2L": []}, {"candidates": 1}))
    assert VE.validate_all(report_only=report_only) is expected
    out = capsys.readouterr().out
    assert ("REPORT variant_not_exhibited_2L" in out) is report_only
    assert ("FAIL variant_not_exhibited_2L" in out) is (not report_only)
