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
import subprocess
import sys
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

# A row may only claim `closed` with both of these non-empty. `out_of_scope` needs a
# closing_revision too -- the commit that recorded the decision -- but no proof artifacts,
# because nothing was built.
CLOSED_REQUIRES = ("proof_artifacts", "closing_revision")


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
    errors = validate(load())
    if errors:
        print(f"FAIL hardening_status ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        return 1
    doc = load()
    by_status: Dict[str, int] = {}
    for row in doc["rows"]:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    print(f"PASS hardening_status: {len(doc['rows'])} H-row(s) valid — "
          + ", ".join(f"{v} {k}" for k, v in sorted(by_status.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
