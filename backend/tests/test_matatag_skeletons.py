"""
Unit tests for MATATAG MCQ Skeleton Generators

Tests the matatag_skeletons.py module including:
- Main entry point
- Routing logic
- Individual generators
- Trap generation
- Difficulty scaling

Author: CCMed Team
"""

import pytest
import random
from typing import Dict, Any

# Import the module under test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from matatag_skeletons import (
    get_matatag_skeleton,
    validate_matatag_answer,
    _route_competency,
    _validate_skeleton,
    _shuffle_options,
    _ordinal,
    _simplify_fraction,
    TRAP_CATALOG,
    COMPETENCY_ROUTES,
)
from matatag_dimensions import (
    get_dimension_values,
    interpolate_dimension,
    GENERATOR_DIMENSIONS,
    DIFFICULTY_LEVEL_MAP,
)
from constraint_extractor import extract_constraints


# ═══════════════════════════════════════════════════════════════════════════════
# TEST UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

class TestUtilities:
    """Test utility functions."""
    
    def test_ordinal(self):
        """Test ordinal number generation."""
        assert _ordinal(1) == "1st"
        assert _ordinal(2) == "2nd"
        assert _ordinal(3) == "3rd"
        assert _ordinal(4) == "4th"
        assert _ordinal(11) == "11th"
        assert _ordinal(12) == "12th"
        assert _ordinal(13) == "13th"
        assert _ordinal(21) == "21st"
        assert _ordinal(22) == "22nd"
        assert _ordinal(23) == "23rd"
        assert _ordinal(100) == "100th"
    
    def test_simplify_fraction(self):
        """Test fraction simplification."""
        assert _simplify_fraction(2, 4) == (1, 2)
        assert _simplify_fraction(3, 9) == (1, 3)
        assert _simplify_fraction(5, 7) == (5, 7)  # Already simplified
        assert _simplify_fraction(6, 8) == (3, 4)
        assert _simplify_fraction(12, 16) == (3, 4)
    
    def test_shuffle_options(self):
        """Test option shuffling."""
        rng = random.Random(42)
        options = [("10", None), ("5", "trap1"), ("15", "trap2"), ("20", "trap3")]
        result = _shuffle_options(options, rng)
        
        assert len(result) == 4
        assert set(result.keys()) == {"A", "B", "C", "D"}
        
        # Check structure
        for key, opt in result.items():
            assert "value" in opt
            assert "trap" in opt
        
        # Ensure correct answer is present
        values = [opt["value"] for opt in result.values()]
        assert "10" in values


# ═══════════════════════════════════════════════════════════════════════════════
# TEST CONSTRAINT EXTRACTOR
# ═══════════════════════════════════════════════════════════════════════════════

class TestConstraintExtractor:
    """Test constraint extraction from competency text."""
    
    def test_numeric_limit(self):
        """Test numeric limit extraction."""
        text = "Add numbers with sums up to 1000"
        constraints = extract_constraints(text)
        assert constraints.get("numeric_limit") == 1000
        
        text = "Count up to 100"
        constraints = extract_constraints(text)
        assert constraints.get("numeric_limit") == 100
    
    def test_digit_count(self):
        """Test digit count extraction."""
        text = "Determine the place value of a digit in a 3-digit number"
        constraints = extract_constraints(text)
        assert constraints.get("digit_count") == 3
        
        text = "Add 2-digit and 1-digit numbers"
        constraints = extract_constraints(text)
        assert constraints.get("digit_count") in [1, 2]  # Finds first match
    
    def test_operations(self):
        """Test operation extraction."""
        text = "Solve problems involving addition and subtraction"
        constraints = extract_constraints(text)
        assert "add" in constraints.get("operations", [])
        assert "sub" in constraints.get("operations", [])
        
        text = "Multiply numbers using the 2, 3, 4, 5, and 10 multiplication tables"
        constraints = extract_constraints(text)
        assert "mul" in constraints.get("operations", [])
    
    def test_fraction_type(self):
        """Test fraction type extraction."""
        text = "Add and subtract similar fractions"
        constraints = extract_constraints(text)
        assert constraints.get("fraction_type") == "similar"
        
        text = "Represent improper fractions and mixed numbers"
        constraints = extract_constraints(text)
        # Should pick up one of them
        assert constraints.get("fraction_type") in ["improper", "mixed"]
    
    def test_denominator_list(self):
        """Test denominator list extraction."""
        text = "Plot fractions with denominators 2, 4, 5, and 10 on the number line"
        constraints = extract_constraints(text)
        denoms = constraints.get("denominator_list", [])
        assert 2 in denoms
        assert 4 in denoms
        assert 5 in denoms
        assert 10 in denoms
    
    def test_regrouping(self):
        """Test regrouping extraction."""
        text = "Add numbers with sums up to 1000, with or without regrouping"
        constraints = extract_constraints(text)
        assert constraints.get("regrouping") == "optional"
        
        text = "Subtract numbers without regrouping"
        constraints = extract_constraints(text)
        assert constraints.get("regrouping") == False
        
        text = "Add numbers with regrouping"
        constraints = extract_constraints(text)
        assert constraints.get("regrouping") == True
    
    def test_ordinal_limit(self):
        """Test ordinal limit extraction."""
        text = "Describe the position of objects using ordinal numbers up to 10th"
        constraints = extract_constraints(text)
        assert constraints.get("ordinal_limit") == 10
        
        text = "Use ordinal numbers up to 100th"
        constraints = extract_constraints(text)
        assert constraints.get("ordinal_limit") == 100
    
    def test_decimal_places(self):
        """Test decimal places extraction."""
        text = "Read and write decimal numbers with decimal parts to hundredths"
        constraints = extract_constraints(text)
        assert constraints.get("decimal_places") == 2
        
        text = "Add decimals to thousandths"
        constraints = extract_constraints(text)
        assert constraints.get("decimal_places") == 3


# ═══════════════════════════════════════════════════════════════════════════════
# TEST ROUTING
# ═══════════════════════════════════════════════════════════════════════════════

class TestRouting:
    """Test competency-to-generator routing."""
    
    def test_counting_routes(self):
        """Test routing to counting generator."""
        competencies = [
            "Count up to 100",
            "Count by 2s, 5s and 10s up to 100",
            "Identify a number that is 1 more or 1 less",
            "Describe position using ordinal numbers",
        ]
        for comp in competencies:
            gen = _route_competency(comp, grade=2)
            assert gen == "counting", f"Expected counting for: {comp}"
    
    def test_place_value_routes(self):
        """Test routing to place value generator."""
        competencies = [
            "Determine the place value of a digit in a 2-digit number",
            "Decompose any 2-digit number into tens and ones",
            "Read and write numerals up to 100",
        ]
        for comp in competencies:
            gen = _route_competency(comp, grade=2)
            assert gen == "place_value", f"Expected place_value for: {comp}"
    
    def test_arithmetic_routes(self):
        """Test routing to arithmetic generator."""
        competencies = [
            "Add numbers with sums up to 100 without regrouping",
            "Subtract numbers where both numbers are less than 100",
            "Multiply numbers using the 2, 3, 4, 5, and 10 multiplication tables",
            "Divide numbers using the 2, 3 4, 5, and 10 multiplication tables",
            "Find the missing number in addition or subtraction sentences",
        ]
        for comp in competencies:
            gen = _route_competency(comp, grade=3)
            assert gen == "arithmetic", f"Expected arithmetic for: {comp}"
    
    def test_fractions_routes(self):
        """Test routing to fractions generator."""
        competencies = [
            "Illustrate 1/2 and 1/4 as parts of a whole",
            "Compare and order unit fractions",
            "Add and subtract similar fractions",
            "Generate equivalent fractions using models",
        ]
        for comp in competencies:
            gen = _route_competency(comp, grade=4)
            assert gen == "fractions", f"Expected fractions for: {comp}"
    
    def test_decimals_routes(self):
        """Test routing to decimals generator."""
        competencies = [
            "Read and write decimal numbers with decimal parts to hundredths",
            "Compare and order decimal numbers",
            "Convert decimal numbers to fractions",
        ]
        for comp in competencies:
            gen = _route_competency(comp, grade=5)
            assert gen == "decimals", f"Expected decimals for: {comp}"
    
    def test_algebra_routes(self):
        """Test routing to algebra generator."""
        competencies = [
            "Evaluate algebraic expressions given the values of the variables",
            "Solve linear equations in one variable",
            "Apply laws of exponents",
            "Factor different types of polynomials",
        ]
        for comp in competencies:
            gen = _route_competency(comp, grade=8)
            assert gen == "algebra", f"Expected algebra for: {comp}"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST DIMENSION VALUES
# ═══════════════════════════════════════════════════════════════════════════════

class TestDimensions:
    """Test difficulty dimension calculations."""
    
    def test_difficulty_levels(self):
        """Test difficulty level mapping."""
        assert DIFFICULTY_LEVEL_MAP[1] == 0.2  # Easy
        assert DIFFICULTY_LEVEL_MAP[2] == 0.5  # Medium
        assert DIFFICULTY_LEVEL_MAP[3] == 0.8  # Hard
        assert DIFFICULTY_LEVEL_MAP[4] == 1.1  # Advanced
    
    def test_dimension_interpolation_linear(self):
        """Test linear dimension interpolation."""
        from matatag_dimensions import DimensionSpec
        
        spec = DimensionSpec(
            name="Test",
            value_type="int",
            default_min=10,
            default_max=100,
            constraint_name=None,
            extrapolate=False,
            description="Test dimension",
            scale_type="linear"
        )
        
        # At difficulty 0
        val = interpolate_dimension(spec, 0.0)
        assert val == 10
        
        # At difficulty 0.5
        val = interpolate_dimension(spec, 0.5)
        assert val == 55
        
        # At difficulty 1.0
        val = interpolate_dimension(spec, 1.0)
        assert val == 100
    
    def test_dimension_interpolation_log(self):
        """Test logarithmic dimension interpolation."""
        from matatag_dimensions import DimensionSpec
        
        spec = DimensionSpec(
            name="Test",
            value_type="int",
            default_min=10,
            default_max=10000,
            constraint_name=None,
            extrapolate=True,
            description="Test dimension",
            scale_type="log"
        )
        
        # At difficulty 0
        val = interpolate_dimension(spec, 0.0)
        assert val == 10
        
        # At difficulty 0.5 (should be geometric mean)
        val = interpolate_dimension(spec, 0.5)
        assert 90 < val < 400  # Around sqrt(10 * 10000) = 316
        
        # At difficulty 1.0
        val = interpolate_dimension(spec, 1.0)
        assert val == 10000
    
    def test_get_dimension_values_with_constraints(self):
        """Test dimension values respect constraints."""
        constraints = {"numeric_limit": 500}
        dimensions = get_dimension_values("arithmetic", 0.5, constraints)
        
        # operand_max should be affected by numeric_limit
        assert "operand_max" in dimensions
        assert dimensions["operand_max"] <= 500


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SKELETON GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestSkeletonGeneration:
    """Test skeleton generation."""
    
    def test_counting_skeleton(self):
        """Test counting skeleton generation."""
        skeleton = get_matatag_skeleton(
            competency_text="Count up to 100",
            grade=1,
            difficulty=0.5,
            seed=12345
        )
        
        assert skeleton is not None
        assert skeleton["generator_type"] == "counting"
        assert "stem" in skeleton
        assert "correct_answer" in skeleton
        assert "options" in skeleton
        assert len(skeleton["options"]) == 4
    
    def test_place_value_skeleton(self):
        """Test place value skeleton generation."""
        skeleton = get_matatag_skeleton(
            competency_text="Determine the place value of a digit in a 3-digit number",
            grade=2,
            difficulty=0.5,
            seed=12345
        )
        
        assert skeleton is not None
        assert skeleton["generator_type"] == "place_value"
        assert "stem" in skeleton
        assert "correct_answer" in skeleton
    
    def test_arithmetic_skeleton(self):
        """Test arithmetic skeleton generation."""
        skeleton = get_matatag_skeleton(
            competency_text="Add numbers with sums up to 100 without regrouping",
            grade=2,
            difficulty=0.5,
            seed=12345
        )
        
        assert skeleton is not None
        assert skeleton["generator_type"] == "arithmetic"
        assert "stem" in skeleton
        assert "+" in skeleton["stem"]  # Should be addition
    
    def test_fractions_skeleton(self):
        """Test fractions skeleton generation."""
        skeleton = get_matatag_skeleton(
            competency_text="Add and subtract similar fractions",
            grade=4,
            difficulty=0.5,
            seed=12345
        )
        
        assert skeleton is not None
        assert skeleton["generator_type"] == "fractions"
        assert "/" in skeleton["stem"] or "/" in skeleton["correct_answer"]
    
    def test_skeleton_has_analytics(self):
        """Test skeleton includes analytics fields."""
        skeleton = get_matatag_skeleton(
            competency_text="Count up to 100",
            grade=1,
            difficulty=0.5,
            seed=12345
        )
        
        assert "analytics" in skeleton
        assert skeleton["analytics"]["time_to_answer_ms"] is None
        assert skeleton["analytics"]["trap_triggered"] is None
        assert skeleton["analytics"]["is_correct"] is None
    
    def test_skeleton_has_difficulty_info(self):
        """Test skeleton includes difficulty information."""
        skeleton = get_matatag_skeleton(
            competency_text="Add numbers with sums up to 1000",
            grade=3,
            difficulty=0.7,
            seed=12345
        )
        
        assert skeleton["difficulty_scalar"] == 0.7
        assert "difficulty_dimensions" in skeleton
        assert "constraints_extracted" in skeleton
    
    def test_deterministic_generation(self):
        """Test that same seed produces same skeleton."""
        skeleton1 = get_matatag_skeleton(
            competency_text="Count up to 100",
            grade=1,
            difficulty=0.5,
            seed=99999
        )
        
        skeleton2 = get_matatag_skeleton(
            competency_text="Count up to 100",
            grade=1,
            difficulty=0.5,
            seed=99999
        )
        
        assert skeleton1["stem"] == skeleton2["stem"]
        assert skeleton1["correct_answer"] == skeleton2["correct_answer"]
    
    def test_different_seeds_different_problems(self):
        """Test that different seeds produce different problems."""
        skeleton1 = get_matatag_skeleton(
            competency_text="Add numbers with sums up to 100",
            grade=2,
            difficulty=0.5,
            seed=11111
        )
        
        skeleton2 = get_matatag_skeleton(
            competency_text="Add numbers with sums up to 100",
            grade=2,
            difficulty=0.5,
            seed=22222
        )
        
        # Very unlikely to be the same
        assert skeleton1["stem"] != skeleton2["stem"] or skeleton1["correct_answer"] != skeleton2["correct_answer"]


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SKELETON VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestSkeletonValidation:
    """Test skeleton validation."""
    
    def test_valid_skeleton(self):
        """Test validation of a valid skeleton."""
        skeleton = {
            "stem": "What is 2 + 3?",
            "correct_answer": "5",
            "options": {
                "A": {"value": "5", "trap": None},
                "B": {"value": "4", "trap": "ar_off_one"},
                "C": {"value": "6", "trap": "ar_off_one"},
                "D": {"value": "1", "trap": "ar_wrong_op"},
            }
        }
        assert _validate_skeleton(skeleton) == True
    
    def test_invalid_skeleton_missing_stem(self):
        """Test validation fails for missing stem."""
        skeleton = {
            "correct_answer": "5",
            "options": {}
        }
        assert _validate_skeleton(skeleton) == False
    
    def test_invalid_skeleton_too_few_options(self):
        """Test validation fails for too few options."""
        skeleton = {
            "stem": "What is 2 + 3?",
            "correct_answer": "5",
            "options": {
                "A": {"value": "5", "trap": None},
                "B": {"value": "4", "trap": "ar_off_one"},
            }
        }
        assert _validate_skeleton(skeleton) == False
    
    def test_invalid_skeleton_duplicate_options(self):
        """Test validation fails for duplicate option values."""
        skeleton = {
            "stem": "What is 2 + 3?",
            "correct_answer": "5",
            "options": {
                "A": {"value": "5", "trap": None},
                "B": {"value": "5", "trap": "ar_off_one"},  # Duplicate!
                "C": {"value": "6", "trap": "ar_off_one"},
                "D": {"value": "1", "trap": "ar_wrong_op"},
            }
        }
        assert _validate_skeleton(skeleton) == False


# ═══════════════════════════════════════════════════════════════════════════════
# TEST ANSWER VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnswerValidation:
    """Test answer validation."""
    
    def test_correct_answer(self):
        """Test validation of correct answer."""
        options = {
            "A": {"value": "5", "trap": None},
            "B": {"value": "4", "trap": "ar_off_one"},
            "C": {"value": "6", "trap": "ar_off_one"},
            "D": {"value": "1", "trap": "ar_wrong_op"},
        }
        
        result = validate_matatag_answer(
            skeleton_id="mat_2_ar_12345",
            student_answer="5",
            correct_answer="5",
            options=options
        )
        
        assert result["is_correct"] == True
        assert result["trap_triggered"] is None
    
    def test_wrong_answer_with_trap(self):
        """Test validation identifies triggered trap."""
        options = {
            "A": {"value": "5", "trap": None},
            "B": {"value": "4", "trap": "ar_off_one"},
            "C": {"value": "6", "trap": "ar_off_one"},
            "D": {"value": "1", "trap": "ar_wrong_op"},
        }
        
        result = validate_matatag_answer(
            skeleton_id="mat_2_ar_12345",
            student_answer="4",
            correct_answer="5",
            options=options
        )
        
        assert result["is_correct"] == False
        assert result["trap_triggered"] == "ar_off_one"
        assert result["trap_info"] is not None
    
    def test_trap_catalog_completeness(self):
        """Test that trap catalog has all required traps."""
        required_traps = [
            "cnt_prev", "cnt_skip", "cnt_back",
            "pv_adj_place", "pv_dig_val", "pv_val_dig",
            "ar_wrong_op", "ar_no_regroup", "ar_off_one",
            "fr_swap_nd", "fr_add_both", "fr_big_den",
            "dc_place_err", "dc_longer_bigger",
            "alg_unlike", "alg_exp_mul",
        ]
        
        for trap in required_traps:
            assert trap in TRAP_CATALOG, f"Missing trap: {trap}"
            assert "name" in TRAP_CATALOG[trap]
            assert "description" in TRAP_CATALOG[trap]


# ═══════════════════════════════════════════════════════════════════════════════
# TEST DIFFICULTY SCALING
# ═══════════════════════════════════════════════════════════════════════════════

class TestDifficultyScaling:
    """Test that difficulty affects problem parameters."""
    
    def test_arithmetic_difficulty_affects_numbers(self):
        """Test that higher difficulty produces larger numbers."""
        easy_skeleton = get_matatag_skeleton(
            competency_text="Add numbers with sums up to 1000",
            grade=3,
            difficulty=0.2,
            seed=12345
        )
        
        hard_skeleton = get_matatag_skeleton(
            competency_text="Add numbers with sums up to 1000",
            grade=3,
            difficulty=0.9,
            seed=12345
        )
        
        # Extract numbers from stems (rough check)
        easy_dims = easy_skeleton["difficulty_dimensions"]
        hard_dims = hard_skeleton["difficulty_dimensions"]
        
        # operand_max should be higher at higher difficulty
        assert hard_dims["operand_max"] > easy_dims["operand_max"]
    
    def test_place_value_difficulty_affects_digits(self):
        """Test that higher difficulty produces more digits."""
        easy_dims = get_dimension_values("place_value", 0.2, {})
        hard_dims = get_dimension_values("place_value", 0.9, {})
        
        # digit_count should be higher at higher difficulty
        assert hard_dims["digit_count"] >= easy_dims["digit_count"]
    
    def test_fractions_difficulty_affects_denominators(self):
        """Test that higher difficulty allows larger denominators."""
        easy_dims = get_dimension_values("fractions", 0.2, {})
        hard_dims = get_dimension_values("fractions", 0.9, {})
        
        # denominator_max should be higher at higher difficulty
        assert hard_dims["denominator_max"] >= easy_dims["denominator_max"]


# ═══════════════════════════════════════════════════════════════════════════════
# TEST INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Integration tests for full workflow."""
    
    def test_full_workflow(self):
        """Test complete workflow from competency to validated answer."""
        # 1. Generate skeleton
        skeleton = get_matatag_skeleton(
            competency_text="Add numbers with sums up to 100 without regrouping",
            grade=2,
            difficulty=0.5,
            seed=42
        )
        
        # 2. Verify skeleton structure
        assert skeleton["generator_type"] == "arithmetic"
        assert skeleton["grade"] == 2
        assert len(skeleton["options"]) == 4
        
        # 3. Find correct answer key
        correct_key = None
        for key, opt in skeleton["options"].items():
            if opt["trap"] is None:
                correct_key = key
                break
        
        assert correct_key is not None
        
        # 4. Validate correct answer
        result = validate_matatag_answer(
            skeleton_id=skeleton["skeleton_id"],
            student_answer=skeleton["options"][correct_key]["value"],
            correct_answer=skeleton["correct_answer"],
            options=skeleton["options"]
        )
        
        assert result["is_correct"] == True
    
    def test_generate_for_multiple_competencies(self):
        """Test generating problems for various competencies."""
        competencies = [
            ("Count up to 100", 1),
            ("Determine the place value of a digit in a 3-digit number", 2),
            ("Add numbers with sums up to 1000", 3),
            ("Compare and order fractions with same denominators", 4),
            ("Read and write decimal numbers to hundredths", 5),
            ("Solve linear equations in one variable", 8),
        ]
        
        for comp, grade in competencies:
            skeleton = get_matatag_skeleton(
                competency_text=comp,
                grade=grade,
                difficulty=0.5,
                seed=99999
            )
            
            assert skeleton is not None, f"Failed for: {comp}"
            assert "stem" in skeleton
            assert "correct_answer" in skeleton
            assert len(skeleton["options"]) == 4


# ═══════════════════════════════════════════════════════════════════════════════
# RUN TESTS
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
