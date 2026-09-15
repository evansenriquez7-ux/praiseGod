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

Usage:
    python -m tests.judgment_batches --plan                       # the batch plan
    python -m tests.judgment_batches --batch 3 \
        --blind local_only/scratch/review/b3.txt \
        --skeleton-dir local_only/scratch/review/b3/
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
