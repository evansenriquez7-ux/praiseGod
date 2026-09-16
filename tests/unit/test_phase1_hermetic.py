"""
`phase1_hermetic` (2026-09-16): every Phase 1 stage runs inside the socket guard.

Why these are unit tests and not only a live mutation
-----------------------------------------------------
The behaviour lives in `run_all.StageLedger.run`, and the live catcher would have to be
`run_all --phase 1`, whose baseline is RED today (`assertion_coverage_8` fails on the two
blocked mutation clusters). A plant scored against a red baseline is rejected, not proven
-- the same wall H-04's §6F cluster sits behind (Mandate 2). So these drive the REAL
`StageLedger` with stubbed stage bodies, exactly as `tests/unit/test_stage_ledger.py`
does for H-03, and `phase1_stage_escapes_the_network_guard` plants into that same code.

NAMED LIMIT: because the catcher is a unit test rather than a live `run_all`, these prove
the runner's guard placement, not that a REAL validator's outbound connection is caught.

WHAT THE BASELINE WAS, MEASURED 2026-09-16 on `55ceb221`
--------------------------------------------------------
`hermetic_database()` was called in exactly ONE place, `validate_grade` (§10), and
`grading_hermetic_10` scopes its claim to "the graded path". The other thirteen Phase 1
stages had no guard and no assertion covering outbound connections:

    $ grep -rn "hermetic_database" --include="*.py" backend/ tests/
      tests/hermetic_db.py        (the definition)
      backend/app/practice_gen/validation/validate_grade.py:291   with hermetic_database():

No network is touched by this module. The guard raises before any real connect, and the
recorder fixture stands in for `socket.socket.connect` so that even an ABSENT guard
cannot reach a host -- otherwise the phase-2 control below would dial out for real.
"""

from __future__ import annotations

import socket

import pytest

from backend.app.practice_gen.validation.run_all import StageLedger
from tests.hermetic_db import HermeticNetworkError, no_network

# Non-loopback, reserved, and never actually dialled: the guard raises first and the
# recorder catches the case where it does not.
ELSEWHERE = ("10.255.255.1", 9)


@pytest.fixture
def recorder(monkeypatch):
    """Stand in for the real connect, so an absent guard is visible but harmless."""
    seen = []

    def _fake_connect(self, address, *a, **kw):
        seen.append(address)
        return None

    monkeypatch.setattr(socket.socket, "connect", _fake_connect, raising=True)
    return seen


def _dial():
    socket.socket().connect(ELSEWHERE)
    return True


class TestPhase1StagesAreGuarded:
    def test_a_phase1_stage_reaching_the_network_is_named(self, recorder, capsys):
        ledger = StageLedger()
        ledger.schedule("s", 1, ("§9",), "t")
        assert ledger.run("s", _dial) is False
        out = capsys.readouterr().out
        assert "FAIL phase1_hermetic" in out, out
        assert recorder == [], "the guard let the connection through to the real socket"

    def test_the_violation_is_crashed_so_its_refs_stay_expected(self, recorder, capsys):
        # `failed` would discard the stage's refs from the two-direction comparison, which
        # is right for a stage that ran and said no, and wrong for one that never ran.
        ledger = StageLedger()
        ledger.schedule("s", 1, ("§9",), "t")
        ledger.run("s", _dial)
        capsys.readouterr()
        assert ledger.get("s").state == "crashed"
        assert ledger.get("s").ok is False

    def test_it_is_not_reported_as_a_generic_stage_crash(self, recorder, capsys):
        ledger = StageLedger()
        ledger.schedule("s", 1, (), "t")
        ledger.run("s", _dial)
        out = capsys.readouterr().out
        assert "stage_crashed_s" not in out, (
            "a Phase 1 gate reaching the network must be named as such, not folded into "
            f"the generic crash boundary: {out}"
        )


class TestTheControls:
    def test_a_clean_phase1_stage_still_completes(self, recorder, capsys):
        # Without this the suite could pass by guarding everything into failure.
        ledger = StageLedger()
        ledger.schedule("s", 1, (), "t")
        assert ledger.run("s", lambda: True) is True
        assert ledger.get("s").state == "completed"

    def test_loopback_is_allowed_through_the_guard(self, recorder, capsys):
        ledger = StageLedger()
        ledger.schedule("s", 1, (), "t")

        def _local():
            socket.socket().connect(("127.0.0.1", 9))
            return True

        assert ledger.run("s", _local) is True, "fastapi.testclient needs loopback"
        assert recorder == [("127.0.0.1", 9)]

    def test_the_guard_is_released_after_the_stage(self, recorder):
        ledger = StageLedger()
        ledger.schedule("s", 1, (), "t")
        ledger.run("s", _dial)
        # Outside the stage the process must be able to connect again, or the guard would
        # leak into everything run_all does after Phase 1.
        socket.socket().connect(ELSEWHERE)
        assert recorder == [ELSEWHERE]


class TestTheNamedLimitation:
    def test_phase2_stages_are_not_guarded(self, recorder, capsys):
        """The owed work named a PHASE 1 gate. §5 and §6F-§6H remain uncovered, and this
        pins that as a measured fact so nobody reads the gate as total."""
        ledger = StageLedger()
        ledger.schedule("s", 2, ("§5",), "t")
        assert ledger.run("s", _dial) is True
        assert recorder == [ELSEWHERE]
        assert "phase1_hermetic" not in capsys.readouterr().out

    def test_the_guard_does_not_reach_into_child_processes(self):
        """`unit_tests`/`census_7` use subprocess and `behavioural_matrix` uses a Pool;
        the guard patches THIS interpreter only. Recorded so the limitation is executable
        rather than only prose."""
        import multiprocessing

        with no_network():
            # A child process does not inherit the patch, which is precisely why the
            # limitation is named. It also must not be broken BY the guard.
            assert multiprocessing.Pool(1).map(abs, [-1]) == [1]
            with pytest.raises(HermeticNetworkError):
                socket.create_connection(ELSEWHERE, timeout=1)
