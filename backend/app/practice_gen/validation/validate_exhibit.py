"""
§2L — a discrete variant a node DECLARES must reach the render a pupil receives.

WHY THIS EXISTS (owner ruling 26, 2026-10-08)
---------------------------------------------
§2I (`validate_compat.validate_declared_variants_are_producible`) proves a declared
`(axis, value)` RENDERS WITHOUT RAISING. It never asked whether the rendered problem
shows that value, and on 2026-10-08 545 of 973 declared pairs were found never to be
exhibited at any of 8 seeds: a DNA that never reads an axis renders perfectly, so §2I
reported green for declared variety no learner ever sees. Clause coverage judged from
declarations was unsound for as long as that stood. This is the check §2I is not.

WHAT "EXHIBITED" MEANS, EXACTLY
-------------------------------
For every `(axis, value)` that `judgment_packets._variant_coverage_candidates` declares
for a node -- the same candidate list §2I and the judgment packets use, never a copy --
the value is requested on the student path at each of `SEEDS`. It is exhibited when
either:

  (a) RECORDED: the generator's own `given_values` carry the value at some seed, as read
      by `tests.attester_packets._matching_variant_evidence`, the matcher the Attester
      packet builder already trusts; or
  (b) RENDERED: at the same seeds, the rendered problem (`SIGNATURE_FIELDS`: question
      text, answer, options, cloze text, visual type, visual payload) differs from the
      render under EVERY sibling value of the same axis on that node -- or, for an axis
      with one declared value, from the render with no variant requested at all.

(b) exists because ruling 26's evidence entry measured 113 pairs that record nothing yet
change the render: honoured, merely uninstrumented. Without (b) every one of them is a
false finding.

(b) is EVERY sibling, not ANY, and that was decided by measurement, not taste. Under
"any", 8 recorded substitutions pass: `mat_g1_mg_q1_0` requests
`shape_set='composite_figures'`, records `basic_triangles_rectangles_squares`, and
renders byte-identically to that sibling -- yet differs from `extended_with_circles`,
so "differs from a sibling" would certify a value the DNA throws away. Two declared
values a pupil cannot tell apart are one variant declared twice.

THE CLASSES A FINDING CARRIES (each names what the generator agent must do)
---------------------------------------------------------------------------
  A  clamp        the student path drops it; `is_student_path=False` records it.
  B  substituted  the generator records ANOTHER value, and the render matches a sibling.
  D  no-op        nothing recorded, and the render matches a sibling (named) at every seed:
                  either the DNA never reads it, or two declared values alias.
  E  default-only the only declared value; nothing recorded, and the render equals the
                  unrequested default, so no diff can show it is honoured.
  R  unrenderable every seed raised. §2I owns producibility; it is named here too so no
                  pair silently drops out of this count.

Each class's remedy is a generator fix under Content Rule 4 -- build it where the lc's
competency names it, undeclare it otherwise, citing the clause -- and is NOT this
module's to make. Making them exhibit is the content queue.

THE ATTESTER-PACKET FOLD-IN
---------------------------
The same stage builds every node's Attester packet with `tests.attester_packets.build`,
the builder a dispatch would call, so a packet the builder REFUSES -- a provider variant
it cannot stratify (`provider_variant_stratification_6F`), or a clause sibling the DNA
cannot yet expose (`clause_enumeration_22`, needs_instrumentation) -- is a named finding
before anyone dispatches a judge, rather than a surprise mid-campaign (Phase 3 met 8 of
them that way). A refused node is rebuilt one capability at a time so every refusing
capability is named, not only the first. Any OTHER exception from the builder is a harness
defect and crashes the stage loudly; only the typed `PacketRefusal` is a content finding.

NAMED LIMITS (Scaling Mandate 6; also in docs/pgen_contract.md §2L and the evidence log)
------------------------------------------------------------------------------------------
1. `len(SEEDS)` seeds per pair. A value exhibited only on seeds outside them reads as
   not exhibited; a sibling that differs only outside them reads as identical.
2. (a) trusts `given_values`. A DNA that records the requested value and then ignores it
   passes (a). (b) is not required on top of (a), because ruling 26 accepts either.
3. (b) is a byte diff of `SIGNATURE_FIELDS`. A value that changes only what this tuple
   omits (hints, interaction mode, formatter choice not reflected in these fields) reads
   as identical; a value that perturbs the generator's random stream without any
   semantic effect reads as honoured.
4. Class E is undecidable by construction: a single declared value equal to the default
   can be honoured and still render like the default. It is reported, because it cannot
   be shown; the remedy for an honoured one is to record it (instrumentation).
5. Classification order is A, then B, then E, then D, so a pair is reported under one
   class even when more than one description fits.
6. The packet fold-in inherits every limit of `tests.attester_packets.build`; its visual
   descriptions are produced by a Node child process the Phase 1 socket guard does not
   see.
7. Report-only inside `run_all` until the exit-code split (NEXT_AGENT_PROMPT H2) lands:
   the stage prints every finding but does not turn run_all red, because its baseline is
   red (Mandate 5). This module's own CLI exits 1 on any finding, and that is the path the
   mutations prove, on a node whose baseline is clean.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[4]

# §8 inventory: the assertions this module can independently fail on.
ASSERTIONS = (
    "variant_not_exhibited_2L",
    "attester_packet_refused_2L",
)

# The seeds of ruling 26's measurement (10_000 + 7919*k), so the first run of this gate
# reproduces the number that motivated it. >= 10_000, so `_render_sample` decodes no
# reserved profile range from them: what is requested is exactly what is passed.
SEEDS: Tuple[int, ...] = tuple(10_000 + 7919 * k for k in range(8))

# What a pupil is given, for criterion (b). Hints are guidance about an item, not the
# item (limitation 3).
SIGNATURE_FIELDS: Tuple[str, ...] = (
    "question_text", "correct_answer", "options", "cloze_text", "visual_type",
    "visual_payload",
)

CLASS_REMEDY = {
    "A": "the student-path clamp replaces it while the direct path records it: let the "
         "student path serve it, or narrow the declaration to what the clamp allows",
    "B": "the DNA substitutes another value: implement this value where the lc's "
         "competency names it, otherwise undeclare it (Content Rule 4, cite the clause)",
    "D": "the DNA never reads this value, or renders it exactly like the sibling(s) named: "
         "implement it where the lc's competency names it, otherwise undeclare it "
         "(Content Rule 4, cite the clause)",
    "E": "the only declared value renders exactly like the default and records nothing: "
         "record it in given_values if it is honoured, otherwise undeclare it",
    "R": "no seed renders it at all (see §2I): fix producibility first",
}


def _signature(sample: Dict[str, Any]) -> str:
    """The rendered problem a pupil sees, as one comparable string."""
    return json.dumps({k: sample.get(k) for k in SIGNATURE_FIELDS},
                      sort_keys=True, default=str)


class _NodeRenders:
    """Every student-path render one node's check needs, each made at most once."""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self._cache: Dict[Tuple[str, int], Any] = {}

    def get(self, profile: Optional[Dict[str, Any]], seed: int) -> Any:
        """The sample, or the exception the render raised (kept, never swallowed)."""
        from .judgment_packets import _render_sample

        key = (json.dumps(profile, sort_keys=True, default=str), seed)
        if key not in self._cache:
            try:
                self._cache[key] = _render_sample(
                    self.node_id, seed, profile, include_private_variant_evidence=True)
            except Exception as exc:  # noqa: BLE001 -- carried into the finding (class R)
                self._cache[key] = exc
        return self._cache[key]


def _rendered(sample: Any) -> bool:
    return isinstance(sample, dict)


def _distinct_from(renders: _NodeRenders, axis: str, value: Any,
                   other: Optional[Dict[str, Any]]) -> bool:
    """True when, at some seed both render, `value` and `other` give different problems."""
    for seed in SEEDS:
        mine, theirs = renders.get({axis: value}, seed), renders.get(other, seed)
        if _rendered(mine) and _rendered(theirs) and _signature(mine) != _signature(theirs):
            return True
    return False


def _direct_path_records(node_id: str, axis: str, value: Any) -> Tuple[Optional[int], List[str]]:
    """
    (first seed at which the NON-student path records the value, or None; the direct-path
    render failures met on the way). Only decides class A, so a refusal there is carried
    into the finding's text rather than raised.
    """
    from ..pipeline import run
    from tests.attester_packets import _matching_variant_evidence

    failures: List[str] = []
    for seed in SEEDS:
        try:
            p = run(node_id, seed=seed, difficulty_profile={axis: value},
                    is_student_path=False)
        except Exception as exc:  # noqa: BLE001 -- carried into the finding text
            failures.append(f"seed {seed}: {type(exc).__name__}")
            continue
        if _matching_variant_evidence({"_provider_variant_evidence": p.get("given_values") or {}},
                                      (axis, value)):
            return seed, failures
    return None, failures


def _reproduce(node_id: str, axis: str, value: Any, seed: int) -> str:
    return (f"Reproduce: judgment_packets._render_sample('{node_id}', {seed}, "
            f"{{{axis!r}: {value!r}}}, include_private_variant_evidence=True)")


def exhibit_findings(node_id: str, stats: Dict[str, int]) -> List[str]:
    """Every declared (axis, value) on one node that never reaches the render."""
    from .judgment_packets import _variant_coverage_candidates
    from tests.attester_packets import _matching_variant_evidence, _variant_evidence_paths

    by_axis: Dict[str, List[Any]] = defaultdict(list)
    for axis, value in _variant_coverage_candidates(node_id):
        by_axis[axis].append(value)

    renders = _NodeRenders(node_id)
    findings: List[str] = []
    for axis, values in by_axis.items():
        for value in values:
            stats["candidates"] += 1
            recorded_other: Dict[int, List[str]] = {}
            failures: List[str] = []
            recorded_at = None
            for seed in SEEDS:
                sample = renders.get({axis: value}, seed)
                if not _rendered(sample):
                    failures.append(f"seed {seed}: {type(sample).__name__}: {sample}"[:160])
                    continue
                if _matching_variant_evidence(sample, (axis, value)):
                    recorded_at = seed
                    break
                seen = [repr(v) for _, v in _variant_evidence_paths(
                    sample.get("_provider_variant_evidence") or {}, axis)]
                if seen:
                    recorded_other[seed] = seen
            if recorded_at is not None:
                stats["exhibited_recorded"] += 1
                continue

            if len(failures) == len(SEEDS):
                cls, why = "R", f"every seed raised; first: {failures[0]}"
            else:
                siblings = [v for v in values if v != value]
                if siblings:
                    alike = [v for v in siblings if not _distinct_from(renders, axis, value, {axis: v})]
                else:
                    alike = [] if _distinct_from(renders, axis, value, None) else ["<default>"]
                if not alike:
                    stats["exhibited_rendered"] += 1
                    continue
                direct_seed, direct_failures = _direct_path_records(node_id, axis, value)
                if direct_failures:
                    failures.append(f"direct path raised at {len(direct_failures)} seed(s): "
                                    f"{direct_failures[:2]}")
                if direct_seed is not None:
                    cls, why = "A", (f"the student path records nothing for it at seeds "
                                     f"{list(SEEDS)}, while is_student_path=False records "
                                     f"it at seed {direct_seed}")
                elif recorded_other:
                    seed, seen = next(iter(recorded_other.items()))
                    cls, why = "B", (f"requested {axis}={value!r} and the generator "
                                     f"recorded {axis}={', '.join(seen)} instead (seed "
                                     f"{seed}); the render equals sibling(s) "
                                     f"{alike!r} at every seed of {list(SEEDS)}")
                elif not siblings:
                    cls, why = "E", (f"the only declared value of {axis!r}; nothing is "
                                     f"recorded and the render equals the unrequested "
                                     f"default at every seed of {list(SEEDS)}")
                else:
                    cls, why = "D", (f"nothing is recorded, and the render equals "
                                     f"sibling(s) {alike!r} at every seed of {list(SEEDS)}")
            stats[f"class_{cls}"] += 1
            raised = (f" Render failures: {failures[:3]}." if failures and cls != "R" else "")
            findings.append(
                f"{node_id}: declared variant {axis}={value!r} is not exhibited "
                f"[class {cls}]: {why}.{raised} Owed: {CLASS_REMEDY[cls]}. "
                f"{_reproduce(node_id, axis, value, SEEDS[0])}"
            )
    return findings


def packet_findings(node_id: str, stats: Dict[str, int]) -> List[str]:
    """Every capability whose Attester packet the builder refuses to assemble."""
    from ..registry import get_node_info
    from tests import attester_packets as AP

    stats["packet_nodes"] += 1
    try:
        AP.build([node_id])
        return []
    except AP.PacketRefusal as refusal:
        first = refusal
    # Refused: rebuild one capability at a time so EVERY refusing capability is named,
    # not only the first the builder met. A needs_instrumentation refusal is node-wide
    # (raised before any capability is visited), so identical messages are reported once.
    out: List[str] = []
    seen: set = set()
    for req in (get_node_info(node_id) or {}).get("requires") or []:
        cap = str(req.get("id", ""))
        try:
            AP.build([node_id], [cap])
        except AP.PacketRefusal as refusal:
            if str(refusal) in seen:
                continue
            seen.add(str(refusal))
            stats["packet_refusals"] += 1
            out.append(f"{node_id}: the Attester packet for capability {cap!r} is refused "
                       f"[{refusal.label}]: {refusal}. Reproduce: "
                       f"tests.attester_packets.build(['{node_id}'], ['{cap}'])")
    if not out:
        raise RuntimeError(
            f"§2L: {node_id}'s whole-node Attester packet was refused ({first}) but no "
            f"single capability's packet is. The builder is not decomposable the way this "
            f"check assumes; that is a harness defect, not a content finding."
        )
    return out


def collect_findings(node_ids: Optional[List[str]] = None) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    """{assertion label: findings} over the given nodes (default: every node), and stats."""
    sys.path.insert(0, str(REPO_ROOT))
    from ..registry import get_all_node_ids

    stats: Dict[str, int] = defaultdict(int)
    out: Dict[str, List[str]] = {label: [] for label in ASSERTIONS}
    for node_id in (node_ids or sorted(get_all_node_ids())):
        out["variant_not_exhibited_2L"].extend(exhibit_findings(node_id, stats))
        out["attester_packet_refused_2L"].extend(packet_findings(node_id, stats))
    return out, dict(stats)


def validate_all(node_ids: Optional[List[str]] = None, report_only: bool = False) -> bool:
    """
    Print every finding. Returns False on any finding -- unless `report_only`, which is
    run_all's stage until H2 lands (limitation 7): there the findings are printed under
    REPORT rather than FAIL and the return is True.
    """
    findings, stats = collect_findings(node_ids)
    word = "REPORT" if report_only else "FAIL"
    total = 0
    for label in ASSERTIONS:
        items = findings[label]
        total += len(items)
        if items:
            print(f"  {word} {label} ({len(items)}):")
            for item in items:
                print(f"    - {item}")
        else:
            print(f"  PASS {label}")
    classes = {k[len("class_"):]: v for k, v in sorted(stats.items()) if k.startswith("class_")}
    print(f"  §2L: {stats.get('candidates', 0)} declared pair(s) at {len(SEEDS)} seeds; "
          f"{stats.get('exhibited_recorded', 0)} recorded, "
          f"{stats.get('exhibited_rendered', 0)} exhibited by render only, "
          f"{len(findings['variant_not_exhibited_2L'])} not exhibited {classes}; "
          f"{stats.get('packet_nodes', 0)} Attester packet(s) built, "
          f"{stats.get('packet_refusals', 0)} refusal(s)")
    if report_only and total:
        print(f"  §2L is REPORT-ONLY until the run_all exit-code split (H2): {total} content "
              f"finding(s) above are the generator work queue and do not turn this run red.")
    return report_only or total == 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="§2L a declared variant must reach the render; Attester packets must build")
    ap.add_argument("--node-ids", help="comma-separated subset")
    args = ap.parse_args()
    nodes = args.node_ids.split(",") if args.node_ids else None
    return 0 if validate_all(nodes) else 1


if __name__ == "__main__":
    sys.exit(main())
