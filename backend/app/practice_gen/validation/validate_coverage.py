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

KNOWN LIMITATION (Scaling Mandate 6)
------------------------------------
A validator that neither declares `ASSERTIONS` nor prints a `  FAIL <label>` line is
invisible here, and so is a new failure mode folded into an existing label's error list.
§8's unit is the assertion, not the mutation: where two mutations prove one label, either
may be deleted without §8 noticing — §7's `mutations` floor is what guards that.

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

REPO_ROOT = Path(__file__).resolve().parents[4]
_VALIDATION_DIR = Path(__file__).resolve().parent

# The one module whose assertion labels are DISCOVERED rather than declared.
_MATRIX_MODULE = "validate_matrix.py"

# Modules that hold no assertions of their own (packet builder, manifest tables). They
# are still scanned for stray `  FAIL <label>` prints; they simply declare nothing.
_HELPER_MODULES = {"__init__.py", "judgment_packets.py", "_manifest.py"}

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
)

# Assertions that can fail but have no mutation proving they do. Each needs a reason and a
# date. This list may only ever get SHORTER. Adding to it to make a run pass is the move it
# exists to catch -- write the mutation instead.
UNPROVEN_ASSERTIONS: Dict[str, str] = {
    # ---- §1* validate_matrix -------------------------------------------------------
    "answer_key_recomputation":     "2026-08-28: §1E sibling; answer_key_integrity is proven, this path is not",
    "concept_gating":               "2026-08-28: distractor-provenance gate; vocabulary_gating is proven, this is not",
    "import_dna":                   "2026-08-28: overlaps compatibility_table, which is proven",
    "interest_invariance_formatted": "2026-08-28: stage 4 covers the property; the matrix label is unproven",
    "interest_theme_generation":    "2026-08-28: as above",
    "reverse_compatibility_check_crash": "2026-08-28: crash variant of a proven check",
    "reverse_curriculum_gate_check": "2026-08-28: curriculum-gate reverse path, unproven",
    "reverse_curriculum_gate_check_crash": "2026-08-28: crash variant of the above",
    "visual_schema_integrity":      "2026-08-28: SHADOWED, measured. Three plants were tried and none isolated it: negative counts and non-coercible types are both caught first by §1G (visual_payload), and a wrong-typed extra field violates nothing because the Pydantic schema coerces and total_value is not even declared. §4 adds little over §1G+§9 on this payload -- worth revisiting as a possible merge rather than a missing mutation",
    "worker_crash":                 "2026-08-28: infrastructure label, not a content assertion",
    "NODE_TO_DNA_presence":         "2026-09-08: registry mapping presence. Was spelled `node_to_dna_presence` from 2026-08-28 to 2026-09-08 and matched no emitted label, so it excused nothing while the real label sat outside the inventory",
    # These eleven were emitted as f-strings and invisible to the old regex. Each is now
    # inventoried by its family name; the ones with mutations are absent from this list.
    "generate_scalar":              "2026-09-08: generation crash at a probe scalar; the boundary mutations plant VALUE errors, which the exactness/containment labels catch first",
    "scalar_exactness_0.0":         "2026-09-08: the 0.0 end of §1A. boundary_off_by_one plants at 1.0; a 0.0 plant that does not also break per-item validity has not been found",
    "scalar_exactness_1.0_exceed":  "2026-09-08: §1A's no-sample-exceeds-max guard at t=1.0. leaky_window plants +10 at 1.0 and window_containment (§1B) reports it first",
    "value_containment":            "2026-09-08: §1B's per-value sweep. leaky_window is caught by window_containment before this label is reached",
    "reach_generation":             "2026-09-08: generation crash during the §1A-reach probe; same shape as generate_scalar",
    "value_reaches_max":            "2026-09-08: §1A-reach proper. Needs a plant that caps the generator below the competency ceiling WITHOUT breaking per-item validity, so §1A/§1B do not catch it first. Not yet found; the axis-catalog mapping is shared, so capping it trips the boundary checks. (Was allowlisted as `scalar_1_0_reach`, a label no check site emits.)",
    "discrete_integrity":           "2026-09-08: a discrete axis value must round-trip into the generated item. Unproven",
    "discrete_gen":                 "2026-09-08: generation crash at a pinned discrete value. Unproven",
    "monotonicity":                 "2026-09-08: §1B's difficulty monotonicity across the scalar sweep. Unproven",
    # ---- §2 validate_compat --------------------------------------------------------
    "registry_coverage":            "2026-09-08: KG<->NODE_TO_DNA<->COMPATIBILITY bidirectional coverage. registry_drift plants in COMPATIBILITY and compatibility_table reports it first",
    "kg_monotonicity":              "2026-09-08: cumulative-vocabulary monotonicity across the knowledge graph. Unproven",
    "lab_portal_equivalence":       "2026-09-08: Lab and portal must serve the same node the same way. Unproven",
    "competency_bounds_parsing":    "2026-09-08: the FIXTURE-table half of bounds parsing; all_competency_bounds_parse is the tree-wide property and IS proven",
    # ---- §3 validate_dna -----------------------------------------------------------
    "dna_structure":                "2026-09-08: DNA structural checks (formula/visual/static_bank/algorithmic). Unproven since §3 was written; a plant is cheap and this is the next debt to pay",
    "dna_difficulty_feasibility":   "2026-09-08: every difficulty profile must be satisfiable. Unproven",
    # ---- stage 4 validate_interest -------------------------------------------------
    "interest_invariance":          "2026-09-08: the stage that the two matrix interest labels are excused AGAINST is itself unproven, so nothing in the interest column is proven anywhere",
    # ---- validate_vocab ------------------------------------------------------------
    "static_vocab_gated_lint":      "2026-09-08: the static half of vocabulary gating (skeleton banks, not rendered output). vocab_leak proves the RENDERED path (§1D)",
    "vocab_audit_pass_rate":        "2026-09-08: full-node vocabulary audit pass-rate gate. Same defect class as §1D's vocabulary_gating, which is proven, on a different code path",
    # ---- §5 validate_judgment ------------------------------------------------------
    "judgment_review_schema_5":     "2026-09-08: per-node review schema (seeds, samples, six findings, verdicts). Unproven",
    "judgment_review_freshness_5":  "2026-09-08: STALE detection -- a review whose seeds no longer render what was judged. Unproven; this is the highest-value §5 debt because it is what makes a review expire",
    "judgment_quote_provenance_5":  "2026-09-08: a rationale quoting content absent from its own packet. Unproven",
    "judgment_rationale_verbatim_5": "2026-09-08: byte-identical rationale reused across nodes. template_review proves the SKELETON cluster, which is the harder form",
    "judgment_reviewer_plurality_5": "2026-09-08: one 'reviewed_by' identity spanning more than one blind batch. The §6H twin (attester_plurality_6H) IS proven",
    "judgment_reviews":             "2026-09-08: run_all's rollup print for §5; the sub-assertions above carry the proof",
    # ---- §6 validate_capability ----------------------------------------------------
    "capability_unattested_6F":     "2026-09-08: a declared capability with no blind Attester verdict. Dominates by volume while the attestation queue is open, which is exactly why a mutation would be hard to tell from the backlog",
    "attester_evidence_6G":         "2026-09-08: a verdict with no reasoning, no cited seed, or a seed absent from its own packet. template_attestation proves the SKELETON-cluster path of §6G only",
    "capability_contract":          "2026-09-08: run_all's rollup print for §6; the sub-assertions above carry the proof",
    # ---- §7 validate_census --------------------------------------------------------
    "census_unit_tests":            "2026-09-08: the unit-test floor. Proving it means shrinking the suite under the harness, which the mutation runner cannot restore safely if interrupted mid-collection",
    "census_mutations":             "2026-09-08: the mutation-count floor. A mutation that deletes mutations is self-referential; the floor is checked by hand when this file changes",
    # ---- §8 validate_coverage ------------------------------------------------------
    # (none: every direction of §8 is proven -- see the five coverage_* mutations)
    # ---- §10 validate_grade --------------------------------------------------------
    "grading_contract_floor_10":    "2026-09-08: §10's FULL-TREE path against GRADE_FLOOR. Both grading mutations run --node-ids, so they prove the zero-tolerance subset path only. §9's floor path IS proven (visual_payload_drops_required_key runs the whole tree), and this is the same gap on the grading side",
    # ---- §0 / run_all --------------------------------------------------------------
    "unit_tests":                   "2026-09-08: the §0 stage gate itself. Individual unit tests are not inventoried here; subtraction_candidate_pool_bounded is the one that is, because a mutation names it",
    "coverage_regression_1H":       "2026-09-08: §1E/§4/§1I coverage compared against the last recorded run. node_dropped_from_check proves the applicability half of §1H, not the regression half",
    "contract_doc_matches_registry": "2026-09-08: pgen_contract.md <-> CONTRACT_CHECKS equality. Unproven",
    "operator_doc_covers_registry": "2026-09-08: the testing_pipeline.md ref floor. Unproven",
    "two_direction_contract_match": "2026-09-08: executed checks vs registered checks. Unproven",
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


def proven_assertions() -> Set[str]:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from tests.mutation_harness import MUTATIONS

    proven: Set[str] = set()
    for m in MUTATIONS:
        proven |= set(m.asserts or ())
    return proven


def validate_coverage() -> List[str]:
    """Return an error per assertion that is neither proven nor knowingly excused."""
    inventory = harness_assertion_labels()
    proven = proven_assertions()
    printed, errors = printed_check_labels()

    unexplained = sorted(inventory - proven - set(UNPROVEN_ASSERTIONS))
    for label in unexplained:
        errors.append(
            f"§8 coverage: assertion {label!r} can fail but no mutation proves it does, and "
            f"it is not in UNPROVEN_ASSERTIONS. An unproven check is a broken check. Write "
            f"the mutation, or add an entry with a reason and a date -- and note the "
            f"allowlist may only shrink."
        )

    # The allowlist must shrink, never grow. Anything on it that is NOW proven should be
    # removed, and anything on it that no longer exists is stale bookkeeping.
    for label in sorted(set(UNPROVEN_ASSERTIONS) & proven):
        errors.append(
            f"§8 coverage: {label!r} is listed as unproven but a mutation now proves it. "
            f"Remove it from UNPROVEN_ASSERTIONS -- the allowlist is a debt register, and "
            f"leaving a paid debt on it hides how much is really left."
        )

    # An allowlist entry naming a label nothing emits excuses NOTHING while reading as an
    # accounted-for debt. Both entries this check found on the day it was written
    # (`node_to_dna_presence`, `scalar_1_0_reach`) were of exactly that shape.
    for label in sorted(set(UNPROVEN_ASSERTIONS) - inventory):
        errors.append(
            f"§8 coverage: UNPROVEN_ASSERTIONS names {label!r}, which no validator declares "
            f"and no check site emits. It excuses nothing while looking like an accounted-for "
            f"debt. Fix the spelling against the emitting site, or delete the entry."
        )

    # `Mutation.asserts` is free text, so a typo silently marks a label proven that no
    # check emits -- while the real label sits in the inventory, unproven and unexcused.
    for label in sorted(proven - inventory):
        errors.append(
            f"§8 coverage: a mutation asserts {label!r}, which no validator declares in "
            f"ASSERTIONS and validate_matrix never emits. Either the label is misspelled, or "
            f"the check it names must declare itself. A mutation proving a label nothing "
            f"emits proves nothing."
        )

    errors += check_phase_registry_failures()

    # Discovery direction: a check that reports itself must be inventoried.
    for label in sorted(set(printed) - inventory):
        errors.append(
            f"§8 coverage: {printed[label][0]} prints '  FAIL {label}' but no module declares "
            f"{label!r} in ASSERTIONS. A check that can report a failure and is not in the "
            f"inventory is a check §8 cannot tell you is unproven."
        )
    return errors


def validate_all() -> bool:
    inventory = harness_assertion_labels()
    proven = proven_assertions()
    declared = declared_assertion_labels()
    errors = validate_coverage()
    if errors:
        print(f"  FAIL assertion_coverage_8 ({len(errors)}):")
        for e in errors[:10]:
            print(f"    - {e}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more.")
        return False
    matrix = matrix_assertion_labels()
    print(f"  PASS assertion_coverage_8: {len(inventory & proven)}/{len(inventory)} harness "
          f"assertions proven ({len(matrix)} discovered in validate_matrix, "
          f"{len(inventory) - len(matrix)} declared across {len(declared)} modules), "
          f"{len(UNPROVEN_ASSERTIONS)} knowingly unproven (allowlist may only shrink)")
    return True


def main() -> int:
    return 0 if validate_all() else 1


if __name__ == "__main__":
    sys.exit(main())
