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


MUTATIONS: List[Mutation] = [
    Mutation(
        name="leaky_window",
        description=(
            "Widen addition's sampled range past the competency ceiling "
            "(sums allowed to exceed max_result by 10)."
        ),
        edits={
            "backend/app/practice_gen/dna/na/addition.py": (
                "                if a + b > max_result:\n",
                "                if a + b > max_result + 10:\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_7"],
        expected_check="§1A/§1B (scalar boundary exactness / window containment)",
    ),
    Mutation(
        name="boundary_off_by_one",
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
        description="Inject a NOT_YET_KNOWN term into generated question text.",
        edits={
            "backend/app/practice_gen/formatters/textual/fmt_mcq.py": (
                "def format_mcq(ctx: QuestionContext, rng: random.Random) -> FormattedProblem:\n",
                "def format_mcq(ctx: QuestionContext, rng: random.Random) -> FormattedProblem:\n"
                "    ctx.question_text = (ctx.question_text or '') + ' Use multiplication to check.'\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_7"],
        expected_check="§1D (vocabulary lint on formatted output)",
    ),
    Mutation(
        name="silent_substitution",
        description=(
            "Make the adapter silently accept an unsupported variant/formatter "
            "combination instead of raising."
        ),
        # Target the orchestrator's DNA-rejection gate, which is what actually
        # refuses an unsupported combination. adapter.py carries a second,
        # redundant raise for the same condition, so patching only that one leaves
        # the pipeline still refusing — the mutation would "survive" while proving
        # nothing about §1C-reverse.
        edits={
            "backend/app/services/orchestrator.py": (
                "                        if not is_variant_supported(d, formatter, var_name, var_val):\n"
                "                            dna_compatible = False\n"
                "                            break\n",
                "                        pass  # planted mutation: silent substitution\n",
            )
        },
        command=["backend.app.practice_gen.validation.validate_matrix", "--node", "mat_g1_na_q1_7"],
        expected_check="§1C-reverse (excluded combinations must raise)",
    ),
    Mutation(
        name="registry_drift",
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
        baseline_must_not_contain=["CONTRADICTED"],
    ),
    Mutation(
        name="stale_attestation",
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
        expect_output_contains=["STALE && re-attest"],
        baseline_must_not_contain=["STALE"],
    ),
    Mutation(
        name="template_review",
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

    d = REPO_ROOT / "validation_reports" / "attestation"
    records = sorted(d.glob("*.json"))
    if not records:
        raise FileNotFoundError(
            "mutation 'stale_attestation': no attestation records to drift. File at "
            "least one Attester verdict before claiming the freshness pass works."
        )
    path = records[0]
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    judged = (data.get("packet") or {}).get("samples_judged")
    if not judged:
        raise ValueError(
            f"mutation 'stale_attestation': {path.name} has no packet.samples_judged, so "
            f"there is nothing to drift. §6F already fails that record for the same reason."
        )
    judged[0]["question_text"] = "planted drift: a stem the pipeline never rendered"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {path: text}


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


def _restore(originals: Dict[Path, str]) -> None:
    for path, text in originals.items():
        path.write_text(text, encoding="utf-8")


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

    results: List[Tuple[Mutation, bool, str]] = []
    for i, m in enumerate(selected, 1):
        print(f"\n[{i}/{len(selected)}] {m.name}: {m.description}")
        print(f"    expected catcher: {m.expected_check}")
        detected, evidence = run_mutation(m)
        results.append((m, detected, evidence))
        print(f"    {'DETECTED' if detected else 'SURVIVED'}: {evidence}")

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
