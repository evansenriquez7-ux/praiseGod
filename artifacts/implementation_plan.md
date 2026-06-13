# Grade-Appropriate Vocabulary Audit & Cleanup Plan

Systematic audit and refinement of student-facing prompt strings, hint texts, and visual labels across all 15 Math DNA modules, 23 visual/textual formatters, and 30+ MATATAG nodes for Grades 1–3.

## User Review Required

> [!IMPORTANT]
> To ensure absolute coverage across all potential outputs (including different seeds, interest profiles, and formatters), we will create a dedicated audit script in the scratch directory. This script will generate actual student-facing text for all competencies under both `pure` and `word_problem` contexts.
**We are targeting all student facing language: This applies to all contexual variants and all formatters. All vocabulary that will be presented to the students

## Open Questions
* **Grade-Appropriate Synonyms**: Are there specific preferred terms we should enforce? We propose the following translation guidelines for Grades 1-3:
  - *Sequence / repeating components* → **Pattern** / **Number pattern**
  - *Minuend / Subtrahend / Addend* → **First number** / **Second number** (or embed in narrative context)
  - *Expression* → **Number sentence** (already fallback in some places)
  - *Determine / Identify* → **Find** / **Choose** / **What is**
  - *Evaluate / Calculate* → **Solve** / **Work out** / **Find the answer to**
  - *Term* (in patterns) → **Number** / **Shape** / **Item**

--- 
**Yes these are appropriate terminologies

## Proposed Changes

We will shift to a scalable, grade-aware architecture rather than relying on a flat "forbidden list."

### Phase 1: Automated Language Audit (Updated)
Update [audit_vocabulary.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/scratch/audit_vocabulary.py) to be **Grade-Aware**. 
Instead of a flat `FORBIDDEN_WORDS` list, the script will import a structured `ACADEMIC_VOCAB` dictionary where each complex word has a defined `min_grade`. The script will now scale to Grade 4+ by only flagging words that appear in problems generated for a grade *lower* than their `min_grade`.

### Phase 2: Centralized Academic Vocabulary Registry
Create `backend/app/practice_gen/vocab_matrix.py` to hold the global `ACADEMIC_VOCAB` dictionary mapping complex academic terms to their `min_grade` and `fallback_string`.
* Example: `"identify": {"min_grade": 4, "fallback": "find"}`
* Define a resolver function `resolve_academic_text(text: str, grade: int) -> str` that automatically replaces complex terms with fallbacks when the target grade is below the threshold.

### Phase 3: Pipeline Integration
Hook the `resolve_academic_text` function into the end of `generate_problem` in `backend/app/practice_gen/adapter.py`. 
By passing the final `FormattedProblem.question_text` and `hints` through this resolver, we completely eliminate the need to hunt down and manually update hardcoded strings across all formatters, adapter, and spines. This ensures that any future generator or formatter will automatically be grade-appropriate!

### Phase 4: Competency Bounds Injection
Update `generate_context` in `backend/app/practice_gen/generators/base_generator.py` to call `get_node_competency_bounds(node_id)` (from `registry.py`) and merge the returned bounds into the `difficulty_profile` before passing it to `dna_module.generate_params`. This guarantees that difficulty dimensions strictly adhere to the MATATAG limits (e.g. bounding `number_reading.py` ranges correctly for Grade 1), physically preventing out-of-bounds generation!

---

## Verification Plan

### Automated Verification
* Re-run [audit_vocabulary.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/scratch/audit_vocabulary.py) to confirm zero problematic words exist in the final output texts.
* Run the test suite:
  ```bash
  PYTHONPATH=. ./venv/bin/pytest backend/app/practice_gen/
  ```
