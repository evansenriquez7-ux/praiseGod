"""Ruling 49/51 helper: compact view of the standing (latest-filed) confirming record of each lc and what its failing
templates printed. usage (repo root): python3 local_only/scratch/h4c/r49brief.py ITEM [ITEM ...]   e.g. S442-001"""
import glob, json, sys

H = "local_only/scratch/h4c"
keys = {}
for g in ("S441", "S442", "S443", "S444", "S445", "S446", "S447"):
    keys.update(json.load(open(f"{H}/keys/{g}.key.json")))
for item in sys.argv[1:]:
    nid = keys[item]["node_id"]
    fs = glob.glob(f"validation_reports/stem_review/{nid}/stem-batch44*-confirming*.json")
    rec = json.load(open(max(fs, key=lambda f: json.load(open(f))["filed_at"])))
    r = json.loads(rec["raw_reply"])
    d = json.load(open(f"{H}/renders/{nid}.json"))
    print(f"## {item} {nid} {rec['dispatch_id']} overall={r['overall']} renders={len(d['problems'])}")
    print("R:", r.get("reasoning", "")[:1100])
    for t in r.get("failing_templates", []):
        e = d["templates"].get(t)
        if e is None:
            print(f"  -- {t[:90]!r}: NOT RENDERED")
            continue
        tx = list(e["texts"].items())
        print(f"  -- {t[:90]!r}: {len(tx)}")
        for x, w in tx[:2]:
            print(f"       [{w}] {x[:150]}")
