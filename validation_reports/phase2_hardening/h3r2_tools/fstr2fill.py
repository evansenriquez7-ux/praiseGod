"""
Rewrite learner-text f-strings (and chosen plain strings) inside named functions into
`slots.fill(template, name=S(expr, domain), ...)` -- byte-identical by construction
(`template.format(**slots)` == the f-string), proven afterwards by the snapshot.

Domains are inferred conservatively and NEVER guessed loosely:
  * `values["k"]` / `values.get("k")` (no default), or a local bound to one   -> "value:k"
  * a local returned in a dict literal as `"k": local` (generate_params)        -> "value:k"
  * a local bound to `<VocabGated>.resolve(...)`, or a nested fill            -> "fill"
  * a local bound to `rng.choice(MODULE_CONST)`                                -> "enum:<mod>.CONST"
  * anything else -> `derived(expr)` (num.derived / text.derived by runtime type)
`value:` claims are checked at runtime by §14 (an escape if wrong), so a bad inference is
loud, never silent.

usage: fstr2fill.py FILE func1,func2,...|ALL [--consts] [--dry]
"""
import ast, re, sys

SKIP_CALLS = {"print", "warn", "debug", "info", "warning", "error", "exception", "critical",
              "ValueError", "RuntimeError", "KeyError", "TypeError", "AssertionError",
              "NotImplementedError", "IndexError", "Exception", "LookupError"}
SKIP_KWARGS = {"problem_id"}
VALUES_NAMES = {"values"}   # plus `<x>.values`; never a visual-params or local dict
LEARNER_DICT_KEYS = {"question", "question_text", "statement", "question_statement",
                     "question_with_blank", "prompt", "sentence", "instruction"}


def _ident(expr_src, node):
    if isinstance(node, ast.Name):
        base = node.id
    elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        base = node.slice.value
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" \
            and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        base = node.args[0].value
    elif isinstance(node, ast.Attribute):
        base = node.attr
    elif isinstance(node, ast.Call):
        f = node.func
        base = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "v")
    else:
        base = "v"
    base = re.sub(r"\W", "_", base).strip("_") or "v"
    if base[0].isdigit():
        base = "v_" + base
    if base in ("self",):
        base = "v"
    return base


def _values_key(node):
    """'k' if node is values["k"] / values.get("k") (no default) / ctx.values[...]."""
    def is_values(n):
        return (isinstance(n, ast.Name) and n.id in VALUES_NAMES) or \
               (isinstance(n, ast.Attribute) and n.attr == "values")
    if isinstance(node, ast.Subscript) and is_values(node.value) and isinstance(node.slice, ast.Constant) \
            and isinstance(node.slice.value, str):
        return node.slice.value
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" \
            and is_values(node.func.value) and len(node.args) == 1 and not node.keywords \
            and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        return node.args[0].value
    return None


FILL_FUNCS = {"fill", "decompose_to_places", "with_article", "transform", "record"}
SKIP_ASSIGN = re.compile(r"(^|_)(key|id|ids|path|name_key)$")


def _is_fill_expr(val):
    """A call that returns a recorded fill, or a conditional choosing between such calls."""
    if isinstance(val, ast.IfExp):
        return _is_fill_expr(val.body) and _is_fill_expr(val.orelse)
    if isinstance(val, ast.JoinedStr):
        return True   # converted to a fill in this same pass
    if isinstance(val, ast.Call):
        f = val.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        return name in FILL_FUNCS or name == "resolve"
    return False


class FuncInfo:
    def __init__(self, fn, module_consts):
        self.var_domain = {}
        reassigned = {}
        for n in ast.walk(fn):
            targets = []
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        targets.append((t.id, n.value))
                    elif isinstance(t, ast.Tuple) and isinstance(n.value, ast.Tuple) and len(t.elts) == len(n.value.elts):
                        targets += [(a.id, b) for a, b in zip(t.elts, n.value.elts) if isinstance(a, ast.Name)]
                    elif isinstance(t, ast.Tuple):
                        for a in t.elts:
                            if isinstance(a, ast.Name):
                                targets.append((a.id, None))
            elif isinstance(n, (ast.AugAssign, ast.AnnAssign)) and isinstance(getattr(n, "target", None), ast.Name):
                targets.append((n.target.id, getattr(n, "value", None)))
            elif isinstance(n, (ast.For, ast.comprehension)):
                for t in ast.walk(n.target):
                    if isinstance(t, ast.Name):
                        targets.append((t.id, None))
            for name, val in targets:
                reassigned[name] = reassigned.get(name, 0) + 1
                dom = None
                if val is not None and not isinstance(n, ast.AugAssign):
                    k = _values_key(val)
                    if k:
                        dom = f'"value:{k}"'
                    elif isinstance(val, ast.Call) and isinstance(val.func, ast.Attribute) and val.func.attr == "resolve":
                        dom = '"fill"'
                    elif _is_fill_expr(val):
                        dom = '"fill"'
                    elif isinstance(val, ast.Call) and isinstance(val.func, ast.Attribute) and val.func.attr == "choice" \
                            and len(val.args) == 1 and isinstance(val.args[0], ast.Name) and val.args[0].id in module_consts:
                        dom = f'"enum:{module_consts[val.args[0].id]}"'
                self.var_domain.setdefault(name, []).append(dom)
        # (A return-dict inference -- "a local returned as 'k': local repeats values[k]" --
        # was tried and dropped: with several return paths and candidate loops it claimed
        # value:<k> for locals a later branch replaced. Precision over recall: such slots
        # are derived, and only a direct read of the generated values is a value: slot.)

    def domain(self, node):
        k = _values_key(node)
        if k:
            return f'"value:{k}"'
        if isinstance(node, ast.Call):
            f = node.func
            fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if fname in FILL_FUNCS or (fname == "resolve"):
                return '"fill"'
        if isinstance(node, ast.Name) and node.id in self.var_domain:
            doms = self.var_domain[node.id]
            assigned = [d for d in doms if d is None or not d.endswith("#dict")]
            dict_doms = {d[:-5] for d in doms if d and d.endswith("#dict")}
            # Single assignment with a known domain wins; a dict-return claim only when the
            # name is assigned once and the dict maps it to ONE key.
            if assigned and assigned[0] is not None and all(d == assigned[0] for d in assigned):
                return assigned[0]
            if len(assigned) <= 1 and len(dict_doms) == 1 and (not assigned or assigned[0] is None):
                return next(iter(dict_doms))
        return None


def module_constants(tree, modname):
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) \
                and isinstance(n.value, (ast.List, ast.Tuple)) \
                and all(isinstance(e, ast.Constant) for e in n.value.elts):
            out[n.targets[0].id] = f"{modname}.{n.targets[0].id}"
    return out


def convert(path, funcs, consts=False):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    modname = path.replace("/", ".")[:-3]
    mconsts = module_constants(tree, modname)
    parents = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parents[c] = n
    targets = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if funcs != ["ALL"] and fn.name not in funcs:
            continue
        # only the outermost function among selected (nested defs are walked inside)
        p = parents.get(fn)
        skip = False
        while p is not None:
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)) and (funcs == ["ALL"] or p.name in funcs):
                skip = True
            p = parents.get(p)
        if skip:
            continue
        info = FuncInfo(fn, mconsts)
        chains = []
        for n in ast.walk(fn):
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add) and not (
                    isinstance(parents.get(n), ast.BinOp) and isinstance(parents[n].op, ast.Add)):
                leaves = _flatten_add(n)
                if any(isinstance(l, ast.JoinedStr) for l in leaves) or \
                        sum(isinstance(l, ast.Constant) and isinstance(l.value, str) for l in leaves) >= 1 and \
                        any(isinstance(l, ast.JoinedStr) for l in leaves):
                    chains.append(n)
        in_chain = set()
        for c in chains:
            for l in ast.walk(c):
                in_chain.add(l)
            targets.append((c, info, "chain"))
        for n in ast.walk(fn):
            if n in in_chain:
                continue
            if isinstance(n, ast.JoinedStr):
                targets.append((n, info, "f"))
            elif consts and isinstance(n, ast.Constant) and isinstance(n.value, str) and _learner_const(n, parents):
                targets.append((n, info, "c"))
    # outermost JoinedStr only; skip excluded contexts
    def excluded(n):
        p = parents.get(n)
        child = n
        while p is not None:
            if isinstance(p, ast.JoinedStr):
                return True
            if isinstance(p, (ast.Raise, ast.Assert)):
                return True
            if isinstance(p, ast.Call):
                f = p.func
                name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                if name in SKIP_CALLS or name == "fill":
                    return True
            if isinstance(p, ast.keyword) and p.arg in SKIP_KWARGS:
                return True
            if isinstance(p, ast.Assign) and any(isinstance(t, ast.Name) and SKIP_ASSIGN.search(t.id) for t in p.targets):
                return True
            if isinstance(p, ast.Subscript) and child is p.slice:
                return True   # an f-string used as an index is a key, not learner text
            if isinstance(p, ast.Expr) and isinstance(child, ast.Constant):
                return True  # docstring / bare string statement
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return False
            child, p = p, parents.get(p)
        return False
    edits = []
    report = []
    for n, info, kind in targets:
        if excluded(n):
            continue
        if kind == "chain":
            pieces = []
            for leaf in _flatten_add(n):
                if isinstance(leaf, ast.JoinedStr):
                    pieces.extend(leaf.values)
                elif isinstance(leaf, ast.Constant) and isinstance(leaf.value, str):
                    pieces.append(leaf)
                else:
                    pieces.append(ast.FormattedValue(value=leaf, conversion=-1, format_spec=None))
            n_values = pieces
        else:
            n_values = getattr(n, "values", None)
        if kind == "c":
            text = n.value
            edits.append((n, f"fill({_pyrepr(text.replace('{', '{{').replace('}', '}}'))})"))
            continue
        parts, slots, names = [], [], {}
        ok = True
        for v in n_values:
            if isinstance(v, ast.Constant):
                parts.append(v.value.replace("{", "{{").replace("}", "}}"))
            elif isinstance(v, ast.FormattedValue):
                esrc = ast.get_source_segment(src, v.value)
                if esrc is None or "\n" in esrc and not esrc.strip():
                    ok = False; break
                esrc = " ".join(esrc.split()) if "\n" in esrc else esrc
                if esrc in names:
                    nm = names[esrc]
                else:
                    nm = _ident(esrc, v.value)
                    used = set(names.values())
                    base, i = nm, 2
                    while nm in used or nm in ("template",):
                        nm = f"{base}{i}"; i += 1
                    names[esrc] = nm
                    dom = info.domain(v.value)
                    slots.append((nm, esrc, dom))
                spec = ""
                if v.conversion != -1:
                    spec += "!" + chr(v.conversion)
                if v.format_spec is not None:
                    fs = v.format_spec
                    if any(isinstance(x, ast.FormattedValue) for x in fs.values):
                        ok = False; break
                    spec += ":" + "".join(x.value for x in fs.values)
                parts.append("{" + nm + spec + "}")
            else:
                ok = False; break
        if not ok:
            report.append(f"SKIPPED (dynamic spec) line {n.lineno}")
            continue
        template = "".join(parts)
        args = []
        for nm, esrc, dom in slots:
            if dom:
                args.append(f"{nm}=S({esrc}, {dom})")
            else:
                args.append(f"{nm}=derived({esrc})")
        call = f"fill({_pyrepr(template)}" + ("".join(", " + a for a in args)) + ")"
        edits.append((n, call))
        report.append(f"line {n.lineno}: {len(slots)} slot(s): " +
                      ", ".join(f"{nm}<-{dom or 'derived'}" for nm, _, dom in slots))
    return src, edits, report


def _flatten_add(n):
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
        return _flatten_add(n.left) + _flatten_add(n.right)
    return [n]


LEARNER_FUNC = re.compile(r"stem|question|prompt|_build|^format_|hint|_line|statement|sentence")
LEARNER_NAME = re.compile(r"question|stem|prompt|sentence|statement|^line\d|instruction")


def _enclosing_func(n, parents):
    p = parents.get(n)
    while p is not None and not isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
        p = parents.get(p)
    return p


def _learner_const(n, parents):
    if not n.value.strip() or len(n.value) < 2:
        return False
    p = parents.get(n)
    fn = _enclosing_func(n, parents)
    in_learner_fn = fn is not None and LEARNER_FUNC.search(fn.name)
    # `return "..."` / `x = "..."` (x a stem-like name) / an IfExp arm of either
    q = p
    if isinstance(q, ast.IfExp):
        q = parents.get(q)
    if in_learner_fn and isinstance(q, ast.Return) and " " in n.value:
        return True
    if isinstance(q, ast.Assign) and any(isinstance(t, ast.Name) and LEARNER_NAME.search(t.id) for t in q.targets) \
            and " " in n.value:
        return True
    # hints.append("...") / hints.extend([...]) / hints = ["...", ...] / return "..."
    if isinstance(p, ast.Call) and isinstance(p.func, ast.Attribute) and p.func.attr in ("append", "insert") \
            and isinstance(p.func.value, ast.Name) and "hint" in p.func.value.id:
        return True
    if isinstance(p, (ast.List, ast.Tuple)):
        gp = parents.get(p)
        if isinstance(gp, ast.Return):
            return True
        if isinstance(gp, ast.Assign) and any(isinstance(t, ast.Name) and "hint" in t.id for t in gp.targets):
            return True
        if isinstance(gp, ast.Call) and isinstance(gp.func, ast.Attribute) and gp.func.attr == "extend" \
                and isinstance(gp.func.value, ast.Name) and "hint" in gp.func.value.id:
            return True
    if isinstance(p, ast.Dict):
        for k, v in zip(p.keys, p.values):
            if v is n and isinstance(k, ast.Constant) and k.value in LEARNER_DICT_KEYS:
                return True
    return False


def _pyrepr(s):
    r = repr(s)
    if r.startswith("'") and '"' not in s:
        r = '"' + r[1:-1].replace("\\'", "'") + '"'
    return r


def apply(path, src, edits):
    lines = src.splitlines(keepends=True)
    offs = [0]
    for l in lines:
        offs.append(offs[-1] + len(l.encode("utf-8")))
    b = src.encode("utf-8")
    spans = []
    for n, rep in edits:
        s = offs[n.lineno - 1] + n.col_offset
        e = offs[n.end_lineno - 1] + n.end_col_offset
        spans.append((s, e, rep))
    spans.sort(reverse=True)
    for s, e, rep in spans:
        b = b[:s] + rep.encode("utf-8") + b[e:]
    out = b.decode("utf-8")
    out = ensure_import(out)
    ast.parse(out)
    open(path, "w", encoding="utf-8").write(out)


def ensure_import(src):
    need = {"S", "fill", "derived"}
    m = re.search(r"^from backend\.app\.practice_gen\.slots import ([^\n]+)$", src, re.M)
    if m:
        have = {x.strip() for x in m.group(1).split(",")}
        names = sorted(have | need)
        return src[:m.start()] + "from backend.app.practice_gen.slots import " + ", ".join(names) + src[m.end():]
    # insert after the last top-level import block line
    lines = src.split("\n")
    idx = 0
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            idx = node.end_lineno
    lines.insert(idx, "from backend.app.practice_gen.slots import S, derived, fill")
    return "\n".join(lines)


if __name__ == "__main__":
    path, funcs = sys.argv[1], sys.argv[2].split(",")
    consts = "--consts" in sys.argv
    src, edits, report = convert(path, funcs, consts)
    for r in report:
        print(r)
    print(f"{len(edits)} edit(s)")
    if "--dry" not in sys.argv and edits:
        apply(path, src, edits)
