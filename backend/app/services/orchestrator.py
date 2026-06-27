from typing import Any, Dict, List, Optional
import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.registry import get_node_dnas, get_node_competency_bounds
from backend.app.practice_gen.compatibility import (
    get_formatters_for_dna,
    get_compatible_formatters_for_variant,
)
from backend.app.practice_gen.axes_catalog import get_axes_for_concept
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
        allowed_difficulties: Optional[Dict[str, List[Any]]] = None,
        allowed_contexts: Optional[Dict[str, List[str]]] = None,
    ) -> FormattedProblem:
        if seed is None:
            seed = random.randint(10000, 99999)
        rng = random.Random(seed)
        
        # Merge allowed configs into a local difficulty_profile
        local_difficulty_profile = dict(difficulty_profile) if difficulty_profile else {}
        if allowed_difficulties:
            for dim, opts in allowed_difficulties.items():
                if opts and isinstance(opts, list) and len(opts) > 0:
                    local_difficulty_profile[dim] = rng.choice(opts)
        
        if allowed_contexts:
            for var_name, opts in allowed_contexts.items():
                if opts and isinstance(opts, list) and len(opts) > 0:
                    local_difficulty_profile[var_name] = rng.choice(opts)

        dna_names = get_node_dnas(node_id)
        if not dna_names:
            raise ValueError(f"No DNA mappings found for node_id '{node_id}'")
            
        primary_concept = dna_names[0]

        # Single source of truth for normalizing scalars (0.0-1.0) into proper dimension values
        axes = get_axes_for_concept(primary_concept)
        for axis in axes:
            if axis.get("dim_type") == "continuous" and axis["name"] in local_difficulty_profile:
                val = local_difficulty_profile[axis["name"]]
                if isinstance(val, (float, int)) and val <= 2.0:
                    competency_bounds = get_node_competency_bounds(node_id)
                    bounds = competency_bounds.get(axis["name"])
                    if bounds:
                        min_val, max_val = bounds
                    else:
                        min_val = axis.get("default_min", 1)
                        max_val = axis.get("default_max", 100)
                    
                    scale_type = axis.get("scale", "linear")
                    if scale_type == "logarithmic":
                        import math
                        shift = 1 if min_val == 0 else 0
                        log_min = math.log10(min_val + shift)
                        log_max = math.log10(max_val + shift)
                        log_val = log_min + val * (log_max - log_min)
                        mapped_val = int(math.pow(10, log_val)) - shift
                    else:
                        if isinstance(min_val, float) or isinstance(max_val, float) or (max_val - min_val <= 2):
                            mapped_val = round(min_val + val * (max_val - min_val), 2)
                        else:
                            mapped_val = int(min_val + val * (max_val - min_val))
                    local_difficulty_profile[axis["name"]] = mapped_val

        # Filter DNAs by requested formatter or allowed_formatters
        valid_dnas = []
        for d in dna_names:
            available_for_d = get_formatters_for_dna(d)
            if formatter and formatter not in available_for_d:
                continue
            if allowed_formatters and not any(f in available_for_d for f in allowed_formatters):
                continue
            valid_dnas.append(d)
            
        if not valid_dnas:
            # Fallback if filters are too strict
            valid_dnas = dna_names

        dna_name = rng.choice(valid_dnas)
        dna = _get_dna_instance(dna_name)

        ctx = generate_context(dna, node_id, grade, seed, local_difficulty_profile, interest_theme)

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
        allowed_formatters: Optional[List[str]] = None,
        allowed_difficulties: Optional[Dict[str, List[Any]]] = None,
        allowed_contexts: Optional[Dict[str, List[str]]] = None,
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
                if allowed_formatters and fmt not in allowed_formatters:
                    continue
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
                allowed_formatters=allowed_formatters,
                allowed_difficulties=allowed_difficulties,
                allowed_contexts=allowed_contexts,
            )
            problems.append(problem)

        return problems
