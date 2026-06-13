# Practice Generation Strategy
## CCMed — Adaptive K-12 Mastery Engine

## 1. Core Architecture
The pipeline has 4 independent layers:
1. **DNA (`dna/`)**: Specifies the math logic, param bounds, error patterns, and variants.
2. **Context Generator (`generators/`)**: Instantiates DNA with seeded random values, applies interest wrapping, and produces `QuestionContext`.
3. **Formatter (`formatters/`)**: Transforms `QuestionContext` into a specific format (e.g., MCQ, cloze, NumberLine).
4. **Experience Wrapper (`experiences/`)**: Wraps formatted problems (e.g., timed, scaffolded).

## 2. DNA Constraints & Difficulty
- **Continuous Dimensions (Windowed Sampling, d=5)**: Value ranges (e.g., `operand_max`). Log scale for ranges >=10x.
- **Discrete Dimensions (Windowed Sampling, d=len(levels))**: Ordered concepts (e.g., `regrouping: ["none", "ones", "tens", "double"]`).
- **Contextual Variants**: Randomly selected non-difficulty variations (e.g., `structure: "change_unknown"`).
- **Error Patterns**: SymPy expressions that model specific student mistakes (e.g., `a - b` for addition). Must be mutually distinct.

## 3. DNA API & Generation
- `generate_params(grade: int, difficulty_profile: dict, seed: int) -> dict`: The entry point for each DNA.
- **IMPORTANT:** The `difficulty_profile` dictionary contains **BOTH** difficulty scalars (e.g., `range`: `0.0`-`1.2`) **AND** contextual variant keys (e.g., `task_type`: `"numeral_to_word"`). You must extract both from this dictionary.

## 4. Vocabulary & Concept Gating
- Nodes enforce vocabulary and cognitive limits. Problems cannot use words or concepts introduced in later nodes.
- Story spines (narratives) and error patterns are automatically filtered by required concepts.
- **Variant Fallbacks:** If a DNA serves multiple grades and a variant exceeds a lower grade's cognitive capacity, you MUST explicitly override or strip it in `generate_params` (e.g., `if grade == 1 and task_type == "numeral_to_expanded": task_type = "numeral_to_word"`).

## 5. Adding New Problem Types
1. Write the new DNA, Formatter, or Wrapper.
2. Update `COMPATIBILITY` mapping in `compatibility.py`.
3. Update `FORMATTER_VARIANT_SUPPORT` in `compatibility.py` if adding specific variants.

## 6. Critical Pitfalls (AVOID THESE)

### A. The "Leaky Window" Problem
When applying a continuous scalar (0.0 to 1.0) to a range, do NOT just scale the `max_target` and pick a random number between `0` and `max_target`. This destroys the progression because a difficulty of `1.0` can still randomly generate `0`.
**Fix:** You MUST dynamically calculate both the lower and upper bounds for the specific scalar slice (e.g., `prev_target + 1` to `current_target`) and constrain the random choice strictly within that segment.

### B. Registry Bounds Overrides
`registry.py` enforces mathematical bounds (e.g., `10` to `100`). However, if `difficulty_profile` contains the `"range"` key (e.g., `"range": 0.0`), `base_generator` will NOT inject the `10` minimum.
**Fix:** Explicitly enforce `max(registry_min, lo)` inside your DNA logic so `d=0` doesn't drop below the learning competency bounds.

### C. Invisible String Formatting (`adapter.py`)
`base_generator` only handles arithmetic `question_text` generation well. For specialized non-arithmetic DNAs (like `number_reading`), it will generate `"None"` or a generic string.
**Fix:** The translation of your generated `values` dict into a clean `question_text` happens in `adapter.py` via `_fix_question_text`. You MUST intercept your concept there to build custom English strings (e.g., `"Write 82 in words."`).

### D. Misinterpreting Constraints
If using the old constraint model (`a <= 55 and b <= 55`), the lower bound is completely ignored during rejection sampling.
**Fix:** Ensure your constraints enforce the lower bound (`max(a,b) >= 38`) or directly sample within the slice as described in Pitfall A.

## 7. MATATAG Curriculum Architecture & Student UI Integration
When fixing or creating generators for the MATATAG Math curriculum, LLM agents must adhere to the end-to-end integration flow built for the Student Portal:
1. **PostgreSQL Configuration Gating:** The MATATAG Lab UI allows admins to define multi-selectable difficulty windows, variants, and formatters. These are persisted per `node_id` in the `competency_configurations` DB table. The `pipeline.run()` engine queries this table and dynamically filters the pool of allowed settings before generating a SymPy problem.
2. **Direct Node Routing:** The Student Portal renders a Curriculum Dashboard consisting of three horizontal swimlanes (Number & Algebra `NA`, Measurement & Geometry `MG`, Data & Probability `DP`). When a student launches a practice session from this roadmap, the frontend passes the explicit `node_id` (e.g., `mat_g2_na_q1_1`) as the `subdomain` parameter to `/api/practice/{student_id}/batch`. 
3. **Dual-Option Views:** Each roadmap node contains a "Read Intro" modal (which summons dynamic slides mapped to the `node_id` directly in the `intro_viewer` workspace) and a "Start Practice" mode. Both modes natively run the Socratic Tutor in the right-hand panel.
4. **Generator Compliance:** When writing or fixing a DNA generator, your code MUST cleanly handle the variants and parameters provided by the DB-enforced `difficulty_profile`. Do not hardcode parameters that bypass the Lab UI's selected checkboxes. If the lab disables a formatter, your generator should gracefully adapt to the ones that remain allowed via the `adapter.py` filtering.
