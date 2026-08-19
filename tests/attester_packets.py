"""
Attester packets — the blind evidence a CAPABILITY_PROVIDERS entry has to survive.

Why this exists
---------------
Rule 9 of the hardening protocol says a `CAPABILITY_PROVIDERS` entry is a *claim that
the artifact produces what the clause names*. That is a semantic claim, and no
mechanical check can evaluate it: "does `task_type=draw_construct` constitute
*drawing*?" is a reading of MATATAG, not a lookup. §6D (validate_capability) can prove
a provider is a wildcard; it cannot prove a specific provider is the *right* one.

Until 2026-08-19 the only party answering that question was the Fixer, about its own
table, with a red line in front of it — the identical structure that produced two sets
of fabricated judgment reviews, and it produced the identical outcome: 474 of 485
entries satisfied by a generic textual formatter, and `run_all` exiting 0.

So the Attester (Rule 1's fourth blind role) answers it instead. It sees one clause and
N rendered student-path samples. It does **not** see:

  * `CAPABILITY_PROVIDERS`, or that an entry is being defended at all
  * the DNA, the formatter registry, or the generator source
  * the node id, which would let it look any of the above up

It answers one question per capability: *do these rendered items exhibit what this
clause names?* -> PROVIDED / NOT_PROVIDED, naming the sample that shows it.

Blindness is a prompt contract, not a sandbox (§6 Runtime). This module's job is to
make the blind half easy to hand over intact: `--packets` writes what the Attester
sees, `--key` writes the mapping it must not see.

Sampling uses `is_student_path=True` — the real serving path. `is_lab=True` bypasses
the competency-bound clamp, so a Lab sample can exhibit a capability the student path
can never reach, which is the exact false positive this role exists to prevent.

Usage:
    python -m tests.attester_packets --node mat_g3_mg_q1_5 \
        --packets local_only/scratch/attester/batch1.json \
        --key     local_only/scratch/attester/batch1.key.json
    python -m tests.attester_packets --unearned --limit 25 ...   # the §6D queue
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from backend.app.practice_gen.pipeline import run
from backend.app.practice_gen.registry import get_node_info
from backend.app.practice_gen.validation import validate_capability as VC

# Fixed so a packet is reproducible: an Attester verdict is about specific seeds, and
# a verdict that cannot be re-rendered is not evidence.
SAMPLE_SEEDS = [11, 23, 42, 57, 64, 78, 91, 103, 118, 127]


def _render(node_id: str, seed: int) -> Dict[str, Any] | None:
    """One student-path sample, reduced to what an Attester may see."""
    p = run(node_id, seed=seed, is_student_path=True)
    fd = p.get("format_data") or {}
    sample: Dict[str, Any] = {
        "seed": seed,
        "formatter": p.get("format") or p.get("formatter"),
        "question_text": p.get("question_text", ""),
        "correct_answer": p.get("correct_answer"),
    }
    options = fd.get("mcq_options") or fd.get("options")
    if options is not None:
        sample["options"] = options
    if p.get("hint"):
        sample["hint"] = p["hint"]
    if fd.get("cloze_text"):
        sample["cloze_text"] = fd["cloze_text"]
    # A visual capability is exhibited by the visual payload, not the stem. Carry the
    # payload's shape (keys and a short repr) so "does this render a table?" is
    # answerable from the packet without handing over the formatter source.
    visual = fd.get("visual") or fd.get("visual_data")
    if visual is not None:
        sample["visual_payload_keys"] = sorted(visual) if isinstance(visual, dict) else type(visual).__name__
        sample["visual_payload_excerpt"] = json.dumps(visual, ensure_ascii=False)[:600]
    return sample


def build(node_ids: List[str], capabilities: List[str] | None = None) -> tuple:
    """
    Returns (packets, key).

    `packets` is the blind half: an opaque item id, the clause, and the samples.
    `key` is the half the Attester must never see: which node and which registered
    provider each item is really about.
    """
    packets: List[Dict[str, Any]] = []
    key: Dict[str, Any] = {}
    n = 0

    for node_id in node_ids:
        meta = get_node_info(node_id) or {}
        requires = meta.get("requires") or []
        samples = []
        for seed in SAMPLE_SEEDS:
            s = _render(node_id, seed)
            if s is not None:
                samples.append(s)
        if not samples:
            raise RuntimeError(
                f"{node_id}: rendered no student-path samples across seeds {SAMPLE_SEEDS}. "
                f"An Attester cannot rule on an empty packet, and a capability with no "
                f"reachable content is a §6C failure, not a packet to file."
            )

        for req in requires:
            cap = str(req.get("id", ""))
            if capabilities is not None and cap not in capabilities:
                continue
            n += 1
            item = f"item_{n:03d}"
            packets.append({
                "item": item,
                "clause": req.get("clause"),
                "competency": meta.get("competency", ""),
                "grade": meta.get("grade"),
                "quarter": meta.get("quarter"),
                "question": (
                    "Do the rendered items below exhibit what this clause names? "
                    "Answer PROVIDED or NOT_PROVIDED and name the seed(s) that show it."
                ),
                "samples": samples,
            })
            key[item] = {
                "node_id": node_id,
                "capability_id": cap,
                "registered_provider": VC.CAPABILITY_PROVIDERS.get(cap),
            }
    return packets, key


def _unearned_targets() -> Dict[str, List[str]]:
    """The §6D queue: capabilities currently carried only by a generic formatter."""
    out: Dict[str, List[str]] = {}
    for e in VC.validate_capability_declarations():
        if "§6D" not in e:
            continue
        m = re.match(r"^(\S+): competency requires '([^']+)'", e)
        if m:
            out.setdefault(m.group(1), []).append(m.group(2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", action="append", default=[])
    ap.add_argument("--unearned", action="store_true",
                    help="build packets for every capability §6D reports as unearned")
    ap.add_argument("--limit", type=int, default=0, help="cap the number of items (batch <=25)")
    ap.add_argument("--packets", required=True)
    ap.add_argument("--key", required=True)
    args = ap.parse_args()

    caps = None
    nodes = list(args.node)
    if args.unearned:
        targets = _unearned_targets()
        nodes = nodes or sorted(targets)
        caps = sorted({c for n in nodes for c in targets.get(n, [])})
    if not nodes:
        raise SystemExit("no nodes selected: pass --node or --unearned")

    packets, key = build(nodes, caps)
    if args.limit:
        packets = packets[: args.limit]
        key = {k: v for k, v in key.items() if k in {p["item"] for p in packets}}

    for path, payload in ((args.packets, packets), (args.key, key)):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"packets: {len(packets)} item(s) -> {args.packets}")
    print(f"key:     {len(key)} mapping(s) -> {args.key}   (Attester must not see this)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
