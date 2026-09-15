"""H-05 regression controls for secondary-DNA vocabulary coverage."""

from __future__ import annotations

from types import SimpleNamespace

from backend.app.practice_gen.validation import validate_vocab


def test_vocab_audit_executes_secondary_dna(monkeypatch):
    calls = []

    def generated(*, dna, node_id, grade, seed, **_kwargs):
        calls.append(dna.concept)
        text = "Use multiplication to check." if dna.concept == "comparing_ordering" else "Clean."
        return SimpleNamespace(
            question_text=text,
            node_id=node_id,
            dna_concept=dna.concept,
            distractors=[],
            distractors_provenance={},
        )

    monkeypatch.setattr(validate_vocab, "generate_context", generated)
    result = validate_vocab.run_vocab_audit("mat_g1_mg_q1_1", grade=1, sample_count=1)

    assert calls == ["shapes_2d", "comparing_ordering"]
    assert result["pass_rate"] == 0.5
    assert any(
        "DNA=comparing_ordering" in violation and "multiplication" in violation
        for violation in result["violations"]
    )
