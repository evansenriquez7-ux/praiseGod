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
import re
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


# Continuous axes that express a *magnitude ceiling* on the numbers a problem may
# contain (as opposed to a count of categories, or a 0-1 difficulty scalar). Only
# these support the generated-value containment assertion in 1A/1B.
# How close to the competency maximum the largest sample at scalar 1.0 has to get
# for the range to count as "exercised" (§1A's "reaches the maximum region").
# Deliberately not 100%: sampling is random and some DNAs round to a friendly
# value, so demanding the exact ceiling would flag correct generators. At 60% a
# generator serving sums of 46 against a stated ceiling of 1000 fails, which is
# the class of gap this exists to catch.
_REACH_FRACTION = 0.6

MAGNITUDE_CAP_AXES: Set[str] = {
    "max_sum",
    "max_product",
    "max_total",
    "max_value",
    "value_max",
    "ordinal_range",
    "range",
}


def _numeric_payload_values(problem: Dict[str, Any]) -> List[Tuple[str, float]]:
    """
    Every plain number a generated problem exposes to the student, labelled for
    the failure message. Booleans are excluded (True == 1 in Python and a
    true/false answer carries no magnitude); non-numeric answers and nested
    structures are skipped rather than coerced.
    """
    out: List[Tuple[str, float]] = []

    def _add(label: str, v: Any) -> None:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return
        out.append((label, float(v)))

    for k, v in (problem.get("given_values") or {}).items():
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                _add(f"given_values.{k}[{i}]", item)
        else:
            _add(f"given_values.{k}", v)

    answer = problem.get("correct_answer")
    if isinstance(answer, (list, tuple)):
        for i, item in enumerate(answer):
            _add(f"correct_answer[{i}]", item)
    else:
        _add("correct_answer", answer)

    return out


def _normalize_stem(text: str) -> str:
    """Lowercase the stem and render LaTeX fractions as 'a/b' so an option like
    '1/8' can be matched against a stem that displays \\(\\frac{1}{8}\\)."""
    t = str(text or "").lower()
    t = re.sub(r"\\d?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"\1/\2", t)
    return t


def _option_in_stem(value: Any, stem: str) -> bool:
    """
    Whether an option value appears in the stem as a *whole* token.

    Substring matching is wrong here: '1' occurs inside '10', and '11' inside
    '0:11', which would make almost every arithmetic item look like a leak.
    """
    s = str(value).strip().lower()
    if not s:
        return False
    # Trailing ':' or '.' only blocks a match when a digit follows it, so "11:00."
    # at the end of a sentence matches while "11" inside "0:11" does not, and "1"
    # inside "1.5" does not.
    return re.search(
        rf"(?<![\w/:.]){re.escape(s)}(?![\w/])(?![:.]\d)", stem
    ) is not None


def _answer_leaks_into_stem(problem: Dict[str, Any]) -> Optional[str]:
    """
    Return a description of the leak, or None.

    A stem that contains its own answer is only a defect when the answer is
    thereby *uniquely* identifiable. Two families of item legitimately restate
    their answer and are deliberately not flagged:

      * comparison and ordering items, which name every candidate they ask about
        ("Which shape has more sides — a triangle or a rectangle?") — caught by
        requiring that exactly one option appear in the stem;
      * items whose task *is* to restate a value under an operation, where the
        answer coincides with an operand ("2 + 1 = 1 + ___" for commutativity,
        "2 + 0 = ___", "4 x 1 = ___") — caught by requiring that the answer be
        the *only* datum in the stem. An item with a second number is asking the
        student to combine them, however trivially; whether such degenerate
        operands are good pedagogy is a separate question from answer leakage,
        and conflating the two made this check fire on 3,702 samples, nearly all
        of them well-formed identity facts.

    What remains is the genuine defect: the stem presents exactly one value, that
    value is the answer, and the student need only copy it — "Jose has lunch at
    1:30. What time is that?", or "What fraction does 2/5 equal parts represent?".
    """
    answer = problem.get("correct_answer")
    if isinstance(answer, (list, tuple, dict, bool)) or answer is None:
        return None  # ordering/true-false/structured answers: nothing to give away

    fmt_data = problem.get("format_data") or {}
    options = fmt_data.get("mcq_options") or fmt_data.get("options")
    if not isinstance(options, list) or len(options) < 2:
        return None  # no distractors to compare against

    stem = _normalize_stem(problem.get("question_text", ""))
    if not stem:
        return None

    present = []
    correct_present = False
    for opt in options:
        if not isinstance(opt, dict):
            return None
        value = opt.get("value")
        if value is None:
            continue
        if _option_in_stem(value, stem):
            present.append(value)
            if opt.get("is_correct"):
                correct_present = True

    if not (correct_present and len(present) == 1):
        return None

    # Mirroring tasks are the one family where answer == given is the *correct*
    # mathematics rather than a leak: a symmetric figure's second half has, by
    # definition, the same number of squares as its first. Copying the value is
    # the skill being assessed, so these are exempt.
    if re.search(r"\bsymmetr(?:y|ic|ical)\b|\bline of symmetry\b|\bmirror\b", stem):
        return None

    # The answer is the stem's only datum → nothing to compute, just copy it.
    stem_values = set(re.findall(r"\d+(?::\d+|/\d+|\.\d+)?", stem))
    if stem_values and stem_values == {str(answer).strip().lower()}:
        return (
            f"the answer {answer!r} is the only value in the stem, so it can be copied "
            f"rather than derived"
        )
    return None


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


# ─────────────────────────────────────────────────────────────────────────────
# Executed-check instrumentation (doc_rem.md §3.5 drift tripwire).
#
# run_all.py cross-checks docs/pgen_contract.md's rule table against the set of
# checks that actually ran. For that comparison to mean anything, the executed
# set has to be *observed*, not asserted by the caller: an earlier version had
# run_all add "§1A".."§1E" to the executed set simply because the matrix exited
# 0, which made the comparison tautological — it could never detect a check
# whose loop body stopped running (an axis filter that matches nothing, a
# formatter list that comes back empty, a section commented out). Each check
# site below records its own id when it actually evaluates an assertion, so a
# silently-dead check now shows up as contract drift and fails the run.
#
# LAST_EXECUTED_CHECKS is populated by run_matrix_validation(); it is a module
# global because multiprocessing workers return their sets for the parent to
# union rather than sharing state.
LAST_EXECUTED_CHECKS: Set[str] = set()

# node_id -> sorted list of §-refs that node actually exercised (written to the
# JSON report alongside the failures).
_EXECUTED_BY_NODE: Dict[str, List[str]] = {}


def run_matrix_for_node(node_id: str, fail_fast: bool) -> Tuple[List[Dict[str, Any]], Set[str]]:
    failures = []
    executed: Set[str] = set()

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
        return failures, executed

    node_info = get_node_info(node_id)
    grade = node_info.get("grade", 1)
    quarter = node_info.get("quarter", 1)
    
    # ─── Load knowledge graph node for vocab gating
    from backend.app.practice_gen.registry import _KG_NODES
    node_kg = _KG_NODES.get(node_id, {})
    not_yet_known = node_kg.get("NOT_YET_KNOWN", [])
    # Merge introduces_vocab the same way cumulative_concepts merges
    # introduces_concepts below: a node's own newly-introduced compound
    # vocab (e.g. mat_g2_mg_q4_3's "straight line"/"curved line") must be
    # allowed to exempt its NOT_YET_KNOWN substring (bare "line", reserved
    # for the later G3 point/line/segment/ray node) -- otherwise no node
    # could ever use the exact vocabulary it exists to introduce.
    cumulative_vocab_list = node_kg.get("cumulative_vocab", []) + node_kg.get("introduces_vocab", [])
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
                return failures, executed
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
                            return failures, executed

            # --- 1A. Scalar boundary exactness ---
            expected_0_0 = get_expected_mapped_value(axis, 0.0, min_val, max_val)
            expected_1_0 = get_expected_mapped_value(axis, 1.0, min_val, max_val)

            # 1A - 0.0 ceiling assertion
            if axis_name != "number_difficulty":
                executed.add("§1A")
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
                        return failures, executed

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
                        return failures, executed

                if max_obs_1_0 != expected_1_0:
                    failures.append({
                        "dna": dna_name,
                        "formatter": "unknown",
                        "check": f"scalar_exactness_1.0_{axis_name}",
                        "seed": 200,
                        "error": f"At 1.0, governed parameter maximum observed value ({max_obs_1_0}) != maximum window ceiling ({expected_1_0})."
                    })
                    if fail_fast:
                        return failures, executed

            # --- 1B. Window containment sweep (containment & monotonicity) ---
            ceilings = []
            for scalar in [0.0, 0.25, 0.5, 0.75, 1.0]:
                expected_ceil = get_expected_mapped_value(axis, scalar, min_val, max_val)
                ceilings.append(expected_ceil)
                
                if axis_name != "number_difficulty":
                    executed.add("§1B")
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
                                return failures, executed

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
                        return failures, executed

            # --- 1A/1B. Generated-value containment (the actual leaky-window check) ---
            #
            # Everything above verifies the scalar -> parameter *mapping*: that the
            # difficulty_profile echoed back carries the right ceiling. It never
            # looked at the numbers the DNA actually produced, so a generator that
            # was handed max_sum=20 and then sampled sums up to 30 passed cleanly.
            # That is precisely the "classic leaky window" Phase 1 §1A names ("no
            # sample exceeds the competency maximum") and Phase 4's first planted
            # mutation targets — and it survived until this check existed.
            #
            # Scoped to scalar 1.0, matching §1A's wording exactly ("no sample
            # exceeds the competency maximum"). It deliberately does NOT assert
            # containment at lower scalars: a window ceiling below a task's
            # structural minimum is routine and legitimate (ordering three distinct
            # numbers needs values above a scalar-0.0 ceiling of 1), so asserting
            # there would flag correct generators rather than leaky ones.
            if axis_name in MAGNITUDE_CAP_AXES:
                # Containment runs FIRST, and unconditionally. It used to sit
                # below the `axis_name not in comp_bounds` guard that narrows
                # *reach*, so that one `continue` also switched off this check —
                # the §1B "no leaky windows" row — for every magnitude axis a
                # competency does not explicitly bind: 14 (node, dna, axis)
                # triples across 13 nodes, 11 of which then had no magnitude
                # containment coverage at all. Verified by inflating every
                # generated integer by 10 000: mat_g1_mg_q2_2 (bound) raised 110
                # value_containment failures, mat_g1_na_q1_5 and mat_g1_dp_q3_0
                # (unbound) raised none. Narrowing reach to competency-bound
                # axes is sound and is preserved below; narrowing containment
                # was never intended — "the DNA exceeded the ceiling it was
                # handed" is a defect whether that ceiling came from the
                # competency or from the axis catalog's default.
                for p in generations[1.0]:
                    cap = p.get("difficulty_profile", {}).get(axis_name)
                    if not isinstance(cap, (int, float)) or isinstance(cap, bool):
                        continue
                    for label, value in _numeric_payload_values(p):
                        if value > cap:
                            failures.append({
                                "dna": dna_name,
                                "formatter": p.get("format", "unknown"),
                                "check": f"value_containment_{axis_name}",
                                "seed": p.get("seed", 0),
                                "error": (
                                    f"Leaky window on axis '{axis_name}' at scalar 1.0: "
                                    f"{label}={value} exceeds the competency maximum {cap} the "
                                    f"DNA was given. Reproduce: node={node_id} dna={dna_name} "
                                    f"seed={p.get('seed')} profile={{'{axis_name}': 1.0}}."
                                ),
                            })
                            if fail_fast:
                                return failures, executed

                # §1A's other half: "at 1.0, at least one sample *reaches* the
                # competency maximum region". Without it a generator can sit far
                # below its own ceiling forever and still pass — e.g. a "sums up
                # to 1000" competency serving nothing above 46. That was the
                # single largest cluster of FAIL verdicts in the judgment
                # reviews (25 of 44 nodes), i.e. a machine-checkable rule that
                # had been left to human opinion.
                # Only assert reach where the node's *competency* states the
                # ceiling. With no bound the ceiling comes from the axis catalog's
                # default, which is a UI range rather than a curriculum claim:
                # mat_g1_na_q1_5 reads "ordinal numbers 1st ... up to 10th" but
                # binds no ordinal_range, so the default 100 would be asserted
                # against a competency that stops at 10. Asserting against a
                # default is the same mistake as sweeping one axis while another
                # sits at 0.5, and it produces failures no generator change can
                # honestly fix.
                if axis_name not in comp_bounds:
                    continue

                # A magnitude-cap axis sets the *ceiling*; `number_difficulty` is
                # the separate axis that decides where inside that ceiling values
                # are drawn. Sweeping only the cap axis therefore measures the
                # co-axis's 0.5 default — multiplication looked stuck at 30/100
                # until number_difficulty was raised too, at which point it
                # reached 90. Drive both to 1.0 so this asserts the generator's
                # true reach rather than a default's.
                reach_profile: Dict[str, Any] = {axis_name: 1.0, "number_difficulty": 1.0}
                reach_samples = []
                for idx in range(10):
                    seed = int(900 + idx)
                    try:
                        reach_samples.append(
                            run(node_id=node_id, difficulty_profile=reach_profile,
                                seed=seed, forced_dna=dna_name)
                        )
                    except Exception as exc:
                        failures.append({
                            "dna": dna_name,
                            "formatter": "unknown",
                            "check": f"reach_generation_{axis_name}",
                            "seed": seed,
                            "error": f"Failed to generate at {reach_profile}: {exc}",
                        })
                        if fail_fast:
                            return failures, executed
                        break

                reach_floor = cap_reach_floor = None
                observed_peak = None
                for p in reach_samples:
                    cap = p.get("difficulty_profile", {}).get(axis_name)
                    if not isinstance(cap, (int, float)) or isinstance(cap, bool):
                        continue
                    executed.add("§1A-reach")
                    cap_reach_floor = cap * _REACH_FRACTION
                    reach_floor = cap
                    for _, value in _numeric_payload_values(p):
                        if observed_peak is None or value > observed_peak:
                            observed_peak = value
                if (
                    cap_reach_floor is not None
                    and observed_peak is not None
                    and observed_peak < cap_reach_floor
                ):
                    failures.append({
                        "dna": dna_name,
                        "formatter": "unknown",
                        "check": f"value_reaches_max_{axis_name}",
                        "seed": 200,
                        "error": (
                            f"Ceiling never approached on axis '{axis_name}': at scalar 1.0 the "
                            f"largest value generated across {len(reach_samples)} samples was "
                            f"{observed_peak}, below {_REACH_FRACTION:.0%} of the competency "
                            f"maximum {reach_floor}. The competency's stated range is not being "
                            f"exercised. Reproduce: node={node_id} dna={dna_name} "
                            f"profile={{'{axis_name}': 1.0}}."
                        ),
                    })
                    if fail_fast:
                        return failures, executed

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
                                return failures, executed
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
                            return failures, executed

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

        # A formatter that explicitly restricts a variant this node's competency
        # binds to an unsupported value is not available for this node — the
        # serving path rejects that DNA/formatter pair (see orchestrator's
        # explicitly_restricted check), so forward-testing it as "should succeed"
        # asserts the opposite of the contract. Example: patterns bound to
        # ask_type="identify_valid" cannot route to the pattern_sequence visual,
        # which restricts ask_type to next/missing. Such pairs are covered by the
        # reverse check ("must raise"), not by the execution matrix.
        available_formatters = []
        for fmt in formatters:
            restrictions = FORMATTER_VARIANT_SUPPORT.get(dna_name, {}).get(fmt)
            if isinstance(restrictions, dict) and any(
                var_name in restrictions
                and not isinstance(bound_val, list)
                and not any(str(v) == str(bound_val) for v in restrictions[var_name])
                for var_name, bound_val in comp_bounds.items()
            ):
                continue
            available_formatters.append(fmt)
        formatters = available_formatters
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

            # Two situations legitimately leave a variant axis with nothing for the
            # caller to select, and both must remove that axis from the combination
            # space rather than annihilating every combination:
            #
            #  1. The competency binds a *synthesized scope* that is not a
            #     Lab-selectable option — patterns' pattern_type="increasing_or_decreasing",
            #     counting's skip_interval="by_1". The registry applies these
            #     internally; the serving path never passes them in a difficulty
            #     profile, so neither may the harness (doing so makes the
            #     orchestrator reject the DNA outright).
            #  2. Every option of the variant is curriculum-gated out at this
            #     node's grade/quarter, so the Lab offers the axis no values at all.
            #
            # Intersecting either case against the option list matched nothing and
            # silently emptied the whole execution matrix for 22 of 151 nodes — all
            # of which still reported PASS, because "no failures" was being read as
            # "verified" (Phase 1: "Any skipped combination is a failure").
            # Competency bounds and the compatibility table disagree on scalar type
            # for some axes — registry.py binds missing_number's `tables` as ints
            # [2,3,4,5,10] while VARIANTS_BY_DNA declares them as strings
            # ['2','3','4','5','10']. Comparing those directly makes every option
            # look out-of-bounds and emptied the matrix for 2 nodes. Matching on the
            # string form restores the check's intent ("is this Lab option inside the
            # competency's allowed set?") without loosening it; the underlying type
            # drift is flagged in IMPLEMENTATION_STATUS.md.
            def _matches(opt_val: Any, bound_val: Any) -> bool:
                if isinstance(bound_val, list):
                    return str(opt_val) in {str(b) for b in bound_val}
                return str(opt_val) == str(bound_val)

            omitted_axes: Dict[str, str] = {}
            for var_name, opt_vals in supported_variants.items():
                if all((var_name, v) in curriculum_excluded for v in opt_vals):
                    omitted_axes[var_name] = "every option curriculum-gated at this grade/quarter"
            for var_name, bound_val in comp_bounds.items():
                if var_name not in supported_variants or var_name == "regrouping":
                    continue
                if isinstance(bound_val, list):
                    continue
                if not any(_matches(v, bound_val) for v in supported_variants[var_name]):
                    omitted_axes[var_name] = f"competency binds synthesized scope {bound_val!r}"

            # Filter combinations by competency bounds and curriculum grade/quarter gates
            filtered_combinations = []
            for assignment in combinations:
                allowed = True
                for var_name, opt_val in assignment.items():
                    if var_name in omitted_axes:
                        continue  # dropped below; the registry governs this axis
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
                        elif not _matches(opt_val, bound_val):
                            allowed = False
                            break
                if allowed:
                    filtered_combinations.append(
                        {k: v for k, v in assignment.items() if k not in omitted_axes}
                    )

            # Dropping an axis collapses several assignments onto the same reduced
            # one, so dedupe rather than re-running an identical assignment N times.
            combinations = []
            for a in filtered_combinations:
                if a not in combinations:
                    combinations.append(a)

            executed.add("§1C-coverage")
            if not combinations:
                failures.append({
                    "dna": dna_name,
                    "formatter": formatter,
                    "check": "empty_execution_matrix",
                    "seed": 0,
                    "error": (
                        f"No variant combination survives filtering for node '{node_id}', DNA "
                        f"'{dna_name}', formatter '{formatter}' — the execution matrix would be "
                        f"skipped entirely and the node would report PASS without generating a "
                        f"single problem. comp_bounds={comp_bounds}, "
                        f"supported_variants={supported_variants}, "
                        f"curriculum_excluded={sorted(curriculum_excluded)}, "
                        f"omitted_axes={omitted_axes}."
                    ),
                })
                if fail_fast:
                    return failures, executed

            for assignment in combinations:
                generations_1c = []
                # 1C - Run pipeline over 5 seeds
                for seed in [42, 43, 44, 45, 46]:
                    try:
                        p = run(node_id=node_id, formatter=formatter, difficulty_profile=assignment, seed=seed, forced_dna=dna_name)
                        generations_1c.append(p)
                        executed.add("§1C")

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
                            executed.add("§4")
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
                            executed.add("§1E")
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
                                    # Ground Rule 5 disclosure, 2026-08-02: widened from
                                    # operation in ("add","subtract","add_subtract","compare")
                                    # to every fractions operation. _eval_formula (validate_dna.py)
                                    # evaluates "numerator / denominator" with Python's native
                                    # `/`, a true-division float -- exact for a power-of-2
                                    # denominator (1/8 == 0.125, no rounding error) but not for
                                    # any other (1/3 == 0.3333333333333333, off from the exact
                                    # rational by ~1e-17). validate_math_answer then parses that
                                    # imprecise float as a sympy Float and the served "1/3" as an
                                    # exact Rational, and their difference does not simplify to
                                    # exactly 0 -- a false answer-key failure on a genuinely
                                    # correct served answer, not a pipeline defect
                                    # (mat_g2_na_q4_0/_1/_2, seed 42, exposed once the
                                    # generate_number_by_window fix let a non-power-of-2
                                    # denominator be sampled at all -- the prior deterministic-
                                    # collapse bug always served 1/8 here, which is exactly
                                    # representable and silently never triggered this).
                                    # validate_dna.py's own `_are_values_equal` already exists to
                                    # do this comparison correctly (mirroring this exact
                                    # float-vs-fraction-string class of false positive, first
                                    # fixed there for "0.5" vs "1/2" -- see
                                    # HARDENING_EVIDENCE.md Ground Rule 2, item 3); this extends
                                    # the equivalent bypass here rather than reimplementing that
                                    # fix a second time.
                                    dna_name == "fractions"
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
                            return failures, executed

                # --- 1E. Interest-theme invariance (formatted output) ---
                if generations_1c and dna.dna_type in ("formula", "algorithmic") and dna.requires_context:
                    executed.add("§1E")
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

                # --- 1F. Answer-leak lint (the stem may not give away its own answer) ---
                #
                # Blind reviewers kept flagging self-answering items by eye —
                # "Maria wakes up at 11:00. What time is that?" with 11:00 among
                # the options, or "What fraction does 1/8 equal parts represent?"
                # answered 1/8. A student scores those without doing the skill,
                # so the item measures nothing. This is mechanical, so it belongs
                # in the harness rather than in a reviewer's judgment.
                for p in generations_1c:
                    executed.add("§1F")
                    leak = _answer_leaks_into_stem(p)
                    if leak is not None:
                        failures.append({
                            "dna": dna_name,
                            "formatter": formatter,
                            "check": "answer_leak_in_stem",
                            "seed": p["seed"],
                            "error": (
                                f"Question stem gives away its own answer: {leak}. A student can "
                                f"answer without exercising the competency. question_text="
                                f"{p.get('question_text','')!r}, correct_answer="
                                f"{p.get('correct_answer')!r}."
                            ),
                        })
                        if fail_fast:
                            return failures, executed

                # --- 1D. Vocabulary & Concept Gating on FORMATTED output ---
                for p in generations_1c:
                    executed.add("§1D")
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
                    executed.add("§1C-reverse")
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

    return failures, executed


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
        failures, executed = run_matrix_for_node(node_id, fail_fast=False)
        return node_id, failures, executed
    except Exception as exc:
        return node_id, [{"dna": "unknown", "formatter": "unknown", "check": "worker_crash",
                          "seed": 0, "error": str(exc)}], set()


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

    global LAST_EXECUTED_CHECKS
    LAST_EXECUTED_CHECKS = set()
    _EXECUTED_BY_NODE.clear()

    report: Dict[str, list] = {}
    total_failures_count = 0
    passed_count = 0
    report_path = Path("validation_reports/matrix_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    def _flush_report():
        with report_path.open("w", encoding="utf-8") as fh:
            json.dump({**report, "_executed_checks": _EXECUTED_BY_NODE},
                      fh, indent=2, ensure_ascii=False)

    if len(node_ids) == 1 or workers == 1:
        # Single-node or forced-sequential mode
        for idx, node_id in enumerate(node_ids, 1):
            print(f"[{idx}/{len(node_ids)}] Checking {node_id} ...", end="", flush=True)
            node_failures, node_executed = run_matrix_for_node(node_id, fail_fast)
            LAST_EXECUTED_CHECKS |= node_executed
            _record(report, node_id, node_failures, node_executed)
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
            for node_id, node_failures, node_executed in pool.imap_unordered(_worker, node_ids):
                completed += 1
                LAST_EXECUTED_CHECKS |= node_executed
                _record(report, node_id, node_failures, node_executed)
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
    print(f"Contract checks actually executed: {sorted(LAST_EXECUTED_CHECKS)}")
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


def _record(report: dict, node_id: str, failures: list, executed: Optional[Set[str]] = None):
    # `report` stays a pure node -> failure-list map (node counts are derived from
    # its length). Per-node executed-check coverage rides in a parallel dict that
    # is merged in only at flush time, so a reviewer can see not just which nodes
    # failed but which contract checks each node actually exercised — an empty
    # coverage set is a node the matrix walked past without asserting anything.
    report[node_id] = failures
    _EXECUTED_BY_NODE[node_id] = sorted(executed or ())


if __name__ == "__main__":
    sys.exit(main())
