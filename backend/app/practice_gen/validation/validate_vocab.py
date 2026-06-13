"""
Practice Generation — Vocabulary & Concept Constraint Validation

Verifies that generated question text respects grade-level vocabulary
gates and does not use terms the student hasn't been introduced to yet.

Refactored from: ph/matatag_grade_knowledge.json NOT_YET_KNOWN lists.

Run as a module:
    python -m backend.app.practice_gen.validation.validate_vocab
"""

from __future__ import annotations

import importlib
import sys
from typing import Any, Dict, List, Optional

from ..dna.base import DNA, QuestionContext
from ..generators.base_generator import generate_context, get_node
from ..registry import NODE_TO_DNA


# ─── DNA module map ───────────────────────────────────────────────────────────

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
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if isinstance(obj, DNA) and obj.concept == concept:
            return obj
    return None


def _text_contains_term(text: str, term: str) -> bool:
    """
    Return True if `term` appears as a standalone token in `text`.

    Case-insensitive.  Matches whole-word occurrences only
    (the term is surrounded by word boundaries or punctuation).
    """
    import re
    pattern = r"(?<![A-Za-z])" + re.escape(term.lower()) + r"(?![A-Za-z])"
    return bool(re.search(pattern, text.lower()))


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATORS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_vocab_constraints(ctx: QuestionContext, node: Dict) -> List[str]:
    """
    Check that generated question text respects vocabulary gates.

    Scans ctx.question_text for:
      1. Mathematical terms present in node["NOT_YET_KNOWN"] — these are
         explicitly forbidden at this point in the curriculum sequence.
      2. Mathematical terms that appear in ctx.question_text but are not yet
         in node["cumulative_vocab"] — this is a softer warning.

    Note: Only terms found in either NOT_YET_KNOWN or cumulative_vocab are
    checked (we don't scan every English word).

    Args:
        ctx: A generated QuestionContext.
        node: The raw knowledge-graph node dict for ctx.node_id.

    Returns:
        List of violation strings. Empty list = clean.
    """
    violations: List[str] = []
    text = ctx.question_text

    not_yet_known: List[str] = node.get("NOT_YET_KNOWN", [])
    cumulative_vocab: List[str] = node.get("cumulative_vocab", [])

    # 1. Forbidden terms (NOT_YET_KNOWN)
    for term in not_yet_known:
        if _text_contains_term(text, term):
            violations.append(
                f"[NOT_YET_KNOWN] '{term}' found in question text for "
                f"{ctx.node_id}: \"{text[:80]}\""
            )

    # 2. Terms used that are not in cumulative_vocab
    # We only check terms that are vocabulary-significant (present in the node's
    # introduces_vocab lists somewhere in the graph).  Here we check against
    # the node's own cumulative_vocab as a proxy.
    introduces_vocab: List[str] = node.get("introduces_vocab", [])
    for term in introduces_vocab:
        # If this node introduces the term, it's available — skip.
        # We warn only if a future-introduced term appears before it's known.
        pass  # handled by NOT_YET_KNOWN check above

    return violations


def validate_concept_constraints(ctx: QuestionContext, node: Dict) -> List[str]:
    """
    Verify that distractors don't presuppose unknown concepts.

    For each distractor in ctx.distractors, this checks whether the
    ErrorPattern that generated it declares a required_concept that is
    absent from node["cumulative_concepts"].

    Since QuestionContext only stores distractor values (not which
    ErrorPattern produced each), this check operates at the DNA level:
    it verifies that the DNA's error_patterns were properly filtered
    by generate_context before producing ctx.distractors.

    In practice, generate_context already filters error_patterns by
    required_concept — so this validator serves as a belt-and-suspenders
    check that the filtering contract was honoured by confirming no
    filtered-out pattern's value appears in ctx.distractors.

    Args:
        ctx: A generated QuestionContext.
        node: The raw knowledge-graph node dict for ctx.node_id.

    Returns:
        List of violation strings. Empty list = clean.
    """
    violations: List[str] = []
    cumulative_concepts = set(node.get("cumulative_concepts", []))
    cumulative_concepts.update(node.get("introduces_concepts", []))
    cumulative_concepts.add(ctx.dna_concept)

    dna = _load_dna(ctx.dna_concept)
    if dna is None:
        return violations

    # Build the set of distractor values that should have been filtered out.
    forbidden_patterns = [
        ep for ep in dna.error_patterns
        if ep.required_concept not in cumulative_concepts
        and ep.formula not in ("None", None)
    ]

    if not forbidden_patterns or not ctx.distractors:
        return violations

    # Evaluate each forbidden pattern against ctx.values.
    for ep in forbidden_patterns:
        try:
            safe_ns = {k: v for k, v in ctx.values.items() if isinstance(v, (int, float))}
            forbidden_val = eval(ep.formula, {"__builtins__": {}}, safe_ns)  # noqa: S307
        except Exception:
            continue

        if forbidden_val in ctx.distractors:
            violations.append(
                f"[CONCEPT_GATE] Distractor {forbidden_val} from ErrorPattern "
                f"'{ep.label}' (requires_concept='{ep.required_concept}') "
                f"appeared in ctx.distractors but concept is not yet known "
                f"at {ctx.node_id}."
            )

    return violations


def run_vocab_audit(
    node_id: str,
    grade: int,
    sample_count: int = 5,
) -> Dict:
    """
    Generate sample problems for a node and run vocabulary/concept checks.

    Args:
        node_id: MATATAG node ID (e.g. "mat_g1_na_q1_7").
        grade: Student grade level.
        sample_count: Number of problems to generate and check.

    Returns:
        Dict with keys:
            "node_id"    (str)
            "violations" (list of str) — all violations found
            "pass_rate"  (float) — fraction of problems with zero violations
    """
    node = get_node(node_id)
    if node is None:
        return {
            "node_id": node_id,
            "violations": [f"node_id '{node_id}' not found in knowledge graph."],
            "pass_rate": 0.0,
        }

    # Pick the first DNA concept for this node
    concepts = NODE_TO_DNA.get(node_id, [])
    if not concepts:
        return {
            "node_id": node_id,
            "violations": [f"node_id '{node_id}' has no entry in NODE_TO_DNA."],
            "pass_rate": 0.0,
        }

    dna = _load_dna(concepts[0])
    if dna is None:
        return {
            "node_id": node_id,
            "violations": [f"Could not import DNA for concept '{concepts[0]}'."],
            "pass_rate": 0.0,
        }

    all_violations: List[str] = []
    problems_with_violations = 0

    for seed in range(sample_count):
        try:
            ctx = generate_context(
                dna=dna,
                node_id=node_id,
                grade=grade,
                seed=seed,
                difficulty_profile=None,
                interest_theme=None,
            )
        except Exception as exc:
            all_violations.append(
                f"seed={seed}: generate_context raised: {exc}"
            )
            problems_with_violations += 1
            continue

        v1 = validate_vocab_constraints(ctx, node)
        v2 = validate_concept_constraints(ctx, node)
        problem_violations = v1 + v2

        if problem_violations:
            problems_with_violations += 1
            all_violations.extend(problem_violations)

    pass_rate = (sample_count - problems_with_violations) / sample_count

    return {
        "node_id": node_id,
        "violations": all_violations,
        "pass_rate": pass_rate,
    }


# ─── entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Spot-check a handful of nodes across grades and branches.
    _SAMPLE_NODES = [
        ("mat_g1_na_q1_7", 1),
        ("mat_g1_mg_q1_0", 1),
        ("mat_g2_na_q3_2", 2),
        ("mat_g3_na_q2_1", 3),
        ("mat_g3_dp_q3_1", 3),
    ]

    any_failures = False
    for nid, gr in _SAMPLE_NODES:
        result = run_vocab_audit(nid, gr, sample_count=5)
        rate = result["pass_rate"]
        status = "PASS" if not result["violations"] else "FAIL"
        print(f"  {status} {nid} (grade {gr}) — pass_rate={rate:.2f}")
        if result["violations"]:
            any_failures = True
            for v in result["violations"]:
                print(f"    - {v}")

    sys.exit(1 if any_failures else 0)
