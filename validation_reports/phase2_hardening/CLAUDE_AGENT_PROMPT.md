# Task prompt — Phase 2 hardening, PHASE A: fix the hint contract (fresh Claude Code session)

**Written 2026-09-25. This REPLACES every previous version of this file and its banners.** Every figure
below was executed on 2026-09-25 at digest `208a52406226e6d0`. If you refresh this file, **rewrite the
state section rather than stacking a banner** — a sibling prompt reached eight banners contradicting its
own body before it was rewritten.

You are working in `/Users/enrichmentcap/Documents/antigravity/ccmed` on the Adaptive K-12 Mastery
Engine's practice-problem-generator hardening. Your job is to move `run_all` toward exiting 0.

`NEXT_AGENT_PROMPT.md` beside this file is the same plan written for a GPT-hosted session. **This file
supersedes it for you**, because the dispatchable reviewer model differs. Where they disagree, follow
this one — except on a measured number, where an executed command beats both.

---

## 0. TWO OWNER DECISIONS OF 2026-09-25 THAT GOVERN THIS SESSION

### Decision 1 — the content fix is AUTHORISED. Spend it.

The owner has approved the engineering and the ~4h re-proof chain for **Phase A: the `generate_hints`
contract** (§3). Do not re-litigate the cost. Do NOT expand the §5 review campaign first — §2 explains
why that ordering is actively wasteful.

### Decision 2 — reviewer families must be CONSISTENT from now on

**Every blind reviewer you dispatch from a Claude host is Haiku** (`model: "haiku"` on the Agent tool),
under ruling 4: *"Haiku subagents extend to ALL agents reviewing sample pg output."* No new rater family
may be introduced. Three things follow:

1. **The reviewer identity names the model that ACTUALLY judged**, e.g.
   `blind-reviewer-haiku45-<wave>-<node>-20260925`.
2. **The 44 existing non-Haiku records are TRUTHFUL and must never be renamed** — 25 `gpt-5.6-luna`
   and 19 `gpt-6-luna`, filed by GPT-hosted sessions. Two of those sessions could not dispatch the
   model §0 then mandated and correctly **changed the MODEL rather than the label**. Normalising any of
   them to Haiku would be a false evidentiary claim, not a tidy-up.
3. **If you cannot dispatch Haiku**, do the same thing they did: change the model, name it truthfully,
   and say so prominently. Never write one model's name onto another's verdict.

**The consistency debt this leaves, which you should help retire:** the corpus spans three families and
measured agreement exists only for Haiku-vs-GPT-5.6-Terra (**11/18 = 61.1%**) and Haiku-vs-Haiku
(**37/42 = 88.1%**). **Both Luna variants are unmeasured against anything.** Phase B (§4) re-reviews
nodes that already carry a Luna verdict — that is the natural, nearly free moment to record
Luna-vs-Haiku agreement on the same clauses. Do it and write the number down; the corpus currently
cannot state its own inter-family consistency, and since ruling 9 made the standard a variable, that
provenance matters.

---

## 1. Ground rules you may not break

Read `CLAUDE.md` / `AGENTS.md` first — the Scaling Mandate, Engineering Protocols and Definition of Done
are binding. The ones that bite hardest here:

1. **Verification is execution.** Never state what a command will do; run it and quote the verbatim
   output. **If you did not run it, write "not measured."**
2. **Never weaken a check to make it pass.** If a gate is red the bug is in the pipeline. The only
   exception is documented ground-truth error, reported with node id and justification.
3. **You never author a Reviewer or Attester verdict.** If a step seems to require you to judge rendered
   student content yourself, **stop — you have misread it.** (Executing a packet to CONFIRM a reviewer's
   factual claim is not authoring a verdict, and you should do it.)
4. **Prove a check by executing a planted violation**, and prove it is caught for the right reason:
   neuter the gate until the mutation SURVIVES, then restore byte-identical and confirm with `cmp`.
5. **Content Rule 4 governs content decisions.** If a competency names a verb, model or range the
   pipeline cannot produce, building it **is the fix**; if the competency does not name it, building it
   is invention and is forbidden. **Quote the clause** either way.
6. **Name every limitation in writing** — docstring, `docs/pgen_contract.md` row, and
   `validation_reports/HARDENING_EVIDENCE.md`.
7. **Contracts and enforcement move together** (Protocol 7). A contract edit with no test diff is
   incomplete work, and vice versa.

**Invocation:** always `PYTHONPATH=. .venv/bin/python …`. No usable bare `python`, no `timeout` on this
host. The fast unit suite takes ~12 minutes; pass `-m "not slow"` explicitly.

---

## 2. State, and WHY THE ORDER OF WORK IS FIX-THEN-REVIEW

```
$ PYTHONPATH=. .venv/bin/python tests/tree_state.py
PASS tree_state: CERTIFIED
  live input digest : 208a52406226e6d0
  worktree          : clean
  mutation_proofs         fresh  163 file(s)
  release_shards          fresh  6 file(s)
  obligation_benchmark    fresh  1 file(s)
  frontend_static_render  fresh  1 file(s)

$ PYTHONPATH=. .venv/bin/python tests/hardening_status.py
PASS hardening_status: 10 H-row(s) valid — 3 closed, 6 open, 1 out_of_scope
```

HEAD is at or after `f642f3a9`; `H-06`'s owner line reads `released @ 724dd91b` and is **unclaimed**.
Disk ~16 GiB free. **If a command disagrees with this file, believe the command** and say so.

```
$ PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all   # 2026-09-25
  RUN_ALL EXIT CODE: 1
  scheduled=17 completed=14 failed=3 crashed=0 not_run=0 incomplete=0
  FAIL judgment_reviews      (§5)  — 2016 at the module / expect 2017 at run_all
  FAIL capability_contract   (§6F) — 173 CONTRADICTED across 82 of 151 nodes
  FAIL assertion_coverage_8        — 3 in 1 family; mutation_proof_integrity_8 9 in 3 families
```

Review corpus: **60 schema-v2 reviews**, verdicts **30 FAIL / 22 CONCERN / 8 PASS**. Legacy queue:
**91 v1 nodes owed** (91 + 60 = 151).

### The measurement that sets the priority

All 2,016 §5 findings, classified by **what actually clears them**:

```
1002  49.7%  sample-level check failure   -> clears by FIXING CONTENT
 523  25.9%  node-level finding           -> clears by FIXING CONTENT
  62   3.1%  clause FAIL                  -> clears by FIXING CONTENT
 277  13.7%  v1 unadjudicable             -> clears by REVIEWING
 129   6.4%  STALE v1                     -> clears by reviewing
  19   0.9%  quote provenance             -> reviewer quality
```

**78.7% of §5 needs content fixed, not nodes reviewed.** Reviewing a node does not reduce §5 — it
CONVERTS one unadjudicable finding into several real content findings, measured at roughly 4:1. That is
the gate working as designed, but it means **§5 reaches 0 only when the content is fixed so reviewers
return PASS.** §5 rose 1236 → 2016 over the campaign. **Do not report a rise as a regression.**

### And reviewing before the hint fix pays for the same work twice

Hints are **bound into the canonical learner-visible packet digest**. From
`validate_judgment.py`'s own STALE message: *"Stem, resolved answer, ordered options, hints, cloze,
visual payload/rendered structure, response configuration, replay inputs, and effective choices are
bound."*

So **the moment `generate_hints` changes, every filed review whose hints change goes STALE and owes a
re-review.** Sixty reviews are filed. Every additional review filed before Phase A is work Phase A
destroys. **That is why Phase A comes first and the 91-node queue waits.**

---

## 3. PHASE A — the `generate_hints` contract. Authorised. Start here.

### The defect, confirmed across three rater families and verified against rendered packets

`generate_params` knows the item's parameters and `generate_hints` does not. **Six manifestations:**

| node | the hints ignore | measured |
|---|---|---|
| `mat_g3_na_q4_7` *(FIXED `ab70698a`)* | the operation | add hints on a subtract item, 11 of 19 |
| `mat_g1_na_q2_0` | the sort direction | **17 of 17** descending items get ascending hints |
| `mat_g1_na_q2_3` | the response variant | blocks-setting item told to write the decomposed form, 6 |
| `mat_g2_mg_q2_0` | the unit **and** the direction | 7 + 7 of 19 |
| `mat_g2_mg_q2_3` | that no ruler exists; length vs distance | 12 of 21 |
| `mat_g2_mg_q4_0` | **arithmetic itself** | **23 of 23** assert a false equation |
| `mat_g2_mg_q4_1` | the a.m./p.m. of its own visual; mark arithmetic | 5 + 2 of 21 |
| `mat_g2_mg_q4_2` | that the item is text or a timetable, not a clock | 20 of 27 |

The worst, and the one to build the gate around:

```
mat_g2_mg_q4_0 — "Describe the duration of an event in terms of number of days and/or weeks
using a calendar."  ALL 23 samples:
    hint: "Subtract: 27 - 24 = 4 days"     but 27-24=3   (4 is right under inclusive counting)
    hint: "Subtract: 10 - 4 = 1 week"      but 10-4=6

mat_g2_mg_q2_0 — the final hint contradicts the hint immediately before it:
    stem:   A pencil is 10 cm long. A ruler is 15 cm long. Which length is shorter?
    answer: 10
    hints:  "15 is more than 10."  then  "The longer length is 10 centimeter (cm)."

mat_g2_mg_q4_2 — a timetable question scaffolded by a clock that is not there:
    stem:   Look at the class schedule. How many minutes long is the English class?
    answer: 45
    hints:  all four read an analog clock, ending "The time shown is 8:00 a.m."
```

**`mat_g2_mg_q4_0` is the most serious defect this campaign has found**, because the final answers are
CORRECT — so every automated gate passes those items while the hints teach a Grade 2 pupil that
27 − 24 = 4. A gate that only checks answers cannot see it.

### What to build

**One shared contract, not six patches.** `29` DNA modules define `generate_hints`
(`grep -rl "def generate_hints" backend/app/practice_gen/dna/ | wc -l`) — find the ones behind the
nodes above by execution, not by guessing filenames. The contract should make a hint chain **declare the
parameters it explains** and fail loudly when they disagree with the item it was generated for. At
minimum the dimensions the evidence names:

* **the operation** (add vs subtract) — already gated for fractions only;
* **the direction** (ascending/descending, shorter/longer) — and no hint may assert a comparison its own
  neighbouring hint denies;
* **the unit** (m vs cm) — a hint may not name a unit the stem does not use;
* **the response variant** (set-the-blocks vs write-the-expansion);
* **the medium it references** — a hint may not tell a pupil to read a ruler, a clock or a visual the
  item does not contain;
* **arithmetic truth** — every equation a hint asserts must actually hold. This one is independent of
  the answer being right, which is precisely why `mat_g2_mg_q4_0` slipped through.

**Generalise the gate.** `fraction_hint_self_consistency` (declared in `run_all.py`, gated in
`tests/unit/test_fraction_hint_consistency.py`, with a contract row and a mutation) covers exactly one
DNA. Extend it — or add a sibling — so the CLASS is gated across every DNA, and say in the docstring and
the contract row which dimensions are covered and which are not. **A gate described as total is how the
next agent stops looking.**

**It owes, per Protocol 7 and the Scaling Mandate:** a mutation per behaviour you fix (a two-site fix
lets a single-site plant survive while proving nothing — see trap 8), each proven by neuter →
SURVIVED → restore byte-identical → DETECTED; a `docs/pgen_contract.md` row moving in the same commit;
and named limits in writing.

**Batch these in the SAME source batch so the chain is paid once** — both are `tests/`-side and both are
already diagnosed:

* **`file_reviews` and the dispatch prompt contradict each other on an ABSENCE clause.** The generated
  prompt says *"one or more cited `sample_ids` … never invent a supporting sample"*; `file_reviews.py:175`
  requires a NON-EMPTY list. A reviewer FAILing a clause for absence reasonably cites none and becomes
  unfileable. It refused a review on 2026-09-25 and will recur on every `draw`/`concrete` absence FAIL.
* **`file_reviews` accepts an `overall` that contradicts the review's own findings.** `mat_g2_mg_q2_2`
  is filed `overall: PASS` with `variant_comprehensiveness: CONCERN`. `validate_judgment` still flags
  the node so nothing is hidden, **but `legacy_review_queue.json`'s `by_overall_verdict` census reads
  the stored field, so corpus statistics overstate PASSes.** Enforce it in the filer or as a §5 finding.

**Also worth investigating, NOT yet established:** `mat_g2_mg_q4_1` has 5 samples whose answer is p.m.
while the rendered structure carries `AM`. A picture contradicting its own answer is what
`§1G visual payload (the picture agrees with its own answer)` exists for. Whether §1G's scope excludes
clock a.m./p.m. labels by design or by omission **is unestablished** — read the check and instrument it
before claiming either.

---

## 4. PHASE B — re-review what Phase A staled, and MEASURE the family agreement

After the chain is green, re-run §5 and list the nodes that went STALE. Re-review them on Haiku with the
four-part template (§5). **Where a staled node carries a Luna verdict, this is the free moment to record
Luna-vs-Haiku agreement on the same clauses** — Decision 2. That number does not exist yet.

## 5. PHASE C — resume the queue. 91 nodes. No re-proof owed.

Only after Phase A, so reviews are not invalidated on arrival. `validation_reports/judgment/` is outside
`INPUT_ROOTS`, so the campaign moves no digest and the tree stays CERTIFIED while you touch no source.

**Get the owed list by execution.** `tests.judgment_batches --plan` is a STATIC partition of all 151
nodes, not a live owed-list, and its batch 7 is already filed:

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

### ⚠ THE DISPATCH TEMPLATE THAT WORKS — all four parts, measured over waves 8–30

A prompt missing any of these produces replies `file_reviews` REFUSES, or replies that file but carry
findings no content fix can clear:

1. **A ≥60-character floor** on every `reasoning` and `rationale`. The filer hard-refuses under 40.
   Three replies were thrown away for this.
2. **An exact-verbatim quoting rule.** Anything in quotes must be a character-for-character substring of
   the printed packet, because `_validate_quote_provenance` treats a span it cannot find as fabricated
   evidence. Tell reviewers: no paraphrase, summary, elision, placeholder or comma-fragment in quotes,
   never two quoted values joined by a dash, and **when in doubt use no quotation marks at all.** One
   node went 13 unmatched spans → **0** on that instruction alone.
3. **Neutral interest-bank context.** `data/interest_bank.json` holds **26 curated interest themes**;
   themed names, objects and emoji are a deliberate product feature. Have reviewers judge whether
   theming **INTERFERES** with the mathematics — not whether the theme is appropriate. Three separate
   reviewers flagged the `bible` theme's ✝️ as a defect and **all three were wrong**; a blind reviewer
   cannot read `interest_bank.json`, so it cannot adjudicate INTENT. Adding this context took one node
   from CONCERN to PASS while its arithmetic checking stayed intact.
4. **An explicit instruction to compare hints against the item** — every content defect found so far came
   from that comparison. Plus: every `clause_evidence` entry must cite at least one sample id INCLUDING
   a FAIL (for an absence, cite the ids EXAMINED), and `overall` must be consistent with the findings.

### Audit every reply BEFORE filing, then audit again after any revision

Check: one assessment per delivered sample; per-sample distinct reasoning; no cross-node verbatim reuse;
one clause verdict per printed requirement with real cited ids; min string length; quoted spans present
in the packet; and `overall` consistent with the findings.

**Call the validator's own functions** — `_validate_quote_provenance` and `_provenance_corpus` — rather
than re-implementing their regex. A 2026-09-25 audit script re-implemented it and **under-reported**: it
found 3 unmatched spans where the validator found 4, and 0 where it found 1. That is the
rule-in-two-places shape, committed by the audit tooling itself.

**THE REVISION TRAP.** Asking a reviewer to fix one mechanical property regresses another. Measured:
telling one to drop quotation marks took unmatched spans 13 → 0 **but dropped its shortest string to 24
characters**; asking another to expand its strings **emptied a clause's `sample_ids`**. And a reviewer's
report of its own file is unreliable — one claimed its shortest string was 128 characters when
measurement showed 44. **Re-run the FULL audit after every revision, and never trust the summary.**
Revise by asking the reviewer to change its own wording; **never edit a verdict, sample id, clause or
`overall` yourself.**

**A rejection on FORM can discard a true finding on SUBSTANCE** — the reply once rejected for templating
was the one that spotted a real oddity the accepted reply missed. **Harvest substantive claims from a
reply before setting it aside.** And **a PASS is not proof of absence**: two dispatches of one node
disagreed PASS vs FAIL and the FAIL was right.

**Repeated reasoning is not automatically templating.** On genuinely identical items, identical reasoning
is accurate — 5 of 76 duplicates once traced to two seeds carrying the same arithmetic, and that review
was correctly filed. Generic frames that would read identically against any sample ARE templating.

Other §5 rules: **file from the DISPATCH-TIME skeleton** (a generator fix landing between dispatch and
filing would pair verdicts with samples the reviewer never saw, and §5 freshness would PASS — the one
error undetectable afterwards); **you assign the reviewer identity**; **one packet file per node**
(`attester_packets.py` numbers items per invocation); **do not file the old batch 1/2 replies**;
**blindness is a prompt contract, not a sandbox** — record `--samples-delivery` and
`--tool-uses-by-reviewer` truthfully, and prefer the harness usage record to the reviewer's self-report,
which has been wrong about its own tool count more than once.

---

## 6. PHASE D — `capability_phase2`, the other 173

**173 CONTRADICTED across 82 nodes and 144 distinct capabilities** — a long tail whose largest cluster is
4 findings. It alone gates `assertion_coverage_8`. It came from a campaign that moved **two variables at
once** (the ruling-9 prevalence standard AND the rater family), so **no single row is settled**: confirm
a lone CONTRADICTED with one more independent dispatch before spending engineering. Then build the
artifact the clause names or delete the provider entry; Content Rule 4 decides and you quote the clause.

Two already-confirmed items to start from:

* **`mat_g1_na_q1_7`'s `concrete` clause.** The competency is *"Illustrate addition of numbers with sums
  up to 20 using a variety of concrete and pictorial models…"*; the packet serves pictorial, number-line
  and number-bond and **no concrete model**. Related `concrete*` findings recur across Grade 1, so one
  artifact may clear several nodes.
* **`mat_g2_mg_q1_2` serves a `draw` competency with 18 `mcq` samples**, `is_visual: false`, zero letting
  a pupil draw, against *"Describe **and draw** the effect of one-direction multi-step slide (or
  translation)…"*. Ruling 3 is explicit that a multiple-choice question *about* drawing does not satisfy
  a competency that says draw.

**The interest-wrapper defect, localised:** the wrapper names a different object than the task — running
shoes wrapped around a crayon task, stones around a sticker task — on **four nodes across three rater
families, always at seeds 701/702**. That one-seed-pair pattern points at the wrapper composition step,
not the interest bank. This is the genuine theming defect, as distinct from the theme being present.

---

## 7. Before any heavy run

```sh
ps -eo pid,ppid,etime,command | grep -iE "mutation_harness|obligation_executor|validate_|pytest" | grep -v grep
df -h /System/Volumes/Data
```

Empty, or resolve it first. On 2026-09-23 two agents ran the corpus concurrently; **four planted bugs
escaped into source and two reached commits**, including `"is_correct": False` in the API route. The
harness plants real bugs in real source and restores them, so while it runs production source is
*supposed* to be transiently modified — a second party "tidying up" `git status` reverts a live plant.

1. **NEVER `git add -A`.** Stage paths you edited, by name. Both committed plants entered that way. The
   pre-commit hook rebuilds Graphify and stages `graphify-out/` itself — expect more files than you
   staged, which is precisely why you stage by name.
2. **Find plants with git, not a marker phrase** (they differ: `# planted mutation`,
   `// planted emission drift`, `// planted degenerate visual`):
   ```sh
   git status --porcelain -- backend/ tests/ scripts/ data/ frontend/src \
       docs/pgen_contract.md docs/testing_pipeline.md
   git grep -n -E "#\s*planted mutation|//\s*planted " HEAD -- backend/ frontend/src \
       | grep -v mutation_harness      # HEAD must be clean
   ```
3. **`pkill -f mutation_harness` may not stop a run** — the parent can appear as `Python -`. Kill by pid.
4. **`FATAL: another mutation run is live…` is the guard WORKING.** Do not delete the marker or revert
   the file; find that pid, let it finish or kill it, then re-run — recovery restores its plant.
5. **A jump in the INVALID count describes your ENVIRONMENT, not the tree.** Three INVALID is the known
   §6F cluster; a contended run once reported nineteen.
6. **Never pipe a long run through `tail -N`.** `tail` holds the entire stream until the pipeline ends,
   so a 2-hour corpus writes nothing to its log and any watcher cannot fire; it also **masks the exit
   code**. Use `| tee <log>`, and capture the exit code from the process:
   `cmd > log 2>&1; echo "EXIT: $?"`.
7. **`du -sh -d 1` is invalid on macOS BSD `du`** — usage to stderr, nothing to stdout. Use `du -h -d 1`.
8. **Do not delete worktrees or files you did not create — ask.**

### Claim the lock and record intent

`H-06`'s `owner` line is the work-lock. Change **only that line** — a whole-file `json.dumps`
renormalises `§`/`—` escapes across rows you do not own and once produced 16 lines of collateral churn. A
`sed` of the single line is safest; if you round-trip the JSON, first prove your writer is byte-stable
(`json.dumps(d, indent=2, ensure_ascii=False) + "\n"` reproduced the file exactly on 2026-09-24 —
verify). **`git diff --numstat` must read `1 1`.** Then:

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin batch \
    --session "<your-session-id>" --note "Phase A: the generate_hints contract"
```

`batch` for source edits, `chain` for re-proof, `campaign` for §5 dispatch. Close with `--complete`.
Release the lock in a **follow-up** commit — `--amend` moves the hash and leaves the row dangling.

**If you inherit an open intent whose session is gone** (check `ps`), recover its uncommitted work first
— verify it, commit it unchanged, author nothing — then close the intent and release the lock with a note
saying why. That has now happened twice; both times reviews were sitting unsaved in the worktree.

---

## 8. The re-proof chain — after Phase A lands

Each step as a background task, ALONE. `tee`, never `tail`.

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
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000
# 4. frontend static render — run_all does NOT regenerate it
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py
# 5. mutation corpus (~2h at 163+ mutations). Expect 160/163 plus whatever you add.
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py 2>&1 | tee corpus.log
# 6. release shards, all six (~26 min each, ~2.6h)
for i in 0 1 2 3 4 5; do
  PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier release --shard-count 6 --shard-index $i
done
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier verify-release
# 7. run_all, ALONE, capturing the REAL exit code
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all > run_all.log 2>&1
echo "RUN_ALL EXIT CODE: $?"
```

**After the corpus, re-check for escaped plants (§7) before anything else.** Then commit the artifacts by
name (`validation_reports/mutation_proofs`, `.../obligation_release_shards`, `obligation_benchmark.json`,
`frontend_static_render.json`, `tree_state.json`), close the intent, confirm CERTIFIED.

**The benchmark prints `recommended_shards=4`; `validate_obligations.py` hard-codes 6.** Follow the
validator — four receipts fail §11 on coverage. **Adding a formatter changes the obligation product**, so
pinned counts in `tests/unit/test_obligation_executor.py` move; confirm each new route is SERVED at
several seeds before touching those numbers.

---

## 9. Traps, each paid for by a real session

**THE RECURRING SHAPE, across eight sessions: a rule that lives in TWO places, fixed in ONE.** Before
calling anything done, ask where else this rule is written. Enumerate sites mechanically
(`mutation_proof._iter_input_files()`, `git grep`) and route behaviour through the ONE helper the
validator itself calls. **Phase A is exactly this shape** — `generate_params` knows the parameter and
`generate_hints` re-derives it — so resist fixing it per-DNA.

1. **A campaign can rot a unit-test FIXTURE without breaking any check.**
   `tests/unit/test_capability_contract.py` has rotted three times — select attestation records by
   OWNERSHIP (`VC._winning_verdict_index`), never positionally. **Filing a review rots
   `tests/unit/test_legacy_review_queue.py`'s artifact test**; regenerate with
   `tests/legacy_review_queue.py --write` and **check the DIRECTION the count moves** — that is how a
   defect was found where `.responses/` provenance was being counted as reviews.
2. **Cosmetic edits cost ~4 hours.** Once certified, touch no source you do not mean to change.
3. **A gate can be defeated one stack frame later — or one ENTRY POINT over.** The orchestrator skips its
   formatter filter for a PINNED formatter. Check a fix on both paths.
4. **A classifier keyed on a MESSAGE STRING is a latent bug.**
5. **A surviving mutation has TWO causes** (broken check, or the plant no longer reaches the code) and
   **`INVALID — the unmutated command baseline exited 1` is a THIRD thing**. Distinguish by executing.
6. **An INVALID that vanishes when re-run alone is not automatically contention.** A sub-second,
   same-length plant once kept running from `__pycache__` after a byte-identical restore. Fixed
   (`d92a3875`) — but **if you hand-restore a file yourself, purge `__pycache__` too.**
7. **A neuter that does not match proves NOTHING and looks like a pass.** One used `–` escapes while
   the file stores literal dashes, so it replaced nothing and the tests passed against unmodified
   source. **Assert the replacement count and print before/after.** For regexes, patch by LINE NUMBER.
8. **Fixing one side of a two-sided rule can shrink coverage SILENTLY while looking fixed.** The
   `_QUOTE_RE` dash fix applied to only the closing lookahead removed the visible false positive while
   leaving the second quoted value unchecked. Found only by executing the tokeniser. **Ask what the
   symmetric half is.**
9. **Retiring an attestation record PROMOTES the previous holder of its orphan pair.** Iterative; once
   took 4 rounds and 13 records.
10. **Every `§` token in `docs/pgen_contract.md` must be a `CONTRACT_CHECKS` key**, prose included.
11. **RE-COUNT every number you quote.** Three sessions have published a wrong count: "149 owed" when it
    was 150, "34 v2 reviews / 9 haiku" when it was 33 / 8, and "1481 across 149" after it was superseded.

---

## 10. Known-red, known-blocked — do not "fix" by re-running

* **`assertion_coverage_8` (3) and `mutation_proof_integrity_8` (9 in 3 families) are the SAME three §6F
  records.** Their baseline command is `capability_phase2`, which is red, so the runner refuses to score
  them. **Only `capability_phase2` reaching 0 clears this.**
* **The supersession defect is UNFIXED — only its findings were cleared.** `_attestation_staleness`
  counts a verdict on a capability nothing consults as live ownership. The scaling fix is **the owner's
  call** and owes a named mutation plus a contract row.
* **H-02 and H-07 read `status: open` with an EMPTY `still_open` list.** Nobody has established whether
  the work is done and the status is stale bookkeeping, or the field is simply unmaintained. **Do not
  assume either way** — establish it by execution.
* **38 nodes carry STALE v1 findings** from noun/theme drift. They owe a fresh review anyway; not a
  generator regression, the digest did not move.

## 11. Not yours

* Opening an `H-11` row — refused; ruling 6 keeps all workstreams under `H-06`.
* The supersession fix (§10) and `CSI-R1`–`CSI-R3` — open owner rulings.
* Release promotion / `H-09`.
* Editing `requires` / `requires_ignore` beyond what an owner ruling authorises — human-authored ground
  truth, locked in `data/skeletons/requires_ignore.lock.json`, the lock moving in the same commit as any
  sanctioned change. Never edit it to make a finding go away; the test is whether MATATAG wrote
  "or"/"e.g.", a reading of the competency you must quote.
* Discarding or re-running the `batch117`–`batch150` prevalence corpus, or any filed v2 review.
* **Renaming any of the 44 `gpt-5.6-luna` / `gpt-6-luna` reviewer identities** (§0 Decision 2).
* **The ✝️ emoji / `bible` interest theme.** A deliberate product feature; whether to use a religious
  symbol as an interchangeable countable is the OWNER's product judgment. Three reviewers were wrong
  about it already.
* Freeing disk by deleting worktrees or files you did not create — ask.
* **`.claude/worktrees/agent-aaac714fac3fe0cc6` holds uncommitted modifications to production source**
  dated Aug 10 (`axes_catalog.py`, `dna/na/comparing_ordering.py`, `formatters/textual/fmt_true_false.py`).
  Needs an owner decision. **Do not delete and do not merge.**

Find something genuinely broken outside your scope? **Name it in the evidence log and your report rather
than fixing it.** A batch that grows is a batch that does not close.

---

## 12. Bookkeeping before you finish

* **Evidence entry in `validation_reports/HARDENING_EVIDENCE.md`**: exact commands, verbatim pass/fail
  output, seeds, dispatch ids, reviewer identities, **and the model + thinking level that judged.**
* **Update `H-06`'s row surgically**; release the lock in a **follow-up** commit.
* **Close your intent** (`tests/tree_state.py --complete`).
* **Rewrite this file's state section** — do not stack a banner. Both this file and `HANDOFF_PROMPT.md`
  are outside `INPUT_ROOTS`; verify with `input_digest()`.
* **Any new file under `validation_reports/phase2_hardening/` must be claimed by a row's
  `proof_artifacts`**, or `hardening_status.py` fails by name.

## 13. What success looks like

`run_all` will not exit 0 this session. A good session:

1. **Lands the `generate_hints` contract as ONE shared rule**, with a mutation per fixed behaviour, a
   generalised gate replacing the fractions-only one, a `docs/pgen_contract.md` row in the same commit,
   and its blind spots named.
2. **Quotes the chain verbatim**, including `run_all`'s observed exit code, and re-checks for escaped
   plants after the corpus.
3. **Measures §5 before and after**, names the entry point, and reports honestly — including that
   clearing hint defects may REVEAL other findings on the same samples, and that reviews going STALE is
   the fix working.
4. **Dispatches every reviewer on Haiku** and leaves the 44 non-Haiku identities untouched (§0).
5. **Records Luna-vs-Haiku agreement** if Phase B gives it the chance.
6. Leaves the tree CERTIFIED, **or** an accurate open intent saying exactly where it stopped. Ruling 3:
   "must end certified" is **not** the rule — an honest interrupted state beats a fabricated clean one.

**Read, in this order:** `CLAUDE.md`; this file; `HANDOFF_PROMPT.md`;
`docs/phase2_hardening_completion_plan.md`'s `START HERE — handoff` for owner rulings 1–10; then the last
four entries in `validation_reports/HARDENING_EVIDENCE.md`, especially **"Haiku §5 wave 30 — the
measurement/time hint system is broadly broken"**, which carries the verified packet evidence Phase A is
built on.

**Where they disagree: an executed command wins, then this file, then the plan's dated blocks.**
