"""
§8 — how many of the harness's assertions are actually proven.

Why this exists
---------------
"17 of 24 checks proven" was measured against the wrong denominator. `CONTRACT_CHECKS`
conflates bundles with atomic checks: `§2` was five sub-checks, `§3` is four DNA
validators, and `validate_matrix` alone emits **26 distinct assertion labels** behind
about eleven refs. A ref counted as proven the moment ONE of its sub-assertions had a
mutation, so §5 read as proven on the strength of a single boilerplate mutation while its
STALE and non-PASS paths were untouched.

And `Mutation.expected_check` was free text. Nothing could state which assertions were
proven, so the deficit could not be counted, tracked, or stopped from growing.

`Mutation.asserts` is now the machine-checkable link. This module inventories every
assertion the harness can emit and requires each to be either proven by a mutation or
named in UNPROVEN_ASSERTIONS with a reason and a date.

Why a floor and not a hard zero
-------------------------------
The deficit is real today. Mandate §5: a check whose baseline is already red cannot be
told from the noise it sits in. So the allowlist is a floor that may only SHRINK -- a NEW
assertion with neither a mutation nor an entry fails immediately, which is the point. The
deficit can never grow again, only be paid down.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Set

REPO_ROOT = Path(__file__).resolve().parents[4]

# Assertions that can fail but have no mutation proving they do. Each needs a reason and a
# date. This list may only ever get SHORTER. Adding to it to make a run pass is the move it
# exists to catch -- write the mutation instead.
UNPROVEN_ASSERTIONS: Dict[str, str] = {
    "answer_key_recomputation":     "2026-08-28: §1E sibling; answer_key_integrity is proven, this path is not",
    "concept_gating":               "2026-08-28: distractor-provenance gate; vocabulary_gating is proven, this is not",
    "import_dna":                   "2026-08-28: overlaps registry_drift, which is proven",
    "interest_invariance_formatted": "2026-08-28: stage 4 covers the property; the matrix label is unproven",
    "interest_theme_generation":    "2026-08-28: as above",
    "reverse_compatibility_check_crash": "2026-08-28: crash variant of a proven check",
    "reverse_curriculum_gate_check": "2026-08-28: curriculum-gate reverse path, unproven",
    "reverse_curriculum_gate_check_crash": "2026-08-28: crash variant of the above",
    "visual_schema_integrity":      "2026-08-28: §4 visual schema; §9 covers the render contract, not this",
    "worker_crash":                 "2026-08-28: infrastructure label, not a content assertion",
    "scalar_1_0_reach":             "2026-08-28: §1A-reach; needs a generator capped below its ceiling",
    "node_to_dna_presence":         "2026-08-28: registry mapping presence",
}


def matrix_assertion_labels() -> Set[str]:
    """Every `"check": "<label>"` the behavioural matrix can emit."""
    src = (REPO_ROOT / "backend" / "app" / "practice_gen" / "validation"
           / "validate_matrix.py").read_text(encoding="utf-8")
    return set(re.findall(r'"check": "([a-z0-9_]+)"', src))


def proven_assertions() -> Set[str]:
    sys.path.insert(0, str(REPO_ROOT))
    from tests.mutation_harness import MUTATIONS

    proven: Set[str] = set()
    for m in MUTATIONS:
        proven |= set(m.asserts or ())
    return proven


def validate_coverage() -> List[str]:
    """Return an error per assertion that is neither proven nor knowingly excused."""
    inventory = matrix_assertion_labels()
    # Assertions outside the matrix carry synthetic labels; they are proven by name via
    # Mutation.asserts and do not need discovering.
    proven = proven_assertions()

    errors: List[str] = []
    unexplained = sorted(inventory - proven - set(UNPROVEN_ASSERTIONS))
    for label in unexplained:
        errors.append(
            f"§8 coverage: assertion {label!r} can fail but no mutation proves it does, and "
            f"it is not in UNPROVEN_ASSERTIONS. An unproven check is a broken check. Write "
            f"the mutation, or add an entry with a reason and a date -- and note the "
            f"allowlist may only shrink."
        )

    # The allowlist must shrink, never grow. Anything on it that is NOW proven should be
    # removed, and anything on it that no longer exists is stale bookkeeping.
    stale = sorted(set(UNPROVEN_ASSERTIONS) & proven)
    for label in stale:
        errors.append(
            f"§8 coverage: {label!r} is listed as unproven but a mutation now proves it. "
            f"Remove it from UNPROVEN_ASSERTIONS -- the allowlist is a debt register, and "
            f"leaving a paid debt on it hides how much is really left."
        )
    return errors


def validate_all() -> bool:
    inventory = matrix_assertion_labels()
    proven = proven_assertions()
    errors = validate_coverage()
    covered = len(inventory & proven)
    if errors:
        print(f"  FAIL assertion_coverage ({len(errors)}):")
        for e in errors[:10]:
            print(f"    - {e}")
        return False
    print(f"  PASS assertion_coverage: {covered}/{len(inventory)} matrix assertions proven, "
          f"{len(UNPROVEN_ASSERTIONS)} knowingly unproven (allowlist may only shrink); "
          f"{len(proven)} assertions proven overall")
    return True


def main() -> int:
    return 0 if validate_all() else 1


if __name__ == "__main__":
    sys.exit(main())
