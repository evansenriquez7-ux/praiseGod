# Metamorphic Testing Pipeline & Checklist Compliance Auditor

Praise God! This document serves as the master operational guide for any agentic coder building, modifying, or auditing practice problem generators (PGs) in this repository. 

Our testing philosophy is built on **failing fast and loud** rather than silent defaulting. This document outlines the architecture, checks, execution CLI, and troubleshooting steps for the metamorphic testing pipeline.

---

## 1. Core Philosophy

Unlike standard unit testing, which only verifies that code runs without raising exceptions, our testing pipeline enforces **metamorphic testing**. It validates the *relationship* between generated outputs across toggled inputs (variants, difficulty scales, and formatters). 

If a PG falls back silently to a default setting or fails to alter its mathematical presentation when parameters change, the pipeline flags a violation immediately.

---

## 2. The Core Verification Checkpoints

The checklist auditor ([exhaustive_checklist_auditor.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/tests/exhaustive_checklist_auditor.py)) runs four distinct metamorphic checks across all generated question variants:

### A. Strict Scalar Mapping (Boundary Checks)
- **Rule**: A difficulty scalar of `0.0` must map strictly to the easiest curriculum bounds, and `1.0` must map strictly to the hardest bounds.
- **Verification**: The auditor generates problems at `0.0`, `0.5`, and `1.0`. It asserts that the output values are bounded correctly inside the difficulty windows without any overlap or out-of-bounds parameter leakage.

### B. Metamorphic Sensitivity Checks
- **Rule**: Changing a conceptual variant (e.g. context, operator, blank position) must result in a distinct question stem.
- **Verification**: The auditor generates problems using the exact same seed while toggling the target variant. If the stems produced are identical (e.g., word problem stem matches pure symbolic stem), it flags a `Sensitivity Violation`.

### C. Semantic Leak Safeguards
- **Rule**: The correct answer or distractors must not be leaked inside the question stem.
- **Verification**: The auditor recursively extracts all scalar numbers, strings, and floats from the generated answer and checks them against the text of the question stem. Any matches (except registered curriculum carve-outs) raise a `Semantic Leak` error.

### D. Formatter and Choice Validity Checks
- **Rule**: Formatters (like MCQ, True/False, Balance Scale) must generate valid structures without duplicates or hardcoded default selections.
- **Verification**: The auditor checks MCQ options to ensure they are unique, contains the correct answer exactly once, and have no duplicate choices.

---

## 3. CLI Execution Guide

### Run Full Curriculum Audit
To audit all 151 curriculum nodes across Grade 1 to 3 (which checks over 1.5 million problem variants):
```bash
bash tests/run_checklist_audit.sh
```

### Run Targeted Node Audits
To debug a specific set of nodes during development:
```bash
bash tests/run_checklist_audit.sh --node-ids mat_g1_na_q1_6,mat_g3_na_q4_2,mat_g3_dp_q3_4
```

### Command Location
The auditor is run via the wrapper shell script [run_checklist_audit.sh](file:///Users/enrichmentcap/Documents/antigravity/ccmed/tests/run_checklist_audit.sh) which sets up the proper Python environment and invokes the underlying runner.

---

## 4. Diagnostics & Troubleshooting Guide

When the auditor flags a compliance failure, follow these step-by-step diagnostic paths to find the root cause:

### Case A: Sensitivity Violation on `context` (Stem did not change)
* **Symptom**: Both `"pure"` and `"word_problem"` contexts generated the exact same symbolic equation stem.
* **Root Cause 1**: The DNA registers `requires_context=False`. Story spines will not be selected unless `requires_context=True` is set on the DNA object.
* **Root Cause 2**: Story spine lookup returned `None`. This happens when `cumulative_concepts` in the node doesn't match the concepts required by the story spines, or the `blank_position` is not mapped to the target fields inside [base_generator.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/backend/app/practice_gen/generators/base_generator.py) (e.g., `"start"` must map to `"a"`, `"change"` to `"b"`, `"result"` to `"total"`, etc.).

### Case B: Sensitivity Violation on `operation` (Operator did not change)
* **Symptom**: Toggling `"addition"` vs `"subtraction"` (or `"multiplication"` vs `"division"`) produced identical parameter sets.
* **Root Cause**: The active DNA's `generate_params()` logic has a hardcoded operator or locks parameters without reading the selected variant from the profile. Inspect the DNA file's `generate_params` loop.

### Case C: Formatter Compat Crash
* **Symptom**: Auditor exits with a `ValueError` saying `Formatter 'x' is not supported by any DNA for node 'y'`.
* **Root Cause**: A multi-DNA node has registered a formatter that is incompatible with the variants enabled by one of its DNAs. Restrain the formatter to `"context": ["pure"]` in `FORMATTER_VARIANT_SUPPORT` inside [compatibility.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/backend/app/practice_gen/compatibility.py).

---
