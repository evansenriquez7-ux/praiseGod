"""
H6: the retired §5/§6F gates' defects, carried as content (owner rulings 25, 52, 55).

Each test is the catching side of a mutation in tests/mutation_harness.py that plants into
`validate_carried` on the path run_all's `carried_defects_5_6` stage executes:

  carried_record_edit_goes_unseen     -> test_an_edited_record_breaks_the_freeze
  carried_concern_defect_dropped      -> test_a_sample_concern_is_carried_with_its_seed
  carried_stale_defect_still_reported -> test_a_stale_record_clears_and_owes_a_rejudgment
  carried_rejudgment_never_owed       -> test_a_stale_record_clears_and_owes_a_rejudgment
  carried_contradiction_dropped       -> test_carried_capabilities_equal_the_retired_gate

The two "equal the retired gate" tests compare against the retired validators' own output
on the live corpus, so the carried stage cannot drift from what the gates confirmed.
"""
from __future__ import annotations

import re
import shutil

import pytest

from backend.app.practice_gen.validation import validate_capability as VC
from backend.app.practice_gen.validation import validate_carried as VCAR
from backend.app.practice_gen.validation import validate_judgment as VJ

# An lc whose §5 record carries per-sample CONCERNs, and one whose standing attestation is
# NOT_PROVIDED (measured 2026-10-17: carried 15 and 1 respectively).
_JUDGED_LC = "mat_g1_dp_q3_0"
_CONTRADICTED_LCS = ["mat_g1_dp_q3_1", "mat_g1_na_q2_1"]


def _tree(tmp_path):
    for d in VCAR.FROZEN_DIRS:
        (tmp_path / d).mkdir(parents=True)
        (tmp_path / d / "r.json").write_text('{"overall": "CONCERN"}', encoding="utf-8")
    return tmp_path


def test_the_live_records_are_frozen():
    assert VCAR.frozen_findings() == []


def test_an_edited_record_breaks_the_freeze(tmp_path):
    root = _tree(tmp_path)
    pin = VCAR.records_digest(root)
    assert VCAR.frozen_findings(root, pin) == [], "control: an untouched tree is frozen"
    # Same file count, same length: only the bytes say a verdict was rewritten.
    path = root / VCAR.FROZEN_DIRS[0] / "r.json"
    path.write_text('{"overall": "PASSES!"}', encoding="utf-8")
    assert VCAR.frozen_findings(root, pin), "an edited record must break the freeze"
    shutil.rmtree(root / VCAR.FROZEN_DIRS[2])
    with pytest.raises(FileNotFoundError):
        VCAR.records_digest(root)


def _record():
    return {
        "samples_reviewed": [{"sample_id": "s1", "seed": 44, "serving_mode": "student_path",
                              "effective": {"format": "mcq"}},
                             {"sample_id": "s2", "seed": 502, "serving_mode": "student_path",
                              "effective": {"format": "cloze"}}],
        "sample_assessments": [
            {"sample_id": "s1", "checks": {"ambiguity": {"verdict": "PASS", "reasoning": "ok"},
                                           "learner_facing_clarity": {"verdict": "CONCERN",
                                                                      "reasoning": "hint mismatch"}}},
            {"sample_id": "s2", "checks": {"ambiguity": {"verdict": "PASS", "reasoning": "ok"}}},
        ],
        "clause_evidence": [{"requirement_id": "r1", "clause": "Count", "verdict": "CONCERN",
                             "sample_ids": ["s2"], "reasoning": "rare"}],
        "findings": {"cognitive_capacity": {"verdict": "PASS", "rationale": "fine"}},
        "overall": "CONCERN",
    }


def test_a_sample_concern_is_carried_with_its_seed():
    found = VCAR.judgment_defects("mat_x", _record())
    sample = [f for f in found if "learner_facing_clarity" in f]
    assert len(sample) == 1, found
    assert "seed 44" in sample[0] and "Owed:" in sample[0]
    clause = [f for f in found if "clause 'r1'" in f]
    assert len(clause) == 1 and "seeds [502]" in clause[0], found
    assert any("overall judgment verdict is CONCERN" in f for f in found)
    assert len(found) == 3, "a PASS check must not be carried"


# The retired gate's verdict lines, by the wording `validate_judgment._validate_one` prints.
_VERDICT_LINE = re.compile(r"is (CONCERN|FAIL); every (learner-visible sample|clause) must pass"
                           r"|decomposition must PASS|\(must be 'PASS'\)|overall judgment verdict is")


def test_carried_judgment_defects_equal_the_retired_gate():
    """Every lc: one carried defect per verdict line the retired §5 gate printed."""
    import json

    from backend.app.practice_gen.registry import get_all_node_ids

    for nid in sorted(get_all_node_ids()):
        path = VJ._node_file(nid)
        if not path.exists():
            continue
        retired = [e for e in VJ._validate_one(nid, path) if _VERDICT_LINE.search(e)]
        carried = VCAR.judgment_defects(nid, json.loads(path.read_text(encoding="utf-8")))
        assert len(carried) == len(retired), (nid, len(carried), len(retired))


def test_a_stale_record_clears_and_owes_a_rejudgment(monkeypatch):
    fresh = VCAR.collect_findings([_JUDGED_LC])
    assert any(f.startswith(_JUDGED_LC) for f in fresh["carried_judgment_defect_5"]), "control"
    assert fresh["carried_defect_rejudge_owed"] == []
    monkeypatch.setattr(VJ, "_validate_freshness", lambda nid, data: [f"{nid}: planted drift"])
    stale = VCAR.collect_findings([_JUDGED_LC])
    assert not any(f.startswith(_JUDGED_LC) for f in stale["carried_judgment_defect_5"]), \
        "a defect on a record that no longer replays must clear"
    assert [f for f in stale["carried_defect_rejudge_owed"] if f.startswith(_JUDGED_LC)], \
        "a cleared defect owes a §17 re-judgment"
    monkeypatch.setattr(VCAR, "_standing_stem_filed_at",
                        lambda node_ids: {n: "2026-10-18T00:00:00Z" for n in node_ids})
    assert VCAR.collect_findings([_JUDGED_LC])["carried_defect_rejudge_owed"] == [], \
        "a §17 record filed after retirement stands"


def test_carried_capabilities_equal_the_retired_gate():
    carried = VCAR.collect_findings(_CONTRADICTED_LCS)["carried_capability_defect_6F"]
    pair = re.compile(r"^(mat_\w+): capability '([^']+)'")
    retired = {pair.match(e).groups() for e in VC.validate_capability_attestation(_CONTRADICTED_LCS)
               if "CONTRADICTED" in e}
    assert retired, "control: these lcs carry CONTRADICTED verdicts"
    assert {pair.match(f).groups() for f in carried} == retired
