# Task prompt: Phase 2 pipeline hardening under owner rulings 23–29 (Claude host)

**Rewritten 2026-10-08 after owner rulings 23–26 redefined Phase 2; rulings 27–29 (2026-10-09) settled its open design questions. This REPLACES every earlier version of
this file.** `CLAUDE_AGENT_PROMPT.md`, `GPT_HANDOFF_PROMPT.md` and `HANDOFF_PROMPT.md` beside it are history.
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

Content findings (the 78 CONTRADICTED, 752 judgment, and §2L's 420 variant + 61 packet-refusal findings) are the
**generators' work queue**.
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
3. **Owner rulings 23–29** in `docs/phase2_hardening_completion_plan.md`, verbatim (search "rulings recorded
   2026-10-08"; 27–29 follow them). Also read rulings 1, 9, 12–16 and 19–22 above them. They still govern what content must
   satisfy.
4. `validation_reports/HARDENING_EVIDENCE.md`, newest entries first:
   - "Declared variants that are never exhibited (§2I blind spot), and owner rulings 23–26";
   - "Phase 3: re-attestation of the queue under the ruled instrument";
   - "Phase 2a landed: the ruling-22 attester gate".
5. `docs/pgen_contract.md` rows for:
   - §2I (line ~28);
   - §1J `count_noun_agreement_1J` (its BLIND SPOTS);
   - the judgment packet allocation (the "126 no-op" MEASURED-NOT-GATED note);
   - `clause_enumeration_22` (its 7 NAMED LIMITS);
   - `stage_ledger_complete`.
6. `CLAUDE_AGENT_PROMPT.md` §7 (heavy runs, the lock), §8 (anchor one-liner), §9 (traps) and §11 (not yours).

---

## 1. State at handoff (2026-10-09, after H1; re-measure before quoting)

```
HEAD                origin/main at the H-06 release commit after H1 (see git log); worktree clean
source              3449378b (H1: f7723703 + the refusal-naming fix); chain artifacts b2550cbb
H-06 lock           RELEASED; claim it (owner line only, numstat 1 1) before any work
tree_state          CERTIFIED, digest 4d314664a4ff03b4 (211 proofs, 6 shards, benchmark, frontend fresh)
run_all             2026-10-09 on 3449378b: EXIT 1, scheduled=18 completed=15 failed=3 crashed=0
                      assertion_coverage_8  the 3 §6F mutations INVALID (their baseline is red)
                      judgment_reviews_5    752   (content queue; retired as a gate by ruling 25, see H6)
                      capability_phase2     78 CONTRADICTED over 42 lcs (content queue; see H6)
                      variant_exhibit_2L    PASS (report-only until H2); prints the §2L queue below
queue snippet (§4)  78 42 33 55  (measured 2026-10-09)
§2L (H1, landed)    973 declared pairs at 8 seeds: 428 recorded, 125 exhibited by render only, 420 not exhibited
                    (A clamp 1, B substituted 90, D no-op/alias 291, E default-only 38, R 0);
                    151 attester packets built, 61 refusals = 20 needs_instrumentation lcs (node-wide)
                    + 41 capabilities over 28 lcs (provider_variant_stratification_6F)
unit suite          1049 passed, 1 skipped (fast suite ~24 min)
mutations           211; corpus 208/211, misses = the 3 §6F INVALIDs only
latest attestation  batch440 (next free prefix: batch441)
```

Corrections to the previous version of this file, measured 2026-10-09:
- It said HEAD was "the commit that records rulings 23-26". That commit did not exist; the rulings, the new
  Definition of Done and the 973/545 entry were uncommitted. H1 committed them as `0c8199b3`.
- Its "9" needs_instrumentation and "8" stratification-refused counts were inside the CONTRADICTED queue only.
  Tree-wide the counts are 20 lcs and 28 lcs (41 capabilities).
- §2's 545 split (277 / 116 / 113 / 38 / 1) was the 2026-10-08 prototype. Its B=116 over-reported: 26 of those
  record the value in another encoding (`scale_10` as `10`, `square_cm` as `'sq cm'`). §2L's classes above
  replace it. The census still counts 973 variant candidates. The §4 measure script printed `not exhibited 545` at H1's
  Phase 0; that script counts "not recorded", and 125 of those 545 change the render, so §2L counts them as exhibited.

The three §6F INVALIDs exist because a content queue currently sits inside a gate's baseline. Under ruling 23
that is a pipeline defect: a check cannot be proven while its baseline is red (Mandate 5). The run_all split
(H2) must give each content check a way to be proven while content debt exists. One way is to plant the mutation
on an lc whose baseline is clean and require it to be caught by name.

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

Rulings 23–29 are recorded verbatim in the plan doc. In short:
- 23: Phase 2 hardens the pipeline, not the generators.
- 24: LLM judges review stems plus field domains; deterministic checks do the rest.
- 25: the per-sample gates are retired once replaced; records are kept.
- 26: clause coverage is ruled from stems, then proven by an exhibit check.
- 27: `run_all` exits 0 / 2 / 1.
- 28: structured slots.
- 29: judges see `CLAUDE.md` by design.

Rulings 19–22 stay in force for any attestation still filed under the old gates before H6 retires them.
Every design choice the earlier draft left to the owner is now ruled. **Stop and ask** for:
- any content judgment that MATATAG and rulings 1–29 do not settle;
- any design question these rulings do not answer;
- anything in "Not yours" (§5).

---

## 4. Plan: pipeline batches H1–H6

Each batch is one `batch` intent and one re-proof chain (§6). Inside a batch, use a dev loop: focused unit
tests, the validator's own module, and `tests/mutation_harness.py --only <new mutations>`. Run the chain once,
at the end. Every new check needs four things:
- a contract row in `docs/pgen_contract.md`, whose § token is a `CONTRACT_CHECKS` key (memory: contract doc
  section signs are scanned);
- a mutation in `tests/mutation_harness.py` that is caught by name and is Phase-1 admissible;
- its NAMED LIMITS, written in the docstring, the contract row and the evidence log;
- no hard-coded lc lists, grades or thresholds tuned to today's tree (Mandate 4).

**Content-finding checks report; they do not block integrity.** Until H2 lands, a new check whose baseline is
red must not be added to a stage that turns `run_all` red. Land H2 first, or land the check in report-only form
with its mutation proven on a clean lc.

### Phase 0: baseline and lock (always, about 30 min)

1. **Heavy-run check** (`CLAUDE_AGENT_PROMPT.md` §7). The `ps` grep must be empty, and `tests/tree_state.py` must
   print `CERTIFIED` with a clean worktree. Otherwise stop and find out why.
2. **Claim H-06.** Edit only its `owner` line; `git diff --numstat
   validation_reports/phase2_hardening/hardening_status.json` must read `1 1`. Commit. Then open the intent:
   `PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin batch --session <yours> --note "<batch id>"`.
3. **Re-measure.** Run both commands below and expect `78 42 33 55` and `candidates 973 not exhibited 545`.
   If either moved, explain why before building.

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

The variant-exhibit measurement is quoted in full in the evidence entry "Declared variants that are never
exhibited". It takes about 55 s.

### H1: variant exhibit check (ruling 26; Mandate 3, so it comes first) -- DONE 2026-10-09

**Landed** as §2L (`validate_exhibit.py`, stage `variant_exhibit_2L`, contract row §2L, evidence entry
"H1: §2L declared variants must reach the render"). Criterion (b) is "differs from EVERY sibling", not any
(measured: "any" certifies 8 recorded substitutions). Report-only until H2: H2 must route `variant_not_exhibited_2L`
and `attester_packet_refused_2L` to exit 2. Also landed: `stage_failure_reaches_verdict` (run_all's verdict
reads every failed stage from the ledger; `dangling_reference_1M` had been left out). Its NAMED LIMIT is H2's:
a stage that prints FAIL but returns True (as §2L does now) is not seen. The text below is the original brief.

**Build** a validator that proves every declared `(lc, axis, value)` from
`judgment_packets._variant_coverage_candidates` reaches the render. Requesting the value at a seed must do one of
two things:
- (a) record the value in `_provider_variant_evidence` (matched by `tests.attester_packets._matching_variant_evidence`);
- (b) change the rendered problem against the same seed under a sibling value (question text, answer, visual
  type, visual params).

**Then:**
- Report non-exhibited pairs as content findings, by class: substituted (B), unrecorded no-op (D), single value
  equal to the default (E), and clamp (A). The class names what the generator agent must do.
- Fold in the attester-packet-build check that Phase 3 owed: build every lc's attester packet, so a
  `provider_variant_stratification_6F` refusal surfaces as a named finding before any dispatch.
- Mutation: undeclare-proof. Make one DNA ignore an axis it currently honours, on an lc whose baseline exhibits
  it, and require the check to catch it by name.
- Record in §2I's contract row that §2I proves producibility only, and point to the new row.

**Not yours:** making the 545 exhibit. Each one is a generator fix under Content Rule 4: build it when the lc's
competency names it, undeclare it otherwise, with the clause cited. Those fixes go in the content queue.

**NAMED LIMIT to keep:** class C shows that an unrecorded variant can still be honoured. The check must accept
(b), or it will report false findings.

### H2: split `run_all` (ruling 23)

- `run_all` classifies every stage result as one of two verdicts:
  - **integrity**: every stage ran (`stage_ledger_complete`), every mutation was DETECTED or properly proven,
    the tree is fresh, and no harness crash;
  - **content**: every finding by lc, seed and owed build.
- Exit codes (ruling 27): **1** if integrity fails, whatever the content; else **2** if any content finding
  exists; else **0**. One command, no flag. Every stage must be classified integrity or content in both
  directions, so a new stage that is not classified is an integrity failure (memory: allowlist checks drift
  silently).
- Every content-guarding mutation must become provable while content debt exists. That ends the "3 §6F INVALID
  by construction" state. Re-anchor each INVALID mutation onto an lc with a clean baseline, and prove it
  DETECTED.
- `CLAUDE.md`'s Definition of Done already states the three codes. When the split lands, delete its "Until the
  exit-code split lands" sentence, and update the `stage_ledger_complete` and `phase1_hermetic` contract rows,
  **in the same commit** (Protocol 7).
- Mutations, each of which must be caught:
  - a content finding that leaks into the integrity verdict (exit 1 instead of 2);
  - an integrity failure hidden in the content report (exit 2 instead of 1);
  - an unclassified stage.

### H3: field domains and the domain check (ruling 24, deterministic half)

- Every learner-facing slot in a stem gets a **declared domain**. A slot is a value interpolated into a spine,
  a DNA f-string or a formatter wrapper. Its domain is the set of nouns, names, units, the number range and the
  enumerations it can take at that lc's bounds.
- **Derive** the domains from the generator's own sources: imported lists, axis bounds and
  `cumulative_vocab`. **Never restate them** (memory: duplicated rule copies disagree).
- **Structured slots (ruling 28).** Each DNA, spine and text-adding formatter emits its template together with a
  structured slots record: slot name, value, domain id. Never infer a slot from learner-facing text. Emitting
  slots is instrumentation, not content repair: it must not change any rendered byte. Prove that by diffing the
  renders before and after over the benchmark seeds.
- A deterministic check renders the lc and proves:
  - (a) the learner-facing text equals the template filled with the slot values;
  - (b) every slot value lies inside its declared domain.

  A slot that is not classified, or text not accounted for by the template, is a named finding. Classify in
  both directions (memory: allowlist checks drift silently).
- Prototype on 3 lcs from different DNAs, and measure how much rewriting a formatter does after the template.
  Then roll out. Text added by a formatter after the template is filled is itself a template with slots.
- Mutation: widen one domain source so a value escapes, and it must be caught. Also add an unclassified slot,
  which must be caught.

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

### H5: composition checks a stem review cannot see

These are known blind spots, each with an instance today that proves the check.
- **Ruling-22 blind spot.** A selector proves the generator CHOSE a sibling, not that the rendered item still
  EXHIBITS it. Instance: `mat_g1_na_q2_1` `read_mcq` NumberLine/EmojiPictorial items drop the skip-count
  sequence, while the hints still describe it. Build a check that the structured value the selector reads
  survives into the rendered payload.
- **Hint/stem agreement.** A hint must describe the problem actually rendered, after the formatter has
  rewrapped it.
- **`count_noun_agreement_1J` limit 1** (singular-after-many, measured but not gated). Instance:
  `mat_g3_na_q2_3` seed 500 `3622 cat toy`. Close it, or narrow it with a mutation that plants a
  singular-after-many and is caught. Do this **before** anyone fixes the instance, while the instance still
  proves the gate.

Each of these reports content findings. Do not fix the instances.

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
- the 9 `needs_instrumentation` lcs;
- the 8 refused lcs;
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
- **Stop** at any content judgment or design question that MATATAG and rulings 1–29 do not settle.

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

- Any edit made mid-chain stales the whole chain. Stop, commit, and restart from the benchmark.
- Until H2 lands, expect exactly 3 INVALID. Any other INVALID means a red baseline: run that mutation's own
  command and find out why. After H2, expect none.
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
number from a command run in that session and does not touch generator content. **H1 is done (2026-10-09); H2 is the next batch.**
