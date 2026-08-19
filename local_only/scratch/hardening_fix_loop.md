# Hardening fix loop — run the pipeline, then fix what it finds

You are one tick of a loop whose job is to **empty the work queue honestly**. The harness is now
trustworthy; the remaining work is content and providers, not checks.

## Step 0 — Preflight. Always. Roughly one second.

```bash
PYTHONPATH=. .venv/bin/python3 scripts/hardening_supervisor.py --reap
```

`--reap` is not optional. Orphaned `multiprocessing` workers survive their parent, keep burning a core
each, and are invisible to any pattern matching the job name — 14 of them once accumulated 59.7
core-hours on a 4-core host and starved everything else to the point that healthy runs looked
deadlocked. Judge liveness by the **process tree's** CPU, never a parent's own: a pool parent idles by
design.

Act on the verdict: `0 IN_FLIGHT` → report and stop, never start a competing run. `40 HUNG_UNREAPED` →
re-run with `--reap`. `30 NEEDS_HUMAN` → report and stop. `10 RESUME` → continue below.
`20 NOTHING_TO_DO` → three lines and stop; do not invent work.

Then read `local_only/scratch/hardening_loop_prompt.md` — the durable protocol (hard rules, hazards,
§0 census, tick types, blind roles). It carries no dated state, so nothing in it expires. Dated state
lives in `local_only/scratch/hardening_ledger.md`. **Run §0 yourself regardless**; where your
measurement disagrees with any file, yours wins and the ledger records the drift.

## Step 1 — Launch the harness in the background, then work while it runs

```bash
PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.run_all > <log> 2>&1 &
```

~35–40 minutes. Never in the foreground, never left outstanding at tick end — read its exit line or
kill it and say so. Iterate with `validate_matrix --node <id>` (~3 s) while it runs.

**The goal is `run_all` exit 0, and the gate is what makes that mean something.** Exit 0 was reached
dishonestly three times, so every fast route to it is now closed by a check: §6D (no generic formatter
as provider), §6F (no unattested claim, no contradicted verdict, no stale attestation), §5 (no
fabricated or templated review). Within a tick, **the failure count is the work queue, not the score** —
it can only be lowered by weakening something, and that is forbidden. Track progress by coverage
(`attested N/787`), which no weakening can move.

## Step 2 — The queue, in priority order, and how to fix each kind

### Rule of sequencing — read this before picking anything

**Fixing a generator invalidates both the judgment review and the attestation for every node it
touches.** §5 freshness re-renders cited seeds; §6F freshness re-renders `packet.samples_judged`. Both
go loud when content moves. So:

- **Never attest a node you are about to change.** You will pay for it twice.
- The natural cycle per node cluster is **attest → fix what it surfaces → re-attest once**. Attesters
  find defects no machine check can, so attestation is how you *discover* the work, not a formality
  after it.
- After any content fix: re-run `validate_matrix --node`, dispatch a **fresh blind re-review**, and
  **re-attest** the node. A stale verdict is not evidence.

### (1) CONTRADICTED — a blind Attester ruled NOT_PROVIDED and the table still claims it

Highest priority: the pipeline is asserting something a blind party has already refuted.

**Fix:** build the artifact that renders what the clause names, then re-attest — *or* delete the entry
and let §6C report the honest gap (that is a Tick F work item, not a defeat).
**Forbidden:** re-filing the verdict, editing the record, deleting the record, or re-registering the
entry under another name. If you believe the Attester was wrong, dispatch a *fresh* Attester on a
fresh packet and record both verdicts — never overwrite one.

### (2) Content defects surfaced by Attesters — the highest-value findings in the tree

These are wrong answers reaching students, and **no machine check catches any of them**. Two of the
first two batches each contained a genuine mathematical error on a node whose judgment review is a
filed PASS. Treat every one as a Tick C.

Currently open (all found unasked, all still unfixed):

| node | seeds | defect |
|---|---|---|
| `mat_g3_dp_q3_4` | 64 | *"3 yellow, 1 red, 1 green — which color is LEAST likely?"* keyed **'red or green'**. Red and green are equally likely, so a student answering "red" is **marked wrong for a correct answer**. Singular "Which color" contradicts a disjunctive key. |
| `mat_g3_mg_q1_5` | 78, 91, 118, 127 | `intersecting lines` offered as a distractor against keyed `perpendicular lines` — but perpendicular lines **are** intersecting lines, so the distractor is not wrong. |
| `mat_g2_mg_q4_3` | 42, 57, 78, 118 | Stem subject is a bare "It" with no antecedent. Binary question ("straight or curved line?") against a four-option set containing two *surface* labels — question and options disagree. |
| `mat_g1_mg_q4_0` | 78 | *"Which direction is clockwise?"* is a vocabulary definition on a competency about identifying position after rotation: no object, no turn, no initial facing direction. |
| `mat_g2_mg_q4_3` | 103 | "A box has six faces that are each a flat square" describes a cube, not a box. |

**Fix:** root-cause it in the generator (Protocol 2 — fix every instance of the cause, not the one
seed), print the seed in any new failure message, re-run the node, then re-review **and** re-attest.
**Forbidden:** editing the rendered sample, special-casing the seed, or narrowing the competency.

### (3) Coverage skew — a generator defect, not a review artifact

Ten seeds routinely yield ~6 distinct stems (`mat_g1_mg_q4_0`: 11≡64≡103, 42≡91, 57≡127). Within that,
clauses ride single seeds: **counter-clockwise appears in 1 of 10**, `most likely` in 1 of 10, the
comparative `more likely` **never**, and RIGHT is never an initial facing direction. A student can
complete a full set having met a named sub-case once.

**Fix:** widen the generator's sampling so every clause the competency names is reachable at a
defensible rate. **Forbidden:** declaring it fine because the clause is technically exhibited.

### (4) §6D wildcards — 59 findings across 15 nodes

The entry names only `mcq`/`cloze`/`true_false`/`error_detect`, which 27 of 28 DNAs offer, so it
discriminates nothing. Worst first: `mat_g1_mg_q4_0` (8), `mat_g2_mg_q4_3` (7), `mat_g3_dp_q3_4` (6),
`mat_g2_mg_q1_2` (5), `mat_g3_dp_q3_0` (5).

**Fix:** point the entry at the artifact that actually produces what the clause names — a variant, a
specific formatter, a bound that genuinely carries a numeric ceiling. If none exists, **build it**
(Rule 8: building it *is* the fix, and "needs new machinery" is not a deferral), or delete the entry
and let the gap be reported.
**Forbidden:** adding a second generic formatter; renaming; widening `COMPATIBILITY` so a generic
name looks specific. Note a PROVIDED verdict does **not** license keeping `mcq` — §6F asks whether the
content does the thing, §6D asks whether the registered provider is real. Both must pass.

### (5) §6E — `bounds` is the live wildcard, and it is not yet built

Stripping `bounds` moves the count by 15: `mat_g1_na_q1_5` ×7, `mat_g2_na_q1_5` ×4, `mat_g3_na_q1_2`
×4 ride the 27-key catch-all alone. Rule 9: *"A `bounds` list is a numeric-ceiling provider and nothing
else."* Only `up_to_10th`/`up_to_20th`/`up_to_100th` are plausibly ceilings; `objects`,
`describe_position`, `1st`, `2nd`, `3rd`, `ordinal_numbers` are not.

**Build the check.** There are exactly **2 distinct bounds lists** in the table (one 27-key list on 483
providers, one empty), so discriminate on **shared-ness** — a list carried verbatim by 483 entries
makes no claim about any particular capability. **Do not threshold on list length**;
`test_bounds_length_is_never_the_discriminator` pins that and must keep passing. Ship it as §6D and
§6F were: `pgen_contract.md` row + `CONTRACT_CHECKS` entry (the two-direction lint fails otherwise) +
unit tests + a planted mutation proved caught by name.

### (6) UNATTESTED — 757 records across 147 nodes

Nobody blind has judged whether the pipeline's output exhibits these clauses. **Measured throughput:
25 clauses across 3 nodes in 151 seconds, 0 tool uses.** ~30 dispatches remain.

**Do:** build packets with `tests/attester_packets.py --node A --node B --node C --packets P --key K`,
pass the samples **inline** in the subagent prompt (so blindness needs no sandbox), state Rule 1's
forbidden-path list verbatim, frame neutrally ("do these items exhibit what this clause names?" —
never "find the defects", which biases toward FAIL). File one record per node under
`validation_reports/attestation/`, **including `packet.node_id` and `packet.samples_judged`**, or §6F
fails the batch as uncheckable. Ask the Attester to report any content problem it notices — that is
where the math errors came from.
**Forbidden:** attesting on `is_lab=True` samples (the competency clamp is bypassed, so a Lab sample
can exhibit a capability the student path can never reach); writing a verdict yourself; batching more
than 25 clauses.

## Step 3 — Every tick ends the same way

- Tree committed, each unit atomic. Never mid-unit, never uncommitted.
- **No background job outstanding.** Read `run_all`'s exit line or kill it and say so.
- `validation_reports/HARDENING_EVIDENCE.md` entry for any commit touching
  `backend/app/practice_gen/` or `data/skeletons/`, with verbatim command output (Rule 7).
- Ledger entry (protocol §4) ending in a specific `Next tick should:`.
- Re-run the supervisor so `hardening_status.json` is current for the next wake-up.
- Report **both** movements: findings *and* coverage. Failures rising while coverage rises is
  progress. Failures falling while coverage is flat is the signature of all three past defeats, and
  reporting a falling failure count on its own is how each of them was presented.

## Never

Weaken a check, widen a provider, flip a verdict, rewrite a test around its own failure, narrow a
declaration, edit a review or an attestation record, or special-case a seed. If a check fails, the bug
is in the pipeline. The only legitimate reasons to leave something unfixed are budget (then name it in
`Next tick should:`), a genuine pedagogical ambiguity that is the maintainer's call (escalate with
both readings), or a ground-truth error in the curriculum data (report with node ID and
justification). "Hard", "large", and "needs new machinery" are none of those.
