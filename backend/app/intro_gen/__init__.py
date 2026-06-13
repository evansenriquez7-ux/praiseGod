"""
Intro Content Generation Module

Generates introductory lesson content for MATATAG nodes.
Perseus templates are the ground truth for teaching structure;
we parameterize them for dynamism and augment where insufficient.

Architecture:
  generator.py        — orchestration: MINI_LESSON_GROUPS, DEFINITION_BANK, main generate loop
  g1_generators.py    — Grade 1 worked example generators (NA Q2-Q4, MG Q1/Q2/Q4, DP Q3)
  g2_generators.py    — Grade 2 worked example generators
  g3_generators.py    — Grade 3 worked example generators

_INTRODUCTIONS is the central registry for all introduction slide text.
Each entry is keyed as "node_key::group_title".
"""

# Central introduction text registry — populated by each grade module on import
_INTRODUCTIONS: dict = {}

# G1_NA_Q1 introductions (defined here since generator.py handles that node directly)
_INTRODUCTIONS.update({
    "g1_na_q1::Counting & Numerals": (
        "Numbers help us count things.\n"
        "We can count up: 1, 2, 3, 4, 5...\n"
        "We can count down: 5, 4, 3, 2, 1...\n"
        "Let's learn how we write and show numbers."
    ),
    "g1_na_q1::Comparing & Ordering": (
        "You can count numbers. Now let's use them.\n"
        "Look at two numbers — which one is bigger?\n"
        "We can also put numbers in order."
    ),
    "g1_na_q1::Breaking Apart Numbers": (
        "You can count numbers. You can compare them.\n"
        "Now let's look inside a number.\n"
        "Every number is made of smaller parts.\n"
        "5 can be 3 and 2. Or 4 and 1. Or 5 and 0.\n"
        "There are many ways to break apart a number."
    ),
    "g1_na_q1::Addition": (
        "You can count up. You can break numbers apart.\n"
        "Now let's put two groups together.\n"
        "How many are there in total?"
    ),
})

# Import grade modules — they register themselves into MINI_LESSON_GROUPS and _INTRODUCTIONS
from .g1_generators import register as _reg_g1  # noqa: E402
from .g2_generators import register as _reg_g2  # noqa: E402
from .g3_generators import register as _reg_g3  # noqa: E402

_reg_g1()
_reg_g2()
_reg_g3()

from .generator import generate_intro_content, get_available_intro_nodes, get_interest_themes  # noqa: E402
