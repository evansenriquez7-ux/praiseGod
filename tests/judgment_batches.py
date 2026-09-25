"""
Judgment batches — the blind evidence a §5 review has to be built from.

Why this exists
---------------
`tests/attester_packets.py` has done this for §6 since 2026-08-19: it writes the blind
half (what the Attester sees) and the key half (what it must not), and
`render_prompt_block` emits the Attester-facing text VERBATIM so the dispatcher cannot
introduce a defect by retyping. That lesson was paid for once already -- a stem shortened
by hand reached an Attester as a different problem, and the Attester's correct verdict
about the page it was given was filed as a pipeline defect.

§5 had no equivalent. `judgment_packets.py` builds a packet and dumps JSON; every blind
review dispatched from it was assembled by hand, which is the same retyping step, on the
larger of the two surfaces (151 reviews x 6 rationales). This module closes that.

It also enforces the two structural properties `validate_judgment` checks across files
and a single dispatch cannot see:

  * batches of at most `_MAX_NODES_PER_REVIEWER` nodes, read from the validator rather
    than restated, because one identity spanning more than one dispatch is a
    fabrication signal (§5 reviewer plurality);
  * a `--skeleton` review file pre-filled with the EXACT samples the reviewer is shown,
    so a filed review always carries re-renderable evidence and always carries the
    options of a choice item -- the omission that left 505 of 2026 recorded samples
    unadjudicable before 2026-09-10.

Named limitation: batch sizing enforces only the validator's 25-node reviewer-plurality cap.
It does not budget response volume after schema v2 added four reasoned checks per sample. A
25-node batch can require thousands of independently authored reasoning blocks and exceed one
reviewer turn's output capacity. Script-generated filler is not a remedy: §5's verbatim and
rationale-skeleton checks reject it. Dispatchers must keep the assigned identity truthful and
must not file a partial or templated response while this operational limit remains open.

Usage:
    python -m tests.judgment_batches --plan                       # the batch plan
    python -m tests.judgment_batches --batch 3 \
        --blind local_only/scratch/review/b3.txt \
        --skeleton-dir local_only/scratch/review/b3/ \
        --prompt local_only/scratch/review/b3_prompt.txt \
        --reviewed-by blind-attester-gpt-5.6-terra-light-b3-20260923 \
        --verdicts-path local_only/scratch/review/b3_verdicts.json
    python -m tests.judgment_batches --node mat_g1_na_q1_0 --blind -
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from backend.app.practice_gen.registry import get_all_node_ids
from backend.app.practice_gen.validation.judgment_packets import build_packet, render_failures
from backend.app.practice_gen.validation.validate_judgment import (
    REQUIRED_FINDINGS,
    SAMPLE_ASSESSMENTS,
    _MAX_NODES_PER_REVIEWER,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def batches() -> List[List[str]]:
    """
    The tree split into blind dispatches of at most one batch each.

    Sorted and fixed-size, so batch N is the same set of nodes on every run and a
    reviewer identity can be tied to a batch rather than to whatever happened to be
    handed out that day. The cap is READ from the validator: tightening
    `_MAX_NODES_PER_REVIEWER` must re-plan the dispatch, never silently produce batches
    the gate will reject.
    """
    nodes = sorted(get_all_node_ids())
    return [nodes[i:i + _MAX_NODES_PER_REVIEWER]
            for i in range(0, len(nodes), _MAX_NODES_PER_REVIEWER)]


def render_prompt_block(packets: List[Dict[str, Any]]) -> str:
    """
    Emit the reviewer-facing text VERBATIM from the packets.

    Whatever this returns is what the reviewer sees. It is copied out of the packet, not
    summarised: a stem paraphrased on the way to a reviewer produces a genuine judgment
    about a problem the pipeline does not serve, and §5 will then re-render the seed and
    report the review stale for a reason that is nobody's fault but the dispatcher's.

    Options are printed for every sample that has them, with the correct one NOT marked.
    A reviewer judges distractor quality from the options, and `_validate_freshness`
    re-renders and compares them, so a review must be built from the same list.
    """
    out: List[str] = []
    for p in packets:
        competency = p["competency_snapshot"]
        out.append("=" * 74)
        out.append(f"NODE: {p['node_id']}")
        out.append(f"PACKET DIGEST: {p['packet_digest']}")
        out.append(f"COMPETENCY (Grade {competency['grade']}, "
                   f"Quarter {competency['quarter']}, {competency.get('subdomain')}):")
        out.append(competency["text"])
        out.append("")
        out.append("REQUIREMENTS (confirm this is a lossless decomposition of the competency):")
        for requirement in p["requirements_snapshot"]:
            out.append(f"  {requirement['id']}: {requirement['clause']}")
        out.append("")
        out.append("SAMPLES (every one of these is real rendered output):")
        for s in p["samples"]:
            out.append(f"  sample {s['sample_id']}  seed {s['seed']}  [{s.get('formatter')}]")
            out.append(f"      stem:    {s['question_text']}")
            out.append(f"      answer:  {s.get('resolved_answer')}")
            opts = s.get("options")
            if opts:
                vals = [str(o.get("value")) if isinstance(o, dict) else str(o) for o in opts]
                out.append(f"      options: {' / '.join(vals)}")
            if "cloze_text" in s:
                out.append(f"      cloze:   {s['cloze_text']}")
            if "hints" in s:
                out.append(f"      hints:   {json.dumps(s['hints'], ensure_ascii=False)}")
            elif "hint" in s:
                out.append(f"      hint:    {s['hint']}")
            out.append(f"      response: {json.dumps(s['effective'], ensure_ascii=False)}")
            if s.get("visual_type"):
                out.append(f"      visual:  {s['visual_type']}")
                out.append("      rendered structure: " + json.dumps(
                    s["visual_render"]["description"], ensure_ascii=False
                ))
                out.append(
                    "      layout limit: this static description does not prove crowding, "
                    "overlap, colour contrast, or physical touch-target size"
                )
        failures = render_failures(p["node_id"])
        if failures:
            # Never silent (Ground Rule 3): a seed the packet builder could not render is
            # part of what the reviewer is judging -- it is a sub-case the node does not
            # serve, which is exactly what `comprehensive_coverage` asks about.
            out.append("")
            out.append("  SEEDS THIS NODE COULD NOT RENDER (judge this as coverage, "
                       "not as a tooling problem):")
            for seed, err in failures:
                out.append(f"      seed {seed}: {err}")
        out.append("")
    return "\n".join(out)


def render_review_prompt(packets: List[Dict[str, Any]], reviewer_identity: str,
                         verdicts_path: str) -> str:
    """Build the complete blind prompt without retyping any packet evidence.

    The reviewer authors only judgments.  Identity, dispatch attribution, raw-response
    provenance, and the canonical samples are joined mechanically by ``file_reviews``.
    """
    finding_keys = ", ".join(sorted(REQUIRED_FINDINGS))
    assessment_keys = ", ".join(sorted(SAMPLE_ASSESSMENTS))
    return f"""You are an independent curriculum reviewer for Philippine MATATAG K-12 mathematics.

You are reviewing rendered output from a practice-problem generator. You have not seen the
generator source. Do not inspect repository source, existing reviews, answer keys beyond the
rendered packet, or any prior verdict. Read only this prompt and write only the JSON response.

ASSIGNED REVIEWER IDENTITY (copy exactly into the top-level `reviewer` field):
  {reviewer_identity}

Write one JSON object to:
  {verdicts_path}

For every node, author all of the following:

1. `findings`: exactly these six keys: {finding_keys}. Each value has `verdict`
   (PASS, CONCERN, or FAIL) and a node-specific `rationale` of at least 40 characters.
   `competency_fulfillment` must additionally contain `decomposition` with a verdict and
   reasoning explaining whether the printed REQUIREMENTS losslessly cover the full competency.
2. `sample_assessments`: one entry for every printed sample, in printed order. Copy its opaque
   `sample_id`; under `checks`, judge exactly: {assessment_keys}. Each check has `verdict`
   and sample-specific `reasoning` of at least 40 characters.
3. `clause_evidence`: one entry for every printed REQUIREMENT, in printed order, with
   `requirement_id`, the clause text copied exactly, `verdict`, reasoning of at least 40
   characters, and one or more cited `sample_ids` from this node. A missing capability may be
   FAIL or CONCERN: cite the sample_ids you EXAMINED and found lacking it (the list may never
   be empty), and never cite a sample as SUPPORTING a clause it does not support.
4. `overall`: FAIL if any node finding, sample check, clause verdict, or decomposition is FAIL;
   otherwise CONCERN if any is CONCERN; otherwise PASS.

Do not add reviewer identities or dispatch IDs inside sample/clause entries; the filing tool
adds dispatcher-controlled attribution. Do not include or retype the samples themselves.
If you quote text in reasoning, quote only text literally printed for that node. Avoid repeated
sentence frames across nodes: normalized rationale skeletons shared by more than three nodes are
rejected as templating.

Response shape:
{{
  "reviewer": "{reviewer_identity}",
  "<node_id>": {{
    "findings": {{
      "competency_fulfillment": {{
        "verdict": "PASS|CONCERN|FAIL", "rationale": "...",
        "decomposition": {{"verdict": "PASS|CONCERN|FAIL", "reasoning": "..."}}
      }},
      "<each other required finding>": {{"verdict": "...", "rationale": "..."}}
    }},
    "sample_assessments": [
      {{"sample_id": "<opaque id>", "checks": {{
        "<each required sample check>": {{"verdict": "...", "reasoning": "..."}}
      }}}}
    ],
    "clause_evidence": [
      {{"requirement_id": "<printed id>", "clause": "<printed clause>",
        "verdict": "...", "reasoning": "...", "sample_ids": ["<opaque id>"]}}
    ],
    "overall": "PASS|CONCERN|FAIL"
  }}
}}

== BLIND PACKET ==

{render_prompt_block(packets)}
"""


def skeleton(packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    A review file pre-filled with the exact samples the reviewer was shown.

    The samples block is copied from the packet whole -- including `options`, which is
    what makes the filed review adjudicable by `_validate_freshness` on all three of the
    fields it compares. A reviewer fills in `reviewed_by`, the verdicts and the
    rationales; it never retypes a sample, because a retyped sample is a stale review
    waiting to happen.
    """
    return {
        "schema_version": packet["schema_version"],
        "node_id": packet["node_id"],
        "competency_snapshot": packet["competency_snapshot"],
        "requirements_snapshot": packet["requirements_snapshot"],
        "packet_digest": packet["packet_digest"],
        "sampling_version": packet["sampling_version"],
        "reviewed_by": "<name the reviewing model/agent>",
        "review_date": "<YYYY-MM-DD>",
        "blind": True,
        "sample_seeds": [sample["seed"] for sample in packet["samples"]],
        "sample_ids": packet["sample_ids"],
        "samples_reviewed": packet["samples"],
        "sample_assessments": [],
        "clause_evidence": [],
        "dispatch_provenance": [],
        "findings": {item: {"verdict": "<PASS|CONCERN|FAIL>",
                            "rationale": "<node-specific, >= 40 chars, quoting only "
                                         "what appears in these samples>"}
                     for item in sorted(REQUIRED_FINDINGS)},
        "overall": "<PASS|CONCERN|FAIL>",
    }


def _main() -> int:
    ap = argparse.ArgumentParser(description="Build blind §5 review dispatches.")
    ap.add_argument("--plan", action="store_true", help="print the batch plan and exit")
    ap.add_argument("--batch", type=int, help="1-indexed batch number from --plan")
    ap.add_argument("--node", action="append", default=[], help="explicit node id")
    ap.add_argument("--blind", help="write the reviewer-facing text here ('-' = stdout)")
    ap.add_argument("--prompt", help="write the complete reviewer prompt here")
    ap.add_argument("--reviewed-by", help="dispatcher-assigned reviewer identity for --prompt")
    ap.add_argument("--verdicts-path", help="response path printed in --prompt")
    ap.add_argument("--skeleton-dir", help="write one pre-filled review file per node here")
    args = ap.parse_args()

    plan = batches()
    if args.plan:
        for i, b in enumerate(plan, 1):
            print(f"batch {i:2d}: {len(b):2d} nodes  {b[0]} .. {b[-1]}")
        print(f"\n{len(plan)} batches of <= {_MAX_NODES_PER_REVIEWER} "
              f"(validate_judgment._MAX_NODES_PER_REVIEWER); each needs its OWN reviewer "
              f"identity, or §5 reports reviewer plurality.")
        return 0

    if args.batch:
        if not 1 <= args.batch <= len(plan):
            raise SystemExit(f"--batch must be 1..{len(plan)}; see --plan")
        nodes = plan[args.batch - 1]
    elif args.node:
        nodes = list(args.node)
    else:
        raise SystemExit("no nodes selected: pass --plan, --batch or --node")

    packets = [build_packet(n) for n in nodes]

    if args.blind:
        text = render_prompt_block(packets)
        if args.blind == "-":
            print(text)
        else:
            Path(args.blind).parent.mkdir(parents=True, exist_ok=True)
            Path(args.blind).write_text(text, encoding="utf-8")
            print(f"blind packet: {len(packets)} node(s), {len(text)} chars -> {args.blind}")

    if args.prompt:
        if not args.reviewed_by or not args.verdicts_path:
            raise SystemExit("--prompt requires --reviewed-by and --verdicts-path")
        text = render_review_prompt(packets, args.reviewed_by, args.verdicts_path)
        Path(args.prompt).parent.mkdir(parents=True, exist_ok=True)
        Path(args.prompt).write_text(text, encoding="utf-8")
        print(f"review prompt: {len(packets)} node(s), {len(text)} chars -> {args.prompt}")

    if args.skeleton_dir:
        d = Path(args.skeleton_dir)
        d.mkdir(parents=True, exist_ok=True)
        for p in packets:
            (d / f"{p['node_id']}.json").write_text(
                json.dumps(skeleton(p), indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"skeletons: {len(packets)} file(s) -> {d}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
