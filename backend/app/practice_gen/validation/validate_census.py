"""
§7 — the suite's own census has not silently got smaller.

Why this exists
---------------
Every other check in this harness asks whether the tree is correct. None asked how much
of the tree was being checked at all. Measured 2026-08-26: nothing anywhere asserted a
minimum node count, unit-test count, or mutation count, so the suite would report green
while shrinking:

  * a unit suite that drops from 349 tests to 12 still exits 0 and prints PASS;
  * a registry that loses 100 nodes has every stage check the remaining 51 and pass;
  * deleting mutations lowers `coverage.mutations_registered` and fails nothing.

A total wipe is already caught -- pytest exits 5 on an empty collection -- so this is
specifically about *silent shrinkage*, which is the realistic failure. The shape is not
hypothetical: while building this check, a test guarding the supervisor's queue
arithmetic was written with `@pytest.mark.slow`, a marker `tests/pytest.ini` deselects by
default. It sat in the repo looking like a gate while never running once.

Raise a floor when the real number rises. Never lower one to make a run pass; a floor
that yields is not a floor, and lowering it is precisely the move it exists to catch.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[4]

CENSUS_FLOORS = {
    "nodes": 151,
    # 399 collected 2026-09-08 (was 340, set when 349 were observed). 59 tests could
    # have stopped running without breaching it, which is the silent shrinkage this
    # floor exists to catch, so it is ratcheted to the real number less a little churn.
    "unit_tests": 395,
    # 48 registered 2026-09-08 (was 37). Four were added to prove §8's own directions and
    # one to prove §2C at (node, formatter) granularity; the ten of headroom that existed
    # before meant ten mutations could be deleted silently, and §8 only notices a deletion
    # that leaves a label unproven -- where two mutations prove one label, this floor is
    # the only guard.
    "mutations": 48,
    # 983 observed 2026-09-08. How many (variant, value) pairs the blind-review packets
    # will actually demonstrate across the tree.
    #
    # This one guards a hole the OTHER direction from §2I. §2I caps unproducible
    # declarations from ABOVE, so a filter in _variant_coverage_candidates that drops too
    # much makes §2I report FEWER findings and look like progress. Measured: gutting two
    # applicability filters took candidates 983 -> 932 and §2I 21 -> 19, and
    # `validate_compat` still exited 0 printing "13/13 check groups passed".
    #
    # Three such filters were added on 2026-09-08 to clear 44 §2I findings; before that
    # there were none to gut. Narrowing what a check looks at is a legitimate fix and a
    # silent way to fake one, and only this floor tells them apart.
    #
    # Lower it deliberately, in the commit that removes a declaration and says which
    # competency clause does not name it -- e.g. dropping unit_type='cm' from three
    # "using non-standard units" nodes should lower this by exactly 6.
    # 983 -> 974 on 2026-09-08, lowered deliberately with the commit that removed the
    # declarations: 3 multi-DNA variants the node's effective bounds forbid outright, and
    # 6 standard-unit values on G1 nodes whose competencies read "using non-standard
    # units". Each removal cites the clause; the count moved by exactly the measured
    # amount, which is the point of stating it here.
    # 974 -> 964 on 2026-09-08, lowered deliberately with the commit that stopped the
    # packet builder declaring variants CURRICULUM_VARIANT_GATES already refuses at the
    # node's grade/quarter: 3x strategy=expanded_form (G1 Q1 nodes, gate G1 Q2),
    # task_type=associative (G1 Q2, gate G2 Q1), 4x number_type=multi_digit (G2 Q3, gate
    # G3 Q3), and draw_construct + recognize_model (G2 Q4, gate G3 Q1). Each clause is
    # quoted in validate_compat's _PRODUCIBLE_FLOOR note; the count moved by exactly the
    # measured 10, which is the point of stating it here.
    "variant_candidates": 964,
}

# §8 inventory: the assertions this module can independently fail on. Derived from the
# floors rather than restated, so adding a floor adds an assertion that must then be
# proven by a mutation or excused in validate_coverage.UNPROVEN_ASSERTIONS -- a new floor
# nobody can breach on purpose is a floor nobody has checked.
ASSERTIONS = ("census",) + tuple(f"census_{key}" for key in CENSUS_FLOORS)


def count_nodes() -> int:
    from backend.app.practice_gen.registry import get_all_node_ids

    return len(get_all_node_ids())


def count_mutations() -> int:
    from tests.mutation_harness import MUTATIONS

    return len(MUTATIONS)


def count_variant_candidates() -> int:
    """(variant, value) pairs the review packets will demonstrate, tree-wide."""
    from backend.app.practice_gen.registry import get_all_node_ids

    from .judgment_packets import _variant_coverage_candidates

    return sum(len(_variant_coverage_candidates(n)) for n in get_all_node_ids())


def count_unit_tests() -> Optional[int]:
    """
    How many tests the fast suite would actually RUN, not how many exist.

    `--collect-only -q` after marker deselection is the honest number: a test that is
    collected but deselected does not gate, so counting the file's contents would let the
    suite hollow out while the census kept passing.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit", "-q", "--collect-only",
         "-p", "no:cacheprovider"],
        cwd=REPO_ROOT, capture_output=True, text=True,
        env={"PYTHONPATH": str(REPO_ROOT), "PATH": "/usr/bin:/bin"},
    )
    # "343/349 tests collected (6 deselected) in 1.20s" or "343 tests collected in 1.20s"
    m = re.search(r"(\d+)(?:/\d+)? tests? collected", proc.stdout)
    return int(m.group(1)) if m else None


def validate_census() -> List[str]:
    """Return one error per floor breached. Empty list means the suite is intact."""
    errors: List[str] = []

    observed = {}
    try:
        observed["nodes"] = count_nodes()
    except Exception as exc:  # noqa: BLE001 - naming the failure beats skipping the floor
        return [f"§7 census: node registry did not load ({exc}); the floor cannot be checked"]
    try:
        observed["mutations"] = count_mutations()
    except Exception as exc:  # noqa: BLE001
        return [f"§7 census: mutation harness did not import ({exc}); the floor cannot be checked"]

    try:
        observed["variant_candidates"] = count_variant_candidates()
    except Exception as exc:  # noqa: BLE001
        return [f"§7 census: variant candidates did not enumerate ({exc}); "
                f"the coverage floor cannot be checked"]

    n = count_unit_tests()
    if n is None:
        return ["§7 census: could not parse a test count from pytest --collect-only; "
                "the unit-test floor cannot be checked, so the suite is unmeasured"]
    observed["unit_tests"] = n

    for key, floor in CENSUS_FLOORS.items():
        got = observed[key]
        if got < floor:
            errors.append(
                f"§7 census: {key}={got} is below the floor of {floor}. The suite got "
                f"smaller — find what left before touching this number. Lowering the "
                f"floor to make this pass is the defect the floor exists to catch."
            )
    return errors


def validate_all() -> bool:
    errors = validate_census()
    if errors:
        print(f"  FAIL census ({len(errors)} floor(s) breached):")
        for e in errors:
            print(f"    - {e}")
        return False
    for key, floor in CENSUS_FLOORS.items():
        got = {"nodes": count_nodes, "mutations": count_mutations,
               "unit_tests": count_unit_tests,
               "variant_candidates": count_variant_candidates}[key]()
        print(f"  PASS census: {key}={got} (floor {floor})")
    return True


def main() -> int:
    return 0 if validate_all() else 1


if __name__ == "__main__":
    sys.exit(main())
