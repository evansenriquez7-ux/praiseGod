# Task prompt: Phase 2 pipeline hardening under owner rulings 23–42 (Claude host)

**Rewritten 2026-10-11 after batch H3-R2 finished the H3 rollout. This REPLACES every earlier version of this
file.** `CLAUDE_AGENT_PROMPT.md`, `GPT_HANDOFF_PROMPT.md` and `HANDOFF_PROMPT.md` beside it are history. Their
method notes (§7 heavy runs and the lock, §8 anchor one-liner, §9 traps, §11 not yours) remain correct and are
cited below; their state sections are stale.

**If you are a fresh session given this file:** your task is batch **H4-0** (§4): build the type-only-slot count
that owner ruling 42 requires, prove it, then tighten the type-only slots of as many lcs as you can finish, prove
the tree byte-identical, run the §6 chain once, and leave the tree CERTIFIED with §1 and §4 of this file rewritten
for the next session. Do not start H4's LLM review until H4-0 has reached at least one lc, and do not start H6.

Trust order: a command you executed > this file > `CLAUDE_AGENT_PROMPT.md` > the dated blocks in
`docs/phase2_hardening_completion_plan.md`.

**Goal (ruling 23).** Phase 2 hardens the **testing pipeline**; it does not fix the problem generators. It is done
when:
- every check is proven by a mutation that lands on the path it executes (Scaling Mandate 1–2);
- `run_all` exits 0 or 2 (integrity green; ruling 27);
- every finding is named by lc, seed and owed build;
- the tree is CERTIFIED.

Content findings are the generators' work queue (listed in §4 "The generator work queue"). You do not fix them,
unless the owner rules otherwise, as rulings 39–40 did.

**Terminology.** The harness calls `mat_g3_dp_q3_4` a "node"; `CLAUDE.md` calls it an **lc**. A node is the bundle
`mat_g3_dp_q3`. A **clause** is a fragment of one lc's competency text. Do not rename code identifiers.

---

## 0. Read first

1. `CLAUDE.md` (a symlink to `AGENTS.md`): the Scaling Mandate, Engineering Protocols, Content Rules, Definition of
   Done (ruling 27's three exit codes) and "If you are a judge". Then `MEMORY.md`, especially:
   - "Duplicated rule copies disagree";
   - "Allowlist checks drift silently";
   - "Mutation must land where behaviour changes";
   - "Proof admissible, not just detected";
   - "Declared variant may be a no-op".
2. This file, completely.
3. **Owner rulings 23–42** in `docs/phase2_hardening_completion_plan.md`, verbatim (search "rulings recorded
   2026-10-08"; 27–42 follow). Also rulings 1, 9, 12–16 and 19–22 above them.
4. `validation_reports/HARDENING_EVIDENCE.md`, newest at the END:
   - "H3-R2: the H3 rollout completed, value-level provenance (ruling 41), and owner rulings 37-42" (read fully);
   - "H3-R1: first H3 rollout slice" (its item 4 is corrected in H3-R2);
   - "H5: composition checks a stem review cannot see";
   - "H3: structured slots (ruling 28) and the §14 field-domain check";
   - "H2: run_all exits 0 / 2 / 1";
   - "H1: §2L declared variants must reach the render".
5. `docs/pgen_contract.md` rows:
   - §14 (`validate_slots`: NAMED LIMITS 1–10, the H3-R1 and H3-R2 amendments);
   - §15 (`validate_composition`: limits 1–8, the H3-R2 amendment);
   - §1J (the H3-R2 amendment: `indefinite_article_1J`, `error_label` as metadata);
   - §16 (the hint contract);
   - §2L;
   - the verdict row and the rule above `_manifest.FINDING_CLASS`.
6. `backend/app/practice_gen/slots.py`: the whole module docstring and every function. This is the instrument you
   will extend: `fill(_src=)`, `S(src=)`, `derived`, `derives`, `computes`, `record`, `bank_fields`, `TRANSFORMS`,
   `RENDERERS`.
7. `CLAUDE_AGENT_PROMPT.md` §7, §8, §9, §11.

---

## 1. State at handoff (2026-10-11, after H3-R2; re-measure before quoting)

```
HEAD                local main at the commit that updated this file (after the H-06 release); NOT pushed
                    (check `git status -sb`)
source              e45915da (H3-R2), checkpoint 5f4738af (rulings 38-40); chain artifacts 035725cc,
                    tree_state 931213d1
H-06 lock           RELEASED; claim it (owner line only, numstat 1 1) before any work
tree_state          CERTIFIED (227 proofs, 6 shards, benchmark, frontend fresh; digest 2fad777fd91972b3)
run_all             2026-10-11 on e45915da: EXIT 2, scheduled=21 completed=15 failed=6 crashed=0; INTEGRITY GREEN;
                    finding_class_registry_complete 182 labels; CONTENT: variant_not_exhibited_2L 420,
                    attester_packet_refused_2L 61, judgment_reviews 752, capability_contract 78,
                    count_noun_singular_after_many_1J 423, slot_domain_escape_14 26,
                    selector_value_unexhibited_15 60, hint_sequence_unshown_15 6; §16 0
§14                 slot_text_unaccounted_14 0 (the rollout is complete); slot_domain_escape_14 26 (all real:
                    20 `items` fallbacks + 6 Python lists printed into hints)
                    type-only slots: 63% of slot-fills, 1,233 distinct site/slot pairs (ruling 42's queue)
§15                 1,351 of 1,351 selector matches decided by record; 60 selector_value_unexhibited_15 (classified
                    in the H3-R2 evidence) + 6 hint_sequence_unshown_15
§1J                 indefinite_article_1J 0; count_noun_singular_after_many_1J 423
render snapshot     tests/render_snapshot.py: 7,285 renders; H3-R2's baseline local_only/scratch/h3r2/s9.jsonl
                    (gitignored: re-take your own `before` snapshot first)
unit suite          978 passed, 1 skipped (~11 min)
mutations           227; corpus 227/227, NO INVALID
latest attestation  batch440 (next free prefix: batch441)
```

**Before you resume anything detached, run `ps -eo pid,lstart,command | grep claude`**: one copy of the agent per
conversation.

**Rollout tools (H3-R2).** Committed as copies under `validation_reports/phase2_hardening/h3r2_tools/`, and also in
the gitignored `local_only/scratch/h3r2/`. Promote the ones you reuse into `tests/` inside your own batch: `tests/`
is a digest input, so moving them changes the proof digest and must happen before your chain.
- `fstr2fill.py`: f-string to fill converter.
- `provenance_pass.py`: slot and template provenance by data and control dependence.
- `upgrade_value.py`: `value:`/`fill` upgrades from observation over seeds 1-40 plus pinned formatters.
- `wide_check.py`: §14's own `check_slot`/`replay` over the same wide seeds.
- `fill_audit.py`: static audit of `"fill"` slots.
- `scoped_snap.py`: byte check for chosen lcs against a full snapshot.
- `probe.py`: the fills and provenance of one render.
- `inv.py`, `comp_run.py`, `comp_groups.py`: inventories.

**Open items no batch owns yet** (named in the evidence; stop and ask before building any):
- **lc and seed naming** (Exit item): §5's findings name an lc but no seed, and §6F 49 of 78 name a seed. What
  "seed" means for an lc-wide finding is unruled.
- **Floors still hide content** (ruling 31): the §6 Phase 1 floor holds 5 `draw` gaps, `formatters_reachable` 6 and
  `obligation_routes_reachable` 5.
- **Unit-test failures are integrity** (ruling 30): 6 lc-parametrized tests and
  `test_invariant_holds_across_the_live_tree`.
- **No cross-process determinism check:** `comparing_ordering` iterates a set, so 89 of 7,285 renders change with
  `PYTHONHASHSEED`.
- **Unowned hint gaps:** a doubled word ("order word word"); `roles` misses "20 items at ₱50 each" hinted as "50 groups
  of 20". (Code-shaped hints are now §14 escapes.)

---

## 2. Rulings in force (verbatim in the plan doc)

- 23: Phase 2 hardens the pipeline, not the generators.
- 24: LLM judges review stems plus field domains.
- 25: the per-sample gates are retired once replaced.
- 26: clause coverage is ruled from stems, proven by the exhibit check.
- 27: `run_all` exits 0 / 2 / 1.
- 28: structured slots.
- 29: judges see `CLAUDE.md`.
- 30: unit-test failures are integrity.
- 31: floors unchanged.
- 32: record defects are content.
- 33: slots cover everything the learner reads.
- 34: an un-instrumented site is a shrinking content finding.
- 35: selector survival by slot provenance.
- 36: H5 hint checks are content only.
- 37: many slices may share one chain.
- 38: `format_data.error_label` is metadata.
- 39: error-detect names its ErrorPattern.
- 40: indefinite articles by sound, gated by §1J.
- 41: §15 closes over value-level provenance (`derives`, `computes`, template `_src`).
- 42: **H4 approves an lc only after that lc's type-only slots are tightened.**

**Stop and ask** for any content judgment or design question rulings 1–42 and MATATAG do not settle, and for
anything in "Not yours" (§5).

---

## 3. What a slot is now (the instrument, in one page)

- `fill(template, _src=(...), name=S(value, domain, src=(...)))` returns `template.format(...)`. Under
  `slots.capture()` it records the template, every slot's value, domain and provenance, the call site, and any
  template provenance.
- **Domains, strongest first:**
  - `value:<key>` (equals the generated value);
  - `E(members, basis)`, `R(lo, hi, basis)`;
  - `enum:<module.NAME>`, `bank:<module.NAME>:<field>`, `noun:<module.NAME>`;
  - `fill` (another recorded fill);
  - `num.derived` / `text.derived` (type only; written by `slots.derived(x)`).
- **Provenance** (§15, rulings 35 and 41):
  - slot `src` (the values keys the value derives from);
  - `_src` (the keys whose test CHOSE the template, true branch only);
  - `slots.derives(key, src)` (a value chosen because of `src`);
  - `slots.computes(key, src)` (a value that is a function of `src`).
  All are the generator's claim. H4's judges review them, and a false one hides a real finding.
- **Option text:** `formatters/_answer_slots.py` (`answer_text`, `distractor_text`, `member_text`,
  `correct_option_key`, `distractors_field`).
- **Banks:** `slots.bank_fields(item, "<module>.<BANK>")`.
- **Spines:** `Spine.render` -> `dna.base.render_spine_text`, replayed through `slots.RENDERERS["spine"]`.
- **Articles:** `dna.base.indefinite_article` / `with_article`.

---

## 4. Plan

| batch | status | what it delivers | blocked by |
|---|---|---|---|
| H1 | DONE 2026-10-09 | §2L variant exhibit check | — |
| H2 | DONE 2026-10-10 | `run_all` exits 0 / 2 / 1 | — |
| H3 | **DONE 2026-10-11** (infrastructure H3; slices H3-R1, H3-R2) | structured slots everywhere; §14 accounting 0 | — |
| H5 | DONE 2026-10-10 | §1J mirror, §15, §16 | — |
| **H4-0** | **next** | ruling 42: a count of type-only slots per lc, then tightening lc by lc | — |
| H4 | open | stem review gate (LLM), per lc once H4-0 has reached it | H4-0 per lc |
| H6 | open | retire `judgment_reviews_5` and `capability_phase2` as gates | H4 |
| Exit | — | the Exit list below holds on one chain | all |

Each batch is one `batch` intent and, under ruling 37, as many slices as you can prove before ONE re-proof chain
(§6).

### Phase 0: baseline and lock (always)

1. The `ps` grep is empty, `df -h /System/Volumes/Data` shows space, `tests/tree_state.py` prints CERTIFIED, and the
   worktree is clean.
2. Claim H-06: edit only its `owner` line (`git diff --numstat` must read `1 1`), commit, then
   `PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin batch --session <yours> --note "<batch>"`.
3. Re-measure, and explain any move before building:
   - `validate_slots`: expect `slot_text_unaccounted_14` PASS and `slot_domain_escape_14 (26)`;
   - `validate_composition`: expect 60 + 6, with 1,351 of 1,351 decided;
   - `validate_language`: expect `indefinite_article_1J` PASS and 423 mirror findings;
   - the queue snippet from H3-R1's brief (expect `78 42 33 55`).
4. `PYTHONPATH=. .venv/bin/python -m tests.render_snapshot local_only/scratch/<batch>/before.jsonl` BEFORE any edit.

### H4-0: type-only slots (owner ruling 42)

1. **Build the count first (Mandate 5: a gate before its queue).** In `validate_slots`, add a label for each (lc,
   site, slot) whose domain is `num.derived`/`text.derived` and carries no named reason. Suggested name:
   `slot_domain_type_only_14`.
   - Class it **content**, as ruling 34 classed the H3 rollout count (ruling 42 says it "rolls out lc by lc, like
     H3"). If you doubt the class, stop and ask.
   - Register it in `_manifest.FINDING_CLASS` and §14's `ASSERTIONS`.
   - Write its contract amendment and NAMED LIMITS.
   - Add a mutation that a clean lc catches by name: tighten one lc fully, then plant a `derived(...)` there.
   - Measure the baseline. Expect about 1,233 site/slot pairs; count per lc.
2. **A "named reason".** Some slots are genuinely computed, such as the sum shown in a hint or a running total. Their
   honest domain is `R(lo, hi, basis)` from the generator's bounds, or a `computes` declaration plus the values they
   come from. Design how a slot carries "this is derived arithmetic, checked by the hint contract" (for example
   `S(x, "num.derived", src=(...))` with a reason string) and stop and ask if the design is not obvious. Never
   exempt a slot by name in the harness (Mandate 4).
3. **Tighten lc by lc,** using `upgrade_value.py`'s method (observe over seeds 1-40 plus pinned formatters; upgrade
   only on unanimous evidence) and reading the code for the rest. After each lc:
   - `scoped_snap.py` 0 changed;
   - `wide_check.py` reports only the known escapes;
   - §14 and §15 unchanged or better.
   Full snapshot and full §14/§15 before the chain.
4. Every changed line that a mutation anchors on must be re-anchored to plant the SAME defect: run the §8 anchor
   one-liner after every file. H3-R2 re-anchored 8 this way.

### H4: stem review gate (ruling 24, LLM half), per lc once H4-0 reaches it

- **Enumerate stem families mechanically from the record,** not by grep: every distinct `Fill.template` (and spine
  id) an lc's student-path renders reach, at the H4 seeds, with each slot's domain and provenance. Pair them with the
  lc's competency text and clauses. One packet per lc.
- A **blind** judge rules per family:
  - can any value in the declared domains produce a wording, vocabulary-gating (Rule 1), cognitive-load (Rule 2) or
    scope (Rule 3) error;
  - are the `src`/`_src`/`derives`/`computes` claims true;
  - can the lc's stems produce every clause (ruling 26).
- Freshness keys on the hash of templates plus domains plus provenance, not on seeds.
- Integrity rules carried over:
  - one dispatch id per lc;
  - verdicts never edited;
  - ruling 20's confirming judge;
  - ruling 21 for disputed claims;
  - the identity names the model;
  - delivery by opaque file (memory: attester dispatch gotchas);
  - judges see `CLAUDE.md` (ruling 29);
  - a judge that read any file other than its packet is set aside.
- Mutations:
  - a stem edit with no new review is stale and caught;
  - a packet missing a reachable family is caught;
  - a judged record whose verdict is removed is caught.

### H6: retire the per-sample gates (ruling 25), only after H4 is proven

Remove `judgment_reviews_5` and the `capability_phase2` attestation stage as gates. Keep the records as read-only
history. Carry every confirmed defect (listed in the Phase 3 evidence) into the content report. Update the contract
rows and `docs/pgen_judgment.md` in the same commit.

### Exit (Phase 2 DONE, per ruling 23)

- `run_all` exits 0 or 2; the corpus is DETECTED with no INVALID; the tree is CERTIFIED.
- Every finding names its lc, seed and owed build. This needs a ruling on lc-wide findings first.
- Every check's NAMED LIMITS are written.

### The generator work queue (NOT Phase 2)

- §2L: 420 non-exhibited variant values and 61 packet refusals.
- §6: 78 CONTRADICTED capabilities.
- §5: 752 judgment problems.
- §1J: 423 singular-after-many.
- §14: 26 escapes.
- §15: 60 + 6, classified in the H3-R2 evidence.
- The H3-R2 "Found, not fixed" list:
  - centavo items asking for pesos;
  - clock-reading selections served as elapsed-time stems;
  - three silent fallbacks.
- The interactive `draw` formatters (rulings 13–18, 31).

Do not start them in a Phase 2 session.

---

## 5. Rules you may not break

- **Verification is execution.** Quote every command with its verbatim output; otherwise write "not measured". Re-count
  every number you publish.
- **Never weaken a check.** Floors and pins move only for a documented ground-truth error.
- **Invocation:** `PYTHONPATH=. .venv/bin/python …`, logged, with `EXIT $?` captured; never pipe through `tail`.
- **Heavy runs alone.** The mutation harness plants real bugs in real source: never edit source, snapshot or test
  while it runs. Afterwards the escaped-plant `git grep` must show only `validate_coverage.py:456`.
- **Stage by name** (an explicit path list is fine; never `git add -A`). Commit end lines name your model truthfully.
  Release the lock in a follow-up commit. Never `--amend` a commit you will cite.
- **Do not fix generator content** without an owner ruling. A source change stales reviews.
- **Instrumentation must be byte-identical.** `render_snapshot --diff` reads 0 changed. A content change the owner
  authorized is attributed field by field (H3-R2's `fielddiff.py`).
- **Not yours:**
  - the ✝️/`bible` theme;
  - `requires`/`requires_ignore`;
  - opening H-11;
  - supersession and CSI-R1–R3;
  - H-09 release promotion;
  - renaming identities or "node" to "lc" in code;
  - discarding filed records or the `batch117`–`batch150` corpus;
  - `.claude/worktrees/agent-aaac714fac3fe0cc6`.

**Traps measured in H3-R1/H3-R2:**
- zsh does not word-split `$VAR`: use `${=VAR}` or write the paths out.
- A `str.rfind("    return {")` also matches deeper-indented returns. Locate insertion points by AST or by exact
  full-line match: H3-R2 briefly put a declaration and a `return` at function level this way, and reverted it.
- Inferring `value:<key>` from return dicts is unreliable. Use direct `values[...]` reads, or unanimous observation.
- A template-provenance pass must count the TRUE branch only. Crediting an `else` fallback hid real §15 findings
  until it was stripped.
- An upgrade proven only by observation (`"fill"`, `value:`) may have an unobserved alternative. Run `fill_audit.py`.
- `wide_check` excludes nothing but the known escapes. Read every line it prints.

---

## 6. The re-proof chain (once per batch; about 4 h 30 min; detached)

```sh
PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q -p no:cacheprovider   # before committing source
# commit source by name; run the CLAUDE_AGENT_PROMPT.md §8 anchor one-liner; then:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin chain --force --session "<id>" --note "..."
nohup zsh local_only/scratch/<batch>/chain.sh > local_only/scratch/<batch>/chain.nohup 2>&1 &
```

`chain.sh` (H1's, unchanged):

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

- Measured in H3-R2: regen+benchmark+frontend 45 s, corpus 64 min (227 mutations), shards 24-27 min each, run_all 40 min; 4 h 18 min in all.
- Wait on the sentinel (`until grep -q "CHAIN DONE" progress.log`), never on `pgrep -f` of a string in the same command.
- **If the chain is interrupted:**
  1. confirm no `chain.sh`/`mutation_harness` process runs, no `MUTATION_IN_FLIGHT` marker exists, and
     `tests.mutation_harness.recover_orphaned_mutation()` returns False;
  2. purge `__pycache__`;
  3. resume at the first stale artifact.
- **When it completes:**
  1. commit the artifacts by name;
  2. run `tree_state.py --complete`;
  3. commit `tree_state.json`;
  4. confirm CERTIFIED;
  5. release the lock.

---

## 7. Bookkeeping before you stop

- An evidence entry with:
  - commands and verbatim output;
  - seeds;
  - every new check's mutation result and NAMED LIMITS;
  - the before/after counts.
- Append to H-06 `progress` surgically (`numstat 1 1`).
- **Rewrite §1 and §4's status in this file.** No banners, no new prompt files.
- Commit by name, close the intent, confirm the tree state, release the lock in a follow-up commit.
- If interrupted, leave an accurate open intent and a **committed** checkpoint.
