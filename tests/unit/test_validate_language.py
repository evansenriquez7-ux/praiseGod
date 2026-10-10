"""
§1J's mirror direction (singular-after-many, batch H5): what it judges and what it must not.

Each case is a shape measured on the live tree on 2026-10-10. The lexicon is the generator's
own (`validate_language.singular_count_nouns`), so these tests also fail if the interest bank
or the unit table stops declaring a noun the gate was proven on.
"""
import pytest

from backend.app.practice_gen.validation import validate_language as VL


@pytest.fixture(scope="module")
def lexicon():
    return VL.singular_count_nouns()


@pytest.mark.parametrize("text, written", [
    # mat_g3_na_q2_3 seed 500: the add_join spine puts a count before {item1}/{item2}.
    ("Lola Caring collected 828 cat toy and 6321 water bowl at the veterinary clinic.",
     ["cat toy", "water bowl"]),
    # length hints: VocabGated "centimeter (cm)" after a count.
    ("Compare 20 centimeter (cm) and 6 centimeter (cm).", ["centimeter", "centimeter"]),
    ("It is 5 meter (m).", ["meter"]),
    ("2 water bottle", ["water bottle"]),
])
def test_declared_singular_after_many_is_a_finding(lexicon, text, written):
    found, _ = VL.scan_singular_after_many(text, lexicon)
    assert [w for _, w, _ in found] == written


@pytest.mark.parametrize("text", [
    "She has 3 cat toys.",                # the plural continues the singular entry
    "There are 3 cat toy boxes.",         # open compound: head is 'boxes'
    "Aling Rosa has 7 running shoes.",    # bank lists it under item1 already plural
    "Sir Ben has 2 crayons.",
    "16 milk tea cups.",                  # not a declared phrase; counted, not judged
    "161 fish food packets.",
    "There are 3 fish.",                  # 'fish' is its own plural in the bank
    "Grade 3 cat toy.",                   # a label numeral
    "5 meters (m) long",
    "1 cat toy",                          # count of one is the other direction's
    "a 9 by 9 array.",
])
def test_correct_or_undecidable_text_is_not_a_finding(lexicon, text):
    found, _ = VL.scan_singular_after_many(text, lexicon)
    assert found == []


def test_lexicon_is_read_from_the_generator_inventories(lexicon):
    from backend.app.practice_gen.generators import interest
    assert "cat toy" in lexicon and "interest bank" in lexicon["cat toy"]
    assert "centimeter" in lexicon and "_UNIT_FORMS" in lexicon["centimeter"]
    assert "fish" not in lexicon
    # every bank noun is represented by its singular, whatever slot it sits in
    from backend.app.practice_gen.dna.base import to_singular_phrase
    for data in interest._INTERESTS.values():
        for slot in ("objects", "item1", "item2"):
            for value in data.get(slot, []):
                s = to_singular_phrase(value.lower())
                assert s in lexicon or s == value.lower(), (slot, value)
