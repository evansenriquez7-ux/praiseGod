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
        digit_match = None
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

        # "Add numbers by expressing addends as tens and ones (expanded
        # form)" (mat_g1_na_q2_4) / "...in expanded form" (mat_g2_na_q1_8):
        # task_type was left unbound, so rng.choice among
        # zero_identity/commutative/associative/expanded_form/counting_up/
        # plain gave expanded_form only a ~1-in-6 chance, and the plain
        # branch's own bare "what is X+Y?" never shows the decomposition
        # the competency names (blind review: comprehensive_coverage FAIL,
        # "the actual expanded-form addition procedure... never appears").
        if "expanded form" in text:
            bounds["task_type"] = "expanded_form"

        # "Illustrate by applying the following properties of addition, using
        # sums up to 20: the sum of zero and any number..., changing the order
        # of the addends..." (mat_g1_na_q1_8) and the grade-2 version that adds
        # "changing the grouping of the addends" (mat_g2_na_q1_10).
        #
        # addition.py implements zero_identity, commutative and associative
        # task types written for these two nodes specifically -- and nothing
        # ever bound task_type for them, so ordinary generation left it None
        # and every sample fell through to the plain "what is X+Y?" default.
        # The two nodes therefore rendered the same content as their
        # plain-addition siblings: mat_g2_na_q1_10 was byte-identical to
        # mat_g2_na_q1_9 on all 19 stratified seeds, and blind review found
        # that of mat_g1_na_q1_8's eighteen samples "only seed 613, 'Is 1 + 2
        # the same as 2 + 1?', actually demonstrates either named property"
        # while "not one of the eighteen items uses 0 as an addend".
        #
        # A sentinel string, not a tuple: a 2-tuple bound is always read as a
        # continuous (min, max) range. The DNA expands this sentinel into the
        # individual properties, cycling them by seed so one node's sample set
        # covers every property its own competency names.
        elif "properties of addition" in text:
            bounds["task_type"] = "properties"
            # Regrouping is not a dimension these competencies vary. "n + 0 = n"
            # cannot carry at all, and "Is a + b the same as b + a?" is answered
            # from the structure of the sentence, not by computing a sum. Left
            # unpinned, the difficulty machinery hands these tasks a regrouping
            # level they cannot express, and validate_matrix's discrete
            # integrity check correctly fails the item for not reflecting the
            # requested level.
            bounds["regrouping"] = "none"

        # "Illustrate addition of 2-digit and 1-digit numbers as 'counting
        # up' on the number line" (mat_g2_na_q1_7): task_type was left
        # unbound, so ordinary (non-variant-coverage) generation never set
        # it at all and every sample fell through to the plain "what is
        # X+Y?" default -- the competency's one named strategy, "counting
        # up," almost never appeared (blind review: "at most 1-2 samples,"
        # with the rest a severe multi-source leak from the co-mapped
        # `counting` DNA's own unrelated skip-counting/backward-counting
        elif "counting up" in text and "putting together" in text:
            bounds["task_type"] = "models_strategies"
            bounds["regrouping"] = "none"

        elif "counting up" in text and "number line" in text:
            bounds["task_type"] = "counting_up"
            # The competency names ONE 2-digit number AND one 1-digit
            # number specifically, not just "a sum up to 110" -- binding
            # only max_sum let both operands range freely up to 109, so
            # roughly half of samples used two 2-digit numbers (e.g.
            # "11 + 10", "93 + 13", some even producing 3-digit sums like
            # "93 + 13 = 106") and violated the competency's own explicit
            # operand-shape wording (blind review, most severe finding on
            # this node: "8/16 samples violate the '2-digit and 1-digit'
            # operand rule"). digit_match already parsed "2-digit and
            # 1-digit" above; thread that shape through explicitly.
            if digit_match:
                # A 2-tuple here would be silently treated as a continuous
                # axis range by the orchestrator's own bound-handling
                # (tuples of length 2 are reserved for that -- confirmed
                # live: the DNA received a bare int instead of a pair).
                # Use a "big_small" string sentinel instead, matching the
                # same convention multiplication.py's table-set sentinels
                # use for non-continuous discrete bounds.
                bounds["operand_digits"] = f"{digit_match.group(1)}_{digit_match.group(2)}"
                # The generic digit_match max_sum floor above is 3 -- but
                # the smallest possible genuine 2-digit + 1-digit sum is
                # 10 + 1 = 11, so scalar 0.0 (which maps to this floor)
                # made the operand-shape constraint infeasible outright
                # (confirmed live: "governed parameter maximum observed
                # value (None)" -- generate_params raised RuntimeError on
                # every scalar-0.0 sample since no pair could satisfy both
                # the shape and a max_sum below 11).
                big_digits = int(digit_match.group(1))
                small_digits = int(digit_match.group(2))
                min_feasible = (10 ** (big_digits - 1)) + (10 ** (small_digits - 1) if small_digits > 1 else 1)
                bounds["max_sum"] = (min_feasible, bounds["max_sum"][1])

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
        # "2-digit by 1-digit" states BOTH operand widths. Parsed before the
        # single-width idiom below, which would otherwise capture only the first
        # number and leave the subtrahend unbounded -- which is how mat_g2_na_q2_3
        # ("Illustrate subtraction of 2-digit by 1-digit") stayed completely
        # unbound and served "What is 930 - 408?".
        pair_match = re.search(r'(\d+)\s*-?\s*digits?\s+by\s+(\d+)\s*-?\s*digits?', text)
        digit_match = re.search(r'(?:up\s+to|to)\s+(\d+)\s*-?\s*digits?', text)
        if pair_match:
            # A stated width is a FLOOR as well as a ceiling: "2-digit" means 10..99,
            # not 1..99. These bounds are difficulty axes, so a floor of 1 let the
            # low end of the range serve "What is 2 - 1?" on a node whose competency
            # reads "2-digit by 1-digit" -- a blind reviewer caught it as the one
            # remaining width violation after the ceiling was bound. Mirror of the
            # subtrahend gap closed in the same file.
            _minuend_digits = int(pair_match.group(1))
            _subtrahend_digits = int(pair_match.group(2))
            bounds["max_minuend"] = (10 ** (_minuend_digits - 1),
                                     (10 ** _minuend_digits) - 1)
            # The (lo, hi) above is the difficulty AXIS range -- it caps the ceiling,
            # it does not floor the drawn operand, so the DNA could still draw a=2
            # under a ceiling of 25. These scalars are the operand floors themselves.
            bounds["min_minuend"] = 10 ** (_minuend_digits - 1)
            bounds["min_subtrahend"] = max(1, 10 ** (_subtrahend_digits - 1))
            # A one-digit subtrahend floors at 1, not 0: subtracting zero leaves the
            # minuend unchanged, and the same reviewer found 11 of 18 subtrahends
            # were 0 or 1, so "only 6 samples demand real counting back".
            bounds["max_subtrahend"] = (max(1, 10 ** (_subtrahend_digits - 1)),
                                        (10 ** _subtrahend_digits) - 1)
        elif digit_match:
            bounds["max_minuend"] = (1, (10 ** int(digit_match.group(1))) - 1)
        else:
            # Parse explicit operand bounds. A capture below 10 is a digit
            # count, an operand count or a step count -- never a minuend
            # ceiling in MATATAG K-3 phrasing -- so it is rejected rather
            # than believed, matching the `val >= 10` floor the generic
            # extraction below applies for exactly this reason. With no
            # parse the DNA's own per-grade _PARAM_BOUNDS governs, which is
            # what the comment above describes.
            # "less than N" and "up to N" are NOT the same ceiling. Treating them
            # alike bound max_minuend=(1, N) for both, so a competency reading
            # "both numbers are less than 20" served 20 itself: "Team A scored 20
            # ... and Team B scored 12" on mat_g1_na_q3_3, and 100 on
            # mat_g2_na_q2_5 whose sentence says less than 100. Blind reviewers
            # scored both FAIL on scale, quoting the operand back. Six of the seven
            # MATATAG competencies using this phrasing are subtraction nodes, so the
            # off-by-one was systematic rather than a one-node slip.
            match = re.search(r'(less than|up to)\s+(\d+)', text)
            if match and int(match.group(2)) >= 10:
                ceiling = int(match.group(2))
                if match.group(1) == "less than":
                    ceiling -= 1
                bounds["max_minuend"] = (1, ceiling)

        # "Estimate the difference of two numbers ..." (mat_g3_na_q2_5) names
        # a distinct skill from exact subtraction -- round both operands,
        # then subtract the rounded values -- that nothing in this DNA
        # produced before task_type="estimate" was added (see subtraction.py
        # generate_params).
        if "estimate" in text:
            bounds["task_type"] = "estimate"

        # "Subtract numbers by expressing minuends and subtrahends as tens
        # and ones (expanded form)" (mat_g1_na_q3_5) -- same text-match
        # rule as addition's identical binding above.
        elif "expanded form" in text:
            bounds["task_type"] = "expanded_form"

    # Multiplication: "products up to X"
    elif dna_name == "multiplication":
        match = re.search(r'products?\s+(?:up\s+to|of\s+up\s+to|to)\s+(\d+)', text)
        if match:
            max_val = int(match.group(1))
            bounds["max_product"] = (0, max_val)

        # Parse table level. "2_3_4_5_10_named" (distinct from the DNA's own
        # bare default "2_3_4_5_10", used when no node binds "table" at all,
        # e.g. mat_g2_na_q3_1's repeated-addition intro) tells
        # multiplication.py this competency explicitly names its tables --
        # see that DNA's _TABLE_SETS for why the distinction matters (0/1
        # dilution the bare-default path must still tolerate).
        if "6, 7, 8, and 9" in text or "6, 7, 8, 9" in text or "6, 7, 8, or 9" in text:
            bounds["table"] = "6_7_8_9"
        elif "2, 3, 4, 5, and 10" in text or "2, 3, 4, 5, 10" in text:
            bounds["table"] = "2_3_4_5_10_named"
        # "2- to 3-digit numbers by a 1-digit number, AND 2- to 4-digit
        # numbers by a number whose leading digit is the only non-zero
        # digit" (mat_g3_na_q3_2) is two genuinely different (multiplicand,
        # multiplier) shapes under one competency -- the DNA's default
        # table pool [0,1,2,3,4,5,10] only coincidentally contains "10",
        # so every sample collapsed onto that one x10 fact and neither a
        # true leading-digit multiplier (100, 2000, ...) nor a 4-digit
        # multiplicand ever appeared (blind review: "the only leading-
        # digit-only multiplier used is x10... no 4-digit multiplicand
        # ever appears"). New sentinel alternates between the two named
        # shapes per seed (see multiplication.py).
        elif "leading digit is the only non-zero digit" in text:
            bounds["table"] = "one_digit_or_leading_digit"

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
        # Both grade-2 repeated-addition competencies contain the phrase
        # "repeated addition", so a single match bound them identically and
        # they rendered word-for-word identical samples on all 11 stratified
        # seeds. They are not the same skill:
        #   mat_g2_na_q3_0 "Count the number of concrete objects in a group by
        #     repeated addition and create equal groups, using ... '5 groups of
        #     3'" -- the equal-groups model, stated in group language.
        #   mat_g2_na_q3_1 "Illustrate and write multiplication as repeated
        #     addition ..." -- writing the repeated sum itself.
        # Blind review scored both FAIL, q3_0 for "'5 groups of 3' and '5
        # threes' never appears in any of the eleven samples" and for being
        # "word-for-word identical to node mat_g2_na_q3_1's eleven samples".
        # "equal groups" appears only in q3_0's text, so it discriminates.
        if "equal groups" in text:
            bounds["task_type"] = "equal_groups"
        elif "repeated addition" in text:
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
            # floor.
            #
            # Revised ceiling (2026-08-06, same Ground Rule 5 correction):
            # the first pass left the ceiling at 1000 (the untouched grade
            # default), but multiplication.py's estimate branch filters
            # candidate (x, y) pairs on their ROUNDED product exceeding
            # max_product, and a 1000 ceiling forces the 3-digit factor
            # (x up to 999) toward its own low end whenever y rounds to
            # >=10 -- verified live: the largest factor ever drawn across
            # 16 review-packet samples was 98, so the competency's own
            # named "2- to 3-digit" factor range never actually reached 3
            # digits (blind review: comprehensive_coverage FAIL,
            # scale_appropriateness FAIL). Raised to the sibling G3
            # multiplication node's own ceiling (10 000) so a genuine
            # 3-digit-by-2-digit pair (e.g. rounded 300 x 30 = 9000) fits.
            bounds["max_product"] = (100, 10000)

        # Every other multiplication competency (table facts, word
        # problems, illustrate-as-repeated-addition, multi-digit
        # regrouping) left task_type completely unbound, so
        # _variant_coverage_candidates (judgment_packets.py) could pin
        # commutative/associative/distributive for ANY of them -- content
        # that only actually belongs to mat_g3_na_q3_1, the one node whose
        # competency text names these properties explicitly. Blind review
        # of mat_g2_na_q3_2/mat_g2_na_q3_3/mat_g3_na_q3_0/mat_g3_na_q3_4
        # flagged this as competency_alignment drift ("tests a different
        # competency (multiplication properties) rather than deepening
        # [table facts]"). "find_product" is the same inert sentinel
        # FORMATTER_VARIANT_SUPPORT already uses for "not one of the named
        # property task_types" -- it isn't a literal VARIANTS_BY_DNA value,
        # so binding it here excludes all three property values without
        # forcing any real behavior change on the default/table-fact path.
        elif "properties" not in text:
            bounds["task_type"] = "find_product"
        else:
            # mat_g3_na_q3_1 itself: left unbound, this node had no
            # auto-vary of its own (unlike most other DNAs' task_type
            # dimensions, which fall back to rng.choice when unbound) --
            # every render silently used multiplication.py's plain/default
            # path, rendering identical content to the sibling table-facts
            # node instead of the three properties (commutative,
            # associative, distributive) this node exists to demonstrate.
            # A list bound here is resolved by multiplication.py's own
            # rng.choice (see that file's identical-pattern comment).
            # "find_product" (the plain-facts sentinel) is included
            # alongside the three properties, not just them alone --
            # omitting it broke two things at once: cloze/true_false/
            # error_detect are restricted to ["find_product", "estimate"]
            # (they can't render a yes/no property claim, see that
            # restriction's own comment), so with no "find_product" in the
            # rotation those formatters had zero valid content at all
            # (§1C empty_execution_matrix); and the property branches
            # deliberately use small illustrative factors regardless of
            # max_product, so with no plain-facts path ever selected, nothing
            # ever exercised this node's true 90 ceiling (§1A-reach). The
            # competency's own "for the 6, 7, 8, 9 multiplication tables"
            # scope also implies genuine table facts belong alongside the
            # properties, not just illustrative small numbers.
            # "zero_identity" added (2026-08-07, Ground Rule 5 disclosure):
            # the competency's own wording names FIVE properties (identity,
            # zero, commutative, associative, distributive) but this list
            # previously bound only three of them -- "one multiplied by any
            # number is equal to the number; zero multiplied by any number
            # is zero" never had a dedicated task_type at all (blind
            # review: "identity property...entirely absent"). See
            # multiplication.py's new zero_identity branch.
            bounds["task_type"] = ["find_product", "commutative", "associative", "distributive", "zero_identity"]

    # Division: operand bound is enforced by the DNA's per-grade
    # _PARAM_BOUNDS[grade] (q_max: g2=50, g3=100). All MATATAG K-3
    # division LCs use operand-bound language ("2,3,4,5,10 tables" or
    # "2- to 3-digit numbers"), not result-bound language
    # ("quotients up to N"). The `max_quotient` axis was removed from
    # the catalog on 2026-07-01 — see axes_catalog.py header.
    elif dna_name == "division":
        # "2- to 3-digit numbers by 1-digit number WITHOUT remainder,
        # 2-digit numbers by 1-digit number WITH remainder, and 2- to
        # 4-digit numbers by 10, 100, and 1000" (mat_g3_na_q4_3) names
        # THREE distinct (dividend, divisor, remainder) shapes in one
        # competency -- checked first because it contains both "without
        # remainder" and "with remainder" as substrings, and the plain
        # if/elif below (matching whichever phrase it finds first) would
        # otherwise always resolve to "without remainder" and permanently
        # force remainder="none", silently dropping both the with-
        # remainder sub-case AND the power-of-ten sub-case entirely
        # (blind review: "None of 18 samples ever produce a remainder, and
        # none divide by 100 or 1000 -- two of the competency's three named
        # sub-cases are entirely absent").
        if "without remainder" in text and "with remainder" in text and "10,100" in text.replace(" ", ""):
            bounds["table"] = "one_digit_mixed_or_power_of_ten"

        # Parse table level
        elif "6, 7, 8, and 9" in text or "6, 7, 8, 9" in text or "6, 7, 8, or 9" in text:
            bounds["table"] = "6_7_8_9"
        elif "2, 3" in text and "5, and 10" in text:
            bounds["table"] = "2_3_4_5_10"
        elif "2, 3, 4, 5, and 10" in text or "2, 3, 4, 5, 10" in text:
            bounds["table"] = "2_3_4_5_10"

        # "Solve division problems involving 2- to 3-digit numbers by A
        # 1-DIGIT number, including problems involving money" (mat_g3_
        # na_q3_5... mat_g3_na_q4_5): the DNA's bare-default divisor pool
        # [2,3,4,5,10] includes 10, a 2-digit divisor -- directly violating
        # this competency's own explicit "1-digit number" scope (blind
        # review: "6 of 16 samples divide by 10 -- a 2-digit divisor --
        # directly violating 'by a 1-digit number'"). "6_7_8_9" already
        # excludes 10 but also excludes 2-5, which this competency does not
        # restrict away.
        elif "1-digit number" in text and "1- to 2-digit" not in text:
            bounds["table"] = "one_digit_2_9"

        # Parse remainder
        if "without remainder" in text:
            bounds["remainder"] = "none"
        elif "with remainder" in text:
            bounds["remainder"] = "with_remainder"

        # "Illustrate division through equal jumps on the number line and
        # AS INVERSE OF MULTIPLICATION" (mat_g3_na_q4_0): neither named
        # model has a meaningful reading when the division doesn't come
        # out even -- a remainder breaks the "inverse of multiplication"
        # framing entirely (19÷10 has no multiplication fact it inverts),
        # and this competency, unlike mat_g3_na_q4_3, never names a
        # remainder sub-case at all. The "remainder" axis was left
        # completely unbound here, so it auto-varied 50/50 with the DNA's
        # own default (blind review/harness: "19 ÷ 10 = ___" served with
        # correct_answer=1, silently dropping the remainder of 9).
        elif "inverse of multiplication" in text:
            bounds["remainder"] = "none"
        elif bounds.get("table"):
            # VARIANTS_BY_DNA["division"]["remainder"] = ["none","some"] has
            # no per-node scoping, so judgment_packets.py's variant-coverage
            # stratification and validate_matrix's §1C sweep can both
            # request remainder="with_remainder" against ANY division node,
            # including a plain "Divide numbers using the 6, 7, 8, and 9
            # multiplication tables" competency that never mentions
            # remainders at all. A table-facts competency is tied 1:1 to
            # its multiplication counterpart (42÷6=7 exactly, because
            # 6×7=42) -- there is no "with remainder" reading of it. A
            # formatter that renders only the quotient as "the answer"
            # (e.g. "15 ÷ 6 = 2") without surfacing the dropped remainder
            # then keys an incomplete statement as fully correct (blind
            # review of mat_g3_na_q4_1 seed 603: 15÷6 is 2 remainder 3, not
            # a clean 2). Binding remainder="none" here closes the leak the
            # same way "estimate"/"even_odd" are already closed elsewhere
            # in this function.
            bounds["remainder"] = "none"

        # "...modelling division as equal sharing or formation of equal
        # groups of objects, and repeated subtraction" (mat_g2_na_q3_5):
        # repeated subtraction is one of three named models, but nothing
        # in this DNA ever produced it (blind review: "repeated
        # subtraction... is modeled in zero of 18 samples"). Independent
        # of the remainder chain above -- this node binds no table, so
        # that chain never touches it either way.
        if "repeated subtraction" in text:
            bounds["task_type"] = "repeated_subtraction_or_default"

        # Parse missing structure
        if "missing number" in text or "missing term" in text:
            # divisor_unknown alone never produces a missing-DIVIDEND item
            # via the division DNA specifically (mat_g3_na_q4_2 is also
            # co-mapped with missing_number, whose OWN blank-position
            # rotation already covers it when THAT DNA gets picked, but
            # division's own renders never did -- blind review: "no
            # sample shows the 'dividend-missing' blank position").
            bounds["structure"] = "divisor_or_dividend_unknown"

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

        # "Distinguish even and odd numbers using division by 2"
        # (mat_g2_na_q3_8) is a classification skill, not a quotient-finding
        # one -- nothing else in this text-match ladder would ever bind it,
        # so it fell through to plain quotient facts every time.
        elif "even" in text and "odd" in text:
            bounds["task_type"] = "even_odd"

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
        if skip_10_100 and skip_2_5_10:
            # "Count by 2s, 5s, 10s, 20s, 50s, and 100s" (mat_g2_na_q1_3)
            # names all six -- the old logic always forced skip_interval=
            # "by_20_50_100" whenever ANY of 20/50/100 appeared, regardless
            # of whether 2/5/10 were ALSO named. skip_pool correctly held
            # all six values, but _select_skip's "by_20_50_100" branch
            # filters the pool down to `s >= 20` before choosing, so 2/5/10
            # sat in the pool yet could never actually be selected (blind
            # review: "Counting by 2s, 5s, and 10s... do not appear in any
            # of the 7 samples"). "by_all" isn't one of _select_skip's
            # three named levels, so it falls through to that function's
            # own unfiltered `rng.choice(pool)` default -- every named
            # increment reachable.
            bounds["skip_pool"] = skip_2_5_10 + skip_10_100
            bounds["skip_interval"] = "by_all"
        elif skip_10_100:
            bounds["skip_pool"] = skip_10_100
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

    # Ordinal numbers: no gate here at all previously -- this DNA's own
    # "ordinal_range" axis (axes_catalog.py) had no per-node ceiling to map
    # against, so every node fell to the axis's generic default_max=100
    # regardless of its own stated scope ("...up to 10th" /"...up to 20th"
    # /"...up to 100th"). Combined with a separate bug in ordinal_numbers.py
    # (it read the wrong profile keys and never varied magnitude at all,
    # coincidentally keeping every render low), fixing that bug without
    # this gate let a G1 "up to 10th" node render "49th"/"52nd" -- a real
    # curriculum-scope violation, not just a coverage gap.
    elif dna_name == "ordinal_numbers":
        match = re.search(r'up\s+to\s+(\d+)(?:st|nd|rd|th)', text)
        if match:
            bounds["ordinal_range"] = (1, int(match.group(1)))

    # "Describe and compare outcomes... using: equally likely, less/least
    # likely, more/most likely, certain, and impossible" (mat_g3_dp_q3_4)
    # names only comparative/superlative vocabulary plus certain/
    # impossible -- the DNA's "likely_unlikely" scenario_type produces
    # bare "likely"/"unlikely" (no "more/less" qualifier at all), which
    # isn't in this competency's own named term list and was diluting the
    # comparative content this competency actually needs (blind review:
    # 6/14 samples used bare likely/unlikely, "bleeding in from an
    # adjacent basic-probability LC"). Excludes that scenario_type via an
    # explicit 2-item allow-list (registry bounds accept lists, not just
    # single values -- same mechanism as missing_number's "tables" bound).
    elif dna_name == "probability_language" and "compare" in text and "less" in text and "more" in text:
        bounds["scenario_type"] = ["certain_impossible", "comparative"]

    # Area: bind task_type per node -- the DNA's own default
    # (task_type="find_area") silently governed every unbound node, so
    # "illustrate ... using square tile units" (mat_g3_mg_q1_0) and
    # "explore inductively the derivation of the formula[s]"
    # (mat_g3_mg_q1_1) rendered indistinguishably from the plain
    # "find the area" competency (mat_g3_mg_q1_2), and the symbolic
    # fallback question text didn't even show the shape's dimensions.
    # All four of this DNA's nodes are now bound. The last two were not, and
    # falling through left task_type unset entirely, so area.py's own
    # `profile.get("task_type", "find_area")` default governed both -- and
    # since mat_g3_mg_q1_2 and mat_g3_mg_q1_3 then differed only by `context`,
    # any formatter that ignores context rendered them identically. A blind
    # review caught it on seeds 55 and 500, where both nodes served the byte-
    # identical item "Look at the 6x25 array. How many squares are shaded in
    # all?" -- an item that satisfies neither competency, since it names no
    # sq. cm / sq. m unit and poses no problem to solve.
    elif dna_name == "area":
        if "derivation" in text or "derive" in text:
            bounds["task_type"] = "derive_formula"
        elif "illustrate" in text or "estimate" in text:
            bounds["task_type"] = "illustrate_tiles"
        # "Solve problems involving areas of squares and rectangles."
        # Problem-solving covers the inverse case the plain "find the areas"
        # competency does not name -- given an area and one side, find the
        # other. Both are wanted, varying per seed, so this is a sentinel
        # resolved by area.py's own seeded rng rather than a list: registry
        # bounds are computed once per node, so resolving the choice here would
        # freeze it to one value forever. Same pattern as calendar's
        # "elapsed_days_or_weeks" and pictographs' "read_or_compare".
        elif "solve problems" in text:
            bounds["task_type"] = "find_area_or_missing_dimension"
        # "Find the areas of squares and rectangles in sq. cm and sq. m."
        # Computing the area itself, and only that -- the inverse is beyond
        # what this competency's own wording asks for. The DNA already varies
        # square_cm/square_m per seed for this task_type, which is what the
        # competency's two named units require.
        elif "sq. cm" in text or "sq. m" in text:
            bounds["task_type"] = "find_area"

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

    # "Describe the duration of an event in terms of number of days and/or
    # weeks using a calendar" (mat_g2_mg_q4_0) has no matching default
    # either (task_type="read_day" reads a single date off the grid, not a
    # duration) -- the DNA already implements "elapsed_days"/
    # "elapsed_weeks" but nothing ever requested them. Sentinel resolved by
    # calendar.py's own seeded rng (registry bounds are computed once per
    # node, not per-seed, so resolving the choice here would freeze it to
    # one fixed value forever -- same pattern as pictographs'
    # "read_or_compare" sentinel).
    elif dna_name == "calendar" and "duration" in text and ("days" in text or "weeks" in text):
        bounds["task_type"] = "elapsed_days_or_weeks"

    # "Solve problems involving time (hour, half hour, quarter hour, days
    # in a week, and months in a year)" (mat_g1_mg_q4_4): time_reading (its
    # other co-mapped DNA) has no day/month concept, so this competency's
    # day/month sub-case never appeared at all (blind review: "Zero
    # samples touch 'days in a week' or 'months in a year'"). Matched on
    # "in a week"/"in a year" specifically, not "of the week"/"of the
    # year", to stay distinct from mat_g1_mg_q4_2's "days of the week and
    # months of the year in the correct order" (bound to "sequence" above).
    elif dna_name == "calendar" and "days in a week" in text and "months in a year" in text:
        bounds["task_type"] = "days_and_months"

    # "Solve problems involving elapsed time (minutes in an hour, hours in
    # a day, days in a week), including timetables" (mat_g2_mg_q4_2):
    # time_reading has no duration-between-two-times concept at all (every
    # other task_type reads/sets a single clock), so the co-mapped
    # `subtraction` DNA (a bare whole-number skill, no time/clock
    # awareness) filled the gap with off-topic content instead (blind
    # review: "9 of 17 samples are off-topic pictograph subtraction-
    # comparison word problems... zero connection to minutes/hours/days/
    # timetables").
    elif dna_name == "time_reading" and "elapsed time" in text:
        bounds["task_type"] = "elapsed_time"

    # "Read and write time in hours and minutes, WITH a.m. and p.m."
    # (mat_g2_mg_q4_1): the DNA's own default lets include_ampm auto-vary
    # 50/50, so roughly half the samples never showed a.m./p.m. at all --
    # fine for a node where it's optional, but this competency names it as
    # a defining, non-optional feature of the skill (blind review: "~38%
    # of samples omit a.m./p.m. entirely... the exact clause that
    # differentiates this Grade 2 competency from Grade 1").
    elif dna_name == "time_reading" and "with a.m. and p.m." in text:
        bounds["include_ampm"] = "yes"

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
            # "Identify ... line segments of EQUAL length" (mat_g3_mg_q1_6)
            # was bound to "compare", whose own generation loop explicitly
            # FORCES its two values apart (while val_b == val_a: redraw) --
            # structurally incapable of ever presenting an equal pair, the
            # entire point of this competency. Bind the dedicated task_type.
            bounds["task_type"] = "equal_length"
        elif "distance between two objects" in text:
            # "Measure the length of an object AND the distance between two
            # objects" (mat_g1_mg_q2_0) names two distinct sub-tasks; without
            # this, task_type always defaulted to read_measurement and
            # "distance between two objects" was never once exercised.
            # length_or_distance is a generate_params-level sentinel that
            # alternates between the two per seed rather than picking one.
            bounds["task_type"] = "length_or_distance"
        # "Measure and compare lengths of objects, in meters (m) or centimeters
        # (cm), and distance in meters" (mat_g2_mg_q2_0) was left UNBOUND, so the
        # DNA's read_measurement default governed and the node rendered the single
        # stem "Measure the object. Its length is ___ cm." on every seed -- neither
        # comparing anything nor ever mentioning distance, though its own sentence
        # names all three. An earlier fix in this file deferred it explicitly
        # ("out of scope for this fix"); it is in scope now. Sentinel, resolved per
        # seed in the DNA, because the competency names three sub-tasks and binding
        # any one of them would drop the other two.
        elif "measure and compare lengths" in text:
            bounds["task_type"] = "measure_compare_or_distance"
        elif "compare lengths and distances" in text:
            # mat_g1_mg_q2_1 matched none of the conditions above, so it
            # also silently defaulted to read_measurement and never once
            # compared two values. Matched on the specific phrase rather
            # than a bare "compare" substring: mat_g2_mg_q2_0 ("Measure
            # and compare lengths...") also contains "compare" but names a
            # dual measure-and-compare skill this single-value binding
            # would only half-cover, and it is out of scope for this fix.
            # "compare" alone only ever renders "Which is longer: X or Y?"
            # (object-length framing) -- the "distances" half of this
            # competency's own name was never once exercised. Alternate
            # between the length- and distance-framed comparisons per seed.
            bounds["task_type"] = "compare_length_or_distance"

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
        if "organize" in text or "into a table" in text:
            bounds["task_type"] = "organize_table"
        # "Present raw data, or data in tabular form, in a pictograph with a
        # scale, OR VICE VERSA" (mat_g2_dp_q3_0) names two directions and was
        # pinned to one. A blind reviewer: "All thirteen sampled items go the same
        # single direction, raw data into a pictograph; none tests the 'vice versa'
        # direction the competency text explicitly names."
        # The reverse direction already exists and is already wired -- task_type
        # "organize_table" renders "Fill in the chart with the correct counts."
        # against a displayed pictograph via the fill_in_table formatter. Nothing
        # needed building; the node was simply bound to half its own sentence.
        # Sentinel rather than a list, because registry bounds are computed once per
        # node and a choice made here would freeze to one direction forever.
        elif "present" in text and "vice versa" in text:
            bounds["task_type"] = "present_or_organize"
        elif "present" in text:
            bounds["task_type"] = "present_data"
        # "interpret" (mat_g2_dp_q3_1: "Interpret data in tabular form and
        # in a pictograph...") wants genuine data reading/comparison, not a
        # single frozen task_type -- unbound, this DNA's own default
        # ("read_value") never varies, so nothing but the plainest read
        # was ever demonstrated. Vary between reading a single category
        # and comparing two (pictographs.py's own "compare_two", which
        # genuinely interprets the dataset -- unlike the bare whole-number
        # comparing_ordering DNA this node used to be co-mapped to and was
        # removed from; see NODE_TO_DNA).
        elif "interpret" in text and ("tabular" in text or "in a table" in text):
            # "Interpret data IN TABULAR FORM AND in a pictograph..."
            # (mat_g2_dp_q3_1) names two displays to interpret, and only the
            # pictograph existed: fill_in_table could blank a table out but not
            # show a filled one, so "read the table" was a real capability gap,
            # not a routing bug. A blind reviewer: "Every one of the twelve
            # sampled items opens with 'Look at the picture graph'; none
            # references reading a table." The read mode of fill_in_table is new
            # in the same commit as this binding; this sentinel is what reaches it.
            bounds["task_type"] = "tabular_and_pictograph"
        elif "interpret" in text:
            # Sentinel resolved per-seed inside pictographs.py's own
            # generate_params (registry bounds are computed once per node,
            # not per render, so a random.choice() here would freeze to one
            # fixed value for every sample instead of genuinely varying).
            bounds["task_type"] = "read_or_compare"
        # "collect" ("Collect data ... through a simple interview",
        # mat_g1_dp_q3_0) previously matched the "organize" branch above,
        # routing it to task_type="organize_table" -- the exact same
        # task_type mat_g1_dp_q3_3 uses for its own, genuinely different
        # "organize data into a table" competency, so the two nodes
        # rendered byte-identical content (blind review). This DNA has no
        # interview-simulation task_type at all (a real, disclosed gap,
        # not a routing bug) -- leaving it unbound at least stops the
        # duplicate-content collision with mat_g1_dp_q3_3.
        # "with or without scale" (mat_g2_dp_q3_1) contains "without scale"
        # as a literal substring, so this used to match and force
        # scale_type="no_scale" for a competency that explicitly wants
        # BOTH to vary -- same substring-collision class as "with and
        # without regrouping"/"without regrouping" elsewhere in this file.
        if ("without a scale" in text or "without scale" in text) and "with or without" not in text:
            bounds["scale_type"] = "no_scale"
        elif "with or without" in text:
            bounds["scale_type"] = "with_or_without_scale"
        elif "with a scale" in text or "with scale" in text or "using a scale" in text:
            bounds["scale_type"] = ["scale_2", "scale_5", "scale_10"]

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
        elif "increasing" in text and "decreasing" in text and "repetitions" in text:
            # "...numbers, letters and rhythmic properties, visual elements
            # in arts, and repetitions" (mat_g2_na_q2_8) names "repetitions"
            # as one of its own sub-cases alongside increasing/decreasing --
            # checked before the plain increasing_or_decreasing branch below
            # so this node also reaches the "repeating" pattern_type (the
            # only one that can use letters -- see patterns.py's identical
            # comment).
            bounds["pattern_type"] = "increasing_decreasing_or_repeating"
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
        elif "compose and decompose" in text:
            # "Compose and decompose numbers up to 10... (e.g., 5 is 5 and
            # 0; 4 and 1; 3 and 2...)" (mat_g1_na_q1_6) names no operation
            # word at all, so it fell through to the DNA's own unbound
            # default (op_axis = rng.choice(allowed_ops), 50/50 addition/
            # subtraction) -- but composing/decomposing a whole into two
            # parts is inherently additive (X = A + B); subtraction facts
            # like "4 - 3 = ___" don't express decomposition at all (blind
            # review: "three samples use subtraction... that belong to the
            # later mat_g1_na_q3_1 competency").
            bounds["operation"] = "addition"

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
        elif "pictorial models" in text or "block or bar" in text or "materials and representations" in text or "concrete and pictorial" in text:
            # For model representation nodes, place_value provides base-10 block models
            bounds["task_type"] = "identify_value"

    # Number reading: "numerals/numbers up to X"
    elif dna_name == "number_reading":
        match = re.search(r'(?:numerals?|numbers?)\s+(?:up\s+to|to)\s+([\d\s]+)', text)
        if match:
            max_val = int(match.group(1).replace(" ", "").strip())
            bounds["range"] = (10, max_val)

        if "pictorial models" in text or "block or bar" in text or "materials and representations" in text or "concrete and pictorial" in text:
            bounds["task_type"] = "model_representation"
        else:
            bounds["task_type"] = "read_and_write"

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

    # "Compare different denominations of peso coins..." (mat_g1_na_q4_5,
    # mat_g2_na_q2_1) -- money_peso.py already implements a real
    # operation="compare" (asks "which has a greater value", built from
    # two distinct coin/bill descriptions), but nothing ever bound it, so
    # these nodes always defaulted to "add_amounts" and never once posed
    # a comparison (blind review: money samples computed totals/change,
    # never compared two denominations).
    elif dna_name == "money_peso" and "compare" in text:
        bounds["operation"] = "compare"

    # "Recognize coins... and bills... and their notations" (mat_g1_na_q4_3)
    # is a naming/notation competency, distinct from its sibling
    # mat_g1_na_q4_4's "Determine the value of a number of bills/coins"
    # (a summing competency) -- both left "operation" unbound, so both
    # defaulted to the same "add_amounts" and rendered text-for-text
    # identical packets (blind review: competency_alignment FAIL,
    # "word-for-word identical to node mat_g1_na_q4_4's samples"). Money's
    # own "read_write" operation (numeral<->words<->symbol notation) is
    # the closest existing match for the "notations" half of this
    # competency; recognizing a coin/bill purely by physical appearance
    # (not notation) remains a separate, undisclosed gap this doesn't
    # cover.
    elif dna_name == "money_peso" and "recognize" in text and "notation" in text:
        bounds["operation"] = "read_write"

    # "Read and write money in words and using: Philippine currency
    # symbols (₱ and PhP)... and the centavo sign" (mat_g3_na_q2_0):
    # operation was left completely unbound, so it defaulted to whatever
    # this DNA's own generate_params() falls back to (not "read_write" --
    # the one operation that actually covers words/PhP/centavo notation),
    # and the co-mapped `number_reading` DNA (no money concept at all)
    # filled a large share of samples with plain numeral content instead
    # (blind review: "9 of 17 samples... zero money content... no ₱
    # symbol, no pesos, nothing"; "the centavo sign never appears").
    elif dna_name == "money_peso" and "read and write" in text and "money" in text:
        bounds["operation"] = "read_write"

    # "Determine the value of a number of bills and/or a number of coins"
    # (mat_g1_na_q4_4) and "Determine and write the value of a number of bills,
    # or a number of coins, or a combination ..." (mat_g2_na_q2_0). Both fell
    # through every branch above with `operation` unbound, so nothing pinned
    # the task to determining a value and variant coverage could serve
    # change-making instead -- blind review on mat_g2_na_q2_0 flagged seed 606,
    # "You paid P1 for an item that costs P0. How much change do you receive?",
    # as "change-making with a nonsensical zero-peso item price rather than the
    # competency's own task of determining the value of a given set".
    elif dna_name == "money_peso" and "determine" in text and "value" in text:
        bounds["operation"] = "add_amounts"

        # mat_g2_na_q2_0's parenthetical enumerates the denomination sub-cases
        # it wants: "(centavo coins only, peso coins only, peso bills only,
        # combined peso coins and peso bills)". money_peso.py already supports
        # coins_only / bills_only / mixed via a `denomination_type` key, but
        # nothing ever bound it, so every node used the "mixed" default and
        # blind review found "peso-bills-only shows up in just one item".
        # A sentinel, not a list: the DNA rotates the sub-cases by seed so one
        # node's sample set covers each of them.
        #
        # NOT handled here: "centavo coins only". money_peso.py stores centavo
        # denominations as centavo integers (_DENOMS_G2_CENTAVOS = [25, 50],
        # i.e. P0.25 and P0.50) while the pile/total pipeline is peso-integer,
        # so dropping them into denom_pool would total them as pesos and label
        # them wrong. That constant is currently referenced nowhere at all.
        # Serving centavo piles needs unit-aware render text in the money
        # formatters, which is its own change.
        if "peso bills only" in text:
            bounds["denomination_type"] = "peso_sub_cases"

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

        # "Represent and identify..." (mat_g2_na_q4_0/_3) vs "Read and
        # write... in fraction notation" (mat_g2_na_q4_1/_4): both pairs
        # share the same identify_name operation and produce the exact
        # same numerator/denominator content, so nothing distinguished
        # which formatter rendered them -- most samples ended up byte-
        # identical between the two sibling nodes regardless of which one
        # explicitly names a visual model vs pure notation (blind review:
        # "the entire packet is byte-identical to sibling node q4_1",
        # "byte-identical duplicate of q4_3's packet"). New axis restricts
        # fraction_shade/fraction_model_read to the "represent" nodes and
        # mcq/cloze to the "read and write in notation" nodes (see
        # FORMATTER_VARIANT_SUPPORT["fractions"] in compatibility.py).
        if "represent and identify" in text:
            bounds["fraction_task_mode"] = "model"
        elif "read and write" in text and "notation" in text:
            bounds["fraction_task_mode"] = "notation"
        elif "equal to one" in text or "greater than one" in text:
            # "Represent fractions that are equal to one and greater than
            # one using models" (mat_g3_na_q4_6) matched neither "unit
            # fraction" nor "similar fraction", so fraction_type stayed
            # unbound and the DNA's own default ("unit_fraction", always
            # numerator=1 over a denominator >=2, i.e. always <1) governed
            # -- every sample rendered a proper fraction strictly less
            # than one, the opposite of what this competency names (blind
            # review: "the target fraction... is a proper fraction
            # strictly less than one" for all 8 samples).
            bounds["fraction_type"] = "improper"
            # "Represent fractions... using models" names no arithmetic
            # operation at all, but leaving "operation" unbound left it
            # vulnerable to VARIANTS_BY_DNA["fractions"]["operation"] =
            # ["add","subtract","add_subtract"] (declared for the sibling
            # add/subtract node, mat_g3_na_q4_7, with no per-node scoping)
            # -- judgment_packets.py's variant-coverage stratification
            # probes those values against every fractions node regardless,
            # so a plain "represent this model" competency got fraction-
            # addition items mixed in (blind review: "Seeds 603, 604, and
            # 605 are fraction-addition problems... competency leakage
            # from node 7").
            bounds["operation"] = "identify_name"
        if False and "order" in text:
            # fractions.py has a working "order" operation (draws N
            # distinct unit/similar fractions, sorts them correctly using
            # real fraction values) and fmt_ordering.py was fixed
            # alongside it to compare "N/D" strings numerically instead of
            # lexicographically ("1/10" < "1/2" as plain strings). BUT
            # validate_matrix.py's own §1E answer_key_integrity check
            # independently recomputes "correctly sorted" via a bare
            # `sorted(items, reverse=...)` with no fraction-aware key, so
            # it disagrees with the DNA's genuinely correct answer for
            # UNIT fractions (varying denominators: ascending fraction
            # VALUE is denominator-DEScending, which is lex-ascending-
            # reversed -- confirmed live, "1/2,1/3,1/4,1/5" numeric-
            # ascending sorts lexicographically to itself only by
            # accident of a 2026-08-10 attempt; the general case
            # disagrees, e.g. served ['1/6','1/5','1/4','1/3']
            # (ascending) vs checker-expected ['1/3','1/4','1/5','1/6']).
            #
            # 2026-08-10: tried scoping this to SIMILAR fractions only
            # (mat_g2_na_q4_5), where same-denominator + single-digit
            # numerator DOES make lex order == numeric order by
            # construction. That is NOT enough: declaring "ordering" as a
            # compatible formatter for the fractions DNA at all exposes
            # operation="order" to validate_matrix's §1C exhaustive sweep
            # against EVERY fractions node regardless of registry
            # scoping (the orchestrator's formatter-forcing path injects
            # operation=rng.choice(["order"]) whenever "ordering" is
            # force-tested) -- confirmed live: forcing it onto
            # mat_g2_na_q4_0/_1 (both fraction_type="unit_fraction") hit
            # the exact lex-mismatch above. Reverted; validate_matrix.py
            # is read-only for generator work (CLAUDE.md) and there is no
            # way to expose "order" to only the nodes where it's safe.
            # mat_g2_na_q4_2/mat_g2_na_q4_5 stay on their pre-existing
            # co-mapped comparing_ordering DNA fallback -- see
            # NODE_TO_DNA's comment there.
            bounds["operation"] = "order"
        elif "compare" in text:
            # "Compare 1/2 and 1/4 using models" (mat_g1_na_q4_1) is also
            # co-mapped to comparing_ordering, a bare whole-number DNA that
            # cannot express a fraction comparison at all -- whenever the
            # orchestrator picked it as the active DNA, the node rendered
            # unrelated whole-number comparisons instead (blind review).
            # Bind operation="compare" so this node's own fractions DNA
            # render reliably produces the comparison itself.
            bounds["operation"] = "compare"

        # "Count halves and quarters" (mat_g1_na_q4_2) is a counting-
        # SEQUENCE skill, not identify/compare/order/add -- the co-mapped
        # `counting` DNA has no fraction concept whatsoever and rendered
        # whole-number skip-counting instead (blind review: "10/17
        # samples (59%) are plain whole-number counting with zero
        # fraction content -- this is active off-topic substitution, not
        # just an absent nice-to-have"). fractions.py's new
        # "count_sequence" operation counts by a fixed unit fraction
        # (1/2 or 1/4) the way counting.py counts by a fixed whole-number
        # skip interval.
        if text.strip().startswith("count") and ("half" in text or "quarter" in text):
            bounds["operation"] = "count_sequence"

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
                # Ground-truth correction (Ground Rule 5, 2026-08-07): a
                # (0, max(tables)*10) range starts the log-scale
                # interpolation (orchestrator.py's continuous-axis mapping)
                # from a floor of 0/1, but every genuine fact from a
                # named-tables competency already has a hard floor of
                # min(tables), and the log scale compresses so heavily
                # toward its own low end that the DEFAULT difficulty scalar
                # (0.5, used whenever no difficulty_profile is supplied)
                # resolved to a ceiling of just 13 for the 6-9 set -- below
                # which only b=6 could pair with a=2 at all; 7/8/9 could
                # only ever appear as a degenerate a=1 fact, and even that
                # was thinned to a single deterministic slot. Verified
                # live: 200 raw seeds against mat_g3_na_q3_0 (unbound
                # difficulty_profile) collapsed to exactly 2 distinct (a,b)
                # pairs, (2,6) and (1,6) -- 7's table never appeared once
                # (blind review: comprehensive_coverage FAIL). The
                # identical shape hit the "2,3,4,5,10" set: table 10
                # appeared 0/499 times, table 2 dominated ~50%. Flooring at
                # 2x the highest named table gives every table room for at
                # least an a=2 fact even at the interpolation's own low end.
                bounds["max_product"] = (2 * max(tables), max(tables) * 10)
            else:
                bounds["max_product"] = (0, grade_defaults["max_product"])
        elif "max_total" in grade_defaults and dna_name == "money_peso":
            bounds["max_total"] = (1, grade_defaults["max_total"])

    # Extract regrouping booleans. "with and/or without regrouping" must be
    # checked before "without regrouping" -- it contains "without
    # regrouping" as a literal substring, so the more specific case was
    # unreachable and every "with and without regrouping" competency (e.g.
    # mat_g3_na_q2_1: "sums up to 10 000, with and without regrouping")
    # was silently bound regrouping=False, permanently hiding the
    # "with regrouping" half the competency explicitly names. "with OR
    # without" (mat_g2_na_q1_9: "sums up to 1000, with or without
    # regrouping") is the identical two-sided requirement phrased with
    # "or" instead of "and" -- the original fix only matched the "and"
    # wording, so this variant still silently forced regrouping=False
    # (blind review: comprehensive_coverage FAIL, "'with regrouping' ...
    # only the 'without regrouping' case is ever generated").
    if "with and without regrouping" in text or "with or without regrouping" in text:
        # Don't strictly bound it, let the catalog dictate options
        pass
    elif "without regrouping" in text:
        bounds["regrouping"] = False
    elif "with regrouping" in text:
        bounds["regrouping"] = True
    elif dna_name == "fractions" and ("add" in text or "subtract" in text or "sum" in text or "difference" in text):
        bounds["operation"] = "add_subtract"

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
    # counting removed (Ground Rule 2, 2026-08-07): competency is
    # "Recognize and represent numbers... using a variety of concrete and
    # pictorial models (e.g., number line, block or bar models, and
    # numerals)" -- a representation skill, not a counting-sequence one.
    # The co-mapped bare counting DNA rendered unrelated skip-count/
    # next-number content instead (blind review: "5/17 samples... test
    # sequence fluency, an axis unrelated to represent numbers using
    # models"). number_reading.py now covers numerals (numeral_to_word/
    # word_to_numeral), block/bar models (identify_value ->
    # place_value_blocks), and number_line is already wired too.
    "mat_g1_na_q1_2": ["number_reading"],
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
    # place_value removed (Ground Rule 2, 2026-08-06): the competency verb is
    # "Add" (expanded-form addition), but co-mapping place_value let the
    # orchestrator's rng.choice(valid_dnas) render bare "What place is the
    # digit X in?" facts with zero addition content roughly half the time
    # (blind review of mat_g1_na_q2_4: comprehensive_coverage FAIL, "not one
    # of the 17 samples shows the actual expanded-form addition procedure").
    "mat_g1_na_q2_4": ["addition"],
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
    # place_value removed (Ground Rule 2, 2026-08-06): competency verb is
    # "Subtract" (expanded-form subtraction) -- subtraction alone now
    # carries this (task_type bound to expanded_form above). place_value
    # had no restriction, so rng.choice(valid_dnas) let bare "what place is
    # digit X" facts and even an unrelated addition "sum" spine collision
    # render with zero subtraction content (blind review: competency_
    # fulfillment/comprehensive_coverage FAIL, competency_alignment FAIL
    # "seed 101... asks for a sum -- addition, not subtraction").
    "mat_g1_na_q3_5": ["subtraction"],
    "mat_g1_na_q3_6": ["patterns"],
    "mat_g1_na_q3_7": ["patterns"],

    # Q4: Fractions (1/2, 1/4), money (coins/bills to ₱100)
    "mat_g1_na_q4_0": ["fractions"],
    # "comparing_ordering" removed 2026-08-05 (Ground Rule 2): "Compare 1/2
    # and 1/4 using models" cannot be expressed by a bare whole-number
    # comparison DNA at all -- whenever the orchestrator picked it as the
    # active DNA, the node rendered an unrelated whole-number comparison
    # (blind review). fractions.py's own operation="compare" now covers
    # this competency directly.
    "mat_g1_na_q4_1": ["fractions"],
    # counting removed (Ground Rule 2, 2026-08-07): "Count halves and
    # quarters" is a fraction-counting-sequence skill; the co-mapped bare
    # whole-number counting DNA has no fraction concept and rendered
    # off-topic whole-number sequences (blind review: "active off-topic
    # substitution, not just an absent nice-to-have"). fractions.py's new
    # "count_sequence" operation (registry-bound above) covers it
    # directly now.
    "mat_g1_na_q4_2": ["fractions"],
    "mat_g1_na_q4_3": ["money_peso"],
    "mat_g1_na_q4_4": ["money_peso"],
    # "comparing_ordering" removed 2026-08-05 (Ground Rule 2): a bare
    # whole-number comparison DNA cannot express "which coin/bill is
    # worth more" -- money_peso.py's own operation="compare" (registry.py
    # money_peso block) now covers this competency directly.
    "mat_g1_na_q4_5": ["money_peso"],
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
    # "calendar" added (2026-08-10): "days in a week, and months in a
    # year" is one of this competency's three named sub-cases, but
    # time_reading has no day/month concept at all -- co-map calendar
    # (task_type bound to the new "days_and_months" sentinel above) so
    # that sub-case actually gets generated instead of never appearing
    # (blind review: "Zero samples touch 'days in a week' or 'months in a
    # year,' both explicitly named in the competency").
    "mat_g1_mg_q4_4": ["time_reading", "calendar"],

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
    # counting removed (Ground Rule 2, 2026-08-07): identical reasoning to
    # mat_g1_na_q1_2 above.
    "mat_g2_na_q1_2":  ["number_reading"],
    "mat_g2_na_q1_3":  ["counting"],
    "mat_g2_na_q1_4":  ["comparing_ordering"],
    "mat_g2_na_q1_5":  ["ordinal_numbers"],
    "mat_g2_na_q1_6":  ["place_value"],
    # counting removed (Ground Rule 2, 2026-08-07): competency is
    # "Illustrate addition of 2-digit and 1-digit numbers as 'counting up'
    # on the number line" -- a specific ADDITION strategy, not a general
    # counting/skip-counting skill. The co-mapped bare counting DNA has no
    # concept of "counting up as an addition strategy" at all; it just
    # rendered unrelated skip-counting and backward-counting sequences
    # (blind review: "severe multi-source content leak... a counting-
    # BACKWARD item, which is conceptually the inverse of this competency
    # and belongs to subtraction"). addition.py's own task_type=
    # "counting_up" (now bound above) expresses the real skill directly.
    "mat_g2_na_q1_7":  ["addition"],
    # place_value removed (Ground Rule 2, 2026-08-06): same root cause as
    # mat_g1_na_q2_4 -- competency is "Add ... in expanded form", but
    # co-mapping place_value let bare digit-position facts (up to 4-digit
    # numbers, ~9x over the competency's own 1000 ceiling) render instead of
    # expanded-form addition (blind review: comprehensive_coverage FAIL,
    # scale_appropriateness FAIL).
    "mat_g2_na_q1_8":  ["addition"],
    "mat_g2_na_q1_9":  ["addition"],
    "mat_g2_na_q1_10": ["addition"],

    # Q2: Money (to ₱1000), addition problems, subtraction (to 1000),
    #     patterns (increasing/decreasing)
    "mat_g2_na_q2_0": ["money_peso"],
    # "comparing_ordering" removed 2026-08-05 (Ground Rule 2), same
    # reasoning as mat_g1_na_q4_5.
    "mat_g2_na_q2_1": ["money_peso"],
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
    # counting removed (Ground Rule 2, 2026-08-06): competency is "Count
    # objects in a group by repeated addition and create equal groups,
    # using language such as '5 groups of 3'" -- multiplication alone
    # already carries this (task_type bound to repeated_addition above).
    # counting had no restriction at all, so rng.choice(valid_dnas) let
    # generic skip-counting/backward-counting sequences ("994, 995...")
    # render with zero equal-groups framing, especially at the seed>=500
    # max-difficulty tier where counting's much larger range (10-1000 vs
    # multiplication's 0-100 max_product) dominated (blind review:
    # competency_alignment FAIL, "content shifts entirely to skip-counting
    # near 994-995... rather than deepening equal-groups reasoning").
    "mat_g2_na_q3_0": ["multiplication"],
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
    # comparing_ordering removed (Ground Rule 2, 2026-08-06): competency is
    # "Distinguish even and odd numbers using division by 2" -- division
    # alone now carries this (task_type bound to even_odd above).
    # comparing_ordering had no restriction, so rng.choice(valid_dnas) let
    # bare whole-number comparisons ("307 ___ 270") render with zero
    # even/odd content (blind review: comprehensive_coverage FAIL, "the
    # central named sub-case... never appears in any of the 19 samples").
    "mat_g2_na_q3_8": ["division"],
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
    # comparing_ordering kept for now (see "order" binding's `False and`
    # guard above): fractions.py's "order" operation is written and
    # correct, but disabled pending a fraction-aware sort key in
    # validate_matrix.py's §1E check, which is read-only for generator
    # work. Reverting this mapping too would leave these two nodes with
    # NO ordering content at all rather than the pre-existing (off-topic
    # but at least present) comparing_ordering fallback.
    "mat_g2_na_q4_2": ["fractions", "comparing_ordering"],
    "mat_g2_na_q4_3": ["fractions"],
    "mat_g2_na_q4_4": ["fractions"],
    # comparing_ordering kept for now: identical reasoning to
    # mat_g2_na_q4_2 above, for "Order similar fractions...".
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
    # addition removed (Ground Rule 2, 2026-08-06): length_measurement
    # already self-narrates its own word problems via its "question" field
    # (its blank_target="answer" never matches a spine's required
    # blank_target, so it never reaches spine selection at all). When
    # addition was picked instead, the only spines whose required_concepts
    # matched this node's own domain (meas_object/meas_compare_lengths) use
    # {len_a}/{len_b}/{unit} slots that no DNA populates -- spine.render
    # KeyErrors and silently falls back to a bare, context-free arithmetic
    # fact ("What is 390 + 312?"), losing all length/distance framing
    # (blind review: comprehensive_coverage FAIL, "zero mention of length,
    # distance, or centimeters"; identical content to unrelated sibling
    # mat_g2_mg_q4_6 at the same seeds, confirming the addition DNA carried
    # no node-specific framing at all).
    "mat_g2_mg_q2_3": ["length_measurement"],

    # Q4: Duration/elapsed time, time in hours+minutes,
    #     straight vs curved lines, perimeter
    # time_reading removed (Ground Rule 2, 2026-08-06): competency is
    # "Describe the duration of an event in ... days and/or weeks using a
    # calendar" -- calendar alone now carries this (task_type bound to
    # elapsed_days_or_weeks above). time_reading had no restriction, so
    # rng.choice(valid_dnas) let plain clock-reading/-setting content
    # render with zero calendar-duration content (blind review:
    # competency_fulfillment/comprehensive_coverage/variant_
    # comprehensiveness/competency_alignment/scale_appropriateness all
    # FAIL, "not one of the 6 samples computes a duration in days or
    # weeks").
    "mat_g2_mg_q4_0": ["calendar"],
    "mat_g2_mg_q4_1": ["time_reading"],
    # "subtraction" removed (Ground Rule 2, 2026-08-10): competency is
    # "Solve problems involving elapsed time... including timetables" --
    # subtraction has no time/clock awareness at all; when picked it
    # rendered off-topic pictograph-themed word problems with zero
    # connection to time (blind review: "9 of 17 samples... zero
    # connection to minutes/hours/days/timetables"). time_reading now
    # implements a real elapsed_time task_type (registry-bound above)
    # instead of relying on a mismatched co-mapped DNA.
    "mat_g2_mg_q4_2": ["time_reading"],
    "mat_g2_mg_q4_3": ["geometric_lines"],
    "mat_g2_mg_q4_4": ["perimeter", "length_measurement"],
    "mat_g2_mg_q4_5": ["perimeter"],
    # addition removed (Ground Rule 2, 2026-08-06): same root cause as
    # mat_g2_mg_q2_3 -- perimeter already self-narrates via
    # base_generator._build_symbolic_question's dedicated "fencing" template
    # (blank_target="answer" never matches any spine, so it never needs one).
    # addition being co-mapped only let rng.choice(valid_dnas) render bare
    # facts with zero perimeter content (blind review: comprehensive_coverage
    # FAIL, "not one triangle... rectangular-garden fencing" template only;
    # off-domain seeds identical to unrelated sibling mat_g2_mg_q2_3).
    "mat_g2_mg_q4_6": ["perimeter"],

    # ────────────────────────────────────────────────────────────────────────
    # GRADE 2 — Data & Probability
    # ────────────────────────────────────────────────────────────────────────

    "mat_g2_dp_q3_0": ["pictographs"],
    # "comparing_ordering" removed 2026-08-05 (Ground Rule 2): "Interpret
    # data in tabular form and in a pictograph" cannot be expressed by a
    # bare whole-number comparison DNA -- whenever the orchestrator picked
    # it as the active DNA, the node rendered unrelated large-magnitude
    # number comparisons (blind review: 9 of 16 samples). pictographs.py's
    # own "compare_two" task_type genuinely interprets the dataset instead.
    "mat_g2_dp_q3_1": ["pictographs"],

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
    # "number_reading" removed (Ground Rule 2, 2026-08-10): competency is
    # "Read and write money in words and using: Philippine currency
    # symbols (₱ and PhP)... and the centavo sign" -- number_reading has
    # no money/currency concept at all; when picked it rendered plain
    # numeral content with zero peso context (blind review: "9 of 17
    # samples... zero money content -- no ₱ symbol, no pesos, nothing").
    # money_peso's own operation="read_write" (registry-bound above) now
    # covers words/symbols/centavo notation directly.
    "mat_g3_na_q2_0": ["money_peso"],
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
