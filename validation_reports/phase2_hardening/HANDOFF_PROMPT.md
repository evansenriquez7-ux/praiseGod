# Handoff — continue the Phase 2 hardening plan

**Rewritten 2026-09-16, current as of `14d98739`. This file is deliberately a POINTER, not
a summary.**

Earlier versions duplicated the plan's status and then drifted from it: on 2026-09-15 this
file described a 105-proof corpus, a green Phase 1 snapshot and a red interest path, while
the tree had 145 mutations, a red Phase 1 and a green interest path. Two sources of truth is
how a session inherits confident wrong numbers, so the status lives in exactly one place.

## Read this, in this order

1. **`AGENTS.md` / `CLAUDE.md`** — the Scaling Mandate, the Engineering Protocols and the
   Definition of Done are binding. Verification is execution; a prediction phrased as a
   confirmation is a lie.
2. **`docs/phase2_hardening_completion_plan.md`, the `START HERE — handoff` section at the
   end.** That is the live handoff: measured state, the three red stages and who owns each,
   the two mutation clusters that cannot currently be proven, the recommended order of work,
   and **ten** measured traps. Everything you need to pick up work is there.
3. The middle of that plan for the *design* of whichever step you are implementing. Read it
   for design, never for status — the status sections are dated and the handoff wins.
4. **`validation_reports/HARDENING_EVIDENCE.md`**, last entry, for how the current numbers
   were obtained and which commands produced them.

## Confirm the tree before trusting any number here

```sh
git log --oneline -1            # expect 14d98739 or a descendant
git status --porcelain          # expect EMPTY
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
#  -> PASS hardening_status: 9 H-row(s) valid — 3 closed, 5 open, 1 out_of_scope
```

## The three things worth saying twice

**The Definition of Done command needs no prefix.** `run_all` pins the database URL empty
itself and prints what it overrode, because `.env` carries a live Neon URL and the verdict
used to depend on whether you remembered.

```sh
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
```

**The Definition of Done is NOT met, and no artifact in this repository claims it is.**
Three stages are red: 1,158 Phase 2 review findings, 218 attestation findings, and the two
mutation clusters behind `assertion_coverage_8`. Every red is named, none is warning-only,
`crashed=0`. Do not report a green subset as completion.

**SEQUENCING — read this before you edit a single file.** `obligation_manifest_11` is green
because six release receipts exist, and every receipt binds `source_input_digest()`, the same
`INPUT_ROOTS` digest the 146-record mutation corpus binds. **Any** edit under `backend/app`,
`tests`, `scripts`, `data`, `frontend/src`, `docs/pgen_contract.md` or
`docs/testing_pipeline.md` invalidates all of it and costs **~70 min of corpus plus ~2.5h of
sweep** to restore. That is correct for gates that certify bytes rather than intentions, and
it was paid twice on 2026-09-16 — the second time for about 200 lines of harness fix. So:

> **Batch every source edit, land them all, and run the corpus and the sweep LAST.**
> The plan's "recommended order" is only valid for a session that edits no source.

Plan traps 9 and 10 carry the measurements behind this.

## One open decision that is the owner's, not yours

The handoff rule says claim an H-row before starting work. `tests/unit/test_hardening_status.py
::test_the_live_ledger_has_a_row_per_blocker` pins the row set to `H-01`–`H-09`, and its
`f"H-0{n}"` pattern cannot express a two-digit row. **Those two rules conflict for any NEW
blocker.** On 2026-09-16 an agent opened `H-10` for the Phase-1-wide hermeticity gate, saw
`unit_tests` go red, and **withdrew the row rather than edit the assertion** — editing a check
so your own change passes is what Protocol 5 forbids, and the row set is the owner's ground
truth, not an error. That work is recorded in the plan and the evidence log instead.

If your work needs a new row, **stop and ask the owner**. Do not edit that test on your own
authority, and do not quietly file the work under someone else's row.

## Claim your row before you start

`owner` is a work-lock. Claim the row, release it on commit (`unclaimed` or
`released @ <rev>`), and if your session identifier embeds an H-row token make sure it is
*your own* row — that check exists because a worker claimed H-07 while doing H-08, which left
the untouched blocker reading as live work and the nearly-finished one reading as unstarted.

## What to pick up

The plan's `START HERE` recommended order is current; steps 1 (H-04's sweep) and 5 (the
Phase-1-wide hermeticity gate) are done. The largest unstarted body of work is **`H-07` / §1L
(plan step 3A)**, and step 3A says in its own words that it is "its own project" and "not a
one-session lint migration" — M1 asks only for the nonbinding
`context_semantics_inventory.json` with zero unmapped live sources. Do **not** add a binding
§1L contract row against a red baseline.

Whatever you pick: build the gate while its baseline is clean (Mandate 5), prove it by
executing a planted violation rather than by reading the validator (Mandate 1), diagnose a
surviving mutation by instrumenting the real path (Mandate 2), and name every blind spot in
the docstring, the contract row and the evidence log (Mandate 6). A gate described as total
is how the next agent stops looking.
