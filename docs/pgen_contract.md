# PG Pipeline Contract

A generator is done when `python -m backend.app.practice_gen.validation.run_all` exits 0 and the judgment review (`pgen_judgment.md`) is filed. Checking a box proves nothing; the command output proves everything. If you believe a rule here is wrong, change the harness and this table in the same PR — never quietly deviate.

## Contract Rules Table

| Rule | Enforced by | Runs in |
|---|---|---|
| Scalar 0.0/1.0 map exactly to competency bounds | `validate_matrix` §1A | CI (`validate-pgen`); does not block deploy |
| No leaky windows; monotonic windows | `validate_matrix` §1B | CI (`validate-pgen`); does not block deploy |
| Scalar 1.0 actually reaches the competency's stated range | `validate_matrix` §1A-reach | CI (`validate-pgen`); does not block deploy |
| Every supported variant×formatter executes cleanly with valid answers | `validate_matrix` §1C | CI (`validate-pgen`); does not block deploy |
| Unsupported combos raise; no silent substitution | `validate_matrix` §1C-reverse | CI (`validate-pgen`); does not block deploy |
| No NOT_YET_KNOWN vocab in formatted output | `validate_matrix` §1D | CI (`validate-pgen`); does not block deploy |
| Answer key survives formatting; interest-invariant | `validate_matrix` §1E | CI (`validate-pgen`); does not block deploy |
| A question stem never gives away its own answer | `validate_matrix` §1F | CI (`validate-pgen`); does not block deploy |
| Every node generates: no node passes on an empty execution matrix | `validate_matrix` §1C-coverage | CI (`validate-pgen`); does not block deploy |
| Registry/compatibility bidirectional coverage | `validate_compat` §2 | CI (`validate-pgen`); does not block deploy |
| Difficulty profiles meet MIN_ACCEPTANCE_RATE | `validate_dna` §3 (feasibility) | CI (`validate-pgen`); does not block deploy |
| Response payload matches strict schema | Pydantic model + `validate_matrix` §4 | runtime + CI (`validate-pgen`) |
| Every node carries a genuine, non-boilerplate, non-stale blind judgment review with a PASS verdict | `validate_judgment` §5 | CI (`validate-pgen`); does not block deploy |

**On "does not block deploy".** Every rule above is still enforced, still on every push, and still
fails loudly — in the `validate-pgen` workflow, which runs independently of `deploy-backend`. The two
were separated deliberately: `run_all` exits 0 only at a 100% node PASS rate, which is the hardening
loop's *done* signal, not a shipping criterion. Gating Cloud Run on it meant a curriculum verdict about
a Grade-2 word problem could block an unrelated backend fix. Nothing here was weakened to make a build
pass; the checks moved out of the deploy path, they did not relax. A rule that is failing is still a
rule that must be fixed — the deploy simply no longer waits on it.

## Core Principles

1. **Matatag Lab as Single Source of Truth**: The Lab's Generate Preview must render exactly what the student portal will serve for the same enabled options. Drop `is_lab=True` for normal previews so the Lab runs through the same competency-bound clamp.
2. **Avoid Graceful Fallbacks**: The pipeline must fail fast and loud when schema validation, import, or limits are violated. No silent defaulting behavior is allowed.
