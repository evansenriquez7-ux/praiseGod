from typing import Any, Dict, List, Optional
import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.registry import get_node_dnas, get_node_competency_bounds
from backend.app.practice_gen.compatibility import (
    get_formatters_for_dna,
    get_compatible_formatters_for_variant,
    get_grade_gated_variants,
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
        seed: Optional[int] = None,
        difficulty_profile: Optional[Dict[str, Any]] = None,
        interest_theme: Optional[str] = None,
        formatter: Optional[str] = None,
        experience: str = "standard",
        experience_config: Optional[Dict] = None,
        allowed_formatters: Optional[List[str]] = None,
        allowed_difficulties: Optional[Dict[str, List[Any]]] = None,
        allowed_contexts: Optional[Dict[str, List[str]]] = None,
        is_lab: bool = False,
    ) -> FormattedProblem:
        if seed is None:
            seed = random.randint(10000, 99999)
        rng = random.Random(seed)
        
        # Merge allowed configs into a local difficulty_profile
        local_difficulty_profile = dict(difficulty_profile) if difficulty_profile else {}
        
        # If the UI sends multi-select variants as a list, pick one randomly for this generation
        keys_to_remove = []
        for k, v in local_difficulty_profile.items():
            if isinstance(v, str):
                v = v.strip()
                if v.startswith("[") and v.endswith("]"):
                    import ast
                    try:
                        v = ast.literal_eval(v)
                    except Exception:
                        pass
                elif "," in v:
                    v = [opt.strip() for opt in v.split(",") if opt.strip()]
            
            if isinstance(v, list) and len(v) > 0:
                local_difficulty_profile[k] = rng.choice(v)
            elif v in ("", "any", "random", None):
                keys_to_remove.append(k)
                
        for k in keys_to_remove:
            del local_difficulty_profile[k]

        if allowed_difficulties:
            for dim, opts in allowed_difficulties.items():
                if opts and isinstance(opts, list) and len(opts) > 0 and dim not in local_difficulty_profile:
                    local_difficulty_profile[dim] = rng.choice(opts)
        
        if allowed_contexts:
            for var_name, opts in allowed_contexts.items():
                if opts and isinstance(opts, list) and len(opts) > 0:
                    local_difficulty_profile[var_name] = rng.choice(opts)

        dna_names = get_node_dnas(node_id)
        if not dna_names:
            raise ValueError(f"No DNA mappings found for node_id '{node_id}'")

        primary_concept = dna_names[0]

        # Extract grade and quarter from node_id for vocabulary gating
        import re
        match = re.match(r"mat_g(\d+)_[a-z]+_q(\d+)_\d+", node_id)
        grade, quarter = None, None
        if match:
            grade, quarter = int(match.group(1)), int(match.group(2))

        # Apply grade-based variant gating (vocabulary gating per pgen_checklist)
        if grade and quarter and not is_lab:
            gated_variants = get_grade_gated_variants(primary_concept, grade, quarter)
            # Filter local_difficulty_profile to only include allowed variant values
            keys_to_remove = []
            for var_name, var_value in local_difficulty_profile.items():
                if var_name in gated_variants:
                    if var_value not in gated_variants[var_name]:
                        # This variant value is gated - remove it to allow fallback
                        keys_to_remove.append(var_name)
            for k in keys_to_remove:
                del local_difficulty_profile[k]

        # Inject non-continuous variants from competency bounds
        # This ensures variants like 'operation'='add_subtract' are applied even in lab mode
        competency_bounds = get_node_competency_bounds(node_id)
        for k, v in competency_bounds.items():
            if not isinstance(v, tuple) and k not in local_difficulty_profile:
                local_difficulty_profile[k] = v

        # Single source of truth for normalizing scalars (0.0-1.0) into proper dimension values
        axes = get_axes_for_concept(primary_concept)
        for axis in axes:
            if axis.get("dim_type") == "continuous" and axis["name"] in local_difficulty_profile:
                val = local_difficulty_profile[axis["name"]]
                if isinstance(val, (float, int)) and val <= 2.0:
                    if is_lab:
                        # For lab manual testing, use axis default bounds
                        min_val = axis.get("default_min", 1)
                        max_val = axis.get("default_max", 100)
                    else:
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
            raise ValueError(f"Formatter '{formatter}' is not supported by any DNA for node '{node_id}'")

        dna_name = rng.choice(valid_dnas)
        dna = _get_dna_instance(dna_name)

        if not formatter and allowed_formatters and len(allowed_formatters) == 1:
            formatter = allowed_formatters[0]

        if formatter:
            from backend.app.practice_gen.compatibility import FORMATTER_VARIANT_SUPPORT
            if dna_name in FORMATTER_VARIANT_SUPPORT and formatter in FORMATTER_VARIANT_SUPPORT[dna_name]:
                caps = FORMATTER_VARIANT_SUPPORT[dna_name][formatter]
                for variant_name, allowed_vals in caps.items():
                    if variant_name not in local_difficulty_profile and allowed_vals:
                        local_difficulty_profile[variant_name] = rng.choice(allowed_vals)

        # Parse grade level from node ID
        import re
        grade_match = re.search(r"mat_g(\d+)", node_id)
        effective_grade = int(grade_match.group(1)) if grade_match else 1

        ctx = generate_context(dna, node_id, effective_grade, seed, local_difficulty_profile, interest_theme, is_lab=is_lab)

        if formatter is None:
            available = get_formatters_for_dna(dna_name)
            from backend.app.practice_gen.compatibility import FORMATTER_VARIANT_SUPPORT
            caps = FORMATTER_VARIANT_SUPPORT.get(dna_name, {})
            filtered_available = []
            for fmt in available:
                fmt_caps = caps.get(fmt, {})
                compatible = True
                for variant_name, allowed_vals in fmt_caps.items():
                    ctx_val = ctx.values.get(variant_name)
                    if ctx_val and allowed_vals and ctx_val not in allowed_vals:
                        compatible = False
                        break
                if compatible:
                    filtered_available.append(fmt)
            available = filtered_available
            
            if allowed_formatters:
                available = [fmt for fmt in available if fmt in allowed_formatters]
            if not available:
                raise ValueError(f"No compatible formatters available for DNA '{dna_name}'")
            formatter = _weighted_choice(rng, available)

        problem = apply_formatter(ctx, formatter, rng)
        # Annotate the problem with the DNA concept that was actually chosen.
        # Without this, the auditor cannot do per-DNA content checks (it would
        # fall back to the first DNA in the node's list, which is not
        # necessarily the one the orchestrator picked). This was the root
        # cause of the v-final "Fractions DNA concept overridden" violations:
        # the audit thought 'fractions' was picked, but the orchestrator
        # actually picked 'comparing_ordering' (because 'fractions' doesn't
        # support the 'ordering' formatter). See Phase 4 in
        # generator_testing_strategy.md.
        try:
            problem.dna_name = dna_name
        except Exception:
            # Some FormattedProblem subclasses may not allow attribute
            # assignment; fall back silently. The audit's check still works
            # via the orchestrator's run-time filter, just less precisely.
            pass
        return apply_experience(problem, experience, experience_config)

    @staticmethod
    def generate_batch(
        node_id: str,
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
            raise ValueError(f"No valid formatters found for node '{node_id}' across any of its DNAs")

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
