"""
Clause enumeration — owner ruling 22(b)'s classification and ruling 19's sibling strata.

Why this exists
---------------
Ruling 19 judges an enumerated sibling clause (one item of a list in the competency:
skip intervals, graph orientations, likelihood words, named figures) as PROVIDED when the
generator serves it by design and a packet stratified so that every sibling is sampled
shows it at least twice. Before this module the Attester packet stratified only on
explicit `CAPABILITY_PROVIDERS.variants`, so a sibling the generator serves through a
plain field value (`skip_by=50`, `orientation=table`) landed in the packet by luck, and
the W2 queue read "observed in 1-4 of 10" as NOT_PROVIDED for 68 findings (review F1).

Ruling 22 approves packet-only selectors on two conditions, enforced here:

  (a) a selector observes STRUCTURED generator values only -- never a substring of
      learner-facing text. The ops are `equals`, `one_of`, `lt`, `gte` and `any_of` (an OR
      of condition lists). No substring op exists, and an unknown op raises.
  (b) every required clause is classified: once, as an enumeration member, or as not
      enumerated. A clause with neither fails by name.

What it holds
-------------
`TABLE` is the human reading, per node: each enumeration's verbatim competency wording
and, per member, exactly one disposition --

    selector              {"observe": [conditions]}. `path` names a key matched at any
                          depth of the sample's given_values; the special path
                          `visual_type` reads the rendered sample's visual_type.
    needs_instrumentation the sibling is visible only in learner-facing text; the DNA
                          must emit a structured field first. The packet builder REFUSES
                          such a node, naming the member.
    unserved              the generator's own vocabulary has no value for it. No stratum;
                          the Attester judges it on the base samples.

An enumeration is two or more required clauses the competency lists as alternative
CONTENT the items range over -- objects, figures, cases, units, terms, properties,
directions, arithmetic operations, named specific media. NOT enumerations: coordinated
task verbs (read/write, compose/decompose; ruling 9), abstract medium words such as
"concrete" or "pictorial models" (rulings 12 and 15), parts present together in every
item ("Compare 1/2 and 1/4"), and synonyms ("slide (or translation)").

Selectors are keyed per (node, member), never per capability id: 140 of the 472 ids are
shared by nodes whose DNAs emit different fields (`half_hour` is `precision` on
mat_g1_mg_q4_1 but `minute` on mat_g1_mg_q4_4), so a capability-wide selector would be
wrong on one of them.

The tracked file `validation_reports/phase2_hardening/clause_enumeration.json` is what
`tests/attester_packets.py` reads. It is generated from TABLE by this module, never by
hand, and `validate` fails if it is not byte-for-byte the builder's output.

NAMED LIMITS
------------
1. The classification is a human curriculum reading (drafted 2026-10-07, reviewed the
   same day). `validate` proves it is complete and well-formed, not that it is right.
2. A selector proves a stratum CAN render, not how often pupils see it (ruling 19 calls
   this provision by design).
3. `answer` equality (e.g. answer == "triangle") and `visual_type` are treated as
   structured values. They are generator outputs, not substrings, but they are the
   closest a selector comes to learner-facing content.
4. Only siblings WITHIN one enumeration are barred from sharing a selector. On
   mat_g1_na_q1_0 "1 more or 1 less" reuses "counting up or down"'s `direction`
   selectors: the DNA's only "1 more" item is "what comes next" on a forward sequence.
5. needs_instrumentation members are refused, not judged, until their DNA emits a field.

Usage:
    PYTHONPATH=. .venv/bin/python -m tests.clause_enumeration --write
    PYTHONPATH=. .venv/bin/python -m tests.clause_enumeration --check            # the gate
    PYTHONPATH=. .venv/bin/python -m tests.clause_enumeration --check-renders    # slow
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List

from backend.app.practice_gen.registry import get_all_node_ids, get_node_info

PATH = Path(__file__).resolve().parents[1] / "validation_reports" / "phase2_hardening" / "clause_enumeration.json"
LABEL = "clause_enumeration_22"
SCHEMA_VERSION = 1
OPS = ("equals", "one_of", "lt", "gte")
DISPOSITIONS = ("observe", "needs_instrumentation", "unserved")


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

TABLE = {
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



# --------------------------------------------------------------------------- matching

def _num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _values_at(value: Any, key: str) -> List[Any]:
    out: List[Any] = []
    if isinstance(value, dict):
        for k, v in value.items():
            if str(k) == key:
                out.append(v)
            out.extend(_values_at(v, key))
    elif isinstance(value, list):
        for v in value:
            out.extend(_values_at(v, key))
    return out


def condition_matches(evidence: Dict[str, Any], visual_type: Any, cond: Dict[str, Any]) -> bool:
    """One condition against one sample's structured values. Unknown ops raise."""
    if "any_of" in cond:
        if set(cond) != {"any_of"}:
            raise ValueError(f"{LABEL}: any_of condition carries other keys: {cond!r}")
        return any(all(condition_matches(evidence, visual_type, c) for c in branch)
                   for branch in cond["any_of"])
    ops = set(cond) - {"path"}
    if not cond.get("path") or len(ops) != 1 or not ops <= set(OPS):
        raise ValueError(f"{LABEL}: condition {cond!r} is not one path plus one of {OPS}")
    path = cond["path"]
    actuals = [visual_type] if path == "visual_type" else _values_at(evidence, path)
    for actual in actuals:
        if "equals" in cond and str(actual) == str(cond["equals"]):
            return True
        if "one_of" in cond and str(actual) in {str(x) for x in cond["one_of"]}:
            return True
        if "lt" in cond and _num(actual) is not None and _num(actual) < cond["lt"]:
            return True
        if "gte" in cond and _num(actual) is not None and _num(actual) >= cond["gte"]:
            return True
    return False


def selector_matches(sample: Dict[str, Any], selector: Dict[str, Any]) -> bool:
    """All of a member's conditions hold on one rendered sample (private evidence attached)."""
    evidence = sample.get("_provider_variant_evidence") or {}
    return all(condition_matches(evidence, sample.get("visual_type"), cond)
               for cond in selector["observe"])


# --------------------------------------------------------------------------- building

def _requires(meta: Dict[str, Any]) -> List[str]:
    return [str(r["id"]) for r in (meta.get("requires") or [])]


def build_document(table: Dict[str, Any] | None = None,
                   node_info: Callable[[str], Dict[str, Any]] = get_node_info,
                   node_ids: List[str] | None = None) -> Dict[str, Any]:
    """The tracked file's content, from TABLE and the live registry. Never hand-edited."""
    table = TABLE if table is None else table
    nodes: Dict[str, Any] = {}
    for node_id in sorted(get_all_node_ids() if node_ids is None else node_ids):
        meta = node_info(node_id) or {}
        requires = _requires(meta)
        if not requires and node_id not in table:
            continue
        competency = meta.get("competency", "")
        enums = [{"wording": wording, "members": members}
                 for wording, members in table.get(node_id, [])]
        seen = {m for e in enums for m in e["members"]}
        nodes[node_id] = {
            "competency_sha256": hashlib.sha256(competency.encode("utf-8")).hexdigest(),
            "enumerations": enums,
            "not_enumerated": [r for r in requires if r not in seen],
        }
    for node_id in sorted(set(table) - set(nodes)):
        nodes[node_id] = {"competency_sha256": "", "enumerations": [
            {"wording": w, "members": m} for w, m in table[node_id]], "not_enumerated": []}
    return {"schema_version": SCHEMA_VERSION,
            "ruling": "owner rulings 19 and 22, docs/phase2_hardening_completion_plan.md",
            "generated_by": "python -m tests.clause_enumeration --write",
            "nodes": nodes}


def serialize(doc: Dict[str, Any]) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def load(path: Path = PATH) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- the gate

def _selector_errors(selector: Any, where: str) -> List[str]:
    errors: List[str] = []
    if not isinstance(selector, list) or not selector:
        return [f"{LABEL}: {where} selector has no conditions"]
    for cond in selector:
        if not isinstance(cond, dict):
            errors.append(f"{LABEL}: {where} condition {cond!r} is not an object")
        elif "any_of" in cond:
            if set(cond) != {"any_of"} or not cond["any_of"]:
                errors.append(f"{LABEL}: {where} malformed any_of {cond!r}")
                continue
            for branch in cond["any_of"]:
                errors.extend(_selector_errors(branch, where))
        else:
            ops = set(cond) - {"path"}
            if not cond.get("path") or len(ops) != 1 or not ops <= set(OPS):
                errors.append(f"{LABEL}: {where} condition op {sorted(ops)} is not one of "
                              f"{OPS + ('any_of',)} (ruling 22a: no substring op): {cond!r}")
    return errors


def validate(doc: Dict[str, Any],
             node_info: Callable[[str], Dict[str, Any]] = get_node_info,
             node_ids: List[str] | None = None) -> List[str]:
    """Every way the classification can be incomplete or malformed, each named by node."""
    errors: List[str] = []
    if doc.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{LABEL}: schema_version {doc.get('schema_version')!r} != {SCHEMA_VERSION}")
    nodes = doc.get("nodes") or {}
    for node_id in sorted(get_all_node_ids() if node_ids is None else node_ids):
        meta = node_info(node_id) or {}
        requires = _requires(meta)
        entry = nodes.get(node_id)
        if entry is None:
            if requires:
                errors.append(f"{LABEL}: {node_id} declares requires {requires} but is missing "
                              f"from the classification")
            continue
        if not requires:
            errors.append(f"{LABEL}: {node_id} is classified but declares no requires")
            continue
        competency = meta.get("competency", "")
        want = hashlib.sha256(competency.encode("utf-8")).hexdigest()
        if entry.get("competency_sha256") != want:
            errors.append(f"{LABEL}: {node_id} competency_sha256 mismatch: the competency "
                          f"changed since it was classified; re-read it and regenerate")
        counts = {r: 0 for r in requires}
        foreign: List[str] = []
        for enum in entry.get("enumerations") or []:
            wording = enum.get("wording") or ""
            if not wording or wording not in competency:
                errors.append(f"{LABEL}: {node_id} enumeration wording is not verbatim in the "
                              f"competency: {wording!r}")
            members = enum.get("members") or {}
            if len(members) < 2:
                errors.append(f"{LABEL}: {node_id} enumeration {wording!r} has fewer than two members")
            selectors: Dict[str, str] = {}
            for member, disp in members.items():
                where = f"{node_id}/{member}"
                if member in counts:
                    counts[member] += 1
                else:
                    foreign.append(member)
                kinds = [k for k in DISPOSITIONS if k in (disp or {})]
                if len(kinds) != 1 or set(disp) != set(kinds):
                    errors.append(f"{LABEL}: {where} needs exactly one disposition of "
                                  f"{DISPOSITIONS}, got {sorted(disp or {})}")
                    continue
                if kinds[0] == "observe":
                    errors.extend(_selector_errors(disp["observe"], where))
                    canon = json.dumps(disp["observe"], sort_keys=True)
                    if canon in selectors:
                        errors.append(f"{LABEL}: {node_id} siblings {selectors[canon]!r} and "
                                      f"{member!r} share a selector in {wording!r}")
                    selectors.setdefault(canon, member)
                elif not isinstance(disp[kinds[0]], str) or not disp[kinds[0]].strip():
                    errors.append(f"{LABEL}: {where} {kinds[0]} has an empty reason")
        for clause in entry.get("not_enumerated") or []:
            if clause in counts:
                counts[clause] += 1
            else:
                foreign.append(clause)
        for clause in foreign:
            errors.append(f"{LABEL}: {node_id} classifies {clause!r}, which the node does not require")
        for clause, n in counts.items():
            if n != 1:
                errors.append(f"{LABEL}: {node_id} required clause {clause!r} is classified "
                              f"{n} times (must be exactly once)")
    known = set(get_all_node_ids() if node_ids is None else node_ids)
    for node_id in sorted(set(nodes) - known):
        errors.append(f"{LABEL}: {node_id} is classified but is not a registered node")
    return errors


def check(path: Path = PATH) -> List[str]:
    """The gate the unit suite runs: the tracked file is valid AND is the builder's output."""
    if not path.exists():
        return [f"{LABEL}: {path} is missing; run `python -m tests.clause_enumeration --write`"]
    text = path.read_text(encoding="utf-8")
    errors = validate(json.loads(text))
    errors += [e.replace(f"{LABEL}: ", f"{LABEL}: TABLE: ", 1) for e in validate(build_document())]
    if text != serialize(build_document()):
        errors.append(f"{LABEL}: {path.name} is not the builder's output; it was edited by "
                      f"hand or TABLE changed without `--write`")
    return errors


def node_dispositions(node_id: str, doc: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """{member: disposition} for one node, from the tracked file. Raises if unclassified."""
    doc = load() if doc is None else doc
    entry = (doc.get("nodes") or {}).get(node_id)
    if entry is None:
        raise KeyError(f"{LABEL}: {node_id} is not in {PATH.name}")
    return {m: d for e in entry["enumerations"] for m, d in e["members"].items()}


def member_wordings(node_id: str, doc: Dict[str, Any] | None = None) -> Dict[str, str]:
    """{member: the verbatim enumeration wording it belongs to} for one node."""
    doc = load() if doc is None else doc
    entry = (doc.get("nodes") or {}).get(node_id)
    if entry is None:
        raise KeyError(f"{LABEL}: {node_id} is not in {PATH.name}")
    return {m: e["wording"] for e in entry["enumerations"] for m in e["members"]}


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="regenerate the tracked file from TABLE")
    ap.add_argument("--check", action="store_true", help="run the gate on the tracked file")
    ap.add_argument("--check-renders", action="store_true",
                    help="render each selector's packet seeds and report any with < 2 matches")
    args = ap.parse_args(argv)
    if args.write:
        doc = build_document()
        errors = validate(doc)
        if errors:
            print("\n".join(errors))
            return 1
        PATH.write_text(serialize(doc), encoding="utf-8")
        members = [d for v in doc["nodes"].values() for e in v["enumerations"] for d in e["members"].values()]
        print(f"wrote {PATH}: nodes={len(doc['nodes'])} "
              f"enumerations={sum(len(v['enumerations']) for v in doc['nodes'].values())} "
              f"members={len(members)} "
              + " ".join(f"{k}={sum(1 for d in members if k in d)}" for k in DISPOSITIONS)
              + f" not_enumerated={sum(len(v['not_enumerated']) for v in doc['nodes'].values())}")
    if args.check:
        errors = check()
        print("\n".join(errors) if errors else f"{LABEL}: OK ({PATH.name})")
        if errors:
            return 1
    if args.check_renders:
        from tests.attester_packets import _render_selector_samples
        doc = load()
        failed = 0
        for node_id in sorted(doc["nodes"]):
            for member, disp in node_dispositions(node_id, doc).items():
                if "observe" not in disp:
                    continue
                try:
                    seeds, _ = _render_selector_samples(node_id, member, disp)
                except RuntimeError as exc:
                    failed += 1
                    print(f"FAIL {exc}")
        print(f"check_renders: {failed} selector(s) could not render 2 matching samples")
        if failed:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
