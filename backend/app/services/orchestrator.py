from typing import Any, Dict, List, Optional
import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.registry import get_node_dnas
from backend.app.practice_gen.compatibility import (
    get_formatters_for_dna,
    get_compatible_formatters_for_variant,
)
from backend.app.practice_gen.adapter import _get_dna_instance, _weighted_choice, apply_formatter, apply_experience
from backend.app.practice_gen.generators.base_generator import generate_context

class PracticeOrchestrator:
    """
    Bridge Layer separating the generation logic from the FastAPI routing/server layer.
    Replaces direct `pipeline.run` and `adapter.py` top-level functions to handle
    dependency injection and state management context wrapping.
    """
    
    @staticmethod
    def generate_problem(
        node_id: str,
        grade: int,
        seed: Optional[int] = None,
        difficulty_profile: Optional[Dict[str, Any]] = None,
        interest_theme: Optional[str] = None,
        formatter: Optional[str] = None,
        experience: str = "standard",
        experience_config: Optional[Dict] = None,
        allowed_formatters: Optional[List[str]] = None,
    ) -> FormattedProblem:
        if seed is None:
            seed = random.randint(10000, 99999)
        rng = random.Random(seed)

        dna_names = get_node_dnas(node_id)
        if not dna_names:
            raise ValueError(f"No DNA mappings found for node_id '{node_id}'")

        dna_name = rng.choice(dna_names)
        dna = _get_dna_instance(dna_name)

        ctx = generate_context(dna, node_id, grade, seed, difficulty_profile, interest_theme)

        if formatter is None:
            available = get_formatters_for_dna(dna_name)
            task_type = ctx.values.get("task_type")
            if task_type:
                compatible = get_compatible_formatters_for_variant(dna_name, "task_type", task_type)
                if compatible:
                    available = [fmt for fmt in available if fmt in compatible]
            if allowed_formatters:
                available = [fmt for fmt in available if fmt in allowed_formatters]
            if not available:
                available = ["mcq"]
            formatter = _weighted_choice(rng, available)

        problem = apply_formatter(ctx, formatter, rng)
        return apply_experience(problem, experience, experience_config)

    @staticmethod
    def generate_batch(
        node_id: str,
        grade: int,
        count: int = 5,
        difficulty_profile: Optional[Dict[str, Any]] = None,
        interest_theme: Optional[str] = None,
        experience: str = "standard",
    ) -> List[FormattedProblem]:
        base_seed = random.randint(10000, 99999)
        batch_rng = random.Random(base_seed)

        dna_names = get_node_dnas(node_id)
        if not dna_names:
            raise ValueError(f"No DNA mappings found for node_id '{node_id}'")

        available_formatters: List[str] = []
        seen: set = set()
        for dna_name in dna_names:
            for fmt in get_formatters_for_dna(dna_name):
                if fmt not in seen:
                    seen.add(fmt)
                    available_formatters.append(fmt)
        if not available_formatters:
            available_formatters = ["mcq"]

        problems: List[FormattedProblem] = []
        last_formatter: Optional[str] = None

        for i in range(count):
            seed = base_seed + i
            candidates = [f for f in available_formatters if f != last_formatter]
            if not candidates:
                candidates = available_formatters
            formatter = _weighted_choice(batch_rng, candidates)
            last_formatter = formatter

            problem = PracticeOrchestrator.generate_problem(
                node_id=node_id,
                grade=grade,
                seed=seed,
                difficulty_profile=difficulty_profile,
                interest_theme=interest_theme,
                formatter=formatter,
                experience=experience,
            )
            problems.append(problem)

        return problems
