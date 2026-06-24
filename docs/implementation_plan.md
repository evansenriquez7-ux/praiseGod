# Architectural Refactoring Implementation Plan

Based on the review of `frontend/src/App.jsx` (5800+ lines) and `backend/app/main.py` (3200+ lines), as well as insights from `GRAPH_REPORT.md`, the architecture exhibits a "monolithic bloat" pattern. The following is a prioritized, phased implementation plan designed to incrementally refactor the codebase to ensure zero downtime while directly addressing the identified bottlenecks.

## Phase 1: Immediate Priority - Data Contracts & Normalization (High Impact)
**Goal:** Bridge the gap between DNA generation and visual formatters by eliminating manual adapter logic and strictly typing the pipeline.
*Rationale: `QuestionContext` and `FormattedProblem` are "God Nodes" heavily coupled via inferred edges. `adapter.py` exists as a hack due to loose contracts.*

1. **Strict Pydantic Output Schemas (`practice_gen/dna/`)**
   - Normalize the output of all DNA generators to a strict `QuestionContext` Pydantic schema.
   - Ensure the DNA layer reliably outputs data that directly fulfills the formatter requirements *before* the pipeline continues.
   
2. **Deprecate & Remove Adapter "Fixers" (`practice_gen/adapter.py`)**
   - Eliminate repetitive error-correction functions like `_fix_context_answer`, `_fix_distractors`, and `_fix_question_text`.
   - The pipeline must "fail fast" on invalid DNA rather than silently hacking fixes.

## Phase 2: Structural Improvements via Graph Insights (Medium Risk)
**Goal:** Group fragmented, low-cohesion communities into meaningful bounded contexts and introduce a Bridge Layer to reduce coupling in `main.py`.

1. **Create a Bridge Layer (`PracticeOrchestrator`)**
   - Instead of `main.py` calling `pipeline.run` directly, introduce a `PracticeOrchestrator` service.
   - Wrap the `QuestionContext` and use dependency injection to select the appropriate DNA and Formatter based on the student's profile, decoupling `main.py` from the generation logic.

2. **Refactor Low-Cohesion Communities into `DomainService` Packages**
   - Address Communities 2 (Curriculum Pitfalls), 3 (DNA/Hint wrapping), and 5 (ErrorPattern/VocabGated/Math fragments).
   - Group these into a single `DomainService` package.
   - Introduce a `LearningDomain` base class that encapsulates the DNA logic, curriculum constraints, and error-handling patterns for specific subject areas.

## Phase 3: Frontend Efficiency & State Management (Medium Risk)
**Goal:** Dismantle the `App.jsx` "God Component" (5800+ lines) and optimize the React render cycle.

1. **State Management Migration (`frontend/src/store/`)**
   - Introduce **Zustand** to manage global state arrays and heavily-mutated states (e.g., coordinate/layout-specific state for `reactflow` and `dnd-kit`).
   - This prevents the React render cycle from re-calculating the entire `App.jsx` tree on every mouse drag.

2. **Componentize Views (`frontend/src/views/`)**
   - Extract major view blocks from `App.jsx` into separate components (`LoginView.jsx`, `PracticeView.jsx`, `ParentDashboard.jsx`).
   - Reduce `App.jsx` to primarily handling routing, context providers, and high-level layout wrappers.

3. **API Client & Utility Functions**
   - Extract `window.fetch` overrides and custom base URL logic into `frontend/src/api/apiClient.js`.
   - Extract `renderMath(text)` and `renderVisualInner(...)` into dedicated utility files.

## Phase 4: Performance & Scaling - Backend Efficiency (High Risk)
**Goal:** Remove local I/O and memory bottlenecks to enable horizontal scaling and decompose `main.py`.

1. **In-Memory Cache to Redis**
   - Move global dictionaries (`QUESTION_CACHE`, `MATATAG_SKELETON_CACHE`, `ELA_SKELETON_CACHE`) from local RAM to **Redis**.
   - This is a prerequisite for scaling: it resolves the "memory island" issue and allows multiple FastAPI instances to share the same cache pool seamlessly.

2. **Backend Decomposition (`backend/app/services/` & `backend/app/routes/`)**
   - Move business logic (scoring, curriculum advancement) into domain-specific service files.
   - Utilize `FastAPI APIRouter` to compartmentalize endpoints (`routes/parent.py`, `routes/practice.py`, `routes/student.py`).
   - Update `main.py` to simply construct the `FastAPI` app, handle CORS middleware, and call `app.include_router(...)`.

3. **Telemetry & File-Based Logging Migration**
   - Move telemetry and history tracking from `scratch/gen_problems.jsonl` to an asynchronous queue (e.g., Redis Streams) and bulk-flush to PostgreSQL.

## Phase 5: CI/CD & Verification
- Establish standard unit and integration tests for the new `PracticeOrchestrator`, the strict `QuestionContext` schema, and the decoupled `DomainService` packages.
- Deploy changes incrementally (e.g., merge Phase 1 to live, verify; merge Phase 2 to live, verify) to ensure no regressions.
