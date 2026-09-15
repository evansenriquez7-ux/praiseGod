"""Negative controls for consumed frontend evidence completeness."""

from __future__ import annotations

import json

from backend.app.practice_gen.validation import mutation_proof, validate_render


def _artifact() -> dict:
    description = {
        "source": "rendered_static_markup",
        "element_count": 3,
    }
    common = {
        "visual_type": "NumberBond",
        "formatter": "number_bond",
        "node_id": "mat_g1_na_q2_5",
        "seed": 42,
        "interaction_mode": "set",
        "answer_collection": "numeric_input",
    }
    return {
        "source_input_digest": mutation_proof.input_digest(),
        "cases_executed": 2,
        "renders_executed": 4,
        "registered_visual_types": sorted(validate_render._required_keys()),
        "production_visual_types": ["NumberBond"],
        "unreachable_renderer_registrations": [],
        "outcomes": [
            {**common, "case_id": case_id, "mode": mode, "description": description}
            for case_id in ("number-bond-case-a", "number-bond-case-b")
            for mode in ("active", "disabled")
        ],
        "answer_roundtrips": [
            {
                "case_id": case_id,
                "seed": 42,
                "correct_answer": 7,
                "emitted_answer": 7,
            }
            for case_id in ("number-bond-case-a", "number-bond-case-b")
        ],
    }


def _validate(tmp_path, monkeypatch, artifact: dict) -> bool:
    path = tmp_path / "frontend.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(validate_render, "STATIC_RENDER_ARTIFACT", path)
    return validate_render.validate_static_render_artifact()


def test_complete_roundtrip_artifact_passes(tmp_path, monkeypatch):
    assert _validate(tmp_path, monkeypatch, _artifact()) is True


def test_pruned_roundtrip_artifact_fails(tmp_path, monkeypatch):
    artifact = _artifact()
    artifact["answer_roundtrips"] = artifact["answer_roundtrips"][:1]

    assert _validate(tmp_path, monkeypatch, artifact) is False


def test_duplicate_modes_cannot_hide_an_unrendered_mode(tmp_path, monkeypatch):
    artifact = _artifact()
    artifact["outcomes"][1]["mode"] = "active"

    assert _validate(tmp_path, monkeypatch, artifact) is False
