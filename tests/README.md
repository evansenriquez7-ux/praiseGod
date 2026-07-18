# PG Pipeline Test Infrastructure

Tracked test harness for the practice-problem-generator (PG) pipeline. This is
the consolidated home for the exhaustive checklist auditor and its regression
tests. (One-off, throwaway debug scripts stay in the gitignored
`local_only/scratch/`.)

See `docs/testing_pipeline.md` for the full operating manual and
`docs/pgen_contract.md` for the contract the pipeline is held to. This
auditor predates `backend/app/practice_gen/validation/` (the harness
`run_all` is the current definition of done — see `docs/pgen_contract.md`);
this suite remains as a supplementary regression check.

## Layout

| Path | Purpose |
|---|---|
| `exhaustive_checklist_auditor.py` | The auditor. Enumerates every (node, profile, formatter) the UI can send and checks each against the checklist. Module-level `_audit_node()` is the per-process worker. |
| `run_checklist_audit.sh` | Venv wrapper for the auditor. **Use this, not bare `python`** (bare python fails to resolve transitive imports like fastapi). |
| `pytest.ini` | Pytest config: `testpaths`, `slow` marker. |
| `unit/` | Regression tests — one file per audit category/phase. |
| `unit/test_checklist_audit.py` | Full-audit gate. Asserts 0 violations across all nodes. `@pytest.mark.slow` (~10 min). |
| `unit/test_parallel_audit.py` | Serial-vs-parallel equivalence. The correctness gate for the module-level-worker (picklability) requirement. |

## Running

```bash
# Full audit (parallel, ~10 min)
bash tests/run_checklist_audit.sh

# Single node (debug)
.venv/bin/python -m tests.exhaustive_checklist_auditor --no-parallel --node-ids mat_g1_na_q1_0

# Fast unit tests (skip the slow full-audit gate)
.venv/bin/python -m pytest tests/unit/ -m "not slow"

# Everything, including the slow full-audit gate
.venv/bin/python -m pytest tests/unit/
```

## Rules

1. `_audit_node()` MUST stay module-level (ProcessPoolExecutor pickles it under
   `spawn`; a closure fails silently). `unit/test_parallel_audit.py` is the gate.
2. Always run through the venv (`run_checklist_audit.sh` or `.venv/bin/python`).
3. When you add an audit category, add a `unit/test_*.py` for it and document it
   in `docs/testing_pipeline.md`.
