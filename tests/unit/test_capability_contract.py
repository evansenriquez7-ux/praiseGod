"""
Mutation tests for the capability contract (§6A/§6B/§6C).

These exist because green is not evidence. Phase 4 of pgen_hardening.md was recorded
as done for weeks and scored 4/7 the first time it was honestly executed, so every
check here is proved by planting the exact violation it claims to catch.

The load-bearing case is `test_omission_survives_provenance_but_not_coverage`. §6A
alone is not enough: an agent whose pipeline cannot render "draw" could simply omit
the draw requirement, and §6C (required ⊆ provided) would then pass trivially. Only
§6B coverage closes that, and this test pins the division of labour so a future
refactor cannot quietly drop it.
"""

from backend.app.practice_gen.validation import validate_capability as VC

COMPETENCY = "Recognize and draw parallel, intersecting, and perpendicular lines."

HONEST = [
    {"kind": "task", "id": "recognize_lines", "clause": "Recognize"},
    {"kind": "task", "id": "draw_lines", "clause": "draw"},
    {"kind": "object", "id": "parallel_lines", "clause": "parallel"},
    {"kind": "object", "id": "intersecting_lines", "clause": "intersecting"},
    {"kind": "object", "id": "perpendicular_lines", "clause": "perpendicular lines"},
]


def test_honest_declaration_passes_provenance_and_coverage():
    assert VC._validate_provenance("N", COMPETENCY, HONEST) == []
    assert VC._validate_coverage("N", COMPETENCY, HONEST, []) == []


def test_invention_is_caught_by_provenance():
    """A requirement the curriculum never states cannot be declared."""
    invented = HONEST + [
        {"kind": "task", "id": "estimate_angle", "clause": "estimate the angle"}
    ]
    errs = VC._validate_provenance("N", COMPETENCY, invented)
    assert any("estimate_angle" in e and "does not appear" in e for e in errs), errs


def test_omission_survives_provenance_but_not_coverage():
    """
    The loophole this whole design would otherwise have: drop the requirement you
    cannot satisfy, and required ⊆ provided passes vacuously.
    """
    omitted = [r for r in HONEST if r["id"] != "draw_lines"]

    # Provenance cannot see an omission -- everything still cited is genuine.
    assert VC._validate_provenance("N", COMPETENCY, omitted) == []

    # Coverage does, by name.
    errs = VC._validate_coverage("N", COMPETENCY, omitted, [])
    assert any("'draw'" in e or "draw" in e for e in errs), errs


def test_requires_ignore_must_be_explicit_to_excuse_a_word():
    """Ignoring a competency word is possible but visible -- never a silent default."""
    omitted = [r for r in HONEST if r["id"] != "draw_lines"]
    assert VC._validate_coverage("N", COMPETENCY, omitted, []) != []
    assert VC._validate_coverage("N", COMPETENCY, omitted, ["draw"]) == []


def test_missing_clause_is_an_error_not_a_skip():
    no_clause = [{"kind": "task", "id": "draw_lines"}]
    errs = VC._validate_provenance("N", COMPETENCY, no_clause)
    assert any("no 'clause'" in e for e in errs), errs


def test_unprovided_capability_names_the_node_and_the_clause():
    """
    The acceptance test for the entire capability contract: mat_g3_mg_q1_5's
    competency says "draw" and nothing in the pipeline draws, so the harness must
    say so itself rather than leaving it to a reviewer's judgment.
    """
    errs = VC.validate_capability_declarations(["mat_g3_mg_q1_5"])
    draw = [e for e in errs if "draw_lines" in e]
    assert draw, f"expected an unprovided-capability failure for draw_lines, got {errs}"
    assert "mat_g3_mg_q1_5" in draw[0]
    assert "no pipeline artifact provides it" in draw[0]
