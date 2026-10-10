"""
Structured slots for the ANSWER text a formatter shows (owner rulings 28 and 33; batch H3-R2).

A formatter does not author its options' words: it lays out the generator's keyed answer and
the generator's distractors. So the slot it records says exactly that -- the keyed answer is
`value:<blank_target>` (the generated value it repeats) or, when the context keys a value the
values dict does not hold, the context's own `correct_answer`; a distractor is one of the
generator's own distractor list. A formatter that prints option text it invented is then a
`slot_domain_escape_14` (§14), not a silently accounted string.

Only strings are recorded: a number in an option is not learner TEXT in §1J's classification
(`validate_language._strings_in`), and the value is returned unchanged in every case, so no
rendered byte changes.
"""
from __future__ import annotations

from typing import Any, Iterable

from backend.app.practice_gen.slots import E, S, fill


def answer_text(value: Any, ctx: Any) -> Any:
    """The keyed answer as a recorded fill (strings only; anything else is returned as is)."""
    if not isinstance(value, str):
        return value
    values = ctx.values or {}
    bt = ctx.blank_target or "result"
    if bt in values and values[bt] == value:
        domain: Any = f"value:{bt}"
    else:
        domain = E((ctx.correct_answer,), "QuestionContext.correct_answer (the keyed answer)")
    return fill("{answer}", answer=S(value, domain))


def member_text(value: Any, members: Iterable[Any], basis: str) -> Any:
    """A string drawn from the generator's own collection (`members`), as a recorded fill."""
    if not isinstance(value, str):
        return value
    return fill("{member}", member=S(value, E(tuple(members), basis)))


def distractor_text(value: Any, ctx: Any) -> Any:
    """A distractor the generator produced (`QuestionContext.distractors`), as a recorded fill."""
    return member_text(value, ctx.distractors or (), "QuestionContext.distractors (the generator's own)")


def correct_option_key(mcq_options: Any) -> str:
    """The letter of the option marked correct, recorded as one of this item's own option keys."""
    keys = tuple(o["key"] for o in mcq_options)
    key = next(o["key"] for o in mcq_options if o["is_correct"])
    return fill("{key}", key=S(key, E(keys, "the option keys this item shows")))


def distractors_field(ctx: Any) -> Any:
    """`ctx.distractors` passed through to the payload, its strings recorded (a non-list is returned as is)."""
    if not isinstance(ctx.distractors, list):
        return ctx.distractors
    return [distractor_text(d, ctx) for d in ctx.distractors]
