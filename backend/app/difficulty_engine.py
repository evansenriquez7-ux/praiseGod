"""
Difficulty Engine Module

SCALAR DIFFICULTY SYSTEM - Curriculum-driven dimension interpolation.

Orchestrates the scalar difficulty system by:
1. Converting difficulty level (1-4) to scalar (0.0-1.5)
2. Computing dimension ranges from curriculum context
3. Interpolating all dimensions independently
4. Selecting numbers by divisibility difficulty

Author: CCMed Team
"""

import random
from typing import Dict, List, Tuple, Optional, Any
from .difficulty_dimensions import (
    DIFFICULTY_LEVEL_MAP, 
    VISUAL_TYPE_DIMENSIONS,
    interpolate_dimension,
    get_dimension_value
)
from .dimension_ranges import compute_dimension_ranges, compute_all_dimension_ranges
from .divisibility import divisibility_difficulty, select_number_by_divisibility
from .constraint_extractor import extract_constraints


def normalize_difficulty(difficulty: Any) -> float:
    """
    Normalize difficulty input to scalar float.
    
    Accepts:
    - int (1-4) → maps to 0.2, 0.5, 0.8, 1.1
    - float (0.0-1.5+) → used directly
    - str ("easy", "medium", "hard") → maps to int then float
    
    Returns:
        Scalar difficulty as float
    """
    if isinstance(difficulty, (int, float)):
        if difficulty in [1, 2, 3, 4]:
            return DIFFICULTY_LEVEL_MAP[difficulty]
        else:
            return float(difficulty)
    
    elif isinstance(difficulty, str):
        # Legacy string support
        mapping = {"easy": 1, "medium": 2, "hard": 3, "advanced": 4}
        level = mapping.get(difficulty.lower(), 2)
        return DIFFICULTY_LEVEL_MAP[level]
    
    # Default to medium
    return 0.5


def get_scalar_difficulty(difficulty_level: Any) -> float:
    """
    Convert any difficulty format to scalar 0.0-1.5+.
    
    Args:
        difficulty_level: 1-4, float, or string name
    
    Returns:
        Scalar difficulty
    """
    return normalize_difficulty(difficulty_level)


def compute_dimension_context(
    context: Dict,
    visual_type: str,
    difficulty: float,
) -> Dict[str, Any]:
    """
    Compute interpolated values for all dimensions of a visual type.
    
    Args:
        context: Curriculum context from curriculum_context.py
        visual_type: Visual skeleton type (e.g., "PesoMoney")
        difficulty: Scalar difficulty 0.0-1.5+
    
    Returns:
        Dict of dimension_id -> interpolated value
    """
    if visual_type not in VISUAL_TYPE_DIMENSIONS:
        return {}
    
    dimension_specs = VISUAL_TYPE_DIMENSIONS[visual_type]
    result = {}
    
    # Get curriculum context
    competency_text = context.get("competency", {}).get("text", "")
    prev_node = context.get("prev_node")
    next_node = context.get("next_node")
    grade = context.get("grade", 5)
    
    # Compute ranges for each dimension
    for dim_id, spec in dimension_specs.items():
        if spec.constraint_name:
            # Dimension has curriculum-driven constraint
            dim_range = compute_dimension_ranges(
                competency_text,
                prev_node,
                next_node,
                grade,
                spec.constraint_name
            )
            
            # Interpolate based on difficulty
            curr_difficulty = difficulty
            if difficulty <= 1.0:
                # Normal range: interpolate between floor and ceiling
                min_val = dim_range.floor
                max_val = dim_range.ceiling
            else:
                # Bridge zone: interpolate between ceiling and bridge_target
                t_bridge = difficulty - 1.0  # 0.0 to 0.5+
                min_val = dim_range.ceiling
                max_val = dim_range.bridge_target
                # Remap difficulty to [0, 1] for this segment
                curr_difficulty = min(t_bridge / 0.5, 1.0)
            
            result[dim_id] = interpolate_dimension(spec, curr_difficulty, min_val, max_val)
        else:
            # Dimension uses default range
            result[dim_id] = interpolate_dimension(spec, difficulty)
    
    return result


# ========== LEGACY COMPATIBILITY FUNCTIONS ==========
# These maintain backward compatibility with existing generators


def compute_difficulty_windows(context: Dict, difficulty_level: int) -> Tuple[int, int]:
    """
    LEGACY: Compute the amount range (min, max) for a specific difficulty level.
    
    Kept for backward compatibility. New code should use compute_dimension_context().
    
    Args:
        context: Curriculum context from curriculum_context.py
        difficulty_level: 1 (easy), 2 (medium), 3 (hard), 4 (advanced)
    
    Returns:
        (min_amount, max_amount) tuple
    """
    # Convert to scalar
    difficulty = normalize_difficulty(difficulty_level)
    
    # Get competency info
    competency_text = context.get("competency", {}).get("text", "")
    prev_node = context.get("prev_node")
    next_node = context.get("next_node")
    grade = context.get("grade", 5)
    
    # Compute range for numeric_limit dimension
    dim_range = compute_dimension_ranges(
        competency_text,
        prev_node,
        next_node,
        grade,
        "numeric_limit"
    )
    
    # Map difficulty to range
    if difficulty <= 0.25:
        # Lower quartile
        return (int(dim_range.floor), int(dim_range.floor + (dim_range.ceiling - dim_range.floor) * 0.25))
    elif difficulty <= 0.75:
        # Middle range
        return (int(dim_range.floor + (dim_range.ceiling - dim_range.floor) * 0.25),
                int(dim_range.floor + (dim_range.ceiling - dim_range.floor) * 0.75))
    elif difficulty <= 1.0:
        # Upper quartile
        return (int(dim_range.floor + (dim_range.ceiling - dim_range.floor) * 0.75), 
                int(dim_range.ceiling))
    else:
        # Bridge zone
        return (int(dim_range.ceiling), int(dim_range.bridge_target))


def select_target_amount(window: Tuple[int, int], difficulty_level: int, rng: random.Random) -> int:
    """
    LEGACY: Select a target amount within the window, respecting divisibility rules.
    
    Kept for backward compatibility. New code should use select_number_by_divisibility().
    
    Args:
        window: (min, max) range
        difficulty_level: 1 (easy), 2 (medium), 3 (hard), 4 (advanced)
        rng: Random number generator
    
    Returns:
        Selected target amount
    """
    min_val, max_val = window
    difficulty = normalize_difficulty(difficulty_level)
    
    # Use new divisibility system
    return select_number_by_divisibility(min_val, max_val, difficulty, rng)


def select_denominations(context: Dict, difficulty_level: int, rng: random.Random) -> List[int]:
    """
    Select which denominations are available for this problem.
    
    Rules:
    1. Never exceed explicit limit (if ₱100 limit, no ₱200 bills)
    2. Always include ₱1 to ensure any amount is reachable
    3. Randomize subset for variety (remove 0-2 denominations)
    4. Respect "exclude centavos" constraint (already no centavos in default list)
    
    Args:
        context: Curriculum context
        difficulty_level: 1-4
        rng: Random number generator
    
    Returns:
        List of available denominations
    """
    # All standard Philippine denominations (excluding centavos)
    all_denoms = [1, 5, 10, 20, 50, 100, 200, 500, 1000]
    
    # Get the limit (explicit or traditional default)
    limit = context.get("explicit_limit")
    if limit is None:
        limit = context.get("traditional_defaults", {}).get("max_amount", 1000)
    
    # Filter to denominations ≤ limit
    valid = [d for d in all_denoms if d <= limit]
    
    if not valid:
        return [1]  # Fallback to just ₱1
    
    # For easy difficulty, sometimes remove larger denominations to encourage thinking
    difficulty = normalize_difficulty(difficulty_level)
    if difficulty < 0.3:
        # Easy: sometimes limit to smaller bills to force more pieces
        typical_target_max = int(limit * 0.3)
        # Remove denominations > typical target
        restricted = [d for d in valid if d <= typical_target_max]
        # But always keep at least ₱1 and one larger denomination
        if len(restricted) < 2:
            restricted = valid[:3] if len(valid) >= 3 else valid
        valid = restricted
    
    # Randomize: 30% chance to remove 1-2 denominations for variety
    # But ALWAYS keep ₱1 (for reachability)
    if len(valid) > 3 and rng.random() < 0.3:
        removable = [d for d in valid if d != 1 and d != max(valid)]
        if removable:
            num_to_remove = rng.choice([1, 2]) if len(removable) > 2 else 1
            for _ in range(num_to_remove):
                if removable:
                    to_remove = rng.choice(removable)
                    valid = [d for d in valid if d != to_remove]
                    removable = [d for d in removable if d != to_remove]
    
    return sorted(valid)


def get_difficulty_name(level: int) -> str:
    """Convert difficulty level (1-4) to name."""
    names = {1: "easy", 2: "medium", 3: "hard", 4: "advanced"}
    return names.get(level, "medium")


def get_difficulty_level(name: str) -> int:
    """Convert difficulty name to level (1-4)."""
    mapping = {"easy": 1, "medium": 2, "hard": 3, "advanced": 4}
    return mapping.get(name.lower(), 2)
