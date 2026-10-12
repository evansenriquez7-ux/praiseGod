"""reanchor.py NAME FILE  < JSON {"old": ..., "new": ...}: rewrite the (old, new) literals of one mutation's edit by AST position."""
import ast, json, sys
name, target = sys.argv[1], sys.argv[2]; spec = json.load(sys.stdin)
H = "tests/mutation_harness.py"; src = open(H, encoding="utf-8").read(); tree = ast.parse(src)
b = src.encode("utf-8"); lines = src.splitlines(keepends=True); bl = [l.encode("utf-8") for l in lines]
def off(ln, col): return sum(len(x) for x in bl[:ln - 1]) + col
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "Mutation":
        kw = {k.arg: k.value for k in node.keywords}
        if isinstance(kw.get("name"), ast.Constant) and kw["name"].value == name:
            d = kw["edits"]
            for k, v in zip(d.keys, d.values):
                if k.value == target:
                    o, n = v.elts
                    reps = [(off(o.lineno, o.col_offset), off(o.end_lineno, o.end_col_offset), repr(spec["old"])),
                            (off(n.lineno, n.col_offset), off(n.end_lineno, n.end_col_offset), repr(spec["new"]))]
                    for s, e, t in sorted(reps, reverse=True):
                        b = b[:s] + t.encode("utf-8") + b[e:]
                    open(H, "w", encoding="utf-8").write(b.decode("utf-8")); print("re-anchored", name); sys.exit(0)
sys.exit("not found")
