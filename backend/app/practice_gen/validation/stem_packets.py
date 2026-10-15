"""
§17 stem packets -- what an LLM judge reads when it reviews an lc's stems (owner rulings 24, 26,
42 and 44; batch H4).

Ruling 24 moves LLM review from seeded samples to STEM TEMPLATES plus the declared DOMAIN of
every slot that fills them. This module builds that unit, per lc, from the generator's own
structured record (`slots.capture()`, ruling 28), never from learner-facing text:

  * it renders every path of `validate_slots.paths(lc)` -- the ONE enumeration §14 also renders
    (ruling 44b), so every family a judge approves is a family §14 domain-checks;
  * it keeps the fills that REACH learner-read text (`validate_language._texts`, the §1J
    classification §14 shares): a fill whose text is a learner-read field, or whose text fills a
    `fill` slot of a reaching fill (ruling 44a);
  * a FAMILY is (spine id, or the call site's module, template, renderer). The call site's LINE is
    left out of the key on purpose: an unrelated edit above a call site moves its line, and a
    review must not go stale over bytes the learner never sees. Two call sites in one module with
    the same template are therefore one family, their domains merged;
  * a wrapper is collapsed into what it prints only when every slot is `fill` AND its literal
    text adds no letter or digit (`{answer}`, `{p0}, {p1}`): ruling 44a. A wrapper that adds words
    (`{statement}. True or False?`) is a family of its own;
  * each slot's domain is rendered for a reader by RESOLVING it (ruling 44c): an `enum:`/`noun:`
    list by its members and a `bank:` field by its bank's rows (ruling 47, below), a runtime `E` by the union of its members (a
    vocabulary gate `G` by the ONE word it gives the lc, ruling 48, below) and an
    `R` by its lowest lo and highest hi over the enumerated renders, `value:<key>` by its key and
    what renders printed for it (ruling 50, below), a
    `fill` slot by the families whose text filled it, a type-only slot by its registered reason
    and `src`. Provenance (`src`, template `_src`) and the lc's `derives`/`computes` declarations
    (ruling 41) are listed, because §15 trusts them and ruling 41 says H4 reviews them;
  * each family says WHERE the learner reads it (owner ruling 46a, 2026-10-14): `appears_in`
    lists the learner-read fields (`validate_language._texts`' names, index dropped:
    `question_text`, `hints`, `format_data.options`, `distractors`, ...) its text was observed
    in, through wordless wrappers; `nested_in` lists the families it is printed inside. Found
    on the first real dispatch: a judge read the option family `{member}` as "the whole stem",
    because nothing in the packet said it is only ever an answer choice. The builder raises on
    a family with neither;
  * an item bank is printed ROW BY ROW in `banks` (owner ruling 47, 2026-10-14), each row with
    the fields this lc prints from it, and `one_row_per_problem` says whether every render
    enumerated printed its fields of the bank from ONE row. Found on the second real dispatch:
    printed as one flat list per field, a bank lost which answer each question is keyed to, and
    a judge FAILed a correctly keyed bank as "questions and answers can be mismatched";
  * only text the pg can print is shown (owner ruling 48, 2026-10-14): a vocabulary gate `G` shows
    the one word the generator's own vocabulary rule gives the lc (`prints`); a bank shows only
    the rows a render drew -- on `paths()` or on the student path at `SWEEP_SEEDS` -- with
    `rows_left_out`; and a runtime `E` whose declared members, at every render that fills it, lie
    in one unprinted field of the row that render drew is shown as that row's field (`read_from`).
    Found on the first fan-out: judges FAILed on "chart" (a gate's other word), on shape rows the
    lc never draws, and on categories shown apart from the subject row they belong to;
  * a fill whose every slot is a vocabulary gate (`{term}`) is one family PER GATE (owner ruling
    48e), so each gate word is shown nested only in the parents it fills; found on the first
    ruling-48 fan-out, where judges dropped any of an lc's gate words into any gate slot;
  * slots printed under ONE shared domain (`{p0}, {p1}, {p2}`) say whether every render observed
    -- `paths()` and the `SWEEP_SEEDS` student renders -- printed them as different values
    (`distinct_in_every_render`, owner ruling 48d; the key names the first render that repeated
    one). Found on the ruling-48 pilot: a judge FAILed a category list as able to repeat a member,
    which no render does;
  * a `value:<key>` slot shows what renders printed for it (owner ruling 50, 2026-10-15): over
    `paths()` and the `SWEEP_SEEDS` student renders, every number as runs of consecutive integers
    (`printed_runs`; ruling 50b, the same day: a lowest-highest pair hid gaps), else every value
    (`printed`). Found on the first fan-out
    on ruling 48e: all 2,122 such slots on 144 of 151 lcs showed only a key that the declared
    bounds never state, so judges guessed what `{comparison}` or `{word_form}` prints and quoted
    the guesses (213 quoted spans no packet contains, 81 of 151 replies unfileable);
  * the lc's competency text, clauses (`requires`), vocabulary gates and declared variants
    (ruling 26) and declared bounds complete the item.

The BLIND half (`build_item`) carries no lc id and no source path; the KEY half maps the item's
family ids back to modules, call sites and a path that reaches each one. `item_hash` is the
freshness key: the digest of exactly what the judge read (minus the opaque item id), so a
change to anything the judge read -- a template, a member, a bound, a provenance claim, a
clause -- changes it, and nothing the judge did not read does.

NAMED LIMITS (Scaling Mandate 6; also in docs/pgen_contract.md §17):
  1. Paths are `validate_slots.paths()` only (§14 limit 1): a family reached only by another
     seed, experience or difficulty profile is not in the packet. A pinned path that refuses
     contributes nothing here and is §14's `slot_path_refused_14`.
  2. A runtime `E`/`R` is resolved from the renders observed: a member or bound only an
     unvisited path produces is not shown (and §14 does not check it there either).
  3. A `value:<key>` slot shows what the renders observed printed for it (ruling 50), not its
     range: a value only another seed, a pinned formatter at another seed or another profile
     prints is not shown (sampling, as limit 9; measured 2026-10-14, runtime values do not
     saturate by 1,000 seeds), and a value printed only on a sweep render under a domain the
     enumerated renders never recorded for that slot is not shown. Its range is bounded where it
     is generated (§14 limit 5); the judge is told the values are observed, not a bound.
  4. Text no fill produced (un-instrumented, §14 `slot_text_unaccounted_14`) has no family and is
     not in the packet; §14 names it.
  5. One-member domains of the value itself (`E((x,), ...)`) are shown as written; they bound
     nothing, and the judge is told so only by reading them.
  6. A `fill` slot's families are matched by TEXT (the record has no pointer from a fill to the
     fill it nests): when two families can print the same string ("impossible" as a term and
     as a bank answer), both are listed. Over-inclusive, never lossy.
  7. `appears_in` / `nested_in` are matched by text the same way (limit 6): a family whose text
     happens to equal another field's text (an option "5" and a hint "5") is listed in both.
     Over-inclusive, never lossy. They are observed over `paths()` only (limit 1).
  8. `banks` prints the rows drawn on `paths()` or on the student path at `SWEEP_SEEDS` (41-240;
     ruling 48b, superseding ruling 47's every-row printing): a row first drawn only later, or
     only by a pinned formatter or another profile, is not shown (measured 2026-10-14 on 46 lcs:
     none). `one_row_per_problem` is observed over `paths()` only (limit 1), and rows are matched
     by value: a render whose values all occur together in some row counts as one-row even if the
     generator took them from two rows that happen to share them, and both rows count as drawn.
  9. A runtime `E` keeps every DECLARED member: sampling cannot tell a rare member from one the lc
     can never print (measured 2026-10-14: no saturation at 1,000 seeds), so only a gate `G`
     (decided by its declared rule) and bank rows are narrowed. A vocabulary-conditioned word
     recorded as a plain `E` is shown with both its words.
 10. The pairing of a runtime `E` with the drawn row (ruling 48c) is observed only on renders that
     also print a field of that bank; a slot filled where none is printed stays a runtime list.
 11. `distinct_in_every_render` is OBSERVED over `paths()` and the `SWEEP_SEEDS` student renders
     only: a repeat that only another seed, a pinned formatter at another seed or another profile
     produces is not seen, so `true` means no observed render repeated a value, not that none can
     (sampling, as limit 9). `false` is always a real render, named in the key.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import string
import sys
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from backend.app.practice_gen.slots import DERIVED_REASONS, RENDERERS, TRANSFORMS, E, G, R

# Bumped only when the item's SHAPE changes on purpose; it is part of every hash, so a bump
# stales every review (which is what a shape change must do). `stem_review_hash_drift_17`
# catches a hash that changes WITHOUT a bump. 2 (2026-10-14, owner ruling 46a): every family
# carries `appears_in` / `nested_in`, the learner-read fields its text was observed in.
# 3 (2026-10-14, owner ruling 47): an item bank is printed as its rows in `banks`, not as one
# flat list per field, with whether each problem printed its fields from one row.
# 4 (2026-10-14, owner ruling 48): only text the pg can print -- a vocabulary gate shows the one
# word it gives the lc, a bank only the rows a render drew (enumerated paths plus SWEEP_SEEDS),
# and a runtime slot read from the drawn row is shown as that row's field.
# 5 (2026-10-14, owner ruling 48d): slots printed under one shared domain say whether every
# render observed printed them as different values (`distinct_in_every_render`).
# 6 (2026-10-14, owner ruling 48e): a pure vocabulary-gate fill (`{term}`) is one family per gate,
# nested only in the parents its own word fills.
# 7 (2026-10-15, owner ruling 50): a `value:<key>` slot shows what renders printed for it.
# 8 (2026-10-15, owner ruling 50b): printed numbers as lossless runs, not a lowest-highest pair.
HASH_VERSION = 8

# Owner ruling 48b/d: extra STUDENT-path seeds rendered only to learn which bank rows the lc draws
# and whether slots sharing a domain ever print one value twice (never judged, never a family
# source). Measured 2026-10-14 on 46 lcs (seeds 41-1040 and every
# advertised formatter pinned at 41-240): every bank row first drawn outside the 43 enumerated
# renders was drawn by seed 240, and none later.
SWEEP_SEEDS = tuple(range(41, 241))

_ALNUM = re.compile(r"[^\W_]")            # a letter or digit, in any script


def _canon(obj: Any) -> Any:
    """A JSON-ready, order-stable copy. A value with no stable text form raises (integrity)."""
    if isinstance(obj, dict):
        return {str(k): _canon(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_canon(v) for v in obj]
    if isinstance(obj, (set, frozenset)):
        return sorted((_canon(v) for v in obj), key=_dump)
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        return repr(obj)
    text = repr(obj)
    if " at 0x" in text:
        raise TypeError(f"stem packet value {text[:80]} has no stable text form (an object address)")
    return text


def _dump(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def item_hash(item: Dict[str, Any]) -> str:
    """The freshness key: sha256 over everything the judge read, the opaque item id excluded."""
    body = {k: v for k, v in item.items() if k != "item"}
    return hashlib.sha256(f"stem-v{HASH_VERSION}:{_dump(_canon(body))}".encode("utf-8")).hexdigest()


def digest(obj: Any) -> str:
    """sha256 of the canonical JSON of `obj` (a whole packet item, a raw reply)."""
    return hashlib.sha256(_dump(_canon(obj)).encode("utf-8")).hexdigest()


def _literal(template: str) -> str:
    """A template's own text: every `{slot}` removed, escaped braces kept as braces."""
    return re.sub(r"\{[^{}]*\}", "", template.replace("{{", "\0").replace("}}", "\1")).replace("\0", "{").replace("\1", "}")


def is_wordless_wrapper(fill: Any) -> bool:
    """Ruling 44a: every slot is `fill` and the template adds no letter or digit."""
    return bool(fill.slots) and all(d == "fill" for _n, _v, d in fill.slots) \
        and not _ALNUM.search(_literal(fill.template))


def _module(site: str) -> str:
    return site.rsplit(":", 1)[0]


def family_key(fill: Any) -> Tuple[str, str, str]:
    """
    (spine id or call-site module, template, renderer name or ''). A fill whose every slot is a
    vocabulary gate (`VocabGated.resolve`'s `{term}`) is keyed by its gate(s) too (owner ruling
    48e): keyed by module and template alone, every gate word an lc prints was ONE family nested
    in every parent any of them fills, so a judge read each word as able to fill each slot
    ("Use the how much time has passed to find the answer"). Measured 2026-10-14: 83 of 151 lcs
    print more than one gate word through that one family.
    """
    source = fill.renderer_ref or _module(fill.site)
    if fill.slots and all(isinstance(d, G) for _n, _v, d in fill.slots):
        source = f"{source} [gate {', '.join(sorted({d.requires for _n, _v, d in fill.slots}))}]"
    return (source, fill.template, fill.renderer or "")


def reaching(problem: Dict[str, Any], fills: List[Any]) -> List[Any]:
    """The fills whose text a learner reads, directly or nested through `fill` slots, in record order."""
    from backend.app.practice_gen.validation.validate_language import _texts

    read = {text for _where, text in _texts(problem)}
    by_text: Dict[str, List[Any]] = {}
    for f in fills:
        by_text.setdefault(f.text, []).append(f)
    seen: set = set()
    stack = [f for f in fills if f.text in read]
    while stack:
        f = stack.pop()
        if id(f) in seen:
            continue
        seen.add(id(f))
        for _name, value, domain in f.slots:
            if domain == "fill":
                stack.extend(g for g in by_text.get(str(value), []) if g is not f)
    return [f for f in fills if id(f) in seen]


def field_roles(problem: Dict[str, Any], reach: List[Any]) -> Dict[int, Tuple[set, set]]:
    """
    {id(fill): (fields, parents)} for every reaching fill (owner ruling 46a). `fields` are the
    learner-read fields (`validate_language._texts`' names, list index dropped: `hints`, not
    `hints[2]`) whose text IS the fill's text, or the text of a wordless wrapper it fills, since
    such a wrapper adds nothing; `parents` are the family keys of the non-wrapper fills whose
    `fill` slot it fills (it is read inside them). Matched by text, as `reaching` is.
    """
    from backend.app.practice_gen.validation.validate_language import _texts

    direct: Dict[str, set] = {}
    for where, text in _texts(problem):
        direct.setdefault(text, set()).add(where.split("[", 1)[0])
    holders: Dict[str, List[Any]] = {}
    for g in reach:
        for _n, v, d in g.slots:
            if d == "fill":
                holders.setdefault(str(v), []).append(g)
    memo: Dict[int, Tuple[set, set]] = {}
    visiting: set = set()

    def roles(f: Any) -> Tuple[set, set]:
        if id(f) in memo:
            return memo[id(f)]
        if id(f) in visiting:          # two wrappers printing the same text fill each other
            return set(), set()
        visiting.add(id(f))
        fields, parents = set(direct.get(f.text, ())), set()
        for g in holders.get(f.text, []):
            if g is f:
                continue
            if is_wordless_wrapper(g):
                up_fields, up_parents = roles(g)
                fields |= up_fields
                parents |= up_parents
            else:
                parents.add(family_key(g))
        visiting.discard(id(f))
        memo[id(f)] = (fields, parents)
        return memo[id(f)]

    return {id(f): roles(f) for f in reach}


def observe_lc(node_id: str) -> Tuple[List[Tuple[int, Optional[str], Dict[str, Any], List[Any], Dict[str, Any]]],
                                      List[Tuple[int, str, str]]]:
    """
    (renders, refused): every path of `validate_slots.paths(node_id)` rendered under capture, as
    (seed, formatter, problem, fills, values); and (seed, formatter, error) for each PINNED path
    that refused (§14 names those as `slot_path_refused_14`). A student-path raise propagates.
    """
    from backend.app.practice_gen.validation import validate_slots as VS

    renders, refused = [], []
    for seed, formatter in VS.paths(node_id):
        if formatter is None:
            problem, fills, values = VS.observe(node_id, seed)
        else:
            try:
                problem, fills, values = VS.observe(node_id, seed, formatter)
            except Exception as exc:  # noqa: BLE001 - returned by name; §14 reports it
                # DISPOSITION: named-failure -- returned to the caller and printed by §17;
                # §14 names the same path as `slot_path_refused_14` (owner ruling 44b).
                refused.append((seed, formatter, f"{type(exc).__name__}: {str(exc)[:160]}"))
                problem = None
        if problem is not None:
            renders.append((seed, formatter, problem, fills, values))
    return renders, refused


def _bank_rows(dotted: str) -> List[Dict[str, Any]]:
    """The rows of the generator's own item bank `module.NAME`: a list of dicts, else it raises."""
    module_path, _, name = dotted.rpartition(".")
    rows = getattr(importlib.import_module(module_path), name)
    if not isinstance(rows, (list, tuple)) or not all(isinstance(r, dict) for r in rows):
        raise TypeError(f"stem packet: bank {dotted!r} is not a list of dicts")
    return list(rows)


def _sweep(node_id: str, dotteds: List[str]) -> Tuple[Dict[str, set], Dict[Tuple[str, str, str], List[Any]],
                                                       Dict[Tuple[Any, ...], set]]:
    """
    (rows, occurrences, printed) observed on the STUDENT path at `SWEEP_SEEDS` (owner rulings
    48b/d, 50): {bank: row indices drawn}, for the banks the enumerated renders already print,
    matched by value as on those renders; {family key: [((seed, None), {slot: value}), ...]}, one
    entry per reaching fill; and {(family key, slot, `value:<key>` domain): {`_printed` value}}.
    Only these three things are read: the renders are never judged, and a family or a bank only
    they reach is not in the packet (limit 1). A student-path raise propagates.
    """
    from backend.app.practice_gen.validation import validate_slots as VS

    rows: Dict[str, set] = {d: set() for d in dotteds}
    occ: Dict[Tuple[str, str, str], List[Any]] = {}
    printed: Dict[Tuple[Any, ...], set] = {}
    for seed in SWEEP_SEEDS:
        problem, fills, _values = VS.observe(node_id, seed)
        drawn: Dict[str, set] = {}
        for f in reaching(problem, fills):
            for _n, v, d in f.slots:
                if isinstance(d, str) and d.startswith("bank:"):
                    dotted, _, fld = d[len("bank:"):].rpartition(":")
                    drawn.setdefault(dotted, set()).add((fld, _dump(_canon(v))))
            if not is_wordless_wrapper(f):
                occ.setdefault(family_key(f), []).append(((seed, None), {n: _dump(_canon(v)) for n, v, _d in f.slots}))
                for n, v, d in f.slots:
                    if isinstance(d, str) and d.startswith("value:"):
                        printed.setdefault((family_key(f), n, d), set()).add(_printed(v))
        for dotted, pairs in drawn.items():
            if dotted in rows:
                flds = {fld for fld, _v in pairs}
                rows[dotted] |= {i for i, r in enumerate(_bank_rows(dotted)) if pairs <= _row_pairs(r, flds)}
    return rows, occ, printed


def _printed(value: Any) -> Tuple[str, Any]:
    """Ruling 50: one printed value of a `value:<key>` slot -- ("n", the number) or ("t", its canonical JSON)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return ("n", value)
    return ("t", _dump(_canon(value)))


def _runs(numbers: List[Any]) -> List[List[Any]]:
    """
    Ruling 50b: sorted distinct numbers as [first, last] runs of consecutive integers -- lossless,
    and compact where values are dense. A lowest-highest pair hid gaps: mat_g2_na_q3_2's table
    factor prints only 2, 3, 4, 5 and 10, shown as "2-10", and two judges FAILed on "7 x 8".
    A non-integer is a run of its own.
    """
    out: List[List[Any]] = []
    for v in numbers:
        if out and isinstance(v, int) and isinstance(out[-1][1], int) and v == out[-1][1] + 1:
            out[-1][1] = v
        else:
            out.append([v, v])
    return out


def _runs_text(runs: List[List[Any]]) -> str:
    """
    The runs as ONE line ("2 to 5, 10"): printed as JSON lists they took four prompt lines per run,
    and 53 of 151 prompts passed 2,000 lines (one 10,312) -- a judge then reads in pieces and the
    audit refuses a partial read. Lossless: every run is written out.
    """
    return ", ".join(str(a) if a == b else f"{a} to {b}" for a, b in runs)


def _row_pairs(row: Dict[str, Any], fields: set) -> set:
    """(field, canonical member) for every value a row offers in `fields` (a list field: each member)."""
    out = set()
    for fld in fields:
        if fld in row:
            v = row[fld]
            out |= {(fld, _dump(_canon(m))) for m in (v if isinstance(v, (list, tuple)) else [v])}
    return out


def _resolve_static(domain: str) -> Dict[str, Any]:
    """A registry-id domain rendered for a reader (members resolved by §14's own resolvers)."""
    from backend.app.practice_gen.validation import validate_slots as VS

    if domain.startswith("enum:"):
        obj = VS._enum(domain[len("enum:"):])
        members = list(obj) if isinstance(obj, dict) else VS._members(obj)   # `in` tests dict KEYS
        return {"domain": "one of a fixed list", "list": domain.rsplit(".", 1)[-1], "members": _canon(members)}
    if domain.startswith("noun:"):
        return {"domain": "a noun from a fixed list, or its plural", "list": domain.rsplit(".", 1)[-1],
                "members": _canon(VS._members(VS._enum(domain[len("noun:"):])))}
    if domain.startswith("bank:"):
        # The bank is printed once, ROW BY ROW, in the item's `banks` table (owner ruling 47);
        # `_bank` is the module path that table is built from, replaced by its label on output.
        dotted, _, fld = domain[len("bank:"):].rpartition(":")
        _bank_rows(dotted)
        return {"domain": "a field of a fixed item bank", "_bank": dotted, "field": fld}
    if domain.startswith("value:"):
        return {"domain": "repeats a generated value", "key": domain[len("value:"):]}
    if domain in ("num.derived", "text.derived"):
        return {"domain": "a number computed by the generator" if domain == "num.derived"
                else "text computed by the generator"}
    if domain == "fill":
        return {"domain": "nested learner text"}
    raise ValueError(f"stem packet: domain id {domain!r} has no kind this builder renders")


def _transformation(name: str) -> Optional[Dict[str, str]]:
    if not name:
        return None
    if name in TRANSFORMS:
        doc = (TRANSFORMS[name].__doc__ or "").strip().splitlines()[0]
        return {"name": name, "meaning": doc}
    if name in RENDERERS:
        return {"name": name, "meaning": "the template is rendered by the spine renderer, which also "
                                         "chooses a/an by sound and the singular after a count of 1"}
    raise ValueError(f"stem packet: renderer {name!r} is neither a registered transform nor renderer")


def build_item(node_id: str, renders=None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    (item, key) for one lc. `item` is the blind half WITHOUT its opaque "item" id (the dispatcher
    assigns one); `key` maps family ids to their modules, first call site and a reaching path.
    """
    from backend.app.practice_gen.registry import get_node_competency_bounds, get_node_dnas, get_node_info
    from backend.app.practice_gen.validation.judgment_packets import _variant_coverage_candidates

    info = get_node_info(node_id)
    if info is None:
        raise ValueError(f"stem packet: unknown lc {node_id!r}")
    if renders is None:
        renders, _refused = observe_lc(node_id)

    fams: "OrderedDict[Tuple[str, str, str], Dict[str, Any]]" = OrderedDict()
    derivations = set()
    nested_of: Dict[Tuple[str, str, str], Dict[str, set]] = {}
    # Ruling 47: per bank (module path), the fields this lc prints from it and the first render
    # whose printed fields of it are found together in NO single row (None: every render's are).
    bank_seen: Dict[str, Dict[str, Any]] = {}
    # Ruling 48: the vocabulary a gate is resolved against (the generator's own rule); per
    # render, the bank rows it drew; per (family, slot, basis) of a runtime E, the members it
    # declared at each render -- to find a slot that is really a field of the drawn row.
    from backend.app.practice_gen.validation.validate_slots import lc_vocab
    vocab = lc_vocab(node_id)
    render_rows: List[Dict[str, set]] = []
    e_seen: Dict[Tuple[Any, ...], List[Tuple[int, frozenset]]] = {}

    for ri, (seed, formatter, problem, fills, values) in enumerate(renders):
        drawn: Dict[str, set] = {}
        reach = reaching(problem, fills)
        by_text: Dict[str, List[Any]] = {}
        for f in reach:
            by_text.setdefault(f.text, []).append(f)
        roles = field_roles(problem, reach)

        def sources(value: str, holder: Any, depth: int = 0) -> set:
            """Family keys whose text fills a `fill` slot, looking through wordless wrappers."""
            out = set()
            for g in by_text.get(str(value), []):
                if g is holder:
                    continue
                if is_wordless_wrapper(g):
                    if depth > 50:
                        raise RecursionError(f"stem packet: wrapper nesting past 50 at {g.site}")
                    for _n, v, _d in g.slots:
                        out |= sources(v, g, depth + 1)
                else:
                    out.add(family_key(g))
            return out

        for f in reach:
            if is_wordless_wrapper(f):
                continue
            key = family_key(f)
            fam = fams.setdefault(key, {"site": f.site, "path": (seed, formatter), "slots": OrderedDict(),
                                        "chosen_by": set(), "fields": set(), "nested_in": set(), "occ": []})
            fam["occ"].append(((seed, formatter), {n: _dump(_canon(v)) for n, v, _d in f.slots}))
            fields, parents = roles[id(f)]
            fam["fields"] |= fields
            fam["nested_in"] |= parents
            srcs, whys = dict(f.sources), dict(f.reasons)
            fam["chosen_by"] |= set(srcs.get("__template__", ()))
            for name, value, domain in f.slots:
                slot = fam["slots"].setdefault(name, OrderedDict())
                if isinstance(domain, R):
                    if isinstance(domain.lo, bool) or not isinstance(domain.lo, (int, float)) \
                            or isinstance(domain.hi, bool) or not isinstance(domain.hi, (int, float)):
                        raise TypeError(f"stem packet: R bounds {domain.lo!r}..{domain.hi!r} at {f.site} are not numbers")
                    d = slot.setdefault(("R", domain.basis), {"domain": "a number in a range", "basis": domain.basis,
                                                             "lo": domain.lo, "hi": domain.hi})
                    d["lo"], d["hi"] = min(d["lo"], domain.lo), max(d["hi"], domain.hi)
                elif isinstance(domain, G):
                    # Ruling 48a: for this lc the gate prints ONE word; the other is left out.
                    d = slot.setdefault(("G", domain.basis, domain.requires), {
                        "domain": "the one word a vocabulary gate gives this lc", "basis": domain.basis,
                        "requires_vocab": domain.requires, "prints": _canon(domain.for_vocab(vocab)),
                        "words_left_out": 1})
                elif isinstance(domain, E):
                    d = slot.setdefault(("E", domain.basis), {"domain": "one of the generator's own choices",
                                                             "basis": domain.basis, "members": set()})
                    d["members"] |= {_dump(_canon(m)) for m in domain.members}
                    e_seen.setdefault((key, name, domain.basis), []).append(
                        (ri, frozenset(_dump(_canon(m)) for m in domain.members)))
                elif domain is None:
                    d = slot.setdefault(("none",), {"domain": "UNCLASSIFIED (no domain recorded)"})
                elif isinstance(domain, str):
                    d = slot.setdefault(("id", domain), _resolve_static(domain))
                    if domain == "fill":
                        d.setdefault("_families", set()).update(sources(value, f))
                    elif domain.startswith("bank:"):
                        dotted, _, fld = domain[len("bank:"):].rpartition(":")
                        drawn.setdefault(dotted, set()).add((fld, _dump(_canon(value))))
                    elif domain.startswith("value:"):
                        d.setdefault("_printed", set()).add(_printed(value))
                else:
                    raise TypeError(f"stem packet: domain {domain!r} at {f.site} is not a str, R or E")
                if srcs.get(name):
                    d.setdefault("_from", set()).update(srcs[name])
                if whys.get(name):
                    d["reason"] = whys[name]
        for dv in getattr(fills, "derivations", []):
            derivations.add((dv.kind, dv.key, tuple(dv.src)))
        rows_here: Dict[str, set] = {}
        for dotted, pairs in drawn.items():
            seen_b = bank_seen.setdefault(dotted, {"fields": set(), "mixed_at": None})
            flds = {fld for fld, _v in pairs}
            seen_b["fields"] |= flds
            rows_here[dotted] = {i for i, r in enumerate(_bank_rows(dotted)) if pairs <= _row_pairs(r, flds)}
            if seen_b["mixed_at"] is None and not rows_here[dotted]:
                seen_b["mixed_at"] = [seed, formatter]
        render_rows.append(rows_here)

    # Ruling 48c: a runtime E whose declared members, at EVERY render that fills it, lie in one
    # field this lc does not otherwise print of a row that render drew, is that row's field (the
    # pictograph's categories are its `_THEMES` row's own). Observed, never predicted; two
    # candidate fields for one slot raise rather than choose.
    paired: Dict[Tuple[Any, ...], Tuple[str, str]] = {}
    for occ_key, occ in e_seen.items():
        cands: Optional[set] = None
        for ri, members in occ:
            here = set()
            for dotted, idxs in render_rows[ri].items():
                rows = _bank_rows(dotted)
                for i in idxs:
                    for fld, v in rows[i].items():
                        if fld in bank_seen[dotted]["fields"]:
                            continue
                        if members <= {_dump(_canon(m)) for m in (v if isinstance(v, (list, tuple)) else [v])}:
                            here.add((dotted, fld))
            cands = here if cands is None else cands & here
            if not cands:
                break
        if cands:
            if len(cands) > 1:
                raise ValueError(f"stem packet: slot {occ_key[1]!r} ({occ_key[2]}) at {fams[occ_key[0]]['site']} "
                                 f"matches {len(cands)} bank fields {sorted(cands)}; refusing to choose one")
            paired[occ_key] = next(iter(cands))
    paired_fields: Dict[str, set] = {}
    for (k, name, basis), (dotted, fld) in paired.items():
        slot = fams[k]["slots"][name]
        del slot[("E", basis)]
        slot[("id", f"bank:{dotted}:{fld}")] = {"domain": "a field of a fixed item bank", "_bank": dotted,
                                                "field": fld, "read_from": "the row drawn for the problem"}
        paired_fields.setdefault(dotted, set()).add(fld)
    sweep, sweep_occ, sweep_printed = _sweep(node_id, sorted(bank_seen))
    # Ruling 50: a generated value's sweep prints join the slot's own, where the enumerated renders
    # recorded that slot under that same `value:` domain (limit 3).
    for (k, name, domain), seen_v in sweep_printed.items():
        d = fams.get(k, {}).get("slots", {}).get(name, {}).get(("id", domain))
        if d is not None:
            d["_printed"] |= seen_v

    order = sorted(fams, key=lambda k: (k[0], k[1], k[2]))
    ids = {k: f"F{i + 1:02d}" for i, k in enumerate(order)}
    families, key_families, used_reasons = [], OrderedDict(), set()
    # A fixed list (`enum:`/`noun:`) is printed ONCE, in `lists`, and named by every slot that
    # draws from it: measured 2026-10-13, inlining it per slot made mat_g2_na_q2_7's packet
    # 173,763 characters, most of them one 2,350-character pool repeated. Nothing is dropped:
    # every member is printed, and the table is part of the hash.
    lists: "OrderedDict[str, Any]" = OrderedDict()
    # An item bank is printed ONCE, in `banks`, as its ROWS (owner ruling 47, 2026-10-14). Until
    # then each field was a flat list of its own, so a judge could not tell which answer a question
    # is keyed to: the first S441-001 judge FAILed `{answer}` and `{question}` as mismatchable,
    # though pictographs.py draws one row whole. Each row shows the fields this lc prints from the
    # bank; `one_row_per_problem` says whether every render enumerated printed its fields of the
    # bank from one row (observed, never assumed: `fmt_pictograph` fills a bank's symbol and
    # subject at different call sites).
    banks: "OrderedDict[str, Any]" = OrderedDict()
    bank_label: Dict[str, str] = {}
    key_banks: "OrderedDict[str, Any]" = OrderedDict()
    for dotted in sorted(bank_seen):
        name, n = dotted.rsplit(".", 1)[-1], 1
        label = name
        while label in banks:
            n += 1
            label = f"{name}#{n}"
        flds = sorted(bank_seen[dotted]["fields"] | paired_fields.get(dotted, set()))
        # Ruling 48b: only the rows a render drew -- on the enumerated paths or the sweep.
        drawn_rows = set().union(*(rr.get(dotted, set()) for rr in render_rows)) | sweep[dotted]
        carrying = [i for i, r in enumerate(_bank_rows(dotted)) if any(f in r for f in flds)]
        shown = [i for i in carrying if i in drawn_rows]
        banks[label] = {"fields": flds, "one_row_per_problem": bank_seen[dotted]["mixed_at"] is None,
                        "rows": [{f: _bank_rows(dotted)[i][f] for f in flds if f in _bank_rows(dotted)[i]}
                                 for i in shown],
                        "rows_left_out": len(carrying) - len(shown)}
        bank_label[dotted] = label
        key_banks[label] = {"module": dotted, "first_render_not_from_one_row": bank_seen[dotted]["mixed_at"],
                            "rows_drawn": shown, "sweep_seeds": [SWEEP_SEEDS[0], SWEEP_SEEDS[-1]]}

    def _table(name: str, members: Any) -> str:
        # Each distinct member once, in the list's own order (a bank repeats answers across rows;
        # membership is what the slot is checked against, not multiplicity).
        unique, seen_m = [], set()
        for m in members:
            if _dump(m) not in seen_m:
                seen_m.add(_dump(m))
                unique.append(m)
        members = unique
        label, n = name, 1
        while label in lists and lists[label] != members:
            n += 1
            label = f"{name}#{n}"
        lists[label] = members
        return label

    for k in order:
        fam = fams[k]
        slots_out = OrderedDict()
        for name, kinds in fam["slots"].items():
            descs = []
            for kind_key in sorted(kinds, key=_dump):
                d = dict(kinds[kind_key])
                if "members" in d and isinstance(d["members"], set):
                    d["members"] = [json.loads(m) for m in sorted(d["members"])]
                elif "members" in d:
                    d["members_in_list"] = _table(d.pop("list"), d.pop("members"))
                if "_bank" in d:
                    d["bank"] = bank_label[d.pop("_bank")]
                if "_printed" in d:
                    # Ruling 50: what renders printed for a generated value -- every number as runs of
                    # consecutive integers (ruling 50b: a lowest-highest pair hid gaps), else every
                    # value (observed, not a bound: limit 3).
                    seen_v = d.pop("_printed")
                    if all(kind == "n" for kind, _v in seen_v):
                        d["printed_runs"] = _runs_text(_runs(sorted({v for _k, v in seen_v})))
                    else:
                        d["printed"] = [v if kind == "n" else json.loads(v)
                                        for kind, v in sorted(seen_v, key=lambda kv: (kv[0], _dump(kv[1])))]
                if "_families" in d:
                    d["families"] = sorted(ids[x] for x in d.pop("_families") if x in ids)
                if "_from" in d:
                    d["derived_from_values"] = sorted(d.pop("_from"))
                if "reason" in d:
                    used_reasons.add(d["reason"])
                descs.append(d)
            slots_out[name] = descs
        # Slots with IDENTICAL domains are printed once with all their names (a join's p0..pN
        # share one domain: measured 2026-10-13, printing it per member made one packet
        # 127,927 characters). Lossless: every name and every domain is still printed.
        # Guard (found 2026-10-13 in a real packet: a slot was printed under its LIST's name,
        # because a loop variable was reused): the slot names printed are exactly the names the
        # generator recorded, and every field of the template is among them (a renderer such as
        # the spine may record more: its inflection arguments). Otherwise the builder raises.
        fields = {f for _lit, f, _spec, _conv in string.Formatter().parse(k[1]) if f is not None}
        if set(slots_out) != set(fam["slots"]) or not fields <= set(slots_out):
            raise ValueError(f"stem packet: family {k[1]!r} at {fam['site']} prints slots {sorted(slots_out)}; "
                             f"recorded {sorted(fam['slots'])}; template fields {sorted(fields)}")
        grouped: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        for name, descs in slots_out.items():
            grouped.setdefault(_dump(_canon(descs)), {"slots": [], "domains": descs})["slots"].append(name)
        # Ruling 48d: slots printed under ONE domain say whether any render observed (enumerated
        # paths and the SWEEP_SEEDS student renders) printed one value twice among them. Found on
        # the ruling-48 pilot: a judge FAILed `{p0}, {p1}, {p2}` as able to repeat a category,
        # which no render does (a theme's six distinct categories, printed as a prefix).
        repeats: Dict[str, Any] = {}
        for g in grouped.values():
            if len(g["slots"]) > 1:
                first = None
                for where, vals in fam["occ"] + sweep_occ.get(k, []):
                    got = [vals[n] for n in g["slots"] if n in vals]
                    if len(set(got)) < len(got):
                        first = list(where)
                        break
                g["distinct_in_every_render"] = first is None
                if first is not None:
                    repeats[",".join(g["slots"])] = first
        # Ruling 46a: where the learner reads this family's text. A family seen in no field and
        # nested in no other family reached learner text by no path this builder can name.
        nested = sorted(ids[p] for p in fam["nested_in"] if p in ids and p != k)
        if not fam["fields"] and not nested:
            raise ValueError(f"stem packet: family {k[1]!r} at {fam['site']} reaches learner text, yet is in no "
                             f"learner-read field and nested in no packeted family")
        families.append({
            "id": ids[k],
            "template": k[1],
            "appears_in": sorted(fam["fields"]),
            "nested_in": nested,
            "transformation": _transformation(k[2]),
            "slots": list(grouped.values()),
            "template_chosen_by_values": sorted(fam["chosen_by"]),
        })
        key_families[ids[k]] = {"source": k[0], "first_site": fam["site"], "renderer": k[2],
                                "path": list(fam["path"]), "first_render_repeating": repeats}

    bounds = []
    for dna in get_node_dnas(node_id):
        bounds.append(_canon(get_node_competency_bounds(node_id, dna)))
    item = {
        "competency": {"text": info.get("competency", ""), "grade": info.get("grade"),
                       "quarter": info.get("quarter")},
        "clauses": [{"id": r.get("id"), "kind": r.get("kind"), "clause": r.get("clause")}
                    for r in (info.get("requires") or [])],
        "vocabulary": {k: _canon(info.get(k)) for k in (
            "student_vocab", "curriculum_vocab", "introduces_vocab", "cumulative_vocab",
            "NOT_YET_KNOWN", "sentence_max_words", "number_format")},
        "declared_variants": _canon(sorted(_variant_coverage_candidates(node_id), key=_dump)),
        "declared_bounds": bounds,
        "families": _canon(families),
        "lists": _canon(lists),
        "banks": _canon(banks),
        "value_derivations": [{"kind": kind, "key": key, "from": list(src)}
                              for kind, key, src in sorted(derivations)],
        "reason_kinds": {k: DERIVED_REASONS[k] for k in sorted(used_reasons)},
    }
    key = {"node_id": node_id, "families": key_families, "banks": key_banks}
    return item, key


def coverage_gaps(item: Dict[str, Any], key: Dict[str, Any], renders) -> List[Tuple[int, Optional[str], str]]:
    """
    (seed, formatter, text) for every learner-read field whose producing fill -- or, through a
    wordless wrapper, every fill it nests -- belongs to no family in the item. An independent,
    top-down walk from each field (not `build_item`'s own loop), so a builder that drops a family
    is caught here by name (`stem_family_unpacketed_17`).
    """
    from backend.app.practice_gen.validation.validate_language import _texts

    packeted = {(f["source"], fam["template"], f["renderer"])
                for fam, f in ((fam, key["families"][fam["id"]]) for fam in item["families"])}
    gaps = []
    for seed, formatter, problem, fills, _values in renders:
        by_text: Dict[str, List[Any]] = {}
        for f in fills:
            by_text.setdefault(f.text, []).append(f)

        def covered(text: str, holder: Any = None, depth: int = 0) -> bool:
            producers = [g for g in by_text.get(text, []) if g is not holder]
            if not producers:
                return True        # un-instrumented text: §14's finding, not a packet gap
            for g in producers:
                if family_key(g) in packeted:
                    if all(covered(str(v), g, depth + 1) for _n, v, d in g.slots if d == "fill"):
                        return True
                elif is_wordless_wrapper(g) and depth < 50:
                    if all(covered(str(v), g, depth + 1) for _n, v, _d in g.slots):
                        return True
            return False

        for _where, text in _texts(problem):
            if not covered(text):
                gaps.append((seed, formatter, text))
    return gaps


def prompt_block(item: Dict[str, Any], item_id: str) -> str:
    """The text a judge reads for one item: its JSON, printed whole (no truncation, no dedup)."""
    return json.dumps({"item": item_id, **item}, ensure_ascii=False, indent=1)


def _main() -> int:
    ap = argparse.ArgumentParser(description="Build blind §17 stem packets (one item per lc) and their key.")
    ap.add_argument("--nodes", required=True, help="comma-separated lc ids")
    ap.add_argument("--prefix", required=True, help="opaque item id prefix, e.g. S441")
    ap.add_argument("--packets", required=True, help="output: the blind items (what judges see)")
    ap.add_argument("--key", required=True, help="output: item id -> lc, hash and families (judges never see it)")
    args = ap.parse_args()
    packets, keys = [], {}
    for i, node_id in enumerate(n.strip() for n in args.nodes.split(",") if n.strip()):
        renders, refused = observe_lc(node_id)
        item, key = build_item(node_id, renders)
        gaps = coverage_gaps(item, key, renders)
        if gaps:
            raise SystemExit(f"{node_id}: the packet misses {len(gaps)} learner-read field(s), first "
                             f"{gaps[0]!r}: refusing to write a packet that omits a reachable family")
        item_id = f"{args.prefix}-{i + 1:03d}"
        packets.append({"item": item_id, **item})
        keys[item_id] = {**key, "item_hash": item_hash(item), "refused_paths": refused}
        print(f"{item_id}: {len(item['families'])} families, {len(item['clauses'])} clauses, "
              f"{len(refused)} refused pinned path(s)")
    with open(args.packets, "w", encoding="utf-8") as fh:
        json.dump(packets, fh, ensure_ascii=False, indent=1)
    with open(args.key, "w", encoding="utf-8") as fh:
        json.dump(keys, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
