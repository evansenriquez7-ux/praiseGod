# PG Pipeline Hardening — Implementation Plan

**Audience:** autonomous coding agent working in this repository.
**Goal:** make it structurally impossible for a broken problem generator to ship, by replacing checklist-based self-verification with a machine-enforced harness wired into CI.

Read this entire document before writing any code. Execute the phases **in order**. Each phase has acceptance criteria that must pass before you move to the next phase.

---

## Ground Rules (read first, these override your habits)

1. **You do not get to decide a check passed.** A check passes when the harness exits 0. Prose claims of verification are worthless. Every phase ends with you running a command and pasting its real output into the evidence log (Phase 7).
2. **Never weaken an assertion to make it pass.** If a harness assertion fails, the bug is in the generator/DNA/formatter layer, not the assertion — fix the pipeline. The only permitted reason to change an assertion is a documented error in the ground-truth spec (competency bounds or KG vocab fields), and that change must be called out explicitly in your final report with the node ID and justification.
3. **No graceful fallbacks anywhere in the harness.** If a node is missing bounds, a DNA fails to import, a formatter isn't routable — that is a loud FAIL with a named error, never a skip, warn-and-continue, or default value. Skipping is how bugs hide.
4. **Fixed seeds everywhere.** All harness sampling uses deterministic seeds so failures are reproducible. Print the seed in every failure message.
5. **Do not touch these files except as this plan directs:** `pgen_checklist.md` and other docs (handled separately by DOCS_REMEDIATION.md), and once Phase 1 lands, `validation/_manifest.py` is append-only for you.

---

## Phase 0 — Consolidate duplicated registries (prerequisite)

**Problem:** `_DNA_MODULE_MAP` is copy-pasted in `validate_dna.py`, `validate_compat.py`, `validate_interest.py`, `validate_vocab.py`. `_KNOWN_FORMATTERS` in `validate_compat.py` hand-duplicates the adapter's formatter router. Drift between copies means a validator can silently skip a new DNA — a graceful fallback inside the verification layer.

**Do:**
1. Create `backend/app/practice_gen/validation/_manifest.py` exposing:
   - `DNA_MODULE_MAP: Dict[str, str]` — the single canonical map (move it here).
   - `KNOWN_FORMATTERS: Set[str]` — **derived programmatically** from the adapter's formatter router table (import it; do not retype the names). If the router table isn't importable without side effects, refactor the router table into a module-level constant in `adapter.py` first.
   - `load_dna(concept: str) -> DNA` — the shared loader. It must **raise** (not return None) on import failure or missing DNA instance.
2. Rewrite all four validators to import from `_manifest.py`. Delete the local copies.
3. Add a check inside `_manifest.py` (executed at import) asserting `set(DNA_MODULE_MAP.keys()) == set(COMPATIBILITY.keys())`. Mismatch → raise at import time.

**Accept when:** `python -m backend.app.practice_gen.validation.validate_dna`, `validate_compat`, `validate_interest`, `validate_vocab` all still run, and `grep -rn "_DNA_MODULE_MAP" backend/app/practice_gen/validation/` shows only `_manifest.py`.

---## Phase 1 — Build `validate_matrix.py` (the core harness)

Create `backend/app/practice_gen/validation/validate_matrix.py`. This is the single most important artifact in this plan. It executes the **full behavioral matrix** for every node through the *real* pipeline path (the same code path as `/api/matatag/lab/v2/generate` → `pipeline.run` → adapter → formatter), never a simplified proxy.

For **every node** in `knowledge_graph_g1_3.json` (fail loudly if a node has no `NODE_TO_DNA` entry — do not skip):

### 1A. Scalar boundary exactness (checklist §1 "Strict Scalar Mapping")
For each continuous difficulty dimension of each of the node's DNAs:
- Resolve the node's ground-truth bounds via `registry.get_node_competency_bounds(node_id)` (fall back to the MATATAG per-grade ceiling **only** where the registry itself defines that fallback — the harness must use the same resolution function the serving path uses, never its own copy).
- Generate ≥ 30 problems at scalar exactly `0.0` and ≥ 30 at exactly `1.0` (distinct seeds).
- Assert: at 0.0, the governed parameter's **maximum observed value equals the competency minimum window ceiling** per the dimension's windowing rules in `DIFFICULTY_DIMENSIONS.md`; at 1.0, at least one sample **reaches** the competency maximum region and **no sample exceeds** the competency maximum. (Exceeding the max at 1.0 is the classic leaky window.)

### 1B. Window containment sweep (checklist §1 "Functional Integrity")
- Sweep scalars `{0.0, 0.25, 0.5, 0.75, 1.0}` × ≥ 20 seeds per scalar, per dimension.
- Assert every generated parameter lands inside the window that scalar defines, and that windows are **monotonic**: the parameter distribution at scalar s+Δ must not have a lower ceiling than at s.
- Discrete dimensions: iterate every option value; assert the generated problem actually reflects the selected option (e.g. `skip_interval=5` → consecutive terms differ by 5).

### 1C. Variant × formatter execution matrix (checklist §2 & §3 "Functional Integrity")
- Enumerate every `(variant_name, variant_value)` from `VARIANTS_BY_DNA`, filtered per formatter through `get_supported_variants(dna, formatter)` — i.e. exactly the combinations the Lab UI can enable.
- For every supported `(dna, formatter, variant assignment)` combination × ≥ 5 seeds: run the full pipeline and assert:
  - no exception raised;
  - `question_text` is non-empty;
  - a `correct_answer` exists and is non-null;
  - MCQ-family output: exactly the expected option count, correct answer present among options, options mutually distinct, no option is empty/`None`/`"undefined"`;
  - visual formatters: the visual payload validates against `VisualSchemaRegistry` for that formatter — **strict validation, unknown/missing fields are errors**;
  - the formatter actually used matches the formatter requested (no silent rerouting).
- Additionally assert the **reverse**: for combinations *excluded* by `FORMATTER_VARIANT_SUPPORT`, requesting them raises a clear error rather than silently substituting (this checks the fail-fast contract at the pipeline boundary; mirror the 4xx behavior the router already implements).

### 1D. Vocabulary lint on FORMATTED output (checklist §4 "Vocabulary Gating")
- Reuse `validate_vocab.validate_vocab_constraints` / `validate_concept_constraints`, but run them against the **final formatted text**: question text *plus* cloze sentence, instruction strings, and every MCQ option label — not just the raw `QuestionContext`.
- Run for every node (not 5 spot-check nodes), every DNA of the node (not just the first), across the 1C matrix samples (reuse those generations; don't regenerate).
- `NOT_YET_KNOWN` hit = hard FAIL.

### 1E. Answer-key integrity
- For formula DNAs: independently recompute the answer from `ctx.values` + `answer_formula` and assert it equals the served `correct_answer` **after** formatting (catches formatter-layer answer corruption).
- Assert interest-theme invariance on the formatted output for ≥ 3 themes (extend the existing `validate_interest` logic to post-formatter text/answers).

### Output contract
- CLI: `python -m backend.app.practice_gen.validation.validate_matrix [--node NODE_ID] [--fail-fast]`.
- Prints a per-node PASS/FAIL table and writes a machine-readable report to `validation_reports/matrix_report.json` (node → check → failures, each failure carrying `dna`, `formatter`, `variants`, `scalar`, `seed`).
- Exit 0 only on zero failures. Any skipped combination is a failure.

**Accept when:** the harness runs to completion over all nodes. Do **not** expect it to pass on first run — it will surface real bugs. Log every failure it finds in the evidence log, then fix pipeline bugs until it exits 0. Every pipeline fix must be listed in the final report with the failing assertion that motivated it.

---

## Phase 2 — Wire feasibility + all validators into one gate

1. `validate_dna.py`'s `__main__` currently never calls `validate_difficulty_feasibility`. Fix: run it for every DNA × every grade present in its `param_bounds`, and include failures in the exit code.
2. Create `backend/app/practice_gen/validation/run_all.py` that runs, in order: `validate_dna` → `validate_compat` → `validate_interest` → `validate_vocab` (full-node mode) → `validate_matrix`. First non-zero exit aborts with that exit code. No flag may exist that skips a validator.

**Accept when:** `python -m backend.app.practice_gen.validation.run_all` exits 0 on the fixed pipeline.

---

## Phase 3 — CI enforcement

1. Add `.github/workflows/validate-pgen.yml`:
   - Triggers: every PR and every push touching `backend/**` or `data/**`.
   - Steps: checkout → set up Python (match the backend Dockerfile's version) → install backend deps → `python -m backend.app.practice_gen.validation.run_all`.
   - No `|| true`. No `continue-on-error`. (The hosting workflow's `|| true` pattern is explicitly **not** acceptable here.)
   - Upload `validation_reports/matrix_report.json` as a workflow artifact on failure.
2. Modify `deploy-backend.yml` so deployment **requires** the validation job to succeed (job-level `needs:` or make validation a job inside the deploy workflow that gates the build step).

**Accept when:** a deliberately broken commit (see Phase 4) fails CI and blocks deploy; reverting it goes green.

---

## Phase 4 — Mutation-test the harness (verify the verifier)

Prove the harness catches bugs by planting them. For each mutation below: apply it on a throwaway branch, run `run_all`, **assert it fails with a message pointing at the planted bug**, then revert. Record each mutation → detection in the evidence log.

1. **Leaky window:** in one formula DNA, widen the sampled range at scalar 1.0 beyond the competency max (e.g. `hi + 10`). Must be caught by 1A/1B.
2. **Boundary off-by-one:** make scalar 1.0 map to `max - 1`. Must be caught by 1A (max never reached).
3. **Broken formatter combo:** make one formatter raise for one specific variant value it claims to support. Must be caught by 1C.
4. **Answer corruption:** in one formatter, off-by-one the correct answer's option value. Must be caught by 1E.
5. **Vocab leak:** inject a term from a node's `NOT_YET_KNOWN` list into that DNA's template text. Must be caught by 1D.
6. **Silent substitution:** make the adapter silently reroute an unsupported variant/formatter combo to a supported one instead of raising. Must be caught by 1C's reverse check.
7. **Registry drift:** add a fake DNA concept to `COMPATIBILITY` without a module. Must be caught at `_manifest.py` import.

**Accept when:** 7/7 mutations detected. If any mutation survives, the harness has a hole — fix the harness (this is the one phase where editing assertions is the point), then rerun **all 7**.

---

## Phase 5 — Strict response schema; kill frontend fallbacks

**Problem:** `App.jsx` maps the v2 response through a fallback cascade (`format_data.mcq_options` → `format_data.options` → `data.options` array → object → `[]`; difficulty defaults to 0.5). This renders *something* even when a formatter emits the wrong shape, hiding output-contract bugs.

1. Define one strict Pydantic response model for `/api/matatag/lab/v2/generate` (and the portal serving endpoint) — exact option shape, required fields, `extra="forbid"`. The harness (1C) validates every generated problem against this same model.
2. Frontend: replace the fallback cascade with a single accessor for the canonical shape. If the shape is wrong, surface a visible error state ("Malformed problem payload — see console"), never an empty render. Remove the `0.5` difficulty default; missing axes is an error state.
3. Remove the `open("/tmp/last_request.json", "w")` debug write in `matatag_lab_v2_generate`.

**Accept when:** lab preview and student portal render correctly against the strict schema; a hand-crafted malformed payload produces the visible error state, not a blank/partial render.

---

## Phase 6 — LLM-path audit

Determine whether any **live serving path** for practice problems routes text through `subagents.py` (LLM narrative generation) as opposed to the template-based `interest_bank.json` path.

- If **no live path** uses the LLM for practice_gen output: state this in the report with the call-graph evidence (grep results / route trace).
- If **any** does: deterministic CI cannot prove its output safe. Implement a **runtime gate**: run the 1D vocab lint on the LLM output at serving time; on violation, reject and regenerate (bounded retries), then fail loudly. Add a harness check that the gate exists and rejects a seeded violation (mock the LLM to return a known-bad string).

**Accept when:** the question is answered with evidence, and if applicable the runtime gate is implemented and mutation-tested.

---

## Phase 7 — Evidence log (your definition of done)

Maintain `validation_reports/HARDENING_EVIDENCE.md` as you go. Required contents:
1. Per phase: the exact commands run and their **verbatim** final output (pass/fail summary lines).
2. Every pipeline bug found by the harness in Phase 1: node, assertion, root cause, fix commit.
3. Phase 4 mutation table: mutation → detecting assertion → verbatim failure message.
4. Any ground-truth spec corrections made under Ground Rule 2, with justification.
5. Phase 6 conclusion with evidence.

A phase without verbatim command output in this log is **not complete**, regardless of what the code looks like.

---

## Explicit non-goals
- Do not redesign difficulty dimensions, variants, or formatters. This plan verifies existing contracts; it does not change pedagogy.
- Do not add new formatters/variants "while you're in there."
- Do not modify `pgen_checklist.md` or other docs — that is handled by `doc_rem.md`.