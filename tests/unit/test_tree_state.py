"""
The three-state determination, proved in every direction that matters.

`tests/tree_state.py` exists because two of the three states were indistinguishable from
the digests alone and were told apart by reading prose. A state machine that replaces a
paragraph is only an improvement if it cannot lie, and the one lie that costs real money is
`certified` on a tree that is not: it tells the next session to skip a ~3.4h re-proof and
then build content on artifacts that describe different bytes.

So the tests below are organised around that verdict. Every input that must forbid
`certified` is planted individually, because "all four conditions hold" is exactly the shape
of assertion that keeps passing when one of its terms is quietly dropped.

The state machine is driven over a TEMPORARY root with an injected digest rather than
against the live repository. That is deliberate: a test that asserted the real tree's state
would pass or fail depending on whether a chain had been run, which is not a property of
this module. What the temporary root does NOT cover is named in `tree_state`'s known
limitation 4 — `_worktree_is_dirty`'s own git call — and the live-tree test at the bottom
covers what a temporary root cannot.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests import tree_state as ts

LIVE = "a" * 64
STALE = "b" * 64


def _write(root: Path, rel: str, digest: str, key: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({key: digest, "note": "fixture"}), encoding="utf-8")


def _fresh_tree(root: Path, digest: str = LIVE) -> None:
    """One artifact in each of the four families, all recording `digest`."""
    _write(root, "validation_reports/mutation_proofs/some_mutation.json", digest,
           "input_digest")
    _write(root, "validation_reports/phase2_hardening/obligation_release_shards/"
                 "shard_000_of_006.json", digest, "source_input_digest")
    _write(root, "validation_reports/phase2_hardening/obligation_benchmark.json", digest,
           "source_input_digest")
    _write(root, "validation_reports/phase2_hardening/frontend_static_render.json", digest,
           "source_input_digest")


def _state(root: Path, live: str = LIVE, dirty: bool = False) -> str:
    return ts.collect_state(root=root, live_digest=live, dirty=dirty)["state"]


# ── the positive control ──────────────────────────────────────────────────────────

def test_a_fresh_clean_tree_with_no_intent_is_certified(tmp_path):
    """The control. If this fails, no negative result below means anything."""
    _fresh_tree(tmp_path)
    assert _state(tmp_path) == ts.CERTIFIED


# ── every way `certified` must be refused ─────────────────────────────────────────

@pytest.mark.parametrize("family_file,key", [
    ("validation_reports/mutation_proofs/some_mutation.json", "input_digest"),
    ("validation_reports/phase2_hardening/obligation_release_shards/shard_000_of_006.json",
     "source_input_digest"),
    ("validation_reports/phase2_hardening/obligation_benchmark.json", "source_input_digest"),
    ("validation_reports/phase2_hardening/frontend_static_render.json",
     "source_input_digest"),
])
def test_one_stale_family_forbids_certified(tmp_path, family_file, key):
    """
    Each family planted stale on its own. Parametrised rather than written once because a
    freshness check that reads three of four families reports `certified` on a tree whose
    fourth is a month old, and only a per-family plant can tell the difference.
    """
    _fresh_tree(tmp_path)
    _write(tmp_path, family_file, STALE, key)
    assert _state(tmp_path) == ts.AWAITING_REPROOF


def test_a_single_stale_file_inside_a_family_forbids_certified(tmp_path):
    """147 current proofs and one stale one is a stale corpus, not a 99.3% fresh one."""
    _fresh_tree(tmp_path)
    for n in range(1, 6):
        _write(tmp_path, f"validation_reports/mutation_proofs/m{n}.json", LIVE,
               "input_digest")
    _write(tmp_path, "validation_reports/mutation_proofs/m6.json", STALE, "input_digest")
    assert _state(tmp_path) == ts.AWAITING_REPROOF


def test_a_dirty_worktree_forbids_certified(tmp_path):
    """Fresh artifacts plus uncommitted edits is work in flight, not a certified tree."""
    _fresh_tree(tmp_path)
    assert _state(tmp_path, dirty=True) == ts.INTERRUPTED


def test_an_open_intent_forbids_certified_even_on_a_fresh_clean_tree(tmp_path):
    """
    The state the digests cannot see. A session that opened an intent and died may have
    committed and even re-proved; the work is still unfinished, and the optimistic reading
    is the dangerous one.
    """
    _fresh_tree(tmp_path)
    ts.begin("chain", "reached shard 3 of 6", "session-x", root=tmp_path)
    assert _state(tmp_path) == ts.INTERRUPTED


def test_a_missing_family_is_not_fresh(tmp_path):
    """`all([])` is True, which is how a deleted corpus certifies a tree."""
    _fresh_tree(tmp_path)
    (tmp_path / "validation_reports/phase2_hardening/obligation_benchmark.json").unlink()
    assert _state(tmp_path) == ts.AWAITING_REPROOF


def test_an_artifact_that_records_no_digest_is_not_fresh(tmp_path):
    """A receipt whose digest key is absent proves nothing; it must not read as current."""
    _fresh_tree(tmp_path)
    path = tmp_path / "validation_reports/phase2_hardening/frontend_static_render.json"
    path.write_text(json.dumps({"note": "no digest field at all"}), encoding="utf-8")
    assert _state(tmp_path) == ts.AWAITING_REPROOF
    fam = {f["name"]: f for f in ts.collect_state(
        root=tmp_path, live_digest=LIVE, dirty=False)["families"]}
    assert fam["frontend_static_render"]["unreadable_files"], fam


def test_a_corrupt_artifact_is_not_fresh(tmp_path):
    """Half-written JSON from an interrupted run is unreadable, not current."""
    _fresh_tree(tmp_path)
    path = tmp_path / "validation_reports/phase2_hardening/obligation_benchmark.json"
    path.write_text('{"source_input_digest": "aaaa', encoding="utf-8")
    assert _state(tmp_path) == ts.AWAITING_REPROOF


# ── the two states that used to be indistinguishable ──────────────────────────────

def test_the_two_stale_states_are_now_told_apart(tmp_path):
    """
    THE WHOLE POINT. Identical digests, identical clean worktree; the only difference is
    whether a session recorded that it had started something. Before this module both of
    these read the same way and were separated by a human-written paragraph.
    """
    _fresh_tree(tmp_path, STALE)
    assert _state(tmp_path) == ts.AWAITING_REPROOF

    ts.begin("batch", "three of four items landed", "session-y", root=tmp_path)
    assert _state(tmp_path) == ts.INTERRUPTED


def test_completing_an_intent_returns_a_stale_tree_to_awaiting_reproof(tmp_path):
    """Clearing the intent is trusted, but it cannot manufacture freshness (limitation 3)."""
    _fresh_tree(tmp_path, STALE)
    ts.begin("batch", "landing edits", "session-y", root=tmp_path)
    ts.complete("edits landed, chain owed", root=tmp_path)
    assert _state(tmp_path) == ts.AWAITING_REPROOF


def test_completing_an_intent_on_a_fresh_tree_certifies_it(tmp_path):
    _fresh_tree(tmp_path)
    ts.begin("chain", "running the chain", "session-y", root=tmp_path)
    ts.complete("chain complete", root=tmp_path)
    assert _state(tmp_path) == ts.CERTIFIED


# ── the intent file's own rules ───────────────────────────────────────────────────

def test_beginning_over_an_open_intent_is_refused(tmp_path):
    """Overwriting erases the only record of work somebody did not finish."""
    ts.begin("batch", "first", "session-a", root=tmp_path)
    with pytest.raises(SystemExit) as exc:
        ts.begin("chain", "second", "session-b", root=tmp_path)
    assert "already open" in str(exc.value)
    assert ts.load_intent(tmp_path)["session"] == "session-a"


def test_force_overwrites_a_read_intent(tmp_path):
    ts.begin("batch", "first", "session-a", root=tmp_path)
    ts.begin("chain", "second", "session-b", root=tmp_path, force=True)
    assert ts.load_intent(tmp_path)["session"] == "session-b"


def test_an_unknown_intent_kind_is_refused(tmp_path):
    """The kind selects the next-step instruction, so free text is a marker that is mute."""
    with pytest.raises(SystemExit) as exc:
        ts.begin("having_a_think", "?", "session-a", root=tmp_path)
    assert "not one of" in str(exc.value)


def test_completing_with_nothing_open_is_refused(tmp_path):
    with pytest.raises(SystemExit) as exc:
        ts.complete("done", root=tmp_path)
    assert "no intent is open" in str(exc.value)


def test_a_completed_intent_is_kept_not_discarded(tmp_path):
    """The previous session's note is how the next one learns what happened."""
    ts.begin("chain", "reached shard 4", "session-a", root=tmp_path)
    ts.complete("all six shards done", root=tmp_path)
    doc = json.loads((tmp_path / "validation_reports/phase2_hardening/tree_state.json")
                     .read_text(encoding="utf-8"))
    assert doc["open_intent"] is None
    assert doc["last_completed"]["note"] == "reached shard 4"
    assert doc["last_completed"]["completion_note"] == "all six shards done"
    assert doc["last_completed"]["completed_at"]


def test_every_intent_kind_carries_a_next_step(tmp_path):
    """A marker that cannot say what to do next only reports that something is wrong."""
    for kind in ts.INTENT_KINDS:
        ts.begin(kind, "x", "session-a", root=tmp_path, force=True)
        assert ts.load_intent(tmp_path)["next_step"].strip()


def test_an_unreadable_state_file_is_fatal_not_silently_empty(tmp_path):
    """The one case that must never read as 'nothing is happening' (Protocol 3)."""
    path = tmp_path / "validation_reports/phase2_hardening/tree_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"open_intent": {"kind": "batch"', encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        ts.load_intent(tmp_path)
    assert "unreadable" in str(exc.value)


# ── the two claims about the live repository ──────────────────────────────────────

def test_writing_the_state_file_does_not_move_the_input_digest():
    """
    VERIFIED, NOT ASSUMED. Recording that a batch has started must not invalidate the
    artifacts the batch is about to invalidate, or the marker is unusable in the one
    situation it exists for. `validation_reports/` is not an `INPUT_ROOT` and this file is
    not in `INPUT_FILES` — this executes that claim rather than restating it.
    """
    from backend.app.practice_gen.validation.mutation_proof import input_digest

    before = input_digest()
    doc = ts._load_doc()
    original = ts.STATE_FILE.read_text(encoding="utf-8") if ts.STATE_FILE.exists() else None
    try:
        probe = dict(doc)
        probe["digest_probe"] = "written by test_writing_the_state_file_does_not_move_the_input_digest"
        ts._save_doc(probe)
        assert input_digest() == before, (
            "writing tree_state.json moved the input digest, so recording batch intent now "
            "costs a full re-proof and the marker cannot be used for what it was built for"
        )
    finally:
        if original is None:
            ts.STATE_FILE.unlink(missing_ok=True)
        else:
            ts.STATE_FILE.write_text(original, encoding="utf-8")
    assert input_digest() == before


def test_the_live_state_file_parses_and_is_claimed_by_an_H_row():
    """
    Two directions at once: the committed file is readable as a state document, and the
    ledger claims it. An artifact no row claims is evidence the ledger cannot bind to a
    blocker, and `hardening_status` fails on it — this names the file so a future rename
    fails here, where the message says why, rather than there.
    """
    from tests import hardening_status as hs

    doc = json.loads(ts.STATE_FILE.read_text(encoding="utf-8"))
    assert doc["schema_version"] == ts.SCHEMA_VERSION
    assert "open_intent" in doc
    rel = ts.STATE_FILE.relative_to(ts.REPO_ROOT).as_posix()
    claimed = {a for row in hs.load()["rows"] for a in (row.get("proof_artifacts") or [])}
    assert rel in claimed, f"{rel} is claimed by no H-row"
