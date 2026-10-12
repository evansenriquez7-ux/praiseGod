"""Dump validate_slots.collect_findings (the real check) as JSON; print type-only per lc.
  tonly.py OUT.json [lc1,lc2]"""
import json, sys, collections
from backend.app.practice_gen.validation import validate_slots as VS
if __name__ == "__main__":
    lcs = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    f = VS.collect_findings(lcs)
    json.dump(f, open(sys.argv[1], "w"), indent=0, ensure_ascii=False)
    for lab, items in f.items():
        print(lab, len(items))
    per = collections.Counter(i.split(":", 1)[0] for i in f["slot_domain_type_only_14"])
    print("open lcs", len(per))
    if lcs:
        for i in f["slot_domain_type_only_14"] + f["slot_domain_escape_14"]:
            print(" ", i.split(" at seed")[0], "|", i.split("seeds): ")[1][:60] if "seeds): " in i else "")
