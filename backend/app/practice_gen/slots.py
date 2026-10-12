"""
Structured slots for learner-facing text (owner rulings 24, 28, 33, 34; batch H3).

Every learner-read string a DNA, spine or formatter builds from a template is built with
`fill`, which returns EXACTLY the string the f-string it replaced returned, and -- only when
the harness is listening -- records what produced it: the template, each slot's name, value
and DOMAIN ID, and the file:line of the call. The record is the generator's own statement
of its template and slots. It is never reconstructed from the learner-facing text
(ruling 28; that would be ruling 22a's error one level down).

    question_text = fill(
        "Look at the array. It shows {rows} groups of {cols} ({sum}). How many in all?",
        rows=S(rows, "num.lc_bound:rows"), cols=S(cols, "num.lc_bound:cols"),
        sum=S(_repeated_sum(rows, cols), "text.derived"),
    )

Rules a call site follows:
  * The template is the f-string's literal text with each `{expression}` replaced by a
    named slot. `template.format(**values)` must equal the f-string byte for byte; the
    render snapshot (`tests/render_snapshot.py`) proves it per change.
  * Every slot names a domain id registered in `backend.app.practice_gen.validation.
    slot_domains.DOMAINS`. A slot with no domain (a bare value instead of `S(...)`) or an
    unregistered id is a finding, never a default.
  * A slot whose value is itself learner text built elsewhere (a formatter wrapping the
    DNA's stem) uses the domain `"fill"`: its value must be the text of another recorded
    fill, which is how nested templates are accounted for.
  * A string transformed after it is built (`.replace`, a regex, `Spine.render`'s
    inflection) is recorded with `renderer=` naming the ONE function the check replays to
    reproduce it, so the check asks the generator's own rule instead of a second copy.

Outside `capture()` the only cost is one ContextVar read per call: nothing is recorded,
nothing is attached to the payload, no rendered byte changes.

NAMED LIMITS (Scaling Mandate 6):
  * Coverage is by call site. Text built without `fill` is invisible here; the domain
    check reports it as un-instrumented (a content finding, ruling 34) by field, lc and
    seed, so the rollout is countable, but it cannot name the un-instrumented SITE.
  * A recorded fill proves its text came from its template and slots. It does not prove
    the template was the one a judge approved (H4's freshness does that).
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Tuple


@dataclass(frozen=True)
class R:
    """
    A RUNTIME numeric domain: the closed range a generator draws a slot from, computed
    from the same bound variables it draws with (never restated). `basis` says where the
    range comes from, for the judge who approves it (H4) and the reader of a finding.
    """
    lo: Any
    hi: Any
    basis: str


@dataclass(frozen=True)
class E:
    """
    A RUNTIME enumeration: the exact choices a generator picked a slot from, taken from its
    own object (a VocabGated's preferred/fallback pair, say). `basis` names that object.
    """
    members: Tuple[Any, ...]
    basis: str


@dataclass(frozen=True)
class S:
    """
    One slot value and its domain: a registry id (str), a runtime range (`R`) or enumeration (`E`).

    `src` is the slot's PROVENANCE (batch H5, owner ruling 35): the keys of the generator's
    own `values` this slot is derived from, stated by the generator -- a sequence string
    built from `start` and `skip_by` names both. A `value:<key>` domain implies `src=(key,)`.
    §15 reads it to decide whether a structured value a clause selector chose is exhibited
    by what the learner reads; it never infers provenance from text.
    """
    value: Any
    domain: Any
    src: Tuple[str, ...] = ()
    why: Optional[str] = None      # a DERIVED_REASONS kind, type-only domains only (ruling 42)


# ─── Why a type-only slot cannot be tightened (owner rulings 42-43; batch H4-0) ───────
# Ruling 42: before H4 approves an lc, every `num.derived`/`text.derived` slot it reaches is
# tightened to `value:`/`E`/`R`/`enum:`/`bank:`/`fill`, or carries a NAMED per-slot reason it
# cannot be. Ruling 43 (owner, 2026-10-12) fixes the form: the reason is a kind registered
# HERE, and the slot must also name its `src` -- the generator `values` keys it is computed
# from, each present in the values of that render -- so the judge who reviews the reason (H4)
# can bound the slot by the domains of what it came from. §14 counts every type-only slot
# without a valid reason as `slot_domain_type_only_14`. A kind is added here, with its
# meaning, never as a harness-side exemption of a named slot (Scaling Mandate 4).
DERIVED_REASONS: Dict[str, str] = {
    "arithmetic": (
        "a number the generator computes from the generated values named in src (a half, a "
        "sum, a difference, a running total, a place's digit). Its range is the image of those "
        "values' own domains; whether the arithmetic is RIGHT is the hint contract's (§16) and "
        "§1E's to check, not §14's."),
}


def derived(value: Any, src: Tuple[str, ...] = (), why: Optional[str] = None) -> S:
    """
    A slot COMPUTED from other values, typed by what it is: "num.derived" for a number,
    "text.derived" otherwise (batch H3-R2). Both are type-only domains (§14 limits 4 and 8):
    use a stricter domain -- `value:<key>`, `E`, `R`, `enum:`, `fill` -- wherever the
    generator has one. A non-string object printed into text (a list, None, a bool) is then
    a `slot_domain_escape_14`, which is what it is: code-shaped text a learner reads.

    `why` (owner rulings 42-43) names the `DERIVED_REASONS` kind that says why no stricter
    domain exists; it is valid only with a non-empty `src`. Without one the slot is counted
    by `slot_domain_type_only_14`.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return S(value, "num.derived", src, why)
    return S(value, "text.derived", src, why)


BANK_FIELDS = ("question", "question_text", "answer", "distractors", "statement", "template")


def bank_fields(item: Dict[str, Any], bank: str, fields: Tuple[str, ...] = BANK_FIELDS) -> Dict[str, Any]:
    """
    A copy of an item drawn from a static bank (a module-level list of dicts), with its
    learner-text fields recorded as fills whose domain is the bank itself:
    `bank:<bank>:<field>` (batch H3-R2). A string field becomes one fill; a list of strings
    (`distractors`) becomes one fill per member. Values are unchanged.
    """
    out = dict(item)
    # Provenance (owner rulings 35 and 41): a bank row's text was drawn together with the
    # row's other fields, so each field derives from the whole row's keys.
    row = tuple(item.keys())
    for name in fields:
        if name not in out:
            continue
        value, domain = out[name], f"bank:{bank}:{name}"
        if isinstance(value, str):
            out[name] = fill("{%s}" % name, **{name: S(value, domain, src=row)})
        elif isinstance(value, list):
            out[name] = [fill("{%s}" % name, **{name: S(v, domain, src=row)}) if isinstance(v, str) else v
                         for v in value]
    return out


def _reasons(slots: Dict[str, Any]) -> Tuple[Tuple[str, str], ...]:
    """(slot name, `why`) for every slot that carries a reason (owner rulings 42-43)."""
    return tuple((name, v.why) for name, v in slots.items() if isinstance(v, S) and v.why is not None)


def _provenance(v: Any) -> Tuple[str, ...]:
    """The `values` keys a slot is derived from: its declared `src`, plus a `value:` key."""
    if not isinstance(v, S):
        return ()
    keys = tuple(v.src)
    if isinstance(v.domain, str) and v.domain.startswith("value:"):
        keys += (v.domain[len("value:"):],)
    return keys


@dataclass(frozen=True)
class Fill:
    """One recorded template fill: what a generator built, and from what."""
    template: str
    slots: Tuple[Tuple[str, Any, Any], ...]   # (name, value, domain id | R | None)
    text: str
    site: str                                           # "path/to/module.py:LINE"
    renderer: Optional[str] = None                      # replayed by the check if set
    renderer_ref: Optional[str] = None                  # e.g. the spine id Spine.render used
    sources: Tuple[Tuple[str, Tuple[str, ...]], ...] = ()   # (slot name, provenance keys)
    reasons: Tuple[Tuple[str, str], ...] = ()               # (slot name, DERIVED_REASONS kind)
    extra: Dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


@dataclass(frozen=True)
class Derivation:
    """
    Value-level provenance (owner ruling 41). kind "derives": `values[key]` was CHOSEN because
    of `values[src]` (showing key exhibits src). kind "computes": `values[key]` is a FUNCTION of
    `values[src]` (showing every src exhibits key).
    """
    key: str
    src: Tuple[str, ...]
    site: str
    kind: str = "derives"


class Trace(list):
    """The fills recorded inside `capture()` (a list, as before), plus `derivations`."""

    def __init__(self) -> None:
        super().__init__()
        self.derivations: List[Derivation] = []


_TRACE: ContextVar[Optional[Trace]] = ContextVar("slot_trace", default=None)


def derives(key: str, src: Tuple[str, ...]) -> None:
    """
    Declare that the generated value `values[key]` derives from `values[k]` for k in `src`
    (owner ruling 41, batch H3-R2): a DNA that sets `a = 0` because `task_type ==
    "zero_identity"` declares `derives("a", src=("task_type",))`. §15 closes over these, so
    an item that SHOWS `a` exhibits the selector that chose it. Recorded only under
    `capture()`; nothing is returned or attached to the payload.
    """
    trace = _TRACE.get()
    if trace is not None:
        trace.derivations.append(Derivation(key=key, src=tuple(src), site=_site(2)))


def computes(key: str, src: Tuple[str, ...]) -> None:
    """
    Declare that the generated value `values[key]` is a FUNCTION of `values[k]` for k in
    `src` (owner ruling 41): division's `remainder = a % b`. An item that shows every `src`
    therefore exhibits `key`. Recorded only under `capture()`.
    """
    trace = _TRACE.get()
    if trace is not None:
        trace.derivations.append(Derivation(key=key, src=tuple(src), site=_site(2), kind="computes"))


@contextmanager
def capture() -> Iterator[Trace]:
    """Record every `fill` (and every `derives` declaration) made inside the block."""
    fills = Trace()
    token = _TRACE.set(fills)
    try:
        yield fills
    finally:
        _TRACE.reset(token)


def _site(depth: int) -> str:
    """file:line of the caller `depth` frames up (cheap: no source read, unlike inspect.stack)."""
    frame = sys._getframe(depth)
    path = frame.f_code.co_filename
    marker = "backend/app/practice_gen/"
    if marker in path:
        path = path[path.index(marker):]
    return f"{path}:{frame.f_lineno}"


def fill(template: str, /, _src: Tuple[str, ...] = (), **slots: Any) -> str:
    """
    `template.format(**values)`, recorded with its slots when the harness is capturing.

    Each keyword is a slot. Pass `S(value, domain_id)`; a bare value is formatted the same
    way but recorded with NO domain, which the domain check reports by name.

    `_src` is TEMPLATE-level provenance (batch H3-R2, owner ruling 35): the `values` keys
    whose value CHOSE this template -- a stem written under `if task_type ==
    "zero_identity":` derives from `task_type` even though no slot prints it. It is the
    generator's own claim, recorded as the source entry "__template__" (§15 reads it like
    any slot's provenance; H4's judges review it).
    """
    values = {name: (v.value if isinstance(v, S) else v) for name, v in slots.items()}
    text = template.format(**values)
    trace = _TRACE.get()
    if trace is not None:
        sources = tuple((name, _provenance(v)) for name, v in slots.items())
        if _src:
            sources += (("__template__", tuple(_src)),)
        trace.append(Fill(
            template=template,
            slots=tuple((name, values[name], v.domain if isinstance(v, S) else None)
                        for name, v in slots.items()),
            text=text,
            site=_site(2),
            sources=sources,
            reasons=_reasons(slots),
        ))
    return text


def record(template: str, text: str, slots: Dict[str, Any], renderer: str,
           renderer_ref: Optional[str] = None, _src: Tuple[str, ...] = ()) -> str:
    """
    Record text a generator produced by a TRANSFORMATION the check must replay.

    For output that is not `template.format(...)` -- `Spine.render`'s inflection, a
    `.replace("___", ...)` -- the producer records the template, its slots and the name of
    the one function that reproduces the text from them (`renderer`). Returns `text`.
    """
    trace = _TRACE.get()
    if trace is not None:
        trace.append(Fill(
            template=template,
            slots=tuple((name, (v.value if isinstance(v, S) else v),
                         v.domain if isinstance(v, S) else None) for name, v in slots.items()),
            text=text,
            site=_site(2),
            renderer=renderer,
            renderer_ref=renderer_ref,
            sources=tuple((name, _provenance(v)) for name, v in slots.items())
            + ((("__template__", tuple(_src)),) if _src else ()),
            reasons=_reasons(slots),
        ))
    return text


# ─── Transformations (one copy each) ─────────────────────────────────────────
# A generator that changes text after building it calls the function here and records the
# call with `record(..., renderer=<name>)`; the slot check replays the SAME function by name.
# Adding a transformation means adding it here, so there is never a harness-side copy.

def strip_trailing_period(text: str) -> str:
    """`text.rstrip('.')`: fmt_true_false strips a statement's own period before ". True or False?"."""
    return text.rstrip(".")


def capitalize(text: str) -> str:
    """`text.capitalize()`: a gated term opening a sentence ("The difference of ...")."""
    return text.capitalize()


def fill_blank(text: str, value: Any) -> str:
    """
    `text.replace("___", str(value))`: a formatter writing a claimed answer into the blank
    of a stem another layer built (fmt_true_false's statement from subtraction's
    "If 7 + 5 = 12, then 12 − 5 = ___." stem; batch H3-R1).
    """
    return text.replace("___", str(value))


def strip_model_gloss(text: str) -> str:
    """fmt_geometry_figure's own `_strip_model_gloss`, called by name (one copy; H3-R2)."""
    from backend.app.practice_gen.formatters.visual.fmt_geometry_figure import _strip_model_gloss
    return _strip_model_gloss(text)


TRANSFORMS = {
    "strip_trailing_period": strip_trailing_period,
    "capitalize": capitalize,
    "fill_blank": fill_blank,
    "strip_model_gloss": strip_model_gloss,
}


# ─── Renderers (one copy each) ───────────────────────────────────────────────
# Text a generator produces from a TEMPLATE by more than `str.format` (a spine's article
# choice and its agreement after "1") is recorded with `record(..., renderer=<name>)`. The
# check replays it as `RENDERERS[name](template, **slots)`, importing the generator's own
# function by its dotted path, so there is never a harness-side copy (batch H3-R2).
RENDERERS = {
    "spine": "backend.app.practice_gen.dna.base.render_spine_text",
}


def renderer(name: str):
    """The generator function a recorded renderer name refers to."""
    import importlib
    module_path, _, attr = RENDERERS[name].rpartition(".")
    return getattr(importlib.import_module(module_path), attr)


def transform(name: str, text: str, /, **args: Any) -> str:
    """
    Apply a registered transformation to a recorded fill's text, recording the result.

    `text` is recorded as a `"fill"` slot (it must be another recorded fill's text). Any
    further argument the transformation takes is passed by keyword as a slot -- pass
    `S(value, domain)` so it is recorded with its domain -- and the check replays the
    transformation with every recorded slot as a keyword (batch H3-R1).
    """
    extra = {k: (v.value if isinstance(v, S) else v) for k, v in args.items()}
    out = TRANSFORMS[name](text, **extra)
    trace = _TRACE.get()
    if trace is not None:
        trace.append(Fill(template="{text}",
                          slots=(("text", text, "fill"),) + tuple(
                              (k, extra[k], v.domain if isinstance(v, S) else None)
                              for k, v in args.items()),
                          text=out, site=_site(2), renderer=name,
                          sources=tuple((k, _provenance(v)) for k, v in args.items()),
                          reasons=_reasons(args)))
    return out
