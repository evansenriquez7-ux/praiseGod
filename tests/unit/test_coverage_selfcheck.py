"""
§8's own bookkeeping directions, driven against a STUBBED proof state (2026-09-17).

Why these are unit tests and not only a live mutation
-----------------------------------------------------
Eight mutations in `tests/mutation_harness.py` plant a violation into real source and ask
`validate_coverage` to name it. Their live catcher is `validate_coverage` itself, whose
baseline exits 1 -- so every one of them scored INVALID rather than DETECTED, and the
runner was right to refuse them (Mandate 5: a planted failure proves nothing without a
clean control).

That red is a SELF-REFERENCE DEADLOCK, and it does not dissolve by re-running: §8 is red
because these labels are unproven, and these labels are unproven because §8 is red. The
documented delete-and-rerun remedy was executed on 2026-09-16 and 3 of 4 attempts stayed
INVALID.

Measured on 2026-09-17 on `15f5b2fc`, the red is confined to ONE thing -- the executed
proof corpus. Of the eight error families `validate_coverage_tagged` can emit, the three
proof-state families carried all 10 errors and the five bookkeeping families carried zero:

    $ ... validate_coverage_tagged() with `_proof_state` stubbed
      errors under stub: 0
      families: {}

So this module stubs exactly one thing -- `_proof_state`, replaced by "assume every
mutation's claim holds" -- and drives the REAL `validate_coverage_tagged` over the REAL
tree. The plant still lands in real source and still has to travel the real code path;
what the stub removes is only the unrelated execution debt that was masking it.

WHAT THIS TRADES, AND IT IS A REAL TRADE
----------------------------------------
These prove the bookkeeping directions against a coverage state in which proof records are
ASSUMED CURRENT. They do NOT prove §8's execution accounting -- that a record which fails
verification is reported, that a stale digest is caught per label, that `never_executed`
and `proof_does_not_hold` are told apart. Those three families are stubbed out here and
remain provable only against a green live corpus, which is what the §6F cluster is waiting
on. This is the same trade H-03's contract row already names for the stage-ledger
mutations: "proved against the real gate" is exchanged for "proved at all".

NOT ONE TEST HERE READS THE LIVE PROOF CORPUS, AND THAT IS LOAD-BEARING
-----------------------------------------------------------------------
The obvious eighth test -- "the corpus on disk is current" -- was written first and then
deleted, because it rebuilds the very deadlock this module exists to break. `tree_moved`
is True when ANY record is stale, so during the ~70-minute table run the corpus is
legitimately mixed (records from the previous run have not been overwritten yet) and that
test fails. `pytest` then exits 1, and EVERY mutation whose command is this module gets a
red baseline and scores INVALID again. Measured 2026-09-17: creating this very file moved
the digest and turned that test red, exactly as trap 9 says it should.

So `source_edited_without_reproof` is proved here through the MECHANISM instead -- a
synthetic record carrying a digest that does not match, which `verify_proof` must reject
as STALE. Its mutation plants into that comparison rather than into a source file.

NAMED LIMIT: a test asserting the live tree is clean catches a planted violation, and it
catches a BROKEN check only through the mutation that plants one. Read together with
`TestTheChecksHaveTeeth` below, which builds each violation synthetically so the module
cannot pass by checking nothing.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Set, Tuple

import pytest

from backend.app.practice_gen.validation import mutation_proof
from backend.app.practice_gen.validation import validate_coverage as vc


def _stubbed_proof_state() -> Dict[str, object]:
    """
    The coverage state §8 would see if every mutation's claim held.

    `proven` is `declared_assertions()` -- what the table CLAIMS -- which is precisely the
    thing §8 refuses to count as evidence. That refusal is the point of the gate and is
    NOT under test here; it is stubbed so the bookkeeping directions underneath it become
    reachable. See the module docstring's trade.
    """
    return {
        "proven": set(vc.declared_assertions()),
        "errors": [],
        "tree_moved": False,
        "stale_tree_only": set(),
        "failed_verification": {},
        "records": {},
    }


def _synthetic_mutation():
    """A registered mutation for the synthetic record to belong to.

    Without one, `verify_proof` short-circuits on "no mutation of that name is registered"
    and never reaches the digest comparison -- which would make the staleness test below
    pass against a check that had been removed entirely.
    """
    from tests.mutation_harness import Mutation

    return Mutation(
        name="synthetic",
        description="synthetic fixture, never planted",
        edits={},
        command=["true"],
        expected_check="synthetic",
        asserts=["synthetic_label"],
        expect_output_contains=["marker"],
        baseline_must_not_contain=["marker"],
    )


def _synthetic_record(**overrides) -> Dict[str, object]:
    """
    A complete, otherwise-valid proof record. Every REQUIRED_FIELD is present so that a
    rejection can only come from the field under test -- a record missing a field returns
    PARTIAL and short-circuits, which would make a staleness test pass for the wrong
    reason.
    """
    record: Dict[str, object] = {
        "schema_version": mutation_proof.SCHEMA_VERSION,
        "mutation": "synthetic",
        "definition_digest": "0" * 64,
        "asserts": ["synthetic_label"],
        "command": ["true"],
        "expect_output_contains": ["marker"],
        "baseline_must_not_contain": ["marker"],
        "baseline_exit": 0,
        "planted_exit": 1,
        "observed_markers": {"marker": True},
        "diagnostic_line": "synthetic",
        "detected": True,
        "mutated_paths": ["backend/app/practice_gen/dna/base.py"],
        "input_digest": "0" * 64,
        "environment": {},
        "restored_clean": True,
        "started_at": "2026-09-17T00:00:00+08:00",
        "finished_at": "2026-09-17T00:00:01+08:00",
        "phase1_admissible": True,
        "paths_outside_input_set": [],
    }
    record.update(overrides)
    return record


@pytest.fixture
def tagged(monkeypatch) -> List[Tuple[str, str]]:
    """The real `validate_coverage_tagged`, over the real tree, minus the execution debt."""
    monkeypatch.setattr(vc, "_proof_state", _stubbed_proof_state, raising=True)
    return vc.validate_coverage_tagged()


def _of(tagged: List[Tuple[str, str]], family: str) -> List[str]:
    return [msg for msg, fam in tagged if fam == family]


class TestTheLiveTreeUnderAStubbedProofState:
    """One test per bookkeeping direction. Each is the baseline a mutation plants against."""

    def test_the_allowlist_holds_no_paid_debt(self, tagged):
        # `allowlist_keeps_a_paid_debt`: an entry left on UNPROVEN_ASSERTIONS after its
        # mutation was written overstates the deficit and makes the register unreadable.
        paid = _of(tagged, "allowlist_paid")
        assert paid == [], "\n".join(paid)

    def test_the_allowlist_names_no_phantom_label(self, tagged):
        # `allowlist_names_a_phantom_label`: an entry naming a label nothing emits excuses
        # nothing while reading as accounted-for debt. Two of this shape were found live.
        phantom = _of(tagged, "allowlist_phantom")
        assert phantom == [], "\n".join(phantom)

    def test_every_assertion_is_proven_or_excused(self, tagged):
        # `coverage_map_gap`: a label removed from the allowlist with no mutation written
        # must be reported as neither proven nor excused.
        unproven = _of(tagged, "unproven_assertion")
        assert unproven == [], "\n".join(unproven)

    def test_no_mutation_asserts_a_label_nothing_declares(self, tagged):
        # `mutation_asserts_an_unknown_label`: `Mutation.asserts` is free text, so a typo
        # marks a phantom label proven while the real one falls back into the unproven set.
        unknown = _of(tagged, "asserts_unknown")
        assert unknown == [], "\n".join(unknown)

    def test_every_contract_check_declares_the_phase_it_runs_in(self, tagged):
        # `contract_check_declares_no_phase`: a ref with no phase is omitted from EVERY
        # band, and the two-direction tripwire still passes. 28 of 35 refs were once here.
        phase = _of(tagged, "phase_registry")
        assert phase == [], "\n".join(phase)

    def test_every_printed_fail_label_is_declared(self, tagged):
        # `undeclared_check_reports_itself`: a check that prints its own FAIL without
        # declaring the label is one §8 cannot tell you is unproven.
        undeclared = _of(tagged, "undeclared_check") + _of(tagged, "printed_scan")
        assert undeclared == [], "\n".join(undeclared)

    def test_every_silent_handler_carries_a_disposition(self):
        # `silent_handler_without_a_disposition`. Not proof-state dependent, so it needs
        # no stub -- it is here because it is the eighth member of the same cluster and
        # was blocked by the same red baseline.
        silent = vc.silent_path_failures()
        assert silent == [], "\n".join(silent)

    def test_a_proof_from_a_different_tree_is_rejected(self):
        # `source_edited_without_reproof`: a record taken on other bytes describes what no
        # longer runs. Synthetic rather than live -- see the module docstring for why a
        # live-corpus assertion here would re-poison every baseline in this file.
        mutation = _synthetic_mutation()
        record = _synthetic_record(
            input_digest="a" * 64,
            definition_digest=mutation_proof.definition_digest(mutation),
        )
        errs = mutation_proof.verify_proof(record, mutation, "b" * 64)
        assert any("the source/fixture tree has changed" in e for e in errs), errs


class TestTheChecksHaveTeeth:
    """
    Synthetic violations, so the suite above cannot pass by checking nothing.

    The tests above assert the live tree is clean; on their own they would also pass if a
    check stopped emitting entirely. These build each violation by hand and require the
    REAL check to name it. A mutation that disables a check is therefore caught here even
    when it plants no live violation.
    """

    def _tagged_with(self, monkeypatch, *, allowlist=None, declared=None,
                     inventory=None, printed=None) -> List[Tuple[str, str]]:
        monkeypatch.setattr(vc, "_proof_state", _stubbed_proof_state, raising=True)
        if allowlist is not None:
            monkeypatch.setattr(vc, "UNPROVEN_ASSERTIONS", allowlist, raising=True)
        if declared is not None:
            monkeypatch.setattr(vc, "declared_assertions", lambda: set(declared), raising=True)
        if inventory is not None:
            monkeypatch.setattr(vc, "harness_assertion_labels", lambda: set(inventory),
                                raising=True)
        if printed is not None:
            monkeypatch.setattr(vc, "printed_check_labels", lambda: (printed, []), raising=True)
        return vc.validate_coverage_tagged()

    def test_a_paid_debt_on_the_allowlist_is_named(self, monkeypatch):
        tagged = self._tagged_with(
            monkeypatch,
            allowlist={"planted_paid": "planted: a mutation now proves this"},
            declared={"planted_paid"},
            inventory={"planted_paid"},
            printed={},
        )
        assert "planted_paid" in "\n".join(_of(tagged, "allowlist_paid"))

    def test_a_phantom_allowlist_entry_is_named(self, monkeypatch):
        tagged = self._tagged_with(
            monkeypatch,
            allowlist={"planted_phantom": "planted: nothing emits this"},
            declared=set(),
            inventory={"a_real_label"},
            printed={},
        )
        assert "planted_phantom" in "\n".join(_of(tagged, "allowlist_phantom"))

    def test_an_unproven_unexcused_assertion_is_named(self, monkeypatch):
        tagged = self._tagged_with(
            monkeypatch,
            allowlist={},
            declared=set(),
            inventory={"planted_orphan"},
            printed={},
        )
        assert "planted_orphan" in "\n".join(_of(tagged, "unproven_assertion"))

    def test_a_mutation_asserting_an_unknown_label_is_named(self, monkeypatch):
        tagged = self._tagged_with(
            monkeypatch,
            allowlist={},
            declared={"planted_typo"},
            inventory={"a_real_label"},
            printed={},
        )
        assert "planted_typo" in "\n".join(_of(tagged, "asserts_unknown"))

    def test_an_undeclared_printed_check_is_named(self, monkeypatch):
        tagged = self._tagged_with(
            monkeypatch,
            allowlist={},
            declared=set(),
            inventory={"a_real_label"},
            printed={"planted_undeclared": ["validate_planted.py"]},
        )
        assert "planted_undeclared" in "\n".join(_of(tagged, "undeclared_check"))

    def test_a_check_with_no_declared_phase_is_named(self, monkeypatch):
        from backend.app.practice_gen.validation import _manifest

        pruned = {ref: phase for ref, phase in _manifest.CHECK_PHASE.items() if ref != "§9"}
        monkeypatch.setattr(_manifest, "CHECK_PHASE", pruned, raising=True)
        failures = vc.check_phase_registry_failures()
        assert "§9" in "\n".join(failures), failures

    def test_a_matching_digest_is_not_reported_as_stale(self):
        # The control for `test_a_proof_from_a_different_tree_is_rejected`: without it that
        # test would pass against a check that called EVERY record stale.
        mutation = _synthetic_mutation()
        record = _synthetic_record(
            input_digest="a" * 64,
            definition_digest=mutation_proof.definition_digest(mutation),
        )
        errs = mutation_proof.verify_proof(record, mutation, "a" * 64)
        assert errs == [], errs
