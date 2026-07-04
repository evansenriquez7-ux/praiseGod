"""
test_checklist_audit.py
=======================
Slow pytest entry that runs the full checklist auditor (in parallel
via ProcessPoolExecutor) and asserts 0 violations. Catches regressions
in the audit pipeline before they ship to production.

Marked @pytest.mark.slow because the full audit still takes 20-40
minutes on a 4-core machine (was 5.8 hours before parallelization).
Run with: ../.venv/bin/python -m pytest tests/unit/test_checklist_audit.py -v -m slow
"""

import pytest

from tests.exhaustive_checklist_auditor import run_audit


@pytest.mark.slow
def test_full_audit_zero_violations():
    failures, repro_crashes = run_audit(parallel=True)
    assert len(failures) == 0, (
        f"Checklist audit found {len(failures)} nodes with violations. "
        f"First few:\n" +
        "\n".join(
            f"  {nid}: {errs[0][:120]}"
            for nid, errs in list(failures.items())[:5]
        )
    )
    assert len(repro_crashes) == 0, (
        f"Checklist audit found {len(repro_crashes)} pipeline crashes. "
        f"First few:\n" +
        "\n".join(
            f"  {c['node_id']} seed={c['seed']} fmt={c['formatter']}: {c['error_message'][:80]}"
            for c in repro_crashes[:5]
        )
    )
