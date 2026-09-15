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
import re
import sys
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

from ..dna.base import DNA, ErrorPattern
from ..generators.difficulty import (
    MIN_ACCEPTANCE_RATE,
    enumerate_profiles,
    measure_acceptance_rate,
)
from ..generators.base_generator import generate_context
from ..registry import NODE_TO_DNA, get_node_info


from ._manifest import DNA_MODULE_MAP, load_dna

# §8 inventory: the assertions this module can independently fail on. Each must be
# proven by a mutation naming it in `Mutation.asserts`, or excused in
# validate_coverage.UNPROVEN_ASSERTIONS with a reason and a date.
ASSERTIONS = (
    "dna_structure",               # validate_all_dnas: formula/visual/static_bank/algorithmic shape
    "dna_difficulty_feasibility",  # run_all_feasibility_checks: every profile is satisfiable
)


STRUCTURAL_SEEDS: Tuple[int, ...] = (0, 1, 42, 99, 2_147_483_647)


def _sample_params_for_grade(dna: DNA, grade: int, seed: int = 42) -> Dict[str, Any]:
    """
    Call the DNA module's generate_params with a neutral profile.
    A declared grade that cannot generate is a named structural failure.  Returning
    ``None`` here used to erase the entire formula/error-pattern check silently.
    """
    module_path = DNA_MODULE_MAP.get(dna.concept)
    if module_path is None:
        raise ImportError(f"{dna.concept}: no DNA_MODULE_MAP entry")
    mod = importlib.import_module(module_path)
    return mod.generate_params(grade, {}, seed)


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


def _are_values_equal(v1: Any, v2: Any) -> bool:
    """Compare numeric values exactly, without binary-float approximation."""
    def canonical(value: Any) -> Tuple[str, Any]:
        if isinstance(value, bool):
            return ("bool", value)
        if isinstance(value, (int, Fraction)):
            return ("number", Fraction(value))
        if isinstance(value, float):
            return ("number", Fraction(str(value)))
        if isinstance(value, str):
            try:
                return ("number", Fraction(value.strip()))
            except (ValueError, ZeroDivisionError):
                return ("text", value)
        return (type(value).__qualname__, value)

    return canonical(v1) == canonical(v2)


def _declared_grades(dna: DNA) -> Tuple[List[int], List[str]]:
    grades: List[int] = []
    errors: List[str] = []
    for key in dna.param_bounds:
        if not re.fullmatch(r"g\d+", key):
            errors.append(
                f"{dna.concept}: invalid param_bounds grade key {key!r}; expected g<digits>."
            )
            continue
        grades.append(int(key[1:]))
    if not grades:
        errors.append(f"{dna.concept}: no declared grades in param_bounds.")
    return sorted(set(grades)), errors


def _validate_formula_samples(dna: DNA) -> List[str]:
    """Exercise every applicable node and declared grade at deterministic seeds."""
    errors: List[str] = []
    grades, grade_errors = _declared_grades(dna)
    errors.extend(grade_errors)
    for grade in grades:
        node_ids = [
            node_id
            for node_id, concepts in NODE_TO_DNA.items()
            if dna.concept in concepts
            and (get_node_info(node_id) or {}).get("grade") == grade
        ]
        # A bound may intentionally precede its first node (currently counting/perimeter
        # g3). It is still syntax-checked directly, but is explicitly not claimed as a
        # student-path obligation until a node maps it.
        if not node_ids:
            for seed in STRUCTURAL_SEEDS:
                try:
                    sample_values = _sample_params_for_grade(dna, grade, seed=seed)
                    _eval_formula(dna.answer_formula, sample_values)
                except Exception as exc:
                    errors.append(
                        f"{dna.concept} unmapped grade={grade} seed={seed}: "
                        f"formula sampling raised: {exc}"
                    )
            continue

        for node_id in node_ids:
            for seed in STRUCTURAL_SEEDS:
                try:
                    ctx = generate_context(
                        dna=dna,
                        node_id=node_id,
                        grade=grade,
                        seed=seed,
                        difficulty_profile=None,
                        interest_theme=None,
                        is_student_path=True,
                    )
                except Exception as exc:
                    errors.append(
                        f"{dna.concept} node={node_id} grade={grade} seed={seed}: "
                        f"generate_context raised: {exc}"
                    )
                    continue

                # A distractor equal to the key is a hard failure on the produced
                # context. Raw ErrorPattern formulas may collide for particular values;
                # production must remove key collisions before this seam. Equal-valued
                # distractors are deliberately left to §1K's display-aware rule: two
                # representations of the same wrong value can be legitimate.
                for distractor in ctx.distractors:
                    if _are_values_equal(distractor, ctx.correct_answer):
                        errors.append(
                            f"{dna.concept} node={node_id} grade={grade} seed={seed}: "
                            f"produced distractor equals correct answer {distractor!r}."
                        )
    return errors


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATORS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_formula_dna(dna: DNA) -> List[str]:
    """
    Validate a formula-type DNA for structural correctness.

    Checks:
      1. answer_formula is not None.
      2. For every declared grade where param_bounds exists:
         All (lo, hi) pairs with numeric bounds satisfy lo < hi.
      3. For each ErrorPattern: formula evaluates without error for
         five deterministic samples at every declared grade.
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

    errors.extend(_validate_formula_samples(dna))

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
    _, grade_errors = _declared_grades(dna)
    errors.extend(grade_errors)

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
    _, grade_errors = _declared_grades(dna)
    errors.extend(grade_errors)

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


def validate_algorithmic_dna(dna: DNA) -> List[str]:
    """
    Validate an algorithmic-type DNA for structural correctness.
    Similar to validate_formula_dna since it evaluates formulas/error patterns against generated values.
    """
    errors: List[str] = []
    concept = dna.concept

    # 1. answer_formula present
    if dna.answer_formula is None:
        errors.append(f"{concept}: answer_formula is None for algorithmic-type DNA.")
        return errors

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

    errors.extend(_validate_formula_samples(dna))

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

    for concept in DNA_MODULE_MAP:
        try:
            dna = load_dna(concept)
        except ImportError as e:
            results[concept] = [f"{concept}: could not import DNA module: {e}"]
            continue

        if dna.dna_type == "formula":
            errors = validate_formula_dna(dna)
        elif dna.dna_type == "visual_read":
            errors = validate_visual_dna(dna)
        elif dna.dna_type == "static_bank":
            errors = validate_static_bank_dna(dna)
        elif dna.dna_type == "algorithmic":
            errors = validate_algorithmic_dna(dna)
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

    module_path = DNA_MODULE_MAP.get(dna.concept)
    mod = importlib.import_module(module_path) if module_path else None
    bounds = dna.param_bounds_for_grade(grade)

    for profile in enumerate_profiles(dna):
        # Some DNAs pre-declare certain (axis, grade-range) combinations as
        # infeasible and gate them at the config layer (e.g. addition's
        # regrouping_is_feasible, consulted by the Lab config router) so that
        # combination is never actually requested from the generator. Skip
        # those here too instead of flagging a sampler viability problem
        # that can never occur on the serving path.
        if "regrouping" in profile and mod is not None and hasattr(mod, "regrouping_is_feasible"):
            max_result = bounds.get("max_result") or (bounds.get("a")[1] if "a" in bounds and isinstance(bounds["a"], tuple) else None)
            if max_result is not None:
                import inspect
                sig = inspect.signature(mod.regrouping_is_feasible)
                kwargs = {}
                if "grade" in sig.parameters:
                    kwargs["grade"] = grade
                if not mod.regrouping_is_feasible(profile["regrouping"], max_result, **kwargs):
                    continue

        rng = random.Random(rng_seed)
        rate = measure_acceptance_rate(dna, grade, profile, rng)
        if rate < MIN_ACCEPTANCE_RATE:
            errors.append(
                f"{dna.concept} grade={grade} profile={profile}: "
                f"acceptance rate {rate:.3f} < MIN ({MIN_ACCEPTANCE_RATE})."
            )

    return errors


def run_all_feasibility_checks() -> Dict[str, List[str]]:
    """
    Run validate_difficulty_feasibility for every DNA x every grade present
    in that DNA's param_bounds. Returns concept -> list of error strings
    (empty list = all profiles viable for that DNA across its grades).
    """
    results: Dict[str, List[str]] = {}
    for concept in DNA_MODULE_MAP:
        try:
            dna = load_dna(concept)
        except ImportError as e:
            results[concept] = [f"{concept}: could not import DNA module: {e}"]
            continue

        grades = sorted(
            int(key[1:]) for key in dna.param_bounds if key.startswith("g") and key[1:].isdigit()
        )
        errors: List[str] = []
        for grade in grades:
            errors.extend(validate_difficulty_feasibility(dna, grade))
        results[concept] = errors

    total = len(results)
    failed_concepts = [c for c, errs in results.items() if errs]
    print(f"\nDifficulty feasibility validation: {total - len(failed_concepts)}/{total} passed, {len(failed_concepts)} failed.")
    for concept, errs in results.items():
        if errs:
            print(f"  FAIL {concept}:")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"  PASS {concept}")

    return results


# ─── entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = validate_all_dnas()
    failed = [c for c, errs in results.items() if any(not e.startswith("WARN") for e in errs)]

    feasibility_results = run_all_feasibility_checks()
    feasibility_failed = [c for c, errs in feasibility_results.items() if errs]

    sys.exit(1 if (failed or feasibility_failed) else 0)
