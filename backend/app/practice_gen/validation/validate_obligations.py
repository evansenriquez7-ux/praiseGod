"""
§11 — the student-path obligation manifest holds itself to production.

WHY THIS IS A GATE AND NOT JUST A REPORT
----------------------------------------
Plan step 0B (`H-04`) asks for a machine-generated obligation manifest derived from the
production student route, and gives it an acceptance test with a sharp edge: "two
independent derivations agree on the reachable count". That is not ceremony. The plan
itself carried a recorded figure of 4,325 obligations across 463 node/DNA/formatter
pairs, the probe that produced it is NOT on disk, and **neither number reproduces** from
any candidate model (measured 2026-09-12: 3,063 / 5,238 / 2,950 / 5,060 depending on the
scope and whether assignments are summed or crossed). A count nobody can re-derive is a
number, not evidence -- so the manifest derives it twice, by two different traversals of
the production tables, and this check fails if they disagree.

The second direction is the one the enumeration found on its first run. §2B and §2C
already gate "a formatter a node ADVERTISES must be servable". Nothing gated the reverse:
a formatter REGISTERED in `adapter.FORMATTER_ROUTES` that no node can ever receive. Five
exist, in two distinct classes:

  * `fill_in_blank`, `numeric_input`, `ten_frame` -- registered routes that **no DNA
    declares** in COMPATIBILITY. Nothing can select them at all.
  * `balance_scale` (missing_number) and `table_read` (pictographs) -- declared by a DNA,
    but every node mapped to that DNA excludes them through NODE_FORMATTER_EXCLUSIONS.

A FLOOR, NOT A HARD ZERO -- AND WHY
------------------------------------
Scaling Mandate 5 says a gate whose baseline is already red cannot be told apart from the
noise it sits in, so it is activated at the measured count and may only SHRINK. Driving it
to zero means deciding whether each dead route should be deleted or wired to a node, and
that is a curriculum question (a formatter may exist for a grade not yet built), not one
this harness may answer on its own. Recording the number and refusing to let it grow is
what the harness can honestly do today.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
  * **Enumeration is not execution.** This counts the reachable space; it generates
    nothing. An obligation counted here may still be refused at generation time. Step 0B's
    executor is what turns that into a named failure.
  * **Experience and interest are NOT crossed into the manifest.** Both are free
    parameters of `pipeline.run()`, so the true product is 5,060 x 4 x 27 = 546,480. The
    budget file records the multiplier rather than enumerating it, because the execution
    cost has not been measured. This is the largest unclosed part of `H-04` and neither
    this module nor the budget file describes it as covered.
  * **Two derivations agreeing does not make the model right.** Both read the same
    production tables. They catch a transcription error in either traversal, not a
    misunderstanding shared by both.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[4]

# §8 inventory: the assertions this module can independently fail on.
ASSERTIONS = (
    "obligation_derivations_agree",   # two traversals of one production fact disagree
    "obligation_routes_reachable",    # a registered route no obligation can reach
)

# MEASURED 2026-09-12: 5, in the two classes named in the docstring. Shrink-only.
UNREACHABLE_ROUTE_FLOOR = 5


def collect_findings() -> List[str]:
    sys.path.insert(0, str(REPO_ROOT))
    from tests.obligation_manifest import build_budget

    findings: List[str] = []
    budget = build_budget()

    counts = budget["counts"]
    alt = budget["independent_derivation"]
    if not alt["agrees"]:
        findings.append(
            f"obligation_derivations_agree: the node-first traversal counts "
            f"{counts['node_dna_formatter_pairs']} (node, DNA, formatter) pairs and "
            f"{counts['discrete_obligations']} discrete obligations; the formatter-first "
            f"traversal counts {alt['pairs']} and {alt['discrete_obligations']}. Two "
            f"derivations of one production fact disagree, so neither is evidence of the "
            f"reachable space."
        )

    unreachable = budget["derived_coverage"]["formatters_no_obligation_can_reach"]
    if len(unreachable) > UNREACHABLE_ROUTE_FLOOR:
        findings.append(
            f"obligation_routes_reachable: {len(unreachable)} registered formatter "
            f"route(s) no obligation can reach, above the floor of "
            f"{UNREACHABLE_ROUTE_FLOOR}: {unreachable}. A route in "
            f"adapter.FORMATTER_ROUTES that no node can ever serve is either a DNA that "
            f"forgot to declare it, or a formatter whose nodes all exclude it. The floor "
            f"may only shrink."
        )
    return findings


def validate_all() -> bool:
    findings = collect_findings()
    if findings:
        for finding in findings:
            print(f"  FAIL {finding}")
        return False

    from tests.obligation_manifest import BUDGET_PATH, build_budget

    budget = build_budget()
    counts = budget["counts"]
    cross = budget["not_crossed_into_the_manifest"]
    unreachable = budget["derived_coverage"]["formatters_no_obligation_can_reach"]
    print(f"  PASS obligation_derivations_agree: two independent traversals agree on "
          f"{counts['node_dna_formatter_pairs']} (node, DNA, formatter) pair(s) and "
          f"{counts['discrete_obligations']} discrete obligation(s); "
          f"{counts['continuous_class_crossings']} continuous class crossing(s)")
    print(f"  PASS obligation_routes_reachable: {len(unreachable)} registered route(s) "
          f"unreachable (floor {UNREACHABLE_ROUTE_FLOOR}, shrink-only): {unreachable}")
    print(f"       experience x{cross['experience']['multiplier']} and interest "
          f"x{cross['student_interest']['multiplier']} are NOT crossed in "
          f"({cross['full_cross_if_enumerated']} if enumerated) -- limitation 2")
    print(f"       budget written to {BUDGET_PATH.relative_to(REPO_ROOT)}")
    return True


def main() -> int:
    return 0 if validate_all() else 1


if __name__ == "__main__":
    sys.exit(main())
