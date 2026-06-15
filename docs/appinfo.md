# CCMed — Adaptive K-12 Mastery Engine

## Core Purpose
A local-first, closed-loop software engine designed to progress K-12 students to 99th-percentile standardized test scores (NWEA MAP / Digital SAT) in Math and Verbal Competency (ELA) with maximum time efficiency. It replaces static curriculum with infinite, AI-generated, psychometrically targeted practice problems.

---

## Core Features

### 1. Single-Pass Onboarding (Binary Search Placement)
Runs a tree-based binary search across academic milestones. Correct → leap forward; incorrect → drop back. Pinpoints the student's exact "knowledge frontier" in under 15 questions per subject. Eliminates multi-day diagnostic testing.

### 2. Stealth Continuous Assessment
Every practice problem doubles as a data point. The system continuously maps and updates the student's mastery graph without the student realizing they are being formally evaluated. Eliminates test anxiety.

### 3. Isomorphic Just-in-Time (JIT) Generation
Python backend creates a deterministic mathematical/verbal skeleton (the invariant core). A Gemini CLI subagent wraps that skeleton in a narrative themed around the student's hobbies (e.g., racing, space, gaming) at their target reading level. Produces infinite, plagiarism-proof questions.

### 4. Deterministic Validation Pipeline
After Gemini generates a problem narrative, the backend validates it deterministically:
- **Math**: SymPy re-solves the problem independently and verifies the answer key matches.
- **Reading/Writing (V2+)**: Rule-based checks verify answer option consistency, grammar correctness, and passage-question alignment.
- **Rejection loop**: If validation fails, the problem is silently discarded and regenerated (max 3 retries before falling back to the pre-generated buffer). The student never sees an invalid problem.

### 5. Trap-Aware Evaluation & The Socratic Split
Submissions are graded deterministically (not by the LLM). If a student picks an engineered "trap option" (e.g., True but Irrelevant in Reading, Sign Change in Math), the UI locks progress and splits the screen for Socratic tutoring.

**Socratic Tutor modes**:
- **Auto-trigger**: Activates after any incorrect answer with guidance targeted at the specific misconception.
- **On-demand**: A persistent "Ask Tutor" button allows multi-turn conversational Socratic sessions with Gemini at any time.

### 6. Browser-Native Telemetry Defense ("The Waste Meter")
JavaScript window listeners detect distraction and burnout:
- **Tab Switching**: Pauses the sprint if the browser tab loses focus.
- **Inactivity**: Flags if a student idles for over 120 seconds.
- **Click-Spamming**: Locks the interface for 30 seconds on rapid answer clicks.
- **Time-vs-Difficulty Analysis**: Flags answers submitted too quickly relative to difficulty as probable guessing.
- **Answer Pattern Detection**: Detects degenerate patterns (e.g., always selecting the same letter) and triggers a re-engagement prompt.
- **Must have option to be toggled on/off in parent console

### 7. Spaced Repetition Memory Engine
Calculates forgetting curves per topic. Once mastered, sets an expiration timer. When expired, silently slipstreams a review question into the daily queue to verify retention.

### 8. Adaptive Difficulty Pacing (Elo Rating System)
Both the student and each question maintain an Elo-like difficulty rating that updates after every interaction. Provides smoother difficulty curves than discrete grade-level jumps. The Elo delta feeds into stealth assessment (Feature 2) to refine the mastery graph.

### 9. Worked Examples & Interleaving
- **Worked Example Effect**: For new or struggling topics, alternates between a fully-solved worked example and a similar problem for the student to solve. Reduces cognitive load during skill acquisition.
- **Interleaving**: Problem types are mixed across recently-active topics within each session (e.g., fractions + geometry + algebra) rather than blocked by single topic. Harder in the moment but produces significantly better long-term retention.

### 10. Scaffolded Problem Decomposition
When a student fails 2+ consecutive problems on the same skill node, the system decomposes the next problem into sequential sub-steps (e.g., a multi-step equation → "isolate the variable" as its own micro-problem, then the next step, building back up). This is structural (built into the generation pipeline), distinct from the conversational Socratic tutor.

---

## Multi-Student & Multi-Device Support

### Profile Management
- Each student has their own profile with separate login (name + PIN)
- Each profile maintains completely independent data (Elo ratings, mastery graph, spaced repetition queues, telemetry)
- UI adapts to each student's age, interests, and language preference on login

### Authentication
- **Student login**: Name + numeric PIN (age-appropriate, low-friction)
- **Parent/guardian access**: Separate, stronger alphanumeric password for profile management, data export, and system configuration. For now during this testing phase, disable the parent password, but will enable later during launch. 
- **No external accounts**: All authentication is local — no email, no OAuth, no cloud

---

## Localization

### Language Support
Fully bilingual: **English** (default) and **Tagalog** (Filipino).

All UI text, question stems, answer choices, and Socratic tutor dialogue are available in both languages. Language selection is per student profile and switchable at any time. AI-generated content adheres strictly to the active language setting.

---

## Data Ingredients & Targets

### Target Performance Metrics (The 99th Percentile Goal)
- **K-8 (NWEA MAP)**: Targets RIT scores of 245–260+ in Math, 230–242+ in Reading, 232–245+ in Language.
  - **Source**: 2025 MAP Growth Norms Technical Manual (Appendix B) — publicly available from NWEA.
- **9-12 (Digital SAT)**: Targets the 700–800 score band per section.
  - **Source**: College Board's annual *Total Group SAT Suite of Assessments Report* — publicly available.
  - **Scale**: 400–1600 total, 200–800 per section.

### Ingested Knowledge Graphs

The knowledge graph is constructed by merging multiple freely available sources into a unified prerequisite graph:

| Source | What It Provides | Format | Access |
|---|---|---|---|
| **Learning Commons Graph** (CZI / 1EdTech CASE) | Complete K-12 learning components, standards, learning progressions, prerequisite relationships | JSONL, API | [learningcommons.org](https://learningcommons.org) — free API registration |
| **K12-KGraph** | Dense prerequisite trees for Math & Science concepts, skills, exercises, chapters | HuggingFace dataset | [huggingface.co/datasets/lhpku20010120/K12-KGraph](https://huggingface.co/datasets/lhpku20010120/K12-KGraph) — free |
| **Common Standards Project** | All 50-state academic standards with GUIDs, hierarchical relationships | REST API, JSON dumps | [commonstandardsproject.com](http://commonstandardsproject.com) — free API |
| **Achieve the Core Coherence Map** | Common Core Math prerequisite → successor standard mappings (visual graph) | Web tool (scrapeable) | [achievethecore.org/coherence-map](https://achievethecore.org/coherence-map/) — free |
| **Achieve the Core / HuggingFace** | CCSS Math standards with "progress to/from" connections | HuggingFace dataset | [huggingface.co/datasets/allenai/achieve-the-core](https://huggingface.co/datasets/allenai/achieve-the-core) — free |
| **SirFizX/standards-data** | JSON representations of Common Core standards (CEDS-aligned schema) | GitHub repo (JSON) | [github.com/SirFizX/standards-data](https://github.com/SirFizX/standards-data) — free |

> **Build Strategy**: Merge these sources into a single unified graph stored in PostgreSQL. Learning Commons provides the canonical node structure; K12-KGraph supplies dense prerequisite edges; Common Standards Project and Achieve the Core fill gaps and provide cross-references. A build script handles deduplication, edge reconciliation, and schema normalization.

### Subject Scope Strategy
- **V1**: Math only (full K-12 scope) — deterministic evaluation is most straightforward, SymPy integration is cleanest, and the knowledge graph is most well-defined.
- **V2+**: Reading and Writing expansion. Architecture is designed from Day 1 to support multi-subject expansion (subject-agnostic interfaces, pluggable evaluators, modular knowledge graph loaders).

---

## Technical Architecture Stack

### Deployment Model
- **Central server**: One device on the home network runs the full CCMed stack — FastAPI backend, PostgreSQL (canonical data store), and serves the web UI. This device is also a client (students can use the app directly on it).
- **Client devices**: Android tablets (one per child) run a lightweight local client with offline caching (SQLite).
- **Access**: Any device on the home Wi-Fi accesses the app via the central server's LAN address (browser) or via native APK (Capacitor wrapper, connects to central server, caches locally).
- **Sync model**: On each knowledge graph node completion → save locally → push to central server over LAN. If offline, queue locally and sync on reconnect. Central server is authoritative; local changes applied as patches with timestamp ordering.
- **Recovery**: If a tablet is lost/broken/reset, full student history is restored from the central server.
- **No cloud dependency**: Internet required only for Gemini CLI API calls.

### Intelligence Engine — Gemini CLI Subagents. In the future, this app must be compatible for connection with any AI provider with an agent llm CLI

The FastAPI backend orchestrates specialized Gemini CLI subagent instances, each with its own system prompt, toolset, and output schema:

| Subagent | Role | Trigger | Output Schema |
|---|---|---|---|
| **Problem Narrator** | Wraps deterministic math skeletons in student-interest-themed narratives at target reading level | JIT generation pipeline | `{stem, options[], correct_key, narrative_metadata}` |
| **Socratic Tutor** | Multi-turn conversational tutor triggered by incorrect answers or on-demand | Wrong answer / student request | Streaming text (multi-turn chat) |
| **Trap Analyzer** | Generates plausible distractor options engineered around common misconceptions | Problem generation pipeline | `{distractors[], trap_type[], misconception_tags[]}` |
| **Worked Example Author** | Produces step-by-step worked solutions for new/struggling topics | Scaffolding engine | `{steps[], explanations[], visual_hints[]}` |
| **Translator** | Translates all student-facing content to Tagalog when language preference is set | Any content generation | Translated text preserving structure |

**Orchestrator behavior**:
- Backend decides which subagent to invoke based on pipeline stage
- Each call includes structured system instructions, student context (age, interests, language, current node), and a JSON output schema
- Responses validated deterministically before reaching the student (see Feature 4)
- All subagent calls are logged for debugging and prompt refinement

### Data Tier
- **Central server — PostgreSQL (canonical store)**:
  - Students, profiles, language preferences, interest tags
  - Knowledge graph nodes, edges, prerequisite mappings
  - Mastery state, Elo ratings, forgetting curves
  - Session telemetry (time-on-task, answer patterns, distraction events)
  - Problem buffer cache
  - Worked example templates and scaffolding state
- **Local devices — SQLite (offline cache)**:
  - Mirrors the active student's data for zero-latency reads/writes
  - Queues unsynced changes locally when central server is unreachable

### Backend Framework
- **FastAPI (Python)**
  - Deterministic math evaluation and problem validation via **SymPy**
  - JIT problem skeleton generation with validation pipeline
  - Gemini CLI subagent orchestration (subprocess calls with structured I/O)
  - Queue management, spaced repetition scheduling, and interleaving logic
  - Elo rating computation
  - Scaffolded decomposition engine
  - LAN sync API endpoints
  - here.now claimed address: https://mellow-mirage-jhc3.here.now/
  - Tailscale funnel: https://enrichmentcaps-mac-mini.tailf77f05.ts.net/api 

### Frontend UI
- **Vite + React**
  - Distraction-free, responsive web workspace optimized for tablet deployment over home Wi-Fi
  - Bilingual UI (English / Tagalog) with runtime language switching
  - Multi-student profile switching with PIN login
  - Worked example presentation mode
  - Socratic tutor split-screen with multi-turn chat
  - Telemetry defense UI (pause/lock overlays)
  - **Android APK**: Packaged via Capacitor for native Android deployment

---

## Deferred Features (V2+)

The following features are designed into the architecture but not implemented in V1:

- **Sprint Mode & Gamification**: Timed micro-sessions, streak/XP system, "boss fight" review rounds
- **AI-Generated Skill Games**: Gemini-generated mini-games that reinforce skills from current knowledge graph position (with a Game Designer subagent)
- **Comprehensive Analytics Dashboard**: Mastery map visualization, score trajectory, session analytics, skill breakdowns, data export (CSV/JSON)
- **Offline-First Problem Buffer**: Rolling pre-generated buffer of 20-30 problems, predictive pre-generation for likely-next nodes
- **Accessibility**: WCAG 2.1 AA, dyslexia-friendly fonts, color-blind palettes, screen reader support
- **Privacy & Compliance documentation**: COPPA compliance notes, data sovereignty policy, Gemini API data handling policy

---

## Engineering Standards & Workflow

### 1. Research-Driven Node Implementation
Whenever knowledge graph nodes occur without specific implementation details or pedagogical examples for their respective grade level, the developer must:
- Search for the primary source of that node (CCSS, Learning Commons, etc.).
- Identify specific research-backed details, assessment rubrics, or sample problems.
- Document these findings in an organized manner within the `data/research/` directory.
- Use these research-backed findings to build deterministic SymPy generators, ensuring the educational validity of the system.
