"""Regenerate _generated_formatter_exclusions.py by asking the orchestrator.

    PYTHONPATH=. .venv/bin/python3 -m scripts.regen_formatter_exclusions

Empirical on purpose: three attempts to model the orchestrator's eligibility rules
statically all drifted from it. A pair is excluded only if it is refused at EVERY probe
seed, so a seed-dependent refusal never lands here.
"""
from __future__ import annotations
import collections
from pathlib import Path

PROBE_SEEDS = (11, 23, 42, 57, 64, 78, 91, 103, 118, 127, 555, 999)


def main() -> int:
    from backend.app.services.orchestrator import PracticeOrchestrator
    from backend.app.practice_gen.registry import NODE_TO_DNA, COMPATIBILITY_FORMATTERS_FOR_NODE

    excl: dict[str, list[str]] = collections.defaultdict(list)
    for node_id in NODE_TO_DNA:
        for fmt in COMPATIBILITY_FORMATTERS_FOR_NODE(node_id):
            refused_every_seed = True
            for seed in PROBE_SEEDS:
                try:
                    PracticeOrchestrator.generate_problem(
                        node_id=node_id, seed=seed, formatter=fmt, is_lab=False)
                    refused_every_seed = False
                    break
                except Exception as exc:  # noqa: BLE001
                    if "is not supported by any DNA" not in str(exc):
                        refused_every_seed = False
                        break
            if refused_every_seed:
                excl[node_id].append(fmt)
    print(f"{sum(len(v) for v in excl.values())} exclusions across {len(excl)} nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
