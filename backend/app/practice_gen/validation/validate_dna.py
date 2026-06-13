"""
Practice Generation — DNA Validation Suite

Validates structural correctness and difficulty feasibility of all DNA instances.

Run as a module:
    python -m backend.app.practice_gen.validation.validate_dna
"""

from __future__ import annotations

import importlib
import math
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

from ..dna.base import DNA, ErrorPattern
from ..generators.difficulty import (
    MIN_ACCEPTANCE_RATE,
    enumerate_profiles,
    measure_acceptance_rate,
)


# ─── DNA module registry (mirrors base_generator._DNA_MODULE_MAP) ─────────────

_DNA_MODULE_MAP: Dict[str, str] = {
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


def _load_dna(concept: str) -> Optional[DNA]:
    """Import the DNA module and return its DNA instance, or None on failure."""
    module_path = _DNA_MODULE_MAP.get(concept)
    if module_path is None:
        return None
    try:
        mod = importlib.import_module(module_path)
    except ImportError:
        return None
    # Convention: the DNA instance is the only DNA object at module level.
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if isinstance(obj, DNA) and obj.concept == concept:
            return obj
    return None


def _sample_params_for_grade(dna: DNA, grade: int, seed: int = 42) -> Optional[Dict[str, Any]]:
    """
    Call the DNA module's generate_params with a neutral profile.
    Returns the params dict, or None if generation fails.
    """
    module_path = _DNA_MODULE_MAP.get(dna.concept)
    if module_path is None:
        return None
    try:
        mod = importlib.import_module(module_path)
        return mod.generate_params(grade, {}, seed)
    except Exception:
        return None


def _eval_formula(formula: str, values: Dict[str, Any]) -> Any:
    """Evaluate a formula string with values as variable bindings."""
    _safe_ns: Dict[str, Any] = {
        "__builtins__": {},
        "sum": sum,
        "round": round,
        "int": int,
        "float": float,
        "abs": abs,
        "max": max,
        "min": min,
        "log10": math.log10,
        "str": str,
        "len": len,
        "sorted": sorted,
    }
    ns = {**_safe_ns, **values}
    return eval(formula, {"__builtins__": {}}, ns)  # noqa: S307


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATORS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_formula_dna(dna: DNA) -> List[str]:
    """
    Validate a formula-type DNA for structural correctness.

    Checks:
      1. answer_formula is not None.
      2. For each grade (g1, g2, g3) where param_bounds exists:
         All (lo, hi) pairs with numeric bounds satisfy lo < hi.
      3. For each ErrorPattern: formula evaluates without error for
         sample param values at grade 1.
      4. Distractors != correct answer for sample param values.
      5. Distractors are mutually distinct.

    Args:
        dna: A DNA instance with dna_type == "formula".

    Returns:
        List of error strings. Empty list = valid.
    """
    errors: List[str] = []
    concept = dna.concept

    # 1. answer_formula present
    if dna.answer_formula is None:
        errors.append(f"{concept}: answer_formula is None for formula-type DNA.")
        return errors  # further checks require answer_formula

    # 2. param_bounds lo < hi
    for grade_key, bounds in dna.param_bounds.items():
        for param_name, bound in bounds.items():
            if not isinstance(bound, (list, tuple)) or len(bound) < 2:
                continue
            lo, hi = bound[0], bound[1]
            if not (isinstance(lo, (int, float)) and isinstance(hi, (int, float))):
                continue
            if lo >= hi:
                errors.append(
                    f"{concept} [{grade_key}]: param '{param_name}' has "
                    f"lo={lo} >= hi={hi} — randint would crash."
                )

    # 3–5. Evaluate error patterns against sample params
    grade_keys = list(dna.param_bounds.keys())
    sample_grade_key = grade_keys[0] if grade_keys else None
    sample_grade = int(sample_grade_key[1]) if sample_grade_key else 1
    sample_values = _sample_params_for_grade(dna, sample_grade, seed=42)

    if sample_values is not None:
        # Compute correct answer
        try:
            correct = _eval_formula(dna.answer_formula, sample_values)
        except Exception as exc:
            errors.append(
                f"{concept}: answer_formula '{dna.answer_formula}' failed to "
                f"evaluate for sample values {sample_values}: {exc}"
            )
            correct = None

        distractor_values: List[Any] = []
        for ep in dna.error_patterns:
            # 3. Formula evaluates without error
            if ep.formula in ("None", None):
                continue
            try:
                d_val = _eval_formula(ep.formula, sample_values)
            except Exception as exc:
                errors.append(
                    f"{concept}: ErrorPattern '{ep.label}' formula "
                    f"'{ep.formula}' raised: {exc}"
                )
                continue

            if correct is not None:
                # 4. Distractor != correct (runtime filter handles edge cases — WARN only)
                if d_val == correct:
                    errors.append(
                        f"WARN {concept}: ErrorPattern '{ep.label}' produces "
                        f"distractor == correct answer ({d_val}) for sample seed. "
                        f"Runtime distractor filter handles this."
                    )
                    # Don't track collisions-with-correct as duplicate distractors;
                    # runtime already skips them.
                    continue

            # 5. Distractors mutually distinct
            if d_val in distractor_values:
                errors.append(
                    f"{concept}: ErrorPattern '{ep.label}' produces a duplicate "
                    f"distractor value ({d_val})."
                )
            else:
                distractor_values.append(d_val)

    return errors


def validate_visual_dna(dna: DNA) -> List[str]:
    """
    Validate a visual_read-type DNA.

    Checks:
      1. answer_formula is None.
      2. visual_home is set (non-empty string).
      3. compatible_formatters contains at least one visual formatter
         (any formatter not in the pure-textual set).

    Args:
        dna: A DNA instance with dna_type == "visual_read".

    Returns:
        List of error strings. Empty list = valid.
    """
    _TEXTUAL_FORMATTERS = {
        "mcq", "cloze", "numeric_input", "ordering",
        "true_false", "error_detect", "fill_in_blank",
    }
    errors: List[str] = []
    concept = dna.concept

    if dna.answer_formula is not None:
        errors.append(
            f"{concept}: visual_read DNA should have answer_formula=None, "
            f"got '{dna.answer_formula}'."
        )

    if not dna.visual_home:
        errors.append(f"{concept}: visual_read DNA must have visual_home set.")

    visual_formatters = [
        f for f in dna.compatible_formatters if f not in _TEXTUAL_FORMATTERS
    ]
    if not visual_formatters:
        errors.append(
            f"{concept}: visual_read DNA has no visual formatters in "
            f"compatible_formatters: {dna.compatible_formatters}"
        )

    return errors


def validate_static_bank_dna(dna: DNA) -> List[str]:
    """
    Validate a static_bank-type DNA.

    Checks:
      1. answer_formula is None.
      2. At least one compatible formatter is declared.

    Args:
        dna: A DNA instance with dna_type == "static_bank".

    Returns:
        List of error strings. Empty list = valid.
    """
    errors: List[str] = []
    concept = dna.concept

    if dna.answer_formula is not None:
        errors.append(
            f"{concept}: static_bank DNA should have answer_formula=None, "
            f"got '{dna.answer_formula}'."
        )

    if not dna.compatible_formatters:
        errors.append(
            f"{concept}: static_bank DNA must have at least one "
            f"compatible_formatters entry."
        )

    return errors


def validate_all_dnas() -> Dict[str, List[str]]:
    """
    Import and validate all 27 DNA instances.

    Dispatches each DNA to the appropriate type-specific validator.

    Returns:
        Dict mapping concept name → list of error strings.
        An empty list means that DNA passed all checks.
    """
    results: Dict[str, List[str]] = {}

    for concept in _DNA_MODULE_MAP:
        dna = _load_dna(concept)
        if dna is None:
            results[concept] = [f"{concept}: could not import DNA module."]
            continue

        if dna.dna_type == "formula":
            errors = validate_formula_dna(dna)
        elif dna.dna_type == "visual_read":
            errors = validate_visual_dna(dna)
        elif dna.dna_type == "static_bank":
            errors = validate_static_bank_dna(dna)
        else:
            errors = [f"{concept}: unknown dna_type '{dna.dna_type}'."]

        results[concept] = errors

    # Print summary
    total = len(results)
    passed = sum(1 for errs in results.values() if not [e for e in errs if not e.startswith("WARN")])
    failed = total - passed
    print(f"\nDNA validation: {passed}/{total} passed, {failed} failed.")
    for concept, errs in results.items():
        hard_errs = [e for e in errs if not e.startswith("WARN")]
        if hard_errs:
            print(f"  FAIL {concept}:")
            for e in errs:
                print(f"    - {e}")
        elif errs:
            print(f"  WARN {concept}:")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"  PASS {concept}")

    return results


def validate_difficulty_feasibility(
    dna: DNA,
    grade: int,
    rng_seed: int = 42,
) -> List[str]:
    """
    Verify that every difficulty profile for a DNA meets MIN_ACCEPTANCE_RATE.

    For each profile from enumerate_profiles(dna), measures the fraction of
    uniform samples from dna.param_bounds that satisfy that profile's
    constraints.  Profiles below MIN_ACCEPTANCE_RATE are reported as errors.

    Args:
        dna: DNA specification.
        grade: Student grade level (1–3).
        rng_seed: Seed for the acceptance-rate sampler.

    Returns:
        List of error strings. Empty list = all profiles are viable.
    """
    errors: List[str] = []

    for profile in enumerate_profiles(dna):
        rng = random.Random(rng_seed)
        rate = measure_acceptance_rate(dna, grade, profile, rng)
        if rate < MIN_ACCEPTANCE_RATE:
            errors.append(
                f"{dna.concept} grade={grade} profile={profile}: "
                f"acceptance rate {rate:.3f} < MIN ({MIN_ACCEPTANCE_RATE})."
            )

    return errors


# ─── entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = validate_all_dnas()
    failed = [c for c, errs in results.items() if errs]
    sys.exit(1 if failed else 0)
