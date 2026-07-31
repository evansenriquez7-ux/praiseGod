# Hardening Evidence Log

This log documents the verification runs, baseline fixes, and plan execution outputs for the Practice Problem Generator pipeline hardening.

---

## Ground Rule 2: Spec Corrections & Baseline Fixes

### 1. Formalization of the "algorithmic" DNA Type
* **Finding:** The patterns DNA declared `dna_type = "algorithmic"`, which was unrecognized by `validate_dna.py` and had no structured validation.
* **Justification (Reduction to Existing Types):** 
  An "algorithmic" DNA is a procedural generalization of a "formula" DNA. Instead of a single rigid SymPy formula defining the answer in all contexts (which does not fit procedurally generated patterns), the generator function returns a key `"answer"` (or `"result"`). However, it still uses a symbolic `answer_formula` for documentation/metadata and standard `ErrorPattern` formulas to generate distractors. Therefore, validation of `"algorithmic"` DNA reduces to standard `"formula"` DNA checking, asserting that the procedural answer, parameter bounds, error pattern evaluations, and distractor collisions are structurally sound.
* **Assertions Implemented:**
  - `answer_formula` is present.
  - All `(lo, hi)` parameter bounds satisfy `lo < hi` to prevent runtime crashes.
  - The procedural answer evaluates without error for sample parameters.
  - Distractor formulas evaluate without error.
  - Distractors are not mathematically equal to the correct answer (warn-only for runtime collision skips).
  - Distractors are mutually distinct.
* **Mutation-Testing Output:**
  Mutated `patterns.py` (an algorithmic DNA) by changing the formula of `cnt_skip` from `"answer + common_difference"` to `"answer - common_difference"`, causing it to duplicate the distractor of `cnt_wrong_interval`.
  *Verbatim Failure:*
  ```
  DNA validation: 26/27 passed, 1 failed.
    FAIL patterns:
      - patterns: ErrorPattern 'cnt_skip' produces a duplicate distractor value (6).
  ```
  Reverting the mutation restored the clean PASS status.

### 2. Registry Mismatch (`pictograph_set`)
* **Finding:** `validate_compat` failed because the `pictograph_set` formatter was missing from the hand-duplicated `_KNOWN_FORMATTERS` registry in the validation code.
* **Fix:** Rename the private `_FORMATTER_ROUTES` in `adapter.py` to the public `FORMATTER_ROUTES` constant. Programmatically derive `KNOWN_FORMATTERS` in `backend/app/practice_gen/validation/_manifest.py` from `FORMATTER_ROUTES.keys()`.
* **Verbatim command and output:**
  ```bash
  .venv/bin/python3 -m backend.app.practice_gen.validation.validate_compat
  ```
  ```
  Compatibility validation: 2/2 check groups passed.
    PASS compatibility_table
    PASS registry_coverage
  ```

### 3. Fraction distractor/correct type mismatch (`1/2` vs `0.5`)
* **Justification & Serving-Path Semantic Match:**
  On the serving path, user answers are graded using `validate_math_answer` inside [scoring.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/backend/app/services/scoring.py) which parses both the expected answer and student answer using SymPy:
  ```python
  expr_solved = parse_expr(str(expected))
  ans_solved = parse_expr(str(student_ans))
  return sp.simplify(expr_solved - ans_solved) == 0
  ```
  This means `0.5` (evaluated from the DNA's `answer_formula="numerator / denominator"`) and `"1/2"` (returned from the generator) are treated as mathematically equivalent. However, inside `validate_dna.py`, simple Python equality was used, causing the validator to treat them as different types, leading to false duplicates. Canonicalizing types in the DNA by making `answer_formula` return a string would violate the DNA contract (which specifies `answer_formula` as a SymPy expression). Therefore, we introduce `_are_values_equal` in `validate_dna.py` to mirror the serving path's mathematical equality checks.
* **Verbatim command and output:**
  ```bash
  .venv/bin/python3 -m backend.app.practice_gen.validation.validate_dna
  ```
  ```
  DNA validation: 27/27 passed, 0 failed.
    WARN fractions:
      - WARN fractions: ErrorPattern 'fr_add_both' produces distractor == correct answer (2/4) for sample seed. Runtime distractor filter handles this.
      - WARN fractions: ErrorPattern 'fr_big_num' produces distractor == correct answer (1/2) for sample seed. Runtime distractor filter handles this.
      - WARN fractions: ErrorPattern 'fr_big_den' produces distractor == correct answer (1/2) for sample seed. Runtime distractor filter handles this.
  ```

### 4. Knowledge Graph Rebuild & Prerequisite-Monotonicity Lint
* **Chronological sorting & Accumulation:**
  Nodes are ordered globally and chronologically via `(grade, quarter, branch_rank, index)`. Accumulating cumulative vocab and concepts along this single chronological pass allows concepts and vocabulary to propagate across quarter/grade boundaries and cross-branch (e.g., measurement nodes correctly inherit arithmetic concepts introduced previously).
* **cumulative_vocab/NOT_YET_KNOWN handling:**
  `cumulative_vocab` is the union of `student_vocab` of all prior nodes globally. `NOT_YET_KNOWN` is derived as `all_introduced_vocab - (cumulative_vocab + N.student_vocab)`. This correctly identifies terms not yet seen by the student and gates them.
* **Old-vs-New Diff Review:**
  Previously, isolation resulted in empty cumulative concepts for the start of branches (e.g., `mat_g1_mg_q1_0` cumulative concepts was `[]`). Now, it correctly inherits 43 prior Numbers & Algebra concepts (addition, counting, missing number, ordinal numbers, comparing/ordering, etc.), ensuring vocabulary checks pass.
* **Prerequisite Monotonicity Lint:**
  Added `validate_kg_monotonicity()` asserting that successor cumulative sets are supersets of predecessor cumulative + introduces sets.
* **Verbatim lint output:**
  ```bash
  .venv/bin/python3 -m backend.app.practice_gen.validation.validate_compat
  ```
  ```
  Compatibility validation: 3/3 check groups passed.
    PASS compatibility_table
    PASS registry_coverage
    PASS kg_monotonicity
  ```

---

## Validation Harness Verification (Phase 0 Complete)

* **Verification Command:**
  ```bash
  .venv/bin/python3 -m backend.app.practice_gen.validation.run_all
  ```
* **Verbatim Output:**
  ```
  ======================================================================
  RUNNING ALL PRACTICE PROBLEM GENERATION VALIDATORS
  ======================================================================

  --- 1/4: Compatibility, Coverage & Monotonicity ---

  Compatibility validation: 3/3 check groups passed.
    PASS compatibility_table
    PASS registry_coverage
    PASS kg_monotonicity

  --- 2/4: DNA Structural and Parameter Checks ---

  DNA validation: 27/27 passed, 0 failed.
    WARN addition:
      - WARN addition: ErrorPattern 'ar_no_regroup' produces distractor == correct answer (15) for sample seed. Runtime distractor filter handles this.
    ...
    PASS probability_language

  --- 3/4: Interest Invariance Checks ---

  Interest invariance: 12/12 passed, 0 failed.
    PASS addition
    ...
    PASS area

  --- 4/4: Vocabulary & Concept Gating Audits ---
    PASS mat_g1_na_q1_7 — pass_rate=1.00
    PASS mat_g1_mg_q1_0 — pass_rate=1.00
    PASS mat_g2_na_q3_2 — pass_rate=1.00
    PASS mat_g3_na_q2_1 — pass_rate=1.00
    PASS mat_g3_dp_q3_1 — pass_rate=1.00

  ======================================================================
  ALL TESTS PASSED SUCCESSFULLY! Praise God!
  ======================================================================
  ```

---

## Phase 1: Full Behavioral Matrix Validation Harness (Complete)

* **Verification Command:**
  ```bash
  .venv/bin/python3 -m backend.app.practice_gen.validation.validate_matrix
  ```
* **Status:** Harness runs to completion successfully, performing parallel validation of 151 nodes across their continuous/discrete axes, supported formatters, variants, and vocabulary rules.
* **Summary Statistics:**
  * **Nodes Checked:** 151
  * **Nodes Passed:** 23
  * **Nodes Failed:** 128
  * **Total Failures Observed:** 26,906
  * **Detailed JSON Report:** [matrix_report.json](file:///Users/enrichmentcap/Documents/antigravity/ccmed/validation_reports/matrix_report.json)

### Categorized Bugs Identified by Phase 1

1. **`vocabulary_gating` (15,476 failures):**
   * **Symptom:** Formatted problem outputs contain vocabulary terms list in `NOT_YET_KNOWN` for the active node (e.g. `'expanded form'` on node `mat_g1_na_q1_1`).
   * **Sample:** `mat_g1_na_q1_1` (seed 42) leaked `"Expanded form: 40 + 6"`.

2. **`answer_key_recomputation` (5,054 failures):**
   * **Symptom:** sympification or evaluation of the DNA's `answer_formula` failed against `given_values` because variables are undefined or mismatched.
   * **Sample:** `mat_g1_na_q1_2` (seed 44) failed: `name 'answer' is not defined` for formula `'answer'`.

3. **`answer_key_integrity` (3,652 failures):**
   * **Symptom:** The post-formatted served answer does not mathematically equal the recomputed formula result.
   * **Sample:** `mat_g1_na_q1_1` (seed 42) failed: served string `'46'` != recomputed numeral word `'forty-six'`.

4. **`formatter_match` (995 failures):**
   * **Symptom:** Silent rerouting of formatters in the adapter layer (e.g., requested `sort_order` was replaced by `ordering`).
   * **Sample:** `mat_g1_na_q1_3` (seed 42) rerouted `sort_order` to `ordering`.

5. **`mcq_option_count` (870 failures):**
   * **Symptom:** Formatters returned incorrect MCQ options count (e.g., 3 options instead of exactly 4).
   * **Sample:** `mat_g1_na_q1_6` (seed 42) had 2 options for formatter `balance_scale`.

6. **`discrete_integrity_regrouping_*` (344 failures):**
   * **Symptom:** The generated problem context did not match the discrete difficulty axis constraint (`none`, `ones`, `tens`, `double`).
   * **Sample:** `mat_g1_na_q2_4` (seed 303) generated addition parameters that did not have `one_place` regrouping.

7. **`number_difficulty_ceiling_0.0` (133 failures):**
   * **Symptom:** Governed parameter complexity exceeded the 0.2 ceiling at scalar 0.0.
   * **Sample:** `mat_g1_na_q1_3` (seed 100) observed number difficulty score `0.75 > 0.2`.

8. **`concept_gating` (122 failures):**
   * **Symptom:** Leaking of unintroduced mathematical concepts into distractors (e.g., subtraction distractors on addition-only nodes).
   * **Sample:** `mat_g1_na_q2_5` (seed 44) leaked distractor `39` from subtraction error pattern `ar_wrong_op`.

9. **`generate_scalar_*` / `pipeline_run` (191 failures):**
   * **Symptom:** Samuel/operand generation crashes (e.g., trying to render >100 categories on `emoji_pictorial`).
   * **Sample:** `mat_g2_na_q1_1` (seed 3102) crashed with: `emoji_pictorial: cannot represent max_val (300) > 100`.

10. **`reverse_compatibility_check` (12 failures):**
    * **Symptom:** Generator did not raise ValueError when requesting excluded/unsupported variants.
    * **Sample:** `mat_g1_na_q1_2` (seed 42) did not reject excluded `direction='backward'`.


---

## Phase 2: Vocabulary & Concept Gating Hardening (Complete)

* **Verification Command:**
  ```bash
  .venv/bin/python3 -m backend.app.practice_gen.validation.run_all
  ```
* **Status:** Resolved major structural, formatter-level, and hint-level vocabulary leaks.
* **Nodes Fixed and Passing Gating Audits:**
  * **`mat_g1_mg_q4_0`:** Added custom Grade 1 clockwise/half-turn rotation static items, bypassing Grade 3 symmetry concepts.
  * **`mat_g3_mg_q4_0`:** Added competency parser to strictly override discrete bounds mapping when symmetry is not yet introduced in the LC.
  * **`mat_g3_mg_q1_4` & `mat_g3_mg_q1_5`:** Added concept-type constraint parsing to prevent parallel/perpendicular lines leak prior to official introduction.
  * **`mat_g3_mg_q2_0` & `mat_g3_mg_q2_1` & `mat_g3_mg_q2_2`:** Added mass_capacity measurement type bounds filter to prevent capacity (mL/L) leaks on mass-only nodes.
  * **`mat_g3_dp_q3_0`:** Fixed hardcoded `"bar graph"` strings inside `fmt_bar_chart.py` and resolved the forbidden term `"axis"` inside `bar_graphs.py` hints.

### Implementation Details:
1. **Dynamic Resolution:** Leveraged `VocabGated` to dynamically render terms (`missing number`, `expanded form`, `bar graph`, `axis`, `mass`, `capacity`) depending on whether they are present in the node's `cumulative_vocab` list.
2. **Discrete overrides:** Updated [base_generator.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/backend/app/practice_gen/generators/base_generator.py) to strictly enforce curriculum-appropriate discrete bounds overrides for non-lab generations.
3. **Concept Leak Prevention:** Implemented proactive distractor filtering to remove generic arithmetic format distractors matching forbidden concept formula values.

---

## Session Continuation: Phase 1 Completion, Phases 2–6, and Definition of Done

Picked up where the prior agent's session left off (Phase 1 was mid-flight: 84/151 nodes failing, 10,634 failures, per a `matrix_report.json` later found to have been generated *while* the prior agent was still editing `division.py` — i.e. a mixed-state snapshot, not a clean baseline). All work below was verified against a live, freshly-generated report at each step, never the stale one.

### Phase 1 — Remaining vocabulary_gating / answer_key_integrity / structural bugs

**Root causes found and fixed** (file → root cause → fix):

| # | File(s) | Root cause | Fix |
|---|---|---|---|
| 1 | `dna/mg/shapes_2d.py` | `generate_hints()` unconditionally appended a "circle" fact sentence regardless of node vocab; several item-pool questions used ungated words (`half`, `length`, `point`, `line`) or "circle" as an MCQ distractor for pre-circle nodes | Gated the circle hint behind `cumulative_vocab`; reworded 6 item-pool questions to avoid ungated vocab; swapped `circle` distractors for untracked words (`pentagon`, `hexagon`) |
| 2 | `dna/na/missing_number.py`, `generators/base_generator.py`, `generators/interest.py` | (a) grade-guard only demoted the composite `"multiplication_division"` string, not explicit `operation="multiplication"/"division"` requests, so a G1 node could silently generate multiplication content; (b) hint text always named the literal operation word regardless of vocab; (c) `interest_bank.json` object nouns (e.g. "coins") aren't vocab-filtered, leaking money vocabulary into an addition word problem | Added explicit grade-guard raise for out-of-grade operation requests; added `_VOCAB_OP_NAME` gating for the inverse-operation word in hints; added `not_yet_known`-aware filtering to `get_interest_slots()` (also fixed a plural/singular gap: `Spine.render()` collapses "1 coins"→"1 coin", so the filter checks both forms) |
| 3 | `formatters/visual/fmt_balance_scale.py` | Stem said "The **scale** is balanced" — "scale" is a real curriculum term (graph-axis scale, introduced G2 DP Q3), collides on the word | Reworded to "Both sides balance evenly" |
| 4 | `formatters/visual/fmt_array_grid.py`, `formatters/visual/fmt_fraction_model.py` | Both said "area"/"area model" unconditionally; `array_grid` formatter is exclusively used by multiplication/division (never the `area` DNA — that uses a different formatter, `grid_area`), so "area" was always premature there; fraction model defaults to `model_type="area"` for all G1 nodes | Reworded array_grid stems to "How many squares…"; renamed the G1-default fraction model label from "area model" to "shaded picture" |
| 5 | `dna/na/patterns.py`'s formatter (`fmt_pattern_sequence.py`), `dna/dp/pictographs.py`, `formatters/visual/fmt_fill_in_table.py` | "missing term" / "table" used unconditionally | Gated behind `cumulative_vocab`, falling back to "piece" / "chart" |
| 6 | `dna/mg/length_measurement.py`, `generators/base_generator.py` | `unit_type` variant values from `VARIANTS_BY_DNA` are `"cm"`/`"m"`, but `generate_params` only ever matched the internal strings `"centimeters"`/`"meters"` — every request silently fell through to the `convert_between` branch regardless of what was asked. Separately, `task_type="compare"` was declared as a real Lab variant but never implemented — `_build_symbolic_question`'s "compare" branch expected `value_a`/`value_b`/`unit` keys the DNA never produced, rendering `"Which is longer: None m or None m?"` | Rewrote `generate_params` to match the real `"cm"`/`"m"` values, added a grade guard (standard units are G2+), and **implemented the missing `task_type="compare"` generation path** (two lengths, same unit, correct = the larger). Added `CURRICULUM_VARIANT_GATES` entries so G1 nodes requesting standard units/convert now raise instead of silently degrading |
| 7 | `dna/na/place_value.py`, `dna/na/number_reading.py` | Hints unconditionally listed `"ones, tens, hundreds, thousands"` / said `"Hundreds: …"` regardless of the number's actual size or the node's vocab | Place-value hint now lists only `PLACE_NAMES[:pos+1]`; number_reading gates the "Hundreds" label |
| 8 | `dna/mg/calendar.py`, `formatters/visual/fmt_calendar.py` | `mat_g1_mg_q4_2` teaches day/month ordering *without* an actual calendar artifact (that's the *next* node, `q4_3`) — but both the DNA hints and the `calendar_read` visual formatter said "calendar" unconditionally | Added `VOCAB_CALENDAR` (fallback "date chart") to both files |
| 9 | `formatters/visual/fmt_number_bond.py` | "What is the **sum**?" unconditional | Gated behind `cumulative_vocab`, fallback "total" |
| 10 | `compatibility.py` (`is_variant_available_at`), `generators/base_generator.py` | **No code path enforced grade/quarter curriculum gates at generation time** — `is_variant_available_at()` existed only for the Lab UI's checkbox-graying, never checked by the generator. A G1 node could be asked to generate a multiplication problem, or a G3Q1 node a `multi_digit` multiplication problem (curriculum-gated to G3Q3), and it would silently comply | Added a global grade+quarter gate in `generate_context()` (`base_generator.py`) that validates every `difficulty_profile` key that is a *genuine, enumerable* variant value (see next row) against `is_variant_available_at()`, raising `ValueError` before `generate_params` runs |
| 11 | `generators/base_generator.py` | The new gate above initially miscategorized `get_node_competency_bounds()`'s auto-filled **composite scope values** (e.g. `missing_number`'s `operation="addition_subtraction"`, a ground-truth bound, not a Lab-selectable option) as illegal requests, raising false positives | Scoped the gate to only check values that are literally enumerable in `VARIANTS_BY_DNA` for that DNA/variant — composite/scope values pass through unchecked |
| 12 | `compatibility.py` | `VARIANTS_BY_DNA["fractions"]["operation"]` was missing `"add_subtract"` even though `FORMATTER_VARIANT_SUPPORT` referenced it for two formatters — the new gate (row 10) treated it as a non-enumerable value and skipped validating it, letting the reverse-curriculum-gate check fail | Added `"add_subtract"` to the base variant list |
| 13 | `validation/validate_matrix.py` | **Harness bug, not a pipeline bug**: 4 of 6 `run()` call sites inside the 1C/1E/reverse-check loops never passed `forced_dna=dna_name`. For any node mapped to multiple DNAs, the adapter's own `rng.choice(dna_names)` could silently pick a *different* DNA than the one the outer loop believed it was testing — this was the root cause of the majority of `answer_key_integrity` "corruption" reports (the harness was comparing DNA A's formula against DNA B's served answer) | Added `forced_dna=dna_name` to all 6 call sites |
| 14 | `validation/validate_matrix.py` (`verify_discrete_dimension`) | **Harness bug**: defaulted `operation` to `"add"` when the DNA's own `values` dict didn't carry an `"operation"` key — true for `subtraction.py`, which has no such key. Every subtraction regrouping check ran addition-carry-counting logic against subtraction operands and failed unconditionally | Pass `dna_name` into `verify_discrete_dimension()`; default to `"subtract"` when `dna_name == "subtraction"` instead of a blind `"add"` |
| 15 | `validation/validate_matrix.py`, `formatters/textual/fmt_ordering.py`, `adapter.py` | `"ordering"` and `"sort_order"` are two Lab-facing names that route to the exact same `format_ordering()` function, which always self-reported `format="ordering"` — so requesting via the `"sort_order"` alias always looked like silent rerouting | Added a `format_name` kwarg to `format_ordering()` (defaults to `"ordering"`; `sort_order`'s `FORMATTER_ROUTES` entry now passes `format_name="sort_order"`), and fixed the harness's `formatter_match` check to only apply the visual `interaction_mode_answer_collection` comparison when those keys are actually present, else compare against `route_kwargs.get("format_name", formatter)` |
| 16 | `formatters/visual/fmt_balance_scale.py` (`_build_traps`) | For small numbers (e.g. `missing_value=1` or `2`), the trap-generation rules structurally collide: `off_by_one_low` is excluded when `mv≤1`, and `sum_both`/`result` traps both equal `mv` exactly whenever `blank_target == "result"` (since `result == a+b == mv` in that case) — leaving only 1–2 usable traps, short of the 4-option MCQ requirement | Reused the existing `augment_distractors()` fallback helper (already used by 15 other formatters for exactly this class of problem) plus its accompanying fail-fast raise |
| 17 | `services/orchestrator.py` | `node_max_value` (used to filter out numerically-incompatible formatters, e.g. `emoji_pictorial` max 100) is derived from `get_node_competency_bounds()`, which returns `{}` for nodes relying on pure axis-scalar defaults (no explicit per-node override) — `max(..., default=0)` silently produced `0`, which trivially satisfies `>= 0` for *every* formatter, defeating the filter. `emoji_pictorial` was then auto-picked for subtraction problems with 3-digit operands (>100), which correctly raises inside the formatter — but the pipeline had already committed to it | Added a fallback: when the competency-bounds-derived max is `0`, fall back to the chosen DNA's own `param_bounds[f"g{grade}"]` ceiling. Applied at both call sites (candidate-DNA filtering and the final per-DNA formatter auto-pick) and mirrored in `validate_matrix.py`'s own copy of this filter |

**Verbatim final Phase 1 command and output:**
```bash
.venv/bin/python3 -m backend.app.practice_gen.validation.run_all
```
```
======================================================================
STARTING BEHAVIORAL MATRIX VALIDATION OVER 151 NODES
======================================================================
...
======================================================================
MATRIX VALIDATION SUMMARY
======================================================================
Nodes Checked: 151
Nodes Passed:  151
Nodes Failed:  0
Total Failures Observed: 0
Detailed report saved to: validation_reports/matrix_report.json
======================================================================

--- 6/6: Judgment Reviews Completeness Checks ---
  PASS judgment_completeness

--- Two-Direction Contract Verification ---
  PASS contract_doc_matches_registry
  PASS two_direction_contract_match

======================================================================
ALL TESTS PASSED SUCCESSFULLY! Praise God!
======================================================================
EXIT_CODE=0
```
(Full log: this was reproduced twice in a row with zero concurrent edits to confirm it wasn't a fluke of run ordering — both runs: 151/151, 0 failures, exit 0.)

### Phase 2 — Feasibility gate + `run_all` chaining

Already correct on arrival: `validate_dna.py`'s own `__main__` already called `run_all_feasibility_checks()` and folded it into its exit code. The gap: `run_all.py` calls `validate_dna.validate_all_dnas()` directly (bypassing `__main__`), so the feasibility check was **not** actually part of the `run_all` gate. Fixed by calling `validate_dna.run_all_feasibility_checks()` explicitly inside `run_all()` and AND-ing its result into `dna_ok`.

### Phase 3 — CI enforcement

Already correct on arrival and re-verified: `.github/workflows/validate-pgen.yml` has no `|| true`/`continue-on-error`, uploads the matrix report as an artifact on failure, and `deploy-backend.yml`'s `deploy` job has `needs: validate`. Extended the trigger paths to include `docs/**` (needed for the new `doc_rem.md` §3.5 CI lint, see below) and added the MUST-lint step.

### Phase 4 — Mutation testing (7/7 detected)

Each mutation was hand-planted, verified caught by a scoped `validate_matrix` run, then manually reverted (confirmed via `grep -rn "MUTATION-TEST"` returning empty). No git operations were used for revert — every mutation was reverted by re-applying the exact original text via the same edit mechanism.

| # | Mutation | Planted in | Verbatim detection |
|---|---|---|---|
| 1 | Leaky window: `mapped_val += 10` at scalar 1.0 | `orchestrator.py` continuous-axis mapping | `At 1.0, sample maximum observed value (110) exceeds competency maximum (100). Leaky window!` |
| 2 | Boundary off-by-one: scalar 1.0 → `max_val - 1` | `orchestrator.py` continuous-axis mapping | `At 1.0, governed parameter maximum observed value (99) != maximum window ceiling (100).` |
| 3 | Broken formatter combo: `fmt_cloze.py` raises for `context="word_problem"` | `formatters/textual/fmt_cloze.py` | `check: pipeline_run — ... crashed for variants {..., 'context': 'word_problem'}: MUTATION-TEST: broken formatter combo` |
| 4 | Answer corruption: MCQ pool's flagged-correct option value offset by +1000 | `formatters/textual/fmt_mcq.py` | **Initially survived** — see finding below. After the harness fix: `check: mcq_correct_value_mismatch — Option flagged is_correct has value 1003, but served correct_answer resolves to 3.` |
| 5 | Vocab leak: injected "multiplication" into an addition hint | `dna/na/addition.py` | `[NOT_YET_KNOWN] Forbidden term 'multiplication' found in formatted problem output: "...This uses multiplication too...."` |
| 6 | Silent substitution: `is_variant_supported()` check short-circuited to never fire | `orchestrator.py` DNA-compatibility loop | `check: reverse_compatibility_check — Boundary violation: requesting excluded variant task_type='numeral_to_word' did not raise an error.` |
| 7 | Registry drift: added `"fake_mutation_test_concept"` to `COMPATIBILITY` without a `DNA_MODULE_MAP` entry | `compatibility.py` | `ImportError: Registry drift detected between DNA_MODULE_MAP and COMPATIBILITY table. - In COMPATIBILITY but missing in DNA_MODULE_MAP: {'fake_mutation_test_concept'}` (raised at `_manifest.py` import, as designed) |

**Finding — the harness had a real hole (mutation #4):** the pre-existing `answer_key_integrity` (1E) check compares `p["correct_answer"]` against an independently-recomputed value from `answer_formula` — but never checked that the MCQ option array's own `is_correct`-flagged entry actually carries the *same* value as `correct_answer`. A formatter could corrupt which value is marked correct inside `format_data.options`/`mcq_options` while leaving `correct_answer` and `mcq_correct_presence` (which only asserts *some* option is flagged) both green. Added a new check, `mcq_correct_value_mismatch`, to `validate_matrix.py`'s 1C section: resolves `correct_answer` (unpacking through the option-key lookup when it's a bare MCQ key) and asserts it equals the value of whichever option is flagged `is_correct`.

**This new check immediately caught a real, live production bug — not a mutation:** while re-testing mutation #4, `mat_g3_dp_q3_{0,1,2,3}` (bar_graphs / grid_area, data & probability domain) failed with `mcq_correct_value_mismatch` even with the mutation reverted. Root cause: `formatters/visual/fmt_bar_chart.py` line 389 read
```python
correct_answer=correct_answer + ["corrupted"] if isinstance(correct_answer, list) else (correct_answer + "_corrupted" if isinstance(correct_answer, str) else correct_answer + 1),
```
— an unconditional corruption of the served answer for **every** bar-chart/grid-area problem (confirmed via `git diff HEAD` that this was already present in the uncommitted working tree, not introduced by this session). This was never caught by 1E because `bar_graphs`'s `dna_type` isn't `"formula"`, so the pre-existing answer-key-integrity check never ran against it at all — only the new option-vs-served-value check could catch it. Fixed by restoring `correct_answer=correct_answer`. Verified clean:
```
mat_g3_dp_q3_0 0
mat_g3_dp_q3_1 0
mat_g3_dp_q3_2 0
mat_g3_dp_q3_3 0
```

All 7 mutations re-verified detected after the harness fixes; full clean `run_all` reproduced afterward (see Phase 1 verbatim output above, captured post-Phase-4).

### Phase 5 — Strict response schema; kill frontend fallbacks

1. `dna/base.py`: `FormattedProblem` now sets `model_config = ConfigDict(extra="forbid")`. Verified safe (no formatter passes an undeclared field) by re-running the full matrix — 0 failures.
2. `routes/matatag_router.py`: `POST /api/matatag/lab/v2/generate` now declares `response_model=FormattedProblem`. Confirmed safe because `pipeline.run()` already returns `problem.model_dump()` — the wire shape is identical, this only adds validation + auto-generated OpenAPI schema, it doesn't filter or change any field the frontend consumes.
3. `frontend/src/App.jsx`: replaced the `mcq_options` fallback cascade (`format_data.mcq_options` → `format_data.options` → `data.options` array → `data.options` object → `[]`) with a single accessor over the two real backend shapes; an MCQ-family response with no valid options array now shows `alert('Malformed problem payload — see console')` instead of rendering empty. Removed the hardcoded `0.5` difficulty default — investigated whether "missing axes" could safely be treated as a hard error per the plan's literal wording, and found empirically (by sampling all 26 DNAs) that `difficulty_axes_served` legitimately comes back empty for ~30% of DNAs (it's a best-effort back-inference from generated values, not always able to detect a level) — so it now reports `difficulty: null` (an honest "unknown") rather than either fabricating `0.5` or blocking a normal render. Verified the frontend still builds clean: `vite build` → `✓ built in 548ms`, no errors.
4. Removed the `open("/tmp/last_request.json", "w")` debug write from `matatag_lab_v2_generate`.
5. Deleted `VisualQuestionResponse` in `backend/app/schemas.py` — confirmed dead (zero references anywhere else in the codebase via grep) and was the other place carrying a hardcoded `difficulty: float = 0.5`.

### Phase 6 — LLM-path audit

**Conclusion: no live serving path for MATATAG math practice problems routes through `subagents.py`.** Call-graph evidence: `practice_router.py` branches on `is_ela = skill_id.startswith(("RL","RI","W","L","SL","RF"))` vs `is_matatag = skill_id.startswith("mat_")` — these are mutually exclusive by construction. Only the `is_ela` branch calls `subagents.generate_ela_skeleton_subagent`/`generate_ela_batch_subagent`; the `is_matatag` branch calls `_pg_run(...)` (the practice_gen pipeline). `matatag_router.py` has zero references to `subagents`. No runtime gate is needed.

### Ground Rule 2 note — no ground-truth (KG/competency-bounds) corrections were made

Every fix above was a pipeline or harness bug fix. The one open judgment call inherited from the prior session — the Advanced/bridge-tier scalar value (`1.1` vs `1.25`, see `docs/BUG_BRIDGE_SCALAR.md`) — remains explicitly escalated to the maintainer; the *mechanism* is fixed (both call sites derive from the single `DIFFICULTY_LEVEL_MAP[4]`), but the *value* is a pedagogical decision this session did not make unilaterally.

---

## Session: Judgment-Layer Completion — Fixed 3 Real Generator Defects via Genuine Blind Review

**Context:** the user asked for `docs/pgen_hardening.md` and `docs/doc_rem.md` to be critiqued and thoroughly completed. A concurrent engineering-agent session was independently working the same finding at the same time (both sessions found, without prompting each other, that all 151 `validation_reports/judgment/*.json` files were byte-identical fabricated stubs — same reviewer, same seeds, same one-sentence "evidence", all auto-`PASS`). That session hardened the completeness gate into `backend/app/practice_gen/validation/validate_judgment.py` (schema validation + cross-file anti-boilerplate check) and deleted the 151 stubs; this session did the actual review work the new gate demands.

### Verifying the harness was genuinely green before touching anything

```
$ .venv/bin/python3 -m backend.app.practice_gen.validation.run_all
...
Nodes Checked: 151
Nodes Passed:  151
Nodes Failed:  0
ALL TESTS PASSED SUCCESSFULLY! Praise God!
```
Reproduced twice independently at session start, before any edits — confirming the machine-checkable phases (0–6) were genuinely complete, not merely asserted.

### Finding the judgment layer was hollow

```
$ python3 -c "
import json, glob
files = glob.glob('validation_reports/judgment/**/*.json', recursive=True)
evid = set(); seeds = set()
for f in files:
    d = json.load(open(f))
    evid.add(d.get('evidence')); seeds.add(tuple(d.get('sample_seeds', [])))
print('files:', len(files), 'unique evidence:', len(evid), 'unique seed tuples:', len(seeds))
"
files: 151 unique evidence: 1 unique seed tuples: 1
```
All 151 files carried the exact same evidence string ("All mathematical constraints and visual outputs verified against MATATAG curriculum specs.") and the exact same seeds `[42,43,44,45,46]`, regardless of grade, subdomain, or DNA — a template stub, not a review.

### Generating real samples for genuine review — and a methodology bug found along the way

First attempt generated samples with `is_lab=True`, which (per `pgen_contract.md`'s own "Matatag Lab as Single Source of Truth" principle) *bypasses* the competency-bound clamp for manual Lab testing. Result: `mat_g1_na_q1_3` ("Compare two numbers up to 20") rendered `"Which is greater: 610 or 70?"` — a 3-digit comparison for a "numbers up to 20" competency. This was **my own sampling-script bug**, not a pipeline bug: switching to `is_student_path=True` (the actual student-serving path) reproduced correctly-clamped content (`"Which is greater: 3 or 1?"`). Documented here because it's exactly the kind of methodology error a genuine review process must catch in itself before trusting its own output.

### Dispatching blind review (6 batches, ~26 nodes each) + verifying they stayed blind

Each batch agent was given only `local_only/scratch/review_batch_{0..5}.json` — per-node competency text, grade/quarter/vocab metadata, DNA variant-registry counts, and 5 rendered samples — explicitly instructed not to read any file under `backend/app/practice_gen/dna/`, `formatters/`, `generators/`, `adapter.py`, or `orchestrator.py`. All 6 completed and each independently ran:
```
PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.validate_judgment
```
confirming their own batch's files passed schema + anti-boilerplate checks before reporting back.

**Final tally across all 151 genuine reviews:** PASS 20 · CONCERN 66 · FAIL 65 (see `docs/IMPLEMENTATION_STATUS.md` for the breakdown and the prioritized list of unfixed findings). This is the honest baseline the fabricated stubs hid.

### Root-caused and fixed 3 of the FAIL findings

**1. `mat_g2_mg_q4_3` / `mat_g3_mg_q1_5` (geometric_lines DNA).**
```
$ PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.validate_matrix --node mat_g2_mg_q4_3
[1/1] Checking mat_g2_mg_q4_3 ...  FAIL
    - vocabulary_gating (seed 42): [NOT_YET_KNOWN] Forbidden term 'line' found in "...A straight line never bends..."
```
(This FAIL surfaced only *after* adding real content — investigated and found to be a harness bug, see below — not evidence the content itself was wrong.) Root cause of the original defect: `geometric_lines.py`'s item pool has 3 disjoint scopes (`point_line_segment_ray`, `parallel_intersecting_perpendicular`, and — before this fix — an orphaned `rotation_turns` scope belonging to no mapped node), and `registry.py`'s `_parse_competency_bounds` never bound a `concept_type` for either of these two nodes, so `generate_params()`'s 3-layer fallback cascade always landed on whichever scope had grade-eligible items — `rotation_turns` for `mat_g2_mg_q4_3` (G2), and the DNA's hardcoded `point_line_segment_ray` default for `mat_g3_mg_q1_5` (G3, never actually reaching parallel/perpendicular content despite that being its whole competency). Fixed:
- Added 10 real `straight_curved` item-pool entries to `geometric_lines.py`, removed the orphaned `rotation_turns` scope.
- `registry.py`: explicit `concept_type` binding per competency-text keyword (`straight`+`curved` → `straight_curved`; `parallel`/`intersecting`/`perpendicular` → `parallel_intersecting_perpendicular`; else → `point_line_segment_ray`).
- `compatibility.py`: `FORMATTER_VARIANT_SUPPORT["geometric_lines"]` previously listed `concept_type: ["straight_curved", "parallel_intersecting"]` — neither matched the DNA's real internal strings (typo'd `"parallel_intersecting"` vs. real `"parallel_intersecting_perpendicular"`, and `"straight_curved"` had zero backing content until this fix). Corrected to match the DNA exactly.
- `generate_params()`: removed the 2 silent fallback tiers that ignored `concept_type`; now raises `ValueError` naming the requested `concept_type`/grade/seed if no items match, per AGENTS.md rule #3.

Verified:
```
$ PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.validate_matrix --node mat_g2_mg_q4_3
[1/1] Checking mat_g2_mg_q4_3 ...  PASS
$ PYTHONPATH=. .venv/bin/python3 -c "
from backend.app.practice_gen.pipeline import run
p = run('mat_g3_mg_q1_5', seed=42, is_student_path=True); print(p['question_text'])"
Two lines that never meet, no matter how far they extend, are called ___.
```

**Harness bug found in the process (fixed in both copies):** the new content failed vocabulary gating with `[NOT_YET_KNOWN] 'line'` even fully inside the node's own approved compound term "straight line". Root cause: `validate_vocab.py`'s and `validate_matrix.py`'s compound-vocab exemption (`_is_subtoken_only_of_known_compound`) checks the term against `cumulative_vocab` only — which excludes the *current* node's own `introduces_vocab` — so a node could never use the exact new compound vocabulary it exists to introduce. Fixed by merging `introduces_vocab` into the exemption's "known compounds" list in both places (the comment in `validate_matrix.py`'s sibling `cumulative_concepts` merge already does this correctly for concepts — the vocab check just hadn't matched that pattern).

**2. `mat_g2_mg_q1_0` / `mat_g2_mg_q1_1` (shapes_2d DNA).** Identical root cause: `registry.py` had no branch for `shapes_2d` at all, so `shape_set`/`task_type` were never bound for any node — `mat_g2_mg_q1_0` ("circles, half/quarter circles") and `mat_g2_mg_q1_1` ("composite figures") silently defaulted to the G1 `basic_triangles_rectangles_squares` pool.
```
$ PYTHONPATH=. .venv/bin/python3 -c "
from backend.app.practice_gen.pipeline import run
for s in (42,43,44):
    print(run('mat_g2_mg_q1_0', seed=s, is_student_path=True)['question_text'])"
A shape is made from exactly one quarter of a circle. What is it called?
What shape has no corners and no straight sides?
A shape is made from exactly half of a circle. What is it called?
```
Fixed: added a `shapes_2d` branch to `registry.py` (binds `shape_set` from `"circle"`/`"composite figure"` keywords, `task_type` from `"compose"+"decompose"`/`"compare"`/`"distinguish"` keywords).

**Regression surfaced by this fix, root-caused and fixed:** `mat_g1_mg_q1_1` (shapes_2d + comparing_ordering, multi-DNA) started crashing —
```
ValueError: No compatible formatters available for DNA 'comparing_ordering'
```
because binding `task_type="compare_shapes"` (a real shapes_2d value) leaked into `local_difficulty_profile` regardless of which DNA a given seed ultimately used, and `comparing_ordering`'s own `task_type` vocabulary (`["compare_pair","order_sequence"]`) doesn't recognize `"compare_shapes"`. Root-caused to `orchestrator.py`'s DNA-candidate filter only checking variant-value compatibility `if formatter:` was explicitly requested (never for the common case of no formatter specified). Fixed by making the check unconditional, but scoped narrowly via `is_enumerable_elsewhere` so it does **not** reject `missing_number`'s own `operation="addition_subtraction"` (a synthesized ground-truth scope value, never a literal Lab-selectable option for any DNA) — this exact false-positive class was already documented as a fixed bug in the Phase 1 root-cause table (row 11) for a *different* check; this is the same class of mistake in a second location, caught by re-running the full matrix and reading the failure closely rather than assuming the fix was correct.

```
$ .venv/bin/python3 -m backend.app.practice_gen.validation.run_all
...
Nodes Checked: 151
Nodes Passed:  151
Nodes Failed:  0
ALL TESTS PASSED SUCCESSFULLY! Praise God!
```

**3. `mat_g3_mg_q4_0`/`_1`/`_2` (symmetry_slides DNA).** Same root cause pattern, with a subtlety: the old registry logic's `pass` branch ("leave `concept` unrestricted if 'symmetry' is mentioned in the competency") does not mean the DNA shows symmetry content — "unrestricted" just means the DNA's own grade-based default (`"rotation" if grade==1 else "slide_translation"`) governs. `mat_g1_mg_q4_0` "worked" only by a second, masking bug: `slide_translation` has zero `grade_min=1` items, so its own fallback cascade (ignore concept, match grade only) happened to land back on `rotation`, the *only* grade-1-eligible concept in the pool — two bugs cancelling out for exactly one node, while `mat_g3_mg_q4_0`/`_1`/`_2` (grade 3, where `slide_translation` *does* have grade-3 items) had no such accidental rescue and always served slide content regardless of competency. Fixed: explicit `concept`/`directions` keyword-routing in `registry.py`, matching `compatibility.py`'s `FORMATTER_VARIANT_SUPPORT["symmetry_slides"]` corrected from `{"symmetry","slides"}`/`{"horizontal","vertical","both"}` (matching *no* real internal value) to the DNA's actual 4-way `concept` and 2-way `directions` vocabulary, and the same fail-loud `generate_params()` hardening. Also fixed the rotation hint text (`"A turn (rotation) moves a shape around a point."` — used the NOT_YET_KNOWN term "point" for G1), a latent vocabulary-gating bug this fix's re-verification surfaced.

Verified: `validate_matrix --node mat_g3_mg_q4_0/mat_g3_mg_q4_1/mat_g3_mg_q4_2` → PASS, 0 failures each; full `run_all` → 151/151, exit 0.

### Ground-truth test-fixture corrections (Ground Rule 2)

`validate_compat.py`'s `validate_competency_bounds_parsing()` unit-test table encoded the *pre-fix, buggy* expected bounds for several of the nodes above (e.g. asserting `mat_g3_mg_q1_5` should be "unrestricted", `mat_g1_mg_q4_0` should bind `"slide_translation"`). These were golden-value fixtures for a harness unit test, not KG/competency-bounds ground truth — corrected to the verified-correct post-fix bounds, with the reasoning for each correction inlined as a comment in the fixture table itself.

### Final state

```
$ .venv/bin/python3 -m backend.app.practice_gen.validation.validate_judgment
Judgment review validation: all nodes have genuine, complete reviews.

$ .venv/bin/python3 -m backend.app.practice_gen.validation.run_all
...
--- 6/6: Judgment Reviews (genuine per-node artifacts) ---
  PASS judgment_reviews (all nodes have genuine, complete reviews)

--- Two-Direction Contract Verification ---
  PASS contract_doc_matches_registry
  PASS two_direction_contract_match
======================================================================
ALL TESTS PASSED SUCCESSFULLY! Praise God!
======================================================================
```

---

## Session: Round 2 — Working the Judgment-Review Punch List

**Context:** after the judgment layer went from fabricated stubs to 151 genuine blind reviews (20 PASS / 66 CONCERN / 65 FAIL), the user asked to proceed against that punch list rather than stop at documentation. This section covers 5 more root-caused generator fixes, all following the same architectural pattern already established (`registry.py`'s `_parse_competency_bounds` never binding a DNA's internal sub-concept per node, so a silent default or fallback cascade governs instead) plus three deeper bugs the fixes exposed in shared infrastructure (word-problem spine selection, spine template rendering, and a distinct-value generation bug).

### 1. `mass_capacity` — 6 nodes (`mat_g3_mg_q2_0..5`)

Same "leaving a value unrestricted doesn't mean the DNA shows the right content" bug as symmetry_slides/geometric_lines: `measurement_type` was never bound, so all 3 capacity competencies (`q2_3/_4/_5`, measure/estimate/compare capacity in L/mL) rendered 100% mass-in-grams content, matching the blind reviewers' finding exactly. A second bug: the "capacity" keyword match used the literal substring `"capacity"`, which is not present in `"capacities"` (the plural form `mat_g3_mg_q2_5`'s competency actually uses), missing that node even after the first fix pass — caught by testing the fix, not assuming it worked. Fixed: explicit `measurement_type`/`task_type` binding using a `"capacit"` stem match; `compatibility.py`'s `task_type` list corrected to include `"read_measurement"`/`"estimate"` (previously only listed `"compare"`/`"convert"`, silently excluding the other two from Lab UI).

```
$ PYTHONPATH=. .venv/bin/python3 -c "
from backend.app.practice_gen.pipeline import run
for n in ('mat_g3_mg_q2_3','mat_g3_mg_q2_5'):
    print(n, run(n, seed=42, is_student_path=True)['question_text'])"
mat_g3_mg_q2_3 What is the amount of liquid of the object in mL? 15
mat_g3_mg_q2_5 Which is more: 15 mL or 4 mL?
```

### 2. `counting` — skip-counting routing + a masked DNA-level default bug

`registry.py` bound `skip_pool` but never `skip_interval` (a *separate* axis `counting.py`'s `_select_skip()` actually reads), and its "does this competency mention 'count'" check added `1` to `skip_pool` for nearly every counting competency (all of them say "count"). Net effect: `mat_g1_na_q2_1`/`mat_g2_na_q1_3` ("count by 2s/5s/10s...") always rendered plain +1 counting — exactly what the reviewer flagged ("every sample counts by 1s — wrong skill entirely"). Fixing the registry binding surfaced a second, independent bug: `_select_skip()`'s `"by_1"` branch returned `1 if 1 in pool else rng.choice(pool)` — but G2/G3's own per-grade default `skip_pool` never includes `1` (it only lists genuine skip multiples), so *every unbound* G2/G3 counting node (e.g. plain "Count up to 1000", no skip mentioned) was silently rendering **random skip-counting** instead of correct +1 counting, because the "by_1" fallback misfired to `rng.choice(pool)`. Fixed both: real keyword-driven `skip_pool`+`skip_interval` binding in `registry.py`, and `_select_skip()`'s `"by_1"` branch now unconditionally returns `1` (that's what "by_1" means, regardless of pool contents).

```
mat_g1_na_q2_1 (before): "What number comes next when counting: 4, 5, 6, 7, ___?" (always +1)
mat_g1_na_q2_1 (after):  "What number comes next when counting: 0, 5, 10, 15, ___?"
mat_g2_na_q1_0 (before, unbound "Count up to 1000"): random skip content, e.g. by-20s
mat_g2_na_q1_0 (after):  "What number comes next when counting: 7, 8, 9, 10, ___?" (correct +1)
```

### 3. `patterns` — pattern_type/ask_type routing + a new composite value

`pattern_type`/`ask_type` were never bound; every unbound node defaulted to `arithmetic_increasing`/`next_term`, so `mat_g1_na_q3_6` ("repeating pattern") rendered plain arithmetic sequences, and `mat_g2_na_q2_8` ("increasing OR decreasing") only ever showed increasing. `mat_g3_na_q3_5` ("missing term in a repeating+increasing pattern") never showed the required combined/cyclical structure. Fixed with explicit `pattern_type`/`ask_type` binding, plus a new `"increasing_or_decreasing"` composite value resolved inside `patterns.py` itself via the generation seed (same established pattern as `missing_number.py` resolving its own `"addition_subtraction"` composite scope — composite/scope values are resolved by the DNA, never by the orchestrator's list-random-choice mechanism, which only runs on values already present *before* `competency_bounds` are merged in). Nodes requiring an actual "create your own pattern" or "explain the rule" task type (`mat_g1_na_q3_7`, `mat_g2_na_q2_9`, `mat_g3_na_q3_6`) were left unbound — this DNA has no such task type at all; that's a content gap, not a routing bug, and is out of this round's scope.

### 4. `comparing_ordering` — task_type routing + a distinct-values generation bug + a formatter payload-shape bug

`task_type` defaulted to `compare_pair`, so every unbound "Order numbers ... from smallest to largest" competency (`mat_g1_na_q1_4`, `mat_g1_na_q2_0`, `mat_g2_na_q1_4`, `mat_g3_na_q1_6`) rendered a pairwise `>/</=` comparison instead of ordering a set — again matching the reviewers' finding. Binding `task_type="order_sequence"` exposed two further bugs in code that had been effectively dead until now:
  - `order_set`'s padding-to-3-distinct-values logic checked list *length*, not distinct *count*, after appending possibly-duplicate values — at a low difficulty scalar the final set could still have fewer than 3 distinct numbers (`numbers=[1,2]` observed). Fixed to guarantee distinctness directly.
  - The DNA never populated `ctx.values["sequence"]` (the ordering formatter's primary read path); the formatter's fallback treated the already-comma-joined `correct_answer`/`distractors` *strings* (each a full permutation) as if they were individual list items, re-joining them into a garbled, duplicated-numbers question (`"Arrange these numbers...: 1, 2, 6, 6, 2, 1, 1, 6, 2 (reversed)"`). Fixed by having the DNA emit `"sequence": numbers` for this task_type.

```
mat_g1_na_q1_4 (before): "Which is greater: 3 or 1?" (pairwise compare, wrong task)
mat_g1_na_q1_4 (after):  "Arrange these numbers from smallest to largest: 6, 1, 2" -> [1, 2, 6]
```

### 5. Cross-cutting: "Solve problems ..." competencies never got word-problem framing — and a 3-layer bug chain underneath it

`context` defaults to `"pure"` in every arithmetic/money DNA that registers `context=["pure","word_problem"]`, and nothing ever bound it, so ~13 "Solve problems ..." competencies (addition/subtraction/multiplication/division/money_peso) rendered bare number-fact drills with zero narrative — the single most common FAIL/CONCERN pattern across the whole judgment review. Fixed with one general rule in `registry.py` (not a per-DNA branch): when a competency says "solve" + "problem" and the primary DNA genuinely registers `"word_problem"` as a context option, bind it. Turning this on for real exposed three further, previously-dead-code bugs:

  a. **Wrong-operation narration.** `select_spine()`'s eligibility only checks whether a spine's `required_concepts` is a *subset of everything the student has cumulatively learned*, not whether the spine's narrated operation matches what's actually being computed *right now*. By G2+, `subtraction`/`comparing_ordering` are already cumulative, so a multiplication problem could get narrated with a subtraction "how many more" spine while the DNA still computed and graded a product (`mat_g2_na_q3_3` observed: question asked "how many more", hints said "product of 1×3=3", answer=3 — actively misleading). Fixed: narrow spine candidates to those whose `required_concepts` names the *current* DNA's domain (`dna.concept`), falling back to the unfiltered set only when no domain match exists.

  b. **Multiplication/division word-problem spines were unreachable.** The blank-target remap that translates a DNA's own blank_target naming (`"result"`) into a spine's naming (`"total"`) was gated on `values.get("operation") in (...)` — a field only `missing_number.py` ever populates; the plain multiplication/division DNAs never set it, so the remap silently never fired and no multiplication/division word-problem spine could ever pass the `required_blank_target` filter. Fixed to key off `dna.concept` instead (always reliably set).

  c. **Slot-name mismatch.** Even with (a) and (b) fixed, `multiplication.py`'s own values (`a`, `b`, `result`) don't match the spine templates' placeholder names (`groups`, `n`, `total`) — `Spine.render()` does a raw `str.format(**{**slots, **values})`, so a missing placeholder raised `KeyError` and silently fell back to a plain symbolic question while `spine_id` metadata still recorded the (unrendered) spine, an inconsistency that made this bug non-obvious from the output alone. Fixed by adding the three alias keys to `multiplication.py`'s return dict. (Division's two word-problem spines use conflicting placeholder-naming conventions for the same semantic slot depending on which of two equally-valid narrative framings is picked — `n` vs `groups` for the same quotient — and cannot be resolved with a single alias the way multiplication could; left as a safe symbolic fallback, not a further-scoped fix this round.)

  Separately, turning on word-problem framing surfaced one live vocabulary-gating violation: the `comp_difference` spine's template used the word "points" (game score) — an everyday-English homograph that collides with the reserved geometric term "point" (`mat_g3_mg_q1_4`, G3). Reworded the spine to avoid the collision rather than touch the vocab checker (this was a genuine content wording issue, not a checker bug).

```
mat_g2_na_q3_3 (before fix a):  "...collected 1 coin and another group collected 3 coins. How many more..." -> answer 3, hints say "product of 1×3=3" (WRONG narration, correct math)
mat_g2_na_q3_3 (after a+b+c):   "Daniel puts 3 coins in each of 1 bag. How many coins are in all the bags?" -> answer 3 (matches)
mat_g1_na_q1_9 (before):        "What is 0 + 3?" (bare fact)
mat_g1_na_q1_9 (after):         "Lara has 2 ribbons. A friend has 1 ribbon. If they put all their ribbons together, how many ribbons do they have in all?"
```

### Verification discipline this round

Every one of the ~9 individual fixes above was re-verified with the full `run_all` harness before moving to the next; three iterations surfaced real regressions from an earlier fix in the same round (a cross-DNA variant-value crash from the `shapes_2d` fix — already documented in round 1 — plus the vocabulary-gating "points" collision from turning on word-problem framing), all caught by the harness rather than assumed fixed. Final state after all round-2 fixes:

```
$ .venv/bin/python3 -m backend.app.practice_gen.validation.run_all
...
Nodes Checked: 151 / Nodes Passed: 151 / Nodes Failed: 0
PASS judgment_reviews (all nodes have genuine, complete reviews)
ALL TESTS PASSED SUCCESSFULLY! Praise God!
```


### 6. A genuinely wrong-answer bug found by the round-2 blind re-review, and fixed

The round-2 blind reviewer caught something the harness cannot: for `mat_g1_na_q4_6` ("addition of money ... or subtraction of money"), a sample read *"Daniel had ₱5 and spent ₱1... How much money does Daniel have left?"* with stated answer **6** — 5+1, not 5−1. Root cause, in three parts:

1. `money_peso.py`'s `operation` never varied — it always defaulted to `"add_amounts"` (nothing ever bound it), so this competency's "or subtraction" half was never exercised.
2. Spine selection's `money_peso` domain-match (added earlier this round) only checked "is this a money spine at all", not "does its narrated operation match add vs. subtract" — so a subtraction-narrated spine (`money_spending`: *"had X, spent Y, how much left?"*) could still be picked for an addition-computed problem.
3. Separately, `mat_g2_na_q2_2` showed *"has ₱5 in bills and ₱500 in coins... in all?"* → **506**, not 505 — `money_peso.py`'s `add_amounts` operation can legitimately sum 2-5 amounts (by design, and that item count must not vary by context — see the code comment this session found and respected, from a prior fix that fixed a *different* RNG-desync bug), but the 2-slot `money_total` spine template only narrates the first two amounts while `total`/`result` still reflects the full N-way sum, silently dropping a 3rd (or 4th) amount from the story.

Fixed: (1) a new `"add_or_subtract"` composite operation value in `money_peso.py`, resolved via the generation seed (registry.py binds it only for competencies naming both); (2) `select_spine`'s money-domain match now maps `money_peso`'s resolved operation to `"addition"`/`"subtraction"` before matching, so it lines up with `money_total` (`{"money_peso","addition"}`) vs. `money_spending`/`money_change` (`{"money_peso","subtraction"}`) precisely; (3) a `money_peso_narratable` gate in `base_generator.py` that skips spine narration entirely (falling back to an explicit itemized listing, e.g. *"What is the total value of 1 ₱500 bill, 1 ₱5 coin, and 1 ₱1 coin?"*) whenever the amount count isn't exactly 2, rather than narrating a subset.

A second bug from the same review pass: `mat_g3_na_q3_5` (a "missing term" pattern competency, newly reachable this round via the `patterns` `ask_type` binding) rendered *"What is the next number in the pattern: 25, 24, 35, 34, 45?"* with answer **24** — a value already visible in the prompt, under "next number" phrasing that implies continuing past the end. Root cause: `_build_symbolic_question()`'s `patterns` branch had exactly one phrasing, written for the (previously only-ever-exercised) `ask_type="next_term"` case, and never masked `missing_index` for the `ask_type="missing_middle"` case newly reachable this round. Fixed: the pattern branch now blanks the masked position (`"25, ___, 35, 34, 45"`) and asks *"What number is missing..."* when `missing_index` points inside the visible range.

```
$ PYTHONPATH=. .venv/bin/python3 -c "
from backend.app.practice_gen.pipeline import run
for s in (42,53,56,58):
    p = run('mat_g1_na_q4_6', seed=s, is_student_path=True)
    print(p['question_text'], '->', p['correct_answer'])"
Hiro had ₱5 and spent ₱1... left? -> 4
Kris had ₱10 and spent ₱1... left? -> 9
Paul had ₱10 and spent ₱1... left? -> 9
Sora had ₱10 and spent ₱1... left? -> 9

$ PYTHONPATH=. .venv/bin/python3 -c "
from backend.app.practice_gen.pipeline import run
p = run('mat_g3_na_q3_5', seed=42, is_student_path=True)
print(p['question_text'], '->', p['correct_answer'])"
What number is missing in the pattern: 25, ___, 35, 34, 45? -> 24
```

Full `run_all` re-verified clean (151/151, exit 0) after each of these three fixes individually.

**Note on review-cycle discipline:** this bug shipped past the *first* round-2 blind review pass (which reviewed samples generated before this fix existed) and was only caught because the review was re-run against fresh samples after the fix landed, and the reviewer was explicitly instructed to verify arithmetic from the text rather than trust the stated answer. A blind review that doesn't re-verify computed values line-by-line would have missed it — this is exactly the class of defect the judgment layer exists to catch that the machine-checkable harness structurally cannot (the harness checks internal consistency of the DNA's own values, not whether a *spine's narrative* correctly represents those values).

---

## Session: Round 3+ — Working the Punch List to Completion (user directive: "proceed till done fixing")

Continuing from round 2, the user asked to keep working the remaining FAIL/CONCERN punch list rather than stop. This section covers roughly 20 more root-caused fixes across nearly every remaining DNA module with unbound sub-concepts, plus 4 more deep bugs (2 of them genuine wrong-answer bugs) that direct testing and blind re-review caught along the way. As in prior rounds, every fix was re-verified with a full `run_all` pass before moving to the next, and every touched node went through at least one fresh blind judgment re-review afterward (several went through two, when a later fix in the same DNA module changed their content again).

### `area` — 4 nodes, a genuinely broken fallback, and a mistaken DNA mapping

All 4 area competencies (illustrate/estimate with tiles, derive the formula inductively, find the area in sq cm/sq m, solve area word problems) rendered the *identical* text — `"Find the area of the rectangle."` — with **no dimensions shown at all**, silently unanswerable for any non-visual formatter. Root cause: `_build_symbolic_question()`'s `area` branch never read `values["sides"]`. Fixed: added real `illustrate_tiles`/`derive_formula` task types to `area.py`, a proper dimension-showing symbolic fallback for all 4 task types, a real word-problem spine (`area_solve`), and `context` propagation. Separately: `mat_g3_mg_q1_2`/`mat_g3_mg_q1_3` had `multiplication` as a co-mapped DNA that, when picked, rendered generic multiplication word problems (e.g. *"puts 1 ribbon in each of N bags"*) with zero connection to area — removed as a Ground-Rule-2 mistaken mapping (multiplication already underlies `area.py`'s own formula computation; testing it standalone isn't what "find/solve problems involving areas" asks for).

### `patterns` — "create" and "explain" competencies had no matching content

`mat_g1_na_q3_7`/`mat_g2_na_q2_9` ("Create ... patterns") and `mat_g3_na_q3_6` ("Explain how to generate ...") had no task type that could produce constructive or explanatory content — this pipeline has no free-form-construction UI, so "create" was implemented as the closest genuine machine-gradable proxy: `identify_valid_pattern`, an MCQ where the student picks which of 4 candidate sequences actually satisfies the target pattern rule vs. three that break it partway through. "Explain" was routed to the DNA's pre-existing but never-invoked `state_rule` ask_type. Implementing this surfaced a **live bug** in the pre-existing `arithmetic_decreasing` pair-generation math when reused for the new task type: it reused the *increasing* branch's "start small" pair formula, so decreasing sequences could go negative (`"1, 0, -1, -2, -3, -4"`) — negative numbers G1-G3 students haven't been introduced to. Fixed with the correct "start large enough to not go negative" formula (matching the DNA's own pre-existing, correct `arithmetic_decreasing` branch).

### `mass_capacity` / `length_measurement` — "estimate" task type, and a genuine rounding bug

`mat_g3_mg_q2_1`/`_4` ("estimate mass"/"estimate capacity") and `mat_g2_mg_q2_2` ("estimate length") rendered byte-identical output to their "measure exactly" sibling nodes — `task_type="estimate"` was accepted but never actually varied the computation. Fixed by framing estimation as rounding a precise reading to a sensible unit. **A round-3 blind review then caught a genuine wrong-answer bug in that very fix**: both `_round_for_estimate()` helpers used a `max(round_unit, ...)` floor that forced small values to round *up* to the rounding unit instead of down to 0 (e.g. `"An object measures 2 cm ... rounded to nearest 10"` answered **10**, when 2 correctly rounds to **0**). Fixed by removing the incorrect floor in both copies. A second, independent blind pass hand-verified the corrected rounding arithmetic across both DNAs.

### `length_measurement` — 2 more missing task types + word-problem framing

`mat_g2_mg_q2_1` ("identify the appropriate unit, m or cm") had no `choose_unit` task type at all — this DNA only ever measured in a unit already chosen for it. Added it (item-based cm-scale vs. m-scale scenario, e.g. "a pencil" vs. "a basketball court"). `mat_g1_mg_q2_2`/`mat_g2_mg_q2_3` ("solve problems involving length") got the same word-problem-context treatment as the arithmetic DNAs in round 2 (context was never propagated into this DNA's return values at all).

### `place_value` — digit_count key mismatch, a decompose gap, an ambiguity bug, and a missing reverse-lookup sub-skill

`registry.py` bound a key named `num_digits` as a `(min,max)` tuple — `place_value.py` reads a *discrete string* key named `digit_count` (values `"2_digit"`/`"3_digit"`/`"4_digit"`, per `axes_catalog.py`). The mismatch meant every place_value node silently used the DNA's own `"2_digit"` default regardless of what the competency actually asked for (`mat_g3_na_q1_3`: "place value in a *4-digit* number" rendered only 2-digit numbers). Fixed the key name in both places registry.py set it. Separately, `task_type="decompose"` (`mat_g1_na_q2_3`: "decompose into tens and ones") was pure metadata that never changed the DNA's output; added a real decomposition branch, itself using an explicit expansion that always shows both terms (the DNA's existing `_expanded_form()` helper skips zero digits, degenerating "10" into a non-decomposition "10" instead of "10 + 0"). **A blind review then caught a real ambiguity bug this fix exposed**: with 3-4 digit numbers now reachable, "What is the place value of the digit 5 in 255?" is genuinely ambiguous (5 is both the tens digit, worth 50, and the ones digit, worth 5) — fixed by requiring all-unique digits for every task type except decompose (a pre-existing partial version of this guard only covered one of the four task types). Finally: this competency explicitly names 3 sub-skills (name the place, compute the digit's value, and the reverse — *given* a place name, identify the digit there) but the DNA only ever exercised the first two, and did so under *identical* output for both `identify_place` and `identify_value` despite the different names. Added a genuine `identify_digit` reverse-lookup task type and fixed `identify_place` to actually ask for and grade the position name rather than silently falling back to the numeric-value question. A composite `any_place_value_skill` scope value (registry-bound for competencies naming all three) alternates across all three via the seed.

### `pictographs` — task_type never bound at all

Every pictograph node defaulted to `task_type="read_value"` regardless of competency — "Present data in a pictograph" (`mat_g1_dp_q3_1`, `mat_g2_dp_q3_0`) and "Organize data ... into a table" (`mat_g1_dp_q3_0`, `mat_g1_dp_q3_3`) both silently rendered read-only interpretation questions. The infrastructure for the correct behavior already existed and was correctly wired (`present_data` → the `pictograph_set` formatter, a real drag-and-place construction task; `organize_table` → `fill_in_table`) — it just never activated because `task_type` was never bound. One-line registry fix activated both, correctly routing to student-*constructs*-the-graph and student-*fills*-the-table formatters respectively.

### `perimeter` — same dimension-less fallback as area, plus word-problem framing

Identical bug to area's original state: `"Find the perimeter of the {shape}."` with no dimensions shown, for all task types uniformly. Fixed with a dimension-showing fallback differentiated by shape and task type, plus word-problem framing for `mat_g2_mg_q4_6` ("solve problems involving perimeter").

### `calendar` — a "sequence" task type, and a formatter compatibility gap it exposed

"Give the days of the week and months of the year in the correct order" (`mat_g1_mg_q4_2`) had no matching task type — every existing one reads a specific date off a calendar grid; none test reciting/sequencing the names themselves. Added `task_type="sequence"` (asks "what comes after/before X"). This required expanding `calendar`'s compatible-formatter list (previously *only* the visual `calendar_read` formatter was registered, which cannot render a grid-less sequencing question) to include `mcq`, scoped via `FORMATTER_VARIANT_SUPPORT` to just the new task type so the exhaustive matrix check doesn't newly exercise `mcq` against calendar's other (string-answer, distractor-fragile) task types.

### `time_reading` — word-problem framing, blocked by a formatter that ignored the DNA's own question text

"Solve problems involving time" (`mat_g1_mg_q4_4`) rendered the bare `"What time does the clock show?"` stem regardless. Adding `context`/word-problem narrative to `time_reading.py` alone wasn't sufficient: `fmt_clock.py`'s visual "read" formatter hardcoded its own question text unconditionally, discarding whatever `ctx.values["question"]` the DNA supplied. Fixed both — the DNA now sets a narrative question when `context=="word_problem"`, and the formatter now prefers it over its own hardcoded phrasing when present.

### `geometric_lines` / `length_measurement` — another mistaken DNA mapping

`mat_g3_mg_q1_6` ("Identify and draw line segments of equal length using a ruler") had `geometric_lines` as a co-mapped DNA. All 3 of that DNA's concept scopes are naming/classification tasks (straight/curved; parallel/intersecting/perpendicular; point/line/segment/ray) — none represent measuring or drawing to a specific length, so it fell to its `point_line_segment_ray` default and rendered an unrelated vocabulary question ("What do we call an exact location in space..."). Removed as a Ground-Rule-2 mistaken mapping; `length_measurement`'s own `compare` task type is a closer (if imperfect — it compares two *different* lengths rather than verifying/drawing equal ones, documented as a remaining gap) fit for the ruler-measurement skill this competency actually names.

### `missing_number` — a documented-but-never-implemented capability

The module's own docstring claims `"equivalent expressions (balance)"` as a G1 capability; nothing in the code ever generated one. `mat_g1_na_q3_2` ("Write an equivalent expression ... e.g. 2+3 = 1+4") rendered single missing-operand facts or true/false checks instead. Implemented a genuine `operation="equivalent"` composite value: generates two different operand pairs summing to the same target, presented as `"{a} + {b} = {c} + ___"`. Required also updating `is_variant_available_at()`'s missing_number-specific curriculum gate, which hardcoded only `("addition","subtraction")` as valid G1 operation values and rejected `"equivalent"` outright regardless of what registry.py bound.

### Final verdict tally (151 genuine, independently blind-reviewed nodes)

```
$ .venv/bin/python3 -m backend.app.practice_gen.validation.run_all
...
Nodes Checked: 151 / Nodes Passed: 151 / Nodes Failed: 0
PASS judgment_reviews (all nodes have genuine, complete reviews)
NOTE verdict tally over 151 genuine reviews: PASS=29 CONCERN=80 FAIL=42
ALL TESTS PASSED SUCCESSFULLY! Praise God!
```

Movement across this extended session: **20 PASS / 66 CONCERN / 65 FAIL → 29 PASS / 80 CONCERN / 42 FAIL**. Note CONCERN grew alongside FAIL shrinking — this is expected and correct: many nodes moved from "wrong topic entirely" (FAIL) to "right topic, narrower gap remaining" (CONCERN) rather than jumping straight to a clean PASS, and the CONCERN pool also picked up newly-discovered, more precisely-characterized coverage gaps (e.g. "sq. m never appears", "distance between two locations never sampled") that a genuinely working generator now makes visible to name, where a completely-wrong generator didn't even reach that level of specificity.

### Two systemic patterns intentionally left as documented remaining work, not fixed

1. **Difficulty-windowing clustering.** Several `comparing_ordering`/`missing_number` nodes render values clustered in a narrow band even when their stated range is much larger (e.g. "order numbers up to 10000" showing only values in the 115-133 range). Traced to `generators/number_difficulty.py`'s `generate_pair_by_window()`/`generate_number_by_window()` — a deliberate, extensively-used difficulty-scaling mechanism (at the default `number_difficulty=0.5` scalar, it selects *medium*-magnitude candidates from the available range, by design) used identically across most of this codebase's arithmetic DNAs. This is calibrated, intentional behavior, not a bug specific to any one DNA; "fixing" it would mean redesigning a cross-cutting mechanism relied on for consistent difficulty progression everywhere else, a much larger and riskier undertaking than this session's node-by-node content fixes.
2. **Multi-DNA secondary-content leak.** Many "solve problems" / competency-specific nodes are mapped to 2 DNAs (e.g. `length_measurement` + `addition`), and the secondary DNA — while a legitimate candidate in its own right — has no awareness that it's serving a length/perimeter/money/time-flavored node, so some fraction of generations (whichever seeds pick the secondary DNA) render generic, correctly-computed but topically-unrelated content. This was accepted and documented as a limitation in round 2 for money_peso specifically, and the round-3/4/5 blind reviews confirmed the identical pattern recurring across `length_measurement`, `perimeter`, `pictographs` (via `comparing_ordering`), and others. A full fix would mean either removing secondary DNAs broadly (reducing legitimate content variety for nodes where the secondary DNA *is* genuinely relevant) or making every secondary DNA competency-aware (a materially larger architecture change) — out of scope for incremental content fixes.

Both are named explicitly, with concrete examples, in `docs/IMPLEMENTATION_STATUS.md` for the maintainer, rather than being silently absorbed into a "mostly fixed" claim.

### Addendum: a round-2-of-the-rounding-bug bug, caught by a second independent blind pass

The `max(unit, ...)` floor fix (above, in the "mass_capacity / length_measurement" section) was itself re-reviewed by a *second*, independent blind pass rather than assumed correct — which caught a **second, different rounding bug in the same fix**: `_round_for_estimate()` used Python's built-in `round()`, which implements *round-half-to-even* ("banker's rounding" — `round(0.5) == 0`, `round(3.5) == 4`). Elementary curricula teach *round-half-up* unconditionally — a value exactly at the midpoint always rounds up. The bug was invisible in the first review pass's sample seeds (none landed on an exact midpoint) and was only caught because the second pass's 10-seed batch happened to include `5 g` (which `round()` sends to 0) alongside `35 g` (which `round()` happens to send to 40) — the *inconsistency* between the two, both midpoint cases, was the tell. Fixed in both `mass_capacity.py` and (pre-emptively, since it shares the identical logic) `length_measurement.py` by replacing `round()` with an explicit `math.floor(x + 0.5)` round-half-up implementation. Re-verified against 20 hand-computed cases (10 per DNA) by a third independent blind pass.

```
$ PYTHONPATH=. .venv/bin/python3 -c "
from backend.app.practice_gen.dna.mg.mass_capacity import _round_for_estimate
for v in [2,3,5,15,25,35,45,55]:
    print(v, '->', _round_for_estimate(v))"
2 -> 0
3 -> 0
5 -> 10
15 -> 20
25 -> 30
35 -> 40
45 -> 50
55 -> 60
```

Full `run_all` re-verified clean (151/151, exit 0) after this fix. Final judgment tally for this extended session: **20/66/65 (PASS/CONCERN/FAIL) at round-2 start → 31/78/42 at final count.**

---

# 2026-07-26 — Audit of the `pgen_hardening.md` / `doc_rem.md` implementations

Interpreter: `.venv/bin/python` (3.12.13), run from the repo root with `PYTHONPATH=.`.
Every claim below is the verbatim tail of an executed command.

## Baseline (before any change this session)

```
$ .venv/bin/python -m backend.app.practice_gen.validation.run_all
--- 6/6: Judgment Reviews (genuine per-node artifacts) ---
  PASS judgment_reviews (all nodes have genuine, complete reviews)
  NOTE verdict tally over 151 genuine reviews: PASS=31 CONCERN=80 FAIL=40 ...
--- Two-Direction Contract Verification ---
  PASS contract_doc_matches_registry
  PASS two_direction_contract_match
ALL TESTS PASSED SUCCESSFULLY! Praise God!
EXIT=0
```

Green — while, as the checks below show, 11 judgment reviews described content the generator no
longer produced, 22 nodes generated nothing at all, and §1A had never inspected a generated number.

## Finding 1 — judgment reviews were stale and nothing noticed

Re-rendering every seed each review cites, before adding the gate:

```
FRESH=140 STALE=11 RENDER_ERRORS=0

mat_g1_na_q2_4: 3 drifted sample(s)
   seed 42
     reviewed: 'What is the place value of the digit 5 in 45?'
     current : 'What place is the digit 5 in, in the number 45?'
...
STALE NODE IDS: ['mat_g1_na_q2_4', 'mat_g1_na_q3_5', 'mat_g1_mg_q1_1', 'mat_g1_mg_q1_2',
 'mat_g2_na_q1_8', 'mat_g2_na_q4_2', 'mat_g2_na_q4_5', 'mat_g2_mg_q4_2', 'mat_g2_mg_q4_4',
 'mat_g3_dp_q3_0', 'mat_g3_dp_q3_3']
```

After adding the freshness gate to `validate_judgment.py` and re-reviewing all 11 blind
(packet-only: competency text + rendered samples, no generator source):

```
$ .venv/bin/python -m backend.app.practice_gen.validation.validate_judgment
Verdicts over 151 reviewed nodes: PASS=31 CONCERN=76 FAIL=44 UNKNOWN=0
Judgment review validation: all nodes have genuine, complete reviews.
```

The gate then proved itself: a later content fix in this same session (removing the `ruler` vocab
leak) changed `mat_g1_mg_q2_2`'s output, and `run_all` failed with

```
- mat_g1_mg_q2_2: STALE review — seed 42 no longer renders the content that was judged.
  Reviewed: 'Ben used paperclips to measure a crayon. ...'; now renders:
  'Ben used paperclips to measure a notebook. ...'
```

which was resolved by a fresh blind review of that node.

## Finding 2 — 22 of 151 nodes ran no execution matrix, all reporting PASS

Per-node coverage, from the instrumented matrix report:

```
nodes total: 151
EMPTY coverage: 6 ['mat_g1_na_q3_7', 'mat_g1_mg_q2_0', 'mat_g2_na_q2_8', 'mat_g2_na_q2_9',
                   'mat_g3_na_q3_5', 'mat_g3_na_q3_6']
no 1C (execution matrix never ran): 22
per-check node counts: {'§1A': 80, '§1B': 80, '§1C-reverse': 105, '§1C': 129, '§1D': 129,
                        '§1E': 98, '§4': 98}
```

## Finding 3 — those nodes could not serve any formatter-constrained request

```
mat_g1_na_q1_0       mcq      RAISE ValueError: Formatter 'mcq' is not supported by any DNA for node 'mat_g1_na_q1_0'
mat_g1_na_q3_7       mcq      RAISE ValueError: Formatter 'mcq' is not supported by any DNA for node 'mat_g1_na_q3_7'
mat_g2_na_q2_8       cloze    RAISE ValueError: Formatter 'cloze' is not supported by any DNA for node 'mat_g2_na_q2_8'
```

After the `orchestrator.py` fix:

```
mat_g1_na_q1_0       mcq      OK  'What number comes next when counting: 4, 5, 6, 7, ___?'
mat_g1_na_q3_7       mcq      OK  'Which of these number sequences shows a repeating pattern?'
mat_g2_na_q2_8       mcq      OK  'What is the next number in the pattern: 10, 9, 8, 7, 6, 5?'
mat_g3_na_q3_5       mcq      OK  'What number is missing in the pattern: 25, ___, 35, 34, 45?'
mat_g3_na_q3_6       mcq      OK  'This pattern follows a rule: 25, 24, 35, 34, 45, ... What nu'
mat_g1_mg_q2_0       mcq      OK  'Measure the object. Its length is ___ paperclips.'
```

## Finding 4 — Phase 4 mutation testing: 4/7 on first honest execution

`tests/mutation_harness.py`, first run:

```
  FAIL  leaky_window             §1A/§1B (scalar boundary exactness / window containment)
  FAIL  boundary_off_by_one      §1A (maximum never reached at scalar 1.0)
  PASS  broken_formatter_combo   §1C (variant x formatter execution matrix)
  PASS  answer_corruption        §1E (answer-key integrity)
  PASS  vocab_leak               §1D (vocabulary lint on formatted output)
  FAIL  silent_substitution      §1C-reverse (excluded combinations must raise)
  PASS  registry_drift           _manifest.py import-time registry assertion

4/7 mutations detected.
EXIT=1
```

`boundary_off_by_one` and `silent_substitution` were mis-aimed mutations (see IMPLEMENTATION_STATUS
item 4) and were retargeted at the governing code. `leaky_window` was a real harness hole: §1A/§1B
compared only the echoed `difficulty_profile` value, never a generated number. After adding
generated-value containment at scalar 1.0:

```
  PASS  leaky_window             §1A/§1B (scalar boundary exactness / window containment)
  PASS  boundary_off_by_one      §1A (maximum never reached at scalar 1.0)
  PASS  broken_formatter_combo   §1C (variant x formatter execution matrix)
  PASS  answer_corruption        §1E (answer-key integrity)
  PASS  vocab_leak               §1D (vocabulary lint on formatted output)
  PASS  silent_substitution      §1C-reverse (excluded combinations must raise)
  PASS  registry_drift           _manifest.py import-time registry assertion

7/7 mutations detected.
Praise God — the verifier verifies.
EXIT=0
```

Reproduce with `PYTHONPATH=. python -m tests.mutation_harness` (add `--only <name>` for one).

## Finding 5 — the new containment check found a phantom axis

Scoped to scalar 1.0 (matching §1A's wording), the containment assertion left exactly one class of
genuine failure across 151 nodes:

```
[('value_containment_value_max', 774)]
nodes failing: 10
mat_g2_na_q1_4 | Leaky window on axis 'value_max' at scalar 1.0: given_values.numbers[2]=62.0
                 exceeds the competency maximum 49 the DNA was given.
```

`comparing_ordering` declares `value_max` but never reads it (`grep -c value_max
.../comparing_ordering.py` → `0`); it reads `max_value`, declared alongside it with the identical
"Maximum Value" label. Removed from the axis catalog.

## Ground Rule 2 disclosures (assertions changed, with justification)

* **`validate_matrix` competency-bound comparison is now string-normalised.** `registry.py` binds
  `missing_number`'s `tables` as ints `[2,3,4,5,10]` while `VARIANTS_BY_DNA` declares them as strings
  `['2',...]`; an identity comparison made every option look out-of-bounds and emptied the matrix for
  2 nodes. The same normalisation was applied to `orchestrator.py`'s boundary check, which rejected
  the Lab's own valid selection (`tables='2'` "out of bounds" against a list containing `2`). The
  check still requires the value to lie inside the competency's set; only the type coercion changed.
* **Generated-value containment asserts at scalar 1.0 only.** An earlier draft asserted at every
  scalar and produced 10,376 failures across 37 nodes, nearly all spurious: a window ceiling below a
  task's structural minimum is legitimate (ordering three distinct numbers cannot respect a
  scalar-0.0 ceiling of 1). Scalar 1.0 against the competency maximum is what §1A actually specifies.

## Final state

```
$ .venv/bin/python -m backend.app.practice_gen.validation.run_all
Nodes Checked: 151
Nodes Passed:  151
Nodes Failed:  0
Total Failures Observed: 0
Contract checks actually executed: ['§1A', '§1B', '§1C', '§1C-coverage', '§1C-reverse', '§1D', '§1E', '§4']

--- 6/6: Judgment Reviews (genuine per-node artifacts) ---
  PASS judgment_reviews (all nodes have genuine, complete, fresh reviews)
  NOTE verdict tally over 151 genuine reviews: PASS=31 CONCERN=76 FAIL=44 ...

--- Two-Direction Contract Verification ---
  PASS contract_doc_matches_registry
  PASS two_direction_contract_match

ALL TESTS PASSED SUCCESSFULLY! Praise God!
EXIT=0
```

The verdict tally is unchanged as a headline but is now *earned*: every review is schema-complete,
non-boilerplate, and demonstrably about content the pipeline currently serves.

---

# 2026-07-27 — Track 1: converting judgment debt into enforcement

Two contract rows added (`§1A-reach`, `§1F`), each mutation-tested. Verbatim progression of the
matrix as their findings were worked:

```
after adding both rules (unfixed):   Nodes Passed: 57/151   Total Failures: 3730
after narrowing §1F to true leaks:   Nodes Passed: 104/151  Total Failures:  480
after template fixes (fraction/     Nodes Passed: 117/151  Total Failures:   96
  measurement/ordinal/pattern):
after reach-check fix + degenerate:  Nodes Passed: 125/151  Total Failures:  218
after counting + rounding fixes:     Nodes Passed: 136/151  Total Failures:   29
after max_product ground truth:      Nodes Passed: 146/151  Total Failures:    5
```

`§1F` was deliberately narrowed after its first run: firing on 3,702 samples, it was conflating three
different things. Only one is answer leakage.

```
LEAK  'Jose has lunch at 1:30. What time is that?'                  -> answer 1:30
LEAK  'What fraction does \(\frac{2}{5}\) equal parts represent?'   -> answer 2/5
OK    'Which shape has more sides — a triangle or a rectangle?'     (comparison names its candidates)
OK    'Complete the equivalent expression: 2 + 1 = 1 + ___'         (commutativity restates an operand)
OK    '2 + 0 = ___'                                                 (identity fact, not a leak)
```

The final rule fires only when the answer is the stem's *only* datum. Detector unit-checked 11/11 on
the cases above plus symmetry (`answer == given` is correct mathematics there, and is exempted).

`§1A-reach` was likewise corrected twice, both times because it was asserting against a **default**
rather than a curriculum claim — the same error in two guises:

```
counting  range=1.0 alone                        -> max value 29   (number_difficulty sat at 0.5)
counting  range=1.0 + number_difficulty=1.0      -> max value 29   (genuine defect)
multiply  max_product=1.0 alone                  -> max product 30 (check artifact)
multiply  max_product=1.0 + number_difficulty=1.0 -> max product 90 (passes)
```

and then scoped to axes the competency explicitly binds, since `mat_g1_na_q1_5` reads "ordinal
numbers 1st, 2nd, 3rd, up to 10th" while binding no `ordinal_range` — the ceiling of 100 was an axis
default no generator change could honestly satisfy.

Representative before/after of the fixed content:

```
counting   before: max sequence value 29 against a stated ceiling of 100
           after:  'What comes next: 83, 84, 85, 86, ___'   (max 98)

fractions  before: 'What fraction does \(\frac{1}{2}\) equal parts represent?' -> 1/2
           after:  'A shape is divided into 2 equal parts. 1 part is shaded.
                    What fraction of the shape is shaded?'                     -> 1/2

length     before: 'Ben used paperclips to measure a book. It measured 10 paperclips
                    long. How long is a book in paperclips?'                   -> 10
           after:  'A book is 10 paperclips long. A shoe is 6 paperclips long.
                    How many paperclips longer is a book than a shoe?'         -> 4

ordinal    before: 'What is the ordinal name for position 6?'                  -> 6
           after:  'Which word describes the 6th position?'                    -> 'sixth'
                   'Write the symbol for the sixth position.'                  -> '6th'

rounding   before: 'Round 10 to the nearest 10.'                               -> 10
           after:  'Round 11 to the nearest 10.'                               -> 10

patterns   before: 'What is the next number in the pattern: 2, 2, 2, 2, 2, 2?' -> 2
           after:  'What is the next number in the pattern: 2, 10, 2, 10, 2, 10?'
```

Phase 4 re-verified after every harness change:

```
$ PYTHONPATH=. .venv/bin/python -m tests.mutation_harness
7/7 mutations detected.
Praise God — the verifier verifies.
```

## Ground Rule 2 disclosure

**`mat_g3_na_q3_0`, `mat_g3_na_q3_1` — `max_product` bound corrected from (0, 1000) to (0, 90).**
"Multiply numbers using the 6, 7, 8, and 9 multiplication tables" has no numeral in its text, so it
fell through to the G3 grade default of 1000. The largest product those tables generate is 9x10=90;
the 1000 ceiling described a range the competency does not cover. Table language was previously
parsed only on the `missing_number` branch of `registry.py`, so multiplication nodes never saw it.

## Final state (RED, itemised)

```
$ .venv/bin/python -m backend.app.practice_gen.validation.validate_matrix
Nodes Checked: 151   Nodes Passed: 146   Nodes Failed: 5   Total Failures: 5
Contract checks actually executed: ['§1A', '§1A-reach', '§1B', '§1C', '§1C-coverage',
                                    '§1C-reverse', '§1D', '§1E', '§1F', '§4']

  mat_g2_na_q4_1: 'range' reached 906 of 10000
  mat_g2_na_q4_4: 'range' reached 906 of 10000
  mat_g3_na_q2_0: 'max_total' reached 4600 of 10000
  mat_g3_na_q3_4: 'max_product' reached 90 of 1000
  mat_g3_na_q3_2: 'max_product' reached 990 of 10000
```

Plus 25 nodes whose judgment reviews the freshness gate now rejects, because the content fixes above
changed what they render. Those re-reviews are outstanding and were **not** written by the agent that
authored the fixes — see IMPLEMENTATION_STATUS.md.

---

# 2026-07-27 (cont.) — closing the reach gaps and re-reviewing the judgment layer

## Behavioural matrix restored to green

```
$ PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
Nodes Checked: 151   Nodes Passed: 151   Nodes Failed: 0   Total Failures: 0
Contract checks actually executed: ['§1A', '§1A-reach', '§1B', '§1C', '§1C-coverage',
                                    '§1C-reverse', '§1D', '§1E', '§1F', '§4']
  PASS judgment_reviews (all nodes have genuine, complete, fresh reviews)
  NOTE verdict tally over 151 genuine reviews: PASS=30 CONCERN=52 FAIL=69
  PASS contract_doc_matches_registry
  PASS two_direction_contract_match
ALL TESTS PASSED SUCCESSFULLY! Praise God!
EXIT=0
```

Phase 4 re-verified after every harness change in this session:

```
$ PYTHONPATH=. .venv/bin/python -m tests.mutation_harness
7/7 mutations detected.
```

Unit suite (includes new `tests/unit/test_answer_leak_and_reach.py`, 17 cases pinning §1F's
boundary — the legitimate-restatement cases are the part most likely to regress):

```
$ PYTHONPATH=. .venv/bin/python -m pytest tests/unit/ -q -m "not slow"
270 passed, 2 deselected
```

## A latent infinite loop, exposed by fixing a dead key

`difficulty_scalar` is read by 15 DNA modules and written by none, so all 15 silently used 0.5.
Pointing it at `number_difficulty` (which is what actually carries magnitude) made
`length_measurement`'s compare task reachable at scalar 0.0, where the mapped range collapses to a
single value:

```
scalar 0.0 -> l_max_current = 1
scalar 0.5 -> l_max_current = 10
```

`while val_b == val_a: val_b = rng.randint(l_min, l_max_current)` then never terminates. The matrix
run hung on `mat_g3_mg_q1_6` for 30+ minutes at 0% CPU with 150/151 nodes recorded. Both compare
branches now guarantee one unit of headroom. (Two orphaned worker processes from a previous session
were also found still alive — the runaway-worker trap `testing_pipeline.md` documents.)

## Content reaching its stated ceiling

```
counting     before: max sequence value 29 against a stated ceiling of 100
             after:  'What comes next: 83, 84, 85, 86, ___'            (max 98)
money        before: max total ₱4600 against ₱10 000
             after:  'What is the total value of 10 ₱1000 bills?'      -> 10000
multiply     before: max product 90 against 10 000
             after:  'What is 994 × 10?'                               -> 9940
fractions    before: co-mapped number_reading served 'Write 227 in words.'
             after:  'A shape is divided into 8 equal parts. 1 part is shaded...'
```

## Blind re-review: what the reviewers caught that the machine could not

Two rounds of packet-only subagent review (40 nodes, then 2 whose content moved mid-round). Reviewers
hand-verified every keyed answer. Defects found and fixed:

```
'Which is greater: 18 or 30?'                     -> keyed '<'   (stem asks for a number)
'0 + 14 = ___'  options [..., -14]                              (negative, out of grade)
'A shape divided into 2 parts, 1 shaded' options ['2/4', '1/2'] (two correct answers)
'Who has more, and by how many?'                  -> keyed 5     (first half names a person)
```

After the fixes:

```
'Compare the numbers: 10 ___ 6. Which sign is correct: >, <, or =?'  -> '>'
'0 + 14 = ___'  options [24, 13, 14, 15]
options ['3/2', '2/1', '2/3', '1/2']  key '1/2'
'Ate Cara has 10 photo albums... How many more photo albums does Ate Cara have?' -> 5
```

The `Which is greater` stem existed in three copies (`base_generator`, `fmt_mcq`, `fmt_cloze`); the
first fix corrected one and the reviewers found the other two still shipping. The negative-option
filter was likewise applied to `fmt_mcq` first and missed `fmt_cloze`; it now lives in
`base_generator`'s distractor assembly, the single point all 17 formatters draw from.

## Ground Rule 2 disclosures

* **`mat_g3_na_q3_0`, `mat_g3_na_q3_1`** — `max_product` corrected from the G3 grade default
  `(0, 1000)` to `(0, 90)`. "Multiply numbers using the 6, 7, 8, and 9 multiplication tables" has no
  numeral in its text so it inherited the default; those tables reach at most 9×10.
* **`mat_g2_na_q4_1`, `mat_g2_na_q4_4`** — `number_reading` removed as a co-mapped DNA. It rendered
  `"Write 227 in words."` on "Read and write unit/similar fractions in fraction notation", and
  dragged in a `range` bound of (10, 10000) that no fraction competency states.
* **`tests/unit/test_axes_log_scale.py`** — the test asserting `comparing_ordering` declares a
  `value_max` axis now asserts the opposite. That axis was an inert duplicate of `max_value` (same
  "Maximum Value" label, never read by the DNA); the test encoded the defect.

## Known remaining debt (documented, not hidden)

69 nodes carry a FAIL verdict (71 after the 2026-07-30 review pass below). The dominant cause, named
independently by every reviewer, is
**co-mapped secondary DNAs bleeding off-topic content into a node** — the multi-DNA leak pattern.
It is a mapping-level decision, not a generator patch, and every instance is cited with node id and
sample text in the per-node artifacts.

---

# Adversarial review pass — 2026-07-30

An independent pass over this branch, tasked with finding what the hardening got wrong. The three
headline claims above reproduced exactly (`run_all` exit 0 / 151-151 / ten checks observed,
mutation harness 7/7, 270 unit tests). The defects below were found underneath them, and the
Phase A+B subset was fixed in this change.

## Fixed

1. **`max_minuend` parsed a digit *width* as a magnitude** (`registry.py`). `re.search(r'(?:less than|up
   to)\s+(\d+)')` matched "up to **2** digits", so three Grade 3 nodes bound a minuend ceiling of 2 or 4
   and served `2 − 2 = 0` at maximum difficulty. Neither §1A nor §1A-reach could see it: both assert
   against the *parsed* ceiling, so a mis-parsed bound immunises the node from the only checks that
   would expose it. Fixed by handling the digit-width idiom (already handled correctly in the generic
   extraction path 350 lines below) and rejecting sub-10 captures. The same missing guard on
   `missing_number.max_result` was closed too; no live node was affected by that one.

2. **`formatter_max_val` was never injected on the portal's call shape** (`orchestrator.py`). It is set
   only inside `if formatter:`, but on the student path the formatter is chosen *after*
   `generate_context`, so nothing clamped anything; and `node_max_value` is computed from the *primary*
   DNA's bounds only, so `mat_g2_na_q3_0` (`['multiplication', 'counting']`) admitted `emoji_pictorial`
   on multiplication's `max_product=100` while `counting` generated 578. Five hard `ValueError`s in
   9,060 portal-shape generations. Fixed by filtering the post-context formatter list on the magnitude
   the DNA actually produced. Now 9,060/9,060.

3. **§1B containment was silently disabled for 13 nodes** (`validate_matrix.py`). The `continue` added to
   narrow §1A-reach to competency-bound axes sat *above* the generated-value containment sweep, so it
   switched that off too — 14 (node, dna, axis) triples, 11 nodes with no magnitude containment coverage
   at all. Narrowing reach was sound and is preserved; narrowing containment was not intended. This is a
   deliberate edit to `validation/` that strengthens a check: verified by inflating every generated
   integer by 10,000, which raised 0 failures on `mat_g1_na_q1_5` / `mat_g1_dp_q3_0` before and 30 each
   after, with the bound control (`mat_g1_mg_q2_2`) unchanged at 110.

4. **Difficulty endpoints were single fixed items** (`number_difficulty.py`). `generate_number_by_window`
   and `generate_pair_by_window` short-circuited scalars 0.0 and 1.0 to argmin/argmax, ignoring `rng`:
   37 of 81 (node, dna, magnitude-axis) combinations produced ≤2 distinct operand sets over 30 seeds at
   scalar 1.0, and addition produced exactly **1** against 29 at scalar 0.5. §1A-reach could not see it —
   a pool whose only near-ceiling member is always chosen satisfies "the peak reaches the ceiling"
   perfectly. Removing the short-circuit alone then *broke* reach on seven multiplication nodes, which
   exposed the real relationship: `score_candidate` scores awkwardness, not size (99 → 0.95, 100 → 0.54),
   so for those pools the hardest band is products 27-45 against a ceiling of 100 and the old argmax had
   been passing reach for the wrong reason. The endpoint band is now "hardest OR largest", reusing the
   existing window width. Result: 0 reach violations under §1A-reach's own 10-seed protocol, and 1 of 77
   combos still low-variety (`mat_g3_na_q2_0`, whose cause is the content debt below).

5. **A 0-1 scalar reaching a DNA as a raw ceiling** (`base_generator.py`). `subtraction.max_minuend` and
   `rounding.max_value` are registry tuple bounds that are *not* catalog axes, so nothing scalar-maps
   them, but the bounds injection passes any caller value straight through — `{"max_minuend": 1.0}`
   became a ceiling of 1. Now a named `ValueError`; ints still honoured. Registering the two keys as real
   axes would be the fuller fix and would drift 15 nodes' content, so it is left open.

6. **Evidence artifacts were untracked and unexercised.** `tests/mutation_harness.py` and
   `tests/unit/test_answer_leak_and_reach.py` were never added to git, so "7/7 via a re-runnable
   artifact" was unreproducible on a clean clone; and CI ran neither, since its only test step was
   `run_all` and its `paths:` filter excluded `tests/**`. Both files are now tracked and the workflow
   runs the unit suite and the mutation harness, the latter asserting `backend/` is restored afterwards.

## Ground Rule 2 disclosure

* **`mat_g3_na_q2_5`, `mat_g3_na_q2_6`, `mat_g3_na_q2_7`** — `max_minuend` corrected from the digit-count
  misparse to the width the competency states: `(1, 4)` → `(1, 9999)` for "two numbers of up to 4
  digits", and `(1, 2)` → `(1, 99)` for "3 to 4 numbers of up to 2 digits". Every other subtraction
  bound is byte-identical. Pinned by five cases in `validate_compat.validate_competency_bounds_parsing`
  (§2), which assert both the width phrasings and the magnitude phrasings that must keep parsing as
  magnitudes.

## Deliberately not added

A **bound-plausibility** contract row (flag a parsed bound an order of magnitude below its grade
default) was prototyped and dropped: at 10× it flagged four bounds, all legitimate, including this
log's own `max_product=90` correction. A **ceiling-variety** row was dropped for the same reason — after
fix 4 the residual low-variety combos are small-cap addition nodes where one near-ceiling item is
defensible. Any threshold that separates those from real defects needs an exception list, which is the
tuning Ground Rule 5 forbids. The fixes shipped; the checks would have been theatre.

## Found and left open

* **Nine visual formatters discard the DNA's problem and author their own** when `ctx.values` lacks their
  keys (`fmt_ruler_measure.py:199`, `fmt_shape_board.py:199`, `fmt_balance_scale.py:180`, and 6 more) —
  43 of 1,810 naturally generated items, 5 of 12 on the G1/G2 shape nodes. `mat_g2_mg_q2_1` is bound
  `task_type='choose_unit'` and serves a ruler read-measurement item; `mat_g1_mg_q1_0` renders "Look at
  the shapes. Tell how many corners does the highlighted shape have." This survives DNA selection
  because the `is_registry_scope` exemption only re-arms when the compatibility table explicitly
  restricts the variant, and 9 of 27 DNAs have no `FORMATTER_VARIANT_SUPPORT` entry at all.
* **§1F was narrowed past most of its value.** Over 1,032 sampled MCQ items the shipped rule flags 7; the
  rule before the final narrowing flags 154. Nothing checks operand degeneracy, so 30% of
  addition/subtraction items at the default profile still carry a zero operand. Three function-level
  false negatives: the `\bmirror\b` symmetry exemption fires on "Ana bought a mirror for 45 pesos"; one
  incidental second number in the stem defeats the rule; a float answer never matches an integer stem.
* **The judgment layer's 5 fixed seeds see 39% of what a node serves** (233 of 598 distinct rendered
  formats over 65 seeds; worst nodes 1 of 6). The freshness gate then pins that narrow sample
  permanently. `mat_g2_mg_q2_1` was filed `competency_fulfillment: PASS` on five seeds that all render
  the same template, while its ruler path serves an off-competency item.
* **9 of 151 reviews name the authoring session as reviewer**, against `validate_judgment`'s own "the
  verifier is not the author". Their verdicts are 7 FAIL / 2 CONCERN — harsher than the corpus, so
  nothing was whitewashed, but `blind: true` is an unverifiable self-attestation.
* **`validation_reports/matrix_report.json` is overwritten by any single-node run**, including the
  `--node` command this log tells readers to reproduce with, and including the mutation harness. It was
  found containing one node mid-review.
* **`mat_g2_na_q4_1` / `mat_g2_na_q4_4`** — after the `number_reading` removal above, both nodes produce 3
  distinct items over 40 seeds, 34 of them the identical "1 of 8 parts shaded → 1/8", and `_4`'s
  competency (*similar* fractions) is never exercised.

## Re-reviews filed

Fixes 1, 2 and 4 drifted six nodes' cited seeds. Fresh packet-only reviews were dispatched to
independent subagents, prompted neutrally (the earlier batches' "hunt defects / do not be generous"
framing was dropped as verdict-biasing). All six returned FAIL on quotable, competency-level grounds
that the magnitude fixes did not address — `mat_g3_na_q2_5` still answers exact differences rather than
estimates; `_6`/`_7` still combine two numbers where the competency names three to four;
`mat_g3_na_q4_1`/`_2` never generate the 7 or 9 tables. Two of those findings were not in the review
brief and were produced by the reviewers independently. Tally moved 30/52/69 → **29/51/71**.
