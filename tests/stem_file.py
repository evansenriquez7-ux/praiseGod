"""
stem_file.py -- write a §17 judge's prompt, and file the judge's reply without retyping it (owner
rulings 20, 24, 29 and 44; batch H4).

Two subcommands, the two halves of one dispatch:

  prompt   Writes the exact text a judge reads for ONE packet item (the instructions below plus
           the item, printed whole by `stem_packets.prompt_block`) to a file the judge is told to
           read. Delivery by file (memory: "Attester dispatch gotchas"): retyping a packet into a
           prompt is how a shortened stem became a filed defect on 2026-08-20.

  file     Turns one reply into one record under validation_reports/stem_review/<lc>/. What it
           takes from the JUDGE is the raw reply, byte for byte; everything else is the
           dispatcher's or the packet's:
             * the packet is copied from the packets file WRITTEN AT DISPATCH TIME, never rebuilt
               (tests/file_reviews.py's lesson: rebuilding at filing time pairs a verdict with
               content the judge never saw, and freshness then passes the fabrication). A
               generator change between dispatch and filing therefore shows up as STALE, which
               is the honest result;
             * the lc and its family keys come from the key file the judge never saw;
             * the identity (`--judged-by`, which must name the model that judged) and the
               dispatch id are assigned by the dispatcher; a reply cannot choose them.
           It refuses -- loudly, writing nothing -- everything §17 would reject on that record:
           an item not in the packet, a reply that does not parse or whose verdict is invalid
           against its packet (`validate_stem_review.verdict_problems`), a quote its packet does
           not contain, a placeholder identity, an identity already used on another lc, a
           confirming record whose first record is missing, of another hash or of the same
           identity, and any record path that already exists (records are never overwritten).

Usage:
    PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.stem_packets \\
        --nodes mat_g2_na_q3_8 --prefix S441 --packets P.json --key K.json
    PYTHONPATH=. .venv/bin/python tests/stem_file.py prompt --packets P.json --item S441-001 --out prompt.txt
    PYTHONPATH=. .venv/bin/python tests/stem_file.py file --packets P.json --key K.json --item S441-001 \\
        --reply reply.txt --role first --judged-by blind-stem-judge-claude-haiku-...-S441-001-first \\
        --dispatch-id stem-batch441-S441-001-first --filed-at 2026-10-14T10:00:00Z \\
        --delivery "judge read only prompt.txt; dispatched with CLAUDE.md loaded (ruling 29)" \\
        --tool-uses "read prompt.txt; replied with one JSON object" --prompt prompt.txt
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.practice_gen.validation import stem_packets as SP  # noqa: E402
from backend.app.practice_gen.validation import validate_stem_review as VSR  # noqa: E402
from backend.app.practice_gen.validation.validate_judgment import _rationale_skeleton, _MAX_SKELETON_CLUSTER  # noqa: E402

# The judge's instructions. They say how to READ the packet and what to rule; they never say what
# the answer is (owner ruling 1: never encode the answer in a dispatch prompt) and state no
# numeric threshold that no ruling states (ruling 19).
INSTRUCTIONS = """\
You are a judge in this project's testing pipeline (see "If you are a judge" in CLAUDE.md).
Read ONLY this file. Do not open any other file, run code, or search.

This file is one item. It describes ONE learning competency (lc) of the MATATAG curriculum:
its competency text, its clauses, the vocabulary it may use (cumulative_vocab, the vocabulary
introduced here, and NOT_YET_KNOWN terms it must never use), its declared variants and bounds,
and EVERY family of learner-facing text its problem generator prints. A family has an id
(F01, F02, ...) and a template; two families may print the same template. "appears_in" names
the fields of the problem where the learner reads that family's text: "question_text" is the
question; "hints" are hints; "correct_answer" is the keyed answer; "distractors",
"format_data.options" and "format_data.mcq_options" are answer choices; other "format_data.*"
fields are text shown with the item (a sentence, statement, expression, name, time or
direction). "nested_in" names the families whose text this family's text is printed inside.
Judge each family where it appears: an answer choice is one choice, not a whole question.
Each {slot} in a template is filled from a declared domain:
  - "one of a fixed list": a member of the named list in "lists";
  - "a field of a fixed item bank": the named field of a row of the named bank in "banks". A
    bank is printed row by row. Where its "one_row_per_problem" is true, every field a problem
    prints from that bank comes from ONE row: judge each row as one problem (its question, its
    own keyed answer, its own distractors). Where it is false, one problem may print fields of
    the bank from different rows. A field whose value is a list (such as "distractors") gives
    one answer choice per member. Only the rows this lc draws are printed; "rows_left_out"
    counts the bank's other rows, which this lc never prints. Where a slot's domain says
    "read_from": "the row drawn for the problem", the slot prints a member of that field of the
    SAME row the problem's other fields of that bank come from;
  - "the one word a vocabulary gate gives this lc": the word in "prints". The generator picks it
    by whether this lc may use "requires_vocab"; for this lc it is always that word, and the
    gate's other word is never printed (it is left out, "words_left_out");
  - "a noun from a fixed list, or its plural": a member of the named list, or its plural;
  - "a number in a range": any number from lo to hi;
  - "one of the generator's own choices": every member the generator offered across the renders
    enumerated. Where its basis says it is the value itself (for example "the keyed answer"),
    the list shows what was observed and does not bound the slot: treat it as unbounded;
  - "repeats a generated value": the generated value named by "key" (its range is set by the
    declared bounds);
  - "nested learner text": the text of the listed families;
  - "a number computed by the generator" / "text computed by the generator": a value computed
    from the generated values in derived_from_values, for the reason given in reason_kinds.
"derived_from_values", "template_chosen_by_values" and "value_derivations" are the generator's
own claims about which generated values a slot, a template choice or a value comes from.
A separate deterministic check proves every value a learner sees stays inside these domains,
so judge the domains as the full set of what can appear.

Rule 1 (overall): could ANY value in these domains, filled into these templates, produce text
that is wrong for a learner of this lc: an incorrect or misleading statement, wording a learner
of this grade and quarter cannot read, vocabulary or a concept beyond the lc's gates, a context
or load beyond the grade and quarter, or content outside or short of the competency's scope?
PASS if none can. FAIL if any can: list the id of EVERY family at fault in failing_families,
and each of their templates, copied exactly as printed, in failing_templates.

Rule 2 (clauses): for EVERY clause id, PRODUCIBLE if these families and declared variants can
produce problems that address that clause, giving in "family" the id of the one family that
best produces it and in "template" its template, copied exactly as printed; otherwise
NOT_PRODUCIBLE with "family": null and "template": null.

Quote exactly. Any text you put in quotation marks must appear in this file. Do not guess.

Reply with exactly ONE JSON object and nothing else:
{"item": "<this item's id>",
 "clauses": {"<clause id>": {"verdict": "PRODUCIBLE" or "NOT_PRODUCIBLE",
                             "family": "<family id, or null>",
                             "template": "<its exact template, or null>",
                             "reasoning": "<why>"}, ...one entry per clause id...},
 "failing_families": ["<family id>", ...],
 "failing_templates": ["<exact template>", ...],
 "overall": "PASS" or "FAIL",
 "reasoning": "<why, citing the templates and domains you relied on>"}

THE ITEM:
"""


def _load_item(packets_path: str, item_id: str) -> Dict[str, Any]:
    packets = json.loads(Path(packets_path).read_text(encoding="utf-8"))
    hits = [p for p in packets if p.get("item") == item_id]
    if len(hits) != 1:
        raise SystemExit(f"REFUSED: item {item_id!r} is in {packets_path} {len(hits)} time(s), not once")
    return hits[0]


def prompt_text(item: Dict[str, Any]) -> str:
    body = {k: v for k, v in item.items() if k != "item"}
    return INSTRUCTIONS + SP.prompt_block(body, item["item"]) + "\n"


def cmd_prompt(args) -> int:
    item = _load_item(args.packets, args.item)
    Path(args.out).write_text(prompt_text(item), encoding="utf-8")
    print(f"wrote {args.out} ({len(prompt_text(item))} characters) for {args.item}")
    return 0


def build_record(item: Dict[str, Any], key: Dict[str, Any], raw: str, args) -> Dict[str, Any]:
    """The record, in the order a reader wants it. Raises SystemExit on any refusal."""
    body = {k: v for k, v in item.items() if k != "item"}
    lc_hash = SP.item_hash(body)
    if key.get("item_hash") != lc_hash:
        raise SystemExit(f"REFUSED: the key's item_hash {str(key.get('item_hash'))[:12]} is not the packet's "
                         f"{lc_hash[:12]}: packets and key are not one dispatch")
    try:
        datetime.fromisoformat(args.filed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(f"REFUSED: --filed-at {args.filed_at!r} is not ISO 8601: {exc}")
    prompt_digest = hashlib.sha256(Path(args.prompt).read_bytes()).hexdigest()
    if Path(args.prompt).read_text(encoding="utf-8") != prompt_text(item):
        raise SystemExit(f"REFUSED: {args.prompt} is not the prompt this tool writes for {item['item']}")
    return {
        "schema_version": VSR.SCHEMA_VERSION,
        "hash_version": SP.HASH_VERSION,
        "node_id": key["node_id"],
        "record_id": args.dispatch_id,
        "role": args.role,
        "confirms": args.confirms,
        "item_id": item["item"],
        "lc_hash": lc_hash,
        "judged_by": args.judged_by,
        "dispatch_id": args.dispatch_id,
        "filed_at": args.filed_at,
        "delivery": args.delivery,
        "tool_uses_by_judge": args.tool_uses,
        "dispatch_prompt_digest": prompt_digest,
        "raw_reply": raw,
        "raw_reply_digest": VSR.reply_digest(raw),
        "packet_digest": SP.digest(item),
        "family_keys": key["families"],
        "packet": item,
    }


def refusals(rec: Dict[str, Any], review_dir: Path) -> List[str]:
    """Everything §17 would reject on this record, checked against the records already filed."""
    fixture = review_dir.resolve() != VSR.REVIEW_DIR.resolve()
    bad, drift = VSR.record_problems(rec, fixture)
    out = bad + drift
    if not out:
        out += VSR.quote_problems(rec)
    existing = [r for _p, r in VSR.load_records(review_dir) if "__unparseable__" not in r]
    others = sorted({r.get("node_id") for r in existing if r.get("judged_by") == rec["judged_by"]} - {rec["node_id"]})
    if others:
        out.append(f"judged_by {rec['judged_by']!r} is already on records of {others}")
    if any(r.get("dispatch_id") == rec["dispatch_id"] for r in existing):
        out.append(f"dispatch id {rec['dispatch_id']!r} is already filed")
    if not bad and "_verdict" in rec:
        sk = _rationale_skeleton(rec["_verdict"]["reasoning"])
        # Only records §17 counts (valid on their own bytes) are compared, as §17 compares them.
        lcs = {r.get("node_id") for r in existing
               if not any(VSR.record_problems(r, fixture)) and _rationale_skeleton(r["_verdict"]["reasoning"]) == sk}
        lcs |= {rec["node_id"]}
        if len(lcs) > _MAX_SKELETON_CLUSTER:
            out.append(f"its reasoning frame is shared by {len(lcs)} lcs (max {_MAX_SKELETON_CLUSTER})")
    if rec["role"] == "confirming":
        first = [r for r in existing if r.get("node_id") == rec["node_id"] and r.get("record_id") == rec["confirms"]]
        if not first:
            out.append(f"it confirms {rec['confirms']!r}, which is not filed for {rec['node_id']}")
        elif first[0].get("role") != "first" or first[0].get("lc_hash") != rec["lc_hash"]:
            out.append(f"{rec['confirms']!r} is not a first record on the same hash")
        elif first[0].get("judged_by") == rec["judged_by"] or first[0].get("dispatch_id") == rec["dispatch_id"]:
            out.append("the confirming judge must not share the first judge's identity or dispatch")
    return out


def cmd_file(args) -> int:
    item = _load_item(args.packets, args.item)
    keys = json.loads(Path(args.key).read_text(encoding="utf-8"))
    if args.item not in keys:
        raise SystemExit(f"REFUSED: item {args.item!r} is not in the key file {args.key}")
    raw = Path(args.reply).read_text(encoding="utf-8")
    rec = build_record(item, keys[args.item], raw, args)
    review_dir = Path(args.review_dir)
    problems = refusals(rec, review_dir)
    if problems:
        raise SystemExit("REFUSED (nothing written):\n  - " + "\n  - ".join(problems))
    rec.pop("_verdict", None)
    out = review_dir / rec["node_id"] / f"{rec['record_id']}.json"
    if out.exists():
        raise SystemExit(f"REFUSED: {out} exists; records are never overwritten")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"filed {out} ({rec['role']}, {VSR.parse_reply(raw)['overall']})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt")
    p.add_argument("--packets", required=True)
    p.add_argument("--item", required=True)
    p.add_argument("--out", required=True)
    f = sub.add_parser("file")
    for name in ("--packets", "--key", "--item", "--reply", "--judged-by", "--dispatch-id", "--filed-at",
                 "--delivery", "--tool-uses", "--prompt"):
        f.add_argument(name, required=True)
    f.add_argument("--role", required=True, choices=VSR.ROLES)
    f.add_argument("--confirms", default=None, help="record id of the first record (confirming role only)")
    f.add_argument("--review-dir", default=str(VSR.REVIEW_DIR))
    args = ap.parse_args()
    return cmd_prompt(args) if args.cmd == "prompt" else cmd_file(args)


if __name__ == "__main__":
    sys.exit(main())
