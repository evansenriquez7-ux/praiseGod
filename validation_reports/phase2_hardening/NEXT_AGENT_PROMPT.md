# Task prompt: Phase 2 pipeline hardening DONE — handoff to generator work (owner rulings 19–57)

**Rewritten 2026-10-20 after P2-A (part 2) upon Phase 2 completion (rulings 23, 27, 52–57). This REPLACES every earlier
version of this file.** `CLAUDE_AGENT_PROMPT.md`, `GPT_HANDOFF_PROMPT.md` and `HANDOFF_PROMPT.md` beside it (all in
`validation_reports/phase2_hardening/`) are history. Their method notes
are still correct and cited below: §7 heavy runs and the lock, §8 anchor one-liner, §9 traps, §11 not yours. Their
state sections are stale.

Trust order: a command you executed > this file > `CLAUDE_AGENT_PROMPT.md` > the dated blocks in
`docs/phase2_hardening_completion_plan.md`.

---

## 0. Your task, in one paragraph

**Phase 2 pipeline hardening is DONE** (rulings 23, 27, 52–57; artifacts certified at `e8ad784d`, digest
`1e0d9d480c1c3257`):
- every check is proven by a mutation that lands on its executed path (`UNPROVEN_ASSERTIONS` is empty: **202/202**
  assertions proven by execution, **0** knowingly unproven; **282/282** mutations `DETECTED`, `0` SURVIVED, `0`
  INVALID);
- `run_all` exits **2** with `INTEGRITY: GREEN` (`0` integrity failures across all 22 stages);
- every content finding across all 17 content labels is reported by name with its `lc`, witness `seed` (or ruling 52's
  substitute) and `Owed:` build, enforced by `content_finding_named` (PASS);
- the tree is `CERTIFIED` (`tests/tree_state.py`), and all 9 in-scope hardening rows (`H-01`..`H-08`, `H-10`) in
  `validation_reports/phase2_hardening/hardening_status.json` are `closed` (`H-09` `out_of_scope`).

**Your task now is generator (content) work (§6)**: clear the content findings in the `run_all` work queue until
`python -m backend.app.practice_gen.validation.run_all` exits **0** with `INTEGRITY: GREEN` and `CERTIFIED`. Remember
that `backend/app/practice_gen/validation/` and `docs/pgen_contract.md` are read-only during generator work unless an
owner ruling directs a harness change, and any generator/DNA/formatter edit inside `mutation_proof.INPUT_ROOTS` will
require re-running affected §17 stem judges (on fresh packets with new dispatch ids) and the §8 re-proof chain before
stopping. Leave this file rewritten for the next session when you stop.

**Terminology.**
- **Node** vs **lc**: the harness calls `mat_g3_dp_q3_4` a "node"; `CLAUDE.md` calls it an **lc**. A node is the
  bundle `mat_g3_dp_q3`.
- **Clause:** a fragment of one lc's competency text.
- **Stem family:** (spine id or call-site module, template, renderer), as `stem_packets.family_key` defines it.
- Do not rename code identifiers.

---

## 1. Read first (in this order; budget about 45 minutes)

1. `CLAUDE.md` (a symlink to `AGENTS.md`): the Scaling Mandate, Engineering Protocols, Content Rules, Definition
   of Done, and "If you are a judge". Then `MEMORY.md`, especially these entries:
   - "Mutation must land where behaviour changes"
   - "Proof admissible, not just detected"
   - "New run_all stage needs a stub"
   - "CERTIFIED can hide a red unit test"
   - "Allowlist checks drift silently"
   - "Duplicated rule copies disagree"
   - "Name-keyed stage dispatch hid failures"
   - "Dispatch subagents on Haiku"
2. This file, completely.
3. **Owner rulings** in `docs/phase2_hardening_completion_plan.md`, verbatim: 19–22 (search "rulings recorded
   2026-10-07"), 23–51 (search "rulings recorded 2026-10-08"), and 52–57 (search "rulings recorded 2026-10-19").
4. `validation_reports/HARDENING_EVIDENCE.md`, newest at the END. Read "2026-10-20 — P2-A (part 2) & Phase 2 DONE",
   "2026-10-19 — P2-A (part 1)", "H4-C" and "H4" fully, then the NAMED LIMITS of "H4-0-R2", "H4-0" and "H3-R2".
5. `docs/pgen_contract.md`:
   - the verdict row and the rule above `_manifest.FINDING_CLASS`;
   - §5 (`validate_judgment`), §6 (capability), §17 (stem review), and §18 (`validate_determinism`);
   - §8 (mutation proofs, assertion coverage) and §10 (`phase1_hermetic`).
6. `validation_reports/phase2_hardening/hardening_status.json`: all 10 H-rows (`9 closed, 1 out_of_scope`).
7. Code, as background:
   - `backend/app/practice_gen/validation/run_all.py`: the stage table, the `_stage_*` functions
     run through `ledger.run(...)`, the Phase 2 stage loop, `_check_content_findings_named`, and the verdict and
     exit code;
   - `backend/app/practice_gen/validation/_manifest.py` (`FINDING_CLASS`, 202 labels);
   - `backend/app/practice_gen/validation/validate_coverage.py` (`UNPROVEN_ASSERTIONS`, empty `{}`);
   - `tests/mutation_harness.py` (282 mutations);
   - `tests/unit/test_stage_ledger.py` (`stubbed_harness`);
   - `tests/tree_state.py`.
8. `validation_reports/phase2_hardening/CLAUDE_AGENT_PROMPT.md` §7, §8, §9, §11.

---

## 2. State at handoff (2026-10-20, Phase 2 DONE; re-measure before quoting)

```
HEAD                main at the handoff commit that last changed this file (after e8ad784d); check
                    `git status -sb` for whether it is pushed
source              1956e7f9 (last source/contract change, scoping 4 §2 mutations) on top of ce82b256
                    (rulings 53, 56, 57, H-02, H-05) and 28fc7d40 (rulings 52, 54, 55, H-06, H-07);
                    chain + tree_state e8ad784d
locks               ALL RELEASED @ e8ad784d (9 closed, 1 out_of_scope in hardening_status.json)
tree_state          CERTIFIED (282 proofs, 7 shards, benchmark, frontend fresh; digest 1e0d9d480c1c3257)
run_all             2026-10-20 on e8ad784d: EXIT 2; scheduled=22 completed=12 failed=10 crashed=0 not_run=0
                    incomplete=0; INTEGRITY GREEN; unit_tests 1030 passed, 1 skipped (full `tests/unit -m "not slow"`:
                    1082 passed, 1 skipped); mutation_proof_integrity_8 282 verified;
                    assertion_coverage_8 202/202 proven by execution, 0 knowingly unproven;
                    content_finding_named PASS; finding_class_registry_complete 202 labels;
                    census nodes=151 unit_tests=1016 mutations=282
  CONTENT (17)      stem_review_fail_17 141, stem_clause_unproducible_17 15,
                    carried_judgment_defect_5 751, carried_capability_defect_6F 78,
                    variant_not_exhibited_2L 420, attester_packet_refused_2L 61,
                    count_noun_singular_after_many_1J 423, render_hash_order_dependent_18 81 (on 4 lcs),
                    slot_domain_escape_14 74, slot_text_unaccounted_14 4, slot_path_refused_14 1,
                    selector_value_unexhibited_15 58, hint_sequence_unshown_15 6,
                    formatters_served_are_advertised 30 (on 16 lcs), formatters_reachable 6,
                    obligation_routes_reachable 5, capability_contract (Phase 1 draw) 5
§17                 every lc has a filed first judge and blind confirmer (355 records); 141 FAIL, 10 PASS,
                    15 NOT_PRODUCIBLE clauses; every §17 integrity label PASS
mutations           282; corpus 282/282 DETECTED, 0 SURVIVED, 0 INVALID
latest attestation  batch447 (next free prefix: batch448)
```

Hardening rows (`PYTHONPATH=. .venv/bin/python tests/hardening_status.py` -> `9 closed, 1 out_of_scope`):

| Row | Status | Closed at |
|---|---|---|
| H-01 | closed | `06ca013c` |
| H-02 | closed (`0` unproven assertions; `202/202` proven) | `e8ad784d` |
| H-03 | closed | `b9da4bd2` |
| H-04 | closed | `a0f3b1e8` |
| H-05 | closed (`formatters_served_are_advertised` + `lab_v1` `ClockSet` grading check) | `e8ad784d` |
| H-06 | closed (§17 + §14 + §5/§6 retirement per rulings 25 & 55) | `28fc7d40` |
| H-07 | closed (per ruling 56; NAMED LIMITS documented) | `e8ad784d` |
| H-08 | closed (pointer-drag NAMED LIMIT documented in docstring + contract + evidence) | `e8ad784d` |
| H-09 | out_of_scope | — |
| H-10 | closed (`tests/tree_state.py` + 4 artifact families CERTIFIED) | `e8ad784d` |

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
- 23: **Phase 2 hardens the pipeline, not the generators**; it is DONE when integrity is green, every check is
  proven by a mutation on its executed path, the tree is CERTIFIED, and every finding is reported with its lc,
  seed and what to build.
- 24: LLM judges review stems plus field domains; deterministic checks prove fields stay inside them.
- 25: **the per-sample gates (`judgment_reviews_5`, `capability_phase2`) are retired once the stem gate and field
  checks are each proven by mutation; records stay as read-only history; confirmed defects go to the content
  queue.**
- 26: clause coverage is ruled per lc from stems and declared variants, proven by the §2L exhibit check.
- 27: `run_all` exits 0 / 2 / 1; harness work is done at 0 or 2.  28: structured slots.  29: judges see `CLAUDE.md`.
- 30: unit-test failures are integrity.  31: floors (superseded by ruling 53).  32: record defects are content.
- 33: slots cover everything the learner reads (hints included).  34: an un-instrumented site is a content finding.
- 35, 41: §15 decides selector survival by slot and value-level provenance (`derives`, `computes`, template `_src`).
- 36: H5 hint checks are content only.  37: many slices may share one chain.  38: `error_label` is metadata.
- 39: error-detect names its ErrorPattern.  40: indefinite articles by sound, gated by §1J.
- 42: H4 approves an lc only after its type-only slots are tightened (true for all 151).
- 43: a type-only slot's reason is a registered `slots.DERIVED_REASONS` kind plus a `src` the values carry.
- 44: the stem gate's design.
  - (d) ONE overall verdict per lc: `stem_review_fail_17` names templates, not seeds.
  - (e) Every lc gets a first judge and a blind confirmer; the later verdict stands.
  - (h) Haiku judges, about 6 concurrent.
- 45: the campaign was approved.  46–48e: packet content.  49: a standing FAIL is settled by real renders.
  50, 50b: a value slot shows what it printed (HASH_VERSION 8).
- 51: ruling 21 only where every ground of the standing record is disproved by renders; every disproof is logged.
- 52: every content finding must carry a witness seed from `validate_slots.paths()` where a render exists, or an
  explicit `seed=<none:...>` reason where no render exists (`stem_clause_unproducible_17`, unreached routes/formatters,
  un-seeded records), plus `Owed:`; enforced by `content_finding_named`.
- 53: the three content floors (`obligation_routes_reachable`, `formatters_reachable`, §6 Phase 1 `capability_contract`)
  are removed as floors and reclassified as `"content"` findings naming each gap with `lc`, `seed`, and `Owed:`.
- 54: cross-process determinism (§18 `validate_determinism.py`, `render_hash_order_dependent_18`) compares §14's 7,285
  paths across `PYTHONHASHSEED=1` and `PYTHONHASHSEED=2`; the 81 order-dependent paths on 4 lcs are `"content"`.
- 55: `judgment_reviews_5` and `capability_phase2` are replaced by read-only historical defect carriers (`carried_judgment_defect_5`:
  751 defects; `carried_capability_defect_6F`: 78 capabilities); integrity checks on the historical corpora remain active.
- 56: H-07 is closed against §17 + §14 + §15 with explicit NAMED LIMITS in `docs/pgen_contract.md` §17 and
  `HARDENING_EVIDENCE.md`.
- 57: `census_unit_tests` and `census_mutations` are proven directly by mutation in `tests/mutation_harness.py`
  (`census_unit_tests_floor_breached`, `census_mutations_floor_breached`), bringing `UNPROVEN_ASSERTIONS` to `0`.

**Stop and ask** for any content judgment or design question that rulings 1–57 and MATATAG do not settle, and for
anything in "Not yours" (§7).

---

## 4. Phase 0: baseline and lock (always, before any edit)

1. Check the starting state:
   - `ps` grep is empty;
   - `df -h /System/Volumes/Data` shows space;
   - `PYTHONPATH=. .venv/bin/python tests/tree_state.py` prints CERTIFIED;
   - `PYTHONPATH=. .venv/bin/python tests/hardening_status.py` prints `9 closed, 1 out_of_scope`;
   - the worktree is clean; note what `git status -sb` says about origin (push only when the owner asks).

   CERTIFIED does not cover `validation_reports/`, so also run
   `PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q -p no:cacheprovider`. Expect 1082 passed,
   1 skipped; run it in the background and read while it runs.
2. Before any edit inside `mutation_proof.INPUT_ROOTS` or `INPUT_FILES`, open a tree-state intent:
   `PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin batch --session <yours> --note "<batch>: ..."`.
3. Re-measure the target stage(s) before and after editing.

---

## 5. Phase 2 completion summary (all batches A–F DONE at `e8ad784d`)

All five owner questions in §5.1 were answered and recorded verbatim as **owner rulings 52–57** in
`docs/phase2_hardening_completion_plan.md`. Batches A–F were completed across commits `28fc7d40`, `ce82b256`,
`1956e7f9`, and `e8ad784d`:
- **A. H6 (`H-06`, ruling 55):** Retired live per-sample gates; added read-only historical defect carriers
  `carried_judgment_defect_5` (751 findings) and `carried_capability_defect_6F` (78 findings) while preserving
  all historical corpus integrity checks.
- **B. `H-02` (`UNPROVEN_ASSERTIONS` -> 0, ruling 57):** Planted and proved 11 mutations covering every previously
  unproven assertion (`concept_gating_leaks_future_term`, `reverse_compatibility_check_crashes`,
  `reverse_curriculum_gate_accepts_future_term`, `reverse_curriculum_gate_check_crashes`,
  `visual_schema_integrity_missing_kind`, `monotonicity_drops_known_vocab`, `coverage_regression_1h_drops_node`,
  `census_unit_tests_floor_breached`, `census_mutations_floor_breached`), plus the 2 rollup labels removed with H6.
  `assertion_coverage_8` now reports `202/202 proven by execution, 0 knowingly unproven`.
- **C. Floors & determinism (rulings 53 & 54):** Removed the three floors (`obligation_routes_reachable` 5,
  `formatters_reachable` 6, `capability_contract` Phase 1 `draw` 5) and reclassified them as named `"content"`
  findings; added §18 `validate_determinism.py` (`render_hash_order_dependent_18`: 81 paths on 4 lcs, `"content"`, and
  `determinism_subprocess_18`, `"integrity"`).
- **D. Naming every content finding (ruling 52):** Every content finding across all 17 active content labels now
  carries `lc`, `seed=<int>` (or `seed=<none:reason>`), and `Owed: <what to build>`, enforced by
  `content_finding_named` in `run_all.py` and proven by `content_finding_named_omits_seed`.
- **E. `H-05`, `H-07`, `H-08`, `H-10`:** Closed with full acceptance-check evidence in `hardening_status.json` and
  `HARDENING_EVIDENCE.md`. Added `formatters_served_are_advertised` (catching 30 unadvertised `(lc, formatter)` pairs on
  16 lcs) and `lab_v1` `ClockSet` elapsed-time grading verification in `validate_DiagnosticLab.py` (planting and
  detecting `lab_route_clockset_ignores_elapsed_hours` without mutating generator content on `mat_g1_mg_q4_4`).
- **F. Exit verification:** Full chain completed at `e8ad784d` (`282/282` mutations `DETECTED`, 7 obligation shards
  `0` failures across `519,615` cache keys / `2,078,460` executions, `run_all` EXIT 2 with `INTEGRITY: GREEN`,
  `tree_state.py` `CERTIFIED`).

### 5.3 Integrity rules carried over (non-negotiable)

- Records are never edited or deleted.
- One dispatch id per review.
- The identity names the model that judged.
- Judges see `CLAUDE.md` (ruling 29).
- A judge that read any file other than its packet is set aside.
- The dispatcher never retypes a verdict.

If you dispatch §17 stem judges after editing a generator/DNA/formatter:
- use `effort: "medium"` (or the owner-specified judge model);
- give prompts of 2,000 lines or more as explicit chunked Read calls;
- the tools H4-C used are committed in `validation_reports/phase2_hardening/h4c_tools/` (read its README.md); they
  assume H4-C's gitignored scratch layout, so copy and re-prove them before relying on them.

---

## 6. The generator work queue (17 content labels in `run_all`)

Every item below is named by `lc`, `seed`, and `Owed:` in `run_all`'s output:

1. `stem_review_fail_17`: **141** FAIL lcs (each naming its witness seed, failing templates, and judge remedies).
   Disproved and real grounds per lc: `validation_reports/phase2_hardening/h4c_tools/r49.log`.
2. `stem_clause_unproducible_17`: **15** `NOT_PRODUCIBLE` clauses (listed in the "H4-C" evidence entry).
3. `carried_judgment_defect_5`: **751** historical per-sample judgment defects across the read-only §5 corpus.
4. `carried_capability_defect_6F`: **78** `CONTRADICTED` capabilities across the read-only §6F corpus.
5. `variant_not_exhibited_2L`: **420** non-exhibited `(lc, axis, value)` pairs.
6. `attester_packet_refused_2L`: **61** packet refusals.
7. `count_noun_singular_after_many_1J`: **423** singular-after-many grammar findings.
8. `render_hash_order_dependent_18`: **81** `PYTHONHASHSEED`-sensitive paths on **4** lcs (`mat_g1_na_q1_9`,
   `mat_g1_na_q2_2`, `mat_g2_na_q1_8`, `mat_g3_na_q1_6` — set iteration in `comparing_ordering.py`).
9. `slot_domain_escape_14`: **74** slot domain escapes.
10. `slot_text_unaccounted_14`: **4** unaccounted slot text findings.
11. `slot_path_refused_14`: **1** refused slot path.
12. `selector_value_unexhibited_15`: **58** unexhibited selector values.
13. `hint_sequence_unshown_15`: **6** unshown hint sequences.
14. `formatters_served_are_advertised`: **30** `(lc, formatter)` pairs served by `practice_portal` (`format_mode="all"`)
    that are absent from `ADVERTISED_FORMATTERS[lc]` across **16** lcs (`mat_g1_mg_q4_1..4`, `mat_g2_mg_q3_1..4`,
    `mat_g3_dp_q3_1..4`, `mat_g3_mg_q1_5..6`, `mat_g3_na_q4_5`, `mat_g3_na_q4_8`).
15. `formatters_reachable`: **6** advertised `(lc, formatter)` pairs never produced on the 64-seed sweep (`pictorial_group`
    on `mat_g2_na_q1_1`, `mat_g2_na_q1_5`, `mat_g2_na_q2_4`, `mat_g2_na_q2_5`, `mat_g3_na_q1_2`, `mat_g3_na_q1_5`).
16. `obligation_routes_reachable`: **5** obligation routes with zero reaching lcs (`balance_scale`, `fill_in_blank`,
    `numeric_input`, `table_read`, `ten_frame`).
17. `capability_contract` (§6 Phase 1): **5** `draw` capabilities with no matching formatter (`mat_g1_mg_q1_3`,
    `mat_g2_mg_q1_4`, `mat_g2_mg_q4_3`, `mat_g3_mg_q1_3`, `mat_g3_mg_q3_3`; rulings 13–18, 31, 53).
- Plus the "Found, not fixed" lists in the P2-A (part 2), H4-C, H4, H4-0-R2, H4-0 and H3-R2 evidence entries:
  - `mat_g1_mg_q4_4` seed 8 (`difficulty="mid"`): `measurement_geometry.py` sets `correct_answer = f"{end_h}:00"` for
    an elapsed-time ("How many hours was the activity?") stem while `interactive_config.target_hours = duration`, so
    `lab_v1` `ClockSet` submission of `{hours: duration, minutes: 0}` grades `is_correct=False`;
  - a wrong True/False key on `mat_g3_na_q4_2` (seeds 11, 16);
  - `"48 ÷ 8"` on `mat_g2_na_q3_6`/`_9`;
  - `"order word word"`;
  - `'peso60'`;
  - the gaming/fandom `OBJECTS_POOL` members;
  - `fmt_emoji_pictorial`'s `"items"` fallback;
  - single-letter `pattern_sequence` options.

---

## 7. Rules you may not break

- **Verification is execution.** Quote every command with its verbatim output; otherwise write "not measured".
  Re-count every number you publish.
- **Never weaken a check.** Floors and pins move only for a documented ground-truth error or an owner ruling.
- **Invocation:** `PYTHONPATH=. .venv/bin/python …`, logged, with `EXIT $?` captured. Never pipe a long run through
  `tail`. zsh does not word-split `$VAR`: use `${=VAR}`.
- **Heavy runs alone.** The mutation harness plants real bugs in real source (and in some `validation_reports/`
  files). Never edit source, tests, snapshots or `validation_reports/` while it runs, and never run renders beside
  it. Afterwards the escaped-plant `git grep` shows only `validate_coverage.py:456`.
- **Stage by name.** Never `git add -A`; the pre-commit hook also stages `graphify-out/`. Commit end lines name your
  model truthfully. Release the lock in a follow-up commit. Never `--amend` a commit you will cite. Push only when
  the owner asks.
- **Do not fix generator content** without an owner ruling; a source change stales reviews and §17 records. If one
  is unavoidable, re-dispatch the stale lcs' §17 judges on fresh packets (new dispatch ids).
- **Instrumentation must be byte-identical** (`render_snapshot --diff`: 0 changed).
- **Not yours:**
  - the ✝️/`bible` theme;
  - `requires`/`requires_ignore`;
  - opening H-11;
  - supersession and CSI-R1–R3;
  - H-09 release promotion;
  - renaming identities, or "node" to "lc", in code;
  - discarding filed records or the `batch117`–`batch150` corpus;
  - `.claude/worktrees/agent-aaac714fac3fe0cc6`.
- **Traps measured in earlier batches:**
  - Locate insertion points by AST or by exact full-line match, never `rfind`.
  - Infer `value:<key>` from direct `values[...]` reads, not return dicts.
  - Template provenance counts the TRUE branch only.
  - An upgrade proven only by observation may have an unobserved alternative.
  - Read every line `slot_wide_check.py` prints.
  - A scoped check given an unknown formatter name gets an EMPTY lc list and silently measures the whole tree.
  - A mutation's fixture invalidated by same-session work shows only in the FULL table run.

---

## 8. The re-proof chain (once per batch that changes source; about 4 h 50 min; detached)

```sh
PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q -p no:cacheprovider   # before committing source
# dev loop first: every mutation that plants in a changed file or runs your new check, one at a time:
#   PYTHONPATH=. .venv/bin/python tests/mutation_harness.py --only <name>
# (an INVALID "baseline exited 1" right after source edits is usually stale frontend evidence: run
#  DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py, then re-run that one mutation)
# commit source by name; bash validation_reports/phase2_hardening/h4_0_tools/anchors.sh must print "all anchors OK"; then:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin chain --force --session "<id>" --note "..."
mkdir -p local_only/scratch/<batch>
nohup zsh validation_reports/phase2_hardening/h4c_tools/chain.sh <batch> > local_only/scratch/<batch>/chain.nohup 2>&1 &
```

The chain script is committed: `validation_reports/phase2_hardening/h4c_tools/chain.sh <batch>` (logs go to
`local_only/scratch/<batch>/chain/`). It reads `projection.recommended_shard_count` from `obligation_benchmark.json`
after the benchmark step (7 today) and moves stale `shard_*_of_*.json` receipts aside first. Never hard-code the
shard count.

Measured in H4-C on `6ebbd1b3`:
- regen + benchmark + frontend: 50 s;
- corpus: 68 min (262 mutations);
- 7 shards: 26–27 min each;
- run_all: 48 min;
- about 5 h in all.

Each new mutation adds roughly 20–60 s to the corpus.

- Wait with one background `until grep -q "CHAIN DONE" local_only/scratch/<batch>/chain/progress.log; do sleep 60; done`
  (one notification).
  Never wait on `pgrep -f` of a string in the same command.
- **If interrupted:**
  - confirm there is no `chain.sh` or `mutation_harness` process;
  - confirm there is no `MUTATION_IN_FLIGHT` marker;
  - confirm `tests.mutation_harness.recover_orphaned_mutation()` returns False;
  - purge `__pycache__`;
  - resume at the first stale artifact.
- **When it completes:**
  - commit the artifacts by name (`validation_reports/mutation_proofs`, `.../obligation_release_shards`,
    `obligation_benchmark.json`, `frontend_static_render.json`);
  - run `tree_state.py --complete --note "..."`;
  - commit `tree_state.json`;
  - confirm CERTIFIED.

---

## 9. Bookkeeping before you stop

- **Evidence entry.** Add one at the END of `validation_reports/HARDENING_EVIDENCE.md`, with:
  - commands with verbatim output, and seeds;
  - every new check's mutation result and NAMED LIMITS;
  - before and after counts;
  - the owner questions asked and answered (record each new ruling verbatim in the plan doc too);
  - your own mistakes caught before commit.
- **Hardening rows.** Append to the worked row's `progress` surgically (`numstat 1 1`). Close a row (`status`) only
  with evidence per acceptance check.
- **Rewrite this file's §0, §2 and §5 status.** No banners, no new prompt files.
- **Commit and release.** Commit by name, then run the unit suite once more after the last commit (CERTIFIED
  cannot see `validation_reports/`). Confirm the tree state, and release the lock in a follow-up commit.
- **If interrupted:** leave an accurate open intent and a **committed** checkpoint.
