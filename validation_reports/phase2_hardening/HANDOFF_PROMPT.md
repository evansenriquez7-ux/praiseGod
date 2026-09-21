# Handoff — continue the Phase 2 hardening plan

**Rewritten 2026-09-21 (evening), after Phase A landed and was re-proved. The tree is
CERTIFIED. This file is deliberately a POINTER, not a summary.**

Earlier versions duplicated the plan's status and then drifted from it. Two sources of truth
is how a session inherits confident wrong numbers, so status lives in exactly one place —
the plan's `START HERE — handoff` — and this file tells you how to reach it safely and what
the owner has already decided.

---

## FIRST: establish what state the tree is in

**Do this before touching anything.** There are THREE states and ONE command tells you
which you are in — that command is new as of 2026-09-21 and replaces the ad-hoc script
plus prose table that used to live here.

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py     # exit 0 only when CERTIFIED
```

It reports the live digest, the worktree, each of the four digest-bound artifact families,
and any OPEN INTENT — a record written when a batch or chain STARTS and cleared when it
finishes. That intent is what separates the two states that were previously
indistinguishable from the digests alone:

| State | Means | Do |
|---|---|---|
| `certified` | nothing in flight, worktree clean, all four families fresh | **Start THE JOB.** Do not re-run the chain; it proves nothing new |
| `awaiting_reproof` | a batch landed, the chain was never run | Run the chain in the documented order |
| `interrupted` | an intent is open, or the worktree is dirty | Read the open intent — it names what was in flight and the next step |

**The expected reading right now:**

```text
PASS tree_state: CERTIFIED
  live input digest : 3907ad23d1b84972
  mutation_proofs         fresh  150 file(s)
  release_shards          fresh  6 file(s)
  obligation_benchmark    fresh  1 file(s)
  frontend_static_render  fresh  1 file(s)
```

Also confirm the ledger, which now runs to `H-10`:

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
#  -> PASS hardening_status: 10 H-row(s) valid — 3 closed, 5 open, 1 out_of_scope, 1 ...
```

NAMED LIMITS of `tree_state`, so you keep looking: an intent is a claim, not a lock (no pid,
no heartbeat, no timeout — a live session cannot be told from one that died holding it); a
session that never calls `--begin` leaves a dirty worktree with no record of WHY; and
`--complete` is trusted, caught only in that clearing it on a stale tree still reports
`awaiting_reproof` rather than `certified`.

---

## THE JOB

The owner ruled on 2026-09-21. These supersede standing rules where they conflict, and the
full text is in the plan's `START HERE`. Read it there; the summary here is orientation only.

Your work has **two phases, in this order, and the order is load-bearing.**

### Phase A — DONE 2026-09-21, and re-proved. Do not redo it.

All four items landed and the chain was run: corpus 147/150 (three §6F survivors, all
`INVALID` on a red `capability_phase2` baseline), six shards at 0 failures, verify-release
complete, `run_all` at `scheduled=17 completed=14 failed=3 crashed=0`.

1. **Interruption-safety machinery** — `tests/tree_state.py` + `tree_state.json`, under the
   new row `H-10`, with `tree_state_certifies_a_stale_tree` DETECTED.
2. **H-row cap widened** to two digits; the typo-catching directions kept, the growth ban
   dropped, and the rule moved into `validate()` so the documented command enforces it.
3. **The §1J hints hole is closed at the root.** It had never linted a hint. Fixing only
   that field would have left eight other unread surfaces, so fields are now classified in
   both directions and an unclassified one is its own finding — which caught two more on
   its first full run. Reach 21,604 -> 73,300 texts.
4. **The four undrawn-referent nodes were FIXED, then §1M landed** at a zero baseline.
   The set was FOUR, not six; the earlier probe was scratch and its number is not
   reproducible.

**Two things Phase A found that were bigger than Phase A:** the LAB path was still serving
undrawn stems after the student path was fixed (two entry points, one rule, neither
enforcing it on the pinned path), and `formatters_reachable`'s floor of 35 was mostly
BOOKKEEPING — the exclusions generator told an eligibility refusal from a content crash by
SUBSTRING, so ~27 pairs stayed wrongly advertised. Floor ratcheted 35 -> 6.

### Phase B — the capability attestation campaign

**This is the only work that can turn a red stage green.** `judgment_reviews_5`,
`capability_phase2` AND `assertion_coverage_8` are all downstream of it.

**Attestation filing is DIGEST-FREE — verified, not assumed.** `validation_reports/judgment/`
and `validation_reports/attestation/` are deliberately outside the fingerprint (see
`mutation_proof.INPUT_FILES`' comment). A probe file written into `attestation/` left the
digest unmoved. **So the entire campaign runs without spending a single re-proof**, provided
you touch no source. That is precisely why Phase A goes first.

Owner ruled the **whole 218-finding queue is one campaign**, spanning sessions and
**resumable**. Start with the nine ripe nodes — 17 of the 67 CONTRADICTED sit here, and each
already renders content that demonstrably moved toward its clause:

```text
mat_g2_na_q4_3 (6)   fraction number-line and set models now render
mat_g1_na_q1_0 (2)   counting backward now renders
mat_g2_na_q3_0 (2)   the "5 threes" register now renders  [see §1J note below]
mat_g3_mg_q2_0 (2)   a graduated dial is now drawn (was UNANSWERABLE)
mat_g3_mg_q2_3 (2)   a graduated cylinder is now drawn (was UNANSWERABLE)
mat_g1_dp_q3_3 (2)   the pictograph is now drawn (was UNANSWERABLE)
mat_g3_na_q1_4 (1)   rounding to the nearest thousand now renders
mat_g3_mg_q2_1 (0)   estimate no longer keys a zero measurement
mat_g3_mg_q2_4 (0)   same
```

**`mat_g2_na_q3_0` changed again on 2026-09-21** (`e23a4ffe`, the §1J fix). Its renders are
newer than any prior evidence — re-attest it against what it renders NOW, not against any
recorded sample.

**How blindness works, per the owner's ruling.** You DISPATCH to a separate agent that has
neither the answer key nor your context. `tests/attester_packets.py` writes what the Attester
sees and the key it must not see; `tests/attester_file.py` turns returned verdicts into
§6F/§6G records without retyping. **Blindness is a prompt contract, not a sandbox.** You never
author a verdict, never re-file one, and never copy a v1 rationale forward — all 151 legacy
reviews are v1 and unadjudicable, and the v1→v2 migration was refused as impossible in
principle. Use `legacy_review_queue.json` to PRIORITISE, never as evidence.

**A generator fix does not clear a §6F finding.** Only a blind re-judgement does. The
2026-09-19 batch fixed seven content defects and cleared ZERO findings — the queue stayed at
218 and merely shifted kind.

---

## If you arrive mid-anything

A handoff can happen at any moment; hardware and environment failures are outside a session's
control, and the owner has ruled that "must end certified" is NOT the rule. So:

* **Shards are individually resumable.** Each receipt records its own digest. Re-run only the
  stale indices — that is a 2.5-hour saving you get by reading digests instead of guessing.
* **A surviving mutation has TWO causes** and you must tell them apart: the check is broken,
  or the plant no longer reaches the code the validator runs. Diagnose by instrumenting the
  real path, never by reading the validator and concluding it would work.
* **`INVALID — the unmutated command baseline exited 1` is a THIRD thing** and is neither.
  The runner refused to score, because the baseline was already red. Re-running cannot fix it.
* **Never re-prove `obligation_benchmark_outlives_source` while shards are running.** It
  plants into `tests/obligation_executor.py`, the module the shards spend 2.6h inside.

---

## Read this, in this order

1. **`AGENTS.md` / `CLAUDE.md`** — the Scaling Mandate, Engineering Protocols, Definition of
   Done. Verification is execution; a prediction phrased as a confirmation is a lie.
   **Note the 2026-09-21 ruling supersedes File Management's read-only rule on `validation/`.**
2. **`docs/phase2_hardening_completion_plan.md`, `START HERE — handoff`.** It opens with a
   dated block that supersedes everything below it, including the six owner rulings in full.
3. The middle of that plan for the *design* of what you implement. Design, never status.
4. **`validation_reports/HARDENING_EVIDENCE.md`**, last two entries (2026-09-20), for how the
   current numbers were obtained.

---

## Claim your row before you start

`owner` is a work-lock. Claim it, release it on commit (`unclaimed` or `released @ <rev>`).
If your session identifier embeds an H-row token, make sure it is *your own* — that check
exists because a worker once claimed H-07 while doing H-08.

```sh
PYTHONPATH=. .venv/bin/python tests/hardening_status.py     # must PASS before and after
```

`H-06` was released `@ e23a4ffe` on 2026-09-20 and stays OPEN — it holds the M2 capability
queue and must not be closed by a re-proof alone. **`H-02`, `H-05`, `H-07` and `H-08` are all
open and unclaimed.** Phase A item 2 lets you open `H-10` for the first time — the
row set can finally express one.

**Edit the ledger SURGICALLY.** `json.dumps(ensure_ascii=True)` over the whole file
renormalises `§`/`—` escapes across rows you do not own; a 2026-09-20 session produced 16
lines of collateral churn that way and had to revert. Patch the lines you mean to patch.

Every artifact you add under `validation_reports/phase2_hardening/` — including inside
subdirectories — must be claimed by some row's `proof_artifacts`, or the ledger fails.

---

## Traps that cost real time

1. **A gate can be defeated one stack frame later.** Verify at the REAL consumer, not at the
   function you edited. The orchestrator's narrowing of a list-valued bound was silently
   undone by `generate_context`; the orchestrator's own output looked correct.
2. **A rule copy-pasted into N sites will disagree with itself.** The `_number_plurals`
   register lived in SIX places; waking it up shipped "1 threes" past a green matrix, green
   compat, green render and 739 green unit tests, because the only gate that catches it runs
   in the re-proof chain. Consolidate to one definition and route it through the same helper
   the validator imports.
3. **`_generated_formatter_exclusions.py` goes stale** whenever a formatter or COMPATIBILITY
   entry changes; §2B fails loudly naming each entry. Regenerate with
   `PYTHONPATH=. .venv/bin/python3 -m scripts.regen_formatter_exclusions`. **Never hand-edit
   it** — it is derived empirically because three attempts to model the orchestrator's
   eligibility rules statically all drifted.
4. **Adding a formatter changes the obligation product**, so pinned counts in
   `tests/unit/test_obligation_executor.py` move. Confirm every added route is actually
   SERVED at several seeds *before* touching those numbers. Updating a count to match reality
   is legitimate; updating it to make a test pass is not.
5. **A shared distractor helper can be right for arithmetic and wrong for your domain.**
   `augment_distractors` refuses negatives but allows ZERO — correct for sums, and it put a
   `0 g` option against a `1 g` answer. Filter in your formatter; do not weaken a helper
   fifteen formatters share.
6. **The pre-commit hook rebuilds Graphify and stages `graphify-out/`.** Expect more files in
   the commit than you staged. It does NOT move the input digest — verify that rather than
   assume it.
7. **Do not run anything heavy concurrently.** `tests/frontend_renderer.py` writes to one
   fixed path with no PID and no lock; six call sites funnel through it. Unfixed.
8. **Cosmetic edits cost 3.4 hours.** A 2026-09-20 session realigned four import
   continuation lines AFTER completing the chain and invalidated the whole re-proof. It was
   reverted byte-for-byte rather than re-run. Once certified, touch no source you do not mean
   to change.
9. **`git commit --amend` moves the hash**, so a ledger row written as `released @ <hash>`
   before the amend points at a dangling commit. Release in a follow-up commit, not an amend.

---

## Still owner-owned — do not hand-patch around these

**`CSI-R1`–`CSI-R3`** are open owner rulings in `context_semantics_inventory.json`. `CSI-R4`
is ruled and closed.

---

## Limitations left standing — named so you keep looking

* ~~**§1J does not lint hints.**~~ CLOSED 2026-09-21. It lints them now, along with eight
  other surfaces it had never read, and an unclassified payload field is its own finding
  (`unclassified_pupil_text_1J`). STILL TRUE: §1M's deixis list is closed, so a stem that
  points in wording nobody has seen yet is not caught; §1J's mirror direction (a singular
  noun after a count of two or more) is measured and printed but does not gate; count/verb
  agreement is not checked at all; and neither reads the VISUAL payload's own labels.
* ~~**No gate catches a stem that references a display the item never draws.**~~ CLOSED
  2026-09-21 by §1M. STILL TRUE: it cannot tell whether the drawn visual is the RIGHT one —
  an item that says "look at the pictograph" and draws a clock passes §1M and is §1G's and
  §9's business — and it cannot see a display the pupil needs but the stem never mentions.
* **A DECLARED variant axis restricted by `FORMATTER_VARIANT_SUPPORT` is still unchecked on
  the orchestrator's PINNED path.** `assert_formatter_supports` is deliberately scoped to
  UNDECLARED axes, because caps, profiles and `ctx.values` do not share one vocabulary —
  widening it refused every pinned render on `mat_g2_mg_q2_0` (§2B) and 46 producible
  declarations on `mat_g1_na_q1_7` (§2I). Closing it needs sentinel resolution, per-DNA.
* **A legitimate axis value of `0`, `""` or `False` is never enforced by either path**,
  because both skip falsy values — a guard that exists only to survive `division`'s
  `remainder` name collision. No current axis uses one.
* **`fraction_model_read` cannot draw an improper fraction** (it emitted `shaded_parts=7`
  in a shape with `total_parts=3`), so `mat_g3_na_q4_6` is served by `fraction_shade`
  alone. Multi-whole support in that formatter would widen it.
* **The ANY reading of `formatter_refused_at_node` is not mutation-covered at its own
  comparison.** Proven to still catch silent substitution and consistent with production on
  the NONE and PARTIAL cases; the `wanted & allowed` boundary itself is unproven.
* **Nothing asserts a pictograph's symbol COUNT equals the table's answer.** Verified once,
  by hand.
* **`ScaleRead` geometry is proven by arithmetic on emitted attributes, not layout** — jsdom
  has no layout engine, the same blind spot §12 already names for NumberLine/BarChart.
* **The estimate-task floor gates nothing.** A sibling DNA framing estimation as rounding
  would reproduce the zero-measurement defect with every gate green.
* **§8's execution accounting is stubbed** and stays provable only against a green live
  corpus. Do not describe §8 as fully proven.
* **`comparing_ordering` and `missing_number` each declare a `visual_home` that
  `base_generator` can never read** (it reads it only for `visual_read` DNAs; both are
  `algorithmic`). Measured no-ops. Fixing them is a DNA edit that belongs to its own change.
* **The Phase 1 network guard patches ONE interpreter**, so connections opened inside
  children of `unit_tests`, `census_7` and `behavioural_matrix` are invisible; Phase 2 stages
  are unguarded; loopback is allowed. See `docs/pgen_contract.md`'s `phase1_hermetic` row.

---

## Rules this handoff will not let you skip

- **The Definition of Done is an executed `run_all` with its output shown.** It is currently
  **NOT met** and this document does not claim otherwise. A green subset is not completion.
- **Never weaken a check to make it pass.** If a gate is red, the bug is in the pipeline. The
  one exception is documented ground-truth error, reported with node ID and justification.
  (The H-row widening is such a case and is already ruled.)
- **Prove a check by executing a planted violation**, not by reading the validator.
- **Check that your mutation is not passing for the wrong reason.** A plant that edits a
  digest-bound module reds the freshness check by itself, so the command exits 1 whether or
  not your gate works. Break your own gate deliberately and confirm the marker disappears.
- **A fix at the data layer gates nothing.** Where you fix content without a gate, say so.
- **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
  the evidence log. A gate described as total is how the next agent stops looking.
- **File an Evidence section** in `validation_reports/HARDENING_EVIDENCE.md` with the exact
  commands, verbatim output, and seeds for anything found or fixed.
