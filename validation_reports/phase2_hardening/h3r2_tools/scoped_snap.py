"""
Scoped byte-identity check: re-render only the given lcs exactly as tests/render_snapshot
does (same _render, same seeds, PYTHONHASHSEED=0) and compare with a full baseline file.
  PYTHONPATH=. .venv/bin/python local_only/scratch/h3r2/scoped_snap.py BASE.jsonl lc1,lc2|--dna name|--all-of FILE
"""
import json, os, sys
if os.environ.get("PYTHONHASHSEED") != "0":
    os.execve(sys.executable, [sys.executable, *sys.argv], {**os.environ, "PYTHONHASHSEED": "0"})
from tests.render_snapshot import _render, STUDENT_SEEDS, PINNED_SEEDS

def lcs_for_dna(dna):
    from backend.app.practice_gen.registry import get_all_node_ids, get_node_dnas
    return sorted(n for n in get_all_node_ids() if dna in (get_node_dnas(n) or []))

if __name__ == "__main__":
    base_path, spec = sys.argv[1], sys.argv[2]
    from backend.app.practice_gen.registry import get_node_formatters
    if spec == "--dna":
        lcs = sorted({n for d in sys.argv[3].split(",") for n in lcs_for_dna(d)})
    else:
        lcs = spec.split(",")
    base = {}
    for line in open(base_path, encoding="utf-8"):
        k = json.loads(line)["k"]
        if k[0] in lcs: base[json.dumps(k)] = line
    changed, n = [], 0
    for node_id in lcs:
        keys = [(node_id, s, None) for s in STUDENT_SEEDS] + [
            (node_id, s, f) for f in sorted(get_node_formatters(node_id) or []) for s in PINNED_SEEDS]
        for (nid, seed, fmt) in keys:
            line = json.dumps({"k": [nid, seed, fmt], "r": _render(nid, seed, fmt)},
                              sort_keys=True, default=str, ensure_ascii=False) + "\n"
            k = json.dumps([nid, seed, fmt]); n += 1
            if base.get(k) != line: changed.append(k)
    print(f"scoped_snap: {len(lcs)} lc(s), {n} render(s), {len(changed)} changed, baseline had {len(base)}")
    for k in changed[:15]: print("  -", k)
    sys.exit(1 if changed or n != len(base) else 0)
