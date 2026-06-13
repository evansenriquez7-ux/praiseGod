# MATATAG Lab Architecture Summary

The MATATAG Lab is an interactive environment designed to test and configure perfect, curriculum-aligned practice problems. It integrates the MATATAG K-12 learning competencies with dynamic problem generators.

Here is a comprehensive breakdown of the pipeline and the critical files that generate the final practice problems:

## 1. The Entry Point: API & Pipeline
When a user requests a problem (via the Lab UI), the request hits the API endpoint in **`main.py`** (specifically `/api/matatag/lab`). The request includes the chosen competency (`node_id`) and any tweaked difficulty dimensions or contextual variants (`difficulty_profile`).

**`backend/app/practice_gen/pipeline.py`**
This file acts as the orchestrator. The `PracticePipeline` class receives the request, delegates the node lookup to the registry, fetches the correct generator, and builds the final JSON problem representation containing the question, answer, and error distractors.

## 2. Curriculum Mapping & Constraints
Before generating the problem, the engine needs to know *what* to generate and *how hard* it can be.

**`backend/app/practice_gen/registry.py`**
- Maps the 151 MATATAG Knowledge Graph nodes (like `mat_g1_na_q1_8`) directly to their mathematical "DNA" (e.g., `addition`, `subtraction`).
- Parses the raw curriculum text from `matatagmath.json` to extract hard mathematical limits (e.g., extracting "sums up to 100" to set `max_sum=100`, or extracting "without regrouping").

**`backend/app/practice_gen/axes_catalog.py`**
- Defines the catalog of UI levers (sliders and dropdowns) available in the Lab for each concept.
- Configures things like `number_difficulty` (continuous from 0.0 to 1.0) or `regrouping` options.

## 3. The Core Engines: DNA Files
The actual mathematical generation happens inside the DNA files. There are currently 15 specific DNA modules (such as `addition.py`, `multiplication.py`, `fractions.py`, etc.) stored in:
**`backend/app/practice_gen/dna/na/`**

Each DNA file exports two critical things:
1. **`generate_params(grade, difficulty_profile, seed)`**: A function that generates the actual numbers for the problem. It enforces the curriculum bounds (e.g., `max_product`) and applies the `number_difficulty` scalar using `generate_pair_by_window` to ensure the numbers scale appropriately to the student's mastery.
2. **`DNA` class**: An object that declares the core formula (`a * b = result`), compatible UI formats (`mcq`, `numeric_input`), and specific error tracking patterns (e.g., identifying if a student added instead of multiplied).

## 4. Contextual Narratives: Spines & Interests
If the practice problem requires a "word problem" context, the DNA generator requests a story wrapper.

**`backend/app/practice_gen/spines.py`**
- Holds a centralized registry of narrative logic `Spine` objects (e.g., `mult_equal_groups`, `div_sharing`, `frac_pizza`).
- Selects an age-appropriate narrative logic that matches the underlying math operation.

**`data/skeletons/interest_bank.json`**
- This file is the dynamic source of truth for the student's personal interests.
- When `spines.py` formats the story template, it dynamically injects items, character names, and containers from the `interest_bank.json` corresponding to the student's chosen `interest_id` (e.g., `anime_rpg`, `kpop`, `basketball`).

---

### Step-by-Step Generation Flow
1. **UI Request**: User selects Grade 2 Multiplication competency and sets `interest_id` to "kpop".
2. **Registry Lookup**: `pipeline.py` asks `registry.py` what DNA to use. `registry.py` returns `multiplication.py` and curriculum bounds (`max_product=100`).
3. **Number Generation**: `multiplication.py`'s `generate_params()` creates the numbers (`a=2, b=4`) using continuous difficulty algorithms.
4. **Story Formatting**: `multiplication.py` detects a word problem context and calls `spines.py`. `spines.py` selects an "equal groups" spine and injects "lightsticks" and "concert venues" from the `interest_bank.json` kpop category.
5. **Final Output**: `pipeline.py` packages the `question` text, the `result`, and the applicable `error_patterns` and returns it to the UI.
