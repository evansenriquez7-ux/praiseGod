"""
Practice Generation — DNA-Formatter Compatibility Table
=========================================================

COMPATIBILITY maps each DNA concept name to the list of formatter names
that can present it.  These lists are sourced directly from the
compatible_formatters field of each DNA instance.

FORMATTER_VARIANT_SUPPORT maps each DNA concept to a dict of formatter →
variant restrictions. This table is used to pre-filter variant dropdowns
in the lab UI based on the selected formatter.

Formatter name categories:
  Textual:
    mcq               — Multiple choice (4 options)
    cloze             — Fill-in-blank (equation or word problem via context variant)
    ordering          — Drag-to-order sequence
    true_false        — Binary yes/no judgment
    error_detect      — Spot the mistake in a worked example
    fill_in_blank     — Standalone blank (no cloze sentence)

  Visual – read mode (student reads a visual, answers a question):
    number_line_read  — Read value/position from a number line
    array_grid_read   — Read total from an array/grid
    place_value_blocks_read — Read number from base-10 blocks
    peso_money_read   — Read total from displayed coins/bills
    clock_read        — Read time from analog clock face
    bar_chart_read    — Read value from a bar chart
    pictograph_read   — Read count from a pictograph (no scale)
    fraction_model_read — Read fraction from shaded model
    ruler_measure     — Read length from a ruler
    grid_area         — Read area from a square-grid figure
    sort_order        — Read the sorted sequence
    shape_board       — Identify shape from visual board
    ten_frame         — Read count from a ten-frame
    balance_scale     — Read relationship from a balance scale
    pattern_sequence  — Read/identify next term in a visual pattern
    calendar_read     — Read date/day from a calendar
    categorize        — Sort items into labelled categories

  Visual – set mode (student builds/manipulates the visual):
    number_line_set   — Place a value on a number line
    array_grid_set    — Build an array to show a product
    place_value_blocks_set — Build a number with base-10 blocks
    peso_money_build  — Select coins/bills to make a total
    clock_set         — Set clock hands to show a time
    bar_chart_set     — Fill bar heights in a bar chart
    fraction_shade    — Shade a fraction model
    fill_in_table     — Complete a data table
    number_bond       — Complete a number bond diagram

Refactored from:
  - matatag_skeletons.py VISUAL_COMPETENCY_ROUTES
  - practice_gen_strategy.md Section 9
  - Each DNA instance's compatible_formatters list
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any


# ═══════════════════════════════════════════════════════════════════════════════
# COMPATIBILITY TABLE
# Each entry mirrors the compatible_formatters list of the DNA instance.
# ═══════════════════════════════════════════════════════════════════════════════

COMPATIBILITY: Dict[str, List[str]] = {

    # ── Number & Algebra ──────────────────────────────────────────────────────

    "addition": [
        "mcq",
        "cloze",              # Fill-in-blank (pure equation or word problem via context variant)
        "true_false",
        "error_detect",
        "number_line_read",
        "number_line_set",
        "number_bond",
        "emoji_pictorial",    # Pictorial model with emojis (aligns with competency)
    ],

    "subtraction": [
        "mcq",
        "cloze",
        "true_false",
        "error_detect",
        "number_line_read",
        "number_bond",
        "emoji_pictorial",    # Pictorial model with emojis (aligns with competency)
    ],

    "multiplication": [
        "mcq",
        "cloze",
        "true_false",
        "error_detect",
        "array_grid_read",
        "array_grid_set",
    ],

    "division": [
        "mcq",
        "cloze",
        "true_false",
        "error_detect",
        "array_grid_read",
        "array_grid_set",
    ],

    "counting": [
        "mcq",
        "cloze",
        "ordering",           # Ordering makes sense for counting sequences
        "number_line_read",
        "ten_frame",
        "bar_chart_read",
        "emoji_pictorial",
    ],

    "number_reading": [
        "mcq",
        "cloze",
        "true_false",
        "number_line_read",
        "number_line_set",
        "place_value_blocks_read",
        "place_value_blocks_set",
        "bar_chart_read",
        "emoji_pictorial",
    ],

    "ordinal_numbers": [
        "mcq",
        "cloze",
    ],

    "place_value": [
        "mcq",
        "cloze",
        "true_false",
        "place_value_blocks_read",
        "place_value_blocks_set",
    ],

    "comparing_ordering": [
        "mcq",
        "cloze",
        "ordering",
        "sort_order",
        "true_false",
    ],

    "missing_number": [
        "mcq",
        "cloze",
        "true_false",
        "balance_scale",
    ],

    "patterns": [
        "mcq",
        "cloze",
        "pattern_sequence",
        "fill_in_table",
    ],

    "fractions": [
        "mcq",
        "cloze",
        "fraction_model_read",
        "fraction_shade",
    ],

    "money_peso": [
        "mcq",
        "cloze",
        "peso_money_read",
        "peso_money_build",
    ],

    "rounding": [
        "mcq",
        "cloze",
        "number_line_read",
    ],

    "order_of_operations": [
        "mcq",
        "cloze",
    ],

    # ── Measurement & Geometry ────────────────────────────────────────────────

    "shapes_2d": [
        "mcq",
        "categorize",
        "shape_board",
    ],

    "length_measurement": [
        "mcq",
        "cloze",
        "ruler_measure",
    ],

    "mass_capacity": [
        "mcq",
        "cloze",
    ],

    "time_reading": [
        "clock_read",
        "clock_set",
    ],

    "calendar": [
        "calendar_read",
    ],

    "perimeter": [
        "mcq",
        "cloze",
    ],

    "area": [
        "mcq",
        "cloze",
        "grid_area",
    ],

    "geometric_lines": [
        "mcq",
    ],

    "symmetry_slides": [
        "mcq",
        "shape_board",
    ],

    # ── Data & Probability ────────────────────────────────────────────────────

    "pictographs": [
        "mcq",
        "bar_chart_read",
        "pictograph_read",
        "pictograph_set",
        "fill_in_table",
    ],

    "bar_graphs": [
        "bar_chart_read",
        "bar_chart_set",
    ],

    "probability_language": [
        "mcq",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def is_compatible(dna_concept: str, formatter_name: str) -> bool:
    """
    Return True if the formatter is compatible with the given DNA concept.

    Args:
        dna_concept: DNA concept name, e.g. "addition".
        formatter_name: Formatter name, e.g. "mcq".

    Returns:
        True if formatter_name is in COMPATIBILITY[dna_concept].
        False if the concept is not in the table or the formatter is absent.
    """
    return formatter_name in COMPATIBILITY.get(dna_concept, [])


def get_formatters_for_dna(dna_concept: str) -> List[str]:
    """
    Return all formatter names compatible with a given DNA concept.

    Args:
        dna_concept: DNA concept name, e.g. "addition".

    Returns:
        List of formatter name strings, or an empty list if the concept
        is not in the compatibility table.
    """
    return list(COMPATIBILITY.get(dna_concept, []))


def get_dnas_for_formatter(formatter_name: str) -> List[str]:
    """
    Return all DNA concept names that support a given formatter.

    Performs a reverse lookup over COMPATIBILITY.

    Args:
        formatter_name: Formatter name, e.g. "number_line_read".

    Returns:
        List of DNA concept name strings whose compatibility list
        includes formatter_name.
    """
    return [
        concept
        for concept, formatters in COMPATIBILITY.items()
        if formatter_name in formatters
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXTUAL VARIANTS BY DNA
# Each DNA concept defines which contextual variants apply to it.
# Variants are NOT difficulty — they're selected randomly for engagement
# and their performance is tracked separately.
# ═══════════════════════════════════════════════════════════════════════════════

VARIANTS_BY_DNA: Dict[str, Dict[str, List[str]]] = {

    "addition": {
        "context": ["pure", "word_problem"],
        "structure": ["result_unknown"],
        "spine": ["putting_together", "counting_up"],
        "strategy": ["standard", "expanded_form"],
    },

    "subtraction": {
        "context": ["pure", "word_problem"],
        "structure": ["result_unknown", "change_unknown", "start_unknown"],
        "spine": ["taking_away", "comparing"],
    },

    "multiplication": {
        "table": ["2", "3", "4", "5", "10"],
        "structure": ["result_unknown"],
        "number_type": ["single_digit", "multi_digit"],
        "context": ["pure", "word_problem"],
    },

    "division": {
        "remainder": ["none", "some"],
        "table": ["2", "3", "4", "5", "10"],
        "structure": ["result_unknown"],
        "context": ["pure", "word_problem"],
    },

    "counting": {
        "direction": ["forward", "backward"],
        "context": ["pure", "word_problem"],
        "skip_interval": ["1", "2", "5", "10", "20", "50", "100"],
    },

    "number_reading": {
        "task_type": ["numeral_to_word", "word_to_numeral"],
    },

    "ordinal_numbers": {
        "task_type": ["identify_position", "identify_object"],
    },

    "place_value": {
        "include_zeros": ["yes", "no"],
        "task_type": ["identify_place", "identify_value", "compose", "decompose"],
    },

    "comparing_ordering": {
        "proximity": ["close_together", "far_apart"],
        "task_type": ["compare_pair", "order_sequence"],
        "context": ["pure", "word_problem"],
    },

    "missing_number": {
        "operation": ["addition", "subtraction"],
        "equation_type": ["standard", "non_standard"],
        "blank_position": ["start", "middle", "end"],
        "context": ["pure", "word_problem"],
        "tables": ["2", "3", "4", "5", "10"],
    },

    "patterns": {
        "ask_type": ["next", "missing"],
        "pattern_type": ["repeating", "growing"],
    },

    "fractions": {
        "fraction_type": ["proper", "improper", "mixed"],
        "operation": ["add", "subtract"],
        "fraction_model": ["area_model", "set_model", "number_line"],
    },

    "money_peso": {
        "denomination_type": ["coins", "bills", "mixed"],
        "operation": ["add", "subtract"],
        "context": ["pure", "word_problem"],
    },

    "rounding": {
        "precision": ["nearest_ten", "nearest_hundred", "nearest_thousand"],
        "boundary_proximity": ["near_boundary", "far_from_boundary"],
    },

    "order_of_operations": {
        "operation_mix": ["add_sub", "mult_div", "all"],
        "num_operands": ["three_terms", "four_terms"],
    },

    "shapes_2d": {
        "orientation": ["standard", "rotated"],
        "shape_set": ["basic_triangles_rectangles_squares", "extended_with_circles", "composite_figures"],
        "task_type": ["identify_name", "count_sides_corners", "compare_shapes", "compose_decompose"],
    },

    "length_measurement": {
        "unit_type": ["cm", "m"],
        "task_type": ["compare", "convert"],
    },

    "mass_capacity": {
        "unit": ["g", "kg", "ml", "l"],
        "task_type": ["compare", "convert"],
        "measurement_type": ["mass", "capacity"],
    },

    "time_reading": {
        "precision": ["hour", "half_hour", "quarter_hour", "five_minutes", "one_minute"],
        "include_ampm": ["yes", "no"],
    },

    "calendar": {
        "task_type": ["read_calendar", "elapsed_time"],
    },

    "perimeter": {
        "shape": ["square", "rectangle", "triangle"],
        "task_type": ["calculate", "missing_side"],
    },

    "area": {
        "shape": ["square", "rectangle"],
        "task_type": ["calculate", "missing_side"],
        "unit": ["sq_cm", "sq_m"],
    },

    "geometric_lines": {
        "task_type": ["identify", "draw"],
        "concept_type": ["straight_curved", "parallel_intersecting"],
    },

    "symmetry_slides": {
        "concept": ["symmetry", "slides"],
        "directions": ["horizontal", "vertical", "both"],
    },

    "pictographs": {
        "task_type": ["read", "create"],
        "scale_type": ["no_scale", "scale_2", "scale_5", "scale_10"],
    },

    "bar_graphs": {
        "task_type": ["read", "create"],
        "orientation": ["vertical", "horizontal"],
        "scale": ["scale_5", "scale_10", "scale_20"],
    },

    "probability_language": {
        "scenario_type": ["weather", "games", "daily_life"],
        "context": ["pure", "word_problem"],
    },
}
