# PG Pipeline Judgment Guide

**Species: judgment guide** (see [`DOC_RULES.md`](./DOC_RULES.md) R3). These are the curriculum-fidelity
questions a machine cannot score. Nothing here is checked by reading it — the *artifact* is checked, by
`validate_judgment` (step 6/6 of `run_all`). `run_all` is run locally and by the hardening loop; since
2026-08-12 no CI workflow runs it, so nothing here blocks a deploy.

Checking a box in this document proves nothing. Every registered node must have a review file at
`validation_reports/judgment/<group_dir>/<node_id>.json` that passes `validate_judgment`.

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
their own samples. Three further checks are therefore binding (enforced in `validate_judgment.py`,
tested in `tests/unit/test_judgment_antitemplate.py`):

| Check | Rule | Rejected because |
|---|---|---|
| **Quote provenance** | every quoted span of ≥ 4 chars in a rationale must appear in that review's own `samples_reviewed` (stem, answer, option value, formatter) or in the node's MATATAG competency text | a stem quoted but never shown is fabricated evidence, which is worse than a wrong verdict |
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

A review's samples are evidence, not decoration: because the enforcer re-renders every cited seed, a
review filed against content the generator no longer produces fails the run and has to be redone. Changing
a generator therefore obliges a fresh review of the nodes it touches, in the same change.

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
A `FAIL` or `CONCERN` verdict causes `validate_judgment` (and `run_all.py`) to exit with a non-zero error. All nodes must be remediated in generator DNA/formatters and re-reviewed blind to achieve genuine `PASS` verdicts across all 6 findings and overall verdict.
