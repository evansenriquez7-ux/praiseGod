import hashlib
import json
from pathlib import Path

import pytest

import tests.file_reviews as fr
from backend.app.practice_gen.validation.validate_judgment import (
    REQUIRED_FINDINGS,
    SAMPLE_ASSESSMENTS,
)


NODE = "mat_g1_dp_q3_0"
REVIEWER = "blind-attester-gpt-5.6-terra-light-proof-20260923"
REASON = "This reviewer-authored explanation is specific and longer than forty characters."


def _skeleton(root: Path) -> Path:
    skeleton_dir = root / "skeletons"
    skeleton_dir.mkdir(exist_ok=True)
    record = {
        "schema_version": 2,
        "node_id": NODE,
        "competency_snapshot": {"text": "Collect data.", "grade": 1, "quarter": 3,
                                "subdomain": None},
        "requirements_snapshot": [
            {"id": "collect_data", "clause": "Collect data", "kind": "verb"},
            {"id": "simple_interview", "clause": "simple interview", "kind": "context"},
        ],
        "packet_digest": "packet-digest",
        "sampling_version": "test",
        "reviewed_by": "<placeholder>",
        "review_date": "<placeholder>",
        "blind": True,
        "sample_seeds": [42, 43, 44],
        "sample_ids": ["sample-a", "sample-b", "sample-c"],
        "samples_reviewed": [
            {"sample_id": sample_id, "seed": seed, "question_text": f"Question {seed}",
             "resolved_answer": seed}
            for sample_id, seed in zip(("sample-a", "sample-b", "sample-c"), (42, 43, 44))
        ],
        "sample_assessments": [],
        "clause_evidence": [],
        "dispatch_provenance": [],
        "findings": {},
        "overall": "<placeholder>",
    }
    (skeleton_dir / f"{NODE}.json").write_text(json.dumps(record), encoding="utf-8")
    return skeleton_dir


def _reply() -> dict:
    findings = {
        name: {"verdict": "PASS", "rationale": f"{REASON} Finding: {name}."}
        for name in REQUIRED_FINDINGS
    }
    findings["competency_fulfillment"]["decomposition"] = {
        "verdict": "PASS",
        "reasoning": REASON + " The two printed requirements cover the competency.",
    }
    assessments = [{
        "sample_id": sample_id,
        "checks": {
            name: {"verdict": "PASS", "reasoning": f"{REASON} Check: {name}, {sample_id}."}
            for name in SAMPLE_ASSESSMENTS
        },
    } for sample_id in ("sample-a", "sample-b", "sample-c")]
    clauses = [{
        "requirement_id": req_id,
        "clause": clause,
        "verdict": "PASS",
        "reasoning": f"{REASON} Requirement: {req_id}.",
        "sample_ids": ["sample-a"],
    } for req_id, clause in (("collect_data", "Collect data"),
                             ("simple_interview", "simple interview"))]
    return {
        "findings": findings,
        "sample_assessments": assessments,
        "clause_evidence": clauses,
        "overall": "PASS",
    }


def _file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reply: dict) -> Path:
    judgment = tmp_path / "judgment"
    monkeypatch.setattr(fr, "JUDGMENT_DIR", judgment)
    raw = tmp_path / "reply.json"
    raw.write_text(json.dumps({"reviewer": REVIEWER, NODE: reply}), encoding="utf-8")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("exact blind dispatch prompt", encoding="utf-8")
    return fr.file_one(
        NODE, reply, REVIEWER, "2026-09-23", _skeleton(tmp_path),
        raw_response=raw, prompt_path=prompt, dispatch_prefix="judgment-v2-b1-20260923",
        samples_delivery="reviewer read only the saved prompt path",
        tool_uses_by_reviewer="read prompt; wrote one JSON reply",
    )


def test_file_one_preserves_complete_v2_judgment_and_dispatch_bytes(tmp_path, monkeypatch):
    path = _file(tmp_path, monkeypatch, _reply())
    record = json.loads(path.read_text())
    dispatch_id = f"judgment-v2-b1-20260923:{NODE}"

    assert [a["sample_id"] for a in record["sample_assessments"]] == [
        "sample-a", "sample-b", "sample-c"
    ]
    assert {a["reviewer_identity"] for a in record["sample_assessments"]} == {REVIEWER}
    assert {a["dispatch_id"] for a in record["sample_assessments"]} == {dispatch_id}
    assert [c["requirement_id"] for c in record["clause_evidence"]] == [
        "collect_data", "simple_interview"
    ]
    assert {c["reviewer_identity"] for c in record["clause_evidence"]} == {REVIEWER}
    assert record["findings"]["competency_fulfillment"]["clause_ids"] == [
        "collect_data", "simple_interview"
    ]
    provenance = record["dispatch_provenance"]
    assert provenance == [{
        **provenance[0],
        "dispatch_id": dispatch_id,
        "reviewer_identity": REVIEWER,
        "clause_ids": ["collect_data", "simple_interview"],
    }]
    response = path.parent / provenance[0]["response_ref"]
    prompt = path.parent / provenance[0]["prompt_ref"]
    assert hashlib.sha256(response.read_bytes()).hexdigest() == provenance[0]["response_digest"]
    assert hashlib.sha256(prompt.read_bytes()).hexdigest() == provenance[0]["prompt_digest"]
    assert json.loads(response.read_text())[NODE]["sample_assessments"][0]["sample_id"] == "sample-a"


def test_file_one_rejects_a_missing_sample_assessment(tmp_path, monkeypatch):
    reply = _reply()
    reply["sample_assessments"].pop()
    with pytest.raises(ValueError, match="sample_assessments must cover every dispatch-time sample"):
        _file(tmp_path, monkeypatch, reply)


def test_file_one_rejects_retyped_clause_text(tmp_path, monkeypatch):
    reply = _reply()
    reply["clause_evidence"][0]["clause"] = "Collect some data"
    with pytest.raises(ValueError, match="clause text differs from the dispatched packet"):
        _file(tmp_path, monkeypatch, reply)


def test_file_one_preflight_does_not_write_evidence(tmp_path, monkeypatch):
    judgment = tmp_path / "judgment"
    monkeypatch.setattr(fr, "JUDGMENT_DIR", judgment)
    raw = tmp_path / "reply.json"
    raw.write_text(json.dumps({"reviewer": REVIEWER, NODE: _reply()}), encoding="utf-8")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("exact blind dispatch prompt", encoding="utf-8")
    path = fr.file_one(
        NODE, _reply(), REVIEWER, "2026-09-23", _skeleton(tmp_path),
        raw_response=raw, prompt_path=prompt, dispatch_prefix="judgment-v2-b1-20260923",
        samples_delivery="reviewer read only the saved prompt path",
        tool_uses_by_reviewer="read prompt; wrote one JSON reply", write=False,
    )
    assert not path.exists()
    assert not (path.parent / ".responses").exists()


def test_preflight_does_not_mutate_reply_before_write(tmp_path, monkeypatch):
    judgment = tmp_path / "judgment"
    monkeypatch.setattr(fr, "JUDGMENT_DIR", judgment)
    reply = _reply()
    raw = tmp_path / "reply.json"
    raw.write_text(json.dumps({"reviewer": REVIEWER, NODE: reply}), encoding="utf-8")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("exact blind dispatch prompt", encoding="utf-8")
    kwargs = dict(
        raw_response=raw, prompt_path=prompt, dispatch_prefix="judgment-v2-b1-20260923",
        samples_delivery="reviewer read only the saved prompt path",
        tool_uses_by_reviewer="read prompt; wrote one JSON reply",
    )
    fr.file_one(NODE, reply, REVIEWER, "2026-09-23", _skeleton(tmp_path),
                write=False, **kwargs)
    path = fr.file_one(NODE, reply, REVIEWER, "2026-09-23", tmp_path / "skeletons",
                       **kwargs)
    assert path.exists()
    assert "reviewer_identity" not in reply["sample_assessments"][0]


def test_file_one_rejects_an_overall_its_findings_contradict(tmp_path, monkeypatch):
    """mat_g2_mg_q2_2 was filed `overall: PASS` beside a CONCERN finding; the stored
    field feeds the corpus census, so the contradiction overstated PASSes."""
    reply = _reply()
    reply["findings"]["variant_comprehensiveness"]["verdict"] = "CONCERN"
    with pytest.raises(ValueError, match="contradicts the reply's own verdicts, which give 'CONCERN'"):
        _file(tmp_path, monkeypatch, reply)


def test_file_one_accepts_an_overall_that_follows_from_its_findings(tmp_path, monkeypatch):
    reply = _reply()
    reply["clause_evidence"][1]["verdict"] = "FAIL"
    reply["overall"] = "FAIL"
    assert json.loads(_file(tmp_path, monkeypatch, reply).read_text())["overall"] == "FAIL"


def test_file_one_refuses_to_overwrite_another_replys_raw_response(tmp_path, monkeypatch):
    # review_response_copy_not_overwritten: one dispatch prefix per reply. Filing a second,
    # different reply under the same prefix used to overwrite the first record's raw
    # response, silently breaking the digest that record binds.
    first = _file(tmp_path, monkeypatch, _reply())
    provenance = json.loads(first.read_text())["dispatch_provenance"][0]
    response = first.parent / provenance["response_ref"]
    before = response.read_bytes()
    second = _reply()
    second["sample_assessments"][0]["checks"]["ambiguity"]["reasoning"] = (
        REASON + " A different reply filed under the same dispatch prefix."
    )
    with pytest.raises(ValueError, match="already holds a DIFFERENT dispatch's bytes"):
        _file(tmp_path, monkeypatch, second)
    assert response.read_bytes() == before


def test_file_one_allows_refiling_the_same_reply(tmp_path, monkeypatch):
    _file(tmp_path, monkeypatch, _reply())
    _file(tmp_path, monkeypatch, _reply())
