"""
Practice Generation — Carried Defects of the Retired Per-Sample Gates (H6; owner rulings 25, 55)

Ruling 25 retires `judgment_reviews_5` (§5) and the `capability_phase2` attestation queue
(§6F-§6H) as gates, now that the stem review gate (§17) and the field-domain checks (§14)
are each proven by mutation. Their filed records stay as read-only history, and the defects
those records confirmed are carried into the generator work queue. Ruling 55 fixes how:

  * ONE read-only CONTENT stage reports each defect from the frozen records;
  * a per-sample defect is named by lc + seed + facet + owed build;
  * an lc-wide defect (a facet, clause, decomposition or overall verdict) and each of the
    CONTRADICTED capabilities is named by lc + clause/capability + owed build, plus a
    witness seed where the record cites one in a structured field (ruling 52's substitute
    where it cites none);
  * a defect CLEARS when its reviewed render no longer replays to what was reviewed (the
    generator changed it). The lc then owes a §17 re-judgment, reported here until a §17
    record filed after the retirement stands for that lc;
  * records are never edited.

What is checked, by label:

  carried_records_frozen         INTEGRITY. Every file under validation_reports/judgment/,
                                 judgment_audit/ and attestation/ hashes to FROZEN_RECORDS.
                                 An edited, added or deleted record changes what this stage
                                 carries without any generator change, which is the history
                                 ruling 25 freezes.
  carried_judgment_defect_5      CONTENT. A non-PASS verdict in a §5 record whose every
                                 reviewed sample still replays (`validate_judgment.
                                 _validate_freshness` returns nothing).
  carried_capability_defect_6F   CONTENT. A NOT_PROVIDED verdict, standing by last-file-wins
                                 (`validate_capability._load_attestations`), on a capability
                                 the lc still requires and CAPABILITY_PROVIDERS still claims,
                                 in a batch whose judged samples still replay.
  carried_defect_rejudge_owed    CONTENT. A record above no longer replays, so its defects
                                 cleared; the lc's standing §17 record was filed before the
                                 retirement (RETIRED_AT), so nothing has judged the changed
                                 content yet.

The verdict and freshness rules are NOT re-derived here (memory "duplicated rule copies
disagree"): freshness is `validate_judgment._validate_freshness` and `validate_capability.
_attestation_staleness` on one record at a time; the standing attestation verdict is
`validate_capability._load_attestations`; the CONTRADICTED condition is the one
`validate_capability._validate_attestation` applies. The §5 verdict fields are read
structurally from the record, in the order `validate_judgment._validate_one` reads them;
`tests/unit/test_validate_carried.py` holds the two counts equal on the live corpus.

NAMED LIMITS (Scaling Mandate 6; also in the contract's §5/§6F rows):
  1. **Freshness is per record, not per sample.** One sample that no longer replays clears
     every defect in that record (its lc-wide verdicts were reached over all its samples),
     and the lc owes a §17 re-judgment instead.
  2. **A cleared defect is re-judged only to §17's depth.** §17 judges stems and domains,
     not rendered samples (ruling 55), so a sample-level defect class §17 does not judge
     (for example ambiguity, ruling 56) is not re-checked once its sample changes.
  3. **"Re-judged" means a later §17 record stands, not that it judged this defect.** A
     §17 record filed after RETIRED_AT clears `carried_defect_rejudge_owed` for its lc
     whatever it says.
  4. **No new review or attestation is owed.** An lc or capability with no record, or a new
     capability declared after retirement, is not reported here: §17's clause ruling
     (Rule 2) is the live check for what a clause can produce.
  5. **The freshness rules carry their own limits** (`validate_judgment._validate_freshness`
     and `validate_capability._attestation_staleness` docstrings): layout, hints and cloze
     templates are outside the comparison.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ASSERTIONS = (
    "carried_records_frozen",         # a retired gate's record was edited, added or deleted (integrity)
    "carried_judgment_defect_5",      # a non-PASS §5 verdict on a record that still replays
    "carried_capability_defect_6F",   # a standing NOT_PROVIDED the provider table still claims
    "carried_defect_rejudge_owed",    # a record no longer replays and no later §17 record stands
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
FROZEN_DIRS = ("validation_reports/judgment", "validation_reports/judgment_audit",
               "validation_reports/attestation")

# The retired records, frozen at retirement (2026-10-17, H6): file count and the sha256 of
# the sorted "relative path, sha256 of bytes" lines (`records_digest`). Changing this pin is
# changing history; ruling 25 forbids it.
FROZEN_RECORDS = {"files": 1708,
                  "sha256": "59589a0f647c11feeb01ad18485099b83eaa7bbdc8f528f0033e0b4a0620157e"}

# §17 records filed at or before this instant judged the content these records judged
# (H4-C's last filing was 2026-10-16T10:42:00Z). A later one is a re-judgment.
RETIRED_AT = "2026-10-17T00:00:00Z"

_OWED_REJUDGE = ("Owed: re-dispatch the lc's §17 stem judges (first and confirming) on a fresh packet "
                 "and file through tests/stem_file.py (owner ruling 55).")


def records_digest(root: Path = _REPO_ROOT, dirs: Tuple[str, ...] = FROZEN_DIRS) -> Dict[str, Any]:
    """{"files": n, "sha256": hex} over every file under `dirs`, by path relative to `root`."""
    lines = []
    for d in dirs:
        base = root / d
        if not base.is_dir():
            raise FileNotFoundError(f"carried_records_frozen: {base} is not a directory; the retired "
                                    f"records are history and may not be removed (ruling 25).")
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            rel = path.relative_to(root).as_posix()
            lines.append(f"{rel} {hashlib.sha256(path.read_bytes()).hexdigest()}")
    lines.sort()
    return {"files": len(lines), "sha256": hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()}


def frozen_findings(root: Path = _REPO_ROOT, pin: Optional[Dict[str, Any]] = None) -> List[str]:
    pin = FROZEN_RECORDS if pin is None else pin
    live = records_digest(root)
    if live == pin:
        return []
    return [f"the retired §5/§6F records hash to {live['files']} file(s) {live['sha256'][:16]}, not the "
            f"frozen {pin['files']} file(s) {str(pin['sha256'])[:16]}: a record under {', '.join(FROZEN_DIRS)} "
            f"was edited, added or deleted. Owed: restore it from git (records are never edited; ruling 25)."]


def _sample_where(sample: Optional[Dict[str, Any]]) -> str:
    if not sample:
        return "a sample the record does not carry"
    eff = sample.get("effective") or {}
    return (f"seed {sample.get('seed')} (formatter {eff.get('format') or sample.get('formatter')!r}, "
            f"{sample.get('serving_mode')})")


def judgment_defects(node_id: str, data: Dict[str, Any]) -> List[str]:
    """Every non-PASS verdict in one §5 record, in `_validate_one`'s order, each named."""
    from backend.app.practice_gen.validation.validate_judgment import REQUIRED_FINDINGS

    by_id = {str(s.get("sample_id")): s for s in data.get("samples_reviewed") or []}
    repro = f"Reproduce: judgment_packets._render_sample({node_id!r}, <seed>)"
    owed = ("Owed: fix the generator so this render passes (Content Rules 1-3); its §17 review then "
            "goes stale and is re-judged (ruling 55).")
    out: List[str] = []
    for a in data.get("sample_assessments") or []:
        sample = by_id.get(str(a.get("sample_id")))
        for name, block in (a.get("checks") or {}).items():
            if isinstance(block, dict) and block.get("verdict") != "PASS":
                out.append(f"{node_id}: {_sample_where(sample)} {name} is {block.get('verdict')} "
                           f"(sample {a.get('sample_id')}): {str(block.get('reasoning', ''))[:240]!r}. "
                           f"{repro.replace('<seed>', str((sample or {}).get('seed')))}. {owed}")
    for c in data.get("clause_evidence") or []:
        if isinstance(c, dict) and c.get("verdict") != "PASS":
            seeds = [by_id[s].get("seed") for s in c.get("sample_ids") or [] if s in by_id]
            witness = (f"cited samples at seeds {seeds}" if seeds else
                       "ruled substitute (ruling 52): the record cites no sample for this clause")
            out.append(f"{node_id}: clause {c.get('requirement_id')!r} ({c.get('clause')!r}) is "
                       f"{c.get('verdict')}; {witness}: {str(c.get('reasoning', ''))[:240]!r}. Owed: build "
                       f"what the clause names (Content Rule 4); §17 Rule 2 re-rules it (ruling 55).")
    findings = data.get("findings") or {}
    decomposition = (findings.get("competency_fulfillment") or {}).get("decomposition")
    if isinstance(decomposition, dict) and decomposition.get("verdict") != "PASS":
        out.append(f"{node_id}: competency_fulfillment.decomposition is {decomposition.get('verdict')}; "
                   f"ruled substitute (ruling 52): an lc-wide verdict on a retired record, no witness seed: "
                   f"{str(decomposition.get('reasoning', ''))[:240]!r}. Owed: make the lc's problems cover "
                   f"every clause of its competency (Content Rule 3).")
    for item in sorted(REQUIRED_FINDINGS & set(findings)):
        block = findings[item]
        if isinstance(block, dict) and str(block.get("verdict", "")).upper() != "PASS":
            out.append(f"{node_id}: findings[{item!r}] is {block.get('verdict')}; ruled substitute "
                       f"(ruling 52): an lc-wide verdict on a retired record, no witness seed: "
                       f"{str(block.get('rationale', ''))[:240]!r}. Owed: fix the generator so the lc "
                       f"meets {item} (docs/pgen_judgment.md).")
    if str(data.get("overall", "")).upper() != "PASS":
        out.append(f"{node_id}: overall judgment verdict is {data.get('overall')}; ruled substitute "
                   f"(ruling 52): an lc-wide verdict on a retired record, no witness seed. Owed: clear "
                   f"this lc's other carried defects above.")
    return out


def _standing_stem_filed_at(node_ids: List[str]) -> Dict[str, str]:
    """The latest §17 `filed_at` per lc, read from the records on disk."""
    from backend.app.practice_gen.validation import validate_stem_review as VSR

    latest: Dict[str, str] = {}
    for _path, rec in VSR.load_records(VSR.REVIEW_DIR):
        nid, at = rec.get("node_id"), str(rec.get("filed_at", ""))
        if nid in node_ids and at > latest.get(nid, ""):
            latest[nid] = at
    return latest


def collect_findings(node_ids: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """{label: [finding, ...]} over every lc in scope (all lcs when None)."""
    from backend.app.practice_gen.registry import get_all_node_ids
    from backend.app.practice_gen.validation import validate_capability as VC
    from backend.app.practice_gen.validation import validate_judgment as VJ

    scope = sorted(node_ids) if node_ids else sorted(get_all_node_ids())
    out: Dict[str, List[str]] = {label: [] for label in ASSERTIONS}
    out["carried_records_frozen"] = frozen_findings()
    stale: Dict[str, List[str]] = {}

    # ---- §5: one record per lc ---------------------------------------------------------------
    for nid in scope:
        path = VJ._node_file(nid)
        if not path.exists():
            continue  # limit 4: no review is owed after retirement
        data = json.loads(path.read_text(encoding="utf-8"))
        drift = VJ._validate_freshness(nid, data)
        if drift:
            stale.setdefault(nid, []).append(f"its §5 review {path.relative_to(_REPO_ROOT)} no longer "
                                             f"replays ({drift[0][:200]})")
            continue
        out["carried_judgment_defect_5"].extend(judgment_defects(nid, data))

    # ---- §6F: the standing verdict per (lc, capability) --------------------------------------
    attested = VC._load_attestations()
    records = VC._attestation_records()
    batch_of: Dict[tuple, Dict[str, Any]] = {}
    for rec in records:  # sorted by file name, as _load_attestations reads them: last wins
        for v in rec.get("verdicts", []):
            batch_of[(v.get("node_id"), v.get("capability_id"))] = rec
    rows, _guard = VC._declared_nodes(scope)
    stale_batch: Dict[str, List[str]] = {}
    for node_id, _competency, requires, _ignore in rows:
        for req in requires:
            cap = str(req.get("id", ""))
            verdict = attested.get((node_id, cap))
            if verdict is None or verdict.get("verdict") != "NOT_PROVIDED" or cap not in VC.CAPABILITY_PROVIDERS:
                continue
            rec = batch_of[(node_id, cap)]
            batch = str(rec.get("batch"))
            if batch not in stale_batch:
                stale_batch[batch] = VC._attestation_staleness([rec])
            if stale_batch[batch]:
                stale.setdefault(node_id, []).append(
                    f"attestation batch {batch!r} for capability {cap!r} no longer replays "
                    f"({stale_batch[batch][0][:200]})")
                continue
            seeds = [s.get("seed") for s in (rec.get("packet") or {}).get("samples_judged") or []]
            shown = verdict.get("seeds_showing_it") or []
            witness = (f"witness seeds {shown}" if shown else
                       f"ruled substitute (ruling 52): NOT_PROVIDED is an absence, no render shows it; "
                       f"judged seeds {seeds} (student path)")
            out["carried_capability_defect_6F"].append(
                f"{node_id}: capability {cap!r} (clause {req.get('clause')!r}) was ruled NOT_PROVIDED by the "
                f"standing attestation {batch!r} ({rec.get('attested_by')}) and CAPABILITY_PROVIDERS still "
                f"claims {VC.CAPABILITY_PROVIDERS[cap]}; {witness}. Attester's reasoning: "
                f"{str(verdict.get('reasoning'))[:200]!r}. Owed: build the artifact that renders what the "
                f"clause names (Content Rule 4) or delete the provider entry; never re-file the verdict.")

    # ---- cleared defects owe a §17 re-judgment -----------------------------------------------
    filed = _standing_stem_filed_at(sorted(stale))
    for nid in sorted(stale):
        at = filed.get(nid, "")
        if at and at > RETIRED_AT:
            continue  # limit 3: a §17 record filed after retirement stands
        out["carried_defect_rejudge_owed"].append(
            f"{nid}: {'; '.join(stale[nid])}, so its carried defects cleared; the lc's standing §17 record "
            f"was filed {at or 'never'}, not after the retirement ({RETIRED_AT}). {_OWED_REJUDGE}")
    return out


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    findings = collect_findings(node_ids)
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
    print(f"  carried (§5/§6F, rulings 25/55): {total} finding(s); records frozen at "
          f"{FROZEN_RECORDS['files']} file(s)")
    return total == 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="H6: defects carried from the retired §5/§6F records")
    ap.add_argument("--node-ids", help="comma-separated lc subset (proof mode)")
    ap.add_argument("--digest", action="store_true", help="print the live records digest and exit")
    args = ap.parse_args()
    if args.digest:
        print(json.dumps(records_digest()))
        return 0
    return 0 if validate_all(args.node_ids.split(",") if args.node_ids else None) else 1


if __name__ == "__main__":
    sys.exit(main())
