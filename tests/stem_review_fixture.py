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


def _reply(item_id, clauses, overall, reasoning, failing=()):
    """A reply in the key order the mutations rely on: item, clauses, failing_templates, overall, reasoning."""
    return json.dumps({"item": item_id, "clauses": clauses, "failing_templates": list(failing),
                       "overall": overall, "reasoning": reasoning}, ensure_ascii=False)


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
    for i, node_id in enumerate((MAIN,) + OTHERS):
        renders, _refused = SP.observe_lc(node_id)
        body, key = SP.build_item(node_id, renders)
        item_id = f"FIX-{i + 1:03d}"
        item = {"item": item_id, **body}
        key = {**key, "item_hash": SP.item_hash(body)}
        scratch.write_text(stem_file.prompt_text(item), encoding="utf-8")
        if node_id == MAIN:
            clauses = {cid: {"verdict": "PRODUCIBLE", "template": t,
                             "reasoning": f"Fixture: the template '{t}' addresses this clause."}
                       for cid, t in MAIN_CLAUSES.items()}
            first = _file(item, key, _reply(item_id, clauses, "PASS", MAIN_REASONING["first"]),
                          "first", None, "2026-10-13T00:00:00Z", scratch)
            written.append(first)
            written.append(_file(item, key, _reply(item_id, clauses, "PASS", MAIN_REASONING["confirming"]),
                                 "confirming", f"fixture-{MAIN}-first", "2026-10-13T01:00:00Z", scratch))
        else:
            t = body["families"][0]["template"]
            clauses = {c["id"]: {"verdict": "PRODUCIBLE", "template": t, "reasoning": "Fixture: hand-written."}
                       for c in body["clauses"]}
            written.append(_file(item, key, _reply(item_id, clauses, "PASS", SHARED_FRAME.format(t=t)),
                                 "first", None, "2026-10-13T00:00:00Z", scratch))
    scratch.unlink()
    for path in written:
        print(f"wrote {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
