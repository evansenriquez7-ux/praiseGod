"""
Practice Generation — Node Registry
======================================

Maps MATATAG node IDs to DNA concept names and provides lookups
used by the pipeline to select generators and formatters.

Responsibilities:
  1. Load knowledge_graph_g1_3.json at import time.
  2. Load data/ph/matatagmath.json at import time.
  3. Define NODE_TO_DNA: static mapping node_id → List[str] (DNA names).
  4. Expose get_node_dnas(), get_node_formatters(), get_node_info(),
     find_node_id(), get_all_node_ids().

Node ID format: mat_g{grade}_{branch}_q{quarter}_{index}
  branch: na (Number & Algebra), mg (Measurement & Geometry),
          dp (Data & Probability)

DNA concept names exactly match the "concept" field of each DNA instance.

Refactored from:
  - matatag_skeletons.py  COMPETENCY_ROUTES (lines 175–274)
  - curriculum_context.py find_competency_in_curriculum
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from .compatibility import COMPATIBILITY, VARIANTS_BY_DNA


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING — once at import time
# ═══════════════════════════════════════════════════════════════════════════════

# practice_gen/ → app/ → backend/ → ccmed/ (project root)
_ROOT: Path = Path(__file__).parent.parent.parent.parent

_KG_PATH: Path = _ROOT / "data" / "knowledge_graph_g1_3.json"
_MATATAG_PATH: Path = _ROOT / "data" / "ph" / "matatagmath.json"

_KG_NODES: Dict[str, Dict] = {}
_MATATAG_DATA: Dict = {}

try:
    with _KG_PATH.open(encoding="utf-8") as _f:
        _KG_NODES = json.load(_f).get("nodes", {})
except (FileNotFoundError, json.JSONDecodeError):
    _KG_NODES = {}

try:
    with _MATATAG_PATH.open(encoding="utf-8") as _f:
        _MATATAG_DATA = json.load(_f).get("Mathematics", {})
except (FileNotFoundError, json.JSONDecodeError):
    _MATATAG_DATA = {}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPETENCY BOUNDS PARSING
# Extract numeric bounds from competency text for difficulty dimensions.
# ═══════════════════════════════════════════════════════════════════════════════

import re
from typing import Tuple

# ── MATATAG grade-appropriate ceiling per DNA concept ────────────────────────
# When a competency text has no explicit numeric bound (e.g. "Illustrate
# addition of 2-digit and 1-digit numbers as counting up on the number
# line"), we fall back to the MATATAG curriculum's per-grade ceiling.
# These values are derived directly from the official K-3 MATATAG scope:
#   G1 addition/subtraction: sums/differences ≤ 20 (Q1-Q2), ≤ 100 (Q3-Q4)
#   G2 addition/subtraction: sums/differences ≤ 1000
#   G3 addition/subtraction: sums/differences ≤ 10000
#   G1-G3 comparing/ordering: same number ceiling as their grade range
_GRADE_DEFAULT_BOUNDS: Dict[str, Dict[int, Dict[str, int]]] = {
    "addition": {
        1: {"max_sum": 20},
        2: {"max_sum": 1000},
        3: {"max_sum": 10000},
    },
    "comparing_ordering": {
        1: {"max_value": 100},
        2: {"max_value": 1000},
        3: {"max_value": 10000},
    },
    "counting": {
        1: {"range_max": 100},
        2: {"range_max": 1000},
        3: {"range_max": 10000},
    },
    "number_reading": {
        1: {"range_max": 100},
        2: {"range_max": 10000},
        3: {"range_max": 10000},
    },
    "multiplication": {
        2: {"max_product": 100},
        3: {"max_product": 1000},
    },
    "money_peso": {
        1: {"max_total": 20},
        2: {"max_total": 1000},
        3: {"max_total": 10000},
    },
}


def _parse_competency_bounds(
    competency: str,
    dna_name: str,
    grade: int = 1,
) -> Dict[str, Tuple[int, int]]:
    """
    Parse competency text to extract bounds for difficulty dimensions.

    Returns dict mapping dimension names to (min, max) tuples.
    Scalar 0.0 maps to min, scalar 1.0 maps to max.

    Min values are curriculum-appropriate:
    - addition: min=0 (allows 0+0, 0+X, etc. as valid addition problems)
    - multiplication: min=1 (allows 1×1, 1×2, etc. as valid multiplication problems)
    - other: min=1

    When no explicit numeric bound is found in the LC text, a
    grade-appropriate MATATAG curriculum ceiling is applied as a
    fallback (see _GRADE_DEFAULT_BOUNDS). This guarantees that scalar
    1.0 ALWAYS maps to a sensible maximum — never to the raw float 1.0
    which would crash the DNA.

    Examples:
        "sums up to 20" → {"max_sum": (0, 20)}
        "sums up to 100 without regrouping" → {"max_sum": (0, 100)}
        "products up to 100" → {"max_product": (1, 100)}
    """
    bounds = {}
    # Strip spaces between digits (e.g. "10 000" -> "10000")
    text = re.sub(r'(\d)\s+(\d)', r'\1\2', competency.lower())

    # Addition: "sums up to X", "sums of up to X", "sums to X"
    if dna_name == "addition":
        match = re.search(r'sums?\s+(?:up\s+to|of\s+up\s+to|to)\s+(\d+)', text)
        if match:
            max_val = int(match.group(1))
            bounds["max_sum"] = (0, max_val)
        else:
            # Special case: "X-digit and Y-digit numbers" (e.g., "2-digit and 1-digit")
            # Max sum is (10^X - 1) + (10^Y - 1)
            # e.g., 2-digit and 1-digit → (99 + 9) = 108, round to 100
            digit_match = re.search(r'(\d)-digit\s+and\s+(\d)-digit', text)
            if digit_match:
                larger_digits = int(digit_match.group(1))
                smaller_digits = int(digit_match.group(2))
                max_larger = (10 ** larger_digits) - 1
                max_smaller = (10 ** smaller_digits) - 1
                max_val = max_larger + max_smaller
                # Round to nearest 10 for cleaner bounds
                max_val = ((max_val + 5) // 10) * 10
                bounds["max_sum"] = (3, max_val)

        # "Estimate the sum of addends with up to 4 digits" (mat_g3_na_q2_2)
        # is a distinct skill from exact addition -- round each addend to
        # its own leading place, then add -- that nothing in this DNA
        # produced before task_type="estimate" was added (see
        # addition.py generate_params). The co-mapped `rounding` DNA
        # rounds ONE number, not a sum of two, so it cannot express this
        # competency regardless of which node maps to it.
        if "estimate" in text:
            bounds["task_type"] = "estimate"
    
    # Subtraction: operand bound is enforced by the DNA's per-grade
    # _PARAM_BOUNDS[grade] (g1: a<100, g2: a<1000, g3: a<10000). All
    # MATATAG K-3 subtraction LCs use operand-bound language
    # ("both numbers are less than N"), not result-bound language
    # ("differences up to N"). The `max_difference` axis was removed
    # from the catalog on 2026-07-01 — see axes_catalog.py header.
    # However, we still parse and store max_minuend for UI purposes
    # (to show a discrete "max_minuend" axis when the LC has an explicit bound).
    elif dna_name == "subtraction":
        # "up to N digits" states an operand *width*, not a magnitude. The
        # magnitude regex below captured the digit count itself, so
        # mat_g3_na_q2_6 ("... 3 to 4 numbers of up to 2 digits") bound
        # max_minuend=(1, 2) and served "2 - 2 = 0" at scalar 1.0 -- and both
        # §1A and §1A-reach passed, because they assert against the *parsed*
        # ceiling, so a mis-parsed bound immunises the node from the only
        # checks that could expose it. Same digit-width idiom as the generic
        # number extraction further down (see "Check for digit limits first").
        digit_match = re.search(r'(?:up\s+to|to)\s+(\d+)\s*-?\s*digits?', text)
        if digit_match:
            bounds["max_minuend"] = (1, (10 ** int(digit_match.group(1))) - 1)
        else:
            # Parse explicit operand bounds. A capture below 10 is a digit
            # count, an operand count or a step count -- never a minuend
            # ceiling in MATATAG K-3 phrasing -- so it is rejected rather
            # than believed, matching the `val >= 10` floor the generic
            # extraction below applies for exactly this reason. With no
            # parse the DNA's own per-grade _PARAM_BOUNDS governs, which is
            # what the comment above describes.
            match = re.search(r'(?:less than|up to)\s+(\d+)', text)
            if match and int(match.group(1)) >= 10:
                bounds["max_minuend"] = (1, int(match.group(1)))

        # "Estimate the difference of two numbers ..." (mat_g3_na_q2_5) names
        # a distinct skill from exact subtraction -- round both operands,
        # then subtract the rounded values -- that nothing in this DNA
        # produced before task_type="estimate" was added (see subtraction.py
        # generate_params).
        if "estimate" in text:
            bounds["task_type"] = "estimate"

    # Multiplication: "products up to X"
    elif dna_name == "multiplication":
        match = re.search(r'products?\s+(?:up\s+to|of\s+up\s+to|to)\s+(\d+)', text)
        if match:
            max_val = int(match.group(1))
            bounds["max_product"] = (0, max_val)
        
        # Parse table level
        if "6, 7, 8, and 9" in text or "6, 7, 8, 9" in text or "6, 7, 8, or 9" in text:
            bounds["table"] = "6_7_8_9"
        elif "2, 3, 4, 5, and 10" in text or "2, 3, 4, 5, 10" in text:
            bounds["table"] = "2_3_4_5_10"
            
        # Parse number type
        if "2- to 3-digit" in text or "2- to 4-digit" in text:
            bounds["number_type"] = "multi_digit"
        elif "2-digit" in text or "3-digit" in text:
            bounds["number_type"] = "multi_digit"

        # Parse missing structure
        if "missing number" in text or "missing term" in text:
            bounds["structure"] = "factor_unknown"

        # "Illustrate and write multiplication as repeated addition ... using
        # groups of equal quantities" (mat_g2_na_q3_1): the intro-to-
        # multiplication node, whose whole point is the equal-groups model,
        # not a bare fact. Bind task_type so generate_params keeps the
        # repeat-count small enough to write out (see multiplication.py) and
        # the symbolic question renders as an explicit repeated sum instead
        # of "What is 4 x 2?".
        if "repeated addition" in text:
            bounds["task_type"] = "repeated_addition"

        # "Estimate the product of 2- to 3-digit numbers by 1- to 2-digit
        # numbers by estimating the factors using multiples of 10"
        # (mat_g3_na_q3_3) -- round both factors to the nearest 10, then
        # multiply, a skill nothing in this DNA produced before
        # task_type="estimate" was added (see multiplication.py
        # generate_params). The co-mapped `rounding` DNA rounds ONE
        # number, not two factors of a product, so it cannot express this
        # competency regardless of which node maps to it.
        elif "estimate" in text:
            bounds["task_type"] = "estimate"
            # Ground-truth correction (Ground Rule 5): this competency has
            # no explicit "products up to X" phrase, so without this it
            # falls to the generic G3 grade-default ceiling (0, 1000) --
            # and the orchestrator's own default-scalar interpolation of
            # that range resolves to ~62 for ordinary (unconfigured)
            # rendering. Rounding TWO factors to the nearest 10 has a hard
            # mathematical floor: the smallest non-degenerate product with
            # both rounded factors >=10 is 10*10=100, so a ceiling of 62
            # makes every default render degenerate (one factor forced to
            # round to 0, "estimate" always 0 -- verified: 10/10 sampled
            # seeds before this fix). "2- to 3-digit numbers by 1- to
            # 2-digit numbers" itself implies operands in the tens-to-
            # hundreds range, so 100 is this competency's own natural
            # floor, not an arbitrary widening -- the ceiling (1000, the
            # grade default) is unchanged.
            bounds["max_product"] = (100, 1000)

    # Division: operand bound is enforced by the DNA's per-grade
    # _PARAM_BOUNDS[grade] (q_max: g2=50, g3=100). All MATATAG K-3
    # division LCs use operand-bound language ("2,3,4,5,10 tables" or
    # "2- to 3-digit numbers"), not result-bound language
    # ("quotients up to N"). The `max_quotient` axis was removed from
    # the catalog on 2026-07-01 — see axes_catalog.py header.
    elif dna_name == "division":
        # Parse table level
        if "6, 7, 8, and 9" in text or "6, 7, 8, 9" in text or "6, 7, 8, or 9" in text:
            bounds["table"] = "6_7_8_9"
        elif "2, 3" in text and "5, and 10" in text:
            bounds["table"] = "2_3_4_5_10"
        elif "2, 3, 4, 5, and 10" in text or "2, 3, 4, 5, 10" in text:
            bounds["table"] = "2_3_4_5_10"
            
        # Parse remainder
        if "without remainder" in text:
            bounds["remainder"] = "none"
        elif "with remainder" in text:
            bounds["remainder"] = "with_remainder"

        # Parse missing structure
        if "missing number" in text or "missing term" in text:
            bounds["structure"] = "divisor_unknown"

        # "Estimate the quotient of 2- to 3-digit numbers divided by 1- to
        # 2-digit numbers, using multiples of 10 or 100 as appropriate"
        # (mat_g3_na_q4_4) -- round the dividend to the nearest 10/100
        # (matching its own magnitude), keep the divisor exact, then
        # divide -- a skill nothing in this DNA produced before
        # task_type="estimate" was added (see division.py
        # generate_params). The co-mapped `rounding` DNA rounds ONE
        # number in isolation with no division step attached at all, so
        # it cannot express this competency regardless of which node
        # maps to it.
        if "estimate" in text:
            bounds["task_type"] = "estimate"

    # Counting: "count up to X", "numbers up to X"
    elif dna_name == "counting":
        match = re.search(r'(?:count|numbers?)\s+(?:up\s+to|to)\s+(\d+)', text)
        if match:
            max_val = int(match.group(1))
            min_val = 10
            bounds["range"] = (min_val, max_val)

        # Parse skip pool + skip_interval from text. counting.py's
        # generate_params() has TWO axes: skip_pool (eligible skip values)
        # and skip_interval (which BAND of that pool _select_skip() actually
        # draws from). skip_interval was never bound here, so it always
        # defaulted to "by_1" -- and _select_skip()'s "by_1" branch
        # unconditionally returns 1 whenever 1 is anywhere in skip_pool.
        # The old logic below added 1 to skip_pool via a bare "count" in
        # text substring check, which matches almost every counting
        # competency (nearly all contain the word "count") -- so every
        # "count by 2s/5s/10s" competency silently degraded to plain +1
        # counting, 100% of the time, regardless of seed.
        skip_10_100 = [x for x in (20, 50, 100, 250, 1000) if f"{x}s" in text]
        skip_2_5_10 = [x for x in (2, 5, 10) if f"{x}s" in text]
        if skip_10_100:
            bounds["skip_pool"] = skip_2_5_10 + skip_10_100
            bounds["skip_interval"] = "by_20_50_100"
        elif skip_2_5_10:
            bounds["skip_pool"] = skip_2_5_10
            bounds["skip_interval"] = "by_2_5_10"
        elif "1 more or 1 less" in text:
            bounds["skip_pool"] = [1]
            bounds["skip_interval"] = "by_1"
        # else: leave unbound -- plain counting nodes (recognize/represent
        # numbers, count-up-as-addition-strategy, repeated-addition groups)
        # correctly use the DNA's own by_1 default without a bound.
    
    # Area: bind task_type per node -- the DNA's own default
    # (task_type="find_area") silently governed every unbound node, so
    # "illustrate ... using square tile units" (mat_g3_mg_q1_0) and
    # "explore inductively the derivation of the formula[s]"
    # (mat_g3_mg_q1_1) rendered indistinguishably from the plain
    # "find the area" competency (mat_g3_mg_q1_2), and the symbolic
    # fallback question text didn't even show the shape's dimensions.
    elif dna_name == "area":
        if "derivation" in text or "derive" in text:
            bounds["task_type"] = "derive_formula"
        elif "illustrate" in text or "estimate" in text:
            bounds["task_type"] = "illustrate_tiles"

    # Comparing/ordering: bind task_type per node -- the DNA's own default
    # (task_type="compare_pair") silently governed every unbound node, so
    # every "Order numbers ... from smallest to largest" competency
    # (mat_g1_na_q1_4, mat_g1_na_q2_0, mat_g2_na_q1_4, mat_g3_na_q1_6)
    # rendered a pairwise >/</= comparison instead of ordering a full set.
    # Calendar: "Give the days of the week and months of the year in the
    # correct order" has no matching task_type in the DNA's own default
    # (task_type="read_day", which reads a date off a calendar grid, not a
    # recitation/sequencing task) -- bind the new "sequence" task_type.
    elif dna_name == "calendar" and "correct order" in text:
        bounds["task_type"] = "sequence"

    # Length measurement: bind task_type per node -- "identify and use the
    # appropriate unit" and "estimate length" had no matching task_type in
    # this DNA at all (it only ever measured in a unit already chosen for
    # it, and read_measurement/estimate were never differentiated), so both
    # competencies silently rendered the same "Measure the object..."
    # read_measurement stem.
    elif dna_name == "length_measurement":
        if "appropriate unit" in text or "identify and use" in text:
            bounds["task_type"] = "choose_unit"
        elif "estimate" in text:
            bounds["task_type"] = "estimate"
        elif "equal length" in text:
            bounds["task_type"] = "compare"

    # Pictographs: bind task_type per node -- the DNA's own default
    # (task_type="read_value") silently governed every unbound node, and
    # "present_data"/"organize_table" are already correctly wired to their
    # own dedicated formatters (pictograph_set / fill_in_table, see
    # compatibility.py FORMATTER_VARIANT_SUPPORT) -- that routing just
    # never activated because task_type was never bound to those values.
    # "Collect data ... through a simple interview" (mat_g1_dp_q3_0) has no
    # matching task_type in this DNA at all (collecting raw responses is a
    # different action from presenting/organizing already-collected data);
    # routed to "organize_table" as the closest available proxy -- a
    # student who can organize interview-style tally data into a table is
    # exercising a real component of this competency, though not the
    # "conduct the interview" part itself, which this DNA has no way to
    # represent.
    elif dna_name == "pictographs":
        if "organize" in text or "into a table" in text or "collect" in text:
            bounds["task_type"] = "organize_table"
        elif "present" in text:
            bounds["task_type"] = "present_data"
        if "without a scale" in text or "without scale" in text:
            bounds["scale_type"] = "no_scale"

    elif dna_name == "comparing_ordering":
        if "order" in text:
            bounds["task_type"] = "order_sequence"
        elif "compare" in text:
            bounds["task_type"] = "compare_pair"

    # Patterns: bind pattern_type/ask_type per node -- patterns.py's own
    # default (pattern_type="growing" -> arithmetic_increasing, ask_type=
    # "next") silently governed every unbound node, so a "repeating
    # pattern" competency (mat_g1_na_q3_6) rendered plain +1/skip counting
    # instead of a cyclical repeat unit, and a "missing term in a
    # repeating+increasing pattern" competency (mat_g3_na_q3_5) never
    # showed the required combined/cyclical structure. "Create ..."
    # competencies (mat_g1_na_q3_7, mat_g2_na_q2_9) and "Explain how to
    # generate ..." (mat_g3_na_q3_6) are deliberately left unbound here --
    # this DNA only produces fill-in-the-blank "next/missing term" items,
    # it has no construct-your-own-pattern or explain-the-rule task type,
    # so those 3 nodes need new DNA content, not just a routing fix.
    elif dna_name == "patterns":
        if "repeating and increasing" in text or "repeating and decreasing" in text or "increasing components" in text:
            bounds["pattern_type"] = "combined"
        elif "repeating" in text:
            bounds["pattern_type"] = "repeating"
        elif "increasing" in text and "decreasing" in text:
            bounds["pattern_type"] = "increasing_or_decreasing"
        if "missing term" in text:
            bounds["ask_type"] = "missing"
        elif "next term" in text:
            bounds["ask_type"] = "next"
        elif "create" in text:
            # "Create ... patterns" (mat_g1_na_q3_7, mat_g2_na_q2_9) has no
            # free-form construction UI in this pipeline; routed to
            # ask_type="identify_valid" (patterns.py: pick which candidate
            # sequence actually satisfies the pattern rule vs. ones that
            # break it partway through) as the closest machine-gradable
            # proxy for "can construct a valid pattern of this type".
            bounds["ask_type"] = "identify_valid"
        elif "explain how to generate" in text:
            bounds["ask_type"] = "explain"

    # Order of operations: "Perform/solve ... addition and subtraction of 3 to
    # 4 numbers ... observing correct order of operations" (mat_g3_na_q2_6/_7)
    # -- was registered end-to-end (compatibility.py, axes_catalog.py,
    # adapter.py) but never mapped to a node, so it was unreachable and its
    # only output was "What is the value of None + None?" (no branch existed
    # for this concept in either question-text builder). "solve problems" +
    # "money" (q2_7) both drive this DNA's own context/money framing.
    elif dna_name == "order_of_operations":
        if "solve" in text and "problem" in text:
            bounds["context"] = "word_problem"
        # "money" is deliberately left unbound, not forced True: "including
        # problems involving money" names money as ONE sub-case of "solve
        # problems ... with 3 to 4 numbers", not the whole scope. Binding it
        # True would make every item money-themed and the plain-object
        # word problems this same sentence also covers would never appear.
        # The DNA's own generate_params randomizes money ~50/50 per seed
        # when this stays unbound (see order_of_operations.py).

    # Missing Number: "missing number in addition or subtraction... / multiplication or division..."
    elif dna_name == "missing_number":
        # Parse operation
        if "equivalent" in text:
            bounds["operation"] = "equivalent"
        elif "multiplication" in text or "division" in text:
            bounds["operation"] = "multiplication_division"
        elif "addition" in text or "subtraction" in text:
            bounds["operation"] = "addition_subtraction"

        # Parse limit / max_result. Same >= 10 floor as the subtraction branch
        # and the generic extraction below: this pattern has no digit-width
        # guard either, so "up to 2 digits"-style phrasing would otherwise bind
        # max_result=2. No current node trips it (the live parses are 10, 20 and
        # three Nones), so this closes the latent instance of the same root
        # cause without changing any bound.
        match = re.search(r'(?:numbers|sums?|differences?|up\s+to|to)\s+(\d+)', text)
        if match and int(match.group(1)) >= 10:
            bounds["max_result"] = int(match.group(1))

        # Parse tables
        if "6, 7, 8, and 9" in text or "6, 7, 8, 9" in text or "6, 7, 8, or 9" in text:
            bounds["tables"] = [6, 7, 8, 9]
        elif "2, 3, 4, 5, and 10" in text or "2, 3, 4, 5, 10" in text or "2, 3, 4, 5, or 10" in text:
            bounds["tables"] = [2, 3, 4, 5, 10]
            
    # Place value: "X-digit numbers"
    elif dna_name == "place_value":
        # place_value.py's generate_params() reads a *discrete* string
        # profile key "digit_count" (values "2_digit"/"3_digit"/"4_digit",
        # per axes_catalog.py) -- this used to bind a differently-named,
        # differently-shaped key "num_digits" as a (min,max) tuple, which
        # matches nothing generate_params() reads and nothing
        # axes_catalog.py registers, so it was silently dropped by the
        # orchestrator's continuous-axis mapping step (tuple bounds only
        # resolve for axes actually registered under that exact name).
        # Every place_value node was capped at generate_params()'s own
        # "2_digit" default regardless of the competency's stated digit
        # count (e.g. mat_g3_na_q1_3: "place value in a 4-digit number"
        # rendered only 2-digit numbers like 45, 20, 15).
        match = re.search(r'(\d+)-digit', text)
        if match:
            digits = int(match.group(1))
            bounds["digit_count"] = f"{digits}_digit"
        # task_type was previously pure metadata in generate_params() (every
        # value produced identical output), so "decompose" competencies
        # rendered indistinguishably from "identify the place value"
        # (mat_g1_na_q2_3 vs. mat_g1_na_q2_2). Bind it now that
        # generate_params() genuinely branches on it.
        if "decompose" in text:
            bounds["task_type"] = "decompose"
        elif "value of a digit" in text and "digit of" in text and "given its place value" in text:
            # This competency explicitly names all 3 place-value sub-skills
            # (name the place, compute the value, reverse-lookup the digit)
            # -- alternate across all three rather than defaulting to just
            # one (see place_value.py's "any_place_value_skill" composite
            # value).
            bounds["task_type"] = "any_place_value_skill"

    # Number reading: "numerals/numbers up to X"
    elif dna_name == "number_reading":
        match = re.search(r'(?:numerals?|numbers?)\s+(?:up\s+to|to)\s+(\d+)', text)
        if match:
            max_val = int(match.group(1))
            bounds["range"] = (10, max_val)

    # Symmetry and slides: this DNA's item pool spans four disjoint curriculum
    # scopes (rotation/turns; slide/translation; line symmetry; completing a
    # symmetric figure) and every node bound to it must pin exactly one via
    # concept -- leaving concept unbound ("pass") does NOT mean "the DNA
    # shows relevant content regardless" as the old comment assumed; it means
    # the DNA's own hardcoded default governs, which is "slide_translation"
    # for grade>1, so every unbound G2/G3 node here silently defaulted to
    # slide/translation content regardless of its actual competency (only
    # mat_g1_mg_q4_0 coincidentally showed correct rotation content, because
    # slide_translation has no grade_min=1 items so its own fallback cascade
    # happened to land back on the only grade-eligible concept, rotation).
    elif dna_name == "symmetry_slides":
        if "complete" in text and ("symmetric" in text or "symmetry" in text):
            bounds["concept"] = "complete_symmetric_figure"
        elif "symmetry" in text or "symmetric" in text:
            bounds["concept"] = "line_symmetry"
        elif "turn" in text or "clockwise" in text:
            bounds["concept"] = "rotation"
        elif "slide" in text or "translation" in text:
            bounds["concept"] = "slide_translation"
            if "two-direction" in text or "two direction" in text:
                bounds["directions"] = "two_directions"
            elif "one-direction" in text or "one direction" in text:
                bounds["directions"] = "one_direction"

    # Mass and capacity: this DNA's default measurement_type is always
    # "mass" (mass_capacity.py's generate_params) regardless of what's
    # bound -- leaving it "unrestricted" (the old `pass` branch here) does
    # NOT mean the DNA shows capacity content, it means the DNA's own mass
    # default silently governs. This left all 3 capacity-competency nodes
    # (measure/estimate/compare capacity in L/mL) rendering 100% mass-in-
    # grams content. Bind explicitly both ways, plus task_type from
    # estimate/compare keywords (same silent-default risk applies there).
    elif dna_name == "mass_capacity":
        # "capacit" stem catches both "capacity" and the plural "capacities"
        # (mat_g3_mg_q2_5: "Compare capacities of two containers" -- the
        # literal substring "capacity" does not appear in "capacities").
        if "capacit" in text or "liter" in text or "milliliter" in text or "volume" in text:
            bounds["measurement_type"] = "capacity"
        else:
            bounds["measurement_type"] = "mass"
        if "estimate" in text:
            bounds["task_type"] = "estimate"
        elif "compare" in text:
            bounds["task_type"] = "compare"
        elif "measure" in text:
            bounds["task_type"] = "read_measurement"

    # 2D shapes: this DNA's item pool spans multiple task types (name a
    # shape, count sides/corners, compare shapes, compose/decompose) and
    # shape sets (basic triangles/rectangles/squares vs. circles/half/quarter
    # circles vs. composite figures) -- every node must pin both, or the
    # DNA's own default (basic_triangles_rectangles_squares / identify_name)
    # silently governs regardless of what the node's competency actually
    # asks for (this silently dropped circles/composite figures entirely
    # for the two G2 nodes that introduce them).
    elif dna_name == "shapes_2d":
        if "composite figure" in text:
            bounds["shape_set"] = "composite_figures"
        elif "circle" in text:
            bounds["shape_set"] = "extended_with_circles"
        if "compose" in text and "decompose" in text:
            bounds["task_type"] = "compose_decompose"
        elif "compare" in text or "distinguish" in text:
            bounds["task_type"] = "compare_shapes"

    # Geometric lines: this DNA's item pool spans three disjoint curriculum
    # scopes (straight/curved lines & surfaces; parallel/intersecting/
    # perpendicular lines; point/line/segment/ray naming) and every node
    # bound to it must pin exactly one via concept_type -- generate_params()
    # raises rather than substituting a different scope's content when the
    # bound concept_type has no grade-eligible items, so an unmatched branch
    # here is a loud failure, not a silent content swap.
    # Money peso: bind operation when a competency explicitly requires
    # BOTH addition and subtraction of money (e.g. mat_g1_na_q4_6:
    # "addition of money ... or subtraction of money") -- money_peso.py
    # otherwise always defaults to "add_amounts" (never varies), so the
    # "or subtraction" half of the competency was never exercised, and
    # once word-problem framing turned on, spine selection could still
    # narrate the always-addition computation with a subtraction spine
    # (see base_generator.py's money_peso operation->domain mapping).
    elif dna_name == "money_peso" and "addition" in text and "subtraction" in text:
        bounds["operation"] = "add_or_subtract"

    elif dna_name == "geometric_lines":
        if "straight" in text and "curved" in text:
            bounds["concept_type"] = "straight_curved"
        elif "parallel" in text or "intersecting" in text or "perpendicular" in text:
            bounds["concept_type"] = "parallel_intersecting_perpendicular"
        else:
            bounds["concept_type"] = "point_line_segment_ray"

    # Fractions: "unit fraction" (numerator fixed at 1) and "similar fraction"
    # (same-denominator, numerator > 1) are two different competencies sharing
    # this DNA -- mat_g2_na_q4_1 ("read and write unit fractions") and
    # mat_g2_na_q4_4 ("read and write similar fractions") had identical bounds
    # ({}), so both silently fell through to generate_params' own default
    # (fraction_type="unit_fraction"). The "similar" node never exercised a
    # numerator > 1, which is the entire point that distinguishes it from the
    # "unit" node. Bind explicitly from the LC wording.
    elif dna_name == "fractions":
        if "unit fraction" in text:
            bounds["fraction_type"] = "unit_fraction"
        elif "similar fraction" in text:
            bounds["fraction_type"] = "similar_proper"
            
    # Generic text-scrape fallback if no primary limit key was found.
    # Attempt to extract any number >= 10 from the LC text and use it
    # as the bound for dimension-bearing DNA concepts.
    # NOTE: `max_difference` was removed from this list on 2026-07-01.
    # Subtraction LCs are all operand-bound ("both numbers are less
    # than N"), not result-bound, so the DNA's per-grade bounds suffice.
    limit_keys = ["range", "max_value", "max_total", "max_sum", "max_product", "num_digits"]
    if not any(key in bounds for key in limit_keys):
        limits = []
        
        # Check for digit limits first (e.g. "up to 4 digits")
        digit_match = re.search(r'(?:up\s+to|to)\s+(\d+)\s+digits?', text)
        if digit_match:
            digits = int(digit_match.group(1))
            val = (10 ** digits) - 1
            limits.append(val)
        else:
            for match in re.finditer(r'\b\d+\b', text):
                val = int(match.group(0))
                if val >= 10:
                    limits.append(val)
                    
        if limits:
            limit = max(limits)
            if dna_name in ("comparing_ordering", "rounding"):
                bounds["max_value"] = (1, limit)
            elif dna_name in ("counting", "number_reading"):
                bounds["range"] = (10, limit)
            elif dna_name == "money_peso":
                bounds["max_total"] = (1, limit)
            elif dna_name == "addition":
                bounds["max_sum"] = (0, limit)
            elif dna_name == "place_value" and "digit_count" not in bounds:
                # Same key-name fix as the primary place_value branch above
                # ("num_digits" -> "digit_count") applied to this
                # generic-number-extraction fallback path.
                if limit >= 1000:
                    bounds["digit_count"] = "4_digit"
                elif limit >= 100:
                    bounds["digit_count"] = "3_digit"
                elif limit >= 10:
                    bounds["digit_count"] = "2_digit"

    # ── Grade-aware curriculum fallback ──────────────────────────────────────
    # If after all text parsing we STILL have no primary bound for a
    # dimension-bearing DNA concept, apply the MATATAG per-grade ceiling.
    # This ensures scalar 1.0 ALWAYS resolves to a curriculum-valid integer
    # and never crashes the DNA with an impossibly small max.
    if not any(key in bounds for key in limit_keys):
        grade_defaults = _GRADE_DEFAULT_BOUNDS.get(dna_name, {}).get(grade, {})
        if "max_sum" in grade_defaults and dna_name == "addition":
            bounds["max_sum"] = (0, grade_defaults["max_sum"])
        elif "max_value" in grade_defaults and dna_name in ("comparing_ordering", "rounding"):
            bounds["max_value"] = (1, grade_defaults["max_value"])
        elif "range_max" in grade_defaults and dna_name in ("counting", "number_reading"):
            bounds["range"] = (10, grade_defaults["range_max"])
        elif "max_product" in grade_defaults and dna_name == "multiplication":
            # A competency that names specific multiplication tables states its
            # own ceiling: the largest table times the largest single-digit
            # multiplicand the tables are practised against. The grade default
            # (1000 at G3) described a range those nodes can never reach —
            # "Multiply numbers using the 6, 7, 8, and 9 multiplication tables"
            # tops out at 9 x 10 = 90 — so scalar 1.0 pointed at a ceiling ten
            # times beyond the curriculum's actual scope (validate_matrix
            # §1A-reach). Ground-truth correction, Ground Rule 2.
            # Table language is parsed into bounds["tables"] only on the
            # missing_number branch, so read it from the competency text here
            # too rather than silently falling back to the grade default.
            tables = bounds.get("tables")
            if not tables:
                if "6, 7, 8, and 9" in text or "6, 7, 8, 9" in text or "6, 7, 8, or 9" in text:
                    tables = [6, 7, 8, 9]
                elif ("2, 3, 4, 5, and 10" in text or "2, 3, 4, 5, 10" in text
                      or "2, 3, 4, 5, or 10" in text):
                    tables = [2, 3, 4, 5, 10]
            if tables:
                bounds["max_product"] = (0, max(tables) * 10)
            else:
                bounds["max_product"] = (0, grade_defaults["max_product"])
        elif "max_total" in grade_defaults and dna_name == "money_peso":
            bounds["max_total"] = (1, grade_defaults["max_total"])

    # Extract regrouping booleans
    if "without regrouping" in text:
        bounds["regrouping"] = False
    elif "with regrouping" in text:
        bounds["regrouping"] = True
    elif dna_name == "fractions" and ("add" in text or "subtract" in text or "sum" in text or "difference" in text):
        bounds["operation"] = "add_subtract"
    elif "with and without regrouping" in text:
        # Don't strictly bound it, let the catalog dictate options
        pass

    # Cross-cutting: "Solve problems ..." competencies require word-problem
    # framing, not a bare number sentence -- but "context" defaults to
    # "pure" in every arithmetic DNA (addition/subtraction/multiplication/
    # division all register context=["pure","word_problem"] yet nothing
    # ever bound it), so ~20 "solve problems" competencies across the
    # curriculum silently rendered plain arithmetic facts with zero
    # narrative. Only apply when this DNA genuinely registers
    # "word_problem" as a context option (VARIANTS_BY_DNA is the source of
    # truth), so this never fires for DNAs with no such variant.
    if "solve" in text and "problem" in text and "word_problem" in VARIANTS_BY_DNA.get(dna_name, {}).get("context", []):
        bounds.setdefault("context", "word_problem")

    return bounds


def get_node_competency_bounds(node_id: str, dna_name: Optional[str] = None) -> Dict[str, Tuple[int, int]]:
    """
    Get competency-specific bounds for a node's difficulty dimensions.
    
    Returns dict mapping dimension names to (min, max) tuples, derived
    from the LC text. When the LC text has no explicit numeric ceiling,
    falls back to the MATATAG grade-appropriate default so that scalar
    1.0 always maps to a valid maximum (never crashes the DNA).
    
    Returns empty dict if node not found or no DNA mappings exist.
    """
    node_info = _KG_NODES.get(node_id)
    if not node_info:
        return {}
    
    competency = node_info.get("competency", "")
    grade = node_info.get("grade", 1)
    dnas = NODE_TO_DNA.get(node_id, [])
    if not dnas:
        return {}
    
    # Use selected DNA if provided and valid, otherwise fallback to primary DNA
    selected_dna = dna_name if (dna_name and dna_name in dnas) else dnas[0]
    return _parse_competency_bounds(competency, selected_dna, grade)


# ═══════════════════════════════════════════════════════════════════════════════
# NODE_TO_DNA
# Static mapping of node_id → list of DNA concept names.
#
# Construction rationale:
#   - Each node covers 1–3 closely related competency aspects.
#   - DNA names are the exact concept strings from each DNA file.
#   - When a node spans two concepts (e.g. add + subtract in the same
#     problem-solving context), both are listed so the pipeline can pick
#     the most appropriate one for a given formatter.
# ═══════════════════════════════════════════════════════════════════════════════

from backend.app.practice_gen.schemas.visuals import VisualSchemaRegistry

# New Binding Registry (Phase 2 Migration)
BINDINGS = {
    "mat_g1_na_q1_0": {
        "dna": "counting",
        "visual": "emoji_pictorial"
    },
    "mat_g1_na_q1_1": {
        "dna": "number_reading",
        "visual": "emoji_pictorial"
    },
    "mat_g1_na_q1_2": {
        "dna": "number_reading",
        "visual": "emoji_pictorial"
    },
    "mat_g1_na_q1_3": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g1_na_q1_4": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g1_na_q1_5": {
        "dna": "ordinal_numbers",
        "visual": "sort_order"
    },
    "mat_g1_na_q1_6": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q1_7": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q1_8": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q1_9": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q2_0": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g1_na_q2_1": {
        "dna": "counting",
        "visual": "emoji_pictorial"
    },
    "mat_g1_na_q2_2": {
        "dna": "place_value",
        "visual": "place_value_blocks_read"
    },
    "mat_g1_na_q2_3": {
        "dna": "place_value",
        "visual": "place_value_blocks_read"
    },
    "mat_g1_na_q2_4": {
        "dna": "place_value",
        "visual": "place_value_blocks_read"
    },
    "mat_g1_na_q2_5": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q2_6": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g1_na_q3_0": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g1_na_q3_1": {
        "dna": "missing_number",
        "visual": "NumberBond"
    },
    "mat_g1_na_q3_2": {
        "dna": "missing_number",
        "visual": "NumberBond"
    },
    "mat_g1_na_q3_3": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g1_na_q3_4": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g1_na_q3_5": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g1_na_q3_6": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g1_na_q3_7": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g1_na_q4_0": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g1_na_q4_1": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g1_na_q4_2": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g1_na_q4_3": {
        "dna": "money_peso",
        "visual": "peso_money_read"
    },
    "mat_g1_na_q4_4": {
        "dna": "money_peso",
        "visual": "peso_money_build"
    },
    "mat_g1_na_q4_5": {
        "dna": "money_peso",
        "visual": "peso_money_build"
    },
    "mat_g1_na_q4_6": {
        "dna": "money_peso",
        "visual": "peso_money_build"
    },
    "mat_g1_mg_q1_0": {
        "dna": "shapes_2d",
        "visual": "shape_board"
    },
    "mat_g1_mg_q1_1": {
        "dna": "shapes_2d",
        "visual": "shape_board"
    },
    "mat_g1_mg_q1_2": {
        "dna": "shapes_2d",
        "visual": "shape_board"
    },
    "mat_g1_mg_q2_0": {
        "dna": "length_measurement",
        "visual": "ruler_measure"
    },
    "mat_g1_mg_q2_1": {
        "dna": "length_measurement",
        "visual": "ruler_measure"
    },
    "mat_g1_mg_q2_2": {
        "dna": "length_measurement",
        "visual": "ruler_measure"
    },
    "mat_g1_mg_q4_0": {
        "dna": "symmetry_slides",
        "visual": "shape_board"
    },
    "mat_g1_mg_q4_1": {
        "dna": "time_reading",
        "visual": "clock_set"
    },
    "mat_g1_mg_q4_2": {
        "dna": "calendar",
        "visual": "Calendar"
    },
    "mat_g1_mg_q4_3": {
        "dna": "calendar",
        "visual": "Calendar"
    },
    "mat_g1_mg_q4_4": {
        "dna": "time_reading",
        "visual": "clock_set"
    },
    "mat_g1_dp_q3_0": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g1_dp_q3_1": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g1_dp_q3_2": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g1_dp_q3_3": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g2_na_q1_0": {
        "dna": "counting",
        "visual": "number_line_read"
    },
    "mat_g2_na_q1_1": {
        "dna": "number_reading",
        "visual": "place_value_blocks_read"
    },
    "mat_g2_na_q1_2": {
        "dna": "number_reading",
        "visual": "place_value_blocks_read"
    },
    "mat_g2_na_q1_3": {
        "dna": "counting",
        "visual": "bar_chart_read"
    },
    "mat_g2_na_q1_4": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g2_na_q1_5": {
        "dna": "ordinal_numbers",
        "visual": "mcq"
    },
    "mat_g2_na_q1_6": {
        "dna": "place_value",
        "visual": "place_value_blocks_read"
    },
    "mat_g2_na_q1_7": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g2_na_q1_8": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g2_na_q1_9": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g2_na_q1_10": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_0": {
        "dna": "money_peso",
        "visual": "peso_money_read"
    },
    "mat_g2_na_q2_1": {
        "dna": "money_peso",
        "visual": "peso_money_read"
    },
    "mat_g2_na_q2_2": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_3": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_4": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_5": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_6": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_7": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g2_na_q2_8": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g2_na_q2_9": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g2_na_q3_0": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_1": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_2": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_3": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_4": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_5": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_6": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_7": {
        "dna": "missing_number",
        "visual": "mcq"
    },
    "mat_g2_na_q3_8": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q3_9": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g2_na_q4_0": {
        "dna": "fractions",
        "visual": "fraction_shade"
    },
    "mat_g2_na_q4_1": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g2_na_q4_2": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g2_na_q4_3": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g2_na_q4_4": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g2_na_q4_5": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g2_mg_q1_0": {
        "dna": "shapes_2d",
        "visual": "shape_board"
    },
    "mat_g2_mg_q1_1": {
        "dna": "shapes_2d",
        "visual": "shape_board"
    },
    "mat_g2_mg_q1_2": {
        "dna": "symmetry_slides",
        "visual": "shape_board"
    },
    "mat_g2_mg_q2_0": {
        "dna": "length_measurement",
        "visual": "ruler_measure"
    },
    "mat_g2_mg_q2_1": {
        "dna": "length_measurement",
        "visual": "mcq"
    },
    "mat_g2_mg_q2_2": {
        "dna": "length_measurement",
        "visual": "mcq"
    },
    "mat_g2_mg_q2_3": {
        "dna": "length_measurement",
        "visual": "mcq"
    },
    "mat_g2_mg_q4_0": {
        "dna": "time_reading",
        "visual": "clock_set"
    },
    "mat_g2_mg_q4_1": {
        "dna": "time_reading",
        "visual": "clock_set"
    },
    "mat_g2_mg_q4_2": {
        "dna": "time_reading",
        "visual": "clock_set"
    },
    "mat_g2_mg_q4_3": {
        "dna": "geometric_lines",
        "visual": "mcq"
    },
    "mat_g2_mg_q4_4": {
        "dna": "perimeter",
        "visual": "mcq"
    },
    "mat_g2_mg_q4_5": {
        "dna": "perimeter",
        "visual": "mcq"
    },
    "mat_g2_mg_q4_6": {
        "dna": "perimeter",
        "visual": "mcq"
    },
    "mat_g2_dp_q3_0": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g2_dp_q3_1": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g3_na_q1_0": {
        "dna": "number_reading",
        "visual": "number_line_read"
    },
    "mat_g3_na_q1_1": {
        "dna": "number_reading",
        "visual": "place_value_blocks_read"
    },
    "mat_g3_na_q1_2": {
        "dna": "ordinal_numbers",
        "visual": "mcq"
    },
    "mat_g3_na_q1_3": {
        "dna": "place_value",
        "visual": "place_value_blocks_read"
    },
    "mat_g3_na_q1_4": {
        "dna": "rounding",
        "visual": "number_line_read"
    },
    "mat_g3_na_q1_5": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g3_na_q1_6": {
        "dna": "comparing_ordering",
        "visual": "sort_order"
    },
    "mat_g3_na_q2_0": {
        "dna": "money_peso",
        "visual": "peso_money_read"
    },
    "mat_g3_na_q2_1": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_2": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_3": {
        "dna": "addition",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_4": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_5": {
        "dna": "subtraction",
        "visual": "number_line_read"
    },
    "mat_g3_na_q2_6": {
        "dna": "order_of_operations",
        "visual": "mcq"
    },
    "mat_g3_na_q2_7": {
        "dna": "order_of_operations",
        "visual": "mcq"
    },
    "mat_g3_na_q3_0": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q3_1": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q3_2": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q3_3": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q3_4": {
        "dna": "multiplication",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q3_5": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g3_na_q3_6": {
        "dna": "patterns",
        "visual": "pattern_sequence"
    },
    "mat_g3_na_q4_0": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q4_1": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q4_2": {
        "dna": "missing_number",
        "visual": "mcq"
    },
    "mat_g3_na_q4_3": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q4_4": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q4_5": {
        "dna": "division",
        "visual": "array_grid_read"
    },
    "mat_g3_na_q4_6": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g3_na_q4_7": {
        "dna": "fractions",
        "visual": "fraction_model_read"
    },
    "mat_g3_mg_q1_0": {
        "dna": "area",
        "visual": "shape_board"
    },
    "mat_g3_mg_q1_1": {
        "dna": "area",
        "visual": "grid_area"
    },
    "mat_g3_mg_q1_2": {
        "dna": "area",
        "visual": "grid_area"
    },
    "mat_g3_mg_q1_3": {
        "dna": "area",
        "visual": "grid_area"
    },
    "mat_g3_mg_q1_4": {
        "dna": "geometric_lines",
        "visual": "mcq"
    },
    "mat_g3_mg_q1_5": {
        "dna": "geometric_lines",
        "visual": "mcq"
    },
    "mat_g3_mg_q1_6": {
        "dna": "geometric_lines",
        "visual": "mcq"
    },
    "mat_g3_mg_q2_0": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q2_1": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q2_2": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q2_3": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q2_4": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q2_5": {
        "dna": "mass_capacity",
        "visual": "bar_chart_read"
    },
    "mat_g3_mg_q4_0": {
        "dna": "symmetry_slides",
        "visual": "shape_board"
    },
    "mat_g3_mg_q4_1": {
        "dna": "symmetry_slides",
        "visual": "shape_board"
    },
    "mat_g3_mg_q4_2": {
        "dna": "symmetry_slides",
        "visual": "shape_board"
    },
    "mat_g3_dp_q3_0": {
        "dna": "pictographs",
        "visual": "pictograph_read"
    },
    "mat_g3_dp_q3_1": {
        "dna": "bar_graphs",
        "visual": "bar_chart_read"
    },
    "mat_g3_dp_q3_2": {
        "dna": "bar_graphs",
        "visual": "bar_chart_read"
    },
    "mat_g3_dp_q3_3": {
        "dna": "bar_graphs",
        "visual": "bar_chart_read"
    },
    "mat_g3_dp_q3_4": {
        "dna": "probability_language",
        "visual": "mcq"
    }
}

NODE_TO_DNA: Dict[str, List[str]] = {

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 1 — Number & Algebra
    # ────────────────────────────────────────────────────────────────────────

    # Q1: Counting, reading, representing, comparing, ordering, ordinals,
    #     compose/decompose, addition intro, properties of addition
    "mat_g1_na_q1_0": ["counting"],
    "mat_g1_na_q1_1": ["number_reading"],
    "mat_g1_na_q1_2": ["number_reading", "counting"],
    "mat_g1_na_q1_3": ["comparing_ordering"],
    "mat_g1_na_q1_4": ["comparing_ordering"],
    "mat_g1_na_q1_5": ["ordinal_numbers"],
    "mat_g1_na_q1_6": ["missing_number", "addition"],
    "mat_g1_na_q1_7": ["addition"],
    "mat_g1_na_q1_8": ["addition"],
    "mat_g1_na_q1_9": ["addition"],

    # Q2: Ordering to 100, skip counting, place value (2-digit),
    #     decompose, expanded form addition, addition to 100
    "mat_g1_na_q2_0": ["comparing_ordering"],
    "mat_g1_na_q2_1": ["counting"],
    "mat_g1_na_q2_2": ["place_value"],
    "mat_g1_na_q2_3": ["place_value"],
    "mat_g1_na_q2_4": ["place_value", "addition"],
    "mat_g1_na_q2_5": ["addition"],
    "mat_g1_na_q2_6": ["addition"],

    # Q3: Subtraction intro, missing number, patterns
    "mat_g1_na_q3_0": ["subtraction"],
    "mat_g1_na_q3_1": ["missing_number"],
    # "addition" removed 2026-08-04 (Ground Rule 2): "Write an equivalent
    # expression to a given addition or subtraction expression" is already
    # fully covered by missing_number's operation="equivalent" (bound above
    # from the "equivalent" text match) -- verified 9/10 seeds genuinely
    # present a two-sided equivalent-expression task. The co-mapped
    # addition DNA has no notion of "equivalent expression" at all; when
    # picked it rendered a bare "x + y = ___" fact with no second
    # expression to compare against (0/10 content-word hit in the
    # co-mapped-DNA triage).
    "mat_g1_na_q3_2": ["missing_number"],
    "mat_g1_na_q3_3": ["subtraction"],
    "mat_g1_na_q3_4": ["subtraction"],
    "mat_g1_na_q3_5": ["subtraction", "place_value"],
    "mat_g1_na_q3_6": ["patterns"],
    "mat_g1_na_q3_7": ["patterns"],

    # Q4: Fractions (1/2, 1/4), money (coins/bills to ₱100)
    "mat_g1_na_q4_0": ["fractions"],
    "mat_g1_na_q4_1": ["fractions", "comparing_ordering"],
    "mat_g1_na_q4_2": ["fractions", "counting"],
    "mat_g1_na_q4_3": ["money_peso"],
    "mat_g1_na_q4_4": ["money_peso"],
    "mat_g1_na_q4_5": ["money_peso", "comparing_ordering"],
    # "addition" removed 2026-08-04 (Ground Rule 2): "Solve 1-step problems
    # ... involving addition of money ... or subtraction of money" is fully
    # covered by money_peso's own operation="add_or_subtract" (bound above
    # from the "addition"+"subtraction" text match) plus its existing
    # word-problem framing -- the plain addition DNA has no money framing
    # at all; when picked it rendered bare survey-style sums with zero ₱
    # symbols (the filed FAIL finding quoted 6 of 8 samples with no money
    # content whatsoever, e.g. "What is 30 + 45?").
    "mat_g1_na_q4_6": ["money_peso"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 1 — Measurement & Geometry
    # ────────────────────────────────────────────────────────────────────────

    # Q1: 2D shapes
    "mat_g1_mg_q1_0": ["shapes_2d"],
    "mat_g1_mg_q1_1": ["shapes_2d", "comparing_ordering"],
    "mat_g1_mg_q1_2": ["shapes_2d"],

    # Q2: Length with non-standard units
    "mat_g1_mg_q2_0": ["length_measurement"],
    # "comparing_ordering" removed 2026-08-04 (Ground Rule 2): "Compare
    # lengths and distances using non-standard units" is fully covered by
    # length_measurement's own task_type="compare" (see the new "compare"
    # text match added to this DNA's branch below), which already compares
    # two measured lengths in the SAME non-standard unit. comparing_ordering
    # has no unit awareness at all -- when picked it rendered bare whole-
    # number comparisons with no object or unit (0/10 content-word hit,
    # e.g. "Compare the numbers: 18 ___ 30").
    "mat_g1_mg_q2_1": ["length_measurement"],
    # "addition" removed 2026-08-04 (Ground Rule 2): "Solve problems
    # involving lengths and distances using non-standard units" is already
    # fully covered by length_measurement's own word-problem framing (see
    # this DNA's non_standard branch, context=="word_problem" -- gives two
    # measured objects and asks for the difference). The plain addition DNA
    # has no unit/object awareness; when picked it rendered bare survey-
    # style sums with no length content (0/10 content-word hit, e.g.
    # "What is 10 + 1?").
    "mat_g1_mg_q2_2": ["length_measurement"],

    # Q4: Symmetry/slides, time, calendar
    "mat_g1_mg_q4_0": ["symmetry_slides"],
    "mat_g1_mg_q4_1": ["time_reading"],
    "mat_g1_mg_q4_2": ["calendar"],
    "mat_g1_mg_q4_3": ["calendar"],
    # "addition" removed 2026-08-04 (Ground Rule 2): "Solve problems
    # involving time (hour, half hour, quarter hour, days in a week, and
    # months in a year)" is already fully covered by time_reading's own
    # word-problem framing (context=="word_problem" -- narrates an actor's
    # daily activity at a clock time and asks "what time is that?"). The
    # plain addition DNA has no clock/time awareness at all; when picked it
    # rendered bare survey-style sums with no time content (0/10 content-
    # word hit, e.g. a student-count addition problem with no hour/day/
    # month mentioned).
    "mat_g1_mg_q4_4": ["time_reading"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 1 — Data & Probability
    # ────────────────────────────────────────────────────────────────────────

    "mat_g1_dp_q3_0": ["pictographs"],
    "mat_g1_dp_q3_1": ["pictographs"],
    "mat_g1_dp_q3_2": ["pictographs"],
    "mat_g1_dp_q3_3": ["pictographs"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 2 — Number & Algebra
    # ────────────────────────────────────────────────────────────────────────

    # Q1: Count/read/represent to 1000, skip count, ordinals, place value (3-digit),
    #     addition (expanded form, to 1000, properties)
    "mat_g2_na_q1_0":  ["counting"],
    "mat_g2_na_q1_1":  ["number_reading"],
    "mat_g2_na_q1_2":  ["number_reading", "counting"],
    "mat_g2_na_q1_3":  ["counting"],
    "mat_g2_na_q1_4":  ["comparing_ordering"],
    "mat_g2_na_q1_5":  ["ordinal_numbers"],
    "mat_g2_na_q1_6":  ["place_value"],
    "mat_g2_na_q1_7":  ["addition", "counting"],
    "mat_g2_na_q1_8":  ["addition", "place_value"],
    "mat_g2_na_q1_9":  ["addition"],
    "mat_g2_na_q1_10": ["addition"],

    # Q2: Money (to ₱1000), addition problems, subtraction (to 1000),
    #     patterns (increasing/decreasing)
    "mat_g2_na_q2_0": ["money_peso"],
    "mat_g2_na_q2_1": ["money_peso", "comparing_ordering"],
    "mat_g2_na_q2_2": ["addition", "money_peso"],
    "mat_g2_na_q2_3": ["subtraction"],
    "mat_g2_na_q2_4": ["subtraction"],
    "mat_g2_na_q2_5": ["subtraction"],
    "mat_g2_na_q2_6": ["subtraction"],
    # "addition" removed 2026-08-04 (Ground Rule 2): this competency's verb
    # is exclusively subtraction ("Solve ... problems involving subtraction
    # where both numbers are less than 1000"); the co-mapped addition DNA
    # actively contradicted the node's own scope when picked -- e.g. seed
    # 45's literal "What is 440 + 40?" inside a subtraction-only node. This
    # is a stronger case than the usual off-topic-bleed pattern: it isn't
    # just irrelevant content, it demonstrates the WRONG operation for a
    # competency that names one operation exclusively.
    "mat_g2_na_q2_7": ["subtraction"],
    "mat_g2_na_q2_8": ["patterns"],
    "mat_g2_na_q2_9": ["patterns"],

    # Q3: Repeated addition → multiplication, tables 2-5-10,
    #     division intro, missing number in mult/div, even/odd
    "mat_g2_na_q3_0": ["multiplication", "counting"],
    # "addition" removed 2026-08-01 (Ground Rule 2): the plain addition DNA
    # has no notion of equal groups, so co-mapping it here served generic
    # 2-3-digit sums ("661 + 120") with zero connection to multiplication —
    # not "repeated addition" in the sense this LC names, which requires the
    # SAME addend repeated a table-factor number of times. That is now
    # multiplication's own task_type="repeated_addition" (see registry.py's
    # "repeated addition" text match and multiplication.py generate_params).
    "mat_g2_na_q3_1": ["multiplication"],
    "mat_g2_na_q3_2": ["multiplication"],
    "mat_g2_na_q3_3": ["multiplication"],
    "mat_g2_na_q3_4": ["division"],
    "mat_g2_na_q3_5": ["division"],
    "mat_g2_na_q3_6": ["division"],
    # "multiplication" removed 2026-08-04 (Ground Rule 2): "Find the missing
    # number in a number sentence involving multiplication or division" is
    # already fully covered by missing_number's own
    # operation="multiplication_division" (bound below from the
    # "multiplication"/"division" text match) -- 7 of 9 sampled seeds
    # already presented a genuine blank-in-equation task. The co-mapped
    # multiplication DNA renders its own array-visual question types
    # ("Shade all the squares inside the 1x10 rectangle...") that contain
    # no number sentence or blank at all -- structurally incapable of
    # expressing "find the missing number".
    "mat_g2_na_q3_7": ["missing_number"],
    "mat_g2_na_q3_8": ["division", "comparing_ordering"],
    "mat_g2_na_q3_9": ["division"],

    # Q4: Fractions (unit, similar) with denominators 2-4
    "mat_g2_na_q4_0": ["fractions"],
    # number_reading removed from _1 and _4 (Ground Rule 2, mistaken mapping):
    # "Read and write unit/similar fractions in fraction notation" is about
    # fraction notation, but number_reading reads whole numbers and rendered
    # "Write 227 in words." on these nodes. It also dragged in a range bound of
    # (10, 10000) that no fraction competency states, which is what
    # validate_matrix §1A-reach flagged.
    "mat_g2_na_q4_1": ["fractions"],
    "mat_g2_na_q4_2": ["fractions", "comparing_ordering"],
    "mat_g2_na_q4_3": ["fractions"],
    "mat_g2_na_q4_4": ["fractions"],
    "mat_g2_na_q4_5": ["fractions", "comparing_ordering"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 2 — Measurement & Geometry
    # ────────────────────────────────────────────────────────────────────────

    # Q1: Circles/composite shapes, slides
    "mat_g2_mg_q1_0": ["shapes_2d"],
    "mat_g2_mg_q1_1": ["shapes_2d"],
    "mat_g2_mg_q1_2": ["symmetry_slides"],

    # Q2: Length in m/cm
    "mat_g2_mg_q2_0": ["length_measurement"],
    "mat_g2_mg_q2_1": ["length_measurement"],
    "mat_g2_mg_q2_2": ["length_measurement"],
    "mat_g2_mg_q2_3": ["length_measurement", "addition"],

    # Q4: Duration/elapsed time, time in hours+minutes,
    #     straight vs curved lines, perimeter
    "mat_g2_mg_q4_0": ["time_reading", "calendar"],
    "mat_g2_mg_q4_1": ["time_reading"],
    "mat_g2_mg_q4_2": ["time_reading", "subtraction"],
    "mat_g2_mg_q4_3": ["geometric_lines"],
    "mat_g2_mg_q4_4": ["perimeter", "length_measurement"],
    "mat_g2_mg_q4_5": ["perimeter"],
    "mat_g2_mg_q4_6": ["perimeter", "addition"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 2 — Data & Probability
    # ────────────────────────────────────────────────────────────────────────

    "mat_g2_dp_q3_0": ["pictographs"],
    "mat_g2_dp_q3_1": ["pictographs", "comparing_ordering"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 3 — Number & Algebra
    # ────────────────────────────────────────────────────────────────────────

    # Q1: Numbers to 10 000, ordinals, place value (4-digit),
    #     rounding, comparing/ordering to 10 000
    "mat_g3_na_q1_0": ["number_reading"],
    "mat_g3_na_q1_1": ["number_reading"],
    "mat_g3_na_q1_2": ["ordinal_numbers"],
    "mat_g3_na_q1_3": ["place_value"],
    "mat_g3_na_q1_4": ["rounding"],
    "mat_g3_na_q1_5": ["comparing_ordering"],
    "mat_g3_na_q1_6": ["comparing_ordering"],

    # Q2: Money (write in words/symbols), addition to 10 000
    #     (with regroup, estimate), subtraction, combined ops
    "mat_g3_na_q2_0": ["money_peso", "number_reading"],
    "mat_g3_na_q2_1": ["addition"],
    # "rounding" removed 2026-08-04 (Ground Rule 2, same reasoning as
    # mat_g3_na_q2_5's subtraction fix): rounding.py rounds ONE number;
    # "estimate the sum of addends" is a two-operand skill (round each
    # addend, then add), which rounding alone cannot express regardless
    # of which node maps to it. That capability now lives in addition.py's
    # task_type="estimate" (see the "estimate" text match in
    # _parse_competency_bounds above), so addition covers this
    # competency's full scope on its own.
    "mat_g3_na_q2_2": ["addition"],
    "mat_g3_na_q2_3": ["addition"],
    "mat_g3_na_q2_4": ["subtraction"],
    # "rounding" removed 2026-08-01 (Ground Rule 2): rounding.py rounds ONE
    # number; "estimate the difference of two numbers" is a two-operand
    # skill (round both, then subtract), which rounding alone cannot express
    # regardless of which node maps to it. That capability now lives in
    # subtraction.py's task_type="estimate" (see the "estimate" text match
    # in _parse_competency_bounds above), so subtraction covers this
    # competency's full scope on its own.
    "mat_g3_na_q2_5": ["subtraction"],
    # "addition"/"subtraction" removed 2026-08-01 (Ground Rule 2): neither
    # 2-operand DNA can express "3 to 4 numbers ... observing correct order
    # of operations" -- the orchestrator picked one or the other per
    # generation and served a plain 2-operand fact every time, so the
    # defining multi-term clause was never exercised on any sampled seed.
    # order_of_operations.py (previously built but unreachable, see the
    # registry.py binding above and the DNA module itself) is a genuine
    # 3-4-term chain and covers this competency's full scope on its own.
    "mat_g3_na_q2_6": ["order_of_operations"],
    "mat_g3_na_q2_7": ["order_of_operations"],

    # Q3: Multiplication tables 6-9, properties, 2-3 digit × 1-2 digit,
    #     estimate product, patterns (repeating + increasing)
    "mat_g3_na_q3_0": ["multiplication"],
    "mat_g3_na_q3_1": ["multiplication"],
    "mat_g3_na_q3_2": ["multiplication"],
    # "rounding" removed 2026-08-04 (Ground Rule 2, same reasoning as
    # mat_g3_na_q2_5): rounding.py rounds ONE number; "estimate the
    # product" is a two-factor skill (round both factors to the nearest
    # 10, then multiply), which rounding alone cannot express. That
    # capability now lives in multiplication.py's task_type="estimate".
    "mat_g3_na_q3_3": ["multiplication"],
    "mat_g3_na_q3_4": ["multiplication"],
    "mat_g3_na_q3_5": ["patterns"],
    "mat_g3_na_q3_6": ["patterns"],

    # Q4: Division with tables 6-9, missing term, 2-3 digit ÷ 1 digit,
    #     estimate quotient, fractions ≥ 1, add/sub similar fractions
    "mat_g3_na_q4_0": ["division"],
    "mat_g3_na_q4_1": ["division"],
    "mat_g3_na_q4_2": ["missing_number", "division"],
    "mat_g3_na_q4_3": ["division"],
    # "rounding" removed 2026-08-04 (Ground Rule 2, same reasoning as
    # mat_g3_na_q2_5): rounding.py rounds ONE number; "estimate the
    # quotient" requires rounding the dividend to a multiple of 10/100
    # and then dividing, which rounding alone cannot express. That
    # capability now lives in division.py's task_type="estimate".
    "mat_g3_na_q4_4": ["division"],
    "mat_g3_na_q4_5": ["division"],
    "mat_g3_na_q4_6": ["fractions"],
    "mat_g3_na_q4_7": ["fractions"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 3 — Measurement & Geometry
    # ────────────────────────────────────────────────────────────────────────

    # Q1: Area (sq, rect), geometric lines, equal-length segments
    "mat_g3_mg_q1_0": ["area"],
    "mat_g3_mg_q1_1": ["area"],
    # Ground Rule 2 correction (docs/pgen_hardening.md judgment review):
    # "multiplication" was previously a co-mapped DNA for both nodes below.
    # When picked, it renders generic multiplication word problems with
    # zero connection to area/rectangles/tiles (verified: e.g. "puts 1
    # ribbon in each of N bags" for a "find the area of a rectangle"
    # competency) -- multiplication *underlies* area's formula, but that is
    # already computed internally by area.py itself; testing bare
    # multiplication facts is not what "find/solve problems involving
    # areas of squares and rectangles" asks for. No commit message or doc
    # justified the mapping. Removed as a mistaken node_id->DNA mapping,
    # not a bounds/routing issue.
    "mat_g3_mg_q1_2": ["area"],
    "mat_g3_mg_q1_3": ["area"],
    "mat_g3_mg_q1_4": ["geometric_lines"],
    "mat_g3_mg_q1_5": ["geometric_lines"],
    # Ground Rule 2 correction (docs/pgen_hardening.md judgment review):
    # "geometric_lines" was previously a co-mapped DNA here. Its 3 concept
    # scopes (straight/curved; parallel/intersecting/perpendicular;
    # point/line/segment/ray naming) are all naming/classification tasks --
    # none of them represent "identify and draw line segments of equal
    # length using a ruler", which is a measurement/comparison skill.  When
    # geometric_lines was picked, it fell to its point_line_segment_ray
    # default and rendered "What do we call an exact location in space..."
    # -- an off-topic vocabulary question. length_measurement's own
    # "compare" task_type is the closer (if imperfect -- it compares two
    # *different* lengths rather than verifying/drawing equal ones) match
    # for this competency's ruler-based measurement skill.
    "mat_g3_mg_q1_6": ["length_measurement"],

    # Q2: Mass (g/kg/mg), capacity (L/mL)
    "mat_g3_mg_q2_0": ["mass_capacity"],
    "mat_g3_mg_q2_1": ["mass_capacity"],
    "mat_g3_mg_q2_2": ["mass_capacity", "comparing_ordering"],
    "mat_g3_mg_q2_3": ["mass_capacity"],
    "mat_g3_mg_q2_4": ["mass_capacity"],
    "mat_g3_mg_q2_5": ["mass_capacity", "comparing_ordering"],

    # Q4: Slides (2-direction), symmetry
    "mat_g3_mg_q4_0": ["symmetry_slides"],
    "mat_g3_mg_q4_1": ["symmetry_slides"],
    "mat_g3_mg_q4_2": ["symmetry_slides"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 3 — Data & Probability
    # ────────────────────────────────────────────────────────────────────────

    "mat_g3_dp_q3_0": ["pictographs", "bar_graphs"],
    "mat_g3_dp_q3_1": ["bar_graphs"],
    "mat_g3_dp_q3_2": ["bar_graphs"],
    "mat_g3_dp_q3_3": ["bar_graphs", "addition"],
    "mat_g3_dp_q3_4": ["probability_language"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def get_node_dnas(node_id: str) -> List[str]:
    """
    Return the list of DNA concept names for a node.

    Args:
        node_id: MATATAG node identifier, e.g. "mat_g1_na_q1_7".

    Returns:
        List of DNA concept name strings, or an empty list if the node
        is not in NODE_TO_DNA.
    """
    return NODE_TO_DNA.get(node_id, [])


def get_node_formatters(node_id: str) -> List[str]:
    """
    Return the union of compatible formatters from all DNAs for a node.

    Looks up each DNA concept in COMPATIBILITY and unions the results.
    Preserves insertion order of the first occurrence of each formatter.

    Args:
        node_id: MATATAG node identifier.

    Returns:
        Ordered list of formatter name strings.
    """
    seen: Set[str] = set()
    result: List[str] = []
    for concept in get_node_dnas(node_id):
        for fmt in COMPATIBILITY.get(concept, []):
            if fmt not in seen:
                seen.add(fmt)
                result.append(fmt)
    return result


def get_node_info(node_id: str) -> Optional[Dict]:
    """
    Return the full knowledge-graph node dict for a node.

    Args:
        node_id: MATATAG node identifier.

    Returns:
        Node dict from knowledge_graph_g1_3.json, or None if not found.
    """
    return _KG_NODES.get(node_id)


def find_node_id(grade: int, branch: str, quarter: int, index: int) -> str:
    """
    Construct a node_id from its components.

    Args:
        grade: Grade level (1–3).
        branch: Branch code: "na", "mg", or "dp".
        quarter: Quarter number (1–4).
        index: Zero-based index within that quarter.

    Returns:
        Formatted node ID string, e.g. "mat_g2_na_q3_5".
    """
    return f"mat_g{grade}_{branch}_q{quarter}_{index}"


def get_all_node_ids(
    grade: Optional[int] = None,
    branch: Optional[str] = None,
) -> List[str]:
    """
    Return all node IDs from NODE_TO_DNA, optionally filtered.

    Nodes are returned in the order they appear in NODE_TO_DNA (insertion
    order, which follows the knowledge-graph branch ordering).

    Args:
        grade: If given, only return nodes for this grade.
        branch: If given (e.g. "na", "mg", "dp"), only return nodes in
            that branch.

    Returns:
        List of node ID strings.
    """
    result: List[str] = []
    for node_id in NODE_TO_DNA:
        parts = node_id.split("_")
        # Expected format: mat_g{grade}_{branch}_q{quarter}_{index}
        if len(parts) < 5:
            continue
        node_grade_str = parts[1]   # "g1", "g2", "g3"
        node_branch = parts[2]      # "na", "mg", "dp"

        if grade is not None:
            if node_grade_str != f"g{grade}":
                continue
        if branch is not None:
            if node_branch != branch:
                continue

        result.append(node_id)

    return result
