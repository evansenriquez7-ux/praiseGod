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
import re
import sys
from pathlib import Path
from typing import List

from ..compatibility import COMPATIBILITY
from ..registry import NODE_TO_DNA, get_node_formatters
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
        # PROTOCOL 5 CORRECTION, 2026-08-13. These two expected values encoded an
        # off-by-one that the parser shared: "less than N" was parsed, and asserted,
        # as an INCLUSIVE ceiling of N. The competency text is the ground truth and
        # it says *less than* -- "less than 10 000" admits 9999, not 10000, and
        # "less than 100" admits 99, not 100. Blind reviewers scored two nodes FAIL
        # on exactly this, quoting the operand back: "Team A scored 20" on a node
        # whose sentence reads "both numbers are less than 20", and three items
        # using exactly 100 on mat_g2_na_q2_5.
        #
        # The cases exist to pin magnitude-vs-digit-width parsing, which they still
        # do; only the boundary moves, and it moves STRICTER (99 < 100), so this
        # tightens the check rather than weakening it.
        ("mat_g3_na_q2_4", "subtraction", {"max_minuend": (1, 9999)}),  # "less than 10 000"
        ("mat_g1_na_q3_4", "subtraction", {"max_minuend": (1, 99)}),    # "less than 100"
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



def validate_advertised_formatters_are_servable() -> List[str]:
    """
    §2B — every formatter a node advertises must actually generate for that node.

    `get_node_formatters()` unions `COMPATIBILITY` across the node's DNAs. Nothing
    narrows that union per node, so a node advertises whatever any of its DNAs can do,
    whether or not the orchestrator will serve it. Measured 2026-08-21:

        (node, advertised formatter) pairs : 690
          servable on every seed           : 454
          refused on EVERY seed            : 236   across 86 of 151 nodes
          refused on SOME seeds only       :   0

    Every refusal is STATIC — the pair never works, on any seed — so this is a
    declaration that is simply false, not a flaky generation. The Lab builds its
    formatter menu from this list, so a third of the offerings raise when selected.

    The same missing mechanism showed up from the other direction on
    `mat_g3_na_q3_1`: its competency is entirely about multiplication properties, an
    array can depict none of them, and there is no way to say so — §1C-coverage reports
    "the execution matrix is empty for array_grid_read" and nothing can act on it.

    This check does not fix either. It makes the class VISIBLE and impossible to
    reintroduce, which is the prerequisite for fixing it once rather than 236 times:
    whatever mechanism lands (a per-node exclusion list, a positive override, or
    deriving the list from the orchestrator's own eligibility test), this check is what
    proves the advertised list and the servable list agree afterwards.

    Deliberately empirical. It ASKS the orchestrator rather than reimplementing its
    eligibility rules, because a second copy of that logic would drift from the first —
    which is exactly how the false declarations here arose. One seed per pair is enough
    given the measurement above that no refusal is seed-dependent.
    """
    from backend.app.services.orchestrator import PracticeOrchestrator

    def _serves(node_id, fmt=None):
        try:
            PracticeOrchestrator.generate_problem(
                node_id=node_id, seed=11, formatter=fmt, is_lab=False,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            return exc

    from backend.app.practice_gen._generated_formatter_exclusions import (
        NODE_FORMATTER_EXCLUSIONS,
    )
    from backend.app.practice_gen.compatibility import COMPATIBILITY
    from ..registry import get_node_dnas

    errors: List[str] = []

    # DIRECTION 2, added after the narrowing shipped: a formatter that is EXCLUDED but
    # has become servable is silently withheld from the node. The first version of this
    # check only looked for "advertised but unservable", so the exclusion map could rot
    # in the direction that quietly narrows content and nothing would notice -- the
    # exact harm the narrowing was warned about. A one-directional check on a generated
    # file is a check that guards only the failure you happened to think of first.
    for node_id, excluded in NODE_FORMATTER_EXCLUSIONS.items():
        for fmt in excluded:
            if not any(fmt in COMPATIBILITY.get(d, []) for d in get_node_dnas(node_id)):
                continue  # no longer offered by any of the node's DNAs; not withheld
            if _serves(node_id, fmt) is True:
                errors.append(
                    f"{node_id}: formatter {fmt!r} is listed in NODE_FORMATTER_EXCLUSIONS "
                    f"but the orchestrator now serves it. The exclusion is stale and is "
                    f"withholding a formatter the node could use. Regenerate with: "
                    f"PYTHONPATH=. .venv/bin/python3 -m scripts.regen_formatter_exclusions"
                )

    for node_id in NODE_TO_DNA:
        # No try/except here on purpose. The first version of this check wrapped this
        # call and swallowed the exception, and because `get_node_formatters` was not
        # imported the swallow ate a NameError on all 151 nodes -- the check reported
        # "0 findings" while doing nothing whatsoever. A check that passes silently
        # because its own lookup failed is worse than no check at all (AGENTS.md rule
        # #3: no bare except, no warn-and-continue).
        advertised = get_node_formatters(node_id)
        refused: List[str] = []
        for fmt in advertised:
            try:
                PracticeOrchestrator.generate_problem(
                    node_id=node_id, seed=11, formatter=fmt, is_lab=False,
                )
            except Exception as exc:  # noqa: BLE001
                if "is not supported by any DNA" not in str(exc):
                    continue  # a content-level failure is another check's business
                refused.append(fmt)

        if not refused:
            continue

        # Two different defects hide behind the same message, and lumping them together
        # makes the finding unactionable. Separate them by asking whether the node can
        # produce ANYTHING when no formatter is pinned:
        #
        #   * every advertised formatter refused, yet auto-select works  -> the PINNED
        #     path is stricter than the auto path. That is a bug in the orchestrator,
        #     not a false advertisement, and excluding the formatters would hide it
        #     while narrowing the node's content. orchestrator.py already carries a
        #     comment about exactly this class ("any request that named a formatter,
        #     i.e. every Lab preview, raised 'Formatter X is not supported by any DNA'
        #     for the 22 nodes bound this way") -- so it has bitten before and the
        #     earlier exemption does not cover these.
        #
        #   * some advertised formatters serve and some do not -> the refusals are
        #     genuine restrictions (e.g. a node bound to task_type='model_representation'
        #     cannot use `mcq`, because an MCQ cannot represent a number with a model),
        #     and the advertised list is simply promising what it should not.
        auto = _serves(node_id)
        if len(refused) == len(advertised) and auto is True:
            errors.append(
                f"{node_id}: ALL {len(advertised)} advertised formatters {sorted(refused)} "
                f"are refused when pinned, yet the node generates fine when no formatter "
                f"is named. The pinned path is stricter than the auto path -- an "
                f"orchestrator defect, not a false advertisement. Do NOT fix this by "
                f"trimming the advertised list; that hides it and narrows the node."
            )
        else:
            for fmt in sorted(refused):
                errors.append(
                    f"{node_id} advertises formatter {fmt!r} via get_node_formatters(), "
                    f"but the orchestrator refuses it for this node while serving other "
                    f"advertised formatters, so the restriction is genuine. The advertised "
                    f"list is a union of COMPATIBILITY across the node's DNAs with no "
                    f"per-node narrowing, so it promises what cannot be served -- and the "
                    f"Lab builds its menu from it."
                )
    return errors



def validate_config_respects_competency() -> List[str]:
    """
    §2D — no configuration reachable through the serving API may serve content outside a
    node's competency.

    `PracticeOrchestrator.generate_problem` accepts `allowed_difficulties` and
    `allowed_contexts` from saved Lab configurations. Until 2026-08-27 it applied them with
    `rng.choice(opts)` and no validation, so the Lab path routed around every §1A/§1B/§1D
    bound the pipeline path enforces. Measured then, on mat_g3_na_q3_1 (competency binds
    task_type to four PROPERTY types, max_product=90):

        task_type='two_step'  ->  "What is 40 x 10?"     product 400, wrong task scope
        task_type='find_product' -> "What is 3 x 8?"     wrong task scope

    and the same route put NOT_YET_KNOWN vocabulary into Grade 1 ("737 is 7 hundreds,
    3 tens, and 7 ones" on mat_g1_na_q2_4). A configuration that was legal when it was
    saved is not legal forever; a competency can narrow underneath it.

    This asserts the refusal directly: for every node axis the competency binds to a value
    SET, offering a value outside that set must raise. Numeric (min, max) bounds are not
    covered here -- those are enforced by the generators and asserted by §1A/§1B.
    """
    from backend.app.services.orchestrator import PracticeOrchestrator
    from ..registry import get_all_node_ids, get_node_dnas, get_node_competency_bounds

    errors: List[str] = []
    for node_id in get_all_node_ids():
        for dna in (get_node_dnas(node_id) or []):
            try:
                bounds = get_node_competency_bounds(node_id, dna) or {}
            except Exception:
                continue
            for axis, bound in bounds.items():
                # List bounds only -- see orchestrator._competency_allows: a tuple is a
                # numeric range (§1A/§1B) and a bare string is a scope sentinel in a
                # different vocabulary from the raw option values a config offers.
                if not isinstance(bound, list):
                    continue
                permitted = {str(x) for x in bound}
                intruder = f"__not_in_competency_{axis}__"
                if intruder in permitted:
                    continue
                try:
                    PracticeOrchestrator.generate_problem(
                        node_id=node_id, seed=11, is_lab=True,
                        allowed_difficulties={axis: [intruder]},
                    )
                except ValueError:
                    continue          # refused, which is the contract
                except Exception:
                    continue          # a content-level failure is another check's business
                errors.append(
                    f"{node_id}: a configuration offering {axis}={intruder!r} was SERVED, "
                    f"but the competency binds {axis} to {sorted(permitted)}. The saved-config "
                    f"path is bypassing curriculum gating (§2D) -- content outside the node's "
                    f"competency can reach a student through the Lab."
                )
    return errors



# The correct option's slot, measured across nodes at a fixed seed. 4 options -> 25% is
# uniform; this allows generous slack for an uneven number of options per node while still
# catching the defect, which was 93%.
_PLACEMENT_CEILING_PCT = 45
_PLACEMENT_SEEDS = (11, 42, 64)


def validate_option_placement() -> List[str]:
    """
    §2E — where the correct option sits must not be predictable from the seed.

    Measured 2026-08-28, before the fix, across 46 MCQ nodes:

        seed 11 -> correct option in slot 1 on 93% of nodes
        seed 64 -> slot 3 on 86%
        seed 42 -> slot 2 on 58%

    A pupil working a practice set at a given seed scored ~90% by always picking the same
    position, having done no mathematics. That invalidates the assessment, not the item.

    Every formatter DID call `rng.shuffle`. The fault was that `rng` is
    `random.Random(seed)` and had consumed a similar number of draws on every node by the
    time the shuffle ran, so the same seed put the answer in the same slot tree-wide --
    random within a node, correlated across nodes, which is precisely the axis a pupil
    experiences. `formatters/_option_order.py` now draws the ordering from a blake2b
    stream keyed by (node_id, seed); after the fix the worst concentration is 30%.

    This asserts the property across nodes, because per-node checks cannot see it: each
    node's own shuffle looked perfectly random the whole time.
    """
    import collections

    from backend.app.services.orchestrator import PracticeOrchestrator
    from ..registry import get_all_node_ids

    errors: List[str] = []
    for seed in _PLACEMENT_SEEDS:
        slots: "collections.Counter[int]" = collections.Counter()
        total = 0
        for node_id in get_all_node_ids():
            try:
                p = PracticeOrchestrator.generate_problem(
                    node_id=node_id, seed=seed, formatter="mcq", is_lab=False)
            except Exception:
                continue
            d = p if isinstance(p, dict) else p.__dict__
            fd = d.get("format_data") or {}
            options = fd.get("mcq_options") or fd.get("options") or []
            if not isinstance(options, list) or len(options) < 2:
                continue
            idx = next((i for i, o in enumerate(options)
                        if isinstance(o, dict) and o.get("is_correct")), None)
            if idx is None:
                continue
            slots[idx] += 1
            total += 1
        if total < 20:
            continue  # too few samples for the proportion to mean anything
        slot, count = slots.most_common(1)[0]
        pct = 100 * count // total
        if pct > _PLACEMENT_CEILING_PCT:
            errors.append(
                f"§2E option placement: at seed {seed} the correct option is in slot "
                f"{slot} on {pct}% of {total} nodes (ceiling {_PLACEMENT_CEILING_PCT}%). "
                f"A pupil can score ~{pct}% on a practice set by always picking that "
                f"position, without doing any mathematics. Distribution: {dict(sorted(slots.items()))}"
            )
    return errors



_REACH_SEEDS = 40

# Baseline measured 2026-08-28 with formatter_name recorded: 18 nodes advertise a
# formatter the student path never selects. Red baseline, so a floor that may only SHRINK
# (Mandate §5); the 18 are tracked as content/routing work, not something to widen around.
_REACH_FLOOR = 18

# A node needs this many successful generations before its unreachable set means
# anything. Half the seed budget: enough for a formatter with any real selection
# weight to appear, few enough that a node with genuine generation gaps is still
# measured rather than silently skipped.
_REACH_MIN_SAMPLES = _REACH_SEEDS // 2

# placement.py's forward-looking G4-G10 milestone ladder is the only file with
# dangling node ids today, and it is deliberate scaffolding. Floor 1 keeps it while
# failing any NEW file that starts naming nodes that do not exist.
_DANGLING_FLOOR = 1


def validate_advertised_formatters_are_reachable() -> List[str]:
    """
    §2C — a formatter a node advertises must be REACHABLE by the path students take.

    §2B proves a formatter can be SERVED when pinned. Nothing proved auto-selection ever
    picks it. Measured 2026-08-28 over a 60-node sample: 12 (node, formatter) pairs across
    6 nodes were never served in 40 seeds, e.g. mat_g1_na_q3_5 never served
    ['emoji_pictorial', 'number_bond', 'number_line_read'].

    That is the documented emoji_pictorial defect class -- "registered and servable on
    both nodes, but the student path never selects it, so all seeds render visual_type
    None". Consequences: §1 spends its sweep validating content no pupil receives, the Lab
    offers a menu wider than what is served, and content variety is materially narrower
    than every report suggests.

    This reads `formatter_name`, which the orchestrator records on the served problem. Do
    NOT go back to inferring it from `format`: that holds the ROUTE name (`read_mcq`),
    which several formatters share, and a first attempt at fingerprinting mis-reported 62
    unreachable pairs where the real number was 12.
    """
    from backend.app.services.orchestrator import PracticeOrchestrator
    from ..registry import get_all_node_ids, get_node_formatters

    errors: List[str] = []
    for node_id in get_all_node_ids():
        advertised = set(get_node_formatters(node_id) or [])
        if len(advertised) < 2:
            continue
        served = set()
        generated = 0
        for seed in range(1, _REACH_SEEDS + 1):
            try:
                p = PracticeOrchestrator.generate_problem(
                    node_id=node_id, seed=seed, is_student_path=True)
            except Exception:
                continue
            generated += 1
            d = p if isinstance(p, dict) else p.__dict__
            if d.get("formatter_name"):
                served.add(d["formatter_name"])

        # A failed generation is not evidence that a formatter is unreachable -- it is no
        # evidence at all. Swallowing them with `continue` and then reporting the shortfall
        # as unreachability made this check LOAD-DEPENDENT: measured under a concurrent
        # mutation run it reported 27 nodes, and 18 on an idle machine, with identical
        # code. A gate whose answer depends on what else the machine is doing is not a
        # gate. Below this quorum the node is unmeasured and says nothing either way.
        if generated < _REACH_MIN_SAMPLES:
            continue
        unreachable = sorted(advertised - served)
        if unreachable:
            errors.append(
                f"{node_id}: advertises {unreachable} but the student path never selected "
                f"{'it' if len(unreachable) == 1 else 'them'} in {_REACH_SEEDS} seeds "
                f"(served: {sorted(served)}). §1 validates content no pupil receives, and "
                f"the Lab offers a menu wider than what is served (§2C)."
            )
    return errors



def validate_node_references_resolve() -> List[str]:
    """
    §2F — every node id written down in the app must exist in the registry.

    Measured 2026-08-28: `services/placement.py`'s MATATAG_PLACEMENT_MILESTONES lists 10
    node ids of which **7 do not exist** (`mat_g4_na_q1_1` ... `mat_g10_na_q1_1`).
    Requesting one raises `ValueError: No DNA mappings found`. It is LATENT today --
    `get_placement_sequence` is called from nowhere -- so this is preventive, not urgent.
    It becomes live the moment grade 4 lands, and nothing anywhere asserted that a node id
    referenced outside the registry resolves.

    That is the Scaling Mandate's concern in miniature: a reference that is fine while the
    grades in front of us are the only grades, and silently wrong the moment they are not.
    Held as a floor rather than zero so the forward-looking milestone ladder can stay,
    while any NEW dangling reference fails immediately.
    """
    import re

    from ..registry import get_all_node_ids

    repo = Path(__file__).resolve().parents[4]
    real = set(get_all_node_ids())
    pattern = re.compile(r'["\'](mat_g\d+_[a-z]+_q\d+_\d+)["\']')

    dangling: List[str] = []
    for path in sorted((repo / "backend" / "app").rglob("*.py")):
        if "validation" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        missing = sorted({m for m in pattern.findall(text) if m not in real})
        if missing:
            dangling.append(
                f"{path.relative_to(repo)}: references {len(missing)} node id(s) absent "
                f"from the registry -- {missing[:6]}. Serving one raises "
                f"'No DNA mappings found' (§2F)."
            )
    if len(dangling) > _DANGLING_FLOOR:
        return dangling
    return []



def validate_all_competency_bounds_parse() -> List[str]:
    """
    §2G — every node's competency bounds must parse to a well-formed result, tree-wide.

    `validate_competency_bounds_parsing` above is a ~20-row table of hand-written
    (node, dna, expected_bounds) cases, all Grade 1-3. It is a legitimate regression
    fixture and it cannot grow on its own: when Grade 4 introduces a `concept` vocabulary
    nobody has seen, the parser can mis-parse it silently while that table still passes.

    Scaling Mandate #4 -- "never scope a check to the grades in front of you". So the
    fixture keeps its exact cases and this asserts the PROPERTY across every node that
    exists, including ones added later:

      * bounds parse without raising;
      * every value is a shape the pipeline knows how to consume -- a (min, max) tuple, a
        list of literals, or a scalar sentinel string/number. Anything else (a dict, a
        None inside a list, a bare object) is a parse the generators cannot act on;
      * a (min, max) tuple is ordered.

    A new grade inherits this automatically. The fixture proves specific readings; this
    proves the parser never returns nonsense on anything in the tree.
    """
    from ..registry import get_all_node_ids, get_node_dnas, get_node_competency_bounds

    errors: List[str] = []
    for node_id in get_all_node_ids():
        for dna in (get_node_dnas(node_id) or []):
            try:
                bounds = get_node_competency_bounds(node_id, dna)
            except Exception as exc:  # noqa: BLE001 - naming the node beats a bare traceback
                errors.append(
                    f"{node_id}/{dna}: competency bounds failed to parse ({type(exc).__name__}: "
                    f"{str(exc)[:90]}). The generators cannot be bound for this node (§2G)."
                )
                continue
            if bounds is None:
                continue
            if not isinstance(bounds, dict):
                errors.append(
                    f"{node_id}/{dna}: bounds parsed to {type(bounds).__name__}, not a dict (§2G)."
                )
                continue
            for axis, value in bounds.items():
                if isinstance(value, tuple):
                    if len(value) != 2:
                        errors.append(
                            f"{node_id}/{dna}: bound {axis}={value!r} is a {len(value)}-tuple; "
                            f"a tuple bound is always read as (min, max) (§2G).")
                    elif all(isinstance(v, (int, float)) for v in value) and value[0] > value[1]:
                        errors.append(
                            f"{node_id}/{dna}: bound {axis}={value!r} has min > max (§2G).")
                elif isinstance(value, list):
                    if not value:
                        errors.append(
                            f"{node_id}/{dna}: bound {axis}=[] permits nothing, so no variant "
                            f"combination can survive filtering (§2G).")
                    elif any(v is None for v in value):
                        errors.append(
                            f"{node_id}/{dna}: bound {axis}={value!r} contains None (§2G).")
                elif not isinstance(value, (str, int, float, bool)):
                    errors.append(
                        f"{node_id}/{dna}: bound {axis} parsed to {type(value).__name__}, which "
                        f"is not a range, a value list, or a scalar sentinel (§2G).")
    return errors


# A competency that names BOTH sides of a dimension, in any wording a curriculum writer
# might use. Deliberately a pattern over the dimension WORD rather than a list of known
# axes: grade 4-10 will phrase this with words that do not exist in the tree today
# ("with and without renaming", "with or without remainders"), and a check that only
# knows "regrouping" would pass them all silently (Scaling Mandate #4).
_TWO_SIDED_CLAUSE = re.compile(r"with\s+(?:and|or)\s+without\s+([a-z]+)")


def validate_competency_scope_not_narrowed() -> List[str]:
    """
    §2H — a competency that names BOTH cases must not be bound to one of them.

    §2G proves bounds are well-FORMED. Nothing proved they are FAITHFUL to the competency
    they were parsed from, and a bound can be perfectly well-formed while asserting half
    of what the curriculum requires.

    That is not hypothetical. Until 2026-09-04 `_parse_competency_bounds` tested
    `"without regrouping" in text` with a bare substring match at one of the two sites
    that needed the distinction. "with and without regrouping" CONTAINS "without
    regrouping", so mat_g3_na_q2_1 ("sums up to 10 000, with and without regrouping") and
    mat_g2_na_q1_9 ("with or without regrouping") were pinned regrouping="none". Measured
    over 120 rendered seeds each: 0/120 items required a carry. The harness was green
    throughout -- every stage validated the content that WAS produced and nothing asked
    whether the competency's other half had gone missing. It took a blind human-style
    review of rendered samples to see it, which does not scale to seven more grades.

    The failure is silent by construction: narrowing a bound REMOVES items, so nothing
    downstream has anything to complain about. This check is the only thing that reads the
    competency text and the parsed bound together.

    Blind spot, stated plainly: this catches the "both cases named, one case bound" shape
    only. A competency clause the parser ignores ENTIRELY -- no bound emitted, no scope
    narrowed -- is invisible here, and is §6's job (capability provision), not this one.
    """
    from ..registry import (get_all_node_ids, get_node_dnas, get_node_info,
                            get_node_competency_bounds)

    errors: List[str] = []
    for node_id in get_all_node_ids():
        text = ((get_node_info(node_id) or {}).get("competency") or "").lower()
        dims = set(_TWO_SIDED_CLAUSE.findall(text))
        if not dims:
            continue
        for dna in (get_node_dnas(node_id) or []):
            try:
                bounds = get_node_competency_bounds(node_id, dna)
            except Exception:  # noqa: BLE001 - §2G owns parse failures; don't double-report
                continue
            if not isinstance(bounds, dict):
                continue
            for dim in sorted(dims):
                if dim not in bounds:
                    continue  # unbound is exactly right: the catalog offers both
                value = bounds[dim]
                # A list of >=2 options or a (min, max) range still admits both cases.
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    continue
                errors.append(
                    f"{node_id}/{dna}: the competency says \"with and/or without {dim}\" -- "
                    f"it names BOTH cases -- but the parsed bound pins {dim}={value!r} to "
                    f"one of them, so the other half of the competency can never be "
                    f"generated. Narrowing removes items silently: no other check fires. "
                    f"Fix the parse, do not widen this assertion (§2H)."
                )
    return errors


# 21, down from 65 on 2026-09-08. Remaining: task_type 6, unit_type 6, number_type 4,
# strategy 3, regrouping 2.
#
# The 44 cleared were all one thing -- a declaration offering a value the node's own
# competency excludes -- and none needed a generator change:
#   * 28 regrouping levels deeper than the node's digit ceiling can reach (a max of 19 is
#     two digits, one borrow position, and was offered four_places);
#   * 8 regrouping levels on estimation competencies, which round their operands before
#     operating and so have no borrow column to have a depth;
#   * 8 multiplication `tables` offered to missing_number nodes whose competency reads
#     "addition or subtraction sentences".
# Each filter reads the node's OWN parsed bounds, so none is a second copy of a generator
# rule -- the failure mode this check's docstring records from an earlier attempt.
#
# What remains is the docstring's *other* cause: a DNA declaring a variant it never
# implements for this shape. Those split two ways and must not be cleared in bulk --
# where the competency NAMES the capability ("Compare masses of objects" wanting
# task_type='compare_pair') the fix is to build it; where it does not (unit_type='cm' on
# a "using non-standard units" competency) the declaration is invention and goes.
#
# A FLOOR, not a hard gate, per Scaling Mandate #5, and it may only ever be lowered.
_PRODUCIBLE_FLOOR = 21


def validate_declared_variants_are_producible() -> List[str]:
    """
    §2I — a discrete variant a node DECLARES must be one the node can actually produce.

    §2B asks whether an advertised formatter can be served; §2C whether the student path
    ever reaches it. Neither asks the same question of the *variant* axes, and nothing did:
    a node can declare regrouping="four_places" while its competency caps sums at 20, which
    needs four carry positions and has one.

    This was invisible rather than absent. `judgment_packets._try_render` swallowed every
    such failure with `except Exception: return None`, so the candidate silently vanished
    from the packet: the reviewer saw fewer samples than intended, and nobody learned that a
    declared variant is unproducible. A silent skip and "there was nothing to render" look
    identical from outside, which is why this went 31 nodes deep before anyone measured it.

    Two distinct causes live behind one number, and the fix differs per cause -- do not
    treat the count as one bug:
      * the value is physically impossible at the node's ceiling (regrouping/borrow depth) --
        the declaration is wrong and should be narrowed;
      * the DNA declares a variant it never implements for this shape (unit_type='cm' on a
        G1 length node, number_type='multi_digit') -- a genuine capability gap, §6's subject.

    Deliberately does NOT predict feasibility from a formula. The first attempt at this
    check did, by calling the DNA's own `regrouping_is_feasible`, and over-filtered 3
    candidates on 2 nodes -- `generate_params` normalizes "one_place" to "ones" BEFORE
    applying that predicate, so a second copy of the rule disagreed with the generator.
    That is the same duplication that caused the §2H defect. Render it and see.
    """
    from .judgment_packets import (_variant_coverage_candidates, _render_sample,
                                   _VARIANT_COVERAGE_SEED_FLOOR)
    from ..registry import get_all_node_ids

    errors: List[str] = []
    for node_id in get_all_node_ids():
        candidates = _variant_coverage_candidates(node_id)
        for i, (axis, value) in enumerate(candidates):
            seed = _VARIANT_COVERAGE_SEED_FLOOR + i
            try:
                _render_sample(node_id, seed)
            except Exception as exc:  # noqa: BLE001 - the failure IS the finding
                errors.append(
                    f"{node_id}: declares {axis}={value!r} but cannot produce it "
                    f"(seed {seed}: {type(exc).__name__}: {str(exc)[:110]}). Either the "
                    f"declaration is wrong for this node's bounds, or the DNA never "
                    f"implements it here -- both leave the reviewer a thinner packet "
                    f"than the node claims to support (§2I)."
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
    monotonicity_errors = validate_kg_monotonicity()
    equivalence_errors = validate_lab_portal_equivalence()
    bounds_errors = validate_competency_bounds_parsing()
    servable_errors = validate_advertised_formatters_are_servable()
    config_errors = validate_config_respects_competency()
    placement_errors = validate_option_placement()
    reach_errors = validate_advertised_formatters_are_reachable()
    dangling_errors = validate_node_references_resolve()
    bounds_property_errors = validate_all_competency_bounds_parse()
    scope_errors = validate_competency_scope_not_narrowed()
    producible_errors = validate_declared_variants_are_producible()
    all_errors = (compat_errors + coverage_errors + monotonicity_errors
                  + equivalence_errors + bounds_errors + servable_errors + config_errors
                  + placement_errors
                  + (reach_errors if len(reach_errors) > _REACH_FLOOR else [])
                  + dangling_errors + bounds_property_errors + scope_errors
                  + (producible_errors if len(producible_errors) > _PRODUCIBLE_FLOOR else []))

    total_checks = 13
    passed = sum([not compat_errors, not coverage_errors, not monotonicity_errors,
                  not equivalence_errors, not bounds_errors, not servable_errors,
                  not config_errors, not placement_errors,
                  len(reach_errors) <= _REACH_FLOOR,
                  not dangling_errors,
                  not bounds_property_errors,
                  not scope_errors,
                  len(producible_errors) <= _PRODUCIBLE_FLOOR])

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

    if servable_errors:
        print("  FAIL advertised_formatters_are_servable:")
        for e in servable_errors[:10]:
            print(f"    - {e}")
        if len(servable_errors) > 10:
            print(f"    ... and {len(servable_errors) - 10} more.")
    else:
        print("  PASS advertised_formatters_are_servable")

    if config_errors:
        print("  FAIL config_respects_competency:")
        for e in config_errors[:10]:
            print(f"    - {e}")
        if len(config_errors) > 10:
            print(f"    ... and {len(config_errors) - 10} more.")
    else:
        print("  PASS config_respects_competency")

    if placement_errors:
        print("  FAIL option_placement:")
        for e in placement_errors:
            print(f"    - {e}")
    else:
        print("  PASS option_placement")

    if len(reach_errors) > _REACH_FLOOR:
        print(f"  FAIL formatters_reachable ({len(reach_errors)} node(s), floor {_REACH_FLOOR}):")
        for e in reach_errors[:10]:
            print(f"    - {e}")
        if len(reach_errors) > 10:
            print(f"    ... and {len(reach_errors) - 10} more.")
    else:
        print(f"  PASS formatters_reachable ({len(reach_errors)} node(s), floor {_REACH_FLOOR})")

    if dangling_errors:
        print("  FAIL node_references_resolve:")
        for e in dangling_errors:
            print(f"    - {e}")
    else:
        print(f"  PASS node_references_resolve (floor {_DANGLING_FLOOR} file(s))")

    if bounds_property_errors:
        print(f"  FAIL all_competency_bounds_parse ({len(bounds_property_errors)}):")
        for e in bounds_property_errors[:10]:
            print(f"    - {e}")
    else:
        print("  PASS all_competency_bounds_parse (every node, not a fixture list)")

    if scope_errors:
        print(f"  FAIL competency_scope_not_narrowed ({len(scope_errors)}):")
        for e in scope_errors[:10]:
            print(f"    - {e}")
    else:
        print("  PASS competency_scope_not_narrowed (no two-sided competency pinned to one side)")

    if len(producible_errors) > _PRODUCIBLE_FLOOR:
        print(f"  FAIL declared_variants_are_producible ({len(producible_errors)}, "
              f"floor {_PRODUCIBLE_FLOOR} — it GREW):")
        for e in producible_errors[:10]:
            print(f"    - {e}")
    else:
        print(f"  PASS declared_variants_are_producible ({len(producible_errors)}, "
              f"floor {_PRODUCIBLE_FLOOR}; floor may only shrink)")

    if bounds_errors:
        print("  FAIL competency_bounds_parsing:")
        for e in bounds_errors:
            print(f"    - {e}")
    else:
        print("  PASS competency_bounds_parsing")

    return not all_errors


# ─── entry point ──────────────────────────────────────────────────────────────

_SINGLE_CHECKS = {
    "reachable": ("formatters_reachable", validate_advertised_formatters_are_reachable),
    "config": ("config_respects_competency", validate_config_respects_competency),
    "placement": ("option_placement", validate_option_placement),
    "references": ("node_references_resolve", validate_node_references_resolve),
    "bounds_property": ("all_competency_bounds_parse", validate_all_competency_bounds_parse),
    "scope": ("competency_scope_not_narrowed", validate_competency_scope_not_narrowed),
    "producible": ("declared_variants_are_producible", validate_declared_variants_are_producible),
    "servable": ("advertised_formatters_are_servable", validate_advertised_formatters_are_servable),
}


def _run_single(name: str) -> int:
    """
    Run ONE check and report it the way validate_all does.

    Exists for the mutation harness. `validate_all` runs eleven checks and §2C alone
    sweeps 40 seeds x 151 nodes, so a mutation that plants in one of them was paying the
    whole module twice (baseline + mutated) -- minutes per mutation, for seven mutations.
    A check that is expensive to prove tends to end up unproven.
    """
    label, fn = _SINGLE_CHECKS[name]
    errors = fn()
    floor = {"formatters_reachable": _REACH_FLOOR,
             "node_references_resolve": _DANGLING_FLOOR,
             "declared_variants_are_producible": _PRODUCIBLE_FLOOR}.get(label, 0)
    over = (len(errors) > floor
            if label in ("formatters_reachable", "declared_variants_are_producible")
            else bool(errors))
    if label == "node_references_resolve":
        over = bool(errors)  # the floor is applied inside that check
    if over:
        print(f"  FAIL {label} ({len(errors)}):")
        for e in errors[:10]:
            print(f"    - {e}")
        return 1
    print(f"  PASS {label} ({len(errors)}, floor {floor})")
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="compatibility / registry checks")
    ap.add_argument("--only", choices=sorted(_SINGLE_CHECKS),
                    help="run a single check (used by the mutation harness)")
    args = ap.parse_args()
    if args.only:
        sys.exit(_run_single(args.only))
    sys.exit(0 if validate_all() else 1)
