"""Regenerate _generated_formatter_exclusions.py by asking the orchestrator.

    PYTHONPATH=. .venv/bin/python3 -m scripts.regen_formatter_exclusions

Empirical on purpose: three attempts to model the orchestrator's eligibility rules
statically all drifted from it. A pair is excluded only if it is refused at EVERY probe
seed, so a seed-dependent refusal never lands here.

FIXED 2026-08-21. The first version of this script did not work, in two independent ways,
and had never been executed:

  * it imported `COMPATIBILITY_FORMATTERS_FOR_NODE` from registry, which does not exist
    -- so it died with ImportError before probing a single pair; and
  * it had no write of any kind. It computed the map, printed a count, and returned. The
    `from pathlib import Path` at the top was never used.

Both matter more than a broken helper usually would, because §2B's own failure message
names this command as the remedy: a node whose exclusion had gone stale told the reader
to run a script that could not run. And the file it "generates" carries a DO NOT EDIT BY
HAND banner, so the map was hand-maintained under a generated label with no way to check
it against the orchestrator. Regeneration must actually happen for the narrowing to be
safe in either direction.

The union is recomputed from COMPATIBILITY directly rather than from
`get_node_formatters()`, which subtracts the very map being written. Using it would make
regeneration a function of its own previous output: once a pair was wrongly excluded it
would never be probed again, and the error would be permanent and self-confirming.
"""
from __future__ import annotations

import collections
from pathlib import Path

PROBE_SEEDS = (11, 23, 42, 57, 64, 78, 91, 103, 118, 127, 555, 999)

TARGET = Path(__file__).resolve().parents[1] / (
    "backend/app/practice_gen/_generated_formatter_exclusions.py"
)

# Everything above the assignment is prose that explains the file; regeneration rewrites
# only the data. Splitting on the assignment keeps the rationale from being lost every
# time the map moves.
_ASSIGN = "NODE_FORMATTER_EXCLUSIONS: Dict[str, List[str]] = {"


def compute() -> tuple[dict[str, list[str]], list[str]]:
    """Returns (exclusions, broken) -- broken = pairs that raise a NON-eligibility error."""
    from backend.app.practice_gen.compatibility import COMPATIBILITY
    from backend.app.practice_gen.registry import NODE_TO_DNA, get_node_dnas
    from backend.app.services.orchestrator import PracticeOrchestrator

    excl: dict[str, list[str]] = collections.defaultdict(list)
    broken: list[str] = []

    for node_id in NODE_TO_DNA:
        seen: set[str] = set()
        union: list[str] = []
        for dna in get_node_dnas(node_id):
            for fmt in COMPATIBILITY.get(dna, []):
                if fmt not in seen:
                    seen.add(fmt)
                    union.append(fmt)

        for fmt in union:
            refused_every_seed = True
            other_error = None
            for seed in PROBE_SEEDS:
                try:
                    PracticeOrchestrator.generate_problem(
                        node_id=node_id, seed=seed, formatter=fmt, is_lab=False,
                    )
                    refused_every_seed = False
                    break
                except Exception as exc:  # noqa: BLE001
                    # Only an ELIGIBILITY refusal is an exclusion. A content-level crash
                    # means the pair is offered and broken, which is §1C's business --
                    # but it is reported here rather than silently treated as servable,
                    # because "it raised, so it is not excluded" reads identically to
                    # "it worked" in the output and that is how a broken pair stays
                    # advertised forever.
                    if "is not supported by any DNA" not in str(exc):
                        refused_every_seed = False
                        other_error = f"{node_id}/{fmt} seed={seed}: {type(exc).__name__}: {exc}"
                        break
            if refused_every_seed:
                excl[node_id].append(fmt)
            elif other_error:
                broken.append(other_error)

    return dict(excl), broken


def main() -> int:
    excl, broken = compute()

    header = TARGET.read_text(encoding="utf-8").split(_ASSIGN)[0]
    body = "".join(
        f"    {node_id!r}: {sorted(excl[node_id])!r},\n" for node_id in sorted(excl)
    )
    TARGET.write_text(f"{header}{_ASSIGN}\n{body}}}\n", encoding="utf-8")

    total = sum(len(v) for v in excl.values())
    print(f"{total} exclusions across {len(excl)} nodes -> {TARGET.name}")
    if broken:
        print(f"\n{len(broken)} advertised pair(s) raise a NON-eligibility error (§1C's queue):")
        for line in broken:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
