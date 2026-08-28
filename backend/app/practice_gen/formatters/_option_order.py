"""
Where the correct option sits must not be predictable.

Why this exists
---------------
Measured 2026-08-28 across 46 MCQ nodes, one seed at a time:

    seed 11 -> correct option in slot 1 on 93% of nodes
    seed 64 -> correct option in slot 3 on 86% of nodes
    seed 42 -> slot 2 on 58%

A pupil working a practice set at a given seed scores ~90% by always picking the same
position, having done no mathematics. That invalidates the assessment, not merely the item.

The cause is not a missing shuffle -- every formatter calls `rng.shuffle`. It is that `rng`
is `random.Random(seed)` and, by the time the shuffle happens, has consumed a similar
number of draws on every node, so the same seed lands the correct option in the same slot
tree-wide. The shuffle is random *within* a node and correlated *across* nodes, which is
exactly the axis a pupil experiences when working through a set.

The fix is to draw the ordering from a stream keyed by (node_id, seed) rather than from
the shared per-problem stream. `hash()` is not usable: PYTHONHASHSEED randomises it per
process, and this pipeline's determinism rule (CLAUDE.md #6) requires the same seed to
give the same problem in every interpreter. blake2b is stable across processes.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any, List, Optional


def option_rng(node_id: Optional[str], seed: Optional[int], salt: str = "options") -> random.Random:
    """A shuffle stream unique to this (node, seed), stable across processes."""
    key = f"{node_id or ''}|{seed if seed is not None else ''}|{salt}".encode("utf-8")
    digest = hashlib.blake2b(key, digest_size=8).digest()
    return random.Random(int.from_bytes(digest, "big"))


def shuffle_options(items: List[Any], node_id: Optional[str], seed: Optional[int],
                    salt: str = "options") -> List[Any]:
    """
    Shuffle in place using a (node, seed)-keyed stream, and return the list.

    Callers keep assigning keys A/B/C/D by position afterwards and deriving the answer
    from the shuffled list, so the letter stays consistent with wherever the correct
    option landed -- no change to what `correct_answer` holds.
    """
    option_rng(node_id, seed, salt).shuffle(items)
    return items
