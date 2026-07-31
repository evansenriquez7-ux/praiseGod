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

It also enforces **freshness**, which is what keeps the artifact from decaying back
into a checkbox. A review is a judgment about *specific rendered content*; the moment
a DNA/registry/formatter change alters what a cited seed renders, that judgment is
about content the pipeline no longer serves. Filed-once-green-forever is exactly the
doc_rem.md §1.4 failure mechanism ("the code implements something adjacent; nothing
detects the gap") reproduced one level up. So every review's cited seeds are
re-rendered through the live pipeline and compared against the `question_text` the
reviewer recorded; drift is a loud FAIL demanding a fresh blind re-review. This is
doc_rem.md R4 ("doc changes ship with their enforcement, atomically") applied to the
judgment species: generator content and its review move together or CI stops.

No graceful fallbacks: a missing, unparseable, incomplete, boilerplate, or stale
review is a loud FAIL naming the node, never a skip (Ground Rule 3).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

from backend.app.practice_gen.registry import get_all_node_ids
from backend.app.practice_gen.validation.judgment_packets import _render_sample

# Anchored to the repo root from this file's location, not the process CWD.
# A CWD-relative path made the gate's verdict depend on where it was invoked
# from (from any other directory it reported "directory does not exist" rather
# than validating), which is a determinism defect in a determinism harness.
_REPO_ROOT = Path(__file__).resolve().parents[4]
JUDGMENT_DIR = _REPO_ROOT / "validation_reports" / "judgment"

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
            # Without a seed the sample cannot be re-rendered, so its freshness
            # can never be verified — that is the loophole the staleness gate
            # below exists to close, so an unseeded sample is itself an error.
            if not isinstance(s.get("seed"), int):
                errs.append(
                    f"{node_id}: samples_reviewed[{i}] missing an integer 'seed'; a sample that "
                    f"cannot be re-rendered cannot be checked for staleness."
                )
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


def _normalize(text: Any) -> str:
    """Collapse whitespace so re-rendered text compares on content, not layout."""
    return " ".join(str(text or "").split())


def _validate_freshness(node_id: str, data: Dict[str, Any]) -> List[str]:
    """
    Re-render every seed the review cites and assert the review is still about
    the content the pipeline actually serves.

    A review is a judgment about specific rendered problems. Once a DNA, registry
    binding, or formatter changes what a cited seed produces, the filed verdict
    describes content that no longer exists — the review is stale and its verdict
    is unearned, whatever it says. Detecting that is the only thing standing
    between "genuine review artifact" and "checkbox with more fields".

    Render failures are hard errors, never skips (Ground Rule 3): a seed the
    pipeline can no longer generate is a strictly worse form of drift than one
    that renders differently.
    """
    errs: List[str] = []
    for i, s in enumerate(data.get("samples_reviewed") or []):
        if not isinstance(s, dict) or not isinstance(s.get("seed"), int):
            continue  # already reported as a schema error by _validate_one
        seed = s["seed"]
        try:
            current = _render_sample(node_id, seed)
        except Exception as exc:  # noqa: BLE001 — re-raised as a named harness failure
            errs.append(
                f"{node_id}: samples_reviewed[{i}] cites seed {seed}, which the live pipeline "
                f"can no longer render ({type(exc).__name__}: {exc}). Reproduce with: "
                f"python -m backend.app.practice_gen.validation.judgment_packets --node {node_id}"
            )
            continue
        reviewed_text = _normalize(s.get("question_text"))
        current_text = _normalize(current.get("question_text"))
        if reviewed_text != current_text:
            errs.append(
                f"{node_id}: STALE review — seed {seed} no longer renders the content that was "
                f"judged. Reviewed: {reviewed_text!r}; now renders: {current_text!r}. The "
                f"generator changed after this review was filed, so its verdict is unearned; "
                f"a fresh blind re-review is required. Rebuild the packet with: "
                f"python -m backend.app.practice_gen.validation.judgment_packets --node {node_id}"
            )
    return errs


def validate_judgment_reviews() -> List[str]:
    """
    Validate every registered node's judgment review. Returns a flat list of
    errors (empty == all reviews genuine and complete).

    Cross-file anti-boilerplate: no rationale string may be reused verbatim
    across two different nodes. That single check defeats the identical-stub
    farm regardless of how many fields a stub fills in.

    Per-node freshness: every cited seed is re-rendered through the live
    pipeline and compared to the text the reviewer recorded, so a review cannot
    outlive the content it judged.
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

        errors.extend(_validate_freshness(nid, data))

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
