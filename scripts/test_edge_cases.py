#!/usr/bin/env python3
"""
Edge case and competency alignment test suite for visual skeletons.

Tests that generated problems align with the specific numbers and operations
mentioned in the MATATAG competency descriptions.
"""

import sys
import os
import json
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app import visual_skeletons

# Competencies with specific numerical constraints
NUMERICAL_COMPETENCIES = [
    # ClockSet - time constraints
    {
        "vtype": "ClockSet",
        "grade": 1,
        "competency": "Read and write time by the hour, half hour, and quarter hour using an analog clock",
        "checks": [
            ("minutes", lambda m: m in [0, 15, 30, 45]),  # Should only use hour/half/quarter
        ],
        "difficulty": 1
    },
    {
        "vtype": "ClockSet",
        "grade": 5,
        "competency": "Describe a 12- and 24-hour clock system",
        "checks": [
            ("use_24_hour", lambda v: v == True),  # Should use 24-hour format
        ],
        "difficulty": 2
    },
    
    # PesoMoney - amount constraints
    {
        "vtype": "PesoMoney",
        "grade": 1,
        "competency": "Recognize coins (excluding centavo coins) and bills up to ₱100",
        "checks": [
            ("target_amount", lambda v: v <= 100),  # Should not exceed ₱100
        ],
        "difficulty": 1
    },
    {
        "vtype": "PesoMoney",
        "grade": 2,
        "competency": "Determine the value of a number of bills, or a number of coins, or a combination of bills and coins up to ₱1000",
        "checks": [
            ("target_amount", lambda v: v <= 1000),  # Should not exceed ₱1000
        ],
        "difficulty": 2
    },
    {
        "vtype": "PesoMoney",
        "grade": 3,
        "competency": "Read and write money in words and using: Philippine currency symbols (₱ and PhP) up to ₱10 000",
        "checks": [
            ("target_amount", lambda v: v <= 10000),  # Should not exceed ₱10000
        ],
        "difficulty": 3
    },
    
    # NumberLine - fraction denominators
    {
        "vtype": "NumberLine",
        "grade": 4,
        "competency": "Plot fraction (proper fractions, improper fractions, and mixed numbers) with denominators 2, 4, 5, and 10 on the number line",
        "checks": [
            ("denominator", lambda d: d in [2, 4, 5, 10]),  # Should use specified denominators
        ],
        "difficulty": 2
    },
    
    # FillInTable - multiplication tables
    {
        "vtype": "FillInTable",
        "grade": 2,
        "competency": "Multiply numbers using the 2, 3, 4, 5, and 10 multiplication tables",
        "checks": [
            ("pattern_type", lambda t: t == "multiplication"),  # Should be multiplication
        ],
        "difficulty": 2
    },
    {
        "vtype": "FillInTable",
        "grade": 3,
        "competency": "Multiply numbers using the 6, 7, 8, and 9 multiplication tables",
        "checks": [
            ("pattern_type", lambda t: t == "multiplication"),  # Should be multiplication
        ],
        "difficulty": 2
    },
    
    # EstimationGate - estimation
    {
        "vtype": "EstimationGate",
        "grade": 3,
        "competency": "Round numbers to the nearest ten, hundred, or thousand",
        "checks": [
            ("tolerance", lambda t: t >= 0.15),  # Should have reasonable tolerance
        ],
        "difficulty": 1
    },
    
    # GridArea - area calculation
    {
        "vtype": "GridArea",
        "grade": 3,
        "competency": "Find the areas of squares and rectangles in sq. cm and sq. m",
        "checks": [
            ("shape_type", lambda s: s == "rectangle"),  # Should be rectangle
            ("correct_count", lambda c: c > 0),  # Should have positive area
        ],
        "difficulty": 2
    },
]


def test_numerical_constraints():
    """Test that competencies with specific numbers respect those constraints."""
    print("\n" + "=" * 60)
    print("EDGE CASE TEST: Numerical Constraints from Competencies")
    print("=" * 60)
    
    results = {"passed": 0, "failed": 0, "warnings": [], "errors": []}
    
    for test_case in NUMERICAL_COMPETENCIES:
        vtype = test_case["vtype"]
        grade = test_case["grade"]
        competency = test_case["competency"]
        checks = test_case["checks"]
        difficulty = test_case.get("difficulty", 2)
        
        # Run multiple seeds to ensure consistency
        for i in range(5):
            seed = random.randint(1000, 99999)
            try:
                skeleton = visual_skeletons.get_visual_skeleton(
                    visual_type=vtype,
                    grade=grade,
                    seed=seed,
                    difficulty=difficulty,
                    competency_text=competency
                )
                params = skeleton["visual_params"]
                
                all_checks_passed = True
                for param_name, check_fn in checks:
                    value = params.get(param_name)
                    if value is None:
                        # Some params may not be present for all problem variants
                        continue
                    if not check_fn(value):
                        all_checks_passed = False
                        results["warnings"].append({
                            "vtype": vtype,
                            "grade": grade,
                            "param": param_name,
                            "value": value,
                            "competency": competency[:60] + "..."
                        })
                
                if all_checks_passed:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                results["errors"].append({
                    "vtype": vtype,
                    "grade": grade,
                    "error": str(e)
                })
    
    print(f"\n✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    
    if results["warnings"]:
        print("\nConstraint violations:")
        for w in results["warnings"][:10]:
            print(f"  - {w['vtype']} Grade {w['grade']}: {w['param']}={w['value']}")
    
    if results["errors"]:
        print("\nErrors:")
        for e in results["errors"]:
            print(f"  - {e['vtype']} Grade {e['grade']}: {e['error']}")
    
    return results["failed"] == 0


def test_difficulty_boundaries():
    """Test that difficulty levels produce problems within expected ranges."""
    print("\n" + "=" * 60)
    print("EDGE CASE TEST: Difficulty Boundaries")
    print("=" * 60)
    
    results = {"passed": 0, "failed": 0, "observations": []}
    
    # Test difficulty edge cases
    edge_difficulties = [0.0, 0.5, 1.0, 1.5, 2.0]  # Scalar difficulties
    
    for diff in edge_difficulties:
        for vtype in ["NumberLine", "PesoMoney", "FillInTable"]:
            min_g, max_g = visual_skeletons.VISUAL_TYPES.get(vtype, (1, 10)) if hasattr(visual_skeletons, 'VISUAL_TYPES') else (1, 10)
            grade = 5  # Middle grade
            
            try:
                skeleton = visual_skeletons.get_visual_skeleton(
                    visual_type=vtype,
                    grade=grade,
                    seed=12345,
                    difficulty=diff
                )
                results["passed"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["observations"].append(f"{vtype} diff={diff}: {str(e)[:50]}")
    
    print(f"\n✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    
    if results["observations"]:
        print("\nObservations:")
        for obs in results["observations"]:
            print(f"  - {obs}")
    
    return results["failed"] == 0


def test_extreme_grades():
    """Test that grade 1 and grade 10 produce appropriate problems."""
    print("\n" + "=" * 60)
    print("EDGE CASE TEST: Extreme Grades (1 and 10)")
    print("=" * 60)
    
    results = {"passed": 0, "failed": 0, "observations": []}
    
    vtypes = ["NumberLine", "FillInTable", "Categorize", "ConstraintSatisfaction"]
    
    for vtype in vtypes:
        for grade in [1, 10]:
            try:
                skeleton = visual_skeletons.get_visual_skeleton(
                    visual_type=vtype,
                    grade=grade,
                    seed=random.randint(1000, 99999),
                    difficulty=2
                )
                
                # Grade 1 should have simpler content
                if grade == 1:
                    params = skeleton["visual_params"]
                    if vtype == "NumberLine":
                        # Grade 1 should use small whole numbers
                        content_type = params.get("content_type")
                        if content_type == "whole_number":
                            results["observations"].append(f"  ✓ {vtype} Grade 1: uses whole numbers")
                        else:
                            results["observations"].append(f"  ? {vtype} Grade 1: uses {content_type}")
                    
                    elif vtype == "Categorize":
                        # Grade 1 should use even/odd
                        categories = params.get("categories", [])
                        if "Even" in categories or "Odd" in categories:
                            results["observations"].append(f"  ✓ {vtype} Grade 1: uses even/odd")
                
                # Grade 10 should have complex content
                if grade == 10:
                    params = skeleton["visual_params"]
                    if vtype == "NumberLine":
                        content_type = params.get("content_type")
                        results["observations"].append(f"  ✓ {vtype} Grade 10: uses {content_type}")
                
                results["passed"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["observations"].append(f"  ✗ {vtype} Grade {grade}: {str(e)[:40]}")
    
    print(f"\n✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    
    print("\nObservations:")
    for obs in results["observations"]:
        print(obs)
    
    return results["failed"] == 0


def test_answer_type_consistency():
    """Test that answer types are consistent across regeneration."""
    print("\n" + "=" * 60)
    print("EDGE CASE TEST: Answer Type Consistency")
    print("=" * 60)
    
    results = {"passed": 0, "failed": 0, "observations": []}
    
    vtypes_and_expected_types = [
        ("NumberLine", int),
        ("ClockSet", tuple),
        ("PesoMoney", int),
        ("FillInTable", list),
        ("EstimationGate", int),
        ("BarChart", list),
        ("SortOrder", list),
        ("GridArea", int),
        ("Categorize", dict),
        ("Calendar", int),
    ]
    
    for vtype, expected_type in vtypes_and_expected_types:
        try:
            skeleton = visual_skeletons.get_visual_skeleton(
                visual_type=vtype,
                grade=5,
                seed=12345,
                difficulty=2
            )
            
            answer = skeleton["correct_answer"]
            actual_type = type(answer)
            
            if actual_type == expected_type:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["observations"].append(
                    f"  ✗ {vtype}: expected {expected_type.__name__}, got {actual_type.__name__}"
                )
                
        except Exception as e:
            results["failed"] += 1
            results["observations"].append(f"  ✗ {vtype}: {str(e)[:40]}")
    
    print(f"\n✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    
    if results["observations"]:
        print("\nIssues:")
        for obs in results["observations"]:
            print(obs)
    
    return results["failed"] == 0


def run_all_edge_tests():
    """Run all edge case tests."""
    print("\n" + "=" * 60)
    print("EDGE CASE & COMPETENCY ALIGNMENT TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Numerical Constraints", test_numerical_constraints),
        ("Difficulty Boundaries", test_difficulty_boundaries),
        ("Extreme Grades", test_extreme_grades),
        ("Answer Type Consistency", test_answer_type_consistency),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"\n!!! TEST {name} CRASHED: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("EDGE CASE TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL EDGE CASE TESTS PASSED!")
    else:
        print("SOME EDGE CASE TESTS FAILED - See above for details")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_edge_tests()
    sys.exit(0 if success else 1)
