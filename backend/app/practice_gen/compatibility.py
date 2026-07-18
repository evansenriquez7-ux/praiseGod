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
# FORMATTER NUMERIC LIMITS
# Defines absolute minimum/maximum values a visual formatter can handle.
# If a generated context exceeds these limits, the orchestrator should clamp
# or reject it *before* generation.
# ═══════════════════════════════════════════════════════════════════════════════

FORMATTER_NUMERIC_LIMITS: Dict[str, Dict[str, Any]] = {
    "emoji_pictorial": {"max_val": 100},
    "place_value_blocks_read": {"max_val": 9999},
    "place_value_blocks_set": {"max_val": 9999},
    "array_grid_read": {"max_val": 400},
    "array_grid_set": {"max_val": 400},
    "ten_frame": {"max_val": 100},
}


# ═══════════════════════════════════════════════════════════════════════════════
# CURRICULUM VARIANT GATES
# Maps (lc, variant_name, variant_value) → (min_grade, min_quarter)
# Indicates when each variant is first introduced in the MATATAG curriculum.
# Used by MATATAG Lab to filter checkbox options (source of truth for what's allowed).
# Used by auditors to verify no variants appear before curriculum introduction.
# ═══════════════════════════════════════════════════════════════════════════════

CURRICULUM_VARIANT_GATES: Dict[tuple, tuple] = {
    # Fractions: keep proper-only (G1Q4 is pre-notation conceptual: halves/quarters only)
    # No gate entries for improper/mixed (not in curriculum for G1-G3)
    ("fractions", "operation", "add"): (3, 4),
    ("fractions", "operation", "subtract"): (3, 4),
    ("fractions", "operation", "add_subtract"): (3, 4),

    # Multiplication: multi_digit introduced in G3Q3 (2-3 digit × 1-digit operations)
    ("multiplication", "number_type", "multi_digit"): (3, 3),

    # Length measurement: standard units (cm/m) are a G2 competency — G1 uses
    # non-standard units only (paperclips, hands, steps).
    ("length_measurement", "unit_type", "cm"): (2, 1),
    ("length_measurement", "unit_type", "m"): (2, 1),
    ("length_measurement", "task_type", "convert"): (2, 1),

    # Word problems: available from G1Q1 per curriculum ("solve problems given orally or in pictures")
    # No gate entries (all LCs with word_problem context available from Q1)
}


def get_variant_curriculum_gate(lc: str, variant_name: str, variant_value: str) -> Optional[tuple]:
    """
    Return the curriculum introduction point for a variant, or None if no gate.

    Args:
        lc: Learning competency name (e.g., "multiplication")
        variant_name: Variant name (e.g., "number_type")
        variant_value: Variant value (e.g., "multi_digit")

    Returns:
        (min_grade, min_quarter) if gated, None if no gate (available from G1Q1)
    """
    return CURRICULUM_VARIANT_GATES.get((lc, variant_name, variant_value))


def is_variant_available_at(lc: str, variant_name: str, variant_value: str, grade: int, quarter: int) -> bool:
    """
    Check if a variant is available at a specific grade/quarter per curriculum.

    Used by MATATAG Lab to filter checkbox options based on curriculum progression.

    Args:
        lc: Learning competency name
        variant_name: Variant name
        variant_value: Variant value
        grade: Student grade (1-3)
        quarter: Student quarter (1-4)

    Returns:
        True if variant is available at this curriculum point, False otherwise
    """
    if lc == "missing_number" and variant_name == "operation":
        if grade >= 3:
            return variant_value in ("multiplication", "division")
        else:
            return variant_value in ("addition", "subtraction")

    gate = get_variant_curriculum_gate(lc, variant_name, variant_value)
    if gate is None:
        # No gate = available from G1Q1
        return True

    min_grade, min_quarter = gate
    return grade > min_grade or (grade == min_grade and quarter >= min_quarter)


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
        "emoji_pictorial",
    ],

    "number_reading": [
        "mcq",
        "cloze",
        "true_false",
        "number_line_read",
        "number_line_set",
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
        "operation": ["addition", "subtraction", "multiplication", "division"],
        "equation_type": ["standard", "non_standard"],
        "blank_position": ["start", "middle", "end"],
        "context": ["pure", "word_problem"],
        "tables": ["2", "3", "4", "5", "10"],
    },

    "patterns": {
        "ask_type": ["next", "missing"],
        "pattern_type": ["repeating", "growing"],
        "element_type": ["numbers", "shapes", "number_words"],
    },

    "fractions": {
        "fraction_type": ["proper"],
        "operation": ["add", "subtract", "add_subtract"],
        "fraction_model": ["area_model", "set_model", "number_line"],
    },

    "money_peso": {
        "task_type": ["count_total", "make_change", "give_money"],
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
        "mode": ["read", "set"],
    },

    "calendar": {
        "task_type": ["read_calendar", "elapsed_time"],
        "calendar_feature": ["days", "weeks", "months", "dates"],
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
        "task_type": ["read_value", "compare_two", "find_total", "find_difference", "present_data", "organize_table"],
        "scale_type": ["no_scale", "scale_2", "scale_5", "scale_10"],
    },

    "bar_graphs": {
        "task_type": ["read_value", "compare_bars", "find_total", "find_difference", "find_most_least"],
        "orientation": ["vertical", "horizontal"],
        "scale": ["scale_5", "scale_10", "scale_20"],
    },

    "probability_language": {
        "scenario_type": ["certain_impossible", "likely_unlikely", "comparative"],
        "context": ["colored_objects", "coins", "spinners", "weather"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FORMATTER-VARIANT SUPPORT TABLE
# Maps DNA → formatter → dict of variant restrictions.
# If a variant is listed, only those values are supported.
# If a variant is omitted, ALL values from VARIANTS_BY_DNA are supported.
# If a formatter is omitted, it supports ALL variants for that DNA.
# Use "*" as formatter key to set defaults for all formatters.
# ═══════════════════════════════════════════════════════════════════════════════

FORMATTER_VARIANT_SUPPORT: Dict[str, Dict[str, Dict[str, List[str]]]] = {

    # ── Number & Algebra ──────────────────────────────────────────────────────

    "addition": {
        # number_line only supports find_sum (can't show missing addend well)
        "number_line_read": {"task_type": ["find_sum"], "context": ["pure"]},
        "number_line_set": {"task_type": ["find_sum"], "context": ["pure"]},
        # number_bond supports all task_types
        "number_bond": {"context": ["pure"]},
    },

    "subtraction": {
        "number_line_read": {"task_type": ["find_difference"], "context": ["pure"]},
        "number_bond": {"context": ["pure"]},
    },

    "multiplication": {
        "table": ["2", "3", "4", "5", "10"],
        "structure": ["result_unknown"],
        # array grid naturally shows product, not missing factor
        "array_grid_read": {"task_type": ["find_product"], "context": ["pure"]},
        "array_grid_set": {"task_type": ["find_product"], "context": ["pure"]},
    },

    "division": {
        "remainder": ["none", "some"],
        "table": ["2", "3", "4", "5", "10"],
        "structure": ["result_unknown"],
        "array_grid_read": {"task_type": ["find_quotient"], "context": ["pure"]},
        "array_grid_set": {"task_type": ["find_quotient"], "context": ["pure"]},
    },

    "missing_number": {
        "balance_scale": {"context": ["pure"]},
    },

    "counting": {
        # emoji_pictorial only works for forward counting
        "emoji_pictorial": {"direction": ["forward"]},
        "number_line_read": {"context": ["pure"]},
        "ordering": {"context": ["pure"]},
    },

    "place_value": {
        "include_zeros": ["yes", "no"],
        # blocks work best for compose/decompose
        "place_value_blocks_read": {"task_type": ["identify_value", "compose", "identify_place"], "context": ["pure"]},
        "place_value_blocks_set": {"task_type": ["compose", "decompose", "identify_value"], "context": ["pure"]},
    },

    "comparing_ordering": {
        "proximity": ["close", "far"],
        "sort_order": {"task_type": ["order_sequence"], "context": ["pure"]},
        "ordering": {"task_type": ["order_sequence"], "context": ["pure"]},
        "mcq": {"task_type": ["compare_pair", "find_between"]},
        "cloze": {"task_type": ["compare_pair", "find_between"]},
        "true_false": {"task_type": ["compare_pair", "find_between"]},
    },

    "patterns": {
        "element_type": ["numbers", "shapes"],
        "ask_type": ["next", "missing"],
        # visual pattern sequence works for find_next
        "pattern_sequence": {"task_type": ["find_next"]},
        "fill_in_table": {"task_type": ["find_missing", "find_rule"]},
    },

    "fractions": {
        "context": ["pure", "word_problem"],
        "fraction_type": ["proper"],
        "operation": ["add", "subtract"],
        # Visual formatters render every operation the fractions DNA emits,
        # including add/subtract (fmt_fraction_model.py:204-243,
        # fmt_fraction_shade.py:185-198). The previous cap restricted these
        # to identify_name/compare (resp. equivalent), which silently
        # rejected every add/subtract profile for mat_g3_na_q4_7 and caused
        # the orchestrator to raise "No compatible formatters available".
        "fraction_model_read": {"operation": ["identify_name", "compare", "add", "subtract", "add_subtract"]},
        "fraction_shade":      {"operation": ["identify_name", "equivalent", "add", "subtract", "add_subtract"]},
    },

    "money_peso": {
        "denomination_type": ["coins", "bills", "mixed"],
        "operation": ["add", "subtract"],
        # visual peso formatters don't handle word problems
        "peso_money_read": {"task_type": ["count_total"], "context": ["pure"]},
        "peso_money_build": {"task_type": ["count_total", "make_change"], "context": ["pure"]},
    },

    "number_reading": {
        "mcq": {"context": ["pure"]},
        "cloze": {"context": ["pure"]},
        "true_false": {"context": ["pure"]},
        # A number line can only ever show a numeral position — it cannot
        # represent a word-form answer. Restrict to word_to_numeral (numeral
        # is the answer); numeral_to_word doesn't fit this visual formatter.
        "number_line_read": {"context": ["pure"], "task_type": ["word_to_numeral"]},
        "number_line_set": {"context": ["pure"], "task_type": ["word_to_numeral"]},
    },

    "rounding": {
        # number line good for showing rounding visually
        "number_line_read": {"task_type": ["round_to_place"], "context": ["pure"]},
    },

    # ── Measurement & Geometry ────────────────────────────────────────────────

    "time_reading": {
        "context": ["pure", "word_problem"],
        "mode": ["analog", "digital"],
        "include_ampm": ["yes", "no"],
        "clock_read": {"task_type": ["read_time"]},
        "clock_set": {"task_type": ["set_time"]},
        # elapsed_time only via mcq/cloze
    },

    "calendar": {
        "context": ["pure", "word_problem"],
        "calendar_feature": ["days", "weeks", "months", "dates"],
        "calendar_read": {},  # all task types work
    },

    "area": {
        "shape": ["rectangle", "square"],
        "unit": ["cm", "m"],
        # grid_area shows counting squares
        "grid_area": {"task_type": ["find_area"]},
    },

    # ── Data & Probability ────────────────────────────────────────────────────

    "pictographs": {
        "mcq": {"task_type": ["read_value", "compare_two", "find_total", "find_difference"]},
        "pictograph_read": {"task_type": ["read_value", "compare_two", "find_total", "find_difference"]},
        "pictograph_set": {"task_type": ["present_data"]},
        "fill_in_table": {"task_type": ["organize_table"]},
    },

    "bar_graphs": {
        "bar_chart_read": {},  # all task types
        "bar_chart_set": {"task_type": ["read_value"]},  # set mode is simpler
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# VARIANT HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_variants_for_dna(dna_concept: str) -> Dict[str, List[str]]:
    """
    Return all contextual variants defined for a DNA concept.

    Args:
        dna_concept: DNA concept name, e.g. "addition".

    Returns:
        Dict mapping variant names to their possible values.
        Empty dict if concept not found.
    """
    return dict(VARIANTS_BY_DNA.get(dna_concept, {}))


def get_supported_variants(
    dna_concept: str,
    formatter_name: str
) -> Dict[str, List[str]]:
    """
    Return variants supported by a specific DNA + formatter combination.

    Applies restrictions from FORMATTER_VARIANT_SUPPORT on top of
    the full variant set from VARIANTS_BY_DNA.

    Args:
        dna_concept: DNA concept name, e.g. "addition".
        formatter_name: Formatter name, e.g. "number_line_read".

    Returns:
        Dict mapping variant names to their allowed values for this
        formatter. If formatter has no restrictions, returns full
        variant set for the DNA.
    """
    base_variants = get_variants_for_dna(dna_concept)
    if not base_variants:
        return {}

    # Check if this DNA has formatter-specific restrictions
    dna_restrictions = FORMATTER_VARIANT_SUPPORT.get(dna_concept, {})
    formatter_restrictions = dna_restrictions.get(formatter_name)

    # No restrictions defined → all variants supported
    if formatter_restrictions is None:
        return base_variants

    # Apply restrictions
    result = {}
    for variant_name, all_values in base_variants.items():
        if variant_name in formatter_restrictions:
            # Use restricted values
            result[variant_name] = formatter_restrictions[variant_name]
        else:
            # No restriction on this variant → all values allowed
            result[variant_name] = all_values

    return result


def is_variant_supported(
    dna_concept: str,
    formatter_name: str,
    variant_name: str,
    variant_value: str
) -> bool:
    """
    Check if a specific variant value is supported for a DNA + formatter.

    Args:
        dna_concept: DNA concept name, e.g. "addition".
        formatter_name: Formatter name, e.g. "number_line_read".
        variant_name: Variant name, e.g. "task_type".
        variant_value: Variant value, e.g. "find_sum".

    Returns:
        True if the variant value is supported, False otherwise.
    """
    supported = get_supported_variants(dna_concept, formatter_name)
    allowed_values = supported.get(variant_name, [])
    return variant_value in allowed_values


def get_compatible_formatters_for_variant(
    dna_concept: str,
    variant_name: str,
    variant_value: str
) -> List[str]:
    """
    Return formatters that support a specific variant value.

    Useful for lab UI to filter formatter dropdown based on selected variant.

    Args:
        dna_concept: DNA concept name, e.g. "addition".
        variant_name: Variant name, e.g. "task_type".
        variant_value: Variant value, e.g. "find_addend".

    Returns:
        List of formatter names that support this variant value.
    """
    all_formatters = get_formatters_for_dna(dna_concept)
    return [
        fmt for fmt in all_formatters
        if is_variant_supported(dna_concept, fmt, variant_name, variant_value)
    ]


def validate_lab_selection(
    dna_concept: str,
    formatter_name: str,
    selected_variants: Dict[str, str]
) -> Dict[str, Any]:
    """
    Validate a lab UI selection and return compatibility info.

    Args:
        dna_concept: DNA concept name.
        formatter_name: Selected formatter.
        selected_variants: Dict of variant_name → selected_value.

    Returns:
        Dict with:
            valid: bool - True if all selections are compatible
            errors: List[str] - Error messages for incompatible selections
            warnings: List[str] - Warnings (e.g., will fall back to MCQ)
            effective_formatter: str - Actual formatter that will be used
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "effective_formatter": formatter_name,
    }

    # Check if formatter is compatible with DNA
    if formatter_name not in get_formatters_for_dna(dna_concept):
        result["valid"] = False
        result["errors"].append(
            f"Formatter '{formatter_name}' is not compatible with '{dna_concept}'"
        )
        return result

    # Check each variant
    supported = get_supported_variants(dna_concept, formatter_name)
    incompatible_variants = []

    for variant_name, variant_value in selected_variants.items():
        if variant_name not in supported:
            # Variant doesn't exist for this DNA
            result["warnings"].append(
                f"Variant '{variant_name}' is not defined for '{dna_concept}'"
            )
            continue

        if variant_value not in supported[variant_name]:
            incompatible_variants.append(
                f"{variant_name}={variant_value}"
            )

    if incompatible_variants:
        result["warnings"].append(
            f"Variants {incompatible_variants} not supported by '{formatter_name}'. "
            f"Will fall back to 'mcq'."
        )
        result["effective_formatter"] = "mcq"

    return result


