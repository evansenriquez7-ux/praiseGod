# Generator Testing Strategy

> **"Praise God" is your catchphrase. Use it appropriately.**
> *(AGENTS.md: this is the project's catchphrase. Use it as a celebration
> when a node passes the audit or a category drops to zero, not as
> decorative noise.)*

## What this document is

The current strategy for catching practice-problem-generator (PG) bugs
in this repo has three components. They were built and hardened across
two sessions (2026-06-30 → 2026-07-01) and replaced the previous
"backend fuzzer + AI static analysis" approach that the
`fuzzer.py` + `visual_components_audit.md` strategy in
`local_only/scratch/oc/visual_components_audit.md` originally used.

If you are a new agent, the previous UI-fuzzer + visual audit strategy
described in the bottom of this file is **historical context only**.
Do not rebuild it. Use the three-component strategy below. It is
strictly more complete and is now the source of truth for "did this
generator follow the checklist?".

## The three components

### 1. Fail-fast PG pipeline

Every DNA, generator, and formatter in `backend/app/practice_gen/`
must surface problems that violate `docs/pgen_checklist.md` as an
**exception**, never as a silently-degraded problem.

- `PracticeOrchestrator.generate_problem()` (in
  `backend/app/services/orchestrator.py`) lets any
  `RuntimeError`/`ValueError` raised by the DNA, the formatter, or
  the visual layer propagate to the caller. It does not catch and
  return a default.
- DNAs that cannot produce a non-degenerate problem for the requested
  profile (e.g. subtraction fallback when `max_minuend <= 2`) raise
  `RuntimeError` with a descriptive message — see
  `backend/app/practice_gen/dna/na/subtraction.py:228-253` for the
  canonical pattern.
- Formatters that cannot build `len(distractors) >= 3` raise
  `ValueError` rather than padding with placeholder strings. See
  `backend/app/practice_gen/generators/_operand_guard.py` for the
  candidate-pool rules that prevent this from being hit in normal
  profiles.

**Why this matters for the audit:** if a profile makes a node
*crash*, the auditor catches the exception, records the
`(node_id, seed, formatter, profile)` tuple in
`repro_crashes.json`, and moves to the next combination. If a profile
makes a node *silently degrade* (return a near-empty problem), the
auditor's downstream content checks flag it as a violation, but it is
much harder to reproduce and root-cause.

**Rule:** when fixing a generator bug, do not add a "graceful default"
that returns a near-empty problem when inputs are bad. Raise. The
audit's job is to surface these failures; the orchestrator's job is
to filter bad profiles out *before* they reach the DNA. If the
orchestrator is letting a bad profile through, that is the bug to
fix, not the DNA's behavior.

### 2. The exhaustive checklist auditor

`local_only/scratch/exhaustive_checklist_auditor.py` is the source
of truth for "does this generator follow
`docs/pgen_checklist.md`?". It enumerates **every (node, profile,
formatter) combination** the UI is allowed to send and checks the
output against the checklist rules.

Key design points:

- **Profile builder is mirrored from the orchestrator.** The auditor
  uses `build_test_profiles()`, `formatter_supports_profile()`, and
  `_profile_violates_numeric_limit()` to ensure it never requests a
  profile the orchestrator would reject with
  `IncompatibleConfigurationError`. This means a violation reported
  by the auditor is a real bug, not a "the auditor asked for
  something invalid" false positive.
- **Per-DNA×formatter compatibility is mirrored from
  `FORMATTER_VARIANT_SUPPORT`**, not recomputed. If the orchestrator
  rejects a (DNA, formatter, variant) combination at runtime
  (see `services/orchestrator.py:140-148` for the runtime filter),
  the audit does not test it.
- **Per-formatter numeric limits** are enforced via
  `FORMATTER_NUMERIC_LIMITS` (in
  `backend/app/practice_gen/compatibility.py`) and
  `_profile_violates_numeric_limit()`. A profile whose mapped value
  exceeds the formatter's `max_val` is filtered out before
  generation. Example: `emoji_pictorial`'s `max_val=100` prevents
  the audit from requesting a profile that would map to 1000.
- **Strict scalar endpoint check** uses
  `get_node_competency_bounds()` (the actual range the orchestrator
  respects) and tolerates **±1 rounding** at `scalar in {0.0, 1.0}`
  because the log mapping `int(pow(10, …))` is inherently lossy at
  the upper boundary. Anything beyond ±1 is a real violation.
- **Fail-fast on harness import errors** (e.g. missing
  `fastapi` in the interpreter). `_import_harness_dependencies()`
  raises `AuditHarnessError` which is a distinct exception type from
  per-node content failures — so a broken venv is never mislabeled
  as 151 distinct per-node bugs. (We hit this in the v3 baseline:
  `Lab Config Fetch Crash: No module named 'fastapi'` × 151 nodes
  was actually a single environment bug.)
- **The auditor writes two JSON files** at the workspace root:
  - `checklist_audit_report.json`: `{node_id: [error_messages]}`
  - `repro_crashes.json`: `[{node_id, seed, formatter,
    difficulty_profile, error_message}, …]` — every crash the audit
    can deterministically re-trigger. This is the bug queue.

**Per AGENTS.md rule #4** (no silent skipping): the auditor asserts
that every variant option it added to `base_profiles` is present in
the returned (de-duplicated) profile list. If a dedup bug drops a
variant, the auditor raises `AssertionError` immediately rather than
producing a misleadingly-clean report.

### 3. The parallelized test pipeline

`run_audit(parallel=True)` distributes nodes across
`ProcessPoolExecutor` worker processes. The per-node body is the
module-level `_audit_node()` (extracted from the old inline `run_audit`
body specifically so `ProcessPoolExecutor` can pickle it).

- **Default: `multiprocessing.cpu_count()` workers** (4 on the Mac
  mini 2018 build target). Override with `--max-workers N`.
- **`chunksize = ceil(N_nodes / N_workers)`** (e.g. 38 for
  151 nodes × 4 workers). This amortizes the ~5-10s per-process
  import cost over ~38 node audits per worker invocation.
- **Correctness gate:** `tests/test_parallel_audit.py` runs the
  audit on 5 sample nodes both serially and in parallel, and asserts
  byte-identical output. This test was the regression net when the
  per-node body was extracted — if you change `_audit_node()` or the
  aggregation, this test must still pass.
- **Slow mark:** the full audit takes ~20-40 min on 4 cores. All
  full-audit tests are marked `@pytest.mark.slow` and excluded from
  the default pytest run. Run them with `-m slow` before opening a PR
  that touches a DNA, formatter, or the auditor.

## How to use it

### Run the full audit (CLI)

```bash
local_only/scratch/run_checklist_audit.sh
```

This is the venv wrapper — use it instead of bare `python`. It
runs `venv/bin/python -m local_only.scratch.exhaustive_checklist_auditor`
and writes `checklist_audit_report.json` + `repro_crashes.json` at
the workspace root. The wrapper exits non-zero if any node has
violations.

CLI flags:

```bash
venv/bin/python -m local_only.scratch.exhaustive_checklist_auditor \
    --max-workers 4    # default 0 (= cpu_count)
    --no-parallel      # run serially (useful for debugging)
    --node-ids mat_g1_na_q1_0,mat_g2_na_q1_0  # restrict to a subset
```

### Run the full audit (pytest)

```bash
cd local_only/scratch
../../venv/bin/python -m pytest tests/test_checklist_audit.py -v -m slow
```

`test_checklist_audit.py` calls `run_audit(parallel=True)` directly
and asserts zero violations. The advantage over the CLI is that it
integrates with the test runner — failures show up in the pytest
output and you can iterate without re-importing the auditor.

### Run a single-node smoke test

```bash
venv/bin/python -m local_only.scratch.exhaustive_checklist_auditor \
    --node-ids mat_g1_na_q1_0 --no-parallel
```

Use `--no-parallel` so the output is deterministic and you can read
the print statements in order.

### Run the unit tests for individual phases

```bash
cd local_only/scratch
../../venv/bin/python -m pytest tests/ -v -m "not slow"
```

This runs the 5 unit-test files (`test_axes_log_scale`,
`test_distractor_fallback`, `test_separation_of_concerns`,
`test_semantic_leak_guards`, `test_strict_scalar_tolerance`)
without the slow full-audit test. Run this before committing any
DNA, formatter, or auditor change.

## File layout

| Path | Purpose |
|---|---|
| `docs/pgen_checklist.md` | The checklist the audit enforces. Read this before fixing any audit finding. |
| `docs/generator_testing_strategy.md` | This file. |
| `local_only/scratch/exhaustive_checklist_auditor.py` | The auditor. 805 lines. Module-level `_audit_node()` is the per-process worker entry point. |
| `local_only/scratch/run_checklist_audit.sh` | Venv wrapper. Use this, not bare `python`. |
| `local_only/scratch/pytest.ini` | Pytest config. Defines `slow` marker. |
| `local_only/scratch/tests/test_parallel_audit.py` | Comparison test: serial vs parallel on 5 sample nodes. **The** correctness gate for the parallelization refactor. |
| `local_only/scratch/tests/test_checklist_audit.py` | Full-audit test. Asserts 0 violations. Marked `@pytest.mark.slow`. |
| `local_only/scratch/tests/test_*_*.py` | Phase-specific unit tests. Not slow. |
| `checklist_audit_report.json` | Output: `{node_id: [error_messages]}`. |
| `repro_crashes.json` | Output: `[{node_id, seed, formatter, difficulty_profile, error_message}, …]`. |
| `local_only/scratch/oc/CHECKLIST_AUDIT_BUG_FIXES.md` | Session log: which categories were fixed and how. Read this when adding a new category. |
| `backend/app/practice_gen/dna/na/*.py` | The DNAs. Each one has its own candidate-pool rules and (for the ones fixed in Phase 1A) `dna_name` annotation. |
| `backend/app/practice_gen/compatibility.py` | `FORMATTER_VARIANT_SUPPORT` + `FORMATTER_NUMERIC_LIMITS`. The auditor mirrors both — if you change one, the other is auto-consistent. |
| `backend/app/services/orchestrator.py` | The orchestrator. Sets `problem.dna_name = dna_name` so the auditor can do per-DNA content checks. |
| `backend/app/practice_gen/dna/base.py` | `FormattedProblem.dna_name: Optional[str]`. The field the orchestrator annotates. |

## What the auditor checks (the categories)

These are the failure categories the audit currently surfaces. When
adding a new category, also add a unit test in
`local_only/scratch/tests/` and document it here.

1. **Pipeline Crash** — `PracticeOrchestrator.generate_problem()` raised
   an exception. Captured with full traceback in the report. Captured
   in `repro_crashes.json` for deterministic re-trigger.
2. **Semantic Leak** — the answer (`correct_answer`) appears as a
   standalone number in the stem. Skipped for
   `PROMPT_TARGET_FORMATTERS` (visual formatters whose prompt *is* the
   task, like `number_line_read`). Skipped for the `comparing_ordering`
   DNA.
3. **Vocabulary Violation** — the stem or any hint contains a word from
   `FORBIDDEN_WORDS` (`sequence`, `minuend`, `subtrahend`, `addend`,
   `multiplicand`, `multiplier`, `divisor`, `dividend`, `expression`,
   `evaluate`). Words that are explicit MATATAG curriculum verbs at
   G1-G3 (e.g. `identify`) are intentionally NOT forbidden.
4. **Formatter Fallback** — the user requested a visual formatter
   (`pictograph_set`, `bar_chart_read`, etc.) but the pipeline
   degraded to a textual format. Indicates the DNA is missing
   `format_used` logic for that formatter/variant combination.
5. **Visual Degradation** — `context=word_problem` was combined with a
   visual formatter and the stem exceeded 200 chars (the threshold;
   K-1 instructional visual prompts routinely run 120-150 chars and
   are valid).
6. **Fractions DNA override** — the DNA picked was `fractions` but
   the stem doesn't mention fractions or use `\\` notation. Indicates
   `fractions` is being selected for ordering/comparing contexts when
   it shouldn't be.
7. **Strict Scalar Endpoint** — at `scalar in {0.0, 1.0}` the mapped
   value is more than ±1 from the expected endpoint. Verified against
   `get_node_competency_bounds()`, not the UI's `min_value`/`max_value`.
8. **Scale Appropriateness** — for wide ranges (`max_val / min_val >= 10`),
   `scalar=0.5` mapped linearly instead of logarithmically. Indicates
   the axis is missing `scale: 'logarithmic'`.
9. **Separation of Concerns** — switching from `context=pure` to
   `context=word_problem` changed the underlying numeric state.
   Captured by comparing the `Counter` of numbers in the stems.
10. **Variant/Dim never exercised** — a contextual variant option or
    difficulty dimension had no coverage in the test profiles.
    Indicates a config bug.
11. **Profile Mismatch** — the value the orchestrator actually used
    differs from the value the auditor requested. Indicates a
    silent-default bug (violates AGENTS.md rule #4).
12. **Strict Scalar Violation** — the mapped value is outside the
    strict `[min, max]` bounds for the dimension. The strict version
    of #7 (uses `get_node_competency_bounds()` directly).
13. **Visual Schema Error** — a visual formatter's output is missing
    required `visual_params` keys (e.g. `FractionModel` requires
    `model_type`, `numerator`, `denominator`, `total_parts`,
    `shaded_parts`).
14. **Formatter mismatch** — the formatters declared in
    `lab_config['formatters']` don't match the union of
    `get_formatters_for_dna(d)` across all DNAs. Indicates a config
    bug.
15. **Invalid dimension type / empty options** — a
    `difficulty_dimensions` or `contextual_variants` entry is
    malformed. Indicates a config bug.

## Lessons learned (read these before touching the audit)

These are the failure modes the previous strategy hit and which the
new strategy is specifically designed to prevent. **If you are
debugging a "weird" audit result, check the lesson list first.**

### Lesson 1: Always run the auditor under the project's venv

The single most common false-positive cascade we've hit:
`Lab Config Fetch Crash: No module named 'fastapi'` × 151 nodes.
This is a **harness** failure, not a content failure, but the
auditor can't tell the difference unless you run it under
`venv/bin/python` (which has `fastapi`, `sqlalchemy`, etc. installed).

**Use `local_only/scratch/run_checklist_audit.sh`, never bare
`python`.** The shell wrapper exists for exactly this reason.

If you see the *same* `Lab Config Fetch Crash` string across most or
all nodes, that is the venv bug, not a real finding.

### Lesson 2: If the audit hangs, the DNA has a runaway loop — not a slow profile

We hit this with `mat_g1_na_q3_3` hanging at 100% CPU for 40+
minutes. The cause was a `while` loop in
`backend/app/practice_gen/dna/na/subtraction.py:228-235` that only
re-rolled `b` (not `a`) when no valid `(a, b)` pair existed. For
`max_minuend=2` there is no valid pair, so the loop ran forever.

How to diagnose:

1. `top` or `ps -p <pid> -o pcpu,etime,command` — confirms the
   process is at 100% CPU (not blocked on I/O).
2. `py-spy dump --pid <pid>` if available (samples the Python
   call stack without killing the process).
3. As a fallback: `kill -SIGALRM <pid>` while a
   `faulthandler.enable()` is active — `faulthandler` writes a
   Python traceback to stderr on `SIGALRM`. See
   `local_only/scratch/oc/CHECKLIST_AUDIT_BUG_FIXES.md` for the
   exact recipe used.
4. **Then fix the DNA**, not the audit. The audit's job is to
   surface the failure; the DNA's job is to fail fast. Re-rolling
   both `a` and `b` and raising `RuntimeError` if no valid pair
   exists is the correct pattern.

**Per AGENTS.md rule #4:** do not add a `time.sleep(0.01)` or
`max_attempts` silent-default that returns a near-empty problem.
Raise. Surface. The audit will report it as a Pipeline Crash, which
is the right outcome — the orchestrator should pre-filter the
profile.

### Lesson 3: When parallelization "loses" a node, the function is not module-level

`ProcessPoolExecutor` pickles the worker function and its
dependencies. If `_audit_node()` is a closure or a local function
inside `run_audit()`, the pool will fail to pickle it and either
crash the whole run or silently drop the node.

The auditor got this wrong on the first refactor: `_audit_node`
was originally inline. The fix was to extract it to the module
level. The regression net is
`local_only/scratch/tests/test_parallel_audit.py` — it runs the
audit on 5 sample nodes both serially and in parallel and asserts
byte-identical output. Run this test before and after any
parallelization refactor.

### Lesson 4: Mirror the orchestrator's compatibility checks exactly

The auditor's `formatter_supports_profile()` is a 1:1 mirror of
`backend/app/services/orchestrator.py:142-148`. The auditor's
`_profile_violates_numeric_limit()` is a 1:1 mirror of
`orchestrator.py:88-119`. **If you change the orchestrator's
continuous-axis mapping or compatibility check, you must update
the auditor in the same commit, or the audit will start
generating false positives (or, worse, false negatives).**

The mirror functions exist to make the audit's profile builder
behave identically to the orchestrator's runtime filter. If the
two diverge, the audit either:
- (a) requests a profile the orchestrator rejects → spurious
  Pipeline Crash counts; or
- (b) skips a profile the orchestrator accepts → false-negative
  coverage gap.

**The mirror is the contract.** The orchestrator's logic is the
source of truth; the audit's mirror must follow.

### Lesson 5: When adding a new check, the failure mode is usually "the rule is too strict"

A common cause of runaway violation counts is a check that flags a
case the orchestrator's own runtime filter would have rejected. We
hit this with:

- **Strict scalar endpoint** initially checked against the UI's
  `min_value`/`max_value` (the full axis range), but the
  orchestrator uses `get_node_competency_bounds()` (a tighter
  competency-specific range). 88,126 false positives. Fix: use
  `competency_bounds`.
- **Semantic leak** initially flagged the answer appearing in the
  stem for *all* formatters, but for `number_line_read` and
  similar visual formatters the prompt *is* the answer. 25,148
  false positives. Fix: add `PROMPT_TARGET_FORMATTERS` carve-out.
- **Visual degradation** initially flagged any word_problem stem
  over 120 chars, but K-1 instructional visual prompts routinely
  run 120-150 chars and are valid. 16,766 false positives. Fix:
  raise threshold to 200.

**When a category's count seems implausibly high, suspect the rule
is too strict, not that the backend is implausibly buggy.** Compare
the auditor's check against the orchestrator's runtime filter and
look for divergence.

### Lesson 6: `dna_name` annotation unlocks per-DNA content checks

`FormattedProblem.dna_name: Optional[str] = None` was added in Phase
1A, and the orchestrator sets `problem.dna_name = dna_name` after
choosing the DNA. This is what made the `Fractions DNA override`
check possible: without knowing which DNA the orchestrator picked
(it is selected stochastically), the auditor cannot check whether
the stem matches the DNA's expected structure.

**Whenever you add a new DNA, set `problem.dna_name` in the
corresponding generator.** The auditor relies on it.

### Lesson 7: One environment bug can masquerade as 151 distinct bugs

The v3 baseline had every single node failing with the same
`Lab Config Fetch Crash: No module named 'fastapi'` error. This
was a single bug (running the audit under bare `python` instead of
`venv/bin/python`) mislabeled as 151 distinct per-node failures.

When investigating an audit run, **first check whether the
violation pattern is implausibly uniform.** If 100+ nodes all fail
with the same string, the bug is in the harness, not the backend.

The fix was `_import_harness_dependencies()` which raises
`AuditHarnessError` (distinct from any per-node content failure)
on transitive import failure. The auditor's `run_audit()` does
not catch `AuditHarnessError` — it propagates and kills the run
with a clear message.

### Lesson 8: Stable seeds are required for repro_crashes

`repro_crashes.json` records `(node_id, seed, formatter,
difficulty_profile)`. The seed is `1000 + sample_index + (1000 *
len(profiles))`. For this to be reproducible:

- The DNA must be deterministic given the same seed, the same
  `difficulty_profile`, and the same `formatter`.
- The `build_test_profiles()` function must produce the same
  profile list across runs (it does — see Lesson 4).
- The `practice_gen` modules must not reach for
  `random.random()` or `random.randint()` at module level (only
  inside a function that takes an `rng` parameter).

If you see repro_crashes that can't be re-triggered, check
whether the DNA is using the global `random` module. **Always use
the `rng` parameter.**

### Lesson 9: macOS `spawn` start method quirks

On macOS, `multiprocessing` defaults to the `spawn` start method.
This means each worker re-imports the entire `backend.app` module
tree, which takes 5-10 seconds. We observed that **3 workers
typically run actively while the 4th is at 0% CPU for the first
few minutes** (it has been spawned but the OS hasn't scheduled it
yet). This is normal, not a bug. The audit's `chunksize` math
accounts for it: `chunksize = ceil(N / workers)` means each
worker is invoked only ~4 times, so the 5-10s import cost is
amortized over 38 nodes per call.

If you see "1 worker at 0% CPU" for the first few minutes of a
4-worker run, do not kill the run. It will pick up.

### Lesson 10: Cleanup is part of the strategy

`local_only/scratch/` is the temporary-scripts directory per
`AGENTS.md` file-placement rules. The diagnostic scripts created
during the runaway-loop investigation
(`diagnose_slow_nodes.py`, `diagnose_slow_nodes_v2.py`,
`diagnose_runaway.py`, `diagnose_combination.py`,
`trace_hang.py`, `verify_remaining_nodes.py`) were temporary and
were deleted at the end of the session. **The audit log files
(`audit_run_*.log`) and the workspace-root report files
(`checklist_audit_report.json`, `repro_crashes.json`) are
regenerated on every audit run, so keep the latest one only.**

## What the previous strategy looked like (historical)

The previous strategy combined:

1. A **HTTP fuzzer** (`fuzzer.py`) that hit the
   `/api/matatag/lab/generate` endpoint with random
   `(node_id, format_preference, axis_values)` permutations and
   asserted the response was valid JSON. This caught 500s and
   empty `mcq_options`, but was blind to the React layer.
2. A **multi-agent static analysis** ("Hub-and-Spoke" AI QA) that
   spawned `CompetencyPgenAuditor` subagents, each auditing a
   batch of visual components by cross-referencing the backend
   formatter (e.g. `fmt_calendar.py`) against its React
   counterpart (e.g. `CalendarInteractive`). This caught
   answer-leaks, state overwrites, and missing interactivity
   bindings.

The static analysis produced `visual_components_audit.md` in
`local_only/scratch/oc/`, which is **still the source of truth
for visual-component bugs** (formatter-side React issues that the
backend auditor cannot see).

The fuzzer's job has been superseded by the exhaustive
checklist auditor. The static-analysis job is still useful for
visual-component bugs but is no longer the only check. If you are
debugging a React rendering bug that the audit doesn't catch,
the static-analysis strategy is still applicable — but use the
checklist auditor's `repro_crashes.json` to get a deterministic
backend payload first, then hand the payload to a visual
auditor.

**Do not rebuild `fuzzer.py` from scratch.** If the
checklist auditor misses something the fuzzer used to catch,
file an issue against the auditor (or add a new category to
it) — that is the path forward.
