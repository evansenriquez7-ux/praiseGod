# Architectural Refactoring Implementation Plan

Based on the review of `frontend/src/App.jsx` (6000+ lines) and `backend/app/main.py` (3500+ lines), the recommendations provided are **highly valid** and align with modern scaling best practices. Below is a structured, phased implementation plan designed to incrementally update the codebase while ensuring zero downtime and continuous functionality on the live site.

## Phase 1: Frontend Decomposition (Low Risk)
**Goal:** Dismantle the `App.jsx` "God Component" and organize the frontend into a modular React architecture.

1. **API Client & Interceptors (`frontend/src/api/apiClient.js`)**
   - Move the custom `DEFAULT_API_BASE` computation, LAN/Tunnel detection, and `API_BASE` resolution out of `App.jsx`.
   - Migrate the `window.fetch` override into a dedicated fetch wrapper or Axios instance that automatically appends the required headers (`Bypass-Tunnel-Reminder`, `ngrok-skip-browser-warning`).

2. **Utility Functions (`frontend/src/utils/`)**
   - Extract `renderMath(text)` into `frontend/src/utils/mathUtils.js`.
   - Extract `renderVisualInner(...)` into `frontend/src/utils/renderUtils.jsx`.

3. **State Management Migration (`frontend/src/store/`)**
   - Introduce **Zustand** (recommended for simplicity) or the **React Context API** to manage global state arrays (e.g., `students`, `selectedStudent`, telemetry tracking variables like `tabSwitchCount` and `idleSeconds`).
   - Leave local UI states (like modal visibility) inside their respective components.

4. **Componentize Views (`frontend/src/views/`)**
   - Extract major view blocks from `App.jsx` into separate components:
     - `LoginView.jsx`
     - `PracticeView.jsx` (can be further split into `SubjectSelection`, `MathTrack`, `MatatagTrack`)
     - `ParentDashboard.jsx`
   - `App.jsx` will be reduced to primarily handling routing, context providers, and high-level layout wrappers.

## Phase 2: Backend Decomposition (Medium Risk)
**Goal:** Refactor the bloated `main.py` into a standard, modular FastAPI structure.

1. **Services Layer (`backend/app/services/`)**
   - Move `update_elo`, `validate_math_answer`, `check_and_advance_subject_frontier`, and `get_clean_node_title` into domain-specific service files (e.g., `services/scoring.py`, `services/curriculum.py`).

2. **API Routing (`backend/app/routes/`)**
   - Utilize `FastAPI APIRouter` to compartmentalize endpoints:
     - `routes/parent.py`: Migrating endpoints like `/api/parent/login`, `/api/parent/config`, `/api/parent/analytics/{student_id}`.
     - `routes/practice.py`: Migrating core generation, batching, and submission routes.
     - `routes/student.py`: Migrating student profiles, authentication, and telemetry endpoints.
   - Update `main.py` to simply construct the `FastAPI` app, handle CORS middleware, and call `app.include_router(...)` for each route module.

## Phase 3: Pipeline Normalization (Medium Risk)
**Goal:** Bridge the gap between DNA generation and visual formatters by eliminating manual adapter logic.

1. **Strict Output Schemas (`practice_gen/dna/`)**
   - Normalize the output of all DNA generators to a strict `QuestionContext` schema.
   - Ensure the DNA layer reliably outputs data that directly fulfills the formatter requirements.

2. **Remove Adapter "Fixers" (`practice_gen/adapter.py`)**
   - With strongly-typed standard inputs, eliminate repetitive error-correction functions like `_fix_context_answer`, `_fix_distractors`, and `_fix_question_text` from `adapter.py`.
   - Result: A cleaner, more predictable pipeline that fails fast on invalid DNA rather than silently hacking fixes.

## Phase 4: Cache & Telemetry Bottleneck Resolution (High Risk)
**Goal:** Remove local I/O and memory bottlenecks to enable horizontal scaling.

1. **Telemetry & File-Based Logging Migration**
   - *Current State:* `_save_practice_question` appends to `scratch/gen_problems.jsonl`.
   - *Action:* Move telemetry and history tracking to an asynchronous queue (e.g., Redis Streams) and bulk-flush to a PostgreSQL table (e.g., `PracticeHistory`). 
   - *Transition:* Temporarily write to both the file and the async queue (Dual-Write). Once verified, phase out the `.jsonl` file.

2. **In-Memory Cache to Redis**
   - *Current State:* Global dictionaries (`QUESTION_CACHE`, `MATATAG_SKELETON_CACHE`, `ELA_SKELETON_CACHE`) live in RAM.
   - *Action:* Provision a Redis instance. Replace dictionary lookups with a centralized distributed cache using Redis `GET`/`SET` commands.
   - *Impact:* Allows multiple FastAPI server instances to share the same cache pool seamlessly, supporting scaling to billions of users.

## Phase 5: CI/CD & Verification
- Establish standard unit and integration tests for the new `apiClient`, refactored FastAPI `routes`, and the strict `QuestionContext` schema.
- Deploy changes incrementally (e.g., merge Phase 1 to live, verify; merge Phase 2 to live, verify).
