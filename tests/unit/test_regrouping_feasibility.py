"""
test_regrouping_feasibility.py
==============================
Verifies the regrouping feasibility model that prevents runaway generation.

A `regrouping` level demands a fixed number of carry (addition) / borrow
(subtraction) places. A number range can only produce so many: a sum/minuend
bounded by an N-digit ceiling can carry/borrow at most N-1 times. When a level
demands more places than the range allows, the combination is *infeasible* and
the DNA must raise immediately instead of exhausting a rejection loop.

These tests pin `max_regrouping_places` against the ground truth
(`_satisfies_regrouping`, brute-forced): at the returned max level at least one
pair exists, and above it none does. They also assert the DNA guard raises fast
on infeasible profiles rather than returning a (possibly off-spec) problem.

Per AGENTS.md rule #4 / testing-strategy §1: construct-or-reject, never
search-and-cap or silently degrade.
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)


# ── ground-truth brute force ────────────────────────────────────────────────

def _carries(a, b):
    carry = 0
    cc = 0
    for pv in (1, 10, 100, 1000, 10000):
        s = (a // pv) % 10 + (b // pv) % 10 + carry
        if s >= 10:
            cc += 1
            carry = 1
        else:
            carry = 0
    return cc


def _borrows(a, b):
    borrow = 0
    bc = 0
    for pv in (1, 10, 100, 1000, 10000):
        da = (a // pv) % 10 - borrow
        db = (b // pv) % 10
        if da < db:
            bc += 1
            borrow = 1
        else:
            borrow = 0
    return bc


def _brute_max_carries(max_result, cap=1500):
    best = 0
    hi = min(max_result, cap)
    for a in range(hi + 1):
        for b in range(min(hi, max_result - a) + 1):
            best = max(best, _carries(a, b))
    return best


def _brute_max_borrows(max_minuend, cap=1500):
    best = 0
    hi = min(max_minuend, cap)
    for a in range(hi + 1):
        for b in range(a + 1):
            best = max(best, _borrows(a, b))
    return best


# ── the helper matches ground truth ─────────────────────────────────────────

@pytest.mark.parametrize("max_result,expected", [
    (9, 0), (20, 1), (100, 2), (200, 2), (999, 2), (1000, 3),
])
def test_addition_max_regrouping_places_matches_bruteforce(max_result, expected):
    from backend.app.practice_gen.dna.na.addition import max_regrouping_places
    assert max_regrouping_places(max_result) == expected
    if max_result <= 1200:
        assert max_regrouping_places(max_result) == _brute_max_carries(max_result)


@pytest.mark.parametrize("max_minuend,expected", [
    (9, 0), (20, 1), (100, 2), (999, 2), (1000, 3),
])
def test_subtraction_max_regrouping_places_matches_bruteforce(max_minuend, expected):
    from backend.app.practice_gen.dna.na.subtraction import max_regrouping_places
    assert max_regrouping_places(max_minuend) == expected
    if max_minuend <= 1200:
        assert max_regrouping_places(max_minuend) == _brute_max_borrows(max_minuend)


# ── feasibility boundary: a pair exists at max, none above ───────────────────

def test_addition_pair_exists_at_max_level_none_above():
    from backend.app.practice_gen.dna.na.addition import (
        max_regrouping_places, _satisfies_regrouping,
    )
    max_result = 999
    mx = max_regrouping_places(max_result)  # 2
    level_by_places = {1: "one_place", 2: "two_places", 3: "three_places"}

    # A pair exists at the max feasible level.
    at_max = level_by_places[mx]
    assert any(
        _satisfies_regrouping(a, b, at_max)
        for a in range(max_result + 1)
        for b in range(max_result - a + 1)
    ), f"no pair satisfies {at_max} within {max_result}"

    # No pair exists one level above the max.
    above = level_by_places[mx + 1]
    assert not any(
        _satisfies_regrouping(a, b, above)
        for a in range(max_result + 1)
        for b in range(max_result - a + 1)
    ), f"a pair unexpectedly satisfies {above} within {max_result}"


# ── the DNA guard raises fast on infeasible profiles ─────────────────────────

def test_addition_guard_raises_on_infeasible():
    from backend.app.practice_gen.dna.na import addition
    # 999 (3-digit) supports at most 2 carries; three_places demands 3.
    with pytest.raises(RuntimeError):
        addition.generate_params(
            grade=3, seed=1,
            difficulty_profile={"max_sum": 999, "regrouping": "three_places"},
        )


def test_addition_generates_on_feasible():
    from backend.app.practice_gen.dna.na import addition
    out = addition.generate_params(
        grade=3, seed=1,
        difficulty_profile={"max_sum": 9999, "regrouping": "three_places"},
    )
    assert out["a"] + out["b"] == out["result"]


def test_subtraction_no_silent_fallback():
    """The old code silently returned a pair ignoring the regrouping constraint
    when the pool came up empty. It must raise instead."""
    from backend.app.practice_gen.dna.na import subtraction
    # Force an empty pool via an impossible level for a tiny range.
    with pytest.raises(RuntimeError):
        subtraction.generate_params(
            grade=1, seed=1,
            difficulty_profile={"regrouping": "four_places"},
        )


def test_auditor_mirror_agrees_with_dna():
    from tests.exhaustive_checklist_auditor import (
        _regrouping_profile_is_feasible,
    )
    # New contract: the profile carries a [0,1] SCALAR for max_sum, and the
    # feasibility check maps it to the concrete value via competency_bounds
    # using the same (logarithmic) scale as the orchestrator. For addition on
    # [0, 9999], scalar 0.5→99 (< 100, three_places infeasible), 0.75→999
    # (>= 100, feasible).
    cb = {"max_sum": (0, 9999)}
    from backend.app.practice_gen.dna.na.addition import regrouping_is_feasible
    # Cross-check the DNA's own feasibility fn so this test tracks it: three
    # carry places need a 4-digit result, so it is feasible only near the top
    # of the range (scalar 1.0 → 9999) and infeasible at scalar 0.5 (→99).
    assert not regrouping_is_feasible("three_places", 99)
    assert regrouping_is_feasible("three_places", 9999)
    # infeasible → excluded (scalar 0.5 maps to 99)
    assert not _regrouping_profile_is_feasible(
        "addition", {"max_sum": 0.5, "regrouping": "three_places"}, cb)
    # feasible → kept (scalar 1.0 maps to 9999)
    assert _regrouping_profile_is_feasible(
        "addition", {"max_sum": 1.0, "regrouping": "three_places"}, cb)
    # no regrouping key → kept
    assert _regrouping_profile_is_feasible("addition", {"max_sum": 0.1}, cb)
    # subtraction: four_places is infeasible at G3's 4-digit ceiling (9999)
    assert not _regrouping_profile_is_feasible(
        "subtraction", {"regrouping": "four_places"}, cb, grade=3)
    # subtraction: three_places is feasible at G3
    assert _regrouping_profile_is_feasible(
        "subtraction", {"regrouping": "three_places"}, cb, grade=3)
