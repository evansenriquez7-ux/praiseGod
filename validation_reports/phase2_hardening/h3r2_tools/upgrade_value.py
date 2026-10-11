"""
Observe every recorded fill on the student path (all lcs x validate_slots.SEEDS) and propose
`derived(x)` -> `S(x, "value:<key>")` upgrades where, in EVERY observation of that
(site, slot), the slot value equals the generator's own values[key] for exactly one key.
Small integers (|v| <= 12) and booleans are excluded: they match unrelated keys by chance.
Writes proposals as JSON; --apply rewrites the sources.
"""
import json, sys, collections, re
from backend.app.practice_gen.validation import validate_slots as VS
from backend.app.practice_gen.registry import get_all_node_ids


def observe():
    from backend.app.services.orchestrator import PracticeOrchestrator
    from backend.app.services import orchestrator as _orch
    from backend.app.practice_gen.slots import capture
    obs = collections.defaultdict(list)       # (site, slot) -> [(value, values-dict)]
    from backend.app.practice_gen.registry import get_node_formatters
    for n in sorted(get_all_node_ids()):
        runs = [(seed, None) for seed in range(1, 41)] + [
            (seed, f) for f in sorted(get_node_formatters(n) or []) for seed in (3, 17, 29)]
        for seed, fmt in runs:
            seen = {}
            real = _orch.apply_formatter
            def spy(ctx, f, rng):
                seen.update(ctx.values or {}); return real(ctx, f, rng)
            _orch.apply_formatter = spy
            try:
                with capture() as fills:
                    PracticeOrchestrator.generate_problem(node_id=n, seed=seed, formatter=fmt,
                                                          is_student_path=fmt is None)
            except Exception:
                continue
            finally:
                _orch.apply_formatter = real
            texts = collections.Counter(g.text for g in fills)
            for f in fills:
                for name, value, domain in f.slots:
                    if domain in ("num.derived", "text.derived"):
                        other = isinstance(value, str) and texts.get(value, 0) > (1 if value == f.text else 0)
                        obs[(f.site, name)].append((value, dict(seen), other))
    return obs


def propose(obs):
    out = []
    for (site, name), items in obs.items():
        if len(items) < 5:
            continue
        if all(isinstance(v, str) and other for v, _vals, other in items):
            out.append({"site": site, "slot": name, "key": "__fill__", "n": len(items)})
            continue
        cands = None
        for value, vals, _other in items:
            if isinstance(value, bool) or (isinstance(value, (int, float)) and abs(value) <= 12):
                cands = set(); break
            keys = {k for k, v in vals.items() if type(v) == type(value) and v == value}
            cands = keys if cands is None else cands & keys
            if not cands:
                break
        if cands and len(cands) == 1:
            out.append({"site": site, "slot": name, "key": next(iter(cands)), "n": len(items)})
    return out


def apply(props):
    by_file = collections.defaultdict(list)
    for p in props:
        path, line = p["site"].rsplit(":", 1)
        by_file[path].append((int(line), p["slot"], p["key"]))
    done = 0
    for path, items in by_file.items():
        lines = open(path, encoding="utf-8").read().split("\n")
        for line, slot, key in items:
            # the call may span lines: search the line and up to 6 following
            for i in range(line - 1, min(line + 6, len(lines))):
                pat = re.compile(r"\b" + re.escape(slot) + r"=derived\(")
                m = pat.search(lines[i])
                if not m:
                    continue
                # find matching paren of derived(
                j = m.end(); depth = 1
                while j < len(lines[i]) and depth:
                    depth += {"(": 1, ")": -1}.get(lines[i][j], 0); j += 1
                if depth:
                    break
                expr = lines[i][m.end():j - 1]
                if key == "__fill__":
                    expr = re.sub(r",\s*src=\([^)]*\)\s*$", "", expr)
                    lines[i] = lines[i][:m.start()] + f'{slot}=S({expr}, "fill")' + lines[i][j:]
                    done += 1
                    break
                if "src=" in expr:
                    break
                lines[i] = lines[i][:m.start()] + f'{slot}=S({expr}, "value:{key}")' + lines[i][j:]
                done += 1
                break
        open(path, "w", encoding="utf-8").write("\n".join(lines))
    return done


if __name__ == "__main__":
    out = sys.argv[1]
    if "--apply" in sys.argv:
        props = json.load(open(out))
        print("applied", apply(props), "of", len(props))
    else:
        props = propose(observe())
        json.dump(props, open(out, "w"), indent=1)
        print(len(props), "proposal(s)")
        for p in props[:40]:
            print(" ", p)
