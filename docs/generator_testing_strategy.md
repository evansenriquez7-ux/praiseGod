# Comprehensive Generator Testing Strategy

This document outlines how we diagnosed and resolved fundamental discrepancies between the Matatag Lab and the Student Portal, and provides a systematic plan for testing all 151 learning competencies to ensure absolute adherence to the prescribed difficulty dimensions, contextual variants, and formatters.

## Diagnosis: Why the UI Output Was Masked
Initially, we were unable to accurately identify what was showing in the Matatag Lab and Student Portal because our test simulations were flawed. When building the test script, we hardcoded the Matatag Lab simulation to force the **maximum possible value** (`max(v)`) for every single difficulty dimension. 
1. **The Artificial Ceiling**: This manual override forced the generator to act as if a user had dragged every slider in the Lab to 100% difficulty, outputting only the absolute hardest variants (e.g., locking minuends at `1000`). 
2. **Missing the "Floor" Flaw**: Because our test script forcefully clamped the difficulty to the ceiling, we completely bypassed and missed the real bug occurring at the 0th percentile (the "floor"), where unbounded generation was producing tiny, inappropriate numbers like `1 - 0`. 
3. **The Routing Bug**: The simulation assumed the Lab endpoint was using the database configuration (like the Portal does), but we failed to realize `matatag_lab_generate` was missing its database dependency and completely ignoring the user's checked boxes.

## Resolution: Ensuring UI-Accurate Testing
To ensure our tests see exactly what the user sees, we realigned the testing architecture:
1. **Single Source of Truth**: We patched `matatag_router.py` to inject the database dependency into the Lab generation endpoint. Both the Portal and the Lab now exclusively pull from `CompetencyConfiguration` in the Postgres database.
2. **Organic Sampling Simulation**: We removed the `max(v)` hardcoding from the test scripts. Instead of forcing manual slider inputs, the test script now passes `{"range": 0.5}` or relies on the allowed lists from the DB, perfectly mirroring how the orchestrator organically samples from the `allowed_difficulties` array (e.g., `rng.choice(opts)`). This exposes the full spectrum of outputs—including the broken floors (e.g., `1 - 0 = 1`) and formatter anomalies (e.g., negative numbers in True/False).

---

## Agent Execution Plan: Validating All 151 Competencies

To ensure every generated problem strictly follows the chosen options and curriculum constraints, an agent must execute the following end-to-end plan across all 151 competencies.

### Phase 1: Pre-Test Configuration Auditing
Before testing the outputs, the agent must fix overlapping dimension configurations according to `pgen_checklist.md` and `difficulty_dimensions.md`.
1. **Audit `axes_catalog.py`**: Scan all continuous difficulty dimensions (especially those with linear scales and `divisions=5`). Identify overlapping outputs where `min_val` and `max_val` are too close (e.g., resulting in scalar options like `[1, 1, 2, 2, 3]`).
2. **Fix Overlaps**: Adjust the divisions, apply logarithmic scaling, or raise the `min_val` to ensure each tick on the slider provides a distinct, monotonically increasing scalar value.

### Phase 2: Systematic Fuzzing & Matrix Generation
For every single `node_id` in the `backend.app.practice_gen.registry`:
1. **Fetch Config**: Query `get_matatag_lab_config(node_id)` to extract all available `difficulty_dimensions`, `contextual_variants`, and `formatters`.
2. **Matrix Construction**:
   - For every continuous dimension, iterate through every generated scalar division.
   - For every discrete dimension, iterate through every level.
   - Pair each difficulty profile with every allowed contextual variant.
   - Route the combination through every compatible formatter.
3. **Execution Run**: Run `pipeline.run()` to generate **10 distinct problems** for each unique combination in the matrix.

### Phase 3: Heuristic Output Validation
As the 10 problems are generated, the agent will dynamically inspect the outputs to ensure they strictly follow the requested options:
1. **Difficulty Adherence**: If the dimension is set to the lowest level (e.g., `number_difficulty=0`), verify the numbers are grade-appropriate (no `1 - 0` in Grade 3). If it is set to max, verify the numbers hit the cap.
2. **Variant Consistency**: If the variant is `structure: "change_unknown"`, parse the question text and `options` to ensure the structure strictly matches the definition (e.g., $A \pm x = C$).
3. **Formatter Integrity**: Check the raw formatter outputs. Ensure `true_false` traps do not generate mathematically or pedagogically invalid traps (like negative numbers for 3rd graders) and that the text is properly constructed.
4. **DNA/Intent Check**: Verify the underlying DNA is preserved. For instance, if the competency requires "Estimation", ensure the presence of the `true_false` formatter does not silently override the `rounding` DNA and revert to exact arithmetic.

### Phase 4: Resolution & Patching
- Log any configuration overlap, logical failure, crash, or heuristic violation.
- Trace the failure directly to the responsible DNA file (e.g., `subtraction.py`), registry bound, or formatting handler (`fmt_true_false.py`).
- Implement the fix, then immediately re-run Phase 2 for that node to guarantee success before moving to the next.
