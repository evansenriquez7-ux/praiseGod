"""Per-render §14 unaccounted fields with formatter/dna (for slice selection)."""
import json, sys
from backend.app.practice_gen.validation import validate_slots as VS
from backend.app.practice_gen.registry import get_all_node_ids
if __name__ == "__main__":
    ids = sys.argv[2].split(",") if len(sys.argv) > 2 else sorted(get_all_node_ids())
    with open(sys.argv[1], "w") as out:
        for n in ids:
            for seed in VS.SEEDS:
                for label, where, reason in VS.render_findings(n, seed):
                    import re
                    fm = re.search(r"\(formatter (\w+), DNA (\w+)\)", reason)
                    out.write(json.dumps({"label": label, "lc": n, "seed": seed, "where": where,
                        "formatter": fm.group(1) if fm else None, "dna": fm.group(2) if fm else None,
                        "reason": reason}) + "\n")
