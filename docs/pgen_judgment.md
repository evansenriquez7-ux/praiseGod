# PG Pipeline Judgment Guide

**Species: judgment guide** (see [`DOC_RULES.md`](./DOC_RULES.md) R3). These are the curriculum-fidelity
questions a machine cannot score. Nothing here is checked by reading it — the *artifact* is checked.
`run_all` is run locally and by the hardening loop; since 2026-08-12 no CI workflow runs it, so nothing
here blocks a deploy.

**Retired as a gate on 2026-10-17 (batch H6, owner rulings 25 and 55).** The per-sample review below is no
longer filed or required. The 151 records under `validation_reports/judgment/` are frozen history: `run_all`'s
`carried_defects_5_6` stage (`validate_carried`) fails integrity if any of them is edited, added or deleted, and
reports every non-PASS verdict on a record that still replays as a content finding (exit 2), named by lc +
seed (or ruling 52's substitute for an lc-wide verdict) + owed build. When a generator change stops a record
replaying, its defects clear and the lc owes a §17 re-judgment. The live LLM gate is the §17 stem review
(`validate_stem_review`, rulings 24 and 44): judges rule on an lc's stem templates and field domains, and §14
proves every rendered field stays inside those domains. `validate_judgment` and its mutations stay in the tree;
its rules below describe what the frozen records were held to.

Checking a box in this document proves nothing. Every registered node had a review file at
`validation_reports/judgment/<group_dir>/<node_id>.json` that passed `validate_judgment`'s record checks.

## What the enforcer accepts

`validate_judgment` rejects, by name and node: a missing or unparseable file, a wrong `node_id`, a
placeholder `reviewed_by`, `blind` not `true`, fewer than 3 distinct `sample_seeds`, fewer than 3
`samples_reviewed` entries, a sample without an integer `seed` or non-empty `question_text`, any of the
six findings missing, any `verdict` outside `PASS`/`CONCERN`/`FAIL`, any `rationale` under 40 characters,
any `rationale` reused verbatim across two nodes, and any cited seed whose live re-render no longer
matches the `question_text` recorded (a **stale** review).

### Anti-template checks

The list above was satisfied in full by 151 fabricated all-PASS reviews written from one template with
the node ID and seed list substituted in. The freshness check did not catch them because it re-renders
`samples_reviewed` and never reads the rationale — so a template rationale stapled onto a freshly
rendered samples block passed cleanly, and 115 of the 151 quoted question stems that appear nowhere in
their own samples. (**CORRECTED 2026-09-24:** that 115 was counted with a provenance corpus that omitted
hints, cloze text, visual payload/render and requirement clauses, all of which the blind packet prints, so
it is an **upper bound** on fabrication rather than a verified count; the same narrow corpus produced 4
false findings against a genuine review on `mat_g3_na_q4_7`. The fabrication conclusion rests on the
reviews being template all-PASS stubs, which is separately evidenced; only the count is unreliable.) Three further checks are therefore binding (enforced in `validate_judgment.py`,
tested in `tests/unit/test_judgment_antitemplate.py`):

| Check | Rule | Rejected because |
|---|---|---|
| **Quote provenance** | every quoted span of ≥ 4 chars in a rationale must appear in that review's own `samples_reviewed` (stem, answer, option value, formatter) or in the node's MATATAG competency text | a stem quoted but never shown is fabricated evidence, which is worse than a wrong verdict |

**Dispatchers: the failure mode this catches is not dishonesty, it is notation.** Measured across
the 2026-09-11 re-review of all 151 nodes, every quote-provenance failure was a reviewer putting an
expression it was *reasoning about* into quotation marks — `length x width`, `side x side`,
`4 x side`, `variety of models` — none of which was on the page it was given. It recurred on the
same node through three separate blind reviewers. Telling a reviewer to "quote only what appears in
the samples" is not enough, because a formula does not feel like a quotation. Say instead:
*quotation marks mean you are copying characters off the page in front of you; write any formula,
rule name or paraphrase with no quotation marks at all.* With that wording it passed first time.
| **Skeleton clustering** | with node IDs, quoted spans, and digits stripped, no rationale frame may recur across more than **3** nodes for the same finding | a frame spanning many nodes is a fill-in-the-blank form, not independent judgment |
| **Reviewer plurality** | no single `reviewed_by` identity may cover more than **25** nodes — one blind batch | one identity across the tree is one pass, not per-node judgment |

These are cross-file properties: a template is only visible against its siblings, and a single reviewer
identity is only visible across the whole tree. Reviews are dispatched in blind batches of ≤ 25 nodes,
each batch naming its own reviewer, which is what makes the 25-node quota satisfiable.

```json
{
  "node_id": "mat_g1_na_q1_0",
  "reviewed_by": "<naming the reviewing model/agent or person>",
  "review_date": "YYYY-MM-DD",
  "blind": true,
  "sample_seeds": [42, 43, 44, 45, 46],
  "samples_reviewed": [{"seed": 42, "question_text": "...", "correct_answer": "..."}],
  "findings": {
    "competency_fulfillment":    {"verdict": "PASS|CONCERN|FAIL", "rationale": "node-specific, >= 40 chars"},
    "comprehensive_coverage":    {"verdict": "...", "rationale": "..."},
    "cognitive_capacity":        {"verdict": "...", "rationale": "..."},
    "variant_comprehensiveness": {"verdict": "...", "rationale": "..."},
    "competency_alignment":      {"verdict": "...", "rationale": "..."},
    "scale_appropriateness":     {"verdict": "...", "rationale": "..."}
  },
  "overall": "PASS|CONCERN|FAIL"
}
```

## Who reviews, and how

The reviewer is **not the author** of the generator. It is handed a packet — the competency text plus
rendered samples from fixed seeds — and never the DNA/formatter source, so the verdict is a judgment
about content rather than the author grading their own homework.

```
python -m backend.app.practice_gen.validation.judgment_packets --node <NODE_ID>
```

A review's samples are evidence, not decoration: the enforcer re-renders every cited seed. Since H6 a record
that no longer replays is not redone; its carried defects clear and the lc owes a §17 re-judgment instead.

## The six items

| Item (`findings` key) | The question the reviewer answers |
|---|---|
| `competency_fulfillment` | Do the sampled problems address the exact verbs and nouns of the node's MATATAG competency? |
| `comprehensive_coverage` | Is every sub-case the competency's wording names actually generated, not just the easiest one? |
| `cognitive_capacity` | Do sentence structure, vocabulary, and required reasoning steps fit this grade and quarter? |
| `variant_comprehensiveness` | Are the logical contextual variations (word problem, pure math, alternate orientations) present? |
| `competency_alignment` | Does the difficulty progression build *this* competency, rather than varying an unrelated axis? |
| `scale_appropriateness` | Does the numeric range match the competency's stated ceiling, on a linear/log scale suited to its span? |

## Enforcement
Since H6 (2026-10-17), a `FAIL` or `CONCERN` verdict on a frozen record that still replays is a carried
content finding (`carried_judgment_defect_5`, exit 2): a generator work item, named by lc, seed and owed build.
It leaves the queue when the generator change that fixes it stops the record replaying and the lc's §17 stem
review is re-judged (`carried_defect_rejudge_owed` until a §17 record filed after the retirement stands).
NAMED LIMIT: §17 judges stems, not samples, so a sample-level defect class §17 does not judge (ambiguity,
for one; ruling 56) is not re-checked once its sample changes.
