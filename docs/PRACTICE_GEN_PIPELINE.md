# Practice Generation Engines (v2)
## CCMed — Adaptive K-12 Mastery Engine

This document outlines the core problem-generation infrastructure for creating adaptive, curriculum-aligned K-12 math problems. The platform utilizes two distinct, powerful generation engines: **The Generative Textual Pipeline (Math DNA)** and **The Stateless Visual Skeletons Engine**.

---

## Part 1: The Textual Pipeline (Math DNA)

The textual/algorithmic pipeline decouples *what* is being tested from *how* it is tested and *how* it is presented across four independent layers.

### 1. Core Architecture Layers

#### Layer 1: Math DNA (`/dna`)
The foundational layer defining rigid mathematical rules for a specific concept (e.g., `addition.py`, `fractions.py`).
*   **Parameter Bounds:** Defines numerical constraints based on grade level (e.g., Grade 1 sums $\le 20$, Grade 2 $\le 1000$).
*   **Error Patterns:** A deterministic catalog of student misconceptions. Uses SymPy expressions to generate highly realistic distractors (e.g., `a - b` for addition).
*   **Vocab Gating:** Enforces terminology (e.g., "sum" vs "addend") strictly adhering to the student's current grade.

#### Layer 2: Difficulty Dimensions (`/generators/difficulty.py`)
Difficulty scales across multiple independent axes, not just a binary "easy/hard".
*   **Discrete Scaling:** Ordered concepts (e.g., `regrouping: ["none", "ones", "tens", "double"]`).
*   **Continuous Scaling:** Uses internal algorithms (like `divisibility.py`) to map a difficulty scalar ($0.0$ to $1.0$) to numerical ranges using **Windowed Sampling**.

#### Layer 3: Contextual Variants (`/experiences`)
Determines the semantic presentation without altering the Math DNA.
*   **Structures:** Bare equations, word problems, or table-reading tasks.
*   **Personalized Theming:** Injects student interests (e.g., Basketball, Creative Sandbox) from the 25-interest bank dynamically.

#### Layer 4: Problem Types & Formatters (`/formatters`)
The final transformation into the JSON payload for the React frontend.
*   **MCQ:** Uses DNA error patterns to generate 3 trap answers.
*   **Numeric Entry:** Fill-in-the-blank prompt requiring exact typed input.

### 2. DNA API & Generation Flow

#### `generate_params(grade: int, difficulty_profile: dict, seed: int) -> dict`
The primary entry point for each DNA module.
*   The `difficulty_profile` contains **BOTH** difficulty scalars (e.g., `"range": 0.5`) **AND** contextual variant keys (e.g., `"task_type": "numeral_to_word"`). 
*   **Registry Enforcements:** `registry.py` defines global mathematical bounds, but individual DNAs must explicitly enforce `max(registry_min, lo)` to ensure $d=0$ doesn't violate curriculum minimums.

---

## Part 2: The Visual Skeletons Engine

Visual skeletons are deterministic, auto-validatable interactive problem generators for the MATATAG Math curriculum. Unlike traditional text multiple-choice questions, visual problems require students to manipulate visual interfaces directly (number lines, clocks, grid systems).

### 1. Architecture Decisions

#### A. Stateless IDs (`skeleton_id`)
To completely eliminate database reads/writes during assignment generation or grading, the visual engine encodes all variables directly within a unique, reproducible string:
```
nl_4_12345_m
│  │   │   │
│  │   │   └─ difficulty (e.g., m = medium, e = easy, h = hard)
│  │   └───── seed
│  └───────── grade
└──────────── type code (e.g., nl = NumberLine, clk = ClockSet)
```
*   **Instant Grading:** Grading operates statelessly by decomposing the ID, regenerating the exact parameters, and verifying the student's interaction directly against the computed truth.

#### B. Snap-to-Grid Validation
Continuous coordinate evaluations introduce floating-point tolerance challenges. The visual engine uses discrete grid alignments (e.g., exactly 12 intervals for clocks, fixed division ticks on number lines) ensuring clear targets for mobile touch states and simple binary `True/False` evaluations.

#### C. Comprehensive Trap Production
Skeletons compute and expose ALL pedagogical traps during the initialization call. This decouples visual math from the persistence layer, allowing the frontend presentation layer to filter or select sub-traps based on real-time student profiling history.

### 2. Supported Visual Types (The 12 Core Archetypes)

| Type | Code | Core Implementation Targets |
|------|------|-----------------------------|
| **FillInTable** | `fit` | Completing step patterns or multiplication matrices. |
| **RuleDiscovery** | `rd` | Discovering abstract algebraic rules from inputs and outputs. |
| **NumberLine** | `nl` | Placing fractional boundaries, decimals, or negative integers. |
| **ConstraintSatisfaction**| `cs` | Finding numeric outputs satisfying complex overlapping rules. |
| **PesoMoney** | `pm` | Accumulating target values using coins and bills combinations. |
| **BarChart** | `bc` | Formulating graphs and charts directly from table data arrays. |
| **ClockSet** | `clk` | Moving hands on an analog face to show target elapsed times. |
| **EstimationGate** | `eg` | Approximating calculation sums before reaching checkpoints. |
| **SortOrder** | `so` | Dragging elements into true sequential order (ascending/descending). |
| **GridArea** | `ga` | Counting boxes or building regions to fulfill area units. |
| **Categorize** | `cat` | Sorting objects into logical property bins. |
| **Calendar** | `cal` | Navigating date scopes or measuring specific day durations. |

### 3. Engine API Interface

```python
# 1. Generate New Visual Problem
skeleton = get_visual_skeleton(visual_type="NumberLine", grade=4, seed=12345, difficulty="medium")

# 2. Stateless Verification
result = validate_student_answer(skeleton_id="nl_4_12345_m", student_answer=3)
# Returns: {"is_correct": True, "trap_triggered": None, "correct_answer": 3}
```

---

## Part 3: Shared Integration Constraints & Pitfalls

When fixing or creating generators (textual or visual) for the MATATAG Math curriculum, implementations must coordinate perfectly with the core student dashboard requirements.

### 1. Critical Pitfalls (AVOID THESE)

#### A. The "Leaky Window" Problem (Continuous Scaling)
Do NOT apply a continuous scalar ($0.0$ to $1.0$) by simply multiplying against a maximum limit and randomizing from $0$. A maximum scalar slice should never drop a mastery level back to a beginner value.
**Fix:** Apply strict **Windowed Sampling**. Dynamically compute distinct segment floors and ceilings (e.g., `prev_target + 1` to `current_target`) and constrain parameters within that isolated window.

#### B. Invisible String Formatting (`adapter.py`)
While `base_generator` outputs mathematical equations well, custom non-arithmetic textual variants or specific descriptions require intercepting.
**Fix:** Always implement custom string construction overrides within `adapter.py` via `_fix_question_text` to handle complex conversions gracefully (e.g., "Write 82 in words.").

#### C. Cognitive Variant Fallbacks
If a single module serves multiple grade bands, check for local constraints. A variant that requires expanded place notation should not break Grade 1 rules.
**Fix:** Use explicit fallbacks:
```python
if grade == 1 and task_type == "numeral_to_expanded":
    task_type = "numeral_to_word"
```

### 2. Gating and Routing Architecture
*   **DB Gating Rules:** Settings are dynamically fetched from the `competency_configurations` database table at runtime before a batch execution starts. Hardcoded parameters bypassing user selections are prohibited.
*   **Routing Signals:** The horizontal curriculum lanes (Number & Algebra `NA`, Measurement & Geometry `MG`, Data & Probability `DP`) request questions by dispatching specific `node_id` configurations to `/api/practice/{student_id}/batch`.
*   **Vocabulary Integrity:** Text components must draw exclusively from `node.cumulative_vocab` (the Incorporate Rule) and strictly ban future terms or advanced descriptions (the Exclude Rule).
