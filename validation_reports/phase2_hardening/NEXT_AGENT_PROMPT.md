# Task prompt — continue the Phase 2 hardening (fresh session)

You are working in `/Users/enrichmentcap/Documents/antigravity/ccmed`, on the Adaptive K-12
Mastery Engine's practice-problem-generator hardening. The tree is **CERTIFIED** and the
re-proof chain is current. Your job is to move `run_all` toward exiting 0 — and to do it in an
order that does not waste days of work.

**The previous prompt in this file was a closeout batch. It is DONE. This supersedes it.**

---

## 0. Ground rules you may not break

Read `CLAUDE.md` / `AGENTS.md` first — the Scaling Mandate, Engineering Protocols and Definition
of Done are binding. The ones that will bite you here:

1. **Verification is execution.** Never report something fixed without running it and showing
   verbatim output. A prediction phrased as a confirmation is a lie.
2. **Never weaken a check to make it pass.** If a gate is red, the bug is in the pipeline. The
   only exception is documented ground-truth error, reported with node id and justification.
3. **You never author an Attester or Reviewer verdict.** Blind evidence comes from a dispatched
   agent with neither the answer key nor your context. If a step seems to need you to judge
   rendered student content yourself, **stop — you have misread it.**
4. **Prove a check by executing a planted violation**, not by reading the validator.
5. **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
   `validation_reports/HARDENING_EVIDENCE.md`.
6. **Content Rule 4 governs every content decision.** MATATAG is the only source of what content
   *becomes*. If a competency names a verb, model or range the pipeline cannot produce, building
   it **is the fix** and is not scope creep. If the competency does not name it, building it is
   invention and is forbidden. **Cite the competency clause** in the commit and the evidence log.

**Invocation:** always `PYTHONPATH=. .venv/bin/python …`. There is no usable bare `python` and no
`timeout` on this host. The fast unit suite takes **11 minutes**, not the 35 seconds an old note
claims; pass `-m "not slow"` explicitly if you run it directly.

---

## 1. Establish state before touching anything

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py          # exit 0 only when CERTIFIED
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
```

Expected:

```
PASS tree_state: CERTIFIED
  live input digest : dfae9bbb7a1398d7
  worktree          : clean
  mutation_proofs         fresh  152 file(s)
  release_shards          fresh  6 file(s)
  obligation_benchmark    fresh  1 file(s)
  frontend_static_render  fresh  1 file(s)

PASS hardening_status: 10 H-row(s) valid — 3 closed, 6 open, 1 out_of_scope
```

**If either disagrees, believe the command, not this file**, and say so before continuing.

Claim the lock and record intent (`H-06`'s `owner` currently reads `released @ 505baf4e`; change
**only** that one line — a whole-file `json.dumps` renormalises escapes across rows you do not
own and has already cost one session 16 lines of collateral churn):

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin campaign \
    --session "<your-session-id>" --note "what you are doing"
# and on completion:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --complete --note "where you got to"
```

Use `--begin campaign` for dispatch work (no re-proof owed) and `--begin batch` for source work.

---

## 2. Measured state, and the ONE thing that decides your order

`run_all` exits 1. Three stages are red:

| stage | count | nature |
|---|---|---|
| `capability_phase2` | **57** CONTRADICTED (36 nodes) | content debt — source work |
| `judgment_reviews_5` | **1252** module / **1253** stage | 151 owed blind re-reviews — dispatch work |
| `assertion_coverage_8` | 3 in 1 family | downstream; unfixable by re-running |

Everything else passes: Phase 1 at its floor of 5, corpus 149/152, six shards 0 failures,
operator coverage 41/41, census `nodes=151 unit_tests=797 mutations=152`.

> **Always quote the ENTRY POINT with a §5 figure.** `validate_judgment` standalone reports 1252;
> the `run_all` stage reports 1253, because `run_all.py:760-764` appends one aggregate rollup the
> module's CLI never emits. Both are correct. This is **not** concurrency pollution — an earlier
> session diagnosed it as such and wrote that into the plan as settled fact. Do not re-open it.

### ⚠ THE 57 IS A TWO-INSTRUMENT NUMBER. THIS DETERMINES YOUR ORDER.

**Owner ruling 9 made prevalence part of the Attester standard** — a verdict must weigh HOW OFTEN
a clause is exhibited across the samples shown, not merely whether any one sample exhibits it.

Only **18 of ~741** filed verdicts were judged under that standard (`batch116`, on
`mat_g1_na_q3_7`, `mat_g2_mg_q2_0`, `mat_g2_mg_q2_2`, `mat_g3_mg_q2_3`). **The rest were judged
on the superseded neutral standard.**

The effect is large and measured. On the same 18 clauses, same packets, same model, varying only
whether the prompt asked for prevalence:

| prompt | PROVIDED | NOT_PROVIDED |
|---|---|---|
| prevalence weighed | 12 | **6** |
| neutral (what ~723 verdicts used) | 16 | **2** |

All six clauses the prevalence prompt failed had been ruled PROVIDED by **two independent raters
each**. So a third of the clauses moved on an instrument change alone.

**Therefore: DO NOT START CONTENT WORK.** Building a formatter for a CONTRADICTED finding earned
on the superseded standard is days of work aimed at a number that is about to move — in both
directions. Some current findings will clear; some current PROVIDEDs will fail. **Re-judge the
corpus first, then build against what survives.**

---

## 3. YOUR JOB, in priority order

### ▶ PRIORITY 1 — the ruling-9 re-dispatch campaign. Costs NO re-proof. Do this first.

Re-judge the attestation corpus under the prevalence standard so `capability_phase2` becomes a
one-instrument number.

* **Scope:** 151 nodes, **767** `(node, capability)` pairs.
* **Caps:** ≤25 clause items per dispatch (§6G); ≤25 nodes per Attester identity (§6H). So
  roughly **31 dispatches over ≥7 identities** for one clean round.
* **Cost:** `validation_reports/attestation/` is **outside** `INPUT_ROOTS`, so a whole campaign
  moves no digest and owes **no chain**. Verify that with `input_digest()` rather than assuming.
* **Batch prefix must sort AFTER `batch116`** — records resolve last-file-wins over a sorted
  glob. Start at `batch117`.
* **EXPECT THE COUNT TO RISE.** A count that rises because the instrument got sharper is
  progress, not regression. Do not tune anything to bring it down.

**Machinery — do not hand-assemble a record:**

```sh
# build the blind half and the key it must not see, ONE NODE PER FILE
PYTHONPATH=. .venv/bin/python -m tests.attester_packets --node <node_id> \
    --packets local_only/scratch/attest117/<node_id>.packets.json \
    --key     local_only/scratch/attest117/<node_id>.key.json

# render the Attester-facing text VERBATIM (never retype a stem)
PYTHONPATH=. .venv/bin/python -c "
import json; from tests.attester_packets import render_prompt_block
b=json.load(open('local_only/scratch/attest117/<node_id>.packets.json'))
print(render_prompt_block(b['packets'] if isinstance(b,dict) else b))" \
    > local_only/scratch/attest117/<node_id>.prompt.txt

# join returned verdicts to the key mechanically
PYTHONPATH=. .venv/bin/python -m tests.attester_file \
    --packets … --key … --verdicts … --batch-prefix batch117 \
    --attested-at <ISO> --attested-by <dispatcher-assigned identity> \
    --action-provided "…" --actions <json> --tool-uses "…" --samples-delivery "…"
```

**⚠ ONE PACKET FILE PER NODE, ALWAYS.** `attester_packets.py` numbers items **per invocation**,
so concatenating several nodes into one prompt mints `item_001` several times and the join
becomes ambiguous. This is unguarded and has already caught one session out. If you dispatch
several nodes together, key the returned JSON by node filename so ids never collide.

### ▶ PRIORITY 2 — the §5 blind judgment re-reviews. Also NO re-proof. Largest queue.

All 151 filed reviews are v1 and unadjudicable; the v1→v2 migration was refused as impossible in
principle (v2 demands per-sample verdicts a v1 reviewer was never asked for, so populating them
would mean authoring judgments nobody gave). `validation_reports/judgment/` is outside the
fingerprint, so this campaign also owes no chain.

**It is 7 dispatches, not 33** — but each is far heavier per node: a §5 review owes **6 findings
plus 4 per-sample assessments** for every node, where a §6 verdict owed one answer per clause.

```sh
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --plan
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --batch 3 \
    --blind local_only/scratch/review/b3.txt --skeleton-dir local_only/scratch/review/b3/
PYTHONPATH=. .venv/bin/python -m tests.file_reviews --batch 3 --verdicts <reply.json> \
    --reviewed-by <dispatcher-assigned identity> --date <ISO> \
    --skeleton-dir local_only/scratch/review/b3/
```

Required per node: `competency_fulfillment`, `comprehensive_coverage`, `cognitive_capacity`,
`variant_comprehensiveness`, `competency_alignment`, `scale_appropriateness`, plus per sample
`mathematical_validity`, `contextual_logical_validity`, `ambiguity`, `learner_facing_clarity`.
Schema v2 only. ≤25 nodes per reviewer identity.

**⚠ TWO §5-ONLY RULES, and one is a trap that PASSES:**

* **File the samples from the DISPATCH-TIME skeleton (`--skeleton-dir`), never a rebuild at
  filing time.** `file_reviews.py`'s first version rebuilt the packet when filing — which sounds
  stricter and is the one mistake that cannot be detected afterwards. A generator fix landing
  between dispatch and filing (the NORMAL case) pairs the reviewer's verdicts with samples it
  never saw, and §5 freshness **PASSES**, because the samples really are fresh. That is a
  fabricated review with a clean bill of health, produced by the tool meant to prevent it.
* **The reviewer identity is assigned by the DISPATCHER.** Measured 2026-09-10: three
  independently dispatched blind agents given the same prompt all converged on variations of one
  self-chosen name, which would silently collapse §5 reviewer plurality and §6H attester
  plurality alike. A mismatched reply is refused.

### ▶ PRIORITY 3 — content debt. ONLY after Priority 1. Costs the full ~3.4h chain.

**57 findings across 36 nodes.** Highest-count nodes today (re-derive after Priority 1 — this
list WILL change): `mat_g3_na_q3_1`, `mat_g2_na_q4_3`, `mat_g2_na_q3_1`, `mat_g2_mg_q4_4`,
`mat_g2_mg_q2_0` at 3 each.

For each finding: **build the artifact the clause names, or delete the provider entry.** Content
Rule 4 decides which, and you must cite the competency clause either way.

* **`draw`-verb findings require a real visual formatter** (owner ruling 3). A multiple-choice
  question *about* drawing does not satisfy a competency that says draw.
* **A clause naming a medium:** decide from the competency's grammar which role it plays — the
  thing the learner must work IN (*illustrate/represent/model/draw … using X*) must actually be
  rendered; a delivery mode or story context (*given orally or in pictures*) can be satisfied by
  a worded context. Ambiguous → judge on the stricter reading and say so (owner ruling 1).
* **Never commit engineering effort to a lone CONTRADICTED.** Confirm with one more independent
  dispatch first. Inter-rater agreement is **88.1% overall, 76.5% on the hardest batch**. One
  dispatch costs minutes; a formatter costs days.

**BATCH ALL SOURCE WORK AND PAY THE CHAIN ONCE.** Order at §5 below.

---

## 4. Dispatch rules — non-negotiable

* **Owner ruling 10: use `gpt-terra` light-thinking subagents** for every blind dispatch. (Ruling
  4 said Haiku; that was written for a Claude-hosted session and its purpose was cost and
  rate-limit safety, not Haiku specifically.) Keep concurrency modest — a wave of 8 heavyweight
  dispatches once hit a session rate limit and killed 14 agents mid-flight.
* **The record must name the model that ACTUALLY judged.** `attested_by` / `reviewed_by` is the
  only thing making §6H and §5 plurality checkable. Writing `haiku` on a `gpt-terra` verdict — or
  the reverse — is a false evidentiary claim. **Existing `batch115`/`batch116` records correctly
  say Haiku because Haiku judged them; do not "normalise" them.**
* **Blindness is a prompt contract, not a sandbox.** A dispatched subagent has tools. Record
  `samples_delivery` and `tool_uses_by_attester` as what they actually were. `--tool-uses 0`
  claims structural blindness a tool-bearing subagent does not have.
* **Never encode the answer in the dispatch prompt.** Give the prevalence standard and the medium
  test as a *decision procedure*, never as a conclusion. A session that asserted "any medium
  clause needs the medium present" got honest answers to the wrong question.
* **Use `legacy_review_queue.json` to PRIORITISE, never as evidence.** A v1 `PASS` records only
  that somebody once wrote PASS.
* **Audit an all-PROVIDED batch before filing**: count distinct reasoning skeletons (§6G allows 3
  per cluster) and cross-check every PROVIDED whose clause names a visual medium against whether
  its samples actually rendered one. `template_attestation` is a live, DETECTED mutation for
  fill-in-the-blank verdicts.

**⚠ CROSS-FAMILY COMPARISON IS UNMEASURED.** The 88.1% figure is Haiku-against-Haiku. `gpt-terra`
is a different rater *family*. A `gpt-terra` NOT_PROVIDED landing against a Claude-era PROVIDED is
**not, on its own, a regression** — nothing currently separates a genuine finding from a family
effect. Say so in your handoff, and do not silently attribute movement to the pipeline.

---

## 5. If you land source work — the chain, in order

```sh
# 1. Scan all 152 mutation anchors. Two seconds versus a fifty-minute abort at 54/152.
PYTHONPATH=. .venv/bin/python -c "
from pathlib import Path; import tests.mutation_harness as mh
print([(m.name, r) for m in mh.MUTATIONS if m.edits for r,(f,_) in m.edits.items()
       if Path(r).read_text().count(f) != 1] or 'all anchors OK')"

# 2. Regenerate exclusions if any formatter or COMPATIBILITY entry moved. NEVER hand-edit it.
PYTHONPATH=. .venv/bin/python -m scripts.regen_formatter_exclusions

# 3. Frontend artifact (~10s)
PYTHONPATH=. .venv/bin/python tests/frontend_suite.py

# 4. Benchmark — AFTER your last source commit, or obligation_benchmark_11 is red at baseline
#    and its mutation scores INVALID rather than DETECTED.
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000

# 5. Mutation corpus (~70 min). Background it; run nothing else.
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py

# 6. SIX release shards (~2.6h). See the warning.
for i in 0 1 2 3 4 5; do
  PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier release --shard-count 6 --shard-index $i
done
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier verify-release

# 7. The Definition of Done, ALONE, output shown in full.
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
```

**⚠ THE BENCHMARK LIES ABOUT SHARD COUNT.** Step 4 prints `recommended_shards=4`.
`validate_obligations.py:165` **hard-codes `shard_count = 6`**. Follow the validator — four
receipts fail §11 on coverage. Its `projected_release` is computed from the count it recommends,
so treat it as a per-shard figure only: measured six-shard reality is ~2.57–2.59h aggregate,
worst shard ~1,580s against the 1,800s budget.

**Adding a formatter changes the obligation product**, so the pinned counts in
`tests/unit/test_obligation_executor.py` move. Confirm every added route is actually SERVED at
several seeds *before* touching those numbers. Updating a count to match reality is legitimate;
updating it to make a test pass is not.

---

## 6. Traps that have each cost a real session real time

1. **Cosmetic edits cost 3.4 hours.** Once certified, touch no source you do not mean to change.
   A session realigned four import continuation lines *after* completing the chain and invalidated
   the whole re-proof.
2. **When correcting a claim copy-pasted into prose, enumerate the sites by SWEEPING
   `mutation_proof._iter_input_files()`, never from memory.** One such correction half-landed
   twice — the claim had been written into five digest-bound places, a prompt named three, and a
   fifth was missed by two sessions running. It cost the chain twice.
3. **A gate can be defeated one stack frame later — or one ENTRY POINT over.** The orchestrator
   and the adapter enforce formatter rules differently, and the orchestrator skips its filter
   entirely for a PINNED formatter. Check a fix on BOTH paths.
4. **A rule copy-pasted into N sites will disagree with itself.** Route through the same helper
   the validator imports.
5. **A classifier keyed on a MESSAGE STRING is a latent bug.** Eligibility-versus-crash was told
   apart by message text and left ~27 node/formatter pairs wrongly advertised for weeks.
6. **A shared distractor helper can be right for arithmetic and wrong for your domain.**
   `augment_distractors` refuses negatives but allows ZERO — correct for sums, and it put a `0 g`
   option against a `1 g` answer.
7. **`git commit --amend` moves the hash**, so a ledger row written `released @ <hash>` before the
   amend points at a dangling commit. Release in a follow-up commit.
8. **The pre-commit hook rebuilds Graphify and stages `graphify-out/`.** Expect more files than
   you staged. It does not move the input digest — verify rather than assume.
9. **A surviving mutation has TWO causes** and you must distinguish them: the check is broken, or
   the plant no longer reaches the code the validator runs. Diagnose by instrumenting the real
   path, never by reading the validator and concluding it would work.
10. **`INVALID — the unmutated command baseline exited 1` is a THIRD thing** and is neither. The
    runner refused to score because the baseline was already red.

---

## 7. Known-red, known-blocked — do not "fix" these by re-running

* **`assertion_coverage_8` (3 in 1 family)** is the §6F mutation cluster
  (`contradicted_attestation`, `attestation_drops_options`, `attestation_leaks_into_phase1`).
  Their baseline command is `capability_phase2`, which is red, so the runner refuses to score
  them. **Only `capability_phase2` reaching 0 clears this.** Do not spend 70 minutes re-running
  the corpus expecting movement.
* **The supersession defect is UNFIXED — only its findings were cleared.**
  `_attestation_staleness` counts a verdict on a capability nothing consults as live ownership.
  Any future grade whose `requires_ignore` grows, or any `requires` id renamed after attestation,
  reproduces it. The scaling fix — disregard non-consulted pairs — is **the owner's call**, and
  owes a named mutation plus a contract row. Do not implement it unilaterally.
* **Retiring a record PROMOTES the previous holder of its orphan pair.** Retirement is iterative;
  it once took 4 rounds and 13 records. Re-measure after every round.

---

## 8. Bookkeeping before you finish

* **Evidence section in `validation_reports/HARDENING_EVIDENCE.md`**: exact commands, verbatim
  pass/fail output, seeds for anything found. Without it the task is not done.
* **Update `H-06`'s row** surgically; `git diff --numstat` must show only what you intended.
  Release the lock in a **follow-up** commit (trap 7).
* **Close your intent** with `tests/tree_state.py --complete`.
* **Bring `HANDOFF_PROMPT.md` current** — refresh the expected-digest block and put your banner
  at the top, demoting the previous one to "(historical)". That file and the evidence log are
  outside `INPUT_ROOTS`; verify with `input_digest()` rather than assuming.
* **Any new artifact under `validation_reports/phase2_hardening/` must be claimed by some row's
  `proof_artifacts`**, or `hardening_status.py` fails by name.

---

## 9. Not yours

* **Opening an `H-11` row.** The owner has already refused one; ruling 6 keeps all three
  workstreams under `H-06`.
* **The supersession fix** (§7) and **`CSI-R1`–`CSI-R3`** — open owner rulings.
* **Release promotion / `H-09`** — explicitly out of scope for this plan.
* **Editing `requires` / `requires_ignore`** beyond what an owner ruling authorises. It is
  human-authored ground truth, locked in `data/skeletons/requires_ignore.lock.json`, and the lock
  moves in the same commit as any sanctioned change. Never edit it merely to make a finding go
  away: the test is whether MATATAG wrote "or"/"e.g.", which is a reading of the competency text
  you must quote.
* **Splitting H-08's intro-surface render gap into its own row** — the owner's call.

If you find something genuinely broken outside your scope, **name it in the evidence log and your
report rather than fixing it.**

---

## 10. What success looks like

You will almost certainly **not** reach `run_all` exiting 0 this session — the content queue is
large and the §5 queue is 151 nodes. That is expected. A good session:

1. Leaves the tree **CERTIFIED** with `tests/tree_state.py` exit 0 and the ledger PASSing.
2. Moves at least one queue by a **measured** amount, each stage measured ALONE.
3. Files every verdict through the dispatch machinery, with truthful identities, and **authors
   none**.
4. Records what it measured, what it assumed, and what it left — including any limitation it
   discovered — so the next session inherits numbers it can trust rather than confident wrong
   ones.

**Read, in this order:** `CLAUDE.md`; `docs/phase2_hardening_completion_plan.md`'s
`START HERE — handoff` (its dated blocks supersede everything below them, owner rulings 1–10
included); the middle of that plan for the *design* of whatever you implement; and the
2026-09-21/22 entries in `validation_reports/HARDENING_EVIDENCE.md` for how the current numbers
were obtained and what was measured rather than assumed.
