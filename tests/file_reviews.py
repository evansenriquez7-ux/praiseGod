"""
file_reviews.py — put a blind reviewer's verdicts on disk without letting the reviewer
write the evidence.

Why this exists as a script rather than a hand edit. A §5 review is two things stapled
together: the VERDICTS, which only a blind reviewer may author, and the SAMPLES those
verdicts are about, which are evidence and must come from the live pipeline. A reviewer
that supplies its own samples block can file a verdict about content the generator never
produced, which is the fabrication §5's freshness check exists to catch -- and a
dispatcher that retypes a stem produces the same corruption by accident.

So: `samples_reviewed` and `sample_seeds` are copied from the SKELETON WRITTEN AT
DISPATCH TIME (`judgment_batches --skeleton-dir`), and the reviewer's reply supplies only
`findings` and `overall`. Nothing in the reply can reach the evidence block.

Why the dispatch-time skeleton and not a fresh rebuild at filing time. The first version
of this module rebuilt the packet when filing, which sounds stricter and is in fact the
one mistake that cannot be detected afterwards. A generator fix landing between dispatch
and filing -- which is the normal case, because the whole point of a review batch is to
find defects and fix them -- would pair the reviewer's verdicts with samples the reviewer
never saw, and §5 freshness would PASS the result, because the samples really are fresh.
That is a fabricated review with a clean bill of health: exactly what §5 exists to stop,
manufactured by the tool meant to prevent it.

Filing the samples the reviewer actually saw makes drift VISIBLE instead: §5 re-renders
them, reports the node stale, and the honest remedy -- re-review that node against the
content it now serves -- is the one the harness names.

The reviewer identity is supplied by the DISPATCHER, not read from the reply. Measured
2026-09-10 across three independently dispatched blind agents given the same prompt:
all three converged on variations of one self-declared name, which would silently
weaken §5 reviewer plurality and §6H attester plurality alike. A reply whose identity
does not match the one assigned is refused.

Usage:
    PYTHONPATH=. .venv/bin/python -m tests.file_reviews \
        --batch 1 --verdicts local_only/scratch/review/b1_verdicts.json \
        --reviewed-by reviewer-b1-quartz-mallow-4412 --date 2026-09-10 \
        --skeleton-dir local_only/scratch/review/b1/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.practice_gen.validation.validate_judgment import (  # noqa: E402
    JUDGMENT_DIR,
    REQUIRED_FINDINGS,
)
from tests.judgment_batches import batches  # noqa: E402

_VERDICTS = {"PASS", "CONCERN", "FAIL"}


def _target_path(node_id: str) -> Path:
    """Where this node's review lives, matching the existing on-disk layout."""
    existing = list(JUDGMENT_DIR.rglob(f"{node_id}.json"))
    if len(existing) > 1:
        raise ValueError(
            f"{node_id}: {len(existing)} review files on disk ({existing}). Two copies of "
            f"one node's review is two verdicts; resolve it before filing a third."
        )
    if existing:
        return existing[0]
    # New review: mirror the convention <subject>_<grade>_<branch>_<quarter>/
    parent = JUDGMENT_DIR / node_id.rsplit("_", 1)[0]
    parent.mkdir(parents=True, exist_ok=True)
    return parent / f"{node_id}.json"


def file_one(node_id: str, verdict_block: Dict[str, Any], reviewed_by: str,
             date: str, skeleton_dir: Path) -> Path:
    """Write one review: the evidence shown, reviewer-authored verdicts, assigned identity."""
    findings = verdict_block.get("findings")
    if not isinstance(findings, dict) or set(findings) != REQUIRED_FINDINGS:
        missing = REQUIRED_FINDINGS - set(findings or {})
        extra = set(findings or {}) - REQUIRED_FINDINGS
        raise ValueError(
            f"{node_id}: reply carries findings {sorted(findings or {})}, expected the six "
            f"judgment items (missing={sorted(missing)}, unexpected={sorted(extra)}). A "
            f"partial review is not a review; re-dispatch rather than filling the gap in."
        )
    for item, block in findings.items():
        if block.get("verdict") not in _VERDICTS:
            raise ValueError(
                f"{node_id}.{item}: verdict {block.get('verdict')!r} is not one of "
                f"{sorted(_VERDICTS)}."
            )
        if len(str(block.get("rationale", "")).strip()) < 40:
            raise ValueError(
                f"{node_id}.{item}: rationale is under 40 characters. §5 rejects it, and a "
                f"dispatcher padding it out would be authoring the review."
            )
    if verdict_block.get("overall") not in _VERDICTS:
        raise ValueError(f"{node_id}: overall {verdict_block.get('overall')!r} is invalid.")

    # The evidence block, exactly as the reviewer was shown it at dispatch time.
    skel_path = skeleton_dir / f"{node_id}.json"
    if not skel_path.exists():
        raise FileNotFoundError(
            f"{node_id}: no dispatch-time skeleton at {skel_path}. The samples a review "
            f"is filed with must be the ones the reviewer saw; rebuilding them here would "
            f"silently re-pair these verdicts with whatever the generator produces now. "
            f"Re-run `judgment_batches --batch N --skeleton-dir ...` BEFORE dispatching, "
            f"and keep the directory until the reply is filed."
        )
    review = json.loads(skel_path.read_text(encoding="utf-8"))
    if review.get("node_id") != node_id:
        raise ValueError(
            f"{node_id}: skeleton at {skel_path} carries node_id "
            f"{review.get('node_id')!r}. Refusing to file one node's verdicts against "
            f"another node's samples."
        )
    review["reviewed_by"] = reviewed_by
    review["review_date"] = date
    review["blind"] = True
    review["findings"] = findings
    review["overall"] = verdict_block["overall"]

    path = _target_path(node_id)
    path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="File a blind reviewer's §5 verdicts.")
    ap.add_argument("--batch", type=int, help="1-indexed batch from --plan")
    ap.add_argument("--nodes",
                    help="file of node ids (one per line) for a REPAIR dispatch -- a set "
                         "of nodes that went stale or whose review failed a §5 gate, which "
                         "does not line up with any --plan batch")
    ap.add_argument("--verdicts", required=True, help="the reviewer's reply, as JSON")
    ap.add_argument("--reviewed-by", required=True, help="the identity YOU assigned")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--skeleton-dir", required=True,
                    help="the --skeleton-dir used when this batch was DISPATCHED")
    args = ap.parse_args()

    reply = json.loads(Path(args.verdicts).read_text(encoding="utf-8"))
    claimed = reply.pop("reviewer", None)
    if claimed is not None and claimed != args.reviewed_by:
        raise ValueError(
            f"reply declares reviewer {claimed!r} but the dispatcher assigned "
            f"{args.reviewed_by!r}. Identity is assigned, never self-declared -- reject the "
            f"batch rather than filing under a name you did not issue."
        )

    if (args.batch is None) == (args.nodes is None):
        raise ValueError("pass exactly one of --batch or --nodes.")
    if args.batch is not None:
        expected = set(batches()[args.batch - 1])
    else:
        expected = set(Path(args.nodes).read_text(encoding="utf-8").split())
    if len(expected) > 25:
        raise ValueError(
            f"{len(expected)} nodes under one identity; §5 reviewer plurality caps a blind "
            f"batch at 25. Split the dispatch and assign a second identity."
        )
    got = {k for k in reply if k.startswith("mat_")}
    if got != expected:
        raise ValueError(
            f"reply covers {len(got)} node(s), expected {len(expected)}. "
            f"missing={sorted(expected - got)} unexpected={sorted(got - expected)}"
        )

    for node_id in sorted(expected):
        path = file_one(node_id, reply[node_id], args.reviewed_by, args.date,
                        Path(args.skeleton_dir))
        print(f"  filed {node_id} -> {path.relative_to(REPO_ROOT)}")
    print(f"{len(expected)} review(s) filed under {args.reviewed_by!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
