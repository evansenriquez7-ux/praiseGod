"""
Curriculum Context Extraction Module

Extracts limits, constraints, and neighboring nodes from MATATAG curriculum
to enable curriculum-driven difficulty scaling for visual skeleton problems.

Author: CCMed Team
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Traditional defaults by grade (fallback when no explicit limits found)
TRADITIONAL_DEFAULTS = {
    1: {"min_amount": 10, "max_amount": 100, "denominations": [1, 5, 10, 20, 50, 100]},
    2: {"min_amount": 10, "max_amount": 1000, "denominations": [1, 5, 10, 20, 50, 100, 200, 500]},
    3: {"min_amount": 50, "max_amount": 1000, "denominations": [1, 5, 10, 20, 50, 100, 200, 500]},
    4: {"min_amount": 50, "max_amount": 1000, "denominations": [1, 5, 10, 20, 50, 100, 200, 500]},
    5: {"min_amount": 100, "max_amount": 10000, "denominations": [1, 5, 10, 20, 50, 100, 200, 500, 1000]},
    6: {"min_amount": 100, "max_amount": 10000, "denominations": [1, 5, 10, 20, 50, 100, 200, 500, 1000]},
    7: {"min_amount": 500, "max_amount": 100000, "denominations": [1, 5, 10, 20, 50, 100, 200, 500, 1000]},
    8: {"min_amount": 500, "max_amount": 100000, "denominations": [1, 5, 10, 20, 50, 100, 200, 500, 1000]},
    9: {"min_amount": 500, "max_amount": 100000, "denominations": [1, 5, 10, 20, 50, 100, 200, 500, 1000]},
    10: {"min_amount": 500, "max_amount": 100000, "denominations": [1, 5, 10, 20, 50, 100, 200, 500, 1000]},
}


# Load MATATAG curriculum data
_MATATAG_PATH = Path(__file__).parent.parent.parent / "data" / "ph" / "matatagmath.json"
_MATATAG_DATA = {}

if _MATATAG_PATH.exists():
    with open(_MATATAG_PATH, encoding="utf-8") as f:
        _MATATAG_DATA = json.load(f).get("Mathematics", {})


def extract_numerical_limits(text: str) -> List[int]:
    """
    Extract numerical limits from competency text.
    
    Examples:
        "up to ₱100" → [100]
        "up to ₱1000" → [1000]
        "numbers up to 10 000" → [10000]
        "between ₱50 and ₱200" → [50, 200]
    
    Returns list of integers found that are likely limits (≥10).
    """
    # Match ₱XXX or numbers with commas or spaces
    patterns = [
        r'₱\s*([\d,\s]+)',  # ₱100, ₱1,000, ₱10 000
        r'up to\s+([\d,\s]+)',  # up to 100, up to 10 000
        r'less than\s+([\d,\s]+)',  # less than 1000
        r'between\s+([\d,\s]+)\s+and\s+([\d,\s]+)',  # between 50 and 200
    ]
    
    limits = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            for group in match.groups():
                # Clean up: remove commas, spaces
                cleaned = group.replace(',', '').replace(' ', '')
                try:
                    num = int(cleaned)
                    # Only consider limits ≥ 10 (avoid picking up "2-step", "3-digit", etc.)
                    if num >= 10:
                        limits.append(num)
                except ValueError:
                    continue
    
    return sorted(set(limits))


def check_exclude_centavos(text: str) -> bool:
    """Check if competency explicitly excludes centavo coins."""
    return 'excluding centavo' in text.lower()


def find_competency_in_curriculum(competency_text: str) -> Optional[Dict]:
    """
    Find a competency in the MATATAG curriculum and return its location.
    
    Returns:
        {
            "grade": int,
            "strand": str,
            "quarter": int,
            "index": int,  # Position within that quarter
            "text": str
        }
    """
    # Normalize the search text
    normalized_search = competency_text.lower().strip()
    
    for grade_key, grade_data in _MATATAG_DATA.items():
        # Extract grade number
        match = re.search(r'Grade\s+(\d+)', grade_key)
        if not match:
            continue
        grade_num = int(match.group(1))
        
        for strand_name, quarters in grade_data.items():
            for quarter_key, competencies in quarters.items():
                # Extract quarter number
                q_match = re.search(r'Quarter\s+(\d+)', quarter_key)
                if not q_match:
                    continue
                quarter_num = int(q_match.group(1))
                
                for idx, comp_text in enumerate(competencies):
                    # Exact match or very close match
                    if comp_text.lower().strip() == normalized_search:
                        return {
                            "grade": grade_num,
                            "strand": strand_name,
                            "quarter": quarter_num,
                            "index": idx,
                            "text": comp_text
                        }
    
    return None


def get_neighboring_nodes(location: Dict) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Get previous and next nodes in the same strand.
    
    Logic:
    1. First try same grade, next quarter
    2. If not found, try next grade, any quarter
    
    Returns (prev_node, next_node) where each is:
        {"text": str, "limit": int | None, "grade": int, "quarter": int}
    """
    grade = location["grade"]
    strand = location["strand"]
    quarter = location["quarter"]
    index = location["index"]
    
    grade_key = f"Grade {grade}"
    quarter_key = f"Quarter {quarter}"
    
    # Get current quarter's competencies
    if grade_key not in _MATATAG_DATA or strand not in _MATATAG_DATA[grade_key]:
        return None, None
    
    current_quarter_comps = _MATATAG_DATA[grade_key][strand].get(quarter_key, [])
    
    prev_node = None
    next_node = None
    
    # PREVIOUS NODE: Previous competency in same quarter
    if index > 0:
        prev_text = current_quarter_comps[index - 1]
        prev_node = {
            "text": prev_text,
            "limit": max(extract_numerical_limits(prev_text)) if extract_numerical_limits(prev_text) else None,
            "grade": grade,
            "quarter": quarter
        }
    else:
        # Try previous quarter in same grade
        for q in range(quarter - 1, 0, -1):
            prev_q_key = f"Quarter {q}"
            if prev_q_key in _MATATAG_DATA[grade_key][strand]:
                prev_quarter_comps = _MATATAG_DATA[grade_key][strand][prev_q_key]
                if prev_quarter_comps:
                    prev_text = prev_quarter_comps[-1]  # Last competency of previous quarter
                    prev_node = {
                        "text": prev_text,
                        "limit": max(extract_numerical_limits(prev_text)) if extract_numerical_limits(prev_text) else None,
                        "grade": grade,
                        "quarter": q
                    }
                    break
        
        # If still not found, try previous grade
        if not prev_node:
            for g in range(grade - 1, 0, -1):
                prev_grade_key = f"Grade {g}"
                if prev_grade_key in _MATATAG_DATA and strand in _MATATAG_DATA[prev_grade_key]:
                    # Get last competency from any quarter
                    for q in range(4, 0, -1):
                        q_key = f"Quarter {q}"
                        if q_key in _MATATAG_DATA[prev_grade_key][strand]:
                            comps = _MATATAG_DATA[prev_grade_key][strand][q_key]
                            if comps:
                                prev_text = comps[-1]
                                prev_node = {
                                    "text": prev_text,
                                    "limit": max(extract_numerical_limits(prev_text)) if extract_numerical_limits(prev_text) else None,
                                    "grade": g,
                                    "quarter": q
                                }
                                break
                    if prev_node:
                        break
    
    # NEXT NODE: Next competency in same quarter
    if index < len(current_quarter_comps) - 1:
        next_text = current_quarter_comps[index + 1]
        next_node = {
            "text": next_text,
            "limit": max(extract_numerical_limits(next_text)) if extract_numerical_limits(next_text) else None,
            "grade": grade,
            "quarter": quarter
        }
    else:
        # Try next quarter in same grade
        for q in range(quarter + 1, 5):
            next_q_key = f"Quarter {q}"
            if next_q_key in _MATATAG_DATA[grade_key][strand]:
                next_quarter_comps = _MATATAG_DATA[grade_key][strand][next_q_key]
                if next_quarter_comps:
                    next_text = next_quarter_comps[0]  # First competency of next quarter
                    next_node = {
                        "text": next_text,
                        "limit": max(extract_numerical_limits(next_text)) if extract_numerical_limits(next_text) else None,
                        "grade": grade,
                        "quarter": q
                    }
                    break
        
        # If still not found, try next grade
        if not next_node:
            for g in range(grade + 1, 11):
                next_grade_key = f"Grade {g}"
                if next_grade_key in _MATATAG_DATA and strand in _MATATAG_DATA[next_grade_key]:
                    # Get first competency from any quarter
                    for q in range(1, 5):
                        q_key = f"Quarter {q}"
                        if q_key in _MATATAG_DATA[next_grade_key][strand]:
                            comps = _MATATAG_DATA[next_grade_key][strand][q_key]
                            if comps:
                                next_text = comps[0]
                                next_node = {
                                    "text": next_text,
                                    "limit": max(extract_numerical_limits(next_text)) if extract_numerical_limits(next_text) else None,
                                    "grade": g,
                                    "quarter": q
                                }
                                break
                    if next_node:
                        break
    
    return prev_node, next_node


def get_curriculum_context(competency_text: str) -> Dict:
    """
    Get comprehensive context for a competency including limits and neighbors.
    
    Returns:
        {
            "grade": int,
            "strand": str,
            "quarter": int,
            "explicit_limit": int | None,
            "explicit_denominations": List[int] | None,
            "exclude_centavos": bool,
            "prev_node": {
                "text": str,
                "limit": int | None,
                "grade": int,
                "quarter": int
            } | None,
            "next_node": {
                "text": str,
                "limit": int | None,
                "grade": int,
                "quarter": int
            } | None,
            "traditional_defaults": {
                "min_amount": int,
                "max_amount": int,
                "denominations": List[int]
            }
        }
    """
    # Find competency in curriculum
    location = find_competency_in_curriculum(competency_text)
    
    if not location:
        # Fallback: assume Grade 5 if not found
        grade = 5
        strand = "Number and Algebra"
        quarter = 1
        prev_node = None
        next_node = None
    else:
        grade = location["grade"]
        strand = location["strand"]
        quarter = location["quarter"]
        prev_node, next_node = get_neighboring_nodes(location)
    
    # Extract explicit limits from the competency text
    limits = extract_numerical_limits(competency_text)
    explicit_limit = max(limits) if limits else None
    
    # Get traditional defaults for this grade
    defaults = TRADITIONAL_DEFAULTS.get(grade, TRADITIONAL_DEFAULTS[5])
    
    return {
        "grade": grade,
        "strand": strand,
        "quarter": quarter,
        "explicit_limit": explicit_limit,
        "explicit_denominations": None,  # TODO: Parse if explicitly mentioned
        "exclude_centavos": check_exclude_centavos(competency_text),
        "prev_node": prev_node,
        "next_node": next_node,
        "traditional_defaults": defaults
    }


def get_strand_progression(strand_name: str, start_grade: int = 1, end_grade: int = 10) -> List[Dict]:
    """
    Get all competencies in a strand across grades (for analysis/debugging).
    
    Returns list of competencies with their metadata.
    """
    progression = []
    
    for grade in range(start_grade, end_grade + 1):
        grade_key = f"Grade {grade}"
        if grade_key not in _MATATAG_DATA or strand_name not in _MATATAG_DATA[grade_key]:
            continue
        
        for quarter in range(1, 5):
            quarter_key = f"Quarter {quarter}"
            if quarter_key not in _MATATAG_DATA[grade_key][strand_name]:
                continue
            
            comps = _MATATAG_DATA[grade_key][strand_name][quarter_key]
            for idx, comp_text in enumerate(comps):
                limits = extract_numerical_limits(comp_text)
                progression.append({
                    "grade": grade,
                    "quarter": quarter,
                    "index": idx,
                    "text": comp_text,
                    "limits": limits,
                    "max_limit": max(limits) if limits else None
                })
    
    return progression
