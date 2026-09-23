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

The CONCURRENT path (2026-09-23)
--------------------------------
The marker used to be ONE fixed path shared by every invocation. When two agents ran the
corpus at once, a run exiting normally deleted the other run's marker; that run was then
killed and its plant survived with no record -- four plants escaped, two reached commits.
The marker is now per invocation, and recovery replays only markers whose pid is dead.

The concurrent tests below use a REAL second process that imports the harness and writes
its own marker through the harness's own `_write_marker`, rather than hand-writing a
file with a guessed name: a test that re-derived the marker name would keep passing with
the fixed path restored, because it would never share the path the harness chose.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# The "other run": imports the harness, plants into a file, writes its marker the way the
# harness does, prints the marker path, and stays live until stdin closes.
_OTHER_RUN = r"""
import sys
from pathlib import Path
from tests import mutation_harness as h
h._MARKER_DIR = Path(sys.argv[1])
h._MARKER = h._new_marker_path()
target = Path(sys.argv[2])
original = target.read_text(encoding="utf-8")
h._IN_FLIGHT[target] = original
target.write_text(original + "# other run's live plant\n", encoding="utf-8")
h._write_marker()
print(h._MARKER, flush=True)
sys.stdin.read()
"""


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
def h(monkeypatch, tmp_path):
    """The harness, with its marker directory moved off the real scratch directory.

    Only the DIRECTORY is redirected; the marker name is still minted by the harness's
    own `_new_marker_path`, so a regression in how names are chosen reaches these tests.
    Never pointing at the real scratch dir also means a live corpus run's marker there
    cannot make these tests refuse, and these tests cannot touch it.
    """
    mod = _harness()
    monkeypatch.setattr(mod, "_MARKER_DIR", tmp_path / "scratch")
    monkeypatch.setattr(mod, "_MARKER", mod._new_marker_path())
    monkeypatch.setattr(mod, "_IN_FLIGHT", {})
    return mod


@pytest.fixture
def scratch_target(tmp_path):
    """A throwaway file standing in for planted pipeline source."""
    f = tmp_path / "planted_source.py"
    f.write_text("ORIGINAL = 1\n", encoding="utf-8")
    return f


def _dead_pid() -> int:
    """A pid that existed a moment ago and has been reaped."""
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    return child.pid


def _dead_marker(h, planted: dict) -> Path:
    marker = h._MARKER_DIR / f"MUTATION_IN_FLIGHT-{_dead_pid()}-{'0' * 32}.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps(planted), encoding="utf-8")
    return marker


class _OtherRun:
    """A concurrent harness invocation with a plant in flight, in a real process."""

    def __init__(self, h, target: Path):
        env = dict(os.environ, PYTHONPATH=str(REPO))
        self.proc = subprocess.Popen(
            [sys.executable, "-c", _OTHER_RUN, str(h._MARKER_DIR), str(target)],
            cwd=REPO, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
        )
        line = self.proc.stdout.readline().strip()
        assert line, f"the other run never reported its marker (exit {self.proc.poll()})"
        self.marker = Path(line)

    def kill9(self) -> None:
        """SIGKILL, then reap: an unreaped zombie still answers kill(pid, 0)."""
        self.proc.send_signal(signal.SIGKILL)
        self.proc.wait()

    def close(self) -> None:
        if self.proc.poll() is None:
            self.kill9()


def test_orphaned_mutation_is_recovered_before_anything_else(h, scratch_target):
    """A marker left by a killed run must be replayed, and then cleared."""
    original = scratch_target.read_text(encoding="utf-8")
    scratch_target.write_text("ORIGINAL = 999  # planted mutation\n", encoding="utf-8")
    marker = _dead_marker(h, {str(scratch_target): original})

    assert h.recover_orphaned_mutation() is True
    assert scratch_target.read_text(encoding="utf-8") == original, (
        "RESTORE HOLE: a mutation a killed run left planted was not undone; the next "
        "run would measure a corrupted tree and report its own damage as findings"
    )
    assert not marker.exists(), "the marker must be cleared once it has been replayed"


def test_legacy_fixed_name_marker_is_still_replayed(h, scratch_target):
    """A marker written by pre-fix code carries no pid; it can only be an orphan."""
    original = scratch_target.read_text(encoding="utf-8")
    scratch_target.write_text("ORIGINAL = 999  # planted mutation\n", encoding="utf-8")
    legacy = h._MARKER_DIR / "MUTATION_IN_FLIGHT.json"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(json.dumps({str(scratch_target): original}), encoding="utf-8")

    assert h.recover_orphaned_mutation() is True
    assert scratch_target.read_text(encoding="utf-8") == original
    assert not legacy.exists()


def test_no_marker_means_nothing_to_recover(h):
    """The common path must be silent and cheap, not merely correct."""
    assert h.recover_orphaned_mutation() is False


def test_unreadable_marker_fails_loud_rather_than_guessing(h):
    """
    A corrupt marker means a run was killed and the tree MAY still be planted.

    Deleting it and carrying on would be a silent default (CLAUDE.md #3) over exactly the
    state that matters most, so it must stop the run and name the remedy.
    """
    marker = _dead_marker(h, {})
    marker.write_text("{not json", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        h.recover_orphaned_mutation()
    assert "killed mid-mutation" in str(exc.value)
    assert marker.exists(), "an unreadable marker is evidence; it must not be deleted"


def test_unparseable_marker_name_fails_loud(h):
    """A marker-shaped file whose owner cannot be read is not skipped silently."""
    odd = h._MARKER_DIR / "MUTATION_IN_FLIGHT-notapid.json"
    odd.parent.mkdir(parents=True, exist_ok=True)
    odd.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        h.recover_orphaned_mutation()
    assert "does not parse" in str(exc.value)


def test_each_invocation_mints_its_own_marker(h):
    """Two calls in one process still differ: uniqueness is (pid, uuid4), not pid."""
    a, b = h._new_marker_path(), h._new_marker_path()
    assert a != b
    assert h._MARKER_NAME.match(a.name) and h._MARKER_NAME.match(b.name)


def test_a_concurrent_runs_normal_exit_leaves_the_killed_runs_plant_recoverable(
    h, scratch_target, tmp_path
):
    """
    The 2026-09-23 incident, replayed with two real processes.

    Run B (another process) has a plant in flight. Run A (this process) plants, restores
    and exits normally. B is then kill -9'd. The next start must still find B's marker
    and undo B's plant. With one shared marker path, A's normal exit deleted B's marker
    and B's plant survived with no record.
    """
    own_target = tmp_path / "own_source.py"
    own_target.write_text("OWN = 1\n", encoding="utf-8")
    original_b = scratch_target.read_text(encoding="utf-8")

    other = _OtherRun(h, scratch_target)
    try:
        # Run A: plant, persist, restore, exit normally -- the harness's own calls.
        h._IN_FLIGHT[own_target] = own_target.read_text(encoding="utf-8")
        own_target.write_text("OWN = 999  # planted mutation\n", encoding="utf-8")
        h._write_marker()
        h._restore_in_flight("run A exiting normally")
        assert own_target.read_text(encoding="utf-8") == "OWN = 1\n"

        assert other.marker.exists(), (
            "SHARED MARKER: run A's normal exit deleted run B's kill-safety marker while "
            "B still had a plant in flight. If B is now killed, its plant survives in the "
            "tree with no record -- the 2026-09-23 escape."
        )
        assert json.loads(other.marker.read_text(encoding="utf-8")) == {
            str(scratch_target): original_b
        }, "run B's marker no longer holds B's original text"

        other.kill9()
        assert scratch_target.read_text(encoding="utf-8") != original_b, "B never planted"
        assert h.recover_orphaned_mutation() is True
        assert scratch_target.read_text(encoding="utf-8") == original_b, (
            "RESTORE HOLE: run B was killed mid-mutation and its plant was not undone"
        )
        assert not other.marker.exists()
    finally:
        other.close()


def test_recovery_never_reverts_a_live_runs_plant(h, scratch_target):
    """
    A live run's plant is SUPPOSED to be in the tree. Reverting it corrupts that run:
    it scores its mutation against unmutated source and files a spurious SURVIVED.
    """
    original = scratch_target.read_text(encoding="utf-8")
    other = _OtherRun(h, scratch_target)
    try:
        planted = scratch_target.read_text(encoding="utf-8")
        assert planted != original, "the other run never planted"
        try:
            h.recover_orphaned_mutation()
        except SystemExit:
            pass  # the refusal is pinned by the next test; this one pins the plant
        assert scratch_target.read_text(encoding="utf-8") == planted, (
            "LIVE PLANT REVERTED: recovery replayed the marker of a run that is still "
            "in flight, reverting its plant underneath it"
        )
        assert other.marker.exists(), "recovery deleted a live run's marker"
    finally:
        other.close()


def test_recovery_refuses_to_start_beside_a_live_run(h, scratch_target):
    """Measuring beside another run's live plant is the contention itself; say so."""
    other = _OtherRun(h, scratch_target)
    try:
        with pytest.raises(SystemExit) as exc:
            h.recover_orphaned_mutation()
        assert "another mutation run is live" in str(exc.value)
        assert str(other.proc.pid) in str(exc.value)
    finally:
        other.close()


# ---------------------------------------------------------------------------------------
# Planted BYTECODE (2026-09-23). A planted command that exits in under a second lets the
# restore land in the same whole second as the plant; with a same-length plant, CPython's
# .pyc check (mtime in whole seconds + size) then keeps running the PLANT from
# __pycache__ after the source is byte-identical again. The same-second landing is made
# deterministic here by pinning the restored file's mtime back to the plant's.
# ---------------------------------------------------------------------------------------

_ORIGINAL_SRC = "VALUE = 111\n"
_PLANTED_SRC = "VALUE = 999\n"   # same byte length: size cannot tell them apart


def _import_value(module_dir: Path) -> str:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
    proc = subprocess.run(
        [sys.executable, "-c", "import plantmod; print(plantmod.VALUE)"],
        cwd=module_dir, env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def _plant_and_compile(module_dir: Path) -> tuple[Path, os.stat_result]:
    """Plant, then let a real interpreter compile the plant into __pycache__."""
    src = module_dir / "plantmod.py"
    src.write_text(_PLANTED_SRC, encoding="utf-8")
    planted_stat = src.stat()
    assert _import_value(module_dir) == "999", "the plant was never compiled"
    assert list((module_dir / "__pycache__").glob("plantmod.*.pyc")), "no bytecode written"
    return src, planted_stat


def _pin_same_second(src: Path, planted_stat: os.stat_result) -> None:
    os.utime(src, ns=(planted_stat.st_atime_ns, planted_stat.st_mtime_ns))


def test_a_same_second_restore_leaves_no_planted_bytecode(h, tmp_path):
    """The normal `_restore` path: source restored AND the plant's bytecode gone."""
    mod_dir = tmp_path / "mods"
    mod_dir.mkdir()
    src, planted_stat = _plant_and_compile(mod_dir)

    h._IN_FLIGHT[src] = _ORIGINAL_SRC
    h._restore({src: _ORIGINAL_SRC})
    _pin_same_second(src, planted_stat)

    assert src.read_text(encoding="utf-8") == _ORIGINAL_SRC
    assert _import_value(mod_dir) == "111", (
        "PLANTED BYTECODE SURVIVED: the source was restored byte-identical but the "
        "interpreter still ran the plant from __pycache__, because the restore landed in "
        "the plant's second at the plant's size. Every later measurement of this tree "
        "runs the planted bug, and no digest can see it."
    )


def test_startup_recovery_leaves_no_planted_bytecode(h, tmp_path):
    """The kill -9 path goes through the same helper, and must drop the bytecode too."""
    mod_dir = tmp_path / "mods"
    mod_dir.mkdir()
    src, planted_stat = _plant_and_compile(mod_dir)
    _dead_marker(h, {str(src): _ORIGINAL_SRC})

    assert h.recover_orphaned_mutation() is True
    _pin_same_second(src, planted_stat)

    assert src.read_text(encoding="utf-8") == _ORIGINAL_SRC
    assert _import_value(mod_dir) == "111", (
        "PLANTED BYTECODE SURVIVED RECOVERY: a killed run's plant was restored in source "
        "but still runs from __pycache__"
    )
