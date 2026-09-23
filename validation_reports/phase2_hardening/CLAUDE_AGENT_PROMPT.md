# Task prompt — continue Phase 2 hardening (fresh Claude Code session)

**Updated 2026-09-24 by `claude-h06-s5-campaign-2026-09-24`.** Priority 3 (`_apply` atomicity) is
DONE and proved. The §5 campaign is OPEN: **one node is filed and 149 remain owed** — and the gate
that was blocking it is fixed. `_provenance_corpus` was a four-field allowlist while the blind packet
prints hints, cloze text, visual payload/render and the requirement clauses, so it raised FOUR FALSE
findings against an honest review, punishing reviewers for quoting hint text — the field the seed-44
defect lived in. If you read an older copy of this file, note the owed-queue figure it quotes (151)
was itself wrong: `.responses/` provenance was being counted as reviews. **It is 150 total, 149 left.**

You are working in `/Users/enrichmentcap/Documents/antigravity/ccmed` on the Adaptive K-12 Mastery
Engine's practice-problem-generator hardening. Your job is to move `run_all` toward exiting 0.

`NEXT_AGENT_PROMPT.md` beside this file is written for a ChatGPT-hosted agent. **This file
supersedes it for you**, because the dispatch model and the tooling differ.

---

## 0. Before anything: the disk, and one agent at a time

### ⚠ The disk was FULL at handoff

```sh
df -h /System/Volumes/Data
```

At handoff: **296 MiB free** of 112 GiB. A `git worktree add` failed with `No space left on device`
mid-checkout. Most of the space is not this repo's working tree — there are 19 other registered
worktrees (`git worktree list`) plus whatever else the user keeps. **Do not delete anything you did
not create.** If there is less than a few GB free, **stop and tell the user** before any heavy run:
a corpus or shard run that dies on ENOSPC produces failures that look exactly like harness defects,
and a truncated proof or receipt is worse than none.

### Only one agent in this repository

```sh
ps -eo pid,ppid,etime,command | grep -iE "mutation_harness|obligation_executor|validate_|pytest" | grep -v grep
```

Empty, or stop and resolve it first. On 2026-09-23 two agents ran the mutation corpus concurrently;
four planted bugs escaped into source and two reached commits (including `"is_correct": False` in the
API route). Rules that incident bought, all still binding:

1. **NEVER `git add -A`.** Stage the paths you edited, by name. The pre-commit hook rebuilds Graphify
   and stages `graphify-out/` itself — expect those extra files.
2. **Check for plants with git, not a marker phrase:**
   ```sh
   git status --porcelain -- backend/ tests/ scripts/ data/ frontend/src docs/pgen_contract.md docs/testing_pipeline.md
   git grep -n -E "#\s*planted mutation|//\s*planted " HEAD -- backend/ frontend/src | grep -v mutation_harness   # must be empty
   ```
3. **`pkill -f mutation_harness` does not stop a run** — the parent shows as `Python -`. Kill the
   parent by pid.

**What changed on 2026-09-23/24:** the harness's kill-safety marker is now per invocation
(`local_only/scratch/MUTATION_IN_FLIGHT-<pid>-<uuid4>.json`). If `tests/mutation_harness.py` exits
with `FATAL: another mutation run is live and has a plant in the tree right now`, **that is the
guard working** — another run's plant is supposed to be in the tree. Do NOT delete the marker and do
NOT revert the file; find that pid, let it finish or kill it by pid, then re-run (recovery then
restores its plant automatically).

---

## 1. Ground rules you may not break

Read `CLAUDE.md` / `AGENTS.md` first — the Scaling Mandate, Engineering Protocols and Definition of
Done are binding. The ones that bite hardest:

1. **Verification is execution.** Never state what a command will do; run it and quote the verbatim
   output. If you did not run it, write "not measured".
2. **Never weaken a check to make it pass.** The one exception is documented ground-truth error,
   reported with node id and justification.
3. **You never author an Attester or Reviewer verdict.** Blind evidence comes from a dispatched agent
   that has neither the answer key nor your context. If a step seems to need you to judge rendered
   student content yourself, **stop — you have misread it.**
4. **Prove a check with a planted violation, and prove the plant is caught for the right reason:**
   neuter the test's own assertions until the mutation SURVIVES, then restore byte-identical (`cmp`).
5. **Content Rule 4:** if a competency names a verb/model/range the pipeline cannot produce, building
   it is the fix; if it does not name it, building it is invention. **Quote the clause** either way.
6. **Name every limitation in writing** — docstring, `docs/pgen_contract.md` row, and
   `validation_reports/HARDENING_EVIDENCE.md`.

**Invocation:** always `PYTHONPATH=. .venv/bin/python …`. No bare `python`, no `timeout` on this host.
The fast unit suite takes ~11 minutes; pass `-m "not slow"` if you run pytest directly.

---

## 2. Establish state

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
```

**Expected:**

```
PASS tree_state: CERTIFIED
  live input digest : 07015c154d6f6c8f
  worktree          : clean
  mutation_proofs         fresh  160 file(s)
  release_shards          fresh  6 file(s)
  obligation_benchmark    fresh  1 file(s)
  frontend_static_render  fresh  1 file(s)

PASS hardening_status: 10 H-row(s) valid — 3 closed, 6 open, 1 out_of_scope
```

HEAD should be at or after `1adf79ff`. `H-06`'s owner line reads `released @ e94d2a0d`.
**If a command disagrees with this file, believe the command** and say so before continuing.

**CERTIFIED means: do NOT re-run the chain.** It proves nothing new. Any edit under `INPUT_ROOTS`
(`backend/app`, `tests`, `scripts`, `data`, `frontend/src`, plus `docs/pgen_contract.md`,
`docs/testing_pipeline.md` and the frontend package manifests) makes every artifact stale and costs
the full ~4h chain (§6). Touch no source you do not mean to change.

### Claim the lock and record intent

`H-06`'s `owner` line is the work-lock. Change **only** that line (a `sed` of that one line — a
whole-file `json.dumps` renormalises escapes across rows you do not own). Verify with
`git diff --numstat` (expect `1 1`), commit it by name, then:

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin campaign \
    --session "<your-session-id>" --note "what you are doing"
```

`campaign` for §5 dispatch work (no re-proof owed), `batch` for source edits, `chain` for re-proof.
Close with `tests/tree_state.py --complete --note "where you got to"`.

---

## 3. Measured state — executed 2026-09-24 at `126e9eb19a1122bc`, ALONE

```
$ PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
  FAIL       assertion_coverage_8           phase 1     1.1s
  FAIL       judgment_reviews_5             phase 2   140.5s
  FAIL       capability_phase2              phase 2    24.0s
  scheduled=17 completed=14 failed=3 crashed=0 not_run=0 incomplete=0
  SOME ALL TESTS CHECKS FAILED.
```

(That run went through `| tee | tail`, so the PIPELINE's exit code was `tail`'s, not the harness's.
The verdict line and `failed=3` are quoted instead of an exit number nobody observed. Don't pipe a
long run through `tail -N` at all — `tail` holds every line until the pipeline ends, so a 70-minute
corpus writes NOTHING until it finishes and any monitor on that file is structurally unable to fire.)

| stage | count | nature |
|---|---|---|
| `judgment_reviews_5` | **1237** at `run_all` / **1236** at `validate_judgment` | **149** nodes still schema v1 |
| `capability_phase2` | **173** CONTRADICTED | content debt, 82 of 151 nodes — untouched |
| `assertion_coverage_8` | 3 in 1 family (and `mutation_proof_integrity_8` 9 in 3 families — the same three records) | the §6F cluster; only `capability_phase2` reaching 0 clears it |

Mutation corpus: **159/162**, the only misses being the three §6F-cluster INVALIDs
(`contradicted_attestation`, `attestation_drops_options`, `attestation_leaks_into_phase1`), whose
baseline `capability_phase2` is red. Six release shards `failures=0`, worst 1,586s of the 1,800s
budget.

> **Always quote the entry point with a §5 figure.** `run_all`'s stage appends one aggregate rollup
> the module CLI never emits, so they differ by exactly one. Both are correct. Settled.
>
> **The module CLI prints only the first 10 findings.** To see all of them:
> ```python
> from backend.app.practice_gen.validation.validate_judgment import validate_judgment_reviews
> problems = validate_judgment_reviews()   # list[str], ~140s
> ```
> The last session attributed the 1263→1264 move this way: the one new finding is
> `mat_g3_na_q4_7: STALE review -- the canonical learner-visible packet digest changed`, caused by the
> `ab70698a` hint fix changing exactly the hints that review judged. The freshness gate working.

---

## 4. Your job, in priority order

### ▶ PRIORITY 1 — the §5 blind judgment re-reviews. NO re-proof owed. Largest queue.

151 nodes owe a fresh schema-v2 blind review: 150 still v1 (the v1→v2 migration was refused as
impossible in principle), plus `mat_g3_na_q4_7`, now stale. `validation_reports/judgment/` sits
outside the input digest, so **this campaign moves no digest and the tree stays CERTIFIED** as long
as you touch no source.

#### ⚠ FIRST, ASK THE USER ONE QUESTION — the rater family

The only filed v2 review (`mat_g3_na_q4_7`) was judged by **GPT-5.6-Terra**, which you cannot
dispatch. You will use Haiku (owner ruling 4: "Haiku subagents extend to ALL agents reviewing sample
pg output"). Cross-family agreement was measured at only **61.1%** (11/18), within-family Haiku
**88.1%** (37/42). The v2 corpus is one review deep, so switching families now costs almost nothing.
**Recommendation: proceed with Haiku, record the mixed family in your evidence entry, and include
`mat_g3_na_q4_7` in your dispatch** (it is batch 7 and owes re-review anyway, so the corpus ends up
single-family). The previous two sessions both deferred this decision. **Put it to the user with
AskUserQuestion before your first dispatch** — do not decide it silently.

#### The tooling — read `--help`, the flags changed

```sh
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --help
PYTHONPATH=. .venv/bin/python -m tests.file_reviews --help
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --plan
```

`--plan` currently prints seven batches: six of 25 nodes and `batch 7: 1 nodes mat_g3_na_q4_7`.
**The plan is an ownership partition, NOT a safe one-turn dispatch size.** A §5 review owes 6
findings plus per-sample assessments for every sample; batch 1 alone needs ~2,044 per-sample reasons,
which is beyond one model turn. **Split by response volume** — `judgment_batches` takes `--node` for
one node, and `file_reviews` takes `--nodes <file>` for a set that does not line up with a plan batch.
Keep **≤25 nodes per reviewer identity**, and give every dispatch its own identity.

Dispatch side (`judgment_batches`): `--blind` (reviewer-facing text), `--prompt` (the complete
reviewer prompt), `--reviewed-by` (the identity YOU assign), `--verdicts-path`, `--skeleton-dir`.
Filing side (`file_reviews`), ALL required: `--verdicts`, `--reviewed-by`, `--date`,
`--skeleton-dir`, `--dispatch-prompt`, `--dispatch-id`, `--samples-delivery`,
`--tool-uses-by-reviewer`. **Start with ONE node end-to-end** (dispatch → reply → file → re-run
`validate_judgment` and confirm that node's findings changed as expected) before any wave.

#### ⚠ §5 rules, the first of which is a trap that PASSES

* **File from the DISPATCH-TIME skeleton (`--skeleton-dir` used at dispatch), never a rebuild.** A
  generator fix landing between dispatch and filing would pair the verdicts with samples the reviewer
  never saw, and §5 freshness would PASS because the samples really are fresh.
* **The reviewer identity is assigned by YOU**, and must name the model that actually judged (e.g.
  containing `haiku`). Blind agents left to name themselves once converged on one name, collapsing
  plurality. A mismatched reply is refused by the filer.
* **Do not file the old batch 1 or batch 2 replies** — template clustering and verbatim cross-node
  rationale reuse. They were rejected; they stay rejected.
* **Record the prompt you dispatched** (the `--prompt` file) and pass it as `--dispatch-prompt`.
* **Blindness is a prompt contract, not a sandbox.** A subagent has tools. Record
  `--samples-delivery` and `--tool-uses-by-reviewer` as what actually happened. Claiming 0 tool uses
  asserts a structural blindness a tool-bearing subagent does not have — report what the Agent tool
  result shows.
* **Never encode the answer in the prompt.** Give the standard and decision procedure, never a
  conclusion.
* **Expect reviews to find real bugs, and queue them AS BUGS.** The first genuine v2 review found 11
  of 19 samples walking a pupil through addition on a subtraction item — a defect every automated gate
  had passed. A finding recorded only as "review evidence" is a defect nobody fixes. Name each one in
  the evidence log with node, seed and the rendered text; do not fix source mid-campaign (§6).

#### Dispatch mechanics

* `Agent` tool with **`model: "haiku"`**. Keep concurrency modest (≤3–4 in flight); a wave of 8 Opus
  dispatches once hit the rate limit and killed 14 agents mid-flight.
* Do not claim GPT-5.6-Terra or any model you did not dispatch. Existing records naming
  `gpt-5.6-terra` or `haiku45` are truthful — do not normalise them.
* Audit each reply mechanically before filing (distinct reasoning per sample, no cross-node verbatim
  reuse). The filer enforces much of this; do not rely on it alone.

### ▶ PRIORITY 2 — content debt, ONLY on confirmed findings. Costs the full chain.

**173 CONTRADICTED across 82 nodes.** They came from a campaign that changed two variables at once
(the prevalence standard AND the rater family), so **no single row is settled**. **Never commit
engineering effort to a lone CONTRADICTED** — confirm it with one more independent Haiku dispatch
first. For each confirmed one: build the artifact the clause names, or delete the provider entry;
Content Rule 4 decides and you quote the clause. `draw`-verb findings need a real visual formatter
(ruling 3) — a multiple-choice question *about* drawing does not satisfy "draw".

Batch all source work into ONE batch so the chain is paid once, and include Priority 3 in it.

### ▶ PRIORITY 3 — DONE 2026-09-24, kept for the record

**Done.** `_apply` now runs TWO passes: pass 1 reads and validates every anchor and writes nothing,
so a moved anchor cannot leave a partial plant; pass 2 registers each file in `_IN_FLIGHT` and
refreshes the marker BEFORE its write lands, so a failure no preflight can predict (ENOSPC, a
read-only file, a kill between two writes) stays recoverable. New label
`mutation_apply_is_all_or_nothing` in `run_all.py`, its own contract row, two tests in
`tests/unit/test_mutation_killsafe.py`, and **two mutations — one per pass**, because a two-site fix
lets a single-site plant survive while proving nothing:

```
  PASS  apply_writes_before_validating_all_anchors §0 (a multi-file plant is all-or-nothing)
  PASS  apply_plants_without_registering_in_flight §0 (a planted file is recoverable before its write lands)
```

NAMED LIMIT, in the docstring and the row: this covers the `edits` path only. A mutation supplying
`apply_fn` owns its own rollback and is reached by neither pass.

---

## 5. Traps, each paid for by a real session

**THE RECURRING SHAPE: a rule that lives in TWO places, fixed in ONE.** Before calling anything done,
ask where else this rule is written. Enumerate sites mechanically
(`mutation_proof._iter_input_files()`, `git grep`), and route behaviour through the ONE helper the
validator itself calls.

1. **An INVALID that vanishes when re-run alone is not automatically "contention".** On 2026-09-23 a
   quiet, single-agent corpus scored seven spurious INVALIDs. The cause: a sub-second, same-length
   plant (`phase_ref_misassigned`, 0.88s) kept running from `__pycache__` after a byte-identical
   restore, because `.pyc` freshness is whole-second mtime + size. **Fixed** (`d92a3875`, every restore
   purges bytecode), but the lesson generalises: diagnose by instrumenting and forcing the condition
   (the evidence log shows the `os.utime` reproduction), never by re-running until green.
2. **A campaign can rot a unit-test FIXTURE without breaking any check.**
   `tests/unit/test_capability_contract.py` has rotted three times. Select attestation records by
   OWNERSHIP (`VC._winning_verdict_index`), never positionally.
3. **Cosmetic edits cost ~4 hours.** Once certified, touch no source you do not mean to change.
4. **A gate can be defeated one stack frame later — or one ENTRY POINT over.** The orchestrator skips
   its formatter filter for a PINNED formatter. Check a fix on both paths.
5. **A classifier keyed on a MESSAGE STRING is a latent bug.**
6. **`git commit --amend` moves the hash**, so `released @ <hash>` written before an amend dangles.
   Release the lock in a follow-up commit.
7. **A surviving mutation has TWO causes** (check broken, or plant no longer reaches the code), and
   **`INVALID — baseline exited 1` is a THIRD thing**. Distinguish them by executing.
8. **Adding a formatter changes the obligation product**, so pinned counts in
   `tests/unit/test_obligation_executor.py` move. Confirm each new route is SERVED at several seeds
   before touching those numbers.
9. **The benchmark prints `recommended_shards=4`; the validator hard-codes 6.** Follow the validator.
10. **Retiring an attestation record PROMOTES the previous holder of its orphan pair.** Retirement is
    iterative; it once took 4 rounds and 13 records.

---

## 6. The re-proof chain — ONLY after landing source work

Run each step as a background task, ALONE, and do nothing else heavy while it runs. Check `df -h`
first.

```sh
# 0. fast suite green BEFORE committing source (~11 min)
PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q
# commit source by name, then:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin chain --force --session "<id>" --note "..."
# 1. anchors (2 seconds, vs. a 50-minute abort mid-corpus)
PYTHONPATH=. .venv/bin/python -c "
from pathlib import Path; import tests.mutation_harness as mh
print([(m.name, r) for m in mh.MUTATIONS if m.edits for r,(f,_) in m.edits.items()
       if Path(r).read_text().count(f) != 1] or 'all anchors OK')"
# 2. generated exclusions (never hand-edit its output)
PYTHONPATH=. .venv/bin/python -m scripts.regen_formatter_exclusions
# 3. benchmark — AFTER the last source commit, or obligation_benchmark_11 scores INVALID
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000
# 4. frontend static render — run_all does NOT regenerate it
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py
# 5. mutation corpus (~70 min). Expect 157/160+ with only the §6F cluster INVALID.
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py
# 6. release shards, all six (~26 min each, ~2.6h total)
for i in 0 1 2 3 4 5; do
  PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier release --shard-count 6 --shard-index $i
done
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier verify-release
# 7. run_all, ALONE, quoted verbatim
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
```

Then commit the artifacts by name (`validation_reports/mutation_proofs`,
`validation_reports/phase2_hardening/obligation_release_shards`, `obligation_benchmark.json`,
`frontend_static_render.json`, `tree_state.json`), close the intent, and confirm `tree_state.py`
prints CERTIFIED.

---

## 7. Not yours

* Opening an `H-11` row (refused; ruling 6 keeps all workstreams under `H-06`).
* The supersession defect (`_attestation_staleness` counts a verdict on a capability nothing consults
  as live ownership) and `CSI-R1`–`CSI-R3` — open owner rulings.
* Release promotion / `H-09`.
* Editing `requires` / `requires_ignore` beyond what an owner ruling authorises (human-authored,
  locked in `data/skeletons/requires_ignore.lock.json`).
* Discarding or re-running the `batch117`–`batch150` prevalence corpus (ruling 2).
* Freeing disk space by deleting other worktrees or files you did not create — ask the user.

Find something broken outside scope? **Name it in the evidence log and your report** rather than
fixing it.

---

## 8. Bookkeeping before you finish

* **Evidence section in `validation_reports/HARDENING_EVIDENCE.md`**: exact commands, verbatim
  output, seeds, dispatch ids and reviewer identities. Without it the task is not done.
* **Update `H-06`'s row surgically** (`git diff --numstat` shows only what you intended); release the
  lock in a **follow-up** commit.
* **Close your intent** (`tests/tree_state.py --complete`).
* **Bring `HANDOFF_PROMPT.md` current** — new banner on top, previous one demoted to "(historical)",
  refresh the expected-state block. Rewrite this file too if its priorities are no longer true.
* **Any new file under `validation_reports/phase2_hardening/` must be claimed by a row's
  `proof_artifacts`**, or `hardening_status.py` fails by name.

## 9. What success looks like

You will not reach `run_all` exit 0 this session. A good session:

1. Gets the rater-family decision from the user, and records it.
2. Moves the §5 queue by a **measured** amount: `validate_judgment` before and after, both quoted,
   with the delta attributed per node.
3. Files every verdict through `file_reviews` with truthful identities and dispatch provenance, and
   **authors none**.
4. Queues every defect a reviewer finds as a named bug with node, seed and rendered text.
5. Leaves the tree CERTIFIED (if no source was touched it stays certified — verify with
   `tree_state.py`), or leaves an accurate open intent saying exactly where it stopped.

**Read, in this order:** `CLAUDE.md`; this file; `HANDOFF_PROMPT.md` (its "Limitations left
standing"); `docs/phase2_hardening_completion_plan.md`'s `START HERE — handoff` for owner rulings
1–10 in full; then the three most recent entries in `validation_reports/HARDENING_EVIDENCE.md`,
especially **"2026-09-23/24 — two harness-safety fixes"** and **"lossless §5 filing repair, first
genuine v2 review"**, which shows how the one good v2 review was dispatched and filed.

**Where they disagree: an executed command wins, then this file, then the plan's dated blocks.**
