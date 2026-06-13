"""
MATATAG MCQ Difficulty Dimensions Module

Defines difficulty dimensions for all MATATAG MCQ generator types.
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
from typing import Any, Dict, Optional, List


# Difficulty level to scalar mapping (same as visual_skeletons)
DIFFICULTY_LEVEL_MAP = {
    1: 0.2,   # Easy
    2: 0.5,   # Medium
    3: 0.8,   # Hard
    4: 1.1,   # Advanced (bridge zone)
}


@dataclass
class DimensionSpec:
    """
    Specification for a single difficulty dimension.
    """
    name: str                       # Human-readable name
    value_type: str                 # "float", "int", "bool", "choice"
    default_min: Any                # Default value at difficulty 0.0
    default_max: Any                # Default value at difficulty 1.0
    constraint_name: Optional[str]  # Which constraint from extractor affects this
    extrapolate: bool               # Can exceed default_max in bridge zone?
    description: str                # What this dimension controls
    scale_type: str = "linear"      # "linear", "log", or "auto"
    choices: Optional[List] = None  # For "choice" type - list of options


# ═══════════════════════════════════════════════════════════════════════════════
# COUNTING DIMENSIONS (Grades 1-3)
# Competencies: count up to N, count by 2s/5s/10s, 1 more/1 less, ordinal numbers
# ═══════════════════════════════════════════════════════════════════════════════

COUNTING_DIMENSIONS = {
    "max_number": DimensionSpec(
        name="Maximum Number",
        value_type="int",
        default_min=10,
        default_max=1000,
        constraint_name="numeric_limit",
        extrapolate=True,
        description="Upper bound of counting range",
        scale_type="log"
    ),
    "skip_interval": DimensionSpec(
        name="Skip Count Interval",
        value_type="choice",
        default_min=0,  # Index into choices at easy
        default_max=4,  # Index into choices at hard
        constraint_name=None,
        extrapolate=False,
        description="Counting by 1s, 2s, 5s, 10s, etc.",
        choices=[1, 2, 5, 10, 20, 50, 100]
    ),
    "direction_complexity": DimensionSpec(
        name="Direction Complexity",
        value_type="float",
        default_min=0.0,   # Always forward
        default_max=1.0,   # May include backward
        constraint_name=None,
        extrapolate=False,
        description="Probability of backward counting (threshold 0.6)"
    ),
    "ordinal_max": DimensionSpec(
        name="Maximum Ordinal",
        value_type="int",
        default_min=10,
        default_max=100,
        constraint_name="ordinal_limit",
        extrapolate=True,
        description="Highest ordinal position (10th, 20th, 100th)"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# PLACE VALUE DIMENSIONS (Grades 1-6)
# Competencies: place value, value of digit, expanded form, read/write numerals
# ═══════════════════════════════════════════════════════════════════════════════

PLACE_VALUE_DIMENSIONS = {
    "max_number": DimensionSpec(
        name="Maximum Number",
        value_type="int",
        default_min=20,
        default_max=10000,
        constraint_name="numeric_limit",
        extrapolate=False,
        description="Upper bound on generated numbers (derived from competency text)",
        scale_type="log"
    ),
    "digit_count": DimensionSpec(
        name="Digit Count",
        value_type="int",
        default_min=2,
        default_max=6,
        constraint_name="digit_count",
        extrapolate=False,
        description="Number of digits in the number (capped by max_number)"
    ),
    "target_place": DimensionSpec(
        name="Target Place Index",
        value_type="int",
        default_min=0,        # Ones place
        default_max=5,        # Hundred thousands place
        constraint_name=None,
        extrapolate=False,
        description="Which place value to focus on (0=ones, 1=tens, etc.)"
    ),
    "include_zeros": DimensionSpec(
        name="Include Internal Zeros",
        value_type="float",
        default_min=0.0,
        default_max=0.8,
        constraint_name=None,
        extrapolate=False,
        description="Probability of zeros in middle positions"
    ),
    "question_type": DimensionSpec(
        name="Question Type",
        value_type="float",
        default_min=0.0,      # Digit identification
        default_max=1.0,      # Expanded form
        constraint_name=None,
        extrapolate=False,
        description="0=find digit, 0.5=find value, 1.0=expanded form"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# ARITHMETIC DIMENSIONS (Grades 1-6)
# Competencies: add, subtract, multiply, divide (with/without regrouping)
# ═══════════════════════════════════════════════════════════════════════════════

ARITHMETIC_DIMENSIONS = {
    "operand_max": DimensionSpec(
        name="Operand Maximum",
        value_type="int",
        default_min=10,
        default_max=10000,
        constraint_name="numeric_limit",
        extrapolate=True,
        description="Maximum value of operands",
        scale_type="log"
    ),
    "operand_digit_count": DimensionSpec(
        name="Operand Digit Count",
        value_type="int",
        default_min=1,
        default_max=4,
        constraint_name="digit_count",
        extrapolate=True,
        description="Number of digits per operand"
    ),
    "regrouping_probability": DimensionSpec(
        name="Regrouping Probability",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name=None,
        extrapolate=False,
        description="Probability of requiring carry/borrow"
    ),
    "regrouping_required": DimensionSpec(
        name="Regrouping Required",
        value_type="bool",
        default_min=False,
        default_max=True,
        constraint_name="regrouping",
        extrapolate=False,
        description="Force regrouping based on competency"
    ),
    "step_count": DimensionSpec(
        name="Step Count",
        value_type="int",
        default_min=1,
        default_max=3,
        constraint_name="step_count",
        extrapolate=True,
        description="Number of operations in problem"
    ),
    "divisibility_difficulty": DimensionSpec(
        name="Divisibility Difficulty",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name=None,
        extrapolate=True,
        description="How 'nice' the numbers are (0=round numbers, 1=any)"
    ),
    "include_remainder": DimensionSpec(
        name="Include Remainder",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name=None,
        extrapolate=False,
        description="Probability of division with remainder (threshold 0.5)"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# FRACTIONS DIMENSIONS (Grades 1-6)
# Competencies: identify, compare, order, add/subtract, equivalents, simplify
# ═══════════════════════════════════════════════════════════════════════════════

FRACTIONS_DIMENSIONS = {
    "denominator_max": DimensionSpec(
        name="Maximum Denominator",
        value_type="int",
        default_min=2,
        default_max=12,
        constraint_name="denominator_limit",
        extrapolate=True,
        description="Largest allowed denominator"
    ),
    "allowed_denominators": DimensionSpec(
        name="Allowed Denominators",
        value_type="choice",
        default_min=0,
        default_max=3,
        constraint_name="denominator_list",
        extrapolate=False,
        description="List of denominators based on competency",
        choices=[[2, 4], [2, 3, 4, 5], [2, 3, 4, 5, 6, 8], [2, 3, 4, 5, 6, 8, 10, 12]]
    ),
    "fraction_type_index": DimensionSpec(
        name="Fraction Type",
        value_type="float",
        default_min=0.0,      # Unit fractions (1/n)
        default_max=1.0,      # Mixed numbers
        constraint_name="fraction_type",
        extrapolate=False,
        description="0=unit, 0.3=proper, 0.6=improper, 1.0=mixed"
    ),
    "like_denominators": DimensionSpec(
        name="Like Denominators Probability",
        value_type="float",
        default_min=1.0,      # Always same denominator
        default_max=0.0,      # Different denominators
        constraint_name=None,
        extrapolate=False,
        description="Probability of same denominator in operations"
    ),
    "simplification_required": DimensionSpec(
        name="Simplification Required",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name=None,
        extrapolate=False,
        description="Probability answer needs simplification"
    ),
    "operation_complexity": DimensionSpec(
        name="Operation Complexity",
        value_type="float",
        default_min=0.0,      # Compare/identify only
        default_max=1.0,      # Add/subtract
        constraint_name=None,
        extrapolate=False,
        description="0=compare, 0.5=add similar, 1.0=add dissimilar"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# DECIMALS DIMENSIONS (Grades 4-6)
# Competencies: place value, read/write, compare, order, round, convert
# ═══════════════════════════════════════════════════════════════════════════════

DECIMALS_DIMENSIONS = {
    "decimal_places": DimensionSpec(
        name="Decimal Places",
        value_type="int",
        default_min=1,
        default_max=4,
        constraint_name="decimal_places",
        extrapolate=True,
        description="Number of decimal places (tenths=1, hundredths=2, etc.)"
    ),
    "whole_part_max": DimensionSpec(
        name="Whole Part Maximum",
        value_type="int",
        default_min=1,
        default_max=1000,
        constraint_name="numeric_limit",
        extrapolate=True,
        description="Maximum whole number part",
        scale_type="log"
    ),
    "operation_type": DimensionSpec(
        name="Operation Type",
        value_type="float",
        default_min=0.0,      # Read/identify
        default_max=1.0,      # Compute
        constraint_name=None,
        extrapolate=False,
        description="0=place value, 0.3=compare, 0.6=add/sub, 1.0=mul/div"
    ),
    "conversion_required": DimensionSpec(
        name="Conversion Required",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name=None,
        extrapolate=False,
        description="Probability of fraction<->decimal conversion"
    ),
    "trailing_zeros": DimensionSpec(
        name="Trailing Zeros",
        value_type="float",
        default_min=0.0,
        default_max=0.5,
        constraint_name=None,
        extrapolate=False,
        description="Probability of trailing zeros to test equivalence"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# RATIOS AND PERCENT DIMENSIONS (Grades 6-7)
# Competencies: ratios, proportions, percentages, conversion between forms
# ═══════════════════════════════════════════════════════════════════════════════

RATIOS_PERCENT_DIMENSIONS = {
    "ratio_max": DimensionSpec(
        name="Ratio Maximum",
        value_type="int",
        default_min=5,
        default_max=100,
        constraint_name="numeric_limit",
        extrapolate=True,
        description="Maximum value in ratio terms"
    ),
    "percent_type": DimensionSpec(
        name="Percent Type",
        value_type="float",
        default_min=0.0,      # Simple percentages (25%, 50%, 75%)
        default_max=1.0,      # Any percentage
        constraint_name=None,
        extrapolate=False,
        description="0=benchmark %, 0.5=nice %, 1.0=any %"
    ),
    "conversion_complexity": DimensionSpec(
        name="Conversion Complexity",
        value_type="float",
        default_min=0.0,      # No conversion
        default_max=1.0,      # Multiple conversions
        constraint_name=None,
        extrapolate=False,
        description="0=single form, 0.5=one conversion, 1.0=chain"
    ),
    "proportion_type": DimensionSpec(
        name="Proportion Type",
        value_type="float",
        default_min=0.0,      # Direct proportion
        default_max=1.0,      # Inverse proportion
        constraint_name=None,
        extrapolate=False,
        description="0=direct only, 1.0=may include inverse"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# ALGEBRA DIMENSIONS (Grades 7-10)
# Competencies: expressions, equations, variables, exponents, polynomials
# ═══════════════════════════════════════════════════════════════════════════════

ALGEBRA_DIMENSIONS = {
    "term_count": DimensionSpec(
        name="Term Count",
        value_type="int",
        default_min=2,
        default_max=5,
        constraint_name=None,
        extrapolate=True,
        description="Number of terms in expression"
    ),
    "coefficient_max": DimensionSpec(
        name="Coefficient Maximum",
        value_type="int",
        default_min=5,
        default_max=20,
        constraint_name=None,
        extrapolate=True,
        description="Maximum coefficient value"
    ),
    "exponent_max": DimensionSpec(
        name="Exponent Maximum",
        value_type="int",
        default_min=1,
        default_max=4,
        constraint_name=None,
        extrapolate=True,
        description="Maximum exponent value"
    ),
    "variable_count": DimensionSpec(
        name="Variable Count",
        value_type="int",
        default_min=1,
        default_max=2,
        constraint_name=None,
        extrapolate=False,
        description="Number of different variables"
    ),
    "negatives_probability": DimensionSpec(
        name="Negatives Probability",
        value_type="float",
        default_min=0.0,
        default_max=1.0,
        constraint_name="include_negatives",
        extrapolate=False,
        description="Probability of negative coefficients"
    ),
    "equation_complexity": DimensionSpec(
        name="Equation Complexity",
        value_type="float",
        default_min=0.0,      # One-step equations
        default_max=1.0,      # Multi-step with distribution
        constraint_name=None,
        extrapolate=False,
        description="0=one-step, 0.5=two-step, 1.0=multi-step"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# GEOMETRY PROPERTIES DIMENSIONS (Grades 1-10)
# Competencies: shape properties, angles, lines, polygons, circles
# ═══════════════════════════════════════════════════════════════════════════════

GEOMETRY_PROPS_DIMENSIONS = {
    "shape_complexity": DimensionSpec(
        name="Shape Complexity",
        value_type="float",
        default_min=0.0,      # Basic shapes (triangle, rectangle, square)
        default_max=1.0,      # Complex polygons (hexagon, irregular)
        constraint_name=None,
        extrapolate=False,
        description="0=basic, 0.5=quadrilaterals, 1.0=n-gons"
    ),
    "property_type": DimensionSpec(
        name="Property Type",
        value_type="float",
        default_min=0.0,      # Count sides/corners
        default_max=1.0,      # Angle relationships
        constraint_name=None,
        extrapolate=False,
        description="0=counting, 0.5=classification, 1.0=relationships"
    ),
    "angle_precision": DimensionSpec(
        name="Angle Precision",
        value_type="float",
        default_min=0.0,      # Right angles only
        default_max=1.0,      # Any angle
        constraint_name=None,
        extrapolate=False,
        description="0=90 only, 0.5=multiples of 30, 1.0=any"
    ),
    "polygon_sides_max": DimensionSpec(
        name="Maximum Polygon Sides",
        value_type="int",
        default_min=3,
        default_max=10,
        constraint_name="polygon_sides",
        extrapolate=False,
        description="Maximum sides for polygons"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# MEASUREMENT DIMENSIONS (Grades 1-7)
# Competencies: length, mass, capacity, time, temperature, unit conversion
# ═══════════════════════════════════════════════════════════════════════════════

MEASUREMENT_DIMENSIONS = {
    "measurement_type": DimensionSpec(
        name="Measurement Type",
        value_type="choice",
        default_min=0,
        default_max=3,
        constraint_name=None,
        extrapolate=False,
        description="Type of measurement",
        choices=["length", "mass", "capacity", "time"]
    ),
    "value_max": DimensionSpec(
        name="Value Maximum",
        value_type="int",
        default_min=10,
        default_max=10000,
        constraint_name="numeric_limit",
        extrapolate=True,
        description="Maximum measurement value",
        scale_type="log"
    ),
    "conversion_steps": DimensionSpec(
        name="Conversion Steps",
        value_type="int",
        default_min=0,
        default_max=2,
        constraint_name=None,
        extrapolate=False,
        description="Number of unit conversions required"
    ),
    "unit_familiarity": DimensionSpec(
        name="Unit Familiarity",
        value_type="float",
        default_min=0.0,      # Common units (m, kg, L)
        default_max=1.0,      # All units (mm, mg, mL)
        constraint_name=None,
        extrapolate=False,
        description="0=common, 0.5=standard, 1.0=all metric"
    ),
    "computation_required": DimensionSpec(
        name="Computation Required",
        value_type="float",
        default_min=0.0,      # Identification only
        default_max=1.0,      # Multi-step computation
        constraint_name=None,
        extrapolate=False,
        description="0=identify, 0.5=convert, 1.0=compute"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA AND PROBABILITY DIMENSIONS (Grades 1-10)
# Competencies: read tables/graphs, mean/median/mode, probability
# ═══════════════════════════════════════════════════════════════════════════════

DATA_PROBABILITY_DIMENSIONS = {
    "data_size": DimensionSpec(
        name="Data Set Size",
        value_type="int",
        default_min=3,
        default_max=10,
        constraint_name=None,
        extrapolate=True,
        description="Number of data points"
    ),
    "value_max": DimensionSpec(
        name="Data Value Maximum",
        value_type="int",
        default_min=10,
        default_max=100,
        constraint_name="numeric_limit",
        extrapolate=True,
        description="Maximum value in data set"
    ),
    "measure_type": DimensionSpec(
        name="Measure Type",
        value_type="float",
        default_min=0.0,      # Count/read
        default_max=1.0,      # Mean/median/mode
        constraint_name=None,
        extrapolate=False,
        description="0=read, 0.5=mode, 0.7=median, 1.0=mean"
    ),
    "probability_complexity": DimensionSpec(
        name="Probability Complexity",
        value_type="float",
        default_min=0.0,      # Simple (1 event)
        default_max=1.0,      # Compound events
        constraint_name=None,
        extrapolate=False,
        description="0=simple, 0.5=two events, 1.0=compound"
    ),
    "decimal_answers": DimensionSpec(
        name="Decimal Answers",
        value_type="float",
        default_min=0.0,      # Whole number answers
        default_max=1.0,      # Decimal answers
        constraint_name=None,
        extrapolate=False,
        description="Probability of non-integer answers"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# CONCEPTUAL DIMENSIONS (Fallback for all grades)
# Competencies: identify, describe, illustrate, recognize, represent
# ═══════════════════════════════════════════════════════════════════════════════

CONCEPTUAL_DIMENSIONS = {
    "abstraction_level": DimensionSpec(
        name="Abstraction Level",
        value_type="float",
        default_min=0.0,      # Concrete examples
        default_max=1.0,      # Abstract definitions
        constraint_name=None,
        extrapolate=False,
        description="0=example-based, 0.5=property-based, 1.0=definition-based"
    ),
    "distractor_similarity": DimensionSpec(
        name="Distractor Similarity",
        value_type="float",
        default_min=0.2,      # Obviously wrong
        default_max=0.9,      # Very similar
        constraint_name=None,
        extrapolate=False,
        description="How similar distractors are to correct answer"
    ),
    "context_complexity": DimensionSpec(
        name="Context Complexity",
        value_type="float",
        default_min=0.0,      # Direct question
        default_max=1.0,      # Requires inference
        constraint_name=None,
        extrapolate=False,
        description="Amount of context processing required"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATOR TYPE TO DIMENSIONS MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

GENERATOR_DIMENSIONS = {
    "counting": COUNTING_DIMENSIONS,
    "place_value": PLACE_VALUE_DIMENSIONS,
    "arithmetic": ARITHMETIC_DIMENSIONS,
    "fractions": FRACTIONS_DIMENSIONS,
    "decimals": DECIMALS_DIMENSIONS,
    "ratios_percent": RATIOS_PERCENT_DIMENSIONS,
    "algebra": ALGEBRA_DIMENSIONS,
    "geometry_props": GEOMETRY_PROPS_DIMENSIONS,
    "measurement": MEASUREMENT_DIMENSIONS,
    "data_probability": DATA_PROBABILITY_DIMENSIONS,
    "conceptual": CONCEPTUAL_DIMENSIONS,
}


# ═══════════════════════════════════════════════════════════════════════════════
# INTERPOLATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def log_interpolate(min_val: float, max_val: float, t: float) -> float:
    """
    Logarithmic interpolation between min and max.
    Produces slow growth at low t values, accelerating toward max.
    """
    if min_val <= 0 or max_val <= 0:
        return min_val + t * (max_val - min_val)
    return min_val * pow(max_val / min_val, t)


def interpolate_dimension(
    spec: DimensionSpec,
    difficulty: float,
    actual_min: Optional[Any] = None,
    actual_max: Optional[Any] = None,
) -> Any:
    """
    Interpolate a dimension value at given difficulty level.
    """
    min_val = actual_min if actual_min is not None else spec.default_min
    max_val = actual_max if actual_max is not None else spec.default_max
    
    # Clamp difficulty for non-extrapolating dimensions
    t = difficulty
    if t > 1.0 and not spec.extrapolate:
        t = 1.0
    
    if spec.value_type == "bool":
        return t >= 0.5
    
    if spec.value_type == "choice" and spec.choices:
        # Map difficulty to index in choices list
        idx = int(t * (len(spec.choices) - 1))
        idx = max(0, min(idx, len(spec.choices) - 1))
        return spec.choices[idx]
    
    # Determine scale type
    scale = spec.scale_type
    if scale == "auto":
        if min_val > 0 and max_val > 0 and max_val / min_val >= 10:
            scale = "log"
        else:
            scale = "linear"
    
    # Compute value
    if scale == "log" and min_val > 0 and max_val > 0:
        value = log_interpolate(min_val, max_val, t)
    else:
        value = min_val + t * (max_val - min_val)
    
    if spec.value_type == "int":
        return round(value)
    else:
        return value


def get_dimension_values(
    generator_type: str,
    difficulty: float,
    constraints: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Get all interpolated dimension values for a generator type.
    
    Args:
        generator_type: Generator type name (e.g., "arithmetic")
        difficulty: Scalar difficulty 0.0 to 1.5+
        constraints: Extracted constraints from competency text
    
    Returns:
        Dict of dimension_id -> interpolated value
    """
    if generator_type not in GENERATOR_DIMENSIONS:
        return {}
    
    dimensions = GENERATOR_DIMENSIONS[generator_type]
    result = {}
    
    for dim_id, spec in dimensions.items():
        # Check if constraint overrides this dimension
        actual_min = None
        actual_max = None
        
        if spec.constraint_name and spec.constraint_name in constraints:
            constraint_val = constraints[spec.constraint_name]
            
            # How to use constraint depends on the constraint type
            if isinstance(constraint_val, bool):
                # Boolean constraint forces the value
                result[dim_id] = constraint_val
                continue
            elif isinstance(constraint_val, list):
                # List constraint (e.g., denominator_list) - use as choices
                if spec.value_type == "choice":
                    spec = DimensionSpec(
                        name=spec.name,
                        value_type="choice",
                        default_min=0,
                        default_max=len(constraint_val) - 1,
                        constraint_name=spec.constraint_name,
                        extrapolate=False,
                        description=spec.description,
                        choices=constraint_val
                    )
            elif isinstance(constraint_val, (int, float)):
                # Numeric constraint - use as ceiling
                actual_max = constraint_val
        
        result[dim_id] = interpolate_dimension(spec, difficulty, actual_min, actual_max)
    
    # ── Post-processing: enforce cross-dimension consistency ──────────────────
    # For place_value: digit_count must not exceed what max_number allows
    if generator_type == "place_value" and "max_number" in result and "digit_count" in result:
        max_num = result["max_number"]
        if max_num and max_num > 0:
            max_digits_allowed = len(str(int(max_num)))  # e.g., 100 → 3 digits
            result["digit_count"] = min(result["digit_count"], max_digits_allowed)
    
    # Also cap target_place by digit_count
    if generator_type == "place_value" and "target_place" in result and "digit_count" in result:
        result["target_place"] = min(result["target_place"], result["digit_count"] - 1)
    
    return result
