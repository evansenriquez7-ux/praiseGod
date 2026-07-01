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
        from local_only.scratch.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert formatter_supports_profile("fractions", "ordering", {}) is False

    def test_fractions_rejects_sort_order(self):
        from local_only.scratch.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert formatter_supports_profile("fractions", "sort_order", {}) is False

    def test_fractions_accepts_mcq(self):
        from local_only.scratch.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert formatter_supports_profile("fractions", "mcq", {}) is True

    def test_fractions_accepts_cloze(self):
        from local_only.scratch.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert formatter_supports_profile("fractions", "cloze", {}) is True

    def test_fractions_accepts_fraction_model_read(self):
        from local_only.scratch.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert formatter_supports_profile(
            "fractions", "fraction_model_read", {}
        ) is True

    def test_comparing_ordering_accepts_ordering(self):
        from local_only.scratch.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert (
            formatter_supports_profile("comparing_ordering", "ordering", {})
            is True
        )

    def test_addition_rejects_fraction_model_read(self):
        from local_only.scratch.exhaustive_checklist_auditor import (
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
        from local_only.scratch.exhaustive_checklist_auditor import (
            formatter_supports_profile,
        )
        assert (
            formatter_supports_profile("nonexistent_dna", "any_formatter", {})
            is True
        )


class TestOrchestratorAnnotatesDnaName:
    """The orchestrator must set problem.dna_name to the actually-chosen DNA."""

    def test_orchestrator_sets_dna_name_for_ordering(self):
        from backend.app.services.orchestrator import PracticeOrchestrator
        prob = PracticeOrchestrator.generate_problem(
            node_id="mat_g1_na_q4_1",
            seed=91000,
            difficulty_profile={
                "fraction_type": "proper",
                "operation": "add",
                "fraction_model": "area_model",
                "number_difficulty": 0.5,
                "context": "pure",
            },
            formatter="ordering",
            is_lab=False,
        )
        # ordering is not in fractions' compatible_formatters, so the
        # orchestrator must have picked 'comparing_ordering'.
        assert prob.dna_name == "comparing_ordering", (
            f"Expected dna_name=comparing_ordering, got {prob.dna_name!r}. "
            f"The orchestrator's runtime filter at orchestrator.py:125 should "
            f"have skipped 'fractions' for formatter='ordering'."
        )

    def test_orchestrator_sets_dna_name_for_fractions_only(self):
        from backend.app.services.orchestrator import PracticeOrchestrator
        # When the formatter is in fractions' compatible_formatters, the
        # orchestrator may still pick the other DNA. We just need to verify
        # the annotation is set (not None and not the fallback).
        prob = PracticeOrchestrator.generate_problem(
            node_id="mat_g1_na_q4_1",
            seed=91000,
            difficulty_profile={
                "fraction_type": "proper",
                "operation": "add",
                "fraction_model": "area_model",
                "number_difficulty": 0.5,
                "context": "pure",
            },
            formatter="cloze",
            is_lab=False,
        )
        assert prob.dna_name is not None
        assert prob.dna_name in ("fractions", "comparing_ordering")
