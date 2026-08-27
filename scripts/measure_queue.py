#!/usr/bin/env python3
"""
Print the hardening work queue, every band, from ONE measurement.

Why this exists
---------------
Both tick protocols used to carry their own inline measurement script: a ~25-line
heredoc that re-ran `validate_judgment` and `validate_capability` and printed the
bands. The preflight supervisor had already run the same two validators seconds
earlier. So every tick paid for the queue twice (~54s), and -- far worse -- there
were two implementations of the question "what work is outstanding?" that could
disagree.

They did disagree, in the way that matters. The inline script counted stages 7 and 8.
The supervisor's verdict counted stage 8 alone. Neither counted stage 6, the §1
behavioural matrix. On 2026-08-26 a live §1C `empty_execution_matrix` on
mat_g3_na_q3_1 -- a node that renders no problems at all and would still report PASS --
was invisible to both, while 455 consecutive ticks optimised a 158-item queue that was
really 735.

One measurement, one definition, every band. The supervisor computes it during preflight
and writes it to the status file; this reads that file back and refuses it if it is not
current.

Usage
-----
    PYTHONPATH=. .venv/bin/python3 scripts/measure_queue.py           # read preflight's
    PYTHONPATH=. .venv/bin/python3 scripts/measure_queue.py --force   # measure now
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATUS = REPO / "local_only/scratch/hardening_status.json"
SUPERVISOR = REPO / "scripts/hardening_supervisor.py"

# A measurement is "the queue right now". Past this age it is a memory, and the tick
# protocol's rule is that the queue is never remembered. Preflight runs immediately
# before the tick, so a current status is seconds old, not minutes.
MAX_STATUS_AGE_SEC = 600


def _measure_now() -> None:
    """Re-run the supervisor so it rewrites the status file, then fall through to read it."""
    subprocess.run(
        [sys.executable, str(SUPERVISOR), "--reap"],
        cwd=REPO, capture_output=True, text=True,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true",
                    help="re-run the supervisor instead of reading preflight's measurement")
    args = ap.parse_args()

    if args.force or not STATUS.exists():
        _measure_now()

    if not STATUS.exists():
        print("FATAL: no status file and the supervisor did not produce one.", file=sys.stderr)
        return 2

    st = json.loads(STATUS.read_text(encoding="utf-8"))
    age = time.time() - STATUS.stat().st_mtime
    if age > MAX_STATUS_AGE_SEC:
        print(f"status is {int(age)}s old (limit {MAX_STATUS_AGE_SEC}s) — re-measuring.",
              file=sys.stderr)
        _measure_now()
        st = json.loads(STATUS.read_text(encoding="utf-8"))
        # Recompute: reporting the pre-refresh age would describe the measurement we
        # just threw away.
        age = time.time() - STATUS.stat().st_mtime

    bands = st.get("bands")
    m = st.get("matrix_evidence")
    if bands is None or m is None:
        print("FATAL: the capability contract did not evaluate — this is a CLASS C repair "
              "and the tick's only unit. Nothing here can be measured until it is fixed.",
              file=sys.stderr)
        return 2

    def row(label: str, key: str) -> str:
        b = bands[key]
        return f"{label:<28}: {b['n']:4d}  across {b['nodes']:3d} nodes"

    # §1 leads because it is the band that outranks the others: it is the only one that
    # asserts the rendered content is correct at all.
    trust = "" if m["trusted"] else f"   <-- {m['state']}, NOT counted in the total"
    print(f"§1  matrix failures (6/8)   : {m['findings']:4d}"
          f"  across {m['total'] - 0:3d} nodes checked{trust}")
    print(f"    matrix evidence         : {m['state']} "
          f"({m['covered']}/{m['total']} nodes covered)")
    if not m["trusted"]:
        print("    >>> §1 IS UNMEASURED. Refresh it before trusting any zero below:")
        print("    >>> PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.validate_matrix")
    print(row("§5  STALE/malformed reviews", "5_stale_reviews"))
    print(row("§5  non-PASS verdicts", "5_non_pass"))
    print(row("§6F CONTRADICTED", "6F_contradicted"))
    print(row("§6F stale attestations", "6F_stale_attest"))
    print(row("§6F UNATTESTED", "6F_unattested"))
    print(row("§6D wildcard providers", "6D_wildcards"))
    print(f"    6D worst first          : {bands['6D_wildcards']['worst']}")
    print(f"TOTAL findings              : {st['findings_total']}   (the work queue, not the score)")
    print(f"tally: {st.get('verdict_tally')}")
    print(f"measured at {st['checked_at']} ({int(age)}s ago)")

    cov = st.get("coverage") or {}
    if cov:
        print(f"COVERAGE (the goal): attested {cov.get('capabilities_attested')}/"
              f"{cov.get('capabilities_total')} ({cov.get('attested_pct')}%) | "
              f"reviewed {cov.get('nodes_reviewed')}/{cov.get('nodes_total')} | "
              f"mutations {cov.get('mutations_registered')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
