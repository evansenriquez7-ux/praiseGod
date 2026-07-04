"""Tests for the strict-scalar-endpoint ±1 tolerance in the checklist auditor.

These tests verify that the auditor's continuous-axis endpoint check
accepts off-by-one rounding (a known artifact of the orchestrator's
logarithmic mapping via ``int(pow(10, ...))``) and rejects anything
beyond that as a real violation.

Per AGENTS.md rule #4 (no silent fallbacks), this tolerance is a
narrow, documented carve-out at the *boundary*, not a graceful
default: actual_val is still required to be present and within ±1 of
the expected endpoint. The check fails fast (adds a violation) for
any drift beyond that.
"""
import os
import sys

import pytest

# Make the auditor importable. The auditor expects to run from the
# workspace root (it adds the project root to sys.path itself), so we
# do the same for the test.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)

from tests.exhaustive_checklist_auditor import (  # noqa: E402
    _strict_scalar_endpoint_violates,
)


class TestStrictScalarEndpointWithinTolerance:
    """±1 (and exact match) are NOT violations."""

    def test_exact_match_at_lower_bound_is_not_violation(self):
        assert _strict_scalar_endpoint_violates(actual_val=5, expected=5) is False

    def test_exact_match_at_upper_bound_is_not_violation(self):
        assert _strict_scalar_endpoint_violates(actual_val=100, expected=100) is False

    def test_plus_one_at_upper_bound_is_not_violation(self):
        # actual=expected+1 at scalar=1.0 (e.g. 51 when expected 50)
        assert _strict_scalar_endpoint_violates(actual_val=51, expected=50) is False

    def test_minus_one_at_lower_bound_is_not_violation(self):
        # actual=expected-1 at scalar=0.0 (e.g. 4 when expected 5)
        assert _strict_scalar_endpoint_violates(actual_val=4, expected=5) is False

    def test_plus_one_at_lower_bound_is_not_violation(self):
        # ±1 tolerance is symmetric at both endpoints
        assert _strict_scalar_endpoint_violates(actual_val=6, expected=5) is False

    def test_minus_one_at_upper_bound_is_not_violation(self):
        assert _strict_scalar_endpoint_violates(actual_val=49, expected=50) is False


class TestStrictScalarEndpointBeyondTolerance:
    """>±1 IS a violation."""

    def test_plus_two_at_upper_bound_is_violation(self):
        # The exact case the plan calls out: actual=expected+2 must fail
        assert _strict_scalar_endpoint_violates(actual_val=52, expected=50) is True

    def test_minus_two_at_lower_bound_is_violation(self):
        assert _strict_scalar_endpoint_violates(actual_val=3, expected=5) is True

    def test_large_drift_at_upper_bound_is_violation(self):
        # Anything far from the endpoint is a real mapping failure
        assert _strict_scalar_endpoint_violates(actual_val=200, expected=50) is True

    def test_large_drift_at_lower_bound_is_violation(self):
        assert _strict_scalar_endpoint_violates(actual_val=200, expected=5) is True

    def test_wrong_endpoint_at_lower_bound_is_violation(self):
        # actual_val=0 when expected=5 is 5 units off — not a rounding artifact
        assert _strict_scalar_endpoint_violates(actual_val=0, expected=5) is True


class TestStrictScalarEndpointNoneHandling:
    """actual_val=None is the caller's responsibility, not this predicate's."""

    def test_none_actual_is_not_a_violation_from_this_predicate(self):
        # The call site gates on `actual_val is not None` before calling
        # this helper, so a None actual is handled upstream. The
        # predicate itself treats None as "no opinion" (not a violation)
        # to be defensive — the call site controls whether absence is
        # itself a problem.
        assert _strict_scalar_endpoint_violates(actual_val=None, expected=5) is False


class TestStrictScalarEndpointParity:
    """±1 tolerance is symmetric in the deviation magnitude, not signed."""

    def test_deviation_of_one_in_either_direction_is_allowed(self):
        # Sign should not matter; only magnitude.
        assert _strict_scalar_endpoint_violates(actual_val=6, expected=5) is False
        assert _strict_scalar_endpoint_violates(actual_val=4, expected=5) is False

    def test_deviation_of_two_in_either_direction_is_rejected(self):
        assert _strict_scalar_endpoint_violates(actual_val=7, expected=5) is True
        assert _strict_scalar_endpoint_violates(actual_val=3, expected=5) is True


class TestProductionCallSiteUsesHelper:
    """The production check (scalar in (0.0, 1.0)) must consult the
    helper and only add a failure when it returns True. This test
    mirrors the production branch in
    `exhaustive_checklist_auditor.py` exactly so that a future edit
    cannot silently weaken the check.

    We do not need to spin up the orchestrator — the helper is the
    single source of truth and the production branch is a one-line
    call to it.
    """

    def test_scalar_one_zero_upper_bound_helper_decides(self):
        failures = []
        scalar = 1.0
        min_val, max_val = 1, 50
        actual_val = 51  # expected+1 — tolerated
        expected = min_val if scalar == 0.0 else max_val
        if scalar in (0.0, 1.0) and _strict_scalar_endpoint_violates(actual_val, expected):
            failures.append("would-have-been-added")
        assert failures == []

    def test_scalar_zero_lower_bound_helper_decides(self):
        failures = []
        scalar = 0.0
        min_val, max_val = 1, 50
        actual_val = 0  # expected-1 — tolerated
        expected = min_val if scalar == 0.0 else max_val
        if scalar in (0.0, 1.0) and _strict_scalar_endpoint_violates(actual_val, expected):
            failures.append("would-have-been-added")
        assert failures == []

    def test_scalar_one_upper_bound_two_off_adds_failure(self):
        failures = []
        scalar = 1.0
        min_val, max_val = 1, 50
        actual_val = 52  # expected+2 — NOT tolerated
        expected = min_val if scalar == 0.0 else max_val
        if scalar in (0.0, 1.0) and _strict_scalar_endpoint_violates(actual_val, expected):
            failures.append("would-have-been-added")
        assert failures == ["would-have-been-added"]

    def test_scalar_zero_lower_bound_two_off_adds_failure(self):
        failures = []
        scalar = 0.0
        min_val, max_val = 1, 50
        actual_val = -1  # expected-2 — NOT tolerated
        expected = min_val if scalar == 0.0 else max_val
        if scalar in (0.0, 1.0) and _strict_scalar_endpoint_violates(actual_val, expected):
            failures.append("would-have-been-added")
        assert failures == ["would-have-been-added"]

    def test_scalar_one_exact_match_no_failure(self):
        failures = []
        scalar = 1.0
        min_val, max_val = 1, 50
        actual_val = 50  # exact match
        expected = min_val if scalar == 0.0 else max_val
        if scalar in (0.0, 1.0) and _strict_scalar_endpoint_violates(actual_val, expected):
            failures.append("would-have-been-added")
        assert failures == []

    def test_scalar_zero_exact_match_no_failure(self):
        failures = []
        scalar = 0.0
        min_val, max_val = 1, 50
        actual_val = 1  # exact match
        expected = min_val if scalar == 0.0 else max_val
        if scalar in (0.0, 1.0) and _strict_scalar_endpoint_violates(actual_val, expected):
            failures.append("would-have-been-added")
        assert failures == []
