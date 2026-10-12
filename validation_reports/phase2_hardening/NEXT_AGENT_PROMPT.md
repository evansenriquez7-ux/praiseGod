# Task prompt: Phase 2 pipeline hardening under owner rulings 23–43 (Claude host)

**Rewritten 2026-10-13 after batch H4-0-R2 (ruling 42's type-only count is 0 on all 151 lcs; tree CERTIFIED).
This REPLACES every earlier version of this file.** `CLAUDE_AGENT_PROMPT.md`, `GPT_HANDOFF_PROMPT.md` and
`HANDOFF_PROMPT.md` beside it are history: their method notes (§7 heavy runs and the lock, §8 anchor one-liner, §9
traps, §11 not yours) are still correct and cited below; their state sections are stale.

Trust order: a command you executed > this file > `CLAUDE_AGENT_PROMPT.md` > the dated blocks in
`docs/phase2_hardening_completion_plan.md`.

---

## 0. Your task, in one paragraph

Build batch **H4**: the LLM **stem review gate** of owner ruling 24. Every lc is now at 0 type-only slots (ruling
42's precondition), so every lc's stems can be reviewed. H4 is a **new check**: a packet builder that enumerates each
lc's stem families from the slot record, a filed-verdict format, and a `run_all` stage that fails when an lc's
current stems are not covered by a fresh, valid, blind approval. You prove each of its failure paths with a
mutation caught by name, run the §8 re-proof chain once, and leave the tree CERTIFIED with this file's §0, §2 and §5
rewritten. **H4 has open design questions (§5.2): ask the owner before you build past them, and ask before you
dispatch any judge.** Do not start H6. Do not fix generator content.

**Goal of Phase 2 (ruling 23).** It hardens the **testing pipeline**, not the generators. It is done when every
check is proven by a mutation on the path it executes (Scaling Mandate 1–2), `run_all` exits 0 or 2 (integrity
green; ruling 27), every finding is named by lc, seed and owed build, and the tree is CERTIFIED. Content findings
are the generators' work queue (§6.4); you do not fix them unless the owner rules otherwise (as rulings 39–40 did).

**Terminology.** The harness calls `mat_g3_dp_q3_4` a "node"; `CLAUDE.md` calls it an **lc**. A node is the bundle
`mat_g3_dp_q3`. A **clause** is a fragment of one lc's competency text. A **stem family** (this file's term) is one
distinct recorded template an lc's renders reach. Do not rename code identifiers.

---

## 1. Read first (in this order; budget about 40 minutes)

1. `CLAUDE.md` (a symlink to `AGENTS.md`): the Scaling Mandate, Engineering Protocols, Content Rules, Definition of
   Done and **"If you are a judge"** (your judges will read it; ruling 29). Then `MEMORY.md`, especially:
   "Attester dispatch gotchas", "Dispatch subagents on Haiku", "Judgment reviews go stale", "Reviewer evidence must
   be lossless", "Duplicated rule copies disagree", "Allowlist checks drift silently", "Mutation must land where
   behaviour changes", "Proof admissible, not just detected", "CERTIFIED can hide a red unit test".
2. This file, completely.
3. **Owner rulings** in `docs/phase2_hardening_completion_plan.md`, verbatim: 19–22 (search "rulings recorded
   2026-10-07") and 23–43 (search "rulings recorded 2026-10-08"; 27–43 follow). Rulings 20, 21, 24, 26, 29, 41, 42
   and 43 are H4's core.
4. `validation_reports/HARDENING_EVIDENCE.md`, newest at the END: "H4-0-R2" and "H4-0" fully; then "H3-R2", "H5",
   "H3", "H2", "H1" (headings and NAMED LIMITS).
5. `docs/pgen_contract.md` rows §14 (all amendments and NAMED LIMITS 1–12), §15, §16, §5 (`validate_judgment`), §2L,
   the verdict row, and the rule above `_manifest.FINDING_CLASS`.
6. Code (§5.1 says what each gives H4): `backend/app/practice_gen/slots.py` (whole file);
   `validation/validate_slots.py` (`render_findings`, `collect_findings`); `validation/judgment_packets.py`;
   `validation/validate_judgment.py` (its docstring: why freshness, quote provenance, plurality and skeleton checks
   exist); `tests/file_reviews.py`, `tests/attester_packets.py`, `tests/attester_file.py` (docstrings);
   `validation/run_all.py` around the stage table (~line 670), the stage functions (~line 1105) and the stage list
   (~line 1204); `validation/_manifest.py` (`FINDING_CLASS`); one `Mutation(...)` in `tests/mutation_harness.py`
   (e.g. `slot_loosened_to_type_only`, ~line 5189).
7. `CLAUDE_AGENT_PROMPT.md` §7, §8, §9, §11.

---

## 2. State at handoff (2026-10-13, after H4-0-R2; re-measure before quoting)

```
HEAD                local main, NOT pushed (git status -sb: ahead of origin)
source              ea3c1600 (H4-0-R2); chain artifacts 75f15cc2; tree_state c26fd7fb; docs 2b976ce6
H-06 lock           RELEASED (5c0594fe); claim it before any work (§4 Phase 0)
tree_state          CERTIFIED (230 proofs, 6 shards, benchmark, frontend fresh; digest 8fd5dbe548788b49)
run_all             2026-10-13 on ea3c1600: EXIT 2; scheduled=21 completed=15 failed=6 crashed=0; INTEGRITY GREEN;
                    172/183 assertions proven by execution; finding_class_registry_complete 183 labels
  CONTENT           variant_not_exhibited_2L 420, attester_packet_refused_2L 61, judgment_reviews 752,
                    capability_contract 78, count_noun_singular_after_many_1J 423, slot_domain_escape_14 67,
                    selector_value_unexhibited_15 58, hint_sequence_unshown_15 6   (slot_domain_type_only_14 PASSES)
§14                 type_only 0 (151 of 151 lcs); escape 67; unaccounted 0. Wide (seeds 1-40 + every pinned
                    formatter): only 2 type-only site/slot pairs, both list-printing escapes. 61 unreasoned
                    `derived(` lines remain in source, 60 of them reached by nothing (NAMED LIMIT 11)
§15                 58 + 6; 1,351 of 1,351 selector matches decided by record
§1J                 indefinite_article_1J 0; count_noun_singular_after_many_1J 423
stem families       measured 2026-10-13 at the 20 student seeds, keyed (spine id or call site, template):
                    151 lcs; per lc min 5, median 18, max 59 (mat_g2_na_q3_1; mat_g2_na_q3_0 55); 2,867 (lc, family)
                    pairs; 955 distinct templates tree-wide. These include structural wrappers ("{answer}", a
                    join's "{p0}, {p1}") that a packet may collapse (§5.2 question 1)
unit suite          986 passed, 1 skipped (~11 min)
mutations           230; corpus 230/230, no INVALID
latest attestation  batch440 (next free prefix: batch441); §5 review records in validation_reports/judgment/
                    (24 node-group dirs); attestation records in validation_reports/attestation/
```

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

**Stop and ask** for any content judgment or design question that rulings 1–43 and MATATAG do not settle, and for
anything in "Not yours" (§7).

---

## 4. Phase 0: baseline and lock (always, before any edit)

1. `ps` grep empty; `df -h /System/Volumes/Data` shows space; `PYTHONPATH=. .venv/bin/python tests/tree_state.py`
   prints CERTIFIED; worktree clean. CERTIFIED does not cover `validation_reports/`, so also run
   `PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q -p no:cacheprovider` (expect 986 passed,
   1 skipped; ~11 min; run it in the background and read while it runs).
2. Claim H-06: in `validation_reports/phase2_hardening/hardening_status.json` edit ONLY its `owner` line with
   `sed` (`git diff --numstat` must read `1 1`), commit by name, then
   `PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin batch --session <yours> --note "H4: ..."`.
3. Re-measure, and explain any move before building:
   - `validate_slots`: `slot_domain_escape_14 (67)`, `slot_domain_type_only_14` PASS, NOTE `151 of 151`;
   - `validate_composition`: 58 + 6, with 1,351 of 1,351 decided;
   - `validate_language`: `indefinite_article_1J` PASS and 423 mirror findings;
   - the capability queue snippet below (`78 42 33 55` at H4-0-R2's Phase 0; ~2 min).
4. If you will touch any source: `PYTHONPATH=. .venv/bin/python -m tests.render_snapshot local_only/scratch/<batch>/before.jsonl`
   BEFORE the first edit, and keep `tests/slot_wide_check.py` (expect `TOTAL distinct 24 | renders that raised: 2`,
   the two `mat_g2_mg_q4_3` pinned-mcq refusals) and the §15 dump
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

### 5.1 What already exists for you to reuse (do not write a second copy of any of it)

| need | existing piece | what it gives you |
|---|---|---|
| the record of what an lc renders | `slots.capture()` + `validate_slots.render_findings` | every `Fill`: template, slots (value, domain), `sources` (provenance), `reasons`, `site`, `renderer_ref` (spine id); `Trace.derivations` (`derives`/`computes`) |
| learner-read fields | `validate_language._texts` | the §1J classification that §14 and §15 already share |
| seeds | `validate_slots.SEEDS` (1–20, student path) | the paths §14's count was proven on |
| a blind packet + skeleton written at dispatch time | `judgment_packets.build_packet`, `tests/file_reviews.py` (skeleton at dispatch, filer copies the evidence, dispatcher-assigned identity) | the pattern that stopped fabricated reviews: reuse its rules, not its per-sample content |
| opaque delivery, a key file the judge never sees, filing without retyping | `tests/attester_packets.py --packets/--key`, `tests/attester_file.py` (refuses unknown items, empty reasoning, uncited seeds, templated skeletons; `--supersedes` takes a FILE path) | the ruling-20 confirming-judge mechanics |
| anti-fabrication checks on a filed review | `validate_judgment.py`: freshness, quote provenance, reviewer plurality, skeleton clustering | the checks a stem verdict also needs (adapted to stems, not seeds) |
| a stage in `run_all` | the stage table (~line 670: `("slot_domains_14", 1, ("§14",), "...")`), a `_stage_<name>()` function (~line 1105) that adds its § to `executed_checks`, and the stage list (~line 1204) | where H4 plugs in |
| finding classes | `_manifest.FINDING_CLASS` (every label is CONTENT or INTEGRITY; `finding_class_registry_complete` fails on an unclassified one) and each module's `ASSERTIONS` tuple (counted by `assertion_coverage_8`) | how a new label is registered |
| contract keys | `run_all.CONTRACT_CHECKS`: every `§` token in `docs/pgen_contract.md`, prose included, must be a key | a new § number is registered there before the contract row uses it |
| mutations | `Mutation(name, asserts, description, edits={path: (old, new)}, command, expected_check, expect_output_contains, baseline_must_not_contain)` | the plant must land on the path the check executes; `--only <name>` runs one |

### 5.2 Design questions to settle with the owner FIRST (use AskUserQuestion; recommend an option for each)

Rulings 24, 26, 29 and 42 fix what H4 is for; they do not fix these, and each changes what you build:
1. **Family granularity.** Is a family (spine id or call site, template)? Do structural wrappers (`{answer}`, a
   join's `{p0}, {p1}`, `{text}` transforms) collapse into the family that prints them? (2,867 (lc, family) pairs
   raw; median 18 per lc, max 59.) Recommended: collapse wrappers whose every slot is `fill`; keep everything else.
2. **Which paths enumerate an lc.** The 20 student seeds only (what §14 proved), or also pinned formatters, other
   experiences and difficulty profiles (§14 NAMED LIMIT 1)? A family reached only off those paths goes unreviewed.
   Recommended: student seeds plus every advertised formatter, with the remaining gap named as a limit.
3. **Freshness key.** Ruling 24 says the hash of templates + domains + provenance. Domains include runtime `E`/`R`
   objects whose members vary per render: hash the domain's members, or its kind and basis? Recommended: kind +
   basis + members for static banks; kind + basis + bounds for runtime ones; prove both directions by mutation.
4. **Verdict shape and quorum.** Per family or per lc? Which verdicts need ruling 20's confirming judge (a FAIL
   that creates a finding? a PASS that clears an lc?) Recommended: per-family verdicts plus one overall per lc;
   a confirming judge on every non-PASS and on a sample of PASS.
5. **What a FAIL becomes.** A content finding by lc and family (exit 2; owed: fix the stem or its domain), or
   integrity? Ruling 32 classes record defects as content, and a missing or stale review is presumably content too
   (as `judgment_reviews` is), but ask.
6. **Clause coverage (ruling 26).** Does the stem judge also rule "can these stems produce every clause", and how
   does that interact with §6F attestations and §2L? Recommended: the judge rules it per clause; the existing
   records stay until H6.
7. **Judge model and budget.** Memory says fan-out on Haiku (`model: "haiku"`), about 6 concurrent; 151 packets
   plus confirmers. Confirm before the first dispatch.

### 5.3 What to build (after the answers), in slices under one chain (ruling 37)

1. **Packet builder** (e.g. `validation/stem_packets.py`): from the record, per lc, every family with its template
   text; each slot's domain rendered for a reader (the members of an `E`, the bounds and basis of an `R`, the list an
   `enum:`/`bank:` names, which fill a `fill` slot nests); the provenance claims (`src`, `_src`, `derives`,
   `computes`) and `arithmetic` reasons; and the lc's competency text, clauses and vocabulary gates. No node id and
   no source paths in the blind half (opaque item ids; a key file the judge never sees).
2. **Freshness hash** per family and per lc, computed from the live record, never from the filed packet.
3. **Filer** that copies the packet's evidence, takes only verdicts and reasoning from the judge, assigns the
   dispatcher's identity, and refuses everything `attester_file.py` refuses.
4. **Validator stage** (a new §, registered in `CONTRACT_CHECKS`, `FINDING_CLASS`, its module's `ASSERTIONS`, the
   stage table and the stage list): for every lc, every current family has a valid, fresh, non-superseded verdict.
   FAILs are reported by lc, family, a seed that reaches it, and owed build.
5. **Mutations, each caught by name on a real lc** (run `--only` until each is DETECTED, then the chain):
   - a stem edit with no new review is stale (template change → hash change);
   - a domain loosened with no new review is stale (e.g. an `E` member added);
   - a packet missing a reachable family is caught (drop one family from the builder);
   - a filed record whose verdict is removed or edited is caught;
   - a provenance claim changed with no new review is stale.
   Proofs must not depend on an LLM: build fixture records by hand under a fixture directory that the proof lists in
   `mutation_proof.INPUT_FILES` (memory: "Proof admissible, not just detected").
6. **Contract row and NAMED LIMITS** in `docs/pgen_contract.md` (at least: the paths enumerated; a verdict is a
   reading, not a proof; families reached only by unvisited paths; the judge's model and noise rate under ruling 20).
7. **Only then, with the owner's go-ahead, the dispatch campaign** (batch441 onward): filed through the filer,
   confirmers per the answer to question 4, disputes per ruling 21, and every reply audited against the packet it
   was shown (Haiku quotes badly: an unprinted seed or an elided quote means set the reply aside and re-dispatch).

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
