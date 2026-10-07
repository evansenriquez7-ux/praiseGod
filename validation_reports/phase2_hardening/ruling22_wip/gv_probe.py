"""Read-only: render student-path samples for a node and summarise its structured given_values.

Usage: PYTHONPATH=. .venv/bin/python <this> <node_id> [n_seeds] [profile_json]
Prints each given_values path with its value distribution (scalars only, lists flattened).
"""
import collections
import json
import sys

from backend.app.practice_gen.validation.judgment_packets import _render_sample


def walk(value, prefix, out):
    if isinstance(value, dict):
        for k, v in value.items():
            walk(v, f"{prefix}.{k}" if prefix else str(k), out)
    elif isinstance(value, (list, tuple)):
        if all(not isinstance(v, (dict, list, tuple)) for v in value):
            out[prefix + "[]"].append(json.dumps(sorted(map(str, value)))[:80])
            for v in value:
                out[prefix + "[*]"].append(str(v)[:60])
        else:
            for v in value:
                walk(v, prefix + "[*]", out)
    else:
        out[prefix].append(str(value)[:60])


def main():
    node = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    profile = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    out = collections.defaultdict(list)
    rendered = 0
    for seed in range(1000, 1000 + n):
        s = _render_sample(node, seed, difficulty_profile=profile,
                           include_private_variant_evidence=True)
        if s is None:
            continue
        rendered += 1
        walk(s.get("_provider_variant_evidence") or {}, "", out)
    print(f"{node}: {rendered}/{n} rendered")
    for path in sorted(out):
        c = collections.Counter(out[path])
        if len(c) > 12:
            print(f"  {path:<40} {len(c)} distinct, e.g. {list(c)[:4]}")
        else:
            print(f"  {path:<40} {dict(c)}")


if __name__ == "__main__":
    main()
