"""DRAFT -- owner ruling 22(b) clause classification and ruling-19 sibling strata.

STATUS (2026-10-07, claude-h06-phase2-instrument-20261007): a DRAFT for the next agent.
No harness code reads this file or its output yet. Nothing here is a proven gate.

What it encodes
---------------
1. Every required clause of every node is classified exactly once: as a member of an
   ENUMERATION, or as not enumerated. An enumeration is two or more required clauses that
   the competency lists as alternative CONTENT the items range over -- objects, figures,
   cases, units, terms, properties, directions, arithmetic operations, named specific
   media. NOT enumerations: coordinated task verbs (read/write, compose/decompose; ruling
   9), abstract medium words such as "concrete" or "pictorial models" (rulings 12 and 15),
   parts present together in every item (the 2-digit and the 1-digit operand of one sum;
   "Compare 1/2 and 1/4", where every item shows both), and synonyms ("slide (or
   translation)"). This is a curriculum READING, recorded so it can be reviewed; it is not
   machine-derived.
2. Every enumeration member carries exactly one stratum disposition:
     selector              -- exact observations of STRUCTURED generator values (ruling
                              22a). Ops: equals, one_of, lt, gte, any_of (OR of condition
                              lists). No substring op exists. `path` names a key matched at
                              any depth of the sample's given_values; the special path
                              `visual_type` reads the rendered sample's visual_type.
     needs_instrumentation -- the sibling is visible only in learner-facing text; the DNA
                              must emit a structured field before it can be stratified.
     unserved              -- the generator's own vocabulary has no value for it.
   Siblings in one enumeration must not share a selector (a shared broad stratum, e.g.
   four rotation clauses all on `concept=rotation`, guarantees none of them).

Selectors are keyed per (node, member), never per capability id: 140 of the 472 ids are
shared by nodes whose DNAs emit different fields (`half_hour` is `precision` on
mat_g1_mg_q4_1 but `minute` on mat_g1_mg_q4_4).

Evidence basis: field values observed by rendering student-path seeds 1000-1039 per node
(`gv_probe.py`, `vt_probe.py` beside this file). `--check-renders` re-renders those seeds
and reports any selector observed fewer than 2 times. It does NOT run the packet builder.

Usage:
    PYTHONPATH=. .venv/bin/python validation_reports/phase2_hardening/ruling22_wip/build_clause_enumeration_draft.py OUT.json [--check-renders]
"""
import hashlib
import json
import sys

from backend.app.practice_gen.registry import get_all_node_ids, get_node_info


def eq(path, value):
    return {"observe": [{"path": path, "equals": value}]}


def one_of(path, values):
    return {"observe": [{"path": path, "one_of": list(values)}]}


def both(*conds):
    return {"observe": list(conds)}


def NI(reason):
    return {"needs_instrumentation": reason}


def UNSERVED(reason):
    return {"unserved": reason}


TEXT_ONLY = "sibling identity appears only in learner-facing question/answer text; no structured field"
COIN_BILL = ("no coin/bill flag in given_values; denomination values alone are ambiguous "
             "(P20 exists as both a coin and a bill)")
REGROUP = ("no structured with/without-regrouping flag; recomputing carries in the harness "
           "would duplicate a generator rule (memory: duplicated-rule-copies-disagree)")

E = {
    "mat_g1_mg_q1_0": [("triangle, rectangle, square", {
        "triangle": eq("answer", "triangle"), "rectangle": eq("answer", "rectangle"),
        "square": eq("answer", "square")})],
    "mat_g1_mg_q1_1": [("sides and corners", {
        "sides_of_a_shape": NI(TEXT_ONLY + " (task_type is compare_shapes for every item)"),
        "corners_of_a_shape": NI(TEXT_ONLY + " (task_type is compare_shapes for every item)")})],
    "mat_g1_mg_q1_2": [("triangles, squares, and rectangles", {
        "triangles": NI("component shapes of a compose/decompose item appear only in text"),
        "squares": NI("component shapes of a compose/decompose item appear only in text"),
        "rectangles": NI("component shapes of a compose/decompose item appear only in text")})],
    "mat_g1_mg_q2_0": [("the length of an object and the distance between two objects", {
        "measure_length": eq("task_type", "read_measurement"),
        "measure_distance": eq("task_type", "distance_between")})],
    "mat_g1_mg_q2_1": [("lengths and distances", {
        "lengths": eq("task_type", "compare"), "distances": eq("task_type", "compare_distance")})],
    "mat_g1_mg_q2_2": [("lengths and distances", {
        "lengths": eq("word_measure", "length"), "distances": eq("word_measure", "distance")})],
    "mat_g1_mg_q4_0": [
        ("half turn or in quarter turn", {
            "half_turn": NI("turn size appears only in question text (concept=rotation for all)"),
            "quarter_turn": NI("turn size appears only in question text (concept=rotation for all)")}),
        ("clockwise or in counter-clockwise direction", {
            "clockwise": NI("rotation direction appears only in question text"),
            "counter_clockwise": NI("rotation direction appears only in question text")})],
    "mat_g1_mg_q4_1": [("hour, half hour, and quarter hour", {
        "hour": eq("precision", "hour"), "half_hour": eq("precision", "half_hour"),
        "quarter_hour": eq("precision", "quarter_hour")})],
    "mat_g1_mg_q4_2": [("days of the week and months of the year", {
        "days_of_the_week": eq("unit", "days"), "months_of_the_year": eq("unit", "months")})],
    "mat_g1_mg_q4_4": [("hour, half hour, quarter hour, days in a week, and months in a year", {
        "hour": both({"path": "task_type", "equals": "clock_reading"}, {"path": "minute", "equals": 0}),
        "half_hour": both({"path": "task_type", "equals": "clock_reading"}, {"path": "minute", "equals": 30}),
        "quarter_hour": both({"path": "task_type", "equals": "clock_reading"},
                             {"path": "minute", "one_of": [15, 45]}),
        "days_in_a_week": eq("task_type", "read_day"),
        "months_in_a_year": eq("task_type", "problem_months")})],
    "mat_g1_na_q1_0": [
        ("counting up or down", {
            "count_forward_from_a_given_number": eq("direction", "forward"),
            "count_backward_from_a_given_number": eq("direction", "backward")}),
        ("1 more or 1 less", {
            "identify_one_more_than_a_number": eq("direction", "forward"),
            "identify_one_less_than_a_number": eq("direction", "backward")})],
    "mat_g1_na_q1_2": [("number line, block or bar models, and numerals", {
        "number_line": eq("task_type", "number_line"),
        "block_or_bar_models": eq("visual_type", "PlaceValueBlocks"),
        "numerals": NI("no task represents a number as a numeral alone; numerals are the answer "
                       "form of every item, so no structured value separates this sibling")})],
    "mat_g1_na_q1_4": [("from smallest to largest, and vice versa", {
        "smallest_to_largest": eq("direction", "ascending"), "vice_versa": eq("direction", "descending")})],
    "mat_g1_na_q1_5": [("1st, 2nd, 3rd, up to 10th", {
        "1st": eq("symbol", "1st"), "2nd": eq("symbol", "2nd"), "3rd": eq("symbol", "3rd"),
        "up_to_10th": one_of("symbol", ["4th", "5th", "6th", "7th", "8th", "9th", "10th"])})],
    "mat_g1_na_q1_6": [("5 is 5 and 0; 4 and 1; 3 and 2; 2 and 3; 1 and 4; 0 and 5", {
        "5_is_5_and_0": eq("pair", "5 and 0"), "4_and_1": eq("pair", "4 and 1"),
        "3_and_2": eq("pair", "3 and 2"), "2_and_3": eq("pair", "2 and 3"),
        "1_and_4": eq("pair", "1 and 4"), "0_and_5": eq("pair", "0 and 5")})],
    "mat_g1_na_q1_7": [("'counting up,' and 'putting together'", {
        "counting_up": eq("task_type", "counting_up"),
        "putting_together": eq("task_type", "putting_together")})],
    "mat_g1_na_q1_8": [("the sum of zero and any number is equal to the number, and changing the order "
                        "of the addends does not change the sum", {
        "identity_property": eq("task_type", "zero_identity"),
        "commutative_property": eq("task_type", "commutative")})],
    "mat_g1_na_q2_0": [("from smallest to largest, and vice versa", {
        "smallest_to_largest": eq("direction", "ascending"), "vice_versa": eq("direction", "descending")})],
    "mat_g1_na_q2_1": [("2s, 5s and 10s", {
        "step_2s": eq("skip_by", 2), "step_5s": eq("skip_by", 5), "step_10s": eq("skip_by", 10)})],
    "mat_g1_na_q2_2": [("the place value of a digit in a 2-digit number, the value of a digit, and the "
                        "digit of a number, given its place value", {
        "determine_place_value": eq("task_type", "identify_place"),
        "determine_value": eq("task_type", "identify_value"),
        "determine_digit": eq("task_type", "identify_digit")})],
    "mat_g1_na_q2_5": [("2-digit and 1-digit numbers, and 2-digit and 2-digit numbers", {
        "operands_2_1_digit": {"observe": [{"any_of": [[{"path": "a", "lt": 10}], [{"path": "b", "lt": 10}]]}]},
        "operands_2_2_digit": both({"path": "a", "gte": 10}, {"path": "b", "gte": 10})})],
    "mat_g1_na_q3_4": [("2-digit minus 1-digit numbers, and 2-digit minus 2-digit numbers", {
        "sub_2d_1d": both({"path": "b", "lt": 10}), "sub_2d_2d": both({"path": "b", "gte": 10})})],
    "mat_g1_na_q4_0": [("1/2 and 1/4", {
        "half": eq("denominator", 2), "quarter": eq("denominator", 4)})],
    "mat_g1_na_q4_2": [("halves and quarters", {
        "halves": eq("denominator", 2), "quarters": eq("denominator", 4)})],
    "mat_g1_na_q4_3": [("coins (excluding centavo coins) and bills", {
        "coins": NI(COIN_BILL), "bills": NI(COIN_BILL)})],
    "mat_g1_na_q4_4": [("a number of bills and/or a number of coins", {
        "number_of_bills": NI(COIN_BILL), "number_of_coins": NI(COIN_BILL)})],
    "mat_g1_na_q4_5": [("peso coins (excluding centavo coins) and bills", {
        "peso_coins": NI(COIN_BILL), "bills": NI(COIN_BILL)})],
    "mat_g1_na_q4_6": [("addition of money where the sum is up to ₱100, or subtraction of money", {
        "addition_of_money": eq("operation", "add_amounts"),
        "subtraction_of_money": eq("operation", "find_change")})],
    "mat_g2_dp_q3_0": [("raw data, or data in tabular form", {
        "raw_data": eq("task_type", "present_data"), "tabular_form": eq("task_type", "organize_table")})],
    "mat_g2_dp_q3_1": [("in tabular form and in a pictograph", {
        "tabular_form": eq("visual_type", "FillInTable"), "pictograph": eq("visual_type", "BarChart")})],
    "mat_g2_mg_q1_0": [("circles, half circles and quarter circles", {
        "circles": eq("answer", "circle"), "half_circles": eq("answer", "half-circle"),
        "quarter_circles": eq("answer", "quarter-circle")})],
    "mat_g2_mg_q1_1": [
        ("squares, rectangles, triangles, circles, half circles, and quarter circles", {
            m: NI("component shapes of a composite figure appear only in question text")
            for m in ["squares", "rectangles", "triangles", "circles", "half_circles", "quarter_circles"]}),
        ("cut-outs and square grids", {
            "cut_outs": NI("cut-out vs square-grid setting appears only in question text"),
            "square_grids": NI("cut-out vs square-grid setting appears only in question text")})],
    "mat_g2_mg_q1_2": [("basic shapes and figures", {
        "basic_shapes": NI(TEXT_ONLY), "basic_figures": NI(TEXT_ONLY)})],
    "mat_g2_mg_q2_0": [("lengths of objects, in meters (m) or centimeters (cm), and distance", {
        "lengths": one_of("task_type", ["compare", "read_measurement"]),
        "distance": eq("task_type", "compare_distance")})],
    "mat_g2_mg_q2_1": [("the length of an object and the distance between two locations", {
        "length": NI("task_type is choose_unit for every item; object vs two-location appears only in text"),
        "distance": NI("task_type is choose_unit for every item; object vs two-location appears only in text")})],
    "mat_g2_mg_q2_2": [("length using meters or centimeters, and distance", {
        "length": NI("task_type is estimate for every item; length vs distance appears only in text"),
        "distance": NI("task_type is estimate for every item; length vs distance appears only in text")})],
    "mat_g2_mg_q2_3": [("length and distance", {
        "length": eq("word_measure", "length"), "distance": eq("word_measure", "distance")})],
    "mat_g2_mg_q4_0": [("number of days and/or weeks", {
        "number_of_days": eq("task_type", "elapsed_days"), "number_of_weeks": eq("task_type", "elapsed_weeks")})],
    "mat_g2_mg_q4_1": [("hours and minutes", {
        "hours": eq("precision", "hour"), "minutes": one_of("precision", ["five_minutes", "one_minute"])})],
    "mat_g2_mg_q4_2": [("minutes in an hour, hours in a day, days in a week", {
        "minutes_in_an_hour": eq("elapsed_unit", "minutes"), "hours_in_a_day": eq("elapsed_unit", "hours"),
        "days_in_a_week": eq("elapsed_unit", "days")})],
    "mat_g2_mg_q4_3": [
        ("straight and curved lines", {
            "straight_lines": NI("concept_type is straight_curved for every item; lines vs surfaces only in text"),
            "curved_lines": NI("concept_type is straight_curved for every item; lines vs surfaces only in text")}),
        ("flat and curved surfaces", {
            "flat_surfaces": NI("concept_type is straight_curved for every item; lines vs surfaces only in text"),
            "curved_surfaces": NI("concept_type is straight_curved for every item; lines vs surfaces only in text")})],
    "mat_g2_mg_q4_5": [("triangles, squares, and rectangles", {
        "triangles": eq("shape", "triangle"), "squares": eq("shape", "square"),
        "rectangles": eq("shape", "rectangle")})],
    "mat_g2_mg_q4_6": [("triangles, squares, and rectangles", {
        "triangles": eq("shape", "triangle"), "squares": eq("shape", "square"),
        "rectangles": eq("shape", "rectangle")})],
    "mat_g2_na_q1_10": [("the sum of zero and any number is equal to the number, changing the order of "
                         "the addends does not change the sum, and changing the grouping of the addends "
                         "does not change the sum", {
        "identity_property": eq("task_type", "zero_identity"),
        "commutative_property": eq("task_type", "commutative"),
        "associative_property": eq("task_type", "associative")})],
    "mat_g2_na_q1_3": [("2s, 5s, 10s, 20s, 50s, and 100s", {
        "twos": eq("skip_by", 2), "fives": eq("skip_by", 5), "tens": eq("skip_by", 10),
        "twenties": eq("skip_by", 20), "fifties": eq("skip_by", 50), "hundreds": eq("skip_by", 100)})],
    "mat_g2_na_q1_4": [("from smallest to largest, and vice versa", {
        "smallest_to_largest": eq("direction", "ascending"),
        "largest_to_smallest": eq("direction", "descending")})],
    "mat_g2_na_q1_6": [("the place value of a digit in a 3-digit number, the value of a digit, and the "
                        "digit of a number, given its place value", {
        "determine_place_value": eq("task_type", "identify_place"),
        "determine_value_of_digit": eq("task_type", "identify_value"),
        "determine_digit_given_place_value": eq("task_type", "identify_digit")})],
    "mat_g2_na_q1_9": [("with or without regrouping", {
        "with_regrouping": NI(REGROUP), "without_regrouping": NI(REGROUP)})],
    "mat_g2_na_q2_0": [
        ("a number of bills, or a number of coins, or a combination of bills and coins", {
            "number_of_bills": NI(COIN_BILL), "number_of_coins": NI(COIN_BILL),
            "combination_of_bills_and_coins": NI(COIN_BILL)}),
        ("centavo coins only, peso coins only, peso bills only, combined peso coins and peso bills", {
            "centavo_coins_only": eq("denomination_unit", "centavo"),
            "peso_coins_only": NI(COIN_BILL), "peso_bills_only": NI(COIN_BILL),
            "combined_peso_coins_and_peso_bills": NI(COIN_BILL)})],
    "mat_g2_na_q2_1": [("peso coins and bills", {"peso_coins": NI(COIN_BILL), "bills": NI(COIN_BILL)})],
    "mat_g2_na_q2_3": [("on the number line and as an inverse of addition", {
        "number_line": eq("task_type", "number_line_subtraction"),
        "inverse_of_addition": eq("task_type", "inverse_of_addition")})],
    "mat_g2_na_q2_4": [("2-digit minus 1-digit numbers, and 2-digit minus 2-digit numbers", {
        "2_digit_minus_1_digit": both({"path": "b", "lt": 10}),
        "2_digit_minus_2_digit": both({"path": "b", "gte": 10})})],
    "mat_g2_na_q2_8": [("numbers, letters and rhythmic properties, visual elements in arts, and repetitions", {
        "numbers": NI("number vs letter terms are distinguishable only by the term text"),
        "letters": NI("number vs letter terms are distinguishable only by the term text"),
        "repetitions": eq("pattern_kind", "repeating")})],
    "mat_g2_na_q3_0": [("'5 groups of 3' and '5 threes'", {
        "5_groups_of_3": eq("group_form", "groups_of"), "5_threes": eq("group_form", "plural_name")})],
    "mat_g2_na_q3_1": [("groups of equal quantities, arrays, counting by multiples, and equal jumps on a "
                        "number line", {
        "groups_of_equal_quantities": eq("visual_type", "EmojiPictorial"),
        "array": eq("visual_type", "GridArea"),
        "counting_by_multiples": eq("task_type", "skip_counting"),
        "equal_jumps_on_a_number_line": eq("task_type", "number_line_jumps")})],
    "mat_g2_na_q3_5": [("equal sharing or formation of equal groups of objects, and repeated subtraction", {
        "equal_sharing": NI("sharing vs grouping both emit task_type=find_quotient"),
        "formation_of_equal_groups": NI("sharing vs grouping both emit task_type=find_quotient"),
        "repeated_subtraction": eq("task_type", "repeated_subtraction")})],
    "mat_g2_na_q3_7": [("multiplication or division", {
        "multiplication": eq("operation", "multiplication"), "division": eq("operation", "division")})],
    "mat_g2_na_q4_2": [("from smallest to largest, and vice versa", {
        "smallest_to_largest": eq("direction", "ascending"), "vice_versa": eq("direction", "descending")})],
    "mat_g2_na_q4_3": [("groups of objects, fraction charts, fraction tiles, and the number line", {
        "groups_of_objects": eq("model_type", "set_model"),
        "fraction_charts": UNSERVED("model_type emits only number_line, area_model and set_model"),
        "fraction_tiles": UNSERVED("model_type emits only number_line, area_model and set_model"),
        "number_line": eq("model_type", "number_line")})],
    "mat_g2_na_q4_5": [("from smallest to largest, and vice versa", {
        "smallest_to_largest": eq("direction", "ascending"), "vice_versa": eq("direction", "descending")})],
    "mat_g3_dp_q3_0": [("rolling a die or tossing a coin", {
        "rolling_die": eq("experiment_type", "die_roll"), "tossing_coin": eq("experiment_type", "coin_toss")})],
    "mat_g3_dp_q3_1": [
        ("tables and single bar graphs", {
            "data_table": eq("orientation", "table"),
            "single_bar_graph": one_of("orientation", ["horizontal", "vertical"])}),
        ("horizontal and vertical", {
            "horizontal_bar_graph": eq("orientation", "horizontal"),
            "vertical_bar_graph": eq("orientation", "vertical")})],
    "mat_g3_dp_q3_2": [
        ("tables and single bar graphs", {
            "tables": eq("orientation", "table"),
            "single_bar_graphs": one_of("orientation", ["horizontal", "vertical"])}),
        ("horizontal and vertical", {
            "horizontal": eq("orientation", "horizontal"), "vertical": eq("orientation", "vertical")})],
    "mat_g3_dp_q3_3": [("horizontal and vertical", {
        "horizontal": eq("orientation", "horizontal"), "vertical": eq("orientation", "vertical")})],
    "mat_g3_dp_q3_4": [("equally likely, less/least likely, more/most likely, certain, and impossible", {
        "equally_likely": eq("probability_term", "equally likely"),
        "less_least_likely": one_of("probability_term", ["less likely", "least likely"]),
        "more_most_likely": one_of("probability_term", ["more likely", "most likely"]),
        "certain": eq("probability_term", "certain"),
        "impossible": eq("probability_term", "impossible")})],
    "mat_g3_mg_q1_0": [("a square or rectangle", {
        "square_figure": eq("shape", "square"), "rectangle_figure": eq("shape", "rectangle")})],
    "mat_g3_mg_q1_1": [("a square and a rectangle", {
        "square_figure": eq("shape", "square"), "rectangle_figure": eq("shape", "rectangle")})],
    "mat_g3_mg_q1_2": [
        ("squares and rectangles", {
            "square_figure": eq("shape", "square"), "rectangle_figure": eq("shape", "rectangle")}),
        ("sq. cm and sq. m", {
            "square_centimeter": eq("unit", "sq cm"), "square_meter": eq("unit", "sq m")})],
    "mat_g3_mg_q1_3": [("squares and rectangles", {
        "square_figure": eq("shape", "square"), "rectangle_figure": eq("shape", "rectangle")})],
    "mat_g3_mg_q1_4": [("a point, line, line segment, and ray", {
        "point": eq("kind", "point"), "line": eq("kind", "line"),
        "line_segment": eq("kind", "segment"), "ray": eq("kind", "ray")})],
    "mat_g3_mg_q1_5": [("parallel, intersecting, and perpendicular lines", {
        "parallel_lines": eq("kind", "parallel"), "intersecting_lines": eq("kind", "intersecting"),
        "perpendicular_lines": eq("kind", "perpendicular")})],
    "mat_g3_na_q1_1": [("in numerals and in words", {
        "numerals": eq("task_type", "word_to_numeral"), "words": eq("task_type", "numeral_to_word")})],
    "mat_g3_na_q1_3": [("the place value of a digit in a 4-digit number, the value of a digit, and the "
                        "digit of number, given its place value", {
        "place_value_of_digit": eq("task_type", "identify_place"),
        "value_of_digit": eq("task_type", "identify_value"),
        "digit_of_number": eq("task_type", "identify_digit")})],
    "mat_g3_na_q1_4": [("nearest ten, hundred, or thousand", {
        "nearest_ten": eq("round_to", 10), "hundred": eq("round_to", 100), "thousand": eq("round_to", 1000)})],
    "mat_g3_na_q1_6": [("from smallest to largest, and vice versa", {
        "smallest_to_largest": eq("direction", "ascending"), "vice_versa": eq("direction", "descending")})],
    "mat_g3_na_q2_0": [("in words and using: Philippine currency symbols (₱ and PhP) up to ₱10 000, and "
                        "the centavo sign", {
        m: NI("notation form (words, the peso sign, PhP, the centavo sign) appears only in text")
        for m in ["words", "peso_sign", "php", "centavo_sign"]})],
    "mat_g3_na_q2_1": [("with and without regrouping", {
        "with_regrouping": NI(REGROUP), "without_regrouping": NI(REGROUP)})],
    "mat_g3_na_q3_1": [("one multiplied by any number is equal to the number; zero multiplied by any number "
                        "is zero; changing the order of the numbers being multiplied does not change the "
                        "product; changing the grouping of the numbers being multiplied does not change the "
                        "product; and multiplying the sum of two addends by a number is the same as the sum "
                        "of the products of a number by each addend", {
        "one_multiplied_by_any_number": {"observe": [
            {"path": "task_type", "equals": "zero_identity"},
            {"any_of": [[{"path": "a", "equals": 1}], [{"path": "b", "equals": 1}]]}]},
        "zero_multiplied_by_any_number": {"observe": [
            {"path": "task_type", "equals": "zero_identity"},
            {"any_of": [[{"path": "a", "equals": 0}], [{"path": "b", "equals": 0}]]}]},
        "changing_the_order": eq("task_type", "commutative"),
        "changing_the_grouping": eq("task_type", "associative"),
        "multiplying_the_sum_of_two_addends": eq("task_type", "distributive")})],
    "mat_g3_na_q3_2": [("2- to 3-digit numbers by a 1-digit number, and 2- to 4-digit numbers by a number "
                        "whose leading digit is the only non-zero digit", {
        "2_to_3_digit_by_1_digit": both({"path": "b", "lt": 10}),
        "2_to_4_digit_by_leading_non_zero": both({"path": "b", "gte": 10})})],
    "mat_g3_na_q3_5": [("repeating and increasing components or repeating and decreasing components", {
        "repeating_and_increasing": both({"path": "common_difference", "gte": 1}),
        "repeating_and_decreasing": both({"path": "common_difference", "lt": 0})})],
    "mat_g3_na_q3_6": [("repeating and increasing components or repeating and decreasing components", {
        "repeating_and_increasing": both({"path": "common_difference", "gte": 1}),
        "repeating_and_decreasing": both({"path": "common_difference", "lt": 0})})],
    "mat_g3_na_q4_0": [("through equal jumps on the number line and as inverse of multiplication", {
        "equal_jumps": eq("task_type", "number_line_jumps"),
        "inverse_of_multiplication": eq("task_type", "inverse_of_multiplication")})],
    "mat_g3_na_q4_2": [("multiplication or division", {
        "multiplication": eq("operation", "multiplication"), "division": eq("operation", "division")})],
    "mat_g3_na_q4_3": [("2- to 3-digit numbers by 1-digit number without remainder, 2-digit numbers by "
                        "1-digit number with remainder, and 2- to 4-digit numbers by 10,100, and 1000", {
        "1_digit_number_without_remainder": both({"path": "b", "lt": 10}, {"path": "remainder", "equals": 0}),
        "1_digit_number_with_remainder": both({"path": "remainder", "gte": 1}),
        "10_100_1000": one_of("b", [10, 100, 1000])})],
    "mat_g3_na_q4_6": [("equal to one and greater than one", {
        "equal_to_one": NI("numerator==denominator is a comparison of two fields; DNA should emit a class"),
        "greater_than_one": NI("numerator>denominator is a comparison of two fields; DNA should emit a class")})],
    "mat_g3_na_q4_7": [("Add and subtract", {
        "add": eq("operation", "add"), "subtract": eq("operation", "subtract")})],
}

_OPS = {"equals", "one_of", "lt", "gte"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _paths(value, key):
    out = []
    if isinstance(value, dict):
        for k, v in value.items():
            if str(k) == key:
                out.append(v)
            out.extend(_paths(v, key))
    elif isinstance(value, list):
        for v in value:
            out.extend(_paths(v, key))
    return out


def _cond_ok(sample, cond):
    if "any_of" in cond:
        return any(all(_cond_ok(sample, c) for c in branch) for branch in cond["any_of"])
    path = cond["path"]
    actuals = [sample.get("visual_type")] if path == "visual_type" else _paths(
        sample.get("_provider_variant_evidence") or {}, path)
    for a in actuals:
        if "equals" in cond and str(a) == str(cond["equals"]):
            return True
        if "one_of" in cond and str(a) in {str(x) for x in cond["one_of"]}:
            return True
        if "lt" in cond and _num(a) is not None and _num(a) < cond["lt"]:
            return True
        if "gte" in cond and _num(a) is not None and _num(a) >= cond["gte"]:
            return True
    return False


def _validate_selector(sel, where, errors):
    for cond in sel.get("observe") or []:
        if "any_of" in cond:
            for branch in cond["any_of"]:
                for c in branch:
                    _validate_selector({"observe": [c]}, where, errors)
            continue
        ops = set(cond) - {"path"}
        if not cond.get("path") or len(ops) != 1 or not ops <= _OPS:
            errors.append(f"{where}: malformed condition {cond!r}")


def main(out_path, check_renders):
    errors, nodes = [], {}
    pending = dict(E)
    for node_id in sorted(get_all_node_ids()):
        meta = get_node_info(node_id) or {}
        requires = [str(r["id"]) for r in (meta.get("requires") or [])]
        if not requires:
            continue
        competency = meta.get("competency", "")
        enums, seen = [], []
        for wording, members in pending.pop(node_id, []):
            if wording not in competency:
                errors.append(f"{node_id}: wording not verbatim: {wording!r}")
            sels = []
            for m, disp in members.items():
                if m not in requires:
                    errors.append(f"{node_id}: member {m!r} is not a required clause")
                kinds = set(disp) & {"observe", "needs_instrumentation", "unserved"}
                if len(kinds) != 1:
                    errors.append(f"{node_id}/{m}: needs exactly one disposition, got {sorted(disp)}")
                if "observe" in disp:
                    _validate_selector(disp, f"{node_id}/{m}", errors)
                    sels.append(json.dumps(disp, sort_keys=True))
            if len(sels) != len(set(sels)):
                errors.append(f"{node_id}: siblings share a selector in {wording!r}")
            seen += list(members)
            enums.append({"wording": wording, "members": members})
        if len(seen) != len(set(seen)):
            errors.append(f"{node_id}: a member is in more than one enumeration")
        nodes[node_id] = {
            "competency_sha256": hashlib.sha256(competency.encode("utf-8")).hexdigest(),
            "enumerations": enums,
            "not_enumerated": [r for r in requires if r not in seen],
        }
    if pending:
        errors.append(f"classified nodes that declare no requires: {sorted(pending)}")
    if errors:
        print("\n".join(errors))
        return 1
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"schema_version": 0, "status": "DRAFT -- not read by any harness code",
                   "ruling": "owner rulings 19 and 22, docs/phase2_hardening_completion_plan.md",
                   "nodes": nodes}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    members = [(n, m, d) for n, v in nodes.items() for e in v["enumerations"] for m, d in e["members"].items()]
    count = lambda k: sum(1 for _, _, d in members if k in d)
    print(f"nodes={len(nodes)} enumerations={sum(len(v['enumerations']) for v in nodes.values())} "
          f"members={len(members)} selector={count('observe')} needs_instrumentation="
          f"{count('needs_instrumentation')} unserved={count('unserved')} "
          f"not_enumerated={sum(len(v['not_enumerated']) for v in nodes.values())}")
    if check_renders:
        from backend.app.practice_gen.validation.judgment_packets import _render_sample
        weak = 0
        by_node = {}
        for n, m, d in members:
            if "observe" in d:
                by_node.setdefault(n, []).append((m, d))
        for n, items in sorted(by_node.items()):
            samples = [s for s in (_render_sample(n, seed, include_private_variant_evidence=True)
                                   for seed in range(1000, 1040)) if s is not None]
            for m, d in items:
                hits = sum(1 for s in samples if all(_cond_ok(s, c) for c in d["observe"]))
                if hits < 2:
                    weak += 1
                    print(f"WEAK {n}/{m}: {hits}/{len(samples)} renders match {d['observe']}")
        print(f"check_renders: {weak} selector(s) observed fewer than 2 times in seeds 1000-1039")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--check-renders" in sys.argv[2:]))
