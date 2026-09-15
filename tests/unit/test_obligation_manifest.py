"""
The obligation manifest (§11, H-04): determinism, and the model it claims.

`H-04`'s acceptance opens with "enumeration is deterministic" and "two independent
derivations agree on the reachable count". The second is a gate (§11); the first cannot
be, because a mutation proves a check FIRES and determinism is the absence of variation.
It is pinned here instead.

Why that matters more than usual: the plan carried a recorded figure of 4,325 obligations
across 463 pairs whose probe is not on disk and which no candidate model reproduces. A
count nobody can re-derive is a number, not evidence. These tests are what stop this
manifest becoming the next such number.
"""

from __future__ import annotations

from tests.obligation_manifest import (
    CONTINUOUS_CLASSES,
    build_budget,
    derive_count_independently,
    enumerate_obligations,
)


class TestDeterminism:
    def test_two_enumerations_are_byte_identical(self):
        first, first_rejects = enumerate_obligations()
        second, second_rejects = enumerate_obligations()
        assert [o.key() for o in first] == [o.key() for o in second]
        assert [(r.node_id, r.dna, r.formatter, r.rule) for r in first_rejects] == \
               [(r.node_id, r.dna, r.formatter, r.rule) for r in second_rejects]

    def test_obligations_are_unique(self):
        obligations, _ = enumerate_obligations()
        keys = [o.key() for o in obligations]
        assert len(keys) == len(set(keys)), "an obligation counted twice inflates the budget"

    def test_enumeration_is_sorted_so_diffs_are_readable(self):
        obligations, _ = enumerate_obligations()
        assert [o.key() for o in obligations] == sorted(o.key() for o in obligations)

    def test_each_assignment_is_sorted_and_pins_each_variant_once(self):
        obligations, _ = enumerate_obligations()
        for o in obligations[:2000]:
            names = [k for k, _ in o.assignment]
            assert names == sorted(names)
            assert len(names) == len(set(names)), f"{o.key()} pins a variant twice"


class TestTheTwoDerivationsAgree:
    def test_they_agree_on_the_live_tree(self):
        obligations, _ = enumerate_obligations()
        pairs = {(o.node_id, o.dna, o.formatter) for o in obligations}
        alt_pairs, alt_total = derive_count_independently()
        assert (alt_pairs, alt_total) == (len(pairs), len(obligations))


class TestTheBudgetReportSaysWhatItDoesNotCover:
    def test_it_records_the_plan_figure_as_unreproduced(self):
        """A superseded number must stay visible, or the next agent re-inherits it."""
        budget = build_budget()
        stated = budget["plan_figure_not_reproduced"]
        assert stated["recorded_in_plan"] == {"pairs": 463, "allowed_assignments": 4325}
        assert "NOT REPRODUCIBLE" in stated["status"]

    def test_it_crosses_experience_and_interest_into_the_execution_model(self):
        budget = build_budget()
        cross = budget["execution_model"]
        assert cross["experience"]["multiplier"] == 4
        assert cross["student_interest_request"]["multiplier"] == 27
        assert cross["finite_obligations"] == (
            budget["counts"]["discrete_obligations"] * 4 * 27
        )
        assert cross["release_represented_executions"] == (
            cross["finite_obligations"] * cross["seeds_per_obligation"]
        )

    def test_curriculum_gate_is_keyed_by_dna_not_node_id(self):
        """The first executor benchmark found 152/1,000 false-reachable entries here."""
        obligations, _ = enumerate_obligations()
        missing_number_g1 = [
            dict(o.assignment)
            for o in obligations
            if o.node_id == "mat_g1_na_q3_1" and o.dna == "missing_number"
        ]
        assert missing_number_g1
        assert all(profile.get("tables") not in {"6", "7", "8", "9"}
                   for profile in missing_number_g1)

        length_g1 = [
            dict(o.assignment)
            for o in obligations
            if o.node_id == "mat_g1_mg_q2_2" and o.dna == "length_measurement"
        ]
        assert length_g1
        assert all(profile.get("unit_type") not in {"cm", "m"} for profile in length_g1)

    def test_every_rejection_names_a_production_rule(self):
        _, rejections = enumerate_obligations()
        assert rejections, "a tree with no rejections would mean the gates are not read"
        for r in rejections:
            assert r.rule in {"NODE_FORMATTER_EXCLUSIONS", "FORMATTER_VARIANT_SUPPORT",
                              "NODE_TO_DNA_presence"}, r.rule
            assert r.detail, "a rejection without a reason is a silent drop"

    def test_continuous_classes_cover_both_boundaries_and_an_interior(self):
        names = {n for n, _ in CONTINUOUS_CLASSES}
        values = {v for _, v in CONTINUOUS_CLASSES}
        assert names == {"min_boundary", "interior", "max_boundary"}
        assert values == {0.0, 0.5, 1.0}
