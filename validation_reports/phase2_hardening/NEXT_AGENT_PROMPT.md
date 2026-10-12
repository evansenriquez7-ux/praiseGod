# Task prompt: Phase 2 pipeline hardening under owner rulings 23–43 (Claude host)

**Rewritten 2026-10-12 after batch H4-0-R2 tightened the last 50 lcs (ruling 42's count is 0 on all 151). This
REPLACES every earlier version of this file.** `CLAUDE_AGENT_PROMPT.md`, `GPT_HANDOFF_PROMPT.md` and `HANDOFF_PROMPT.md` beside it
are history. Their method notes (§7 heavy runs and the lock, §8 anchor one-liner, §9 traps, §11 not yours) remain
correct and are cited below; their state sections are stale.

**If you are a fresh session given this file:** the next batch is **H4** (§4): the LLM stem review gate (ruling 24),
built per lc now that every lc is at 0 type-only slots (ruling 42). It is a new check: design it from §4's H4
section, prove each of its mutations by name, run the §6 chain once, and leave the tree CERTIFIED with §1 and §4
rewritten. **Stop and ask** before dispatching any judge or fixing any design point rulings 1–43 do not settle
(packet shape, freshness key, the confirming-judge rule). Do not start H6.

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
3. **Owner rulings 23–43** in `docs/phase2_hardening_completion_plan.md`, verbatim (search "rulings recorded
   2026-10-08"; 27–43 follow). Also rulings 1, 9, 12–16 and 19–22 above them.
4. `validation_reports/HARDENING_EVIDENCE.md`, newest at the END:
   - "H4-0-R2: the ruling-42 rollout completed (937 -> 0; 151 of 151 lcs at 0)" (read fully);
   - "H4-0: the ruling-42 type-only slot count, owner ruling 43, and the first 101 lcs tightened";
   - "H3-R2: the H3 rollout completed, value-level provenance (ruling 41), and owner rulings 37-42";
   - "H3-R1: first H3 rollout slice" (its item 4 is corrected in H3-R2);
   - "H5: composition checks a stem review cannot see";
   - "H3: structured slots (ruling 28) and the §14 field-domain check";
   - "H2: run_all exits 0 / 2 / 1";
   - "H1: §2L declared variants must reach the render".
5. `docs/pgen_contract.md` rows:
   - §14 (`validate_slots`: NAMED LIMITS 1–12, the H3-R1, H3-R2 and H4-0 amendments);
   - §15 (`validate_composition`: limits 1–8, the H3-R2 amendment);
   - §1J (the H3-R2 amendment: `indefinite_article_1J`, `error_label` as metadata);
   - §16 (the hint contract);
   - §2L;
   - the verdict row and the rule above `_manifest.FINDING_CLASS`.
6. `backend/app/practice_gen/slots.py`: the whole module docstring and every function. This is the instrument you
   will extend: `fill(_src=)`, `S(src=, why=)`, `derived(why=)`, `DERIVED_REASONS`, `join`, `derives`, `computes`,
   `record`, `bank_fields`, `TRANSFORMS`, `RENDERERS`. Then `validate_slots.py` (check (e), `type_only_reason`).
7. `CLAUDE_AGENT_PROMPT.md` §7, §8, §9, §11.

---

## 1. State at handoff (2026-10-12, after H4-0-R2; re-measure before quoting)

```
HEAD                local main at the commit that updated this file (after the H-06 release); NOT pushed
                    (check `git status -sb`)
source              ea3c1600 (H4-0-R2); chain artifacts `75f15cc2`, tree_state `c26fd7fb`
H-06 lock           RELEASED; claim it (owner line only, numstat 1 1) before any work
tree_state          CERTIFIED (230 proofs, 6 shards, benchmark, frontend fresh; digest 8fd5dbe548788b49)
run_all             2026-10-13 on ea3c1600: EXIT 2, scheduled=21 completed=15 failed=6 crashed=0; INTEGRITY GREEN; 172/183 assertions proven by execution;
                    CONTENT: variant_not_exhibited_2L 420, attester_packet_refused_2L 61, judgment_reviews 752, capability_contract 78, count_noun_singular_after_many_1J 423, slot_domain_escape_14 67, selector_value_unexhibited_15 58, hint_sequence_unshown_15 6; slot_domain_type_only_14 PASSES
§14                 slot_domain_type_only_14 0: 151 of 151 lcs at 0 (ruling 42's rollout is complete);
                    slot_domain_escape_14 67 (H4-0's 60, plus base_generator's bar-graph `category` default +3 and
                    the fractions add/subtract hint chain run on count_sequence items +4); slot_text_unaccounted_14 0
                    type-only slot-fills without a reason: 0% at the 20 seeds; over seeds 1-40 + every pinned
                    formatter only the two list-printing escapes stay type-only (H4-0: 672 site/slot pairs);
                    61 unreasoned `derived(` lines remain in source, 60 of them reached by nothing (NAMED LIMIT 11)
§15                 58 + 6 (1,351 of 1,351 decided); the 2 fewer are a provenance correction (H4-0-R2 evidence)
§1J                 indefinite_article_1J 0; count_noun_singular_after_many_1J 423 (unchanged)
render snapshot     tests/render_snapshot.py: 7,285 renders; H4-0-R2's baseline local_only/scratch/h4_0_r2/s4.jsonl
                    (gitignored: re-take your own `before` snapshot first)
unit suite          986 passed, 1 skipped (~11 min)
mutations           230; corpus 230/230, NO INVALID
latest attestation  batch440 (next free prefix: batch441)
```

**Before you resume anything detached, run `ps -eo pid,lstart,command | grep claude`**: one copy of the agent per
conversation.

**Every lc is at 0 type-only slots** at the 20 seeds, so H4 may start on any lc. A slot a new seed, profile or
pinned formatter reaches can still be type-only (NAMED LIMIT 11); the tools below find and tighten it.

**Tools.** Promoted into `tests/` (digest inputs): `tests/slot_wide_check.py` (§14's own checks over seeds 1-40 + every
pinned formatter; a render that raises is now printed and counted, not skipped) and `tests/scoped_snapshot.py` (byte
check for chosen lcs against a full snapshot). Committed in `validation_reports/phase2_hardening/h4_0_tools/`; they take
their paths as arguments and run in place (`PYTHONPATH=. .venv/bin/python validation_reports/phase2_hardening/h4_0_tools/<tool> ...`):
- `tonly.py`: the real `validate_slots.collect_findings`, dumped as JSON, open lcs counted.
- `obs.py`: every type-only slot observed over seeds 1-40 + pinned formatters (values, keys equal in EVERY observation,
  whether every value is another fill's text).
- `plan.py`: the greedy order of lcs (fewest new site/slot pairs first) with each slot's code line and observation.
- `propose.py` + `tighten.py`: unanimous `value:`/`fill` proposals, rewritten by AST position (dry run first, read it).
- `rep.py`: exact replacements with asserted counts; adds slot imports (CHECK module-level imports afterwards: it
  missed a function-level-only import once, see the evidence).
- `cn_rewrite.py`: `derived(count_noun(n, p))` -> `E((count_noun(1, p), p))` by AST.
- `reanchor.py`: rewrite one mutation's (old, new) literals by AST position.
- `kinds.py`, `comp_dump.py` (§15 findings in full, to diff), `anchors.sh` (the §8 anchor one-liner).

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
  of 20".
- **A non-digest commit can turn the unit suite red under a CERTIFIED tree** (found in H4-0): H3-R2 committed
  `h3r2_tools/` after its chain; `test_the_live_ledger_claims_every_artifact_on_disk` failed from then on, while
  `tree_state` printed CERTIFIED, because `validation_reports/` is not a digest input. H4-0 fixed the instance (H-06
  claims both tools directories); nothing gates the class.

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
- 43: a type-only slot's named reason is a registered `slots.DERIVED_REASONS` kind plus a non-empty `src` the
  generator's values carry; the count covers every RECORDED slot, learner-reachable or not.

**Stop and ask** for any content judgment or design question rulings 1–43 and MATATAG do not settle, and for
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
  - `num.derived` / `text.derived` (type only; written by `slots.derived(x)`); counted by
    `slot_domain_type_only_14` unless `slots.derived(x, src=(...), why="<kind>")` names a registered
    `DERIVED_REASONS` kind (only `arithmetic` so far) and every `src` key is in the values.
- **Joins:** `slots.join(sep, parts, domain, src)` records a variable-length list as one slot per member.
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
| H3 | DONE 2026-10-11 (infrastructure H3; slices H3-R1, H3-R2) | structured slots everywhere; §14 accounting 0 | — |
| H5 | DONE 2026-10-10 | §1J mirror, §15, §16 | — |
| H4-0 | DONE 2026-10-12 | ruling 42's count (`slot_domain_type_only_14`), ruling 43's reason form, 3 mutations; 101 lcs tightened | — |
| H4-0-R2 | DONE 2026-10-12 | the last 50 lcs to 0 (937 -> 0; 151 of 151), byte-identical; `slots.carried` | — |
| **H4** | **next** | stem review gate (LLM), per lc at 0 type-only slots | — (151 of 151 ready) |
| H6 | open | retire `judgment_reviews_5` and `capability_phase2` as gates | H4 |
| Exit | — | the Exit list below holds on one chain | all |

Each batch is one `batch` intent and, under ruling 37, as many slices as you can prove before ONE re-proof chain
(§6). H4-0-R2 finished the count, so H4 is built once against a complete one.

### Phase 0: baseline and lock (always)

1. The `ps` grep is empty, `df -h /System/Volumes/Data` shows space, `tests/tree_state.py` prints CERTIFIED, and the
   worktree is clean. CERTIFIED does not cover `validation_reports/` (open item above), so also run
   `PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q -p no:cacheprovider` (expect 985 passed).
2. Claim H-06: edit only its `owner` line (`git diff --numstat` must read `1 1`), commit, then
   `PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin batch --session <yours> --note "<batch>"`.
3. Re-measure, and explain any move before building:
   - `validate_slots`: expect `slot_domain_escape_14 (60)`, `slot_domain_type_only_14 (937)`, NOTE `101 of 151`;
   - `validate_composition`: expect 60 + 6, with 1,351 of 1,351 decided;
   - `validate_language`: expect `indefinite_article_1J` PASS and 423 mirror findings;
   - the capability queue snippet below (expect `78 42 33 55`; about 2 min):

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

4. `PYTHONPATH=. .venv/bin/python -m tests.render_snapshot local_only/scratch/<batch>/before.jsonl` BEFORE any edit.
   Also dump `comp_dump.py` and run `tests/slot_wide_check.py` BEFORE any edit: they are your §15 and escape baselines
   (expect `TOTAL distinct 19 | renders that raised: 2` -- the two `mat_g2_mg_q4_3` pinned-mcq refusals).

### H4-0-R2: the remaining type-only slots (owner rulings 42-43) -- DONE 2026-10-12; the method, for slots a new path reaches

Per wave (H4-0 ran five): `obs.py` -> `plan.py N` -> read each slot's code -> tighten -> `tonly.py` -> anchors ->
full snapshot (56 s) -> §15 dump -> wide check. Rules H4-0 paid for:
- **Strongest honest domain, in this order:** turn a non-learner string back into plain code; `value:<the key the
  code reads>` (never a key chosen by testing equality); `enum:`/`bank:` over the generator's own module object;
  `E` over the local list or literal pair it is drawn from (bind a literal list to a name first, same rng draw);
  `R` over the draw bounds by name; `fill`/`slots.join`/`slots.transform`; and only then `arithmetic` with the
  values keys it is computed from.
- **Count nouns** use `E((count_noun(1, p), p))`, the generator's own rule, never a restated singular.
- **Keep provenance as it was** (copy each slot's `src`), unless the dependence is plainly true; then re-diff §15.
- **An honest domain can surface a real defect as an escape** (H4-0: the `items` fallback, the `category` default).
  Report it by name and count; never weaken a domain to hide it.
- **After every file:** module-level slot imports (a function-level import hid a missing `E` once); the anchor
  one-liner (seven mutations were re-anchored in H4-0 to plant the SAME defect, with `reanchor.py`).
- Do not use `git stash` while anything runs.

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
- §14: 67 escapes (H3-R2's 26; the `fmt_emoji_pictorial` items fallback at its name slots, +29; base_generator's
  pictograph fallback `category` default, +5, and its bar-graph twin, +3; the fractions add/subtract hint chain
  served on count_sequence items, +4: "Add only the top numbers: 2 + 0 = 2." on mat_g1_na_q4_2).
- §15: 58 + 6, classified in the H3-R2 evidence (two fewer since H4-0-R2: a provenance correction).
- The H3-R2 "Found, not fixed" list:
  - centavo items asking for pesos;
  - clock-reading selections served as elapsed-time stems;
  - three silent fallbacks.
- The H4-0 "Found, not fixed" list: the pictograph fallback `category` default; seven silent defaults met while
  tightening (named in the H4-0 evidence); two copies of the number-to-words builder.
- The H4-0-R2 "Found, not fixed" list: the two escapes above; `_fraction_words`' digit fallback and "halfs";
  fmt_fraction_model's `model_names.get(model_type, "model")` mismatch; the silent `"+"` operation-symbol defaults;
  `num_to_words` past 10,000; two one-member answer domains (named in the H4-0-R2 evidence).
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
  authorized is attributed field by field (`validation_reports/phase2_hardening/h3r2_tools/fielddiff.py`).
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
- An upgrade proven only by observation (`"fill"`, `value:`) may have an unobserved alternative. Run
  `validation_reports/phase2_hardening/h3r2_tools/fill_audit.py`.
- `tests/slot_wide_check.py` excludes nothing but the known escapes. Read every line it prints.

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

- Measured in H4-0: regen+benchmark+frontend 44 s, corpus 64 min (230 mutations), shards 24-27 min each, run_all 40 min; 4 h 19 min in all.
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
