"""
The H-row ledger's schema gate, proved in both directions.

`tests/hardening_status.py` is the check that a hardening blocker cannot quietly lose its
evidence. A gate nobody has watched fail is not known to work (Scaling Mandate 1), and this
one is not reachable by the mutation harness -- it is not registered in `run_all`, because
it tracks PLAN progress rather than pipeline behaviour. So its directions are planted here
instead, against in-memory documents rather than the live ledger.

Every test names the specific way the ledger could lie if the check were absent.
"""

from __future__ import annotations

import copy

import pytest

from tests import hardening_status as hs


def _row(**over):
    row = {
        "id": "H-99", "status": "open", "owner": "unassigned",
        "affected_assertions": [], "baseline_evidence": "measured",
        "acceptance_checks": ["something"], "proof_artifacts": [],
        "closing_revision": None, "updated_at": "2026-09-12T00:00:00+08:00",
    }
    row.update(over)
    return row


def _doc(*rows):
    return {"schema_version": hs.SCHEMA_VERSION, "rows": list(rows)}


def test_the_live_ledger_is_valid():
    """The real file on disk holds. If this fails, the ledger is broken, not the test."""
    assert hs.validate(hs.load()) == []


def test_the_live_ledger_has_a_row_per_blocker():
    ids = {r["id"] for r in hs.load()["rows"]}
    assert ids == {f"H-0{n}" for n in range(1, 10)}


def test_valid_document_produces_no_errors():
    assert hs.validate(_doc(_row())) == []


@pytest.mark.parametrize("field", hs.REQUIRED_FIELDS)
def test_a_missing_required_field_is_caught(field):
    row = _row()
    del row[field]
    errors = hs.validate(_doc(row))
    assert any(repr(field) in e and "missing" in e for e in errors), errors


def test_closed_without_proof_artifacts_is_refused():
    """The whole point: a blocker may not be marked closed with no evidence."""
    row = _row(status="closed", proof_artifacts=[], closing_revision="HEAD")
    errors = hs.validate(_doc(row))
    assert any("proof_artifacts" in e and "not closed" in e for e in errors), errors


def test_closed_without_a_closing_revision_is_refused():
    row = _row(status="closed", proof_artifacts=["docs"], closing_revision=None)
    errors = hs.validate(_doc(row))
    assert any("closing_revision" in e for e in errors), errors


def test_out_of_scope_still_needs_the_deciding_commit():
    row = _row(status="out_of_scope", closing_revision=None)
    errors = hs.validate(_doc(row))
    assert any("out_of_scope" in e and "closing_revision" in e for e in errors), errors


def test_a_closing_revision_that_is_not_a_commit_is_caught():
    row = _row(status="closed", proof_artifacts=["docs"],
               closing_revision="0000000000000000000000000000000000000000")
    errors = hs.validate(_doc(row))
    assert any("not a commit" in e for e in errors), errors


def test_a_proof_artifact_that_does_not_exist_is_caught():
    row = _row(status="closed", proof_artifacts=["validation_reports/no_such_thing"],
               closing_revision="HEAD")
    errors = hs.validate(_doc(row))
    assert any("does not exist on disk" in e for e in errors), errors


def test_an_open_row_may_not_keep_a_closing_revision():
    """Closed-then-reopened must clear its provenance, or the row reads as both."""
    row = _row(status="open", closing_revision="HEAD")
    errors = hs.validate(_doc(row))
    assert any("Clear it or close the row" in e for e in errors), errors


def test_an_unknown_status_is_caught():
    errors = hs.validate(_doc(_row(status="mostly_done")))
    assert any("is not one of" in e for e in errors), errors


def test_duplicate_ids_are_caught():
    errors = hs.validate(_doc(_row(id="H-01"), _row(id="H-01")))
    assert any("duplicate id" in e for e in errors), errors


def test_a_wrong_schema_version_is_caught():
    doc = _doc(_row())
    doc["schema_version"] = 99
    errors = hs.validate(doc)
    assert any("schema_version" in e for e in errors), errors


def test_rows_missing_entirely_is_caught():
    errors = hs.validate({"schema_version": hs.SCHEMA_VERSION})
    assert any("`rows` is missing" in e for e in errors), errors
