"""Wide observation of every type-only slot: seeds 1-40 student path + every pinned formatter at 3,17,29.
Writes JSON {site|slot: {n, lcs, eq (keys equal in EVERY obs, any value size), vals (distinct, <=40),
types, allfill (every value is another fill's text), src (recorded), why}}."""
import json, sys, collections
from backend.app.practice_gen.registry import get_all_node_ids, get_node_formatters
from backend.app.practice_gen.slots import capture
from backend.app.services.orchestrator import PracticeOrchestrator
from backend.app.services import orchestrator as _orch
TO = ("num.derived", "text.derived")
if __name__ == "__main__":
    lcs = sys.argv[2].split(",") if len(sys.argv) > 2 else sorted(get_all_node_ids())
    acc = {}
    fails = 0
    for n in lcs:
        runs = [(s, None) for s in range(1, 41)] + [(s, f) for f in sorted(get_node_formatters(n) or []) for s in (3, 17, 29)]
        for seed, fmt in runs:
            seen = {}; real = _orch.apply_formatter
            def spy(ctx, f, rng):
                seen.update(ctx.values or {}); return real(ctx, f, rng)
            _orch.apply_formatter = spy
            try:
                with capture() as fills:
                    PracticeOrchestrator.generate_problem(node_id=n, seed=seed, formatter=fmt, is_student_path=fmt is None)
            except Exception as exc:          # a pinned combination that refuses: recorded, not hidden
                fails += 1
                continue
            finally:
                _orch.apply_formatter = real
            texts = collections.Counter(g.text for g in fills)
            for f in fills:
                srcs, whys = dict(f.sources), dict(f.reasons)
                for name, v, d in f.slots:
                    if d not in TO or whys.get(name): continue
                    k = f"{f.site}|{name}"
                    a = acc.setdefault(k, {"n": 0, "lcs": set(), "eq": None, "vals": [], "types": set(),
                                           "allfill": True, "src": set(), "keys": None})
                    a["n"] += 1; a["lcs"].add(n); a["types"].add(type(v).__name__)
                    eq = {kk for kk, x in seen.items() if type(x) == type(v) and x == v}
                    a["eq"] = eq if a["eq"] is None else a["eq"] & eq
                    a["keys"] = set(seen) if a["keys"] is None else a["keys"] & set(seen)
                    if not (isinstance(v, str) and texts.get(v, 0) > (1 if v == f.text else 0)): a["allfill"] = False
                    a["src"].add(tuple(srcs.get(name, ())))
                    r = v if isinstance(v, (int, float, str)) else repr(v)
                    if r not in a["vals"] and len(a["vals"]) < 40: a["vals"].append(r)
    out = {k: {**a, "lcs": sorted(a["lcs"]), "eq": sorted(a["eq"] or []), "types": sorted(a["types"]),
               "src": sorted(a["src"]), "keys": sorted(a["keys"] or [])} for k, a in acc.items()}
    json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False, indent=0, default=str)
    print(len(out), "site|slot observed;", fails, "pinned/seed renders raised")
