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
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

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


def _plant_template_attestation(count: int) -> Dict[Path, str]:
    """
    Overwrite one record's verdict reasoning with a per-clause fill-in of one frame.

    This is the §5 fabrication shape aimed at the surface that is now four times
    larger. §6F cannot see it: the packet is untouched, so freshness still passes,
    the verdicts still exist, and nothing contradicts them. Only §6G reads the
    reasoning.

    The record is chosen for having `count` verdicts it still *owns* -- a superseded
    record is exempt from §6G by design, so planting in one would prove nothing.
    """
    import json

    d = REPO_ROOT / "validation_reports" / "attestation"
    records = sorted(d.glob("*.json"))
    if not records:
        raise FileNotFoundError(
            "mutation 'template_attestation': no attestation records to template. File "
            "at least one Attester verdict before claiming §6G works."
        )
    # Replay last-file-wins so we plant in verdicts that are actually live.
    owner: Dict[tuple, Path] = {}
    for path in records:
        for v in json.loads(path.read_text(encoding="utf-8")).get("verdicts", []):
            owner[(v.get("node_id"), v.get("capability_id"))] = path

    for path in records:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        live = [v for v in data.get("verdicts", [])
                if owner.get((v.get("node_id"), v.get("capability_id"))) == path]
        if len(live) < count:
            continue
        for v in live[:count]:
            seed = (v.get("seeds_showing_it") or [0])[0]
            v["reasoning"] = (
                f"Seed {seed} plainly exhibits '{v.get('clause')}' across the sample set."
            )
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return {path: text}

    raise ValueError(
        f"mutation 'template_attestation': no record owns {count} live verdicts, so the "
        f"skeleton cluster cannot exceed its cap. Repoint the mutation rather than "
        f"lowering _MAX_ATTESTER_SKELETON_CLUSTER."
    )


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


MUTATIONS: List[Mutation] = [
    Mutation(
        name="leaky_window",
        asserts=['scalar_boundary_containment'],
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
        asserts=['scalar_boundary_exactness'],
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
                "\n        correct_answer=ctx.correct_answer,\n",
                "\n        correct_answer=(ctx.correct_answer + 1)\n"
                "        if isinstance(ctx.correct_answer, int) and not isinstance(ctx.correct_answer, bool)\n"
                "        else ctx.correct_answer,\n",
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
        asserts=['manifest_registry_assertion'],
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
        name="stale_attestation",
        asserts=['capability_stale_attestation_6F'],
        description=(
            "Drift the content an Attester judged, leaving the verdict on file. Without a "
            "freshness pass the contract has a permanent hole: attest everything once, "
            "then change generators freely, and run_all keeps exiting 0 on evidence about "
            "content that no longer exists."
        ),
        edits={},
        apply_fn=lambda: _drift_attested_content(),
        command=["backend.app.practice_gen.validation.validate_capability"],
        expected_check="§6F freshness (attestation is about content that still exists)",
        expect_output_contains=["STALE && planted drift"],
        baseline_must_not_contain=["planted drift"],
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
        edits={},
        apply_fn=lambda: _plant_template_rationale(4),
        command=["backend.app.practice_gen.validation.validate_judgment"],
        expected_check="§5 (rationale-skeleton clustering)",
        expect_output_contains=["template rationale", "share one findings"],
        baseline_must_not_contain=["template rationale"],
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
        edits={},
        apply_fn=lambda: _plant_template_attestation(4),
        command=["backend.app.practice_gen.validation.validate_capability"],
        expected_check="§6G (attester reasoning-skeleton clustering)",
        expect_output_contains=["attester boilerplate (§6G) && share one normalized"],
        baseline_must_not_contain=["attester boilerplate (§6G)"],
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
        asserts=['suite_census_7'],
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
        edits={
            "backend/app/practice_gen/formatters/visual/fmt_place_value_blocks.py": (
                '    format_data: dict = {"visual_params": vp}\n',
                '    vp = {k: v for k, v in vp.items() if k != "total_value"}  # planted mutation\n'
                '    format_data: dict = {"visual_params": vp}\n',
            )
        },
        command=["backend.app.practice_gen.validation.validate_render",
                 "--node-ids", "mat_g1_na_q1_2"],
        expected_check="§9 (the payload must be renderable by the component the student sees)",
        expect_output_contains=["FAIL render_contract", "total_value"],
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
        expect_output_contains=["FAIL assertion_coverage", "worker_crash"],
        baseline_must_not_contain=["FAIL assertion_coverage"],
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
                "        correct_answer=ctx.correct_answer,\n        distractors=distractors,",
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
        asserts=["answer_leak_in_stem_declared"],
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
]


# The templated-review mutation cannot be a literal find/replace: each review's
# prose differs per node, so an anchor would have to hardcode four rationales and
# would go stale the moment any node is re-reviewed. It edits the JSON structurally
# instead, and returns the same {path: original_text} map so `_restore` is unchanged.
_TEMPLATE_RATIONALE = (
    "The items for {node_id} were reviewed against the competency and found to "
    "address it directly. The number ranges observed are appropriate for the grade "
    "and quarter, the vocabulary stays within what has been introduced, and the "
    "answer keys are correct throughout. No issues were identified for {node_id}."
)



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


def _drift_attested_content() -> Dict[Path, str]:
    """Change the rendered text an attestation records, as a generator change would."""
    import json
    from backend.app.practice_gen.validation import validate_capability as VC

    d = REPO_ROOT / "validation_reports" / "attestation"
    records = sorted(d.glob("*.json"))
    if not records:
        raise FileNotFoundError(
            "mutation 'stale_attestation': no attestation records to drift. File at "
            "least one Attester verdict before claiming the freshness pass works."
        )
    all_records = [json.loads(p.read_text(encoding="utf-8")) for p in records]
    winner = VC._winning_verdict_index(all_records)
    target = None
    target_data = None
    for idx, path in enumerate(records):
        rec = all_records[idx]
        verdict_pairs = [(v.get("node_id"), v.get("capability_id")) for v in rec.get("verdicts", [])]
        if verdict_pairs and any(winner.get(pair) == idx for pair in verdict_pairs):
            packet = rec.get("packet") or {}
            node_id = packet.get("node_id")
            judged = packet.get("samples_judged")
            if node_id and judged:
                target = path
                target_data = rec
                break
    if target is None:
        raise ValueError(
            "mutation 'stale_attestation': could not find an active winning attestation record to drift."
        )
    original_text = target.read_text(encoding="utf-8")
    target_data["packet"]["samples_judged"][0]["question_text"] = "planted drift: a stem the pipeline never rendered"
    target.write_text(json.dumps(target_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {target: original_text}


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


def _plant_template_rationale(n_nodes: int) -> Dict[Path, str]:
    """
    Overwrite `findings.competency_fulfillment.rationale` on `n_nodes` reviews with
    one shared template, node ID substituted in.

    n_nodes must exceed validate_judgment._MAX_SKELETON_CLUSTER, or the planted
    template is *within* the tolerance the check deliberately allows for sibling
    nodes and its survival would say nothing. Read the threshold rather than
    assuming it, so tightening the check cannot silently invalidate this mutation.
    """
    import json

    from backend.app.practice_gen.validation.validate_judgment import _MAX_SKELETON_CLUSTER

    if n_nodes <= _MAX_SKELETON_CLUSTER:
        raise ValueError(
            f"mutation 'template_review': planting {n_nodes} templated rationales cannot "
            f"trip a check that tolerates {_MAX_SKELETON_CLUSTER}. Plant more than the "
            f"threshold -- never lower the threshold to suit the mutation."
        )

    review_dir = REPO_ROOT / "validation_reports" / "judgment"
    targets = sorted(review_dir.rglob("*.json"))[:n_nodes]
    if len(targets) < n_nodes:
        raise FileNotFoundError(
            f"mutation 'template_review': needed {n_nodes} review files under "
            f"'{review_dir}', found {len(targets)}. The mutation harness is stale "
            f"relative to the tree."
        )

    originals: Dict[Path, str] = {}
    for path in targets:
        text = path.read_text(encoding="utf-8")
        originals[path] = text
        data = json.loads(text)
        node_id = data.get("node_id", path.stem)
        data["findings"]["competency_fulfillment"]["rationale"] = (
            _TEMPLATE_RATIONALE.format(node_id=node_id)
        )
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return originals


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


def run_mutation(mutation: Mutation) -> Tuple[bool, str]:
    """
    Apply, run, restore. Returns (detected, evidence-line).

    Detection means the validator exited non-zero *and*, where the mutation
    declares them, its output carried the expected markers — an unrelated crash
    is not proof the assertion works.
    """
    # A validator that is already failing will "detect" anything. Prove the marker
    # is absent before planting, or the mutation proves nothing about the check.
    if mutation.baseline_must_not_contain:
        _, before = _run(mutation)
        already = [m for m in mutation.baseline_must_not_contain
                   if _marker_present(m, before)]
        if already:
            return False, (
                f"INVALID — the unmutated tree already reports {already}; this mutation "
                f"cannot distinguish the planted bug from the pre-existing failure."
            )

    originals: Dict[Path, str] = {}
    try:
        originals = _apply(mutation)
        _IN_FLIGHT.update(originals)
        _write_marker()
        code, output = _run(mutation)
    finally:
        if originals:
            _restore(originals)

    if code == 0:
        return False, "SURVIVED — validator exited 0 with the bug planted."

    missing = [m for m in mutation.expect_output_contains if not _marker_present(m, output)]
    if missing:
        return False, f"exited {code} but output lacked expected marker(s): {missing}"

    line = _first_failure_line(output)
    return True, f"exit {code} — {line}"


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

    results: List[Tuple[Mutation, bool, str]] = []
    try:
        for i, m in enumerate(selected, 1):
            print(f"\n[{i}/{len(selected)}] {m.name}: {m.description}")
            print(f"    expected catcher: {m.expected_check}")
            detected, evidence = run_mutation(m)
            results.append((m, detected, evidence))
            print(f"    {'DETECTED' if detected else 'SURVIVED'}: {evidence}")
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
