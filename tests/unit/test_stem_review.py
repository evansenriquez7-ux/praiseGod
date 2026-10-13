"""§17 stem review gate (batch H4, owner rulings 24, 44): the packet rules and the record rules."""
import copy
import json
from pathlib import Path

import pytest

from backend.app.practice_gen.slots import Fill
from backend.app.practice_gen.validation import stem_packets as SP
from backend.app.practice_gen.validation import validate_stem_review as V

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "stem_review_fixtures"
MAIN = "mat_g2_na_q3_8"


def _record(lc=MAIN, role="confirming"):
    return json.loads((FIXTURES / lc / f"fixture-{lc}-{role}.json").read_text(encoding="utf-8"))


def test_the_fixture_baseline_every_17_mutation_plants_into_is_clean():
    """A red baseline here makes every §17 mutation INVALID (re-run tests/stem_review_fixture.py)."""
    found, stats = V.collect_findings([MAIN], FIXTURES)
    assert not any(found.values()), {k: v for k, v in found.items() if v}
    assert stats["approved"] == 1


def _fill(template, *domains):
    return Fill(template=template, slots=tuple((f"s{i}", "x", d) for i, d in enumerate(domains)),
                text="x", site="backend/app/practice_gen/x.py:1")


@pytest.mark.parametrize("template,domains,wordless", [
    ("{answer}", ("fill",), True),
    ("{p0}, {p1}", ("fill", "fill"), True),
    ("{statement}. True or False?", ("fill",), False),      # adds words: a family (ruling 44a)
    ("{p0} and {p1}", ("fill", "fill"), False),
    ("{p0}, {p1}", ("fill", "value:a"), False),             # a non-fill slot: a family
    ("{{{p0}}}", ("fill",), True),                          # escaped braces are not letters
])
def test_a_wrapper_collapses_only_when_all_fill_and_wordless(template, domains, wordless):
    assert SP.is_wordless_wrapper(_fill(template, *domains)) is wordless


def test_the_family_key_leaves_out_the_line_but_keeps_module_template_and_renderer():
    a = Fill(template="T {x}", slots=(), text="", site="backend/app/practice_gen/m.py:10")
    b = Fill(template="T {x}", slots=(), text="", site="backend/app/practice_gen/m.py:99")
    c = Fill(template="T {x}", slots=(), text="", site="backend/app/practice_gen/m.py:10", renderer="capitalize")
    assert SP.family_key(a) == SP.family_key(b) != SP.family_key(c)


def test_the_hash_excludes_the_item_id_and_moves_with_anything_the_judge_reads():
    item = _record()["packet"]
    body = {k: v for k, v in item.items() if k != "item"}
    assert SP.item_hash(item) == SP.item_hash({**item, "item": "OTHER"}) == SP.item_hash(body)
    moved = copy.deepcopy(body)
    moved["clauses"][0]["clause"] += "!"
    assert SP.item_hash(moved) != SP.item_hash(body)


def test_a_reply_is_parsed_without_repair():
    assert V.parse_reply('```json\n{"a": 1}\n```') == {"a": 1}
    with pytest.raises(json.JSONDecodeError):
        V.parse_reply('Here is my verdict: {"a": 1}')


def test_a_verdict_must_answer_every_clause_and_quote_printed_templates():
    rec = _record()
    reply = V.parse_reply(rec["raw_reply"])
    assert V.verdict_problems(reply, rec["packet"]) == []
    short = copy.deepcopy(reply)
    short["clauses"].pop("divisor_2")
    assert any("are not exactly the packet's clauses" in p for p in V.verdict_problems(short, rec["packet"]))
    failing = copy.deepcopy(reply)
    failing.update(overall="FAIL", failing_families=[], failing_templates=[])
    assert any("names no failing template or family" in p for p in V.verdict_problems(failing, rec["packet"]))
    invented = copy.deepcopy(reply)
    invented["clauses"]["division"]["template"] = "Share {n} among 2."
    assert any("must quote a template the packet prints" in p for p in V.verdict_problems(invented, rec["packet"]))


def test_a_fixture_identity_is_refused_outside_a_fixture_directory():
    bad, _drift = V.record_problems(_record(), fixture_dir=False)
    assert any("mutation-proof fixture identity" in p for p in bad)
    assert V.record_problems(_record(), fixture_dir=True) == ([], [])


def test_the_filer_refuses_an_identity_already_used_on_another_lc():
    from tests import stem_file
    rec = _record()
    rec["judged_by"] = "fixture-not-a-judge-mat_g3_mg_q2_0-first"
    problems = stem_file.refusals(rec, FIXTURES)
    assert any("is already on records of ['mat_g3_mg_q2_0']" in p for p in problems)


def test_a_slot_is_printed_under_its_own_name_not_its_lists():
    """
    Found 2026-10-13 in a real packet: moving a bank field into the `lists` table reused the slot
    loop's variable, so `{answer}` was printed with a slot named '_ITEM_POOL.answer' (94 of 151
    packets). mat_g3_dp_q3_4 draws its stems from a bank and has no renderer extras, so every
    family's printed slot names must equal its template's fields exactly.
    """
    import string
    item, _key = SP.build_item("mat_g3_dp_q3_4")
    assert item["lists"], "the lc's bank fields must be printed in the lists table"
    for fam in item["families"]:
        fields = {f for _l, f, _s, _c in string.Formatter().parse(fam["template"]) if f is not None}
        printed = {name for group in fam["slots"] for name in group["slots"]}
        assert printed == fields, (fam["id"], fam["template"], printed)
    members = item["lists"]["_ITEM_POOL.answer"]
    assert len(members) == len({json.dumps(m) for m in members}), "a list prints each member once"


def test_a_family_id_must_print_exactly_the_template_quoted_beside_it():
    """Ruling 46b: two families can print one template, so ids and quotes must agree."""
    rec = _record()
    reply = V.parse_reply(rec["raw_reply"])
    odd = "1 is left over, so {n} is an odd number."
    ok = copy.deepcopy(reply)
    ok.update(overall="FAIL", failing_families=["F01"], failing_templates=[odd])
    assert V.verdict_problems(ok, rec["packet"]) == []
    wrong = copy.deepcopy(ok)
    wrong["failing_families"] = ["F04"]
    assert any("print the template(s)" in p for p in V.verdict_problems(wrong, rec["packet"]))
    unknown = copy.deepcopy(ok)
    unknown["failing_families"] = ["F99"]
    assert any("'F99' is not a family id the packet prints" in p for p in V.verdict_problems(unknown, rec["packet"]))
    missing = copy.deepcopy(reply)
    missing.pop("failing_families")
    assert any("failing_families is not a list" in p for p in V.verdict_problems(missing, rec["packet"]))
    clause = copy.deepcopy(reply)
    clause["clauses"]["division"]["family"] = "F01"
    assert any("family 'F01' is not a packet family printing" in p for p in V.verdict_problems(clause, rec["packet"]))
    np = copy.deepcopy(reply)
    np["clauses"]["division"] = {"verdict": "NOT_PRODUCIBLE", "family": "F03", "template": None, "reasoning": "x"}
    assert any("NOT_PRODUCIBLE quotes no template and no family" in p for p in V.verdict_problems(np, rec["packet"]))


def test_every_family_says_where_the_learner_reads_it():
    """
    Ruling 46a. Found on the first real dispatch (2026-10-14): a judge read mat_g1_dp_q3_0's
    option family `{member}` as "the whole stem". Measured over its 43 renders independently of
    the builder, the option families are read only as answer choices and the bank question
    only as the question; the packet must say so.
    """
    item, _key = SP.build_item("mat_g1_dp_q3_0")
    by = {}
    for fam in item["families"]:
        by.setdefault(fam["template"], []).append(set(fam["appears_in"]))
        assert fam["appears_in"] or fam["nested_in"], fam
    assert by["{question}"] == [{"question_text"}]
    assert by["{member}"] == [{"distractors", "format_data.options"}]
    assert all(roles == {"correct_answer", "format_data.options"} for roles in by["{answer}"])
    assert len(by["{answer}"]) == 2, "two families print '{answer}': the case ruling 46b's ids exist for"
