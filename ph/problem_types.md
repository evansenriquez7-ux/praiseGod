# Problem Types

AI-generated and AI-gradeable problem types for the ccmed app in addition to the existing multiple choice and writing prompt format. All examples are grounded in real CCSS standards and existing skeleton trap names from `backend/app/sympy_skeletons.py`.

---

## Overview

| # | Type | Best Subjects | Grading Method | New Backend Logic | New Frontend UI |
|---|---|---|---|---|---|
| 1 | Short Numeric / Expression Input | Math | SymPy (exists) | None | Text input field |
| 2 | Fill-in-the-Blank / Cloze | Math, Language | Exact match | None | Inline input(s) |
| 3 | Select All That Apply | Math, Reading | Set comparison | Trivial | Checkbox list |
| 4 | Error Analysis / Spot the Mistake | Math | AI (2-trait rubric) | New grader prompt | Same as writing |
| 5 | Sentence Correction | Language | AI (error-targeted) | New grader prompt | Textarea |
| 6 | Evidence-Based Short Answer | Reading | AI (3-trait rubric) | New grader prompt | Textarea |
| 7 | Ordering / Sequencing | Reading, Math | Exact sequence | None | Drag-and-drop |

---

## 1. Short Numeric / Expression Input

**Standard:** `5.NF.A.1` — Add and subtract fractions with unlike denominators

**Current MCQ:**
> Solve: 1/4 + 2/7 = ?
> - A) 3/11 *(adds numerators and denominators — trap)*
> - B) 2/11
> - **C) 15/28** ✓
> - D) −1/28

**New format:**
> Solve: 1/4 + 2/7 = `________`

Student types `15/28`, `30/56`, or `0.5357` — all accepted as equivalent.

**Why it's better than MCQ:** Forces recall instead of recognition. Eliminates the option to guess by elimination. Natural for high school algebra where answers aren't cleanly enumerable.

**Grading:**
- Function: `sympy_skeletons.validate_answer(math_expr, student_input)` — `backend/app/sympy_skeletons.py`
- Already exists. No new backend code needed.
- SymPy symbolic equivalence handles fractions, decimals, and equivalent expressions.

**Implementation notes:**
- `question_mode`: `"numeric_input"`
- `QuestionResponse.options` → empty list `[]`
- `AnswerSubmitRequest.selected_answer` → student's typed string
- Grading path in `main.py` reuses the existing `validate_answer` branch

---

## 2. Fill-in-the-Blank / Cloze

### Language variant

**Standard:** `L.4.1.g` — Correctly use frequently confused words (there / their / they're)

> The three friends brought `________` own lunches to the picnic.
>
> *(Correct: `their`)*

**Standard:** `L.5.2.a` — Use punctuation to separate items in a series

> We visited Paris`_`, Rome`_`, and Madrid on our trip.
>
> *(Correct: `,` `,`)*

**Standard:** `L.3.2.a` — Capitalize appropriate words

> Every july`_` our town holds a parade on main street`_`
>
> *(Correct: `J`, `.` — capitalize July; capitalize Main Street)*

### Math variant

**Standard:** `5.NF.A.1`

> 1/4 + `________` = 15/28
>
> *(Correct: `2/7` — graded with SymPy)*

**Why it's better than MCQ for Language:** Grammar MCQs can be solved by elimination ("which sentence *sounds* wrong?"). Cloze tests genuine recall of the rule — the student must produce the answer, not recognize it.

**Grading:**
- Language: Exact string match (case-insensitive). Answer is fixed at generation time.
- Math: `validate_answer()` — SymPy equivalence.
- Neither requires AI.

**Implementation notes:**
- `question_mode`: `"cloze"`
- `stem` contains `{{BLANK}}` tokens marking blank positions, e.g. `"We visited Paris{{BLANK}}, Rome{{BLANK}}, and Madrid."`
- `correct_answer`: JSON array of expected fills, e.g. `[",", ","]`
- Frontend renders inline `<input>` fields at each `{{BLANK}}` position

---

## 3. Select All That Apply (Multi-Select)

### Math variant

**Standard:** `8.EE.A.1` — Properties of integer exponents

> Which expressions are equivalent to 2⁶? **Select all that apply.**
>
> - [x] A) 2³ × 2³ ✓
> - [x] B) 2⁸ ÷ 2² ✓
> - [x] C) (2³)² ✓
> - [ ] D) 2² × 2² ✗ *(= 2⁴ = 16, not 64)*
> - [ ] E) 6² ✗ *(= 36)*
>
> **Correct set: {A, B, C}**

### Reading variant

**Standard:** `RL.2.1` — Ask and answer questions about key details *(after a generated passage)*

> Which of the following are mentioned in the passage? **Select all that apply.**
>
> - [x] A) The fox was hungry ✓
> - [ ] B) The grapes were purple ✗ *(not stated)*
> - [x] C) The fox jumped several times ✓
> - [ ] D) Another animal watched the fox ✗
>
> **Correct set: {A, C}**

**Why it's better than MCQ:** Higher cognitive demand — eliminates the "eliminate two, 50/50 guess" strategy. Appropriate for standards that explicitly say "select all" or "which of the following."

**Grading:**
- Exact set comparison: `student_selected == correct_set`
- Optional partial credit: award if all correct keys selected AND no incorrect keys selected
- Fully deterministic — no AI

**Implementation notes:**
- `question_mode`: `"multi_select"`
- `correct_answer`: JSON array of correct keys, e.g. `["A", "B", "C"]`
- `AnswerSubmitRequest.selected_answer`: JSON array of student's selected keys
- Frontend renders checkboxes instead of radio buttons
- Submit button disabled until at least one box is checked

---

## 4. Error Analysis / Spot the Mistake (skip for now because needs an ai grader)

**Standard:** `5.NF.A.1` — Uses existing trap `add_numerators_and_denominators`

> A student solved 1/4 + 2/7 and showed this work:
>
> > 1/4 + 2/7 = **3/11**
>
> The answer is wrong. **What mistake did they make? Explain in your own words.**

**Expected student response:**
> *"They added the top numbers (1 + 2 = 3) and the bottom numbers (4 + 7 = 11) separately, but you can't add fractions that way. You need a common denominator first."*

---

**Standard:** `A-REI.B.3` — Uses existing trap `swapped_x_and_y`

> A student solved the system x + y = 3, x − y = 1 and wrote:
>
> > x = 1, y = 2
>
> The answer is wrong. **Identify the mistake and explain what the correct answer is.**

**Expected student response:**
> *"They found the right numbers (1 and 2) but mixed up which one is x and which is y. The correct answer is x = 2, y = 1."*

**Why it's powerful:** This directly inverts the existing skeleton architecture. Every skeleton already has a `trap_name` on each distractor (e.g. `"add_numerators_and_denominators"`, `"swapped_x_and_y"`, `"sign_error"`). Generation is nearly free — just show the wrong answer and ask the student to diagnose it.

**Grading:** AI (2-trait rubric)
1. **Accuracy** (1–4): Did the student correctly identify the specific error?
2. **Clarity** (1–4): Did they explain it intelligibly?

AI receives: `{trap_name, wrong_answer, correct_answer, student_explanation}` — the `trap_name` tells the grader exactly what error to look for.

**Implementation notes:**
- `question_mode`: `"error_analysis"`
- Generation: extract a distractor with a non-null `trap_name` from the skeleton; present it as "a student's work"
- `correct_answer`: the `trap_name` string (used to anchor AI grading)
- New subagent: `grade_error_analysis_subagent()` in `backend/app/subagents.py`
- Frontend: same textarea UI as writing prompt

---

## 5. Sentence Correction (skip for now because needs an ai grader)

**Standard:** `L.3.2.a` — Capitalize appropriate words in titles

> **Rewrite this sentence correctly:**
>
> *last summer, my family visited yellowstone national park and saw a grizzly bear.*

**Correct rewrite:**
> Last summer, my family visited Yellowstone National Park and saw a grizzly bear.

---

**Standard:** `L.5.1.b` — Form and use the perfect verb tenses

> **Rewrite this sentence correctly:**
>
> *By the time we arrived, she already eat all the pizza.*

**Correct rewrite:**
> By the time we arrived, she had already eaten all the pizza.

---

**Standard:** `L.4.2.b` — Use commas and quotation marks to mark direct speech

> **Rewrite this sentence correctly:**
>
> *The coach shouted run faster and don't give up!*

**Correct rewrite:**
> The coach shouted, "Run faster and don't give up!"

**Grading:** AI (error-targeted)

AI receives: `{standard_description, target_errors: [...], original_sentence, student_rewrite}` and checks:
1. Was each target error corrected?
2. Did the student introduce any new errors?

Verdict is per-error (fixed / not fixed / new error introduced), not a holistic score.

**Implementation notes:**
- `question_mode`: `"sentence_correction"`
- `stem`: the flawed sentence
- `correct_answer`: the fully corrected sentence (stored server-side, never sent to client)
- `metadata.target_errors`: array of error descriptors used to anchor AI grading, e.g. `["capitalize_first_word", "capitalize_proper_noun:Yellowstone National Park"]`
- New subagent: `grade_sentence_correction_subagent()` in `backend/app/subagents.py`

---

## 6. Evidence-Based Short Answer (skip for now because needs an ai grader)

**Standard:** `RI.5.1` — Quote accurately from a text when explaining what it says explicitly

**AI-generated passage (~100 words):**
> *Honeybees are essential to agriculture. According to the USDA, bees pollinate more than 90 commercial crops in the United States. Without bees, one-third of our food supply would disappear. Farmers in California alone rely on rented beehives to pollinate almond trees each spring, a process worth over $1 billion annually. Colony collapse disorder — a phenomenon where worker bees abandon their hives — has threatened bee populations since 2006, alarming scientists and farmers alike.*

**Question:**
> The author claims that bees are economically important to farmers. Find **one sentence from the passage** that best supports this claim and explain in 1–2 sentences how it supports it.

**Strong student response:**
> *"Farmers in California alone rely on rented beehives to pollinate almond trees each spring, a process worth over $1 billion annually." This supports the claim because it shows that farmers depend on bees financially — without them, a billion-dollar industry would fail.*

**Why it matters:** Standards like `RI.5.1`, `RI.6.1`, `RL.7.1` explicitly require students to *cite textual evidence*. MCQ cannot assess this — a student can pick the right answer without ever locating or reading the relevant passage sentence. Evidence-based short answer is the only format that actually tests the standard.

**Grading:** AI (3-trait rubric)
1. **Quote validity** (pass/fail): Is the quoted sentence actually present in the passage? *(prevents hallucination; checked with string search before AI)*
2. **Relevance** (1–4): Does the quote relate to the claim in the question?
3. **Explanation quality** (1–4): Does the student's explanation connect the quote to the claim?

**Implementation notes:**
- `question_mode`: `"evidence_based"`
- `stem` includes the full generated passage + the question
- `correct_answer`: stores the passage text server-side for quote validation
- Quote validation is a deterministic string search before AI grading is invoked
- New subagent: `grade_evidence_based_subagent()` in `backend/app/subagents.py`
- Frontend: textarea below the passage

---

## 7. Ordering / Sequencing

### Reading variant

**Standard:** `RL.3.3` — Describe how characters respond to major events and challenges

> **Drag the events into the correct order.**
>
> | | Card |
> |---|---|
> | `[ ]` | Goldilocks ran out of the house and never returned. |
> | `[ ]` | She tasted the porridge and sat in the chairs. |
> | `[ ]` | Goldilocks entered the empty cottage. |
> | `[ ]` | The three bears came home and found her asleep. |
>
> **Correct order:** Entered cottage → Tasted/sat → Bears returned → Goldilocks fled

### Math variant (procedure steps)

**Standard:** `A-REI.B.3` — Solve linear equations in one variable

> **Drag these steps into the correct order to solve 2x + 4 = 10.**
>
> | | Step |
> |---|---|
> | `[ ]` | x = 3 |
> | `[ ]` | 2x + 4 = 10 |
> | `[ ]` | Divide both sides by 2 |
> | `[ ]` | Subtract 4 from both sides: 2x = 6 |
>
> **Correct order:** Original equation → Subtract 4 → Divide by 2 → Solution

**Grading:** Exact sequence comparison — fully deterministic, no AI.

Optional partial credit: Kendall tau distance (number of inversions from correct order) for scoring intermediate understanding.

**Implementation notes:**
- `question_mode`: `"ordering"`
- `options`: array of card objects `[{key: "A", text: "..."}, ...]` — served in shuffled order
- `correct_answer`: JSON array of keys in correct order, e.g. `["B", "D", "C", "A"]`
- `AnswerSubmitRequest.selected_answer`: JSON array of keys in student's submitted order
- Frontend: drag-and-drop card list; submit button activates after all cards are placed
- ReactFlow drag primitives already present in the app

---

## Implementation Priority

| Priority | Type | Effort | Reason |
|---|---|---|---|
| 1 | Short numeric input | Low | `validate_answer()` already exists — frontend change only |
| 2 | Multi-select | Low | Set comparison is trivial; immediate MCQ quality upgrade |
| 3 | Sentence correction | Medium | Closes the gap for Language standards currently forced into MCQ |
| 4 | Error analysis | Medium | `trap_name` architecture makes generation nearly free |
| 5 | Evidence-based short answer | Medium | Required to actually assess "cite evidence" reading standards |
| 6 | Fill-in-the-blank | Low-Medium | Good for Language vocabulary; needs inline input UI |
| 7 | Ordering / sequencing | Medium | Needs drag-and-drop UI; high value for story sequence + procedure standards |
