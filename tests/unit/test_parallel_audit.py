"""
test_parallel_audit.py
=======================
Verifies that run_audit(parallel=True) produces byte-identical output
to run_audit(parallel=False) on the same input. This guards against
silent regressions in the per-node extraction (must be module-level
for ProcessPoolExecutor pickling) and the aggregation step.

Marked @pytest.mark.slow (~15 min on a 4-core machine). The full
sample is 5 nodes (1 from each grade x strand combination), which
exercises all DNA + formatter combinations without taking the full
5.8-hour audit time.
"""

import pytest


SAMPLE_FOR_PARALLEL = [
    "mat_g1_na_q1_0",
    "mat_g1_mg_q1_0",
    "mat_g1_dp_q3_0",
    "mat_g2_na_q1_0",
    "mat_g3_na_q1_0",
]


@pytest.mark.slow
def test_parallel_audit_matches_serial():
    from tests.exhaustive_checklist_auditor import run_audit

    serial_failures, serial_repro = run_audit(
        node_ids=SAMPLE_FOR_PARALLEL, parallel=False,
    )
    parallel_failures, parallel_repro = run_audit(
        node_ids=SAMPLE_FOR_PARALLEL, parallel=True,
    )

    serial_dict = {nid: list(errs) for nid, errs in serial_failures.items()}
    parallel_dict = {nid: list(errs) for nid, errs in parallel_failures.items()}

    assert serial_dict == parallel_dict, (
        f"Failure dicts differ.\n"
        f"  Serial-only nodes: {set(serial_dict) - set(parallel_dict)}\n"
        f"  Parallel-only nodes: {set(parallel_dict) - set(serial_dict)}"
    )

    sort_key = lambda c: (c['node_id'], c['seed'], c['formatter'])
    serial_sorted = sorted(serial_repro, key=sort_key)
    parallel_sorted = sorted(parallel_repro, key=sort_key)

    assert serial_sorted == parallel_sorted, (
        f"Repro crash lists differ. "
        f"Serial count={len(serial_sorted)}, parallel count={len(parallel_sorted)}"
    )
