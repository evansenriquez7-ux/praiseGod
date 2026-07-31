"""
Unit tests for the two behaviours changed on 2026-07-30:

  * difficulty window endpoints (`number_difficulty.generate_number_by_window` /
    `generate_pair_by_window`) — scalar 0.0 and 1.0 used to short-circuit to
    argmin/argmax, ignoring `rng` entirely, so an endpoint served a single fixed
    item forever (37 of 81 node/dna/magnitude-axis combinations produced <= 2
    distinct operand sets over 30 seeds at scalar 1.0; addition produced exactly
    1, against 29 at scalar 0.5). The endpoints are now bands, but a band must
    still *contain* the pool extreme or the competency ceiling stops being
    reachable and §1A-reach fails.

  * `base_generator`'s scalar-vs-magnitude guard — a registry tuple bound whose
    key is not a registered continuous axis is never scalar-mapped, so a 0-1
    scalar reached the DNA as a raw ceiling of 1.

Both properties are cheap to assert here and expensive to notice in a 151-node
matrix run, which is the point.
"""

from __future__ import annotations

import random

import pytest

from backend.app.practice_gen.generators.number_difficulty import (
    generate_number_by_window,
    generate_pair_by_window,
)

# A pool with several distinct high-magnitude members, so a band can be a band.
POOL = list(range(1, 21))
PAIRS = [(a, b) for a in range(1, 11) for b in range(1, 11)]


def _draw_numbers(scalar, pool=POOL, n=60, num_type="whole"):
    return {
        generate_number_by_window(pool, scalar, 5, random.Random(s), num_type)
        for s in range(n)
    }


def _draw_pairs(scalar, pairs=PAIRS, n=60):
    return {
        generate_pair_by_window(pairs, scalar, 5, random.Random(s))
        for s in range(n)
    }


# ── endpoints are bands, not points ──────────────────────────────────────────
#
# Asserted at scalar 1.0 only, and that is not an oversight. `score_candidate`
# scores *awkwardness*, not magnitude (99 -> 0.95 but 100 -> 0.54, because a
# round number is the easier item), and for a pool of 1..20 every score lands in
# [0.45, 0.95]. The 0.0 band [0.0, w] is therefore empty for such a pool and
# resolves through the "closest to window centre" fallback — deterministically,
# by design, and unchanged by this commit. Only the top band has room to be a
# band, so only the top band can be asserted to behave like one.

def test_top_band_samples_more_than_one_value():
    """The regression this exists for: argmax ignored rng completely."""
    drawn = _draw_numbers(1.0)
    assert len(drawn) > 1, (
        f"scalar 1.0 collapsed to the single value {drawn} across 60 seeds — "
        f"the endpoint is a point again, not a band"
    )


def test_top_band_samples_more_than_one_pair():
    drawn = _draw_pairs(1.0)
    assert len(drawn) > 1, f"scalar 1.0 collapsed to {drawn}"


def test_top_band_is_not_just_the_maximum():
    """Pins the design intent against a re-introduced argmax: scalar 1.0 means
    "the hardest band", which contains awkward-but-smaller numbers too, not
    "the largest value in the pool"."""
    drawn = _draw_numbers(1.0)
    assert drawn - {max(POOL)}, f"scalar 1.0 returned only the pool maximum: {drawn}"


def test_interior_scalars_respond_to_the_rng():
    assert len(_draw_numbers(0.5)) > 1


# ── the endpoint must reach the ceiling even when score fights magnitude ─────

def test_top_band_reaches_the_ceiling_when_score_and_magnitude_disagree():
    """
    The exact shape that failed 7 multiplication nodes in a full matrix run.

    mat_g2_na_q3_0's pool is the 2/3/4/5/10 tables with products <= 100. Its top
    *awkwardness* band is products 27-45, because 10 x 10 = 100 is too round to
    score highly — so sampling the score band alone left the competency's stated
    ceiling unreachable, and injecting the lone extreme pair gave only a 74%
    chance of drawing it across the 10 samples §1A-reach takes. This asserts the
    reach property at unit speed instead of via a 15-minute matrix run.
    """
    pairs = [(a, b) for b in (2, 3, 4, 5, 10) for a in range(1, 11) if a * b <= 100]
    # §1A-reach's own protocol: 10 samples, peak must clear 60% of the ceiling.
    peak = max(
        a * b
        for a, b in (
            generate_pair_by_window(pairs, 1.0, 5, random.Random(900 + i))
            for i in range(10)
        )
    )
    assert peak >= 0.6 * 100, (
        f"peak product {peak} across 10 samples is below 60% of the pool ceiling "
        f"100 — the top of the competency's range is unreachable"
    )


def test_bottom_band_reaches_the_floor():
    pairs = [(a, b) for b in (2, 3, 4, 5, 10) for a in range(1, 11) if a * b <= 100]
    trough = min(
        a * b
        for a, b in (
            generate_pair_by_window(pairs, 0.0, 5, random.Random(900 + i))
            for i in range(10)
        )
    )
    assert trough <= 6, f"easiest band never produced a small product (min {trough})"


# ── ...but the band still contains the extreme, so the ceiling is reachable ──

def test_scalar_one_can_reach_the_pool_maximum():
    """§1A-reach depends on this: sampling the top *score* band is not enough,
    because score is not magnitude. Without the explicit extreme, five G2
    multiplication nodes peaked at 45 against a stated ceiling of 100."""
    assert max(POOL) in _draw_numbers(1.0)


def test_scalar_zero_can_reach_the_pool_minimum():
    assert min(POOL) in _draw_numbers(0.0)


def test_scalar_one_pairs_can_reach_the_extreme_pair():
    assert max(PAIRS) in _draw_pairs(1.0)


def test_fraction_extreme_is_chosen_by_value_not_tuple_order():
    """(1, 2) is larger than (1, 10); lexicographic order says otherwise."""
    fractions = [(1, 2), (1, 4), (1, 10), (3, 4)]
    assert (3, 4) in _draw_numbers(1.0, pool=fractions, num_type="fraction")
    assert (1, 10) in _draw_numbers(0.0, pool=fractions, num_type="fraction")


# ── scalar-vs-magnitude guard ────────────────────────────────────────────────

def test_unmapped_bound_rejects_a_difficulty_scalar():
    """`max_minuend` is bound by the registry but is not a catalog axis, so
    nothing maps 1.0 onto (1, 9999) — the DNA would receive a ceiling of 1."""
    from backend.app.practice_gen.pipeline import run

    with pytest.raises(ValueError, match="looks like a 0-1 difficulty scalar"):
        run(
            node_id="mat_g3_na_q2_5",
            difficulty_profile={"max_minuend": 1.0, "number_difficulty": 1.0},
            seed=9102,
            forced_dna="subtraction",
        )


def test_unmapped_bound_accepts_an_absolute_magnitude():
    from backend.app.practice_gen.pipeline import run

    p = run(
        node_id="mat_g3_na_q2_5",
        difficulty_profile={"max_minuend": 9999, "number_difficulty": 1.0},
        seed=9102,
        forced_dna="subtraction",
    )
    values = [v for v in (p.get("given_values") or {}).values() if isinstance(v, int)]
    assert max(values) > 1000, f"expected 4-digit operands, got {values}"
