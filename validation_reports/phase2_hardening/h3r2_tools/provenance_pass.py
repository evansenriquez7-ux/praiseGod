"""
Provenance pass over instrumented generator files (batch H3-R2).

(A) value: upgrade -- `slot=derived(x)` becomes `slot=S(x, "value:k")` when x's REACHING
    definition (nearest preceding assignment walking back through enclosing blocks; any
    conditional/loop assignment in between stops the search) is `values["k"]` or
    `values.get("k")` with no default.
(B) template provenance -- each `fill(...)` gets `_src=(...)`: the `values` keys read by the
    tests of the `if` statements / conditional expressions that enclose it (control
    dependence: the generator chose this template because of those values).

usage: provenance_pass.py FILE [--dry]
"""
import ast, sys

VALUES = {"values"}


def values_key(node, allow_default):
    def is_values(n):
        return (isinstance(n, ast.Name) and n.id in VALUES) or \
               (isinstance(n, ast.Attribute) and n.attr == "values") or \
               (isinstance(n, ast.BoolOp) and any(is_values(v) for v in n.values))
    if isinstance(node, ast.Subscript) and is_values(node.value) and isinstance(node.slice, ast.Constant) \
            and isinstance(node.slice.value, str):
        return node.slice.value
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" \
            and is_values(node.func.value) and node.args and isinstance(node.args[0], ast.Constant) \
            and isinstance(node.args[0].value, str) and (allow_default or (len(node.args) == 1 and not node.keywords)):
        return node.args[0].value
    return None


def default_chain(node):
    """Keys of values.get("k", values.get("k2", ...)): every key the value may come from."""
    keys = []
    while True:
        k = values_key(node, allow_default=True)
        if not k:
            break
        keys.append(k)
        if isinstance(node, ast.Call) and len(node.args) > 1:
            node = node.args[1]
        else:
            break
    return tuple(keys)


def assigns(stmt, name):
    """'direct' if stmt directly assigns name; 'inside' if a nested statement does; None otherwise."""
    if isinstance(stmt, ast.Assign):
        for t in stmt.targets:
            for x in ast.walk(t):
                if isinstance(x, ast.Name) and x.id == name:
                    return "direct"
    if isinstance(stmt, (ast.AugAssign, ast.AnnAssign)) and isinstance(stmt.target, ast.Name) and stmt.target.id == name:
        return "inside"   # an augmented assignment changes the value: not a clean reaching def
    for x in ast.walk(stmt):
        if x is stmt:
            continue
        if isinstance(x, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.For, ast.comprehension, ast.With,
                          ast.NamedExpr)):
            targets = []
            if isinstance(x, ast.Assign):
                targets = x.targets
            elif isinstance(x, (ast.AugAssign, ast.AnnAssign, ast.NamedExpr)):
                targets = [x.target]
            elif isinstance(x, (ast.For, ast.comprehension)):
                targets = [x.target]
            for t in targets:
                for y in ast.walk(t):
                    if isinstance(y, ast.Name) and y.id == name:
                        return "inside"
    return None


class Pass:
    def __init__(self, src):
        self.src = src
        self.tree = ast.parse(src)
        self._stored = {}
        self.parents = {}
        for n in ast.walk(self.tree):
            for c in ast.iter_child_nodes(n):
                self.parents[c] = n

    def stmt_of(self, node):
        n = node
        while n is not None and not isinstance(self.parents.get(n), (ast.Module,)) and not self._in_body(n):
            n = self.parents.get(n)
        return n

    def _in_body(self, n):
        p = self.parents.get(n)
        if p is None:
            return False
        for field in ("body", "orelse", "finalbody", "handlers"):
            seq = getattr(p, field, None)
            if isinstance(seq, list) and any(n is x for x in seq):
                return True
        return False

    def reaching(self, node, name, allow_default=False):
        """values key of name's reaching definition from node's statement, or None."""
        st = self.stmt_of(node)
        while st is not None:
            p = self.parents.get(st)
            if p is None:
                return None
            body = None
            for field in ("body", "orelse", "finalbody"):
                seq = getattr(p, field, None)
                if isinstance(seq, list) and any(st is x for x in seq):
                    body = seq
            if body is None:
                st = p; continue
            idx = next(i for i, x in enumerate(body) if x is st)
            for prev in reversed(body[:idx]):
                a = assigns(prev, name)
                if a == "direct" and isinstance(prev, ast.Assign) and len(prev.targets) == 1 \
                        and isinstance(prev.targets[0], ast.Name):
                    return values_key(prev.value, allow_default)
                if a:
                    return None
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return None
            st = p
        return None

    def stored_names(self, fn):
        """Locals the function stores under their own name in a dict literal ("k": k)."""
        if fn not in self._stored:
            names = set()
            for d in ast.walk(fn):
                if isinstance(d, ast.Dict):
                    for k, v in zip(d.keys, d.values):
                        # a key the function writes into the values it returns: a local of the
                        # same name that a test reads is that value's choice
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            names.add(k.value)
            self._stored[fn] = names
        return self._stored[fn]

    def enclosing_fn(self, n):
        p = self.parents.get(n)
        while p is not None and not isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
            p = self.parents.get(p)
        return p

    def test_keys(self, test, at):
        keys = []
        fn = self.enclosing_fn(at)
        for x in ast.walk(test):
            k = values_key(x, allow_default=True)
            if k:
                keys.append(k)
            elif isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                k = self.reaching(at, x.id, allow_default=True)
                if k:
                    keys.append(k)
                elif fn is not None and x.id in self.stored_names(fn):
                    keys.append(x.id)
        return keys

    def slot_keys(self, expr, at, depth=4):
        """Data dependence: every values key the expression reads, following locals through
        their reaching definitions (depth-limited)."""
        keys = []
        for x in ast.walk(expr):
            chain = default_chain(x)
            if chain:
                keys += chain
            elif isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load) and depth > 0:
                d = self.reaching_def(at, x.id)
                if d is not None:
                    keys += self.slot_keys(d, d, depth - 1)
        return tuple(dict.fromkeys(keys))

    def _slot_keys_old(self, expr, at):
        """values keys a slot expression derives from: a values read (default allowed), or a
        local whose reaching definition is such a read or a conditional testing values."""
        chain = default_chain(expr)
        if chain:
            return chain
        if isinstance(expr, ast.Name):
            st = self.stmt_of(at)
            d = self.reaching_def(at, expr.id)
            if d is None:
                return ()
            chain = default_chain(d)
            if chain:
                return chain
            if isinstance(d, ast.IfExp):
                return tuple(dict.fromkeys(self.test_keys(d.test, d)))
        return ()

    def reaching_def(self, node, name):
        """The value expression of name's reaching definition (or None)."""
        st = self.stmt_of(node)
        while st is not None:
            p = self.parents.get(st)
            if p is None:
                return None
            body = None
            for field in ("body", "orelse", "finalbody"):
                seq = getattr(p, field, None)
                if isinstance(seq, list) and any(st is x for x in seq):
                    body = seq
            if body is None:
                st = p; continue
            idx = next(i for i, x in enumerate(body) if x is st)
            for prev in reversed(body[:idx]):
                a = assigns(prev, name)
                if a == "direct" and isinstance(prev, ast.Assign) and len(prev.targets) == 1 \
                        and isinstance(prev.targets[0], ast.Name):
                    return prev.value
                if a:
                    return None
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return None
            st = p
        return None

    def control_keys(self, call):
        keys = []
        child, p = call, self.parents.get(call)
        while p is not None and not isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            # TRUE branch only: a fill in an if's body was chosen because the test held; a
            # fill in its else (a fallback) shows no particular value of what was tested.
            if isinstance(p, ast.If) and any(child is x for x in p.body):
                keys += self.test_keys(p.test, p)
            elif isinstance(p, ast.IfExp) and child is p.body:
                keys += self.test_keys(p.test, p)
            child, p = p, self.parents.get(p)
        return tuple(dict.fromkeys(keys))

    def run(self):
        edits = []   # (start, end, text)
        lines = self.src.splitlines(keepends=True)
        offs = [0]
        for l in lines:
            offs.append(offs[-1] + len(l.encode("utf-8")))
        pos = lambda ln, col: offs[ln - 1] + col
        nA = nB = 0
        for call in ast.walk(self.tree):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "fill"
                    and call.args):
                continue
            # (A)
            for kw in call.keywords:
                v = kw.value
                if kw.arg and isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "derived" \
                        and len(v.args) == 1 and not v.keywords and isinstance(v.args[0], ast.Name):
                    k = self.reaching(call, v.args[0].id)
                    if k:
                        edits.append((pos(v.lineno, v.col_offset), pos(v.end_lineno, v.end_col_offset),
                                      f'S({v.args[0].id}, "value:{k}")'))
                        nA += 1
            # (A') provenance without a value: claim -- a derived(x) slot whose x was read from
            # values with a default, or chosen by a conditional on values, names those keys.
            for kw in call.keywords:
                v = kw.value
                if kw.arg and isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "derived" \
                        and len(v.args) == 1 and not v.keywords:
                    keys = self.slot_keys(v.args[0], call)
                    if keys:
                        at = pos(v.args[0].end_lineno, v.args[0].end_col_offset)
                        edits.append((at, at, ", src=(" + ", ".join(repr(k) for k in keys) + ",)"))
                        nA += 1
            # (B)
            if any(kw.arg == "_src" for kw in call.keywords):
                continue
            keys = self.control_keys(call)
            if keys:
                t = call.args[0]
                at = pos(t.end_lineno, t.end_col_offset)
                edits.append((at, at, ", _src=(" + ", ".join(repr(k) for k in keys) + ",)"))
                nB += 1
        b = self.src.encode("utf-8")
        for s, e, txt in sorted(edits, reverse=True):
            b = b[:s] + txt.encode("utf-8") + b[e:]
        out = b.decode("utf-8")
        ast.parse(out)
        return out, nA, nB


if __name__ == "__main__":
    path = sys.argv[1]
    src = open(path, encoding="utf-8").read()
    out, nA, nB = Pass(src).run()
    print(f"{path}: value-upgrades {nA}, template-src {nB}")
    if "--dry" not in sys.argv and out != src:
        open(path, "w", encoding="utf-8").write(out)
