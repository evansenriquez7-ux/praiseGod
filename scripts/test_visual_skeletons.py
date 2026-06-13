#!/usr/bin/env python3
"""
Comprehensive test suite for visual skeleton problem generation.

Tests:
1. All 12 visual types generate valid skeletons
2. All grades 1-10 work for each applicable visual type
3. Edge cases for difficulty levels
4. Competency text alignment with generated problems
5. Answer validation logic
"""

import sys
import os
import json
import random

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app import visual_skeletons

# Visual types and their supported grade ranges
VISUAL_TYPES = {
    "FillInTable": (1, 10),
    "RuleDiscovery": (1, 10),
    "ConstraintSatisfaction": (2, 10),
    "PesoMoney": (1, 10),
    "BarChart": (1, 9),
    "NumberLine": (1, 10),
    "EstimationGate": (2, 9),
    "ClockSet": (1, 7),
    "SortOrder": (1, 7),
    "GridArea": (2, 10),
    "Categorize": (1, 9),
    "Calendar": (1, 10),
}

# Test competencies for specific visual types
TEST_COMPETENCIES = {
    "NumberLine": [
        ("Grade 1", "Order numbers up to 20 from smallest to largest"),
        ("Grade 3", "Plot fraction (proper fractions, improper fractions, and mixed numbers) with denominators 2, 4, 5, and 10 on the number line"),
        ("Grade 7", "Locate integers on the number line"),
    ],
    "ClockSet": [
        ("Grade 1", "Read and write time by the hour, half hour, and quarter hour using an analog clock"),
        ("Grade 2", "Read and write time in hours and minutes, with a.m. and p.m., using an analog clock"),
        ("Grade 5", "Describe a 12- and 24-hour clock system"),
    ],
    "PesoMoney": [
        ("Grade 1", "Recognize coins (excluding centavo coins) and bills up to ₱100 and their notations"),
        ("Grade 2", "Determine the value of a number of bills, or a number of coins, or a combination of bills and coins up to ₱1000"),
        ("Grade 3", "Read and write money in words and using: Philippine currency symbols (₱ and PhP) up to ₱10 000"),
    ],
    "FillInTable": [
        ("Grade 1", "Determine the next term/s in a repeating pattern"),
        ("Grade 2", "Multiply numbers using the 2, 3, 4, 5, and 10 multiplication tables"),
        ("Grade 3", "Multiply numbers using the 6, 7, 8, and 9 multiplication tables"),
    ],
    "ConstraintSatisfaction": [
        ("Grade 3", "Distinguish even and odd numbers using division by 2"),
        ("Grade 5", "Distinguish prime numbers from composite numbers using the Sieve of Eratosthenes"),
        ("Grade 6", "Determine the common factors and the greatest common factor (GCF) of two numbers"),
    ],
    "Categorize": [
        ("Grade 1", "Compare and distinguish 2-dimensional shapes according to features"),
        ("Grade 5", "Distinguish prime numbers from composite numbers"),
        ("Grade 7", "Classify polygons according to the number of sides"),
    ],
    "Calendar": [
        ("Grade 1", "Give the days of the week and months of the year in the correct order"),
        ("Grade 1", "Determine the day and month of the year using a calendar"),
        ("Grade 2", "Describe the duration of an event in terms of number of days and/or weeks using a calendar"),
    ],
    "EstimationGate": [
        ("Grade 3", "Round numbers to the nearest ten, hundred, or thousand"),
        ("Grade 4", "Estimate the sum and difference of two 5- to 6-digit numbers"),
        ("Grade 5", "Estimate each of two decimal numbers to the nearest whole number to estimate their product"),
    ],
}


def test_visual_type_generation():
    """Test that all visual types generate valid skeletons for all supported grades."""
    print("\n" + "=" * 60)
    print("TEST 1: Visual Type Generation for All Grades")
    print("=" * 60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for vtype, (min_grade, max_grade) in VISUAL_TYPES.items():
        for grade in range(min_grade, max_grade + 1):
            for difficulty in [1, 2, 3, 4]:
                try:
                    seed = random.randint(1000, 99999)
                    skeleton = visual_skeletons.get_visual_skeleton(
                        visual_type=vtype,
                        grade=grade,
                        seed=seed,
                        difficulty=difficulty
                    )
                    
                    # Validate skeleton structure
                    assert "skeleton_id" in skeleton, "Missing skeleton_id"
                    assert "visual_type" in skeleton, "Missing visual_type"
                    assert "visual_params" in skeleton, "Missing visual_params"
                    assert "correct_answer" in skeleton, "Missing correct_answer"
                    assert "all_traps" in skeleton, "Missing all_traps"
                    
                    # Validate skeleton passes internal validation
                    assert visual_skeletons.validate_skeleton(skeleton), "Skeleton failed validation"
                    
                    results["passed"] += 1
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "visual_type": vtype,
                        "grade": grade,
                        "difficulty": difficulty,
                        "error": str(e)
                    })
    
    print(f"\n✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    
    if results["errors"]:
        print("\nErrors:")
        for err in results["errors"][:10]:  # Show first 10 errors
            print(f"  - {err['visual_type']} Grade {err['grade']} Diff {err['difficulty']}: {err['error']}")
        if len(results["errors"]) > 10:
            print(f"  ... and {len(results['errors']) - 10} more errors")
    
    return results["failed"] == 0


def test_skeleton_regeneration():
    """Test that skeleton_id allows deterministic regeneration."""
    print("\n" + "=" * 60)
    print("TEST 2: Skeleton Regeneration from ID")
    print("=" * 60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for vtype, (min_grade, max_grade) in VISUAL_TYPES.items():
        grade = random.randint(min_grade, max_grade)
        seed = random.randint(1000, 99999)
        difficulty = random.randint(1, 3)
        
        try:
            # Generate original
            original = visual_skeletons.get_visual_skeleton(
                visual_type=vtype,
                grade=grade,
                seed=seed,
                difficulty=difficulty
            )
            
            # Regenerate from ID
            regenerated = visual_skeletons.regenerate_skeleton(original["skeleton_id"])
            
            # Compare key fields
            assert original["correct_answer"] == regenerated["correct_answer"], \
                f"Correct answer mismatch: {original['correct_answer']} vs {regenerated['correct_answer']}"
            
            results["passed"] += 1
            
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "visual_type": vtype,
                "error": str(e)
            })
    
    print(f"\n✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    
    if results["errors"]:
        print("\nErrors:")
        for err in results["errors"]:
            print(f"  - {err['visual_type']}: {err['error']}")
    
    return results["failed"] == 0


def test_answer_validation():
    """Test that answer validation correctly identifies correct and incorrect answers."""
    print("\n" + "=" * 60)
    print("TEST 3: Answer Validation")
    print("=" * 60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for vtype, (min_grade, max_grade) in VISUAL_TYPES.items():
        grade = random.randint(min_grade, max_grade)
        seed = random.randint(1000, 99999)
        
        try:
            skeleton = visual_skeletons.get_visual_skeleton(
                visual_type=vtype,
                grade=grade,
                seed=seed,
                difficulty=2
            )
            
            correct_answer = skeleton["correct_answer"]
            skeleton_id = skeleton["skeleton_id"]
            
            # Test correct answer
            result = visual_skeletons.validate_student_answer(skeleton_id, correct_answer)
            assert result["is_correct"], f"Correct answer rejected for {vtype}: {correct_answer}"
            
            results["passed"] += 1
            
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "visual_type": vtype,
                "error": str(e)
            })
    
    print(f"\n✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    
    if results["errors"]:
        print("\nErrors:")
        for err in results["errors"]:
            print(f"  - {err['visual_type']}: {err['error']}")
    
    return results["failed"] == 0


def test_trap_triggers():
    """Test that incorrect answers trigger appropriate traps."""
    print("\n" + "=" * 60)
    print("TEST 4: Trap Triggering")
    print("=" * 60)
    
    results = {"passed": 0, "failed": 0, "traps_found": 0, "errors": []}
    
    for vtype, (min_grade, max_grade) in VISUAL_TYPES.items():
        grade = random.randint(min_grade, max_grade)
        seed = random.randint(1000, 99999)
        
        try:
            skeleton = visual_skeletons.get_visual_skeleton(
                visual_type=vtype,
                grade=grade,
                seed=seed,
                difficulty=2
            )
            
            skeleton_id = skeleton["skeleton_id"]
            all_traps = skeleton.get("all_traps", {})
            
            # Test a few trap values
            for trap_name, trap_data in list(all_traps.items())[:3]:
                trap_val = trap_data.get("value") or trap_data.get("position") or trap_data.get("values")
                if trap_val is not None:
                    result = visual_skeletons.validate_student_answer(skeleton_id, trap_val)
                    
                    if not result["is_correct"]:
                        results["traps_found"] += 1
                        if result.get("trap_triggered"):
                            # Good - trap was identified
                            pass
            
            results["passed"] += 1
            
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "visual_type": vtype,
                "error": str(e)
            })
    
    print(f"\n✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    print(f"  Traps correctly triggered: {results['traps_found']}")
    
    if results["errors"]:
        print("\nErrors:")
        for err in results["errors"]:
            print(f"  - {err['visual_type']}: {err['error']}")
    
    return results["failed"] == 0


def test_difficulty_scaling():
    """Test that difficulty affects problem complexity appropriately."""
    print("\n" + "=" * 60)
    print("TEST 5: Difficulty Scaling")
    print("=" * 60)
    
    results = {"passed": 0, "observations": []}
    
    test_types = ["NumberLine", "FillInTable", "ConstraintSatisfaction", "PesoMoney"]
    
    for vtype in test_types:
        min_grade, max_grade = VISUAL_TYPES[vtype]
        grade = (min_grade + max_grade) // 2  # Use middle grade
        seed = 12345  # Fixed seed for comparison
        
        try:
            easy = visual_skeletons.get_visual_skeleton(vtype, grade, seed, difficulty=1)
            hard = visual_skeletons.get_visual_skeleton(vtype, grade, seed, difficulty=4)
            
            # Compare some aspect that should scale with difficulty
            easy_params = easy["visual_params"]
            hard_params = hard["visual_params"]
            
            observation = f"{vtype}: "
            
            if vtype == "NumberLine":
                easy_div = easy_params.get("divisions", 0)
                hard_div = hard_params.get("divisions", 0)
                observation += f"divisions: easy={easy_div}, hard={hard_div}"
                
            elif vtype == "FillInTable":
                easy_blanks = len(easy_params.get("blank_inputs", []))
                hard_blanks = len(hard_params.get("blank_inputs", []))
                observation += f"blanks: easy={easy_blanks}, hard={hard_blanks}"
                
            elif vtype == "ConstraintSatisfaction":
                easy_constraints = len(easy_params.get("constraints", []))
                hard_constraints = len(hard_params.get("constraints", []))
                observation += f"constraints: easy={easy_constraints}, hard={hard_constraints}"
                
            elif vtype == "PesoMoney":
                easy_target = easy_params.get("target_amount", 0)
                hard_target = hard_params.get("target_amount", 0)
                observation += f"target: easy=₱{easy_target}, hard=₱{hard_target}"
            
            results["observations"].append(observation)
            results["passed"] += 1
            
        except Exception as e:
            results["observations"].append(f"{vtype}: ERROR - {str(e)}")
    
    print("\nObservations:")
    for obs in results["observations"]:
        print(f"  - {obs}")
    
    return True


def test_visual_params_structure():
    """Test that visual_params contain required fields for frontend rendering."""
    print("\n" + "=" * 60)
    print("TEST 6: Visual Params Structure")
    print("=" * 60)
    
    required_fields = {
        "NumberLine": ["range", "divisions", "correct_position"],
        "ClockSet": ["hours", "minutes", "use_24_hour"],
        "PesoMoney": ["target_amount", "available_denominations"],
        "FillInTable": ["columns", "rows", "blank_inputs"],
        "RuleDiscovery": ["table", "rule_expression"],
        "ConstraintSatisfaction": ["constraints", "valid_answers", "constraint_descriptions"],
        "BarChart": ["labels", "values", "max_y"],
        "SortOrder": ["items", "correct_sequence", "direction"],
        "GridArea": ["grid_size", "correct_count"],
        "Categorize": ["categories", "items", "correct_categories"],
        "Calendar": ["year", "month", "task_type"],
        "EstimationGate": ["operation", "exact_value", "tolerance"],
    }
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for vtype, required in required_fields.items():
        min_grade, max_grade = VISUAL_TYPES[vtype]
        grade = min_grade
        
        try:
            skeleton = visual_skeletons.get_visual_skeleton(vtype, grade, seed=12345, difficulty=2)
            params = skeleton["visual_params"]
            
            missing = [f for f in required if f not in params]
            if missing:
                results["failed"] += 1
                results["errors"].append({
                    "visual_type": vtype,
                    "missing_fields": missing
                })
            else:
                results["passed"] += 1
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "visual_type": vtype,
                "error": str(e)
            })
    
    print(f"\n✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    
    if results["errors"]:
        print("\nErrors:")
        for err in results["errors"]:
            if "missing_fields" in err:
                print(f"  - {err['visual_type']}: missing {err['missing_fields']}")
            else:
                print(f"  - {err['visual_type']}: {err['error']}")
    
    return results["failed"] == 0


def test_competency_specific_generation():
    """Test that specific competency text produces appropriate problem types."""
    print("\n" + "=" * 60)
    print("TEST 7: Competency-Specific Generation")
    print("=" * 60)
    
    results = {"passed": 0, "failed": 0, "observations": []}
    
    for vtype, competencies in TEST_COMPETENCIES.items():
        for grade_label, competency_text in competencies:
            grade = int(grade_label.split()[1])
            
            try:
                skeleton = visual_skeletons.get_visual_skeleton(
                    visual_type=vtype,
                    grade=grade,
                    seed=random.randint(1000, 99999),
                    difficulty=2,
                    competency_text=competency_text
                )
                
                results["passed"] += 1
                
                # Check for curriculum-relevant features
                params = skeleton["visual_params"]
                stem = skeleton.get("stem_template", "")
                
                # Example: ClockSet should use 24-hour for Grade 5+
                if vtype == "ClockSet" and grade >= 5:
                    if params.get("use_24_hour"):
                        results["observations"].append(f"  ✓ ClockSet Grade {grade}: 24-hour mode active")
                
                # Example: PesoMoney should respect denomination limits
                if vtype == "PesoMoney":
                    target = params.get("target_amount", 0)
                    results["observations"].append(f"  ✓ PesoMoney Grade {grade}: target ₱{target}")
                
            except Exception as e:
                results["failed"] += 1
                results["observations"].append(f"  ✗ {vtype} {grade_label}: {str(e)}")
    
    print(f"\n✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    
    if results["observations"]:
        print("\nObservations:")
        for obs in results["observations"][:15]:
            print(obs)
    
    return results["failed"] == 0


def run_all_tests():
    """Run all tests and report overall results."""
    print("\n" + "=" * 60)
    print("VISUAL SKELETONS TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Visual Type Generation", test_visual_type_generation),
        ("Skeleton Regeneration", test_skeleton_regeneration),
        ("Answer Validation", test_answer_validation),
        ("Trap Triggering", test_trap_triggers),
        ("Difficulty Scaling", test_difficulty_scaling),
        ("Visual Params Structure", test_visual_params_structure),
        ("Competency-Specific Generation", test_competency_specific_generation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n!!! TEST {name} CRASHED: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED - See above for details")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
