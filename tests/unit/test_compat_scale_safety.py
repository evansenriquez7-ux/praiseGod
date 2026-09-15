"""Scale-safety regressions for the registry and explicit KG-edge checks."""

from __future__ import annotations

import json

from backend.app.practice_gen.validation import validate_compat


def _node(*, cumulative_vocab=(), student_vocab=(), prior=()):
    return {
        "cumulative_concepts": [],
        "introduces_concepts": [],
        "cumulative_vocab": list(cumulative_vocab),
        "student_vocab": list(student_vocab),
        "prior_node_ids": list(prior),
    }


def test_monotonicity_uses_declared_edges_not_sorted_adjacency(tmp_path, monkeypatch):
    graph = {
        "nodes": {
            "mat_g1_na_q1_0": _node(student_vocab=("first",)),
            # This node is adjacent by ID but is not a prerequisite successor.
            "mat_g1_na_q1_1": _node(),
            "mat_g10_na_q1_0": _node(
                cumulative_vocab=("first",), prior=("mat_g1_na_q1_0",)
            ),
        }
    }
    path = tmp_path / "kg.json"
    path.write_text(json.dumps(graph), encoding="utf-8")
    monkeypatch.setattr(validate_compat, "_KG_PATH", path)
    monkeypatch.setattr(
        validate_compat, "NODE_TO_DNA", {node_id: [] for node_id in graph["nodes"]}
    )

    assert validate_compat.validate_kg_monotonicity() == []


def test_monotonicity_reports_loss_on_an_explicit_edge(tmp_path, monkeypatch):
    graph = {
        "nodes": {
            "mat_g1_na_q1_0": _node(student_vocab=("first",)),
            "mat_g10_na_q1_0": _node(prior=("mat_g1_na_q1_0",)),
        }
    }
    path = tmp_path / "kg.json"
    path.write_text(json.dumps(graph), encoding="utf-8")
    monkeypatch.setattr(validate_compat, "_KG_PATH", path)
    monkeypatch.setattr(
        validate_compat, "NODE_TO_DNA", {node_id: [] for node_id in graph["nodes"]}
    )

    errors = validate_compat.validate_kg_monotonicity()
    assert len(errors) == 1
    assert "mat_g1_na_q1_0 -> mat_g10_na_q1_0" in errors[0]
    assert "first" in errors[0]


def test_registry_coverage_refuses_orphan_node_mapping(monkeypatch):
    mappings = dict(validate_compat.NODE_TO_DNA)
    mappings["mat_g10_na_q1_999"] = ["addition"]
    monkeypatch.setattr(validate_compat, "NODE_TO_DNA", mappings)

    errors = validate_compat.validate_registry_coverage()
    assert any("mat_g10_na_q1_999" in error for error in errors)


def test_registry_coverage_refuses_unused_compatibility_declaration(monkeypatch):
    compatibility = dict(validate_compat.COMPATIBILITY)
    compatibility["planted_unused_dna"] = ["mcq"]
    dna_modules = dict(validate_compat.DNA_MODULE_MAP)
    dna_modules["planted_unused_dna"] = "backend.app.practice_gen.dna.na.addition"
    monkeypatch.setattr(validate_compat, "COMPATIBILITY", compatibility)
    monkeypatch.setattr(validate_compat, "DNA_MODULE_MAP", dna_modules)

    errors = validate_compat.validate_registry_coverage()
    assert any("planted_unused_dna" in error and "unused" in error for error in errors)
