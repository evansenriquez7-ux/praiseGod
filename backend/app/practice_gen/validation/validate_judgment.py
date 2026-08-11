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

Freshness alone proved insufficient, and the way it failed is worth stating: it
re-renders `samples_reviewed` and never reads the rationale. A set of 151 reviews
was filed in which the samples block WAS regenerated fresh from the live pipeline
and a template rationale — one sentence frame with the node ID and seed list
substituted in — was stapled to it. Freshness passed all 151; the verbatim-reuse
check passed them too, because substituting the node ID makes no two rationales
byte-identical. 115 of them quoted question stems that appear nowhere in their own
samples. Three cross-file/structural checks close that hole (thresholds below):
quote provenance, rationale-skeleton clustering, and reviewer plurality.

No graceful fallbacks: a missing, unparseable, incomplete, boilerplate, templated,
or stale review is a loud FAIL naming the node, never a skip (Ground Rule 3).
"""

from __future__ import annotations

import collections
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from backend.app.practice_gen.registry import get_all_node_ids, get_node_info
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

# --- Anti-template thresholds -------------------------------------------------
# The verbatim-reuse check below defeats byte-identical stubs, but not a template
# with the node ID and seed list substituted in — which is exactly how a set of
# 151 fabricated all-PASS reviews passed this gate. Three structural checks close
# that hole; each threshold is stated here so weakening one is a visible diff.

# How many nodes may share one *normalized* rationale skeleton (node IDs, quoted
# spans, and digits stripped) before it is a template rather than a coincidence.
# Sibling nodes legitimately produce similar prose; a skeleton spanning more than
# a handful of nodes is a fill-in-the-blank form, not independent judgment.
_MAX_SKELETON_CLUSTER = 3

# How many nodes one `reviewed_by` identity may cover. A blind review is dispatched
# in batches of <= 25 nodes (docs/pgen_judgment.md review protocol); one identity
# stamped across the whole tree means one pass, not 151 independent judgments.
_MAX_NODES_PER_REVIEWER = 25

# Quoted spans shorter than this are too generic to trace to a source.
_MIN_QUOTE_LEN = 4

# A quoted span: an opening quote at a word boundary, a closing quote followed by
# whitespace/punctuation/end. The boundary anchors keep intra-word apostrophes
# ("student's") from being read as quote delimiters.
_QUOTE_RE = re.compile(r"""(?:(?<=^)|(?<=[\s(\[]))(['"])(.+?)\1(?=[\s.,;:)\]]|$)""")

# Node-ID-ish tokens, quoted spans, and digit runs are the three things a template
# substitutes per node. Stripping them collapses a template to a constant string.
_NODE_ID_RE = re.compile(r"\bmat_g\d+_[a-z]+_q\d+(?:_\d+)?\b")
_DIGITS_RE = re.compile(r"\d+")


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
        elif verdict != "PASS":
            errs.append(f"{node_id}: findings['{item}'].verdict is '{verdict}' (must be 'PASS').")
        rationale = str(f.get("rationale", "")).strip()
        if len(rationale) < _MIN_RATIONALE_LEN:
            errs.append(
                f"{node_id}: findings['{item}'].rationale too short/absent "
                f"(< {_MIN_RATIONALE_LEN} chars); a node-specific justification is required."
            )

    overall = str(data.get("overall", "")).upper()
    if overall not in VALID_VERDICTS:
        errs.append(f"{node_id}: 'overall' verdict {data.get('overall')!r} not in {sorted(VALID_VERDICTS)}.")
    elif overall != "PASS":
        errs.append(
            f"{node_id}: overall judgment verdict is '{overall}' (must be 'PASS'); "
            f"curriculum alignment defects and concerns must be resolved."
        )

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


def _rationale_skeleton(rationale: str) -> str:
    """
    Collapse a rationale to the structure that survives per-node substitution.

    A template review is written once and filled in per node: the node ID, the
    seed numbers, and the quoted competency/sample text change; the sentence
    frame does not. Strip exactly those three and two genuinely independent
    rationales still read differently, while 151 instances of one form collapse
    to a single identical string.
    """
    s = _NODE_ID_RE.sub("<NODE>", rationale.strip().lower())
    s = _QUOTE_RE.sub("<QUOTED>", s)
    s = _DIGITS_RE.sub("#", s)
    return " ".join(s.split())


def _provenance_corpus(node_id: str, data: Dict[str, Any]) -> str:
    """
    Everything a rationale for this node is entitled to quote: the samples the
    review itself carries (stems, answers, options, formatter names) plus the
    node's own MATATAG competency text. Anything else quoted as if observed was
    not observed here.
    """
    parts: List[str] = [node_id, str(get_node_info(node_id).get("competency", ""))]
    for s in data.get("samples_reviewed") or []:
        if not isinstance(s, dict):
            continue
        parts.append(str(s.get("question_text", "")))
        parts.append(str(s.get("correct_answer", "")))
        parts.append(str(s.get("formatter", "")))
        for opt in s.get("options") or []:
            if isinstance(opt, dict):
                parts.append(str(opt.get("value", "")))
            else:
                parts.append(str(opt))
    return " ".join(" ".join(p.split()).lower() for p in parts)


def _validate_quote_provenance(node_id: str, data: Dict[str, Any]) -> List[str]:
    """
    Every span a rationale puts in quotes must exist in the review's own packet.

    The freshness gate re-renders `samples_reviewed` and proves *the samples block*
    is current — but it never reads the rationale, so a template rationale stapled
    onto a freshly-rendered samples block passes it untouched. That is the precise
    mechanism by which 115 of 151 filed reviews quoted stems that appear nowhere in
    the samples they claim to have judged. A quoted stem with no source in the
    packet is fabricated evidence, which is a harder failure than a wrong verdict.
    """
    errs: List[str] = []
    corpus = _provenance_corpus(node_id, data)
    for item, f in (data.get("findings") or {}).items():
        if not isinstance(f, dict):
            continue
        rationale = str(f.get("rationale", ""))
        for _, span in _QUOTE_RE.findall(rationale):
            probe = " ".join(span.split()).lower().strip().rstrip(".")
            if len(probe) < _MIN_QUOTE_LEN:
                continue
            if probe not in corpus:
                errs.append(
                    f"{node_id}: findings['{item}'].rationale quotes {span!r}, which appears "
                    f"nowhere in this review's own samples_reviewed or competency text — the "
                    f"reviewer cited content it was never shown. Rebuild the packet and "
                    f"re-review blind: python -m backend.app.practice_gen.validation."
                    f"judgment_packets --node {node_id}"
                )
    return errs


def _validate_reviewer_plurality(reviewers: Dict[str, List[str]]) -> List[str]:
    """
    One reviewer identity may not stamp the whole tree.

    Blind review is dispatched in batches of <= _MAX_NODES_PER_REVIEWER nodes, each
    to a separate agent that sees only that batch's packets. A single `reviewed_by`
    string spanning more nodes than a batch therefore did not come from the review
    protocol — it came from one pass writing files, which is the shape a fabricated
    set has and a genuine one cannot.
    """
    errs: List[str] = []
    for name, nodes in sorted(reviewers.items()):
        if len(nodes) > _MAX_NODES_PER_REVIEWER:
            errs.append(
                f"reviewer plurality: 'reviewed_by' identity {name!r} covers {len(nodes)} nodes "
                f"(max {_MAX_NODES_PER_REVIEWER} — one blind batch). A single identity spanning "
                f"more than one batch is one pass, not independent per-node judgment. "
                f"First nodes: {sorted(nodes)[:5]}."
            )
    return errs


def _validate_skeleton_clusters(skeletons: Dict[tuple, List[str]]) -> List[str]:
    """Fail any normalized rationale skeleton shared by more than _MAX_SKELETON_CLUSTER nodes."""
    errs: List[str] = []
    for (item, skeleton), nodes in sorted(skeletons.items(), key=lambda kv: -len(kv[1])):
        if len(nodes) > _MAX_SKELETON_CLUSTER:
            errs.append(
                f"template rationale: {len(nodes)} nodes share one findings['{item}'] skeleton "
                f"(max {_MAX_SKELETON_CLUSTER}) — node IDs, quoted spans, and digits stripped, the "
                f"rationales are the same sentence frame, which is a fill-in-the-blank form rather "
                f"than independent judgment. Skeleton: {skeleton[:160]!r}. "
                f"Nodes: {sorted(nodes)[:5]}{' ...' if len(nodes) > 5 else ''}."
            )
    return errs


def validate_judgment_reviews(fail_fast: bool = False) -> List[str]:
    """
    Validate every registered node's judgment review. Returns a flat list of
    errors (empty == all reviews genuine, complete, fresh, and PASS).

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
    skeletons: Dict[tuple, List[str]] = collections.defaultdict(list)  # (item, skeleton) -> nodes
    reviewers: Dict[str, List[str]] = collections.defaultdict(list)  # reviewed_by -> nodes

    for nid in node_ids:
        path = _node_file(nid)
        errs = _validate_one(nid, path)
        errors.extend(errs)
        if errs or not path.exists():
            if fail_fast and errors:
                return errors
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            if fail_fast and errors:
                return errors
            continue

        freshness_errs = _validate_freshness(nid, data)
        errors.extend(freshness_errs)
        if fail_fast and errors:
            return errors

        errors.extend(_validate_quote_provenance(nid, data))
        if fail_fast and errors:
            return errors

        reviewers[str(data.get("reviewed_by", "")).strip()].append(nid)

        for item, f in (data.get("findings") or {}).items():
            if not isinstance(f, dict):
                continue
            rationale = str(f.get("rationale", "")).strip().lower()
            if len(rationale) < _MIN_RATIONALE_LEN:
                continue
            skeletons[(item, _rationale_skeleton(rationale))].append(nid)
            if rationale in seen_rationales and seen_rationales[rationale] != nid:
                errors.append(
                    f"{nid}: findings['{item}'].rationale is copied verbatim from "
                    f"'{seen_rationales[rationale]}' — boilerplate is not a genuine review."
                )
                if fail_fast:
                    return errors
            else:
                seen_rationales[rationale] = nid

        if fail_fast and errors:
            return errors

    # Cross-file structure. These are the checks a per-node pass structurally
    # cannot make: a template is only visible against its siblings, and a single
    # reviewer identity is only visible across the whole tree.
    errors.extend(_validate_skeleton_clusters(skeletons))
    errors.extend(_validate_reviewer_plurality(reviewers))

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
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Judgment Review Validator")
    parser.add_argument("--fail-fast", "-f", action="store_true", help="Exit immediately on first failure")
    args = parser.parse_args()

    v = summarize_verdicts()
    print(
        f"Verdicts over {v['reviewed']} reviewed nodes: "
        f"PASS={v['PASS']} CONCERN={v['CONCERN']} FAIL={v['FAIL']} UNKNOWN={v['UNKNOWN']}"
    )
    errs = validate_judgment_reviews(fail_fast=args.fail_fast)
    if errs:
        print(f"Judgment review validation: {len(errs)} problem(s) found.")
        for e in errs[:40]:
            print(f"  FAIL {e}")
        if len(errs) > 40:
            print(f"  ... and {len(errs) - 40} more.")
        sys.exit(1)
    print("Judgment review validation: all nodes have genuine, complete reviews with PASS verdicts.")
    sys.exit(0)
