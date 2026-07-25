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

These auditors independently re-check, by a different code path, several properties the CI-enforced harness already binds and enforces (`validate_matrix` §1A–§1C in [`pgen_contract.md`](pgen_contract.md)) — useful as a second opinion during manual debugging, not as a second source of the rule itself.

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

| Goal | Command |
|---|---|
| **Run Full Checklist Audit** (Parallel) | `bash tests/run_checklist_audit.sh` |
| **Run Targeted Checklist Audit** (Node list) | `bash tests/run_checklist_audit.sh --node-ids mat_g1_na_q1_6,mat_g3_na_q4_2` |
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
