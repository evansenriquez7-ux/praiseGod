"""
§14 structured slots (owner rulings 28, 33, 34; batch H3): each domain kind accepts what is
inside it and rejects what is not, the replay reproduces a fill, and `fill` is byte-identical
to the f-string it replaces. The mutations in tests/mutation_harness.py prove the CLI path on
clean lcs; these pin each kind on its own so a kind cannot quietly start accepting anything.
"""
from __future__ import annotations

import pytest

from backend.app.practice_gen.slots import E, Fill, R, S, capture, fill, transform
from backend.app.practice_gen.validation import validate_slots as V

DIV = "backend.app.practice_gen.dna.na.division.EVEN_ODD_LABELS"
BANK = "backend.app.practice_gen.dna.mg.geometric_lines._ITEM_POOL"
NOUNS = "backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial._EMOJI_NAMES"


def _label(value, domain, given=None, texts=()):
    out = V.check_slot(value, domain, given or {}, set(texts))
    return None if out is None else out[0]


@pytest.mark.parametrize("value,domain,given,texts,expected", [
    (5, R(1, 9, "b"), {}, (), None),
    (10, R(1, 9, "b"), {}, (), "slot_domain_escape_14"),
    (True, R(0, 9, "b"), {}, (), "slot_domain_escape_14"),          # bool is not a number here
    ("odd", E(("even", "odd"), "b"), {}, (), None),
    ("prime", E(("even", "odd"), "b"), {}, (), "slot_domain_escape_14"),
    ("even", f"enum:{DIV}", {}, (), None),
    ("prime", f"enum:{DIV}", {}, (), "slot_domain_escape_14"),
    ("x", "enum:no.such.module.THING", {}, (), "slot_domain_unknown_14"),
    ("straight line", f"bank:{BANK}:answer", {}, (), None),
    ("wiggly line", f"bank:{BANK}:answer", {}, (), "slot_domain_escape_14"),
    ("curved line", f"bank:{BANK}:distractors", {}, (), None),        # list field flattened
    ("x", f"bank:{BANK}:no_such_field", {}, (), "slot_domain_unknown_14"),
    ("apples", f"noun:{NOUNS}", {}, (), None),                       # plural by the shared rule
    ("apple", f"noun:{NOUNS}", {}, (), None),
    ("items", f"noun:{NOUNS}", {}, (), "slot_domain_escape_14"),
    (31, "value:dividend", {"dividend": 31}, (), None),
    (32, "value:dividend", {"dividend": 31}, (), "slot_domain_escape_14"),
    (31, "value:dividend", {}, (), "slot_domain_escape_14"),
    (3, "num.derived", {}, (), None),
    ("3", "num.derived", {}, (), "slot_domain_escape_14"),
    ("🏀🏀", "text.derived", {}, (), None),
    (7, "text.derived", {}, (), "slot_domain_escape_14"),
    ("inner", "fill", {}, ("inner",), None),
    ("inner", "fill", {}, ("other",), "slot_text_unaccounted_14"),
    (1, None, {}, (), "slot_unclassified_14"),
    (1, "nonsense:kind", {}, (), "slot_domain_unknown_14"),
    (1, 42, {}, (), "slot_domain_unknown_14"),
])
def test_each_domain_kind(value, domain, given, texts, expected):
    assert _label(value, domain, given, texts) == expected


def test_fill_is_byte_identical_and_records_only_when_capturing():
    n = 31
    assert fill("Divide {n} by 2: how many 2s fit into {n}?", n=S(n, "num.derived")) \
        == f"Divide {n} by 2: how many 2s fit into {n}?"
    with capture() as fills:
        fill("{a} − {b}", a=S(5, "num.derived"), b=2)
    assert len(fills) == 1 and fills[0].slots == (("a", 5, "num.derived"), ("b", 2, None))
    assert fills[0].site.startswith("tests/unit/test_validate_slots.py:") or ":" in fills[0].site


def test_replay_accepts_a_true_fill_and_names_a_false_one():
    good = Fill(template="{a} + {b}", slots=(("a", 1, None), ("b", 2, None)), text="1 + 2", site="x:1")
    bad = Fill(template="{a} + {b}", slots=(("a", 1, None), ("b", 2, None)), text="1 + 3", site="x:1")
    assert V.replay(good) is None
    assert "replay gives '1 + 2'" in V.replay(bad)
    with capture() as fills:
        transform("strip_trailing_period", "It is 7.")
    assert V.replay(fills[0]) is None and fills[0].text == "It is 7"


def test_a_transform_with_an_argument_replays_and_its_argument_is_domain_checked():
    """H3-R1: `fill_blank` writes a claimed value into another fill's blank; the check
    replays it with every recorded slot and judges the value's domain like any slot."""
    with capture() as fills:
        stem = fill("If {d} + {b} = {a}, then {a} − {b} = ___.", d=S(7, "num.derived"),
                    b=S(5, "num.derived"), a=S(12, "num.derived"))
        out = transform("fill_blank", stem, value=S(8, E((7, 8), "claimed values")))
    assert out == "If 7 + 5 = 12, then 12 − 5 = 8." == stem.replace("___", "8")
    f = fills[-1]
    assert f.renderer == "fill_blank" and V.replay(f) is None
    assert f.slots[1] == ("value", 8, E((7, 8), "claimed values"))
    forged = Fill(template=f.template, slots=f.slots, text=out.replace("8.", "9."), site=f.site,
                  renderer=f.renderer)
    assert "replay gives" in V.replay(forged)
    assert V.check_slot(9, f.slots[1][2], {}, set())[0] == "slot_domain_escape_14"


@pytest.mark.parametrize("node_id", ["mat_g2_na_q3_8", "mat_g2_mg_q4_3"])
def test_the_instrumented_prototype_lcs_are_clean(node_id):
    """The two lcs the §14 mutations plant on: a red baseline here makes them INVALID."""
    found = V.collect_findings([node_id])
    assert not any(found.values()), found


def test_an_uninstrumented_field_is_named_by_lc_seed_and_formatter(monkeypatch):
    # Since the H3 rollout finished (H3-R2, 2026-10-11) no lc carries un-instrumented text,
    # so the text is planted: the addition DNA's hints built without `fill`.
    from backend.app.practice_gen.dna.na import addition
    monkeypatch.setattr(addition, "generate_hints",
                        lambda values, cumulative_vocab: [f"Add {values['a']} and {values['b']}."])
    found = V.collect_findings(["mat_g1_na_q2_4"])
    items = found["slot_text_unaccounted_14"]
    # A field names the formatter and DNA; a nested slot names the exact file:line site.
    assert items and all(i.startswith("mat_g1_na_q2_4: ") and " at seed " in i
                         and ("formatter " in i or "backend/app/practice_gen/" in i)
                         for i in items)
    assert any("hints" in i and "DNA addition" in i for i in items)


def test_a_fill_slot_is_not_accounted_by_its_own_fill():
    """H5: an identity transform must not let un-instrumented text account for itself."""
    from backend.app.practice_gen.slots import capture, transform
    with capture() as fills:
        out = transform("strip_trailing_period", "90 − 2 = 87")   # no period: identity
    assert out == "90 − 2 = 87" and len(fills) == 1
    f = fills[0]
    others = {g.text for g in fills} - {f.text}
    assert V.check_slot(f.slots[0][1], "fill", {}, others)[0] == "slot_text_unaccounted_14"


def test_a_spine_replays_through_the_generator_renderer_and_chooses_its_article():
    """H3-R2 / owner ruling 40: a spine is recorded with renderer "spine" and replayed by
    the generator's own render_spine_text; "A {place}" agrees with the place's sound."""
    from backend.app.practice_gen.dna.base import Spine, render_spine_text
    sp = Spine(id="t", template="A {place} has {a} {objects}.", required_concepts=set(),
               blank_target="a", grade_band=(1, 3))
    with capture() as fills:
        text = sp.render({"place": "art fair", "objects": "paintbrushes", "actor": "Mika",
                          "item1": "pencil", "item2": "eraser"}, {"a": 1})
    assert text == "An art fair has 1 paintbrush."
    f = fills[-1]
    assert f.renderer == "spine" and V.replay(f) is None
    assert render_spine_text("A {place} is here.", place="classroom") == "A classroom is here."


def test_bank_fields_records_the_row_as_domain_and_provenance():
    from backend.app.practice_gen.slots import bank_fields
    with capture() as fills:
        out = bank_fields({"question": "Q?", "answer": "square", "distractors": ["a", "b"], "kind": "x"},
                          "backend.app.practice_gen.dna.mg.shapes_2d._ITEM_POOL")
    assert out["question"] == "Q?" and out["distractors"] == ["a", "b"]
    q = next(f for f in fills if f.text == "Q?")
    assert q.slots[0][2] == "bank:backend.app.practice_gen.dna.mg.shapes_2d._ITEM_POOL:question"
    assert dict(q.sources)["question"] == ("question", "answer", "distractors", "kind")
