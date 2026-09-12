"""
Mutation harness — verify the verifier (pgen_hardening.md Phase 4).

The validation harness is the only thing standing between a broken generator and
production. Phase 4 exists because a harness that passes proves nothing until you
have proved it can *fail*: "Prove the harness catches bugs by planting them."

Prior sessions recorded Phase 4 as done with no runnable artifact — the claim was
inherited as prose, which is exactly what Ground Rule 1 forbids ("You do not get
to decide a check passed"). This module makes the claim re-executable.

Each mutation is a surgical find/replace against real pipeline source. For each:
apply it, run the validator that is supposed to notice, assert a non-zero exit,
and restore the file in a `finally` so an interrupted run cannot leave the tree
dirty. A mutation that survives is a hole in the harness, reported as such.

Usage:
    python -m tests.mutation_harness                  # all mutations
    python -m tests.mutation_harness --only leaky_window
    python -m tests.mutation_harness --list

Exit code 0 iff every mutation was detected.

WHAT A RUN LEAVES BEHIND (2026-09-12)
-------------------------------------
Until this date a run of this table left nothing on disk, so §8 could only count
mutations that had been WRITTEN, never mutations that had been RUN. `validate_coverage`'s
own docstring named that hole: a mutation that SURVIVED, or that this runner refused to
score as INVALID, still marked its label proven.

Every executed mutation now writes a machine-readable proof record to
`validation_reports/mutation_proofs/<name>.json` — baseline and planted exit statuses,
which expected markers were actually observed, the paths it edited, and three digests
binding it to the mutation definition and the working-tree bytes it ran against. §8 reads
those records instead of `Mutation.asserts`. See
`backend/app/practice_gen/validation/mutation_proof.py` for the schema and the verifier.

A proof is published only AFTER the tree is restored and the input digest is confirmed
unchanged, and the write is atomic, so an interrupted run leaves a rejected `.json.tmp`
rather than a half-record that reads as current.

`run_all` CONSUMES proofs and never invokes this module: a gate that can regenerate its
own evidence is not a gate.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.practice_gen.validation import mutation_proof  # noqa: E402

# Every subprocess runs the harness the same way CI does, from the repo root.
_ENV_PREFIX = [sys.executable, "-m"]


@dataclass
class Mutation:
    """One planted bug plus the command expected to catch it."""

    name: str
    description: str
    # file -> (exact text to find, replacement). All edits are applied together
    # and reverted together.
    edits: Dict[str, Tuple[str, str]]
    # Validator invocation (module path + args) expected to exit non-zero.
    command: List[str]
    # The spec check that should do the catching (for the report table).
    expected_check: str
    # Substrings that, if present in the output, confirm the failure points at
    # the planted bug rather than at unrelated noise. Empty = exit code only.
    # The assertion label(s) this mutation proves, e.g. ["empty_execution_matrix"].
    # `expected_check` is free text for humans; this is the machine-checkable link that
    # lets §8 state which assertions are proven. Without it "17 of 24 checks proven"
    # counts a REF as proven when one of its sub-assertions is -- and validate_matrix
    # alone emits 26 distinct assertion labels behind ~11 refs.
    asserts: List[str] = field(default_factory=list)
    expect_output_contains: List[str] = field(default_factory=list)
    # Substrings the *unmutated* tree must NOT already produce. Without this, a
    # mutation "passes" on a validator that was failing before it was applied --
    # which is precisely the state §5 and §6 are in while the honest work queue
    # is open, and precisely the false green Phase 4 exists to prevent.
    #
    # A marker containing " && " means "all of these parts on ONE line". A bare
    # substring is too coarse once several checks report on the same capability:
    # §6F's UNATTESTED finding names `count_forward_from_a_given_number`, which made
    # §6D's mutation undetectable-by-baseline even though §6D itself was working fine.
    # The conjunction restores the discrimination without loosening the guard.
    baseline_must_not_contain: List[str] = field(default_factory=list)
    # Some mutations cannot be written as a literal find/replace: a templated
    # review has to be planted across several report files whose prose differs
    # per node. Such a mutation supplies a callable that performs the edits and
    # returns {path: original_text} for the same `finally` restore.
    apply_fn: Optional[Callable[[], Dict[Path, str]]] = None




def _plant_vocab_leak(term: str) -> Dict[Path, str]:
    """
    Append a NOT_YET_KNOWN term to the stem fmt_mcq actually emits.

    The previous form of this mutation set `ctx.question_text` at the top of
    `format_mcq` and was a silent no-op for however long fmt_mcq has looked like
    this: the pure branch rebuilds the stem from `_build_pure_question(ctx)` and
    never reads that field, so the planted term was discarded before it could reach
    §1D. `validate_matrix --node mat_g1_na_q1_7` exited 0 with the bug applied, the
    mutation was scored as SURVIVED, and the vocabulary gate -- Content Rule 1 --
    had therefore never been demonstrated to work at all.

    Both branches are patched, and a missing anchor raises rather than skipping. A
    mutation that can quietly stop landing is worse than no mutation: it reports a
    hole in the harness that is really a hole in the test, and it hides whichever
    one is real.
    """
    path = REPO_ROOT / "backend/app/practice_gen/formatters/textual/fmt_mcq.py"
    text = path.read_text(encoding="utf-8")
    anchors = {
        # pure branch -- rebuilt from the DNA, so the term must be appended after the build
        "        question_text = _build_pure_question(ctx)\n":
            f"        question_text = _build_pure_question(ctx) + ' Use {term} to check.'\n",
        # word_problem branch -- carries ctx.question_text through
        "        question_text = ctx.question_text\n":
            f"        question_text = (ctx.question_text or '') + ' Use {term} to check.'\n",
    }
    mutated = text
    for anchor, replacement in anchors.items():
        if mutated.count(anchor) != 1:
            raise ValueError(
                f"mutation 'vocab_leak': anchor {anchor.strip()!r} matched "
                f"{mutated.count(anchor)} times in fmt_mcq.py, expected exactly 1. The "
                f"formatter moved; repoint the mutation at the line that actually "
                f"reaches FormattedProblem.question_text and re-prove §1D. Do NOT drop "
                f"the anchor -- an unlanded mutation scores SURVIVED and reads as a "
                f"broken vocabulary gate."
            )
        mutated = mutated.replace(anchor, replacement)
    path.write_text(mutated, encoding="utf-8")
    return {path: text}


def _plant_silent_substitution() -> Dict[Path, str]:
    """
    Disable BOTH redundant gates that refuse an unsupported variant/formatter pair.

    There are two, and they are genuinely redundant: `adapter.py` raises directly,
    and `orchestrator.py` marks the DNA incompatible, which surfaces as a raise from
    its forced-DNA check. Patching either one alone leaves the other refusing, `run()`
    still raises ValueError, and §1C-reverse -- which asks only "did requesting an
    excluded variant raise?" -- correctly sees a refusal and reports nothing. The
    mutation then scores SURVIVED and reads as a broken check when the check is fine.

    That is what happened here for as long as this mutation has existed. It patched
    only the orchestrator, on the theory that adapter's raise was "redundant" -- true,
    but redundancy is exactly why one-sided patching proves nothing.

    It was also pointed at mat_g1_na_q1_7, which does not execute §1C-reverse at all:
    the check only runs when a DNA has variant values its formatter excludes, and that
    node has none. A mutation aimed at a check the node never runs cannot be caught.
    mat_g1_na_q1_0 executes both §1C-reverse and §4.
    """
    targets = {
        REPO_ROOT / "backend/app/practice_gen/adapter.py": (
            "            if not is_variant_supported(dna_name, formatter, var_name, var_value):\n"
            "                raise ValueError(\n"
            "                    f\"generate_problem: variant {var_name}='{var_value}' is not supported \"\n"
            "                    f\"by formatter '{formatter}' for DNA '{dna_name}'.\"\n"
            "                )\n",
            "            pass  # planted mutation: silent substitution\n",
        ),
        REPO_ROOT / "backend/app/services/orchestrator.py": (
            "                        if not is_variant_supported(d, formatter, var_name, var_val):\n"
            "                            dna_compatible = False\n"
            "                            break\n",
            "                        pass  # planted mutation: silent substitution\n",
        ),
    }
    originals: Dict[Path, str] = {}
    for path, (anchor, replacement) in targets.items():
        text = path.read_text(encoding="utf-8")
        if text.count(anchor) != 1:
            for done, original in originals.items():
                done.write_text(original, encoding="utf-8")
            raise ValueError(
                f"mutation 'silent_substitution': anchor matched {text.count(anchor)} times "
                f"in {path.name}, expected exactly 1. BOTH gates must be disabled together or "
                f"the surviving one refuses and the mutation proves nothing. Repoint it; do "
                f"not drop the file."
            )
        originals[path] = text
        path.write_text(text.replace(anchor, replacement), encoding="utf-8")
    return originals


# ---------------------------------------------------------------------------------
# §5 plants (2026-09-10).
#
# §5 declared six assertions and exactly ONE (`judgment_rationale_skeleton_5`) had a
# mutation, so five could have been silently broken and the 696 findings on the tree
# would have looked identical either way. Every plant below lands in a review JSON under
# validation_reports/judgment/, because that is what §5 READS -- the lesson §6 paid for
# on 2026-09-09, when a plant plausibly placed in the source survived because
# `get_node_info` reads a build artifact instead.
#
# Each plant LOCATES its target by re-rendering rather than naming a node, so it cannot
# quietly stop landing when the tree moves (a mutation that does not land scores
# SURVIVED and reads as a broken gate). A precondition it cannot satisfy raises.
# ---------------------------------------------------------------------------------








# A capability id no node's `requires` names. `draw_lines` held exactly this shape on
# disk until 2026-09-10 -- a live registration orphaned by a rename -- so re-adding it
# reproduces the real defect rather than an invented one.
_ORPHAN_PROVIDER = "draw_lines"

# A node whose generated record carries a `cumulative_concepts` list to drift. The real
# drift found on 2026-09-10 spanned 18 nodes; one is enough to prove the comparison.
_STALE_GRAPH_NODE = "mat_g1_na_q3_6"

# A node whose `requires_ignore` the plant appends to. Pinned rather than scanned so the
# marker names one node and the baseline guard can discriminate.
_IGNORE_LOCK_NODE = "mat_g1_na_q1_2"

# The visual type whose React component the frontend-contract plant adds a read to.
# GridArea renders on real student-path seeds across several nodes, so a newly required
# key is actually reached by §9's sampling rather than sitting in an unrendered branch.
_FRONTEND_PLANT_KEY = "planted_contract_key"

# The three §6F fixtures below are PINNED to named nodes, not scanned for, and each
# raises loudly if its node stops satisfying the precondition. §6F's queue is red (220
# findings), so a scanned plant would land on a record that is already reported and the
# run would score INVALID on the baseline guard -- see Scaling Mandate 5. Every marker
# is a "<node> && <message>" conjunction for the same reason.
# Was mat_g2_na_q2_8 until 2026-09-10. The §5b alphabetic-pattern work shifted that
# node's rng stream, so its record went STALE ON THE STEM and §6F's stem branch fired
# before the option comparison could be reached -- the plant stopped reaching the code
# the validator runs, and the full-table run scored it SURVIVED while the check itself
# was fine (Scaling Mandate 2, second cause). `_require_fresh_sample` below now turns
# that into a loud, named failure instead of a silent survival. Repointed to a data
# node, whose content no current content work touches.
_ATTEST_UNADJUDICABLE_NODE = "mat_g2_na_q3_8"   # clean record, true_false on every seed




















# ---------------------------------------------------------------------------------
# §6 Phase 2 plants (2026-09-10).
# ---------------------------------------------------------------------------------








MUTATIONS: List[Mutation] = [
    Mutation(
        name="leaky_window",
        asserts=["window_containment"],
        description=(
            "Make the scalar->value map land ten ABOVE the maximum at t=1.0, so "
            "generation overshoots the competency ceiling. The mirror of "
            "boundary_off_by_one: that one proves §1A's 'must reach the maximum', this "
            "one proves §1B's 'must never exceed it'."
        ),
        # Previously this widened addition.py's sum filter (`a + b > max_result` ->
        # `+ 10`) and was a silent no-op: the generator is TARGET-driven, not
        # rejection-driven, so selection aims at the competency target and never picks
        # the extra pairs a wider filter admits. Widening `a_hi` as well changed nothing
        # for the same reason -- measured, 100 seeds, max sum stayed exactly 20 against a
        # ceiling of 20. A mutation that cannot breach cannot prove containment, and this
        # one scored SURVIVED for as long as it existed, reading as a broken §1A/§1B.
        # Corrupting the target is the only thing that actually overshoots: 36 breaches
        # in 60 seeds, sums to 30 against a ceiling of 20.
        edits={
            "backend/app/services/orchestrator.py": (
                '                    local_difficulty_profile[axis["name"]] = mapped_val\n',
                '                    if val >= 1.0 and isinstance(mapped_val, int):\n'
                '                        mapped_val = mapped_val + 10\n'
                '                    local_difficulty_profile[axis["name"]] = mapped_val\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_7"],
        expected_check="§1A/§1B (scalar boundary exactness / window containment)",
        expect_output_contains=["window_containment && exceeds ceiling"],
        baseline_must_not_contain=["exceeds ceiling"],
    ),
    Mutation(
        name="boundary_off_by_one",
        asserts=["scalar_exactness_1.0"],
        description="Make the scalar->value map land one below the maximum at t=1.0.",
        # Patch the orchestrator's scalar->value mapping, which is what actually
        # governs continuous axes on the serving path. dna/base.py's
        # interpolate()/log_interpolate() implement the same formula but are not
        # on this path, so mutating them changed nothing and the "mutation"
        # proved nothing about the harness. (That the formula exists in three
        # places at all is a doc_rem R2 violation, noted in IMPLEMENTATION_STATUS.)
        edits={
            "backend/app/services/orchestrator.py": (
                '                    local_difficulty_profile[axis["name"]] = mapped_val\n',
                '                    if val >= 1.0 and isinstance(mapped_val, int):\n'
                '                        mapped_val = mapped_val - 1\n'
                '                    local_difficulty_profile[axis["name"]] = mapped_val\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_7"],
        expected_check="§1A (maximum never reached at scalar 1.0)",
    ),
    Mutation(
        name="broken_formatter_combo",
        asserts=['pipeline_run'],
        description="Make the MCQ formatter raise for a variant value it claims to support.",
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                "    correct = ctx.correct_answer\n",
                "    correct = ctx.correct_answer\n"
                "    if (ctx.given_values or {}).get('operation') == 'add':\n"
                "        raise RuntimeError('planted mutation: mcq refuses addition')\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_7"],
        expected_check="§1C (variant x formatter execution matrix)",
    ),
    Mutation(
        name="answer_corruption",
        asserts=['answer_key_integrity'],
        description="Off-by-one the correct answer the MCQ formatter serves.",
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                # Anchored to line start. fmt_mcq gained a second FormattedProblem
                # return at a deeper indent, and a bare 8-space anchor is a substring
                # of the 12-space line, so the literal matched twice and _apply
                # aborted -- taking mutations 4..12 with it. The leading newline
                # tightens the anchor; it does not loosen the mutation.
                #
                # REPOINTED 2026-09-11: the served field became `correct_answer=correct`
                # when compare_pair's MCQ presentation started offering whole comparison
                # statements (`correct` is `ctx.correct_answer` on every other path). The
                # full table caught the stale anchor and REFUSED to run rather than
                # scoring a plant it never applied -- which is the whole reason a
                # `--only` run cannot stand in for the full one after content work.
                "\n        correct_answer=correct,\n",
                "\n        correct_answer=(correct + 1)\n"
                "        if isinstance(correct, int) and not isinstance(correct, bool)\n"
                "        else correct,\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_7"],
        expected_check="§1E (answer-key integrity)",
    ),
    Mutation(
        name="vocab_leak",
        asserts=['vocabulary_gating'],
        description=(
            "Append a NOT_YET_KNOWN term ('multiplication', forbidden on a G1 addition "
            "node) to the stem fmt_mcq actually emits. Content Rule 1 is the rule that "
            "stops a grade's items using a later grade's vocabulary, and §1D is the only "
            "machine check that enforces it."
        ),
        edits={},
        apply_fn=lambda: _plant_vocab_leak("multiplication"),
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_7"],
        expected_check="§1D (vocabulary lint on formatted output)",
        # Exit code alone is not proof: name the term and the check together on one line.
        expect_output_contains=["NOT_YET_KNOWN && multiplication"],
        baseline_must_not_contain=["NOT_YET_KNOWN && multiplication"],
    ),
    Mutation(
        name="silent_substitution",
        asserts=['reverse_compatibility_check'],
        description=(
            "Disable both redundant gates so an unsupported variant/formatter pair is "
            "accepted silently instead of raising. A pipeline that substitutes rather "
            "than refuses will serve a later grade content its formatter cannot render."
        ),
        edits={},
        apply_fn=lambda: _plant_silent_substitution(),
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§1C-reverse (excluded combinations must raise)",
        expect_output_contains=["reverse_compatibility_check && did not raise an error"],
        baseline_must_not_contain=["did not raise an error"],
    ),
    Mutation(
        name="registry_drift",
        asserts=["compatibility_table"],
        description="Add a DNA concept to COMPATIBILITY with no module behind it.",
        edits={
            "backend/app/practice_gen/compatibility.py": (
                "COMPATIBILITY: Dict[str, List[str]] = {\n",
                "COMPATIBILITY: Dict[str, List[str]] = {\n"
                '    "planted_phantom_dna": ["mcq"],\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_compat"],
        expected_check="_manifest.py import-time registry assertion",
        expect_output_contains=["planted_phantom_dna"],
    ),
    # ------------------------------------------------------------------------
    # §5 and §6 — the two stages that have actually been defeated.
    #
    # The seven mutations above cover the machine stages (§1A-§1F, §2, §3), none
    # of which has ever been faked. §5 was defeated twice by fabricated reviews
    # and §6 once by a provider table where a generic formatter satisfied every
    # clause, and the harness planted nothing for either. A green mutation run
    # said the boundary/formatter/vocab checks work; it said nothing about the
    # checks that had failed three times between them.
    # ------------------------------------------------------------------------
    Mutation(
        name="wildcard_provider",
        asserts=['capability_generic_formatter_6D'],
        description=(
            "Replace a capability's real, discriminating provider with the generic "
            "textual formatter family -- the exact shape that neutralised §6C in "
            "August 2026, when 474 of 485 entries listed mcq/cloze/true_false/"
            "error_detect and every clause was satisfied by text."
        ),
        edits={},
        apply_fn=lambda: _plant_wildcard_provider("count_forward_from_a_given_number"),
        command=["backend.app.practice_gen.validation.validate_capability"],
        expected_check="§6D (a generic textual formatter is not a provider)",
        # Must name the capability AND cite §6D: exiting non-zero is not proof
        # while the honest §6D queue is open.
        expect_output_contains=["count_forward_from_a_given_number && §6D"],
        baseline_must_not_contain=["count_forward_from_a_given_number && §6D"],
    ),
    Mutation(
        name="contradicted_attestation",
        asserts=['capability_contradicted_6F'],
        description=(
            "Re-register a capability a blind Attester already ruled NOT_PROVIDED -- the "
            "regression §6F exists to stop. Until 2026-08-20 an Attester verdict took "
            "effect only if the Fixer chose to act on it, which is the same "
            "author-verifying-itself structure the role was created to break."
        ),
        edits={},
        apply_fn=lambda: _plant_contradicted_entry("draw_line_relationships"),
        command=["backend.app.practice_gen.validation.validate_capability"],
        expected_check="§6F (blind Attester verdict contradicted by the table)",
        expect_output_contains=["CONTRADICTED && draw_line_relationships"],
        baseline_must_not_contain=["CONTRADICTED && draw_line_relationships"],
    ),
    Mutation(
        name="orphan_provider",
        asserts=['capability_orphan_provider_6A'],
        description=(
            "Register a capability no node requires. Every §6 check is driven by a "
            "node's `requires`, so nothing read such an entry at all -- it was never "
            "attested, never contradicted and never provision-checked, while standing "
            "ready to pre-approve the first future node whose competency extracts that "
            "id, with no Attester having seen a rendered sample of it."
        ),
        edits={},
        apply_fn=lambda: _plant_orphan_provider(),
        command=["backend.app.practice_gen.validation.validate_capability", "--phase", "1"],
        expected_check="§6A (a provider entry no requirement reaches)",
        expect_output_contains=[f"{_ORPHAN_PROVIDER} && but no node's `requires` names it"],
        baseline_must_not_contain=[f"{_ORPHAN_PROVIDER} && but no node's `requires` names it"],
    ),
    Mutation(
        name="stale_attestation",
        asserts=['capability_stale_attestation_6F'],
        description=(
            "Drift the content an Attester judged, leaving the verdict on file. Without a "
            "freshness pass the contract has a permanent hole: attest everything once, "
            "then change generators freely, and run_all keeps exiting 0 on evidence about "
            "content that no longer exists."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'attestation_stale'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "attestation"],
        expected_check="§6F freshness (attestation is about content that still exists)",
        expect_output_contains=["isolated_plant_attestation", 'is STALE (§6F) at seed'],
        baseline_must_not_contain=["isolated_plant_attestation", "FAIL isolated_control_attestation"],
    ),
    Mutation(
        name="attestation_answer_drift",
        asserts=['capability_stale_attestation_6F'],
        description=(
            "Move the answer an attestation was filed against while its stem stays "
            "byte-identical. Until 2026-09-10 §6F compared the stem and nothing else, so "
            "a capability verdict outlived the answer changing under it -- the drift "
            "shape §5 has expired reviews for since `stale_answer_same_key`."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'attestation_answer_drift'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "attestation"],
        expected_check="§6F freshness (the keyed value, not just the stem)",
        expect_output_contains=["isolated_plant_attestation", 'no longer keys the same answer'],
        baseline_must_not_contain=["isolated_plant_attestation", "FAIL isolated_control_attestation"],
    ),
    Mutation(
        name="attestation_option_drift",
        asserts=['capability_stale_attestation_6F'],
        description=(
            "Move one offered distractor under an unchanged stem and key, and separately "
            "turn a non-choice item into a choice item -- the two branches of §6F's "
            "option comparison, planted together so one run says whether both fire. The "
            "Attester is shown the option list under every sample, so its verdict rests "
            "on options §6F did not compare at all before 2026-09-10."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'attestation_option_drift'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "attestation"],
        expected_check="§6F freshness (the offered options, as §5 compares them)",
        expect_output_contains=["isolated_plant_attestation", 'no longer offered the same options'],
        baseline_must_not_contain=["isolated_plant_attestation", "FAIL isolated_control_attestation"],
    ),
    Mutation(
        name="attestation_drops_options",
        asserts=['capability_attestation_options_recorded_6F'],
        description=(
            "Make a formatter start emitting an option table on a node whose filed "
            "attestation carries none -- the exact state 137 of 151 live records were "
            "found in, because the record skeleton in tests/attester_packets.py copied "
            "four fields and dropped the `options` the Attester was actually shown. "
            "Planted in the GENERATOR rather than the record because that is how the "
            "state arises: a record cannot be repaired into carrying options it never "
            "recorded, so the only honest signal is the live render growing them."
        ),
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_true_false.py": (
                '    format_data = {\n'
                '        "statement": statement,\n'
                '        "is_true": is_true,\n'
                '        "correct_answer": is_true,\n'
                '    }\n',
                '    format_data = {\n'
                '        "statement": statement,\n'
                '        "is_true": is_true,\n'
                '        "correct_answer": is_true,\n'
                '        "options": [\n'
                '            {"key": "A", "value": True, "is_correct": is_true},\n'
                '            {"key": "B", "value": False, "is_correct": not is_true},\n'
                '        ],\n'
                '    }\n',
            ),
        },
        command=["backend.app.practice_gen.validation.validate_capability"],
        expected_check="§6F adjudicability (an attestation must carry the choices it was shown)",
        expect_output_contains=[
            f"{_ATTEST_UNADJUDICABLE_NODE} && records no 'options' at seed"],
        baseline_must_not_contain=[
            f"{_ATTEST_UNADJUDICABLE_NODE} && records no 'options' at seed"],
    ),
    Mutation(
        name="template_review",
        asserts=['judgment_rationale_skeleton_5'],
        description=(
            "Staple one fill-in-the-blank rationale, with the node ID substituted "
            "in, onto four separate reviews -- the fabrication that passed every "
            "check this repo had, twice, because verbatim-reuse detection compares "
            "byte equality and a substituted node ID is not byte-identical."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'template_skeleton'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "judgment"],
        expected_check="§5 (rationale-skeleton clustering)",
        expect_output_contains=["isolated_plant_judgment", 'template rationale:'],
        baseline_must_not_contain=["isolated_plant_judgment", "FAIL isolated_control_judgment"],
    ),
    # ------------------------------------------------------------------------
    # §5's other five assertions (2026-09-10), plus the sixth added with them.
    #
    # Every §5 command below runs with `--all`. §5's CLI prints the first 40 findings by
    # default, and while the re-review queue is open it reports hundreds -- a planted
    # violation that lands past the cut is scored SURVIVED, which reports a hole in the
    # harness where the hole is really in the test (Scaling Mandate 2). `--all` is display
    # only; the error set, the count and the exit code are identical either way, and the
    # `baseline_must_not_contain` probe then runs against the WHOLE corpus rather than
    # its first 40 lines.
    # ------------------------------------------------------------------------
    Mutation(
        name="stale_review_undetected",
        asserts=['judgment_review_freshness_5'],
        description=(
            "Rewrite a CURRENTLY-FRESH sample's recorded stem so it no longer matches "
            "what the pipeline renders. Freshness is what makes a review expire rather "
            "than become a checkbox, it produces 512 of §5's findings on this tree, and "
            "until now nothing had shown it firing."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'stale_stem'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "judgment"],
        expected_check="§5 freshness (a review may not outlive the content it judged)",
        expect_output_contains=["isolated_plant_judgment", 'no longer renders the content that was judged'],
        baseline_must_not_contain=["isolated_plant_judgment", "FAIL isolated_control_judgment"],
    ),
    Mutation(
        name="stale_answer_same_key",
        asserts=['judgment_review_freshness_5'],
        description=(
            "Move the correct value onto a distractor that was ALREADY offered, keeping "
            "the stem, the option multiset and the A-D key byte-identical. Until "
            "2026-09-10 the answer comparison read the raw `correct_answer` field, which "
            "is a KEY on the 59 read_mcq nodes, so this drift passed every §5 gate."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'stale_answer_same_key'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "judgment"],
        expected_check="§5 freshness (the keyed VALUE, not the slot it landed in)",
        expect_output_contains=["isolated_plant_judgment", 'no longer keys the same answer'],
        baseline_must_not_contain=["isolated_plant_judgment", "FAIL isolated_control_judgment"],
    ),
    Mutation(
        name="review_schema_incomplete",
        asserts=['judgment_review_schema_5'],
        description=(
            "Delete a required finding from a review and cut its seed list below the "
            "distinct-seed quorum -- two independent branches of the schema gate, so one "
            "run says whether both still fire."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'schema_incomplete'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "judgment"],
        expected_check="§5 schema (seeds, samples, six findings, verdicts)",
        expect_output_contains=["isolated_plant_judgment", 'findings missing required items'],
        baseline_must_not_contain=["isolated_plant_judgment", "FAIL isolated_control_judgment"],
    ),
    Mutation(
        name="fabricated_quote",
        asserts=['judgment_quote_provenance_5'],
        description=(
            "Quote, in a rationale, a span that appears nowhere in that review's own "
            "packet or competency text -- the mechanism by which 115 of 151 fabricated "
            "reviews cited stems they were never shown."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'fabricated_quote'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "judgment"],
        expected_check="§5 quote provenance (a rationale may only cite what it was shown)",
        expect_output_contains=["isolated_plant_judgment", "appears nowhere in this review's own samples_reviewed"],
        baseline_must_not_contain=["isolated_plant_judgment", "FAIL isolated_control_judgment"],
    ),
    Mutation(
        name="verbatim_rationale_reuse",
        asserts=['judgment_rationale_verbatim_5'],
        description=(
            "Copy one node's rationale byte-for-byte onto another node's same finding. "
            "The donor is chosen quote-free so the copy trips verbatim reuse ALONE -- a "
            "mutation that fires two gates cannot say which one it proved."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'verbatim_rationale'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "judgment"],
        expected_check="§5 verbatim rationale reuse across nodes",
        expect_output_contains=["isolated_plant_judgment", 'is copied verbatim from'],
        baseline_must_not_contain=["isolated_plant_judgment", "FAIL isolated_control_judgment"],
    ),
    Mutation(
        name="single_reviewer_identity",
        asserts=['judgment_reviewer_plurality_5'],
        description=(
            "Stamp one `reviewed_by` identity across more nodes than a blind batch may "
            "hold. §6H's twin has been proven since 2026-08-28; §5's original was not, "
            "so the older of the two plurality gates was the unproven one."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'single_reviewer'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "judgment"],
        expected_check="§5 reviewer plurality (one identity may not span the tree)",
        expect_output_contains=["isolated_plant_judgment", 'reviewer plurality:'],
        baseline_must_not_contain=["isolated_plant_judgment", "FAIL isolated_control_judgment"],
    ),
    Mutation(
        name="mcq_reviewed_without_options",
        asserts=['judgment_options_recorded_5'],
        description=(
            "Delete the recorded options from a sample whose live render still offers "
            "some. Until 2026-09-10 that was a silent skip -- 505 of 2026 recorded "
            "samples were in that state, with the option comparison switched off and, on "
            "read_mcq, the answer unresolvable, and nothing said so."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'options_dropped'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "judgment"],
        expected_check="§5 option adjudicability (a choice item must carry its choices)",
        expect_output_contains=["isolated_plant_judgment", "records no 'options'"],
        baseline_must_not_contain=["isolated_plant_judgment", "FAIL isolated_control_judgment"],
    ),
    # ------------------------------------------------------------------------
    # The §6 phase seam (2026-09-08). §6A-§6E need no agent-authored artifact and
    # run in Phase 1; §6F-§6H read validation_reports/attestation/ and run in
    # Phase 2. Both halves lived in one function until this split, so 75 findings
    # that compute in 0.1s sat in a backlog that costs 9.9s to recompute. A seam
    # held only by a docstring is a convention; these two mutations are what make
    # it a contract.
    # ------------------------------------------------------------------------
    Mutation(
        name="attestation_leaks_into_phase1",
        asserts=['capability_phase_boundary_6'],
        description=(
            "Read the attestation corpus from the Phase 1 (artifact-free) half -- the "
            "one-line convenience that would silently make the fast band unrunnable "
            "without an agent-authored artifact on disk, while still exiting 0."
        ),
        edits={
            "backend/app/practice_gen/validation/validate_capability.py": (
                "    rows, errs = _declared_nodes(node_ids)\n"
                "    for node_id, competency, requires, ignore in rows:\n"
                "        errs += _validate_provenance(node_id, competency, requires)",
                "    rows, errs = _declared_nodes(node_ids)\n"
                "    _leaked = _load_attestations()\n"
                "    for node_id, competency, requires, ignore in rows:\n"
                "        errs += _validate_attestation(node_id, requires, _leaked)\n"
                "        errs += _validate_provenance(node_id, competency, requires)",
            )
        },
        command=["backend.app.practice_gen.validation.validate_capability"],
        expected_check="§6 phase boundary (Phase 1 must run with the attestation corpus absent)",
        expect_output_contains=["capability_phase_boundary_6 && is not"],
        baseline_must_not_contain=["capability_phase_boundary_6"],
    ),
    Mutation(
        name="phase_ref_misassigned",
        asserts=['capability_phase_partition_6'],
        description=(
            "Relabel §6D as Phase 2 while `_validate_provision` keeps reporting it from "
            "the Phase 1 half. Registry and execution disagreeing is how a check's cost "
            "moves between bands without anyone deciding to move it -- the state §6 was "
            "already in, with six refs added on one boolean."
        ),
        edits={
            # Repointed 2026-09-09: CHECK_PHASE moved to _manifest when the seam was
            # applied harness-wide (§5 is Phase 2 for the same reason §6F is), and
            # validate_capability now derives its §6 slice from there.
            "backend/app/practice_gen/validation/_manifest.py": (
                '"§6C": 1, "§6D": 1, "§6E": 1,',
                '"§6C": 1, "§6D": 2, "§6E": 1,',
            )
        },
        command=["backend.app.practice_gen.validation.validate_capability"],
        expected_check="§6 per-phase reconciliation (a finding may only cite refs of its own phase)",
        expect_output_contains=["capability_phase_partition_6 && §6D"],
        baseline_must_not_contain=["capability_phase_partition_6"],
    ),
    Mutation(
        name="template_attestation",
        asserts=['attester_reasoning_skeleton_6G'],
        description=(
            "Staple one fill-in-the-blank reasoning, with the clause substituted in, "
            "onto four live Attester verdicts. §6F passes it untouched -- the packet is "
            "unchanged so freshness holds, the verdicts exist, nothing contradicts them. "
            "This is the §5 fabrication aimed at a surface four times larger (787 "
            "verdicts against 151 reviews), dispatched in unattended batches nobody reads."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'attester_template'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "attestation"],
        expected_check="§6G (attester reasoning-skeleton clustering)",
        expect_output_contains=["isolated_plant_attestation", 'attester boilerplate (§6G)'],
        baseline_must_not_contain=["isolated_plant_attestation", "FAIL isolated_control_attestation"],
    ),
    # ---------------------------------------------------------------------------
    # 2026-08-26: the four checks below were registered and binding but had no
    # mutation, so nothing had ever shown them failing. §1C-coverage in particular
    # is the check that caught mat_g3_na_q3_1 -- a node whose execution matrix is
    # empty, which renders no problems at all and would otherwise report PASS. The
    # harness's single most valuable catch was made by an unproven check.
    # ---------------------------------------------------------------------------
    Mutation(
        name="empty_execution_matrix",
        asserts=['empty_execution_matrix'],
        description=(
            "Rename the two task_type values mat_g1_na_q1_9's competency binds, so no "
            "variant combination survives filtering. This is the live shape of "
            "mat_g3_na_q3_1: a competency naming task_types the DNA does not support, "
            "leaving a node that generates nothing while every per-problem check "
            "vacuously passes -- there are no problems to fail on."
        ),
        edits={
            "backend/app/practice_gen/compatibility.py": (
                '            "expanded_form", "counting_up", "putting_together",\n',
                '            "expanded_form", "counting_up_PLANTED", "putting_together_PLANTED",\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_9"],
        expected_check="§1C-coverage (every node/DNA/formatter has a non-empty execution matrix)",
        expect_output_contains=["empty_execution_matrix"],
        baseline_must_not_contain=["empty_execution_matrix"],
    ),
    Mutation(
        name="answer_leak_in_stem",
        asserts=['answer_leak_in_stem'],
        description=(
            "Reduce the stem to the answer itself, so the student need only copy it -- "
            "'Jose has lunch at 1:30. What time is that?'. "
            "SCOPE, verified by instrumenting the rendered path rather than reading the "
            "validator: §1F fires ONLY when the answer is the stem's sole numeric datum. "
            "An earlier version of this mutation appended 'It is 70.' to a counting stem "
            "('66, 67, 68, 69, ___? It is 70.') and SURVIVED -- the stem carried five "
            "numbers, so the check declined it by design. That narrowing is deliberate "
            "(conflating it with degenerate-operand items fired on 3,702 well-formed "
            "identity facts), but it means §1F does NOT catch a leak in a stem that "
            "carries any other number. That blind spot was real; it is CLOSED as of "
            "2026-08-28 by a second, independent path (see stem_declares_the_answer) "
            "that asks whether the stem DECLARES the answer rather than merely "
            "contains it. This mutation still pins the narrow form, which must keep "
            "working on its own."
        ),
        # Planted in `mcq`, not `numeric_input`: the first attempt targeted
        # fmt_numeric_input and SURVIVED, because no node under test advertises that
        # formatter -- the mutation never reached the code §1F executes. That is the
        # second cause of a surviving mutation (a moved/unreachable anchor), not a
        # broken check, and the fix is to land it on the executed path.
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                "        question_text = _build_pure_question(ctx)\n",
                "        question_text = f\"The answer is {ctx.correct_answer}. What is it?\"\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§1F (question stem does not leak its own answer)",
        expect_output_contains=["answer_leak_in_stem"],
        baseline_must_not_contain=["answer_leak_in_stem"],
    ),
    Mutation(
        name="inverted_number_line",
        asserts=['visual_payload'],
        description=(
            "Swap a number line's start and end so the axis runs backwards. Every other "
            "stage reads TEXT: the stem still says 'what number is marked?' and reads "
            "perfectly, while the picture the student is shown is incoherent. §1G is the "
            "only check that looks at visual_params at all, across the 71 of 151 nodes "
            "that render one."
        ),
        edits={},
        apply_fn=lambda: _invert_number_line_axis(),
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§1G (rendered visual payload is real and self-consistent)",
        expect_output_contains=["visual_payload", "is not below end"],
        baseline_must_not_contain=["is not below end"],
    ),
    Mutation(
        name="unservable_advertised_formatter",
        asserts=['advertised_formatters_are_servable'],
        description=(
            "Make the orchestrator refuse `true_false` for every node while still serving "
            "the rest. get_node_formatters() unions COMPATIBILITY across a node's DNAs "
            "with no per-node narrowing, so the node keeps advertising a formatter that "
            "cannot be served -- and the Lab builds its menu from that list."
        ),
        edits={
            "backend/app/services/orchestrator.py": (
                "        if not valid_dnas:\n"
                "            raise ValueError(f\"Formatter '{formatter}' is not supported by any DNA for node '{node_id}'\")",
                "        if formatter == 'true_false':\n"
                "            valid_dnas = []  # planted mutation: refuse one advertised formatter\n"
                "        if not valid_dnas:\n"
                "            raise ValueError(f\"Formatter '{formatter}' is not supported by any DNA for node '{node_id}'\")",
            )
        },
        command=["backend.app.practice_gen.validation.validate_compat", "--only", "servable"],
        expected_check="§2B (every formatter a node advertises can actually be served)",
        expect_output_contains=["advertises formatter 'true_false'"],
        baseline_must_not_contain=["advertises formatter 'true_false'"],
    ),
    Mutation(
        name="node_dropped_from_check",
        asserts=['per_node_applicability_1H'],
        description=(
            "Stop §1A recording itself on one node while that node's axes still make it "
            "applicable. This is the only mutation that perturbs the harness rather than "
            "the pipeline, because §1H's subject IS the harness's own per-node coverage: "
            "the defect it guards is a check that quietly stops reaching nodes. Before "
            "§1H existed, run_all only unioned executed checks across all 151 nodes, so "
            "one node exercising §1A satisfied the suite and the other 150 could skip it "
            "in silence."
        ),
        edits={
            "backend/app/practice_gen/validation/validate_matrix.py": (
                '            if axis_name != "number_difficulty":\n'
                '                executed.add("§1A")\n',
                '            if axis_name != "number_difficulty":\n'
                '                if node_id != "mat_g1_na_q1_0":  # planted mutation\n'
                '                    executed.add("§1A")\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§1H (every check a node's composition makes applicable ran on that node)",
        expect_output_contains=["§1H applicability", "mat_g1_na_q1_0"],
        baseline_must_not_contain=["§1H applicability — the node's own composition"],
    ),
    Mutation(
        name="shrinking_node_registry",
        asserts=["census", "census_nodes"],
        description=(
            "Drop every node after the first ten from the registry. Every stage then "
            "checks ten nodes, finds nothing wrong with them, and the suite reports green "
            "on 7% of the tree. Nothing asserted the suite's own size until §7: a total "
            "wipe is caught (pytest exits 5 on an empty collection) but silent shrinkage "
            "was not, in nodes, unit tests, or mutations."
        ),
        edits={
            "backend/app/practice_gen/registry.py": (
                "    result: List[str] = []\n"
                "    for node_id in NODE_TO_DNA:\n",
                "    result: List[str] = []\n"
                "    for node_id in list(NODE_TO_DNA)[:10]:  # planted mutation\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_census"],
        expected_check="§7 (the suite's own census has not shrunk below its floor)",
        expect_output_contains=["census", "is below the floor"],
        baseline_must_not_contain=["is below the floor"],
    ),
    Mutation(
        name="degenerate_answer_key",
        asserts=['degenerate_answer_key'],
        description=(
            "Key every multiplication-property statement True, which is exactly how "
            "mat_g3_na_q3_1 shipped: 180 of 180 sampled items across the commutative, "
            "associative and distributive task types were True, so a pupil answering "
            "'yes' every time scored 100% without applying any property. §1E checks the "
            "key survives formatting; nothing checked the key was worth having."
        ),
        edits={
            "backend/app/practice_gen/dna/na/multiplication.py": (
                "        holds = rng.random() < 0.5\n",
                "        holds = True  # planted mutation: never generate a false statement\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g3_na_q3_1"],
        expected_check="§1I (a true/false item family may not key every sample the same way)",
        expect_output_contains=["degenerate_answer_key", "scores 100%"],
        baseline_must_not_contain=["degenerate_answer_key"],
    ),
    Mutation(
        name="config_bypasses_competency",
        asserts=['config_respects_competency'],
        description=(
            "Remove the §2D refusal so a saved Lab configuration is applied unchecked -- "
            "the state the orchestrator was in until 2026-08-27, when offering "
            "task_type='two_step' on mat_g3_na_q3_1 served 'What is 40 x 10?' against a "
            "competency binding four property types with max_product=90, and the same "
            "route put NOT_YET_KNOWN vocabulary ('737 is 7 hundreds...') into Grade 1. "
            "Every §1A/§1B/§1D bound is enforced on the pipeline path; this one routes "
            "around all of them."
        ),
        edits={
            "backend/app/services/orchestrator.py": (
                "                permitted = _competency_allows(dim, opts)\n",
                "                permitted = list(opts)  # planted mutation: skip the competency gate\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_compat", "--only", "config"],
        expected_check="§2D (a saved configuration may not serve content outside a node's competency)",
        expect_output_contains=["config_respects_competency", "bypassing curriculum gating"],
        baseline_must_not_contain=["bypassing curriculum gating"],
    ),
    Mutation(
        name="unrenderable_visual_payload",
        asserts=['render_contract_9'],
        description=(
            "Drop `total_value` from the PlaceValueBlocks payload -- a key the React "
            "component reads. It collapses to `undefined` and the block diagram renders "
            "wrong or empty, while every stage that reads TEXT reports PASS. This is the "
            "class the frontend auditor was written for (Bug #56 empty visual, #58 dot at "
            "0 on the number line) and which no gate covered until §9: the auditor was "
            "referenced by zero gates and had been holding 12 critical findings across 4 "
            "nodes -- ClockSet, Calendar, and the FractionModel total_wholes collapse "
            "that is Bug #57."
        ),
        # Planted at the FINAL payload, not at the internal dict. Removing it upstream
        # makes the formatter raise KeyError on its own downstream read -- a crash, which
        # is another stage's finding, not §9's. §9 is about a payload that is BUILT and
        # SERVED while missing a key the component reads.
        #
        # REPOINTED 2026-09-11 for the same reason as `visual_payload_drops_required_key`
        # (see its note): the old plant dropped `total_value` from PlaceValueBlocks, and
        # `PlaceValueBlocksInteractive` reads no such key -- it destructures thousands /
        # hundreds / tens / ones, each with its own default, so the DERIVED contract for
        # that visual type is `required: []` and §9 can enforce nothing on it at all. The
        # mutation survived in the pristine tree at 950bc9a8. GridArea's `shaded` is a
        # bare read in the component and is not required by GridAreaParams, which is the
        # combination §9 exists for; `mat_g2_na_q3_4` serves that payload on the student
        # path at two of §9's three seeds.
        edits={
            "backend/app/practice_gen/formatters/visual/fmt_array_grid.py": (
                '    format_data: dict = {"visual_params": vp}\n',
                '    vp = {k: v for k, v in vp.items() if k != "shaded"}  # planted mutation\n'
                '    format_data: dict = {"visual_params": vp}\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_render",
                 "--node-ids", "mat_g2_na_q3_4"],
        expected_check="§9 (the payload must be renderable by the component the student sees)",
        expect_output_contains=["FAIL render_contract", "shaded"],
        baseline_must_not_contain=["FAIL render_contract"],
    ),
    Mutation(
        name="grader_rejects_correct_answer",
        asserts=['grading_contract_10'],
        description=(
            "Make the Lab v1 grader reject every submission. This is the worst defect "
            "class the system can have -- a pupil does the mathematics right and is told "
            "they are wrong -- and it had no gate until §10. The auditor written for it "
            "(Bug #002 fraction_shade portal=False vs v1/v2=True, #003 cloze, #004 mcq "
            "leniency) was referenced by zero gates. The live baseline is 5 real "
            "mis-gradings: list/ordering answers that lab_v2 accepts and portal+lab_v1 "
            "both reject, plus one time answer."
        ),
        edits={
            "backend/app/routes/matatag_router.py": (
                "    return {\n"
                '        "is_correct": is_correct,\n'
                '        "correct_answer": correct_answer_str,\n'
                '        "trap_triggered": trap_triggered,\n',
                "    return {\n"
                '        "is_correct": False,  # planted mutation: reject every answer\n'
                '        "correct_answer": correct_answer_str,\n'
                '        "trap_triggered": trap_triggered,\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_grade",
                 "--node-ids", "mat_g1_na_q1_0"],
        expected_check="§10 (a known-correct answer must be graded correct by all three graders)",
        expect_output_contains=["FAIL grading_contract", "told they are wrong"],
        baseline_must_not_contain=["FAIL grading_contract"],
    ),
    Mutation(
        name="predictable_option_placement",
        asserts=['option_placement'],
        description=(
            "Revert the option shuffle to the shared per-problem rng stream. Every "
            "formatter still calls shuffle, and each node's own ordering still looks "
            "random -- but the stream is at the same state on every node, so one seed "
            "puts the correct option in the same slot tree-wide. Measured before the fix: "
            "slot 1 on 93% of nodes at seed 11, slot 3 on 86% at seed 64. A pupil scores "
            "~90% on a practice set by always picking that position. No per-node check "
            "can see this; it is only visible across nodes."
        ),
        edits={
            "backend/app/practice_gen/formatters/_option_order.py": (
                '    option_rng(node_id, seed, salt).shuffle(items)\n',
                '    random.Random(seed).shuffle(items)  # planted mutation: shared stream\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_compat", "--only", "placement"],
        expected_check="§2E (the correct option's position must not be predictable from the seed)",
        expect_output_contains=["FAIL option_placement", "without doing any mathematics"],
        baseline_must_not_contain=["FAIL option_placement"],
    ),
    Mutation(
        name="formatter_unreachable_on_student_path",
        asserts=['formatters_reachable'],
        description=(
            "Stop the orchestrator recording which formatter it chose. §2C then cannot "
            "tell a served formatter from an unserved one and every advertised formatter "
            "reads as unreachable. This pins the field the check depends on: `format` "
            "holds the ROUTE name (read_mcq), which several formatters share, so "
            "reachability is unanswerable without `formatter_name` -- a first attempt at "
            "inferring it by fingerprinting mis-reported 62 unreachable pairs where the "
            "real number was 12."
        ),
        edits={
            "backend/app/services/orchestrator.py": (
                "            problem.formatter_name = formatter\n",
                "            problem.formatter_name = None  # planted mutation\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_compat", "--only", "reachable"],
        expected_check="§2C (an advertised formatter must be reachable by the student path)",
        expect_output_contains=["FAIL formatters_reachable"],
        baseline_must_not_contain=["FAIL formatters_reachable"],
    ),
    Mutation(
        name="dangling_node_reference",
        asserts=['node_references_resolve'],
        description=(
            "Add a node id that does not exist to a served code path. placement.py already "
            "carries 7 such ids (its forward-looking G4-G10 ladder), latent because nothing "
            "calls it -- but nothing asserted that a referenced node RESOLVES, so a live one "
            "would raise 'No DNA mappings found' in front of a student. This is the Scaling "
            "Mandate in miniature: fine while G1-3 are the only grades, silently wrong after."
        ),
        edits={
            "backend/app/services/curriculum.py": (
                "from backend.app import models\n",
                'from backend.app import models\n'
                '_PLANTED_NODE = "mat_g9_na_q1_7"  # planted mutation: absent from the registry\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_compat", "--only", "references"],
        expected_check="§2F (every node id referenced in the app must exist in the registry)",
        expect_output_contains=["FAIL node_references_resolve", "mat_g9_na_q1_7"],
        baseline_must_not_contain=["FAIL node_references_resolve"],
    ),
    Mutation(
        name="malformed_competency_bound",
        asserts=['all_competency_bounds_parse'],
        description=(
            "Make the bounds parser return an inverted (min, max) range. The ~20-row "
            "fixture table above still passes -- its hand-written G1-3 cases do not cover "
            "the mutated path -- which is exactly why the tree-wide property exists. A "
            "fixture proves specific readings; only the property catches a parser that "
            "starts returning nonsense on nodes nobody wrote a case for."
        ),
        edits={},
        apply_fn=lambda: _plant_inverted_bound(),
        command=["backend.app.practice_gen.validation.validate_compat", "--only", "bounds_property"],
        expected_check="§2G (every node's competency bounds parse to a well-formed shape)",
        expect_output_contains=["FAIL all_competency_bounds_parse", "min > max"],
        baseline_must_not_contain=["FAIL all_competency_bounds_parse"],
    ),
    Mutation(
        name="competency_scope_narrowed",
        asserts=["competency_scope_not_narrowed"],
        description=(
            "Blind the parser to two-sided phrasing: `_regrouping_is_two_sided` always "
            "returns False, so \"with and without regrouping\" is read as the one-sided "
            "\"without regrouping\" it contains as a substring. That is the historical "
            "defect's semantics -- mat_g3_na_q2_1 and mat_g2_na_q1_9 bind regrouping to a "
            "single case and render 0/120 carries. Every other stage stays green, because "
            "narrowing a bound REMOVES items and nothing downstream has anything to "
            "complain about. This is the shape a whole grade can inherit in silence.\n"
            "Planted at the predicate, not at either call site, deliberately: the fix put "
            "a guard at BOTH sites, so reverting one leaves the other still correct and "
            "the mutation survives while proving nothing. A mutation must land where the "
            "behaviour actually changes -- verified by watching it survive the call-site "
            "edit first."
        ),
        edits={
            "backend/app/practice_gen/registry.py": (
                "    return any(phrase in text for phrase in _TWO_SIDED_REGROUPING_PHRASES)",
                "    return False",
            ),
        },
        command=["backend.app.practice_gen.validation.validate_compat", "--only", "scope"],
        expected_check="§2H (a competency naming both cases must not be bound to one)",
        expect_output_contains=["FAIL competency_scope_not_narrowed", "mat_g3_na_q2_1"],
        baseline_must_not_contain=["FAIL competency_scope_not_narrowed"],
    ),
    Mutation(
        name="unproducible_variant_declared",
        asserts=["declared_variants_are_producible"],
        description=(
            "Drop the competency-bounds filter from the variant-coverage candidate builder, "
            "so nodes start declaring variant values their own competency excludes and the "
            "unproducible count climbs above its floor. This is the shape that hid for 31 "
            "nodes: the packet builder swallowed each failed render with `except Exception: "
            "return None`, so a declared-but-impossible variant simply vanished and the "
            "reviewer got a thinner packet with no indication anything was missing."
        ),
        # ANCHOR REPOINTED 2026-09-08, twice, and the second time is the instructive one.
        #
        # The original read "if bound is None or _bound_allows(bound, v):\n pairs.add(...)"
        # and matched ZERO times -- the loop had been restructured into guard-clause form
        # when the later filters were added, so this mutation raised "anchor matched 0
        # times" instead of testing anything and §2I's proof was stale (Mandate 2).
        #
        # Re-pointing it at the FIRST guard clause alone made it SURVIVE. The builder
        # filters against bounds TWICE -- once per-DNA (`bound`) and once against the
        # node's effective bounds (`eff`), which are the same values on a single-DNA node
        # -- so removing one changes nothing: candidates 964, findings 0. Removing both
        # takes candidates to 1633 and findings to 644. The redundancy is deliberate (a
        # multi-DNA node renders on one DNA while declaring for several), so the plant
        # must cover both sites: a mutation has to land where BEHAVIOUR changes, not
        # merely where the rule is written.
        edits={
            "backend/app/practice_gen/validation/judgment_packets.py": (
                "                for v in opts:\n"
                "                    if bound is not None and not _bound_allows(bound, v):\n"
                "                        continue\n"
                "                    eff = effective_bounds.get(var_name)\n"
                "                    if eff is not None and not _bound_allows(eff, v):\n"
                "                        continue\n",
                "                for v in opts:  # planted mutation: bounds filtering dropped\n",
            ),
        },
        command=["backend.app.practice_gen.validation.validate_compat", "--only", "producible"],
        expected_check="§2I (a declared discrete variant must be producible)",
        expect_output_contains=["FAIL declared_variants_are_producible"],
        baseline_must_not_contain=["FAIL declared_variants_are_producible"],
    ),
    Mutation(
        name="coverage_map_gap",
        asserts=["assertion_coverage_8"],
        description=(
            "Remove an assertion from the allowlist without writing its mutation. §8 must "
            "then report it as neither proven nor excused. This is the gate that stops the "
            "deficit growing: before §8, `Mutation.expected_check` was free text and "
            "nothing could state which assertions were proven, so '17 of 24 checks' "
            "counted a REF as proven when one of its sub-assertions was -- while "
            "validate_matrix alone emits 26 assertion labels behind ~11 refs."
        ),
        edits={
            "backend/app/practice_gen/validation/validate_coverage.py": (
                '    "worker_crash":                 "2026-08-28: infrastructure label, not a content assertion",\n',
                '    # planted mutation: allowlist entry removed, no mutation written\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_coverage"],
        expected_check="§8 (every assertion is proven by a mutation or on a shrinking allowlist)",
        # The marker names the planted LABEL, and the baseline guard does too. It used to
        # be the bare rollup line "FAIL assertion_coverage", which stopped discriminating
        # the moment §8 could be red for any other reason -- and since 2026-09-12 it can
        # be: §8 now counts EXECUTED proofs, so during the very run that produces them it
        # reports every not-yet-proven label. That made this mutation score INVALID
        # against a baseline it had itself caused. The specific conjunction survives a red
        # baseline, which is what a mutation's guard has to do.
        expect_output_contains=["worker_crash' can fail but no mutation proves it"],
        baseline_must_not_contain=["worker_crash' can fail but no mutation proves it"],
    ),
    Mutation(
        name="source_edited_without_reproof",
        asserts=["mutation_proof_integrity_8"],
        description=(
            "Edit pipeline source and re-run §8 WITHOUT re-running the mutation table. Every "
            "proof record on disk was taken against different bytes, so none of them "
            "describes what now runs, and §8 must say so rather than inheriting the last "
            "run's green. This is the direction that makes execution-proof worth having: a "
            "proof that cannot go stale is a checkbox with a digest on it."
        ),
        edits={
            # A comment in a DNA base class: a real edit to a real input, chosen because it
            # changes no behaviour at all. The point is precisely that §8 must object to an
            # unproved edit WITHOUT needing to know whether it mattered.
            "backend/app/practice_gen/dna/base.py": (
                "from __future__ import annotations\n",
                "from __future__ import annotations\n# planted mutation: an unproved source edit\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_coverage"],
        expected_check="§8 (an executed-mutation proof record that no longer describes the tree)",
        expect_output_contains=[
            "FAIL mutation_proof_integrity_8",
            "different source/fixture tree",
        ],
        baseline_must_not_contain=["different source/fixture tree"],
    ),
    # ---------------------------------------------------------------------------
    # §1J / §1K -- the two bounded lints on what a pupil READS, added 2026-09-12 while
    # both counts were zero (Scaling Mandate 5). Each plant reverts a real composition
    # site to the shape that was live before the fix, so the mutation is the defect the
    # gate was built on rather than an invented one.
    # ---------------------------------------------------------------------------
    Mutation(
        name="count_noun_disagrees",
        asserts=["count_noun_agreement_1J"],
        description=(
            "Interpolate a count and a plural noun with a bare f-string, the way "
            "'jump back 1 units' reached pupils. §1J must catch a stem whose noun "
            "disagrees with its own count -- including inside a quoted statement, which "
            "is where 'Taking away 1 cookies' was hiding."
        ),
        edits={
            "backend/app/practice_gen/dna/na/subtraction.py": (
                'f"Starting at {a_val} on the number line, jump back {b_val} {count_noun(b_val, \'units\')}. What number do you land on?",',
                'f"Starting at {a_val} on the number line, jump back {b_val} units. What number do you land on?",',
            )
        },
        command=["backend.app.practice_gen.validation.validate_language",
                 "--node-ids", "mat_g2_na_q2_3"],
        expected_check="§1J (an explicit count and its noun agree in the rendered text)",
        expect_output_contains=["mat_g2_na_q2_3 && 1 units"],
        baseline_must_not_contain=["count_noun_agreement_1J ("],
    ),
    Mutation(
        name="second_option_answers_too",
        asserts=["option_degeneracy_1K"],
        description=(
            "Make a distractor carry the keyed answer's exact value, so two of the four "
            "options are right and a pupil who picks the wrong right one is marked wrong. "
            "§1K must catch it by VALUE rather than by string equality."
        ),
        edits={
            # Plants in the PIPELINE, not in the check: an off-by-one in the pool slice
            # that lets the correct answer into the distractor list. The first plant tried
            # here -- emptying fmt_mcq's `seen` dedup set -- SURVIVED, because no
            # distractor pool on this tree happens to contain the key as a string, so the
            # plant never reached the code §1K runs on (Mandate 2, second cause). Recorded
            # rather than quietly replaced.
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                "    distractors = candidates[:3]\n",
                "    distractors = [correct] + candidates[:2]\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_options",
                 "--node-ids", "mat_g1_na_q4_2"],
        expected_check="§1K (exactly one option may answer the question)",
        expect_output_contains=["option_degeneracy_1K", "carry the keyed answer's exact value"],
        baseline_must_not_contain=["option_degeneracy_1K ("],
    ),
    # ---------------------------------------------------------------------------
    # The MCQ answer-key family: five assertions guarding the options a pupil actually
    # chooses between. All five were on §8's unproven allowlist -- the largest cluster of
    # assertion debt in the harness, and the one closest to the student.
    # ---------------------------------------------------------------------------
    Mutation(
        name="mcq_wrong_option_count",
        asserts=["mcq_option_count"],
        description="Serve three options instead of four, so the pupil is choosing from a short menu.",
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
                '    options = options[:3]  # planted mutation: short option list\n' + '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§4/§1C (MCQ option count)",
        expect_output_contains=["mcq_option_count"],
        baseline_must_not_contain=["mcq_option_count"],
    ),
    Mutation(
        name="mcq_no_correct_option",
        asserts=["mcq_correct_presence"],
        description=(
            "Mark every option incorrect. The pupil cannot answer correctly no matter what "
            "they choose, and nothing that reads the stem would notice."
        ),
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
                '    options = [dict(o, is_correct=False) for o in options]  # planted mutation\n' + '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§4/§1C (an MCQ must contain its correct answer)",
        expect_output_contains=["mcq_correct_presence"],
        baseline_must_not_contain=["mcq_correct_presence"],
    ),
    Mutation(
        name="mcq_duplicate_options",
        asserts=["mcq_option_uniqueness"],
        description=(
            "Duplicate an option value, so two choices are indistinguishable and one of "
            "them is 'wrong' while reading identically to the right one."
        ),
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
                '    if len(options) > 1:  # planted mutation: duplicate a value\n'
                '        options[-1] = dict(options[-1], value=options[0]["value"])\n' + '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§4/§1C (MCQ options must be distinct)",
        expect_output_contains=["mcq_option_uniqueness"],
        baseline_must_not_contain=["mcq_option_uniqueness"],
    ),
    Mutation(
        name="mcq_empty_option_value",
        asserts=["mcq_option_validity"],
        description=(
            "Blank one option's value. It renders as an empty choice the pupil can select "
            "and can never be right."
        ),
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
                '    if options:  # planted mutation: blank an option\n'
                '        options[-1] = dict(options[-1], value="")\n' + '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§4/§1C (no MCQ option may be empty)",
        expect_output_contains=["mcq_option_validity"],
        baseline_must_not_contain=["mcq_option_validity"],
    ),
    Mutation(
        name="mcq_key_disagrees_with_option",
        asserts=["mcq_correct_value_mismatch"],
        description=(
            "Flag a DIFFERENT option as correct from the one the answer key names. The "
            "pupil who answers correctly is marked wrong -- the same class §10 catches at "
            "the grader, caught here at the payload instead."
        ),
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
                '    if len(options) > 1:  # planted mutation: key names a different option\n'
                '        options = [dict(o, is_correct=(i == (0 if not o["is_correct"] else 1)))\n'
                '                   for i, o in enumerate(options)]\n' + '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§4/§1C (the flagged option must match the answer key)",
        expect_output_contains=["mcq_correct_value_mismatch"],
        baseline_must_not_contain=["mcq_correct_value_mismatch"],
    ),
    # Per-problem integrity: cheap to plant, and each guards something a pupil would meet
    # directly -- a blank question, a missing key, a formatter that is not what was asked for.
    Mutation(
        name="blank_question_text",
        asserts=["question_text_presence"],
        description="Serve an empty stem. The pupil is shown options and no question.",
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
                '    question_text = ""  # planted mutation: blank stem\n' + '    format_data = {\n        "options": options,\n        "correct_key": correct_key,\n        "context": context_variant,\n    }\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§1C (a served problem must carry a question)",
        expect_output_contains=["question_text_presence"],
        baseline_must_not_contain=["question_text_presence"],
    ),
    Mutation(
        name="missing_correct_answer",
        asserts=["correct_answer_presence"],
        description=(
            "Serve a problem with no answer key at all. Nothing downstream can grade it, "
            "and the reviews and attestations that read rendered output would still pass."
        ),
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                # REPOINTED 2026-09-11, same cause as `answer_corruption` one file over:
                # the served field became `correct_answer=correct` when compare_pair's
                # MCQ presentation started offering whole comparison statements. Two
                # mutations anchored on that one line and the full table caught both.
                "        correct_answer=correct,\n        distractors=distractors,",
                "        correct_answer=None,  # planted mutation: no answer key\n        distractors=distractors,",
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§1C (a served problem must carry an answer key)",
        expect_output_contains=["correct_answer_presence"],
        baseline_must_not_contain=["correct_answer_presence"],
    ),
    Mutation(
        name="formatter_route_mismatch",
        asserts=["formatter_match"],
        description=(
            "Return a route name that is not the formatter that was requested. The Lab and "
            "the matrix both believe they pinned one formatter while another was served -- "
            "which is how a per-formatter sweep can validate content nobody asked for."
        ),
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                '        format="mcq",\n        format_data=format_data,',
                '        format="cloze",  # planted mutation: route lies about the formatter\n        format_data=format_data,',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§1C (the served route must be the formatter that was requested)",
        expect_output_contains=["formatter_match"],
        baseline_must_not_contain=["formatter_match"],
    ),
    Mutation(
        name="stem_declares_the_answer",
        asserts=["answer_leak_in_stem"],
        description=(
            "Append 'It is <answer>.' to a counting stem. THIS EXACT PLANT SURVIVED on "
            "2026-08-26: §1F fires only when the answer is the stem's sole numeric datum, "
            "and '66, 67, 68, 69, ___? It is 70.' carries five numbers, so the check "
            "declined it by design. The narrowness was deliberate -- the wider form fired "
            "on 3,702 well-formed identity facts -- so the hole was closed with a SECOND, "
            "independent path that asks whether the answer is DECLARED rather than merely "
            "present. Verified silent across 906 renders before being asserted."
        ),
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                "        question_text = _build_pure_question(ctx)\n",
                '        question_text = f"{_build_pure_question(ctx)} It is {ctx.correct_answer}."\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_0"],
        expected_check="§1F (a stem may not state its own answer)",
        expect_output_contains=["answer_leak_in_stem", "states the answer outright"],
        baseline_must_not_contain=["states the answer outright"],
    ),
    Mutation(
        name="single_attester_identity",
        asserts=["attester_plurality_6H"],
        description=(
            "Stamp one identity on every attestation record, as a single pass over the "
            "table would. §5 has enforced reviewer plurality since it was written; "
            "attestation had no equivalent because all 173 records carried NO identity "
            "field at all -- so independence was uncheckable on a surface four times "
            "larger than §5's. §6G caps how many verdicts one BATCH may hold, which stops "
            "one record covering the table, but nothing stopped one agent filing every "
            "batch: the author-verifying-itself structure the blind role exists to break."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'single_attester'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "attestation"],
        expected_check="§6H (an Attester identity may not cover more than one dispatch)",
        expect_output_contains=["isolated_plant_attestation", 'attester plurality:'],
        baseline_must_not_contain=["isolated_plant_attestation", "FAIL isolated_control_attestation"],
    ),
    Mutation(
        name="attester_without_evidence",
        asserts=["attester_evidence_6G"],
        description=(
            "Break all three evidence branches of §6G on three live verdicts in one "
            "record: reasoning removed, PROVIDED with no seed named, and a seed cited "
            "that is absent from the record's own packet. `template_attestation` proved "
            "the skeleton-cluster path only, so the branch that asks a verdict to LOCATE "
            "what it saw was unproven on a 787-verdict surface."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'attester_no_evidence'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "attestation"],
        expected_check="§6G (a verdict must show its work and name the seeds that show it)",
        expect_output_contains=["isolated_plant_attestation", "names no seed in 'seeds_showing_it'"],
        baseline_must_not_contain=["isolated_plant_attestation", "FAIL isolated_control_attestation"],
    ),
    Mutation(
        name="withdrawn_attestation",
        asserts=["capability_unattested_6F"],
        description=(
            "Delete one declared capability's verdict from EVERY record that carries it. "
            "§6F's UNATTESTED branch reports zero on this tree, and 'everything is "
            "attested' and 'the check cannot see a gap' are different facts a passing run "
            "cannot tell apart. Removing it from the winning record alone would let an "
            "older record win and the capability would still read as attested -- the plant "
            "would land where behaviour does not change."
        ),
        # MIGRATED 2026-09-12 off the live corpus. This plant used to edit a real
        # agent-authored review file, which bound its proof to bytes Phase 1 may not
        # read and the fingerprint does not cover, and made it unprovable on a fresh
        # clone. It now plants into an isolated corpus built from live renders; the
        # driver runs a CLEAN build first, so every run carries its own positive
        # control. See tests/isolated_corpus.py.
        edits={
            "tests/isolated_corpus.py": (
                'PLANT: Optional[str] = None\n',
                "PLANT: Optional[str] = 'withdrawn_attestation'\n",
            )
        },
        command=["tests.isolated_corpus", "--gate", "attestation"],
        expected_check="§6F UNATTESTED (a declared capability nobody blind has judged)",
        expect_output_contains=["isolated_plant_attestation", 'is UNATTESTED (§6F)'],
        baseline_must_not_contain=["isolated_plant_attestation", "FAIL isolated_control_attestation"],
    ),
    Mutation(
        name="subtraction_pool_uncapped",
        asserts=['subtraction_candidate_pool_bounded'],
        description=(
            "Remove the enumerate-or-sample guard from subtraction's "
            "counting_back/taking_away branch, restoring the unbounded pair "
            "enumeration that made 49,994,955 _satisfies_regrouping calls at "
            "mat_g3_na_q2_4's max_minuend=9999 -- ~120s for one problem, and 42 of "
            "the 48 minutes a full validate_matrix run took."
        ),
        # Deliberately caught by a unit test, NOT a validator. That is the finding:
        # no §-check in the harness notices this bug. The tree-wide run sat at 48
        # minutes with one worker pegged for 42 of them and still reported
        # "151/151 pass, 0 findings". A complexity regression is invisible to every
        # assertion the matrix emits, so the test asserts predicate CALL COUNT --
        # deterministic, unlike wall-clock, which would be flaky under load.
        edits={
            "backend/app/practice_gen/dna/na/subtraction.py": (
                "        if max_minuend <= _EXHAUSTIVE_MINUEND_CEILING:\n"
                "            for a in range(lo_a, max_minuend + 1):\n",
                "        if True:  # planted mutation: pool cap removed\n"
                "            for a in range(lo_a, max_minuend + 1):\n",
            )
        },
        command=["pytest",
                 "tests/unit/test_subtraction_candidate_pool.py"
                 "::test_large_range_does_not_enumerate_the_whole_space",
                 "-q"],
        expected_check="candidate-pool budget (counting_back/taking_away)",
        expect_output_contains=["test_large_range_does_not_enumerate_the_whole_space"],
        baseline_must_not_contain=["test_large_range_does_not_enumerate_the_whole_space"],
    ),
    Mutation(
        name="grader_keys_a_value_answer",
        asserts=["grading_contract_10"],
        description=(
            "Send the portal's non-MCQ fallback back to comparing the submission against "
            "`correct_key`, the bug §10 caught: a `sort_order` answer of [10, 9, 8] was "
            "tested as \"[10, 9, 8]\" == \"A\", so a pupil who ordered the numbers "
            "correctly was told they were wrong. Four nodes served this."
        ),
        # Scoped to one node: validate_grade's --node-ids path is zero-tolerance (the
        # floor applies only to a full-tree run), so a single node both proves the check
        # and keeps the mutation to ~20s instead of the 13 minutes a full sweep costs.
        edits={
            "backend/app/routes/practice_router.py": (
                "                is_correct = answers_match(req.selected_answer, skeleton.get(\"correct_answer\"))\n",
                "                is_correct = (str(req.selected_answer).upper() == skeleton.get(\"correct_key\", \"A\").upper())\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_grade",
                 "--node-ids", "mat_g1_na_q1_4"],
        expected_check="§10 grading contract (a known-correct answer is graded correct)",
        expect_output_contains=["KNOWN-CORRECT && portal"],
        baseline_must_not_contain=["KNOWN-CORRECT"],
    ),
    Mutation(
        name="visual_payload_drops_required_key",
        asserts=["render_contract_floor_9"],
        description=(
            "Drop total_wholes from the FractionModel payload -- the key the React "
            "component needs to pre-render enough shapes for improper fractions. The "
            "assignment had genuinely been lost (the comment above it ended "
            "mid-sentence), shipping 7 broken payloads across 3 nodes."
        ),
        # Guards the §9 applicability change made in the same commit. §9 used to select
        # on `visual_type` alone and so reported 9 plain-text questions as broken
        # visuals; it now selects on is_visual, matching QuestionRenderer.jsx:44. This
        # mutation proves that narrowing did not stop it catching a REAL missing key on
        # a genuinely visual payload -- the failure mode of "fixing" a check by making
        # it look at less.
        #
        # REPOINTED 2026-09-11, and the reason is the whole point of this harness. The
        # plant used to drop `total_wholes`, which the hand-written REQUIRED_KEYS map
        # listed. When that map was replaced by a contract DERIVED from the component
        # AST (2026-09-11, one commit earlier), `total_wholes` stopped being required --
        # because `FractionModelInteractive` does not read it. The mutation went on
        # running, planting a bug §9 could no longer see, and SURVIVED: measured in a
        # pristine worktree at 950bc9a8, `0/1 mutations detected`, so BOTH §9 assertions
        # were unproven from the moment the contract became derived. That is cause two of
        # a surviving mutation -- the anchor moved out from under the check, not the
        # check breaking -- and the fix is to land the plant on a key the component
        # genuinely reads. `interaction_mode` is FractionModel's one derived-required
        # key, and the Pydantic model does not require it, so the payload is BUILT and
        # SERVED without it rather than raising at §4 first.
        edits={
            "backend/app/practice_gen/formatters/visual/fmt_fraction_model.py": (
                '    format_data: dict = {"visual_params": vp}\n',
                '    vp = {k: v for k, v in vp.items() if k != "interaction_mode"}  # planted mutation\n'
                '    format_data: dict = {"visual_params": vp}\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_render"],
        expected_check="§9 render contract (payload carries every key the component reads)",
        expect_output_contains=["FractionModel && interaction_mode"],
        baseline_must_not_contain=["FAIL render_contract"],
    ),
    Mutation(
        name="variant_coverage_silently_narrowed",
        asserts=["census", "census_variant_candidates"],
        description=(
            "Gut an applicability filter in _variant_coverage_candidates so the blind-"
            "review packets stop demonstrating variants they should. This is the failure "
            "mode §2I CANNOT see: it caps unproducible declarations from above, so "
            "dropping candidates makes it report FEWER findings and read as progress."
        ),
        # Measured before this gate existed: gutting two filters took candidates
        # 983 -> 932 and §2I 21 -> 19, and validate_compat still exited 0 printing
        # "13/13 check groups passed". Narrowing what a check looks at is both a
        # legitimate fix and a silent way to fake one; the §7 floor is what tells them
        # apart. Aimed at the census, not §2I, precisely because §2I gets QUIETER here.
        edits={
            "backend/app/practice_gen/validation/judgment_packets.py": (
                '    return bounds.get("task_type") != "estimate"\n',
                '    return False  # planted mutation: coverage silently narrowed\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_census"],
        expected_check="§7 census (variant coverage did not shrink)",
        expect_output_contains=["variant_candidates && below the floor"],
        baseline_must_not_contain=["variant_candidates && below the floor"],
    ),
    Mutation(
        name="single_formatter_unreachable",
        asserts=["formatters_reachable"],
        description=(
            "Make ONE more advertised formatter unreachable on nodes that are ALREADY on "
            "§2C's list. The existing mutation makes every advertised formatter "
            "unreachable and so blows past any floor; this is the regression a floor "
            "actually has to catch, and at node granularity it could not: the node count "
            "stays at 18 while cloze joins pattern_sequence as unserved on two patterns "
            "nodes. Measured -- pairs 37 -> 39, nodes 18 -> 18. A floor defeats only a "
            "regression smaller than its headroom, and every within-node regression was "
            "smaller than a node-counted floor's headroom by construction."
        ),
        edits={
            "backend/app/practice_gen/compatibility.py": (
                '        "pattern_sequence": {"task_type": ["find_next"], '
                '"ask_type": ["next", "missing"]},\n',
                '        "pattern_sequence": {"task_type": ["find_next"], '
                '"ask_type": ["next", "missing"]},\n'
                '        "cloze": {"task_type": ["__planted_never__"]},  # planted mutation\n',
            ),
        },
        command=["backend.app.practice_gen.validation.validate_compat", "--only", "reachable"],
        expected_check="§2C (an advertised formatter must be reachable on the student path)",
        expect_output_contains=["FAIL formatters_reachable", "advertises 'cloze'"],
        baseline_must_not_contain=["advertises 'cloze'"],
    ),
    # ---- §6's Phase 1 band: the four refs that were unproven while 75 findings sat
    # ---- under them. Mandate 3 -- a gate you are about to clear findings under has to
    # ---- be shown to work first. All four run the artifact-free half (0.1s, not 9.9s).
    Mutation(
        name="declarations_out_of_sync",
        asserts=["capability_declarations_in_sync_6"],
        description=(
            "Edit the HAND-AUTHORED declarations without rebuilding the graph §6 reads. "
            "data/knowledge_graph_g1_3.json is a build artifact of "
            "scripts/rebuild_knowledge_graph.py over data/skeletons/vocab_annotation.json, "
            "and nothing checked the two agreed -- so an author who edits the source and "
            "forgets the rebuild has §6 validate a stale copy indefinitely, while §6's own "
            "'no requires declaration' message points them at the file the validator does "
            "not read. Found because `clause_not_in_competency` planted here first and "
            "SURVIVED: the plant never reached the code the validator runs."
        ),
        edits={
            "data/skeletons/vocab_annotation.json": (
                '"id": "half_turn",\n          "clause": "half turn"',
                '"id": "half_turn",\n          "clause": "half rotation"',
            ),
        },
        command=["backend.app.practice_gen.validation.validate_capability", "--phase", "1"],
        expected_check="§6 (the declarations validated are the ones an author wrote)",
        expect_output_contains=["mat_g1_mg_q4_0 && does not match"],
        baseline_must_not_contain=["does not match"],
    ),
    Mutation(
        name="stale_generated_graph",
        asserts=["capability_declarations_in_sync_6"],
        description=(
            "Drift the generated graph from a fresh build of its skeleton in a field the "
            "sync gate did not compare. It checked `requires` and `requires_ignore` only, "
            "and the graph on disk at 8cb8dd22 differed in `cumulative_concepts` on 18 "
            "nodes -- the ground truth §1D's NOT_YET_KNOWN gating is judged against. The "
            "gate now rebuilds the skeleton in memory and compares every field, because a "
            "hand-picked field list goes stale the moment the builder derives something "
            "new."
        ),
        edits={},
        apply_fn=lambda: _plant_stale_generated_graph(),
        command=["backend.app.practice_gen.validation.validate_capability", "--phase", "1"],
        expected_check="§6 (the generated graph matches a fresh build, in every field)",
        expect_output_contains=[f"{_STALE_GRAPH_NODE} && 'cumulative_concepts'"],
        baseline_must_not_contain=[f"{_STALE_GRAPH_NODE} && 'cumulative_concepts'"],
    ),
    Mutation(
        name="unsanctioned_requires_ignore",
        asserts=["requires_ignore_locked_6B"],
        description=(
            "Add a word to a node's `requires_ignore` without sanctioning it in "
            "data/skeletons/requires_ignore.lock.json. Ignoring a competency word is a "
            "curriculum ruling only a human may make, and it is also the free half of "
            "§6B's own remedy -- 'declare the requirement, or list the word in "
            "requires_ignore' -- so without the lock an agent can silence a coverage "
            "finding by waiving the competency instead of serving it."
        ),
        edits={},
        apply_fn=lambda: _plant_unsanctioned_requires_ignore(),
        command=["backend.app.practice_gen.validation.validate_capability", "--phase", "1"],
        expected_check="§6B (requires_ignore is human-authored ground truth)",
        expect_output_contains=[f"{_IGNORE_LOCK_NODE} && does not match"],
        baseline_must_not_contain=[f"{_IGNORE_LOCK_NODE} && does not match"],
    ),
    Mutation(
        name="frontend_contract_key_unserved",
        asserts=["render_contract_floor_9"],
        description=(
            "Make a React component read a params key no payload supplies. Until "
            "2026-09-11 the contract §9 checks against was a HAND-WRITTEN key map in "
            "tests/frontend_contract_auditor.py, so a component that started reading a "
            "new key was covered only if someone remembered to add it there -- and "
            "measured that day it had drifted 35 keys away from the components it "
            "claimed to mirror. The map is now derived from the component AST, so this "
            "plant is reached the moment it is written, with no list to update."
        ),
        edits={
            "frontend/src/components/VisualSkeletons.jsx": (
                "export function GridAreaInteractive({ params, onAnswer, disabled }) {\n"
                "  const { grid_size, correct_count, width, height, shape_type, cols, rows } = params || {};",
                "export function GridAreaInteractive({ params, onAnswer, disabled }) {\n"
                "  const { grid_size, correct_count, width, height, shape_type, cols, rows } = params || {};\n"
                f"  const plantedContractKey = params.{_FRONTEND_PLANT_KEY};  // planted mutation\n"
                "  void plantedContractKey;",
            ),
        },
        command=["backend.app.practice_gen.validation.validate_render"],
        expected_check="§9 (the payload carries every key the component reads)",
        expect_output_contains=[_FRONTEND_PLANT_KEY],
        baseline_must_not_contain=[_FRONTEND_PLANT_KEY],
    ),
    Mutation(
        name="clause_not_in_competency",
        asserts=["capability_provenance_6A"],
        description=(
            "Re-word a declared clause so the competency no longer contains it. §6A is the "
            "half of the tiling rule that blocks INVENTION: without it an agent can declare "
            "a requirement MATATAG never wrote, and §6C will then report it as provided or "
            "not as if it were real. Plants in the declarations themselves, which is where "
            "the defect would live."
        ),
        edits={
            # The GENERATED graph, not the hand-authored source: `get_node_info` reads
            # data/knowledge_graph_g1_3.json, which scripts/rebuild_knowledge_graph.py
            # builds from vocab_annotation.json. Planting in the source made this
            # mutation SURVIVE -- it never reached the code the validator runs
            # (Mandate 2, second cause). That the two can disagree at all is now its own
            # gate: `declarations_out_of_sync`.
            "data/knowledge_graph_g1_3.json": (
                '"id": "half_turn",\n          "clause": "half turn"',
                '"id": "half_turn",\n          "clause": "half somersault"',
            ),
        },
        command=['backend.app.practice_gen.validation.validate_capability', '--phase', '1'],
        expected_check="§6A (a declared clause must be a literal substring of the competency)",
        expect_output_contains=["half somersault && does not appear in the node's competency"],
        baseline_must_not_contain=["does not appear in the node's competency"],
    ),
    Mutation(
        name="competency_word_uncovered",
        asserts=["capability_coverage_6B"],
        description=(
            "Delete a requirement so a competency word is covered by no clause. §6B is the "
            "half of the tiling rule that blocks OMISSION -- the loophole that guts the "
            "whole design, because an agent that cannot render 'half turn' could simply not "
            "declare it and §6C would pass trivially. mat_g1_mg_q4_0's competency names "
            "'half turn' explicitly."
        ),
        edits={
            "data/knowledge_graph_g1_3.json": (
                '        {\n          "kind": "range",\n          "id": "half_turn",\n'
                '          "clause": "half turn"\n        },\n',
                '',
            ),
        },
        command=['backend.app.practice_gen.validation.validate_capability', '--phase', '1'],
        expected_check="§6B (every content word of the competency is covered by some clause)",
        expect_output_contains=["mat_g1_mg_q4_0 && are covered by no requirement"],
        baseline_must_not_contain=["are covered by no requirement"],
    ),
    Mutation(
        name="capability_provider_unregistered",
        asserts=["capability_provision_6C"],
        description=(
            "Remove a capability's provider entry entirely. §6C is what converts 'an agent "
            "decided this node was too hard' into a named build item, and it was unproven "
            "while 74 §6D findings sat next to it. `0_and_5` is chosen because its entry is "
            "a genuine variant provider -- ('pair', '0 and 5') on compose_decompose_to_10 -- "
            "so deleting it moves a SATISFIED capability into the unprovided branch, which "
            "is the transition the check exists to notice."
        ),
        edits={
            "backend/app/practice_gen/validation/validate_capability.py": (
                "    '0_and_5': {'variants': [('pair', '0 and 5'), "
                "('pair', 'all ways to make 5')]},\n",
                "    # planted mutation: provider entry deleted\n",
            ),
        },
        command=['backend.app.practice_gen.validation.validate_capability', '--phase', '1'],
        expected_check="§6C (every declared capability maps to something the node can produce)",
        expect_output_contains=["'0_and_5' && register it in CAPABILITY_PROVIDERS"],
        baseline_must_not_contain=["'0_and_5' && register it in CAPABILITY_PROVIDERS"],
    ),
    Mutation(
        name="provider_is_only_a_bounds_catch_all",
        asserts=["capability_nondiscriminating_bounds_6E"],
        description=(
            "Strip an entry's formatters so its only remaining provider is the 27-key "
            "`bounds` list that 474 of 484 entries carry verbatim. §6E is §6D's twin -- §6D "
            "catches the generic FORMATTER escape, §6E the generic BOUNDS escape -- and it "
            "was the unproven one. A catch-all shared by all but ten entries makes no claim "
            "about any capability in particular, so it must not rescue one."
        ),
        edits={
            "backend/app/practice_gen/validation/validate_capability.py": (
            # Repointed 2026-09-09: '1st' moved onto a SPECIFIC bounds list
            # (['ordinal_range', 'max_ordinal']) when the ordinal band was cleared,
            # so it no longer carries the catch-all this mutation needs.
            # 'range_up_to_100' does, and mat_g1_na_q1_0 reaches it by a specific
            # formatter today.
                "    'range_up_to_100': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},\n",
                "    'range_up_to_100': {'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},\n",
            ),
        },
        command=['backend.app.practice_gen.validation.validate_capability', '--phase', '1'],
        expected_check="§6E (a `bounds` catch-all most of the table shares is not a provider)",
        expect_output_contains=["'range_up_to_100' && only reachable provider is a `bounds` catch-all"],
        baseline_must_not_contain=["only reachable provider is a `bounds` catch-all"],
    ),
    Mutation(
        name="contract_check_declares_no_phase",
        asserts=["check_phase_registry_8"],
        description=(
            "Drop a registered check's phase from _manifest.CHECK_PHASE. `run_all "
            "--phase N` selects stages by that registry, so a ref with no phase is "
            "omitted from EVERY band -- and the two-direction tripwire still passes, "
            "because it only ever compares the refs that ran against the refs expected "
            "for the band that ran. A check that runs in no phase stops running the "
            "moment anyone runs a phase, silently. Measured 2026-09-09, before the "
            "registry went harness-wide: 28 of 35 refs were in exactly this state."
        ),
        edits={
            "backend/app/practice_gen/validation/_manifest.py": (
                '    "§9": 1,\n',
                '    # planted mutation: §9 phase removed\n',
            ),
        },
        command=["backend.app.practice_gen.validation.validate_coverage"],
        expected_check="§8 (every contract check declares the phase it runs in)",
        expect_output_contains=["§9 && declares no phase"],
        baseline_must_not_contain=["declares no phase"],
    ),
    # ---- §8's own four extra directions ------------------------------------------
    #
    # §8 is the gate that measures whether the other gates are real, so the one thing it
    # may not be is unproven itself. Its first direction (inventoried, unproven, not
    # excused) is `coverage_map_gap` above; these four cover the rest. All are cheap --
    # validate_coverage parses source and imports the validation package, no generation.
    Mutation(
        name="allowlist_keeps_a_paid_debt",
        asserts=["assertion_allowlist_paid_8"],
        description=(
            "Park an assertion that IS proven on the unproven allowlist. The allowlist is "
            "a debt register whose only permitted direction is down; an entry left on it "
            "after its mutation was written overstates the remaining deficit and, worse, "
            "makes the register unreadable as a work queue."
        ),
        edits={
            "backend/app/practice_gen/validation/validate_coverage.py": (
                '    # ---- §1* validate_matrix ---',
                '    "vocabulary_gating":            "planted mutation: this label IS proven",\n'
                '    # ---- §1* validate_matrix ---',
            ),
        },
        command=["backend.app.practice_gen.validation.validate_coverage"],
        expected_check="§8 (an allowlisted assertion a mutation now proves)",
        expect_output_contains=["vocabulary_gating && now proves it"],
        baseline_must_not_contain=["now proves it"],
    ),
    Mutation(
        name="allowlist_names_a_phantom_label",
        asserts=["assertion_allowlist_phantom_8"],
        description=(
            "Add an allowlist entry for a label no check site emits. Two entries of "
            "exactly this shape were found on 2026-09-08 when the inventory was widened: "
            "`node_to_dna_presence` (the emitted label is `NODE_TO_DNA_presence`) and "
            "`scalar_1_0_reach` (no site emits it at all). Both had read as accounted-for "
            "debt since 2026-08-28 while excusing nothing, and the real labels sat outside "
            "the inventory entirely."
        ),
        edits={
            "backend/app/practice_gen/validation/validate_coverage.py": (
                '    # ---- §1* validate_matrix ---',
                '    "worker_crash_typo":            "planted mutation: nothing emits this",\n'
                '    # ---- §1* validate_matrix ---',
            ),
        },
        command=["backend.app.practice_gen.validation.validate_coverage"],
        expected_check="§8 (an allowlist entry naming a label nothing emits)",
        expect_output_contains=["worker_crash_typo && excuses nothing"],
        baseline_must_not_contain=["excuses nothing"],
    ),
    Mutation(
        name="mutation_asserts_an_unknown_label",
        asserts=["assertion_asserts_unknown_8"],
        description=(
            "Misspell a `Mutation.asserts` label. `asserts` is free text, so a typo marks "
            "a label proven that nothing emits while the REAL label quietly falls back "
            "into the unproven set -- the same defect as a phantom allowlist entry, "
            "entered from the mutation side. Plants in the harness rather than the "
            "pipeline because the harness's own bookkeeping is what §8 audits."
        ),
        edits={
            "tests/mutation_harness.py": (
                '        asserts=[\'option_placement\'],\n',
                '        asserts=[\'option_placementt\'],  # planted mutation\n',
            ),
        },
        command=["backend.app.practice_gen.validation.validate_coverage"],
        expected_check="§8 (a mutation asserting a label no validator declares)",
        expect_output_contains=["option_placementt && no validator declares"],
        baseline_must_not_contain=["no validator declares"],
    ),
    Mutation(
        name="undeclared_check_reports_itself",
        asserts=["assertion_undeclared_check_8"],
        description=(
            "Add a check that prints its own `  FAIL <label>` line without declaring the "
            "label in its module's ASSERTIONS. This is the discovery direction: without "
            "it, the DECLARED half of the inventory is only as complete as whoever last "
            "edited a validator remembered to make it, and a new gate could be added, "
            "never proven, and never counted as unproven either."
        ),
        edits={
            "backend/app/practice_gen/validation/validate_census.py": (
                '        print(f"  FAIL census ({len(errors)} floor(s) breached):")\n',
                '        print(f"  FAIL census ({len(errors)} floor(s) breached):")\n'
                '        print("  FAIL undeclared_planted_check: nobody declared me")\n',
            ),
        },
        command=["backend.app.practice_gen.validation.validate_coverage"],
        expected_check="§8 (a printed FAIL label no module declares)",
        expect_output_contains=["undeclared_planted_check && no module declares"],
        baseline_must_not_contain=["no module declares"],
    ),
    Mutation(
        name="emoji_pictorial_draws_a_different_operation",
        asserts=["answer_key_integrity"],
        description=(
            "Put back the silent default `operation = ctx.dna_concept if ctx.dna_concept "
            "in ('addition', 'subtraction') else 'addition'`, which is how "
            "fmt_emoji_pictorial stood until 2026-09-11. Pointed at a multiplication "
            "node it then draws a + b items beside an answer keyed a x b: a PICTURE that "
            "contradicts its own key, on the two grade-2 nodes whose competencies are "
            "stated entirely in groups. Declaring a visual formatter compatible with a "
            "DNA it has no branch for does not make it render that DNA -- it makes it "
            "render something else, which is the same lesson fmt_number_line's money "
            "branch records."
        ),
        edits={
            "backend/app/practice_gen/formatters/visual/fmt_emoji_pictorial.py": (
                "        operation = ctx.dna_concept\n"
                '        a = values.get("a", 3)\n',
                "        operation = ctx.dna_concept if ctx.dna_concept in (\"addition\", \"subtraction\") else \"addition\"  # planted mutation\n"
                '        a = values.get("a", 3)\n',
            ),
        },
        command=["backend.app.practice_gen.validation.validate_matrix",
                 "--node", "mat_g2_na_q3_0"],
        expected_check="§1E answer-key integrity (the picture's arithmetic is the item's)",
        expect_output_contains=["emoji_pictorial && answer_key_integrity"],
        baseline_must_not_contain=["answer_key_integrity"],
    ),
    Mutation(
        name="number_line_drops_its_jumps",
        asserts=[],
        description=(
            "Stop the multiplication number-line payload carrying the jumps its own stem "
            "promises -- the state the pipeline was in until 2026-09-11, when it rendered "
            "'Starting at 0, taking 2 equal jumps of 9 on the number line lands on ___' "
            "over a line with a single dot on it. "
            "Caught by a UNIT TEST, not by a validator, and that is the finding: the "
            "React component reads jump_count/jump_size inside a branch, so the derived "
            "frontend contract classes them CONDITIONAL and §9 -- which enforces "
            "unconditional keys only -- cannot see their absence. §1G checks that a "
            "DECLARED run of jumps is consistent; nothing but this test checks that a "
            "competency naming the medium still gets one."
        ),
        edits={
            "backend/app/practice_gen/formatters/visual/fmt_number_line.py": (
                '        "jump_from": start,\n'
                '        "jump_size": a,\n'
                '        "jump_count": b,\n',
                "        # planted mutation: the medium the competency names, undeclared\n",
            ),
        },
        command=["pytest",
                 "tests/unit/test_media_the_competency_names.py"
                 "::test_multiplication_number_line_carries_its_jumps",
                 "-q"],
        expected_check="the payload draws the medium mat_g2_na_q3_1 names",
        expect_output_contains=["test_multiplication_number_line_carries_its_jumps"],
        baseline_must_not_contain=["test_multiplication_number_line_carries_its_jumps"],
    ),
    Mutation(
        name="number_line_jumps_land_elsewhere",
        asserts=["visual_payload"],
        description=(
            "Draw one jump more than the item is keyed to. The picture is still a "
            "well-formed run of equal jumps on a well-formed axis -- every §1G invariant "
            "that existed before 2026-09-11 passes it -- but it lands on a different "
            "number than the pupil is graded on, which is the defect a drawn model can "
            "have that a text stem cannot."
        ),
        edits={
            "backend/app/practice_gen/formatters/visual/fmt_number_line.py": (
                '        "jump_count": b,\n',
                '        "jump_count": b + 1,  # planted mutation\n',
            ),
        },
        command=["backend.app.practice_gen.validation.validate_matrix",
                 "--node", "mat_g2_na_q3_1"],
        expected_check="§1G visual payload (the picture agrees with its own answer)",
        expect_output_contains=["visual_payload && landing on"],
        baseline_must_not_contain=["visual_payload"],
    ),
    Mutation(
        name="compare_pair_asks_for_a_sign_and_offers_statements",
        asserts=["pipeline_run"],
        description=(
            "Drop the word-problem wording that asks which STATEMENT is true, leaving the "
            "narrative ending on 'Which sign correctly compares the two amounts?' while "
            "fmt_mcq offers four whole statements -- a stem asking a question its own "
            "options cannot answer. The four-statement presentation (owner ruling "
            "2026-09-11) replaced a permanent 'cannot be determined' fourth option, and "
            "this is the way it can go wrong silently: both halves render, and only the "
            "pupil notices they do not match. The formatter refuses instead."
        ),
        edits={
            "backend/app/practice_gen/dna/na/comparing_ordering.py": (
                '            result_dict["question_statement"] = (\n'
                '                f"{actor} has {a} {a_word}. {friend} has {b} {b_word}. "\n'
                '                f"Which statement is true?"\n'
                "            )\n",
                "            pass  # planted mutation: the statement wording removed\n",
            ),
        },
        command=["backend.app.practice_gen.validation.validate_matrix",
                 "--node", "mat_g1_na_q1_3"],
        expected_check="§1C execution (a formatter refuses a stem its options cannot answer)",
        expect_output_contains=["pipeline_run && question_statement"],
        baseline_must_not_contain=["pipeline_run"],
    ),
    # ── §10's second direction, added with it 2026-09-12 (H-01) ─────────────────────
    #
    # `grader_rejects_correct_answer` above plants an ALWAYS-FALSE grader. Until these
    # existed there was no plant for its mirror: an ALWAYS-TRUE grader satisfied every
    # §10 assertion perfectly, because the only obligation was that a correct answer be
    # accepted. The plan names both explicitly as H-01 closure evidence.
    Mutation(
        name="grader_accepts_wrong_answer",
        asserts=["grading_refusal_10"],
        description=(
            "Make the Lab v1 grader accept every submission -- the exact mirror of "
            "`grader_rejects_correct_answer`, and the defect an accept-only §10 could "
            "never see. A pupil who gets the mathematics wrong is told they are right, "
            "their ELO rises, and mastery is recorded for a competency they do not have."
        ),
        edits={
            "backend/app/routes/matatag_router.py": (
                "    return {\n"
                '        "is_correct": is_correct,\n'
                '        "correct_answer": correct_answer_str,\n'
                '        "trap_triggered": trap_triggered,\n',
                "    return {\n"
                '        "is_correct": True,  # planted mutation: accept every answer\n'
                '        "correct_answer": correct_answer_str,\n'
                '        "trap_triggered": trap_triggered,\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_grade",
                 "--node-ids", "mat_g1_na_q1_0"],
        expected_check="§10 (a known-wrong or malformed submission must be graded incorrect)",
        expect_output_contains=["FAIL grading_refusal_10",
                                "KNOWN-WRONG && told they are right"],
        baseline_must_not_contain=["FAIL grading_refusal_10"],
    ),
    Mutation(
        name="grader_coerces_malformed_boolean",
        asserts=["grading_refusal_10"],
        description=(
            "Restore the lenient true/false membership test that all three graders shared "
            "until 2026-09-12: `str(v).lower() in (\"true\", \"yes\", \"t\", \"1\")`, which has no "
            "failure value, so every unrecognised submission became False. On a "
            "`true_false` item keyed False -- about half of them -- a pupil who submitted "
            "gibberish was graded CORRECT. Measured on three G1 nodes before the fix."
        ),
        edits={
            "backend/app/services/scoring.py": (
                "    student = parse_bool_answer(student_ans)\n"
                "    correct = parse_bool_answer(correct_ans)\n"
                "    return student is not None and correct is not None and student == correct\n",
                "    # planted mutation: the pre-2026-09-12 lenient membership test\n"
                '    student = str(student_ans).strip().lower() in ("true", "yes", "t", "1")\n'
                '    correct = str(correct_ans).strip().lower() in ("true", "yes", "t", "1")\n'
                "    return student == correct\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_grade",
                 "--node-ids", "mat_g1_na_q1_1"],
        expected_check="§10 (a malformed submission must not be coerced into the keyed answer)",
        expect_output_contains=["FAIL grading_refusal_10", "MALFORMED"],
        baseline_must_not_contain=["FAIL grading_refusal_10"],
    ),
    Mutation(
        name="grader_drops_key_normalisation",
        asserts=["grading_equivalence_10"],
        description=(
            "Drop the `.strip()` from the shared MCQ key normaliser. This was the state "
            "of the tree until 2026-09-12: the comparison was hand-written seven times "
            "and only Lab v2 stripped, so a submission of '  B  ' against a key of 'B' "
            "was refused by the portal and Lab v1 and accepted by Lab v2 -- 211 of 256 "
            "MCQ samples, one submission, two answers."
        ),
        edits={
            "backend/app/services/scoring.py": (
                "    return str(value).strip().upper()\n",
                "    return str(value).upper()  # planted mutation: strip() removed\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_grade",
                 "--node-ids", "mat_g1_na_q1_0"],
        expected_check="§10 (an equivalent rendering of the correct answer is still accepted)",
        expect_output_contains=["FAIL grading_equivalence_10", "whitespace-"],
        baseline_must_not_contain=["FAIL grading_equivalence_10"],
    ),
    Mutation(
        name="grading_obligation_silently_skipped",
        asserts=["grading_obligation_10"],
        description=(
            "Make generation raise for one node. Until 2026-09-12 §10 answered this with "
            "`except Exception: continue`, so a node whose grading contract was never "
            "exercised at all reported exactly like a node that passed -- the silent-skip "
            "shape AGENTS.md Protocol 3 forbids and plan step 0A names for every "
            "obligation failure."
        ),
        edits={
            "backend/app/services/orchestrator.py": (
                "        rng = random.Random(seed)\n",
                "        rng = random.Random(seed)\n"
                '        if node_id == "mat_g1_na_q1_0":  # planted mutation\n'
                '            raise RuntimeError("planted generation failure")\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_grade",
                 "--node-ids", "mat_g1_na_q1_0"],
        expected_check="§10 (an obligation that cannot be executed fails by name)",
        expect_output_contains=["FAIL grading_obligation_10",
                                "planted generation failure"],
        baseline_must_not_contain=["FAIL grading_obligation_10"],
    ),
    Mutation(
        name="graded_path_reaches_the_network",
        asserts=["grading_hermetic_10"],
        description=(
            "Add an outbound connection to the portal's submit route. This is H-01 in "
            "miniature: §10 used to open the CONFIGURED database, so on 2026-09-12 the "
            "same code crashed Phase 1 in the morning (Neon DNS) and passed in the "
            "afternoon. A gate whose verdict depends on an external host is not a gate "
            "(Protocol 6). The hermetic guard must name the regression, not tolerate it."
        ),
        edits={
            "backend/app/routes/practice_router.py": (
                "    # Grading\n",
                "    # Grading\n"
                "    import socket as _planted_socket  # planted mutation\n"
                '    _planted_socket.create_connection(("example.com", 80), timeout=1)\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_grade",
                 "--node-ids", "mat_g1_na_q1_0"],
        expected_check="§10 (the graded path must not reach the network)",
        expect_output_contains=["FAIL grading_hermetic_10",
                                "outbound network connection"],
        baseline_must_not_contain=["FAIL grading_hermetic_10"],
    ),
    Mutation(
        name="grader_rejects_correct_answer_tree_wide",
        asserts=["grading_contract_floor_10"],
        description=(
            "The same always-false Lab v1 grader as `grader_rejects_correct_answer`, run "
            "WITHOUT --node-ids so it lands on the full-tree floor path instead of the "
            "zero-tolerance subset path. `grading_contract_floor_10` was allowlisted as "
            "unproven from 2026-09-08 precisely because both grading mutations were "
            "scoped to one node -- the same gap §9's floor path had already closed on the "
            "render side. It costs a full sweep, which is 33 seconds now that §10 is "
            "hermetic and no longer waits on a database across the public internet."
        ),
        edits={
            "backend/app/routes/matatag_router.py": (
                "    return {\n"
                '        "is_correct": is_correct,\n'
                '        "correct_answer": correct_answer_str,\n'
                '        "trap_triggered": trap_triggered,\n',
                "    return {\n"
                '        "is_correct": False,  # planted mutation: reject every answer\n'
                '        "correct_answer": correct_answer_str,\n'
                '        "trap_triggered": trap_triggered,\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_grade"],
        expected_check="§10 full-tree floor (mis-gradings measured against GRADE_FLOOR)",
        expect_output_contains=["FAIL grading_contract_floor_10",
                                "mis-gradings exceeds floor"],
        baseline_must_not_contain=["FAIL grading_contract_floor_10"],
    ),
    # ── The stage ledger (H-03, 2026-09-12) ────────────────────────────────────────
    #
    # These drive pytest rather than a validator, for the reason `subtraction_pool_uncapped`
    # already does: the behaviour lives in `run_all` itself, a full Phase 1 run costs about
    # eight minutes, and the Phase 2 band's baseline is red by construction so a plant there
    # could not be scored at all (Mandate 2). `tests/unit/test_stage_ledger.py` drives the
    # REAL StageLedger and the REAL run_all with every validator stubbed, so the plant lands
    # on the production control flow and is caught by name in under a second.
    #
    # NAMED LIMIT: because the catcher is a unit test rather than a live `run_all`, these
    # prove the ledger's control flow, not that a crash in a REAL validator is contained.
    # The measurement that establishes the latter is recorded in the test module's docstring
    # and in HARDENING_EVIDENCE.md, and was taken by monkeypatching a live run.
    Mutation(
        name="stage_crash_escapes_the_ledger",
        asserts=["stage_crashed_"],
        description=(
            "Let a stage's exception propagate instead of being recorded. This is exactly "
            "the state of run_all until 2026-09-12, and it was measured: one stage raising "
            "took §10, §8, §7, the two-direction tripwire AND the final summary with it, "
            "and printed nothing naming what had been lost. An operator saw a traceback, "
            "not the fact that the grading contract never ran."
        ),
        edits={
            "backend/app/practice_gen/validation/run_all.py": (
                "        except BaseException as exc:  # noqa: BLE001 - a crash must not escape a stage\n",
                "        except () as exc:  # planted mutation: the boundary catches nothing\n",
            )
        },
        command=["pytest", "tests/unit/test_stage_ledger.py", "-q", "-p", "no:cacheprovider"],
        expected_check="the stage exception boundary (a crash is a named failure, not an escape)",
        expect_output_contains=["test_a_raising_stage_is_contained_and_named"],
        baseline_must_not_contain=["test_a_raising_stage_is_contained_and_named"],
    ),
    Mutation(
        name="unreached_stage_reported_as_clean",
        asserts=["stage_ledger_complete"],
        description=(
            "Stop counting a scheduled-but-never-entered stage as a failure. A fail-fast "
            "abort then reports exactly like a clean run of a smaller suite: the stages it "
            "never reached simply vanish from the report. An obligation nobody checked is "
            "not an obligation that passed -- that is the whole claim of this ledger, and "
            "without this plant nothing proves the harness makes it."
        ),
        edits={
            "backend/app/practice_gen/validation/run_all.py": (
                '        elif stage.state in ("scheduled", "attempted"):\n',
                '        elif stage.state in ():  # planted mutation: unreached == fine\n',
            )
        },
        command=["pytest", "tests/unit/test_stage_ledger.py", "-q", "-p", "no:cacheprovider"],
        expected_check="the stage ledger (an unreached obligation is a failure, not silence)",
        expect_output_contains=["test_a_stage_that_never_ran_is_a_ledger_failure"],
        baseline_must_not_contain=["test_a_stage_that_never_ran_is_a_ledger_failure"],
    ),
    Mutation(
        name="crash_deletes_its_own_expected_refs",
        asserts=["two_direction_contract_match"],
        description=(
            "Let a CRASHED stage discard its own §-refs from the two-direction comparison, "
            "the way a FAILED stage legitimately does. The tripwire that exists to notice a "
            "registered check never executing is then silenced by the very crash that "
            "stopped it executing. This also PAYS an allowlist entry: "
            "`two_direction_contract_match` had been unproven since 2026-09-08."
        ),
        edits={
            "backend/app/practice_gen/validation/run_all.py": (
                '            if _stage.state == "failed":\n',
                '            if _stage.state in ("failed", "crashed"):  # planted mutation\n',
            )
        },
        command=["pytest", "tests/unit/test_stage_ledger.py", "-q", "-p", "no:cacheprovider"],
        expected_check="two-direction drift (a crash cannot delete its own expected refs)",
        expect_output_contains=["test_a_crash_cannot_delete_its_own_expected_refs"],
        baseline_must_not_contain=["test_a_crash_cannot_delete_its_own_expected_refs"],
    ),
    Mutation(
        name="stage_runs_in_the_wrong_band",
        asserts=["stage_phase_matches_manifest"],
        description=(
            "Stop comparing each stage's declared refs against the band "
            "`_manifest.CHECK_PHASE` registers them to. These are two registries "
            "describing one fact and nothing compared them until 2026-09-12: move §9 to "
            "Phase 2 in the manifest and `render_contract_9` still runs in Phase 1, so "
            "`--phase 2` reports it registered-but-never-executed forever while "
            "`--phase 1` goes on executing a ref it does not own. The wrong-phase path "
            "plan step 0A asks to be proved."
        ),
        edits={
            "backend/app/practice_gen/validation/run_all.py": (
                "            elif registered != stage.phase:\n",
                "            elif False:  # planted mutation: bands need not agree\n",
            )
        },
        command=["pytest", "tests/unit/test_stage_ledger.py", "-q", "-p", "no:cacheprovider"],
        expected_check="the stage schedule agrees with _manifest.CHECK_PHASE on every ref",
        expect_output_contains=["test_a_ref_registered_to_the_other_band_is_caught"],
        baseline_must_not_contain=["test_a_ref_registered_to_the_other_band_is_caught"],
    ),
    # ── §11, the obligation manifest (H-04, 2026-09-12) ────────────────────────────
    Mutation(
        name="obligation_derivations_diverge",
        asserts=["obligation_derivations_agree"],
        description=(
            "Drop one production gate from the node-first traversal only, so the two "
            "derivations stop describing the same reachable space. This is the failure "
            "the plan's own recorded figure walked into: 4,325 obligations across 463 "
            "pairs, derived once, by a probe that is no longer on disk, reproducible by "
            "no candidate model. A count nobody can re-derive is a number, not evidence."
        ),
        edits={
            "tests/obligation_manifest.py": (
                "                if formatter_refused_at_node(dna, comp_bounds, formatter):\n"
                "                    rejections.append(Rejection(\n",
                "                if False:  # planted mutation: one gate, one traversal\n"
                "                    rejections.append(Rejection(\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_obligations"],
        expected_check="§11 (two independent derivations of the reachable count agree)",
        expect_output_contains=["FAIL obligation_derivations_agree",
                                "disagree"],
        baseline_must_not_contain=["FAIL obligation_derivations_agree"],
    ),
    Mutation(
        name="dead_formatter_route_ignored",
        asserts=["obligation_routes_reachable"],
        description=(
            "Register a sixth formatter route nothing can reach. §2B and §2C hold "
            "'a formatter a node ADVERTISES must be servable'; until §11 nothing held the "
            "reverse, so a route in adapter.FORMATTER_ROUTES that no DNA declares and no "
            "node advertises sat there indefinitely. Five already do, in two classes, "
            "which is why the gate is a shrink-only floor rather than a hard zero."
        ),
        edits={
            "backend/app/practice_gen/adapter.py": (
                "FORMATTER_ROUTES: Dict[str, tuple] = {\n",
                'FORMATTER_ROUTES: Dict[str, tuple] = {\n'
                '    "planted_dead_route": (),  # planted mutation\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_obligations"],
        expected_check="§11 (a registered formatter route no obligation can reach)",
        expect_output_contains=["FAIL obligation_routes_reachable",
                                "planted_dead_route"],
        baseline_must_not_contain=["FAIL obligation_routes_reachable"],
    ),
]

# The templated-review mutation cannot be a literal find/replace: each review's
# prose differs per node, so an anchor would have to hardcode four rationales and
# would go stale the moment any node is re-reviewed. It edits the JSON structurally
# instead, and returns the same {path: original_text} map so `_restore` is unchanged.



def _invert_number_line_axis() -> Dict[Path, str]:
    """
    Swap start/end in every number-line payload the formatter builds.

    A find/replace cannot do this: the `"start": start_val, "end": end_val` pair occurs
    three times in the file and the harness (correctly) refuses an anchor that matches
    more than once rather than letting it land somewhere unintended.
    """
    path = REPO_ROOT / "backend/app/practice_gen/formatters/visual/fmt_number_line.py"
    original = path.read_text(encoding="utf-8")
    pair = '"start": start_val,\n            "end": end_val,'
    swapped = '"start": end_val,\n            "end": start_val,'
    if pair not in original:
        raise ValueError(
            "mutation 'inverted_number_line': the start/end payload pair moved in "
            "fmt_number_line.py. Update the anchor rather than loosening it -- a "
            "mutation that no longer reaches the formatter proves nothing about §1G."
        )
    path.write_text(original.replace(pair, swapped), encoding="utf-8")
    return {path: original}


def _plant_inverted_bound() -> Dict[Path, str]:
    """Make get_node_competency_bounds hand back an inverted (min, max) range."""
    path = REPO_ROOT / "backend" / "app" / "practice_gen" / "registry.py"
    original = path.read_text(encoding="utf-8")
    marker = "def get_node_competency_bounds("
    if marker not in original:
        raise ValueError(
            "mutation 'malformed_competency_bound': get_node_competency_bounds moved. "
            "Update the anchor rather than loosening it."
        )
    idx = original.index(marker)
    body_start = original.index("\n", original.index(":", idx)) + 1
    injected = (
        "    # planted mutation: hand back an inverted range\n"
        "    import os as _os\n"
        "    if _os.environ.get('MUTATION_INVERT_BOUND', '1') == '1':\n"
        "        return {'range': (100, 1)}\n"
    )
    path.write_text(original[:body_start] + injected + original[body_start:], encoding="utf-8")
    return {path: original}



def _plant_wildcard_provider(capability: str) -> Dict[Path, str]:
    """
    Rewrite one CAPABILITY_PROVIDERS entry so its only provider is the generic textual
    family -- the August 2026 shape.

    Done by locating the entry rather than by matching its literal text: a real provider
    line carries a 27-key `bounds` catch-all and runs past 600 characters, and an anchor
    that long goes stale on any unrelated edit to the same entry. The locate-and-replace
    still fails loudly if the entry is absent.
    """
    path = REPO_ROOT / "backend/app/practice_gen/validation/validate_capability.py"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^([ \t]*)'{re.escape(capability)}':[^\n]*\n", re.MULTILINE)
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise ValueError(
            f"mutation 'wildcard_provider': found {len(matches)} entries for "
            f"'{capability}' in CAPABILITY_PROVIDERS, expected exactly 1. The table "
            f"moved; repoint the mutation rather than loosening it."
        )
    indent = matches[0]
    replacement = f"{indent}'{capability}': {{'formatters': ['mcq', 'cloze']}},\n"
    path.write_text(pattern.sub(replacement, text, count=1), encoding="utf-8")
    return {path: text}






def _require_fresh_sample(node_id: str, sample: Dict, mutation: str) -> Dict:
    """
    Assert a fixture sample still renders what its record says, and return the render.

    §6F reports the FIRST problem it finds per record and stops. So a fixture whose stem
    has drifted answers with the stem finding no matter what is planted underneath it,
    and the plant is scored SURVIVED even though the check works perfectly. That is
    Scaling Mandate 2's second cause, and it is invisible unless the plant says so:
    `attestation_option_drift` passed on its own and then survived in the full-table run
    after unrelated content work moved mat_g2_na_q2_8's rng stream.

    Raising here converts that into a named failure that tells the next agent exactly
    which fixture moved and what it moved to, instead of a hole reported in the harness
    where the hole is really in the test.
    """
    from backend.app.practice_gen.validation.judgment_packets import _render_sample

    current = _render_sample(node_id, sample["seed"])
    was = " ".join(str(sample.get("question_text", "")).split())
    now = " ".join(str(current.get("question_text", "")).split())
    if was != now:
        raise ValueError(
            f"mutation {mutation!r}: fixture {node_id} seed {sample['seed']} is already "
            f"STALE ON THE STEM, so §6F reports that and never reaches the branch this "
            f"mutation plants in. The check is not what moved -- the content is.\n"
            f"  recorded: {was[:110]!r}\n"
            f"  renders : {now[:110]!r}\n"
            f"Repoint the fixture to a record whose stem still matches."
        )
    return current






def _plant_contradicted_entry(capability: str) -> Dict[Path, str]:
    """
    Put back a provider entry that a filed Attester verdict says does not provide.

    Located rather than literal-matched: the entry is *absent* by design (it was
    deleted on the verdict), so there is no anchor text to match. It is re-inserted
    immediately after the table's opening brace.
    """
    path = REPO_ROOT / "backend/app/practice_gen/validation/validate_capability.py"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^CAPABILITY_PROVIDERS[^\n=]*=\s*\{\n", text, re.MULTILINE)
    marker = m.group(0) if m else ""
    if not marker:
        raise ValueError(
            "mutation 'contradicted_attestation': could not locate the "
            "CAPABILITY_PROVIDERS table opening. The module moved; repoint the mutation."
        )
    if f"'{capability}':" in text:
        raise ValueError(
            f"mutation 'contradicted_attestation': {capability!r} is already registered, "
            f"so re-adding it proves nothing. This mutation requires the entry to be "
            f"absent (deleted on an Attester ruling)."
        )
    injected = marker + f"    '{capability}': {{'variants': [('task_type', 'draw_construct')]}},\n"
    path.write_text(text.replace(marker, injected, 1), encoding="utf-8")
    return {path: text}


def _plant_unsanctioned_requires_ignore() -> Dict[Path, str]:
    """
    Drop a competency word into `requires_ignore` without sanctioning it in the lock.

    This is the cheapest possible way to silence a §6B coverage finding: §6B's own
    message offers two remedies -- "declare the requirement they describe, or list them
    in 'requires_ignore' with the reason" -- and the second costs nothing. Ignoring a
    competency word is a curriculum ruling (docs/pgen_rulings.md R-5, owner 2026-09-11:
    human-authored, verifiable by git history), so the lock file is what makes taking
    that remedy a visible, isolated act instead of a silent one.
    """
    import json

    path = REPO_ROOT / "data" / "skeletons" / "vocab_annotation.json"
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    node = data["nodes"].get(_IGNORE_LOCK_NODE)
    if node is None:
        raise ValueError(
            f"mutation 'unsanctioned_requires_ignore': {_IGNORE_LOCK_NODE} is not in "
            f"vocab_annotation.json. Repoint the fixture."
        )
    planted = "planted_unsanctioned_word"
    ig = node.get("requires_ignore") or []
    if planted in ig:
        raise ValueError(
            f"mutation 'unsanctioned_requires_ignore': {planted!r} is already present, "
            f"so planting it proves nothing."
        )
    node["requires_ignore"] = ig + [planted]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return {path: text}


def _plant_stale_generated_graph() -> Dict[Path, str]:
    """
    Drift the GENERATED graph away from a fresh build of its skeleton, in a field that
    is neither `requires` nor `requires_ignore`.

    Until 2026-09-10 the sync gate compared those two fields alone, and the graph
    checked in at 8cb8dd22 differed from a fresh build in `cumulative_concepts` on 18
    nodes -- the ground truth §1D's NOT_YET_KNOWN gating reads. The gate's own stated
    failure mode ("§6 validates a stale copy, silently and indefinitely") was live on
    disk, one field over from where it was looking.

    Plants a concept the skeleton does not imply, which is the shape the real drift had.
    """
    import json

    path = REPO_ROOT / "data" / "knowledge_graph_g1_3.json"
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    node = data["nodes"].get(_STALE_GRAPH_NODE)
    if node is None or not isinstance(node.get("cumulative_concepts"), list):
        raise ValueError(
            f"mutation 'stale_generated_graph': {_STALE_GRAPH_NODE} carries no "
            f"'cumulative_concepts' list to drift. Repoint the mutation; do not narrow "
            f"the comparison back to two fields."
        )
    node["cumulative_concepts"] = sorted(
        set(node["cumulative_concepts"]) | {"planted_stale_concept"})
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {path: text}


def _plant_orphan_provider() -> Dict[Path, str]:
    """
    Re-add a provider entry under a capability id NO node requires.

    Every other §6 check starts from a node's `requires`, so an orphan entry is read by
    none of them -- never attested, never contradicted, never provision-checked -- while
    sitting ready to pre-approve the first future node whose competency extracts that id.
    `draw_lines` was in exactly this state until 2026-09-10, left behind when
    `draw_line_relationships` was unregistered on an Attester's NOT_PROVIDED ruling.
    """
    path = REPO_ROOT / "backend/app/practice_gen/validation/validate_capability.py"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^CAPABILITY_PROVIDERS[^\n=]*=\s*\{\n", text, re.MULTILINE)
    if not m:
        raise ValueError(
            "mutation 'orphan_provider': could not locate the CAPABILITY_PROVIDERS table "
            "opening. The module moved; repoint the mutation."
        )
    if f"'{_ORPHAN_PROVIDER}':" in text:
        raise ValueError(
            f"mutation 'orphan_provider': {_ORPHAN_PROVIDER!r} is already registered, so "
            f"re-adding it proves nothing. This mutation requires the entry to be absent."
        )
    injected = m.group(0) + (
        f"    '{_ORPHAN_PROVIDER}': "
        f"{{'variants': [('task_type', 'draw_construct')], 'formatters': ['mcq']}},\n"
    )
    path.write_text(text.replace(m.group(0), injected, 1), encoding="utf-8")
    return {path: text}




def _apply(mutation: Mutation) -> Dict[Path, str]:
    """Apply every edit, returning original contents for restoration."""
    if mutation.apply_fn is not None:
        if mutation.edits:
            raise ValueError(
                f"mutation '{mutation.name}': declares both `edits` and `apply_fn`. "
                f"Pick one -- two restore paths is how a mutation harness leaves the "
                f"tree dirty."
            )
        return mutation.apply_fn()
    originals: Dict[Path, str] = {}
    for rel, (find, replace) in mutation.edits.items():
        path = REPO_ROOT / rel
        if not path.exists():
            raise FileNotFoundError(
                f"mutation '{mutation.name}': target file '{rel}' does not exist. "
                f"The mutation harness is stale relative to the tree."
            )
        text = path.read_text(encoding="utf-8")
        count = text.count(find)
        if count != 1:
            raise ValueError(
                f"mutation '{mutation.name}': anchor for '{rel}' matched {count} times, expected "
                f"exactly 1. The source moved; update the anchor rather than loosening it.\n"
                f"  anchor: {find!r}"
            )
        originals[path] = text
        path.write_text(text.replace(find, replace), encoding="utf-8")
    return originals



# ---------------------------------------------------------------------------------
# Kill-safe restore.
#
# `run_mutation` restores in a `finally`, which covers exceptions and clean exits and
# nothing else. On 2026-08-26 a 10-minute tool timeout sent SIGTERM mid-mutation and the
# `finally` never ran: `orchestrator.py` was left carrying
# `if formatter == 'true_false': valid_dnas = []` and had to be restored from git by
# hand. A harness that plants bugs in real source MUST NOT be able to leave one behind --
# the next run would then measure a tree it silently corrupted.
#
# Three layers, because each covers what the others cannot:
#   * signal handlers (SIGTERM/SIGINT) -- the timeout and Ctrl-C cases;
#   * atexit -- any other interpreter shutdown;
#   * an on-disk marker holding the ORIGINAL text -- SIGKILL, power loss, OOM, where no
#     handler runs at all. The next start finds it and restores before doing anything.
# ---------------------------------------------------------------------------------

_IN_FLIGHT: Dict[Path, str] = {}
_MARKER = REPO_ROOT / "local_only" / "scratch" / "MUTATION_IN_FLIGHT.json"


def _write_marker() -> None:
    """Persist what is planted, so a kill -9 is still recoverable."""
    import json
    _MARKER.parent.mkdir(parents=True, exist_ok=True)
    _MARKER.write_text(
        json.dumps({str(k): v for k, v in _IN_FLIGHT.items()}, ensure_ascii=False),
        encoding="utf-8",
    )


def _clear_marker() -> None:
    _MARKER.unlink(missing_ok=True)


def _restore_in_flight(reason: str) -> None:
    if not _IN_FLIGHT:
        _clear_marker()
        return
    print(f"\n!! {reason}: restoring {len(_IN_FLIGHT)} planted file(s) before exit",
          file=sys.stderr)
    for path, text in _IN_FLIGHT.items():
        try:
            path.write_text(text, encoding="utf-8")
        except OSError as exc:  # say which file is still dirty; never swallow it
            print(f"!! COULD NOT RESTORE {path}: {exc}", file=sys.stderr)
    _IN_FLIGHT.clear()
    _clear_marker()


def recover_orphaned_mutation() -> bool:
    """
    Restore a mutation a previous run was killed before undoing. Returns True if it did.

    Runs before anything else in main(): measuring a tree that still carries a planted
    bug is worse than not measuring at all, because every result would look like a real
    finding.
    """
    import json
    if not _MARKER.exists():
        return False
    try:
        planted = json.loads(_MARKER.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise SystemExit(
            f"FATAL: {_MARKER} exists but is unreadable ({exc}). A previous run was killed "
            f"mid-mutation and the tree may still carry a planted bug. Restore the files "
            f"named in git status by hand, delete the marker, and re-run."
        )
    if not planted:
        _clear_marker()
        return False
    print(f"!! a previous run was killed mid-mutation; restoring {len(planted)} file(s)",
          file=sys.stderr)
    for path_str, text in planted.items():
        target = Path(path_str)
        # Display only -- a path outside the repo must not abort the restore. Crashing
        # while recovering is the worst possible moment to crash: it leaves the tree
        # planted AND the marker in place.
        try:
            shown = target.relative_to(REPO_ROOT)
        except ValueError:
            shown = target
        print(f"   restoring {shown}", file=sys.stderr)
        target.write_text(text, encoding="utf-8")
    _clear_marker()
    return True


def _install_kill_safety() -> None:
    import atexit
    import signal

    atexit.register(lambda: _restore_in_flight("interpreter exiting"))

    def _handler(signum, _frame):
        _restore_in_flight(f"received signal {signum}")
        raise SystemExit(128 + signum)

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(sig, _handler)
        except (ValueError, OSError):
            pass  # not the main thread, or the platform lacks it


def _restore(originals: Dict[Path, str]) -> None:
    for path, text in originals.items():
        path.write_text(text, encoding="utf-8")
        _IN_FLIGHT.pop(path, None)
    _write_marker() if _IN_FLIGHT else _clear_marker()


def _run(mutation: Mutation) -> Tuple[int, str]:
    proc = subprocess.run(
        _ENV_PREFIX + mutation.command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _marker_present(marker: str, output: str) -> bool:
    """A plain substring, or -- with ' && ' -- several substrings on the SAME line."""
    if " && " not in marker:
        return marker in output
    parts = [p for p in marker.split(" && ") if p]
    return any(all(p in line for p in parts) for line in output.splitlines())


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def run_mutation(mutation: Mutation) -> Tuple[bool, str]:
    """
    Apply, run, restore. Returns (detected, evidence-line).

    Kept as the two-value entry point callers already use; `run_mutation_recorded`
    carries the full result. Detection means the validator exited non-zero *and*, where
    the mutation declares them, its output carried the expected markers — an unrelated
    crash is not proof the assertion works.
    """
    result = run_mutation_recorded(mutation)
    return result["detected"], result["diagnostic_line"]


def run_mutation_recorded(mutation: Mutation) -> Dict[str, Any]:
    """
    Apply, run, restore — and record everything a proof record needs to be checkable.

    The returned dict is the proof record MINUS the digests the caller adds after
    restoration (`input_digest`), because a digest taken while a bug is planted describes
    a tree that only existed for the length of the run.

    `restored_clean` is observed, not assumed: every planted file is read back and
    compared against the text this runner saved before planting. A `finally` that ran is
    not evidence that a write succeeded, and the one thing a harness that edits real
    source may never do is leave one behind quietly.
    """
    record: Dict[str, Any] = {
        "schema_version": mutation_proof.SCHEMA_VERSION,
        "mutation": mutation.name,
        "definition_digest": mutation_proof.definition_digest(mutation),
        "asserts": sorted(mutation.asserts or ()),
        "command": list(mutation.command),
        "expected_check": mutation.expected_check,
        "expect_output_contains": list(mutation.expect_output_contains or ()),
        "baseline_must_not_contain": list(mutation.baseline_must_not_contain or ()),
        "baseline_exit": None,
        "baseline_markers_already_present": [],
        "planted_exit": None,
        "observed_markers": {},
        "diagnostic_line": "",
        "detected": False,
        "mutated_paths": [],
        "restored_clean": False,
        "environment": mutation_proof.environment_fingerprint(),
        "started_at": _now(),
        "finished_at": None,
    }

    # A validator that is already failing will "detect" anything. Prove the marker
    # is absent before planting, or the mutation proves nothing about the check.
    if mutation.baseline_must_not_contain:
        base_code, before = _run(mutation)
        record["baseline_exit"] = base_code
        already = [m for m in mutation.baseline_must_not_contain
                   if _marker_present(m, before)]
        record["baseline_markers_already_present"] = already
        if already:
            record["diagnostic_line"] = (
                f"INVALID — the unmutated tree already reports {already}; this mutation "
                f"cannot distinguish the planted bug from the pre-existing failure."
            )
            record["restored_clean"] = True   # nothing was planted
            record["finished_at"] = _now()
            return record

    originals: Dict[Path, str] = {}
    try:
        originals = _apply(mutation)
        _IN_FLIGHT.update(originals)
        _write_marker()
        record["mutated_paths"] = sorted(mutation_proof._rel(p) for p in originals)
        code, output = _run(mutation)
        record["planted_exit"] = code
    finally:
        if originals:
            _restore(originals)
            record["restored_clean"] = all(
                path.exists() and path.read_text(encoding="utf-8") == text
                for path, text in originals.items()
            )
        else:
            record["restored_clean"] = True

    record["observed_markers"] = {
        m: _marker_present(m, output) for m in mutation.expect_output_contains
    }
    record["finished_at"] = _now()

    if code == 0:
        record["diagnostic_line"] = "SURVIVED — validator exited 0 with the bug planted."
        return record

    missing = [m for m, seen in record["observed_markers"].items() if not seen]
    if missing:
        record["diagnostic_line"] = (
            f"exited {code} but output lacked expected marker(s): {missing}"
        )
        return record

    record["detected"] = True
    record["diagnostic_line"] = f"exit {code} — {_first_failure_line(output)}"
    return record


def _first_failure_line(output: str) -> str:
    """Pull the first line that reads like a failure, for the evidence table."""
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if any(tok in low for tok in ("fail", "error", "drift", "traceback", "raise")):
            return line[:220]
    return output.strip().splitlines()[-1][:220] if output.strip() else "(no output)"


def main() -> int:
    ap = argparse.ArgumentParser(description="Mutation-test the pg validation harness.")
    ap.add_argument("--only", help="Run a single mutation by name.")
    ap.add_argument("--list", action="store_true", help="List mutation names and exit.")
    args = ap.parse_args()

    # Before anything: undo a mutation a killed run left planted, and arm the handlers
    # so this run cannot leave one either.
    recover_orphaned_mutation()
    _install_kill_safety()

    if args.list:
        for m in MUTATIONS:
            print(f"{m.name:24s} {m.description}")
        return 0

    selected = MUTATIONS
    if args.only:
        selected = [m for m in MUTATIONS if m.name == args.only]
        if not selected:
            print(f"No mutation named '{args.only}'. Use --list.")
            return 2

    print("=" * 78)
    print(f"MUTATION TESTING THE VALIDATION HARNESS ({len(selected)} mutation(s))")
    print("=" * 78)

    # Most mutations invoke `validate_matrix --node X`, and a single-node run REPLACES
    # validation_reports/matrix_report.json with a report covering that one node. The
    # hardening supervisor reads that file as its §1 evidence, so an unguarded mutation
    # run silently destroys tree-wide §1 coverage and leaves the queue unmeasurable.
    # Snapshot it here and put it back, the same way file edits are restored.
    _matrix_report = REPO_ROOT / "validation_reports" / "matrix_report.json"
    _matrix_backup = _matrix_report.read_bytes() if _matrix_report.exists() else None

    # The digest of the tree the proofs describe, taken on a CLEAN tree before anything
    # is planted. Re-taken after every mutation: a run that cannot restore the bytes it
    # started from has no business publishing evidence about them.
    clean_digest = mutation_proof.input_digest()
    print(f"\ninput digest (clean tree): {clean_digest[:16]}  "
          f"proofs -> {mutation_proof.PROOF_DIR.relative_to(REPO_ROOT)}/")

    results: List[Tuple[Mutation, bool, str]] = []
    unpublished: List[str] = []
    try:
        for i, m in enumerate(selected, 1):
            print(f"\n[{i}/{len(selected)}] {m.name}: {m.description}")
            print(f"    expected catcher: {m.expected_check}")
            record = run_mutation_recorded(m)
            detected, evidence = record["detected"], record["diagnostic_line"]
            results.append((m, detected, evidence))
            print(f"    {'DETECTED' if detected else 'SURVIVED'}: {evidence}")

            # Publish only after restoration, and only once the tree is byte-identical to
            # the one the digest describes. Anything else and the proof would bind a
            # result to source that is not what ran.
            after = mutation_proof.input_digest()
            if after != clean_digest:
                unpublished.append(m.name)
                print(f"    !! PROOF NOT PUBLISHED: the input tree changed during this "
                      f"mutation ({clean_digest[:12]} -> {after[:12]}). The tree was not "
                      f"restored to the bytes the run started from, or another process "
                      f"edited it. Nothing in validation_reports/mutation_proofs/ was "
                      f"written for {m.name}.", file=sys.stderr)
                continue
            outside = mutation_proof.paths_outside_input_set(record["mutated_paths"])
            record["input_digest"] = clean_digest
            record["paths_outside_input_set"] = outside
            record["phase1_admissible"] = not outside
            path = mutation_proof.write_proof(record)
            if outside:
                print(f"    proof filed (NOT Phase-1 admissible: edits {outside}) "
                      f"-> {path.relative_to(REPO_ROOT)}")
    finally:
        if _matrix_backup is None:
            _matrix_report.unlink(missing_ok=True)
        else:
            _matrix_report.write_bytes(_matrix_backup)

    print("\n" + "=" * 78)
    print("MUTATION SUMMARY")
    print("=" * 78)
    for m, detected, evidence in results:
        print(f"  {'PASS' if detected else 'FAIL'}  {m.name:24s} {m.expected_check}")
    caught = sum(1 for _, d, _ in results if d)
    print(f"\n{caught}/{len(results)} mutations detected.")
    if unpublished:
        print(f"\n!! {len(unpublished)} proof(s) NOT published because the tree moved "
              f"under them: {unpublished}. §8 will report the affected assertions as "
              f"unproven until those mutations are re-run on a quiet tree.")
        return 1
    if caught != len(results):
        print("A surviving mutation is a hole in the harness, not a harmless gap:")
        for m, detected, _ in results:
            if not detected:
                print(f"  - {m.name}: nothing enforces {m.expected_check}")
        return 1
    print("Praise God — the verifier verifies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
