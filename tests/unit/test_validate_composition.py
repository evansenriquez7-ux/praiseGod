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


def test_value_level_provenance_closes_in_both_declared_directions():
    """Owner ruling 41 (H3-R2): `derives` credits the chooser through a SHOWN value;
    `computes` credits a value whose every source is shown; neither credits an unshown value."""
    from backend.app.practice_gen.slots import computes, derives
    with capture() as fills:
        derives("a", src=("task_type",))
        computes("remainder", src=("a", "b"))
        stem = fill("What is {a} + {b}?", a=S(0, "value:a"), b=S(7, "value:b"))
    keys = VC.exhibited_keys({"question_text": stem, "hints": [], "format_data": {}}, fills)
    assert {"a", "b", "task_type", "remainder"} <= keys
    with capture() as fills2:
        derives("a", src=("task_type",))
        computes("remainder", src=("a", "b"))
        stem2 = fill("What is the sum with {b}?", b=S(7, "value:b"))
    keys2 = VC.exhibited_keys({"question_text": stem2, "hints": [], "format_data": {}}, fills2)
    assert "task_type" not in keys2 and "remainder" not in keys2


def test_template_provenance_is_recorded_as_a_template_source():
    """`fill(..., _src=...)`: the values keys that CHOSE the template (H3-R2)."""
    with capture() as fills:
        stem = fill("What is {a} + {b}?", _src=("task_type",), a=S(1, "value:a"), b=S(2, "value:b"))
    assert dict(fills[0].sources)["__template__"] == ("task_type",)
    assert "task_type" in VC.exhibited_keys({"question_text": stem, "hints": [], "format_data": {}}, fills)
