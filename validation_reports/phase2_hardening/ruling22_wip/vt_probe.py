import collections, sys
from backend.app.practice_gen.validation.judgment_packets import _render_sample
node=sys.argv[1]; c=collections.Counter(); tasks=collections.defaultdict(collections.Counter)
for seed in range(1000,1040):
    s=_render_sample(node,seed,include_private_variant_evidence=True)
    if s is None: continue
    vt=s.get("visual_type"); c[vt]+=1
    tasks[str((s.get("_provider_variant_evidence") or {}).get("task_type"))][vt]+=1
print(node,"visual_type:",dict(c),"| by task_type:",{k:dict(v) for k,v in tasks.items()})
