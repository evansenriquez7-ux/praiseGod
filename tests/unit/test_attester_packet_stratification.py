"""Provider-variant stratification for blind capability packets.

The gate is deliberately exercised through ``build``: a helper-only test would stay
green if the builder stopped putting the allocated samples into the packet the Attester
actually receives.
"""

from __future__ import annotations

from tests import attester_packets as ap
from tests import frontend_renderer


_NODE = "synthetic_node"
_CAPABILITY = "count_forward_from_a_given_number"
_VARIANT = ("direction", "forward")


def _sample(node_id, seed, difficulty_profile=None):
    private = dict(difficulty_profile or {})
    return {
        "node_id": node_id,
        "seed": seed,
        "formatter": "mcq",
        "question_text": f"seed {seed}",
        "correct_answer": 1,
        "resolved_answer": 1,
        "requested": {
            "difficulty_profile": difficulty_profile,
            "student_interest": None,
            "experience": "standard",
        },
        "serving_mode": "student_path",
        "effective": {
            "format": "mcq",
            "is_visual": False,
            "visual_type": None,
            "interaction_mode": None,
            "answer_collection": None,
            "experience": "standard",
        },
        "_provider_variant_evidence": private,
    }


def _build(monkeypatch):
    monkeypatch.setattr(ap, "get_node_info", lambda _node_id: {
        "competency": "Count forward from a given number.",
        "grade": 1,
        "quarter": 1,
        "requires": [{"id": _CAPABILITY, "clause": "counting up"}],
    })
    monkeypatch.setattr(ap, "_provider_variants_for",
                        lambda _node_id, _capability_id: [_VARIANT])
    monkeypatch.setattr(ap, "_render", _sample)
    monkeypatch.setattr(frontend_renderer, "attach_rendered_visual_descriptions",
                        lambda samples: samples)
    return ap.build([_NODE])


def test_every_provider_variant_keeps_two_samples_in_the_attester_packet(monkeypatch):
    packets, key = _build(monkeypatch)
    packet = packets[0]
    private = key[packet["item"]]
    mapping = private["provider_variant_seed_map"]

    assert len(mapping) == 1
    assert mapping[0]["variant"] == list(_VARIANT)
    assert len(mapping[0]["seeds"]) == 2
    sample_by_seed = {sample["seed"]: sample for sample in packet["samples"]}
    assert set(mapping[0]["seeds"]) <= set(sample_by_seed), (
        "provider_variant_stratification_6F: allocated provider-variant samples "
        "were dropped before the Attester packet"
    )
    for seed in mapping[0]["seeds"]:
        assert sample_by_seed[seed]["requested"]["difficulty_profile"] == {
            _VARIANT[0]: _VARIANT[1]
        }


def test_seed_map_is_printed_without_leaking_provider_labels(monkeypatch):
    packets, _key = _build(monkeypatch)
    prompt = ap.render_prompt_block(packets)
    for seed in packets[0]["provider_variant_strata"][0]["seeds"]:
        assert str(seed) in prompt
    map_block = prompt.split("PROVIDER-VARIANT SEED MAP", 1)[1].split("SAMPLES:", 1)[0]
    assert "direction" not in map_block
    assert "forward" not in map_block


def test_variant_seed_sequence_is_stable_and_variant_specific():
    first = ap._variant_seed_candidates(_VARIANT)
    assert first == ap._variant_seed_candidates(_VARIANT)
    assert first != ap._variant_seed_candidates(("direction", "backward"))
    assert len(first) == len(set(first))
