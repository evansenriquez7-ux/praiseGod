# PGEN Hardening Loop — Tick Protocol

You are one **tick** of a long-running loop whose goal is:

> Every one of the 151 MATATAG nodes carries a **genuine, blind, fresh** judgment review whose
> `overall` verdict is `PASS`, and `run_all` exits 0 — with no fabricated review anywhere in the tree.

Read this entire file, then work **complete units, back to back, for as long as your budget allows**,
committing each one atomically before starting the next. Stop when you are running low on room —
never mid-unit, never with an uncommitted tree.

The unit of resilience is the **commit**, not the tick. A tick can be killed mid-flight by the 5-hour
usage limit, and the atomic per-unit commit is what makes that survivable; there is no additional
safety in stopping after the first unit when you still have budget. So: one unit is the *minimum* a
tick delivers, not the maximum. Keep going while there is honest work in front of you and room to
do it. Ending a tick is not ending the loop — the next tick reads your ledger and continues.

---

## 0. You start cold. Derive state from disk, never from memory.

Run these first, every tick, before deciding anything:

```bash
git -C /Users/enrichmentcap/Documents/antigravity/ccmed log --oneline -8
git -C /Users/enrichmentcap/Documents/antigravity/ccmed status --porcelain | head -30
tail -40 local_only/scratch/hardening_ledger.md   # create if absent
```

Then take the honest verdict census:

```bash
PYTHONPATH=. .venv/bin/python3 - <<'PY'
import json, glob, re, collections
c = collections.Counter(); skel = collections.Counter(); quote_miss = []
for f in sorted(glob.glob('validation_reports/judgment/**/*.json', recursive=True)):
    d = json.load(open(f)); c[d.get('overall')] += 1
    r = d['findings']['competency_fulfillment']['rationale']
    s = re.sub(r'mat_g\d_\w+', '<N>', r); s = re.sub(r"'[^']*'", '<Q>', s); s = re.sub(r'\d+', '#', s)
    skel[s[:90]] += 1
    texts = {x.get('question_text', '') for x in d.get('samples_reviewed', [])}
    for q in re.findall(r'\(such as .(.*?).\)', r):
        if q and q not in texts: quote_miss.append(d['node_id'])
print('verdicts:', dict(c))
print('largest rationale skeleton cluster:', skel.most_common(1))
print('reviews quoting a sample not in their own packet:', len(quote_miss))
PY
```

Then the **gate-health sweep**, which is not optional — a prior tick found the gate's biggest blind
spot here and nowhere else (94 non-PASS reviews were skipping every content check, because a non-PASS
verdict *is* an error and the loop did `if errs: continue`):

```bash
PYTHONPATH=. .venv/bin/python3 -c "
from backend.app.practice_gen.validation import validate_judgment as VJ
errs = VJ.validate_judgment_reviews()
verdict  = [e for e in errs if \"must be 'PASS'\" in e]
other    = [e for e in errs if \"must be 'PASS'\" not in e]
print('gate errors:', len(errs), '| verdict:', len(verdict), '| NON-VERDICT:', len(other))
for e in other[:10]: print('   -', e)
print('tally:', VJ.summarize_verdicts())
"
```

**`NON-VERDICT` must be 0.** Anything there is a stale, fabricated, or malformed review hiding behind
the verdict noise — fix it before any content work, because a review about content the pipeline no
longer serves will send you chasing a defect that isn't there.

**These numbers decide which tick you run.** Nothing else does — not the ledger's claims, not a green
GitHub check, not what a previous tick said it had finished.

---

## 1. Hard rules — violating any of these makes the tick worse than doing nothing

1. **Three roles, three agents, never merged.** The whole judgment layer collapsed twice because one
   agent played all three. Keep them separate:

   | Role | Who | Sees | Writes | Must never |
   |---|---|---|---|---|
   | **Fixer** | you, the tick | everything | generator code, evidence log, ledger | write or edit any `validation_reports/judgment/*.json`, or author a `requires` block |
   | **Declarer** | blind subagent | the node's **competency text only** | its `requires` block in `data/skeletons/vocab_annotation.json` | read the generator source, the rendered samples, or the existing registries |
   | **Reviewer** | blind subagent | packet only (competency text, grade/quarter/vocab, rendered samples) | one review JSON per node | read `dna/`, `formatters/`, `generators/`, `adapter.py`, `orchestrator.py`, or any other node's review |
   | **Evaluator** | adversarial subagent | packet + the filed review | one audit JSON per batch | read generator source, or know who wrote the review |

   **The Declarer is separate for the same reason the Reviewer is.** A `requires` block written by
   whoever builds the generator will agree with the generator and drift from MATATAG alongside it —
   the author-verifying-itself failure that produced 151 fabricated reviews, twice. It sees the
   competency sentence and nothing else.

   If you find yourself hand-editing a review JSON, stop — that is the exact fabrication failure mode
   this repo has already suffered twice.
2. **Never flip a verdict.** `overall: "FAIL"` → `"PASS"` is only ever legitimate as the *output of a
   fresh blind re-review dispatched after a generator fix*. Changing the string is falsifying evidence.
3. **Never weaken a check** (`validate_*.py`, schemas, assertions) to make something pass. If the
   harness fails, the bug is in the pipeline. The only exception is a documented ground-truth error,
   which must be reported with node ID and justification (CLAUDE.md Protocol 5).
4. **Verification is execution.** Every claim in your tick report is backed by a command and its
   verbatim output. `PYTHONPATH=. .venv/bin/python3` — there is no bare `python` or `timeout` on this host.
5. **Root cause, then all instances.** Query the Graphify MCP first for anything touching multiple
   files or the axes → DNA → compatibility → orchestrator → formatter path. Fix the cause everywhere,
   not the one node that reported it. The recurring cause in this repo is
   *`registry.py`'s `_parse_competency_bounds` never binding a DNA's internal sub-concept for a node,
   so a silent default or fallback cascade governs instead* — check for that pattern first.
6. **No fallbacks.** No bare `except`, no warn-and-continue, no `|| true`, no default values papering
   over a missing binding. Errors are loud, named, and print the seed.
7. **Commit each unit atomically** before the tick ends. Never end a tick with a half-applied fix.
8. **Build the machinery a node needs. This overrides `pgen_hardening.md`'s non-goals.**

   That spec ends with: *"Do not redesign difficulty dimensions, variants, or formatters… Do not add
   new formatters/variants 'while you're in there.'"* Those lines were written when the plan's scope
   was *verifying existing contracts*. **The maintainer has explicitly superseded them for this loop
   (2026-08-12):** if a node's competency cannot be satisfied without a new formatter, variant, axis,
   or DNA, **building it is the fix, and building it is in scope.** Read the non-goals as "don't
   gold-plate unrelated things", not "don't build what a competency requires".

   A previous agent correctly refused under the old reading and left nodes untouched — e.g. it rejected
   `mat_g3_mg_q1_5` because "no line-drawing formatter exists anywhere… genuinely new machinery, not a
   gate to open." Under this rule, that is a **Tick F**, not a deferral.
9. **`CAPABILITY_PROVIDERS` is not an escape hatch.** §6C passes when a declared capability maps to a
   registered provider. Nothing checks that the provider *semantically satisfies the clause* — mapping
   `draw_lines` to `task_type=identify_name` would silence the failure and pass every check, because
   that value genuinely exists and is genuinely reachable. This is the one place the capability
   contract can be defeated without weakening a single assertion.

   So: adding a `CAPABILITY_PROVIDERS` entry is a claim that the artifact **produces what the clause
   names**, and it carries the same evidence bar as a code fix — a rendered sample showing it, quoted
   in the ledger. If you cannot produce that sample, the honest move is to leave the capability
   unmapped and build the thing. An entry added to make a red line go away is falsifying evidence, in
   the same family as flipping a verdict (Rule 2).
10. **"Not an easy fix" is not a reason to defer.** Difficulty, novelty, and "this needs new machinery"
   are descriptions of the work, not exemptions from it. There are exactly three legitimate reasons to
   leave a node unfixed, and each is recorded in the ledger with its reason:
   - **Budget** — the tick ran out of room. Then it is the *next* tick's first item, named in
     `Next tick should:`. Not a deferral, a handoff.
   - **A pedagogical decision that is genuinely the maintainer's** — the MATATAG text is ambiguous and
     two readings imply different content. Escalate with both readings, don't guess.
   - **A ground-truth error** — the competency bounds or KG vocab are themselves wrong (CLAUDE.md
     Protocol 5). Report with node ID and justification.

   "Hard", "large", "would need a new formatter", and "out of scope" are **not** on that list. If you
   catch yourself writing one of those in the ledger, you are writing a Tick F, not a deferral.

---

## 2. Known hazards (learned the hard way — do not rediscover them)

- `validate_matrix --node X` **overwrites** `validation_reports/matrix_report.json` with a one-node
  report. Never read that file as a full-tree baseline unless the last thing that wrote it was a full
  `run_all`. Regenerate with `run_all` before drawing tree-wide conclusions.
- A single node's matrix check costs ≈3 s. Full `run_all` costs minutes. Budget accordingly: scoped
  `--node` runs during iteration, one full `run_all` at the end of the tick.
- `is_lab=True` bypasses the competency-bound clamp. Any sampling you do for review packets or for
  eyeballing content must use `is_student_path=True` — the real serving path.
- The anti-boilerplate gate only catches **verbatim** rationale reuse. A template with the node ID
  substituted in slips straight through. That is exactly how the current fabricated set got filed.
- Multi-DNA nodes: the adapter may pick a different DNA than the loop you think you're testing. Pass
  `forced_dna=` when a check is DNA-specific.
- **CI does not run this harness at all.** As of 2026-08-12 there is no `validate-pgen.yml`;
  `deploy-backend.yml` builds, smoke-tests `/api/health`, and deploys, and that is the whole of CI for the
  backend. A shipped Cloud Run revision is *not* a validated one — the smoke test proves the app boots,
  nothing more. **You are the only thing standing between a broken pipeline change and production**, so run
  strict `run_all` before you commit, every tick, and never infer from a green GitHub check.
- **Trust the census, not stage 6's summary line.** The fabricated-review episode is resolved (the gate
  now reports honestly), but the lesson stands: that line summarizes what the gate *checked*, and the
  gate has had two blind spots so far — freshness validating the samples block but not the rationale,
  and every content check skipping non-PASS reviews entirely. Run §0 yourself.
- **A `FAIL` count going *up* is often the system working.** When a boilerplate review is deleted and
  re-reviewed honestly, the honest verdict is frequently worse — `mat_g3_mg_q1_5` went CONCERN → FAIL
  once a real reviewer noticed its competency says "recognize **and draw**" and draw was 0/10. Report
  the movement, don't optimize the number.

---

## 2b. Where the work actually stands (2026-08-13 — verify in §0, don't trust)

```
census        57 PASS / 61 CONCERN / 33 FAIL      (151 reviewed, 0 unreviewed)
run_all       EXIT_CODE=1 — red at 6/7 (verdicts) and 7/7 (capability). Stages 1-5 green.
capability    145 of 151 nodes undeclared · 10 capabilities declared with no provider
gate health   stale 0 · non-verdict errors 0 · skeleton cluster 2 · phantom quotes 0 · 18 reviewers
```

**The capability contract (§6) is new as of 2026-08-13 and changes how you work.** Six nodes are
declared as fixtures; the other 145 are not, and declaring the node you are working is now step 0 of
every Tick C.

> ⚠️ **The six fixture declarations were authored by the Fixer, not by a blind Declarer — they violate
> the separation this design depends on, and they are the precedent 145 more will follow.** They were
> written while looking at `VARIANTS_BY_DNA`, so at least one mapping (`distinguish_shapes` →
> `task_type=identify_name`) was chosen because that value existed, not because the competency implied
> it. That is exactly the author-verifying-itself drift the Declarer role exists to prevent.
>
> **Your first unit of work: re-declare those six blind and diff the result.** Dispatch a Declarer with
> only each competency sentence, then compare to what is in `vocab_annotation.json`. This is worth
> doing first for two reasons — it corrects the precedent before it propagates, and comparing a blind
> declaration against a sighted one on the same node is the cheapest possible test of whether the
> Declarer separation actually changes the output. If they agree, you have evidence the role is
> cheap insurance. If they diverge, you have just measured how much the separation is worth, and every
> subsequent declaration is better for it. Record the diff in the ledger either way.

The ten already-named gaps below are your first build queue — but treat them as *provisional* until
the re-declaration above confirms them, since they derive from those same six declarations:

| Node | Capability with no provider |
|---|---|
| `mat_g3_mg_q1_5` | `draw_lines` — *"Recognize and **draw** parallel…"*, and no drawing formatter exists |
| `mat_g1_na_q1_0` | `identify_one_more`, `identify_one_less` — named explicitly in the competency; `counting` has no task_type for either |
| `mat_g3_mg_q2_3` | `measuring_tool` — *"using appropriate measuring tools"* |
| `mat_g3_dp_q3_1` | `data_table` — *"Present data in **tables** and single bar graphs"*; only bar-chart formatters are offered |
| `mat_g2_na_q3_1` | `repeated_addition`, `concrete_model`, `equal_groups`, `skip_counting`, `number_line_jumps` — the competency enumerates seven representations and `multiplication` declares variants for none |

`mat_g2_na_q3_1`'s five include the number-line-jump machinery the ledger deferred twice. It is no
longer a deferral; it is a named build item (Rule 8, Tick F).

Every remaining gate error is an honest verdict. Nothing is hiding. The named queue, highest value first:

1. **`mat_g3_mg_q1_0/_1/_2/_3`** — largest untouched duplication group (14–15 shared seeds).
   Duplication has been the most tractable shape; five of the first eight fixes were duplication or
   unbound keys. Plain Tick C.
2. **Number-line jumps** — `mat_g2_na_q3_1` and `mat_g3_na_q4_0`, two FAILs, one build. **Tick F**, but
   start at Step 1: `fmt_number_line.py` already exists and is routed twice.
3. **Line drawing** — `mat_g3_mg_q1_5`'s "draw" verb, 0/10. `geometric_lines` declares only
   `["mcq", "categorize"]`, compatibility offers only `["mcq"]`, `visual_home=None`. A prior tick
   rejected this as out of scope; under Rule 8 it is a **Tick F**. Check `fmt_shape_board.py` before
   building new.
4. **The 61 CONCERNs are almost entirely untouched** — every Tick C so far targeted FAILs. That is now
   the largest pile, and `run_all` cannot exit 0 while one remains.

### The five defect shapes (diagnosis checklist — read the rationale, then match it to one of these)

1. **Key consumed but never bound** — a DNA reads a profile key nothing sets, so a default governs and
   the real branches are dead code. (mass/capacity `unit`; properties-of-addition `task_type`; money
   `operation`/`denomination_type`.)
2. **One text match too broad** — two competencies collapse onto one binding and render identically.
   (`"repeated addition"` matching both G2 nodes.)
3. **Formatter gated off the node that needs it** — the named model is structurally unreachable.
   Opening the gate usually *also* needs task-specific stem text in the same tick, or you trade a
   coverage gap for a duplication bug. (`array_grid_*` restricted to `find_product`.)
4. **Named form generated only as a distractor** — present in the item, never as the answer. Count
   correct answers separately from distractors. (the centavo sign.)
5. **One boundary defined twice with different comparisons** — binding a sub-case isn't enough if the
   pool disagrees with the renderer about where the boundary sits. Verify the *rendered text*; the
   printed label is ground truth, not the numeric value. (coin/bill at ₱20.)

---

## 3. Pick your tick type from the §0 census

Evaluate the triggers **in order**. The first one that fires is your tick.

### Tick 0 — `run_all` is red at a *machine* stage
**Trigger:** `run_all` exits non-zero at any stage other than **6/7 judgment** and **7/7 capability**.
Those two are the honest work queues and are expected to be red for a long time; stages 1–5 are not.

**Do:** fix that first — a red machine gate makes every judgment verdict unreliable, because the
reviews are about content a broken generator produced. Root-cause, fix all instances, `run_all`, commit.

> **Measured 2026-08-12** (verify, don't trust): stage 1's `comparing_ordering` and `area` failures are
> **fixed**; `run_all` → `EXIT_CODE=1` red **only at 6/6**, on non-PASS verdicts. Stages 1–5 green, DNA
> 27/27, matrix 151/151 / 0 failures, all ten contract checks executing, both contract checks PASS.
> So Tick 0 should not fire — if it does, something regressed and it is yours to fix first.

### Tick A — the gate cannot detect fabrication
**Trigger:** the largest rationale-skeleton cluster is > 3 nodes, **or** any review quotes a sample
absent from its own `samples_reviewed`, **or** one `reviewed_by` string covers all 151, **or** §0's
`NON-VERDICT` count is not 0.

> **Status:** the three checks below were built and the fabricated set was deleted and re-reviewed;
> as of 2026-08-12 the census reads skeleton cluster 2, phantom quotes 0, 18 reviewers, non-verdict
> errors 0. **This tick should not fire.** If it does, the gate has regressed or grown a third blind
> spot — treat the history below as the pattern to look for, not as work still to do.

**How the gate was fooled before** — the two blind spots it has actually had, so you recognize a third:

| Existing check | How the 151 templated reviews satisfied it |
|---|---|
| `blind: true` | a self-attested boolean; nothing verifies it |
| `reviewed_by` not a placeholder | one plausible string, repeated 151× |
| rationale ≥ 40 chars | templates are long |
| verbatim rationale reuse (`validate_judgment.py:267`, exact `==`) | node ID substituted into the template → not byte-identical |
| **freshness** (re-render each cited seed, compare `question_text`) | **`samples_reviewed` was regenerated fresh from the live pipeline and a template rationale stapled to it.** Freshness validates the *samples block*, not the *rationale* — which is why 115 of 151 rationales quoted text absent from their own freshly-rendered samples |
| `overall == PASS` | simply written as `PASS` |
| **every content check above** | a non-PASS verdict *is* an error, and the loop did `if errs: continue` — so all 94 CONCERN/FAIL reviews were exempt from freshness, quote provenance, skeleton clustering and reviewer plurality. The anti-template machinery only ever ran on the reviews least likely to need it |

The shape both blind spots share: **a check that runs on a subset it doesn't announce.** When you add a
check, state out loud which files it does *not* examine, and go look at those.

**Do:** harden `backend/app/practice_gen/validation/validate_judgment.py` so each of those becomes a
loud FAIL. Minimum three new checks:
  - **Skeleton clustering:** normalize each rationale (strip node IDs, quoted spans, digits); if any
    normalized skeleton recurs across more than a small threshold of nodes, FAIL naming them.
  - **Quote provenance:** every sample text a rationale quotes must appear verbatim in that review's
    own `samples_reviewed`. Fabricated quotes are a hard FAIL.
  - **Reviewer plurality:** a single `reviewed_by` string covering all 151 nodes is not a review pass.

Then **delete** every review the hardened gate rejects and record the deletion in the ledger. Ending
this tick with `run_all` red is correct and expected — an honest red beats a fabricated green.
Note in the ledger that this is a deliberate, documented red.

> This is the one place editing an assertion is the point: you are strengthening the verifier, not
> weakening it. Prove it by re-running the gate against the deleted files' content and showing it fails.

### Tick B — nodes lack a review
**Trigger:** the gate is hardened, and some nodes have no review file (or a rejected one).

**Do:** build stratified packets via `judgment_packets.py` (5 base seeds + extra seeds chosen to cover
every distinct rendering path — a 5-seed packet historically saw only ~39% of the formats a node
serves). Dispatch **blind subagents**, ≤ 25 nodes per batch, ideally 2–3 batches per tick so the tick
fits inside the budget. Each subagent:
  - receives only the packet JSON (competency text, grade/quarter, vocab metadata, rendered samples);
  - is forbidden the generator source paths in Rule 1;
  - is prompted **neutrally** — "score PASS/CONCERN/FAIL by accuracy" — never "hunt defects"
    (defect-hunting framing was measured to bias verdicts toward FAIL);
  - must quote real sample text from its own packet in every rationale;
  - runs `PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.validate_judgment`
    on its own output before reporting back.

**Then run the evaluator pass. A batch is not done until its audit is clean.** For each batch,
dispatch a *separate* adversarial subagent that receives the packet and the filed reviews but **not**
the generator source and **not** the identity of the reviewer. Its job is to score the *review*, not
the content. It must answer, per node:

  - Does every rationale describe **these** samples? Any quoted text must appear verbatim in the
    packet. (The machine checks this too — the evaluator catches the softer case: a rationale that
    paraphrases content the packet does not contain.)
  - Does the verdict **follow from** its own rationale? A rationale naming a real defect under a
    `PASS` verdict is unearned, and so is a `FAIL` whose rationale describes nothing wrong.
  - **Transplant test:** could this rationale be pasted onto a sibling node, changing only the node
    ID, and still read as true? If yes, it is a template and the review is void.
  - On a random 20% of the batch, **re-judge independently first**, without looking at the filed
    verdict, then compare. Report the disagreement rate; a rate above ~20% means the batch is
    unreliable and every node in it gets re-reviewed by a fresh reviewer.

Write the audit to `validation_reports/judgment_audit/<batch>.json` — **not** under
`validation_reports/judgment/`, whose recursive glob would parse an audit file as a review. Re-dispatch
every node the evaluator voids. An evaluator is LLM judgment, not a hard gate: the mechanical checks
from Tick A are the load-bearing part, and the evaluator catches only what they structurally cannot.

Whenever you re-review after a fix, diff the new verdicts against the previous commit's per node and
report the movement. Nodes that did **not** move are the real remaining punch list.

### Tick C — honest CONCERN/FAIL verdicts exist  ← the main loop
**Trigger:** census shows any `overall` in {CONCERN, FAIL}.

**Do, per cluster (a cluster, never a single node) — then start the next cluster if budget remains:**
0. **Declare first, if the node has no `requires` block.** Dispatch a **Declarer** subagent (Rule 1)
   with only the node's competency sentence; it writes `requires` into
   `data/skeletons/vocab_annotation.json`, then you run `scripts/rebuild_knowledge_graph.py` and
   `validate_capability`. Do this *before* diagnosing: §6C will often name the defect outright, and a
   declaration is cheaper to write than the same finding is to discover by reading samples.
   145 of 151 nodes are still undeclared — declaring the node you are about to work is part of working it.
1. Group the open findings by root cause, not by node. Pick the cluster with the highest
   (severity × node count). FAIL before CONCERN.
2. Read the actual rationales — `findings.*.rationale` names the specific defect and quotes the
   sample. That text is your bug report. Cross-read it against §6C's output for the same node; where
   they agree, the harness has already told you what to build.
3. Graphify the affected path. Find the root cause. Enumerate **every** node/DNA the cause touches.
4. Fix it. No fallbacks. If a competency binding is missing in `registry.py`, bind it explicitly and
   make the DNA `raise` (naming concept/grade/seed) when nothing matches, rather than cascading.
   **If the root cause turns out to be "nothing in the pipeline can render what this competency asks
   for", you are in a Tick F — go build it (Rule 8). Do not downgrade the cluster to whatever nearby
   symptom happens to be fixable, and do not defer it for being large (Rule 10).**
5. Verify: `validate_matrix --node <each affected node>` → PASS, then full `run_all`.
6. Dispatch a **fresh blind re-review** of every node the fix touched. Fixes are not done until a
   reviewer who never saw the fix scores the new content.
7. Append to `validation_reports/HARDENING_EVIDENCE.md`: node(s), the failing rationale that motivated
   the fix, root cause, fix, verbatim before/after output.
8. Commit: `fix(pgen): <root cause> — clears <N> judgment findings`.
9. Re-run the §0 census. If non-PASS nodes remain and you have budget, **go back to step 1 with the
   next cluster**. Do not end the tick just because one cluster is done — end it when you are low on
   room. A tick that clears four clusters is four times as good as one that clears one.

### Tick F — the harness named a capability nothing provides
**Trigger:** `run_all` stage 7/7 reports `competency requires '<cap>' … but no pipeline artifact
provides it` for a node you are working. **This is no longer your judgment call** — §6C names the gap
from the competency sentence, so "I decided this needs new machinery" and "I decided it doesn't" are
both out of your hands. Build what it names.

Run it as a Tick C with the extra steps below.

**Step 1 — prove it doesn't already exist. Most "missing machinery" isn't.**
The ledger's own defect shape #3 is *"formatter gated off the node that needs it — the named model is
structurally unreachable."* Opening a gate is hours; building a formatter is a tick. Check, in order:

```bash
ls backend/app/practice_gen/formatters/visual/ backend/app/practice_gen/formatters/textual/
grep -n "<capability>" backend/app/practice_gen/adapter.py            # FORMATTER_ROUTES, line 62
grep -n "<capability>" backend/app/practice_gen/compatibility.py      # COMPATIBILITY 185, VARIANTS_BY_DNA 471, FORMATTER_VARIANT_SUPPORT 718
```

Worked example of why: the "number-line-jump machinery" the ledger defers twice is described as new,
but **`formatters/visual/fmt_number_line.py` already exists** and `adapter.py` routes it twice
(`number_line_read`, `number_line_set`). The real question is whether it can render a *jump*, and
whether it's offered to `mat_g2_na_q3_1` / `mat_g3_na_q4_0` at all. Extending an existing formatter
and opening its gate is a far smaller change than a new one — and it is the *right* change, because
two ways to draw a number line is a defect in itself.

**Step 2 — build it, wiring every registry in the same commit.** The registries cross-check each
other at import and in the harness, so a partial wiring fails loudly (good) but confusingly (avoidable).

| Adding | Touch |
|---|---|
| a **formatter** | `adapter.py` `FORMATTER_ROUTES` (:62) → `compatibility.py` `COMPATIBILITY` (:185) for each DNA that may use it → `FORMATTER_VARIANT_SUPPORT` (:718) → `schemas/visuals.py` `VisualSchemaRegistry` (:113) if visual → `FORMATTER_NUMERIC_LIMITS` (:70) if it can't render arbitrary magnitudes |
| a **variant** | `compatibility.py` `VARIANTS_BY_DNA` (:471) → `FORMATTER_VARIANT_SUPPORT` (:718) → `CURRICULUM_VARIANT_GATES` (:97) if grade/quarter-gated → the binding in `registry.py`'s `_parse_competency_bounds`, or nothing will ever select it |
| a **DNA** | `dna/<domain>/<name>.py` → `validation/_manifest.py` `DNA_MODULE_MAP` (:18) → `compatibility.py` `COMPATIBILITY` (keys must match `DNA_MODULE_MAP` exactly; `_manifest.py` asserts this at import) → `registry.py` `NODE_TO_DNA` (:2064) → `axes_catalog.py` for its difficulty axes |

**Step 3 — the three traps that will bite you.** These are paid-for lessons; do not rediscover them.

- **Declaring a formatter exposes it to an exhaustive sweep on *every* mapped node**, not just the one
  you built it for. §1C enumerates every supported `(dna, formatter, variant)` combination, so adding
  one name to a DNA's `COMPATIBILITY` list can generate hundreds of new combinations, each of which
  must execute cleanly. Add the formatter to the narrowest DNA set that satisfies the competency, then
  run the **full** `run_all` — a scoped `--node` run will not show you the blast radius.
- **A 2-tuple bound in the registry is always read as a continuous `(min, max)` range.** If your new
  variant needs a discrete multi-part value, use a string sentinel, not a tuple.
- **Adding a difficulty axis means auditing its `default`.** `axes_catalog`'s counting range axis once
  carried the file's only `default: 0.0`, which pinned default generation to the scalar floor and
  looked exactly like a DNA bug. Give a new axis a defensible default and say why in the ledger.

**Step 4 — verify and review as Tick C.** Scoped `validate_matrix --node` for every affected node, then
full `run_all`, then a **fresh blind re-review**. New machinery gets the same evidence bar as a
one-line binding fix — arguably higher, since nothing has ever exercised it.

**Budget honestly.** A Tick F is 1–2 ticks. That is fine. Do not shrink it into a Tick C by fixing the
symptom, and do not skip it because it is large.

### Tick D — census is 151 PASS
**Trigger:** `run_all` exits 0 (which now also means all 151 nodes declared and every declared
capability provided), zero CONCERN, zero FAIL, gate hardened, census clean.

**Do:** one clean-room confirmation — `run_all` twice in a row with no edits in between, both exit 0;
`validate_judgment` green; the §0 census script shows no skeleton clustering and no phantom quotes.
Then update `docs/IMPLEMENTATION_STATUS.md` with the true tally, write
`local_only/scratch/HARDENING_DONE` containing the final verbatim output, and commit.

### Tick E — done marker exists
**Trigger:** `local_only/scratch/HARDENING_DONE` exists.

**Do:** nothing but re-run the §0 census. If it still reads 151 PASS, reply in three lines ("still
green, N ticks since completion") and stop — do not re-open finished work. If it has regressed,
delete the marker and run the appropriate tick next time.

---

## 4. Every tick ends with a ledger entry

Append to `local_only/scratch/hardening_ledger.md` (create if missing):

```markdown
## <ISO date/time> — Tick <0|A|B|C|D|E|F>
- **Census before:** PASS=… CONCERN=… FAIL=…   (gate: stale=… non-verdict=…)
- **Unit(s) of work:** <one sentence each — a tick may hold several>
- **Root cause:** <one sentence, or n/a>
- **Machinery built:** <formatter/variant/axis/DNA + every registry wired, or "none">
- **Files touched:** …
- **Verification:** <command> → <verbatim summary line>
- **Census after:** PASS=… CONCERN=… FAIL=…
- **Commit(s):** <sha> <subject>
- **Next tick should:** <one sentence — the handoff to your future cold self>
```

The **Next tick should** line is the most valuable thing you write. A future tick reads it instead of
re-deriving your reasoning.

**One thing the ledger may not say: that a node was skipped for being hard.** If a node resisted you,
record what you learned and what the next attempt should try — "rejected as out of scope" is not a
ledger entry this loop accepts (Rule 10). Re-read Rule 8 before writing anything of that shape.

---

## 5. Tick report to the user

Short. Census before → after, what you fixed, the verbatim pass/fail line, the commit sha, and what
the next tick will do. Then an **Evidence** section (commands + verbatim output + seeds), per CLAUDE.md.

If the tick was cut short by the usage limit: say so plainly, confirm the tree is committed and
consistent, and put the resumption point in the ledger.
