"""§0 — a hint chain may not walk a pupil to a value its own final line denies.

THE DEFECT THIS CLOSES
----------------------
`fractions.generate_hints` served BOTH operations from one branch that hardcoded
addition, while its last line printed the REAL answer from `result_num`. For an
addition item the two agreed; for a subtraction item they did not. Measured on
`mat_g3_na_q4_7` seed 44 by a blind schema-v2 reviewer on 2026-09-23:

    "When adding fractions with the same denominator, keep the denominator the same."
    "Add only the numerators: 2 + 1 = 3."
    "Write the result over the same denominator: 3/6."
    "The answer is 1/6."

A pupil who follows the working gets 3/6 and is then told 1/6. Eleven of that
node's nineteen samples did this.

It was the second half of a TWO-SITE rule that had only been half fixed. The
`add_subtract` sentinel in `generate_params` was taught to resolve to a concrete
operation per call after an earlier blind reviewer reported that "subtract is
never enacted" -- but `generate_hints` was never taught the same distinction, so
the moment subtraction began to be served its guidance was wrong. That is the
shape this test exists to stop recurring: a generator gains a case and its
explanation does not.

WHY A SELF-CONSISTENCY CHECK RATHER THAN A RECOMPUTATION
--------------------------------------------------------
This asserts that the hints do not contradict THEMSELVES. It deliberately does
not re-derive what the answer ought to be: a second copy of the arithmetic in
the harness is a rule that will eventually disagree with the generator's copy,
which this repository has paid for before. The served answer is taken as given;
what is checked is that the worked steps arrive at it.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
1. **Scoped to the fractions DNA**, because that is where the stated-intermediate
   pattern exists today. A DNA that words its steps differently is not covered,
   and this check cannot see a hint that is merely unhelpful -- only one that is
   self-contradictory. `mat_g1_na_q4_2` renders "Add only the top numbers:
   2 + 0 = 2" on a counting-by-halves task: arithmetically consistent, so this
   test passes it, and whether it is pedagogically apt is §5's business.
2. **It reads the stated intermediate, not every intermediate.** A chain that
   states no result fraction before its final line is skipped rather than failed,
   because silence is not contradiction.
"""
from __future__ import annotations

import re

import pytest

from backend.app.practice_gen.registry import NODE_TO_DNA
from backend.app.practice_gen.validation import judgment_packets as jp

FRACTION = r"[0-9]+/[0-9]+"
_FRACTION_NODES = sorted(n for n, d in NODE_TO_DNA.items() if "fractions" in (d or []))


def _contradiction(hints):
    """Return (stated_intermediate, stated_final) when they disagree, else None."""
    if not hints or len(hints) < 2:
        return None
    final = re.search(rf"answer is\s+({FRACTION})", hints[-1])
    if not final:
        return None
    for step in hints[:-1]:
        stated = re.search(rf"(?:same\s+(?:denominator|bottom number)):\s*({FRACTION})", step)
        if stated and stated.group(1) != final.group(1):
            return stated.group(1), final.group(1)
    return None


def test_the_detector_catches_the_defect_it_was_written_for():
    """The 2026-09-23 chain, verbatim. A detector that cannot catch its own
    motivating case is decoration, so it is asserted before it is trusted."""
    assert _contradiction([
        "When adding fractions with the same denominator, keep the denominator the same.",
        "Add only the numerators: 2 + 1 = 3.",
        "Write the result over the same denominator: 3/6.",
        "The answer is 1/6.",
    ]) == ("3/6", "1/6")
    assert _contradiction([
        "When subtracting fractions with the same denominator, keep the denominator the same.",
        "Subtract only the numerators: 2 - 1 = 1.",
        "Write the result over the same denominator: 1/6.",
        "The answer is 1/6.",
    ]) is None


@pytest.mark.parametrize("node_id", _FRACTION_NODES)
def test_no_fraction_hint_chain_contradicts_its_own_answer(node_id):
    packet = jp.build_packet(node_id)
    samples = packet.get("samples") or []
    assert samples, f"{node_id}: packet rendered no samples"

    offenders = []
    for sample in samples:
        clash = _contradiction(sample.get("hints") or [])
        if clash:
            offenders.append(
                f"seed {sample.get('seed')} ({sample.get('formatter')}): hints compute "
                f"{clash[0]} then assert {clash[1]} -- {sample.get('hints')}"
            )

    assert not offenders, (
        f"{node_id}: {len(offenders)} of {len(samples)} hint chains walk the pupil to a "
        f"value the final hint denies.\n  " + "\n  ".join(offenders[:5])
    )
