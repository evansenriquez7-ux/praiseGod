"""
test_answers_match.py
=====================
Pins `backend.app.services.scoring.answers_match`, the single value comparison the
portal, Lab v1 and Lab v2 now share for non-MCQ answers.

Why it exists
-------------
§10 (the grading contract) held five findings where a pupil did the mathematics right
and was told they were wrong. Both had the same shape: a grader that did not recognise
a format fell back to something that could never match.

  * portal and Lab v1 fell back to an MCQ *key* comparison, so a `sort_order` answer of
    [10, 9, 8] was tested as "[10, 9, 8]" == "A". Four nodes.
  * Lab v1's ClockSet branch parsed the correct answer leniently (digits only) but the
    student's answer strictly (`int("35 p.m.")`), so an identical string was rejected.

The regression guard that matters most here is `test_am_pm_is_not_collapsed`: the
obvious fix for the clock bug -- pull digits out of both sides -- makes '9:35 a.m.'
equal '9:35 p.m.', marking a genuinely WRONG answer correct. That is worse than the
bug it fixes, so it must stay impossible.
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)

from backend.app.services.scoring import answers_match  # noqa: E402


# ── the four sort_order findings ─────────────────────────────────────────────

@pytest.mark.parametrize("submitted", [
    [10, 9, 8],           # native list, as the portal receives it
    "[10, 9, 8]",         # JSON string, as Lab v1 receives it via query param
    "[10,9,8]",           # no spaces
    ["10", "9", "8"],     # strings rather than ints
])
def test_correct_ordering_is_accepted_in_every_transport(submitted):
    assert answers_match(submitted, [10, 9, 8]) is True


@pytest.mark.parametrize("submitted", [
    [10, 8, 9],           # right numbers, wrong order
    [8, 9, 10],           # reversed
    [10, 9],              # too short
    [10, 9, 8, 7],        # too long
    [11, 9, 8],           # one wrong value
])
def test_wrong_ordering_is_rejected(submitted):
    assert answers_match(submitted, [10, 9, 8]) is False


def test_order_is_significant():
    """These are ordering answers -- a set comparison would accept a wrong sequence."""
    assert answers_match([8, 9, 10], [10, 9, 8]) is False


# ── the ClockSet finding, and the fix that must NOT be used ──────────────────

def test_identical_time_string_is_accepted():
    assert answers_match("9:35 p.m.", "9:35 p.m.") is True


def test_case_and_whitespace_are_forgiven():
    assert answers_match("  9:35 P.M. ", "9:35 p.m.") is True


def test_am_pm_is_not_collapsed():
    """
    REGRESSION GUARD. Parsing digits out of both sides ([9, 35] == [9, 35]) would make
    this pass and mark a wrong answer correct. Half a day is not a rounding error.
    """
    assert answers_match("9:35 a.m.", "9:35 p.m.") is False


# ── scalars and dicts ────────────────────────────────────────────────────────

@pytest.mark.parametrize("s,c,expected", [
    ("5", 5, True),
    (5, "5", True),
    ("5", "6", False),
    ("cat", "CAT", True),
    ({"hours": 9, "minutes": 35}, {"hours": 9, "minutes": 35}, True),
    ({"hours": 9, "minutes": 35}, {"hours": 9, "minutes": 30}, False),
    ({"hours": 9}, {"hours": 9, "minutes": 35}, False),
])
def test_scalar_and_dict_comparison(s, c, expected):
    assert answers_match(s, c) is expected


def test_list_and_scalar_do_not_match():
    """A shape mismatch must not fall through to a string compare that accidentally passes."""
    assert answers_match([10, 9, 8], "10") is False
