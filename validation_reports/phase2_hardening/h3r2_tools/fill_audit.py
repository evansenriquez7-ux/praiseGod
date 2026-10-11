"""Static audit: every S(<name>, "fill") slot -- is EVERY assignment to <name> in its function fill-producing?"""
import ast, sys, subprocess
FILLERS = {"fill", "transform", "record", "resolve", "decompose_to_places", "with_article", "answer_text",
           "member_text", "distractor_text", "correct_option_key"}
def is_fillish(v, assigns, seen=()):
    if isinstance(v, ast.IfExp):
        return is_fillish(v.body, assigns, seen) and is_fillish(v.orelse, assigns, seen)
    if isinstance(v, ast.Call):
        f = v.func; n = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
        return n in FILLERS
    if isinstance(v, ast.Name):
        if v.id in seen: return True
        vals = assigns.get(v.id)
        return bool(vals) and all(is_fillish(x, assigns, seen + (v.id,)) for x in vals)
    return False
files = subprocess.run(["git", "ls-files", "backend/app/practice_gen/dna", "backend/app/practice_gen/formatters",
                        "backend/app/practice_gen/generators", "backend/app/practice_gen/slots.py"],
                       capture_output=True, text=True).stdout.split()
bad = 0
for path in files:
    if not path.endswith(".py"): continue
    tree = ast.parse(open(path).read())
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)): continue
        assigns, params = {}, {a.arg for a in fn.args.args + fn.args.kwonlyargs}
        for n in ast.walk(fn):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name): assigns.setdefault(t.id, []).append(n.value)
                    elif isinstance(t, ast.Tuple):
                        for e in t.elts:
                            if isinstance(e, ast.Name): assigns.setdefault(e.id, []).append(None)
            elif isinstance(n, (ast.AugAssign, ast.For)) :
                tgt = n.target
                for e in ast.walk(tgt):
                    if isinstance(e, ast.Name): assigns.setdefault(e.id, []).append(None)
        for c in ast.walk(fn):
            if isinstance(c, ast.Call) and getattr(c.func, "id", None) == "S" and len(c.args) == 2 \
                    and isinstance(c.args[1], ast.Constant) and c.args[1].value == "fill":
                x = c.args[0]
                ok = True
                if isinstance(x, ast.Name):
                    if x.id in params and x.id not in assigns:
                        ok = None   # a parameter: depends on the caller
                    else:
                        vals = assigns.get(x.id, [])
                        ok = bool(vals) and all(v is not None and is_fillish(v, assigns) for v in vals)
                elif isinstance(x, ast.Call):
                    ok = is_fillish(x, assigns) or None
                else:
                    ok = None
                if ok is False:
                    bad += 1
                    print(f"NOT-ALWAYS-FILL {path}:{c.lineno} {ast.get_source_segment(open(path).read(), x)[:60]}")
                elif ok is None and "--all" in sys.argv:
                    print(f"UNKNOWN {path}:{c.lineno} {ast.get_source_segment(open(path).read(), x)[:60]}")
print("flagged", bad)
