"""
Phase 1: Download and index the MathFish dataset (allenai/mathfish).

Maps 21,776 problems to individual CCSS standard IDs.
Writes per-standard evidence files to data/processed/by_standard/.

Source: https://huggingface.co/datasets/allenai/mathfish
License: ODC-By 1.0 (dataset), CC BY 4.0 / CC BY-NC-SA 4.0 (content)
"""
import os
import sys
import json
from collections import defaultdict

# Set HuggingFace cache before importing
os.environ["HF_HOME"] = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'data', '.cache', 'huggingface')
)
from huggingface_hub import snapshot_download


def download():
    """Download MathFish from HuggingFace."""
    target_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'huggingface', 'mathfish')
    target_dir = os.path.abspath(target_dir)
    os.makedirs(target_dir, exist_ok=True)

    # Check if already downloaded
    if os.path.exists(os.path.join(target_dir, 'README.md')):
        print(f"MathFish already downloaded at {target_dir}")
        return target_dir

    print("Downloading allenai/mathfish from HuggingFace...")
    snapshot_download(
        repo_id="allenai/mathfish",
        repo_type="dataset",
        local_dir=target_dir
    )
    print(f"Download complete: {target_dir}")
    return target_dir


def index_by_standard(mathfish_dir: str):
    """
    Parse MathFish JSONL files and index problems by CCSS standard ID.
    Writes per-standard JSON files to data/processed/by_standard/.
    """
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'by_standard')
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    problems_by_standard = defaultdict(list)
    total_problems = 0
    problems_with_standards = 0

    # Find all JSONL files in the dataset
    for root, dirs, files in os.walk(mathfish_dir):
        for fname in sorted(files):
            if not fname.endswith('.jsonl'):
                continue
            fpath = os.path.join(root, fname)
            print(f"  Parsing {fname}...")
            with open(fpath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    total_problems += 1
                    standards = item.get("standards", [])
                    if not standards:
                        continue

                    problems_with_standards += 1

                    # Index by each standard this problem addresses
                    for entry in standards:
                        # Format: ["Addressing", "4.NF.A.1"] or similar
                        if isinstance(entry, list) and len(entry) >= 2:
                            relation, standard_id = entry[0], entry[1]
                        elif isinstance(entry, dict):
                            relation = entry.get("relation", "")
                            standard_id = entry.get("standard", "")
                        else:
                            continue

                        # Only index primary alignment relations
                        if relation in ("Addressing", "Alignment", "Building On",
                                        "Building Towards"):
                            problems_by_standard[standard_id].append({
                                "source": "mathfish",
                                "text": item.get("text", ""),
                                "metadata": item.get("metadata", {}),
                                "source_curriculum": item.get("source", ""),
                                "relation": relation,
                                "id": item.get("id", "")
                            })

    # Write per-standard evidence files
    for standard_id, problems in problems_by_standard.items():
        safe_id = standard_id.replace(".", "_").replace("-", "_")
        outpath = os.path.join(output_dir, f"{safe_id}.json")

        # Load existing data if present (to merge with other sources later)
        existing = {}
        if os.path.exists(outpath):
            with open(outpath, 'r', encoding='utf-8') as f:
                existing = json.load(f)

        if "problems" not in existing:
            existing["problems"] = []

        # Avoid duplicates if re-run
        existing_ids = {p.get("id") for p in existing["problems"] if p.get("source") == "mathfish"}
        new_problems = [p for p in problems if p.get("id") not in existing_ids]
        existing["problems"].extend(new_problems)
        existing["node_id"] = standard_id

        with open(outpath, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"MathFish Indexing Complete")
    print(f"{'='*60}")
    print(f"Total problems parsed:        {total_problems}")
    print(f"Problems with standards:      {problems_with_standards}")
    print(f"Unique standards found:       {len(problems_by_standard)}")
    print(f"Total problem-standard pairs: {sum(len(v) for v in problems_by_standard.values())}")
    print(f"Output directory:             {output_dir}")
    print(f"{'='*60}")

    # Print top 20 standards by problem count
    sorted_standards = sorted(problems_by_standard.items(), key=lambda x: -len(x[1]))
    print(f"\nTop 20 standards by problem count:")
    for std, probs in sorted_standards[:20]:
        print(f"  {std:20s} — {len(probs):4d} problems")

    # Print coverage by grade
    grade_counts = defaultdict(int)
    for std in problems_by_standard:
        parts = std.split(".")
        if parts[0] in ("K", "1", "2", "3", "4", "5", "6", "7", "8"):
            grade_counts[parts[0]] += 1
        elif parts[0].startswith("HS") or parts[0] in ("A", "N", "F", "G", "S"):
            grade_counts["HS"] += 1
        else:
            grade_counts["Other"] += 1

    print(f"\nStandards covered by grade:")
    for grade in ["K", "1", "2", "3", "4", "5", "6", "7", "8", "HS", "Other"]:
        if grade in grade_counts:
            print(f"  Grade {grade:5s}: {grade_counts[grade]} standards")


if __name__ == "__main__":
    mathfish_dir = download()
    index_by_standard(mathfish_dir)
