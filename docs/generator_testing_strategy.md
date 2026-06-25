# Comprehensive Generator Testing Strategy

This document outlines how the `float('three_four')` crash was discovered in the MATATAG Lab, and provides a systematic plan for an autonomous agent to test all learning competencies to identify and fix similar bugs.

## How the Error Was Reproduced
The initial testing of the backend generator using default parameters (e.g., passing `difficulty_profile=None`) yielded zero errors. The generator only crashed when triggered *from the frontend UI*. To uncover the issue, we mirrored the exact data flow of the Matatag Lab:

1. **Analyzed the Frontend Lab Configuration:** We queried `/api/matatag/lab/config/mat_g3_dp_q3_0` and inspected the returned `difficulty_dimensions`. We noticed that `num_categories` was designated as `dim_type: "discrete"`, with options containing string levels (e.g., `level: "three_four"`).
2. **Traced the Frontend Request Payload:** We analyzed `fetchMatatagQuestion` in `App.jsx` and found that for `discrete` dimensions, the frontend explicitly populates the `difficultyProfile` with the string `level` rather than a numeric scalar.
3. **Simulated the Frontend Payload in Python:** We created a test script that imported the backend generator's `run()` function and passed a mock `difficulty_profile` identical to the frontend's payload:
   ```python
   dp = {
       "scale_type": "no_scale",
       "task_type": "read_single",
       "num_categories": "three_four"
   }
   run("mat_g3_dp_q3_0", student_grade=3, difficulty_profile=dp)
   ```
4. **Identified the Root Cause:** The generator immediately crashed with `ValueError: could not convert string to float: 'three_four'`. The DNA generator for pictographs (`pictographs.py`) expected `num_categories` to be a continuous float scalar and erroneously tried to parse the discrete string level. 

---

## Agent Execution Plan

To systematically eliminate these issues across the entire platform, an agent should run a comprehensive fuzzer against the `practice_gen` pipeline, mirroring the exact configurations served to the frontend.

### Step 1: Discover All Learning Competencies
- Use `get_all_node_ids()` from `backend.app.practice_gen.registry` to get a list of all MATATAG node IDs.

### Step 2: Fetch the Valid Configuration Schema
For each `node_id`:
- Query the lab configuration (mimicking the `/api/matatag/lab/config/{node_id}` endpoint). You can invoke `get_matatag_lab_config(node_id)` from `matatag_router.py`.
- Extract the `difficulty_dimensions`, `contextual_variants`, and `formatters` exposed by the configuration. 

### Step 3: Construct Frontend-Accurate Payloads
- Generate test matrices for the node.
- **Difficulty Profiles:** 
  - If a dimension is `dim_type: "continuous"`, pick the numeric `value`.
  - If a dimension is `dim_type: "discrete"`, pick the string `level`.
  - Test edge cases (easiest config, hardest config, and random permutations).
- **Variants:** Pair the difficulty profiles with all valid `contextual_variants`.
- **Formatters:** Run the generated profiles against every valid formatter defined in the `formatters` list for that config.

### Step 4: Fuzz the Generator Pipeline
- Pass the constructed payloads into `backend.app.practice_gen.pipeline.run(node_id=node_id, difficulty_profile=profile, variant_values=variants, formatter=formatter)`.
- Wrap the execution in a `try...except` block.

### Step 5: Log and Fix
- If an exception occurs (e.g., `ValueError`, `TypeError`, `KeyError`), log the stack trace, the exact `node_id`, and the JSON payload that caused it.
- Trace the error into the specific DNA file (e.g., `dna/dp/bar_graphs.py` or `dna/na/addition.py`) and fix the parsing logic so it safely handles the payload provided by the lab configuration.
- Continue testing until all combinations for all nodes yield a 100% success rate.
