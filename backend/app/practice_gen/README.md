# Practice Generation Pipeline (v2)

This directory contains the core generative engine for creating adaptive, curriculum-aligned K-12 math practice problems.

## The Generation Workflow

Our generation architecture decouples *what* is being tested from *how* it is tested and *how* it is presented. This separation of concerns allows us to generate an infinite variety of problems while maintaining strict pedagogical accuracy. The workflow follows four distinct layers:

### 1. Math DNA (`/dna`)
The foundational layer that defines the rigid mathematical rules for a specific concept (e.g., `addition.py`, `fractions.py`).
* **Parameter Bounds:** Defines the absolute numerical constraints based on grade level (e.g., Grade 1 additions up to 20, Grade 2 up to 1000).
* **Error Patterns:** A deterministic catalog of common student misconceptions. For instance, in addition, a student might subtract the numbers (`a - b`), or fail to regroup (`(a % 10 + b % 10) + (a // 10 + b // 10) * 10`). These exact formulas generate highly realistic distractors for multiple-choice problems.
* **Vocab Gating:** Ensures terminology (like "sum" vs "addend") strictly adheres to the student's current grade and curriculum node.

### 2. Difficulty Dimensions (`/generators/difficulty.py`)
Difficulty in math is multi-dimensional. A problem isn't just "easy" or "hard" — it scales across various independent axes.
* **Discrete & Continuous Scaling:** Dimensions can be discrete choices (e.g., `regrouping: none | ones | tens | double`) or continuous values (e.g., magnitude, target number).
* **Algorithmic Selection:** We use internal algorithms (like `divisibility.py`) to procedurally select numbers that match an exact abstract difficulty scalar from 0.0 (easiest) to 1.0 (mastery).

### 3. Contextual Variants (`/experiences`)
These determine the semantic presentation of the problem without altering the underlying Math DNA.
* **Structures:** Defines if the math is presented as a bare equation (`a + b = ?`), a word problem (`[Name] has [a] apples and buys [b] more...`), or a word problem with extraneous information to test reading comprehension.
* **Personalized Theming:** Injects the student's interests (e.g., Basketball, Minecraft) into the problem's flavor text dynamically.

### 4. Problem Types & Formatters (`/formatters`)
The final presentation layer that transforms the generated mathematical state and context into the final JSON payload for the React frontend.
* **Multiple Choice (MCQ):** Automatically calculates the correct answer and uses the DNA's error patterns to generate 3 highly plausible trap answers.
* **Visual Interactive:** Outputs specific parameters for custom React interactive components (e.g., `SortOrder`, number lines, clocks).
* **Numeric Entry:** Prepares a simple fill-in-the-blank prompt requiring exact typed input.

---

## The "Countless Problems" Multiplier
Because these four layers are completely independent, a single Math DNA module is incredibly powerful. Combining:
* 1 Math DNA logic model
* × 5 variations in difficulty dimensions
* × 10 different contextual structures (bare equation, word problem, table reading, etc.)
* × 3 formatters (MCQ, Visual, Direct Entry)

...results in hundreds of distinct problem archetypes, each of which can accept thousands of different number combinations. This guarantees that a student can practice a single competency indefinitely without ever seeing the exact same problem twice.
