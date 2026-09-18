# Handoff — continue the Phase 2 hardening plan

**Rewritten 2026-09-19 on `e49b0cb4`. This file is deliberately a POINTER, not a summary.**

Earlier versions duplicated the plan's status and then drifted from it: one described a
105-proof corpus, a green Phase 1 and a red interest path while the tree had 145 mutations,
a red Phase 1 and a green interest path. Two sources of truth is how a session inherits
confident wrong numbers, so the status lives in exactly one place — the plan's
`START HERE — handoff` — and this file tells you how to reach it safely.

---

## FIRST: establish whether the tree is mid-re-proof

```sh
git log --oneline -1                     # expect e49b0cb4 or a descendant
git status --porcelain                   # NOT empty => a session was interrupted mid-chain
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
#  -> PASS hardening_status: 9 H-row(s) valid — 3 closed, 5 open, 1 out_of_scope

PYTHONPATH=. .venv/bin/python - <<'PY'
from backend.app.practice_gen.validation.mutation_proof import input_digest
import json, glob, collections
live = input_digest(); print('LIVE', live[:16])
for f in sorted(glob.glob('validation_reports/phase2_hardening/obligation_release_shards/*.json')):
    print(' ', f.split('/')[-1], json.load(open(f))['source_input_digest'] == live)
for n in ('obligation_benchmark.json', 'frontend_static_render.json'):
    print(' ', n, json.load(open(f'validation_reports/phase2_hardening/{n}'))['source_input_digest'] == live)
c = collections.Counter(json.load(open(f))['input_digest'] == live
                        for f in glob.glob('validation_reports/mutation_proofs/*.json'))
print('  proofs current', c[True], 'stale', c[False])
PY
```

As of `e49b0cb4` every one of those is `True` at digest `1060da57c9f5ef18`, with 147 proofs
and 0 stale. **If any is False, a re-proof never finished — finish it before starting new
work**, in this order, each alone (see trap 6):

```sh
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py                                         # ~10s
DATABASE_URL= PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000 # ~16s
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/mutation_harness.py                                        # ~70m
for N in 0 1 2 3 4 5; do DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/obligation_executor.py \
    --tier release --workers 4 --shard-count 6 --shard-index $N; done                                       # ~2.6h
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/obligation_executor.py --tier verify-release
```

**Shards are individually resumable and you should check before restarting all six.** Each
receipt records its own digest, so a sweep interrupted partway (this happened on 2026-09-18)
leaves the completed shards provably reusable. Re-run only the stale indices. That is a
2.5-hour saving you get by reading the digests instead of guessing.

---

## Read this, in this order

1. **`AGENTS.md` / `CLAUDE.md`** — the Scaling Mandate, the Engineering Protocols and the
   Definition of Done are binding. Verification is execution; a prediction phrased as a
   confirmation is a lie.
2. **`docs/phase2_hardening_completion_plan.md`, the `START HERE — handoff` section at the
   end.** The live status: red stages, who owns each, the recommended order, the traps.
3. The middle of that plan for the *design* of whatever you implement. Read it for design,
   never for status — the status sections are dated and `START HERE` wins.
4. **`validation_reports/HARDENING_EVIDENCE.md`**, last entries, for how the current numbers
   were obtained and which commands produced them.

---

## The four things worth saying twice

**The Definition of Done command needs no prefix.** `run_all` pins the database URL empty
itself and prints what it overrode, because `.env` carries a live Neon URL.

```sh
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
```

**The Definition of Done is NOT met, and no artifact here claims it is.** Three stages are
red — `judgment_reviews_5`, `capability_phase2`, `assertion_coverage_8` — every red is
named, nothing is warning-only, `crashed=0`. **Do not report a green subset as completion.**
Read the counts from the plan's `START HERE`, not from this file.

**SEQUENCING — FOUR artifacts bind the source digest, not three.** Any edit under
`backend/app`, `tests`, `scripts`, `data`, `frontend/src`, `docs/pgen_contract.md` or
`docs/testing_pipeline.md` invalidates the mutation corpus (~70m), the six release receipts
(~2.6h), `obligation_benchmark.json` (~16s) **and `frontend_static_render.json` (~10s)**.
The fourth was found on 2026-09-18 and is the treacherous one: `run_all` does NOT regenerate
it, and it currently survives a source edit only *incidentally*, because five mutations run
`tests.frontend_suite` as their command and rewrite it as a side effect of the corpus run.
If those five are ever scoped or removed, an edit leaves §12 stale with no documented
remedy. Regenerate it explicitly. Plan traps 9 and 10 carry the measurements.

> **Batch every source edit, land them all, then re-prove: frontend artifact, benchmark,
> corpus, sweep LAST.** The plan's "recommended order" is only valid for a session that
> edits no source.

**Never re-prove `obligation_benchmark_outlives_source` while the shards are running.** That
mutation plants into `tests/obligation_executor.py`, the module the shards spend 2.6h in.

---

## Two open decisions that are the owner's, not yours

**1. A new blocker needs a new H-row, and the row set cannot express one.**
`tests/unit/test_hardening_status.py::test_the_live_ledger_has_a_row_per_blocker` pins the
rows to `H-01`–`H-09` with an `f"H-0{n}"` pattern that cannot produce a two-digit row. On
2026-09-16 an agent opened `H-10`, saw `unit_tests` go red, and **withdrew the row rather
than edit the assertion** — editing a check so your own change passes is what Protocol 5
forbids. **If your work needs a new row, stop and ask the owner.** Two known candidates are
waiting on exactly this: the intro-surface render gap (below) and the `A arena has 10
basketballs` article/noun gate that §1J does not catch.

**2. `CSI-R1`–`CSI-R3`** are open owner rulings in
`validation_reports/phase2_hardening/context_semantics_inventory.json`. `CSI-R4` is ruled and
closed. Do not hand-patch around them.

---

## Claim your row before you start

`owner` is a work-lock. Claim the row, release it on commit (`unclaimed` or
`released @ <rev>`), and if your session identifier embeds an H-row token make sure it is
*your own* — that check exists because a worker claimed H-07 while doing H-08.

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py     # must PASS before and after
```

Every artifact you add under `validation_reports/phase2_hardening/` — including inside
subdirectories — must be claimed by some row's `proof_artifacts`, or the ledger fails.

---

## What is left

**M2 content work is now the ONLY remaining blocker in the harness, and everything else
funnels into it.** Read the plan's `START HERE` for the ranking; the shape as of 2026-09-19:

- **M2 (plan steps 6 and 7) — the whole of the remaining project.** 1,158 review findings and
  218 attestation findings. The attestation queue is also what unblocks the §6F mutation
  cluster, which is now the **sole surviving cluster**: the corpus is 144/147 and all three
  survivors are §6F. Clearing that queue takes it to 147/147 and is the only path left to a
  green `assertion_coverage_8`. The 151 filed reviews are all v1 and unadjudicable; a v1→v2
  migration was **refused as impossible in principle** (it would mean authoring judgments
  nobody gave). Use `legacy_review_queue.json` to *prioritise* re-review, never as evidence.
- **`H-07` / §1L** — M1 (the nonbinding inventory) is DONE. **Do not add a binding §1L
  contract row**: the inventory's own findings are what make the baseline red, and step 3A
  forbids the row until they are zero. `CSI-R1`–`CSI-R3` are the owner's.
- **`H-08` stays OPEN although its five registrations are dispositioned and gated.** Its
  finding — "nothing executes the React components" — is still literally true of the intro
  surface: `/api/matatag/intro/{node_key}` is live, serves 24 nodes, and its cards are drawn
  by ~25 inline `vt === '...'` branches in `frontend/src/App.jsx` emitting 29 visual types,
  and `tests/frontend_suite.py` never loads `App.jsx`. Closing the row on the practice half
  would describe a half-covered gate as total. Needs an H-row; ask first.
- **`H-05`'s and `H-06`'s remainders** as capacity allows.
- **Not a task, but do not lose it:** `comparing_ordering` and `missing_number` each declare
  a `visual_home` that `base_generator` can never read (it reads it only for `visual_read`
  DNAs; both are `algorithmic`). Measured no-ops. Fixing them is a DNA edit that belongs to
  its own change, with its own re-proof.

**§8 is closed and should stay closed.** Its eight mutations were a self-reference deadlock
until 2026-09-17; they now run `pytest tests/unit/test_coverage_selfcheck.py` against a
stubbed `_proof_state`, all at `base=0`. **What that does NOT prove is named in the §8
contract row**: §8's execution accounting (a record failing verification, a per-label stale
digest, `never_executed` vs `proof_does_not_hold`) is stubbed out and stays provable only
against a green live corpus. Do not describe §8 as fully proven.

---

## Rules this handoff will not let you skip

- **The Definition of Done is an executed `run_all` with its output shown.** It is currently
  NOT met and this document does not claim otherwise.
- **Never weaken a check to make it pass.** If a gate is red, the bug is in the pipeline. The
  one exception is documented ground-truth error, reported with node ID and justification.
- **Prove a check by executing a planted violation**, not by reading the validator. A
  surviving mutation has two causes — a broken check, or a plant that no longer reaches the
  code the validator runs — and you must tell them apart by instrumenting the real path.
  Both were live at once in the §8 cluster: `coverage_map_gap`'s anchor had been matching
  **zero lines** since the allowlist shrank 29 → 11, invisible because the runner rejects on
  a red baseline *before* it plants.
- **Check that your mutation is not passing for the wrong reason.** A plant that edits a
  digest-bound module reds the freshness check by itself, so the command exits 1 whether or
  not your gate works. Break your own gate deliberately and confirm the marker disappears;
  the proof must rest on the marker, not the exit code. Measured on 2026-09-18.
- **A fix at the data layer gates nothing.** Where you fix content without a gate, say so.
- **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
  the evidence log. A gate described as total is how the next agent stops looking.
- **File an Evidence section** in `validation_reports/HARDENING_EVIDENCE.md` with the exact
  commands, verbatim output, and seeds for anything found or fixed.
