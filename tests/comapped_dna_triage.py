"""
Mechanical triage for co-mapped-DNA bleed: for every FAIL/CONCERN node mapped
to 2+ DNAs, render ~10 seeds per co-mapped DNA via forced_dna (not the
orchestrator's random pick, which dilutes a bad DNA's signal), and check
whether the rendered question_text shares any content word with the node's
competency text. A DNA that misses on every seed is confirmed off-topic
bleed, not a hunch.
"""
import json
import re
from collections import Counter
from backend.app.practice_gen.pipeline import run
from backend.app.practice_gen.registry import get_all_node_ids, get_node_dnas, get_node_info

STOPWORDS = {
    "the","a","an","and","or","of","to","in","on","for","with","using","use",
    "up","numbers","number","up to","given","its","is","are","by","from",
    "as","that","this","their","other","various","other's","two","three",
    "four","1","2","3","4","including","involving","through","between",
}

def content_words(text):
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}

results = []
for nid in sorted(get_all_node_ids()):
    group = "_".join(nid.split("_")[:-1])
    try:
        review = json.load(open(f"validation_reports/judgment/{group}/{nid}.json"))
    except FileNotFoundError:
        continue
    if review.get("overall") not in ("FAIL", "CONCERN"):
        continue
    dnas = get_node_dnas(nid) or []
    if len(dnas) < 2:
        continue
    info = get_node_info(nid)
    comp_words = content_words(info.get("competency", ""))
    per_dna_hit_rate = {}
    for dna in dnas:
        hits = 0
        total = 0
        for seed in range(300, 310):
            try:
                p = run(nid, seed=seed, forced_dna=dna, is_student_path=True)
            except Exception:
                continue
            total += 1
            qwords = content_words(p.get("question_text", ""))
            if qwords & comp_words:
                hits += 1
        per_dna_hit_rate[dna] = f"{hits}/{total}" if total else "n/a"
    results.append((nid, review.get("overall"), dnas, per_dna_hit_rate))

print(f"{'node_id':22} {'verdict':8} {'dnas':45} per-dna content-word hit rate")
zero_hit_dnas = Counter()
for nid, overall, dnas, rates in results:
    print(f"{nid:22} {overall:8} {str(dnas):45} {rates}")
    for dna, rate in rates.items():
        if rate not in ("n/a",) and rate.split("/")[0] == "0":
            zero_hit_dnas[(nid, dna)] += 1

print()
print(f"=== {len(results)} co-mapped FAIL/CONCERN nodes checked ===")
print(f"=== {len(zero_hit_dnas)} (node, dna) pairs with ZERO content-word hits across 10 seeds -- confirmed bleed candidates ===")
for (nid, dna), _ in zero_hit_dnas.items():
    print(f"  {nid}: '{dna}' never shares a competency content word")
