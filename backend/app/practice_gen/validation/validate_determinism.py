"""
Practice Generation — A Seed Reproduces the Same Problem in Every Process (§18; owner ruling 54)

Every finding the harness reports names a seed (ruling 52) so a generator agent can
reproduce it. That promise holds only if `generate_problem(node_id, seed, ...)` serves the
same problem in every Python process. It did not: iterating a `set` of strings follows
`PYTHONHASHSEED`, and measured on 2026-10-17 81 of the 7,285 `validate_slots.paths()`
renders differed between PYTHONHASHSEED=0 and 12345, all on the four comparing_ordering lcs,
in the order of `distractors`. `tests/render_snapshot.py` pinned the hash seed to make its
own diff exact; nothing asserted that a served problem is the same across processes.

This stage renders every path (student seeds 1-40 plus every advertised formatter pinned at
seeds 3, 17 and 29; the same `validate_slots.paths()` §14 and §17 use) in two child
processes, one per hash seed in HASH_SEEDS, through `tests.render_snapshot` (the full
`FormattedProblem.model_dump()`, a raised render recorded as its exception), and compares
them path by path.

  render_hash_order_dependent_18   CONTENT. One finding per path whose two renders differ,
                                   named by lc + seed (+ formatter) + the differing fields +
                                   owed build.
  determinism_harness_18           INTEGRITY. A child process failed, or the two children
                                   enumerated different paths, so the comparison is not of
                                   like with like.

NAMED LIMITS (Scaling Mandate 6; also in the contract's §18 row):
  1. **Two hash seeds, not all of them.** An order that happens to agree under 0 and 12345
     is not seen; a third seed would cost a third render pass.
  2. **These paths and the default experience only** (render_snapshot's own limit): a
     dependence reachable only on another seed, difficulty profile or interest is not seen.
  3. **Hash order only.** Other cross-process nondeterminism (wall-clock time, os.environ,
     filesystem order) is caught only where it happens to differ between the two children,
     which run at nearly the same moment on the same machine.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ASSERTIONS = (
    "render_hash_order_dependent_18",  # a path renders differently under two PYTHONHASHSEEDs
    "determinism_harness_18",          # a child failed or the two path sets differ (integrity)
)

HASH_SEEDS = ("0", "12345")
_REPO_ROOT = Path(__file__).resolve().parents[4]
_CHILD = ("import sys; from tests.render_snapshot import snapshot; "
          "sys.exit(snapshot(sys.argv[1], sys.argv[2].split(',') if sys.argv[2] else None))")


def _diff_paths(a: Any, b: Any, where: str = "") -> List[str]:
    """The dotted paths at which two JSON values differ (lists compared whole)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out: List[str] = []
        for key in sorted(set(a) | set(b)):
            out += _diff_paths(a.get(key), b.get(key), f"{where}.{key}" if where else key)
        return out
    return [] if a == b else [where or "(root)"]


def _render_all(node_ids: Optional[List[str]], tmp: Path) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """{hash seed: {path key: render}} from one child per hash seed, run concurrently."""
    procs = []
    for hs in HASH_SEEDS:
        out = tmp / f"renders_{hs}.jsonl"
        env = {**os.environ, "PYTHONHASHSEED": hs, "PYTHONPATH": str(_REPO_ROOT)}
        procs.append((hs, out, subprocess.Popen(
            [sys.executable, "-c", _CHILD, str(out), ",".join(node_ids or [])],
            cwd=_REPO_ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
    renders: Dict[str, Dict[str, Any]] = {}
    problems: List[str] = []
    for hs, out, proc in procs:
        log, _ = proc.communicate()
        if proc.returncode != 0 or not out.exists():
            problems.append(f"the PYTHONHASHSEED={hs} render child exited {proc.returncode}: "
                            f"{log.strip()[-400:]!r}. Owed: fix the harness (tests.render_snapshot).")
            continue
        with open(out, encoding="utf-8") as fh:
            renders[hs] = {json.dumps(row["k"]): row["r"] for row in map(json.loads, fh)}
    return renders, problems


def collect_findings(node_ids: Optional[List[str]] = None) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    from backend.app.practice_gen.validation.validate_slots import path_call

    out: Dict[str, List[str]] = {label: [] for label in ASSERTIONS}
    with tempfile.TemporaryDirectory(prefix="determinism18_") as tmp:
        renders, problems = _render_all(node_ids, Path(tmp))
    out["determinism_harness_18"] += problems
    stats = {"paths": 0}
    if problems:
        return out, stats
    first, second = (renders[hs] for hs in HASH_SEEDS)
    if set(first) != set(second):
        out["determinism_harness_18"].append(
            f"the two render children enumerated different paths ({len(set(first) ^ set(second))} "
            f"on one side only), so they cannot be compared. Owed: fix the harness "
            f"(validate_slots.paths must not depend on hash order).")
        return out, stats
    stats["paths"] = len(first)
    for key in sorted(first, key=lambda k: (json.loads(k)[0], json.loads(k)[1], str(json.loads(k)[2]))):
        if first[key] == second[key]:
            continue
        node_id, seed, formatter = json.loads(key)
        fields = _diff_paths(first[key], second[key])
        out["render_hash_order_dependent_18"].append(
            f"{node_id}: seed {seed}{'' if formatter is None else f' formatter {formatter!r}'} renders "
            f"differently under PYTHONHASHSEED={HASH_SEEDS[0]} and {HASH_SEEDS[1]} in {fields[:6]}"
            f"{' ...' if len(fields) > 6 else ''}: a seed does not reproduce this problem in another "
            f"process. Reproduce: PYTHONHASHSEED=<n> {path_call(node_id, seed, formatter)}. Owed: make "
            f"the generator's choice and order independent of hash order (iterate a list or a sorted "
            f"set, never a bare set of strings).")
    return out, stats


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    findings, stats = collect_findings(node_ids)
    total = 0
    for label in ASSERTIONS:
        items = findings[label]
        total += len(items)
        if items:
            print(f"  FAIL {label} ({len(items)}):")
            for item in items:  # every finding, by name (ruling 23)
                print(f"    - {item}")
        else:
            print(f"  PASS {label}")
    print(f"  §18: {stats['paths']} path(s) rendered under PYTHONHASHSEED {' and '.join(HASH_SEEDS)}; "
          f"{len(findings['render_hash_order_dependent_18'])} differ")
    return total == 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§18 a seed reproduces the same problem in every process")
    ap.add_argument("--node-ids", help="comma-separated lc subset (proof mode)")
    args = ap.parse_args()
    return 0 if validate_all(args.node_ids.split(",") if args.node_ids else None) else 1


if __name__ == "__main__":
    sys.exit(main())
