"""
§14 -- learner-read text is a recorded fill of declared slots, each inside its domain
(owner rulings 24, 28, 33, 34; batch H3).

Ruling 24 moves LLM review to stem templates plus the DOMAIN of every slot that fills them,
and makes the approval safe only "if its fields cannot escape it". Ruling 28 says how a
slot is known: each DNA, spine and text-adding formatter emits its template with a
structured slots record (`backend/app/practice_gen/slots.py`), never inferred from the
text. This module renders each lc on the student path under `slots.capture()` and proves:

  (a) every learner-read field (`validate_language._texts`, the §1J classification, reused
      rather than restated) equals the text of a recorded fill -- else
      `slot_text_unaccounted_14`, the site is not instrumented yet (ruling 34: content);
  (b) every recorded fill replays: `template.format(**slots)` (or the registered
      transformation it names, called with every recorded slot as a keyword -- `text` and
      any argument such as `fill_blank`'s `value`, H3-R1) reproduces its text -- else
      `slot_template_mismatch_14`. A spine is replayed through `slots.RENDERERS` (its
      template plus every recorded slot, by the generator's own `render_spine_text`);
  (c) every slot names a domain -- else `slot_unclassified_14` -- that this module can
      resolve -- else `slot_domain_unknown_14`, the one INTEGRITY label here, because the
      harness then cannot judge the slot at all;
  (d) every slot value lies inside its domain -- else `slot_domain_escape_14`.

DOMAIN KINDS (the only ones; a new kind is added here, with a test):
  R(lo, hi, basis)   runtime range the generator computed from the bounds it draws with
  E(members, basis)  runtime enumeration: the generator's own choices (a VocabGated pair)
  "enum:<dotted>"    membership in the generator's own imported list/tuple/set/dict keys
  "bank:<dotted>:<f>" membership in field <f> across the generator's own list of item
                     dicts (a list-valued field is flattened): a static item bank
  "value:<key>"      equals the generator's own `QuestionContext.values[key]`, observed at
                     the formatter boundary (a slot repeating a generated value)
  "noun:<dotted>"    a noun from the generator's own list/dict values, or its plural by the
                     shared inflection rule (`dna.base.to_singular_phrase`, which §1J uses)
  "text.derived"     text a generator computes from other slots (a repeated emoji display);
                     type-checked only
  "num.derived"      a number computed from other slots (int/float, not bool)
  "fill"             equals the text of another recorded fill (nested template)

Findings are aggregated per (lc, label, field or site) and name the lc, the first seed,
the formatter and DNA, and what is owed. CLI:

    PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.validate_slots [--node-ids a,b]

exits 1 on any finding (it has one kind); in run_all the labels are classified by
`_manifest.FINDING_CLASS` (content -> exit 2; `slot_domain_unknown_14` -> exit 1).

NAMED LIMITS (Scaling Mandate 6; also in docs/pgen_contract.md §14 and the evidence log):
  1. `SEEDS` seeds per lc on the default student path only; a template reachable only by
     a pinned formatter, another experience or another difficulty profile is not seen.
  2. Visual payload strings are not learner-read fields here: §1J's `_texts` excludes
     them (its limitation 2), and this reuses that classification.
  3. A field is accounted when its text EQUALS a recorded fill's text. Two fills that
     produce the same string are indistinguishable, which is harmless for accounting.
  4. "num.derived" checks the type only; whether the arithmetic is right is the hint
     contract's and §1E's job.
  5. "value:<key>" trusts that `values[key]`'s own domain was checked where it was
     generated; a value generated without `fill` is not.
  8. "text.derived" checks the type only (as "num.derived" does).
  6. Un-instrumented text is counted by field, not by source site (the record is what
     names a site, and un-instrumented text has none).
  7. §1J classifies some tags as pupil text (`format_data.context` = 'pure' on mcq), so
     those must be filled too; the classification is §1J's, inherited unchanged.
"""
from __future__ import annotations

import importlib
import sys
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from backend.app.practice_gen.slots import E, R, RENDERERS, TRANSFORMS, capture, renderer

ASSERTIONS = (
    "slot_text_unaccounted_14",   # a learner-read field no recorded fill produced
    "slot_template_mismatch_14",  # a recorded fill that does not replay from its slots
    "slot_unclassified_14",       # a slot recorded with no domain
    "slot_domain_unknown_14",     # a domain id this module cannot resolve (integrity)
    "slot_domain_escape_14",      # a slot value outside its declared domain
)

SEEDS: Tuple[int, ...] = tuple(range(1, 21))

_ENUM_CACHE: Dict[str, Any] = {}


def _enum(dotted: str) -> Any:
    """The generator's own collection at `module.path.NAME` (cached). Raises if absent."""
    if dotted not in _ENUM_CACHE:
        module_path, _, name = dotted.rpartition(".")
        obj = getattr(importlib.import_module(module_path), name)
        if not isinstance(obj, (list, tuple, set, frozenset, dict)):
            raise TypeError(f"enum domain {dotted!r} names a {type(obj).__name__}, "
                            f"not a list/tuple/set/dict")
        _ENUM_CACHE[dotted] = obj
    return _ENUM_CACHE[dotted]


_BANK_CACHE: Dict[str, Any] = {}


def _bank(spec: str) -> Any:
    """Every value field `f` takes across the generator's own list of dicts `module.NAME`."""
    if spec not in _BANK_CACHE:
        dotted, _, fld = spec.rpartition(":")
        module_path, _, name = dotted.rpartition(".")
        items = getattr(importlib.import_module(module_path), name)
        if not isinstance(items, (list, tuple)) or not all(isinstance(i, dict) for i in items):
            raise TypeError(f"bank domain {spec!r} does not name a list of dicts")
        members = []
        for item in items:
            if fld not in item:
                continue          # an item without the field contributes nothing, not None
            v = item[fld]
            members.extend(v if isinstance(v, (list, tuple)) else [v])
        if not members:
            raise ValueError(f"bank domain {spec!r}: no item carries field {fld!r}")
        _BANK_CACHE[spec] = members
    return _BANK_CACHE[spec]


def _members(obj: Any) -> List[Any]:
    return list(obj.values()) if isinstance(obj, dict) else list(obj)


def check_slot(value: Any, domain: Any, given: Dict[str, Any], texts: set) -> Optional[Tuple[str, str]]:
    """None if `value` lies in `domain`; else (label, reason). `given` is ctx.values."""
    if domain is None:
        return ("slot_unclassified_14", "the slot was recorded with no domain (a bare value, not S(value, domain))")
    if isinstance(domain, R):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ("slot_domain_escape_14", f"value {value!r} is not a number but its domain is a range")
        if not (domain.lo <= value <= domain.hi):
            return ("slot_domain_escape_14",
                    f"value {value!r} is outside its declared range [{domain.lo}, {domain.hi}] ({domain.basis})")
        return None
    if isinstance(domain, E):
        if value not in domain.members:
            return ("slot_domain_escape_14",
                    f"value {value!r} is not one of {list(domain.members)!r} ({domain.basis})")
        return None
    if not isinstance(domain, str):
        return ("slot_domain_unknown_14", f"domain {domain!r} is neither a registry id nor R(...)/E(...)")
    if domain == "text.derived":
        if not isinstance(value, str):
            return ("slot_domain_escape_14", f"derived text {value!r} is not a string")
        return None
    if domain.startswith("noun:"):
        from backend.app.practice_gen.dna.base import to_singular_phrase
        try:
            nouns = _members(_enum(domain[len("noun:"):]))
        except (ImportError, AttributeError, TypeError, ValueError) as exc:
            return ("slot_domain_unknown_14", f"noun domain {domain!r} does not resolve: {type(exc).__name__}: {exc}")
        if value not in nouns and to_singular_phrase(str(value)) not in nouns:
            return ("slot_domain_escape_14",
                    f"noun {value!r} is not in {domain[len('noun:'):]} (nor is its singular "
                    f"{to_singular_phrase(str(value))!r}): the generator used a noun outside its own list")
        return None
    if domain == "fill":
        if str(value) not in texts:
            # The inner text was built by an un-instrumented site: owed instrumentation,
            # the same finding as an unaccounted field (ruling 34), not a domain escape.
            return ("slot_text_unaccounted_14",
                    f"nested slot value {str(value)[:80]!r} is not the text of any recorded fill "
                    f"(the template it came from is not instrumented)")
        return None
    if domain == "num.derived":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ("slot_domain_escape_14", f"derived value {value!r} is not a number")
        return None
    if domain.startswith("value:"):
        key = domain[len("value:"):]
        if key not in given:
            return ("slot_domain_escape_14", f"the generator's values carry no {key!r} for this slot to repeat")
        if given[key] != value:
            return ("slot_domain_escape_14",
                    f"value {value!r} differs from the generated values[{key!r}] = {given[key]!r}")
        return None
    if domain.startswith("enum:"):
        try:
            members = _enum(domain[len("enum:"):])
        except (ImportError, AttributeError, TypeError, ValueError) as exc:
            return ("slot_domain_unknown_14", f"enum domain {domain!r} does not resolve: {type(exc).__name__}: {exc}")
        if value not in members:
            return ("slot_domain_escape_14", f"value {value!r} is not in {domain[len('enum:'):]}")
        return None
    if domain.startswith("bank:"):
        try:
            members = _bank(domain[len("bank:"):])
        except (ImportError, AttributeError, TypeError, ValueError) as exc:
            return ("slot_domain_unknown_14", f"bank domain {domain!r} does not resolve: {type(exc).__name__}: {exc}")
        if value not in members:
            return ("slot_domain_escape_14", f"value {str(value)[:80]!r} is not in the bank {domain[len('bank:'):]}")
        return None
    return ("slot_domain_unknown_14", f"domain id {domain!r} has no kind this module resolves")


def replay(fill) -> Optional[str]:
    """None if the recorded fill reproduces its text from its template and slots; else why not."""
    values = {name: value for name, value, _d in fill.slots}
    try:
        if fill.renderer is None:
            again = fill.template.format(**values)
        elif fill.renderer in RENDERERS:
            # A template-level renderer (a spine): the generator's own function, by name.
            again = renderer(fill.renderer)(fill.template, **values)
        elif fill.renderer in TRANSFORMS:
            # Every recorded slot is passed by keyword: `text` (the transformed fill) and any
            # argument the transformation takes, such as `fill_blank`'s `value` (H3-R1).
            again = TRANSFORMS[fill.renderer](**values)
        else:
            return f"renderer {fill.renderer!r} is not a registered transformation"
    except (KeyError, IndexError, ValueError) as exc:
        return f"replay raised {type(exc).__name__}: {exc}"
    if again != fill.text:
        return f"replay gives {again[:80]!r}, recorded {fill.text[:80]!r}"
    return None


def render_findings(node_id: str, seed: int) -> List[Tuple[str, str, str]]:
    """(label, where, reason) for one student-path render of one lc."""
    from backend.app.services.orchestrator import PracticeOrchestrator
    from backend.app.practice_gen.validation.validate_language import _texts

    from backend.app.services import orchestrator as _orch

    # Observe the generator's own QuestionContext.values at the formatter boundary, so a
    # "value:<key>" slot is compared with what was GENERATED (the answer included, which
    # the payload's given_values deliberately omits). Read-only; restored in `finally`.
    seen: Dict[str, Any] = {}
    real = _orch.apply_formatter

    def _spy(ctx, formatter_name, rng):
        seen.update(ctx.values or {})
        return real(ctx, formatter_name, rng)

    _orch.apply_formatter = _spy
    try:
        with capture() as fills:
            problem = PracticeOrchestrator.generate_problem(
                node_id=node_id, seed=seed, is_student_path=True).model_dump()
    finally:
        _orch.apply_formatter = real
    texts = {f.text for f in fills}
    # How many fills produced each text. A "fill" slot must be accounted by a fill OTHER
    # than the one holding it: `slots.transform` records "{text}" around its input, and when
    # the transformation is the identity (no trailing period to strip) its output equals its
    # input, so an un-instrumented statement accounted ITSELF. Found 2026-10-10 (H5) on
    # fmt_true_false's subtraction statements, which §14 had passed as instrumented.
    produced: Dict[str, int] = {}
    for f in fills:
        produced[f.text] = produced.get(f.text, 0) + 1
    given = seen
    out: List[Tuple[str, str, str]] = []
    for f in fills:
        why = replay(f)
        if why:
            out.append(("slot_template_mismatch_14", f.site, why))
        others = texts if produced[f.text] > 1 else texts - {f.text}
        for name, value, domain in f.slots:
            bad = check_slot(value, domain, given, others)
            if bad:
                out.append((bad[0], f"{f.site} slot {name!r}", bad[1]))
    for where, text in _texts(problem):
        if text not in texts:
            out.append(("slot_text_unaccounted_14", where.split("[")[0],
                        f"{text[:90]!r} is not the text of any recorded fill: the site that "
                        f"builds it is not instrumented (formatter {problem.get('formatter_name')}, "
                        f"DNA {problem.get('dna_name')})"))
    return out


def collect_findings(node_ids: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """{label: [finding, ...]}, one finding per (lc, label, where), naming its first seed."""
    from backend.app.practice_gen.registry import get_all_node_ids

    grouped: "OrderedDict[Tuple[str, str, str], Dict[str, Any]]" = OrderedDict()
    for node_id in (node_ids or sorted(get_all_node_ids())):
        for seed in SEEDS:
            for label, where, reason in render_findings(node_id, seed):
                key = (node_id, label, where)
                if key not in grouped:
                    grouped[key] = {"seed": seed, "reason": reason, "seeds": set()}
                grouped[key]["seeds"].add(seed)
    out: Dict[str, List[str]] = {label: [] for label in ASSERTIONS}
    for (node_id, label, where), g in grouped.items():
        owed = ("instrument the site with slots.fill/S (ruling 28)"
                if label in ("slot_text_unaccounted_14", "slot_unclassified_14")
                else "keep the value inside its declared domain, or correct the declaration"
                if label == "slot_domain_escape_14"
                else "record the template the text is really built from"
                if label == "slot_template_mismatch_14"
                else "register the domain kind in validate_slots or fix the id")
        out[label].append(
            f"{node_id}: {where} at seed {g['seed']} ({len(g['seeds'])} of {len(SEEDS)} seeds): "
            f"{g['reason']}. Reproduce: PracticeOrchestrator.generate_problem(node_id={node_id!r}, "
            f"seed={g['seed']}, is_student_path=True) under slots.capture(). Owed: {owed}.")
    return out


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    findings = collect_findings(node_ids)
    total = 0
    for label in ASSERTIONS:
        items = findings[label]
        total += len(items)
        if items:
            print(f"  FAIL {label} ({len(items)}):")
            for item in items[:15]:
                print(f"    - {item}")
            if len(items) > 15:
                print(f"    ... and {len(items) - 15} more.")
        else:
            print(f"  PASS {label}")
    scope = len(node_ids) if node_ids else "all"
    print(f"  §14: {total} finding(s) over {scope} lc(s) x {len(SEEDS)} seed(s)")
    return total == 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§14 learner-read text is a recorded fill of declared slots")
    ap.add_argument("--node-ids", help="comma-separated lc subset (proof mode)")
    args = ap.parse_args()
    return 0 if validate_all(args.node_ids.split(",") if args.node_ids else None) else 1


if __name__ == "__main__":
    sys.exit(main())
