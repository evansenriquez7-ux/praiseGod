# Handoff — continue the Phase 2 hardening plan

**Refreshed 2026-09-24 (claude-h06-s5-campaign-2026-09-24): the §5 blind re-review campaign is
OPEN and its blocking gate is fixed. `_provenance_corpus` was a four-field allowlist while the blind
packet prints hints, cloze text, visual payload/render and the requirement clauses, so it raised FOUR
FALSE findings against an honest review — punishing reviewers for quoting hint text, the very field
the seed-44 defect lived in. Fixed, with the `115 of 151` claim corrected in all SIX places it lived
(it is an UPPER BOUND, not a count). Also fixed: `_apply` could leak a multi-file plant into
production source, and `_legacy_review_paths` counted dispatch provenance as reviews (the owed queue
is **150**, not the 151/152 the artifact reported). Chain re-proved ALONE at `da4f9588`; digest is
now `126e9eb19a1122bc`. ONE node is filed (`mat_g3_na_q4_7`, Haiku); **149 remain owed** and the
campaign is unblocked. ⚠ The data volume has ~3.3 GiB free — run `df -h` before any heavy run. This
file is deliberately a POINTER, not a summary.**

*(historical)* Refreshed 2026-09-24 (claude-h06-killsafe-chain-2026-09-23): per-invocation kill-safety
marker and bytecode-purging restores, re-proved at `07015c154d6f6c8f`.

*(historical)* Refreshed 2026-09-23 after the lossless §5 filing repair, first genuine v2 review, and
complete re-proof at digest `e321fd21ab20c475`.

Earlier versions duplicated the plan's status and then drifted from it. Two sources of truth
is how a session inherits confident wrong numbers, so status lives in exactly one place —
the plan's `START HERE — handoff` — and this file tells you how to reach it safely, what the
owner has already decided, and what will waste your time if nobody warns you.

---

## FIRST: establish what state the tree is in

**One command. Run it before touching anything.** It replaces the ad-hoc digest script and
the human-written paragraph that used to live here — that was a pipeline defect, and closing
it was the last session's first job.

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py      # exit 0 only when CERTIFIED
```

It prints the live digest, the worktree, each of the four digest-bound artifact families,
and any OPEN INTENT — a record written when a batch or chain STARTS and cleared when it
finishes. The intent is what separates the two states that were previously indistinguishable
from the digests alone.

| State | Means | Do |
|---|---|---|
| `certified` | nothing in flight, worktree clean, all four families fresh | **Start THE JOB.** Do NOT re-run the chain; it proves nothing new |
| `awaiting_reproof` | a batch landed, the chain was never run | Run the chain, in the documented order in the plan |
| `interrupted` | an intent is open, or the worktree is dirty | Read the open intent — it names what was in flight and the next step |

**The expected reading right now:**

```text
PASS tree_state: CERTIFIED
  live input digest : 126e9eb19a1122bc
  worktree          : clean
  mutation_proofs         fresh  162 file(s)
  release_shards          fresh  6 file(s)
  obligation_benchmark    fresh  1 file(s)
  frontend_static_render  fresh  1 file(s)
```

And the ledger, which now runs to `H-10`:

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
#  -> PASS hardening_status: 10 H-row(s) valid — 3 closed, 6 open, 1 out_of_scope
```

**If either command disagrees with the block above, believe the command, not this file.**

**NAMED LIMITS of `tree_state`, so you keep looking:** an intent is a claim, not a lock — no
pid, no heartbeat, no timeout, so a live session cannot be told from one that died holding
one; a session that never calls `--begin` leaves a dirty worktree with no record of WHY; and
`--complete` is trusted, caught only in that clearing it on a stale tree still reports
`awaiting_reproof` rather than `certified`.

Record your own intent before starting work that can be interrupted:

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin campaign \
    --session <your-session-id> --note "what you are doing"
# ... and on completion:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --complete --note "where you got to"
```

---

## ⚠ 2026-09-23 (latest) — §5 FILER REPAIRED; FIRST V2 REVIEW FILED. START HERE.

Tree is **CERTIFIED** at `e321fd21ab20c475`, worktree clean, all four digest-bound artifact
families fresh. `run_all` was **EXECUTED**: EXIT 1,
`scheduled=17 completed=14 failed=3 crashed=0`.

| stage | count |
|---|---|
| `capability_phase2` | **173** CONTRADICTED across **82 of 151 nodes** |
| `judgment_reviews_5` | **1263** module / **1264** entry point |
| `assertion_coverage_8` | 3 in 1 family, downstream of red §6F baseline |

Commit `267e3b5b` repaired the schema-v2 filing boundary: prompts now demand all six findings,
four assessments per dispatch-time sample, clause evidence, and decomposition; the filer validates
the entire batch before writing, preserves the dispatch skeleton, and stores exact prompt/reply
provenance. Two new named mutations are DETECTED; the corpus is 151/154 with only the known three
§6F INVALID baselines.

One genuine blind v2 review is filed for `mat_g3_na_q4_7`, judged by GPT-5.6-Terra/light under
`blind-attester-gpt-5.6-terra-light-b7-20260923`. It has 27 substantive findings, including eleven
subtraction samples whose correct answer keys are paired with addition hints. Preserve the verdicts.
**150 nodes remain v1.**

**Do not file the existing batch 1 or batch 2 replies.** Mechanical audit found forbidden rationale
reuse/template clustering. A 25-node v2 packet can demand thousands of independent per-sample
reasons (batch 1 needs 2,044), beyond one model turn. The filer correctly rejects incomplete or
templated replies, but the planner does not yet size by response volume or support authenticated
partial continuation. Split future dispatches more finely while keeping dispatcher-assigned,
truthful reviewer identities and the 25-node maximum.

The full source re-proof is current: frontend PASS, benchmark current, six release shards complete,
and 154 mutation records fresh. During recovery, no orphaned process existed; the valid shard 0
receipt was retained and only stale shards 1–5 were resumed sequentially. `run_all` first exposed a
stale derived legacy queue; regeneration repaired it, and the final unit stage passed 801/1/2.

**NEXT:** continue the §5 blind queue using response-volume-sized dispatches. Content debt only on
independently confirmed findings. Definition of Done is not met.

**THE AGENT'S TASK IS `NEXT_AGENT_PROMPT.md`, not this file.**

---

## 2026-09-23 (historical) — CAMPAIGN REVIEWED AND KEPT; §0 REPAIRED.

Tree is **CERTIFIED** at `575e87127d7b6c27`, worktree clean, all four families fresh.
`run_all` was **EXECUTED**: EXIT 1, `scheduled=17 completed=14 failed=3`.

| stage | count |
|---|---|
| `capability_phase2` | **173** CONTRADICTED across **82 of 151 nodes** |
| `judgment_reviews_5` | **1252** module / **1253** stage — quote the entry point |
| `assertion_coverage_8` | 3 in 1 family |

**The `batch117`–`batch150` prevalence corpus is VERIFIED GENUINE and is KEPT.** 151/151 nodes,
767/767 pairs, every verdict byte-identical to its dispatch, 767 distinct reasoning skeletons,
truthful identities, prior records preserved. The 57 → 173 rise matched an independent 3.0x
prediction at 3.11x.

**But 173 moved TWO variables, not one.** Measured on the same 18 clauses with the standard held
fixed, **cross-family agreement is 11/18 = 61.1%** against 88.1% within-family, disagreeing in
both directions. So part of the rise is a sharper standard and part is a different rater family.
**The aggregate is usable; no individual row is settled — confirm any finding with a second
dispatch before building.**

**The campaign silently broke §0 and the session that ran it did not find out**, because it wrote
"`run_all` is still expected to exit 1" instead of running it. Two fixtures in
`tests/unit/test_capability_contract.py` had rotted — **neither check was broken**. Repaired, and
the pattern is now trap 2 in the agent prompt: select attestation records by OWNERSHIP
(`_winning_verdict_index`), never positionally, and assert about the specific pair under test.
That was the **third** occurrence in that one file.

**NEXT:** the seven-dispatch §5 schema-v2 blind re-review campaign (no re-proof owed). Content
debt only on confirmed findings.

**THE AGENT'S TASK IS `NEXT_AGENT_PROMPT.md`, not this file.** Hand that over; it points back
here for the standing limitations list and the long-form traps. This file is STATUS and
BACKGROUND — read its top banner and treat anything marked "(historical)" as record only.

**Dispatch model (owner ruling 10, restated precisely 2026-09-23): `GPT-5.6-Terra` on LIGHT
THINKING.** The `batch117`–`batch150` identities abbreviate it to `gpt-terra`; that is the
SAME model, recorded before the name was restated. Those records are truthful — do not
rewrite them — but new identities spell it out:
`blind-attester-gpt-5.6-terra-light-<batch>-<YYYYMMDD>`.

---

## 2026-09-23 (historical) — RULING-9 RE-DISPATCH COMPLETE.

Tree is **CERTIFIED** at `dfae9bbb7a1398d7`; all four digest-bound artifact families remain
fresh. `H-06` is `released @ 459b72df`, still OPEN. The campaign moved no input digest and owes
no re-proof.

The capability corpus is now single-standard: **151 nodes / 767 `(node, capability)` pairs**
were re-judged under the prevalence standard in **34 dispatches (`batch117`–`batch150`) by 25
truthfully named GPT-Terra identities**. The largest identity covered 11 nodes, below §6H's 25.
Verdicts: **593 PROVIDED / 174 NOT_PROVIDED**. Filing was mechanical through
`tests.attester_file`; the dispatching session authored no verdict.

Measured alone after filing:

| stage | count | note |
|---|---:|---|
| `capability_phase2` | **173** | 173 CONTRADICTED; 0 UNATTESTED, STALE, UNADJUDICABLE, §6G, §6H, or other |
| `judgment_reviews_5` | **1252 module / 1253 stage** | unchanged; still 151 schema-v2 blind re-reviews owed |
| `assertion_coverage_8` | **3 in 1 family** | downstream of the red §6F baseline; do not re-run expecting movement |

The old-instrument count was 57. **57 → 173 is the sharper instrument working, not a content
regression.** It also changes rater family from Claude-era records to GPT-Terra; cross-family
agreement remains unmeasured. A lone NOT_PROVIDED still requires an independent confirmation
before engineering work. Do not tune the count downward.

**NEXT:** Priority 2 is the seven-dispatch §5 schema-v2 blind re-review campaign. Use
`tests.judgment_batches` and file the dispatch-time skeletons through `tests.file_reviews`;
never rebuild samples at filing time. Only after the §5 queue is single-standard should source
work be batched against confirmed capability findings.

Named operational defects/limits retained: per-node packet files are mandatory because item IDs
restart at `item_001`; several Attesters initially returned wrong JSON enums/keys or combined
node files, and the mechanical join rejected every malformed return before filing. The existing
Graphify index is on the legacy pre-#1504 node-ID scheme and its campaign query was weak, so
executed repository tooling—not that traversal—was the evidence source.

---

## 2026-09-22 (historical) — CLOSEOUT REVIEWED AND COMPLETED.

Tree is **CERTIFIED** at `dfae9bbb7a1398d7`, worktree clean, all four artifact families fresh.
`H-06` is `released @ 505baf4e`, still OPEN. The chain is current — **do not re-run it.**

**Measured state, each stage run ALONE:**

| stage | count | note |
|---|---|---|
| `capability_phase2` | **57** | 57 CONTRADICTED, 0 UNATTESTED, 0 STALE, 0 UNADJUDICABLE |
| `judgment_reviews_5` | **1252 module / 1253 stage** | quote the ENTRY POINT; the ±1 is `run_all`'s rollup, not pollution |
| `assertion_coverage_8` | 3 in 1 family | the §6F cluster, INVALID against a red `capability_phase2` |

Corpus **149/152**; survivors are exactly `contradicted_attestation`,
`attestation_drops_options`, `attestation_leaks_into_phase1`. Phase 1 at its floor of 5.
Operator coverage **41/41**. `run_all` exits 1 — **the Definition of Done is NOT met.**

**READ THIS BEFORE YOU TRUST `capability_phase2`'s 57.** The corpus now mixes TWO Attester
standards. Owner ruling 9 made prevalence part of the standard, and only the 18 verdicts on
`mat_g1_na_q3_7`, `mat_g2_mg_q2_0`, `mat_g2_mg_q2_2` and `mat_g3_mg_q2_3` (`batch116`) were
judged under it. The other ~723 were judged on the superseded neutral standard. **57 is
therefore a two-instrument number.** Owner ruling 10 adds a second variable for any NEW
dispatch: `gpt-terra` light-thinking rather than Haiku, which is a different rater FAMILY, and
the measured 88.1% agreement is Haiku-against-Haiku and does NOT transfer.

**What that means operationally:** a cross-standard or cross-family NOT_PROVIDED landing against
an older PROVIDED is **not, on its own, a regression**. Nothing currently separates a genuine
finding from an instrument effect. The resolution is the corpus-wide ruling-9 re-dispatch
campaign (~33 dispatches, no re-proof owed because attestation is outside the fingerprint).

**A correction that half-landed TWICE, and the rule that stops a third time.** The renderer fix
cited a §5 figure that was never the renderer. That claim was written into FIVE digest-bound
places; the first correction pass named three, the closeout found a fourth and correctly named
it out-of-list, and a fifth was missed by both. All five are now correct. **When correcting a
claim that was copy-pasted into prose, enumerate the sites by sweeping
`mutation_proof._iter_input_files()`, never from memory** — the hand-listed set cost the 3.4h
chain twice.

**Still open under `H-06`:** ~51 CONTRADICTED content findings, the 151 owed §5 blind
re-reviews, the unfixed supersession test, and the ruling-9 campaign.

---

## 2026-09-22 (historical) — CLOSEOUT COMPLETE; CORPUS NOW MIXES TWO STANDARDS

Tree is **CERTIFIED** at `0d8a8ec3f9812aba`; the full chain is current and costs nothing to
redo. `H-06` is `released @ 2b7c6d18`, still OPEN.

* **The deferred source batch is DONE.** The three renderer-evidence strings now identify
  55-under-load versus 61-on-three-clean-runs as the measured concurrency symptom; the §5
  1252/1253 difference is correctly documented as module versus `run_all` stage rollup.
  `docs/testing_pipeline.md` now documents §1M and operator coverage is **41/41**.
* **`batch116` is filed from the already-earned blind Haiku prevalence verdicts.** It adds 18
  verdicts over four nodes: 12 PROVIDED and 6 NOT_PROVIDED. `capability_phase2` is now **57
  CONTRADICTED, 0 UNATTESTED, 0 STALE, 0 UNADJUDICABLE** (up from 53 because the instrument got
  sharper, not because content changed).
* **The corpus is mixed-standard.** These 18 verdicts were prevalence-weighed under owner ruling
  9; the earlier 741 verdicts were earned under the superseded neutral standard. Therefore 57 is
  not a single-instrument prevalence estimate. The corpus-wide ruling-9 campaign remains owed.
* **Owner ruling 10 changes future dispatches from this agent to `gpt-terra` light-thinking.**
  That is a second instrument variable: historical verdicts are Claude-family, and cross-family
  agreement is UNMEASURED. Do not call a GPT-Terra NOT_PROVIDED against a Claude-era PROVIDED a
  regression; separate family effects only with the clean same-prompt/same-packet family control.
* **The re-proof is complete.** Mutation corpus **149/152**, with exactly the known invalid §6F
  cluster; six release shards each cover 96,885 cache keys / 387,540 represented executions with
  zero failures; aggregate 9,323.807s, worst 1,591.542s. `run_all` completed every scheduled stage.
* **Three tracked stages remain red:** `judgment_reviews_5` = **1253 at the stage entry point**
  (1252 module + one rollup); `capability_phase2` = **57**; `assertion_coverage_8` = **3 in one
  §6F family**. This is the expected H-06 debt, not a clean Definition of Done.
* **Named out-of-scope stale text:** `run_all.py:105-106` still repeats the misattributed §5
  figure in a comment. It was outside the exact closeout list and was recorded rather than used
  to expand the batch.
* **Do not restart closeout work.** The remaining queues are the 151 blind §5 re-reviews, the
  corpus-wide ruling-9 re-dispatch, the CONTRADICTED content findings, and the supersession test.
  Do not open H-11.

---

## 2026-09-22 (historical) — RULINGS 7, 8 AND 9 ACTED ON

Tree is **CERTIFIED** at `124ee1ca14d20526`; the chain was run in full and costs nothing to redo.
`H-06` is `released @ d86c9508`, still OPEN.

* **Fix A and Fix B are DONE.** Do not redo them. `capability_phase2` **55 → 53**.
* **`judgment_reviews_5` is 1252 from the module and 1253 from the `run_all` stage, and BOTH ARE
  CORRECT.** The plan's instruction not to "restore" 1253 is wrong and is now marked superseded.
  Always quote the entry point with the figure.
* **Owner ruling 9: prevalence is now part of the Attester standard.** All 741 filed verdicts were
  earned on the superseded neutral standard, so today's 53 is an OLD-instrument number. The ruling is
  scoped as a corpus-wide re-dispatch campaign (~33 Haiku dispatches, no re-proof owed) and was
  deliberately NOT half-applied. **Expect the count to RISE.** `batch115` replaces first.
* **THREE CORRECTIONS ARE OWED IN THE NEXT SOURCE BATCH, before you run the chain:** the overstated
  "§5 reported 1253 where it has 1252" sentence in `tests/frontend_renderer.py`'s docstring, the
  `docs/pgen_contract.md` renderer row and the `renderer_case_id_omits_node_id` mutation description;
  plus `docs/testing_pipeline.md`, which lacks a counterpart for the new row
  (`operator_doc_covers_registry` 40/40 → 40/41, passing but a real gap). All are digest-bound, which
  is why they were not done at the END of a chain.
* **The benchmark prints `recommended_shards=4`; `validate_obligations.py:165` hard-codes 6.**
  Follow the validator. Six shards measured 2.593h aggregate, worst shard 1588.9s vs a 1800s budget.
* **Still open under `H-06`:** ~51 CONTRADICTED content findings, the 151 owed §5 re-reviews, the
  unfixed supersession test, and now the ruling-9 campaign.

---

## THE JOB — §6 is now pure content debt; §5 is the last zero-cost campaign

**Phase A is DONE (2026-09-21). Phase B's attestation campaign is DONE (2026-09-22). The
7-node structural blocker is CLEARED (2026-09-22, late). Do not redo any of it, and do not plan
another §6 attestation campaign.** `H-06` is `released @ e18015f0`, still OPEN.

**Read the plan's `START HERE — handoff` for the numbers.** This file does not repeat them,
because two sources of truth is how a session inherits confident wrong ones. In outline:
`capability_phase2` went **218 → 55 and EVERY remaining finding is CONTRADICTED** — zero STALE,
zero UNATTESTED, zero missing-options, zero missing-visual, §6G integrity 0 errors, §6H
plurality PASS. All 151 nodes now carry fresh blind evidence.

**Three stages are still red and the Definition of Done is still NOT met**:
`judgment_reviews_5` (1252), `capability_phase2` (55), `assertion_coverage_8` (3 in 1 family,
still INVALID against a red baseline — re-running cannot fix it).

### Where the remaining work is, and what each piece costs

**§5 — the 151 owed blind judgment re-reviews. THIS IS THE ONLY ZERO-RE-PROOF WORK LEFT, and
it is the largest queue.** `validation_reports/judgment/` is outside the fingerprint, so a whole
review campaign moves no digest. All 151 filed reviews are v1 and unadjudicable; the v1→v2
migration was refused as impossible in principle. **If you want to make progress without paying
3.4h, start here.** Seven dispatches — see the machinery section below.

**§6 — 55 CONTRADICTED, all of it source work, so BATCH it.** Every one owes the chain, so do
not land one fix, re-prove, then land another. It is not one queue:

* **51 are genuine content debt** across 35 nodes, each backed by fresh blind evidence naming
  the exact gap. Build the artifact the clause names, or delete the provider entry; **Content
  Rule 4 decides which** — if the competency names the verb, model or range, building it IS the
  fix and is not scope creep; if it does not, building it is invention and the entry goes. Cite
  the competency clause in the commit and the evidence log. Three different sizes of work sit
  inside this: 24 name a medium, 30 name a verb/range, and **~5 name the verb `draw`**, which by
  owner ruling 3 requires a valid visual formatter — a multiple-choice question ABOUT drawing
  does not satisfy a competency that says draw.
* **4 are NOT content debt.** `mat_g1_na_q3_6` `numbers_example` + `letters_example` and
  `mat_g1_na_q3_7` `objects` + `images` are the §6B ground-truth decomposition defect below. No
  generator can clear them; **do not try to build content for them.** (Counted as 3 in an earlier
  draft — `mat_g1_na_q4_6` `in_pictures` was on that list and has since cleared to PROVIDED, and
  `concrete_models`/`objects` on `mat_g1_na_q3_4`, `mat_g2_na_q3_5` and `mat_g3_mg_q2_2` read
  "concrete **and** pictorial models" / "masses **of** objects", which are CONJUNCTIONS and so
  genuine debt. Check the conjunction/disjunction before classifying any of them.)

**BEFORE YOU BUILD ANYTHING FOR A §6 FINDING — the reproducibility rule.** A measured control
(same prompt, same packet, fresh Haiku identities) puts inter-rater agreement at **88.1%
overall, and only 76.5% on the hardest batch**. Five verdicts moved, in both directions: two of
the five CONTRADICTED on `mat_g2_na_q3_5` did NOT reproduce, and two filed PROVIDEDs failed on
re-judgement. **So never commit engineering effort to a lone CONTRADICTED — confirm it with one
more independent dispatch first.** That costs a single Haiku dispatch and can save days of
formatter work; at 88% agreement, dual-dispatching all 55 would be expected to overturn ~6. Nor
is a lone PROVIDED proof of coverage. The AGGREGATE (218 → 55) is robust because it rests on
hundreds of verdicts; no individual row is. Full numbers, direction of each disagreement, and the
control's own limits are in the plan's `START HERE` and `HARDENING_EVIDENCE.md`.

### Owner rulings, 2026-09-22 — binding, and they resolve forks earlier handoffs left open

1. **The medium test.** When a clause names a medium, decide from the competency's grammar which
   role it plays: the thing the learner must work IN (*illustrate / represent / model / draw …
   **using** X*) → it must actually be rendered; a delivery mode or story context (*given orally
   or in pictures*; a word problem that merely involves objects) → a worded context can satisfy
   it. Ambiguous → judge on the stricter reading and say so. **Never encode the answer in the
   dispatch prompt.** This session's first prompt did exactly that, asserting any medium clause
   needs the medium present, and that is the §6 analogue of the 2026-08-20 transcription defect:
   the Attester answers honestly about the question it was actually asked. Measured consequence —
   with the corrected prompt, `mat_g1_na_q4_6`'s `in_pictures` went CONTRADICTED → PROVIDED on
   real PesoMoney and NumberLine visuals. It was never a content gap.
2. **Filed blind evidence may be retired ONLY once replaced by new valid blind evidence**, and
   the replacement must be verified per record and per pair before anything is removed. This is
   how the 7-node blocker was cleared; the method is in the plan's `START HERE`. **Do not delete
   a filed record on any other basis.**
3. **`draw`-verb findings require a valid visual formatter.** Source work.
4. **Haiku subagents extend to ALL agents reviewing sample pg output**, the §5 campaign
   included. Name the model that actually judged in the record — §6H/§5 independence is only
   checkable if the record is truthful about who made the verdict.
6. **All three workstreams complete under this handoff — no `H-11`.** `H-06` carries the §6
   content debt, the structural/ground-truth defects, and the 151 owed judgment re-reviews.
7. **The §6B ground-truth correction is AUTHORISED for the next session** (owner, 2026-09-22).
   Sign-off is given; the node ids and justification still go in the commit and the evidence log
   per Protocol 5. Spec below.
8. **The fixed-path renderer is to be FIXED in the next session** (owner, 2026-09-22). It is a
   blocker in its own right, not an operating note: it has corrupted two recorded figures, in
   both directions. Spec below.

### The §6B ground-truth decomposition defect — owner-owned, do NOT hand-patch

`requires` extraction promotes **non-normative sentence material** into mandatory capabilities,
so the pipeline is charged with debt the curriculum never asked for. Three measured instances:

* **A disjunction flattened into a conjunction.** `mat_g1_na_q3_7` — "Create repeating patterns
  using objects, images, **or** numbers" — has `requires = [create, repeating_patterns, objects,
  images, numbers]` and no `requires_ignore` at all. Serving numeric patterns fully satisfies
  MATATAG, yet `objects` and `images` report CONTRADICTED for ever.
* **An `e.g.` example promoted to a requirement.** `mat_g1_na_q3_6` — "(**e.g.**, numbers: 2, 4,
  2, 4__, __; letters: a, b, c, …)" — requires `numbers_example` and `letters_example`. A blind
  Attester correctly reported the exact illustrative sequence never renders.
* **One branch of a parenthetical disjunction made compulsory** while the other was ignored.
  `mat_g1_na_q4_6` — "(given orally **or** in pictures)" — `orally` and `or` are in
  `requires_ignore`, `in_pictures` is still required.

**Measured reach, so this is not an anecdote:** 6 nodes carry ≥2 alternatives of ONE disjunction
separately required — `mat_g1_na_q1_2`, `mat_g1_na_q3_7`, `mat_g2_mg_q2_1`, `mat_g2_mg_q2_2`,
`mat_g3_mg_q2_1`, `mat_g3_mg_q2_4` — and 2 carry `example`-derived requirements
(`mat_g1_na_q3_2`, `mat_g1_na_q3_6`). **Four of the six pass TODAY only because the pipeline
happens to serve every alternative**, so the defect is LATENT and grows with grade level as
competencies acquire more alternatives.

It is `requires` / `requires_ignore` — human-authored ground truth under §6B, locked in
`data/skeletons/requires_ignore.lock.json` — so correcting it is a `data/` edit under
`INPUT_ROOTS` needing **owner sign-off (Protocol 5: node id, source, reason)** plus the chain.
**Recommended and NOT applied:** a disjunction contributes ONE satisfiable requirement (or marks
its alternatives mutually sufficient), and `e.g.` material is illustrative and belongs in
`requires_ignore`.

### NEXT SESSION — TWO OWNER-AUTHORISED SOURCE FIXES. Batch them with the content work.

Both are source edits under `INPUT_ROOTS`, so they owe the chain — and so does the content debt.
**Do all the source work in ONE batch, then run the chain ONCE.** Order at the end of this
section.

#### FIX A — §6B: make the `requires` annotation follow its own existing convention

**Do not invent a schema field. The convention already exists and was applied inconsistently.**
Some nodes already collapse a disjunction into ONE requirement and pass cleanly:

```
mat_g2_mg_q2_1   'm or cm'                          -> id 'm_or_cm'                             ONE requirement  ✅
mat_g3_mg_q2_1   'grams, kilograms, and/or milligrams' -> 'grams_kilograms_and_or_milligrams'    ONE requirement  ✅
mat_g3_mg_q2_4   'liters and/or milliliters'        -> 'liters_and_or_milliliters'               ONE requirement  ✅
mat_g1_na_q3_7   'objects, images, or numbers'      -> 'objects' + 'images' + 'numbers'          THREE  ❌
mat_g2_mg_q2_2   'meters or centimeters'            -> 'meters' + 'centimeters'                  TWO    ❌ (latent)
```

So Fix A is: **one disjunction contributes one requirement**, spelled the way `m_or_cm` already
is. `requires` is hand-authored in `data/skeletons/vocab_annotation.json` and carried through
UNCHANGED by `scripts/rebuild_knowledge_graph.py` (which must never synthesise it), so the edit
is to that one file plus a KG rebuild. Entries are `{"clause": ..., "id": ..., "kind": ...}`.

And separately, `e.g.` material is illustrative, not a requirement:

```
mat_g1_na_q3_6   '(e.g., numbers: 2,4,2,4__; letters: a,b,c,...)'  -> 'numbers_example','letters_example'  (kind: range)
mat_g1_na_q3_2   '(e.g., 2+3 = 1+4; 10-5 = 6-1)'                   -> 'example_1','example_2'              (kind: context)
```

**Which findings this clears — exactly 4 of the 55**, and no more:
`mat_g1_na_q3_6` `numbers_example` + `letters_example`; `mat_g1_na_q3_7` `objects` + `images`.
`mat_g1_na_q3_2`'s two and `mat_g2_mg_q2_2`'s two currently PASS, so they are LATENT — fix them
in the same batch while the baseline is clean (Mandate 5), not after they turn red.

**`mat_g1_na_q1_2` is the judgement call in this set, and it is NOT obviously a disjunction.**
Its competency reads "using a variety of concrete and pictorial models (e.g., number line, block
or bar models, **and** numerals)" — an `e.g.` list joined by "and", so it may be a conjunction of
required models, a list of examples, or both. Decide it explicitly and record the reading; do not
let it ride on the pattern of the others.

**What Fix A also drags in — check all of it before running the chain:**

* **Renaming a capability id orphans its `CAPABILITY_PROVIDERS` entry**, and §6 Phase 1's
  `_validate_no_orphan_providers` will name it. Update the table in the same commit.
* **A new capability id has no attestation**, so §6F reports it **UNATTESTED** — worse than the
  CONTRADICTED you removed. **Re-attest every touched node in the same session**, via
  `tests/attester_packets.py`, batch prefix above `batch114`. This is the same trap that made
  deleting records measure 61 → 82.
* `requires_ignore` is locked in `data/skeletons/requires_ignore.lock.json` and compared by
  §6B's `_validate_requires_ignore_lock`. If you move a word into `requires_ignore`, the lock
  moves with it, in the same commit.
* Protocol 5: the commit and the evidence log carry the node id, the competency text, and the
  reason. Owner ruling 7 is the sign-off; it does not replace the record.

#### FIX B — the fixed-path renderer, and the SILENT mechanism behind it

`tests/frontend_renderer.py` writes `local_only/scratch/frontend_packet_render/{corpus,result}.json`
— **fixed paths, no pid, no uuid, no lock** — and six call sites funnel through it, including both
§5 and §6F's freshness pass. Two concurrent runs overwrite each other's corpus and result.

**The loud failure is already guarded** (`if set(active) != set(by_id): raise RuntimeError(...)`,
which is what made §5 crash with "renderer returned active evidence for [~400 packets]").
**The SILENT failure is a second, separate defect and it is why a figure can move quietly:**

```python
case_id = f"packet-{index}-seed-{sample.get('seed')}"      # tests/frontend_renderer.py:44
```

**`case_id` omits `node_id`** — though `node_id` is right there and is even stored inside the
case. So two different nodes' packets both produce `packet-0-seed-11`. When two processes
collide, the id SETS can coincide while the rendered structure belongs to the other process, the
`set(active) != set(by_id)` guard passes, and one run attaches the other's visual evidence. That
is how §6F reported 55 where the tree had 61, and §5 reported 1253 where it has 1252 — no crash,
no warning.

**Fix both halves, or the loud guard keeps hiding the quiet one:**

1. Give each invocation its own directory (pid + uuid under `SCRATCH`, cleaned up after), so two
   processes cannot share a file at all.
2. Put `node_id` into `case_id`, so an id collision is impossible and the existing guard actually
   detects cross-talk rather than passing through it.

**It needs a mutation, and the mutation must target the SILENT path**, not the loud one — a plant
that only trips the existing `RuntimeError` proves nothing new. Prove it by constructing two
sample sets from different nodes that collide on `packet-<index>-seed-<seed>` and asserting the
evidence attached is each one's own. Ship the `docs/pgen_contract.md` row in the same commit
(Protocol 7). **Editing `docs/pgen_contract.md` invalidates the whole mutation corpus** — that is
fine here because the batch owes the corpus anyway, but do it before the corpus run, never after.

#### The order for the batch, so you pay the chain once

1. Land **all** source work: Fix A (+ provider table, + lock), Fix B (+ its mutation), and as much
   of the ~51 content debt as you are taking. Rebuild the KG after touching
   `vocab_annotation.json`.
2. **Re-attest every node whose capability ids changed** (zero re-proof, and it prevents the
   UNATTESTED regression). Confirm `capability_phase2` moved the way you expect, run ALONE.
3. Regenerate `_generated_formatter_exclusions.py` if any formatter or COMPATIBILITY entry moved
   (trap 6), and check the pinned counts in `tests/unit/test_obligation_executor.py` (trap 7).
4. **Scan all 150 mutation anchors** (trap 1) — two seconds, versus a fifty-minute abort.
5. Regenerate `tests/frontend_suite.py`'s artifact (~10s), then the benchmark (~16s), then the
   corpus (~70min), then the six release shards (~2.6h). **The benchmark goes AFTER your last
   source commit** (trap 2) and the sweep is the LAST source-affecting act (trap 9).
6. `run_all` alone, output shown. Then `tests/tree_state.py` must report CERTIFIED.

### The machinery — TWO campaigns, TWO toolchains. Do not cross them.

Both dispatch blind, and both refuse to let you retype evidence, but they are different
modules and the §5 one has a hazard §6's does not.

**§6 attestation (DONE):** `tests/attester_packets.py` writes the blind half and the key it must
not see; `render_prompt_block` emits the Attester-facing text verbatim; `tests/attester_file.py`
joins returned verdicts to the key mechanically. The campaign's plan, per-dispatch status and
verdict counts are in `phase2_hardening/attestation_campaign.json` — resumable, claimed by `H-06`.

**§5 judgment review (OWED, 151 nodes):** a DIFFERENT pair.

```sh
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --plan          # the batch plan
PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --batch 3 \
    --blind local_only/scratch/review/b3.txt --skeleton-dir local_only/scratch/review/b3/
PYTHONPATH=. .venv/bin/python -m tests.file_reviews \
    --batch 3 --verdicts <reply.json> \
    --reviewed-by <dispatcher-assigned-identity> --date <ISO> \
    --skeleton-dir local_only/scratch/review/b3/
```

`backend/.../validation/judgment_packets.py` is the underlying builder and has its own CLI, but
dispatch through `tests/judgment_batches.py`: hand-assembling a §5 review is the retyping defect
that module was written to close, on the larger of the two surfaces (151 reviews × 6 rationales).

**Two §5-specific rules that have no §6 analogue, and one of them is a trap that PASSES:**

* **File the samples from the DISPATCH-TIME skeleton (`--skeleton-dir`), never a rebuild at
  filing time.** `file_reviews.py`'s first version rebuilt the packet when filing — which sounds
  stricter and is the one mistake that cannot be detected afterwards. A generator fix landing
  between dispatch and filing (the NORMAL case, since the point of a batch is to find defects and
  fix them) pairs the reviewer's verdicts with samples it never saw, and §5 freshness PASSES,
  because the samples really are fresh. That is a fabricated review with a clean bill of health,
  manufactured by the tool meant to prevent it. Filing what the reviewer actually saw makes the
  drift VISIBLE instead — the node reports stale and the honest remedy is a re-review.
* **The reviewer identity is assigned by the DISPATCHER and a mismatched reply is refused.**
  Measured 2026-09-10: three independently dispatched blind agents given the same prompt all
  converged on variations of one self-declared name, which would silently weaken §5 reviewer
  plurality and §6H attester plurality alike.

**Scale of the §5 campaign — executed 2026-09-22, not estimated:**

```text
$ PYTHONPATH=. .venv/bin/python -m tests.judgment_batches --plan
batch  1: 25 nodes  mat_g1_dp_q3_0 .. mat_g1_na_q1_9
batch  2: 25 nodes  mat_g1_na_q2_0 .. mat_g2_mg_q1_0
batch  3: 25 nodes  mat_g2_mg_q1_1 .. mat_g2_na_q2_0
batch  4: 25 nodes  mat_g2_na_q2_1 .. mat_g2_na_q4_5
batch  5: 25 nodes  mat_g3_dp_q3_0 .. mat_g3_na_q1_3
batch  6: 25 nodes  mat_g3_na_q1_4 .. mat_g3_na_q4_6
batch  7:  1 nodes  mat_g3_na_q4_7 .. mat_g3_na_q4_7

7 batches of <= 25 ...; each needs its OWN reviewer identity, or §5 reports reviewer plurality.
```

So it is **7 dispatches, not 33** — but each is far heavier per node than a §6 one, because a
§5 review owes 6 findings plus 4 per-sample assessments for every node, where a §6 verdict owed
one answer per clause. Budget accordingly and expect corrective rounds.

Other constraints: schema v2 only, ≤25 nodes per reviewer identity, 6 required
findings per node (`competency_fulfillment`, `comprehensive_coverage`, `cognitive_capacity`,
`variant_comprehensiveness`, `competency_alignment`, `scale_appropriateness`) plus 4 per-sample
assessments (`mathematical_validity`, `contextual_logical_validity`, `ambiguity`,
`learner_facing_clarity`). Rationale skeletons cluster at 3, same as §6G.

**What the §6 campaign learned that carries over, so you do not rediscover it:**

* **A replacement record must supersede EVERY `(node, capability)` pair its predecessor holds**,
  or `_attestation_staleness` keeps reading the old record and its finding never clears. This is
  the mechanic behind the 7-node blocker.
* **Records resolve last-file-wins over a SORTED glob**, so a replacement batch prefix must sort
  AFTER the incumbent. `batch114` is now the maximum (the campaign ran batch080–batch112 and the
  7-node re-attestation added batch113–batch114); start above it.
* **≤25 clause items per dispatch (§6G); ≤25 nodes per Attester identity (§6H).** At 776 pairs
  over 151 nodes that is ~33 dispatches for one clean round.
* **Plan highest-finding-count first.** It front-loads the nodes where CONTRADICTED concentrates
  (2.27 findings/node) and leaves a tail at 1.00, where all-PROVIDED batches are the PREDICTED
  result rather than a sign of a lax reviewer — a distinction worth measuring before you trust
  or distrust a batch.
* **Audit an all-PROVIDED batch before filing it**: count distinct reasoning skeletons (§6G
  allows 3 per cluster) and cross-check every PROVIDED whose clause names a visual medium
  against whether its samples actually rendered one.
* **Dispatch subagents on Haiku and keep concurrency modest.** A 2026-09-21 wave of 8 Opus
  dispatches hit the session rate limit and killed 14 agents mid-flight; the owner's instruction
  is Haiku only. Name the model that actually judged in `attested_by` — §6H independence is only
  checkable if the record is truthful about who made the verdict.

### How blindness works — the owner's ruling, and it is not negotiable

You **DISPATCH** to a separate agent that has neither the answer key nor your context. You never
author a verdict, never re-file one, and never copy a v1 rationale forward.

**Blindness is a prompt contract, not a sandbox**, and a dispatched subagent has tools. Record
`samples_delivery` and `tool_uses_by_attester` as what they actually were; `--tool-uses 0` claims
structural blindness that a tool-bearing subagent does not have, and writing it would be a false
evidentiary claim.

All 151 legacy reviews are v1 and unadjudicable. Use `legacy_review_queue.json` to PRIORITISE,
never as evidence: a v1 `PASS` records only that somebody once wrote PASS, and tick A found
template rationales in that corpus. §6G clusters reasoning skeletons precisely to catch a
fill-in-the-blank verdict stapled onto many clauses, and `template_attestation` is a live,
DETECTED mutation for it. Do not give it something to find.

---

## Read this, in this order

1. **`AGENTS.md` / `CLAUDE.md`** — the Scaling Mandate, Engineering Protocols, Definition of
   Done. Verification is execution; a prediction phrased as a confirmation is a lie.
   The 2026-09-21 ruling supersedes File Management's read-only rule on `validation/`.
2. **`docs/phase2_hardening_completion_plan.md`, `START HERE — handoff`.** It opens with a
   dated block that supersedes everything below it, including the owner rulings in full.
3. The middle of that plan for the *design* of what you implement. Design, never status.
4. **`validation_reports/HARDENING_EVIDENCE.md`**, the 2026-09-21/22 entries, for how the
   current numbers were obtained and what was measured rather than assumed — including the
   campaign's audit of its own verdicts and the named limits of its blindness contract.

---

## Claim your row before you start

`owner` is a work-lock. Claim it, release it on commit (`unclaimed` or `released @ <rev>`).
If your session identifier embeds an H-row token, make sure it is *your own* — that check
exists because a worker once claimed H-07 while doing H-08.

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py     # must PASS before and after
```

* **`H-06`** holds the M2 capability queue. Released `@ e18015f0`, still OPEN, and must not be
  closed by a re-proof alone. Its attestation campaign is COMPLETE and its structural blocker is
  CLEARED. What remains under it, per owner ruling 6 and all in one row: **51 CONTRADICTED
  content findings, 4 CONTRADICTED that are the §6B ground-truth defect (AUTHORISED, ruling 7),
  the renderer concurrency defect (AUTHORISED, ruling 8), the still-unfixed supersession test,
  and the 151 owed blind judgment re-reviews.**
* **`H-10`** is the interruption-safety row, released `@ 7912add7`, still OPEN: the machinery
  exists and its mutation is detected, but the row's own finding is only half answered.
* **`H-02`, `H-05`, `H-07`, `H-08`** are open and unclaimed. `H-02`'s 3 remaining §6F errors are
  downstream of `capability_phase2` reaching 0. Since 2026-09-22 that means clearing the 55
  CONTRADICTED — all source work — because every evidence-shape and structural finding is gone.
  Re-attestation cannot move them.
* Splitting **H-08's intro-surface render gap** into its own row is still the OWNER's call.
  The row set can express `H-11` now; that is not permission to open one.

**Edit the ledger SURGICALLY.** `json.dumps(ensure_ascii=True)` over the whole file
renormalises `§`/`—` escapes across rows you do not own; a 2026-09-20 session produced 16
lines of collateral churn that way and had to revert. Patch the lines you mean to patch, and
check `git diff --numstat` shows only what you intended.

Every artifact you add under `validation_reports/phase2_hardening/` — including inside
subdirectories — must be claimed by some row's `proof_artifacts`, or the ledger fails.

---

## If you arrive mid-anything

A handoff can happen at any moment; hardware and environment failures are outside a session's
control, and the owner ruled that "must end certified" is NOT the rule.

* **Run `tests/tree_state.py` first.** If an intent is open it tells you what was in flight.
* **Shards are individually resumable.** Each receipt records its own digest. Re-run only the
  stale indices — a 2.5-hour saving you get by reading digests instead of guessing.
* **A surviving mutation has TWO causes** and you must tell them apart: the check is broken,
  or the plant no longer reaches the code the validator runs. Diagnose by instrumenting the
  real path, never by reading the validator and concluding it would work.
* **`INVALID — the unmutated command baseline exited 1` is a THIRD thing** and is neither.
  The runner refused to score, because the baseline was already red. Re-running cannot fix it.

---

## Traps that cost real time

1. **Scan all 150 mutation anchors BEFORE running the corpus after any source batch.** A
   2026-09-21 run aborted at 54/150 because a batch edit had moved one anchor. The scan takes
   two seconds; the abort cost fifty minutes.
   ```sh
   PYTHONPATH=. .venv/bin/python -c "
   from pathlib import Path; import tests.mutation_harness as mh
   print([(m.name, r) for m in mh.MUTATIONS if m.edits for r,(f,_) in m.edits.items()
          if Path(r).read_text().count(f) != 1] or 'all anchors OK')"
   ```
2. **Re-run the benchmark AFTER your last source commit, not before.** A commit landing
   between the benchmark and the corpus leaves `obligation_benchmark_11` red at baseline, and
   `obligation_benchmark_outlives_source` then scores INVALID rather than DETECTED. Never
   re-prove that one WHILE shards run — its plant edits the module they spend 2.6h inside.
3. **A gate can be defeated one stack frame later — or one ENTRY POINT over.** The
   orchestrator and the adapter enforce formatter rules differently, and the orchestrator
   skips its filter entirely for a PINNED formatter. A student-path fix left the Lab still
   serving an undrawn stem, and §1M could not see it because §1M samples the student path.
4. **A rule copy-pasted into N sites will disagree with itself.** `_number_plurals` lived in
   SIX places; `length_measurement` kept its own `_sing()` beside the shared inflection rule.
   Consolidate, and route through the same helper the validator imports.
5. **A classifier that keys on a MESSAGE STRING is a latent bug.** The exclusions generator
   told an eligibility refusal from a content crash with
   `"is not supported by any DNA" not in str(exc)`, so ~27 node/formatter pairs stayed
   wrongly advertised and `formatters_reachable` counted them as content debt for weeks. It
   is a type now, `FormatterNotEligible`.
6. **`_generated_formatter_exclusions.py` goes stale** whenever a formatter or COMPATIBILITY
   entry changes; §2B fails loudly naming each entry. Regenerate with
   `PYTHONPATH=. .venv/bin/python3 -m scripts.regen_formatter_exclusions`. **Never hand-edit
   it** — it is derived empirically because three attempts to model the rules statically drifted.
7. **Adding a formatter changes the obligation product**, so pinned counts in
   `tests/unit/test_obligation_executor.py` move. Confirm every added route is actually SERVED
   at several seeds *before* touching those numbers. Updating a count to match reality is
   legitimate; updating it to make a test pass is not.
8. **The fast unit suite takes ELEVEN MINUTES**, not the 35 seconds an old note claims, and
   `tests/pytest.ini`'s `addopts` is NOT picked up from the repo root — pass `-m "not slow"`
   explicitly or the two 15–40 minute pool tests run too. Background it.
9. **A shared distractor helper can be right for arithmetic and wrong for your domain.**
   `augment_distractors` refuses negatives but allows ZERO — correct for sums, and it put a
   `0 g` option against a `1 g` answer. Filter in your formatter.
10. **The pre-commit hook rebuilds Graphify and stages `graphify-out/`.** Expect more files in
    the commit than you staged. It does NOT move the input digest — verify that rather than
    assume it.
11. **[LARGELY CLOSED 2026-09-22 under owner ruling 8 — see the correction below before
    trusting the rest of this trap.]** `tests/frontend_renderer.py` now renders every
    invocation in its own `run-<pid>-<uuid4>` directory AND puts `node_id` in `case_id`,
    so two callers can neither share a file nor mint the same id. Both halves carry their
    own DETECTED mutation (`renderer_shares_one_fixed_render_path`,
    `renderer_case_id_omits_node_id`). **AND THE §5 HALF OF THIS TRAP WAS NEVER THE
    RENDERER AT ALL:** the 1252-vs-1253 difference is `run_all.py:760-764` appending one
    aggregate finding the module's CLI never emits — module 1252, stage 1253,
    deterministic, measured with nothing running. Quote the ENTRY POINT alongside any §5
    figure. The §6F observation (55 under load against 61 clean, three times) was real and
    is what the fix addresses. Contention is still not serialised, so prefer measuring
    alone. Original text follows.

    **Do not run anything heavy concurrently, and the failure is not always loud.**
    `tests/frontend_renderer.py` writes to one fixed path with no PID and no lock; six call
    sites funnel through it, including BOTH §5 and §6F's freshness pass. Unfixed. The
    documented symptom was §5 crashing (`renderer returned active evidence for [~400
    packets]`), but on 2026-09-22, when the tree stood at **61** findings, `validate_capability
    --phase 2` run alongside a running `validate_judgment` reported **55** — while three runs
    alone all reported 61. **It under-reported by six, silently.** (Do not read those two figures
    as today's count; the tree is now 55 for unrelated reasons.) It also perturbs UPWARD: the
    `judgment_reviews_5` figure of 1253 recorded on 2026-09-21 is 1252 on inputs `git` proves
    byte-identical (no change to `validation_reports/judgment/` and no source change since
    `664fbe46`), and 1252 is stable across two clean runs. **Neither a lower nor a higher §5 /
    §6F count means anything unless it was measured with nothing else running.** Measure each
    stage ALONE before you write its number anywhere.
12. **Cosmetic edits cost 3.4 hours.** A 2026-09-20 session realigned four import
    continuation lines AFTER completing the chain and invalidated the whole re-proof. Once
    certified, touch no source you do not mean to change.
13. **`git commit --amend` moves the hash**, so a ledger row written as `released @ <hash>`
    before the amend points at a dangling commit. Release in a follow-up commit.

---

## Still owner-owned — do not hand-patch around these

**`CSI-R1`–`CSI-R3`** are open owner rulings in `context_semantics_inventory.json`. `CSI-R4`
is ruled and closed. Splitting H-08's intro-surface gap into its own row is also the owner's —
and note owner ruling 6 already refused a new row for the §5 campaign, so the bar for opening
`H-11` is higher than "the schema allows it".

**The §6B ground-truth decomposition defect WAS owner-owned and is now AUTHORISED** (owner
ruling 7, 2026-09-22). `requires`/`requires_ignore` is still human-authored ground truth and
still locked, so the correction carries node id, source and reason per Protocol 5 — the ruling is
the sign-off, not a substitute for the record. **4 of the 55 CONTRADICTED are this.** Never edit
the lock merely to make a finding go away: the test is whether MATATAG wrote "or"/"e.g.", which is
a reading of the competency text you must quote.

---

## Limitations left standing — named so you keep looking

* **§1M's deixis list is CLOSED.** A stem that points in wording nobody has seen yet is not
  caught; the pattern count prints with the pass line so the hole's size is a number. It also
  cannot tell whether the drawn visual is the RIGHT one — "look at the pictograph" beside a
  drawn clock passes §1M and is §1G's and §9's business — and it cannot see a display the
  pupil needs but the stem never mentions. It reads stems, not hints.
* **§1J's mirror direction does not gate** (a singular noun after a count of two or more is
  measured and printed only), count/verb agreement is unchecked, and neither lint reads the
  visual payload's own labels.
* **A DECLARED variant axis restricted by `FORMATTER_VARIANT_SUPPORT` is still unchecked on
  the orchestrator's PINNED path.** `assert_formatter_supports` is deliberately scoped to
  UNDECLARED axes: caps, profiles and `ctx.values` do not share one vocabulary, and widening
  it refused every pinned render on `mat_g2_mg_q2_0` (§2B) and 46 producible declarations on
  `mat_g1_na_q1_7` (§2I). Closing it needs sentinel resolution, per-DNA.
* **A legitimate axis value of `0`, `""` or `False` is never enforced by either path**,
  because both skip falsy values — a guard that exists only to survive `division`'s
  `remainder` name collision. No current axis uses one.
* **`fraction_model_read` cannot draw an improper fraction** (it emitted `shaded_parts=7` in a
  shape with `total_parts=3`), so `mat_g3_na_q4_6` is served by `fraction_shade` alone.
* **The ANY reading of `formatter_refused_at_node` is not mutation-covered at its own
  comparison.** The `wanted & allowed` boundary itself is unproven.
* **Nothing asserts a pictograph's symbol COUNT equals the table's answer.** Verified once, by hand.
* **`ScaleRead` and `GeometryFigure` geometry are proven by arithmetic on emitted attributes,
  not layout** — jsdom has no layout engine, the blind spot §12 already names for
  NumberLine/BarChart. The elements exist and are distinct; nothing proves they are legible.
* **The estimate-task floor gates nothing.** A sibling DNA framing estimation as rounding
  would reproduce the zero-measurement defect with every gate green.
* **§8's execution accounting is stubbed** and stays provable only against a green live
  corpus. Do not describe §8 as fully proven.
* **`comparing_ordering` and `missing_number` each declare a `visual_home` that
  `base_generator` can never read** (it reads it only for `visual_read` DNAs; both are
  `algorithmic`). Measured no-ops. Fixing them is a DNA edit belonging to its own change.
* **The Phase 1 network guard patches ONE interpreter**, so connections opened inside children
  of `unit_tests`, `census_7` and `behavioural_matrix` are invisible; Phase 2 stages are
  unguarded; loopback is allowed.
* **A single blind verdict is ~88% reproducible, 76.5% on hard batches** (measured 2026-09-22
  over 42 of 741 verdicts, same prompt, same packet, fresh Haiku raters). Verdicts are earned and
  re-renderable, but one verdict is not settled fact. Dual dispatch before building; see the
  reproducibility rule above.
* **THE SUPERSESSION DEFECT IS UNFIXED — only its findings were cleared.**
  `_attestation_staleness` skips a predecessor only when EVERY pair it holds is superseded, and
  it counts a verdict on a capability nothing consults as live ownership. The 7 affected records
  were retired manually on 2026-09-22 under owner ruling 2. Any future grade whose
  `requires_ignore` grows, or any `requires` id renamed after attestation, reproduces it and will
  need the same manual retirement chain. The scaling fix — disregard non-consulted pairs in the
  supersession test — is still open and owes a named mutation plus a contract row.
* **Retiring a record PROMOTES the previous holder of its orphan pair.** Found by doing it:
  deleting the 7 reporting records left 2 STALE when `batch023` inherited
  `('mat_g1_na_q1_9','orally')` from the deleted `batch028`. Retirement is iterative; it took 4
  rounds and 13 records. Re-measure after every round rather than assuming one pass is enough.
* **Nothing makes an Attester weigh PREVALENCE.** A clause can be ruled PROVIDED on the strength
  of one seed in ten — measured on `mat_g1_na_q3_0` `concrete_pictorial`, where a second rater
  failed it on the other nine. The packet format offers no notion of "how often", so a competency
  demanding a model is satisfiable by a single lucky seed.
* **[FIXED 2026-09-22, ruling 8.]** ~~`tests/frontend_renderer.py`'s single fixed path has
  now corrupted TWO recorded figures~~ — and only ONE of the two was ever the renderer.
  The §6F figure (−6) was; the §5 figure (+1) was the `run_all` rollup above. Both halves
  of the renderer defect are fixed and mutation-covered. **Residual:** uniqueness is per
  `(pid, uuid4)`, not a lock — cross-talk is gone, contention is not.
* **SUPERSEDED, kept so a stale copy is recognisable:** `tests/frontend_renderer.py`'s single fixed path has now corrupted TWO recorded figures
  (§6F by −6, §5 by +1) — a live defect, not an operating note. **Owner ruling 8 authorises
  fixing it next session**; spec in the NEXT SESSION section. Until it lands, trap 11 stands and
  every stage figure must be measured with nothing else running.

---

## Rules this handoff will not let you skip

- **The Definition of Done is an executed `run_all` with its output shown.** It is currently
  **NOT met** and this document does not claim otherwise. A green subset is not completion.
- **Never weaken a check to make it pass.** If a gate is red, the bug is in the pipeline. The
  one exception is documented ground-truth error, reported with node ID and justification.
- **Prove a check by executing a planted violation**, not by reading the validator.
- **Check that your mutation is not passing for the wrong reason.** A plant that edits a
  digest-bound module reds the freshness check by itself, so the command exits 1 whether or
  not your gate works. Break your own gate deliberately and confirm the marker disappears.
- **A fix at the data layer gates nothing.** Where you fix content without a gate, say so.
- **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
  the evidence log. A gate described as total is how the next agent stops looking.
- **File an Evidence section** in `validation_reports/HARDENING_EVIDENCE.md` with the exact
  commands, verbatim output, and seeds for anything found or fixed.
