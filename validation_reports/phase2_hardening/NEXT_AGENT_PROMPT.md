# Task prompt — continue Phase 2 hardening (GPT-hosted session)

**Refreshed wave 4, 2026-09-24.** Four more `gpt-5.6-luna`/medium reviews were filed:
`mat_g1_mg_q2_2`, `mat_g1_mg_q4_0`, `mat_g1_mg_q4_1`, `mat_g1_mg_q4_2`. The legacy queue moved
**141 → 137** (`schema_counts {2: 14, None: 137}`), and `validate_judgment_reviews()` measured
**1428 findings across 150 nodes**. New bugs queued include weekday/month competencies only asking
isolated before/after pairs instead of full ordered lists, malformed date-chart hints without a
printed chart, and more decorative interest wrappers on rotation/turn tasks.

**Refreshed again 2026-09-24 by `codex-h06-s5-luna-campaign-2-2026-09-24`.** Eight more
`gpt-5.6-luna`/medium reviews were dispatched and filed: `mat_g1_dp_q3_1`, `mat_g1_dp_q3_2`,
`mat_g1_dp_q3_3`, `mat_g1_mg_q1_0`, `mat_g1_mg_q1_1`, `mat_g1_mg_q1_2`, `mat_g1_mg_q2_0`,
`mat_g1_mg_q2_1`. The legacy queue moved **149 → 141** (`schema_counts {2: 10, None: 141}`), while
`validate_judgment_reviews()` moved **1238 → 1391** because the fresh reviews found real content
defects. New bugs queued for source work include pictograph packets/rendering as `BarChart` or
omitting symbol counts, table-from-pictograph rows blank despite nonzero answers, under-specified
triangle composition, unverifiable ruler-measure geometry, and shorter-distance hints saying the
correct shorter value is "longer." Everything below is historical unless this banner or a later
executed command supersedes it.

**Refreshed 2026-09-24 by `codex-h06-s5-luna-campaign-2026-09-24`.** One required GPT-host
`gpt-5.6-luna`/medium blind review was dispatched and filed for `mat_g1_dp_q3_0`
(`blind-reviewer-gpt-5.6-luna-medium-b1n1-20260924`). It was valid schema v2 and moved the legacy
queue **150 → 149** (`schema_counts {2: 2, None: 149}`), but it found current content concerns, so
`validate_judgment_reviews()` moved **1236 → 1238** and still reports 150 nodes with §5 findings.
The new bug to preserve for the content batch: seeds 701 and 702 add irrelevant interest wrappers
("dance shoes" on a fruit interview; "basketballs" on a shoes interview), producing contextual
validity and learner-facing clarity CONCERNs. The §5 v2 corpus is now mixed-family: 1 Haiku node
(`mat_g3_na_q4_7`) and 1 `gpt-5.6-luna` medium node. Disk measured **2.1 GiB free**; do not run
corpus/shards without resolving disk pressure. Everything below is the previous prompt except where
an executed command above supersedes it.

**Written 2026-09-24, replacing every previous version of this file.** You are working in
`/Users/enrichmentcap/Documents/antigravity/ccmed` on the Adaptive K-12 Mastery Engine's
practice-problem-generator hardening. Your job is to move `run_all` toward exiting 0.

`CLAUDE_AGENT_PROMPT.md` beside this file is the same task written for a Claude Code session. **This
file supersedes it for you**, because the dispatch model differs. Where they disagree, follow this
one — except on a measured number, where an executed command beats both.

The tree was **CERTIFIED** before the current campaign intent. The previous session opened the §5
campaign and fixed the gate that was blocking it. **149 schema-v1 nodes remain owed**; one additional
schema-v2 node (`mat_g1_dp_q3_0`) is freshly reviewed but red on content concerns. That queue is your
main job and it costs no re-proof chain as long as you touch no source.

---

## 0. THE MODEL YOUR REVIEWERS MUST USE — owner instruction, 2026-09-24

**Every blind reviewer subagent you dispatch must be `gpt-5.6-luna` at MEDIUM thinking.** This is the
owner's instruction of 2026-09-24 and it supersedes ruling 10's `GPT-5.6-Terra` for this campaign.
Ruling 4 (`Haiku subagents extend to ALL agents reviewing sample pg output`) is a Claude-host rule and
does not bind you.

Three things follow, and none is optional:

1. **The reviewer identity must name the model that ACTUALLY judged.** Use the established shape, e.g.
   `blind-reviewer-gpt-5.6-luna-medium-b1-20260924`. `reviewed_by` is the only thing that makes §5
   reviewer plurality checkable, so writing one model's name on another's verdict is a false
   evidentiary claim, not a tidy-up.
2. **Never claim a model you did not dispatch.** Do not write `haiku`, `haiku45` or `gpt-5.6-terra`
   onto a Luna verdict. **Existing records naming `gpt-5.6-terra` or `haiku45` are truthful — do not
   normalise them.**
3. **Record the thinking level too**, in the identity or in `--samples-delivery`. "Medium" is part of
   what produced the verdict, and ruling 9 already proved that changing the standard changes the
   answer; changing the reasoning budget plausibly does too.

### ⚠ THE RATER-FAMILY CONSEQUENCE — record it, do not silently absorb it

The §5 v2 corpus is **one review deep and currently single-family**: `mat_g3_na_q4_7`, judged
2026-09-24 by `haiku45-s5-reviewer-a-2026-09-24`. Dispatching Luna makes the corpus **mixed-family
from your first filing.**

Measured agreement, on the same 18 clauses with the standard held fixed:

```
cross-family  (Haiku vs GPT-5.6-Terra):  11/18 = 61.1%
within-family (Haiku vs Haiku):          37/42 = 88.1%
```

`gpt-5.6-luna` is a **third** family and its agreement with either is **unmeasured**. So:

* **State the mixture plainly** in your `HARDENING_EVIDENCE.md` entry: 1 node Haiku, N nodes
  gpt-5.6-luna-medium.
* **Flag `mat_g3_na_q4_7`** as the one node a future consistency pass should re-judge under Luna if
  single-family is ever wanted.
* **Do NOT re-review or discard it to force uniformity.** It is a genuine, fresh, verified v2 review
  and ruling 2 protects it. Re-dispatching it would also be wasted work — see the batch-7 trap in §4.
* If you can cheaply do so, **measure Luna-vs-Haiku agreement on that one node's 18 clauses** and
  record the number. The corpus currently cannot state its own inter-family agreement, and since
  ruling 9 made the standard a variable, that provenance matters.

---

## 1. Ground rules you may not break

Read `CLAUDE.md` / `AGENTS.md` first — the Scaling Mandate, Engineering Protocols and Definition of
Done are binding. The ones that bite hardest here:

1. **Verification is execution.** Never state what a command will do; run it and quote the verbatim
   output. **If you did not run it, write "not measured"** rather than characterising it. A previous
   session wrote "`run_all` is still expected to exit 1" without running it; there were four red
   stages, not three, because its own work had broken §0.
2. **Never weaken a check to make it pass.** If a gate is red the bug is in the pipeline. The only
   exception is documented ground-truth error, reported with node id and justification.
3. **You never author a Reviewer or Attester verdict.** Blind evidence comes from a dispatched agent
   that has neither the answer key nor your context. If a step seems to require you to judge rendered
   student content yourself, **stop — you have misread it.**
4. **Prove a check by executing a planted violation**, and prove it is caught for the right reason:
   neuter the gate until the mutation SURVIVES, then restore byte-identical and confirm with `cmp`.
5. **Content Rule 4 governs content decisions.** If a competency names a verb, model or range the
   pipeline cannot produce, building it **is the fix**; if the competency does not name it, building
   it is invention and is forbidden. **Quote the clause** either way.
6. **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
   `validation_reports/HARDENING_EVIDENCE.md`.

**Invocation:** always `PYTHONPATH=. .venv/bin/python …`. There is no usable bare `python` and no
`timeout` on this host. The fast unit suite takes ~11 minutes; pass `-m "not slow"` explicitly, or two
15–40 minute pool tests run too.

---

## 2. Before any heavy run: disk, and one agent at a time

### ⚠ The disk is tight

```sh
df -h /System/Volumes/Data
```

At handoff: **~3.3 GiB free of 112 GiB.** It was 295 MiB before the last session reclaimed 2.5 GB
from regenerable caches (`pip`, `Homebrew`, `puccinialin`, `vscode-cpptools`, `com.apple.python`,
`node-gyp`). There is little left to reclaim inside this repo family, which is only 3.9 GB of the
92 GB used. **If free space is under a few GB, stop and tell the user** before a corpus or shard run:
a run that dies on ENOSPC produces failures that look exactly like harness defects, and a truncated
proof is worse than none. **Do not delete worktrees or files you did not create — ask.**

Deliberately left alone, and NOT yours to clear: `ms-playwright` + `ms-playwright-go` (677 MB;
`requirements.txt` lists playwright), `aws` (381 MB; `cli/cache` holds SSO tokens), `Google`
(browser profile), and the 19 sibling `ccmed-hardening-*` worktrees (909 MB, the user's branches).

### Only one agent in this repository

```sh
ps -eo pid,ppid,etime,command | grep -iE "mutation_harness|obligation_executor|validate_|pytest" | grep -v grep
```

Empty, or stop and resolve it first. On 2026-09-23 two agents ran the mutation corpus concurrently;
**four planted bugs escaped into source and two reached commits**, including `"is_correct": False` in
the API route, which rejects every student answer. The mutation harness works by planting a real bug
into real source and restoring it, so while it runs production source is *supposed* to be transiently
modified — a second party "tidying up" `git status` reverts a live plant.

Rules that incident bought, all still binding:

1. **NEVER `git add -A` in this repo.** Stage the paths you edited, by name. Both committed plants
   entered exactly this way. The pre-commit hook rebuilds Graphify and stages `graphify-out/` itself,
   so expect more files than you staged — which is precisely why you stage by name.
2. **Check for plants with git, not a marker phrase** (they differ: `# planted mutation`,
   `// planted emission drift`, `// planted degenerate visual` — three greps, three different misses):
   ```sh
   git status --porcelain -- backend/ tests/ scripts/ data/ frontend/src \
       docs/pgen_contract.md docs/testing_pipeline.md
   git grep -n -E "#\s*planted mutation|//\s*planted " HEAD -- backend/ frontend/src \
       | grep -v mutation_harness      # HEAD must be clean
   ```
   The bare word "planted" appears in legitimate prose throughout the validators. Match the comment
   markers, not the word.
3. **`pkill -f mutation_harness` may not stop a run** — the parent can appear as `Python -` and match
   nothing. Kill the parent by pid from the `ps` output.
4. **The kill-safety marker is per invocation** (`MUTATION_IN_FLIGHT-<pid>-<uuid4>.json`). If the
   harness exits with `FATAL: another mutation run is live and has a plant in the tree right now`,
   **that is the guard working.** Do not delete the marker and do not revert the file; find that pid,
   let it finish or kill it, then re-run — recovery restores its plant automatically.
5. **A jump in the INVALID count is a statement about your ENVIRONMENT, not the tree.** Three INVALID
   is the known §6F cluster. A contended run once reported nineteen.

### ⚠ Never pipe a long run through `tail -N`

`tail` holds the **entire** stream until the pipeline ends, so a 70-minute mutation corpus writes
NOTHING to its log until it finishes — and any watcher on that file is structurally incapable of
firing. The last session briefly read that silence as "no survivors yet"; it was no visibility at all.
`tail` also **masks the exit code**, because the pipeline reports `tail`'s status, so a red `run_all`
piped that way looks like exit 0.

**Use `| tee <log>`, read the exit code from the process, and check liveness with `ps`.** If you did
not observe an exit code, quote the harness's own verdict line (`SOME ALL TESTS CHECKS FAILED`,
`failed=3`) instead of a number you did not see.

Related host quirk: **`du -sh -d 1` is invalid on macOS BSD `du`** (`-s` and `-d` conflict). It prints
a usage message to stderr and nothing to stdout, so a disk survey piped to `sort` silently reports
nothing. Use `du -h -d 1`.

---

## 3. Establish state

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
```

**Expected:**

```
PASS tree_state: CERTIFIED
  live input digest : 126e9eb19a1122bc
  worktree          : clean
  mutation_proofs         fresh  162 file(s)
  release_shards          fresh  6 file(s)
  obligation_benchmark    fresh  1 file(s)
  frontend_static_render  fresh  1 file(s)

PASS hardening_status: 10 H-row(s) valid — 3 closed, 6 open, 1 out_of_scope
```

HEAD should be at or after `ccc7d3c1`; `H-06`'s owner line reads `released @ 9c4f26f9` and is
unclaimed. **If a command disagrees with this file, believe the command** and say so before
continuing. (The previous session was handed a prompt whose expected digest was two commits stale;
the command was right and the prompt was wrong.)

**CERTIFIED means: do NOT re-run the chain.** It proves nothing new. Any edit under `INPUT_ROOTS`
(`backend/app`, `tests`, `scripts`, `data`, `frontend/src`, plus `docs/pgen_contract.md`,
`docs/testing_pipeline.md` and the frontend package manifests) makes every artifact stale and costs
the full ~4h chain (§6). **`validation_reports/` is OUTSIDE `INPUT_ROOTS`**, which is why the §5
campaign moves no digest. Verify with `input_digest()` rather than assuming — note `tree_state`
prints only the first 16 chars:

```sh
PYTHONPATH=. .venv/bin/python -c "
from backend.app.practice_gen.validation.mutation_proof import input_digest
print(input_digest()[:16])"
```

### Claim the lock and record intent

`H-06`'s `owner` line is the work-lock. Change **only that line** — a whole-file `json.dumps`
renormalises `§`/`—` escapes across rows you do not own and once produced 16 lines of collateral
churn. A `sed` of the single line is safest; if you must round-trip the JSON, first prove your writer
is byte-stable (`json.dumps(d, indent=2, ensure_ascii=False) + "\n"` reproduced the file exactly on
2026-09-24 — verify, don't assume). **`git diff --numstat` must read `1 1`.** Commit it by name, then:

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin campaign \
    --session "<your-session-id>" --note "what you are doing"
```

`campaign` for §5 dispatch work (no re-proof owed), `batch` for source edits, `chain` for re-proof.
Close with `tests/tree_state.py --complete --note "where you got to"`. Release the lock in a
**follow-up** commit — `git commit --amend` moves the hash, so a row written `released @ <hash>`
before an amend points at a dangling commit.

---

## 4. Measured state — executed 2026-09-24 at `126e9eb19a1122bc`, ALONE

```
$ PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
  FAIL       assertion_coverage_8           phase 1     1.1s
  FAIL       judgment_reviews_5             phase 2   140.5s
  FAIL       capability_phase2              phase 2    24.0s
  scheduled=17 completed=14 failed=3 crashed=0 not_run=0 incomplete=0
  SOME ALL TESTS CHECKS FAILED.
```

| stage | count | nature |
|---|---|---|
| `judgment_reviews_5` | **1237** at `run_all` / **1236** at `validate_judgment` | **150 nodes** still schema v1 — your queue |
| `capability_phase2` | **173** CONTRADICTED across 82 of 151 nodes | content debt — source work, costs the chain |
| `assertion_coverage_8` | 3 in 1 family (plus `mutation_proof_integrity_8` 9 in 3 families — the same three records) | the §6F cluster; **only `capability_phase2` reaching 0 clears it** |

Mutation corpus: **159/162**, the only misses being the three §6F-cluster INVALIDs
(`contradicted_attestation`, `attestation_drops_options`, `attestation_leaks_into_phase1`), whose
baseline command `capability_phase2` is red so the runner refuses to score them. Six release shards
`failures=0`, worst 1,586s of the 1,800s budget. Benchmark `failures=0`. Frontend 41/41.

> **Always quote the ENTRY POINT with a §5 figure.** `run_all`'s stage appends one aggregate rollup
> the module CLI never emits, so the two differ by exactly one. Both are correct. This is **not**
> concurrency pollution — an earlier session diagnosed it as such and wrote that into the plan as
> fact. Settled; do not re-open it.
>
> **The module CLI prints only the first 10 findings.** To see all of them (~140s):
> ```python
> from backend.app.practice_gen.validation.validate_judgment import validate_judgment_reviews
> problems = validate_judgment_reviews()   # list[str]
> ```
> **`wc -l` on that output undercounts by one** — the findings are joined with `\n` and the last line
> carries no trailing newline. Count in Python.

---

## 5. PRIORITY 1 — the §5 blind re-reviews. 150 nodes. No re-proof owed.

150 nodes still carry schema-v1 reviews, which are unadjudicable by construction; the v1→v2 migration
was refused as impossible in principle, so each owes a fresh blind review.
`validation_reports/judgment/` sits outside the input digest, so **this campaign moves no digest and
the tree stays CERTIFIED** as long as you touch no source.

### The tooling — read `--help`, the flags changed

```sh
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --help
PYTHONPATH=. .venv/bin/python -m tests.file_reviews --help
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --plan
```

Dispatch side (`judgment_batches`): `--batch` / `--node`, `--blind` (reviewer-facing text),
`--prompt` (the complete reviewer prompt), `--reviewed-by` (the identity YOU assign),
`--verdicts-path`, `--skeleton-dir`.

Filing side (`file_reviews`), **all required**: `--verdicts`, `--reviewed-by`, `--date`,
`--skeleton-dir`, `--dispatch-prompt`, `--dispatch-id`, `--samples-delivery`,
`--tool-uses-by-reviewer`. `--batch N` for a plan batch, or `--nodes <file>` for a repair set that
does not line up with one.

**Do ONE node end-to-end first** — dispatch → reply → audit → file → re-run `validate_judgment` and
confirm that node's findings changed exactly as expected — before any wave. The last session did this
and it is how the false-positive gate was found.

### ⚠ THE BATCH-7 TRAP

`batches()` is a **static partition of all 151 registered nodes**, sorted and fixed-size — it is NOT a
live "owed" list. So:

* **batches 1–6 are exactly the 150 nodes you owe.**
* **batch 7 is `mat_g3_na_q4_7`, which is already filed, fresh and PASSing.** Dispatching it would
  re-review a current node and overwrite a genuine verified review. **Do not dispatch batch 7.**

**The plan is an ownership partition, NOT a safe one-turn dispatch size.** A §5 review owes 6 findings
plus 4 per-sample assessments for every sample plus one clause verdict per requirement; batch 1 alone
needs ~2,044 per-sample reasons, beyond one model turn. **Split by response volume** — use `--node`
for one node and `--nodes <file>` when filing a set. Keep **≤25 nodes per reviewer identity**
(`validate_judgment._MAX_NODES_PER_REVIEWER`) and give every dispatch its own identity.

### ⚠ §5 rules, the first of which is a trap that PASSES

* **File from the DISPATCH-TIME skeleton (`--skeleton-dir` as used at dispatch), never a rebuild at
  filing time.** `file_reviews.py`'s first version rebuilt the packet when filing — which sounds
  stricter and is the one mistake that cannot be detected afterwards. A generator fix landing between
  dispatch and filing (the NORMAL case) pairs the reviewer's verdicts with samples it never saw, and
  §5 freshness **PASSES**, because the samples really are fresh.
* **The reviewer identity is assigned by YOU, the dispatcher.** Three independently dispatched blind
  agents once converged on variations of one self-chosen name, which would silently collapse reviewer
  plurality. A mismatched reply is refused by the filer.
* **ONE PACKET FILE PER NODE.** `attester_packets.py` numbers items **per invocation**, so
  concatenating nodes mints `item_001` several times and the join becomes ambiguous. Unguarded; it has
  caught two sessions.
* **Do not file the old batch 1 or batch 2 replies** — a mechanical audit found template clustering
  and verbatim cross-node rationale reuse. They were rejected; they stay rejected.
* **Blindness is a prompt contract, not a sandbox.** A dispatched subagent has tools. Record
  `--samples-delivery` and `--tool-uses-by-reviewer` as what actually happened. `--tool-uses 0` claims
  a structural blindness a tool-bearing subagent does not have.
* **Never encode the answer in the dispatch prompt.** Give the standard and the medium test as a
  *decision procedure*, never a conclusion. A session that asserted "any medium clause needs the
  medium present" got honest answers to the wrong question.
* **Record the prompt you dispatched** and pass it as `--dispatch-prompt`.
* **Audit every reply mechanically before filing.** The filer enforces much of this; do not rely on it
  alone. Check: one assessment per delivered sample, distinct reasoning per sample, no cross-node
  verbatim reuse, one clause verdict per printed requirement, and cited `sample_ids` that exist. A
  blanket all-PASS is exactly what needs the closest look — but note that on a node whose items are
  genuinely identical, repeated reasoning can be *accurate* rather than templated. On 2026-09-24, 5 of
  76 duplicate strings traced to two seeds carrying the same arithmetic; that was filed and correct.

### ⚠ THE §5 QUEUE IS DEFECT DISCOVERY, NOT BOOKKEEPING

The first genuine schema-v2 review found a student-facing bug on its first try that every automated
gate had passed — **11 of 19 samples walked a pupil through addition to a value their own final hint
denied**:

```
seed 44, a SUBTRACTION item whose answer is 1/6:
  "Add only the numerators: 2 + 1 = 3."
  "Write the result over the same denominator: 3/6."
  "The answer is 1/6."
```

Fixed and gated (`fraction_hint_self_consistency`). **Expect blind reviews to surface pipeline bugs,
and queue them AS BUGS** — a finding recorded only as "review evidence to preserve" is a defect nobody
will fix. Name each one in the evidence log with node, seed and the rendered text. **Do not fix
generator source mid-campaign**: batch it (§6), or you pay the chain twice.

---

## 6. PRIORITY 2 — content debt, ONLY on confirmed findings. Costs the full chain.

**173 CONTRADICTED across 82 nodes.** They came from a campaign that moved **two variables at once** —
the ruling-9 prevalence standard AND the rater family — so the aggregate is usable but **no single row
is settled.** **Never commit engineering effort to a lone CONTRADICTED**; confirm it with one more
independent dispatch first. One dispatch costs minutes, a formatter costs days.

For each confirmed finding: build the artifact the clause names, or delete the provider entry. Content
Rule 4 decides which and you quote the clause either way. `draw`-verb findings need a real visual
formatter (ruling 3) — a multiple-choice question *about* drawing does not satisfy a competency that
says draw.

**Batch all source work into ONE batch so the chain is paid once.**

---

## 7. What the last session changed — do not re-break these

Each fix is proven by a mutation and carries a NAMED LIMIT. Read the limit before assuming coverage.

1. **`_provenance_corpus` is no longer an allowlist** (`validate_judgment.py`). It named four fields
   (`question_text`, `correct_answer`, `formatter`, `options`) while the blind packet also prints
   hints, cloze text, visual payload, the rendered visual structure and the requirement clauses — all
   of which the stored `samples_reviewed` snapshot already carried. It raised **four FALSE findings**
   against a genuine review for quoting `'denominator'` and `'numerator'` (57 and 19 occurrences in
   the packet's hints), `'similar_fractions'` (a printed requirement id) and `'fraction-part'` (a
   printed `role_counts` KEY). It punished the most valuable thing a reviewer does — quoting the hint
   text, the field the seed-44 defect lived in. It is now a recursive flatten of every scalar and
   mapping key in each stored sample, so it cannot drift as packet fields are added.
   **NAMED LIMIT:** the corpus is the stored snapshot, a superset of the printed packet for a few
   internal fields (`replay_digest`, `renderer_input_digest`), so quoting one of those field names or
   digest values is NOT caught.
   **If a reviewer's honest quote still trips this gate, the corpus is missing a printed field —
   diagnose it, do not coach reviewers away from quoting.**
2. **The "115 of 151" figure is an UPPER BOUND, not a count.** It was measured with that same narrow
   corpus, so it also counted honest quotes of hints and clauses as fabrication. The fabrication
   conclusion stands on those reviews being template all-PASS stubs, which is separately evidenced;
   only the count is unreliable. The claim lived in **six** files and all six are corrected. **If you
   quote the figure, quote the qualification with it.**
3. **`_apply` is all-or-nothing** (`tests/mutation_harness.py`). It validated one anchor and wrote that
   file before reading the next, so a multi-file plant whose SECOND anchor had moved left the FIRST
   file mutated in production source with every recovery path blind to it. Now two passes: validate
   every anchor before writing any file, then register each file in `_IN_FLIGHT` with a marker refresh
   **before** its write lands. Label `mutation_apply_is_all_or_nothing`, two mutations (one per pass).
   **NAMED LIMIT:** covers the `edits` path only — a mutation supplying `apply_fn` owns its own
   rollback and is reached by neither pass.
4. **`_legacy_review_paths` no longer counts dispatch provenance as reviews.** A bare `rglob("*.json")`
   swept in `<node dir>/.responses/<dispatch-id>.json`, so the owed-queue artifact read 151 when 150
   were owed, and **rose to 152 when a review was filed.** Both phantom "missing a v1 facet" and
   "orphan review" entries were those files. Now 150, both facets 0.
5. **`validate_judgment` sorts its findings.** A bare set intersection iterated in `PYTHONHASHSEED`
   order, so the same tree printed findings in different orders in consecutive processes and a
   before/after diff buried the 4 changed lines under ~90 reordered ones. **Sort before diffing two
   §5 runs regardless** — other emitters may still be unordered.

---

## 8. Traps, each paid for by a real session

**THE RECURRING SHAPE, across six sessions: a rule that lives in TWO places, fixed in ONE.** Before
calling anything done, ask where else this rule is written. Enumerate sites mechanically
(`mutation_proof._iter_input_files()`, `git grep`), and route behaviour through the ONE helper the
validator itself calls, never a second copy. Examples that each cost real time:

* the renderer's unique-path half and its `case_id` half — each masked the other;
* an overstated §5 claim copy-pasted into FIVE digest-bound files — a correction naming three
  half-landed, twice, costing the chain each time;
* `fractions.generate_params` taught to enact subtraction while `generate_hints` was not — so the
  moment subtraction shipped, its explanation was wrong;
* `_provenance_corpus`'s field allowlist versus the packet renderer that prints more than it lists.

1. **A campaign can rot a unit-test FIXTURE without breaking any check.** When the corpus moved
   57 → 173, two tests in `tests/unit/test_capability_contract.py` went red and neither check was
   broken. That file has rotted three times. Select attestation records by OWNERSHIP
   (`VC._winning_verdict_index`), never positionally, and assert about the specific pair under test,
   never "this node is globally clean". **Filing a review also rots
   `tests/unit/test_legacy_review_queue.py`'s artifact test** — that is real drift; regenerate with
   `PYTHONPATH=. .venv/bin/python tests/legacy_review_queue.py --write` and *check the direction the
   count moves*, which is how defect 4 above was found.
2. **Cosmetic edits cost ~4 hours.** Once certified, touch no source you do not mean to change.
3. **A gate can be defeated one stack frame later — or one ENTRY POINT over.** The orchestrator skips
   its formatter filter entirely for a PINNED formatter. Check a fix on both paths.
4. **A classifier keyed on a MESSAGE STRING is a latent bug.** One left ~27 node/formatter pairs
   wrongly advertised for weeks.
5. **A surviving mutation has TWO causes** — the check is broken, or the plant no longer reaches the
   code the validator runs — and **`INVALID — the unmutated command baseline exited 1` is a THIRD
   thing** and is neither. Distinguish by instrumenting the real path, never by re-running until green.
6. **An INVALID that vanishes when re-run alone is not automatically "contention".** A quiet
   single-agent corpus once scored seven spurious INVALIDs: a sub-second, same-length plant kept
   running from `__pycache__` after a byte-identical restore, because `.pyc` freshness is whole-second
   mtime plus size. Fixed (`d92a3875`), but the lesson generalises. If you hand-restore a file
   yourself, purge `__pycache__` too.
7. **Adding a formatter changes the obligation product**, so pinned counts in
   `tests/unit/test_obligation_executor.py` move. Confirm every added route is actually SERVED at
   several seeds *before* touching those numbers.
8. **The benchmark prints `recommended_shards=4`; `validate_obligations.py` hard-codes 6.** Follow the
   validator — four receipts fail §11 on coverage.
9. **Retiring an attestation record PROMOTES the previous holder of its orphan pair.** Retirement is
   iterative; it once took 4 rounds and 13 records.
10. **Every `§` token in `docs/pgen_contract.md` must be a `CONTRACT_CHECKS` key**, prose included —
    the doc/registry match is scanned in both directions.

---

## 9. The re-proof chain — ONLY after landing source work

Run each step as a background task, ALONE, and do nothing else heavy while it runs. Check `df -h`
first. Use `tee`, never `tail` (§2).

```sh
# 0. fast suite green BEFORE committing source (~11 min)
PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q
# commit source by name, then:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin chain --force --session "<id>" --note "..."
# 1. anchors (2 seconds, versus a 50-minute abort mid-corpus)
PYTHONPATH=. .venv/bin/python -c "
from pathlib import Path; import tests.mutation_harness as mh
print([(m.name, r) for m in mh.MUTATIONS if m.edits for r,(f,_) in m.edits.items()
       if Path(r).read_text().count(f) != 1] or 'all anchors OK')"
# 2. generated exclusions (never hand-edit its output)
PYTHONPATH=. .venv/bin/python -m scripts.regen_formatter_exclusions
# 3. benchmark — AFTER the last source commit, or obligation_benchmark_11 is red at
#    baseline and its mutation scores INVALID rather than DETECTED
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000
# 4. frontend static render — run_all does NOT regenerate it
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py
# 5. mutation corpus (~70 min). Expect 159/162+, only the §6F cluster INVALID.
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
prints CERTIFIED. **After the corpus, re-check for escaped plants (§2) before doing anything else.**

---

## 10. Known-red, known-blocked — do not "fix" by re-running

* **`assertion_coverage_8` (3 in 1 family)** and **`mutation_proof_integrity_8` (9 in 3 families)**
  are the same three §6F records. Their baseline command is `capability_phase2`, which is red, so the
  runner refuses to score them. **Only `capability_phase2` reaching 0 clears this.**
* **The supersession defect is UNFIXED — only its findings were cleared.**
  `_attestation_staleness` counts a verdict on a capability nothing consults as live ownership. The
  scaling fix is **the owner's call** and owes a named mutation plus a contract row.
* **H-02 and H-07 read `status: open` with an EMPTY `still_open` list.** Nobody has established
  whether the work is done and the status is stale bookkeeping, or the field simply is not maintained
  for those rows. **Do not assume either way** — if you need them, establish it by execution and
  record what you find.

---

## 11. Not yours

* Opening an `H-11` row — the owner has refused one; ruling 6 keeps all workstreams under `H-06`.
* The supersession fix (§10) and `CSI-R1`–`CSI-R3` — open owner rulings.
* Release promotion / `H-09` — out of scope for this plan.
* Editing `requires` / `requires_ignore` beyond what an owner ruling authorises. Human-authored ground
  truth, locked in `data/skeletons/requires_ignore.lock.json`; the lock moves in the same commit as
  any sanctioned change. Never edit it to make a finding go away — the test is whether MATATAG wrote
  "or"/"e.g.", a reading of the competency text you must quote.
* Discarding or re-running the `batch117`–`batch150` prevalence corpus, or the filed v2 review on
  `mat_g3_na_q4_7`. Both are verified genuine and protected by ruling 2.
* Freeing disk space by deleting worktrees or files you did not create — ask the user.
* **`.claude/worktrees/agent-aaac714fac3fe0cc6` holds uncommitted modifications to production source**
  dated Aug 10 (`backend/app/practice_gen/axes_catalog.py`, `dna/na/comparing_ordering.py`,
  `formatters/textual/fmt_true_false.py`). Abandoned work or a forgotten experiment; it needs an owner
  decision. **Do not delete it and do not merge it.**

Find something genuinely broken outside your scope? **Name it in the evidence log and your report
rather than fixing it.** A batch that grows is a batch that does not close.

---

## 12. Bookkeeping before you finish

* **Evidence section in `validation_reports/HARDENING_EVIDENCE.md`**: exact commands, verbatim
  pass/fail output, seeds for any failure, dispatch ids, reviewer identities, **and the model +
  thinking level that judged**. Without it the task is not done.
* **Update `H-06`'s row surgically** (`git diff --numstat` shows only what you intended), and release
  the lock in a **follow-up** commit.
* **Close your intent** (`tests/tree_state.py --complete`).
* **Bring this file and `HANDOFF_PROMPT.md` current** — new banner on top, previous demoted to
  "(historical)", refreshed expected-state block. Both are outside `INPUT_ROOTS`; verify with
  `input_digest()` rather than assuming.
* **Any new file under `validation_reports/phase2_hardening/` must be claimed by a row's
  `proof_artifacts`**, or `hardening_status.py` fails by name.
* **Re-check the owed-node count by execution** before you quote it. The last session wrote "149
  remain owed" in two committed docs when the true figure was 150 — filing `mat_g3_na_q4_7` removed a
  151st node carrying a stale v2 review, not one of the 150 v1 nodes. Count it:
  ```sh
  PYTHONPATH=. .venv/bin/python -c "
  from backend.app.practice_gen.validation.validate_judgment import validate_judgment_reviews
  import re
  p = validate_judgment_reviews()
  print('findings', len(p), 'nodes', len({m.group(1) for x in p if (m:=re.match(r'(mat_[a-z0-9_]+)', x))}))"
  ```

---

## 13. What success looks like

You will **not** reach `run_all` exiting 0 this session — 150 nodes owe reviews and 82 carry content
debt. A good session:

1. **Uses `gpt-5.6-luna` at medium thinking for every blind reviewer**, names it truthfully in
   `reviewed_by`, and records the mixed-family consequence (§0).
2. Moves the §5 queue by a **measured** amount: `validate_judgment` before and after, both quoted,
   with the delta attributed per node, and the entry point named.
3. Files every verdict through `file_reviews` with truthful identities and dispatch provenance, and
   **authors none**.
4. Queues every defect a reviewer finds as a named bug with node, seed and rendered text — and does
   not fix generator source mid-campaign.
5. Leaves the tree CERTIFIED (it stays certified if you touch no source — verify with
   `tree_state.py`), **or** leaves an accurate open intent saying exactly where it stopped. Owner
   ruling 3: "must end certified" is **not** the rule — an honest interrupted state beats a fabricated
   clean one.
6. Records what it measured, what it assumed, and what it left — including any limitation it
   discovered — so the next session inherits numbers it can trust rather than confident wrong ones.

**Read, in this order:** `CLAUDE.md`; this file; `HANDOFF_PROMPT.md` (its "Limitations left
standing"); `docs/phase2_hardening_completion_plan.md`'s `START HERE — handoff` for owner rulings 1–10
in full; then the most recent entries in `validation_reports/HARDENING_EVIDENCE.md`, especially
**"2026-09-24 — §5 campaign started, and the gate that was punishing honest reviewers"** and
**"2026-09-23 — lossless §5 filing repair, first genuine v2 review"**, which together show how a
review is dispatched, audited and filed.

**Where they disagree: an executed command wins, then this file, then the plan's dated blocks.**
