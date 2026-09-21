"""
tree_state.py — which of the three tree states this repository is in, as one command.

THE DEFECT THIS CLOSES
----------------------
Four artifact families are bound to the digest of `mutation_proof.INPUT_ROOTS`: the six
release shard receipts, the obligation benchmark, the frontend static render, and the
mutation proof corpus. Comparing each against the live digest tells you WHETHER they are
current. It does not tell you WHY they are not, and the two reasons need opposite
responses:

  * a batch landed and its ~3.4h re-proof was never run  -> run the chain, in order;
  * a session was interrupted mid-work                   -> resume where it stopped, and
                                                            re-run only the stale shards.

Measured on 2026-09-21: these two are INDISTINGUISHABLE from the digests alone. Both can
present as "artifacts stale", and a clean worktree does not separate them either — an
interrupted session may have committed before it died. Until today the only way to tell was
to read a human-written paragraph in `HANDOFF_PROMPT.md`, which is prose that drifts from
the tree it describes and cannot be executed. The plan calls that a pipeline defect
(owner ruling 3, 2026-09-21: "the pipeline must instead accommodate arbitrary
interruption").

WHY INTENT, AND NOT MORE DIGESTS
-------------------------------
No amount of hashing recovers a fact that was never recorded. "Somebody meant to do a
five-hour thing and got as far as step two" is not a property of the bytes on disk; it is a
property of a plan that existed in a session that is now gone. So this module records the
INTENT explicitly, at the moment work starts, and clears it when work completes. An intent
left open IS the interruption signal, and it carries what the next session needs: what kind
of work, when it began, who began it, and a free-text note naming the step reached.

`validation_reports/phase2_hardening/tree_state.json` therefore:

  * is COMMITTED, so it survives a clone and a fresh checkout reads the same story;
  * is DIGEST-FREE, deliberately. It records no hash of anything. A state file that went
    stale with the tree would need its own freshness gate, and the recursion has to stop
    somewhere. Freshness is computed live, on every call, from the artifacts themselves;
  * sits OUTSIDE `INPUT_ROOTS` (`validation_reports/` is not a root), so writing it costs
    no re-proof. Recording that a batch has started must not itself invalidate the
    artifacts the batch is about to invalidate — that would make the marker unusable in
    the one situation it exists for. Verified rather than assumed: see
    `test_writing_the_state_file_does_not_move_the_input_digest`.

THE THREE STATES
----------------
    certified         no intent open, worktree clean, all four families fresh.
    awaiting_reproof  no intent open, worktree clean, at least one family stale. A batch
                      landed and the chain was not run.
    interrupted       an intent is open, OR the worktree is dirty. Work was in flight.

`interrupted` deliberately wins over the digests. An open intent means a session did not
reach its own finish line, and that is true whether or not its artifacts happen to be
current — the dangerous reading is the optimistic one.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
1. **An intent is a claim, not a lock.** Nothing here can tell a session that is alive from
   one that died holding an open intent; there is no pid, no heartbeat, no timeout. That is
   the same trade `hardening_status.STALE_LOCK_HOURS` makes for the H-row lock, without
   even the staleness window — added here would be a clock-dependent verdict in a module
   whose whole job is to be executable and deterministic. Read `began_at` and decide.
2. **A session that never calls `--begin` is invisible to the intent half.** The dirty
   worktree still reports `interrupted`, but with no record of what the edits were FOR,
   which is most of the value. This is a convention, enforced only by the habit of running
   the command; nothing can make an absent record appear.
3. **`--complete` is trusted.** Clearing the intent asserts the work finished; this module
   does not re-derive whether it did. The freshness half is what catches the mismatch: an
   intent cleared on a stale tree reports `awaiting_reproof`, not `certified`.
4. **The worktree check is not exercised by the unit tests.** `collect_state` takes `dirty`
   as an argument so the state machine can be driven over a temporary root, and the tests
   pass it explicitly; `_worktree_is_dirty`'s own `git status --porcelain` call is covered
   only by running this module for real. Named rather than described as covered.
5. **Freshness is per-FAMILY, not per-file, for the two multi-file families.** A single
   stale shard makes the release family stale, which is correct for the verdict but coarser
   than the receipts themselves — each records its own digest, and re-running only the stale
   indices is a 2.5-hour saving. `--json` prints the per-file detail so that saving stays
   reachable.
"""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = REPO_ROOT / "validation_reports" / "phase2_hardening" / "tree_state.json"

SCHEMA_VERSION = 1

# §8 inventory: see `run_all.ASSERTIONS`, where this label is declared.
ASSERTIONS = (
    "tree_state_certification",
)

CERTIFIED = "certified"
AWAITING_REPROOF = "awaiting_reproof"
INTERRUPTED = "interrupted"

# A closed set, extended by adding a word -- never by accepting free text. An intent whose
# kind is not one of these cannot be given a next-step instruction, and an intent that
# cannot say what to do next is a marker that only tells you something is wrong.
INTENT_KINDS = {
    # Source edits under INPUT_ROOTS are being landed. Invalidates all four families.
    "batch": "Land every remaining source edit, then run the re-proof chain in order.",
    # The re-proof chain itself: frontend suite, benchmark, mutation corpus, six shards,
    # verify-release, run_all. Resumable per shard.
    "chain": "Resume the chain at the first step whose artifact is still stale; shards "
             "are individually resumable, so re-run only the stale indices.",
    # Digest-free work (the attestation campaign). Interruptible, but costs no re-proof.
    "campaign": "Resume the campaign; it touches no source, so no re-proof is owed.",
}

# The four digest-bound artifact families, and the key each records its digest under. The
# two keys differ because the corpus and the receipts were built by different steps of the
# plan; both are read rather than one being assumed (Mandate 1 -- a check that guesses a
# field name reports fresh on a file it failed to parse).
_FAMILIES = (
    ("mutation_proofs", "validation_reports/mutation_proofs/*.json", "input_digest"),
    ("release_shards",
     "validation_reports/phase2_hardening/obligation_release_shards/*.json",
     "source_input_digest"),
    ("obligation_benchmark",
     "validation_reports/phase2_hardening/obligation_benchmark.json",
     "source_input_digest"),
    ("frontend_static_render",
     "validation_reports/phase2_hardening/frontend_static_render.json",
     "source_input_digest"),
)


@dataclass
class Family:
    """Freshness of one digest-bound artifact family."""

    name: str
    fresh_files: List[str] = field(default_factory=list)
    stale_files: List[str] = field(default_factory=list)
    unreadable: List[str] = field(default_factory=list)

    @property
    def present(self) -> int:
        return len(self.fresh_files) + len(self.stale_files) + len(self.unreadable)

    @property
    def fresh(self) -> bool:
        """A family is fresh only if it has files and every one of them is current.

        An EMPTY family is not fresh. A missing corpus is the same evidential position as a
        stale one -- nothing current proves anything about this tree -- and reporting
        `all()` over an empty list as True is how a deleted artifact directory certifies a
        tree (`all([]) is True`).
        """
        return self.present > 0 and not self.stale_files and not self.unreadable


def _read_digest(path: Path, key: str) -> Optional[str]:
    """The digest an artifact records, or None if it cannot be read as one."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    value = doc.get(key) if isinstance(doc, dict) else None
    return value if isinstance(value, str) and value else None


def artifact_families(live_digest: str, root: Path = REPO_ROOT) -> List[Family]:
    """Every family, split into fresh/stale/unreadable against `live_digest`."""
    out: List[Family] = []
    for name, pattern, key in _FAMILIES:
        fam = Family(name=name)
        for match in sorted(glob.glob(str(root / pattern))):
            path = Path(match)
            rel = path.relative_to(root).as_posix()
            recorded = _read_digest(path, key)
            if recorded is None:
                fam.unreadable.append(rel)
            elif recorded == live_digest:
                fam.fresh_files.append(rel)
            else:
                fam.stale_files.append(rel)
        out.append(fam)
    return out


def load_intent(root: Path = REPO_ROOT) -> Optional[Dict[str, Any]]:
    """The open intent, or None. A missing or intent-free state file means none."""
    path = root / STATE_FILE.relative_to(REPO_ROOT)
    if not path.exists():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(
            f"FATAL: {path} exists but is unreadable ({exc}). This file records whether "
            f"work is in flight, so an unreadable one is the one case that must not be "
            f"read as 'nothing is happening'. Repair it from git history before running "
            f"anything else."
        )
    intent = doc.get("open_intent") if isinstance(doc, dict) else None
    return intent if isinstance(intent, dict) else None


def _worktree_is_dirty(root: Path = REPO_ROOT) -> bool:
    """`git status --porcelain` is non-empty. See known limitation 4."""
    proc = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"FATAL: `git status --porcelain` exited {proc.returncode} in {root}: "
            f"{proc.stderr.strip()!r}. Whether the worktree is clean is half of the state "
            f"determination and must not be guessed."
        )
    return bool(proc.stdout.strip())


def determine_state(families: List[Family], dirty: bool,
                    intent: Optional[Dict[str, Any]]) -> str:
    """
    The state machine. Pure, so both halves of every branch are unit-testable.

    Order matters and is the conservative one: an open intent or a dirty worktree means
    work was in flight, and that outranks whatever the digests say. `certified` is the only
    verdict that requires EVERY condition to hold, which is what makes the optimistic
    reading the hard one to reach.
    """
    if intent is not None:
        return INTERRUPTED
    if dirty:
        return INTERRUPTED
    if all(f.fresh for f in families):
        return CERTIFIED
    return AWAITING_REPROOF


def collect_state(root: Path = REPO_ROOT, live_digest: Optional[str] = None,
                  dirty: Optional[bool] = None) -> Dict[str, Any]:
    """
    The whole determination, as a dict. Arguments are injectable so the state machine can
    be driven over a temporary root with a known digest (see known limitation 4).
    """
    if live_digest is None:
        from backend.app.practice_gen.validation.mutation_proof import input_digest
        live_digest = input_digest()
    if dirty is None:
        dirty = _worktree_is_dirty(root)
    families = artifact_families(live_digest, root)
    intent = load_intent(root)
    return {
        "state": determine_state(families, dirty, intent),
        "live_digest": live_digest,
        "worktree_dirty": dirty,
        "open_intent": intent,
        "families": [
            {"name": f.name, "fresh": f.fresh, "files_present": f.present,
             "stale_files": f.stale_files, "unreadable_files": f.unreadable}
            for f in families
        ],
    }


# ── the intent file ───────────────────────────────────────────────────────────────

def _empty_doc() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "note": (
            "Intent record for interruption safety. Written when a batch, chain or "
            "campaign STARTS and cleared when it completes; an intent left open means a "
            "session did not reach its finish line. Deliberately digest-free -- see "
            "tests/tree_state.py. Read with `PYTHONPATH=. .venv/bin/python "
            "tests/tree_state.py`."
        ),
        "open_intent": None,
        "last_completed": None,
    }


def _load_doc(root: Path = REPO_ROOT) -> Dict[str, Any]:
    path = root / STATE_FILE.relative_to(REPO_ROOT)
    if not path.exists():
        return _empty_doc()
    return json.loads(path.read_text(encoding="utf-8"))


def _save_doc(doc: Dict[str, Any], root: Path = REPO_ROOT) -> Path:
    path = root / STATE_FILE.relative_to(REPO_ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def begin(kind: str, note: str, session: str, root: Path = REPO_ROOT,
          force: bool = False) -> Dict[str, Any]:
    """Record that work has started. Refuses to overwrite an intent already open."""
    if kind not in INTENT_KINDS:
        raise SystemExit(
            f"FATAL: intent kind {kind!r} is not one of {sorted(INTENT_KINDS)}. The kind "
            f"selects the next-step instruction a later session reads, so an unknown kind "
            f"is a marker that cannot say what to do."
        )
    doc = _load_doc(root)
    open_intent = doc.get("open_intent")
    if isinstance(open_intent, dict) and not force:
        raise SystemExit(
            f"FATAL: an intent is already open ({open_intent.get('kind')!r} begun "
            f"{open_intent.get('began_at')} by {open_intent.get('session')!r}). Overwriting "
            f"it would erase the only record of work someone else did not finish. Complete "
            f"it with `--complete`, or pass `--force` if you have read it and it is yours."
        )
    doc["schema_version"] = SCHEMA_VERSION
    doc["open_intent"] = {
        "kind": kind,
        "began_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "session": session,
        "note": note,
        "next_step": INTENT_KINDS[kind],
    }
    _save_doc(doc, root)
    return doc["open_intent"]


def complete(note: str, root: Path = REPO_ROOT) -> Dict[str, Any]:
    """Clear the open intent, keeping it as `last_completed`."""
    doc = _load_doc(root)
    open_intent = doc.get("open_intent")
    if not isinstance(open_intent, dict):
        raise SystemExit(
            "FATAL: no intent is open, so there is nothing to complete. If work was done "
            "without `--begin`, say so in the evidence log rather than filing a completion "
            "for work this file never saw start (known limitation 2)."
        )
    finished = dict(open_intent)
    finished["completed_at"] = datetime.now(timezone.utc).astimezone().isoformat(
        timespec="seconds")
    if note:
        finished["completion_note"] = note
    doc["open_intent"] = None
    doc["last_completed"] = finished
    _save_doc(doc, root)
    return finished


# ── reporting ─────────────────────────────────────────────────────────────────────

_WHAT_TO_DO = {
    CERTIFIED: ("Every digest-bound artifact is current and nothing is in flight. Do not "
                "re-run the chain -- it proves nothing new. Touch no source you do not "
                "mean to change."),
    AWAITING_REPROOF: ("A batch landed and its re-proof was not run. Run the chain in "
                       "order: frontend suite, benchmark, mutation corpus, the six "
                       "release shards, verify-release, then run_all."),
    INTERRUPTED: ("Work was in flight. Read the open intent below (or `git status`, if "
                  "none was recorded) before starting anything new; shards are "
                  "individually resumable, so re-run only the stale indices."),
}


def report(state: Dict[str, Any]) -> None:
    verdict = state["state"]
    print(f"{'PASS' if verdict == CERTIFIED else 'STATE'} tree_state: {verdict.upper()}")
    print(f"  live input digest : {state['live_digest'][:16]}")
    print(f"  worktree          : {'DIRTY' if state['worktree_dirty'] else 'clean'}")
    for fam in state["families"]:
        mark = "fresh" if fam["fresh"] else "STALE"
        detail = f"{fam['files_present']} file(s)"
        if fam["stale_files"]:
            detail += f", {len(fam['stale_files'])} stale"
        if fam["unreadable_files"]:
            detail += f", {len(fam['unreadable_files'])} unreadable"
        print(f"  {fam['name']:<24}{mark:<7}{detail}")
    intent = state["open_intent"]
    if intent:
        print(f"  OPEN INTENT       : {intent.get('kind')!r} begun {intent.get('began_at')} "
              f"by {intent.get('session')!r}")
        print(f"    note            : {intent.get('note')}")
        print(f"    next step       : {intent.get('next_step')}")
    print(f"  -> {_WHAT_TO_DO[verdict]}")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Which of the three tree states this repository is in.")
    ap.add_argument("--begin", metavar="KIND", choices=sorted(INTENT_KINDS),
                    help="record that work of this kind has started")
    ap.add_argument("--complete", action="store_true",
                    help="clear the open intent, keeping it as last_completed")
    ap.add_argument("--note", default="", help="what is being done, or what was reached")
    ap.add_argument("--session", default="", help="session identifier holding the intent")
    ap.add_argument("--force", action="store_true",
                    help="with --begin, overwrite an intent that is already open")
    ap.add_argument("--json", action="store_true", help="machine-readable state")
    args = ap.parse_args(argv)

    if args.begin and args.complete:
        print("FATAL: --begin and --complete are opposite operations; pass one.",
              file=sys.stderr)
        return 2
    if args.begin:
        if not args.session:
            print("FATAL: --begin needs --session, or the intent cannot say who holds it.",
                  file=sys.stderr)
            return 2
        opened = begin(args.begin, args.note, args.session, force=args.force)
        print(f"tree_state: opened {opened['kind']!r} intent -- {opened['next_step']}")
        return 0
    if args.complete:
        done = complete(args.note)
        print(f"tree_state: completed {done['kind']!r} intent begun {done['began_at']}")
        return 0

    state = collect_state()
    if args.json:
        print(json.dumps(state, indent=2))
    else:
        report(state)
    return 0 if state["state"] == CERTIFIED else 1


if __name__ == "__main__":
    sys.exit(main())
