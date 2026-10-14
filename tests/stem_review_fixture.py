"""
Write the §17 mutation-proof fixture records (batch H4) into tests/stem_review_fixtures/.

The proofs of §17 must not depend on an LLM (NEXT_AGENT_PROMPT §5.3), so these records are
HAND-WRITTEN: every reply below was written by the agent that built the gate, under the identity
prefix `validate_stem_review.FIXTURE_PREFIX`, which §17 refuses anywhere but a fixture directory.
They are not reviews and judge nothing.

  * mat_g2_na_q3_8 (the lc §14's mutations also plant on): a first and a confirming record, both
    PASS with every clause PRODUCIBLE, on the LIVE packet. `validate_stem_review --node-ids
    mat_g2_na_q3_8 --review-dir tests/stem_review_fixtures` therefore exits 0, and each §17
    mutation plants one defect into the generator, the builder or one of these records.
  * mat_g1_dp_q3_0 (owner ruling 47): the same pair on an lc whose stems draw from an ITEM
    BANK, which mat_g2_na_q3_8 does not, so a mutation of how a bank is packeted reaches a
    record whose freshness is checked.
  * mat_g1_mg_q1_0 and mat_g1_dp_q3_2 (owner ruling 48): the same pair on an lc with VOCABULARY
    GATES and a shared bank its filter draws only some rows of, and on an lc whose runtime
    category slots are shown as a field of the drawn bank row -- so a mutation of how a gate, the
    drawn rows or that pairing is packeted reaches a record whose freshness is checked.
  * mat_g2_na_q4_0 (owner ruling 48e): the same pair on an lc that prints several vocabulary-gate
    words through `{term}` (fraction, numerator, denominator), so a mutation of how gate words
    are split into families reaches a record whose freshness is checked.
  * mat_g3_mg_q2_0, mat_g3_mg_q2_2, mat_g3_mg_q2_5: one first record each, out of the proof's
    scope, whose overall reasoning shares ONE sentence frame (3 lcs: the most §17 allows), so a
    mutation that gives mat_g2_na_q3_8 that frame makes 4; and whose identities a mutation can
    reuse. Their freshness is never checked (they are out of scope), only their own bytes.

Re-run this ONLY when the fixture lc's stems change (the proofs' baselines then report it STALE,
and every §17 mutation is INVALID until the fixture is rewritten) or when the record schema changes:

    PYTHONPATH=. .venv/bin/python tests/stem_review_fixture.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.practice_gen.validation import stem_packets as SP  # noqa: E402
from backend.app.practice_gen.validation import validate_stem_review as VSR  # noqa: E402
from tests import stem_file  # noqa: E402

FIXTURE_DIR = REPO_ROOT / "tests" / "stem_review_fixtures"
MAIN = "mat_g2_na_q3_8"
BANK_LC = "mat_g1_dp_q3_0"
BANK_CLAUSES = {"collect_data": "{question}", "one_variable": "{question}", "simple_interview": "{question}"}
BANK_REASONING = {
    "first": "Fixture, not a judgment: each interview row is read as one problem with its own keyed answer.",
    "confirming": "Fixture, not a judgment: the bank rows and the hints were read for the bank lc's gate words.",
}
GATE_LC = "mat_g1_mg_q1_0"
GATE_TEMPLATE = "Look at the shapes in different sizes and orientations. Which shape on the board has {v}?"
GATE_CLAUSES = {c: GATE_TEMPLATE for c in ("identify", "simple_2_dimensional_shapes", "triangle", "rectangle",
                                           "square", "different_size", "different_orientation")}
GATE_REASONING = {
    "first": "Fixture, not a judgment: the gated hint word and the drawn shape rows were read for this lc.",
    "confirming": "Fixture, not a judgment: the board question was read with the clue it names.",
}
PAIR_LC = "mat_g1_dp_q3_2"
PAIR_CLAUSES = {"interpret": "Look at the picture graph. {sub_q}", "pictograph": "Look at the {pg_label} carefully.",
                "without_scale": "Each picture stands for 1 item."}
PAIR_REASONING = {
    "first": "Fixture, not a judgment: each theme row was read with its own subject and categories.",
    "confirming": "Fixture, not a judgment: the reading questions were read against one picture graph each.",
}
TERM_LC = "mat_g2_na_q4_0"
TERM_CLAUSES = {"represent": "Shade {fraction_str} of the shape.", "identify": "What fraction does the {name} show?",
                "unit_fractions": "What fraction does the {name} show?",
                "denominators_2_3_4_5_6_8": "What fraction does the {name} show?"}
TERM_REASONING = {
    "first": "Fixture, not a judgment: each gate word was read in the hint it is printed in.",
    "confirming": "Fixture, not a judgment: the shading and naming questions were read for unit fractions.",
}
OTHERS = ("mat_g3_mg_q2_0", "mat_g3_mg_q2_2", "mat_g3_mg_q2_5")
DELIVERY = ("fixture written by tests/stem_review_fixture.py for §17 mutation proofs; no judge was "
            "dispatched, so no judge read the packet or CLAUDE.md")

MAIN_CLAUSES = {
    "distinguish": "{d} ÷ 2 comes out exactly, so {d} is an even number",
    "even_and_odd_numbers": "Nothing is left over, so {n} is an even number.",
    "division": "Divide {n} by 2: how many 2s fit into {n}?",
    "divisor_2": "2 × {half} = {twice}, and {n} − {twice} = {left}.",
}
MAIN_REASONING = {
    "first": ("Fixture, not a judgment: the hint 'Divide {n} by 2: how many 2s fit into {n}?' and the "
              "statements about even and odd numbers keep to division by 2."),
    "confirming": ("Fixture, not a judgment: each template names the remainder of a division by 2, e.g. "
                   "'1 is left over, so {n} is an odd number.', and uses no gated word."),
}
# One frame for the three out-of-scope lcs (quotes stripped, these are the same skeleton).
SHARED_FRAME = "Fixture, not a judgment: the template '{t}' was read with its domains, and nothing in it is out of scope."


def _reply(item_id, clauses, overall, reasoning):
    """A reply in the key order the mutations rely on: item, clauses, failing_families,
    failing_templates, overall, reasoning (schema 2, owner ruling 46b)."""
    return json.dumps({"item": item_id, "clauses": clauses, "failing_families": [], "failing_templates": [],
                       "overall": overall, "reasoning": reasoning}, ensure_ascii=False)


def _family_of(body, template):
    """The one family printing `template`; a fixture never guesses between two (ruling 46b)."""
    ids = [f["id"] for f in body["families"] if f["template"] == template]
    if len(ids) != 1:
        raise SystemExit(f"fixture: template {template!r} is printed by {len(ids)} families {ids}, not one")
    return ids[0]


def _file(item, key, raw, role, confirms, stamp, prompt_path):
    args = SimpleNamespace(
        role=role, confirms=confirms, judged_by=f"{VSR.FIXTURE_PREFIX}-{key['node_id']}-{role}",
        dispatch_id=f"fixture-{key['node_id']}-{role}", filed_at=stamp, delivery=DELIVERY,
        tool_uses="none (hand-written fixture)", prompt=str(prompt_path))
    rec = stem_file.build_record(item, key, raw, args)
    problems = stem_file.refusals(rec, FIXTURE_DIR)
    if problems:
        raise SystemExit(f"fixture {key['node_id']} {role} refused: {problems}")
    rec.pop("_verdict", None)
    out = FIXTURE_DIR / key["node_id"] / f"{rec['record_id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def main() -> int:
    if FIXTURE_DIR.exists():
        shutil.rmtree(FIXTURE_DIR)
    FIXTURE_DIR.mkdir(parents=True)
    scratch = FIXTURE_DIR / "_prompt.txt"
    written = []
    specs = {MAIN: (MAIN_CLAUSES, MAIN_REASONING), BANK_LC: (BANK_CLAUSES, BANK_REASONING),
             GATE_LC: (GATE_CLAUSES, GATE_REASONING), PAIR_LC: (PAIR_CLAUSES, PAIR_REASONING),
             TERM_LC: (TERM_CLAUSES, TERM_REASONING)}
    for i, node_id in enumerate((MAIN, BANK_LC) + OTHERS + (GATE_LC, PAIR_LC, TERM_LC)):
        renders, _refused = SP.observe_lc(node_id)
        body, key = SP.build_item(node_id, renders)
        item_id = f"FIX-{i + 1:03d}"
        item = {"item": item_id, **body}
        key = {**key, "item_hash": SP.item_hash(body)}
        scratch.write_text(stem_file.prompt_text(item), encoding="utf-8")
        if node_id in specs:
            spec, why = specs[node_id]
            clauses = {cid: {"verdict": "PRODUCIBLE", "family": _family_of(body, t), "template": t,
                             "reasoning": f"Fixture: the template '{t}' addresses this clause."}
                       for cid, t in spec.items()}
            first = _file(item, key, _reply(item_id, clauses, "PASS", why["first"]),
                          "first", None, "2026-10-13T00:00:00Z", scratch)
            written.append(first)
            written.append(_file(item, key, _reply(item_id, clauses, "PASS", why["confirming"]),
                                 "confirming", f"fixture-{node_id}-first", "2026-10-13T01:00:00Z", scratch))
        else:
            t, fid = body["families"][0]["template"], body["families"][0]["id"]
            clauses = {c["id"]: {"verdict": "PRODUCIBLE", "family": fid, "template": t,
                                 "reasoning": "Fixture: hand-written."}
                       for c in body["clauses"]}
            written.append(_file(item, key, _reply(item_id, clauses, "PASS", SHARED_FRAME.format(t=t)),
                                 "first", None, "2026-10-13T00:00:00Z", scratch))
    scratch.unlink()
    for path in written:
        print(f"wrote {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
