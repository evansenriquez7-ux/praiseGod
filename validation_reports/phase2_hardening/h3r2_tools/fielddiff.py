"""Which payload paths differ between two render_snapshot files (for attributing a content change)."""
import json, sys, collections
def load(p):
    out = {}
    for l in open(p):
        r = json.loads(l); out[json.dumps(r["k"])] = r["r"]
    return out
def walk(a, b, path, acc):
    if type(a) != type(b): acc.append(path); return
    if isinstance(a, dict):
        for k in set(a) | set(b): walk(a.get(k), b.get(k), f"{path}.{k}", acc)
    elif isinstance(a, list):
        if len(a) != len(b): acc.append(path + "[len]"); return
        for i, (x, y) in enumerate(zip(a, b)): walk(x, y, f"{path}[]", acc)
    elif a != b: acc.append(path)
if __name__ == "__main__":
    A, B = load(sys.argv[1]), load(sys.argv[2])
    paths = collections.Counter(); fmts = collections.Counter(); n = 0; ex = []
    for k in A:
        if k in B and A[k] != B[k]:
            n += 1; acc = []; walk(A[k], B[k], "", acc)
            paths.update(set(acc)); fmts[B[k].get("formatter_name")] += 1
            if len(ex) < int(sys.argv[3] if len(sys.argv) > 3 else 3): ex.append((k, [(p) for p in acc][:4]))
    print("changed renders:", n); print("paths:", dict(paths)); print("formatters:", dict(fmts))
    for e in ex: print("  e.g.", e)
