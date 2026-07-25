"""
Practice Generation — Judgment Review Validator (hard gate)

The judgment items in `docs/pgen_judgment.md` (Competency Fulfillment, Cognitive
Capacity, Scale Appropriateness, ...) are the checks a machine CANNOT score. The
honest requirement (`doc_rem.md` §3.1) is that a reviewer who is *not the author*
of the generator files a genuine per-node review artifact citing specific rendered
samples — "the verifier is not the author, and the output is an artifact, not a
checkbox."

This module does not — and cannot — judge whether a review's verdict is *correct*.
What it CAN do is make the hollow-stub attack fail: it rejects boilerplate, demands
node-specific rationale for every judgment item, and requires the review to carry
the actual samples it claims to have judged. A run of 151 byte-identical stub files
(same reviewer, same seeds, all-PASS, same one-sentence evidence) — the exact thing
this replaces — fails here loudly.

No graceful fallbacks: a missing, unparseable, incomplete, or boilerplate review is
a loud FAIL naming the node, never a skip (Ground Rule 3).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set

from backend.app.practice_gen.registry import get_all_node_ids

JUDGMENT_DIR = Path("validation_reports/judgment")

# The six judgment items from docs/pgen_judgment.md. Every genuine review must
# carry a finding for each, with a node-specific rationale.
REQUIRED_FINDINGS: Set[str] = {
    "competency_fulfillment",
    "comprehensive_coverage",
    "cognitive_capacity",
    "variant_comprehensiveness",
    "competency_alignment",
    "scale_appropriateness",
}

VALID_VERDICTS: Set[str] = {"PASS", "FAIL", "CONCERN"}

# Placeholder reviewer identities that indicate an auto-generated stub, not a
# genuine independent review. A real review names the model/agent that produced it.
_PLACEHOLDER_REVIEWERS: Set[str] = {"", "reviewer-agent", "agent", "reviewer", "tbd", "todo"}

# Minimum rationale length (chars). Below this a rationale cannot be node-specific.
_MIN_RATIONALE_LEN = 40

# Minimum distinct sample seeds a genuine review must have looked at.
_MIN_SEEDS = 3


def _node_file(node_id: str) -> Path:
    parts = node_id.split("_")
    group_dir = "_".join(parts[:-1])  # e.g. "mat_g1_na_q1"
    return JUDGMENT_DIR / group_dir / f"{node_id}.json"


def _validate_one(node_id: str, path: Path) -> List[str]:
    """Return a list of schema/quality errors for one node's review file."""
    errs: List[str] = []
    if not path.exists():
        return [f"{node_id}: missing genuine judgment review (expected '{path}')."]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{node_id}: review file '{path}' is not valid JSON: {exc}."]

    if not isinstance(data, dict):
        return [f"{node_id}: review file '{path}' must be a JSON object."]

    if data.get("node_id") != node_id:
        errs.append(f"{node_id}: review 'node_id' is {data.get('node_id')!r}, expected {node_id!r}.")

    reviewer = str(data.get("reviewed_by", "")).strip().lower()
    if reviewer in _PLACEHOLDER_REVIEWERS:
        errs.append(
            f"{node_id}: 'reviewed_by' is a placeholder ({data.get('reviewed_by')!r}); "
            f"a genuine review must name the reviewing model/agent."
        )

    if data.get("blind") is not True:
        errs.append(
            f"{node_id}: review must attest 'blind': true — the reviewer must be given only the "
            f"competency text + rendered samples, blind to the generator implementation."
        )

    seeds = data.get("sample_seeds")
    if not isinstance(seeds, list) or len(set(seeds)) < _MIN_SEEDS:
        errs.append(f"{node_id}: 'sample_seeds' must list >= {_MIN_SEEDS} distinct seeds (got {seeds!r}).")

    # The review must carry the actual samples it judged, not just claim to have seen them.
    samples = data.get("samples_reviewed")
    if not isinstance(samples, list) or len(samples) < _MIN_SEEDS:
        errs.append(
            f"{node_id}: 'samples_reviewed' must contain >= {_MIN_SEEDS} rendered samples "
            f"(question_text + correct_answer) the reviewer actually judged."
        )
    else:
        for i, s in enumerate(samples):
            if not isinstance(s, dict) or not str(s.get("question_text", "")).strip():
                errs.append(f"{node_id}: samples_reviewed[{i}] missing non-empty 'question_text'.")
                break

    findings = data.get("findings")
    if not isinstance(findings, dict):
        errs.append(f"{node_id}: 'findings' must be an object keyed by the six judgment items.")
        return errs

    missing = REQUIRED_FINDINGS - set(findings.keys())
    if missing:
        errs.append(f"{node_id}: findings missing required items: {sorted(missing)}.")

    for item in REQUIRED_FINDINGS & set(findings.keys()):
        f = findings[item]
        if not isinstance(f, dict):
            errs.append(f"{node_id}: findings['{item}'] must be an object with 'verdict' and 'rationale'.")
            continue
        verdict = str(f.get("verdict", "")).upper()
        if verdict not in VALID_VERDICTS:
            errs.append(f"{node_id}: findings['{item}'].verdict {f.get('verdict')!r} not in {sorted(VALID_VERDICTS)}.")
        rationale = str(f.get("rationale", "")).strip()
        if len(rationale) < _MIN_RATIONALE_LEN:
            errs.append(
                f"{node_id}: findings['{item}'].rationale too short/absent "
                f"(< {_MIN_RATIONALE_LEN} chars); a node-specific justification is required."
            )

    if str(data.get("overall", "")).upper() not in VALID_VERDICTS:
        errs.append(f"{node_id}: 'overall' verdict {data.get('overall')!r} not in {sorted(VALID_VERDICTS)}.")

    return errs


def validate_judgment_reviews() -> List[str]:
    """
    Validate every registered node's judgment review. Returns a flat list of
    errors (empty == all reviews genuine and complete).

    Cross-file anti-boilerplate: no rationale string may be reused verbatim
    across two different nodes. That single check defeats the identical-stub
    farm regardless of how many fields a stub fills in.
    """
    errors: List[str] = []
    node_ids = get_all_node_ids()

    if not JUDGMENT_DIR.exists():
        return [f"Judgment review directory '{JUDGMENT_DIR}' does not exist."]

    seen_rationales: Dict[str, str] = {}  # rationale -> first node_id that used it

    for nid in node_ids:
        path = _node_file(nid)
        errs = _validate_one(nid, path)
        errors.extend(errs)
        if errs or not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for item, f in (data.get("findings") or {}).items():
            if not isinstance(f, dict):
                continue
            rationale = str(f.get("rationale", "")).strip().lower()
            if len(rationale) < _MIN_RATIONALE_LEN:
                continue
            if rationale in seen_rationales and seen_rationales[rationale] != nid:
                errors.append(
                    f"{nid}: findings['{item}'].rationale is copied verbatim from "
                    f"'{seen_rationales[rationale]}' — boilerplate is not a genuine review."
                )
            else:
                seen_rationales[rationale] = nid

    return errors


def summarize_verdicts() -> Dict[str, int]:
    """
    Tally overall verdicts across all present review files. This is surfaced
    loudly by the runner: a genuine review that says FAIL is documented
    pedagogical debt — the point of the judgment layer is that these findings
    are visible, not buried under a green 'reviews exist' check.
    """
    counts: Dict[str, int] = {"PASS": 0, "CONCERN": 0, "FAIL": 0, "UNKNOWN": 0, "reviewed": 0}
    for nid in get_all_node_ids():
        path = _node_file(nid)
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        counts["reviewed"] += 1
        verdict = str(data.get("overall", "")).upper()
        counts[verdict if verdict in VALID_VERDICTS else "UNKNOWN"] += 1
    return counts


if __name__ == "__main__":
    import sys

    v = summarize_verdicts()
    print(
        f"Verdicts over {v['reviewed']} reviewed nodes: "
        f"PASS={v['PASS']} CONCERN={v['CONCERN']} FAIL={v['FAIL']} UNKNOWN={v['UNKNOWN']}"
    )
    errs = validate_judgment_reviews()
    if errs:
        print(f"Judgment review validation: {len(errs)} problem(s) found.")
        for e in errs[:40]:
            print(f"  FAIL {e}")
        if len(errs) > 40:
            print(f"  ... and {len(errs) - 40} more.")
        sys.exit(1)
    print("Judgment review validation: all nodes have genuine, complete reviews.")
    sys.exit(0)
