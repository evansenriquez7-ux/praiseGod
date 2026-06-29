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

## The Limitations of the Fuzzer & The AI Static Analysis Strategy
While the `fuzzer.py` strategy effectively eliminated 500s and ensured the backend generated valid JSON structures, **it was fundamentally incomplete because it lacked semantic awareness of the frontend**. The fuzzer could only prove that the backend sent a payload; it could not detect if the React components in `VisualSkeletons.jsx` were misinterpreting that payload.

Because the fuzzer was blind to the UI layer, it completely missed severe logical flaws, such as:
1. **Answer Leaks:** Components rendering the exact `correct_answer` in plain text during `read` mode.
2. **State Overwrites:** React `useEffect` hooks automatically firing `onAnswer()` on-mount, grading the student before they interacted.
3. **Missing Interactivity:** Components declaring `interaction_mode="set"` but completely missing the UI bindings to actually capture user input.
4. **Data Type Mismatches:** Frontend components passing complex objects back to the evaluator instead of the expected integer.

**The Solution: Multi-Agent Static Analysis**
To catch these UI/Logic bugs without building complex headless browser suites, we implemented a "Hub-and-Spoke" AI QA strategy:
1. **Batching:** We extracted all unique visual formatters from the backend registry.
2. **Subagent Delegation:** We spawned a pool of specialized `CompetencyPgenAuditor` subagents, assigning each a batch of visual components. 
3. **Static Audit:** Each subagent cross-referenced the backend formatter (e.g. `fmt_calendar.py`) against its React counterpart (e.g. `CalendarInteractive`) to hunt for state management bugs and answer leaks based on the strict rules in `pgen_checklist.md`.
4. **Centralized Resolution:** The agents reported their findings to the lead agent, producing a comprehensive `visual_components_audit.md` which was used to systematically patch the entire platform. 

This token-efficient static analysis succeeded where the fuzzer failed, uncovering and fixing deeply embedded interactivity bugs across the entire curriculum in a matter of minutes.
