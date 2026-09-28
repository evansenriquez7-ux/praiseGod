# Handoff prompt: finish Phase C (and prepare Phase D)

You are continuing the Phase 2 hardening campaign in this repo, picking up from a Claude agent
that stopped at a weekly rate limit on 2026-09-28. Read `CLAUDE.md` first. Every rule in it binds you.
Then read `validation_reports/phase2_hardening/CLAUDE_AGENT_PROMPT.md`, the campaign prompt and its
state section. This file tells you only what changed after that state was written.

## Non-negotiable rules
- Verification is execution. Quote every command you run and its verbatim output. Never predict.
- Invoke Python as `PYTHONPATH=. .venv/bin/python`. Never pipe a long run through `tail`.
- Never weaken a check. Never author or edit a reviewer's verdict, sample id, clause or `overall`.
- Stage files by name. Never `git add -A`. Commits end with a Co-Authored-By line naming your model.
- Do not rename the 44 gpt-5.6-luna / gpt-6-luna review records.
- Do not delete worktrees or files you did not create.
- Do not touch `.claude/worktrees/agent-aaac714fac3fe0cc6`, the ✝️/bible theme, `requires` /
  `requires_ignore`, or open H-11.
- The H-06 owner line in `validation_reports/phase2_hardening/hardening_status.json` is the work lock.
  It is still held by this campaign. Edit only that line (`git diff --numstat` must read `1 1`).
- End every report with an **Evidence** section.

## Where things stand (HEAD = the commit that adds this file; see `git log -3`)
- **Phase C review filing is complete:** all 91 owed nodes have a blind Haiku review filed
  (commits `e0457268`, `49284dc2`, `e559091b`). Scratch material for each node is in
  `local_only/scratch/phaseC/<node>/`: `prompt.txt`, `verdicts.json`, `reviewer_id`, `skeletons/`,
  and `set_aside/`. `agents.txt` maps nodes to reviewers. `harvested_claims.txt` holds claims taken
  from replies that were set aside, plus defects confirmed by rendering.
- **KNOWN DEFECT, the first thing to fix: 76 review records fail §5 on provenance.**
  - Cause: the scratch filers `local_only/scratch/phase{B,C}/file.sh` passed a *wave-level*
    `--dispatch-id` (`s5-phaseC-w<W>-haiku45-20260925`) for each node. `tests/file_reviews.py` names
    the `.responses/<prefix>.json` / `.prompt.txt` copy by that prefix, so each later node in a wave
    overwrote the earlier nodes' copies.
  - Result: `validate_judgment --all` prints exactly 76 findings of "raw response digest does not
    match" (63 Phase C, 13 Phase B). The validator gate works; the filer was the hole.
- **Filer fix, committed in `855645fd`:**
  - `file_reviews.file_one` now refuses to overwrite an existing copy that holds different bytes.
  - Tests are in `tests/unit/test_file_reviews.py`; 9 pass.
  - Mutation `review_response_copy_overwritten` was detected 1/1. Its proof file,
    `validation_reports/mutation_proofs/review_response_copy_overwritten.json`, is committed alongside this file.

  - Registry id `review_response_copy_not_overwritten` is added to `run_all.py`, with a row in
    `docs/pgen_contract.md`.
  - **Not yet run:** full `run_all`. `operator_doc_covers_registry` may require the new id to be named
    in `docs/testing_pipeline.md`; run it and see. The full mutation table has not been run either.
- **All 76 originals are recoverable.** For each broken record,
  `local_only/scratch/phase{B,C}/<node>/verdicts.json` and `prompt.txt` sha256-match the
  `response_digest` / `prompt_digest` recorded in the node's `dispatch_provenance`. This was verified
  by script on 2026-09-28. Re-verify before you use them.

## Your steps, in order
1. **Repair the 76 records.**
   - Make both `file.sh` scripts pass a per-node prefix, e.g.
     `--dispatch-id s5-phaseC-w${W}-haiku45-20260925-${N}`.
   - List the broken records: recompute each `dispatch_provenance` digest against its referenced
     file. The scan code is easy to rewrite: glob `validation_reports/judgment/*/*.json` and compare
     sha256 values.
   - For each broken node, first confirm the scratch `verdicts.json` and `prompt.txt` match the
     recorded digests. Then re-file it through `file.sh` with the *same* `tool_uses_by_reviewer` text,
     read from the existing record. Append one sentence to that text explaining the re-filing.
   - Diff each old record against its new one. Only `dispatch_id`, `response_ref`, `prompt_ref` and
     the appended sentence may differ. Every verdict and every piece of reasoning must be identical.
     Show this diff in the evidence.
   - Leave the wave-level `.responses` files in place: the last node of each wave still references
     them validly.
   - Re-run `validate_judgment --all`. The digest-mismatch count must be 0.
2. **Run the full proof chain** (`run_all`, then the full `tests/mutation_harness.py` table). Fix
   anything the new registry id breaks, for example by naming it in `docs/testing_pipeline.md`.
   Re-record mutation proofs as the table writes them.
3. **Phase C bookkeeping** (the campaign prompt describes each item):
   - Re-measure §5. Check for STALE reviews.
   - Scan each reviewer transcript for paths outside the reviewer's own node directory. Every filed
     record's `tool_uses_by_reviewer` already states this.
   - Write a Phase C entry in `validation_reports/HARDENING_EVIDENCE.md`. It must cover:
     - the leniency pattern: 4 of 5 "reconcile your overall" requests produced softened verdicts,
       so contradicted replies were set aside and re-dispatched fresh instead;
     - the fresh-redispatch method;
     - `mat_g3_na_q2_1`: three reviewers. The first reply was invalid JSON. The second gave overall
       PASS against its own CONCERN verdicts. The third needed one brace added (a character diff
       shows a single 1-character insertion) and `decomposition` nested under
       `competency_fulfillment` (a structural diff shows every verdict unchanged);
     - `mat_g3_na_q4_4`: asked to narrow clause citations, the reviewer did not, and three clauses
       still cite all 26 samples. This is noted in its record;
     - the confirmed content defects in `harvested_claims.txt`;
     - the 76-record provenance defect and its fix.
   - Append H-06 progress surgically.
   - Rewrite the state section of `CLAUDE_AGENT_PROMPT.md`.
   - Run `PYTHONPATH=. .venv/bin/python tests/tree_state.py --complete`, commit, and confirm the
     tree reads CERTIFIED. Release the lock in a separate follow-up commit.
4. **Stop and ask the user before Phase D.** Phase D covers the 173 CONTRADICTED `capability_phase2`
   findings, plus the owed source batch:
   - the hint contract lacks an "operation" dimension. `fractions.generate_hints` has no ordering
     branch, so `mat_g2_na_q4_2` and `q4_5` get addition hints on ordering items;
   - time_reading set-order determinism;
   - the §1G ClockSet invariant;
   - the calendar month mismatch and `VOCAB_ELAPSED` garble (`mat_g1_mg_q4_4`);
   - `mat_g2_na_q2_2` seed 605: a subtraction item on an addition node;
   - `mat_g3_dp_q3_1` / `q3_2`: stems say "table" but only a BarChart is drawn;
   - `mat_g3_dp_q3_2` seed 900: "2023" offered as an option;
   - `mat_g3_na_q3_0` seed 605: "What is 5 × 7?" on the 6–9 tables node;
   - seed 701/702 interest-wrapper mismatches.

   Phase D's scope was never confirmed with the user.

## Traps the previous agent hit
- `auto.py` / `revfile.py` diff against `verdicts.v1.json`. A stale or invalid v1 left by a crashed
  run makes them crash or mis-compare. Check v1 before trusting the diff.
- A `pgrep` self-match makes `run_all` look like it is still running. Read the log's exit line
  instead.
- `run_all` takes a long time. Launch it in the background, detached, and write to a log.
- The Graphify pre-commit hook re-stages its own outputs; that is expected.
