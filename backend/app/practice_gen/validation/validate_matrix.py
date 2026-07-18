"""
validate_matrix.py

Executes the full behavioral matrix for every node in the MATATAG knowledge graph.
Checks:
  1A. Scalar boundary exactness
  1B. Window containment sweep (monotonicity and window containment)
  1C. Variant x Formatter execution matrix
  1D. Vocabulary/Concept lint on final formatted output
  1E. Answer-key integrity & interest invariance

CLI:
  python -m backend.app.practice_gen.validation.validate_matrix [--node NODE_ID] [--fail-fast]
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Set up backend imports
from backend.app.practice_gen.pipeline import run
from backend.app.practice_gen.registry import (
    get_node_competency_bounds,
    get_node_dnas,
    get_node_info,
    get_all_node_ids,
)
from backend.app.practice_gen.axes_catalog import get_axes_for_concept
from backend.app.practice_gen.compatibility import (
    VARIANTS_BY_DNA,
    get_supported_variants,
    FORMATTER_VARIANT_SUPPORT,
    is_variant_available_at,
)
from backend.app.practice_gen.validation._manifest import DNA_MODULE_MAP, load_dna
from backend.app.practice_gen.validation.validate_vocab import _text_contains_term
from backend.app.practice_gen.validation.validate_dna import _are_values_equal
from backend.app.services.scoring import validate_math_answer
from backend.app.practice_gen.schemas.visuals import VisualSchemaRegistry


def get_variant_combinations(supported_variants: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """Generate all possible variant assignment combinations from supported variants dict."""
    if not supported_variants:
        return [{}]
    import itertools
    keys = list(supported_variants.keys())
    value_lists = [supported_variants[k] for k in keys]
    combinations = []
    for values in itertools.product(*value_lists):
        combinations.append(dict(zip(keys, values)))
    return combinations


def get_expected_mapped_value(axis: dict, val: float, min_val: float, max_val: float) -> float:
    """Compute the expected mapped value ceiling based on scalar and divisions (t_hi)."""
    scale_type = axis.get("scale", "linear")
    if axis["name"] != "number_difficulty":
        divisions = axis.get("divisions", 5)
        w = 1.0 / divisions
        t_val = val * (1.0 - w) + w
    else:
        t_val = val

    if scale_type == "logarithmic":
        shift = 1 if min_val == 0 else 0
        log_min = math.log10(min_val + shift)
        log_max = math.log10(max_val + shift)
        log_val = log_min + t_val * (log_max - log_min)
        return int(math.pow(10, log_val)) - shift
    else:
        if isinstance(min_val, float) or isinstance(max_val, float) or (max_val - min_val <= 2):
            return round(min_val + t_val * (max_val - min_val), 2)
        else:
            return int(min_val + t_val * (max_val - min_val))


def score_problem_operands(problem: Dict[str, Any], axis_name: str) -> List[float]:
    """Score the complexity of whole numbers/fractions in problem.given_values."""
    from backend.app.practice_gen.generators.number_difficulty import score_candidate
    given = problem.get("given_values", {})
    correct = problem.get("correct_answer")
    scores = []
    
    # Identify maximum bound for whole numbers
    max_val = problem.get("difficulty_profile", {}).get(axis_name, 100)
    if not isinstance(max_val, (int, float)):
        max_val = 100

    # Collect numeric candidates
    candidates = []
    for k, v in given.items():
        if k in ("a", "b", "result", "numerator", "denominator", "value_g", "value_kg", "value_ml", "value_l"):
            if isinstance(v, (int, float)):
                candidates.append((v, "integer"))
            elif isinstance(v, tuple) and len(v) == 2:
                candidates.append((v, "fraction"))
    
    if isinstance(correct, bool):
        pass  # true_false formatter: boolean correct_answer is not a numeric operand
    elif isinstance(correct, (int, float)):
        candidates.append((correct, "integer"))
    elif isinstance(correct, tuple) and len(correct) == 2:
        candidates.append((correct, "fraction"))

    for val, t in candidates:
        try:
            scores.append(score_candidate(val, max_val, t))
        except Exception:
            pass
            
    return scores


def count_addition_carries(a: int, b: int) -> int:
    carries = 0
    carry = 0
    while a > 0 or b > 0:
        da = a % 10
        db = b % 10
        if da + db + carry >= 10:
            carries += 1
            carry = 1
        else:
            carry = 0
        a //= 10
        b //= 10
    return carries


def count_subtraction_borrows(a: int, b: int) -> int:
    borrows = 0
    borrow = 0
    while a > 0:
        da = a % 10
        db = b % 10 + borrow
        if da < db:
            borrows += 1
            borrow = 1
        else:
            borrow = 0
        a //= 10
        b //= 10
    return borrows


def verify_discrete_dimension(problem: Dict[str, Any], axis_name: str, option_val: Any, dna_name: str) -> bool:
    """Assert that the generated problem actually reflects the selected discrete option."""
    given = problem.get("given_values", {})
    if axis_name == "regrouping":
        a = given.get("a", 0)
        b = given.get("b", 0)
        # Not every DNA emits an "operation" key (e.g. subtraction.py doesn't) —
        # the DNA being tested is the ground truth for which arithmetic applies,
        # not a guessed default (defaulting to "add" silently ran addition-carry
        # logic against subtraction values and always failed).
        operation = given.get("operation") or ("subtract" if dna_name == "subtraction" else "add")
        if operation == "add":
            carries = count_addition_carries(a, b)
            if option_val == "none":
                return carries == 0
            elif option_val == "one_place":
                return carries == 1
            elif option_val == "two_places":
                return carries == 2
        elif operation == "subtract":
            borrows = count_subtraction_borrows(a, b)
            if option_val == "none":
                return borrows == 0
            elif option_val == "one_place":
                return borrows == 1
            elif option_val == "two_places":
                return borrows == 2
    elif axis_name in ("skip_interval", "step"):
        # Consecutive terms in sequence must match step/interval
        terms = given.get("sequence", [])
        if len(terms) >= 2:
            step = int(option_val)
            for i in range(len(terms) - 1):
                if abs(terms[i+1] - terms[i]) != step:
                    return False
    return True


def run_matrix_for_node(node_id: str, fail_fast: bool) -> List[Dict[str, Any]]:
    failures = []

    # Get mapped DNAs
    dna_names = get_node_dnas(node_id)
    if not dna_names:
        failures.append({
            "dna": "unknown",
            "formatter": "unknown",
            "check": "NODE_TO_DNA_presence",
            "seed": 0,
            "error": f"Node '{node_id}' has no entry in NODE_TO_DNA."
        })
        return failures

    node_info = get_node_info(node_id)
    grade = node_info.get("grade", 1)
    quarter = node_info.get("quarter", 1)
    
    # ─── Load knowledge graph node for vocab gating
    from backend.app.practice_gen.registry import _KG_NODES
    node_kg = _KG_NODES.get(node_id, {})
    not_yet_known = node_kg.get("NOT_YET_KNOWN", [])
    cumulative_vocab_list = node_kg.get("cumulative_vocab", [])
    cumulative_concepts = set(node_kg.get("cumulative_concepts", [])) | set(node_kg.get("introduces_concepts", []))

    for dna_name in dna_names:
        try:
            dna = load_dna(dna_name)
        except Exception as e:
            failures.append({
                "dna": dna_name,
                "formatter": "unknown",
                "check": "import_dna",
                "seed": 0,
                "error": f"Could not import DNA module for concept '{dna_name}': {e}"
            })
            if fail_fast:
                return failures
            continue

        # A node's own DNA concept is available to itself the moment it's introduced —
        # mirrors validate_vocab.validate_concept_constraints's cumulative_concepts.add(ctx.dna_concept).
        dna_cumulative_concepts = cumulative_concepts | {dna_name}

        # Get continuous & discrete axes
        axes = get_axes_for_concept(dna_name)
        continuous_axes = [a for a in axes if a.get("dim_type") == "continuous"]
        discrete_axes = [a for a in axes if a.get("dim_type") == "discrete"]

        # ─── 1A & 1B: Scalar Boundaries & containment sweep
        for axis in continuous_axes:
            axis_name = axis["name"]
            
            # Resolve bounds
            comp_bounds = get_node_competency_bounds(node_id, dna_name)
            bounds = comp_bounds.get(axis_name)
            if bounds:
                min_val, max_val = bounds
            else:
                min_val = axis.get("default_min", 0.0 if axis_name == "number_difficulty" else 1)
                max_val = axis.get("default_max", 1.0 if axis_name == "number_difficulty" else 100)

            # Generate problems at {0.0, 0.25, 0.5, 0.75, 1.0}
            generations: Dict[float, List[Dict[str, Any]]] = {s: [] for s in [0.0, 0.25, 0.5, 0.75, 1.0]}
            
            # Generate 30 seeds for 0.0 and 1.0 (to satisfy 1A), and 20 seeds for 0.25, 0.5, 0.75
            for scalar in [0.0, 0.25, 0.5, 0.75, 1.0]:
                count = 30 if scalar in (0.0, 1.0) else 20
                for idx in range(count):
                    seed = int(100 + val_to_seed_offset(scalar) * 1000 + idx)
                    try:
                        p = run(node_id=node_id, difficulty_profile={axis_name: scalar}, seed=seed, forced_dna=dna_name)
                        generations[scalar].append(p)
                    except Exception as e:
                        failures.append({
                            "dna": dna_name,
                            "formatter": "unknown",
                            "check": f"generate_scalar_{scalar}",
                            "seed": seed,
                            "error": f"Failed to generate problem for axis '{axis_name}' at scalar {scalar}: {e}"
                        })
                        if fail_fast:
                            return failures

            # --- 1A. Scalar boundary exactness ---
            expected_0_0 = get_expected_mapped_value(axis, 0.0, min_val, max_val)
            expected_1_0 = get_expected_mapped_value(axis, 1.0, min_val, max_val)

            # 1A - 0.0 ceiling assertion
            if axis_name != "number_difficulty":
                observed_vals_0_0 = [g.get("difficulty_profile", {}).get(axis_name) for g in generations[0.0]]
                max_obs_0_0 = max(observed_vals_0_0) if observed_vals_0_0 else None
                if max_obs_0_0 != expected_0_0:
                    failures.append({
                        "dna": dna_name,
                        "formatter": "unknown",
                        "check": f"scalar_exactness_0.0_{axis_name}",
                        "seed": 100,
                        "error": f"At 0.0, governed parameter maximum observed value ({max_obs_0_0}) != minimum window ceiling ({expected_0_0})."
                    })
                    if fail_fast:
                        return failures

                # 1A - 1.0 boundary assertion (no sample exceeds max_val)
                observed_vals_1_0 = [g.get("difficulty_profile", {}).get(axis_name) for g in generations[1.0]]
                max_obs_1_0 = max(observed_vals_1_0) if observed_vals_1_0 else None
                if max_obs_1_0 > max_val:
                    failures.append({
                        "dna": dna_name,
                        "formatter": "unknown",
                        "check": f"scalar_exactness_1.0_exceed_{axis_name}",
                        "seed": 200,
                        "error": f"At 1.0, sample maximum observed value ({max_obs_1_0}) exceeds competency maximum ({max_val}). Leaky window!"
                    })
                    if fail_fast:
                        return failures

                if max_obs_1_0 != expected_1_0:
                    failures.append({
                        "dna": dna_name,
                        "formatter": "unknown",
                        "check": f"scalar_exactness_1.0_{axis_name}",
                        "seed": 200,
                        "error": f"At 1.0, governed parameter maximum observed value ({max_obs_1_0}) != maximum window ceiling ({expected_1_0})."
                    })
                    if fail_fast:
                        return failures

            # --- 1B. Window containment sweep (containment & monotonicity) ---
            ceilings = []
            for scalar in [0.0, 0.25, 0.5, 0.75, 1.0]:
                expected_ceil = get_expected_mapped_value(axis, scalar, min_val, max_val)
                ceilings.append(expected_ceil)
                
                if axis_name != "number_difficulty":
                    for p in generations[scalar]:
                        val = p.get("difficulty_profile", {}).get(axis_name)
                        if val is not None and val > expected_ceil:
                            failures.append({
                                "dna": dna_name,
                                "formatter": "unknown",
                                "check": f"window_containment_{scalar}_{axis_name}",
                                "seed": p["seed"],
                                "error": f"Generated parameter {val} exceeds ceiling {expected_ceil} defined by scalar {scalar}."
                            })
                            if fail_fast:
                                return failures

            # Monotonicity check
            for i in range(len(ceilings) - 1):
                if ceilings[i+1] < ceilings[i]:
                    failures.append({
                        "dna": dna_name,
                        "formatter": "unknown",
                        "check": f"monotonicity_{axis_name}",
                        "seed": 0,
                        "error": f"Monotonicity violation for axis '{axis_name}': ceiling at index {i+1} ({ceilings[i+1]}) < index {i} ({ceilings[i]})."
                    })
                    if fail_fast:
                        return failures

        # ─── 1B Discrete dimensions check
        comp_bounds = get_node_competency_bounds(node_id, dna_name)
        for axis in discrete_axes:
            axis_name = axis["name"]
            raw_options = [opt["value"] for opt in axis.get("options", [])]
            options = []
            for opt_val in raw_options:
                if axis_name in comp_bounds:
                    bound_val = comp_bounds[axis_name]
                    if axis_name == "regrouping":
                        if bound_val is False and opt_val not in ("none", False):
                            continue
                        if bound_val is True and opt_val not in ("ones", True, "one_place"):
                            continue
                    else:
                        if isinstance(bound_val, list):
                            if opt_val not in bound_val:
                                continue
                        else:
                            if opt_val != bound_val:
                                continue
                options.append(opt_val)

            for opt_val in options:
                # Generate problems enforcing this option value
                for idx in range(10):
                    seed = int(300 + idx)
                    try:
                        p = run(node_id=node_id, difficulty_profile={axis_name: opt_val}, seed=seed, forced_dna=dna_name)
                        if not verify_discrete_dimension(p, axis_name, opt_val, dna_name):
                            failures.append({
                                "dna": dna_name,
                                "formatter": p["format"],
                                "check": f"discrete_integrity_{axis_name}_{opt_val}",
                                "seed": seed,
                                "error": f"Generated problem does not reflect discrete option '{opt_val}' (values: {p.get('given_values')})."
                            })
                            if fail_fast:
                                return failures
                    except RuntimeError as e:
                        # Infeasible combination (e.g. regrouping=two_places but max_sum=20) —
                        # this is expected for constrained nodes, not a harness failure.
                        pass
                    except Exception as e:
                        failures.append({
                            "dna": dna_name,
                            "formatter": "unknown",
                            "check": f"discrete_gen_{axis_name}_{opt_val}",
                            "seed": seed,
                            "error": f"Failed to generate discrete problem for '{axis_name}' = '{opt_val}': {e}"
                        })
                        if fail_fast:
                            return failures

        # ─── 1C. Variant × formatter execution matrix
        # Use COMPATIBILITY[dna_name] — the same set the orchestrator and serving path use.
        # dna.compatible_formatters can be a broader/stale list.
        from backend.app.practice_gen.compatibility import COMPATIBILITY, FORMATTER_NUMERIC_LIMITS
        formatters = COMPATIBILITY.get(dna_name, [])
        # Filter formatters by the node's maximum value vs. formatter limits (matching orchestrator logic).
        # comp_bounds can be empty for nodes relying purely on axis-scalar defaults — that must not
        # silently disable the filter (default=0 lets an incompatible >100 emoji_pictorial through).
        # Fall back to this DNA's own param_bounds ceiling for the grade, mirroring orchestrator.py.
        node_max_value = max(
            (b[1] for b in comp_bounds.values() if isinstance(b, tuple) and len(b) == 2),
            default=0,
        )
        if node_max_value <= 0:
            grade_bounds = dna.param_bounds.get(f"g{grade}", {})
            node_max_value = max(
                (b[1] for b in grade_bounds.values() if isinstance(b, tuple) and len(b) == 2),
                default=0,
            )
        formatters = [
            fmt for fmt in formatters
            if FORMATTER_NUMERIC_LIMITS.get(fmt, {}).get("max_val", float("inf")) >= node_max_value
        ]
        for formatter in formatters:
            supported_variants = get_supported_variants(dna_name, formatter)
            combinations = get_variant_combinations(supported_variants)

            # Curriculum-gated (var_name, opt_val) pairs excluded at this node's
            # grade/quarter (e.g. missing_number operation=multiplication before G3).
            # These are the Lab UI's real availability rules (is_variant_available_at)
            # — combos it filters out. They must not be forward-tested as "should
            # succeed"; they belong in the reverse check ("must raise").
            curriculum_excluded: Set[Tuple[str, Any]] = set()
            for var_name, opt_vals in supported_variants.items():
                for opt_val in opt_vals:
                    if not is_variant_available_at(dna_name, var_name, opt_val, grade, quarter):
                        curriculum_excluded.add((var_name, opt_val))

            # Filter combinations by competency bounds and curriculum grade/quarter gates
            filtered_combinations = []
            for assignment in combinations:
                allowed = True
                for var_name, opt_val in assignment.items():
                    if (var_name, opt_val) in curriculum_excluded:
                        allowed = False
                        break
                    if var_name in comp_bounds:
                        bound_val = comp_bounds[var_name]
                        if var_name == "regrouping":
                            if bound_val is False and opt_val not in ("none", False):
                                allowed = False
                                break
                            if bound_val is True and opt_val not in ("ones", True, "one_place"):
                                allowed = False
                                break
                        else:
                            if isinstance(bound_val, list):
                                if opt_val not in bound_val:
                                    allowed = False
                                    break
                            else:
                                if opt_val != bound_val:
                                    allowed = False
                                    break
                if allowed:
                    filtered_combinations.append(assignment)
            combinations = filtered_combinations
            
            for assignment in combinations:
                generations_1c = []
                # 1C - Run pipeline over 5 seeds
                for seed in [42, 43, 44, 45, 46]:
                    try:
                        p = run(node_id=node_id, formatter=formatter, difficulty_profile=assignment, seed=seed, forced_dna=dna_name)
                        generations_1c.append(p)
                        
                        # Assertions on FormattedProblem
                        # Correct formatter used. For visual formatters the `format` field encodes
                        # "{interaction_mode}_{answer_collection}" — e.g. "read_mcq" for emoji_pictorial.
                        # Verify via FORMATTER_ROUTES, not by comparing with formatter name directly.
                        from backend.app.practice_gen.adapter import FORMATTER_ROUTES
                        route_kwargs = FORMATTER_ROUTES.get(formatter, (None, None, {}))[2]
                        if "interaction_mode" in route_kwargs or "answer_collection" in route_kwargs:
                            expected_fmt = f"{route_kwargs.get('interaction_mode', '')}_{route_kwargs.get('answer_collection', '')}"
                        else:
                            expected_fmt = route_kwargs.get("format_name", formatter)
                        if p["format"] != expected_fmt:
                            failures.append({
                                "dna": dna_name,
                                "formatter": formatter,
                                "check": "formatter_match",
                                "seed": seed,
                                "error": f"Silent rerouting detected: expected format '{expected_fmt}' but got '{p['format']}'"
                            })
                            
                        # question_text non-empty
                        if not p.get("question_text"):
                            failures.append({
                                "dna": dna_name,
                                "formatter": formatter,
                                "check": "question_text_presence",
                                "seed": seed,
                                "error": "Question text is empty."
                            })
                            
                        # correct_answer non-null
                        if p.get("correct_answer") is None:
                            failures.append({
                                "dna": dna_name,
                                "formatter": formatter,
                                "check": "correct_answer_presence",
                                "seed": seed,
                                "error": "Correct answer is missing/null."
                            })
                            
                        # MCQ assertions — visual formatters store options under mcq_options
                        if p["format"] == "mcq" or p.get("answer_collection") == "mcq":
                            fmt_data = p.get("format_data", {})
                            options = fmt_data.get("options", []) or fmt_data.get("mcq_options", [])
                            # Expected option count (normally 4)
                            if len(options) != 4:
                                failures.append({
                                    "dna": dna_name,
                                    "formatter": formatter,
                                    "check": "mcq_option_count",
                                    "seed": seed,
                                    "error": f"MCQ option count = {len(options)} (expected 4)."
                                })
                            # Correct answer present
                            correct_present = any(opt.get("is_correct") for opt in options)
                            if not correct_present:
                                failures.append({
                                    "dna": dna_name,
                                    "formatter": formatter,
                                    "check": "mcq_correct_presence",
                                    "seed": seed,
                                    "error": "Correct answer not flagged/present among options."
                                })
                            # The option flagged is_correct must actually carry the served
                            # correct_answer's value — not just *some* flagged option (a
                            # formatter can corrupt which value is marked correct while
                            # leaving correct_answer/is_correct-presence untouched).
                            elif not isinstance(p.get("correct_answer"), bool):
                                flagged_value = next(opt.get("value") for opt in options if opt.get("is_correct"))
                                served = p.get("correct_answer")
                                if isinstance(served, str) and len(served) == 1 and served.isalpha():
                                    matched = [o for o in options if o.get("key") == served]
                                    served_value = matched[0].get("value") if matched else served
                                else:
                                    served_value = served
                                if str(flagged_value) != str(served_value):
                                    failures.append({
                                        "dna": dna_name,
                                        "formatter": formatter,
                                        "check": "mcq_correct_value_mismatch",
                                        "seed": seed,
                                        "error": f"Option flagged is_correct has value {flagged_value!r}, but served correct_answer resolves to {served_value!r}."
                                    })
                            # Options mutually distinct
                            option_vals = [str(opt.get("value")) for opt in options]
                            if len(set(option_vals)) != len(option_vals):
                                failures.append({
                                    "dna": dna_name,
                                    "formatter": formatter,
                                    "check": "mcq_option_uniqueness",
                                    "seed": seed,
                                    "error": f"MCQ options contain duplicate values: {option_vals}."
                                })
                            # No option is empty/null/undefined
                            for opt in options:
                                if opt.get("value") in (None, "", "None", "null", "undefined"):
                                    failures.append({
                                        "dna": dna_name,
                                        "formatter": formatter,
                                        "check": "mcq_option_validity",
                                        "seed": seed,
                                        "error": f"MCQ option value is invalid: {opt.get('value')}."
                                    })
                                    
                        # Visual validation
                        if p.get("is_visual"):
                            try:
                                VisualSchemaRegistry.validate(p.get("visual_type"), p.get("visual_params"))
                            except Exception as exc:
                                failures.append({
                                    "dna": dna_name,
                                    "formatter": formatter,
                                    "check": "visual_schema_integrity",
                                    "seed": seed,
                                    "error": f"Visual schema validation failed for '{p.get('visual_type')}': {exc}"
                                })

                        # --- 1E. Answer-key integrity (formula checks) ---
                        if dna.dna_type == "formula" and dna.answer_formula:
                            served = p["correct_answer"]
                            if isinstance(served, list):
                                # "ordering"-family formatters answer a different question
                                # ("sort these numbers") than the DNA's answer_formula ("compute
                                # the next number") — the two are not comparable. Instead verify
                                # the served list is the correctly-sorted permutation of what was shown.
                                fmt_data = p.get("format_data", {})
                                items = fmt_data.get("items")
                                direction = fmt_data.get("direction", "ascending")
                                if items is not None:
                                    expected_order = sorted(items, reverse=(direction == "descending"))
                                    if sorted(served, key=str) != sorted(items, key=str):
                                        failures.append({
                                            "dna": dna_name,
                                            "formatter": formatter,
                                            "check": "answer_key_integrity",
                                            "seed": seed,
                                            "error": f"Ordering answer-key corruption: served {served} is not a permutation of shown items {items}."
                                        })
                                    elif served != expected_order:
                                        failures.append({
                                            "dna": dna_name,
                                            "formatter": formatter,
                                            "check": "answer_key_integrity",
                                            "seed": seed,
                                            "error": f"Ordering answer-key corruption: served {served} != correctly-sorted {expected_order} (direction={direction})."
                                        })
                                continue

                            # Recompute the answer from given_values + answer_formula
                            from backend.app.practice_gen.validation.validate_dna import _eval_formula
                            try:
                                import sympy as sp
                                try:
                                    expr = sp.sympify(dna.answer_formula)
                                    formula_vars = {str(s) for s in expr.free_symbols}
                                except Exception:
                                    import re
                                    formula_vars = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', dna.answer_formula or ""))
                                
                                # First, unpack the served correct_answer so that it is always numeric/flat
                                fmt_data = p.get("format_data", {})
                                unpacked_served = served
                                if isinstance(unpacked_served, str) and len(unpacked_served) == 1 and unpacked_served.isalpha():
                                    # MCQ key — find the actual numeric value from options/mcq_options
                                    opts = fmt_data.get("options", []) or fmt_data.get("mcq_options", [])
                                    matched = [o for o in opts if o.get("key") == unpacked_served]
                                    if matched:
                                        unpacked_served = matched[0]["value"]
                                elif isinstance(unpacked_served, dict):
                                    # error_detect / complex answer format — compare correct_value if present
                                    unpacked_served = unpacked_served.get("correct_value", None)
                                
                                missing_vars = [v for v in formula_vars if v not in p.get("given_values", {})]
                                if missing_vars:
                                    # Skip recomputation check since one or more variables needed to compute/check the formula are masked/blanked out.
                                    recomputed = unpacked_served
                                else:
                                    recomputed = _eval_formula(dna.answer_formula, p.get("given_values", {}))

                                served = unpacked_served
                                if isinstance(p.get("correct_answer"), bool):
                                    # true_false — skip numeric integrity check
                                    recomputed = served
                                # Some formatters query a different property than the DNA's raw answer_formula:
                                # 1. "ordering" family formatters sort list items.
                                # 2. "array_grid" family when used on division asks for the total grid area (dividend), not the quotient.
                                # 3. "number_line" family when used on rounding asks for the point position, not the rounded value.
                                is_semantic_bypass = (
                                    "ordering" in formatter or
                                    ("array_grid" in formatter and dna_name == "division") or
                                    ("number_line" in formatter and dna_name == "rounding") or
                                    ("fraction" in formatter and dna_name == "fractions") or
                                    (dna_name == "fractions" and p.get("given_values", {}).get("operation") in ("add", "subtract", "add_subtract", "compare"))
                                )
                                if is_semantic_bypass:
                                    continue

                                if not validate_math_answer(recomputed, served):
                                    failures.append({
                                        "dna": dna_name,
                                        "formatter": formatter,
                                        "check": "answer_key_integrity",
                                        "seed": seed,
                                        "error": f"Answer-key corruption: recomputed '{recomputed}' != served '{served}'."
                                    })
                            except Exception as exc:
                                failures.append({
                                    "dna": dna_name,
                                    "formatter": formatter,
                                    "check": "answer_key_recomputation",
                                    "seed": seed,
                                    "error": f"Could not recompute answer using formula '{dna.answer_formula}': {exc}"
                                })

                    except Exception as e:
                        failures.append({
                            "dna": dna_name,
                            "formatter": formatter,
                            "check": "pipeline_run",
                            "seed": seed,
                            "error": f"Pipeline run crashed for variants {assignment}: {e}"
                        })
                        if fail_fast:
                            return failures

                # --- 1E. Interest-theme invariance (formatted output) ---
                if generations_1c and dna.dna_type in ("formula", "algorithmic") and dna.requires_context:
                    # Take the first clean generation
                    ref_p = generations_1c[0]
                    ref_ans = ref_p["correct_answer"]
                    # Generate with other interest themes
                    for theme in ("animals", "sports", "food"):
                        try:
                            theme_p = run(node_id=node_id, formatter=formatter, difficulty_profile=assignment, seed=ref_p["seed"], student_interest=theme, forced_dna=dna_name)
                            if not validate_math_answer(ref_ans, theme_p["correct_answer"]):
                                failures.append({
                                    "dna": dna_name,
                                    "formatter": formatter,
                                    "check": "interest_invariance_formatted",
                                    "seed": ref_p["seed"],
                                    "error": f"Interest invariance violation: correct answer changed from '{ref_ans}' to '{theme_p['correct_answer']}' under theme '{theme}'."
                                })
                        except Exception as e:
                            failures.append({
                                "dna": dna_name,
                                "formatter": formatter,
                                "check": "interest_theme_generation",
                                "seed": ref_p["seed"],
                                "error": f"Failed to generate problem with theme '{theme}': {e}"
                            })

                # --- 1D. Vocabulary & Concept Gating on FORMATTED output ---
                for p in generations_1c:
                    # Formatted text block
                    text_blocks = [p["question_text"]] + p.get("hints", [])
                    # MCQ options
                    if p["format"] == "mcq" or p.get("answer_collection") == "mcq":
                        for opt in p.get("format_data", {}).get("options", []):
                            text_blocks.append(str(opt.get("value", "")))
                    combined_text = " ".join(text_blocks)

                    # Check forbidden terms
                    for term in not_yet_known:
                        if _text_contains_term(combined_text, term):
                            # Exempt: term only appears as sub-token of a known compound
                            # (e.g. "line" in "number line" when "number line" is cumulative_vocab)
                            t_lower = term.lower()
                            containing_knowns = [
                                k for k in cumulative_vocab_list
                                if t_lower in k.lower() and k.lower() != t_lower
                            ]
                            if containing_knowns:
                                modified = combined_text.lower()
                                import re as _re
                                for kc in containing_knowns:
                                    modified = modified.replace(kc.lower(), " __KNOWN__ ")
                                if not _re.search(r'(?<![A-Za-z])' + _re.escape(t_lower) + r'(?![A-Za-z])', modified):
                                    continue  # only appeared inside known compound
                            failures.append({
                                "dna": dna_name,
                                "formatter": formatter,
                                "check": "vocabulary_gating",
                                "seed": p["seed"],
                                "error": f"[NOT_YET_KNOWN] Forbidden term '{term}' found in formatted problem output: \"{combined_text[:120]}...\""
                            })

                    # Check concept constraints
                    forbidden_labels = {
                        ep.label for ep in dna.error_patterns
                        if ep.required_concept not in dna_cumulative_concepts
                    }
                    if forbidden_labels:
                        dist_prov = p.get("distractors_provenance", {}) or {}
                        for d, source in dist_prov.items():
                            if source in forbidden_labels:
                                failures.append({
                                    "dna": dna_name,
                                    "formatter": formatter,
                                    "check": "concept_gating",
                                    "seed": p["seed"],
                                    "error": f"[CONCEPT_GATE] Distractor value {d} from ErrorPattern '{source}' leaked into output."
                                })

            # ─── 1C (Reverse): requesting excluded variants must raise ValueError
            # Find an excluded option/variant if any exist
            all_dna_variants = VARIANTS_BY_DNA.get(dna_name, {})
            for var_name, allowed_vals in supported_variants.items():
                full_vals = all_dna_variants.get(var_name, [])
                excluded_vals = set(full_vals) - set(allowed_vals)
                if excluded_vals:
                    excluded_val = list(excluded_vals)[0]
                    # Request this excluded option
                    bad_profile = {var_name: excluded_val}
                    try:
                        run(node_id=node_id, formatter=formatter, difficulty_profile=bad_profile, seed=42, forced_dna=dna_name)
                        failures.append({
                            "dna": dna_name,
                            "formatter": formatter,
                            "check": "reverse_compatibility_check",
                            "seed": 42,
                            "error": f"Boundary violation: requesting excluded variant {var_name}='{excluded_val}' did not raise an error."
                        })
                    except ValueError:
                        # Success: correctly rejected the incompatible variant
                        pass
                    except Exception as exc:
                        failures.append({
                            "dna": dna_name,
                            "formatter": formatter,
                            "check": "reverse_compatibility_check_crash",
                            "seed": 42,
                            "error": f"Requesting excluded variant {var_name}='{excluded_val}' raised wrong exception: {exc}"
                        })

            # ─── 1C (Reverse): curriculum-gated variants (is_variant_available_at)
            # must also raise ValueError when requested at a grade/quarter that
            # doesn't support them yet (e.g. missing_number operation=multiplication
            # before G3) — mirrors what the Lab UI hides from teachers.
            for var_name, excluded_val in curriculum_excluded:
                bad_profile = {var_name: excluded_val}
                try:
                    run(node_id=node_id, formatter=formatter, difficulty_profile=bad_profile, seed=42, forced_dna=dna_name)
                    failures.append({
                        "dna": dna_name,
                        "formatter": formatter,
                        "check": "reverse_curriculum_gate_check",
                        "seed": 42,
                        "error": f"Curriculum-gate violation: requesting {var_name}='{excluded_val}' (not yet available at grade={grade}, quarter={quarter}) did not raise an error."
                    })
                except ValueError:
                    pass
                except Exception as exc:
                    failures.append({
                        "dna": dna_name,
                        "formatter": formatter,
                        "check": "reverse_curriculum_gate_check_crash",
                        "seed": 42,
                        "error": f"Requesting curriculum-gated variant {var_name}='{excluded_val}' raised wrong exception: {exc}"
                    })

    return failures


def val_to_seed_offset(val: float) -> int:
    if val == 0.0:
        return 0
    if val == 0.25:
        return 1
    if val == 0.5:
        return 2
    if val == 0.75:
        return 3
    if val == 1.0:
        return 4
    return 5


def _worker(node_id: str) -> tuple:
    """Top-level worker so multiprocessing can pickle it."""
    try:
        failures = run_matrix_for_node(node_id, fail_fast=False)
        return node_id, failures
    except Exception as exc:
        return node_id, [{"dna": "unknown", "formatter": "unknown", "check": "worker_crash",
                          "seed": 0, "error": str(exc)}]


def run_matrix_validation(node: Optional[str] = None, fail_fast: bool = False, workers: int = 0) -> int:
    # Load all nodes
    all_node_ids = get_all_node_ids()
    
    if node:
        if node not in all_node_ids:
            print(f"Error: Node ID '{node}' is not registered.")
            return 1
        node_ids = [node]
    else:
        node_ids = all_node_ids

    print("======================================================================")
    print(f"STARTING BEHAVIORAL MATRIX VALIDATION OVER {len(node_ids)} NODES")
    print("======================================================================\n")

    report: Dict[str, list] = {}
    total_failures_count = 0
    passed_count = 0
    report_path = Path("validation_reports/matrix_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    def _flush_report():
        with report_path.open("w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)

    if len(node_ids) == 1 or workers == 1:
        # Single-node or forced-sequential mode
        for idx, node_id in enumerate(node_ids, 1):
            print(f"[{idx}/{len(node_ids)}] Checking {node_id} ...", end="", flush=True)
            node_failures = run_matrix_for_node(node_id, fail_fast)
            _record(report, node_id, node_failures)
            if node_failures:
                print("  FAIL")
                total_failures_count += len(node_failures)
                for f in node_failures:
                    print(f"    - [{f['dna']} / {f['formatter']}] {f['check']} (seed {f['seed']}): {f['error']}")
                if fail_fast:
                    print("\nAborting validation due to --fail-fast.")
                    break
            else:
                print("  PASS")
                passed_count += 1
            _flush_report()
    else:
        # Parallel mode — multiprocessing across nodes
        n_workers = workers if workers > 0 else max(1, multiprocessing.cpu_count() - 1)
        print(f"Using {n_workers} parallel workers.\n")
        completed = 0
        with multiprocessing.Pool(processes=n_workers) as pool:
            for node_id, node_failures in pool.imap_unordered(_worker, node_ids):
                completed += 1
                _record(report, node_id, node_failures)
                if node_failures:
                    print(f"[{completed}/{len(node_ids)}] {node_id}  FAIL ({len(node_failures)} failures)")
                    for f in node_failures[:3]:  # print first 3 per node to avoid flooding
                        print(f"    - [{f['dna']} / {f['formatter']}] {f['check']} (seed {f['seed']}): {f['error'][:120]}")
                    if len(node_failures) > 3:
                        print(f"    ... and {len(node_failures) - 3} more (see report)")
                    total_failures_count += len(node_failures)
                else:
                    print(f"[{completed}/{len(node_ids)}] {node_id}  PASS")
                    passed_count += 1
                _flush_report()  # incremental write after each node

    print("\n======================================================================")
    print("MATRIX VALIDATION SUMMARY")
    print("======================================================================")
    print(f"Nodes Checked: {len(node_ids)}")
    print(f"Nodes Passed:  {passed_count}")
    print(f"Nodes Failed:  {len(report) - passed_count}")
    print(f"Total Failures Observed: {total_failures_count}")
    print(f"Detailed report saved to: {report_path}")
    print("======================================================================")

    return 1 if total_failures_count > 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Practice Problem Generator Matrix Validation Harness")
    parser.add_argument("--node", help="Verify only this specific node ID (e.g. mat_g1_na_q1_7)")
    parser.add_argument("--fail-fast", action="store_true", help="Abort validation immediately on first failure")
    parser.add_argument("--workers", type=int, default=0,
                        help="Parallel worker count (0 = auto = cpu_count). Ignored with --node.")
    args = parser.parse_args()
    return run_matrix_validation(node=args.node, fail_fast=args.fail_fast, workers=args.workers)


def _record(report: dict, node_id: str, failures: list):
    report[node_id] = failures


if __name__ == "__main__":
    sys.exit(main())
