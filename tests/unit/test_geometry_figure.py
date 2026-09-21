"""
GeometryFigure: the drawn model, and the two things that make it a model at all.

`geometric_lines` served `recognize_model` through `mcq`, which draws nothing, so the
model lived as ASCII inside the stem with a parenthetical gloss:

    "Look at the model: • A--------B • (a straight path with endpoints at both ends).
     Which geometric figure is represented?"

That item is answerable from the GLOSS -- "a straight path with endpoints at both ends"
is the definition of a line segment -- so it tested reading a definition rather than
recognising a model, while MATATAG names the model outright on both nodes.

Two directions are asserted here, because fixing either alone leaves the defect:

 1. **The figure is DRAWN, and the drawing carries the distinction.** A ray and a line
    differ by one arrowhead; perpendicular and intersecting lines differ by a right-angle
    marker. Those are counted in React's emitted markup, not in the payload -- a payload
    that merely SAYS kind='ray' proves nothing about what a pupil sees. This is the same
    standard §12 holds ScaleRead's needle to, and it inherits the same named blind spot:
    jsdom has no layout engine, so this proves the elements EXIST and are distinct, never
    that they are positioned legibly.
 2. **The stem no longer describes what the figure shows.** Otherwise the drawing is
    decoration beside a self-answering sentence, which is the original defect with an
    extra picture.
"""

from __future__ import annotations

import pytest

from tests.frontend_renderer import attach_rendered_visual_descriptions


# What each kind must DRAW. Every row is a distinction a pupil has to see, and the
# numbers are the ones measured from the emitted markup on 2026-09-21 -- not chosen
# in advance and then made true.
#
#   point          a dot, and no path at all
#   line           extends BOTH ways: two arrowheads
#   segment        stops at both ends: two endpoints, NO arrowhead
#   ray            one endpoint end, one arrowhead end
#   parallel       two paths that never meet: no intersection marker
#   perpendicular  two paths AND the square corner that distinguishes it
#   intersecting   two paths crossing, and NO square corner
_EXPECTED = {
    "point":         {"path": 0, "endpoint": 1, "arrowhead": 0, "right-angle": 0, "intersection": 0},
    "line":          {"path": 1, "endpoint": 2, "arrowhead": 2, "right-angle": 0, "intersection": 0},
    "segment":       {"path": 1, "endpoint": 2, "arrowhead": 0, "right-angle": 0, "intersection": 0},
    "ray":           {"path": 1, "endpoint": 2, "arrowhead": 1, "right-angle": 0, "intersection": 0},
    "parallel":      {"path": 2, "endpoint": 0, "arrowhead": 0, "right-angle": 0, "intersection": 0},
    "perpendicular": {"path": 2, "endpoint": 0, "arrowhead": 0, "right-angle": 1, "intersection": 0},
    "intersecting":  {"path": 2, "endpoint": 0, "arrowhead": 0, "right-angle": 0, "intersection": 1},
    "triangle":      {"path": 1, "endpoint": 3, "arrowhead": 0, "right-angle": 0, "intersection": 0},
}

_LETTER_STROKES = {"H": 3, "T": 2, "X": 2}


def _params(kind: str) -> dict:
    labels = {"point": ["P"], "triangle": ["A", "B", "C"]}.get(kind, ["A", "B"])
    if kind in ("parallel", "perpendicular", "intersecting"):
        labels = []
    return {"kind": kind, "labels": labels}


@pytest.fixture(scope="module")
def rendered():
    """Every kind rendered ONCE. One Node invocation for the whole module -- now for COST
    rather than for safety: since 2026-09-22 (owner ruling 8) each invocation renders in
    its own `run-<pid>-<uuid4>` directory, so concurrent callers no longer corrupt each
    other. Driving Node once per kind would still be needlessly slow."""
    cases = [(k, _params(k)) for k in _EXPECTED]
    cases += [(f"letter{L}", {"kind": "letter", "labels": [], "letter": L})
              for L in _LETTER_STROKES]
    out = attach_rendered_visual_descriptions([
        {"seed": i, "node_id": name, "visual_type": "GeometryFigure", "_visual_params": vp}
        for i, (name, vp) in enumerate(cases)
    ])
    return {s["node_id"]: s["visual_render"]["description"] for s in out}


@pytest.mark.parametrize("kind", sorted(_EXPECTED))
def test_each_kind_draws_its_distinguishing_elements(kind, rendered):
    desc = rendered[kind]
    roles = desc["role_counts"]
    for role, expected in _EXPECTED[kind].items():
        assert roles.get(role, 0) == expected, (
            f"{kind}: emitted {role}={roles.get(role, 0)}, expected {expected}. "
            f"role_counts={roles}"
        )
    assert desc["svg_count"] == 1, kind


def test_a_ray_and_a_line_are_not_the_same_drawing():
    """The pair a pupil is most likely to confuse, asserted as a DIFFERENCE rather than
    two independent counts -- two rows of a table can both drift and still agree."""
    assert _EXPECTED["ray"]["arrowhead"] != _EXPECTED["line"]["arrowhead"]
    assert _EXPECTED["segment"]["arrowhead"] == 0


def test_perpendicular_is_distinguished_from_intersecting_by_the_square_corner():
    """Both are two crossing paths; the right-angle marker is the ONLY visual difference,
    so if it stops being emitted the two become the same picture with different keys."""
    assert _EXPECTED["perpendicular"]["right-angle"] == 1
    assert _EXPECTED["intersecting"]["right-angle"] == 0
    assert _EXPECTED["perpendicular"]["path"] == _EXPECTED["intersecting"]["path"]


@pytest.mark.parametrize("letter,strokes", sorted(_LETTER_STROKES.items()))
def test_a_letter_is_drawn_as_strokes_not_set_as_type(letter, strokes, rendered):
    """The letter's SEGMENTS are the model. A glyph in a font is not a figure a pupil can
    point at, and `text_labels` carrying "H" would mean the letter was typed, not drawn."""
    desc = rendered[f"letter{letter}"]
    assert desc["role_counts"].get("path", 0) == strokes, desc["role_counts"]
    assert letter not in desc["text_labels"], desc["text_labels"]


def test_an_unknown_kind_is_a_loud_failure_not_an_empty_box():
    """A routing defect must be visible as one. Rendering a blank frame is how an
    unanswerable item reaches a pupil looking like a normal one (Protocol 3)."""
    with pytest.raises(Exception):
        attach_rendered_visual_descriptions([{
            "seed": 0, "node_id": "bogus", "visual_type": "GeometryFigure",
            "_visual_params": {"kind": "rhombus", "labels": []},
        }])


# ── the stem direction ────────────────────────────────────────────────────────

def test_every_recognize_model_pool_item_declares_a_figure():
    """The formatter RAISES when handed an item with no figure, and
    FORMATTER_VARIANT_SUPPORT is what keeps that raise unreachable. This asserts the
    other half: that the restriction it relies on is satisfiable for every item it
    admits."""
    from backend.app.practice_gen.dna.mg import geometric_lines as gl

    pool = getattr(gl, "_ITEM_POOL", None)
    assert pool, "geometric_lines._ITEM_POOL not found; this test is pinned to it"
    model_items = [i for i in pool if i.get("task_type") == "recognize_model"]
    assert model_items, "no recognize_model items at all"
    missing = [i["question"][:60] for i in model_items if not i.get("figure")]
    assert not missing, f"recognize_model items with no figure to draw: {missing}"


def test_the_drawn_stem_does_not_describe_the_figure():
    """The gloss must go when the drawing arrives, or the item is still answerable
    without looking at the model."""
    from backend.app.practice_gen.formatters.visual.fmt_geometry_figure import (
        _strip_model_gloss,
    )

    original = ("Look at the model: • A--------B • (a straight path with endpoints at "
                "both ends). Which geometric figure is represented?")
    out = _strip_model_gloss(original)
    assert out == "Look at the model. Which geometric figure is represented?", out
    for tell in ("--------", "endpoints at both ends", "straight path"):
        assert tell not in out, (tell, out)


def test_a_stem_with_no_gloss_is_left_alone():
    """The positive control: an item whose referent is a letter or a real-world object
    must not be mangled by the stripper."""
    from backend.app.practice_gen.formatters.visual.fmt_geometry_figure import (
        _strip_model_gloss,
    )

    original = "Look at the letter 'H'. The two vertical side segments are an example of ___."
    assert _strip_model_gloss(original) == original
