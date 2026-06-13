"""
inline_perseus_items.py

Makes every data/processed/by_standard/*.json file self-contained by
embedding the full practice problems (questions, answer choices, hints)
directly inside each khan_exercises entry.

Before:
  khan_exercises[0] = {
    "node_id": "...", "template_file": "perseus_templates/xxx.json", ...
  }

After:
  khan_exercises[0] = {
    "node_id": "...", "template_file": "...",
    "items": [
      {
        "item_id": "...",
        "question_content": "...",
        "answer_data": {...},   ← correct answers included
        "hints": [...],
        "widget_types": [...]
      },
      ...
    ]
  }

Idempotent — safe to re-run. Only updates files where at least one
exercise is missing its items array.
"""

import json
import os
from pathlib import Path

BY_STANDARD_DIR = Path(__file__).parent.parent / "data" / "processed" / "by_standard"
TEMPLATES_DIR   = Path(__file__).parent / "perseus_extractor" / "output" / "perseus_templates"


def load_items(node_id: str) -> list:
    """Read assessment_items from a Perseus template file."""
    tpath = TEMPLATES_DIR / f"{node_id}.json"
    if not tpath.exists():
        return []
    try:
        with open(tpath) as f:
            t = json.load(f)
        return t.get("assessment_items", [])
    except Exception:
        return []


def process_file(fpath: Path) -> tuple[int, int]:
    """
    Inline items into every khan_exercise that lacks them.
    Returns (exercises_updated, exercises_skipped).
    """
    with open(fpath) as f:
        data = json.load(f)

    khan_exercises = data.get("khan_exercises", [])
    if not khan_exercises:
        return 0, 0

    updated = 0
    skipped = 0
    dirty   = False

    for ex in khan_exercises:
        node_id = ex.get("node_id", "")
        if not node_id:
            skipped += 1
            continue

        # Skip if already inlined
        if ex.get("items"):
            skipped += 1
            continue

        items = load_items(node_id)
        if items:
            ex["items"] = items
            dirty = True
            updated += 1
        else:
            skipped += 1

    if dirty:
        with open(fpath, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return updated, skipped


def main():
    files = sorted(BY_STANDARD_DIR.glob("*.json"))
    print(f"Processing {len(files)} by_standard files...")
    print(f"Perseus templates dir: {TEMPLATES_DIR}")
    print()

    total_files_updated = 0
    total_exercises_inlined = 0
    total_exercises_missing = 0

    for fpath in files:
        updated, skipped = process_file(fpath)
        if updated > 0:
            total_files_updated += 1
            total_exercises_inlined += updated
            print(f"  [OK] {fpath.name:<40} +{updated} inlined, {skipped} already done/missing")
        total_exercises_missing += skipped if updated == 0 and skipped > 0 else 0

    print()
    print("=" * 55)
    print(f"Files updated:        {total_files_updated}")
    print(f"Exercises inlined:    {total_exercises_inlined}")


if __name__ == "__main__":
    main()
