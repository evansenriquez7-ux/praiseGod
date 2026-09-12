"""
Phase 2 hardening — step 0 migration inventory (permanent audit tooling).

`docs/phase2_hardening_completion_plan.md` step 0 asks for two machine-readable
inventories before any of the consolidation work touches a validator:

  1. **The requirement inventory.** One row for every `(node_id, requirement_id)` the
     pipeline actually validates today, joined to every piece of review evidence on
     record for it, with an explicit state. Plus the pairs that exist only in the
     historical corpus and are no longer required, accounted for separately rather than
     dropped.

  2. **The assertion/mutation migration table.** One row per harness assertion label and
     one per registered mutation, saying where each is emitted from today, what proves
     it, and whether that proof is a declaration or an execution.

Both are written to `validation_reports/phase2_hardening/`. Neither changes a validator,
a threshold, or a contract; this module is read-only with respect to the pipeline and is
safe to run at any point in the milestone.

WHY IT IS PERMANENT AND NOT A SCRATCH SCRIPT
--------------------------------------------
The plan requires the migration to reconcile at the END of M1 as well as at the start:
"unexpected removals fail reconciliation". A one-off script in `local_only/` cannot be
re-run against the tree it is supposed to police, so the inventory it produced would be
a snapshot nobody could reproduce. This lives in `tests/` for the same reason
`mutation_harness.py` does.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
* The evidence join is **per (node, capability)** for attestation and **per node** for
  judgment, because that is the granularity the two corpora were filed at. The plan's
  merged record is per (node, requirement) clause; until step 1 lands there is no
  clause-level judgment evidence to join, so `judgment` here is node-scoped context and
  this module says so in every row rather than implying clause coverage it cannot see.
* `state` is computed from the CURRENT declarations and the CURRENT corpora. It is a
  description of debt, never a verdict: no state produced here may be read as a review
  having passed. `current_evidence` means only "a winning PROVIDED verdict exists whose
  freshness the §6F sweep did not fault on this run".
* Freshness is taken from the live §6F/§5 findings rather than recomputed here. Two
  copies of a rule disagree eventually; this one observes the validators instead.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "validation_reports" / "phase2_hardening"

from backend.app.practice_gen.validation import validate_capability as cap  # noqa: E402
from backend.app.practice_gen.validation import validate_coverage as cov  # noqa: E402
from backend.app.practice_gen.validation import validate_judgment as jud  # noqa: E402

# A §6 finding names its node first, then quotes the capability id. Both phases use the
# same shape, which is what lets a finding be attributed back to an inventory row.
_FINDING_NODE_CAP = re.compile(r"^(?P<node>mat_g\d+_[a-z]+_q\d+_\d+): capability '(?P<cap>[^']+)'")
_FINDING_NODE = re.compile(r"^(?P<node>mat_g\d+_[a-z]+_q\d+_\d+)\b")


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _checkout_state() -> Dict[str, Any]:
    """The exact tree the inventory describes, including uncommitted work."""
    def git(*args: str, strip: bool = True) -> str:
        out = subprocess.run(["git", *args], cwd=REPO_ROOT, check=True,
                             capture_output=True, text=True).stdout
        # `--porcelain` lines are `XY<space>PATH`, and X is a SPACE for an unstaged
        # change. A blanket .strip() therefore ate the leading space of the FIRST line
        # only, so the fixed [3:] offset below cut one character off that one path and
        # left every other path correct -- `validation_reports/x` came back as
        # `alidation_reports/x`. Observed 2026-09-12 in a regenerated inventory. Strip
        # trailing newlines only when the caller is parsing columns.
        return out.strip() if strip else out.rstrip("\n")

    dirty = git("status", "--porcelain", strip=False)
    return {
        "head": git("rev-parse", "HEAD"),
        "head_short": git("rev-parse", "--short", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "working_tree_clean": dirty == "",
        # Rename entries read `R  old -> new`; the arrow form is preserved verbatim
        # rather than guessed at, because this field is provenance, not a path list.
        "dirty_paths": [line[3:] for line in dirty.splitlines()],
        "python": sys.version.split()[0],
        "generated_at": _now(),
    }


# ─── 1. Requirement inventory ─────────────────────────────────────────────────


def _attestation_provenance() -> Tuple[Dict[Tuple[str, str], Dict[str, Any]],
                                       Dict[Tuple[str, str], List[Dict[str, Any]]]]:
    """
    (winning verdict per pair, every verdict per pair) with its source file attached.

    Replays `validate_capability`'s own resolution rule -- last file wins over a sorted
    glob, per `_winning_verdict_index` -- rather than re-deriving one, so the inventory
    and the gate can never disagree about which record is authoritative.
    """
    records: List[Tuple[str, Dict[str, Any]]] = []
    if cap._ATTESTATION_DIR.exists():
        for path in sorted(cap._ATTESTATION_DIR.glob("*.json")):
            records.append((path.name, json.loads(path.read_text(encoding="utf-8"))))

    all_verdicts: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    winning: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for filename, rec in records:
        for v in rec.get("verdicts", []):
            key = (v.get("node_id"), v.get("capability_id"))
            entry = {
                "source_file": filename,
                "batch": rec.get("batch"),
                "attested_at": rec.get("attested_at"),
                "attester": rec.get("attested_by") or rec.get("attester"),
                "verdict": v.get("verdict"),
                "clause": v.get("clause"),
                "confidence": v.get("confidence"),
                "seeds_showing_it": v.get("seeds_showing_it"),
                "reasoning": v.get("reasoning"),
                "action_taken": v.get("action_taken"),
                "packet_seeds": (rec.get("packet") or {}).get("seeds"),
            }
            all_verdicts[key].append(entry)
            winning[key] = entry          # last file wins, exactly as the gate resolves
    return winning, dict(all_verdicts)


def _judgment_context() -> Dict[str, Dict[str, Any]]:
    """Node-scoped judgment review context. NOT clause evidence -- see module docstring."""
    out: Dict[str, Dict[str, Any]] = {}
    if not jud.JUDGMENT_DIR.exists():
        return out
    for path in sorted(jud.JUDGMENT_DIR.glob("*/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        node = data.get("node_id")
        if not node:
            continue
        out[node] = {
            "source_file": str(path.relative_to(REPO_ROOT)),
            "reviewed_by": data.get("reviewed_by"),
            "review_date": data.get("review_date"),
            "overall": data.get("overall"),
            "facets": {k: (v or {}).get("verdict") for k, v in (data.get("findings") or {}).items()},
            "sample_seeds": data.get("sample_seeds"),
            "n_samples": len(data.get("samples_reviewed") or []),
        }
    return out


def _findings_by_pair(findings: List[str]) -> Tuple[Dict[Tuple[str, str], List[str]],
                                                    Dict[str, List[str]],
                                                    List[str]]:
    """Split a §6 finding list into per-(node,cap), per-node, and tree-wide buckets."""
    per_pair: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    per_node: Dict[str, List[str]] = defaultdict(list)
    tree_wide: List[str] = []
    for f in findings:
        m = _FINDING_NODE_CAP.match(f)
        if m:
            per_pair[(m.group("node"), m.group("cap"))].append(f)
            continue
        m = _FINDING_NODE.match(f)
        if m:
            per_node[m.group("node")].append(f)
            continue
        tree_wide.append(f)
    return dict(per_pair), dict(per_node), tree_wide


# A §6F freshness finding is filed against the BATCH, not the pair: "Every verdict in
# this batch is about content that no longer exists". So the batch name in the message is
# what attributes those 150 node-scoped findings down to the pairs they invalidate --
# without it, every stale pair reads as `current_evidence`, which is the exact shape of
# error this inventory exists to prevent.
_STALE_BATCH = re.compile(r"attestation batch '(?P<batch>[^']+)' is STALE")


def _stale_batches(findings: List[str]) -> Set[str]:
    return {m.group("batch") for f in findings for m in [_STALE_BATCH.search(f)] if m}


def _state_for(pair_findings: List[str], winner: Dict[str, Any] | None,
               evidence_stale: bool) -> str:
    """
    The row's debt state. Describes evidence, never substitutes for it.

      unresolved_content  -- a blind verdict says the pipeline does not do this
      missing_review      -- nobody blind has judged this pair
      stale_evidence      -- a verdict exists but the content it judged has moved, so the
                            ruling is unadjudicable either way
      current_evidence    -- a winning PROVIDED verdict the freshness sweep did not fault

    `unresolved_content` outranks `stale_evidence` because that is what §6F enforces: a
    CONTRADICTED entry blocks whether or not its batch has since drifted, and softening it
    to "unadjudicable" would let a generator edit retire an inconvenient ruling. The
    staleness is still recorded on the row as `evidence_stale`.
    """
    blob = " ".join(pair_findings)
    if "CONTRADICTED" in blob:
        return "unresolved_content"
    if "UNATTESTED" in blob or winner is None:
        return "missing_review"
    if winner.get("verdict") == "NOT_PROVIDED":
        # No CONTRADICTED finding means the capability has no provider entry: the gap is
        # honestly reported elsewhere, but the requirement is still unmet content.
        return "unresolved_content"
    if evidence_stale or pair_findings:   # batch drift, or any other §6F/§6G pair finding
        return "stale_evidence"
    return "current_evidence"


def build_requirement_inventory() -> Dict[str, Any]:
    rows_src, guard_errors = cap._declared_nodes(None)
    winning, all_verdicts = _attestation_provenance()
    judgment = _judgment_context()

    phase2 = cap.validate_capability_attestation(None)
    per_pair, per_node, tree_wide = _findings_by_pair(phase2)
    stale_batches = _stale_batches(phase2)

    rows: List[Dict[str, Any]] = []
    required_pairs: Set[Tuple[str, str]] = set()
    for node_id, competency, requires, ignore in rows_src:
        for req in requires:
            cap_id = str(req.get("id", ""))
            key = (node_id, cap_id)
            required_pairs.add(key)
            winner = winning.get(key)
            pf = per_pair.get(key, [])
            evidence_stale = bool(winner and winner.get("batch") in stale_batches)
            rows.append({
                "node_id": node_id,
                "requirement_id": cap_id,
                "clause": req.get("clause"),
                "competency": competency,
                "state": _state_for(pf, winner, evidence_stale),
                "evidence_stale": evidence_stale,
                "has_provider_entry": cap_id in cap.CAPABILITY_PROVIDERS,
                "provider": cap.CAPABILITY_PROVIDERS.get(cap_id),
                "winning_attestation": winner,
                "attestation_history_count": len(all_verdicts.get(key, [])),
                "findings": pf,
                "judgment_context": judgment.get(node_id),
            })

    historical = []
    for key, entries in sorted(all_verdicts.items()):
        if key in required_pairs:
            continue
        historical.append({
            "node_id": key[0],
            "requirement_id": key[1],
            "state": "historical_only",
            "ruling": entries[-1].get("verdict"),
            "records": entries,
            "note": "no longer a declared requirement; retained as historical evidence",
        })

    return {
        "schema_version": 1,
        "checkout": _checkout_state(),
        "summary": {
            "declared_nodes": len(rows_src),
            "declaration_guard_errors": len(guard_errors),
            "required_pairs": len(rows),
            "loaded_attestation_pairs": len(all_verdicts),
            "historical_pairs_not_required": len(historical),
            "phase2_findings": len(phase2),
            "findings_attributed_to_pairs": sum(len(v) for v in per_pair.values()),
            "findings_attributed_to_nodes_only": sum(len(v) for v in per_node.values()),
            "findings_tree_wide": len(tree_wide),
            "stale_attestation_batches": len(stale_batches),
            "pairs_on_a_stale_batch": sum(1 for r in rows if r["evidence_stale"]),
            "states": dict(Counter(r["state"] for r in rows)),
            "judgment_reviews_on_disk": len(judgment),
        },
        "guard_errors": guard_errors,
        "tree_wide_findings": tree_wide,
        "node_scoped_findings": per_node,
        "rows": rows,
        "historical_only": historical,
    }


# ─── 2. Assertion / mutation migration table ──────────────────────────────────


def build_assertion_table() -> Dict[str, Any]:
    from tests.mutation_harness import MUTATIONS

    inventory = cov.harness_assertion_labels()
    declared = cov.declared_assertion_labels()
    matrix = cov.matrix_assertion_labels()
    printed, _printed_errs = cov.printed_check_labels()

    emitted_by: Dict[str, str] = {}
    for module, labels in declared.items():
        for label in labels:
            emitted_by[label] = module
    for label in matrix:
        emitted_by.setdefault(label, cov._MATRIX_MODULE)

    proving: Dict[str, List[str]] = defaultdict(list)
    for m in MUTATIONS:
        for label in (m.asserts or ()):
            proving[label].append(m.name)

    assertion_rows = []
    for label in sorted(inventory):
        muts = proving.get(label, [])
        assertion_rows.append({
            "assertion": label,
            "declared_in": emitted_by.get(label, "<discovered>"),
            "printed_by": printed.get(label, []),
            "discovered_in_matrix": label in matrix,
            "proving_mutations": muts,
            # §8 proves by DECLARATION; whether the mutation was ever DETECTED is the
            # hole step 4 closes. Stated per row so the table cannot be read as proof.
            "proof_kind": "declared" if muts else ("allowlisted" if label in cov.UNPROVEN_ASSERTIONS else "none"),
            "allowlist_reason": cov.UNPROVEN_ASSERTIONS.get(label),
        })

    mutation_rows = []
    for m in MUTATIONS:
        mutation_rows.append({
            "mutation": m.name,
            "asserts": list(m.asserts or ()),
            "expected_check": m.expected_check,
            "command": m.command,
            "expect_output_contains": list(m.expect_output_contains or ()),
            "baseline_must_not_contain": list(m.baseline_must_not_contain or ()),
            "edit_paths": sorted(m.edits.keys()),
            "uses_apply_fn": m.apply_fn is not None,
            # A mutation whose command is the whole runner exercises the assertion
            # through a wrapper rather than its own entry point (plan step 4).
            "runs_run_all": any("run_all" in part for part in m.command),
            "reads_review_corpus": any(
                str(p).startswith("validation_reports/") for p in m.edits
            ) or m.apply_fn is not None,
        })

    orphan_asserts = sorted(set(proving) - inventory)
    return {
        "schema_version": 1,
        "checkout": _checkout_state(),
        "summary": {
            "assertions_inventoried": len(inventory),
            "assertions_with_a_mutation": sum(1 for r in assertion_rows if r["proving_mutations"]),
            "assertions_allowlisted_unproven": sum(1 for r in assertion_rows if r["proof_kind"] == "allowlisted"),
            "assertions_unaccounted": sum(1 for r in assertion_rows if r["proof_kind"] == "none"),
            "mutations_registered": len(MUTATIONS),
            "mutations_via_run_all_wrapper": sum(1 for r in mutation_rows if r["runs_run_all"]),
            "mutations_touching_review_corpus": sum(1 for r in mutation_rows if r["reads_review_corpus"]),
            "mutation_asserts_outside_inventory": orphan_asserts,
        },
        "assertions": assertion_rows,
        "mutations": mutation_rows,
    }


def _write(name: str, payload: Dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Phase 2 hardening step-0 migration inventory")
    ap.add_argument("--only", choices=("requirements", "assertions"), default=None)
    args = ap.parse_args()

    if args.only in (None, "assertions"):
        table = build_assertion_table()
        path = _write("assertion_migration.json", table)
        print(f"assertion table -> {path.relative_to(REPO_ROOT)}")
        for k, v in table["summary"].items():
            print(f"  {k}: {v}")

    if args.only in (None, "requirements"):
        inv = build_requirement_inventory()
        path = _write("requirement_inventory.json", inv)
        print(f"requirement inventory -> {path.relative_to(REPO_ROOT)}")
        for k, v in inv["summary"].items():
            print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
