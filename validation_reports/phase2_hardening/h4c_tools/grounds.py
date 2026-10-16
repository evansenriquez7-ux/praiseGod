"""Ruling 49 helper: for one lc, print the standing confirmed review's failing templates and what renders printed for each.
usage: python3 local_only/scratch/h4c/grounds.py NODE_ID [MAX_TEXTS]"""
import glob, json, sys
nid = sys.argv[1]; mx = int(sys.argv[2]) if len(sys.argv) > 2 else 12
recs = sorted(glob.glob(f"validation_reports/stem_review/{nid}/stem-batch44*-confirming*.json"))
if not recs: sys.exit(f"{nid}: no confirming record")
# the standing record is the latest filed (validate_stem_review reads the latest-filed record per lc)
recs = sorted(recs, key=lambda f: json.load(open(f))["filed_at"])
rec = json.load(open(recs[-1])); recs = [recs[-1]]
r = json.loads(rec["raw_reply"])
d = json.load(open(f"local_only/scratch/h4c/renders/{nid}.json"))
print(f"## {nid}  {recs[0].split('/')[-1]}  overall={r.get('overall')}")
print("REASONING:", r.get("reasoning", "")[:1500])
for t in r.get("failing_templates", []):
    e = d["templates"].get(t)
    if e is None:
        print(f"-- {t!r}: NOT RENDERED in {len(d['problems'])} renders"); continue
    texts = list(e["texts"].items())
    print(f"-- {t!r}: {len(texts)} distinct")
    for x, w in texts[:mx]: print(f"     [{w}] {x[:220]}")
