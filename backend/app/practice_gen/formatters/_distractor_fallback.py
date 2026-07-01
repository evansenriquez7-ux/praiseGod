"""
_distractor_fallback.py — Distractor Augmentation Helper

Per AGENTS.md rule #4: "Avoid Graceful Fallbacks and Silent Defaulting
Behavior: Do not use." This module augments a distractor pool with
semantically valid alternatives that share the *type* of the correct
answer. It is invoked by the 15 formatters *before* their fail-fast
``len(distractor_list) < 3`` raise check, so the raise is preserved
(an actual bug still surfaces) but in normal use the candidate pool is
large enough that the raise is never reached.

The helper is intentionally simple: it produces numerically-nearby
integers (and for strings, parametric variants) that are guaranteed
distinct from ``correct`` and from any existing member of
``distractor_set``. It does *not* invent pedagogical traps or guess
domain semantics — that is the formatter's job. It only fills the pool
when a formatter's own trap builder produced fewer than ``target``
candidates.
"""

from __future__ import annotations

from typing import Any, Iterable, Set


def augment_distractors(
    distractor_set: Iterable[Any],
    correct: Any,
    target: int = 3,
    max_delta: int = 5,
) -> list:
    """
    Return a list of distractors padded to at least ``target`` items.

    Parameters
    ----------
    distractor_set:
        Any iterable of existing distractor candidates (a set, list, or
        tuple). Order is *not* preserved — the returned list is a new
        list.
    correct:
        The correct answer. Distractors must be distinct from this
        value.
    target:
        Minimum number of distractors to return. The function returns
        ``max(len(distractor_set), target)`` items when possible, capped
        at the maximum number of valid candidates it can produce.
    max_delta:
        For numeric ``correct``, the largest absolute delta searched
        from ``correct`` to find unused integers. The search walks
        outward in a symmetric pattern: ``±1, ±2, … ±max_delta``. For
        non-numeric ``correct``, up to ``max_delta`` parametric string
        variants are produced.

    Returns
    -------
    list
        A new list containing the original distractors (deduplicated
        and excluding the correct answer) followed by augmented
        candidates until the list length reaches ``target`` or the
        candidate space is exhausted. The list may be shorter than
        ``target`` if the search space is exhausted; in that case the
        caller's fail-fast raise check will fire.
    """
    if target < 0:
        raise ValueError(f"target must be non-negative, got {target}")
    if max_delta < 0:
        raise ValueError(f"max_delta must be non-negative, got {max_delta}")

    seen: Set[Any] = set()
    result: list = []

    def _add(value: Any) -> bool:
        if value in seen or value == correct:
            return False
        seen.add(value)
        result.append(value)
        return True

    for d in distractor_set:
        if d == correct:
            continue
        if d in seen:
            continue
        seen.add(d)
        result.append(d)

    if len(result) >= target:
        return result[:target]

    if isinstance(correct, bool):
        _add(not correct)
    elif isinstance(correct, (int, float)):
        for delta in range(1, max_delta + 1):
            for sign in (1, -1):
                if len(result) >= target:
                    return result[:target]
                candidate = correct + (delta * sign)
                if isinstance(correct, int) and not isinstance(candidate, int):
                    candidate = int(candidate)
                _add(candidate)
    else:
        for i in range(1, max_delta + 1):
            if len(result) >= target:
                return result[:target]
            candidate = f"{correct}_{i}"
            _add(candidate)

    return result
