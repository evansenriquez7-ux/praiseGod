# Learning Competency Practice Problem Generator Checklist

**MANDATORY**: Before a generator is considered complete, an agent must verify every item on this checklist. All pg pipeline bug fixes must be done according to the following:

**Matatag Lab as Single Source of Truth**

The Matatag Lab displays all learning competencies. Each learning competency displays all the available difficulty dimensions, contextual variants, and formatters specific to that learning competency. Each of these options can be enabled/disabled from the checkbox options. The Generate Preview randomly chooses from the enabled difficulty dimension options, contextual variants, and formatters, then generates a practice problem. The student portal should only display learning competency practice problems according to the enabled options in the Matatag Lab. From this single source of truth, agents can accurately test the UI outputs.

**Avoid Graceful Fallbacks and Silent Defaulting Behavior**

The pg pipeline must avoid graceful fallbacks and silent defaulting behavior. When the auditor script tests the pg's to check for compliance with this checklist, these behaviors hide bugs. The pg pipeline is meant for failing fast and loud, this way the auditor script can recognize the issue so it can be fixed.


## 1. Difficulty Dimensions

Difficulty dimensions control the core progression of a problem's complexity. They represent an ordered path from easiest to hardest (e.g., numerical ranges, regrouping levels, spatial orientation, or analytical depth). Dimensions must represent an ordered progression of difficulty. Do NOT use difficulty dimensions for unordered categorical variations.

* [ ] **Strict Scalar Mapping**: A scalar of `0.0` MUST map to the exact minimum bound prescribed by the competency. A scalar of `1.0` MUST map to the exact maximum bound.
* [ ] **Numerical Nature**: Dimensions must be mathematical/numerical. Do NOT use difficulty dimensions for language variations or problem presentation (use Contextual Variants for that).
* [ ] **Scale Appropriateness**: For continuous ranges (`d=5`), use a **logarithmic scale** for wide ranges (e.g., >= 10x jump, like 10 to 1000) and a **linear scale** for narrow ranges.
* [ ] **Functional Integrity**: Every dimension scalar must execute without errors and provably restrict the generated parameters to the correct difficulty window (e.g. no "leaky windows").
* [ ] **Competency Alignment**: The difficulty progression must directly assist a student in mastering the specific learning competency. (Note: continuous `number\_difficulty` is generally NOT appropriate for pure counting-based competencies).

## 2. Contextual Variants

Contextual variants represent different ways to present or interact with the core concept (e.g., purely numerical vs. word problem, forward vs backward). Variants are randomly selected to test different manifestations of a concept. While some variants (like word problems) may naturally carry higher cognitive loads than others, they must represent valid, alternative presentations of the core concept.

* [ ] **Competency Fulfillment**: At least ONE contextual variant must directly and explicitly address the exact wording of the learning competency.
* [ ] **Functional Integrity**: Every variant option must execute without errors and successfully generate the expected problem context.
* [ ] **Separation of Concerns**: Variants must NOT alter the core mathematical difficulty.
* [ ] **Variant Comprehensiveness**: Ensure all logical variants for the underlying math concept of the learning competency are included. Variants must assist the student/user in mastering the learning competency. Include missing variants in compatibility.py if not already included.

## 3. Formatters (Problem Types)

Formatters determine how the problem is visually and interactively presented (e.g., MCQ, cloze, number line).

* [ ] **Formatter Comprehensiveness**: Ensure all listed formatters in compatibility.py have been evaluated for usage and applicability towards the learning competency.
* [ ] **Competency Fulfillment**: At least ONE formatter must directly match the specific interaction required by the learning competency.
* [ ] **Functional Integrity**: The DNA must execute without errors for every formatter it claims compatibility with. Must also adhere to difficulty dimensions and variants. Must display visuals cleanly and have answer fields.
* [ ] **Visual Compatibility**: Ensure purely visual formatters correctly bypass or gracefully handle contextual variants (like word problems) that they are incompatible with.
* [ ] **Formatter Comprehensiveness**: Ensure all listed formatters in compatibility.py have been evaluated for usage and applicability in the learning competency.

## 4. Final Review

* [ ] **Comprehensive Coverage**: The generator directly addresses EVERY aspect of the written MATATAG learning competency.
* [ ] **Cognitive Capacity**: The math logic does not exceed the mental capacity expected for the specific grade and quarter.
* [ ] **Vocabulary Gating**: All text, instructions, and concepts used are strictly grade- and quarter-appropriate. No vocabulary or mathematical concepts from future curriculum nodes are used or implied.
* [ ] **Mandatory Testing:** This checklist is only complete when you inspected the output, and proven that the generation pipeline produces the correct, final results that the UI expects.


