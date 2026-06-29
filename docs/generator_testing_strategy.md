# Generator Testing Strategy

## Why Previous UI Tests Were Inaccurate
Initially, I mistakenly relied directly on the backend's `router` tests without ensuring that all the variables mimicking the frontend (`format_preference`, `axis_values`) were correctly passed down to the `pipeline.run` method and subsequent generator layers. The frontend UI forces particular variants (such as `pictograph_set`) which the backend fell back to defaulting in tests, completely obscuring issues with missing `task_type` attributes. Essentially, my tests were checking the backend's "happy path" logic rather than the precise endpoints hit by the student portal's UI payload.

## Guaranteeing UI-Parity in Testing
To fix this, I developed `fuzzer.py` which intercepts the actual list of nodes (`axes_catalog.py`) and emulates the exact frontend POST requests by building valid HTTP query URLs matching `/api/matatag/lab/generate?node_id=...&format_preference=...&axis_values=...`. 
1. The fuzzer enumerates *every* formatter listed in the capabilities list for a node.
2. It generates valid permutations of boundary conditions for all `continuous` sliders.
3. It validates that the backend returns the `FormattedProblem` with `format_used` properly matching the `format_preference`, and it confirms that the `mcq_options` list is never empty unless explicitly allowed.

By running this fuzzer across all 151 competencies simultaneously, I surfaced exactly what a user would see on the UI for any configuration. Through multiple runs, I successfully zeroed out all generator errors, including `Empty mcq_options` and `Candidates list cannot be empty`.

## Manual Output Validation Plan (The "10-Problem Cross-Axis Test")
After resolving errors according to `difficulty_dimensions.md` and `pgen_checklist.md`, we must manually verify 10 problems per configuration.

**Testing Matrix for each Competency:**
1. **Difficulty Dimensions:** Test boundaries `scalar=0.0`, `0.5`, `1.0`. For overlapping continuous dimensions, ensure they operate independently (e.g., `number_difficulty` vs `range` boundaries).
2. **Contextual Variants:** Iterate through pure math equations and word problems.
3. **Formatters:** Test every supported UI interaction type (`mcq`, `cloze`, `pictograph_set`, etc).

**Evaluation Criteria:**
- **Strict Scalar Mapping:** Does `scalar=0.0` reliably output the lowest range bounds without crashing or overlapping with higher bounds?
- **Cognitive Fidelity:** Do the problems match the exact grade-level expectations?
- **Variant Independence:** Does adding a contextual variant (e.g., word problem) accidentally alter the underlying numerical difficulty?
- **UI Renderability:** Are visuals perfectly aligned and inputs clearly marked?

**Next Steps:**
I will proceed to review the overlapping continuous dimensions across the DNAs and adjust bounds before initiating the manual output inspection.
