"""Owner ruling 22: the clause classification gate and the selector strata it feeds.

`test_tracked_classification_passes_the_gate` is the gate on the REAL file the packet
builder reads; the mutations in `tests/mutation_harness.py` plant into that file. The
synthetic tests below prove each failure direction on its own, so a gate that stopped
checking one of them cannot hide behind the real file happening to be clean.
"""

from __future__ import annotations

import copy
import hashlib

import pytest

from tests import attester_packets as ap
from tests import clause_enumeration as CE
from tests import frontend_renderer


def test_tracked_classification_passes_the_gate():
    errors = CE.check()
    assert errors == [], "\n".join(errors)


def test_tracked_classification_is_a_proof_input():
    """Mutations plant into this file; outside the digest their proofs are inadmissible."""
    from backend.app.practice_gen.validation import mutation_proof as MP

    rel = CE.PATH.relative_to(MP._REPO_ROOT).as_posix()
    assert rel in MP.input_manifest(), f"{CE.LABEL}: {rel} is not in the proof input digest"
    assert MP.paths_outside_input_set([rel]) == []


# --------------------------------------------------------------------------- synthetic

_COMPETENCY = "Count by 2s and 5s up to 100."
_NODE = "synthetic_node"


def _info(node_id):
    return {"competency": _COMPETENCY, "grade": 1, "quarter": 2, "requires": [
        {"id": "count", "clause": "Count"},
        {"id": "step_2s", "clause": "2s"},
        {"id": "step_5s", "clause": "5s"},
    ]}


def _doc():
    return CE.build_document(
        table={_NODE: [("2s and 5s", {"step_2s": CE.eq("skip_by", 2),
                                      "step_5s": CE.eq("skip_by", 5)})]},
        node_info=_info, node_ids=[_NODE])


def _errors(doc):
    return CE.validate(doc, node_info=_info, node_ids=[_NODE])


def _members(doc):
    return doc["nodes"][_NODE]["enumerations"][0]["members"]


def test_synthetic_document_is_clean():
    assert _errors(_doc()) == []


def test_node_with_requires_missing_from_the_file_fails():
    doc = _doc()
    del doc["nodes"][_NODE]
    assert any("missing from the classification" in e for e in _errors(doc))


def test_competency_hash_mismatch_fails():
    doc = _doc()
    doc["nodes"][_NODE]["competency_sha256"] = hashlib.sha256(b"old wording").hexdigest()
    assert any("competency_sha256 mismatch" in e for e in _errors(doc))


def test_wording_not_verbatim_fails():
    doc = _doc()
    doc["nodes"][_NODE]["enumerations"][0]["wording"] = "2s, and 5s"
    assert any("not verbatim" in e for e in _errors(doc))


def test_required_clause_classified_zero_times_fails():
    doc = _doc()
    doc["nodes"][_NODE]["not_enumerated"].remove("count")
    assert any("'count' is classified 0 times" in e for e in _errors(doc))


def test_required_clause_classified_twice_fails():
    doc = _doc()
    doc["nodes"][_NODE]["not_enumerated"].append("step_2s")
    assert any("'step_2s' is classified 2 times" in e for e in _errors(doc))


def test_classified_id_the_node_does_not_require_fails():
    doc = _doc()
    doc["nodes"][_NODE]["not_enumerated"].append("step_10s")
    assert any("'step_10s', which the node does not require" in e for e in _errors(doc))


def test_member_with_two_dispositions_fails():
    doc = _doc()
    _members(doc)["step_2s"]["unserved"] = "also unserved"
    assert any("needs exactly one disposition" in e for e in _errors(doc))


def test_member_with_no_disposition_fails():
    doc = _doc()
    _members(doc)["step_2s"] = {}
    assert any("needs exactly one disposition" in e for e in _errors(doc))


@pytest.mark.parametrize("kind", ["needs_instrumentation", "unserved"])
def test_empty_reason_fails(kind):
    doc = _doc()
    _members(doc)["step_2s"] = {kind: "  "}
    assert any(f"{kind} has an empty reason" in e for e in _errors(doc))


@pytest.mark.parametrize("op", ["contains", "startswith", "regex", "in_text"])
def test_condition_op_outside_the_allowed_set_fails(op):
    doc = _doc()
    _members(doc)["step_2s"] = {"observe": [{"path": "question_text", op: "2s"}]}
    assert any("no substring op" in e for e in _errors(doc))


def test_op_inside_any_of_is_checked_too():
    doc = _doc()
    _members(doc)["step_2s"] = {"observe": [{"any_of": [[{"path": "q", "contains": "2"}]]}]}
    assert any("no substring op" in e for e in _errors(doc))


def test_two_siblings_sharing_a_selector_fail():
    doc = _doc()
    _members(doc)["step_5s"] = copy.deepcopy(_members(doc)["step_2s"])
    assert any("share a selector" in e for e in _errors(doc))


def test_hand_edited_file_fails_the_builder_equality(tmp_path):
    path = tmp_path / "clause_enumeration.json"
    path.write_text(CE.PATH.read_text(encoding="utf-8").replace('"schema_version": 1',
                                                                '"schema_version":  1'),
                    encoding="utf-8")
    assert any("is not the builder's output" in e for e in CE.check(path))


def test_matcher_raises_on_an_unknown_op():
    with pytest.raises(ValueError, match=CE.LABEL):
        CE.selector_matches({"_provider_variant_evidence": {"skip_by": 2}},
                            {"observe": [{"path": "skip_by", "contains": "2"}]})


def test_matcher_reads_structured_values_and_visual_type():
    sample = {"_provider_variant_evidence": {"outer": {"skip_by": 5}}, "visual_type": "BarChart",
              "question_text": "skip_by 2"}
    assert CE.selector_matches(sample, CE.eq("skip_by", 5))
    assert not CE.selector_matches(sample, CE.eq("skip_by", 2))  # text is never read
    assert CE.selector_matches(sample, CE.eq("visual_type", "BarChart"))
    assert CE.selector_matches(sample, CE.both({"path": "skip_by", "gte": 5},
                                               {"path": "skip_by", "lt": 6}))
    assert CE.selector_matches(sample, {"observe": [{"any_of": [[{"path": "x", "equals": 1}],
                                                               [{"path": "skip_by", "equals": 5}]]}]})


# --------------------------------------------------------------------------- packet builder

def _sample(node_id, seed, difficulty_profile=None):
    return {
        "node_id": node_id, "seed": seed, "formatter": "mcq", "question_text": f"seed {seed}",
        "correct_answer": 1, "resolved_answer": 1, "visual_type": None,
        "requested": {"difficulty_profile": difficulty_profile, "student_interest": None,
                      "experience": "standard"},
        "serving_mode": "student_path",
        "effective": {"format": "mcq", "is_visual": False, "visual_type": None,
                      "interaction_mode": None, "answer_collection": None,
                      "experience": "standard"},
        "_provider_variant_evidence": {"skip_by": 2 if seed % 2 else 5,
                                       **(difficulty_profile or {})},
    }


def _build(monkeypatch, members):
    doc = CE.build_document(table={_NODE: [("2s and 5s", members)]},
                            node_info=_info, node_ids=[_NODE])
    monkeypatch.setattr(ap, "get_node_info", _info)
    monkeypatch.setattr(ap.CE, "load", lambda path=CE.PATH: doc)
    monkeypatch.setattr(ap, "_provider_variants_for",
                        lambda _n, cap: [("direction", "forward")] if cap == "count" else
                        [("skip_by", 2)])
    monkeypatch.setattr(ap, "_render", _sample)
    monkeypatch.setattr(frontend_renderer, "attach_rendered_visual_descriptions",
                        lambda samples: samples)
    return ap.build([_NODE])


def test_enumeration_member_is_stratified_by_its_selector_only(monkeypatch):
    packets, key = _build(monkeypatch, {"step_2s": CE.eq("skip_by", 2),
                                        "step_5s": CE.eq("skip_by", 5)})
    by_cap = {key[p["item"]]["capability_id"]: (p, key[p["item"]]) for p in packets}
    for cap, value in (("step_2s", 2), ("step_5s", 5)):
        packet, private = by_cap[cap]
        assert private["provider_variant_seed_map"] == []  # never the explicit variant
        (mapping,) = private["clause_selector_seed_map"]
        assert len(set(mapping["seeds"])) == 2
        samples = {s["seed"]: s for s in packet["samples"]}
        assert set(mapping["seeds"]) <= set(samples), (
            f"{CE.LABEL}: selector samples were dropped before the Attester packet")
        for seed in mapping["seeds"]:
            assert _sample(_NODE, seed)["_provider_variant_evidence"]["skip_by"] == value
            assert samples[seed]["requested"]["difficulty_profile"] is None
        assert [s["seeds"] for s in packet["provider_variant_strata"]] == [mapping["seeds"]]
    # A non-enumerated clause keeps 314a745a's explicit-variant stratification.
    assert by_cap["count"][1]["provider_variant_seed_map"][0]["variant"] == ["direction", "forward"]
    prompt = ap.render_prompt_block(packets)
    map_block = prompt.split("PROVIDER-VARIANT SEED MAP", 1)[1].split("SAMPLES:", 1)[0]
    assert "skip_by" not in map_block
    assert by_cap["step_2s"][0]["clause_standard"] == {
        "kind": "enumerated_sibling", "ruling": 19, "list": "2s and 5s"}
    assert by_cap["count"][0]["clause_standard"] == {"kind": "not_enumerated", "ruling": 9}
    assert 'STANDARD (owner ruling 19): this clause is one item of the list "2s and 5s"' in prompt
    assert "STANDARD (owner ruling 9)" in prompt


def test_needs_instrumentation_member_refuses_the_node(monkeypatch):
    with pytest.raises(RuntimeError, match=r"clause_enumeration_22: synthetic_node has "
                                           r"needs_instrumentation member\(s\) \['step_5s'\]"):
        _build(monkeypatch, {"step_2s": CE.eq("skip_by", 2), "step_5s": CE.NI("text only")})


def test_unserved_member_gets_no_stratum(monkeypatch):
    packets, key = _build(monkeypatch, {"step_2s": CE.eq("skip_by", 2),
                                        "step_5s": CE.UNSERVED("no value")})
    (packet,) = [p for p in packets if key[p["item"]]["capability_id"] == "step_5s"]
    assert packet["provider_variant_strata"] == []
    assert key[packet["item"]]["clause_selector_seed_map"] == []


def test_unmatchable_selector_fails_loudly_with_the_member(monkeypatch):
    with pytest.raises(RuntimeError, match=r"synthetic_node/step_5s could not render 2"):
        _build(monkeypatch, {"step_2s": CE.eq("skip_by", 2), "step_5s": CE.eq("skip_by", 50)})


def test_selector_seed_sequence_is_stable_and_member_specific():
    first = ap._selector_seed_candidates(_NODE, "step_2s")
    assert first == ap._selector_seed_candidates(_NODE, "step_2s")
    assert first != ap._selector_seed_candidates(_NODE, "step_5s")
    assert first != ap._selector_seed_candidates("other_node", "step_2s")
    assert min(first) >= 10_000
