# Task prompt: continue Phase 2 hardening (fresh GPT-hosted session)

**Rewritten 2026-09-30 after the Phase D source batch landed. This REPLACES every earlier version of
this file.** `GPT_HANDOFF_PROMPT.md` beside it is finished history; do not execute it.
`CLAUDE_AGENT_PROMPT.md` is the same plan written for a Claude host; its §5–§10 hold the long-form
method and traps this file summarises. Where sources disagree, trust them in this order: a command you
executed, then this file, then `CLAUDE_AGENT_PROMPT.md`, then the dated blocks in
`docs/phase2_hardening_completion_plan.md`.

You are working in `/Users/enrichmentcap/Documents/antigravity/ccmed`, on the practice-problem
generator hardening for the Adaptive K-12 Mastery Engine. The goal is to move
`PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all` toward exit 0.
It will not reach 0 this session. Leave it closer to 0, with every claim proven by execution.

---

## 0. Read first, in this order

1. `CLAUDE.md` / `AGENTS.md`. The Scaling Mandate, Engineering Protocols, Content Rules and Definition
   of Done bind you completely.
2. This file.
3. `validation_reports/HARDENING_EVIDENCE.md`: the last three entries (Phase B, Phase C, Phase D).
4. `CLAUDE_AGENT_PROMPT.md` §5 (review method), §6 (the 173), §7 (heavy runs), §9 (traps),
   §10 (known-red) and §11 (not yours).

---

## 1. State at handoff (re-measure it; never quote these numbers without re-running)

```
HEAD                  5489d597 (lock released); tree_state CERTIFIED at digest 7253f2a3e89f1566
run_all               EXIT 1, scheduled=17 completed=14 failed=3 crashed=0
  judgment_reviews_5    2020 findings, 143 of 151 reviews STALE
  capability_phase2     188 = 173 CONTRADICTED + 15 STALE attestations
  assertion_coverage_8  3: the §6F mutation cluster; clears only when capability_phase2 reaches 0
every Phase 1 stage   PASS (content, vocabulary, matrix, render, grading, obligations, census)
mutation corpus       187/190 DETECTED; the 3 INVALID are the §6F cluster
obligations           458 pairs, 4,249 base, 458,892 finite, 2,294,460 executions; 6 release shards clean
review corpus         151/151 schema-v2: 120 haiku45, 17 gpt-5.6-luna, 14 gpt-6-luna
H-06                  status open; lock released ("released @ 300f6263")
```

Commands that re-measure this state:

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.validate_judgment --all > /tmp/vj.log 2>&1; echo "EXIT $?"
```

**Why 143 reviews are STALE:** Phase D reworded the interest-cue sentence from "*X has a math challenge
about Y*" to "*X enjoys Y. Here is a math challenge.*" That wording appears at seeds 701/702 on every
node. Of the 143, **136 are stale only because of that sentence**; this was established seed by seed.
**Seven have real content changes:**

- `mat_g2_na_q2_2`
- `mat_g2_na_q3_2`
- `mat_g2_na_q3_3`
- `mat_g3_dp_q3_2`
- `mat_g3_mg_q2_1`
- `mat_g3_mg_q2_4`
- `mat_g3_na_q3_0`

Staleness is by packet digest. **It is never waived, and no verdict is ever carried forward.**

---

## 2. OWNER GATES: resolve these before any dispatch

Record the owner's answers here, or in the session, before starting W1 or W2.

**Gate A: reviewer model.** Owner ruling 4 makes **Haiku** the family for every blind reviewer, and
the plan says: *"If you cannot dispatch Haiku from this host, STOP and ask the owner."* A GPT host
usually cannot dispatch Haiku. So:
- If you **can** dispatch Claude Haiku 4.5, use it, and put `haiku45` in every identity.
- If you **cannot**, stop and ask the owner which model to use. **Do not substitute one silently.**
- Whatever judges, the identity names the model that actually judged, including its reasoning level.
- Never rename the 17 `gpt-5.6-luna` or 14 `gpt-6-luna` records, and never write one model's name onto
  another model's verdict.

**Gate B: scope.** Re-reviewing 143 nodes is a Phase-C-sized campaign. Phase C took many sessions and
several rate-limit interruptions. The owner must say which of these to do, in what order:
- **W1**: re-review the stale nodes. The 7 content-changed nodes are the highest value, because their
  verdicts genuinely may change.
- **W2**: the 173 CONTRADICTED.

If neither gate is answered, do only **W0** and then ask.

---

## 3. Workstreams

### W0: baseline and lock (always)

1. Heavy-run check (see §4). Confirm the tree is CERTIFIED and the worktree is clean.
2. Claim H-06: edit **only** its `owner` line with `sed`, then check that
   `git diff --numstat validation_reports/phase2_hardening/hardening_status.json` reads `1 1`. Commit
   that change.
3. Open an intent with `tests/tree_state.py --begin <kind> --session <id> --note "..."`, where `<kind>` is:
   - `campaign` for review dispatch; this touches no source, so no re-proof is owed;
   - `batch` for source edits;
   - `chain` for the re-proof chain.
4. Re-measure §5 and §6F yourself, and write the numbers down before you change anything.

### W1: re-review STALE nodes (blind; no source touched)

Order: the 7 content-changed nodes first, then the other 136.

**Build each dispatch at dispatch time:**

```sh
PYTHONPATH=. .venv/bin/python tests/judgment_batches.py --node <node> \
  --prompt <dir>/prompt.txt --reviewed-by <identity> \
  --verdicts-path <dir>/verdicts.json --skeleton-dir <dir>/skeletons
```

Keep one directory per node under `local_only/scratch/<your-phase>/<node>/`. The reviewer reads only
`prompt.txt` and writes only `verdicts.json`.

**The four-part dispatch addendum.** A reply missing any part is refused or unusable
(`CLAUDE_AGENT_PROMPT.md` §5 has the evidence):
1. Every reasoning and rationale is at least 60 characters.
2. No quotation marks unless the quoted text is a verbatim substring of the packet. When in doubt,
   use no quotes at all.
3. Neutral interest-theme context: the 26 themes are a deliberate product feature. Judge whether
   theming **interferes** with the maths. The ✝️/`bible` theme is the owner's call, not the reviewer's.
4. Compare every hint against its item. Every clause cites real sample ids; for an absence, cite the
   ids examined. `overall` follows from the reviewer's own verdicts: FAIL if any verdict is FAIL, else
   CONCERN if any is CONCERN, else PASS.

**Audit before filing, using the validator's own functions** (`validate_judgment._validate_one`,
`_validate_quote_provenance`) and the real filer. Do not re-implement their regexes; a re-implemented
audit once under-reported. Check: 60-character floor, no duplicated per-sample reasoning, valid
citations, quote provenance, and a derived `overall`.

**File with `tests/file_reviews.py`, giving each node its own dispatch id**, for example
`--dispatch-id s5-<phase>-w<W>-<model>-<date>-<node>`.
- A wave-level id shared by several nodes overwrote 76 records' raw responses in Phase B/C.
- The filer now **refuses** that overwrite. If you see "already holds a DIFFERENT dispatch's bytes",
  the fix is a unique id. Never delete the old copy.
- Filing replaces the node's review file in place; the old record survives only in git.

**Reviewer-integrity rules, each paid for in Phase C:**
- **Never edit a verdict, sample id, clause or `overall` yourself.** You may ask a reviewer to fix
  syntax, structure or wording. Afterwards, prove by structural diff against the first reply
  (`verdicts.v1.json`) that no verdict changed.
- **When a reply's `overall` contradicts its own verdicts, do NOT ask that reviewer to reconcile.**
  4 of 5 reconciliation requests softened verdicts instead of fixing `overall`. Instead:
  1. harvest the reply's non-PASS claims;
  2. move the reply to `set_aside/`;
  3. dispatch the node to a **fresh** reviewer who sees none of the prior exchange.
- The same set-aside-and-redispatch rule applies to unparseable JSON after one repair, and to skipped
  samples.
- For `--tool-uses-by-reviewer`, take tool use from the harness usage record when one exists, otherwise
  from the transcript. Never take it from the reviewer's self-report. Record any path outside the node's
  own directory.
- A reviewer's claimed content defect is a **claim** until you confirm it by rendering that seed:
  `judgment_packets._render_sample(node, seed)`. Record confirmed defects for a later source batch. Do
  not fix them mid-campaign: a source change stales reviews again.

**Commit filed reviews by name** at regular checkpoints. Include each node's review JSON and its
`.responses/` pair. After filing, run `tests/legacy_review_queue.py --write` and check which direction
its count moves.

### W2: the 173 CONTRADICTED `capability_phase2` findings

There are 173 across 82 nodes and 144 capabilities, a long tail. They came from a campaign that changed
two variables at once (ruling 9's prevalence standard and the rater family), so **no single row is
settled.** For each finding:
1. **Confirm it** with one more independent blind Attester dispatch. Tooling: `tests/attester_packets.py`
   (one packet file per node) and `tests/attester_file.py`. The same model gate applies.
2. **Then decide by Content Rule 4, and quote the MATATAG clause.**
   - If the competency names the thing, build the artifact that produces it (a formatter, variant, DNA
     or visual). That is the fix.
   - If it does not, the capability provider entry is invention and must be removed.
   - Never delete a provider entry just to make a finding go away.

Two confirmed starting points:
- **`mat_g1_na_q1_7`, the `concrete` clause.** The competency reads *"… using a variety of concrete and
  pictorial models"*, but no concrete model is served. Similar `concrete*` findings recur in Grade 1, so
  one artifact may clear several.
- **`mat_g2_mg_q1_2`.** The competency reads *"Describe **and draw** the effect of … slide"*, but all 18
  samples are MCQ with no drawing. Ruling 3: an MCQ *about* drawing does not satisfy "draw".

The 15 STALE attestations need a fresh Attester judgment, not engineering. W2's source work is a
`batch`: it stales reviews and attestations and owes the full re-proof chain (§5 below).

---

## 4. Rules you may not break

- **Verification is execution.** Quote every command and its verbatim output. If you did not run
  something, write "not measured".
- **Never weaken a check.** A floor or pinned count moves only for a documented ground-truth error:
  - by exactly the measured delta;
  - with the node id and the clause quoted in the code comment, the contract row, the commit and the
    evidence log;
  - after a full diff proving nothing else moved.

  Phase D's `ac614688` is the model to follow.
- **Invocation:** `PYTHONPATH=. .venv/bin/python …` only. There is no usable bare `python` and no
  `timeout` on this host. Never pipe a long run through `tail`. Write to a log and capture the exit code:
  `cmd > log 2>&1; echo "EXIT $?"`.
- **Stage by name. Never `git add -A`.** The pre-commit hook re-stages `graphify-out/` itself; that is
  expected.
- **Before any heavy run** (mutation corpus, release shards, `run_all`, the full pytest suite), check:
  - `ps -eo pid,etime,command | grep -iE "mutation_harness|obligation_executor|validate_|pytest"` must
    return nothing;
  - `df -h /System/Volumes/Data` must show enough space.

  The mutation harness plants real bugs in real source. Run it **alone**, never "tidy" `git status`
  while it runs, and afterwards check for escaped plants:
  `git grep -n -E "#\s*planted mutation|//\s*planted " HEAD -- backend/ frontend/src | grep -v mutation_harness`
  must be empty.
- **Mutation anchors.** Any edit to a file a mutation anchors on can move that anchor. Check them all
  before the corpus with the anchor one-liner in `CLAUDE_AGENT_PROMPT.md` §8.
- **Commits end with a Co-Authored-By line naming YOUR model truthfully.** Release the lock in a
  **follow-up** commit; `--amend` moves the hash.
- **Do not delete worktrees or files you did not create.** In particular, do not touch
  `.claude/worktrees/agent-aaac714fac3fe0cc6`.
- **Not yours:**
  - the ✝️/`bible` theme;
  - `requires` / `requires_ignore`;
  - opening H-11;
  - the supersession fix and `CSI-R1`–`CSI-R3`;
  - release promotion (H-09);
  - renaming any reviewer identity;
  - discarding filed reviews or the `batch117`–`batch150` corpus.

  Name what you find in these areas; do not fix it.
- **Stop at every owner gate.** The previous GPT session was told to ask before Phase D and started it
  anyway. The work turned out useful, but it staled 143 reviews without an owner decision. A gate is not
  a suggestion.

---

## 5. The re-proof chain (owed after ANY source commit; about 5 hours; run each step alone)

```sh
PYTHONPATH=. .venv/bin/python -m pytest tests/unit -m "not slow" -q -p no:cacheprovider   # before committing source (~18 min)
# commit source by name, then:
PYTHONPATH=. .venv/bin/python tests/tree_state.py --begin chain --force --session "<id>" --note "..."
PYTHONPATH=. .venv/bin/python -m scripts.regen_formatter_exclusions        # never hand-edit its output
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000
DATABASE_URL= PYTHONPATH=. .venv/bin/python tests/frontend_suite.py
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py > corpus.log 2>&1; echo "EXIT $?"
for i in 0 1 2 3 4 5; do PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier release --shard-count 6 --shard-index $i; done
PYTHONPATH=. .venv/bin/python -m tests.obligation_executor --tier verify-release
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all > run_all.log 2>&1; echo "EXIT $?"
```

Launch the chain detached (`nohup … &!`) with one log per step, so a session end cannot kill it.

- **Any source or harness edit made mid-chain stales every artifact produced so far.** Stop the chain,
  commit the edit, and restart from the benchmark. This cost Phase D one restart.
- **Expect exactly 3 INVALID** (the §6F cluster). Any other INVALID means an unmutated baseline is red.
  Run that mutation's own command to see which floor or check broke. Do not re-run the corpus hoping it
  changes.
- The obligation benchmark prints `recommended_shards=4`, but `validate_obligations` hard-codes 6.
  Follow the validator.
- Afterwards, commit the artifacts by name:
  - `validation_reports/mutation_proofs`
  - `.../obligation_release_shards`
  - `obligation_benchmark.json`
  - `obligation_budget.json`
  - `frontend_static_render.json`
  - `tree_state.json`

  Then run `tree_state.py --complete`, confirm the tree reads CERTIFIED, and release the lock in a
  follow-up commit.

---

## 6. Traps learned in Phases C and D

1. **A frontend evidence check must read the field the component reads.** Two corpora reach the React
   renderers with different wrapper shapes: frontend_suite, and the capability-freshness packet render.
   Reading the top-level `interaction_mode` broke 3 capability tests. Use `visual_params`.
2. **A content fix can shrink the obligation product and the census legitimately.** Prove it by diffing
   the full obligation set and variant set against the parent commit. Every other node must be
   byte-identical. Only after that may you move the pinned counts and floors, as in §4.
3. **A symptom fix can leave a silent fallback behind.** In Phase D, the DNA clamp hid `fmt_bar_chart`'s
   cross-grade category top-up. Replace the fallback with a named failure that carries the seed, and
   prove it fails by removing the clamp.
4. **A reviewer's summary of its own file is unreliable.** Re-run the full audit after every revision.
5. **`auto.py`-style scratch helpers keep a `verdicts.v1.json` baseline.** A stale or invalid v1 left
   by a crashed run makes the wording-only diff crash or lie. Check v1 before trusting the diff.
6. **Re-count every number you publish.** Three sessions have shipped a wrong count.

---

## 7. Bookkeeping before you stop (including an interrupted stop)

- Write an evidence entry in `validation_reports/HARDENING_EVIDENCE.md`. Include:
  - commands with verbatim output;
  - seeds;
  - dispatch ids and reviewer identities;
  - **the model and reasoning level that judged**;
  - any set-aside replies, and the harvested claims from them;
  - named limits.
- Append to H-06's `progress` surgically (`numstat 1 1`).
- Rewrite §1 of this file, and the state section of `CLAUDE_AGENT_PROMPT.md`, rather than adding a
  banner.
- Commit by name, close your intent, confirm the tree state, and release the lock in a follow-up
  commit.
- **If you are interrupted**, leave an accurate open intent and a committed checkpoint. An honest
  INTERRUPTED state beats a fabricated clean one.

**A good session:**
- resolves both owner gates;
- files blind reviews that survive the validator unchanged, starting with the 7 content-changed nodes,
  or lands W2 artifacts that a fresh Attester confirms, each tied to a quoted clause;
- measures §5 and §6F before and after;
- quotes every number from a command run in that session.
