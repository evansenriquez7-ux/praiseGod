"""Guard against a dict literal defining the same key twice in a pipeline registry.

Python resolves a duplicate key silently: the last one wins and the earlier entry is
discarded with no error, no warning, and no trace at runtime. Nothing in the harness can
see it, because by the time the module is imported the duplicate is already gone -- the
only place the evidence survives is the source text. So this reads the AST rather than
the imported object.

Found live in adapter.py, where FORMATTER_ROUTES defined "grid_area" twice: once routing
to fmt_bar_chart.format_bar_chart and again, 25 lines later, to
fmt_array_grid.format_array_grid. The bar-chart route had never run and nothing said so.

Exits non-zero when any duplicate is found. Add registries here as they are created.
"""
import ast
import collections
import sys

REGISTRY_FILES = [
    "backend/app/practice_gen/adapter.py",
    "backend/app/practice_gen/compatibility.py",
    "backend/app/practice_gen/registry.py",
    "backend/app/practice_gen/axes_catalog.py",
    "backend/app/practice_gen/validation/_manifest.py",
    "backend/app/practice_gen/validation/validate_capability.py",
]


def dict_assignments(tree):
    """Yield (name, ast.Dict) for every module-level dict literal, annotated or not."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Dict):
            target, value = node.target, node.value
        else:
            continue
        name = getattr(target, "id", None)
        if name:
            yield name, value


def main():
    findings = 0
    for path in REGISTRY_FILES:
        try:
            source = open(path).read()
        except FileNotFoundError:
            print(f"MISSING  {path} — listed in REGISTRY_FILES but not on disk")
            findings += 1
            continue
        for name, node in dict_assignments(ast.parse(source)):
            keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
            for key, count in collections.Counter(keys).items():
                if count == 1:
                    continue
                lines = [k.lineno for k in node.keys
                         if isinstance(k, ast.Constant) and k.value == key]
                print(f"DUPLICATE  {path}")
                print(f"    {name}[{key!r}] defined {count} times, at lines {lines}")
                print(f"    Python keeps only the last; every earlier entry is dead code.")
                findings += 1
    if findings:
        print(f"\n{findings} duplicate registry key(s).")
        return 1
    print(f"No duplicate keys in {len(REGISTRY_FILES)} registry file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
