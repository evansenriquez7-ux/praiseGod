import random
from dataclasses import dataclass
from typing import Set, Tuple, List, Optional, Dict, Any
import json
import os

INTEREST_BANK_PATH = os.path.join(os.path.dirname(__file__), "../../../data/interest_bank.json")
try:
    with open(INTEREST_BANK_PATH, "r", encoding="utf-8") as f:
        INTEREST_BANK = json.load(f)["interests"]
except Exception:
    INTEREST_BANK = {}


@dataclass
class Spine:
    id: str
    template: str
    required_concepts: Set[str]
    blank_target: str
    grade_band: Tuple[int, int]
    
    # Optional logic category if a generator wants a specific type of word problem
    # e.g., "putting_together", "change_increase", "comparison"
    narrative_logic: str = "generic"

# ─── CORE REGISTRY ──────────────────────────────────────────────────────────

ALL_SPINES: List[Spine] = [
    # ── ADDITION SPINES ──
    # putting_together
    Spine(
        id="add_put_together_1",
        template="There are {a} {item} in one {container} and {b} {item} in another {container}. If you put all the {item} together, how many {item} are there?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="putting_together"
    ),
    Spine(
        id="add_put_together_2",
        template="{name} has {a} {item} and {name2} has {b} {item}. If they put all their {item} together, how many {item} do they have in all?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="putting_together"
    ),
    Spine(
        id="add_put_together_3",
        template="One {container} has {a} {item}. Another {container} has {b} {item}. If you put all the {item} from both {container}s together, how many {item} are there?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="putting_together"
    ),
    Spine(
        id="add_put_together_4",
        template="{name} found {a} {item}. {name2} found {b} {item}. If they put all their {item} together, how many {item} do they have altogether?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="putting_together"
    ),
    
    # counting_up
    Spine(
        id="add_count_up_1",
        template="Start at {a}. Count up {b} more. What number do you land on?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="counting_up"
    ),
    Spine(
        id="add_count_up_2",
        template="{name} is on step {a}. {name} climbs up {b} more steps. What step is {name} on now?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="counting_up"
    ),
    Spine(
        id="add_count_up_3",
        template="Begin at {a}. Count forward {b}. What number do you reach?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="counting_up"
    ),
    Spine(
        id="add_count_up_4",
        template="{name} is at position {a}. {pronoun} hops forward {b} times. What position is {name} at now?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="counting_up"
    ),
    
    # change_increase
    Spine(
        id="add_change_increase_1",
        template="{name} has {a} {item}. {name2} gives {name} {b} more {item}. How many {item} does {name} have now?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="change_increase"
    ),
    Spine(
        id="add_change_increase_2",
        template="{name} had {a} {item}. Then {name} got {b} more {item}. How many {item} does {name} have now?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="change_increase"
    ),
    Spine(
        id="add_change_increase_3",
        template="There are {a} {item} on the table. {name} puts {b} more {item} on the table. How many {item} are on the table now?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="change_increase"
    ),
    Spine(
        id="add_change_increase_4",
        template="{name} collected {a} {item} in the morning and {b} more {item} in the afternoon. How many {item} did {name} collect in all?",
        required_concepts={"addition"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="change_increase"
    ),

    # ── MISSING ADDEND SPINES (Algebraic Structures) ──
    Spine(
        id="add_change_unknown_1",
        template="{name} has {a} {item}. After getting some more {item}, {name} now has {result} {item}. How many {item} did {name} get?",
        required_concepts={"addition"},
        blank_target="b",
        grade_band=(1, 3),
        narrative_logic="change_unknown"
    ),
    Spine(
        id="add_start_unknown_1",
        template="{name} had some {item}. After getting {b} more {item}, {name} now has {result} {item}. How many {item} did {name} have at first?",
        required_concepts={"addition"},
        blank_target="a",
        grade_band=(1, 3),
        narrative_logic="start_unknown"
    ),
    
    # ── SUBTRACTION SPINES ──
    # taking_away
    Spine(
        id="sub_take_away_1",
        template="{name} has {a} {item}. {pronoun} gives away {b} {item}. How many {item} does {name} have left?",
        required_concepts={"subtraction"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="taking_away"
    ),
    Spine(
        id="sub_take_away_2",
        template="There are {a} {item} on the table. {name} takes away {b} {item}. How many {item} are left on the table?",
        required_concepts={"subtraction"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="taking_away"
    ),
    Spine(
        id="sub_take_away_3",
        template="{name} had {a} {item}. {pronoun} used {b} of them. How many {item} are left?",
        required_concepts={"subtraction"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="taking_away"
    ),
    Spine(
        id="sub_take_away_4",
        template="A {container} has {a} {item}. {name} removes {b} {item}. How many {item} are left in the {container}?",
        required_concepts={"subtraction"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="taking_away"
    ),
    
    # counting_back
    Spine(
        id="sub_count_back_1",
        template="Start at {a}. Count back {b}. What number do you land on?",
        required_concepts={"subtraction"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="counting_back"
    ),
    Spine(
        id="sub_count_back_2",
        template="{name} is on step {a}. {pronoun} goes down {b} steps. What step is {name} on now?",
        required_concepts={"subtraction"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="counting_back"
    ),
    Spine(
        id="sub_count_back_3",
        template="{name} is at position {a}. {pronoun} hops backward {b} times. What position is {name} at now?",
        required_concepts={"subtraction"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="counting_back"
    ),
    
    # comparing
    Spine(
        id="sub_compare_1",
        template="{name} has {a} {item}. {name2} has {b} {item}. How many more {item} does {name} have than {name2}?",
        required_concepts={"subtraction"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="comparing"
    ),
    Spine(
        id="sub_compare_2",
        template="There are {a} {item} in one {container} and {b} {item} in another. How many more {item} are in the first {container}?",
        required_concepts={"subtraction"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="comparing"
    ),
    Spine(
        id="sub_compare_3",
        template="{name} has {a} {item}. {name2} has {b} {item}. How many fewer {item} does {name2} have?",
        required_concepts={"subtraction"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="comparing"
    ),
    
    # missing subtrahend / minuend
    Spine(
        id="sub_change_unknown_1",
        template="{name} had {a} {item}. After giving some away, {pronoun} now has {result} {item}. How many {item} did {name} give away?",
        required_concepts={"subtraction"},
        blank_target="b",
        grade_band=(1, 3),
        narrative_logic="change_unknown"
    ),
    Spine(
        id="sub_start_unknown_1",
        template="{name} had some {item}. After giving away {b} {item}, {pronoun} now has {result} {item}. How many {item} did {name} have at first?",
        required_concepts={"subtraction"},
        blank_target="a",
        grade_band=(1, 3),
        narrative_logic="start_unknown"
    ),

    # ── MULTIPLICATION SPINES ──
    Spine(
        id="mult_equal_groups_1",
        template="{name} has {a} {container}s. Each {container} has {b} {item}. How many {item} does {name} have in all?",
        required_concepts={"multiplication"},
        blank_target="result",
        grade_band=(2, 3),
        narrative_logic="equal_groups"
    ),
    Spine(
        id="mult_equal_groups_2",
        template="There are {a} {container}s on the table. If you put {b} {item} in each {container}, how many {item} are there in total?",
        required_concepts={"multiplication"},
        blank_target="result",
        grade_band=(2, 3),
        narrative_logic="equal_groups"
    ),
    Spine(
        id="mult_rate_1",
        template="{name} buys {a} {item}. Each {item} costs {b} pesos. How much does {name} pay in all?",
        required_concepts={"multiplication", "money_peso"},
        blank_target="result",
        grade_band=(2, 3),
        narrative_logic="rate"
    ),
    Spine(
        id="mult_array_1",
        template="A garden has {a} rows of plants. There are {b} plants in each row. How many plants are there altogether?",
        required_concepts={"multiplication"},
        blank_target="result",
        grade_band=(2, 3),
        narrative_logic="array"
    ),

    # ── DIVISION SPINES ──
    Spine(
        id="div_sharing_1",
        template="{name} has {a} {item}. {pronoun} shares them equally among {b} friends. How many {item} does each friend get?",
        required_concepts={"division"},
        blank_target="result",
        grade_band=(2, 3),
        narrative_logic="sharing"
    ),
    Spine(
        id="div_grouping_1",
        template="{name} has {a} {item}. {pronoun} puts them into groups of {b}. How many groups can {name} make?",
        required_concepts={"division"},
        blank_target="result",
        grade_band=(2, 3),
        narrative_logic="grouping"
    ),
    Spine(
        id="div_money_1",
        template="{name} paid {a} pesos for {b} identical {item}. How much did each {item} cost?",
        required_concepts={"division", "money_peso"},
        blank_target="result",
        grade_band=(2, 3),
        narrative_logic="sharing"
    ),

    # ── FRACTIONS SPINES ──
    Spine(
        id="frac_pizza_1",
        template="{name} has a pizza cut into {b} equal slices. {pronoun} eats {a} slices. What fraction of the pizza did {name} eat?",
        required_concepts={"fractions"},
        blank_target="result",
        grade_band=(2, 3),
        narrative_logic="pizza"
    ),

    # ── MONEY SPINES ──
    Spine(
        id="money_add_1",
        template="{name} has {a} pesos. {name2} gives {name} {b} more pesos. How much money does {name} have now?",
        required_concepts={"money_peso"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="add_money"
    ),
    Spine(
        id="money_sub_1",
        template="{name} has {a} pesos. {pronoun} buys a {item} for {b} pesos. How much change will {name} get?",
        required_concepts={"money_peso"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="sub_money"
    ),

    # ── COMPARING / ORDERING SPINES ──
    Spine(
        id="comp_two_1",
        template="{name} has {a} {item}. {name2} has {b} {item}. Compare the number of {item} they have: {a} ___ {b}",
        required_concepts={"comparing_ordering"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="compare_two"
    ),
    Spine(
        id="comp_order_1",
        template="{name} counted {item} in different {container}s and got: {seq_str}. Order these numbers from smallest to largest.",
        required_concepts={"comparing_ordering"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="order_set"
    ),

    # ── COUNTING SPINES ──
    Spine(
        id="count_forward_1",
        template="{name} is counting forward by {skip_by}s. {pronoun} says: {seq_str}, ... What number comes next?",
        required_concepts={"counting"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="forward"
    ),
    Spine(
        id="count_backward_1",
        template="{name} is counting backward by {skip_by}s. {pronoun} says: {seq_str}, ... What number comes next?",
        required_concepts={"counting"},
        blank_target="result",
        grade_band=(1, 3),
        narrative_logic="backward"
    ),

]

def get_eligible_spines(
    grade: int,
    concept: str,
    blank_target: Optional[str] = None,
    narrative_logic: Optional[str] = None
) -> List[Spine]:
    """Find all spines matching the constraints."""
    eligible = []
    for s in ALL_SPINES:
        # Check grade band
        if not (s.grade_band[0] <= grade <= s.grade_band[1]):
            continue
        # Check concept matches
        if concept not in s.required_concepts:
            continue
        # Check blank target constraint if specified
        if blank_target and s.blank_target != blank_target:
            continue
        # Check narrative logic if specified
        if narrative_logic and s.narrative_logic != narrative_logic:
            continue
            
        eligible.append(s)
    return eligible

def select_spine(
    grade: int,
    concept: str,
    rng: random.Random,
    blank_target: Optional[str] = None,
    narrative_logic: Optional[str] = None
) -> Optional[Spine]:
    """Randomly select an eligible spine."""
    eligible = get_eligible_spines(grade, concept, blank_target, narrative_logic)
    if not eligible:
        return None
    return rng.choice(eligible)

def format_spine(
    spine: Spine,
    math_vars: Dict[str, Any],
    rng: random.Random,
    grade: int,
    interest_id: Optional[str] = None
) -> str:
    """Format a spine template using slots from the interest bank."""
    # Select interest profile
    available_interests = list(INTEREST_BANK.values())
    if not available_interests:
        # Fallback if JSON missing
        actors = ["Maria", "Juan", "Ana", "Pedro"]
        objects = ["apples", "books", "stickers", "marbles"]
        places = ["basket", "box", "bag", "jar"]
    else:
        # Filter by grade
        valid_interests = [i for i in available_interests if i["grade_band"][0] <= grade <= i["grade_band"][1]]
        if not valid_interests:
            valid_interests = available_interests
            
        if interest_id and interest_id in INTEREST_BANK:
            interest = INTEREST_BANK[interest_id]
        else:
            interest = rng.choice(valid_interests)
            
        actors = interest.get("actors", ["student"])
        objects = interest.get("objects", ["items"])
        places = interest.get("places", ["places"])
        
    # Pick random slots
    name = rng.choice(actors)
    name2 = rng.choice([n for n in actors if n != name] or actors)
    item = rng.choice(objects)
    container = rng.choice(places)
    
    # Heuristic for pronoun
    pronoun = "He" if name in ["David", "Moses", "Kuya", "Emman", "Juan", "Pedro", "Carlos", "Miguel", "Diego"] else "She"
    
    # Merge math vars and narrative slots
    format_dict = {
        **math_vars,
        "name": name,
        "name2": name2,
        "item": item,
        "container": container,
        "pronoun": pronoun,
    }
    
    return spine.template.format(**format_dict)
