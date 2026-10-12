"""rep.py FILE  < JSON [[old, new, count], ...]  -- exact replacements, asserting counts; adds E/R/S/transform/join imports used."""
import json, sys, re
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text(); reps = json.load(sys.stdin)
for old, new, n in reps:
    c = s.count(old)
    assert c == n, f"{c} != {n}: {old[:80]}"
    s = s.replace(old, new)
m = re.search(r"^from backend\.app\.practice_gen\.slots import ([^\n]+)$", s, re.M)
names = [x.strip() for x in m.group(1).split(",")]
for want in ("E", "R", "S", "transform", "join", "derived"):
    if want not in names and re.search(r"\b%s\(" % want, "".join(r[1] for r in reps)):
        names.append(want)
names = sorted(set(names), key=lambda t: (t[0].islower(), t))
s = s[:m.start(1)] + ", ".join(names) + s[m.end(1):]
p.write_text(s); print(p.name, "ok:", len(reps), "|", m.group(0)[:0] + ", ".join(names))
