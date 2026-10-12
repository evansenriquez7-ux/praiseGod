import collections, sys
from backend.app.practice_gen.validation import validate_slots as VS
from backend.app.practice_gen.registry import get_all_node_ids
from backend.app.practice_gen.slots import capture, E, R
from backend.app.services.orchestrator import PracticeOrchestrator
occ = collections.Counter(); pairs = collections.defaultdict(set)
for n in sorted(get_all_node_ids()):
    for seed in VS.SEEDS:
        with capture() as fills:
            PracticeOrchestrator.generate_problem(node_id=n, seed=seed, is_student_path=True)
        for f in fills:
            whys = dict(f.reasons)
            for name, v, d in f.slots:
                k = ("E" if isinstance(d, E) else "R" if isinstance(d, R) else
                     (d.split(":")[0] if isinstance(d, str) and ":" in d else str(d)))
                if k in ("num.derived", "text.derived") and whys.get(name): k += "+why:" + whys[name]
                occ[k] += 1; pairs[k].add((f.site, name))
tot = sum(occ.values())
for k, v in occ.most_common(): print(f"{k:28s} {v:7d} {100*v/tot:5.1f}%  {len(pairs[k]):5d} site/slot")
print("total", tot)
