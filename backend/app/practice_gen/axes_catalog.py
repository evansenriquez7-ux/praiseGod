"""
Practice Generation — Difficulty Axes Catalog
==============================================

UI-ready axis definitions per DNA concept. Used by the
/api/matatag/difficulty-axes/{node_id} endpoint to populate
the Problem Lab axis controls.

Each entry is a list of axis dicts:
  {
    "name":    str,           # matches key in DNA.difficulty_axes
    "label":   str,           # human-readable label for the UI
    "options": [              # ordered easy → hard
      {"value": str, "label": str},
      ...
    ],
    "default": str            # value of the easiest / most common option
  }
"""

from __future__ import annotations

from typing import Dict, List


# ═══════════════════════════════════════════════════════════════════════════════
# CATALOG
# ═══════════════════════════════════════════════════════════════════════════════

CONCEPT_AXES_CATALOG: Dict[str, List[dict]] = {

    # ── Number & Algebra ──────────────────────────────────────────────────────

    "counting": [
        {
            "name": "range",
            "label": "Number Range",
            "dim_type": "continuous",
            "scale": "logarithmic",
            "default_min": 10,
            "default_max": 10000,
            "divisions": 5,
            "default": 0.0,
        },
        {
            "name": "skip_interval",
            "label": "Skip-Counting Interval",
            "options": [
                {"value": "by_1",         "label": "By 1s"},
                {"value": "by_2_5_10",    "label": "By 2s, 5s, or 10s"},
                {"value": "by_20_50_100", "label": "By 20s, 50s, or 100s"},
            ],
            "default": "by_1",
        },
    ],

    "comparing_ordering": [
        {
            "name": "max_value",
            "label": "Maximum Value",
            "dim_type": "continuous",
            "default_min": 20,
            "default_max": 10000,
            "divisions": 5,
            "default": 0.5,
        },
        {
            "name": "number_difficulty",
            "label": "Number Difficulty",
            "dim_type": "continuous",
            "default_min": 0.0,
            "default_max": 1.0,
            "divisions": 5,
            "default": 0.5,
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "compare_two",  "label": "Compare Two Numbers (=, <, >)"},
                {"value": "order_set",    "label": "Order a Set of Numbers"},
                {"value": "find_between", "label": "Find a Number Between Two Others"},
            ],
            "default": "compare_two",
        },
        {
            "name": "proximity",
            "label": "Number Closeness",
            "options": [
                {"value": "far_apart",      "label": "Far Apart (easier)"},
                {"value": "close_together", "label": "Close Together (trickier)"},
            ],
            "default": "far_apart",
        },
    ],

    "ordinal_numbers": [
        {
            "name": "range",
            "label": "Ordinal Range",
            "options": [
                {"value": "1st_to_10th",   "label": "1st to 10th"},
                {"value": "11th_to_20th",  "label": "11th to 20th"},
                {"value": "21st_to_100th", "label": "21st to 100th"},
            ],
            "default": "1st_to_10th",
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "identify_ordinal",   "label": "Identify the Ordinal"},
                {"value": "find_position",      "label": "Find the Position"},
                {"value": "compare_positions",  "label": "Compare Two Positions"},
            ],
            "default": "identify_ordinal",
        },
    ],

    "addition": [
        {
            "name": "max_sum",
            "label": "Maximum Sum",
            "dim_type": "continuous",  # Continuous dimension - scalar maps to number range
            "default_min": 2,          # Minimum possible max_sum (sums of at least 2)
            "default_max": 1000,       # Maximum possible max_sum (for higher grades)
            "divisions": 5,            # d=5 divisions for windowed sampling
            "default": 0.5,            # Default scalar
        },
        {
            "name": "regrouping",
            "label": "Regrouping (Carrying)",
            "dim_type": "discrete",
            "options": [
                {"value": "none",   "label": "No Regrouping"},
                {"value": "ones",   "label": "Regroup Ones"},
                {"value": "tens",   "label": "Regroup Tens"},
                {"value": "double", "label": "Regroup Ones and Tens"},
            ],
            "default": "none",
        },
        {
            "name": "number_difficulty",
            "label": "Number Difficulty",
            "dim_type": "continuous",
            "default_min": 0.0,
            "default_max": 1.0,
            "divisions": 5,
            "default": 0.5,
        },
        # NOTE: "structure" removed - it's a contextual variant, not a difficulty dimension
    ],

    "subtraction": [
        {
            "name": "max_difference",
            "label": "Maximum Difference (Minuend)",
            "dim_type": "continuous",
            "default_min": 2,
            "default_max": 1000,
            "divisions": 5,
            "default": 0.5,
        },
        {
            "name": "regrouping",
            "label": "Regrouping (Borrowing)",
            "dim_type": "discrete",
            "options": [
                {"value": "none",   "label": "No Borrowing"},
                {"value": "ones",   "label": "Borrow in Ones Place"},
                {"value": "tens",   "label": "Borrow in Tens Place"},
                {"value": "double", "label": "Borrow in Both Places"},
            ],
            "default": "none",
        },
        {
            "name": "number_difficulty",
            "label": "Number Difficulty",
            "dim_type": "continuous",
            "default_min": 0.0,
            "default_max": 1.0,
            "divisions": 5,
            "default": 0.5,
        },
    ],

    "missing_number": [
        {
            "name": "operation",
            "label": "Operation",
            "options": [
                {"value": "addition_subtraction",    "label": "Addition or Subtraction"},
                {"value": "multiplication_division", "label": "Multiplication or Division"},
            ],
            "default": "addition_subtraction",
        },
        {
            "name": "blank_position",
            "label": "Missing Position",
            "options": [
                {"value": "result", "label": "Missing Result  (a + b = ___)"},
                {"value": "change", "label": "Missing Second Number  (a + ___ = c)"},
                {"value": "start",  "label": "Missing First Number  (___ + b = c)"},
            ],
            "default": "result",
        },
        {
            "name": "equation_type",
            "label": "Equation Type",
            "options": [
                {"value": "standard",           "label": "Standard  (a op b = ___)"},
                {"value": "balance_expression", "label": "Balance  (a + b = c + ___)"},
            ],
            "default": "standard",
        },
    ],

    "place_value": [
        {
            "name": "digit_count",
            "label": "Number of Digits",
            "options": [
                {"value": "2_digit", "label": "2-Digit Numbers"},
                {"value": "3_digit", "label": "3-Digit Numbers"},
                {"value": "4_digit", "label": "4-Digit Numbers"},
            ],
            "default": "2_digit",
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "identify_place", "label": "Identify the Place"},
                {"value": "identify_value", "label": "Identify the Value of a Digit"},
                {"value": "compose",        "label": "Compose the Number"},
                {"value": "decompose",      "label": "Decompose into Place Values"},
            ],
            "default": "identify_place",
        },
        {
            "name": "include_zeros",
            "label": "Zero Digits",
            "options": [
                {"value": "no_zeros",   "label": "No Zero Digits"},
                {"value": "with_zeros", "label": "Include Zero Digits (e.g. 304)"},
            ],
            "default": "no_zeros",
        },
    ],

    "number_reading": [
        {
            "name": "range",
            "label": "Number Range",
            "dim_type": "continuous",
            "scale": "logarithmic",
            "default_min": 10,
            "default_max": 100,
        },
    ],

    "patterns": [
        {
            "name": "pattern_type",
            "label": "Pattern Type",
            "options": [
                {"value": "repeating",              "label": "Repeating Pattern (A B A B\u2026)"},
                {"value": "arithmetic_increasing",  "label": "Increasing Arithmetic Pattern"},
                {"value": "arithmetic_decreasing",  "label": "Decreasing Arithmetic Pattern"},
                {"value": "combined",               "label": "Repeating + Increasing (combined)"},
            ],
            "default": "repeating",
        },
        {
            "name": "element_type",
            "label": "Pattern Elements",
            "options": [
                {"value": "numbers",      "label": "Numbers"},
                {"value": "number_words", "label": "Number Words"},
            ],
            "default": "numbers",
        },
        {
            "name": "ask_type",
            "label": "Question Type",
            "options": [
                {"value": "next_term",     "label": "Find the Next Term"},
                {"value": "missing_middle","label": "Find a Missing Middle Term"},
                {"value": "state_rule",    "label": "State the Rule"},
            ],
            "default": "next_term",
        },
    ],

    "fractions": [
        {
            "name": "fraction_type",
            "label": "Fraction Type",
            "options": [
                {"value": "unit_fraction",  "label": "Unit Fractions (1/2, 1/4, 1/8)"},
                {"value": "similar_proper", "label": "Similar Proper Fractions"},
                {"value": "mixed_number",   "label": "Mixed Numbers (\u2265 1)"},
            ],
            "default": "unit_fraction",
        },
        {
            "name": "fraction_model",
            "label": "Model",
            "options": [
                {"value": "area_model",  "label": "Area Model (shapes)"},
                {"value": "set_model",   "label": "Set Model (groups of objects)"},
                {"value": "number_line", "label": "Number Line"},
            ],
            "default": "area_model",
        },
        {
            "name": "operation",
            "label": "Operation",
            "options": [
                {"value": "identify_name", "label": "Identify / Name the Fraction"},
                {"value": "compare",       "label": "Compare Fractions"},
                {"value": "add_subtract",  "label": "Add or Subtract Similar Fractions"},
            ],
            "default": "identify_name",
        },
    ],

    "money_peso": [
        {
            "name": "max_total",
            "label": "Maximum Total",
            "dim_type": "continuous",
            "default_min": 100,
            "default_max": 10000,
            "divisions": 5,
            "default": 0.5,
        },
        {
            "name": "number_difficulty",
            "label": "Number Difficulty",
            "dim_type": "continuous",
            "default_min": 0.0,
            "default_max": 1.0,
            "divisions": 5,
            "default": 0.5,
        },
        {
            "name": "denomination_type",
            "label": "Denomination",
            "options": [
                {"value": "coins_only", "label": "Coins Only"},
                {"value": "bills_only", "label": "Bills Only"},
                {"value": "mixed",      "label": "Coins and Bills (mixed)"},
            ],
            "default": "coins_only",
        },
        {
            "name": "operation",
            "label": "Operation",
            "options": [
                {"value": "identify_value", "label": "Identify the Total Value"},
                {"value": "add_amounts",    "label": "Add Two Amounts"},
                {"value": "find_change",    "label": "Find the Change"},
            ],
            "default": "identify_value",
        },
    ],

    "multiplication": [
        {
            "name": "max_product",
            "label": "Maximum Product",
            "dim_type": "continuous",
            "default_min": 4,
            "default_max": 1000,
            "divisions": 5,
            "default": 0.5,
        },
        {
            "name": "table",
            "label": "Times Tables",
            "options": [
                {"value": "2_3_4_5_10", "label": "2s, 3s, 4s, 5s, 10s"},
                {"value": "6_7_8_9",    "label": "6s, 7s, 8s, 9s"},
            ],
            "default": "2_3_4_5_10",
        },
        {
            "name": "structure",
            "label": "Problem Structure",
            "options": [
                {"value": "result_unknown", "label": "Find the Product  (a \u00d7 b = ?)"},
                {"value": "factor_unknown", "label": "Find a Factor  (a \u00d7 ? = c)"},
            ],
            "default": "result_unknown",
        },
        {
            "name": "number_difficulty",
            "label": "Number Difficulty",
            "dim_type": "continuous",
            "default_min": 0.0,
            "default_max": 1.0,
            "divisions": 5,
            "default": 0.5,
        },
    ],

    "division": [
        {
            "name": "max_quotient",
            "label": "Maximum Quotient",
            "dim_type": "continuous",
            "default_min": 2,
            "default_max": 100,
            "divisions": 5,
            "default": 0.5,
        },
        {
            "name": "remainder",
            "label": "Remainder",
            "options": [
                {"value": "none",           "label": "No Remainder (exact)"},
                {"value": "with_remainder", "label": "With Remainder"},
            ],
            "default": "none",
        },
        {
            "name": "table",
            "label": "Related Times Tables",
            "options": [
                {"value": "2_3_4_5_10", "label": "2s, 3s, 4s, 5s, 10s"},
                {"value": "6_7_8_9",    "label": "6s, 7s, 8s, 9s"},
            ],
            "default": "2_3_4_5_10",
        },
        {
            "name": "structure",
            "label": "Problem Structure",
            "options": [
                {"value": "result_unknown",  "label": "Find the Quotient  (a \u00f7 b = ?)"},
                {"value": "divisor_unknown", "label": "Find the Divisor  (a \u00f7 ? = c)"},
            ],
            "default": "result_unknown",
        },
        {
            "name": "number_difficulty",
            "label": "Number Difficulty",
            "dim_type": "continuous",
            "default_min": 0.0,
            "default_max": 1.0,
            "divisions": 5,
            "default": 0.5,
        },
    ],

    "rounding": [
        {
            "name": "precision",
            "label": "Round to Nearest",
            "options": [
                {"value": "nearest_ten",      "label": "Nearest Ten"},
                {"value": "nearest_hundred",  "label": "Nearest Hundred"},
                {"value": "nearest_thousand", "label": "Nearest Thousand"},
            ],
            "default": "nearest_ten",
        },
        {
            "name": "boundary_proximity",
            "label": "Closeness to Rounding Boundary",
            "options": [
                {"value": "far_from_boundary", "label": "Far from Boundary (clearer)"},
                {"value": "near_boundary",     "label": "Near Boundary (trickier)"},
            ],
            "default": "far_from_boundary",
        },
    ],

    "order_of_operations": [
        {
            "name": "num_operands",
            "label": "Expression Length",
            "options": [
                {"value": "three_terms", "label": "Three Terms"},
                {"value": "four_terms",  "label": "Four Terms"},
            ],
            "default": "three_terms",
        },
        {
            "name": "operation_mix",
            "label": "Operations Used",
            "options": [
                {"value": "add_only",      "label": "Addition Only"},
                {"value": "mixed_add_sub", "label": "Addition and Subtraction"},
            ],
            "default": "add_only",
        },
        {
            "name": "number_size",
            "label": "Number Size",
            "options": [
                {"value": "1_digit", "label": "Single-Digit"},
                {"value": "2_digit", "label": "Two-Digit"},
            ],
            "default": "1_digit",
        },
    ],

    # ── Measurement & Geometry ────────────────────────────────────────────────

    "area": [
        {
            "name": "shape",
            "label": "Shape",
            "options": [
                {"value": "square",    "label": "Square"},
                {"value": "rectangle", "label": "Rectangle"},
            ],
            "default": "square",
        },
        {
            "name": "unit",
            "label": "Unit",
            "options": [
                {"value": "square_cm", "label": "Square Centimeters (sq. cm)"},
                {"value": "square_m",  "label": "Square Meters (sq. m)"},
            ],
            "default": "square_cm",
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "find_area",              "label": "Find the Area"},
                {"value": "find_missing_dimension", "label": "Find the Missing Side Length"},
            ],
            "default": "find_area",
        },
    ],

    "calendar": [
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "read_day_of_week", "label": "Read the Day of the Week"},
                {"value": "read_month",       "label": "Read the Month"},
                {"value": "find_date",        "label": "Find a Specific Date"},
                {"value": "elapsed_days",     "label": "Count Elapsed Days"},
                {"value": "elapsed_weeks",    "label": "Count Elapsed Weeks"},
            ],
            "default": "read_day_of_week",
        },
        {
            "name": "calendar_feature",
            "label": "Calendar Feature",
            "options": [
                {"value": "days_order",   "label": "Days of the Week in Order"},
                {"value": "months_order", "label": "Months of the Year in Order"},
                {"value": "full_calendar","label": "Full Calendar Grid"},
            ],
            "default": "days_order",
        },
    ],

    "geometric_lines": [
        {
            "name": "concept_type",
            "label": "Concept",
            "options": [
                {"value": "point_line_segment_ray",          "label": "Point, Line, Segment, Ray"},
                {"value": "parallel_intersecting_perpendicular","label": "Parallel, Intersecting, Perpendicular"},
                {"value": "rotation_turns",                  "label": "Rotations and Turns"},
            ],
            "default": "point_line_segment_ray",
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "identify_name",     "label": "Identify by Name"},
                {"value": "identify_property", "label": "Identify a Property"},
                {"value": "apply_rotation",    "label": "Apply a Rotation"},
            ],
            "default": "identify_name",
        },
    ],

    "length_measurement": [
        {
            "name": "unit_type",
            "label": "Unit",
            "options": [
                {"value": "non_standard",  "label": "Non-Standard Units (e.g. paper clips)"},
                {"value": "centimeters",   "label": "Centimeters (cm)"},
                {"value": "meters",        "label": "Meters (m)"},
                {"value": "convert_between","label": "Convert m \u2194 cm"},
            ],
            "default": "non_standard",
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "read_measurement", "label": "Read a Measurement"},
                {"value": "compare_lengths",  "label": "Compare Two Lengths"},
                {"value": "estimate",         "label": "Estimate a Length"},
                {"value": "solve_problem",    "label": "Solve a Word Problem"},
            ],
            "default": "read_measurement",
        },
    ],

    "mass_capacity": [
        {
            "name": "measurement_type",
            "label": "Measurement Type",
            "options": [
                {"value": "mass",     "label": "Mass (weight)"},
                {"value": "capacity", "label": "Capacity (volume)"},
            ],
            "default": "mass",
        },
        {
            "name": "unit",
            "label": "Unit",
            "options": [
                {"value": "grams_kilograms",    "label": "Grams (g) / Kilograms (kg)"},
                {"value": "liters_milliliters", "label": "Liters (L) / Milliliters (mL)"},
            ],
            "default": "grams_kilograms",
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "read_measurement", "label": "Read a Measurement"},
                {"value": "compare",          "label": "Compare Two Measurements"},
                {"value": "estimate",         "label": "Estimate"},
                {"value": "convert",          "label": "Convert Between Units"},
            ],
            "default": "read_measurement",
        },
    ],

    "perimeter": [
        {
            "name": "shape",
            "label": "Shape",
            "options": [
                {"value": "square",    "label": "Square"},
                {"value": "rectangle", "label": "Rectangle"},
                {"value": "triangle",  "label": "Triangle"},
            ],
            "default": "square",
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "find_perimeter",   "label": "Find the Perimeter"},
                {"value": "find_missing_side","label": "Find the Missing Side"},
            ],
            "default": "find_perimeter",
        },
        {
            "name": "number_size",
            "label": "Side Length Size",
            "options": [
                {"value": "small_numbers",  "label": "Small Numbers"},
                {"value": "larger_numbers", "label": "Larger Numbers"},
            ],
            "default": "small_numbers",
        },
    ],

    "shapes_2d": [
        {
            "name": "shape_set",
            "label": "Shape Set",
            "options": [
                {"value": "basic_triangles_rectangles_squares","label": "Triangles, Rectangles, Squares"},
                {"value": "extended_with_circles",             "label": "+ Circles and Semi-Circles"},
                {"value": "composite_figures",                 "label": "Composite (combined) Figures"},
            ],
            "default": "basic_triangles_rectangles_squares",
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "identify_name",      "label": "Identify by Name"},
                {"value": "count_sides_corners","label": "Count Sides and Corners"},
                {"value": "compare_shapes",     "label": "Compare Two Shapes"},
                {"value": "compose_decompose",  "label": "Compose or Decompose"},
            ],
            "default": "identify_name",
        },
        {
            "name": "orientation",
            "label": "Orientation",
            "options": [
                {"value": "standard", "label": "Standard Orientation"},
                {"value": "rotated",  "label": "Rotated / Non-Standard Orientation"},
            ],
            "default": "standard",
        },
    ],

    "symmetry_slides": [
        {
            "name": "concept",
            "label": "Concept",
            "options": [
                {"value": "slide_translation",       "label": "Slide (Translation)"},
                {"value": "line_symmetry",            "label": "Line Symmetry"},
                {"value": "complete_symmetric_figure","label": "Complete a Symmetric Figure"},
            ],
            "default": "slide_translation",
        },
        {
            "name": "directions",
            "label": "Number of Slide Directions",
            "options": [
                {"value": "one_direction", "label": "One Direction"},
                {"value": "two_directions","label": "Two Directions"},
            ],
            "default": "one_direction",
        },
    ],

    "time_reading": [
        {
            "name": "precision",
            "label": "Precision",
            "options": [
                {"value": "hour",         "label": "To the Hour"},
                {"value": "half_hour",    "label": "To the Half Hour"},
                {"value": "quarter_hour", "label": "To the Quarter Hour"},
                {"value": "five_minutes", "label": "To 5 Minutes"},
                {"value": "one_minute",   "label": "To 1 Minute"},
            ],
            "default": "hour",
        },
        {
            "name": "mode",
            "label": "Mode",
            "options": [
                {"value": "read", "label": "Read the Clock"},
                {"value": "set",  "label": "Set the Clock (interactive)"},
            ],
            "default": "read",
        },
        {
            "name": "include_ampm",
            "label": "a.m. / p.m.",
            "options": [
                {"value": "no_ampm",   "label": "Without a.m./p.m."},
                {"value": "with_ampm", "label": "With a.m./p.m."},
            ],
            "default": "no_ampm",
        },
    ],

    # ── Data & Probability ────────────────────────────────────────────────────

    "bar_graphs": [
        {
            "name": "orientation",
            "label": "Bar Orientation",
            "options": [
                {"value": "vertical",   "label": "Vertical Bars"},
                {"value": "horizontal", "label": "Horizontal Bars"},
            ],
            "default": "vertical",
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "read_value",    "label": "Read a Single Value"},
                {"value": "compare_bars",  "label": "Compare Two Bars"},
                {"value": "find_total",    "label": "Find the Total"},
                {"value": "find_difference","label": "Find the Difference"},
                {"value": "find_most_least","label": "Find Most / Least"},
            ],
            "default": "read_value",
        },
        {
            "name": "scale",
            "label": "Scale",
            "options": [
                {"value": "scale_5",  "label": "Scale of 5"},
                {"value": "scale_10", "label": "Scale of 10"},
                {"value": "scale_20", "label": "Scale of 20"},
            ],
            "default": "scale_5",
        },
    ],

    "pictographs": [
        {
            "name": "scale_type",
            "label": "Symbol Scale",
            "options": [
                {"value": "no_scale", "label": "No Scale (1 symbol = 1)"},
                {"value": "scale_2",  "label": "1 symbol = 2"},
                {"value": "scale_5",  "label": "1 symbol = 5"},
                {"value": "scale_10", "label": "1 symbol = 10"},
            ],
            "default": "no_scale",
        },
        {
            "name": "task_type",
            "label": "Task",
            "options": [
                {"value": "read_single",    "label": "Read One Category"},
                {"value": "compare_two",    "label": "Compare Two Categories"},
                {"value": "find_total",     "label": "Find the Total"},
                {"value": "find_difference","label": "Find the Difference"},
            ],
            "default": "read_single",
        },
        {
            "name": "num_categories",
            "label": "Number of Categories",
            "options": [
                {"value": "three_four", "label": "3 or 4 Categories"},
                {"value": "five_six",   "label": "5 or 6 Categories"},
            ],
            "default": "three_four",
        },
    ],

    "probability_language": [],
}


def get_axes_for_concept(concept: str) -> list:
    """Return the UI-ready axis list for a concept, or [] if not found."""
    return CONCEPT_AXES_CATALOG.get(concept, [])


def compute_difficulty_scalar(concept: str, axis_values: dict) -> float:
    """
    Compute a 0.0–1.0 difficulty scalar from the selected axis values.

    For each axis present in axis_values, compute the fraction:
        selected_index / (num_options - 1)

    Return the average across all axes. Falls back to 0.5 if nothing matches.
    """
    axes = CONCEPT_AXES_CATALOG.get(concept, [])
    if not axes:
        return 0.5

    scalars = []
    for axis in axes:
        name = axis["name"]
        if name not in axis_values:
            continue
        selected = axis_values[name]
        
        if "options" not in axis:
            min_val = axis.get("default_min", 0.0)
            max_val = axis.get("default_max", min_val + 1.0)
            if max_val <= min_val:
                scalars.append(0.5)
            else:
                try:
                    s = (float(selected) - min_val) / (max_val - min_val)
                    scalars.append(max(0.0, min(1.0, s)))
                except (ValueError, TypeError):
                    scalars.append(0.5)
            continue

        option_values = [o["value"] for o in axis["options"]]
        if selected not in option_values:
            continue
        idx = option_values.index(selected)
        n = len(option_values)
        scalars.append(idx / (n - 1) if n > 1 else 0.5)

    return sum(scalars) / len(scalars) if scalars else 0.5
