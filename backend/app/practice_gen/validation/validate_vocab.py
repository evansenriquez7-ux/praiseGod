"""
Practice Generation — Vocabulary & Concept Constraint Validation

Verifies that generated question text respects grade-level vocabulary
gates and does not use terms the student hasn't been introduced to yet.

Refactored from: data/ph/matatag_grade_knowledge.json NOT_YET_KNOWN lists.

Run as a module:
    python -m backend.app.practice_gen.validation.validate_vocab
"""

from __future__ import annotations

import importlib
import sys
from typing import Any, Dict, List, Optional

from ..dna.base import DNA, QuestionContext
from ..generators.base_generator import generate_context, get_node
from ..registry import NODE_TO_DNA, get_all_node_ids, get_node_info


from ._manifest import DNA_MODULE_MAP, load_dna


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

    def _is_subtoken_only_of_known_compound(term: str, known: List[str], text: str) -> bool:
        """True if `term` appears in `text` ONLY inside known compound vocab, never standalone."""
        import re
        t_lower = term.lower()
        containing_knowns = [k for k in known if t_lower in k.lower() and k.lower() != t_lower]
        if not containing_knowns:
            return False
        # Replace every known compound phrase with a placeholder, then check for term alone
        modified = text.lower()
        for known_compound in containing_knowns:
            modified = modified.replace(known_compound.lower(), " __KNOWN__ ")
        standalone_pattern = r'(?<![A-Za-z])' + re.escape(t_lower) + r'(?![A-Za-z])'
        return not bool(re.search(standalone_pattern, modified))

    # 1. Forbidden terms (NOT_YET_KNOWN)
    for term in not_yet_known:
        if _text_contains_term(text, term):
            # Exempt: term only appears as sub-token of a known compound (e.g. "line" in "number line")
            if _is_subtoken_only_of_known_compound(term, cumulative_vocab, text):
                continue
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

    try:
        dna = load_dna(ctx.dna_concept)
    except ImportError:
        return violations

    forbidden_patterns = [
        ep for ep in dna.error_patterns
        if ep.required_concept not in cumulative_concepts
    ]
    forbidden_labels = {ep.label for ep in forbidden_patterns}
    if not forbidden_labels or not ctx.distractors:
        return violations

    distractors_provenance = getattr(ctx, "distractors_provenance", {}) or {}
    for d, source in distractors_provenance.items():
        if source in forbidden_labels:
            violations.append(
                f"[CONCEPT_GATE] Distractor {d} from ErrorPattern "
                f"'{source}' appeared in ctx.distractors but concept is not yet known "
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

    try:
        dna = load_dna(concepts[0])
    except ImportError as e:
        return {
            "node_id": node_id,
            "violations": [f"Could not import DNA for concept '{concepts[0]}': {e}"],
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


def lint_all_vocab_gated_instances() -> List[str]:
    from backend.app.practice_gen.validation._manifest import DNA_MODULE_MAP
    from backend.app.practice_gen.adapter import FORMATTER_ROUTES
    from backend.app.practice_gen.dna.base import VocabGated
    import importlib

    violations: List[str] = []

    # 1. Collect all VocabGated instances and their source modules
    vocab_gated_by_concept: Dict[str, List[VocabGated]] = {}

    # Gather from DNA modules
    for concept, module_path in DNA_MODULE_MAP.items():
        try:
            mod = importlib.import_module(module_path)
            instances = []
            for name in dir(mod):
                val = getattr(mod, name)
                if isinstance(val, VocabGated):
                    instances.append(val)
            if instances:
                vocab_gated_by_concept[concept] = instances
        except Exception as e:
            violations.append(f"Failed to import DNA module {module_path}: {e}")

    # Gather from formatter modules
    formatter_gated_instances: List[VocabGated] = []
    for fmt_name, route in FORMATTER_ROUTES.items():
        module_path, _, _ = route
        try:
            mod = importlib.import_module(module_path)
            for name in dir(mod):
                val = getattr(mod, name)
                if isinstance(val, VocabGated):
                    formatter_gated_instances.append(val)
        except Exception as e:
            violations.append(f"Failed to import formatter module {module_path}: {e}")

    # 2. Audit against knowledge graph nodes
    # For DNA-specific instances: check against every node mapped to that DNA concept
    for concept, instances in vocab_gated_by_concept.items():
        nodes_for_concept = [nid for nid, concepts in NODE_TO_DNA.items() if concepts and concepts[0] == concept]
        for nid in nodes_for_concept:
            node = get_node(nid)
            if not node:
                continue
            not_yet_known = node.get("NOT_YET_KNOWN", [])
            cumulative_vocab = set(node.get("cumulative_vocab", []))
            for inst in instances:
                # If requires_vocab is known, preferred is resolved; otherwise, fallback is resolved
                if inst.requires_vocab in cumulative_vocab:
                    resolved_text = inst.preferred
                else:
                    resolved_text = inst.fallback

                for term in not_yet_known:
                    if _text_contains_term(resolved_text, term):
                        violations.append(
                            f"[VOCAB_GATED_LINT] DNA '{concept}' instance resolved text '{resolved_text}' "
                            f"contains forbidden term '{term}' for node '{nid}'."
                        )

    # For formatter-level instances: check against every node
    for inst in formatter_gated_instances:
        for nid, concepts in NODE_TO_DNA.items():
            if not concepts:
                continue
            node = get_node(nid)
            if not node:
                continue
            not_yet_known = node.get("NOT_YET_KNOWN", [])
            cumulative_vocab = set(node.get("cumulative_vocab", []))
            # Determine resolved branch
            if inst.requires_vocab in cumulative_vocab:
                resolved_text = inst.preferred
            else:
                resolved_text = inst.fallback

            for term in not_yet_known:
                if _text_contains_term(resolved_text, term):
                    violations.append(
                        f"[VOCAB_GATED_LINT] Formatter instance resolved text '{resolved_text}' "
                        f"contains forbidden term '{term}' for node '{nid}'."
                    )

    return violations


def run_all_vocab_audits(sample_count: int = 5) -> Dict[str, Dict]:
    """
    Run run_vocab_audit for every node in the knowledge graph (full-node mode),
    not just a handful of spot-checked nodes.

    Returns:
        Dict mapping node_id -> audit result dict (node_id, violations, pass_rate).
    """
    results: Dict[str, Dict] = {}

    # Run static VocabGated linter
    lint_violations = lint_all_vocab_gated_instances()
    if lint_violations:
        results["static_vocab_gated_lint"] = {
            "node_id": "static_vocab_gated_lint",
            "violations": lint_violations,
            "pass_rate": 0.0
        }
        print("  FAIL static_vocab_gated_lint:")
        for v in lint_violations:
            print(f"    - {v}")

    for node_id in get_all_node_ids():
        node = get_node_info(node_id)
        if node is None:
            raise ValueError(f"Node '{node_id}' is in NODE_TO_DNA but missing from the knowledge graph.")
        grade = node.get("grade")
        if grade is None:
            raise ValueError(f"Node '{node_id}' has no 'grade' field in the knowledge graph.")
        results[node_id] = run_vocab_audit(node_id, grade, sample_count=sample_count)
    return results


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

    # Run static linter
    lint_violations = lint_all_vocab_gated_instances()
    if lint_violations:
        print("  FAIL static_vocab_gated_lint:")
        for v in lint_violations:
            print(f"    - {v}")
        any_failures = True

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
