"""
Divisibility Module

Scores numbers by their divisibility difficulty and selects numbers that match
a target divisibility difficulty for curriculum-driven problem generation.

Divisibility Difficulty Scale (0.0-1.0):
- 0.0: Very divisible (100, 50, 30) - easy mental math
- 0.5: Moderately divisible (24, 35, 40)
- 1.0: Prime-like (97, 83, 67) - hardest mental math

Author: CCMed Team
"""

import random
from typing import Dict, List


def is_prime(n: int) -> bool:
    """
    Check if a number is prime.
    
    Args:
        n: Number to check
    
    Returns:
        True if prime
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Check odd divisors up to sqrt(n)
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    
    return True


def divisibility_difficulty(n: int) -> float:
    """
    Score a number's divisibility difficulty from 0.0 (easiest) to 1.0 (hardest).
    
    Factors considered:
    - Trailing zeros (100, 50, 10) → very easy
    - Divisibility by 10, 5, 2, 3 → easier
    - Small magnitude → easier
    - Prime numbers → hardest
    - "Looks prime" (ends in 1,3,7,9 but isn't) → hard
    
    Args:
        n: Number to score (must be positive integer)
    
    Returns:
        Difficulty score from 0.0 to 1.0
    
    Examples:
        >>> divisibility_difficulty(100)
        0.0   # Very easy (trailing zeros, divisible by everything)
        >>> divisibility_difficulty(50)
        0.05  # Very easy
        >>> divisibility_difficulty(24)
        0.4   # Medium (divisible by 2, 3)
        >>> divisibility_difficulty(97)
        0.95  # Very hard (prime)
    """
    if n <= 0:
        return 0.5  # Neutral for invalid input
    
    score = 0.5  # Start neutral
    
    # Trailing zeros bonus (very round numbers)
    trailing_zeros = len(str(n)) - len(str(n).rstrip('0'))
    score -= trailing_zeros * 0.15
    
    # Divisibility bonuses (cumulative)
    if n % 10 == 0:
        score -= 0.15
    if n % 5 == 0:
        score -= 0.10
    if n % 2 == 0:
        score -= 0.08
    if n % 3 == 0:
        score -= 0.05
    
    # Prime penalty (harder to work with)
    if is_prime(n):
        score += 0.35
    
    # "Looks prime" penalty (ends in 1, 3, 7, 9 but not prime)
    if n % 10 in [1, 3, 7, 9] and not is_prime(n) and n > 10:
        score += 0.15
    
    # Small number bonus (easier mental math)
    if n <= 10:
        score -= 0.20
    elif n <= 25:
        score -= 0.12
    elif n <= 50:
        score -= 0.05
    
    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, score))


# Precomputed divisibility buckets for fast lookup
_DIVISIBILITY_BUCKETS = None


def _init_buckets(max_value: int = 10000) -> Dict[str, List[int]]:
    """
    Precompute divisibility buckets for numbers 1 to max_value.
    
    Buckets:
    - very_easy: 0.0-0.2
    - easy: 0.2-0.4
    - medium: 0.4-0.6
    - hard: 0.6-0.8
    - very_hard: 0.8-1.0
    """
    buckets = {
        'very_easy': [],
        'easy': [],
        'medium': [],
        'hard': [],
        'very_hard': [],
    }
    
    for n in range(1, max_value + 1):
        score = divisibility_difficulty(n)
        if score < 0.2:
            buckets['very_easy'].append(n)
        elif score < 0.4:
            buckets['easy'].append(n)
        elif score < 0.6:
            buckets['medium'].append(n)
        elif score < 0.8:
            buckets['hard'].append(n)
        else:
            buckets['very_hard'].append(n)
    
    return buckets


def get_divisibility_buckets(max_value: int = 10000) -> Dict[str, List[int]]:
    """Get or initialize divisibility buckets."""
    global _DIVISIBILITY_BUCKETS
    if _DIVISIBILITY_BUCKETS is None:
        _DIVISIBILITY_BUCKETS = _init_buckets(max_value)
    return _DIVISIBILITY_BUCKETS


def select_number_by_divisibility(
    min_val: int,
    max_val: int,
    target_difficulty: float,
    rng: random.Random,
    tolerance: float = 0.15
) -> int:
    """
    Select a number from [min_val, max_val] whose divisibility difficulty
    is close to target_difficulty.
    
    Uses precomputed buckets for efficiency on large ranges.
    
    Args:
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)
        target_difficulty: Target divisibility difficulty (0.0-1.0)
        rng: Random number generator
        tolerance: Acceptable error from target (default 0.15)
    
    Returns:
        Selected number
    
    Example:
        >>> rng = random.Random(42)
        >>> select_number_by_divisibility(10, 100, 0.2, rng)
        25  # Easy divisibility (multiple of 5)
        >>> select_number_by_divisibility(10, 100, 0.8, rng)
        97  # Hard divisibility (prime)
    """
    if min_val > max_val:
        return min_val
    
    # For small ranges, use direct scoring
    if max_val - min_val < 100:
        candidates = range(min_val, max_val + 1)
        scored = [(n, divisibility_difficulty(n)) for n in candidates]
        
        # Find matches within tolerance
        matches = [n for n, score in scored 
                  if abs(score - target_difficulty) <= tolerance]
        
        if matches:
            return rng.choice(matches)
        
        # Fallback: closest match
        scored.sort(key=lambda x: abs(x[1] - target_difficulty))
        return scored[0][0]
    
    # For large ranges, use bucket lookup
    buckets = get_divisibility_buckets()
    
    # Map target_difficulty to bucket
    if target_difficulty < 0.2:
        bucket_name = 'very_easy'
    elif target_difficulty < 0.4:
        bucket_name = 'easy'
    elif target_difficulty < 0.6:
        bucket_name = 'medium'
    elif target_difficulty < 0.8:
        bucket_name = 'hard'
    else:
        bucket_name = 'very_hard'
    
    # Filter bucket to valid range
    pool = [n for n in buckets[bucket_name] if min_val <= n <= max_val]
    
    if pool:
        return rng.choice(pool)
    
    # Fallback: try adjacent buckets
    bucket_order = ['very_easy', 'easy', 'medium', 'hard', 'very_hard']
    bucket_idx = bucket_order.index(bucket_name)
    
    for offset in [1, -1, 2, -2]:
        adj_idx = bucket_idx + offset
        if 0 <= adj_idx < len(bucket_order):
            adj_pool = [n for n in buckets[bucket_order[adj_idx]] 
                       if min_val <= n <= max_val]
            if adj_pool:
                return rng.choice(adj_pool)
    
    # Last resort: random from range
    return rng.randint(min_val, max_val)
