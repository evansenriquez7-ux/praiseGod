"""
hardening_status.py — the H-row ledger for the Phase 2 hardening plan, and its schema gate.

`docs/phase2_hardening_completion_plan.md` replaces the historical per-tick narrative in
`validation_reports/hardening_ledger.md` (last entry 2026-08-26, tick 489, five commits
stale) with a machine-checkable status ledger. This module owns both the rows and the
check that they are well formed.

WHY A SCHEMA GATE AND NOT JUST A JSON FILE
------------------------------------------
The ledger's whole purpose is that a blocker cannot quietly lose its evidence. A row with
`status: closed` and an empty `proof_artifacts`, or a `closing_revision` naming a commit
that does not exist, is exactly the shape of bookkeeping the plan calls "numbers, not
safety". `validate()` refuses those, so a row closes only when it can show its work.

WHAT THIS IS NOT
----------------
Not a validator registered in `run_all`, and deliberately so: these rows track PLAN
progress, not pipeline behaviour, and a §-ref for them would put planning state inside the
contract the pipeline is measured against. Run it directly, or from a migration/audit step.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER = REPO_ROOT / "validation_reports" / "phase2_hardening" / "hardening_status.json"

SCHEMA_VERSION = 1

REQUIRED_FIELDS = (
    "id", "status", "owner", "affected_assertions", "baseline_evidence",
    "acceptance_checks", "proof_artifacts", "closing_revision", "updated_at",
)

VALID_STATUS = ("open", "in_progress", "closed", "out_of_scope")

# `owner` is a WORK-LOCK, not an accountability field. One person directs this repo, so
# "who is responsible" is never in question and a column answering it would be constant.
# The real hazard is two parallel worktree sessions both starting the same blocker, or a
# fresh agent inheriting a half-built row with no sign anyone had been there. So the field
# records WHO HOLDS THE ROW RIGHT NOW:
#
#   "unclaimed"            nobody is working it -- free to pick up
#   "<anything else>"      a session identifier; that session is mid-flight on this row
#   "released @ <rev>"     the holder finished and handed it back
#
# Claim before starting, release on commit. The two rules below are what make it load
# bearing rather than decorative.
UNCLAIMED = "unclaimed"
_RELEASED_PREFIX = "released @ "

# A row may only claim `closed` with both of these non-empty. `out_of_scope` needs a
# closing_revision too -- the commit that recorded the decision -- but no proof artifacts,
# because nothing was built.
CLOSED_REQUIRES = ("proof_artifacts", "closing_revision")

# ---------------------------------------------------------------------------------------
# THE THREE DIRECTIONS ADDED 2026-09-16, AND THE MEASUREMENT THAT FORCED THEM
# ---------------------------------------------------------------------------------------
# The two original rules caught `in_progress` + `unclaimed` and a closed row still held.
# Measured on the tree at f8597c0f, the ledger passed those two while saying the two most
# misleading things it could say:
#
#   * H-07 was `in_progress`, held by `codex-20260914-h08-static-render` -- H-08's session
#     -- with its own measurement_status reading "unmeasured -- inherited from the plan".
#     An untouched row read as somebody's live work, so the next session would skip it.
#   * H-08 was `open`/`unclaimed` with `proof_artifacts: []`, while
#     `phase2_hardening/frontend_static_render.json` (its evidence, and the newest file in
#     that directory) sat on disk claimed by nobody. A nearly-finished row read as
#     unstarted, so the next session would redo it.
#
# Both directions of the lock were legal and the one field binding a row to its evidence
# was empty on the row with the most evidence. These three close that.
#
# 1. A session identifier that embeds an H-row token must embed ITS OWN. The convention in
#    use is `codex-<date>-<row>-<slug>`; a token naming a different row is the H-07 defect
#    exactly, and it is deterministic to catch -- no threshold, no clock.
_OWNER_ROW_TOKEN = re.compile(r"h-?(\d{2})", re.IGNORECASE)

# 2. Every artifact in the plan's own directory must be claimed by some row, in the same
#    two-direction shape the rest of the harness uses: disk vs claimed, both ways. Without
#    it the ledger can only notice an artifact it NAMES that is missing, never one that
#    exists and belongs to a row that forgot it. These three are the ledger's own
#    bookkeeping rather than any row's evidence, so they are exempt BY NAME -- a broad
#    prefix exemption is how a real artifact corpus gets excluded wholesale.
ARTIFACT_DIR = REPO_ROOT / "validation_reports" / "phase2_hardening"
_NOT_PROOF_ARTIFACTS = {
    "hardening_status.json",   # this ledger
    "HANDOFF_PROMPT.md",       # prose handoff, superseded every session
}

# 3. A lock is a temporal claim, so staleness is the only way to tell "someone is working
#    this" from "someone died holding this". 36 hours is deliberately generous: it must not
#    fire on an overnight pause in a single session's work, only on a session that is gone.
#    This is the one check here whose verdict depends on when it runs -- acceptable because
#    this module is deliberately NOT registered in `run_all` (see the docstring).
STALE_LOCK_HOURS = 36


def validate(doc: Dict[str, Any]) -> List[str]:
    """Return one error per way this ledger does not hold. Empty list means it does."""
    errors: List[str] = []

    if doc.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"schema_version is {doc.get('schema_version')!r}, expected {SCHEMA_VERSION}"
        )

    rows = doc.get("rows")
    if not isinstance(rows, list):
        return errors + ["`rows` is missing or not a list"]

    seen = set()
    for i, row in enumerate(rows):
        where = f"row {i} ({row.get('id', '<no id>')})"

        for field in REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"{where}: missing required field {field!r}")

        rid = row.get("id")
        if rid in seen:
            errors.append(f"{where}: duplicate id {rid!r}")
        seen.add(rid)

        status = row.get("status")
        if status not in VALID_STATUS:
            errors.append(
                f"{where}: status {status!r} is not one of {VALID_STATUS}"
            )

        # The rule the ledger exists for: a closed blocker shows its work.
        if status == "closed":
            for field in CLOSED_REQUIRES:
                if not row.get(field):
                    errors.append(
                        f"{where}: status is 'closed' but {field!r} is empty. A blocker "
                        f"that cannot name the evidence that closed it is not closed."
                    )
        if status == "out_of_scope" and not row.get("closing_revision"):
            errors.append(
                f"{where}: status is 'out_of_scope' but no closing_revision names the "
                f"commit that recorded the decision."
            )

        owner = row.get("owner")
        if not isinstance(owner, str) or not owner.strip():
            errors.append(
                f"{where}: owner must be a non-empty string -- {UNCLAIMED!r}, a session "
                f"identifier, or {_RELEASED_PREFIX!r} plus a revision."
            )
        else:
            # A row nobody is holding cannot be in flight. This is the direction that
            # catches an abandoned session: the row says in_progress, the lock says
            # nobody has it, so the work stopped without anyone recording where.
            if status == "in_progress" and owner == UNCLAIMED:
                errors.append(
                    f"{where}: status is 'in_progress' but owner is {UNCLAIMED!r}. Either a "
                    f"session holds this row and should name itself, or the work stopped and "
                    f"the status should say so."
                )
            # And a finished row must not still be locked, or the next session reads a
            # closed blocker as someone else's live work and leaves it alone.
            if status in ("closed", "out_of_scope") and owner != UNCLAIMED \
                    and not owner.startswith(_RELEASED_PREFIX):
                errors.append(
                    f"{where}: status is {status!r} but owner is still {owner!r}. Release the "
                    f"lock ({UNCLAIMED!r} or {_RELEASED_PREFIX!r}<revision>) so the row does "
                    f"not read as someone's live work."
                )
            # A lock that embeds an H-row token must embed its own. See direction 1 above.
            token = _OWNER_ROW_TOKEN.search(owner)
            if token and isinstance(rid, str):
                own = _OWNER_ROW_TOKEN.search(rid)
                if own and token.group(1) != own.group(1):
                    errors.append(
                        f"{where}: owner {owner!r} names H-{token.group(1)}, not {rid}. A "
                        f"session holding the wrong row makes an untouched blocker read as "
                        f"live work and leaves its real row looking unclaimed. Fix the lock, "
                        f"or move it to the row the work is actually on."
                    )
            # A lock nobody has touched for STALE_LOCK_HOURS is an abandoned session.
            if status == "in_progress":
                age = _hours_since(row.get("updated_at"))
                if age is None:
                    errors.append(
                        f"{where}: status is 'in_progress' but updated_at "
                        f"{row.get('updated_at')!r} is not a parseable timestamp, so the "
                        f"lock's age -- the only thing separating live work from an "
                        f"abandoned session -- cannot be measured."
                    )
                elif age > STALE_LOCK_HOURS:
                    errors.append(
                        f"{where}: status is 'in_progress' and owner {owner!r} has held it "
                        f"for {age:.0f}h (> {STALE_LOCK_HOURS}h). Either that session is "
                        f"gone and the lock should be released with the partial work "
                        f"recorded in `progress`/`still_open`, or it is alive and must "
                        f"touch `updated_at`."
                    )

        # An open row with proof artifacts is not an error, but a closing_revision on one
        # is: it means the row was closed and reopened without clearing its provenance.
        if status in ("open", "in_progress") and row.get("closing_revision"):
            errors.append(
                f"{where}: status is {status!r} but closing_revision is "
                f"{row['closing_revision']!r}. Clear it or close the row."
            )

        for rev_field in ("closing_revision",):
            rev = row.get(rev_field)
            if rev and not _revision_exists(rev):
                errors.append(
                    f"{where}: {rev_field} {rev!r} is not a commit in this repository."
                )

        for art in row.get("proof_artifacts") or []:
            if not (REPO_ROOT / art).exists():
                errors.append(f"{where}: proof_artifact {art!r} does not exist on disk.")

    # NOTE: the disk->rows direction (`_unclaimed_artifacts`) deliberately lives in
    # `main()` rather than here. `validate()` judges a DOCUMENT; reconciling the whole
    # artifact directory judges the repository, and running it against a synthetic
    # document would report every real artifact as unclaimed, which is noise rather than
    # a finding.
    return errors


def _hours_since(stamp: Any) -> float | None:
    """Age of an ISO-8601 timestamp in hours, or None if it will not parse."""
    if not isinstance(stamp, str):
        return None
    try:
        when = datetime.fromisoformat(stamp)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - when).total_seconds() / 3600.0


def _unclaimed_artifacts(rows: List[Dict[str, Any]]) -> List[str]:
    """
    The other direction of `proof_artifacts`: an artifact on disk that no row claims.

    The original check only walked rows -> disk, so it could catch a row naming a file
    that had been deleted but never a file whose row had forgotten it. That is the H-08
    shape: the newest artifact in the directory, belonging to a row whose list was empty.
    """
    if not ARTIFACT_DIR.is_dir():
        return []
    claimed = {
        art for row in rows for art in (row.get("proof_artifacts") or [])
    }
    errors: List[str] = []
    for path in sorted(ARTIFACT_DIR.iterdir()):
        if not path.is_file() or path.name in _NOT_PROOF_ARTIFACTS:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel not in claimed:
            errors.append(
                f"artifact {rel!r} exists but no H-row lists it in proof_artifacts. Either "
                f"it is a row's evidence and that row should claim it, or nothing needs it "
                f"and it should be deleted -- an unclaimed artifact is evidence the ledger "
                f"cannot bind to a blocker."
            )
    return errors


def _revision_exists(rev: str) -> bool:
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"{rev}^{{commit}}"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return proc.returncode == 0


def load() -> Dict[str, Any]:
    with LEDGER.open(encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    if not LEDGER.exists():
        print(f"FAIL hardening_status: {LEDGER} does not exist")
        return 1
    doc = load()
    errors = validate(doc) + _unclaimed_artifacts(doc.get("rows") or [])
    if errors:
        print(f"FAIL hardening_status ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        return 1
    by_status: Dict[str, int] = {}
    for row in doc["rows"]:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    print(f"PASS hardening_status: {len(doc['rows'])} H-row(s) valid — "
          + ", ".join(f"{v} {k}" for k, v in sorted(by_status.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
