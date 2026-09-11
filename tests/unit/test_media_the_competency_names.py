"""
test_media_the_competency_names.py
==================================
Pins the two pictures mat_g2_na_q3_0 and mat_g2_na_q3_1 name in their own words, and
that each agrees with the answer its item is keyed to.

Why it exists
-------------
mat_g2_na_q3_1 reads "Illustrate and write multiplication as repeated addition, using a
variety of concrete and pictorial models and numerals, and using groups of equal
quantities, arrays, counting by multiples, and EQUAL JUMPS ON A NUMBER LINE." Arrays
were drawn by GridArea. The other two were not drawn at all:

  * the number line rendered "Starting at 0, taking 2 equal jumps of 9 on the number
    line lands on ___" over a line carrying a single dot -- text DESCRIBING a picture
    the payload had no field to express;
  * `emoji_pictorial` hard-coded `operation = ... if ... in ("addition", "subtraction")
    else "addition"`, so pointed at a multiplication node it drew `a + b` items beside
    an answer of `a x b` -- a picture that contradicts its own key.

Both are now built. The jumps half is pinned HERE rather than by §9, and that is the
point of the file: the React component reads `jump_count`/`jump_size` inside a branch,
so `tests/frontend/extract_visual_contract.mjs` classifies them CONDITIONAL, and §9
enforces unconditional keys only ("reported, not enforced" -- its own named limit). A
payload that silently stopped carrying its jumps would therefore pass every § check in
the harness and ship a bare line under a stem promising arrows. That is precisely the
shape of gap Scaling Mandate 1 calls a broken check, so the absence gate lives in a unit
test, where it is cheap and mutation-provable.

The emoji half IS caught by §1E (the key would stop matching `a * b`), but §1E can only
say the ANSWER is wrong; this says what the PICTURE draws, which is the clause being
served.
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, _REPO_ROOT)

from backend.app.services.orchestrator import PracticeOrchestrator  # noqa: E402

_SEEDS = (11, 23, 42, 57, 64, 78, 91, 103)


def _payloads(node_id, formatter):
    """Every (given_values, visual_params, keyed value) this node serves at _SEEDS."""
    out = []
    for seed in _SEEDS:
        p = PracticeOrchestrator.generate_problem(
            node_id=node_id, seed=seed, formatter=formatter, is_lab=False
        )
        d = p if isinstance(p, dict) else p.__dict__
        fd = d.get("format_data") or {}
        options = fd.get("mcq_options") or fd.get("options") or []
        keyed = d.get("correct_answer")
        if isinstance(keyed, str) and len(keyed) == 1 and keyed.isalpha():
            matched = [o for o in options if o.get("key") == keyed]
            assert matched, f"{node_id} seed {seed}: option key {keyed!r} is not among the options"
            keyed = matched[0]["value"]
        out.append((seed, d.get("given_values") or {}, d.get("visual_params") or {}, keyed))
    assert out, "no samples generated"
    return out


def test_multiplication_number_line_carries_its_jumps():
    """The payload declares the jumps the stem promises, and they land on the key."""
    for seed, values, vp, keyed in _payloads("mat_g2_na_q3_1", "number_line_read"):
        a, b = values.get("a"), values.get("b")
        assert vp.get("jump_size") == a, (
            f"seed {seed}: number line for {b} jumps of {a} carries jump_size="
            f"{vp.get('jump_size')!r}. The stem promises arrows the picture will not draw."
        )
        assert vp.get("jump_count") == b, (
            f"seed {seed}: number line for {b} jumps of {a} carries jump_count="
            f"{vp.get('jump_count')!r}."
        )
        landing = vp["jump_from"] + vp["jump_size"] * vp["jump_count"]
        assert landing == keyed, (
            f"seed {seed}: the drawn jumps land on {landing} but the item is keyed to "
            f"{keyed}. The picture and the answer disagree."
        )


def test_number_line_set_mode_draws_no_jumps():
    """A 'set' item asks the pupil to PLACE the landing point; drawing it answers it."""
    import random

    from backend.app.practice_gen.formatters.visual.fmt_number_line import format_number_line

    read = PracticeOrchestrator.generate_problem(
        node_id="mat_g2_na_q3_1", seed=42, formatter="number_line_read", is_lab=False
    )
    d = read if isinstance(read, dict) else read.__dict__
    assert d["visual_params"].get("jump_count"), "precondition: the read payload has jumps"

    from backend.app.practice_gen.generators.base_generator import generate_context
    from backend.app.practice_gen.adapter import _get_dna_instance

    dna = _get_dna_instance("multiplication")
    ctx = generate_context(dna, "mat_g2_na_q3_1", 2, 42,
                           {"task_type": "number_line_jumps", "context": "pure"})
    problem = format_number_line(ctx, random.Random(42), interaction_mode="set",
                                 answer_collection="fill_in_blank")
    for key in ("jump_from", "jump_size", "jump_count"):
        assert key not in problem.visual_params, (
            f"a 'set' number line carries {key}: the run of jumps ends on the value the "
            f"pupil is being asked to place, so drawing it hands over the answer."
        )


@pytest.mark.parametrize("node_id", ["mat_g2_na_q3_0", "mat_g2_na_q3_1"])
def test_emoji_pictorial_draws_groups_of_equal_quantities(node_id):
    """b groups of a items, and a x b is what the item keys."""
    for seed, values, vp, keyed in _payloads(node_id, "emoji_pictorial"):
        assert vp.get("operation") == "multiplication", (
            f"{node_id} seed {seed}: emoji picture drawn as {vp.get('operation')!r} on a "
            f"multiplication node -- the picture shows a different operation than the key."
        )
        assert vp["group_a"] == values.get("a") and vp["group_b"] == values.get("b"), (
            f"{node_id} seed {seed}: picture shows {vp['group_b']} groups of {vp['group_a']} "
            f"for an item generated as {values.get('b')} x {values.get('a')}."
        )
        assert vp["group_a"] * vp["group_b"] == keyed, (
            f"{node_id} seed {seed}: {vp['group_b']} groups of {vp['group_a']} is "
            f"{vp['group_a'] * vp['group_b']} items, but the item is keyed to {keyed}."
        )
