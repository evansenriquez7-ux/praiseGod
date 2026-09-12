"""
§10 — the grading contract, in BOTH directions, hermetically.

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
client.

THE SECOND DIRECTION, ADDED 2026-09-12 (H-01)
---------------------------------------------
Until this date the check submitted a KNOWN-CORRECT answer and asserted acceptance, and
nothing else. An **always-true grader passed it perfectly**: mark every submission
correct and every assertion here is satisfied. Half of a grading contract is not a
grading contract, and the missing half is the one that lets a pupil pass without learning.

Four obligations now run against every sample, each reported under its own assertion:

  * ACCEPT      -- the known-correct answer is graded correct by all three graders.
  * REFUSE      -- a KNOWN-WRONG answer (`_emit_wrong`) and a MALFORMED submission
                   (`_emit_malformed`) are graded correct by NONE of them.
  * EQUIVALENCE -- a whitespace-padded rendering of the correct answer is still accepted.
                   Bounded deliberately; see KNOWN LIMITATIONS.
  * OBLIGATION  -- every (node, seed) pair either executes all of the above or fails BY
                   NAME. The previous version answered a generation crash and an
                   underivable answer with `continue`, so a node that could not be
                   exercised at all was indistinguishable from a node that passed.

HERMETIC, AND WHY THAT IS A CORRECTNESS PROPERTY RATHER THAN HYGIENE
--------------------------------------------------------------------
This check used to open `SessionLocal()` -- the CONFIGURED database, a Neon host reached
over the public internet -- and write a shared `GraderGate_shared` learner into it. On
2026-09-12 the identical code crashed the entire Phase 1 run (`could not translate host
name ...neon.tech`) in the morning and passed in the afternoon, because the network
happened to be up. That is non-determinism in a gate, which Protocol 6 forbids; it is not
merely a flaky test. It also meant every run mutated production learner state, so the
check's inputs drifted under it.

It now runs inside `tests.hermetic_db.hermetic_database()`: a throwaway SQLite file, all
tables created fresh, deleted on exit, with every outbound non-loopback socket raising
`HermeticNetworkError` by name. Measured consequence: the full tree fell from 14m23s to
**24.8 seconds**, because almost all of that time was network round trips.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
  * **Representation equivalence is whitespace only.** The plan asks for a
    "representation-equivalent answer where the contract permits one". Whitespace is
    gated because it is unambiguous and measured clean. DECIMAL rendering is NOT gated:
    measured 2026-09-12, a submission of "73.0" against a key of `73` is refused on
    **122 of 122** whole-number fill-in-blank/cloze samples -- by all three graders
    alike, so there is no grader disagreement, only a shared strictness. Whether a
    MATATAG whole-number blank should accept a decimal rendering is a curriculum ruling
    (AGENTS.md Protocol 5), not a harness decision, and it is recorded here unanswered
    rather than quietly gated in either direction.
  * **Three seeds per node**, not the obligation manifest. Breadth over formatters,
    variants and profiles is step 0B's (`H-04`) job; this is the grading contract over
    the student path, not a coverage sweep.
  * **`_emit_wrong` is derivation, not adversarial search.** It perturbs one field of the
    keyed answer. A grader that accepts a *differently* wrong answer -- one this function
    does not construct -- is not caught here.
  * **SQLite is not PostgreSQL**; see `tests/hermetic_db.py`'s own limitations block.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[4]

# §8 inventory: the assertions this module can independently fail on. Each must be
# proven by a mutation naming it in `Mutation.asserts`, or excused in
# validate_coverage.UNPROVEN_ASSERTIONS with a reason and a date.
ASSERTIONS = (
    "grading_contract_10",        # subset mode (--node-ids): any finding fails
    "grading_contract_floor_10",  # full tree, ACCEPT direction, measured against GRADE_FLOOR
    "grading_refusal_10",         # a KNOWN-WRONG or MALFORMED submission graded correct
    "grading_equivalence_10",     # a whitespace-equivalent correct answer refused
    "grading_obligation_10",      # a (node, seed) obligation that could not be executed
    "grading_hermetic_10",        # the graded path attempted an outbound connection
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

# A submission no response contract in the tree can key. Used for the malformed
# direction, and as the wrong answer for non-numeric free-text keys.
_SENTINEL = "definitely_not_the_answer_zzz"


# ─────────────────────────────────────────────────────────────────────────────
# Deriving the second direction
# ─────────────────────────────────────────────────────────────────────────────

def _as_number(value: Any) -> Optional[float]:
    """The numeric value of a scalar answer, or None if it is not one."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        token = value.strip().replace(",", "").replace("₱", "")
        try:
            return float(token)
        except ValueError:
            return None
    return None


def _mcq_keys(payload: Dict[str, Any]) -> Dict[str, bool]:
    """key -> is_correct, from whichever option shape this payload carries."""
    fd = payload.get("format_data") or {}
    opts = fd.get("mcq_options") or fd.get("options") or payload.get("options") or []
    out: Dict[str, bool] = {}
    if isinstance(opts, list):
        for o in opts:
            if isinstance(o, dict) and o.get("key"):
                out[str(o["key"])] = bool(o.get("is_correct"))
    elif isinstance(opts, dict):
        for k, v in opts.items():
            out[str(k)] = bool(v.get("is_correct")) if isinstance(v, dict) else False
    return out


def _emit_wrong(payload: Dict[str, Any], correct: Any) -> Any:
    """
    A submission that is KNOWN wrong for this payload, or None if none is derivable.

    None is not a skip: the caller reports it as a `grading_obligation_10` failure,
    because a sample whose refusal direction cannot be exercised is a sample this gate
    has not checked.
    """
    ac = payload.get("answer_collection") or ""
    fmt = payload.get("format") or ""
    mode = payload.get("question_mode") or ""

    # MCQ -- any other DECLARED key. Not an invented one: the grader must refuse a
    # plausible choice a pupil could actually click, not an impossible token.
    if ac == "mcq" or fmt == "mcq":
        others = [k for k, is_correct in _mcq_keys(payload).items()
                  if not is_correct and k != str(correct)]
        return others[0] if others else None

    if fmt == "true_false" or ac == "true_false":
        truthy = str(correct).strip().lower() in ("true", "yes", "t", "1")
        return "False" if truthy else "True"

    if fmt == "error_detect":
        # `_emit_correct` serialises the two-part answer to JSON text; perturb it there.
        try:
            parsed = json.loads(correct) if isinstance(correct, str) else correct
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if isinstance(parsed, dict):
            value = _as_number(parsed.get("correct_value"))
            if value is not None:
                parsed = dict(parsed)
                parsed["correct_value"] = value + 1
                return json.dumps(parsed)
            if isinstance(parsed.get("has_error"), bool):
                parsed = dict(parsed)
                parsed["has_error"] = not parsed["has_error"]
                return json.dumps(parsed)
        return None

    # Ordered sequences -- a different ORDER where one exists, since order is the
    # competency being tested; a changed element only where it does not.
    if isinstance(correct, list):
        if len(correct) >= 2:
            swapped = list(correct)
            swapped[0], swapped[-1] = swapped[-1], swapped[0]
            if [str(x) for x in swapped] != [str(x) for x in correct]:
                return swapped
        if not correct:
            return None
        head = _as_number(correct[0])
        return ([head + 1] if head is not None else [_SENTINEL]) + list(correct[1:])

    # Structured visual answers -- clock_set, currency_picker, plotter_bar.
    if isinstance(correct, dict):
        perturbed = dict(correct)
        for field in ("total", "hour", "minute", "correct_value", "value"):
            value = _as_number(perturbed.get(field))
            if value is not None:
                perturbed[field] = value + 1
                return perturbed
        if isinstance(perturbed.get("has_error"), bool):
            perturbed["has_error"] = not perturbed["has_error"]
            return perturbed
        return None

    number = _as_number(correct)
    if number is not None:
        # A number line grades within a tolerance, so step clear of it rather than
        # submitting a value the contract legitimately accepts.
        visual = payload.get("visual_params") or {}
        tolerance = _as_number(visual.get("tolerance")) or 0.0
        step = (2.0 * tolerance + 1.0) if mode == "number_line" else 1.0
        wrong = number + max(1.0, step)
        if isinstance(correct, (int, float)):
            return wrong
        return str(int(wrong)) if float(wrong).is_integer() else str(wrong)

    if isinstance(correct, str) and correct.strip():
        return _SENTINEL
    return None


def _emit_malformed(correct: Any) -> Any:
    """A submission that is structurally invalid for this payload's response contract."""
    if isinstance(correct, (list, dict)):
        return "{not json at all"
    return _SENTINEL


def _emit_whitespace_equivalent(correct: Any) -> Any:
    """
    The same answer, padded. None where padding is meaningless for the shape.

    Deliberately the weakest possible equivalence claim -- see KNOWN LIMITATIONS on why
    decimal rendering is measured but not gated.
    """
    if isinstance(correct, str) and correct.strip():
        return f"  {correct}  "
    return None


# ─────────────────────────────────────────────────────────────────────────────
# The sweep
# ─────────────────────────────────────────────────────────────────────────────

class _Findings:
    """One list per assertion this module can fail on, so a report never conflates them."""

    def __init__(self) -> None:
        self.accept: List[str] = []
        self.refuse: List[str] = []
        self.equivalence: List[str] = []
        self.obligation: List[str] = []
        self.hermetic: List[str] = []
        self.samples = 0
        self.equivalence_samples = 0

    def total(self) -> int:
        return (len(self.accept) + len(self.refuse) + len(self.equivalence)
                + len(self.obligation) + len(self.hermetic))


def collect_findings(node_ids: Optional[List[str]] = None) -> _Findings:
    """Exercise every (node, seed) obligation in all four directions, hermetically."""
    sys.path.insert(0, str(REPO_ROOT))
    from tests.hermetic_db import HermeticNetworkError, hermetic_database

    found = _Findings()

    with hermetic_database():
        from fastapi.testclient import TestClient

        from backend.app.main import app
        from backend.app.database import SessionLocal
        from backend.app.models import StudentProfile
        from backend.app.practice_gen.registry import get_all_node_ids
        from backend.app.services.orchestrator import PracticeOrchestrator
        from backend.app.services.cache import _fallback_cache
        from tests.grader_roundtrip_auditor import _emit_correct

        # One throwaway learner in a throwaway database. Nothing survives the block.
        db = SessionLocal()
        try:
            learner = StudentProfile(name="GraderGate_hermetic", pin_hash="x", age=8,
                                     grade=3, language_preference="en")
            db.add(learner)
            db.commit()
            db.refresh(learner)
            student_id = learner.id
        finally:
            db.close()

        client = TestClient(app)

        def submit(node_id: str, problem_id: str, answer: Any) -> Dict[str, Any]:
            """The same submission through all three production grader entry points."""
            verdicts: Dict[str, Any] = {}
            try:
                verdicts["portal"] = client.post("/api/practice/submit", json={
                    "selected_answer": answer, "student_id": student_id,
                    "session_id": None, "skill_id": node_id, "skeleton_id": problem_id,
                    "stem": "", "correct_answer": "", "response_time_ms": 5000,
                    "telemetry_flagged": False,
                }).json().get("is_correct")
            except HermeticNetworkError:
                raise
            except Exception as exc:
                verdicts["portal"] = f"ERR:{type(exc).__name__}"
            try:
                as_str = (json.dumps(answer) if isinstance(answer, (list, dict))
                          else str(answer))
                verdicts["lab_v1"] = client.post(
                    "/api/matatag/lab/submit",
                    params={"skeleton_id": problem_id, "student_answer": as_str},
                ).json().get("is_correct")
            except HermeticNetworkError:
                raise
            except Exception as exc:
                verdicts["lab_v1"] = f"ERR:{type(exc).__name__}"
            try:
                verdicts["lab_v2"] = client.post(
                    "/api/matatag/lab/v2/submit",
                    json={"problem_id": problem_id, "student_answer": answer},
                ).json().get("is_correct")
            except HermeticNetworkError:
                raise
            except Exception as exc:
                verdicts["lab_v2"] = f"ERR:{type(exc).__name__}"
            return verdicts

        for node_id in (node_ids or get_all_node_ids()):
            for seed in SEEDS_PER_NODE:
                try:
                    problem = PracticeOrchestrator.generate_problem(
                        node_id=node_id, seed=seed, is_student_path=True
                    )
                except HermeticNetworkError as exc:
                    found.hermetic.append(f"{node_id} (seed {seed}): generation {exc}")
                    continue
                except Exception as exc:
                    # NOT `continue`. A node that cannot be generated is a node this gate
                    # has not checked, and the previous version reported that as silence.
                    found.obligation.append(
                        f"{node_id} (seed {seed}): generation raised "
                        f"{type(exc).__name__}: {exc}. The grading contract was never "
                        f"exercised for this obligation."
                    )
                    continue

                payload = problem if isinstance(problem, dict) else (
                    problem.model_dump() if hasattr(problem, "model_dump")
                    else dict(problem.__dict__))
                problem_id = payload.get("problem_id") or f"{node_id}_{seed}"
                for prefix in ("matatag:", "practice_gen_v2:", "practice_gen:"):
                    _fallback_cache[prefix + problem_id] = payload

                fmt = payload.get("format")
                collection = payload.get("answer_collection")
                correct = _emit_correct(payload)
                if correct is None:
                    found.obligation.append(
                        f"{node_id} (seed {seed}): no correct answer is derivable for "
                        f"format={fmt!r} answer_collection={collection!r}. The grading "
                        f"contract cannot be stated, let alone checked."
                    )
                    continue

                found.samples += 1

                try:
                    # --- direction 1: the correct answer must be ACCEPTED -------------
                    verdicts = submit(node_id, problem_id, correct)
                    refused = {k: v for k, v in verdicts.items() if v is not True}
                    if refused:
                        found.accept.append(
                            f"{node_id} (seed {seed}): a KNOWN-CORRECT answer {correct!r} "
                            f"was not graded correct by {sorted(refused)} -- verdicts "
                            f"{verdicts}. A pupil who does the mathematics right is told "
                            f"they are wrong."
                        )

                    # --- direction 2: a wrong answer must be REFUSED ------------------
                    wrong = _emit_wrong(payload, correct)
                    if wrong is None:
                        found.obligation.append(
                            f"{node_id} (seed {seed}): no KNOWN-WRONG answer is derivable "
                            f"for format={fmt!r} answer_collection={collection!r} "
                            f"(correct={correct!r}). The refusal direction is unchecked "
                            f"for this obligation."
                        )
                    else:
                        verdicts = submit(node_id, problem_id, wrong)
                        accepted = sorted(k for k, v in verdicts.items() if v is True)
                        if accepted:
                            found.refuse.append(
                                f"{node_id} (seed {seed}): a KNOWN-WRONG answer {wrong!r} "
                                f"(correct: {correct!r}) was graded CORRECT by {accepted} "
                                f"-- verdicts {verdicts}. A pupil who gets it wrong is "
                                f"told they are right."
                            )

                    # --- direction 3: a malformed submission must be REFUSED ----------
                    malformed = _emit_malformed(correct)
                    verdicts = submit(node_id, problem_id, malformed)
                    accepted = sorted(k for k, v in verdicts.items() if v is True)
                    if accepted:
                        found.refuse.append(
                            f"{node_id} (seed {seed}): a MALFORMED submission "
                            f"{malformed!r} (correct: {correct!r}) was graded CORRECT by "
                            f"{accepted} -- verdicts {verdicts}. An out-of-contract "
                            f"submission is being coerced into the keyed answer."
                        )

                    # --- direction 4: an equivalent rendering must be ACCEPTED --------
                    equivalent = _emit_whitespace_equivalent(correct)
                    if equivalent is not None:
                        found.equivalence_samples += 1
                        verdicts = submit(node_id, problem_id, equivalent)
                        refused = {k: v for k, v in verdicts.items() if v is not True}
                        if refused:
                            found.equivalence.append(
                                f"{node_id} (seed {seed}): {equivalent!r}, a whitespace-"
                                f"equivalent rendering of the correct answer {correct!r}, "
                                f"was refused by {sorted(refused)} -- verdicts {verdicts}."
                            )
                except HermeticNetworkError as exc:
                    found.hermetic.append(f"{node_id} (seed {seed}): {exc}")

    return found


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    found = collect_findings(node_ids)
    ok = True

    # Hermeticity first: if the graded path reached the network, nothing below is a
    # deterministic result and saying otherwise would be the exact claim H-01 refuted.
    if found.hermetic:
        print(f"  FAIL grading_hermetic_10: {len(found.hermetic)} outbound connection "
              f"attempt(s) from the graded path")
        for finding in found.hermetic[:5]:
            print(f"    - {finding}")
        ok = False

    if found.obligation:
        print(f"  FAIL grading_obligation_10: {len(found.obligation)} obligation(s) could "
              f"not be executed")
        for finding in found.obligation[:8]:
            print(f"    - {finding}")
        ok = False

    if found.refuse:
        print(f"  FAIL grading_refusal_10: {len(found.refuse)} submission(s) that must be "
              f"refused were graded CORRECT")
        for finding in found.refuse[:8]:
            print(f"    - {finding}")
        ok = False

    if found.equivalence:
        print(f"  FAIL grading_equivalence_10: {len(found.equivalence)} equivalent "
              f"rendering(s) of a correct answer were refused")
        for finding in found.equivalence[:8]:
            print(f"    - {finding}")
        ok = False

    if node_ids:
        # Subset mode is zero-tolerance in every direction. The other three assertions
        # have already printed their own FAIL lines above; this one owns the ACCEPT
        # direction, which has no floor outside a full-tree run.
        if found.accept:
            print(f"  FAIL grading_contract_10: {len(found.accept)} finding(s) on {node_ids}")
            for finding in found.accept[:8]:
                print(f"    - {finding}")
            ok = False
        elif ok:
            print(f"  PASS grading_contract_10: 0 findings on {len(node_ids)} node(s) "
                  f"({found.samples} sample(s), 4 direction(s) each)")
        return ok

    if len(found.accept) > GRADE_FLOOR:
        print(f"  FAIL grading_contract_floor_10: {len(found.accept)} mis-gradings exceeds "
              f"floor {GRADE_FLOOR}")
        for finding in found.accept[:10]:
            print(f"    - {finding}")
        ok = False
    else:
        print(f"  PASS grading_contract_floor_10: {len(found.accept)} mis-gradings "
              f"(floor {GRADE_FLOOR}) over {found.samples} student-path sample(s)")

    if ok:
        print(f"  PASS grading_refusal_10: 0 of {found.samples * 2} known-wrong/malformed "
              f"submission(s) graded correct")
        print(f"  PASS grading_equivalence_10: 0 of {found.equivalence_samples} "
              f"whitespace-equivalent submission(s) refused; DECIMAL rendering is measured "
              f"but NOT gated (limitation 1)")
        print(f"  PASS grading_obligation_10: every (node, seed) obligation executed")
        print(f"  PASS grading_hermetic_10: no outbound connection from the graded path")
    return ok


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§10 grading contract, both directions")
    ap.add_argument("--node-ids", help="comma-separated subset; any finding fails")
    args = ap.parse_args()
    nodes = [n.strip() for n in args.node_ids.split(",")] if args.node_ids else None
    return 0 if validate_all(nodes) else 1


if __name__ == "__main__":
    sys.exit(main())
