"""
§1J — count/noun agreement in the text a pupil actually reads.

WHAT THIS CHECKS, EXACTLY
-------------------------
One bounded, mechanical property: where rendered student-facing text writes an explicit
count followed by a count noun, the noun's number agrees with the count. "jump back 1
units", "move back 1 steps", "Taking away 1 cookies" — three stems that were being served
on 2026-09-12, each grammatically wrong in a way a six-year-old reader is entitled not to
meet in a maths question.

It is NOT a test of age-appropriate language. Vocabulary and concept gating is §1D's, and
reading load and register belong to the judgment reviews. This lint is two sentences wide
and says so in its contract row.

WHY THE RULE IS IMPORTED AND NOT RESTATED
-----------------------------------------
`Spine.render` already singularises "1 <plural>" while filling a template. The three
defects above all come from text a formatter composed ITSELF — an error-detect item
quoting a worked solution, a number-line stem naming a jump — which never passes through
that path. So the pipeline's rule was right and its reach was short.

This module therefore imports `dna.base.to_singular_phrase`, the generator's own
inflection, and applies it to the FINAL rendered text. A second implementation of the
rule would drift from the first and then the harness and the generator would disagree
about what correct English is, with no way to tell which was right.

DOMAIN, AND THE COUNTER-EXAMPLES IT MUST NOT FLAG (Mandate 6)
-------------------------------------------------------------
A "count" is a run of digits that is not part of a larger literal: `₱5`, `1.5`, `3/4` and
the `1` in `₱1 coins` are denominations and numerals, not counts, and a count noun after
them refers to the quantity in front, not to the digits. All four are excluded by the
count pattern, and `5 ₱1 coins` — the shape that made a naive regex report a false
positive on two money nodes — is correct English that this lint must pass.

The word after a count is judged only when it is a plausible count noun:

  * `_LABEL_PRECEDERS` — a closed set of words after which a numeral NAMES something
    rather than counting it. "If each item for Grade 1 costs ₱10" is not a count of one
    cost; it is grade one, and `costs` is a verb. The word before the numeral is the only
    thing that distinguishes the two, so the pattern captures it.
  * `_FUNCTION_WORDS` — a closed set of copulas, operators and determiners that can
    legitimately follow a numeral ("1 is 1 one", "1 plus 2", "1 less", "1 more"). These
    are never nouns, and several of them end in `s`, which is why a bare
    `endswith("s")` test reports them.
  * Unit ABBREVIATIONS (`m`, `cm`, `kg`, `L`, `mg`) are invariant in written maths — "18
    L", "1 L" — and are left alone by the inflection rule anyway, which is why they need
    no special case here beyond not being plural-looking.
  * Anything else the inflection rule reports as already-singular is left alone. An
    unknown noun is NOT silently classified as correct: it is counted and reported in the
    run summary as unclassified, so the size of the blind spot is a number and not a
    shrug.

THE MIRROR DIRECTION: SINGULAR-AFTER-MANY (batch H5, 2026-10-10)
----------------------------------------------------------------
"828 cat toy and 6321 water bowl" (mat_g3_na_q2_3 seed 500) and "5 meter (m)" (length
hints) are the mirror defect: a singular noun after a count of two or more. The next token
alone cannot decide it -- "16 milk tea cups", "4 square tiles", "a 9 by 9 array" all put a
singular-looking word after a count and are correct -- so the gate does not guess at the
head of a noun phrase. It asks the GENERATOR which phrases are count nouns and in which
number, and judges only those (`count_noun_singular_after_many_1J`):

  * The lexicon is read from the generator's own inventories, never restated: every noun
    in `generators.interest._INTERESTS` and `NEUTRAL_SLOTS` (`objects`, `item1`, `item2`),
    each reduced to its singular by `to_singular_phrase` -- the slots are not uniformly
    singular ("cat toy" sits beside "running shoes") -- plus the long unit names in
    `hint_contract._UNIT_FORMS` whose plural differs. A word the bank lists in `objects`
    that the rule leaves unchanged is its own plural ("fish") and is never judged.
  * The phrase must be the LONGEST lexicon entry the text continues with, and must end at
    a word boundary: "3 cat toys" continues "cat toy" with an "s", so it is the plural and
    passes.
  * The phrase must be CLOSED -- followed by punctuation, the end of the text, or a
    `_FUNCTION_WORDS` word ("and", "at"). "3 cat toy boxes" is a compound whose head is
    "boxes" and is not judged.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
1. **The mirror direction is gated only on the generator's declared count nouns.** A noun
   outside the interest bank and the unit table (a DNA-local noun list, a formatter's own
   nouns such as `fmt_emoji_pictorial._EMOJI_NAMES`) is MEASURED and printed as
   "observed and NOT judged", never gated; so is an open compound ("3 cat toy boxes").
   Measured 2026-10-10 over seeds 1-60: 7,129 singular-after-many shapes, of which the
   lexicon judges the closed ones. A grade-7 noun is judged as soon as the bank or unit
   table declares it; a noun that lives only in a DNA is not, until H3's slots record its
   domain.
2. It reads the rendered strings, not the visual payload. A picture whose label
   disagrees with its own count is §1G's and §9's territory, not this module's.
3. Agreement between a count and a VERB ("There are 1 apple") is handled by
   `Spine.render`'s copula rules for templated text and is not checked here at all.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[4]

# §8 inventory: the assertions this module can independently fail on.
ASSERTIONS = (
    "count_noun_agreement_1J",
    # The reach direction, added 2026-09-21: a string-bearing payload field this module
    # neither lints nor deliberately excludes. Its own label rather than a count/noun
    # finding, because the two take different fixes -- one is a defect in the text, the
    # other is a defect in this check's coverage, and reporting both under one label is
    # how a coverage hole gets closed by fixing a stem.
    "unclassified_pupil_text_1J",
    # The mirror direction (batch H5, 2026-10-10): a count of two or more before a phrase
    # the generator's own noun inventory declares singular. Its own label because it reads
    # a different source of truth (the inventory, not the inflection rule) and has its own
    # named limit.
    "count_noun_singular_after_many_1J",
    # Owner ruling 40 (2026-10-11): an indefinite article that disagrees with the sound of
    # the word after it ("A art fair"), judged by the generator's own rule
    # (`dna.base.indefinite_article`), never a second copy of it.
    "indefinite_article_1J",
)

# Seeds 1..60 on every node: 9060 student-path samples, measured at ~65s for the whole
# tree. Chosen against the defects this gate was built on rather than for round numbers --
# the ten stratified seeds the packet builder uses would have MISSED `Shade 1 groups of 1
# squares` entirely, which lands on seeds 12 and 40 of `mat_g2_na_q3_0`. A cheap check
# that samples too thinly is a gate that reports green about seeds it never rendered.
SEEDS_PER_NODE: Tuple[int, ...] = tuple(range(1, 61))

# A count: digits not preceded by another digit, a decimal point, a slash, or a currency
# symbol. `₱1 coins`, `1.5 m`, `3/4 of` are excluded by construction -- see the docstring.
# The optional leading word is captured so a LABEL numeral can be told from a count.
_COUNT_NOUN = re.compile(r"(?<![\d.,/₱$])\b(?:([A-Za-z][A-Za-z\-']*)\s+)?(\d+)\s+([A-Za-z][A-Za-z\-']*)")

# Words that turn the numeral after them into a LABEL, not a count. "Grade 1 costs ₱10"
# names a grade and uses `costs` as a verb; "Step 3 shows" names a step. Explicit and
# extensible by adding a word, never by loosening the pattern -- a numeral-as-identifier
# is a naming convention, and a grade-7 node will bring more of them (Mandate 4).
_LABEL_PRECEDERS = frozenset({
    "grade", "level", "page", "set", "row", "column", "day", "week", "month", "year",
    "step", "question", "item", "number", "no", "figure", "shape", "group", "team",
    "box", "bag", "jar", "shelf", "table", "chart", "graph", "line", "part", "section",
})

# Words that can follow a numeral and are not count nouns. Closed, explicit, and extended
# by adding a word here -- never by loosening the pattern. Several end in `s`, which is
# the whole reason this set exists.
_FUNCTION_WORDS = frozenset({
    "is", "was", "are", "were", "has", "have", "had", "does", "do", "did",
    "plus", "minus", "times", "less", "more", "fewer", "and", "or", "of", "in",
    "on", "at", "to", "from", "the", "a", "an", "this", "that", "these", "those",
    "each", "every", "all", "both", "than", "then", "as", "so", "if", "but",
    "it", "its", "his", "her", "their", "them", "they", "he", "she", "we", "you",
    "left", "right", "up", "down", "out", "away", "back", "over", "under",
    "red", "blue", "green", "yellow", "orange", "purple", "black", "white", "brown",
    "shaded", "unshaded", "equal", "same", "different", "whole", "half",
    # Added 2026-09-21, when linting `hints` for the first time surfaced them as false
    # positives. Both are here because neither can be a count noun after a numeral in this
    # domain, which is the bar for this set -- `shows`, `costs` and `times` are NOT added,
    # however verb-like they look in a given stem, because each is also a real noun and
    # silencing one would hide a genuine disagreement.
    "equals",   # "We need to find what 12 + 1 equals." -- a verb; there is no "1 equal"
    "vs",       # "1 vs 1: the larger top number ..." -- versus, and to_singular_phrase
                # would otherwise propose the non-word "1 v"
})


# ---------------------------------------------------------------------------------------
# THE FIELD CLASSIFICATION, AND THE HOLE THAT FORCED IT (2026-09-21)
# ---------------------------------------------------------------------------------------
# `_texts` used to name the fields it read and nothing else. That is an allowlist a human
# maintains against a payload the pipeline keeps changing, and it had drifted badly.
# MEASURED on 2026-09-21 over 453 student-path renders (151 nodes x 3 seeds), before any
# fix: the payload carried NINE text-bearing surfaces this function never looked at.
#
#   hints                  430/453 samples   <- a LIST. The function read `hint`, SINGULAR,
#                                              which the student path does not emit AT ALL.
#                                              No hint text had ever been linted. Live
#                                              violation on the day: mat_g2_na_q3_0 seed 17
#                                              shipping "Think of it as 1 groups of 3: 3."
#   format_data.mcq_options 127              <- a LIST, read by every MCQ pupil
#   distractors             159
#   correct_answer          205
#   format_data.statement    46 (covered), sentence 42, actor_name 22,
#   format_data.problem_expression 22, error_label 22, items 12, direction 12, time_str 8
#
# The contract row meanwhile claimed §1J covered "the rendered stem, its nested quoted
# statements, its options and its hint". The hint clause was false for as long as the
# student path has emitted `hints`, and "its options" was true only for the 204 samples
# carrying `format_data.options` and false for the 127 carrying `mcq_options` instead.
#
# ROOT CAUSE, not the symptom (Protocol 2). Adding `hints` alone would leave the same
# defect in eight other fields and leave the mechanism that produced it untouched: a
# silent allowlist cannot tell "I read every pupil-facing field" from "I read the fields
# somebody thought of". So the fields are now classified in BOTH directions, and a
# string-bearing key in neither set is a FINDING (`unclassified_pupil_text_1J`) rather
# than a silent omission. The next payload field to appear must be classified by someone
# who has looked at it -- which is the only form of this check that survives a grade 7
# payload nobody here has seen (Mandate 4).
_PUPIL_TEXT_KEYS: Tuple[str, ...] = (
    "question_text",
    "hints",            # the list the student path emits
    "hint",             # the singular some other surfaces still carry; both, not either
    "cloze_template",
    "instruction",
    "correct_answer",   # displayed back to the pupil on completion
    "distractors",      # the wrong options; string-valued on 164 of 453 samples
)

# Keys that carry a string and are NOT read as prose by a pupil: ids, enum tags, routing
# names, and the teacher-facing competency. Each is here because it was observed in the
# payload and classified deliberately -- not to silence the unclassified direction, which
# would defeat the point of having it.
_METADATA_KEYS: Tuple[str, ...] = (
    "problem_id", "node_id", "format", "answer_collection", "experience",
    "interest_theme", "dna_name", "formatter_name", "blank_target", "visual_type",
    "interaction_mode", "spine_id", "seed", "grade",
    # MATATAG competency text, shown in the Lab and teacher surfaces. Curriculum prose,
    # not something this lint may judge: its wording is ground truth (Protocol 5).
    "competency_text",
)

_PUPIL_TEXT_FD_KEYS: Tuple[str, ...] = (
    "prompt", "statement", "cloze_template",
    "sentence", "problem_expression", "actor_name", "time_str",
    "direction", "options", "mcq_options", "items",
    # Both found by the unclassified direction on its FIRST full run, 2026-09-21, on
    # `error_detect` routes the 3-seed probe never reached -- which is the direction
    # working exactly as intended. `actors_answer` is interpolated into the stem a pupil
    # reads ("Grace says the missing number is 13 R 3"), and `correct_value` is the same
    # kind of value as the top-level `correct_answer` already linted above.
    "actors_answer", "correct_value",
)

_METADATA_FD_KEYS: Tuple[str, ...] = (
    "correct_key",      # an option LETTER, not text
    # The context VARIANT the formatter served (mcq / cloze / error_detect). Classified as
    # pupil text until 2026-10-10, when H3's slot check (§14) had to account for it as
    # learner-read: MEASURED over 7,285 renders it takes only six tag values ('pure' 3,531,
    # 'word_problem' 572, 'colored_objects' 21, 'spinners' 12, 'coins' 9, 'weather' 1), and
    # no file under frontend/src reads format_data.context. A tag a pupil never sees is
    # metadata; linting it for count/noun agreement checked nothing.
    "context",
    # error_detect's trap identifier ("none", "unknown_error", or since ruling 39 the
    # ErrorPattern label such as "ar_off_one_high"). Classified as pupil text until
    # 2026-10-11 (owner ruling 38): MEASURED over 7,285 renders it took two tag values
    # ('none' 231, 'unknown_error' 135), and no file under frontend/src reads it.
    "error_label",
)


def _strings_in(value: Any) -> List[str]:
    """
    Every string a payload value contributes, flattened. [] when it contributes none.

    Handles the three shapes the payload actually uses: a bare string, a list of strings
    (`hints`, `mcq_options`), and a list of option dicts carrying `value`. A dict or a
    number contributes nothing -- visual payloads are §1G's and §9's, which is this
    module's known limitation 2, and a number has no noun after it to disagree with.
    """
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            if isinstance(item, dict):
                item = item.get("value")
            if isinstance(item, str) and item.strip():
                out.append(item)
        return out
    return []


def _texts(problem: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    (where, text) for every string a pupil reads. Nested statements included.

    An error-detect item quotes a worked solution INSIDE its stem; a cloze carries a
    template; options carry values; every item carries a LIST of hints. All of them are
    read, so all of them are linted. See the classification above for what is deliberately
    excluded and why.
    """
    out: List[Tuple[str, str]] = []
    for key in _PUPIL_TEXT_KEYS:
        strings = _strings_in(problem.get(key))
        for i, text in enumerate(strings):
            where = key if len(strings) == 1 and not isinstance(
                problem.get(key), list) else f"{key}[{i}]"
            out.append((where, text))
    fd = problem.get("format_data")
    if isinstance(fd, dict):
        for key in _PUPIL_TEXT_FD_KEYS:
            strings = _strings_in(fd.get(key))
            for i, text in enumerate(strings):
                where = f"format_data.{key}" if len(strings) == 1 and not isinstance(
                    fd.get(key), list) else f"format_data.{key}[{i}]"
                out.append((where, text))
    return out


def unclassified_fields(problem: Dict[str, Any]) -> List[str]:
    """
    Every string-bearing payload key this module has never been told how to treat.

    The direction that stops `_texts` going quietly out of date. A field that is neither
    linted nor deliberately excluded is one nobody has looked at, and a lint reports green
    through exactly that gap -- which is how no hint text was ever checked while §1J stood
    at 0 findings over 9,060 samples.
    """
    out: List[str] = []
    for key, value in problem.items():
        if key in _PUPIL_TEXT_KEYS or key in _METADATA_KEYS:
            continue
        if _strings_in(value):
            out.append(key)
    fd = problem.get("format_data")
    if isinstance(fd, dict):
        for key, value in fd.items():
            if key in _PUPIL_TEXT_FD_KEYS or key in _METADATA_FD_KEYS:
                continue
            if _strings_in(value):
                out.append(f"format_data.{key}")
    return out


def singular_count_nouns() -> Dict[str, str]:
    """
    {singular phrase: where the generator declares it} for the mirror direction.

    Read from the generator's own inventories on every call -- the interest bank the spines
    fill `{objects}`, `{item1}` and `{item2}` from, and the hint contract's unit table -- so a
    noun added to either is judged without touching this module (Mandate 4). A phrase the
    bank also lists as a plural (`objects`) that `to_singular_phrase` leaves unchanged is its
    own plural ("fish") and is dropped: a count before it is correct in either number.
    """
    from backend.app.practice_gen.dna.base import to_singular_phrase
    from backend.app.practice_gen.generators import interest
    from backend.app.practice_gen.hint_contract import _UNIT_FORMS

    lexicon: Dict[str, str] = {}
    invariant: set = set()
    themes = list(interest._INTERESTS.items()) + [
        ("NEUTRAL_SLOTS", {k: [v] for k, v in interest.NEUTRAL_SLOTS.items()})]
    for theme, data in themes:
        for value in data.get("objects", []) or []:
            low = value.lower()
            singular = to_singular_phrase(low)
            if singular == low:
                invariant.add(low)
            else:
                lexicon.setdefault(singular, f"interest bank '{theme}'.objects ('{value}')")
        # `item1`/`item2` are NOT uniformly singular in the bank ("cat toy" beside "running
        # shoes" and "crayons", measured 2026-10-10), so each value is singularised by the
        # same rule rather than trusted to be singular because of the slot it sits in.
        for slot in ("item1", "item2"):
            for value in data.get(slot, []) or []:
                lexicon.setdefault(to_singular_phrase(value.lower()),
                                   f"interest bank '{theme}'.{slot} ('{value}')")
    for unit, forms in _UNIT_FORMS.items():
        longs = [f for f in forms if len(f) > 2]
        for singular in longs:
            if to_singular_phrase(singular + "s") == singular and singular + "s" in longs:
                lexicon.setdefault(singular, f"hint_contract._UNIT_FORMS['{unit}']")
    for word in invariant:
        lexicon.pop(word, None)
    return lexicon


def scan_singular_after_many(text: str, lexicon: Dict[str, str]) -> Tuple[List[Tuple[int, str, str]], int]:
    """
    (violations, observed_not_judged) for the mirror direction in one string.

    A violation is (count, written_phrase, source): a count >= 2 whose following text is,
    longest match first, a lexicon phrase ending at a word boundary and closed by
    punctuation, the end of the text or a `_FUNCTION_WORDS` word. Every other
    singular-looking word after a count >= 2 is counted, not judged (limitation 1).
    """
    from backend.app.practice_gen.dna.base import to_singular_phrase

    violations: List[Tuple[int, str, str]] = []
    unjudged = 0
    for m in _COUNT_NOUN.finditer(text):
        before, count, word = m.group(1), int(m.group(2)), m.group(3)
        if count < 2 or (before and before.lower() in _LABEL_PRECEDERS):
            continue
        if word.lower() in _FUNCTION_WORDS:
            continue
        after = text[m.start(3):]
        low = after.lower()
        best = max((ph for ph in lexicon if low.startswith(ph)), key=len, default=None)
        if best is not None and (len(low) == len(best) or not low[len(best)].isalpha()):
            nxt = re.match(r"\s*([A-Za-z][A-Za-z']*)", after[len(best):])
            if nxt is None or nxt.group(1).lower() in _FUNCTION_WORDS:
                violations.append((count, after[:len(best)], lexicon[best]))
                continue
        if to_singular_phrase(word.lower()) == word.lower():
            unjudged += 1
    return violations, unjudged


def scan_text(text: str) -> Tuple[List[Tuple[int, str, str]], int, int]:
    """
    (violations, plural_after_one_ok, singular_after_many_observed) for one string.

    A violation is (count, written_word, correct_word). Only the plural-after-one
    direction is returned as a violation -- see KNOWN LIMITATION 1.
    """
    from backend.app.practice_gen.dna.base import to_singular_phrase

    violations: List[Tuple[int, str, str]] = []
    unclassified = 0
    mirror = 0
    for m in _COUNT_NOUN.finditer(text):
        before, count, word = m.group(1), int(m.group(2)), m.group(3)
        if before and before.lower() in _LABEL_PRECEDERS:
            continue
        low = word.lower()
        if low in _FUNCTION_WORDS:
            continue
        singular = to_singular_phrase(low)
        looks_plural = singular != low
        if count == 1:
            if looks_plural:
                violations.append((count, word, singular))
            else:
                unclassified += 1
        elif not looks_plural:
            mirror += 1
    return violations, unclassified, mirror


# An article candidate: "a"/"an" as a whole word, then the next whitespace-delimited token.
_ARTICLE = re.compile(r"(?<![\w'’-])(a|an|A|An)\s+(\S+)")
# What may precede a CAPITALISED "A"/"An" for it to be an article: the start of the text or of
# a sentence, or an opening quote/bracket. Mid-sentence, "A" is a label ("Garden Plot A is",
# "Segment A and": 75 such uses measured 2026-10-11 over seeds 1-60), not an article.
_SENTENCE_START = (".", "!", "?", ":", "\"", "“", "‘", "(", "\n")


def scan_articles(text: str) -> List[Tuple[str, str, str]]:
    """(written article, next word, article the shared rule gives) for each disagreement."""
    from backend.app.practice_gen.dna.base import indefinite_article

    out: List[Tuple[str, str, str]] = []
    for m in _ARTICLE.finditer(text):
        written, token = m.group(1), m.group(2)
        if written[0].isupper():
            before = text[:m.start()].rstrip(" ")
            if before and not before.endswith(_SENTENCE_START):
                continue
        core = token.lstrip("'\"‘“(")
        if not core or not core[0].isalnum():
            continue          # a symbol, a blank or a formula: no word to agree with
        want = indefinite_article(core)
        if want != written.lower():
            out.append((written, core.rstrip(".,;:!?'\"’”)"), want))
    return out


def collect_findings(node_ids: Optional[List[str]] = None) -> Tuple[List[str], Dict[str, int], Dict[str, str], List[str]]:
    """Every (node, seed, field) whose rendered text disagrees with its own count."""
    sys.path.insert(0, str(REPO_ROOT))
    from backend.app.practice_gen.registry import get_all_node_ids
    from backend.app.services.orchestrator import PracticeOrchestrator

    findings: List[str] = []
    mirror_findings: List[str] = []
    article_findings: List[str] = []
    lexicon = singular_count_nouns()
    unclassified_seen: Dict[str, str] = {}
    stats = {"samples": 0, "render_failures": 0, "singular_after_many_observed": 0,
             "singular_words_unjudged": 0, "texts_linted": 0, "mirror_lexicon": len(lexicon)}
    for node_id in (node_ids or get_all_node_ids()):
        for seed in SEEDS_PER_NODE:
            try:
                problem = PracticeOrchestrator.generate_problem(
                    node_id=node_id, seed=seed, is_student_path=True
                )
            except Exception as exc:  # noqa: BLE001 -- named, never a silent skip
                stats["render_failures"] += 1
                findings.append(
                    f"{node_id}: seed {seed} could not be rendered on the student path "
                    f"({type(exc).__name__}: {exc}), so its language was never linted. "
                    f"Reproduce: PracticeOrchestrator.generate_problem(node_id='{node_id}', "
                    f"seed={seed}, is_student_path=True)"
                )
                continue
            d = problem if isinstance(problem, dict) else problem.__dict__
            stats["samples"] += 1
            # One example per field is enough: the fix is to classify the FIELD, and
            # 9,060 copies of the same instruction is noise, not evidence.
            for field in unclassified_fields(d):
                unclassified_seen.setdefault(field, f"{node_id} seed {seed}")
            for where, text in _texts(d):
                stats["texts_linted"] += 1
                bad, unclassified, _mirror = scan_text(text)
                stats["singular_words_unjudged"] += unclassified
                for written, word, want in scan_articles(text):
                    article_findings.append(
                        f"{node_id}: seed {seed} {where} writes '{written} {word}', but the "
                        f"pipeline's own article rule (dna.base.indefinite_article, by sound) "
                        f"gives '{want}'. Text: {text[:160]!r}. Reproduce: "
                        f"PracticeOrchestrator.generate_problem(node_id='{node_id}', "
                        f"seed={seed}, is_student_path=True)"
                    )
                many, unjudged = scan_singular_after_many(text, lexicon)
                stats["singular_after_many_observed"] += unjudged
                for count, written, source in many:
                    mirror_findings.append(
                        f"{node_id}: seed {seed} {where} writes '{count} {written}' -- a count "
                        f"of {count} before a phrase the generator's own noun inventory "
                        f"declares SINGULAR ({source}). Text: {text[:160]!r}. Reproduce: "
                        f"PracticeOrchestrator.generate_problem(node_id='{node_id}', "
                        f"seed={seed}, is_student_path=True)"
                    )
                for count, written, correct in bad:
                    findings.append(
                        f"{node_id}: seed {seed} {where} writes '{count} {written}' where the "
                        f"count is {count}; the pipeline's own inflection rule "
                        f"(dna.base.to_singular_phrase) gives '{count} {correct}'. "
                        f"Text: {text[:160]!r}"
                    )
    stats["unclassified_fields"] = len(unclassified_seen)
    stats["article_findings"] = article_findings
    return findings, stats, unclassified_seen, mirror_findings


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    findings, stats, unclassified, mirror = collect_findings(node_ids)
    ok = True
    if findings:
        print(f"  FAIL count_noun_agreement_1J ({len(findings)}):")
        for f in findings[:12]:
            print(f"    - {f}")
        if len(findings) > 12:
            print(f"    ... and {len(findings) - 12} more.")
        ok = False
    else:
        print(f"  PASS count_noun_agreement_1J: 0 findings over {stats['samples']} "
              f"student-path sample(s), {stats['texts_linted']} text(s) linted; "
              f"{stats['singular_words_unjudged']} already-singular word(s) after a "
              f"count of 1")
    if mirror:
        print(f"  FAIL count_noun_singular_after_many_1J ({len(mirror)}):")
        for f in mirror[:12]:
            print(f"    - {f}")
        if len(mirror) > 12:
            print(f"    ... and {len(mirror) - 12} more.")
        ok = False
    else:
        print(f"  PASS count_noun_singular_after_many_1J: 0 findings against "
              f"{stats['mirror_lexicon']} declared singular count noun(s)")
    articles = stats["article_findings"]
    if articles:
        print(f"  FAIL indefinite_article_1J ({len(articles)}):")
        for f in articles[:12]:
            print(f"    - {f}")
        if len(articles) > 12:
            print(f"    ... and {len(articles) - 12} more.")
        ok = False
    else:
        print(f"  PASS indefinite_article_1J: 0 findings over {stats['texts_linted']} text(s)")
    print(f"  NOTE: {stats['singular_after_many_observed']} singular-looking word(s) after a "
          f"count of 2 or more observed and NOT judged (known limitation 1: outside the "
          f"generator's declared count nouns, or an open compound)")
    if unclassified:
        print(f"  FAIL unclassified_pupil_text_1J ({len(unclassified)}):")
        for field, where in sorted(unclassified.items()):
            print(f"    - payload field {field!r} carries text that §1J neither lints nor "
                  f"deliberately excludes (first seen {where}). Classify it in "
                  f"validate_language._PUPIL_TEXT_KEYS / _METADATA_KEYS (or the "
                  f"format_data pair) after LOOKING at what a pupil sees. A field nobody "
                  f"has classified is a field this lint reports green through.")
        ok = False
    else:
        print(f"  PASS unclassified_pupil_text_1J: every string-bearing payload field is "
              f"either linted or deliberately excluded")
    return ok


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§1J count/noun agreement in rendered text")
    ap.add_argument("--node-ids", help="comma-separated subset")
    args = ap.parse_args()
    nodes = args.node_ids.split(",") if args.node_ids else None
    return 0 if validate_all(nodes) else 1


if __name__ == "__main__":
    sys.exit(main())
