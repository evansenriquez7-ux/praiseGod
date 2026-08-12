"""
Practice Generation — Capability Contract Validator (§6)

The problem this solves
-----------------------
`registry.py`'s `_parse_competency_bounds` is ~1,300 lines of keyword matching that
*infers* machine bindings from English competency prose ("count by 2s" -> skip_interval,
"capacit" -> measurement_type). Four of the five known defect shapes are that inference
guessing wrong: a key consumed but never bound, one text match too broad, a formatter
gated off the node that needs it, a boundary defined twice. For 151 nodes this has been
hand-patched node by node. Branch count grows with nodes and *collisions* grow faster,
so it does not survive grade 4, let alone 12.

The fix is to stop inferring. Each node **declares** what its competency requires, in
`data/skeletons/vocab_annotation.json` (the hand-authored source; the knowledge graph is
a build artifact and anything typed into it dies on the next rebuild). This module then
checks the declaration against both the curriculum text and the pipeline.

Three checks, and the first two are what keep the declaration honest
-------------------------------------------------------------------
§6A **provenance** — every `clause` is a literal substring of the node's own `competency`.
    Blocks *invention*: a requirement the curriculum never states cannot be declared.

§6B **coverage** — every content word of `competency` appears in at least one `clause`.
    Blocks *omission*, which is the loophole that would otherwise gut this whole design:
    an agent that cannot render "draw" could simply not declare "draw", and §6C would
    pass trivially. Coverage forces the declaration to account for every word the
    curriculum wrote.

    Together, §6A and §6B make the clauses *tile* the competency — which is AGENTS.md
    Content Rule 3 ("nothing beyond the curriculum's explicit scope, nothing less than
    its full scope") enforced mechanically rather than by review.

§6C **required ⊆ provided** — every declared capability maps to something the node's
    reachable (DNA, formatter, variant) space can actually produce. A capability with no
    provider is not a warning and not a judgment call: it is a named failure that says
    which node, which clause, and what to build. That message is the point of this module
    — it converts "an agent decided this node was too hard" into a work item.

No graceful fallbacks (AGENTS.md Protocol 3). A node with no `requires` block is a loud
failure, never a skip — `if "requires" not in node: continue` is precisely the bug that
let 94 non-PASS judgment reviews escape every content check.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from backend.app.practice_gen.compatibility import COMPATIBILITY, VARIANTS_BY_DNA
from backend.app.practice_gen.registry import (
    NODE_TO_DNA,
    get_all_node_ids,
    get_node_competency_bounds,
    get_node_info,
)

# Function words that carry no requirement. Kept deliberately generous: a word that
# belongs here is one no generator could ever be asked to "produce". Anything
# contentful must be covered by a clause, or listed in the node's own
# `requires_ignore` where the omission is visible in review and in the diff.
_STOPWORDS: Set[str] = {
    "a", "an", "and", "or", "the", "of", "to", "in", "on", "for", "with", "by", "as",
    "at", "from", "into", "up", "down", "that", "this", "these", "those", "is", "are",
    "be", "been", "such", "according", "using", "use", "used", "including", "includes",
    "include", "variety", "appropriate", "given", "e", "g", "i", "eg", "ie", "etc",
    "than", "then", "it", "its", "their", "them", "other", "others", "also", "may",
    "can", "will", "shall", "each", "any", "all", "both", "either", "neither",
}

# The curriculum-to-pipeline interface. A declared capability id is *provided* when one
# of these concrete artifacts is reachable for the node. This table is deliberately
# explicit rather than inferred -- inference is the thing this module exists to replace.
#
#   variants: (variant_key, variant_value) pairs; provided if the node has a DNA whose
#             VARIANTS_BY_DNA[dna][key] contains value.
#   formatters: formatter names; provided if the node has a DNA whose COMPATIBILITY[dna]
#             lists one of them.
#
# A capability absent from this table has NO provider, which is the correct and useful
# answer for anything the pipeline cannot yet do. Do not add an entry to silence a
# failure -- add one only when the artifact genuinely exists.
CAPABILITY_PROVIDERS: Dict[str, Dict[str, List[Any]]] = {
    # --- geometric_lines (mat_g3_mg_q1_5) ---
    "recognize_line_relationships": {"variants": [("task_type", "identify_name")]},
    # The node's competency bounds pin concept_type to this one value, which is why forcing
    # the other two changes nothing -- that is the clamp working, not a dead key. A rendered
    # sample confirms the content: seed 42 -> "Two lines that cross at exactly one point are
    # called ___." -> "intersecting lines". One value bundles all three relationships, so
    # §6C can only ask whether the node reaches it; whether a given seed renders
    # *perpendicular* rather than only *parallel* is a §6D (exercised) question.
    "parallel_lines": {"variants": [("concept_type", "parallel_intersecting_perpendicular")]},
    "intersecting_lines": {"variants": [("concept_type", "parallel_intersecting_perpendicular")]},
    "perpendicular_lines": {"variants": [("concept_type", "parallel_intersecting_perpendicular")]},
    # "draw_line_relationships" is deliberately ABSENT -- geometric_lines offers only
    # ["mcq"] and no drawing formatter exists anywhere. That absence is the point: it is
    # what turns mat_g3_mg_q1_5 into a named build item instead of a node an agent declines.

    # --- shapes_2d (mat_g1_mg_q1_1) ---
    "compare_shapes": {"variants": [("task_type", "compare_shapes")]},
    "two_dimensional_shapes": {"variants": [("shape_set", "basic_triangles_rectangles_squares")]},
    # "distinguish_shapes", "sides_of_a_shape" and "corners_of_a_shape" are deliberately
    # ABSENT, and this is the mapping the loop's §2b singled out as suspect. Earlier
    # revisions pointed them at `task_type=identify_name` and `task_type=count_sides_corners`.
    # Both values are declared by the DNA, but this node's competency bounds pin
    # `task_type='compare_shapes'`, so the student path selects `compare_shapes` on 100/100
    # seeds and can never reach either one. They named a value that exists and is listed but
    # is unreachable *here* -- which is precisely the Rule 9 defeat, and precisely what the
    # clamp intersection in `_provided_for_node` now catches on its own.
    # "shape_features_as_comparison_basis" is ABSENT because nothing varies features as a
    # comparison axis; the bound serves one fixed comparison task.

    # --- counting (mat_g1_na_q1_0) ---
    "count_forward_from_a_given_number": {"variants": [("direction", "forward")]},
    "count_backward_from_a_given_number": {"variants": [("direction", "backward")]},
    # `counting` names its ceiling axis "range", not "max_value" -- the bound key is
    # per-DNA, so the provider lists every key that can carry a ceiling.
    "range_up_to_100": {"bounds": ["range", "max_value", "max_count", "max_sum"]},
    # "count_objects_to_a_total", "identify_a_number_relative_to_another",
    # "identify_one_more_than_a_number" and "identify_one_less_than_a_number" deliberately
    # ABSENT -- the competency names one-more/one-less explicitly ("identifying a number
    # that is 1 more or 1 less") and `counting` has no task_type for either.

    # --- mass_capacity (mat_g3_mg_q2_3) ---
    # Measured over 200 student-path seeds: mL appears in 97 and L in 103, so the node
    # genuinely serves both units the competency names. (An earlier probe here forced
    # `unit` and saw one rendering, and briefly read that as a dead key; it was the
    # competency-bound clamp pinning measurement_type/task_type, and the DNA choosing the
    # unit itself. Census the rendered output before calling a key dead.)
    "measure_capacity": {"variants": [("task_type", "read_measurement"),
                                      ("measurement_type", "capacity")]},
    "liters": {"variants": [("unit", "l")]},
    "milliliters": {"variants": [("unit", "ml")]},
    # "capacity_of_a_container" and "measuring_tools_for_capacity" deliberately ABSENT --
    # no tool concept exists in the DNA, so "using appropriate measuring tools" is unserved.

    # --- bar_graphs (mat_g3_dp_q3_1) ---
    "present_data": {"formatters": ["bar_chart_set"]},
    "single_bar_graph": {"formatters": ["bar_chart_set", "bar_chart_read"]},
    "horizontal_bar_graph": {"variants": [("orientation", "horizontal")]},
    "vertical_bar_graph": {"variants": [("orientation", "vertical")]},
    # "data_table" and "data_set" deliberately ABSENT -- the competency says "in tables AND
    # single bar graphs"; COMPATIBILITY["bar_graphs"] offers only the two bar-chart formatters.

    # --- multiplication (mat_g2_na_q3_1) ---
    "illustrate_multiplication": {"formatters": ["array_grid_set"]},
    "write_multiplication_sentence": {"formatters": ["mcq", "cloze"]},
    "array": {"formatters": ["array_grid_read", "array_grid_set"]},
    "pictorial_model": {"formatters": ["array_grid_read", "array_grid_set"]},
    "numeral_form": {"formatters": ["mcq", "cloze"]},
    # "multiplication_as_repeated_addition", "concrete_model",
    # "groups_of_equal_quantities", "counting_by_multiples" and
    # "equal_jumps_on_a_number_line" deliberately ABSENT -- the competency enumerates seven
    # representations and `multiplication` declares variants for none of them.
}


def _content_words(text: str) -> List[str]:
    """Lowercased alphanumeric tokens of `text`, minus function words."""
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())
    return [t for t in tokens if t not in _STOPWORDS]


def _validate_provenance(node_id: str, competency: str, requires: List[Dict]) -> List[str]:
    """§6A — a clause the competency does not contain is invented, not declared."""
    errs: List[str] = []
    hay = competency.lower()
    for i, req in enumerate(requires):
        clause = str(req.get("clause", "")).strip()
        if not clause:
            errs.append(
                f"{node_id}: requires[{i}] ({req.get('id')!r}) has no 'clause'. Every "
                f"requirement cites the competency text it comes from."
            )
            continue
        if clause.lower() not in hay:
            errs.append(
                f"{node_id}: requires[{i}] ({req.get('id')!r}) cites clause {clause!r}, "
                f"which does not appear in the node's competency. Declaring a requirement "
                f"the curriculum never states is invention (AGENTS.md Content Rule 4)."
            )
    return errs


def _validate_coverage(node_id: str, competency: str, requires: List[Dict],
                       ignore: List[str]) -> List[str]:
    """§6B — a competency word no clause covers is a requirement silently dropped."""
    covered: Set[str] = set()
    for req in requires:
        covered.update(_content_words(str(req.get("clause", ""))))
    covered.update(w.lower() for w in ignore)

    missing = [w for w in _content_words(competency) if w not in covered]
    if not missing:
        return []
    return [
        f"{node_id}: competency words {sorted(set(missing))} are covered by no requirement "
        f"clause. Either declare the requirement they describe, or list them in "
        f"'requires_ignore' with the reason. Silently dropping a competency word is how a "
        f"node passes while never generating what it was written to teach."
    ]


def _bound_restricts_to(bound: Any) -> Set[str] | None:
    """
    The set of values a competency bound permits for a *discrete* variant key, or None
    when the bound does not restrict a variant that way.

    A scalar bound pins the key to one value; a list bound restricts it to its members.
    A 2-tuple is always a continuous (min, max) range, never a discrete pair -- see
    docs/pgen_hardening.md -- so it restricts no variant and returns None.
    """
    if isinstance(bound, tuple):
        return None
    if isinstance(bound, (str, int)) and not isinstance(bound, bool):
        return {str(bound)}
    if isinstance(bound, list):
        return {str(b) for b in bound}
    return None


def _provided_for_node(node_id: str) -> Dict[str, Set[str]]:
    """
    The concrete artifacts reachable for this node **on the student path**.

    `VARIANTS_BY_DNA` is what a DNA *declares*; it is not what the node can serve.
    `_parse_competency_bounds` clamps discrete variant keys per node, and `is_student_path`
    applies that clamp -- so a node whose bounds pin `task_type='compare_shapes'` can never
    select `identify_name`, however loudly its DNA declares that value.

    Intersecting the declaration with the clamp is what stops a capability from being
    reported as provided by a variant value the student path can never reach. Without it,
    §6C answers "does some DNA list this value" when the question is "can this node produce
    it" -- and those diverge exactly on the nodes whose competency is narrower than its DNA.
    """
    dnas = NODE_TO_DNA.get(node_id) or []
    bounds = get_node_competency_bounds(node_id) or {}
    variants: Set[str] = set()
    formatters: Set[str] = set()
    for dna in dnas:
        for key, values in (VARIANTS_BY_DNA.get(dna) or {}).items():
            allowed = _bound_restricts_to(bounds[key]) if key in bounds else None
            for v in values:
                if allowed is not None and str(v) not in allowed:
                    continue
                variants.add(f"{key}={v}")
        formatters.update(COMPATIBILITY.get(dna) or [])
    return {"variants": variants, "formatters": formatters}


def _validate_provision(node_id: str, requires: List[Dict]) -> List[str]:
    """§6C — required ⊆ provided. An unprovided capability is a build item, named."""
    errs: List[str] = []
    avail = _provided_for_node(node_id)
    dnas = NODE_TO_DNA.get(node_id) or []

    for req in requires:
        cap = str(req.get("id", ""))
        spec = CAPABILITY_PROVIDERS.get(cap)
        if spec is None:
            errs.append(
                f"{node_id}: competency requires {cap!r} (from clause "
                f"{req.get('clause')!r}), but no pipeline artifact provides it. "
                f"Reachable DNAs: {dnas or '[]'}. Build the formatter/variant/dd/DNA that "
                f"produces it and register it in CAPABILITY_PROVIDERS "
                f"(see docs/pgen_hardening.md Part 1) -- this is the fix, not a reason to defer "
                f"the node (AGENTS.md Content Rule 4)."
            )
            continue

        ok = any(f"{k}={v}" in avail["variants"] for k, v in spec.get("variants", []))
        ok = ok or any(f in avail["formatters"] for f in spec.get("formatters", []))
        # A numeric ceiling is provided by the node's competency bounds rather than by
        # a variant value -- that is the one part of _parse_competency_bounds worth
        # keeping, since a range genuinely is derivable from "up to 100".
        if not ok and spec.get("bounds"):
            bounds = get_node_competency_bounds(node_id) or {}
            ok = any(b in bounds for b in spec["bounds"])
        if not ok:
            errs.append(
                f"{node_id}: capability {cap!r} (clause {req.get('clause')!r}) has "
                f"providers registered {spec}, but none is reachable from this node's "
                f"DNAs {dnas}. Either the node is mapped to the wrong DNA, or the "
                f"provider is gated off the node that needs it."
            )
    return errs


def validate_capability_declarations(node_ids: List[str] | None = None) -> List[str]:
    """Run §6A/§6B/§6C over every registered node. Returns a flat list of failures."""
    errs: List[str] = []
    for node_id in (node_ids if node_ids is not None else get_all_node_ids()):
        meta = get_node_info(node_id)
        competency = str((meta or {}).get("competency", "")).strip()
        if not competency:
            errs.append(f"{node_id}: no competency text in the knowledge graph.")
            continue

        requires = (meta or {}).get("requires")
        if requires is None:
            errs.append(
                f"{node_id}: no 'requires' declaration. Add one to "
                f"data/skeletons/vocab_annotation.json, authored from the competency text "
                f"alone (see docs/pgen_hardening.md Part 1). Undeclared nodes are not skipped."
            )
            continue
        if not isinstance(requires, list) or not requires:
            errs.append(f"{node_id}: 'requires' must be a non-empty list of requirement records.")
            continue

        ignore = (meta or {}).get("requires_ignore") or []
        errs += _validate_provenance(node_id, competency, requires)
        errs += _validate_coverage(node_id, competency, requires, ignore)
        errs += _validate_provision(node_id, requires)
    return errs


if __name__ == "__main__":
    import sys

    failures = validate_capability_declarations()
    if failures:
        print(f"Capability contract: {len(failures)} failure(s).")
        for f in failures:
            print(f"  - {f}")
    else:
        print("Capability contract: all nodes declare, cite, cover, and are provided for.")
    sys.exit(1 if failures else 0)
