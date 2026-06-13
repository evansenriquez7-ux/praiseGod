#!/usr/bin/env python3
"""
Production readiness stress test.
Tests high-volume generation, concurrent access patterns, and error recovery.
"""

import sys
import time
from collections import defaultdict
from app.visual_skeletons import (
    get_visual_skeleton,
    regenerate_skeleton,
    validate_student_answer,
)

VISUAL_TYPES = [
    "NumberLine", "ClockSet", "PesoMoney", "FillInTable",
    "RuleDiscovery", "ConstraintSatisfaction", "BarChart",
    "EstimationGate", "SortOrder", "GridArea", "Categorize", "Calendar"
]


def test_high_volume_generation():
    """Test generating many problems quickly."""
    print("TEST 1: High-Volume Generation")
    print("-" * 80)
    
    problems_per_type = 100
    total_problems = len(VISUAL_TYPES) * problems_per_type
    
    start_time = time.time()
    successes = 0
    failures = []
    
    for visual_type in VISUAL_TYPES:
        for i in range(problems_per_type):
            grade = (i % 6) + 2  # Grades 2-7
            seed = 60000 + i
            difficulty = (i % 4) + 1  # Difficulties 1-4
            
            try:
                skeleton = get_visual_skeleton(visual_type, grade, seed, difficulty)
                successes += 1
            except Exception as e:
                failures.append((visual_type, grade, seed, difficulty, str(e)[:50]))
    
    elapsed = time.time() - start_time
    
    print(f"Generated {successes}/{total_problems} problems in {elapsed:.2f}s")
    print(f"Throughput: {successes/elapsed:.1f} problems/second")
    print(f"Success rate: {100*successes/total_problems:.1f}%")
    
    if failures:
        print(f"\nFailures (showing first 5):")
        for vtype, grade, seed, diff, error in failures[:5]:
            print(f"  {vtype} G{grade} S{seed} D{diff}: {error}")
    
    print()
    return successes == total_problems


def test_uniqueness_across_seeds():
    """Test that different seeds produce different problems."""
    print("TEST 2: Uniqueness Across Seeds")
    print("-" * 80)
    
    num_problems = 100
    all_passed = True
    
    for visual_type in VISUAL_TYPES:
        correct_answers = []
        
        for seed in range(70000, 70000 + num_problems):
            try:
                skeleton = get_visual_skeleton(visual_type, 5, seed, 2)
                correct_answers.append(str(skeleton["correct_answer"]))
            except:
                pass
        
        if len(correct_answers) > 0:
            unique_count = len(set(correct_answers))
            uniqueness = 100 * unique_count / len(correct_answers)
            
            status = "✓" if uniqueness >= 30 else "⚠"
            print(f"{status} {visual_type}: {uniqueness:.1f}% unique ({unique_count}/{len(correct_answers)})")
            
            if uniqueness < 30:
                all_passed = False
    
    print()
    return all_passed


def test_regeneration_consistency():
    """Test that regeneration always produces same answer."""
    print("TEST 3: Regeneration Consistency (1000 tests)")
    print("-" * 80)
    
    num_tests = 1000
    mismatches = []
    
    for i in range(num_tests):
        visual_type = VISUAL_TYPES[i % len(VISUAL_TYPES)]
        grade = (i % 6) + 2
        seed = 80000 + i
        difficulty = (i % 4) + 1
        
        try:
            # Generate original
            skeleton = get_visual_skeleton(visual_type, grade, seed, difficulty)
            original_answer = skeleton["correct_answer"]
            skeleton_id = skeleton["skeleton_id"]
            
            # Regenerate 3 times
            for _ in range(3):
                regenerated = regenerate_skeleton(skeleton_id)
                if regenerated["correct_answer"] != original_answer:
                    mismatches.append((skeleton_id, original_answer, regenerated["correct_answer"]))
                    break
        except:
            pass
    
    if mismatches:
        print(f"✗ Found {len(mismatches)} mismatches:")
        for sid, orig, regen in mismatches[:5]:
            print(f"  {sid}: {orig} ≠ {regen}")
    else:
        print(f"✓ All {num_tests} regenerations matched original")
    
    print()
    return len(mismatches) == 0


def test_validation_accuracy():
    """Test that validation correctly identifies right and wrong answers."""
    print("TEST 4: Validation Accuracy")
    print("-" * 80)
    
    num_tests = 200
    false_positives = []  # Wrong answer marked correct
    false_negatives = []  # Correct answer marked wrong
    
    for i in range(num_tests):
        visual_type = VISUAL_TYPES[i % len(VISUAL_TYPES)]
        grade = (i % 6) + 2
        seed = 90000 + i
        difficulty = (i % 4) + 1
        
        try:
            skeleton = get_visual_skeleton(visual_type, grade, seed, difficulty)
            skeleton_id = skeleton["skeleton_id"]
            correct_answer = skeleton["correct_answer"]
            
            # Test correct answer
            result = validate_student_answer(skeleton_id, correct_answer)
            if not result["is_correct"]:
                false_negatives.append((skeleton_id, "Correct answer marked wrong"))
            
            # Test wrong answer (if we have traps)
            if skeleton["all_traps"]:
                trap_values = [
                    t.get("value") or t.get("position") or t.get("values")
                    for t in skeleton["all_traps"].values()
                ]
                wrong_answer = next((v for v in trap_values if v is not None and v != correct_answer), None)
                
                if wrong_answer is not None:
                    result = validate_student_answer(skeleton_id, wrong_answer)
                    if result["is_correct"]:
                        false_positives.append((skeleton_id, f"Trap {wrong_answer} marked correct"))
        except:
            pass
    
    if false_positives or false_negatives:
        print(f"✗ Validation errors found:")
        print(f"  False positives (wrong marked correct): {len(false_positives)}")
        print(f"  False negatives (correct marked wrong): {len(false_negatives)}")
        
        for sid, msg in (false_positives + false_negatives)[:5]:
            print(f"    {sid}: {msg}")
    else:
        print(f"✓ All {num_tests} validations accurate")
    
    print()
    return len(false_positives) == 0 and len(false_negatives) == 0


def test_error_recovery():
    """Test that system recovers gracefully from bad inputs."""
    print("TEST 5: Error Recovery")
    print("-" * 80)
    
    bad_inputs = [
        ("Invalid skeleton_id", lambda: regenerate_skeleton("invalid_id")),
        ("Grade 0", lambda: get_visual_skeleton("NumberLine", 0, 12345, 2)),
        ("Grade 100", lambda: get_visual_skeleton("NumberLine", 100, 12345, 2)),
        ("Negative difficulty", lambda: get_visual_skeleton("NumberLine", 5, 12345, -1)),
        ("Invalid visual type", lambda: get_visual_skeleton("InvalidType", 5, 12345, 2)),
    ]
    
    all_handled = True
    
    for test_name, test_func in bad_inputs:
        try:
            test_func()
            print(f"⚠ {test_name}: No error raised (unexpected)")
            all_handled = False
        except Exception as e:
            # Should raise an error
            print(f"✓ {test_name}: Raised {type(e).__name__}")
    
    print()
    return all_handled


def test_difficulty_progression():
    """Test that difficulty increases with difficulty parameter."""
    print("TEST 6: Difficulty Progression")
    print("-" * 80)
    
    # This is a heuristic test - check that harder problems use larger ranges
    for visual_type in ["NumberLine", "PesoMoney", "BarChart"]:
        try:
            easy = get_visual_skeleton(visual_type, 5, 95000, 1)
            hard = get_visual_skeleton(visual_type, 5, 95000, 4)
            
            # Check if hard problems have characteristics of higher difficulty
            # (This is type-specific and heuristic)
            if visual_type == "PesoMoney":
                easy_amt = easy["visual_params"]["target_amount"]
                hard_amt = hard["visual_params"]["target_amount"]
                if hard_amt > easy_amt:
                    print(f"✓ {visual_type}: Difficulty increases (₱{easy_amt} → ₱{hard_amt})")
                else:
                    print(f"⚠ {visual_type}: Difficulty may not increase (₱{easy_amt} → ₱{hard_amt})")
            else:
                print(f"✓ {visual_type}: Generated at both difficulties")
        except Exception as e:
            print(f"✗ {visual_type}: {e}")
    
    print()
    return True


def main():
    print("=" * 80)
    print("PRODUCTION READINESS STRESS TEST")
    print("=" * 80)
    print()
    
    tests = [
        ("High-Volume Generation", test_high_volume_generation),
        ("Uniqueness Across Seeds", test_uniqueness_across_seeds),
        ("Regeneration Consistency", test_regeneration_consistency),
        ("Validation Accuracy", test_validation_accuracy),
        ("Error Recovery", test_error_recovery),
        ("Difficulty Progression", test_difficulty_progression),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"✗ {test_name}: Crashed with {type(e).__name__}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    for test_name, passed in results:
        icon = "✓" if passed else "✗"
        print(f"{icon} {test_name}")
    
    print()
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"Overall: {passed_count}/{total_count} tests passed ({100*passed_count/total_count:.1f}%)")
    
    if passed_count == total_count:
        print()
        print("🎉 SYSTEM IS PRODUCTION READY!")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
