# PG Pipeline Judgment Guide

This document governs the qualitative checks that resist automation. These checks require human or external reviewer-agent evaluation. 

Checking a box in this document is not proof of compliance. Instead, every node ID must have a filled review form committed to `validation_reports/judgment/<group_dir>/<node_id>.json` (or `.md`) citing specific sample seeds.

---

## Judgment Checklist Items

### 1. Competency Fulfillment
* **Question**: Does at least one generated context variant and formatter directly address the exact wording of the MATATAG learning competency?
* **Reviewer**: External reviewer agent or human developer.
* **Evidence**: Verify that the generated question text covers the explicit verbs and nouns of the competency.

### 2. Comprehensive Coverage
* **Question**: Does the generator address every single aspect and sub-case of the written competency?
* **Reviewer**: Human reviewer or external agent.
* **Evidence**: Audit across multiple seeds to check that all curriculum sub-cases are generated.

### 3. Cognitive Capacity
* **Question**: Is the mathematical complexity and contextual readability level appropriate for the student's grade and quarter? (E.g., no multi-step word problems using advanced vocabulary in Grade 1).
* **Reviewer**: Master educator agent or human reviewer.
* **Evidence**: Review the sentence structure, readability, and required cognitive steps.

### 4. Variant Comprehensiveness
* **Question**: Are all logical contextual variations (word problems, pure math, different question orientations) included to help students master the concept?
* **Reviewer**: Human maintainer or reviewer agent.
* **Evidence**: Confirm that all expected contextual variant options are registered.

### 5. Competency Alignment
* **Question**: Does the difficulty progression directly align with and assist in mastering this specific learning competency?
* **Reviewer**: Educator reviewer.
* **Evidence**: Confirm the continuous and discrete axes correspond to logical pedagogical steps.

### 6. Scale Appropriateness
* **Question**: Is the difficulty scale (linear vs. logarithmic) appropriate for the range of the axis?
* **Reviewer**: Human developer.
* **Evidence**: Check that wide ranges (>= 10x jump, like 10 to 1000) use logarithmic scales, and narrow ranges use linear scales.
