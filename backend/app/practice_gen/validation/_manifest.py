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
    "§1J": 1, "§1K": 1,
    "§2": 1, "§2B": 1, "§2C": 1, "§2D": 1, "§2E": 1, "§2F": 1, "§2G": 1, "§2H": 1, "§2I": 1,
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
