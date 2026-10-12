"""Inventory of type-only slots at validate_slots.SEEDS on the student path.
One JSONL row per (lc, seed, site, slot) occurrence: domain, value repr, reachable (closure from
learner-read fields through 'fill' slots), keys of ctx.values equal to the value."""
import json, sys, collections
from backend.app.practice_gen.validation import validate_slots as VS
from backend.app.practice_gen.validation.validate_language import _texts
from backend.app.practice_gen.registry import get_all_node_ids
from backend.app.practice_gen.slots import capture
from backend.app.services.orchestrator import PracticeOrchestrator
from backend.app.services import orchestrator as _orch

def run(n, seed):
    seen = {}; real = _orch.apply_formatter
    def spy(ctx, f, rng):
        seen.update(ctx.values or {}); return real(ctx, f, rng)
    _orch.apply_formatter = spy
    try:
        with capture() as fills:
            p = PracticeOrchestrator.generate_problem(node_id=n, seed=seed, is_student_path=True).model_dump()
    finally:
        _orch.apply_formatter = real
    return p, fills, seen

if __name__ == "__main__":
    out = open(sys.argv[1], "w")
    lcs = sys.argv[2].split(",") if len(sys.argv) > 2 else sorted(get_all_node_ids())
    for n in lcs:
        for seed in VS.SEEDS:
            p, fills, seen = run(n, seed)
            by = collections.defaultdict(list)
            for f in fills: by[f.text].append(f)
            reach = set(); stack = []
            for where, t in _texts(p):
                for f in by.get(t, []): stack.append((f, where.split("[")[0]))
            field_of = {}
            while stack:
                f, w = stack.pop()
                if id(f) in reach: continue
                reach.add(id(f)); field_of[id(f)] = w
                for _nm, v, d in f.slots:
                    if d == "fill" and isinstance(v, str):
                        stack.extend((g, w) for g in by.get(v, []) if g is not f)
            for f in fills:
                for (nm, v, d), (_n2, src) in zip(f.slots, f.sources):
                    if d not in ("num.derived", "text.derived"): continue
                    eq = sorted(k for k, x in seen.items() if type(x) == type(v) and x == v)
                    out.write(json.dumps({"lc": n, "seed": seed, "site": f.site, "slot": nm, "dom": d,
                        "v": v if isinstance(v, (int, float, str)) else repr(v), "reach": id(f) in reach,
                        "field": field_of.get(id(f)), "eq": eq, "src": list(src), "tpl": f.template[:90],
                        "fmt": p.get("formatter_name"), "dna": p.get("dna_name")}, ensure_ascii=False, default=str) + "\n")
    out.close()
