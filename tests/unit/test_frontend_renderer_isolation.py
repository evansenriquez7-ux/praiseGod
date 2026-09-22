"""§12/§5/§6F — two concurrent renderer invocations may not contaminate each other.

WHY TWO SEPARATE DIRECTIONS AND NOT ONE END-TO-END TEST
-------------------------------------------------------
`tests/frontend_renderer.py` had two independent defects, and they mask each other, so a
single end-to-end assertion proves neither:

  * a FIXED corpus/result path shared by every invocation (the loud one: two runs overwrite
    each other, the id sets disagree, and the existing `set(active) != set(by_id)` guard
    raises);
  * a `case_id` of `packet-{index}-seed-{seed}` that OMITTED `node_id` (the silent one: two
    different nodes mint the SAME id, so when two runs collide the id sets can coincide
    while the rendered structure belongs to the other process -- the loud guard passes and
    one run attaches the other's visual evidence).

Measured cost of the silent half before it was fixed: §6F reported 55 findings under
concurrent load on a tree that had 61, against 61 on three clean runs -- no crash and no
warning.

CORRECTED 2026-09-22: this docstring originally also cited "§5 reported 1253 where it has
1252" as a second corrupted figure. That was MISATTRIBUTED and is NOT this defect. The §5
difference is `run_all._stage_judgment_reviews_5` appending one aggregate finding the
module's own CLI never emits, so 1252 (module) and 1253 (stage) are both correct for their
entry point. The §6F symptom above is the one this test exists for.

Unique directories alone make the end-to-end behaviour correct EVEN WITH the colliding id
space restored -- which is exactly why a mutation that reverts `case_id` would survive an
end-to-end test. Each half is therefore asserted on its own invariant, against the real
code path, with the real Node renderer executing.

KNOWN LIMITATION (Scaling Mandate 6): these tests observe the corpus the module actually
hands to Node by wrapping `subprocess.run`, not by re-deriving the id in the test. That is
deliberate -- re-deriving it here would be a second copy of the rule, which is how two
copies come to disagree. What it does NOT prove is that the operating system gives two
processes distinct pids; `uuid4` is what carries that case, and it is not independently
asserted here.
"""
from __future__ import annotations

import json
import subprocess
import threading

from tests import frontend_renderer
from tests.frontend_renderer import SCRATCH, attach_rendered_visual_descriptions


def _sample(node_id: str, kind: str, labels, seed: int = 11) -> dict:
    return {
        "seed": seed,
        "node_id": node_id,
        "visual_type": "GeometryFigure",
        "_visual_params": {"kind": kind, "labels": labels},
    }


def _record_invocations(monkeypatch):
    """Capture the corpus path and contents of every real Node invocation."""
    seen = []
    real_run = subprocess.run

    def wrapper(command, **kwargs):
        corpus_path = command[-2]
        seen.append({
            "corpus_path": corpus_path,
            "cases": json.loads(open(corpus_path, encoding="utf-8").read())["cases"],
        })
        return real_run(command, **kwargs)

    monkeypatch.setattr(frontend_renderer.subprocess, "run", wrapper)
    return seen


def test_two_nodes_at_the_same_index_and_seed_do_not_share_a_case_id(monkeypatch):
    """THE SILENT PATH. Index and seed alone do not identify a packet -- the node does.

    Two invocations, each rendering ONE sample, so both sit at index 0 with the same seed.
    Before the fix both minted `packet-0-seed-11`, and an id that two different nodes can
    both produce is what lets one run's evidence be joined onto another run's samples.
    """
    seen = _record_invocations(monkeypatch)
    attach_rendered_visual_descriptions([_sample("mat_g3_gm_q1_0", "triangle", ["A", "B", "C"])])
    attach_rendered_visual_descriptions([_sample("mat_g1_na_q1_0", "point", ["P"])])

    assert len(seen) == 2, seen
    first, second = seen[0]["cases"][0]["case_id"], seen[1]["cases"][0]["case_id"]
    assert first != second, (
        f"two different nodes at index 0 seed 11 both minted case_id {first!r}: "
        "a colliding id lets a concurrent run's rendered structure be attached to these "
        "samples while the set-equality guard still passes"
    )
    assert "mat_g3_gm_q1_0" in first and "mat_g1_na_q1_0" in second, (first, second)


def test_each_invocation_renders_in_its_own_directory(monkeypatch):
    """THE LOUD PATH. Two invocations may not share a corpus or a result file."""
    seen = _record_invocations(monkeypatch)
    attach_rendered_visual_descriptions([_sample("mat_g3_gm_q1_0", "triangle", ["A", "B", "C"])])
    attach_rendered_visual_descriptions([_sample("mat_g1_na_q1_0", "point", ["P"])])

    paths = [row["corpus_path"] for row in seen]
    assert paths[0] != paths[1], f"both invocations wrote the same corpus path: {paths[0]}"
    for path in paths:
        assert str(SCRATCH) in path, path


def test_concurrent_invocations_each_receive_their_own_evidence():
    """The behaviour the two invariants exist to protect, under real concurrency.

    A triangle and a point are not confusable: 3 endpoints against 1. If either run picked
    up the other's markup, the role counts say so.
    """
    results: dict = {}
    errors: list = []

    def run(node_id, kind, labels):
        try:
            out = attach_rendered_visual_descriptions([_sample(node_id, kind, labels)])
            results[node_id] = out[0]["visual_render"]["description"]["role_counts"]
        except Exception as exc:  # recorded, then re-raised by the assertion below
            errors.append(f"{node_id}: {exc}")

    threads = [
        threading.Thread(target=run, args=("mat_g3_gm_q1_0", "triangle", ["A", "B", "C"])),
        threading.Thread(target=run, args=("mat_g1_na_q1_0", "point", ["P"])),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors
    assert results["mat_g3_gm_q1_0"].get("endpoint") == 3, results
    assert results["mat_g1_na_q1_0"].get("endpoint") == 1, results


def test_a_successful_render_leaves_no_directory_behind():
    """Scratch is cleaned on the success path; a FAILED render keeps its directory on
    purpose, so the corpus that produced the failure survives for diagnosis."""
    before = set(SCRATCH.glob("run-*")) if SCRATCH.exists() else set()
    attach_rendered_visual_descriptions([_sample("mat_g3_gm_q1_0", "triangle", ["A", "B", "C"])])
    after = set(SCRATCH.glob("run-*")) if SCRATCH.exists() else set()
    assert after == before, f"left behind: {sorted(str(p) for p in after - before)}"
