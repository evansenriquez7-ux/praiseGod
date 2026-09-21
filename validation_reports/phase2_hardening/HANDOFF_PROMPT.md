# Handoff — continue the Phase 2 hardening plan

**Rewritten 2026-09-21 on `2d335e8c`, with the tree CERTIFIED. This file is deliberately a
POINTER, not a summary.**

Earlier versions duplicated the plan's status and then drifted from it. Two sources of truth
is how a session inherits confident wrong numbers, so status lives in exactly one place —
the plan's `START HERE — handoff` — and this file tells you how to reach it safely and what
the owner has already decided.

---

## FIRST: establish what state the tree is in

**Do this before touching anything.** There are THREE states and they are not equally obvious.

```sh
git log --oneline -1                     # expect 2d335e8c or a descendant
git status --porcelain                   # NOT empty => a session was interrupted
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

**The expected reading on `2d335e8c`, and what CERTIFIED looks like:**

```text
LIVE 90ed5464a45073d9
  shard_000..005          True   (all six)
  obligation_benchmark    True
  frontend_static_render  True
  proofs current 147 stale 0
```

| What you see | What it means | What to do |
|---|---|---|
| All `True`, clean tree | **Certified. This is the state you were handed.** | Start THE JOB below. Do not re-run the chain — it proves nothing new. |
| Mixed/`False`, **clean** tree | A batch landed and its re-proof was not run | Re-proof chain first, in the documented order below |
| Any `False`, **dirty** tree | A session was interrupted mid-work | Read "if you arrive mid-anything" below. Shards are individually resumable. |

**The last two are indistinguishable from the digests alone** and today you can only tell
them apart by reading prose. **That is a pipeline defect and fixing it is step 1 of your
job.** See THE JOB.

---

## THE JOB

The owner ruled on 2026-09-21. These supersede standing rules where they conflict, and the
full text is in the plan's `START HERE`. Read it there; the summary here is orientation only.

Your work has **two phases, in this order, and the order is load-bearing.**

### Phase A — land every source edit in ONE batch, pay ONE re-proof

Anything under `INPUT_ROOTS` (`backend/app`, `tests`, `scripts`, `data`, `frontend/src`,
`docs/pgen_contract.md`, `docs/testing_pipeline.md`) invalidates all four artifact families
and costs ~3.4h to restore. **So do all of it at once, then re-prove once.** Four items,
all owner-authorised:

1. **Interruption-safety machinery (do this first — it makes every later session cheaper).**
   Build `validation_reports/phase2_hardening/tree_state.json` (committed, digest-free,
   survives a clone) recording *intent*: written when a batch or chain starts, cleared on
   completion. Plus `tests/tree_state.py`, a single entry point that prints which of the
   three states the tree is in. **It needs its own mutation proving it cannot report
   `certified` on a stale tree.** Today no such machinery exists — `MUTATION_IN_FLIGHT.json`
   is a kill-safety marker for the corpus alone, nothing records batch intent, and the
   three-state determination is an ad-hoc script plus a human-written paragraph.
2. **Widen the H-row cap.** `tests/unit/test_hardening_status.py:50` pins
   `assert ids == {f"H-0{n}" for n in range(1, 10)}`, which cannot express `H-10`. Widen to
   two digits with the contract row in the same commit. H-08's remainder (the intro-surface
   render gap) has been waiting on exactly this.
3. **Fix the §1J hints hole.** `validate_language._texts` reads `problem["hint"]`, singular;
   the student-path payload carries `hints`, a LIST. **No hint text has ever been linted.**
   `mat_g2_na_q3_0` seed 17 currently ships `"Think of it as 1 groups of 3: 3."` — a live
   violation of the exact class §1J exists to catch. Fix the lint, then fix whatever it
   finds. `dna.base.count_noun` is the rule; do not re-derive it.
4. **Fix the 6 undrawn-referent nodes, THEN build the gate.** Owner ruled: draw the referent
   on all 6 before the gate lands, so its baseline is genuinely zero rather than
   dispositioned-around. No gate catches a stem referencing a display the item never draws —
   three nodes served literally unanswerable items until 2026-09-19 and the sweep that found
   them was a scratch probe, not a check.

Then, and only then, the chain — **in this order**:

```sh
# frontend FIRST when source changed (~10s) — run_all does NOT regenerate it
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py
# benchmark (~16s) — skipping it leaves a survivor you will misdiagnose
DATABASE_URL= PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000
# corpus (~50m). EXIT 1 IS NORMAL: it reports survivors. Read the tail, do not assume a crash.
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/mutation_harness.py
# sweep LAST (~2.6h, six shards ~25.5m each)
for N in 0 1 2 3 4 5; do DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/obligation_executor.py \
    --tier release --workers 4 --shard-count 6 --shard-index $N; done
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/obligation_executor.py --tier verify-release
# the Definition of Done — needs no DATABASE_URL= prefix; run_all pins it itself
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
```

### Phase B — the capability attestation campaign

**This is the only work that can turn a red stage green.** `judgment_reviews_5`,
`capability_phase2` AND `assertion_coverage_8` are all downstream of it.

**Attestation filing is DIGEST-FREE — verified, not assumed.** `validation_reports/judgment/`
and `validation_reports/attestation/` are deliberately outside the fingerprint (see
`mutation_proof.INPUT_FILES`' comment). A probe file written into `attestation/` left the
digest unmoved. **So the entire campaign runs without spending a single re-proof**, provided
you touch no source. That is precisely why Phase A goes first.

Owner ruled the **whole 218-finding queue is one campaign**, spanning sessions and
**resumable**. Start with the nine ripe nodes — 17 of the 67 CONTRADICTED sit here, and each
already renders content that demonstrably moved toward its clause:

```text
mat_g2_na_q4_3 (6)   fraction number-line and set models now render
mat_g1_na_q1_0 (2)   counting backward now renders
mat_g2_na_q3_0 (2)   the "5 threes" register now renders  [see §1J note below]
mat_g3_mg_q2_0 (2)   a graduated dial is now drawn (was UNANSWERABLE)
mat_g3_mg_q2_3 (2)   a graduated cylinder is now drawn (was UNANSWERABLE)
mat_g1_dp_q3_3 (2)   the pictograph is now drawn (was UNANSWERABLE)
mat_g3_na_q1_4 (1)   rounding to the nearest thousand now renders
mat_g3_mg_q2_1 (0)   estimate no longer keys a zero measurement
mat_g3_mg_q2_4 (0)   same
```

**`mat_g2_na_q3_0` changed again on 2026-09-21** (`e23a4ffe`, the §1J fix). Its renders are
newer than any prior evidence — re-attest it against what it renders NOW, not against any
recorded sample.

**How blindness works, per the owner's ruling.** You DISPATCH to a separate agent that has
neither the answer key nor your context. `tests/attester_packets.py` writes what the Attester
sees and the key it must not see; `tests/attester_file.py` turns returned verdicts into
§6F/§6G records without retyping. **Blindness is a prompt contract, not a sandbox.** You never
author a verdict, never re-file one, and never copy a v1 rationale forward — all 151 legacy
reviews are v1 and unadjudicable, and the v1→v2 migration was refused as impossible in
principle. Use `legacy_review_queue.json` to PRIORITISE, never as evidence.

**A generator fix does not clear a §6F finding.** Only a blind re-judgement does. The
2026-09-19 batch fixed seven content defects and cleared ZERO findings — the queue stayed at
218 and merely shifted kind.

---

## If you arrive mid-anything

A handoff can happen at any moment; hardware and environment failures are outside a session's
control, and the owner has ruled that "must end certified" is NOT the rule. So:

* **Shards are individually resumable.** Each receipt records its own digest. Re-run only the
  stale indices — that is a 2.5-hour saving you get by reading digests instead of guessing.
* **A surviving mutation has TWO causes** and you must tell them apart: the check is broken,
  or the plant no longer reaches the code the validator runs. Diagnose by instrumenting the
  real path, never by reading the validator and concluding it would work.
* **`INVALID — the unmutated command baseline exited 1` is a THIRD thing** and is neither.
  The runner refused to score, because the baseline was already red. Re-running cannot fix it.
* **Never re-prove `obligation_benchmark_outlives_source` while shards are running.** It
  plants into `tests/obligation_executor.py`, the module the shards spend 2.6h inside.

---

## Read this, in this order

1. **`AGENTS.md` / `CLAUDE.md`** — the Scaling Mandate, Engineering Protocols, Definition of
   Done. Verification is execution; a prediction phrased as a confirmation is a lie.
   **Note the 2026-09-21 ruling supersedes File Management's read-only rule on `validation/`.**
2. **`docs/phase2_hardening_completion_plan.md`, `START HERE — handoff`.** It opens with a
   dated block that supersedes everything below it, including the six owner rulings in full.
3. The middle of that plan for the *design* of what you implement. Design, never status.
4. **`validation_reports/HARDENING_EVIDENCE.md`**, last two entries (2026-09-20), for how the
   current numbers were obtained.

---

## Claim your row before you start

`owner` is a work-lock. Claim it, release it on commit (`unclaimed` or `released @ <rev>`).
If your session identifier embeds an H-row token, make sure it is *your own* — that check
exists because a worker once claimed H-07 while doing H-08.

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py     # must PASS before and after
```

`H-06` was released `@ e23a4ffe` on 2026-09-20 and stays OPEN — it holds the M2 capability
queue and must not be closed by a re-proof alone. **`H-02`, `H-05`, `H-07` and `H-08` are all
open and unclaimed.** Phase A item 2 lets you open `H-10` for the first time — the
row set can finally express one.

**Edit the ledger SURGICALLY.** `json.dumps(ensure_ascii=True)` over the whole file
renormalises `§`/`—` escapes across rows you do not own; a 2026-09-20 session produced 16
lines of collateral churn that way and had to revert. Patch the lines you mean to patch.

Every artifact you add under `validation_reports/phase2_hardening/` — including inside
subdirectories — must be claimed by some row's `proof_artifacts`, or the ledger fails.

---

## Traps that cost real time

1. **A gate can be defeated one stack frame later.** Verify at the REAL consumer, not at the
   function you edited. The orchestrator's narrowing of a list-valued bound was silently
   undone by `generate_context`; the orchestrator's own output looked correct.
2. **A rule copy-pasted into N sites will disagree with itself.** The `_number_plurals`
   register lived in SIX places; waking it up shipped "1 threes" past a green matrix, green
   compat, green render and 739 green unit tests, because the only gate that catches it runs
   in the re-proof chain. Consolidate to one definition and route it through the same helper
   the validator imports.
3. **`_generated_formatter_exclusions.py` goes stale** whenever a formatter or COMPATIBILITY
   entry changes; §2B fails loudly naming each entry. Regenerate with
   `PYTHONPATH=. .venv/bin/python3 -m scripts.regen_formatter_exclusions`. **Never hand-edit
   it** — it is derived empirically because three attempts to model the orchestrator's
   eligibility rules statically all drifted.
4. **Adding a formatter changes the obligation product**, so pinned counts in
   `tests/unit/test_obligation_executor.py` move. Confirm every added route is actually
   SERVED at several seeds *before* touching those numbers. Updating a count to match reality
   is legitimate; updating it to make a test pass is not.
5. **A shared distractor helper can be right for arithmetic and wrong for your domain.**
   `augment_distractors` refuses negatives but allows ZERO — correct for sums, and it put a
   `0 g` option against a `1 g` answer. Filter in your formatter; do not weaken a helper
   fifteen formatters share.
6. **The pre-commit hook rebuilds Graphify and stages `graphify-out/`.** Expect more files in
   the commit than you staged. It does NOT move the input digest — verify that rather than
   assume it.
7. **Do not run anything heavy concurrently.** `tests/frontend_renderer.py` writes to one
   fixed path with no PID and no lock; six call sites funnel through it. Unfixed.
8. **Cosmetic edits cost 3.4 hours.** A 2026-09-20 session realigned four import
   continuation lines AFTER completing the chain and invalidated the whole re-proof. It was
   reverted byte-for-byte rather than re-run. Once certified, touch no source you do not mean
   to change.
9. **`git commit --amend` moves the hash**, so a ledger row written as `released @ <hash>`
   before the amend points at a dangling commit. Release in a follow-up commit, not an amend.

---

## Still owner-owned — do not hand-patch around these

**`CSI-R1`–`CSI-R3`** are open owner rulings in `context_semantics_inventory.json`. `CSI-R4`
is ruled and closed.

---

## Limitations left standing — named so you keep looking

* **§1J does not lint hints.** Phase A item 3. Until then, a green §1J covers stems,
  statements, prompts and cloze templates — NOT hints.
* **No gate catches a stem that references a display the item never draws.** Phase A item 4.
* **The ANY reading of `formatter_refused_at_node` is not mutation-covered at its own
  comparison.** Proven to still catch silent substitution and consistent with production on
  the NONE and PARTIAL cases; the `wanted & allowed` boundary itself is unproven.
* **Nothing asserts a pictograph's symbol COUNT equals the table's answer.** Verified once,
  by hand.
* **`ScaleRead` geometry is proven by arithmetic on emitted attributes, not layout** — jsdom
  has no layout engine, the same blind spot §12 already names for NumberLine/BarChart.
* **The estimate-task floor gates nothing.** A sibling DNA framing estimation as rounding
  would reproduce the zero-measurement defect with every gate green.
* **§8's execution accounting is stubbed** and stays provable only against a green live
  corpus. Do not describe §8 as fully proven.
* **`comparing_ordering` and `missing_number` each declare a `visual_home` that
  `base_generator` can never read** (it reads it only for `visual_read` DNAs; both are
  `algorithmic`). Measured no-ops. Fixing them is a DNA edit that belongs to its own change.
* **The Phase 1 network guard patches ONE interpreter**, so connections opened inside
  children of `unit_tests`, `census_7` and `behavioural_matrix` are invisible; Phase 2 stages
  are unguarded; loopback is allowed. See `docs/pgen_contract.md`'s `phase1_hermetic` row.

---

## Rules this handoff will not let you skip

- **The Definition of Done is an executed `run_all` with its output shown.** It is currently
  **NOT met** and this document does not claim otherwise. A green subset is not completion.
- **Never weaken a check to make it pass.** If a gate is red, the bug is in the pipeline. The
  one exception is documented ground-truth error, reported with node ID and justification.
  (The H-row widening is such a case and is already ruled.)
- **Prove a check by executing a planted violation**, not by reading the validator.
- **Check that your mutation is not passing for the wrong reason.** A plant that edits a
  digest-bound module reds the freshness check by itself, so the command exits 1 whether or
  not your gate works. Break your own gate deliberately and confirm the marker disappears.
- **A fix at the data layer gates nothing.** Where you fix content without a gate, say so.
- **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
  the evidence log. A gate described as total is how the next agent stops looking.
- **File an Evidence section** in `validation_reports/HARDENING_EVIDENCE.md` with the exact
  commands, verbatim output, and seeds for anything found or fixed.
