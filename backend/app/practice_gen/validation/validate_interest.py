"""Practice-generation interest invariance on the final student-path problem.

Every mapped context-using DNA is exercised at every node, for every theme the
interest bank declares appropriate to that node's grade, at five deterministic seeds.
The requested theme must survive into final-problem metadata, at least one declared
theme value must reach the learner-visible final problem, and the mathematical answer
must remain invariant.

Known limitation (H-05): visibility proves that the requested theme reached the final
problem; it does not prove the resulting narrative is natural, helpful, or coherent.
Those semantic properties remain Phase 2 judgment work.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from backend.app.services.orchestrator import PracticeOrchestrator

from ..generators.interest import get_grade_appropriate_interests
from ..registry import NODE_TO_DNA, get_node_info
from ._manifest import DNA_MODULE_MAP, load_dna
from .validate_dna import _are_values_equal

ASSERTIONS = ("interest_invariance", "interest_theme_visibility")

INTEREST_SEEDS = (731, 733, 739, 743, 751)
_BANK_PATH = Path(__file__).resolve().parents[4] / "data" / "interest_bank.json"


def _interest_bank() -> Dict[str, Dict[str, Any]]:
    return json.loads(_BANK_PATH.read_text(encoding="utf-8"))["interests"]


def _theme_is_visible(problem: Any, theme: str, bank: Dict[str, Dict[str, Any]]) -> bool:
    """Whether a declared theme value reaches the final learner-facing payload."""
    theme_data = bank[theme]
    candidates: List[str] = []
    for key in ("actors", "objects", "places", "item1", "item2"):
        candidates.extend(str(value).lower() for value in theme_data.get(key, []) if value)
    if theme_data.get("emoji"):
        candidates.append(str(theme_data["emoji"]))
    rendered = json.dumps(problem.model_dump(), ensure_ascii=False, default=str).lower()
    return any(candidate in rendered for candidate in candidates)


def validate_interest_invariance(
    dna: Any,
    grade: int,
    node_id: str,
    trials: int = len(INTEREST_SEEDS),
    bank: Dict[str, Dict[str, Any]] | None = None,
) -> List[str]:
    """Check all supported themes on one node/DNA through the final student path."""
    if not dna.requires_context:
        return []
    if trials < 1 or trials > len(INTEREST_SEEDS):
        raise ValueError(
            f"trials={trials}; expected 1..{len(INTEREST_SEEDS)} deterministic seeds"
        )

    themes = get_grade_appropriate_interests(grade)
    if not themes:
        return [f"{dna.concept} node={node_id} grade={grade}: no supported interest themes"]

    bank = bank or _interest_bank()
    errors: List[str] = []
    for seed in INTEREST_SEEDS[:trials]:
        expected_answer: Any = None
        answer_set = False
        for theme in themes:
            try:
                problem = PracticeOrchestrator.generate_problem(
                    node_id=node_id,
                    seed=seed,
                    interest_theme=theme,
                    is_student_path=True,
                    forced_dna=dna.concept,
                )
            except Exception as exc:
                errors.append(
                    f"{dna.concept} node={node_id} grade={grade} seed={seed} "
                    f"theme={theme!r}: production generation raised: {exc}"
                )
                continue

            if problem.node_id != node_id or problem.dna_name != dna.concept:
                errors.append(
                    f"{dna.concept} node={node_id} grade={grade} seed={seed} "
                    f"theme={theme!r}: served node/DNA "
                    f"{problem.node_id}/{problem.dna_name}"
                )
            if problem.interest_theme != theme:
                errors.append(
                    f"{dna.concept} node={node_id} grade={grade} seed={seed}: "
                    f"requested theme={theme!r}, served metadata={problem.interest_theme!r}"
                )
            if not _theme_is_visible(problem, theme, bank):
                errors.append(
                    f"interest_theme_visibility: {dna.concept} node={node_id} "
                    f"grade={grade} seed={seed} theme={theme!r}: no declared theme "
                    "value reached the final learner-facing problem"
                )

            if not answer_set:
                expected_answer = problem.correct_answer
                answer_set = True
            elif not _are_values_equal(problem.correct_answer, expected_answer):
                errors.append(
                    f"{dna.concept} node={node_id} grade={grade} seed={seed}: "
                    f"correct_answer differs across themes; expected "
                    f"{expected_answer!r}, theme={theme!r} served "
                    f"{problem.correct_answer!r}"
                )
    return errors


def validate_all_interest_invariance() -> Dict[str, List[str]]:
    """Run every applicable node/DNA/theme and gate final theme visibility."""
    results: Dict[str, List[str]] = {}
    bank = _interest_bank()
    visibility_total = 0
    visibility_missing = 0
    visibility_examples: List[str] = []

    for node_id, concepts in NODE_TO_DNA.items():
        node = get_node_info(node_id)
        if node is None:
            results[f"{node_id}/(registry)"] = [
                f"{node_id}: missing knowledge-graph node"
            ]
            continue
        grade = node.get("grade")
        if not isinstance(grade, int):
            results[f"{node_id}/(registry)"] = [
                f"{node_id}: grade must be int, got {grade!r}"
            ]
            continue

        for concept in concepts:
            key = f"{node_id}/{concept}"
            if concept not in DNA_MODULE_MAP:
                results[key] = [f"{concept}: missing from DNA_MODULE_MAP"]
                continue
            try:
                dna = load_dna(concept)
            except ImportError as exc:
                results[key] = [f"{concept}: could not import DNA module: {exc}"]
                continue
            if not dna.requires_context:
                continue

            themes = get_grade_appropriate_interests(grade)
            visibility_total += len(themes) * len(INTEREST_SEEDS)
            results[key] = validate_interest_invariance(
                dna, grade, node_id, bank=bank
            )
            visible_errors = [
                error for error in results[key]
                if error.startswith("interest_theme_visibility:")
            ]
            visibility_missing += len(visible_errors)
            for error in visible_errors:
                if len(visibility_examples) < 5:
                    visibility_examples.append(error)

    total = len(results)
    failed = sum(bool(errors) for errors in results.values())
    print(f"\nInterest invariance: {total - failed}/{total} node/DNA pairs passed.")
    for key, errors in results.items():
        if errors:
            print(f"  FAIL {key}:")
            for error in errors:
                print(f"    - {error}")
    if visibility_missing:
        print(
            "  FAIL interest_theme_visibility: "
            f"{visibility_missing}/{visibility_total} supported requests had no "
            f"theme-bank value in final output; examples={visibility_examples}"
        )
    else:
        print(
            "  PASS interest_theme_visibility: "
            f"all {visibility_total} supported node/DNA/theme/seed requests reached "
            "the final learner-facing problem"
        )
    return results


if __name__ == "__main__":
    _results = validate_all_interest_invariance()
    sys.exit(1 if any(_results.values()) else 0)
