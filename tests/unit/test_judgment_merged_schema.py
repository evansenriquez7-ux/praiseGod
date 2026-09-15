"""Negative controls for the versioned, lossless Phase-2 judgment record."""
from __future__ import annotations

import copy
import hashlib
import json
import pytest

from backend.app.practice_gen.registry import get_node_info
from backend.app.practice_gen.validation import validate_judgment as vj


NODE = "mat_g1_na_q1_0"
REASON = (
    "The delivered learner-visible sample supplies concrete evidence for this judgment "
    "without relying on generator source or provider claims."
)


def _record(tmp_path, monkeypatch):
    monkeypatch.setattr(vj, "JUDGMENT_DIR", tmp_path)
    info = get_node_info(NODE)
    sample = {
        "node_id": NODE,
        "seed": 42,
        "formatter": "mcq",
        "question_text": "Which number comes next after 4?",
        "correct_answer": "A",
        "resolved_answer": 5,
        "options": [
            {"key": "A", "value": 5, "is_correct": True},
            {"key": "B", "value": 6, "is_correct": False},
        ],
        "requested": {
            "difficulty_profile": None,
            "student_interest": None,
            "experience": "standard",
        },
        "serving_mode": "student_path",
        "effective": {
            "format": "mcq",
            "is_visual": False,
            "visual_type": None,
            "interaction_mode": None,
            "answer_collection": "mcq",
            "experience": "standard",
        },
        "sample_id": "sample-one",
    }
    sample["replay_digest"] = vj._json_digest(sample)
    requirements = [dict(req) for req in info["requires"]]
    clause_ids = [str(req["id"]) for req in requirements]
    competency = {
        "text": info["competency"],
        "grade": info["grade"],
        "quarter": info["quarter"],
        "subdomain": info.get("subdomain") or info.get("domain"),
    }
    core = {
        "schema_version": vj.REVIEW_SCHEMA_VERSION,
        "sampling_version": "unit-sampling-v1",
        "node_id": NODE,
        "competency_snapshot": competency,
        "requirements_snapshot": requirements,
        "sample_ids": [sample["sample_id"]],
        "samples": [sample],
    }
    packet_digest = vj._json_digest(core)
    dispatch_id = "dispatch-alpha"
    reviewer = "merged-reviewer-alpha"
    findings = {
        item: {"verdict": "PASS", "rationale": REASON}
        for item in vj.REQUIRED_FINDINGS
    }
    findings["competency_fulfillment"].update({
        "clause_ids": clause_ids,
        "decomposition": {
            "verdict": "PASS",
            "requirement_ids": clause_ids,
            "reasoning": REASON,
        },
    })
    findings["comprehensive_coverage"]["clause_ids"] = clause_ids
    assessment = {
        "sample_id": sample["sample_id"],
        "reviewer_identity": reviewer,
        "dispatch_id": dispatch_id,
        "checks": {
            name: {"verdict": "PASS", "reasoning": REASON}
            for name in vj.SAMPLE_ASSESSMENTS
        },
    }
    clauses = [{
        "requirement_id": req["id"],
        "clause": req["clause"],
        "verdict": "PASS",
        "reasoning": REASON,
        "sample_ids": [sample["sample_id"]],
        "reviewer_identity": reviewer,
        "dispatch_id": dispatch_id,
    } for req in requirements]
    response_path = tmp_path / "group" / ".responses" / "raw.json"
    response_path.parent.mkdir(parents=True)
    response_path.write_text(json.dumps({"returned": "exact raw response"}), encoding="utf-8")
    review_path = tmp_path / "group" / f"{NODE}.json"
    record = {
        **{key: value for key, value in core.items() if key != "samples"},
        "packet_digest": packet_digest,
        "sample_seeds": [42],
        "samples_reviewed": [sample],
        "sample_assessments": [assessment],
        "clause_evidence": clauses,
        "findings": findings,
        "overall": "PASS",
        "dispatch_provenance": [{
            "dispatch_id": dispatch_id,
            "reviewer_identity": reviewer,
            "review_date": "2026-09-14",
            "blind": True,
            "packet_digest": packet_digest,
            "clause_ids": clause_ids,
            "response_ref": ".responses/raw.json",
            "response_digest": hashlib.sha256(response_path.read_bytes()).hexdigest(),
        }],
    }
    return review_path, record


def _errors(tmp_path, monkeypatch, mutate):
    path, record = _record(tmp_path, monkeypatch)
    mutate(record)
    return vj._validate_v2_schema(NODE, path, record)


def test_valid_merged_record_has_no_schema_errors(tmp_path, monkeypatch):
    path, record = _record(tmp_path, monkeypatch)
    assert vj._validate_v2_schema(NODE, path, record) == []


def test_requirement_omission_is_unadjudicable(tmp_path, monkeypatch):
    errors = _errors(tmp_path, monkeypatch, lambda r: r["requirements_snapshot"].pop())
    assert any("requirements_snapshot is not the exact live" in error for error in errors)


def test_requirement_duplication_is_unadjudicable(tmp_path, monkeypatch):
    errors = _errors(tmp_path, monkeypatch,
                     lambda r: r["requirements_snapshot"].append(
                         copy.deepcopy(r["requirements_snapshot"][0])))
    assert any("requirements_snapshot is not the exact live" in error for error in errors)


def test_altered_requirement_wording_is_unadjudicable(tmp_path, monkeypatch):
    errors = _errors(tmp_path, monkeypatch,
                     lambda r: r["requirements_snapshot"][0].update(clause="altered"))
    assert any("requirements_snapshot is not the exact live" in error for error in errors)


def test_unknown_requirement_is_unadjudicable(tmp_path, monkeypatch):
    errors = _errors(tmp_path, monkeypatch,
                     lambda r: r["requirements_snapshot"].append(
                         {"kind": "task", "id": "invented", "clause": "invented"}))
    assert any("requirements_snapshot is not the exact live" in error for error in errors)


def test_packet_digest_cannot_be_repaired_to_modified_samples_by_claim(tmp_path, monkeypatch):
    def mutate(record):
        record["samples_reviewed"][0]["question_text"] += " altered"
        record["samples_reviewed"][0]["replay_digest"] = vj._json_digest(
            {k: v for k, v in record["samples_reviewed"][0].items() if k != "replay_digest"}
        )

    errors = _errors(tmp_path, monkeypatch, mutate)
    assert any("packet_digest does not match" in error for error in errors)


def test_missing_sample_assessment_is_rejected(tmp_path, monkeypatch):
    errors = _errors(tmp_path, monkeypatch, lambda r: r["sample_assessments"].clear())
    assert any("cover each delivered sample exactly once" in error for error in errors)


def test_duplicate_and_foreign_clause_ids_are_rejected(tmp_path, monkeypatch):
    def mutate(record):
        record["clause_evidence"][1]["requirement_id"] = "invented"

    errors = _errors(tmp_path, monkeypatch, mutate)
    assert any("exact requirement IDs once each" in error for error in errors)


def test_raw_response_drift_is_rejected(tmp_path, monkeypatch):
    def mutate(record):
        response = tmp_path / "group" / ".responses" / "raw.json"
        response.write_text('{"returned":"changed"}', encoding="utf-8")

    errors = _errors(tmp_path, monkeypatch, mutate)
    assert any("raw response digest does not match" in error for error in errors)


@pytest.mark.parametrize("field", ["sample_assessments", "clause_evidence"])
def test_assessment_identity_must_match_dispatch(tmp_path, monkeypatch, field):
    errors = _errors(tmp_path, monkeypatch,
                     lambda r: r[field][0].update(reviewer_identity="foreign-reviewer"))
    assert any("reviewer does not match dispatch" in error for error in errors), (
        f"seed=42 {field}: foreign reviewer accepted; errors={errors}"
    )


def test_clause_must_belong_to_attributed_dispatch(tmp_path, monkeypatch):
    errors = _errors(tmp_path, monkeypatch,
                     lambda r: r["dispatch_provenance"][0].update(
                         clause_ids=r["dispatch_provenance"][0]["clause_ids"][:-1]))
    assert any("clause allocation does not match" in error for error in errors), (
        f"seed=42 omitted dispatch clause accepted; errors={errors}"
    )
