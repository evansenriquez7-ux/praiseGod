"""
The validation harness package — and the one thing that must happen before any of it runs.

HERMETICITY: THE DATABASE URL IS PINNED EMPTY FOR EVERY ENTRY POINT
-------------------------------------------------------------------
`.env` in this repo carries a live Neon Postgres URL. `backend/app/database.py` calls
`load_dotenv()` and captures `os.getenv("DATABASE_URL")` into a MODULE-LEVEL constant at
import time, and `load_dotenv()` does not override a key already present in `os.environ`.
So a pin is only effective before `backend.app.database` is first imported.

WHY IT LIVES IN THE PACKAGE `__init__` AND NOT IN `run_all`
-----------------------------------------------------------
It was in `run_all` first, and that was not enough — measured, before it shipped. Every
mutation in `tests/mutation_harness.py` runs its own command as a subprocess, and those
commands invoke a validator DIRECTLY:

    python -m backend.app.practice_gen.validation.validate_capability

`run_all` is never imported on that path, so all 145 mutation subprocesses still resolved
the live Neon URL:

    $ python -c "import ...validation.validate_capability, backend.app.database as db; \\
                 print(repr(db.DATABASE_URL))"
      'postgresql://neondb_owner:npg_rkx1bqZNJ...'

Python imports every parent package before a submodule, so this file is the one place that
covers `run_all`, `python -m ...validate_X`, the mutation runner, and anything else that
reaches into the package. A pin that covers only the aggregate runner leaves the harness's
own verification layer environment-dependent, which is the more expensive half.

WHY PIN IT AT ALL
-----------------
Without it the harness's verdict depends on an ambient variable the operator has to
remember. Measured on identical bytes 2026-09-16:
`tests/unit/test_supervisor_queue.py::test_queue_counts_all_three_bands` FAILED in 15.89s
with the variable unset and PASSED in 153.15s with it empty, because the three-band probe
reached the real database. `AGENTS.md`'s Definition of Done names `run_all` with no prefix,
so the documented command was not the command `H-01`'s evidence was proved with. A gate
whose answer depends on the environment is not a gate (Protocol 6), and the fix belongs in
the harness rather than in an instruction a future session must remember.

NOT A SILENT DEFAULT (Protocol 3)
---------------------------------
`run_all._print_hermeticity_banner` prints what was overridden at the top of every run,
scheme and host only — never the credential, because that output is pasted into evidence
logs and commit messages. `_PINNED_DATABASE_URL` below preserves the prior value so the
banner can name it.

LIMITATION, NAMED (Scaling Mandate 6)
-------------------------------------
This pins a URL, which is CONFIGURATION, not enforcement. It does **not** make Phase 1
hermetic: it only removes the operator's ability to get a different answer by forgetting a
prefix. `tests/hermetic_db.hermetic_database()` — the throwaway SQLite plus the socket guard
that raises `HermeticNetworkError` by name — is called in exactly ONE place,
`validate_grade`, and `grading_hermetic_10` asserts "no outbound connection from **the
graded path**". The other thirteen Phase 1 stages have neither the guard nor any assertion
covering outbound connections, so a network dependency introduced anywhere outside §10 would
surface only as flaky redness.

OWED, with a clean baseline available today (Mandate 5 says that is when to build a gate):
install the guard around every Phase 1 stage, add a `phase1_hermetic` assertion, and prove
it with a mutation that plants an outbound connection in a NON-§10 stage. See
`docs/pgen_contract.md`'s §10 row and the `START HERE` handoff in
`docs/phase2_hardening_completion_plan.md`. Do not read this pin as having closed it.
"""

import os

# The prior value, kept so the banner can say what it replaced. Read before the override.
_PINNED_DATABASE_URL = os.environ.get("DATABASE_URL")
os.environ["DATABASE_URL"] = ""
