"""Ruling 49 helper: dump what an lc's renders actually printed, grouped by template.

usage: PYTHONPATH=. .venv/bin/python local_only/scratch/h4c/render_dump.py NODE_ID [OUT.json]

Read-only. Renders every path validate_slots.paths(NODE_ID) names (student seeds 1-40 plus each
advertised formatter at seeds 3, 17, 29) through validate_slots.observe -- the same entry §14/§17
render through -- and records, per template, every distinct text it printed with the first
(seed, formatter) that printed it. Also records each path's question_text, hints and answer choices.
A path that raises is recorded with its error (never skipped silently).
"""
import json
import sys
from collections import OrderedDict

from backend.app.practice_gen.validation.validate_slots import observe, paths


def main(node_id: str, out: str) -> int:
    by_tpl: "OrderedDict[str, dict]" = OrderedDict()
    problems = []
    errors = []
    for seed, fmt in paths(node_id):
        try:
            problem, fills, _seen = observe(node_id, seed, fmt)
        except Exception as exc:  # recorded and reported, never swallowed
            errors.append({"seed": seed, "formatter": fmt, "error": f"{type(exc).__name__}: {exc}"})
            continue
        for f in fills:
            ent = by_tpl.setdefault(f.template, {"site": f.site, "texts": OrderedDict()})
            ent["texts"].setdefault(f.text, f"seed {seed}" + (f" formatter {fmt}" if fmt else ""))
        fd = problem.get("format_data") or {}
        problems.append({"seed": seed, "formatter": fmt,
                         "question_text": problem.get("question_text"),
                         "hints": problem.get("hints"),
                         "correct_answer": problem.get("correct_answer"),
                         "options": fd.get("options") or fd.get("mcq_options") or problem.get("distractors")})
    json.dump({"node_id": node_id, "errors": errors, "templates": by_tpl, "problems": problems},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(f"{node_id}: {len(problems)} renders, {len(errors)} errors, {len(by_tpl)} templates -> {out}")
    return 1 if errors else 0


if __name__ == "__main__":
    nid = sys.argv[1]
    sys.exit(main(nid, sys.argv[2] if len(sys.argv) > 2 else f"local_only/scratch/h4c/renders/{nid}.json"))
