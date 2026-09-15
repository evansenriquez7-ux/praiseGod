"""
The proof consumer, tested against isolated proof fixtures.

`validate_coverage` now counts an assertion proven only when an EXECUTED mutation left a
proof record that still holds. That makes `mutation_proof.verify_proof` the gate behind
every other gate's claim to be proven — so it gets the same treatment it exists to impose:
every way a record can fail to be evidence is planted here and asserted to be caught by
name.

Nothing in this file touches `validation_reports/mutation_proofs/`. Every test builds its
own proof directory and its own fingerprint roots in `tmp_path`, so the suite is safe to
run concurrently with a real mutation run and cannot be made to pass by the state of the
repository's own proofs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.practice_gen.validation import mutation_proof as mp


class _FakeMutation:
    """The attribute surface `definition_digest` and `verify_proof` actually read."""

    def __init__(self, name="planted", asserts=("some_label",), command=("mod", "--node", "n"),
                 expect=("marker",), baseline=("marker",), edits=None):
        self.name = name
        self.asserts = list(asserts)
        self.command = list(command)
        self.expected_check = "§X (the check under test)"
        self.expect_output_contains = list(expect)
        self.baseline_must_not_contain = list(baseline)
        self.edits = edits or {"backend/app/x.py": ("find", "replace")}
        self.apply_fn = None


def _record(mutation: _FakeMutation, digest: str, **overrides):
    rec = {
        "schema_version": mp.SCHEMA_VERSION,
        "mutation": mutation.name,
        "definition_digest": mp.definition_digest(mutation),
        "asserts": sorted(mutation.asserts),
        "command": list(mutation.command),
        "expected_check": mutation.expected_check,
        "expect_output_contains": list(mutation.expect_output_contains),
        "baseline_must_not_contain": list(mutation.baseline_must_not_contain),
        "baseline_exit": 0,
        "baseline_markers_already_present": [],
        "planted_exit": 1,
        "observed_markers": {m: True for m in mutation.expect_output_contains},
        "diagnostic_line": "exit 1 —   FAIL some_label (1)",
        "detected": True,
        "mutated_paths": ["backend/app/x.py"],
        "restored_clean": True,
        "environment": {"python": "3.12.13"},
        "started_at": "2026-09-12T04:00:00+08:00",
        "finished_at": "2026-09-12T04:01:00+08:00",
        "input_digest": digest,
        "phase1_admissible": True,
        "paths_outside_input_set": [],
    }
    rec.update(overrides)
    return rec


@pytest.fixture
def proof_dir(tmp_path, monkeypatch):
    d = tmp_path / "mutation_proofs"
    d.mkdir()
    monkeypatch.setattr(mp, "PROOF_DIR", d)
    return d


def _file(proof_dir: Path, rec: dict) -> Path:
    path = proof_dir / f"{rec['mutation']}.json"
    path.write_text(json.dumps(rec), encoding="utf-8")
    return path


def _errs(rec, mutation, digest="D", **kw):
    return mp.verify_proof(rec, mutation, digest, **kw)


# ─── the happy path, so every rejection below is a real discrimination ────────


def test_a_complete_current_detected_record_verifies():
    m = _FakeMutation()
    assert _errs(_record(m, "D"), m) == []


def test_proven_labels_reads_the_record(proof_dir, monkeypatch):
    m = _FakeMutation()
    monkeypatch.setattr(mp, "input_digest", lambda manifest=None: "D")
    _file(proof_dir, _record(m, "D"))
    proven, errors = mp.proven_labels([m])
    assert proven == {"some_label"}
    assert errors == []


# ─── deletion of a result ────────────────────────────────────────────────────


def test_a_deleted_proof_proves_nothing_and_is_not_an_error(proof_dir, monkeypatch):
    m = _FakeMutation()
    monkeypatch.setattr(mp, "input_digest", lambda manifest=None: "D")
    proven, errors = mp.proven_labels([m])
    assert proven == set()
    assert errors == []          # "never run" is the inventory's finding, not this one


# ─── changed sources / fixtures ──────────────────────────────────────────────


def test_a_changed_input_tree_makes_the_proof_stale():
    m = _FakeMutation()
    errs = _errs(_record(m, "OLD-DIGEST"), m, digest="NEW-DIGEST")
    assert any("STALE" in e and "source/fixture tree has changed" in e for e in errs)


def test_the_input_digest_moves_when_any_input_file_moves(tmp_path, monkeypatch):
    root = tmp_path / "fixtures"
    (root / "sub").mkdir(parents=True)
    (root / "sub" / "a.py").write_text("one", encoding="utf-8")
    monkeypatch.setattr(mp, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(mp, "INPUT_ROOTS", ("fixtures",))

    before = mp.input_digest()
    (root / "sub" / "a.py").write_text("two", encoding="utf-8")
    after_edit = mp.input_digest()
    (root / "sub" / "b.py").write_text("new file", encoding="utf-8")
    after_add = mp.input_digest()

    assert before != after_edit, "an edited input must invalidate every proof"
    assert after_edit != after_add, "an ADDED untracked input must invalidate them too"


def test_compiled_and_cache_files_are_not_inputs(tmp_path, monkeypatch):
    root = tmp_path / "fixtures"
    (root / "__pycache__").mkdir(parents=True)
    (root / "a.py").write_text("one", encoding="utf-8")
    monkeypatch.setattr(mp, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(mp, "INPUT_ROOTS", ("fixtures",))
    before = mp.input_digest()
    (root / "__pycache__" / "a.cpython-312.pyc").write_bytes(b"\x00bytecode")
    (root / "a.pyc").write_bytes(b"\x00bytecode")
    assert mp.input_digest() == before


# ─── changed mutation definitions ────────────────────────────────────────────


def test_a_changed_definition_makes_the_proof_stale():
    m = _FakeMutation()
    rec = _record(m, "D")
    moved = _FakeMutation(command=("mod", "--node", "a-different-node"))
    errs = _errs(rec, moved)
    assert any("definition has changed" in e for e in errs)


def test_a_changed_plant_makes_the_proof_stale():
    m = _FakeMutation()
    rec = _record(m, "D")
    replanted = _FakeMutation(edits={"backend/app/x.py": ("find", "something else entirely")})
    assert any("definition has changed" in e for e in _errs(rec, replanted))


def test_apply_fn_source_is_part_of_the_definition():
    m = _FakeMutation()
    m.edits = {}
    m.apply_fn = lambda: {}
    first = mp.definition_digest(m)
    m.apply_fn = lambda: {"a": "b"}          # a different plant, same signature
    assert mp.definition_digest(m) != first


# ─── wrong failure labels ────────────────────────────────────────────────────


def test_a_proof_carrying_the_wrong_label_is_rejected():
    m = _FakeMutation()
    rec = _record(m, "D", asserts=["a_label_the_table_no_longer_claims"])
    # The definition digest moves with `asserts`, so both directions report; the label
    # mismatch must be named in its own right rather than hidden behind the staleness.
    assert any("the label a proof carries must be the label the table claims" in e.lower()
               for e in _errs(rec, m))


def test_an_expected_marker_that_was_not_observed_is_rejected():
    m = _FakeMutation()
    rec = _record(m, "D", observed_markers={"marker": False})
    assert any("were NOT observed" in e for e in _errs(rec, m))


def test_a_declared_marker_with_no_observation_is_rejected():
    m = _FakeMutation(expect=("marker", "second marker"))
    rec = _record(m, "D", observed_markers={"marker": True})
    assert any("carry no observation" in e for e in _errs(rec, m))


def test_a_survived_mutation_proves_nothing():
    m = _FakeMutation()
    rec = _record(m, "D", detected=False, planted_exit=0,
                  diagnostic_line="SURVIVED — validator exited 0 with the bug planted.")
    errs = _errs(rec, m)
    assert any("NOT DETECTED" in e for e in errs)
    assert any("SURVIVED" in e for e in errs)


def test_an_invalid_baseline_result_proves_nothing():
    """The runner's INVALID verdict: the tree already reported the marker."""
    m = _FakeMutation()
    rec = _record(m, "D", detected=False, planted_exit=None,
                  baseline_markers_already_present=["marker"],
                  diagnostic_line="INVALID — the unmutated tree already reports ['marker']")
    assert any("NOT DETECTED" in e for e in _errs(rec, m))


def test_a_mutation_with_baseline_markers_and_no_baseline_run_is_rejected():
    m = _FakeMutation()
    rec = _record(m, "D", baseline_exit=None)
    assert any("records no baseline run" in e for e in _errs(rec, m))


def test_a_red_baseline_cannot_prove_a_mutation():
    m = _FakeMutation()
    rec = _record(m, "D", baseline_exit=1)
    assert any("baseline exited 1" in e for e in _errs(rec, m))


# ─── dirty-tree edits and restoration ────────────────────────────────────────


def test_an_unrestored_tree_invalidates_the_proof():
    m = _FakeMutation()
    rec = _record(m, "D", restored_clean=False)
    assert any("could not confirm it restored" in e for e in _errs(rec, m))


def test_a_proof_bound_to_paths_outside_the_input_set_is_not_phase1_admissible():
    m = _FakeMutation()
    rec = _record(m, "D", phase1_admissible=False,
                  paths_outside_input_set=["validation_reports/judgment/x/y.json"],
                  mutated_paths=["validation_reports/judgment/x/y.json"])
    errs = _errs(rec, m)
    assert any("NOT PHASE-1 ADMISSIBLE" in e for e in errs)
    # ...and it is still admissible evidence for a caller that says so explicitly.
    assert _errs(rec, m, require_phase1_admissible=False) == []


def test_paths_outside_input_set_is_computed_from_the_real_roots():
    assert mp.paths_outside_input_set(["backend/app/services/orchestrator.py"]) == []
    assert mp.paths_outside_input_set(["tests/unit/test_mutation_proof.py"]) == []
    assert mp.paths_outside_input_set(
        ["validation_reports/judgment/mat_g1_na_q1/mat_g1_na_q1_0.json"]
    ) == ["validation_reports/judgment/mat_g1_na_q1/mat_g1_na_q1_0.json"]


# ─── partial, malformed and interrupted records ──────────────────────────────


@pytest.mark.parametrize("field", sorted(mp.REQUIRED_FIELDS))
def test_every_required_field_is_required(field):
    m = _FakeMutation()
    rec = _record(m, "D")
    rec.pop(field)
    errs = _errs(rec, m)
    assert errs, f"a record missing {field!r} must not verify"
    if field != "mutation":
        assert any("PARTIAL" in e for e in errs)


def test_an_unsupported_schema_version_is_rejected():
    m = _FakeMutation()
    rec = _record(m, "D", schema_version=mp.SCHEMA_VERSION + 1)
    assert any("schema_version" in e for e in _errs(rec, m))


def test_an_interrupted_write_is_reported_not_ignored(proof_dir):
    (proof_dir / "planted.json.tmp").write_text("{", encoding="utf-8")
    _proofs, errors = mp.load_proofs()
    assert any("unfinished write" in e for e in errors)


def test_malformed_json_is_reported(proof_dir):
    (proof_dir / "planted.json").write_text("{not json", encoding="utf-8")
    _proofs, errors = mp.load_proofs()
    assert any("not valid JSON" in e for e in errors)


def test_a_proof_filed_under_the_wrong_name_is_rejected(proof_dir):
    (proof_dir / "planted.json").write_text(
        json.dumps({"mutation": "some_other_mutation"}), encoding="utf-8")
    proofs, errors = mp.load_proofs()
    assert proofs == {}
    assert any("must be filed under the name of the mutation" in e for e in errors)


def test_an_orphaned_proof_names_the_missing_mutation():
    m = _FakeMutation()
    errs = _errs(_record(m, "D"), None)
    assert any("no mutation of that name is registered" in e for e in errs)


def test_proven_labels_drops_a_label_whose_proof_fails(proof_dir, monkeypatch):
    m = _FakeMutation()
    monkeypatch.setattr(mp, "input_digest", lambda manifest=None: "D")
    _file(proof_dir, _record(m, "D", detected=False, planted_exit=0))
    proven, errors = mp.proven_labels([m])
    assert proven == set()
    assert errors


# ─── the write path ──────────────────────────────────────────────────────────


def test_write_proof_is_atomic_and_leaves_no_temp(proof_dir):
    m = _FakeMutation()
    path = mp.write_proof(_record(m, "D"))
    assert path.exists()
    assert list(proof_dir.glob("*.tmp")) == []
    assert json.loads(path.read_text(encoding="utf-8"))["mutation"] == "planted"
