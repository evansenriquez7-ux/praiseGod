# Introductory Content Strategy
## CCMed — Adaptive K-12 Mastery Engine

---

## 1. Philosophy

Introductory content is built on one principle: **Perseus templates are the
ground truth for teaching structure; we parameterize them for dynamism and
augment them where insufficient.**

The system is designed so that:

- Worked examples shown in intros preview the exact problem formats students
  will encounter in practice — reducing cognitive load at first attempt
- Numbers and actors in worked examples are dynamic — different seed produces
  different values — so content stays fresh across sessions
- Vocabulary and cognitive complexity are enforced automatically by the same
  constraint system used for practice generation
- Interest wrapping enriches worked examples without affecting mathematical
  correctness
- Definitions and introductions are added where Perseus provides insufficient
  context for first-time learners
- All content is provably correct by construction — no LLM at runtime

---

## 2. Core Architecture

The pipeline has four stages:

```
┌─────────────────────────────────────────────────────────────┐
│  Perseus Template (source of truth)                         │
│  Real hint sequences from Khan Academy exercises covering   │
│  early math. Contains visual strategies, step-by-step       │
│  scaffolding, and proven pedagogical patterns.              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│  Parameterization Layer                                     │
│  Transforms fixed Perseus hint sequences into templates     │
│  with variable slots, param_bounds, and interest slots.     │
│  One parameterized template → infinite correct instances.   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│  Augmentation Layer                                         │
│  Adds what Perseus lacks: concept definitions, connecting   │
│  introductions, vocabulary introductions. Constrained by     │
│  the knowledge graph's cumulative_vocab and grade ceiling.  │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│  Runtime Generator                                          │
│  Fills variable slots with seeded random values, applies    │
│  interest wrapping, assembles mini-lessons into ordered     │
│  slide sequences. Serves via API.                           │
└─────────────────────────────────────────────────────────────┘
```

Each stage is independent. New competencies require only new Perseus mappings
and (where needed) new augmentation content. Existing templates remain
untouched.

---

## 3. Content Types

### Type A: Perseus-Derived (Dynamic, Automatable)

Worked examples extracted from Perseus hint sequences. These are the
core teaching content — they show concepts in action step-by-step.

**Properties:**
- Structurally identical to what students encounter in practice
- Multiple visual strategies per concept (number line, ten frame, place
  value blocks, groups of objects — following Perseus)
- Variable slots for numbers (different seed = different values)
- Interest-wrappable (actors and objects from the 25-interest bank)
- 100% correct by construction (answer_formula + param_bounds)
- Rendered using existing visual components + ASCII/text fallbacks

**Source:** `scripts/perseus_extractor/output/perseus_templates/` (9,072 files)
**Mapping:** `ph/matatag_matched_problems.json` (competency → Perseus templates)

### Type B: Authored Augmentations (Static, Validated)

Content that Perseus does not provide — needed for students encountering
a concept for the first time.

**Includes:**
- Concept definitions (what IS addition? what does "sum" mean?)
- Introduction text (motivate the concept, connect to what student already knows)
- Vocabulary introductions (new terms with grade-appropriate definitions)
- Contextual framing (WHY do we need this concept?)

**Properties:**
- Authored once (by specialized subagent), validated, stored permanently
- Constrained by `cumulative_vocab` (never uses future terms)
- Constrained by `sentence_max_words` (grade-appropriate sentence length)
- Constrained by `NOT_YET_KNOWN` (explicit exclusion of advanced concepts)
- NOT interest-wrapped (definitions are universal, not themed)

**Source:** Knowledge graph + definition bank (authored offline)

---

## 4. Perseus Template → Parameterized Template

### The Transformation Process

A Perseus template contains fixed assessment items with hint sequences.
The parameterization process converts these into dynamic intro templates.

#### Original Perseus (fixed):

```json
{
    "question_content": "**Add.**\n\n${}\\Large\\blueE{9} + \\maroonD6 ={}$ [[☃ numeric-input 3]]",
    "hints": [
        "Let's use a number line to help us solve.\n\n![](web+graphie:.../images/...)",
        "First, let's jump $\\blueE{9}$ on the number line.\n\n![](web+graphie:.../images/...)",
        "Next, let's jump $\\maroonD6$ on the number line.\n\n![](web+graphie:.../images/...)",
        "The jumps end at the number $\\goldE{15}$.\n\n![](web+graphie:.../images/...)",
        "${}\\Large\\blueE{9} + \\maroonD6 = \\goldE{15}$"
    ]
}
```

#### Parameterized Version (dynamic):

```python
{
    "source_template_id": "a277c638c65a55f3b098b471a10b48bb",
    "strategy": "number_line",
    "param_bounds": {"a": (1, 9), "b": (1, 9)},
    "answer_formula": "a + b",
    "interest_wrappable": False,

    "steps": [
        {
            "text": "Let's use a number line to add.",
            "visual": {
                "type": "NumberLine",
                "params": {"start": 0, "end": 20, "markers": []}
            }
        },
        {
            "text": "First, let's jump $\\blueE{{{a}}}$ on the number line.",
            "visual": {
                "type": "NumberLine",
                "params": {"start": 0, "end": 20, "hop_to": "{a}"}
            }
        },
        {
            "text": "Next, let's jump $\\maroonD{{{b}}}$ more.",
            "visual": {
                "type": "NumberLine",
                "params": {"start": 0, "end": 20, "hop_from": "{a}", "hop_by": "{b}"}
            }
        },
        {
            "text": "The jumps end at $\\goldE{{{result}}}$.",
            "visual": {
                "type": "NumberLine",
                "params": {"start": 0, "end": 20, "highlight": "{result}"}
            }
        },
        {
            "text": "$\\blueE{{{a}}} + \\maroonD{{{b}}} = \\goldE{{{result}}}$",
            "visual": None
        }
    ]
}
```

### Variable Slot Types

| Slot Type | Description | Example |
|-----------|-------------|---------|
| `{a}`, `{b}` | Numeric parameters drawn from `param_bounds` | `a=5, b=3` |
| `{result}` | Computed from `answer_formula` | `result = a + b = 8` |
| `{actor}` | Character name from interest bank | `"Kuya Franz"` |
| `{objects}` | Countable noun from interest bank | `"headsets"` |
| `{place}` | Location from interest bank | `"internet cafe"` |

### Parameterization Rules

1. **Numbers become variables** — any numeric value in a hint step that could
   reasonably change becomes a slot with `param_bounds`
2. **Object nouns become interest slots** — "sharks", "cookies", "flowers" become
   `{objects}` when `interest_wrappable = True`
3. **Actor names become interest slots** — character names become `{actor}`
4. **Structure stays fixed** — the pedagogical step sequence (introduce tool →
   show first value → perform operation → state result) never changes
5. **Visual params reference variables** — `"hop_to": "{a}"` means the visual
   component renders dynamically based on the filled value
6. **LaTeX color coding preserved** — `\blueE`, `\maroonD`, `\goldE` stay as-is
   to maintain visual consistency with practice problems

### Multiple Strategies Per Concept

Perseus "Add within 20" uses FOUR visual strategies across its 20 items:
- Items 1-6: Number line
- Items 7-11: Ten frame
- Items 12-15: Place value blocks
- Items 16-20: Groups of objects

We parameterize ALL of them. The intro shows multiple strategies to give
students multiple mental models — exactly as Perseus designed it.

---

## 5. Vocabulary & Cognitive Constraints

The same two-rule system from `practice_gen_strategy.md` applies:

### Rule 1: Incorporate — draw from prior vocabulary

All intro text may freely use any term in `node.cumulative_vocab`. These are
terms from all prior nodes that the student has already been taught.

### Rule 2: Exclude — never use future vocabulary

No intro text may use, imply, or require any term NOT in
`node.cumulative_vocab ∪ node.introduces_vocab`. The intro for a node may
use terms it IS introducing (that's the point of the intro), plus everything
prior. Nothing beyond.

### Enforcement Points

| Content Type | How Constraints Apply |
|--------------|----------------------|
| Type A (worked examples) | Step text uses only `cumulative_vocab` + mathematical notation |
| Type B (definitions) | Definition text uses only `cumulative_vocab` to define `introduces_vocab` terms |
| Type B (introductions) | Connecting narrative uses only `cumulative_vocab`; NEVER defines vocabulary terms |
| Interest slots | Interest bank objects are general language (not controlled — "basketball" doesn't need teaching) |

### Grade Knowledge Ceiling

From `ph/matatag_grade_knowledge.json`:

| Grade | `sentence_max_words` | `number_range.max` | Key Constraint |
|-------|---------------------|-------------------|----------------|
| 1 | 15 | 100 | No commas, no thousands separator |
| 2 | 18 | 1,000 | No commas for numbers up to 1000 |
| 3 | 22 | 10,000 | Space separator for thousands |

Every sentence in intro content respects `sentence_max_words`. Every number
in worked examples respects `number_range.max`.

### NOT_YET_KNOWN Enforcement

Each grade level declares concepts that have NOT been introduced. The intro
system never references these, even implicitly:

- Grade 1: No coordinates, no parallel/perpendicular lines, no area, no
  multiplication, no division, no bar graphs
- Grade 2: No decimals, no ratios, no algebraic expressions, no volume,
  no mean/median/mode

---

## 6. Interest Wrapping

Interest wrapping applies to Type A worked examples where Perseus uses
concrete objects (groups of sharks, cookies, flowers, etc.). These become
slots fillable from the student's registered interest theme.

### Interest Bank Structure

Source: `data/ interest_bank.json` — 25 Filipino student interest
themes, each providing:

```json
{
    "interest_id": 1,
    "name": "Competitive Multiplayer Games",
    "grade_band": [5, 10],
    "actors": ["Kuya Franz", "Aldrin", "Mikko", ...],
    "objects": ["ranked matches", "hero skins", "kill streaks", ...],
    "places": ["internet cafe", "school computer lab", ...],
    "item1": ["headset", "gaming mouse", ...],
    "item2": ["phone cooling fan", "controller grip", ...],
    "peso_range": [50, 1500]
}
```

### When Interest Wrapping Applies

- **Worked examples with object groups** — "12 sharks + 8 sharks" becomes
  "12 {objects} + 8 {objects}" → "12 hero skins + 8 hero skins"
- **Story-framed worked examples** — "{actor} has {a} {objects}. {actor}
  gets {b} more."
- **NOT applied to:** definitions, introduction text, pure mathematical notation,
  number line / ten frame / place value block strategies (these are abstract)

### Grade Band Filtering

Each interest theme has a `grade_band`. An interest designed for Grades 5-10
is not appropriate for a Grade 1 student. The generator filters by:

```python
eligible_interests = [
    theme for theme in INTEREST_BANK
    if theme.grade_band[0] <= student_grade <= theme.grade_band[1]
]
```

### Answer Invariance

The correct answer is identical regardless of interest theme. The math never
changes. Only the story context changes.

```
f(a=5, b=3, interest="gaming")    → result = 8
f(a=5, b=3, interest="basketball") → result = 8
f(a=5, b=3, interest=None)         → result = 8
```

---

## 7. Mini-Lesson Grouping

A "node" in the user's terminology is a quarter within a subdomain (e.g.,
G1_NA_Q1 = Grade 1, Number & Algebra, Quarter 1). Each node contains
multiple learning competencies.

### Grouping Algorithm

Competencies within a node are grouped into mini-lessons by concept
relatedness. Groups are defined statically based on pedagogical analysis:

```python
MINI_LESSON_GROUPS = {
    "g1_na_q1": [
        {
            "title": "Counting & Numerals",
            "competencies": ["mat_g1_na_q1_0", "mat_g1_na_q1_1", "mat_g1_na_q1_2"],
            "perseus_strategies": ["count_objects", "number_line", "ten_grid", "place_value_blocks"]
        },
        {
            "title": "Comparing & Ordering",
            "competencies": ["mat_g1_na_q1_3", "mat_g1_na_q1_4", "mat_g1_na_q1_5"],
            "perseus_strategies": ["place_value_decomposition", "number_line_comparison"]
        },
        {
            "title": "Breaking Apart Numbers",
            "competencies": ["mat_g1_na_q1_6"],
            "perseus_strategies": ["ten_frame", "number_bonds"]
        },
        {
            "title": "Addition",
            "competencies": ["mat_g1_na_q1_7", "mat_g1_na_q1_8", "mat_g1_na_q1_9"],
            "perseus_strategies": ["number_line", "ten_frame", "place_value_blocks", "groups_of_objects"]
        }
    ]
}
```

### Mini-Lesson Structure

Each mini-lesson produces this slide sequence:

```
1. Introduction slide — Type B content
   Motivates the concept and connects to what student already knows.
   MUST NOT define vocabulary terms — that is the definitions slide's job.
   [1 slide, short sentences, cumulative_vocab only]

   GOOD: "You can count up. Now let's put two groups together.
          How many are there in total?"
   BAD:  "Addition means putting two groups together.
          The answer is called the sum."
   (The BAD version defines "addition" and "sum" — making the
   definitions slide redundant.)

2. Definition slide — Type B content
   Formally introduces new vocabulary for these competencies.
   [1 slide, terms + simple definitions from definition bank]
   Omitted entirely when student_vocab = [] for the group.

3. Worked example slides — Type A content (one per visual strategy)
   Step-by-step demonstration using Perseus-derived template.
   [2-5 slides depending on concept, one strategy per slide set]
   Multiple strategies shown if Perseus uses multiple.
   Interest wrapping applied to object-group strategies.
   EVERY competency in the group must have at least one worked example.
```

### Slide Count Estimates

| Node | Mini-lessons | Slides per mini-lesson | Total slides |
|------|-------------|----------------------|--------------|
| G1_NA_Q1 | 4 | 3-5 | 12-20 |
| G1_NA_Q2 | 3-4 | 3-5 | 9-20 |
| G1_MG_Q1 | 2-3 | 3-4 | 6-12 |

---

## 8. Definition Bank

### Vocabulary Classification Principle

**`student_vocab` is NOT derived from competency text.** Competency text is
written for teachers and curriculum designers. It uses process language
("compose", "decompose", "illustrate", "represent") that was never meant
to become student vocabulary.

`student_vocab` is independently determined by asking:

> **"Would a student be unable to understand or answer a practice problem
> without knowing this specific word?"**

If the answer is no — if the concept can be taught by demonstration, or
the word is common English, or it's a formal name for something shown
visually — the word is excluded. **When in doubt, leave it out.**

### Two-Field Vocabulary Structure

Every node in `vocab_annotation.json` has two fields:

```json
{
  "student_vocab": ["terms students need to understand practice problems"],
  "curriculum_vocab": ["teacher/curriculum terms — never shown to students"]
}
```

`student_vocab` feeds into:
- The **definitions slide** in the intro (only if non-empty)
- The **`cumulative_vocab`** in `knowledge_graph_g1_3.json` (accumulated across nodes)
- Constraint checking for worked example and introduction text

`curriculum_vocab` is kept for curriculum alignment tracing only.

### When `student_vocab = []`

Many nodes have no student vocabulary. This is correct, not a gap.
The mini-lesson structure becomes:

```
1. Introduction slide  — motivates the concept, connects to prior learning
2. Worked example(s)   — demonstrates the concept through action
```

No definitions slide. The concept is taught entirely through demonstration.
The introduction text must also contain no words outside
`cumulative_vocab` — it cannot introduce terms through the back door.

### Classification Rules

**Always `curriculum_vocab` (never `student_vocab`):**

| Category | Examples |
|----------|---------|
| Process verbs from competency text | `compose`, `decompose`, `illustrate`, `represent`, `apply`, `distinguish` |
| Curriculum methodology phrases | `concrete materials`, `concrete model`, `pictorial model`, `given orally`, `given in pictures` |
| Scope/range qualifiers | `sums up to 100`, `without regrouping` (where the concept is regrouping, not scope), `2-digit and 1-digit` |
| Formal property names before grade-appropriate | `identity property`, `commutative property` (G1-G2), `associative property` (G1-G2), `multiplicative identity` (G1-G3) |
| Redundant process descriptions | `read numerals` (the term is `numeral`), `compose shapes`, `decompose shapes` |
| Framework qualifiers | `vice versa`, `tabular form`, `inductively` |

**`student_vocab` test — passes all three:**
1. The word would appear in a practice problem question
2. The word is a noun, adjective, or specific math phrase — not a process verb
3. A student could not do the practice problems without knowing this word

### Definition Bank Location

`backend/app/intro_gen/generator.py` — `DEFINITION_BANK` dict.

Definitions use only `cumulative_vocab` words at the grade the term is
introduced. Maximum one sentence. No circular definitions (no using the
term to define itself).

### Rebuilding After Changes

If `student_vocab` changes in `vocab_annotation.json`:

```bash
python3 scripts/reclassify_vocab.py   # re-applies classification map
python3 scripts/rebuild_knowledge_graph.py  # recomputes cumulative_vocab
```

Never edit `knowledge_graph_g1_3.json` by hand — it is generated.

---

## 9. Runtime Generation Pipeline

When a student enters a node for the first time (or chooses to review):

```python
def generate_intro(node_key: str, student_id: int, seed: int = None) -> IntroContent:
    """
    node_key: e.g., "g1_na_q1"
    Returns ordered slide sequence for the full node intro.
    """
    seed = seed or generate_seed()
    rng = Random(seed)

    # 1. Load mini-lesson groups for this node
    groups = MINI_LESSON_GROUPS[node_key]

    # 2. Load student interest (if any)
    interest = get_student_interest(student_id)

    mini_lessons = []
    for group in groups:
        slides = []

        # 3. Load knowledge graph data for these competencies
        competency_ids = group["competencies"]
        introduces_vocab = collect_introduces_vocab(competency_ids)
        cumulative_vocab = get_cumulative_vocab(competency_ids[0])

        # 4. Generate introduction slide (Type B)
        introduction = generate_introduction(
            competency_ids=competency_ids,
            cumulative_vocab=cumulative_vocab,
            sentence_max_words=get_sentence_max(node_key)
        )
        slides.append(introduction)

        # 5. Generate definition slide (Type B)
        definitions = lookup_definitions(introduces_vocab)
        slides.append(definitions)

        # 6. Generate worked example slides (Type A)
        for strategy in group["perseus_strategies"]:
            template = load_parameterized_template(competency_ids, strategy)
            values = sample_values(template.param_bounds, rng)
            result = compute_result(template.answer_formula, values)

            # Apply interest wrapping if applicable
            if template.interest_wrappable and interest:
                context = fill_interest_slots(template, interest, rng)
            else:
                context = None

            worked_example = fill_template(template, values, result, context)
            slides.append(worked_example)

        mini_lessons.append(MiniLesson(
            title=group["title"],
            slides=slides
        ))

    return IntroContent(
        node_key=node_key,
        seed=seed,
        mini_lessons=mini_lessons,
        can_skip=True
    )
```

### Seeded Randomness

Same principle as practice generation:
- Same seed → same numbers in worked examples
- Different seed → different numbers → fresh content
- Enables reproducibility (teacher can share a specific intro) while
  ensuring variety across sessions

---

## 10. Backend API Specification

### GET /api/matatag/intro/{node_key}

Returns the full intro content for a node.

**Parameters:**
- `node_key` (path): e.g., `"g1_na_q1"`, `"g2_mg_q3"`
- `student_id` (query): for interest wrapping
- `seed` (query, optional): for reproducibility

**Response:**

```json
{
    "node_key": "g1_na_q1",
    "node_label": "Grade 1 — Numbers, Counting & Addition",
    "seed": 48291,
    "can_skip": true,
    "mini_lessons": [
        {
            "title": "Counting & Numerals",
            "competencies_covered": ["mat_g1_na_q1_0", "mat_g1_na_q1_1", "mat_g1_na_q1_2"],
            "slides": [
                {
                    "type": "introduction",
                    "content": "Numbers help us count things.\nWe can count up: 1, 2, 3, 4...\nLet's learn how we write and show numbers."
                },
                {
                    "type": "definitions",
                    "terms": [
                        {"term": "counting up", "definition": "saying numbers from small to big"},
                        {"term": "numeral", "definition": "a symbol for a number, like 5 or 23"},
                        {"term": "number line", "definition": "a line with numbers in order"}
                    ]
                },
                {
                    "type": "worked_example",
                    "title": "Counting on a Number Line",
                    "strategy": "number_line",
                    "steps": [
                        {
                            "text": "Let's find 1 more than $\\blueE{7}$.",
                            "visual_type": "NumberLine",
                            "visual_params": {"start": 0, "end": 15, "markers": [7]}
                        },
                        {
                            "text": "Start at $\\blueE{7}$. Count up 1.",
                            "visual_type": "NumberLine",
                            "visual_params": {"start": 0, "end": 15, "hop_from": 7, "hop_by": 1}
                        },
                        {
                            "text": "We land on $\\goldE{8}$. 1 more than 7 is $\\goldE{8}$.",
                            "visual_type": "NumberLine",
                            "visual_params": {"start": 0, "end": 15, "highlight": 8}
                        }
                    ]
                },
                {
                    "type": "worked_example",
                    "title": "Counting Objects",
                    "strategy": "groups_of_objects",
                    "steps": [
                        {
                            "text": "How many turtles are there?",
                            "visual_type": "ObjectGrid",
                            "visual_params": {"object": "turtle", "count": 12, "rows": 3, "cols": 4}
                        },
                        {
                            "text": "We count: 1, 2, 3... 12.\nThe last number we say is $\\goldE{12}$.",
                            "visual_type": "ObjectGrid",
                            "visual_params": {"object": "turtle", "count": 12, "numbered": true, "highlight_last": true}
                        },
                        {
                            "text": "There are $\\goldE{12}$ turtles.",
                            "visual_type": null,
                            "visual_params": null
                        }
                    ]
                }
            ]
        }
    ]
}
```

### POST /api/matatag/intro/{node_key}/viewed

Marks the intro as viewed for a student.

**Body:**
```json
{"student_id": 27}
```

**Response:**
```json
{"status": "ok", "viewed_at": "2025-01-15T10:30:00Z"}
```

### GET /api/matatag/intro/{node_key}/status

Checks whether a student has viewed the intro.

**Parameters:**
- `student_id` (query)

**Response:**
```json
{"viewed": true, "viewed_at": "2025-01-15T10:30:00Z"}
```

---

## 11. Frontend Specification

### New View State: `node_intro`

Added to `practiceViewType` in `App.jsx`:

```
'subject_selection' → 'matatag_track_selection' → 'node_intro' → 'workspace'
```

### Entry Flow

```
Student clicks subdomain track (e.g., "Number & Algebra")
    ↓
Backend identifies current node (e.g., g1_na_q1)
    ↓
Frontend checks: GET /api/matatag/intro/g1_na_q1/status?student_id=27
    ├── Not viewed → Show entry screen:
    │     "Start Learning" (prominent) + "Skip to Practice" (secondary)
    └── Already viewed → Show entry screen:
          "Review Lesson" + "Start Practice" (prominent)
    ↓
Student clicks "Start Learning" or "Review Lesson"
    ↓
GET /api/matatag/intro/g1_na_q1?student_id=27
    ↓
Frontend renders slides in node_intro view
    ↓
Student completes or skips
    ↓
POST /api/matatag/intro/g1_na_q1/viewed (if first time)
    ↓
Transition to workspace (practice)
```

### Slide Component

```
┌─────────────────────────────────────────┐
│  ← Mini-lesson 1 of 4                  │
│  "Counting & Numerals"                  │
├─────────────────────────────────────────┤
│                                         │
│  [Slide content rendered by type]       │
│                                         │
│  For "introduction": markdown text      │
│  For "definitions": term/definition list│
│  For "worked_example": step-by-step     │
│    with visual component + text         │
│                                         │
├─────────────────────────────────────────┤
│  ○ ○ ● ○ ○         [Skip] [Next →]     │
│  slide 3 of 5                           │
└─────────────────────────────────────────┘
```

### Slide Type Rendering

| Type | Rendering |
|------|-----------|
| `introduction` | Markdown paragraphs with LaTeX math support |
| `definitions` | Highlighted term cards: **term** — definition |
| `worked_example` | Current step shown with text + visual component below. "Next Step" advances within the worked example. |

### Visual Rendering Priority

1. **Existing visual components** — `NumberLine`, `BarChart`, `ClockSet`,
   `GridArea`, `SortOrder`, `Calendar`, `PesoMoney` (from `visual_skeletons.py`
   + `VisualSkeletons.jsx`)
2. **ASCII/text fallback** — for cases where no interactive component exists
3. **New components** — created only when existing components are insufficient

### Navigation

- **Within a worked example:** "Next Step" button advances through steps
  (one step shown at a time, like a slideshow within a slide)
- **Between slides:** "Next" / "Previous" buttons
- **Between mini-lessons:** automatic transition with title card
- **Skip:** always available — jumps to practice immediately
- **Final slide:** "Ready to Practice!" button transitions to workspace

---

## 12. Database Model

### New Table: `node_intro_views`

```sql
CREATE TABLE node_intro_views (
    id              SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES student_profiles(id),
    node_key        VARCHAR(20) NOT NULL,  -- e.g., "g1_na_q1"
    viewed_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, node_key)
);
```

### Node Key Format

Derived from competency IDs by dropping the competency index:

```
mat_g1_na_q1_0  →  node_key = "g1_na_q1"
mat_g2_mg_q3_5  →  node_key = "g2_mg_q3"
```

Pattern: `g{grade}_{area_code}_q{quarter}`

---

## 13. Validation

### Type A Validation (Worked Examples)

Same principle as practice generation: correctness is proven at authoring
time, not checked at runtime.

| Check | What It Validates |
|-------|-------------------|
| Formula proof | `answer_formula` produces correct result for ALL values within `param_bounds` |
| Bound safety | `param_bounds` never produce invalid states (e.g., `randint(a, b)` with `a >= b`) |
| Visual coherence | Visual params reference valid variables and produce renderable states |
| Interest invariance | Result is identical regardless of interest theme applied |
| Step completeness | Every worked example ends with the answer explicitly stated |

### Type B Validation (Authored Content)

| Check | What It Validates |
|-------|-------------------|
| Vocab audit | All terms in text exist in `cumulative_vocab ∪ introduces_vocab` for that node |
| Sentence length | Every sentence ≤ `sentence_max_words` for the grade |
| NOT_YET_KNOWN | No terms from the exclusion list appear |
| Definition circularity | Definitions don't use the term being defined |
| Definition simplicity | Definition text uses only `cumulative_vocab` (prior terms) |
| Introduction distinctness | Introduction text DOES NOT contain definitions of vocabulary terms |

### Validation Pipeline

```python
def validate_intro_content(node_key: str, content: IntroContent) -> list[str]:
    errors = []
    kg = load_knowledge_graph()

    for mini_lesson in content.mini_lessons:
        for slide in mini_lesson.slides:
            if slide.type == "introduction":
                errors += validate_vocab(slide.text, node_key, kg)
                errors += validate_sentence_length(slide.text, node_key, kg)
                errors += validate_not_yet_known(slide.text, node_key, kg)
                errors += validate_no_definitions(slide.text, node_key, kg)

            elif slide.type == "definitions":
                for term_entry in slide.terms:
                    errors += validate_definition(term_entry, node_key, kg)

            elif slide.type == "worked_example":
                errors += validate_formula(slide.answer_formula, slide.param_bounds)
                errors += validate_bounds(slide.param_bounds)
                errors += validate_visual_params(slide.steps)
                if slide.interest_wrappable:
                    errors += validate_interest_invariance(slide)

    return errors
```

---

## 14. Subagent Roles

Specialized subagents handle offline authoring and validation tasks:

### Definition Author Subagent

**Input:** `introduces_vocab` list + `cumulative_vocab` at that node +
`sentence_max_words` for the grade

**Task:** Produce a grade-appropriate definition for each term that uses
only prior vocabulary and fits within sentence length constraints.

**Output:** Definition bank entries (JSON)

**Runs:** Once per new vocabulary term. Output is validated and stored
permanently.

### Introduction Author Subagent

**Input:** Competency text + `cumulative_concepts` + `introduces_concepts`
+ `sentence_max_words`

**Task:** Write 2-4 connecting sentences that motivate the concept group,
linking to what the student already knows. MUST NOT define vocabulary terms
— that is the definitions slide's job. The introduction should make the
student curious about the concept without naming or defining it formally.

**Output:** Introduction text (markdown)

**Runs:** Once per mini-lesson group. Output is validated and stored
permanently.

### Content Validator Subagent

**Input:** Any authored intro content + knowledge graph data for the
target node

**Task:** Run all validation checks (vocab audit, sentence length,
NOT_YET_KNOWN, definition quality, pedagogical soundness)

**Output:** Pass/fail + list of violations

**Runs:** On every authored content piece before it's accepted into the
system.

### Perseus Strategy Selector Subagent

**Input:** MATATAG competency text + available Perseus templates (9,072)

**Task:** Identify which Perseus templates best demonstrate the competency,
beyond what `matatag_matched_problems.json` provides. Evaluate pedagogical
appropriateness, grade-level fit, and visual strategy diversity.

**Output:** Ranked list of Perseus template IDs with rationale

**Runs:** Once per competency. Improves on the automated similarity matching.

---

## 15. Data Dependencies

| File | Role in Intro System |
|------|---------------------|
| `data/knowledge_graph_g1_3.json` | Primary constraint source: `introduces_vocab`, `cumulative_vocab`, `cumulative_concepts`, `sentence_max_words`, `prior_node_ids` |
| `data/skeletons/vocab_annotation.json` | Source of truth for what each node introduces (drives definition slides) |
| `ph/matatag_grade_knowledge.json` | Grade-level ceiling: `number_range`, `sentence_max_words`, `NOT_YET_KNOWN`, `operations_known` |
| `ph/matatag_matched_problems.json` | Maps competencies → Perseus templates (starting point for worked examples) |
| `data/ interest_bank.json` | 25 interest themes for wrapping worked examples |
| `scripts/perseus_extractor/output/perseus_templates/*.json` | Source templates: hint sequences, visual strategies, assessment items |
| `scripts/perseus_extractor/output/ccss_crosswalk_v2.json` | Maps CCSS standards → Perseus templates (useful for finding additional relevant templates) |

---

## 16. File Structure

```
backend/app/
  intro_gen/
    __init__.py
    templates/
      __init__.py
      parameterized/          # Parameterized Perseus templates (Type A)
        counting.py           # Counting strategies (number line, objects)
        addition.py           # Addition strategies (number line, ten frame, blocks, objects)
        comparison.py         # Comparing strategies (place value decomposition)
        place_value.py        # Place value strategies (blocks, ten grids, expanded form)
        subtraction.py        # Subtraction strategies
        ...                   # One file per DNA concept
      definitions/
        definition_bank.json  # All vocab definitions (~300 terms)
      introductions/
        g1_na_q1.json         # Type B introduction text per mini-lesson group
        g1_na_q2.json
        ...

    generator.py              # Runtime generator: fills slots, applies interest, assembles slides
    groupings.py              # MINI_LESSON_GROUPS: node_key → competency groups
    validation.py             # Validation pipeline for all content types
    schemas.py                # IntroSlide, MiniLesson, IntroContent dataclasses

  main.py                     # Add intro endpoints (GET/POST)
  models.py                   # Add NodeIntroView table
  schemas.py                  # Add IntroContentResponse Pydantic schema

frontend/src/
  App.jsx                     # Add node_intro view state + slide component
  components/
    IntroSlides.jsx           # (optional) Extract slide component if App.jsx too large

data/
  skeletons/
    knowledge_graph_g1_3.json # Existing — provides constraints
    vocab_annotation.json     # Existing — provides introduces_vocab
    interest_bank.json        # Existing — provides interest themes
```

---

## 17. Reference: G1_NA_Q1 Intro Structure

The first node to implement (Grade 1, Number & Algebra, Quarter 1):

### Competencies (10 total)

| Index | Competency | Concept Group |
|-------|-----------|---------------|
| 0 | Count up to 100 (counting up/down, 1 more/1 less) | Counting & Numerals |
| 1 | Read and write numerals up to 100 | Counting & Numerals |
| 2 | Represent numbers using models (number line, blocks) | Counting & Numerals |
| 3 | Compare two numbers up to 20 | Comparing & Ordering |
| 4 | Order numbers up to 20 (ascending/descending) | Comparing & Ordering |
| 5 | Ordinal numbers (1st through 10th) | Comparing & Ordering |
| 6 | Compose and decompose numbers up to 10 | Breaking Apart Numbers |
| 7 | Addition with sums up to 20 (concrete/pictorial models) | Addition |
| 8 | Properties of addition (identity, commutative) | Addition |
| 9 | Solve addition word problems (sums up to 20) | Addition |

### Mini-Lesson 1: "Counting & Numerals"

**Type B — Introduction:**
> Numbers help us count things.
> We can count up: 1, 2, 3, 4, 5...
> We can count down: 5, 4, 3, 2, 1...
> Let's learn how we write and show numbers.

*(Note: does NOT define "numeral" or "number line" — those are
defined on the definitions slide. The introduction only motivates.)*

**Type B — Definitions:**
- **1 more** — the next number when you count up
- **1 less** — the next number when you count down
- **numeral** — a written symbol for a number
- **number line** — a line with numbers placed in order

**Type A — Worked Example (Number Line — "1 more", competency _0):**
> Step 1: "Let's find 1 more than {a}." [NumberLine: marker at {a}]
> Step 2: "Start at {a}. Count up 1." [NumberLine: hop from {a} by 1]
> Step 3: "We land on {result}. 1 more than {a} is {result}." [NumberLine: highlight {result}]
> param_bounds: {a: (2, 50)}; formula: a + 1

**Type A — Worked Example (Number Line — "1 less", competency _0):**
> Step 1: "Let's find 1 less than {a}." [NumberLine: marker at {a}]
> Step 2: "Start at {a}. Count down 1." [NumberLine: hop from {a} by -1]
> Step 3: "We land on {result}. 1 less than {a} is {result}." [NumberLine: highlight {result}]
> param_bounds: {a: (3, 50)}; formula: a - 1

**Type A — Worked Example (Numeral Recognition, competency _1):**
> Step 1: "The numeral {n} is a symbol for the number {n}." [NumberLine: range n-4 to n+4]
> Step 2: "Find {n} on the number line." [NumberLine: highlight {n}]
> Step 3: "1 more than {n} is {n+1}. 1 less than {n} is {n-1}." [NumberLine: markers at n-1, n+1]
> param_bounds: {n: (12, 40)}; connects numeral recognition to 1-more/1-less

**Type A — Worked Example (Object Counting, competency _2):**
> Step 1: "How many {objects} are there?" [ObjectGrid: {count} objects]
> Step 2: "We count each one: 1, 2, 3... {count}. The last number is {count}." [ObjectGrid: numbered]
> Step 3: "There are {count} {objects}." [result statement]
> param_bounds: {count: (5, 15)}; interest_wrappable: True

### Mini-Lesson 2: "Comparing & Ordering"

**Type B — Introduction:**
> You can count numbers. Now let's use them.
> Look at two numbers — which one is bigger?
> We can also put numbers in order.

*(Note: does NOT define "compare" — the definitions slide does that.
Uses "bigger" which is a cross-branch term available from the start.)*

**Type B — Definitions:**
- **compare** — look at two numbers to find which is bigger or smaller
- **1st** — first — the one at the front
- **2nd** — second — the one right after 1st
- **3rd** — third — the one right after 2nd
- **4th** through **10th** — fourth through tenth (each: "the one right after {N-1}th")

**Type A — Worked Example (Number Line Comparison, competency _3):**
> Step 1: "Compare {a} and {b}." [NumberLine: markers at both]
> Step 2: "Find each on the number line. The one further to the right is bigger." [NumberLine: markers]
> Step 3: "{a} is more than {b}." (or "less than") [text only]
> param_bounds: {a: (1, 20), b: (1, 20), a ≠ b}; uses "more than" / "less than" (NOT "greater than")

**Type A — Worked Example (Ordering, competency _4):**
> Step 1: "Put these in order: {shuffled 4 numbers}" [NumberCards: unordered]
> Step 2: "Find the smallest first..." [NumberCards: ordered, highlighted]
> Step 3: "In order: {sorted}" [text only]
> param_bounds: 4 distinct numbers from range (1, 20)

**Type A — Worked Example (Ordinal Position, competency _5):**
> Step 1: "These are in a line: {5 items}" [OrderedLine: 5 items]
> Step 2: "The 1st is {item0}. The 2nd is {item1}. The 3rd is {item2}." [OrderedLine: highlighted]
> Step 3: "1st, 2nd, 3rd... tell where something is in a line." [text only]
> interest_wrappable: True (items from interest bank objects)

### Mini-Lesson 3: "Breaking Apart Numbers"

**`student_vocab`: `[]` — no definitions slide**

**Type B — Introduction:**
> You can count numbers. You can compare them.
> Now let's look inside a number.
> Every number is made of smaller parts.
> 5 can be 3 and 2. Or 4 and 1. Or 5 and 0.
> There are many ways to break apart a number.

*(No reference to "compose" or "decompose" — those are curriculum terms,
not student vocabulary. The concept is taught entirely by demonstration.)*

**Type A — Worked Example (Ten Frame — "Parts of 10", competency _6):**
> Step 1: "Here is a ten frame. Fill {a} dots." [TenFrame: {a} filled]
> Step 2: "How many spaces are empty?" [TenFrame: empty highlighted]
> Step 3: "{a} and {complement} make 10." [TenFrame: both labelled]
> param_bounds: {a: (1, 9)}; no + notation; no vocab terms in steps

**Type A — Worked Example (Number Bonds — "Breaking Apart a Number", competency _6):**
> Step 1: "Let's look at {target}." [NumberBond: whole={target}, parts empty]
> Step 2: "One way: {target} is {part1} and {part2}." [NumberBond: filled]
> Step 3: "Another way: {target} is {alt1} and {alt2}." [NumberBond: alternate split]
> Step 4: "{target} can be broken apart in many ways." [no visual]
> param_bounds: {target: (5, 10)}; two distinct splits shown; no + sign anywhere

### Mini-Lesson 4: "Addition"

**Type B — Introduction:**
> You can count up. You can break numbers apart.
> Now let's put two groups together.
> How many are there in total?

*(Note: does NOT use the words "addition" or "sum" — those are
defined on the definitions slide. The introduction only poses the question.)*

**Type B — Definitions:**
- **addition** — putting two groups together to find the total
- **sum** — the answer you get when you add

*(Note: "addend" is curriculum_vocab, not student_vocab. Students do not
need this word to solve any G1 practice problem. The concept of "numbers
being added" is conveyed through demonstration, not vocabulary.)*

**Type A — Worked Example (Number Line, competency _7):**
> Step 1: "Let's add {a} + {b}." [NumberLine: empty]
> Step 2: "First, jump to {a}." [NumberLine: hop to {a}]
> Step 3: "Next, jump {b} more." [NumberLine: hop from {a} by {b}]
> Step 4: "The jumps end at {result}. {a} + {b} = {result}." [NumberLine: highlight]
> param_bounds: {a: (2, 9), b: (1, 9), a+b ≤ 20}; formula: a + b

**Type A — Worked Example (Ten Frame, competency _7):**
> Step 1: "Let's add {a} + {b} using a ten frame." [TenFrame: empty]
> Step 2: "First, show {a} dots." [TenFrame: {a} filled]
> Step 3: "Next, add {b} more dots." [TenFrame: {a}+{b} filled]
> Step 4: "Count all the dots: {result}. {a} + {b} = {result}." [TenFrame: total]
> param_bounds: {a: (4, 9), b: (1, 9), a+b ≤ 20}; formula: a + b

**Type A — Worked Example (Groups of Objects — interest-wrapped, competency _7):**
> Step 1: "{actor} has {a} {objects}." [ObjectGroup: {a} items]
> Step 2: "{actor} gets {b} more {objects}." [ObjectGroup: {a} + {b} items, adding highlighted]
> Step 3: "Now {actor} has {result} {objects} total. {a} + {b} = {result}" [ObjectGroup: all items]
> param_bounds: {a: (3, 10), b: (2, 8), a+b ≤ 20}; interest_wrappable: True

**Type A — Worked Example (Identity Property — interest-wrapped, competency _8):**
> With interest: "{actor} has {a} {objects}. {actor} gets 0 more."
> Without interest: "What is {a} + 0?"
> Step 2: "Nothing was added." [ObjectGroup: same count]
> Step 3: "{a} + 0 = {a}. Adding zero keeps the number the same." [equation]
> param_bounds: {a: (1, 20)}; formula: a; interest_wrappable: True

**Type A — Worked Example (Commutative Property, competency _8):**
> Step 1: "Let's add {a} and {b}." [ObjectGroup: two color groups]
> Step 2: "{a} + {b} = {result}. Now flip the order: {b} and {a}." [ObjectGroup: reversed groups]
> Step 3: "{b} + {a} = {result}. Same answer! The order does not change the sum." [text only]
> param_bounds: {a: (1, 8), b: (a+1, 9)}; formula: a + b
> NOTE: Step 1 poses the problem WITHOUT revealing the answer. Answer appears
> only AFTER both orderings are shown. This lets students discover the pattern.

---

## 18. Implementation Phases

### Phase 1: Infrastructure
- Backend: `NodeIntroView` model, API endpoints, schemas
- Backend: `intro_gen/` module structure with generator and validation
- Frontend: `node_intro` view state, slide component, navigation flow

### Phase 2: G1_NA_Q1 Content
- Parameterize Perseus templates for counting, comparison, decomposition, addition
- Author definition bank entries for G1 NA Q1 vocabulary (~30 terms)
- Author introduction text for 4 mini-lessons
- Validate all content against knowledge graph constraints

### Phase 3: Scale to G1
- Extend to remaining G1 nodes (NA Q2-Q4, MG Q1-Q4, DP Q1-Q4)
- Author definitions for all G1 vocabulary
- Parameterize additional Perseus templates

### Phase 4: Scale to G1-3
- Extend to G2 and G3
- Complete definition bank (~300 terms)
- Create/refine subagents for scaling content authoring

---

## 19. Open Questions (To Resolve During Implementation)

1. **Perseus image assets** — Perseus templates reference `web+graphie:` images.
   Do we host these, regenerate equivalent SVGs, or use our existing visual
   components exclusively?

2. **Worked example step count** — Perseus uses 2-5 steps. Should we enforce
   a consistent step count across all worked examples, or let it vary naturally?

3. **Multiple strategies shown vs. student choice** — Should the intro show
   ALL strategies sequentially (as designed above), or let the student choose
   which strategy to view?

4. **Intro revisit behavior** — When a student reviews a previously-viewed
   intro, should it use the same seed (familiar content) or a new seed
   (fresh numbers)?

5. **Partial completion** — If a student views 2 of 4 mini-lessons and leaves,
   should the system remember their position?

---

## 20. Lessons Learned & Implementation Pitfalls

This section documents mistakes made during the G1_NA_Q1 implementation and how to
avoid them on future nodes. **Read this before implementing any new node.**

---

### 20.0 Curriculum Descriptor ≠ Student Vocabulary

**Problem (the most important pitfall):** Competency text is written for teachers
and curriculum designers. It uses process language ("compose and decompose numbers",
"illustrate addition", "represent using pictorial models") that describes WHAT
TEACHERS DO, not words students need to learn. Treating competency text as the
source of student vocabulary produces definition slides full of abstract, formal
terms that get in the way of learning the concept.

**Example of the mistake:**
G1 NA Q1_6 competency: "Compose and decompose numbers up to 10..."
Old student_vocab: `["compose", "decompose"]`
Result: A Grade 1 student was shown definitions for Latin-root words before
learning the concept.

**The correct approach:**
Ask: *"Would a student be unable to answer a practice problem without knowing
this specific word?"* If no — or if in doubt — leave it out.

For G1 NA Q1_6, the concept is taught entirely by demonstration:
- "5 can be 3 and 2. Or 4 and 1."
- Number bond visuals showing two different splits
- No vocabulary slide at all

**Rule:** `student_vocab` is an INDEPENDENT judgment, not an extraction from
competency text. Many nodes correctly have `student_vocab = []`.

**Vocabulary source of truth:** `data/skeletons/vocab_annotation.json`
— `student_vocab` field per node.

**Never regenerate vocab from competency text.** If `vocab_annotation.json`
needs updating, edit `STUDENT_VOCAB_MAP` in `scripts/reclassify_vocab.py`
and re-run both scripts.

---

### 20.1 Interest Bank Maintenance

**Problem:** The `25_student_interests.md` file listed "Bible & Christianity" as
interest #1, but `interest_bank.json` was missing it entirely. The API returned
only 25 interests instead of 26.

**Root Cause:** Manual sync between documentation (MD) and implementation (JSON).

**Prevention:**
1. When adding/modifying interests, update BOTH files in the same commit
2. Interest IDs in JSON must match the numbering in the MD file
3. Every interest entry MUST include an `emoji` field for visual rendering
4. Run validation: `curl /api/matatag/intro/interests | jq '.interests | length'`
   should match the count in `25_student_interests.md`

**Interest Bank Entry Checklist:**
```json
{
  "interest_key": {
    "interest_id": 1,           // Must match MD numbering
    "name": "Display Name",
    "grade_band": [1, 10],      // [min_grade, max_grade]
    "actors": [...],            // 5-10 character names
    "objects": [...],           // 5-10 countable nouns
    "places": [...],            // 5-10 locations
    "item1": [...],             // Purchasable items (low cost)
    "item2": [...],             // Purchasable items (higher cost)
    "peso_range": [20, 500],    // Price range for word problems
    "emoji": "🔹"               // REQUIRED: theme emoji for fallback rendering
  }
}
```

---

### 20.2 Visual Param Formats

**Problem:** The `ObjectGroup` visual type had TWO different param formats, but
the frontend renderer only handled one. The commutative property slide used
`{groups: [...]}` instead of `{count: N}`, causing "No items" to display.

**Root Cause:** Backend generator used different param shapes for different
pedagogical purposes without documenting the contract.

**Prevention:**
1. Document ALL param formats for each visual type BEFORE implementing
2. Frontend renderers must handle all documented formats
3. When a visual type needs a new param format, update both backend AND frontend

**Visual Type Param Contracts:**

| Visual Type | Format 1 (Simple) | Format 2 (Multi-group) |
|-------------|-------------------|------------------------|
| `ObjectGroup` | `{count, object, adding?, numbered?}` | `{groups: [{count, color}, ...]}` |
| `NumberLine` | `{start, end, markers?, highlight?}` | `{start, end, hop_from, hop_by}` |
| `TenFrame` | `{filled, total, highlight_empty?}` | `{filled, total, color_split, added}` |
| `NumberBond` | `{whole, parts: [a, b]}` | — |
| `PlaceValueBlocks` | `{number, color?}` | — |
| `NumberCards` | `{numbers: [...], ordered?}` | — |
| `OrderedLine` | `{items: [...], highlighted?: [indices]}` | — |
| `Comparison` | `{left, right}` | `{left: {visual, ...}, right: {visual, ...}}` |
| `FractionBar` | `{parts, shaded, label?}` | `{parts, shaded, allow_overflow?, show_wholes?}` |
| `ClockSet` | `{hour, minute, highlight?}` | `{hour, minute, second_hour?, second_minute?}` |
| `PesoMoney` | `{coins: [...], bills: [...], mode}` | — |
| `BarGraph` | `{data: [{label, value}], orientation}` | — |
| `AreaGrid` | `{rows, cols, show_total?}` | — |
| `BalanceScale` | `{left: {label, mass_g}, right: {...}}` | — |
| `CapacityDisplay` | `{containers: [{label, capacity_mL}]}` | — |
| `SymmetryDisplay` | `{shape, mode, axis?}` | — |
| `ProbabilityBag` | `{items: [{color, count}], highlight?, show_counts?}` | — |
| `CoinDisplay` | `{show_both?, result?}` | — |

**ObjectGroup Detailed Formats:**

```javascript
// Format 1: Simple count (most worked examples)
{
  "count": 10,           // Number of items to show
  "object": "scrolls",   // Object name for label
  "adding": 6,           // Optional: items being added (different color)
  "numbered": false      // Optional: show numbers instead of emojis
}

// Format 2: Multiple color groups (commutative property)
{
  "groups": [
    {"count": 7, "color": "blue"},
    {"count": 9, "color": "maroon"}
  ]
}
```

---

### 20.3 LaTeX Color Command Rendering

**Problem:** Backend outputs Perseus-style color commands (`$\blueE{7}$`), but
the frontend displayed them as raw text instead of colored numbers.

**Root Cause:** LaTeX color commands require explicit parsing—they don't
auto-render in React/browser.

**Prevention:**
1. All text rendering must include a LaTeX color parser
2. Parser must handle: `\blueE{}`, `\maroonD{}`, `\goldE{}`, `\greenD{}`, `\redD{}`

**Color Command Mapping:**

| Command | Color | Font Weight | Use Case |
|---------|-------|-------------|----------|
| `\blueE{x}` | `#3b82f6` (blue) | 800 | First operand |
| `\maroonD{x}` | `#b91c5c` (maroon) | 700 | Second operand |
| `\goldE{x}` | `#d97706` (amber) | 800 | Result/answer |
| `\greenD{x}` | `#10b981` (green) | 700 | Part 1 in decomposition |
| `\redD{x}` | `#ef4444` (red) | 700 | Highlighted/empty |

**Parser Implementation Pattern:**

```javascript
function parseLatexColors(text) {
  const colorMap = {
    'blueE': { color: '#3b82f6', fontWeight: 800 },
    'maroonD': { color: '#b91c5c', fontWeight: 700 },
    'goldE': { color: '#d97706', fontWeight: 800 },
    'greenD': { color: '#10b981', fontWeight: 700 },
    'redD': { color: '#ef4444', fontWeight: 700 },
  };
  
  // Regex: \colorName{content}
  const regex = /\\(\w+)\{([^}]+)\}/g;
  
  // Split and map to React elements with appropriate styling
  // Return array of text spans and styled spans
}
```

---

### 20.4 Empty State Handling

**Problem:** When `displayCount` was 0 or params were missing expected fields,
the renderer showed an ugly "No items" box instead of gracefully hiding.

**Root Cause:** Defensive fallback showed something instead of nothing.

**Prevention:**
1. If a visual has no meaningful content, return `null` (render nothing)
2. Never show placeholder text like "No items" or "0 items"
3. Check for valid data BEFORE rendering the container

**Pattern:**

```javascript
// BAD: Shows empty box
if (vt === 'ObjectGroup') {
  const count = vp.count || 0;
  return (
    <div className="visual-box">
      {count > 0 ? renderItems(count) : <div>No items</div>}
    </div>
  );
}

// GOOD: Returns null if nothing to show
if (vt === 'ObjectGroup') {
  // Handle groups format first
  if (vp.groups && Array.isArray(vp.groups)) {
    return renderGroups(vp.groups);
  }
  
  const count = vp.count || 0;
  if (count <= 0) return null;  // Don't render anything
  
  return (
    <div className="visual-box">
      {renderItems(count)}
    </div>
  );
}
```

---

### 20.5 Proportional Visual Representations

**Problem:** PlaceValueBlocks showed a 60px tall "tens" block and a 14px "ones"
cube—arbitrary sizes that didn't convey the 10:1 relationship.

**Root Cause:** Visual design without mathematical accuracy consideration.

**Prevention:**
1. When a visual represents quantity, sizes MUST be proportional
2. Include a LEGEND showing what each element represents
3. Label elements with their values when helpful

**PlaceValueBlocks Requirements:**

```
┌─────────────────────────────────────────────────────┐
│  LEGEND:                                            │
│  ┌──┐                                               │
│  │10│ = 10        ┌─┐ = 1                          │
│  │  │             └─┘                               │
│  │  │                                               │
│  └──┘                                               │
├─────────────────────────────────────────────────────┤
│  VALUE: 23                                          │
│                                                     │
│  ┌──┐  ┌──┐       ┌─┐ ┌─┐ ┌─┐                      │
│  │10│  │10│       │1│ │1│ │1│                      │
│  │  │  │  │       └─┘ └─┘ └─┘                      │
│  │  │  │  │                                        │
│  └──┘  └──┘                                         │
│                                                     │
│  2 × 10 + 3 × 1 = 23                               │
└─────────────────────────────────────────────────────┘
```

**Sizing Formula:**
- Unit size: 16px (configurable)
- Ones block: `unitSize × unitSize` (16×16 = 256 sq px)
- Tens block: `unitSize × 2` wide, `unitSize × 10` tall (32×160 = 5120 sq px ≈ 20× ones)
  - Or use same width and 10× height for visual clarity

---

### 20.6 Emoji Mapping Strategy

**Problem:** Object groups showed generic colored squares instead of meaningful
icons. "10 scrolls" displayed as 10 blue boxes.

**Root Cause:** No emoji mapping system for interest-themed objects.

**Prevention:**
1. Build comprehensive emoji map covering ALL interest bank objects
2. Implement fallback chain: exact → lowercase → partial match → theme emoji → default
3. Update emoji map when adding new interests

**Emoji Map Structure:**

```javascript
const emojiMap = {
  // Exact matches (singular and plural)
  'scroll': '📜', 'scrolls': '📜',
  'fish': '🐟', 'sheep': '🐑',
  'basketball': '🏀', 'basketballs': '🏀',
  
  // Compound objects
  'loaves of bread': '🍞', 'dog treat': '🦴',
  
  // Generic fallbacks
  'item': '📦', 'items': '📦',
};

// Fallback chain
function getEmoji(objectName, themeEmoji) {
  // 1. Exact match
  if (emojiMap[objectName]) return emojiMap[objectName];
  
  // 2. Lowercase match
  if (emojiMap[objectName.toLowerCase()]) return emojiMap[objectName.toLowerCase()];
  
  // 3. Partial match (object contains key or key contains object)
  for (const [key, emoji] of Object.entries(emojiMap)) {
    if (objectName.toLowerCase().includes(key) || key.includes(objectName.toLowerCase())) {
      return emoji;
    }
  }
  
  // 4. Theme emoji from interest bank
  if (themeEmoji) return themeEmoji;
  
  // 5. Default
  return '🔹';
}
```

**Interest Theme Emojis (from interest_bank.json):**

| Interest | Emoji |
|----------|-------|
| Bible & Christianity | ✝️ |
| Competitive Gaming | 🎮 |
| Creative & Sandbox | 🧱 |
| Anime RPG | ⚔️ |
| Basketball | 🏀 |
| Food & Baking | 🧁 |
| Pets | 🐕 |
| Visual Arts | 🎨 |

---

### 20.7 JSX Syntax Pitfalls

**Problem:** A ternary expression mixed string concatenation with JSX, causing
a syntax error that displayed incorrectly.

**Root Cause:** JSX and string interpolation don't mix in ternaries.

**Example of Bug:**

```javascript
// BAD: Mixing string and JSX in ternary
<div>
  {displayCount > 0 ? `${displayCount} ${obj}${adding && <span>...</span>}` : ''}
</div>

// GOOD: Use pure JSX
<div>
  {displayCount > 0 && (
    <span>
      {displayCount} {obj}
      {adding !== undefined && (
        <span> ({count} <span style={{color: 'blue'}}>+</span> {adding})</span>
      )}
    </span>
  )}
</div>
```

**Prevention:**
1. Never mix template literals with JSX elements
2. Use `&&` for conditional rendering, not ternary with empty string
3. Wrap complex conditional content in fragments or spans

---

### 20.8 Field Naming Conventions

**Problem:** Documentation showed `visual: {type, params}` but implementation
used `visual_type` and `visual_params` as flat fields on the step object.

**Root Cause:** Inconsistency between spec and implementation.

**Actual Step Structure (use this):**

```json
{
  "text": "Let's add $\\blueE{5} + \\maroonD{3}$.",
  "visual_type": "NumberLine",
  "visual_params": {
    "start": 0,
    "end": 20,
    "hop_from": 5,
    "hop_by": 3
  }
}
```

**NOT this (documentation was aspirational):**

```json
{
  "text": "...",
  "visual": {
    "type": "NumberLine",
    "params": {...}
  }
}
```

**Prevention:**
1. Always verify actual API response structure with `curl | jq` before coding
2. Update documentation when implementation differs from spec
3. Frontend code must match actual backend output, not spec

---

### 20.9 Node Completion Checklist

Before marking a node's intro content as complete, verify:

**Backend Verification:**
```bash
# 1. Check interest count matches MD file
curl -s 'http://localhost:8000/api/matatag/intro/interests' | jq '.interests | length'

# 2. Verify all interests have required fields
curl -s 'http://localhost:8000/api/matatag/intro/interests' | jq '.interests[] | select(.emoji == null)'
# Should return nothing

# 3. Test intro generation with each interest theme
for interest in bible basketball anime_rpg food_baking; do
  curl -s "http://localhost:8000/api/matatag/intro/g1_na_q1?interest=$interest&seed=42" | jq '.interest_applied'
done

# 4. Verify all visual types have params
curl -s 'http://localhost:8000/api/matatag/intro/g1_na_q1?seed=42' | \
  jq '[.mini_lessons[].slides[].steps[]? | select(.visual_type != null) | .visual_type] | unique'
```

**Frontend Verification:**
1. Build succeeds: `npm run build` (no errors)
2. Each mini-lesson renders without console errors
3. Each worked example step displays correctly
4. LaTeX colors render as colored text (not raw `\blueE{...}`)
5. Visual components show meaningful content (not empty boxes or "No items")
6. Emojis display for object groups
7. PlaceValueBlocks show legend and proportional sizing
8. Commutative property shows two color-coded groups

**Manual Testing Flow:**
1. Open Intro Lab in Parent Dashboard
2. Select the node being tested
3. Try 3+ different interest themes
4. Step through ALL slides in ALL mini-lessons
5. Verify every visual renders correctly
6. Check different seed values produce different numbers

---

### 20.10 Common Generator Pitfalls

**randint(a, b) crashes when a >= b:**
```python
# BAD: Can crash if operand_max is too small
b = rng.randint(1, operand_max - a)  # Crashes if operand_max <= a

# GOOD: Ensure valid range
b = rng.randint(1, max(1, operand_max - a))
```

**Duplicate digits in place value:**
```python
# BAD: "4575" has two 5s, causing ambiguity in "which digit is in tens place?"
num = rng.randint(10, 99)

# GOOD: Filter for unique digits if asking about specific digit positions
while True:
    num = rng.randint(10, 99)
    digits = str(num)
    if len(set(digits)) == len(digits):
        break
```

**Grade-inappropriate content:**
```python
# BAD: Using "mean" for Grade 1
visual_type = "BarChart"  # Bar charts with mean line

# GOOD: Check NOT_YET_KNOWN for the grade
if "mean" in GRADE_KNOWLEDGE[grade]["NOT_YET_KNOWN"]:
    # Use pictograph instead of bar chart with statistics
```

---

### 20.11 Debugging Visual Rendering Issues

When a visual doesn't render correctly:

1. **Check API response:**
   ```bash
   curl -s 'http://localhost:8000/api/matatag/intro/g1_na_q1?seed=42' | \
     jq '.mini_lessons[3].slides[4].steps[0]'
   ```

2. **Verify visual_type is recognized:**
   - Search frontend for `if (vt === 'YourVisualType')`
   - If not found, the renderer doesn't exist yet

3. **Verify visual_params format:**
   - Compare actual params to documented contract (Section 20.2)
   - Check for missing required fields

4. **Check for empty/zero values:**
   - `count: 0` or missing `count` may cause empty render
   - `groups: []` (empty array) needs handling

5. **Verify emoji mapping:**
   - Check if object name is in emojiMap
   - Try exact, lowercase, and partial matches manually

6. **Console errors:**
   - Open browser dev tools
   - Look for React rendering errors or undefined property access

---

### 20.12 Introduction Slide ≠ Definitions Slide (CRITICAL)

**Problem:** The introduction slide was written as if it WERE the definitions
slide — it defined vocabulary terms inline, making the definitions slide
redundant. This is the single most common mistake when authoring new node content.

**Example of the mistake:**

Introduction for "Addition":
> "Addition means putting two groups together. The answer is called the sum."

Then the definitions slide:
> **addition** — putting two groups together to find the total
> **sum** — the answer you get when you add

The student heard the definition twice. The introduction stole the definitions
slide's job.

**The correct approach:**

The Introduction slide has ONE job: **motivate the concept and connect to
prior learning.** It asks a question or teases what's coming. It NEVER
defines, names, or formally introduces vocabulary terms.

| Slide | Job | Example |
|-------|-----|---------|
| Introduction | Motivate + connect to prior learning | "You can count up. What happens when you put two groups together?" |
| Definitions | Formally introduce vocabulary terms | "**addition** — putting two groups together" |
| Worked examples | Demonstrate the concept in action | "Let's add 5 + 3. Jump to 5 on the number line..." |

**Test for introduction text:** If you can delete the definitions slide and
the student still knows the vocabulary, your introduction is doing the
definitions slide's job. Rewrite it.

**Correct introduction patterns:**
- "You can count. Now let's look at two numbers — which is bigger?"
- "You can count up. You can break numbers apart. Now let's put groups together."
- "You can compare numbers. Now let's look inside a number."

**Wrong introduction patterns:**
- "Compare means find which is bigger or smaller." ← THIS IS A DEFINITION
- "A numeral is a written symbol for a number." ← THIS IS A DEFINITION
- "The answer is called the sum." ← THIS IS A DEFINITION

---

### 20.13 Grade-Level Vocabulary Constraints

**Problem:** The comparison worked example used "greater than" — a Grade 3
term — in Grade 1 content. The text said "$7$ is greater than $4$" when it
should have said "$7$ is more than $4$".

**Root Cause:** Not consulting `matatag_grade_knowledge.json` for the
grade-appropriate comparison vocabulary. "Greater than" appears only in
Grade 3's `comparison_vocabulary`.

**Prevention:**

1. **Always check grade-level vocabulary** before writing worked example text
2. The two sources of truth:
   - `data/knowledge_graph_g1_3.json` → `cumulative_vocab` at each node
   - `ph/matatag_grade_knowledge.json` → `comparison_vocabulary`, `allowed_question_words`

**Grade 1 comparison language:**
- USE: "more than", "less than", "bigger", "smaller", "same"
- DO NOT USE: "greater than", "less than" (with "greater"), ">", "<", "="

**Grade 2 comparison language:**
- Adds: "greater", "smallest", "largest", "order"
- Still no: ">", "<", "=" symbols

**Grade 3 comparison language:**
- Adds: "greater than", "less than", "equal to", ">", "<", "="

---

### 20.14 Cross-Branch Terms and the Vocabulary System

**Problem:** Basic comparison words like "bigger", "smaller", "same" are
pre-existing student knowledge (children know these before school), but they
were missing from `_cross_branch_terms` in `vocab_annotation.json`. This
caused false constraint violations when the intro system used them.

**How the system works:**

```
vocab_annotation.json → _cross_branch_terms + per-node student_vocab
                ↓
scripts/rebuild_knowledge_graph.py → reads cross_branch_terms from vocab_annotation.json
                ↓
data/knowledge_graph_g1_3.json → cumulative_vocab at each node
```

`cumulative_vocab` at any node = `_cross_branch_terms` + all `student_vocab`
from prior nodes in the same branch.

**Current cross-branch terms (always available to all nodes):**
```json
["number", "equal", "more", "less", "bigger", "smaller", "same",
 "how many", "total", "left", "count", "group"]
```

**When to add new cross-branch terms:**
- The word is everyday language students know before school
- The word is used across multiple branches (NA, MG, DP)
- The word is NOT a mathematical concept that gets formally taught

**After modifying `_cross_branch_terms`:**
```bash
python3 scripts/rebuild_knowledge_graph.py  # recomputes all cumulative_vocab
```

Never edit `knowledge_graph_g1_3.json` by hand — it is generated.

---

### 20.15 Every Competency Needs a Worked Example

**Problem:** The "Counting & Numerals" mini-lesson covered competencies
`_0`, `_1`, `_2` but only had worked examples for `_0` (1-more/1-less) and
`_2` (counting objects). Competency `_1` (read/write numerals) had no
demonstration.

**Prevention:**

When implementing a mini-lesson group, verify coverage:

```
For each competency in the group:
  └─ At least one worked example must address this competency
```

If a competency cannot be naturally demonstrated (e.g., "write numerals"
is a motor skill), create a worked example that demonstrates the CONCEPT
behind the competency (e.g., numeral-to-position correspondence on a
number line).

---

### 20.16 Interest Wrapping Must Be Consistent Within a Mini-Lesson

**Problem:** The "Addition" mini-lesson had three interest-wrapped slides
(groups of objects), then suddenly showed "What is 15 + 0?" with generic
"dots" for the identity property — breaking the thematic consistency.

**Prevention:**

If `interest_ctx` is available:
- ALL object-group slides in the mini-lesson should use it
- The identity property should say "{actor} has {a} {objects}. {actor} gets 0 more."
- The commutative property can use abstract groups (color-coded) since it's
  demonstrating an abstract concept

**Rule:** If the student is "in" an interest theme, don't break them out of
it for individual slides. The only exception is slides that use abstract
visual tools (number line, ten frame, number bonds) where objects don't appear.

---

### 20.17 Don't Pre-Reveal Answers in Worked Examples

**Problem:** The commutative property slide showed the full equation with the
answer on step 1: "$3 + 8 = 11$". Then step 2 showed "$8 + 3 = 11$". The
student saw both answers immediately — no discovery moment.

**Prevention:**

Worked examples should follow the pattern:
```
Step 1: POSE the problem (no answer visible)
Step 2: WORK through it (show the process)
Step 3: REVEAL the answer
```

For the commutative property specifically:
```
Step 1: "Let's add 3 and 8." [show two color groups — no equation yet]
Step 2: "3 + 8 = 11. Now flip: 8 and 3." [reveal first answer, pose second]
Step 3: "8 + 3 = 11. Same answer! The order does not change the sum."
```

The student first sees the groups, then discovers the answer, then sees it
holds when flipped. Never show the punchline on step 1.

---

### 20.18 Definition Quality: Positional Context for Ordinals

**Problem:** Ordinal definitions 4th through 10th were just word forms:
"4th — fourth", "5th — fifth". These don't convey what ordinals mean —
they're just pronunciation guides.

**Prevention:**

When defining a sequence of related terms (ordinals, place values, etc.),
maintain the pattern established by the first entries:

```
GOOD (maintains pattern):
  1st — first — the one at the front
  2nd — second — the one right after 1st
  3rd — third — the one right after 2nd
  4th — fourth — the one right after 3rd
  ...
  10th — tenth — the one right after 9th

BAD (drops pattern):
  1st — first — the one at the front
  2nd — second — the one right after 1st
  3rd — third — the one right after 2nd
  4th — fourth
  5th — fifth
```

If 4th needs context, so does 10th. If 10th doesn't need context, neither
does 2nd. Be consistent.

---

### 20.19 Interest Themes Are Not Grade-Filtered

**Problem (previously):** We initially filtered interest themes by grade_band,
thinking themes like "Competitive Gaming" were inappropriate for Grade 1.
This was wrong — the INTEREST is just contextual wrapping; the CONTENT
difficulty is controlled by the generator.

**The correct approach:**

All 26 interest themes are available to all students. A Grade 1 student who
loves anime should get anime-themed problems — with Grade 1 content:
- "Hiro has 5 cards. He gets 3 more. How many cards now?"

The theme just provides actors and objects. The math is grade-appropriate
regardless of theme. A student's interest should never be filtered based
on their grade — that's patronizing and demotivating.

**Implementation:**
```python
def get_interest_themes(grade: int = None) -> List[Dict]:
    """Return all interest themes. Grade parameter is ignored."""
    # Return ALL themes — do not filter by grade_band
```

**The grade_band field** in `interest_bank.json` is kept for potential future
use (e.g., linguistic complexity in word problems) but is NOT used for
filtering the interest selection dropdown.

---

### 20.20 Every Step Needs a Visual — No Exceptions

**Problem:** Conclusion/answer steps frequently had `"visual_type": None`,
leaving students with just text on critical understanding moments. Examples:

- "One half means 1 out of 2 equal parts." ← No fraction visual shown
- "If there are 3 red and 1 blue in a bag, red is more likely." ← No bag visual
- "The time is 3:00 — 3 o'clock." ← No clock shown

**Why this is harmful:**

1. **Cognitive disconnect:** The visual was shown in step 2, but step 3
   (the punchline) has no visual. The student's eyes move to blank space
   right when they need visual reinforcement.

2. **Lost anchoring:** Early-grade students need the concrete representation
   visible WHILE hearing the abstract statement. "Half means 1 of 2 parts"
   needs the fraction bar visible.

3. **Probability especially:** Abstract concepts like "more likely" are
   MEANINGLESS without the visual context. The statement "red is more likely"
   requires seeing the bag with 3 red and 1 blue.

**The rule:**

> **Every worked example step MUST have a visual. Repeat the visual from the
> previous step if no new visual is needed — but never leave visual_type as None.**

**Pattern:**
```python
# BAD: Conclusion step with no visual
{"text": "One half means 1 out of 2 equal parts.",
 "visual_type": None, "visual_params": None}

# GOOD: Repeat the visual for reinforcement
{"text": "One half means 1 out of 2 equal parts.",
 "visual_type": "FractionBar",
 "visual_params": {"parts": 2, "shaded": 1, "label": "1/2"}}
```

**Visual types that MUST appear on conclusion steps:**

| Concept | Required Visual Type |
|---------|---------------------|
| Fractions | `FractionBar` (showing the shaded parts) |
| Probability | `ProbabilityBag` or `CoinDisplay` |
| Time | `ClockSet` (showing the answer time) |
| Money | `PesoMoney` (showing the coins/bills) |
| Measurement | `LengthCompare`, `RulerDisplay`, `BalanceScale`, etc. |
| Area | `AreaGrid` (with `show_total: true`) |
| Shapes | `ShapeDisplay` (showing the referenced shape) |
| Comparisons | `Comparison` (with both items visible) |

---

### 20.21 No Subjective Language in Introduction Slides

**Problem:** Introduction slides used phrases like:
- "You know pictographs."
- "You know tens and ones."
- "You learned how to measure mass."

These are **subjective assumptions** about student knowledge. They add no
teaching value and can feel invalidating if the student doesn't remember.

**The correct approach:**

Replace "You know X" with a **brief factual summary** of X:

| BAD | GOOD |
|-----|------|
| "You know pictographs." | "Pictographs use pictures to show data." |
| "You know tens and ones." | "Tens and ones show place value." |
| "You know how to measure mass." | "Mass tells how heavy something is." |
| "You know half and quarter." | "Half means 2 equal parts. Quarter means 4." |
| "You know pesos and bills." | "Pesos come in coins and bills." |

**Why the summary is better:**

1. **Not assumptive:** Doesn't claim the student knows something
2. **Actually teaches:** Provides a quick refresher of the concept
3. **Provides context:** Sets up what's coming next
4. **Accessible:** Student who forgot still gets oriented

**Pattern for introduction slides:**

```
1. [Quick factual summary of prior concept] — 1 sentence
2. [Bridge to new concept] — "Now let's..."
3. [Tease what's coming] — optional motivating sentence
```

**Example:**
```
Pictographs use pictures to show data.      ← factual summary
Now let's use bars to show data.            ← bridge
A bar graph makes it easy to compare        ← motivation
numbers at a glance.
```

**Search your generators for these red-flag patterns:**
- `"You know"`
- `"You learned"`
- `"You already"`
- `"Remember that"`
- `"As you know"`

Replace all of them with factual summaries.

---

### 20.22 Critical Visual Types for Specific Concepts

**Problem:** Some concepts REQUIRE specific visual types that were missing
from the intro visual toolkit. The most critical example: **Probability**
had no visual types at all — students saw abstract statements like
"red is more likely" with no visual representation.

**New visual types added for G1-G3:**

| Visual Type | Purpose | Required Params |
|-------------|---------|-----------------|
| `ProbabilityBag` | Colored objects in a bag | `{items: [{color, count}], highlight?, show_counts?}` |
| `CoinDisplay` | Heads/tails coin for probability | `{show_both?, result?}` |

**Visual type requirements by concept:**

| Concept | Required Visual | Why |
|---------|-----------------|-----|
| Probability (bag) | `ProbabilityBag` | Must show actual objects to make "more likely" concrete |
| Probability (coin) | `CoinDisplay` | Must show both outcomes for "equally likely" |
| Fractions (comparison) | `Comparison` with `FractionBar` | Must show both fractions side-by-side |
| Money calculations | `PesoMoney` | Must show actual coins/bills being used |
| Time telling | `ClockSet` | Must show clock face with hands |
| Length comparison | `LengthCompare` | Must show both objects with measurement units |
| Mass comparison | `BalanceScale` | Must show which side is heavier |
| Capacity comparison | `CapacityDisplay` | Must show relative container sizes |
| Symmetry | `SymmetryDisplay` | Must show the axis of symmetry |
| Area | `AreaGrid` | Must show the grid with squares counted |

**When implementing a new concept:**

1. Check if existing visual types can represent it
2. If not, design a new visual type with clear param contract
3. Implement the renderer in `App.jsx` BEFORE generating content
4. Document the params in this section

**Never output a visual_type that has no frontend renderer.**

---

### 20.23 Visual Param Consistency

**Problem:** The same visual type was used with inconsistent params across
different generators, causing some renderers to fail silently.

**Prevention:**

1. **Document param contracts** in Section 20.2 BEFORE using a new format
2. **Use consistent param names** across all generators:
   - `highlight` (not `highlighted`, `mark`, `select`)
   - `show_total` (not `showTotal`, `display_total`)
   - `items` for arrays (not `data`, `values`, `list`)

3. **Required vs optional params** — document clearly:
   ```javascript
   // ProbabilityBag params
   {
     items: [{color, count}],  // REQUIRED: array of {color, count} objects
     highlight?: string,       // OPTIONAL: color to highlight
     show_counts?: boolean     // OPTIONAL: default true
   }
   ```

4. **Test new params with curl** before assuming they work:
   ```bash
   curl -s '...?seed=42' | jq '.mini_lessons[].slides[].steps[]?.visual_params'
   ```
