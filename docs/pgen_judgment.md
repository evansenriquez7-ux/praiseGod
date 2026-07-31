# PG Pipeline Judgment Guide

**Species: judgment guide** (see [`DOC_RULES.md`](./DOC_RULES.md) R3). These are the curriculum-fidelity
questions a machine cannot score. Nothing here is checked by reading it — the *artifact* is checked, by
`validate_judgment` (step 6/6 of `run_all`; CI, blocks deploy).

Checking a box in this document proves nothing. Every registered node must have a review file at
`validation_reports/judgment/<group_dir>/<node_id>.json` that passes `validate_judgment`.

## What the enforcer accepts

`validate_judgment` rejects, by name and node: a missing or unparseable file, a wrong `node_id`, a
placeholder `reviewed_by`, `blind` not `true`, fewer than 3 distinct `sample_seeds`, fewer than 3
`samples_reviewed` entries, a sample without an integer `seed` or non-empty `question_text`, any of the
six findings missing, any `verdict` outside `PASS`/`CONCERN`/`FAIL`, any `rationale` under 40 characters,
any `rationale` reused verbatim across two nodes, and any cited seed whose live re-render no longer
matches the `question_text` recorded (a **stale** review).

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

## What this gate does not do

It cannot decide whether a verdict is *right*. A `FAIL` verdict is a passing artifact and a failing node:
`run_all` prints the PASS/CONCERN/FAIL tally so curriculum-fidelity debt stays visible instead of hiding
under a green check. Triage of that debt is tracked in [`IMPLEMENTATION_STATUS.md`](./IMPLEMENTATION_STATUS.md).
