"""
The v1 review corpus is preserved as a queue, and never as evidence.

`validate_judgment` requires `schema_version == 2`; all 151 filed reviews are v1, so all
151 were rejected as unadjudicable in one step on 2026-09-15. The plan required the
reconciliation to ship with the enforcement ("lossless filing path", step 1; "cut over
without losing findings", step 5; "all legacy unresolved findings reconcile without
omissions", M1 acceptance). It did not, so the whole earned corpus stopped being visible
as work.

These tests hold the two halves of the fix apart, because the danger runs in both
directions: the queue must lose NOTHING, and it must certify NOTHING.
"""

from __future__ import annotations

import json

import pytest

from backend.app.practice_gen.validation.validate_judgment import REVIEW_SCHEMA_VERSION
from tests import legacy_review_queue as lrq


@pytest.fixture(scope="module")
def queue():
    return lrq.build_queue()


# ── it loses nothing ──────────────────────────────────────────────────────────

def test_every_legacy_review_on_disk_becomes_a_queue_entry(queue):
    """The whole point: no file may be silently skipped."""
    on_disk = {
        json.loads(p.read_text(encoding="utf-8")).get("node_id") or p.stem
        for p in lrq._legacy_review_paths()
        if json.loads(p.read_text(encoding="utf-8")).get("schema_version")
        != REVIEW_SCHEMA_VERSION
    }
    assert {n["node_id"] for n in queue["nodes"]} == on_disk
    assert queue["counts"]["legacy_nodes"] == len(on_disk)


def test_every_entry_keeps_its_verdict_and_its_rationale_verbatim(queue):
    """A summarised rationale is a lost rationale."""
    for entry in queue["nodes"]:
        source = json.loads(
            (lrq.REPO_ROOT / entry["source_path"]).read_text(encoding="utf-8")
        )
        for facet, body in entry["facets"].items():
            assert body["verdict"] == source["findings"][facet]["verdict"]
            assert body["rationale"] == source["findings"][facet]["rationale"]


def test_the_non_pass_queue_is_carried_not_flattened(queue):
    """
    The unresolved queue is the reason this file exists. If it reported only overall
    verdicts, the per-facet detail that says WHAT to look at would be gone.
    """
    assert queue["counts"]["nodes_with_a_non_pass_facet"] > 0
    assert queue["counts"]["non_pass_by_facet"], "per-facet counts must survive"
    for entry in queue["nodes"]:
        expected = [f for f, b in entry["facets"].items() if b["verdict"] != "PASS"]
        assert sorted(entry["non_pass_facets"]) == sorted(expected)


def test_both_shapes_of_the_v1_overall_field_are_read():
    """v1 wrote `overall` as a bare string AND as a dict; both are live on disk."""
    assert lrq._overall_verdict({"overall": "CONCERN"}) == "CONCERN"
    assert lrq._overall_verdict({"overall": {"verdict": "FAIL"}}) == "FAIL"
    # An unrecognised third shape stays visible as a hole rather than being guessed.
    assert lrq._overall_verdict({"overall": 7}) is None
    assert lrq._overall_verdict({}) is None


def test_an_unparseable_review_is_loud_rather_than_dropped(tmp_path, monkeypatch):
    """Silently omitting a corrupt review is the exact loss this module prevents."""
    bad = tmp_path / "mat_g1_na_q1_0.json"
    bad.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(lrq, "_legacy_review_paths", lambda: [bad])
    with pytest.raises(ValueError, match="not valid JSON"):
        lrq.build_queue()


def test_a_missing_v1_facet_is_recorded_as_a_hole(tmp_path, monkeypatch):
    bad = tmp_path / "mat_g1_na_q1_0.json"
    bad.write_text(json.dumps({
        "node_id": "mat_g1_na_q1_0", "overall": "CONCERN",
        "findings": {"competency_fulfillment": {"verdict": "FAIL", "rationale": "r"}},
    }), encoding="utf-8")
    monkeypatch.setattr(lrq, "_legacy_review_paths", lambda: [bad])
    entry = lrq.build_queue()["nodes"][0]
    assert set(entry["facets_missing_from_the_v1_record"]) == set(lrq.V1_FACETS) - {
        "competency_fulfillment"
    }


# ── it certifies nothing ──────────────────────────────────────────────────────

def test_the_queue_declares_itself_non_adjudicable_at_every_level(queue):
    """
    Marked once at the top is not enough: a single entry copied out of this file must
    still read as non-evidence.
    """
    assert queue["adjudicable"] is False
    assert queue["why_not_adjudicable"]
    for entry in queue["nodes"]:
        assert entry["adjudicable"] is False


def test_no_queue_entry_claims_the_current_schema(queue):
    """If an entry ever declared v2, it would be readable as filed evidence."""
    for entry in queue["nodes"]:
        assert entry["declared_schema_version"] != REVIEW_SCHEMA_VERSION


def test_a_review_already_at_the_current_schema_is_excluded(tmp_path, monkeypatch):
    """The queue is for superseded records; current evidence does not belong in it."""
    good = tmp_path / "mat_g1_na_q1_0.json"
    good.write_text(json.dumps({
        "node_id": "mat_g1_na_q1_0", "schema_version": REVIEW_SCHEMA_VERSION,
        "findings": {}, "overall": "PASS",
    }), encoding="utf-8")
    monkeypatch.setattr(lrq, "_legacy_review_paths", lambda: [good])
    built = lrq.build_queue()
    assert built["nodes"] == []
    assert built["counts"]["already_current_and_excluded"] == 1


def test_the_queue_states_the_work_still_owed(queue):
    """A queue that does not say what it costs gets read as a resolution."""
    assert str(queue["counts"]["legacy_nodes"]) in queue["required_work"]
    assert "blind" in queue["required_work"]


def test_the_validator_still_rejects_every_legacy_review_and_points_at_the_queue():
    """
    The enforcement must NOT soften. A v1 review is still unadjudicable; the message
    simply stops implying the prior verdict was thrown away.
    """
    from backend.app.practice_gen.validation.validate_judgment import _validate_v2_schema

    errs = _validate_v2_schema("mat_g1_na_q1_0", lrq.REPO_ROOT / "x.json",
                               {"schema_version": None})
    assert len(errs) == 1
    assert "unadjudicable" in errs[0]
    assert "legacy_review_queue.json" in errs[0]
    assert "re-review is owed" in errs[0]


def test_the_written_artifact_matches_a_fresh_build(queue):
    """
    The committed artifact must not drift from the corpus it describes. If this fails,
    re-run `tests/legacy_review_queue.py --write`.
    """
    if not lrq.QUEUE_PATH.exists():
        pytest.skip("artifact not written yet")
        return
    written = json.loads(lrq.QUEUE_PATH.read_text(encoding="utf-8"))
    assert written["source_corpus_sha256"] == queue["source_corpus_sha256"]
    assert written["counts"] == queue["counts"]
