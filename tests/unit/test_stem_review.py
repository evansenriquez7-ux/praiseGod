"""§17 stem review gate (batch H4, owner rulings 24, 44): the packet rules and the record rules."""
import copy
import dataclasses
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
    assert item["banks"], "the lc's bank fields must be printed in the banks table (ruling 47)"
    for fam in item["families"]:
        fields = {f for _l, f, _s, _c in string.Formatter().parse(fam["template"]) if f is not None}
        printed = {name for group in fam["slots"] for name in group["slots"]}
        assert printed == fields, (fam["id"], fam["template"], printed)


def test_an_item_bank_is_printed_row_by_row():
    """
    Ruling 47. Found on the second real dispatch (2026-10-14): each bank field printed as its own
    flat list, so a judge FAILed mat_g1_dp_q3_0's correctly keyed interview bank as "questions
    and answers can be mismatched". Measured over its 43 renders independently of the builder,
    every question is printed with its own row's answer and options; the packet must show the
    rows and say so. A render that prints fields of two rows must turn the flag false.
    """
    from backend.app.practice_gen.dna.dp.pictographs import _INTERVIEW_POOL
    from backend.app.practice_gen.slots import Trace

    renders, _refused = SP.observe_lc("mat_g1_dp_q3_0")
    item, key = SP.build_item("mat_g1_dp_q3_0", renders)
    bank = item["banks"]["_INTERVIEW_POOL"]
    assert bank["fields"] == ["answer", "distractors", "question"]
    assert bank["one_row_per_problem"] is True
    assert bank["rows"] == [{f: r[f] for f in bank["fields"]} for r in _INTERVIEW_POOL]
    assert key["banks"]["_INTERVIEW_POOL"]["first_render_not_from_one_row"] is None
    assert not any(k.startswith("_INTERVIEW_POOL") for k in item["lists"]), "a bank is not flattened into lists"
    for fam in item["families"]:
        for group in fam["slots"]:
            for d in group["domains"]:
                if d["domain"] == "a field of a fixed item bank":
                    assert d["bank"] == "_INTERVIEW_POOL" and "members_in_list" not in d, d

    seed, fmt, problem, fills, values = renders[0]
    own = next(r for r in _INTERVIEW_POOL if r["question"] == problem["question_text"])
    other = next(r for r in _INTERVIEW_POOL if r["answer"] != own["answer"] and r["question"] != own["question"])
    mixed = Trace()
    for f in fills:
        if f.slots and f.slots[0][2] == "bank:backend.app.practice_gen.dna.dp.pictographs._INTERVIEW_POOL:question":
            f = dataclasses.replace(f, text=other["question"], slots=((f.slots[0][0], other["question"], f.slots[0][2]),))
        mixed.append(f)
    mixed.derivations = fills.derivations
    swapped = (seed, fmt, {**problem, "question_text": other["question"]}, mixed, values)
    item2, key2 = SP.build_item("mat_g1_dp_q3_0", [swapped] + renders[1:])
    assert item2["banks"]["_INTERVIEW_POOL"]["one_row_per_problem"] is False
    assert key2["banks"]["_INTERVIEW_POOL"]["first_render_not_from_one_row"] == [seed, fmt]
    assert SP.item_hash(item2) != SP.item_hash(item)


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


def _domains(item):
    for fam in item["families"]:
        for group in fam["slots"]:
            for d in group["domains"]:
                yield fam, group["slots"], d


def test_a_vocabulary_gate_shows_only_the_word_it_gives_the_lc():
    """
    Ruling 48a. Found on the first H4-C fan-out (2026-10-14): S441-004's judge FAILed four
    templates of mat_g1_dp_q3_3 on "chart", the other word of a `'table'` gate, though the lc
    knows "table" and none of its 43 renders prints "chart". The packet must show only the word
    the gate gives this lc, resolved by the generator's own vocabulary rule.
    """
    from backend.app.practice_gen.generators.base_generator import generator_vocabulary, get_node

    assert "table" in generator_vocabulary(get_node("mat_g1_dp_q3_3"))
    renders, _refused = SP.observe_lc("mat_g1_dp_q3_3")
    printed = {f.slots[i][1] for _s, _f, _p, fills, _v in renders for f in fills
               for i, (n, _val, _d) in enumerate(f.slots) if n in ("table_word", "chart_word")}
    assert printed == {"table"}, "measured independently of the builder: only 'table' is printed"
    item, _key = SP.build_item("mat_g1_dp_q3_3", renders)
    gates = [d for _f, names, d in _domains(item) if set(names) & {"table_word", "chart_word"}]
    assert gates and all(d == {"domain": "the one word a vocabulary gate gives this lc",
                               "basis": "'table' gated by cumulative_vocab", "requires_vocab": "table",
                               "prints": "table", "words_left_out": 1} for d in gates), gates
    assert "chart" not in json.dumps(item["families"], ensure_ascii=False).replace("chart_word", "")


def test_a_bank_shows_only_the_rows_the_lc_draws():
    """
    Ruling 48b. S441-005's judge FAILed mat_g1_mg_q1_0 on 'circle' and 'corner' rows of a shared
    `_ITEM_POOL` its filter never draws (74 rows printed; its 43 renders offer only triangle,
    square, rectangle and "none of these"). The packet shows the rows drawn on the enumerated
    paths or the SWEEP_SEEDS student renders, and how many it leaves out; computed here from the
    renders by value, independently of the builder's loop.
    """
    from backend.app.practice_gen.dna.mg.shapes_2d import _ITEM_POOL
    from backend.app.practice_gen.validation import validate_slots as VS

    dotted = "backend.app.practice_gen.dna.mg.shapes_2d._ITEM_POOL"
    renders, _refused = SP.observe_lc("mat_g1_mg_q1_0")
    item, key = SP.build_item("mat_g1_mg_q1_0", renders)
    bank = item["banks"]["_ITEM_POOL"]
    seen_answers = set()
    for p, fills in [(r[2], r[3]) for r in renders] + [VS.observe("mat_g1_mg_q1_0", s)[:2] for s in SP.SWEEP_SEEDS]:
        seen_answers |= {v for f in SP.reaching(p, fills) for _n, v, d in f.slots if d == f"bank:{dotted}:answer"}
    assert {r["answer"] for r in bank["rows"]} == seen_answers
    assert not any("circle" in json.dumps(r) or "corner" in json.dumps(r) for r in bank["rows"])
    carrying = [r for r in _ITEM_POOL if any(f in r for f in bank["fields"])]
    assert bank["rows_left_out"] == len(carrying) - len(bank["rows"]) > 0
    assert key["banks"]["_ITEM_POOL"]["sweep_seeds"] == [SP.SWEEP_SEEDS[0], SP.SWEEP_SEEDS[-1]]


def test_a_runtime_list_read_from_the_drawn_row_is_shown_as_that_rows_field():
    """
    Ruling 48c. S441-003's judge FAILed mat_g1_dp_q3_2's {subj} as printable with another
    theme's categories; its 13 compare renders all pair them, because the categories are the
    drawn `_THEMES` row's own -- but the packet showed them as a separate list. Observed per
    render: the slot is shown as the row's `categories` field. A render whose categories come
    from ANOTHER row must undo that (and change the hash).
    """
    from backend.app.practice_gen.dna.dp.pictographs import _THEMES
    from backend.app.practice_gen.slots import E, Trace

    renders, _refused = SP.observe_lc("mat_g1_dp_q3_2")
    item, _key = SP.build_item("mat_g1_dp_q3_2", renders)
    assert "categories" in item["banks"]["_THEMES"]["fields"]
    paired = [(names, d) for _f, names, d in _domains(item) if d.get("read_from")]
    assert paired and all(d["bank"] == "_THEMES" and d["field"] == "categories" for _n, d in paired)
    assert {f["template"] for f, _n, d in _domains(item) if d.get("read_from")} >= {"{p0}, {p1}, {p2}", "{join} or {v}"}
    # A categories slot stays a runtime list only where some render filling it prints NO field of
    # the bank (the reading questions, each a theme's own `question_stem`): no row to observe.
    left = {f["template"] for f, _n, d in _domains(item) if d.get("basis") == "the graph's categories"}
    for tpl in left:
        assert any(not any(isinstance(d, str) and "_THEMES" in d for g in SP.reaching(p, fl) for _n, _v, d in g.slots)
                   for _s, _f, p, fl, _v in renders if any(g.template == tpl for g in fl)), tpl

    i, (seed, fmt, problem, fills, values) = next(
        (i, r) for i, r in enumerate(renders)
        if any(f.template == "{p0}, {p1}, {p2}" and isinstance(d, E) and d.basis == "the graph's categories"
               for f in r[3] for _n, _v, d in f.slots))
    foreign = tuple(c for t in _THEMES for c in t["categories"])        # every theme's categories
    moved = Trace()
    for f in fills:
        moved.append(dataclasses.replace(f, slots=tuple(
            (n, v, E(foreign, d.basis) if isinstance(d, E) and d.basis == "the graph's categories" else d)
            for n, v, d in f.slots)))
    moved.derivations = fills.derivations
    item2, _k2 = SP.build_item("mat_g1_dp_q3_2", renders[:i] + [(seed, fmt, problem, moved, values)] + renders[i + 1:])
    p012 = [d for f, _n, d in _domains(item2) if f["template"] == "{p0}, {p1}, {p2}"]
    assert p012 and all(d.get("basis") == "the graph's categories" and not d.get("read_from") for d in p012), p012
    assert SP.item_hash(item2) != SP.item_hash(item)


def test_slots_sharing_a_domain_say_whether_a_render_repeated_a_value():
    """
    Ruling 48d. Found on the ruling-48 pilot (2026-10-14): S441-003's judge FAILed
    mat_g1_dp_q3_2's `{p0}, {p1}, {p2}` as able to print one category twice, which no render
    does (each theme has six distinct categories, printed as a prefix). Slots printed under one
    domain say whether any render observed printed one value twice among them; measured here from
    the renders independently of the builder. A render that repeats one must turn it false.
    """
    from backend.app.practice_gen.slots import Trace

    renders, _refused = SP.observe_lc("mat_g1_dp_q3_2")
    item, key = SP.build_item("mat_g1_dp_q3_2", renders)
    fam = next(f for f in item["families"] if f["template"] == "{p0}, {p1}, {p2}")
    group = next(g for g in fam["slots"] if g["slots"] == ["p0", "p1", "p2"])
    assert group["distinct_in_every_render"] is True
    assert key["families"][fam["id"]]["first_render_repeating"] == {}
    seen = [[v for _n, v, _d in f.slots] for _s, _f, _p, fills, _v in renders for f in fills
            if f.template == "{p0}, {p1}, {p2}"]
    assert seen and all(len(set(vals)) == len(vals) for vals in seen)

    i, (seed, fmt, problem, fills, values) = next(
        (i, r) for i, r in enumerate(renders) if any(f.template == "{p0}, {p1}, {p2}" for f in r[3]))
    repeated = Trace()
    for f in fills:
        if f.template == "{p0}, {p1}, {p2}":
            (n0, v0, d0), (n1, _v1, d1), rest = f.slots[0], f.slots[1], f.slots[2:]
            f = dataclasses.replace(f, slots=((n0, v0, d0), (n1, v0, d1)) + tuple(rest))
        repeated.append(f)
    repeated.derivations = fills.derivations
    item2, key2 = SP.build_item("mat_g1_dp_q3_2", renders[:i] + [(seed, fmt, problem, repeated, values)] + renders[i + 1:])
    fam2 = next(f for f in item2["families"] if f["template"] == "{p0}, {p1}, {p2}")
    assert next(g for g in fam2["slots"] if g["slots"] == ["p0", "p1", "p2"])["distinct_in_every_render"] is False
    assert key2["families"][fam2["id"]]["first_render_repeating"] == {"p0,p1,p2": [seed, fmt]}
    assert SP.item_hash(item2) != SP.item_hash(item)
