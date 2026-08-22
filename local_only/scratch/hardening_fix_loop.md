# Hardening fix loop — one tick

You are one tick of a loop whose job is to **empty the work queue honestly**. The harness is
trustworthy; the remaining work is content, reviews, and providers — not checks.

**This prompt carries no counts.** The revision before this one pasted the queue and was wrong
within three days: it claimed 59 §6D findings (actual 74), 757 unattested (actual 644), and never
mentioned §5 stale reviews at all — which by then was the single largest item in the tree at 557.
A prompt that carries state is a prompt that lies. Every number you act on, you measure in Step 2.

---

## Step 1 — Preflight. Always. Roughly one second.

```bash
PYTHONPATH=. .venv/bin/python3 scripts/hardening_supervisor.py --reap
```

`--reap` is not optional. Orphaned `multiprocessing` workers survive their parent, keep burning a
core each, and are invisible to any pattern matching the job name — 14 of them once accumulated 59.7
core-hours on this 4-core host and starved everything else to the point that healthy runs looked
deadlocked. Judge liveness by the **process tree's** CPU, never a parent's own: a pool parent idles
by design.

**Act on the verdict:**

**`10 RESUME`** → continue below, with two conditions:
- If the printed tree is **MODIFIED**, you are *resuming an interrupted tick*, not starting a new
  one. Read `git diff` first, then make one explicit choice and name it in your report: **finish**
  that unit (verify it, commit it) or **`git restore`** it. Never begin new work stacked on top of
  a half-finished unit — that is how a tick produces something no later tick can trust.
- Your starting point is the ledger's `Next tick should:` (the supervisor prints it), not any list
  in this file.

**`0 IN_FLIGHT`** → a watched process is alive. Do **not** stop yet — find out whose it is:

```bash
ps -o pid,ppid,etime,time,args -p <pid>
```

- **A `run_all` this loop left behind** (args name `practice_gen.validation.run_all`): do *not*
  start a second one — two concurrent matrix runs on 3 workers each will starve this 4-core host.
  Attach to it instead: `ls -t local_only/scratch/run_all_*.log | head -1`, wait for the exit line,
  record it, and continue the tick from `Next tick should:`.
- **Anything else, or a process you cannot account for** (another session, a human, `pytest`,
  `mutation_harness`): report and stop. Never start a competing run.

**`30 NEEDS_HUMAN`** → report and stop.

**`20 NOTHING_TO_DO`** → three lines and stop. Do not invent work.

**`40 HUNG_UNREAPED`** → unreachable when `--reap` is passed (`hardening_supervisor.py`, gated behind
`if hung and not killed:`). If you see it, you dropped the flag. Re-run the command exactly as
written above.

---

## Step 2 — Measure the queue. ~17 seconds. Never skip it, never substitute a remembered number.

```bash
PYTHONPATH=. .venv/bin/python3 - <<'PY'
import re, collections
from backend.app.practice_gen.validation import validate_judgment as VJ, validate_capability as VC
NODE = re.compile(r'mat_g\d_\w+?_q\d_\d+')
j = VJ.validate_judgment_reviews()
stale   = [e for e in j if "must be 'PASS'" not in e]
verdict = [e for e in j if "must be 'PASS'" in e]
c   = VC.validate_capability_declarations()
d6d = [e for e in c if '6D' in e]
d6f = [e for e in c if '6F' in e]
un  = [e for e in d6f if 'unattested'  in e.lower()]
con = [e for e in d6f if 'contradict'  in e.lower()]
sta = [e for e in d6f if 'stale'       in e.lower()]
def nodes(es): return {m.group(0) for e in es for m in [NODE.search(e)] if m}
print(f"§5  STALE/malformed reviews : {len(stale):4d}  across {len(nodes(stale)):3d} nodes   <- fix before content work")
print(f"§5  non-PASS verdicts       : {len(verdict):4d}  across {len(nodes(verdict)):3d} nodes")
print(f"§6F CONTRADICTED            : {len(con):4d}  across {len(nodes(con)):3d} nodes   <- highest priority")
print(f"§6F stale attestations      : {len(sta):4d}  across {len(nodes(sta)):3d} nodes")
print(f"§6F UNATTESTED              : {len(un):4d}  across {len(nodes(un)):3d} nodes")
print(f"§6D wildcard providers      : {len(d6d):4d}  across {len(nodes(d6d)):3d} nodes")
print(f"    6D worst first          : {collections.Counter(m.group(0) for e in d6d for m in [NODE.search(e)] if m).most_common(5)}")
print(f"TOTAL capability findings   : {len(c)}   (the work queue, not the score)")
print(f"tally: {VJ.summarize_verdicts()}")
PY
```

**This is stages 6/7 and 7/7 of `run_all`, exactly** — `run_all` calls
`validate_judgment.validate_judgment_reviews()` and
`validate_capability.validate_capability_declarations()`, the same two functions. You are not
approximating the harness here; you are running the two stages that can have moved, for 17 seconds
instead of 50 minutes.

**Priority — work the first band that is non-zero:**

1. **§5 stale / malformed reviews.** The durable protocol: *"`NON-VERDICT` must be 0 … fix it before
   any content work."* A review about content the pipeline no longer produces is not evidence of
   anything, and it hides real verdicts behind noise.
2. **§6F CONTRADICTED** — a blind Attester ruled NOT_PROVIDED and the table still claims it. The
   pipeline is asserting something a blind party has already refuted.
3. **Content defects an Attester reported** (Appendix A, plus anything new). No machine check
   catches these; they are wrong answers reaching students.
4. **§6F stale attestations** → **§6D wildcards** → **§6F UNATTESTED**.

**Campaign override.** If the loop was launched naming a campaign (e.g. *"work the attestation
backlog"*), that band goes first and the rest keep their relative order. Record the deviation and its
reason in the ledger entry. Bands 1 and 2 are never skipped silently — if a campaign defers them,
the ledger says so with the current count, so the deferral is visible rather than lost.

Within a tick, the failure count is **the work queue, not the score**. It can only be lowered by
weakening something, and that is forbidden. Track progress by coverage (`attested N/787`,
`reviewed N/151`), which no weakening can move.

---

## Step 3 — Read the durable protocol

`local_only/scratch/hardening_loop_prompt.md` — hard rules, known hazards, tick types, blind-role
dispatch, process hygiene. It carries no dated state, so nothing in it expires. Two corrections to
apply while you read it:

- **§2b points at `hardening_tick_prompt.md`, which does not exist.** Ignore that pointer. The queue
  is Step 2's measurement; the next-item pointer is the ledger's `Next tick should:`.
- Its `run_all` timing is the correct one: **~50 minutes**, measured. Budget 50, not 35.

Where your own measurement disagrees with any file, **yours wins**, and the ledger records the drift.

---

## Step 4 — Classify the unit before you touch anything

Every unit is exactly one of two classes, and the class decides whether this tick pays 50 minutes.

| | **Class A — pipeline** | **Class B — records** |
|---|---|---|
| touches | `backend/app/practice_gen/`, `data/skeletons/` | `validation_reports/`, `docs/`, the ledger |
| examples | generator/DNA/adapter/axes/formatter fixes, new machinery (Tick F) | attestation batches, blind re-reviews, evidence entries |
| can move | every harness stage, 1–7 | stages 6 and 7 only |
| verification | **full `run_all` before commit** | Step 2's two gates — nothing else can have changed |

Ask the classifier rather than guessing:

```bash
PIPE=$(git status --porcelain -- backend/app/practice_gen/ data/skeletons/)
if [ -n "$PIPE" ]; then echo "CLASS A — full run_all REQUIRED:"; echo "$PIPE";
else echo "CLASS B — no pipeline file touched; stages 1-5 cannot have moved"; fi
```

**Pair the classes.** A Class A unit costs a 50-minute `run_all` you must wait out anyway. Fill that
window with Class B work — which is where the bulk of the queue lives. One Class A unit with Class B
work running inside its window is the most a tick can do; a Class A unit with an idle window wastes
most of the tick, and back-to-back Class A units in one tick means two `run_all`s or one dishonest
verdict.

---

## Step 5 — `run_all`: when it is required, and how to spend the 50 minutes

**Class B ticks run no `run_all` at all.** Stages 1–5 verify generation; if no generator changed,
they cannot have moved, and Step 2 already ran the only two stages that could. **Name the skip in
the ledger with the classifier output that justified it.** A skipped run is *named*, never assumed —
an unexplained skip is indistinguishable from an evasion.

**Class A ticks run it, in this order:**

1. **Fix, then verify scoped and cheap** (seconds, not minutes):
   ```bash
   PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.validate_matrix --node <id>   # ~3 s each
   PYTHONPATH=. .venv/bin/python3 scripts/check_blast_radius.py --dna <name>                           # every sibling on that DNA
   ```
   Note `validate_matrix --node` **overwrites** `validation_reports/matrix_report.json` with a
   one-node report. Never read that file as a tree-wide baseline afterwards.

2. **Freeze pipeline edits.** From here until the run lands, nothing under
   `backend/app/practice_gen/` or `data/skeletons/` changes. A `run_all` that overlaps your edits
   reports on a tree that no longer exists — the verdict is worthless and nothing in the output will
   tell you so.

3. **Launch it in the background, never the foreground:**
   ```bash
   PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.run_all \
     > local_only/scratch/run_all_$(date +%m%d_%H%M).log 2>&1 &
   ```

4. **Spend the window on Class B work** — build packets, dispatch blind subagents, file records,
   draft the evidence entry. Never on more pipeline edits (that breaks the freeze). Never on
   `tests/mutation_harness.py`, which edits tracked files in place and must not run concurrently.

5. **Read the exit line before you commit.** Either the job landed and you recorded its result, or
   you killed it and said so. Never end a tick with a background job outstanding — an outstanding
   job is what makes the next tick's preflight return `IN_FLIGHT` and lose its slot.

CI does not run this harness. On a Class A unit you are the only gate between a broken pipeline
change and production.

---

## Step 6 — The defect taxonomy: how to fix each kind, and what is forbidden

### Rule of sequencing — read this before picking anything

**Fixing a generator invalidates both the judgment review and the attestation for every node it
touches.** §5 freshness re-renders cited seeds; §6F freshness re-renders `packet.samples_judged`.
Both go loud when content moves. So:

- **Never attest or re-review a node you are about to change.** You will pay for it twice.
- The cycle per node cluster is **attest → fix what it surfaces → re-attest once**. Attesters find
  defects no machine check can, so attestation is how you *discover* work, not a formality after it.
- After any content fix: re-run `validate_matrix --node`, dispatch a **fresh blind re-review**, and
  **re-attest**. A stale verdict is not evidence.

### §5 — stale or malformed reviews

The seed no longer renders what was judged, or keys a different answer. Almost always the honest
downstream cost of a content fix that landed without its re-review.

**Fix:** rebuild the packet
(`python -m backend.app.practice_gen.validation.judgment_packets --node <id>`), dispatch a fresh
blind reviewer on it, file the new review. §6F honours supersession, so re-reviews subtract rather
than accumulate.
**Forbidden:** editing the stored review, re-dating it, or deleting it to make the count fall.

### §6F CONTRADICTED — a blind Attester ruled NOT_PROVIDED and the table still claims it

**Fix:** build the artifact that renders what the clause names, then re-attest — *or* delete the
entry and let §6C report the honest gap (a Tick F work item, not a defeat).
**Forbidden:** re-filing the verdict, editing the record, deleting the record, or re-registering the
entry under another name. If you believe the Attester was wrong, dispatch a *fresh* Attester on a
fresh packet and record **both** verdicts — never overwrite one.

### Content defects surfaced by Attesters — the highest-value findings in the tree

Wrong answers reaching students; no machine check catches any of them. Two of the first two batches
each contained a genuine mathematical error on a node whose judgment review is a filed PASS.

**Fix:** root-cause it in the generator (Protocol 2 — every instance of the cause, not the one
seed), print the seed in any new failure message, re-run the node, then re-review **and** re-attest.
**Forbidden:** editing the rendered sample, special-casing the seed, or narrowing the competency.

### Coverage skew — a generator defect, not a review artifact

Ten seeds routinely collapse to ~6 distinct stems, and within that, named clauses ride single seeds.
A student can complete a full set having met a named sub-case once.

**Fix:** widen the generator's sampling so every clause the competency names is reachable at a
defensible rate. **Forbidden:** declaring it fine because the clause is technically exhibited.

### §6D — wildcard providers

An entry naming only `mcq`/`cloze`/`true_false`/`error_detect` discriminates nothing: 27 of 28 DNAs
offer them.

**Fix:** point the entry at the artifact that actually produces what the clause names — a variant, a
specific formatter, a bound that genuinely carries a numeric ceiling. If none exists, **build it**
(Rule 8: building it *is* the fix; "needs new machinery" is not a deferral), or delete the entry and
let the gap be reported.
**Forbidden:** adding a second generic formatter; renaming; widening `COMPATIBILITY` so a generic
name looks specific. A PROVIDED verdict does **not** license keeping `mcq` — §6F asks whether the
content does the thing, §6D asks whether the registered provider is real. Both must pass.

### §6E — `bounds` as a wildcard, if the check is still unbuilt

Rule 9: *"A `bounds` list is a numeric-ceiling provider and nothing else."* Discriminate on
**shared-ness** — a list carried verbatim by hundreds of entries makes no claim about any particular
capability. **Do not threshold on list length**; `test_bounds_length_is_never_the_discriminator`
pins that and must keep passing. Ship it as §6D and §6F were: `pgen_contract.md` row +
`CONTRACT_CHECKS` entry (the two-direction lint fails otherwise) + unit tests + a planted mutation
proved caught by name.

### §6F UNATTESTED — nobody blind has judged whether the output exhibits the clause

Measured throughput: 25 clauses across 3 nodes in 151 seconds, 0 tool uses.

**Do:** build packets with
`tests/attester_packets.py --node A --node B --node C --packets P --key K` (`--node` repeats;
`--unearned` targets everything §6D reports as unearned). Pass the samples **inline** in the
subagent prompt, so blindness needs no sandbox. State Rule 1's forbidden-path list verbatim. Frame
neutrally — *"do these items exhibit what this clause names?"*, never *"find the defects"*, which
was measured to bias toward FAIL. File one record per node under `validation_reports/attestation/`,
**including `packet.node_id` and `packet.samples_judged`**, or §6F fails the batch as uncheckable.
Ask the Attester to report any content problem it notices — that is where the math errors came from.
**Forbidden:** attesting on `is_lab=True` samples (the competency clamp is bypassed, so a Lab sample
can exhibit a capability the student path can never reach); writing a verdict yourself; batching
more than 25 clauses.

> **§6F cannot tell an earned verdict from a fabricated one. Read this before filing any batch.**
>
> §5 carries three structural gates against fabricated reviews — verbatim-reuse, rationale-skeleton
> clustering (`_MAX_SKELETON_CLUSTER = 3`), quote provenance, and reviewer plurality
> (`_MAX_NODES_PER_REVIEWER = 25`). **§6F carries none of them.** It checks JSON validity, the verdict
> enum, freshness (re-rendering `packet.samples_judged`), and UNATTESTED/CONTRADICTED. The record's
> `role` and `blindness` fields are never read by any validator, and `reasoning` is read exactly once
> — to quote it back inside a CONTRADICTED message.
>
> §5's own history is what that costs: freshness alone passed all 151 fabricated reviews, and 115 of
> them quoted stems appearing nowhere in their own packets. A templated all-PROVIDED batch would
> sail through §6F today and raise coverage while proving nothing.
>
> So until the gate exists, the discipline is yours to keep and to evidence:
>
> - **A distinct attester identity per batch.** Never stamp one identity across the campaign.
> - **Run the interim self-audit over every record on disk before you commit**, and paste its output
>   in the evidence entry. A rising cluster count or an unexplained phantom quote fails the batch —
>   rebuild it, do not file it.

```bash
PYTHONPATH=. .venv/bin/python3 - <<'PY'
import json, glob, collections
from backend.app.practice_gen.validation.validate_judgment import (
    _rationale_skeleton, _QUOTE_RE, _MIN_QUOTE_LEN)
skel = collections.Counter(); byident = collections.Counter(); phantom = []; total = 0
for f in sorted(glob.glob('validation_reports/attestation/*.json')):
    d = json.load(open(f)); pkt = d.get('packet', {}) or {}
    corpus = " ".join(str(s.get('question_text','')) + " " + str(s.get('correct_answer',''))
                      for s in (pkt.get('samples_judged') or [])).lower()
    ident = f"{d.get('role')}|{json.dumps(d.get('blindness'), sort_keys=True)}"
    for v in d.get('verdicts', []):
        total += 1; byident[ident] += 1
        r = str(v.get('reasoning',''))
        skel[_rationale_skeleton(r)] += 1
        allowed = corpus + " " + str(v.get('clause','')).lower()
        for _q, span in _QUOTE_RE.findall(r):
            s = span.strip().lower()
            if len(s) >= _MIN_QUOTE_LEN and s not in allowed:
                phantom.append((d.get('batch'), v.get('node_id'), v.get('capability_id'), span[:70]))
print(f"verdicts audited              : {total}")
print(f"distinct reasoning skeletons  : {len(skel)}")
print(f"largest skeleton cluster      : {skel.most_common(1)[0][1]}   (§5 caps at 3)")
print(f"distinct attester identities  : {len(byident)}   largest covers {byident.most_common(1)[0][1]}")
print(f"phantom-quote candidates      : {len(phantom)}")
for p in phantom[:10]: print("   -", p)
PY
```

> This audit's corpus is **narrower than §5's** — it holds stems and answers, not options, formatter
> names, or the node's competency text — so a flagged span is a *candidate*, not a proven phantom.
> Adjudicate each one by reading it: an Attester legitimately puts descriptions in quotes ("share N
> among M"), and that is not a fabricated citation. Treat a jump in the count as the signal, not the
> absolute number.
>
> **This is an interim, and an agent auditing itself is the weaker arrangement by construction.** The
> durable fix is to port §5's three gates onto §6F as a contract check, shipped the way §6D and §6F
> were: `pgen_contract.md` row + `CONTRACT_CHECKS` entry + unit tests + a planted mutation proved
> caught by name. **Do not build that check inside an unattended run.** An agent authoring the gate
> that constrains its own output is the exact conflict of interest behind all three past defeats;
> that unit is done attended, or not by this loop.

---

## Step 7 — Every tick ends the same way

- **Tree committed, each unit atomic.** Never mid-unit, never uncommitted.
- **No background job outstanding.** Exit line read and recorded, or killed and said so.
- `validation_reports/HARDENING_EVIDENCE.md` entry for any commit touching
  `backend/app/practice_gen/` or `data/skeletons/`, with verbatim command output (Rule 7).
- **Ledger entry** (protocol §4) ending in a specific `Next tick should:`. If this was a Class B
  tick, the entry names the `run_all` skip and the classifier output behind it.
- Re-run the supervisor so `hardening_status.json` is current for the next wake-up.
- Report **both** movements: findings *and* coverage. Failures rising while coverage rises is
  progress. Failures falling while coverage is flat is the signature of all three past defeats, and
  reporting a falling failure count on its own is how each of them was presented.

---

## Step 8 — Decide the next tick yourself

You cannot read your remaining rate-limit budget from inside the loop, so pace on what you can
observe:

| what happened this tick | next wake |
|---|---|
| a unit committed cleanly | **60 s** — start the next tick immediately |
| work identified but you ran out of room mid-unit | **60 s**, and leave the tree committed |
| a call failed in a way that suggests a rate limit or a dropped connection | **3600 s** (the max), and say so in the report |
| `NOTHING_TO_DO` or `NEEDS_HUMAN` | **stop the loop** |

Call `ScheduleWakeup` with the same prompt before the turn ends. If you never call it, the loop is
over: there is no external supervisor to restart it, and you must not build one (§6 — the retired
daemon dry-ran forever, measured liveness by commit mtime, and pointed at a compressed protocol that
cost 392 wildcard providers). If you want a heartbeat that survives this session, it is
`scripts/hardening_supervisor.py --reap` on an OS schedule, outside the session, doing no pipeline
work — not an agent.

---

## Never

Weaken a check, widen a provider, flip a verdict, rewrite a test around its own failure, narrow a
declaration, edit a review or an attestation record, or special-case a seed. If a check fails, the
bug is in the pipeline. The only legitimate reasons to leave something unfixed are budget (then name
it in `Next tick should:`), a genuine pedagogical ambiguity that is the maintainer's call (escalate
with both readings), or a ground-truth error in the curriculum data (report with node ID and
justification). "Hard", "large", and "needs new machinery" are none of those.

---

## Appendix A — carried content defects

These came from Attesters, unasked. **Verified 2026-08-23: none was touched in ticks 20–23** (no
ledger mention after tick 19), so all are presumed still open — but each is a claim about rendered
content, so **confirm it against a fresh render before fixing, and delete the row once it is fixed
and re-attested.** The ledger, not this table, is the authority on disposition.

| node | seeds | defect |
|---|---|---|
| `mat_g3_dp_q3_4` | 64 | *"3 yellow, 1 red, 1 green — which color is LEAST likely?"* keyed **'red or green'**. Red and green are equally likely, so a student answering "red" is **marked wrong for a correct answer**. Singular "Which color" contradicts a disjunctive key. |
| `mat_g3_mg_q1_5` | 78, 91, 118, 127 | `intersecting lines` offered as a distractor against keyed `perpendicular lines` — but perpendicular lines **are** intersecting lines, so the distractor is not wrong. |
| `mat_g2_mg_q4_3` | 42, 57, 78, 118 | Stem subject is a bare "It" with no antecedent. Binary question ("straight or curved line?") against a four-option set containing two *surface* labels — question and options disagree. |
| `mat_g1_mg_q4_0` | 78 | *"Which direction is clockwise?"* is a vocabulary definition on a competency about identifying position after rotation: no object, no turn, no initial facing direction. |
| `mat_g2_mg_q4_3` | 103 | "A box has six faces that are each a flat square" describes a cube, not a box. |
