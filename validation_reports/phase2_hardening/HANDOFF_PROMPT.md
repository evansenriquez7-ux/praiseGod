# Handoff prompt — continue `docs/phase2_hardening_completion_plan.md`

Written 2026-09-14 on a working tree based at `f8597c0f`.

Continue implementing `docs/phase2_hardening_completion_plan.md`. Read `AGENTS.md` /
`CLAUDE.md` first. The Scaling Mandate and Engineering Protocols are binding, and the
Definition of Done is an executed `run_all` result with output, never a code reading.

## Current executed state

- The complete 105-mutation corpus was re-proved against input digest
  `8bf50a2a4632b9d9`: 104/105 were detected in the aggregate. The sole survivor was
  `source_edited_without_reproof`, with the documented self-poison refusal. Both it and
  `allowlist_keeps_a_paid_debt` were then deleted and re-run individually; each was
  detected 1/1.
- The proof gate now reports 105 current proofs, 93/123 assertions proven by execution,
  30 on the shrink-only allowlist, and 17 classified silent handlers.
- Hermetic Phase 1 was executed with an empty `DATABASE_URL` and exited 0:
  `scheduled=14 completed=14 failed=0 crashed=0 not_run=0 incomplete=0`.
- Phase 2 was also executed and exited 1: judgment reviews have 484 problems and the
  capability contract has 217 problems (67 contradicted, 76 stale, 74 unadjudicable).
  The complete, unqualified Definition of Done is therefore not achieved.
- H-04's executor exists. Two derivations agree on 459 node/DNA/formatter pairs, 4,293
  base obligations, and 18,906 continuous crossings. Crossing 27 interest requests and
  four experiences gives 463,644 finite obligations; five seed slots represent 2,318,220
  executions through 579,555 cache keys.
- The current four-worker benchmark executed 1,000 cache keys / 4,000 represented
  executions with zero failures in 17.136s (median 6.993ms, p95 32.068ms, peak RSS
  112,369,664 bytes). It projects 2.759h total and six 27.588m modulo shards.
- H-05 has seven of eight named assertion debts proved. Registry coverage is
  bidirectional; KG monotonicity follows all 5,726 explicit prerequisite edges; DNA
  structure covers all applicable nodes/declared grades at five seeds with exact typed
  comparisons and multi-digit grades; vocabulary covers every mapped DNA; interest
  invariance runs every grade-supported theme over 94 node/DNA pairs on the final path.

## Rows that remain open

- H-04 is partial: the six release shards have not run, so the complete finite sweep is
  explicitly NOT certified. The PR tier and benchmark do not substitute for receipts.
- H-05 is partial: learner-visible interest delivery is genuinely red. At seed 731,
  555/820 supported requests contain no value from the requested theme bank.
  `lab_portal_equivalence` also remains a static source check with no behavioral mutation.
  Full formatter × interest coverage awaits H-04 release receipts.
- H-06 still has no visual fields in `_render_sample`. Its description must come from
  rendered output, never directly from the payload.
- H-02 has 30 assertion debts. H-07 and H-08 remain open; H-09 is out of scope.
  H-01 and H-03 are closed with their written residuals preserved.

## Recommended next move

Run H-04's six release shards if the roughly 2.759-hour budget is acceptable. Otherwise,
continue H-05 by repairing learner-visible theme delivery and then prove behavioral
Lab/portal equivalence. H-08 can move ahead of H-06 because H-06 depends on static
rendered-output descriptions.

## Invariants and traps

- Run Phase 1 with `DATABASE_URL=` empty; that is the H-01 hermeticity proof.
- Any edit under `mutation_proof.INPUT_ROOTS` invalidates all 105 proof records. Batch
  such edits, then run the full corpus once.
- A scratch script importing `run_all` needs an
  `if __name__ == "__main__"` guard or process-pool workers re-run Phase 1.
- Never assert `unit_tests` on a mutation that drives one test file.
- Every section-sign token in `docs/pgen_contract.md` is scanned as a contract reference.
- The two proof-integrity mutations can self-poison because the refusal quotes their own
  marker. After a full run, delete each affected proof record and re-run it with `--only`.
  A third survivor is a real finding until instrumentation proves otherwise.
- Do not close an H-row for only the half completed. Preserve `progress`,
  `still_open`, and `residual`.

End every substantive report with an Evidence section containing exact commands and
verbatim results, including seeds for defects found and fixed.

## Resume checkpoint — 2026-09-14, supersedes earlier next-action claims

The current dirty tree is newer than the 105-proof/green-Phase-1 snapshot above.
Do not report that snapshot as certification of these bytes. The latest session notes
and exact logs are in `local_only/scratch/hardening_resume.txt` and `resume_*.log`.

This resumed session closed two reproduced schema attribution gaps at seed 42:
assessment reviewers must match their dispatch, and dispatch clause allocations must
match attributed clause evidence. Both new mutations were detected individually,
but later renderer edits invalidate those proof digests until re-run.

A full unit baseline was interrupted after two failures (134 passed, 1 skipped).
The actual visual path at `mat_g1_na_q1_0`, seed 43, exposed `tsx` CLI IPC creation
failing with sandbox `listen EPERM`. Direct `node --import tsx` rendered the same
sample successfully. Both Python renderer entry points now use that loader from the
frontend directory. Focused regressions are the next checkpoint, followed by frontend
evidence generation, full mutations and unqualified `run_all`.

No live review/attestation was authored or upgraded. The merged filing workflow,
independent reviews, release sweeps, and other open H-rows remain unfinished.
