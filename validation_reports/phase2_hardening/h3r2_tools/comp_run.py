import sys
from backend.app.practice_gen.validation import validate_composition as VC
if __name__ == "__main__":
    ids = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    out, stats = VC.collect_findings(ids)
    with open(sys.argv[1], "w") as fh:
        for k, items in out.items():
            for i in items: fh.write(f"{k} | {i}\n")
        fh.write(str(stats) + "\n")
