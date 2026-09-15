"""
The judgment packet's sample allocation (plan step 2).

M1 acceptance: "`_stratified_seeds` covers every declared `(variant, value)` pair with no
per-node cap, pins interest explicitly, and varies difficulty across more than two points
-- measured, not asserted."

These are the assertions behind that "measured, not asserted". A review campaign run on
the old allocation structurally could not see cases the reviewer was being asked to judge,
and the staleness gate then pinned the blind spot in place, because it only re-renders the
seeds a review already cites.

MEASURED 2026-09-12, before and after:

    variant (variant, value) pairs declared          975
    reachable under the old per-node cap of 6        683   (68 nodes exceeded it)
    reachable now                                    975   (+292, exactly as planned)
    landing as DISTINCT samples                      849   (126 render identical text)
    interest allocation before                         0   (`interest` appeared 0 times)
    tree-wide samples                               3514   (mean 23.3, min 17, max 44)
"""

from __future__ import annotations

import pytest

from backend.app.practice_gen.validation import judgment_packets as jp


NODE = "mat_g1_na_q1_0"
BIG_NODE = "mat_g2_na_q2_2"   # 25 variant candidates: the node the old cap of 6 hurt most


class TestNoPerNodeVariantCap:
    def test_the_cap_constant_is_gone(self):
        assert not hasattr(jp, "_VARIANT_COVERAGE_SAMPLES"), (
            "a per-node cap on variant coverage left 292 declared (variant, value) pairs "
            "unreachable by any packet; it must not come back"
        )

    def test_every_declared_candidate_is_attempted(self):
        """Attempted, not necessarily kept: a no-op variant is deduped, which is correct."""
        candidates = jp._variant_coverage_candidates(BIG_NODE)
        assert len(candidates) > 6, "this node exists in the test to exceed the old cap"
        seeds = jp._stratified_seeds(BIG_NODE)
        variant_seeds = [s for s in seeds
                         if jp._VARIANT_COVERAGE_SEED_FLOOR <= s < jp._VARIANT_COVERAGE_SEED_CEIL]
        assert len(variant_seeds) > 6, (
            f"only {len(variant_seeds)} variant samples for {len(candidates)} candidates; "
            f"the cap appears to be back"
        )

    def test_the_variant_range_is_wide_enough_for_the_worst_node(self):
        from backend.app.practice_gen.registry import get_all_node_ids
        worst = max(len(jp._variant_coverage_candidates(n)) for n in get_all_node_ids())
        span = jp._VARIANT_COVERAGE_SEED_CEIL - jp._VARIANT_COVERAGE_SEED_FLOOR
        assert worst <= span, (
            f"{worst} candidates on one node but only {span} reserved seeds; the modulo "
            f"in _render_sample would alias two candidates onto one seed"
        )


class TestInterestIsPinned:
    def test_three_buckets_themed_contrasting_and_neutral(self):
        buckets = jp._interest_buckets(NODE)
        assert len(buckets) == 3
        assert buckets[0] is None, "the neutral default must be one of the buckets"
        assert buckets[1] != buckets[2], "a contrasting theme must actually contrast"
        assert all(isinstance(b, str) for b in buckets[1:])

    def test_buckets_are_stable_across_calls(self):
        """crc32, not hash(): hash() is salted per process and would break replay."""
        assert jp._interest_buckets(NODE) == jp._interest_buckets(NODE)

    def test_different_nodes_draw_different_themes(self):
        a = jp._interest_buckets("mat_g1_na_q1_0")[1:]
        b = jp._interest_buckets("mat_g3_na_q4_1")[1:]
        assert a != b, "every node drawing one theme would hide theme-specific defects"

    def test_the_packet_actually_allocates_interest_samples(self):
        seeds = jp._stratified_seeds(NODE)
        pinned = [s for s in seeds
                  if jp._INTEREST_SEED_FLOOR <= s < jp._INTEREST_SEED_CEIL]
        assert pinned, "interest had ZERO allocation before 2026-09-12"

    def test_a_themed_sample_records_the_interest_it_asked_for(self):
        sample = jp._render_sample(NODE, jp._INTEREST_SEED_FLOOR + 1)
        assert sample["requested"]["student_interest"] is not None


class TestDifficultyIsARangeNotTwoPoints:
    def test_at_least_three_distinct_continuous_profiles_are_sampled(self):
        seeds = jp._stratified_seeds(NODE)
        profiles = set()
        for seed in seeds:
            requested = jp._render_sample(NODE, seed)["requested"]["difficulty_profile"]
            profiles.add(None if requested is None
                         else tuple(sorted((k, str(v)) for k, v in requested.items())))
        assert len(profiles) >= 3, (
            f"only {len(profiles)} distinct difficulty profile(s): the packet saw the "
            f"default and the all-axes ceiling and nothing else"
        )

    def test_the_floor_is_sampled(self):
        sample = jp._render_sample(NODE, jp._FLOOR_DIFFICULTY_SEED_FLOOR)
        assert all(v == 0.0 for v in sample["requested"]["difficulty_profile"].values())

    def test_per_axis_max_moves_exactly_one_axis(self):
        """The all-axes range cannot answer 'which axis made this too hard'."""
        sample = jp._render_sample(NODE, jp._PER_AXIS_MAX_SEED_FLOOR)
        profile = sample["requested"]["difficulty_profile"]
        assert len(profile) == 1 and list(profile.values()) == [1.0]


class TestExperienceIsVaried:
    def test_the_reachable_experiences_come_from_production(self):
        assert "standard" in jp._reachable_experiences()

    def test_the_packet_allocates_every_wrapper_but_the_default(self):
        seeds = jp._stratified_seeds(NODE)
        allocated = [s for s in seeds
                     if jp._EXPERIENCE_SEED_FLOOR <= s < jp._EXPERIENCE_SEED_CEIL]
        expected = len([e for e in jp._reachable_experiences() if e != "standard"])
        assert len(allocated) == expected

    def test_an_experience_sample_records_a_non_default_wrapper(self):
        sample = jp._render_sample(NODE, jp._EXPERIENCE_SEED_FLOOR)
        assert sample["requested"]["experience"] != "standard"


class TestSeedRangesStayDisjoint:
    """
    Freshness re-renders from `(node_id, seed)` with NO profile argument, so a seed's
    number alone decides what it means. Two overlapping ranges would silently re-render a
    reviewed sample under the wrong profile and report drift that is not there.
    """

    def test_no_two_reserved_ranges_overlap(self):
        ranges = [
            ("base", 42, 47),
            ("formatter", 47, 147),
            ("max_all_axes", jp._MAX_DIFFICULTY_SEED_FLOOR, jp._MAX_DIFFICULTY_SEED_CEIL),
            ("variant", jp._VARIANT_COVERAGE_SEED_FLOOR, jp._VARIANT_COVERAGE_SEED_CEIL),
            ("interest", jp._INTEREST_SEED_FLOOR, jp._INTEREST_SEED_CEIL),
            ("per_axis", jp._PER_AXIS_MAX_SEED_FLOOR, jp._PER_AXIS_MAX_SEED_CEIL),
            ("floor", jp._FLOOR_DIFFICULTY_SEED_FLOOR, jp._FLOOR_DIFFICULTY_SEED_CEIL),
            ("experience", jp._EXPERIENCE_SEED_FLOOR, jp._EXPERIENCE_SEED_CEIL),
        ]
        for i, (name_a, lo_a, hi_a) in enumerate(ranges):
            assert lo_a < hi_a, f"{name_a} range is empty"
            for name_b, lo_b, hi_b in ranges[i + 1:]:
                assert hi_a <= lo_b or hi_b <= lo_a, f"{name_a} overlaps {name_b}"

    def test_every_allocated_seed_falls_in_a_known_range(self):
        for seed in jp._stratified_seeds(NODE):
            assert (42 <= seed < 147 or 500 <= seed < 1100), seed


class TestReplayIdentityIsExplicit:
    def test_every_sample_records_what_it_requested(self):
        for seed in jp._stratified_seeds(NODE):
            requested = jp._render_sample(NODE, seed)["requested"]
            assert set(requested) == {"difficulty_profile", "student_interest",
                                      "experience"}, (
                "a record that depends on seed arithmetic alone cannot describe itself"
            )


class TestCanonicalPacket:
    def test_build_is_deterministic_and_digest_bound(self):
        first = jp.build_packet(NODE)
        second = jp.build_packet(NODE)
        assert first == second
        core = {key: value for key, value in first.items() if key != "packet_digest"}
        assert first["packet_digest"] == jp._json_digest(core)

    def test_packet_snapshots_live_competency_and_requirements(self):
        from backend.app.practice_gen.registry import get_node_info

        packet = jp.build_packet(NODE)
        live = jp.get_node_info(NODE)
        assert packet["schema_version"] == 2
        assert packet["sampling_version"] == jp.SAMPLING_VERSION
        assert packet["competency_snapshot"]["text"] == live["competency"]
        assert packet["requirements_snapshot"] == live["requires"]

    def test_samples_preserve_replay_and_learner_visible_fields(self):
        packet = jp.build_packet(NODE)
        assert packet["sample_ids"] == [s["sample_id"] for s in packet["samples"]]
        assert len(packet["sample_ids"]) == len(set(packet["sample_ids"]))
        for sample in packet["samples"]:
            assert sample["node_id"] == NODE
            assert sample["serving_mode"] == "student_path"
            assert "resolved_answer" in sample
            assert set(sample["effective"]) == {
                "format", "is_visual", "visual_type", "interaction_mode", "answer_collection",
                "experience",
            }
            digestable = {k: v for k, v in sample.items() if k != "replay_digest"}
            assert sample["replay_digest"] == jp._json_digest(digestable)

    def test_visual_sample_keeps_full_payload_and_rendered_description(self):
        packet = jp.build_packet(NODE)
        visual = next(s for s in packet["samples"] if s.get("visual_type"))
        assert isinstance(visual["visual_payload"], dict) and visual["visual_payload"]
        assert "_visual_params" not in visual, "the renderer's private handoff must not leak"
        assert visual["visual_render"]["description"]["source"] == "rendered_static_markup"
        assert visual["visual_render"]["renderer_input_digest"]
