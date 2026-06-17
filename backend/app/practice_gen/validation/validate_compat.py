"""
Practice Generation — Compatibility & Registry Coverage Validation

Verifies that:
  1. Every DNA concept in COMPATIBILITY can be imported.
  2. Every formatter in each concept's list is a recognised formatter name.
  3. Every node in knowledge_graph_g1_3.json appears in NODE_TO_DNA.
  4. Every DNA concept in NODE_TO_DNA appears in COMPATIBILITY.

Run as a module:
    python -m backend.app.practice_gen.validation.validate_compat
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import List

from ..compatibility import COMPATIBILITY
from ..registry import NODE_TO_DNA


# ─── Known formatter names (from compatibility.py docstring) ─────────────────

_KNOWN_FORMATTERS = {
    # Textual
    "mcq", "cloze", "numeric_input", "ordering", "true_false",
    "error_detect", "fill_in_blank",
    # Visual – read
    "number_line_read", "array_grid_read", "place_value_blocks_read",
    "peso_money_read", "clock_read", "bar_chart_read", "pictograph_read",
    "fraction_model_read", "ruler_measure", "grid_area", "sort_order",
    "shape_board", "ten_frame", "balance_scale", "pattern_sequence",
    "calendar_read", "categorize", "emoji_pictorial",
    # Visual – set
    "number_line_set", "array_grid_set", "place_value_blocks_set",
    "peso_money_build", "clock_set", "bar_chart_set", "fraction_shade",
    "fill_in_table", "number_bond",
}

# DNA module paths (same as validate_dna) ─────────────────────────────────────

_DNA_MODULE_MAP: dict = {
    "addition":            "backend.app.practice_gen.dna.na.addition",
    "subtraction":         "backend.app.practice_gen.dna.na.subtraction",
    "multiplication":      "backend.app.practice_gen.dna.na.multiplication",
    "division":            "backend.app.practice_gen.dna.na.division",
    "counting":            "backend.app.practice_gen.dna.na.counting",
    "number_reading":      "backend.app.practice_gen.dna.na.number_reading",
    "ordinal_numbers":     "backend.app.practice_gen.dna.na.ordinal_numbers",
    "place_value":         "backend.app.practice_gen.dna.na.place_value",
    "comparing_ordering":  "backend.app.practice_gen.dna.na.comparing_ordering",
    "missing_number":      "backend.app.practice_gen.dna.na.missing_number",
    "patterns":            "backend.app.practice_gen.dna.na.patterns",
    "fractions":           "backend.app.practice_gen.dna.na.fractions",
    "money_peso":          "backend.app.practice_gen.dna.na.money_peso",
    "rounding":            "backend.app.practice_gen.dna.na.rounding",
    "order_of_operations": "backend.app.practice_gen.dna.na.order_of_operations",
    "shapes_2d":           "backend.app.practice_gen.dna.mg.shapes_2d",
    "length_measurement":  "backend.app.practice_gen.dna.mg.length_measurement",
    "mass_capacity":       "backend.app.practice_gen.dna.mg.mass_capacity",
    "time_reading":        "backend.app.practice_gen.dna.mg.time_reading",
    "calendar":            "backend.app.practice_gen.dna.mg.calendar",
    "perimeter":           "backend.app.practice_gen.dna.mg.perimeter",
    "area":                "backend.app.practice_gen.dna.mg.area",
    "geometric_lines":     "backend.app.practice_gen.dna.mg.geometric_lines",
    "symmetry_slides":     "backend.app.practice_gen.dna.mg.symmetry_slides",
    "pictographs":         "backend.app.practice_gen.dna.dp.pictographs",
    "bar_graphs":          "backend.app.practice_gen.dna.dp.bar_graphs",
    "probability_language":"backend.app.practice_gen.dna.dp.probability_language",
}

# Path to the knowledge graph JSON ────────────────────────────────────────────

_KG_PATH: Path = (
    Path(__file__).parent.parent.parent.parent.parent
    / "data"
    / "knowledge_graph_g1_3.json"
)


def validate_compatibility_table() -> List[str]:
    """
    Validate every entry in the COMPATIBILITY table.

    Checks:
      1. Each DNA concept in COMPATIBILITY can be imported via its module path.
      2. Each formatter in each concept's list is a recognised formatter name.

    Returns:
        List of error strings. Empty list = table is clean.
    """
    errors: List[str] = []

    for concept, formatters in COMPATIBILITY.items():
        # 1. DNA concept must be importable
        module_path = _DNA_MODULE_MAP.get(concept)
        if module_path is None:
            errors.append(
                f"COMPATIBILITY: concept '{concept}' has no entry in "
                f"_DNA_MODULE_MAP — cannot verify importability."
            )
        else:
            try:
                importlib.import_module(module_path)
            except ImportError as exc:
                errors.append(
                    f"COMPATIBILITY: concept '{concept}' module "
                    f"'{module_path}' failed to import: {exc}"
                )

        # 2. Each formatter must be a known formatter name
        for fmt in formatters:
            if fmt not in _KNOWN_FORMATTERS:
                errors.append(
                    f"COMPATIBILITY['{concept}']: formatter '{fmt}' is not "
                    f"in the known formatter set."
                )

    return errors


def validate_registry_coverage() -> List[str]:
    """
    Verify bidirectional coverage between the knowledge graph and NODE_TO_DNA,
    and between NODE_TO_DNA and COMPATIBILITY.

    Checks:
      1. Every node in knowledge_graph_g1_3.json appears in NODE_TO_DNA.
      2. Every DNA concept in NODE_TO_DNA appears in COMPATIBILITY.

    Returns:
        List of error strings. Empty list = coverage is complete.
    """
    errors: List[str] = []

    # Load knowledge graph node IDs
    kg_node_ids: set = set()
    try:
        with _KG_PATH.open(encoding="utf-8") as f:
            kg_data = json.load(f)
        kg_node_ids = set(kg_data.get("nodes", {}).keys())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        errors.append(f"Could not load knowledge_graph_g1_3.json: {exc}")
        return errors

    # 1. Every KG node must appear in NODE_TO_DNA
    for node_id in sorted(kg_node_ids):
        if node_id not in NODE_TO_DNA:
            errors.append(
                f"Knowledge graph node '{node_id}' is missing from NODE_TO_DNA."
            )

    # 2. Every DNA concept in NODE_TO_DNA must appear in COMPATIBILITY
    all_concepts_in_registry: set = set()
    for concepts in NODE_TO_DNA.values():
        all_concepts_in_registry.update(concepts)

    for concept in sorted(all_concepts_in_registry):
        if concept not in COMPATIBILITY:
            errors.append(
                f"NODE_TO_DNA concept '{concept}' is missing from COMPATIBILITY."
            )

    return errors


def validate_all() -> bool:
    """
    Run all compatibility and coverage checks and print a summary.

    Returns:
        True if all checks pass, False if any errors were found.
    """
    compat_errors = validate_compatibility_table()
    coverage_errors = validate_registry_coverage()
    all_errors = compat_errors + coverage_errors

    total_checks = 2
    passed = sum([not compat_errors, not coverage_errors])

    print(f"\nCompatibility validation: {passed}/{total_checks} check groups passed.")

    if compat_errors:
        print("  FAIL compatibility_table:")
        for e in compat_errors:
            print(f"    - {e}")
    else:
        print("  PASS compatibility_table")

    if coverage_errors:
        print("  FAIL registry_coverage:")
        for e in coverage_errors:
            print(f"    - {e}")
    else:
        print("  PASS registry_coverage")

    return not all_errors


# ─── entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ok = validate_all()
    sys.exit(0 if ok else 1)
