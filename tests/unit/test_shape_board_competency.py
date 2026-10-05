"""Execution proof for Grade 1 shape-identification content."""

from backend.app.practice_gen.validation.judgment_packets import _render_sample


SEEDS = (11, 23, 42, 57, 64, 78, 91, 103, 118, 127)


def test_g1_shape_identification_serves_the_three_figures_with_variation():
    """The named shape types, sizes, and angles must reach the learner payload."""
    appearances = {"triangle": set(), "rectangle": set(), "square": set()}
    for seed in SEEDS:
        sample = _render_sample("mat_g1_mg_q1_0", seed)
        assert sample["formatter"] == "read_mcq", seed
        assert sample["visual_type"] == "ShapeBoard", seed
        assert "different sizes and orientations" in sample["question_text"], seed
        assert "Which shape on the board" in sample["question_text"], seed
        assert "small flat shape" not in sample["question_text"], seed
        shapes = sample["visual_payload"]["shapes"]
        assert {s["type"] for s in shapes} == set(appearances), seed
        assert len({s["size_px"] for s in shapes}) == 3, seed
        assert len({s["orientation_deg"] for s in shapes}) == 3, seed
        for shape in shapes:
            appearances[shape["type"]].add((shape["size_px"], shape["orientation_deg"]))
    assert all(len(values) >= 3 for values in appearances.values()), appearances
