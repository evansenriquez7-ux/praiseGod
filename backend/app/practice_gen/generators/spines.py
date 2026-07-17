"""
Practice Generation — Story Spines
====================================

Defines all reusable narrative templates (Spine instances) for the
context generator.  A Spine wraps a mathematical problem inside a
brief, grade-appropriate story so the numbers feel purposeful.

Slot keys used in templates (filled by interest.get_interest_slots):
    {actor}    — student-relatable character name (e.g. "Maria", "Coach Ben")
    {objects}  — countable theme objects (e.g. "stickers", "basketballs")
    {place}    — setting (e.g. "classroom", "barangay court")
    {item1}    — secondary theme item (e.g. "pencil")
    {item2}    — tertiary theme item (e.g. "eraser")

Value keys used in templates (filled by generate_params output):
    {a}        — first operand / starting quantity
    {b}        — second operand / change quantity
    {result}   — computed answer (correct answer for "result_unknown" structure)
    {n}        — generic multiplier / group size
    {groups}   — number of groups
    {total}    — total result for multiplication/division contexts
    {price}    — unit price (money context)
    {amount}   — money total (money context)
    {change}   — change returned (money context)
    {paid}     — amount paid (money context)
    {len_a}    — first length (measurement context)
    {len_b}    — second length (measurement context)
    {unit}     — measurement unit string (cm, m, etc.)

Each Spine is gated on:
  1. required_concepts ⊆ node.cumulative_concepts  (math gate)
  2. grade_band[0] ≤ grade ≤ grade_band[1]          (language gate)

blank_target matches a key in the QuestionContext.values dict —
it identifies which value is the unknown (the "blank" in the problem).

Export
------
ALL_SPINES : List[Spine]
select_spine : callable
"""

from __future__ import annotations

import random
from typing import List, Optional, Set

from ..dna.base import Spine


# ═══════════════════════════════════════════════════════════════════════════════
# ADDITION SPINES — gain / combination / counting up / putting together
# ═══════════════════════════════════════════════════════════════════════════════

# Aligned with competency: "describes addition as 'counting up' and 'putting together'"

_ADD_COUNTING_UP = Spine(
    id="add_counting_up",
    template=(
        "Start at {a}. Count up {b} more. "
        "What number do you land on?"
    ),
    required_concepts={"addition"},
    blank_target="result",
    grade_band=(1, 2),
)

_ADD_COUNTING_UP_STORY = Spine(
    id="add_counting_up_story",
    template=(
        "{actor} is on step {a}. "
        "{actor} climbs up {b} more steps. "
        "What step is {actor} on now?"
    ),
    required_concepts={"addition"},
    blank_target="result",
    grade_band=(1, 2),
)

_ADD_PUTTING_TOGETHER = Spine(
    id="add_putting_together",
    template=(
        "One basket has {a} {objects}. Another basket has {b} {objects}. "
        "If you put all the {objects} together, how many {objects} are there?"
    ),
    required_concepts={"addition"},
    blank_target="result",
    grade_band=(1, 3),
)

_ADD_PUT_TOGETHER_NAMES = Spine(
    id="add_putting_together_names",
    template=(
        "{actor} has {a} {objects}. A friend has {b} {objects}. "
        "If they put all their {objects} together, how many {objects} do they have in all?"
    ),
    required_concepts={"addition"},
    blank_target="result",
    grade_band=(1, 3),
)

_ADD_FOUND = Spine(
    id="add_found",
    template=(
        "{actor} found {a} {objects}. A friend found {b} {objects}. "
        "If they put all their {objects} together, how many {objects} do they have altogether?"
    ),
    required_concepts={"addition"},
    blank_target="result",
    grade_band=(1, 3),
)

_ADD_COUNT_FORWARD = Spine(
    id="add_count_forward",
    template="Begin at {a}. Count forward {b}. What number do you reach?",
    required_concepts={"addition"},
    blank_target="result",
    grade_band=(1, 3),
)

_SUB_REMOVES = Spine(
    id="sub_removes",
    template="A {place} has {a} {objects}. {actor} removes {b} {objects}. How many {objects} are left in the {place}?",
    required_concepts={"subtraction"},
    blank_target="result",
    grade_band=(1, 3),
)

_ADD_GAIN = Spine(
    id="add_gain",
    template=(
        "{actor} had {a} {objects}. "
        "Then {actor} got {b} more. "
        "How many {objects} does {actor} have now?"
    ),
    required_concepts={"addition"},
    blank_target="result",
    grade_band=(1, 3),
)

_ADD_COMBINATION = Spine(
    id="add_combination",
    template=(
        "There are {a} {objects} in one basket and {b} {objects} in another basket. "
        "How many {objects} are there in all?"
    ),
    required_concepts={"addition"},
    blank_target="result",
    grade_band=(1, 3),
)

_ADD_JOIN = Spine(
    id="add_join",
    template=(
        "{actor} collected {a} {item1} and {b} {item2} at the {place}. "
        "How many items did {actor} collect in total?"
    ),
    required_concepts={"addition"},
    blank_target="result",
    grade_band=(1, 3),
)

_ADD_START_UNKNOWN = Spine(
    id="add_start_unknown",
    template=(
        "{actor} had some {objects}. After getting {b} more, "
        "{actor} had {result} {objects} in all. "
        "How many {objects} did {actor} start with?"
    ),
    required_concepts={"addition", "missing_number"},
    blank_target="a",
    grade_band=(1, 3),
)

_ADD_CHANGE_UNKNOWN = Spine(
    id="add_change_unknown",
    template=(
        "{actor} had {a} {objects}. "
        "{actor} got some more and now has {result} {objects}. "
        "How many {objects} did {actor} get?"
    ),
    required_concepts={"addition", "missing_number"},
    blank_target="b",
    grade_band=(1, 3),
)


# ═══════════════════════════════════════════════════════════════════════════════
# SUBTRACTION SPINES — loss / giving away / how many left
# ═══════════════════════════════════════════════════════════════════════════════

_SUB_LOSS = Spine(
    id="sub_loss",
    template=(
        "{actor} had {a} {objects}. "
        "{actor} used {b} of them. "
        "How many {objects} are left?"
    ),
    required_concepts={"subtraction"},
    blank_target="result",
    grade_band=(1, 3),
)

_SUB_GIVE_AWAY = Spine(
    id="sub_give_away",
    template=(
        "{actor} had {a} {objects} and gave {b} to friends at the {place}. "
        "How many {objects} does {actor} have left?"
    ),
    required_concepts={"subtraction"},
    blank_target="result",
    grade_band=(1, 3),
)

_SUB_HOW_MANY_LEFT = Spine(
    id="sub_how_many_left",
    template=(
        "There were {a} {objects} in a box. "
        "{b} {objects} were taken out. "
        "How many {objects} are still in the box?"
    ),
    required_concepts={"subtraction"},
    blank_target="result",
    grade_band=(1, 3),
)

_SUB_START_UNKNOWN = Spine(
    id="sub_start_unknown",
    template=(
        "{actor} had some {objects}. After giving away {b}, "
        "{actor} had {result} left. "
        "How many {objects} did {actor} start with?"
    ),
    required_concepts={"subtraction", "missing_number"},
    blank_target="a",
    grade_band=(1, 3),
)

_SUB_CHANGE_UNKNOWN = Spine(
    id="sub_change_unknown",
    template=(
        "{actor} had {a} {objects}. After giving away some, "
        "{actor} had {result} left. "
        "How many {objects} did {actor} give away?"
    ),
    required_concepts={"subtraction", "missing_number"},
    blank_target="b",
    grade_band=(1, 3),
)

# Aligned with competency: "describes subtraction as 'taking away,' 'counting back,' and 'comparing'"

_SUB_COUNTING_BACK = Spine(
    id="sub_counting_back",
    template=(
        "Start at {a}. Count back {b}. "
        "What number do you land on?"
    ),
    required_concepts={"subtraction"},
    blank_target="result",
    grade_band=(1, 2),
)

_SUB_COUNTING_BACK_STORY = Spine(
    id="sub_counting_back_story",
    template=(
        "{actor} is on step {a}. "
        "{actor} goes down {b} steps. "
        "What step is {actor} on now?"
    ),
    required_concepts={"subtraction"},
    blank_target="result",
    grade_band=(1, 2),
)

_SUB_TAKING_AWAY = Spine(
    id="sub_taking_away",
    template=(
        "{actor} has {a} {objects}. "
        "{actor} gives away {b} {objects}. "
        "How many {objects} does {actor} have left?"
    ),
    required_concepts={"subtraction"},
    blank_target="result",
    grade_band=(1, 3),
)

_SUB_TAKING_AWAY_TABLE = Spine(
    id="sub_taking_away_table",
    template=(
        "There are {a} {objects} on the table. "
        "{actor} takes away {b} {objects}. "
        "How many {objects} are left on the table?"
    ),
    required_concepts={"subtraction"},
    blank_target="result",
    grade_band=(1, 3),
)

_SUB_COMPARING = Spine(
    id="sub_comparing",
    template=(
        "{actor} has {a} {objects}. A friend has {b} {objects}. "
        "How many more {objects} does {actor} have than the friend?"
    ),
    required_concepts={"subtraction"},
    blank_target="result",
    grade_band=(1, 3),
)

_SUB_COMPARING_FEWER = Spine(
    id="sub_comparing_fewer",
    template=(
        "{actor} has {a} {objects}. A friend has {b} {objects}. "
        "How many fewer {objects} does the friend have?"
    ),
    required_concepts={"subtraction"},
    blank_target="result",
    grade_band=(1, 3),
)


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARISON SPINES — who has more / difference
# ═══════════════════════════════════════════════════════════════════════════════

_COMP_WHO_HAS_MORE = Spine(
    id="comp_who_has_more",
    template=(
        "{actor} has {a} {objects}. A classmate has {b} {objects}. "
        "Who has more, and by how many?"
    ),
    required_concepts={"subtraction", "comparing_ordering"},
    blank_target="result",
    grade_band=(1, 3),
)

_COMP_DIFFERENCE = Spine(
    id="comp_difference",
    template=(
        "Team A scored {a} points and Team B scored {b} points at the {place}. "
        "What is the difference in their scores?"
    ),
    required_concepts={"subtraction", "comparing_ordering"},
    blank_target="result",
    grade_band=(1, 3),
)


# ═══════════════════════════════════════════════════════════════════════════════
# MULTIPLICATION SPINES — equal groups / rows of
# ═══════════════════════════════════════════════════════════════════════════════

_MUL_EQUAL_GROUPS = Spine(
    id="mul_equal_groups",
    template=(
        "There are {groups} groups of {n} {objects}. "
        "How many {objects} are there altogether?"
    ),
    required_concepts={"multiplication"},
    blank_target="total",
    grade_band=(2, 3),
)

_MUL_ROWS_OF = Spine(
    id="mul_rows_of",
    template=(
        "{actor} arranged {objects} in {groups} rows with {n} in each row at the {place}. "
        "How many {objects} are there in all?"
    ),
    required_concepts={"multiplication"},
    blank_target="total",
    grade_band=(2, 3),
)

_MUL_REPEATED_ADD = Spine(
    id="mul_repeated_add",
    template=(
        "{actor} puts {n} {objects} in each of {groups} bags. "
        "How many {objects} are in all the bags?"
    ),
    required_concepts={"multiplication", "addition"},
    blank_target="total",
    grade_band=(2, 3),
)


# ═══════════════════════════════════════════════════════════════════════════════
# DIVISION SPINES — sharing equally / how many groups
# ═══════════════════════════════════════════════════════════════════════════════

_DIV_SHARE_EQUALLY = Spine(
    id="div_share_equally",
    template=(
        "{actor} wants to share {total} {objects} equally among {groups} friends. "
        "How many {objects} does each friend get?"
    ),
    required_concepts={"division"},
    blank_target="n",
    grade_band=(2, 3),
)

_DIV_HOW_MANY_GROUPS = Spine(
    id="div_how_many_groups",
    template=(
        "There are {total} {objects}. "
        "If {n} {objects} are put in each bag, how many bags are needed?"
    ),
    required_concepts={"division"},
    blank_target="groups",
    grade_band=(2, 3),
)


# ═══════════════════════════════════════════════════════════════════════════════
# MONEY SPINES — buying / spending / change
# ═══════════════════════════════════════════════════════════════════════════════

_MONEY_BUYING = Spine(
    id="money_buying",
    template=(
        "{actor} wants to buy {a} {objects} that cost ₱{price} each. "
        "How much does {actor} need to pay in all?"
    ),
    required_concepts={"money_peso", "multiplication"},
    blank_target="amount",
    grade_band=(2, 3),
)

_MONEY_SPENDING = Spine(
    id="money_spending",
    template=(
        "{actor} had ₱{a} and spent ₱{b} on {objects} at the {place}. "
        "How much money does {actor} have left?"
    ),
    required_concepts={"money_peso", "subtraction"},
    blank_target="result",
    grade_band=(1, 3),
)

_MONEY_CHANGE = Spine(
    id="money_change",
    template=(
        "{actor} paid ₱{paid} for {objects} that cost ₱{amount}. "
        "How much change should {actor} receive?"
    ),
    required_concepts={"money_peso", "subtraction"},
    blank_target="change",
    grade_band=(2, 3),
)

_MONEY_TOTAL = Spine(
    id="money_total",
    template=(
        "{actor} has ₱{a} in bills and ₱{b} in coins. "
        "How much money does {actor} have in all?"
    ),
    required_concepts={"money_peso", "addition"},
    blank_target="result",
    grade_band=(1, 3),
)


# ═══════════════════════════════════════════════════════════════════════════════
# MEASUREMENT SPINES — comparing lengths / measuring objects
# ═══════════════════════════════════════════════════════════════════════════════

_MEAS_COMPARE_LENGTHS = Spine(
    id="meas_compare_lengths",
    template=(
        "{actor} measured two {objects}. "
        "The first is {len_a} {unit} and the second is {len_b} {unit}. "
        "What is the total length of both {objects}?"
    ),
    required_concepts={"length_measurement", "addition"},
    blank_target="result",
    grade_band=(1, 3),
)

_MEAS_DIFFERENCE = Spine(
    id="meas_difference",
    template=(
        "One {item1} is {len_a} {unit} long. Another is {len_b} {unit} long. "
        "How much longer is the first than the second?"
    ),
    required_concepts={"length_measurement", "subtraction"},
    blank_target="result",
    grade_band=(2, 3),
)

_MEAS_OBJECT = Spine(
    id="meas_object",
    template=(
        "{actor} measured a {item1} at the {place}. "
        "It was {len_a} {unit} long. "
        "A second {item2} was {len_b} {unit} long. "
        "What is the combined length?"
    ),
    required_concepts={"length_measurement", "addition"},
    blank_target="result",
    grade_band=(1, 3),
)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA SPINES — reading results / collecting data
# ═══════════════════════════════════════════════════════════════════════════════

_DATA_READ_RESULTS = Spine(
    id="data_read_results",
    template=(
        "A class survey showed {a} students like {item1} and {b} students like {item2}. "
        "How many students were surveyed in all?"
    ),
    required_concepts={"pictographs", "addition"},
    blank_target="result",
    grade_band=(1, 3),
)

_DATA_COMPARE = Spine(
    id="data_compare",
    template=(
        "In a pictograph, {actor}'s group collected {a} {objects} and "
        "another group collected {b} {objects}. "
        "How many more did {actor}'s group collect?"
    ),
    required_concepts={"pictographs", "subtraction", "comparing_ordering"},
    blank_target="result",
    grade_band=(2, 3),
)

_DATA_BAR_READ = Spine(
    id="data_bar_read",
    template=(
        "A bar graph shows {a} {item1} and {b} {item2} sold at the {place}. "
        "How many items were sold in total?"
    ),
    required_concepts={"bar_graphs", "addition"},
    blank_target="result",
    grade_band=(2, 3),
)


_COUNTING_STORY = Spine(
    id="counting_story",
    template=(
        "{actor} is counting {dir_word} by {skip_by} starting from {seq_a}. "
        "The count is: {seq_a}, {seq_b}, {seq_c}, {seq_d}. "
        "What is the next number {actor} should say?"
    ),
    required_concepts={"counting"},
    blank_target="answer",
    grade_band=(1, 3),
)


_COMP_SYMBOL_STORY = Spine(
    id="comp_symbol_story",
    template=(
        "{actor} has {a} {objects}. Another classmate has {b} {objects}. "
        "Which comparison is correct: {a} ___ {b}?"
    ),
    required_concepts={"comparing_ordering"},
    blank_target="answer",
    grade_band=(1, 3),
)

_COMP_BETWEEN_STORY = Spine(
    id="comp_between_story",
    template=(
        "{actor} is thinking of a number of {objects} that is greater than {a} but less than {b}. "
        "What is the number?"
    ),
    required_concepts={"comparing_ordering"},
    blank_target="answer",
    grade_band=(1, 3),
)

_COMP_ORDER_STORY = Spine(
    id="comp_order_story",
    template=(
        "{actor} has cards with numbers: {numbers_str}. "
        "Arrange the numbers from smallest to largest."
    ),
    required_concepts={"comparing_ordering"},
    blank_target="answer",
    grade_band=(1, 3),
)


# ═══════════════════════════════════════════════════════════════════════════════
# MASTER LIST
# ═══════════════════════════════════════════════════════════════════════════════

ALL_SPINES: List[Spine] = [
    # Counting
    _COUNTING_STORY,
    # Comparison - comparing_ordering
    _COMP_SYMBOL_STORY,
    _COMP_BETWEEN_STORY,
    _COMP_ORDER_STORY,
    # Addition - counting up (competency-aligned)
    _ADD_COUNTING_UP,
    _ADD_COUNTING_UP_STORY,
    # Addition - putting together (competency-aligned)
    _ADD_PUTTING_TOGETHER,
    _ADD_PUT_TOGETHER_NAMES,
    # Addition - general
    _ADD_GAIN,
    _ADD_COMBINATION,
    _ADD_JOIN,
    _ADD_START_UNKNOWN,
    _ADD_CHANGE_UNKNOWN,
    # Subtraction - counting back (competency-aligned)
    _SUB_COUNTING_BACK,
    _SUB_COUNTING_BACK_STORY,
    # Subtraction - taking away (competency-aligned)
    _SUB_TAKING_AWAY,
    _SUB_TAKING_AWAY_TABLE,
    _SUB_REMOVES,
    # Subtraction - comparing (competency-aligned)
    _SUB_COMPARING,
    _SUB_COMPARING_FEWER,
    # Subtraction - general
    _SUB_LOSS,
    _SUB_GIVE_AWAY,
    _SUB_HOW_MANY_LEFT,
    _SUB_START_UNKNOWN,
    _SUB_CHANGE_UNKNOWN,
    # Comparison
    _COMP_WHO_HAS_MORE,
    _COMP_DIFFERENCE,
    # Multiplication
    _MUL_EQUAL_GROUPS,
    _MUL_ROWS_OF,
    _MUL_REPEATED_ADD,
    # Division
    _DIV_SHARE_EQUALLY,
    _DIV_HOW_MANY_GROUPS,
    # Money
    _MONEY_BUYING,
    _MONEY_SPENDING,
    _MONEY_CHANGE,
    _MONEY_TOTAL,
    # Measurement
    _MEAS_COMPARE_LENGTHS,
    _MEAS_DIFFERENCE,
    _MEAS_OBJECT,
    # Data
    _DATA_READ_RESULTS,
    _DATA_COMPARE,
    _DATA_BAR_READ,
]


# ═══════════════════════════════════════════════════════════════════════════════
# SELECT SPINE
# ═══════════════════════════════════════════════════════════════════════════════

def select_spine(
    node_cumulative_concepts: Set[str],
    grade: int,
    rng: random.Random,
    prior_concepts: Set[str],
    required_blank_target: Optional[str] = None,
) -> Optional[Spine]:
    """
    Choose the best narrative Spine for the current problem context.

    Eligibility rules (all must pass):
      1. spine.required_concepts ⊆ node_cumulative_concepts
      2. spine.grade_band[0] <= grade <= spine.grade_band[1]
      3. if required_blank_target is given, spine.blank_target must equal it —
         a spine whose unknown is the `result` cannot render a `change_unknown`
         (unknown=b) problem: it would print b's value literally, leaking the
         answer and asking the wrong question ("...gives away 0... how many
         left?" for answer b=0). Blank-target agreement keeps the narrative's
         unknown aligned with the DNA's unknown.

    Scoring (higher = more preferred):
      score = len(spine.required_concepts & prior_concepts)

    Ties are broken by a random draw from the rng so results are
    reproducible given the same seed.

    Args:
        node_cumulative_concepts: All concepts the student has seen so far,
            from the knowledge graph node.
        grade: Student grade level (1–10).
        rng: Seeded Random instance for reproducible tie-breaking.
        prior_concepts: Subset of cumulative_concepts the student has
            already practiced (used to prefer richer spines).

    Returns:
        The selected Spine, or None if no eligible spine exists.
    """
    eligible = [
        spine for spine in ALL_SPINES
        if spine.is_eligible(node_cumulative_concepts, grade)
    ]

    if required_blank_target is not None:
        matched = [s for s in eligible if s.blank_target == required_blank_target]
        # Only narrow when a matching spine exists. If none matches the
        # requested blank_target, returning None lets the caller fall back to
        # the symbolic question builder (which blanks the correct operand)
        # rather than silently rendering a mismatched narrative.
        eligible = matched

    if not eligible:
        return None

    # Score: number of required_concepts the student has prior practice with.
    # Higher score → more contextually appropriate spine.
    scored = [
        (len(spine.required_concepts & prior_concepts), spine)
        for spine in eligible
    ]

    max_score = max(s for s, _ in scored)
    top_tier = [spine for s, spine in scored if s == max_score]

    return rng.choice(top_tier)
