from backend.app.practice_gen.validation import validate_judgment as vj
from tests import frontend_renderer


def _current():
    return {
        "seed": 42,
        "question_text": "Look at the number line.",
        "correct_answer": 6,
        "visual_type": "NumberLine",
        "_visual_params": {"start": 0, "end": 6},
    }


def _rendered(samples):
    rows = []
    for sample in samples:
        row = dict(sample)
        row.pop("_visual_params", None)
        row["visual_render"] = {
            "visual_type": "NumberLine",
            "renderer_input_digest": "current-digest",
            "description": {"source": "rendered_static_markup", "element_count": 12},
        }
        rows.append(row)
    return rows


def test_missing_rendered_visual_is_unadjudicable(monkeypatch):
    monkeypatch.setattr(vj, "_render_sample", lambda _node, _seed: _current())
    monkeypatch.setattr(frontend_renderer, "attach_rendered_visual_descriptions", _rendered)
    errors = vj._validate_freshness("mat_g1_na_q1_0", {
        "samples_reviewed": [{
            "seed": 42,
            "question_text": "Look at the number line.",
            "correct_answer": 6,
        }],
    })
    assert any("records no render-derived visual evidence" in error for error in errors)


def test_corrupt_rendered_visual_is_stale(monkeypatch):
    monkeypatch.setattr(vj, "_render_sample", lambda _node, _seed: _current())
    monkeypatch.setattr(frontend_renderer, "attach_rendered_visual_descriptions", _rendered)
    errors = vj._validate_freshness("mat_g1_na_q1_0", {
        "samples_reviewed": [{
            "seed": 42,
            "question_text": "Look at the number line.",
            "correct_answer": 6,
            "visual_render": {
                "visual_type": "NumberLine",
                "renderer_input_digest": "corrupt-digest",
                "description": {"source": "rendered_static_markup", "element_count": 0},
            },
        }],
    })
    assert any("rendered visual description" in error for error in errors)
