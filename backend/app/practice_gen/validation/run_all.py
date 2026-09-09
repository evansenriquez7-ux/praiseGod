"""
Practice Generation — Validation Harness Runner

Runs the validators in the practice problem generation pipeline, in two bands.

PHASE 1 -- artifact-free. Runnable on a fresh clone by an agent that has authored
nothing. This is the fix-until-green loop:
  §0    pytest tests/unit (the harness's own tests — fast suite, slow deselected)
  §3    validate_dna (structure, feasibility, distractors)
  §2*   validate_compat (registry, coverage, monotonicity, reachability, producibility)
        validate_interest (interest invariance)
        validate_vocab (vocabulary gating and concept constraints, full-node mode)
  §1*/§4 validate_matrix (exhaustive behavioural matrix)
  §6A-E validate_capability_provision (declared, cited, covered, provided)
  §9    validate_render      §10 validate_grade      §8 validate_coverage
  §7    validate_census

PHASE 2 -- needs an agent-authored artifact on disk before it can run at all:
  §5    validate_judgment  (validation_reports/judgment/)
  §6F-H validate_capability_attestation (validation_reports/attestation/)

The seam is artifact-dependence, not "does it need an LLM" -- every check here is
programmatic; the LLM only ever PRODUCES the artifact. Phase 2 is gated on Phase 1
being green, because a review or attestation is a judgment about specific rendered
seeds and any Phase 1 fix that changes generation invalidates it.

`--phase 1` / `--phase 2` runs one band and exits on that band alone. The phase of each
§-ref lives in `_manifest.CHECK_PHASE` -- one registry, read here and by
validate_capability, held complete by §8's `check_phase_registry_8` -- and is reconciled
against the phase it actually ran in by the Two-Direction block below.

Exit code is 0 if and only if every check in scope passes.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Set

from backend.app.practice_gen.validation import (
    validate_compat,
    validate_dna,
    validate_interest,
    validate_capability,
    validate_judgment,
    validate_matrix,
    validate_census,
    validate_render,
    validate_grade,
    validate_coverage,
    validate_vocab,
)
from backend.app.practice_gen.validation.validate_matrix import run_matrix_validation
from backend.app.practice_gen.validation._manifest import CHECK_PHASE, refs_in_phase

_PGEN_CONTRACT_PATH = Path(__file__).resolve().parents[4] / "docs" / "pgen_contract.md"

# §8 inventory: the assertions the RUNNER owns, as opposed to the ones it re-reports for
# the modules it drives. Each must be proven by a mutation naming it in
# `Mutation.asserts`, or excused in validate_coverage.UNPROVEN_ASSERTIONS.
ASSERTIONS = (
    "unit_tests",                          # §0: the fast suite passes
    # §0 is 399 tests and §8 does not inventory them one by one; §7's unit_tests floor
    # guards their number. A test a mutation names individually is inventoried here.
    "subtraction_candidate_pool_bounded",  # tests/unit/test_subtraction_candidate_pool.py
    "contract_doc_matches_registry",
    "operator_doc_covers_registry",
    "two_direction_contract_match",
)


def _parse_contract_section_refs() -> Set[str]:
    """
    Extract every '§1A'-style reference from docs/pgen_contract.md's rule
    table (R4/§3.5 doc_rem.md: the doc is the single source of truth for
    which checks are binding — a contract row pointing at a check this
    module doesn't know how to execute must fail CI, not drift silently).
    """
    if not _PGEN_CONTRACT_PATH.exists():
        raise FileNotFoundError(
            f"pgen_contract.md not found at '{_PGEN_CONTRACT_PATH}' — cannot verify "
            f"the contract table's checks are all implemented."
        )
    text = _PGEN_CONTRACT_PATH.read_text(encoding="utf-8")
    return set(re.findall(r"§[\w-]+", text))


# Single source of truth mapping contract sections to validation checkers.
# Keys are cross-checked against docs/pgen_contract.md's own §-refs below —
# a row in the doc naming a §-ref not in this dict (or vice versa) is a
# doc/harness drift and fails run_all (see the Two-Direction check).
CONTRACT_CHECKS: Dict[str, str] = {
    "§0": "pytest tests/unit: the harness's own unit tests pass (slow suite deselected)",
    "§1A": "validate_matrix: boundary exactness (0.0/1.0)",
    "§1B": "validate_matrix: containment sweep (monotonicity and window bounds)",
    "§1A-reach": "validate_matrix: scalar 1.0 reaches the competency maximum region",
    "§1C": "validate_matrix: execution matrix (variant x formatter combinations)",
    "§1C-reverse": "validate_matrix: reverse check (excluded combinations raise clear errors)",
    "§1C-coverage": "validate_matrix: every node/DNA/formatter has a non-empty execution matrix",
    "§1D": "validate_matrix: vocabulary/concept lint on final formatted output",
    "§1E": "validate_matrix: answer-key & interest theme invariance on formatted output",
    "§1F": "validate_matrix: question stem does not leak its own answer",
    "§1G": "validate_matrix: rendered visual payload is real and self-consistent",
    "§1H": "validate_matrix: every check a node's composition makes applicable actually ran on that node",
    "§1I": "validate_matrix: a true/false item family may not key every sample the same way",
    "§2": "validate_compat: registry/compatibility coverage & monotonicity",
    "§2B": "validate_compat: every formatter a node advertises can actually be served for it",
    "§2D": "validate_compat: a saved configuration may not serve content outside a node's competency",
    "§2E": "validate_compat: the correct option's position must not be predictable from the seed",
    "§2C": "validate_compat: a formatter a node advertises must be reachable by the student path, not merely servable when pinned",
    "§2F": "validate_compat: every node id referenced in the app must exist in the registry",
    "§2G": "validate_compat: every node's competency bounds parse to a well-formed shape — the tree-wide property behind the fixture table",
    "§2I": "validate_compat: a discrete variant a node DECLARES must be one it can actually produce — a shrinking floor; the silent packet skip that hid 65 of these is now recorded",
    "§2H": "validate_compat: a competency naming BOTH cases of a dimension must not be bound to one of them — §2G proves bounds are well-formed, this proves they are faithful",
    "§3": "validate_dna: structural checks and difficulty profiles feasibility",
    "§4": "validate_matrix: VISUAL payload schema validation (recorded only under is_visual, so ~67 of 151 nodes; non-visual response shape rests on the Pydantic model at runtime)",
    "§5": "validate_judgment PHASE 2 (whole): genuine, non-boilerplate, non-stale blind judgment reviews",
    "§6": "validate_capability PHASE 1: competency requirements declared, cited, covered, and provided — artifact-free, runs with validation_reports/attestation/ absent",
    "§6D": "validate_capability PHASE 1: a capability carried only by a generic textual formatter is not provided",
    "§6E": "validate_capability PHASE 1: a capability carried only by a `bounds` list most of the table shares is not provided",
    "§6F": "validate_capability PHASE 2: every declared capability carries a blind Attester verdict, and none is contradicted",
    "§6G": "validate_capability PHASE 2: an attestation shows its work — non-boilerplate reasoning citing seeds from its own packet",
    "§6H": "validate_capability PHASE 2: an Attester verdict must name who made it, and no identity may cover more than one dispatch",
    "§7": "run_all: the suite's own census (nodes, unit tests, mutations) has not shrunk below its floor",
    "§8": "validate_coverage: every assertion the harness can emit is either proven by a mutation or on a shrinking allowlist",
    "§9": "validate_render: the payload a node emits must be renderable by the React component the student sees",
    "§10": "validate_grade: a known-correct answer must be graded correct by all three graders",
}

_LAST_UNIT_TEST_COUNT: list = [None]


def _run_unit_tests() -> bool:
    """
    Run the fast unit suite and report it as a harness stage (§0).

    Subprocess rather than in-process pytest: the validators are already imported here
    with module-level state (CAPABILITY_PROVIDERS is mutated by several mutation tests),
    and pytest collecting into this same interpreter would let a test's monkeypatching
    leak into the stages that run afterwards. A clean interpreter is the only honest way
    to run tests that plant mutations in the modules this harness is about to use.
    """
    import subprocess

    repo_root = Path(__file__).resolve().parents[4]
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit", "-q", "-p", "no:cacheprovider"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(repo_root)},
    )
    tail = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()]
    summary = tail[-1] if tail else "(no output)"
    # "343 passed, 1 skipped, 2 deselected, 1 warning in 202.98s" -> 343. Recorded so §7
    # can assert the suite did not silently shrink; a test that stops running stops gating.
    m = re.search(r"(\d+) passed", summary)
    _LAST_UNIT_TEST_COUNT[0] = int(m.group(1)) if m else None
    if proc.returncode == 0:
        print(f"  PASS unit_tests ({summary})")
        return True
    print(f"  FAIL unit_tests ({summary}):")
    for line in proc.stdout.splitlines():
        if line.startswith("FAILED") or line.startswith("ERROR"):
            print(f"    - {line}")
    return False


def run_all(fail_fast: bool = False, phase: Optional[int] = None) -> int:
    """
    Run the harness. `phase=1` runs only the artifact-free band, `phase=2` only the band
    that needs an agent-authored artifact, `None` runs everything.

    --phase 1 exists because "Phase 1 is done" was not a claim this runner could make.
    The seam was decided per-ref for §6 on 2026-09-08 but 28 of the 35 refs carried no
    phase at all, so asserting Phase 1 meant running ten commands by hand and reading
    them -- which the Definition of Done exists to forbid. The band each stage belongs to
    is read from `_manifest.CHECK_PHASE`, never restated here.
    """
    if phase not in (None, 1, 2):
        raise ValueError(f"phase must be 1, 2 or None; got {phase!r}")
    banner = ("RUNNING ALL PRACTICE PROBLEM GENERATION VALIDATORS" if phase is None
              else f"RUNNING PHASE {phase} VALIDATORS "
                   f"({'artifact-free' if phase == 1 else 'needs an agent-authored artifact'})")
    print("======================================================================")
    print(banner)
    print("======================================================================\n")

    def _runs(p: int) -> bool:
        """True if the band `p` is in scope for this run."""
        return phase is None or phase == p

    executed_checks: Set[str] = set()
    # Which PHASE each executed §-ref actually ran in, against which
    # validate_capability.CHECK_PHASE is reconciled below. Recorded rather than
    # assumed, for the same reason validate_matrix records LAST_EXECUTED_CHECKS: a
    # check that silently changes band is a check whose cost moved without anyone
    # deciding to move it.
    executed_phase: Dict[str, int] = {}

    def _phase_refs(phase: int) -> Set[str]:
        """The §6 refs registered to `phase` that this runner also contracts for.

        `CHECK_PHASE` also phases §6A/§6B/§6C, which findings cite but CONTRACT_CHECKS
        does not register as separate rows; intersecting keeps the two-direction check
        comparing like with like instead of reporting three permanent phantoms.
        """
        return {ref for ref, p in CHECK_PHASE.items()
                if p == phase and ref in CONTRACT_CHECKS}

    def _record_phase(phase: int) -> None:
        for ref in _phase_refs(phase):
            executed_checks.add(ref)
            executed_phase[ref] = phase

    # 1. Unit tests (§0) — the harness's own tests.
    #
    # run_all did not run pytest until 2026-08-20, and the cost of that blind spot is
    # measured: two capability-gate tests sat red on HEAD for an unknown number of ticks
    # (one of them guarding the very freshness machinery §6F depends on), and a reroute
    # in an earlier tick broke three orchestrator tests that stayed red for three more
    # ticks while every tick report said the tree was clean. Green stages over red tests
    # is exactly the "green is not evidence" failure this harness exists to prevent.
    #
    # Deselects `slow` (tests/pytest.ini does this by default): the two slow tests spawn
    # process pools and take 15-40 minutes each, which is what made a plain pytest run
    # look like a deadlock for five ticks. The fast suite is ~35s, so it runs FIRST --
    # there is no sense spending 40 minutes on the matrix when the harness's own tests
    # are broken.
    if _runs(1):
        print("--- Unit Tests (the harness's own tests) ---")
        unit_ok = _run_unit_tests()
        if unit_ok:
            executed_checks.add("§0")
        if not unit_ok and fail_fast:
            return 1
    else:
        unit_ok = True

    if _runs(1):
        print("\n--- DNA Structural and Parameter Checks ---")
        dna_results = validate_dna.validate_all_dnas()
        dna_failed = [c for c, errs in dna_results.items() if any(not e.startswith("WARN") for e in errs)]

        feasibility_results = validate_dna.run_all_feasibility_checks()
        feasibility_failed = [c for c, errs in feasibility_results.items() if errs]

        dna_ok = len(dna_failed) == 0 and len(feasibility_failed) == 0
        if dna_ok:
            executed_checks.add("§3")
        elif fail_fast:
            print("  ABORT after DNA validation (fail-fast active)")
            return 1
    else:
        dna_ok = True

    # 2. Compatibility
    if _runs(1):
        print("\n--- Compatibility, Coverage & Monotonicity ---")
        compat_ok = validate_compat.validate_all()
        if compat_ok:
            executed_checks.add("§2")
            executed_checks.add("§2B")
            executed_checks.add("§2D")
            executed_checks.add("§2E")
            executed_checks.add("§2C")
            executed_checks.add("§2F")
            executed_checks.add("§2G")
            executed_checks.add("§2H")
            executed_checks.add("§2I")
        elif fail_fast:
            print("  ABORT after compatibility validation (fail-fast active)")
            return 1
    else:
        compat_ok = True

    # 3. Interest Invariance
    if _runs(1):
        print("\n--- Interest Invariance Checks ---")
        interest_results = validate_interest.validate_all_interest_invariance()
        interest_failed = [c for c, errs in interest_results.items() if errs]
        interest_ok = len(interest_failed) == 0
        if not interest_ok and fail_fast:
            print("  ABORT after interest invariance (fail-fast active)")
            return 1
    else:
        interest_ok = True

    # 4. Vocabulary & Concept Gating (Full-Node Mode)
    if _runs(1):
        print("\n--- Vocabulary & Concept Gating Audits (Full-Node Mode) ---")
        vocab_results = validate_vocab.run_all_vocab_audits(sample_count=2)
        vocab_failed = []
        for nid, audit in vocab_results.items():
            if audit["pass_rate"] < 1.0:
                vocab_failed.append((nid, audit["violations"]))
        vocab_ok = len(vocab_failed) == 0
        if not vocab_ok:
            print(f"  FAIL vocab_audit_pass_rate ({len(vocab_failed)} node(s) below 1.00):")
            for nid, violations in vocab_failed[:5]:  # print first 5 to avoid flood
                print(f"    - {nid}: {violations}")
            if len(vocab_failed) > 5:
                print(f"    ... and {len(vocab_failed) - 5} more nodes.")
            if fail_fast:
                return 1
        else:
            print("  PASS vocabulary gating audit (all nodes)")
    else:
        vocab_ok = True

    # 5. Exhaustive Behavioral Matrix
    if _runs(1):
        print("\n--- Exhaustive Behavioral Matrix Validation ---")
        # Run matrix validator. We set workers=0 for auto-detection.
        matrix_code = run_matrix_validation(fail_fast=fail_fast, workers=0)
        matrix_ok = matrix_code == 0
        # The matrix's §-refs are *observed*, not assumed: validate_matrix records an
        # id at each check site when that site actually evaluates an assertion.
        executed_checks |= validate_matrix.LAST_EXECUTED_CHECKS

        # §1H — per-node applicability. The union above proves each check ran SOMEWHERE;
        # this proves each ran on every node whose own composition demands it. Without it a
        # check can quietly stop reaching 150 of 151 nodes and the suite still reports green.
        applicability_errors = validate_matrix.applicability_failures(
            validate_matrix._EXECUTED_BY_NODE
        )
        # §1E, §4 and §1I depend on what a seed happens to produce, so applicability cannot
        # predict them and a node that silently stops exercising one is invisible. Comparison
        # against the last recorded run can see it.
        applicability_errors += validate_matrix.coverage_regressions(
            validate_matrix._EXECUTED_BY_NODE
        )
        executed_checks.add("§1H")
        if applicability_errors:
            matrix_ok = False
            print(f"  FAIL per_node_applicability_1H (§1H applicability, {len(applicability_errors)} node(s)):")
            for e in applicability_errors[:10]:
                print(f"    - {e}")
            if len(applicability_errors) > 10:
                print(f"    ... and {len(applicability_errors) - 10} more.")
        else:
            print(f"  PASS §1H applicability (all {len(validate_matrix._EXECUTED_BY_NODE)} "
                  f"nodes ran every check their composition makes applicable)")

        if not matrix_ok and fail_fast:
            print("  ABORT after matrix validation (fail-fast active)")
            return 1
    else:
        matrix_ok = True

    # 6. Judgment Reviews (genuine, non-boilerplate — hard gate)
    if _runs(2):
        print("\n--- Judgment Reviews (genuine per-node artifacts) ---")
        judgment_errors = validate_judgment.validate_judgment_reviews(fail_fast=fail_fast)
        v = validate_judgment.summarize_verdicts()
        if v["FAIL"] > 0 or v["CONCERN"] > 0:
            judgment_errors.append(
                f"Unresolved judgment verdicts remain across {v['reviewed']} nodes: "
                f"PASS={v['PASS']} CONCERN={v['CONCERN']} FAIL={v['FAIL']}; "
                f"all nodes must reach PASS verdict."
            )
        judgment_ok = len(judgment_errors) == 0
        if judgment_ok:
            executed_checks.add("§5")
            print(
                f"  PASS judgment_reviews (all {v['reviewed']} nodes have genuine, fresh, PASS reviews: "
                f"PASS={v['PASS']} CONCERN={v['CONCERN']} FAIL={v['FAIL']})"
            )
        else:
            print(f"  FAIL judgment_reviews ({len(judgment_errors)} problem(s) — non-PASS verdicts or incomplete reviews):")
            for err in judgment_errors[:10]:
                print(f"    - {err}")
            if len(judgment_errors) > 10:
                print(f"    ... and {len(judgment_errors) - 10} more.")
            if fail_fast:
                return 1
    else:
        judgment_ok = True

    # 7. Capability Contract (§6) — in its two phases.
    #
    # The seam is NOT "does this check need an LLM": every §6 check is programmatic,
    # and the LLM's only job is to PRODUCE an attestation, never to validate one. The
    # seam is whether a check needs an AGENT-AUTHORED ARTIFACT to exist before it can
    # run at all. §6A–§6E do not (knowledge graph, `requires`, CAPABILITY_PROVIDERS:
    # 75 findings in 0.1s, runs with validation_reports/attestation/ absent). §6F–§6H
    # do, and freshness re-renders every attested seed: 90 findings in 9.9s.
    #
    # Until 2026-09-08 both ran on ONE boolean and added their six §-refs together, so
    # 75 findings that belong in the fix-until-green loop were filed in a ~865-finding
    # Phase-2 backlog and nothing in the harness could tell the two bands apart. The
    # phase of each ref is read from validate_capability.CHECK_PHASE rather than
    # restated here — one registry, so a second copy cannot disagree with it.
    if _runs(1):
        print("\n--- Capability Contract Phase 1 (artifact-free — §6A–§6E) ---")
        provision_errors = validate_capability.validate_capability_provision()
        provision_ok = len(provision_errors) == 0
        if provision_ok:
            _record_phase(1)
            print("  PASS capability_contract (Phase 1: all nodes declare, cite, cover, "
                  "and are provided for)")
        else:
            undeclared = [e for e in provision_errors if "no 'requires' declaration" in e]
            unprovided = [e for e in provision_errors if "no pipeline artifact provides it" in e]
            wildcarded = [e for e in provision_errors if "§6D" in e]
            print(
                f"  FAIL capability_contract (Phase 1, {len(provision_errors)} problem(s): "
                f"{len(undeclared)} node(s) undeclared, {len(unprovided)} capability(ies) "
                f"with no provider, of which {len(wildcarded)} are carried only by a "
                f"generic textual formatter (§6D)):"
            )
            for err in provision_errors[:10]:
                print(f"    - {err}")
            if len(provision_errors) > 10:
                print(f"    ... and {len(provision_errors) - 10} more.")
            if fail_fast:
                return 1
    else:
        provision_ok = True

    # PHASE 2 — gated on Phase 1 in the reorganised loop, but still RUN here so a
    # single `run_all` reports the whole contract. Skipping it when Phase 1 is red
    # would hide the attestation band behind a §6D backlog, which is the failure this
    # split exists to end, not to repeat one level down.
    if _runs(2):
        print("\n--- Capability Contract Phase 2 (attestation — §6F–§6H) ---")
        attestation_errors = validate_capability.validate_capability_attestation()
        attestation_ok = len(attestation_errors) == 0
        if attestation_ok:
            _record_phase(2)
            print("  PASS capability_contract (Phase 2: every declared capability carries "
                  "a fresh, non-boilerplate, attributed blind Attester verdict)")
        else:
            unattested = [e for e in attestation_errors if "UNATTESTED" in e]
            contradicted = [e for e in attestation_errors if "CONTRADICTED" in e]
            stale = [e for e in attestation_errors if "is STALE" in e]
            print(
                f"  FAIL capability_contract (Phase 2, {len(attestation_errors)} problem(s): "
                f"{len(contradicted)} CONTRADICTED, {len(unattested)} UNATTESTED and "
                f"{len(stale)} STALE (§6F)):"
            )
            # UNATTESTED dominates by volume while the backlog is open and would bury the
            # findings that name a defect. Show the ones that name a real problem first.
            attestation_errors = (
                [e for e in attestation_errors if "UNATTESTED" not in e] + unattested
            )
            for err in attestation_errors[:10]:
                print(f"    - {err}")
            if len(attestation_errors) > 10:
                print(f"    ... and {len(attestation_errors) - 10} more.")
            if fail_fast:
                return 1
    else:
        attestation_ok = True

    # Two-direction contract enforcement check
    # The four stages below are all Phase 1: each reads code, the knowledge graph or the
    # harness's own bookkeeping, and none needs an agent-authored artifact on disk.
    render_ok = grade_ok = coverage_ok = census_ok = True
    if _runs(1):
        print("\n--- Render Contract (§9) ---")
        # The first stage that looks past FormattedProblem at what the STUDENT receives.
        # Everything above validates the pipeline's data; this asks whether the React
        # component can render it. It was an ungated auditor until 2026-08-28 and had been
        # holding 12 critical findings across 4 nodes the whole time.
        render_ok = validate_render.validate_all()
        executed_checks.add("§9")

        print("\n--- Grading Contract (§10) ---")
        # The worst defect class in the system: a pupil does the mathematics right and is
        # told they are wrong. Three graders serve answers and can disagree about one.
        grade_ok = validate_grade.validate_all()
        executed_checks.add("§10")

        print("\n--- Assertion Coverage (§8) ---")
        # Replaces "N of M checks proven", which counted a contract REF as proven when one
        # of its sub-assertions was. validate_matrix alone emits 38 assertion labels behind
        # ~11 refs, so that number flattered the harness considerably.
        coverage_ok = validate_coverage.validate_all()
        executed_checks.add("§8")

        print("\n--- Suite Census (§7) ---")
        census_ok = validate_census.validate_all()
        executed_checks.add("§7")

    print("\n--- Two-Direction Contract Verification ---")
    try:
        # (doc_rem.md §3.5 drift tripwire) docs/pgen_contract.md is the single
        # source of truth for which §-refs are binding. A contract row naming
        # a §-ref this module doesn't implement — or an implemented check the
        # doc doesn't mention — is drift, and fails the run.
        doc_refs = _parse_contract_section_refs()
        registry_refs = set(CONTRACT_CHECKS.keys())
        if doc_refs != registry_refs:
            raise AssertionError(
                f"Drift between docs/pgen_contract.md and run_all.py's CONTRACT_CHECKS registry!\n"
                f"  In contract doc but not implemented: {doc_refs - registry_refs}\n"
                f"  Implemented but not in contract doc: {registry_refs - doc_refs}"
            )
        print("  PASS contract_doc_matches_registry")

        # The OPERATOR doc drifts the same way and had no tripwire. Measured 2026-08-28:
        # docs/testing_pipeline.md was 83 lines last touched 2026-07-31 and named 3 of the
        # 24 checks then registered, while asserting a "CI-enforced harness" that had been
        # deleted six weeks earlier. Someone deploying or operating this reads that file.
        #
        # Deliberately a FLOOR, not equality: pgen_contract.md is the binding table and
        # must match exactly, whereas testing_pipeline.md is prose that explains a subset.
        # Requiring every ref would force boilerplate; requiring a floor stops it rotting.
        operator_doc = Path(__file__).resolve().parents[4] / "docs" / "testing_pipeline.md"
        if operator_doc.exists():
            text = operator_doc.read_text(encoding="utf-8")
            named = {r for r in registry_refs if r in text}
            floor = 12
            if len(named) < floor:
                raise AssertionError(
                    f"docs/testing_pipeline.md names only {len(named)} of "
                    f"{len(registry_refs)} registered checks (floor {floor}). The operator "
                    f"documentation has fallen behind the pipeline it describes; a reader "
                    f"is being told about a harness that no longer exists. Missing: "
                    f"{sorted(registry_refs - named)[:12]}"
                )
            print(f"  PASS operator_doc_covers_registry ({len(named)}/{len(registry_refs)} refs, floor {floor})")

        # Compare the checks the contract table claims are binding against the
        # checks the harness *observed itself* running. Under --phase, only the band
        # that ran is in scope -- comparing a phase-1 run against all 35 refs would
        # report every phase-2 ref as "registered but not executed" forever, which
        # would make the drift tripwire useless in exactly the mode meant to be run
        # after every edit.
        expected_subset = set(CONTRACT_CHECKS.keys())
        if phase is not None:
            expected_subset &= refs_in_phase(phase)
        matrix_refs = {"§1A", "§1A-reach", "§1B", "§1C", "§1C-reverse", "§1C-coverage",
                   "§1D", "§1E", "§1F", "§1G", "§1H", "§1I", "§4"}
        if not unit_ok:
            expected_subset.discard("§0")
            executed_checks.discard("§0")
        if not dna_ok:
            expected_subset.discard("§3")
            executed_checks.discard("§3")
        if not compat_ok:
            expected_subset.discard("§2")
            executed_checks.discard("§2")
            expected_subset.discard("§2B")
            executed_checks.discard("§2B")
        if not matrix_ok:
            expected_subset -= matrix_refs
            executed_checks -= matrix_refs
        if not judgment_ok:
            expected_subset.discard("§5")
            executed_checks.discard("§5")
        # Per PHASE, not per stage: a red Phase 1 no longer suppresses the §6F/§6G/§6H
        # rows, and a red Phase 2 no longer suppresses §6/§6D/§6E. Six hand-written
        # discard pairs on one boolean is what made the seam invisible here too.
        for _phase, _ok in ((1, provision_ok), (2, attestation_ok)):
            if _ok:
                continue
            for _ref in _phase_refs(_phase):
                expected_subset.discard(_ref)
                executed_checks.discard(_ref)

        if executed_checks != expected_subset:
            raise AssertionError(
                f"Drift between contract registry and executed harness verifications!\n"
                f"  Executed but not registered: {executed_checks - expected_subset}\n"
                f"  Registered but not executed: {expected_subset - executed_checks}"
            )

        # Third direction, added with the §6 phase split: a ref must have run in the
        # phase it is REGISTERED to. `_record_phase` derives its refs from CHECK_PHASE,
        # so this catches the remaining way they can disagree — a stage calling
        # `_record_phase` with the wrong phase, which would otherwise only show up as a
        # confusing "registered but not executed" for the refs it skipped.
        #
        # This is the runner's half of the reconciliation and it is only reachable by a
        # full `run_all`. The half a mutation can prove in ten seconds is
        # validate_capability's `capability_phase_partition_6`, which holds each half's
        # FINDINGS to the same registry.
        misphased = {ref: (got, validate_capability.CHECK_PHASE[ref])
                     for ref, got in executed_phase.items()
                     if got != validate_capability.CHECK_PHASE.get(ref)}
        if misphased:
            raise AssertionError(
                f"Drift between validate_capability.CHECK_PHASE and the phase each check "
                f"actually ran in!\n"
                + "\n".join(f"  {ref}: ran in Phase {got}, registered as Phase {want}"
                             for ref, (got, want) in sorted(misphased.items()))
            )
        print("  PASS two_direction_contract_match")
        contract_match_ok = True
    except (AssertionError, FileNotFoundError) as exc:
        print(f"  FAIL two_direction_contract_match: {exc}")
        contract_match_ok = False

    print("\n======================================================================")
    all_ok = (unit_ok and dna_ok and compat_ok and interest_ok and vocab_ok and matrix_ok
              and judgment_ok and provision_ok and attestation_ok and contract_match_ok
              and census_ok and render_ok and grade_ok and coverage_ok)
    scope = "ALL TESTS" if phase is None else f"PHASE {phase}"
    if all_ok:
        print(f"{scope} PASSED SUCCESSFULLY! Praise God!")
        if phase == 1:
            print("Phase 1 is green: every check that needs no agent-authored artifact "
                  "passes, so Phase 2's reviews and attestations can be filed against "
                  "generation that will not move under them.")
        print("======================================================================")
        return 0
    else:
        print(f"SOME {scope} CHECKS FAILED. Please review the output above.")
        print("======================================================================")
        return 1

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Practice Generation — Validation Harness Runner")
    parser.add_argument("--fail-fast", "-f", action="store_true", help="Exit immediately on first validator failure")
    parser.add_argument(
        "--phase", type=int, choices=(1, 2), default=None,
        help="run only one band: 1 = artifact-free (the fix-until-green loop), "
             "2 = needs an agent-authored artifact in validation_reports/. "
             "Omit to run everything.",
    )
    args = parser.parse_args()
    sys.exit(run_all(fail_fast=args.fail_fast, phase=args.phase))
