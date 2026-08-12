"""
test_judgment_antitemplate.py
=============================
The judgment gate's job is to make a fabricated review fail loudly. It did not.

A set of 151 all-PASS reviews was filed in which every rationale came from one
template with the node ID and seed list substituted in, and 115 of them quoted
question stems that appear nowhere in their own `samples_reviewed`. That set
satisfied every check the gate had:

  - `blind: true`                  — a self-attested boolean
  - `reviewed_by` not a placeholder — one plausible string, repeated 151x
  - rationale >= 40 chars           — templates are long
  - verbatim rationale reuse        — the node ID was substituted, so no two
                                      rationales were byte-identical
  - freshness (re-render each seed) — `samples_reviewed` WAS freshly rendered;
                                      a template rationale was stapled to it.
                                      Freshness validates the samples block, and
                                      never reads the rationale at all.

Three structural checks close that hole. This file is their enforcement: each
test asserts both directions — the fabricated shape FAILS *and* the genuine
shape PASSES. A check that fails everything is not a gate, it is an outage, so
the negative controls here are as load-bearing as the positive ones.
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)

from backend.app.practice_gen.validation.validate_judgment import (  # noqa: E402
    _MAX_NODES_PER_REVIEWER,
    _MAX_SKELETON_CLUSTER,
    _rationale_skeleton,
    _validate_quote_provenance,
    _validate_reviewer_plurality,
    _validate_skeleton_clusters,
)

# A node whose competency text is real, so the provenance corpus is the real one.
_NODE = "mat_g1_na_q1_0"

_SAMPLES = [
    {"seed": 42, "formatter": "mcq", "question_text": "What is 2 + 1?", "correct_answer": "3"},
    {"seed": 43, "formatter": "cloze", "question_text": "Count the stars: 1, 2, ___", "correct_answer": "3"},
    {"seed": 44, "formatter": "mcq", "question_text": "How many apples are there?", "correct_answer": "5"},
]


def _review(rationale):
    return {
        "node_id": _NODE,
        "samples_reviewed": _SAMPLES,
        "findings": {"competency_fulfillment": {"verdict": "PASS", "rationale": rationale}},
    }


# --- Check 1: quote provenance ------------------------------------------------

def test_quote_present_in_own_samples_passes():
    """A reviewer quoting a stem it was actually shown is the genuine shape."""
    r = _review(
        "Across the sampled items the target skill is exercised directly; for instance "
        "'What is 2 + 1?' requires the student to add two single-digit addends."
    )
    assert _validate_quote_provenance(_NODE, r) == []


def test_quote_absent_from_own_samples_fails():
    """The exact fabrication mechanism: a stem quoted that the packet never contained."""
    r = _review(
        "Across the sampled items the target skill is exercised directly; for instance "
        "'Write 33 in words.' requires the student to render a numeral as a word."
    )
    errs = _validate_quote_provenance(_NODE, r)
    assert len(errs) == 1
    assert "Write 33 in words." in errs[0]
    assert _NODE in errs[0]


def test_competency_text_may_be_quoted():
    """Quoting the node's own MATATAG competency is legitimate, not fabrication."""
    from backend.app.practice_gen.registry import get_node_info

    competency = str(get_node_info(_NODE).get("competency", "")).strip().rstrip(".")
    assert competency, f"{_NODE} has no competency text; the corpus check would be vacuous"
    r = _review(f"The sampled problems fulfill the competency '{competency}' as written, with no drift.")
    assert _validate_quote_provenance(_NODE, r) == []


def test_intraword_apostrophe_is_not_a_quote():
    """"student's" must not be parsed as an opening quote — that would fail genuine prose."""
    r = _review(
        "The stems sit inside the student's demonstrated range for this quarter and do not "
        "reach for vocabulary introduced later in the sequence."
    )
    assert _validate_quote_provenance(_NODE, r) == []


# --- Check 2: skeleton clustering --------------------------------------------

def test_template_collapses_to_one_skeleton():
    """Same frame, different node/seeds/quotes -> identical skeleton. This is the tell."""
    a = _rationale_skeleton(
        "For node mat_g1_na_q1_0 (Grade 1 Quarter 1 curriculum), the sampled problems directly "
        "fulfill the MATATAG competency 'Count objects up to 100.'. Across seeds 42, 43, 44."
    )
    b = _rationale_skeleton(
        "For node mat_g3_mg_q2_1 (Grade 3 Quarter 2 curriculum), the sampled problems directly "
        "fulfill the MATATAG competency 'Measure length in centimetres.'. Across seeds 51, 52, 53."
    )
    assert a == b


def test_independent_rationales_have_distinct_skeletons():
    """Two reviewers describing different content must not collapse together."""
    a = _rationale_skeleton(
        "Every item asks the student to combine two quantities, which is the addition "
        "competency verbatim; nothing in the set reaches past sums of 10."
    )
    b = _rationale_skeleton(
        "The items alternate between reading a picture graph and tallying a column, so the "
        "data-handling competency is covered from both directions."
    )
    assert a != b


def test_cluster_over_threshold_fails_and_at_threshold_passes():
    key = ("competency_fulfillment", "the sampled problems fulfil <QUOTED> for node <NODE>")
    at_limit = {key: [f"mat_g1_na_q1_{i}" for i in range(_MAX_SKELETON_CLUSTER)]}
    assert _validate_skeleton_clusters(at_limit) == []

    over_limit = {key: [f"mat_g1_na_q1_{i}" for i in range(_MAX_SKELETON_CLUSTER + 1)]}
    errs = _validate_skeleton_clusters(over_limit)
    assert len(errs) == 1
    assert "template rationale" in errs[0]
    assert str(_MAX_SKELETON_CLUSTER + 1) in errs[0]


# --- Check 3: reviewer plurality ---------------------------------------------

def test_one_batch_per_reviewer_passes():
    reviewers = {"agent-A batch 1": [f"n{i}" for i in range(_MAX_NODES_PER_REVIEWER)]}
    assert _validate_reviewer_plurality(reviewers) == []


def test_one_reviewer_over_a_batch_fails():
    reviewers = {"agent-A": [f"n{i}" for i in range(_MAX_NODES_PER_REVIEWER + 1)]}
    errs = _validate_reviewer_plurality(reviewers)
    assert len(errs) == 1
    assert "reviewer plurality" in errs[0]


def test_many_reviewers_each_within_a_batch_passes():
    reviewers = {f"agent-{b}": [f"n{b}_{i}" for i in range(20)] for b in range(8)}
    assert _validate_reviewer_plurality(reviewers) == []


# --- The content checks must not skip non-PASS reviews -------------------------

def test_concern_review_still_gets_content_checks(tmp_path, monkeypatch):
    """
    A CONCERN or FAIL verdict must not exempt a review from the content checks.

    `validate_judgment_reviews` used to `continue` whenever `_validate_one`
    returned any error -- and a non-PASS verdict always returns one, because the
    verdict itself is reported as an error. So freshness, quote provenance,
    skeleton clustering and reviewer plurality ran only over all-PASS reviews,
    exempting every CONCERN/FAIL review from all four. Those are precisely the
    reviews a generator fix is most likely to invalidate: when this was found,
    mat_g1_na_q1_7 (CONCERN) had a stale sample on disk while the full gate
    reported zero.
    """
    import json as _json

    import backend.app.practice_gen.validation.validate_judgment as VJ

    node = "mat_g1_na_q1_0"
    group = tmp_path / "mat_g1_na_q1"
    group.mkdir(parents=True)
    phantom = "Write 33 in words."
    review = {
        "node_id": node,
        "reviewed_by": "unit-test reviewer",
        "review_date": "2026-08-12",
        "blind": True,
        "sample_seeds": [42, 43, 44],
        "samples_reviewed": [
            {"seed": s, "formatter": "mcq", "question_text": f"placeholder stem {s}", "correct_answer": "1"}
            for s in (42, 43, 44)
        ],
        "findings": {
            item: {
                "verdict": "CONCERN",
                "rationale": (
                    f"The sampled items quote '{phantom}' which does not appear in this "
                    f"node's own packet anywhere, so the evidence is unsourced."
                ),
            }
            for item in VJ.REQUIRED_FINDINGS
        },
        "overall": "CONCERN",
    }
    (group / f"{node}.json").write_text(_json.dumps(review), encoding="utf-8")

    monkeypatch.setattr(VJ, "JUDGMENT_DIR", tmp_path)
    monkeypatch.setattr(VJ, "get_all_node_ids", lambda *a, **k: [node])

    errs = VJ.validate_judgment_reviews()

    # The quote the rationale invents is caught even though the verdict is CONCERN.
    assert any(phantom in e for e in errs), errs
    # And the non-PASS verdict is still reported -- this fix must not weaken the
    # rule that run_all cannot pass while a CONCERN or FAIL review exists.
    assert any("must be 'PASS'" in e for e in errs), errs
