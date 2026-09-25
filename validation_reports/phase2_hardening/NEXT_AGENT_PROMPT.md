# Task prompt — continue Phase 2 hardening (GPT-hosted session)

**Written 2026-09-25. This REPLACES every previous version of this file, including its stacked
banners.** The previous copy had accumulated eight refresh banners whose numbers contradicted its own
body — the body still said "150 nodes owed" and quoted a digest three commits stale. Every figure below
was executed on 2026-09-25 at digest `208a52406226e6d0`. If you refresh this file, **rewrite the state
section rather than stacking another banner on top of it.**

You are working in `/Users/enrichmentcap/Documents/antigravity/ccmed` on the Adaptive K-12 Mastery
Engine's practice-problem-generator hardening. Your job is to move `run_all` toward exiting 0.

`CLAUDE_AGENT_PROMPT.md` beside this file is the same task written for a Claude Code session. **This
file supersedes it for you.** Where they disagree, follow this one — except on a measured number, where
an executed command beats both.

---

## 0. THE MODEL YOUR REVIEWERS MUST USE

**Every blind reviewer subagent you dispatch must be `gpt-5.6-luna` at MEDIUM thinking.** This is the
owner's instruction of 2026-09-24 and it supersedes ruling 10's `GPT-5.6-Terra` for this campaign.

1. **The reviewer identity must name the model that ACTUALLY judged**, e.g.
   `blind-reviewer-gpt-5.6-luna-medium-<batch>-<node>-20260925`. `reviewed_by` is the only thing that
   makes §5 reviewer plurality checkable, so writing one model's name on another's verdict is a false
   evidentiary claim, not a tidy-up.
2. **Never claim a model you did not dispatch.** The corpus already contains **8 truthful `haiku45`
   records**, filed by Claude-hosted sessions that could not dispatch Luna and therefore changed the
   MODEL rather than the label. **Do not normalise them to Luna.** If you ever cannot dispatch Luna,
   do the same thing: change the model, never the label, and say so.
3. **Record the thinking level**, in the identity or in `--samples-delivery`. Ruling 9 proved that
   changing the standard changes the answer; changing the reasoning budget plausibly does too.

**The v2 corpus is already mixed-family and that is recorded, not hidden:** 25 `gpt-5.6-luna` medium,
8 `haiku45`, and 1 `gpt-6-luna` medium, truthfully labelled because this host could not dispatch
`gpt-5.6-luna`. Measured agreement on 18 clauses with the standard fixed — cross-family (Haiku vs
GPT-5.6-Terra) **11/18 = 61.1%**, within-family (Haiku vs Haiku) **37/42 = 88.1%**. Luna-vs-Haiku
agreement is **still unmeasured**; if you can cheaply measure it on a node both families have judged,
record the number. Do NOT re-review or discard existing records to force uniformity — ruling 2
protects them.

---

## 1. Ground rules you may not break

Read `CLAUDE.md` / `AGENTS.md` first — the Scaling Mandate, Engineering Protocols and Definition of
Done are binding. The ones that bite hardest here:

1. **Verification is execution.** Never state what a command will do; run it and quote the verbatim
   output. **If you did not run it, write "not measured."** A session once wrote "`run_all` is still
   expected to exit 1" without running it; there were four red stages, not three.
2. **Never weaken a check to make it pass.** If a gate is red the bug is in the pipeline. The only
   exception is documented ground-truth error, reported with node id and justification.
3. **You never author a Reviewer or Attester verdict.** If a step seems to require you to judge
   rendered student content yourself, **stop — you have misread it.**
4. **Prove a check by executing a planted violation**, and prove it is caught for the right reason:
   neuter the gate until the mutation SURVIVES, then restore byte-identical and confirm with `cmp`.
5. **Content Rule 4:** if a competency names a verb, model or range the pipeline cannot produce,
   building it **is the fix**; if the competency does not name it, building it is invention and is
   forbidden. **Quote the clause** either way.
6. **Name every limitation in writing** — docstring, `docs/pgen_contract.md` row, and
   `validation_reports/HARDENING_EVIDENCE.md`.

**Invocation:** always `PYTHONPATH=. .venv/bin/python …`. No usable bare `python`, no `timeout` on this
host. The fast unit suite takes ~12 minutes; pass `-m "not slow"` explicitly or two 15–40 minute pool
tests run too.

---

## 2. State, executed 2026-09-25

The live input digest before this review-only campaign was `208a52406226e6d0` and
`tests/tree_state.py` reported `CERTIFIED`. The campaign changed review evidence and handoff
artifacts, not generator or harness source. The campaign intent is complete; the final
post-commit certification check is recorded with the release commit. `H-06` is currently
claimed by `codex-h06-s5-gpt6luna-20260925`; release it in a follow-up commit.
Disk at campaign start: **17 GiB free** of 112 GiB. If a command disagrees with this file,
believe the command.

```
$ PYTHONPATH=. .venv/bin/python tests/legacy_review_queue.py
legacy_review_queue: 117 legacy review(s), NOT adjudicable evidence
  re-reviews owed         : 117

$ PYTHONPATH=. .venv/bin/python tests/hardening_status.py
PASS hardening_status: 10 H-row(s) valid — 3 closed, 6 open, 1 out_of_scope

$ PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
RUN_ALL EXIT CODE: 1
  PASS unit_tests (826 passed, 1 skipped, 2 deselected, 4 warnings in 736.58s (0:12:16))
  FAIL judgment_reviews (1554 problem(s) — non-PASS verdicts or incomplete reviews)
  FAIL capability_contract (Phase 2, 173 problem(s): 173 CONTRADICTED, 0 UNATTESTED, 0 STALE (§6F), 0 UNADJUDICABLE (no recorded options))
  FAIL assertion_coverage_8 (3 in 1 family)
  scheduled=17 completed=14 failed=3 crashed=0 not_run=0 incomplete=0
```

| stage | count | nature |
|---|---|---|
| `judgment_reviews_5` | **1554** at `run_all` / **1553** at the module | **117 nodes** still schema v1 |
| `capability_phase2` | **173** CONTRADICTED across 82 of 151 nodes | content debt; source work costs the re-proof chain |
| `assertion_coverage_8` | 3 in 1 family (+ `mutation_proof_integrity_8` 9 in 3 families — the SAME three records) | §6F cluster; baseline `capability_phase2` is red |

Mutation corpus **160/163**. Six release shards `failures=0`, worst 1,592s of the 1,800s budget.
Benchmark `failures=0`. Frontend 41/41. These are digest-bound artifacts at
`208a52406226e6d0`, carried forward because no input source changed.

Review corpus: **34 schema-v2 reviews**: 25 `gpt-5.6-luna` medium, 8 `haiku45`,
1 `gpt-6-luna` medium. Verdicts **12 FAIL / 15 CONCERN / 7 PASS**.
`legacy_review_queue.json` agrees independently: **117 owed + 34 excluded = 151**.
The new `mat_g1_na_q3_0` review is FAIL; §5 rose **1538 → 1553 at the module**,
all 15 added findings on that node (12 → 27). The `run_all` stage adds one aggregate
rollup, so cite the entry point with either count. A rise from a fresh review is
newly exposed content debt, not a generator regression. Seed 701's stones/stickers
wrapper mismatch and the missing concrete-model clause are queued in
`HARDENING_EVIDENCE.md`.

> For the complete module finding list (~190s), call `validate_judgment_reviews()`
> and count the returned list in Python. Its CLI prints only the first 10; `wc -l`
> undercounts output joined without a trailing newline.

---

## 3. Before any heavy run

### One agent at a time

```sh
ps -eo pid,ppid,etime,command | grep -iE "mutation_harness|obligation_executor|validate_|pytest" | grep -v grep
```

Empty, or resolve it first. On 2026-09-23 two agents ran the corpus concurrently; **four planted bugs
escaped into source and two reached commits**, including `"is_correct": False` in the API route, which
rejects every student answer. The harness plants real bugs in real source and restores them, so while
it runs production source is *supposed* to be transiently modified — a second party "tidying up"
`git status` reverts a live plant.

1. **NEVER `git add -A` in this repo.** Stage paths you edited, by name. Both committed plants entered
   exactly that way. The pre-commit hook rebuilds Graphify and stages `graphify-out/` itself, so expect
   more files than you staged — which is precisely why you stage by name.
2. **Find plants with git, not a marker phrase** (they differ: `# planted mutation`,
   `// planted emission drift`, `// planted degenerate visual`):
   ```sh
   git status --porcelain -- backend/ tests/ scripts/ data/ frontend/src \
       docs/pgen_contract.md docs/testing_pipeline.md
   git grep -n -E "#\s*planted mutation|//\s*planted " HEAD -- backend/ frontend/src \
       | grep -v mutation_harness      # HEAD must be clean
   ```
   The bare word "planted" appears in legitimate prose throughout the validators.
3. **`pkill -f mutation_harness` may not stop a run** — the parent can appear as `Python -`. Kill the
   parent by pid.
4. **The kill-safety marker is per invocation.** `FATAL: another mutation run is live and has a plant
   in the tree right now` is **the guard working.** Do not delete the marker or revert the file; find
   that pid, let it finish or kill it, then re-run — recovery restores its plant automatically.
5. **A jump in the INVALID count describes your ENVIRONMENT, not the tree.** Three INVALID is the known
   §6F cluster. A contended run once reported nineteen.
6. **Check `df -h /System/Volumes/Data`.** It was once down to 295 MiB; a run that dies on ENOSPC
   produces failures that look exactly like harness defects. **Do not delete worktrees or files you did
   not create — ask.** Off-limits: `ms-playwright` (+`-go`), `aws` (SSO tokens in `cli/cache`),
   `Google`, and the 19 sibling `ccmed-hardening-*` worktrees.

### Two invocation traps that cost real time

* **Never pipe a long run through `tail -N`.** `tail` holds the ENTIRE stream until the pipeline ends,
  so a 2-hour corpus writes nothing to its log until it finishes and any watcher on that file cannot
  fire. It also **masks the exit code** — the pipeline reports `tail`'s status, so a red `run_all` looks
  like exit 0. **Use `| tee <log>`**, capture the exit code from the process itself
  (`cmd > log 2>&1; echo "EXIT: $?"`), and check liveness with `ps`.
* **`du -sh -d 1` is invalid on macOS BSD `du`** (`-s` and `-d` conflict): usage message to stderr,
  nothing to stdout, so a disk survey piped to `sort` silently reports nothing. Use `du -h -d 1`.

---

## 4. Claim the lock and record intent

`H-06`'s `owner` line is the work-lock. Change **only that line** — a whole-file `json.dumps`
renormalises `§`/`—` escapes across rows you do not own and once produced 16 lines of collateral churn.
A `sed` of the single line is safest; if you round-trip the JSON, first prove your writer is byte-stable
(`json.dumps(d, indent=2, ensure_ascii=False) + "\n"` reproduced the file exactly on 2026-09-24 —
verify, don't assume). **`git diff --numstat` must read `1 1`.** Commit it by name, then:

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin campaign \
    --session "<your-session-id>" --note "what you are doing"
```

`campaign` for §5 dispatch (no re-proof owed), `batch` for source edits, `chain` for re-proof. Close
with `--complete --note "where you got to"`. Release the lock in a **follow-up** commit — `git commit
--amend` moves the hash, so a row written `released @ <hash>` before an amend dangles.

**If you inherit someone's open intent and their session is gone** (check `ps`), close it with a note
saying so and release the lock. A 2026-09-24 session was rate-limited mid-wave and left both held; the
row read as live work until a later session cleared it. Recover their uncommitted work first — verify
it, then commit it unchanged, and author nothing.

---

## 5. PRIORITY 1 — the §5 blind re-reviews. 117 nodes. No re-proof owed.

`validation_reports/judgment/` is outside `INPUT_ROOTS`, so **this campaign moves no digest and the
tree stays CERTIFIED** as long as you touch no source. Verify rather than assume:

```sh
PYTHONPATH=. .venv/bin/python -c "
from backend.app.practice_gen.validation.mutation_proof import input_digest
print(input_digest()[:16])"        # tree_state prints only the first 16 chars
```

### Get the owed list by execution, not from a batch plan

```sh
PYTHONPATH=. .venv/bin/python -c "
import json,glob
from backend.app.practice_gen.registry import get_all_node_ids
v2=set()
for f in glob.glob('validation_reports/judgment/*/mat_*.json'):
    if '/.responses/' in f: continue
    d=json.load(open(f))
    if d.get('schema_version')==2: v2.add(d['node_id'])
owed=[n for n in sorted(get_all_node_ids()) if n not in v2]
print(len(owed), owed[:10])"
```

**`tests.judgment_batches --plan` is a STATIC partition of all 151 registered nodes** — sorted,
fixed-size, NOT a live owed-list. Its batch 7 is `mat_g3_na_q4_7`, which is already filed and fresh;
dispatching it would overwrite a genuine verified review. Derive your work list from the command above.
Next owed nodes in order as of 2026-09-25: `mat_g1_na_q3_1` … `mat_g1_na_q3_7`, then `mat_g1_na_q4_*`.

### The tooling

```sh
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --help
PYTHONPATH=. .venv/bin/python -m tests.file_reviews --help
```

Dispatch (`judgment_batches`): `--node` (or `--batch`), `--blind`, `--prompt`, `--reviewed-by`
(the identity YOU assign), `--verdicts-path`, `--skeleton-dir`.

File (`file_reviews`), **all required**: `--verdicts`, `--reviewed-by`, `--date`, `--skeleton-dir`,
`--dispatch-prompt`, `--dispatch-id`, `--samples-delivery`, `--tool-uses-by-reviewer`. Use `--batch N`
for a plan batch or `--nodes <file>` for any other set; **one node per file works and is the shape that
has been used successfully** (it keeps `dispatch_id` per node).

**Do ONE node end-to-end first** — dispatch → audit → file → re-measure that node — before any wave.
Both gate defects found so far were found exactly that way.

### ⚠ THE DISPATCH TEMPLATE THAT WORKS — all four parts, or your replies get refused

Waves 8–9 measured this. A prompt missing any of these produces replies that `file_reviews` REFUSES, or
that file but carry findings no content fix can ever clear:

1. **A ≥60-character floor on every `reasoning` and `rationale`.** `file_reviews` hard-refuses a
   reasoning under 40 chars (`ValueError: ... reasoning is under 40 characters`). Two replies were
   thrown away for this; re-dispatched with a stated 60-char floor they came back at min 130 and 75.
2. **An exact-verbatim quoting rule.** Any text in quotation marks must be a character-for-character
   substring of the printed packet, because `_validate_quote_provenance` checks every quoted span and
   treats one it cannot find as fabricated evidence. Tell reviewers: no paraphrase, summary, elision
   (`...`), placeholder (`X`), or comma-fragment inside quotes; **when in doubt use no quotation marks
   at all** and describe the content. One node went from 8 quote findings to **0** on this instruction
   alone.
3. **Neutral interest-bank context.** `data/interest_bank.json` holds **26 curated student-interest
   themes** (sports, gaming, food, faith and others); themed names, objects and emoji are a deliberate
   product feature. Tell reviewers to judge whether theming **INTERFERES** with the mathematics or the
   clarity of the task — not whether the theme itself is appropriate. **This is context, not a
   conclusion**; reviewers must still flag a wrapper that contradicts the problem's own content.
4. **An explicit instruction to check hints against the item.** Every content defect found so far came
   from that comparison.

**Why part 3 exists.** Three independent blind reviewers on three different nodes each flagged a ✝️
emoji as a defect, and **all three were wrong**: it is the `bible` theme (`interest_id: 1`, grade band
1–10). A blind reviewer cannot read `interest_bank.json`, so it cannot tell a deliberate feature from
stray junk. Measured effect of adding the context: `mat_g1_na_q2_4` went CONCERN → PASS while still
checking every sample's arithmetic — the false finding went, the real checking stayed.
**Generalisation: a blind reviewer can adjudicate CONTENT but not INTENT.** Any finding about theming,
persona or decoration must be adjudicated by YOU against `interest_bank.json` before it is queued as a
bug. Contrast the genuine kind: a "dance shoes" wrapper on a fruit-interview problem, where the theme
contradicts the problem's own content.

### ⚠ §5 rules, the first of which is a trap that PASSES

* **File from the DISPATCH-TIME skeleton (`--skeleton-dir` as used at dispatch), never a rebuild at
  filing time.** A generator fix landing between dispatch and filing (the NORMAL case) would pair the
  reviewer's verdicts with samples it never saw, and §5 freshness **PASSES**, because the samples
  really are fresh. This is the one error that cannot be detected afterwards.
* **The reviewer identity is assigned by YOU.** Blind agents left to name themselves once converged on
  one name, collapsing plurality. A mismatched reply is refused.
* **ONE PACKET FILE PER NODE.** `attester_packets.py` numbers items per invocation, so concatenating
  nodes mints `item_001` several times and the join becomes ambiguous. Unguarded; it has caught two
  sessions.
* **Do not file the old batch 1 / batch 2 replies** — template clustering and verbatim cross-node
  reuse. Rejected, and they stay rejected.
* **Blindness is a prompt contract, not a sandbox.** A subagent has tools. Record `--samples-delivery`
  and `--tool-uses-by-reviewer` as what ACTUALLY happened. **Reviewer self-reports of their own tool
  use are unreliable** — three reviewers named only one of their two calls. Trust the harness usage
  record and say which you used.
* **Never encode the answer in the prompt.** Give the standard as a decision procedure, never a
  conclusion.
* **Audit every reply mechanically BEFORE filing.** One assessment per delivered sample; per-sample
  distinct reasoning; no cross-node verbatim reuse; one clause verdict per printed requirement; cited
  `sample_ids` that exist; min reasoning length; and quoted spans that appear in the packet. Script it —
  every one of those has caught a real reply.
* **Repeated reasoning is not automatically templating.** On a node whose items are genuinely
  identical, identical reasoning is *accurate*: 5 of 76 duplicates once traced to two seeds carrying the
  same arithmetic, and that review was filed and correct. Judge whether the string names that sample's
  own content. Generic frames that would read identically against any sample ("the answer is
  unambiguous; options are distinct") ARE templating — one reply was rejected for exactly that.
* **A rejection on FORM can discard a true finding on SUBSTANCE.** The reply rejected for templating was
  the one that spotted a real oddity the accepted reply missed. **Harvest the substantive claims from a
  reply before you set it aside.**
* **A PASS is not proof of absence.** Two dispatches of one node disagreed PASS vs FAIL, and the FAIL
  was right — six samples whose hints demanded a decomposed form the answer field rejected.
  Within-family agreement is only 88.1%.

### Expect reviews to find real bugs — and queue them AS BUGS

A finding recorded only as "review evidence to preserve" is a defect nobody will fix. Name each one in
`HARDENING_EVIDENCE.md` with node, seed and the rendered text. **Do not fix generator source
mid-campaign** — batch it (§7), or you pay the ~4h chain twice.

---

## 6. PRIORITY 2 — content debt. The highest-value fix is already confirmed.

**173 CONTRADICTED across 82 nodes and 144 distinct capabilities.** It is a long tail: the largest
single cluster is 4 findings, and the whole "concrete" family is 6 findings under 5 different names. No
one artifact clears a big batch. The 173 came from a campaign that moved **two variables at once** (the
ruling-9 prevalence standard AND the rater family), so the aggregate is usable but **no single row is
settled** — confirm a lone CONTRADICTED with one more independent dispatch before spending engineering
on it. For each confirmed one: build the artifact the clause names, or delete the provider entry;
Content Rule 4 decides and you quote the clause. `draw`-verb findings need a real visual formatter
(ruling 3) — a multiple-choice question *about* drawing does not satisfy a competency that says draw.

### ▶ START HERE: `generate_hints` ignores the item's variant. THREE DNAs, one root cause.

Confirmed across two rater families and verified by executing against the packets:

| node | the item asks for | the hints teach |
|---|---|---|
| `mat_g3_na_q4_7` (FIXED, `ab70698a`) | subtraction | addition |
| `mat_g1_na_q2_0` | largest to smallest — **17 of 17 samples** | least to greatest |
| `mat_g1_na_q2_3` | set base-10 blocks — 6 samples | write the decomposed form |

```
mat_g1_na_q2_0 seed 42:
  stem:   Arrange these numbers from largest to smallest: 61, 62, 29
  answer: [62, 61, 29]
  hints:  "Find the smallest number first, then the next smallest."
          "Ordered from least to greatest: [29, 61, 62]."

mat_g1_na_q2_3:
  stem:   Use base-10 blocks to show the number 76.      answer: 76
  hints:  "Write the broken apart form of 76."  "Break each digit into its place value: 70 + 6."
```

A pupil following the hints faithfully produces the wrong answer in every one of these. **This is the
"rule in TWO places" shape: `generate_params` knows the variant and `generate_hints` does not.** The
fix is probably ONE shared contract — a hint chain that must declare the variant it explains — not
three independent patches. **Sweep every `generate_hints` against its item's variant before assuming
only three DNAs are affected.** `fraction_hint_self_consistency` already gates the fraction case; the
generalised gate does not exist yet and is the single most valuable check available.

Two more verified content defects to fold into the same batch:

* **`mat_g1_na_q2_5` seed 607 serves `hints: []`** — the only sample with no scaffolding in a 34-sample
  packet — on the stem `Is 12 + 27 the same as 27 + 10?` with options including `Only when both are 0`,
  against a competency naming only addition without regrouping. Reads like a mangled commutativity
  template whose second operand was regenerated independently (27 + 10 where 27 + 12 was meant).
  Confirmed by two independent dispatches.
* **`mat_g1_na_q1_7`'s `concrete` clause FAILs.** The competency is *"Illustrate addition of numbers
  with sums up to 20 using a variety of concrete and pictorial models…"*; the packet serves pictorial,
  number-line and number-bond and **no concrete model**. Content Rule 4: the clause says `concrete`, so
  building it IS the fix. Related `concrete*` CONTRADICTED findings suggest one artifact may clear
  several nodes. Its hints also use first-digit/last-digit place-value language while the competency
  names only "counting up" and "putting together" — check `NOT_YET_KNOWN` before writing
  digit-decomposing hints (Content Rule 1).

**Batch ALL source work into ONE batch so the chain is paid once.**

---

## 7. The re-proof chain — ONLY after landing source work

Each step as a background task, ALONE, nothing else heavy running. `tee`, never `tail`.

```sh
# 0. fast suite green BEFORE committing source (~12 min)
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
# 3. benchmark — AFTER the last source commit, or obligation_benchmark_11 is red at baseline
#    and its mutation scores INVALID rather than DETECTED
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000
# 4. frontend static render — run_all does NOT regenerate it
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py
# 5. mutation corpus (~2h at 163 mutations). Expect 160/163, only the §6F cluster.
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py 2>&1 | tee corpus.log
# 6. release shards, all six (~26 min each, ~2.6h total)
for i in 0 1 2 3 4 5; do
  PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier release --shard-count 6 --shard-index $i
done
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier verify-release
# 7. run_all, ALONE, capturing the REAL exit code
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all > run_all.log 2>&1
echo "RUN_ALL EXIT CODE: $?"
```

**After the corpus, re-check for escaped plants (§3) before anything else.** Then commit the artifacts
by name (`validation_reports/mutation_proofs`, `.../obligation_release_shards`,
`obligation_benchmark.json`, `frontend_static_render.json`, `tree_state.json`), close the intent, and
confirm `tree_state.py` prints CERTIFIED.

**The benchmark prints `recommended_shards=4`; `validate_obligations.py` hard-codes 6.** Follow the
validator — four receipts fail §11 on coverage.

---

## 8. Traps, each paid for by a real session

**THE RECURRING SHAPE, now across seven sessions: a rule that lives in TWO places, fixed in ONE.**
Before calling anything done, ask where else this rule is written. Enumerate sites mechanically
(`mutation_proof._iter_input_files()`, `git grep`) and route behaviour through the ONE helper the
validator itself calls. Instances that each cost real time: the renderer's unique-path half and its
`case_id` half; an overstated §5 claim in FIVE digest-bound files (a correction naming three
half-landed, twice); `fractions.generate_params` taught subtraction while `generate_hints` was not;
`_provenance_corpus`'s field allowlist versus a packet renderer that prints more than it lists.

1. **A campaign can rot a unit-test FIXTURE without breaking any check.**
   `tests/unit/test_capability_contract.py` has rotted three times — select attestation records by
   OWNERSHIP (`VC._winning_verdict_index`), never positionally. **Filing a review rots
   `tests/unit/test_legacy_review_queue.py`'s artifact test**; regenerate with
   `PYTHONPATH=. .venv/bin/python tests/legacy_review_queue.py --write` and **check the DIRECTION the
   count moves** — that is how a defect was found where dispatch-provenance files were being counted as
   reviews, making the owed queue read 151 when 150 were owed and RISE to 152 on a filing.
2. **Cosmetic edits cost ~4 hours.** Once certified, touch no source you do not mean to change.
3. **A gate can be defeated one stack frame later — or one ENTRY POINT over.** The orchestrator skips
   its formatter filter entirely for a PINNED formatter. Check a fix on both paths.
4. **A classifier keyed on a MESSAGE STRING is a latent bug.** One left ~27 node/formatter pairs
   wrongly advertised for weeks.
5. **A surviving mutation has TWO causes** (the check is broken, or the plant no longer reaches the code
   the validator runs) and **`INVALID — the unmutated command baseline exited 1` is a THIRD thing**,
   neither. Distinguish by instrumenting the real path, never by re-running until green.
6. **An INVALID that vanishes when re-run alone is not automatically "contention".** A quiet
   single-agent corpus once scored seven spurious INVALIDs: a sub-second, same-length plant kept running
   from `__pycache__` after a byte-identical restore, because `.pyc` freshness is whole-second mtime
   plus size. Fixed (`d92a3875`). **If you hand-restore a file yourself, purge `__pycache__` too.**
7. **A neuter that does not match proves NOTHING, and it looks like a pass.** A 2026-09-24 neuter used
   `–` escapes while the file stores literal dash characters, so it replaced nothing, the tests
   passed against unmodified source, and that run nearly went into the record as proof. **Assert the
   replacement count, and print before/after.** For regexes, patch by LINE NUMBER.
8. **Fixing one side of a two-sided rule can shrink coverage SILENTLY while looking fixed.** The
   `_QUOTE_RE` dash fix, applied to only the closing lookahead, removed the visible false positive while
   leaving the second quoted value unchecked — because the character before it was the dash and the
   opening lookbehind rejected it. Found only by executing the tokeniser. **Ask what the symmetric half
   is.**
9. **Adding a formatter changes the obligation product**, so pinned counts in
   `tests/unit/test_obligation_executor.py` move. Confirm each new route is SERVED at several seeds
   before touching those numbers.
10. **Retiring an attestation record PROMOTES the previous holder of its orphan pair.** Retirement is
    iterative; it once took 4 rounds and 13 records.
11. **Every `§` token in `docs/pgen_contract.md` must be a `CONTRACT_CHECKS` key**, prose included —
    scanned in both directions.

---

## 9. What the last sessions changed — do not re-break these

Each carries a NAMED LIMIT. Read the limit before assuming coverage.

1. **`_provenance_corpus` is no longer a four-field allowlist.** It named `question_text`,
   `correct_answer`, `formatter`, `options` while the packet also prints hints, cloze text, visual
   payload/render and requirement clauses, so quoting a HINT — the field the seed-44 defect lived in —
   was reported as fabrication. Now a recursive flatten of every scalar and mapping key in each stored
   sample, so it cannot drift as fields are added. **LIMIT:** the corpus is the stored snapshot, a
   superset of the printed packet for internal fields (`replay_digest`, `renderer_input_digest`), so
   quoting one of those is not caught.
2. **`_QUOTE_RE` takes the dashes on BOTH sides.** `'40'-'50'` used to merge into one span no packet can
   contain. **LIMIT:** the gate still cannot tell a reviewer's paraphrase-in-quotes from a fabrication,
   which is why §5 part 2 exists. That is a DISPATCH-side fix, never a validator change.
   **If an honest verbatim quote still trips this gate, the corpus is missing a printed field —
   diagnose it; do not coach reviewers away from quoting.**
3. **The "115 of 151" figure is an UPPER BOUND, not a count** — measured with the narrow corpus, so it
   also counted honest quotes as fabrication. The fabrication conclusion stands on those reviews being
   template all-PASS stubs, which is separately evidenced. **Quote the qualification with the figure.**
4. **`_apply` is all-or-nothing** — validate every anchor before writing any file, then register each
   file in `_IN_FLIGHT` with a marker refresh before its write lands. **LIMIT:** the `edits` path only;
   a mutation supplying `apply_fn` owns its own rollback.
5. **`_legacy_review_paths` skips dot-directories**, so `.responses/` provenance is no longer counted as
   reviews.
6. **`validate_judgment` sorts its findings** (a bare set intersection iterated in `PYTHONHASHSEED`
   order). **Still sort before diffing two §5 runs** — other emitters may be unordered.

---

## 10. Known-red, known-blocked — do not "fix" by re-running

* **`assertion_coverage_8` (3) and `mutation_proof_integrity_8` (9 in 3 families) are the SAME three
  §6F records.** Their baseline command is `capability_phase2`, which is red, so the runner refuses to
  score them. **Only `capability_phase2` reaching 0 clears this.**
* **The supersession defect is UNFIXED — only its findings were cleared.** `_attestation_staleness`
  counts a verdict on a capability nothing consults as live ownership. The scaling fix is **the owner's
  call** and owes a named mutation plus a contract row.
* **H-02 and H-07 read `status: open` with an EMPTY `still_open` list.** Nobody has established whether
  the work is done and the status is stale bookkeeping, or the field simply is not maintained for those
  rows. **Do not assume either way** — establish it by execution and record what you find.
* **38 nodes carry STALE v1 findings** from noun/theme drift (`mat_g1_na_q2_1` seed 44 was reviewed as
  "100 books" and now renders "100 cupcakes"). Those nodes owe a fresh review anyway, so STALE is simply
  a second reason. **Not a generator regression** — the digest did not move.

---

## 11. Not yours

* Opening an `H-11` row — refused; ruling 6 keeps all workstreams under `H-06`.
* The supersession fix (§10) and `CSI-R1`–`CSI-R3` — open owner rulings.
* Release promotion / `H-09`.
* Editing `requires` / `requires_ignore` beyond what an owner ruling authorises — human-authored ground
  truth, locked in `data/skeletons/requires_ignore.lock.json`, the lock moving in the same commit as any
  sanctioned change. Never edit it to make a finding go away; the test is whether MATATAG wrote
  "or"/"e.g.", a reading of the competency text you must quote.
* Discarding or re-running the `batch117`–`batch150` prevalence corpus, or any filed v2 review. Verified
  genuine, protected by ruling 2.
* Renaming the 8 truthful `haiku45` reviewer identities to Luna (§0).
* **The ✝️ emoji / `bible` interest theme.** It is a deliberate product feature. Whether to keep using a
  religious symbol as an interchangeable countable is the OWNER's product judgment, not a pipeline
  defect, and three reviewers have already been wrong about it.
* Freeing disk by deleting worktrees or files you did not create — ask.
* **`.claude/worktrees/agent-aaac714fac3fe0cc6` holds uncommitted modifications to production source**
  dated Aug 10 (`axes_catalog.py`, `dna/na/comparing_ordering.py`, `formatters/textual/fmt_true_false.py`).
  Abandoned work or a forgotten experiment; needs an owner decision. **Do not delete and do not merge.**

Find something genuinely broken outside your scope? **Name it in the evidence log and your report
rather than fixing it.** A batch that grows is a batch that does not close.

---

## 12. Bookkeeping before you finish

* **Evidence entry in `validation_reports/HARDENING_EVIDENCE.md`**: exact commands, verbatim pass/fail
  output, seeds, dispatch ids, reviewer identities, **and the model + thinking level that judged.**
  Without it the task is not done.
* **Update `H-06`'s row surgically** (`git diff --numstat` shows only what you intended); release the
  lock in a **follow-up** commit.
* **Close your intent** (`tests/tree_state.py --complete`).
* **Rewrite this file's state section** — do not stack another banner. The previous copy reached eight,
  and its body contradicted its own top. Both this file and `HANDOFF_PROMPT.md` are outside
  `INPUT_ROOTS`; verify with `input_digest()` rather than assuming.
* **Any new file under `validation_reports/phase2_hardening/` must be claimed by a row's
  `proof_artifacts`**, or `hardening_status.py` fails by name.
* **RE-COUNT every number you quote, by execution.** Two sessions have now published a wrong count:
  "149 remain owed" when it was 150, and "34 v2 reviews / 9 haiku" when it was 33 / 8. Both were caught
  by re-counting, not by review.

---

## 13. What success looks like

You will **not** reach `run_all` exiting 0 — 117 nodes owe reviews and 82 carry content debt. A good
session:

1. **Dispatches every blind reviewer on `gpt-5.6-luna` at medium thinking**, names it truthfully in
   `reviewed_by`, and leaves the existing `haiku45` records alone.
2. Uses the four-part dispatch template (§5) from the first dispatch, so replies are fileable.
3. Moves the §5 queue by a **measured** amount — `validate_judgment` before and after, both quoted,
   entry point named, delta attributed per node — and does **not** report a RISE as a regression.
4. Files every verdict through `file_reviews` with truthful identities and provenance, and **authors
   none**.
5. Queues every defect a reviewer finds as a named bug with node, seed and rendered text, adjudicating
   theming findings against `interest_bank.json` first.
6. Leaves the tree CERTIFIED (it stays certified if you touch no source — verify), **or** leaves an
   accurate open intent saying exactly where it stopped. Owner ruling 3: "must end certified" is **not**
   the rule — an honest interrupted state beats a fabricated clean one.
7. Records what it measured, what it assumed, and what it left, so the next session inherits numbers it
   can trust rather than confident wrong ones.

**If you have appetite for source work**, the single highest-value item in the whole plan right now is
§6's `generate_hints`/variant contract: three DNAs are confirmed broken, the defect makes rendered
hints actively teach pupils the wrong procedure, and no gate catches the general case.

**Read, in this order:** `CLAUDE.md`; this file; `HANDOFF_PROMPT.md` (its "Limitations left standing");
`docs/phase2_hardening_completion_plan.md`'s `START HERE — handoff` for owner rulings 1–10 in full; then
the last three entries in `validation_reports/HARDENING_EVIDENCE.md`, especially
**"2026-09-24 — Haiku §5 wave 8, and a SECOND quote-provenance defect"** and its wave-9 subsection,
which show a full dispatch → audit → file → measure cycle including two rejected replies and a
retracted finding.

**Where they disagree: an executed command wins, then this file, then the plan's dated blocks.**
