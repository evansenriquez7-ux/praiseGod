# PGEN Hardening — Gemini & Antigravity CLI Tick Protocol

> "Praise God"

You are one **tick**: a single autonomous agentic invocation (running headless via `scripts/gemini_hardening_runner.sh` or in an Antigravity CLI session). You start cold every time — the ledger is your only memory, and **a commit is the only work that survives you**. §13 is the full contract with the runner; read it before you plan the tick, not after.

## The Goal, and Why Exit 0 Alone is Not It

> Every one of the 151 MATATAG nodes carries a genuine, blind, fresh judgment review verdicted `PASS`;
> every node declares what its competency requires and the pipeline genuinely provides it; and
> `run_all` exits 0 — with no fabricated review, no wildcard provider, and no test rewritten around its
> own failure.

Exit 0 is the definition of done (`AGENTS.md`) and it has been reached dishonestly **three times**: twice by fabricated reviews, once by a provider table where a generic formatter satisfied every clause. The answer to a gameable goal is not a different goal — it is a gate that cannot be cheaply satisfied. Each contract check is a claim that used to be taken on trust:

| Check | What it stopped being possible to fake |
|---|---|
| **§5 skeleton clustering / quote provenance / freshness** | A template review with the node ID substituted in. |
| **§6A / §6B** | Inventing a requirement, or omitting the one you cannot satisfy. |
| **§6C** | Pointing a capability at nothing. |
| **§6D** | A generic textual formatter (`mcq`, `cloze`, etc.) satisfying every clause on every node. |
| **§6F CONTRADICTED / UNATTESTED / freshness** | Re-registering what a blind Attester rejected; a claim nobody blind examined; an attestation about content that no longer renders. |
| **§6G** | A templated all-`PROVIDED` attestation batch. |

**This harness is the foundation grades 4–10 get built on.** A gate that lets one bad claim through certifies the *method* that will produce every later grade. Closing a hole in the harness is never a detour from the content queue.

**The failure count is the work queue, not the score.** It can always be lowered by weakening something. Three numbers cannot, because the party producing each cannot see what would be weakened:
1. Capabilities with a blind Attester verdict.
2. Nodes with a fresh blind review.
3. Gates with a planted mutation actually caught.

**Report both movements, always.** Failures rising while coverage rises is progress. Failures falling while coverage is flat is the signature of all three past defeats.

**Where state lives — this file is not it.** This file is durable protocol only: rules, hazards, procedure. Current state has exactly one home each:

| Artifact | Holds | Changes |
|---|---|---|
| **this file** (`local_only/scratch/gemini_hardening_loop_prompt.md`) | Rules, hazards, procedure | Rarely |
| `validation_reports/hardening_ledger.md` | Current state and the work queue (`Next tick should:`) | Every tick |
| `local_only/scratch/hardening_status.json` | Machine snapshot for the cheap check — **a claim, not evidence** | Every supervisor run |
| `validation_reports/HARDENING_EVIDENCE.md` | Verbatim command output — the receipt an auditor reads | Every pipeline commit |

**Every number you act on, you measure (§2).** Where your measurement disagrees with anything written anywhere — this file, the ledger, the status file, a previous tick's report — **yours wins**, and the ledger records the drift.

---

## 1. Preflight — Always (~30 Seconds)

Run the supervisor with `--reap` before making any decisions:

```bash
PYTHONPATH=. .venv/bin/python3 scripts/hardening_supervisor.py --reap
```

`--reap` is mandatory. Orphaned `multiprocessing` workers survive their parent and burn cores. Judge liveness by the **process tree's** CPU, never a parent's own.

- **`10 RESUME`** $\rightarrow$ Continue, with two conditions:
  - If the tree is **MODIFIED**, you are *resuming an interrupted tick*. Read `git diff` first, then make one explicit choice and name it: **finish** that unit (verify, commit) or **`git restore`** it. Never stack new work on a half-finished unit.
  - If the `why` names an **unevaluatable capability contract**, that is a Class C repair and **this tick's only unit** — §2 can measure nothing until it is fixed.
  - Otherwise your starting point is the ledger's `Next tick should:`, which the supervisor prints.
- **`0 IN_FLIGHT`** $\rightarrow$ A watched process is alive. Find out whose: `ps -o pid,ppid,etime,time,args -p <pid>`.
  - **A `run_all` this loop left behind:** Do not start a second one — attach instead: `ls -t local_only/scratch/run_all_*.log | head -1`, wait for the exit line, record it, continue from `Next tick should:`.
  - **Anything you cannot account for:** Report and stop. Never start a competing run.
- **`20 NOTHING_TO_DO`** $\rightarrow$ Every band is zero. Run the §10 Green Audit; do not invent work.
  - This verdict now covers stages 6, 7 and 8. Before 2026-08-26 it fired on stage 8 alone,
    so it could have declared "no work" with 575 stale reviews and a live §1C failure open.
- **`10 RESUME` naming `§1 matrix evidence is STALE/PARTIAL/MISSING`** $\rightarrow$ the
  queue is not measurable. Refreshing stage 6 is this tick's only unit:
  `PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.validate_matrix`.
- **`40 HUNG_UNREAPED`** $\rightarrow$ Re-run the command with `--reap`.

---

## 2. Measure the Queue — Never Skipped, Never Remembered

Run the supervisor. It measures **every band** — §1 (matrix), §5 (judgment), §6
(capability) — and refuses to report a band it could not measure as zero:

```bash
PYTHONPATH=. .venv/bin/python3 scripts/hardening_supervisor.py --reap
```

It prints, and writes to `local_only/scratch/hardening_status.json`:

```
  QUEUE (all bands) : 735   <- the work queue, not the score
    §1 matrix  (6/8): 2
    §5 judgment(7/8): 575
    §6 capability(8/8): 158
  §1 matrix evidence: FRESH (151/151 nodes covered)
```

**If `§1 matrix evidence` is not FRESH, the queue is not measurable.** MISSING, PARTIAL,
STALE or UNREADABLE all mean stage 6 has no current evidence — and stage 6 owns the §1
content-correctness checks, the band that outranks everything else here. Rebuild it
before trusting any count:

```bash
PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.validate_matrix
```

Why the supervisor rather than a hand-rolled script: until 2026-08-26 §2 measured stages
7 and 8 only, by calling `validate_judgment` and `validate_capability` directly. Stage 6
was absent from the number, so a live §1C `empty_execution_matrix` on `mat_g3_na_q3_1` —
a node that renders no problems at all and would still report PASS — sat unqueued through
455 consecutive ticks. A queue that omits a band cannot report that band as outstanding.

---

## 3. Priority & Campaign Handling

Work the first non-zero band unless overridden by a Campaign:

0. **§1 matrix findings — content correctness. Outranks everything, campaigns included.**
   A node that renders nothing, an answer key that disagrees with its own stem,
   vocabulary from a later grade. These are defects reaching students. **If §1 is
   non-zero, or its evidence is not `FRESH`, that is this tick's work no matter what
   campaign is named.** This band was absent from this list until 2026-08-26, which is
   why a live `empty_execution_matrix` on `mat_g3_na_q3_1` went unqueued for 455 ticks.
1. **§5 stale / malformed reviews.** A review about content the pipeline no longer produces is noise and must be refreshed.
2. **§6F CONTRADICTED** — A blind Attester ruled `NOT_PROVIDED` and the table still claims it.
3. **Live content defects surfaced by Attesters** (Appendix A). Wrong answers reaching students.
4. **§6F stale attestations** $\rightarrow$ **§6D wildcards** $\rightarrow$ **§6F UNATTESTED**.

**A campaign directs ORDER, never SCOPE.** It may reorder bands 1-4 among themselves. It
may never defer band 0, and it may never place a lower-priority band above a
higher-priority one indefinitely. The 2026-08-24 run took a campaign aimed at §6F
UNATTESTED — **priority 4 of 4** — and let it hold the loop for 30 hours while §5 (557
findings, priority 1) and §1 (a live content defect, priority 0) received no work at all.
Driving the lowest band to zero also *manufactured* higher-priority work: §6F
CONTRADICTED rose 31 → 83 as attestation coverage grew, and every one of those was then
deferred by the same campaign that created it.

### Campaign Override
A campaign arrives via `HARDENING_TICK_PROMPT` (e.g. `Campaign: work the §6F attestation backlog...`). If specified:
- That campaign's target band goes first.
- Deferred bands (e.g. §5 stale or §6F CONTRADICTED) are **deferred, not skipped**: every ledger entry must name both with their current re-measured counts.

#### When the campaign's target band reaches zero — THE CAMPAIGN IS OVER
**Fall through to the default priority order above and work the first non-zero band.**
Do not re-measure and write a ledger entry about having nothing to do. Say in that
tick's ledger entry that the campaign is complete and which band you moved to.

This clause exists because it was missing. On 2026-08-24 a campaign targeting §6F
UNATTESTED — priority **4 of 4** — drove that band to zero at tick 33. The campaign then
pinned work to an empty band while the supervisor, counting the global queue, kept
answering RESUME. Neither condition could end: the agent could not work a deferred band,
could not stop, and (per Rule 10) could not escalate. The only legal act left was to
re-measure and write a ledger entry, which it did **455 times over 30 hours**, at a cost
of 112M tokens and the week's quota, while §5 stale (557 findings, priority 1) received
no work at all.

Both runners now detect this mechanically and end the run after
`HARDENING_NOOP_TICK_LIMIT` (default 12) consecutive ticks that commit nothing but a
ledger entry. That backstop is not a substitute for this clause — it stops the bleeding;
falling through is what actually keeps the work moving.

#### Campaign exhaustion — a campaign directs order, never scope

**The moment the campaign's target band measures zero, the campaign is complete and no
longer in force.** Fall through to the default priority list above and work the first
non-zero band. You do not need a new prompt, and you do not wait for one.

This clause exists because its absence cost a 40-hour run. On 2026-08-24 a campaign
targeted §6F UNATTESTED — priority 4 of 4. That band hit zero at tick 33. The supervisor
still said `RESUME` (it counts every band, and 735 findings stood), but the campaign
pinned work to a band with nothing in it, and §12 had removed the escalation path. The
only legal act left was to re-measure and write a ledger entry saying there was nothing
to do. **The loop did exactly that 455 times**, burning 109M tokens and the weekly quota,
while priority band 1 — 557 stale reviews — received no work at all.

So, mechanically:

1. Campaign band non-zero → work it.
2. Campaign band **zero** → campaign over; work the first non-zero band in the default order.
3. **Every** band zero → that is the §10 Green Audit condition. Run it. Do not idle.
4. A tick whose only output is a ledger entry saying the queue could not be worked is a
   **failed tick**. Say so in the ledger in those words, and say which rule blocked you.
   The runner independently counts these and ends the run after
   `HARDENING_NOOP_TICK_LIMIT` (default 12) consecutive ones.

**No campaign may defer §1.** §1 matrix findings are content-correctness failures — a node
that renders nothing, an answer key that disagrees with its stem, vocabulary from a later
grade. They outrank every other band and every campaign. If §1 is non-zero, or its
evidence is not `FRESH`, that is the tick's work regardless of what campaign is named.

---

## 4. Hard Rules & The 4 Blind Roles

**Never merge the Fixer with any blind role.**

| Role | Environment / Model | Sees | Writes | Must Never |
|---|---|---|---|---|
| **Fixer** | Main Agent (Gemini 3.7 Flash High) | Everything | Generator code, evidence log, ledger | Write/edit review JSONs, author `requires` blocks, or attest its own table entries. |
| **Declarer** | Subagent (`Model: "pro"` — Gemini 3.1 Pro Low) | Competency text **only** | `requires` / `requires_ignore` in `vocab_annotation.json` | Read generator code, rendered samples, diffs, or registries. |
| **Attester** | Subagent (`Model: "pro"` — Gemini 3.1 Pro Low) | Capability clause + N rendered student-path samples | `PROVIDED` / `NOT_PROVIDED` + seed citations | Read `CAPABILITY_PROVIDERS`, generator code, or know the node ID. |
| **Reviewer** | Subagent (`Model: "pro"` — Gemini 3.1 Pro Low) | Packet JSON only (competency, vocab, rendered samples) | Review JSON (`overall`, findings) | Read `dna/`, `formatters/`, `adapter.py`, or sibling reviews. |
| **Evaluator** | Adversarial Subagent (`Model: "pro"` — Gemini 3.1 Pro Low) | Packet JSON + filed review JSON | Audit JSON | Read generator code or know who wrote the review. |

### Subagent Invocation Standard
- Use `invoke_subagent` with `Model: "pro"` (Gemini 3.1 Pro Low) in batches of $\le 12$ nodes or $\le 25$ clauses.
- State the forbidden paths verbatim in the subagent prompt.
- **Reviewer Plurality**: No single `reviewed_by` identity may cover $> 25$ nodes repository-wide.

---

## 5. Unit Classification (Class A / B / C)

| | **Class A — Generation** | **Class B — Records** | **Class C — Harness** |
|---|---|---|---|
| **Touches** | `backend/app/practice_gen/` (except `validation/`), `data/skeletons/` | `validation_reports/`, `docs/`, ledger | `backend/app/practice_gen/validation/` |
| **Examples** | DNA/adapter/formatter fixes, new machinery | Attestation batches, re-reviews, evidence logs | Contract checks, validators |
| **Can Move** | Every stage 1–7 | Stages 6 and 7 only | Target stage & two-direction lint |
| **Verification** | **Full `run_all` before commit** | Fast §2 check (~17s) | Target validator + fast unit tests + mutation check |

Class classifier check:
```bash
GEN=$(git status --porcelain -- backend/app/practice_gen/ data/skeletons/ | grep -v 'practice_gen/validation/')
HARNESS=$(git status --porcelain -- backend/app/practice_gen/validation/)
if [ -n "$GEN" ];     then echo "CLASS A — generation touched, full run_all REQUIRED:"; echo "$GEN"; fi
if [ -n "$HARNESS" ]; then echo "CLASS C — harness touched, mutation + unit + lint REQUIRED:"; echo "$HARNESS"; fi
if [ -z "$GEN$HARNESS" ]; then echo "CLASS B — stages 1-5 cannot have moved"; fi
```

---

## 6. `run_all` Management

- **Class B and Class C ticks run NO `run_all` at all.** Name the skip in the ledger with the classifier output.
- **Class A ticks run it in this sequence:**
  1. Verify scoped and cheap first: `validate_matrix --node <id>` (~3s) and `check_blast_radius.py --dna <name>`.
  2. **Freeze pipeline edits.** No generator code changes while `run_all` executes.
  3. Launch in background:
     ```bash
     PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.run_all > local_only/scratch/run_all_$(date +%m%d_%H%M).log 2>&1 &
     ```
  4. Spend the wait window doing Class B work (attestations, reviews, documentation).
  5. Read the exit line before committing. Never leave background runs outstanding.

---

## 7. Defect Taxonomy & Mechanical Tools

### §6F UNATTESTED (Attestation Workflow)
1. **Build Packet**:
   ```bash
   python -m tests.attester_packets --node <NODE_ID> \
       --packets local_only/scratch/attester/batch.json \
       --key     local_only/scratch/attester/batch.key.json
   ```
2. **Dispatch Blind Attester**: Spawn blind `pro` subagent passing packet samples inline. Prompt: *"Do these items exhibit what this clause names? Return PROVIDED or NOT_PROVIDED with seeds showing it."*
3. **File Verdict Mechanically**:
   ```bash
   python tests/attester_file.py \
       --packets  local_only/scratch/attester/batch.json \
       --key      local_only/scratch/attester/batch.key.json \
       --verdicts local_only/scratch/attester/batch.verdicts.json \
       --batch-prefix batch_$(date +%m%d) \
       --attested-at $(date -u +"%Y-%m-%dT%H:%M:%SZ") \
       --tool-uses 0 \
       --samples-delivery "inline prompt" \
       --action-provided "Left registered; no change." \
       --actions local_only/scratch/attester/batch.actions.json
   ```

### §6D Wildcards
- Generic textual formatters (`mcq`, `cloze`, `true_false`, `error_detect`) can **never** be providers for representation/model capabilities.
- Point the capability at the concrete visual/construct artifact or build the missing machinery.

### §5 Stale Reviews
- Rebuild packet: `python -m backend.app.practice_gen.validation.judgment_packets --node <id>`.
- Dispatch fresh blind Reviewer subagent (`Model: "pro"`).
- File new review; audit with Evaluator subagent.

---

## 8. Building Machinery (Rule 8 / Tick F)

When a competency requires a new formatter, variant, difficulty axis, or DNA:
1. **Prove it doesn't already exist** in `formatters/visual/` or `formatters/textual/`.
2. **Wire all 5 registries atomically in the same commit**:
   - `adapter.py` (`FORMATTER_ROUTES`)
   - `compatibility.py` (`COMPATIBILITY`, `VARIANTS_BY_DNA`, `FORMATTER_VARIANT_SUPPORT`)
   - `schemas/visuals.py` (`VisualSchemaRegistry` if visual)
   - `registry.py` (`_parse_competency_bounds`, `NODE_TO_DNA`)
   - `validate_capability.py` (`CAPABILITY_PROVIDERS`)
3. Run Safety Net 1 (Registry Cross-Audit) and Safety Net 2 (Blast Radius Diff).

---

## 9. Known Hazards & 5 Defect Shapes

1. **Key consumed but never bound** — DNA reads a profile key nothing sets, so defaults govern.
2. **One text match too broad** — Two competencies collapse onto one binding and render identically.
3. **Formatter gated off the node that needs it** — Named representation is structurally unreachable.
4. **Named form generated only as a distractor** — Appears in options, never as keyed answer.
5. **One boundary defined twice with different comparisons** — Pool and renderer disagree on boundaries.

---

## 10. The §10 Green Audit (Before Believing Exit 0)

When `run_all` exits 0 or the queue reaches 0:
1. **Interrogate reference data by deletion**:
   ```bash
   PYTHONPATH=. .venv/bin/python3 - <<'PY'
   import copy
   from backend.app.practice_gen.validation import validate_capability as VC
   P = VC.CAPABILITY_PROVIDERS
   GENERIC = {'mcq', 'cloze', 'true_false', 'error_detect'}
   orig = copy.deepcopy(P)
   base = len(VC.validate_capability_declarations())
   for v in P.values():
       if 'formatters' in v:
           v['formatters'] = [f for f in v['formatters'] if f not in GENERIC]
   stripped_fmt = len(VC.validate_capability_declarations())
   P.clear(); P.update(copy.deepcopy(orig))
   for v in P.values():
       v.pop('bounds', None)
   stripped_bounds = len(VC.validate_capability_declarations())
   P.clear(); P.update(copy.deepcopy(orig))
   print('providers:', len(P))
   print('capability problems reported          :', base)
   print('...if generic formatters provided none:', stripped_fmt)
   print('...if bounds lists provided none      :', stripped_bounds)
   print('>>> UNEARNED PASSES:', stripped_fmt - base)
   PY
   ```
2. **Sample rationales directly** — Verify authentic, non-templated reasoning.
3. **Diff `git log` against `HARDENING_EVIDENCE.md`** — Every pipeline commit must carry a receipt.
4. **Run `run_all` twice cleanly** with no intervening edits.
5. Only then write `local_only/scratch/HARDENING_DONE`.

---

## 11. Ending the Tick

Every tick ends with:
1. **Clean, committed working tree**.
2. **No background jobs outstanding**.
3. **`HARDENING_EVIDENCE.md` entry** for any pipeline/skeleton commit.
4. **Ledger entry appended to `validation_reports/hardening_ledger.md`**:

```markdown
## <ISO date/time> — tick <n>
- **Queue before:** §5 stale=… §6F contra=… stale=… unattested=… §6D=…   coverage: attested N/787, reviewed N/151
- **Unit(s) of work:** <one sentence each>
- **Class:** A / B / C, with classifier output justifying any run_all skip
- **Root cause:** <one sentence, or n/a>
- **Machinery built:** <formatter/variant/axis/DNA + registries wired, or "none">
- **Verification:** <command> → <verbatim summary line>
- **Blind verdicts obtained:** <Attester / Reviewer / Declarer batches, or "none">
- **DECIDED (reversible):** <node, rung, reading rejected, what would flip it — or omit>
- **Evidence log entry:** <heading appended, or why none needed>
- **Queue after:** … + coverage after
- **Commit(s):** <sha> <subject>
- **Next tick should:** <specific first item for next tick>
```

---

## 12. Resolution Ladder (Rule 10: No Human Escalation)

When a competency reading is contested, stop at the first settling rung and record as `DECIDED (reversible)`:
1. **Competency wording** — MATATAG's verbs, ranges, and named sub-cases are the authority.
2. **Node ground truth** — `NOT_YET_KNOWN`, `cumulative_vocab` eliminate impossible readings.
3. **Neighbouring nodes** — A reading duplicating an adjacent node is wrong.
4. **Narrower reading wins** — Never over-reach past the written curriculum.

---

## 13. Runner Contract & Safety Limits

- **Hard Wall-Clock Cap**: 90 minutes (`HARDENING_TICK_CAP_SEC=5400`).
- **Terminal Condition**: `local_only/scratch/HARDENING_DONE` exists (written only after §10 Green Audit).
- **Manual Hand-Brake**: `touch local_only/scratch/HARDENING_STOP`.

---

## Appendix A — Carried Content Defects

From Attesters, unasked. Confirm against a fresh render before fixing, and delete the row once fixed and re-attested.

| Node | Seeds | Defect |
|---|---|---|
| `mat_g3_dp_q3_4` | 64 | *"3 yellow, 1 red, 1 green — which color is LEAST likely?"* keyed **'red or green'**. Red and green are equally likely; student answering "red" is marked wrong. |
| `mat_g3_mg_q1_5` | 78, 91, 118, 127 | `intersecting lines` offered as distractor against `perpendicular lines` — but perpendicular lines **are** intersecting lines. |
| `mat_g2_mg_q4_3` | 42, 57, 78, 118 | Stem subject is a bare "It" with no antecedent. Binary question against 4-option set containing surface labels. |
| `mat_g1_mg_q4_0` | 78 | *"Which direction is clockwise?"* is a vocab definition on rotation competency: no object, no turn. |
| `mat_g2_mg_q4_3` | 103 | "A box has six faces that are each a flat square" describes a cube, not a box. |
