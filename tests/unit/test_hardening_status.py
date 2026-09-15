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
from datetime import datetime, timedelta, timezone

import pytest

from tests import hardening_status as hs


def _row(**over):
    # `updated_at` defaults to NOW, not a fixed date, because a fixture standing in for a
    # row someone is holding has to be a row someone touched: `STALE_LOCK_HOURS` reads this
    # field to tell live work from an abandoned session. Tests about staleness pass an old
    # timestamp explicitly.
    row = {
        "id": "H-99", "status": "open", "owner": "unassigned",
        "affected_assertions": [], "baseline_evidence": "measured",
        "acceptance_checks": ["something"], "proof_artifacts": [],
        "closing_revision": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
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


# ─── the work-lock directions ─────────────────────────────────────────────────
# `owner` is a lock, not an accountability field (see hardening_status.UNCLAIMED).
# These four are what make it load bearing: without them the column is decoration.


def test_in_progress_may_not_be_unclaimed():
    """The abandoned-session case: the row says in flight, the lock says nobody has it."""
    errors = hs.validate(_doc(_row(status="in_progress", owner=hs.UNCLAIMED)))
    assert any("in_progress" in e and hs.UNCLAIMED in e for e in errors), errors


def test_a_closed_row_may_not_still_be_held():
    """Otherwise the next session reads a finished blocker as someone's live work."""
    row = _row(status="closed", owner="session-x",
               proof_artifacts=["docs"], closing_revision="HEAD")
    errors = hs.validate(_doc(row))
    assert any("still" in e and "Release the lock" in e for e in errors), errors


def test_an_empty_owner_is_caught():
    errors = hs.validate(_doc(_row(owner="")))
    assert any("non-empty string" in e for e in errors), errors


def test_a_held_in_progress_row_and_a_released_closed_row_are_both_valid():
    """The two shapes the lock is FOR must not be flagged."""
    held = _row(id="H-98", status="in_progress", owner="session-x")
    released = _row(id="H-97", status="closed", owner="released @ HEAD",
                    proof_artifacts=["docs"], closing_revision="HEAD")
    assert hs.validate(_doc(held, released)) == []


def test_the_live_ledger_locks_are_consistent():
    """Every row on disk obeys the lock rules, not just the schema."""
    rows = hs.load()["rows"]
    for r in rows:
        if r["status"] == "in_progress":
            assert r["owner"] != hs.UNCLAIMED, r["id"]
        if r["status"] in ("closed", "out_of_scope"):
            assert r["owner"] == hs.UNCLAIMED or r["owner"].startswith("released @ "), r["id"]


# ─── the three directions added 2026-09-16 ────────────────────────────────────
# Measured on the tree at f8597c0f: the ledger PASSED the schema and both original
# lock rules while H-07 sat `in_progress` under H-08's session identifier with its
# own measurement_status reading "unmeasured", and H-08 sat `open`/`unclaimed` with
# `proof_artifacts: []` beside the newest artifact in its own directory. Two legal
# rows, pointing the next session at exactly the wrong one each.


def test_a_lock_naming_another_row_is_caught():
    """The H-07 defect: the H-08 worker claimed H-07 and never released it."""
    row = _row(id="H-07", status="in_progress", owner="codex-20260914-h08-static-render")
    errors = hs.validate(_doc(row))
    assert any("names H-08, not H-07" in e for e in errors), errors


def test_a_lock_naming_its_own_row_is_accepted():
    """The positive control -- the convention in use must not be flagged."""
    row = _row(id="H-04", status="in_progress", owner="codex-20260912-h04-executor")
    assert hs.validate(_doc(row)) == []


def test_a_session_identifier_with_no_row_token_is_accepted():
    """The check must not require the convention, only that it be self-consistent."""
    row = _row(id="H-04", status="in_progress", owner="some-session-42")
    assert hs.validate(_doc(row)) == []


def test_a_lock_held_past_the_staleness_window_is_caught():
    """An abandoned session: in flight, held, and untouched for days."""
    old = (datetime.now(timezone.utc) - timedelta(hours=hs.STALE_LOCK_HOURS + 60)).isoformat()
    row = _row(status="in_progress", owner="session-x", updated_at=old)
    errors = hs.validate(_doc(row))
    assert any("has held it for" in e and "released" in e for e in errors), errors


def test_a_lock_inside_the_staleness_window_is_accepted():
    recent = (datetime.now(timezone.utc) - timedelta(hours=hs.STALE_LOCK_HOURS - 1)).isoformat()
    row = _row(status="in_progress", owner="session-x", updated_at=recent)
    assert hs.validate(_doc(row)) == []


def test_an_unparseable_timestamp_on_a_held_row_is_caught():
    """A lock whose age cannot be measured is a lock that cannot be told from abandoned."""
    row = _row(status="in_progress", owner="session-x", updated_at="last tuesday")
    errors = hs.validate(_doc(row))
    assert any("not a parseable timestamp" in e for e in errors), errors


def test_an_artifact_no_row_claims_is_caught():
    """The H-08 direction: rows->disk was checked, disk->rows was not."""
    errors = hs._unclaimed_artifacts([_row(proof_artifacts=[])])
    assert any("frontend_static_render.json" in e for e in errors), errors
    assert all("no H-row lists it" in e for e in errors), errors


def test_the_ledger_s_own_bookkeeping_is_not_demanded_as_evidence():
    """The ledger and the prose handoff are nobody's proof artifacts."""
    errors = hs._unclaimed_artifacts([_row(proof_artifacts=[])])
    joined = " ".join(errors)
    assert "hardening_status.json" not in joined
    assert "HANDOFF_PROMPT.md" not in joined


def test_the_live_ledger_claims_every_artifact_on_disk():
    """The real reconciliation, which is what `main()` runs."""
    assert hs._unclaimed_artifacts(hs.load()["rows"]) == []
