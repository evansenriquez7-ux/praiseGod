"""
Preserve the v1 review corpus as a QUEUE, not as evidence (plan step 1/step 5).

THE PROBLEM THIS SOLVES
-----------------------
`validate_judgment` requires `schema_version == 2`. Every one of the 151 reviews on disk
predates that schema and carries no `schema_version` at all, so on 2026-09-15 all 151 were
rejected as "legacy evidence ... unadjudicable" in a single step. The plan required the
opposite of that: step 1 calls for a "lossless filing path", step 5 for a cutover "without
losing findings", and M1 acceptance for "all legacy unresolved findings reconcile without
omissions". Enforcement shipped before the reconciliation, so the entire earned review
corpus stopped being visible as work.

WHY THIS IS NOT A MIGRATION, AND WILL NEVER BE ONE
--------------------------------------------------
A field-level v1 -> v2 migration is impossible in principle, not merely unimplemented. v2
demands per-sample contextual-validity verdicts, exact clause coverage, and dispatch-bound
provenance. A v1 reviewer was never asked any of those questions, so there is no v1 field
to map them from -- filling them would mean writing reviewer judgments no reviewer gave.
That is precisely the fabrication that cost 151 reviews their standing in tick A
(`6d8385f`), and it would be undetectable afterwards because the forged fields would be
internally consistent.

So this module refuses the migration and does the other half instead: it copies every v1
verdict and rationale into one machine-readable queue, marked `adjudicable: false` at the
top level and per node. The queue answers "what did the previous programme believe about
this node, and what still needs looking at" WITHOUT any of it counting as evidence. The
151 fresh blind re-reviews remain owed; this is what stops them from being re-derived from
nothing.

WHAT THIS DELIBERATELY DOES NOT DO (Scaling Mandate 6)
------------------------------------------------------
  * It does not gate. Nothing in `run_all` consumes this artifact, because a queue of
    superseded opinions is not a pass/fail condition -- and a gate that read it would be
    letting v1 verdicts back in through the side door.
  * It does not delete or rewrite the v1 files. They stay where they are, and
    `validate_judgment` goes on rejecting them by name; that rejection is correct. This
    only guarantees their content survives somewhere a reader will find it.
  * It preserves the v1 verdict TEXT verbatim and makes no attempt to judge whether a v1
    rationale was any good. Several were found to be templates in tick A. A `PASS` here
    is a record that someone once wrote PASS, nothing more.
  * A v1 review whose node no longer exists is reported as an orphan rather than dropped.

USAGE
-----
    PYTHONPATH=. .venv/bin/python tests/legacy_review_queue.py            # summary only
    PYTHONPATH=. .venv/bin/python tests/legacy_review_queue.py --write    # emit artifact
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = REPO_ROOT / "validation_reports" / "judgment"
QUEUE_PATH = (REPO_ROOT / "validation_reports" / "phase2_hardening"
              / "legacy_review_queue.json")

SCHEMA_VERSION = 1

# The schema a review must declare to be adjudicable evidence. Anything else is legacy and
# belongs in this queue instead. Read from the validator rather than restated, so the two
# cannot drift -- re-deriving a rule the other side owns is how duplicated copies disagree.
def _current_review_schema() -> int:
    from backend.app.practice_gen.validation.validate_judgment import REVIEW_SCHEMA_VERSION

    return REVIEW_SCHEMA_VERSION


# The six facets the v1 programme recorded. Named explicitly: a v1 file missing one is a
# hole worth reporting, not a key to skip silently.
V1_FACETS = (
    "competency_fulfillment",
    "comprehensive_coverage",
    "cognitive_capacity",
    "variant_comprehensiveness",
    "competency_alignment",
    "scale_appropriateness",
)

_PASS = "PASS"


def _overall_verdict(data: Dict[str, Any]) -> Any:
    """
    v1 wrote `overall` two ways: a bare string, and a dict carrying `verdict`.

    Both shapes are live in the corpus on disk, so both are read. Returning None rather
    than guessing keeps an unrecognised third shape visible as a hole.
    """
    overall = data.get("overall")
    if isinstance(overall, str):
        return overall
    if isinstance(overall, dict):
        return overall.get("verdict")
    return None


def _repo_relative(path: Path) -> str:
    """
    A repo-relative path where possible, the absolute one otherwise.

    Not a fallback that hides an error: a review outside the repository is unusual but
    its LOCATION is still the thing a reader needs, and `relative_to` would raise and
    take the whole queue down over a formatting detail.
    """
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _node_is_declared(node_id: str) -> bool:
    """Whether the curriculum still declares this node (an orphan review is flagged)."""
    from backend.app.practice_gen.registry import get_node_info

    return get_node_info(node_id) is not None


def _legacy_review_paths() -> List[Path]:
    if not REVIEW_DIR.is_dir():
        return []
    return sorted(REVIEW_DIR.rglob("*.json"))


def build_queue() -> Dict[str, Any]:
    """Every v1 review on disk, as a queue entry. Raises on a file it cannot parse."""
    current = _current_review_schema()
    nodes: List[Dict[str, Any]] = []
    skipped_current: List[str] = []
    hasher = hashlib.sha256()

    for path in _legacy_review_paths():
        raw = path.read_bytes()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            # Fail loudly: a review that will not parse is a lost finding, and silently
            # omitting it is the exact failure this module exists to prevent.
            raise ValueError(f"{path}: not valid JSON, so its findings cannot be "
                             f"preserved -- {exc}") from exc

        node_id = data.get("node_id") or path.stem
        if data.get("schema_version") == current:
            # Already adjudicable evidence; it does not belong in a legacy queue.
            skipped_current.append(node_id)
            continue

        hasher.update(raw)
        facets: Dict[str, Any] = {}
        missing: List[str] = []
        non_pass: List[str] = []
        found = data.get("findings") or {}
        for facet in V1_FACETS:
            entry = found.get(facet)
            if not isinstance(entry, dict):
                missing.append(facet)
                continue
            verdict = entry.get("verdict")
            facets[facet] = {
                "verdict": verdict,
                # Verbatim. This module does not summarise a reviewer's words.
                "rationale": entry.get("rationale"),
            }
            if verdict != _PASS:
                non_pass.append(facet)

        nodes.append({
            "node_id": node_id,
            "source_path": _repo_relative(path),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "declared_schema_version": data.get("schema_version"),
            "reviewed_by": data.get("reviewed_by"),
            "review_date": data.get("review_date"),
            "blind": data.get("blind"),
            "sample_seeds": data.get("sample_seeds") or [],
            "overall_verdict": _overall_verdict(data),
            # A review for a node the curriculum no longer declares is an orphan. It is
            # kept and flagged rather than dropped: the finding may still be real for a
            # renamed node, and a silent omission here is the loss this module prevents.
            "node_still_declared": _node_is_declared(node_id),
            "facets": facets,
            "facets_missing_from_the_v1_record": missing,
            "non_pass_facets": non_pass,
            # Repeated per node, not only at the top, so a single entry copied out of
            # this file cannot be mistaken for a current verdict.
            "adjudicable": False,
        })

    by_overall: Dict[str, int] = {}
    by_facet: Dict[str, int] = {}
    for entry in nodes:
        key = str(entry["overall_verdict"])
        by_overall[key] = by_overall.get(key, 0) + 1
        for facet, body in entry["facets"].items():
            if body["verdict"] != _PASS:
                by_facet[facet] = by_facet.get(facet, 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "legacy_review_queue",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "adjudicable": False,
        "why_not_adjudicable": (
            "These are v1 reviews. The current schema (v"
            f"{current}) requires per-sample contextual-validity verdicts, exact clause "
            "coverage and dispatch-bound provenance, which a v1 reviewer was never asked "
            "for and which therefore cannot be recovered from a v1 record without "
            "inventing them. Every node listed here still owes a fresh blind re-review. "
            "This file exists so that the previous programme's findings remain visible as "
            "a QUEUE while none of them counts as evidence."
        ),
        "required_work": (
            f"{len(nodes)} node(s) need a fresh blind review filed at schema_version "
            f"{current}. Rebuild a packet with: python -m "
            "backend.app.practice_gen.validation.judgment_packets --node <node_id>"
        ),
        "source_review_dir": REVIEW_DIR.relative_to(REPO_ROOT).as_posix(),
        "source_corpus_sha256": hasher.hexdigest(),
        "counts": {
            "legacy_nodes": len(nodes),
            "already_current_and_excluded": len(skipped_current),
            "by_overall_verdict": dict(sorted(by_overall.items())),
            "nodes_with_a_non_pass_facet": sum(1 for n in nodes if n["non_pass_facets"]),
            "non_pass_by_facet": dict(sorted(by_facet.items())),
            "records_missing_a_v1_facet": sum(
                1 for n in nodes if n["facets_missing_from_the_v1_record"]
            ),
            "orphan_reviews_for_undeclared_nodes": sum(
                1 for n in nodes if not n["node_still_declared"]
            ),
        },
        "nodes": nodes,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--write", action="store_true",
                    help=f"write {QUEUE_PATH.relative_to(REPO_ROOT)}")
    args = ap.parse_args()

    queue = build_queue()
    counts = queue["counts"]
    if not queue["nodes"]:
        print("legacy_review_queue: no v1 reviews on disk — nothing to preserve.")
        return 0

    print(f"legacy_review_queue: {counts['legacy_nodes']} legacy review(s), "
          f"NOT adjudicable evidence")
    print(f"  overall verdicts        : {counts['by_overall_verdict']}")
    print(f"  with a non-PASS facet   : {counts['nodes_with_a_non_pass_facet']}")
    print(f"  non-PASS by facet       : {counts['non_pass_by_facet']}")
    print(f"  missing a v1 facet      : {counts['records_missing_a_v1_facet']}")
    print(f"  orphan (node undeclared): {counts['orphan_reviews_for_undeclared_nodes']}")
    print(f"  re-reviews owed         : {counts['legacy_nodes']}")

    if args.write:
        QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        QUEUE_PATH.write_text(
            json.dumps(queue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"  wrote {QUEUE_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
