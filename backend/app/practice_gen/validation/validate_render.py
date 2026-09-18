"""
§9/§12 — payload schema plus consumed browserless React render evidence.

Why this exists
---------------
All eight of run_all's stages stop at `FormattedProblem`. They validate the pipeline's
data -- the answer key survives formatting, the vocabulary is in-grade, the visual payload
is arithmetically sane. None asks whether the React component can render what it is
handed. A `visual_params` key the component reads collapses to `undefined`/`0`/`false`,
and the pupil sees an empty or wrong picture while every stage reports PASS.

Measured on the student path, 2026-08-28, three seeds per node:

    FractionModel  missing ['total_wholes']                    x7   (Bug #57)
    Calendar       missing ['month','year']        params: {}  x3
    BarChart       missing ['categories']          params: {}  x3
    ClockSet       missing ['hours','minutes',...] params: {}  x3

Three of those four render from a COMPLETELY EMPTY payload.

Why this checks the student path rather than driving the auditor
----------------------------------------------------------------
`tests/frontend_contract_auditor.py` owns the contract knowledge (REQUIRED_KEYS) and is
reused here, but it is not a usable gate as it stands:

  * its worker pool does not finish on the full tree -- >25 min without completing,
    while `--no-parallel` takes ~11 min, and killing it strands `multiprocessing.spawn`
    orphans that slow everything afterwards (the tree's own "Trap 3");
  * it samples by pinning each advertised formatter, so it never exercises the auto-select
    path students actually get. It reported `mat_g1_dp_q3_0` CLEAN while that node serves
    a BarChart with an empty payload to every student who lands on it.

Driving the student path directly is faster, deterministic, and measures the thing that
matters. The auditor remains valuable as a deeper sweep across pinned formatters.

Floors, not a hard zero
-----------------------
The baseline is red, and Scaling Mandate §5 is explicit that a check whose baseline is
already red cannot be told from the noise it sits in. The floor may only SHRINK; lowering
it to make a run pass is the move it exists to catch.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[4]

# §8 inventory: the assertions this module can independently fail on. Each must be
# proven by a mutation naming it in `Mutation.asserts`, or excused in
# validate_coverage.UNPROVEN_ASSERTIONS with a reason and a date.
#
# The two modes are separate assertions on purpose. This module's own history is the
# argument: with RENDER_FLOOR at 16 the floor path let 7 planted broken payloads through
# while the subset path would have caught them instantly. A floor that swallows a
# mutation is a check that cannot be proven, so the floor path is proven separately.
ASSERTIONS = (
    "render_contract_9",        # subset mode (--node-ids): any finding fails
    "render_contract_floor_9",  # full tree measured against RENDER_FLOOR
    "frontend_artifact_fresh_12",  # static-render evidence binds current inputs
    "frontend_static_render_12",   # every recorded component execution succeeded
    "rendered_visual_description_12",  # descriptions derive from emitted markup
    "frontend_answer_roundtrip_13",  # component emission matches backend key by value
    "renderer_registration_disposition_12",  # every unreachable registration is dispositioned
)


# Every renderer registration the practice obligation graph cannot reach must say WHY, in
# one of exactly two classes. The shape is §8's `silent_path_disposition_8`: an unreachable
# registration is not itself a defect, but an UNEXPLAINED one is, because "the suite covers
# 15 of 20" reads identically whether the other five are retired names or live components
# nothing renders.
#
#   dead-route             nothing emits this visual type on ANY surface. Retired name.
#   non-practice-reachable not reachable from the practice obligation graph, but LIVE on
#                          another student-facing surface, so the component is not dead
#                          and deleting it would break that surface.
#
# Measured 2026-09-18 by execution, not by reading (see the H-08 evidence entry):
# `generate_intro_content` over all 24 intro nodes at seeds 7/21/42, 0 errors, counting
# every `visual_type` reachable from the live `/api/matatag/intro/{node_key}` route.
_DISPOSITION_CLASSES = ("dead-route", "non-practice-reachable")

UNREACHABLE_REGISTRATION_DISPOSITIONS: Dict[str, str] = {
    "BalanceScale": (
        "non-practice-reachable -- 2026-09-18: fmt_balance_scale emits it, but §11 floors "
        "`balance_scale` as an unreachable route (advertised on missing_number nodes, which "
        "refuse every variant it offers). LIVE on the intro surface: 15 payloads on 1 intro "
        "node, rendered by its own `vt === 'BalanceScale'` branch in App.jsx. Not dead."
    ),
    "TenFrame": (
        "non-practice-reachable -- 2026-09-18: fmt_ten_frame emits it, but §11 floors "
        "`ten_frame` as an unreachable route. LIVE on the intro surface: 18 payloads on 1 "
        "intro node, rendered by its own `vt === 'TenFrame'` branch in App.jsx. Not dead."
    ),
    "Categorize": (
        "dead-route -- 2026-09-18: no formatter emits visual_type 'Categorize'; it was "
        "refactored into fmt_shape_board (ShapeBoard). Absent from intro content at every "
        "node and seed measured, and App.jsx has no branch for it. Retired name."
    ),
    "RuleDiscovery": (
        "dead-route -- 2026-09-18: no formatter emits visual_type 'RuleDiscovery'; it was "
        "refactored into fmt_pattern_sequence (PatternSequence) and fmt_fill_in_table. "
        "Absent from intro content, and App.jsx has no branch for it. Retired name."
    ),
    "SortOrder": (
        "dead-route -- 2026-09-18: no formatter emits visual_type 'SortOrder'; ordering "
        "became the TEXTUAL fmt_ordering, which produces no visual payload. Absent from "
        "intro content, and App.jsx has no branch for it. NOTE: comparing_ordering still "
        "declares visual_home='SortOrder', but base_generator reads visual_home only when "
        "dna_type=='visual_read' and that DNA is 'algorithmic', so the declaration is a "
        "measured no-op (visual_type=None on every generated problem). Retired name."
    ),
}

# ZERO, as of 2026-09-08. The floor is gone, not shrunk.
#
# It stood at 16 and was doing real harm. Of those 16:
#   * 7 were genuine -- fmt_fraction_model.py had lost its `total_wholes` assignment
#     (the comment above it ended mid-sentence). Fixed.
#   * 9 were this check's own false positives -- it selected on `visual_type`, the
#     node's visual CATEGORY, and so demanded Calendar/BarChart/ClockSet payloads from
#     plain-text questions. Both renderers ask whether a payload EXISTS
#     (QuestionRenderer.jsx:44 gates on is_visual), so no student ever saw those.
#     Applicability now matches the renderer.
#
# Why it must be zero and not 7-shrunk-to-0-later: with the floor at 16, the
# `visual_payload_drops_required_key` mutation SURVIVED -- 7 planted broken payloads
# still exited 0, so §9 could not be proven at all. A floor above the real defect count
# does not merely tolerate defects, it makes the check unprovable, which is strictly
# worse than the defects it was tracking.
RENDER_FLOOR = 0

SEEDS_PER_NODE = (11, 42, 64)
STATIC_RENDER_ARTIFACT = (
    REPO_ROOT / "validation_reports" / "phase2_hardening"
    / "frontend_static_render.json"
)


def validate_static_render_artifact() -> bool:
    """Consume, but never regenerate, the digest-bound React render result.

    The artifact is produced explicitly by ``tests/frontend_suite.py``.  This consumer
    verifies current-input freshness, execution totals, registry identity, and that each
    description identifies itself as parsed from rendered markup.

    Named limits: jsdom has no layout engine, so NumberLine and BarChart pointer-drag
    geometry remains unproven. Static markup cannot establish crowding, overlap, colour
    contrast, or real touch-target size. Five current renderUtils registrations are not
    reachable from a practice student-path obligation; the artifact names them and this
    check does not misreport them as covered.
    """
    from backend.app.practice_gen.validation.mutation_proof import input_digest

    errors: List[str] = []
    if not STATIC_RENDER_ARTIFACT.exists():
        errors.append(
            f"missing {STATIC_RENDER_ARTIFACT.relative_to(REPO_ROOT)}; build it with "
            "PYTHONPATH=. .venv/bin/python tests/frontend_suite.py"
        )
        artifact: Dict[str, Any] = {}
    else:
        try:
            import json

            artifact = json.loads(STATIC_RENDER_ARTIFACT.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"static-render artifact is unreadable: {exc}")
            artifact = {}

    current_digest = input_digest()
    recorded_digest = artifact.get("source_input_digest")
    if recorded_digest != current_digest:
        errors.append(
            "frontend render evidence is stale: source input digest is "
            f"{str(recorded_digest)[:12] or 'missing'}, current is {current_digest[:12]}. "
            "Re-run PYTHONPATH=. .venv/bin/python tests/frontend_suite.py"
        )

    outcomes = artifact.get("outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        errors.append("frontend artifact records no executed component cases")
        outcomes = []
    if artifact.get("renders_executed") != len(outcomes) or len(outcomes) != 2 * artifact.get("cases_executed", 0):
        errors.append(
            f"frontend artifact claims {artifact.get('cases_executed')} cases / "
            f"{artifact.get('renders_executed')} renders but carries {len(outcomes)} outcomes"
        )

    current_registered = sorted(_required_keys())
    if artifact.get("registered_visual_types") != current_registered:
        errors.append(
            "frontend artifact's renderer registry does not equal the current AST-derived "
            f"registry ({artifact.get('registered_visual_types')} != {current_registered})"
        )

    covered = sorted({row.get("visual_type") for row in outcomes if row.get("visual_type")})
    if covered != artifact.get("production_visual_types"):
        errors.append(
            "frontend artifact component coverage does not equal its declared production "
            f"visual types ({covered} != {artifact.get('production_visual_types')})"
        )
    case_modes: Dict[str, set[str]] = {}
    case_metadata: Dict[str, tuple[Any, Any]] = {}
    for row in outcomes:
        case_id = row.get("case_id")
        seed = row.get("seed")
        mode = row.get("mode")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"frontend outcome has invalid case_id={case_id!r}")
        else:
            case_modes.setdefault(case_id, set()).add(mode)
            metadata = (row.get("interaction_mode"), row.get("answer_collection"))
            if case_id in case_metadata and case_metadata[case_id] != metadata:
                errors.append(f"{case_id}: active/disabled interaction metadata disagrees")
            case_metadata[case_id] = metadata
        desc = row.get("description") or {}
        if mode not in {"active", "disabled"}:
            errors.append(f"{row.get('case_id')} seed {seed}: invalid render mode {mode!r}")
        if desc.get("source") != "rendered_static_markup":
            errors.append(
                f"{row.get('case_id')} seed {seed}: {mode} visual description is not "
                "identified as render-derived"
            )
        if not isinstance(desc.get("element_count"), int) or desc.get("element_count", 0) <= 2:
            errors.append(
                f"{row.get('case_id')} seed {seed}: {mode} render is degenerate "
                f"(element_count={desc.get('element_count')!r})"
            )
    expected_modes = {"active", "disabled"}
    invalid_modes = {
        case_id: sorted(modes)
        for case_id, modes in case_modes.items()
        if modes != expected_modes
    }
    if len(case_modes) != artifact.get("cases_executed", 0) or invalid_modes:
        errors.append(
            "frontend artifact does not carry exactly one active and one disabled render "
            f"per case (cases={len(case_modes)}, invalid={invalid_modes})"
        )

    from backend.app.services.scoring import answers_match

    roundtrips = artifact.get("answer_roundtrips")
    if not isinstance(roundtrips, list) or not roundtrips:
        errors.append("frontend artifact records no onAnswer round trips")
        roundtrips = []
    expected_roundtrip_ids = sorted(
        case_id for case_id, (interaction_mode, answer_collection) in case_metadata.items()
        if interaction_mode == "set" or answer_collection != "mcq"
    )
    actual_roundtrip_ids = sorted(
        row.get("case_id") for row in roundtrips if isinstance(row, dict)
    )
    if (len(actual_roundtrip_ids) != len(set(actual_roundtrip_ids))
            or actual_roundtrip_ids != expected_roundtrip_ids):
        errors.append(
            "frontend answer-roundtrip coverage disagrees with rendered interactive cases: "
            f"recorded={actual_roundtrip_ids}, expected={expected_roundtrip_ids}"
        )
    for row in roundtrips:
        if not answers_match(row.get("emitted_answer"), row.get("correct_answer")):
            errors.append(
                f"{row.get('case_id')} seed {row.get('seed')}: component emitted "
                f"{row.get('emitted_answer')!r}, keyed {row.get('correct_answer')!r}"
            )

    # ── renderer_registration_disposition_12 ──────────────────────────────────
    # Two directions, because each catches a different way the record rots.
    unreachable_now = sorted(artifact.get("unreachable_renderer_registrations") or [])
    disposition_errors: List[str] = []
    for name in unreachable_now:
        text = UNREACHABLE_REGISTRATION_DISPOSITIONS.get(name)
        if not text:
            disposition_errors.append(
                f"renderer registration {name!r} is unreachable from the practice obligation "
                f"graph and carries NO disposition. An unexplained gap reads exactly like a "
                f"covered one. Add an entry to UNREACHABLE_REGISTRATION_DISPOSITIONS naming "
                f"it {' or '.join(_DISPOSITION_CLASSES)}, with the evidence and a date."
            )
        elif not text.startswith(_DISPOSITION_CLASSES):
            disposition_errors.append(
                f"renderer registration {name!r} has a disposition that does not start with "
                f"one of {list(_DISPOSITION_CLASSES)}: {text[:60]!r}. The class is what makes "
                f"the record machine-readable; free prose is how a dead route hides."
            )
    # A disposition for something that is no longer unreachable is stale bookkeeping: either
    # the registration became reachable (delete the entry, it is now covered) or it was
    # removed (delete the entry, it names nothing). Same direction as §8's allowlist checks.
    for name in sorted(set(UNREACHABLE_REGISTRATION_DISPOSITIONS) - set(unreachable_now)):
        disposition_errors.append(
            f"UNREACHABLE_REGISTRATION_DISPOSITIONS names {name!r}, which is NOT currently an "
            f"unreachable registration. Either it is now reached by the practice obligation "
            f"graph, or the registration is gone. Delete the entry -- a disposition that "
            f"excuses nothing reads as accounted-for coverage."
        )
    errors.extend(disposition_errors)

    if errors:
        print(f"  FAIL frontend_static_render_12: {len(errors)} artifact finding(s)")
        for error in errors[:10]:
            print(f"    - {error}")
        return False

    print(
        f"  PASS frontend_artifact_fresh_12: digest {current_digest[:12]}; "
        f"{artifact.get('cases_executed')} real student-path payload(s)"
    )
    print(
        f"  PASS frontend_static_render_12: {len(covered)} production visual type(s) "
        "executed active and disabled"
    )
    print(
        f"  PASS rendered_visual_description_12: {len(outcomes)} descriptions "
        "parsed from rendered markup"
    )
    print(
        f"  PASS frontend_answer_roundtrip_13: {len(roundtrips)} correct UI interactions "
        "emitted values accepted by answers_match"
    )
    by_class: Dict[str, List[str]] = {}
    for name in unreachable_now:
        cls = UNREACHABLE_REGISTRATION_DISPOSITIONS[name].split(" --", 1)[0]
        by_class.setdefault(cls, []).append(name)
    print(
        f"  PASS renderer_registration_disposition_12: all {len(unreachable_now)} unreachable "
        f"registration(s) dispositioned ("
        + "; ".join(f"{cls}: {', '.join(names)}" for cls, names in sorted(by_class.items()))
        + ")"
    )
    if unreachable_now:
        print("    NOT COVERED — unreachable renderer registrations: " + ", ".join(unreachable_now))
    print("    BLIND SPOT — NumberLine/BarChart pointer-drag geometry (jsdom has no layout)")
    return True


def _required_keys() -> Dict[str, List[str]]:
    """
    The contract itself lives with the auditor; reuse it rather than restating it.

    Since 2026-09-11 the auditor DERIVES it from the component AST rather than carrying
    a hand-written map, so §9 now inherits a contract that cannot go stale. The previous
    map had drifted 35 keys away from the components it claimed to mirror, which means
    §9 was checking a contract nobody had reconciled with the source in a long while.

    A required GROUP (`a ?? b ?? c` -- supply at least one) cannot be expressed as a flat
    required-key list, so §9 checks the unconditional keys only and the auditor checks
    both. Named rather than glossed: §9 is the weaker of the two on this axis.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from tests.frontend_contract_auditor import visual_contract

    return {vt: spec["required"] for vt, spec in visual_contract().items()}


def collect_findings(node_ids: Optional[List[str]] = None) -> List[str]:
    """Every (node, seed) whose visual payload omits a key the component reads."""
    sys.path.insert(0, str(REPO_ROOT))
    from backend.app.practice_gen.registry import get_all_node_ids
    from backend.app.services.orchestrator import PracticeOrchestrator

    required = _required_keys()
    findings: List[str] = []
    for node_id in (node_ids or get_all_node_ids()):
        for seed in SEEDS_PER_NODE:
            try:
                p = PracticeOrchestrator.generate_problem(
                    node_id=node_id, seed=seed, is_student_path=True
                )
            except Exception:
                # DISPOSITION: checked -- §1C/§1C-coverage own generation failures and
                # sweep far more seeds than §9's three, so a node that cannot generate
                # fails there. RESIDUAL: a failure unique to one of §9's three seeds is
                # invisible here, because §9 only checks what it managed to render.
                continue  # a generation failure is another stage's finding, not §9's
            d = p if isinstance(p, dict) else p.__dict__
            vt = d.get("visual_type")
            # Applicability follows the RENDERER, not the node's category label.
            #
            # This used to select on `visual_type` alone, which is the visual family the
            # NODE belongs to -- inherited from the registry and present even when a
            # given problem is plain text. A Calendar node serving "What month comes
            # after August?" as cloze has visual_type='Calendar', visual_params=None,
            # and was reported as a broken Calendar payload. Nine such findings across
            # three nodes; no student ever saw a broken visual, because BOTH renderers
            # ask whether a picture exists:
            #     QuestionRenderer.jsx:44   {question.is_visual ? <visual/> : <text/>}
            #     App.jsx:1403              {visual_type && visual_params && ...}
            # This check re-derived that condition and got it wrong -- the same
            # duplicated-rule divergence it exists to catch elsewhere.
            #
            # `is_visual` is safe to trust as of the FormattedProblem invariant that
            # derives it from visual_params (tests/unit/test_is_visual_invariant.py);
            # before that, one formatter set it from visual_type and it could lie.
            # A genuinely visual problem missing a key is still caught -- see the
            # FractionModel/total_wholes findings this same run reported and fixed.
            if not d.get("is_visual"):
                continue
            if not vt or vt not in required:
                continue
            params = d.get("visual_params")
            if not isinstance(params, dict):
                params = {}
            missing = [k for k in required[vt] if k not in params]
            if missing:
                findings.append(
                    f"{node_id} (seed {seed}): {vt} payload omits {missing}, which the "
                    f"React component reads. It collapses to undefined/0/false and the "
                    f"student sees a broken or empty visual. Payload has: "
                    f"{sorted(params)[:6] or 'NOTHING'}"
                )
    return findings


def validate_all(node_ids: Optional[List[str]] = None, *, artifact_only: bool = False) -> bool:
    """
    Full tree: compare against the floor.
    Subset (`node_ids`): require ZERO findings, so §9 is mutation-provable in seconds.
    """
    if artifact_only:
        return validate_static_render_artifact()

    findings = collect_findings(node_ids)

    if node_ids:
        if findings:
            print(f"  FAIL render_contract_9: {len(findings)} finding(s) on {node_ids}")
            for f in findings[:8]:
                print(f"    - {f}")
            return False
        print(f"  PASS render_contract_9: 0 findings on {len(node_ids)} node(s)")
        return True

    if len(findings) > RENDER_FLOOR:
        print(f"  FAIL render_contract_floor_9: {len(findings)} broken renders exceeds "
              f"floor {RENDER_FLOOR}")
        for f in findings[:10]:
            print(f"    - {f}")
        return False
    print(f"  PASS render_contract_floor_9: {len(findings)} broken renders (floor {RENDER_FLOOR})")
    if findings:
        print(f"    {len(findings)} payloads the student cannot render remain — content work:")
        for f in findings[:4]:
            print(f"      - {f[:110]}")
    return validate_static_render_artifact()


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§9 render contract")
    ap.add_argument("--node-ids", help="comma-separated subset; any finding fails")
    ap.add_argument("--artifact-only", action="store_true",
                    help="consume the §12 static-render artifact without generating §9 samples")
    args = ap.parse_args()
    nodes = [n.strip() for n in args.node_ids.split(",")] if args.node_ids else None
    return 0 if validate_all(nodes, artifact_only=args.artifact_only) else 1


if __name__ == "__main__":
    sys.exit(main())
