# Task prompt: P4-0 onward of the Phase 2 hardening (Claude host)

**Rewritten 2026-10-08 for a fresh Claude session, after `claude-h06-phase2a-gate-20261007` landed and
proved Phase 2 (the ruling-22 attester gate). §1 and §4 were updated the same day, after Phase 3
(`claude-h06-phase3-reattest-20261008`). This REPLACES every earlier version of this file.**
`CLAUDE_AGENT_PROMPT.md`, `GPT_HANDOFF_PROMPT.md` and `HANDOFF_PROMPT.md` beside it are history. Their
§5–§10 method notes (the dispatch template, audit-before-filing, heavy runs, traps) remain correct and
are cited below. Their state sections and queue sizes are stale; ignore them.

Trust order: a command you executed > this file > `CLAUDE_AGENT_PROMPT.md` > the dated blocks in
`docs/phase2_hardening_completion_plan.md`.

Goal: `PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all` exits 0, with the
three §6F mutations DETECTED (207/207 at the current corpus size), not INVALID. This takes several
sessions. Each session leaves the tree CERTIFIED or honestly INTERRUPTED, with every number re-measured.

**Your job this session: P4-0 (§4)**, the first source batch: instrument the refused nodes, and fix the
provider-variant reachability defect that Phase 3 found on 8 more (§1). It has one `batch` intent and one chain.
Phase 3 is DONE (2026-10-08, `claude-h06-phase3-reattest-20261008`).

---

## 0. Read first

1. `CLAUDE.md`: Scaling Mandate, Engineering Protocols, Content Rules, Definition of Done. Your memory
   index (`MEMORY.md`) too, especially "Dispatch subagents on Haiku" and "Proof admissible, not just
   detected".
2. This file, completely.
3. `validation_reports/HARDENING_EVIDENCE.md`: the newest entries first. Start with "Phase 3:
   re-attestation of the queue under the ruled instrument"; it holds the queue, by node, that P4 works
   from, and what Phase 3 found. Then read "Phase 2a landed: the ruling-22 attester gate".
4. Owner rulings 1, 9, 12–15 and 18–22 in `docs/phase2_hardening_completion_plan.md`, verbatim.
5. `validation_reports/phase2_hardening/dispatch_instructions_20261007.md`: the Attester prompt you
   will paste, and the dispatcher rules above it. **Use it as written.**
6. The docstring of `tests/clause_enumeration.py` (what a stratum is, and the named limits) and of
   `tests/attester_file.py` (what the filer refuses).
7. `CLAUDE_AGENT_PROMPT.md` §5 (the dispatch template and the audit), §7 (heavy runs, the lock),
   §9 (traps), §11 (not yours).

---

## 1. State at handoff (2026-10-08, after Phase 3; re-measure before quoting)

```
HEAD                the H-06 lock-release commit after 4fe84cff (Phase 3 records); worktree clean
source              9c4e036e, unchanged by Phase 3 (no source, test or classification edit)
H-06 lock           RELEASED; claim it (owner line only, numstat 1 1) before any work
tree_state          CERTIFIED, digest 0acfacdb145cd162 (207 proofs, 6 shards, benchmark, frontend fresh)
run_all             last full run 2026-10-07 19:18 on 9c4e036e: EXIT 1, failed=3 (not re-run in Phase 3)
                      assertion_coverage_8  the 3 §6F mutations INVALID (their baseline is red)
                      judgment_reviews_5    752
                      capability_phase2     124 then; NOW 78 CONTRADICTED over 42 nodes
                                            (validate_capability_attestation(), executed 2026-10-08)
corpus              204/207 DETECTED; INVALID = the §6F cluster until capability_phase2 reaches 0
unit suite          1034 passed, 1 skipped (fast suite ~22 min)
ruling 22           clause_enumeration.json: 151 nodes, 94 enumerations, 240 members (182 selector,
                    56 needs_instrumentation, 2 unserved), 527 not enumerated. A proof input.
latest attestation  batch440 (next free prefix: batch441)
```

**Phase 3 result** (evidence entry "Phase 3: re-attestation of the queue under the ruled instrument"):
- 38 nodes re-attested by blind Claude Haiku 4.5 judges, with every move confirmed (ruling 20).
  124 → **78 CONTRADICTED**: 48 cleared, 2 created (`mat_g2_na_q2_3` number_line,
  `mat_g2_na_q4_0` denominators_2_3_4_5_6_8), 36 never re-attested.
- Rare: 42 cleared, 15 remain. Absent: 4 cleared (+2 by a Luna confirmation), 23 remain.
  The split is from the saved row list `local_only/scratch/p3/rare_absent_classification.json`
  (78/42/4, re-derived by hand; the old 68/52/4 list was never saved).
- First vs confirming Haiku judge on the same packet: 20.0% of moved verdicts disagreed (12/60);
  12.2% of all items (23/189).
- **Not re-attested, owed to P4-0:**
  - the 9 `needs_instrumentation` nodes (23 findings; listed below);
  - 8 nodes the packet builder REFUSES with `provider_variant_stratification_6F` (13 findings):
    `mat_g1_mg_q4_4`, `mat_g1_na_q3_0`, `mat_g2_dp_q3_0`, `mat_g2_mg_q4_1`, `mat_g2_mg_q4_2`,
    `mat_g2_mg_q4_4`, `mat_g3_mg_q1_6`, `mat_g3_mg_q2_2`. On these, `_variant_coverage_candidates`
    advertises variants the serving path never emits under that name (`context`, `spine`,
    `scale_type`, `mode`) or never serves (`identify_and_measure`, `measure_tools`, `unit_type=m`,
    `unit=l` on a mass node). Measured 0/64 seeds each (`local_only/scratch/p3/diag_variants.py`).
- The 9 refused nodes: `mat_g1_mg_q4_0`, `mat_g1_na_q4_3`, `mat_g1_na_q4_4`, `mat_g2_mg_q1_1`,
  `mat_g2_mg_q1_2`, `mat_g2_mg_q4_3`, `mat_g2_na_q2_0`, `mat_g2_na_q3_5`, `mat_g3_na_q2_0`.
- **The single-Luna confirmations owed by ruling 20 are DONE.** `batch398` and `batch405` were built from
  the Luna records (owner decision 2026-10-08). The other five Luna nodes owed nothing, or were
  re-attested.

**Every packet item prints `STANDARD (owner ruling 19|9)`.** This is a new instrument variable, so any
comparison with W2's figures must say so.

---

## 2. What the review of the last two sessions found (why this plan differs)

Each finding came from an executed command: `validate_capability --phase 2`, `validate_judgment --all`,
and a per-node dump of `validation_reports/attestation/batch*_<node>.json`. Re-derive them before you
rely on them. They were recorded in the "Phase 2 instrument baseline" evidence entry (`54260249`).

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

## 3. OWNER RULINGS 19–22 (given 2026-10-07; recorded in `docs/phase2_hardening_completion_plan.md`)

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

**Ruling 22 (given 2026-10-07): packet-only attester selectors are approved, on two conditions.**
- (a) A selector observes **structured generator values only**, never a substring of learner-facing
  question or answer text.
- (b) **Every required clause is classified**, either as a stratum (a reachable exact variant or a
  selector) or as explicitly not enumerated, with the competency wording cited. A clause with neither
  classification **fails loudly by name**.
- The ruling's text says `CAPABILITY_PROVIDERS` "may" carry selectors. Key them **per (node, member)**
  instead, because a capability-wide selector is wrong for the 140 of 472 ids shared across DNAs. The
  landed gate does this (`tests/clause_enumeration.py`), and the contract row records why.

**Still a stop-and-ask:** any new content judgment that MATATAG and rulings 1–22 do not settle, any
production verb Phase 4 cannot map to rulings 3, 13 or 16, and anything in "Not yours" (§5).

---

## 4. Plan

### Phase 0: baseline and lock (always, about 30 min)

1. **Heavy-run check** (`CLAUDE_AGENT_PROMPT.md` §7). The `ps` grep must be empty, and
   `tests/tree_state.py` must print `CERTIFIED` with a clean worktree. If it prints anything else, stop
   and find out why.
2. **Claim H-06.** Edit only its `owner` line, check that
   `git diff --numstat validation_reports/phase2_hardening/hardening_status.json` reads `1 1`, and
   commit. Then open the intent:
   `PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin campaign --session <yours> --note "Phase 3 re-attestation"`.
3. **Run the gate:** `PYTHONPATH=. .venv/bin/python -m tests.clause_enumeration --check`, and expect
   `clause_enumeration_22: OK`. If it fails, a node's requires or competency changed. Re-read the
   competency, correct `TABLE`, and regenerate with `--write`, never by hand. That is a source change,
   so it needs its own chain: stop and report.
4. **Re-measure the queue.** Use the snippet below; expect 124 / 55 / 46 / 99. If the counts moved,
   explain why before dispatching.

```sh
PYTHONPATH=. .venv/bin/python - <<'PY'
import re, collections
from backend.app.practice_gen.validation import validate_capability as VC
from tests import clause_enumeration as CE
doc = CE.load(); by = collections.defaultdict(list)
for e in VC.validate_capability_attestation():
    m = re.search(r"(mat_\w+): capability '([^']+)' \(clause '[^']*'\) is CONTRADICTED", e)
    if m: by[m.group(1)].append(m.group(2))
blocked = {n for n in by if any("needs_instrumentation" in d for d in CE.node_dispositions(n, doc).values())}
print(sum(map(len, by.values())), len(by), len(by) - len(blocked), sum(len(by[n]) for n in by if n not in blocked))
PY
```

### Phases 1 and 2: DONE

Phase 1 (owner gates) was resolved by rulings 19–22. Phase 2 (instrument) landed in `c4fcb384` and
`9c4e036e`: the chain completed and the tree is CERTIFIED. What it built and its named limits are in the
evidence entry and in the `docs/pgen_contract.md` row for `clause_enumeration_22`. **Do not modify it
during Phase 3.** Any edit to `tests/` or `backend/` stales the certified tree and owes a 5-hour chain.

### Phase 3: DONE (2026-10-08, `claude-h06-phase3-reattest-20261008`)

The result is in §1 and the evidence entry. Records `batch370`–`batch440`. Use the same method every time a
batch stales a node and it must be re-attested (Phase 4 and later). The scripts are under
`local_only/scratch/p3/` (gitignored, so copy them before relying on them):
- `audit.py`, `pipe.py` (`first`/`confirm`), `fileit.py`;
- `compare.py`, which feeds the disagreement rate;
- `measure.py`.

1. **Build** one packet per node with `tests.attester_packets --node`. A `provider_variant_stratification_6F`
   refusal is a finding about the provider table or the DNA, not something to retry.
2. **Deliver by file** (owner-approved 2026-10-08):
   - write section A of `dispatch_instructions_20261007.md`, extracted mechanically, followed by the
     verbatim `render_prompt_block` output, to an opaquely named scratchpad file (`p3/dNN/prompt.txt`);
   - keep no node id and no key file beside it;
   - the Agent-tool prompt only names the file to Read and the `verdicts.json` to Write;
   - record exactly that in `--samples-delivery`.
3. **Identity:** `blind-attester-claude-haiku-4.5-default-<role>-<node>-<YYYYMMDD>`, one per node and role.
4. **Audit before filing:**
   - one verdict per item;
   - every cited seed printed;
   - PROVIDED cites a seed;
   - reasoning of 60+ characters;
   - every quoted span found in the prompt the Attester received.

   Tolerate only trailing punctuation, case and whitespace. Elisions and placeholders are failures. Take tool
   use from the harness transcript and refuse any path outside the dispatch's own two files.
5. **Revise wording only** by asking the same Attester to change its own wording, and prove the revision by a
   structural diff (item, verdict and seeds) against v1. A fabricated seed means set the reply aside: harvest
   its claims and send the identical prompt to a fresh Attester.
6. **Compute moves before filing** against the current winner (`_load_attestations` +
   `CAPABILITY_PROVIDERS`). For every clear or create:
   - dispatch one confirming judge on a byte-identical copy of the prompt;
   - file it afterwards with the moved items only;
   - pass `--supersedes`, which takes a **JSON file path**, not inline JSON.
7. **Commit records by name** as you go. Afterwards run `tests/tree_state.py` and the two tests that
   filing is known to rot (§9 trap 1).

**Owed from Phase 3** (none of it is fixed; each item is named in the evidence entry):
- The 8 provider-variant refusals → P4-0. Also add a harness check that builds every node's attester
  packet, so a refusal surfaces before dispatch. Mandate 5: add it while its finding count can be driven
  to zero.
- **Ruling-22 blind spot.** A selector proves the generator CHOSE the sibling, not that the rendered item
  still EXHIBITS it.
  - Example: `mat_g1_na_q2_1` `read_mcq` NumberLine/EmojiPictorial items drop the skip-count sequence
    while their hints describe it.
  - Owed: a check with its mutation, then the formatter fix.
- `mat_g1_na_q2_2`'s `identify_value` stem reads "place value". → P4-8 wording.
- Blindness: Agent-tool subagents inherit `CLAUDE.md`. Either remove that or record it in
  `samples_delivery`.

### Phase 4: content batches by shared artifact (each is one `batch` intent, one chain)

Every change quotes the MATATAG clause it builds toward (Content Rule 4) in the commit and the evidence
log. Within a batch, iterate in a **dev loop**: focused unit tests, the node's validators, and
`mutation_harness.py --only` for new mutations. Run the **chain once** at the end of the batch. Then
re-review and re-attest, under rulings 20 and 21, every node the batch staled.

**P4-0 comes first after Phase 3: instrument the DNAs of the refused nodes.** The 56
`needs_instrumentation` members sit on 20 nodes, 9 of them in the queue. Each DNA must emit a
STRUCTURED field naming its sibling:
- rotation turn size and direction;
- coin vs bill;
- with/without regrouping;
- composite-figure parts;
- lines vs surfaces;
- money notation;
- numbers vs letters;
- sharing vs grouping;
- fraction equal to / greater than one;
- the rest are listed in `TABLE`.

Then switch each member from `NI(...)` to a selector in `TABLE`, `--write`, prove each new selector with
`--check-renders`, and run one chain. Then re-attest those nodes as in Phase 3. A field must describe
what the generator chose; it must never be derived from learner-facing text (ruling 22a).

**P4-0 also owns the 8 provider-variant refusals Phase 3 found** (§1).

- **How to approach each variant.** Each advertised variant either:
  - is emitted by the DNA under the name the provider table uses, or
  - stops being advertised by `_variant_coverage_candidates`.
- **Before dropping any, show from the competency that the node does not need it.** Example: `unit=l` on
  "compare masses".
- **Put the check in the harness in the same batch.** Build every node's attester packet, so this
  surfaces before dispatch.

Phase 3 also re-derived the batch membership below; the current queue is in §1, and the per-node list is
in the evidence entry.

Proposed content batches, from the absent group. Re-derive membership from the Phase 3 result before
starting:

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

1. Bucket every non-PASS claim:
   - **confirmed**: rendered at its seed with `judgment_packets._render_sample`;
   - **disputed**: one fresh reviewer settles it (ruling 21);
   - **staled**: re-review after the batch that touches it.
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
   2026-10-07). A reviewer caught what the gate cannot.
   - Close the limitation, or narrow it with a mutation that plants a singular-after-many and is caught.
   - Do this **before** fixing the content instance, while the instance still proves the gate.

### Exit

- `run_all` exits 0.
- The full corpus reads 207/207 or more DETECTED with **no INVALID**.
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

**A good session** completes Phase 3 for the 46 nodes with every move confirmed under ruling 20,
records the measured queue and the disagreement rate, and leaves the tree CERTIFIED with H-06 released.
It quotes every number from a command run in that session. If it runs out of time, it commits every filed
record, leaves an accurate open `campaign` intent, and says exactly which nodes are done.
