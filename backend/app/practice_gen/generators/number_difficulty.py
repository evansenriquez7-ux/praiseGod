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


def _magnitude_key(num_type: str):
    """Order candidates by magnitude. Fractions compare by value, not by the
    tuple's lexicographic order (which would rank 1/2 below 1/10)."""
    if num_type == "fraction":
        return lambda v: v[0] / v[1]
    return lambda v: v


def _magnitude_edge_band(magnitudes: dict, scalar: float, w: float) -> List[Any]:
    """
    The top (scalar 1.0) or bottom (scalar 0.0) `w`-fraction of the pool by
    magnitude, as a list of candidate keys.

    Why the endpoints need this at all: `score_candidate` scores *awkwardness*,
    not size — 99 scores 0.95 while 100 scores 0.54, because a round number is
    the easier item. For some pools the two are anti-correlated, so the top score
    band can sit far below the pool ceiling: mat_g2_na_q3_0's hardest band is
    products 27-45 against a competency maximum of 100, whose 10 x 10 is too
    round to score high. Sampling the score band alone therefore made the top of
    the competency's stated range unreachable at *any* setting, which is exactly
    the gap §1A-reach exists to catch — it had been masked by the old argmax
    short-circuit, which passed reach for the wrong reason (it maximised size,
    not difficulty). Injecting the single extreme was not enough either: one
    member among seven gives a 74% chance of being drawn across the 10 samples
    §1A-reach takes, and seven multiplication nodes duly failed.

    So the difficulty maximum is "hardest OR largest", and near-ceiling items are
    a substantial share of the band rather than a lottery ticket. `w` is the
    window width already in use for interior scalars; no new constant.
    """
    if not magnitudes:
        return []
    lo, hi = min(magnitudes.values()), max(magnitudes.values())
    if hi <= lo:
        return list(magnitudes.keys())
    if scalar == 1.0:
        cut = hi - w * (hi - lo)
        return [k for k, m in magnitudes.items() if m >= cut]
    cut = lo + w * (hi - lo)
    return [k for k, m in magnitudes.items() if m <= cut]


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
            
    # The endpoints deliberately go through the same window + rng.choice as
    # every other scalar. They used to short-circuit to argmax/argmin, which
    # ignored `rng` entirely and made the endpoint a single fixed item: over 30
    # seeds at scalar 1.0, 37 of 81 (node, dna, magnitude-axis) combinations
    # produced <= 2 distinct operand sets, and addition produced exactly 1
    # against 29 at scalar 0.5 — a teacher who set difficulty to maximum got
    # the identical question every time. §1A-reach could not see it: a pool
    # whose only near-ceiling member is always chosen satisfies "the peak
    # reaches the ceiling" perfectly. The window below already resolves
    # scalar 1.0 to [1-w, 1.0] and scalar 0.0 to [0.0, w], i.e. exactly the
    # endpoint bands. Those bands are not a drop-in replacement, though: they
    # are bands in *score* space, and the fast paths were maximising magnitude,
    # so the endpoints also need the magnitude widening applied below — see
    # _magnitude_edge_band.
    # §1A boundary exactness is unaffected: it asserts on the mapped
    # difficulty_profile ceiling, not on which operand the picker returns.

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

    # At the endpoints, widen the band to "hardest OR largest" (see
    # _magnitude_edge_band for why the score band alone leaves the competency
    # ceiling unreachable).
    if scalar in (0.0, 1.0):
        key = _magnitude_key(num_type)
        edge = _magnitude_edge_band({v: key(v) for v in unique_candidates}, scalar, w)
        window_candidates.extend(v for v in edge if v not in window_candidates)

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
            
    # Same removal as generate_by_window above, same reasoning: the endpoints
    # resolve through the window and `rng` rather than collapsing to the single
    # argmax/argmin pair. This is the branch responsible for "What is 10 x 10?"
    # being the only item a max-difficulty multiplication node ever served.

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

    # Same endpoint widening as generate_number_by_window. A pair's magnitude is
    # the sum of its operands' magnitudes: monotone in both, and so a proxy for
    # whatever the DNA finally computes from them (product, sum, difference)
    # without this module needing to know which.
    if scalar in (0.0, 1.0):
        key = _magnitude_key(num_type)
        edge = _magnitude_edge_band(
            {p: key(p[0]) + key(p[1]) for p in candidate_pairs}, scalar, w
        )
        window_pairs.extend(p for p in edge if p not in window_pairs)

    if window_pairs:
        return rng.choice(window_pairs)

    t_mid = (t_lo + t_hi) / 2.0
    scored_pairs.sort(key=lambda item: abs(item[1] - t_mid))
    return scored_pairs[0][0]
