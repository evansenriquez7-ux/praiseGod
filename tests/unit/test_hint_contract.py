"""The hint contract, gated across EVERY node: a hint chain explains the item it serves.

This replaces `tests/unit/test_fraction_hint_consistency.py`, which gated one
dimension (a stated intermediate against the final line) on one DNA (fractions).
The defect class it caught was never fractions-specific. By 2026-09-25 blind
reviewers across three rater families had found it on eight nodes, and running
this gate over the tree found it on many more -- calendar hints asserting
"27 - 24 = 4", division hints asserting "82 ÷ 2 = 0", multiplication hints
asserting "5 × 6 = 6", ascending hints on descending sorts, clock-hand hints on
timetables, ruler hints with no ruler, formatters that moved an item's blank while
its hints kept the DNA's. The answers were right, so no answer-checking gate saw
any of it.

WHAT IS GATED, AND WHERE THE RULE LIVES
--------------------------------------
The rule is `backend.app.practice_gen.hint_contract.hint_chain_violations` -- ONE
function, called by this gate and by `adapter.apply_formatter` on every served
problem (so a violating item raises `HintContractError` in production too). This
file never restates the rule; it only calls it. Its dimensions, and what each does
NOT cover, are listed in that module's docstring and in `docs/pgen_contract.md`.

WHAT THIS GATE SEES
-------------------
Every node's canonical judgment-packet seeds, rendered on the student path by the
same `_render_sample` `build_packet` uses -- without the frontend description step,
which the contract does not read (0.6 s a node instead of 2.9 s). A seed outside
that set is covered only by the serving-path enforcement, which runs wherever a
problem is generated: validate_matrix's exhaustive sweep, the obligation executor,
and production.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
1. A hint that is merely UNHELPFUL, or right for a different item of the same
   shape with every statement true, passes. Aptness is §5's business.
2. Every dimension reads English phrasing. A DNA that words a claim in a way the
   contract does not parse is not covered on that claim; the module docstring names
   the phrasings each dimension reads.
3. A chain that states nothing checkable is skipped -- silence is not contradiction.
"""
from __future__ import annotations

import importlib

import pytest

from backend.app.practice_gen import hint_contract as hc
from backend.app.practice_gen.registry import get_all_node_ids
from backend.app.practice_gen.schemas.visuals import VisualSchemaRegistry
from backend.app.practice_gen.validation import judgment_packets as jp

_NODES = sorted(get_all_node_ids())


def _dimensions(**item):
    return [d for d, _ in hc.hint_chain_violations(**item)]


# ── the detector, proven on its motivating cases before it is trusted ────────

# (dimension, the defect verbatim from the evidence, the repaired chain).
# A detector that cannot catch its own motivating case is decoration.
_MOTIVATING = [
    ("arithmetic",
     dict(hints=["Count the days between 24 and 27 on the calendar.", "Subtract: 27 - 24 = 4 days."],
          stem="How many days are there from January 24 to January 27, inclusive?",
          visual_type="Calendar", correct_answer=4),
     dict(hints=["Find 24 and 27 on the calendar. Count both of those days too.", "27 - 24 + 1 = 4 days."],
          stem="How many days are there from January 24 to January 27, inclusive?",
          visual_type="Calendar", correct_answer=4)),
    ("stated_result",
     dict(hints=["When adding fractions with the same denominator, keep the denominator the same.",
                 "Add only the numerators: 2 + 1 = 3.",
                 "Write the result over the same denominator: 3/6.", "The answer is 1/6."],
          stem="What is 2/6 - 1/6?"),
     dict(hints=["When subtracting fractions with the same denominator, keep the denominator the same.",
                 "Subtract only the numerators: 2 - 1 = 1.",
                 "Put the result over the same denominator: 1/6.", "The answer is 1/6."],
          stem="What is 2/6 - 1/6?")),
    ("stated_answer",
     dict(hints=["Look at the pattern: [10, 1, 10, 1, 10, 1].",
                 "The what it does is: Repeat the group: 10, 1. The answer is 10."],
          stem="What is the missing piece (position 6) in the pattern?",
          options=[{"key": "C", "value": 10, "is_correct": False}, {"key": "D", "value": 1, "is_correct": True}],
          correct_answer="D"),
     dict(hints=["Look at the pattern: 10, 1, 10, 1, 10, 1, ___.", "Repeat the group: 10, 1. The answer is 10."],
          stem="What is the missing piece (position 7) in the pattern?",
          options=[{"key": "C", "value": 10, "is_correct": True}, {"key": "D", "value": 1, "is_correct": False}],
          correct_answer="C")),
    ("open_equation",
     dict(hints=["The number statement is: ___ + 11 = 20", "Use subtraction to undo the operation.",
                 "20 − 11 = 9.", "Check: 9 + 11 = 20. ✓"],
          stem="Both sides balance evenly. 9 + ? = 20. What is the missing value?",
          options=[{"key": "D", "value": 11, "is_correct": True}], correct_answer="D"),
     dict(hints=["The number statement is: ___ + 11 = 20", "Use subtraction to undo the operation.",
                 "20 − 11 = 9.", "Check: 9 + 11 = 20. ✓"],
          stem="Both sides balance evenly. ? + 11 = 20. What is the missing value?",
          options=[{"key": "D", "value": 9, "is_correct": True}], correct_answer="D")),
    ("operation",
     dict(hints=["When adding fractions with the same denominator, keep the denominator the same.",
                 "Add only the numerators: 1 + 0 = 1."],
          stem="Arrange these fractions from least to greatest: 1/4, 3/4, 2/4."),
     dict(hints=["Read the requested order: smallest to largest.",
                 "For equal bottom numbers, compare the top numbers."],
          stem="Arrange these fractions from least to greatest: 1/4, 3/4, 2/4.")),
    ("remainder",
     dict(hints=["We need to divide 51 by 8.",
                 "Ask: how many times does 8 fit into 51? 8 × 6 R 3 = 6 R 36 R 36 R 36 R 3.",
                 "The quotient is 6 R 3 remainder 3 (written as 6 R 3 R3)."],
          stem="51 ÷ 8 = 7 R 3. True or False?"),
     dict(hints=["We need to divide 51 by 8.",
                 "Ask: how many times does 8 fit into 51? 8 × 6 = 48.",
                 "The quotient is 6 remainder 3 (written as 6 R 3)."],
          stem="51 ÷ 8 = 7 R 3. True or False?")),
    ("roles",
     dict(hints=["We need to find the total of equal groups 5 groups of 2.",
                 "Think of it as 2 groups of 5: 5 + 5.", "The product of 5 × 2 = 10."],
          stem="Starting at 0, taking 2 equal jumps of 5 on the number line lands on ___"),
     dict(hints=["We need to find the total of equal groups 2 groups of 5.",
                 "Think of it as 2 groups of 5: 5 + 5.", "The product of 5 × 2 = 10."],
          stem="Starting at 0, taking 2 equal jumps of 5 on the number line lands on ___")),
    ("direction",
     dict(hints=["Numbers to order: [29, 61, 62].", "Find the smallest number first, then the next smallest.",
                 "Ordered from least to greatest: [29, 61, 62]."],
          stem="Arrange these numbers from largest to smallest: 61, 62, 29"),
     dict(hints=["Numbers to order: 29, 61, 62.", "Find the largest number first, then the next largest.",
                 "Ordered from greatest to least: 62, 61, 29."],
          stem="Arrange these numbers from largest to smallest: 61, 62, 29")),
    ("direction",
     dict(hints=["Compare 10 centimeter (cm) and 15 centimeter (cm).", "15 is more than 10.",
                 "The longer length is 10 centimeter (cm)."],
          stem="A pencil is 10 cm long. A ruler is 15 cm long. Which length is shorter in cm?"),
     dict(hints=["Compare 10 centimeter (cm) and 15 centimeter (cm).", "15 is more than 10.",
                 "The shorter length is 10 centimeter (cm)."],
          stem="A pencil is 10 cm long. A ruler is 15 cm long. Which length is shorter in cm?")),
    ("unit",
     dict(hints=["Compare 2 centimeter (cm) and 1 centimeter (cm).", "2 is more than 1.",
                 "The longer distance is 2 centimeter (cm)."],
          stem="The distance from the bench to the tree is 2 m. The distance from the gate to the tree "
               "is 1 m. Which distance is longer in meters?"),
     dict(hints=["Compare 2 meter (m) and 1 meter (m).", "2 is more than 1.",
                 "The longer distance is 2 meter (m)."],
          stem="The distance from the bench to the tree is 2 m. The distance from the gate to the tree "
               "is 1 m. Which distance is longer in meters?")),
    ("medium",
     dict(hints=["The short hand shows the hour. The long hand shows the minutes.",
                 "The short (hour) hand points near 8.", "The time shown is 8:00 a.m.."],
          stem="Look at the class schedule. How many minutes long is the English class?",
          visual_type="Timetable"),
     dict(hints=["Find the row for English in the class schedule.",
                 "It starts at 9:00 a.m. and ends at 9:45 a.m.",
                 "Count on from the start time to the end time: that is 45 minutes."],
          stem="Look at the class schedule. How many minutes long is the English class?",
          visual_type="Timetable")),
    ("response",
     dict(hints=["Write the broken apart form of 10.", "Break each digit into its place value: 10 + 0."],
          stem="Use base-10 blocks to show the number 10.", visual_type="PlaceValueBlocks",
          interaction_mode="set"),
     dict(hints=["Break 10 into parts by place value: 10 + 0.", "10 is 1 ten and 0 ones."],
          stem="Use base-10 blocks to show the number 10.", visual_type="PlaceValueBlocks",
          interaction_mode="set")),
]


@pytest.mark.parametrize("dimension,defect,repaired", _MOTIVATING,
                         ids=[f"{d}-{i}" for i, (d, _, _) in enumerate(_MOTIVATING)])
def test_each_dimension_catches_its_motivating_case(dimension, defect, repaired):
    assert dimension in _dimensions(**defect), (
        f"the {dimension} dimension missed the defect it exists for: {hc.hint_chain_violations(**defect)}")
    assert _dimensions(**repaired) == [], (
        f"the repaired chain is flagged: {hc.hint_chain_violations(**repaired)}")


def test_every_dimension_has_a_motivating_case():
    """A dimension added to the contract without a proven case is unproven."""
    assert set(hc.DIMENSIONS) == {d for d, _, _ in _MOTIVATING}


def test_every_visual_schema_is_classified():
    """A new visual type must be declared a medium or unmediated -- never neither.

    An allowlist that names its members stops covering new ones silently; this is
    the direction that fails on an unclassified schema.
    """
    mediated = {t for types in hc.MEDIUM_VISUAL_TYPES.values() for t in types}
    classified = mediated | set(hc.UNMEDIATED_VISUAL_TYPES)
    schemas = set(VisualSchemaRegistry.SCHEMAS)
    assert schemas - classified == set(), f"unclassified visual schemas: {sorted(schemas - classified)}"
    assert classified - schemas == set(), f"classified names that are not schemas: {sorted(classified - schemas)}"
    assert mediated & set(hc.UNMEDIATED_VISUAL_TYPES) == set()


# ── the class, gated over every node ─────────────────────────────────────────

_HINT_FAILURE_TYPES = (hc.HintContractError.__name__, hc.HintGenerationError.__name__)


@pytest.mark.parametrize("node_id", _NODES)
def test_no_served_hint_contradicts_its_item(node_id):
    offenders = []
    seeds = jp._stratified_seeds(node_id)
    # Stratification trial-renders candidate seeds and SKIPS any that raise, recording
    # them in `render_failures`. A seed the contract refused therefore never reaches
    # the loop below -- found 2026-09-25 when a planted "Write" on a set-the-blocks item
    # SURVIVED: every set-mode seed was refused, dropped from the packet, and the
    # remaining read-mode seeds passed. The recorder writes `type(exc).__name__` first,
    # so the refusal is identified by its exception TYPE, never by message text.
    for seed, message in jp.render_failures(node_id):
        if message.split(":", 1)[0] in _HINT_FAILURE_TYPES:
            offenders.append(f"stratification dropped seed {seed}: {message}")
    for seed in seeds:
        try:
            sample = jp._render_sample(node_id, seed)
        except hc.HintContractError as exc:
            offenders.append(f"served path refused seed {seed}: {exc}")
            continue
        found = hc.hint_chain_violations(
            hints=sample.get("hints"),
            stem=sample.get("question_text") or "",
            options=sample.get("options"),
            visual_type=sample.get("visual_type"),
            visual_payload=sample.get("visual_payload"),
            interaction_mode=(sample.get("effective") or {}).get("interaction_mode"),
            correct_answer=sample.get("correct_answer"),
        )
        offenders += [f"seed {seed} ({sample.get('formatter')}): [{d}] {m}" for d, m in found]
    assert not offenders, (
        f"{node_id}: {len(offenders)} hint chain(s) contradict the item they serve.\n  "
        + "\n  ".join(offenders[:6])
    )


# ── the two properties that make the rule bind in production ─────────────────

_BAD_CALENDAR_CHAIN = ["Subtract: 27 - 24 = 4 days."]


def test_serving_path_enforces_the_contract(monkeypatch):
    """`apply_formatter` must refuse a contradicting chain, on the orchestrator path
    the packet uses. Without this the gate would be a report, not a contract."""
    calendar = importlib.import_module("backend.app.practice_gen.dna.mg.calendar")
    monkeypatch.setattr(calendar, "generate_hints", lambda values, vocab: list(_BAD_CALENDAR_CHAIN))
    with pytest.raises(hc.HintContractError, match=r"\[arithmetic\]"):
        jp._render_sample("mat_g2_mg_q4_0", 42)


def test_hint_generation_failure_is_loud(monkeypatch):
    """A hint builder that raises must fail the item by name, never ship it hintless.

    `base_generator` swallowed every such exception until 2026-09-25, which hid five
    hint builders reading keys their own task types never set.
    """
    calendar = importlib.import_module("backend.app.practice_gen.dna.mg.calendar")

    def _broken(values, vocab):
        raise KeyError("planted_missing_key")

    monkeypatch.setattr(calendar, "generate_hints", _broken)
    with pytest.raises(RuntimeError, match=r"calendar\.generate_hints failed .*seed=42.*planted_missing_key"):
        jp._render_sample("mat_g2_mg_q4_0", 42)


# ── an answer-key defect the contract's own guard surfaced ───────────────────

@pytest.mark.parametrize("task_type", ["commutative", "associative", "distributive"])
def test_a_property_statement_keyed_false_is_false(task_type):
    """A property item keyed False must state something false, and vice versa.

    Found 2026-09-25 when multiplication's hint chain began working out both sides:
    at a small `max_product` the "different" factor could equal the original, so
    "Is (a × b) × 2 the same as a × (b × 2)?" was keyed False. The oracle is the hint
    builder's own check (it raises when the sides and the key disagree), so the
    arithmetic is not restated here. Small ceilings are swept because that is where
    the range for a second factor collapses.
    """
    multiplication = importlib.import_module("backend.app.practice_gen.dna.na.multiplication")
    for max_product in (10, 12, 16, 20, 30, 50, 90):
        for seed in range(120):
            values = multiplication.generate_params(3, {"task_type": task_type, "max_product": max_product}, seed)
            multiplication.generate_hints(values, set())


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [(23, 8, "11 ones is 1 ten and 1 one."),
     (27, 5, "12 ones is 1 ten and 2 ones.")],
)
def test_addition_non_regrouping_hint_inflects_ones(a, b, expected):
    """The place-value explanation agrees with its own remainder count."""
    addition = importlib.import_module("backend.app.practice_gen.dna.na.addition")
    hints = addition.generate_hints(
        {"task_type": "putting_together", "a": a, "b": b, "result": a + b},
        {"ones", "tens"},
    )
    assert any(expected in hint for hint in hints), hints
