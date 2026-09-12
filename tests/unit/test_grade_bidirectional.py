"""
§10's second direction: the emitters that make an always-true grader detectable.

Why these are pinned
--------------------
`grading_refusal_10` is only as strong as `_emit_wrong`. If that function ever returns
something that is NOT actually wrong -- the correct answer under another spelling, an
MCQ key that happens to be the keyed one, an "ordering" that is the same ordering -- the
refusal gate passes vacuously and an always-true grader walks straight through it again.
A vacuous gate is worse than none, because it reports green (Scaling Mandate 1).

So each case asserts two things: the derived submission differs from the key, and it
differs in the way the response contract can actually express.
"""

from __future__ import annotations

import json

import pytest

from backend.app.practice_gen.validation.validate_grade import (
    _emit_malformed,
    _emit_whitespace_equivalent,
    _emit_wrong,
)
from backend.app.services.scoring import (
    answers_match,
    bool_answers_match,
    normalize_option_key,
    parse_bool_answer,
)


class TestEmitWrong:
    def test_mcq_returns_a_declared_but_incorrect_key(self):
        payload = {"answer_collection": "mcq", "format": "mcq", "format_data": {
            "mcq_options": [
                {"key": "A", "value": 3, "is_correct": False},
                {"key": "B", "value": 4, "is_correct": True},
                {"key": "C", "value": 5, "is_correct": False},
            ]}}
        wrong = _emit_wrong(payload, "B")
        assert wrong in {"A", "C"}, "must be a key a pupil could actually click"
        assert wrong != "B"

    def test_mcq_with_no_other_option_is_underivable_not_wrong(self):
        """One option means no wrong answer exists; that is an obligation failure, not a pass."""
        payload = {"answer_collection": "mcq", "format": "mcq", "format_data": {
            "mcq_options": [{"key": "A", "value": 3, "is_correct": True}]}}
        assert _emit_wrong(payload, "A") is None

    @pytest.mark.parametrize("correct,expected", [("True", "False"), ("False", "True"),
                                                  (True, "False"), ("true", "False")])
    def test_true_false_flips(self, correct, expected):
        payload = {"format": "true_false", "answer_collection": "true_false"}
        assert _emit_wrong(payload, correct) == expected

    def test_ordering_changes_the_order_not_the_elements(self):
        payload = {"format": "ordering"}
        wrong = _emit_wrong(payload, [1, 2, 3])
        assert wrong != [1, 2, 3]
        assert sorted(wrong) == [1, 2, 3], "order is the competency; keep the multiset"

    def test_single_element_list_cannot_be_reordered_so_the_element_moves(self):
        wrong = _emit_wrong({"format": "ordering"}, [7])
        assert wrong == [8.0]

    def test_numeric_steps_clear_of_a_number_line_tolerance(self):
        payload = {"question_mode": "number_line", "visual_params": {"tolerance": 2.5}}
        wrong = _emit_wrong(payload, 10)
        assert abs(wrong - 10) > 2.5, "a wrong answer inside tolerance is graded CORRECT"

    def test_numeric_string_keeps_its_type(self):
        assert _emit_wrong({"format": "cloze"}, "35") == "36"

    def test_free_text_answer_gets_a_token_no_contract_keys(self):
        wrong = _emit_wrong({"format": "cloze"}, "half past three")
        assert isinstance(wrong, str) and wrong != "half past three"

    def test_error_detect_perturbs_the_value_inside_its_json(self):
        correct = json.dumps({"has_error": True, "correct_value": 12})
        wrong = json.loads(_emit_wrong({"format": "error_detect"}, correct))
        assert wrong["has_error"] is True
        assert wrong["correct_value"] != 12

    def test_structured_visual_answer_perturbs_one_field(self):
        wrong = _emit_wrong({"question_mode": "clock_set"}, {"hour": 3, "minute": 30})
        assert wrong != {"hour": 3, "minute": 30}
        assert set(wrong) == {"hour", "minute"}, "shape must stay in contract"

    def test_empty_answer_is_underivable(self):
        assert _emit_wrong({"format": "cloze"}, "") is None
        assert _emit_wrong({"format": "cloze"}, None) is None


class TestEmitMalformedAndEquivalent:
    def test_malformed_for_structured_answers_is_not_parseable(self):
        with pytest.raises(json.JSONDecodeError):
            json.loads(_emit_malformed([1, 2, 3]))

    def test_malformed_for_scalars_is_a_token_no_key_can_be(self):
        assert _emit_malformed("35") not in ("35", "")

    def test_whitespace_equivalent_preserves_the_answer(self):
        assert _emit_whitespace_equivalent("B").strip() == "B"

    def test_whitespace_equivalent_is_none_where_padding_is_meaningless(self):
        assert _emit_whitespace_equivalent([1, 2]) is None
        assert _emit_whitespace_equivalent(7) is None


class TestSharedGraderPrimitives:
    """The three graders must agree because they call the SAME function (Protocol 2)."""

    @pytest.mark.parametrize("value,expected", [
        ("True", True), ("t", True), ("YES", True), ("1", True), (True, True), (1, True),
        ("False", False), ("no", False), ("0", False), (False, False), (0, False),
    ])
    def test_parse_bool_answer_accepts_the_contract(self, value, expected):
        assert parse_bool_answer(value) is expected

    @pytest.mark.parametrize("value", ["", "  ", "maybe", "definitely_not_the_answer_zzz",
                                       None, 7, [], {}])
    def test_parse_bool_answer_refuses_everything_else(self, value):
        assert parse_bool_answer(value) is None, (
            "an unrecognised submission must have a FAILURE value; the old membership "
            "test made it False, so gibberish was graded CORRECT on every False-keyed item"
        )

    def test_malformed_boolean_is_not_correct_against_either_key(self):
        assert bool_answers_match("zzz", "False") is False
        assert bool_answers_match("zzz", "True") is False

    def test_unparseable_key_grades_incorrect_rather_than_raising(self):
        assert bool_answers_match("True", "banana") is False

    def test_option_key_normalisation_is_strip_then_upper(self):
        assert normalize_option_key("  b  ") == "B"
        assert normalize_option_key("B") == normalize_option_key(" b ")

    def test_answers_match_normalises_whitespace_on_both_sides(self):
        assert answers_match("  1/4  ", "1/4") is True
        assert answers_match("1/4", "1/3") is False
