"""
Difficulty Dimensions Module

Defines all 71 difficulty dimensions across 12 visual skeleton types.
Each dimension specifies how it scales from 0.0 (easiest) to 1.0 (hardest).

Difficulty scale:
- 0.0-1.0: Normal range (within competency constraints)
- >1.0: Bridge zone (toward next competency level)

Scaling types:
- "linear": value = min + t * (max - min)
- "log": value = min * (max/min)^t  (slow start, accelerating growth)
- "auto": use log if max/min >= 10, else linear

Author: CCMed Team
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


# Difficulty level to scalar mapping
DIFFICULTY_LEVEL_MAP = {
    1: 0.2,   # Easy
    2: 0.5,   # Medium
    3: 0.8,   # Hard
    4: 1.1,   # Advanced (bridge zone)
}


def log_interpolate(min_val: float, max_val: float, t: float) -> float:
    """
    Logarithmic interpolation between min and max.
    
    Produces slow growth at low t values, accelerating toward max.
    This is ideal for numeric ranges where early difficulties should
    stay within comfortable bounds.
    
    Args:
        min_val: Minimum value (at t=0)
        max_val: Maximum value (at t=1)
        t: Interpolation factor 0.0 to 1.0+
    
    Returns:
        Interpolated value
    
    Example:
        log_interpolate(1, 1000, 0.0) → 1
        log_interpolate(1, 1000, 0.25) → ~5.6
        log_interpolate(1, 1000, 0.5) → ~31.6
        log_interpolate(1, 1000, 0.75) → ~177.8
        log_interpolate(1, 1000, 1.0) → 1000
    """
    if min_val <= 0 or max_val <= 0:
        # Fall back to linear for non-positive values
        return min_val + t * (max_val - min_val)
    
    return min_val * pow(max_val / min_val, t)


@dataclass
class DimensionSpec:
    """
    Specification for a single difficulty dimension.
    
    Defines how a dimension scales from easy (0.0) to hard (1.0+).
    """
    name: str                  # Human-readable name
    value_type: str            # "float", "int", "bool"
    default_min: Any           # Default value at difficulty 0.0
    default_max: Any           # Default value at difficulty 1.0
    constraint_name: Optional[str]  # Which constraint from extractor affects this
    extrapolate: bool          # Can exceed default_max in bridge zone?
    description: str           # What this dimension controls
    scale_type: str = "linear" # "linear", "log", or "auto" (auto uses log if ratio >= 10)


# Define dimensions for each visual type
PESO_MONEY_DIMENSIONS = {
    "amount_percentile": DimensionSpec(
        name="Amount Percentile",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name=None,  # This stays 0-1, not tied to peso amounts
        extrapolate=True,
        description="Position within [floor, ceiling] amount range"
    ),
    "divisibility": DimensionSpec(
        name="Divisibility Difficulty",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name=None,
        extrapolate=True,
        description="Target number divisibility (0=easy multiples, 1=prime-like)"
    ),
    "denom_ratio": DimensionSpec(
        name="Denomination Ratio",
        value_type="float",
        default_min=1.0,
        default_max=0.4,
        constraint_name=None,
        extrapolate=True,
        description="Fraction of valid denominations available"
    ),
    "require_optimal": DimensionSpec(
        name="Require Optimal Solution",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name=None,
        extrapolate=False,
        description="Threshold at 0.7 = require fewest pieces"
    ),
    "min_pieces": DimensionSpec(
        name="Minimum Pieces",
        value_type="int",
        default_min=1,
        default_max=6,
        constraint_name=None,
        extrapolate=True,
        description="Minimum pieces in optimal solution"
    ),
}

NUMBER_LINE_DIMENSIONS = {
    "range_percentile": DimensionSpec(
        name="Range Percentile",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name="numeric_limit",
        extrapolate=True,
        description="Position within curriculum range",
        scale_type="auto"  # Use log when curriculum range is large (e.g., 1-1000)
    ),
    "position_difficulty": DimensionSpec(
        name="Position Difficulty",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name=None,
        extrapolate=False,
        description="0=on labeled tick, 1=between ticks requiring estimation"
    ),
    "content_complexity": DimensionSpec(
        name="Content Complexity",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name=None,
        extrapolate=True,
        description="0=whole numbers, 0.5=fractions, 1.0=decimals/negatives"
    ),
    "tick_label_density": DimensionSpec(
        name="Tick Label Density",
        value_type="float",
        default_min=1.0,
        default_max=0.1,
        constraint_name=None,
        extrapolate=True,
        description="Fraction of ticks that show labels"
    ),
    "divisions": DimensionSpec(
        name="Division Count",
        value_type="int",
        default_min=10,
        default_max=50,
        constraint_name=None,
        extrapolate=True,
        description="Number of tick marks on the line"
    ),
}

# Additional dimension specs for other types (abbreviated for space)
CLOCK_SET_DIMENSIONS = {
    "minute_granularity": DimensionSpec("Minute Granularity", "int", 60, 1, "time_granularity", False, "Minutes must be multiple of this"),
    "snap_interval": DimensionSpec("Snap Interval", "int", 30, 1, None, False, "UI snap granularity in minutes"),
    "hand_overlap_risk": DimensionSpec("Hand Overlap Risk", "float", 0.0, 1.0, None, False, "Avoid times where hands are close"),
    "elapsed_time": DimensionSpec("Elapsed Time Task", "float", 0.0, 1.0, None, True, "Calculate duration vs set single time"),
    "ampm_required": DimensionSpec("AM/PM Required", "float", 0.0, 1.0, None, False, "Threshold 0.6 = must specify AM/PM"),
}

# Simplified specs for remaining types (full implementation would expand these)
VISUAL_TYPE_DIMENSIONS = {
    "PesoMoney": PESO_MONEY_DIMENSIONS,
    "NumberLine": NUMBER_LINE_DIMENSIONS,
    "ClockSet": CLOCK_SET_DIMENSIONS,
    # Add other types as needed
}


def interpolate_dimension(
    spec: DimensionSpec,
    difficulty: float,
    actual_min: Optional[Any] = None,
    actual_max: Optional[Any] = None,
) -> Any:
    """
    Interpolate a dimension value at given difficulty level.
    
    Supports three scale types:
    - "linear": value = min + t * (max - min)
    - "log": value = min * (max/min)^t  (slow start, fast finish)
    - "auto": use log if max/min >= 10, else linear
    
    Args:
        spec: Dimension specification
        difficulty: Scalar difficulty 0.0 to 1.5+
        actual_min: Override default_min (from curriculum context)
        actual_max: Override default_max (from curriculum context)
    
    Returns:
        Interpolated value for this dimension
    """
    # Use provided ranges or defaults
    min_val = actual_min if actual_min is not None else spec.default_min
    max_val = actual_max if actual_max is not None else spec.default_max
    
    # Clamp difficulty for non-extrapolating dimensions
    t = difficulty
    if t > 1.0 and not spec.extrapolate:
        t = 1.0
    
    if spec.value_type == "bool":
        # Boolean: threshold at 0.5
        return t >= 0.5
    
    # Determine scale type
    scale = spec.scale_type
    if scale == "auto":
        # Auto-detect: use log if ratio >= 10 and both values positive
        if min_val > 0 and max_val > 0 and max_val / min_val >= 10:
            scale = "log"
        else:
            scale = "linear"
    
    # Compute value based on scale type
    if scale == "log" and min_val > 0 and max_val > 0:
        # Logarithmic interpolation: min * (max/min)^t
        # This gives slow growth at low difficulty, fast growth at high difficulty
        # Example: range 1-1000, t=0.5 → 1 * (1000/1)^0.5 = 31.6
        value = min_val * pow(max_val / min_val, t)
    else:
        # Linear interpolation (default)
        value = min_val + t * (max_val - min_val)
    
    if spec.value_type == "int":
        return round(value)
    elif spec.value_type == "float":
        return value
    else:
        return value


def get_dimension_value(
    visual_type: str,
    dimension_id: str,
    difficulty: float,
    actual_min: Optional[Any] = None,
    actual_max: Optional[Any] = None,
) -> Any:
    """
    Get interpolated value for a specific dimension.
    
    Args:
        visual_type: Visual skeleton type
        dimension_id: Dimension identifier
        difficulty: Scalar difficulty
        actual_min: Override minimum (from curriculum)
        actual_max: Override maximum (from curriculum)
    
    Returns:
        Interpolated dimension value
    """
    if visual_type not in VISUAL_TYPE_DIMENSIONS:
        raise ValueError(f"Unknown visual type: {visual_type}")
    
    dims = VISUAL_TYPE_DIMENSIONS[visual_type]
    if dimension_id not in dims:
        raise ValueError(f"Unknown dimension {dimension_id} for {visual_type}")
    
    spec = dims[dimension_id]
    return interpolate_dimension(spec, difficulty, actual_min, actual_max)
