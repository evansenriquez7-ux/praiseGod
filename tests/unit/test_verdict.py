"""
run_all's three exit codes (owner ruling 27, batch H2, 2026-10-09).

    0  integrity green and no content finding
    2  integrity green and content findings exist -- the generator work queue
    1  integrity failure, whatever the content

Every finding is classified by the assertion LABEL that reported it, through
`_manifest.FINDING_CLASS`. These tests drive the REAL `run_all` with every validator
stubbed (the `stubbed_harness` fixture from test_stage_ledger), so the control flow under
test is the production control flow, in seconds. Each `verdict_*` / `finding_*` label in
run_all.ASSERTIONS is proven by a mutation in tests/mutation_harness.py that plants into
that control flow and is caught here BY NAME.

The tests iterate FINDING_CLASS itself rather than a hand-picked sample of labels, so a
label added to the registry is exercised without editing this file (an allowlist drifts).

NAMED LIMIT: stubbed, so these prove the verdict's control flow, not that each real
validator prints the label its findings belong to. That half is measured on the full
run_all in the H2 evidence entry (HARDENING_EVIDENCE.md), and §8's
`assertion_undeclared_check_8` holds every literal `  FAIL <label>` site to the inventory.
"""

from __future__ import annotations

import pytest

from backend.app.practice_gen.validation import _manifest
from backend.app.practice_gen.validation import run_all as ra
from backend.app.practice_gen.validation import validate_capability as VC

from tests.unit.test_stage_ledger import stubbed_harness  # noqa: F401  (pytest fixture)


def _matrix_family(label: str) -> bool:
    """A label discovered from validate_matrix's check sites rather than printed."""
    from backend.app.practice_gen.validation import validate_coverage

    return label in validate_coverage.matrix_assertion_labels()


def _printed(label_class: str):
    """Every registry label of one class that a stage reports on a `  FAIL` line."""
    return sorted(lb for lb, cls in _manifest.FINDING_CLASS.items()
                  if cls == label_class and not _matrix_family(lb) and not lb.endswith("_"))


def _stage_prints(stubbed, *labels, ok=False):
    """Make the §2L stage print `  FAIL <label>` for each label and return `ok`."""
    def body(*_a, **_k):
        for label in labels:
            print(f"  FAIL {label} (1):")
            print("    - mat_test_lc: planted finding at seed 1")
        return ok
    stubbed.setattr(ra.validate_exhibit, "validate_all", body)


def _matrix_reports(stubbed, *checks):
    """Make the matrix stage fail with one structured finding per `check`."""
    stubbed.setattr(ra, "run_matrix_validation", lambda **kw: 1)
    stubbed.setattr(ra.validate_matrix, "LAST_FAILURES", [
        {"node_id": "mat_test_lc", "dna": "d", "formatter": "f", "check": c, "seed": 1,
         "error": "planted"} for c in checks])


# ─────────────────────────────────────────────────────────────────────────────
# finding_class_registry_complete
# ─────────────────────────────────────────────────────────────────────────────

def test_finding_class_registry_complete():
    """The live registry equals the live §8 inventory, both directions."""
    problems = ra.finding_class_registry_failures()
    assert not problems, (
        "finding_class_registry_complete: FINDING_CLASS and the §8 inventory disagree:\n  "
        + "\n  ".join(problems))


def test_a_registry_hole_is_an_integrity_failure(stubbed_harness, capsys):
    hole = dict(ra.FINDING_CLASS)
    del hole["variant_not_exhibited_2L"]
    stubbed_harness.setattr(ra, "FINDING_CLASS", hole)
    assert ra.run_all(phase=1) == 1
    out = capsys.readouterr().out
    assert "FAIL finding_class_registry_complete" in out
    assert "variant_not_exhibited_2L" in out


# ─────────────────────────────────────────────────────────────────────────────
# verdict_content_exits_2
# ─────────────────────────────────────────────────────────────────────────────

def test_the_stubbed_control_is_green(stubbed_harness):
    """Without this, every exit code below could be an artefact of the stub."""
    assert ra.run_all(phase=None) == 0


@pytest.mark.parametrize("phase", [1, None])
def test_verdict_content_exits_2(stubbed_harness, capsys, phase):
    """Every CONTENT label, reported alone, exits 2 -- not 1 and not 0."""
    wrong = []
    for label in _printed(_manifest.CONTENT):
        _stage_prints(stubbed_harness, label)
        code = ra.run_all(phase=phase)
        capsys.readouterr()
        if code != 2:
            wrong.append((label, code))
    for label in sorted(lb for lb, c in _manifest.FINDING_CLASS.items()
                        if c == _manifest.CONTENT and _matrix_family(lb)):
        stubbed_harness.setattr(ra.validate_exhibit, "validate_all", lambda **kw: True)
        _matrix_reports(stubbed_harness, f"{label}_planted_axis")
        code = ra.run_all(phase=phase)
        capsys.readouterr()
        if code != 2:
            wrong.append((f"matrix:{label}", code))
        stubbed_harness.setattr(ra, "run_matrix_validation", lambda **kw: 0)
        stubbed_harness.setattr(ra.validate_matrix, "LAST_FAILURES", [])
    assert not wrong, (
        f"verdict_content_exits_2: these CONTENT labels, reported alone, did not exit 2 "
        f"(phase={phase}): {wrong}")


def test_a_content_finding_from_a_stage_that_returned_true_still_counts(
        stubbed_harness, capsys):
    """H1's named limit on `stage_failure_reaches_verdict`, closed: what a stage PRINTS
    is read, so returning True cannot hide a finding it reported."""
    _stage_prints(stubbed_harness, "variant_not_exhibited_2L", ok=True)
    assert ra.run_all(phase=1) == 2
    assert "variant_not_exhibited_2L (stage variant_exhibit_2L)" in capsys.readouterr().out


# ─────────────────────────────────────────────────────────────────────────────
# verdict_integrity_exits_1
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("phase", [1, None])
def test_verdict_integrity_exits_1(stubbed_harness, capsys, phase):
    """Every INTEGRITY label exits 1 -- including when content findings sit beside it,
    which is exactly where an integrity failure can hide in the content report."""
    wrong = []
    for label in _printed(_manifest.INTEGRITY):
        _stage_prints(stubbed_harness, "variant_not_exhibited_2L", label)
        code = ra.run_all(phase=phase)
        capsys.readouterr()
        if code != 1:
            wrong.append((label, code))
    _stage_prints(stubbed_harness, "variant_not_exhibited_2L")
    _matrix_reports(stubbed_harness, "worker_crash")
    code = ra.run_all(phase=phase)
    capsys.readouterr()
    if code != 1:
        wrong.append(("matrix:worker_crash", code))
    assert not wrong, (
        f"verdict_integrity_exits_1: these INTEGRITY labels, reported beside a content "
        f"finding, did not exit 1 (phase={phase}): {wrong}")


def test_a_crashed_stage_beside_content_exits_1(stubbed_harness, capsys):
    _stage_prints(stubbed_harness, "variant_not_exhibited_2L")

    def boom():
        raise RuntimeError("planted crash")

    stubbed_harness.setattr(ra.validate_render, "validate_all", boom)
    assert ra.run_all(phase=1) == 1
    assert "INTEGRITY FAILURE (exit 1)" in capsys.readouterr().out


# ─────────────────────────────────────────────────────────────────────────────
# finding_label_unclassified
# ─────────────────────────────────────────────────────────────────────────────

def test_an_unclassified_printed_label_is_integrity(stubbed_harness, capsys):
    _stage_prints(stubbed_harness, "a_label_nobody_classified")
    assert ra.run_all(phase=1) == 1
    out = capsys.readouterr().out
    assert "FAIL finding_label_unclassified" in out
    assert "a_label_nobody_classified" in out


def test_a_misspelt_family_member_is_not_quietly_content(stubbed_harness, capsys):
    """Prefix matching is for matrix families only: a printed label that merely STARTS
    with a content label is unclassified, not content."""
    _stage_prints(stubbed_harness, "variant_not_exhibited_2L_typo")
    assert ra.run_all(phase=1) == 1
    assert "FAIL finding_label_unclassified" in capsys.readouterr().out


def test_an_unclassified_matrix_check_is_integrity(stubbed_harness, capsys):
    _matrix_reports(stubbed_harness, "a_check_nobody_classified")
    assert ra.run_all(phase=1) == 1
    assert "a_check_nobody_classified" in capsys.readouterr().out


def test_a_matrix_family_resolves_to_its_longest_key():
    assert _manifest.finding_class("window_containment_0.5_range", family=True) == "content"
    assert _manifest.finding_class("scalar_exactness_1.0_exceed_max", family=True) == "content"
    assert _manifest.finding_class("stage_crashed_dna") == "integrity"
    assert _manifest.finding_class("window_containment_0.5_range") is None


# ─────────────────────────────────────────────────────────────────────────────
# §6: integrity and content inside ONE stage, told apart by emitting function
# ─────────────────────────────────────────────────────────────────────────────

def _tagged_phase1(stubbed, tagged):
    stubbed.setattr(ra.validate_capability, "provision_findings_tagged",
                    lambda node_ids=None: list(tagged))


def test_capability_content_within_the_floor_passes(stubbed_harness):
    _tagged_phase1(stubbed_harness, [(VC.CONTENT_ROLLUP, f"mat_x: gap {i}")
                                     for i in range(VC._PROVISION_FLOOR)])
    assert ra.run_all(phase=1) == 0


def test_capability_content_over_the_floor_exits_2(stubbed_harness, capsys):
    _tagged_phase1(stubbed_harness, [(VC.CONTENT_ROLLUP, f"mat_x: gap {i}")
                                     for i in range(VC._PROVISION_FLOOR + 1)])
    assert ra.run_all(phase=1) == 2
    assert "FAIL capability_contract" in capsys.readouterr().out


@pytest.mark.parametrize("label", ["requires_ignore_locked_6B",
                                   "capability_declarations_in_sync_6",
                                   "capability_provenance_6A", "capability_coverage_6B",
                                   "capability_phase_boundary_6",
                                   "capability_phase_partition_6"])
def test_a_capability_integrity_finding_is_not_absorbed_by_the_floor(
        stubbed_harness, capsys, label):
    """One integrity finding plus content well inside the floor: still exit 1."""
    _tagged_phase1(stubbed_harness, [(VC.CONTENT_ROLLUP, "mat_x: a gap"),
                                     (label, "mat_x: planted")])
    assert ra.run_all(phase=1) == 1
    assert f"FAIL {label}" in capsys.readouterr().out


def test_capability_phase2_content_exits_2_and_partition_exits_1(stubbed_harness, capsys):
    stubbed_harness.setattr(ra.validate_capability, "attestation_findings_tagged",
                            lambda node_ids=None: [(VC.CONTENT_ROLLUP, "mat_x: CONTRADICTED")])
    assert ra.run_all(phase=2) == 2
    capsys.readouterr()
    stubbed_harness.setattr(ra.validate_capability, "attestation_findings_tagged",
                            lambda node_ids=None: [(VC.CONTENT_ROLLUP, "mat_x: CONTRADICTED"),
                                                   ("capability_phase_partition_6", "x")])
    assert ra.run_all(phase=2) == 1
