"""
Attester filing — turn one blind Attester's verdicts into §6F/§6G-valid records.

Why this exists
---------------
`attester_packets.py` builds the blind half. The other half — taking what the
Attester said and writing it into `validation_reports/attestation/` — was being done
by hand, and the hardening protocol names hand transcription as a *measured* source of
defect: on 2026-08-20 a stem shortened while pasting turned a transcription error into
a filed pipeline defect. The same hand also has to resolve `item_007` back to a node id
and a capability id from the key file the Attester never saw. That mapping is
mechanical, so a human doing it is pure downside.

So the Fixer never retypes a verdict. The Attester returns JSON keyed by the opaque
`item` id; this module joins it to the key, splits it per node (§6F reads one record per
node), and copies `packet.samples_judged` straight out of the packet the Attester was
shown. Nothing about the verdict — string, seeds, or reasoning — is authored here.

What it refuses to write (all loud, none recoverable)
-----------------------------------------------------
Every one of these is a §6F/§6G failure that would otherwise be discovered *after*
filing, when the honest remedy is re-dispatching the Attester rather than editing the
record — which the protocol forbids outright. Catching them before the write is the
whole point:

  * a verdict for an item that is not in this packet, or a packet item with no verdict
  * a verdict string that is not PROVIDED / NOT_PROVIDED
  * empty reasoning (§6G hard fail — "a verdict without reasoning is a vote")
  * PROVIDED naming no seed (§6G)
  * a cited seed that is not in that record's own `packet.samples_judged` (§6G)
  * more than 25 verdicts in one record (§6G batch size)
  * a reasoning skeleton shared by more than 3 (node, capability) pairs *across the
    whole attestation tree*, which is the templated-batch check — so this fires on
    collision with records already on disk, not just within the incoming batch

`action_taken` is the Fixer's field, not the Attester's, and it is the only thing this
module writes that the Attester did not say. It must be supplied explicitly for every
NOT_PROVIDED: a NOT_PROVIDED is a §6F CONTRADICTED finding the moment it lands, and
"what you did about it" is not a value that has a sensible default.

Usage:
    python tests/attester_file.py \
        --packets  local_only/scratch/attester/t20/B04.json \
        --key      local_only/scratch/attester/t20/B04.key.json \
        --verdicts local_only/scratch/attester/t20/B04.verdicts.json \
        --batch-prefix batch024 \
        --attested-at 2026-08-23T00:00:00Z --tool-uses 1 \
        --samples-delivery "read local_only/scratch/attester/t20/B04.prompt.txt (packet render only)" \
        --action-provided "Left registered; no change." \
        --actions local_only/scratch/attester/t20/B04.actions.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from backend.app.practice_gen.validation.validate_capability import (
    _MAX_ATTESTER_SKELETON_CLUSTER,
    _attestation_records,
)
from backend.app.practice_gen.validation.validate_judgment import _rationale_skeleton

_OUT = Path(__file__).resolve().parents[1] / "validation_reports" / "attestation"
_VALID = {"PROVIDED", "NOT_PROVIDED"}

# What the Attester was told it may and may not see. Recorded verbatim in every record
# because §6F cannot check blindness — the record is the only place the contract is
# testified to, and a record that does not state it is indistinguishable from one where
# it was not honoured.
#
# `samples_delivery` is supplied per batch and is NOT a formality. The protocol's
# preferred mechanism is pasting the packet into the subagent prompt, but a 22-clause
# batch renders ~60k characters, and retyping that by hand is the precise defect
# `attester_packets.render_prompt_block` was written to remove (a stem shortened while
# pasting was filed as a pipeline defect on 2026-08-20). Handing the Attester the
# rendered packet file instead is mechanically safer and equally blind — the file holds
# only clause, competency, grade/quarter and samples — but it is a DIFFERENT contract
# from the one the older records assert, so it is recorded as what it was rather than
# flattened into `samples_passed_inline: True`. A record that misstates how the blind
# half was delivered is unauditable in exactly the way §6F cannot detect.
def _blindness(tool_uses: str, delivery: str) -> Dict[str, Any]:
    return {
        "saw": ["clause", "competency text", "grade/quarter", "10 rendered student-path samples"],
        "did_not_see": [
            "CAPABILITY_PROVIDERS or that any entry was being defended",
            "the node id",
            "the DNA, formatter registry, or generator source",
            "backend/app/practice_gen/dna/, formatters/, generators/, adapter.py, orchestrator.py",
            "validation_reports/, docs/, and every path under local_only/ except the one "
            "named in samples_delivery",
        ],
        "samples_delivery": delivery,
        "framing": "neutral - 'do these items exhibit what this clause names?', never 'find the defects'",
        "tool_uses_by_attester": tool_uses,
    }


def _load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_records(packets: List[Dict[str, Any]], key: Dict[str, Any],
                  verdicts: List[Dict[str, Any]], batch_prefix: str,
                  action_provided: str, actions: Dict[str, str],
                  attested_at: str, attested_by: str, tool_uses: str, delivery: str,
                  supersedes: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    by_item = {p["item"]: p for p in packets}

    seen = {}
    for v in verdicts:
        item = v.get("item")
        if item not in by_item:
            raise SystemExit(
                f"verdict names item {item!r}, which is not in this packet "
                f"({sorted(by_item)[:3]}...). The Attester answered about something it "
                f"was not shown, or the wrong key file was passed."
            )
        if item in seen:
            raise SystemExit(f"item {item!r} carries two verdicts. One dispatch, one verdict.")
        seen[item] = v
    missing = sorted(set(by_item) - set(seen))
    if missing:
        raise SystemExit(
            f"{len(missing)} packet item(s) have no verdict: {missing}. A partial batch "
            f"files a claim about clauses nobody judged — re-dispatch, do not file."
        )

    per_node: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item, v in sorted(seen.items()):
        k = key[item]
        node_id = k["node_id"]
        verdict = str(v.get("verdict", "")).strip().upper()
        if verdict not in _VALID:
            raise SystemExit(f"{item} ({node_id}): verdict {verdict!r} is not PROVIDED/NOT_PROVIDED.")
        reasoning = str(v.get("reasoning", "")).strip()
        if not reasoning:
            raise SystemExit(
                f"{item} ({node_id}, {k['capability_id']}): empty reasoning. §6G fails this "
                f"outright — a verdict without reasoning is a vote, and the contract does "
                f"not count votes."
            )
        seeds = [int(s) for s in (v.get("seeds_showing_it") or [])]
        packet_seeds = {s["seed"] for s in by_item[item]["samples"]}
        bad = sorted(set(seeds) - packet_seeds)
        if bad:
            raise SystemExit(
                f"{item} ({node_id}, {k['capability_id']}): cites seed(s) {bad} that are not "
                f"in the samples it was shown {sorted(packet_seeds)} (§6G seed provenance)."
            )
        if verdict == "PROVIDED" and not seeds:
            raise SystemExit(
                f"{item} ({node_id}, {k['capability_id']}): PROVIDED but names no seed (§6G)."
            )
        if verdict == "NOT_PROVIDED" and item not in actions:
            raise SystemExit(
                f"{item} ({node_id}, {k['capability_id']}): NOT_PROVIDED with no action_taken. "
                f"This lands as a §6F CONTRADICTED finding the moment it is filed; say what "
                f"you did about it. Supply it in --actions keyed by item id."
            )
        entry = {
            "capability_id": k["capability_id"],
            "node_id": node_id,
            "clause": by_item[item]["clause"],
            "verdict": verdict,
            "seeds_showing_it": seeds,
            "reasoning": reasoning,
            "action_taken": actions.get(item, action_provided),
        }
        note = str(v.get("content_note", "")).strip()
        if note:
            entry["content_note_from_attester"] = note
        per_node[node_id].append(entry)

    records: Dict[str, Dict[str, Any]] = {}
    for node_id, entries in per_node.items():
        if len(entries) > 25:
            raise SystemExit(f"{node_id}: {len(entries)} verdicts in one record (§6G max 25).")
        samples = next(p["samples"] for p in packets if key[p["item"]]["node_id"] == node_id)
        batch = f"{batch_prefix}_{node_id}"
        rec = {
            "batch": batch,
            "attested_at": attested_at,
            # §6H: a verdict must name who made it, or its independence cannot be checked.
            # All 173 records filed before 2026-08-28 carry no identity at all, which is why
            # attester plurality was unenforceable while §5's has always been enforced.
            "attested_by": attested_by,
            "role": "Attester",
            "blindness": _blindness(tool_uses, delivery),
            "packet": {
                "builder": "tests/attester_packets.py",
                "filed_by": "tests/attester_file.py (mechanical join on the key the Attester never saw)",
                "sampling": "is_student_path=True",
                "node_id": node_id,
                "seeds": [s["seed"] for s in samples],
                "samples_judged": [
                    {"seed": s["seed"], "question_text": s["question_text"],
                     "correct_answer": s["correct_answer"], "formatter": s["formatter"]}
                    for s in samples
                ],
            },
            "verdicts": entries,
        }
        if node_id in supersedes:
            rec["supersedes"] = supersedes[node_id]
        records[batch] = rec
    return records


def check_skeletons(records: Dict[str, Dict[str, Any]]) -> None:
    """§6G clustering is tree-wide, so collide the incoming batch against what is on disk."""
    clusters: Dict[str, List[tuple]] = defaultdict(list)
    for rec in _attestation_records():
        if rec.get("batch") in records:
            continue
        for v in rec.get("verdicts") or []:
            clusters[_rationale_skeleton(str(v.get("reasoning", "")))].append(
                (v.get("node_id"), v.get("capability_id"), "on-disk"))
    for rec in records.values():
        for v in rec["verdicts"]:
            clusters[_rationale_skeleton(v["reasoning"])].append(
                (v["node_id"], v["capability_id"], "incoming"))
    over = {s: p for s, p in clusters.items() if len(p) > _MAX_ATTESTER_SKELETON_CLUSTER}
    if over:
        lines = [f"  {len(p)} pairs share {s[:100]!r}: {sorted(p)[:6]}" for s, p in over.items()]
        raise SystemExit(
            "§6G skeleton clustering would fail — the batch is the bug, not the check.\n"
            + "\n".join(lines)
            + "\nRe-dispatch the Attester and let it write its own reasoning per clause. "
              "Never edit a record to satisfy this, and never lower the threshold."
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--verdicts", required=True)
    ap.add_argument("--batch-prefix", required=True)
    ap.add_argument("--attested-at", required=True)
    ap.add_argument("--attested-by", required=True,
                    help="the Attester identity (§6H); one identity may cover <=25 nodes")
    ap.add_argument("--action-provided", required=True)
    ap.add_argument("--actions", help="JSON map item_id -> action_taken (required for NOT_PROVIDED)")
    ap.add_argument("--supersedes", help="JSON map node_id -> supersession note")
    # Free-form, and deliberately not an int. `tool_uses_by_attester: 0` is an
    # evidentiary claim, not a statistic: it says the Attester had no way to reach a
    # forbidden path even if the prompt contract failed, so blindness was structural.
    # A dispatch that hands the Attester a packet *file* cannot make that claim — it
    # used at least one Read — and quietly writing an integer there would assert
    # structural blindness the dispatch did not have. Say which one it was.
    ap.add_argument("--tool-uses", required=True,
                    help="what is actually known about the Attester's tool use. '0' claims "
                         "no tool access at all (inline dispatch); anything else must say "
                         "plainly what was and was not verified")
    ap.add_argument("--samples-delivery", required=True,
                    help="how the blind half reached the Attester, recorded verbatim in "
                         "the record's blindness block (e.g. 'pasted inline into the "
                         "subagent prompt', or the exact packet path it was told to read)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    records = build_records(
        _load(args.packets), _load(args.key), _load(args.verdicts), args.batch_prefix,
        args.action_provided, _load(args.actions) if args.actions else {},
        args.attested_at, args.attested_by, args.tool_uses, args.samples_delivery,
        _load(args.supersedes) if args.supersedes else {},
    )
    check_skeletons(records)

    for batch, rec in sorted(records.items()):
        n = len(rec["verdicts"])
        prov = sum(1 for v in rec["verdicts"] if v["verdict"] == "PROVIDED")
        path = _OUT / f"{batch}.json"
        if not args.dry_run:
            path.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{'would write' if args.dry_run else 'wrote'} {path.name}: "
              f"{n} verdict(s), {prov} PROVIDED, {n - prov} NOT_PROVIDED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
