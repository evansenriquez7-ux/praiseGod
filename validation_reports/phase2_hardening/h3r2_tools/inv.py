"""Full-tree §14 inventory: label family counts + one example per (dna, formatter, field)."""
import json, collections, re, sys, subprocess
if __name__ == "__main__":
    out = sys.argv[1]
    subprocess.run([sys.executable, "local_only/scratch/h3r2/per_render.py", out], check=True)
    rows = [json.loads(l) for l in open(out)]
    for lab in ("slot_text_unaccounted_14", "slot_domain_escape_14", "slot_template_mismatch_14",
                "slot_unclassified_14", "slot_domain_unknown_14"):
        print(lab, len({(r["lc"], r["where"]) for r in rows if r["label"] == lab}))
    show = sys.argv[2] if len(sys.argv) > 2 else "slot_text_unaccounted_14"
    g = collections.OrderedDict()
    for r in rows:
        if r["label"] != show: continue
        t = re.search(r"^(?:nested slot value )?(['\"])(.*?)\1 is not", r["reason"]); t = t.group(2) if t else r["reason"][:110]
        k = (r["dna"] or "-", r["formatter"] or "nested", r["where"].split("practice_gen/")[-1])
        g.setdefault(k, {"lcs": set(), "ex": []}); g[k]["lcs"].add(r["lc"])
        if len(g[k]["ex"]) < 2 and t not in [e[2] for e in g[k]["ex"]]: g[k]["ex"].append((r["lc"], r["seed"], t))
    for k, v in sorted(g.items()):
        print(f"{k[0]:20s} {k[1]:20s} {k[2][:44]:44s} lcs={len(v['lcs'])} | " + " || ".join(f"{e[2][:70]!r}@{e[0]}:{e[1]}" for e in v["ex"]))
