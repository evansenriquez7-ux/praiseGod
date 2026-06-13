import random
from .generators.number_difficulty import (
    score_number_difficulty,
    generate_number_by_window,
    generate_pair_by_window,
    score_candidate,
)

def test_score_number_difficulty():
    score_30 = score_number_difficulty(30, 1000)
    score_17 = score_number_difficulty(17, 1000)
    score_997 = score_number_difficulty(997, 1000)
    
    assert score_30 < score_17
    assert score_17 < score_997

def test_generate_number_by_window_ranges():
    rng = random.Random(42)
    candidates = list(range(10, 101))
    
    easy_num = generate_number_by_window(candidates, scalar=0.0, d=5, rng=rng)
    hard_num = generate_number_by_window(candidates, scalar=1.0, d=5, rng=rng)
    
    assert 10 <= easy_num <= 100
    assert 10 <= hard_num <= 100
    assert score_candidate(easy_num, 100, "whole") < score_candidate(hard_num, 100, "whole")

def test_generate_odd_numbers_to_100():
    rng = random.Random(42)
    candidates = [x for x in range(1, 101) if x % 2 != 0]
    
    easy_odd = generate_number_by_window(candidates, scalar=0.0, d=5, rng=rng)
    hard_odd = generate_number_by_window(candidates, scalar=1.0, d=5, rng=rng)
    
    assert easy_odd in candidates
    assert hard_odd in candidates
    assert score_candidate(easy_odd, 100, "whole") < score_candidate(hard_odd, 100, "whole")

def test_generate_decimals():
    rng = random.Random(42)
    candidates = [0.1, 0.125, 0.2, 0.25, 0.333, 0.5, 0.75, 1.0]
    
    easy_decimal = generate_number_by_window(candidates, scalar=0.0, d=5, rng=rng)
    hard_decimal = generate_number_by_window(candidates, scalar=1.0, d=5, rng=rng)
    
    assert easy_decimal in candidates
    assert hard_decimal in candidates
    
    score_easy = score_candidate(easy_decimal, 1.0, "whole", decimal_places=3)
    score_hard = score_candidate(hard_decimal, 1.0, "whole", decimal_places=3)
    
    assert score_easy < score_hard

def test_signed_integers():
    # Negative number should have higher complexity score than positive counterpart
    pos_score = score_candidate(15, 100, "integer")
    neg_score = score_candidate(-15, 100, "integer")
    assert neg_score > pos_score

def test_fractions():
    # Simple proper fraction vs unsimplified vs improper
    score_half = score_candidate((1, 2), None, "fraction", max_den=8)
    score_unsimp = score_candidate((2, 4), None, "fraction", max_den=8)
    score_improper = score_candidate((9, 8), None, "fraction", max_den=8)
    
    assert score_half < score_unsimp
    assert score_half < score_improper

def test_ordinals():
    score_1st = score_candidate(1, 100, "ordinal")
    score_50th = score_candidate(50, 100, "ordinal")
    score_100th = score_candidate(100, 100, "ordinal")
    
    assert score_1st < score_50th < score_100th

def test_generate_fractions_by_window():
    rng = random.Random(42)
    candidates = [(1, 2), (2, 3), (3, 4), (5, 8), (7, 8), (9, 8)]
    
    easy_frac = generate_number_by_window(candidates, scalar=0.0, d=5, rng=rng, num_type="fraction", max_den=8)
    hard_frac = generate_number_by_window(candidates, scalar=1.0, d=5, rng=rng, num_type="fraction", max_den=8)
    
    assert easy_frac in candidates
    assert hard_frac in candidates
    assert score_candidate(easy_frac, None, "fraction", max_den=8) < score_candidate(hard_frac, None, "fraction", max_den=8)

def test_generate_count_by_1():
    rng = random.Random(42)
    # Simulate candidates for count by 1 up to 100
    skip_by = 1
    max_num = 100
    candidates = [(i * skip_by, 0) for i in range((max_num // max(1, skip_by)) + 1)]
    
    easy_start = generate_pair_by_window(candidates, scalar=0.0, d=5, rng=rng)
    hard_start = generate_pair_by_window(candidates, scalar=1.0, d=5, rng=rng)
    
    assert easy_start in candidates
    assert hard_start in candidates
    assert score_candidate(easy_start[0], max_num, "whole") < score_candidate(hard_start[0], max_num, "whole")
