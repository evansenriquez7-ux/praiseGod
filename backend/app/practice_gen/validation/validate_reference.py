"""
§1M — a stem that POINTS at a display must be served with one.

WHAT THIS CHECKS, EXACTLY
-------------------------
One bounded, mechanical property: where rendered student-facing text uses a DEICTIC
phrase — "Look at the model", "shown below", "in the picture" — the item must actually
draw something (`is_visual` and a `visual_type`). A stem that says "look at the scale"
beside a blank page is not a hard item; it is an unanswerable one, and until 2026-09-19
three nodes served literally unanswerable items for exactly this reason:

    mat_g3_mg_q2_0 seed 1: "What is the mass of the object in g?"        -> 1
    mat_g3_mg_q2_3 seed 1: "What is the capacity of the container in L?" -> 8
    mat_g1_dp_q3_3:        "Count the pictures in each row of the pictograph, then ..."

Those three were found by a SCRATCH PROBE, not by a check. The probe was thrown away, so
the defect class had no gate at all and the finding could not be reproduced — when this
module was written on 2026-09-21 the earlier sweep's own count ("6 nodes") could not be
regenerated, because the cue list that produced it no longer existed anywhere. That is
the argument for this file: a measurement nobody can re-run is not a gate, and the next
grade inherits the hole silently.

DEIXIS, NOT MENTION — and why the distinction is the whole design
------------------------------------------------------------------
The tempting rule is "a stem that names a number line must draw a number line". Measured
on 2026-09-21, that rule flags 11 nodes, and its extra 7 are all false:

    "There are 5 knee pads ON THE TABLE. Des takes away 0 ..."   <- furniture
    "A dot is at 12 ON THE NUMBER LINE. If you move back 2 ..."  <- states the position
    "A composite figure is made of a rectangle with a half-circle attached on top."

Each DESCRIBES its situation and is answerable from its own words. The property that
makes an item depend on a drawing is that it POINTS — deixis presupposes that the thing
pointed at is present. So the pattern below matches pointing phrases only, and a stem
that merely names a mathematical object is left alone. This also keeps the check honest
at grade 7: a rule that demanded a drawing for every named object would force a visual
for algebra stems that have no business carrying one (Mandate 4).

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
1. **Deixis is recognised from a closed list of phrases**, extended by adding a phrase,
   never by loosening the pattern. A stem that points in wording nobody has seen yet is
   NOT caught. The list is printed with the pass line so its size is a number rather
   than an assumption.
2. **It cannot tell whether the drawn visual is the RIGHT one.** An item that says "look
   at the pictograph" and draws a clock passes here; that is §1G's and §9's territory —
   this check asks only whether anything was drawn at all.
3. **It cannot see a display the pupil needs but the stem never mentions.** An item that
   silently assumes a diagram passes, because nothing in the text points at one.
4. **It reads the stem and its nested statements, not the hints.** A hint saying "look
   at the picture" on a non-visual item is not caught; hints are guidance about an item
   whose answerability is decided by the stem.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[4]

# §8 inventory: the assertions this module can independently fail on.
ASSERTIONS = (
    "dangling_visual_reference_1M",
)

# Same sampling as §1J, and for the same reason: a cheap check that samples too thinly
# reports green about seeds it never rendered. The four nodes this gate was built on
# fire on 4 to 11 seeds out of 20, so a ten-seed sample would have missed some of them.
SEEDS_PER_NODE: Tuple[int, ...] = tuple(range(1, 61))

# DEICTIC phrases: wording that presupposes the referent is on the page. Closed and
# explicit (limitation 1). Every entry earns its place from a stem that was measured
# live, not from imagination:
#
#   "look at the ..."        mat_g3_mg_q1_4/_5 (the model), mat_g2_mg_q4_2 (the
#                            schedule), mat_g1_na_q4_1 (the fraction models)
#   "count the pictures"     mat_g1_dp_q3_3, which instructed the pupil to count a
#                            pictograph the item did not draw
#   "shown below/above"      the general form of the same promise
_DEICTIC = re.compile(
    r"\blook at (?:the|this)\b"
    r"|\b(?:shown|drawn|pictured) (?:below|above|here)\b"
    r"|\bin the (?:picture|pictograph|picture graph|graph|chart|diagram|figure|model|array|grid)\b"
    r"|\bcount the (?:pictures|symbols|pictures in)\b"
    r"|\buse the (?:picture|graph|chart|diagram|table|scale|ruler|clock) (?:below|above|shown)\b"
    r"|\b(?:the|this) (?:picture|pictograph|picture graph|graph|chart|diagram|figure|model|array|grid|table) (?:below|above|shown)\b",
    re.IGNORECASE,
)


def deictic_phrases(text: str) -> List[str]:
    """Every pointing phrase in one string. Empty when it points at nothing."""
    return [m.group(0) for m in _DEICTIC.finditer(text or "")]


def _stem_texts(problem: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    The text whose deixis decides answerability: the stem and its nested statements.

    Deliberately NOT the hints (limitation 4) and not the options: an option reading
    "the one shown" is odd but does not make the item unanswerable on its own.
    """
    out: List[Tuple[str, str]] = []
    stem = problem.get("question_text")
    if stem:
        out.append(("question_text", str(stem)))
    fd = problem.get("format_data")
    if isinstance(fd, dict):
        for key in ("prompt", "statement", "cloze_template"):
            val = fd.get(key)
            if isinstance(val, str) and val:
                out.append((f"format_data.{key}", val))
    return out


def _draws_something(problem: Dict[str, Any]) -> bool:
    """
    Whether this item puts a display on the page.

    BOTH fields, not either: `is_visual` is a claim and `visual_type` is what the
    renderer actually switches on, so an item carrying one without the other draws
    nothing while reporting that it does.
    """
    return bool(problem.get("is_visual")) and bool(problem.get("visual_type"))


def collect_findings(node_ids: Optional[List[str]] = None) -> Tuple[List[str], Dict[str, int]]:
    """Every (node, seed) whose stem points at a display the item never draws."""
    sys.path.insert(0, str(REPO_ROOT))
    from backend.app.practice_gen.registry import get_all_node_ids
    from backend.app.services.orchestrator import PracticeOrchestrator

    findings: List[str] = []
    stats = {"samples": 0, "render_failures": 0, "deictic_samples": 0,
             "deictic_and_drawn": 0}
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
                    f"({type(exc).__name__}: {exc}), so its references were never "
                    f"checked. Reproduce: PracticeOrchestrator.generate_problem("
                    f"node_id='{node_id}', seed={seed}, is_student_path=True)"
                )
                continue
            d = problem if isinstance(problem, dict) else problem.__dict__
            stats["samples"] += 1
            drawn = _draws_something(d)
            for where, text in _stem_texts(d):
                phrases = deictic_phrases(text)
                if not phrases:
                    continue
                stats["deictic_samples"] += 1
                if drawn:
                    stats["deictic_and_drawn"] += 1
                    continue
                findings.append(
                    f"{node_id}: seed {seed} {where} points at a display "
                    f"({phrases[0]!r}) but the item draws nothing "
                    f"(is_visual={d.get('is_visual')!r}, "
                    f"visual_type={d.get('visual_type')!r}). Either serve it through a "
                    f"formatter that draws the referent, or write a stem that does not "
                    f"promise one. Text: {' '.join(str(text).split())[:160]!r}. "
                    f"Reproduce: PracticeOrchestrator.generate_problem("
                    f"node_id='{node_id}', seed={seed}, is_student_path=True)"
                )
    return findings, stats


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    findings, stats = collect_findings(node_ids)
    if findings:
        print(f"  FAIL dangling_visual_reference_1M ({len(findings)}):")
        for f in findings[:12]:
            print(f"    - {f}")
        if len(findings) > 12:
            print(f"    ... and {len(findings) - 12} more.")
        return False
    print(f"  PASS dangling_visual_reference_1M: 0 findings over {stats['samples']} "
          f"student-path sample(s); {stats['deictic_and_drawn']} sample(s) point at a "
          f"display AND draw one; {_DEICTIC.pattern.count('|') + 1} deictic pattern(s) "
          f"recognised (known limitation 1)")
    return True


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="§1M a stem that points at a display must be served with one")
    ap.add_argument("--node-ids", help="comma-separated subset")
    args = ap.parse_args()
    nodes = args.node_ids.split(",") if args.node_ids else None
    return 0 if validate_all(nodes) else 1


if __name__ == "__main__":
    sys.exit(main())
