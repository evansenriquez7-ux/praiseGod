"""
Practice Generation — Validation Manifest

Central source of truth for the validation suite. Exposes the canonical
DNA module registry, known formatters, and helper to load DNA instances.
"""

from __future__ import annotations

import importlib
from typing import Dict, Set

from backend.app.practice_gen.compatibility import COMPATIBILITY
from backend.app.practice_gen.adapter import FORMATTER_ROUTES
from backend.app.practice_gen.dna.base import DNA

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
