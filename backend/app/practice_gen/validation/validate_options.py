"""
§1K — option degeneracy: a choice item must offer choices a pupil can tell apart, and
exactly one of them may answer the question.

WHAT THIS CHECKS, EXACTLY
-------------------------
Three bounded, mechanical properties of the option set a pupil is actually shown:

  1. **Indistinguishable choices.** Two options that render the same text. Whatever the
     task is, a menu with the same entry twice is a four-option item pretending to be one.
  2. **More than one option satisfies the request.** Another option carries the exact
     same typed value as the keyed answer, so a pupil who picks it is right and is marked
     wrong.
  3. **More than one option flagged correct.** The `is_correct` flags disagree with the
     single-answer contract the grader assumes.

WHAT IT DELIBERATELY DOES NOT GATE, AND WHY
-------------------------------------------
**Equal-valued DISTRACTORS.** Measured 2026-09-12 on 1180 option-bearing student-path
samples: seven items offer two distractors of equal value — `mat_g1_na_q4_2` puts `1/2`
and `2/4` in the same menu, `mat_g3_na_q4_7` puts `1/10` and `2/20`. Neither equals its
keyed answer, so neither item is ambiguous: `What comes next when counting by halves: 1/2,
___?` is keyed `2/2`, and both `2/4` and `1/2` are wrong for the same reason a pupil is
meant to see. A task that asks for a particular REPRESENTATION may legitimately offer
equal-valued representations among its distractors, and a blanket ban would be this gate
inventing a rule the curriculum does not state (Content Rule 4). The count is measured and
printed on every run, so the decision stays visible rather than silent. What is NOT
tolerated is the same shape touching the KEY — that is case 2 and it gates.

There is no per-formatter or per-representation exclusion list. A representation task is
recognised by what it does (its key), not by a name on an allowlist.

HOW VALUES ARE COMPARED
-----------------------
Exactly and by type. `Fraction` for `a/b` and for decimal strings, `int` for integers —
never a float, because `0.1 + 0.2` deciding whether two options are the same answer is not
a property anyone should have to reason about. A trailing unit is parsed and kept: `5 cm`
and `5 m` are NOT equal, and `5 cm` equals only `5 cm` (or `5cm`). Anything that does not
parse as a number-with-optional-unit is compared as normalised text and nothing more; no
symbolic equivalence is guessed at.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
1. **Unsupported equivalence domains are counted, not assumed correct.** Two options that
   mean the same thing in a domain this module cannot parse — `3:30` and `half past
   three`, two different coin sets making ₱27, two drawings of the same shape — are
   reported in the run summary as unjudged pairs. They remain judgment-review work
   (docs/pgen_judgment.md), and a future formatter that introduces such a domain must
   either register how to compare its values or accept that this gate does not cover it.
   It will not be silently covered by a widened guess.
2. It does not check that the keyed answer appears among the options at all; that is §1E's
   answer-key integrity, on the same render.
3. It reads the option VALUES. An option whose distinguishing content is in a picture is
   outside what this module can see.
"""

from __future__ import annotations

import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[4]

# §8 inventory: the assertions this module can independently fail on.
ASSERTIONS = (
    "option_degeneracy_1K",
)

# Seeds 1..60 on every node: 9060 student-path samples, measured at ~65s for the whole
# tree. Chosen against the defects this gate was built on rather than for round numbers --
# the ten stratified seeds the packet builder uses would have MISSED `Shade 1 groups of 1
# squares` entirely, which lands on seeds 12 and 40 of `mat_g2_na_q3_0`. A cheap check
# that samples too thinly is a gate that reports green about seeds it never rendered.
SEEDS_PER_NODE: Tuple[int, ...] = tuple(range(1, 61))

# <number><optional unit>. The unit is kept, never stripped: `5 cm` and `5 m` are
# different answers and a gate that erased the unit would call them the same.
_NUMBER_UNIT = re.compile(
    r"^\s*(?P<sign>[-−])?\s*(?P<cur>[₱$])?\s*(?P<num>\d+(?:\s*/\s*\d+|\.\d+)?)\s*(?P<unit>[A-Za-z¢%]*)\s*$"
)


def typed_value(raw: Any) -> Optional[Tuple[Fraction, str]]:
    """
    (exact value, unit) for an option that parses as a number with an optional unit.

    None when it does not parse — the caller then compares it as text and counts it as an
    unjudged domain rather than guessing at equivalence.
    """
    if isinstance(raw, bool):
        return None                      # True/False is not a quantity
    if isinstance(raw, int):
        return Fraction(raw), ""
    if isinstance(raw, Fraction):
        return raw, ""
    text = str(raw).replace(",", "").strip()
    m = _NUMBER_UNIT.match(text)
    if not m:
        return None
    num = m.group("num").replace(" ", "")
    try:
        value = Fraction(num)
    except (ValueError, ZeroDivisionError):
        return None
    if m.group("sign"):
        value = -value
    unit = (m.group("cur") or "") + (m.group("unit") or "").lower()
    return value, unit


def _normalised_text(raw: Any) -> str:
    return " ".join(str(raw).split()).strip().lower()


def _options(problem: Dict[str, Any]) -> Optional[List[Any]]:
    """
    The option list as the pupil is shown it, using the packet builder's own extraction.

    `mcq_options` or `options` — the same order `judgment_packets._render_sample` uses, so
    a §1K finding and a review packet are talking about the same menu.
    """
    fd = problem.get("format_data")
    if not isinstance(fd, dict):
        return None
    opts = fd.get("mcq_options") or fd.get("options")
    return opts if isinstance(opts, list) and opts else None


def scan_options(opts: List[Any], correct_answer: Any) -> Tuple[List[str], int, int]:
    """
    (violations, equal_valued_distractor_pairs, unjudged_pairs) for one option set.
    """
    values = [o.get("value") if isinstance(o, dict) else o for o in opts]
    texts = [_normalised_text(v) for v in values]
    typed = [typed_value(v) for v in values]

    violations: List[str] = []

    # 1. indistinguishable choices
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if texts[i] and texts[i] == texts[j]:
                violations.append(
                    f"options {i} and {j} render the same text {values[i]!r}; a menu with "
                    f"the same entry twice offers fewer choices than it shows"
                )

    # 2. more than one option satisfies the request
    keyed_indices = [i for i, o in enumerate(opts)
                     if isinstance(o, dict) and o.get("is_correct")]
    key_typed = typed_value(correct_answer)
    key_text = _normalised_text(correct_answer)
    satisfying: List[int] = []
    for i, (t, ty) in enumerate(zip(texts, typed)):
        if key_typed is not None and ty is not None:
            if ty == key_typed:
                satisfying.append(i)
        elif t and t == key_text:
            satisfying.append(i)
    if len(satisfying) > 1:
        violations.append(
            f"options {satisfying} all carry the keyed answer's exact value "
            f"({[values[i] for i in satisfying]} against key {correct_answer!r}); a pupil "
            f"who picks the wrong one of them is right and is marked wrong"
        )

    # 3. more than one option flagged correct
    if len(keyed_indices) > 1:
        violations.append(
            f"options {keyed_indices} are all flagged is_correct "
            f"({[values[i] for i in keyed_indices]}); the grader assumes exactly one"
        )

    # measured, not gated -- see the module docstring
    equal_distractors = 0
    unjudged = 0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if i in satisfying or j in satisfying:
                continue
            if typed[i] is not None and typed[j] is not None:
                if typed[i] == typed[j] and texts[i] != texts[j]:
                    equal_distractors += 1
            elif texts[i] != texts[j]:
                unjudged += 1
    return violations, equal_distractors, unjudged


def collect_findings(node_ids: Optional[List[str]] = None) -> Tuple[List[str], Dict[str, int]]:
    sys.path.insert(0, str(REPO_ROOT))
    from backend.app.practice_gen.registry import get_all_node_ids
    from backend.app.services.orchestrator import PracticeOrchestrator

    findings: List[str] = []
    stats = {"samples": 0, "option_items": 0, "equal_valued_distractor_pairs": 0,
             "unjudged_pairs": 0, "render_failures": 0}
    for node_id in (node_ids or get_all_node_ids()):
        for seed in SEEDS_PER_NODE:
            try:
                problem = PracticeOrchestrator.generate_problem(
                    node_id=node_id, seed=seed, is_student_path=True
                )
            except Exception as exc:  # noqa: BLE001 -- named, never a silent skip
                stats["render_failures"] += 1
                findings.append(
                    f"{node_id}: seed {seed} could not be rendered on the student path "
                    f"({type(exc).__name__}: {exc}), so its options were never checked."
                )
                continue
            d = problem if isinstance(problem, dict) else problem.__dict__
            stats["samples"] += 1
            opts = _options(d)
            if opts is None:
                continue
            stats["option_items"] += 1
            bad, equal_d, unjudged = scan_options(opts, d.get("correct_answer"))
            stats["equal_valued_distractor_pairs"] += equal_d
            stats["unjudged_pairs"] += unjudged
            for v in bad:
                findings.append(f"{node_id}: seed {seed} {v}. Options: {opts}")
    return findings, stats


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    findings, stats = collect_findings(node_ids)
    if findings:
        print(f"  FAIL option_degeneracy_1K ({len(findings)}):")
        for f in findings[:12]:
            print(f"    - {f[:400]}")
        if len(findings) > 12:
            print(f"    ... and {len(findings) - 12} more.")
        return False
    print(f"  PASS option_degeneracy_1K: 0 findings over {stats['option_items']} "
          f"option-bearing sample(s) of {stats['samples']}; "
          f"{stats['equal_valued_distractor_pairs']} equal-valued DISTRACTOR pair(s) "
          f"observed and NOT gated (see docstring), {stats['unjudged_pairs']} pair(s) in "
          f"an equivalence domain this gate cannot compare")
    return True


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§1K option degeneracy")
    ap.add_argument("--node-ids", help="comma-separated subset")
    args = ap.parse_args()
    nodes = args.node_ids.split(",") if args.node_ids else None
    return 0 if validate_all(nodes) else 1


if __name__ == "__main__":
    sys.exit(main())
