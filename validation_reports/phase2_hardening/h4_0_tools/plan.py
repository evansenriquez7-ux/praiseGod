"""plan.py FINDINGS.json OBS.json N  -> the pairs the greedy first-N lcs need, grouped by file, with code + obs."""
import json, collections, re, sys, linecache
f = json.load(open(sys.argv[1])); obs = json.load(open(sys.argv[2])); N = int(sys.argv[3])
skip = set(sys.argv[4].split(",")) if len(sys.argv) > 4 else set()
per = collections.defaultdict(set)
for i in f["slot_domain_type_only_14"]:
    m = re.match(r"(\S+): (\S+) slot '([^']+)' at seed", i); per[m.group(1)].add((m.group(2), m.group(3)))
chosen = set(); done = []
while len(done) < N and len(done) < len(per):
    c, k = min((len(v - chosen), k) for k, v in per.items() if k not in done)
    chosen |= per[k]; done.append(k)
print("LCS", ",".join(done)); print("PAIRS", len(chosen))
by = collections.defaultdict(list)
for site, slot in chosen: by[site.rsplit(":", 1)[0]].append((int(site.rsplit(":", 1)[1]), slot, site))
for path in sorted(by):
    print("=" * 30, path)
    for line, slot, site in sorted(by[path]):
        o = obs.get(f"{site}|{slot}", {})
        code = linecache.getline(path, line).strip()[:150]
        print(f"{line:5d} {slot:14s} eq={o.get('eq')} fill={o.get('allfill')} src={o.get('src')} n={o.get('n')} lcs={len(o.get('lcs',[]))}")
        print(f"       vals={str(o.get('vals'))[:160]}")
        print(f"       | {code}")
