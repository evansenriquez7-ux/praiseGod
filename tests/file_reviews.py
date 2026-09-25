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
DISPATCH TIME (`judgment_batches --skeleton-dir`). The reviewer supplies the six findings,
per-sample checks, exact-clause judgments and overall verdict; the filer validates and preserves
those bytes while adding dispatcher-controlled identity and dispatch attribution. Nothing in
the reply can replace the evidence block or self-assign provenance.

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
        --reviewed-by blind-attester-gpt-5.6-terra-light-b1-20260923 --date 2026-09-23 \
        --skeleton-dir local_only/scratch/review/b1/ \
        --dispatch-prompt local_only/scratch/review/b1_prompt.txt \
        --dispatch-id judgment-v2-b1-20260923 \
        --samples-delivery "reviewer read only the saved prompt path" \
        --tool-uses-by-reviewer "read prompt; wrote one JSON reply"
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.practice_gen.validation.validate_judgment import (  # noqa: E402
    JUDGMENT_DIR,
    REQUIRED_FINDINGS,
    SAMPLE_ASSESSMENTS,
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


def _reasoning(block: Any, *, where: str, field: str) -> None:
    if not isinstance(block, dict) or block.get("verdict") not in _VERDICTS:
        raise ValueError(f"{where}: verdict must be one of {sorted(_VERDICTS)}.")
    if len(str(block.get(field, "")).strip()) < 40:
        raise ValueError(f"{where}: {field} is under 40 characters.")


def derived_overall(findings: Dict[str, Any], assessments: List[Dict[str, Any]],
                    clauses: List[Dict[str, Any]]) -> str:
    """The overall verdict a reply's own verdicts imply -- the dispatch prompt's rule."""
    verdicts = [block.get("verdict") for block in findings.values()]
    verdicts.append(findings["competency_fulfillment"]["decomposition"].get("verdict"))
    verdicts += [check.get("verdict") for a in assessments for check in a["checks"].values()]
    verdicts += [clause.get("verdict") for clause in clauses]
    if "FAIL" in verdicts:
        return "FAIL"
    return "CONCERN" if "CONCERN" in verdicts else "PASS"


def file_one(node_id: str, verdict_block: Dict[str, Any], reviewed_by: str,
             date: str, skeleton_dir: Path, *, raw_response: Path,
             prompt_path: Path, dispatch_prefix: str, samples_delivery: str,
             tool_uses_by_reviewer: str, write: bool = True) -> Path:
    """Write one review: the evidence shown, reviewer-authored verdicts, assigned identity."""
    # Preflight and write run over the same parsed batch object. Never inject dispatcher
    # attribution into the reviewer's raw in-memory reply: the second pass must see the same
    # bytes the first pass validated, and the raw response remains the audit authority.
    verdict_block = copy.deepcopy(verdict_block)
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
        _reasoning(block, where=f"{node_id}.{item}", field="rationale")
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
    sample_ids = review.get("sample_ids") or []
    requirements = review.get("requirements_snapshot") or []
    requirement_ids = [str(req.get("id", "")) for req in requirements]

    assessments = verdict_block.get("sample_assessments")
    if not isinstance(assessments, list) or [a.get("sample_id") for a in assessments
                                             if isinstance(a, dict)] != sample_ids:
        raise ValueError(
            f"{node_id}: sample_assessments must cover every dispatch-time sample exactly "
            "once and in packet order. Re-dispatch rather than filling gaps as dispatcher."
        )
    for assessment in assessments:
        if "reviewer_identity" in assessment or "dispatch_id" in assessment:
            raise ValueError(f"{node_id}: reviewer response must not self-assign attribution.")
        checks = assessment.get("checks")
        if not isinstance(checks, dict) or set(checks) != SAMPLE_ASSESSMENTS:
            raise ValueError(
                f"{node_id} sample {assessment.get('sample_id')}: checks must be exactly "
                f"{sorted(SAMPLE_ASSESSMENTS)}."
            )
        for name, block in checks.items():
            _reasoning(block, where=f"{node_id}.{assessment['sample_id']}.{name}",
                       field="reasoning")

    clauses = verdict_block.get("clause_evidence")
    if not isinstance(clauses, list) or [str(c.get("requirement_id", "")) for c in clauses
                                         if isinstance(c, dict)] != requirement_ids:
        raise ValueError(
            f"{node_id}: clause_evidence must cover the exact dispatch-time requirements once "
            f"and in order; expected={requirement_ids}."
        )
    expected_clauses = {str(req.get("id", "")): req.get("clause") for req in requirements}
    for clause in clauses:
        req_id = str(clause.get("requirement_id", ""))
        if "reviewer_identity" in clause or "dispatch_id" in clause:
            raise ValueError(f"{node_id}: reviewer response must not self-assign attribution.")
        if clause.get("clause") != expected_clauses.get(req_id):
            raise ValueError(f"{node_id}.{req_id}: clause text differs from the dispatched packet.")
        _reasoning(clause, where=f"{node_id}.{req_id}", field="reasoning")
        cited = clause.get("sample_ids")
        if not isinstance(cited, list) or not cited or not set(cited) <= set(sample_ids):
            raise ValueError(f"{node_id}.{req_id}: sample_ids must cite dispatched samples.")

    decomposition = findings["competency_fulfillment"].get("decomposition")
    _reasoning(decomposition, where=f"{node_id}.competency_fulfillment.decomposition",
               field="reasoning")

    # `overall` must follow from the reply's OWN verdicts, by the rule the dispatch
    # prompt states. Until 2026-09-25 any valid verdict was accepted, and
    # mat_g2_mg_q2_2 was filed `overall: PASS` beside a CONCERN finding.
    # validate_judgment still flags that node, but `legacy_review_queue.json`'s
    # `by_overall_verdict` census reads the stored field, so the corpus overstated its
    # PASSes. The dispatcher never edits a verdict: a contradiction is refused, and the
    # reviewer is asked to reconcile its own reply.
    derived = derived_overall(findings, assessments, clauses)
    if verdict_block["overall"] != derived:
        raise ValueError(
            f"{node_id}: overall {verdict_block['overall']!r} contradicts the reply's own "
            f"verdicts, which give {derived!r} (FAIL if any finding, sample check, clause or "
            f"decomposition is FAIL; else CONCERN if any is CONCERN; else PASS). Ask the "
            f"reviewer to reconcile its reply; never edit a verdict as dispatcher."
        )
    findings["competency_fulfillment"]["clause_ids"] = requirement_ids
    findings["competency_fulfillment"]["decomposition"]["requirement_ids"] = requirement_ids
    findings["comprehensive_coverage"]["clause_ids"] = requirement_ids

    dispatch_id = f"{dispatch_prefix}:{node_id}"
    for assessment in assessments:
        assessment["reviewer_identity"] = reviewed_by
        assessment["dispatch_id"] = dispatch_id
    for clause in clauses:
        clause["reviewer_identity"] = reviewed_by
        clause["dispatch_id"] = dispatch_id

    review["reviewed_by"] = reviewed_by
    review["review_date"] = date
    review["blind"] = True
    review["findings"] = findings
    review["sample_assessments"] = assessments
    review["clause_evidence"] = clauses
    review["overall"] = verdict_block["overall"]

    path = _target_path(node_id)
    if not write:
        return path
    response_dir = path.parent / ".responses"
    response_dir.mkdir(parents=True, exist_ok=True)
    response_copy = response_dir / f"{dispatch_prefix}.json"
    prompt_copy = response_dir / f"{dispatch_prefix}.prompt.txt"
    shutil.copyfile(raw_response, response_copy)
    shutil.copyfile(prompt_path, prompt_copy)
    review["dispatch_provenance"] = [{
        "dispatch_id": dispatch_id,
        "reviewer_identity": reviewed_by,
        "review_date": date,
        "blind": True,
        "packet_digest": review["packet_digest"],
        "clause_ids": requirement_ids,
        "response_ref": str(response_copy.relative_to(path.parent)),
        "response_digest": hashlib.sha256(response_copy.read_bytes()).hexdigest(),
        "prompt_ref": str(prompt_copy.relative_to(path.parent)),
        "prompt_digest": hashlib.sha256(prompt_copy.read_bytes()).hexdigest(),
        "samples_delivery": samples_delivery,
        "tool_uses_by_reviewer": tool_uses_by_reviewer,
    }]
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
    ap.add_argument("--dispatch-prompt", required=True,
                    help="exact prompt file sent to the blind reviewer")
    ap.add_argument("--dispatch-id", required=True,
                    help="unique batch dispatch prefix; node id is appended mechanically")
    ap.add_argument("--samples-delivery", required=True,
                    help="truthful description of how/where the prompt was delivered")
    ap.add_argument("--tool-uses-by-reviewer", required=True,
                    help="truthful free-form tool-use report from the reviewer")
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

    if Path(args.dispatch_id).name != args.dispatch_id or not args.dispatch_id.strip():
        raise ValueError("--dispatch-id must be one non-empty filename-safe component.")

    # Preflight the entire response before the first review is overwritten. A malformed
    # node late in a 25-node reply must not leave a half-filed evidentiary batch.
    for node_id in sorted(expected):
        file_one(node_id, reply[node_id], args.reviewed_by, args.date,
                 Path(args.skeleton_dir), raw_response=Path(args.verdicts),
                 prompt_path=Path(args.dispatch_prompt), dispatch_prefix=args.dispatch_id,
                 samples_delivery=args.samples_delivery,
                 tool_uses_by_reviewer=args.tool_uses_by_reviewer, write=False)

    for node_id in sorted(expected):
        path = file_one(node_id, reply[node_id], args.reviewed_by, args.date,
                        Path(args.skeleton_dir), raw_response=Path(args.verdicts),
                        prompt_path=Path(args.dispatch_prompt), dispatch_prefix=args.dispatch_id,
                        samples_delivery=args.samples_delivery,
                        tool_uses_by_reviewer=args.tool_uses_by_reviewer)
        print(f"  filed {node_id} -> {path.relative_to(REPO_ROOT)}")
    print(f"{len(expected)} review(s) filed under {args.reviewed_by!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
