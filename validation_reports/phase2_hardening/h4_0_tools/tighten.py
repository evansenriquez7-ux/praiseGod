"""
Rewrite type-only slots by AST position.  tighten.py DECISIONS.json [--dry]
Each decision: {"site": "backend/...py:LINE", "slot": NAME, "domain": '"value:k"' | '"fill"' | 'E(...)' python
source, "why": optional kind, "src": optional python tuple source (replaces src)}.
Locates the fill/record/join/S-holding call whose span contains LINE and that has keyword NAME whose value
is derived(...) or S(..., "num.derived"/"text.derived", ...). Keeps the slot's existing src unless "src" given.
"""
import ast, json, sys, collections

def find(tree, line, slot):
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.lineno <= line <= node.end_lineno:
            for kw in node.keywords:
                if kw.arg == slot and isinstance(kw.value, ast.Call):
                    v = kw.value; fn = getattr(v.func, "id", None)
                    if fn == "derived" or (fn == "S" and len(v.args) >= 2 and isinstance(v.args[1], ast.Constant)
                                           and v.args[1].value in ("num.derived", "text.derived")):
                        hits.append((node.end_lineno - node.lineno, node, kw))
    hits.sort(key=lambda h: h[0])
    return hits

def offset(lines, ln, col):
    return sum(len(l) for l in lines[:ln - 1]) + len(lines[ln - 1][:col].encode("utf-8").decode("utf-8"))

if __name__ == "__main__":
    decs = json.load(open(sys.argv[1])); dry = "--dry" in sys.argv
    by = collections.defaultdict(list)
    for d in decs:
        path, line = d["site"].rsplit(":", 1); by[path].append((int(line), d))
    ok = bad = 0
    for path, items in by.items():
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src); lines = src.splitlines(keepends=True)
        reps = []
        for line, d in items:
            hits = find(tree, line, d["slot"])
            if not hits:
                print("NOT FOUND", d["site"], d["slot"]); bad += 1; continue
            if len(hits) > 1 and hits[0][0] == hits[1][0]:
                print("AMBIGUOUS", d["site"], d["slot"]); bad += 1; continue
            v = hits[0][2].value
            # byte offsets: ast col offsets are UTF-8 byte offsets
            b = src.encode("utf-8"); bl = [l.encode("utf-8") for l in lines]
            start = sum(len(x) for x in bl[:v.lineno - 1]) + v.col_offset
            end = sum(len(x) for x in bl[:v.end_lineno - 1]) + v.end_col_offset
            expr = ast.get_source_segment(src, v.args[0])
            srckw = [k for k in v.keywords if k.arg == "src"]
            srcsrc = d.get("src") or (ast.get_source_segment(src, srckw[0].value) if srckw else None)
            if srcsrc is None and v.func.id == "S" and len(v.args) >= 3:
                srcsrc = ast.get_source_segment(src, v.args[2])
            if d.get("why"):
                new = f"derived({expr}, src={srcsrc}, why={d['why']!r})"
            else:
                new = f"S({expr}, {d['domain']}" + (f", src={srcsrc}" if srcsrc and srcsrc not in ("()",) else "") + ")"
            reps.append((start, end, new, d))
        reps.sort(key=lambda r: r[0], reverse=True)
        b = src.encode("utf-8")
        for start, end, new, d in reps:
            print(f"  {d['site'].split('practice_gen/')[-1]} {d['slot']}: {b[start:end].decode()[:70]}  ->  {new[:90]}")
            b = b[:start] + new.encode("utf-8") + b[end:]; ok += 1
        if not dry:
            open(path, "w", encoding="utf-8").write(b.decode("utf-8"))
    print("applied" if not dry else "would apply", ok, "failed", bad)
