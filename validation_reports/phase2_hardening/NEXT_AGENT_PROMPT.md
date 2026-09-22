# Task prompt — close out the 2026-09-22 session's owed fixes

You are working in the repository at `/Users/enrichmentcap/Documents/antigravity/ccmed`.
Your job is a **closeout batch**: apply the fixes a previous session landed but deliberately
deferred, then re-prove the tree, so the next Phase 2 hardening session starts from a clean,
certified, internally-consistent state.

This is not exploratory work. The decisions are already made and the owner has already ruled.
Your job is to execute them exactly, verify by running things, and report honestly.

---

## 0. Ground rules you may not break

Read `CLAUDE.md` / `AGENTS.md` in the repo root first. The ones that will bite you here:

1. **Verification is execution.** Never report something fixed without running it and showing
   the verbatim output. A prediction phrased as a confirmation is a lie. Every claim in your
   final report needs the command that produced it.
2. **Never weaken a check to make it pass.** If a gate goes red, the bug is in the pipeline.
3. **Fail fast.** No bare `except`, no `|| true`, no warn-and-continue.
4. **You never author an Attester or Reviewer verdict.** Blind evidence comes from a dispatched
   agent that has neither the answer key nor your context. If a step seems to require you to
   judge rendered student content yourself, **stop and report** — you have misread the step.
5. **Leave every limitation named in writing** — docstring, `docs/pgen_contract.md` row, and
   the evidence log.

**Invocation:** always `PYTHONPATH=. .venv/bin/python …`. There is no usable bare `python` and
no `timeout` on this host.

---

## 1. Establish state before touching anything

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py          # expect: PASS ... CERTIFIED
PYTHONPATH=. .venv/bin/python tests/hardening_status.py    # expect: PASS ... 10 H-row(s) valid
```

Expected reading:

```
PASS tree_state: CERTIFIED
  live input digest : 124ee1ca14d20526
  worktree          : clean
  mutation_proofs         fresh  152 file(s)
  release_shards          fresh  6 file(s)
  obligation_benchmark    fresh  1 file(s)
  frontend_static_render  fresh  1 file(s)
```

**If either command disagrees with this, believe the command, not this file**, and say so in
your report before continuing.

Then claim the work-lock and record your intent:

```sh
# In validation_reports/phase2_hardening/hardening_status.json, H-06's "owner" currently
# reads "released @ d86c9508". Change ONLY that one line to your own session id.
PYTHONPATH=. .venv/bin/python tests/hardening_status.py    # must still PASS

PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin batch \
    --session "<your-session-id>" --note "closeout: 3 string corrections + §1M operator doc + batch116 prevalence filing"
```

**Edit that ledger file SURGICALLY.** Do not round-trip it through `json.dumps` over the whole
file — that renormalises `§`/`—` escapes across rows you do not own and produced 16 lines of
collateral churn for a previous session. After editing, `git diff --numstat` must show exactly
the lines you meant.

---

## 2. What you are fixing, and why each was deferred

A session on 2026-09-22 landed two owner-authorised source fixes and ran the full re-proof
chain. Along the way it discovered that one of its own evidence claims was overstated. It did
**not** correct that claim, because the offending text lives in digest-bound files and editing
a comment would have invalidated a 152-record mutation corpus and six release shards that had
just cost ~3.4 hours to prove. That deferral was deliberate and correct. You are the batch that
pays it, at the START of a batch rather than the end.

### The substance of the correction

The renderer concurrency defect in `tests/frontend_renderer.py` was real and is fixed. It was
originally justified by **two** measured symptoms:

* **§6F reported 55 findings under concurrent load on a tree that had 61** (three clean runs
  all reported 61). This one is real and remains the evidence for the fix.
* **"§5 reported 1253 where it has 1252."** This one was **misattributed.** It is not a
  concurrency effect at all. `run_all._stage_judgment_reviews_5` (`run_all.py:760-764`) calls
  the module and then appends one aggregate finding that the module's own CLI never emits:

  ```python
  judgment_errors = validate_judgment.validate_judgment_reviews(fail_fast=fail_fast)
  v = validate_judgment.summarize_verdicts()
  if v["FAIL"] > 0 or v["CONCERN"] > 0:
      judgment_errors.append(f"Unresolved judgment verdicts remain across {v['reviewed']} nodes: ...")
  ```

  So 1252 (module) + 1 (rollup) = 1253 (stage). Both numbers are correct for their own entry
  point. Measured directly, nothing running: `module 1252`, `reviewed=151 PASS=14 CONCERN=93
  FAIL=44`, stage 1253.

Three digest-bound files still carry the overstated sentence. You are correcting all three.

---

## 3. Source batch — do ALL of it before any re-proof

### 3a. `tests/frontend_renderer.py` (module docstring, around line 18-21)

Replace exactly:

```
    run attached the other run's visual evidence to its own samples. Measured cost: §6F
    reported 55 findings on a tree that had 61, and §5 reported 1253 where it has 1252. No
    crash, no warning, two corrupted figures in opposite directions.
```

with:

```
    run attached the other run's visual evidence to its own samples. Measured cost: §6F
    reported 55 findings under concurrent load on a tree that had 61, against 61 on three
    clean runs. No crash and no warning.

    CORRECTED 2026-09-22: an earlier draft of this docstring also cited "§5 reported 1253
    where it has 1252" as a second symptom. That figure was MISATTRIBUTED and is not this
    defect. `run_all._stage_judgment_reviews_5` appends one aggregate finding the module's
    own CLI never emits, so 1252 (module) and 1253 (stage) are both correct for their entry
    point. Quote the entry point alongside any §5 figure.
```

### 3b. `tests/mutation_harness.py` (the `renderer_case_id_omits_node_id` description, ~line 1950)

Replace exactly:

```
            "Measured cost before the fix: §6F reported 55 findings on a tree that had "
            "61, and §5 reported 1253 where it has 1252. Deliberately NOT aimed at the "
            "loud RuntimeError -- a plant that only trips that guard proves nothing new."
```

with:

```
            "Measured cost before the fix: §6F reported 55 findings under concurrent load "
            "on a tree that had 61, against 61 on three clean runs. (A §5 figure was also "
            "cited originally and was misattributed -- see the module docstring.) "
            "Deliberately NOT aimed at the "
            "loud RuntimeError -- a plant that only trips that guard proves nothing new."
```

### 3c. `docs/pgen_contract.md` (line 61, the renderer row)

Replace exactly:

```
**Measured cost, in both directions and with no crash: §6F reported 55 findings on a tree that had 61, and §5 reported 1253 where it has 1252.**
```

with:

```
**Measured cost, with no crash: §6F reported 55 findings under concurrent load on a tree that had 61, against 61 on three clean runs. CORRECTED 2026-09-22 — a §5 figure of 1253-against-1252 was originally cited here as a second symptom and was MISATTRIBUTED: `run_all`'s §5 stage appends one aggregate finding the module's own CLI never emits, so both numbers are correct for their entry point.**
```

### 3d. `docs/testing_pipeline.md` — document `§1M`

**Read this before acting, because the previous session first got this wrong and corrected
itself.** `operator_doc_covers_registry` reports **40/41**. The single unnamed ref is **`§1M`**,
NOT the new renderer row, and the gap **predates** the 2026-09-22 batch — there were already 41
registry refs before it. Verify for yourself rather than taking my word:

```sh
PYTHONPATH=. .venv/bin/python -c "
from backend.app.practice_gen.validation import run_all as ra
from pathlib import Path
refs=set(ra.CONTRACT_CHECKS)
text=Path('docs/testing_pipeline.md').read_text(encoding='utf-8')
named={r for r in refs if r in text}
print(len(named),'/',len(refs),'| NOT named:',sorted(refs-named))
"
```

`§1M` is the dangling-referent stage added 2026-09-21: **a stem that points at a display must
be served with one.** Add a short operator-facing paragraph describing it, in the same voice and
level of detail as the neighbouring check descriptions in that file. Name its limitation
honestly, because it is already named elsewhere and a doc that omits it is how the next reader
stops looking: **§1M's deixis pattern list is CLOSED** (a stem that points in wording nobody has
seen is not caught, and the pattern count prints with the pass line so the hole's size is a
number); it **cannot tell whether the drawn visual is the RIGHT one**; and it **reads stems, not
hints**, so a display the pupil needs but the stem never mentions is invisible to it.

This check is a **floor of 12, deliberately not equality** (`run_all.py:1051-1053`) —
`testing_pipeline.md` is prose explaining a subset. So this is documentation debt, not a gate
failure. Do not pad the file to chase 41/41.

### 3e. Sanity-check the source batch

```sh
PYTHONPATH=. .venv/bin/python -c "
from backend.app.practice_gen.validation import run_all as ra
refs = ra._parse_contract_section_refs()
print('doc refs not in registry:', sorted(r for r in refs if r not in ra.CONTRACT_CHECKS) or 'NONE')
print('registry keys not in doc:', sorted(k for k in ra.CONTRACT_CHECKS if k not in refs) or 'NONE')
"
```
Both must print `NONE`.

**Commit the source batch now**, before the attestation work, so the chain's "benchmark after
the last source commit" rule is easy to satisfy.

---

## 4. Attestation — file `batch116`, and do NOT judge anything yourself

### The ruling you are implementing

**Owner ruling 9 (2026-09-22): prevalence is now part of the Attester standard.** An Attester
must weigh HOW OFTEN a clause is exhibited across the samples shown, not merely whether any one
sample exhibits it. The owner has since directed that this be applied to the four nodes touched
on 2026-09-22.

Measured basis: on the same 18 clauses, same packets, same Haiku model, the only variable being
whether the prompt asked for prevalence — prevalence-weighed returned 6 NOT_PROVIDED, neutral
returned 2.

### Owner ruling 10 (2026-09-22) — the dispatch model for THIS agent

**Owner ruling 4 said "Haiku subagents for ALL agents reviewing sample pg output."** That was
written for a Claude-hosted session, and its purpose was cost and rate-limit safety: a wave of
8 Opus dispatches once hit the session rate limit and killed 14 agents mid-flight.

**Ruling 10 amends it for this agent: use `gpt-terra` light-thinking subagents for every blind
dispatch you make.** The principle is unchanged — a cheap, separate, blind judge — only the
model name differs, because you are not running on Claude.

**What does NOT change, and is not negotiable:**

* **You still never author a verdict.** Dispatch, or stop.
* **The record must name the model that ACTUALLY judged.** `attested_by` is what makes §6H
  attester plurality and §5 reviewer plurality checkable at all. Writing `haiku` on a
  `gpt-terra` verdict — or the reverse — is a false evidentiary claim.
* **The reviewer identity is assigned by the DISPATCHER**, never self-declared by the judge. On
  2026-09-10 three independently dispatched blind agents given the same prompt all converged on
  variations of one self-chosen name, which would have silently collapsed plurality.
* **Keep concurrency modest**, for the same reason ruling 4 existed.

**CONSEQUENCE YOU MUST CARRY INTO YOUR HANDOFF — this is a second instrument variable.** The
741 verdicts already in `validation_reports/attestation/` were judged by Claude models. Any
`gpt-terra` verdict you add is a different rater *family*, not merely a different rater. The
measured 88.1% inter-rater agreement (76.5% on the hardest batch) was **Haiku-against-Haiku**
and does **not** transfer across families — cross-family agreement is unmeasured.

That matters because this session already found one instrument change masquerading as a content
finding: a prompt that asked for prevalence flipped 6 of 18 clauses that two independent raters
had each passed. A model-family change is the same class of variable. So:

* **Do not read a `gpt-terra` NOT_PROVIDED against a Claude-era PROVIDED as a regression.** It
  may be either a genuine finding or a family effect, and nothing currently distinguishes them.
* **Say so plainly in your handoff**, alongside the ruling-9 mixed-standard warning. The two
  compound: after this batch the corpus can differ in both *standard* and *rater family*.
* If anyone wants that separated, the clean experiment is the same shape as the ruling-5
  control — same prompt, same packets, vary only the family — and it is **not** your batch.

### What you file, and why you are not dispatching

**Both sets of verdicts already exist on disk and were earned by a genuine blind Haiku
Attester** (identity `blind-attester-haiku45-b115-20260922`, ruling 4 compliant):

| file | standard | use |
|---|---|---|
| `local_only/scratch/attest115/<node>.verdicts.json` | **prevalence-weighed** | **FILE THESE** |
| `local_only/scratch/attest115/<node>.neutral.verdicts.json` | neutral (superseded) | already filed as `batch115` |

for the four nodes `mat_g1_na_q3_7`, `mat_g2_mg_q2_0`, `mat_g2_mg_q2_2`, `mat_g3_mg_q2_3`.

The prevalence verdicts were returned in one dispatch whose item ids collided across nodes
(`attester_packets.py` numbers items per invocation, so four nodes each produced `item_001` —
a real, still-unguarded trap). They were split per node by a **positional join that was verified
exact**, position by position, against the packet order. Re-verify before filing:

```sh
PYTHONPATH=. .venv/bin/python - <<'PY'
import json, glob
from pathlib import Path
for f in sorted(glob.glob("local_only/scratch/attest115/*.packets.json")):
    node = Path(f).name.split(".")[0]
    blob = json.load(open(f)); packets = blob["packets"] if isinstance(blob, dict) else blob
    verdicts = json.load(open(f"local_only/scratch/attest115/{node}.verdicts.json"))
    assert len(packets) == len(verdicts), (node, len(packets), len(verdicts))
    for p, v in zip(packets, verdicts):
        assert p["item"] == v["item"], (node, p["item"], v["item"])
    print(f"{node:18s} {len(packets)} items, join OK, "
          f"{sum(1 for v in verdicts if v['verdict']=='PROVIDED')} PROVIDED")
PY
```

**If those scratch files are missing or the join assertion fails, STOP.** Do not reconstruct
verdicts and do not write your own. A fresh blind dispatch is then required, and under **owner
ruling 10** (below) it goes to a **`gpt-terra` light-thinking subagent** — given per-node prompt
files rendered by `tests/attester_packets.render_prompt_block`, with a prompt that states the
prevalence standard and the medium test **without encoding the answer** (owner ruling 1).

Name that dispatch's identity for the model that actually judged, e.g.
`blind-attester-gpt-terra-light-<batch>-<YYYYMMDD>`. **Never label a `gpt-terra` verdict as
Haiku or vice versa** — §6H attester plurality and §5 reviewer plurality are only checkable if
the record is truthful about who made the verdict, and a mislabelled identity is a false
evidentiary claim, not a cosmetic slip.

### Filing

Batch prefix must sort **after** `batch115` — use `batch116`. Records resolve last-file-wins
over a sorted glob.

```sh
TOOLUSES="prompt-contract dispatch to a separate Haiku subagent: told to read exactly four packet renders under local_only/scratch/attest115/ and no other path, and to return verdict JSON. Tool access was NOT structurally prevented, so this does not claim the '0' (inline, no tool access) contract."
DELIVERY="the Attester read attester_packets.render_prompt_block output (item id, clause, competency, grade/quarter and the rendered samples only), verified before dispatch to contain no node id, no capability id and no provider table."

PYTHONPATH=. .venv/bin/python -m tests.attester_file \
  --packets local_only/scratch/attest115/<node>.packets.json \
  --key     local_only/scratch/attest115/<node>.key.json \
  --verdicts local_only/scratch/attest115/<node>.verdicts.json \
  --batch-prefix batch116 --attested-at 2026-09-22T00:00:00Z \
  --attested-by blind-attester-haiku45-b115-20260922 \
  --action-provided "no action needed; the clause is exhibited by the rendered samples" \
  --actions <actions.json>   # REQUIRED for every NOT_PROVIDED item \
  --tool-uses "$TOOLUSES" --samples-delivery "$DELIVERY"
```

Every `NOT_PROVIDED` needs an `action_taken`. Write them to say what is true: **the finding is
recorded and NOT acted on**, because the reproducibility rule (88.1% inter-rater agreement,
76.5% on the hardest batch) forbids committing engineering effort to a lone CONTRADICTED before
a second independent dispatch confirms it. Do not build artifacts or delete provider entries for
these.

### Then measure, ALONE

```sh
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.validate_capability --phase 2
```

**EXPECT THE COUNT TO RISE — from 53 to roughly 57.** That is the ruling working, not a
regression. A count that rises because the instrument got sharper is progress. Record the exact
number and its composition; do not tune anything to bring it back down.

Note: attestation records live outside `INPUT_ROOTS`, so **this step costs no re-proof.**

---

## 5. The re-proof chain — source work is done, now pay it once

Order matters. Each step's trap is named because it has cost a previous session real time.

```sh
# 1. Anchor scan. Two seconds here versus a fifty-minute abort at 54/152.
PYTHONPATH=. .venv/bin/python -c "
from pathlib import Path; import tests.mutation_harness as mh
print([(m.name, r) for m in mh.MUTATIONS if m.edits for r,(f,_) in m.edits.items()
       if Path(r).read_text().count(f) != 1] or 'all anchors OK')"

# 2. Formatter exclusions. NEVER hand-edit the generated file.
PYTHONPATH=. .venv/bin/python -m scripts.regen_formatter_exclusions

# 3. Frontend static render artifact (~10s)
PYTHONPATH=. .venv/bin/python tests/frontend_suite.py

# 4. Benchmark — AFTER your last source commit, or obligation_benchmark_11 is red at
#    baseline and its mutation scores INVALID rather than DETECTED.
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000

# 5. Mutation corpus (~70 min). Run it in the background and do nothing else meanwhile.
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py

# 6. Release shards — SIX. See the warning below. (~2.6h total, sequential)
for i in 0 1 2 3 4 5; do
  PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier release --shard-count 6 --shard-index $i
done
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier verify-release

# 7. The Definition of Done, run ALONE, output shown in full.
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
```

**⚠ THE BENCHMARK LIES ABOUT SHARD COUNT.** Step 4 prints `recommended_shards=4`.
`validate_obligations.py:165` **hard-codes `shard_count = 6`**. Follow the validator, not the
recommendation — four receipts will fail §11 on coverage. The projected total wall time is also
computed from the count it recommends, so treat it as a per-shard figure only. Measured
six-shard reality: 96,885 cache keys and 387,540 represented executions per shard, 0 failures,
aggregate 9,333s = 2.593h, worst shard 1,588.9s against the 1,800s per-shard budget.

**Also:** the fast unit suite takes **11 minutes**, not the 35 seconds an old note claims, and
`tests/pytest.ini`'s `addopts` is not picked up from the repo root. If you run it directly, pass
`-m "not slow"` explicitly or two 15–40 minute pool tests run too. `run_all` handles this itself.

**The pre-commit hook rebuilds Graphify and stages `graphify-out/`.** Expect more files in your
commit than you staged. It does not move the input digest — verify that rather than assume it.

---

## 6. What "done" looks like, and what it does NOT

`run_all` **will exit 1.** That is expected and is not your failure. Three stages are red and all
three are known, tracked work under `H-06`:

| stage | expected | why it is red |
|---|---|---|
| `capability_phase2` | ~57 (up from 53) | genuine content debt + ruling 9's sharper instrument |
| `judgment_reviews_5` | 1252 module / **1253 stage** | the 151 owed blind re-reviews. **Quote the entry point.** |
| `assertion_coverage_8` | 3 in 1 family | the §6F mutation cluster, INVALID against a red `capability_phase2` baseline. Re-running cannot fix it. |

**Your success criteria are:**

1. All four source corrections landed, with `contract_doc_matches_registry` and
   `operator_doc_covers_registry` both PASS (the latter should now read **41/41**).
2. `batch116` filed; `capability_phase2` measured alone and its new number recorded.
3. Mutation corpus at **149/152 or better**, with the 3 survivors being exactly the §6F cluster
   (`contradicted_attestation`, `attestation_drops_options`, `attestation_leaks_into_phase1`).
   **Any other survivor is a real hole — diagnose it, do not wave it through.**
4. `tests/tree_state.py` reports **CERTIFIED**.
5. `tests/hardening_status.py` PASSes, with `H-06` released at your commit hash.

**A surviving mutation has two causes and you must distinguish them:** either the check is
broken, or the plant no longer reaches the code the validator runs. Diagnose by instrumenting
the real path — render the sample, print the value, prove the planted bug arrives — never by
reading the validator and concluding it would work.

---

## 7. Bookkeeping before you finish

* **Evidence section in `validation_reports/HARDENING_EVIDENCE.md`**: exact commands, verbatim
  pass/fail output, seeds for anything found. Without it the task is not done.
* **Update `H-06`'s row** in `hardening_status.json` (surgically), then **release the lock in a
  FOLLOW-UP commit** — `git commit --amend` moves the hash, leaving a `released @ <hash>` row
  pointing at a dangling commit.
* **Close your intent**: `tests/tree_state.py --complete --note "…"`.
* **Update `validation_reports/phase2_hardening/HANDOFF_PROMPT.md`**: refresh the expected-digest
  block and the banner at the top so the next session inherits true numbers. That file and the
  evidence log are outside `INPUT_ROOTS`, so editing them costs nothing — **verify that with
  `input_digest()` rather than assuming it.**

## 8. What is explicitly NOT yours

Do not start these, and do not let them expand your batch:

* The **151 owed §5 blind re-reviews** (7 dispatches via `tests/judgment_batches.py`).
* The **corpus-wide ruling-9 re-dispatch campaign** (~33 `gpt-terra` light-thinking dispatches). Ruling 9 is now the
  standard, so all 741 previously filed verdicts were earned on a superseded instrument and the
  corpus is mixed until that campaign runs. **Say this plainly in your handoff** — it is the
  single most important thing the next session needs to know about what `capability_phase2`'s
  number currently means.
* The **~51 CONTRADICTED content findings**, and the still-unfixed **supersession test**.
* Opening an `H-11` row. The owner has already refused one.

If you find something genuinely broken that is outside this list, **name it in your report
rather than fixing it.** A closeout batch that grows is a closeout batch that does not close.
