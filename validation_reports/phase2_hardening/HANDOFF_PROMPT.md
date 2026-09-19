# Handoff — continue the Phase 2 hardening plan

**Rewritten 2026-09-19 on `7e33d26d`. This file is deliberately a POINTER, not a summary.**

Earlier versions duplicated the plan's status and then drifted from it: one described a
105-proof corpus, a green Phase 1 and a red interest path while the tree had 145 mutations,
a red Phase 1 and a green interest path. Two sources of truth is how a session inherits
confident wrong numbers, so the status lives in exactly one place — the plan's
`START HERE — handoff` — and this file tells you how to reach it safely.

---

## FIRST: establish what state the tree is in

There are THREE states, not two, and the newest one is why this file was rewritten.

```sh
git log --oneline -1                     # expect 7e33d26d or a descendant
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

| What you see | What it means | What to do |
|---|---|---|
| All `True`, clean tree | Certified. Rare. | Pick up M2 below. |
| Mixed / all `False`, **clean** tree, HEAD `7e33d26d` | **Mid-BATCH.** A content batch landed and its re-proof was deliberately not run. This is today's state. | **Run the re-proof chain. That is the job.** |
| Any `False`, **dirty** tree | Mid-re-proof, interrupted. | Finish it; see "Shards are resumable" below. |

**Mid-batch and mid-re-proof look identical from the digests alone.** The difference is
whether the worktree is clean and whether the plan's `START HERE` says a batch landed.
As of `7e33d26d` it does, and the expected reading is:

```text
LIVE 8847c1d5babb0f5f
  shard_000..005          False   (all six)
  obligation_benchmark    False
  frontend_static_render  True    <- ALREADY FRESH. Do not regenerate without a source edit.
  proofs current 0 stale 147
```

---

## THE JOB: run the re-proof chain

Nothing in this plan can be certified until this finishes. It is unattended, ~3.7 hours,
and **no file under `INPUT_ROOTS` may be edited while it runs** (`backend/app`, `tests`,
`scripts`, `data`, `frontend/src`, `docs/pgen_contract.md`, `docs/testing_pipeline.md`).

```sh
# 1. benchmark FIRST — 16s, and skipping it leaves a survivor you will misdiagnose
DATABASE_URL= PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000

# 2. corpus — ~70m
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/mutation_harness.py

# 3. sweep LAST — ~2.6h, six shards, each ~25.5m
for N in 0 1 2 3 4 5; do DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/obligation_executor.py \
    --tier release --workers 4 --shard-count 6 --shard-index $N; done
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/obligation_executor.py --tier verify-release

# 4. the Definition of Done — needs no DATABASE_URL= prefix; run_all pins it itself
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
```

**The frontend artifact is already current and is NOT in this list.** It is the fourth
digest-bound artifact and `run_all` does not regenerate it. If you edit source, regenerate
it explicitly with `DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py`
(~10s), BEFORE the corpus.

**Shards are individually resumable — check before restarting all six.** Each receipt
records its own digest, so a sweep interrupted partway leaves completed shards provably
reusable. Re-run only the stale indices. That is a 2.5-hour saving you get by reading the
digests instead of guessing.

**Never re-prove `obligation_benchmark_outlives_source` while the shards are running.**
That mutation plants into `tests/obligation_executor.py`, the module the shards spend 2.6h
inside.

### What a green re-proof will and will not buy you

It clears `assertion_coverage_8`'s staleness and `obligation_manifest_11`. It does **not**
make `run_all` exit 0: `judgment_reviews_5` and `capability_phase2` are content debt and
stay red. Expect `assertion_coverage_8` to remain red on the §6F cluster, which is
downstream of M2. **Do not report a green subset as completion.**

---

## Read this, in this order

1. **`AGENTS.md` / `CLAUDE.md`** — the Scaling Mandate, the Engineering Protocols and the
   Definition of Done are binding. Verification is execution; a prediction phrased as a
   confirmation is a lie.
2. **`docs/phase2_hardening_completion_plan.md`, the `START HERE — handoff` section.** It
   opens with a dated block that supersedes the numbers below it. Read that block first.
3. The middle of that plan for the *design* of whatever you implement. Read it for design,
   never for status.
4. **`validation_reports/HARDENING_EVIDENCE.md`**, last two entries (both 2026-09-19), for
   how the current numbers were obtained and which commands produced them.

---

## After the re-proof: M2, and the nine nodes that are ripe

M2 is the whole of the remaining project. The plan's `START HERE` carries the counts.

**A generator fix does not clear a §6F finding.** Only a BLIND Attester re-judging the
rendered samples does. The 2026-09-19 batch fixed seven content defects and cleared zero
findings — the queue total stayed at 218 and merely shifted kind (STALE 69 → 73).

**What it did buy is a ranked re-attestation queue.** Nine nodes now render content that
demonstrably moved toward their clause, each showing a STALE or missing-evidence batch with
its CONTRADICTED capabilities still standing. Re-attest these first — they are the pairs
most likely to flip NOT_PROVIDED → PROVIDED, and 17 of the 67 CONTRADICTED live here:

```text
mat_g2_na_q4_3 (6)   fraction number-line and set models now render
mat_g1_na_q1_0 (2)   counting backward now renders
mat_g2_na_q3_0 (2)   the "5 threes" register now renders
mat_g3_mg_q2_0 (2)   a graduated dial is now drawn (was UNANSWERABLE)
mat_g3_mg_q2_3 (2)   a graduated cylinder is now drawn (was UNANSWERABLE)
mat_g1_dp_q3_3 (2)   the pictograph is now drawn (was UNANSWERABLE)
mat_g3_na_q1_4 (1)   rounding to the nearest thousand now renders
mat_g3_mg_q2_1 (0)   estimate no longer keys a zero measurement
mat_g3_mg_q2_4 (0)   same
```

The blind half is built: `tests/attester_packets.py` writes what the Attester sees and the
key it must not see; `tests/attester_file.py` turns returned verdicts into §6F/§6G records
without retyping. **Blindness is a prompt contract, not a sandbox.** Never author a verdict,
never re-file one, and never copy a v1 rationale forward — all 151 legacy reviews are v1 and
unadjudicable, and the v1→v2 migration was refused as impossible in principle. Use
`legacy_review_queue.json` to PRIORITISE, never as evidence.

---

## Traps this session hit that are not in the plan's older list

1. **A gate can be defeated one stack frame later.** The orchestrator's narrowing of a
   list-valued bound was silently undone by `generate_context`, which re-injected the whole
   competency bound over it. The orchestrator's own output looked correct. **Verify at the
   real consumer** — here, `counting.generate_params` — not at the function you edited.
2. **`_generated_formatter_exclusions.py` goes stale whenever a formatter or COMPATIBILITY
   entry changes, and §2B fails loudly naming each entry.** Regenerate with
   `PYTHONPATH=. .venv/bin/python3 -m scripts.regen_formatter_exclusions`. **Never
   hand-edit it** — it is derived empirically because three attempts to model the
   orchestrator's eligibility rules statically all drifted.
3. **Adding a formatter changes the obligation product**, so the pinned counts in
   `tests/unit/test_obligation_executor.py` move. Confirm every added route is actually
   SERVED (execute it at several seeds) *before* touching those numbers. Updating a count
   to match reality is legitimate; updating it to make a test pass is not.
4. **A shared distractor helper can be right for arithmetic and wrong for your domain.**
   `augment_distractors` refuses negatives but allows ZERO — correct for sums, and it put a
   `0 g` option against a `1 g` answer. Filter in your formatter; do not weaken a helper
   fifteen formatters share.
5. **The pre-commit hook rebuilds Graphify and stages `graphify-out/` into every commit.**
   Expect more files in the commit than you staged. It does not move the input digest —
   verify that rather than assume it.
6. **Do not run anything heavy concurrently.** `tests/frontend_renderer.py` writes to one
   fixed path with no PID and no lock; six call sites funnel through it. This is unfixed.

---

## Two open decisions that are the owner's, not yours

**1. A new blocker needs a new H-row, and the row set cannot express one.**
`tests/unit/test_hardening_status.py::test_the_live_ledger_has_a_row_per_blocker` pins the
rows to `H-01`–`H-09` with an `f"H-0{n}"` pattern that cannot produce a two-digit row. On
2026-09-16 an agent opened `H-10`, saw `unit_tests` go red, and **withdrew the row rather
than edit the assertion** — editing a check so your own change passes is what Protocol 5
forbids. **If your work needs a new row, stop and ask the owner.** The intro-surface render
gap (H-08's remainder) is still waiting on exactly this.

**2. `CSI-R1`–`CSI-R3`** are open owner rulings in `context_semantics_inventory.json`.
`CSI-R4` is ruled and closed. Do not hand-patch around them.

---

## Claim your row before you start

`owner` is a work-lock. Claim the row, release it on commit (`unclaimed` or
`released @ <rev>`), and if your session identifier embeds an H-row token make sure it is
*your own* — that check exists because a worker claimed H-07 while doing H-08.

`H-06` is currently **open and unclaimed**. It holds the M2 capability queue and the
2026-09-19 content batch; it is NOT closed and should not be closed by a re-proof alone.

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py     # must PASS before and after
```

Every artifact you add under `validation_reports/phase2_hardening/` — including inside
subdirectories — must be claimed by some row's `proof_artifacts`, or the ledger fails.

---

## Limitations left standing — named so you keep looking

* **No gate catches a stem that references a display the item never draws.** Three nodes
  served literally unanswerable items until 2026-09-19 and the sweep that found them was a
  scratch probe, not a check. Per Mandate 5 no gate was added because its baseline is not
  zero: 6 nodes / 39 samples of a cosmetic remainder survive, each describing its referent
  in prose. **Rule on those 6, then build the gate.**
* **The ANY reading of `formatter_refused_at_node` is not mutation-covered at its own
  comparison.** It is proven to still catch silent substitution and proven consistent with
  production on both the NONE and PARTIAL cases; the boundary itself is unproven.
* **Nothing asserts a pictograph's symbol COUNT equals the table's answer.** Verified once,
  by hand.
* **`ScaleRead` geometry is proven by arithmetic on emitted attributes, not layout** —
  jsdom has no layout engine, the same blind spot §12 already names for NumberLine/BarChart.
* **The estimate-task floor gates nothing.** A sibling DNA framing estimation as rounding
  would reproduce the zero-measurement defect with every gate green.
* **§8's execution accounting is stubbed** and stays provable only against a green live
  corpus. Do not describe §8 as fully proven.
* **`comparing_ordering` and `missing_number` each declare a `visual_home` that
  `base_generator` can never read** (it reads it only for `visual_read` DNAs; both are
  `algorithmic`). Measured no-ops. Fixing them is a DNA edit that belongs to its own change.

---

## Rules this handoff will not let you skip

- **The Definition of Done is an executed `run_all` with its output shown.** It is currently
  **NOT met** and this document does not claim otherwise.
- **Never weaken a check to make it pass.** If a gate is red, the bug is in the pipeline.
  The one exception is documented ground-truth error, reported with node ID and
  justification.
- **Prove a check by executing a planted violation**, not by reading the validator. A
  surviving mutation has two causes — a broken check, or a plant that no longer reaches the
  code the validator runs — and you must tell them apart by instrumenting the real path.
- **Check that your mutation is not passing for the wrong reason.** A plant that edits a
  digest-bound module reds the freshness check by itself, so the command exits 1 whether or
  not your gate works. Break your own gate deliberately and confirm the marker disappears.
- **A fix at the data layer gates nothing.** Where you fix content without a gate, say so.
- **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
  the evidence log. A gate described as total is how the next agent stops looking.
- **File an Evidence section** in `validation_reports/HARDENING_EVIDENCE.md` with the exact
  commands, verbatim output, and seeds for anything found or fixed.
