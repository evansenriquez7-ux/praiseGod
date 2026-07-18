"""
Practice Generation — Validation Harness Runner

Runs all validators in the practice problem generation pipeline:
  1. validate_dna (DNA structural check, feasibility, distractors)
  2. validate_compat (compatibility table, coverage, monotonicity, lab/portal equivalence)
  3. validate_interest (interest invariance check)
  4. validate_vocab (vocabulary gating and concept constraints check in full-node mode)
  5. validate_matrix (exhaustive behavioral matrix check)
  6. verify_judgment_completeness (verifies that judgment reports exist for all nodes)

Exit code is 0 if and only if all tests pass.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Set

from backend.app.practice_gen.validation import (
    validate_compat,
    validate_dna,
    validate_interest,
    validate_vocab,
)
from backend.app.practice_gen.validation.validate_matrix import run_matrix_validation
from backend.app.practice_gen.registry import get_all_node_ids, get_node_info

_PGEN_CONTRACT_PATH = Path(__file__).resolve().parents[4] / "docs" / "pgen_contract.md"


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
    "§1A": "validate_matrix: boundary exactness (0.0/1.0)",
    "§1B": "validate_matrix: containment sweep (monotonicity and window bounds)",
    "§1C": "validate_matrix: execution matrix (variant x formatter combinations)",
    "§1C-reverse": "validate_matrix: reverse check (excluded combinations raise clear errors)",
    "§1D": "validate_matrix: vocabulary/concept lint on final formatted output",
    "§1E": "validate_matrix: answer-key & interest theme invariance on formatted output",
    "§2": "validate_compat: registry/compatibility coverage & monotonicity",
    "§3": "validate_dna: structural checks and difficulty profiles feasibility",
    "§4": "validate_matrix: response schema validation",
}

def verify_judgment_completeness() -> List[str]:
    """
    Ensure every registered node in the knowledge graph has a corresponding
    judgment evidence file under validation_reports/judgment/<group_dir>/<node_id>.json (or .md).
    """
    errors: List[str] = []
    node_ids = get_all_node_ids()
    base_dir = Path("validation_reports/judgment")
    
    if not base_dir.exists():
        errors.append(f"Judgment validation directory '{base_dir}' does not exist.")
        return errors
        
    for nid in node_ids:
        parts = nid.split("_")
        group_dir = "_".join(parts[:-1])  # e.g., "mat_g1_na_q1"
        node_file_json = base_dir / group_dir / f"{nid}.json"
        node_file_md = base_dir / group_dir / f"{nid}.md"
        
        if not node_file_json.exists() and not node_file_md.exists():
            errors.append(f"Missing judgment evidence file for node '{nid}' (expected under '{base_dir / group_dir}').")
            
    return errors

def run_all() -> int:
    print("======================================================================")
    print("RUNNING ALL PRACTICE PROBLEM GENERATION VALIDATORS")
    print("======================================================================\n")

    executed_checks: Set[str] = set()

    # 1. DNA Validation
    print("--- 1/6: DNA Structural and Parameter Checks ---")
    dna_results = validate_dna.validate_all_dnas()
    dna_failed = [c for c, errs in dna_results.items() if any(not e.startswith("WARN") for e in errs)]

    feasibility_results = validate_dna.run_all_feasibility_checks()
    feasibility_failed = [c for c, errs in feasibility_results.items() if errs]

    dna_ok = len(dna_failed) == 0 and len(feasibility_failed) == 0
    if dna_ok:
        executed_checks.add("§3")

    # 2. Compatibility
    print("\n--- 2/6: Compatibility, Coverage & Monotonicity ---")
    compat_ok = validate_compat.validate_all()
    if compat_ok:
        executed_checks.add("§2")

    # 3. Interest Invariance
    print("\n--- 3/6: Interest Invariance Checks ---")
    interest_results = validate_interest.validate_all_interest_invariance()
    interest_failed = [c for c, errs in interest_results.items() if errs]
    interest_ok = len(interest_failed) == 0

    # 4. Vocabulary & Concept Gating (Full-Node Mode)
    print("\n--- 4/6: Vocabulary & Concept Gating Audits (Full-Node Mode) ---")
    vocab_results = validate_vocab.run_all_vocab_audits(sample_count=2)
    vocab_failed = []
    for nid, audit in vocab_results.items():
        if audit["pass_rate"] < 1.0:
            vocab_failed.append((nid, audit["violations"]))
    vocab_ok = len(vocab_failed) == 0
    if not vocab_ok:
        print(f"  FAIL vocabulary gating audit ({len(vocab_failed)} nodes failed):")
        for nid, violations in vocab_failed[:5]:  # print first 5 to avoid flood
            print(f"    - {nid}: {violations}")
        if len(vocab_failed) > 5:
            print(f"    ... and {len(vocab_failed) - 5} more nodes.")
    else:
        print("  PASS vocabulary gating audit (all nodes)")

    # 5. Exhaustive Behavioral Matrix
    print("\n--- 5/6: Exhaustive Behavioral Matrix Validation ---")
    # Run matrix validator. We set workers=0 for auto-detection.
    # We pass fail_fast=False to gather complete failures.
    matrix_code = run_matrix_validation(fail_fast=False, workers=0)
    matrix_ok = matrix_code == 0
    if matrix_ok:
        executed_checks.add("§1A")
        executed_checks.add("§1B")
        executed_checks.add("§1C")
        executed_checks.add("§1C-reverse")
        executed_checks.add("§1D")
        executed_checks.add("§1E")
        executed_checks.add("§4")

    # 6. Judgment Reviews Completeness
    print("\n--- 6/6: Judgment Reviews Completeness Checks ---")
    judgment_errors = verify_judgment_completeness()
    judgment_ok = len(judgment_errors) == 0
    if judgment_ok:
        print("  PASS judgment_completeness")
    else:
        print("  FAIL judgment_completeness:")
        for err in judgment_errors[:10]:
            print(f"    - {err}")
        if len(judgment_errors) > 10:
            print(f"    ... and {len(judgment_errors) - 10} more missing files.")

    # Two-direction contract enforcement check
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

        # Check matching set between executed and registered checks
        # (Ignore §2 and §3 if their prior steps failed, to prevent redundant assertion crashes)
        expected_subset = set(CONTRACT_CHECKS.keys())
        if not dna_ok:
            expected_subset.discard("§3")
        if not compat_ok:
            expected_subset.discard("§2")
        if not matrix_ok:
            for s in ("§1A", "§1B", "§1C", "§1C-reverse", "§1D", "§1E", "§4"):
                expected_subset.discard(s)

        if executed_checks != expected_subset:
            raise AssertionError(
                f"Drift between contract registry and executed harness verifications!\n"
                f"  Executed but not registered: {executed_checks - expected_subset}\n"
                f"  Registered but not executed: {expected_subset - executed_checks}"
            )
        print("  PASS two_direction_contract_match")
        contract_match_ok = True
    except (AssertionError, FileNotFoundError) as exc:
        print(f"  FAIL two_direction_contract_match: {exc}")
        contract_match_ok = False

    print("\n======================================================================")
    all_ok = dna_ok and compat_ok and interest_ok and vocab_ok and matrix_ok and judgment_ok and contract_match_ok
    if all_ok:
        print("ALL TESTS PASSED SUCCESSFULLY! Praise God!")
        print("======================================================================")
        return 0
    else:
        print("SOME TESTS FAILED. Please review the output above.")
        print("======================================================================")
        return 1

if __name__ == "__main__":
    sys.exit(run_all())
