"""
`run_all` pins DATABASE_URL before anything can capture it, and says that it did.

WHY THIS FILE EXISTS
--------------------
`.env` in this repo carries a live Neon Postgres URL. `backend/app/database.py` calls
`load_dotenv()` and then captures `os.getenv("DATABASE_URL")` into a MODULE-LEVEL constant
at import time; `load_dotenv()` does not override a key already present in `os.environ`.
So a pin is only effective before `backend.app.database` is first imported.

WHAT THESE TESTS DO AND DO NOT GUARD
------------------------------------
They assert the OUTCOME -- `backend.app.database.DATABASE_URL == ""` after importing
`run_all` -- not where the pin sits in the file. That distinction is measured, not assumed:
no module in `run_all`'s validator import block imports `backend.app.database` at import
time (they take it lazily inside functions), so moving the pin below that block does not
currently change the outcome and these tests correctly do NOT fail on it. Verified by
planting exactly that edit; all six still passed.

What they DO catch is the combination that would actually hurt: a module-level
`backend.app.database` import appearing in the validator block while the pin sits beneath
it. Asserting the outcome rather than the line number is what makes them survive a
refactor, and it is the honest thing to claim -- an earlier draft of this docstring said
these tests guarded the placement, and that was false.

Measured before the pin, on identical bytes (2026-09-16):
`tests/unit/test_supervisor_queue.py::test_queue_counts_all_three_bands` FAILED in 15.89s
with the variable unset and PASSED in 153.15s with it empty, because the three-band probe
reached the real database. A gate whose answer depends on an ambient variable is not a gate
(Protocol 6), and CLAUDE.md's Definition of Done names `run_all` with no prefix -- so the
documented command was not the command H-01 was proved with.

Each test runs a FRESH interpreter. `backend.app.database` is almost certainly already
imported in the pytest process, so asserting against this process would prove nothing about
import order.

WHAT THIS DOES NOT CLAIM (Mandate 6)
------------------------------------
That Phase 1 is hermetic. The pin removes the operator's ability to change the verdict by
forgetting a prefix; it installs no socket guard. `hermetic_database()` is used in exactly
one place (`validate_grade`) and `grading_hermetic_10` is scoped to "the graded path", so
thirteen Phase 1 stages still have no assertion covering outbound connections. That gate is
owed work, named here, in the §10 contract row, and in the plan's START HERE handoff.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _fresh(code: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run `code` in a fresh interpreter rooted at the repo, with PYTHONPATH set."""
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env.pop("DATABASE_URL", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, "-c", code], cwd=REPO_ROOT,
                          capture_output=True, text=True, env=env)


def test_env_carries_a_real_url_so_this_pin_is_load_bearing():
    """
    The control. If `.env` stopped configuring a database, these tests would pass for the
    wrong reason and the pin would look unnecessary.
    """
    proc = _fresh(
        "import backend.app.database as db; "
        "print('CONFIGURED' if db.DATABASE_URL else 'EMPTY')"
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "CONFIGURED", (
        "backend.app.database resolved no DATABASE_URL on its own, so this repo no longer "
        "reproduces the condition the pin exists for. Re-read the pin's comment before "
        "deleting it -- it may now be dead, or .env may simply be absent on this machine."
    )


def test_importing_run_all_leaves_database_url_empty():
    """The pin's whole job, asserted where it actually lands: the module constant."""
    proc = _fresh(
        "import backend.app.practice_gen.validation.run_all as ra; "
        "import backend.app.database as db; "
        "print(repr(db.DATABASE_URL))"
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "''", (
        f"backend.app.database.DATABASE_URL is {proc.stdout.strip()} after importing "
        f"run_all. The pin must execute BEFORE the first import that reaches "
        f"backend.app.database -- check it has not been moved below run_all's import block."
    )


def test_the_graded_path_cannot_open_a_remote_engine_after_the_pin():
    """The consequence that matters: `get_engine()` refuses instead of dialling out."""
    proc = _fresh(
        "import backend.app.practice_gen.validation.run_all as ra; "
        "import backend.app.database as db\n"
        "try:\n"
        "    db.get_engine(); print('CONNECTED')\n"
        "except ValueError as e:\n"
        "    print('REFUSED')\n"
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "REFUSED"


def test_an_operator_supplied_url_is_overridden_not_honoured():
    """
    A deliberately set DATABASE_URL must NOT win. That is the point: the harness's verdict
    may not depend on the caller's environment.
    """
    proc = _fresh(
        "import backend.app.practice_gen.validation.run_all as ra; "
        "import backend.app.database as db; "
        "print(repr(db.DATABASE_URL))",
        env_extra={"DATABASE_URL": "postgresql://someone@example.invalid/db"},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "''"


def test_the_override_is_announced_rather_than_silent():
    """
    Protocol 3: no silent defaults. Overriding a variable the operator set must say so, or
    the next person debugging a connection error cannot tell the harness took the wheel.
    """
    proc = _fresh(
        "import backend.app.practice_gen.validation.run_all as ra; "
        "ra._print_hermeticity_banner()",
        env_extra={"DATABASE_URL": "postgresql://user:secret@db.example.invalid/prod"},
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "pinned to empty" in out
    assert "db.example.invalid" in out, "the banner should name what it replaced"
    assert "secret" not in out, (
        "the banner must not print the credential -- this output is pasted into evidence "
        "logs and commit messages"
    )


def test_the_banner_names_the_limitation_it_does_not_cover():
    """A pin described as hermeticity is how the next agent stops looking (Mandate 6)."""
    proc = _fresh(
        "import backend.app.practice_gen.validation.run_all as ra; "
        "ra._print_hermeticity_banner()"
    )
    assert proc.returncode == 0, proc.stderr
    assert "LIMITATION" in proc.stdout
    assert "§10" in proc.stdout or "hermetic_db" in proc.stdout
