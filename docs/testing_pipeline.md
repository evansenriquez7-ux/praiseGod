# Metamorphic Testing Pipeline & Checklist Compliance Auditor

> [!NOTE]
> **Reference only. Not part of `run_all`/CI.** This document describes the supplementary `tests/` auditors — dev-tooling for exploring the pipeline by hand. They are **not** wired into `.github/workflows/validate-pgen.yml` or `run_all.py`; the binding, CI-enforced contract lives in [`pgen_contract.md`](pgen_contract.md). None of the checks below are a second enforcement path — where they overlap with the contract table, the contract table is authoritative and this file links to it rather than restating the rule.

This document is a supplementary operational guide for any agentic coder exploring or auditing practice problem generators (PGs) with the `tests/` dev-tooling in this repository.

The `tests/` auditors share the harness's **fail fast and loud** philosophy (see [`pgen_contract.md`](pgen_contract.md)) but are manually invoked, not CI-gated.

---

## 1. Pipeline Layout & Architecture

The testing framework consists of three automated pipeline components under the `tests/` directory:

| Component File | CLI Command | Purpose & Checks |
|---|---|---|
| **Exhaustive Checklist Auditor**<br>[exhaustive_checklist_auditor.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/tests/exhaustive_checklist_auditor.py) | `bash tests/run_checklist_audit.sh` | Enumerates every `(node, profile, formatter)` allowed by `compatibility.py` and checks boundaries, operator sensitivity, formatting rules, and semantic leaks. |
| **Frontend Contract Auditor**<br>[frontend_contract_auditor.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/tests/frontend_contract_auditor.py) | `PYTHONPATH=. .venv/bin/python -m tests.frontend_contract_auditor` | Evaluates React render-schema payload contracts: checks that required `visual_params` keys are present, improper fraction units are calculated correctly, and answer fields don't leak to client payload parameters. |
| **Grader Round-Trip Auditor**<br>[grader_roundtrip_auditor.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/tests/grader_roundtrip_auditor.py) | `PYTHONPATH=. .venv/bin/python -m tests.grader_roundtrip_auditor` | Exercises route paths via FastAPI's `TestClient`. Checks that portal, lab v1, and lab v2 grader routes agree that correct student submissions are marked correct. |

---

## 2. Core Metamorphic Checkpoints

These auditors independently re-check, by a different code path, several properties the harness already binds and enforces (locally via `run_all` — there is NO CI enforcement; `validate-pgen.yml` was deleted 2026-08-12) (`validate_matrix` §1A–§1C in [`pgen_contract.md`](pgen_contract.md)) — useful as a second opinion during manual debugging, not as a second source of the rule itself.

### A. Strict Scalar Mapping (Boundary Checks)
- **Cross-checks:** `pgen_contract.md`'s scalar-boundary row (`validate_matrix` §1A).
- **How:** The auditor generates problems at `0.0`, `0.5`, and `1.0` and asserts the output values are bounded correctly inside the difficulty windows without overlap or out-of-bounds leakage (strict $\pm 1$ rounding tolerance due to lossy log-linear mappings).

### B. Metamorphic Sensitivity Checks
- **Cross-checks:** `pgen_contract.md`'s variant×formatter execution row (`validate_matrix` §1C).
- **How:** The auditor generates problems using the exact same seed while toggling the target variant (context, operator, blank position, …). If the stems produced are identical, it flags a `Sensitivity Violation`.

### C. Semantic Leak Safeguards
- **Cross-checks:** `pgen_contract.md`'s answer-key-integrity row (`validate_matrix` §1E).
- **How:** The auditor recursively extracts all scalar numbers, strings, and floats from the generated answer and checks them against the question stem text. Any match (except registered curriculum carve-outs) raises a `Semantic Leak` error.

### D. Formatter and Choice Validity Checks
- **Cross-checks:** `pgen_contract.md`'s variant×formatter execution row (`validate_matrix` §1C).
- **How:** The auditor checks MCQ options for uniqueness, exactly one correct answer, and no duplicate choices.

---

## 3. CLI Execution Reference Table

`tests/mutation_harness.py` is the `pgen_hardening.md` Phase 4 artifact: it plants each of the seven
specified bugs in real pipeline source, runs the validator meant to catch it, asserts a non-zero exit,
and restores the file. It edits tracked files in place while running, so it is kept out of CI and off
concurrent harness runs; run it after changing anything in `backend/app/practice_gen/validation/`.

| Goal | Command |
|---|---|
| **Run Full Checklist Audit** (Parallel) | `bash tests/run_checklist_audit.sh` |
| **Run Targeted Checklist Audit** (Node list) | `bash tests/run_checklist_audit.sh --node-ids mat_g1_na_q1_6,mat_g3_na_q4_2` |
| **Mutation-test the validation harness** (verify the verifier) | `PYTHONPATH=. .venv/bin/python -m tests.mutation_harness` |
| **Mutation-test a single planted bug** | `PYTHONPATH=. .venv/bin/python -m tests.mutation_harness --only leaky_window` (`--list` to see all seven) |
| **Run Frontend Contract Audit** | `PYTHONPATH=. .venv/bin/python -m tests.frontend_contract_auditor` |
| **Run Grader Round-Trip Audit** | `PYTHONPATH=. .venv/bin/python -m tests.grader_roundtrip_auditor` |
| **Fast Pytest suite** (Skips slow full-audit) | `PYTHONPATH=. .venv/bin/python -m pytest tests/unit/ -m "not slow"` |
| **Full Pytest suite** | `PYTHONPATH=. .venv/bin/python -m pytest tests/unit/` |
| **Clean Up DB Grader Test Students** | `PYTHONPATH=. .venv/bin/python -c 'from backend.app.database import SessionLocal; from backend.app.models import StudentProfile; db = SessionLocal(); deleted = db.query(StudentProfile).filter(StudentProfile.name.like("GraderAudit_%")).delete(synchronize_session=False); db.commit(); print(f"Deleted {deleted} test students."); db.close()'` |

---

## 4. Diagnostics & Troubleshooting Traps

When running the audits, keep these core troubleshooting tips in mind:

### Trap 1: Pickle Errors under Process Worker Spawns
- **Issue**: Parallel execution worker crashes with pickle exceptions.
- **Reason**: The process pool worker function `_audit_node()` has to stay a module-level function. It cannot be wrapped in a closure or nested function because Python's `spawn` start method cannot pickle closures.

### Trap 2: Bare Python Invocation vs. Shell Wrapper
- **Issue**: Running the script with bare `python` outputs `ModuleNotFoundError: No module named 'fastapi'`.
- **Reason**: The virtual environment wrapper script matches library namespaces for FastAPI/SQLAlchemy. Always run using the `.venv/bin/python` binary, `PYTHONPATH=.`, or the wrapper scripts.

### Trap 3: Runaway Worker Processes
- **Issue**: CPU cores sit at 100% indefinitely on a single node.
- **Reason**: Infinite loop inside a DNA's parameter generation loop (e.g. subtraction min/max condition that can never be met for a specific scalar). Inspect the log outputs to find the active node, and fix the bounds selection logic in the DNA module.

---

---

## 5. The Harness As It Actually Is (regenerate this when checks change)

**There is no CI enforcement.** `validate-pgen.yml` was deleted on 2026-08-12 at the
maintainer's direction and `deploy-backend.yml` has no `needs: validate`. The suite is run
locally by `run_all`, driven by the hardening loop. A deploy is gated only by Cloud Run
refusing to promote a revision whose container fails to start.

### Running it

```bash
PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.run_all   # exit 0 = done
PYTHONPATH=. .venv/bin/python3 scripts/hardening_supervisor.py --reap           # cheap queue read
PYTHONPATH=. .venv/bin/python3 -m tests.mutation_harness                        # prove the checks fail
```

`run_all` exiting 0 is the only completion signal. A green stage proves nothing on its own:
the mutation harness is what shows each check can actually fail, and a check with no
mutation is unproven regardless of how long it has been passing.

### Stages

| Stage | What it covers |
|---|---|
| 1/8 unit tests (§0) | the harness's own tests; `tests/unit/` |
| 2/8 DNA structural (§3) | generator structure and difficulty-profile feasibility |
| 3/8 compatibility (§2 family) | registry coverage, monotonicity, servability, reachability, saved-config gating, option placement |
| 4/8 interest invariance | the answer must not depend on the interest theme |
| 5/8 vocabulary gating | no NOT_YET_KNOWN vocabulary in rendered output |
| 6/8 behavioural matrix (§1 family) | the per-node content sweep — boundaries, execution matrix, answer keys, visuals, applicability |
| 7/8 judgment reviews (§5) | blind per-node review artifacts, non-boilerplate and non-stale |
| 8/8 capability contract (§6 family) | competency → pipeline provision, blind Attester verdicts |
| §1J count/noun agreement | an explicit count and the noun after it must agree in the text a pupil reads |
| §1K option degeneracy | a choice item must offer distinguishable choices, and exactly one may answer it |
| §9 render contract | the payload must be renderable by the React component the student sees |
| §10 grading contract | a known-correct answer must be graded correct by all three graders |
| §7 census | the suite itself has not silently shrunk |
| two-direction | the contract doc, this doc, and the registry agree |

### Every binding check

| Ref | Enforced by |
|---|---|
| `§0` | pytest tests/unit: the harness's own unit tests pass (slow suite deselected) |
| `§1A` | validate_matrix: boundary exactness (0.0/1.0) |
| `§1B` | validate_matrix: containment sweep (monotonicity and window bounds) |
| `§1A-reach` | validate_matrix: scalar 1.0 reaches the competency maximum region |
| `§1C` | validate_matrix: execution matrix (variant x formatter combinations) |
| `§1C-reverse` | validate_matrix: reverse check (excluded combinations raise clear errors) |
| `§1C-coverage` | validate_matrix: every node/DNA/formatter has a non-empty execution matrix |
| `§1D` | validate_matrix: vocabulary/concept lint on final formatted output |
| `§1E` | validate_matrix: answer-key & interest theme invariance on formatted output |
| `§1F` | validate_matrix: question stem does not leak its own answer |
| `§1G` | validate_matrix: rendered visual payload is real and self-consistent |
| `§1H` | validate_matrix: every check a node's composition makes applicable actually ran on that node |
| `§1I` | validate_matrix: a true/false item family may not key every sample the same way |
| `§1J` | validate_language: an explicit count and its noun must agree in the rendered student text, nested quoted statements included |
| `§1K` | validate_options: a choice item must offer distinguishable choices, and exactly one of them may answer the question |
| `§2` | validate_compat: registry/compatibility coverage & monotonicity |
| `§2B` | validate_compat: every formatter a node advertises can actually be served for it |
| `§2D` | validate_compat: a saved configuration may not serve content outside a node's competency |
| `§2E` | validate_compat: the correct option's position must not be predictable from the seed |
| `§2C` | validate_compat: a formatter a node advertises must be reachable by the student path, not merely servable when pinned |
| `§2F` | validate_compat: every node id referenced in the app must exist in the registry |
| `§2G` | validate_compat: every node's competency bounds parse to a well-formed shape — the tree-wide property behind the fixture table |
| `§2H` | validate_compat: a competency naming BOTH cases of a dimension must not be bound to one of them — §2G proves bounds are well-formed, §2H proves they are faithful to the competency text |
| `§2I` | validate_compat: a discrete variant a node declares must be one it can actually produce — a shrinking floor (65 at 2026-09-04), not a hard gate |
| `§3` | validate_dna: structural checks and difficulty profiles feasibility |
| `§4` | validate_matrix: VISUAL payload schema validation (recorded only under is_visual, so ~67 of 151 nodes; non-visual response shape rests on the Pydantic model at runtime) |
| `§5` | validate_judgment: genuine, non-boilerplate, non-stale blind judgment reviews |
| `§6` | validate_capability: competency requirements declared, cited, covered, and provided |
| `§6D` | validate_capability: a capability carried only by a generic textual formatter is not provided |
| `§6E` | validate_capability: a capability carried only by a `bounds` list most of the table shares is not provided |
| `§6F` | validate_capability: every declared capability carries a blind Attester verdict, and none is contradicted |
| `§6G` | validate_capability: an attestation shows its work — non-boilerplate reasoning citing seeds from its own packet |
| `§6H` | validate_capability: an Attester verdict must name who made it, and no identity may cover more than one dispatch |
| `§7` | run_all: the suite's own census (nodes, unit tests, mutations) has not shrunk below its floor |
| `§8` | validate_coverage: every assertion the harness can emit is either proven by an EXECUTED mutation (a verified proof record in `validation_reports/mutation_proofs/`) or on a shrinking allowlist |
| `§9` | validate_render: the payload a node emits must be renderable by the React component the student sees |
| `§10` | validate_grade: a known-correct answer must be graded correct by all three graders |

### Proving the harness

`python tests/mutation_harness.py` plants each registered bug, runs the validator that
should notice, restores the tree, and — since 2026-09-12 — writes a machine-readable proof
record per mutation to `validation_reports/mutation_proofs/`. §8 READS those records; it
does not run the table. So the order is: run the mutation table, then `run_all`. Editing
any file under `mutation_proof.INPUT_ROOTS` invalidates every proof, and §8 says so in one
line rather than 140.

### Floors

Several checks carry a **floor** rather than a hard zero, because their baseline was red
when they were built and Scaling Mandate §5 says a check whose baseline is already red
cannot be told from the noise it sits in. A floor may only ever SHRINK. Lowering one to
make a run pass is precisely the move it exists to catch. Current floors live in
`validate_census.CENSUS_FLOORS`, `validate_render.RENDER_FLOOR`,
`validate_grade.GRADE_FLOOR`, and `validate_compat._REACH_FLOOR`.
