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
    extra: Dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


_TRACE: ContextVar[Optional[List[Fill]]] = ContextVar("slot_trace", default=None)


@contextmanager
def capture() -> Iterator[List[Fill]]:
    """Record every `fill` made inside the block into the yielded list."""
    fills: List[Fill] = []
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


def fill(template: str, /, **slots: Any) -> str:
    """
    `template.format(**values)`, recorded with its slots when the harness is capturing.

    Each keyword is a slot. Pass `S(value, domain_id)`; a bare value is formatted the same
    way but recorded with NO domain, which the domain check reports by name.
    """
    values = {name: (v.value if isinstance(v, S) else v) for name, v in slots.items()}
    text = template.format(**values)
    trace = _TRACE.get()
    if trace is not None:
        trace.append(Fill(
            template=template,
            slots=tuple((name, values[name], v.domain if isinstance(v, S) else None)
                        for name, v in slots.items()),
            text=text,
            site=_site(2),
            sources=tuple((name, _provenance(v)) for name, v in slots.items()),
        ))
    return text


def record(template: str, text: str, slots: Dict[str, Any], renderer: str,
           renderer_ref: Optional[str] = None) -> str:
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
            sources=tuple((name, _provenance(v)) for name, v in slots.items()),
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


TRANSFORMS = {
    "strip_trailing_period": strip_trailing_period,
    "capitalize": capitalize,
}


def transform(name: str, text: str) -> str:
    """Apply a registered transformation to a recorded fill's text, recording the result."""
    out = TRANSFORMS[name](text)
    trace = _TRACE.get()
    if trace is not None:
        trace.append(Fill(template="{text}", slots=(("text", text, "fill"),), text=out,
                          site=_site(2), renderer=name))
    return out
