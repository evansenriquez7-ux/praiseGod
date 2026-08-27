"""
The supervisor's queue must count every band, and must never report an unmeasured
band as zero.

Why this file exists
--------------------
Until 2026-08-26 `hardening_supervisor.py` derived its RESUME/NOTHING_TO_DO verdict
from `validate_capability` alone. That number is stage 8 of eight. Stage 6 (the §1
behavioural matrix) and stage 7 (§5 judgment reviews) were absent from it, so the
verdict that decides "is there work?" could not see 575 stale reviews or a live §1C
`empty_execution_matrix` on mat_g3_na_q3_1 -- a node that renders no problems at all
and would still report PASS. 455 consecutive ticks optimised a number that did not
contain the defect, and the loop reported a 158-item queue while 735 findings stood.

Stage 6 costs ~30 minutes over 151 nodes, so the supervisor reads the report it leaves
behind instead of re-running it. That trade is only safe while the report's coverage
and freshness travel with the count. These tests plant each way the report can fail to
be current and assert the supervisor refuses to trust it -- because a cached zero that
outlives the content it describes is the same false green in a new place.
"""

from __future__ import annotations

import importlib.util
import json
import os
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
REPORT = REPO / "validation_reports" / "matrix_report.json"


def _supervisor():
    """Load the supervisor by path -- scripts/ is not an importable package."""
    spec = importlib.util.spec_from_file_location(
        "hardening_supervisor", REPO / "scripts" / "hardening_supervisor.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _full_clean_report() -> dict:
    from backend.app.practice_gen.registry import get_all_node_ids

    return {n: [] for n in get_all_node_ids()} | {"_executed_checks": {}}


@pytest.fixture
def restore_report():
    """Every test here rewrites the real matrix report; hand it back untouched."""
    original = REPORT.read_bytes() if REPORT.exists() else None
    original_mtime = REPORT.stat().st_mtime if REPORT.exists() else None
    yield
    if original is None:
        REPORT.unlink(missing_ok=True)
    else:
        REPORT.write_bytes(original)
        os.utime(REPORT, (original_mtime, original_mtime))


# --------------------------------------------------------------------------------
# The evidence-state guards. These use matrix_evidence() directly: it is pure, so the
# planted state is the only thing under test and each case costs milliseconds.
# --------------------------------------------------------------------------------

def test_partial_matrix_report_is_not_trusted(restore_report):
    """
    `validate_matrix --node X` overwrites the tree-wide report with a single node.

    A partial report must read as "unmeasured", never as a clean tree. Without this,
    one Class A tick verifying one node would erase 150 nodes of §1 evidence and the
    queue would report zero §1 findings the moment after.
    """
    sup = _supervisor()
    REPORT.write_text(
        json.dumps({"mat_g1_na_q1_0": [], "_executed_checks": {}}), encoding="utf-8"
    )

    m = sup.matrix_evidence()
    assert m["state"] == "PARTIAL", f"got {m['state']}"
    assert m["trusted"] is False, (
        "COVERAGE HOLE: a one-node matrix report was accepted as evidence about 151 nodes"
    )
    assert m["covered"] < m["total"]


def test_stale_matrix_report_is_not_trusted(restore_report):
    """A report older than the content it describes is evidence about content that changed."""
    sup = _supervisor()
    # Full coverage, so only freshness can disqualify it.
    REPORT.write_text(json.dumps(_full_clean_report()), encoding="utf-8")
    newest = sup._newest_pipeline_mtime()
    os.utime(REPORT, (newest - 3600, newest - 3600))

    m = sup.matrix_evidence()
    assert m["state"] == "STALE", f"got {m['state']}"
    assert m["trusted"] is False, (
        "FRESHNESS HOLE: a matrix report predating the generators it describes was "
        "accepted. Change a generator and the queue keeps reporting the old zero."
    )


def test_fresh_full_report_is_trusted(restore_report):
    """The positive control -- without it the guards above could pass by always failing."""
    sup = _supervisor()
    REPORT.write_text(json.dumps(_full_clean_report()), encoding="utf-8")
    now = time.time() + 5  # unambiguously newer than any pipeline file
    os.utime(REPORT, (now, now))

    m = sup.matrix_evidence()
    assert m["state"] == "FRESH", f"got {m['state']}"
    assert m["trusted"] is True
    assert m["covered"] == m["total"]


def test_missing_and_unreadable_reports_are_not_trusted(restore_report):
    """No report, and a corrupt report, must both refuse to answer -- loudly, not as zero."""
    sup = _supervisor()

    REPORT.unlink(missing_ok=True)
    m = sup.matrix_evidence()
    assert m["state"] == "MISSING"
    assert m["trusted"] is False

    REPORT.write_text("{not json at all", encoding="utf-8")
    m = sup.matrix_evidence()
    assert m["state"] == "UNREADABLE"
    assert m["trusted"] is False


def test_untrusted_band_contributes_zero_but_findings_stay_visible(restore_report):
    """
    An untrusted band must not add to the gate total -- and must not vanish either.

    Reporting its findings while excluding them from the total is the whole point: the
    operator sees "§1=2 (PARTIAL, NOT counted)" rather than a confident zero.
    """
    sup = _supervisor()
    REPORT.write_text(
        json.dumps({"mat_g1_na_q1_0": [{"check": "planted"}], "_executed_checks": {}}),
        encoding="utf-8",
    )
    m = sup.matrix_evidence()
    assert m["trusted"] is False
    assert m["findings"] == 1, "an untrusted band must still report what it saw"


# --------------------------------------------------------------------------------
# The integration test. ~27s: it evaluates the real capability contract and judgment
# reviews in a subprocess. It is the only place the actual gate arithmetic is proved,
# so it is deliberately NOT marked `slow` -- that marker is deselected by default
# (tests/pytest.ini addopts), and a gate that does not run does not gate. The marker is
# for the 15-40 minute process-pool tests; half a minute belongs in the fast suite.
# --------------------------------------------------------------------------------

def test_queue_counts_all_three_bands(restore_report):
    """The gate number must be the sum of every band it trusts -- not stage 8 alone."""
    sup = _supervisor()
    q = sup.queue_state()
    assert q is not None, "queue probe did not run; the contract may be unevaluatable"
    assert set(q) >= {"capability", "judgment", "matrix", "total"}

    counted_matrix = q["matrix"]["findings"] if q["matrix"]["trusted"] else 0
    assert q["total"] == q["capability"] + q["judgment"] + counted_matrix, (
        "BAND OMITTED: the gate total must include every band it trusts. This is the "
        "exact shape of the 2026-08-26 defect -- a total that silently dropped stages 6 "
        "and 7 and reported 158 while 735 findings were open."
    )
    # The regression that started it all: capability alone must not be the gate.
    if q["judgment"] or counted_matrix:
        assert q["total"] != q["capability"], (
            "the gate equals the capability count while other bands hold findings -- "
            "stages 6/7 are being ignored again"
        )


# --------------------------------------------------------------------------------
# STALLED (exit 30) — the loop is committing but not working.
#
# Not the NEEDS_HUMAN that was retired on 2026-08-23. That one was agent-declared and
# legitimised deferral. This is derived from committed history, so a tick can neither
# assert it nor suppress it: it fires only when the last STALL_COMMITS commits touched
# nothing but the ledger, the status file and the graph cache, while findings stand.
# --------------------------------------------------------------------------------

def test_bookkeeping_streak_detects_the_real_spin():
    """
    HEAD of this repo is the tail of the 2026-08-24 spin: 455 consecutive commits whose
    only content was a ledger entry. The detector must see it in real history, not in a
    fixture -- a synthetic-only test would not have caught the thing that happened.
    """
    sup = _supervisor()
    streak = sup.bookkeeping_only_streak()
    assert streak >= sup.STALL_COMMITS, (
        f"the detector saw a streak of {streak} where real history holds a run of "
        f"ledger-only commits; a spin this size must be detectable"
    )


def test_a_real_commit_breaks_the_streak(monkeypatch):
    """One commit with actual work in it resets the count — a spin must be *consecutive*."""
    sup = _supervisor()

    def fake_sh(*args):
        if "--format=%H" in args:
            return "aaa\nbbb\nccc\n"
        sha = args[-1]
        if sha == "bbb":  # a real unit of work
            return "backend/app/practice_gen/dna/na/place_value.py\n"
        return "local_only/scratch/hardening_ledger.md\n"

    monkeypatch.setattr(sup, "_sh", fake_sh)
    assert sup.bookkeeping_only_streak() == 1, (
        "the streak must stop at the first commit carrying real work, otherwise a loop "
        "that does one unit every twenty ticks would look permanently stalled"
    )


def test_graph_cache_and_archive_count_as_bookkeeping(monkeypatch):
    """
    graphify-out/ and the ledger archive are written as a side effect of reporting.
    A tick that rewrote only those did no more work than one that rewrote the ledger.
    """
    sup = _supervisor()

    def fake_sh(*args):
        if "--format=%H" in args:
            return "aaa\nbbb\n"
        return "graphify-out/graph.json\nlocal_only/scratch/ledger_archive/x.md\n"

    monkeypatch.setattr(sup, "_sh", fake_sh)
    assert sup.bookkeeping_only_streak() == 2
