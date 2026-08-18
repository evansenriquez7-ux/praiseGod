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
    # 10000, not 9999: "represent numbers up to 10 000" (mat_g3_na_q1_0)
    # has a range ceiling of exactly 10000, and this limit is checked
    # STATICALLY against the node's declared ceiling before any value is
    # generated (orchestrator.py's formatter-availability pre-filter) --
    # a 9999 cap excluded this formatter from the node entirely,
    # regardless of what any specific seed would actually generate
    # (confirmed live: "No compatible formatters available"). _decompose()
    # handles exactly 10000 correctly (10 thousand-blocks, thousands=10)
    # since it's plain divmod with no digit-count assumption baked in.
    "place_value_blocks_read": {"max_val": 10000},
    "place_value_blocks_set": {"max_val": 10000},
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

    # Addition: expanded form requires tens and ones place value introduced in G1 Q2 (mat_g1_na_q2_2)
    ("addition", "task_type", "expanded_form"): (1, 2),
    ("addition", "strategy", "expanded_form"): (1, 2),
    ("addition", "task_type", "associative"): (2, 1),

    # Multiplication: multi_digit introduced in G3Q3 (2-3 digit × 1-digit operations)
    ("multiplication", "number_type", "multi_digit"): (3, 3),

    # Length measurement: standard units (cm/m) are a G2 competency — G1 uses
    # non-standard units only (paperclips, hands, steps).
    ("length_measurement", "unit_type", "cm"): (2, 1),
    ("length_measurement", "unit_type", "m"): (2, 1),
    # Unit conversion is NOT a G1-G3 competency. Grepping every competency in the
    # knowledge graph for "convert"/"conversion" returns nothing, and
    # mat_g2_mg_q2_3's cumulative_concepts carries no conversion concept either --
    # yet this gate admitted the task from G2 Q1, and a blind reviewer found
    # "Convert 4 m to cm." rendering inside "Solve problems involving length and
    # distance" and scored the node FAIL: a bare metre-to-centimetre conversion
    # needing a x100 the grade has not been taught. Producing content no competency
    # names is invention (CLAUDE.md Content Rule 3), so the gate moves past this
    # graph entirely rather than the task_type being deleted -- keeping it declared
    # leaves the §1C sweep intact, exactly as the `estimate` gating did.
    ("length_measurement", "task_type", "convert"): (4, 1),
    # missing_number's param_bounds give G2 the 2/3/4/5/10 tables and only G3 the
    # full 2-9 set, so the 6-9 tables are not selectable before Grade 3.
    ("missing_number", "tables", "6"): (3, 1),
    ("missing_number", "tables", "7"): (3, 1),
    ("missing_number", "tables", "8"): (3, 1),
    ("missing_number", "tables", "9"): (3, 1),
    # length_measurement.generate_params raises for choose_unit below grade 2
    # ("m vs cm" presupposes standard units, which G1 does not use), but the gate
    # was never registered here — so the Lab offered the option at G1 and every
    # generation crashed. The gate mirrors the DNA's own rule.
    ("length_measurement", "task_type", "choose_unit"): (2, 1),
    # Length estimation enters the curriculum at mat_g2_mg_q2_2 ("Estimate length
    # using meters or centimeters, and distance using meters") and nowhere earlier
    # -- no Grade 1 competency in the knowledge graph asks a pupil to estimate a
    # length at all. Ungated, this task_type reached mat_g1_mg_q2_2 ("Solve problems
    # involving lengths and distances using non-standard units"), where a blind
    # reviewer found it rendering a rounding exercise the grade has not been taught:
    # "'Rounded to the nearest 10' again asks for a rounding operation this grade's
    # measurement competency does not call for and Grade 1 has not yet taught."
    ("length_measurement", "task_type", "estimate"): (2, 2),

    # Geometric lines: point/segment/ray and parallel/perp enter at G3 Q1 (mat_g3_mg_q1_4/5)
    ("geometric_lines", "task_type", "recognize_model"): (3, 1),
    ("geometric_lines", "task_type", "draw_construct"): (3, 1),
    ("geometric_lines", "concept_type", "point_line_segment_ray"): (3, 1),
    ("geometric_lines", "concept_type", "parallel_intersecting_perpendicular"): (3, 1),

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
            # "equivalent" (equivalent-expressions task, e.g. mat_g1_na_q3_2)
            # is a G1 addition/subtraction-family variant, not a new
            # operation -- it must be allowed alongside addition/subtraction
            # here or the curriculum gate rejects it outright regardless of
            # what registry.py binds.
            return variant_value in ("addition", "subtraction", "equivalent")

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
        # "ordering" removed (2026-08-06, Ground Rule 5): a counting
        # sequence (skip-counting, "what comes next") is already in a
        # fixed, meaningful order -- fmt_ordering.py shuffles it and asks
        # the student to re-sort it, which is comparing_ordering's skill
        # (rank an unordered set), not counting's own ("continue this
        # sequence" / "count up or down from a given number"). Also
        # exposed a genuine wrong-answer-key bug: counting's own
        # "direction":"forward"/"backward" vocabulary collided with
        # fmt_ordering.py's "ascending"/"descending" check, producing
        # mismatched text/answer pairs (blind review of mat_g1_na_q1_0
        # seed 72: asked "largest to smallest", keyed ascending).
        "number_line_read",
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
        # "fill_in_table" removed -- see patterns.py DNA definition's
        # identical comment (categorical count-table formatter, no
        # relation to patterns.py's actual sequence/rule data).
    ],

    "fractions": [
        "mcq",
        "cloze",
        "fraction_model_read",
        "fraction_shade",
        # "ordering" deliberately excluded -- see fractions.py DNA
        # definition's identical comment and registry.py's "order"
        # binding comment (§1C's exhaustive sweep defeats any attempt to
        # scope it to only the nodes where it's mathematically safe).
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
        # mcq/cloze added for the new elapsed_time task_type (mat_g2_mg_
        # q4_2): elapsed-time problems are inherently textual word
        # problems (a start/end time and a duration), not a single-clock
        # visual read/set -- scoped to task_type=="elapsed_time" only via
        # FORMATTER_VARIANT_SUPPORT below, so the default clock-reading
        # path (task_type=="clock_reading") never picks them.
        "mcq",
        "cloze",
    ],

    "calendar": [
        "calendar_read",
        # task_type="sequence" (recite/order day or month names) has no
        # calendar grid to show and is excluded from calendar_read's own
        # FORMATTER_VARIANT_SUPPORT entry above -- mcq is its only
        # compatible formatter.
        "mcq",
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
        # shape_board removed: it cannot illustrate these items and never could.
        # symmetry_slides asks about arrows turning ("An arrow faces UP. It does
        # a quarter turn counter-clockwise...") and shapes sliding across a grid;
        # none of that is a member of shape_board's shape catalogue, so the
        # formatter fell straight through to its _build_shapes fallback and drew
        # an unrelated board of random polygons on every single generation
        # (20/20 when forced), discarding the DNA's question and answer. The
        # table asserted a capability the formatter does not have. Rendering
        # these properly needs a formatter that can draw an oriented arrow or a
        # translated figure; until one exists, mcq states the item honestly.
    ],

    # ── Data & Probability ────────────────────────────────────────────────────

    "pictographs": [
        "pictograph_read",
        "pictograph_set",
        "fill_in_table",
        "table_read",
        "mcq",
    ],

    "bar_graphs": [
        "bar_chart_read",
        "bar_chart_set",
    ],

    "probability_language": [
        "mcq",
    ],

    "probability_experiment": [
        "mcq",
        "cloze",
        "true_false",
        "error_detect",
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
        "task_type": [
            "zero_identity", "commutative", "associative",
            "expanded_form", "counting_up", "putting_together",
            "models_strategies",
        ],
    },

    "subtraction": {
        "context": ["pure", "word_problem"],
        "structure": ["result_unknown", "change_unknown", "start_unknown"],
        "spine": ["taking_away", "comparing"],
    },

    "multiplication": {
        "table": ["2", "3", "4", "5", "6", "7", "8", "9", "10"],
        "structure": ["result_unknown"],
        "number_type": ["single_digit", "multi_digit"],
        "context": ["pure", "word_problem"],
        "task_type": ["find_product", "zero_identity", "commutative", "associative", "distributive", "equal_groups", "repeated_addition", "skip_counting", "number_line_jumps", "two_step"],
    },

    "division": {
        "remainder": ["none", "with_remainder"],
        "table": ["2_3_4_5_10", "6_7_8_9", "one_digit_2_9", "one_digit_mixed_or_power_of_ten"],
        "structure": ["result_unknown", "divisor_unknown", "dividend_unknown"],
        "context": ["pure", "word_problem"],
        # Neither "estimate" nor "even_odd" is listed here, deliberately --
        # both work via the registry-scope exemption instead (like
        # multiplication's "estimate", also absent from its own
        # VARIANTS_BY_DNA task_type list), because each is bound directly by
        # registry.py's text match for the one node whose competency names
        # it. get_supported_variants has no per-node scoping: it's computed
        # once per (dna, formatter) pair from this table alone, so declaring
        # either value here made validate_matrix's §1C exhaustive sweep test
        # it against *every* division-mapped node's own vocabulary/formatter
        # set, not just its one intended node -- caught twice: "estimate"'s
        # "quotient" wording isn't introduced vocabulary at G2Q3
        # (mat_g2_na_q3_4), and "even_odd"'s "even"/"odd" wording isn't
        # introduced vocabulary at other G2Q3 division nodes either, plus
        # its categorical (non-numeric) answer crashes mcq/cloze/
        # error_detect's numeric-only distractor padding regardless of
        # vocabulary. Leaving task_type undeclared here sidesteps the
        # exhaustive sweep for both; real generation still resolves them
        # correctly because the registry binds task_type directly and the
        # DNA branch reads it from the profile regardless of any
        # VARIANTS_BY_DNA declaration.
    },

    "counting": {
        "direction": ["forward", "backward"],
        "context": ["pure", "word_problem"],
        "skip_interval": ["1", "2", "5", "10", "20", "50", "100"],
    },

    "number_reading": {
        "task_type": ["numeral_to_word", "word_to_numeral", "numeral_to_expanded", "identify_value", "number_line"],
    },

    "ordinal_numbers": {
        "task_type": ["identify_position", "identify_object"],
    },

    "place_value": {
        "include_zeros": ["yes", "no"],
        # "compose" was registered but never a real branch in
        # generate_params() (fell through to the identify_value default);
        # replaced with "identify_digit", the genuine reverse-lookup
        # sub-skill ("the digit of a number given its place value") this
        # competency names but the DNA never implemented.
        "task_type": ["identify_place", "identify_value", "identify_digit", "decompose"],
    },

    "comparing_ordering": {
        "proximity": ["close_together", "far_apart"],
        "task_type": ["compare_pair", "order_sequence"],
        "context": ["pure", "word_problem"],
        "direction": ["ascending", "descending"],
    },

    "missing_number": {
        "operation": ["addition", "subtraction", "multiplication", "division", "equivalent"],
        "equation_type": ["standard", "non_standard"],
        "blank_position": ["start", "middle", "end"],
        "context": ["pure", "word_problem"],
        # missing_number.py supports tables 2-9 at G3 (its own param_bounds say so)
        # and registry.py binds mat_g3_na_q4_2 to tables [6,7,8,9] — but 6-9 were
        # never declared here, so the Lab could not offer them and that competency
        # had no representable option at all. Gated to G3 below.
        "tables": ["2", "3", "4", "5", "6", "7", "8", "9", "10"],
    },

    "patterns": {
        # Every patterns-mapped node binds its own explicit pattern_type
        # AND ask_type in registry.py (verified: all 6 nodes have both),
        # so declaring either here serves no real exhaustive-coverage
        # purpose -- it only lets validate_matrix's §1C sweep and
        # judgment_packets.py's variant-coverage stratification request
        # ask_type="next"/"missing" against a node whose own competency is
        # scoped to "explain"/state_rule instead (mat_g3_na_q3_6: "Explain
        # how to generate..."), producing a genuinely different skill's
        # content under this node (blind review: seed 50's "What is the
        # missing term..." tests sibling node mat_g3_na_q3_5's own named
        # skill, not this one's). Real generation still resolves correctly
        # because the registry binds both directly and the DNA reads them
        # from the profile regardless of any VARIANTS_BY_DNA declaration
        # (same registry-scope-exemption pattern as division's "estimate"/
        # "even_odd"). "element_type" is additionally dead: patterns.py's
        # generate_params never reads it at all.
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
        # Matches order_of_operations.py's own generate_params check exactly
        # ("add_only" vs. anything else defaulting to mixed) -- the previous
        # ["add_sub", "mult_div", "all"] never matched any string the DNA
        # actually compares against (and "mult_div" is fiction: this DNA only
        # ever implements + and -, per its own "G3 Q2 ... MDAS subset" scope,
        # i.e. left-to-right + and - only). Caught only now because this DNA
        # was never mapped to a node before.
        "operation_mix": ["add_only", "mixed_add_sub"],
        "num_operands": ["three_terms", "four_terms"],
        "context": ["pure", "word_problem"],
    },

    "shapes_2d": {
        "orientation": ["standard", "rotated"],
        "shape_set": ["basic_triangles_rectangles_squares", "extended_with_circles", "composite_figures"],
        "task_type": ["identify_name", "count_sides_corners", "compare_shapes", "compose_decompose"],
    },

    "length_measurement": {
        "unit_type": ["cm", "m"],
        "task_type": [
            "compare", "convert", "read_measurement", "choose_unit", "estimate",
            "distance_between", "equal_length", "compare_distance",
            "solve_problems_non_standard", "solve_word_problem",
        ],
        "context": ["pure", "word_problem"],
    },

    "mass_capacity": {
        "unit": ["g", "kg", "ml", "l"],
        "task_type": ["compare", "convert", "read_measurement", "estimate"],
        "measurement_type": ["mass", "capacity"],
    },

    "time_reading": {
        "precision": ["hour", "half_hour", "quarter_hour", "five_minutes", "one_minute"],
        "include_ampm": ["yes", "no"],
        "mode": ["read", "set"],
        "task_type": ["clock_reading", "elapsed_time"],
        "context": ["pure", "word_problem"],
    },

    "calendar": {
        # Must match calendar.py's real internal task_type strings.
        "task_type": ["read_day", "read_month", "find_date", "elapsed_days", "elapsed_weeks", "sequence"],
        "calendar_feature": ["days", "weeks", "months", "dates"],
    },

    "perimeter": {
        # Must match perimeter.py's real internal task_type strings -- the
        # previous "calculate"/"missing_side" values matched neither the
        # DNA's actual "find_perimeter"/"find_missing_side" values.
        "shape": ["square", "rectangle", "triangle"],
        "task_type": ["find_perimeter", "find_missing_side", "identify_and_measure", "identify_definition", "measure_tools"],
        "context": ["pure", "word_problem"],
    },

    "area": {
        # Must match area.py's real internal task_type strings -- the
        # previous "calculate"/"missing_side" values matched neither the
        # DNA's actual "find_area"/"find_missing_dimension" values nor its
        # newer "illustrate_tiles"/"derive_formula" values, so this table
        # never restricted anything meaningfully for area.
        "shape": ["square", "rectangle"],
        "task_type": ["find_area", "find_missing_dimension", "illustrate_tiles", "derive_formula"],
        "unit": ["square_cm", "square_m"],
        "context": ["pure", "word_problem"],
    },

    "geometric_lines": {
        # Must match geometric_lines.py's _ITEM_POOL concept_type/task_type
        # values exactly -- generate_params() raises (no silent fallback)
        # when a requested combination has zero grade-eligible items, so a
        # registered variant value that doesn't exist in the pool is a hard
        # failure at generation time, not a quietly-wrong substitution.
        "task_type": ["identify_name", "identify_property", "recognize_model", "draw_construct"],
        "concept_type": ["straight_curved", "parallel_intersecting_perpendicular", "point_line_segment_ray"],
    },

    "symmetry_slides": {
        # Must match symmetry_slides.py's _ITEM_POOL concept/directions
        # values exactly -- generate_params() raises (no silent fallback)
        # when a requested combination has zero grade-eligible items.
        "concept": ["rotation", "slide_translation", "line_symmetry", "complete_symmetric_figure"],
        "directions": ["one_direction", "two_directions"],
    },

    "pictographs": {
        "task_type": ["read_value", "compare_two", "find_total", "find_difference", "present_data", "organize_table", "read_table", "collect_interview"],
        "scale_type": ["no_scale", "scale_2", "scale_5", "scale_10"],
    },

    "bar_graphs": {
        "task_type": ["read_value", "compare_bars", "find_total", "find_difference", "find_most_least", "present_data", "solve_problem"],
        "orientation": ["vertical", "horizontal", "table"],
        "scale": ["scale_5", "scale_10", "scale_20"],
    },

    "probability_language": {
        "scenario_type": ["certain_impossible", "equally_likely", "comparative", "superlative", "likely_unlikely"],
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
        "number_line_read": {"task_type": ["find_sum", "counting_up"], "context": ["pure"]},
        "number_line_set": {"task_type": ["find_sum", "counting_up"], "context": ["pure"]},
        # emoji_pictorial (visual ten-frame/counters) and number_bond
        # model concrete addition, not symbolic algebraic properties
        "emoji_pictorial": {"task_type": ["find_sum", "putting_together", "visual_counting", "counting_up"]},
        # number_bond models part-whole decomposition
        "number_bond": {"task_type": ["find_sum", "putting_together", "part_part_whole", "missing_addend"], "context": ["pure"]},
        # commutative/associative render a Yes/No claim ("Is a+b the same
        # as b+a?"), not a numeric fact -- error_detect's "character says
        # <value>, correct?" framing serves that claim's boolean answer as
        # the string "True"/"False" rather than a Python bool, which
        # defeats §1E's isinstance(bool) skip and false-positives as answer
        # corruption against the raw arithmetic recomputation.
        "error_detect": {
            "task_type": ["zero_identity", "expanded_form", "counting_up", "putting_together"]
        },
        # true_false wraps a statement in its OWN "...True or False?"
        # judgment -- commutative/associative's claim ("Is a+b the same as
        # b+a?") is already that judgment, and its blank_target="answer"
        # (no "result" key at all) fell through this formatter's
        # blank_target=="a" default branch to render "{fill} + {b} =
        # None" (blind review of mat_g1_na_q1_7 seed 613, same root cause
        # as the fmt_mcq.py fix for this task_type).
        "true_false": {
            "task_type": ["zero_identity", "expanded_form", "counting_up", "putting_together"]
        },
        # cloze is a fill-in-the-blank formatter -- commutative/associative's
        # yes/no claim has no blank to fill (blank_target="answer", no
        # "result" key), so _build_equation_sentence's generic blank_target
        # branches rendered "___ + {b} = None" (same root cause as the
        # error_detect/true_false restrictions above, just never applied to
        # cloze). Same allow-list.
        "cloze": {
            "task_type": ["zero_identity", "expanded_form", "counting_up", "putting_together"]
        },
    },

    "subtraction": {
        "number_line_read": {"task_type": ["find_difference", "counting_back"], "context": ["pure"]},
        "number_bond": {"task_type": ["find_difference"], "context": ["pure"]},
        "emoji_pictorial": {"task_type": ["find_difference", "take_away", "taking_away", "counting_back"], "context": ["pure", "word_problem"]},
    },

    "length_measurement": {
        # ruler_measure draws a ruler with an object laid against it and asks
        # "How long is the object?" — that is read_measurement and nothing else.
        # length_measurement had no entry in this table at all, so the formatter
        # was offered for every task_type: mat_g2_mg_q2_1 is bound
        # task_type="choose_unit" ("Which unit would you use to measure a
        # book: centimeters or meters?") and served a ruler-reading item whose
        # answer key came from invented visual params, with the DNA's actual
        # choose_unit item discarded. compare ("which is longer?") and estimate
        # are equally undrawable on a single ruler — estimate especially, since
        # a ruler hands over the measurement the student is meant to estimate.
        # distance_between belongs here with read_measurement: it is the same
        # read-the-visual task, measuring a gap rather than an object, and the ruler
        # renders it correctly (object_start/object_end span the gap). Without it the
        # task fell to mcq/cloze, where "A box and a bag are placed apart. The
        # distance between them is ___ blocks." keyed 5 against distractors 4/6/7
        # with nothing in the item to distinguish them -- 93 of 200 samples on
        # mat_g1_mg_q2_0, and a blind reviewer scored the node FAIL for it.
        #
        # Note the fix is to give the task its visual, NOT to restrict it and hope:
        # at G1 there is no other visual formatter, so restricting alone would have
        # left the task unrenderable.
        "ruler_measure": {"task_type": ["read_measurement", "distance_between"]},
        # The reverse restriction, which was missing. Limiting ruler_measure to
        # read_measurement stopped the ruler serving the wrong tasks, but nothing
        # stopped mcq and cloze serving read_measurement -- and that direction is
        # just as broken, because read_measurement is a READ-THE-VISUAL task: strip
        # the ruler and the item has nothing in it to read. It rendered "Measure the
        # object. Its length is ___ cm." 171 times through mcq and 69 through cloze,
        # against only 32 answerable ruler items. A blind reviewer scored two nodes
        # FAIL for it -- "nothing in the stem or sample determines the keyed answers
        # 1, 2, 2, 3" -- and noted those were "precisely the items that would have
        # carried the verb measure", so the competency lost its verb to a broken item.
        #
        # Listing every task_type EXCEPT read_measurement is how this table excludes
        # a value; it has no negative form.
        "mcq": {"task_type": ["compare", "convert", "choose_unit", "estimate",
                              "equal_length", "compare_distance", "solve_problems_non_standard", "solve_word_problem"]},
        "cloze": {"task_type": ["compare", "convert", "choose_unit", "estimate",
                                "equal_length", "compare_distance", "solve_problems_non_standard", "solve_word_problem"]},
    },

    "multiplication": {
        "table": ["2", "3", "4", "5", "10"],
        "structure": ["result_unknown"],
        # array grid naturally shows product, not missing factor -- that concern
        # is about `structure`, which "structure": ["result_unknown"] above
        # already constrains. Restricting task_type to find_product alone also
        # excluded repeated_addition and equal_groups, which is backwards: an
        # array IS the pictorial model those two competencies are about.
        # mat_g2_na_q3_1 reads "Illustrate and write multiplication as repeated
        # addition, using a variety of concrete and pictorial models ...,
        # arrays, counting by multiples, and equal jumps on a number line" --
        # it names arrays outright, yet this gate made array_grid_read and
        # array_grid_set unreachable on it, so all 11 sampled seeds served mcq
        # and blind review scored it FAIL: "no pictorial or concrete model is
        # shown" and "None of the competency's named representations -- arrays,
        # counting by multiples, or equal jumps on a number line -- appear
        # anywhere in the eleven samples."
        "array_grid_read": {"task_type": ["find_product", "zero_identity", "repeated_addition", "equal_groups", "skip_counting", "number_line_jumps"], "context": ["pure"]},
        "array_grid_set": {"task_type": ["find_product", "zero_identity", "repeated_addition", "equal_groups", "skip_counting", "number_line_jumps"], "context": ["pure"]},
        "error_detect": {"task_type": ["find_product", "estimate", "zero_identity", "equal_groups", "repeated_addition", "skip_counting", "number_line_jumps", "two_step"]},
        "true_false": {"task_type": ["find_product", "estimate", "zero_identity", "equal_groups", "repeated_addition", "skip_counting", "number_line_jumps", "two_step"]},
        "cloze": {"task_type": ["find_product", "estimate", "zero_identity", "equal_groups", "repeated_addition", "skip_counting", "number_line_jumps", "two_step"]},
    },

    "division": {
        "remainder": ["none", "some"],
        "table": ["2", "3", "4", "5", "10"],
        "array_grid_read": {"task_type": ["find_quotient"], "context": ["pure"], "table": ["2_3_4_5_10", "6_7_8_9"], "remainder": ["none"], "structure": ["result_unknown"]},
        "array_grid_set": {"task_type": ["find_quotient"], "context": ["pure"], "table": ["2_3_4_5_10", "6_7_8_9"], "remainder": ["none"], "structure": ["result_unknown"]},
        # even_odd's answer is a categorical "even"/"odd" string with only
        # one possible opposite value -- get_supported_variants has no
        # per-node scoping (it's computed once per (dna, formatter) pair
        # from VARIANTS_BY_DNA + this table alone), so declaring "even_odd"
        # in VARIANTS_BY_DNA["division"]["task_type"] makes validate_matrix's
        # §1C exhaustive sweep test it against every formatter for every
        # division-mapped node, not just mat_g2_na_q3_8. mcq/cloze/
        # error_detect all build a 4-option pool from ctx.distractors and
        # pad missing slots via numeric offsets (isinstance(correct, (int,
        # float))), which raises for a string correct answer with fewer
        # than 3 distinct distractors (confirmed: "MCQ formatter could not
        # generate enough distractors for string correct answer 'even'").
        # true_false is the only formatter that fits a binary judgment
        # without needing extra distractors, so it's the only one left
        # unrestricted.
        "mcq": {"task_type": ["find_quotient", "estimate", "number_line_jumps", "inverse_of_multiplication"]},
        "cloze": {"task_type": ["find_quotient", "estimate", "number_line_jumps", "inverse_of_multiplication"]},
        "error_detect": {"task_type": ["find_quotient", "estimate", "number_line_jumps", "inverse_of_multiplication"]},
    },

    "missing_number": {
        # operation="equivalent" (mat_g1_na_q3_2: "Write an equivalent
        # expression...") returns TWO equated expressions (a+b=c+d), a
        # structure this visual formatter has no concept of at all --
        # _build_balance_params only ever renders a single "a op b = ?"
        # equation, _stem() never checks ctx.values["question"] (the
        # equivalent branch's own narrative), and its op_char lookup has
        # no "equivalent" entry so it silently defaults to "+" regardless
        # of whether the underlying expression is add- or subtract-based
        # (blind review: "19 + ? = 16" served answer 3, which is only
        # correct for 19 - ? = 16, not addition -- a genuine math error
        # in what the visual displayed vs. what it graded).
        "balance_scale": {"context": ["pure"], "operation": ["addition", "subtraction", "multiplication", "division"]},
    },

    "counting": {
        # emoji_pictorial only works for forward counting
        "emoji_pictorial": {"direction": ["forward"]},
        "number_line_read": {"context": ["pure"]},
        "ordering": {"context": ["pure"]},
    },

    "place_value": {
        "include_zeros": ["yes", "no"],
        "mcq": {"task_type": ["identify_value", "identify_digit", "compose", "decompose"]},
        # blocks work best for compose/decompose
        "place_value_blocks_read": {"task_type": ["compose"], "context": ["pure"]},
        "place_value_blocks_set": {"task_type": ["compose", "decompose"], "context": ["pure"]},
    },

    "comparing_ordering": {
        "proximity": ["close", "far"],
        # "context": ["pure"] used to be the only value here because
        # comparing_ordering.py never generated word-problem framing for
        # order_set at all -- context was effectively always "pure" in
        # practice regardless of what was requested. Now that it does
        # (fmt_ordering.py prefers values["question"] when present), this
        # restriction has to allow "word_problem" too, or task_type=
        # "order_sequence" + context="word_problem" has NO compatible
        # formatter at all (mcq/cloze/true_false below don't support
        # order_sequence either) -- confirmed live: "No compatible
        # formatters available for DNA 'comparing_ordering'" at scalar 0.0
        # for every order_set-bound node once word_problem context could
        # be drawn.
        "sort_order": {"task_type": ["order_sequence"], "context": ["pure", "word_problem"]},
        "ordering": {"task_type": ["order_sequence"], "context": ["pure", "word_problem"]},
        "mcq": {"task_type": ["compare_pair", "find_between"]},
        "cloze": {"task_type": ["compare_pair", "find_between"]},
        "true_false": {"task_type": ["compare_pair", "find_between"]},
    },

    "patterns": {
        "element_type": ["numbers", "shapes"],
        "ask_type": ["next", "missing"],
        # visual pattern sequence works for find_next
        # ask_type is restricted too: this visual renders one sequence with blanked
        # positions, so it can express "what comes next/what is missing" but not
        # ask_type="identify_valid" (choose which of four candidate sequences follows
        # the rule) or "state_rule" — those have no blank to render and produced a
        # zero-option problem when routed here.
        "pattern_sequence": {"task_type": ["find_next"], "ask_type": ["next", "missing"]},
        # "fill_in_table" removed -- see patterns.py DNA definition's
        # comment (that formatter is a categorical count table with no
        # relation to patterns.py's sequence/rule data).
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
        # Both visual formatters' schemas model a SINGLE shape
        # (total_parts/shaded_parts) -- fine for a proper fraction
        # (shaded <= total), but "improper"/"mixed" fraction_type
        # (mat_g3_na_q4_6: "equal to one and greater than one") can
        # produce a numerator bigger than the denominator, which these
        # single-shape trap/visual builders have no representation for
        # (count_unshaded goes negative, "shade 17 of 5 parts" has no
        # valid rendering on one shape). base_generator's own symbolic
        # question text now handles improper fractions by describing
        # multiple identical shapes -- restrict these two visual
        # formatters to the fraction_type values that stay within a
        # single shape until their schemas gain real multi-shape support.
        "fraction_model_read": {
            "operation": ["identify_name", "compare", "add", "subtract", "add_subtract"],
            "fraction_type": ["unit_fraction", "unit", "similar_proper", "proper"],
            # "represent and identify" nodes (mat_g2_na_q4_0/_3) vs "read
            # and write... in fraction notation" siblings (mat_g2_na_q4_1/
            # _4) -- see registry.py's fraction_task_mode binding comment.
            # Absent for every OTHER fractions node (compare/add_subtract/
            # count_sequence never set this axis), so this restriction
            # only ever excludes the notation-only nodes, never those.
            "fraction_task_mode": ["model"],
        },
        "fraction_shade": {
            "operation": ["identify_name", "equivalent", "add", "subtract", "add_subtract"],
            "fraction_type": ["unit_fraction", "unit", "similar_proper", "proper"],
            "fraction_task_mode": ["model"],
        },
        # operation="order" (mat_g2_na_q4_2/mat_g2_na_q4_5) returns a LIST
        # under blank_target="sequence" -- mcq/cloze/numeric_input expect a
        # single scalar correct answer and crash against a list (mcq:
        # "could not generate enough distractors for string correct
        # answer ['1/8','1/2',...]"). "order" itself is currently disabled
        # (see registry.py's `False and "order" in text` guard) but these
        # allow-lists stay as a safety net if it's ever re-enabled.
        # "count_sequence" (mat_g1_na_q4_2: "Count halves and quarters")
        # returns a single fraction-string answer (not a list, unlike
        # "order" above), so it fits mcq/cloze/numeric_input directly --
        # unlike fraction_model_read/fraction_shade, which model a single
        # shape and have no way to show 4 sequence terms at once.
        # fraction_task_mode="model" (mat_g2_na_q4_0/_3, "represent and
        # identify") is excluded here so those nodes render exclusively
        # through the visual formatters above -- absent for every other
        # operation, so this never affects compare/add_subtract/
        # count_sequence.
        "mcq":           {"operation": ["identify_name", "compare", "add", "subtract", "add_subtract", "count_sequence"], "fraction_task_mode": ["notation"]},
        "cloze":         {"operation": ["identify_name", "compare", "add", "subtract", "add_subtract", "count_sequence"], "fraction_task_mode": ["notation"]},
        "numeric_input": {"operation": ["identify_name", "compare", "add", "subtract", "add_subtract", "count_sequence"]},
    },

    "money_peso": {
        "denomination_type": ["coins", "bills", "mixed"],
        "operation": ["add", "subtract"],
        # visual peso formatters don't handle word problems
        "peso_money_read": {"task_type": ["count_total"], "context": ["pure"]},
        "peso_money_build": {"task_type": ["count_total", "make_change"], "context": ["pure"]},
    },

    "number_reading": {
        # "identify_value" (mat_g1_na_q1_2/mat_g2_na_q1_2/mat_g3_na_q1_0's
        # block/bar-model representation) has no word/expanded form and no
        # inherent question phrasing of its own -- it exists to be read off
        # a visual (place_value_blocks). mcq/cloze/true_false's own
        # "number_reading" text builders don't check task_type at all, so
        # routing "identify_value" through them produced a mismatched
        # "Write 5 in words." stem keyed to the bare numeral answer "5"
        # (confirmed live). Excluded here the same way number_line excludes
        # numeral_to_word below.
        "mcq": {"context": ["pure"], "task_type": ["numeral_to_word", "word_to_numeral", "numeral_to_expanded", "read_and_write"]},
        "cloze": {"context": ["pure"], "task_type": ["numeral_to_word", "word_to_numeral", "numeral_to_expanded", "read_and_write"]},
        "true_false": {"context": ["pure"], "task_type": ["numeral_to_word", "word_to_numeral", "numeral_to_expanded", "read_and_write"]},
        "number_line_read": {"context": ["pure"], "task_type": ["number_line", "model_representation"]},
        "number_line_set": {"context": ["pure"], "task_type": ["number_line", "model_representation"]},
        "place_value_blocks_read": {"context": ["pure"], "task_type": ["identify_value", "model_representation"]},
        "place_value_blocks_set": {"context": ["pure"], "task_type": ["identify_value", "model_representation"]},
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
        # "read_time"/"set_time" never matched anything time_reading.py
        # actually set (its default path left task_type unset entirely),
        # so these were dead restrictions -- clock_read/clock_set passed
        # unconditionally via the orchestrator's "absent value always
        # passes" rule regardless of what this dict said. Now that the
        # default path explicitly sets task_type="clock_reading" (see
        # time_reading.py), match that real value instead.
        "clock_read": {"task_type": ["clock_reading"]},
        "clock_set": {"task_type": ["clock_reading"]},
        # elapsed_time (mat_g2_mg_q4_2) is a start/end/duration word
        # problem with no single clock to show -- textual only, and
        # excluded from the default clock_reading path by the same
        # task_type match above.
        "mcq": {"task_type": ["elapsed_time"]},
        "cloze": {"task_type": ["elapsed_time"]},
    },

    "calendar": {
        "context": ["pure", "word_problem"],
        "calendar_feature": ["days", "weeks", "months", "dates"],
        # task_type="sequence" (recite/order day or month names) has no
        # calendar grid to show -- generate_params() doesn't populate
        # visual_params meaningfully for it, so the visual formatter must
        # not claim to support it (an empty dict here previously meant
        # "all task types work", which let the calendar_read formatter get
        # picked for "sequence" and silently render an unrelated
        # date-lookup grid instead).
        "calendar_read": {"task_type": ["read_day", "read_month", "find_date", "elapsed_days", "elapsed_weeks"]},
        # mcq is calendar's other newly-added compatible formatter (see
        # COMPATIBILITY["calendar"] below) but is scoped to task_type=
        # "sequence" only -- the other task_types' string answers (e.g. a
        # bare day-of-week name) hit a pre-existing MCQ distractor-count
        # bug that was never reachable before mcq became compatible with
        # this DNA at all; fixing that generically is out of scope here.
        "mcq": {"task_type": ["sequence"]},
    },

    "area": {
        "shape": ["rectangle", "square"],
        "unit": ["cm", "m"],
        # grid_area draws a tiled figure and asks how many squares cover it.
        # It was offered to find_area, which is mat_g3_mg_q1_2's competency
        # ("Find the areas ... in sq. cm and sq. m") and part of q1_3's --
        # but the item it renders names no unit at all, so it cannot satisfy
        # either. Counting the tiles that cover a figure is precisely
        # mat_g3_mg_q1_0's competency ("Illustrate and estimate the area of a
        # square or rectangle using square tile units"), which is the one node
        # the formatter was gated off. Defect shape #3, in both directions at
        # once: unreachable where it belongs, and serving where it does not.
        # illustrate_tiles ONLY. Widening this to derive_formula as well was tried
        # and reverted in the same tick: fmt_array_grid renders one stem ("Look at
        # the 3x7 array. How many squares are shaded in all?") regardless of
        # task_type, so offering it to both made mat_g3_mg_q1_0 and mat_g3_mg_q1_1
        # byte-identical on seeds 55 and 500 -- trading one duplication for another,
        # which is the documented trap in opening a formatter gate. Any future
        # widening needs task-specific stem text in fmt_array_grid first.
        "grid_area": {"task_type": ["illustrate_tiles"]},
    },

    "pictographs": {
        "mcq": {"task_type": ["collect_interview"]},
        "pictograph_read": {"task_type": ["read_value", "compare_two", "find_total", "find_difference"]},
        "pictograph_set": {"task_type": ["present_data"]},
        "fill_in_table": {"task_type": ["organize_table"]},
        "table_read": {"task_type": ["read_table"]},
    },

    "bar_graphs": {
        "bar_chart_read": {"task_type": ["read_value", "compare_bars", "find_total", "find_difference", "find_most_least", "solve_problem"]},
        "bar_chart_set": {"task_type": ["present_data"]},
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


