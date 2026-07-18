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
        is_student_path: bool = False,
        forced_dna: Optional[str] = None,
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

        primary_concept = forced_dna if (forced_dna and forced_dna in dna_names) else dna_names[0]

        # Vocabulary gating injection
        from backend.app.practice_gen.registry import _KG_NODES
        node_kg = _KG_NODES.get(node_id, {})
        not_yet_known = node_kg.get("NOT_YET_KNOWN", [])
        if "remainder" in not_yet_known and "remainder" not in local_difficulty_profile:
            local_difficulty_profile["remainder"] = "none"

        # Inject non-continuous variants from competency bounds
        # This ensures variants like 'operation'='add_subtract' are applied even in lab mode
        competency_bounds = get_node_competency_bounds(node_id, primary_concept)
        if not is_student_path and not is_lab and difficulty_profile:
            for k, v in difficulty_profile.items():
                if k in competency_bounds:
                    bound_val = competency_bounds[k]
                    if isinstance(bound_val, tuple) and len(bound_val) == 2:
                        continue  # Continuous bounds
                    # Discrete bounds check
                    if k == "regrouping":
                        if bound_val is False and v not in ("none", False):
                            raise ValueError(f"Boundary violation: requesting out-of-bounds discrete variant regrouping='{v}' on non-student path.")
                        if bound_val is True and v not in ("ones", True, "one_place"):
                            raise ValueError(f"Boundary violation: requesting out-of-bounds discrete variant regrouping='{v}' on non-student path.")
                    else:
                        if isinstance(bound_val, list):
                            if v not in bound_val:
                                raise ValueError(f"Boundary violation: requesting out-of-bounds discrete variant {k}='{v}' on non-student path.")
                        else:
                            if v != bound_val:
                                raise ValueError(f"Boundary violation: requesting out-of-bounds discrete variant {k}='{v}' on non-student path.")

        for k, v in competency_bounds.items():
            if not isinstance(v, tuple) and k not in local_difficulty_profile:
                local_difficulty_profile[k] = v

        # Single source of truth for normalizing scalars (0.0-1.0) into proper dimension values
        axes = get_axes_for_concept(primary_concept)
        for axis in axes:
            if axis.get("dim_type") == "continuous":
                axis_name = axis["name"]
                if axis_name not in local_difficulty_profile:
                    local_difficulty_profile[axis_name] = axis.get("default", 0.5)

        for axis in axes:
            if axis.get("dim_type") == "continuous" and axis["name"] in local_difficulty_profile:
                val = local_difficulty_profile[axis["name"]]
                if isinstance(val, (float, int)) and val <= 2.0:
                    if is_lab:
                        # For lab manual testing, use axis default bounds
                        min_val = axis.get("default_min", 1)
                        max_val = axis.get("default_max", 100)
                    else:
                        competency_bounds = get_node_competency_bounds(node_id, primary_concept)
                        bounds = competency_bounds.get(axis["name"])
                        if bounds:
                            min_val, max_val = bounds
                        else:
                            min_val = axis.get("default_min", 1)
                            max_val = axis.get("default_max", 100)
                    
                    scale_type = axis.get("scale", "linear")
                    # Calculate window ceiling t_hi if not number_difficulty
                    if axis["name"] != "number_difficulty":
                        divisions = axis.get("divisions", 5)
                        w = 1.0 / divisions
                        t_val = val * (1.0 - w) + w
                    else:
                        t_val = val

                    if scale_type == "logarithmic":
                        import math
                        shift = 1 if min_val == 0 else 0
                        log_min = math.log10(min_val + shift)
                        log_max = math.log10(max_val + shift)
                        log_val = log_min + t_val * (log_max - log_min)
                        mapped_val = int(math.pow(10, log_val)) - shift
                    else:
                        if isinstance(min_val, float) or isinstance(max_val, float) or (max_val - min_val <= 2):
                            mapped_val = round(min_val + t_val * (max_val - min_val), 2)
                        else:
                            mapped_val = int(min_val + t_val * (max_val - min_val))
                    local_difficulty_profile[axis["name"]] = mapped_val

        # Filter DNAs by requested formatter or allowed_formatters and variant compatibility
        from backend.app.practice_gen.compatibility import VARIANTS_BY_DNA, is_variant_supported, FORMATTER_NUMERIC_LIMITS
        node_max_value = max(
            (b[1] for b in competency_bounds.values()
             if isinstance(b, tuple) and len(b) == 2),
            default=0,
        )
        valid_dnas = []
        for d in dna_names:
            available_for_d = get_formatters_for_dna(d)
            # node_max_value comes from competency_bounds, which can be empty
            # for nodes relying purely on axis-scalar defaults (no explicit
            # per-node override) — that must not silently disable the numeric
            # filter (default=0 would let a >100 emoji_pictorial group through).
            # Fall back to this DNA's own param_bounds ceiling for the grade.
            d_max_value = node_max_value
            if d_max_value <= 0:
                import re as _re
                _grade_match = _re.search(r"mat_g(\d+)", node_id)
                _grade = int(_grade_match.group(1)) if _grade_match else 1
                d_bounds = _get_dna_instance(d).param_bounds.get(f"g{_grade}", {})
                d_max_value = max(
                    (b[1] for b in d_bounds.values() if isinstance(b, tuple) and len(b) == 2),
                    default=0,
                )
            # Filter by numeric limit
            available_for_d = [
                fmt for fmt in available_for_d
                if FORMATTER_NUMERIC_LIMITS.get(fmt, {}).get("max_val", float("inf")) >= d_max_value
            ]
            if formatter and formatter not in available_for_d:
                continue
            if allowed_formatters and not any(f in available_for_d for f in allowed_formatters):
                continue
            
            # Ensure the DNA is compatible with the requested variant profile
            dna_compatible = True
            if formatter:
                dim_names = {axis["name"] for axis in get_axes_for_concept(d)}
                for var_name, var_val in local_difficulty_profile.items():
                    if var_name in dim_names:
                        continue  # Skip difficulty dimensions
                    
                    # If this is a registered variant for the concept, check if it's supported
                    if var_name in VARIANTS_BY_DNA.get(d, {}):
                        if not is_variant_supported(d, formatter, var_name, var_val):
                            dna_compatible = False
                            break
                    else:
                        # DNA doesn't register this variant.
                        # For context, non-pure values require a word problem/story capability.
                        if var_name == "context" and var_val != "pure":
                            dna_compatible = False
                            break
            if not dna_compatible:
                continue

            valid_dnas.append(d)
            
        if forced_dna:
            if forced_dna not in valid_dnas:
                raise ValueError(f"Forced DNA '{forced_dna}' not compatible or supported for node '{node_id}'")
            valid_dnas = [forced_dna]
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

            # Feed the formatter's display ceiling to the DNA so it clamps its
            # generated magnitudes to what the formatter can actually render.
            # e.g. emoji_pictorial (max_val=100) cannot show a group of 744 —
            # the addition/subtraction DNAs already honor `formatter_max_val`
            # (they clamp max_result/max_minuend), but nothing was setting it,
            # so an emoji-served subtraction generated 3-digit minuends and the
            # formatter raised. Inject it from FORMATTER_NUMERIC_LIMITS.
            from backend.app.practice_gen.compatibility import FORMATTER_NUMERIC_LIMITS
            fmt_limit = FORMATTER_NUMERIC_LIMITS.get(formatter, {}).get("max_val")
            if fmt_limit is not None:
                local_difficulty_profile["formatter_max_val"] = fmt_limit

        # Parse grade level from node ID
        import re
        grade_match = re.search(r"mat_g(\d+)", node_id)
        effective_grade = int(grade_match.group(1)) if grade_match else 1

        ctx = generate_context(dna, node_id, effective_grade, seed, local_difficulty_profile, interest_theme, is_lab=is_lab, is_student_path=is_student_path)

        if formatter is None:
            available = get_formatters_for_dna(dna_name)
            # Same node_max_value=0 fallback as the candidate-DNA filter above:
            # an empty competency_bounds must not silently disable the numeric
            # filter and let e.g. emoji_pictorial through for a >100 value.
            picked_max_value = node_max_value
            if picked_max_value <= 0:
                picked_bounds = dna.param_bounds.get(f"g{effective_grade}", {})
                picked_max_value = max(
                    (b[1] for b in picked_bounds.values() if isinstance(b, tuple) and len(b) == 2),
                    default=0,
                )
            # Filter by numeric limit
            available = [
                fmt for fmt in available
                if FORMATTER_NUMERIC_LIMITS.get(fmt, {}).get("max_val", float("inf")) >= picked_max_value
            ]
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
        # support the 'ordering' formatter). See docs/testing_pipeline.md.
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
