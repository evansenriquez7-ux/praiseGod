#!/usr/bin/env python3
"""
Keep the hardening ledger small enough that committing it is cheap.

Why this exists
---------------
The ledger is append-only and tracked, so every tick rewrites the whole file as a new
git blob. By 2026-08-26 it was 2.0 MB over 18,625 lines and 489 ticks, and its blobs
accounted for 552 MB across 2,680 objects in history (126 MB packed). The 2026-08-24
run alone committed it 467 times in 40 hours -- 463 of those commits contained nothing
else, because a campaign deadlock left "write a ledger entry" as the only legal act.

That deadlock is fixed in the runners (they now stop after HARDENING_NOOP_TICK_LIMIT
unproductive ticks). This handles the other half: the active ledger stays bounded, and
older entries move to a dated archive beside it rather than being deleted.

Nothing is ever discarded. Entries are moved, and the archive is appended to.

Usage
-----
    PYTHONPATH=. .venv/bin/python3 scripts/rotate_ledger.py            # rotate if needed
    PYTHONPATH=. .venv/bin/python3 scripts/rotate_ledger.py --check    # report only
    PYTHONPATH=. .venv/bin/python3 scripts/rotate_ledger.py --keep 40  # keep 40 ticks
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "local_only/scratch/hardening_ledger.md"
ARCHIVE_DIR = LEDGER.parent / "ledger_archive"

# Entries begin with a level-2 heading: "## 2026-08-26 — tick 489 — ...".
ENTRY = re.compile(r"^## \d{4}-\d{2}-\d{2} — tick ", re.MULTILINE)

DEFAULT_KEEP = 60


def split_entries(text: str) -> tuple[str, list[str]]:
    """Return (preamble, [entry, ...]) without losing a byte."""
    starts = [m.start() for m in ENTRY.finditer(text)]
    if not starts:
        return text, []
    preamble = text[: starts[0]]
    bounds = starts + [len(text)]
    return preamble, [text[bounds[i]:bounds[i + 1]] for i in range(len(starts))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep", type=int, default=DEFAULT_KEEP,
                    help=f"how many recent tick entries stay in the active ledger (default {DEFAULT_KEEP})")
    ap.add_argument("--check", action="store_true", help="report and exit without writing")
    args = ap.parse_args()

    if not LEDGER.exists():
        print(f"no ledger at {LEDGER.relative_to(REPO)} — nothing to rotate.")
        return 0

    text = LEDGER.read_text(encoding="utf-8")
    preamble, entries = split_entries(text)
    size_mb = len(text.encode("utf-8")) / 1_048_576

    print(f"ledger: {size_mb:.2f} MB, {len(text.splitlines())} lines, {len(entries)} tick entries")
    if len(entries) <= args.keep:
        print(f"at or under the {args.keep}-entry bound — no rotation needed.")
        return 0

    move, keep = entries[: len(entries) - args.keep], entries[len(entries) - args.keep:]
    archive = ARCHIVE_DIR / f"hardening_ledger_{date.today().isoformat()}.md"
    print(f"would move {len(move)} entry(ies) to {archive.relative_to(REPO)}, "
          f"keeping the most recent {len(keep)}")
    if args.check:
        return 0

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    header = "" if archive.exists() else (
        "# Hardening ledger archive\n\n"
        "Rotated out of `local_only/scratch/hardening_ledger.md` to keep the active file\n"
        "cheap to commit. Nothing here was edited; entries are verbatim and in order.\n"
    )
    with archive.open("a", encoding="utf-8") as fh:
        fh.write(header)
        fh.write("".join(move))

    # Write the trimmed ledger only after the archive is safely on disk.
    LEDGER.write_text(preamble + "".join(keep), encoding="utf-8")
    new_mb = LEDGER.stat().st_size / 1_048_576
    print(f"rotated: active ledger now {new_mb:.2f} MB ({len(keep)} entries); "
          f"{len(move)} archived to {archive.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
