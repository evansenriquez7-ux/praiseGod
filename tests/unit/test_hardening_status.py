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
    """
    WIDENED TO TWO DIGITS 2026-09-21 (owner ruling 2). This assertion used to read
    `assert ids == {f"H-0{n}" for n in range(1, 10)}`, which could not express `H-10` --
    H-08's intro-surface remainder had been waiting on that literal since 2026-09-18.

    What the pin was for is kept: ids well formed, unique, contiguous, and none lost. What
    it is not allowed to keep is the growth ban, so the count is a FLOOR (the nine blockers
    recorded up to 2026-09-20) rather than an equality -- the same choice
    `operator_doc_covers_registry` makes and for the same reason. A row is added by
    justifying a blocker, never by editing an arithmetic literal here (Mandate 4).
    """
    rows = hs.load()["rows"]
    ids = {r["id"] for r in rows}
    assert len(ids) == len(rows), "duplicate row id on disk"
    assert all(hs._ROW_ID.match(i) for i in ids), sorted(ids)
    assert hs._row_id_sequence(rows) == []
    assert len(ids) >= 9, f"a recorded blocker has been dropped from the ledger: {sorted(ids)}"


def test_a_two_digit_row_id_is_accepted():
    """The whole point of the widening: `H-10` must be expressible."""
    assert hs.validate(_doc(_row(id="H-10"))) == []


@pytest.mark.parametrize("bad", ["H-1", "H-100", "H-1O", "h-01", "H01", "HH-01", 10, None])
def test_a_malformed_row_id_is_caught(bad):
    """Every typo direction the old membership pin caught, kept without the growth ban."""
    errors = hs.validate(_doc(_row(id=bad)))
    assert any("is not of the form" in e for e in errors), (bad, errors)


def test_a_gap_in_the_row_ids_is_caught():
    """A row deleted from the middle reads as a blocker the ledger has lost."""
    rows = [_row(id="H-01"), _row(id="H-02"), _row(id="H-04")]
    errors = hs._row_id_sequence(rows)
    assert any("H-03" in e and "contiguous" in e for e in errors), errors


def test_a_row_numbered_past_the_end_is_caught():
    """`H-12` opened while H-10/H-11 were never written loses two rows, not gains one."""
    errors = hs._row_id_sequence([_row(id="H-01"), _row(id="H-12")])
    assert any("H-12" in e and "past the end" in e for e in errors), errors


def test_a_contiguous_run_including_two_digits_is_accepted():
    """The positive control for the widening, at the digit boundary."""
    rows = [_row(id="H-%02d" % n) for n in range(1, 12)]
    assert hs._row_id_sequence(rows) == []


def test_the_contiguity_rule_is_not_asserted_against_a_synthetic_document():
    """`validate()` judges a DOCUMENT, so a one-row `H-99` fixture is legal there. If this
    ever fails, contiguity has been moved into `validate()` and every fixture in this file
    is now asserting the shape of the live ledger instead of the rule under test."""
    assert hs.validate(_doc(_row(id="H-99"))) == []


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
    assert "GPT_HANDOFF_PROMPT.md" not in joined


def test_the_live_ledger_claims_every_artifact_on_disk():
    """The real reconciliation, which is what `main()` runs."""
    assert hs._unclaimed_artifacts(hs.load()["rows"]) == []


# ── The subdirectory hole, found 2026-09-16 after H-04's sweep ──────────────────────
# `iterdir()` + `is_file()` skipped every subdirectory, so the six release receipts --
# 2.59 hours of execution, the most expensive evidence in the plan directory -- were
# exempt from the disk->rows direction entirely. Measured before the fix: 6 on disk, 0
# reported.

def test_an_artifact_in_a_subdirectory_is_not_invisible():
    errors = hs._unclaimed_artifacts([_row(proof_artifacts=[])])
    assert any("obligation_release_shards/shard_000_of_006.json" in e for e in errors), (
        "a nested artifact must be reconciled like any other; this is the H-08 shape one "
        f"directory level down -- {errors}"
    )


def test_a_claimed_directory_claims_what_is_inside_it():
    """H-02 claims `validation_reports/mutation_proofs` as a directory, so a row must be
    able to claim a directory of receipts the same way rather than re-listing every file
    each time a shard count changes."""
    claimed = "validation_reports/phase2_hardening/obligation_release_shards"
    errors = hs._unclaimed_artifacts([_row(proof_artifacts=[claimed])])
    assert not any("obligation_release_shards" in e for e in errors), errors


def test_a_nested_file_does_not_inherit_a_top_level_exemption(tmp_path, monkeypatch):
    """Exemptions are keyed to the path relative to the artifact directory, not to a bare
    filename -- otherwise `sub/hardening_status.json` would exempt itself by name."""
    monkeypatch.setattr(hs, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(hs, "ARTIFACT_DIR", tmp_path / "artifacts")
    (tmp_path / "artifacts" / "sub").mkdir(parents=True)
    (tmp_path / "artifacts" / "hardening_status.json").write_text("{}")
    (tmp_path / "artifacts" / "sub" / "hardening_status.json").write_text("{}")

    errors = hs._unclaimed_artifacts([_row(proof_artifacts=[])])
    assert len(errors) == 1, errors
    assert "sub/hardening_status.json" in errors[0]
