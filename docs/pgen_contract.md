# PG Pipeline Contract

A generator is done when `python -m backend.app.practice_gen.validation.run_all` exits 0 and the judgment review (`pgen_judgment.md`) is filed. Checking a box proves nothing; the command output proves everything. If you believe a rule here is wrong, change the harness and this table in the same PR — never quietly deviate.

## Contract Rules Table

| Rule | Enforced by | Runs in |
|---|---|---|
| Scalar 0.0/1.0 map exactly to competency bounds | `validate_matrix` §1A | local `run_all`; not in CI |
| No leaky windows; monotonic windows | `validate_matrix` §1B | local `run_all`; not in CI |
| Scalar 1.0 actually reaches the competency's stated range | `validate_matrix` §1A-reach | local `run_all`; not in CI |
| Every supported variant×formatter executes cleanly with valid answers | `validate_matrix` §1C | local `run_all`; not in CI |
| Unsupported combos raise; no silent substitution | `validate_matrix` §1C-reverse | local `run_all`; not in CI |
| No NOT_YET_KNOWN vocab in formatted output | `validate_matrix` §1D | local `run_all`; not in CI |
| Answer key survives formatting; interest-invariant | `validate_matrix` §1E | local `run_all`; not in CI |
| A question stem never gives away its own answer | `validate_matrix` §1F | local `run_all`; not in CI |
| Every node generates: no node passes on an empty execution matrix | `validate_matrix` §1C-coverage | local `run_all`; not in CI |
| Registry/compatibility bidirectional coverage | `validate_compat` §2 | local `run_all`; not in CI |
| Difficulty profiles meet MIN_ACCEPTANCE_RATE | `validate_dna` §3 (feasibility) | local `run_all`; not in CI |
| Response payload matches strict schema | Pydantic model + `validate_matrix` §4 | runtime + local `run_all` |
| Every node carries a genuine, non-boilerplate, non-stale blind judgment review with a PASS verdict | `validate_judgment` §5 | local `run_all`; not in CI |
| Every node declares what its MATATAG competency requires, cites the clause, covers every competency word, and the pipeline provides it | `validate_capability` §6 | local `run_all`; not in CI |
| A capability's provider is the artifact that renders what the clause names, never a generic textual formatter every DNA already offers | `validate_capability` §6D | local `run_all`; not in CI |
| A formatter a node advertises must actually be servable for that node — the advertised list may not promise what the orchestrator refuses | `validate_compat` §2B | local `run_all`; not in CI |
| A rendered visual payload must depict something real and agree with its own answer — no invented currency, no empty grids, no value off its own axis | `validate_matrix` §1G | local `run_all`; not in CI |
| The harness's own unit tests pass before any stage reports green — green stages over red tests is not evidence | `pytest tests/unit` §0 | local `run_all`; not in CI |
| A capability's `bounds` provider must be a numeric-ceiling claim about that capability, never a list most of the table carries verbatim | `validate_capability` §6E | local `run_all`; not in CI |
| Every declared capability carries a blind Attester verdict that the rendered output exhibits what its clause names, and no entry contradicts one | `validate_capability` §6F | local `run_all`; not in CI |
| An attestation stops being evidence when the content it judged changes: every record still supplying a winning verdict is re-rendered and must still match. A record is exempt only once **every** one of its verdicts has been replaced by a later record — supersession is derived from the records themselves, never from a record's own `supersedes` text, so it must be earned by filing a replacement that faces this same check | `validate_capability` §6F freshness | local `run_all`; not in CI |
| An attestation must show its work: its reasoning is present and not a per-clause fill-in of one shared sentence frame (max 3 verdicts per normalized skeleton), a `PROVIDED` verdict names the seeds that show the clause, every named seed exists in that record's own `packet.samples_judged`, and no record carries more than one blind dispatch (25 verdicts). Judged on live verdicts only, by the same last-file-wins supersession rule §6F freshness uses | `validate_capability` §6G | local `run_all`; not in CI |

**On "local `run_all`; not in CI".** Every rule above is still enforced and still fails loudly — but
the enforcement now runs **only** where someone runs it: `python -m backend.app.practice_gen.validation.run_all`,
executed by the hardening loop each tick and by anyone touching the pipeline. As of 2026-08-12 no
GitHub Actions workflow runs it.

The reason is that `run_all` exits 0 only at a 100% node PASS rate, which makes it a *done* signal for
the curriculum work, not a shipping criterion. Wiring it to CI meant a curriculum verdict about a
Grade-2 word problem blocked unrelated backend deploys, including the manual testing by which those
verdicts get resolved.

Nothing here was weakened to make a build pass — no assertion changed, no check relaxed, no `|| true`
introduced. What changed is *where* the checks run, and that carries a real cost worth naming: a rule
in this table is now only as binding as the discipline of running the harness. There is no longer an
automated tripwire that stops an unverified pipeline change from reaching production. Restoring one
once the census reaches zero is the obvious fix; until then, `run_all` before you push is the contract.

## Core Principles

1. **Matatag Lab as Single Source of Truth**: The Lab's Generate Preview must render exactly what the student portal will serve for the same enabled options. Drop `is_lab=True` for normal previews so the Lab runs through the same competency-bound clamp.
2. **Avoid Graceful Fallbacks**: The pipeline must fail fast and loud when schema validation, import, or limits are violated. No silent defaulting behavior is allowed.
