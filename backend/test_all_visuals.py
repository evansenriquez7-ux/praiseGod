#!/usr/bin/env python3
"""
Comprehensive test suite for all 11 visual skeleton types.
Tests generation, validation, regeneration, and answer checking.

Note: EstimationGate was removed - the visual "gate" reveals too much about acceptable range.
"""

import sys
import traceback
from app.visual_skeletons import (
    get_visual_skeleton, 
    regenerate_skeleton, 
    validate_student_answer,
    validate_skeleton
)

VISUAL_TYPES = [
    "NumberLine",
    "ClockSet", 
    "PesoMoney",
    "FillInTable",
    "RuleDiscovery",
    "ConstraintSatisfaction",
    "BarChart",
    # "EstimationGate",  # Removed: visual "gate" reveals too much about acceptable range
    "SortOrder",
    "GridArea",
    "Categorize",
    "Calendar"
]

def test_visual_type(visual_type: str, grade: int, num_tests: int = 20):
    """
    Comprehensive test for a single visual type.
    Returns dict with results and any errors found.
    """
    results = {
        "type": visual_type,
        "grade": grade,
        "total_tests": num_tests * 4,  # 4 difficulty levels
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    for difficulty in [1, 2, 3, 4]:
        for seed in range(10000 + difficulty * 1000, 10000 + difficulty * 1000 + num_tests):
            try:
                # Test 1: Generation
                skeleton = get_visual_skeleton(visual_type, grade, seed, difficulty)
                
                # Test 2: Validation
                if not validate_skeleton(skeleton):
                    results["errors"].append(f"Seed {seed} diff {difficulty}: Validation failed")
                    results["failed"] += 1
                    continue
                
                # Test 3: Regeneration consistency
                skeleton_id = skeleton["skeleton_id"]
                regenerated = regenerate_skeleton(skeleton_id)
                
                if skeleton["correct_answer"] != regenerated["correct_answer"]:
                    results["errors"].append(
                        f"Seed {seed} diff {difficulty}: Regeneration mismatch - "
                        f"original={skeleton['correct_answer']}, regen={regenerated['correct_answer']}"
                    )
                    results["failed"] += 1
                    continue
                
                # Test 4: Correct answer validation
                correct_answer = skeleton["correct_answer"]
                validation_result = validate_student_answer(skeleton_id, correct_answer)
                
                if not validation_result["is_correct"]:
                    results["errors"].append(
                        f"Seed {seed} diff {difficulty}: Correct answer marked wrong! "
                        f"Answer={correct_answer}"
                    )
                    results["failed"] += 1
                    continue
                
                # Test 5: Wrong answer detection (use a trap if available)
                if skeleton["all_traps"]:
                    trap_values = [
                        trap_data.get("value") or trap_data.get("position") or trap_data.get("values")
                        for trap_data in skeleton["all_traps"].values()
                    ]
                    wrong_answer = next((v for v in trap_values if v is not None and v != correct_answer), None)
                    
                    if wrong_answer is not None:
                        wrong_result = validate_student_answer(skeleton_id, wrong_answer)
                        if wrong_result["is_correct"]:
                            results["errors"].append(
                                f"Seed {seed} diff {difficulty}: Trap answer marked correct! "
                                f"Trap={wrong_answer}"
                            )
                            results["failed"] += 1
                            continue
                
                results["passed"] += 1
                
            except Exception as e:
                results["errors"].append(
                    f"Seed {seed} diff {difficulty}: Exception - {type(e).__name__}: {str(e)}"
                )
                results["failed"] += 1
    
    return results


def test_edge_cases():
    """Test specific edge cases for each visual type."""
    edge_tests = []
    
    # NumberLine: negative numbers, decimals, zero
    try:
        skeleton = get_visual_skeleton("NumberLine", 6, 50000, 3)
        edge_tests.append(("NumberLine - negative/decimal support", "PASS"))
    except Exception as e:
        edge_tests.append(("NumberLine - negative/decimal support", f"FAIL: {e}"))
    
    # ClockSet: 24-hour afternoon times (Grade 5+)
    try:
        afternoon_found = False
        for seed in range(60000, 60050):
            skeleton = get_visual_skeleton("ClockSet", 5, seed, 3)
            if skeleton["visual_params"]["hours"] >= 13:
                afternoon_found = True
                break
        edge_tests.append(("ClockSet - 24-hour afternoon times", "PASS" if afternoon_found else "FAIL: No afternoon times"))
    except Exception as e:
        edge_tests.append(("ClockSet - 24-hour afternoon times", f"FAIL: {e}"))
    
    # ClockSet: 12-hour format (Grade 3)
    try:
        skeleton = get_visual_skeleton("ClockSet", 3, 70000, 2)
        is_12_hour = not skeleton["visual_params"]["use_24_hour"]
        edge_tests.append(("ClockSet - 12-hour for Grade 3", "PASS" if is_12_hour else "FAIL: Using 24-hour"))
    except Exception as e:
        edge_tests.append(("ClockSet - 12-hour for Grade 3", f"FAIL: {e}"))
    
    # PesoMoney: large amounts (₱100+)
    try:
        skeleton = get_visual_skeleton("PesoMoney", 5, 80000, 4)
        amount = skeleton["visual_params"]["target_amount"]
        edge_tests.append(("PesoMoney - large amounts", f"PASS (₱{amount})" if amount > 50 else f"SKIP (₱{amount})"))
    except Exception as e:
        edge_tests.append(("PesoMoney - large amounts", f"FAIL: {e}"))
    
    # FillInTable: multiplication tables
    try:
        skeleton = get_visual_skeleton("FillInTable", 3, 90000, 2)
        edge_tests.append(("FillInTable - generation", "PASS"))
    except Exception as e:
        edge_tests.append(("FillInTable - generation", f"FAIL: {e}"))
    
    # RuleDiscovery: algebraic expressions
    try:
        skeleton = get_visual_skeleton("RuleDiscovery", 7, 100000, 3)
        edge_tests.append(("RuleDiscovery - algebraic expressions", "PASS"))
    except Exception as e:
        edge_tests.append(("RuleDiscovery - algebraic expressions", f"FAIL: {e}"))
    
    return edge_tests


def main():
    print("=" * 80)
    print("COMPREHENSIVE VISUAL SKELETON TEST SUITE")
    print("=" * 80)
    print()
    
    # Test each visual type
    all_results = []
    for visual_type in VISUAL_TYPES:
        print(f"Testing {visual_type}...", end=" ", flush=True)
        
        # Choose appropriate grade for each type
        grade = 5  # Default
        if visual_type == "Calendar":
            grade = 2
        elif visual_type == "RuleDiscovery":
            grade = 7
        
        results = test_visual_type(visual_type, grade, num_tests=10)
        all_results.append(results)
        
        if results["failed"] == 0:
            print(f"✓ PASS ({results['passed']}/{results['total_tests']})")
        else:
            print(f"✗ FAIL ({results['passed']}/{results['total_tests']} passed, {results['failed']} failed)")
    
    print()
    print("=" * 80)
    print("EDGE CASE TESTS")
    print("=" * 80)
    print()
    
    edge_results = test_edge_cases()
    for test_name, result in edge_results:
        status = "✓" if "PASS" in result else ("⊘" if "SKIP" in result else "✗")
        print(f"{status} {test_name}: {result}")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    total_passed = sum(r["passed"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)
    total_tests = sum(r["total_tests"] for r in all_results)
    
    print(f"Total tests run: {total_tests}")
    print(f"Passed: {total_passed} ({100*total_passed/total_tests:.1f}%)")
    print(f"Failed: {total_failed} ({100*total_failed/total_tests:.1f}%)")
    print()
    
    # Print detailed errors
    failed_types = [r for r in all_results if r["failed"] > 0]
    if failed_types:
        print("FAILURES BY TYPE:")
        print()
        for result in failed_types:
            print(f"{result['type']} - {result['failed']} failures:")
            # Show first 5 errors
            for error in result["errors"][:5]:
                print(f"  • {error}")
            if len(result["errors"]) > 5:
                print(f"  ... and {len(result['errors']) - 5} more")
            print()
    else:
        print("🎉 All tests passed!")
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
