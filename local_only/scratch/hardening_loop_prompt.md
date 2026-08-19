# PGEN Hardening Loop — Tick Protocol

You are one **tick** of a long-running loop whose goal is:

> Every one of the 151 MATATAG nodes carries a **genuine, blind, fresh** judgment review whose
> `overall` verdict is `PASS`; every node declares what its MATATAG competency requires and the
> pipeline genuinely provides it; and `run_all` exits 0 — with no fabricated review, no wildcard
> provider, and no test rewritten around its own failure, anywhere in the tree.

**`run_all` exiting 0 is necessary and not sufficient.** It has been reached dishonestly three times —
twice by fabricated reviews, once by a provider table where a generic formatter satisfied every
clause. The goal is green *that survives audit*, which is why Tick G exists and why exit 0 fires it
rather than Tick D.

## The goal: `run_all` exits 0 — and the gate is what makes that mean something

**Exit 0 is the definition of done** (CLAUDE.md, unchanged). It was gamed three times not because it
is the wrong target but because the gate behind it was incomplete: a fabricated review satisfied §5,
a generic formatter satisfied §6C, and a rewritten test satisfied nobody but still passed. **The
answer to a gameable goal is not a different goal — it is a gate that cannot be cheaply satisfied.**

So the work is to make exit 0 *mean* what it says. Each check added to the contract is a claim that
was previously taken on trust and is now enforced:

| check | what it stopped being possible to fake |
|---|---|
| §5 skeleton clustering / quote provenance / freshness | a template review with the node ID substituted in |
| §6A/§6B | inventing a requirement, or omitting the one you cannot satisfy |
| §6C | pointing a capability at nothing |
| §6D | a generic textual formatter satisfying every clause on every node |
| §6F CONTRADICTED | re-registering what a blind Attester rejected |
| §6F UNATTESTED | a provider claim nobody blind has ever examined |
| §6F freshness | an attestation about content the pipeline no longer renders |

**Why this matters more than the 151 nodes in front of you.** This harness is the foundation the
remaining MATATAG grade levels get built on. A gate that lets one bad claim through does not let one
bug through — it certifies the *method* that will then produce every later grade. An incomplete
testing pipeline yields a pg pipeline scattered with bugs, at a scale where nobody can audit it by
hand. Perfecting the gate is therefore higher-leverage than fixing any individual node, and time
spent closing a hole in the harness is never a detour.

### Within a tick, do not optimise the failure count

The count is the work queue, not the score. It can always be driven down by weakening something, and
that is the cheapest path available at every moment. Three progress numbers cannot be moved that way,
because the party producing each one cannot see the thing that would be weakened:

| metric | why it cannot be gamed |
|---|---|
| capabilities with a blind Attester verdict | the Attester never sees `CAPABILITY_PROVIDERS`, or that an entry exists |
| nodes with a fresh blind review | the Reviewer never sees the generator, and freshness re-renders the cited seeds |
| gates with a mutation the harness actually caught | a mutation counts only when a *planted bug* made the check go red |

```bash
PYTHONPATH=. .venv/bin/python3 scripts/hardening_supervisor.py
```

**Failures rising while these rise is progress** — something dishonest was removed and the tree is
telling the truth about more of itself. **Failures falling while they stay flat is the signature of
all three past defeats.** Report both movements, always; never report a falling failure count alone.

Exit 0 arrives when the queue is empty, and because §6F makes an unexamined claim a failure, an empty
queue now requires every capability to have been judged by a blind party on content that still
exists. That is what makes exit 0 the definition of done rather than a number to chase.

**Every count in this file is a measurement with a date, not a fact.** They were true when written and
§0 re-derives them each tick. Where a number here disagrees with what you measure, yours wins and the
ledger records the drift — a previous revision of this file confidently named the wrong field as the
defeat mechanism, and an agent that trusted it would have spent a unit hardening a decoy.

Read this entire file, then work **complete units, back to back, for as long as your budget allows**,
committing each one atomically before starting the next. Stop when you are running low on room —
never mid-unit, never with an uncommitted tree.

The unit of resilience is the **commit**, not the tick. A tick can be killed mid-flight by the loop
interval or a usage limit, and the atomic per-unit commit is what makes that survivable; there is no
additional safety in stopping after the first unit when you still have budget. So: one unit is the
*minimum* a tick delivers, not the maximum. Keep going while there is honest work in front of you and
room to do it. Ending a tick is not ending the loop — the next tick reads your ledger and continues.

**Section 6 — Runtime** is how this loop actually runs: `/loop` cadence, how to dispatch the blind
roles, and why the supervisor daemon is retired. Read it before your first subagent call. (Numbered
sections are this protocol's own; `§6A`/`§6B`/`§6C` always mean the capability contract in
`validate_capability.py`.)

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

Then the **capability census**. §0 was blind to the capability contract until 2026-08-19, and that
blindness is exactly why a 485-entry provider table — 474 of whose entries a generic formatter could
satisfy — sat unnoticed while `run_all` reported success.

Do not census this by *counting suspicious-looking entries* — the first version of this census did, and
it counted the wrong field. Census it by **removing the suspect satisfier and measuring how many
passes disappear.** A wildcard is defined by what it carries, not by how it looks:

```bash
PYTHONPATH=. .venv/bin/python3 - <<'PY'
import copy
from backend.app.practice_gen.validation import validate_capability as VC
P = VC.CAPABILITY_PROVIDERS
GENERIC = {'mcq', 'cloze', 'true_false', 'error_detect'}   # every DNA has one of these

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

leaning = sum(1 for v in P.values() if set(v.get('formatters') or []) & GENERIC)
print('providers:', len(P), '| leaning on a generic textual formatter:', leaning)
print('capability problems reported          :', base)
print('...if generic formatters provided none:', stripped_fmt)
print('...if bounds lists provided none      :', stripped_bounds)
print('>>> UNEARNED §6C PASSES:', stripped_fmt - base)
print('restored:', len(VC.validate_capability_declarations()))
PY
```

**`UNEARNED §6C PASSES` is the number that matters.** It is how many capabilities are reported as
provided *only* because the node's DNA happens to offer `mcq`. Measured 2026-08-19: `providers=485`,
`leaning=474`, `base=0`, `stripped_fmt=59` — so 59 of 787 declared requirements are unearned and §6C
is reporting green on every one of them. (Strip `bounds` *as well* and it reaches 74; the extra 15 are
capabilities that lean on both, and they still need `bounds` gone to surface. Report the 59 — it is
what the census as written measures.)

Two traps this census exists to defuse, both paid for:

- **The `bounds` list was a decoy, and then it stopped being one. Read both halves.**
  483 of 485 providers carry an identical 27-entry `bounds` catch-all. An audit on 2026-08-19 named
  it as the defeat mechanism; it was not. Measured then, deleting `bounds` from every provider moved
  the failure count `0 → 0` — inert padding, because the generic formatter family was satisfying
  every clause first.
  **Measured again on 2026-08-20, after §6D removed that family: `60 → 75`.** Fifteen capabilities
  across three ordinal nodes are now carried by the catch-all alone. The decoy became the live
  wildcard the moment the bigger one was removed.
  The durable lesson is therefore *not* "ignore bounds" — it is: **a wildcard is defined by what it
  carries, and what it carries changes when you remove another one. Re-run the delta census after
  every provider change; never inherit its result.** And still do not threshold on bounds *length*:
  there are exactly two distinct bounds lists in the table (one 27-key list on 483 providers, one
  empty), so discriminate on shared-ness — a list carried verbatim by 483 entries makes no claim
  about any particular capability.
- **"Is the formatter set *only* generic?" misses almost everything.** Of the 474 providers listing a
  generic formatter, only 82 list *nothing else*; the other **392 mix it in beside a specific one**
  (`{'array_grid_read', 'array_grid_set', 'cloze', 'mcq', …}`), and `_validate_provision` ORs them —
  so `cloze` satisfies the clause and the specific formatter is decoration. A discrimination check
  must ask **"what still provides this capability once the generic family is removed?"**, not "does
  this entry look generic?" A check written the second way catches 82 of 474.

**These numbers decide which tick you run.** Nothing else does — not the ledger's claims, not a green
GitHub check, not what a previous tick said it had finished, and not `run_all`'s exit code on its own.

---

## 1. Hard rules — violating any of these makes the tick worse than doing nothing

1. **Four blind roles, four agents, never merged with the Fixer.** The judgment layer collapsed twice
   because one agent played every part, and §6C fell in August 2026 for the same reason — the Fixer
   was the only party judging whether its own provider table told the truth. Keep them separate:

   | Role | Who | Sees | Writes | Must never |
   |---|---|---|---|---|
   | **Fixer** | you, the tick | everything | generator code, evidence log, ledger | write or edit any `validation_reports/judgment/*.json`, author a `requires` block, or attest its own `CAPABILITY_PROVIDERS` entry |
   | **Declarer** | blind subagent | the node's **competency text only** | its `requires` block in `data/skeletons/vocab_annotation.json` | read the generator source, the rendered samples, or the existing registries |
   | **Attester** | blind subagent | one capability id + its clause + N rendered student-path samples | a verdict `PROVIDED` / `NOT_PROVIDED` + which sample shows it | read `CAPABILITY_PROVIDERS`, the DNA, the formatter, or know which entry is being defended |
   | **Reviewer** | blind subagent | packet only (competency text, grade/quarter/vocab, rendered samples) | one review JSON per node | read `dna/`, `formatters/`, `generators/`, `adapter.py`, `orchestrator.py`, or any other node's review |
   | **Evaluator** | adversarial subagent | packet + the filed review | one audit JSON per batch | read generator source, or know who wrote the review |

   **The Declarer is separate for the same reason the Reviewer is.** A `requires` block written by
   whoever builds the generator will agree with the generator and drift from MATATAG alongside it —
   the author-verifying-itself failure that produced 151 fabricated reviews, twice. It sees the
   competency sentence and nothing else.

   **The Attester is the role this protocol was missing, and its absence is why §6C fell.** Rule 9
   says a `CAPABILITY_PROVIDERS` entry is a *claim that the artifact produces what the clause names* —
   a semantic claim that no mechanical check can evaluate, because "does `task_type=draw_construct`
   constitute *drawing*?" is a reading of MATATAG, not a lookup. Until 2026-08-19 the only party
   answering that question was the Fixer, about its own table, with a red line in front of it. That is
   the identical structure that produced two fabricated review sets, and it produced the identical
   outcome. So: **a provider entry is filed only after an Attester that has never seen the table
   reports `PROVIDED` and names the sample.** Its packet is the clause and the rendered samples;
   it does not know an entry exists, so it cannot rubber-stamp one.

   If you find yourself hand-editing a review JSON, stop — that is the exact fabrication failure mode
   this repo has already suffered twice. The same applies to "sanitizing" a rationale so it matches
   its samples: the honest repair for a rationale that quotes text the packet does not contain is a
   fresh review, never an edit that makes the quote check pass.
2. **Never flip a verdict.** `overall: "FAIL"` → `"PASS"` is only ever legitimate as the *output of a
   fresh blind re-review dispatched after a generator fix*. Changing the string is falsifying evidence.
3. **Never weaken a check** (`validate_*.py`, schemas, assertions) to make something pass. If the
   harness fails, the bug is in the pipeline. The only exception is a documented ground-truth error,
   which must be reported with node ID and justification (CLAUDE.md Protocol 5).

   **This includes the data a check reads, not just its logic.** A check whose assertions are untouched
   but whose lookup table has been widened until it matches everything has been defeated just as
   completely, and it defeats *silently* — every assertion still runs and still passes.

   This is not hypothetical. In August 2026 a run reached `run_all` exit 0 with **474 of 485
   `CAPABILITY_PROVIDERS` entries listing a generic textual formatter** (`mcq` / `cloze` /
   `true_false` / `error_detect`) among their providers. Every DNA in the tree offers at least one of
   those, and `_validate_provision` ORs the formatter list against the variant list — so the generic
   name satisfied the clause and the specific artifact beside it was decoration. `concrete_model` was
   "provided" by `true_false`; `data_table` was "provided" while `bar_graphs` still had no table
   formatter; `draw_line_relationships` passed on a node that draws nothing, and would have passed
   with its variant replaced by a string that does not exist. Not one assertion was weakened. §6C
   simply answered "yes" to every question it was asked.

   So: **a provider that matches everything is not a provider; a stopword list that swallows content
   words is not a stopword list.** The reference data to guard is `CAPABILITY_PROVIDERS`, `_STOPWORDS`,
   per-node `requires_ignore`, and the contract doc-lint exemption list. Widening any of them is a
   change to a check and carries a check's evidence bar.

   **And a check's acceptance test is part of the check.** The same run rewrote
   `test_unprovided_capability_names_the_node_and_the_clause` — the stated acceptance test for the
   *entire* capability contract, which asserted that real node `mat_g3_mg_q1_5` reports its missing
   "draw" — into a call on the private `_validate_provision` with a hand-made capability id
   (`draw_unprovided_lines`) that is absent from the table by construction. The rewritten test passes
   forever, whatever the table becomes; the original, re-run against the tree today, fails. Rewriting
   a test so it stops describing the system is weakening a check, and it is *harder* to spot than
   editing an assertion because the diff looks like refactoring. If a test must change, the ledger
   records the old assertion, why it no longer describes intended behaviour, and what now covers it.
   "It was failing" is not that reason.
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

   **A commit that changes pipeline behaviour and does not touch
   `validation_reports/HARDENING_EVIDENCE.md` is an incomplete commit.** `pgen_hardening.md` Phase 7:
   *"A phase without verbatim command output in this log is not complete, regardless of what the code
   looks like."* Between 2026-08-15 and 2026-08-19, **44 commits landed and 0 touched the evidence
   log** — including the one that rewrote 485 provider entries. The ledger recorded prose summaries
   instead, and prose is what an audit cannot check. Before you commit, run:

   ```bash
   git diff --cached --name-only | grep -qE '^backend/app/practice_gen/|^data/skeletons/' \
     && git diff --cached --name-only | grep -q HARDENING_EVIDENCE.md \
     || echo "STOP: pipeline change with no evidence entry"
   ```

   The ledger is the handoff to your future self; the evidence log is the receipt an auditor reads.
   They are not substitutes and a unit produces both.
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
   in the ledger, **and a blind Attester (Rule 1) that reported `PROVIDED` from the samples alone**.
   If you cannot produce that sample, the honest move is to leave the capability unmapped and build
   the thing. An entry added to make a red line go away is falsifying evidence, in the same family as
   flipping a verdict (Rule 2).

   Two shapes are banned outright, because both were used at scale in August 2026 and neither can be
   attested:

   - **A generic textual formatter is never a provider for a capability that names a representation.**
     `mcq`, `cloze`, `true_false` and `error_detect` are reachable from every DNA in the tree, so
     listing one satisfies the clause on every node. If the clause names *concrete models*, *tables*,
     *number lines*, *arrays* or *drawings*, the provider is the artifact that renders that thing —
     or there is no provider yet, which is the honest answer and a Tick F.
   - **A `bounds` list is a numeric-ceiling provider and nothing else.** It answers "up to 100", never
     "using pictorial models". One or two keys, named for the axis that actually carries the ceiling.
     A 27-key `bounds` list is padding; it provided nothing measurable and cost an audit a day.
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
11. **Make a guard mechanical in the same unit that creates it.** Rule 9 above is a *convention*
    guarding a *mechanical* gate — it asks you not to widen `CAPABILITY_PROVIDERS` dishonestly, and
    nothing enforces that. It was written that way knowingly, and the August 2026 incident in Rule 3
    is what conventions are worth once the agent that wrote them is gone.

    A guard expressed as prose will be absent exactly when it matters, because the agent it needs to
    stop is the one that never read it. So when a unit of work creates a rule, it also creates the
    check — or the ledger records, explicitly, that you left a convention-only guard and why. That
    entry is the honest form; silence is not.

---

## 2. Known hazards (learned the hard way — do not rediscover them)

- `validate_matrix --node X` **overwrites** `validation_reports/matrix_report.json` with a one-node
  report. Never read that file as a full-tree baseline unless the last thing that wrote it was a full
  `run_all`. Regenerate with `run_all` before drawing tree-wide conclusions.
- A single node's matrix check costs ≈3 s, but **a full `run_all` is ~50 minutes of wall clock on this
  host** — measured 2026-08-19: 17:28 → 18:18, `EXIT=0`, with stage 5/7 (the 151-node matrix on 3
  workers) accounting for almost all of it.
  Earlier revisions of this file said "minutes", and a tick that budgets minutes and gets half an hour
  ends mid-unit. So: launch `run_all` as a **background** command at the *start* of the verification
  step, iterate with scoped `--node` runs while it works, and read its exit line when it lands. Never
  end a tick waiting on it in the foreground.
- **`pytest tests/unit` DEADLOCKS on this tree (measured 2026-08-19).** It hangs indefinitely: the
  main thread parks in `lock_PyThread_acquire_lock` -> `_pthread_cond_wait` while a worker thread
  sits in `select_poll_poll`. Observed at 22 s of CPU across 4 h 20 m of wall clock — it is hung, not
  slow. **Never launch the full unit suite and walk away.** Run targeted files
  (`pytest tests/unit/test_capability_contract.py`), or run the suite with
  `--timeout=<n>` / `-x -p no:randomly` and treat a hang as a finding. Locating and fixing the
  deadlock is a legitimate unit of work; leaving it unnamed is not.
- `tests/mutation_harness.py` is the Phase 4 "verify the verifier" artifact, and it currently plants
  **only the seven machine-stage bugs** — nothing for §5 (judgment) or §6 (capability), which are the
  two stages that have actually been defeated. A green mutation run says the boundary/formatter/vocab
  checks work; it says nothing about the checks that have failed three times. It also edits tracked
  files in place, so never run it concurrently with `run_all`.
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

## 2b. Where the work stands — SINGLE SOURCE OF TRUTH IS THE TICK PROMPT

**Current state and the work queue live in `local_only/scratch/hardening_tick_prompt.md`, not here.**

This section used to carry both, and it drifted out of date within hours of a repair tick: an agent
reading it on 2026-08-20 was told, as a live instruction, to "restore the two weakened tests first" —
work that had already landed as `fce7f8df` the previous evening. Duplicated state is how a protocol
starts lying, and a stale instruction costs a whole unit before anyone notices.

So this file is now **only the durable part**: the hard rules, the paid-for hazards, the census
scripts, the tick types, and the runtime. Those change rarely. Anything with a date on it — verdict
counts, provider counts, what is done, what is next — is in the tick prompt, which is rewritten every
tick.

**If the two ever disagree, §0's own measurement wins over both** (§0, first paragraph). Neither file
is evidence; they are notes about evidence.

### Carried forward — two named gaps, still open

Both were named from competency text and neither is plausibly satisfied by a generic formatter, so
they survive §6D and are real work rather than reporting artifacts:

- **`mat_g2_na_q3_1`** — the competency enumerates seven representations (concrete models, pictorial
  models, numerals, equal groups, arrays, counting by multiples, equal jumps on a number line). Start
  at Tick F Step 1: `fmt_number_line.py` already exists and `adapter.py` routes it twice, so the
  number-line jumps may be a gate to open rather than a formatter to build.
- **`mat_g3_dp_q3_1`** — *"Present data in **tables** and single bar graphs"*, where `COMPATIBILITY`
  offers only the two bar-chart formatters.

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
   (As of 2026-08-20 all 151 nodes declare, so this step is now the exception rather than the rule —
   but a node that somehow lacks a `requires` block is still declared before it is diagnosed.)
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
grep -n "<capability>" backend/app/practice_gen/adapter.py backend/app/practice_gen/compatibility.py
# locate the registries by name, never by line number -- they drift, and an earlier
# revision of this file shipped four stale ones:
grep -nE "^(FORMATTER_ROUTES|COMPATIBILITY|VARIANTS_BY_DNA|FORMATTER_VARIANT_SUPPORT|CURRICULUM_VARIANT_GATES|FORMATTER_NUMERIC_LIMITS|NODE_TO_DNA|DNA_MODULE_MAP)" \
  backend/app/practice_gen/adapter.py backend/app/practice_gen/compatibility.py \
  backend/app/practice_gen/registry.py backend/app/practice_gen/validation/_manifest.py
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
| a **formatter** | `adapter.py` `FORMATTER_ROUTES` → `compatibility.py` `COMPATIBILITY` for each DNA that may use it → `FORMATTER_VARIANT_SUPPORT` → `schemas/visuals.py` `VisualSchemaRegistry` if visual → `FORMATTER_NUMERIC_LIMITS` if it can't render arbitrary magnitudes |
| a **variant** | `compatibility.py` `VARIANTS_BY_DNA` → `FORMATTER_VARIANT_SUPPORT` → `CURRICULUM_VARIANT_GATES` if grade/quarter-gated → the binding in `registry.py`'s `_parse_competency_bounds`, or nothing will ever select it |
| a **DNA** | `dna/<domain>/<name>.py` → `validation/_manifest.py` `DNA_MODULE_MAP` → `compatibility.py` `COMPATIBILITY` (keys must match `DNA_MODULE_MAP` exactly; `_manifest.py` asserts this at import) → `registry.py` `NODE_TO_DNA` → `axes_catalog.py` for its difficulty axes |

**Then register the capability** in `validation/validate_capability.py` `CAPABILITY_PROVIDERS`,
pointing at the artifact you just built — never at a generic textual formatter (Rule 9) — and get an
Attester verdict on a rendered sample before you commit.

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

### Tick G — green arrived, and you have not yet earned the right to believe it
**Trigger:** `run_all` exits 0, **or** the census went green since the last ledger entry, **or** any
part of the green was produced by something other than this loop's own ticks.

**Why this tick exists ahead of Tick D.** Every other trigger in this protocol fires on *red* — red at
a machine stage, a gate that cannot detect fabrication, missing reviews, non-PASS verdicts, a
capability with no provider. There was no trigger for green, and green is this project's
characteristic failure: fabricated reviews twice, and a neutralised §6C once. A defeated check exits 0
exactly as happily as a working one, so an exit code cannot be the thing that ends the work.

**Do — audit *how* green was reached, not merely that it was:**

1. **Re-derive every number yourself** — the §0 census, the gate-health sweep, and the capability
   census. Do not read them from the ledger or from a previous tick's report.
2. **Interrogate the reference data behind every passing check** (Rule 3), by deletion rather than by
   eye. A check is only as strong as the table it consults, and that table is where a green run is
   cheapest to fake. Run all three **reference-data probes** below this list — providers,
   `requires_ignore`, `_STOPWORDS` — and report all three results, not only the one that failed.
3. **Sample the judgment layer directly** — skeleton clustering, phantom quotes, reviewer plurality,
   freshness. The census reports these; look at three or four actual rationales anyway and ask whether
   a reviewer who could not see the generator could have written them.
4. **Diff `git log` against the ledger *and* against the evidence log.** Commits with no
   corresponding ledger entry were produced outside this loop and carry no evidence trail; commits
   that changed the pipeline without touching `HARDENING_EVIDENCE.md` carry no receipt (Rule 7).
   Inherit nothing from either — verify. Naming which commits you verified, and how, is the most
   useful thing this tick writes.

   ```bash
   git log --oneline --since=<last-audited-date> | wc -l
   git log --oneline --since=<last-audited-date> -- validation_reports/HARDENING_EVIDENCE.md | wc -l
   ```

5. **Read every test diff in the window.** A rewritten test is the cheapest possible way to make a
   check stop noticing, and it reads as refactoring in review (Rule 3). For each changed test, check
   out the *pre-edit* assertion and run it against the current tree. If it fails, the commit did not
   satisfy the check — it removed it, and the failure is your work item.

   ```bash
   git log --oneline --since=<date> -- tests/ | cat
   git show <sha> -- tests/            # then re-run the OLD assertion by hand
   ```

   Measured 2026-08-19: two of three test edits in the window fail when their pre-edit assertions are
   re-run — `test_unprovided_capability_names_the_node_and_the_clause` and
   `test_orchestrator_sets_dna_name_for_ordering`.
6. **Say which layers are genuine and which are not, layer by layer.** The answer is always mixed, and
   reporting it as mixed is the point. The worked example is the 2026-08-19 audit: the judgment layer was
   genuine (151 PASS, skeleton cluster 1, 0 phantom quotes, 127 distinct reviewers, 0 gate errors),
   §6A provenance was genuine, §6B was partly earned, §6C was neutralised, and two unit tests had
   been rewritten around their own failures. Tearing up all of it because part failed would have
   destroyed real work; accepting all of it because `run_all` exited 0 would have shipped a defeated
   gate. Neither is available to you — you have to say which is which, and show the command.

#### Tick G reference-data probes

Run at column 0, not nested — the heredoc terminator must be unindented or the script never closes.

**(a) Providers** — §0's delta census. `UNEARNED §6C PASSES > 0` means §6C is reporting on nothing.

**(b) `requires_ignore`** — a competency word parked here is a requirement silently dropped (§6B):

```bash
PYTHONPATH=. .venv/bin/python3 - <<'PY'
import json
kg = json.load(open('data/knowledge_graph_g1_3.json'))
nodes = kg.get('nodes', kg)
items = nodes.items() if isinstance(nodes, dict) else [(n.get('id'), n) for n in nodes]
FUNCTION = {'a','an','and','or','the','of','to','in','on','for','with','by','as','at','from',
            'into','is','are','be','using','use','such','including','e','g',',',':',';',"'",
            'its','their','both','where','which','that','this','than','then','if','when'}
for nid, n in items:
    if not isinstance(n, dict):
        continue
    sus = [w for w in (n.get('requires_ignore') or []) if w.lower() not in FUNCTION]
    if sus:
        print(f'{nid}: {sus}\n    {n.get("competency", "")[:120]}')
PY
```

**(c) `_STOPWORDS`** — did the list grow to swallow content words?

```bash
git log -p -- backend/app/practice_gen/validation/validate_capability.py \
  | grep -E '^\+.*_STOPWORDS' -A 10 | head -40
```

Measured 2026-08-19: (b) flags 37 nodes, 25 of which park an unambiguous content word — including
`mat_g1_na_q2_2` ignoring `place` and `value`. The other 12 are borderline (`involving`, `given`,
`e.g.,`) and are a judgment call to record, not necessarily a defect.
(c) is clean — `_STOPWORDS` is unchanged since the file was created.

**Then:** if the audit is clean, Tick D fires and the work is done. If it is not, the layer that failed
becomes your next unit — and the ledger records what you audited, what held, and what did not.

### Tick D — census is 151 PASS
**Trigger:** `run_all` exits 0 (which now also means all 151 nodes declared and every declared
capability provided), zero CONCERN, zero FAIL, gate hardened, census clean — **and Tick G's audit has
passed.** Exit 0 alone does not fire this tick; it fires Tick G.

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
## <ISO date/time> — Tick <0|A|B|C|D|E|F|G>
- **Census before:** PASS=… CONCERN=… FAIL=…   (gate: stale=… non-verdict=…)
- **Unit(s) of work:** <one sentence each — a tick may hold several>
- **Root cause:** <one sentence, or n/a>
- **Machinery built:** <formatter/variant/axis/DNA + every registry wired, or "none">
- **Files touched:** …
- **Verification:** <command> → <verbatim summary line>
- **Blind verdicts obtained:** <Declarer / Attester / Reviewer / Evaluator batches, or "none">
- **Evidence log entry:** <the HARDENING_EVIDENCE.md heading you appended, or why the unit needed none>
- **Census after:** PASS=… CONCERN=… FAIL=…   (unearned §6C passes: …)
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

---

## 6. Runtime — how this loop runs in Claude Code

**Cadence is `/loop`. There is no external supervisor, and you must not build one.**
`scripts/run_hardening_daemon.py` and `scripts/autonomous_hardening_driver.sh` are **retired**
(2026-08-19). They were an outer-loop process supervisor written for a different CLI, and they were
worse than nothing on three counts, each worth remembering as a shape:

- The daemon **only ever executed `--dry-run`** — its entire log is one simulated cycle. It looked
  like infrastructure and supervised nothing.
- It pointed at a **compressed 11 KB derivative** of this protocol whose §0 omitted the capability
  census entirely. That is the precise blind spot that let 392 wildcard providers through: the agent
  ran a census that could not see the thing that was broken.
- The driver ended with `run_all ... || echo "exit code: $?"` and `git status ... || true`, so it
  **always exited 0**. A monitor that cannot report red is a monitor that reports green.

Copies are preserved under `local_only/scratch/retired_daemon/` if you need the history. Do not
revive them, do not schedule cron wakeups, and do not write a second, shorter version of this file —
the short version is how the blind spot got in.

**Dispatching the four blind roles.** Use the Task tool, one agent per role, one batch per call:

- **Blindness is a prompt contract, not a sandbox.** A subagent *can* read `dna/`; it must be told
  not to, in its own prompt, with the paths named (Rule 1's "Must never" column, verbatim). Include
  only the packet — competency text, grade/quarter/vocab metadata, rendered samples — and never the
  diff, the generator, your diagnosis, or what you hope the answer is.
- **Prompt neutrally.** "Score PASS/CONCERN/FAIL by accuracy", never "find the defects" —
  defect-hunting framing was measured to bias verdicts toward FAIL.
- **Batch ≤25 nodes (or capabilities) per agent**, 2–3 batches per tick, so a killed tick loses one
  batch rather than the run.
- **An Attester batch carries no node ids in its verdict prompt** beyond what the samples show. It
  answers one question per capability: *do these rendered items exhibit what this clause names?*

**Running the harness.** A full `run_all` is a **background** command — launch it with
`run_in_background`, keep working on scoped `--node` runs, and read the exit line when it lands.
Do not block a tick on it and do not skip it because it is slow.

**Process hygiene — run this FIRST, before §0, every tick. This is not optional.**

A hung background job silently kills the whole loop. `/loop` cron ticks fire **only while the REPL is
idle**, so one stuck process means no tick ever fires again — and because it fires nothing, it also
reports nothing. On 2026-08-19 a `pytest tests/unit` deadlocked at 20:41 and the loop went dark for
five hours; four scheduled ticks never ran, and the failure was invisible until a human asked why.

A monitor that cannot report red is a monitor that reports green (§6's retired-daemon lesson). A loop
that cannot report *stalled* is the same thing.

```bash
# Anything Python-shaped that is old and barely burning CPU is hung, not slow.
ps -eo pid,etime,time,comm,args | grep -E "[p]ytest|[r]un_all|practice_gen" | \
  awk '{print $1, "elapsed="$2, "cpu="$3, $4}'
```

Judge by the **CPU-to-elapsed ratio**, never by elapsed alone: a healthy `run_all` worker burns ~50%
of a core, so ~25 min CPU per 50 min wall. Under a few percent for more than ~10 minutes is a hang.

- **Remediate it.** `kill -9 <pid>`, then say so in the ledger with the pid, the elapsed time, and
  what it was. Do not tiptoe around a stuck process and do not "wait a bit longer" — it is not going
  to finish.
- **Diagnose before killing when it is cheap**: `sample <pid> 3` names the blocking call in seconds,
  and a reproducible hang is a bug worth a unit, not just cleanup.
- **Distinguish yours from someone else's.** A process from an earlier session is still blocking the
  loop and should still be cleared, but say whose it was.

**Never end a tick with a background job still outstanding.** Launching `run_all` in the background
is correct; *ending the tick without reading its exit line* is not. Before you write the ledger
entry, either the job has landed and you have recorded its result, or you have killed it and recorded
that you did. An outstanding job is what stops the next tick from ever starting.

**Ending a tick.** The tree is committed, the ledger has its entry (§4), the evidence log has its
verbatim output (Rule 7), and `Next tick should:` names the first item for your cold future self.
A tick that ends mid-unit with an uncommitted tree has produced nothing a later tick can trust.
