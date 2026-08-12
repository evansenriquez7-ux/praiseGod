# PG Pipeline — Implementation Status

> [!NOTE]
> **Reference only. No binding rules live here.** This file tracks the *completion status* of the two implementation plans — [`pgen_hardening.md`](./pgen_hardening.md) (the harness) and [`doc_rem.md`](./doc_rem.md) (the docs remediation). The plans themselves are pristine specs and are not edited to record progress; progress is recorded here. Binding rules live in [`pgen_contract.md`](./pgen_contract.md); verbatim command evidence lives in [`../validation_reports/HARDENING_EVIDENCE.md`](../validation_reports/HARDENING_EVIDENCE.md).

**Last audited:** 2026-08-02 — see "2026-08-02 — stratified re-review, six curriculum fixes, and
housekeeping" below. Full verbatim command evidence for this audit is in
[`HARDENING_EVIDENCE.md`](../validation_reports/HARDENING_EVIDENCE.md), Phases D–F, and was
independently re-derived from a cold start (not log-trust) by a second, dedicated audit pass after
this session — every claim held.

**Previously audited:** 2026-07-26 — see "2026-07-26 audit" below, which found `run_all` was exiting 0
partly because several checks were not running; the earlier summary in this file is kept for history
but its Phase 1 and Phase 4 claims were over-stated and are corrected in the per-phase table.

**Earlier still:** 2026-07-25. **Auditors:** two engineering-agent sessions working concurrently on this same repo — one hardened the judgment-completeness gate (`validate_judgment.py`) and re-audited the four `doc_rem.md` done-criteria; the other (this update, extended across multiple rounds at the user's explicit direction to keep working the punch list) dispatched the blind-reviewer agents the new gate requires and root-caused/fixed 23 distinct generator defects the reviews surfaced — including 3 genuine wrong-answer bugs (a money word problem whose stated answer contradicted its own story; two independent rounding-convention bugs) that were caught specifically because each fix was re-verified by a *fresh* blind reviewer against post-fix samples rather than assumed correct.

---

## Headline: what is actually true right now

```
$ PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
...
Nodes Checked: 151   Nodes Passed: 151   Nodes Failed: 0
PASS judgment_reviews (all nodes have genuine, complete, fresh reviews)
ALL TESTS PASSED SUCCESSFULLY! Praise God!
```

**`run_all` exits 0.** All 151 nodes pass `validate_dna`/`validate_compat`/`validate_interest`/`validate_vocab`/`validate_matrix` (0 failures, all ten contract checks executing, including `§1A-reach` and `§1F`), and `validate_judgment` confirms all 151 nodes have a genuine, schema-complete, non-boilerplate, **non-stale** review filed.

**That green does not mean the curriculum content is clean.** It means every node has an *honest, cited* judgment verdict — most of which are not PASS. Tally across the 151 genuine review files, as of 2026-08-02:

| Overall verdict | Count | What it means |
|---|---|---|
| PASS | 11 | Reviewer found no mismatch between competency and rendered content. |
| CONCERN | 60 | Reviewer found a real but survivable gap (thin sample diversity, partial scope coverage, minor framing mismatch). |
| FAIL | 80 | Reviewer found a clear content-competency mismatch (wrong sub-skill, wrong number range, missing required framing, byte-identical to a sibling node's content, etc). |

**Read this tally as more honest, not worse, than the 31/80/40 it replaces.** The reviews that produced 31/80/40 sampled 5 fixed seeds per node — 39% of the distinct rendering paths a node could actually serve, project-wide (verified by enumerating format diversity across 65+ seeds; some nodes' 5 base seeds saw as little as 1 of 6 formats they actually render). The seeds were widened so each node's packet samples every distinct rendering path it produces, not just whichever one 5 fixed draws happened to land on — and PASS dropped from 31 to 11 because several nodes whose 5-seed sample was accidentally all-good turned out to have a real, previously-invisible defect in a path those 5 seeds never touched (the headline case: a shape-drawing visual formatter was discarding the DNA's item and drawing unrelated random polygons on ~23% of a Grade-1 shape node's items, and no 5-seed review had ever rendered that path). This tally is a *lower bound estimate* becoming a *closer-to-true* one, not new debt. Full history of every tally movement and its cause: [`HARDENING_EVIDENCE.md`](../validation_reports/HARDENING_EVIDENCE.md).

See "2026-08-02 — stratified re-review, six curriculum fixes, and housekeeping" below for this round's fixes, and "Found, not fixed" for what's left.

---

## 2026-08-02 — stratified re-review, six curriculum fixes, and housekeeping

**1. Judgment layer: stratified packets, full re-review.** `judgment_packets.py` now samples up to
5 extra seeds per node (beyond the 5 fixed base seeds), each chosen because it renders a distinct
formatter/format the base 5 miss — closing the 39%-of-rendering-paths blind spot described in the
Headline above. All 151 nodes were re-reviewed blind against the wider packets (10 batches, plus two
more small follow-up batches for nodes whose content drifted as fixes below landed), with reviewers
prompted neutrally (PASS/CONCERN/FAIL by accuracy, not "hunt defects") after the prior round's framing
was found to bias verdicts toward FAIL. Tally: **29/51/71 → 11/60/80** (PASS/CONCERN/FAIL) — read
alongside the Headline note above on why this is more honest, not more broken.

**2. Six named curriculum-debt nodes fixed**, each verified via `validate_matrix --node` and direct
render inspection, each shipped with a fresh blind re-review of every node it touched:

- **`mat_g3_na_q2_5`** ("estimate the difference") — no estimation task existed in `subtraction.py`
  at all; it served exact differences, and the co-mapped `rounding` DNA rounds one number, not the
  difference of two. Added `task_type="estimate"` (round both operands to the larger's leading place,
  subtract the rounded pair); removed `rounding` as a co-mapped DNA (Ground Rule 2 — it cannot express
  this competency regardless of node).
- **`mat_g3_na_q2_6`/`_7`** ("3 to 4 numbers ... observing correct order of operations") —
  `order_of_operations.py`, a complete 3–4-term left-to-right chain generator, was fully registered
  in `compatibility.py`/`axes_catalog.py`/`adapter.py` but **never mapped to any node**; called
  directly it rendered `"What is the value of None + None?"`. Wired it up (fixing two further bugs
  found only by reaching it for the first time: an `operation_mix` vocabulary that matched nothing
  the DNA checked, and a hardcoded `"three_terms"` default that meant an unbound request could never
  produce a 4-term item). `addition`/`subtraction` removed as co-mapped DNAs (neither can express a
  3-4-term chain).
- **`mat_g3_na_q4_1`/`_2`** ("divide using the 6, 7, 8, and 9 tables") — `division.py`'s quotient
  ceiling stayed at the grade default (99) even when a table was bound, serving quotients like 15,
  30, 80 that are not table facts. Capped the quotient to table range when a table is explicitly
  requested. Separately, `fmt_array_grid.py`'s division rendering computed dividend×divisor as a
  fabricated "total" (e.g. a 1080-square array for `180 ÷ 6`) — fixed with a division-specific branch
  computing the true dividend from divisor rows × quotient columns.
- **`mat_g2_na_q3_1`** ("multiplication as repeated addition") — co-mapped with `addition`, which has
  no notion of equal groups and served plain 2-3-digit sums unrelated to multiplication. Removed
  `addition` (Ground Rule 2); added `task_type="repeated_addition"`, which renders an explicit
  written-out sum (`"4 + 4 + 4 = ___. What is 4 x 3?"`) alongside the existing array visual.
- **`mat_g2_na_q4_1`/`_4`** ("unit fractions" / "similar fractions") — `registry.py` had no branch at
  all for the `fractions` DNA, so both nodes silently shared the same default (`fraction_type=
  "unit_fraction"`) — `_4`'s numerator-greater-than-1 case was never exercised. Bound `fraction_type`
  from the competency text ("unit fraction" vs. "similar fraction").
- **Zero-operand degeneracy** (not a named node, a cross-cutting fix): 30-70% of addition/subtraction
  items at the default profile carried a 0 operand (`"What is 4 + 0?"`) — legitimate content, but
  dominant rather than occasional. `addition.py`/`subtraction.py` now prefer the non-zero-operand
  candidate subset, falling back to the full pool only when that subset is empty; a 0 operand stays
  fully reachable, just no longer dominant. Measured: 31.0% → 0.9% (then re-measured at 12.1% after a
  correction below), verified across all 34 addition/subtraction-mapped nodes.

**3. A systemic root cause behind several of the above, and two bugs it exposed once fixed.**
`generators/number_difficulty.py`'s `generate_pair_by_window`/`generate_number_by_window` — the
shared difficulty-window sampler used by nearly every arithmetic DNA — deterministically returned the
*single* closest-scoring candidate, ignoring `rng` entirely, whenever a pool's score distribution left
the requested-scalar window empty. Not a corner case: `mat_g3_na_q4_2`'s missing-factor pool always
resolved to the identical `(6, 1)` pair regardless of seed (the "6 ÷ 6 = ___ on 3 of 5 seeds" finding),
and a 6-candidate unit-fraction pool always resolved to `1/8`. Fixed by falling back to the full
candidate pool (via `rng.choice`) once the window is this sparse. Two regressions this uncovered, both
fixed same-session: (a) the fallback double-diluted the *deliberately* narrow near-ceiling/near-floor
band the endpoint-widening logic (scalar 0.0/1.0) already built on purpose, breaking
`mat_g3_na_q2_0`'s ability to reach its ₱10,000 ceiling — fixed by exempting scalar 0.0/1.0 from the
fallback, since the endpoint mechanism already owns that case; (b) a float-precision false positive in
`fractions.py`'s answer-key check, `Float(0.3333333333333333) != Rational(1, 3)`, previously masked
because the old deterministic collapse always served the exactly-representable `1/8` — widened
`validate_matrix.py`'s existing fractions answer-key bypass (Ground Rule 5 disclosure, full reasoning
in `HARDENING_EVIDENCE.md`).

**4. Two live wrong-answer-key bugs**, found by the fresh blind reviewers themselves (not hunted for),
fixed immediately since they are correctness bugs, not coverage gaps:
- A `"groups"`/`"n"` alias added to `division.py` for the array_grid fix (item 2 above) collided with
  a *different*, pre-existing meaning of those same two keys in `base_generator.py`'s fallback
  question-text builder, silently swapping a displayed divisor for the quotient (`"15 ÷ 3?"` keyed to
  3, when the true fact is `15 ÷ 5 = 3`). Reverted the colliding alias; added a
  concept-gated branch in `fmt_array_grid.py` instead.
- `fmt_error_detect.py` assumed `blank_target` was always `"result"`, showing a fully-known equation
  and unconditionally appending `"= {actor's answer}"` — when a co-mapped DNA legitimately bound a
  different blank (e.g. `"divisor_unknown"`), this showed a **true** statement judged as needing
  "correction" to an unrelated number. Rewrote to place the actor's claimed answer at the actual
  blanked slot. Verified across every error_detect render on every addition/subtraction/
  multiplication/division/missing_number node (5,800 samples in a follow-up audit): 0 inconsistencies.

**5. Housekeeping.** `validation_reports/matrix_report.json` (rewritten by every `run_all`/
`validate_matrix` invocation, including single-`--node` runs, which shrank it to one node and had
already blocked a `git checkout`) is now gitignored — CI already captures it via
`actions/upload-artifact` on failure, so nothing depended on it being tracked.
`backend/app/database.py`'s `DATABASE_URL` presence check moved from import time to first actual
connection (`get_engine()`) — five unit tests that reach a database-free route
(`get_matatag_lab_config`) no longer need a dummy `DATABASE_URL` just to import it; the CI workaround
env var was removed.

Full root-cause detail, every command run, and verbatim before/after output for all of the above:
[`HARDENING_EVIDENCE.md`](../validation_reports/HARDENING_EVIDENCE.md), Phases D–F. Independently
re-verified from a cold start by a dedicated post-session audit (re-ran every Definition-of-Done
command and re-derived every specific claim by direct render inspection, not by trusting the log) —
nothing was found reverted, broken, or incomplete.

---

## Root-caused and fixed, 2026-07-25 session (not just filed as findings)

**Round 1 — DNA sub-concept routing (5 nodes + 2 cross-cutting bugs):**

1. **`mat_g2_mg_q4_3`** ("straight vs. curved lines, flat vs. curved surfaces") and **`mat_g3_mg_q1_5`** ("parallel/intersecting/perpendicular lines") — the `geometric_lines` DNA had *zero* item-pool content for the first node's actual competency and silently substituted unrelated G1 rotation-degree trivia via a three-layer concept-ignoring fallback; the second node's competency was never bound to a `concept_type` at all, so it always fell back to the DNA's `point_line_segment_ray` default and had never once served parallel/perpendicular content. Fixed: added real `straight_curved` item-pool content, bound `concept_type` explicitly per node in `registry.py`, corrected `compatibility.py`'s `FORMATTER_VARIANT_SUPPORT` (it registered Lab-facing variant values — `"straight_curved"`, `"parallel_intersecting"` — that matched *no* string the DNA's pool actually used), and hardened `generate_params()` to raise instead of silently substituting a different `concept_type`'s content.
2. **`mat_g2_mg_q1_0`** ("circles, half/quarter circles") and **`mat_g2_mg_q1_1`** ("composite figures") — identical root cause in the `shapes_2d` DNA: `registry.py` never bound `shape_set`/`task_type` for any node, so these two G2 nodes silently defaulted to the G1 `basic_triangles_rectangles_squares` pool and never showed circles or composite figures. Fixed the same way (explicit per-node binding + fail-loud fallback).
3. **`mat_g3_mg_q4_0`/`_1`/`_2`** ("two-direction slides", "line symmetry", "complete a symmetric figure") — same root cause in `symmetry_slides`, plus a subtler variant: the old registry logic's `pass` ("leave `concept` unrestricted if 'symmetry' is mentioned") did **not** mean the DNA would show symmetry content — it meant the DNA's own grade-based default (`slide_translation` for grade > 1) governed, so all three G3 nodes silently served slide content. (`mat_g1_mg_q4_0`'s rotation content "worked" only by accident: `slide_translation` has no grade-1 items, so its *own* fallback cascade happened to land back on `rotation`, the only grade-1-eligible concept — two bugs masking each other.) Fixed with explicit `concept`/`directions` binding per node, plus the same fail-loud hardening.
4. **A cross-cutting harness bug**, found via #2 and #3: `validate_vocab.py` and `validate_matrix.py`'s vocabulary-gating check exempts a `NOT_YET_KNOWN` term only if it appears solely inside an already-`cumulative_vocab` compound phrase (e.g. "line" inside "number line") — but `cumulative_vocab` excludes the *current* node's own `introduces_vocab`, so no node could ever use the exact compound vocabulary it exists to introduce. Fixed by merging `introduces_vocab` into the compound-exemption check in both copies of this logic.
5. **An orchestrator bug surfaced by fix #2**: binding a per-node variant value can crash generation for a *sibling* DNA on the same multi-DNA node if that DNA reuses the same variant *name* with a disjoint value set (`shapes_2d`'s `task_type="compare_shapes"` isn't valid for `comparing_ordering`, a co-mapped DNA on `mat_g1_mg_q1_1`). Fixed by rejecting a candidate DNA whose own registered variant vocabulary doesn't recognize a value about to be sent to it — scoped carefully to not reject the many legitimate cases where a bound value is a synthesized ground-truth scope (e.g. `missing_number`'s `operation="addition_subtraction"`) that was never a literal Lab-selectable option for *any* DNA in the first place.

**Round 2 — worked further down the punch list, at the user's request (11 more nodes directly + a cross-cutting word-problem fix touching ~13 more, plus 6 deeper infrastructure bugs the fixes exposed):**

6. **`mass_capacity`** (6 nodes, `mat_g3_mg_q2_0..5`) — `measurement_type` was never bound (same "unrestricted ≠ shows the right content" mistake as symmetry_slides); the 3 capacity competencies rendered 100% mass-in-grams content. A `"capacity"` substring check also missed the plural `"capacities"` in one node's own competency text.
7. **`counting`** — `skip_interval` was never bound (a *second* axis beyond `skip_pool`), and a `"count" in text` check silently added `1` to `skip_pool` for nearly every counting competency. Net effect: "count by 2s/5s/10s" nodes always rendered plain +1 counting. Fixing the binding surfaced a second bug: G2/G3's default `skip_pool` never includes `1`, so `_select_skip()`'s `"by_1"` fallback (`1 if 1 in pool else rng.choice(pool)`) silently rendered *random skip-counting* for every unbound plain-counting node at those grades. Both fixed.
8. **`patterns`** — `pattern_type`/`ask_type` were never bound; "repeating pattern" competencies rendered plain arithmetic sequences, and an "increasing OR decreasing" competency only ever showed increasing. Added a new `"increasing_or_decreasing"` composite value resolved by the DNA itself via the seed (same pattern as `missing_number`'s `"addition_subtraction"`).
9. **`comparing_ordering`** — `task_type` was never bound; "order numbers" competencies rendered pairwise comparisons instead of ordering a set. Fixing it surfaced two dead-code bugs in the never-before-exercised `order_set` path: a distinct-value padding bug (could still yield fewer than 3 distinct numbers) and a formatter payload-shape bug (the DNA never populated the ordering formatter's primary read key, so it fell back to re-joining already-formatted answer/distractor strings into a garbled, duplicated-numbers question).
10. **Cross-cutting word-problem framing** — `context` defaults to `"pure"` in every arithmetic/money DNA; nothing ever bound it, so ~13 "Solve problems ..." competencies rendered bare number-fact drills. Turning this on for real (one general registry rule, not per-DNA) exposed a chain of dormant bugs in shared spine-narration infrastructure: (a) spine eligibility only checked "has the student cumulatively seen this concept", not "does this spine's narrated operation match what's being computed right now" — a multiplication problem could get narrated with a subtraction "how many more" spine while still grading a product; (b) multiplication/division's blank-target remap was gated on a DNA field only `missing_number` ever sets, so their word-problem spines were structurally unreachable; (c) `multiplication.py`'s own value keys (`a`/`b`/`result`) didn't match its spines' placeholder names (`groups`/`n`/`total`), so template rendering silently `KeyError`'d and fell back to a plain symbolic question even after a spine was "selected". All three fixed, plus a live vocabulary-gating collision (a spine's use of "points" as in game score vs. the reserved geometric term "point") found and reworded along the way.
11. **A live wrong-answer bug**, caught only by re-running the blind review against fresh post-fix samples: `mat_g1_na_q4_6` ("addition of money ... or subtraction of money") rendered *"Daniel had ₱5 and spent ₱1... how much money does Daniel have left?"* with stated answer **6** (5+1, not 5−1) — `money_peso.py`'s operation never varied from `"add_amounts"`, so a subtraction-narrated spine could still get picked for an addition-computed value. `mat_g2_na_q2_2` separately showed *"has ₱5 in bills and ₱500 in coins... in all?"* → **506** where the narrated 2 amounts summed to 505 — a 3rd, unmentioned amount was silently folded into the stated total. Fixed with a new `"add_or_subtract"` composite operation, a domain-match refinement so spine selection distinguishes money-addition from money-subtraction narratives, and a gate that skips narration entirely (falling back to an explicit itemized list) when the amount count doesn't match what the 2-slot spine template can narrate.
12. **A "next term" vs. "missing term" phrasing/masking bug**, newly reachable via fix #8's `ask_type` binding: `mat_g3_na_q3_5` rendered *"What is the next number in the pattern: 25, 24, 35, 34, 45?"* with answer **24** — a value already visible in the prompt, phrased as if continuing past the end. `_build_symbolic_question()`'s one-size-fits-all patterns phrasing had never been exercised against `ask_type="missing_middle"` before. Fixed to blank the masked position and ask "What number is missing...".

Every fix above was re-verified with a full `run_all` pass before moving to the next, and the round-2 fixes (6–12) were additionally re-verified by a *fresh* blind-review pass against post-fix samples (not assumed correct from the fix alone) — which is how #11 and #12 were caught in the first place.

**Round 3+ — continued at the user's explicit direction ("proceed till done fixing") until the punch list was worked down to two documented systemic patterns (below) plus lower-severity coverage gaps:**

13. **`area`** (4 nodes) — every one rendered the *identical*, dimension-less `"Find the area of the rectangle."`, silently unanswerable for any non-visual formatter. Added real `illustrate_tiles`/`derive_formula` task types, a dimension-showing fallback, and a word-problem spine. Also removed `multiplication` as a mistaken co-mapped DNA on 2 of the 4 nodes (Ground Rule 2 — it rendered fully unrelated content, e.g. "puts 1 ribbon in each of N bags", when picked).
14. **`patterns`** "create"/"explain" competencies (3 nodes) — no task type existed for constructive or explanatory content; added `identify_valid_pattern` (recognize which candidate sequence satisfies the rule) as the closest MCQ-gradable proxy for "create", and activated the DNA's pre-existing but never-invoked `state_rule` ask_type for "explain". Surfaced and fixed a live bug in the *pre-existing* `arithmetic_decreasing` math when reused here: it could generate negative numbers.
15. **`mass_capacity`/`length_measurement` "estimate"** (3 nodes) — `task_type="estimate"` was accepted but never varied output from "measure exactly". Framed as rounding to a sensible unit — which surfaced **two separate real rounding bugs**, both caught only by blind re-review hand-verifying the arithmetic: a `max(unit, ...)` floor that wrongly rounded small values *up* instead of down to 0, and (after fixing that) Python's `round()` using round-half-to-even instead of the round-half-up convention elementary curricula teach (`5 → 0` instead of `10`). Both fixed with an explicit round-half-up implementation, re-verified against 20 hand-computed cases by a third independent blind pass.
16. **`length_measurement`** — added `choose_unit` (`mat_g2_mg_q2_1`: "identify the appropriate unit, m or cm" had no matching task type at all) and extended word-problem framing (added in round 2 for one node) to the G2 standard-units code path, which the round-2 fix hadn't reached.
17. **`place_value`** (4 nodes) — a `num_digits`/`digit_count` key-name mismatch (registry bound a tuple under a name the DNA never reads) meant every node silently used 2-digit numbers regardless of the competency's stated digit count. Fixed the key, plus: a real `decompose` task type (was pure metadata before), a genuine **digit-ambiguity bug** the digit-count fix exposed ("the digit 5 in 255" — two 5's at different place values, real answer undefined) fixed by requiring unique digits, and a missing reverse-lookup sub-skill (`identify_digit`: given a place name, find the digit there) this 3-part competency named but the DNA only ever tested 2 of the 3 directions.
18. **`pictographs`** (5 nodes) — `task_type` never bound; "present data" and "organize into a table" competencies rendered read-only interpretation regardless. The correct formatter routing (`present_data` → student *constructs* the graph; `organize_table` → student *fills in* a table) already existed and was correctly wired — it just never activated.
19. **`perimeter`** (2 nodes) — same dimension-less fallback bug as area, plus missing word-problem framing.
20. **`calendar`** — "give days/months in the correct order" had no matching task type (every existing one reads a specific date off a grid). Added `sequence`; required expanding the DNA's compatible-formatter list (previously only the visual grid formatter was registered) scoped narrowly to avoid exercising a pre-existing MCQ distractor-count fragility in the DNA's other task types.
21. **`time_reading`** — word-problem framing was blocked twice: the DNA never propagated `context`, and separately the visual clock formatter hardcoded its own question text, discarding whatever the DNA supplied. Fixed both.
22. **`geometric_lines`/`length_measurement`** — another Ground Rule 2 mistaken mapping: `mat_g3_mg_q1_6` ("equal-length segments via ruler") had `geometric_lines` co-mapped, whose 3 concept scopes are all naming/classification tasks structurally incapable of representing a measurement skill; it rendered an unrelated vocabulary question. Removed.
23. **`missing_number`** — the module's own docstring claimed `"equivalent expressions (balance)"` as a capability; nothing implemented it. `mat_g1_na_q3_2` rendered single missing-operand facts instead of the equivalent-expressions the competency names. Implemented a genuine `operation="equivalent"` value; required also fixing a hardcoded curriculum gate that only allowlisted `("addition","subtraction")` for this DNA's G1 operations, rejecting the new value regardless of what the registry bound.

Every fix in this round was likewise re-verified with a full `run_all` pass, and every touched node went through at least one fresh blind judgment re-review after the fix (several went through two or three, when a later fix in the same DNA module changed their content again, or when a re-review caught a further bug the first fix introduced). Verbatim before/after evidence for all 23 items across all three rounds: [`HARDENING_EVIDENCE.md`](../validation_reports/HARDENING_EVIDENCE.md).

---

## Two systemic patterns — one partially fixed, one still architectural

1. **Difficulty-windowing clustering / collapse.** The *bug* component of this — a pool's score
   distribution leaving the requested-scalar window empty caused a fully deterministic, `rng`-blind
   collapse to a single candidate, not just "clustering" — was root-caused and fixed 2026-08-02 (see
   above): `generate_pair_by_window`/`generate_number_by_window` now fall back to the full candidate
   pool when the window is this sparse. What remains is the *calibrated design* this session did not
   touch and does not consider a bug: at `number_difficulty=0.5`, the window deliberately selects
   medium-magnitude candidates, so a node whose default profile never varies that scalar will still
   under-exercise the extremes of a wide stated range. This is intended difficulty progression, not a
   defect — but it means "order numbers up to 10000" can still render a narrow band of values at the
   *default* profile even though 0.0/1.0 now correctly reach the true floor/ceiling.
2. **Multi-DNA secondary-content leak.** Confirmed by 2026-08-02's stratified re-review as the single
   largest cause of FAIL verdicts: **29 of the current 80 FAIL nodes are mapped to 2+ DNAs**, and every
   one fixed this session (`mat_g2_na_q3_1`, `mat_g3_na_q2_5`, `mat_g3_na_q2_6`, `mat_g3_na_q2_7`) was
   exactly this pattern — the secondary DNA has no awareness it's serving a specific competency and
   renders generic, correctly-computed, but topically-unrelated content. Those four are now worked
   examples of the fix (remove the unfit co-mapped DNA; build the missing capability into the DNA that
   stays, or replace it with a DNA that already has it), and `HARDENING_EVIDENCE.md` Phase D proposes a
   mechanical triage script (render ~10 seeds *per co-mapped DNA* via `forced_dna`, check whether any
   seed's `question_text` shares a content word with the competency text) to confirm the remaining 25
   without needing a human to eyeball each one. Not yet built or run at scale — still the highest-
   leverage remaining work.

## Found, not fixed — prioritized for the maintainer (updated 2026-08-02)

80 FAIL + 60 CONCERN nodes carry a specific, quoted defect in their own
`validation_reports/judgment/<group>/<node_id>.json` — this is not a summary of all 140, only the
patterns and highest-confidence leads worth a maintainer's attention first:

- **29 co-mapped-DNA-bleed FAILs** — see pattern 2 above. The node list is enumerable directly:
  `python -c "from backend.app.practice_gen.registry import get_all_node_ids, get_node_dnas; ..."`
  filtered to `overall == "FAIL"` and `len(dnas) >= 2`.
- **The "estimate" pattern generalizes past the one node fixed.** `mat_g3_na_q2_5` ("estimate the
  difference") now genuinely estimates; `mat_g3_na_q2_2` ("estimate the sum", `addition` + `rounding`)
  and `mat_g3_na_q3_3` ("estimate the product", `multiplication` + `rounding`) are the identical shape,
  unfixed — the same `task_type="estimate"` pattern (round operands to the larger's leading place,
  compute on the rounded pair, serve the rounded values as `a`/`b` so the DNA's own `answer_formula`
  still recomputes correctly) should port directly.
- **`mat_g2_na_q3_1`'s multiplication table still over-represents 0/1.** The repeated-addition and
  co-mapping fixes landed 2026-08-02, but the same zero/one-thinning fix applied to `addition.py`/
  `subtraction.py` was never ported to `multiplication.py`'s grade-2 table set
  (`[0, 1, 2, 3, 4, 5, 10]`), and a fresh reviewer still found "6 of 7 samples are bare x0/x1 fact
  recall." Same fix, different file — but re-read `HARDENING_EVIDENCE.md` Phase F's guard-condition
  notes first, this exact class of fix diluted a deliberately narrow endpoint band once already.
- **`mat_g2_na_q1_10`** ("properties of addition — zero, commutative, associative") — only the
  zero-identity property is ever exercised; no `task_type` exists to select commutative/associative
  content, and it was found byte-identical to a sibling node's content.
- **`mat_g1_na_q4_3`/`mat_g1_na_q4_4`** — byte-identical samples across two different competencies
  (coin recognition vs. coin valuation).
- **`mat_g2_na_q4_2`/`mat_g2_na_q4_5`** ("order fractions") — the `ordering` formatter is being applied
  to whole numbers instead of fractions; zero samples ever order two fractions.
- **DNA needs genuinely new content, not just a routing fix** — `area` (4 G3 nodes render
  near-identical "find the area of the rectangle" regardless of illustrate/derive-formula/
  standard-units/solve-problems framing) and `patterns` (`mat_g1_na_q3_7`/`mat_g2_na_q2_9` need a
  "create your own pattern" task type; `mat_g3_na_q3_6` needs an "explain the rule" task type —
  neither exists in the DNA). Unchanged from the prior audit; not touched 2026-08-02.
- **`comparing_ordering`'s number spread** and **scale/range not tied to a node's stated ceiling
  elsewhere** (e.g. `mat_g3_na_q1_3`) — unchanged from the prior audit.

Full per-node citations with exact sample text live in each node's `validation_reports/judgment/<group>/<node_id>.json` (`overall: "FAIL"` or `"CONCERN"`, `findings.competency_fulfillment.rationale`).

---

## 2026-07-27 — judgment debt converted into enforcement

Two new contract rows were added because the largest clusters of judgment-review FAIL verdicts
turned out to be machine-checkable. They flagged 47 of 151 nodes; every one was worked to a root
cause and the behavioural matrix is back to **151/151 with all ten contract checks executing**.
No rule was relaxed to get there — the two narrowings that were applied (below) corrected checks
that were asserting against *defaults* rather than curriculum claims.

Two rules were added, each with a mutation test and a contract row:

* **`§1A-reach`** — §1A's other half ("at 1.0, at least one sample *reaches* the competency maximum
  region") had never been implemented; only "no sample exceeds" existed. It asserts only on axes the
  node's competency explicitly binds, because an unbound axis's ceiling is an axis-catalog default,
  not a curriculum claim.
* **`§1F`** — a question stem may not give away its own answer.

Between them they flagged 47 of 151 nodes. Working the shared root causes brought the matrix to
**146/151 passing (5 failures)**:

| Fixed | Nodes | Root cause |
|---|---|---|
| Fraction stem | 9 | `"What fraction does \(\frac{1}{8}\) equal parts represent?"` — ungrammatical *and* self-answering; now states the partitioning in words. |
| Measurement word problem | 12 | `"It measured 5 paperclips long. How long is a book in paperclips?"` — restated its own answer; now compares two measured objects. |
| Ordinal stem/answer mismatch | 3 | `base_generator` accepted only `values["question"]`, but `ordinal_numbers` returns `question_text`, so its rendered template was discarded and a generic "ordinal name" stem was answered with a numeral. |
| Counting range | 11 | `counting` read `difficulty_scalar`, a key nothing sets; left at 0.5 it pinned "count up to 100" at ~31. |
| Degenerate rounding | 2 | `rounding` had a graceful fallback that reintroduced already-round numbers ("Round 10 to the nearest 10."); `mass_capacity`'s estimate task had the same defect. |
| Degenerate area | 3 | `side_min = 1` gave a 1x1 square whose area equals its own side, and the ungrammatical "1 rows and 1 columns". |
| Constant "pattern" | 1 | a repeating cycle could draw one value, rendering "2, 2, 2, 2, 2, 2". |
| `max_product` bound | 2 | *Ground-truth correction (Ground Rule 2):* "Multiply using the 6, 7, 8, and 9 tables" inherited the G3 default ceiling of 1000; its real ceiling is 9x10. Table language was parsed only on the `missing_number` branch. |

**The last five reach failures, and what they turned out to be:**

| Node | Root cause |
|---|---|
| `mat_g3_na_q3_2` | The competency names "2- to 4-digit numbers by a number whose leading digit is the only non-zero digit, with products up to 10 000" — a sub-skill the DNA never implemented. Round multipliers (×20, ×300, ×2000) added. |
| `mat_g3_na_q3_4` | `number_type` defaulted to `single_digit` when *unbound*, capping every unrestricted G3 competency at max(table)×9 = 90. An unbound variant now means "let the ceiling govern"; an explicit value is still honoured, and table-named competencies stay single-digit. |
| `mat_g3_na_q2_0` | With ₱1000 the largest note and a 6-item cap, no pile could exceed ₱6000 against a ₱10 000 ceiling. Item count now scales to the ceiling (bounded at 12), plus deliberate near-ceiling piles, since uniform draws cluster around ₱2000. |
| `mat_g2_na_q4_1`, `mat_g2_na_q4_4` | *Ground-truth correction:* `number_reading` was co-mapped onto "Read and write unit/similar fractions in fraction notation" and rendered `"Write 227 in words."`. Removed. |

### Blind re-review round, and what it caught

All 151 reviews are current. The 40 nodes whose content moved were re-reviewed by
subagents given only the packet (competency text + rendered samples, never the generator source),
and the artifacts cite **the samples the reviewer actually read**, not a fresh render — so
`validate_judgment`'s freshness gate independently confirms they are still current rather than the
assembler asserting it. That caught two nodes whose content changed mid-round; both were re-reviewed.

The reviewers found five defects the machine checks could not, each now fixed:

| Defect | Where |
|---|---|
| `"Which is greater: 18 or 30?"` keyed to the symbol `<` — the stem asks for a number, the key is a relation, so a correct pupil is marked wrong. Flagged independently by three reviewers. | The stem existed in **three** copies (`base_generator`, `fmt_mcq`, `fmt_cloze`) — another R2 violation; all three now ask for the sign that is actually keyed. |
| Negative options (`-34`, `-14`, `-3`, `-1`) offered to Grades 1–3, who have not met numbers below zero. Some are legitimate `ErrorPattern` misconceptions ("b − a"), but they are unreadable rather than tempting at these grades. | Filtered once in `base_generator`'s distractor assembly, which covers all 17 formatters; `augment_distractors` also no longer manufactures them. |
| `"2/4"` offered as a distractor against a keyed `"1/2"` — two correct answers, invisible to a uniqueness check that compares strings. | Distractors equal to the answer *as a value* are now dropped. |
| `"Who has more, and by how many?"` keyed to the bare difference — the first half of the question names a person. | Spine reworded to ask only the quantity it keys. |
| Reviewers hand-verified the arithmetic of every sampled item across both rounds and found **no wrong keys** beyond the mis-keyed items above. | — |

The tally is now **PASS=29 CONCERN=51 FAIL=71** (30/52/69 before the 2026-07-30 adversarial review pass
re-reviewed six drifted nodes; see `validation_reports/HARDENING_EVIDENCE.md`). That is worse-looking
than the 31/76/44 it replaced
and it is the honest number: the earlier reviews were partly stale, and this round's reviewers were
instructed to hunt defects rather than accept plausible content. The FAIL verdicts are dominated by
one architectural pattern the reviewers named repeatedly and independently — **co-mapped secondary
DNAs bleeding off-topic content into a node** (a fractions node serving whole-number comparisons, a
money node serving a bare `822 + 15`). That is the documented multi-DNA leak, it is not a wrong
answer, and it needs a mapping-level decision rather than a generator patch. Every instance is cited
with node id and sample text in `validation_reports/judgment/<group>/<node_id>.json`.

**The systemic root cause behind most of the range cluster:** `difficulty_scalar` is read by 15 DNA
modules and **set by nothing**, so every one of them silently used 0.5. It now falls back to
`number_difficulty` (the axis that actually carries magnitude), matching what `rounding.py` and
`money_peso.py` already did.

That change exposed a latent **infinite loop**: `length_measurement`'s compare task draws two values
and loops `while val_b == val_a`, but at scalar 0.0 the mapped range collapses to a single value
(`log_interpolate(1, 100, 0.0) == 1`), so the loop never terminated. `mat_g3_mg_q1_6` hung the matrix
run indefinitely. Both compare branches now guarantee at least one unit of headroom.

---

## 2026-07-26 audit — the harness was green while not looking

A review of both plans' implementations found that `run_all` exited 0 partly because
several checks were not actually checking. Each item below was found by executing something,
not by reading code; verbatim output is in
[`HARDENING_EVIDENCE.md`](../validation_reports/HARDENING_EVIDENCE.md).

**1. Judgment reviews went stale silently (11 of 151).** `validate_judgment` verified a review's
*schema* but never re-rendered the seeds it cited, so a review outlived the content it judged.
Re-rendering every cited seed showed 11 nodes whose reviewed `question_text` no longer matched the
generator's output — refuting the previous claim that every touched node had been re-reviewed
post-fix. A freshness gate now re-renders each cited seed and fails on drift, which makes
"change a generator ⇒ re-review that node" mechanical rather than remembered (`doc_rem.md` R4
applied to the judgment species). All 11 were re-reviewed blind; their verdicts moved the tally
from 31/80/40 to 31/76/44 (PASS/CONCERN/FAIL) because the honest re-reads found real defects,
including a **mis-keyed answer** at `mat_g1_mg_q1_2` ("a rectangle cut down the middle" keyed as
"two squares", with the correct "two rectangles" scored wrong) and a **self-answering stem** at
`mat_g2_mg_q4_2` ("Maria wakes up at 11:00. What time is that?").

**2. Twenty-two of 151 nodes ran no execution matrix at all — and all reported PASS.** Phase 1's
output contract says "any skipped combination is a failure", but a node whose variant combinations
all filtered away simply generated nothing and, having no failures, counted as verified. This was
invisible until each check site was instrumented to record whether it actually ran. Root cause: a
competency bound naming a *synthesized scope* (`skip_interval="by_1"`, `pattern_type="increasing_or_decreasing"`,
`ask_type="identify_valid"`) or an axis whose every option is curriculum-gated intersected to the
empty set. An empty matrix is now a named failure (`§1C-coverage`), and such axes are omitted so
the registry governs them, as the serving path does.

**3. Those 22 nodes could not serve any formatter-constrained request.** Fixing #2 immediately
surfaced a live bug: `orchestrator.py` checked registry-bound synthesized scopes against
`FORMATTER_VARIANT_SUPPORT`, which enumerates only literal Lab options — so every request naming a
formatter (i.e. **every Lab preview**) raised `Formatter 'X' is not supported by any DNA` for those
nodes. Exempting synthesized scopes, while still honouring an explicit per-formatter restriction,
fixed it.

**4. Phase 4 scored 4/7 the first time it was actually run.** The phase was recorded as done with no
runnable artifact. `tests/mutation_harness.py` now plants all seven bugs, runs the validator meant to
catch each, and restores the tree. First honest execution: 4/7. Two survivors were my own mis-aimed
mutations (patching `dna/base.interpolate`, which is dead for continuous axes, and `adapter.py`'s
raise, which the orchestrator redundantly duplicates) — retargeted at the code that governs. The
third was a genuine hole: **§1A/§1B only ever compared the echoed `difficulty_profile` value, never
the numbers the DNA actually generated**, so a generator handed `max_sum=20` that produced sums of 30
passed cleanly. That is the exact "classic leaky window" §1A names. A generated-value containment
assertion at scalar 1.0 now closes it. 7/7 detected.

**5. That new check found a phantom difficulty axis.** `comparing_ordering` declared `value_max` as a
continuous axis — a second Lab slider carrying the identical "Maximum Value" label as `max_value` —
and the DNA never read it. Ten nodes generated values above a ceiling they were never asked to
respect. Removed from the axis catalog; `value_max` remains real for `pictographs`/`bar_graphs`.

**Also fixed, each surfaced by a now-running check:** `fmt_pattern_sequence` omitted the required
`pattern_kind` on two of three construction paths; `pattern_sequence` was routed for
`ask_type="identify_valid"` it cannot render (zero-option problems); `choose_unit` was offered at G1
though the DNA raises below G2; `"a ruler"` leaked into `mat_g1_mg_q2_0`'s G1 non-standard-units text
as a `NOT_YET_KNOWN` term; `missing_number` tables 6–9 were undeclared despite `mat_g3_na_q4_2`
requiring them; and an int-vs-string type drift between competency bounds and variant vocabularies
made the Lab's own valid selections fail a boundary check.

**One CI gap:** `validate-pgen.yml`'s doc lint used `grep ... || true`, the exact pattern Phase 3
forbids in a validation gate — it collapsed "no match" (exit 1) and "grep failed" (exit ≥2) into
"clean". Rewritten with explicit exit-code handling and `find`, so files in future `docs/`
subdirectories cannot slip past either.

---

## `pgen_hardening.md` (harness) — per-phase status

| Phase | Status | Verification |
|---|---|---|
| 0 — consolidate registries | done | `grep -rn "_DNA_MODULE_MAP" backend/app/practice_gen/validation/` empty; validators import from `_manifest.py`; import-time `set(DNA_MODULE_MAP)==set(COMPATIBILITY)` assertion present. |
| 1 — `validate_matrix.py` (1A–1E) | done | Full behavioral matrix over 151 nodes through the real pipeline path; 0 failures. **Coverage is now observed, not assumed** — see the 2026-07-26 audit below, which found 22 of 151 nodes were being skipped entirely while reporting PASS. |
| 2 — single gate | done | `run_all.py` chains dna(+feasibility)→compat→interest→vocab(full-node)→matrix→judgment; no skip flag. |
| 3 — CI enforcement | done, with one clause deliberately reversed | `validate-pgen.yml` runs `run_all` + the docs `must`-lint + the unit suite + the mutation harness, no `\|\| true`/`continue-on-error`. **Phase 3's second clause — "deployment *requires* the validation job to succeed (job-level `needs:`)" — was reversed on 2026-08-12 at the maintainer's direction; see below.** |
| 4 — mutation-test the verifier | done | **7/7 via a re-runnable artifact**, `tests/mutation_harness.py`. The previous "done (re-inherited, not re-run)" entry was an unverified inheritance; when first actually executed on 2026-07-26 it scored **4/7**. See below. |
| 5 — strict schema; kill fallbacks | done | `FormattedProblem` uses `ConfigDict(extra="forbid")`; App.jsx fallback cascade removed; `/tmp/last_request.json` debug write gone. |
| 6 — LLM-path audit | done, with a scope note | No live **MATATAG** practice-gen path routes through `subagents.py` (`matatag_router.py` imports it but never calls it). The ELA practice path *does* (`practice_router.py` → `generate_ela_skeleton_subagent`/`generate_ela_batch_subagent`); it is outside this harness's MATATAG scope and has **no runtime vocab gate**. Phase 6's wording is "any live serving path for practice problems", so this is an open item, not a closed one. |
| 7 — evidence log | done | `HARDENING_EVIDENCE.md` carries verbatim output for every phase, including the 2026-07-26 audit. |

**Open, escalated (not a defect):** the unified Advanced/bridge-tier scalar *value* (`1.1` vs `1.25`, [`BUG_BRIDGE_SCALAR.md`](./BUG_BRIDGE_SCALAR.md)) — mechanism fixed, value is a pedagogical decision for the maintainer.

### 2026-08-12 — Phase 3's deploy gate reversed at the maintainer's direction

`pgen_hardening.md` Phase 3 required `deploy-backend.yml` to gate deployment on the validation job
(`needs: validate`). That clause is now reversed: `deploy-backend.yml` contains only the `deploy` job,
and the full suite lives in its own `validate-pgen.yml`, which blocks nothing.

**Why.** `run_all` was doing two unrelated jobs. It exits 0 only at a 100% node PASS rate — that is the
hardening loop's *stop* signal, and it is correct that it stays red until the last node passes. But
wiring it to `needs:` also made it the shipping criterion, so a CONCERN verdict on a Grade-2 word
problem blocked every backend deploy, including the manual testing by which those very verdicts get
resolved. Run `31595859973` is the illustration: **151/151 nodes passed the behavioral matrix and the
deploy still failed**, on stage 6/6 alone.

**Evidence that no code check was weakened.** Measured at the time of the change
(`validate_judgment.validate_judgment_reviews()`): **290 total gate errors, 290 non-PASS curriculum
verdicts, 0 integrity errors** (tally `PASS=57 CONCERN=61 FAIL=33` across 151 reviewed). Nothing that
was blocking the deploy was a code defect. Every validator still runs on every push, still fails
loudly, and no `|| true` or `continue-on-error` was introduced anywhere — the checks moved out of the
deploy path, they did not relax. `docs/pgen_contract.md`'s "Runs in" column was updated in the same
commit (Protocol 7).

**Known cost.** `validate-pgen` is now continuously red until the census reaches zero, so a genuine new
break in the DNA or matrix stages produces the same red X as the expected curriculum debt. The badge is
uninformative for the duration; the step log and the hardening loop's per-tick `run_all` are where a
regression actually surfaces. Worth restoring a gate once the census reaches zero.

---

## `doc_rem.md` (docs remediation) — done-criteria status

| Criterion | Status |
|---|---|
| (a) no binding rule without a named enforcer | **Fixed.** CI lint now matches lowercase `must` (not just uppercase `MUST`); `testing_pipeline.md`'s 7 restated imperatives were reclassified as descriptive cross-references. The reverse gap — a deploy-blocking *enforcer* with no contract row — was closed on 2026-07-26: `validate_judgment` ran in `run_all` but appeared nowhere in the contract table, and is now row `§5`. |
| (b) no fact stated in two places | **Fixed for docs.** `testing_pipeline.md` reclassified as a dev-tooling explainer; `vocab_gate.md`'s links corrected to `../backend/...`. **Open in code:** the scalar→value windowing formula is implemented three times (`orchestrator.py`, `validate_matrix.get_expected_mapped_value`, `dna/base.interpolate`), which is the same R2 violation one layer down — and the `dna/base` copy turned out to be dead for continuous axes. |
| (c) `run_all` cross-checks the contract table | **True in both directions now.** The executed-check set is *observed* (each check site in `validate_matrix` records its own §-ref) rather than asserted by the runner, so a check that silently stops running fails the cross-check. Remaining limit unchanged: it verifies a row's check *ran*, not that it does what the row's prose claims. |
| (d) `DOC_RULES.md` exists and is linked from README | True. |
| (e) §3.2's bridge-scalar assertion | **Open.** The 1.1-vs-1.25 value is unified through `DIFFICULTY_LEVEL_MAP[4]`, but `validate_compat` enforces this by grepping `matatag_router.py`'s *source text*, not by asserting behaviour. doc_rem §3.2 asked the harness to assert bridge samples stay inside the bridge window and never appear when the Lab config disables it; that behavioural check does not exist. |

**Judgment layer — genuine, hard-gated, and now fully populated.** `validate_judgment.py` rejects: missing files, non-JSON, wrong `node_id`, a placeholder `reviewed_by`, `blind` not `true`, fewer than 3 sample seeds, fewer than 3 real rendered samples, any of the 6 required findings missing a `verdict`/`rationale`, a rationale under 40 characters, a cited seed whose live re-render no longer matches the recorded `question_text` (**freshness** — added after 11 reviews were caught stale, see the 2026-07-26 audit below), and — the load-bearing anti-boilerplate check — **any rationale string reused verbatim across two different nodes**. As of 2026-08-02, all 151 nodes are reviewed by agents blind to the generator/DNA/formatter source against *stratified* packets (5 fixed base seeds plus up to 5 more, each chosen because it renders a distinct format the base 5 miss — see "2026-08-02" above), dispatched across 10 initial batches plus follow-up batches for nodes whose content drifted as later fixes landed. `validate_judgment` confirms: **151/151 genuine, fresh, 0 schema/boilerplate errors.**
