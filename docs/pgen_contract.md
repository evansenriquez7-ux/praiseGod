# PG Pipeline Contract

A generator is done when `python -m backend.app.practice_gen.validation.run_all` exits 0 and the judgment review (`pgen_judgment.md`) is filed. Checking a box proves nothing; the command output proves everything. If you believe a rule here is wrong, change the harness and this table in the same PR — never quietly deviate.

## Contract Rules Table

| Rule | Enforced by | Runs in |
|---|---|---|
| Scalar 0.0/1.0 map exactly to competency bounds — **exempt for the `number_difficulty` axis**, whose mapped value IS the scalar, making the assertion vacuous. 82 of 151 nodes carry it as their only continuous axis and therefore have no §1A; §1H asserts that the remaining 61 all do | `validate_matrix` §1A | local `run_all`; not in CI |
| No leaky windows; monotonic windows | `validate_matrix` §1B | local `run_all`; not in CI |
| Scalar 1.0 actually reaches the competency's stated range | `validate_matrix` §1A-reach | local `run_all`; not in CI |
| Every supported variant×formatter executes cleanly with valid answers | `validate_matrix` §1C | local `run_all`; not in CI |
| Unsupported combos raise; no silent substitution | `validate_matrix` §1C-reverse | local `run_all`; not in CI |
| No NOT_YET_KNOWN vocab in formatted output | `validate_matrix` §1D | local `run_all`; not in CI |
| Answer key survives formatting; interest-invariant | `validate_matrix` §1E | local `run_all`; not in CI |
| A question stem never gives away its own answer. TWO independent paths: (a) the answer is the stem's sole numeric datum, so it can be copied rather than derived; (b) the stem DECLARES it — "it is X", "the answer is X" — regardless of what else the stem carries. Path (b) closes the hole path (a) left by design, without reopening the 3,702 false positives the naive wide form produced; verified silent across 906 renders before being asserted. Worked examples ("for example 45 = 40 + 5") are exempt | `validate_matrix` §1F | local `run_all`; not in CI |
| Every node generates: no node passes on an empty execution matrix — scoped to formatter/DNA pairs the node can actually be served. A pair whose competency bounds refuse it (ALL bound values must be renderable, not any) is covered by §1C-reverse's "must raise", not here. Before 2026-08-26 the refusal test skipped list-valued bounds (78 exist), so `mat_g3_na_q3_1` reported `empty_execution_matrix` against `array_grid_read`, a formatter it never offers | `validate_matrix` §1C-coverage | local `run_all`; not in CI |
| Registry/compatibility bidirectional coverage | `validate_compat` §2 | local `run_all`; not in CI |
| Difficulty profiles meet MIN_ACCEPTANCE_RATE | `validate_dna` §3 (feasibility) | local `run_all`; not in CI |
| Response payload matches strict schema | Pydantic model (runtime, every problem) + `validate_matrix` §4 (**visual payloads only** — §4 is recorded solely under `is_visual`, so it covers 67 of 151 nodes; non-visual response shape rests on the Pydantic model alone) | runtime + local `run_all` |
| Every node carries a genuine, non-boilerplate, non-stale blind judgment review with a PASS verdict | `validate_judgment` §5 | local `run_all`; not in CI |
| Every node declares what its MATATAG competency requires, cites the clause, covers every competency word, and the pipeline provides it | `validate_capability` §6 | local `run_all`; not in CI |
| A capability's provider is the artifact that renders what the clause names, never a generic textual formatter every DNA already offers | `validate_capability` §6D | local `run_all`; not in CI |
| Every node id referenced anywhere in `backend/app/` must exist in the registry. `placement.py`'s forward-looking G4–G10 milestone ladder holds 7 that do not (latent — it is called from nowhere), so the floor is 1 file; any NEW file naming absent nodes fails | `validate_compat` §2F | local `run_all`; not in CI |
| Every node's competency bounds parse to a well-formed shape — a (min,max) tuple, a non-empty value list, or a scalar sentinel — asserted TREE-WIDE rather than against the ~20-row G1–G3 fixture table, so a new grade inherits the property automatically (Mandate #4) | `validate_compat` §2G | local `run_all`; not in CI |
| A competency naming BOTH cases of a dimension ("with and/or without X", matched as a pattern so grade 4–10 wordings are caught too) must not have X bound to one case. §2G proves bounds are well-FORMED; this proves they are FAITHFUL. Until 2026-09-04 `"without regrouping" in text` matched "with and without regrouping" as a substring, pinning mat_g3_na_q2_1 and mat_g2_na_q1_9 to 0/120 carries with every stage green — narrowing a bound removes items, so nothing downstream complains. Blind spot: a clause the parser ignores ENTIRELY emits no bound and is invisible here (that is §6's job) | `validate_compat` §2H | local `run_all`; not in CI |
| A discrete variant a node DECLARES must be one it can actually produce. **Floor 21 since 2026-09-08** (was 65; the 44 cleared were declarations offering values the node's own competency excludes — regrouping deeper than the digit ceiling allows, regrouping on estimation competencies, multiplication `tables` on addition/subtraction nodes — no generator change needed). Remainder is the other cause: a DNA declaring a variant it never implements. Build it where the competency names it, delete the declaration where it does not | `validate_compat` §2I | local `run_all`; not in CI |
| A formatter a node advertises must be REACHABLE by the student path, not merely servable when pinned (§2B). Baseline 2026-08-28: 18 nodes advertise formatters auto-select never picks — the matrix stage validates content no pupil receives and the Lab menu is wider than what is served. Floor may only SHRINK | `validate_compat` §2C | local `run_all`; not in CI |
| The correct option's position must not be predictable from the seed — measured across nodes at a fixed seed, no slot may exceed 45%. Before 2026-08-28 it was 93% (slot 1 at seed 11), so a pupil could score ~90% by always picking one position | `validate_compat` §2E | local `run_all`; not in CI |
| A saved Lab configuration may not serve content outside a node's competency — `allowed_difficulties` / `allowed_contexts` are intersected with the node's CURRENT bounds and an empty intersection raises. A config legal when saved is not legal forever. Value SETS only; numeric (min,max) bounds stay with §1A/§1B | `validate_compat` §2D | local `run_all`; not in CI |
| A formatter a node advertises must actually be servable for that node — the advertised list may not promise what the orchestrator refuses | `validate_compat` §2B | local `run_all`; not in CI |
| A true/false item family may not key every sample the same way — an all-True property set lets a pupil score 100% by answering yes, so it measures nothing. Boolean answers only, pooled across a (DNA, formatter) pair's variant combinations | `validate_matrix` §1I | local `run_all`; not in CI |
| Every check a node's own composition makes applicable actually ran **on that node** — the suite-level union proves a check ran somewhere, not everywhere | `validate_matrix` §1H | local `run_all`; not in CI |
| A known-correct answer must be graded CORRECT by all three graders (portal, Lab v1, Lab v2). **Floor 0 since 2026-09-08** (was 5, all real: an unrecognised format fell through to an MCQ *key* comparison in portal/lab_v1, so `sort_order`'s [10,9,8] was tested against "A"; lab_v1 also parsed the correct answer more leniently than the student's). All three now share `services.scoring.answers_match`, keyed off the answer's shape, not a format-name list | `validate_grade` §10 | local `run_all`; not in CI |
| A node's payload must carry every key the React component reads — a missing `visual_params` key collapses to `undefined`/`0`/`false` and breaks the render. **Floor 0 since 2026-09-08** (was 16: 7 real, fixed in `fmt_fraction_model`; 9 were this check selecting on `visual_type`, the node's category, rather than on `is_visual` as both renderers do). Applies to problems that actually carry a payload | `validate_render` §9 | local `run_all`; not in CI |
| Every assertion the harness can emit is either proven by a mutation naming it in `Mutation.asserts`, or listed in `UNPROVEN_ASSERTIONS` with a reason and a date. That allowlist may only SHRINK — a NEW assertion with neither fails immediately. Baseline 2026-08-28: 8/26 matrix assertions proven, 20 knowingly unproven | `validate_coverage` §8 | local `run_all`; not in CI |
| The suite's own census (nodes, unit tests, mutations) has not shrunk below its floor | `validate_census` §7 | local `run_all`; standalone in seconds |
| An Attester verdict must name who made it (`attested_by`), and no identity may cover more than 25 nodes — mirroring §5's reviewer plurality. Measured 2026-08-28: all 173 existing records carried NO identity field, so independence was uncheckable on a surface 4x larger than §5. Records before 2026-08-28 are grandfathered; failing them would condemn genuinely blind work to close a schema gap | `validate_capability` §6H | local `run_all`; not in CI |
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

**Known blind spot — the matrix report is overwritten by a single-node run (named 2026-08-26).**
Every matrix rule above (§1A through §1H) is enforced by `validate_matrix`, which writes its results to
`validation_reports/matrix_report.json`. Running it for one node —
`validate_matrix --node mat_g1_na_q1_0` — **replaces** the tree-wide report with that one node
rather than merging into it. Any consumer reading that file afterwards sees a tree of one.

This matters because the hardening supervisor reads that report instead of re-running a
30-minute matrix sweep every tick. The mitigation is in the reader, not the writer:
`hardening_supervisor.matrix_evidence()` compares the report's node coverage against
`get_all_node_ids()` and its mtime against the newest file under `backend/app/practice_gen/`
and `data/skeletons/`, and marks anything incomplete or outdated as `PARTIAL` / `STALE` /
`MISSING` / `UNREADABLE`. Only a `FRESH` report contributes its count to the work queue;
every other state is reported as *unmeasured* and forces a refresh. Proven by
`tests/unit/test_supervisor_queue.py`, which plants each state and asserts it is refused.

Merging instead of clobbering is *not* obviously the better fix, and it is worth saying why.
A naively merged report would carry results produced at different times against different
generator revisions, then present the union as tree-wide coverage — mixed freshness reported
as a clean sweep, which is a quieter failure than the clobber. A merge is only safe if every
node's row carries its own timestamp and freshness is judged per row. That is unbuilt.

Until it is: **a single-node matrix run leaves the tree without stage-6 evidence**, the reader says
so rather than guessing, and the next full `run_all` restores it. `tests/mutation_harness.py`
snapshots and restores the report around its run for the same reason — most of its mutations
invoke `validate_matrix --node X`, so without that the act of proving the harness would have
destroyed the evidence the harness depends on.

**Why the queue counts stages 6, 7 and 8 (2026-08-26).** The supervisor's RESUME/NOTHING_TO_DO
verdict previously derived from `validate_capability` alone — stage 8 of eight. It could therefore
report "no work" with 575 stale reviews (stage 7) and a live `empty_execution_matrix` (§1C-coverage, stage 6)
outstanding, and for 455 consecutive ticks it reported a 158-item queue that was really 735. The
gate now sums all three bands, and `scripts/measure_queue.py` prints them from that one measurement
so the tick protocol cannot compute a second, divergent number.

## Core Principles

1. **Matatag Lab as Single Source of Truth**: The Lab's Generate Preview must render exactly what the student portal will serve for the same enabled options. Drop `is_lab=True` for normal previews so the Lab runs through the same competency-bound clamp.
2. **Avoid Graceful Fallbacks**: The pipeline must fail fast and loud when schema validation, import, or limits are violated. No silent defaulting behavior is allowed.
