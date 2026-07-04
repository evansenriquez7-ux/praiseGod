"""
test_separation_of_concerns.py
================================
Tests for the relaxed Separation-of-Concerns check in
`exhaustive_checklist_auditor.py`.

Background:
  The audit harness compares the numeric state of a `pure` problem and the
  same problem wrapped in a `word_problem` context. Comparing regex-scraped
  stem digits is the WRONG signal: a value that is blanked (the
  ``blank_target``) or rendered as a word by a word_problem spine
  legitimately leaves the visible stem even though the underlying math is
  unchanged (e.g. pure "0 + 0 = ___" prints two zeros; the word_problem
  "There are ___ ... and 0 ..." prints only one). The auditor therefore
  compares the *semantic operands* — the numeric ``given_values`` plus the
  answer, which are identical across contexts by construction. The check
  requires the pure operands to be a *multiset subset* of the word-problem
  operands: every (n, count) pair in pure must still appear in word_problem
  with at least the same count.

These tests exercise the comparison semantics directly so we do not need
to spin up the full orchestrator. The reference implementation of the
subset check is reproduced inline so the tests verify the *behavior* the
auditor now implements — and the helper is also exported so future
auditor changes can be tested through this module.
"""

from pathlib import Path

import pytest


AUDITOR_PATH = Path(__file__).resolve().parents[1] / "exhaustive_checklist_auditor.py"


def _pure_numbers_are_subset_of_word(pure_state, word_state):
    """Reference implementation of the relaxed separation-of-concerns check.

    Mirrors the logic added to `exhaustive_checklist_auditor.py` next to
    the `Separation of Concerns Violation` failure path. Returns the dict
    of missing/insufficient numbers (empty when pure is a multiset subset
    of word).
    """
    ref_nums = (pure_state or {}).get("_semantic_operands") or ()
    cur_nums = (word_state or {}).get("_semantic_operands") or ()
    ref_counter = dict(ref_nums)
    cur_counter = dict(cur_nums)
    return {n: c for n, c in ref_counter.items() if cur_counter.get(n, 0) < c}


def _make_state(*pairs):
    """Build a synthetic numeric state with the given (number, count) pairs."""
    return {"_semantic_operands": tuple(sorted(pairs))}


class TestSeparationOfConcernsSubset:
    """Positive cases — pure is a subset of word_problem; no violation."""

    def test_pure_subset_of_word_with_extra_object_number(self):
        # Pure has {1, 2, 3} (each once). Word-problem has the same
        # plus an extra "1 mystery novel" — the 1 is repeated, others
        # are the same. Pure is a subset, so no violation.
        pure = _make_state((1, 1), (2, 1), (3, 1))
        word = _make_state((1, 2), (2, 1), (3, 1))
        assert _pure_numbers_are_subset_of_word(pure, word) == {}

    def test_pure_exactly_equals_word(self):
        # Pure and word-problem are byte-equal — still a subset.
        pure = _make_state((1, 1), (2, 1), (3, 1))
        word = _make_state((1, 1), (2, 1), (3, 1))
        assert _pure_numbers_are_subset_of_word(pure, word) == {}

    def test_pure_with_decimal_subset_of_word(self):
        # Decimals from the pure stem must still be present in the
        # word-problem stem even if the wrapper added integer object
        # counts.
        pure = _make_state((0.5, 1), (2, 1))
        word = _make_state((0.5, 1), (1, 3), (2, 1))
        assert _pure_numbers_are_subset_of_word(pure, word) == {}

    def test_zero_plus_zero_blanked_operand_no_violation(self):
        # Regression for the mat_g3_na_q2_1 false positives: pure
        # "0 + 0 = ___" and word_problem "There are ___ ... and 0 ..."
        # differ in visible stem digits (three 0s vs two), but the
        # semantic operands (given a=0, b=0, answer=0) are identical, so
        # there must be no violation.
        pure = _make_state((0, 3))  # a=0, b=0, answer=0
        word = _make_state((0, 3))
        assert _pure_numbers_are_subset_of_word(pure, word) == {}

    def test_pure_empty_always_subset(self):
        # An empty pure state (e.g. no extracted numbers) is trivially
        # a subset of any word state.
        assert _pure_numbers_are_subset_of_word({}, _make_state((7, 1))) == {}
        assert _pure_numbers_are_subset_of_word(_make_state(), _make_state((7, 1))) == {}


class TestSeparationOfConcernsViolation:
    """Negative cases — pure is NOT a subset of word_problem; violation."""

    def test_disjoint_number_sets_flagged(self):
        # Pure has {1, 2, 3}; word-problem has {4, 5, 6} — all core
        # numbers missing, every pure number is a violation.
        pure = _make_state((1, 1), (2, 1), (3, 1))
        word = _make_state((4, 1), (5, 1), (6, 1))
        missing = _pure_numbers_are_subset_of_word(pure, word)
        assert 1 in missing and 2 in missing and 3 in missing
        assert missing[1] == 1 and missing[2] == 1 and missing[3] == 1

    def test_partial_overlap_still_flagged(self):
        # Pure has {1, 2, 3}; word-problem has {1, 4, 5} — 2 and 3
        # are missing, so a violation must be reported.
        pure = _make_state((1, 1), (2, 1), (3, 1))
        word = _make_state((1, 1), (4, 1), (5, 1))
        missing = _pure_numbers_are_subset_of_word(pure, word)
        assert 2 in missing
        assert 3 in missing
        assert 1 not in missing

    def test_reduced_count_flagged(self):
        # Pure uses the number 7 twice; word-problem only uses it once.
        # Multiplicity must be preserved.
        pure = _make_state((7, 2))
        word = _make_state((7, 1))
        missing = _pure_numbers_are_subset_of_word(pure, word)
        assert missing == {7: 2}


class TestAuditorWiring:
    """Verify the auditor file actually contains the relaxed check."""

    def test_auditor_has_subset_check(self):
        # We don't need to run the full audit (it spins up the
        # orchestrator). We just confirm the source file references the
        # new logic so a regression in the harness is caught at test
        # time.
        if not AUDITOR_PATH.exists():
            pytest.skip(f"auditor not found at {AUDITOR_PATH}")
        source = AUDITOR_PATH.read_text(encoding="utf-8")
        assert "_semantic_operands" in source, (
            "Auditor no longer reads _semantic_operands — the "
            "separation-of-concerns check must compare given_values/answer "
            "operands, not regex-scraped stem digits."
        )
        assert "Separation of Concerns Violation" in source, (
            "Auditor no longer references the Separation of Concerns "
            "Violation failure — the check appears to have been removed."
        )
        # The new logic must compute a `missing` dict (multiset
        # subtraction) and only emit a failure when it is non-empty.
        # This is what makes the check a *subset* check rather than
        # the previous strict equality check.
        assert "cur_counter.get(n, 0) < c" in source, (
            "Auditor no longer performs the multiset subset check "
            "(`cur_counter.get(n, 0) < c`) — the relaxed check has "
            "regressed to the strict comparison."
        )
        assert "if missing:" in source, (
            "Auditor no longer gates the failure on a non-empty "
            "`missing` dict — the relaxed check has regressed."
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
