"""
Dimension Ranges Module

Computes dimension ranges (floor, ceiling, bridge) from curriculum context
and neighboring nodes. This enables curriculum-driven difficulty scaling.

Author: CCMed Team
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any
from .constraint_extractor import extract_constraints
from .skill_matcher import are_skills_related


# Grade-based traditional defaults (fallback when no explicit constraints)
GRADE_DEFAULTS = {
    1: {"min": 1, "max": 100},
    2: {"min": 1, "max": 1000},
    3: {"min": 1, "max": 10000},
    4: {"min": 1, "max": 1000000},
    5: {"min": 1, "max": 1000000},
    6: {"min": 1, "max": 1000000},
    7: {"min": 1, "max": 1000000},
    8: {"min": 1, "max": 1000000},
    9: {"min": 1, "max": 1000000},
    10: {"min": 1, "max": 1000000},
}


@dataclass
class DimensionRange:
    """
    Computed range for a dimension based on curriculum context.
    
    Defines floor, ceiling, and bridge target for interpolation.
    """
    dimension_id: str
    floor: float           # Minimum value (from prev node or grade default)
    ceiling: float         # Maximum value (from current node constraint)
    bridge_target: float   # Target for difficulty > 1.0 (from next node)
    constraint_source: str # "explicit", "neighbor", "default"


def are_competencies_related(
    text_a: str,
    text_b: str,
    visual_type_a: Optional[str] = None,
    visual_type_b: Optional[str] = None,
) -> bool:
    """
    Check if two competencies are teaching related skills.
    
    Two competencies are related if BOTH:
    1. They map to the same visual type (if provided)
    2. They share skill keywords
    
    Args:
        text_a: First competency text
        text_b: Second competency text
        visual_type_a: Visual type for first competency (optional)
        visual_type_b: Visual type for second competency (optional)
    
    Returns:
        True if both conditions met
    """
    # Condition 1: Same visual type (if provided)
    if visual_type_a is not None and visual_type_b is not None:
        if visual_type_a != visual_type_b:
            return False
    
    # Condition 2: Same skill keywords
    return are_skills_related(text_a, text_b)


def compute_dimension_ranges(
    competency_text: str,
    prev_node: Optional[Dict],
    next_node: Optional[Dict],
    grade: int,
    constraint_name: str,
) -> DimensionRange:
    """
    Compute floor, ceiling, and bridge for a dimension.
    
    Args:
        competency_text: Current competency text
        prev_node: Previous node dict with 'text', 'limit', etc.
        next_node: Next node dict with 'text', 'limit', etc.
        grade: Current grade level
        constraint_name: Which constraint to extract (e.g., 'numeric_limit')
    
    Returns:
        DimensionRange with computed floor/ceiling/bridge
    """
    # Extract constraints from current competency
    current_constraints = extract_constraints(competency_text)
    
    # Get current ceiling
    if constraint_name in current_constraints:
        ceiling = float(current_constraints[constraint_name])
        constraint_source = "explicit"
    else:
        # No explicit constraint - use grade default
        ceiling = float(GRADE_DEFAULTS.get(grade, GRADE_DEFAULTS[5])["max"])
        constraint_source = "default"
    
    # Compute FLOOR
    floor = None
    
    if prev_node:
        prev_text = prev_node.get("text", "")
        
        # Only use prev constraint if competencies are related
        if are_competencies_related(prev_text, competency_text):
            prev_constraints = extract_constraints(prev_text)
            
            if constraint_name in prev_constraints:
                prev_limit = float(prev_constraints[constraint_name])
                
                # Use prev_limit as floor if it's less than current ceiling
                if prev_limit < ceiling:
                    floor = prev_limit
                    constraint_source = "neighbor"
    
    # Fallback to grade default if no valid prev found
    if floor is None:
        floor = float(GRADE_DEFAULTS.get(grade, GRADE_DEFAULTS[5])["min"])
        if floor >= ceiling:
            floor = max(1.0, ceiling * 0.1)  # 10% of ceiling
    
    # Compute BRIDGE TARGET
    bridge = None
    
    if next_node:
        next_text = next_node.get("text", "")
        
        # Only use next constraint if competencies are related
        if are_competencies_related(competency_text, next_text):
            next_constraints = extract_constraints(next_text)
            
            if constraint_name in next_constraints:
                next_limit = float(next_constraints[constraint_name])
                
                # Use next_limit as bridge if significantly higher
                if next_limit > ceiling * 1.2:
                    bridge = next_limit
    
    # Fallback to 50% extrapolation if no valid next found
    if bridge is None:
        bridge = ceiling * 1.5
    
    return DimensionRange(
        dimension_id=constraint_name,
        floor=floor,
        ceiling=ceiling,
        bridge_target=bridge,
        constraint_source=constraint_source
    )


def compute_all_dimension_ranges(
    competency_text: str,
    prev_node: Optional[Dict],
    next_node: Optional[Dict],
    grade: int,
    constraint_names: list,
) -> Dict[str, DimensionRange]:
    """
    Compute ranges for all applicable dimensions.
    
    Args:
        competency_text: Current competency
        prev_node: Previous neighboring node
        next_node: Next neighboring node
        grade: Grade level
        constraint_names: List of constraint names to compute
    
    Returns:
        Dict mapping constraint_name -> DimensionRange
    """
    ranges = {}
    
    for constraint_name in constraint_names:
        ranges[constraint_name] = compute_dimension_ranges(
            competency_text,
            prev_node,
            next_node,
            grade,
            constraint_name
        )
    
    return ranges
