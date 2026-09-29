"""The hint contract: a hint chain must explain THE ITEM IT WAS SERVED WITH.

WHY THIS EXISTS
---------------
`generate_params` knows an item's parameters; each DNA's `generate_hints`
re-derives them from `values`, and before 2026-09-25 many simply did not. Blind
reviewers across three rater families found the same shape on eight nodes:
add-hints on subtract items, ascending hints on descending sorts, a "shorter"
item whose last hint names the longer length, clock-hand hints on timetable and
day-of-week items, ruler hints on word problems with no ruler, "write the
expanded form" on a set-the-blocks item, and -- the worst -- a calendar chain
that told every Grade 2 pupil "Subtract: 27 - 24 = 4 days". The ANSWERS were
right, so no answer-checking gate could see any of it.

ONE RULE, ONE PLACE
-------------------
`hint_chain_violations` is the only statement of this rule. It is called from
two entry points and they call the SAME function, so the rule cannot drift
between them:

  * `adapter.apply_formatter` -- every served problem (the adapter AND the
    orchestrator route through it) raises `HintContractError` on a violation;
  * `tests/unit/test_hint_contract.py` -- the named gate, run over every node's
    canonical learner-visible judgment packet.

It reads only what the pupil sees (stem, hints, options, visual payload,
interaction mode). It never recomputes an answer: a second copy of a
generator's arithmetic in the harness is a rule that eventually disagrees with
the generator's (this repository has paid for that repeatedly).

DIMENSIONS COVERED -- and, as importantly, NOT covered (Scaling Mandate 6)
--------------------------------------------------------------------------
  arithmetic     Every `a op b [op c ...] = n` a hint asserts must hold, for
                 whole numbers joined by + - x × ÷. NOT covered: fractions,
                 decimals, money with a decimal point, clock times (all excluded
                 by design, because "1/2" and "8:15" are not integer operands),
                 equations written in words ("3 groups of 4 make 12"), and
                 inequalities.
  stated_result  A step that states a result fraction ("... same denominator:
                 3/6") may not disagree with the chain's final "The answer is
                 N/D" line. WORDING-SPECIFIC: only that phrasing is read, which
                 today is the fractions DNA's; a chain worded differently is not
                 covered by this dimension (arithmetic still reads its steps).
  stated_answer  A hint that SAYS what the answer is -- "The answer is N",
                 "Answer: N", "The mass shown is N" -- must name the item's own
                 served answer. Found as a pattern formatter that asked for a
                 different position than the DNA's, whose hints then concluded
                 "The answer is 10" on an item keyed 1 (mat_g1_na_q3_6). And as a
                 scale whose drawn reading was snapped to 30 g while the hint said
                 "The mass shown is 31 g". WORDING-SPECIFIC: only those phrasings
                 are read, and only whole-number or N/D answers are compared. A
                 generic "last number in the chain" rule was measured and rejected:
                 58 findings over the tree, the majority correct hints whose blank
                 is not the total ("Check: 9 + 11 = 20").
  open_equation  Every open equation a hint states ("___ + 11 = 20") must hold
                 when its blank is filled with the item's own served answer. Found
                 as a formatter that moved the blank while the hints kept the
                 DNA's: mat_g1_na_q3_1 served "9 + ? = 20" (answer 11) beside
                 "___ + 11 = 20" -- every closed equation true, the item a
                 different one. A derived step ("1 + ___ = 5" when the answer is
                 4) passes, as it should. NOT covered: an item whose answer is not
                 a whole number (fractions, times, expressions, True/False), an
                 equation with more than one distinct unknown, and parenthesised
                 expressions, which neither this nor `arithmetic` parses.
  operation      A hint may not teach a different operation from the one the
                 stem asks the pupil to perform. Currently recognises explicit
                 ordering stems and addition/subtraction hint instructions.
                 NOT covered: implicit operations, synonyms outside the closed
                 patterns below, or a hint that names no operation at all.
  direction      (a) An ordering hint may not name the opposite direction to the
                 stem's ("least to greatest" on a "largest to smallest" item).
                 (b) A numeric comparison a hint states ("15 is more than 10")
                 must be true. (c) A concluding "The longer/shorter ... is V"
                 must name the right one of the values the chain said it
                 compares. (d) Its polarity must match a "Which ... is
                 shorter?" stem. NOT covered: comparisons between words
                 ("Ana has more than Ben"), or polarity words outside the two
                 lists below.
  unit           A measurement unit a hint names (cm, m, km, mm, g, kg, mL, L,
                 and their long forms) must be named somewhere the pupil can see
                 -- stem, options, or the visual payload. NOT covered: time
                 units (minutes, hours, days, weeks) and currency; a unit
                 visible only in a picture's rendered pixels and not its payload.
  medium         A hint may not tell a pupil to read a clock's hands, a ruler, a
                 calendar, a timetable, a number line, base-10 blocks, a ten
                 frame or a scale that the item does not contain. A medium is
                 PRESENT when the served visual is of a mapped type, or when the
                 stem itself names it. That second arm is a known hole: "A ruler
                 is 15 cm long" names a ruler as an OBJECT and so licenses ruler
                 hints. Only DEFINITE references are read ("the ruler", a
                 clock's hands); an analogy ("like 15 minutes on a clock")
                 passes. Media not in `_MEDIA` are not covered, but every visual
                 schema must be classified as a medium or as unmediated, so a new
                 visual type cannot arrive unclassified.
  response       A set-mode item (the pupil manipulates a visual) may not be told
                 to "Write ..."; a read/answer item may not be told to "Set the
                 / Drag the / Move the" something. Only those imperatives, at the
                 start of a hint sentence, are read -- "Move forward 1 letter each
                 time" is a pattern rule, not an instruction to handle an object.

A hint that is merely UNHELPFUL, or apt for a different item of the same shape,
passes every dimension here; aptness is §5's business. And a chain that states
nothing checkable is skipped, because silence is not contradiction.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "HintContractError",
    "HintGenerationError",
    "DIMENSIONS",
    "MEDIUM_VISUAL_TYPES",
    "UNMEDIATED_VISUAL_TYPES",
    "hint_chain_violations",
    "enforce_hint_contract",
]

DIMENSIONS = ("arithmetic", "stated_result", "stated_answer", "open_equation", "operation", "direction", "unit", "medium", "response")


class HintContractError(ValueError):
    """A served hint chain contradicts the item it was generated for."""


class HintGenerationError(RuntimeError):
    """A DNA's `generate_hints` raised. Typed so a caller can tell it from any other
    generation failure without reading the message (`judgment_packets._try_render`
    records the exception's type name, and the gate fails a node on this type)."""


# ── arithmetic ────────────────────────────────────────────────────────────────
# An operand is a whole number that is not part of a fraction ("1/2"), a clock
# time ("8:15"), a decimal ("5.50") or a longer digit run.
_INT = r"(?<![\d/:.,])\d+(?![\d/:]|[.,]\d)"
_OP = r"\s*([+\-−x×÷])\s*"
_EQUATION_RE = re.compile(rf"({_INT}(?:{_OP}{_INT})+)\s*=\s*({_INT})")
_TOKEN_RE = re.compile(r"\d+|[+\-−x×÷]")


def _evaluate(expression: str) -> Optional[float]:
    """Left-to-right with × ÷ before + -; None when a division is not exact."""
    tokens = _TOKEN_RE.findall(expression)
    terms: List[float] = [float(tokens[0])]
    signs: List[str] = []
    for op, raw in zip(tokens[1::2], tokens[2::2]):
        value = float(raw)
        if op in ("x", "×"):
            terms[-1] *= value
        elif op == "÷":
            if value == 0:
                return None
            terms[-1] /= value
        else:
            signs.append(op)
            terms.append(value)
    total = terms[0]
    for op, value in zip(signs, terms[1:]):
        total = total + value if op == "+" else total - value
    return total


def _arithmetic(hints: Sequence[str]) -> List[str]:
    found = []
    for hint in hints:
        for match in _EQUATION_RE.finditer(hint):
            expression, stated = match.group(1), int(match.group(3))
            value = _evaluate(expression)
            if value is None or value != stated:
                shown = "undefined" if value is None else (
                    int(value) if float(value).is_integer() else round(value, 3))
                found.append(
                    f"asserts {expression.strip()} = {stated}, but {expression.strip()} "
                    f"= {shown} -- in {hint!r}"
                )
    return found


# ── stated result (wording-specific; see module docstring) ───────────────────
_FRACTION = r"[0-9]+/[0-9]+"
_FINAL_FRACTION_RE = re.compile(rf"answer is\s+({_FRACTION})")
_STATED_FRACTION_RE = re.compile(rf"same\s+(?:denominator|bottom number):\s*({_FRACTION})")


def _stated_result(hints: Sequence[str]) -> List[str]:
    if len(hints) < 2:
        return []
    final = _FINAL_FRACTION_RE.search(hints[-1])
    if not final:
        return []
    found = []
    for step in hints[:-1]:
        stated = _STATED_FRACTION_RE.search(step)
        if stated and stated.group(1) != final.group(1):
            found.append(
                f"a step computes {stated.group(1)} but the final hint asserts "
                f"{final.group(1)} -- in {step!r}"
            )
    return found


# ── stated answer (wording-specific; see module docstring) ───────────────────
_STATED_ANSWER_RE = re.compile(
    r"(?:\banswer is|\bAnswer:|\bshown is)\s+(?<![\d/:.])(\d+(?:/\d+)?)(?![\d/:]|[.,]\d)")


def _stated_answer(hints: Sequence[str], answer: Any) -> List[str]:
    if isinstance(answer, bool):
        return []
    if isinstance(answer, (int, float)) and float(answer).is_integer():
        served = str(int(answer))
    elif isinstance(answer, str) and re.fullmatch(r"\d+(?:/\d+)?", answer.strip()):
        served = answer.strip()
    else:
        return []
    found = []
    for hint in hints:
        for stated in _STATED_ANSWER_RE.findall(hint):
            if stated != served:
                found.append(f"says the answer is {stated}, but the item's answer is {served} -- in {hint!r}")
    return found


# ── open equation ────────────────────────────────────────────────────────────
_BLANK = r"(?:\?|_{2,})"
_TERM = rf"(?:(?<![\d/:.])\d+(?![\d/:])|{_BLANK})"
_SIDE = rf"{_TERM}(?:\s*[+\-−x×÷]\s*{_TERM})*"
_OPEN_EQUATION_RE = re.compile(rf"(?<![\d(])({_SIDE})\s*=\s*({_SIDE})(?![\d)])")


def _answer_value(correct_answer: Any, options: Any) -> Any:
    """The served answer's VALUE: the option marked correct, else the answer itself.

    `correct_answer` is an option KEY under some formatters (read_mcq stores "B"),
    so an MCQ is resolved through the option flagged `is_correct` -- the one field
    every option-bearing formatter sets, in the served problem and the packet alike.
    """
    if isinstance(options, list):
        for option in options:
            if isinstance(option, dict) and option.get("is_correct") and "value" in option:
                return option["value"]
    return correct_answer


def _open_equation(hints: Sequence[str], answer: Any) -> List[str]:
    if isinstance(answer, bool) or not isinstance(answer, (int, float)):
        if not (isinstance(answer, str) and answer.strip().isdigit()):
            return []
    filled = str(int(float(answer)))
    found = []
    for hint in hints:
        for match in _OPEN_EQUATION_RE.finditer(hint):
            equation = match.group(0)
            if not re.search(_BLANK, equation):
                continue
            left = _evaluate(re.sub(_BLANK, filled, match.group(1)))
            right = _evaluate(re.sub(_BLANK, filled, match.group(2)))
            if left is None or right is None or left != right:
                found.append(
                    f"states the open equation {equation.strip()!r}, which the item's own "
                    f"answer {filled} does not satisfy -- in {hint!r}")
    return found


# ── operation (wording-specific; see module docstring) ──────────────────────
_ORDER_STEM_RE = re.compile(
    r"\b(?:arrange|order)\b.*\b(?:least|smallest|greatest|largest)\b"
    r"|\bordered from (?:least|smallest|greatest|largest)\b",
    re.I,
)
_ADD_HINT_RE = re.compile(r"\b(?:when adding|add only|adding fractions?)\b", re.I)
_SUBTRACT_HINT_RE = re.compile(r"\b(?:when subtracting|subtract only|subtracting fractions?)\b", re.I)


def _operation(hints: Sequence[str], stem: str) -> List[str]:
    """Catch an explicitly named hint operation that contradicts the stem's task."""
    if not _ORDER_STEM_RE.search(stem):
        return []
    found = []
    for hint in hints:
        named = "addition" if _ADD_HINT_RE.search(hint) else (
            "subtraction" if _SUBTRACT_HINT_RE.search(hint) else None
        )
        if named:
            found.append(
                f"an ordering item is taught as {named} -- in {hint!r}"
            )
    return found


# ── direction ─────────────────────────────────────────────────────────────────
_ASCENDING_RE = re.compile(
    r"least to greatest|smallest to (?:largest|biggest|greatest)|lowest to highest"
    r"|shortest to longest|lightest to heaviest|ascending", re.I)
_DESCENDING_RE = re.compile(
    r"greatest to least|largest to smallest|biggest to smallest|highest to lowest"
    r"|longest to shortest|heaviest to lightest|descending", re.I)

_GREATER = ("more", "greater", "larger", "bigger", "longer", "taller", "heavier",
            "farther", "older", "higher")
_LESSER = ("less", "fewer", "smaller", "shorter", "lighter", "lesser", "nearer",
           "younger", "lower")
_POLARITY = {w: "greater" for w in _GREATER} | {w: "lesser" for w in _LESSER}
_CMP_WORDS = "|".join(_GREATER + _LESSER)
_NUM = r"\d+(?:\.\d+)?"

_CLAIM_RE = re.compile(rf"(?<![\d/:.])({_NUM})\b[^.\d]{{0,30}}?\bis\s+({_CMP_WORDS})\s+than\s+({_NUM})\b", re.I)
_COMPARE_RE = re.compile(rf"\bCompare\s+({_NUM})\b[^.]*?\band\s+({_NUM})\b", re.I)
_CONCLUSION_RE = re.compile(rf"\b(?:The|the)\s+({_CMP_WORDS})\b[^.]{{0,40}}?\bis\s+({_NUM})\b", re.I)
_STEM_QUESTION_RE = re.compile(rf"\bwhich\b[^?]*?\b({_CMP_WORDS})\b", re.I)


def _direction(hints: Sequence[str], stem: str) -> List[str]:
    found = []
    text = " ".join(hints)
    stem_up, stem_down = bool(_ASCENDING_RE.search(stem)), bool(_DESCENDING_RE.search(stem))
    if stem_down and not stem_up and _ASCENDING_RE.search(text):
        found.append(f"the stem orders DESCENDING but a hint orders ascending ({_ASCENDING_RE.search(text).group(0)!r})")
    if stem_up and not stem_down and _DESCENDING_RE.search(text):
        found.append(f"the stem orders ASCENDING but a hint orders descending ({_DESCENDING_RE.search(text).group(0)!r})")

    for hint in hints:
        for a, word, b in _CLAIM_RE.findall(hint):
            a_val, b_val = float(a), float(b)
            polarity = _POLARITY[word.lower()]
            if (polarity == "greater" and not a_val > b_val) or (polarity == "lesser" and not a_val < b_val):
                found.append(f"asserts {a} is {word} than {b}, which is false -- in {hint!r}")

    compared: Optional[Tuple[float, float]] = None
    for hint in hints:
        pair = _COMPARE_RE.search(hint)
        if pair:
            compared = (float(pair.group(1)), float(pair.group(2)))
        conclusion = _CONCLUSION_RE.search(hint)
        if not conclusion:
            continue
        word, value = conclusion.group(1), float(conclusion.group(2))
        polarity = _POLARITY[word.lower()]
        if compared and value in compared and compared[0] != compared[1]:
            right = max(compared) if polarity == "greater" else min(compared)
            if value != right:
                found.append(
                    f"compares {compared[0]:g} and {compared[1]:g} then names {value:g} "
                    f"as the {word} one -- in {hint!r}")
        asked = _STEM_QUESTION_RE.search(stem)
        if asked and _POLARITY[asked.group(1).lower()] != polarity:
            found.append(
                f"the stem asks which is {asked.group(1)} but the hint concludes about "
                f"the {word} one -- in {hint!r}")
    return found


# ── unit ──────────────────────────────────────────────────────────────────────
_UNIT_FORMS = {
    "mm": ("mm", "millimeter", "millimeters", "millimetre", "millimetres"),
    "cm": ("cm", "centimeter", "centimeters", "centimetre", "centimetres"),
    "km": ("km", "kilometer", "kilometers", "kilometre", "kilometres"),
    "m": ("m", "meter", "meters", "metre", "metres"),
    "kg": ("kg", "kilogram", "kilograms"),
    "g": ("g", "gram", "grams"),
    "mL": ("ml", "milliliter", "milliliters", "millilitre", "millilitres"),
    "L": ("l", "liter", "liters", "litre", "litres"),
}
_FORM_TO_UNIT = {form: unit for unit, forms in _UNIT_FORMS.items() for form in forms}
# A unit is only read where it can only be a unit: after a number, or a long
# form anywhere, or an abbreviation in parentheses ("centimeter (cm)").
_UNIT_AFTER_NUMBER_RE = re.compile(
    r"\d\s*(" + "|".join(sorted(_FORM_TO_UNIT, key=len, reverse=True)) + r")(?!\w)", re.I)
_UNIT_LONG_RE = re.compile(
    r"\b(" + "|".join(sorted((f for f in _FORM_TO_UNIT if len(f) > 2), key=len, reverse=True)) + r")\b", re.I)
_UNIT_PAREN_RE = re.compile(r"\((mm|cm|km|m|kg|g|ml|l)\)", re.I)
# "in cm", "in meters", "unit: cm" -- a stem naming the unit it asks for.
_UNIT_ASKED_RE = re.compile(r"\b(?:in|unit[s]?:?)\s+(mm|cm|km|m|kg|g|ml|l)\b", re.I)
# "cm or m?" -- a choice between units; and an option whose whole value is a unit
# (options are flattened to JSON, so it appears as "m" in quotes).
_UNIT_CHOICE_RE = re.compile(r"(?<![\w.])(mm|cm|km|m|kg|g|ml|l)\s+or\s+(?=(?:mm|cm|km|m|kg|g|ml|l)\b)", re.I)
_UNIT_CHOICE_TAIL_RE = re.compile(r"\bor\s+(mm|cm|km|m|kg|g|ml|l)(?![\w.])", re.I)
_UNIT_QUOTED_RE = re.compile(r'"(mm|cm|km|m|kg|g|ml|l)"', re.I)
# A multi-letter abbreviation is unambiguous as a whole word anywhere.
_UNIT_WORD_RE = re.compile(r"(?<![\w.])(mm|cm|km|kg|ml)(?![\w.])", re.I)


def _units_in(text: str) -> set:
    units = set()
    for regex in (_UNIT_AFTER_NUMBER_RE, _UNIT_LONG_RE, _UNIT_PAREN_RE, _UNIT_ASKED_RE,
                  _UNIT_CHOICE_RE, _UNIT_CHOICE_TAIL_RE, _UNIT_QUOTED_RE, _UNIT_WORD_RE):
        for form in regex.findall(text):
            units.add(_FORM_TO_UNIT[form.lower()])
    return units


def _unit(hints: Sequence[str], visible: str) -> List[str]:
    named = _units_in(" ".join(hints))
    shown = _units_in(visible)
    stray = sorted(named - shown)
    if not stray:
        return []
    return [f"a hint names the unit {', '.join(stray)} but the item shows only "
            f"{', '.join(sorted(shown)) or 'no unit'}"]


# ── medium ────────────────────────────────────────────────────────────────────
# medium -> (how a hint refers to it, how a stem can name it, the visual types that ARE it)
# A hint REFERS to a medium only by a definite reference ("the ruler", "on the
# calendar") or by a part that exists only on it (a clock's hands). An indefinite
# mention is an analogy, not an instruction -- "a quarter turn is like 15 minutes
# on a clock" does not tell the pupil to read a clock -- and is not read. That
# is a named hole: an analogy to a medium the item lacks passes.
_MEDIA: Dict[str, Tuple[re.Pattern, re.Pattern, Tuple[str, ...]]] = {
    "clock": (re.compile(r"\bthe clock\b|\b(?:short|long|hour|minute)\s+(?:\((?:hour|minute)\)\s+)?hand\b", re.I),
              re.compile(r"\bclock\b", re.I), ("ClockSet",)),
    "ruler": (re.compile(r"\bthe ruler\b", re.I), re.compile(r"\bruler\b", re.I), ("RulerMeasure",)),
    "calendar": (re.compile(r"\bthe calendar\b", re.I), re.compile(r"\bcalendar\b", re.I), ("Calendar",)),
    "timetable": (re.compile(r"\bthe (?:bus |class )?(?:timetable|schedule)\b", re.I),
                  re.compile(r"\btimetable\b|\bschedule\b", re.I), ("Timetable",)),
    "number_line": (re.compile(r"\bthe number line\b", re.I), re.compile(r"\bnumber line\b", re.I), ("NumberLine",)),
    "blocks": (re.compile(r"\bthe (?:base-10 |base ten )?(?:blocks|rods|flats)\b", re.I),
               re.compile(r"\bblocks?\b", re.I), ("PlaceValueBlocks",)),
    "ten_frame": (re.compile(r"\bthe ten[- ]frame\b", re.I), re.compile(r"\bten[- ]frame\b", re.I), ("TenFrame",)),
    # A bar graph's axis has a scale too ("The scale on the vertical axis goes up by 5").
    "scale": (re.compile(r"\bthe scale\b", re.I), re.compile(r"\bscale\b", re.I),
              ("ScaleRead", "BalanceScale", "BarChart")),
}
MEDIUM_VISUAL_TYPES = {medium: types for medium, (_, _, types) in _MEDIA.items()}
# Every visual schema must be classified: either it IS one of the media above, or
# it is named here as carrying no hint vocabulary this contract reads. The gate
# fails on an unclassified schema, so a new visual cannot slip in uncovered.
UNMEDIATED_VISUAL_TYPES = (
    "EmojiPictorial", "FillInTable", "FractionModel",
    "FractionShade", "GeometryFigure", "GridArea", "NumberBond", "PatternSequence",
    "PesoMoney", "Pictograph", "ShapeBoard",
)


def _medium(hints: Sequence[str], stem: str, visual_type: Optional[str]) -> List[str]:
    found = []
    for medium, (in_hint, in_stem, types) in _MEDIA.items():
        referenced = next((h for h in hints if in_hint.search(h)), None)
        if referenced is None:
            continue
        if visual_type in types or in_stem.search(stem):
            continue
        found.append(
            f"a hint refers to a {medium.replace('_', ' ')} the item does not contain "
            f"(visual: {visual_type or 'none'}) -- in {referenced!r}")
    return found


# ── response ──────────────────────────────────────────────────────────────────
_SENTENCE_START = r"(?:^|[.!?]\s+)"
_WRITE_RE = re.compile(_SENTENCE_START + r"Write\b")
_MANIPULATE_RE = re.compile(_SENTENCE_START + r"(?:Set|Drag|Move) the\b")


def _response(hints: Sequence[str], interaction_mode: Optional[str]) -> List[str]:
    found = []
    for hint in hints:
        if interaction_mode == "set" and _WRITE_RE.search(hint):
            found.append(f"a set-mode item (the pupil manipulates the visual) is told to write -- in {hint!r}")
        if interaction_mode != "set" and _MANIPULATE_RE.search(hint):
            found.append(f"an answer item with nothing to manipulate is told to set/drag/move -- in {hint!r}")
    return found


# ── entry points ──────────────────────────────────────────────────────────────

def _flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


def hint_chain_violations(
    *,
    hints: Sequence[str],
    stem: str,
    options: Any = None,
    visual_type: Optional[str] = None,
    visual_payload: Any = None,
    interaction_mode: Optional[str] = None,
    correct_answer: Any = None,
) -> List[Tuple[str, str]]:
    """Every (dimension, message) on which `hints` contradict the item they serve."""
    hints = [h for h in (hints or []) if isinstance(h, str)]
    if not hints:
        return []
    visible = " ".join((stem or "", _flatten(options), _flatten(visual_payload)))
    out: List[Tuple[str, str]] = []
    out += [("arithmetic", m) for m in _arithmetic(hints)]
    out += [("stated_result", m) for m in _stated_result(hints)]
    answer = _answer_value(correct_answer, options)
    out += [("stated_answer", m) for m in _stated_answer(hints, answer)]
    out += [("open_equation", m) for m in _open_equation(hints, answer)]
    out += [("operation", m) for m in _operation(hints, stem or "")]
    out += [("direction", m) for m in _direction(hints, stem or "")]
    out += [("unit", m) for m in _unit(hints, visible)]
    out += [("medium", m) for m in _medium(hints, stem or "", visual_type)]
    out += [("response", m) for m in _response(hints, interaction_mode)]
    return out


def enforce_hint_contract(problem: Any, formatter_name: str) -> None:
    """Raise on a served problem whose hints contradict it. Called by `apply_formatter`."""
    format_data = getattr(problem, "format_data", None) or {}
    violations = hint_chain_violations(
        hints=problem.hints,
        stem=problem.question_text,
        options=format_data.get("options") or format_data.get("mcq_options"),
        visual_type=problem.visual_type if problem.is_visual else None,
        visual_payload=problem.visual_params if problem.is_visual else None,
        interaction_mode=problem.interaction_mode,
        correct_answer=problem.correct_answer,
    )
    if violations:
        raise HintContractError(
            f"hint contract violated for node={problem.node_id} seed={problem.seed} "
            f"formatter={formatter_name}: "
            + "; ".join(f"[{d}] {m}" for d, m in violations)
            + f" | stem={problem.question_text!r} hints={problem.hints!r}"
        )
