# Task prompt: Phase 2 pipeline hardening under owner rulings 23–36 (Claude host)

**Rewritten 2026-10-08 after owner rulings 23–26 redefined Phase 2; rulings 27–29 (2026-10-09) settled its open design questions.
Updated 2026-10-10 after batch H5 landed (H3's infrastructure and prototype before it): the H3 rollout is next. This REPLACES every earlier version
of this file.** `CLAUDE_AGENT_PROMPT.md`, `GPT_HANDOFF_PROMPT.md` and `HANDOFF_PROMPT.md` beside it are history.
Their §5–§10 method notes (dispatch template, audit-before-filing, heavy runs, traps) remain correct and are
cited below. Their state sections, queue sizes and goals are stale; ignore them.

Trust order: a command you executed > this file > `CLAUDE_AGENT_PROMPT.md` > the dated blocks in
`docs/phase2_hardening_completion_plan.md`.

**Goal (ruling 23).** Phase 2 hardens the **testing pipeline**. It does **not** fix the problem generators.
Phase 2 is done when the pipeline catches every error Phase 1 misses, so that when the whole pipeline runs,
generator agents can find and fix every generator error from its output alone. Concretely:
- every check is proven by a mutation that lands on the path it executes (Scaling Mandate 1–2);
- `run_all` exits 0 (integrity green, no content findings), 2 (integrity green, content findings, each named by
  lc, seed and what to build) or 1 (integrity failure) (ruling 27);
- the tree is CERTIFIED.

Content findings (the 78 CONTRADICTED, 752 judgment, §2L's 420 variant + 61 packet-refusal findings, and §14's 14
domain escapes, §1J's 423 singular-after-many, §15's 22 composition findings) are the **generators' work queue**. §14's 800 `slot_text_unaccounted_14` findings are content by
ruling 34 too, but clearing them is the H3 rollout (instrumentation), which IS Phase 2 work.
They are not a Phase 2 blocker, and you do not fix them.

**Terminology.** The harness calls `mat_g3_dp_q3_4` a "node". `CLAUDE.md` calls it an **lc**, and a node is
the bundle `mat_g3_dp_q3`. Each lc is judged independently of the other lcs in its node. A **clause** is a fragment
of one lc's written competency text (`validate_capability.py` §6A/§6B). This file says "lc"; code and older
documents say "node". Do not rename code identifiers. That is a large change nobody has ruled on.

This takes several sessions. Each session works one batch (§4), leaves the tree CERTIFIED or honestly
INTERRUPTED, and re-measures every number it publishes.

---

## 0. Read first

1. `CLAUDE.md` (a symlink to `AGENTS.md`): the Scaling Mandate, the Engineering Protocols, the Content Rules,
   the **Definition of Done** (already rewritten to ruling 27's three exit codes, ahead of H2's code) and
   "If you are a judge" (ruling 29). Also read `MEMORY.md`, especially "Declared variant may
   be a no-op", "Duplicated rule copies disagree", "Allowlist checks drift silently", "Mutation must land where
   behaviour changes" and "Proof admissible, not just detected".
2. This file, completely.
3. **Owner rulings 23–36** in `docs/phase2_hardening_completion_plan.md`, verbatim (search "rulings recorded
   2026-10-08"; 27–36 follow them). Also read rulings 1, 9, 12–16 and 19–22 above them. They still govern what content must
   satisfy.
4. `validation_reports/HARDENING_EVIDENCE.md`, newest entries first (newest is at the END of the file):
   - "H2: run_all exits 0 / 2 / 1 (owner ruling 27), and the three §6F INVALIDs re-anchored";
   - "H1: §2L declared variants must reach the render (ruling 26), and a verdict hole in run_all";
   - "Declared variants that are never exhibited (§2I blind spot), and owner rulings 23–26";
   - "Phase 3: re-attestation of the queue under the ruled instrument";
   - "Phase 2a landed: the ruling-22 attester gate".
5. `docs/pgen_contract.md` rows for:
   - §2I (line ~28);
   - §1J `count_noun_agreement_1J` (its BLIND SPOTS);
   - the judgment packet allocation (the "126 no-op" MEASURED-NOT-GATED note);
   - `clause_enumeration_22` (its 7 NAMED LIMITS);
   - `stage_ledger_complete`, and `stage_failure_reaches_verdict` beside it;
   - §2L (`variant_exhibit_2L`; its 7 NAMED LIMITS);
   - the verdict row (`finding_class_registry_complete` ... `verdict_content_exits_2`; its 7 NAMED LIMITS), and the
     rule written above `_manifest.FINDING_CLASS`.
6. `CLAUDE_AGENT_PROMPT.md` §7 (heavy runs, the lock), §8 (anchor one-liner), §9 (traps) and §11 (not yours).

---

## 1. State at handoff (2026-10-10, after H5; re-measure before quoting)

```
HEAD                local main at the commit that updated this file (after the H-06 release); worktree
                    clean. Not pushed when written: check `git status -sb` before assuming origin has it
source              4c32cec1 (H5); chain artifacts 7d01a4a2, tree_state 403930d9
H-06 lock           RELEASED; claim it (owner line only, numstat 1 1) before any work
tree_state          CERTIFIED (225 proofs, 6 shards, benchmark, frontend fresh; digest 8f3acdfb0fb94441)
run_all             2026-10-10 on 4c32cec1: EXIT 2, scheduled=21 completed=15 failed=6 crashed=0
                      INTEGRITY GREEN; finding_class_registry_complete 181 labels
                      CONTENT: variant_not_exhibited_2L 420, attester_packet_refused_2L 61,
                               judgment_reviews 752, capability_contract 78 (all CONTRADICTED),
                               slot_text_unaccounted_14 794, slot_domain_escape_14 20,
                               count_noun_singular_after_many_1J 423,
                               selector_value_unexhibited_15 16, hint_sequence_unshown_15 6
                      §16 hint contract over the live tree: 0 findings
queue snippet (§4)  78 42 33 55  (measured 2026-10-09)
§2L                 973 pairs: 428 recorded, 125 by render only, 420 not exhibited; 151 packets, 61 refusals
§14                 814 = 794 unaccounted (rollout queue) + 20 escapes (fmt_emoji_pictorial's "items"
                    fallback); H5 fixed a self-accounting hole that had hidden 46 families
§15                 1,351 selector matches over 3,020 renders: 96 decided by record, 1,255 undecided
unit suite          973 passed, 1 skipped (fast suite ~11 min; the 151-test hint sweep is now §16)
mutations           225; corpus 225/225, NO INVALID
assertions          170/181 proven by execution, 11 on the shrinking allowlist
render snapshot     tests/render_snapshot.py: 7,285 renders; H5's baseline local_only/scratch/h5/after1.jsonl
latest attestation  batch440 (next free prefix: batch441)
```

**Before you resume anything detached, run `ps -eo pid,lstart,command | grep claude`.** In H2 the chain ran
under `nohup` (as §6 advises), the session that started it stayed alive after the conversation was resumed
elsewhere, and two copies of the same agent did the end-of-chain bookkeeping 2 s apart. It did no harm only by
luck. One copy per conversation; ask the owner to close the others before editing.

**What H2, H3 and H5 left for later batches** (each written as a named limit in its contract row):
- **lc and seed naming is not enforced.** The Definition of Done says a finding the pipeline cannot name by lc
  and seed blocks harness work. Measured 2026-10-10: §5's 751 findings name an lc but 0 name a seed; §6F 49 of
  78 name a seed; §2L's 20 needs_instrumentation refusals are lc-wide (no seed); the 5 floor-hidden §6 findings
  name no seed. §5 and §6F retire in H6; what "seed" means for an lc-wide finding is not ruled (**stop and ask**).
  This is Phase 2's Exit item, not done. (§14's findings all name lc and seed.)
- **Floors still hide content** (ruling 31): the §6 Phase 1 floor holds the 5 `draw` gaps (mat_g2_mg_q1_2,
  mat_g3_mg_q1_4, mat_g3_mg_q1_5, mat_g3_mg_q4_0, mat_g3_mg_q4_1), `formatters_reachable` 6,
  `obligation_routes_reachable` 5. A later batch makes them report as content.
- **Unit-test failures are all integrity** (ruling 30), including 157 live-output sweeps. H5 moves the hint sweep
  (`test_no_served_hint_contradicts_its_item`, 151 lcs) into a content stage.
- **The H3 rollout** (see §4 H3): ~800 (lc, field) families are not instrumented, so ruling 24's premise holds
  only on the three prototype lcs.
- **No cross-process determinism check** (found in H3): `comparing_ordering` iterates a set when it builds
  `distractors`, so 89 of 7,285 renders on mat_g1_na_q1_4, mat_g1_na_q2_0, mat_g2_na_q1_4 and mat_g3_na_q1_6 change
  with `PYTHONHASHSEED`. Every check runs in one process with one hash seed, so none sees it. The defect is
  generator work; the missing check is harness work that no batch owns yet (H5 did not take it).
- **Unowned harness gaps found in H5** (each in the H5 evidence): no check reads code-shaped text in hints
  (`['peso10', 'peso5', ...]`, `[9, 1, 8]`); `roles` misses "20 items at ₱50 each" hinted as "50 groups of
  20"; a doubled word ("order word word") passes everything. Stop and ask before building any of them.
- **§15's record decides 96 of 1,351 selector matches.** The H3 rollout makes the rest decidable; when you
  instrument a site, give every slot derived from a structured value its `src=` (provenance), or §15 will
  report the selector value as unexhibited.

Corrections to the previous version of this file, measured 2026-10-10:
- The H3 brief said "prototype on 3 lcs ... then roll out" as if the rollout fit one batch. It does not: about
  1,250 learner-text sites author the text (51 spine templates, ~729 DNA f-strings, ~458 formatter sites), and
  formatters rebuild 43% of stems (1,311 of 3,020 student-path items), so formatter text needs slots as much as
  DNA text. Spines produce only 9% of items (270 of 3,020).
- §1J classed `format_data.context` as learner text. It is a tag (six values, read by nothing in
  `frontend/src`); corrected in `eb3ce6cc`, texts linted 73,875 -> 68,659.

---

## 2. Why the plan changed

- **Per-sample LLM judging could not converge.** The definition of done forced `capability_phase2` and
  `judgment_reviews_5` to 0, which required fixing content. Every content fix staled reviews and owed a 5-hour
  chain, and the judges are noisy: 22.4% of verdicts flipped in W2, and 20.0% of moved verdicts disagreed in
  Phase 3. So Phase 2 had turned into generator repair.
- **Stems are the better unit for LLM review (ruling 24).** Wording, vocabulary gating, scope and pedagogy live
  in the stem template and in the domain of each field that fills it. Judging the template once covers every
  seed, goes stale only when the template or a domain changes, and is far cheaper. What a stem cannot show is
  deterministic work:
  - formatter rewraps;
  - hint/stem agreement;
  - count-noun agreement;
  - visuals;
  - value-dependent defects;
  - whether a declared variant reaches the render.
- **A content-guarding check was found unproven (Mandate 3).** §2I proves a declared variant renders without
  raising. It does not prove the render shows it. 545 of 973 pairs never do: 277 are true no-ops, 116 are
  substituted, 113 change the render without recording it, 38 cannot be decided and 1 is clamped. Clause
  coverage judged from declarations is unsound until this is closed (ruling 26).

---

## 3. Rulings in force

Rulings 23–36 are recorded verbatim in the plan doc. In short:
- 23: Phase 2 hardens the pipeline, not the generators.
- 24: LLM judges review stems plus field domains; deterministic checks do the rest.
- 25: the per-sample gates are retired once replaced; records are kept.
- 26: clause coverage is ruled from stems, then proven by an exhibit check.
- 27: `run_all` exits 0 / 2 / 1.
- 28: structured slots.
- 29: judges see `CLAUDE.md` by design.
- 30: a failing unit test is integrity (exit 1), for now.
- 31: H2 changes no floor; floor-hidden findings are a named limit.
- 32: defects in the filed §5/§6F-§6H records are content.
- 33: structured slots cover everything the learner reads: stem, options, statements, worked solutions, cloze
  text and hints.
- 34: an un-instrumented site is a CONTENT finding (exit 2) that shrinks as the rollout proceeds; the check is
  proven by mutations on lcs that are already instrumented.
- 35: a selector's value survives when a non-hint learner-read fill derives from it (slot provenance); a
  labelled text stopgap covers lcs the record cannot decide yet.
- 36: new H5 hint checks are content stages only; serving keeps enforcing the existing hint dimensions.

Rulings 19–22 stay in force for any attestation still filed under the old gates before H6 retires them. **Stop and ask** for:
- any content judgment that MATATAG and rulings 1–36 do not settle;
- any design question these rulings do not answer;
- anything in "Not yours" (§5).

---

## 4. Plan: pipeline batches H1–H6

**What is left to finish Phase 2** (one batch per session, in this order; each ends with the §6 chain):

| batch | status | what it delivers | blocked by |
|---|---|---|---|
| H1 | DONE 2026-10-09 | §2L variant exhibit check; verdict reads failed stages from the ledger | — |
| H2 | DONE 2026-10-10 | `run_all` exits 0 / 2 / 1; every finding classified integrity or content; the 3 §6F INVALIDs re-anchored and DETECTED; §2L leaves report-only | — |
| **H3** | **IN PROGRESS, next** (infrastructure, §14 check and prototype landed 2026-10-10; counting lcs added in H5; rollout owed) | structured slots (ruling 28) and the field-domain check | — |
| H4 | open | stem review gate: stem-family packets, blind judges, template+domain freshness | H3 per lc: an lc's stems may be approved only once its `slot_text_unaccounted_14` count is 0 |
| H5 | DONE 2026-10-10 | §1J singular-after-many; §15 selector survival (record) + hint-run stopgap; §16 hint contract as a content stage (ruling 30); §14 self-accounting fix | — |
| H6 | open | retire `judgment_reviews_5` and `capability_phase2` as gates; carry confirmed defects into the content report | H3 (rollout done), H4 |
| Exit | — | the "Exit" list below holds on one chain | all of the above |

The H3 rollout may span several sessions (each session is still one `batch` intent and one chain). H4 can start on lcs
whose rollout is done. H6 must be last.

Each batch is one `batch` intent and one re-proof chain (§6). Inside a batch, use a dev loop: focused unit
tests, the validator's own module, and `tests/mutation_harness.py --only <new mutations>`. Run the chain once,
at the end. Every new check needs five things:
- a contract row in `docs/pgen_contract.md`, whose § token is a `CONTRACT_CHECKS` key (memory: contract doc
  section signs are scanned);
- a mutation in `tests/mutation_harness.py` that is caught by name and is Phase-1 admissible;
- its NAMED LIMITS, written in the docstring, the contract row and the evidence log;
- no hard-coded lc lists, grades or thresholds tuned to today's tree (Mandate 4);
- a row in `_manifest.FINDING_CLASS` for every label it can print, classified by the rule written above that
  table. Without one, `finding_class_registry_complete` fails (exit 1).

**Content-finding checks set exit 2, not 1** (H2). A new content check may land with a red baseline: its labels
are CONTENT, so `run_all` exits 2. Its mutation must still be proven on a baseline that exits 0, so give its
CLI an lc scope (as `validate_exhibit --node-ids` and `validate_capability --node-ids` have) and plant on a
clean lc. Print each finding as `  FAIL <label> ...`, with the registered label first: the verdict reads that
token, and a data value in that position (a concept, an lc id) reads as an unclassified label (exit 1).

### Phase 0: baseline and lock (always, about 30 min)

1. **Heavy-run check** (`CLAUDE_AGENT_PROMPT.md` §7). The `ps` grep must be empty, and `tests/tree_state.py` must
   print `CERTIFIED` with a clean worktree. Otherwise stop and find out why.
2. **Claim H-06.** Edit only its `owner` line; `git diff --numstat
   validation_reports/phase2_hardening/hardening_status.json` must read `1 1`. Commit. Then open the intent:
   `PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin batch --session <yours> --note "<batch id>"`.
3. **Re-measure.** Run both commands below. Expect `78 42 33 55` from the first, and from the second
   `EXIT 1` (the module's own CLI; in `run_all` these are content, exit 2) plus the summary line `973 declared pair(s) at 8 seeds; 428 recorded, 125 exhibited by render only,
   420 not exhibited {'A': 1, 'B': 90, 'D': 291, 'E': 38}; 151 Attester packet(s) built, 61 refusal(s)`
   (deterministic; about 5.5 min). If either moved, explain why before building.

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

```sh
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.validate_exhibit > exhibit.log 2>&1; echo "EXIT $?"
grep "§2L:" exhibit.log
```

### H1: variant exhibit check (ruling 26; Mandate 3, so it comes first) -- DONE 2026-10-09

**Landed** as §2L (`validate_exhibit.py`, stage `variant_exhibit_2L`, contract row §2L, evidence entry
"H1: §2L declared variants must reach the render"). Criterion (b) is "differs from EVERY sibling", not any
(measured: "any" certifies 8 recorded substitutions). It was report-only until H2, which made its two labels content
(exit 2). Also landed: `stage_failure_reaches_verdict` (run_all's verdict reads every failed stage from the
ledger; `dangling_reference_1M` had been left out). Its named limit -- a stage that prints FAIL but returns True
was not seen -- was closed by H2. The original brief is preserved in git history (`7a9b211a`).

### H2: split `run_all` (ruling 23) -- DONE 2026-10-10

**Landed** in `36f03396`, chain `64e760d1`. `run_all` exits 1 on integrity, else 2 on content, else 0,
classifying every finding by the label that reported it through `_manifest.FINDING_CLASS` (172 rows, held equal to
the §8 inventory in both directions). The ledger reads each stage's printed `  FAIL <label>` lines whatever it
returns, which closes H1's limit on `stage_failure_reaches_verdict`; the matrix is read from
`validate_matrix.LAST_FAILURES`. §6 is tagged by emitting function and its Phase 1 floor absorbs content only.
`validate_capability --node-ids` exists; the three §6F INVALIDs are DETECTED on clean lcs. §2L is content.
Owner rulings 30–32 settled unit tests, floors and record defects. Evidence: "H2: run_all exits 0 / 2 / 1".
The original brief is preserved in git history (`ddc1e120`).

### H3: field domains and the domain check (ruling 24, deterministic half) -- IN PROGRESS

**Landed 2026-10-10** in `eb3ce6cc`, chain `bc6edb99` (evidence: "H3: structured slots (ruling 28) and the §14
field-domain check"; contract row §14):
- `backend/app/practice_gen/slots.py`: `fill(template, **slots)` returns exactly `template.format(...)` and records
  (template, slots, site) only inside `capture()`. `S(value, domain)`; runtime domains `R(lo, hi, basis)` and
  `E(members, basis)`, computed by the generator from what it draws with; `record(...)` and `TRANSFORMS` for
  text the check must replay. Read its docstring before instrumenting anything.
- `validate_slots` (§14, stage `slot_domains_14`, `--node-ids`): (a) each learner-read field (§1J's
  `validate_language._texts`, reused) equals a recorded fill; (b) each fill replays; (c) each slot has a domain
  that resolves; (d) each value lies in its domain. Domain kinds and their accept/reject pins:
  `tests/unit/test_validate_slots.py`.
- `tests/render_snapshot.py` (byte identity, 7,285 renders, `PYTHONHASHSEED=0`): 0 changed.
- Prototype: mat_g2_na_q3_8 (division / true_false), mat_g2_mg_q4_3 (geometric_lines / mcq), mat_g1_na_q3_3
  (subtraction / emoji_pictorial), plus `VocabGated.resolve` and every subtraction hint. 5 mutations on
  mat_g2_na_q3_8, all DETECTED in the corpus.

**Owed: the rollout.** Work down `slot_text_unaccounted_14` (800 (lc, field) families) to 0. The loop for each
DNA or formatter:
1. `PYTHONPATH=. .venv/bin/python -m tests.render_snapshot local_only/scratch/<batch>/before.jsonl` BEFORE editing.
2. Replace each learner-text f-string with `fill(...)`, every slot an `S(value, domain)`. Derive domains from the
   generator's own objects (`R` from its bounds, `E`/`enum:`/`bank:` from its lists, `value:<key>` for a value
   another layer drew). Never restate a list in the harness. Text a formatter wraps around a DNA stem uses domain
   `"fill"`. A post-fill transformation goes through `slots.TRANSFORMS` (add it there, once).
3. `validate_slots --node-ids <the lcs it serves>`: the field disappears from (a). Any new (c)/(d) finding is either
   a wrong domain (fix the domain) or a real escape (leave it; it is content, ruling 23), and you say which.
4. `render_snapshot --diff before after` must read `0 changed`. Anything else means the edit changed content:
   revert it.
5. If a DNA or formatter you instrumented hosts an existing mutation's anchor, re-run that mutation with
   `--only`.

Prioritize by learner volume: the student-path formatters (`mcq`, `true_false`, `cloze`, `error_detect`) and the
DNAs that rebuild stems. The 14 escapes are a real defect (fmt_emoji_pictorial's `_EMOJI_NAMES.get(emoji,
"item")`): do not "fix" the domain to admit "items". Named limits are in the §14 contract row; limit 6 (findings
name a field, not the source line) is the cost each rollout session pays in searching.

The original brief is preserved in git history (`87b23669`).

### H4: stem review gate (ruling 24, LLM half)

- **Enumerate stem families mechanically** per lc:
  - the spines in `generators/spines.py` the lc can select;
  - the DNA f-strings it can reach;
  - the formatter wrappers that add learner-facing text;
  - the hint templates.
  Pair each with its H3 slot domains and with the lc's competency text and clauses. One packet per lc.
- The **blind** LLM judge rules, per stem family:
  - can any value in the declared domains produce a wording, vocabulary-gating (Content Rule 1), cognitive-load
    (Rule 2) or scope (Rule 3) error;
  - can the lc's stems and declared variants produce every clause (ruling 26).
- Freshness keys on the hash of the templates plus domains, not on seeds. A record goes stale only when a stem
  or domain it judged changes.
- Keep the integrity rules that already apply:
  - one dispatch id per lc;
  - verdicts never edited;
  - ruling 20's confirming judge on any verdict that would clear or create a finding;
  - ruling 21 for disputed claims;
  - the identity names the model that judged;
  - delivery by opaque file (memory: attester dispatch gotchas).
- **Judges see `CLAUDE.md` by design (ruling 29).** Dispatch with the Agent tool as in Phase 3. The judge
  section of `CLAUDE.md` tells judges:
  - to judge only the packet;
  - not to read the repo, run code or use Graphify;
  - that lenient passes and false findings are both failures;
  - to output only the requested format.

  Blindness still means no provider tables, no other judges' records, and no lc-to-key mapping beside the
  packet. Each record's delivery field states that `CLAUDE.md` was loaded. Audit tool use from the harness
  transcript: a judge that read any file other than its packet is set aside.
- Mutation:
  - a stem edit with no new review must be stale and caught;
  - a packet missing a reachable stem family must be caught, so enumeration is complete in both directions;
  - a judged record whose verdict is removed must be caught.

### H5: composition checks a stem review cannot see -- DONE 2026-10-10

**Landed** in `4c32cec1`, chain `7d01a4a2` (evidence: "H5: composition checks a stem review cannot see"; contract
rows §1J, §14, §15, §16). Owner rulings 35-36 settled what "survives" means and where new hint checks live.
- §1J `count_noun_singular_after_many_1J`: judged against the generator's declared count nouns (interest bank,
  unit table), closed phrases only. 423 real findings, including the brief's mat_g3_na_q2_3 instance.
- §15 `validate_composition`: `selector_value_unexhibited_15` by slot provenance (`S(..., src=)`), decided
  only on fully instrumented renders; `hint_sequence_unshown_15` text stopgap. The brief's mat_g1_na_q2_1
  instance is caught by both.
- §16 `validate_hint_contract`: ruling 30's move of the live hint sweep out of the unit suite.
- §14: a nested fill can no longer account for itself.
The original brief is preserved in git history (`b88732ef`).

### H6: retire the per-sample gates (ruling 25)

Only after H3, H4 and H5 are each mutation-proven:
- Remove `judgment_reviews_5` and the `capability_phase2` attestation stage as gates. Keep their modules, if
  other code needs them, as clearly labelled history.
- Filed review and attestation records stay **read-only history**. Never edit or delete them.
- Carry every defect they **confirmed** into the content-findings report, citing the record. The confirmed
  defects are listed in the Phase 3 evidence entry:
  - `mat_g1_na_q2_2` `identify_value` "place value";
  - `mat_g2_na_q2_7` and `mat_g3_na_q2_4` hints;
  - `mat_g3_na_q3_4` factor roles;
  - `mat_g1_mg_q1_2` triangle composition;
  - `mat_g2_mg_q1_1` seed 601.
- Update the contract rows and `docs/pgen_judgment.md` in the same commit.

### Exit (Phase 2 DONE, per ruling 23)

- `run_all` exits 0 or 2: the integrity verdict is green (ruling 27).
- The full mutation corpus is DETECTED with **no INVALID**.
- The content-findings report runs to completion, and every finding names its lc, seed and owed build.
- The tree is CERTIFIED.
- Every new check's NAMED LIMITS are written down.

### The generator work queue (NOT Phase 2; for the agents who run the pipeline afterwards)

The old P4-0 to P4-7 content batches and the Phase 5 judgment queue are kept for reference in the Phase 3
evidence entry and the plan doc. They are generator work and are owed under Content Rule 4 once the pipeline is
hardened. This includes:
- §2L's 420 non-exhibited variant values (by class: what to build or undeclare) and its 61 packet refusals:
  20 `needs_instrumentation` lcs and 41 capabilities over 28 lcs refused by `provider_variant_stratification_6F`
  (tree-wide counts; the old "9" and "8" were only inside the CONTRADICTED queue);
- the interactive draw and manipulative formatters;
- range and scope gaps.
Do not start them in a Phase 2 session.

---

## 5. Rules you may not break

- **Verification is execution.** Quote every command with its verbatim output; otherwise write "not measured".
  Re-count every number you publish.
- **Never weaken a check.** Floors and pins move only for a documented ground-truth error, by the measured delta,
  after a full diff (Phase D's `ac614688` is the model). Retiring a gate under ruling 25 is not weakening it, but
  only once its replacement is proven.
- **Invocation:** `PYTHONPATH=. .venv/bin/python …`. Write to a log and capture `EXIT $?`. Never pipe through
  `tail`.
- **Before any heavy run:** the `ps` grep must be empty, and `df -h /System/Volumes/Data` must show enough space.
  Run the mutation harness **alone**. Afterwards, the escaped-plant `git grep` must be empty.
- **Stage by name. Never `git add -A`.**
  - Commit end lines must name **your** model truthfully.
  - Release the lock in a follow-up commit.
  - Never `--amend` a commit you will cite.
- **Do not fix generator content.** Ruling 23 makes that the generators' queue, and a source change stales
  reviews.
- **Not yours:**
  - the ✝️/`bible` theme;
  - `requires` and `requires_ignore`;
  - opening H-11;
  - supersession and CSI-R1–R3;
  - H-09 release promotion;
  - renaming identities, or renaming "node" to "lc" in code;
  - discarding filed records or the `batch117`–`batch150` corpus;
  - `.claude/worktrees/agent-aaac714fac3fe0cc6`.

  Name what you find in these areas; do not fix it.
- **Stop** at any content judgment or design question that MATATAG and rulings 1–36 do not settle.

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

**Run it detached, not as a session background task.** In H1 the session ended mid-corpus and killed the
chain with it (about an hour lost). Write the steps into a script under `local_only/scratch/<batch>/` and start
it with `nohup zsh chain.sh > chain.nohup 2>&1 &`, so it survives the session. H1's script, which wrote one log per
step and a `progress.log` of `START`/`END <step> EXIT <rc>` lines, was:

```sh
#!/bin/zsh
cd <repo root>; L=local_only/scratch/<batch>/chain; mkdir -p $L; export PYTHONPATH=.
step() { local name=$1; shift; echo "START $name $(date +%H:%M:%S)" >> $L/progress.log
  "$@" > $L/$name.log 2>&1; local rc=$?; echo "END $name EXIT $rc $(date +%H:%M:%S)" >> $L/progress.log; }
step regen .venv/bin/python -m scripts.regen_formatter_exclusions
step benchmark .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000
step frontend env DATABASE_URL= .venv/bin/python tests/frontend_suite.py
step corpus .venv/bin/python tests/mutation_harness.py
git grep -n "planted mutation" -- backend scripts frontend/src data > $L/escaped_plants.log 2>&1
echo "escaped-plant grep lines: $(wc -l < $L/escaped_plants.log)" >> $L/progress.log
for i in 0 1 2 3 4 5; do step shard$i .venv/bin/python -m tests.obligation_executor --tier release --shard-count 6 --shard-index $i; done
step verify .venv/bin/python -m tests.obligation_executor --tier verify-release
step run_all .venv/bin/python -m backend.app.practice_gen.validation.run_all
echo "CHAIN DONE $(date +%H:%M:%S)" >> $L/progress.log
```

Measured durations in H1: regen + benchmark + frontend under 1 min, corpus about 63 min (211 mutations), each
shard 24–27 min, run_all about 48 min (its unit_tests stage alone is about 24 min), so about 4.5 h in all.
The escaped-plant grep's one expected line is the comment at `validate_coverage.py:456`; anything else is a
plant that escaped.

**If a chain is interrupted:** check that no chain process is running (`pgrep -f chain.sh`, `pgrep -f mutation_harness`), that
there is no `MUTATION_IN_FLIGHT` marker, that `tests.mutation_harness.recover_orphaned_mutation()` returns False, that
`git status` shows no tracked source change and that the escaped-plant grep is at baseline. Then purge
`__pycache__` (memory: planted bytecode outlives restore) and resume at the first step whose artifact
`tree_state.py` reports stale.

- Any edit made mid-chain stales the whole chain. Stop, commit, and restart from the benchmark.
- Expect no INVALID (H2). Any INVALID means a red baseline: run that mutation's own command and find out why.
- Expect `run_all` EXIT 2 while content findings remain. EXIT 1 is an integrity failure: read the verdict block.
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
  - the model and reasoning level of any judge;
  - every new check's mutation result;
  - its NAMED LIMITS.
- Append to H-06 `progress` surgically (`numstat 1 1`).
- **Rewrite §1 and §4's status in this file.** Do not add a banner or create another prompt file.
- Commit by name, close your intent, confirm the tree state, and release the lock in a follow-up commit.
- If you are interrupted, leave an accurate open intent and a **committed** checkpoint.

**A good session** lands one H-batch completely: the check is built, its mutation is DETECTED by name, its
contract row and NAMED LIMITS are written, and the chain has run once with the tree CERTIFIED. It quotes every
number from a command run in that session and does not touch generator content. **H1 (2026-10-09) and H2 (2026-10-10) are done; H3 is next, or H5, which does not depend on H3.**
