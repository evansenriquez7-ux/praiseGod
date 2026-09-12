"""
The stage ledger (H-03): a crash must not delete the obligations it never reached.

Why these are unit tests and not only mutations
-----------------------------------------------
The behaviour under test lives in `run_all`, and a full `run_all --phase 1` takes about
eight minutes -- too slow for a mutation's baseline-plus-planted pair, and its Phase 2
baseline is red by construction so a plant there could not be scored (Mandate 2). These
drive the real `StageLedger` and the real `run_all` with every validator stubbed, so the
control flow being asserted is the production control flow, in milliseconds. The
mutations in `tests/mutation_harness.py` plant into that same code and are caught here
BY NAME.

MEASURED BEFORE THE FIX (2026-09-12, same probe, current tree at the time):

    run_all returned      : None        <- raised; no exit code at all
    run_all raised        : RuntimeError: planted stage crash
    stage after the crash reached? grade_§10   : False
    stage after the crash reached? coverage_§8 : False
    stage after the crash reached? census_§7   : False
    two-direction section printed : False
    final summary printed         : False
    any line naming the crash     : False

One stage raising took three further gates, the drift tripwire and the summary with it,
and printed nothing naming what had been lost.
"""

from __future__ import annotations

import pytest

from backend.app.practice_gen.validation import run_all as ra
from backend.app.practice_gen.validation.run_all import (
    StageLedger,
    StageResult,
    _print_stage_ledger,
)


# ─────────────────────────────────────────────────────────────────────────────
# The ledger itself
# ─────────────────────────────────────────────────────────────────────────────

class TestStageLedger:
    def test_a_scheduled_stage_starts_scheduled_not_passing(self):
        ledger = StageLedger()
        stage = ledger.schedule("s", 1, ("§9",), "t")
        assert stage.state == "scheduled"
        assert stage.ok is None, "an unrun stage has no verdict; it must not default to True"

    def test_a_completed_stage_records_completed(self):
        ledger = StageLedger()
        ledger.schedule("s", 1, (), "t")
        assert ledger.run("s", lambda: True) is True
        assert ledger.get("s").state == "completed"

    def test_a_failing_stage_records_failed_not_crashed(self):
        ledger = StageLedger()
        ledger.schedule("s", 1, (), "t")
        assert ledger.run("s", lambda: False) is False
        assert ledger.get("s").state == "failed"

    def test_a_raising_stage_is_contained_and_named(self, capsys):
        ledger = StageLedger()
        ledger.schedule("boom", 1, ("§9",), "t")

        def body():
            raise RuntimeError("planted")

        assert ledger.run("boom", body) is False, "a crash must not propagate"
        stage = ledger.get("boom")
        assert stage.state == "crashed"
        assert "RuntimeError: planted" in stage.detail
        out = capsys.readouterr().out
        assert "FAIL stage_crashed_boom" in out
        assert "§9" in out, "the refs the crash skipped must be named, not silently dropped"

    def test_even_a_baseexception_is_contained(self):
        """KeyboardInterrupt and SystemExit are how a stage most often dies in CI."""
        ledger = StageLedger()
        ledger.schedule("s", 1, (), "t")

        def body():
            raise SystemExit(2)

        assert ledger.run("s", body) is False
        assert ledger.get("s").state == "crashed"

    def test_duplicate_stage_names_are_refused(self):
        ledger = StageLedger()
        ledger.schedule("s", 1, (), "t")
        with pytest.raises(ValueError, match="scheduled twice"):
            ledger.schedule("s", 1, (), "t")

    def test_every_stage_is_timed(self):
        ledger = StageLedger()
        ledger.schedule("s", 1, (), "t")
        ledger.run("s", lambda: True)
        assert ledger.get("s").seconds >= 0.0

    def test_a_crashed_stage_is_still_timed(self):
        ledger = StageLedger()
        ledger.schedule("s", 1, (), "t")
        ledger.run("s", lambda: (_ for _ in ()).throw(RuntimeError("x")))
        assert ledger.get("s").seconds >= 0.0


# ─────────────────────────────────────────────────────────────────────────────
# The ledger report
# ─────────────────────────────────────────────────────────────────────────────

class TestLedgerReport:
    def test_a_clean_run_reports_no_failures(self, capsys):
        ledger = StageLedger()
        ledger.schedule("a", 1, (), "t")
        ledger.run("a", lambda: True)
        assert _print_stage_ledger(ledger, 1) == []
        assert "PASS stage_ledger_complete" in capsys.readouterr().out

    def test_a_failed_stage_is_not_a_ledger_failure(self):
        """It ran and reported. Its own FAIL line is the finding; this is not a second one."""
        ledger = StageLedger()
        ledger.schedule("a", 1, (), "t")
        ledger.run("a", lambda: False)
        assert _print_stage_ledger(ledger, 1) == []

    def test_a_crashed_stage_is_a_ledger_failure(self, capsys):
        ledger = StageLedger()
        ledger.schedule("a", 1, (), "t")
        ledger.run("a", lambda: (_ for _ in ()).throw(RuntimeError("x")))
        failures = _print_stage_ledger(ledger, 1)
        assert len(failures) == 1 and "CRASHED" in failures[0]
        assert "FAIL stage_ledger_complete" in capsys.readouterr().out

    def test_a_stage_that_never_ran_is_a_ledger_failure(self, capsys):
        """The unattempted-stage path: a fail-fast abort leaves later stages unchecked."""
        ledger = StageLedger()
        ledger.schedule("a", 1, (), "t")
        ledger.schedule("b", 1, ("§10",), "t")
        ledger.run("a", lambda: False)
        failures = _print_stage_ledger(ledger, 1)
        assert len(failures) == 1
        assert "never checked" in failures[0] and "§10" in failures[0]
        assert "NOT RUN" in capsys.readouterr().out

    def test_the_report_is_scoped_to_the_phase_being_run(self):
        ledger = StageLedger()
        ledger.schedule("p2", 2, ("§5",), "t")
        assert _print_stage_ledger(ledger, 1) == [], "a phase-2 stage is not owed in phase 1"
        assert len(_print_stage_ledger(ledger, 2)) == 1

    def test_phase_none_owes_every_stage(self):
        ledger = StageLedger()
        ledger.schedule("p1", 1, (), "t")
        ledger.schedule("p2", 2, (), "t")
        assert len(_print_stage_ledger(ledger, None)) == 2


# ─────────────────────────────────────────────────────────────────────────────
# End to end through the real run_all, with every validator stubbed
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def stubbed_harness(monkeypatch):
    """Neutralise every validator so only run_all's own control flow is under test."""
    monkeypatch.setattr(ra, "_run_unit_tests", lambda: True)
    monkeypatch.setattr(ra, "run_matrix_validation", lambda **kw: 0)
    monkeypatch.setattr(ra.validate_matrix, "LAST_EXECUTED_CHECKS",
                        {"§1A", "§1A-reach", "§1B", "§1C", "§1C-reverse", "§1C-coverage",
                         "§1D", "§1E", "§1F", "§1G", "§1I", "§4"})
    monkeypatch.setattr(ra.validate_matrix, "_EXECUTED_BY_NODE", {})
    monkeypatch.setattr(ra.validate_matrix, "applicability_failures", lambda *a, **k: [])
    monkeypatch.setattr(ra.validate_matrix, "coverage_regressions", lambda *a, **k: [])
    monkeypatch.setattr(ra.validate_dna, "validate_all_dnas", lambda: {})
    monkeypatch.setattr(ra.validate_dna, "run_all_feasibility_checks", lambda: {})
    monkeypatch.setattr(ra.validate_compat, "validate_all", lambda: True)
    monkeypatch.setattr(ra.validate_interest, "validate_all_interest_invariance", lambda: {})
    monkeypatch.setattr(ra.validate_vocab, "run_all_vocab_audits",
                        lambda **kw: {"n": {"pass_rate": 1.0, "violations": []}})
    monkeypatch.setattr(ra.validate_capability, "validate_capability_provision", lambda: [])
    monkeypatch.setattr(ra.validate_language, "validate_all", lambda: True)
    monkeypatch.setattr(ra.validate_options, "validate_all", lambda: True)
    monkeypatch.setattr(ra.validate_render, "validate_all", lambda: True)
    monkeypatch.setattr(ra.validate_grade, "validate_all", lambda: True)
    monkeypatch.setattr(ra.validate_coverage, "validate_all", lambda: True)
    monkeypatch.setattr(ra.validate_census, "validate_all", lambda: True)
    # Phase 2 too, so a `phase=None` run stays in the fast suite: the real judgment and
    # attestation stages read the agent-authored corpora and take tens of seconds.
    monkeypatch.setattr(ra.validate_judgment, "validate_judgment_reviews", lambda **kw: [])
    monkeypatch.setattr(ra.validate_judgment, "summarize_verdicts",
                        lambda: {"reviewed": 0, "PASS": 0, "CONCERN": 0, "FAIL": 0})
    monkeypatch.setattr(ra.validate_capability, "validate_capability_attestation", lambda: [])
    return monkeypatch


class TestCrashIsolationEndToEnd:
    def test_a_stubbed_phase_1_run_is_green(self, stubbed_harness, capsys):
        """The control: without this, a red result below would prove nothing."""
        assert ra.run_all(phase=1) == 0
        out = capsys.readouterr().out
        assert "PASS stage_ledger_complete" in out
        assert "PHASE 1 PASSED SUCCESSFULLY" in out

    def test_a_crash_does_not_stop_later_stages(self, stubbed_harness, capsys):
        def boom():
            raise RuntimeError("planted stage crash")

        stubbed_harness.setattr(ra.validate_render, "validate_all", boom)
        code = ra.run_all(phase=1)
        out = capsys.readouterr().out

        assert code == 1, "a crashed stage must produce an exit code, not an exception"
        assert "Grading Contract" in out, "§10 runs after the crash"
        assert "Assertion Coverage" in out, "§8 runs after the crash"
        assert "Suite Census" in out, "§7 runs after the crash"
        assert "Two-Direction Contract Verification" in out
        assert "CHECKS FAILED" in out, "the summary must still be printed"
        assert "FAIL stage_crashed_render_contract_9" in out
        assert "planted stage crash" in out

    def test_a_crash_cannot_delete_its_own_expected_refs(self, stubbed_harness, capsys):
        """
        The distinction the whole ledger exists for. A FAILED stage's refs leave the
        two-direction comparison, because it ran and reported. A CRASHED stage's refs
        must NOT, or the crash silently erases the obligations it skipped.
        """
        def boom():
            raise RuntimeError("planted stage crash")

        stubbed_harness.setattr(ra.validate_render, "validate_all", boom)
        ra.run_all(phase=1)
        out = capsys.readouterr().out
        assert "FAIL two_direction_contract_match" in out
        assert "§9" in out.split("Two-Direction")[1], (
            "§9 must be reported as registered-but-not-executed after its stage crashed"
        )

    def test_a_failed_stage_does_not_trip_the_drift_tripwire(self, stubbed_harness, capsys):
        """The other half: an honest failure is not also reported as drift."""
        stubbed_harness.setattr(ra.validate_render, "validate_all", lambda: False)
        code = ra.run_all(phase=1)
        out = capsys.readouterr().out
        assert code == 1
        assert "PASS two_direction_contract_match" in out
        assert "PASS stage_ledger_complete" in out, "a reported failure reached a verdict"

    def test_fail_fast_records_what_it_never_reached(self, stubbed_harness, capsys):
        stubbed_harness.setattr(ra.validate_compat, "validate_all", lambda: False)
        code = ra.run_all(fail_fast=True, phase=1)
        out = capsys.readouterr().out
        assert code == 1
        assert "FAIL stage_ledger_complete" in out
        assert "NOT RUN" in out
        assert "grading_contract_10" in out, (
            "an aborted run must say which obligations it never checked"
        )

    def test_every_scheduled_stage_appears_in_the_ledger(self, stubbed_harness, capsys):
        ra.run_all(phase=1)
        out = capsys.readouterr().out.split("--- Stage Ledger ---")[1]
        for name in ("unit_tests", "dna", "compatibility", "interest_invariance",
                     "vocabulary", "behavioural_matrix", "capability_phase1",
                     "count_noun_1J", "option_degeneracy_1K", "render_contract_9",
                     "grading_contract_10", "assertion_coverage_8", "census_7"):
            assert name in out, f"{name} is scheduled but absent from the ledger"

    def test_phase_2_stages_are_not_scheduled_in_a_phase_1_run(self, stubbed_harness, capsys):
        ra.run_all(phase=1)
        out = capsys.readouterr().out.split("--- Stage Ledger ---")[1]
        assert "judgment_reviews_5" not in out
        assert "capability_phase2" not in out


# ─────────────────────────────────────────────────────────────────────────────
# Two registries, one fact: the schedule and _manifest.CHECK_PHASE
# ─────────────────────────────────────────────────────────────────────────────

class TestStagePhaseMatchesManifest:
    """
    `CHECK_PHASE` decides which band a ref BELONGS to; the stage schedule decides which
    band actually RUNS it. Nothing compared them until 2026-09-12, so moving a ref in the
    manifest and forgetting the stage left `--phase 2` reporting it as never executed
    forever while `--phase 1` went on executing it.
    """

    def test_the_real_schedule_agrees_with_the_real_manifest(self, stubbed_harness, capsys):
        ra.run_all(phase=None)
        assert "PASS stage_phase_matches_manifest" in capsys.readouterr().out

    def test_a_ref_registered_to_the_other_band_is_caught(self, stubbed_harness, capsys, monkeypatch):
        flipped = dict(ra.CHECK_PHASE)
        flipped["§9"] = 2
        monkeypatch.setattr(ra, "CHECK_PHASE", flipped)
        code = ra.run_all(phase=1)
        out = capsys.readouterr().out
        assert code == 1
        assert "FAIL stage_phase_matches_manifest" in out
        assert "render_contract_9" in out and "§9" in out

    def test_a_ref_missing_from_the_manifest_is_caught(self, stubbed_harness, capsys, monkeypatch):
        stripped = {k: v for k, v in ra.CHECK_PHASE.items() if k != "§10"}
        monkeypatch.setattr(ra, "CHECK_PHASE", stripped)
        code = ra.run_all(phase=1)
        out = capsys.readouterr().out
        assert code == 1
        assert "FAIL stage_phase_matches_manifest" in out
        assert "no entry in" in out
