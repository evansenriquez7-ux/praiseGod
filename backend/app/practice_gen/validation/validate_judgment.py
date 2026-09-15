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
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.registry import get_all_node_ids, get_node_info
from backend.app.practice_gen.validation.judgment_packets import (
    _json_digest,
    _render_sample,
    build_packet,
)

# §8 inventory: the assertions this module can independently fail on. Each must be
# proven by a mutation naming it in `Mutation.asserts`, or excused in
# validate_coverage.UNPROVEN_ASSERTIONS with a reason and a date.
ASSERTIONS = (
    "judgment_review_schema_5",       # _validate_one: seeds, samples, six findings, verdicts
    "judgment_packet_integrity_5",    # canonical sample/replay/packet digests and identities
    "judgment_clause_coverage_5",     # exact live requirement snapshot and one verdict per clause
    "judgment_sample_assessments_5",  # every delivered sample explicitly judged on four checks
    "judgment_dispatch_provenance_5", # packet-bound identity plus immutable raw response digest
    "judgment_review_freshness_5",    # STALE -- the reviewed seed no longer renders what was judged
    "judgment_options_recorded_5",    # a choice item reviewed without the option set it was shown
    "judgment_visual_evidence_5",     # missing/corrupt render-derived visual evidence
    "judgment_quote_provenance_5",    # a rationale quoting content absent from its own packet
    "judgment_rationale_verbatim_5",  # a rationale byte-identical to another node's
    "judgment_rationale_skeleton_5",  # _validate_skeleton_clusters: one sentence frame, many nodes
    "judgment_reviewer_plurality_5",  # one 'reviewed_by' identity across more than one blind batch
    "judgment_reviews",               # run_all's rollup print for the stage
)

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
REVIEW_SCHEMA_VERSION = 2
SAMPLE_ASSESSMENTS: Set[str] = {
    "mathematical_validity",
    "contextual_logical_validity",
    "ambiguity",
    "learner_facing_clarity",
}

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


def _packet_core_from_review(data: Dict[str, Any]) -> Dict[str, Any]:
    """Reconstruct exactly the packet content whose digest the review claims."""
    return {
        "schema_version": data.get("schema_version"),
        "sampling_version": data.get("sampling_version"),
        "node_id": data.get("node_id"),
        "competency_snapshot": data.get("competency_snapshot"),
        "requirements_snapshot": data.get("requirements_snapshot"),
        "sample_ids": data.get("sample_ids"),
        "samples": data.get("samples_reviewed"),
    }


def _validate_v2_schema(node_id: str, path: Path, data: Dict[str, Any]) -> List[str]:
    """Validate the merged, lossless review record introduced by hardening H-06/H-07."""
    errs: List[str] = []
    if data.get("schema_version") != REVIEW_SCHEMA_VERSION:
        # The rejection is correct and stays. What it must NOT imply is that the prior
        # verdict is gone: on 2026-09-15 this message rejected all 151 reviews at once
        # with nowhere for a reader to find what the previous programme had concluded,
        # which is the loss the plan's "lossless filing path" was written to prevent.
        # A v1 record cannot be migrated -- v2 wants judgments a v1 reviewer was never
        # asked for -- so it is preserved as a QUEUE instead, never as evidence.
        return [
            f"{node_id}: review schema_version is {data.get('schema_version')!r}, expected "
            f"{REVIEW_SCHEMA_VERSION}; legacy evidence omits canonical learner-visible fields, "
            "clause coverage, and dispatch-bound provenance and is unadjudicable. A fresh "
            "blind re-review is owed. The v1 verdict and rationale are preserved, as a "
            "non-adjudicable lead only, in "
            "validation_reports/phase2_hardening/legacy_review_queue.json "
            "(rebuild: PYTHONPATH=. .venv/bin/python tests/legacy_review_queue.py --write)."
        ]

    info = get_node_info(node_id) or {}
    expected_competency = {
        "text": info.get("competency", ""),
        "grade": info.get("grade"),
        "quarter": info.get("quarter"),
        "subdomain": info.get("subdomain") or info.get("domain"),
    }
    if data.get("competency_snapshot") != expected_competency:
        errs.append(
            f"{node_id}: competency_snapshot differs from the complete live MATATAG competency "
            "and grade/quarter context; altered or omitted wording cannot inherit PASS."
        )
    expected_requirements = [dict(req) for req in (info.get("requires") or [])]
    if data.get("requirements_snapshot") != expected_requirements:
        errs.append(
            f"{node_id}: requirements_snapshot is not the exact live ordered requirement set; "
            "omission, duplication, altered wording, and unknown clauses are unadjudicable."
        )

    samples = data.get("samples_reviewed")
    sample_ids = data.get("sample_ids")
    if not isinstance(samples, list) or not isinstance(sample_ids, list):
        return errs + [f"{node_id}: v2 review requires list samples_reviewed and sample_ids."]
    actual_ids = [sample.get("sample_id") if isinstance(sample, dict) else None
                  for sample in samples]
    if sample_ids != actual_ids or len(set(sample_ids)) != len(sample_ids):
        errs.append(
            f"{node_id}: sample_ids must be unique and exactly match samples_reviewed in "
            "delivered order; additional historical samples cannot replace a required sample."
        )
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            continue
        digestable = {key: value for key, value in sample.items() if key != "replay_digest"}
        if sample.get("replay_digest") != _json_digest(digestable):
            errs.append(
                f"{node_id}: samples_reviewed[{index}] replay_digest does not bind its full "
                "canonical learner-visible and replay content."
            )

    recorded_digest = data.get("packet_digest")
    if recorded_digest != _json_digest(_packet_core_from_review(data)):
        errs.append(
            f"{node_id}: packet_digest does not match the exact delivered packet recorded in "
            "this review; verdicts and evidence may not be re-paired."
        )

    assessments = data.get("sample_assessments")
    if not isinstance(assessments, list):
        errs.append(f"{node_id}: sample_assessments must explicitly judge every delivered sample.")
        assessments = []
    assessed_ids = [a.get("sample_id") for a in assessments if isinstance(a, dict)]
    if assessed_ids != sample_ids or len(assessed_ids) != len(set(assessed_ids)):
        errs.append(
            f"{node_id}: sample_assessments must cover each delivered sample exactly once, in "
            "packet order, without missing, duplicate, or foreign sample_ids."
        )
    for index, assessment in enumerate(assessments):
        if not isinstance(assessment, dict):
            errs.append(f"{node_id}: sample_assessments[{index}] must be an object.")
            continue
        checks = assessment.get("checks")
        if not isinstance(checks, dict) or set(checks) != SAMPLE_ASSESSMENTS:
            errs.append(
                f"{node_id}: sample_assessments[{index}].checks must contain exactly "
                f"{sorted(SAMPLE_ASSESSMENTS)}."
            )
            continue
        for name, block in checks.items():
            if not isinstance(block, dict) or block.get("verdict") not in VALID_VERDICTS:
                errs.append(f"{node_id}: sample {assessment.get('sample_id')} {name} verdict is invalid.")
                continue
            if block["verdict"] != "PASS":
                errs.append(
                    f"{node_id}: sample {assessment.get('sample_id')} {name} is "
                    f"{block['verdict']}; every learner-visible sample must pass."
                )
            if len(str(block.get("reasoning", "")).strip()) < _MIN_RATIONALE_LEN:
                errs.append(
                    f"{node_id}: sample {assessment.get('sample_id')} {name} reasoning is "
                    f"under {_MIN_RATIONALE_LEN} characters."
                )

    expected_by_id = {str(req.get("id", "")): req for req in expected_requirements}
    clause_evidence = data.get("clause_evidence")
    if not isinstance(clause_evidence, list):
        errs.append(f"{node_id}: clause_evidence must contain one verdict per requirement.")
        clause_evidence = []
    clause_ids = [str(entry.get("requirement_id", ""))
                  for entry in clause_evidence if isinstance(entry, dict)]
    if (set(clause_ids) != set(expected_by_id) or len(clause_ids) != len(expected_by_id)
            or len(clause_ids) != len(set(clause_ids))):
        errs.append(
            f"{node_id}: clause_evidence must cover the exact requirement IDs once each; "
            f"expected={sorted(expected_by_id)}, got={clause_ids}."
        )
    valid_sample_ids = set(sample_ids)
    for entry in clause_evidence:
        if not isinstance(entry, dict):
            errs.append(f"{node_id}: every clause_evidence entry must be an object.")
            continue
        req_id = str(entry.get("requirement_id", ""))
        expected = expected_by_id.get(req_id)
        if expected is not None and entry.get("clause") != expected.get("clause"):
            errs.append(f"{node_id}: clause_evidence[{req_id}] alters the live clause wording.")
        verdict = entry.get("verdict")
        if verdict not in VALID_VERDICTS:
            errs.append(f"{node_id}: clause_evidence[{req_id}] verdict is invalid.")
        elif verdict != "PASS":
            errs.append(f"{node_id}: clause_evidence[{req_id}] is {verdict}; every clause must pass.")
        cited = entry.get("sample_ids")
        if not isinstance(cited, list) or not cited or not set(cited) <= valid_sample_ids:
            errs.append(
                f"{node_id}: PASS clause_evidence[{req_id}] must cite one or more sample_ids "
                "from the delivered packet."
            )
        if len(str(entry.get("reasoning", "")).strip()) < _MIN_RATIONALE_LEN:
            errs.append(f"{node_id}: clause_evidence[{req_id}] reasoning is too short/absent.")
        for field in ("reviewer_identity", "dispatch_id"):
            if not str(entry.get(field, "")).strip():
                errs.append(f"{node_id}: clause_evidence[{req_id}] missing {field} attribution.")

    findings = data.get("findings") or {}
    for item in ("competency_fulfillment", "comprehensive_coverage"):
        block = findings.get(item) if isinstance(findings, dict) else None
        if isinstance(block, dict) and block.get("clause_ids") != clause_ids:
            errs.append(
                f"{node_id}: findings['{item}'].clause_ids must reference every clause_evidence "
                "entry in order."
            )
    fulfillment = findings.get("competency_fulfillment") if isinstance(findings, dict) else None
    decomposition = fulfillment.get("decomposition") if isinstance(fulfillment, dict) else None
    if (not isinstance(decomposition, dict)
            or decomposition.get("verdict") != "PASS"
            or decomposition.get("requirement_ids") != clause_ids
            or len(str(decomposition.get("reasoning", "")).strip()) < _MIN_RATIONALE_LEN):
        errs.append(
            f"{node_id}: competency_fulfillment.decomposition must PASS, explain why the "
            "requirements losslessly cover the full competency, and reference every clause."
        )

    dispatches = data.get("dispatch_provenance")
    if not isinstance(dispatches, list) or not dispatches:
        errs.append(f"{node_id}: dispatch_provenance must bind the delivered packet and raw reply.")
        dispatches = []
    dispatch_by_id: Dict[str, Dict[str, Any]] = {}
    for dispatch in dispatches:
        if not isinstance(dispatch, dict):
            errs.append(f"{node_id}: every dispatch_provenance entry must be an object.")
            continue
        dispatch_id = str(dispatch.get("dispatch_id", "")).strip()
        if not dispatch_id or dispatch_id in dispatch_by_id:
            errs.append(f"{node_id}: dispatch IDs must be non-empty and unique within the record.")
            continue
        dispatch_by_id[dispatch_id] = dispatch
        reviewer = str(dispatch.get("reviewer_identity", "")).strip().lower()
        if reviewer in _PLACEHOLDER_REVIEWERS:
            errs.append(f"{node_id}: dispatch {dispatch_id} has a placeholder reviewer identity.")
        if dispatch.get("blind") is not True:
            errs.append(f"{node_id}: dispatch {dispatch_id} must record blind: true.")
        if dispatch.get("packet_digest") != recorded_digest:
            errs.append(f"{node_id}: dispatch {dispatch_id} does not bind the delivered packet digest.")
        dispatched_clauses = dispatch.get("clause_ids")
        if not isinstance(dispatched_clauses, list) or len(dispatched_clauses) > 25:
            errs.append(f"{node_id}: dispatch {dispatch_id} must carry at most 25 clause verdicts.")
        response_ref = dispatch.get("response_ref")
        response_digest = str(dispatch.get("response_digest", ""))
        if not isinstance(response_ref, str) or not response_ref.strip():
            errs.append(f"{node_id}: dispatch {dispatch_id} missing exact returned response_ref.")
        else:
            response_path = (path.parent / response_ref).resolve()
            try:
                response_path.relative_to(JUDGMENT_DIR.resolve())
            except ValueError:
                errs.append(f"{node_id}: dispatch {dispatch_id} response_ref escapes judgment storage.")
            else:
                if not response_path.is_file():
                    errs.append(f"{node_id}: dispatch {dispatch_id} raw response is missing at {response_ref!r}.")
                elif hashlib.sha256(response_path.read_bytes()).hexdigest() != response_digest:
                    errs.append(f"{node_id}: dispatch {dispatch_id} raw response digest does not match.")
    used_dispatches = {
        str(entry.get("dispatch_id", "")) for entry in clause_evidence if isinstance(entry, dict)
    } | {
        str(entry.get("dispatch_id", "")) for entry in assessments if isinstance(entry, dict)
    }
    if used_dispatches != set(dispatch_by_id):
        errs.append(
            f"{node_id}: dispatch provenance must exactly cover dispatch IDs used by sample and "
            f"clause assessments; got={sorted(dispatch_by_id)}, used={sorted(used_dispatches)}."
        )
    for entry in [*clause_evidence, *assessments]:
        if not isinstance(entry, dict):
            continue
        dispatch = dispatch_by_id.get(str(entry.get("dispatch_id", "")))
        if dispatch is not None and entry.get("reviewer_identity") != dispatch.get("reviewer_identity"):
            errs.append(
                f"{node_id}: seed(s)={data.get('sample_seeds')} assessment reviewer does not match dispatch "
                f"{entry.get('dispatch_id')!r}."
            )
    for dispatch_id, dispatch in dispatch_by_id.items():
        assigned = dispatch.get("clause_ids")
        observed = [entry.get("requirement_id") for entry in clause_evidence
                    if isinstance(entry, dict) and entry.get("dispatch_id") == dispatch_id]
        if not isinstance(assigned, list) or collections.Counter(map(str, assigned)) != collections.Counter(map(str, observed)):
            errs.append(
                f"{node_id}: seed(s)={data.get('sample_seeds')} dispatch {dispatch_id!r} clause allocation does not match "
                f"attributed evidence: assigned={assigned!r}, observed={observed!r}."
            )
    for assessment in assessments:
        if isinstance(assessment, dict):
            for field in ("reviewer_identity", "dispatch_id"):
                if not str(assessment.get(field, "")).strip():
                    errs.append(
                        f"{node_id}: sample assessment {assessment.get('sample_id')} missing "
                        f"{field} attribution."
                    )
    return errs


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

    errs.extend(_validate_v2_schema(node_id, path, data))

    seeds = data.get("sample_seeds")
    if (not isinstance(seeds, list) or len(set(seeds)) < _MIN_SEEDS
            or seeds != [s.get("seed") for s in (data.get("samples_reviewed") or [])
                         if isinstance(s, dict)]):
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


# What a sample carries when it records no answer at all. A distinct sentinel rather
# than "" because "" is a value `correct_answer` can legitimately hold.
_NO_ANSWER = "<no answer recorded>"


def _answer_value(raw: Any) -> str:
    """
    An answer field reduced for comparison, WITHOUT `_normalize`'s falsy collapse.

    `_normalize` is `str(x or "")`, which is right for a stem and wrong for an answer:
    it maps `False`, `0`, `[]` and `None` all to the empty string. `true_false` items
    key a bool, and a record that stored the string 'False' compares against a live
    render of `False` -- identical content -- while `_normalize` reads the recorded
    side as 'False' and the live side as '', reporting drift that did not happen.

    That is not hypothetical and it is not §5-only: `docs/pgen_contract.md` carried
    "b11_mat_g2_na_q3_5 seed 11 was attested against a key of False and now renders an
    empty key" as the motivating example for closing §6F's answer blind spot. Rendered
    2026-09-10, that seed still keys `False`; the "empty key" was `_normalize(False)`
    reporting on itself. Measured the same day, using this helper instead changes ZERO
    §5 findings on the current tree (the falsy shape does not occur in the review
    corpus) and removes 10 would-be false positives from §6F's answer comparison,
    where `true_false` is common.

    The inverse direction matters as much: `None` and `False` must not compare equal,
    or an item that stops producing an answer reads as unchanged.
    """
    if raw is None:
        return _NO_ANSWER
    return " ".join(str(raw).split())


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

    **What is compared, and what is not.** The stem, the keyed answer, and the set
    of offered options. For a long time only the stem was compared, and that gap was
    live: a change to mat_g3_mg_q1_0's distractors left every stem byte-identical
    while the options went from [8, 15, 16, 17] to [8, 12, 16, 20], so the gate
    called the review fresh while its rationale reasoned at length about 15, 16 and
    17 -- options that no longer existed. A reviewer judges distractor quality,
    scale and answerability from the options as much as from the stem, so a review
    whose options have moved is exactly as stale as one whose stem has.

    Options are compared as an unordered multiset of values, not as a sequence:
    which options are offered is what the reviewer judged, and A/B/C/D placement
    moving is not drift in the content.

    A sample that records no `options` while its live render offers some is no longer
    skipped -- it is its own named failure (`judgment_options_recorded_5`). See the
    comment at that check for what the skip was hiding and why the decision is made
    from the render rather than from a formatter name.

    Visual freshness compares the render-derived structural evidence carried by the
    packet, never a payload paraphrase. Missing evidence on a currently visual sample is
    unadjudicable. The named residual is layout: static markup cannot establish crowding,
    overlap, colour contrast or physical touch-target size. Hints and cloze templates
    are also still outside this comparison.

    SECOND KNOWN LIMITATION, measured (Scaling Mandate 6). Freshness re-renders only the
    seeds a review ALREADY cites, so it cannot notice that the packet builder has since
    grown seeds the reviewer was never shown. `_stratified_seeds` now emits
    max-difficulty seeds (>= 500) and discrete-variant-coverage seeds (>= 600) that
    demonstrate 975 (variant, value) pairs tree-wide, and a review filed before those
    existed is judged fresh on the thinner packet it was built from. Measured 2026-09-10:
    **32 of 151 reviews are missing at least one variant-coverage seed the current
    builder emits**, and 39 are missing at least one seed of any kind. The gate is a set
    comparison, not a text comparison -- `set(_stratified_seeds(node)) - {s["seed"] for s
    in samples_reviewed}` -- so its findings are separable by construction from the
    hundreds of routine STALE findings around them, and all 32 are enumerable today.
    Deliberately not shipped in the commit that measured it: this baseline is red (1013
    findings) and Scaling Mandate 5 says a gate built into that cannot be told from the
    noise. Build it in the commit that drives the re-review queue to zero, which is also
    the commit in which its own count becomes zero.
    """
    errs: List[str] = []
    reviewed_samples = data.get("samples_reviewed") or []
    if data.get("schema_version") == REVIEW_SCHEMA_VERSION:
        try:
            current_packet = build_packet(node_id)
        except Exception as exc:  # noqa: BLE001 — converted to a named, reproducible failure
            return [
                f"{node_id}: the current canonical student-path packet cannot be rendered "
                f"({type(exc).__name__}: {exc}). Reproduce with: python -m "
                f"backend.app.practice_gen.validation.judgment_packets --node {node_id}"
            ]
        if data.get("sampling_version") != current_packet["sampling_version"]:
            errs.append(
                f"{node_id}: STALE review -- sampling_version changed from "
                f"{data.get('sampling_version')!r} to {current_packet['sampling_version']!r}; a "
                "review of a thinner or different allocation cannot certify the current packet."
            )
        if data.get("sample_ids") != current_packet["sample_ids"]:
            errs.append(
                f"{node_id}: STALE review -- required sample identities changed; additional "
                "historical samples cannot replace a newly required sample."
            )
        if data.get("packet_digest") != current_packet["packet_digest"]:
            errs.append(
                f"{node_id}: STALE review -- the canonical learner-visible packet digest changed. "
                "Stem, resolved answer, ordered options, hints, cloze, visual payload/rendered "
                "structure, response configuration, replay inputs, and effective choices are bound."
            )
        current_by_index = {
            i: current for i, current in enumerate(current_packet["samples"])
            if i < len(reviewed_samples)
        }
    else:
        # Preserve all legacy checks while v1 evidence is being migrated. A schema
        # failure must not exempt a CONCERN/FAIL or stale record from the old controls.
        raw_current: List[Dict[str, Any]] = []
        current_indices: List[int] = []
        for i, sample in enumerate(reviewed_samples):
            if not isinstance(sample, dict) or not isinstance(sample.get("seed"), int):
                continue
            try:
                raw_current.append(_render_sample(node_id, sample["seed"]))
                current_indices.append(i)
            except Exception as exc:  # noqa: BLE001 — named rather than skipped
                errs.append(
                    f"{node_id}: samples_reviewed[{i}] cites seed {sample['seed']}, which the "
                    f"live pipeline can no longer render ({type(exc).__name__}: {exc})."
                )
        from tests.frontend_renderer import attach_rendered_visual_descriptions
        from backend.app.practice_gen.validation.judgment_packets import finalize_samples

        rendered_current = finalize_samples(attach_rendered_visual_descriptions(raw_current))
        current_by_index = dict(zip(current_indices, rendered_current))

    for i, s in enumerate(reviewed_samples):
        if i not in current_by_index:
            continue
        seed = s["seed"]
        current = current_by_index[i]
        reviewed_text = _normalize(s.get("question_text"))
        current_text = _normalize(current.get("question_text"))
        rebuild = (
            f"Rebuild the packet with: "
            f"python -m backend.app.practice_gen.validation.judgment_packets --node {node_id}"
        )
        if reviewed_text != current_text:
            errs.append(
                f"{node_id}: STALE review — seed {seed} no longer renders the content that was "
                f"judged. Reviewed: {reviewed_text!r}; now renders: {current_text!r}. The "
                f"generator changed after this review was filed, so its verdict is unearned; "
                f"a fresh blind re-review is required. {rebuild}"
            )
            continue  # the stem already proves drift; one error per seed is enough

        reviewed_visual = s.get("visual_render")
        current_visual = current.get("visual_render")
        if current_visual is not None and reviewed_visual is None:
            errs.append(
                f"{node_id}: samples_reviewed[{i}] (seed {seed}) records no render-derived "
                f"visual evidence, but the live item renders {current_visual.get('visual_type')}. "
                f"Missing learner-visible evidence is unadjudicable. {rebuild}"
            )
            continue
        if reviewed_visual is not None and current_visual is None:
            errs.append(
                f"{node_id}: STALE review -- seed {seed} was judged with a rendered visual "
                f"but the live item has none. {rebuild}"
            )
            continue
        if reviewed_visual is not None and reviewed_visual != current_visual:
            errs.append(
                f"{node_id}: STALE review -- seed {seed}'s rendered visual description or "
                f"renderer-input digest changed. A visual judgment cannot survive that drift. "
                f"{rebuild}"
            )
            continue

        reviewed_opts = _option_values(s)
        current_opts = _option_values(current)

        # An MCQ reviewed without its options is UNADJUDICABLE, and until 2026-09-10 it
        # was silently skipped -- the `is not None` guard below read "no options recorded"
        # and "not a choice item" as the same thing. Measured on this tree the day the
        # skip was closed: 505 of 2026 recorded samples (434 mcq + 71 read_mcq) carried no
        # options at all, so for a quarter of the corpus the option comparison never ran
        # and, on read_mcq, the ANSWER comparison could not be resolved either -- its
        # `correct_answer` is an A-D key, and a key with no option table behind it names
        # nothing. That is Ground Rule 3's silent skip, one level up.
        #
        # Whether an item is a choice item is decided by the LIVE RENDER, never by a
        # formatter name: `read_mcq`, `mcq` and `cloze` all carry option tables today and
        # a grade-7 formatter that does not exist yet may carry one too (Scaling Mandate
        # 4). Rendering is also the only place that knows, so this is enforced here rather
        # than in the parse-time schema, which cannot see it.
        #
        # This check MUST precede the answer comparison: on key-valued formatters, an
        # answer cannot be resolved without its option table. Comparing the raw field
        # first would report an answer-drift symptom for a review that is structurally
        # unadjudicable.
        if current_opts is not None and reviewed_opts is None:
            errs.append(
                f"{node_id}: samples_reviewed[{i}] (seed {seed}) records no 'options', but the "
                f"live render of that seed offers {len(current_opts)}: {current_opts}. A review "
                f"of a choice item that does not carry the choices it was shown cannot be "
                f"checked for option drift at all, and on a key-valued formatter its answer "
                f"cannot be resolved either. Re-file the review from a current packet. {rebuild}"
            )
            continue
        if reviewed_opts is not None and current_opts is None:
            errs.append(
                f"{node_id}: STALE review -- seed {seed} was reviewed as a choice item offering "
                f"{reviewed_opts}, but the live render offers no options at all. The item stopped "
                f"being a selection task after the review was filed. {rebuild}"
            )
            continue

        reviewed_answer, reviewed_keyed = _resolved_answer(s)
        current_answer, current_keyed = _resolved_answer(current)
        # Compare the VALUE the item keys, not the slot the value landed in -- but only
        # when both sides actually resolve a key through their own option table. When
        # either side does not, the raw field is all there is and it is compared as-is,
        # which is why an MCQ reviewed without its options is a named failure above
        # rather than a comparison made on a guess.
        if reviewed_keyed != current_keyed:
            reviewed_answer = _answer_value(s.get("correct_answer"))
            current_answer = _answer_value(current.get("correct_answer"))
        if reviewed_answer != current_answer:
            errs.append(
                f"{node_id}: STALE review — seed {seed} keeps its wording but no longer keys the "
                f"same answer. Reviewed: {_answer_display(s)}; now keys: {_answer_display(current)}. A "
                f"verdict about correctness cannot survive the answer changing under it. {rebuild}"
            )
            continue

        if reviewed_opts is not None and current_opts is not None and reviewed_opts != current_opts:
            errs.append(
                f"{node_id}: STALE review — seed {seed} keeps its wording but is no longer offered "
                f"the same options. Reviewed: {reviewed_opts}; now offers: {current_opts}. "
                f"Distractor quality, scale and answerability are judged from the options, so a "
                f"verdict about them is unearned once they move. {rebuild}"
            )
    return errs


def _option_values(sample: Dict[str, Any]) -> Optional[List[str]]:
    """
    The offered option values as a sorted list of strings, or None when the sample
    records no options at all (cloze and fill-in-blank items genuinely have none).

    Sorted because which options are offered is what a reviewer judges; their
    A/B/C/D placement moving is not drift in the content.
    """
    opts = sample.get("options")
    if not isinstance(opts, list):
        return None
    values: List[str] = []
    for o in opts:
        if isinstance(o, dict) and "value" in o:
            values.append(_answer_value(o["value"]))
        else:
            values.append(_answer_value(o))
    return sorted(values)


def _resolved_answer(sample: Dict[str, Any]) -> tuple:
    """
    `(value, resolved_through_a_key)` for this sample's keyed answer.

    `read_mcq` stores an A-D KEY in `correct_answer` on 59 nodes; `mcq` and `cloze`
    store the value. Comparing the raw field across a re-render therefore compares a
    SLOT on the key-valued formatters, and a slot is not what a reviewer judged --
    `_option_values` has said so since it was written ("A/B/C/D placement moving is not
    drift in the content") and compares options as an unordered multiset for exactly
    this reason. The answer comparison contradicted its own sibling.

    Measured 2026-09-10 over every recorded sample whose stem still renders identically
    and whose answer is key-resolvable on BOTH sides:

      * 88 findings had a DIFFERENT key and the SAME resolved value -- placement-only.
        mat_g1_mg_q4_1 seed 42 was reviewed keying C='2:15' and now keys B='2:15': the
        option multiset is identical, the correct value is identical, the letter moved.
        (An earlier hand count of this population read the NEW letter through the OLD
        option table and reported it as C='2:15' -> B='2:10'. That is the same
        one-step-removed comparison this docstring exists to stop; the rendered pair is
        printed above.)
      * 2 findings had the SAME key and a DIFFERENT resolved value -- mat_g3_na_q1_0
        seed 45, keyed 'C' before and after while the item moved from 491 to 7844.
        Those were reported by NOTHING in the answer comparison.
      * 2 findings had a different key and a genuinely different value (mat_g2_na_q1_2).

    So the raw comparison over-reported 88 and under-reported 2 on this tree. The
    under-report is the part that matters and the part the option multiset cannot cover
    for you: an item whose correct flag moves to a DISTRACTOR THAT WAS ALREADY OFFERED
    keeps its stem, keeps its option multiset, and can keep its key -- every §5 gate
    passes it while the answer changed. `stale_answer_same_key` in tests/mutation_harness
    plants exactly that.

    The placement half is a NARROWING, and a narrowing cannot be proven by a mutation
    (the harness needs the plant to make the validator FAIL, and a narrowing makes it
    quieter). It is pinned by `test_judgment_answer_resolution.py` in both directions
    instead, which is what that file is for.
    """
    raw = _answer_value(sample.get("correct_answer"))
    opts = sample.get("options")
    if not isinstance(opts, list):
        return raw, False
    for o in opts:
        if isinstance(o, dict) and _answer_value(o.get("key")) == raw and "value" in o:
            return _answer_value(o["value"]), True
    return raw, False


def _answer_display(sample: Dict[str, Any]) -> str:
    """
    The keyed answer as a reader can act on it: the value, not the slot it landed in.

    `read_mcq` stores an A-D KEY in `correct_answer` on 59 nodes, not a value, so a
    drift message built from the raw field read "Reviewed: 'C'; now keys: 'B'" -- which
    tells a reader a letter moved and nothing about whether the item changed. Measured
    2026-09-10 across the 128 letter-keyed STALE findings on this tree: 88 of them key a
    genuinely DIFFERENT VALUE under an identical stem and an identical option set
    (mat_g1_mg_q4_1 seed 42 was reviewed keying C='2:15' and now keys B='2:10'), and
    ZERO are shuffle-only. So the finding is right in every case and only its wording
    was wrong.

    This is display only, and its resolution is best-effort by construction -- an answer
    that is not a key of this sample's own option table is shown as-is -- because a
    message helper may never be the thing that decides whether a review passes. The
    paragraph that stood here until 2026-09-10 said "the comparison in
    `_validate_freshness` is unchanged and still runs on the raw field", which stopped
    being true in the same commit that wrote it: `_resolved_answer` now decides the
    comparison, and the re-rendered pair above ("now keys B='2:10'") was the
    one-step-removed reading `_resolved_answer`'s own docstring corrects to B='2:15'.
    Both errors are left visible here because a docstring that quietly self-heals is
    how the next reader stops checking.
    """
    raw = _answer_value(sample.get("correct_answer"))
    opts = sample.get("options")
    if not isinstance(opts, list):
        return repr(raw)
    for o in opts:
        if isinstance(o, dict) and _answer_value(o.get("key")) == raw and "value" in o:
            return f"{raw!r} (= {_answer_value(o['value'])!r})"
    return repr(raw)


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


def _review_reasonings(data: Dict[str, Any]):
    """Yield every reviewer-authored reasoning field with its precise record location.

    Hypothetical remediation text is deliberately not part of this iterator. Quotation
    marks in a proposed future example are not claims about observed packet evidence.
    """
    for item, finding in (data.get("findings") or {}).items():
        if not isinstance(finding, dict):
            continue
        yield f"findings['{item}'].rationale", str(finding.get("rationale", ""))
        decomposition = finding.get("decomposition")
        if isinstance(decomposition, dict):
            yield (f"findings['{item}'].decomposition.reasoning",
                   str(decomposition.get("reasoning", "")))
    for index, entry in enumerate(data.get("clause_evidence") or []):
        if isinstance(entry, dict):
            yield f"clause_evidence[{index}].reasoning", str(entry.get("reasoning", ""))
    for index, assessment in enumerate(data.get("sample_assessments") or []):
        if not isinstance(assessment, dict):
            continue
        for name, block in (assessment.get("checks") or {}).items():
            if isinstance(block, dict):
                yield (f"sample_assessments[{index}].checks['{name}'].reasoning",
                       str(block.get("reasoning", "")))


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
    for location, rationale in _review_reasonings(data):
        for _, span in _QUOTE_RE.findall(rationale):
            probe = " ".join(span.split()).lower().strip().rstrip(".")
            if len(probe) < _MIN_QUOTE_LEN:
                continue
            if probe not in corpus:
                errs.append(
                    f"{node_id}: {location} quotes {span!r}, which appears "
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
    for (item, skeleton), nodes in sorted(skeletons.items(), key=lambda kv: -len(set(kv[1]))):
        distinct_nodes = sorted(set(nodes))
        if len(distinct_nodes) > _MAX_SKELETON_CLUSTER:
            errs.append(
                f"template rationale: {len(distinct_nodes)} nodes share one {item} skeleton "
                f"(max {_MAX_SKELETON_CLUSTER}) — node IDs, quoted spans, and digits stripped, the "
                f"rationales are the same sentence frame, which is a fill-in-the-blank form rather "
                f"than independent judgment. Skeleton: {skeleton[:160]!r}. "
                f"Nodes: {distinct_nodes[:5]}{' ...' if len(distinct_nodes) > 5 else ''}."
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
    dispatch_clause_counts: Dict[str, int] = collections.defaultdict(int)
    dispatch_identities: Dict[str, str] = {}

    for nid in node_ids:
        path = _node_file(nid)
        errors.extend(_validate_one(nid, path))
        if fail_fast and errors:
            return errors

        # Only a review that is absent or unreadable can be skipped here. This
        # used to `continue` whenever _validate_one returned ANY error -- and a
        # CONCERN or FAIL verdict always returns one, because a non-PASS verdict
        # is itself reported as an error. The effect was that freshness, quote
        # provenance, skeleton clustering and reviewer plurality ran ONLY over
        # all-PASS reviews: every CONCERN/FAIL review was exempt from all four,
        # which is backwards, since those are exactly the reviews a generator
        # fix is most likely to invalidate.
        #
        # Measured when this was found: mat_g1_na_q1_7 (CONCERN) had a stale
        # sample on disk -- a generator change had altered what its cited seed
        # renders -- while the full gate reported 0 stale reviews.
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # DISPOSITION: checked -- _validate_one reports the malformed file by name
            # in the same run, so the review cannot pass by being unreadable.
            continue  # already reported by _validate_one
        if not isinstance(data, dict) or not isinstance(data.get("findings"), dict):
            continue  # malformed shape, already reported by _validate_one

        errors.extend(_validate_freshness(nid, data))
        if fail_fast and errors:
            return errors

        errors.extend(_validate_quote_provenance(nid, data))
        if fail_fast and errors:
            return errors

        if data.get("schema_version") == REVIEW_SCHEMA_VERSION:
            for dispatch in data.get("dispatch_provenance") or []:
                if not isinstance(dispatch, dict):
                    continue
                dispatch_id = str(dispatch.get("dispatch_id", "")).strip()
                identity = str(dispatch.get("reviewer_identity", "")).strip()
                if not dispatch_id or not identity:
                    continue
                if dispatch_id in dispatch_identities and dispatch_identities[dispatch_id] != identity:
                    errors.append(
                        f"dispatch {dispatch_id!r} is attributed to both "
                        f"{dispatch_identities[dispatch_id]!r} and {identity!r}."
                    )
                dispatch_identities[dispatch_id] = identity
                reviewers[identity].append(nid)
                dispatch_clause_counts[dispatch_id] += len(dispatch.get("clause_ids") or [])
        else:
            reviewers[str(data.get("reviewed_by", "")).strip()].append(nid)

        for location, reasoning in _review_reasonings(data):
            rationale = reasoning.strip().lower()
            if len(rationale) < _MIN_RATIONALE_LEN:
                continue
            if location.startswith("findings["):
                category = location.split("].", 1)[0] + "]"
            elif ".checks[" in location:
                category = "sample_" + location.rsplit("checks[", 1)[1].split("]", 1)[0]
            else:
                category = location.split("[", 1)[0]
            skeletons[(category, _rationale_skeleton(rationale))].append(nid)
            if rationale in seen_rationales and seen_rationales[rationale] != nid:
                errors.append(
                    f"{nid}: {location} is copied verbatim from "
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
    for dispatch_id, count in sorted(dispatch_clause_counts.items()):
        if count > 25:
            errors.append(
                f"dispatch {dispatch_id!r} carries {count} clause verdicts across records "
                "(max 25); split it rather than enlarging the exemption."
            )

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
            # DISPOSITION: checked -- _validate_one fails the run on a malformed review,
            # so this cannot turn a bad review into a pass. RESIDUAL: it DOES understate
            # `reviewed`, so the summary line counts fewer nodes than exist on disk.
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
    # Display only, and it exists for one reason: a mutation aimed at §5 has to be
    # VISIBLE to be scored. While the re-review queue is open this gate reports hundreds
    # of routine STALE findings, and a planted violation that lands past the 40-line cut
    # is scored SURVIVED -- a hole in the harness reported where the hole is really in
    # the test (Scaling Mandate 2). `--all` prints every finding; the error set, the
    # count and the exit code are identical either way. The mutation harness also runs
    # its `baseline_must_not_contain` probe through this flag, so the pre-plant guard is
    # checked against the WHOLE corpus rather than its first 40 lines.
    parser.add_argument("--all", "-a", action="store_true",
                        help="Print every finding rather than the first 40 (display only)")
    args = parser.parse_args()

    v = summarize_verdicts()
    print(
        f"Verdicts over {v['reviewed']} reviewed nodes: "
        f"PASS={v['PASS']} CONCERN={v['CONCERN']} FAIL={v['FAIL']} UNKNOWN={v['UNKNOWN']}"
    )
    errs = validate_judgment_reviews(fail_fast=args.fail_fast)
    if errs:
        print(f"Judgment review validation: {len(errs)} problem(s) found.")
        # Structural findings first. These are the fabrication detectors -- one
        # rationale skeleton stamped across many nodes, one reviewer identity
        # spanning the tree, a quote with no source in its own packet. Routine
        # staleness outnumbers them by hundreds while the honest re-review queue is
        # open, so a flat print buried them below the cut and the mutation proving
        # skeleton clustering scored SURVIVED for want of a visible line. run_all
        # already orders §6 this way for the same reason. Display order only: the
        # error set, the count and the exit code are unchanged.
        _STRUCTURAL = ("template rationale", "reviewer plurality", "quotes ",
                       "copied verbatim from")
        structural = [e for e in errs if any(m in e for m in _STRUCTURAL)]
        routine = [e for e in errs if e not in structural]
        shown = structural + routine
        limit = len(shown) if args.all else 40
        for e in shown[:limit]:
            print(f"  FAIL {e}")
        if len(errs) > limit:
            print(f"  ... and {len(errs) - limit} more. Re-run with --all to see them.")
        sys.exit(1)
    print("Judgment review validation: all nodes have genuine, complete reviews with PASS verdicts.")
    sys.exit(0)
