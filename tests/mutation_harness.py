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
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
                "        correct_answer=ctx.correct_answer,\n",
                "        correct_answer=(ctx.correct_answer + 1)\n"
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
]


def _apply(mutation: Mutation) -> Dict[Path, str]:
    """Apply every edit, returning original contents for restoration."""
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


def run_mutation(mutation: Mutation) -> Tuple[bool, str]:
    """
    Apply, run, restore. Returns (detected, evidence-line).

    Detection means the validator exited non-zero *and*, where the mutation
    declares them, its output carried the expected markers — an unrelated crash
    is not proof the assertion works.
    """
    originals: Dict[Path, str] = {}
    try:
        originals = _apply(mutation)
        code, output = _run(mutation)
    finally:
        if originals:
            _restore(originals)

    if code == 0:
        return False, "SURVIVED — validator exited 0 with the bug planted."

    missing = [m for m in mutation.expect_output_contains if m not in output]
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
