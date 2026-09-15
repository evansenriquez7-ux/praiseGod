"""Controls for mutation execution itself, before proof-record consumption."""

from tests import mutation_harness as mh


def test_red_baseline_is_invalid_before_any_plant(monkeypatch):
    mutation = mh.Mutation(
        name="unit_red_baseline",
        description="unit fixture",
        edits={},
        command=["unused"],
        expected_check="unit fixture",
        asserts=["mutation_proof_integrity_8"],
        baseline_must_not_contain=["target marker"],
    )
    monkeypatch.setattr(mh, "_run", lambda _mutation: (1, "unrelated baseline failure"))

    def forbidden_apply(_mutation):
        raise AssertionError("a mutation must not be planted onto a red baseline")

    monkeypatch.setattr(mh, "_apply", forbidden_apply)
    record = mh.run_mutation_recorded(mutation)

    assert record["detected"] is False
    assert record["planted_exit"] is None
    assert record["restored_clean"] is True
    assert "baseline exited 1" in record["diagnostic_line"]
