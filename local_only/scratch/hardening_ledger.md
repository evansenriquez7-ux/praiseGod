# PGEN Hardening Ledger

One entry per tick. The **Next tick should** line is the handoff to a cold future tick.

---

## 2026-08-12 — Tick A

- **Census before:** PASS=151 CONCERN=0 FAIL=0 — but every one of them fabricated. Largest rationale
  skeleton cluster = 151/151 nodes; 115 reviews quoted a stem absent from their own `samples_reviewed`;
  all 151 filed under a single `reviewed_by`.
- **Tick 0 did not fire:** `run_all` was **green (EXIT_CODE=0)** at tick start. The stage-1
  `comparing_ordering` / `area` failures described as seed state in the loop prompt were already fixed by
  commit `b6473c1`; the working tree was clean, not ~193 uncommitted files. The loop prompt's §3 Tick 0
  seed-state block is now stale — verified, not trusted, per its own instruction.
- **Unit of work:** Hardened `validate_judgment.py` with the three anti-template checks Tick A specifies,
  proved both directions with a new unit test file, documented the rules in `docs/pgen_judgment.md`, and
  deleted all 151 rejected reviews.
- **Root cause (of the fabrication surviving the gate):** the freshness check re-renders
  `samples_reviewed` and **never reads the rationale**. A template rationale stapled onto a
  freshly-rendered samples block therefore passed cleanly, and the verbatim-reuse check
  (`validate_judgment.py` exact `==`) passed too because substituting the node ID makes no two
  rationales byte-identical.
- **Files touched:**
  - `backend/app/practice_gen/validation/validate_judgment.py` — +3 checks (quote provenance,
    skeleton clustering, reviewer plurality); thresholds are named module constants.
  - `tests/unit/test_judgment_antitemplate.py` — **new**, 10 tests, each asserting both directions.
  - `docs/pgen_judgment.md` — new "Anti-template checks" section (Protocol 7: enforcement + contract
    move together).
  - `validation_reports/judgment/**` — 151 files deleted (recoverable from `567848a`).
- **Verification:**
  - `validate_judgment` against the fabricated set → `228 problem(s) found` = 182 quote-provenance
    + 45 skeleton-cluster + 1 reviewer-plurality. Rejection set derived from data (not message text):
    quote 91 nodes, skeleton 151, reviewer 151 → **union 151, survivors 0**.
  - `pytest tests/unit/test_judgment_antitemplate.py -q` → `10 passed in 0.19s`.
  - `run_all` → `EXIT_CODE=1`, red **only** at 6/6 judgment. Stages 1–5 green, matrix 151/151,
    0 failures, all ten contract checks executing, both two-direction contract checks PASS.
- **Census after:** PASS=0 CONCERN=0 FAIL=0 — no reviews on disk. **This red is deliberate and
  documented.** An honest red beats a fabricated green.
- **Commit:** `6d8385f` fix(judgment): harden gate against template reviews; delete 151 fabricated
  reviews. (A pre-commit hook also rebuilt and staged `graphify-out/` into this commit — expected,
  it happens on every commit in this repo.)

### Findings parked for a later tick (NOT this tick's scope)

1. **Two pre-existing pytest failures, unrelated to this tick.**
   `tests/unit/test_checklist_audit.py::test_full_audit_zero_violations` and
   `tests/unit/test_parallel_audit.py::test_parallel_audit_matches_serial` both die on
   `ImportError: cannot import name '_FORMATTER_ROUTES' from 'backend.app.practice_gen.adapter'`
   (`tests/exhaustive_checklist_auditor.py:1272`). `_FORMATTER_ROUTES` does not exist in `adapter.py`
   at `567848a` — the auditor imports a symbol the adapter no longer exports. `run_all` does not run
   these files, which is why it stayed green over a broken auditor. Full suite: **292 passed, 2 failed**.
2. **`run_all`'s 6/6 line under-reports an empty directory.** With `validation_reports/judgment/`
   absent, the gate short-circuits to a single "directory does not exist" error rather than naming all
   151 missing nodes. Loud and exit-1, so not urgent, but "1 problem(s)" understates 151 missing reviews
   to a cold reader. Pre-existing code path, not introduced here.

- **Next tick should:** run **Tick B** — nodes lack reviews. Build stratified packets with
  `judgment_packets.py`, dispatch blind reviewer subagents in batches of **≤ 25 nodes** (the new
  `_MAX_NODES_PER_REVIEWER` quota makes this mandatory, not advisory — each batch MUST write its own
  distinct `reviewed_by` string or the gate rejects the batch). Aim for 2–3 batches in the tick, then
  the adversarial evaluator pass into `validation_reports/judgment_audit/<batch>.json`. Expect genuine
  verdicts to include CONCERN/FAIL — that is the point, and it feeds Tick C. Do **not** re-review from
  the deleted files; they are void. Reviewers must quote real stems from their own packet, since quote
  provenance is now a hard FAIL.

---

## 2026-08-12 — Tick B (first review batch)

- **Census before:** PASS=0 CONCERN=0 FAIL=0 — no reviews on disk (all 151 deleted in `6d8385f`).
  Tick 0 did not fire; Tick A did not fire (gate hardened last tick). Tick B is correct.
- **Unit of work:** reviewed the first **50 of 151** nodes. Two blind reviewer batches of 25 in
  parallel (B1, B2), each audited by a separate adversarial evaluator, plus a third reviewer (B3)
  for the nodes the evaluators voided.
- **Root cause:** n/a — this tick produces evidence, it does not fix a generator.
- **Files touched:** 50 new reviews under `validation_reports/judgment/`; `judgment_audit/batch_B1.json`,
  `batch_B2.json`, `batch_B1_fixer_correction.md`. No pipeline code touched.
- **Verification:**
  - census over the 50: `verdicts: {'FAIL': 11, 'CONCERN': 20, 'PASS': 19}`,
    **quote-provenance failures: 0**, **largest skeleton cluster: 1**, 3 reviewer identities
    (25 / 23 / 2, all within the 25-node quota). Compare the deleted set: cluster 151, 115 phantom
    quotes, 1 reviewer.
  - `run_all` → `EXIT_CODE=1`, red **only** at 6/6 (`192 problem(s)` = 101 unreviewed nodes + genuine
    non-PASS verdicts). Stages 1–5 green; matrix 151/151, 0 failures; both contract checks PASS.
  - verdict movement vs `a4bba70` over these 50: CONCERN→PASS 12, FAIL→CONCERN 11, CONCERN→CONCERN 8,
    CONCERN→FAIL 6, FAIL→FAIL 5, FAIL→PASS 4, PASS→PASS 3, PASS→CONCERN 1. **Movement runs both
    directions**, which is itself evidence of independent judgment rather than a rubber stamp.
- **Census after:** PASS=19 CONCERN=20 FAIL=11 over 50 reviewed; 101 nodes still unreviewed.
- **Commit:** `f04b2ac` review(judgment): file 50 genuine blind reviews for batches B1–B3 with
  adversarial audits.

### Evaluator findings, and one I rejected

- B1 evaluator: 0% disagreement on its 5-node independent re-judgment; 1 void.
- B2 evaluator: 20% disagreement (boundary, 1 of 5); 2 voids — `mat_g1_na_q2_3` (rationale listed
  sampled values that were not in the packet; it dropped seed 500's real value 50 and invented a
  duplicate 40) and `mat_g1_na_q3_5` (claimed read_mcq samples carry the expanded-form frame; seeds
  55 and 500 are bare `How many items are left?`). **Both voids verified true against the packet**
  and both nodes re-reviewed blind by B3 → both CONCERN, with accurate evidence.
- **Void REJECTED:** B1 voided `mat_g1_na_q1_8` claiming its seed 45 renders `0 + 2 = ___`. Verified:
  seed 45 is `1 + 2 = ___`, and no sample in that node contains the character `0` at all. The
  reviewer's FAIL was earned. Review kept, node NOT re-reviewed. Full enumeration in
  `validation_reports/judgment_audit/batch_B1_fixer_correction.md`.
- **Lesson for future ticks:** an evaluator's void is a *claim*, not a verdict. Verify it against the
  packet before deleting a review and re-dispatching — this tick, 1 of 3 voids was itself fabricated.

### Findings parked (NOT this tick's scope)

3. **Packets carry no vocab metadata.** `build_packet` emits competency_text/grade/quarter/samples but
   no `NOT_YET_KNOWN` / `cumulative_vocab`, so reviewers judge vocabulary gating from grade/quarter and
   their own K-12 expertise rather than from KG ground truth (CLAUDE.md content rule 1 says check it,
   don't guess). Consider adding it to `judgment_packets.build_packet`.
4. **Possible answer leak seen in passing**, `mat_g1_na_q2_3` seed 50:
   `Write 20 as tens and ones, for example 45 = 40 + 5. The answer is 60 + ...` — stem states an answer,
   and 60 does not decompose 20. Not chased this tick; belongs to Tick C.
5. **B2 evaluator's standing concern:** the two defects it found are the same species — a
   coverage/format claim quietly misdescribing which samples carry a required feature. It recommends a
   second pass over B2's other 23 nodes before fully trusting them. Not done this tick.
6. (Carried from Tick A) two pre-existing pytest failures on `_FORMATTER_ROUTES`; `run_all`'s 6/6 line
   under-reports an absent judgment directory.

- **Next tick should:** run **Tick B again** for the next 50 nodes — batches B4/B5 covering
  `mat_g2_mg_q1_1` onward through the g2 range (101 remain: g2 mg/na and all of g3). Reuse this tick's
  reviewer and evaluator prompts verbatim; they produced structurally clean, genuinely varied output.
  Keep batches ≤ 25 with a distinct `reviewed_by` per batch. Verify every evaluator void against the
  packet before acting on it. Once all 151 are reviewed, switch to **Tick C** and cluster the
  CONCERN/FAIL findings by root cause — the g1 dp/mg findings already cluster hard around
  "competency's second half never generated" (`mat_g2_dp_q3_0` vice-versa direction,
  `mat_g2_dp_q3_1` tabular half, `mat_g1_na_q1_8` identity property), which looks like one registry
  binding cause, not three content bugs.

---

## 2026-08-12 — Tick B (batch B4) — *preceded by one aborted tick*

- **Aborted tick, no state lost.** The prior tick dispatched B4 **and** B5 in parallel and was killed by
  the session usage limit before either reviewer wrote a file. Verified on restart: working tree clean at
  `f04b2ac`, 50 reviews on disk, 0 unparseable, census unchanged. **Nothing to repair.** Lesson applied
  immediately: **one batch of 25 per tick, not two.** Two 25-node reviewers plus two evaluators does not
  fit the budget.
- **Census before:** PASS=19 CONCERN=20 FAIL=11 over 50 reviewed; 101 unreviewed. Tick 0 no (run_all red
  only at 6/6), Tick A no (cluster 1, 0 phantom quotes, 3 reviewers). Tick B fires.
- **Unit of work:** batch **B4** — nodes 51–75 (`mat_g2_mg_q1_1` … `mat_g2_na_q2_0`), one blind reviewer
  plus one adversarial evaluator.
- **Root cause:** n/a — evidence-producing tick.
- **Files touched:** 25 new reviews under `validation_reports/judgment/`; `judgment_audit/batch_B4.json`.
  No pipeline code.
- **Verification:**
  - B4 verdicts: 11 PASS / 6 CONCERN / 8 FAIL. Reviewer self-reported 0 structural errors after fixing
    10 quote-provenance violations it had introduced — **the hardened gate caught them before filing**,
    which is the check working as designed.
  - census over all 75: `{'FAIL': 19, 'CONCERN': 26, 'PASS': 30}`, **largest skeleton cluster 2**
    (threshold 3), **quote-provenance failures 0**, 4 reviewer identities (25/25/23/2, all ≤ quota).
  - B4 evaluator: **0 voided**, **0% disagreement** on 5-node independent re-judgment, batch reliable.
    It recounted every numeric coverage claim rather than trusting it.
  - `run_all` → `EXIT_CODE=1`, red **only** at 6/6 (`203 problem(s)`). All 6 stages ran; matrix 151/151,
    0 failures; both contract checks PASS.
- **Census after:** PASS=30 CONCERN=26 FAIL=19 over 75 reviewed; **76 unreviewed**.
- **Commit:** `9e86afa` review(judgment): file 25 genuine blind reviews for batch B4 with adversarial audit.

### The Tick C cluster is now identified — verified, not inferred

`mat_g2_na_q1_10` competency: *"Illustrate and apply the following properties of addition using sums up
to 1000: the sum of zero and any number…, changing the order of the addends…, changing the grouping…"*
`mat_g2_na_q1_9` competency: *"Add numbers with sums up to 1000, with or without regrouping."*

Verified directly from the packet: **their sample lists are byte-for-byte identical across all 19
stratified seeds** (`IDENTICAL sample lists? True`; 19 shared stems, 0 unique to either). The properties
node serves plain addition facts — identity, commutativity, and associativity are never illustrated.

This is the **same shape as `mat_g1_na_q1_8`** (B1, FAIL): G1 properties-of-addition, 18 samples, not one
using 0 as an addend, only seed 613 (`Is 1 + 2 the same as 2 + 1?`) showing commutativity. Two grades,
one defect — a properties-of-addition node is not bound to a properties-specific generator and falls
through to the plain `addition` DNA. That is precisely the recurring cause named in the loop prompt §1
rule 5 (`registry.py`'s `_parse_competency_bounds` never binding a DNA's internal sub-concept, so a
default cascade governs instead). **Do not fix it node-by-node.**

Related "second half of the competency never generated" findings, likely the same or an adjacent cause:
`mat_g2_mg_q2_1` (distance-between-locations absent), `mat_g2_mg_q2_0`/`_2` (meters absent),
`mat_g2_mg_q4_2` (days/timetables absent), `mat_g2_na_q2_0` (centavo coins absent),
`mat_g2_dp_q3_0` (vice-versa direction absent), `mat_g2_dp_q3_1` (tabular half absent),
`mat_g1_mg_q1_2` ("draw" half absent), `mat_g1_na_q3_7` (construction half absent).
Worst single finding in B4: `mat_g2_mg_q4_4` — 10 of 16 samples are length-measurement items with
nothing to do with perimeter (evaluator recounted and confirmed the exact seed list).

### Findings parked

7. Placeholder scan across all 5 packets built so far: exactly **one** literal unfilled placeholder in
   rendered content — `mat_g1_mg_q2_2` seed 607, `An object measures 2 non_standard.` Not a cluster.

- **Next tick should:** **one** batch of 25 (`B5`: `mat_g2_na_q2_1` … `mat_g2_na_q4_5`) — its packet is
  already built at `scratchpad/packet_batch5.json`, reusable only while the pipeline is unchanged; if any
  generator commit lands first, rebuild it. Then the B5 evaluator. That leaves 51 (all g3) for two more
  ticks. **Alternatively, switch to Tick C now** and fix the properties-of-addition binding above — it is
  root-caused, spans ≥2 confirmed nodes, and Tick C outranks Tick B in the §3 trigger order once honest
  FAIL verdicts exist. Recommend Tick C next: 19 FAILs are already banked, and fixing a binding invalidates
  the reviews of every node it touches, so reviewing more nodes first risks re-work.

---

## 2026-08-12 — Tick B (batch B5) — 9 of 25 voided

- **Census before:** PASS=30 CONCERN=26 FAIL=19 over 75 reviewed; 76 unreviewed. Tick 0 no, Tick A no
  (cluster 2, 0 quote failures). **Tick B fires** — §3 says evaluate triggers in order and take the
  first that fires, and Tick B is listed above Tick C. My previous entry recommended jumping to Tick C;
  the protocol's ordering wins. That tension is still live — see "Next tick should".
- **Unit of work:** batch **B5** (`mat_g2_na_q2_1` … `mat_g2_na_q4_5`), one blind reviewer + one
  adversarial evaluator. Packet was the one prebuilt in the aborted tick; confirmed still valid because
  no pipeline code changed between (`git diff f04b2ac..HEAD -- backend/` empty).
- **Root cause:** n/a — evidence-producing tick.
- **Files touched:** 16 new reviews; `judgment_audit/batch_B5.json`. 9 reviews written then **deleted**
  as voided. No pipeline code.
- **Verification:**
  - B5 as filed: 9 PASS / 8 CONCERN / 8 FAIL. **The reviewer miscounted its own totals** (reported
    10/8/7). Disk is authoritative; always recount from disk, never from an agent's summary.
  - Evaluator: **9 of 25 void (36%)**, `batch_reliable: false`. Disagreement on independent
    re-judgment: **0/5 (0%)** — including on two nodes it voided. **Verdict directions sound, supporting
    evidence unreliable.** That is the precise failure profile to expect from here on.
  - I verified **4 of the 9 voids** directly against the packet before acting. All 4 stand. But **two of
    the evaluator's own counter-figures were themselves wrong** (gave q2_8's max as 88 when it is 81;
    called the q4_2/q4_5 rationales "word-for-word identical" when they are not — the gate's verbatim
    check would have caught that anyway). Voids stand on packet evidence, not on evaluator arithmetic.
  - census after deletion (91 reviews): `{'FAIL': 22, 'CONCERN': 32, 'PASS': 37}`, cluster 2,
    quote failures 0, 5 reviewers.
  - `run_all` → `EXIT_CODE=1`, `211 problem(s)` at 6/6, **0 non-judgment FAIL lines**, 6 stages ran,
    matrix 151/151 with 0 failures, both contract checks PASS.
- **Census after:** PASS=37 CONCERN=32 FAIL=22 over **91 reviewed**; **60 unreviewed** (51 never
  reviewed + the 9 voided returned to the pool).
- **Commit:** `d50748d` review(judgment): file 16 surviving B5 reviews; void 9 for false evidentiary claims.

### Voided nodes — back in the unreviewed pool, need a fresh reviewer
`mat_g2_na_q2_1`, `q2_3`, `q2_5`, `q2_8`, `q3_0`, `q3_1`, `q3_3`, `q4_2`, `q4_5`.
All 9 for check-1 (rationale states counts/spans/"all-every" claims false of its own packet), none for a
wrong verdict direction.

### Tick C cluster — now three confirmed root causes, all verified from packets myself

1. **Sibling duplication.** `mat_g2_na_q1_9` ≡ `q1_10` (19/19 identical) and `mat_g2_na_q3_0` ≡ `q3_1`
   (11/11 identical) — adjacent nodes with *different* competencies rendering byte-identical samples.
   Same shape as `mat_g1_na_q1_8`. A sub-concept is not bound and a default cascade governs.
2. **Fraction ordering routed to whole numbers.** `mat_g2_na_q4_2` ("Order unit fractions…") and
   `mat_g2_na_q4_5` ("Order similar fractions…") emit only whole-number sorts — `495, 231, 502`, up to
   `834` — with **zero fractions in any ordering task**. This is the cost of the known harness §1E
   fraction-sort blind spot (`validate_matrix`'s ordering check uses bare `sorted()`, wrong for `"N/D"`
   strings). Per that note: **do not weaken the check — fix the routing.**
3. **"Second half of the competency never generated"** — the broad family: `mat_g2_mg_q2_1`,
   `mat_g2_mg_q2_0/_2`, `mat_g2_mg_q4_2`, `mat_g2_na_q2_0`, `mat_g2_dp_q3_0/_1`, `mat_g1_mg_q1_2`,
   `mat_g1_na_q3_7`, plus B5's `q2_7` and `q4_0`/`q4_3` (named denominators never appear).

### Findings parked
8. **Evaluator arithmetic is not trustworthy either.** Both reviewer and evaluator have now produced
   false numeric claims. Any count that drives a decision must be recomputed by the Fixer with a script.
   Consider adding a mechanical check: flag rationales asserting "all/every/only N of M" and recount.

- **Next tick should:** **switch to Tick C.** 22 honest FAILs and 32 CONCERNs are banked, three root
  causes are identified and packet-verified, and Tick B has now cost five ticks with re-work appearing
  (9 voids). Start with cluster 1 (sibling duplication) — it is the most mechanical: Graphify the
  registry → DNA → adapter path for `mat_g2_na_q1_10` / `q3_1`, find why the sub-concept never binds,
  make the DNA `raise` naming concept/grade/seed instead of cascading, then re-render both pairs and
  confirm the sample lists diverge. Fixing it invalidates the reviews of every node it touches, so do it
  **before** reviewing the remaining 60. If a future tick insists on finishing Tick B first, the next
  batch is the 9 voided nodes plus `mat_g3_*`.

---

## 2026-08-12 — Tick B (batch B6) — audit clean, 0 voided

- **Census before:** PASS=37 CONCERN=32 FAIL=22 over 91 reviewed; 60 unreviewed. Tick 0 no, Tick A no.
  **Tick B fires** (§3 order: Tick B is listed above Tick C, and nodes lack reviews). I have now
  recommended jumping to Tick C twice; the loop re-fired unchanged, so I treated that as the decision
  and stopped re-litigating. **Do not raise it a third time — just follow §3 order.**
- **Unit of work:** batch **B6** = the 9 nodes voided in B5 (re-reviewed by a fresh identity) + 16 g3
  nodes (`dp_q3`, `mg_q1`, `mg_q2`). One blind reviewer + one adversarial evaluator.
- **Root cause:** n/a — evidence-producing tick.
- **Files touched:** 25 new reviews; `judgment_audit/batch_B6.json`. No pipeline code.
- **Verification:**
  - B6: **3 PASS / 8 CONCERN / 14 FAIL**, counts confirmed against disk (this reviewer counted
    correctly, unlike B5's).
  - Evaluator: **0 void**, **0/5 disagreement**, `batch_reliable: true`. It script-verified every
    quantitative claim instead of eyeballing.
  - census over 116: `{'FAIL': 36, 'CONCERN': 40, 'PASS': 40}`, cluster 2, quote failures 0, 6 reviewers.
  - `run_all` → `EXIT_CODE=1`, `288 problem(s)` at 6/6, **0 non-judgment FAIL lines**, 6 stages,
    matrix 151/151 / 0 failures, both contract checks PASS.
  - **The 9 re-reviewed nodes returned the same verdict directions** as the discarded B5 reviews. That
    independently corroborates the B5 evaluator: those verdicts were sound, only their evidence was false.
- **Census after:** PASS=40 CONCERN=40 FAIL=36 over **116 reviewed**; **35 unreviewed**.
- **Commit:** `e947306` review(judgment): file 25 blind reviews for batch B6; audit clean, 0 voided.

### I made a verification error this tick — recorded so it is not repeated

I told the evaluator that a filed claim was false: that `mat_g3_mg_q2_3`'s values matched a sibling mass
node. **I had compared the wrong pair** (`mg_q2_1` instead of `mg_q2_0`). The evaluator pushed back with
a script and was right. Against `mg_q2_0` the two nodes are identical on **9/9 shared seeds**. When
spot-checking a claim about "a sibling", identify *which* sibling from the review text before comparing.

### Tick C cluster — sibling duplication is now the dominant root cause, script-verified

| Pair / group | Overlap | Competencies |
|---|---|---|
| `mat_g2_na_q1_9` = `q1_10` | 19/19 identical | "Add… sums up to 1000" vs "…properties of addition" |
| `mat_g2_na_q3_0` = `q3_1` | 11/11 identical | "repeated addition" vs "multiplication as repeated addition" |
| `mat_g2_na_q4_2` = `q4_5` | 9/9 ordering identical | "Order unit fractions" vs "Order similar fractions" |
| `mat_g3_mg_q1_0/_1/_2/_3` | 14–15 of shared seeds | area/perimeter formula family |
| `mat_g3_mg_q2_0` = `q2_3` | 9/9, identical answers | **"Measure mass in grams (g), kilograms (kg)…" vs "Measure capacity in liters (L) and/or milliliters (mL)…"** |

The last is the clearest single reproduction: seed 42 renders `What is the weight of the object in g?`
and `What is the amount of liquid of the object in mL?`, both answering `15`, with identical option
lists. **Mass and capacity are the same generator with a unit label swapped.** Five independent
groups, three grades — one binding cause.

Other confirmed, directly verified: `mat_g3_dp_q3_0`'s competency is *"Collect data from experiments
with a small number of possible outcomes (e.g., rolling a die or tossing a coin)"* and **0 of 14**
samples mention a die, coin, or spinner. `mat_g3_mg_q2_1` is **15/15 grams**, zero kg, zero mg.

- **Next tick should:** finish Tick B with the **last 35 nodes** — one batch of 25 (`mat_g3_mg_q4_*`,
  `mat_g3_na_q1_*`, `mat_g3_na_q2_*`) then a final batch of 10 next tick, each with its own evaluator
  and a distinct `reviewed_by`. After that the census has all 151 and §3 falls through to **Tick C**,
  where the first cluster is unambiguous: **sibling duplication**, five verified groups, starting with
  `mat_g3_mg_q2_0`/`q2_3` because mass-vs-capacity is the least ambiguous reproduction and its seeds
  are recorded above. Graphify the registry → DNA → adapter path for that pair first.

---

## 2026-08-12 — Tick B (batch B7a, 12 nodes) — *preceded by a second aborted tick*

- **Second aborted tick, again no state lost.** A 25-node B7 reviewer was killed by the session usage
  limit before writing any file. Verified on restart: tree clean at `e947306`, 116 reviews, 0
  unparseable. **Two 25-node dispatches have now died this way.**
  **Batch size is now 12, not 25.** Measured: 12 nodes cost ~122k subagent tokens and finished;
  25 nodes cost 210k+ and died twice. Do not go back to 25.
- **Census before:** PASS=40 CONCERN=40 FAIL=36 over 116; 35 unreviewed. Tick 0 no, Tick A no,
  **Tick B fires**.
- **Unit of work:** batch **B7a** — 12 g3 nodes (`mg_q2_4`, `mg_q2_5`, `mg_q4_0-2`, `na_q1_0-6`),
  one blind reviewer + one adversarial evaluator.
- **Files touched:** 12 new reviews; `judgment_audit/batch_B7a.json`. No pipeline code.
- **Verification:**
  - B7a: **3 PASS / 9 CONCERN / 0 FAIL**, counts confirmed against disk.
  - Evaluator: **0 void**, **0/3 disagreement**, `batch_reliable: true`.
  - census over 128: `{'FAIL': 36, 'CONCERN': 49, 'PASS': 43}`, cluster 2, quote failures 0, 7 reviewers.
  - `run_all` → `EXIT_CODE=1`, `297 problem(s)` at 6/6, **0 non-judgment FAIL lines**, 6 stages,
    matrix 151/151 / 0 failures, both contract checks PASS.
  - I independently verified three of the reviewer's numeric claims; **all exact**:
    `na_q1_2` ordinals present are 7,8,9,12,46,47,49,52,53 → max **53rd** vs competency "up to 100th";
    `na_q1_5` max integer anywhere **6709** vs "up to 10 000"; `na_q1_0` seeds 600/601 byte-identical
    to sibling `na_q1_1` (`Write 334 in words.`).
- **Census after:** PASS=43 CONCERN=49 FAIL=36 over **128 reviewed**; **23 unreviewed**.
- **Commit:** `ee6b7d4` review(judgment): file 12 blind reviews for batch B7a; audit clean, leniency flagged.

### New failure mode found: reviewer leniency (not caught by any machine check)

The evaluator flagged that this batch **rounds near-total competency misses down to CONCERN instead of
FAIL**. Verified directly: `mat_g3_mg_q2_5`'s competency is *"Compare capacities of two containers"*;
all **15/15** samples are the single template `Which is more: # mL or # mL?` with **zero** container
nouns. That is a 0/15 miss on the competency's stated object, filed as CONCERN. Same shape at
`mat_g3_na_q1_0`, where **7 of 13** samples test a sibling's word↔numeral competency.

**No verdict was changed** — flipping a filed verdict is falsifying evidence (§1 rule 2); only a fresh
blind re-review can move one. **Consequence for Tick C: rank clusters by the evidence in the rationale,
not by the CONCERN/FAIL label.** Some CONCERNs in this tree are total misses.

### Sibling-duplication cluster — now six verified groups
`g2_na_q1_9`≡`q1_10` (19/19) · `g2_na_q3_0`≡`q3_1` (11/11) · `g2_na_q4_2`≡`q4_5` (9/9 ordering) ·
`g3_mg_q1_0/_1/_2/_3` (14–15 shared seeds) · `g3_mg_q2_0`≡`q2_3` (9/9, mass≡capacity) ·
**`g3_na_q1_0`/`q1_1` (seeds 600, 601)** ← new this tick.

- **Next tick should:** finish Tick B with the **last 23 nodes** in **two batches of ~12**
  (`mat_g3_na_q2_*` + `na_q3_*` = 12, then `na_q3_5`/`na_q3_6` + `na_q4_*` = 11), each with its own
  evaluator and a distinct `reviewed_by`. That is two more ticks. Then §3 falls through to **Tick C**,
  first cluster **sibling duplication** (six groups above), starting with `g3_mg_q2_0`/`q2_3` —
  mass≡capacity on 9/9 seeds is the least ambiguous reproduction in the tree.

---

## 2026-08-12 — Tick B (batch B7b, 12 nodes) — 3 of 12 voided

- **Census before:** PASS=43 CONCERN=49 FAIL=36 over 128; 23 unreviewed. Tick 0 no, Tick A no,
  **Tick B fires**.
- **Unit of work:** batch **B7b** — 12 g3 nodes (`na_q2_0-7`, `na_q3_0-3`), reviewer + evaluator.
  12-node size held up again (~134k reviewer / ~139k evaluator tokens, both finished).
- **Files touched:** 9 new reviews (3 written then deleted as voided); `judgment_audit/batch_B7b.json`.
  No pipeline code.
- **Verification:**
  - B7b filed: 5 PASS / 7 CONCERN / 0 FAIL, counts confirmed against disk.
  - Evaluator: **3 void (25%)**, `batch_reliable: false`; **0/3 disagreement** on independent
    re-judgment. Same profile as B5: verdict directions right, supporting evidence wrong.
  - **All 3 voids verified by me against the packet before deletion — all stand:**
    `q2_0` credits the centavo notation as generated, but `¢` is the `correct_answer` on **0 of 17**
    samples and appears only as a *wrong distractor* (seeds 42/44/46/72/600/601/604);
    `q2_2` lists cloze among its formatters, actual distribution is `mcq`×13 + `read_fill_in_blank`×2,
    **zero cloze**; `q2_4` gives the largest operand as "seed44's 7222" when seed 604 is
    `What is 8460 − 1120?`.
  - census after deletion (137): `{'FAIL': 36, 'CONCERN': 54, 'PASS': 47}`, cluster 2, quote failures 0,
    8 reviewers.
  - `run_all` → `EXIT_CODE=1`, `300 problem(s)` at 6/6, **0 non-judgment FAIL lines**, 6 stages,
    matrix 151/151 / 0 failures, both contract checks PASS.
- **Census after:** PASS=47 CONCERN=54 FAIL=36 over **137 reviewed**; **14 unreviewed**.
- **Commit:** `f145495` review(judgment): file 9 surviving B7b reviews; void 3 for false evidentiary claims.

### A claim I flagged as suspect that turned out to be fine — my error, not the reviewer's
I told the evaluator that `q3_1`'s "duplicates sibling `q3_0`" claim looked false, having found 0
byte-identical texts across their 13 shared seeds. The evaluator checked the rationale's actual wording:
it never asserts textual identity, it says the samples duplicate *rote-fact content belonging to the
sibling tables competency* — the weaker, defensible claim. **I was testing a stronger claim than the
review made.** Second time this has happened (cf. `mg_q2_3`, wrong sibling). Read the rationale's exact
wording before designing the check.

### Leniency confirmed for a second consecutive batch
`mat_g3_na_q3_2`: competency names *"2- to 3-digit numbers by a 1-digit number"*; **0 of 14** samples
pair a 3-digit multiplicand with a 1-digit multiplier — 936, 962 and 845 are each multiplied only by 10.
A wholly unexercised named sub-case, filed CONCERN. Verdict not changed (§1 rule 2).
**Standing instruction for Tick C: rank by the evidence in the rationale, not the CONCERN/FAIL label.**

### New content finding worth its own fix (not duplication)
`mat_g3_na_q2_0`: the competency's centavo notation is *only ever generated as a wrong answer*. That is
distinct from the "sub-case never generated" family — here the sub-case appears exclusively as a
distractor, which teaches against the competency.

- **Next tick should:** **finish Tick B** — the last **14** nodes in one batch of 12 plus the 2 leftovers,
  or one batch of 14 (still under the 12-node norm's proven ceiling; 14 is acceptable, 25 is not).
  Nodes: `na_q2_0`, `na_q2_2`, `na_q2_4` (the three voided) + `na_q3_4`, `na_q3_5`, `na_q3_6`,
  `na_q4_0`–`na_q4_7`. Use a fresh `reviewed_by` and give the reviewer the FAIL/CONCERN calibration
  paragraph — two batches running 0 FAIL is a calibration signal, not a content signal.
  **After that the census covers all 151 and §3 falls through to Tick C.** First cluster: sibling
  duplication (six verified groups), starting `g3_mg_q2_0`≡`q2_3` (mass≡capacity, 9/9 seeds).

---

## 2026-08-12 — Tick B (batch B8, 14 nodes) — **TICK B COMPLETE: all 151 nodes reviewed**

- **Census before:** PASS=47 CONCERN=54 FAIL=36 over 137; 14 unreviewed.
- **Unit of work:** final batch **B8** — the 3 nodes voided in B7b + `na_q3_4-6` + `na_q4_0-7`.
  Reviewer + evaluator. 14 nodes fit the budget fine (~160k / ~127k tokens).
- **Files touched:** 14 new reviews; `judgment_audit/batch_B8.json`. No pipeline code.
- **Verification:**
  - B8: **5 PASS / 4 CONCERN / 5 FAIL**, counts confirmed against disk.
  - Evaluator: **0 void**, **0/4 disagreement**, **no miscalibrated verdict in either direction**,
    `batch_reliable: true`.
  - **FULL-TREE CENSUS: 151 reviewed — `{'PASS': 52, 'CONCERN': 58, 'FAIL': 41}`, UNREVIEWED 0.**
    Largest skeleton cluster **2** (threshold 3), quote-provenance failures **0**, **9 reviewer
    identities** all within quota. (Deleted fabricated set for contrast: cluster 151, 115 phantom
    quotes, 1 reviewer.)
  - `run_all` → `EXIT_CODE=1`, `313 problem(s)` at 6/6, **0 non-judgment FAIL lines**,
    **0 "missing genuine judgment review" errors** — every remaining problem is a genuine non-PASS
    verdict, not a missing artifact. Matrix 151/151 / 0 failures; both contract checks PASS.
- **Commit:** `881f1fa` review(judgment): file final 14 reviews — all 151 nodes now carry a blind review.

### Calibration was fixed by instruction, and it held
B7a and B7b both filed 0 FAIL and were audited as systematically lenient. B8's reviewer got explicit
FAIL/CONCERN criteria (FAIL = a named sub-case with **0%** representation; CONCERN = a real partial
gap) and filed 5 FAIL — the evaluator confirmed every one rests on a genuine 0% gap, and found no
unearned FAIL either. **Give that calibration paragraph to every future reviewer.**

Independently verified this tick: `mat_g3_na_q4_0` — competency *"Illustrate division through equal
jumps on the number line and as inverse of multiplication"*, **0 of 18** samples mention a jump, a
number line, or the inverse relation. `mat_g3_na_q2_0` — `¢` correct on **0 of 17**, distractor only;
**rediscovered independently by a different reviewer from a fresh packet** than the one that found it
in B7b, which is real corroboration. `mat_g3_na_q4_5` — dividends 30,2,20,12,10,10,10,72,81,27,12,3,20,
max **81**, 0 of 13 reach 3 digits (evaluator hand-parsed the word-problem stems; my regex could not).

## TICK C PUNCH LIST — 41 FAIL nodes

By domain: `g2_na` 12 · `g2_mg` 6 · `g1_na` 5 · `g3_mg` 5 · `g3_na` 5 · `g3_dp` 3 · `g1_mg` 2 ·
`g2_dp` 2 · `g1_dp` 1.
By judgment item: comprehensive_coverage 30 · competency_fulfillment 20 · competency_alignment 18 ·
variant_comprehensiveness 7 · scale_appropriateness 6 · cognitive_capacity 3.

```
mat_g1_dp_q3_0 mat_g1_mg_q1_0 mat_g1_mg_q2_2 mat_g1_na_q1_2 mat_g1_na_q1_8 mat_g1_na_q1_9
mat_g1_na_q2_4 mat_g1_na_q3_3 mat_g2_dp_q3_0 mat_g2_dp_q3_1 mat_g2_mg_q1_0 mat_g2_mg_q2_0
mat_g2_mg_q2_1 mat_g2_mg_q2_2 mat_g2_mg_q4_2 mat_g2_mg_q4_4 mat_g2_na_q1_10 mat_g2_na_q1_5
mat_g2_na_q2_0 mat_g2_na_q2_3 mat_g2_na_q2_5 mat_g2_na_q2_7 mat_g2_na_q3_0 mat_g2_na_q3_1
mat_g2_na_q4_1 mat_g2_na_q4_2 mat_g2_na_q4_4 mat_g2_na_q4_5 mat_g3_dp_q3_0 mat_g3_dp_q3_1
mat_g3_dp_q3_2 mat_g3_mg_q1_6 mat_g3_mg_q2_0 mat_g3_mg_q2_1 mat_g3_mg_q2_2 mat_g3_mg_q2_3
mat_g3_na_q2_0 mat_g3_na_q3_4 mat_g3_na_q4_0 mat_g3_na_q4_3 mat_g3_na_q4_5
```

**`comprehensive_coverage` is the single largest failing item (30 of 41).** That is one symptom —
*a sub-case the competency names is never generated* — not thirty bugs.

### Root-cause clusters, all packet-verified, ranked for Tick C
1. **Sibling duplication (7 groups).** `g2_na_q1_9`≡`q1_10` (19/19) · `g2_na_q3_0`≡`q3_1` (11/11) ·
   `g2_na_q4_2`≡`q4_5` (9/9 ordering) · `g3_mg_q1_0/_1/_2/_3` (14–15 shared seeds) ·
   `g3_mg_q2_0`≡`q2_3` (9/9, **mass ≡ capacity**) · `g3_na_q1_0`/`q1_1` (seeds 600,601) ·
   `g3_na_q4_2` (seeds 42≡43 *within* one node).
2. **Named sub-case never generated** — the 30 `comprehensive_coverage` FAILs.
3. **Fraction ordering routed to whole numbers** — `g2_na_q4_2`/`q4_5`, zero fractions in any ordering
   task; ties to the known harness §1E `sorted()` blind spot. Fix the routing, not the check.
4. **Required form generated only as a distractor** — `g3_na_q2_0`'s centavo notation. Distinct family:
   the sub-case exists but exclusively as a wrong answer, which teaches against the competency.

- **Next tick should:** **TICK C.** §3's trigger order now falls through to it — every node has a
  review and CONCERN/FAIL verdicts exist. Take **cluster 1**, and inside it start with
  `g3_mg_q2_0`≡`g3_mg_q2_3` (mass ≡ capacity, identical answers on seeds 42,43,44,45,46,50,500,501,502).
  Per §3 Tick C: Graphify the registry → DNA → adapter path **first**, find why the sub-concept never
  binds, enumerate every node the cause touches, make the DNA `raise` naming concept/grade/seed rather
  than cascading to a default, then `validate_matrix --node <each>` and a full `run_all`. Then dispatch
  a **fresh blind re-review** of every node the fix touched — a fix is not done until a reviewer who
  never saw it scores the new content — and append to `validation_reports/HARDENING_EVIDENCE.md`.
  Remember: **rank by the evidence in each rationale, not by the CONCERN/FAIL label** — B7a/B7b
  leniency means some CONCERNs (e.g. `g3_mg_q2_5`, 0/15 containers; `g3_na_q3_2`, 0/14 3-digit×1-digit)
  are total misses.

---

## 2026-08-12 — **TICK C #1** — mass/capacity unit binding

- **Census before:** PASS=52 CONCERN=58 FAIL=41 over 151 reviewed, 0 unreviewed. Tick 0 no, Tick A no,
  **Tick B no longer fires** (every node has a review) → **§3 falls through to Tick C.**
- **Unit of work:** cluster 1, sub-cluster `mass_capacity` — 6 nodes, `mat_g3_mg_q2_0…_5`.
- **Root cause:** `mass_capacity.py` read `unit` off the difficulty profile while `_DIFFICULTY_AXES`
  declared only `number_difficulty`. **`unit` was never a declared axis**, so nothing varied it and no
  registry binding set it — pinned to its default forever. `read_measurement`/`estimate`/`compare`
  never consulted it, hardcoding `"g"` / `"mL"`; kg, mg and L were unreachable everywhere and the
  kg→g `convert` branch was dead code. Separately `_PARAM_BOUNDS` gave both types the identical
  `1..5000` envelope over one `random.Random(seed)`, so mass and capacity rendered the same numbers.
  **Textbook §1 rule 5.**
- **Files touched:** `backend/app/practice_gen/dna/mg/mass_capacity.py` only;
  6 reviews rewritten; `validation_reports/HARDENING_EVIDENCE.md`.
- **Verification:**
  - before → after rendering, seeds 42–502: `q2_0 {g}` → `{g:3,kg:3,mg:3}`; `q2_3 {mL}` → `{mL:3,L:6}`;
    answers were **identical on all 9 shared seeds**, now disjoint.
  - `validate_matrix --node` × 6 → `Total Failures Observed: 0` each.
  - tie sweep: **0 ties across 97 compare items / 58 seeds**; rounding bases `{10,100,1000}` only.
  - `run_all` → `EXIT_CODE=1`, judgment problems **313 → 285**, 6 stages, matrix 151/151 / 0 failures,
    **0 non-judgment FAIL lines, 0 STALE errors**, both contract checks PASS.
- **Fresh blind re-review** (reviewer never saw the fix, rebuilt packet):
  `q2_0 FAIL→PASS · q2_1 FAIL→PASS · q2_2 FAIL→PASS · q2_3 FAIL→CONCERN · q2_4 CONCERN→PASS ·
  q2_5 CONCERN→PASS`.
- **Census after:** **PASS=57 CONCERN=55 FAIL=37** (net −4 FAIL, +5 PASS).
- **Commit:** `cdad76d` fix(pgen): bind mass/capacity units to the competency — clears 4 FAIL, 2 CONCERN.

### Two extra defects the post-fix review caught — both fixed in the same commit
- **Unanswerable comparison:** `Which is heavier: 4 mg or 4 mg?` — a tie, MCQ still marking one option
  correct. Now guaranteed distinct.
- **Non-place-value rounding:** `_round_unit_for` returned `500` for values ≥1000 → "rounded to the
  nearest 500". Now `1000`. Latent for as long as readings never exceeded 1000.

### Method notes for the next Tick C (these cost time this tick)
1. **A fix invalidates its nodes' reviews.** The freshness gate flagged all 6 as STALE immediately
   (`seed 44 ... Reviewed: 'in g?'; now renders: 'in kg?'`). Budget for delete → rebuild packet →
   re-review **inside the same tick**, or the tree ends red on staleness.
2. **Expect two review rounds.** The first post-fix review found two *new* real defects; fixing them
   invalidated the reviews again. Round 1 → fix → round 2 was the actual shape. Plan for it.
3. **A new `raise` can break the matrix at scalar extremes.** My tie-guard raised at `scalar 0.0`
   where `log_interpolate` collapses the range to `[1,1]` — 30 matrix failures per compare node. The
   guard was right that the state is broken; the fix was to widen the range, not to drop the guard.
   **Always run `validate_matrix --node` after adding a raise, before re-reviewing.**

- **Next tick should:** **Tick C #2.** Remaining sibling-duplication groups, in this order —
  `g2_na_q1_9`≡`q1_10` (19/19 identical, properties-of-addition served as plain addition; same shape
  as `mat_g1_na_q1_8`, so fix both), then `g2_na_q3_0`≡`q3_1` (11/11), then
  `g3_mg_q1_0/_1/_2/_3` (14–15 shared seeds), then `g3_na_q1_0`/`q1_1` (seeds 600,601) and
  `g3_na_q4_2` (seeds 42≡43 *within* one node). Diagnose the same way: read the filed rationales, check
  whether the DNA consumes a profile key that `_DIFFICULTY_AXES` never declares, and check whether two
  concepts share one RNG stream over one bounds envelope. After that, cluster 3 (fraction ordering
  routed to whole numbers, `g2_na_q4_2`/`q4_5`) and cluster 4 (`g3_na_q2_0` centavo notation generated
  only as a distractor). **Rank by the evidence in each rationale, not the CONCERN/FAIL label.**

---

## 2026-08-12 — **TICK C #2** — properties of addition never bound

- **Census before:** PASS=57 CONCERN=57 FAIL=37. Tick 0/A/B no → **Tick C**.
- **Unit of work:** cluster 1 continued — `mat_g1_na_q1_8`, `mat_g2_na_q1_10`.
- **Root cause (same shape as Tick C #1):** `addition.py` already implements `zero_identity`,
  `commutative`, `associative`, written for these two nodes **by name** — dead code, because
  `_parse_competency_bounds` never bound `task_type` for the properties competencies. The registry
  binds `task_type` for addition's other sub-skills (`estimate`, `expanded_form`, `counting_up`);
  properties were just missing from that list. Both nodes fell through to plain addition.
- **Files touched:** `registry.py`, `dna/na/addition.py`, 2 reviews, `HARDENING_EVIDENCE.md`.
- **Verification:** properties shown `q1_8` 1/18 → `zero_identity 10/19 + commutative 6/19`;
  `q1_10` 0/19 → `zero_identity 9/18, commutative 4/18, associative 3/18`;
  `q1_9`≡`q1_10` identical stems **19/19 → 1/18**; carrying pairs 0;
  `validate_matrix --node` × 4 → 0 failures each;
  `run_all` → `EXIT_CODE=1`, **matrix 151/151, 0 failures**, 0 non-judgment FAIL lines, contracts PASS.
- **Fresh blind re-review:** `mat_g1_na_q1_8 FAIL→CONCERN`, `mat_g2_na_q1_10 FAIL→CONCERN`.
- **Census after:** **PASS=57 CONCERN=59 FAIL=35.**
- **Commit:** `dbb60fb`.

### Three lessons this tick paid for — read before the next Tick C

1. **"No regrouping" is spelled three ways: absent, `"none"`, and the boolean `False`.** My first guard
   tested `not in (None, "none")` and broke `mat_g1_na_q2_5` / `q2_6` (which bind `regrouping=False`
   and reach property task types via variant coverage) for **600 matrix failures**. Normalize before
   comparing an axis value.
2. **`validate_matrix --node` does not show blast radius.** Those two nodes were green in every scoped
   run I did and only the full `run_all` caught them. **Run the full `run_all` before believing a
   generator change is contained**, even when the scoped nodes are green.
3. **A new `raise` must tolerate every legal encoding of "unconstrained".** Same root lesson as #1;
   the harness treats `RuntimeError` from generation as an expected infeasible combination, which is
   the right channel — but only for combinations that are *genuinely* infeasible.

### Two defects found while verifying, NOT fixed — pick these up next

1. **Regression I introduced.** `_carry_free_addends` distributes a ones budget and a tens budget only,
   capping any addend at 99. `mat_g2_na_q1_10`'s competency says "sums up to 1000" and its largest sum
   is now **97**. **Fix: give the helper a hundreds column budget** so carry-free 3-digit addends are
   reachable. Then re-review that node. This is the first thing the next tick should do.
2. **Gate gap — `validate_judgment_reviews` never freshness-checks a non-PASS review.** In the loop,
   `if errs or not path.exists(): ... continue` skips `_validate_freshness` whenever `_validate_one`
   already returned anything — and a CONCERN/FAIL verdict *always* returns something. Measured this
   tick: `mat_g1_na_q1_8` and `mat_g2_na_q1_10` were **16 and 19 samples stale** while the full gate
   reported **0 STALE**. A stale FAIL review is therefore invisible. This is a Tick-A-species hardening
   (editing the verifier is the point there); do it in its own tick, not inside a generator fix, since
   `validation/` is read-only while fixing a generator.

- **Next tick should:** finish the regression above (hundreds column + re-review `mat_g2_na_q1_10`),
  then continue cluster 1 with `g2_na_q3_0`≡`q3_1` (11/11 identical, repeated addition vs
  multiplication-as-repeated-addition) — expect the identical diagnosis: check whether
  `multiplication`/`counting` consumes a `task_type` the registry never binds. Remaining after that:
  `g3_mg_q1_0/_1/_2/_3`, `g3_na_q1_0`/`q1_1`, `g3_na_q4_2` (seeds 42≡43 within one node). Then
  cluster 3 (fraction ordering → whole numbers) and cluster 4 (`g3_na_q2_0` centavo-as-distractor).
  Note `mat_g3_na_q3_1` binds `task_type` as a **list** including `find_product`, which dilutes its
  property coverage — the sentinel pattern used here is the better model.

---

## 2026-08-12 — **TICK C #3** — hundreds column (closes the regression from #2)

- **Census before:** PASS=57 CONCERN=59 FAIL=35. Tick 0/A/B no → **Tick C**.
- **Unit of work:** the regression the previous tick recorded and left open — `_carry_free_addends`
  budgeted only ones and tens, capping every addend at 99, so `mat_g2_na_q1_10` ("sums up to **1000**")
  topped out at 97.
- **Fix:** the helper now walks place-value columns `(1, 10, 100)`, each with its own budget of 9 (a
  column summing ≤9 cannot carry), each capped by what the lower columns already spent. Another column
  is now a one-line addition.
- **Verification:**
  - `mat_g2_na_q1_10` max operand **97 → 927**; largest associative sample `553 + 123 + 221 = 897`
    (seed 501); carrying pairs **0**.
  - `mat_g1_na_q1_8` **unchanged** (max operand 16; its ceiling of 20 leaves the hundreds budget at 0)
    and re-rendered with **0 stale samples**.
  - `validate_matrix --node` × 4 (`q1_8`, `q1_10`, `q2_5`, `q2_6`) → 0 failures each.
  - `run_all` → `EXIT_CODE=1`, **matrix 151/151, 0 failures**, 0 non-judgment FAIL lines, contracts PASS.
- **Fresh blind re-review** of `mat_g2_na_q1_10`: **CONCERN** (unchanged verdict, narrower grounds — the
  scale objection is now that only the associative samples reach toward 1000, not that everything is
  capped at 97).
- **Census after:** **PASS=57 CONCERN=59 FAIL=35** (unchanged; the node was already CONCERN).
- **Commit:** `00f9c1a`.

### Method note worth keeping
I deleted **both** nodes' reviews before checking staleness, then found `mat_g1_na_q1_8` had **0 stale
samples** — its rendering was untouched — and restored it with `git checkout HEAD -- <path>`.
**Check `_validate_freshness` per node *before* deleting a review.** A fix often changes only a subset
of the nodes that share the generator, and a valid review is expensive to recreate.

- **Next tick should:** continue cluster 1 with **`g2_na_q3_0` ≡ `q3_1`** (11/11 identical stems;
  "count by repeated addition" vs "illustrate and write multiplication as repeated addition"). Expect
  the same diagnosis both previous Tick Cs found: a DNA consuming a `task_type`/sub-concept key that
  `_parse_competency_bounds` never binds for that node. Check `multiplication` and `counting`.
  Remaining in cluster 1 after that: `g3_mg_q1_0/_1/_2/_3` (14–15 shared seeds),
  `g3_na_q1_0`/`q1_1` (seeds 600, 601), `g3_na_q4_2` (seeds 42≡43 *within* one node).
  Then cluster 3 (fraction ordering → whole numbers, `g2_na_q4_2`/`q4_5`) and cluster 4
  (`g3_na_q2_0` centavo generated only as a distractor).
  **Still open from #2 and not yet scheduled:** the gate gap where `validate_judgment_reviews` skips
  `_validate_freshness` for any review that already has an error, so a stale CONCERN/FAIL review is
  invisible. That is Tick-A-species work — give it its own tick.

---

## 2026-08-12 — **TICK C #4** — equal_groups split from repeated_addition

- **Census before:** PASS=57 CONCERN=59 FAIL=35. Tick 0/A/B no → **Tick C**.
- **Unit of work:** cluster 1 continued — `mat_g2_na_q3_0` ≡ `q3_1` (11/11 identical stems).
- **Root cause — a NEW shape, not the previous two.** Not an unbound key. Both competencies contain the
  literal phrase `"repeated addition"`, so `_parse_competency_bounds`' single text match bound **both**
  to `task_type="repeated_addition"` with the same `max_product`. Identical bindings → identical output.
  `"equal groups"` appears only in `q3_0`'s text and discriminates them.
  **Generalisation for future ticks: a duplication pair can come from one text match that is too broad,
  not only from a key that is never bound. Check both.**
- **Files touched:** `registry.py`, `generators/base_generator.py`,
  `formatters/textual/fmt_mcq.py`, `formatters/textual/fmt_cloze.py`, 1 review, `HARDENING_EVIDENCE.md`.
- **Verification:** group language in `q3_0` **0/11 → 10/11**; bare `"What is A × B?"`
  **3/11 → 0/11**; `q3_0`≡`q3_1` identical stems **11/11 → 1/11**;
  `validate_matrix --node` × 3 → 0 failures; `run_all` → `EXIT_CODE=1`, **matrix 151/151, 0 failures**,
  0 non-judgment FAIL lines, contracts PASS.
- **Fresh blind re-review:** `mat_g2_na_q3_0` **FAIL → CONCERN**.
- **Census after:** **PASS=57 CONCERN=60 FAIL=34.**
- **Commit:** `1943859`.

### The trap that cost most of this tick
**The repeated-addition render framing is duplicated in THREE places:**
`base_generator._build_symbolic_question`, `formatters/textual/fmt_mcq.py`, and
`formatters/textual/fmt_cloze.py` — each rebuilds its own question text. I edited `base_generator`
first and **nothing changed**, because `mcq` is this node's formatter on every sampled seed.
**Before adding any question-stem branch, `grep -rn` the existing sibling branch across
`generators/` and `formatters/` and patch every copy.** The code comments already flag this
duplication; they are worth reading first.

### Still open, and the natural next unit
`mat_g2_na_q3_1` remains **FAIL**: its competency names *arrays*, *counting by multiples*, and *equal
jumps on a number line*, and the review found **none of the three** in any sample, nor any pictorial
model. The multiplication DNA already declares `array_grid_read` / `array_grid_set` in
`compatible_formatters`, so this is a **formatter-selection** question, not new content authoring —
find why those formatters are never chosen for this node. (Memory note
`formatter-declaration-triggers-exhaustive-sweep` is relevant: declaring a formatter exposes it to the
§1C sweep on every mapped node, so check the sweep before changing bindings.)

- **Next tick should:** fix `mat_g2_na_q3_1` (array/number-line/skip-count models never selected) — it
  is the last node in the `g2_na_q3` pair and still FAIL. After that, remaining cluster-1 duplication:
  `g3_mg_q1_0/_1/_2/_3` (14–15 shared seeds), `g3_na_q1_0`/`q1_1` (seeds 600, 601), `g3_na_q4_2`
  (seeds 42≡43 *within* one node). Then cluster 3 (fraction ordering → whole numbers,
  `g2_na_q4_2`/`q4_5`) and cluster 4 (`g3_na_q2_0` centavo generated only as a distractor).
  **Still unscheduled:** the Tick-A-species gate gap — `validate_judgment_reviews` skips
  `_validate_freshness` whenever `_validate_one` already returned an error, so a stale CONCERN/FAIL
  review is invisible. Give it its own tick.

---

## 2026-08-12 — **TICK C #5** — arrays reachable; census did NOT move

- **Census before:** PASS=57 CONCERN=60 FAIL=34. **Census after: PASS=57 CONCERN=60 FAIL=34 — unchanged.**
  Judgment problems 285 → 281. This tick improved content but **cleared no verdict**. Recording that
  plainly: not every Tick C moves the census.
- **Unit of work:** `mat_g2_na_q3_1` — its competency names arrays, yet `array_grid_read/set` were
  unreachable on it.
- **Root cause:** `compatibility.py` gated both array formatters to `task_type: ["find_product"]`.
  `q3_1` binds `repeated_addition` → arrays structurally impossible on the node that names arrays.
  The gate's own comment ("shows product, not missing factor") is about **`structure`**, already
  constrained by the sibling `"structure": ["result_unknown"]` entry — the `task_type` restriction was
  unintended collateral. **Lesson: read what a compatibility comment claims to protect and check
  whether a *different* key already protects it.**
- **Files touched:** `compatibility.py`, `formatters/visual/fmt_array_grid.py`, 2 reviews,
  `HARDENING_EVIDENCE.md`.

### The mid-tick regression — and why the second half of the fix was mandatory
Widening the gate **alone made things worse**: both siblings then rendered the *same* array stems
(`Shade all the squares inside the 3×2 rectangle`) because the array formatter never named which
sub-skill it illustrated. Duplication went **0 → 6 of 15**, and `mat_g2_na_q3_0` regressed
**CONCERN → FAIL**. The blind re-review caught it; I verified the 6 shared stems myself before acting.
`fmt_array_grid.py` now frames by task type (`equal_groups` → "3 groups of 3";
`repeated_addition` → "It shows 3 + 3 + 3"), which took duplication to **1 of 15** and recovered
`q3_0` to CONCERN.
**Generalisable: making a formatter reachable on a new task type usually requires giving that
formatter task-specific stem text in the same tick, or you trade a coverage gap for a duplication bug.**

- **Verification:** `q3_1` formatters `mcq` only → `mcq + read_mcq + set_fill_in_blank`;
  samples naming "array" 0 → 1; identical stems 0/11 → 6/15 → **1/15**;
  `validate_matrix --node` × 5 → 0 failures; `run_all` → `EXIT_CODE=1`, **matrix 151/151, 0 failures**,
  0 non-judgment FAIL lines, contracts PASS.
- **Fresh blind re-review:** `q3_0 CONCERN → CONCERN`, `q3_1 FAIL → FAIL`.
- **Commit:** `40a8531`.

### Why `mat_g2_na_q3_1` is still FAIL — and why I stopped
Two of its competency's six named representations, **"counting by multiples"** and **"equal jumps on a
number line"**, appear in **0 of 15** samples. Neither exists anywhere in the multiplication DNA or its
formatters — this is **new content to author**, not a binding to repair, and it is larger than one
tick. Treat it as its own unit when picked up: a skip-count task type and a number-line-jump
formatter/visual.

- **Next tick should:** **stop working this pair** and take a cheaper, higher-yield cluster. Options in
  order of expected value:
  1. `g3_na_q1_0`/`q1_1` duplication (only seeds 600, 601 shared) — likely a narrow binding fix.
  2. `g3_na_q4_2` — seeds 42≡43 render identically *within a single node*, which is a distinct bug
     shape (intra-node collision, not sibling leakage) and probably a small RNG/profile issue.
  3. Cluster 4, `g3_na_q2_0` — the centavo notation is generated **only as a wrong distractor**,
     never as a correct answer. Self-contained and clearly wrong.
  4. `g3_mg_q1_0/_1/_2/_3` (14–15 shared seeds) — the largest remaining duplication group.
  Defer: `mat_g2_na_q3_1`'s missing representations, and the Tick-A gate gap
  (`validate_judgment_reviews` skips `_validate_freshness` when `_validate_one` already errored, so a
  stale CONCERN/FAIL review is invisible — still unscheduled).

---

## 2026-08-12 — **TICK C #6** — centavo sign taught, not only trapped

- **Census before:** PASS=57 CONCERN=60 FAIL=34. **Census after: PASS=57 CONCERN=61 FAIL=33.**
  Judgment problems 281 (unchanged — a FAIL→CONCERN move does not reduce the gate's error count).
- **Unit of work:** `mat_g3_na_q2_0` — cluster 4, the "named form generated only as a distractor" family.
- **Root cause — a fourth distinct shape, worth naming:** the sub-case *is* generated, but only ever on
  the **wrong side of the answer key**. `money_peso.py`'s `read_write` has three tasks and `¢` sat in the
  `distractors` list of all three — including the sub-case that mentions centavos, which asks for the
  decimal form (`₱0.25` correct) and marks `25¢` wrong. **A notation a pupil only ever sees marked wrong
  is being taught against, not taught.**
- **Fix:** the `symbols` branch rotated two G3 sub-cases (peso-decimal, PhP code); now rotates three,
  adding the inverse question `"How is ₱0.25 written using the centavo sign?"` → `"25¢"`.
- **Files touched:** `dna/na/money_peso.py`, 1 review, `HARDENING_EVIDENCE.md`.
- **Verification:** seeds where `¢` is the **correct** answer **0/17 → 3/17** (46, 603, 604);
  `validate_matrix --node` on **all 8** money_peso nodes → 0 failures each;
  `run_all` → `EXIT_CODE=1`, matrix 151/151 / 0 failures, 0 non-judgment FAIL lines, contracts PASS.
- **Blast radius was contained by grade gating:** the change sits behind `grade == 3`, so the four G1
  and three G2 money nodes re-rendered **identically (0 stale each)** and their reviews stayed valid.
  Only `mat_g3_na_q2_0` was re-reviewed. **Gating a fix by grade is the cheapest way to keep a
  multi-node DNA's other reviews alive — prefer it when the competency difference is grade-scoped.**
- **Fresh blind re-review:** `mat_g3_na_q2_0` **FAIL → CONCERN**.
- **Commit:** `7944bf4`.

### Four defect shapes seen so far in Tick C — use this as the diagnosis checklist
1. **Key consumed but never declared/bound** (mass/capacity `unit`; properties-of-addition `task_type`)
   — the DNA reads a profile key nothing sets, so a default governs and branches are dead code.
2. **One text match too broad** (`"repeated addition"` matching both g2 nodes) — two competencies
   collapse onto one binding and render identically.
3. **Formatter gated off the node that needs it** (`array_grid_*` restricted to `find_product`) — the
   named model is structurally unreachable. Fixing this usually *also* requires task-specific stem text
   in the same tick, or you trade the coverage gap for a duplication bug.
4. **Named form generated only as a distractor** (`¢`) — present in the item, but never as the answer.
   **Check correct-answer counts separately from distractor counts.**

- **Next tick should:** keep taking self-contained FAILs. Suggested order:
  1. `mat_g2_na_q2_0` (**FAIL**, money) — blind review says "centavo coins never appear in any of 17
     samples" and one sample tests change-making with a nonsensical ₱0 item price. Same DNA I just
     touched, different grade branch, so the diagnosis is fresh in the file.
  2. `mat_g3_na_q4_0` (**FAIL**) — "Illustrate division through equal jumps on the number line and as
     inverse of multiplication"; 0 of 18 samples mention a jump, number line, or the inverse relation.
     Note this shares the missing number-line-jump machinery with `mat_g2_na_q3_1`, so building it once
     would clear two FAILs — that makes it the highest-yield remaining item, though it is genuinely new
     content and likely two ticks.
  3. `g3_mg_q1_0/_1/_2/_3` — the largest remaining duplication group (14–15 shared seeds).
  **Still unscheduled:** the Tick-A gate gap — `validate_judgment_reviews` skips `_validate_freshness`
  whenever `_validate_one` already returned an error, so a stale CONCERN/FAIL review is invisible.

---

## 2026-08-12 — **TICK C #7** — money value nodes; census unchanged, one blocker isolated

- **Census before:** PASS=57 CONCERN=61 FAIL=33. **After: PASS=57 CONCERN=61 FAIL=33 — unchanged.**
  Second tick in a row that improved content without clearing a verdict; that is a normal outcome
  when a node's FAIL rests on a sub-case that needs new machinery.
- **Unit of work:** `mat_g2_na_q2_0` (FAIL) and `mat_g1_na_q4_4` (CONCERN, same root cause).
- **Three defects, all found by following the binding:**
  1. **`operation` never bound** — both "Determine the value of..." competencies fell through every
     `money_peso` branch, so variant coverage could serve change-making (`"You paid ₱1 for an item that
     costs ₱0"`). Bound `operation="add_amounts"`.
  2. **`denomination_type` never bound** — DNA supported `coins_only`/`bills_only`/`mixed`, nothing set
     it. Bound sentinel `peso_sub_cases`; DNA rotates by seed.
  3. **The coin/bill boundary was defined twice with different comparisons** — label is
     `is_bill = denom >= 20` (so ₱20 prints as a *bill*), filter admitted `d <= 20` (so ₱20 was a
     *coin*). A "coins only" pile still showed a bill.
- **Files touched:** `registry.py`, `dna/na/money_peso.py`, 2 reviews, `HARDENING_EVIDENCE.md`.
- **Verification:** `peso coins only` **0 → 0 (rotation) → 6 (boundary fix)**; `peso bills only`
  **1 → 3**; change-making samples **1 → 0**; `validate_matrix --node` on **all 8** money_peso nodes
  → 0 failures; `run_all` → `EXIT_CODE=1`, matrix 151/151 / 0 failures, 0 non-judgment FAIL lines.
- **Fresh blind re-review:** `mat_g2_na_q2_0 FAIL → FAIL`, `mat_g1_na_q4_4 CONCERN → CONCERN`.
- **Commit:** `6d225c9`.

### A fifth defect shape for the checklist
5. **One boundary defined twice, with different comparisons.** Binding the sub-case correctly is not
   enough if the pool that implements it disagrees with the renderer about where the boundary sits.
   **After binding a discrete sub-case, verify the rendered text actually satisfies it** — don't trust
   that selecting `coins_only` produced coins. My own first check classified by numeric value and got
   the opposite answer to the reviewer, who classified by the sample's printed label. **The label is
   the ground truth; a student sees the label.**

### `mat_g2_na_q2_0` is now FAIL on exactly one blocker
Five of six findings PASS. The sole remaining defect: `"centavo coins only"` is one of the four
sub-cases its competency names and **0 of 14** samples mention any centavo denomination.
**Why it was not done:** `money_peso.py` stores centavo denominations as **centavo integers**
(`_DENOMS_G2_CENTAVOS = [25, 50]` meaning ₱0.25/₱0.50) while the pile/total pipeline is
**peso-integer** — dropping them into `denom_pool` totals them as pesos and labels them wrong
("2 ₱25 coins"). That constant is **referenced nowhere in the file** and has always been dead.
Serving centavo piles needs unit-aware render text in the money formatters, the same three-call-site
shape as the array-grid framing.

- **Next tick should:** pick from these, in descending value:
  1. **Centavo piles** (`mat_g2_na_q2_0`, the isolated blocker above) — clears a FAIL, and the
     diagnosis is complete: add a `centavos_only` pool plus a `denomination_unit` value threaded into
     the money render text (`money_peso.generate_hints`, `fmt_mcq`, `fmt_cloze`, `base_generator` —
     grep the peso label before editing, this framing is duplicated).
  2. `g3_mg_q1_0/_1/_2/_3` — the largest remaining duplication group (14–15 shared seeds), and
     duplication has been the most tractable shape so far.
  3. `mat_g3_na_q4_0` + `mat_g2_na_q3_1` — both need number-line-jump machinery; building it once
     clears two FAILs, but it is genuinely new content and likely two ticks.
  **Still unscheduled:** the Tick-A gate gap — `validate_judgment_reviews` skips `_validate_freshness`
  whenever `_validate_one` already returned an error, so a stale CONCERN/FAIL review is invisible.

---

## 2026-08-12 — **TICK A (second)** — content checks were skipping every non-PASS review

- **Census before:** PASS=57 CONCERN=61 FAIL=33. **After: PASS=57 CONCERN=60 FAIL=34.**
  **The FAIL count went UP by one, and that is the fix working** — a boilerplate review was
  understating a node's real state.
- **Why Tick A and not Tick C:** §3's Tick A trigger lists the three fabrication signatures known when
  the loop prompt was written (skeleton cluster > 3, phantom quotes, single `reviewed_by`); none fire.
  I ran it anyway on a **fourth, measured, live** signature: the gate was hiding a stale review on disk.
  Deriving state honestly is the point of §0, and a gate that lies makes every Tick C input unreliable.
  **Added to the §0 census: a staleness sweep.** Run it every tick — it is how this was found.
- **The defect:** `validate_judgment_reviews` did `if errs or not path.exists(): continue`, and
  `_validate_one` reports a non-PASS verdict **as an error** — so all 94 CONCERN/FAIL reviews were
  exempt from **freshness, quote provenance, skeleton clustering and reviewer plurality**. The
  anti-template checks built in the first Tick A had only ever run on all-PASS reviews.
- **Live proof at tick start:** `mat_g1_na_q1_7` (CONCERN) had a stale sample — seed 613 reviewed as
  `'Is 1 + 2 the same as 2 + 1?'`, now rendering `'Is 3 + 1 ...'` after my own `_carry_free_addends`
  change — while the full gate reported **0 stale**.
- **Fix:** only an absent or unreadable review is skipped; anything that parses gets every content
  check regardless of verdict or schema errors.
- **The pass rule is untouched and was verified.** `run_all` still cannot exit 0 with any CONCERN/FAIL:
  enforced both in `validate_judgment.py` (every non-PASS verdict is an error) and at
  `run_all.py:146` (`if v["FAIL"] > 0 or v["CONCERN"] > 0`). After the change, 286 non-PASS verdict
  errors still reported. The new regression test asserts this explicitly so the fix cannot be undone
  in a way that weakens it.
- **What it caught immediately:** `mat_g3_mg_q1_5`'s `scale_appropriateness` rationale was **copied
  verbatim** from `mat_g3_mg_q1_4`. Both non-PASS, so the verbatim-reuse check had never run on either.
  Deleted and re-reviewed blind → **CONCERN → FAIL**: its competency is *"Recognize **and draw**
  parallel, intersecting, and perpendicular lines"* and the draw verb is exercised **0 of 10** times.
- **Verification:** `pytest tests/unit/ -q` → 293 passed, 2 failed (the long-standing
  `_FORMATTER_ROUTES` ImportErrors, unrelated); `run_all` → `EXIT_CODE=1`, matrix 151/151 / 0 failures,
  0 non-judgment FAIL lines, contracts PASS; **gate errors 288, of which non-verdict errors: 0**;
  **stale reviews: 0**.
- **Mutation-checked the new test** rather than trusting green: under the old loop the phantom quote is
  missed, under the new one it is caught.
- **Commit:** `6c368c8`.

### The tree is now in a clean, fully-legible state
Every remaining gate error is a non-PASS verdict. Nothing is hiding: no stale review, no boilerplate,
no phantom quote, no template skeleton, no reviewer over quota. `run_all`'s distance from exit 0 is
exactly the 94 nodes' worth of honest content debt, which is what it should be.

- **Next tick should:** back to **Tick C**. Highest value first:
  1. **`mat_g3_mg_q1_5`** — the FAIL just uncovered. "Draw" is 0/10; check whether a draw/construct
     formatter exists for `geometric_lines` before assuming new content is needed (the array-grid
     precedent: the formatter existed and was simply gated off).
  2. **Centavo piles** for `mat_g2_na_q2_0` — diagnosis complete in the previous entry; clears a FAIL.
  3. `g3_mg_q1_0/_1/_2/_3` — largest remaining duplication group, and its `q1_4`/`q1_5` pair is now
     known to be similar enough that a reviewer copied a rationale between them.
  Defer still: number-line-jump machinery (`mat_g2_na_q3_1` + `mat_g3_na_q4_0`, two FAILs, one build).

---

## 2026-08-12 — **TICK C #8 — FINAL TICK. THE LOOP WAS STOPPED HERE BY THE USER.**

- **Census before:** PASS=57 CONCERN=60 FAIL=34. **After: PASS=57 CONCERN=61 FAIL=33.**
- **Unit of work:** centavo piles for `mat_g2_na_q2_0` — the single blocker isolated in Tick C #7.
- **Root cause:** `_DENOMS_G2_CENTAVOS = [25, 50]` stores **centavo integers** while the pile pipeline
  is **peso-integer**, so the constant was referenced nowhere and had always been dead.
- **Fix:** keep a centavo pile **homogeneous** (denominations, total and labels all centavos) so the
  scales never mix; carry a `denomination_unit` value so both money description sites print the right
  unit. A centavo piece is always a coin, so the ₱20 bill/coin threshold is not applied to it.
- **The bug the fix exposed (worth remembering):** first attempt rendered five seeds as the identical
  `2 25¢ coins`. `max_total` arrives in **pesos** after difficulty interpolation and can be below 50,
  while the smallest centavo pile is 2×25 = 50 — so all candidates were filtered out and the
  "two of the smallest denomination" fallback fired every time. **A unit-scoped ceiling must be
  converted before it can cap a pile in that unit.**
- **Verification:** centavo samples **0/17 → 6/18**, distinct stems 5 of 6, totals 75–400;
  `validate_matrix --node` on all 8 money_peso nodes → 0 failures; `run_all` → `EXIT_CODE=1`,
  matrix 151/151 / 0 failures, 0 non-judgment FAIL lines, contracts PASS; **stale 0, non-verdict gate
  errors 0**.
- **Fresh blind re-review:** `mat_g2_na_q2_0` **FAIL → CONCERN**.
- **Commit:** `1da0ea7`.
- **Note:** `mat_g3_mg_q1_5` was investigated first and **rejected as a tick** — `geometric_lines`
  declares only `["mcq", "categorize"]`, compatibility offers only `["mcq"]`, `visual_home=None`, and
  **no line-drawing formatter exists anywhere**. Unlike the array-grid case, its "draw" gap is genuinely
  new machinery, not a gate to open.

## LOOP STOPPED — 2026-08-12

The recurring job (`ac0f9ef5`, every 30 min) was **cancelled** at the user's request. Working tree is
clean, `main` is committed. **Note: `1da0ea7` is committed but NOT pushed** — everything up to
`6c368c8` is on `origin/main`; this last commit is local only.

### State at stop
```
census        57 PASS / 61 CONCERN / 33 FAIL   (151 reviewed, 0 unreviewed)
run_all       EXIT_CODE=1 — red only at 6/6, on 290 non-PASS verdict errors
              matrix 151/151, 0 failures; 0 non-judgment FAIL lines; contracts PASS
gate health   stale 0 · non-verdict errors 0 · skeleton cluster 2 · quote failures 0 · 18 reviewers
```
Every remaining gate error is an honest non-PASS verdict. Nothing is hiding.

### To resume
Re-arm with `/loop 45m Read local_only/scratch/hardening_loop_prompt.md and execute exactly one tick
per its protocol...`. Start at §0, and **include the staleness sweep** — it is not in the loop prompt's
§0 block but it is how the gate's biggest blind spot was found.

### Highest-value remaining work, in order
1. **`g3_mg_q1_0/_1/_2/_3`** — largest untouched duplication group (14–15 shared seeds). Duplication has
   been the most tractable shape; five of the eight fixes so far were duplication or unbound keys.
2. **Number-line-jump machinery** — `mat_g2_na_q3_1` and `mat_g3_na_q4_0` both FAIL on it; building it
   once clears two FAILs. Genuinely new content, budget two ticks.
3. **Line-drawing formatter** — `mat_g3_mg_q1_5`'s "draw" verb, 0/10. Also new machinery.
4. **The 61 CONCERNs are almost entirely untouched.** Every Tick C so far targeted FAILs.

### The five defect shapes found (diagnosis checklist — this is the most reusable output)
1. **Key consumed but never bound** — DNA reads a profile key nothing sets; a default governs and the
   real branches are dead code. (mass/capacity `unit`; properties-of-addition `task_type`; money
   `operation` and `denomination_type`.)
2. **One text match too broad** — two competencies collapse onto one binding and render identically.
   (`"repeated addition"` matching both g2 nodes.)
3. **Formatter gated off the node that needs it** — the named model is structurally unreachable.
   Opening the gate usually *also* requires task-specific stem text in the same tick, or you trade a
   coverage gap for a duplication bug. (`array_grid_*` restricted to `find_product`.)
4. **Named form generated only as a distractor** — present in the item, never as the answer. Check
   correct-answer counts separately from distractor counts. (the centavo sign.)
5. **One boundary defined twice, with different comparisons** — binding a sub-case is not enough if the
   pool disagrees with the renderer about where the boundary sits. Verify the *rendered text* satisfies
   the sub-case; the printed label is ground truth, not the numeric value. (coin/bill at ₱20.)

---

## 2026-08-13 — Tick C (unit 1 of the queue: the six fixture re-declarations)

- **Census before:** PASS=57 CONCERN=61 FAIL=33 (151 reviewed, 0 unreviewed)
  (gate: non-verdict=0 · skeleton cluster=1 · phantom quotes=0)
  `run_all` EXIT_CODE=1, red only at 6/7 and 7/7. Tick 0 and Tick A correctly did not fire.
- **Unit of work:** re-declared the six fixture nodes from a blind Declarer (§2b's named first
  item), diffed against the sighted originals, and re-keyed `CAPABILITY_PROVIDERS` to only the
  mappings rendered evidence earns.
- **Root cause:** `_provided_for_node` measured reachability against `VARIANTS_BY_DNA` — what a
  DNA *declares* — while the student path applies `_parse_competency_bounds`' per-node clamp.
  On any node whose competency is narrower than its DNA, §6C could report a capability as
  provided by a variant value the student path can never select.
- **Machinery built:** none (no new formatter/variant/axis/DNA). Check strengthened:
  `_provided_for_node` now intersects declared variants with the node's competency bounds, via a
  new `_bound_restricts_to` that treats a scalar/list bound as a restriction and a 2-tuple as a
  continuous range (never a discrete pair). Two diagnostic probes promoted to `tests/pgen_probes/`.
- **Files touched:** `backend/app/practice_gen/validation/validate_capability.py`,
  `data/skeletons/vocab_annotation.json`, `data/knowledge_graph_g1_3.json`,
  `validation_reports/HARDENING_EVIDENCE.md`, `tests/pgen_probes/{collapse,variant_binding}_probe.py`
- **Verification:**
  - `run_all` → `Nodes Checked: 151 / Nodes Passed: 151 / Nodes Failed: 0 / Total Failures
    Observed: 0`, all ten contract checks executing, stages 1–5 all PASS, `EXIT_CODE=1` red only
    at 6/7 (291 judgment) and 7/7 (163 capability). No regression.
  - Re-introducing the flagged `distinguish_shapes -> task_type=identify_name` mapping in memory
    now fails §6C unaided: `caught the unreachable-value mapping: True`.
- **Census after:** PASS=57 CONCERN=61 FAIL=33 (unchanged — no generator content changed).
  Capability gaps **10 → 18**; undeclared nodes unchanged at 145.
- **Commit(s):** `63e769e` fix(capability): measure §6C reachability on the student path, not on
  DNA declarations

### The measurement §2b asked for — is the Declarer separation worth its cost?

**Yes, and it is now measured.** The blind Declarer saw only the six competency sentences (no
file tools at all) and:

- passed §6A (provenance) and §6B (coverage) with **zero failures**, never having seen the checker;
- **never declared fewer** requirements than the sighted author;
- declared **more on four of six nodes** (+5 total: g1_na_q1_0 5→7, g1_mg_q1_1 5→6,
  g3_mg_q2_3 4→5, g3_dp_q3_1 5→6).

The divergence is entirely one-directional — under-declaration by the sighted author. The two
nodes where they agreed (g2_na_q3_1, g3_mg_q1_5) are the two whose competency enumerates its own
list, leaving no room to quietly drop anything. **Every gap §2b listed as provisional survives
blind re-declaration, so the build queue is confirmed rather than provisional.**

### The wrong turn, recorded on purpose

My first probe forced each declared variant value and called any key whose values all rendered
identically "dead". On that basis I removed three earned mappings and wrote that `mat_g3_mg_q2_3`
"hardcodes mL so liters never render". **That was wrong** — the identical renderings were the
competency-bound clamp working, and a census of *unforced* output shows L in 103 of 200 seeds and
mL in 97. Mappings restored. `collapse_probe.py` now prints each key's bound and labels results
`CLAMPED` (expected) vs `!! DEAD` (candidate), so the two cannot be confused again.

Second false alarm, same session: `problem["format"]` is the *interaction* format (`read_mcq`,
`set_fill_in_blank`), **not** the formatter name. Comparing it to a formatter name made
array_grid look unreachable for `mat_g2_na_q3_1`; it is reachable (22 of 100 seeds).

### Next tick should:

**Declare-first is now cheap and proven — start every Tick C with a blind Declarer batch.** The
highest-value next unit is the **`mat_g3_mg_q1_0/_1/_2/_3` duplication cluster** (queue item 1,
still untouched): three CONCERNs whose rationales name the same cause — sibling nodes rendering
identical items for the same seed (`q1_1` reuses `q1_0`'s 2×7 grid on seed 42; `q1_2` seed 604
and `q1_3` seeds 55/500 serve the sibling's item verbatim). That is defect shape #2, one text
match too broad in `_parse_competency_bounds`, and it is a plain Tick C.

Then the two Tick Fs, both confirmed by blind declaration: `equal_jumps_on_a_number_line`
(`mat_g2_na_q3_1` + `mat_g3_na_q4_0`) and `draw_line_relationships` (`mat_g3_mg_q1_5`).
For the number line, **start from `fmt_number_line.py`, which already renders a single hop**
(`hop_from`/`hop_by`, grade-3 branch at :157) and is routed twice in `adapter.py`
(`number_line_read` :102, `number_line_set` :188). Extending it to *repeated equal* jumps is the
change; note the frontend arc renderer at `frontend/src/App.jsx:1435` draws one arc and will need
the same extension, so budget backend + frontend.

Also live, from `tests/pgen_probes/collapse_probe.py`: **23 unclamped collapsed value pairs**
across the six fixtures — `mat_g2_na_q3_1`'s `table` key (5 declared values → 1 rendering) and
`mat_g3_mg_q2_3`'s `unit` key (4 → 1) are the two largest, and both are unclamped, so unlike the
clamped collapses they are genuine candidates.

---

## 2026-08-13 — Tick C (the g3_mg_q1 area cluster — queue item 1)

- **Census before:** PASS=57 CONCERN=61 FAIL=33 (gate: non-verdict=0, skeleton cluster=1, quotes=0)
  `run_all` EXIT_CODE=1, red only at 6/7 and 7/7. Tick 0 / A / B correctly did not fire.
- **Unit(s) of work:** declared the six `mat_g3_mg_q1_*` nodes from a blind Declarer, then fixed
  the area cluster's sibling duplication at its root and re-reviewed all four nodes blind.
- **Root cause:** `_parse_competency_bounds` bound `task_type` for only two of the `area` DNA's
  four nodes. `mat_g3_mg_q1_2` and `mat_g3_mg_q1_3` fell through to `area.py`'s own
  `profile.get("task_type", "find_area")` default, leaving them differing **only by `context`** —
  which any context-blind formatter ignores. Defect shape #1.
- **Machinery built:** none new. Changed: registry bindings for two nodes (one via a per-seed
  string sentinel, resolved in the DNA); `grid_area` re-routed from `find_area` to
  `illustrate_tiles`; `find_missing_dimension` restricted to rectangles; two silent defaults
  deleted in favour of named raises; one duplicate registry key removed; new AST guard at
  `tests/pgen_probes/duplicate_registry_keys.py`.
- **Files touched:** `registry.py`, `compatibility.py`, `adapter.py`, `dna/mg/area.py`,
  `generators/base_generator.py`, `data/skeletons/vocab_annotation.json`,
  `data/knowledge_graph_g1_3.json`, `tests/pgen_probes/duplicate_registry_keys.py`,
  `validation_reports/HARDENING_EVIDENCE.md`, four review JSONs.
- **Verification:**
  - sibling duplication, all six pairs × 200 seeds → `0 identical of 200` on every pair
  - `validate_matrix --node` × 4 → PASS, PASS, PASS, PASS
  - stray `?` placeholders across 400 seeds of `mat_g3_mg_q1_3` → `0`
  - `run_all` → `Nodes Checked: 151 / Passed: 151 / Failed: 0 / Total Failures Observed: 0`,
    all ten contract checks executing, 67 PASS stage lines, `EXIT_CODE=1` red only at 6/7 and 7/7
  - gate → `NON-VERDICT errors: 0`
- **Census after:** PASS=56 CONCERN=61 FAIL=34. **The count got worse, and that is the system
  working**: `mat_g3_mg_q1_0` moved PASS→CONCERN under a fresh reviewer that had never seen the
  old verdict, and `mat_g3_mg_q1_3` stayed FAIL but for an entirely different reason.
  Capability: undeclared 145→139, gaps 18→59 (the six new declarations, none of them mapped).
- **Commit(s):** `618bea7` fix(pgen): bind task_type for all four area nodes

### What the blind re-review actually bought

The first pass of reviewers worked from packets built *before* the last generator fix. The gate
caught it precisely — **only `mat_g3_mg_q1_3` was stale**, on exactly the five seeds the fix
changed — and rejected nothing else. My own ad-hoc staleness check had flagged all four nodes;
it was wrong, because `judgment_packets` renders seeds ≥500 under forced difficulty profiles
that a plain `run(...)` does not reproduce. **Trust the gate's freshness check, not a hand-rolled
re-render.**

`mat_g3_mg_q1_3` was then re-reviewed on a fresh packet by a reviewer that never saw the old
review. It is still FAIL — but the old FAIL was the `?` placeholder (now fixed and gone from the
rationale), and the new FAIL is `scale_appropriateness`: seed 501 needs 924 ÷ 22 and seed 602
needs 216 ÷ 18, two-digit divisors past Grade 3 Q1.

### Next tick should:

**Grade-3 magnitude control is now the single highest-value cluster, and three independent blind
reviewers converged on it without conferring.** Every one of the four area nodes was marked down
for scale:
- `q1_0` — seed 501's `12 rows and 12 columns` = 144, a two-digit × two-digit product
- `q1_1` — same 12×12
- `q1_2` — seed 502's 42×42 = 1764, seed 604's 14×26
- `q1_3` — 924 ÷ 22, 216 ÷ 18, 16×16, 20×20

These come from `_PARAM_BOUNDS["g3"]` in `dna/mg/area.py` (`side_cm_max`, `side_m_max`,
`side_cm_max_tiling`), which the max-difficulty seeds (≥500) drive to their ceiling. One bounds
fix plausibly clears findings on all four nodes at once — the same shape as this tick's fix, one
level up. Check the G3 Q1 multiplication table range in the knowledge graph before choosing the
new ceiling; do not guess it.

Second, smaller and also convergent: **the garden word problems never state the tile size**, so
`q1_0` seed 601 and `q1_3` seed 42 only key correctly if a tile is silently 1 unit square. Two
reviewers flagged it independently. And `q1_3` seeds 43/603 are the identical 16 cm square item.

Still open and untouched, both confirmed by blind declaration: `equal_jumps_on_a_number_line`
(`mat_g2_na_q3_1` + `mat_g3_na_q4_0`) and `draw_line_relationships` (`mat_g3_mg_q1_5`), plus
`mat_g3_mg_q1_1`'s real competency gap — "Explore **inductively** the derivation" is still served
by stems that hand the rule over (`Using the formula rows × columns, ...`), which no binding can
fix and which needs a genuine multi-case inductive item. That is a Tick F.

---

## 2026-08-13 — Tick C (G3 area magnitudes) — **CUT SHORT BY THE 5-HOUR USAGE LIMIT**

- **Census before:** PASS=56 CONCERN=61 FAIL=34 (gate: non-verdict=0)
  `run_all` EXIT_CODE=1, red only at 6/7 and 7/7. Tick 0 / A / B correctly did not fire.
- **Unit of work:** gated the `area` DNA's dimensions to the multiplication tables the student
  actually holds at G3 Q1, and fixed a second site where the array formatter fabricated its own.
- **Root cause:** an area is a multiplication, but sides were drawn from a free `randint(2, 50)`
  band scaled by difficulty, with nothing tying the draw to the taught tables. The harder the
  item, the more certainly it required an untaught table.
- **Ground truth (read, not guessed — the previous handoff's instruction):**
  `mat_g3_mg_q1_2.cumulative_concepts` has `multiplication_tables_2_3_4_5_10` and
  `division_tables_2_3_4_5_10`; `mat_g3_na_q3_0` **(G3 Q3)** introduces
  `multiplication_tables_6_7_8_9`; `mat_g3_na_q3_2` (G3 Q3) introduces 2-3 digit × 1-digit.
  All four area nodes are **G3 Q1**, so the 6/7/8/9 tables are two quarters away and multi-digit
  × multi-digit is not in Grade 3 at all. This was a Content Rule 1 violation, not a taste call.
- **Machinery built:** none new. `_table_and_cofactor` in `dna/mg/area.py` (one side always from
  `_KNOWN_TABLES = (2,3,4,5,10)`, the other 2..10; difficulty widens the pool, never past the
  curriculum; the inverse task's divisor is pinned to the table factor). Missing **square**
  branch added to `fmt_array_grid.format_array_grid`.
- **Files touched:** `dna/mg/area.py`, `formatters/visual/fmt_array_grid.py`,
  `validation_reports/HARDENING_EVIDENCE.md`, two review JSONs.
- **Verification:**
  - violations outside the 2,3,4,5,10 tables: `23/120, 26/120, 28/120, 31/120` → **`0/220` on all four**
  - fabricating fallback reachability across all 24 array_grid nodes:
    `NONE — every array now takes its dimensions from the DNA`
  - `validate_matrix --node` PASS on the four area nodes and on four array_grid consumers
    spanning the G2Q3 / G3Q3 boundary
  - `run_all` → 151/151, 0 failures, all ten contract checks, stages 1–5 green, EXIT_CODE=1 red
    only at 6/7 and 7/7
  - variety preserved: `mat_g3_mg_q1_3` 89 distinct stem shapes, dimensions [2,3,4,5,6,7,8,10]
- **Census after:** PASS=56 CONCERN=60 FAIL=35 (q1_1 CONCERN→FAIL under a fresh reviewer).
- **Commit(s):** see below.

### ⚠️ RESUMPTION POINT — the next tick's FIRST item, before anything else

**`NON-VERDICT` is 29, not 0.** The tick was killed by the usage limit part-way through the
re-review step. Two of the four reviewers finished, two did not:

```
mat_g3_mg_q1_0  re-reviewed after G3 table gating   ✓ fresh   (CONCERN)
mat_g3_mg_q1_1  re-reviewed after G3 table gating   ✓ fresh   (FAIL)
mat_g3_mg_q1_2  still last tick's review            ✗ STALE  (15 freshness errors)
mat_g3_mg_q1_3  still last tick's review            ✗ STALE  (14 freshness errors)
```

The generator change is complete, verified and committed; only the *reviews* of `q1_2` and
`q1_3` lag the content. **Re-review those two blind before any new content work** — §0 says a
non-zero NON-VERDICT count must be cleared first, because a review describing content the
pipeline no longer serves will send you chasing a defect that is not there. Fresh packets are
already built at `local_only/scratch/`-adjacent scratch paths; rebuild them rather than reusing,
since the tick may have moved on. Do **not** hand-edit those two files — that is the fabrication
failure mode this repo has suffered twice.

### Next tick should, after clearing the two stale reviews:

`mat_g3_mg_q1_1` is now **FAIL** on a fresh reviewer, and its competency gap is the real one:
"Explore **inductively** the derivation of the formulas" is still served by stems that hand the
rule over (`Using the formula rows × columns, ...`). No binding fixes this — it needs a genuine
multi-case inductive item, where the student compares several tilings and states the rule. The
blind Declarer independently said the same ("a generator that shows one tiled rectangle and
states the formula does not satisfy it; it needs a multi-case sweep"). **That is a Tick F.**

Still open and untouched, both confirmed by blind declaration: `equal_jumps_on_a_number_line`
(`mat_g2_na_q3_1` + `mat_g3_na_q4_0`, start from `fmt_number_line.py`'s existing single hop at
:157 and note the frontend arc renderer at `frontend/src/App.jsx:1435`) and
`draw_line_relationships` (`mat_g3_mg_q1_5`).

---

## 2026-08-13 — Tick C (cleared the stale reviews, then the indeterminate word problem)

- **Census before:** PASS=56 CONCERN=60 FAIL=35. **Gate: NON-VERDICT=29** — the previous tick's
  resumption point, `mat_g3_mg_q1_2` and `_3` describing content the generator no longer served.
- **Unit 1 — cleared the stale reviews (§0's precondition).** Both re-reviewed blind on freshly
  built packets by a reviewer that saw neither the generator nor the previous verdicts.
  **NON-VERDICT 29 → 0.** `mat_g3_mg_q1_3` moved **FAIL → CONCERN**: the reviewer independently
  confirmed last tick's table gating landed, listing every inverse division in its packet
  (15/5, 8/4, 21/3, 30/5, 28/4, 24/3, 18/3, 24/4 — all inside the 3/4/5 tables, every quotient
  single-digit) and scoring `scale_appropriateness` PASS.
  Commit `6661ec4`.
- **Unit 2 — the tiling word problem had no determinate answer.**
  - **Root cause:** `spines.py` `_AREA_SOLVE` read "...with square tiles. How many tiles are
    needed to cover it completely?" — never stating the tile size. The keyed count is only
    correct if the reader silently assumes a 1-unit tile. **Two independent blind reviewers
    flagged this on different nodes in different ticks without conferring**, which is what marks
    it as a correctness defect in the item rather than a phrasing preference.
  - **Fix:** the spine now states "with square tiles that are 1 {length_unit} on each side"; both
    of area.py's shape branches already set `length_unit`. The garden narration is pinned to
    metres (blind review: "gardens at 5 cm x 2 cm, 3 cm per side" are unpicturable).
  - **A correction made mid-fix:** pinning on `context == "word_problem"` alone was too broad —
    `q1_3`'s *inverse* items render in the plain frame, not as a garden, so the first version made
    that node render metres **300/300** and threw away half its unit variety. Narrowed to exclude
    `find_missing_dimension`; it now reads 231 m / 69 cm.
  - **Verification:** across 300 seeds per node — **156 garden items, 0 without a stated tile
    size, 0 measured in centimetres**; `q1_2` still carries both units its competency names
    (152 cm / 148 m). `validate_matrix --node` PASS ×4. `run_all` 151/151, 0 failures, all ten
    contract checks, stages 1–5 green, EXIT_CODE=1 red only at 6/7 and 7/7.
  - Commit `82d0e8e`.
- **Census after:** PASS=56 CONCERN=61 FAIL=34.

### ⚠️ RESUMPTION POINT — first item next tick

**NON-VERDICT is 9**, not 0: the Unit 2 spine change made all four area reviews stale
(`q1_0` 1, `q1_1` 1, `q1_2` 1, `q1_3` 6). Two blind reviewers were dispatched on fresh packets
(`t5_*.json`) and were still running when the tick ended. **Rebuild the packets and re-review all
four blind before any new content work** — §0 requires NON-VERDICT to be 0 first. Do **not**
hand-edit those files.

This is the second tick running where a content fix outran its reviews. The pattern is now clear
and worth planning around: **any spine or DNA change invalidates every review of every node that
DNA serves**, so budget the re-review as part of the fix, not after it — a four-node cluster costs
roughly two reviewer dispatches, and they are slow.

### Next tick should, after clearing the stale reviews:

`mat_g3_mg_q1_1` is **FAIL** on a fresh reviewer and its gap is the real one: "Explore
**inductively** the derivation of the formulas" is still served by stems that hand the rule over
(`Using the formula rows × columns, what is the total number of tiles?`). No binding fixes this —
it needs a genuine multi-case inductive item where the student compares several tilings and states
the rule, and the answer object is a *formula*, not a number. The blind Declarer said the same
independently ("it needs a multi-case sweep"). **That is a Tick F**, and it is the last thing
standing between this cluster and a clean set.

Also still open, both confirmed by blind declaration and untouched:
`equal_jumps_on_a_number_line` (`mat_g2_na_q3_1` + `mat_g3_na_q4_0` — start from
`fmt_number_line.py`'s existing single hop at :157, and note the frontend arc renderer at
`frontend/src/App.jsx:1435` draws one arc) and `draw_line_relationships` (`mat_g3_mg_q1_5`).

### Tick addendum — the re-review landed and caught two regressions from this cluster's own fixes

Both reviewers finished after the ledger above was written. Their findings were **not** the
expected "still CONCERN for known reasons" — both named defects **introduced by fixes made in
this same cluster**, which is the argument for re-reviewing rather than assuming a fix is clean:

1. **Squares lost their dimension label.** `fmt_array_grid`'s read-mode stem tested
   `shape_type == "rectangle"`, so the square figures the earlier square branch started sending
   through fell to the generic "Look at the shaded shape." — `mat_g3_mg_q1_0` seed 500 became a
   10×10 figure with 100 correct, no dimensions, distractors 97/101/102. Fixed.
2. **Centimetre gardens survived in two places.** The metres pin ran *after* the tiling branch
   had forced `square_cm`, and a **forced `unit` variant** bypasses it entirely. Two fixes, since
   there were two causes: branch order corrected, and the **surface noun now follows the unit**
   ("a square card measuring 5 cm on each side" rather than a 5 cm garden). Overriding a forced
   variant would have fought the variant system; renaming the surface does not.

Verified: array items 38 / unlabelled stems **0**; tiling surfaces 171 / cm gardens **0**;
matrix 151/151, 0 failures; stages 1–5 green. Commits `2d7ea6a`, `68c5f2f`.

**Measured census after all four fresh reviews: PASS=56 CONCERN=61 FAIL=34.**
(An earlier draft of this entry stated 56/62/33 and NON-VERDICT=8 — those were written before
the measurement and were wrong. The figures here are the ones `validate_judgment` actually
returned. Do not trust a number in this ledger that is not accompanied by the command that
produced it.)

**NON-VERDICT is 4**, not 0 — `mat_g3_mg_q1_0` 2, `mat_g3_mg_q1_1` 1, `mat_g3_mg_q1_3` 1
(the last two fixes restaled those reviews again). Same handoff as above,
unchanged: **rebuild packets and re-review all four blind before any new content work.** This is
now the third consecutive tick where a content fix outran its reviews — the lesson is recorded
above and is worth acting on rather than repeating: for a four-node cluster, plan the fix and its
re-review as one unit, and expect the reviewers to be slow (both took ~55 min this tick).

Known remaining findings on the cluster, from the fresh reviews, for whoever picks this up:
- `q1_1` **FAIL** — the inductive-derivation gap. Tick F. Unchanged and unaffected by any of this.
- `q1_2` CONCERN — seeds 50/500 byte-identical; 13 of 14 samples use one of two frames.
- `q1_0` CONCERN — was the "shaded shape" stem, now fixed; needs re-review to confirm.

---

## 2026-08-13 — Tick C + **Tick F** (the area cluster clears its last FAIL)

- **Census before:** PASS=56 CONCERN=61 FAIL=34. Gate: **NON-VERDICT=4** (the inherited
  resumption point — seeds 500/601/601/603, exactly what the previous tick's fixes changed).
- **Unit 1 — cleared the stale reviews.** Three nodes re-reviewed blind. NON-VERDICT 4 → 0.
- **Unit 2 — Tick F: built the inductive derivation for `mat_g3_mg_q1_1`.**
  - **The gap, named twice independently.** A blind reviewer scored it FAIL ("No sample derives
    anything... no correct answer is ever a formula"), and §6C named the same four capabilities as
    unprovided *from the competency sentence alone* (`explore_pattern_across_cases`,
    `reason_inductively_from_cases`, `derive_area_formula`, `area_formula_expression`). Two
    instruments, one reading rendered content and one reading the curriculum, agreeing.
  - **Step 1 said don't build what exists.** `fmt_fill_in_table` exists and is routed; more to the
    point, `mcq` already supports a *string* answer with string distractors
    (`values["distractors"]`, the mechanism `shapes_2d` uses). **No new formatter was needed** —
    the gap was in the DNA and the stem, which is the "most missing machinery isn't" lesson.
  - **Built:** an `area.py` `derive_formula` branch returning three tiled cases and keying the
    *rule*; a `base_generator` stem that shows the cases and asks which rule always works, and
    **raises** if cases are absent rather than falling back. "Formula**s**" is plural in the
    competency, so the shape decides: rectangle → `length × width`, square → `side × side`.
  - **Verified:** 107 / 93 split across 200 seeds, 0 items whose stem contains the keyed answer.
  - Commit `4e71789`.
- **Unit 3 — the capability contract for the cluster.** Registered the area providers with a
  rendered sample behind each (Rule 9). **Total gaps 59 → 30; the area cluster reaches 0.**
  Also fixed a hole this exposed in §6C itself: `mat_g3_mg_q1_3` is bound to a per-seed
  **sentinel** that is deliberately not a Lab-selectable variant, so intersecting
  `VARIANTS_BY_DNA` with the bound reported it as having *no reachable task_type at all* — the
  opposite of the truth. A bound the registry pins is now reachable by construction; the clamp
  still excludes what the bound excludes, so the Rule 9 defeat stays caught (re-verified).
- **Unit 4 — polish the new item**, on its own re-review's findings: article agreement
  ("a 8 by 2 rectangle") and a bracketed distractor `2 × (length + width)` using grouping symbols
  no stem at this grade uses. Commit `6686385`.
- **Census after: PASS=56 CONCERN=62 FAIL=33.** `mat_g3_mg_q1_1` **FAIL → CONCERN** — the
  reviewer scored fulfilment, coverage and alignment all PASS on the new item. **The whole
  g3_mg_q1 area cluster is now CONCERN with no FAIL.**
- `run_all`: 151/151, 0 failures, all ten contract checks, stages 1–5 green, capability failures
  198 → 169.

### The stale-packet race solved itself this tick — do this deliberately from now on

Three ticks running, a content fix has outrun its reviews. This tick the reviewer was handed a
`q1_1` packet built before the derive_formula rewrite, **noticed all 13 seeds failed freshness,
rebuilt the packet itself, and re-reviewed against what actually renders** — its first pass had
scored FAIL on the stale content. **Put "verify packet freshness before scoring, and rebuild if
stale" in every reviewer prompt.** It converts this race from a silent wrong verdict into a
self-correcting one, and it cost nothing.

### ⚠️ RESUMPTION POINT

**NON-VERDICT is 5**, all on `mat_g3_mg_q1_1` — Unit 4's polish restaled its review. Rebuild the
packet and re-review that one node blind before new content work.

### Next tick should:

The area cluster is done with FAILs; what remains there is `variant_comprehensiveness` on all
four (single sentence frames) and `q1_0`'s `competency_fulfillment` CONCERN — the reviewer's
sharpest remaining point: *"the estimate half is only a word — seed 50 says 'Estimate how many
unit tiles cover the square in all' while offering 15, 16 and 17, so no estimation strategy
separates them and the item silently demands an exact product."* That is a real competency gap
("Illustrate **and estimate**"), and fixing it means distractors far enough apart that estimating
actually discriminates.

Then the two remaining named Tick Fs, both still untouched and both confirmed by blind
declaration:
- `equal_jumps_on_a_number_line` (`mat_g2_na_q3_1` + `mat_g3_na_q4_0`) — start from
  `fmt_number_line.py`'s existing single hop (grade-3 branch, `hop_from`/`hop_by`); note
  `frontend/src/App.jsx:1435` draws one arc and will need extending too.
- `draw_line_relationships` (`mat_g3_mg_q1_5`) — `geometric_lines` offers only `["mcq"]`;
  check `fmt_shape_board.py` before building new.

**30 capability gaps remain across the tree, and 139 nodes are still undeclared** — declaring a
node is cheap (a blind Declarer, competency text only) and repeatedly turns out to name the
defect outright before any sample is read.

---

## 2026-08-13 — Tick C (two correctness fixes, and a blind spot found in the freshness check)

- **Census before:** PASS=56 CONCERN=62 FAIL=33. Gate: **NON-VERDICT=5** (`mat_g3_mg_q1_1`, the
  inherited resumption point).
- **Unit 1 — cleared the stale review.** `q1_1` re-reviewed blind, with the freshness-verification
  step added to the prompt (the ledger's recommendation last tick). The reviewer reported
  `stale seeds: []` before scoring, so its verdict is about current content and nothing else.
- **Unit 2 — the inductive item admitted two correct answers.** The reviewer scored `q1_1` FAIL
  on a real logical flaw in the item built last tick:
  > "at width 2 the distractor `length + length` is mathematically identical to `length × width`.
  > Seed 42 (`4 by 2` → 8, `7 by 2` → 14, `9 by 2` → 18) ... each have two answers consistent with
  > all presented evidence."

  A pupil who induced faithfully from all the evidence was marked wrong. Fixed by never drawing a
  fixed width of 2 — **and**, because the property is general, by checking it rather than assuming
  it: `_RULE_VALUES` gives each distractor its arithmetic and `_assert_cases_determine` raises,
  naming seed/distractor/cases, if any distractor reproduces the keyed total on every case.
  Guard verified to fire on the reviewer's exact case set and pass a well-posed one; 500
  consecutive seeds generate with it never firing. Commit `711aded`.
- **Unit 3 — "estimate" was only a word (`q1_0`).** Competency: "Illustrate **and estimate** the
  area ... using square tile units", but seed 50 offered 15, 16, 17 against an answer of 16.
  Two layers: the DNA supplied no distractors for `illustrate_tiles`, so the shared error patterns
  governed and `fmt_mcq` padded with ±1; and fixing that alone still left 10 of 212 items close,
  because error-pattern distractors are appended afterwards and can land anywhere — a 3×7 tiling's
  perimeter 2×(3+7)=20 sits **4.8%** from the area 21. Fixed with misconception-based distractors
  held a fifth of the answer apart, plus the same separation rule applied where options are
  finally assembled. **10 → 0 of 212**; smallest relative gap 0.200. Commit `65a66be`.
- `run_all`: 151/151, 0 failures, all ten contract checks, stages 1–5 green, throughout.
- **Census after:** PASS=56 CONCERN=61 FAIL=34 (`q1_1`'s honest fresh FAIL from Unit 1).

### ⚠️ A blind spot in the freshness check — the next tick's first item

**The freshness check compares `question_text` only. It does not compare the options.** Unit 3
changed `q1_0`'s options completely while leaving every stem byte-identical, so:

```
mat_g3_mg_q1_0 seed 50
  stem identical:     True          <- so the gate reports the review FRESH
  reviewed options:   [8, 15, 16, 17]
  live options:       [8, 12, 16, 20]
```

The filed review's rationale reasons explicitly about 15, 16 and 17 — options that no longer
render. **The review is substantively stale while NON-VERDICT reports 0 for it.** This is exactly
the shape §2 warns about: *a check that runs on a subset it doesn't announce*. It is the third
blind spot this gate has had, after "freshness validated the samples block but not the rationale"
and "every content check skipped non-PASS reviews".

**Fix it in `validate_judgment.py` by comparing the rendered options (and correct_answer) as well
as the stem.** Expect NON-VERDICT to jump when it lands — that is the point, and an honest red
beats a silent green. Budget the re-reviews it will demand; do not land it without room for them.

### Resumption point
- **NON-VERDICT = 7**, all `mat_g3_mg_q1_1` (Unit 2's fix restaled it). Re-review blind.
- **`mat_g3_mg_q1_0` also needs re-review** even though the gate calls it fresh, for the reason
  above. Do not trust the gate on this one node until the options check is in.

### Next tick should:
1. Land the options comparison in the freshness check, then re-review whatever it marks stale.
2. `q1_1`'s remaining `variant_comprehensiveness` CONCERN is real and unaddressed: one sentence
   frame across all 15 seeds, and seeds 50/500/501 render byte-identical text, as do 44/502 —
   fifteen seeds yield twelve distinct items. The square pool is only {2,3,4,5} choose 3, which is
   four combinations; widening it and varying the frame would fix both.
3. Then the two remaining named Tick Fs, still untouched: `equal_jumps_on_a_number_line`
   (`mat_g2_na_q3_1` + `mat_g3_na_q4_0`, start from `fmt_number_line.py`'s single hop; the frontend
   arc at `App.jsx:1435` needs extending too) and `draw_line_relationships` (`mat_g3_mg_q1_5`).
4. **139 nodes remain undeclared and 30 capability gaps remain.** Declaring is cheap and keeps
   naming defects before any sample is read.

---

## 2026-08-13 — Tick A (the freshness blind spot) + re-reviews. **NON-VERDICT reaches 0.**

- **Census before:** PASS=56 CONCERN=61 FAIL=34. Gate: NON-VERDICT=7.
- **Unit 1 — Tick A: closed the freshness blind spot.** `_validate_freshness` compared
  `question_text` only — not the keyed answer, not the options. The gap was live: the previous
  tick changed `mat_g3_mg_q1_0`'s distractors while leaving every stem byte-identical, so the gate
  called the review fresh while its rationale reasoned about options (15, 16, 17) that no longer
  rendered. **Third blind spot this gate has had, same shape as the first two: a check running on
  a subset it doesn't announce.** Now compares stem → answer → option multiset, one error per
  seed. Stated in the docstring: a sample recording no `options` key is not option-checked (right
  for cloze/fill-in-blank, 480 of 2107 samples, but an MCQ review filed without options escapes).
  NON-VERDICT 7 → 18, **all eleven new errors on the one node whose options moved** and the other
  148 untouched — precise, not noisy. Commit `bc852a3`.
- **Unit 2 — re-reviewed q1_0 and q1_1 blind.** `mat_g3_mg_q1_0` → **PASS on all six findings**,
  the first node in this cluster to get there; the reviewer confirmed the estimation fix on its
  own terms. `q1_1` → CONCERN with the induction guard independently verified sample by sample.
  Commit `ef3e7df`.
- **Unit 3 — widened the derivation item's case pools, added a second framing.** 15 samples → 11
  distinct became 14 → 13, one sentence frame became six, and the width stopped being pinned at 4
  (self-inflicted: excluding 2, which the guard requires, had left the low pool as {3,4}).
  1000 seeds with the guard never firing. Commit `d014054`.
- **Unit 4 — re-reviewed q1_1 again.** Five PASS, one CONCERN. **NON-VERDICT 12 → 0.**
  Commit `62da2b3`.
- **Census after: PASS=57 CONCERN=61 FAIL=33.** `run_all` 151/151, 0 failures, all ten contract
  checks, stages 1–5 green throughout.

### A review the gate rejected — the process working
The first attempt at Unit 4 was cut off by the usage limit. Its recovered file parsed cleanly and
looked fine, but the gate caught a **fabricated quote**: the rationale quoted `'A = l w'`, notation
the reviewer invented, appearing in no sample. It was **reverted, not edited to pass**, and the
node re-reviewed from scratch with the failure named in the prompt plus a pre-write self-check.
The replacement came back clean first time. Put that self-check in every reviewer prompt:

```bash
bad=[q for f in review['findings'].values()
     for q in re.findall(r"'([^']+)'", f['rationale']) if q not in corpus]
```

### Next tick should:

1. **`mat_g3_mg_q1_1`'s one remaining CONCERN, stated precisely by the reviewer:**
   > "all eight rectangle samples hold the second dimension fixed across their three cases (only
   > ever 4, 5, or 10), so no variant in the pool ever shows both factors changing — the evidence
   > never demonstrates that the second factor matters, which is the core of the inductive
   > derivation."

   Right, and sharper than the variety point it replaced: with width fixed, the cases are equally
   consistent with "total = length × 4" as a rule about that figure. `_assert_cases_determine`
   does *not* catch this — the offered distractors are all refuted; the gap is in what the
   evidence **demonstrates**, not what it rules out. Make some items vary both factors; the guard
   still holds (varying both makes distractors easier to refute). **Budget the re-review with the
   fix** — that is now four ticks of evidence that a content change without its review is a debt.
2. The two remaining named Tick Fs, still untouched, both confirmed by blind declaration:
   `equal_jumps_on_a_number_line` (`mat_g2_na_q3_1` + `mat_g3_na_q4_0`; start from
   `fmt_number_line.py`'s existing single hop, and note `frontend/src/App.jsx:1435` draws one arc)
   and `draw_line_relationships` (`mat_g3_mg_q1_5`; check `fmt_shape_board.py` first).
3. **139 nodes undeclared, 30 capability gaps.** Declaring is cheap — a blind Declarer on the
   competency sentence alone — and has repeatedly named the defect before any sample was read.

**State at handoff: tree clean, NON-VERDICT 0, all four area nodes freshly reviewed, one at PASS.**

---

## 2026-08-13 — Tick C. **`mat_g3_mg_q1_1` reaches PASS; NON-VERDICT stays 0.**

- **Census before:** PASS=57 CONCERN=61 FAIL=33. Gate: NON-VERDICT=0, tree clean.
- **Unit 1 — made the derivation's evidence show that both factors matter.** The standing CONCERN
  was that every rectangle item held its width fixed, so the cases were equally consistent with
  "total = length × 4" as a rule about that one figure. Added a both-factors-vary case shape
  alongside the fixed-width one. Commit `acdf58a`.
  - Caught before commit: pairing two independent draws rendered `'a 3 by 3 rectangle'` — a
    rectangle with equal sides. The length is nudged off the width on collision.
- **Unit 2 — re-reviewed; the CONCERN moved and got sharper.** Five PASS, but
  `competency_fulfillment` now: *"three of the eight rectangle items hold one dimension fixed ...
  an add-a-constant pattern fits the counts equally well."* Seed 43's `70/80/90` is as consistent
  with "add 10 each time" as with `length × width`. Commit at `acdf58a`'s review.
- **Unit 3 — removed the fixed-width shape entirely.** It had been kept on half the seeds on the
  reasoning that a steady width makes the pattern easier to spot. **Two successive blind reviewers
  rejected that reasoning**, and they were right: for a competency about deriving that *both*
  factors govern the area, a case set holding one fixed is not an easier version of the task, it
  is evidence for a different rule. Commit `a82a389`.
- **Unit 4 — re-reviewed: PASS on all six findings.** Commit `028a7d6`.
- **Census after: PASS=58 CONCERN=60 FAIL=33. NON-VERDICT 0.** `run_all` 151/151, 0 failures, all
  ten contract checks, stages 1–5 green throughout.

### The pattern worth keeping from this tick
The fix→review→fix→review cycle converged in two rounds because each reviewer's CONCERN was
*specific enough to act on without interpretation* — it named seeds, quoted the stems, and said
what property was missing. That came from asking the reviewer directly whether the evidence
**demonstrates** the keyed rule, not just whether the item is answerable. Two different questions;
the second one is what `_assert_cases_determine` already covers, and only the first found this.

The last reviewer also declined to inflate a minor observation into a CONCERN, saying so
explicitly. That is the behaviour the neutral prompt framing is for — worth preserving verbatim in
future reviewer prompts: *"a clean PASS is a legitimate result if the content earns it ... do not
manufacture a concern to look thorough."*

### Next tick should:
1. **`mat_g3_mg_q1_2`** — CONCERN on `variant_comprehensiveness` and `competency_alignment`:
   seeds 50 and 500 render byte-identical, 13 of 14 samples use one of only two sentence frames,
   and nothing ever asks straight out for an area in square units in a context. The area DNA's
   `find_area` path has had the least attention of the four.
2. **`mat_g3_mg_q1_3`** — CONCERN on `variant_comprehensiveness`: all 14 samples come from two
   frames (the garden tiling context and the bare inverse), and no item takes two steps.
3. Then the two remaining named **Tick F**s, still untouched and both confirmed by blind
   declaration: `equal_jumps_on_a_number_line` (`mat_g2_na_q3_1` + `mat_g3_na_q4_0`; start from
   `fmt_number_line.py`'s existing single hop, and note `frontend/src/App.jsx:1435` draws one arc,
   so budget backend + frontend) and `draw_line_relationships` (`mat_g3_mg_q1_5`; check
   `fmt_shape_board.py` before building new).
4. **139 nodes undeclared, 30 capability gaps.** Declaring is cheap and has repeatedly named the
   defect before any sample was read.

**State at handoff: tree clean, NON-VERDICT 0, area cluster has no FAIL and two nodes at PASS.**

---

## 2026-08-13 — Tick C: the **length_measurement** FAIL cluster. FAIL 33 → 32.

- **Census before:** PASS=58 CONCERN=60 FAIL=33. Gate: NON-VERDICT=0, tree clean.
- **Cluster choice — a correction to the previous handoff.** That handoff named `q1_2`/`q1_3`'s
  variety CONCERNs next, but those are CONCERNs while 33 FAILs sat untouched, and the protocol
  says **FAIL before CONCERN**. Grouping the FAILs by **DNA** rather than node prefix (prefix
  grouping showed no cluster; DNA grouping showed one immediately):

  ```
  5  ('length_measurement',): mat_g1_mg_q2_2, mat_g2_mg_q2_0/_1/_2, mat_g3_mg_q1_6
  4  ('subtraction',)   3  ('pictographs',)   3  ('division',)   ...
  ```

  **Group FAILs by DNA, not by node id.** Node prefixes scatter a shared root cause across
  quarters and grades; the DNA is where the cause actually lives.
- **Unit 1 — three defects, all in `length_measurement`'s `estimate` branch.** Commit `c653b16`.
  1. **The enum printed as the unit.** Every other branch resolves a real name via
     `_NON_STANDARD_UNITS`; this one printed `unit_mode`, so Grade 1 read *"An object measures 2
     non_standard. About how many non_standard is that…"*.
  2. **The task was ungated and reached Grade 1.** Checked, not assumed: **no G1 competency asks
     to estimate a length** — `mat_g2_mg_q2_2` is where MATATAG introduces it. Gated at (2, 2).
  3. **Estimates that rounded the quantity away, then estimates that were no-ops.** Length 2 to
     the nearest 10 keys 0; fixing that exposed boundary values (10 to the nearest 5 keys 10).
     Rounding unit now derived from magnitude, length floored, boundary values nudged — the
     treatment `mass_capacity.py` already uses.
  - Verified: 1800 items across 9 nodes → 0 enum leaks, 0 rounding-to-zero, 0 no-op estimates.
    Packets still build for the gated G1 node (16 samples): the builder skips forbidden variants.
- **Unit 2 — re-reviewed both changed nodes.** Commit `a2c30d4`.
  - `mat_g1_mg_q2_2` **FAIL → CONCERN**; reviewer confirms *"no placeholder tokens, and seed 55
    even singularizes to 'A notebook is 1 paperclip long.'"*
  - `mat_g2_mg_q2_2` stays FAIL, but the diagnosis moved off the arithmetic — *"every seed's
    rounding genuinely moves the number, no answer equals the stated value and none is zero"*.
- **Census after: PASS=58 CONCERN=61 FAIL=32.** NON-VERDICT 0. `run_all` 151/151, 0 failures,
  all ten contract checks, stages 1–5 green throughout.

### Next tick should:

1. **`mat_g2_mg_q2_2` — the coverage FAIL, and it is a one-line diagnosis.** Its competency is
   *"Estimate length using meters or centimeters, **and distance using meters**"*, and the
   reviewer found **zero** items for the second clause: all 11 seeds run the one template, ten in
   cm. The cause is visible in the binding:

   ```
   mat_g2_mg_q2_2 bounds: {'task_type': 'estimate'}
   length_measurement task_types: [..., 'estimate', 'distance_between', 'compare_distance', ...]
   ```

   A single scalar bound pins it to object-length estimation, so the distance half can never
   render. `distance_between` already exists. This wants the **sentinel** idiom (as
   `mat_g3_mg_q1_3` uses for `find_area_or_missing_dimension`): bind a value the DNA resolves per
   seed into estimate-a-length or estimate-a-distance. Check `distance_between` renders in metres.
2. Its sibling **`mat_g2_mg_q2_1`** has the identical shape — bound `{'task_type': 'choose_unit'}`
   against a competency naming *"the length of an object **and the distance between two
   locations**"*, and its FAIL rationale says the distance scenario "does not show up once".
   Same fix, same tick.
3. `mat_g2_mg_q2_0` — competency requires "distance in meters"; its distance item renders in cm.
4. Then the next DNA clusters by size: **subtraction (4)**, **pictographs (3)**, **division (3)**.
5. Still untouched, both confirmed by blind declaration: `equal_jumps_on_a_number_line`
   (`mat_g2_na_q3_1` + `mat_g3_na_q4_0`) and `draw_line_relationships` (`mat_g3_mg_q1_5`).
6. **139 nodes undeclared, 30 capability gaps.**

**State at handoff: tree clean, NON-VERDICT 0, FAIL down to 32.**

---

## 2026-08-13 — Tick C: the distance clause. **FAIL 32 → 30.**

- **Census before:** PASS=58 CONCERN=61 FAIL=32. Gate: NON-VERDICT=0, tree clean.
- **Unit 1 — three G2 competencies named distance; none served it.** Measured: **0 of 200 items
  on each of `mat_g2_mg_q2_0/_1/_2` mentioned a distance at all.** Commit `e005c2f`.
  - `q2_0` was unbound (`{}`), so `read_measurement` governed and it rendered one stem,
    "Measure the object. Its length is ___ cm.", on every seed. Bound to a sentinel — the idiom
    its own G1 siblings already use, and which an earlier fix in `registry.py` had explicitly
    deferred for this node ("out of scope for this fix").
  - **The real find: binding it was not enough.** The DNA redirects
    `distance_between → compare_distance` at grade ≥ 2, and **that redirect sat below the
    `compare_distance` branch it redirects into** — so a redirected task fell past every handler
    to the `read_measurement` return at the bottom of the function. Moving it up with the other
    sentinel resolutions is what actually made distance render.
  - `choose_unit` and `estimate` had no distance framing at all; both now alternate per seed, with
    `estimate` fixing metres for the distance case because the competency names metres for it.
  - Result: 0/200 → **60/200, 106/200, 106/200**.
- **Unit 2 — re-reviewed all five affected nodes** (two reviewers in parallel, both packets fresh,
  0 structural errors). Commit `d842865`.
  - `q2_1` **FAIL → CONCERN**, `q2_2` **FAIL → CONCERN**. Reviewer on q2_2: *"Distance items
    correctly use meters — the distance-clause fix landed here"*, and the estimation is genuine —
    *"in no seed does the answer equal the stated value (11→10, 13→15, 18→20, 487→500)"*.
  - `q2_3` CONCERN: *"The distance clause is genuinely fixed ... both named sub-cases are present"*.
- **Census after: PASS=57 CONCERN=64 FAIL=30.** NON-VERDICT 0. `run_all` 151/151, 0 failures,
  all ten contract checks, stages 1–5 green throughout.

### Next tick should:

1. **`mat_g2_mg_q2_0` — one line, and the reviewer named it as the highest-value follow-up.**
   Distance now renders, but in **centimetres**: *"seed 42: `The distance from the bench to the
   tree is 22 cm.`"* — while the competency says *"distance in **meters**"*. The
   `distance_between → compare_distance` redirect lands in a branch that uses the node's `cm`
   `unit_mode`. Force metres for the distance framing (the same override `estimate` already got
   this tick), then re-review. The reviewer also notes no stem names a measuring tool, though the
   competency says "using appropriate measuring tools" — that half is still unserved.
2. **`mat_g2_mg_q4_4` (perimeter) — FAIL with three independent findings, one a real correctness
   bug.** Seed 604 asks the perimeter of *"A triangle has sides 2 cm, 4 cm, and 7 cm"*, which
   **violates the triangle inequality** (2+4 < 7) and is not a plane figure. Also: of its two named
   sub-cases, *identify* is covered but *measure the perimeter* is absent — all seven measuring
   items measure a single object's length, never a figure's border — and seeds 605/606/607 are
   unit-choice and distance items templated from the Q2 node, mentioning no plane figure at all.
   That last part suggests `perimeter` nodes are falling through to `length_measurement`'s tasks.
3. **Object nouns are decoupled from magnitudes across this DNA** — "crayon" renders at 5, 8, 10,
   21 and 49 cm; a bench-to-tree gap of 22 cm; a garden path 30 cm long. The arithmetic is sound
   but the referents train wrong size benchmarks. One shared fix (bind each object noun to a
   plausible magnitude band) would lift `scale_appropriateness` across several nodes at once.
4. Then the next DNA clusters by FAIL count: **subtraction (4)**, **pictographs (3)**,
   **division (3)**.
5. Still untouched: `equal_jumps_on_a_number_line` and `draw_line_relationships` (both Tick F).
6. **139 nodes undeclared, 30 capability gaps.**

**State at handoff: tree clean, NON-VERDICT 0, FAIL down to 30.**

---

## 2026-08-13 — Tick C: perimeter. **FAIL 30 → 29.**

- **Census before:** PASS=57 CONCERN=64 FAIL=30. Gate: NON-VERDICT=0, tree clean.
- **Unit 1 — two defects in `perimeter`, the second hiding behind the first.** Commit `ac72eb0`.
  1. **The DNA emitted impossible triangles.** Three independent `randint` draws with nothing
     relating them, so `"A triangle has sides 2 cm, 4 cm, and 7 cm"` (2+4 < 7) was asked for its
     perimeter. The third side is now drawn from the window the first two leave open
     (`|a-b| < c < a+b` ∩ bounds), the first two redrawn if it closes, and an explicit check
     raises if the inequality is ever violated. Deliberately *not* clamped to an endpoint, which
     would bias every such case onto the same degenerate triangle.
  2. **`profile.get("shape", "rectangle")` — a silent default, and no node binds `shape`.** So
     `mat_g2_mg_q4_5` ("Find the perimeter of **triangles, squares, and rectangles**") served
     rectangles **200 of 200**. Two of the three shapes in its own sentence were unreachable.
     Same defect shape as `area.py`'s, same fix. Now 60 triangle / 72 rectangle / 68 square.
- **Unit 2 — re-reviewed all three perimeter nodes.** Commit `776be23`. `mat_g2_mg_q4_4`
  **FAIL → CONCERN**. The reviewer verified both fixes by machine, not by eye: *"All 12 triangles
  across the three packets satisfy the inequality on every pairing, including the two tight cases
  ... Every perimeter is arithmetically correct — 45/45 matched by machine check"*, and *"Shape
  coverage is complete on nodes 5 and 6"*.
- **Census after: PASS=57 CONCERN=65 FAIL=29.** NON-VERDICT 0. `run_all` 151/151, 0 failures,
  all ten contract checks, stages 1–5 green throughout.

### A false alarm of mine, recorded so it is not repeated
I first measured `mat_g2_mg_q4_6` as naming no shape in 200/200 samples. That was my regex, not the
generator: I searched for `triangle`/`rectangle` and the word problems say **triangular** and
**rectangular**. The node was already correct. **Match on the wording the content actually uses**
before concluding a sub-case is missing.

### Next tick should:

1. **Object-to-unit pairing — now the single highest-value fix in the tree, and confirmed across
   two DNAs.** Every real-world context is sized in centimetres regardless of the noun:
   *"A rectangular garden is 5 cm long and 12 cm wide."*, *"A rectangular garden is 7 cm long and
   1 cm wide."*, *"A triangular flower bed has sides 3 cm, 9 cm, and 11 cm."*, a bench-to-tree
   distance of 22 cm, "crayon" at 5, 8, 10, 21 and 49 cm. `mat_g2_mg_q4_4` **contradicts itself**
   — seed 605 rewards "m" for the distance between the barangay hall and the plaza while seed 607
   asserts a 22 cm bench-to-tree distance.

   The fix is one shared mechanism: **bind each context noun to a plausible magnitude band and
   unit** (crayon/pencil/spoon → cm, small; garden/court/road/flower bed → m). It lifts
   `scale_appropriateness` on `length_measurement` and `perimeter` nodes simultaneously — at least
   six nodes, several of them the only remaining non-PASS finding on their node.
   Secondary, same area: seeds 43/601/604 describe a garden whose **width exceeds its length**.
2. **`mat_g2_mg_q4_4`'s co-mapped DNA — a decision, not an edit.** It maps to both `perimeter` and
   `length_measurement`; ten of sixteen samples name no figure. But `COMPATIBILITY['perimeter']`
   is `['mcq','cloze']` and `ruler_measure` comes only from `length_measurement`, so deleting the
   co-mapping — the fix this file documents for two other nodes — costs the node its only
   measuring visual while its competency says "using appropriate **tools**". Either give
   `perimeter` a ruler-based formatter, or accept the co-mapping and bind it so the length half
   serves the figure. Escalate if neither reading is obviously right.
3. **`mat_g2_mg_q2_0`** — still FAIL: distance renders in centimetres though the competency says
   "distance in meters". One-line override, same as `estimate` got.
4. Then the next FAIL clusters by DNA: **subtraction (4)**, **pictographs (3)**, **division (3)**.
5. Still untouched: `equal_jumps_on_a_number_line`, `draw_line_relationships` (both Tick F).
6. **139 nodes undeclared, 30 capability gaps.**

**State at handoff: tree clean, NON-VERDICT 0, FAIL down to 29.**

---

## 2026-08-13 — Tick C: object-to-unit pairing. **PASS 57 → 59.**

- **Census before:** PASS=57 CONCERN=65 FAIL=29. Gate: NON-VERDICT=0, tree clean.
- **Unit 1 — the numbers were right and the things were wrong.** Commit `b4c7315`.
  The previous tick's reviewer named this as the one systematic defect left, spanning two DNAs:
  *"The arithmetic is sound; the referents train wrong size benchmarks."* A pupil met a 49 cm
  crayon and a 5 cm garden.
  1. **`perimeter`'s word-problem templates hardcoded `cm`.** The magnitudes were always fine for
     a garden — only the unit was wrong. Now metres; bare-geometry framings stay in cm, where an
     abstract figure is meant. Same template also orders its sides, since blind review found
     gardens whose width exceeded their length.
  2. **`length_measurement` clamped every classroom object to one shared `[5, 50]` band** with a
     single special-cased noun — which is how a crayon reached 49 cm. Replaced with per-object
     bands.
  - **A leak the first attempt left**, caught by measuring rather than assuming: five values sat
    exactly one under their floor (a book at 17, a ruler at 14) because the tie-breaker did
    `max(1, val_b - 1)` and stepped past the band. It now steps *within* it.
- **Unit 2 — re-reviewed the four affected nodes.** Commit `6d4906a`.
  **`mat_g2_mg_q4_5` CONCERN → PASS** and **`mat_g2_mg_q4_6` CONCERN → PASS**, the reviewer
  confirming both this tick's and last tick's fixes: *"All four triangles satisfy the triangle
  inequality (2-1-2, 2-4-4, 10-21-17, 12-6-17)"*, *"all three named figures well covered"*, and
  *"Gardens and flower beds are consistently in metres — the object-to-unit fix clearly landed
  here."*
- **Census after: PASS=59 CONCERN=62 FAIL=30.** NON-VERDICT 0. `run_all` 151/151, 0 failures,
  all ten contract checks, stages 1–5 green throughout.

### Next tick should:

1. **Finish the pairing fix — it did not reach the length-and-distance stems.** The reviewer was
   precise: the same defective family survives in `mat_g2_mg_q2_3` and `mat_g2_mg_q4_4` —
   *"A garden path is 30 cm long."*, *"The distance from the bench to the tree is 20 cm."* Two
   specific causes, both mine to finish:
   - `_OBJECT_CM_BANDS` puts **"a garden path" at (30, 100) cm**. A garden path is an m-scale
     object; it does not belong in a centimetre table at all. Move it to the metre pool the way
     `choose_unit` already partitions `cm_scale_items` / `m_scale_items`.
   - The **`compare_distance` stems render in the node's `unit_mode`, which is cm.** A distance
     between two landmarks is metres. `mat_g2_mg_q2_3` **contradicts itself** — seed 601 teaches
     that such a distance is measured in "m" while seed 603 asserts 20 cm. This is the same
     one-line override still outstanding for `mat_g2_mg_q2_0` (item 3 below); **do both together**,
     they are the same cause.
2. **`mat_g2_mg_q4_4` went CONCERN → FAIL on an honest re-read** — *"Only 6 of 16 samples ask for
   a perimeter ... Neither verb identify nor the appropriate tools clause is exercised anywhere;
   no tool is ever named."* This is the co-mapped-DNA tension recorded last tick, now scored
   rather than described. It needs the decision named there: either give `perimeter` a
   ruler-based formatter (so the co-mapping can go), or bind the length half to serve the figure.
   **Escalate if neither reading is obviously right** — it is a pedagogical call about what
   "measure the perimeter using appropriate tools" should render.
3. **`mat_g2_mg_q2_0`** — still FAIL: distance renders in cm though the competency says metres.
   Fold into item 1.
4. Then the next FAIL clusters by DNA: **subtraction (4)**, **pictographs (3)**, **division (3)**.
5. Still untouched: `equal_jumps_on_a_number_line`, `draw_line_relationships` (both Tick F).
6. **139 nodes undeclared, 30 capability gaps.**

**State at handoff: tree clean, NON-VERDICT 0, PASS up to 59.**

---

## 2026-08-13 — Tick C: stranded reviews landed, then conversion + cm ceiling.

- **Census before:** PASS=59 CONCERN=62 FAIL=30. Gate: **NON-VERDICT=17** (the previous tick
  committed its fix but the usage limit killed its re-review).
- **Unit 1 — landed the three stranded reviews.** Rather than re-review from scratch, the same
  agent was **resumed from its own transcript** — its judgment was already made and quote-checked,
  so resuming preserved both the work and its blindness. NON-VERDICT 17 → 0. Commit `0062ece`.
  **Worth reusing: a reviewer killed after judging but before writing can be resumed to write.**
- **Unit 2 — two defects, both grounded in the curriculum rather than in taste.** Commit `82bb320`.
  1. **`Convert 4 m to cm.` is invention.** Not merely "later grade" — **no competency anywhere in
     the G1–G3 graph mentions conversion**, and `mat_g2_mg_q2_3` carries no conversion concept.
     Yet `CURRICULUM_VARIANT_GATES` asserted an introduction point of (2, 1), a curriculum fact
     that does not exist. Gate moved past this graph; the task_type stays declared so §1C stays
     intact, as with `estimate`. It had been reachable at six of nine nodes.
  2. **`cm_max: 500`** produced *"Which is longer: 409 cm or 237 cm?"* — four metres in
     centimetres. A metre stick is the largest tool this grade measures with, so a cm reading past
     100 is a metre reading wearing the wrong unit. Now 100.
  - Verified: 2776 items across 9 nodes → **0 conversion items, 0 cm readings above 100**.
- **Unit 3 — re-reviewed all five affected nodes.** Commit above.
  `mat_g2_mg_q2_3` **FAIL → CONCERN**. Two nodes moved **CONCERN → FAIL** on the defect this tick
  deliberately left, now scored rather than described.
- **Census after: PASS=59 CONCERN=61 FAIL=31.** NON-VERDICT 0. `run_all` 151/151, 0 failures,
  all ten contract checks, stages 1–5 green throughout.

### Next tick should:

1. **`"Measure the object. Its length is ___ cm."` — now the single dominant cause in this
   subtree, driving FAILs on two nodes.** *"nothing in the stem or sample determines the keyed
   answers 1, 2, 2, 3"*, and *"those are precisely the items that would have carried the verb
   'measure'"*. 7 of 16 samples on `mat_g2_mg_q4_4` too.

   **Naming the object will not fix it.** `read_measurement` is a *read-the-visual* task: with the
   `ruler_measure` formatter the item is answerable; the same values through plain `mcq`/`cloze`
   have no visual and no derivable answer. The fix is **formatter routing** — restrict
   `read_measurement` to `ruler_measure` in `FORMATTER_VARIANT_SUPPORT`. Expect the §1C
   empty-execution-matrix tension that the `grid_area` re-route hit: a node bound to
   `read_measurement` would leave `mcq`/`cloze` with no surviving combination. Work that blast
   radius through *before* editing; the area cluster's history in this ledger has the pattern.
2. **`mat_g2_mg_q2_2` — a new, separate, cheap finding:** *"the 'estimate length using meters'
   branch is entirely absent"* because every metre item is a distance. Its competency names three
   parts and serves two. The distance framing added two ticks ago pinned metres to distances only;
   let a length estimate use metres too.
3. **`mat_g3_mg_q1_6`** — FAIL: *draw* never appears, no ruler is used, and seed 604 asks about a
   2 m segment for a classroom ruler. Related to the same Tick F as `draw_line_relationships`.
4. **`mat_g2_mg_q4_4`** — the co-mapped-DNA decision, still open and still needing a call.
5. Then the next FAIL clusters by DNA: **subtraction (4)**, **pictographs (3)**, **division (3)**.
6. **139 nodes undeclared, 30 capability gaps.**

**State at handoff: tree clean, NON-VERDICT 0.**
