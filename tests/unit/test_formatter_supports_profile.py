"""
test_formatter_supports_profile.py
===================================
Regression test for the v-final "Fractions DNA concept overridden"
false positives (1,080 violations across 6 nodes).

The audit's `formatter_supports_profile()` previously returned True
when `FORMATTER_VARIANT_SUPPORT[dna_name][formatter]` had no entry
(no formatter-specific caps). This meant the audit would request
combinations like (fractions, ordering) that the orchestrator would
reject at runtime (because 'ordering' is not in fractions'
compatible_formatters list).

The orchestrator actually picks 'comparing_ordering' for those
combinations, but the audit's `dna_name` fallback (to
`primary_concept = dna_names[0] = 'fractions'`) caused the Fractions
DNA check to fire as a false positive.

This test verifies the fix:
  1. formatter_supports_profile now rejects (fractions, ordering)
  2. formatter_supports_profile accepts (comparing_ordering, ordering)
  3. The orchestrator sets problem.dna_name to the actually-chosen DNA

Per AGENTS.md rule #4: the test is the regression net — if anyone
reverts the formatter_supports_profile fix, the Fractions DNA
violations will reappear and these tests will fail.
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)


class TestFormatterSupportsProfileGate1:
    """formatter_supports_profile must reject formatters not in the
    DNA's compatible_formatters list (matches orchestrator.py:125)."""

    def test_fractions_rejects_ordering(self):
        from tests.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert formatter_supports_profile("fractions", "ordering", {}) is False

    def test_fractions_rejects_sort_order(self):
        from tests.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert formatter_supports_profile("fractions", "sort_order", {}) is False

    def test_fractions_accepts_mcq(self):
        from tests.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert formatter_supports_profile("fractions", "mcq", {}) is True

    def test_fractions_accepts_cloze(self):
        from tests.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert formatter_supports_profile("fractions", "cloze", {}) is True

    def test_fractions_accepts_fraction_model_read(self):
        from tests.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert formatter_supports_profile(
            "fractions", "fraction_model_read", {}
        ) is True

    def test_comparing_ordering_accepts_ordering(self):
        from tests.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert (
            formatter_supports_profile("comparing_ordering", "ordering", {})
            is True
        )

    def test_addition_rejects_fraction_model_read(self):
        from tests.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert (
            formatter_supports_profile("addition", "fraction_model_read", {})
            is False
        )

    def test_unknown_dna_treated_as_no_formatter_constraint(self):
        # If the DNA isn't in COMPATIBILITY, gate 1 is skipped (dna_formatters
        # is empty) and the function falls through to gate 2 (the
        # FORMATTER_VARIANT_SUPPORT caps, which will also be empty for an
        # unknown DNA). Result: True (defensive: don't filter unknown DNAs).
        from tests.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert (
            formatter_supports_profile("nonexistent_dna", "any_formatter", {})
            is True
        )


class TestOrchestratorAnnotatesDnaName:
    """The orchestrator must set problem.dna_name to the actually-chosen DNA."""

    # These tests are about ONE property: when a node maps to several DNAs and the
    # requested formatter is supported by exactly one of them, the orchestrator's
    # runtime filter must skip the others and annotate the DNA it actually used.
    #
    # They kept rotting because they hardcoded a node. cc5977f5 repointed one onto
    # mat_g1_na_q1_6 and, per its own restored docstring, "deleted the only coverage of
    # the filter it exists to test"; it was restored onto mat_g2_na_q4_2, which has since
    # stopped supporting `ordering`; and mat_g1_na_q1_6 was rerouted to a single-DNA
    # concept on 2026-08-20, which broke the other two outright. A node id is not the
    # subject of these tests -- the filter is. So the subject is now LOCATED, not named.
    def test_orchestrator_annotates_the_only_dna_offering_the_formatter(self):
        """
        The cross-DNA formatter filter, asserted as an INVARIANT over every case where
        it is observable, rather than on a hardcoded node.

        Three separate tests used to pin this on named nodes and all three rotted:
        cc5977f5 repointed one onto mat_g1_na_q1_6 and, per its own restored docstring,
        "deleted the only coverage of the filter it exists to test"; it was restored onto
        mat_g2_na_q4_2, which has since stopped serving `ordering`; and mat_g1_na_q1_6
        was rerouted to a single-DNA concept on 2026-08-20, breaking the other two. A
        node id was never the subject -- the filter is.

        Observable means: the node maps to several DNAs, exactly one of them offers the
        formatter, and the orchestrator actually serves that combination. Whenever that
        holds, the DNA it annotates must be that sole owner.
        """
        from backend.app.services.orchestrator import PracticeOrchestrator
        from backend.app.practice_gen.registry import NODE_TO_DNA, get_node_formatters
        from backend.app.practice_gen.compatibility import COMPATIBILITY

        observed, mismatches = 0, []
        for node_id, dnas in NODE_TO_DNA.items():
            if len(dnas) < 2:
                continue
            try:
                formatters = get_node_formatters(node_id)
            except Exception:  # noqa: BLE001 - node advertises nothing; not this test's subject
                continue
            for fmt in formatters:
                owners = [d for d in dnas if fmt in COMPATIBILITY.get(d, [])]
                if len(owners) != 1:
                    continue
                try:
                    prob = PracticeOrchestrator.generate_problem(
                        node_id=node_id, seed=91000, formatter=fmt, is_lab=False,
                    )
                except Exception:  # noqa: BLE001 - see test_advertised_formatters_are_servable
                    continue
                observed += 1
                if prob.dna_name != owners[0]:
                    mismatches.append((node_id, fmt, owners[0], prob.dna_name))

        assert observed, (
            "no multi-DNA node currently serves a formatter offered by exactly one of "
            "its DNAs, so this invariant is vacuous -- that is itself a regression in "
            "coverage, not a pass"
        )
        assert not mismatches, (
            f"the orchestrator annotated a DNA that does not offer the requested "
            f"formatter in {len(mismatches)} case(s): {mismatches[:5]}"
        )

    def test_orchestrator_sets_dna_name_for_fractions_only(self):
        """
        The complementary case: when the formatter IS offered by the node's own DNA,
        the annotation must still be set to a real DNA rather than left None or a
        fallback. RESTORED 2026-08-19 (hardening Unit 1) alongside its siblings.
        """
        from backend.app.services.orchestrator import PracticeOrchestrator
        prob = PracticeOrchestrator.generate_problem(
            node_id="mat_g2_na_q4_2",
            seed=91000,
            difficulty_profile={
                "fraction_type": "unit_fraction",
                "number_difficulty": 0.5,
                "context": "pure",
            },
            formatter="mcq",
            is_lab=False,
        )
        assert prob.dna_name, f"dna_name was not annotated, got {prob.dna_name!r}"
        assert prob.dna_name in ("fractions", "comparing_ordering"), prob.dna_name
