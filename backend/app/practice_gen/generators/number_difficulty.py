import math
import random
from typing import Tuple, List, Union, Optional, Any

# ─── DIFFICULTY SCORING FOR DIFFERENT TYPES ───────────────────────────────────

def score_whole_or_decimal(x: Union[int, float], max_val: Union[int, float], decimal_places: int = 0) -> float:
    """Score a whole number or decimal based on divisibility, digits, and magnitude."""
    if x <= 0:
        return 0.0
        
    scale = 10 ** decimal_places
    x_int = int(round(x * scale))
    max_val_int = int(round(max_val * scale))
    
    # 1. Divisibility (0.0 = divisible by 30, 1.0 = coprime to 30)
    gcd_30 = math.gcd(x_int, 30)
    c_div = 1.0 - (gcd_30 / 30.0)
    
    # 2. Digit Complexity (large digits are harder)
    clean_str = str(x).replace(".", "")
    digits = [int(d) for d in clean_str if d.isdigit()]
    c_digits = sum(digits) / (9.0 * len(digits)) if digits else 0.0
    
    # 3. Magnitude (log-linear scale difficulty)
    ref_max = max(max_val_int, x_int, 2)
    c_mag = math.log(x_int) / math.log(ref_max) if x_int > 1 else 0.0
    c_mag = min(1.0, max(0.0, c_mag))
    
    score = (0.50 * c_div) + (0.30 * c_digits) + (0.20 * c_mag)
    return round(score, 4)

# Keep alias for backward compatibility and test imports
score_number_difficulty = score_whole_or_decimal


def score_signed_integer(x: int, max_val: int) -> float:
    """Score signed integers, adding a small penalty for negative numbers."""
    abs_x = abs(x)
    abs_max = max(abs(max_val), 1)
    base_score = score_whole_or_decimal(abs_x, abs_max)
    
    # Negative numbers add 15% difficulty due to cognitive load of signs
    if x < 0:
        base_score = min(1.0, base_score + 0.15)
    return round(base_score, 4)


def score_fraction(n: int, d: int, max_den: int) -> float:
    """
    Score a fraction n/d based on:
    - Denominator size (40%)
    - Numerator/Denominator ratio (40% - improper fractions are harder)
    - Reduction/Simplification state (20% - unsimplified is harder)
    """
    if d <= 0 or n < 0:
        return 0.0
        
    # Denominator magnitude difficulty
    c_den = d / max(max_den, 2)
    
    # Proper vs improper fraction complexity
    ratio = n / d
    c_ratio = min(1.0, ratio)
    if ratio > 1.0:
        c_ratio = min(1.0, c_ratio + 0.20) # Improper fraction penalty
        
    # Is it simplified? (conceptually harder if GCD > 1 because it requires reduction)
    gcd_nd = math.gcd(n, d)
    c_reduced = 0.0 if gcd_nd == 1 else 1.0
    
    score = (0.40 * c_den) + (0.40 * c_ratio) + (0.20 * c_reduced)
    return round(score, 4)


def score_ordinal(index: int, max_index: int) -> float:
    """Ordinal difficulty scales linearly with magnitude (1st is easiest, 100th is hardest)."""
    if max_index <= 1:
        return 0.0
    val = (index - 1) / (max_index - 1)
    return round(val, 4)


def score_candidate(val: Any, max_val: Any, num_type: str, max_den: int = 10, decimal_places: int = 0) -> float:
    """Unified scoring router based on number type."""
    if num_type == "fraction":
        if isinstance(val, tuple) and len(val) == 2:
            return score_fraction(val[0], val[1], max_den)
        return 0.5
    if num_type == "integer":
        return score_signed_integer(int(val), int(max_val))
    if num_type == "ordinal":
        return score_ordinal(int(val), int(max_val))
    # Default: whole number or decimal
    return score_whole_or_decimal(val, max_val, decimal_places)


# ─── UTILITIES ────────────────────────────────────────────────────────────────

def _count_decimal_places(v: Any) -> int:
    if not isinstance(v, (int, float)):
        return 0
    if isinstance(v, int) or v.is_integer():
        return 0
    s = f"{v:.15f}".rstrip("0")
    if "." in s:
        return len(s.split(".")[1])
    return 0


# ─── UNIFIED WINDOW SAMPLING GENERATORS ────────────────────────────────────────

def generate_number_by_window(
    candidates: List[Any],
    scalar: float,
    d: int,
    rng: random.Random,
    num_type: str = "whole",
    max_den: int = 10
) -> Any:
    """
    Choose a number randomly from the candidates list within the difficulty range window.
    Works with whole numbers, signed integers, decimals, fractions, and ordinals.
    """
    if not candidates:
        raise ValueError("Candidates list cannot be empty")
        
    unique_candidates = list(set(candidates))
    
    # Calculate scale parameters
    if num_type == "fraction":
        # Sort fractions by computed score
        scored_candidates = []
        for val in unique_candidates:
            score = score_candidate(val, None, num_type, max_den)
            scored_candidates.append((val, score))
    else:
        # Sort values
        unique_candidates = sorted(unique_candidates)
        max_val = unique_candidates[-1]
        decimal_places = max(_count_decimal_places(v) for v in unique_candidates) if num_type == "whole" else 0
        
        scored_candidates = []
        for val in unique_candidates:
            score = score_candidate(val, max_val, num_type, decimal_places=decimal_places)
            scored_candidates.append((val, score))
            
    # Compute window bounds
    w = 1.0 / d
    t_lo = scalar * (1.0 - w)
    t_hi = t_lo + w
    
    t_lo = max(0.0, min(1.0, t_lo))
    t_hi = max(0.0, min(1.0, t_hi))
    
    window_candidates = []
    for val, score in scored_candidates:
        if t_lo <= score <= t_hi:
            window_candidates.append(val)
            
    if window_candidates:
        return rng.choice(window_candidates)
        
    # Fallback: Closest to window center
    t_mid = (t_lo + t_hi) / 2.0
    scored_candidates.sort(key=lambda item: abs(item[1] - t_mid))
    return scored_candidates[0][0]


def generate_pair_by_window(
    candidate_pairs: List[Tuple[Any, Any]],
    scalar: float,
    d: int,
    rng: random.Random,
    num_type: str = "whole",
    max_den: int = 10
) -> Tuple[Any, Any]:
    """
    Choose an operand pair randomly from candidate_pairs within the difficulty range window.
    Works with all K-12 MATATAG number sets.
    """
    if not candidate_pairs:
        raise ValueError("Candidate pairs list cannot be empty")
        
    # Find max values for magnitude scaling
    if num_type == "fraction":
        scored_pairs = []
        for a, b in candidate_pairs:
            s_a = score_candidate(a, None, num_type, max_den)
            s_b = score_candidate(b, None, num_type, max_den)
            score = round(math.sqrt((s_a**2 + s_b**2) / 2.0), 4)
            scored_pairs.append(((a, b), score))
    else:
        max_val = max(max(abs(a), abs(b)) if num_type == "integer" else max(a, b) for a, b in candidate_pairs)
        decimal_places = max(
            max(_count_decimal_places(a), _count_decimal_places(b))
            for a, b in candidate_pairs
        ) if num_type == "whole" else 0
        
        scored_pairs = []
        for a, b in candidate_pairs:
            s_a = score_candidate(a, max_val, num_type, decimal_places=decimal_places)
            s_b = score_candidate(b, max_val, num_type, decimal_places=decimal_places)
            score = round(math.sqrt((s_a**2 + s_b**2) / 2.0), 4)
            scored_pairs.append(((a, b), score))
            
    # Compute window bounds
    w = 1.0 / d
    t_lo = scalar * (1.0 - w)
    t_hi = t_lo + w
    
    t_lo = max(0.0, min(1.0, t_lo))
    t_hi = max(0.0, min(1.0, t_hi))
    
    window_pairs = []
    for pair, score in scored_pairs:
        if t_lo <= score <= t_hi:
            window_pairs.append(pair)
            
    if window_pairs:
        return rng.choice(window_pairs)
        
    t_mid = (t_lo + t_hi) / 2.0
    scored_pairs.sort(key=lambda item: abs(item[1] - t_mid))
    return scored_pairs[0][0]
