"""
Skill Matcher Module

Identifies skill types from competency text to determine if two competencies
are teaching the same underlying skill (required for using neighboring node
constraints in difficulty scaling).

Author: CCMed Team
"""

from typing import List, Set

# Comprehensive skill keywords extracted from all 506 MATATAG competencies
SKILL_KEYWORDS = {
    # Basic number skills (6 categories)
    'counting': ['count', 'counting', 'skip count', 'skip-count'],
    'comparison': ['compare', 'comparing', 'comparison', 'greater', 'lesser', 'equal'],
    'ordering': ['order', 'ordering', 'arrange', 'arranging', 'sequence', 'smallest', 'largest'],
    'identification': ['recognize', 'identify', 'identification', 'distinguish', 'differentiate', 'classify'],
    'read_write': ['read and write', 'read or write', 'reading', 'writing', 'write numbers', 'read numbers'],
    'representation': ['represent', 'representation', 'illustrate', 'model', 'draw', 'construct'],
    
    # Arithmetic operations (4 categories)
    'addition': ['add', 'adding', 'addition', 'sum', 'addend', 'plus'],
    'subtraction': ['subtract', 'subtracting', 'subtraction', 'difference', 'minus', 'take away'],
    'multiplication': ['multiply', 'multiplying', 'multiplication', 'product', 'times', 'multiplication table'],
    'division': ['divide', 'dividing', 'division', 'quotient', 'remainder', 'divisor', 'dividend'],
    
    # Number concepts (7 categories)
    'place_value': ['place value', 'digit', 'digits', 'ones', 'tens', 'hundreds', 'thousands'],
    'compose_decompose': ['compose', 'decompose', 'regroup', 'regrouping', 'expanded form'],
    'rounding': ['round', 'rounding', 'nearest'],
    'estimation': ['estimate', 'estimating', 'estimation', 'approximate', 'about'],
    'even_odd': ['even', 'odd', 'parity'],
    'prime_composite': ['prime', 'composite', 'prime number', 'composite number'],
    'factors_multiples': ['factor', 'factors', 'multiple', 'multiples', 'gcf', 'lcm', 'greatest common', 'least common', 'divisible', 'divisibility'],
    
    # Fractions & Decimals (3 categories)
    'fractions': ['fraction', 'fractions', 'numerator', 'denominator', 'proper', 'improper', 'mixed number', 'half', 'quarter', 'third'],
    'decimals': ['decimal', 'decimals', 'decimal place', 'decimal point', 'tenths', 'hundredths'],
    'ratio_percent': ['ratio', 'ratios', 'proportion', 'percent', 'percentage', 'rate'],
    
    # Algebra (3 categories)
    'patterns': ['pattern', 'patterns', 'sequence', 'sequences', 'rule', 'rules', 'next term', 'nth term'],
    'algebra': ['equation', 'equations', 'expression', 'expressions', 'variable', 'variables', 'algebraic', 'solve for', 'unknown'],
    'exponents': ['exponent', 'exponential', 'power', 'squared', 'cubed'],
    
    # Geometry - Shapes (2 categories)
    'shapes_2d': ['triangle', 'triangles', 'rectangle', 'rectangles', 'square', 'squares', 'circle', 'circles', 
                  'polygon', 'polygons', 'quadrilateral', 'pentagon', 'hexagon', 'shape', 'shapes'],
    'shapes_3d': ['cube', 'cubes', 'rectangular prism', 'prism', 'prisms', 'pyramid', 'pyramids', 
                  'sphere', 'cylinder', 'cone', 'solid figure', 'solid figures', '3d', 'three-dimensional'],
    
    # Geometry - Lines & Angles (5 categories)
    'lines_geometry': ['line', 'lines', 'ray', 'rays', 'segment', 'segments', 'parallel', 'perpendicular', 
                       'intersect', 'intersection', 'vertex', 'vertices', 'edge', 'edges', 'face', 'faces'],
    'angles': ['angle', 'angles', 'degree', 'degrees', 'acute', 'obtuse', 'right angle', 'straight angle'],
    'transformations': ['symmetry', 'symmetric', 'congruent', 'congruence', 'similar', 'similarity',
                        'translate', 'translation', 'reflect', 'reflection', 'rotate', 'rotation', 'transform'],
    'coordinate_plane': ['coordinate', 'coordinates', 'cartesian', 'x-axis', 'y-axis', 'origin', 'plot', 'point'],
    'position': ['position', 'ordinal', '1st', '2nd', '3rd', 'first', 'second', 'third', 'location', 'direction'],
    
    # Measurement (4 categories)
    'measurement_length': ['length', 'width', 'height', 'distance', 'meter', 'centimeter', 'kilometer', 
                          'inch', 'foot', 'feet', 'measure', 'measuring', 'measurement'],
    'measurement_area': ['area', 'perimeter', 'square unit', 'square meter', 'square cm'],
    'measurement_volume': ['volume', 'capacity', 'liter', 'milliliter', 'cubic'],
    'measurement_mass': ['mass', 'weight', 'gram', 'kilogram', 'heavy', 'light'],
    
    # Time & Calendar (2 categories)
    'time': ['time', 'clock', 'hour', 'minute', 'second', 'elapsed', 'duration', 'am', 'pm'],
    'calendar': ['calendar', 'day', 'days', 'week', 'weeks', 'month', 'months', 'year', 'years', 'date'],
    
    # Money (1 category)
    'money': ['money', 'peso', 'pesos', 'coin', 'coins', 'bill', 'bills', '₱', 'currency', 'centavo', 'price', 'cost'],
    
    # Data & Statistics (4 categories)
    'data_collection': ['data', 'collect', 'survey', 'tally', 'frequency', 'sample'],
    'graphing': ['graph', 'graphs', 'graphing', 'chart', 'charts', 'pictograph', 'bar graph', 'line graph', 
                 'pie chart', 'histogram', 'plot', 'plotting'],
    'statistics': ['statistics', 'mean', 'median', 'mode', 'range', 'average', 'central tendency'],
    'probability': ['probability', 'chance', 'likely', 'unlikely', 'certain', 'impossible', 'random', 'outcome', 'event'],
    
    # Other (4 categories)
    'financial': ['interest', 'simple interest', 'compound interest', 'principal', 'depreciation', 
                  'profit', 'loss', 'discount', 'financial', 'budget', 'income', 'expense'],
    'sets': ['set', 'sets', 'subset', 'union', 'intersection', 'element', 'member'],
    'conversion': ['convert', 'conversion', 'equivalent', 'equivalence'],
    'problem_solving': ['solve', 'solving', 'problem', 'problems', 'word problem', 'real-life', 'real life', 'application'],
}


def get_skill_types(competency_text: str) -> List[str]:
    """
    Extract all matching skill types from a competency text.
    
    Args:
        competency_text: Full competency text from MATATAG
    
    Returns:
        List of skill type IDs that match the competency
        (e.g., ['money', 'addition', 'problem_solving'])
    
    Example:
        >>> get_skill_types("Solve problems involving addition of money...")
        ['addition', 'money', 'problem_solving']
    """
    text_lower = competency_text.lower()
    matches = []
    
    for skill_id, keywords in SKILL_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            matches.append(skill_id)
    
    return matches


def get_primary_skill(competency_text: str) -> str:
    """
    Get the primary (most relevant) skill type for a competency.
    
    Uses heuristics to determine which skill is "primary" when multiple match.
    Priority order: specific skills > generic skills
    
    Returns:
        Primary skill ID, or "unknown" if no match
    """
    skills = get_skill_types(competency_text)
    
    if not skills:
        return "unknown"
    
    # Priority order (more specific skills first)
    priority_order = [
        # Money and time are very specific
        'money', 'time', 'calendar', 'financial',
        # Specific math concepts
        'fractions', 'decimals', 'ratio_percent', 'exponents',
        'prime_composite', 'factors_multiples', 'even_odd',
        # Operations (more specific than "problem_solving")
        'addition', 'subtraction', 'multiplication', 'division',
        # Measurement
        'measurement_length', 'measurement_area', 'measurement_volume', 'measurement_mass',
        # Geometry
        'shapes_2d', 'shapes_3d', 'angles', 'transformations', 'coordinate_plane',
        # Patterns and algebra
        'patterns', 'algebra',
        # Data
        'graphing', 'statistics', 'probability', 'data_collection',
        # Basic skills
        'counting', 'comparison', 'ordering', 'estimation', 'rounding',
        # Generic (least priority)
        'identification', 'read_write', 'representation', 'problem_solving',
    ]
    
    for skill in priority_order:
        if skill in skills:
            return skill
    
    # Fallback to first match
    return skills[0]


def skills_overlap(skills_a: List[str], skills_b: List[str]) -> bool:
    """
    Check if two skill lists have any overlap.
    
    Args:
        skills_a: Skill list from first competency
        skills_b: Skill list from second competency
    
    Returns:
        True if any skills match
    """
    return len(set(skills_a) & set(skills_b)) > 0


def are_skills_related(text_a: str, text_b: str) -> bool:
    """
    Check if two competency texts teach related skills.
    
    Two competencies are skill-related if they share at least one
    skill keyword category.
    
    Args:
        text_a: First competency text
        text_b: Second competency text
    
    Returns:
        True if skills overlap
    
    Example:
        >>> are_skills_related(
        ...     "Compare numbers up to 20",
        ...     "Compare numbers up to 100"
        ... )
        True
        >>> are_skills_related(
        ...     "Recognize numbers up to 100",
        ...     "Compare numbers up to 20"
        ... )
        False  # Different skills (identification vs comparison)
    """
    skills_a = get_skill_types(text_a)
    skills_b = get_skill_types(text_b)
    
    return skills_overlap(skills_a, skills_b)
