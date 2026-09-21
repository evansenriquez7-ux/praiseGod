# Handoff — continue the Phase 2 hardening plan

**Rewritten 2026-09-21 (evening) on `2aedd33e`, tree CERTIFIED. This file is deliberately a
POINTER, not a summary.**

Earlier versions duplicated the plan's status and then drifted from it. Two sources of truth
is how a session inherits confident wrong numbers, so status lives in exactly one place —
the plan's `START HERE — handoff` — and this file tells you how to reach it safely, what the
owner has already decided, and what will waste your time if nobody warns you.

---

## FIRST: establish what state the tree is in

**One command. Run it before touching anything.** It replaces the ad-hoc digest script and
the human-written paragraph that used to live here — that was a pipeline defect, and closing
it was the last session's first job.

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py      # exit 0 only when CERTIFIED
```

It prints the live digest, the worktree, each of the four digest-bound artifact families,
and any OPEN INTENT — a record written when a batch or chain STARTS and cleared when it
finishes. The intent is what separates the two states that were previously indistinguishable
from the digests alone.

| State | Means | Do |
|---|---|---|
| `certified` | nothing in flight, worktree clean, all four families fresh | **Start THE JOB.** Do NOT re-run the chain; it proves nothing new |
| `awaiting_reproof` | a batch landed, the chain was never run | Run the chain, in the documented order in the plan |
| `interrupted` | an intent is open, or the worktree is dirty | Read the open intent — it names what was in flight and the next step |

**The expected reading right now:**

```text
PASS tree_state: CERTIFIED
  live input digest : 3907ad23d1b84972
  worktree          : clean
  mutation_proofs         fresh  150 file(s)
  release_shards          fresh  6 file(s)
  obligation_benchmark    fresh  1 file(s)
  frontend_static_render  fresh  1 file(s)
```

And the ledger, which now runs to `H-10`:

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
#  -> PASS hardening_status: 10 H-row(s) valid — 3 closed, 6 open, 1 out_of_scope
```

**If either command disagrees with the block above, believe the command, not this file.**

**NAMED LIMITS of `tree_state`, so you keep looking:** an intent is a claim, not a lock — no
pid, no heartbeat, no timeout, so a live session cannot be told from one that died holding
one; a session that never calls `--begin` leaves a dirty worktree with no record of WHY; and
`--complete` is trusted, caught only in that clearing it on a stale tree still reports
`awaiting_reproof` rather than `certified`.

Record your own intent before starting work that can be interrupted:

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin campaign \
    --session <your-session-id> --note "what you are doing"
# ... and on completion:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --complete --note "where you got to"
```

---

## THE JOB — Phase B, and only Phase B

**Phase A is DONE (2026-09-21) and re-proved. Do not redo any of it.** Interruption-safety
machinery, the two-digit H-row cap, the §1J hints hole, and the four undrawn-referent nodes
plus the §1M gate all landed, and the full chain was run: corpus 147/150, six shards at 0
failures, `verify-release` complete, `run_all` at `scheduled=17 completed=14 failed=3
crashed=0`. Details in the plan's `START HERE` and in `HARDENING_EVIDENCE.md`.

**Three stages are red and all three are M2's attestation debt.** They are the whole of the
remaining work in this plan:

| Stage | Count | Note |
|---|---|---|
| `judgment_reviews_5` | **1253** | went UP from 1221 — see below; this is correct |
| `capability_phase2` | **218** — 67 CONTRADICTED, 0 UNATTESTED, 74 STALE, 50 UNADJUDICABLE, 27 other | |
| `assertion_coverage_8` | 3 in 1 family (§6F) | **Cannot be fixed by re-running.** Its three mutations return `INVALID` because their baseline IS `capability_phase2`, which is red. Only clearing the queue clears it. |

**Phase A made `judgment_reviews_5` WORSE, and that is correct behaviour, not a regression to
undo.** Changing a generator makes every review of its old output STALE, and a stale verdict
is unearned — `mat_g1_na_q1_0` seed 42 was reviewed as *"What number comes next when
counting: 94, 95, 96, 97, ___?"* and now renders *"What number is marked?"*. The nodes that
gained visuals are exactly the nodes whose filed reviews describe content that no longer
exists. **A generator fix does not clear a §6F finding, and it can create §5 ones.** Expect
the count to move against you whenever you touch content; the only thing that clears either
queue is a blind re-judgement.

### The campaign

Owner ruled the **whole 218-finding queue is ONE campaign**, spanning sessions and
**resumable**. It is also the only work that can turn a red stage green.

**It costs NO re-proof, provided you touch no source.** `validation_reports/judgment/` and
`validation_reports/attestation/` are deliberately outside the fingerprint (see
`mutation_proof.INPUT_FILES`' comment) — verified, not assumed: a probe file written into
`attestation/` left the digest unmoved. That is precisely why Phase A went first, and why you
should be reluctant to open a source edit now. **If you do touch source, you owe the whole
~3.4h chain again.**

**Where to start — measured on THIS tree, not inherited.** Highest finding counts first:

```text
mat_g2_na_q4_3   7      mat_g1_na_q1_0   3      mat_g2_mg_q1_2   3
mat_g2_na_q3_5   5      mat_g3_mg_q2_0   3      mat_g2_na_q1_3   3
mat_g3_mg_q1_1   5      mat_g3_mg_q2_3   3      mat_g1_na_q3_2   3
mat_g1_mg_q1_0   3      mat_g1_dp_q3_3   3      mat_g1_na_q3_7   3
mat_g3_na_q2_1   3      mat_g3_mg_q2_2   3
```

**SIX NODES CHANGED ON 2026-09-21 and their prior evidence is worthless.** Re-attest these
against what they render NOW, never against a recorded sample:

```text
mat_g1_na_q4_1   now draws FractionModel   ("Compare 1/2 and 1/4 using models")
mat_g3_na_q4_6   now served by fraction_shade, was unservable entirely
mat_g3_na_q4_7   now draws fraction models
mat_g3_mg_q1_4   now draws GeometryFigure  ("Recognize, using models, ... point, line, ray")
mat_g3_mg_q1_5   now draws GeometryFigure  ("Recognize and draw parallel/perpendicular")
mat_g2_mg_q4_2   now draws Timetable       ("...including timetables")
```

Also re-render before judging anything on `mat_g2_na_q3_0`, `mat_g1_mg_q2_2`, the
`mat_g2_mg_q4_*` family, `mat_g3_mg_q3_2`, and the calendar and perimeter nodes — their
HINTS changed when §1J began linting hint text for the first time.

### How blindness works — the owner's ruling, and it is not negotiable

You **DISPATCH** to a separate agent that has neither the answer key nor your context.
`tests/attester_packets.py` writes what the Attester sees and the key it must not see;
`tests/attester_file.py` turns returned verdicts into §6F/§6G records without retyping.

**Blindness is a prompt contract, not a sandbox.** You never author a verdict, never re-file
one, and never copy a v1 rationale forward. All 151 legacy reviews are v1 and unadjudicable,
and the v1→v2 migration was refused as impossible in principle — v2 demands per-sample
contextual-validity verdicts, exact clause coverage and dispatch-bound provenance that no v1
reviewer was ever asked for, so populating those fields means authoring judgments nobody
gave. Use `legacy_review_queue.json` to PRIORITISE, never as evidence. A v1 `PASS` records
only that somebody once wrote PASS; tick A found template rationales in that corpus.

§6G clusters reasoning skeletons precisely to catch a fill-in-the-blank verdict stapled onto
many clauses. `template_attestation` is a live, DETECTED mutation for it. Do not give it
something to find.

---

## Read this, in this order

1. **`AGENTS.md` / `CLAUDE.md`** — the Scaling Mandate, Engineering Protocols, Definition of
   Done. Verification is execution; a prediction phrased as a confirmation is a lie.
   The 2026-09-21 ruling supersedes File Management's read-only rule on `validation/`.
2. **`docs/phase2_hardening_completion_plan.md`, `START HERE — handoff`.** It opens with a
   dated block that supersedes everything below it, including the owner rulings in full.
3. The middle of that plan for the *design* of what you implement. Design, never status.
4. **`validation_reports/HARDENING_EVIDENCE.md`**, the 2026-09-21 entries, for how the
   current numbers were obtained and what was measured rather than assumed.

---

## Claim your row before you start

`owner` is a work-lock. Claim it, release it on commit (`unclaimed` or `released @ <rev>`).
If your session identifier embeds an H-row token, make sure it is *your own* — that check
exists because a worker once claimed H-07 while doing H-08.

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py     # must PASS before and after
```

* **`H-06`** holds the M2 capability queue — **this is your row for the campaign.** Released
  `@ e23a4ffe`, still OPEN, and must not be closed by a re-proof alone.
* **`H-10`** is the interruption-safety row, released `@ 7912add7`, still OPEN: the machinery
  exists and its mutation is detected, but the row's own finding is only half answered.
* **`H-02`, `H-05`, `H-07`, `H-08`** are open and unclaimed. `H-02` shrinks as the queue
  clears — its 3 remaining §6F errors are downstream of your campaign.
* Splitting **H-08's intro-surface render gap** into its own row is still the OWNER's call.
  The row set can express `H-11` now; that is not permission to open one.

**Edit the ledger SURGICALLY.** `json.dumps(ensure_ascii=True)` over the whole file
renormalises `§`/`—` escapes across rows you do not own; a 2026-09-20 session produced 16
lines of collateral churn that way and had to revert. Patch the lines you mean to patch, and
check `git diff --numstat` shows only what you intended.

Every artifact you add under `validation_reports/phase2_hardening/` — including inside
subdirectories — must be claimed by some row's `proof_artifacts`, or the ledger fails.

---

## If you arrive mid-anything

A handoff can happen at any moment; hardware and environment failures are outside a session's
control, and the owner ruled that "must end certified" is NOT the rule.

* **Run `tests/tree_state.py` first.** If an intent is open it tells you what was in flight.
* **Shards are individually resumable.** Each receipt records its own digest. Re-run only the
  stale indices — a 2.5-hour saving you get by reading digests instead of guessing.
* **A surviving mutation has TWO causes** and you must tell them apart: the check is broken,
  or the plant no longer reaches the code the validator runs. Diagnose by instrumenting the
  real path, never by reading the validator and concluding it would work.
* **`INVALID — the unmutated command baseline exited 1` is a THIRD thing** and is neither.
  The runner refused to score, because the baseline was already red. Re-running cannot fix it.

---

## Traps that cost real time

1. **Scan all 150 mutation anchors BEFORE running the corpus after any source batch.** A
   2026-09-21 run aborted at 54/150 because a batch edit had moved one anchor. The scan takes
   two seconds; the abort cost fifty minutes.
   ```sh
   PYTHONPATH=. .venv/bin/python -c "
   from pathlib import Path; import tests.mutation_harness as mh
   print([(m.name, r) for m in mh.MUTATIONS if m.edits for r,(f,_) in m.edits.items()
          if Path(r).read_text().count(f) != 1] or 'all anchors OK')"
   ```
2. **Re-run the benchmark AFTER your last source commit, not before.** A commit landing
   between the benchmark and the corpus leaves `obligation_benchmark_11` red at baseline, and
   `obligation_benchmark_outlives_source` then scores INVALID rather than DETECTED. Never
   re-prove that one WHILE shards run — its plant edits the module they spend 2.6h inside.
3. **A gate can be defeated one stack frame later — or one ENTRY POINT over.** The
   orchestrator and the adapter enforce formatter rules differently, and the orchestrator
   skips its filter entirely for a PINNED formatter. A student-path fix left the Lab still
   serving an undrawn stem, and §1M could not see it because §1M samples the student path.
4. **A rule copy-pasted into N sites will disagree with itself.** `_number_plurals` lived in
   SIX places; `length_measurement` kept its own `_sing()` beside the shared inflection rule.
   Consolidate, and route through the same helper the validator imports.
5. **A classifier that keys on a MESSAGE STRING is a latent bug.** The exclusions generator
   told an eligibility refusal from a content crash with
   `"is not supported by any DNA" not in str(exc)`, so ~27 node/formatter pairs stayed
   wrongly advertised and `formatters_reachable` counted them as content debt for weeks. It
   is a type now, `FormatterNotEligible`.
6. **`_generated_formatter_exclusions.py` goes stale** whenever a formatter or COMPATIBILITY
   entry changes; §2B fails loudly naming each entry. Regenerate with
   `PYTHONPATH=. .venv/bin/python3 -m scripts.regen_formatter_exclusions`. **Never hand-edit
   it** — it is derived empirically because three attempts to model the rules statically drifted.
7. **Adding a formatter changes the obligation product**, so pinned counts in
   `tests/unit/test_obligation_executor.py` move. Confirm every added route is actually SERVED
   at several seeds *before* touching those numbers. Updating a count to match reality is
   legitimate; updating it to make a test pass is not.
8. **The fast unit suite takes ELEVEN MINUTES**, not the 35 seconds an old note claims, and
   `tests/pytest.ini`'s `addopts` is NOT picked up from the repo root — pass `-m "not slow"`
   explicitly or the two 15–40 minute pool tests run too. Background it.
9. **A shared distractor helper can be right for arithmetic and wrong for your domain.**
   `augment_distractors` refuses negatives but allows ZERO — correct for sums, and it put a
   `0 g` option against a `1 g` answer. Filter in your formatter.
10. **The pre-commit hook rebuilds Graphify and stages `graphify-out/`.** Expect more files in
    the commit than you staged. It does NOT move the input digest — verify that rather than
    assume it.
11. **Do not run anything heavy concurrently.** `tests/frontend_renderer.py` writes to one
    fixed path with no PID and no lock; six call sites funnel through it. Unfixed.
12. **Cosmetic edits cost 3.4 hours.** A 2026-09-20 session realigned four import
    continuation lines AFTER completing the chain and invalidated the whole re-proof. Once
    certified, touch no source you do not mean to change.
13. **`git commit --amend` moves the hash**, so a ledger row written as `released @ <hash>`
    before the amend points at a dangling commit. Release in a follow-up commit.

---

## Still owner-owned — do not hand-patch around these

**`CSI-R1`–`CSI-R3`** are open owner rulings in `context_semantics_inventory.json`. `CSI-R4`
is ruled and closed. Splitting H-08's intro-surface gap into its own row is also the owner's.

---

## Limitations left standing — named so you keep looking

* **§1M's deixis list is CLOSED.** A stem that points in wording nobody has seen yet is not
  caught; the pattern count prints with the pass line so the hole's size is a number. It also
  cannot tell whether the drawn visual is the RIGHT one — "look at the pictograph" beside a
  drawn clock passes §1M and is §1G's and §9's business — and it cannot see a display the
  pupil needs but the stem never mentions. It reads stems, not hints.
* **§1J's mirror direction does not gate** (a singular noun after a count of two or more is
  measured and printed only), count/verb agreement is unchecked, and neither lint reads the
  visual payload's own labels.
* **A DECLARED variant axis restricted by `FORMATTER_VARIANT_SUPPORT` is still unchecked on
  the orchestrator's PINNED path.** `assert_formatter_supports` is deliberately scoped to
  UNDECLARED axes: caps, profiles and `ctx.values` do not share one vocabulary, and widening
  it refused every pinned render on `mat_g2_mg_q2_0` (§2B) and 46 producible declarations on
  `mat_g1_na_q1_7` (§2I). Closing it needs sentinel resolution, per-DNA.
* **A legitimate axis value of `0`, `""` or `False` is never enforced by either path**,
  because both skip falsy values — a guard that exists only to survive `division`'s
  `remainder` name collision. No current axis uses one.
* **`fraction_model_read` cannot draw an improper fraction** (it emitted `shaded_parts=7` in a
  shape with `total_parts=3`), so `mat_g3_na_q4_6` is served by `fraction_shade` alone.
* **The ANY reading of `formatter_refused_at_node` is not mutation-covered at its own
  comparison.** The `wanted & allowed` boundary itself is unproven.
* **Nothing asserts a pictograph's symbol COUNT equals the table's answer.** Verified once, by hand.
* **`ScaleRead` and `GeometryFigure` geometry are proven by arithmetic on emitted attributes,
  not layout** — jsdom has no layout engine, the blind spot §12 already names for
  NumberLine/BarChart. The elements exist and are distinct; nothing proves they are legible.
* **The estimate-task floor gates nothing.** A sibling DNA framing estimation as rounding
  would reproduce the zero-measurement defect with every gate green.
* **§8's execution accounting is stubbed** and stays provable only against a green live
  corpus. Do not describe §8 as fully proven.
* **`comparing_ordering` and `missing_number` each declare a `visual_home` that
  `base_generator` can never read** (it reads it only for `visual_read` DNAs; both are
  `algorithmic`). Measured no-ops. Fixing them is a DNA edit belonging to its own change.
* **The Phase 1 network guard patches ONE interpreter**, so connections opened inside children
  of `unit_tests`, `census_7` and `behavioural_matrix` are invisible; Phase 2 stages are
  unguarded; loopback is allowed.

---

## Rules this handoff will not let you skip

- **The Definition of Done is an executed `run_all` with its output shown.** It is currently
  **NOT met** and this document does not claim otherwise. A green subset is not completion.
- **Never weaken a check to make it pass.** If a gate is red, the bug is in the pipeline. The
  one exception is documented ground-truth error, reported with node ID and justification.
- **Prove a check by executing a planted violation**, not by reading the validator.
- **Check that your mutation is not passing for the wrong reason.** A plant that edits a
  digest-bound module reds the freshness check by itself, so the command exits 1 whether or
  not your gate works. Break your own gate deliberately and confirm the marker disappears.
- **A fix at the data layer gates nothing.** Where you fix content without a gate, say so.
- **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
  the evidence log. A gate described as total is how the next agent stops looking.
- **File an Evidence section** in `validation_reports/HARDENING_EVIDENCE.md` with the exact
  commands, verbatim output, and seeds for anything found or fixed.
