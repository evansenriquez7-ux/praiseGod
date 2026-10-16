"""
§17 -- every lc's current stems carry a fresh, valid, confirmed blind approval (owner rulings
20, 24, 26, 29, 42 and 44; batch H4).

Ruling 24 makes the LLM judge's unit the STEM TEMPLATE plus the declared domain of every slot
that fills it; §14 proves every rendered field stays inside those domains. This stage is the
other half: it fails when an lc's current stems are not covered by an approval. For every lc it
rebuilds the stem packet from the live record (`stem_packets.build_item`, over the same
`validate_slots.paths()` §14 renders) and reads the filed records in
`validation_reports/stem_review/<lc>/`:

  stem_family_unpacketed_17   (INTEGRITY) a learner-read field whose producing family is not in
                              the packet: the builder dropped something a judge never saw
  stem_review_hash_drift_17   (INTEGRITY) a record whose stored packet no longer hashes to its
                              stored `lc_hash` under the same HASH_VERSION: the freshness code
                              changed, so every verdict it compares is suspect
  stem_review_record_invalid_17  a record that is malformed, edited (its verdict is not what its
                              raw reply says, or a digest does not hold), cites a template or
                              family id the packet does not print, names family ids that do not
                              print exactly the templates it quotes (ruling 46b), or omits a
                              clause verdict
  stem_review_quote_provenance_17  a reasoning that quotes text its own packet does not contain
  stem_review_identity_reused_17   one `judged_by` identity on records of more than one lc
                              (ruling 44: one dispatch per lc and role)
  stem_review_skeleton_17     one reasoning sentence frame across more than
                              `validate_judgment._MAX_SKELETON_CLUSTER` lcs (a template, not a
                              judgment)
  stem_review_missing_17      an lc with no valid record
  stem_review_stale_17        the standing record's `lc_hash` differs from the live packet's
                              (a template, member, bound, provenance claim or clause moved), or
                              it was filed under another HASH_VERSION
  stem_review_unconfirmed_17  the standing record is not a confirming judge's record that names a
                              valid first record on the same hash by a different identity
                              (ruling 20 as ruling 44e applies it: every lc, PASS or FAIL)
  stem_review_fail_17         the standing (later, confirming) verdict is FAIL; named by the
                              failing family ids and templates the judge gave and a path that
                              reaches each
  stem_clause_unproducible_17 the standing verdict rules a clause NOT_PRODUCIBLE (ruling 44g)

Everything but the two INTEGRITY labels is CONTENT (ruling 44f): its remedy is a generator fix
or a fresh review, not harness work. Record checks (validity, quotes, identity, skeleton) run
over EVERY record in the directory; the per-lc checks run over the lcs in scope.

CLI (proof mode reads a fixture directory):

    PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.validate_stem_review \
        [--node-ids a,b] [--review-dir DIR]

NAMED LIMITS (Scaling Mandate 6; also in docs/pgen_contract.md §17 and the evidence log):
  1. Paths are `validate_slots.paths()` (stem_packets limit 1): a family reached only elsewhere is
     neither reviewed nor domain-checked.
  2. A verdict is a READING by one model, not a proof. Ruling 20 accepts a measured ~22% single-
     judge flip rate; ruling 44e confirms every lc, and the later verdict stands.
  3. Blindness is a prompt contract: the record's `delivery` field testifies to it (and that the
     judge saw CLAUDE.md, ruling 29); nothing here can verify what the judge read.
  4. Tamper detection: the verdict is the raw reply parsed (never a separate field), and the reply
     is bound to its digest inside the record. An edit that rewrites reply and digest together is
     not detectable here (as §5's dispatch provenance); git history is the only witness.
  5. Quote provenance checks quoted spans only; an unquoted false claim about the packet passes.
  6. The per-lc verdict names failing TEMPLATES and their family ids (ruling 44d: no per-family
     verdicts; ruling 46b: ids beside quotes), so a FAIL names the families the judge named, not
     necessarily every family at fault.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.app.practice_gen.validation import stem_packets as SP
from backend.app.practice_gen.validation.validate_judgment import (
    _MAX_SKELETON_CLUSTER,
    _MIN_QUOTE_LEN,
    _QUOTE_RE,
    _flatten_shown,
    _rationale_skeleton,
)

ASSERTIONS = (
    "stem_family_unpacketed_17",        # a learner-read field whose family the packet omits (integrity)
    "stem_review_hash_drift_17",        # a stored packet no longer hashes to its stored lc_hash (integrity)
    "stem_review_record_invalid_17",    # a malformed or edited record, or one citing what its packet lacks
    "stem_review_quote_provenance_17",  # a reasoning quoting text absent from its own packet
    "stem_review_identity_reused_17",   # one judged_by identity on more than one lc
    "stem_review_skeleton_17",          # one reasoning frame across too many lcs
    "stem_review_missing_17",           # an lc with no valid record
    "stem_review_stale_17",             # the standing record's hash differs from the live packet's
    "stem_review_unconfirmed_17",       # the standing record has no valid confirming judge
    "stem_review_fail_17",              # the standing verdict is FAIL
    "stem_clause_unproducible_17",      # the standing verdict rules a clause NOT_PRODUCIBLE
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
REVIEW_DIR = _REPO_ROOT / "validation_reports" / "stem_review"

# 2 (2026-10-14, owner ruling 46b): a reply names family IDS beside the templates it quotes.
SCHEMA_VERSION = 2
ROLES = ("first", "confirming")
OVERALL = ("PASS", "FAIL")
CLAUSE_VERDICTS = ("PRODUCIBLE", "NOT_PRODUCIBLE")
_MIN_REASONING = 40
_PLACEHOLDER_IDS = {"", "judge", "reviewer", "agent", "tbd", "todo"}
# A fixture record (tests/fixtures/stem_review/) is hand-built for mutation proofs, never a judge's
# verdict: its identity carries this prefix and it is refused anywhere but a fixture directory.
FIXTURE_PREFIX = "fixture-not-a-judge"
_REQUIRED = ("schema_version", "hash_version", "node_id", "record_id", "role", "confirms", "item_id",
             "lc_hash", "packet", "packet_digest", "family_keys", "raw_reply", "raw_reply_digest",
             "judged_by", "dispatch_id", "filed_at", "delivery", "tool_uses_by_judge")


def reply_digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_reply(raw: str) -> Dict[str, Any]:
    """
    A judge's raw reply as JSON. One optional ```json fence is removed; nothing else is
    repaired (a reply that does not parse is set aside and re-dispatched, never fixed by hand).
    The filer and this validator share this one function.
    """
    text = raw.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.S)
    return json.loads(fence.group(1) if fence else text)


def verdict_problems(verdict: Any, packet: Dict[str, Any]) -> List[str]:
    """What is wrong with a reply's verdict against the packet it answered (empty = valid)."""
    out: List[str] = []
    if not isinstance(verdict, dict):
        return ["the verdict is not a JSON object"]
    if verdict.get("item") != packet.get("item"):
        out.append(f"the reply answers item {verdict.get('item')!r}, the packet is {packet.get('item')!r}")
    if verdict.get("overall") not in OVERALL:
        out.append(f"overall {verdict.get('overall')!r} is not one of {OVERALL}")
    reasoning = verdict.get("reasoning")
    if not isinstance(reasoning, str) or len(reasoning.strip()) < _MIN_REASONING:
        out.append(f"the overall reasoning is missing or shorter than {_MIN_REASONING} characters")
    templates = {f["template"] for f in packet.get("families", [])}
    # Ruling 46b: two families can print the identical template ('{answer}' from the options
    # and from a bank, measured on 54 of 151 lcs), so a quoted template alone cannot say which
    # family a verdict means. The reply names family ids too, and ids and quotes must agree.
    template_of = {f["id"]: f["template"] for f in packet.get("families", [])}
    failing = verdict.get("failing_templates")
    fam_ids = verdict.get("failing_families")
    if not isinstance(failing, list):
        out.append("failing_templates is not a list")
    elif not isinstance(fam_ids, list):
        out.append("failing_families is not a list (ruling 46b: a reply names the failing family ids)")
    else:
        if verdict.get("overall") == "FAIL" and not (failing and fam_ids):
            out.append("a FAIL names no failing template or family (rulings 44e, 46b: it must quote both)")
        out += [f"failing template {t!r} is not a template the packet prints" for t in failing if t not in templates]
        out += [f"failing family {i!r} is not a family id the packet prints" for i in fam_ids if i not in template_of]
        named = {template_of[i] for i in fam_ids if i in template_of}
        if all(i in template_of for i in fam_ids) and named != set(failing):
            out.append(f"failing_families {sorted(fam_ids)} print the template(s) {sorted(named)}, not exactly the "
                       f"failing_templates {sorted(set(failing))} (ruling 46b)")
    clauses = verdict.get("clauses")
    want = [c["id"] for c in packet.get("clauses", [])]
    if not isinstance(clauses, dict):
        out.append("clauses is not an object keyed by clause id")
    else:
        if sorted(clauses) != sorted(want):
            out.append(f"clause verdicts {sorted(clauses)} are not exactly the packet's clauses {sorted(want)}")
        for cid, c in clauses.items():
            if not isinstance(c, dict) or c.get("verdict") not in CLAUSE_VERDICTS:
                out.append(f"clause {cid!r}: verdict is not one of {CLAUSE_VERDICTS}")
                continue
            if not isinstance(c.get("reasoning"), str) or not c["reasoning"].strip():
                out.append(f"clause {cid!r}: empty reasoning")
            if c["verdict"] == "PRODUCIBLE" and c.get("template") not in templates:
                out.append(f"clause {cid!r}: PRODUCIBLE must quote a template the packet prints, got {c.get('template')!r}")
            elif c["verdict"] == "PRODUCIBLE" and template_of.get(c.get("family")) != c.get("template"):
                out.append(f"clause {cid!r}: family {c.get('family')!r} is not a packet family printing the quoted "
                           f"template {c.get('template')!r} (ruling 46b)")
            elif c["verdict"] == "NOT_PRODUCIBLE" and (c.get("template") is not None or c.get("family") is not None):
                out.append(f"clause {cid!r}: NOT_PRODUCIBLE quotes no template and no family")
    return out


def record_problems(rec: Dict[str, Any], fixture_dir: bool) -> Tuple[List[str], List[str]]:
    """(record_invalid problems, hash_drift problems) for one record, from its own bytes alone."""
    missing = [k for k in _REQUIRED if k not in rec]
    if missing:
        return [f"missing field(s) {missing}"], []
    out: List[str] = []
    if rec["schema_version"] != SCHEMA_VERSION:
        out.append(f"schema_version {rec['schema_version']!r} is not {SCHEMA_VERSION}")
    if rec["role"] not in ROLES:
        out.append(f"role {rec['role']!r} is not one of {ROLES}")
    if (rec["role"] == "confirming") != bool(rec["confirms"]):
        out.append("a confirming record must name the record it confirms, and a first record none")
    who = str(rec["judged_by"]).strip()
    if who.lower() in _PLACEHOLDER_IDS:
        out.append(f"judged_by {who!r} is a placeholder, not the model that judged")
    if who.startswith(FIXTURE_PREFIX) and not fixture_dir:
        out.append(f"judged_by {who!r} is a mutation-proof fixture identity, refused outside a fixture directory")
    if "CLAUDE.md" not in str(rec["delivery"]):
        out.append("the delivery field does not state that the judge was dispatched with CLAUDE.md (ruling 29)")
    packet = rec["packet"]
    if not isinstance(packet, dict) or packet.get("item") != rec["item_id"]:
        return out + ["the stored packet is not an object for this record's item_id"], []
    if SP.digest(packet) != rec["packet_digest"]:
        out.append("the stored packet does not match its packet_digest (edited after filing)")
    if reply_digest(rec["raw_reply"]) != rec["raw_reply_digest"]:
        out.append("the raw reply does not match its raw_reply_digest (edited after filing)")
    # The verdict is never stored beside the reply: it IS the reply, parsed by the one function
    # the filer used, and the reply is bound to its digest. An edited verdict is an edited reply.
    try:
        parsed = parse_reply(rec["raw_reply"])
    except (json.JSONDecodeError, TypeError, AttributeError) as exc:
        return out + [f"the raw reply does not parse: {type(exc).__name__}: {exc}"], []
    rec["_verdict"] = parsed
    out += verdict_problems(parsed, packet)
    drift: List[str] = []
    if rec["hash_version"] == SP.HASH_VERSION and SP.item_hash(packet) != rec["lc_hash"] \
            and SP.digest(packet) == rec["packet_digest"]:
        drift.append(f"the stored packet hashes to {SP.item_hash(packet)[:12]} under HASH_VERSION "
                     f"{SP.HASH_VERSION}, the record says {rec['lc_hash'][:12]}: the freshness code changed "
                     f"without a HASH_VERSION bump")
    return out, drift


def quote_problems(rec: Dict[str, Any]) -> List[str]:
    """Every quoted span in every reasoning must occur in the record's own packet (as §5)."""
    shown: List[str] = []
    _flatten_shown(rec["packet"], shown)
    corpus = " \n ".join(" ".join(s.split()).lower() for s in shown)
    v = rec.get("_verdict") if isinstance(rec.get("_verdict"), dict) else {}
    texts = [("overall reasoning", v.get("reasoning") or "")]
    for cid, c in sorted((v.get("clauses") or {}).items()):
        if isinstance(c, dict):
            texts.append((f"clause {cid!r} reasoning", c.get("reasoning") or ""))
    out = []
    for where, text in texts:
        for _q, span in _QUOTE_RE.findall(str(text)):
            probe = " ".join(span.split()).lower().strip().rstrip(".")
            if len(probe) >= _MIN_QUOTE_LEN and probe not in corpus:
                out.append(f"{where} quotes {span!r}, which its own packet does not contain")
    return out


def load_records(review_dir: Path) -> List[Tuple[Path, Dict[str, Any]]]:
    """Every record under `review_dir`, sorted by path. A file that is not JSON is returned as None."""
    out = []
    if not review_dir.is_dir():
        return out
    for path in sorted(review_dir.rglob("*.json")):
        try:
            out.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except json.JSONDecodeError as exc:
            out.append((path, {"__unparseable__": f"{exc}"}))
    return out


def _family_diff(old: Dict[str, Any], new: Dict[str, Any]) -> str:
    """What moved between a reviewed packet and the live one, for a stale finding."""
    a = {f["template"]: SP.digest({k: v for k, v in f.items() if k != "id"}) for f in old.get("families", [])}
    b = {f["template"]: SP.digest({k: v for k, v in f.items() if k != "id"}) for f in new.get("families", [])}
    parts = []
    added, gone = sorted(set(b) - set(a)), sorted(set(a) - set(b))
    changed = sorted(t for t in set(a) & set(b) if a[t] != b[t])
    if added:
        parts.append(f"new template(s) {added[:3]!r}")
    if gone:
        parts.append(f"template(s) no longer reached {gone[:3]!r}")
    if changed:
        parts.append(f"domain/provenance changed in {changed[:3]!r}")
    other = [k for k in sorted(set(old) | set(new)) if k not in ("item", "families") and old.get(k) != new.get(k)]
    if other:
        parts.append(f"changed section(s) {other}")
    return "; ".join(parts) or "the hash moved"


def collect_findings(node_ids: Optional[List[str]] = None,
                     review_dir: Path = REVIEW_DIR) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    """({label: [finding, ...]}, stats). One finding per (lc, label, record or cause)."""
    from backend.app.practice_gen.registry import get_all_node_ids

    review_dir = Path(review_dir)
    fixture_dir = review_dir.resolve() != REVIEW_DIR.resolve()
    out: Dict[str, List[str]] = {label: [] for label in ASSERTIONS}
    rel = lambda p: str(p.relative_to(_REPO_ROOT)) if p.is_relative_to(_REPO_ROOT) else str(p)  # noqa: E731

    # ---- every record, on its own bytes ----------------------------------------------------
    valid: Dict[str, List[Tuple[Path, Dict[str, Any]]]] = defaultdict(list)
    identities: Dict[str, set] = defaultdict(set)
    skeletons: Dict[str, set] = defaultdict(set)
    known = set(get_all_node_ids())
    for path, rec in load_records(review_dir):
        if "__unparseable__" in rec:
            out["stem_review_record_invalid_17"].append(f"{rel(path)}: not JSON ({rec['__unparseable__']}). "
                                                         f"Owed: re-dispatch and file through tests/stem_file.py.")
            continue
        node_id = rec.get("node_id")
        bad, drift = record_problems(rec, fixture_dir)
        if node_id not in known:
            bad.append(f"node_id {node_id!r} is not a registered lc")
        if path.parent.name != node_id:
            bad.append(f"filed under {path.parent.name!r}, not under its node_id's directory")
        for d in drift:
            out["stem_review_hash_drift_17"].append(f"{node_id}: {rel(path)}: {d}. Owed: restore the hash "
                                                     f"code, or bump stem_packets.HASH_VERSION on purpose.")
        for b in bad:
            out["stem_review_record_invalid_17"].append(f"{node_id}: {rel(path)}: {b}. Owed: re-dispatch the lc "
                                                         f"blind and file through tests/stem_file.py (records are never edited).")
        quotes = [] if bad else quote_problems(rec)
        for q in quotes:
            out["stem_review_quote_provenance_17"].append(f"{node_id}: {rel(path)}: {q}. Owed: set the reply "
                                                           f"aside and re-dispatch the lc blind.")
        if bad or drift or quotes:
            continue
        valid[node_id].append((path, rec))
        identities[str(rec["judged_by"])].add(node_id)
        skeletons[_rationale_skeleton(rec["_verdict"]["reasoning"])].add(node_id)

    # ---- across records ----------------------------------------------------------------------
    reused = {who for who, lcs in identities.items() if len(lcs) > 1}
    for who in sorted(reused):
        out["stem_review_identity_reused_17"].append(
            f"judged_by {who!r} is on records of {len(identities[who])} lcs {sorted(identities[who])[:5]}: one "
            f"dispatch judges one lc in one role (ruling 44). Owed: re-dispatch each lc under its own identity.")
    templated = {sk for sk, lcs in skeletons.items() if len(lcs) > _MAX_SKELETON_CLUSTER}
    for sk in sorted(templated):
        out["stem_review_skeleton_17"].append(
            f"{len(skeletons[sk])} lcs share one overall-reasoning frame (max {_MAX_SKELETON_CLUSTER}; lc ids, "
            f"quotes and digits stripped): {sk[:140]!r}. lcs {sorted(skeletons[sk])[:5]}. Owed: re-dispatch blind.")
    for node_id in list(valid):
        valid[node_id] = [(p, r) for p, r in valid[node_id]
                          if str(r["judged_by"]) not in reused
                          and _rationale_skeleton(r["_verdict"]["reasoning"]) not in templated]

    # ---- per lc in scope ---------------------------------------------------------------------
    scope = list(node_ids) if node_ids else sorted(known)
    stats = {"lcs": len(scope), "families": 0, "refused_paths": 0, "approved": 0}
    for node_id in scope:
        renders, refused = SP.observe_lc(node_id)
        item, key = SP.build_item(node_id, renders)
        stats["families"] += len(item["families"])
        stats["refused_paths"] += len(refused)
        for seed, formatter, text in SP.coverage_gaps(item, key, renders):
            from backend.app.practice_gen.validation.validate_slots import path_call
            out["stem_family_unpacketed_17"].append(
                f"{node_id}: the learner-read text {text[:80]!r} at seed {seed}"
                f"{'' if formatter is None else f' formatter {formatter!r}'} is produced by a family the stem "
                f"packet does not contain. Reproduce: {path_call(node_id, seed, formatter)}. Owed: fix "
                f"stem_packets.build_item so every reaching family is packeted.")
        live = SP.item_hash(item)
        recs = sorted(valid.get(node_id, []), key=lambda pr: (str(pr[1]["filed_at"]), pr[1]["record_id"]))
        if not recs:
            out["stem_review_missing_17"].append(
                f"{node_id}: no valid stem review is filed ({len(item['families'])} families, "
                f"{len(item['clauses'])} clauses). Owed: dispatch a first and a confirming blind judge "
                f"(owner rulings 24, 44) and file both through tests/stem_file.py.")
            continue
        path, last = recs[-1]
        if last["hash_version"] != SP.HASH_VERSION or last["lc_hash"] != live:
            why = (f"filed under HASH_VERSION {last['hash_version']}, now {SP.HASH_VERSION}"
                   if last["hash_version"] != SP.HASH_VERSION else _family_diff(last["packet"], item))
            out["stem_review_stale_17"].append(
                f"{node_id}: the standing review {rel(path)} judged hash {str(last['lc_hash'])[:12]}, the live "
                f"stems hash to {live[:12]}: {why}. Owed: re-dispatch the lc blind (first and confirming).")
            continue
        firsts = {r["record_id"]: r for _p, r in recs if r["role"] == "first"}
        first = firsts.get(last["confirms"]) if last["role"] == "confirming" else None
        if last["role"] != "confirming":
            why = "the latest record is a first judge's; no confirming judge has filed after it"
        elif first is None:
            why = f"it confirms {last['confirms']!r}, which is not a valid first record for this lc"
        elif first["lc_hash"] != last["lc_hash"]:
            why = "the first record it confirms judged a different hash"
        elif first["judged_by"] == last["judged_by"] or first["dispatch_id"] == last["dispatch_id"]:
            why = "the confirming judge shares the first judge's identity or dispatch"
        else:
            why = None
        if why:
            out["stem_review_unconfirmed_17"].append(
                f"{node_id}: {rel(path)}: {why} (ruling 20 as ruling 44e applies it: every lc). Owed: "
                f"dispatch one independent blind confirming judge on the same packet.")
            continue
        verdict = last["_verdict"]
        if verdict["overall"] == "FAIL":
            # Named by the family ids the judge gave (ruling 46b), never by looking a template up:
            # a template printed by two families would name one of them arbitrarily.
            template_of = {f["id"]: f["template"] for f in item["families"]}
            named = []
            for fid in verdict["failing_families"]:
                k = key["families"].get(fid, {})
                p = k.get("path")
                named.append(f"{fid} {template_of.get(fid)!r} (reached at seed {p[0]}"
                             f"{'' if p[1] is None else f' formatter {p[1]!r}'}, {k.get('first_site')})" if p
                             else f"{fid} {template_of.get(fid)!r}")
            out["stem_review_fail_17"].append(
                f"{node_id}: the confirmed stem review {rel(path)} is FAIL ({last['judged_by']}): "
                f"{verdict['reasoning'][:300]!r}. Failing: {'; '.join(named)}. Owed: fix the stem or its "
                f"domain in the generator, then re-review.")
        for cid, c in sorted(verdict["clauses"].items()):
            if c["verdict"] == "NOT_PRODUCIBLE":
                clause = next((x["clause"] for x in item["clauses"] if x["id"] == cid), cid)
                out["stem_clause_unproducible_17"].append(
                    f"{node_id}: clause {cid!r} ({clause!r}) is ruled NOT_PRODUCIBLE by the confirmed review "
                    f"{rel(path)}: {c['reasoning'][:240]!r}. Witness: ruled substitute (ruling 52): a "
                    f"NOT_PRODUCIBLE clause has no render. Owed: build what the clause names "
                    f"(Content Rule 4), then re-review.")
        if verdict["overall"] == "PASS" and all(c["verdict"] == "PRODUCIBLE" for c in verdict["clauses"].values()):
            stats["approved"] += 1
    return out, stats


def validate_all(node_ids: Optional[List[str]] = None, review_dir: Path = REVIEW_DIR) -> bool:
    findings, stats = collect_findings(node_ids, review_dir)
    total = 0
    for label in ASSERTIONS:
        items = findings[label]
        total += len(items)
        if items:
            print(f"  FAIL {label} ({len(items)}):")
            for item in items:  # every finding, by name (ruling 23)
                print(f"    - {item}")
        else:
            print(f"  PASS {label}")
    print(f"  NOTE: {stats['approved']} of {stats['lcs']} lc(s) carry a confirmed, fresh PASS with every clause "
          f"PRODUCIBLE; {stats['families']} stem families packeted; {stats['refused_paths']} pinned path(s) "
          f"refused (named by §14 as slot_path_refused_14)")
    print(f"  §17: {total} finding(s) over {stats['lcs']} lc(s); records read from {review_dir}")
    return total == 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§17 every lc's stems carry a fresh, valid, confirmed blind approval")
    ap.add_argument("--node-ids", help="comma-separated lc subset (proof mode)")
    ap.add_argument("--review-dir", default=str(REVIEW_DIR), help="records directory (proof mode: a fixture dir)")
    args = ap.parse_args()
    return 0 if validate_all(args.node_ids.split(",") if args.node_ids else None, Path(args.review_dir)) else 1


if __name__ == "__main__":
    sys.exit(main())
