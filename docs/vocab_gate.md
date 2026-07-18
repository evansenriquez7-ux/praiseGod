# Vocabulary and Concept Gating Strategy

> [!NOTE]
> **Reference only.** Binding rules live in [pgen_contract.md](docs/pgen_contract.md).

## 1. Objectives & Context

The Adaptive K-12 Mastery Engine enforces strict grade-and-quarter-level vocabulary constraints dictated by the MATATAG curriculum. Student-facing problems, hints, and distractors prevent the presentation of mathematical terms or concepts that have not yet been introduced. 

This document details the three-tiered strategy used to isolate vocabulary, gate concepts, and prevent false-positive leakage.

---

## 2. Dynamic Phrasing via `VocabGated`

To avoid vocabulary leakage, the system resolves template terminology dynamically at runtime rather than utilizing hardcoded strings.

### 2.1 The `VocabGated` Helper
Every gated vocabulary term is represented by a `VocabGated` instance:
```python
VOCAB_EXPANDED_FORM = VocabGated(
    requires_vocab="expanded form", 
    preferred="expanded form", 
    fallback="broken apart form"
)
```
During generation, the helper resolves the term against the student's `cumulative_vocab` (the set of all introduced words for the active node):
```python
label = VOCAB_EXPANDED_FORM.resolve(cumulative_vocab)
```

### 2.2 Shared and Formatter-Level Gating
* **In question generation:** Stems inside [base_generator.py](backend/app/practice_gen/generators/base_generator.py) use resolved terms dynamically (e.g. resolving `missing number` to `unknown number` for early Grade 1 addition/subtraction nodes).
* **In layout rendering:** Visual formatters (like [fmt_bar_chart.py](backend/app/practice_gen/formatters/visual/fmt_bar_chart.py)) inspect `cumulative_vocab` at render-time to substitute appropriate strings (e.g., swapping `bar graph` for `graph` where the term is unintroduced).

---

## 3. Registry-Level Concept Constraints

When a single DNA module covers multiple sequential concepts (e.g., `symmetry_slides` covers both slides and symmetry; `mass_capacity` covers both mass and capacity), earlier nodes mapping to that DNA restrict generation to only the introduced concept subset.

### 3.1 Competency Parsing
In [registry.py](backend/app/practice_gen/registry.py), `_parse_competency_bounds` inspects the node's learning competency text. If a concept is not mentioned (e.g., symmetry is absent from the slide competency), a discrete constraint is added:
```python
elif dna_name == "symmetry_slides":
    if "symmetry" in text or "symmetric" in text:
        pass
    else:
        bounds["concept"] = "slide_translation"
```

### 3.2 Gated Overrides
The student portal serving path clamps and overrides difficulty profile options using these competency bounds to ensure students receive only curriculum-compliant questions. On non-student paths (such as the verification harness or the Lab preview), the pipeline does not silently clamp requested parameters, ensuring that out-of-bound requests are rejected loudly.

---

## 4. Provenance-Based Concept Gating

Formatters or allowed error patterns can sometimes generate distractors that coincidentally equal the mathematical output of a locked/forbidden error pattern (e.g., generating `11` via an allowed arithmetic offset of `12 - 1` when `pv_zero_exp` is forbidden). 

To prevent false-positive concept leaks without altering production distractors:
1. Every distractor is tagged with its provenance (source name) at generation time (e.g., `distractors_provenance[distractor_value] = error_pattern_label`).
2. The verification harness checks this provenance dictionary instead of looking for value collisions. If a distractor's source label matches a forbidden error pattern, a concept gating violation is raised.
3. Coincidental value collisions from allowed generators or formatting layers are ignored, preserving the original distractor pool.
