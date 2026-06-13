"""
Constraint Extractor Module

Parses dimensional constraints from MATATAG competency text to enable
curriculum-driven difficulty scaling.

Extracts limits like:
- "up to ₱100" → numeric_limit: 100
- "3-digit numbers" → digit_count: 3
- "by the half hour" → time_granularity: 30
- "excluding centavo coins" → exclude_centavos: True

Author: CCMed Team
"""

import re
from typing import Dict, Any, List, Optional


def extract_constraints(competency_text: str) -> Dict[str, Any]:
    """
    Extract all dimensional constraints from a competency text.
    
    Args:
        competency_text: Full competency text from MATATAG curriculum
    
    Returns:
        Dictionary mapping constraint types to values
    
    Example:
        >>> extract_constraints("Determine the value of bills up to ₱100")
        {'numeric_limit': 100, 'currency_types': ['bills']}
    """
    text = competency_text
    text_lower = text.lower()
    constraints = {}
    
    # ========== NUMERIC LIMITS ==========
    # Patterns: "up to X", "less than X", "with sums up to X"
    numeric_patterns = [
        r'up to ₱?([\d,\s]+)',
        r'less than ₱?([\d,\s]+)',
        r'sums? (?:up )?to ₱?([\d,\s]+)',
        r'with(?:in)? ₱?([\d,\s]+)',
        r'numbers (?:up )?to ₱?([\d,\s]+)',
    ]
    
    for pattern in numeric_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '').replace(' ', '')
            try:
                numeric_value = int(value_str)
                if numeric_value >= 10:  # Ignore small numbers like "2-step"
                    constraints['numeric_limit'] = numeric_value
                    break
            except ValueError:
                continue
    
    # ========== DIGIT COUNT ==========
    # Pattern: "N-digit number"
    digit_match = re.search(r'(\d+)-?digit', text_lower)
    if digit_match:
        constraints['digit_count'] = int(digit_match.group(1))
    
    # ========== DECIMAL PLACES ==========
    # Pattern: "N decimal place(s)"
    decimal_match = re.search(r'(\d+) decimal place', text_lower)
    if decimal_match:
        constraints['decimal_places'] = int(decimal_match.group(1))
    
    # ========== TIME GRANULARITY ==========
    # Patterns: "by the hour", "half hour", "quarter hour"
    if 'quarter hour' in text_lower or 'quarter-hour' in text_lower:
        constraints['time_granularity'] = 15
    elif 'half hour' in text_lower or 'half-hour' in text_lower:
        constraints['time_granularity'] = 30
    elif 'by the hour' in text_lower or 'on the hour' in text_lower:
        constraints['time_granularity'] = 60
    elif 'minute' in text_lower and 'hour' not in text_lower:
        # If mentions minutes without hour context, assume 1-minute precision
        constraints['time_granularity'] = 1
    
    # ========== FRACTION DENOMINATORS ==========
    # Pattern: "denominators up to N" or "denominators 2, 3, 4"
    denom_match = re.search(r'denominator[s]? (?:up to |of )?(\d+)', text_lower)
    if denom_match:
        constraints['denominator_limit'] = int(denom_match.group(1))
    
    # Specific denominator lists: "denominators 2, 3, 4, 5"
    denom_list_match = re.search(r'denominator[s]? ([\d,\s]+(?:and [\d]+)?)', text_lower)
    if denom_list_match:
        denom_str = denom_list_match.group(1)
        denoms = [int(d.strip()) for d in re.findall(r'\d+', denom_str)]
        if denoms:
            constraints['denominator_list'] = denoms
            constraints['denominator_limit'] = max(denoms)
    
    # ========== FRACTION TYPES ==========
    if 'unit' in text_lower:
        constraints['fraction_type'] = 'unit'
    elif 'similar' in text_lower:
        constraints['fraction_type'] = 'similar'
    elif 'dissimilar' in text_lower:
        constraints['fraction_type'] = 'dissimilar'
    elif 'improper' in text_lower:
        constraints['fraction_type'] = 'improper'
    elif 'proper' in text_lower:
        constraints['fraction_type'] = 'proper'
    elif 'mixed' in text_lower:
        constraints['fraction_type'] = 'mixed'
    
    # ========== OPERATIONS ==========
    operations = []
    if 'addition' in text_lower or 'add ' in text_lower or 'sum' in text_lower:
        operations.append('add')
    if 'subtraction' in text_lower or 'subtract' in text_lower or 'difference' in text_lower:
        operations.append('sub')
    if 'multiplication' in text_lower or 'multiply' in text_lower or 'product' in text_lower:
        operations.append('mul')
    if 'division' in text_lower or 'divide' in text_lower or 'quotient' in text_lower:
        operations.append('div')
    
    if operations:
        constraints['operations'] = operations
    
    # ========== STEP COUNT ==========
    step_match = re.search(r'(\d+)-?step', text_lower)
    if step_match:
        constraints['step_count'] = int(step_match.group(1))
    elif 'multi-step' in text_lower or 'multistep' in text_lower:
        constraints['step_count'] = 2  # Default multi-step to 2
    
    # ========== MONEY-SPECIFIC ==========
    if 'centavo' in text_lower:
        if 'excluding' in text_lower:
            constraints['exclude_centavos'] = True
        else:
            constraints['include_centavos'] = True
    
    # Currency types
    currency_types = []
    if 'bill' in text_lower:
        currency_types.append('bills')
    if 'coin' in text_lower:
        currency_types.append('coins')
    if currency_types:
        constraints['currency_types'] = currency_types
    
    # ========== MULTIPLICATION TABLES ==========
    # Pattern: "2, 3, 4, 5, and 10 multiplication tables"
    mult_table_match = re.search(r'([\d,\s]+(?:and [\d]+)?) multiplication table', text_lower)
    if mult_table_match:
        tables_str = mult_table_match.group(1)
        tables = [int(d.strip()) for d in re.findall(r'\d+', tables_str)]
        if tables:
            constraints['multiplication_tables'] = tables
            constraints['multiplication_max'] = max(tables)
    
    # ========== ROUNDING PRECISION ==========
    if 'nearest ten' in text_lower:
        constraints['rounding_precision'] = 10
    elif 'nearest hundred' in text_lower:
        constraints['rounding_precision'] = 100
    elif 'nearest thousand' in text_lower:
        constraints['rounding_precision'] = 1000
    
    # ========== NUMBER TYPES ==========
    if 'integer' in text_lower or 'positive and negative' in text_lower:
        constraints['include_negatives'] = True
    
    if 'even' in text_lower and 'odd' in text_lower:
        constraints['parity'] = 'both'
    elif 'even' in text_lower:
        constraints['parity'] = 'even'
    elif 'odd' in text_lower:
        constraints['parity'] = 'odd'
    
    if 'prime' in text_lower:
        constraints['include_primes'] = True
    if 'composite' in text_lower:
        constraints['include_composites'] = True
    
    # ========== ORDINAL LIMITS ==========
    # Pattern: "up to 10th", "up to 100th"
    ordinal_match = re.search(r'up to (\d+)(?:st|nd|rd|th)', text_lower)
    if ordinal_match:
        constraints['ordinal_limit'] = int(ordinal_match.group(1))
    
    # ========== REGROUPING ==========
    # Pattern: "with regrouping", "without regrouping", "with or without regrouping"
    if 'with or without regrouping' in text_lower:
        constraints['regrouping'] = 'optional'
    elif 'without regrouping' in text_lower:
        constraints['regrouping'] = False
    elif 'with regrouping' in text_lower:
        constraints['regrouping'] = True
    
    # ========== POLYGON SIDES ==========
    # Pattern: "5, 6, 8, or 10 sides" or "polygons with 5, 6, 8, or 10 sides"
    polygon_match = re.search(r'(\d+(?:,\s*\d+)*(?:,?\s*(?:or|and)\s*\d+)?)\s*sides', text_lower)
    if polygon_match:
        sides_str = polygon_match.group(1)
        sides = [int(s.strip()) for s in re.findall(r'\d+', sides_str)]
        if sides:
            constraints['polygon_sides'] = sides
    
    # ========== EQUATION TYPE ==========
    if 'linear equation' in text_lower:
        constraints['equation_type'] = 'linear'
    elif 'quadratic equation' in text_lower or 'quadratic' in text_lower:
        constraints['equation_type'] = 'quadratic'
    
    # ========== PLACE-SPECIFIC DECIMAL MENTIONS ==========
    if 'tenths' in text_lower and 'decimal_places' not in constraints:
        constraints['decimal_places'] = 1
    elif 'hundredths' in text_lower and 'decimal_places' not in constraints:
        constraints['decimal_places'] = 2
    elif 'thousandths' in text_lower and 'decimal_places' not in constraints:
        constraints['decimal_places'] = 3
    
    return constraints


def extract_numeric_limit(competency_text: str) -> Optional[int]:
    """
    Quick extraction of just the numeric limit.
    
    Returns:
        Numeric limit or None if not found
    """
    constraints = extract_constraints(competency_text)
    return constraints.get('numeric_limit')


def has_constraint(competency_text: str, constraint_type: str) -> bool:
    """
    Check if a competency has a specific constraint type.
    
    Args:
        competency_text: Competency text
        constraint_type: Constraint key to check (e.g., 'numeric_limit')
    
    Returns:
        True if constraint is present
    """
    constraints = extract_constraints(competency_text)
    return constraint_type in constraints
