#!/usr/bin/env python3
"""
Attach a blind Reviewer's verdicts to the packet it was shown, and file them.

Why this exists
---------------
The Fixer must never retype a verdict. `tests/attester_file.py` records why: on
2026-08-20 a stem shortened while pasting turned a transcription error into a filed
pipeline defect, and on 2026-08-28 a heredoc turned "x" into "x" so legitimate quotes
failed §5's provenance check. Both are the same failure -- a human (or an agent acting as
one) in the copy path.

So the Reviewer returns ONLY its verdicts and rationales. `sample_seeds` and
`samples_reviewed` are copied mechanically out of the packet the Reviewer was handed,
which is what makes the filed record provably about the content that was judged -- the
property §5's freshness check compares against.

Usage:
    python scripts/file_blind_reviews.py --packet <packet.json> --verdicts <verdicts.json>

`verdicts.json` is the Reviewer's raw output: a list of objects with node_id,
reviewed_by, review_date, blind, overall, findings.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JUDGMENT = REPO / "validation_reports" / "judgment"

REQUIRED_AXES = {
    "competency_fulfillment", "comprehensive_coverage", "cognitive_capacity",
    "variant_comprehensiveness", "competency_alignment", "scale_appropriateness",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="file blind reviews against their packet")
    ap.add_argument("--packet", required=True)
    ap.add_argument("--verdicts", required=True)
    args = ap.parse_args()

    packet = {n["node_id"]: n for n in json.loads(Path(args.packet).read_text(encoding="utf-8"))}
    verdicts = json.loads(Path(args.verdicts).read_text(encoding="utf-8"))

    written = []
    for v in verdicts:
        node_id = v["node_id"]
        if node_id not in packet:
            raise SystemExit(
                f"FATAL: verdict names {node_id!r}, which is not in the packet. A review "
                f"about a node the Reviewer was not shown is not evidence."
            )
        missing = REQUIRED_AXES - set(v.get("findings", {}))
        if missing:
            raise SystemExit(
                f"FATAL: {node_id} is missing axes {sorted(missing)}. §5 requires all six; "
                f"re-dispatch rather than filing a partial review."
            )
        pkt = packet[node_id]
        record = {
            "node_id": node_id,
            "reviewed_by": v["reviewed_by"],
            "review_date": v["review_date"],
            "blind": bool(v.get("blind", True)),
            "overall": v["overall"],
            "findings": v["findings"],
            # Mechanical, never retyped -- see the module docstring.
            "sample_seeds": pkt["sample_seeds"],
            "samples_reviewed": pkt["samples"],
        }
        out = JUDGMENT / node_id.rsplit("_", 1)[0] / f"{node_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append((node_id, v["overall"], out))

    for node_id, overall, out in written:
        print(f"  filed {node_id:18} {overall:8} -> {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
