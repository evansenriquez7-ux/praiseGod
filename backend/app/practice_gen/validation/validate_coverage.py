"""
§8 — how many of the harness's assertions are actually proven.

Why this exists
---------------
"17 of 24 checks proven" was measured against the wrong denominator. `CONTRACT_CHECKS`
conflates bundles with atomic checks: `§2` was five sub-checks, `§3` is four DNA
validators, and `validate_matrix` alone emits **38 distinct assertion labels** behind
about eleven refs. A ref counted as proven the moment ONE of its sub-assertions had a
mutation, so §5 read as proven on the strength of a single boilerplate mutation while its
STALE and non-PASS paths were untouched.

And `Mutation.expected_check` was free text. Nothing could state which assertions were
proven, so the deficit could not be counted, tracked, or stopped from growing.

`Mutation.asserts` is now the machine-checkable link. This module inventories every
assertion the harness can emit and requires each to be either proven by a mutation or
named in UNPROVEN_ASSERTIONS with a reason and a date.

Why the inventory is the whole harness and not just the matrix
--------------------------------------------------------------
Until 2026-09-08 the inventory was a regex for `"check": "..."` over validate_matrix.py
and nothing else. Measured that day: 26 labels inventoried, 43 proven — **27 mutations
proved assertions §8 had never heard of**, every mutation added in the four preceding
commits included. Deleting any of those 27 left §8 printing PASS. §8 is the gate that
measures whether the other gates are real, and it was measuring 37% of them.

The regex was also wrong about the matrix itself:

  * `"check": f"window_containment_{scalar}_{axis_name}"` is an f-string, so the pattern
    skipped it. Eleven assertion FAMILIES were invisible — including the two that the
    harness's two OLDEST mutations (`leaky_window`, `boundary_off_by_one`) prove.
  * `[a-z0-9_]+` cannot match `NODE_TO_DNA_presence`. Its allowlist entry was spelled
    `node_to_dna_presence`, matched nothing, and excused nothing. So did `scalar_1_0_reach`,
    a name no check site ever emitted.

How an assertion gets inventoried
---------------------------------
Two mechanisms, because the harness has two shapes of assertion:

  * DISCOVERED — validate_matrix records `{"check": <label>}` at every check site, so its
    labels are read straight out of the AST with f-strings collapsed to their family name
    (`window_containment_{scalar}_{axis}` -> `window_containment`). Nothing to maintain: a
    new check site is inventoried the moment it is written.
  * DECLARED — every other validator reports a whole check group through one
    `print("  FAIL <label>")` and returns error strings, so there is no per-assertion
    marker to discover. Each module declares `ASSERTIONS`, naming what it can
    independently fail on, next to the checks themselves.

A declaration can rot, so it is pinned from three more directions (see `validate_coverage`):
a mutation may not assert a label no module declares; the allowlist may not name one
either; and every `  FAIL <label>` a validator prints must be in the inventory, which is
what catches a check added without a declaration.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
A validator that neither declares `ASSERTIONS` nor prints a `  FAIL <label>` line is
invisible here, and so is a new failure mode folded into an existing label's error list.
§8's unit is the assertion, not the mutation: where two mutations prove one label, either
may be deleted without §8 noticing — §7's `mutations` floor is what guards that.

An unproven label is reported in one of three families, because each takes a different
fix: `never_executed` (claimed, but no proof record exists — run it), `proof_does_not_hold`
(a record exists and fails verification, e.g. a red baseline — repair the control and
re-run it, do NOT write a second mutation), and `unproven_assertion` (nothing claims the
label — write a mutation or record a dated allowlist entry). What this still does not
distinguish is Mandate 2's two causes of a SURVIVING mutation: a broken check and a plant
that stopped reaching the validated path read identically here.

**§8 proved by DECLARATION until 2026-09-12; it now proves by EXECUTION.**
`proven_assertions()` used to read `Mutation.asserts` out of the mutation table. It never
ran a mutation and never learned whether one was DETECTED, so a mutation that SURVIVED —
or that the runner refused to score, reporting INVALID because the validator was already
failing — still marked its label proven, and still tripped `assertion_allowlist_paid_8` if
the label was also allowlisted. Named 2026-09-10, when `mcq_reviewed_without_options` (a
correct plant against a check whose baseline is red by construction) could not be carried
on the allowlist for exactly that reason.

It is closed by making a run of the mutation table leave an artifact this gate can read.
`tests/mutation_harness.py` writes one proof record per EXECUTED mutation to
`validation_reports/mutation_proofs/`; `mutation_proof.verify_proof` rejects a record that
is missing, partial, malformed, interrupted, stale against the mutation definition or the
working-tree bytes, reporting a SURVIVED result, or carrying an expected marker that was
not observed. A label counts as proven here only when a record survives all of that.

`run_all` CONSUMES those records and never invokes the runner: a gate that can regenerate
its own evidence is not a gate. There is no flag that makes this accept a stale proof.

WHAT EXECUTION-PROOF STILL DOES NOT PROVE (Mandate 6)
-----------------------------------------------------
That a check fires on one planted violation. Not that the check is correct, not that the
violation is the only shape of that defect, and not that a surviving mutation means the
check is broken rather than that the plant stopped reaching the validated path — Mandate
2's two causes are still told apart by hand.

Why a floor and not a hard zero
-------------------------------
The deficit is real today. Mandate §5: a check whose baseline is already red cannot be
told from the noise it sits in. So the allowlist is a floor that may only SHRINK -- a NEW
assertion with neither a mutation nor an entry fails immediately, which is the point. The
deficit can never grow again, only be paid down.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

from backend.app.practice_gen.validation import mutation_proof

REPO_ROOT = Path(__file__).resolve().parents[4]
_VALIDATION_DIR = Path(__file__).resolve().parent

# The one module whose assertion labels are DISCOVERED rather than declared.
_MATRIX_MODULE = "validate_matrix.py"

# Modules that hold no assertions of their own (packet builder, manifest tables). They
# are still scanned for stray `  FAIL <label>` prints; they simply declare nothing.
_HELPER_MODULES = {"__init__.py", "judgment_packets.py", "_manifest.py",
                   "mutation_proof.py"}

# §8 inventory: this module's own directions. Each is a separate way the coverage gate can
# fail, and each has its own mutation -- a gate that measures other gates has no business
# being the one gate that is unproven.
ASSERTIONS = (
    "assertion_coverage_8",           # inventoried, unproven, and not excused
    "assertion_allowlist_paid_8",     # an allowlisted label a mutation now proves
    "assertion_allowlist_phantom_8",  # an allowlist entry naming a label nothing emits
    "assertion_asserts_unknown_8",    # a mutation asserting a label nothing declares
    "assertion_undeclared_check_8",   # a printed `  FAIL` label no module declares
    "check_phase_registry_8",         # a contract ref that declares no harness phase
    "silent_path_disposition_8",      # a silent exception handler with no recorded
                                      # disposition (plan step 0's inventory)
    "mutation_proof_integrity_8",     # an executed-proof record that does not hold
)

# Assertions that can fail but have no mutation proving they do. Each needs a reason and a
# date. This list may only ever get SHORTER. Adding to it to make a run pass is the move it
# exists to catch -- write the mutation instead.
UNPROVEN_ASSERTIONS: Dict[str, str] = {
    # ---- §1* validate_matrix -------------------------------------------------------
    "concept_gating":               "2026-08-28: distractor-provenance gate; vocabulary_gating is proven, this is not",
    "reverse_compatibility_check_crash": "2026-08-28: crash variant of a proven check",
    "reverse_curriculum_gate_check": "2026-08-28: curriculum-gate reverse path, unproven",
    "reverse_curriculum_gate_check_crash": "2026-08-28: crash variant of the above",
    "visual_schema_integrity":      "2026-08-28: SHADOWED, measured. Three plants were tried and none isolated it: negative counts and non-coercible types are both caught first by §1G (visual_payload), and a wrong-typed extra field violates nothing because the Pydantic schema coerces and total_value is not even declared. §4 adds little over §1G+§9 on this payload -- worth revisiting as a possible merge rather than a missing mutation",
    # These eleven were emitted as f-strings and invisible to the old regex. Each is now
    # inventoried by its family name; the ones with mutations are absent from this list.
    "monotonicity":                 "2026-09-08: §1B's difficulty monotonicity across the scalar sweep. Unproven",
    # ---- §2 validate_compat --------------------------------------------------------
    # ---- §3 validate_dna -----------------------------------------------------------
    # ---- §5 validate_judgment ------------------------------------------------------
    # Five §5 entries were paid on 2026-09-10 (stale_review_undetected,
    # stale_answer_same_key, review_schema_incomplete, fabricated_quote,
    # verbatim_rationale_reuse, single_reviewer_identity). §5 had declared six assertions
    # and proven one; five could have been silently broken and its 696 findings would have
    # looked identical either way.
    "judgment_reviews":             "2026-09-08: run_all's rollup print for §5; the sub-assertions above carry the proof",
    # ---- §6 validate_capability ----------------------------------------------------
    "capability_contract":          "2026-09-08: run_all's rollup print for §6; the sub-assertions above carry the proof",
    # ---- §7 validate_census --------------------------------------------------------
    "census_unit_tests":            "2026-09-08: the unit-test floor. Proving it means shrinking the suite under the harness, which the mutation runner cannot restore safely if interrupted mid-collection",
    "census_mutations":             "2026-09-08: the mutation-count floor. A mutation that deletes mutations is self-referential; the floor is checked by hand when this file changes",
    # ---- §8 validate_coverage ------------------------------------------------------
    # (none: every direction of §8 is proven -- see the five coverage_* mutations)
    # ---- §10 validate_grade --------------------------------------------------------
    # PAID 2026-09-12. `grading_contract_floor_10` sat here from 2026-09-08 because both
    # grading mutations ran --node-ids and a full sweep cost 14m23s. Making §10 hermetic
    # (H-01) dropped the full tree to 33 seconds, so
    # `grader_rejects_correct_answer_tree_wide` now plants against the floor path itself.
    # §10's other four assertions are proven by the five mutations added with them.
    # ---- §0 / run_all --------------------------------------------------------------
    "coverage_regression_1H":       "2026-09-08: §1E/§4/§1I coverage compared against the last recorded run. node_dropped_from_check proves the applicability half of §1H, not the regression half",
    # PAID 2026-09-12 by `crash_deletes_its_own_expected_refs`. The tripwire was unproven
    # for four days; the plant that proves it is the one that matters most, because it
    # silences the tripwire using the very crash that stopped a check executing.
}


def _validation_modules() -> List[Path]:
    """Every module in the validation package, in a stable order."""
    return sorted(p for p in _VALIDATION_DIR.glob("*.py") if p.name != "__init__.py")


def _literal_prefix(node: ast.AST) -> str | None:
    """
    The leading literal text of a string constant or f-string.

    An f-string stops at its first placeholder: `f"scalar_exactness_1.0_{axis}"` yields
    `scalar_exactness_1.0_`, which is the assertion FAMILY. Collapsing the placeholder is
    the point -- one label per check site, not one per axis name.
    """
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.JoinedStr):
        parts: List[str] = []
        for piece in node.values:
            if isinstance(piece, ast.Constant) and isinstance(piece.value, str):
                parts.append(piece.value)
            else:
                break
        return "".join(parts)
    return None


def matrix_assertion_labels() -> Set[str]:
    """
    Every `{"check": <label>}` the behavioural matrix can emit, from its AST.

    Read from the syntax tree rather than by regex because eleven of the labels are
    f-strings, which a `"check": "..."` pattern silently skips -- including the families
    the harness's two oldest mutations prove. An unresolvable `check` value is a hard
    failure: a label this function cannot read is a check §8 cannot inventory.
    """
    path = _VALIDATION_DIR / _MATRIX_MODULE
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    labels: Set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant) and key.value == "check"):
                continue
            prefix = _literal_prefix(value)
            if prefix is None:
                raise AssertionError(
                    f"{_MATRIX_MODULE}:{getattr(value, 'lineno', '?')}: a 'check' label that "
                    f"is neither a string nor an f-string cannot be inventoried by §8. Give "
                    f"the check site a literal label."
                )
            labels.add(prefix.rstrip("_"))
    return labels


def declared_assertion_labels() -> Dict[str, Tuple[str, ...]]:
    """
    `ASSERTIONS` as declared by each validation module: {module name: labels}.

    Imported rather than parsed so a module may DERIVE its labels from the data that
    drives its checks -- validate_census builds them from CENSUS_FLOORS, so adding a floor
    adds an assertion that must then be proven or excused. An import failure is raised,
    not swallowed: a validation module that will not import contributes zero assertions,
    and a silent zero here reads as "nothing left to prove".
    """
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    declared: Dict[str, Tuple[str, ...]] = {}
    for path in _validation_modules():
        if path.name in _HELPER_MODULES:
            continue
        module = importlib.import_module(
            f"backend.app.practice_gen.validation.{path.stem}"
        )
        labels = getattr(module, "ASSERTIONS", ())
        if not isinstance(labels, Sequence) or isinstance(labels, str):
            raise AssertionError(
                f"{path.name}: ASSERTIONS must be a sequence of label strings, got "
                f"{type(labels).__name__}."
            )
        if labels:
            declared[path.name] = tuple(labels)
    return declared


def printed_check_labels() -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Every `print("  FAIL <label>")` site in the package: ({label: [sites]}, violations).

    This is the drift trap on the DECLARED half. A new check group reports itself with a
    `  FAIL` line; if its label is not in the inventory, §8 says so, which is what stops a
    check being added without either a mutation or an honest allowlist entry.

    A site whose label is a placeholder (`f"  FAIL {label}"`) re-reports a check named
    elsewhere -- validate_compat's --only runner is the case -- and is skipped. A site
    whose label is neither an identifier nor a placeholder is a convention violation and
    is reported, because §8 cannot tell which assertion it belongs to.
    """
    marker = "  FAIL "
    sites: Dict[str, List[str]] = {}
    violations: List[str] = []
    for path in _validation_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "print" and node.args):
                continue
            prefix = _literal_prefix(node.args[0])
            if prefix is None or not prefix.startswith(marker):
                continue
            rest = prefix[len(marker):]
            if not rest:
                continue  # `f"  FAIL {label}"` -- named at the site that owns the check
            head = ""
            for ch in rest:
                if ch.isalnum() or ch == "_":
                    head += ch
                else:
                    break
            if not head or not (head[0].isalpha() or head[0] == "_"):
                violations.append(
                    f"§8 coverage: {path.name}:{node.lineno} prints '  FAIL {rest[:40]}...', "
                    f"whose label is not a bare identifier. §8 inventories assertions by the "
                    f"label a check prints; give this site an identifier label (and declare "
                    f"it in that module's ASSERTIONS) or drop the '  FAIL ' prefix if it is "
                    f"not an assertion report."
                )
                continue
            sites.setdefault(head, []).append(f"{path.name}:{node.lineno}")
    return sites, violations


def check_phase_registry_failures() -> List[str]:
    """
    Every contract §-ref must declare which harness phase it runs in, and vice versa.

    `_manifest.CHECK_PHASE` is what makes `run_all --phase 1` mean anything: a ref with no
    phase is a check that band-scoped runs silently omit, and the two-direction tripwire
    would then pass while the stage never ran. Measured 2026-09-09 before the registry went
    harness-wide: 28 of 35 refs carried no phase at all, so "Phase 1 is done" could only be
    asserted by running ten commands by hand and reading them.

    Checked in both directions, because both failures are silent. A registered check with
    no phase is omitted from every phased run; a phased ref nobody registered is a phase
    decision about a check that does not exist. `PHASE_ONLY_REFS` is the declared exception
    -- §6A/§6B/§6C are cited by findings and phased for the partition gate, but carry no
    CONTRACT_CHECKS row of their own.
    """
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from backend.app.practice_gen.validation._manifest import CHECK_PHASE, PHASE_ONLY_REFS
    from backend.app.practice_gen.validation.run_all import CONTRACT_CHECKS

    errors: List[str] = []
    for ref in sorted(set(CONTRACT_CHECKS) - set(CHECK_PHASE)):
        errors.append(
            f"§8 coverage: contract check {ref!r} declares no phase in "
            f"_manifest.CHECK_PHASE. `run_all --phase N` would omit it from every band, "
            f"and the two-direction tripwire would still pass -- a check that runs in no "
            f"phase is a check that stops running the moment anyone runs a phase."
        )
    for ref in sorted(set(CHECK_PHASE) - set(CONTRACT_CHECKS) - PHASE_ONLY_REFS):
        errors.append(
            f"§8 coverage: _manifest.CHECK_PHASE phases {ref!r}, which CONTRACT_CHECKS "
            f"does not register. Either add its contract row, or add it to "
            f"PHASE_ONLY_REFS with the reason it carries no row of its own."
        )
    return errors


def harness_assertion_labels() -> Set[str]:
    """The full inventory: discovered matrix labels plus every declared stage label."""
    labels = matrix_assertion_labels()
    for module_labels in declared_assertion_labels().values():
        labels |= set(module_labels)
    return labels


def _mutations() -> Sequence:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from tests.mutation_harness import MUTATIONS

    return MUTATIONS


def declared_assertions() -> Set[str]:
    """
    Every label a mutation CLAIMS to prove. Not evidence — see `proven_assertions`.

    Still needed in two directions that are about the table rather than about any run:
    `assertion_asserts_unknown_8` (a mutation naming a label nothing emits) is a defect in
    the table whether or not the mutation has been executed, and it must be reported the
    same way on a tree with no proofs at all.
    """
    proven: Set[str] = set()
    for m in _mutations():
        proven |= set(m.asserts or ())
    return proven


def _proof_state() -> Dict[str, object]:
    """The executed-proof corpus, evaluated once per call site that needs it."""
    return mutation_proof.evaluate(_mutations())


def proven_assertions() -> Set[str]:
    """
    The labels an EXECUTED, verified, current mutation proof record establishes.

    Not `Mutation.asserts`: that is what the table claims, and a claim is what this gate
    exists to stop counting. See the module docstring and
    `backend/app/practice_gen/validation/mutation_proof.py`.
    """
    return _proof_state()["proven"]  # type: ignore[return-value]


def mutation_proof_failures() -> List[str]:
    """
    One error per proof record on disk that does not hold.

    A mutation with NO record is not reported here — `validate_coverage`'s inventory pass
    reports the resulting hole as an unproven assertion, which is the same finding stated
    where it belongs. Splitting them matters: "never run" and "run, and the result does
    not stand" have different fixes.

    The inventory pass honours that split in THREE families, not two (fixed 2026-09-16):
    `never_executed` (no record), `proof_does_not_hold` (a record exists and fails
    verification), and `unproven_assertion` (no mutation claims the label at all). Until
    the second family existed, 19 labels whose proofs had been taken against a red
    baseline were reported as having no mutation, and the message told the reader to
    write one.
    """
    return _proof_state()["errors"]  # type: ignore[return-value]


def unproven_because_never_executed() -> List[str]:
    """
    Mutations that claim a label but have filed no proof record at all.

    Reported separately from a failed proof so the remaining work is countable: this list
    shrinking to empty is what "the table has been run on these bytes" looks like.
    """
    records, _errs = mutation_proof.load_proofs()
    return sorted(m.name for m in _mutations() if m.asserts and m.name not in records)


def validate_coverage() -> List[str]:
    """Return an error per assertion that is neither proven nor knowingly excused."""
    return [msg for msg, _fam in validate_coverage_tagged()]


def validate_coverage_tagged() -> List[Tuple[str, str]]:
    """`validate_coverage`, with each error paired to the family it belongs to."""
    inventory = harness_assertion_labels()
    state = _proof_state()
    proven: Set[str] = state["proven"]          # type: ignore[assignment]
    stale_tree_only: Set[str] = state["stale_tree_only"]   # type: ignore[assignment]
    declared = declared_assertions()
    printed, errors = printed_check_labels()
    # One tag per error, in step with `errors`, so the printer can show a member of every
    # family instead of the first ten of the loudest one.
    families: List[str] = ["printed_scan"] * len(errors)

    never_run = set(unproven_because_never_executed())
    # A label can be unproven in THREE ways, and they take three different fixes. Reporting
    # the third as the first is how 19 assertions on 2026-09-15 told the reader to "write
    # the mutation" for checks that already had one -- the proof had been taken against a
    # red baseline. Following that message would have added a duplicate rather than re-run
    # the control from a clean tree.
    failed_verification: Dict[str, List[str]] = state["failed_verification"]  # type: ignore[assignment]
    # `stale_tree_only` labels DO have executed proofs; the single tree-move error above
    # already says why they do not currently count, and repeating it per label would
    # bury the finding a planted mutation is meant to surface.
    unexplained = sorted(inventory - proven - set(UNPROVEN_ASSERTIONS) - stale_tree_only)
    for label in unexplained:
        claimants = sorted(m.name for m in _mutations() if label in (m.asserts or ()))
        if claimants and set(claimants) & never_run:
            families.append("never_executed")
            errors.append(
                f"§8 coverage: assertion {label!r} is claimed by mutation(s) {claimants} "
                f"that have filed NO executed proof record on these bytes. A mutation that "
                f"has not been run proves nothing. Run: PYTHONPATH=. .venv/bin/python "
                f"tests/mutation_harness.py --only {claimants[0]}"
            )
            continue
        broken = [c for c in claimants if c in failed_verification]
        if broken:
            families.append("proof_does_not_hold")
            reasons = "; ".join(
                f"{c}: {failed_verification[c][0]}" for c in broken
            )
            errors.append(
                f"§8 coverage: assertion {label!r} IS claimed by mutation(s) {broken}, and "
                f"each has filed a proof record that does NOT hold -- so the assertion is "
                f"unproven, but the mutation is not missing. Do NOT write another mutation "
                f"and do NOT allowlist it: fix what the record says and re-run it. "
                f"Rejection(s): {reasons}"
            )
            continue
        families.append("unproven_assertion")
        errors.append(
            f"§8 coverage: assertion {label!r} can fail but no mutation proves it does, and "
            f"it is not in UNPROVEN_ASSERTIONS. An unproven check is a broken check. Write "
            f"the mutation, or add an entry with a reason and a date -- and note the "
            f"allowlist may only shrink."
        )

    # The allowlist must shrink, never grow. Anything on it that is NOW proven should be
    # removed, and anything on it that no longer exists is stale bookkeeping.
    for label in sorted(set(UNPROVEN_ASSERTIONS) & declared):
        families.append("allowlist_paid")
        errors.append(
            f"§8 coverage: {label!r} is listed as unproven but a mutation now proves it. "
            f"Remove it from UNPROVEN_ASSERTIONS -- the allowlist is a debt register, and "
            f"leaving a paid debt on it hides how much is really left."
        )

    # An allowlist entry naming a label nothing emits excuses NOTHING while reading as an
    # accounted-for debt. Both entries this check found on the day it was written
    # (`node_to_dna_presence`, `scalar_1_0_reach`) were of exactly that shape.
    for label in sorted(set(UNPROVEN_ASSERTIONS) - inventory):
        families.append("allowlist_phantom")
        errors.append(
            f"§8 coverage: UNPROVEN_ASSERTIONS names {label!r}, which no validator declares "
            f"and no check site emits. It excuses nothing while looking like an accounted-for "
            f"debt. Fix the spelling against the emitting site, or delete the entry."
        )

    # `Mutation.asserts` is free text, so a typo silently marks a label proven that no
    # check emits -- while the real label sits in the inventory, unproven and unexcused.
    for label in sorted(declared - inventory):
        families.append("asserts_unknown")
        errors.append(
            f"§8 coverage: a mutation asserts {label!r}, which no validator declares in "
            f"ASSERTIONS and validate_matrix never emits. Either the label is misspelled, or "
            f"the check it names must declare itself. A mutation proving a label nothing "
            f"emits proves nothing."
        )

    phase_errors = check_phase_registry_failures()
    errors += phase_errors
    families += ["phase_registry"] * len(phase_errors)

    # Discovery direction: a check that reports itself must be inventoried.
    for label in sorted(set(printed) - inventory):
        families.append("undeclared_check")
        errors.append(
            f"§8 coverage: {printed[label][0]} prints '  FAIL {label}' but no module declares "
            f"{label!r} in ASSERTIONS. A check that can report a failure and is not in the "
            f"inventory is a check §8 cannot tell you is unproven."
        )
    return list(zip(errors, families))


# How many errors to print per stage, and the rule that stops the head being useless.
_PRINT_BUDGET = 10


def _print_findings(label: str, errors: List[str], families: List[str]) -> None:
    """
    Print a bounded head of `errors` that shows at least one of EVERY family present.

    A flat `errors[:10]` looked harmless and was not. §8 can emit six unrelated families
    at once, and the largest of them -- one line per assertion still lacking a proof --
    drowned the rest: measured 2026-09-12, five of the seven mutations that prove §8's
    own directions scored as "exited 1 but output lacked expected marker(s)", because the
    planted finding was real, was in the list, and was truncated out of the printed head.
    A mutation cannot be told from noise by a check that will not print it.

    `families` is a parallel list of tags, one per error, so grouping is by what the error
    IS rather than by a regex over its prose.
    """
    order: List[str] = []
    grouped: Dict[str, List[str]] = {}
    for fam, err in zip(families, errors):
        grouped.setdefault(fam, []).append(err)
        if fam not in order:
            order.append(fam)

    print(f"  FAIL {label} ({len(errors)} in {len(order)} famil{'y' if len(order) == 1 else 'ies'}):")
    shown = 0
    # One from each family first, so nothing is invisible; then fill the budget.
    for fam in order:
        print(f"    - {grouped[fam][0]}")
        shown += 1
    for fam in order:
        for err in grouped[fam][1:]:
            if shown >= max(_PRINT_BUDGET, len(order)):
                break
            print(f"    - {err}")
            shown += 1
    if shown < len(errors):
        print(f"    ... and {len(errors) - shown} more.")


def silent_path_failures() -> List[str]:
    """
    Every silent exception handler in the package that carries no recorded disposition.

    THE OBLIGATION (plan step 0): "Inventory every warning, `continue`, exception handler
    ... Each receives one of three dispositions: remove it by checking the obligation,
    turn it into a named failure, or record a narrow inherent limitation."

    A SILENT handler is one whose body does nothing but leave -- `continue`, `pass`, or a
    bare `return`, and nothing else. A handler that records a finding and THEN continues
    is the named-failure pattern this exists to encourage, not an instance of the defect;
    counting those would have flagged §10's own obligation handlers, which are exactly
    what the H-01 work replaced `except: continue` WITH.

    Why this sits in §8 rather than a §-ref of its own: §8 is already the gate that
    measures whether the other gates are real. "This assertion has no proof" and "this
    handler drops an obligation without saying so" are the same question asked of
    different things.

    MEASURED 2026-09-12: 33 silent handlers by the first (over-broad) definition, 19 by
    this one, and all 19 now carry a disposition -- 9 `checked`, 3 `named-failure`,
    7 `limitation`. Because the baseline reached ZERO unclassified, this is a hard zero
    rather than a shrink-only floor (Scaling Mandate 5): a silent handler added tomorrow
    fails the build instead of disappearing into a tolerated count.
    """
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from tests.silent_path_inventory import scan

    problems: List[str] = []
    for path in scan():
        if not path.disposition:
            problems.append(
                f"§8 silent path: {path.file}:{path.line} in {path.function}() catches "
                f"`{path.handler}` and does nothing but `{path.body}`. An obligation "
                f"dropped without a word is how attempted work gets reported as coverage. "
                f"Record a disposition in the handler: "
                f"`# DISPOSITION: checked|named-failure|limitation -- <why>`."
            )
        elif path.disposition == "INVALID":
            problems.append(
                f"§8 silent path: {path.file}:{path.line} in {path.function}() has a "
                f"DISPOSITION marker that names no known kind ({path.note[:60]!r}). "
                f"Use one of checked, named-failure, limitation."
            )
    return problems


def validate_all() -> bool:
    inventory = harness_assertion_labels()
    proven = proven_assertions()
    declared = declared_assertion_labels()
    proof_errors = mutation_proof_failures()
    tagged = validate_coverage_tagged()
    errors = [m for m, _f in tagged]

    ok = True
    # Reported as its own assertion rather than folded into the coverage rollup: "a proof
    # record does not hold" and "this label has no proof" are different failures with
    # different fixes, and a single label would let one hide inside the other's count.
    if proof_errors:
        _print_findings("mutation_proof_integrity_8", proof_errors,
                        [mutation_proof.error_family(e) for e in proof_errors])
        ok = False
    else:
        records, _ = mutation_proof.load_proofs()
        print(f"  PASS mutation_proof_integrity_8: {len(records)} executed mutation proof(s) "
              f"verified against the current source/fixture digest")

    silent = silent_path_failures()
    if silent:
        _print_findings("silent_path_disposition_8", silent,
                        ["silent_path"] * len(silent))
        ok = False
    else:
        from tests.silent_path_inventory import build_report
        counts = build_report()["counts"]
        print(f"  PASS silent_path_disposition_8: all "
              f"{counts['silent_handlers']} silent handler(s) carry a recorded "
              f"disposition ({counts['by_disposition']})")

    if errors:
        _print_findings("assertion_coverage_8", errors, [f for _m, f in tagged])
        return False
    if not ok:
        return False
    matrix = matrix_assertion_labels()
    print(f"  PASS assertion_coverage_8: {len(inventory & proven)}/{len(inventory)} harness "
          f"assertions proven BY EXECUTION ({len(matrix)} discovered in validate_matrix, "
          f"{len(inventory) - len(matrix)} declared across {len(declared)} modules), "
          f"{len(UNPROVEN_ASSERTIONS)} knowingly unproven (allowlist may only shrink)")
    return True


def main() -> int:
    return 0 if validate_all() else 1


if __name__ == "__main__":
    sys.exit(main())
