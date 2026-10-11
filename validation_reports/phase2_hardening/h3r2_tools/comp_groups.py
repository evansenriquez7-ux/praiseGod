import re, collections, sys
rows=[l for l in open(sys.argv[1]) if l.startswith("selector_value")]
g=collections.OrderedDict()
for l in rows:
    m=re.search(r"\| (mat_\w+): (\S+)/(\w+) at seed (\d+) \((\d+) of.*?selected by (\[.*?\]), but no non-hint learner-read text is derived from (\[[^\]]*\]).*?the item shows (.*?), and only", l)
    lc, member, fmt, seed, nseeds, sel, paths, shows = m.groups()
    g.setdefault((paths, lc, fmt), []).append((member, seed, re.sub(r"'path': |'equals': ","",sel)[:50], shows[:105]))
for (paths, lc, fmt), v in sorted(g.items()):
    print(f"{paths:20s} {lc:16s} {fmt:18s} n={len(v)} {v[0][2]} | {v[0][3]} @{v[0][1]}")
print(len(rows), "findings in", len(g), "groups")
