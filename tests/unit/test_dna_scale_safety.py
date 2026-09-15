"""H-05 controls for grade breadth and exact DNA value comparisons."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from types import SimpleNamespace

from backend.app.practice_gen.validation import validate_dna
from backend.app.practice_gen.validation._manifest import load_dna


def test_declared_grades_parse_every_digit():
    dna = replace(load_dna("addition"), param_bounds={"g3": {}, "g10": {}})

    grades, errors = validate_dna._declared_grades(dna)

    assert grades == [3, 10]
    assert errors == []


def test_exact_numeric_comparison_never_uses_float_tolerance():
    assert validate_dna._are_values_equal("1/10", Fraction(1, 10))
    assert validate_dna._are_values_equal("0.1", Fraction(1, 10))
    assert not validate_dna._are_values_equal(0.1 + 0.2, 0.3)
    assert not validate_dna._are_values_equal(True, 1)


def test_formula_structure_samples_every_declared_grade(monkeypatch):
    dna = load_dna("addition")
    calls = []

    def sample(**kwargs):
        calls.append((kwargs["node_id"], kwargs["grade"], kwargs["seed"]))
        return SimpleNamespace(correct_answer=11, distractors=[10, 12])

    monkeypatch.setattr(validate_dna, "generate_context", sample)
    validate_dna.validate_formula_dna(dna)

    assert set(calls) == {
        (node_id, grade, seed)
        for node_id, concepts in validate_dna.NODE_TO_DNA.items()
        if "addition" in concepts
        for grade in [(validate_dna.get_node_info(node_id) or {})["grade"]]
        for seed in validate_dna.STRUCTURAL_SEEDS
    }


def test_generation_failure_is_named_with_grade_and_seed(monkeypatch):
    dna = load_dna("addition")

    def sample(**kwargs):
        if kwargs["grade"] == 2 and kwargs["seed"] == 42:
            raise RuntimeError("planted unit failure")
        return SimpleNamespace(correct_answer=11, distractors=[10, 12])

    monkeypatch.setattr(validate_dna, "generate_context", sample)
    errors = validate_dna.validate_formula_dna(dna)

    assert any(
        "grade=2 seed=42" in error and "planted unit failure" in error
        for error in errors
    )
