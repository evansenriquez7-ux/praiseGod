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

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
1. **One direction is enforced: plural-after-one.** The mirror direction (a singular noun
   after a count of two or more, "3 cookie") is MEASURED and reported in the summary but
   does not gate, because deciding that a word is the head of its noun phrase — "3 score
   cards", "2 water bottles" — needs more than the next token, and a gate that guesses
   would fail on a grade-7 noun that does not exist yet. The measured count is printed on
   every run so the decision to leave it open stays visible.
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
})


def _texts(problem: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    (where, text) for every string a pupil reads. Nested statements included.

    An error-detect item quotes a worked solution INSIDE its stem; a cloze carries a
    template; options carry values. All of them are read, so all of them are linted.
    """
    out: List[Tuple[str, str]] = []
    stem = problem.get("question_text")
    if stem:
        out.append(("question_text", str(stem)))
    for key in ("hint", "cloze_template", "instruction"):
        val = problem.get(key)
        if val:
            out.append((key, str(val)))
    fd = problem.get("format_data")
    if isinstance(fd, dict):
        for key in ("prompt", "statement", "cloze_template", "context"):
            val = fd.get(key)
            if isinstance(val, str) and val:
                out.append((f"format_data.{key}", val))
        for i, opt in enumerate(fd.get("options") or []):
            val = opt.get("value") if isinstance(opt, dict) else opt
            if isinstance(val, str) and val:
                out.append((f"format_data.options[{i}]", val))
    return out


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


def collect_findings(node_ids: Optional[List[str]] = None) -> Tuple[List[str], Dict[str, int]]:
    """Every (node, seed, field) whose rendered text disagrees with its own count."""
    sys.path.insert(0, str(REPO_ROOT))
    from backend.app.practice_gen.registry import get_all_node_ids
    from backend.app.services.orchestrator import PracticeOrchestrator

    findings: List[str] = []
    stats = {"samples": 0, "render_failures": 0, "singular_after_many_observed": 0,
             "singular_words_unjudged": 0}
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
            for where, text in _texts(d):
                bad, unclassified, mirror = scan_text(text)
                stats["singular_words_unjudged"] += unclassified
                stats["singular_after_many_observed"] += mirror
                for count, written, correct in bad:
                    findings.append(
                        f"{node_id}: seed {seed} {where} writes '{count} {written}' where the "
                        f"count is {count}; the pipeline's own inflection rule "
                        f"(dna.base.to_singular_phrase) gives '{count} {correct}'. "
                        f"Text: {text[:160]!r}"
                    )
    return findings, stats


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    findings, stats = collect_findings(node_ids)
    if findings:
        print(f"  FAIL count_noun_agreement_1J ({len(findings)}):")
        for f in findings[:12]:
            print(f"    - {f}")
        if len(findings) > 12:
            print(f"    ... and {len(findings) - 12} more.")
        return False
    print(f"  PASS count_noun_agreement_1J: 0 findings over {stats['samples']} student-path "
          f"sample(s); {stats['singular_after_many_observed']} singular-after-many "
          f"construction(s) observed and NOT judged (known limitation 1), "
          f"{stats['singular_words_unjudged']} already-singular word(s) after a count of 1")
    return True


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§1J count/noun agreement in rendered text")
    ap.add_argument("--node-ids", help="comma-separated subset")
    args = ap.parse_args()
    nodes = args.node_ids.split(",") if args.node_ids else None
    return 0 if validate_all(nodes) else 1


if __name__ == "__main__":
    sys.exit(main())
