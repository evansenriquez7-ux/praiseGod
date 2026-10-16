# Task prompt: Phase 2 pipeline hardening under owner rulings 23–51 (Claude host)

**Rewritten 2026-10-13 after batch H4; §0, §2 and §5's status rewritten 2026-10-16 after batch H4-C (the §17 judge
campaign is complete: every lc has a filed first judge and a blind confirmer). This REPLACES every earlier version of
this file.**
`CLAUDE_AGENT_PROMPT.md`, `GPT_HANDOFF_PROMPT.md` and `HANDOFF_PROMPT.md` beside it are history: their method notes
(§7 heavy runs and the lock, §8 anchor one-liner, §9 traps, §11 not yours) are still correct and cited below; their
state sections are stale.

Trust order: a command you executed > this file > `CLAUDE_AGENT_PROMPT.md` > the dated blocks in
`docs/phase2_hardening_completion_plan.md`.

---

## 0. Your task, in one paragraph

Batch **H4-C is done** (2026-10-16). Every one of the 151 lcs has a filed first Haiku judge and a filed blind
confirming judge under `validation_reports/stem_review/` (355 records, `967f5d2c`). Each standing FAIL was checked
against real renders (rulings 49 and 51). `validate_stem_review` now reports `stem_review_missing_17` 0 and every
integrity label PASS; `stem_review_fail_17 (141)` and `stem_clause_unproducible_17 (15)` are content findings for
the generator queue (ruling 23).

**Next: there is no approved batch.** At Phase 0, ask the owner which of these to run:
- **H6** (§6.2): retire the per-sample gates. Ruling 25's precondition (the stem gate proven, its campaign done) now
  holds, but the owner has not said to start.
- An unowned exit item (§6.3).
- Stopping Phase 2 for generator work (§6.4).

Do not fix generator content, and do not edit a filed record. Read the "H4-C" evidence entry (at the END of
`validation_reports/HARDENING_EVIDENCE.md`) before anything else.

**Goal of Phase 2 (ruling 23).** It hardens the **testing pipeline**, not the generators. It is done when every
check is proven by a mutation on the path it executes (Scaling Mandate 1–2), `run_all` exits 0 or 2 (integrity
green; ruling 27), every finding is named by lc, seed and owed build, and the tree is CERTIFIED. Content findings
are the generators' work queue (§6.4).

**Terminology.** The harness calls `mat_g3_dp_q3_4` a "node"; `CLAUDE.md` calls it an **lc**. A node is the bundle
`mat_g3_dp_q3`. A **clause** is a fragment of one lc's competency text. A **stem family** is (spine id or call-site
module, template, renderer) as `stem_packets.family_key` defines it (ruling 44a). Do not rename code identifiers.

---

## 1. Read first (in this order; budget about 40 minutes)

1. `CLAUDE.md` (a symlink to `AGENTS.md`): the Scaling Mandate, Engineering Protocols, Content Rules, Definition of
   Done and **"If you are a judge"** (your judges will read it; ruling 29). Then `MEMORY.md`, especially:
   "Attester dispatch gotchas", "Dispatch subagents on Haiku", "Judgment reviews go stale", "Reviewer evidence must
   be lossless", "Duplicated rule copies disagree", "Allowlist checks drift silently", "Mutation must land where
   behaviour changes", "Proof admissible, not just detected", "CERTIFIED can hide a red unit test", "New run_all
   stage needs a stub".
2. This file, completely.
3. **Owner rulings** in `docs/phase2_hardening_completion_plan.md`, verbatim: 19–22 (search "rulings recorded
   2026-10-07") and 23–45 (search "rulings recorded 2026-10-08"; 27–45 follow). Rulings 20, 21, 24, 26, 29, 44 and
   45 are the campaign's core.
4. `validation_reports/HARDENING_EVIDENCE.md`, newest at the END: "H4" fully; then "H4-0-R2", "H4-0", "H3-R2"
   (headings and NAMED LIMITS).
5. `docs/pgen_contract.md` rows §17 (the stem review gate, NAMED LIMITS 1–12), §14 (its H4 amendment), §5
   (`validate_judgment`), §2L, the verdict row, and the rule above `_manifest.FINDING_CLASS`.
6. Code: `validation/stem_packets.py`, `validation/validate_stem_review.py` and `tests/stem_file.py` (whole
   files: the packet, the gate and the filer the campaign uses); then, as background, `backend/app/practice_gen/slots.py`;
   `validation/validate_slots.py` (`render_findings`, `collect_findings`); `validation/judgment_packets.py`;
   `validation/validate_judgment.py` (its docstring: why freshness, quote provenance, plurality and skeleton checks
   exist); `tests/file_reviews.py`, `tests/attester_packets.py`, `tests/attester_file.py` (docstrings);
   `validation/run_all.py` around the stage table (~line 670), the stage functions (~line 1105) and the stage list
   (~line 1204); `validation/_manifest.py` (`FINDING_CLASS`); one `Mutation(...)` in `tests/mutation_harness.py`
   (e.g. `slot_loosened_to_type_only`, ~line 5189).
7. `CLAUDE_AGENT_PROMPT.md` §7, §8, §9, §11.

---

## 2. State at handoff (2026-10-16, after H4-C; re-measure before quoting)

```
HEAD                local main, NOT pushed (git status -sb: ahead of origin)
source              6ebbd1b3 (ruling 50b, packet HASH_VERSION 8) after 6b2c59ed/8f83125a/613315ee/fb146422/0388fecf/
                    09ca8af0/39c2752b (rulings 46-50); chain 563f7c59; tree_state 9067acd4; records 967f5d2c;
                    evidence/handoff in the bookkeeping commit after it
H-06 lock           RELEASED (follow-up commit); claim it before any work (§4 Phase 0)
tree_state          CERTIFIED (262 proofs, 7 shards, benchmark, frontend fresh; digest 28d1e3f4ef451da6)
run_all             on 6ebbd1b3 (before the records): EXIT 2; scheduled=22 completed=15 failed=7 crashed=0; INTEGRITY
                    GREEN; 184/195 assertions proven by execution; finding_class_registry_complete 195 labels
  CONTENT           variant_not_exhibited_2L 420, attester_packet_refused_2L 61, judgment_reviews 752,
                    capability_contract 78, count_noun_singular_after_many_1J 423, slot_domain_escape_14 74,
                    slot_text_unaccounted_14 4, slot_path_refused_14 1, selector_value_unexhibited_15 58,
                    hint_sequence_unshown_15 6, stem_review_missing_17 151 (now 0; see §17 below)
§17                 validate_stem_review over the filed records: stem_review_missing_17 0, every integrity label PASS;
                    stem_review_fail_17 141, stem_clause_unproducible_17 15; 10 of 151 lcs carry a confirmed PASS with
                    every clause PRODUCIBLE; 2,684 stem families packeted
records             355 in validation_reports/stem_review/ (151 first, 204 confirming incl. 53 ruling-21 records);
                    451 Haiku replies audited, 96 set aside unfiled; all transcripts record claude-haiku-5-5
unit suite          1010 passed, 1 skipped (in the chain's run_all); after the last commit: see the lock-release commit
mutations           262; corpus 262/262, no INVALID
latest attestation  batch447 (next free prefix: batch448)
```

The chain's run_all predates the records, so its CONTENT line still shows `stem_review_missing_17 151`. The next
run_all will report `stem_review_fail_17 (141)` and `stem_clause_unproducible_17 (15)` instead. Records are not a
digest input, so no chain is owed for them.

**Before you resume anything detached, run `ps -eo pid,lstart,command | grep claude`**: one copy of the agent per
conversation.

---

## 3. Rulings in force (verbatim in the plan doc; these are summaries)

- 19: enumerated sibling clauses are judged by design, not by share of samples.
- 20: any model family may judge; the identity names the model that judged; **one confirming judge** for any
  verdict that would create or clear a finding; the later (confirming) verdict stands; records are never edited.
- 21: a dispatcher who believes a non-PASS claim is false sends the lc to one fresh blind reviewer, whose verdict
  settles it; the disproving render and the outcome go in the evidence log.
- 22: packet-only selectors observe structured values only; every required clause is classified.
- 23: Phase 2 hardens the pipeline, not the generators.
- 24: **LLM judges review stems plus field domains**; deterministic checks prove fields stay inside them.
- 25: the per-sample gates (`judgment_reviews_5`, `capability_phase2`) are retired once the stem gate and field
  checks are each proven by mutation; records stay as history; confirmed defects go to the content queue.
- 26: clause coverage is ruled per lc from stems and declared variants, proven by the §2L exhibit check.
- 27: `run_all` exits 0 / 2 / 1.  28: structured slots.  29: judges see `CLAUDE.md`.
- 30: unit-test failures are integrity.  31: floors unchanged.  32: record defects are content.
- 33: slots cover everything the learner reads (hints included).  34: an un-instrumented site is a content finding.
- 35, 41: §15 decides selector survival by slot and value-level provenance (`derives`, `computes`, template `_src`).
- 36: H5 hint checks are content only.  37: many slices may share one chain.  38: `error_label` is metadata.
- 39: error-detect names its ErrorPattern.  40: indefinite articles by sound, gated by §1J.
- 42: **H4 approves an lc only after that lc's type-only slots are tightened** (now true for all 151).
- 43: a type-only slot's reason is a registered `slots.DERIVED_REASONS` kind plus a `src` the values carry.
- 44: **the stem gate's design**: (a) families keep only fills that reach learner text, wordless all-`fill` wrappers
  collapse; (b) §14 and §17 share `validate_slots.paths()`; (c) freshness binds resolved content; (d) ONE overall
  verdict per lc; (e) **every lc gets a first judge and a blind confirmer; the later verdict stands**; a FAIL quotes
  its failing templates; (f) verdicts and record defects are content; (g) the judge rules every clause
  PRODUCIBLE / NOT_PRODUCIBLE (gated); (h) Haiku judges, about 6 concurrent.
- 45: **the campaign is approved**, as designed, from batch441, in a fresh session.
- 46-48e: packet content (where each family is read; item banks row by row; only printable text; repeated values;
  one family per gate word).  49: a standing FAIL is settled by real renders.  50, 50b: a value slot shows what
  it printed, numbers as lossless runs (HASH_VERSION 8).
- 51: **ruling 21 only where every ground of the standing record is disproved by renders**; every disproof is
  logged; where a real printed ground exists the confirmer's FAIL stands.

**Stop and ask** for any content judgment or design question that rulings 1–51 and MATATAG do not settle, and for
anything in "Not yours" (§7).

---

## 4. Phase 0: baseline and lock (always, before any edit)

1. `ps` grep empty; `df -h /System/Volumes/Data` shows space; `PYTHONPATH=. .venv/bin/python tests/tree_state.py`
   prints CERTIFIED; worktree clean. CERTIFIED does not cover `validation_reports/`, so also run
   `PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q -p no:cacheprovider` (expect 999 passed,
   1 skipped; ~11 min; run it in the background and read while it runs).
2. Claim H-06: in `validation_reports/phase2_hardening/hardening_status.json` edit ONLY its `owner` line with
   `sed` (`git diff --numstat` must read `1 1`), commit by name, then
   `PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin batch --session <yours> --note "H4-C: ..."`.
3. Re-measure, and explain any move before building:
   - `validate_slots`: `slot_domain_escape_14 (74)`, `slot_text_unaccounted_14 (4)`, `slot_path_refused_14 (1)`,
     `slot_domain_type_only_14` PASS, NOTE `151 of 151`;
   - `validate_stem_review`: `stem_review_missing_17 (151)`, every other §17 label PASS, `2561 stem families`;
   - `validate_composition`: 58 + 6, with 1,351 of 1,351 decided;
   - `validate_language`: `indefinite_article_1J` PASS and 423 mirror findings;
   - the capability queue snippet below (`78 42 33 55` at H4-0-R2's Phase 0; ~2 min).
4. If you will touch any source: `PYTHONPATH=. .venv/bin/python -m tests.render_snapshot local_only/scratch/<batch>/before.jsonl`
   BEFORE the first edit, and keep `tests/slot_wide_check.py` (expect `TOTAL distinct 24 | renders that raised: 2`,
   the two `mat_g2_mg_q4_3` pinned-mcq refusals; it now walks §14's own paths) and the §15 dump
   (`validation_reports/phase2_hardening/h4_0_tools/comp_dump.py OUT.json`) as baselines.

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

---

## 5. H4: the stem review gate (ruling 24, LLM half)

### 5.0 Status

**Built and proven in batch H4 (2026-10-13), CERTIFIED, and run to completion in batch H4-C (2026-10-14 to
2026-10-16).**

What exists:
- `validate_slots.paths()` / `observe()`: the one path enumeration and render that §14 and §17 share.
- `validation/stem_packets.py`: builds the blind item, now HASH_VERSION 8, under rulings 46-50b:
  - the competency, clauses, vocabulary gates, and declared variants and bounds;
  - families with their slot domains, each saying where it is read (46);
  - item banks printed row by row (47);
  - only printable text (48), and whether a render repeated a value (48d);
  - each gate word as its own family (48e);
  - what a generated value printed, numbers shown as lossless runs (50, 50b).
- `validation/validate_stem_review.py` (§17, Phase 2) reads `validation_reports/stem_review/<lc>/*.json` and uses
  the latest-filed confirming record per lc.
- `tests/stem_file.py prompt|file`: the judge's instructions plus item, and the filer.
- Proofs: 14 §17 mutations against the fixture in `tests/stem_review_fixtures/`. **A generator change to
  mat_g2_na_q3_8 stales the fixture and makes every §17 proof INVALID: re-run `tests/stem_review_fixture.py` then**
  (contract §17 limit 12).

The campaign's result (evidence entry "H4-C"):
- **Records:** 151 firsts and 204 confirmers, 53 of them ruling-21 records. Standing verdicts are 141 FAIL and
  10 PASS, with 15 NOT_PRODUCIBLE clauses.
- **Render checks:** ruling 49/51 checks covered all 141 FAILs and are in `local_only/scratch/h4c/r49.log`, which is
  not committed.
- **Tools:** in `local_only/scratch/h4c/`, not committed:
  - `h4c.py` (take, audit, file);
  - `taf.sh`;
  - `mkdisp.py` (prompts of 2,000 lines or more need explicit chunked Read calls; Haiku otherwise reads only 2,000
    lines);
  - `render_dump.py`, `grounds.py`, `r49brief.py`.
- **When a record goes stale:** a generator change stales the records of the lcs it touches (freshness binds
  resolved content). Re-dispatch those lcs on fresh packets by §5.1 (new dispatch ids; never edit a record).
- **Model:** judges run on the Agent tool's `haiku` alias at `effort: medium`, which the owner asked for to conserve
  rate limits. It resolved to `claude-haiku-5-5` in every transcript. An older Haiku cannot be pinned from this
  host.

### 5.1 The campaign, step by step (H4-C)

1. Build every packet FIRST, in groups (e.g. 25 lcs per packets file; prefix `S441`, `S442`, ...; ids
   `S441-001`...): `PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.stem_packets --nodes
   <lcs> --prefix S441 --packets local_only/scratch/h4c/S441.json --key local_only/scratch/h4c/S441.key.json`.
   Every lc must build (the builder raises on a coverage gap or a slot-name mismatch: that is harness work; stop).
2. For each item write its prompt: `tests/stem_file.py prompt --packets ... --item S441-001 --out
   local_only/scratch/h4c/S441-001.prompt.txt`. Keep the key files out of every judge's reach.
3. Dispatch the FIRST judge per item with the Agent tool, `model: "haiku"` (memory "Dispatch subagents on Haiku"),
   about 6 concurrent. The agent prompt only says: read that one prompt file and reply with exactly what it asks.
   Judges inherit `CLAUDE.md` by design (ruling 29). Save each reply byte for byte to a file.
4. **Audit every reply against its prompt before filing** (memory "Attester dispatch gotchas"): it parses as one
   JSON object; every quoted span appears in the prompt; `failing_templates` and each PRODUCIBLE `template` are
   templates the packet prints EXACTLY; every clause id is answered. The filer refuses most of these itself, but
   a refused or doubtful reply is set aside (never edited) and the item re-dispatched to a fresh judge. If the agent
   read any file other than its prompt, set it aside.
5. File: `tests/stem_file.py file --packets ... --key ... --item S441-001 --reply <reply file> --role first
   --judged-by blind-stem-judge-claude-haiku-<batch>-<item>-first --dispatch-id stem-<batch>-<item>-first
   --filed-at <ISO time> --delivery "judge read only <prompt path>; dispatched with CLAUDE.md loaded (ruling 29)"
   --tool-uses "<what the agent did>" --prompt <prompt path>`. The identity must name the model that judged; the
   Agent tool exposes only `haiku`, so say that, not a version you did not see.
6. Dispatch the CONFIRMING judge per item on the SAME prompt file, a new agent that has seen nothing of the first
   reply; audit; file with `--role confirming --confirms stem-<batch>-<item>-first` and its own identity and
   dispatch id. The later verdict stands (ruling 20).
7. **Disputes (ruling 21):** if you believe a FAIL or NOT_PRODUCIBLE claim is false, do not set it aside on that
   belief: dispatch one more fresh blind judge as a confirming record on the same first record, and log the
   disproving evidence and the outcome in the evidence entry. That record is the latest and stands.
8. After each group: `PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.validate_stem_review
   --node-ids <group>`; at the end, the whole gate. Expect `stem_review_missing_17` to fall to 0 and
   `stem_review_fail_17` / `stem_clause_unproducible_17` to name real generator work by lc and template.
9. Records are FILES under `validation_reports/` (not a digest input): commit them by name per group, claim the
   directory in H-06's `proof_artifacts` in the same commit (memory "CERTIFIED can hide a red unit test"), and run
   the unit suite after the last commit. No chain is owed unless you changed source.
10. If a generator changes while you dispatch, packets filed before it go STALE by design (the filer copies the
    dispatch-time packet); re-dispatch those lcs on fresh packets.

### 5.2 Known limits a judge's verdict inherits (contract §17 NAMED LIMITS)

Paths are `validate_slots.paths()` only; runtime `E`/`R` domains show the members/bounds observed there; a
`value:<key>` slot shows its key, not its range (the item lists the declared bounds); a `fill` slot's families are
matched by text (over-inclusive); one-member domains of the value itself (e.g. `answer_text`, fmt_true_false's
"not" statement) are shown as observed and the prompt tells the judge to treat them as unbounded.

### 5.3 Open design points (ask the owner before building any)

- `stem_review_fail_17` names the templates a judge quoted, not seeds (ruling 44d); the lc-and-seed naming question
  of §6.3 applies to it too.
- After the campaign, H6 (§6.2) retires `judgment_reviews_5` and `capability_phase2` as gates; the owner rules when.

### 5.4 Integrity rules carried over from §5/§6 (non-negotiable)

One dispatch id per lc; verdicts never edited; ruling 20's confirming judge; ruling 21 for disputed claims; the
identity names the model that judged; delivery by opaque file; judges see `CLAUDE.md` (ruling 29) and the record's
delivery field says so; a judge that read any file other than its packet is set aside; the dispatcher never retypes
a verdict.

---

## 6. Other work (not this batch unless the owner says so)

### 6.1 Tightening a type-only slot a new path reaches (the H4-0-R2 method)

If H4's wider enumeration reaches one of the 61 unreasoned `derived(` lines, tighten it before that family is
reviewed (ruling 42). Tools in `validation_reports/phase2_hardening/h4_0_tools/` take paths as arguments and run in
place: `tonly.py` (the real §14 findings as JSON), `obs.py` (wide observation), `plan.py`, `tighten.py`/`propose.py`
(AST rewrites; dry-run first), `rep.py`, `reanchor.py`, `comp_dump.py`, `kinds.py`, `anchors.sh`. Also
`tests/slot_wide_check.py` and `tests/scoped_snapshot.py`. Rules paid for:
- Strongest honest domain, in order: a non-learner string back to plain code; `value:<the key the code reads>`
  (`slots.carried(values, *keys)` for a `values.get(k1, values.get(k2))` chain); `enum:`/`bank:`; `E` over the local
  list (bind it to a name first, same rng draw); `R` over the draw bounds by name; `fill`/`join`/`transform`; only
  then `arithmetic` with src keys the values carry.
- Never a one-member domain of the value itself (`E((x,), ...)`): it bounds nothing.
- A `.get(k, fill(...))` default is built and RECORDED even when unused: make it lazy.
- Keep provenance as it was unless the dependence is plainly true; then re-diff §15 and explain every move.
- An honest domain can surface a real defect as an escape: report it by name and count; never weaken the domain.
- After every file: check module-level imports (a missing `R` raised `NameError` in H4-0-R2), run the scoped
  snapshot and the anchor one-liner. Byte identity is the proof: `render_snapshot --diff` reads 0 changed.

### 6.2 H6: retire the per-sample gates (ruling 25), only after H4 is proven

Remove `judgment_reviews_5` and the `capability_phase2` attestation stage as gates; keep their records as read-only
history; carry every confirmed defect (Phase 3 evidence) into the content report; update the contract rows and
`docs/pgen_judgment.md` in the same commit.

### 6.3 Exit (Phase 2 DONE, ruling 23) and items no batch owns yet (stop and ask before building any)

Exit: `run_all` exits 0 or 2; the corpus DETECTED with no INVALID; CERTIFIED; every finding names lc, seed and owed
build (this needs a ruling on lc-wide findings first); every check's NAMED LIMITS written. Unowned items:
- **lc and seed naming:** §5's findings name an lc but no seed; §6F names a seed in 49 of 78. Unruled.
- **Floors still hide content** (ruling 31): the §6 Phase 1 floor holds 5 `draw` gaps; `formatters_reachable` 6;
  `obligation_routes_reachable` 5.
- **Unit-test failures are integrity** (ruling 30): 6 lc-parametrized tests and
  `test_invariant_holds_across_the_live_tree`.
- **No cross-process determinism check:** `comparing_ordering` iterates a set; 89 of 7,285 renders change with
  `PYTHONHASHSEED`.
- **Unowned hint gaps:** a doubled word ("order word word"); `roles` misses "20 items at ₱50 each" hinted as "50
  groups of 20".
- **A non-digest commit can turn the unit suite red under a CERTIFIED tree** (`validation_reports/` is not a digest
  input): nothing gates the class, so run the unit suite at Phase 0 and after your last commit.

### 6.4 The generator work queue (NOT Phase 2)

- §2L: 420 non-exhibited variant values; 61 packet refusals. §6: 78 CONTRADICTED capabilities. §5: 752 judgment
  problems. §1J: 423 singular-after-many.
- §14 since H4's wider paths (79): +7 escapes from `fmt_emoji_pictorial`'s "items" fallback (now also on the
  STUDENT path, mat_g2_na_q2_4 seed 22); `pattern_sequence` pinned at seed 29 serving the single letters 'n'/'p' as
  options (4 `slot_text_unaccounted_14`, mat_g1_na_q3_6, mat_g2_na_q2_8); mat_g2_mg_q4_3 refusing its advertised
  `mcq` at seeds 17 and 29 (`slot_path_refused_14`). The 67 at the old 20 seeds were:
- §14: 67 escapes: H3-R2's 26 (incl. money_peso's `['peso5', ...]` and patterns' `[8, 8]` printed into hints); the
  `fmt_emoji_pictorial` "items" fallback, +29; base_generator's pictograph fallback `category` default, +5, and its
  bar-graph twin, +3 (neither learner-read at the 20 seeds); the fractions add/subtract hint chain served on
  count_sequence items, +4 (mat_g1_na_q4_2, every seed: "Add only the top numbers: 2 + 0 = 2.").
- §15: 58 + 6 (classified in the H3-R2 evidence; two fewer since H4-0-R2, a provenance correction).
- The "Found, not fixed" lists in the H3-R2, H4-0 and H4-0-R2 evidence: centavo items asking for pesos;
  clock-reading selections served as elapsed-time stems; silent fallbacks and defaults (incl. the `"+"`
  operation-symbol defaults, `model_names.get(model_type, "model")`, `_fraction_words`' digit fallback and "halfs",
  `num_to_words` past 10,000); two copies of the number-to-words builder; one-member answer domains (`answer_text`,
  fmt_true_false's "not" statement) that H4's judges must treat as unbounded.
- The interactive `draw` formatters (rulings 13–18, 31).

---

## 7. Rules you may not break

- **Verification is execution.** Quote every command with its verbatim output; otherwise write "not measured".
  Re-count every number you publish.
- **Never weaken a check.** Floors and pins move only for a documented ground-truth error.
- **Invocation:** `PYTHONPATH=. .venv/bin/python …`, logged, `EXIT $?` captured; never pipe a long run through
  `tail`. zsh does not word-split `$VAR`: use `${=VAR}`.
- **Heavy runs alone.** The mutation harness plants real bugs in real source (and in some `validation_reports/`
  files): never edit source, tests, snapshots or `validation_reports/` while it runs, and never run renders beside
  it. Afterwards the escaped-plant `git grep` shows only `validate_coverage.py:456`.
- **Stage by name** (never `git add -A`; the pre-commit hook also stages `graphify-out/`). Commit end lines name your
  model truthfully. Release the lock in a follow-up commit. Never `--amend` a commit you will cite.
- **Do not fix generator content** without an owner ruling; a source change stales reviews.
- **Instrumentation must be byte-identical** (`render_snapshot --diff`: 0 changed).
- **Not yours:** the ✝️/`bible` theme; `requires`/`requires_ignore`; opening H-11; supersession and CSI-R1–R3; H-09
  release promotion; renaming identities or "node" to "lc" in code; discarding filed records or the
  `batch117`–`batch150` corpus; `.claude/worktrees/agent-aaac714fac3fe0cc6`.
- **Traps measured in earlier batches:** locate insertion points by AST or by exact full-line match, never `rfind`;
  infer `value:<key>` from direct `values[...]` reads, not return dicts; template provenance counts the TRUE branch
  only; an upgrade proven only by observation may have an unobserved alternative
  (`validation_reports/phase2_hardening/h3r2_tools/fill_audit.py`); read every line `slot_wide_check.py` prints;
  a scoped check given an unknown formatter name gets an EMPTY lc list and silently measures the whole tree.

---

## 8. The re-proof chain (once per batch; about 4 h 20 min; detached)

```sh
PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q -p no:cacheprovider   # before committing source
# dev loop first: every mutation that plants in a changed file or runs your new check, one at a time:
#   PYTHONPATH=. .venv/bin/python tests/mutation_harness.py --only <name>
# (an INVALID "baseline exited 1" right after source edits is usually stale frontend evidence: run
#  DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py, then re-run that one mutation)
# commit source by name; bash validation_reports/phase2_hardening/h4_0_tools/anchors.sh must print "all anchors OK"; then:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin chain --force --session "<id>" --note "..."
nohup zsh local_only/scratch/<batch>/chain.sh > local_only/scratch/<batch>/chain.nohup 2>&1 &
```

`chain.sh` (copy `local_only/scratch/h4_0_r2/chain.sh` and change the directory):

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

- Measured in H4-0-R2: regen+benchmark+frontend 45 s, corpus 64 min (230 mutations), shards 24–27 min each, run_all
  40 min; 4 h 19 min in all. Each new mutation adds roughly 20–60 s to the corpus.
- Wait with one background `until grep -q "CHAIN DONE" $L/progress.log; do sleep 60; done` (one notification),
  never on `pgrep -f` of a string in the same command.
- **If interrupted:** confirm no `chain.sh`/`mutation_harness` process, no `MUTATION_IN_FLIGHT` marker, and that
  `tests.mutation_harness.recover_orphaned_mutation()` returns False; purge `__pycache__`; resume at the first
  stale artifact.
- **When it completes:** commit the artifacts by name (`validation_reports/mutation_proofs`,
  `.../obligation_release_shards`, `obligation_benchmark.json`, `frontend_static_render.json`); run
  `tree_state.py --complete --note "..."`; commit `tree_state.json`; confirm CERTIFIED.

---

## 9. Bookkeeping before you stop

- An evidence entry at the END of `validation_reports/HARDENING_EVIDENCE.md`: commands with verbatim output, seeds,
  every new check's mutation result and NAMED LIMITS, before/after counts, the owner questions asked and answered
  (record any new owner ruling verbatim in the plan doc too), and your own mistakes caught before commit.
- Append to H-06 `progress` surgically (`numstat 1 1`).
- **Rewrite §0, §2 and §5's status in this file.** No banners, no new prompt files.
- Commit by name; run the unit suite once more after the last commit (CERTIFIED cannot see `validation_reports/`);
  confirm the tree state; release the lock in a follow-up commit.
- If interrupted: leave an accurate open intent and a **committed** checkpoint.
