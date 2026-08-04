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
from ._manifest import DNA_MODULE_MAP, KNOWN_FORMATTERS


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
        module_path = DNA_MODULE_MAP.get(concept)
        if module_path is None:
            errors.append(
                f"COMPATIBILITY: concept '{concept}' has no entry in "
                f"DNA_MODULE_MAP — cannot verify importability."
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
            if fmt not in KNOWN_FORMATTERS:
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


def validate_kg_monotonicity() -> List[str]:
    """
    Integrity lint check asserting that along every prerequisite edge:
    successor.cumulative ⊇ predecessor.cumulative ∪ predecessor.introduces.
    """
    errors: List[str] = []

    try:
        with _KG_PATH.open(encoding="utf-8") as f:
            kg_data = json.load(f)
        nodes = kg_data.get("nodes", {})
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        errors.append(f"Could not load knowledge_graph_g1_3.json: {exc}")
        return errors

    if not nodes:
        errors.append("Knowledge graph nodes are empty.")
        return errors

    # Branch ordering for chronological sorting
    BRANCH_ORDER = ["na", "mg", "dp"]

    def chronological_sort_key(node_id: str) -> tuple:
        parts = node_id.split("_")
        grade = int(parts[1][1:])
        branch = parts[2]
        quarter = int(parts[3][1:])
        index = int(parts[4])
        branch_rank = BRANCH_ORDER.index(branch) if branch in BRANCH_ORDER else 99
        return (grade, quarter, branch_rank, index)

    sorted_ids = sorted(nodes.keys(), key=chronological_sort_key)

    # Check global chronological monotonicity: successor.cumulative ⊇ predecessor.cumulative ∪ predecessor.introduces
    for i in range(len(sorted_ids) - 1):
        pred_id = sorted_ids[i]
        succ_id = sorted_ids[i + 1]
        pred = nodes[pred_id]
        succ = nodes[succ_id]

        # Concepts check
        pred_dnas = NODE_TO_DNA.get(pred_id, [])
        pred_concepts = (
            set(pred.get("cumulative_concepts", []))
            | set(pred.get("introduces_concepts", []))
            | set(pred_dnas)
        )
        succ_concepts = set(succ.get("cumulative_concepts", []))
        if not pred_concepts.issubset(succ_concepts):
            diff = pred_concepts - succ_concepts
            errors.append(
                f"KG Monotonicity Error (global): {succ_id}.cumulative_concepts does not contain "
                f"all concepts from predecessor {pred_id}. Missing: {diff}"
            )

        # Vocab check
        pred_vocab = set(pred.get("cumulative_vocab", [])) | set(pred.get("student_vocab", []))
        succ_vocab = set(succ.get("cumulative_vocab", []))
        if not pred_vocab.issubset(succ_vocab):
            diff = pred_vocab - succ_vocab
            errors.append(
                f"KG Monotonicity Error (global): {succ_id}.cumulative_vocab does not contain "
                f"all vocab from predecessor {pred_id}. Missing: {diff}"
            )

    return errors


def validate_lab_portal_equivalence() -> List[str]:
    """
    Assert that the Lab router's bridge scalar is dynamically linked to the portal's DIFFICULTY_LEVEL_MAP[4].
    """
    errors: List[str] = []
    from backend.app.practice_gen.dna.base import DIFFICULTY_LEVEL_MAP
    if 4 not in DIFFICULTY_LEVEL_MAP:
        errors.append("DIFFICULTY_LEVEL_MAP does not contain key 4 for Advanced tier.")
        
    router_path = Path(__file__).parent.parent.parent.parent / "routes" / "matatag_router.py"
    if router_path.exists():
        content = router_path.read_text(encoding="utf-8")
        if "bridge_scalar = 1.25" in content:
            errors.append("matatag_router.py still contains hardcoded 'bridge_scalar = 1.25'.")
        if "from backend.app.practice_gen.dna.base import DIFFICULTY_LEVEL_MAP" not in content:
            errors.append("matatag_router.py does not import DIFFICULTY_LEVEL_MAP from base.py.")
    return errors


def validate_competency_bounds_parsing() -> List[str]:
    """
    Unit test table for the registry bounds parser (`_parse_competency_bounds`).
    Asserts expected parsed discrete bounds for special-case nodes.
    """
    from ..registry import get_node_competency_bounds
    
    # Table of (node_id, dna_name, expected_bounds_subset)
    test_cases = [
        # 1. symmetry_slides
        # Ground Rule 2 correction (docs/pgen_hardening.md judgment review):
        # this table previously asserted mat_g1_mg_q4_0 bound to
        # 'slide_translation' and mat_g3_mg_q4_1 was left unrestricted --
        # both encoded the same bug the mat_g3_mg_q1_5/mat_g2_mg_q4_3 fixes
        # addressed. mat_g1_mg_q4_0's competency is rotation (half/quarter
        # turns); it "worked" before only because slide_translation has no
        # grade_min=1 items, so generate_params()'s old concept-ignoring
        # fallback happened to land back on rotation, the only grade-1
        # concept available -- masking the wrong bound with a second bug.
        # mat_g3_mg_q4_1 ("Identify shapes...by drawing the line of
        # symmetry") was never bound at all and so silently defaulted to
        # slide/translation content. Both are now explicitly bound.
        ("mat_g1_mg_q4_0", "symmetry_slides", {"concept": "rotation"}),
        ("mat_g2_mg_q1_2", "symmetry_slides", {"concept": "slide_translation"}),
        ("mat_g3_mg_q4_0", "symmetry_slides", {"concept": "slide_translation", "directions": "two_directions"}),
        ("mat_g3_mg_q4_1", "symmetry_slides", {"concept": "line_symmetry"}),
        ("mat_g3_mg_q4_2", "symmetry_slides", {"concept": "complete_symmetric_figure"}),
        ("mat_g2_mg_q1_0", "shapes_2d", {"shape_set": "extended_with_circles"}),
        ("mat_g2_mg_q1_1", "shapes_2d", {"shape_set": "composite_figures", "task_type": "compose_decompose"}),
        ("mat_g1_mg_q1_1", "shapes_2d", {"task_type": "compare_shapes"}),
        
        # 2. mass_capacity
        # Ground Rule 2 correction (docs/pgen_hardening.md judgment review):
        # this table previously asserted mat_g3_mg_q2_3/_4/_5 (all capacity
        # competencies) left measurement_type unrestricted -- that encoded
        # the same bug fixed for symmetry_slides/geometric_lines: leaving a
        # value "unrestricted" does not mean the DNA shows the requested
        # content, it means the DNA's own default (measurement_type="mass")
        # silently governs, so all 3 capacity nodes rendered 100%
        # mass-in-grams samples. Now bound explicitly both ways.
        ("mat_g3_mg_q2_0", "mass_capacity", {"measurement_type": "mass", "task_type": "read_measurement"}),
        ("mat_g3_mg_q2_1", "mass_capacity", {"measurement_type": "mass", "task_type": "estimate"}),
        ("mat_g3_mg_q2_2", "mass_capacity", {"measurement_type": "mass", "task_type": "compare"}),
        ("mat_g3_mg_q2_3", "mass_capacity", {"measurement_type": "capacity", "task_type": "read_measurement"}),
        ("mat_g3_mg_q2_4", "mass_capacity", {"measurement_type": "capacity", "task_type": "estimate"}),
        ("mat_g3_mg_q2_5", "mass_capacity", {"measurement_type": "capacity", "task_type": "compare"}),
        
        # 3. geometric_lines
        ("mat_g3_mg_q1_4", "geometric_lines", {"concept_type": "point_line_segment_ray"}),
        # Ground Rule 2 correction (docs/pgen_hardening.md judgment review):
        # this table previously asserted concept_type was left unrestricted
        # for mat_g3_mg_q1_5 ("Recognize and draw parallel, intersecting,
        # and perpendicular lines"). Unrestricted meant generate_params()
        # fell back to the DNA's hardcoded default concept_type
        # ("point_line_segment_ray"), so this G3 node could only ever
        # generate point/line/segment/ray-naming content and never actually
        # taught parallel/intersecting/perpendicular lines -- the exact
        # content its own competency text names. Fixed in
        # registry.py's _parse_competency_bounds to bind concept_type
        # explicitly; this fixture now asserts the corrected value.
        ("mat_g3_mg_q1_5", "geometric_lines", {"concept_type": "parallel_intersecting_perpendicular"}),
        ("mat_g2_mg_q4_3", "geometric_lines", {"concept_type": "straight_curved"}),

        # 4. subtraction — digit-width phrasing is not a magnitude.
        # The magnitude regex used to capture the digit count itself, so
        # "up to 2 digits" bound max_minuend=(1, 2) and mat_g3_na_q2_5 served
        # "2 - 2 = 0" at scalar 1.0 on a Grade 3 node. Nothing detected it:
        # §1A and §1A-reach both assert against the *parsed* ceiling, so a
        # mis-parsed bound immunises the node from the only checks that could
        # expose it. These three cases pin the width-vs-magnitude distinction,
        # which is the whole defect class rather than the three symptoms.
        ("mat_g3_na_q2_5", "subtraction", {"max_minuend": (1, 9999)}),   # "up to 4 digits"
        # ...and the magnitude phrasings that must keep parsing as magnitudes.
        ("mat_g3_na_q2_4", "subtraction", {"max_minuend": (1, 10000)}),  # "less than 10 000"
        ("mat_g1_na_q3_4", "subtraction", {"max_minuend": (1, 100)}),    # "less than 100"
    ]
    # Ground Rule 2 correction, 2026-08-02 (docs/pgen_hardening.md judgment
    # review, Phase D): mat_g3_na_q2_6/_7's ("up to 2 digits") cases above were
    # removed. This function's `dna_name` override only applies when it is
    # still one of the node's OWN registered DNAs (`registry.py`'s
    # get_node_competency_bounds: "dna_name if dna_name in dnas else
    # dnas[0]") -- and both nodes were remapped from ["addition",
    # "subtraction"] to ["order_of_operations"] (neither 2-operand DNA can
    # express "3 to 4 numbers ... observing correct order of operations"; see
    # HARDENING_EVIDENCE.md Phase D item 3). Requesting dna_name="subtraction"
    # for either node therefore silently falls back to dnas[0]
    # ("order_of_operations"), which has no "max_minuend" key at all --
    # correctly reproducing this test's own failure ("expected ... got
    # 'None'") once the mapping changed, not a parser regression. The
    # width-vs-magnitude regex fix this table exists to pin is still verified
    # by mat_g3_na_q2_5 ("up to 4 digits") and the two magnitude-phrasing
    # cases below, all still genuinely subtraction-mapped.
    
    errors: List[str] = []
    for node_id, dna_name, expected in test_cases:
        try:
            bounds = get_node_competency_bounds(node_id, dna_name)
            for key, expected_val in expected.items():
                actual_val = bounds.get(key)
                if expected_val is None:
                    # Expect key not to be in bounds, or to be default/unrestricted
                    if actual_val is not None:
                        errors.append(
                            f"Registry bounds parser for '{node_id}' ({dna_name}) expected key '{key}' "
                            f"to be unrestricted, but got '{actual_val}'."
                        )
                else:
                    if actual_val != expected_val:
                        errors.append(
                            f"Registry bounds parser for '{node_id}' ({dna_name}) expected key '{key}' "
                            f"to be '{expected_val}', but got '{actual_val}'."
                        )
        except Exception as e:
            errors.append(f"Failed to get bounds for node '{node_id}' ({dna_name}): {e}")
            
    return errors


def validate_all() -> bool:
    """
    Run all compatibility and coverage checks and print a summary.

    Returns:
        True if all checks pass, False if any errors were found.
    """
    compat_errors = validate_compatibility_table()
    coverage_errors = validate_registry_coverage()
    monotonicity_errors = validate_kg_monotonicity()
    equivalence_errors = validate_lab_portal_equivalence()
    bounds_errors = validate_competency_bounds_parsing()
    all_errors = compat_errors + coverage_errors + monotonicity_errors + equivalence_errors + bounds_errors

    total_checks = 5
    passed = sum([not compat_errors, not coverage_errors, not monotonicity_errors, not equivalence_errors, not bounds_errors])

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

    if monotonicity_errors:
        print("  FAIL kg_monotonicity:")
        for e in monotonicity_errors:
            print(f"    - {e}")
    else:
        print("  PASS kg_monotonicity")

    if equivalence_errors:
        print("  FAIL lab_portal_equivalence:")
        for e in equivalence_errors:
            print(f"    - {e}")
    else:
        print("  PASS lab_portal_equivalence")

    if bounds_errors:
        print("  FAIL competency_bounds_parsing:")
        for e in bounds_errors:
            print(f"    - {e}")
    else:
        print("  PASS competency_bounds_parsing")

    return not all_errors


# ─── entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ok = validate_all()
    sys.exit(0 if ok else 1)
