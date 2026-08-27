"""
The mutation harness must never leave a planted bug in the tree.

Why this file exists
--------------------
`run_mutation` restored in a `finally`, which covers exceptions and clean exits and
nothing else. On 2026-08-26 a 10-minute tool timeout sent SIGTERM mid-mutation, the
`finally` never ran, and `backend/app/services/orchestrator.py` was left carrying
`if formatter == 'true_false': valid_dnas = []`. It had to be restored from git by hand.

A harness that plants bugs in real source is the one thing that must not be able to
leave one behind: the next run would measure a tree it silently corrupted, and every
result would look like a genuine finding.

Three layers cover what the others cannot -- signal handlers (timeout, Ctrl-C), atexit
(any other shutdown), and an on-disk marker holding the ORIGINAL text (SIGKILL, OOM,
power loss, where no handler runs at all). This pins the third, because it is the only
one that survives a kill the process cannot observe.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _harness():
    """
    Plain import, not spec_from_file_location.

    The harness defines `@dataclass class Mutation`, and dataclasses resolves a class's
    module through sys.modules -- loading by path leaves that unset and every field
    raises AttributeError. `tests.mutation_harness` is a real importable module
    (validate_census imports it the same way), so use it.
    """
    from tests import mutation_harness

    return mutation_harness


@pytest.fixture
def scratch_target(tmp_path):
    """A throwaway file standing in for planted pipeline source."""
    f = tmp_path / "planted_source.py"
    f.write_text("ORIGINAL = 1\n", encoding="utf-8")
    return f


def test_orphaned_mutation_is_recovered_before_anything_else(scratch_target):
    """A marker left by a killed run must be replayed, and then cleared."""
    h = _harness()
    original = scratch_target.read_text(encoding="utf-8")
    scratch_target.write_text("ORIGINAL = 999  # planted mutation\n", encoding="utf-8")

    marker = h._MARKER
    prior = marker.read_text(encoding="utf-8") if marker.exists() else None
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({str(scratch_target): original}), encoding="utf-8")
    try:
        assert h.recover_orphaned_mutation() is True
        assert scratch_target.read_text(encoding="utf-8") == original, (
            "RESTORE HOLE: a mutation a killed run left planted was not undone; the next "
            "run would measure a corrupted tree and report its own damage as findings"
        )
        assert not marker.exists(), "the marker must be cleared once it has been replayed"
    finally:
        marker.unlink(missing_ok=True)
        if prior is not None:
            marker.write_text(prior, encoding="utf-8")


def test_no_marker_means_nothing_to_recover():
    """The common path must be silent and cheap, not merely correct."""
    h = _harness()
    marker = h._MARKER
    prior = marker.read_text(encoding="utf-8") if marker.exists() else None
    marker.unlink(missing_ok=True)
    try:
        assert h.recover_orphaned_mutation() is False
    finally:
        if prior is not None:
            marker.write_text(prior, encoding="utf-8")


def test_unreadable_marker_fails_loud_rather_than_guessing(scratch_target):
    """
    A corrupt marker means a run was killed and the tree MAY still be planted.

    Deleting it and carrying on would be a silent default (CLAUDE.md #3) over exactly the
    state that matters most, so it must stop the run and name the remedy.
    """
    h = _harness()
    marker = h._MARKER
    prior = marker.read_text(encoding="utf-8") if marker.exists() else None
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("{not json", encoding="utf-8")
    try:
        with pytest.raises(SystemExit) as exc:
            h.recover_orphaned_mutation()
        assert "killed mid-mutation" in str(exc.value)
    finally:
        marker.unlink(missing_ok=True)
        if prior is not None:
            marker.write_text(prior, encoding="utf-8")
