"""
test_attester_file.py
=====================
`tests/attester_file.py` is the only thing standing between what a blind Attester
said and what lands in `validation_reports/attestation/`. Every §6F/§6G failure it
refuses to write is one that would otherwise be discovered *after* filing — and at
that point the honest remedy is re-dispatching the Attester, because the protocol
forbids editing a filed record outright. So its refusals are gates, and a gate that
has never been shown catching its own violation is not known to work (Scaling
Mandate §1).

Each test asserts both directions: the malformed batch is refused *and* the honest
batch builds. A refuser that refuses everything is an outage, not a gate, so the
positive controls here carry as much weight as the negative ones.

The packet fixture is synthetic on purpose. These guards are about the shape of the
join between verdicts and the key — not about any node's content — so binding them
to a real render would make them slow and would couple them to content churn they
are not measuring.
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, _REPO_ROOT)

from backend.app.practice_gen.validation.validate_capability import (  # noqa: E402
    _MAX_ATTESTER_SKELETON_CLUSTER,
)
from tests.attester_file import build_records, check_skeletons  # noqa: E402

_NODE = "mat_g1_na_q1_0"
_SEEDS = [11, 23, 42]

# The fixture carries four clauses because the templated-batch test needs to *exceed*
# the cluster threshold, and three colliding verdicts are legal. Pinned rather than
# derived from the constant: a fixture sized as `threshold + 1` would quietly follow
# the threshold down, and the protocol forbids lowering it precisely so that doing so
# costs a visible diff. `test_cluster_threshold_is_three` is that diff.
_ITEMS = ("item_001", "item_002", "item_003", "item_004")

_SAMPLES = [
    {"seed": 11, "formatter": "mcq", "question_text": "What is 2 + 1?", "correct_answer": "3"},
    {"seed": 23, "formatter": "mcq", "question_text": "What is 4 + 2?", "correct_answer": "6"},
    {"seed": 42, "formatter": "cloze", "question_text": "Count: 1, 2, ___", "correct_answer": "3"},
]

# Two clauses on one node, which is also the ordinary shape: §6F reads one record per
# node, so a two-item packet exercises the per-node grouping as well as the joins.
_CLAUSES = {
    "item_001": ("Count", "count"),
    "item_002": ("using pictorial models", "pictorial"),
    "item_003": ("up to 100", "range_100"),
    "item_004": ("1 more or 1 less", "one_more_one_less"),
}
_PACKETS = [
    {"item": item, "clause": clause, "competency": "Count up to 100.",
     "grade": 1, "quarter": 1, "samples": _SAMPLES}
    for item, (clause, _cap) in _CLAUSES.items()
]
_KEY = {
    item: {"node_id": _NODE, "capability_id": cap, "registered_provider": None}
    for item, (_clause, cap) in _CLAUSES.items()
}

# Deliberately unalike, and phrased oddly enough that collision with a real filed
# record's skeleton would be a coincidence rather than a matter of time. The
# skeleton normalizer strips node IDs, quoted spans and digits, so "reasoning for
# item_001" / "item_002" would collapse to ONE skeleton and fail — which is the
# check working, and the trap this fixture exists to stay out of.
_HONEST = {
    "item_001": "Each stem names a quantity and asks the pupil to continue a spoken sequence.",
    "item_002": "No payload carries a drawn figure, so nothing pictorial reaches the page.",
    "item_003": "Nothing sampled climbs past the hundred mark; the largest total sits well under it.",
    "item_004": "Steps of one appear going up, but no stem ever asks for the value one below.",
}


def _verdicts(**overrides):
    out = []
    for item in _ITEMS:
        v = {"item": item, "verdict": "PROVIDED", "seeds_showing_it": [11],
             "reasoning": _HONEST[item]}
        v.update(overrides.get(item, {}))
        out.append(v)
    return out


def _build(verdicts, actions=None):
    return build_records(_PACKETS, _KEY, verdicts, "ZZunit", "left registered",
                         actions or {}, "2026-01-01T00:00:00Z", "0",
                         "synthetic fixture", {})


def _refuses(verdicts, needle, actions=None):
    with pytest.raises(SystemExit) as exc:
        check_skeletons(_build(verdicts, actions))
    assert needle.lower() in str(exc.value).lower(), str(exc.value)


# --- the positive control: an honest batch must file ---------------------------

def test_honest_batch_builds_one_record_per_node():
    records = _build(_verdicts())
    check_skeletons(records)
    assert list(records) == [f"ZZunit_{_NODE}"]
    rec = records[f"ZZunit_{_NODE}"]
    assert len(rec["verdicts"]) == len(_ITEMS)
    # §6F fails any batch it cannot re-render, so these two fields are load-bearing.
    assert rec["packet"]["node_id"] == _NODE
    assert [s["seed"] for s in rec["packet"]["samples_judged"]] == _SEEDS


def test_blindness_block_states_delivery_rather_than_assuming_inline():
    """`tool_uses: 0` is a claim that blindness was structural. It must not be implied."""
    rec = _build(_verdicts())[f"ZZunit_{_NODE}"]
    assert rec["blindness"]["samples_delivery"] == "synthetic fixture"
    assert rec["blindness"]["tool_uses_by_attester"] == "0"


# --- the refusals --------------------------------------------------------------

def test_verdict_for_an_item_not_in_the_packet_is_refused():
    extra = _verdicts() + [{"item": "item_999", "verdict": "PROVIDED",
                            "seeds_showing_it": [11], "reasoning": "about something else"}]
    _refuses(extra, "not in this packet")


def test_packet_item_with_no_verdict_is_refused():
    _refuses(_verdicts()[:1], "no verdict")


def test_duplicate_verdict_for_one_item_is_refused():
    _refuses(_verdicts() + _verdicts()[:1], "two verdicts")


def test_verdict_string_outside_the_two_allowed_values_is_refused():
    _refuses(_verdicts(item_001={"verdict": "MAYBE"}), "not PROVIDED/NOT_PROVIDED")


def test_empty_reasoning_is_refused():
    """§6G hard fail: a verdict without reasoning is a vote, and votes are not counted."""
    _refuses(_verdicts(item_001={"reasoning": "   "}), "empty reasoning")


def test_provided_naming_no_seed_is_refused():
    _refuses(_verdicts(item_001={"seeds_showing_it": []}), "names no seed")


def test_seed_outside_the_samples_shown_is_refused():
    """§6G seed provenance — the Attester cannot cite what it was never shown."""
    _refuses(_verdicts(item_001={"seeds_showing_it": [99999]}), "seed provenance")


def test_not_provided_without_an_action_is_refused():
    """A NOT_PROVIDED lands as a §6F CONTRADICTED finding; 'what you did' has no default."""
    _refuses(_verdicts(item_001={"verdict": "NOT_PROVIDED", "seeds_showing_it": []}),
             "no action_taken")


def test_not_provided_with_an_action_is_accepted():
    """The negative control for the one above: supplying the action must let it through."""
    records = _build(_verdicts(item_001={"verdict": "NOT_PROVIDED", "seeds_showing_it": []}),
                     actions={"item_001": "opened as a machinery item"})
    check_skeletons(records)
    v = next(v for v in records[f"ZZunit_{_NODE}"]["verdicts"] if v["capability_id"] == "count")
    assert v["verdict"] == "NOT_PROVIDED"
    assert v["action_taken"] == "opened as a machinery item"


def test_one_sentence_frame_filled_in_per_clause_is_refused():
    """
    The templated-batch shape §6G exists for: same frame, clause words swapped. The
    skeleton normalizer strips the quoted span, so both collapse to one string.
    """
    templated = _verdicts(**{
        item: {"reasoning": f'The samples exhibit what "{_CLAUSES[item][0]}" names.'}
        for item in _ITEMS
    })
    _refuses(templated, "skeleton clustering")


def test_three_shared_skeletons_are_allowed():
    """
    The negative control, and the reason the fixture carries four clauses. The
    threshold is a *maximum*, not a ban: three verdicts may legitimately land on one
    skeleton. If this test ever starts failing alongside the one above, the check has
    become an outage rather than a gate.
    """
    assert _MAX_ATTESTER_SKELETON_CLUSTER == 3
    three = _verdicts(**{
        item: {"reasoning": f'The samples exhibit what "{_CLAUSES[item][0]}" names.'}
        for item in _ITEMS[:3]
    })
    check_skeletons(_build(three))
