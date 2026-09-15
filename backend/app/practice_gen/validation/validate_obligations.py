"""
§11 — the student-path obligation manifest and executor hold themselves to production.

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

EXECUTION, BENCHMARK, AND SHARDS
--------------------------------
The first 1,000-entry benchmark proved why enumeration alone was insufficient: 152 entries
the first manifest called reachable were refused by the production route. Instrumentation
located the cause at a curriculum-gate call that passed `node_id` where the predicate is
DNA-keyed. The corrected manifest contains 4,293 base obligations and crosses every one
with 27 interest requests and four experiences (463,644 finite obligations). A 1,000-cache-
key, four-worker benchmark executes 4,000 represented obligations and is digest-bound to
the current source. The fast PR control executes fixed sentinels spanning every node, DNA,
formatter, interest request, experience, and continuous seed slot.

The release tier uses five deterministic seeds per finite obligation. It caches the common
generator/formatter result across the four terminal experience wrappers, producing 579,555
cache keys that represent 2,318,220 executions. Shards own cache indices by modulo, so a
complete set is non-overlapping and its union is mechanically the manifest.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
  * The PR tier is partial. It runs fixed cross-family sentinels plus base obligations a
    caller explicitly identifies as changed. Only complete release receipts prove the full
    finite sweep.
  * No release receipts is a named failure. A missing, overlapping, stale, failed, or
    over-budget shard also fails; only a complete current union passes.
  * Continuous axes move together at each scalar representative; their Cartesian product
    and behavior between representatives remain unproved.
  * `None` interest means automatic seeded selection, not neutral content. A named theme
    outside a grade band also falls back automatically. H-05 owns the question of whether
    silently ignoring a requested theme is acceptable; this executor proves the request
    path executes, not that every theme changes every rendered item.
  * **Two derivations agreeing does not make the model right.** Both read the same
    production tables. They catch a transcription error in either traversal, not a
    misunderstanding shared by both.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[4]

# §8 inventory: the assertions this module can independently fail on.
ASSERTIONS = (
    "obligation_derivations_agree",   # two traversals of one production fact disagree
    "obligation_routes_reachable",    # a registered route no obligation can reach
    "obligation_dimension_coverage_11",  # a finite/continuous dimension shrank
    "obligation_execution_11",        # a declared-reachable sentinel is refused
    "obligation_benchmark_11",        # benchmark absent, stale, failing, or over budget
    "obligation_release_shards_11",   # release absent/incomplete/overlapping/stale
)

# MEASURED 2026-09-12: 5, in the two classes named in the docstring. Shrink-only.
UNREACHABLE_ROUTE_FLOOR = 5

# Measured after the executor exposed and the manifest fixed a DNA-keyed curriculum-gate
# argument bug. Floors may only rise; a legitimate shrink is a ground-truth change.
BASE_OBLIGATION_FLOOR = 4269
FINITE_OBLIGATION_FLOOR = 461_052
CONTINUOUS_CROSSING_FLOOR = 18_762
REQUIRED_RESPONSE_MODES = {
    "click", "drag", "error_detect", "fill_in_blank", "mcq", "true_false",
}


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

    execution = budget["execution_model"]
    dimension_failures: List[str] = []
    if counts["discrete_obligations"] < BASE_OBLIGATION_FLOOR:
        dimension_failures.append(
            f"base obligations {counts['discrete_obligations']} < floor "
            f"{BASE_OBLIGATION_FLOOR}"
        )
    if counts["continuous_class_crossings"] < CONTINUOUS_CROSSING_FLOOR:
        dimension_failures.append(
            f"continuous crossings {counts['continuous_class_crossings']} < floor "
            f"{CONTINUOUS_CROSSING_FLOOR}"
        )
    if execution["finite_obligations"] < FINITE_OBLIGATION_FLOOR:
        dimension_failures.append(
            f"finite obligations {execution['finite_obligations']} < floor "
            f"{FINITE_OBLIGATION_FLOOR}"
        )
    if execution["experience"]["multiplier"] < 4:
        dimension_failures.append("fewer than four production experience wrappers")
    if execution["student_interest_request"]["multiplier"] < 27:
        dimension_failures.append("fewer than 27 interest request paths")
    if execution["seed_slot_scalars"][:3] != [0.0, 0.5, 1.0]:
        dimension_failures.append(
            "seed slots no longer cover min boundary, interior, and max boundary"
        )
    if dimension_failures:
        findings.append(
            "obligation_dimension_coverage_11: " + "; ".join(dimension_failures)
        )

    # The modulo sharding algorithm is checked against the real current cache-key count.
    # This costs no generation and makes a dropped tail item a named failure.
    from tests.obligation_executor import cache_key_count, shard_indices

    shard_count = 6
    expected_keys = cache_key_count()
    shard_key_count = sum(len(shard_indices(i, shard_count)) for i in range(shard_count))
    if shard_key_count != expected_keys:
        findings.append(
            f"obligation_release_shards_11: modulo shards cover {shard_key_count} "
            f"cache keys, expected {expected_keys}"
        )
    return findings


def _benchmark_findings() -> List[str]:
    from tests.obligation_executor import (
        BENCHMARK_PATH,
        base_manifest_digest,
        finite_obligation_count,
        represented_execution_count,
        source_input_digest,
    )

    if not BENCHMARK_PATH.exists():
        return [f"obligation_benchmark_11: missing {BENCHMARK_PATH.relative_to(REPO_ROOT)}"]
    try:
        benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"obligation_benchmark_11: unreadable benchmark artifact: {exc}"]

    errors: List[str] = []
    if benchmark.get("schema_version") != 1:
        errors.append("unsupported schema_version")
    if benchmark.get("manifest_digest") != base_manifest_digest():
        errors.append("manifest digest is stale")
    if benchmark.get("source_input_digest") != source_input_digest():
        errors.append("source/input digest is stale")
    if benchmark.get("sample_size", 0) < 1000:
        errors.append("fewer than 1,000 representative cache keys measured")
    counts = benchmark.get("counts", {})
    if counts.get("finite_obligations") != finite_obligation_count():
        errors.append("finite-obligation count disagrees with the current manifest")
    if counts.get("release_represented_executions") != represented_execution_count():
        errors.append("release execution count disagrees with the current manifest")
    measurement = benchmark.get("measurement", {})
    if measurement.get("failures"):
        errors.append(f"benchmark contains {len(measurement['failures'])} failure(s)")
    missing_modes = REQUIRED_RESPONSE_MODES - set(measurement.get("response_modes", ()))
    if missing_modes:
        errors.append(f"response modes not exercised: {sorted(missing_modes)}")
    targets = benchmark.get("targets", {})
    if not targets.get("release_projection_within_budget"):
        errors.append("projected release exceeds four hours on the reference runner")
    if not targets.get("shard_projection_within_budget"):
        errors.append("projected release shard exceeds 30 minutes")
    return ["obligation_benchmark_11: " + "; ".join(errors)] if errors else []


def _sentinel_findings() -> tuple[List[str], dict]:
    from tests.obligation_executor import (
        REFERENCE_WORKERS,
        execute_indices,
        pr_sentinel_indices,
        summarize_results,
    )

    indices = pr_sentinel_indices()
    results, elapsed = execute_indices(indices, workers=REFERENCE_WORKERS)
    summary = summarize_results(results, elapsed)
    findings = [
        f"obligation_execution_11: index={failure['cache_index']} "
        f"seed={failure['seed']} key={failure['obligation_key']} "
        f"{failure['exception_type']}: {failure['message']}"
        for failure in summary["failures"]
    ]
    missing_modes = REQUIRED_RESPONSE_MODES - set(summary["response_modes"])
    if missing_modes:
        findings.append(
            f"obligation_execution_11: PR sentinels did not execute response modes "
            f"{sorted(missing_modes)}"
        )
    return findings, summary


def validate_all() -> bool:
    findings = collect_findings()
    findings.extend(_benchmark_findings())
    sentinel_findings, sentinel_summary = _sentinel_findings()
    findings.extend(sentinel_findings)

    from tests.obligation_executor import release_receipt_findings

    release_findings, release_summary = release_receipt_findings()
    findings.extend(f"obligation_release_shards_11: {finding}"
                    for finding in release_findings)
    if findings:
        for finding in findings:
            print(f"  FAIL {finding}")
        return False

    from tests.obligation_manifest import BUDGET_PATH, write_budget

    budget = write_budget()
    counts = budget["counts"]
    execution = budget["execution_model"]
    unreachable = budget["derived_coverage"]["formatters_no_obligation_can_reach"]
    print(f"  PASS obligation_derivations_agree: two independent traversals agree on "
          f"{counts['node_dna_formatter_pairs']} (node, DNA, formatter) pair(s) and "
          f"{counts['discrete_obligations']} discrete obligation(s); "
          f"{counts['continuous_class_crossings']} continuous class crossing(s)")
    print(f"  PASS obligation_routes_reachable: {len(unreachable)} registered route(s) "
          f"unreachable (floor {UNREACHABLE_ROUTE_FLOOR}, shrink-only): {unreachable}")
    print(f"  PASS obligation_dimension_coverage_11: "
          f"{counts['discrete_obligations']} base x "
          f"{execution['student_interest_request']['multiplier']} interest requests x "
          f"{execution['experience']['multiplier']} experiences = "
          f"{execution['finite_obligations']} finite obligations; "
          f"{execution['release_represented_executions']} executions at "
          f"{execution['seeds_per_obligation']} seeds")
    print(f"  PASS obligation_execution_11: {sentinel_summary['cache_keys_completed']} "
          f"PR cache-key sentinels / {sentinel_summary['represented_executions']} "
          f"experience executions completed in {sentinel_summary['elapsed_seconds']:.3f}s")
    print("  PASS obligation_benchmark_11: 1,000 representative cache keys are current, "
          "failure-free, and project within the four-hour / 30-minute-shard budgets")
    print(f"  PASS obligation_release_shards_11: {release_summary['receipts']} current "
          f"shards cover {release_summary['cache_keys']} cache keys / "
          f"{release_summary['represented_executions']} executions with no overlap")
    print(f"       budget written to {BUDGET_PATH.relative_to(REPO_ROOT)}")
    return True


def _run_single(name: str) -> int:
    """Run one independent §11 direction for clean mutation controls."""
    if name == "manifest":
        findings = collect_findings()
    elif name == "benchmark":
        findings = _benchmark_findings()
    elif name == "sentinels":
        findings, _summary = _sentinel_findings()
    elif name == "release":
        from tests.obligation_executor import release_receipt_findings

        raw, _summary = release_receipt_findings()
        findings = [f"obligation_release_shards_11: {finding}" for finding in raw]
    else:  # pragma: no cover - argparse owns this boundary
        raise ValueError(f"unknown §11 check {name!r}")
    if findings:
        for finding in findings:
            print(f"  FAIL {finding}")
        return 1
    print(f"  PASS obligation_{name}_11")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="student-path obligation checks")
    parser.add_argument(
        "--only", choices=("manifest", "benchmark", "sentinels", "release"),
        help="run one independent direction (used by mutation proofs)",
    )
    args = parser.parse_args()
    return _run_single(args.only) if args.only else (0 if validate_all() else 1)


if __name__ == "__main__":
    sys.exit(main())
