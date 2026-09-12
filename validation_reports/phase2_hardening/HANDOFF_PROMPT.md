# Handoff prompt — continue `docs/phase2_hardening_completion_plan.md`

Written 2026-09-12 at `f99c8d9f`. Paste the block below to the next agent.

---

Continue implementing `docs/phase2_hardening_completion_plan.md`. Read `AGENTS.md` /
`CLAUDE.md` first; the Scaling Mandate and the Engineering Protocols are binding, and the
Definition of Done is `run_all` exiting 0 with output shown — never a reading of the code.

## 1. DO THIS FIRST — the tree is green except for one thing, and it is expected

**§8 is RED at HEAD and `run_all --phase 1` exits 1.** The last session's edits
invalidated all 94 mutation proofs and the re-run was stopped partway by a rate limit.
This is the staleness rule working, not a defect.

```sh
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py          # ~25 min, 94 mutations
```

**Expect EXACTLY TWO survivors**, both the documented self-poisoning class. For each:
delete its record and re-run it alone.

```sh
rm validation_reports/mutation_proofs/source_edited_without_reproof.json
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py --only source_edited_without_reproof
rm validation_reports/mutation_proofs/allowlist_keeps_a_paid_debt.json
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py --only allowlist_keeps_a_paid_debt
```

Why: §8 quotes the runner's refusal reason, and the refusal reason quotes the mutation's
own expected marker, so one failure poisons its own baseline forever. Full explanation and
the durable fix (move the plant onto an isolated corpus under `tests/`, as
`tests/isolated_corpus.py` already did for the custody mutations — **owed work, not done**)
are in `mutation_proof.py`'s KNOWN LIMITATIONS. A third survivor is NOT expected; treat one
as a real finding and diagnose it per Scaling Mandate 2 before assuming it is a fixture
problem.

Then confirm the baseline:

```sh
DATABASE_URL= PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all --phase 1
# must be EXIT=0, "scheduled=14 completed=14 failed=0 crashed=0 not_run=0"
```

`DATABASE_URL=` empty is not decoration — it is what proves §10 stays hermetic (`H-01`).
Keep using it.

## 2. Where the plan stands

`validation_reports/phase2_hardening/hardening_status.json` is the ledger; it has a
`handoff` block and per-row `progress` / `still_open` / `residual` fields. **Trust those
over the plan prose**, and keep them updated — `tests/hardening_status.py` validates them.

* `H-01` **CLOSED** `9fbcfdf9` — §10 hermetic and bidirectional. 14m23s → 33s.
* `H-03` **CLOSED** `1d0de929` — stage ledger, crash isolation. Residual named in the row.
* `H-04` first half landed `ade21efb` — obligation manifest, §11, derived twice.
* `H-05` partial `08fdfdde` — silent-path inventory gated at zero; the rest untouched.
* `H-06` partial `a382ab06` — packet sample allocation fixed; visual fields still absent.
* `H-02`, `H-07`, `H-08` untouched. `H-09` out of scope by owner ruling.

Session moved assertions proven BY EXECUTION from 68/107 to 80/117, allowlist 39 → 37,
mutations 79 → 94, unit tests 495 → 617.

## 3. Next work, in `recommended_order`

1. **`H-04`'s executor** (order 3). The manifest counts 459 pairs / 5,060 discrete
   obligations, agreed by two independent derivations. Missing: `experience` (×4) and
   `student_interest` (×27) are NOT crossed in — the true product is **546,480**, recorded
   in `obligation_budget.json` as the largest unclosed gap. Also missing: the
   1,000-obligation benchmark, sharding, and the PR/release tier split (step 0B's 30-minute
   and 4-hour targets are unmeasured).
2. **`H-05`** (order 4). Only the silent-skip family is done. Still open: narrow
   representatives, first-DNA selection, low sample counts, G1–3 assumptions, multi-digit
   grade parsing, exact typed comparisons, real prerequisite edges.
3. **`H-08`** is worth pulling forward out of order, because **`H-06` depends on it**.
   Step 2 requires the packet's visual description be derived from the RENDERED OUTPUT,
   never from the payload; that needs step 5A's `renderToStaticMarkup` suite. Today
   `_render_sample` carries no visual fields at all, so "judgment omits visual fields" and
   "corrupt visual fields produce no freshness error" are both still open. Owner ruling:
   **no browser, no Puppeteer, no `test:e2e`** — delete `frontend/run_servers_and_test.js`.

## 4. Traps this session hit, so you do not

* **A scratch script importing `run_all` needs `if __name__ == "__main__"`.**
  `validate_matrix` drives a `ProcessPoolExecutor` and spawn re-imports `__main__`.
  Without the guard, 52 concurrent copies of Phase 1 ran over the same report files and
  produced a 2700s "matrix stalled" error plus two red tests that pass normally — a result
  shaped exactly like a real finding.
* **Any edit under `mutation_proof.INPUT_ROOTS`** (`backend/app`, `tests`, `scripts`,
  `data`, `frontend/src`, plus `docs/pgen_contract.md` and `docs/testing_pipeline.md`)
  invalidates all 94 proofs — ~25 min to re-prove. Batch your edits, then run the table once.
* **Never assert `unit_tests` on a mutation that drives one test file.** It makes the
  allowlisted `unit_tests` entry read as proven and §8 correctly reports a paid debt.
  Declare a label, as `packet_variant_coverage_uncapped` does.
* **`executed_checks |= ...` inside a stage function** rebinds the name and raises
  `UnboundLocalError`. Use `.update(...)`.
* **Every `§` token in `docs/pgen_contract.md` is scanned** as a contract ref, prose
  included. Do not write "§-refs" in a row.
* **Verify inherited numbers.** Step 0B's recorded 4,325 obligations was unreproducible and
  its probe was gone; step 2's four figures reproduced exactly. Check before building on one.

## 5. How to work

Protocol 7: binding behaviour, its enforcing check, its mutation, and the
`docs/pgen_contract.md` row move in ONE commit. Mandate 5: activate a gate at a measured
zero, or at a shrink-only floor if the baseline is genuinely not clean, and say which.
Mandate 6: name every blind spot in the validator docstring, the contract row, AND
`validation_reports/HARDENING_EVIDENCE.md`. End every task report with an Evidence section
containing the exact commands and their verbatim output.

Do not close an `H-` row on the half of it you did — record `progress` and `still_open`
and leave it open. Two rows were closed this session and both say in writing what they did
not cover.
