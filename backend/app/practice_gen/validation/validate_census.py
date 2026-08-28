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
    "unit_tests": 340,   # 349 observed 2026-08-26, with headroom for ordinary churn
    "mutations": 24,
}


def count_nodes() -> int:
    from backend.app.practice_gen.registry import get_all_node_ids

    return len(get_all_node_ids())


def count_mutations() -> int:
    from tests.mutation_harness import MUTATIONS

    return len(MUTATIONS)


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
               "unit_tests": count_unit_tests}[key]()
        print(f"  PASS census: {key}={got} (floor {floor})")
    return True


def main() -> int:
    return 0 if validate_all() else 1


if __name__ == "__main__":
    sys.exit(main())
