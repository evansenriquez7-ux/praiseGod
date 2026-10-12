"""Rewrite derived(count_noun(x, p)[, src=...]) -> S(count_noun(x, p), E((count_noun(1, p), p), basis)[, src=...])."""
import ast, sys, subprocess
files = subprocess.run(["git", "grep", "-l", "derived(count_noun(", "--", "backend"], capture_output=True, text=True).stdout.split()
total = 0
for path in files:
    src = open(path, encoding="utf-8").read(); tree = ast.parse(src)
    b = src.encode("utf-8"); bl = [l.encode("utf-8") for l in src.splitlines(keepends=True)]
    off = lambda ln, col: sum(len(x) for x in bl[:ln - 1]) + col
    reps = []
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and getattr(n.func, "id", None) == "derived" and n.args
                and isinstance(n.args[0], ast.Call) and getattr(n.args[0].func, "id", None) == "count_noun"):
            inner = n.args[0]; seg = lambda x: ast.get_source_segment(src, x)
            plural = seg(inner.args[1])
            srckw = [k for k in n.keywords if k.arg == "src"]
            assert not [k for k in n.keywords if k.arg == "why"], path
            new = (f"S({seg(inner)}, E((count_noun(1, {plural}), {plural}), \"the noun or its singular (dna.base.count_noun)\")"
                   + (f", src={seg(srckw[0].value)}" if srckw else "") + ")")
            reps.append((off(n.lineno, n.col_offset), off(n.end_lineno, n.end_col_offset), new))
    for s, e, t in sorted(reps, reverse=True):
        b = b[:s] + t.encode("utf-8") + b[e:]
    open(path, "w", encoding="utf-8").write(b.decode("utf-8")); total += len(reps); print(path, len(reps))
print("total", total)
