# Metamorphic Testing Pipeline & Checklist Compliance Auditor

This document serves as the master operational guide for any agentic coder building, modifying, or auditing practice problem generators (PGs) in this repository. 

Our testing philosophy is built on **failing fast and loud** rather than silent defaulting. When the auditor script runs, it verifies that no code degradations, zero-sensitivity mappings, or answer leaks escape.

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

### A. Strict Scalar Mapping (Boundary Checks)
- **Rule**: A difficulty scalar of `0.0` must map strictly to the easiest curriculum bounds, and `1.0` must map strictly to the hardest bounds.
- **Verification**: The auditor generates problems at `0.0`, `0.5`, and `1.0`. It asserts that the output values are bounded correctly inside the difficulty windows without any overlap or out-of-bounds parameter leakage (with a strict $\pm 1$ rounding tolerance due to lossy log-linear mappings).

### B. Metamorphic Sensitivity Checks
- **Rule**: Changing a conceptual variant (e.g. context, operator, blank position) must result in a distinct question stem.
- **Verification**: The auditor generates problems using the exact same seed while toggling the target variant. If the stems produced are identical (e.g., word problem stem matches pure symbolic stem), it flags a `Sensitivity Violation`.

### C. Semantic Leak Safeguards
- **Rule**: The correct answer or distractors must not be leaked inside the question stem.
- **Verification**: The auditor recursively extracts all scalar numbers, strings, and floats from the generated answer and checks them against the text of the question stem. Any matches (except registered curriculum carve-outs) raise a `Semantic Leak` error.

### D. Formatter and Choice Validity Checks
- **Rule**: Formatters (like MCQ, True/False, Balance Scale) must generate valid structures without duplicates or hardcoded default selections.
- **Verification**: The auditor checks MCQ options to ensure they are unique, contains the correct answer exactly once, and have no duplicate choices.

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
- **Reason**: The process pool worker function `_audit_node()` must remain a module-level function. It cannot be wrapped in a closure or nested function because Python's `spawn` start method cannot pickle closures.

### Trap 2: Bare Python Invocation vs. Shell Wrapper
- **Issue**: Running the script with bare `python` outputs `ModuleNotFoundError: No module named 'fastapi'`.
- **Reason**: The virtual environment wrapper script matches library namespaces for FastAPI/SQLAlchemy. Always run using the `.venv/bin/python` binary, `PYTHONPATH=.`, or the wrapper scripts.

### Trap 3: Runaway Worker Processes
- **Issue**: CPU cores sit at 100% indefinitely on a single node.
- **Reason**: Infinite loop inside a DNA's parameter generation loop (e.g. subtraction min/max condition that can never be met for a specific scalar). Inspect the log outputs to find the active node, and fix the bounds selection logic in the DNA module.

---
