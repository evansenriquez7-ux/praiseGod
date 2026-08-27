"""
§9 — the render contract: the payload the STUDENT receives must be renderable.

Why this exists
---------------
All eight of run_all's stages stop at `FormattedProblem`. They validate the pipeline's
data -- the answer key survives formatting, the vocabulary is in-grade, the visual payload
is arithmetically sane. None asks whether the React component can render what it is
handed. A `visual_params` key the component reads collapses to `undefined`/`0`/`false`,
and the pupil sees an empty or wrong picture while every stage reports PASS.

Measured on the student path, 2026-08-28, three seeds per node:

    FractionModel  missing ['total_wholes']                    x7   (Bug #57)
    Calendar       missing ['month','year']        params: {}  x3
    BarChart       missing ['categories']          params: {}  x3
    ClockSet       missing ['hours','minutes',...] params: {}  x3

Three of those four render from a COMPLETELY EMPTY payload.

Why this checks the student path rather than driving the auditor
----------------------------------------------------------------
`tests/frontend_contract_auditor.py` owns the contract knowledge (REQUIRED_KEYS) and is
reused here, but it is not a usable gate as it stands:

  * its worker pool does not finish on the full tree -- >25 min without completing,
    while `--no-parallel` takes ~11 min, and killing it strands `multiprocessing.spawn`
    orphans that slow everything afterwards (the tree's own "Trap 3");
  * it samples by pinning each advertised formatter, so it never exercises the auto-select
    path students actually get. It reported `mat_g1_dp_q3_0` CLEAN while that node serves
    a BarChart with an empty payload to every student who lands on it.

Driving the student path directly is faster, deterministic, and measures the thing that
matters. The auditor remains valuable as a deeper sweep across pinned formatters.

Floors, not a hard zero
-----------------------
The baseline is red, and Scaling Mandate §5 is explicit that a check whose baseline is
already red cannot be told from the noise it sits in. The floor may only SHRINK; lowering
it to make a run pass is the move it exists to catch.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[4]

# Observed 2026-08-28 over all 151 nodes at SEEDS_PER_NODE=3. Each is a payload the React
# component cannot render. Tracked as content work; the floor may only shrink.
RENDER_FLOOR = 16

SEEDS_PER_NODE = (11, 42, 64)


def _required_keys() -> Dict[str, List[str]]:
    """The contract itself lives with the auditor; reuse it rather than restating it."""
    sys.path.insert(0, str(REPO_ROOT))
    from tests.frontend_contract_auditor import REQUIRED_KEYS

    return REQUIRED_KEYS


def collect_findings(node_ids: Optional[List[str]] = None) -> List[str]:
    """Every (node, seed) whose visual payload omits a key the component reads."""
    sys.path.insert(0, str(REPO_ROOT))
    from backend.app.practice_gen.registry import get_all_node_ids
    from backend.app.services.orchestrator import PracticeOrchestrator

    required = _required_keys()
    findings: List[str] = []
    for node_id in (node_ids or get_all_node_ids()):
        for seed in SEEDS_PER_NODE:
            try:
                p = PracticeOrchestrator.generate_problem(
                    node_id=node_id, seed=seed, is_student_path=True
                )
            except Exception:
                continue  # a generation failure is another stage's finding, not §9's
            d = p if isinstance(p, dict) else p.__dict__
            vt = d.get("visual_type")
            if not vt or vt not in required:
                continue
            params = d.get("visual_params")
            if not isinstance(params, dict):
                params = {}
            missing = [k for k in required[vt] if k not in params]
            if missing:
                findings.append(
                    f"{node_id} (seed {seed}): {vt} payload omits {missing}, which the "
                    f"React component reads. It collapses to undefined/0/false and the "
                    f"student sees a broken or empty visual. Payload has: "
                    f"{sorted(params)[:6] or 'NOTHING'}"
                )
    return findings


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    """
    Full tree: compare against the floor.
    Subset (`node_ids`): require ZERO findings, so §9 is mutation-provable in seconds.
    """
    findings = collect_findings(node_ids)

    if node_ids:
        if findings:
            print(f"  FAIL render_contract: {len(findings)} finding(s) on {node_ids}")
            for f in findings[:8]:
                print(f"    - {f}")
            return False
        print(f"  PASS render_contract: 0 findings on {len(node_ids)} node(s)")
        return True

    if len(findings) > RENDER_FLOOR:
        print(f"  FAIL render_contract: {len(findings)} broken renders exceeds floor {RENDER_FLOOR}")
        for f in findings[:10]:
            print(f"    - {f}")
        return False
    print(f"  PASS render_contract: {len(findings)} broken renders (floor {RENDER_FLOOR})")
    if findings:
        print(f"    {len(findings)} payloads the student cannot render remain — content work:")
        for f in findings[:4]:
            print(f"      - {f[:110]}")
    return True


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§9 render contract")
    ap.add_argument("--node-ids", help="comma-separated subset; any finding fails")
    args = ap.parse_args()
    nodes = [n.strip() for n in args.node_ids.split(",")] if args.node_ids else None
    return 0 if validate_all(nodes) else 1


if __name__ == "__main__":
    sys.exit(main())
