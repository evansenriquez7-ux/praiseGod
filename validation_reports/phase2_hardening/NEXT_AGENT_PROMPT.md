# Task prompt: finish Phase 2 hardening (host-neutral)

**Rewritten 2026-10-07 after a review of the Claude (2026-09-30 → 10-03) and GPT (10-05 → 10-07)
sessions. This REPLACES every earlier version of this file.** `CLAUDE_AGENT_PROMPT.md`,
`GPT_HANDOFF_PROMPT.md` and `HANDOFF_PROMPT.md` beside it are history. Their §5–§10 method notes (the
review addendum, audit-before-filing, the heavy-run checklist) remain correct and are cited below. Their
state sections and queue sizes (173, 127, "15 STALE", "7 content-changed + 136") are stale; ignore them.

Trust order: a command you executed > this file > `CLAUDE_AGENT_PROMPT.md` > the dated blocks in
`docs/phase2_hardening_completion_plan.md`.

Goal: `PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all` exits 0, with the
three §6F mutations DETECTED (201/201), not INVALID. This will take several sessions. Each session must
leave the tree CERTIFIED or honestly INTERRUPTED, with every number re-measured.

---

## 0. Read first

1. `CLAUDE.md` / `AGENTS.md`: Scaling Mandate, Engineering Protocols, Content Rules, Definition of Done.
2. This file, completely.
3. `validation_reports/HARDENING_EVIDENCE.md`: the last four entries (from "W2 step 1" on).
4. `CLAUDE_AGENT_PROMPT.md` §5 (the four-part dispatch addendum and audit), §7 (heavy runs), §8 (the
   anchor one-liner), §9 (traps), §11 (not yours).

---

## 1. State at handoff (re-measured 2026-10-07; re-measure before quoting)

```
HEAD                latest bookkeeping commit; code checkpoint 314a745a; worktree clean; H-06 lock held
tree_state          honestly INTERRUPTED; open batch intent, source changed since certified digest
run_all             EXIT 1 on 2026-10-07 baseline, failed=3 (before Phase 2 instrument edits)
capability_phase2   124 CONTRADICTED over 55 nodes, 0 STALE         (validate_capability --phase 2: EXIT 1)
judgment_reviews_5  151 reviews: 78 PASS / 49 CONCERN / 24 FAIL, 0 STALE (validate_judgment --all: EXIT 1)
                    449 per-sample dimension findings on 49 nodes, plus node-level findings
assertion_coverage_8  the 3 §6F mutations, INVALID until capability_phase2 reaches 0
mutation corpus     full corpus not re-measured after edits; focused new mutation 1/1 DETECTED
```

---

## 2. What the review of the last two sessions found (why this plan differs)

Each finding came from an executed command: `validate_capability --phase 2`, `validate_judgment --all`,
and a per-node dump of `validation_reports/attestation/batch*_<node>.json`. Re-derive them before you
rely on them; none is yet recorded in `HARDENING_EVIDENCE.md`. Recording them is a Phase 0 task.

**F1. More than half the capability queue is partly an artifact of the measuring tool.** Of the 124
CONTRADICTED findings, **68** have reasoning stating that the clause *does* appear, just in 1–4 of
10 samples. Ruling 9 ("weigh how often") sets **no threshold**. The W2 dispatch instructions added one
("one or two incidental samples = NOT_PROVIDED"), and Attesters extended it to 30–40%. That contradicts
ruling 1's "never encode the answer in the dispatch prompt". Worse, many of these are **enumerated
sibling clauses that cannot all pass at once** on 10 samples:
- `mat_g3_dp_q3_2`: tables 3/10, horizontal 3/10, vertical 4/10, which sum to 10/10 and all three fail.
- `mat_g2_na_q1_3`: twos/fives/tens/twenties/hundreds at 1–2 each, plus fifties absent.
- `mat_g3_dp_q3_4`: certain/impossible/equally/more-most likely at 1–2 each.

Engineering against these verdicts would tune generators to a noisy judge, not to MATATAG.

**F2. Last-file-wins lets one judge overturn a majority of three.** W2 step 2 established
majority-of-three because a second Haiku judgment flipped 22.4% of verdicts. The 10-06/07 refresh then
filed **single** GPT-5.6 Luna records, a different rater family whose agreement with Haiku has never been
measured. Because the newest record wins every key it judges:
- on `mat_g2_mg_q1_1`, one Luna record reversed the Haiku majority on `circles` (N→P) and
  `square_grids` (P→N) and added `decompose_figures`;
- on `mat_g3_mg_q1_0`, it cleared `square_figure` and raised `estimate_area`, which all six earlier
  judges had passed.

Part of the 127→124 movement is a change of judge, not of content. The real engineering progress is
the 4 findings cleared on `mat_g1_mg_q1_0`, and those rest on one judge too.

**F3. The judgment gate cannot converge as built.** `judgment_reviews_5` requires every sample of all
151 nodes to PASS on every dimension from one LLM reviewer per node. With a measured ~20% flip rate there
is no rule for a reviewer claim the dispatcher has *disproved by rendering*. The only way to remove one is
to re-dispatch until a reviewer stops making it. On `mat_g2_na_q2_7` the GPT session set aside two
replies as "falsely claiming". Disproof is not one of the allowed set-aside grounds (overall
contradicting its verdicts, unparseable after one repair, skipped samples). That is reviewer shopping,
even when done in good faith.

**F4. Throughput.** One W2 source batch, for one node and 4 findings, cost about two days: the ~5 h
chain, then re-review and re-attestation of every node it staled. At that rate, 55 + 73 nodes is months.
Batches must group by **shared artifact** and pay the chain **once per batch**, not once per node.

**F5. Bookkeeping defects.**
- The W2 step 2 evidence cites `945192c4`, an orphaned pre-amend twin; the commit on main is `67df6151`.
- The Claude session stopped on 10-03 with 25 reviews and 26 attestations uncommitted and four source
  commits that had no re-proof chain. The GPT recovery (`bc041f32`) handled this correctly.
- Three overlapping prompt files carried contradictory queue sizes.

What went well, and should be kept:
- measuring the flip rate. Majority-of-three itself is superseded by ruling 20's one confirming
  judge, but the 22.4% figure is why every evidence entry must name that noise;
- the dispatcher-guard fix (`note.sh` had excluded `key.json`);
- structural v1 diffs proving no verdict changed;
- per-node dispatch ids;
- refusing to edit historical records;
- the GPT session's careful recovery audit and complete re-proof chain.

---

## 3. OWNER RULINGS 19–21 (given 2026-10-07; recorded in `docs/phase2_hardening_completion_plan.md`)

The gates the review raised are **resolved**. Read the full text in the plan doc; in short:

**Ruling 19: enumerated sibling clauses are judged by design.** A clause that is one item of a list in
the competency (skip intervals, graph orientations, likelihood words, coin and bill types, named figures)
is PROVIDED when the generator serves it by design (a variant or DNA path produces it) and it is observed
in at least 2 samples of a packet stratified so that every sibling is sampled. Ruling 15's 50% applies to
medium clauses by set composition, not to sibling items. Non-enumerated clauses stay under ruling 9 as
written. **No dispatch prompt states a numeric threshold that no ruling states.**

**Ruling 20: any model family may judge; the attestation quorum is one confirming judge.**
- Use whatever model your host can dispatch. The identity must name the model that actually judged.
  Never rename an existing record.
- Any attestation verdict that would **clear or create** a CONTRADICTED finding gets one further
  independent blind judge on the same packet. If the two disagree, **the confirming (later) judge's
  verdict stands**. Last-file-wins already implements this, so **no validator change is owed**.
- File the confirming record last, after the first, with `--supersedes`. Never edit either record.
- Named consequence, which must appear in every evidence entry that relies on it: a single judge
  flipped 22.4% of verdicts in W2 step 2, and this quorum accepts that noise for cost.
- The 7 nodes whose latest verdicts came from single unconfirmed GPT-5.6 Luna records
  (`mat_g1_na_q3_6`, `mat_g1_mg_q1_0/1/2`, `mat_g2_mg_q1_0/1`, `mat_g3_mg_q1_0`) owe one confirming judge
  for every verdict that moved a finding relative to the record before it.

**Ruling 21: a disputed reviewer claim is settled by one other reviewer.**
- If you believe a non-PASS review claim is false (for example, a render at the cited seed disproves
  it), do **not** set the reply aside on that belief.
- Record the disproving render in the evidence log. Harvest **all** of the reply's non-PASS claims into
  the evidence log, so confirmed ones are not lost.
- Dispatch the node to **one** fresh blind reviewer that has seen none of the earlier exchange. That
  reviewer's verdict settles the claim, and its record is filed as the node's review, through the
  normal filer with its own dispatch id.
- The set-aside grounds are unchanged: an overall that contradicts its own verdicts, JSON still
  unparseable after one repair, or a skipped sample.
- **No validator change is owed.** The filer already replaces the node's review in place.

**Still a stop-and-ask:** any new content judgment that MATATAG and rulings 1–21 do not settle, any
production verb Phase 4 cannot map to rulings 3, 13 or 16, and anything in "Not yours" (§5).

---

## 4. Plan

**Current checkpoint (314a745a, 2026-10-07):** Phase 0 is complete. Phase 2a has a committed,
focused-test-proven implementation for *explicit reachable* `CAPABILITY_PROVIDERS.variants`, including
private render evidence, deterministic seed allocation, an opaque seed map, freshness replay, a contract
row, and mutation `attester_packet_drops_provider_variant_samples` (focused 1/1 DETECTED). It is not yet
the ruled instrument: execution showed that skip-interval capabilities have no `variants`, while `certain`
and `impossible` share the same broad `scenario_type` variant. Therefore the current code cannot guarantee
two observations of every ruling-19 sibling. The batch intent remains open and the tree is honestly
INTERRUPTED. Do not run the full chain or Phase 3 until the owner chooses whether the provider registry may
gain attester-only observable selectors (or supplies another ground truth for those sibling strata).

### Phase 0: baseline and lock (always, about 1 h)

1. Heavy-run check (§5). Confirm CERTIFIED and a clean worktree.
2. Claim H-06: edit only its `owner` line, check that `git diff --numstat …hardening_status.json` reads
   `1 1`, and commit.
3. Run `run_all` alone to a log and capture `EXIT`. Record per-stage counts. It has not been measured
   since 10-06.
4. Fix F5's citation: add a dated correction line to the W2 step 2 entry naming `67df6151`. Do not
   rewrite the old text.

### Phase 1: owner gates. RESOLVED 2026-10-07 (rulings 19–21, §3). Nothing to do.

### Phase 2: instrument work (harness only; one `batch` intent; one chain at the end)

Scaling Mandate items 1, 3 and 5 apply: these gates must be proven before they police anything.

2a. **Stratified attester packets** (`tests/attester_packets.py`). For each clause, derive its provider
variants from `CAPABILITY_PROVIDERS`. Never hard-code node lists. Guarantee at least 2 samples per
provider variant, and choose seeds deterministically from the variant, so the same sibling always
gets the same seeds. Print the seed map into the packet.
- Write a contract row in `docs/pgen_contract.md`.
- Add a mutation in `tests/mutation_harness.py` that drops one provider variant's samples. The packet
  check must catch it by name.
- Name the limit: stratification proves the variant *can* render the clause, not that students see it
  often. Ruling 19 defines "by design".

2b. **Dispatch instructions** for attesters and reviewers: rewrite them from rulings 1, 9, 12, 13, 15
and 19–21 verbatim. They must carry no numeric threshold beyond what a ruling states. Save the exact
text under `validation_reports/phase2_hardening/` (the W2 text was never saved, a named limit).

2c. Rulings 20 and 21 need **no validator change**: last-file-wins and in-place review filing
already implement them. Do not touch supersession. If you find that either ruling cannot be carried out
with the current validator, stop and report it; do not engineer around it.

2d. Run the full re-proof chain (§6) once, after the last Phase 2 commit. Any mutation added in 2a
counts only once the full corpus table shows it caught by name; a `--only` run cannot check the pins.

### Phase 3: re-attest the queue under the ruled instrument (no source, so no chain)

- Re-attest all 55 CONTRADICTED nodes with stratified packets: one blind judge per node, one identity
  per node.
- Ruling 20: every verdict that clears or creates a finding gets one confirming blind judge on the same
  packet, filed afterwards with `--supersedes`. The confirming verdict stands.
- Give the 7 single-Luna nodes (§3) their confirming judges in the same pass.
- File through `tests/attester_file.py`, dry run first.
- Measure and record:
  - how many of the 68 "rare" findings clear;
  - how many of the 52 "absent" findings clear;
  - the first-vs-confirming disagreement rate. Compare it with W2's 22.4%, and state that it is
    cross-family wherever the families differ.
- **The result is the true engineering queue.** Expect most of the absent group to remain.

### Phase 4: content batches by shared artifact (each is one `batch` intent, one chain)

Every change quotes the MATATAG clause it builds toward (Content Rule 4) in the commit and the evidence
log. Within a batch, iterate in a **dev loop**: focused unit tests, the node's validators, and
`mutation_harness.py --only` for new mutations. Run the **chain once** at the end of the batch. Then
re-review and re-attest, under rulings 20 and 21, every node the batch staled.

Proposed batches, from the absent group. Re-derive membership from the Phase 3 result before starting:

| Batch | Artifact | Findings it targets (current names) | Ruling |
|---|---|---|---|
| P4-1 | Interactive draw / transform formatter | `mat_g2_mg_q1_2` draw_effect, basic_figures; `mat_g3_mg_q4_0` draw; `mat_g3_mg_q4_1` drawing_the_line_of_symmetry; `mat_g3_mg_q1_4` draw_geometric_object; `mat_g3_mg_q1_6` draw_segment_of_given_length | 3, 13, 16 |
| P4-2 | Interactive concrete manipulatives (counters, base-ten, groups) | `mat_g1_na_q1_7` concrete; `mat_g1_na_q2_5`/`q3_0` concrete_pictorial; `mat_g1_na_q3_4` concrete_models; `mat_g2_na_q3_1` concrete_model; `mat_g2_na_q3_5` objects/equal groups; `mat_g2_na_q4_3` groups_of_objects; `mat_g3_mg_q1_4` concrete_model_depiction | 12 |
| P4-3 | Partitioned circles, cut-outs, square grids on `ShapeBoard` | `mat_g2_mg_q1_0` represent, half/quarter circles; `mat_g2_mg_q1_1` decompose, half/quarter circles, cut_outs, square_grids | 1, 13 |
| P4-4 | Fraction media: tiles, charts, similar-fraction sets | `mat_g2_na_q4_3` fraction_tiles, fraction_charts, similar_fractions, denominators; `mat_g2_na_q4_4` similar_fractions | 1 |
| P4-5 | Measurement media | `mat_g3_mg_q2_2` balance_scale, objects; `mat_g2_mg_q4_4` measure, tools | 1, 13 |
| P4-6 | Production verbs on MCQ-only nodes (`illustrate*`, `write*`, `create`, `describes`, `collect_data`, `estimate_area`) | `mat_g1_na_q1_8`, `mat_g2_na_q1_10`, `mat_g2_na_q2_3`, `mat_g2_na_q3_1`, `mat_g2_na_q2_0`, `mat_g1_na_q3_7`, `mat_g1_na_q1_7`, `mat_g3_dp_q3_0`, `mat_g3_mg_q1_0` | 3, 13; ask the owner if a verb is not covered |
| P4-7 | Range and scope gaps in DNA | `mat_g1_na_q3_4` sub_2d_1d; `mat_g2_na_q1_3` fifties; `mat_g2_na_q3_0` 5_groups_of_3 / 5_threes; `mat_g3_na_q2_0` php; `mat_g1_dp_q3_1` without_scale; `mat_g2_na_q2_0` peso coins/bills only | 4 (Content Rule 4) |

Before deleting any provider entry, show that the competency does not name the thing. Never delete one
just to clear a finding.

### Phase 5: the judgment queue (73 non-PASS nodes)

1. Bucket every non-PASS claim: **confirmed** (rendered at its seed with
   `judgment_packets._render_sample`), **disputed** (one fresh reviewer settles it, ruling 21), or **staled** (re-review
   after the batch that touches it).
2. Feed confirmed defects into Phase 4 batches, or a dedicated P4-8 "hint and wording" batch. Known
   confirmed items:
   - negative or incomplete regrouping hints on `mat_g2_na_q2_7` and `mat_g3_na_q2_4`;
   - `3622 cat toy` at `mat_g3_na_q2_3` seed 500;
   - no number line on `mat_g2_na_q2_3`;
   - reversed factor roles on `mat_g3_na_q3_4`;
   - triangle composition on `mat_g1_mg_q1_2`;
   - seed 601's result visual on `mat_g2_mg_q1_1`.
3. **Harness gap first (Mandate 3):** `3622 cat toy` is exactly the "singular-after-many" case that
   `count_noun_agreement_1J` names as known limitation 1 and leaves unjudged (7,129 constructions on
   10-06). A reviewer caught what the gate cannot.
   - Close the limitation, or narrow it with a mutation that plants a singular-after-many and is caught.
   - Do this **before** fixing the content instance, while the instance still proves the gate.
   - This also protects G4–10, where counts grow.

### Exit

- `run_all` exits 0.
- The full corpus reads 201/201+ DETECTED with **no INVALID**.
- `docs/pgen_judgment.md` evidence is filed.
- The tree is CERTIFIED.

---

## 5. Rules you may not break

- **Verification is execution.** Quote every command with its verbatim output; write "not measured"
  otherwise. Re-count every number you publish.
- **Never weaken a check.** Floors and pins move only for a documented ground-truth error, by the
  measured delta, after a full diff (Phase D's `ac614688` is the model).
- **Invocation:** `PYTHONPATH=. .venv/bin/python …`. Write to a log and capture `EXIT $?`. Never pipe
  through `tail`.
- **Before any heavy run:** the `ps` grep must be empty and `df -h /System/Volumes/Data` must show
  enough space. Run the mutation harness **alone**. Afterwards, the escaped-plant `git grep` must be
  empty.
- **Stage by name. Never `git add -A`.** Commit end lines name **your** model truthfully. Release the lock
  in a follow-up commit. Never `--amend` a commit you will cite (F5).
- **Reviewer integrity** (`CLAUDE_AGENT_PROMPT.md` §5):
  - you never edit a verdict;
  - when a reply's `overall` contradicts its own verdicts, harvest its claims, set it aside, and
    dispatch a fresh reviewer;
  - prove wording-only repairs by a structural diff against v1;
  - take tool use from the harness record, never from the reviewer's self-report;
  - give every node its own dispatch id.
- **Do not fix content mid-campaign.** A source change stales reviews; queue the fix for a batch.
- **Not yours:**
  - the ✝️/`bible` theme;
  - `requires` / `requires_ignore`;
  - opening H-11;
  - supersession and CSI-R1–R3;
  - H-09 release promotion;
  - renaming identities;
  - discarding filed records or the `batch117`–`batch150` corpus;
  - `.claude/worktrees/agent-aaac714fac3fe0cc6`.

  Name what you find in these areas; do not fix it.
- **Stop at every owner gate**, and at any content judgment that MATATAG and the recorded rulings do not
  settle.

---

## 6. The re-proof chain (once per batch; about 5 h; each step alone, detached with one log per step)

```sh
PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q -p no:cacheprovider   # before committing source
# commit source by name; run the CLAUDE_AGENT_PROMPT.md §8 anchor one-liner; then:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin chain --force --session "<id>" --note "..."
PYTHONPATH=. .venv/bin/python -m scripts.regen_formatter_exclusions
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py > corpus.log 2>&1; echo "EXIT $?"
for i in 0 1 2 3 4 5; do PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier release --shard-count 6 --shard-index $i; done
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier verify-release
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all > run_all.log 2>&1; echo "EXIT $?"
```

- Any edit made mid-chain stales the whole chain: stop, commit, and restart from the benchmark.
- Expect exactly 3 INVALID until `capability_phase2` reaches 0. Any other INVALID means a red baseline;
  run that mutation's own command and find out why.
- Use 6 shards, because `validate_obligations` hard-codes 6.
- When the chain completes:
  1. commit the artifacts by name;
  2. run `tree_state.py --complete`;
  3. confirm CERTIFIED;
  4. release the lock in a follow-up commit.

---

## 7. Bookkeeping before you stop (including an interrupted stop)

- Write an evidence entry with:
  - commands and verbatim output;
  - seeds and dispatch ids;
  - **the model and reasoning level that judged**;
  - set-asides and their harvested claims;
  - flip rates;
  - named limits.
- Append to H-06 `progress` surgically (`numstat 1 1`).
- **Rewrite §1 and §4's status in this file.** Do not add a banner, and do not create another prompt
  file.
- Commit by name, close your intent, confirm the tree state, and release the lock in a follow-up commit.
- If you are interrupted, leave an accurate open intent and a **committed** checkpoint. No uncommitted
  records may outlive the session (F5).

**A good session** lands and proves Phase 2's instrument work, and either completes Phase 3 or lands
one Phase 4 batch whose artifacts a fresh attestation confirms under ruling 20. It quotes
every number from a command run in that session.
