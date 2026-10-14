"""
§14 -- learner-read text is a recorded fill of declared slots, each inside its domain
(owner rulings 24, 28, 33, 34; batch H3).

Ruling 24 moves LLM review to stem templates plus the DOMAIN of every slot that fills them,
and makes the approval safe only "if its fields cannot escape it". Ruling 28 says how a
slot is known: each DNA, spine and text-adding formatter emits its template with a
structured slots record (`backend/app/practice_gen/slots.py`), never inferred from the
text. This module renders each lc on every path of `paths()` -- the ONE enumeration §14 and
§17 share (owner ruling 44b: student seeds 1-40 plus every advertised formatter pinned at seeds
3, 17 and 29) -- under `slots.capture()` and proves:

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
  (d) every slot value lies inside its domain -- else `slot_domain_escape_14`. A vocabulary
      gate `G` (owner ruling 48) is inside its domain only when the printed word is the ONE
      word the gate gives this lc: `requires` in the vocabulary the generator may print for it
      (`base_generator.generator_vocabulary`: cumulative, student and introduced vocabulary,
      the generator's own rule) selects the preferred word, else the fallback. The other word
      escapes;
  (e) every TYPE-ONLY slot (`num.derived`/`text.derived`) carries a named reason it cannot be
      tightened -- else `slot_domain_type_only_14` (owner rulings 42-43; batch H4-0, content).
      A reason is a `slots.DERIVED_REASONS` kind plus a non-empty `src` whose every key is in
      the generator's own values at that render. Ruling 42 makes this count reach 0 on an lc
      before H4 approves that lc's stems: a judge's approval of a type-only domain bounds
      nothing the learner reads. It counts EVERY recorded slot, learner-reachable or not
      (ruling 43), so no closure logic can hide one; a fill that is not learner text is
      tightened by being turned back into plain code, which (a) catches if it was.
  (f) every pinned path renders -- else `slot_path_refused_14` (owner ruling 44b; batch H4,
      content): an advertised formatter the lc refuses at a seed is a named finding, never a
      skipped path. A STUDENT-path render that raises is not caught here: it crashes the
      stage, as before (the student path must never raise).

DOMAIN KINDS (the only ones; a new kind is added here, with a test):
  R(lo, hi, basis)   runtime range the generator computed from the bounds it draws with
  E(members, basis)  runtime enumeration: the generator's own choices
  G(members, basis, requires)  a vocabulary gate (an E of two words, ruling 48): for one lc
                     only `G.for_vocab(cumulative_vocab)` may print (a VocabGated pair)
  "enum:<dotted>"    membership in the generator's own imported list/tuple/set/dict keys
  "bank:<dotted>:<f>" membership in field <f> across the generator's own list of item
                     dicts (a list-valued field is flattened): a static item bank
  "value:<key>"      equals the generator's own `QuestionContext.values[key]`, observed at
                     the formatter boundary (a slot repeating a generated value)
  "noun:<dotted>"    a noun from the generator's own list/dict values, or its plural by the
                     shared inflection rule (`dna.base.to_singular_phrase`, which §1J uses)
  "text.derived"     text a generator computes from other slots (a repeated emoji display);
                     type-checked only, and counted by (e) unless it carries a reason
  "num.derived"      a number computed from other slots (int/float, not bool); likewise
  "fill"             equals the text of another recorded fill (nested template)

Findings are aggregated per (lc, label, field or site) and name the lc, the first seed,
the formatter and DNA, and what is owed. CLI:

    PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.validate_slots [--node-ids a,b]

exits 1 on any finding (it has one kind); in run_all the labels are classified by
`_manifest.FINDING_CLASS` (content -> exit 2; `slot_domain_unknown_14` -> exit 1).

NAMED LIMITS (Scaling Mandate 6; also in docs/pgen_contract.md §14 and the evidence log):
  1. `paths()` only: the student path at `SEEDS` (1-40) and each advertised formatter
     pinned at `PINNED_SEEDS` (3, 17, 29), default experience and difficulty. A template
     reachable only by another seed, experience or difficulty profile is not seen (widened
     from 20 student seeds by owner ruling 44b, batch H4).
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
  9. `slots.derived` slots (`num.derived`/`text.derived`) bound the TYPE only: 63% of
     slot-fills (1,233 distinct site/slot pairs, 2026-10-11) are type-only, so for them a
     judge-approved domain does not bound the value (an H4 prerequisite to tighten).
 10. Accounting covers the paths the seeds reach; a slot declared "fill" whose variable has
     a non-fill alternative on an unreached path is found by a static audit, not here.
 11. (e) is counted at the paths `paths()` reaches (limit 1): a type-only slot only an
     unvisited seed, experience or profile reaches is not counted, so an lc at 0 here has 0
     on these paths, not everywhere.
 13. (f) catches a pinned refusal by exception, of any type, around the generator call only;
     its message is quoted. It cannot tell an eligibility refusal the generator meant from a
     crash on that path; both are named by lc, seed and formatter for the generator queue.
 12. A reason is the generator's own claim. (e) checks that its kind is registered and its
     `src` names keys the generator really carries; it cannot check that the slot IS computed
     from them, or that no stricter domain exists. H4's judges review both (as §15 limit 7).
"""
from __future__ import annotations

import importlib
import sys
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from backend.app.practice_gen.slots import DERIVED_REASONS, E, G, R, RENDERERS, TRANSFORMS, capture, renderer

ASSERTIONS = (
    "slot_text_unaccounted_14",   # a learner-read field no recorded fill produced
    "slot_template_mismatch_14",  # a recorded fill that does not replay from its slots
    "slot_unclassified_14",       # a slot recorded with no domain
    "slot_domain_unknown_14",     # a domain id this module cannot resolve (integrity)
    "slot_domain_escape_14",      # a slot value outside its declared domain
    "slot_domain_type_only_14",   # a type-only slot with no named reason (rulings 42-43)
    "slot_path_refused_14",       # an advertised formatter, pinned, refuses to render (ruling 44b)
)

TYPE_ONLY = ("num.derived", "text.derived")

# The ONE path enumeration §14 and §17 render (owner ruling 44b, batch H4; until then §14
# rendered student seeds 1-20 only). `tests/render_snapshot.py` and `tests/slot_wide_check.py`
# import it rather than restating it, so a reviewed family (§17) is always a domain-checked
# one (§14): an approval whose fields nothing enforces is what ruling 24 forbids.
SEEDS: Tuple[int, ...] = tuple(range(1, 41))          # student path
PINNED_SEEDS: Tuple[int, ...] = (3, 17, 29)           # each advertised formatter, pinned


def paths(node_id: str) -> List[Tuple[int, Optional[str]]]:
    """(seed, formatter) for every path of `node_id`: formatter None is the student path."""
    from backend.app.practice_gen.registry import get_node_formatters
    return ([(seed, None) for seed in SEEDS]
            + [(seed, fmt) for fmt in sorted(get_node_formatters(node_id) or []) for seed in PINNED_SEEDS])


def path_call(node_id: str, seed: int, formatter: Optional[str]) -> str:
    """The exact call that reproduces one path (printed in every finding)."""
    if formatter is None:
        return f"PracticeOrchestrator.generate_problem(node_id={node_id!r}, seed={seed}, is_student_path=True)"
    return (f"PracticeOrchestrator.generate_problem(node_id={node_id!r}, seed={seed}, "
            f"formatter={formatter!r}, is_student_path=False)")

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


def type_only_reason(domain: str, why: Optional[str], src: Tuple[str, ...],
                     given: Dict[str, Any]) -> Optional[str]:
    """
    None if a type-only slot carries a valid named reason (owner rulings 42-43); else what is
    missing. Valid = a registered `slots.DERIVED_REASONS` kind AND a non-empty `src` whose
    every key the generator's own values carry at this render.
    """
    if why is None:
        return (f"type-only domain {domain!r} bounds the type, not the value: tighten it to "
                f"value:/E/R/enum:/bank:/fill, or name a slots.DERIVED_REASONS kind with its src "
                f"(owner rulings 42-43)")
    if why not in DERIVED_REASONS:
        return f"reason {why!r} is not a registered slots.DERIVED_REASONS kind"
    if not src:
        return f"reason {why!r} names no src: a reason must say which generated values the slot comes from"
    missing = [k for k in src if k not in given]
    if missing:
        return (f"reason {why!r} cites src {missing!r}, which the generator's values do not carry "
                f"at this render (it carries {sorted(given)[:12]!r})")
    return None


def check_slot(value: Any, domain: Any, given: Dict[str, Any], texts: set,
               why: Optional[str] = None, src: Tuple[str, ...] = (),
               vocab: Optional[Any] = None) -> Optional[Tuple[str, str]]:
    """
    None if `value` lies in `domain`; else (label, reason). `given` is ctx.values; `why` and
    `src` are the slot's recorded reason and provenance (read for type-only domains only);
    `vocab` is `lc_vocab(lc)`, the generator's vocabulary for the lc (read for a gate `G` only).
    """
    if domain is None:
        return ("slot_unclassified_14", "the slot was recorded with no domain (a bare value, not S(value, domain))")
    if isinstance(domain, R):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ("slot_domain_escape_14", f"value {value!r} is not a number but its domain is a range")
        if not (domain.lo <= value <= domain.hi):
            return ("slot_domain_escape_14",
                    f"value {value!r} is outside its declared range [{domain.lo}, {domain.hi}] ({domain.basis})")
        return None
    if isinstance(domain, G):
        # Owner ruling 48: for one lc a gate can print only one of its two words.
        if vocab is None:
            return ("slot_domain_unknown_14",
                    f"vocabulary gate {domain.basis!r} was checked without the lc's vocabulary")
        want = domain.for_vocab(vocab)
        if value != want:
            return ("slot_domain_escape_14",
                    f"value {value!r} is the gate's other word: {domain.requires!r} is "
                    f"{'' if domain.requires in vocab else 'not '}in this lc's vocabulary, so the "
                    f"gate prints {want!r} ({domain.basis})")
        return None
    if isinstance(domain, E):
        if value not in domain.members:
            return ("slot_domain_escape_14",
                    f"value {value!r} is not one of {list(domain.members)!r} ({domain.basis})")
        return None
    if not isinstance(domain, str):
        return ("slot_domain_unknown_14", f"domain {domain!r} is neither a registry id nor R(...)/E(...)")
    if domain in TYPE_ONLY:
        if domain == "text.derived" and not isinstance(value, str):
            return ("slot_domain_escape_14", f"derived text {value!r} is not a string")
        if domain == "num.derived" and (isinstance(value, bool) or not isinstance(value, (int, float))):
            return ("slot_domain_escape_14", f"derived value {value!r} is not a number")
        missing = type_only_reason(domain, why, tuple(src), given)
        return None if missing is None else ("slot_domain_type_only_14", missing)
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


def observe(node_id: str, seed: int, formatter: Optional[str] = None):
    """
    (problem, fills, values) for one path: the served payload, every recorded fill, and the
    generator's own QuestionContext.values observed at the formatter boundary -- so a
    "value:<key>" slot is compared with what was GENERATED (the answer included, which the
    payload's given_values deliberately omits). Read-only; restored in `finally`. §14 and
    §17 both render through here (one copy). An exception propagates to the caller.
    """
    from backend.app.services.orchestrator import PracticeOrchestrator
    from backend.app.services import orchestrator as _orch

    seen: Dict[str, Any] = {}
    real = _orch.apply_formatter

    def _spy(ctx, formatter_name, rng):
        seen.update(ctx.values or {})
        return real(ctx, formatter_name, rng)

    _orch.apply_formatter = _spy
    try:
        with capture() as fills:
            problem = PracticeOrchestrator.generate_problem(
                node_id=node_id, seed=seed, formatter=formatter,
                is_student_path=formatter is None).model_dump()
    finally:
        _orch.apply_formatter = real
    return problem, fills, seen


_VOCAB_CACHE: Dict[str, frozenset] = {}


def lc_vocab(node_id: str) -> frozenset:
    """
    The vocabulary the generator may print for `node_id` (`base_generator.generator_vocabulary`,
    the generator's own rule, never restated here): what a gate `G` is checked against. Raises
    if the lc is not in the knowledge graph.
    """
    if node_id not in _VOCAB_CACHE:
        from backend.app.practice_gen.generators.base_generator import generator_vocabulary, get_node
        node = get_node(node_id)
        if node is None:
            raise ValueError(f"§14: lc {node_id!r} is not in the knowledge graph")
        _VOCAB_CACHE[node_id] = frozenset(generator_vocabulary(node))
    return _VOCAB_CACHE[node_id]


def render_findings(node_id: str, seed: int, formatter: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """(label, where, reason) for one render of one lc (the student path unless `formatter`)."""
    return observed_findings(*observe(node_id, seed, formatter))


def observed_findings(problem: Dict[str, Any], fills: List[Any], seen: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """(label, where, reason) for one observed render (`observe`'s three results)."""
    from backend.app.practice_gen.validation.validate_language import _texts

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
    vocab = lc_vocab(problem["node_id"])
    out: List[Tuple[str, str, str]] = []
    for f in fills:
        why = replay(f)
        if why:
            out.append(("slot_template_mismatch_14", f.site, why))
        others = texts if produced[f.text] > 1 else texts - {f.text}
        srcs, whys = dict(f.sources), dict(f.reasons)
        for name, value, domain in f.slots:
            bad = check_slot(value, domain, given, others, why=whys.get(name), src=srcs.get(name, ()),
                             vocab=vocab)
            if bad:
                out.append((bad[0], f"{f.site} slot {name!r}", bad[1]))
    for where, text in _texts(problem):
        if text not in texts:
            out.append(("slot_text_unaccounted_14", where.split("[")[0],
                        f"{text[:90]!r} is not the text of any recorded fill: the site that "
                        f"builds it is not instrumented (formatter {problem.get('formatter_name')}, "
                        f"DNA {problem.get('dna_name')})"))
    return out


def _all_lcs() -> List[str]:
    from backend.app.practice_gen.registry import get_all_node_ids
    return sorted(get_all_node_ids())


def collect_findings(node_ids: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """{label: [finding, ...]}, one finding per (lc, label, where), naming its first seed."""
    from backend.app.practice_gen.registry import get_all_node_ids

    grouped: "OrderedDict[Tuple[str, str, str], Dict[str, Any]]" = OrderedDict()
    n_paths: Dict[str, int] = {}
    for node_id in (node_ids or sorted(get_all_node_ids())):
        lc_paths = paths(node_id)
        n_paths[node_id] = len(lc_paths)
        for seed, formatter in lc_paths:
            if formatter is None:
                found = render_findings(node_id, seed)
            else:
                # (f): a pinned path that refuses is a named finding (ruling 44b). Caught
                # around the generator call only (`observe`), never around this module's own
                # checks; the student path is never caught here.
                try:
                    observed = observe(node_id, seed, formatter)
                except Exception as exc:  # noqa: BLE001 - reported by name below, never skipped
                    # DISPOSITION: named-failure -- `slot_path_refused_14`, by lc, seed and formatter.
                    found = [("slot_path_refused_14", f"the pinned {formatter!r} render",
                              f"the render raised {type(exc).__name__}: {str(exc)[:200]}")]
                else:
                    found = observed_findings(*observed)
            for label, where, reason in found:
                key = (node_id, label, where)
                if key not in grouped:
                    grouped[key] = {"path": (seed, formatter), "reason": reason, "paths": set()}
                grouped[key]["paths"].add((seed, formatter))
    out: Dict[str, List[str]] = {label: [] for label in ASSERTIONS}
    for (node_id, label, where), g in grouped.items():
        owed = ("instrument the site with slots.fill/S (ruling 28)"
                if label in ("slot_text_unaccounted_14", "slot_unclassified_14")
                else "keep the value inside its declared domain, or correct the declaration"
                if label == "slot_domain_escape_14"
                else "record the template the text is really built from"
                if label == "slot_template_mismatch_14"
                else ("tighten the slot to value:/E/R/enum:/bank:/fill, or give it a registered "
                      "slots.DERIVED_REASONS kind and its src (owner rulings 42-43)")
                if label == "slot_domain_type_only_14"
                else ("make the advertised formatter serve every seed, or stop advertising it for "
                      "this lc (owner ruling 44b)")
                if label == "slot_path_refused_14"
                else "register the domain kind in validate_slots or fix the id")
        seed, formatter = g["path"]
        # A refusal's `where` already names its formatter (one finding per refused formatter).
        on = "" if formatter is None or label == "slot_path_refused_14" else f" formatter {formatter!r}"
        out[label].append(
            f"{node_id}: {where} at seed {seed}{on} ({len(g['paths'])} of {n_paths[node_id]} paths): "
            f"{g['reason']}. Reproduce: {path_call(node_id, seed, formatter)} under slots.capture(). "
            f"Owed: {owed}.")
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
    # The ruling-42 rollout, lc by lc: how many lcs still reach a type-only slot.
    lcs = list(node_ids) if node_ids else _all_lcs()
    open_lcs = sorted({item.split(":", 1)[0] for item in findings["slot_domain_type_only_14"]})
    print(f"  NOTE: ruling 42 rollout: {len(lcs) - len(open_lcs)} of {len(lcs)} lc(s) reach no "
          f"type-only slot without a reason; {len(open_lcs)} still do")
    print(f"  §14: {total} finding(s) over {scope} lc(s) x paths() (student seeds {SEEDS[0]}-{SEEDS[-1]} "
          f"plus every advertised formatter at seeds {', '.join(map(str, PINNED_SEEDS))})")
    return total == 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§14 learner-read text is a recorded fill of declared slots")
    ap.add_argument("--node-ids", help="comma-separated lc subset (proof mode)")
    args = ap.parse_args()
    return 0 if validate_all(args.node_ids.split(",") if args.node_ids else None) else 1


if __name__ == "__main__":
    sys.exit(main())
