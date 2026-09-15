"""
§8's unproven-label taxonomy, pinned in all three directions.

WHY THIS FILE EXISTS
--------------------
On 2026-09-15 §8 reported 19 assertions as "can fail but no mutation proves it does...
Write the mutation, or add an entry with a reason and a date". Every one of those 19 was
in fact claimed by a mutation; the mutations had filed proof records taken against a RED
baseline, so the records did not hold. The instruction was therefore wrong in the most
expensive direction available: a reader following it would have written a second mutation
for a check that already had one, and left the real defect (a control proved against noise,
Mandate 5) in place.

`validate_coverage_tagged` now separates the three ways a label can be unproven, because
each has a different fix:

    never_executed        no proof record exists            -> run the mutation
    proof_does_not_hold   a record exists and fails         -> repair the control, re-run
    unproven_assertion    nothing claims the label at all   -> write one, or allowlist it

These tests drive the classifier with synthetic proof state rather than the live corpus, so
they keep their meaning once the real corpus is re-proved green.
"""

from __future__ import annotations

from typing import Dict, List, Set

import pytest

from backend.app.practice_gen.validation import validate_coverage as vc


class _Mutation:
    """The two attributes the classifier reads off a mutation table entry."""

    def __init__(self, name: str, asserts: List[str]) -> None:
        self.name = name
        self.asserts = asserts


def _classify(monkeypatch: pytest.MonkeyPatch, *,
              inventory: Set[str],
              mutations: List[_Mutation],
              proven: Set[str],
              stale_tree_only: Set[str],
              failed_verification: Dict[str, List[str]],
              never_run: List[str]) -> Dict[str, List[str]]:
    """Run the real classifier over synthetic proof state; return family -> messages."""
    monkeypatch.setattr(vc, "harness_assertion_labels", lambda: inventory)
    monkeypatch.setattr(vc, "_mutations", lambda: mutations)
    monkeypatch.setattr(vc, "declared_assertions", lambda: set())
    monkeypatch.setattr(vc, "printed_check_labels", lambda: (set(), []))
    monkeypatch.setattr(vc, "unproven_because_never_executed", lambda: never_run)
    monkeypatch.setattr(vc, "UNPROVEN_ASSERTIONS", {})
    monkeypatch.setattr(vc, "_proof_state", lambda: {
        "proven": proven,
        "stale_tree_only": stale_tree_only,
        "failed_verification": failed_verification,
        "errors": [],
    })
    out: Dict[str, List[str]] = {}
    for msg, family in vc.validate_coverage_tagged():
        out.setdefault(family, []).append(msg)
    return out


def test_a_record_that_does_not_hold_is_not_reported_as_a_missing_mutation(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The 2026-09-15 defect: a red-baseline proof read as 'no mutation exists'."""
    families = _classify(
        monkeypatch,
        inventory={"value_containment"},
        mutations=[_Mutation("generated_operand_exceeds_ceiling", ["value_containment"])],
        proven=set(),
        stale_tree_only=set(),
        failed_verification={
            "generated_operand_exceeds_ceiling": [
                "mutation proof 'generated_operand_exceeds_ceiling': baseline exited 1; "
                "Mandate 5 requires a clean control before a planted failure can prove anything."
            ]
        },
        never_run=[],
    )
    assert "unproven_assertion" not in families, (
        "a label whose mutation exists must never be reported as having none"
    )
    assert list(families) == ["proof_does_not_hold"]
    message = families["proof_does_not_hold"][0]
    # The fix must be stated, and the wrong fix must be ruled out by name.
    assert "generated_operand_exceeds_ceiling" in message
    assert "baseline exited 1" in message, "the actual rejection has to reach the reader"
    assert "Do NOT write another mutation" in message


def test_no_record_at_all_is_reported_as_never_executed(
        monkeypatch: pytest.MonkeyPatch) -> None:
    families = _classify(
        monkeypatch,
        inventory={"answer_key_recomputation"},
        mutations=[_Mutation("answer_recomputation_input_missing", ["answer_key_recomputation"])],
        proven=set(),
        stale_tree_only=set(),
        failed_verification={},
        never_run=["answer_recomputation_input_missing"],
    )
    assert list(families) == ["never_executed"]
    assert "--only answer_recomputation_input_missing" in families["never_executed"][0], (
        "the message has to carry the command that pays the debt"
    )


def test_a_label_nothing_claims_still_asks_for_a_mutation(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The original family must survive: an unclaimed label is a real hole."""
    families = _classify(
        monkeypatch,
        inventory={"orphan_label"},
        mutations=[],
        proven=set(),
        stale_tree_only=set(),
        failed_verification={},
        never_run=[],
    )
    assert list(families) == ["unproven_assertion"]
    assert "Write the mutation" in families["unproven_assertion"][0]


def test_never_executed_outranks_a_broken_sibling_proof(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Two mutations, one never run and one whose record fails. The never-run one is the
    cheaper fix and is reported first, so the reader is not sent to repair a control when
    simply running the other would settle the label.
    """
    families = _classify(
        monkeypatch,
        inventory={"shared_label"},
        mutations=[
            _Mutation("never_ran", ["shared_label"]),
            _Mutation("record_broken", ["shared_label"]),
        ],
        proven=set(),
        stale_tree_only=set(),
        failed_verification={"record_broken": ["records no baseline run."]},
        never_run=["never_ran"],
    )
    assert list(families) == ["never_executed"]


def test_a_proven_label_produces_no_error_at_all(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The positive control: none of the three families fires on a label that is proven."""
    families = _classify(
        monkeypatch,
        inventory={"value_containment"},
        mutations=[_Mutation("generated_operand_exceeds_ceiling", ["value_containment"])],
        proven={"value_containment"},
        stale_tree_only=set(),
        failed_verification={},
        never_run=[],
    )
    assert families == {}


def test_a_tree_moved_label_is_not_repeated_per_label(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """
    `stale_tree_only` is already stated once by `evaluate`. Repeating it here would bury
    the families above under one error per assertion in the corpus.
    """
    families = _classify(
        monkeypatch,
        inventory={"value_containment"},
        mutations=[_Mutation("generated_operand_exceeds_ceiling", ["value_containment"])],
        proven=set(),
        stale_tree_only={"value_containment"},
        failed_verification={},
        never_run=[],
    )
    assert families == {}
