# PGEN Checklist Audit Report (Grades 1-3)

## 1. Difficulty Dimensions
**Status:** Incomplete / Misaligned

**Findings:**
- **Misuse of `number_difficulty`:** Almost all DNA generators (including `counting.py`, `addition.py`, etc.) map their core difficulty strictly to the `number_difficulty` axis. However, as noted in the `pgen_checklist.md`, continuous `number_difficulty` is generally **not appropriate** for pure counting-based competencies. The parameter bounds (like `max_num`) are being derived from `number_difficulty` instead of a proper progression aligned with the learning competency.
- **Strict Scalar Mapping:** The `difficulty_scalar` is mapped linearly or logarithmically to numerical bounds, but this strictly controls numerical range, failing to address cognitive progression like regrouping or spatial complexity.

**Required Fixes:**
- Update `counting.py` and other structural DNA files to use dimensions like `range` instead of defaulting to `number_difficulty`.
- Ensure the parameter generation in generators explicitly respects the true `difficulty_scalar` and the specific difficulty axes defined in the DNA `_DIFFICULTY_AXES`.

## 2. Contextual Variants
**Status:** Missing Coverage

**Findings:**
- Several competencies lack comprehensive contextual variants. For example, `peso_money` only has `pure` and `word_problem` context, but lacks variants for "making change", "giving money", etc. 
- Some visual formatters do not gracefully handle these variants. 

**Required Fixes:**
- Expand the variants in `VARIANTS_BY_DNA` in `compatibility.py` to ensure all logical variations for each concept are included.

## 3. Formatters (Problem Types)
**Status:** Rendering and Interactivity Errors

**Findings:**
- **PesoMoney Formatter:** In `registry.py`, money-related competencies (e.g., `mat_g1_na_q4_4` through `mat_g1_na_q4_6`) are incorrectly mapped to the static `peso_money_read` visual. The directions indicate interactive problems where the user must "determine the value" or "solve 1-step problems", which requires `peso_money_build` (interactive) so the student can select coins/bills.
- **ClockSet Formatter:** While `clock_set` exists, the interactive mode requires `interaction_mode="set"`. If not passed correctly by the backend generation logic, the clock remains static and not interactive as expected.
- **State Updates in React Effects:** `VisualSkeletons.jsx` had critical React rendering anti-patterns (e.g., `react-hooks/set-state-in-effect`), which caused cascading re-renders. This prevented interactive formatters from rendering correctly. (Partially mitigated through code refactor, but deeper logic fixes in prop-handling may be required).

**Required Fixes:**
- Update `registry.py` to map interactive tasks directly to interactive formatters (e.g., `peso_money_build`, `clock_set`).
- Ensure the backend generators (e.g., `money_peso.py`) supply `is_interactive: true` to the visual schema when the formatter dictates interactivity.

## 4. Final Review
**Status:** Audit Ongoing

**Conclusion:** 
The generation pipeline has significant structural gaps connecting the backend DNA definition to the frontend interactive formatters. A comprehensive sweep updating `registry.py` and the DNA parameter generators is required to satisfy the `pgen_checklist` for all Grade 1-3 competencies.
