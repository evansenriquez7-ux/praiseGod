"""Differential probe: does forcing a variant value actually change the rendered problem?

CAPABILITY_PROVIDERS claims a capability is provided when the node can *reach* a
(key, value). Reachability is checked against VARIANTS_BY_DNA, which is a declaration.
This renders the same seed under each declared value of the key and reports whether the
student-facing output differs at all. Identical output across every value means the key
is consumed by nobody -- defect shape #1, "key consumed but never bound".
"""
import sys
from backend.app.practice_gen.pipeline import run
from backend.app.practice_gen.compatibility import VARIANTS_BY_DNA
from backend.app.practice_gen.registry import NODE_TO_DNA

SEEDS = [42, 43, 44, 45, 46, 47, 48, 49]

TARGETS = [
    ("mat_g1_mg_q1_1", "task_type"),
    ("mat_g1_mg_q1_1", "shape_set"),
    ("mat_g1_na_q1_0", "direction"),
    ("mat_g3_mg_q2_3", "unit"),
    ("mat_g3_mg_q2_3", "task_type"),
    ("mat_g3_mg_q2_3", "measurement_type"),
    ("mat_g3_dp_q3_1", "orientation"),
    ("mat_g3_dp_q3_1", "task_type"),
]


def render_signature(node, seed, key, value):
    p = run(node, seed=seed, difficulty_profile={key: value}, is_student_path=True)
    return (
        p.get("question_text", ""),
        str(p.get("correct_answer")),
        str(p.get("visual_params")),
    )


def main():
    dead = []
    for node, key in TARGETS:
        values = []
        for dna in NODE_TO_DNA.get(node) or []:
            values += (VARIANTS_BY_DNA.get(dna) or {}).get(key) or []
        values = sorted(set(values))
        if len(values) < 2:
            print(f"SKIP {node} {key}: fewer than two declared values ({values})")
            continue

        differed_on = []
        for seed in SEEDS:
            sigs = {v: render_signature(node, seed, key, v) for v in values}
            if len(set(sigs.values())) > 1:
                differed_on.append(seed)

        status = "BOUND  " if differed_on else "**DEAD**"
        print(f"{status} {node:18s} {key:18s} values={values}")
        print(f"          output differs on seeds: {differed_on or 'NONE — every value renders identically'}")
        if not differed_on:
            dead.append((node, key, values))
            # show the identical rendering so the claim is inspectable
            q, a, _ = render_signature(node, SEEDS[0], key, values[0])
            print(f"          seed={SEEDS[0]} stem (same for all {len(values)} values): {q[:150]}")
            print(f"          answer: {a}")

    print(f"\nkeys declared but never bound: {len(dead)}")
    for node, key, values in dead:
        print(f"  - {node}: {key!r} declares {values} but no value changes the output")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
