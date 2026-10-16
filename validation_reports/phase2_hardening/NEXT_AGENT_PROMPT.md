# Task prompt: finish Phase 2 pipeline hardening (owner rulings 19–51; Claude host)

**Rewritten 2026-10-16 after batch H4-C, at the owner's request: "rewrite the next_agent_prompt.md for a fresh claude
agent session to finish phase 2 hardening". This REPLACES every earlier version of this file.**
`CLAUDE_AGENT_PROMPT.md`, `GPT_HANDOFF_PROMPT.md` and `HANDOFF_PROMPT.md` beside it are history. Their method notes
are still correct and cited below: §7 heavy runs and the lock, §8 anchor one-liner, §9 traps, §11 not yours. Their
state sections are stale.

Trust order: a command you executed > this file > `CLAUDE_AGENT_PROMPT.md` > the dated blocks in
`docs/phase2_hardening_completion_plan.md`.

---

## 0. Your task, in one paragraph

**Finish Phase 2** (ruling 23): harden the testing pipeline until it meets the exit test in §5. The §17 stem
review gate is built, proven, and run to completion over all 151 lcs (batches H4 and H4-C). What is left is:
- **H6**, retiring the per-sample LLM gates (ruling 25);
- the **exit items** that still need an owner ruling;
- the open hardening rows **H-02, H-05, H-07, H-08, H-10**;
- a final exit verification.

Work in batches (§5.2). Each batch is claimed, proven by mutation on the path it executes, chained, CERTIFIED,
logged and released. **Ask the owner the questions in §5.1 before building anything they govern.** One question at
a time, each with measured numbers and a recommendation.

Do not fix generator content. The 141 §17 FAILs and every other content finding are the generators' work queue
(ruling 23, §6), not Phase 2 blockers. Leave this file rewritten for the next session when you stop.

**Goal of Phase 2 (ruling 23, with ruling 27).** It is done when:
- every check is proven by a mutation that lands on its executed path (Scaling Mandate 1–2);
- `run_all` exits 0 or 2 (integrity green);
- every finding is reported by name with its lc, seed and what to build;
- the tree is CERTIFIED.

Content findings do not block Phase 2.

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
   2026-10-07") and 23–51 (search "rulings recorded 2026-10-08"; 27–51 follow). Rulings 23, 25, 27, 30, 31 and 44d
   govern what is left.
4. `validation_reports/HARDENING_EVIDENCE.md`, newest at the END. Read "H4-C" and "H4" fully, then the NAMED LIMITS
   of "H4-0-R2", "H4-0" and "H3-R2".
5. `docs/pgen_contract.md`:
   - the verdict row and the rule above `_manifest.FINDING_CLASS`;
   - §5 (`validate_judgment`), §6 (capability) and §17 (stem review), whose NAMED LIMITS H6 must re-read;
   - §8 (mutation proofs, assertion coverage) and §10 (`phase1_hermetic`).
6. `validation_reports/phase2_hardening/hardening_status.json`: rows H-02, H-05, H-06, H-07, H-08, H-10 (`finding`,
   `acceptance_checks`, `progress`).
7. Code, as background:
   - `validation/run_all.py`: the stage table (~line 670), the stage functions (~line 1105), the stage list
     (~line 1204), and the verdict and exit code;
   - `validation/_manifest.py` (`FINDING_CLASS`);
   - `validation/validate_coverage.py` (`UNPROVEN_ASSERTIONS`);
   - one `Mutation(...)` in `tests/mutation_harness.py`;
   - `tests/test_stage_ledger.py` (`stubbed_harness`);
   - `tests/tree_state.py`.
8. `CLAUDE_AGENT_PROMPT.md` §7, §8, §9, §11.

---

## 2. State at handoff (2026-10-16, after H4-C; re-measure before quoting)

```
HEAD                d729425a on main, PUSHED (origin/main == main)
source              6ebbd1b3 (last harness change, ruling 50b); chain 563f7c59; tree_state 9067acd4;
                    §17 records 967f5d2c; evidence/handoff f5e16525; lock released d729425a
H-06 lock           RELEASED @ f5e16525; claim a row before any work (§4)
tree_state          CERTIFIED (262 proofs, 7 shards, benchmark, frontend fresh; digest 28d1e3f4ef451da6)
run_all             2026-10-16 after d729425a: EXIT 2; scheduled=22 completed=15 failed=7 crashed=0; INTEGRITY
                    GREEN; unit_tests 1010 passed, 1 skipped; mutation_proof_integrity_8 262 verified;
                    assertion_coverage_8 184/195 proven by execution, 11 knowingly unproven;
                    finding_class_registry_complete 195 labels; census nodes=151 unit_tests=1011 mutations=262
  CONTENT           judgment_reviews 752, capability_contract 78, stem_review_fail_17 141,
                    stem_clause_unproducible_17 15, count_noun_singular_after_many_1J 423,
                    variant_not_exhibited_2L 420, attester_packet_refused_2L 61, slot_domain_escape_14 74,
                    slot_text_unaccounted_14 4, slot_path_refused_14 1, selector_value_unexhibited_15 58,
                    hint_sequence_unshown_15 6   (log: local_only/scratch/h4c/run_all_final.log)
§17                 every lc has a filed first judge and blind confirmer (355 records); 141 FAIL, 10 PASS,
                    15 NOT_PRODUCIBLE clauses; every §17 integrity label PASS
floors              obligation_routes_reachable 5 unreachable (balance_scale, fill_in_blank, numeric_input,
                    table_read, ten_frame); formatters_reachable 6; the §6 Phase 1 floor's 5 draw gaps
                    (the last two from the 2026-10-13 handoff; re-measure)
mutations           262; corpus 262/262, no INVALID
latest attestation  batch447 (next free prefix: batch448)
```

Open hardening rows (H-01, H-03 and H-04 are closed; H-09 is out of scope):

| Row | Status |
|---|---|
| H-02 | no progress recorded |
| H-05 | PARTIAL |
| H-06 | PARTIAL; its §17 work is done |
| H-07 | no progress recorded |
| H-08 | substantial progress recorded |
| H-10 | `tests/tree_state.py` exists and works, but the row is still open with no progress recorded |

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
  queue.** Its precondition now holds (§17 and §14 proven; the §17 campaign complete).
- 26: clause coverage is ruled per lc from stems and declared variants, proven by the §2L exhibit check.
- 27: `run_all` exits 0 / 2 / 1; harness work is done at 0 or 2.  28: structured slots.  29: judges see `CLAUDE.md`.
- 30: unit-test failures are integrity.  31: floors unchanged.  32: record defects are content.
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

**Stop and ask** for any content judgment or design question that rulings 1–51 and MATATAG do not settle, and for
anything in "Not yours" (§7).

---

## 4. Phase 0: baseline and lock (always, before any edit)

1. Check the starting state:
   - `ps` grep is empty;
   - `df -h /System/Volumes/Data` shows space;
   - `PYTHONPATH=. .venv/bin/python tests/tree_state.py` prints CERTIFIED;
   - the worktree is clean and `git status -sb` shows no divergence from origin.

   CERTIFIED does not cover `validation_reports/`, so also run
   `PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q -p no:cacheprovider`. Expect 1010 passed,
   1 skipped, about 12 minutes; run it in the background and read while it runs.
2. Claim the row you will work. In `validation_reports/phase2_hardening/hardening_status.json`, edit ONLY its
   `owner` line with `sed` (`git diff --numstat` must read `1 1`) and commit by name. Then run
   `PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin batch --session <yours> --note "<batch>: ..."`.
3. Re-measure, and explain any move before building:
   - `run_all`'s CONTENT line (§2), about 45 minutes; or the stage modules one by one:
     - `validate_slots`: 74 / 4 / 1, type-only PASS, `151 of 151`;
     - `validate_stem_review`: missing 0, fail 141, unproducible 15, every integrity label PASS, 2684 families;
     - `validate_composition`: 58 + 6, 1,351 of 1,351 decided;
     - `validate_language`: `indefinite_article_1J` PASS, 423 mirror findings;
   - the capability queue snippet below (`78 42 33 55` at H4-0-R2's Phase 0; about 2 minutes);
   - `assertion_coverage_8` and its 11 `UNPROVEN_ASSERTIONS` (§5.2 B).
4. If you will touch any source:
   - run `PYTHONPATH=. .venv/bin/python -m tests.render_snapshot local_only/scratch/<batch>/before.jsonl` BEFORE
     the first edit;
   - keep `tests/slot_wide_check.py` as a baseline (expect `TOTAL distinct 24 | renders that raised: 2`);
   - keep the §15 dump as a baseline (`validation_reports/phase2_hardening/h4_0_tools/comp_dump.py OUT.json`).

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

## 5. What is left, and how to finish it

### 5.1 Owner questions to ask FIRST (each blocks the work it governs; ask one at a time)

The owner asked this session to finish Phase 2. That covers the work below. It does not settle the design choices,
which earlier rulings left open:

1. **Naming findings by lc, seed and what to build** (ruling 23's exit test). Several findings name an lc but no
   seed:
   - §5 `judgment_reviews` names an lc but no seed.
   - §6F names a seed in only 49 of 78 (2026-10-13; re-measure).
   - §17 `stem_review_fail_17` names an lc and the quoted templates; ruling 44d makes it lc-wide.

   Ask whether an lc-wide finding may stand as "lc + template/clause + owed build" with no seed. If not, ask
   whether each must carry a witness seed: a render that prints the failing template, found from
   `validate_slots.paths()`. Recommend the witness seed where one exists. A clause ruled NOT_PRODUCIBLE has no
   render, so lc + clause + owed build must be enough for it.
2. **Floors that hide content** (ruling 31 left them unchanged):
   - `obligation_routes_reachable` 5;
   - `formatters_reachable` 6;
   - the §6 Phase 1 floor's 5 `draw` gaps.

   Ask whether each floor becomes a named content finding (an lc, a route, an owed build) or stays as a documented
   Phase 2 limit.
3. **Cross-process determinism.** `comparing_ordering` iterates a set, and 89 of 7,285 renders changed with
   `PYTHONHASHSEED` (2026-10-13; re-measure). Ask whether a determinism check belongs in Phase 2. It would run
   §14's paths under two hash seeds and diff them, which plants and proves trivially. Ask too whether the set
   iteration it would expose counts as content.
4. **H6's shape** (§5.2 A). Two questions:
   - Are `judgment_reviews` (752) and `capability_contract` (78) re-filed as content findings in the new report?
   - Or are they frozen as read-only history, with only their confirmed defects carried into the generator queue?

   Ruling 25 says "carried into the work queue". Ask how they are named: by lc and seed from the record.
5. **H-07** (contextual and logical validity, ambiguity, hints, misconceptions, interaction clarity,
   accessibility). Much of it overlaps the §17 stem judges' Rule 1. Ask whether §17 plus §14 satisfy it for Phase
   2, or whether the §1L semantic-role checks and calibrated reviewers in its acceptance checks are still required.
   Recommend closing it against §17 with its NAMED LIMITS written, if the owner agrees.

Record every answer verbatim as owner ruling 52, 53, … in the plan doc (same format as 44–51) before building.

### 5.2 The batches (suggested order; each is its own claim, proof, chain and release)

**A. H6: retire the per-sample gates (ruling 25; row H-06).**
- Remove `judgment_reviews_5` and the `capability_phase2` attestation stage as gates in `run_all`.
- Keep their records as read-only history: never edit or delete `validation_reports/judgment_reviews/`, attester
  records or the batch117–batch150 corpus.
- Carry every confirmed defect into the content report in the shape question 4 decides.
- In the same commit, update the contract rows §5 and §6 and `docs/pgen_judgment.md` (Protocol 7).
- Update `_manifest.FINDING_CLASS` and `test_stage_ledger.stubbed_harness`. Memory "New run_all stage needs a stub":
  removing a stage also moves the stage-ledger mutations.
- Re-run the assertion-coverage census. `judgment_reviews` and `capability_contract` are in `UNPROVEN_ASSERTIONS`
  as rollup prints, and leave it with their stages.
- Prove the replacement: §17 plus §14 must still catch what the retired gates caught. Name in the evidence which
  of the retired gates' confirmed defect classes §17/§14 now catch, by mutation or by a filed §17 FAIL. Name the
  rest as a NAMED LIMIT.
- Close H-06 only when its four acceptance checks each have evidence.

**B. H-02: no assertion without an executed mutation.**
`UNPROVEN_ASSERTIONS` holds 11 entries (shrink-only):

| Assertion | Why it is unproven |
|---|---|
| `concept_gating` | — |
| `reverse_compatibility_check_crash` | — |
| `reverse_curriculum_gate_check` | — |
| `reverse_curriculum_gate_check_crash` | — |
| `visual_schema_integrity` | measured as shadowed by §1G |
| `monotonicity` | — |
| `judgment_reviews` | rollup; leaves with H6 |
| `capability_contract` | rollup; leaves with H6 |
| `census_unit_tests` | self-referential floor |
| `census_mutations` | self-referential floor |
| `coverage_regression_1H` | — |

For each one:
- plant a mutation that lands on the executed path and is caught by name; or
- write an owner-approved narrow limitation with an independent executable control, per H-02's acceptance check;
  ask the owner for the self-referential census floors.

"Shadowed" means the check is unreachable, which is itself a finding: either the check moves so it can fire, or it
is removed with the reason recorded.

**C. Exit items 2 and 3 (§5.1 answers):** floors and determinism, as the owner rules.

**D. Naming every finding (§5.1 answer 1).**
- Make every content label print lc, seed (or the ruled substitute) and owed build.
- Add a check that FAILS when a content finding lacks them, built while its count is zero (Scaling Mandate 5).
  Prove it with a mutation that strips the seed from one stage's finding.

**E. H-05, H-08, H-10.** Re-measure each row against its own acceptance checks:
- **H-10:** `tests/tree_state.py`, with `--begin`/`--complete` intent and a committed digest-free state file, likely
  satisfies all five checks. Show each by command and close it.
- **H-08:** check the pointer-drag blind spot is written as a NAMED LIMIT.
- **H-05:** PARTIAL. List what is left and fix it or rule it.

Close a row only with evidence per acceptance check.

**F. Exit verification (last).**
- One full chain (§8) on the final source.
- `run_all` EXIT 0 or 2 with INTEGRITY GREEN.
- The corpus DETECTED with no INVALID.
- `tree_state.py` CERTIFIED.
- Every content label names lc, seed and owed build.
- Every check's NAMED LIMITS written in its docstring, contract row and the evidence log.
- Every hardening row closed or ruled out of scope.
- A final evidence entry "Phase 2 DONE". Update `CLAUDE.md`'s Definition of Done only if a ruling changed it
  (Protocol 7).
- Then rewrite this file to hand off to generator work (§6).

### 5.3 Integrity rules carried over (non-negotiable)

- Records are never edited or deleted.
- One dispatch id per review.
- The identity names the model that judged: Haiku via the `haiku` alias; read the model from the transcript, since
  the alias resolved to `claude-haiku-5-5` and cannot pin a version.
- Judges see `CLAUDE.md` (ruling 29).
- A judge that read any file other than its packet is set aside.
- The dispatcher never retypes a verdict.

If you dispatch judges:
- use `effort: "medium"`;
- give prompts of 2,000 lines or more as explicit chunked Read calls;
- the tools in `local_only/scratch/h4c/` (`h4c.py`, `taf.sh`, `mkdisp.py`, `render_dump.py`) are uncommitted
  scratch; copy and re-prove them before relying on them.

---

## 6. The generator work queue (NOT Phase 2; for after the exit)

- §17: 141 FAIL lcs (`stem_review_fail_17`, each naming its failing templates) and 15 NOT_PRODUCIBLE clauses (the
  "H4-C" evidence entry lists them).
- Disproved and real grounds per lc: `local_only/scratch/h4c/r49.log` (uncommitted).
- §2L: 420 non-exhibited variant values; 61 packet refusals.
- §6: 78 CONTRADICTED capabilities.
- §5: 752 judgment problems.
- §1J: 423 singular-after-many.
- §14: 74 / 4 / 1.
- §15: 58 + 6.
- The "Found, not fixed" lists in the H4-C, H4, H4-0-R2, H4-0 and H3-R2 evidence entries. These include:
  - a wrong True/False key on mat_g3_na_q4_2 (seeds 11, 16);
  - "48 ÷ 8" on mat_g2_na_q3_6/_9;
  - "order word word";
  - 'peso60';
  - the gaming/fandom OBJECTS_POOL members;
  - `fmt_emoji_pictorial`'s "items" fallback;
  - single-letter `pattern_sequence` options.
- The interactive `draw` formatters (rulings 13–18, 31).

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
nohup zsh local_only/scratch/<batch>/chain.sh > local_only/scratch/<batch>/chain.nohup 2>&1 &
```

Copy `local_only/scratch/h4c/chain50.sh`, NOT `h4c/chain.sh`, which hard-codes 6 shards. `chain50.sh` reads
`projection.recommended_shard_count` from `obligation_benchmark.json` after the benchmark step (7 today) and moves
stale `shard_*_of_*.json` receipts aside first. Change its directory, and never hard-code the shard count.

Measured in H4-C on `6ebbd1b3`:
- regen + benchmark + frontend: 50 s;
- corpus: 68 min (262 mutations);
- 7 shards: 26–27 min each;
- run_all: 48 min;
- about 5 h in all.

Each new mutation adds roughly 20–60 s to the corpus.

- Wait with one background `until grep -q "CHAIN DONE" $L/progress.log; do sleep 60; done` (one notification).
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
