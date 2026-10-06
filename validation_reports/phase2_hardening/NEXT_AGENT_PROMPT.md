# Task prompt: continue Phase 2 hardening (fresh GPT-hosted session)

**Rewritten 2026-10-06 after the first W2 source batch and its full re-proof. This REPLACES every
earlier version of this file.** `GPT_HANDOFF_PROMPT.md` beside it is finished history; do not execute it.
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

**Updated 2026-10-07 after the stale-evidence refresh. The source digest remains
`878f0affe08d27d4`; no source changed and no re-proof was owed. Re-measure before quoting.**

```
HEAD                  7294cf69 plus the bookkeeping/intent closeout commits
tree_state            CERTIFIED after closeout at digest 878f0affe08d27d4
run_all               not re-measured in the evidence-refresh campaign; last EXIT 1, failed=3
judgment_reviews_5    module 751 findings; 0 of 151 reviews STALE
capability_phase2     124 CONTRADICTED; 0 STALE attestations
assertion_coverage_8  3: the §6F mutation cluster; clears only when capability_phase2 reaches 0
all other Phase 1     PASS, including count_noun_1J (0 findings / 9,060 samples)
mutation corpus       198/201 DETECTED; only the 3 expected §6F controls INVALID
obligations           420 pairs, 3,849 base, 16,701 continuous, 415,692 finite,
                      2,078,460 executions; 6 release shards clean
review verdicts       151/151 schema-v2: 78 PASS / 49 CONCERN / 24 FAIL
H-06                  status open; lock released after the closeout commit
```

Commands that re-measure this state:

```sh
PYTHONPATH=. .venv/bin/python tests/tree_state.py
PYTHONPATH=. .venv/bin/python tests/hardening_status.py
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.validate_judgment --all > /tmp/vj.log 2>&1; echo "EXIT $?"
```

**The stale-evidence refresh is complete.** All 14 stale reviews were freshly re-reviewed by independent
GPT-5.6 Luna medium reviewers and all ten stale attestation records were superseded by fresh blind
attestations. Historical records were preserved. `batch369_mat_g1_na_q3_6` additionally supersedes two
retired example-capability verdicts that the freshness validator correctly continued to treat as live
until a later record won those exact `(node, capability)` keys.

**The first W2 source batch is complete and fully re-proved.** `mat_g1_mg_q1_0` now serves the
curriculum-required triangle, rectangle, and square at different sizes and orientations. The batch also
fixed the `1 ones` regression exposed by `run_all`; commit `383879af` clears all 12 §1J findings.

**Resume in this order:**

1. Continue the 124 CONTRADICTED findings by Content Rule 4, in small source batches.
   Every source batch must quote the MATATAG clause and pay the full chain in §5.
2. Re-review and re-attest every digest-bound record made stale by each source batch; never carry a
   verdict forward.

The complete commands, exact outputs, dispatch identities, set-asides, and named limits are in the
2026-10-06/07 evidence-refresh entry of `validation_reports/HARDENING_EVIDENCE.md`.

---

## 2. OWNER GATES: resolve these before any dispatch

**Gate A: reviewer model.** Phase E used GPT-5.6 Luna, medium, on the GPT host, then Claude Haiku 4.5 on
the Claude host. Both were owner rulings of 2026-09-30.
- If your host cannot dispatch the model the owner last named for it, stop and ask.
- The identity always names the model that actually judged.
- Never rename any existing record.

**Gate B: scope is resolved.** The owner directed the agents to continue until the prompt is effectively
complete. Follow §1's order: refresh the 14 stale reviews and 10 stale attestations, then continue the
127 CONTRADICTED W2 findings. Stop only at a new content judgment that MATATAG and the recorded owner
rulings do not settle.

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

### W1: re-review STALE nodes (blind; no source touched) -- DONE 2026-10-01; reuse this method after any source batch

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
