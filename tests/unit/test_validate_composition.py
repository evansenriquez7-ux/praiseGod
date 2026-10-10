"""§15 (batch H5, owner rulings 35-36): provenance, the record rule and the text stopgap."""
from backend.app.practice_gen.slots import S, capture, fill
from backend.app.practice_gen.validation import validate_composition as VC


def test_provenance_is_recorded_and_value_domain_implies_it():
    with capture() as fills:
        fill("{a} and {seq}", a=S(3, "value:a"), seq=S("1, 3, 5", "text.derived", src=("skip_by",)))
    assert dict(fills[0].sources) == {"a": ("a",), "seq": ("skip_by",)}


def _problem(stem, hints, vp=None):
    return {"question_text": stem, "hints": hints, "visual_params": vp or {}, "format_data": {}}


def test_hint_run_absent_from_the_item_is_a_finding():
    p = _problem("What number is marked on the number line?",
                 ["Look at the list of numbers: 40, 42, 44, 46, ___"], {"start": 40, "value": 48})
    found = VC.hint_runs_unshown(p)
    assert found and found[0][2] == ["42", "44", "46"]


def test_hint_run_shown_in_the_stem_or_bracketed_is_not():
    shown = _problem("What comes next: 40, 42, 44, 46, ___", ["Look at the list of numbers: 40, 42, 44, 46, ___"])
    bracket = _problem("29, 21, 28, ___", ["Repeat the ones [9, 1, 8] and add 50 every group."])
    assert VC.hint_runs_unshown(shown) == [] and VC.hint_runs_unshown(bracket) == []


def test_record_rule_ignores_hints_and_follows_nested_fills():
    with capture() as fills:
        inner = fill("{seq}", seq=S("40, 42, 44, 46", "text.derived", src=("skip_by",)))
        stem = fill("What comes next: {s}, ___", s=S(inner, "fill"))
        hint = fill("Jump by {k}", k=S(2, "value:skip_by"))
    p = {"question_text": stem, "hints": [hint], "format_data": {}}
    assert "skip_by" in VC.exhibited_keys(p, fills)
    with capture() as fills2:
        stem2 = fill("What number is marked?")
        hint2 = fill("Jump by {k}", k=S(2, "value:skip_by"))
    p2 = {"question_text": stem2, "hints": [hint2], "format_data": {}}
    keys = VC.exhibited_keys(p2, fills2)
    assert keys is not None and "skip_by" not in keys
    sel = {"observe": [{"path": "skip_by", "equals": 2}]}
    assert VC.selector_unexhibited(sel, {"skip_by": 2}, None, keys) == ["skip_by"]


def test_an_unaccounted_field_makes_the_render_undecided():
    with capture() as fills:
        fill("Jump by {k}", k=S(2, "value:skip_by"))
    p = {"question_text": "built without fill", "hints": [], "format_data": {}}
    assert VC.exhibited_keys(p, fills) is None
