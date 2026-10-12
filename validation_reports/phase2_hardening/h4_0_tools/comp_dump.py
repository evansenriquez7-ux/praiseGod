import json, sys
from backend.app.practice_gen.validation import validate_composition as VC
f = VC.collect_findings()
f = f[0] if isinstance(f, tuple) else f
json.dump({k: sorted(v) for k, v in f.items() if isinstance(v, list)}, open(sys.argv[1], "w"), indent=0, ensure_ascii=False)
print({k: len(v) for k, v in f.items() if isinstance(v, list)})
