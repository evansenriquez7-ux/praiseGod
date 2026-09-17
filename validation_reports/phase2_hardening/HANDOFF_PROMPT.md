# Handoff — continue the Phase 2 hardening plan

**Rewritten 2026-09-17. This file is deliberately a POINTER, not a summary.**

Earlier versions duplicated the plan's status and then drifted from it: on 2026-09-15 this
file described a 105-proof corpus, a green Phase 1 snapshot and a red interest path, while
the tree had 145 mutations, a red Phase 1 and a green interest path. Two sources of truth is
how a session inherits confident wrong numbers, so the status lives in exactly one place.

---

## FIRST: establish whether the tree is mid-re-proof

The 2026-09-17 session edited `data/interest_bank.json` and `tests/context_semantics_inventory.py`
and its re-proof chain **may not have finished**. Before anything else:

```sh
git log --oneline -1
git status --porcelain                  # NOT empty => a session was interrupted mid-chain
PYTHONPATH=. .venv/bin/python -c "from backend.app.practice_gen.validation.mutation_proof import input_digest; print(input_digest())"
PYTHONPATH=. .venv/bin/python -c "import json,glob;[print(f.split('/')[-1], json.load(open(f))['source_input_digest'][:16]) for f in sorted(glob.glob('validation_reports/phase2_hardening/obligation_release_shards/*.json'))]"
```

**If the receipts' digest does not match `input_digest()`, the re-proof never completed.**
Finish it before starting new work, in this order, each alone (see trap 6):

```sh
DATABASE_URL= PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000   # ~16s
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/mutation_harness.py                                          # ~70m
for N in 0 1 2 3 4 5; do DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/obligation_executor.py \
    --tier release --workers 4 --shard-count 6 --shard-index $N; done                                          # ~2.6h
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/obligation_executor.py --tier verify-release
PYTHONPATH=. .venv/bin/python tests/context_semantics_inventory.py --write --seeds 4                           # ~20m
```

Do not start new work on top of an unfinished chain. A stale receipt reds
`obligation_manifest_11` and a stale benchmark manufactures a surviving mutation that looks
like a broken gate and is not one.

---

## Read this, in this order

1. **`AGENTS.md` / `CLAUDE.md`** — the Scaling Mandate, the Engineering Protocols and the
   Definition of Done are binding. Verification is execution; a prediction phrased as a
   confirmation is a lie.
2. **`docs/phase2_hardening_completion_plan.md`, the `START HERE — handoff` section at the
   end.** That is the live handoff: measured state, the red stages and who owns each, the
   mutation clusters that cannot currently be proven, the recommended order of work, and the
   measured traps. Everything you need to pick up work is there.
3. The middle of that plan for the *design* of whichever step you are implementing. Read it
   for design, never for status — the status sections are dated and the handoff wins.
4. **`validation_reports/HARDENING_EVIDENCE.md`**, last entries, for how the current numbers
   were obtained and which commands produced them.

---

## The four things worth saying twice

**The Definition of Done command needs no prefix.** `run_all` pins the database URL empty
itself and prints what it overrode, because `.env` carries a live Neon URL and the verdict
used to depend on whether you remembered.

```sh
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
```

**The Definition of Done is NOT met, and no artifact in this repository claims it is.**
Three stages are red: the Phase 2 review findings, the attestation findings, and the mutation
clusters behind `assertion_coverage_8`. Every red is named, none is warning-only, `crashed=0`.
**Do not report a green subset as completion.** Read the current counts from the plan's
`START HERE`, not from this file.

**SEQUENCING — THREE artifacts bind `source_input_digest()`, not two.** Any edit under
`backend/app`, `tests`, `scripts`, `data`, `frontend/src`, `docs/pgen_contract.md` or
`docs/testing_pipeline.md` invalidates **the mutation corpus (~70 min), the six release
receipts (~2.6h), and `obligation_benchmark.json` (~16s)**. The benchmark was the one nobody
had named; omitting it leaves `obligation_benchmark_outlives_source §11` surviving, which
reads exactly like a hole in §11 and is a red baseline instead. Plan traps 9 and 10 carry the
measurements.

> **Batch every source edit, land them all, then re-prove: benchmark, corpus, sweep, LAST.**
> The plan's "recommended order" is only valid for a session that edits no source.

**Never re-prove `obligation_benchmark_outlives_source` while the shards are running.** That
mutation plants an edit into `tests/obligation_executor.py`, which is the module the six
shards spend 2.6 hours executing.

---

## One open decision that is the owner's, not yours

The handoff rule says claim an H-row before starting work.
`tests/unit/test_hardening_status.py::test_the_live_ledger_has_a_row_per_blocker` pins the row
set to `H-01`–`H-09`, and its `f"H-0{n}"` pattern cannot express a two-digit row. **Those two
rules conflict for any NEW blocker.** On 2026-09-16 an agent opened `H-10`, saw `unit_tests`
go red, and **withdrew the row rather than edit the assertion** — editing a check so your own
change passes is what Protocol 5 forbids, and the row set is the owner's ground truth.

If your work needs a new row, **stop and ask the owner.** Do not edit that test on your own
authority, and do not quietly file the work under someone else's row.

---

## Claim your row before you start

`owner` is a work-lock. Claim the row, release it on commit (`unclaimed` or
`released @ <rev>`), and if your session identifier embeds an H-row token make sure it is
*your own* row — that check exists because a worker claimed H-07 while doing H-08, which left
the untouched blocker reading as live work and the nearly-finished one reading as unstarted.

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py     # must PASS before and after your edits
```

Every artifact you add under `validation_reports/phase2_hardening/` — including inside
subdirectories — must be claimed by some row's `proof_artifacts`, or the ledger fails.

---

## What is left, and what to pick up

Read the plan's `START HERE` recommended order for the current ranking. As of 2026-09-17 the
shape of the remaining work is:

- **M2 content work is the bulk of the project** — the Phase 2 review findings and the
  attestation findings. This is also what unblocks the §6F mutation cluster, which is
  downstream of the attestation queue rather than of any harness work. The 151 filed reviews
  are all v1 and therefore unadjudicable; a v1→v2 migration was **refused as impossible in
  principle** (it would mean authoring judgments nobody gave). Use
  `validation_reports/phase2_hardening/legacy_review_queue.json` to *prioritise* re-review,
  never as evidence.
- **`H-07` / §1L** — M1 (the nonbinding `context_semantics_inventory.json`) is DONE. **Do not
  add a binding §1L contract row**: the inventory's own findings are what make the baseline
  red, and step 3A forbids the row until they are zero. Three owner rulings, `CSI-R1`–`CSI-R3`,
  are open in the inventory JSON and are the owner's, not yours. `CSI-R4` is ruled and closed.
- **A gap with no gate:** `A arena has 10 basketballs` — article/noun disagreement. §1J checks
  count/noun only and names its blind spots, which do not include articles. Building this
  check is plausibly a new H-row, so **ask first**.
- **`H-08`'s five uncovered registrations** — `BalanceScale`, `Categorize`, `RuleDiscovery`,
  `SortOrder`, `TenFrame`. They need a dead-route versus non-practice-reachable disposition.
  Pointer geometry on `NumberLine`/`BarChart` stays a named blind spot; jsdom cannot prove it
  and it must not be described as covered.
- **`H-05`'s remainder, `H-06`'s remainder, and the §8 self-reference deadlock** as capacity
  allows. The §8 cluster is a genuine deadlock — its baseline IS §8, §8 is red because its
  labels are unproven, and the labels are unproven because the baseline is red. **Do not just
  re-run it**; the documented delete-and-rerun remedy was tried and 3 of 4 attempts stayed
  INVALID. The recommended, not-yet-attempted close is to drive those eight through a unit
  test against a *stubbed* coverage state, recording that trade in the contract row.

---

## Rules this handoff will not let you skip

- **The Definition of Done is an executed `run_all` with its output shown.** It is currently
  NOT met and this document does not claim otherwise.
- **Never weaken a check to make it pass.** If a gate is red, the bug is in the pipeline. The
  one exception is documented ground-truth error, reported with node ID and justification.
- **Prove a check by executing a planted violation**, not by reading the validator. A mutation
  that survives has two causes — a broken check, or a plant that no longer reaches the code
  the validator runs — and you must tell them apart by instrumenting the real path.
- **A fix at the data layer gates nothing.** The 2026-09-17 interest-bank repair corrected
  today's data and added no check; the next author to add a theme entry can reintroduce the
  same shape. Where you fix content without a gate, say so in writing.
- **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
  the evidence log. A gate described as total is how the next agent stops looking.
- **File an Evidence section** in `validation_reports/HARDENING_EVIDENCE.md` with the exact
  commands, verbatim output, and seeds for anything found or fixed.
