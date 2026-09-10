"""
test_judgment_answer_resolution.py
==================================
§5 freshness compares the VALUE an item keys, not the A-D slot the value landed in.

Why this file exists at all: half of that change is a NARROWING, and a narrowing
cannot be proven by the mutation harness. A mutation is scored by making the
validator FAIL with a bug planted; a narrowing makes the validator quieter, so a
plant proving it would have to assert that something does NOT happen, which the
runner has no way to score. `tests/mutation_harness.py` proves the half that
widens (`stale_answer_same_key`); this file pins the half that narrows, in both
directions, so nobody can widen it back or narrow it further without a red test.

What was measured on 2026-09-10, over every recorded sample whose stem still
renders identically and whose answer resolves through an option table on BOTH
sides (`local_only/scratch` reproduction is in the hardening evidence log):

    88  different key, SAME resolved value   -- reported, and should not have been
     2  SAME key, different resolved value   -- NOT reported, and should have been
     2  different key, different value       -- reported, correctly

The under-report is the one that matters and the one the option-multiset
comparison structurally cannot cover: when an item's correct flag moves to a
distractor that was ALREADY on offer, the stem is unchanged, the option multiset
is unchanged, and the key can be unchanged too. Every §5 gate passed that item
while its answer changed underneath the verdict.

`read_mcq` is the formatter that stores a key rather than a value, on 59 nodes.
Nothing here names it: the decision is made from whether a sample's own
`correct_answer` resolves against its own recorded `options`, so a grade-7
formatter with the same shape is covered on the day it is written (Scaling
Mandate 4).
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)

from backend.app.practice_gen.validation.validate_judgment import (  # noqa: E402
    _answer_display,
    _resolved_answer,
)


def _keyed(correct_key, values):
    """A read_mcq-shaped sample: `correct_answer` is a key, options carry the values."""
    return {
        "seed": 42,
        "formatter": "read_mcq",
        "question_text": "What time does the clock show?",
        "correct_answer": correct_key,
        "options": [{"key": k, "value": v, "is_correct": k == correct_key}
                    for k, v in zip("ABCD", values)],
    }


def _valued(correct_value):
    """An mcq-shaped sample: `correct_answer` is the value itself."""
    return {
        "seed": 42,
        "formatter": "mcq",
        "question_text": "What is 2 + 1?",
        "correct_answer": correct_value,
        "options": [{"key": k, "value": v} for k, v in zip("ABCD", ["3", "4", "5", "6"])],
    }


# --- resolution itself --------------------------------------------------------

def test_key_resolves_to_its_option_value():
    assert _resolved_answer(_keyed("C", ["3:15", "2:10", "2:15", "1:15"])) == ("2:15", True)


def test_value_answer_is_not_treated_as_a_key():
    """An `mcq` answer is already a value; nothing may be resolved through the table."""
    assert _resolved_answer(_valued("3")) == ("3", False)


def test_sample_without_options_falls_back_to_the_raw_field():
    """
    The fallback must never invent a value. A sample carrying no options is exactly
    the unadjudicable case `judgment_options_recorded_5` names as its own failure;
    this comparison must not paper over it by guessing.
    """
    assert _resolved_answer({"correct_answer": "C"}) == ("C", False)


def test_key_absent_from_the_option_table_falls_back_to_the_raw_field():
    assert _resolved_answer(_keyed("A", ["3:15"]) | {"correct_answer": "Z"}) == ("Z", False)


# --- the narrowing: placement-only drift must NOT be reported ------------------

def test_placement_only_change_resolves_to_the_same_value():
    """
    mat_g1_mg_q4_1 seed 42, reduced: reviewed keying C='2:15', now keying B='2:15'.
    Same stem, same option multiset, same correct value, different letter. 88 findings
    on the 2026-09-10 tree had this shape and every one of them was a false positive.
    """
    was = _keyed("C", ["3:15", "2:10", "2:15", "1:15"])
    now = _keyed("B", ["3:15", "2:15", "2:10", "1:15"])
    assert _resolved_answer(was)[0] == _resolved_answer(now)[0] == "2:15"


# --- the widening: same key, different value MUST be reported ------------------

def test_same_key_different_value_is_a_real_drift():
    """
    mat_g3_na_q1_0 seed 45, reduced: keyed 'C' before and after, while the item moved
    from 491 to 7844. The raw-field comparison saw 'C' == 'C' and said nothing.
    """
    was = _keyed("C", [493, 490, 491, 492])
    now = _keyed("C", [7843, 7846, 7844, 7845])
    assert _resolved_answer(was)[0] != _resolved_answer(now)[0]


def test_correct_flag_moving_to_an_already_offered_distractor_is_a_real_drift():
    """
    The case the option multiset CANNOT cover: identical stem, identical option
    multiset, identical key, and the correct value moved to a distractor already on
    offer. This is what `stale_answer_same_key` plants in the mutation harness.
    """
    values = ["3:15", "2:15", "2:10", "1:15"]
    was = _keyed("B", values)                      # B = '2:15'
    now = _keyed("B", ["3:15", "2:10", "2:15", "1:15"])  # B = '2:10', same multiset
    assert sorted(str(o["value"]) for o in was["options"]) == \
           sorted(str(o["value"]) for o in now["options"])
    assert was["correct_answer"] == now["correct_answer"] == "B"
    assert _resolved_answer(was)[0] != _resolved_answer(now)[0]


# --- the finding text a human reads -------------------------------------------

def test_finding_text_shows_the_value_not_only_the_letter():
    """
    "Reviewed: 'C'; now keys: 'B'" tells a reader a letter moved and nothing about
    whether the item changed. The display resolves the letter so the reader can see
    which of the two populations above they are looking at.
    """
    shown = _answer_display(_keyed("C", ["3:15", "2:10", "2:15", "1:15"]))
    assert "'C'" in shown and "2:15" in shown


def test_finding_text_is_best_effort_and_never_decides_anything():
    """An unresolvable answer is shown as-is rather than dropped or guessed at."""
    assert _answer_display({"correct_answer": "C"}) == "'C'"
