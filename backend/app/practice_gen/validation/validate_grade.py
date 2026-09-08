"""
§10 — the grading contract: a correct answer must be graded correct, by every grader.

Why this exists
---------------
This is the worst defect class in the system: a pupil does the mathematics right and is
told they are wrong. Three graders serve answers -- the portal, Lab v1 and Lab v2 -- and
they can disagree with each other about the same submission. `tests/grader_roundtrip_auditor.py`
was written for exactly that (its docstring names Bug #002 fraction_shade portal=False vs
v1/v2=True, #003 cloze, #004 mcq value leniency) and was referenced by **zero gates** until
2026-08-28. It ran only when a human remembered.

Why this does not simply drive that auditor
-------------------------------------------
It spins a fresh `TestClient(app)` per node and writes a StudentProfile row per node: two
nodes cost 30 seconds, so the full tree is ~38 minutes of app startup, and it leaves DB
rows behind. It also samples by pinning each advertised formatter from a saved
`CompetencyConfiguration`, which is not the path a student takes -- the same blind spot
that let §9's auditor report a node CLEAN while it served an empty BarChart to every
student.

So this reuses that auditor's hard-won parts -- `_emit_correct`, the three route shapes,
the fallback-cache priming -- but drives them once, over the student path, with a single
client. The contract asserted is the one that matters: submit a KNOWN-CORRECT answer and
every grader must return is_correct=True.

Floors, not a hard zero
-----------------------
The baseline is what it is; Scaling Mandate §5 says a check whose baseline is already red
cannot be told from its noise. The floor may only SHRINK.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[4]

# §8 inventory: the assertions this module can independently fail on. Each must be
# proven by a mutation naming it in `Mutation.asserts`, or excused in
# validate_coverage.UNPROVEN_ASSERTIONS with a reason and a date.
ASSERTIONS = (
    "grading_contract_10",        # subset mode (--node-ids): any finding fails
    "grading_contract_floor_10",  # full tree measured against GRADE_FLOOR
)

# ZERO, as of 2026-09-08 (measured: 0 findings over all 151 nodes x 3 seeds, 14m23s).
#
# It stood at 5, all five real, and both causes were the same defect: an unrecognised
# format fell through to a comparison that could never match.
#   * portal and lab_v1 fell back to an MCQ *key* comparison, so a `sort_order` answer of
#     [10, 9, 8] was tested as "[10, 9, 8]" == "A". Four nodes. lab_v2 fell back to a
#     *value* comparison and was right -- three graders, three different defaults.
#   * lab_v1's ClockSet branch parsed the CORRECT answer leniently (digits only) but the
#     student's strictly (`int("35 p.m.")`), rejecting a byte-identical string.
# Both now route through services.scoring.answers_match, keyed off the answer's SHAPE
# rather than a list of format names -- `sort_order` was missing from lists that already
# contained `ordering`, and a grade 4-10 formatter returning a list would have hit it too.
#
# The floor is removed rather than shrunk for the reason §9's was: a floor at or above the
# real defect count makes the check UNPROVABLE. §9's mutation SURVIVED at floor 16 because
# 7 planted broken payloads still exited 0. A gate that cannot fail cannot be trusted.
GRADE_FLOOR = 0

SEEDS_PER_NODE = (11, 42, 64)


def collect_findings(node_ids: Optional[List[str]] = None) -> List[str]:
    """Every (node, seed) where a known-correct answer is not graded correct by all three."""
    sys.path.insert(0, str(REPO_ROOT))
    from fastapi.testclient import TestClient

    from backend.app.main import app
    from backend.app.database import SessionLocal
    from backend.app.models import StudentProfile
    from backend.app.practice_gen.registry import get_all_node_ids
    from backend.app.services.orchestrator import PracticeOrchestrator
    from backend.app.services.cache import _fallback_cache
    from tests.grader_roundtrip_auditor import _emit_correct

    # One student, one client, for the whole sweep -- the auditor made both per node.
    db = SessionLocal()
    try:
        name = "GraderGate_shared"
        s = db.query(StudentProfile).filter_by(name=name).first()
        if not s:
            s = StudentProfile(name=name, pin_hash="x", age=8, grade=3,
                               language_preference="en")
            db.add(s); db.commit(); db.refresh(s)
        sid = s.id
    finally:
        db.close()

    client = TestClient(app)
    findings: List[str] = []

    for node_id in (node_ids or get_all_node_ids()):
        for seed in SEEDS_PER_NODE:
            try:
                p = PracticeOrchestrator.generate_problem(
                    node_id=node_id, seed=seed, is_student_path=True
                )
            except Exception:
                continue  # generation failures belong to other stages
            d = p if isinstance(p, dict) else (
                p.model_dump() if hasattr(p, "model_dump") else dict(p.__dict__))
            pid = d.get("problem_id") or f"{node_id}_{seed}"
            for key in ("matatag:", "practice_gen_v2:", "practice_gen:"):
                _fallback_cache[key + pid] = d

            answer = _emit_correct(d)
            if answer is None:
                continue  # no derivable correct answer for this collection mode

            verdicts: Dict[str, Any] = {}
            try:
                verdicts["portal"] = client.post("/api/practice/submit", json={
                    "selected_answer": answer, "student_id": sid, "session_id": None,
                    "skill_id": node_id, "skeleton_id": pid, "stem": "",
                    "correct_answer": "", "response_time_ms": 5000,
                    "telemetry_flagged": False,
                }).json().get("is_correct")
            except Exception as exc:
                verdicts["portal"] = f"ERR:{type(exc).__name__}"
            try:
                as_str = json.dumps(answer) if isinstance(answer, (list, dict)) else str(answer)
                verdicts["lab_v1"] = client.post(
                    "/api/matatag/lab/submit",
                    params={"skeleton_id": pid, "student_answer": as_str},
                ).json().get("is_correct")
            except Exception as exc:
                verdicts["lab_v1"] = f"ERR:{type(exc).__name__}"
            try:
                verdicts["lab_v2"] = client.post(
                    "/api/matatag/lab/v2/submit",
                    json={"problem_id": pid, "student_answer": answer},
                ).json().get("is_correct")
            except Exception as exc:
                verdicts["lab_v2"] = f"ERR:{type(exc).__name__}"

            wrong = {k: v for k, v in verdicts.items() if v is not True}
            if wrong:
                findings.append(
                    f"{node_id} (seed {seed}): a KNOWN-CORRECT answer {answer!r} was not "
                    f"graded correct by {sorted(wrong)} -- verdicts {verdicts}. A pupil who "
                    f"does the mathematics right is told they are wrong."
                )
    return findings


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    findings = collect_findings(node_ids)

    if node_ids:
        if findings:
            print(f"  FAIL grading_contract_10: {len(findings)} finding(s) on {node_ids}")
            for f in findings[:8]:
                print(f"    - {f}")
            return False
        print(f"  PASS grading_contract_10: 0 findings on {len(node_ids)} node(s)")
        return True

    if len(findings) > GRADE_FLOOR:
        print(f"  FAIL grading_contract_floor_10: {len(findings)} mis-gradings exceeds "
              f"floor {GRADE_FLOOR}")
        for f in findings[:10]:
            print(f"    - {f}")
        return False
    print(f"  PASS grading_contract_floor_10: {len(findings)} mis-gradings (floor {GRADE_FLOOR})")
    return True


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§10 grading contract")
    ap.add_argument("--node-ids", help="comma-separated subset; any finding fails")
    args = ap.parse_args()
    nodes = [n.strip() for n in args.node_ids.split(",")] if args.node_ids else None
    return 0 if validate_all(nodes) else 1


if __name__ == "__main__":
    sys.exit(main())
