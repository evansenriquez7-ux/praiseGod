"""
Practice Generation — Pipeline Coordinator
============================================

High-level public interface that ties the adapter layer together.
External code (API endpoints, tests, batch scripts) calls this module.

Usage:
    from backend.app.practice_gen.pipeline import run, run_batch, get_pipeline_status

    problem_dict = run("mat_g1_na_q1_7", student_grade=1)
    batch = run_batch("mat_g2_na_q1_8", grade=2, count=5)
    status = get_pipeline_status()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.app.services.orchestrator import PracticeOrchestrator
from .generators.base_generator import _DNA_MODULE_MAP, _import_dna_module
from .registry import get_all_node_ids, get_node_dnas


def run(
    node_id: str,
    student_grade: int,
    student_interest: Optional[str] = None,
    difficulty_profile: Optional[Dict[str, Any]] = None,
    formatter: Optional[str] = None,
    experience: str = "standard",
    seed: Optional[int] = None,
    allowed_formatters: Optional[List[str]] = None,
    allowed_difficulties: Optional[Dict[str, List[Any]]] = None,
    allowed_contexts: Optional[Dict[str, List[str]]] = None,
    is_lab: bool = False,
) -> Dict[str, Any]:
    """
    Generate a single practice problem and return it as a dict.

    This is the single function external code calls to get a complete
    practice problem from the new pipeline.

    Args:
        node_id: MATATAG node identifier, e.g. "mat_g1_na_q1_7".
        student_grade: Student grade level (1–3).
        student_interest: Optional interest theme ID.
        difficulty_profile: Optional axis → level mapping.
        formatter: Optional formatter name. If None, picked automatically.
        experience: Experience wrapper name.
        seed: Reproducibility seed. If None, random.
        is_lab: Whether this is called from the lab to bypass curriculum bounds.

    Returns:
        problem.to_dict() — a fully serialised FormattedProblem dict.
    """
    problem = PracticeOrchestrator.generate_problem(
        node_id=node_id,
        grade=student_grade,
        seed=seed,
        difficulty_profile=difficulty_profile,
        interest_theme=student_interest,
        formatter=formatter,
        experience=experience,
        allowed_formatters=allowed_formatters,
        allowed_difficulties=allowed_difficulties,
        allowed_contexts=allowed_contexts,
        is_lab=is_lab,
    )
    return problem.model_dump()


def run_batch(
    node_id: str,
    grade: int,
    count: int = 5,
    difficulty_profile: Optional[Dict[str, Any]] = None,
    student_interest: Optional[str] = None,
    experience: str = "standard",
    allowed_formatters: Optional[List[str]] = None,
    allowed_difficulties: Optional[Dict[str, List[Any]]] = None,
    allowed_contexts: Optional[Dict[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate a batch of varied practice problems and return them as dicts.

    Args:
        node_id: MATATAG node identifier.
        grade: Student grade level (1–3).
        count: Number of problems to generate (default 5).
        difficulty_profile: Optional shared difficulty profile.
        student_interest: Optional shared interest theme.
        experience: Experience wrapper applied to all problems.

    Returns:
        List of native dicts.
    """
    problems = PracticeOrchestrator.generate_batch(
        node_id=node_id,
        grade=grade,
        count=count,
        difficulty_profile=difficulty_profile,
        interest_theme=student_interest,
        experience=experience,
        allowed_formatters=allowed_formatters,
        allowed_difficulties=allowed_difficulties,
        allowed_contexts=allowed_contexts,
    )
    return [p.model_dump() for p in problems]


def get_pipeline_status() -> Dict[str, Any]:
    """
    Return a health-check dict for the pipeline.

    Checks:
      - Whether each of the 27 DNA concept modules imports cleanly.
      - Count of formatters available per concept.
      - Total node IDs registered.
      - Available experience wrappers.

    Returns:
        {
            "total_nodes": int,
            "total_dna_concepts": int,
            "dna_status": {concept: {"ok": bool, "error": str|None,
                                     "formatter_count": int}},
            "formatters_available": int,
            "experiences_available": List[str],
            "healthy": bool,
        }
    """
    from .compatibility import COMPATIBILITY, get_formatters_for_dna

    dna_status: Dict[str, Dict] = {}
    all_ok = True

    for concept in sorted(_DNA_MODULE_MAP):
        try:
            _import_dna_module(concept)
            formatter_count = len(get_formatters_for_dna(concept))
            dna_status[concept] = {
                "ok": True,
                "error": None,
                "formatter_count": formatter_count,
            }
        except Exception as exc:
            dna_status[concept] = {
                "ok": False,
                "error": str(exc),
                "formatter_count": 0,
            }
            all_ok = False

    all_nodes = get_all_node_ids()
    total_formatters = len(set(
        fmt
        for fmts in COMPATIBILITY.values()
        for fmt in fmts
    ))

    experiences = ["standard", "mastery_drill", "hint_gated", "scaffolded"]

    return {
        "total_nodes": len(all_nodes),
        "total_dna_concepts": len(_DNA_MODULE_MAP),
        "dna_status": dna_status,
        "formatters_available": total_formatters,
        "experiences_available": experiences,
        "healthy": all_ok,
    }
