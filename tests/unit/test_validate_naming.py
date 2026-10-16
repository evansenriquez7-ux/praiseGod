"""
Ruling 52: every content finding names its lc (or route), a witness seed or the ruled
substitute, and an owed build; and every one is printed (ruling 23).

Catching side of the mutations in tests/mutation_harness.py:

  content_finding_seed_stripped      -> test_a_real_1J_finding_is_named (strips the seed
                                        from §1J's mirror finding, the stage's real site)
  content_naming_left_out_of_verdict -> test_an_unnamed_content_finding_fails_integrity
  content_naming_accepts_truncation  -> test_a_truncated_or_empty_block_is_a_problem
"""
from __future__ import annotations

from backend.app.practice_gen.validation import run_all as ra
from backend.app.practice_gen.validation import validate_naming as VN

from tests.unit.test_stage_ledger import stubbed_harness  # noqa: F401  (pytest fixture)

LCS = {"mat_g1_na_q1_0"}
ROUTES = {"mcq"}


def test_a_named_finding_passes_and_each_missing_part_is_named():
    good = "mat_g1_na_q1_0: seed 4 hint quotes '47'. Owed: render the run."
    assert VN.finding_problems(good, LCS, ROUTES) == []
    assert VN.finding_problems(f"mat_g1_na_q1_0: x; {VN.SUBSTITUTE}: no render. Owed: y.", LCS, ROUTES) == []
    assert VN.finding_problems("route 'mcq': unreachable; ruled substitute (ruling 52): no lc. Owed: z.",
                               LCS, ROUTES) == []
    assert len(VN.finding_problems("mat_g1_na_q1_0: hint quotes '47'. Owed: x.", LCS, ROUTES)) == 1
    assert len(VN.finding_problems("mat_g1_na_q1_0: seed 4 hint quotes '47'.", LCS, ROUTES)) == 1
    assert len(VN.finding_problems("mat_g9_xx_q1_0: seed 4. Owed: x.", LCS, ROUTES)) == 1, \
        "an unregistered lc is not an lc"


def test_a_truncated_or_empty_block_is_a_problem():
    text = ("  FAIL count_noun_singular_after_many_1J (3):\n"
            "    - mat_g1_na_q1_0: seed 2 writes '4 apple'. Owed: inflect it.\n"
            "    ... and 2 more.\n"
            "  FAIL slot_domain_escape_14 (1):\n"
            "  FAIL stage_crashed_x (1):\n"
            "    - not a content block: never read\n")
    problems = VN.problems_in_output(text, "s", lcs=LCS, routes=ROUTES)
    assert any("cut short" in p for p in problems), problems
    assert any("lists no finding" in p for p in problems), problems
    assert len(problems) == 2, problems


def test_matrix_owed_table_covers_every_content_family_exactly():
    from backend.app.practice_gen.validation import validate_coverage, validate_matrix
    from backend.app.practice_gen.validation._manifest import CONTENT, FINDING_CLASS

    families = {f for f in validate_coverage.matrix_assertion_labels() if FINDING_CLASS.get(f) == CONTENT}
    assert set(validate_matrix.OWED_BY_CHECK) == families


def test_a_real_1J_finding_is_named():
    """The real §1J site on an lc that prints singular-after-many (measured: seed 2)."""
    from backend.app.practice_gen.validation import validate_language

    _f, _stats, _unclassified, mirror = validate_language.collect_findings(["mat_g2_na_q2_2"])
    assert mirror, "control: mat_g2_na_q2_2 prints a singular count noun after many"
    lcs = VN._known_lcs()
    for finding in mirror:
        assert VN.finding_problems(finding, lcs, set()) == [], finding


def test_an_unnamed_content_finding_fails_integrity(stubbed_harness, capsys):
    def unnamed(**kw):
        print("  FAIL count_noun_singular_after_many_1J (1):")
        print("    - mat_g1_na_q1_0: writes '4 apple' with no seed and nothing owed")
        return False

    stubbed_harness.setattr(ra.validate_language, "validate_all", unnamed)
    assert ra.run_all(phase=1) == 1
    out = capsys.readouterr().out
    assert "FAIL content_finding_named" in out
    assert "content_finding_named: stage 'count_noun_1J'" in out


def test_a_named_content_finding_exits_2(stubbed_harness, capsys):
    def named(**kw):
        print("  FAIL count_noun_singular_after_many_1J (1):")
        print("    - mat_g1_na_q1_0: seed 2 writes '4 apple'. Owed: inflect it.")
        return False

    stubbed_harness.setattr(ra.validate_language, "validate_all", named)
    assert ra.run_all(phase=1) == 2
    assert "PASS content_finding_named" in capsys.readouterr().out
