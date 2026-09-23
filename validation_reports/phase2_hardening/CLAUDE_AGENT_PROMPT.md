# Task prompt — continue Phase 2 hardening (fresh Claude Code session)

You are working in `/Users/enrichmentcap/Documents/antigravity/ccmed` on the Adaptive K-12 Mastery
Engine's practice-problem-generator hardening. Your job is to move `run_all` toward exiting 0.

`NEXT_AGENT_PROMPT.md` beside this file is the same task written for a ChatGPT-hosted agent. **This
file supersedes it for you**, because the dispatch model and the tooling differ. Where they
disagree, follow this one.

---

## 0. Ground rules you may not break

Read `CLAUDE.md` / `AGENTS.md` first — the Scaling Mandate, Engineering Protocols and Definition of
Done are binding. The ones that bite hardest here:

1. **Verification is execution.** Never state what a command will do. Run it and show the verbatim
   output. A session once wrote "`run_all` is still expected to exit 1" without running it; there
   were four red stages, not three, because its own work had broken §0. **If you have not run it,
   say "not measured" rather than characterising it.**
2. **Never weaken a check to make it pass.** If a gate is red the bug is in the pipeline. The one
   exception is documented ground-truth error, reported with node id and justification.
3. **You never author an Attester or Reviewer verdict.** Blind evidence comes from a dispatched
   agent that has neither the answer key nor your context. If a step seems to require you to judge
   rendered student content yourself, **stop — you have misread it.**
4. **Prove a check by executing a planted violation**, not by reading the validator. And check the
   plant is not passing for the wrong reason: neuter your own gate until the mutation SURVIVES,
   then restore it byte-identical.
5. **Content Rule 4 governs content decisions.** If a competency names a verb, model or range the
   pipeline cannot produce, building it **is the fix**. If the competency does not name it,
   building it is invention and is forbidden. **Cite the competency clause** either way.
6. **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
   `validation_reports/HARDENING_EVIDENCE.md`.

**Invocation:** always `PYTHONPATH=. .venv/bin/python …`. There is no usable bare `python` and no
`timeout` on this host. The fast unit suite takes **11 minutes**; pass `-m "not slow"` explicitly
if you run it directly, or two 15–40 minute pool tests run too.

---

## 0b. ONE AGENT AT A TIME. This corrupted commits on 2026-09-23.

**Before any heavy run, confirm you are the only agent working in this repository.**

```sh
ps -eo pid,ppid,etime,command | grep -iE "mutation_harness|obligation_executor|validate_|pytest" | grep -v grep
```

Empty, or stop and resolve it first.

### Why this matters more than it sounds

The mutation harness works by **planting a real bug into real source**, running a check, and
restoring the file. While it runs, production source is *supposed* to be transiently modified. A
second party looking at `git status` sees what look like stray edits — and "tidying them up"
reverts a live plant and corrupts the run that owns it.

Two agents ran the corpus concurrently here. **Four plants escaped into the worktree and TWO
reached commits**, all in production paths — including `"is_correct": False` in the API route,
which rejects every student answer, and a duplicated MCQ option value.

### The four rules this bought

1. **NEVER `git add -A` in this repo.** A harness run one second from restoring a file will have
   its plant committed instead. **Stage the paths you edited, by name.** Both committed plants
   entered exactly this way.
2. **Do not identify plants by grepping a marker phrase.** They differ — `# planted mutation`,
   `// planted emission drift`, `// planted degenerate visual`. Three greps, three different
   misses. Ask git which INPUT_ROOTS files moved and account for every one:
   ```sh
   git status --porcelain -- backend/ tests/ scripts/ data/ frontend/src \
       docs/pgen_contract.md docs/testing_pipeline.md
   git grep -n -E "#\s*planted mutation|//\s*planted " HEAD -- backend/ frontend/src \
       | grep -v mutation_harness      # HEAD must be clean
   ```
   Beware: the bare word "planted" appears in legitimate prose throughout the validators. Match the
   comment markers, not the word.
3. **`pkill -f mutation_harness` does not stop a run.** The parent appears as `Python -` and matches
   nothing; only its children carry the name. Kill the **parent by pid** from the `ps` output.
4. **A jump in the INVALID count is a statement about your ENVIRONMENT, not the tree.** Three
   INVALID is the known §6F cluster. A contended run reported **nineteen**, which reads as sudden
   harness rot — the "red" baseline exited **0** on demand and a clean run reported **0**.

### The kill-safety marker cannot protect you

`tests/mutation_harness.py` writes `local_only/scratch/MUTATION_IN_FLIGHT.json` so a `kill -9` is
recoverable, and its docstring is right that "measuring a tree that still carries a planted bug is
worse than not measuring at all". **But `_MARKER` is a SINGLE FIXED PATH shared by every
invocation**, so a concurrent run exiting normally deletes another run's marker; that run is then
killed and its plant survives with no record.

Same defect class as `tests/frontend_renderer.py`'s fixed path, fixed under owner ruling 8 — except
this one sits inside the safety mechanism. **Fixing it is the cheapest high-value source item
available** (§3, Priority 3).

---

## 1. Establish state first

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
```

**Expected — digest `600ceb7a970a03c5`, and an intent is OPEN.** The tree is `INTERRUPTED`,
deliberately and accurately:

```
STATE tree_state: INTERRUPTED
  live input digest : 600ceb7a970a03c5
  worktree          : clean
  mutation_proofs         fresh  155 file(s)      <- FALSE GREEN, see below
  release_shards          STALE  6 file(s), 6 stale
  obligation_benchmark    fresh  1 file(s)
  frontend_static_render  fresh  1 file(s)
  OPEN INTENT       : 'chain' by 'H-06-recovery-2026-09-23'
```

`hardening_status.py` must print `PASS ... 10 H-row(s) valid — 3 closed, 6 open, 1 out_of_scope`.
`H-06` is `released @ 1ce2fbb8` and unclaimed. **If either command disagrees with this file,
believe the command** and say so before continuing.

### ⚠ `mutation_proofs fresh 155` IS A FALSE GREEN

Every record carries the right digest, so `tree_state` reports the family fresh — it cannot know
*how* they were produced. **They were produced by two agents interrupting and reverting each
other's live plants.** A record scored while its plant was reverted underneath it shows up as a
spurious `SURVIVED` — a hole in the harness that does not exist.

**Re-run the full corpus once, alone, before trusting any mutation result** and before treating
`assertion_coverage_8` as meaningful. It does not resume mid-table. Expect **151/155 or better**,
with the only survivors being the three known §6F cluster members (`contradicted_attestation`,
`attestation_drops_options`, `attestation_leaks_into_phase1`). Any other survivor is either a real
hole or contention damage — **diagnose it, do not wave it through.**

### Claim the lock and record intent

`H-06`'s `owner` line is the work-lock. Change **only** that line — a whole-file `json.dumps`
renormalises `§`/`—` escapes across rows you do not own and once produced 16 lines of collateral
churn. Verify with `git diff --numstat`.

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin chain \
    --session "<your-session-id>" --note "what you are doing"
# on completion:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --complete --note "where you got to"
```

`--begin chain` for re-proof, `--begin batch` for source edits, `--begin campaign` for dispatch
work (no re-proof owed).

---

## 2. Measured state — and what is owed

Last executed `run_all`: **EXIT 1**, `scheduled=17 completed=14 failed=3 crashed=0`.

| stage | count | nature |
|---|---|---|
| `capability_phase2` | **173** CONTRADICTED across **82 of 151 nodes** | content debt — source work |
| `judgment_reviews_5` | **1263** module / **1264** stage | 150 v1 nodes remain |
| `assertion_coverage_8` | 3 in 1 family | downstream; unfixable by re-running |

**Every one of those predates the last source batch and is owed a fresh measurement.** A number you
did not execute is not a number you may quote.

> **Always quote the ENTRY POINT with a §5 figure.** `validate_judgment` standalone and the
> `run_all` stage differ by exactly one, because `run_all.py:760-764` appends an aggregate rollup
> the module's CLI never emits. Both are correct. This is **not** concurrency pollution — an earlier
> session diagnosed it as such and wrote that into the plan as fact. Settled; do not re-open it.

### ⚠ WHAT 173 MEANS, before you plan any content work

The corpus was re-judged under owner ruling 9's **prevalence** standard (151 nodes, 767 pairs,
`batch117`–`batch150`), taking `capability_phase2` from 57 → 173. That campaign is verified genuine
— every verdict byte-identical to its dispatch, 767 distinct reasoning skeletons, prior records
preserved.

**But it moved TWO variables at once — the standard AND the rater family.** Measured on the same 18
clauses with the standard held fixed:

```
cross-family agreement (Haiku vs GPT-5.6-Terra):  11/18 = 61.1%
within-family agreement (Haiku vs Haiku):         37/42 = 88.1%
```

Disagreements ran **both directions**. So the aggregate is usable; **no individual row is settled.**
**Never commit engineering effort to a lone CONTRADICTED — confirm with one more independent
dispatch first.** One dispatch costs minutes; a formatter costs days.

### ⚠ THE §5 QUEUE IS DEFECT DISCOVERY, NOT BOOKKEEPING

The one genuine schema-v2 review filed so far found a student-facing bug on its first try that every
automated gate had passed — **11 of 19 samples walked a pupil through addition to a value their own
final hint denied**:

```
seed 44, a SUBTRACTION item whose answer is 1/6:
  "Add only the numerators: 2 + 1 = 3."
  "Write the result over the same denominator: 3/6."
  "The answer is 1/6."
```

Fixed and gated (`fraction_hint_self_consistency`). **Expect blind reviews to surface pipeline bugs,
and queue them AS BUGS** — a finding recorded only as "review evidence to preserve" is a defect
nobody will fix.

---

## 3. Your job, in priority order

### ▶ PRIORITY 1 — finish the owed chain. Nothing else is trustworthy until you do.

```sh
# 1. anchors: two seconds, versus a fifty-minute abort mid-corpus
PYTHONPATH=. .venv/bin/python -c "
from pathlib import Path; import tests.mutation_harness as mh
print([(m.name, r) for m in mh.MUTATIONS if m.edits for r,(f,_) in m.edits.items()
       if Path(r).read_text().count(f) != 1] or 'all anchors OK')"

PYTHONPATH=. .venv/bin/python -m scripts.regen_formatter_exclusions   # never hand-edit its output
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py               # ~70min, ALONE
for i in 0 1 2 3 4 5; do                                              # all six; see warning
  PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier release --shard-count 6 --shard-index $i
done
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier verify-release
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all   # ALONE, quoted verbatim
```

The benchmark and frontend artifacts are **already fresh** — do not rebuild them unless you land
source work, in which case the benchmark goes **after** your last source commit or
`obligation_benchmark_11` is red at baseline and its mutation scores INVALID rather than DETECTED.

**⚠ THE BENCHMARK LIES ABOUT SHARD COUNT.** It prints `recommended_shards=4`;
`validate_obligations.py:165` **hard-codes `shard_count = 6`**. Follow the validator — four receipts
fail §11 on coverage. Measured six-shard reality: ~2.57–2.59h aggregate, worst shard ~1,580s against
the 1,800s budget.

**Run these as background tasks and do nothing else while they run.** If a run dies, check for an
orphaned parent (`Python -`) before restarting, and re-check for plants.

### ▶ PRIORITY 2 — the §5 blind judgment re-reviews. NO re-proof owed. Largest queue.

150 nodes remain v1 and unadjudicable; the v1→v2 migration was refused as impossible in principle.
`validation_reports/judgment/` sits outside the fingerprint, so this campaign moves no digest.

**The seven-batch plan is an ownership partition, NOT a safe one-turn dispatch size.** A §5 review
owes **6 findings plus 4 per-sample assessments** per node; batch 1 alone needs 2,044 per-sample
reasons, beyond one model turn. **Split by response volume**, keeping ≤25 nodes per reviewer
identity.

```sh
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --plan
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --batch 3 \
    --blind local_only/scratch/review/b3.txt --skeleton-dir local_only/scratch/review/b3/
PYTHONPATH=. .venv/bin/python -m tests.file_reviews --batch 3 --verdicts <reply.json> \
    --reviewed-by <dispatcher-assigned identity> --date <ISO> \
    --skeleton-dir local_only/scratch/review/b3/
```

**⚠ TWO §5-ONLY RULES, and the first is a trap that PASSES:**

* **File the samples from the DISPATCH-TIME skeleton (`--skeleton-dir`), never a rebuild at filing
  time.** `file_reviews.py`'s first version rebuilt the packet when filing — which sounds stricter
  and is the one mistake that cannot be detected afterwards. A generator fix landing between
  dispatch and filing (the NORMAL case) pairs the reviewer's verdicts with samples it never saw, and
  §5 freshness **PASSES**, because the samples really are fresh. A fabricated review with a clean
  bill of health, produced by the tool built to prevent it.
* **The reviewer identity is assigned by the DISPATCHER.** Three independently dispatched blind
  agents once converged on variations of one self-chosen name, which would silently collapse
  reviewer plurality. A mismatched reply is refused.

**Do not file the existing batch 1 or batch 2 replies** — mechanical audit found template clustering
and verbatim cross-node rationale reuse.

### ▶ PRIORITY 3 — the kill-safety marker fix. Small, contained, high value.

Per-invocation marker (`MUTATION_IN_FLIGHT-<pid>-<uuid4>.json`), startup recovery scanning **all**
markers, skipping those whose pid is still live. It owes a mutation targeting the **CONCURRENT**
path — a plant that only trips single-run recovery proves nothing new — plus a
`docs/pgen_contract.md` row in the same commit (Protocol 7).

Batch it with any content work so you pay the chain once.

### ▶ PRIORITY 4 — content debt, ONLY on confirmed findings. Costs the full ~3.4h chain.

**173 findings across 82 nodes.** For each: build the artifact the clause names, or delete the
provider entry; Content Rule 4 decides which and you cite the clause either way. `draw`-verb
findings need a real visual formatter (ruling 3) — a multiple-choice question *about* drawing does
not satisfy a competency that says draw.

---

## 4. Dispatch rules — you are Claude, so ruling 4 applies to you

* **Use the Agent/Task tool with Haiku** for every blind dispatch. Owner ruling 4: "Haiku subagents
  extend to ALL agents reviewing sample pg output." Ruling 10's `GPT-5.6-Terra` applies to
  **ChatGPT-hosted** sessions only — you cannot dispatch it, and you must not claim you did.
* **Keep concurrency modest.** A wave of 8 Opus dispatches once hit the session rate limit and
  killed 14 agents mid-flight.
* **The record must name the model that ACTUALLY judged.** `attested_by` / `reviewed_by` is the only
  thing making §6H and §5 plurality checkable. Writing one model's name on another's verdict is a
  false evidentiary claim, not a tidy-up. **Existing records naming `gpt-5.6-terra` or `haiku45` are
  truthful — do not normalise them.**

> **⚠ A FAMILY DECISION YOU SHOULD MAKE EXPLICITLY AND RECORD.** The single filed v2 review
> (`mat_g3_na_q4_7`) was judged by **GPT-5.6-Terra**, which you cannot dispatch. Continuing §5 with
> Haiku mixes rater families *within* the §5 corpus, and cross-family agreement is measured at only
> **61.1%**. The §5 v2 corpus is **one review deep**, so switching now costs almost nothing and
> switching at 150 would cost everything. **Recommendation: proceed with Haiku under ruling 4, note
> the mixed family in your evidence entry, and flag `mat_g3_na_q4_7` as the one review a future
> consistency pass should re-judge.** If you disagree, say so and ask — do not decide it silently.

* **ONE PACKET FILE PER NODE.** `attester_packets.py` numbers items **per invocation**, so
  concatenating nodes mints `item_001` several times and the join becomes ambiguous. Unguarded; it
  has caught two sessions.
* **Blindness is a prompt contract, not a sandbox.** A dispatched subagent has tools. Record
  `samples_delivery` and `tool_uses_by_attester` as what they actually were; `--tool-uses 0` claims
  structural blindness a tool-bearing subagent does not have.
* **Never encode the answer in the dispatch prompt.** Give the standard and the medium test as a
  *decision procedure*, never a conclusion. A session that asserted "any medium clause needs the
  medium present" got honest answers to the wrong question.
* **Record the prompt you dispatched**, beside the packets, and say where in `samples_delivery`. The
  corpus currently cannot state the wording a verdict was judged under — only the standard — and
  since ruling 9 made the standard a variable, that provenance matters.

---

## 5. Traps, each paid for by a real session

**THE RECURRING SHAPE, across five sessions: a rule that lives in TWO places, fixed in ONE.** Before
calling anything done, ask where else this rule is written.

* the renderer's unique-path half and its `case_id` half — each masked the other, so one mutation
  would have proved nothing;
* an overstated §5 claim copy-pasted into FIVE digest-bound files — a correction naming three
  half-landed, twice, costing the 3.4h chain each time;
* `fractions.generate_params` was taught to enact subtraction after a blind reviewer said it never
  was; `generate_hints` was not, so the moment subtraction shipped its explanation was wrong;
* two attestation fixtures selected records positionally while the validator selects by ownership.

**The remedy is mechanical, not attentive:** enumerate sites by sweeping
`mutation_proof._iter_input_files()`, and route behaviour through the ONE helper the validator
itself calls, never a second copy.

1. **A campaign can rot a unit-test FIXTURE without breaking any check.** When the corpus moved
   57 → 173, two tests in `tests/unit/test_capability_contract.py` went red and **neither check was
   broken**. Select attestation records by OWNERSHIP (`VC._winning_verdict_index`), never
   positionally, and assert about the specific pair under test, never "this node is globally clean".
   That file has now rotted three times.
2. **Cosmetic edits cost 3.4 hours.** Once certified, touch no source you do not mean to change.
3. **A gate can be defeated one stack frame later — or one ENTRY POINT over.** The orchestrator skips
   its formatter filter entirely for a PINNED formatter. Check a fix on both paths.
4. **A classifier keyed on a MESSAGE STRING is a latent bug.** One left ~27 node/formatter pairs
   wrongly advertised for weeks.
5. **`git commit --amend` moves the hash**, so a row written `released @ <hash>` before the amend
   points at a dangling commit. Release in a follow-up commit.
6. **The pre-commit hook rebuilds Graphify and stages `graphify-out/`.** Expect more files than you
   staged — which is exactly why you stage by name and never `-A`. It does not move the input
   digest; verify rather than assume.
7. **A surviving mutation has TWO causes** and you must distinguish them: the check is broken, or the
   plant no longer reaches the code the validator runs. Diagnose by instrumenting the real path.
8. **`INVALID — the unmutated command baseline exited 1` is a THIRD thing** and is neither.
9. **Adding a formatter changes the obligation product**, so pinned counts in
   `tests/unit/test_obligation_executor.py` move. Confirm every added route is actually SERVED at
   several seeds *before* touching those numbers.

---

## 6. Known-red, known-blocked — do not "fix" by re-running

* **`assertion_coverage_8` (3 in 1 family)** is the §6F cluster. Their baseline command is
  `capability_phase2`, which is red, so the runner refuses to score them. **Only `capability_phase2`
  reaching 0 clears this.**
* **The supersession defect is UNFIXED — only its findings were cleared.**
  `_attestation_staleness` counts a verdict on a capability nothing consults as live ownership. The
  scaling fix is **the owner's call** and owes a named mutation plus a contract row.
* **Retiring a record PROMOTES the previous holder of its orphan pair.** Retirement is iterative; it
  once took 4 rounds and 13 records.

---

## 7. Bookkeeping before you finish

* **Evidence section in `validation_reports/HARDENING_EVIDENCE.md`**: exact commands, verbatim
  output, seeds. Without it the task is not done.
* **Update `H-06`'s row** surgically; `git diff --numstat` must show only what you intended. Release
  the lock in a **follow-up** commit (trap 5).
* **Close your intent** with `tests/tree_state.py --complete`.
* **Bring `HANDOFF_PROMPT.md` current** — refresh the expected-digest block, put your banner on top,
  demote the previous one to "(historical)". It and the evidence log are outside `INPUT_ROOTS`;
  verify with `input_digest()` rather than assuming.
* **Any new artifact under `validation_reports/phase2_hardening/` must be claimed by a row's
  `proof_artifacts`**, or `hardening_status.py` fails by name.

---

## 8. Not yours

* Opening an `H-11` row — the owner has refused one; ruling 6 keeps all workstreams under `H-06`.
* The supersession fix (§6) and `CSI-R1`–`CSI-R3` — open owner rulings.
* Release promotion / `H-09` — out of scope for this plan.
* Editing `requires` / `requires_ignore` beyond what an owner ruling authorises. Human-authored
  ground truth, locked in `data/skeletons/requires_ignore.lock.json`; the lock moves in the same
  commit as any sanctioned change. Never edit it to make a finding go away — the test is whether
  MATATAG wrote "or"/"e.g.", a reading of the competency text you must quote.
* Discarding or re-running the `batch117`–`batch150` prevalence corpus, or the filed v2 review. Both
  are verified genuine and protected by ruling 2.

Find something genuinely broken outside your scope? **Name it in the evidence log and your report
rather than fixing it.** A batch that grows is a batch that does not close.

---

## 9. What success looks like

You will **not** reach `run_all` exiting 0 this session — 82 nodes carry content debt and the §5
queue is 150 nodes. A good session:

1. Leaves the tree **CERTIFIED** (`tree_state.py` exit 0) with the ledger PASSing, **or** leaves an
   accurate open intent saying exactly where it stopped. Owner ruling 3: "must end certified" is
   **not** the rule — a handoff can happen at any moment, and an honest interrupted state beats a
   fabricated clean one.
2. Moves at least one queue by a **measured** amount, each stage measured ALONE.
3. **Executes `run_all` and quotes it verbatim**, including when it is red and including the stage
   counts. If you did not run it, say "not measured".
4. Files every verdict through the dispatch machinery with truthful identities, and **authors none**.
5. Records what it measured, what it assumed, and what it left — including any limitation it
   discovered — so the next session inherits numbers it can trust rather than confident wrong ones.

**Read, in this order:** `CLAUDE.md`; **this file**; then
`validation_reports/phase2_hardening/HANDOFF_PROMPT.md` for the standing "Limitations left standing"
list; then `docs/phase2_hardening_completion_plan.md`'s `START HERE — handoff` for owner rulings
1–10 in full, and the middle of that plan for the *design* of whatever you implement; then the
2026-09-22/23 entries in `validation_reports/HARDENING_EVIDENCE.md` for how these numbers were
obtained.

**Where they disagree: an executed command wins, then this file, then the plan's dated blocks.**
