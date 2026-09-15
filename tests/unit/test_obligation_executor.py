"""Executable controls for H-04's finite obligation executor."""

from __future__ import annotations

from tests.obligation_executor import (
    CacheResult,
    ExecutionFailure,
    DEFAULT_SEEDS_PER_OBLIGATION,
    SEED_SLOT_SCALARS,
    _base_obligations,
    decode_cache_index,
    difficulty_profile_for,
    experience_values,
    execute_indices,
    finite_obligation_count,
    interest_request_values,
    pr_indices,
    representative_indices,
    release_receipt_findings,
    represented_execution_count,
    shard_indices,
    stable_seed,
)


def test_current_finite_product_is_the_corrected_reachable_count():
    # Four incompatible peso_money_build routes were removed from production. The
    # manifest must track that executable student-path truth, not an earlier floor.
    assert len(_base_obligations()) == 4269
    assert len(interest_request_values()) == 27
    assert len(experience_values()) == 4
    assert finite_obligation_count() == 461_052
    assert represented_execution_count() == 2_305_260


def test_seed_slots_cover_boundaries_and_extra_interiors():
    assert SEED_SLOT_SCALARS[:3] == (0.0, 0.5, 1.0)
    assert len(SEED_SLOT_SCALARS) == DEFAULT_SEEDS_PER_OBLIGATION


def test_continuous_axes_are_pinned_by_the_seed_slot():
    obligation = next(o for o in _base_obligations()
                      if o.dna == "addition")
    for slot, scalar in enumerate(SEED_SLOT_SCALARS):
        profile = difficulty_profile_for(obligation, slot)
        assert profile["max_sum"] == scalar
        assert profile["number_difficulty"] == scalar


def test_seed_is_stable_and_changes_with_each_execution_coordinate():
    key = _base_obligations()[0].key()
    seed = stable_seed(key, None, 0)
    assert seed == stable_seed(key, None, 0)
    assert len({
        seed,
        stable_seed(key, "bible", 0),
        stable_seed(key, None, 1),
        stable_seed(_base_obligations()[1].key(), None, 0),
    }) == 4


def test_release_shards_are_complete_non_overlapping_and_order_independent():
    total = represented_execution_count() // len(experience_values())
    shards = [shard_indices(i, 6) for i in range(6)]
    assert sum(len(shard) for shard in shards) == total
    assert all(shard.step == 6 and shard.start == i for i, shard in enumerate(shards))
    # Modulo partition: every global index has exactly one owner, irrespective of the
    # order in which shard receipts arrive.
    for index in (0, 1, 5, 6, total // 2, total - 1):
        owners = [i for i, shard in enumerate(shards) if index in shard]
        assert owners == [index % 6]


def test_representative_sample_covers_every_current_finite_dimension():
    indices = representative_indices(1000)
    decoded = [decode_cache_index(index) for index in indices]
    bases = [entry[0] for entry in decoded]
    assert {o.node_id for o in bases} == {o.node_id for o in _base_obligations()}
    assert {o.dna for o in bases} == {o.dna for o in _base_obligations()}
    assert {o.formatter for o in bases} == {o.formatter for o in _base_obligations()}
    assert {entry[1] for entry in decoded} == set(interest_request_values())
    assert {entry[2] for entry in decoded} == set(range(DEFAULT_SEEDS_PER_OBLIGATION))
    # Every cache key executes all four wrappers, so experience is covered by construction.
    assert set(experience_values()) == {
        "hint_gated", "mastery_drill", "scaffolded", "standard"
    }


def test_pr_tier_crosses_each_changed_base_obligation_completely():
    changed = _base_obligations()[0]
    indices = pr_indices([changed.key()])
    matching = [decode_cache_index(index) for index in indices
                if decode_cache_index(index)[0].key() == changed.key()]
    assert len(matching) == len(interest_request_values()) * DEFAULT_SEEDS_PER_OBLIGATION
    assert {(entry[1], entry[2]) for entry in matching} == {
        (interest, slot)
        for interest in interest_request_values()
        for slot in range(DEFAULT_SEEDS_PER_OBLIGATION)
    }


def test_unknown_changed_key_fails_loudly():
    import pytest

    with pytest.raises(ValueError, match="absent from the current manifest"):
        pr_indices(["not|a|live|obligation"])


def test_missing_release_receipts_are_a_blocking_finding(tmp_path):
    findings, summary = release_receipt_findings(tmp_path / "absent-receipts")

    assert summary["status"] == "not_run"
    assert summary["complete"] is False
    assert findings == [
        "no release shard receipts exist; the complete finite sweep is uncertified"
    ]


def test_executor_stops_after_first_failed_obligation(monkeypatch):
    calls = []

    def fake_execute(payload):
        index, _seed_count = payload
        calls.append(index)
        failure = ExecutionFailure(index, 731, "planted", "AssertionError", "boom")
        return CacheResult(index, 0.0, 0, (), (), 0, failure)

    monkeypatch.setattr("tests.obligation_executor._execute_cache_key", fake_execute)
    results, _elapsed = execute_indices(range(5), workers=1)

    assert calls == [0]
    assert len(results) == 1
    assert results[0].failure is not None
