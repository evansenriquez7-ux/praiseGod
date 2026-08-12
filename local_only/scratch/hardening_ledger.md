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
