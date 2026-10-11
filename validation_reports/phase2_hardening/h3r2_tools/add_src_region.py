"""Add KEY to the template provenance (_src) of every fill(...) whose call starts in [L1, L2]."""
import ast, sys
path, l1, l2, key = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
src = open(path, encoding="utf-8").read(); tree = ast.parse(src)
lines = src.splitlines(keepends=True); offs = [0]
for l in lines: offs.append(offs[-1] + len(l.encode()))
pos = lambda ln, c: offs[ln - 1] + c
edits = []
for c in ast.walk(tree):
    if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "fill" and c.args and l1 <= c.lineno <= l2:
        kw = next((k for k in c.keywords if k.arg == "_src"), None)
        if kw is None:
            t = c.args[0]; at = pos(t.end_lineno, t.end_col_offset)
            edits.append((at, at, f", _src=({key!r},)"))
        else:
            vals = [e.value for e in kw.value.elts]
            if key in vals: continue
            edits.append((pos(kw.value.lineno, kw.value.col_offset), pos(kw.value.end_lineno, kw.value.end_col_offset),
                          "(" + ", ".join(repr(v) for v in vals + [key]) + ",)"))
b = src.encode()
for s_, e_, t in sorted(edits, reverse=True): b = b[:s_] + t.encode() + b[e_:]
out = b.decode(); ast.parse(out); open(path, "w", encoding="utf-8").write(out)
print(f"{path} [{l1},{l2}] +{key}: {len(edits)} fill(s)")
