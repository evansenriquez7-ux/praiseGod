"""Pairwise-collapse probe: which declared variant VALUES render identically to each other?

For each declared value of a variant key, render the same seeds and compare the student-facing
output. Values that never render differently are not distinct capabilities, so a
CAPABILITY_PROVIDERS entry pointing at one is unearned even though the value genuinely exists
and is genuinely listed (hardening loop, Rule 9).

READ THIS BEFORE BELIEVING A COLLAPSE
-------------------------------------
Most collapses this probe finds are NOT defects. `is_student_path=True` applies the node's
competency-bound clamp, so a node whose bounds pin `task_type='compare_shapes'` renders that
task no matter which value you force -- the clamp is the pipeline working exactly as designed.

A collapse is only evidence of a defect when the key is NOT clamped for that node. The report
prints each key's competency bound alongside the result so the two cases cannot be confused;
`CLAMPED` lines are expected and are not findings.

The first run of this probe read four clamped keys as dead and briefly removed three earned
CAPABILITY_PROVIDERS entries on the strength of it. Before calling a key dead, census the
*unforced* student-path output and check whether the content appears anyway -- for
mat_g3_mg_q2_3 it did, with L in 103 of 200 seeds and mL in 97.
"""
import sys
from itertools import combinations
from backend.app.practice_gen.pipeline import run
from backend.app.practice_gen.compatibility import VARIANTS_BY_DNA
from backend.app.practice_gen.registry import NODE_TO_DNA, get_node_competency_bounds

SEEDS = [42, 43, 44, 45, 46, 47, 48, 49, 50, 51]

NODES = ["mat_g1_na_q1_0", "mat_g1_mg_q1_1", "mat_g2_na_q3_1",
         "mat_g3_mg_q1_5", "mat_g3_mg_q2_3", "mat_g3_dp_q3_1"]


class Gated(Exception):
    """The variant value is curriculum-gated off this node -- a correct refusal, not a defect."""


def sig(node, seed, key, value):
    try:
        p = run(node, seed=seed, difficulty_profile={key: value}, is_student_path=True)
    except ValueError as exc:
        # base_generator raises this by name when a grade/quarter gate forbids the value.
        # That is the pipeline working, so it is reported separately rather than counted as
        # a collapse. Any other ValueError is a real failure and propagates untouched.
        if "is not available at node" in str(exc):
            raise Gated(str(exc)) from exc
        raise
    return (p.get("question_text", ""), str(p.get("correct_answer")), str(p.get("visual_params")))


def main():
    total_collapsed = 0
    for node in NODES:
        bounds = get_node_competency_bounds(node) or {}
        keys = {}
        for dna in NODE_TO_DNA.get(node) or []:
            for k, vs in (VARIANTS_BY_DNA.get(dna) or {}).items():
                keys.setdefault(k, set()).update(vs)
        print(f"\n=== {node} ===")
        for key, values in sorted(keys.items()):
            values = sorted(values)
            if len(values) < 2:
                continue
            sigs, gated = {}, []
            for v in values:
                try:
                    sigs[v] = tuple(sig(node, s, key, v) for s in SEEDS)
                except Gated:
                    gated.append(v)
            live = [v for v in values if v in sigs]
            if len(live) < 2:
                print(f"  -- {key:18s} {len(values)} declared, {len(gated)} curriculum-gated "
                      f"-> too few reachable values to compare")
                continue
            collapsed = [(a, b) for a, b in combinations(live, 2) if sigs[a] == sigs[b]]
            distinct = len({tuple(x) for x in sigs.values()})
            bound = bounds.get(key, None)
            if distinct == len(live):
                mark, note = "ok     ", ""
            elif key in bounds:
                mark, note = "CLAMPED", f"  <- competency bound pins {key}={bound!r}; expected"
            else:
                mark, note = "!! DEAD", "  <- unclamped and collapsed: candidate defect"
            print(f"  {mark} {key:18s} {len(live)} reachable "
                  f"({len(gated)} gated) -> {distinct} distinct rendering(s){note}")
            if key not in bounds:
                for a, b in combinations(live, 2):
                    if sigs[a] == sigs[b]:
                        print(f"        collapsed: {a!r} == {b!r} on all {len(SEEDS)} seeds")
                total_collapsed += len(collapsed)
    print(f"\nunclamped collapsed value pairs (candidate defects): {total_collapsed}")
    print("clamped collapses are omitted above -- they are the competency bound working.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
