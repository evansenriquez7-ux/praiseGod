import math
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
from typing import Any

import json


def answers_match(student_ans: Any, correct_ans: Any) -> bool:
    """
    Compare a submitted answer to the correct one by VALUE, for any non-MCQ format.

    Why this is shared
    ------------------
    §10 exists because the portal, Lab v1 and Lab v2 can disagree about the same
    submission, and they did: an unrecognised format fell through to an MCQ *key*
    comparison in the portal and Lab v1 (`str(answer).upper() == correct_key`, i.e.
    "[10, 9, 8]" == "A"), while Lab v2 fell through to a *value* comparison and
    happened to be right. Four `sort_order` nodes served a pupil the correct
    ordering and marked it wrong.

    Keying the default off the answer's SHAPE rather than off a list of format
    names is deliberate (Scaling Mandate #4): `sort_order` was missing from lists
    that already contained `ordering`, and a grade 4-10 formatter that returns a
    list would have walked into the identical trap. Nothing here names a format.

    Rules, in order:
      * both sides list-like -> element-wise, order-sensitive, string-normalised
        (order matters: these are ordering/sorting answers)
      * both sides dict-like -> key-by-key on the same normalisation
      * otherwise -> case-insensitive, whitespace-stripped string comparison
    A JSON-encoded string on either side is decoded first, because Lab v1 receives
    its answer as a query parameter and can only send a string.
    """
    def _decode(v: Any) -> Any:
        if isinstance(v, str):
            t = v.strip()
            if t[:1] in ("[", "{"):
                try:
                    return json.loads(t)
                except (json.JSONDecodeError, ValueError):
                    return v
        return v

    def _norm(v: Any) -> str:
        return str(v).strip().lower()

    s_val, c_val = _decode(student_ans), _decode(correct_ans)

    if isinstance(s_val, (list, tuple)) and isinstance(c_val, (list, tuple)):
        return len(s_val) == len(c_val) and all(
            _norm(a) == _norm(b) for a, b in zip(s_val, c_val)
        )
    if isinstance(s_val, dict) and isinstance(c_val, dict):
        return set(s_val) == set(c_val) and all(
            _norm(s_val[k]) == _norm(c_val[k]) for k in c_val
        )
    return _norm(s_val) == _norm(c_val)


def normalize_option_key(value: Any) -> str:
    """
    Normalise an MCQ option key for comparison: strip, then upper-case.

    The key comparison `str(answer).upper() == correct_key.upper()` was written out
    seven times across the portal and the two Lab graders, and only Lab v2 stripped
    whitespace. Measured 2026-09-12 over the full tree: a submission of `"  B  "` for a
    correct key of `"B"` was REFUSED by the portal and Lab v1 and ACCEPTED by Lab v2 on
    211 of 256 MCQ samples -- three graders, one submission, two answers. That is the
    exact defect class §10 was built for, so the normalisation becomes one function
    rather than a seventh hand-written copy (Protocol 2).
    """
    return str(value).strip().upper()


_TRUE_TOKENS = frozenset({"true", "t", "yes", "y", "1"})
_FALSE_TOKENS = frozenset({"false", "f", "no", "n", "0"})


def parse_bool_answer(value: Any) -> "bool | None":
    """
    Parse a true/false submission STRICTLY. `None` means "not a true/false answer".

    Why strict, and why shared
    --------------------------
    All three graders used `str(v).strip().lower() in ("true", "yes", "t", "1")`, which
    has no failure value: every unrecognised submission became **False**. On a
    `true_false` item whose key is False -- roughly half of them -- a pupil who submitted
    nothing meaningful was therefore graded CORRECT. Measured 2026-09-12 on the isolated
    §10 fixture: the string "definitely_not_the_answer_zzz" was accepted by the portal,
    Lab v1 and Lab v2 alike on `mat_g1_na_q1_1`, `mat_g1_na_q1_3` and `mat_g1_na_q1_9`.

    That is a silent default in the accept-wrong direction (Protocol 3), and it was
    written out three times (Protocol 2), so the fix is one function all three call.

    An unparseable KEY also returns None, and the caller then grades the submission
    incorrect rather than raising: a pupil must never see a 500 because a generator
    keyed a malformed boolean. The resulting mis-grading is loud where it belongs --
    every seed of that node becomes a §10 `grading_contract` finding.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value == 1:
            return True
        if value == 0:
            return False
        return None
    if isinstance(value, str):
        token = value.strip().lower()
        if token in _TRUE_TOKENS:
            return True
        if token in _FALSE_TOKENS:
            return False
    return None


def bool_answers_match(student_ans: Any, correct_ans: Any) -> bool:
    """True only when both sides parse as booleans and agree. See `parse_bool_answer`."""
    student = parse_bool_answer(student_ans)
    correct = parse_bool_answer(correct_ans)
    return student is not None and correct is not None and student == correct


def validate_math_answer(expected: Any, student_ans: str) -> bool:
    """
    Deterministic validation using SymPy solver.
    Verifies if the student_ans is mathematically equivalent to expected.
    """
    try:
        expr_solved = parse_expr(str(expected))
        ans_solved = parse_expr(str(student_ans))
        return sp.simplify(expr_solved - ans_solved) == 0
    except Exception:
        return str(expected).strip() == str(student_ans).strip()

def update_elo(student_elo: float, skill_elo: float, is_correct: bool, k_factor: float = 32.0):
    """
    Standard Elo update matchmaking formula.
    Adjusts student ELO and skill/question ELO based on performance.
    """
    expected_student = 1.0 / (1.0 + math.pow(10.0, (skill_elo - student_elo) / 400.0))
    actual_student = 1.0 if is_correct else 0.0
    
    new_student_elo = student_elo + k_factor * (actual_student - expected_student)
    
    # Skill difficulty increases on student failure, decreases on success
    expected_skill = 1.0 - expected_student
    actual_skill = 0.0 if is_correct else 1.0
    new_skill_elo = skill_elo + k_factor * (actual_skill - expected_skill)
    
    return round(new_student_elo, 1), round(new_skill_elo, 1)
