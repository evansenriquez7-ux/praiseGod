import json, sys
obs = json.load(open(sys.argv[1]))
auto, manual = [], []
for k, o in obs.items():
    site, slot = k.split("|")
    vals = o["vals"]; n = o["n"]
    if o["allfill"] and n >= 3:
        auto.append({"site": site, "slot": slot, "domain": '"fill"', "why_auto": f"allfill n={n}"}); continue
    if len(o["eq"]) == 1 and n >= 5:
        nums = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
        distinct = len(vals)
        small = nums and all(abs(v) <= 12 for v in nums)
        if (not small and distinct >= 2) or distinct >= 4 or (isinstance(vals[0], str) and distinct >= 2):
            auto.append({"site": site, "slot": slot, "domain": f'"value:{o["eq"][0]}"', "why_auto": f"eq n={n} distinct={distinct}"}); continue
    manual.append(k)
json.dump(auto, open(sys.argv[2], "w"), indent=0, ensure_ascii=False)
json.dump(manual, open(sys.argv[3], "w"), indent=0)
print("auto", len(auto), "manual", len(manual))
