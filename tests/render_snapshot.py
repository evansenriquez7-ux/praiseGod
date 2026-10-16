"""
Byte-identity snapshot of learner-facing renders (H3, owner ruling 28).

Ruling 28: emitting structured slots is instrumentation and "must not change any rendered
byte". This writes one JSON line per render -- the full `FormattedProblem.model_dump()` --
over (a) the student path for every lc at 40 seeds and (b) every (lc, formatter) pair the
registry advertises, pinned, at 3 seeds. Run it before and after an instrumentation change
and diff the two files; any difference is a changed byte.

    PYTHONPATH=. .venv/bin/python -m tests.render_snapshot OUT.jsonl
    PYTHONPATH=. .venv/bin/python -m tests.render_snapshot --diff BEFORE.jsonl AFTER.jsonl

A render that RAISES is recorded as its exception type and message, so a change that makes
a render start or stop failing is a difference too. NAMED LIMIT: it covers these seeds and
the default experience only; a byte change reachable only elsewhere is not seen.
"""
from __future__ import annotations

import json
import sys

# The paths are §14's own enumeration (`validate_slots.paths`, owner ruling 44b): the student
# path at seeds 1-40 and every advertised formatter pinned at seeds 3, 17, 29. One copy.


def _render(node_id, seed, formatter=None):
    from backend.app.services.orchestrator import PracticeOrchestrator as PO
    try:
        p = PO.generate_problem(node_id=node_id, seed=seed, formatter=formatter,
                                is_student_path=formatter is None)
        return p.model_dump()
    except Exception as exc:  # noqa: BLE001 - a raise is recorded, not swallowed
        return {"__raised__": f"{type(exc).__name__}: {exc}"}


def snapshot(out_path: str, node_ids=None) -> int:
    """Every path of `node_ids` (default: every lc), one JSON line each, to `out_path`.

    `node_ids` scopes a §18 determinism proof (validate_determinism --node-ids) to a clean lc.
    """
    from backend.app.practice_gen.registry import get_all_node_ids
    from backend.app.practice_gen.validation.validate_slots import paths
    n = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for node_id in sorted(node_ids or get_all_node_ids()):
            for seed, formatter in paths(node_id):
                fh.write(json.dumps({"k": [node_id, seed, formatter],
                                     "r": _render(node_id, seed, formatter)},
                                    sort_keys=True, default=str, ensure_ascii=False) + "\n")
                n += 1
    print(f"render_snapshot: wrote {n} render(s) to {out_path}")
    return 0


def diff(before: str, after: str) -> int:
    def load(path):
        with open(path, encoding="utf-8") as fh:
            return {json.dumps(json.loads(line)["k"]): line for line in fh}
    a, b = load(before), load(after)
    keys_changed = sorted(set(a) ^ set(b))
    changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    print(f"render_snapshot diff: {len(a)} before, {len(b)} after, {len(changed)} changed, "
          f"{len(keys_changed)} key(s) present on one side only")
    for k in (changed + keys_changed)[:20]:
        print(f"  - {k}")
    return 1 if changed or keys_changed else 0


if __name__ == "__main__":
    # Pin hash randomisation, or the comparison is not exact. MEASURED 2026-10-10: two
    # unpinned snapshots of identical code differed on 89 of 7,285 renders -- the order of
    # `distractors` (and `given_values.distractors`) on the four comparing_ordering lcs
    # (mat_g1_na_q1_4, mat_g1_na_q2_0, mat_g2_na_q1_4, mat_g3_na_q1_6) follows
    # PYTHONHASHSEED. That is a generator determinism defect (reported, not fixed here: owner
    # ruling 23) and a harness blind spot -- nothing asserts a served FormattedProblem is the
    # same across processes. Pinning makes this tool's diff exact; it does not close either.
    import os
    if sys.argv[1:2] != ["--diff"] and os.environ.get("PYTHONHASHSEED") != "0":
        os.execve(sys.executable, [sys.executable, "-m", "tests.render_snapshot", *sys.argv[1:]],
                  {**os.environ, "PYTHONHASHSEED": "0"})
    if sys.argv[1:2] == ["--diff"]:
        sys.exit(diff(sys.argv[2], sys.argv[3]))
    sys.exit(snapshot(sys.argv[1]))
