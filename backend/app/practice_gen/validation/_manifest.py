"""
Practice Generation — Validation Manifest

Central source of truth for the validation suite. Exposes the canonical
DNA module registry, known formatters, the helper to load DNA instances, and
CHECK_PHASE — which harness phase each contract §-ref belongs to.
"""

from __future__ import annotations

import importlib
from typing import Dict, Set

from backend.app.practice_gen.compatibility import COMPATIBILITY
from backend.app.practice_gen.adapter import FORMATTER_ROUTES
from backend.app.practice_gen.dna.base import DNA

# ─── Harness phase registry ──────────────────────────────────────────────────
#
# THE SEAM: does this check need an agent-authored artifact to exist before it can run?
#
#   no  -> PHASE 1. Reads only code, the knowledge graph and the declarations. Runnable
#          on a fresh clone, in the fix-until-green loop, by an agent that has authored
#          nothing yet.
#   yes -> PHASE 2. Reads validation_reports/judgment/ or validation_reports/attestation/,
#          so it cannot run until an agent has filed one. Spans sessions; gated on
#          Phase 1 being green, because a review or attestation is a judgment about
#          specific rendered seeds and any Phase 1 fix that changes generation
#          invalidates it.
#
# That test is decidable rather than a matter of taste, which is what makes it
# enforceable rather than a convention. It was decided per-ref on 2026-09-08 for §6
# alone; this is the same seam applied to all 35 refs, because until it was, "Phase 1
# is done" was not a claim the harness could make -- `run_all` had no --phase, 28 of the
# 35 refs carried no phase at all, and the only way to assert Phase 1 was to run ten
# commands by hand and read them, which is what the Definition of Done forbids.
#
# `validate_coverage`'s `check_phase_registry_8` holds this against run_all's
# CONTRACT_CHECKS in both directions, so a check cannot be added without declaring the
# phase it runs in. validate_capability derives its §6 view from here rather than
# keeping a second copy.
CHECK_PHASE: Dict[str, int] = {
    # -- Phase 1: artifact-free -------------------------------------------------------
    "§0": 1,            # pytest tests/unit
    "§1A": 1, "§1A-reach": 1, "§1B": 1, "§1C": 1, "§1C-reverse": 1, "§1C-coverage": 1,
    "§1D": 1, "§1E": 1, "§1F": 1, "§1G": 1, "§1H": 1, "§1I": 1,
    "§1J": 1, "§1K": 1, "§1M": 1,
    "§2": 1, "§2B": 1, "§2C": 1, "§2D": 1, "§2E": 1, "§2F": 1, "§2G": 1, "§2H": 1, "§2I": 1, "§2J": 1, "§2K": 1, "§2L": 1,
    "§3": 1,
    "§4": 1,
    # §6A/§6B/§6C are cited by findings but carry no CONTRACT_CHECKS row of their own;
    # they are phased here so validate_capability's partition gate can see them.
    "§6": 1, "§6A": 1, "§6B": 1, "§6C": 1, "§6D": 1, "§6E": 1,
    "§7": 1,
    "§8": 1,
    "§9": 1,
    "§10": 1,
    "§11": 1,           # validate_obligations: the student-path obligation manifest
    "§12": 1,           # consumed browserless React static-render evidence
    "§13": 1,           # component onAnswer value -> backend answers_match
    # -- Phase 2: needs an agent-authored artifact on disk ------------------------------
    "§5": 2,            # validation_reports/judgment/
    "§6F": 2, "§6G": 2, "§6H": 2,   # validation_reports/attestation/
}

# The refs that carry no CONTRACT_CHECKS row. Named so the completeness gate can tell
# "phased but unregistered, deliberately" from "phased but unregistered, by accident".
PHASE_ONLY_REFS: Set[str] = {"§6A", "§6B", "§6C"}


def refs_in_phase(phase: int) -> Set[str]:
    """Every §-ref registered to `phase`."""
    return {ref for ref, p in CHECK_PHASE.items() if p == phase}


# ─── Finding classification registry (owner ruling 27, H2) ───────────────────
#
# `run_all` exits 1 if INTEGRITY fails, else 2 if any CONTENT finding exists, else 0.
# Every assertion label the harness can emit (validate_coverage's §8 inventory) is
# classified here, and `run_all`'s `finding_class_registry_complete` holds this table to
# that inventory in BOTH directions: a label emitted but unclassified, or classified but
# emitted by nothing, is an integrity failure. A label printed at run time that this table
# does not name is an integrity failure too (`finding_label_unclassified`), so a new check
# cannot reach the verdict without someone deciding which kind of finding it reports.
#
# THE RULE (rulings 23, 27, 30-32; recorded in docs/phase2_hardening_completion_plan.md):
#   integrity -- the harness cannot trust its own verdict: a stage crashed or never ran,
#                a mutation proof does not hold, a digest-bound artifact is stale, two of
#                the harness's own registries disagree, a check's reach shrank, or the
#                GROUND TRUTH a check reads (the knowledge graph, `requires` /
#                `requires_ignore` and its lock, the parsed competency bounds) is missing,
#                malformed or tampered. Every unit-test failure (ruling 30). Remedy:
#                harness work.
#   content   -- a defect in what the pipeline under test produces or declares:
#                generators, DNAs, formatters, generator-owned tables, serving routes,
#                graders, and the filed review/attestation records (ruling 32). Remedy:
#                generator work. These are the generator work queue.
# A label whose findings can be EITHER kind is classified integrity (fail safe) and
# named in a comment, because an integrity failure reported as content is the worse
# error: harness work is done at exit 0 or 2, so it would certify a broken harness.
#
# NAMED LIMITS (Scaling Mandate 6):
#   * The class is per LABEL. A new failure mode folded into an existing label's error
#     list inherits that label's class without anyone deciding it.
#   * Matrix findings are classified by their check FAMILY (the f-string prefix §8
#     inventories), so every axis-specific variant of a family shares one class.
#   * A harness defect that surfaces AS a content finding (a broken harness making every
#     `pipeline_run` raise, say) is reported as content. Its volume is the only signal.
INTEGRITY = "integrity"
CONTENT = "content"

FINDING_CLASS: Dict[str, str] = {
    # -- run_all: the runner, its ledger and the unit suite (ruling 30) ---------------
    "unit_tests": INTEGRITY,
    "phase1_hermetic": INTEGRITY,
    "subtraction_candidate_pool_bounded": INTEGRITY,
    "packet_variant_coverage_uncapped": INTEGRITY,
    "packet_interest_pinned": INTEGRITY,
    "attester_provider_variant_stratification": INTEGRITY,
    "attester_clause_enumeration": INTEGRITY,
    "tree_state_certification": INTEGRITY,
    "renderer_invocation_isolation": INTEGRITY,
    "mutation_marker_invocation_isolation": INTEGRITY,
    "mutation_restore_purges_bytecode": INTEGRITY,
    "mutation_apply_is_all_or_nothing": INTEGRITY,
    "hint_contract_arithmetic": INTEGRITY,
    "hint_contract_stated_result": INTEGRITY,
    "hint_contract_stated_answer": INTEGRITY,
    "hint_contract_open_equation": INTEGRITY,
    "hint_contract_operation": INTEGRITY,
    "hint_contract_remainder": INTEGRITY,
    "hint_contract_roles": INTEGRITY,
    "hint_contract_direction": INTEGRITY,
    "hint_contract_unit": INTEGRITY,
    "hint_contract_medium": INTEGRITY,
    "hint_contract_response": INTEGRITY,
    "packet_cross_process_determinism": INTEGRITY,
    "hint_contract_visuals_classified": INTEGRITY,
    "hint_contract_enforced_at_serving": INTEGRITY,
    "hint_generation_fails_loud": INTEGRITY,
    "property_statement_key_matches_truth": INTEGRITY,
    "review_overall_matches_findings": INTEGRITY,
    "review_response_copy_not_overwritten": INTEGRITY,
    "contract_doc_matches_registry": INTEGRITY,
    "operator_doc_covers_registry": INTEGRITY,
    "two_direction_contract_match": INTEGRITY,
    "stage_failure_reaches_verdict": INTEGRITY,
    "stage_ledger_complete": INTEGRITY,
    "stage_phase_matches_manifest": INTEGRITY,
    "stage_crashed_": INTEGRITY,                 # family: stage_crashed_<stage name>
    "finding_class_registry_complete": INTEGRITY,
    "finding_label_unclassified": INTEGRITY,
    "verdict_integrity_exits_1": INTEGRITY,
    "verdict_content_exits_2": INTEGRITY,
    # -- §6 validate_capability ------------------------------------------------------
    # Tagged by the FUNCTION that emits each finding (`provision_findings_tagged`,
    # `attestation_findings_tagged`), never by message text.
    "capability_provenance_6A": INTEGRITY,       # `requires` absent or not cited: ground truth
    "capability_coverage_6B": INTEGRITY,         # competency words `requires` misses: ground truth
    "requires_ignore_locked_6B": INTEGRITY,      # human ground truth edited without its lock
    "capability_declarations_in_sync_6": INTEGRITY,  # the graph §6 reads is not the one authored
    "capability_phase_boundary_6": INTEGRITY,
    "capability_phase_partition_6": INTEGRITY,
    "capability_orphan_provider_6A": CONTENT,    # a generator-owned provider entry nothing requires
    "capability_provision_6C": CONTENT,
    "capability_generic_formatter_6D": CONTENT,
    "capability_nondiscriminating_bounds_6E": CONTENT,
    "capability_unattested_6F": CONTENT,         # §6F-§6H: filed records (ruling 32)
    "capability_contradicted_6F": CONTENT,
    "capability_stale_attestation_6F": CONTENT,
    "capability_attestation_options_recorded_6F": CONTENT,
    "capability_attestation_visual_evidence_6F": CONTENT,
    "attester_reasoning_skeleton_6G": CONTENT,
    "attester_evidence_6G": CONTENT,
    "attester_plurality_6H": CONTENT,
    "capability_contract": CONTENT,              # run_all's rollup of every CONTENT §6 finding
    # -- §7 validate_census ----------------------------------------------------------
    "census": INTEGRITY,
    "census_nodes": INTEGRITY,
    "census_unit_tests": INTEGRITY,
    "census_mutations": INTEGRITY,
    "census_variant_candidates": INTEGRITY,
    # -- §2 validate_compat ----------------------------------------------------------
    "compatibility_table": CONTENT,
    "registry_coverage": CONTENT,
    "kg_monotonicity": INTEGRITY,                # the KG's cumulative vocab is §1D's ground truth
    "lab_portal_equivalence": CONTENT,
    "advertised_formatters_are_servable": CONTENT,
    "config_respects_competency": CONTENT,
    "option_placement": CONTENT,
    "formatters_reachable": CONTENT,
    "node_references_resolve": CONTENT,
    # The parsed competency bounds are what §1A/§1B certify against, so a bound that
    # does not parse, or parses narrower than the competency, is a ground-truth defect.
    "all_competency_bounds_parse": INTEGRITY,
    "competency_scope_not_narrowed": INTEGRITY,
    "competency_bounds_parsing": INTEGRITY,
    "declared_variants_are_producible": CONTENT,
    "medium_composition": CONTENT,
    "batch_matches_single": CONTENT,
    # -- §8 validate_coverage --------------------------------------------------------
    "assertion_coverage_8": INTEGRITY,
    "assertion_allowlist_paid_8": INTEGRITY,
    "assertion_allowlist_phantom_8": INTEGRITY,
    "assertion_asserts_unknown_8": INTEGRITY,
    "assertion_undeclared_check_8": INTEGRITY,
    "check_phase_registry_8": INTEGRITY,
    "silent_path_disposition_8": INTEGRITY,
    "mutation_proof_integrity_8": INTEGRITY,
    # -- §3 validate_dna -------------------------------------------------------------
    "dna_structure": CONTENT,
    "dna_difficulty_feasibility": CONTENT,
    # -- §2L validate_exhibit --------------------------------------------------------
    "variant_not_exhibited_2L": CONTENT,
    "attester_packet_refused_2L": CONTENT,
    # -- §10 validate_grade ----------------------------------------------------------
    "grading_contract_10": CONTENT,
    "grading_contract_floor_10": CONTENT,
    "grading_refusal_10": CONTENT,
    "grading_equivalence_10": CONTENT,
    "grading_obligation_10": INTEGRITY,          # an obligation the check could not execute
    "grading_hermetic_10": INTEGRITY,
    # -- interest invariance -----------------------------------------------------------
    "interest_invariance": CONTENT,
    "interest_theme_visibility": CONTENT,
    # -- §5 validate_judgment: filed records (ruling 32) -----------------------------
    "judgment_review_schema_5": CONTENT,
    "judgment_packet_integrity_5": CONTENT,
    "judgment_clause_coverage_5": CONTENT,
    "judgment_sample_assessments_5": CONTENT,
    "judgment_dispatch_provenance_5": CONTENT,
    "judgment_review_freshness_5": CONTENT,
    "judgment_options_recorded_5": CONTENT,
    "judgment_visual_evidence_5": CONTENT,
    "judgment_quote_provenance_5": CONTENT,
    "judgment_rationale_verbatim_5": CONTENT,
    "judgment_rationale_skeleton_5": CONTENT,
    "judgment_reviewer_plurality_5": CONTENT,
    "judgment_reviews": CONTENT,                 # run_all's rollup print for §5
    # -- §1J validate_language -------------------------------------------------------
    "count_noun_agreement_1J": CONTENT,
    "unclassified_pupil_text_1J": INTEGRITY,     # a payload field the lint does not reach
    # -- §1H validate_matrix (declared) ----------------------------------------------
    "per_node_applicability_1H": INTEGRITY,
    "coverage_regression_1H": INTEGRITY,
    # -- §11 validate_obligations ----------------------------------------------------
    "obligation_derivations_agree": INTEGRITY,
    "obligation_routes_reachable": CONTENT,
    "obligation_dimension_coverage_11": INTEGRITY,
    "obligation_execution_11": CONTENT,
    "obligation_benchmark_11": INTEGRITY,        # MIXED (absent/stale/failing): fail safe
    "obligation_release_shards_11": INTEGRITY,
    # -- §1K / §1M -------------------------------------------------------------------
    "option_degeneracy_1K": CONTENT,
    "dangling_visual_reference_1M": CONTENT,
    # -- §9 / §12 / §13 validate_render ----------------------------------------------
    "render_contract_9": CONTENT,
    "render_contract_floor_9": CONTENT,
    "frontend_artifact_fresh_12": INTEGRITY,     # stale digest-bound evidence
    "frontend_static_render_12": CONTENT,
    "rendered_visual_description_12": INTEGRITY,  # evidence derivation, not the component
    "frontend_answer_roundtrip_13": CONTENT,
    "renderer_registration_disposition_12": INTEGRITY,
    # -- §1D validate_vocab ----------------------------------------------------------
    "static_vocab_gated_lint": CONTENT,
    "vocab_audit_pass_rate": CONTENT,
    # -- §1*/§4 validate_matrix: DISCOVERED check families ---------------------------
    "NODE_TO_DNA_presence": CONTENT,
    "answer_key_integrity": CONTENT,
    "answer_key_recomputation": CONTENT,
    "answer_leak_in_stem": CONTENT,
    "concept_gating": CONTENT,
    "correct_answer_presence": CONTENT,
    "degenerate_answer_key": CONTENT,
    "discrete_gen": CONTENT,
    "discrete_integrity": CONTENT,
    "empty_execution_matrix": CONTENT,
    "formatter_match": CONTENT,
    "generate_scalar": CONTENT,
    "import_dna": CONTENT,
    "interest_invariance_formatted": CONTENT,
    "interest_theme_generation": CONTENT,
    "mcq_correct_presence": CONTENT,
    "mcq_correct_value_mismatch": CONTENT,
    "mcq_option_count": CONTENT,
    "mcq_option_uniqueness": CONTENT,
    "mcq_option_validity": CONTENT,
    "monotonicity": CONTENT,
    "pipeline_run": CONTENT,
    "question_text_presence": CONTENT,
    "reach_generation": CONTENT,
    "reverse_compatibility_check": CONTENT,
    "reverse_compatibility_check_crash": CONTENT,
    "reverse_curriculum_gate_check": CONTENT,
    "reverse_curriculum_gate_check_crash": CONTENT,
    "scalar_exactness_0.0": CONTENT,
    "scalar_exactness_1.0": CONTENT,
    "scalar_exactness_1.0_exceed": CONTENT,
    "value_containment": CONTENT,
    "value_reaches_max": CONTENT,
    "visual_payload": CONTENT,
    "visual_schema_integrity": CONTENT,
    "vocabulary_gating": CONTENT,
    "window_containment": CONTENT,
    "worker_crash": INTEGRITY,                   # the matrix pool lost a node: harness crash
}


def finding_key(label: str, family: bool = False):
    """
    The FINDING_CLASS row an emitted label resolves to, or None when no row names it.

    Exact match, except a key ending in `_` (`stage_crashed_`), which names a family by
    its literal prefix. `family=True` additionally matches `<key>_<anything>`, which is
    how a matrix check (`window_containment_0.5_range`) reaches the family §8 inventories
    (`window_containment`); the LONGEST such key wins, so `scalar_exactness_1.0_exceed_x`
    is not read as `scalar_exactness_1.0`. Printed labels never use `family=True`: a
    misspelt `count_noun_agreement_1J_x` must be unclassified, not quietly content.
    """
    if label in FINDING_CLASS:
        return label
    best = None
    for key in FINDING_CLASS:
        hit = (key.endswith("_") and label.startswith(key)) or (
            family and label.startswith(key + "_"))
        if hit and (best is None or len(key) > len(best)):
            best = key
    return best


def finding_class(label: str, family: bool = False):
    """The class of one emitted label (see `finding_key`), or None when unclassified."""
    key = finding_key(label, family=family)
    return FINDING_CLASS[key] if key is not None else None


# ─── Canonical DNA module registry ───────────────────────────────────────────
DNA_MODULE_MAP: Dict[str, str] = {
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
    "compose_decompose_to_10":   "backend.app.practice_gen.dna.na.compose_decompose_to_10",
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
    "probability_experiment": "backend.app.practice_gen.dna.dp.probability_experiment",
}

# ─── Programmatically derived known formatters ─────────────────────────────────
KNOWN_FORMATTERS: Set[str] = set(FORMATTER_ROUTES.keys())


def load_dna(concept: str) -> DNA:
    """
    Import the DNA module and return its DNA instance.
    Raises ImportError if loading fails or if no DNA instance is found.
    """
    module_path = DNA_MODULE_MAP.get(concept)
    if module_path is None:
        raise ImportError(f"No DNA module mapped for concept '{concept}'")

    try:
        mod = importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Failed to import DNA module '{module_path}': {e}") from e

    # Convention: scan module for DNA instances matching the concept name.
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if isinstance(obj, DNA) and obj.concept == concept:
            return obj

    raise ImportError(f"No DNA instance found in module '{module_path}' for concept '{concept}'")


# ─── Import-time validation ───────────────────────────────────────────────────
# Assert that the DNA module registry is in 1:1 correspondence with the COMPATIBILITY table keys.
dna_keys = set(DNA_MODULE_MAP.keys())
compat_keys = set(COMPATIBILITY.keys())
if dna_keys != compat_keys:
    diff_dna = dna_keys - compat_keys
    diff_compat = compat_keys - dna_keys
    error_msg = "Registry drift detected between DNA_MODULE_MAP and COMPATIBILITY table.\n"
    if diff_dna:
        error_msg += f"  - In DNA_MODULE_MAP but missing in COMPATIBILITY: {diff_dna}\n"
    if diff_compat:
        error_msg += f"  - In COMPATIBILITY but missing in DNA_MODULE_MAP: {diff_compat}\n"
    raise ImportError(error_msg)
