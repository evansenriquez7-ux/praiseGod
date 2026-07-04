"""
test_emoji_formatter_range_gate.py
==================================
Emoji-based formatters are for younger students practicing counting and basic
addition — numbers/sums < 100 only. A formatter that renders quantities as
literal emoji cannot display values > 100 (FORMATTER_NUMERIC_LIMITS:
emoji_pictorial max_val=100).

The bug this guards against: emoji_pictorial was attached to the `addition` DNA
globally, so it was offered on grade-3 nodes whose sums reach 9999 — where it
could only ever raise. The fix gates a formatter off a node when the node's
number range exceeds the formatter's display ceiling, in BOTH the lab-config
builder and the auditor's supported-formatters list (kept in sync so the
Formatter-mismatch check does not fire).
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)


def _formatters(node_id):
    from backend.app.routes.matatag_router import get_matatag_lab_config
    return [f["name"] for f in get_matatag_lab_config(node_id)["formatters"]]


def test_emoji_offered_on_grade1_small_range():
    # range <= 100 -> emoji is valid
    assert "emoji_pictorial" in _formatters("mat_g1_na_q1_0")


def test_emoji_dropped_on_grade3_large_range():
    # sums reach 9999 -> emoji cannot render -> must not be offered
    assert "emoji_pictorial" not in _formatters("mat_g3_na_q2_1")


def test_emoji_dropped_when_range_just_over_100():
    # max_sum upper bound 110 (> 100) -> emoji dropped
    assert "emoji_pictorial" not in _formatters("mat_g2_na_q1_7")


def test_lab_config_and_auditor_agree_on_formatters():
    """The auditor's range-filtered supported_formatters must equal the lab
    config's, or the Formatter-mismatch check fires. Compare the two lists
    directly (cheap) rather than running the full audit."""
    import itertools
    from backend.app.practice_gen.registry import (
        get_node_dnas, get_node_competency_bounds,
    )
    from backend.app.practice_gen.compatibility import (
        get_formatters_for_dna, FORMATTER_NUMERIC_LIMITS,
    )

    node_id = "mat_g3_na_q2_1"
    dnas = get_node_dnas(node_id)
    cb = get_node_competency_bounds(node_id)
    node_max = max(
        (b[1] for b in cb.values() if isinstance(b, tuple) and len(b) == 2),
        default=0,
    )
    supported = sorted({
        fmt for fmt in itertools.chain.from_iterable(
            get_formatters_for_dna(d) for d in dnas)
        if FORMATTER_NUMERIC_LIMITS.get(fmt, {}).get("max_val", float("inf")) >= node_max
    })

    lab_fmts = set(_formatters(node_id))
    assert set(supported) == lab_fmts, (
        f"auditor supported={supported} vs lab config={sorted(lab_fmts)}"
    )
    assert "emoji_pictorial" not in supported
