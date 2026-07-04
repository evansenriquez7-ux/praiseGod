# Generator Testing Strategy

> **"Praise God" is your catchphrase.** Use it as a celebration when a node
> passes the audit or a category drops to zero, not as decorative noise.

## What this document is

The strategy for catching practice-problem-generator (PG) bugs has **three
components**: a fail-fast pipeline, an exhaustive checklist auditor, and a
parallelized test runner. This document is the operating manual for all three.

`docs/pgen_checklist.md` is the checklist the auditor enforces — read it before
fixing any finding. This file tells you how to run the audit, how to read its
output, and which traps to avoid.

## The three components

### 1. Fail-fast PG pipeline

Every DNA, generator, and formatter in `backend/app/practice_gen/` must surface
checklist-violating problems as an **exception**, never as a silently-degraded
problem (see `pgen_checklist.md` §6).

- `PracticeOrchestrator.generate_problem()` (`backend/app/services/orchestrator.py`)
  lets any `RuntimeError`/`ValueError` from the DNA, formatter, or visual layer
  propagate. It does not catch and return a default.
- DNAs that cannot produce a non-degenerate problem raise `RuntimeError` with a
  descriptive message — canonical pattern at
  `backend/app/practice_gen/dna/na/subtraction.py:228-253`.
- Formatters that cannot build `len(distractors) >= 3` raise `ValueError` rather
  than padding with placeholders. Candidate-pool rules that prevent this in
  normal profiles live in `backend/app/practice_gen/generators/_operand_guard.py`.

**Rule:** when fixing a generator bug, do not add a "graceful default" that
returns a near-empty problem for bad inputs. **Raise.** If a bad profile is
reaching the DNA at all, the bug is that the orchestrator failed to pre-filter
it — fix the orchestrator, not the DNA's behavior.

### 2. The exhaustive checklist auditor

`tests/exhaustive_checklist_auditor.py` is the source of truth for
"does this generator follow `docs/pgen_checklist.md`?". It enumerates **every
(node, profile, formatter) combination** the UI is allowed to send and checks
the output against the checklist rules.

Key design points:

- **Profile builder is mirrored from the orchestrator.** It uses
  `build_test_profiles()`, `formatter_supports_profile()`, and
  `_profile_violates_numeric_limit()` so it never requests a profile the
  orchestrator would reject. A reported violation is therefore a real bug, not a
  "the auditor asked for something invalid" false positive. (This mirror is a
  contract — see Trap 3.)
- **Per-DNA×formatter compatibility is mirrored from `FORMATTER_VARIANT_SUPPORT`**
  (in `compatibility.py`), not recomputed. Combinations the orchestrator rejects
  at runtime (`orchestrator.py:140-148`) are not tested.
- **Per-formatter numeric limits** via `FORMATTER_NUMERIC_LIMITS` +
  `_profile_violates_numeric_limit()`: a profile whose mapped value exceeds a
  formatter's `max_val` is filtered before generation (e.g. `emoji_pictorial`'s
  `max_val=100` blocks a profile that would map to 1000).
- **Strict scalar endpoint check** uses `get_node_competency_bounds()` (the range
  the orchestrator actually respects) and tolerates **±1 rounding** at
  `scalar in {0.0, 1.0}` because the log mapping is lossy at the boundary.
  Anything beyond ±1 is a real violation.
- **`dna_name` annotation** (`FormattedProblem.dna_name`, set by the orchestrator
  after DNA selection) is what enables per-DNA content checks like the Fractions
  override. **Whenever you add a new DNA, set `problem.dna_name` in its
  generator** or those checks can't run.
- **Two output files** at the workspace root:
  - `checklist_audit_report.json` — `{node_id: [error_messages]}`
  - `repro_crashes.json` — `[{node_id, seed, formatter, difficulty_profile,
    error_message}, …]`, every crash the audit can deterministically re-trigger.
    This is the bug queue.

  Both files are **overwritten in place** on every run (no rotation) — snapshot
  them if you need to compare runs, and verify their timestamps before trusting a
  report. See Troubleshooting.

Per AGENTS.md rule #4 (no silent skipping): the auditor asserts every variant it
added to `base_profiles` survives de-duplication, raising `AssertionError`
immediately if a dedup bug drops one.

### 3. The parallelized test pipeline

**Why parallelize.** Serial audit: ~151 nodes × ~15 formatters × ~5 profiles × ~10 samples ≈ 1.1M+ problems ≈ 4-6 hours. Parallel (4 cores): ~30-60 min. Problem generation is single-threaded per node; budget a full hour.

**How it works.** `run_audit(parallel=True)` uses `ProcessPoolExecutor` with **module-level** `_audit_node()` as the worker (for pickling). Defaults: 4 workers (`multiprocessing.cpu_count()`), chunksize = ⌈151/4⌉ ≈ 38 nodes/worker (amortizes 5-10s import cost). Override workers with `--max-workers N`.

**Rules:**
1. `_audit_node()` MUST stay module-level, never a closure. `ProcessPoolExecutor` pickles it; closures fail silently. `tests/test_parallel_audit.py` is the regression gate — run before/after any parallelization change.
2. Always use `bash tests/run_checklist_audit.sh` (venv wrapper), never bare `python`. Bare python causes "No module named 'fastapi'" × 151 nodes (Trap 1).
3. Imports inside `_audit_node()` are preferred over module-level (sidesteps circular imports under `spawn`).
4. **First 5 min: 3 active workers, 1 at 0% CPU is normal** (spawn re-imports `backend.app` per worker). Do not kill — it will pick up. Only past ~1 hour is a stuck worker a real hang: check `ps` for a runaway DNA loop (Trap 2, a DNA bug, not the audit).

Every invocation (full audit, single node, worker override, pytest) is listed in
the **How to use it** table below. **Pytest alternative** (for CI integration):
`pytest tests/test_checklist_audit.py -v -m slow` — same audit, integrated output.

## How to use it

| Task | Command |
|------|---------|
| Full audit (parallel) | `bash tests/run_checklist_audit.sh` |
| Single node (debug) | `venv/bin/python -m local_only.scratch.exhaustive_checklist_auditor --no-parallel --node-ids mat_g1_na_q1_0` |
| Multiple nodes | `venv/bin/python -m local_only.scratch.exhaustive_checklist_auditor --node-ids mat_g1_na_q1_0,mat_g2_na_q1_0` |
| Override workers | `venv/bin/python -m local_only.scratch.exhaustive_checklist_auditor --max-workers 2` |
| Full audit (pytest) | `.venv/bin/python -m pytest tests/unit/test_checklist_audit.py -v -m slow` |
| Phase unit tests | `.venv/bin/python -m pytest tests/unit/ -v -m "not slow"` |

**Output files** (overwritten each run, no rotation): `checklist_audit_report.json`, `repro_crashes.json`. Snapshot before re-running if you need to compare: `cp checklist_audit_report.json checklist_audit_report.$(date +%s).json`.

## Troubleshooting

| Problem | Diagnosis | Fix |
|---------|-----------|-----|
| Code change not loading | Run `ls -l checklist_audit_report.json` to check if report is fresh. If fresh but change didn't apply, suspect bytecode cache. | `find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null` then re-run. |
| Report seems stale | Killed/restarted runs leave previous report files. Check timestamp. | `ls -l checklist_audit_report.json` — mtime should match this run. Snapshot before re-running if comparing: `cp checklist_audit_report.json checklist_audit_report.$(date +%s).json` |
| Audit hangs >1 hour | A first-5-min idle worker is normal (spawn re-import); a full run legitimately takes up to ~1 hour. Only beyond that is it a real hang. | `ps -p <pid> -o pcpu,etime,command` — 100% CPU + climbing etime = runaway DNA loop (Trap 2). Fix the DNA's re-roll logic, not the audit. |
| Same error on 100+ nodes (e.g., "No module named 'fastapi'") | This is a harness bug, not 100+ content bugs. | Always use `bash tests/run_checklist_audit.sh` (venv wrapper). Never bare `python`. |

## File layout

| Path | Purpose |
|---|---|
| `docs/pgen_checklist.md` | The checklist the audit enforces. Read before fixing any finding. |
| `docs/generator_testing_strategy.md` | This file. |
| `tests/exhaustive_checklist_auditor.py` | The auditor. Module-level `_audit_node()` is the per-process worker entry point. |
| `tests/run_checklist_audit.sh` | Venv wrapper. Use this, not bare `python`. |
| `tests/pytest.ini` | Pytest config. Defines `slow` marker. |
| `tests/unit/test_parallel_audit.py` | Serial-vs-parallel comparison on 5 nodes. **The** correctness gate for the module-level-worker requirement (Rules #1). |
| `tests/unit/test_checklist_audit.py` | Full-audit test. Asserts 0 violations. `@pytest.mark.slow`. |
| `tests/unit/test_*_*.py` | Phase-specific unit tests. Not slow. |
| `checklist_audit_report.json` | Output: `{node_id: [error_messages]}`. |
| `repro_crashes.json` | Output: `[{node_id, seed, formatter, difficulty_profile, error_message}, …]`. |
| `local_only/scratch/oc/CHECKLIST_AUDIT_BUG_FIXES.md` | Session log: which categories were fixed and how. Read when adding a new category. |
| `backend/app/practice_gen/dna/na/*.py` | The DNAs. Each has its own candidate-pool rules and `dna_name` annotation. |
| `backend/app/practice_gen/compatibility.py` | `FORMATTER_VARIANT_SUPPORT` + `FORMATTER_NUMERIC_LIMITS`. The auditor mirrors both. |
| `backend/app/services/orchestrator.py` | The orchestrator. Sets `problem.dna_name` for per-DNA checks. |
| `backend/app/practice_gen/dna/base.py` | `FormattedProblem.dna_name: Optional[str]`. |

## What the auditor checks (the categories)

When adding a new category, also add a unit test in `tests/unit/`
and document it here.

1. **Pipeline Crash** — `generate_problem()` raised. Full traceback in the report;
   captured in `repro_crashes.json` for deterministic re-trigger.
2. **Semantic Leak** — the answer appears as a standalone number in the stem.
   Skipped for `PROMPT_TARGET_FORMATTERS` (visual formatters whose prompt *is* the
   task, e.g. `number_line_read`) and for the `comparing_ordering` DNA.
3. **Vocabulary Violation** — the stem or a hint contains a `FORBIDDEN_WORDS` term
   (`sequence`, `minuend`, `subtrahend`, `addend`, `multiplicand`, `multiplier`,
   `divisor`, `dividend`, `expression`, `evaluate`). Explicit MATATAG G1-G3
   curriculum verbs (e.g. `identify`) are intentionally allowed.
4. **Formatter Fallback** — a visual formatter was requested but the pipeline
   degraded to a textual format. The DNA is missing `format_used` logic for that
   formatter/variant.
5. **Visual Degradation** — `context=word_problem` + a visual formatter produced a
   stem over 200 chars (K-1 instructional visual prompts run 120-150 chars and are
   valid).
6. **Fractions DNA override** — DNA was `fractions` but the stem doesn't mention
   fractions or use `\\` notation. `fractions` is being selected for
   ordering/comparing contexts where it shouldn't be.
7. **Strict Scalar Endpoint** — at `scalar in {0.0, 1.0}` the mapped value is more
   than ±1 from the expected endpoint. Verified against
   `get_node_competency_bounds()`.
8. **Scale Appropriateness** — for wide ranges (`max_val / min_val >= 10`),
   `scalar=0.5` mapped linearly instead of logarithmically. The axis is missing
   `scale: 'logarithmic'`.
9. **Separation of Concerns** — switching `context=pure` → `context=word_problem`
   changed the underlying numeric state (compared via `Counter` of stem numbers).
10. **Variant/Dim never exercised** — a variant option or dimension had no test
    coverage. A config bug.
11. **Profile Mismatch** — the value the orchestrator used differs from what the
    auditor requested. A silent-default bug (violates AGENTS.md rule #4).
12. **Strict Scalar Violation** — the mapped value is outside the strict
    `[min, max]` bounds (the strict version of #7).
13. **Visual Schema Error** — a visual formatter's output is missing required
    `visual_params` keys (e.g. `FractionModel` needs `model_type`, `numerator`,
    `denominator`, `total_parts`, `shaded_parts`).
14. **Formatter mismatch** — `lab_config['formatters']` doesn't match the union of
    `get_formatters_for_dna(d)` across all DNAs. A config bug.
15. **Invalid dimension type / empty options** — a malformed
    `difficulty_dimensions` or `contextual_variants` entry. A config bug.

## Traps (read first if audit result looks strange)

**Trap 1 — Uniform failure × 100+ nodes = harness bug, not content bugs.** Example: `Lab Config Fetch Crash: No module named 'fastapi'` × 151 nodes. That is **one** environment bug (bare `python` instead of venv wrapper), not 151 per-node bugs. `_import_harness_dependencies()` raises `AuditHarnessError` (distinct type) on import failure to make this clear. Always use `bash tests/run_checklist_audit.sh`.

**Trap 2 — Runaway DNA loop, not slow profile.** A full run legitimately takes up to ~1 hour, so only past that is a worker pinned at 100% CPU a real hang — a DNA with an infinite re-roll loop (e.g., `subtraction.py` re-rolling only `b` for `max_minuend=2`). Diagnose: `ps -p <pid> -o pcpu,etime,command` (100% CPU + climbing etime = runaway). Fix: make the DNA re-roll *both* operands and raise `RuntimeError` if no valid pair exists. Do not add silent defaults like `max_attempts`/`sleep` — the audit surfaces that bug.

**Trap 3 — The auditor's compatibility checks must mirror the orchestrator exactly.**
`formatter_supports_profile()` is a 1:1 mirror of `orchestrator.py:142-148`;
`_profile_violates_numeric_limit()` mirrors `orchestrator.py:88-119`. **The mirror
is the contract, and the orchestrator is the source of truth.** If you change the
orchestrator's continuous-axis mapping or compatibility check, update the auditor
in the *same commit*, or the two diverge and the audit produces:
- (a) profiles the orchestrator rejects → spurious Pipeline Crash counts; or
- (b) skipped profiles the orchestrator accepts → false-negative coverage gaps.

**Trap 4 — An implausibly high category count usually means the rule is too strict.**
When a category's count seems impossibly large, suspect the *check*, not the
backend. Past examples:
- **Strict scalar endpoint** checked against the UI's full axis range instead of
  `get_node_competency_bounds()` → 88,126 false positives. Fix: use competency
  bounds.
- **Semantic leak** flagged the answer-in-stem for *all* formatters, but for
  `number_line_read` the prompt *is* the answer → 25,148 false positives. Fix:
  `PROMPT_TARGET_FORMATTERS` carve-out.
- **Visual degradation** flagged any word_problem stem over 120 chars, but valid
  K-1 visual prompts run 120-150 → 16,766 false positives. Fix: threshold 200.

Compare the auditor's check against the orchestrator's runtime filter and look
for divergence before "fixing" the backend.

**Trap 5 — Non-reproducible repro_crashes = a DNA using the global `random`.**
`repro_crashes.json` records `(node_id, seed, formatter, difficulty_profile)` with
seed `1000 + sample_index + (1000 * len(profiles))`. For a crash to re-trigger, the
DNA must be deterministic given seed + profile + formatter. If a repro can't be
re-triggered, a `practice_gen` module is reaching for `random.random()` /
`random.randint()` instead of the passed-in `rng`. **Always use the `rng`
parameter; never the global `random` module.**

## Historical note

The previous strategy (an HTTP `fuzzer.py` against `/api/matatag/lab/generate`
plus a multi-agent visual static analysis) has been **superseded by the checklist
auditor — do not rebuild `fuzzer.py`.** If the auditor misses something the fuzzer
caught, add a category to the auditor instead. The one still-live artifact is
`local_only/scratch/oc/visual_components_audit.md`, which remains the source of
truth for **React-side visual-component bugs** the backend auditor cannot see. To
debug one, pull a deterministic payload from `repro_crashes.json` first, then hand
it to a visual audit.
