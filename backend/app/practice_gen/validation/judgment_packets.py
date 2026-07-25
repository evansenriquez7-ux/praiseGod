"""
Practice Generation — Blind Judgment Review Packets

Builds the data a *blind* reviewer-agent needs to judge a node's generated
problems against its MATATAG competency — and nothing else. The reviewer is
handed only the competency text plus a set of rendered sample problems from
fixed seeds; it never sees the generator/DNA/formatter code. That is what makes
the resulting review genuine rather than the author grading its own homework
(`doc_rem.md` §3.1: "the verifier is not the author").

A packet is pure rendered output (question text, correct answer, options), so
handing it to a reviewer discloses no implementation detail.

CLI:
    python -m backend.app.practice_gen.validation.judgment_packets --node mat_g1_na_q1_0
    python -m backend.app.practice_gen.validation.judgment_packets --group mat_g1_na_q1
    python -m backend.app.practice_gen.validation.judgment_packets --all
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

from backend.app.practice_gen.pipeline import run
from backend.app.practice_gen.registry import get_all_node_ids, get_node_info

# Fixed seeds so a review is reproducible and the harness can require >= 3 of them.
REVIEW_SEEDS: List[int] = [42, 43, 44, 45, 46]


def _render_sample(node_id: str, seed: int) -> Dict[str, Any]:
    """Generate one problem and reduce it to reviewer-facing rendered fields only."""
    p = run(node_id, seed=seed)
    fd = p.get("format_data") or {}
    options = fd.get("mcq_options") or fd.get("options")
    sample: Dict[str, Any] = {
        "seed": seed,
        "formatter": p.get("format") or p.get("formatter"),
        "question_text": p.get("question_text", ""),
        "correct_answer": p.get("correct_answer"),
    }
    if options is not None:
        sample["options"] = options
    if p.get("hint"):
        sample["hint"] = p.get("hint")
    if fd.get("cloze_text"):
        sample["cloze_text"] = fd.get("cloze_text")
    return sample


def build_packet(node_id: str) -> Dict[str, Any]:
    info = get_node_info(node_id)
    if info is None:
        raise ValueError(f"Unknown node '{node_id}' — cannot build a review packet.")
    samples = [_render_sample(node_id, s) for s in REVIEW_SEEDS]
    return {
        "node_id": node_id,
        "grade": info.get("grade"),
        "quarter": info.get("quarter"),
        "subdomain": info.get("subdomain") or info.get("domain"),
        "competency_text": info.get("competency", ""),
        "sample_seeds": REVIEW_SEEDS,
        "samples": samples,
    }


def build_group(group_prefix: str) -> List[Dict[str, Any]]:
    ids = [n for n in get_all_node_ids() if "_".join(n.split("_")[:-1]) == group_prefix]
    if not ids:
        raise ValueError(f"No nodes found for group '{group_prefix}'.")
    return [build_packet(n) for n in sorted(ids)]


def _main() -> int:
    ap = argparse.ArgumentParser(description="Build blind judgment-review packets.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--node", help="Single node id, e.g. mat_g1_na_q1_0")
    g.add_argument("--group", help="Group prefix, e.g. mat_g1_na_q1")
    g.add_argument("--nodes", help="Comma-separated explicit node ids")
    g.add_argument("--all", action="store_true", help="Every registered node")
    args = ap.parse_args()

    if args.node:
        out: Any = build_packet(args.node)
    elif args.group:
        out = build_group(args.group)
    elif args.nodes:
        out = [build_packet(n.strip()) for n in args.nodes.split(",") if n.strip()]
    else:
        out = [build_packet(n) for n in sorted(get_all_node_ids())]

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
