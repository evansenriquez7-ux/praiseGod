# PG Pipeline Contract

A generator is done when `python -m backend.app.practice_gen.validation.run_all` exits 0 and the judgment review (`pgen_judgment.md`) is filed. Checking a box proves nothing; the command output proves everything. If you believe a rule here is wrong, change the harness and this table in the same PR — never quietly deviate.

## Contract Rules Table

| Rule | Enforced by | Runs in |
|---|---|---|
| Scalar 0.0/1.0 map exactly to competency bounds | `validate_matrix` §1A | CI, blocks deploy |
| No leaky windows; monotonic windows | `validate_matrix` §1B | CI, blocks deploy |
| Every supported variant×formatter executes cleanly with valid answers | `validate_matrix` §1C | CI, blocks deploy |
| Unsupported combos raise; no silent substitution | `validate_matrix` §1C-reverse | CI, blocks deploy |
| No NOT_YET_KNOWN vocab in formatted output | `validate_matrix` §1D | CI, blocks deploy |
| Answer key survives formatting; interest-invariant | `validate_matrix` §1E | CI, blocks deploy |
| Registry/compatibility bidirectional coverage | `validate_compat` §2 | CI, blocks deploy |
| Difficulty profiles meet MIN_ACCEPTANCE_RATE | `validate_dna` §3 (feasibility) | CI, blocks deploy |
| Response payload matches strict schema | Pydantic model + `validate_matrix` §4 | runtime + CI |

## Core Principles

1. **Matatag Lab as Single Source of Truth**: The Lab's Generate Preview must render exactly what the student portal will serve for the same enabled options. Drop `is_lab=True` for normal previews so the Lab runs through the same competency-bound clamp.
2. **Avoid Graceful Fallbacks**: The pipeline must fail fast and loud when schema validation, import, or limits are violated. No silent defaulting behavior is allowed.
