"""
§7 — the suite's own census has not silently got smaller.

Why this exists
---------------
Every other check in this harness asks whether the tree is correct. None asked how much
of the tree was being checked at all. Measured 2026-08-26: nothing anywhere asserted a
minimum node count, unit-test count, or mutation count, so the suite would report green
while shrinking:

  * a unit suite that drops from 349 tests to 12 still exits 0 and prints PASS;
  * a registry that loses 100 nodes has every stage check the remaining 51 and pass;
  * deleting mutations lowers `coverage.mutations_registered` and fails nothing.

A total wipe is already caught -- pytest exits 5 on an empty collection -- so this is
specifically about *silent shrinkage*, which is the realistic failure. The shape is not
hypothetical: while building this check, a test guarding the supervisor's queue
arithmetic was written with `@pytest.mark.slow`, a marker `tests/pytest.ini` deselects by
default. It sat in the repo looking like a gate while never running once.

Raise a floor when the real number rises. Never lower one to make a run pass; a floor
that yields is not a floor, and lowering it is precisely the move it exists to catch.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[4]

CENSUS_FLOORS = {
    "nodes": 151,
    # 399 collected 2026-09-08 (was 340, set when 349 were observed). 59 tests could
    # have stopped running without breaching it, which is the silent shrinkage this
    # floor exists to catch, so it is ratcheted to the real number less a little churn.
    # 412 collected 2026-09-10 (was 399), +9 from test_judgment_answer_resolution.py,
    # which pins the half of §5's answer comparison that NARROWS -- a narrowing cannot be
    # proven by a mutation, because the harness scores a plant by making the validator
    # fail and a narrowing makes it quieter. Ratcheted to the real number less churn.
    # 423 collected 2026-09-10 (was 412), +11 from test_attestation_freshness.py, which
    # pins §6F's branch ORDER and the half of its answer comparison that NARROWS -- the
    # same reason test_judgment_answer_resolution.py exists, one gate over.
    # 428 collected 2026-09-11 (was 424 at the previous ratchet's measurement), +4 from
    # test_media_the_competency_names.py. Those four are the ONLY gate on the equal-jumps
    # payload's existence: the component reads jump_count/jump_size inside a branch, so
    # the derived frontend contract classes them conditional and §9 enforces unconditional
    # keys only. Ratcheted to the real number less a little churn, as above.
    # 472 collected 2026-09-12 (was 428 at the previous ratchet's measurement), +45 from
    # test_mutation_proof.py -- the consumer behind §8's switch from declared to EXECUTED
    # proof. Every rejection reason (partial, malformed, interrupted, stale source, stale
    # definition, wrong label, unobserved marker, SURVIVED, unrestored tree, inadmissible
    # path) is planted there against isolated fixtures, because those directions cannot be
    # proven by a mutation: the mutation runner is the thing they judge. Ratcheted to the
    # real number less a little churn, as above.
    # 495 collected 2026-09-12 (was 473 at the previous ratchet's measurement), +22 from
    # test_hardening_status.py -- the H-row ledger's schema gate, proved in both
    # directions here because it is NOT reachable by the mutation harness: it is not
    # registered in run_all, since it tracks PLAN progress rather than pipeline
    # behaviour, and a §-ref for it would put planning state inside the contract the
    # pipeline is measured against. Every direction it can fail (closed with no proof
    # artifact, closed with no revision, out_of_scope with no deciding commit, a
    # revision that is not a commit, an artifact absent from disk, an open row still
    # carrying provenance, unknown status, duplicate id, wrong schema version, rows
    # missing) is planted against in-memory documents. Ratcheted to the real number less
    # a little churn, as above.
    # 552 collected 2026-09-12 (was 495 at the previous ratchet's measurement), +41 from
    # test_grade_bidirectional.py and +11 from test_hermetic_db.py -- the two halves of
    # §10's second direction (H-01). The emitter tests exist because `grading_refusal_10`
    # is only as strong as `_emit_wrong`: a "wrong" answer that is not actually wrong
    # makes the refusal gate pass vacuously and an always-true grader walks through it
    # again. The fixture tests exist because a hermetic database that silently fell back
    # to the CONFIGURED one would restore H-01 quietly -- the check would still pass, just
    # against a database across the public internet. Neither direction is reachable by a
    # mutation on the pipeline. Ratcheted to the real number less a little churn.
    # 573 collected 2026-09-12 (was 552 at the previous ratchet's measurement), +21 from
    # test_stage_ledger.py -- the H-03 crash boundary. Not reachable by a mutation against
    # a live run_all: a full Phase 1 costs ~8 minutes, and the Phase 2 band's baseline is
    # red by construction, so a plant there could not be scored at all (Mandate 2). These
    # drive the REAL StageLedger and the REAL run_all with every validator stubbed, and
    # three mutations plant into that control flow and are caught here by name.
    # 585 collected 2026-09-12 (was 576), +9 from test_obligation_manifest.py -- §11's
    # determinism half. "Enumeration is deterministic" is an H-04 acceptance item that
    # CANNOT be a mutation: a mutation proves a check fires, and determinism is the
    # absence of variation. It is pinned by test instead, alongside the assertions that
    # the budget report keeps saying what it does NOT cover.
    "unit_tests": 578,
    # 56 registered 2026-09-09 (was 51, 50, 48, 37). Four prove §8's own directions, one
    # §2C at (node, formatter) granularity, two the §6 phase seam, one that every contract
    # check declares the phase it runs in, four the §6 Phase 1 band (§6A/§6B/§6C/§6E, which
    # were unproven while 75 findings sat under them), and one that the declarations §6
    # reads are the ones an author wrote. The ten of headroom that existed before meant ten
    # mutations could be deleted silently, and §8 only notices a deletion that leaves a
    # label unproven -- where two mutations prove one label, this floor is the only guard.
    # 65 registered 2026-09-10 (was 56). Nine prove the Phase 2 band, which had exactly
    # two mutations across its nine assertions: six for §5 (freshness twice -- the stem
    # path and the key-valued answer path -- schema, quote provenance, verbatim reuse,
    # reviewer plurality, and the option-adjudicability check added with them), and two
    # for §6's attestation half (§6G's evidence branches and §6F's UNATTESTED branch,
    # which reported zero and could not say whether that meant "all attested" or "cannot
    # see a gap"). §8 counts assertions, not mutations, and `judgment_review_freshness_5`
    # is now proven by two of them -- so this floor is the only thing that notices if one
    # of that pair is deleted.
    # 68 registered 2026-09-10 (was 65). Three prove §6F's freshness branches beyond the
    # stem, which is all it compared until that day: the keyed VALUE, the offered options
    # (two branches in one plant), and a record that does not carry the options it was
    # shown. `capability_stale_attestation_6F` is now proven by three mutations and
    # nothing but this floor notices if two of them are deleted.
    # 70 registered 2026-09-10 (was 68): +1 for §6A's orphan-provider direction, added in
    # the commit that drove its count to zero (Scaling Mandate 5), and +1 for the WIDENED
    # declaration-sync gate -- `capability_declarations_in_sync_6` is now proven by two
    # mutations (one per field family), so this floor is the only guard on the pair.
    # 71 registered 2026-09-11 (was 70): +1 for `requires_ignore_locked_6B`, the gate
    # that makes owner ruling R-5 machine-checkable -- added while its count was zero.
    # 72 registered 2026-09-11 (was 71): +1 for the frontend visual contract, now derived
    # from the component AST instead of a hand-written key map that had drifted 35 keys.
    # 76 registered 2026-09-11 (was 72): +4 for the three media a competency names and the
    # pipeline did not render. Two prove labels that already had a mutation
    # (`answer_key_integrity`, `visual_payload`) and so are invisible to §8, which counts
    # assertions rather than mutations -- this floor is the only thing that notices if
    # either is deleted. One is caught by a unit test rather than any § check, which is
    # itself the finding it records.
    # 77 registered 2026-09-12 (was 76): +1 for `source_edited_without_reproof`, which
    # proves §8's new `mutation_proof_integrity_8` -- that an executed-mutation proof
    # record goes stale when the source it was taken against moves. Added in the commit
    # that made §8 count EXECUTED proofs rather than `Mutation.asserts`, i.e. while its
    # own finding count was zero (Scaling Mandate 5).
    # 79 registered 2026-09-12 (was 77): +2 for the two bounded student-path lints,
    # `count_noun_disagrees` (§1J) and `second_option_answers_too` (§1K). Both were added
    # with their gates, while each gate's finding count was zero.
    # 85 registered 2026-09-12 (was 79): +6 for §10's second direction and its hermetic
    # fixture (H-01). `grader_accepts_wrong_answer` is the exact mirror of
    # `grader_rejects_correct_answer` -- an ALWAYS-TRUE grader, which satisfied every §10
    # assertion perfectly until that day. `grader_coerces_malformed_boolean` and
    # `grader_drops_key_normalisation` restore the two real defects fixed with the gate.
    # `grading_obligation_silently_skipped` proves an unexecutable obligation fails by
    # name rather than by `continue`. `graded_path_reaches_the_network` proves the socket
    # guard. `grader_rejects_correct_answer_tree_wide` PAYS the `grading_contract_floor_10`
    # allowlist entry, which had stood unproven since 2026-09-08 only because a full sweep
    # cost 14m23s; hermetic, it costs 33s. Three of the six prove labels that now have two
    # mutations, so this floor is the only guard on those pairs.
    # 88 registered 2026-09-12 (was 85): +3 for the stage ledger (H-03). One lets a stage's
    # exception escape the boundary; one stops counting a never-entered stage as a failure;
    # one lets a CRASHED stage discard its own §-refs from the two-direction comparison, and
    # that third PAYS `two_direction_contract_match`, unproven since 2026-09-08.
    # 89 registered 2026-09-12 (was 88): +1 for `stage_runs_in_the_wrong_band`, which
    # proves the stage schedule is held to _manifest.CHECK_PHASE. That is the wrong-phase
    # path plan step 0A asks for; run_all's OTHER phase reconciliation (`misphased`) is
    # unreachable by construction and is recorded as a limitation instead.
    # 91 registered 2026-09-12 (was 89): +2 for §11, the obligation manifest.
    # `obligation_derivations_diverge` drops one production gate from one traversal only,
    # which is the failure the plan's own unreproducible 4,325 figure walked into.
    # `dead_formatter_route_ignored` registers a sixth unreachable route: §2B/§2C hold
    # advertised->servable, and nothing held registered->reachable until §11.
    "mutations": 91,
    # 983 observed 2026-09-08. How many (variant, value) pairs the blind-review packets
    # will actually demonstrate across the tree.
    #
    # This one guards a hole the OTHER direction from §2I. §2I caps unproducible
    # declarations from ABOVE, so a filter in _variant_coverage_candidates that drops too
    # much makes §2I report FEWER findings and look like progress. Measured: gutting two
    # applicability filters took candidates 983 -> 932 and §2I 21 -> 19, and
    # `validate_compat` still exited 0 printing "13/13 check groups passed".
    #
    # Three such filters were added on 2026-09-08 to clear 44 §2I findings; before that
    # there were none to gut. Narrowing what a check looks at is a legitimate fix and a
    # silent way to fake one, and only this floor tells them apart.
    #
    # Lower it deliberately, in the commit that removes a declaration and says which
    # competency clause does not name it -- e.g. dropping unit_type='cm' from three
    # "using non-standard units" nodes should lower this by exactly 6.
    # 983 -> 974 on 2026-09-08, lowered deliberately with the commit that removed the
    # declarations: 3 multi-DNA variants the node's effective bounds forbid outright, and
    # 6 standard-unit values on G1 nodes whose competencies read "using non-standard
    # units". Each removal cites the clause; the count moved by exactly the measured
    # amount, which is the point of stating it here.
    # 974 -> 964 on 2026-09-08, lowered deliberately with the commit that stopped the
    # packet builder declaring variants CURRICULUM_VARIANT_GATES already refuses at the
    # node's grade/quarter: 3x strategy=expanded_form (G1 Q1 nodes, gate G1 Q2),
    # task_type=associative (G1 Q2, gate G2 Q1), 4x number_type=multi_digit (G2 Q3, gate
    # G3 Q3), and draw_construct + recognize_model (G2 Q4, gate G3 Q1). Each clause is
    # quoted in validate_compat's _PRODUCIBLE_FLOOR note; the count moved by exactly the
    # measured 10, which is the point of stating it here.
    # 964 -> 975 on 2026-09-09, RAISED (a floor may always rise with the real number):
    # order_of_operations declared `number_size`, probability_experiment declared
    # `experiment_type`, and ordinal_numbers' task_type list went from two fictional
    # values to the four its templates actually implement plus the new
    # `describe_position`. Every one of those is a variant the review packets can now
    # demonstrate and could not before.
    "variant_candidates": 975,
}

# §8 inventory: the assertions this module can independently fail on. Derived from the
# floors rather than restated, so adding a floor adds an assertion that must then be
# proven by a mutation or excused in validate_coverage.UNPROVEN_ASSERTIONS -- a new floor
# nobody can breach on purpose is a floor nobody has checked.
ASSERTIONS = ("census",) + tuple(f"census_{key}" for key in CENSUS_FLOORS)


def count_nodes() -> int:
    from backend.app.practice_gen.registry import get_all_node_ids

    return len(get_all_node_ids())


def count_mutations() -> int:
    from tests.mutation_harness import MUTATIONS

    return len(MUTATIONS)


def count_variant_candidates() -> int:
    """(variant, value) pairs the review packets will demonstrate, tree-wide."""
    from backend.app.practice_gen.registry import get_all_node_ids

    from .judgment_packets import _variant_coverage_candidates

    return sum(len(_variant_coverage_candidates(n)) for n in get_all_node_ids())


def count_unit_tests() -> Optional[int]:
    """
    How many tests the fast suite would actually RUN, not how many exist.

    `--collect-only -q` after marker deselection is the honest number: a test that is
    collected but deselected does not gate, so counting the file's contents would let the
    suite hollow out while the census kept passing.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit", "-q", "--collect-only",
         "-p", "no:cacheprovider"],
        cwd=REPO_ROOT, capture_output=True, text=True,
        env={"PYTHONPATH": str(REPO_ROOT), "PATH": "/usr/bin:/bin"},
    )
    # "343/349 tests collected (6 deselected) in 1.20s" or "343 tests collected in 1.20s"
    m = re.search(r"(\d+)(?:/\d+)? tests? collected", proc.stdout)
    return int(m.group(1)) if m else None


def validate_census() -> List[str]:
    """Return one error per floor breached. Empty list means the suite is intact."""
    errors: List[str] = []

    observed = {}
    try:
        observed["nodes"] = count_nodes()
    except Exception as exc:  # noqa: BLE001 - naming the failure beats skipping the floor
        return [f"§7 census: node registry did not load ({exc}); the floor cannot be checked"]
    try:
        observed["mutations"] = count_mutations()
    except Exception as exc:  # noqa: BLE001
        return [f"§7 census: mutation harness did not import ({exc}); the floor cannot be checked"]

    try:
        observed["variant_candidates"] = count_variant_candidates()
    except Exception as exc:  # noqa: BLE001
        return [f"§7 census: variant candidates did not enumerate ({exc}); "
                f"the coverage floor cannot be checked"]

    n = count_unit_tests()
    if n is None:
        return ["§7 census: could not parse a test count from pytest --collect-only; "
                "the unit-test floor cannot be checked, so the suite is unmeasured"]
    observed["unit_tests"] = n

    for key, floor in CENSUS_FLOORS.items():
        got = observed[key]
        if got < floor:
            errors.append(
                f"§7 census: {key}={got} is below the floor of {floor}. The suite got "
                f"smaller — find what left before touching this number. Lowering the "
                f"floor to make this pass is the defect the floor exists to catch."
            )
    return errors


def validate_all() -> bool:
    errors = validate_census()
    if errors:
        print(f"  FAIL census ({len(errors)} floor(s) breached):")
        for e in errors:
            print(f"    - {e}")
        return False
    for key, floor in CENSUS_FLOORS.items():
        got = {"nodes": count_nodes, "mutations": count_mutations,
               "unit_tests": count_unit_tests,
               "variant_candidates": count_variant_candidates}[key]()
        print(f"  PASS census: {key}={got} (floor {floor})")
    return True


def main() -> int:
    return 0 if validate_all() else 1


if __name__ == "__main__":
    sys.exit(main())
