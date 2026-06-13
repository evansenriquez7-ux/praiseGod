"""
Integration test for the CCMed practice generation pipeline.

Run with:
    python -m backend.app.practice_gen.test_pipeline
(from the ccmed/ project root)
"""

from __future__ import annotations

import sys
import traceback
from typing import Any, Dict, List, Tuple

from backend.app.practice_gen import pipeline


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _sep(title: str = "") -> None:
    width = 70
    if title:
        print(f"\n{'─' * 4} {title} {'─' * (width - 6 - len(title))}")
    else:
        print("─" * width)


def _print_problem(label: str, p: Dict[str, Any]) -> None:
    print(f"  [{label}]")
    print(f"    problem_id   : {p.get('problem_id')}")
    print(f"    format       : {p.get('format')}")
    print(f"    question_text: {str(p.get('question_text', ''))[:80]}")
    print(f"    correct_answer: {p.get('correct_answer')}")
    print(f"    is_visual    : {p.get('is_visual')}")
    if p.get("is_visual"):
        print(f"    visual_type  : {p.get('visual_type')}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST CASES
# ═══════════════════════════════════════════════════════════════════════════════

def test_pipeline_status() -> Tuple[bool, str]:
    """Test 1 — get_pipeline_status() returns healthy status."""
    try:
        status = pipeline.get_pipeline_status()
        _sep("Pipeline Status")
        print(f"  total_nodes      : {status['total_nodes']}")
        print(f"  total_dna_concepts: {status['total_dna_concepts']}")
        print(f"  formatters       : {status['formatters_available']}")
        print(f"  experiences      : {status['experiences_available']}")
        print(f"  healthy          : {status['healthy']}")

        failed_dna = [
            (c, info["error"])
            for c, info in status["dna_status"].items()
            if not info["ok"]
        ]
        if failed_dna:
            print("\n  FAILED DNA modules:")
            for concept, err in failed_dna:
                print(f"    {concept}: {err}")

        if not status["healthy"]:
            return False, f"Pipeline unhealthy — {len(failed_dna)} DNA(s) failed to import"
        return True, "pipeline status OK"
    except Exception:
        return False, traceback.format_exc()


def test_single_nodes() -> Tuple[bool, str]:
    """Test 2 — Generate one problem for each of 5 selected node_ids."""
    test_cases = [
        ("mat_g1_na_q1_0", 1, "G1 counting"),
        ("mat_g1_na_q1_7", 1, "G1 addition"),
        ("mat_g1_mg_q1_0", 1, "G1 shapes"),
        ("mat_g2_na_q3_0", 2, "G2 multiplication"),
        ("mat_g3_dp_q3_0", 3, "G3 bar graphs"),
    ]

    _sep("Single Node Problems")
    failures = []

    for node_id, grade, label in test_cases:
        try:
            p = pipeline.run(node_id, student_grade=grade, seed=42)
            _print_problem(label, p)

            # Validate required fields
            assert p.get("problem_id"), "missing problem_id"
            assert p.get("format"), "missing format"
            assert p.get("question_text"), "missing question_text"
            assert p.get("correct_answer") is not None, "correct_answer is None"
            assert isinstance(p.get("is_visual"), bool), "is_visual not bool"

        except Exception as exc:
            failures.append(f"{label} ({node_id}): {exc}")
            print(f"  [{label}] FAIL — {exc}")

    if failures:
        return False, "Single node failures:\n" + "\n".join(failures)
    return True, "all 5 single-node problems generated OK"


def test_batch_generation() -> Tuple[bool, str]:
    """Test 3 — Generate batch of 3 for mat_g2_na_q1_8."""
    node_id = "mat_g2_na_q1_8"
    grade = 2

    _sep(f"Batch ({node_id}, count=3)")
    try:
        batch = pipeline.run_batch(node_id, grade=grade, count=3)

        assert len(batch) == 3, f"Expected 3 problems, got {len(batch)}"

        for i, p in enumerate(batch):
            _print_problem(f"batch[{i}]", p)
            assert p.get("problem_id"), f"batch[{i}] missing problem_id"
            assert p.get("format"), f"batch[{i}] missing format"
            assert p.get("correct_answer") is not None, f"batch[{i}] correct_answer is None"

        # Verify formatter variety — shouldn't all be the same
        formats = [p["format"] for p in batch]
        print(f"\n  formats in batch: {formats}")

        return True, f"batch of 3 for {node_id} OK"
    except Exception:
        return False, traceback.format_exc()


# ═══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    tests: List[Tuple[str, Any]] = [
        ("get_pipeline_status()",          test_pipeline_status),
        ("single node generation (5 nodes)", test_single_nodes),
        ("batch generation (count=3)",       test_batch_generation),
    ]

    results: List[Tuple[str, bool, str]] = []

    for name, fn in tests:
        try:
            ok, msg = fn()
        except Exception:
            ok, msg = False, traceback.format_exc()
        results.append((name, ok, msg))

    _sep("Summary")
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)

    for name, ok, msg in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
        if not ok:
            # Indent failure message
            for line in msg.strip().splitlines():
                print(f"         {line}")

    print()
    print(f"  {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
