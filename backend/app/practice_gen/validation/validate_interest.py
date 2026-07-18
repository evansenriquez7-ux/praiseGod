"""
Practice Generation — Interest Invariance Validation

Verifies that interest-theme wrapping never changes the correct answer.
A formula DNA's numeric answer must be identical regardless of which
story spine / interest theme is applied.

Run as a module:
    python -m backend.app.practice_gen.validation.validate_interest
"""

from __future__ import annotations

import importlib
import sys
from typing import Dict, List, Optional

from ..dna.base import DNA
from ..generators.base_generator import generate_context


# ─── DNA module registry (same as validate_dna) ───────────────────────────────

from ._manifest import DNA_MODULE_MAP, load_dna

# Three representative interest themes used for invariance testing.
# These must exist in interest_bank.json; if not found the generator falls back
# to the neutral theme — which is still fine for invariance checking.
_TEST_THEMES: List[str] = ["animals", "sports", "food"]


def validate_interest_invariance(
    dna: DNA,
    grade: int,
    node_id: str,
    trials: int = 10,
) -> List[str]:
    """
    Verify that interest theme does not alter the correct answer.

    For each of `trials` seeds, generates the same problem three times
    (once per _TEST_THEMES) and asserts that all three correct_answer
    values are identical.

    Only applies to formula-type DNAs with requires_context=True.
    Returns an empty list immediately for all other DNA types.

    Args:
        dna: A formula DNA with requires_context=True.
        grade: Student grade level (1–3).
        node_id: A valid MATATAG node ID for this DNA.
        trials: Number of seed values to test.

    Returns:
        List of error strings. Empty list = invariance holds.
    """
    errors: List[str] = []

    if not (dna.dna_type == "formula" and dna.requires_context):
        return errors  # Only meaningful for context-using formula DNAs.

    for seed in range(trials):
        answers: List = []
        for theme in _TEST_THEMES:
            try:
                ctx = generate_context(
                    dna=dna,
                    node_id=node_id,
                    grade=grade,
                    seed=seed,
                    difficulty_profile=None,
                    interest_theme=theme,
                )
                answers.append(ctx.correct_answer)
            except Exception as exc:
                errors.append(
                    f"{dna.concept} seed={seed} theme='{theme}': "
                    f"generate_context raised: {exc}"
                )
                # Can't compare if generation failed; continue to next seed.
                break

        if len(answers) == len(_TEST_THEMES):
            if len(set(answers)) > 1:
                errors.append(
                    f"{dna.concept} seed={seed}: correct_answer differs across "
                    f"interest themes: {dict(zip(_TEST_THEMES, answers))}"
                )

    return errors


def validate_all_interest_invariance() -> Dict[str, List[str]]:
    """
    Run interest invariance checks for all requires_context=True formula DNAs.

    Returns:
        Dict mapping concept name → list of error strings.
    """
    # Map concept → one representative node_id from registry.
    # We import lazily to avoid circular imports.
    from ..registry import NODE_TO_DNA

    # Build concept → first node_id mapping.
    concept_to_node: Dict[str, str] = {}
    for node_id, concepts in NODE_TO_DNA.items():
        for c in concepts:
            if c not in concept_to_node:
                concept_to_node[c] = node_id

    results: Dict[str, List[str]] = {}

    for concept in DNA_MODULE_MAP:
        try:
            dna = load_dna(concept)
        except ImportError:
            continue
        if not (dna.dna_type in ("formula", "algorithmic") and dna.requires_context):
            continue

        node_id = concept_to_node.get(concept)
        if node_id is None:
            results[concept] = [
                f"{concept}: no node_id found in NODE_TO_DNA — cannot test."
            ]
            continue

        # Extract grade from node_id (format: mat_g{grade}_...)
        try:
            grade = int(node_id.split("_")[1][1])
        except (IndexError, ValueError):
            grade = 1

        errors = validate_interest_invariance(dna, grade, node_id)
        results[concept] = errors

    # Print summary
    total = len(results)
    passed = sum(1 for errs in results.values() if not errs)
    failed = total - passed
    print(f"\nInterest invariance: {passed}/{total} passed, {failed} failed.")
    for concept, errs in results.items():
        if errs:
            print(f"  FAIL {concept}:")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"  PASS {concept}")

    return results


# ─── entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = validate_all_interest_invariance()
    failed = [c for c, errs in results.items() if errs]
    sys.exit(1 if failed else 0)
