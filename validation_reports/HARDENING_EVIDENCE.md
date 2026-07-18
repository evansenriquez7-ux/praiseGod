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
