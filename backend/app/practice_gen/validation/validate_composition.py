"""
§15 -- composition: what a clause selector chose, and what a hint describes, must reach the
item the learner reads (batch H5; owner rulings 22, 33, 35, 36).

A selector (`tests/clause_enumeration.py`, ruling 22) proves the generator CHOSE a sibling
from its structured values -- `skip_by == 2` for "counts by 2s". It does not prove the
rendered item still EXHIBITS that choice once a formatter has rewrapped it. Measured on
2026-10-10: mat_g1_na_q2_1 seed 4 is served as "What number is marked on the number line?"
with a dot at 48, while its hints still say "Look at the list of numbers: 40, 42, 44, 46,
___". The selector matched, the Attester's stratum counted it, and the learner never saw a
count by 2s. Owner ruling 35 settles how survival is decided, in two stages:

  RECORD-BASED (`selector_value_unexhibited_15`, content). Every learner-read field is a
  recorded template fill (§14, ruling 28) and every slot names its PROVENANCE: the keys of
  the generator's `values` it was derived from (`slots.S(..., src=...)`; a `value:<key>`
  domain implies it). A selector's structured value is exhibited when some NON-HINT
  learner-read field -- stem, options, statement, cloze, answer text -- is a fill whose
  slots (nested fills included) derive from every path the selector reads. A hint does not
  count: a hint describing the value is exactly the instance above. The rule decides a
  render only when §14 accounts for ALL of its learner-read fields; any other render is
  counted as undecided and printed, never guessed (the rollout makes it decidable lc by lc).

  TEXT STOPGAP (`hint_sequence_unshown_15`, content). Until the rollout reaches an lc, the
  instance's shape is caught from text: a hint that quotes a run of three or more
  comma-separated whole numbers ("40, 42, 44, 46") is a finding when one of those numbers
  appears nowhere in what the item shows (stem, options, cloze, statements and the visual
  payload). It is WORDING-SPECIFIC and labelled a stopgap in the contract row (Mandate 4):
  a hint that describes an unshown item in words, or a run the visual draws but its payload
  does not carry as numbers, is not seen.

Ruling 36: both report content findings here (exit 2) and do not refuse serving.

CLI (proof mode scopes by lc and by served formatter):

    PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.validate_composition \
        [--node-ids a,b] [--formatters mcq,cloze]

NAMED LIMITS (Scaling Mandate 6; also in docs/pgen_contract.md §15 and the evidence log):
  1. `SEEDS` seeds per lc on the default student path only (as §14).
  2. The record-based rule decides only fully-instrumented renders. Since the H3 rollout
     finished (H3-R2, 2026-10-11) that is every render at these seeds (1,351 of 1,351).
  3. Provenance is the generator's own statement. A slot that declares a `src` it does not
     use passes; review of the template (H4) is what catches a false declaration.
  4. A `visual_type` condition is treated as exhibited (the rendered visual IS its type).
     A visual payload exhibits a selector value only through a recorded fill: a number line
     that draws jumps of 2 without a recorded caption is reported as not exhibiting it.
  5. The stopgap reads digits only: fractions, money and times are not runs, and a run
     whose numbers all appear elsewhere in the item (even in another role) passes.
  6. The stopgap skips bracketed lists. Measured 2026-10-10: the only bracketed runs in
     hints are mat_g3_na_q3_5/_6's "Repeat the ones [9, 1, 8]", the ones digits of shown
     terms (derived, not quoted). That they print as a Python list is a defect of its own,
     reported in the evidence log, not by this check.
  7. The record closes over VALUE-level provenance (owner ruling 41): `slots.derives(key,
     src)` -- a shown value chosen BECAUSE of `src` exhibits `src`; `slots.computes(key,
     src)` -- a value that is a function of `src` is exhibited once every `src` is shown --
     and template provenance (`fill(..., _src=...)`). Every declaration is the generator's
     claim; a false one hides a real finding, as limit 3 says of slot `src`.
  8. A template written for the one value of a key its own branch SETS (length's
     `word_measure`, area's `shape`) is declared derived from that key by shared cause.
"""
from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

ASSERTIONS = (
    "selector_value_unexhibited_15",  # record-based: a selector's value reaches only the hints
    "hint_sequence_unshown_15",       # text stopgap: a hint quotes numbers the item does not show
)

SEEDS: Tuple[int, ...] = tuple(range(1, 21))

# A run: three or more whole numbers separated by commas, not part of a larger literal.
_RUN = re.compile(r"(?<![\d./₱$])\d+(?:\s*,\s*\d+(?![\d./])){2,}")
_NUM = re.compile(r"(?<![\d./])\d+(?![\d./])")
_BRACKETED = re.compile(r"\[[^\]]*\]")


def _flat(value: Any) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)


def _is_hint(where: str) -> bool:
    return where.split("[")[0] in ("hints", "hint")


def _render(node_id: str, seed: int):
    """(problem dict, recorded fills) for one student-path render."""
    from backend.app.services.orchestrator import PracticeOrchestrator
    from backend.app.practice_gen.slots import capture

    with capture() as fills:
        problem = PracticeOrchestrator.generate_problem(
            node_id=node_id, seed=seed, is_student_path=True).model_dump()
    return problem, fills      # a slots.Trace: the fills, plus `.derivations` (ruling 41)


def exhibited_keys(problem: Dict[str, Any], fills) -> Optional[Set[str]]:
    """
    The `values` keys the NON-HINT learner-read text is derived from, or None when some
    learner-read field is not a recorded fill (the render is undecidable, limit 2).
    """
    from backend.app.practice_gen.validation.validate_language import _texts

    by_text: Dict[str, list] = {}
    for f in fills:
        by_text.setdefault(f.text, []).append(f)
    fields = _texts(problem)
    if any(text not in by_text for _where, text in fields):
        return None
    keys: Set[str] = set()
    seen: Set[int] = set()
    stack = [f for where, text in fields if not _is_hint(where) for f in by_text[text]]
    while stack:
        f = stack.pop()
        if id(f) in seen:
            continue
        seen.add(id(f))
        for _name, src in f.sources:
            keys.update(src)
        for _name, value, domain in f.slots:
            if domain == "fill" and isinstance(value, str):
                inner = [g for g in by_text.get(value, []) if g is not f]
                if not inner:
                    return None   # the nested text accounts only itself (§14 reports it)
                stack.extend(inner)
    # Owner ruling 41: close over VALUE-level provenance. A shown value the generator
    # declared it chose BECAUSE of other values (`slots.derives`) exhibits those too.
    derivations = getattr(fills, "derivations", ())
    grew = True
    while grew:
        grew = False
        for d in derivations:
            if d.kind == "computes":
                # a function of shown values is shown
                if d.key not in keys and d.src and set(d.src) <= keys:
                    keys.add(d.key)
                    grew = True
            elif d.key in keys and not set(d.src) <= keys:
                # a shown value chosen BECAUSE of others exhibits them
                keys.update(d.src)
                grew = True
    return keys


def _paths(cond: Dict[str, Any]) -> List[List[str]]:
    """Alternative path sets a condition can be satisfied by (one per `any_of` branch)."""
    if "any_of" in cond:
        return [[c["path"] for c in branch] for branch in cond["any_of"]]
    return [[cond["path"]]]


def selector_unexhibited(selector: Dict[str, Any], evidence: Dict[str, Any], visual_type: Any,
                         keys: Set[str]) -> List[str]:
    """Paths the matching selector reads that the non-hint text does not derive from."""
    from tests import clause_enumeration as CE

    missing: List[str] = []
    for cond in selector["observe"]:
        options = []
        for branch_paths, branch in zip(_paths(cond), cond.get("any_of", [[cond]])):
            if all(CE.condition_matches(evidence, visual_type, c) for c in branch):
                options.append([p for p in branch_paths if p != "visual_type"])
        if options and not any(all(p in keys for p in opt) for opt in options):
            missing.extend(p for p in options[0] if p not in keys)
    return missing


def hint_runs_unshown(problem: Dict[str, Any]) -> List[Tuple[str, str, List[str]]]:
    """(hint, run, numbers absent from the item) for every quoted run the item does not show."""
    from backend.app.practice_gen.validation.validate_language import _texts

    shown = " ".join([text for where, text in _texts(problem) if not _is_hint(where)]
                     + [_flat(problem.get("visual_params"))])
    shown_nums = set(_NUM.findall(shown))
    out = []
    for hint in problem.get("hints") or []:
        if not isinstance(hint, str):
            continue
        # A bracketed list ("Repeat the ones [9, 1, 8]") is a derived description -- the
        # ones digits of shown terms -- not a quotation of the item (limit 6).
        for m in _RUN.finditer(_BRACKETED.sub(" ", hint)):
            absent = [n for n in _NUM.findall(m.group(0)) if n not in shown_nums]
            if absent:
                out.append((hint, m.group(0), absent))
    return out


def collect_findings(node_ids: Optional[List[str]] = None,
                     formatters: Optional[Iterable[str]] = None
                     ) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    """({label: [finding]}, stats). One finding per (lc, label, member or formatter)."""
    from backend.app.practice_gen.registry import get_all_node_ids
    from tests import clause_enumeration as CE

    wanted = set(formatters) if formatters else None
    grouped: "OrderedDict[Tuple[str, str, str], Dict[str, Any]]" = OrderedDict()
    stats = {"renders": 0, "selector_matches": 0, "selector_decided": 0, "selector_undecided": 0}
    for node_id in (node_ids or sorted(get_all_node_ids())):
        members = [(m, d) for _w, mm in CE.TABLE.get(node_id, []) for m, d in mm.items()
                   if "observe" in d]
        for seed in SEEDS:
            problem, fills = _render(node_id, seed)
            fmt = problem.get("formatter_name")
            if wanted is not None and fmt not in wanted:
                continue
            stats["renders"] += 1
            evidence, vt = problem.get("given_values") or {}, problem.get("visual_type")
            keys = None
            for member, disp in members:
                if not CE.selector_matches({"_provider_variant_evidence": evidence,
                                            "visual_type": vt}, disp):
                    continue
                stats["selector_matches"] += 1
                if keys is None:
                    keys = exhibited_keys(problem, fills)
                    if keys is None:
                        keys = False
                if keys is False:
                    stats["selector_undecided"] += 1
                    continue
                stats["selector_decided"] += 1
                missing = selector_unexhibited(disp, evidence, vt, keys)
                if missing:
                    g = grouped.setdefault((node_id, "selector_value_unexhibited_15", f"{member}/{fmt}"), {
                        "seed": seed, "seeds": set(),
                        "reason": (f"clause member {member!r} was selected by {disp['observe']!r}, but no "
                                   f"non-hint learner-read text is derived from {missing!r} "
                                   f"(formatter {fmt}): the item shows {problem.get('question_text','')[:90]!r}, "
                                   f"and only the hints carry the choice")})
                    g["seeds"].add(seed)
            for hint, run, absent in hint_runs_unshown(problem):
                g = grouped.setdefault((node_id, "hint_sequence_unshown_15", str(fmt)), {
                    "seed": seed, "seeds": set(),
                    "reason": (f"hint {hint[:90]!r} quotes {run!r}, but {absent!r} appear nowhere in "
                               f"the item the learner sees (formatter {fmt}, stem "
                               f"{problem.get('question_text','')[:80]!r})")})
                g["seeds"].add(seed)
    out: Dict[str, List[str]] = {label: [] for label in ASSERTIONS}
    for (node_id, label, where), g in grouped.items():
        out[label].append(
            f"{node_id}: {where} at seed {g['seed']} ({len(g['seeds'])} of {len(SEEDS)} seeds): "
            f"{g['reason']}. Reproduce: PracticeOrchestrator.generate_problem(node_id={node_id!r}, "
            f"seed={g['seed']}, is_student_path=True). Owed: render what the clause selected (or "
            f"what the hint describes) in the item itself, or stop serving this formatter for it.")
    return out, stats


def validate_all(node_ids: Optional[List[str]] = None,
                 formatters: Optional[Iterable[str]] = None) -> bool:
    findings, stats = collect_findings(node_ids, formatters)
    total = 0
    for label in ASSERTIONS:
        items = findings[label]
        total += len(items)
        if items:
            print(f"  FAIL {label} ({len(items)}):")
            for item in items:  # every finding, by name (ruling 23)
                print(f"    - {item}")
        else:
            print(f"  PASS {label}")
    print(f"  NOTE: {stats['selector_matches']} selector match(es) over {stats['renders']} render(s): "
          f"{stats['selector_decided']} decided by record, {stats['selector_undecided']} undecided "
          f"(a learner-read field is not yet a recorded fill -- named limit 2; the §14 rollout "
          f"makes them decidable)")
    return total == 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§15 composition: selected values and hinted runs reach the item")
    ap.add_argument("--node-ids", help="comma-separated lc subset (proof mode)")
    ap.add_argument("--formatters", help="comma-separated served-formatter subset (proof mode)")
    args = ap.parse_args()
    return 0 if validate_all(args.node_ids.split(",") if args.node_ids else None,
                             args.formatters.split(",") if args.formatters else None) else 1


if __name__ == "__main__":
    sys.exit(main())
