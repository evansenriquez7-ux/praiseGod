"""Show the non-hint learner fills of one render: site, template, slots (domain, src), derivations."""
import sys
from backend.app.practice_gen.validation import validate_composition as VC
from backend.app.practice_gen.validation.validate_language import _texts
if __name__ == "__main__":
    lc, seed = sys.argv[1], int(sys.argv[2])
    p, fills = VC._render(lc, seed)
    gv = p.get("given_values") or {}
    print("FMT", p.get("formatter_name"), "| keys", {k: gv[k] for k in sys.argv[3:] if k in gv})
    by = {f.text: f for f in fills}
    shown = [t for w, t in _texts(p) if not w.startswith("hint")]
    seen = set()
    stack = [by[t] for t in shown if t in by]
    while stack:
        f = stack.pop()
        if id(f) in seen: continue
        seen.add(id(f))
        print(f"  {f.site.split('practice_gen/')[-1]:44s} {f.template[:70]!r}")
        for (n, v, d), (_, src) in zip(f.slots, f.sources):
            print(f"      {n}={str(v)[:30]!r} dom={d if isinstance(d,str) else type(d).__name__} src={src}")
        for (n, src) in f.sources[len(f.slots):]:
            print(f"      [{n}] src={src}")
        for n, v, d in f.slots:
            if d == "fill" and v in by and by[v] is not f: stack.append(by[v])
    print("  derivations:", [(d.key, d.src) for d in fills.derivations])
