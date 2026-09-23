# Task prompt — continue Phase 2 hardening (fresh session)

You are working in `/Users/enrichmentcap/Documents/antigravity/ccmed` on the Adaptive K-12
Mastery Engine's practice-problem-generator hardening. The tree is **CERTIFIED** and the re-proof
chain is current. Your job is to move `run_all` toward exiting 0.

**Previous prompts in this file are DONE and superseded.** The ruling-9 prevalence re-dispatch and
the lossless schema-v2 filing repair are complete. Do not redo them. One genuine v2 review is filed;
continue the remaining blind queue with response-volume-sized packets.

---

## 0. Ground rules you may not break

Read `CLAUDE.md` / `AGENTS.md` first; the Scaling Mandate, Engineering Protocols and Definition of
Done are binding. The ones that bite hardest here:

1. **Verification is execution.** Never state what a command will do. Run it and show the verbatim
   output. **The last session wrote "`run_all` is still expected to exit 1" without running it.
   There were four red stages, not three — its own campaign had broken §0 and it shipped without
   knowing.** If you have not run it, do not characterise it: say "not measured".
2. **Never weaken a check to make it pass.** If a gate is red the bug is in the pipeline. The one
   exception is documented ground-truth error, reported with node id and justification.
3. **You never author an Attester or Reviewer verdict.** Blind evidence comes from a dispatched
   agent with neither the answer key nor your context. If a step seems to require you to judge
   rendered student content, **stop — you have misread it.**
4. **Prove a check by executing a planted violation**, not by reading the validator.
5. **Content Rule 4 governs content decisions.** If a competency names a verb, model or range the
   pipeline cannot produce, building it **is the fix**. If the competency does not name it,
   building it is invention and is forbidden. **Cite the competency clause** either way.
6. **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
   `validation_reports/HARDENING_EVIDENCE.md`.

**Invocation:** always `PYTHONPATH=. .venv/bin/python …`. No usable bare `python`, no `timeout`.
The fast unit suite takes **11 minutes**; pass `-m "not slow"` explicitly if you run it directly.

---

## 0b. BEFORE ANY HEAVY RUN — two hazards this environment has already produced

**1. CHECK FOR A PLANTED MUTATION LEFT IN SOURCE. Do this first, every session.**

A killed corpus run left `formatter_unreachable_on_student_path`'s plant in
`backend/app/services/orchestrator.py` — production, the student path — on 2026-09-23:

```diff
-            problem.formatter_name = formatter
+            problem.formatter_name = None  # planted mutation
```

The harness's kill-safety marker did NOT catch it, and the reason is structural: `_MARKER` is a
SINGLE FIXED PATH shared by every invocation, so a second run exiting normally deletes the first
run's marker, the first is killed, and its plant survives with no record. The next corpus run then
finds no marker and **measures a planted tree as if it were clean** — which its own docstring calls
worse than not measuring at all. Same defect class as the renderer's fixed path, inside the safety
mechanism itself.

```sh
git status --porcelain                 # expect clean; any source file you did not touch is suspect
git diff | grep -n "planted mutation"  # expect NOTHING
ls local_only/scratch/MUTATION_IN_FLIGHT.json 2>/dev/null   # a marker here means recovery is owed
```

If you find one: `git checkout --` the file, confirm `input_digest()` returns to the expected
value, and say so. **Never `git add -A` without looking at what you are adding.** Fixing the marker
properly (per-invocation path, startup scanning all markers, skipping live pids) is the first
source item available and owes a mutation targeting the CONCURRENT path.

**2. RUN HEAVY THINGS ALONE — the failure mode is not a wrong number.**

```sh
pgrep -fl "mutation_harness|obligation_executor|validate_|pytest"   # must be EMPTY first
```

On 2026-09-23 a corpus run overlapping a still-live shard loop reported **NINETEEN** mutations as
`INVALID — the unmutated command baseline exited 1`, against a documented baseline of **three**.
That reads as sudden, wide harness rot and would send you hunting a regression that does not exist.
It was contention: the "red" baseline exits **0** on demand, and a clean run reported **0 INVALID**.

**A jump in the INVALID count is a statement about your ENVIRONMENT before it is a statement about
the tree.** Three INVALID is the known §6F cluster; anything more, check what else is running.

**Also: this environment reaped four consecutive corpus runs** at different points (exit 144),
including one under `nohup`, with ~50GB free and load 2.07 — so not resource exhaustion and not a
bad mutation. If it persists for you, run the corpus outside the agent session rather than burning
attempts, and remember it does NOT resume mid-table.

---

## 1. Establish state first

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
```

**Expected — the live input digest is `600ceb7a970a03c5`, and you may find EITHER of two
states.** A source batch (the fractions hint fix, §2) landed and its re-proof chain was started;
whether it finished is something you must read, not assume.

```
PASS tree_state: CERTIFIED
  live input digest : 600ceb7a970a03c5
  worktree          : clean
  mutation_proofs         fresh  155 file(s)
  release_shards          fresh  6 file(s)
  obligation_benchmark    fresh  1 file(s)
  frontend_static_render  fresh  1 file(s)
```

**If instead you see `awaiting_reproof` or `interrupted`, the chain did not finish. Finish it
before anything else** — §5 has the order. Shards are individually resumable and each receipt
records its own digest, so re-run only the stale indices rather than all six; that is a ~2.5h
saving you get by reading digests instead of guessing. `run_all` is the last step and its result
must be quoted verbatim.

`hardening_status.py` must print `PASS ... 10 H-row(s) valid — 3 closed, 6 open, 1 out_of_scope`.

**If either command disagrees with this file, believe the command**, and say so before
continuing.

Claim the lock (`H-06`'s `owner` reads `released @ …`; change **only** that line — a whole-file
`json.dumps` renormalises escapes across rows you do not own) and record intent:

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin campaign \
    --session "<your-session-id>" --note "what you are doing"
# on completion:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --complete --note "where you got to"
```

`--begin campaign` for dispatch work (no re-proof owed); `--begin batch` for source work.

---

## 2. Measured state — every figure below was executed, not inherited

`run_all` **EXIT 1**, `scheduled=17 completed=14 failed=3 crashed=0`:

| stage | count | nature |
|---|---|---|
| `capability_phase2` | **173** CONTRADICTED across **82 of 151 nodes** | content debt — source work |
| `judgment_reviews_5` | **1263** module / **1264** stage | 150 v1 nodes remain; one genuine v2 review is substantively red |
| `assertion_coverage_8` | 3 in 1 family | downstream; unfixable by re-running |

All other stages PASS: Phase 1 capability at its floor of 5, only the three known INVALID §6F
baselines in the corpus, six shards 0 failures, operator coverage 41/41, `nodes=151`.

**The corpus is now 155 mutations** (was 154): `fraction_hints_ignore_subtraction` was added with
the hint fix in §2. **Re-measure §0, §5 and the corpus yourself** — the figures above predate the
chain that was in flight when this prompt was written, and a number you did not execute is not a
number you may quote.

> **Always quote the ENTRY POINT with a §5 figure.** `validate_judgment` standalone reports 1263;
> the `run_all` stage reports 1264 because `run_all.py:760-764` appends one aggregate rollup the
> module's CLI never emits. Both are correct. This is **not** concurrency pollution — an earlier
> session diagnosed it as such and wrote that into the plan as fact. Settled; do not re-open.

### ⚠ WHAT 173 DOES AND DOES NOT MEAN — read before planning any content work

The 2026-09-22/23 campaign re-judged the whole corpus (151 nodes, 767 pairs, `batch117`–`batch150`)
under owner ruling 9's **prevalence** standard. It is verified genuine: every verdict byte-identical
to its dispatch, 767 distinct reasoning skeletons, truthful GPT-5.6-Terra identities, prior records
preserved. `capability_phase2` went **57 → 173**.

**That rise is real but it is NOT purely "a sharper instrument".** The campaign changed **two**
variables at once — the standard AND the rater family (Claude-era → GPT-5.6-Terra). Measured on the
same 18 clauses with the standard held fixed:

```
cross-family agreement (Haiku vs GPT-5.6-Terra):  11/18 = 61.1%
within-family agreement (Haiku vs Haiku):     37/42 = 88.1%
```

Disagreements ran **both directions** (5 one way, 2 the other), concentrated on compound
measurement competencies. So GPT-5.6-Terra is not uniformly stricter — it is *differently* strict.

**Operationally:**

* The **aggregate** rests on 767 verdicts and is usable. **No individual row is settled.**
* **Never commit engineering effort to a lone CONTRADICTED.** Confirm with one more independent
  dispatch first. One dispatch costs minutes; a formatter costs days.
* A NOT_PROVIDED landing against an older PROVIDED is **not by itself a regression**.

*(Limits of that 61.1%: n=18, purposive sample, and the dispatch prompt WORDING is not stored
anywhere — only the standard, in each verdict's `action_taken` — so it is family **plus** wording.)*

---

### ⚠ THE §5 QUEUE IS NOT BOOKKEEPING — THE FIRST REAL REVIEW FOUND A SHIPPING BUG

The one genuine schema-v2 review filed so far (`mat_g3_na_q4_7`, 2026-09-23) immediately found a
student-facing defect that every automated gate had passed: **11 of 19 samples walked a pupil
through ADDITION to an intermediate their own final hint denied.**

```
seed 44, a SUBTRACTION item whose answer is 1/6:
  "When adding fractions with the same denominator, keep the denominator the same."
  "Add only the numerators: 2 + 1 = 3."
  "Write the result over the same denominator: 3/6."
  "The answer is 1/6."
```

Root cause: `fractions.generate_hints` served both operations from one branch that hardcoded
addition while printing the true `result_num`. **Fixed and gated** (`fraction_hint_self_consistency`,
`tests/unit/test_fraction_hint_consistency.py`, mutation `fraction_hints_ignore_subtraction`
DETECTED). Blast radius was measured by restoring the old behaviour and re-rendering all 11
fractions-DNA nodes: exactly 11 samples on 1 node. Contained.

**Take two things from this.** First, the §5 queue is the highest-yield work in the project right
now — one review out of 151 found a real bug on its first try, so treat the remaining 150 as
defect discovery and not as a checkbox. Second, **expect blind reviews to surface pipeline bugs,
and queue them as bugs.** A finding recorded only as "review evidence to preserve" is a defect
nobody is going to fix.

## 3. Your job, in priority order

### ▶ PRIORITY 1 — the remaining §5 blind judgment re-reviews. NO re-proof owed. Largest queue.

One genuine v2 review is filed for `mat_g3_na_q4_7`; it has 27 substantive findings and must not be
rewritten. The other 150 nodes remain v1 and unadjudicable; the v1→v2 migration was refused as
impossible in principle (v2 demands per-sample verdicts a v1 reviewer was never asked for, so
populating them would mean authoring judgments nobody gave). `validation_reports/judgment/` sits
outside the fingerprint, so this campaign moves no digest and owes no chain.

The old seven-batch plan is an ownership partition, **not a safe one-turn dispatch size**. A §5
review owes **6 findings plus 4 per-sample assessments** per node; batch 1 alone requires 2,044
per-sample reasons, beyond one model response. Split packets by response volume while keeping each
reviewer at no more than 25 nodes and assigning truthful distinct identities.

```sh
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --plan
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --batch 3 \
    --blind local_only/scratch/review/b3.txt --skeleton-dir local_only/scratch/review/b3/
PYTHONPATH=. .venv/bin/python -m tests.file_reviews --batch 3 --verdicts <reply.json> \
    --reviewed-by <dispatcher-assigned identity> --date <ISO> \
    --skeleton-dir local_only/scratch/review/b3/
```

Required per node: `competency_fulfillment`, `comprehensive_coverage`, `cognitive_capacity`,
`variant_comprehensiveness`, `competency_alignment`, `scale_appropriateness`; per sample:
`mathematical_validity`, `contextual_logical_validity`, `ambiguity`, `learner_facing_clarity`.
Schema v2 only. ≤25 nodes per reviewer identity.

**Do not file the existing batch 1 or batch 2 replies.** Mechanical audit found template clustering
and verbatim cross-node rationale reuse (batch 1: all 511 samples CONCERN; 12 oversized clusters,
13 cross-node verbatim reuses; batch 2: all 586 samples PASS; 1 oversized cluster, 22 reuses). The
lossless filer correctly rejects partial/template replies. The planner does not yet support
authenticated partial continuation; that is a named operational limitation in the evidence log.

**⚠ TWO §5-ONLY RULES, and the first is a trap that PASSES:**

* **File the samples from the DISPATCH-TIME skeleton (`--skeleton-dir`), never a rebuild at filing
  time.** `file_reviews.py`'s first version rebuilt the packet when filing — which sounds stricter
  and is the one mistake that cannot be detected afterwards. A generator fix landing between
  dispatch and filing (the NORMAL case) pairs the reviewer's verdicts with samples it never saw,
  and §5 freshness **PASSES**, because the samples really are fresh. That is a fabricated review
  with a clean bill of health, produced by the tool built to prevent it.
* **The reviewer identity is assigned by the DISPATCHER.** Measured 2026-09-10: three
  independently dispatched blind agents given the same prompt all converged on variations of one
  self-chosen name, which would silently collapse §5 reviewer plurality.

### ▶ PRIORITY 2 — content debt, ONLY on confirmed findings. Costs the full ~3.4h chain.

**173 findings across 82 nodes.** Heaviest: `mat_g2_na_q2_0` (8), `mat_g2_na_q4_3` (6),
`mat_g2_na_q1_3` (6), `mat_g3_mg_q1_4` (5), `mat_g3_dp_q3_3` (5), `mat_g3_dp_q3_2` (5).

For each: **build the artifact the clause names, or delete the provider entry.** Content Rule 4
decides which; cite the competency clause either way.

* **Confirm each finding with a second independent dispatch before building** (§2 above). At 61.1%
  cross-family agreement, roughly two in five could move.
* **`draw`-verb findings require a real visual formatter** (owner ruling 3). A multiple-choice
  question *about* drawing does not satisfy a competency that says draw.
* **A clause naming a medium:** decide from the competency's grammar which role it plays — the
  thing the learner must work IN (*illustrate/represent/model/draw … using X*) must actually be
  rendered; a delivery mode or story context (*given orally or in pictures*) can be satisfied by a
  worded context. Ambiguous → stricter reading, and say so (owner ruling 1).

**BATCH ALL SOURCE WORK AND PAY THE CHAIN ONCE.** Order in §5.

---

## 4. Dispatch rules — non-negotiable

* **Owner ruling 10: every blind dispatch goes to a `GPT-5.6-Terra` subagent on LIGHT
  THINKING.** Not a heavier reasoning setting, and not a different model — the ruling's purpose
  is a cheap, separate, blind judge, and a wave of 8 heavyweight dispatches once hit a rate limit
  and killed 14 agents mid-flight. Keep concurrency modest.
* **Name the identity for the model that actually judged, spelled out in full:**
  `blind-attester-gpt-5.6-terra-light-<batch>-<YYYYMMDD>`. The `batch117`–`batch150` records
  abbreviate this to `gpt-terra`; **that is the same model**, recorded before the name was
  restated precisely. Do not "correct" those records — they are truthful — but do not copy the
  abbreviation forward either, because rater family is now a measured variable and an
  abbreviation that drifts is how two families come to look like one.
* **The record must name the model that ACTUALLY judged.** `attested_by` / `reviewed_by` is the
  only thing making plurality checkable. **`batch115`/`batch116` correctly say Haiku because Haiku
  judged them — do not "normalise" them to GPT-5.6-Terra.** Writing either model's name on the
  other's verdict is a false evidentiary claim, not a tidy-up.
* **ONE PACKET FILE PER NODE.** `attester_packets.py` numbers items **per invocation**, so
  concatenating nodes mints `item_001` several times and the join becomes ambiguous. Unguarded;
  it has caught two sessions.
* **Blindness is a prompt contract, not a sandbox.** Record `samples_delivery` and
  `tool_uses_by_attester` as what they actually were. `--tool-uses 0` claims structural blindness
  a tool-bearing subagent does not have.
* **Never encode the answer in the dispatch prompt.** Give the standard and the medium test as a
  *decision procedure*, never a conclusion. A session that asserted "any medium clause needs the
  medium present" got honest answers to the wrong question.
* **Audit an all-PROVIDED batch before filing:** count distinct reasoning skeletons (§6G allows 3
  per cluster) and cross-check every PROVIDED whose clause names a visual medium against whether
  its samples actually rendered one.
* **Record the prompt you dispatched.** The corpus currently cannot state the wording any verdict
  was judged under — only the standard, in `action_taken`. Since ruling 9 made the standard a
  variable, save your dispatch text beside the packets and say where it is in `samples_delivery`.

---

## 5. If you land source work — the chain, in order

```sh
# 1. Scan all 152 anchors. Two seconds versus a fifty-minute abort mid-corpus.
PYTHONPATH=. .venv/bin/python -c "
from pathlib import Path; import tests.mutation_harness as mh
print([(m.name, r) for m in mh.MUTATIONS if m.edits for r,(f,_) in m.edits.items()
       if Path(r).read_text().count(f) != 1] or 'all anchors OK')"

PYTHONPATH=. .venv/bin/python -m scripts.regen_formatter_exclusions   # never hand-edit the output
PYTHONPATH=. .venv/bin/python tests/frontend_suite.py                  # ~10s
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py                # ~70 min, background it
for i in 0 1 2 3 4 5; do
  PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier release --shard-count 6 --shard-index $i
done
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier verify-release
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all   # ALONE, output shown
```

**The benchmark goes AFTER your last source commit**, or `obligation_benchmark_11` is red at
baseline and its mutation scores INVALID rather than DETECTED.

**⚠ THE BENCHMARK LIES ABOUT SHARD COUNT.** It prints `recommended_shards=4`;
`validate_obligations.py:165` **hard-codes `shard_count = 6`**. Follow the validator — four
receipts fail §11 on coverage. Its `projected_release` is derived from the count it recommends, so
treat it as per-shard only. Measured six-shard reality: ~2.57–2.59h aggregate, worst shard ~1,580s
against the 1,800s budget.

**Adding a formatter changes the obligation product**, so pinned counts in
`tests/unit/test_obligation_executor.py` move. Confirm every added route is actually SERVED at
several seeds *before* touching those numbers.

---

## 6. Traps, each paid for by a real session


**THE RECURRING SHAPE, across four consecutive sessions: a rule that lives in TWO places, fixed in
ONE.** Before you call anything done, ask where else this rule is written.

* the renderer's unique-path half and its `case_id` half — each masked the other, so one mutation
  would have proved nothing;
* an overstated §5 claim copy-pasted into FIVE digest-bound files — a correction naming three of
  them half-landed, twice, costing the 3.4h chain each time;
* `fractions`' `generate_params` was taught to enact subtraction after a blind reviewer said it
  never was; `generate_hints` was not, so the moment subtraction shipped its explanation was wrong;
* two attestation-contract fixtures that selected records positionally while the validator selected
  them by ownership.

**The remedy is mechanical, not attentive:** enumerate the sites by sweeping
`mutation_proof._iter_input_files()`, and route behaviour through the ONE helper the validator
itself calls, never a second copy.
1. **RUN `run_all`. DO NOT PREDICT IT.** See §0.1. This is the most recent failure and it hid a
   broken §0 for a whole session.
2. **A campaign can rot a unit-test FIXTURE without breaking any check.** When the corpus moved
   57 → 173, two tests in `tests/unit/test_capability_contract.py` went red. **Neither check was
   broken.** One required a node to be *globally* free of CONTRADICTED before planting its own
   entry; the other took `next(glob("*.json"))` — the FIRST filename, which with 476 records is
   almost always a **superseded** record that is legitimately not consulted for staleness.
   **This is the THIRD occurrence in that one file**; two neighbouring tests carry docstrings
   about earlier rounds. **Standing rule: select an attestation record by OWNERSHIP
   (`VC._winning_verdict_index`, the validator's own rule), never positionally, and assert about
   the specific pair under test, never about a node being globally clean.**
3. **Never re-derive a validator's rule in a test.** A first attempt at trap 2's fix re-derived
   "last file wins over a sorted glob" by hand instead of calling `_winning_verdict_index`. A rule
   copied into a second place will eventually disagree with itself.
4. **When correcting a claim copy-pasted into prose, enumerate the sites by SWEEPING
   `mutation_proof._iter_input_files()`, never from memory.** One correction half-landed twice —
   the claim was in five digest-bound places, a prompt named three, a fifth was missed by two
   sessions. It cost the chain twice.
5. **Cosmetic edits cost 3.4 hours.** Once certified, touch no source you do not mean to change.
6. **A gate can be defeated one stack frame later — or one ENTRY POINT over.** The orchestrator
   skips its formatter filter entirely for a PINNED formatter. Check a fix on both paths.
7. **A classifier keyed on a MESSAGE STRING is a latent bug.** It once left ~27 node/formatter
   pairs wrongly advertised for weeks.
8. **`git commit --amend` moves the hash**, so a row written `released @ <hash>` before the amend
   points at a dangling commit. Release in a follow-up commit.
9. **The pre-commit hook rebuilds Graphify and stages `graphify-out/`.** Expect more files than you
   staged. It does not move the input digest — verify rather than assume.
10. **A surviving mutation has TWO causes:** the check is broken, or the plant no longer reaches
    the code the validator runs. Diagnose by instrumenting the real path.
11. **`INVALID — the unmutated command baseline exited 1` is a THIRD thing** and is neither.

---

## 7. Known-red, known-blocked — do not "fix" by re-running

* **`assertion_coverage_8` (3 in 1 family)** is the §6F cluster (`contradicted_attestation`,
  `attestation_drops_options`, `attestation_leaks_into_phase1`). Their baseline command is
  `capability_phase2`, which is red, so the runner refuses to score them. **Only
  `capability_phase2` reaching 0 clears this.**
* **The supersession defect is UNFIXED — only its findings were cleared.**
  `_attestation_staleness` counts a verdict on a capability nothing consults as live ownership.
  The scaling fix is **the owner's call** and owes a named mutation plus a contract row.
* **Retiring a record PROMOTES the previous holder of its orphan pair.** Retirement is iterative;
  it once took 4 rounds and 13 records.

---

## 8. Bookkeeping before you finish

* **Evidence section in `validation_reports/HARDENING_EVIDENCE.md`**: exact commands, verbatim
  output, seeds. Without it the task is not done.
* **Update `H-06`'s row** surgically; `git diff --numstat` must show only what you intended.
  Release the lock in a **follow-up** commit (trap 8).
* **Close your intent** with `tests/tree_state.py --complete`.
* **Bring `HANDOFF_PROMPT.md` current** — refresh the expected-digest block, put your banner on
  top, demote the previous to "(historical)". Outside `INPUT_ROOTS`; verify with `input_digest()`.
* **Any new artifact under `validation_reports/phase2_hardening/` must be claimed by a row's
  `proof_artifacts`**, or `hardening_status.py` fails by name.

---

## 9. Not yours

* Opening an `H-11` row — the owner has refused one; ruling 6 keeps all workstreams under `H-06`.
* The supersession fix (§7) and `CSI-R1`–`CSI-R3` — open owner rulings.
* Release promotion / `H-09` — out of scope for this plan.
* Editing `requires` / `requires_ignore` beyond what an owner ruling authorises. Human-authored
  ground truth, locked in `data/skeletons/requires_ignore.lock.json`; the lock moves in the same
  commit as any sanctioned change. Never edit it to make a finding go away — the test is whether
  MATATAG wrote "or"/"e.g.", a reading of the competency text you must quote.
* Discarding or re-running the `batch117`–`batch150` prevalence corpus. It is verified genuine and
  protected by ruling 2.

Find something genuinely broken outside your scope? **Name it in the evidence log and your report
rather than fixing it.**

---

## 10. What success looks like

You will **not** reach `run_all` exiting 0 this session — 82 nodes carry content debt and the §5
queue is 151 nodes. A good session:

1. Leaves the tree **CERTIFIED**, `tree_state.py` exit 0, ledger PASSing.
2. Moves at least one queue by a **measured** amount, each stage measured ALONE.
3. **Executes `run_all` and quotes it verbatim** — including when it is red, and including the
   stage counts. If you did not run it, say "not measured" rather than predicting it.
4. Files every verdict through the dispatch machinery with truthful identities, and **authors
   none**.
5. Records what it measured, what it assumed, and what it left — including any limitation it
   discovered — so the next session inherits numbers it can trust.

**Read, in this order:**

1. `CLAUDE.md` / `AGENTS.md` — the Scaling Mandate, Engineering Protocols, Definition of Done.
2. **This file.** It is your task; everything below is background.
3. `validation_reports/phase2_hardening/HANDOFF_PROMPT.md` — the standing **"Limitations left
   standing"** list and the long-form trap catalogue, which this prompt deliberately does not
   duplicate. Read its TOP banner for status and treat blocks marked "(historical)" as record
   only.
4. `docs/phase2_hardening_completion_plan.md`'s `START HERE — handoff` — owner rulings 1–10 in
   full; its dated blocks supersede everything below them. Then the middle of that plan for the
   *design* of whatever you implement — design, never status.
5. The 2026-09-22/23 entries in `validation_reports/HARDENING_EVIDENCE.md` — how every number in
   §2 was obtained, and what was measured rather than assumed.

**Where they disagree, an executed command wins, then this file, then the plan's dated blocks.**
