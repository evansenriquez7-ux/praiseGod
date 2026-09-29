"""Regression tests for the source defects confirmed during Phase C review."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from backend.app.practice_gen.validation import judgment_packets as jp
from backend.app.practice_gen.validation.validate_matrix import _visual_payload_defects


def _sample(node_id: str, seed: int) -> dict:
    return jp._render_sample(node_id, seed)


@pytest.mark.parametrize("node_id", ["mat_g2_na_q4_2", "mat_g2_na_q4_5"])
def test_fraction_ordering_hints_teach_ordering(node_id):
    sample = _sample(node_id, 500)
    hints = " ".join(sample["hints"]).lower()
    assert "adding" not in hints and "add only" not in hints
    assert "largest to smallest" in hints


def test_time_options_are_stable_across_python_hash_seeds():
    code = (
        "import json; "
        "from backend.app.practice_gen.validation.judgment_packets import _render_sample; "
        "print(json.dumps(_render_sample('mat_g2_mg_q4_2', 603)['options'], sort_keys=True))"
    )
    outputs = []
    # These three values are deliberately discriminating for the seed-603
    # time strings; 1 and 2 happen to produce the same set order on CPython
    # 3.12 and would let the motivating mutation survive.
    for hash_seed in ("1", "3", "6"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONPATH=".")
        outputs.append(subprocess.check_output([sys.executable, "-c", code], env=env, text=True))
    assert len(set(outputs)) == 1


@pytest.mark.parametrize(
    "seed,month",
    [(44, 3), (613, 9), (614, 2)],
)
def test_calendar_problem_draws_the_month_named_in_its_stem(seed, month):
    sample = _sample("mat_g1_mg_q4_4", seed)
    assert sample["visual_payload"]["month"] == month
    assert "how much time has passed" not in " ".join(sample["hints"]).lower()
    assert _visual_payload_defects({
        "visual_type": sample["visual_type"],
        "visual_params": sample["visual_payload"],
        "question_text": sample["question_text"],
    }) == []


def test_clock_period_is_in_the_payload_and_checked_by_visual_invariant():
    sample = _sample("mat_g2_mg_q4_1", 42)
    served = {
        "visual_type": sample["visual_type"],
        "visual_params": sample["visual_payload"],
        "question_text": sample["question_text"],
    }
    assert _visual_payload_defects(served) == []
    assert sample["visual_payload"]["period"] == "p.m."
    problem = {
        "visual_type": "ClockSet",
        "visual_params": dict(sample["visual_payload"], period="a.m."),
        "question_text": sample["question_text"],
    }
    defects = _visual_payload_defects(problem)
    assert any("different half of day" in defect for defect in defects)


def test_addition_money_node_never_resolves_to_change_making():
    sample = _sample("mat_g2_na_q2_2", 605)
    assert "left" not in sample["question_text"].lower()
    assert "paid" not in " ".join(sample["hints"]).lower()


@pytest.mark.parametrize("node_id,seed", [("mat_g3_dp_q3_1", 701), ("mat_g3_dp_q3_2", 900)])
def test_table_stems_render_a_real_table(node_id, seed):
    sample = _sample(node_id, seed)
    assert "table" in sample["question_text"].lower()
    assert sample["visual_type"] == "FillInTable"
    assert sample["visual_payload"]["columns"] == ["Category", "Value"]


def test_category_options_come_from_the_displayed_data():
    sample = _sample("mat_g3_dp_q3_2", 900)
    categories = {row[0] for row in sample["visual_payload"]["rows"]}
    assert {option["value"] for option in sample["options"]} <= categories


def test_named_multiplication_table_is_the_leading_factor():
    sample = _sample("mat_g3_na_q3_0", 605)
    assert not sample["question_text"].startswith("What is 5 × 7")
    assert "7 × 5" in sample["question_text"]


def test_interest_cue_does_not_claim_the_task_is_about_an_unrelated_object():
    sample = _sample("mat_g3_dp_q3_1", 701)
    assert "has a math challenge about" not in sample["question_text"]
    assert "Here is a math challenge." in sample["question_text"]
