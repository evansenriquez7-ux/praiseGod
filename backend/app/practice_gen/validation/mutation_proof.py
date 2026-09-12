"""
Executed-mutation proof records — the schema, the fingerprint, and the verifier.

WHY THIS EXISTS
---------------
`validate_coverage` (§8) is the gate that measures whether the other gates are real, and
until this module it measured them by DECLARATION. `proven_assertions()` read
`Mutation.asserts` out of the table: a label counted as proven the moment somebody wrote
a mutation naming it, whether or not that mutation had ever been run, whether or not it
SURVIVED, and whether or not the runner had refused to score it as INVALID. §8's own
docstring named the hole on 2026-09-10 and could not close it, because a run of the
mutation table left nothing on disk that a validator could read.

This module is that artifact. `tests/mutation_harness.py` writes one proof record per
mutation it actually executed; §8 reads them and counts a label proven only when a record
exists that is complete, current, and reports a DETECTED result.

WHAT MAKES A PROOF CURRENT
--------------------------
Three digests, because a stale proof is worse than a missing one — it reports green about
code that has since moved:

  * `input_digest` — sha256 over a manifest of every file in the proof input set
    (`INPUT_ROOTS` below), taken from the WORKING TREE, not from git HEAD. Uncommitted and
    untracked files count: a mutation proved against an edit you have not committed was
    proved against the bytes that ran.
  * `definition_digest` — sha256 over the mutation's own definition, including the source
    of its `apply_fn` where it has one. Changing what a mutation plants, what it runs, or
    what markers it expects invalidates its proof rather than silently inheriting it.
  * `environment` — interpreter and dependency fingerprint, recorded for diagnosis. NOT
    enforced: a check that fails because the patch version of Python moved would be a
    false alarm, and the plan's requirement is that it be *recorded*.

WHAT IS IN THE INPUT SET, AND WHAT IS DELIBERATELY NOT
------------------------------------------------------
`INPUT_ROOTS` is the pipeline, the harness, its fixtures and the ground-truth data;
`INPUT_FILES` adds the two documents a validator actually opens. Together they are
everything a validator reads to reach a verdict. Exclusions are named one
by one (`EXCLUDED_PATHS`) rather than by broad prefix, because the plan's failure mode is
excluding `validation_reports/` wholesale and thereby omitting a fixture corpus a check
actually consumes. `tests/` is an input root precisely so that isolated review corpora
under it are fingerprinted like any other input.

`validation_reports/` is NOT an input root: it holds this module's own output, the
harness's report files, and — today — the two agent-authored corpora. The one file in it
that a validator READS is listed in `INPUT_FILES` by name. The corpora are the reason for
`mutated_paths` and `PHASE1_ADMISSIBLE_ROOTS` below.

THE PHASE BOUNDARY, AND THE ONE THING THIS MODULE REFUSES TO PRETEND
--------------------------------------------------------------------
A proof record is machine-generated, so it is a Phase 1 input (plan step 5). But a proof
is only as artifact-free as the thing it was proved against. 24 of the 76 mutations plant
into `validation_reports/judgment/` or `validation_reports/attestation/` — genuine
agent-authored review files — so their evidence is bound to a corpus Phase 1 may not read
and this module cannot fingerprint. Those proofs are recorded in full and marked
`phase1_admissible: false`, with every out-of-set path named. They are real evidence; they
are not evidence Phase 1 can stand on.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
* The input digest is whole-tree, not per-mutation. Any edit under an input root
  invalidates EVERY proof, which is the safe direction and an expensive one: re-proving
  the table costs a full run. A per-mutation dependency set would be cheaper and would be
  a model of what each validator reads — the kind of second copy that drifts. Named, not
  fixed.
* `environment` is recorded and not enforced (above).
* A proof states that the planted bug was detected by the named markers. It does not and
  cannot state that the check is CORRECT — only that it fires on this violation. Mandate
  2's second cause (a plant that no longer reaches the validated path) is caught by
  `baseline_exit`/`observed_markers`, not by this module.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

SCHEMA_VERSION = 1

_REPO_ROOT = Path(__file__).resolve().parents[4]
PROOF_DIR = _REPO_ROOT / "validation_reports" / "mutation_proofs"

# Everything a validator reads to reach a verdict. Fingerprinted from the working tree.
INPUT_ROOTS: Tuple[str, ...] = (
    "backend/app",
    "tests",
    "scripts",
    "data",
    "frontend/src",
)

# Individual files outside the roots above that a validator READS to reach a verdict.
# Named one by one rather than taking `docs/` wholesale: these two are the only documents
# any validator opens (`run_all._PGEN_CONTRACT_PATH` and its operator-doc floor), and
# fingerprinting the other fourteen would mean a prose edit costs a full re-run of the
# mutation table for no gain in safety. A document a FUTURE validator reads has to be
# added here -- which is the same rule as the roots, stated for a file instead of a tree.
INPUT_FILES: Tuple[str, ...] = (
    "docs/pgen_contract.md",
    "docs/testing_pipeline.md",
    # `validation_reports/` is mostly this harness's OUTPUT, which is why it is not a
    # root. This one file is an INPUT: §1H's coverage-regression check reads it as the
    # baseline it compares against, so a proof about §1H that did not cover it would be
    # bound to everything except the thing the check actually consults. The plan's named
    # failure mode is excluding `validation_reports/` wholesale and silently dropping a
    # fixture like this one; it is listed by name instead.
    #
    # Deliberately still OUTSIDE: matrix_report.json and matrix_node_reports/ (written by
    # the run), hardening_ledger.md (read by scripts/, not by any validator), and
    # judgment/ + attestation/ (agent-authored corpora Phase 1 may not read at all --
    # that exclusion is what `phase1_admissible` reports on rather than hides).
    "validation_reports/check_coverage_baseline.json",
)

# Named one by one. A broad prefix here is how a consumed fixture gets silently omitted.
EXCLUDED_DIR_NAMES: Set[str] = {"__pycache__", ".pytest_cache", "node_modules", ".git"}
EXCLUDED_SUFFIXES: Tuple[str, ...] = (".pyc", ".pyo", ".so")
EXCLUDED_PATHS: Set[str] = {
    # The mutation runner's own kill-safety marker: written and deleted by every run, so
    # digesting it would make the fingerprint depend on whether a run is in flight.
    "local_only/scratch/MUTATION_IN_FLIGHT.json",
}

# A proof is admissible in Phase 1 only if every path its mutation actually edited lies
# inside the fingerprinted input set. Anything else means the evidence is bound to bytes
# this module did not digest — today, the agent-authored review corpora.
PHASE1_ADMISSIBLE_ROOTS: Tuple[str, ...] = INPUT_ROOTS + INPUT_FILES


def _iter_input_files() -> Iterable[Path]:
    for rel in INPUT_FILES:
        path = _REPO_ROOT / rel
        if path.exists():
            yield path
    for root in INPUT_ROOTS:
        base = _REPO_ROOT / root
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIR_NAMES)
            for name in sorted(filenames):
                path = Path(dirpath) / name
                rel = path.relative_to(_REPO_ROOT).as_posix()
                if rel in EXCLUDED_PATHS or rel.endswith(EXCLUDED_SUFFIXES):
                    continue
                yield path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def input_manifest() -> Dict[str, str]:
    """{repo-relative path: sha256} over the whole proof input set, sorted."""
    return {
        p.relative_to(_REPO_ROOT).as_posix(): _sha256_file(p)
        for p in sorted(_iter_input_files())
    }


def input_digest(manifest: Dict[str, str] | None = None) -> str:
    """One digest over the input manifest. Recomputed on every read; never cached."""
    man = input_manifest() if manifest is None else manifest
    blob = "\n".join(f"{k} {v}" for k, v in sorted(man.items())).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def definition_digest(mutation: Any) -> str:
    """
    sha256 over what the mutation IS: what it plants, what it runs, what it expects.

    `apply_fn` mutations carry their planting logic in code rather than in `edits`, so the
    function's source is digested too. Without that, rewriting a plant to target a
    different file would inherit the old proof.
    """
    import inspect

    payload: Dict[str, Any] = {
        "name": mutation.name,
        "edits": {k: list(v) for k, v in sorted(mutation.edits.items())},
        "command": list(mutation.command),
        "expected_check": mutation.expected_check,
        "asserts": sorted(mutation.asserts or ()),
        "expect_output_contains": list(mutation.expect_output_contains or ()),
        "baseline_must_not_contain": list(mutation.baseline_must_not_contain or ()),
    }
    if mutation.apply_fn is not None:
        try:
            payload["apply_fn_source"] = inspect.getsource(mutation.apply_fn)
        except (OSError, TypeError) as exc:
            raise RuntimeError(
                f"mutation '{mutation.name}': apply_fn source is unreadable ({exc}), so its "
                f"proof cannot be bound to what it plants. A proof that cannot be invalidated "
                f"by a change to the plant is not a proof."
            ) from exc
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def environment_fingerprint() -> Dict[str, Any]:
    """Recorded for diagnosis, not enforced — see the module docstring."""
    req = _REPO_ROOT / "requirements.txt"
    return {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "system": platform.system(),
        "machine": platform.machine(),
        "requirements_sha256": _sha256_file(req) if req.exists() else None,
    }


def _rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return str(p)


def paths_outside_input_set(paths: Iterable[Path | str]) -> List[str]:
    """Which of these the fingerprint does not cover. Empty means Phase-1 admissible."""
    outside: List[str] = []
    for p in paths:
        rel = _rel(p)
        if rel in EXCLUDED_PATHS or not any(
            rel == root or rel.startswith(root + "/") for root in PHASE1_ADMISSIBLE_ROOTS
        ):
            outside.append(rel)
    return sorted(set(outside))


def proof_path(name: str) -> Path:
    return PROOF_DIR / f"{name}.json"


def write_proof(record: Dict[str, Any]) -> Path:
    """
    Publish one proof ATOMICALLY, and only after the caller has restored the tree.

    A half-written record read by §8 is a stale proof wearing a current one's name, so the
    write goes to a temp file in the same directory and is renamed into place.
    """
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    path = proof_path(record["mutation"])
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(record, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)
    return path


def load_proofs() -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """
    ({mutation name: record}, errors). A malformed record is an ERROR, never a skip.

    An interrupted write leaves a `.json.tmp` behind; it is reported rather than ignored,
    because "a proof run was killed partway" is exactly the state that must not read as
    "that mutation has no proof yet, carry on".
    """
    proofs: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    if not PROOF_DIR.exists():
        return proofs, errors
    for tmp in sorted(PROOF_DIR.glob("*.json.tmp")):
        errors.append(
            f"mutation proof: '{tmp.name}' is an unfinished write left by an interrupted "
            f"proof run. Re-run that mutation and delete the partial file; do not read "
            f"around it."
        )
    for path in sorted(PROOF_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"mutation proof: '{path.name}' is not valid JSON: {exc}.")
            continue
        if not isinstance(data, dict) or not isinstance(data.get("mutation"), str):
            errors.append(f"mutation proof: '{path.name}' has no 'mutation' name field.")
            continue
        if data["mutation"] != path.stem:
            errors.append(
                f"mutation proof: '{path.name}' names mutation {data['mutation']!r}; a proof "
                f"must be filed under the name of the mutation it proves."
            )
            continue
        proofs[data["mutation"]] = data
    return proofs, errors


# The fields a complete record must carry. Listed rather than inferred so a record written
# by an older runner is REJECTED as partial instead of half-read.
REQUIRED_FIELDS: Tuple[str, ...] = (
    "schema_version", "mutation", "definition_digest", "asserts", "command",
    "expect_output_contains", "baseline_must_not_contain", "baseline_exit",
    "planted_exit", "observed_markers", "diagnostic_line", "detected",
    "mutated_paths", "input_digest", "environment", "restored_clean",
    "started_at", "finished_at", "phase1_admissible", "paths_outside_input_set",
)


def verify_proof(record: Dict[str, Any], mutation: Any, current_input_digest: str,
                 require_phase1_admissible: bool = True) -> List[str]:
    """
    Every reason this record does not prove its mutation. Empty list means it does.

    Ground Rule 3 shape: each rejection names the mutation, what is wrong, and what to do.
    """
    name = record.get("mutation", "<unnamed>")
    errs: List[str] = []

    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        return [
            f"mutation proof '{name}': PARTIAL — missing field(s) {missing}. A record "
            f"written by an older runner cannot be half-read; re-run the mutation."
        ]

    if record["schema_version"] != SCHEMA_VERSION:
        return [
            f"mutation proof '{name}': schema_version {record['schema_version']!r}, this "
            f"harness supports {SCHEMA_VERSION}. Re-run the mutation."
        ]

    if record["detected"] is not True:
        errs.append(
            f"mutation proof '{name}': the recorded result is NOT DETECTED "
            f"({record.get('diagnostic_line')!r}). A mutation that survived, or that the "
            f"runner refused to score, proves nothing. Fix the check or the plant."
        )

    if record["planted_exit"] == 0:
        errs.append(
            f"mutation proof '{name}': SURVIVED — the validator exited 0 with the bug "
            f"planted. Either the check is broken or the plant no longer reaches the code "
            f"the check runs (Mandate 2). Diagnose which before re-filing."
        )

    if record["baseline_must_not_contain"] and record.get("baseline_exit") is None:
        errs.append(
            f"mutation proof '{name}': declares baseline markers but records no baseline "
            f"run. Without it the planted failure cannot be told from a pre-existing one."
        )

    observed = record["observed_markers"]
    if not isinstance(observed, dict):
        errs.append(f"mutation proof '{name}': 'observed_markers' must be an object.")
    else:
        unmet = sorted(m for m, seen in observed.items() if not seen)
        if unmet:
            errs.append(
                f"mutation proof '{name}': expected marker(s) {unmet} were NOT observed in "
                f"the mutated run's output. The validator failed for some other reason; an "
                f"unrelated crash is not proof the assertion works."
            )
        declared = set(record["expect_output_contains"])
        if declared - set(observed):
            errs.append(
                f"mutation proof '{name}': marker(s) {sorted(declared - set(observed))} are "
                f"declared by the mutation but carry no observation in the proof. Re-run it."
            )

    if record["restored_clean"] is not True:
        errs.append(
            f"mutation proof '{name}': the runner could not confirm it restored every "
            f"planted file. The tree this proof describes may still carry the bug."
        )

    if mutation is None:
        errs.append(
            f"mutation proof '{name}': no mutation of that name is registered any more. "
            f"Delete the orphaned proof, or restore the mutation it belongs to."
        )
        return errs

    current_def = definition_digest(mutation)
    if record["definition_digest"] != current_def:
        errs.append(
            f"mutation proof '{name}': STALE — the mutation's definition has changed since "
            f"this proof was written (recorded {record['definition_digest'][:12]}, now "
            f"{current_def[:12]}). What it plants, runs or expects is no longer what was "
            f"proved. Re-run it."
        )

    if sorted(record["asserts"]) != sorted(mutation.asserts or ()):
        errs.append(
            f"mutation proof '{name}': proves {sorted(record['asserts'])} but the mutation "
            f"now asserts {sorted(mutation.asserts or ())}. The label a proof carries must "
            f"be the label the table claims."
        )

    if record["input_digest"] != current_input_digest:
        errs.append(
            f"mutation proof '{name}': STALE — the source/fixture tree has changed since "
            f"this proof was written (recorded {record['input_digest'][:12]}, now "
            f"{current_input_digest[:12]}). The proof describes bytes that are no longer "
            f"what runs. Re-run the mutation table."
        )

    if require_phase1_admissible and record["phase1_admissible"] is not True:
        errs.append(
            f"mutation proof '{name}': NOT PHASE-1 ADMISSIBLE — the mutation edits "
            f"{record['paths_outside_input_set']}, which lie outside the fingerprinted "
            f"input set, so this evidence is bound to an agent-authored corpus Phase 1 may "
            f"not read. Migrate the mutation onto an isolated fixture corpus under tests/."
        )

    return errs


# The one rejection that is a statement about the TREE rather than about any individual
# proof. Told apart from the rest because 76 copies of it is one fact, and because a
# mutation run plants a source edit -- which moves the digest by construction, on every
# mutation in the table. If that produced a per-label error each time, §8 would emit ~140
# findings whenever any mutation is planted, the planted finding would be truncated out of
# the printed head, and the six mutations that prove §8's own directions would stop being
# able to discriminate. Same verdict, one line.
_TREE_MOVED = "the source/fixture tree has changed"


def evaluate(mutations: Iterable[Any],
             require_phase1_admissible: bool = True) -> Dict[str, Any]:
    """
    Everything §8 needs to say about the executed-proof corpus, in one pass.

      proven          -- labels a complete, current, DETECTED record establishes
      errors          -- one per proof that does not hold, with the tree-move collapse
      tree_moved      -- the input digest no longer matches what the proofs were taken on
      stale_tree_only -- labels whose ONLY problem is that tree move; §8 suppresses the
                         per-label error for these because `errors` already says it once
      records         -- the raw proof records that parsed

    A mutation with no proof record at all is NOT an error here — it is simply not proving
    anything, and §8's inventory pass reports the resulting hole. That split matters: "no
    proof yet" and "a proof that does not hold" have different fixes, and collapsing them
    produces one undifferentiated red wall.
    """
    by_name = {m.name: m for m in mutations}
    proofs, errors = load_proofs()
    digest = input_digest()

    proven: Set[str] = set()
    stale_tree_only: Set[str] = set()
    tree_moved_names: List[str] = []
    recorded_digests: Set[str] = set()

    for name, record in sorted(proofs.items()):
        errs = verify_proof(record, by_name.get(name), digest, require_phase1_admissible)
        if not errs:
            proven |= set(record["asserts"])
            continue
        other = [e for e in errs if _TREE_MOVED not in e]
        if not other:
            tree_moved_names.append(name)
            recorded_digests.add(str(record.get("input_digest", ""))[:12])
            stale_tree_only |= set(record.get("asserts") or ())
            continue
        errors.extend(other)

    if tree_moved_names:
        errors.append(
            f"mutation proof: {len(tree_moved_names)} proof record(s) were taken on a "
            f"different source/fixture tree (recorded {sorted(recorded_digests)}, now "
            f"{digest[:12]}), so they describe bytes that are no longer what runs. Every "
            f"assertion they carry is unproven until the table is re-run: "
            f"PYTHONPATH=. .venv/bin/python tests/mutation_harness.py"
        )

    return {
        "proven": proven,
        "errors": errors,
        "tree_moved": bool(tree_moved_names),
        "tree_moved_mutations": sorted(tree_moved_names),
        "stale_tree_only": stale_tree_only,
        "records": proofs,
    }


# The families a proof rejection can belong to, in the order they are worth reading. Used
# by §8's printer so one loud family cannot truncate another out of the printed head --
# the defect that made five of §8's own mutations unscoreable on 2026-09-12.
_ERROR_FAMILIES = (
    (_TREE_MOVED, "tree_moved"),
    ("NOT PHASE-1 ADMISSIBLE", "not_admissible"),
    ("PARTIAL", "partial"),
    ("schema_version", "schema_version"),
    ("NOT DETECTED", "not_detected"),
    ("SURVIVED", "survived"),
    ("were NOT observed", "marker_unobserved"),
    ("carry no observation", "marker_unrecorded"),
    ("definition has changed", "definition_stale"),
    ("label a proof carries", "wrong_label"),
    ("restored", "unrestored"),
    ("no baseline run", "no_baseline"),
    ("no mutation of that name", "orphaned"),
    ("unfinished write", "interrupted"),
    ("not valid JSON", "malformed"),
    ("must be filed under the name", "misfiled"),
)


def error_family(message: str) -> str:
    """Which rejection family this message belongs to. 'other' is a loud default."""
    for needle, family in _ERROR_FAMILIES:
        if needle in message:
            return family
    return "other"


def proven_labels(mutations: Iterable[Any],
                  require_phase1_admissible: bool = True) -> Tuple[Set[str], List[str]]:
    """(labels proven by EXECUTED evidence, one error per proof that does not hold)."""
    result = evaluate(mutations, require_phase1_admissible)
    return result["proven"], result["errors"]
