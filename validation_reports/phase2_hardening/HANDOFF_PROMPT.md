# Handoff — continue the Phase 2 hardening plan

**Rewritten 2026-09-16, current as of `839754b8`. This file is deliberately a POINTER, not a summary.**

Earlier versions of this file duplicated the plan's status and then drifted from it: on
2026-09-15 it described a 105-proof corpus, a green Phase 1 snapshot, and a red interest
path, while the tree had 145 mutations, a red Phase 1, and a green interest path. Two
sources of truth is how a session inherits confident wrong numbers, so the status lives in
exactly one place now.

## Read this, in this order

1. **`AGENTS.md` / `CLAUDE.md`** — the Scaling Mandate, the Engineering Protocols and the
   Definition of Done are binding. Verification is execution; a prediction phrased as a
   confirmation is a lie.
2. **`docs/phase2_hardening_completion_plan.md`, the `START HERE — handoff` section at the
   end.** That section is the live handoff: measured state, the four red stages and who owns
   each, the two mutation clusters that cannot currently be proven, the recommended order of
   work, and eight measured traps. Everything you need to pick up work is there.
3. The middle of that plan for the *design* of whichever step you are implementing. Read it
   for design, never for status — the status sections are dated and the handoff section wins.
4. **`validation_reports/HARDENING_EVIDENCE.md`**, last entry, for how the current numbers
   were obtained and which commands produced them.

## The two things worth saying twice

**The Definition of Done command needs no prefix.** Decided and implemented 2026-09-16:
`run_all` pins the database URL empty itself and prints what it overrode, because `.env`
carries a live Neon URL and the verdict used to depend on whether you remembered.

```sh
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
```

**That is not hermeticity, and the handoff says so.** The socket guard runs in §10 alone;
building a Phase-1-wide hermeticity gate is owed work with a clean baseline available today.

**The Definition of Done is NOT met, and no artifact in this repository claims it is.** Four
stages are red: 1,158 Phase 2 review findings, 218 attestation findings, H-04's unrun
2.555h release sweep, and the two mutation clusters. Every red is named and none is
warning-only. Do not report a green subset as completion.

## Claim your row before you start

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
#  -> PASS hardening_status: 9 H-row(s) valid — 2 closed, 6 open, 1 out_of_scope
```

`owner` is a work-lock. Claim the row, release it on commit, and if your session identifier
embeds an H-row token make sure it is *your own* row — that check exists because a worker
claimed H-07 while doing H-08, which left the untouched blocker reading as live work and the
nearly-finished one reading as unstarted.
