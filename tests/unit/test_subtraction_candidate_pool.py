"""
test_subtraction_candidate_pool.py
==================================
Pins the candidate-pool budget in subtraction.py's counting_back/taking_away branch.

That branch enumerated the ENTIRE (a, b) space before picking one pair. At
mat_g3_na_q2_4's competency ceiling (max_minuend=9999) that was 49,994,955
`_satisfies_regrouping` calls keeping 9.1M pairs -- ~120s for a single problem,
and 42 of the 48 minutes a full `validate_matrix` run took. Every sibling branch
in the file already had the enumerate-or-sample guard; this one did not.

These tests assert WORK DONE, not wall-clock. A timing assertion would be flaky
under load and on other hardware; the predicate call count is deterministic and
is the thing that actually regressed. If someone deletes the cap, the count jumps
by four orders of magnitude and these fail immediately.

Companion mutation: `subtraction_pool_uncapped` in tests/mutation_harness.py.
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)

from backend.app.practice_gen.dna.na import subtraction as S  # noqa: E402


def _count_predicate_calls(monkeypatch, **profile_overrides):
    """Run generate_params once, returning (result, predicate_call_count)."""
    calls = {"n": 0}
    original = S._satisfies_regrouping

    def counting(a, b, level):
        calls["n"] += 1
        return original(a, b, level)

    monkeypatch.setattr(S, "_satisfies_regrouping", counting)

    profile = {
        "task_type": "counting_back",
        "number_difficulty": 0.5,
    }
    profile.update(profile_overrides)
    result = S.generate_params(
        grade=profile_overrides.get("_grade", 3),
        difficulty_profile=profile,
        seed=43,
    )
    return result, calls["n"]


# ── the regression this file exists for ──────────────────────────────────────

def test_large_range_does_not_enumerate_the_whole_space(monkeypatch):
    """max_minuend=9999 must sample, not enumerate 50M pairs."""
    _, n_calls = _count_predicate_calls(monkeypatch, max_minuend=9999)

    # Sampled path: bounded by _MAX_CANDIDATE_PAIRS * 4 attempts, one predicate
    # call each. The uncapped form made 49,994,955.
    assert n_calls <= S._MAX_CANDIDATE_PAIRS * 4, (
        f"counting_back made {n_calls:,} _satisfies_regrouping calls at "
        f"max_minuend=9999; the cap allows {S._MAX_CANDIDATE_PAIRS * 4:,}. "
        f"The pool cap has been removed or bypassed."
    )


def test_small_range_still_enumerates_exhaustively(monkeypatch):
    """Below the ceiling, behaviour is unchanged -- full enumeration."""
    max_minuend = 20
    _, n_calls = _count_predicate_calls(monkeypatch, max_minuend=max_minuend)

    # min_a defaults to 10 when max_minuend >= 10; min_b defaults to 1.
    expected = sum(len(range(1, a + 1)) for a in range(10, max_minuend + 1))
    assert n_calls == expected, (
        f"expected exhaustive enumeration ({expected} calls) at max_minuend="
        f"{max_minuend}, got {n_calls}. Small ranges must not switch to sampling "
        f"-- that would change output for nodes that have no problem today."
    )


def test_ceiling_is_the_boundary_between_the_two_strategies():
    """The guard is a strategy switch, not a range limit."""
    assert S._EXHAUSTIVE_MINUEND_CEILING == 100
    assert S._MAX_CANDIDATE_PAIRS == 2_000


# ── the silent fallback that was removed ─────────────────────────────────────

def test_infeasible_constraint_raises_instead_of_falling_back():
    """
    Was `candidates = [(max_minuend, 1)]` -- a silent default that ignored the
    regrouping constraint and shipped off-spec content (Protocol 3).

    a=9999 has every digit at 9, so no subtrahend can force a borrow; demanding
    one_place regrouping is genuinely infeasible.
    """
    profile = {
        "task_type": "counting_back",
        "max_minuend": 9999,
        "min_minuend": 9999,
        "min_subtrahend": 1,
        "regrouping": "one_place",
        "number_difficulty": 0.5,
    }
    with pytest.raises(RuntimeError) as exc:
        S.generate_params(grade=3, difficulty_profile=profile, seed=4242)

    message = str(exc.value)
    # Protocol 6: a failure that cannot be reproduced has not been reported.
    assert "seed=4242" in message, f"seed missing from failure message: {message}"
    assert "max_minuend=9999" in message
    assert "one_place" in message


# ── determinism (Protocol 6) ─────────────────────────────────────────────────

@pytest.mark.parametrize("max_minuend", [20, 99, 999, 9999])
def test_same_seed_same_pair(max_minuend):
    """Sampling must not cost determinism -- the pool is drawn from `rng`."""
    profile = {
        "task_type": "counting_back",
        "max_minuend": max_minuend,
        "number_difficulty": 0.5,
    }
    first = S.generate_params(grade=3, difficulty_profile=dict(profile), seed=77)
    second = S.generate_params(grade=3, difficulty_profile=dict(profile), seed=77)
    assert (first["a"], first["b"]) == (second["a"], second["b"])


# Seed counts differ on purpose. If the pool cap is ever removed, each 9999 call
# costs ~120s, so a 20-seed loop here would make the suite look deadlocked rather
# than failing -- the exact confusion the two `slow`-marked pool tests already cause.
# The detecting test above fires first and cheaply; this one only needs enough
# seeds to show the bound holds.
@pytest.mark.parametrize("max_minuend,seed_count", [(999, 20), (9999, 3)])
def test_result_is_within_competency_bounds(max_minuend, seed_count):
    """The range the competency states is preserved by the sampled path."""
    for seed in range(42, 42 + seed_count):
        profile = {
            "task_type": "counting_back",
            "max_minuend": max_minuend,
            "number_difficulty": 0.5,
        }
        p = S.generate_params(grade=3, difficulty_profile=profile, seed=seed)
        assert 1 <= p["a"] <= max_minuend, f"a={p['a']} outside 1..{max_minuend} (seed {seed})"
        assert 0 <= p["b"] <= p["a"], f"b={p['b']} not in 0..a (seed {seed})"
        assert p["result"] == p["a"] - p["b"], f"result mismatch (seed {seed})"
        assert p["result"] >= 0, f"negative result (seed {seed})"
