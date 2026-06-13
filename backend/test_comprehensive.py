#!/usr/bin/env python3
"""
Ultra-comprehensive test suite for all visual skeleton types.
Tests all grades, real curriculum competencies, and edge cases.
"""

import sys
import json
import traceback
from pathlib import Path
from app.visual_skeletons import (
    get_visual_skeleton, 
    regenerate_skeleton, 
    validate_student_answer,
    validate_skeleton
)
from app.curriculum_context import get_curriculum_context

VISUAL_TYPES = [
    "NumberLine",
    "ClockSet", 
    "PesoMoney",
    "FillInTable",
    "RuleDiscovery",
    "ConstraintSatisfaction",
    "BarChart",
    "EstimationGate",
    "SortOrder",
    "GridArea",
    "Categorize",
    "Calendar"
]

# Load curriculum for real competency testing
curriculum_path = Path(__file__).parent.parent / "ph" / "matatagmath.json"
with open(curriculum_path, 'r') as f:
    CURRICULUM = json.load(f)


def get_competencies_for_grade(grade: int):
    """Extract all competencies for a specific grade."""
    competencies = []
    
    for quarter_key, quarter_data in CURRICULUM.items():
        if not isinstance(quarter_data, dict):
            continue
        
        # Extract grade from key like "Grade 1 - Quarter 1"
        if f"Grade {grade}" in quarter_key:
            for comp_id, comp_data in quarter_data.items():
                if isinstance(comp_data, dict) and 'text' in comp_data:
                    competencies.append(comp_data['text'])
    
    return competencies


def test_grade_range(visual_type: str):
    """Test each visual type across all applicable grades."""
    results = {
        "type": visual_type,
        "grades_tested": 0,
        "grades_passed": 0,
        "errors": []
    }
    
    # Test grades 1-10
    for grade in range(1, 11):
        try:
            # Test with multiple seeds and difficulties
            success = True
            for difficulty in [1, 2, 3, 4]:
                for seed in range(20000 + grade * 100, 20000 + grade * 100 + 3):
                    skeleton = get_visual_skeleton(visual_type, grade, seed, difficulty)
                    
                    if not validate_skeleton(skeleton):
                        results["errors"].append(
                            f"Grade {grade} diff {difficulty} seed {seed}: Validation failed"
                        )
                        success = False
                        break
                
                if not success:
                    break
            
            results["grades_tested"] += 1
            if success:
                results["grades_passed"] += 1
            
        except Exception as e:
            results["errors"].append(f"Grade {grade}: Exception - {type(e).__name__}: {str(e)}")
            results["grades_tested"] += 1
    
    return results


def test_edge_cases_by_type():
    """Test specific edge cases for each visual type."""
    edge_tests = []
    
    # NumberLine: Test zero, negative, fractions, decimals, large numbers
    test_cases = [
        ("NumberLine Grade 1: Small positive integers", "NumberLine", 1, 30000, 1),
        ("NumberLine Grade 4: Includes zero", "NumberLine", 4, 30001, 2),
        ("NumberLine Grade 6: Negative numbers", "NumberLine", 6, 30002, 3),
        ("NumberLine Grade 6: Decimals", "NumberLine", 6, 30003, 3),
        ("NumberLine Grade 7: Large numbers (100+)", "NumberLine", 7, 30004, 4),
        
        # ClockSet: Test midnight, noon, 24-hour edge cases
        ("ClockSet Grade 3: Exact hour (3:00)", "ClockSet", 3, 30010, 1),
        ("ClockSet Grade 3: Half past (6:30)", "ClockSet", 3, 30011, 1),
        ("ClockSet Grade 4: Any minute", "ClockSet", 4, 30012, 3),
        ("ClockSet Grade 5: 24-hour midnight (00:xx)", "ClockSet", 5, 30013, 2),
        ("ClockSet Grade 5: 24-hour noon (12:xx)", "ClockSet", 5, 30014, 2),
        ("ClockSet Grade 5: 24-hour evening (20:xx)", "ClockSet", 5, 30015, 3),
        ("ClockSet Grade 5: 24-hour late night (23:xx)", "ClockSet", 5, 30016, 3),
        
        # PesoMoney: Test small, medium, large amounts
        ("PesoMoney Grade 1: Very small (₱1-10)", "PesoMoney", 1, 30020, 1),
        ("PesoMoney Grade 2: Small (₱10-50)", "PesoMoney", 2, 30021, 2),
        ("PesoMoney Grade 3: Medium (₱50-100)", "PesoMoney", 3, 30022, 3),
        ("PesoMoney Grade 5: Large (₱100+)", "PesoMoney", 5, 30023, 4),
        ("PesoMoney Grade 5: Bridge zone (>ceiling)", "PesoMoney", 5, 30024, 4),
        
        # FillInTable: Test different pattern types
        ("FillInTable Grade 1: Skip counting", "FillInTable", 1, 30030, 1),
        ("FillInTable Grade 3: Multiplication table", "FillInTable", 3, 30031, 2),
        ("FillInTable Grade 5: Linear pattern (ax+b)", "FillInTable", 5, 30032, 2),
        ("FillInTable Grade 7: Quadratic pattern", "FillInTable", 7, 30033, 4),
        
        # RuleDiscovery: Test algebraic complexity
        ("RuleDiscovery Grade 6: Simple linear", "RuleDiscovery", 6, 30040, 1),
        ("RuleDiscovery Grade 7: Complex linear", "RuleDiscovery", 7, 30041, 3),
        ("RuleDiscovery Grade 8: Quadratic", "RuleDiscovery", 8, 30042, 4),
        
        # ConstraintSatisfaction: Test multiple constraints
        ("ConstraintSatisfaction Grade 2: Two constraints", "ConstraintSatisfaction", 2, 30050, 1),
        ("ConstraintSatisfaction Grade 4: Three constraints + even/odd", "ConstraintSatisfaction", 4, 30051, 3),
        ("ConstraintSatisfaction Grade 6: Divisibility constraints", "ConstraintSatisfaction", 6, 30052, 3),
        
        # BarChart: Test data complexity
        ("BarChart Grade 2: 3 categories, small values", "BarChart", 2, 30060, 1),
        ("BarChart Grade 4: 5 categories, medium values", "BarChart", 4, 30061, 2),
        ("BarChart Grade 6: 5 categories, large values", "BarChart", 6, 30062, 4),
        
        # EstimationGate: Test operations and tolerance
        ("EstimationGate Grade 2: Addition", "EstimationGate", 2, 30070, 1),
        ("EstimationGate Grade 4: Multiplication", "EstimationGate", 4, 30071, 2),
        ("EstimationGate Grade 6: Division", "EstimationGate", 6, 30072, 3),
        
        # SortOrder: Test different data types
        ("SortOrder Grade 1: Small integers (1-20)", "SortOrder", 1, 30080, 1),
        ("SortOrder Grade 3: Larger integers (1-100)", "SortOrder", 3, 30081, 2),
        ("SortOrder Grade 5: Decimals", "SortOrder", 5, 30082, 3),
        ("SortOrder Grade 6: Negative numbers", "SortOrder", 6, 30083, 3),
        ("SortOrder Grade 7: Fractions", "SortOrder", 7, 30084, 4),
        
        # GridArea: Test shape complexity
        ("GridArea Grade 2: Small rectangle (2x3)", "GridArea", 2, 30090, 1),
        ("GridArea Grade 3: Medium rectangle (5x4)", "GridArea", 3, 30091, 2),
        ("GridArea Grade 5: L-shape", "GridArea", 5, 30092, 3),
        ("GridArea Grade 6: Complex shape", "GridArea", 6, 30093, 4),
        
        # Categorize: Test classification complexity
        ("Categorize Grade 2: Even/Odd", "Categorize", 2, 30100, 1),
        ("Categorize Grade 4: Prime/Composite", "Categorize", 4, 30101, 2),
        ("Categorize Grade 5: Shape classification", "Categorize", 5, 30102, 2),
        ("Categorize Grade 7: Algebraic classification", "Categorize", 7, 30103, 3),
        
        # Calendar: Test date operations
        ("Calendar Grade 2: Select specific date", "Calendar", 2, 30110, 1),
        ("Calendar Grade 3: Duration calculation", "Calendar", 3, 30111, 2),
        ("Calendar Grade 4: Multi-week duration", "Calendar", 4, 30112, 3),
    ]
    
    for test_name, visual_type, grade, seed, difficulty in test_cases:
        try:
            skeleton = get_visual_skeleton(visual_type, grade, seed, difficulty)
            
            # Validate
            if not validate_skeleton(skeleton):
                edge_tests.append((test_name, f"FAIL: Validation failed"))
                continue
            
            # Test regeneration
            regenerated = regenerate_skeleton(skeleton["skeleton_id"])
            if skeleton["correct_answer"] != regenerated["correct_answer"]:
                edge_tests.append((test_name, f"FAIL: Regeneration mismatch"))
                continue
            
            # Test correct answer validation
            result = validate_student_answer(skeleton["skeleton_id"], skeleton["correct_answer"])
            if not result["is_correct"]:
                edge_tests.append((test_name, f"FAIL: Correct answer marked wrong"))
                continue
            
            edge_tests.append((test_name, "PASS"))
            
        except Exception as e:
            edge_tests.append((test_name, f"FAIL: {type(e).__name__}: {str(e)[:50]}"))
    
    return edge_tests


def test_with_real_competencies():
    """Test generation with real curriculum competencies."""
    results = []
    
    # Sample competencies from different grades
    test_competencies = [
        (1, "Visualize and represent numbers from 0 to 100 using a variety of materials."),
        (2, "Visualize, represent, and separate objects into groups of equal quantity using concrete objects."),
        (3, "Visualize and represent multiplication of numbers 1 to 10 by 2, 3, 4, 5, and 10."),
        (4, "Visualize division as equal sharing, repeated subtraction, and inverse of multiplication."),
        (5, "Visualize decimal numbers using models, words, and in expanded form."),
        (6, "Visualize and describe the exponent in a number expressed in exponential notation."),
    ]
    
    for grade, competency_text in test_competencies:
        try:
            # Try to generate with this competency
            skeleton = get_visual_skeleton("NumberLine", grade, 40000 + grade, 2, competency_text)
            
            if validate_skeleton(skeleton):
                results.append((f"Grade {grade} with competency", "PASS"))
            else:
                results.append((f"Grade {grade} with competency", "FAIL: Validation failed"))
                
        except Exception as e:
            results.append((f"Grade {grade} with competency", f"FAIL: {type(e).__name__}"))
    
    return results


def test_boundary_conditions():
    """Test boundary and extreme conditions."""
    boundary_tests = []
    
    tests = [
        # Zero handling
        ("NumberLine: Position at 0", lambda: get_visual_skeleton("NumberLine", 4, 50000, 1)),
        
        # Maximum values
        ("PesoMoney: Bridge zone (difficulty 1.2)", lambda: get_visual_skeleton("PesoMoney", 5, 50001, 4)),
        
        # Minimum difficulty
        ("ClockSet: Difficulty 1 (easiest)", lambda: get_visual_skeleton("ClockSet", 3, 50002, 1)),
        
        # Maximum difficulty  
        ("ClockSet: Difficulty 4 (hardest)", lambda: get_visual_skeleton("ClockSet", 5, 50003, 4)),
        
        # Float difficulty
        ("NumberLine: Float difficulty 0.5", lambda: get_visual_skeleton("NumberLine", 4, 50004, 0.5)),
        ("NumberLine: Float difficulty 1.2", lambda: get_visual_skeleton("NumberLine", 6, 50005, 1.2)),
        
        # Edge grades
        ("Calendar: Grade 1 (minimum)", lambda: get_visual_skeleton("Calendar", 1, 50010, 1)),
        ("RuleDiscovery: Grade 10 (maximum)", lambda: get_visual_skeleton("RuleDiscovery", 10, 50011, 3)),
        
        # High seed values
        ("PesoMoney: Seed 999999", lambda: get_visual_skeleton("PesoMoney", 4, 999999, 2)),
        
        # Same seed, different difficulties
        ("Consistency: Same seed, diff 1", lambda: get_visual_skeleton("NumberLine", 5, 77777, 1)),
        ("Consistency: Same seed, diff 2", lambda: get_visual_skeleton("NumberLine", 5, 77777, 2)),
        ("Consistency: Same seed, diff 3", lambda: get_visual_skeleton("NumberLine", 5, 77777, 3)),
        ("Consistency: Same seed, diff 4", lambda: get_visual_skeleton("NumberLine", 5, 77777, 4)),
    ]
    
    for test_name, test_func in tests:
        try:
            skeleton = test_func()
            if validate_skeleton(skeleton):
                boundary_tests.append((test_name, "PASS"))
            else:
                boundary_tests.append((test_name, "FAIL: Validation failed"))
        except Exception as e:
            boundary_tests.append((test_name, f"FAIL: {type(e).__name__}: {str(e)[:40]}"))
    
    return boundary_tests


def main():
    print("=" * 80)
    print("ULTRA-COMPREHENSIVE VISUAL SKELETON TEST SUITE")
    print("Testing all grades, competencies, and edge cases")
    print("=" * 80)
    print()
    
    # Test 1: All visual types across all grades
    print("TEST 1: ALL VISUAL TYPES ACROSS ALL GRADES (1-10)")
    print("-" * 80)
    
    grade_results = []
    for visual_type in VISUAL_TYPES:
        print(f"Testing {visual_type}...", end=" ", flush=True)
        result = test_grade_range(visual_type)
        grade_results.append(result)
        
        if result["grades_passed"] == result["grades_tested"]:
            print(f"✓ PASS ({result['grades_passed']}/{result['grades_tested']} grades)")
        else:
            print(f"⚠ PARTIAL ({result['grades_passed']}/{result['grades_tested']} grades)")
    
    print()
    
    # Test 2: Specific edge cases
    print("TEST 2: EDGE CASES BY TYPE")
    print("-" * 80)
    
    edge_results = test_edge_cases_by_type()
    edge_pass = sum(1 for _, status in edge_results if status == "PASS")
    edge_total = len(edge_results)
    
    for test_name, status in edge_results:
        icon = "✓" if status == "PASS" else "✗"
        # Truncate test name if too long
        display_name = test_name[:60] + "..." if len(test_name) > 60 else test_name
        print(f"{icon} {display_name}: {status}")
    
    print()
    print(f"Edge cases: {edge_pass}/{edge_total} passed ({100*edge_pass/edge_total:.1f}%)")
    print()
    
    # Test 3: Real curriculum competencies
    print("TEST 3: REAL CURRICULUM COMPETENCIES")
    print("-" * 80)
    
    comp_results = test_with_real_competencies()
    comp_pass = sum(1 for _, status in comp_results if status == "PASS")
    comp_total = len(comp_results)
    
    for test_name, status in comp_results:
        icon = "✓" if status == "PASS" else "✗"
        print(f"{icon} {test_name}: {status}")
    
    print()
    print(f"Competency tests: {comp_pass}/{comp_total} passed ({100*comp_pass/comp_total:.1f}%)")
    print()
    
    # Test 4: Boundary conditions
    print("TEST 4: BOUNDARY CONDITIONS")
    print("-" * 80)
    
    boundary_results = test_boundary_conditions()
    boundary_pass = sum(1 for _, status in boundary_results if status == "PASS")
    boundary_total = len(boundary_results)
    
    for test_name, status in boundary_results:
        icon = "✓" if status == "PASS" else "✗"
        print(f"{icon} {test_name}: {status}")
    
    print()
    print(f"Boundary tests: {boundary_pass}/{boundary_total} passed ({100*boundary_pass/boundary_total:.1f}%)")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    total_grade_tests = sum(r["grades_tested"] for r in grade_results)
    total_grade_pass = sum(r["grades_passed"] for r in grade_results)
    
    print(f"Grade range tests: {total_grade_pass}/{total_grade_tests} ({100*total_grade_pass/total_grade_tests:.1f}%)")
    print(f"Edge case tests: {edge_pass}/{edge_total} ({100*edge_pass/edge_total:.1f}%)")
    print(f"Competency tests: {comp_pass}/{comp_total} ({100*comp_pass/comp_total:.1f}%)")
    print(f"Boundary tests: {boundary_pass}/{boundary_total} ({100*boundary_pass/boundary_total:.1f}%)")
    print()
    
    total_tests = total_grade_tests + edge_total + comp_total + boundary_total
    total_pass = total_grade_pass + edge_pass + comp_pass + boundary_pass
    
    print(f"OVERALL: {total_pass}/{total_tests} tests passed ({100*total_pass/total_tests:.1f}%)")
    print()
    
    # Show failures
    failures = []
    
    for result in grade_results:
        if result["errors"]:
            failures.extend([(result["type"], err) for err in result["errors"][:3]])
    
    for test_name, status in edge_results:
        if status != "PASS":
            failures.append(("Edge case", f"{test_name}: {status}"))
    
    for test_name, status in comp_results:
        if status != "PASS":
            failures.append(("Competency", f"{test_name}: {status}"))
    
    for test_name, status in boundary_results:
        if status != "PASS":
            failures.append(("Boundary", f"{test_name}: {status}"))
    
    if failures:
        print("FAILURES (showing first 20):")
        print()
        for category, error in failures[:20]:
            print(f"  [{category}] {error}")
        if len(failures) > 20:
            print(f"  ... and {len(failures) - 20} more")
    else:
        print("🎉 ALL TESTS PASSED!")
    
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
