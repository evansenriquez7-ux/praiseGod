"""
inject_khan_exercises.py

Takes the CCSS crosswalk and injects Khan Academy Perseus exercise references
into CCMed's by_standard JSON files as a `khan_exercises` array.

Each entry in khan_exercises:
{
  "node_id": "...",
  "title": "...",
  "description": "...",
  "topic_path": [...],
  "item_count": 20,
  "template_file": "perseus_templates/{node_id}.json",
  "sample_question": "...",   # first question_content from first item
  "widget_types": [...],      # union of widget types across all items
  "mastery_model": {"type": "m_of_n", "m": 5, "n": 7}
}

Matches crosswalk prefix to CCMed file by prefix match:
  crosswalk key "3_NF" matches CCMed files 3_NF_A_1.json, 3_NF_A_2.json, etc.
  crosswalk key "K_CC" matches K_CC_A_1.json, K_CC_B_4.json, etc.

Does NOT overwrite existing content (problems, tasks, sbac).
Idempotent: re-running replaces the khan_exercises array cleanly.
"""

import json
import os
from pathlib import Path
from collections import defaultdict

CROSSWALK_PATH = Path(__file__).parent / "output" / "ccss_crosswalk.json"
TEMPLATES_DIR = Path(__file__).parent / "output" / "perseus_templates"
CCMED_DIR = Path(__file__).parent.parent.parent / "data" / "processed" / "by_standard"


def load_crosswalk():
    with open(CROSSWALK_PATH) as f:
        return json.load(f)


def get_sample_question(node_id):
    """Load template and return first question content string."""
    tfile = TEMPLATES_DIR / f"{node_id}.json"
    if not tfile.exists():
        return ""
    try:
        with open(tfile) as f:
            t = json.load(f)
        items = t.get("assessment_items", [])
        if items:
            return items[0].get("question_content", "")[:300]
    except Exception:
        pass
    return ""


def get_widget_types(node_id):
    """Load template and return union of all widget types."""
    tfile = TEMPLATES_DIR / f"{node_id}.json"
    if not tfile.exists():
        return []
    try:
        with open(tfile) as f:
            t = json.load(f)
        types = set()
        for item in t.get("assessment_items", []):
            types.update(item.get("widget_types", []))
        return sorted(types)
    except Exception:
        return []


def get_mastery_model(node_id):
    tfile = TEMPLATES_DIR / f"{node_id}.json"
    if not tfile.exists():
        return {}
    try:
        with open(tfile) as f:
            t = json.load(f)
        return t.get("mastery_model", {})
    except Exception:
        return {}


def ccmed_stem_matches_prefix(stem, prefix):
    """
    Check if a CCMed file stem matches a crosswalk prefix.

    Handles two naming conventions:
      Math:  stem="3_NF_A_1", prefix="3_NF"   -> startswith match
      ELA:   stem="RI_3_3_evidence", prefix="3_RI"  -> reverse: domain_grade
             stem="RL_3_1_evidence", prefix="3_RL"

    Also handles upward grade fallback for ELA reading:
      stem="RI_4_2_evidence" will also match prefix="3_RI" (closest lower grade)
    """
    # Standard startswith match (works for all math)
    if stem.startswith(prefix):
        return True

    # ELA reverse match: prefix="3_RI" should match stem="RI_3_3_evidence"
    parts = prefix.split("_", 1)  # ["3", "RI"] or ["K", "L"]
    if len(parts) == 2:
        grade, domain = parts
        if domain in ("RI", "RL", "L", "W", "SL", "RF"):
            # Direct match: RI_3_ prefix
            if stem.startswith(f"{domain}_{grade}_") or stem.startswith(f"{domain}_{grade}"):
                return True
            # Grade fallback for reading: RI_4 or RI_5 files get grade-3 content
            if domain in ("RI", "RL"):
                stem_parts = stem.split("_")
                if len(stem_parts) >= 2 and stem_parts[0] == domain:
                    stem_grade = stem_parts[1]
                    # Map numeric grades: if crosswalk has grade 3, also match grade 4 and 5
                    FALLBACK = {"2": ["3", "4", "5"], "3": ["4", "5"]}
                    for cw_grade, fallback_grades in FALLBACK.items():
                        if grade == cw_grade and stem_grade in fallback_grades:
                            return True

    return False


def main():
    print(f"Loading crosswalk from {CROSSWALK_PATH}...")
    crosswalk = load_crosswalk()
    print(f"  {len(crosswalk)} CCSS prefixes in crosswalk")

    ccmed_files = list(CCMED_DIR.glob("*.json"))
    print(f"  {len(ccmed_files)} CCMed standard files")

    injected_count = 0
    skipped_count = 0
    total_exercises_injected = 0

    # Collect ELA Language prefixes that have no matching CCMed file → create stubs
    ela_lang_prefixes = {k: v for k, v in crosswalk.items()
                         if k.endswith("_L") and not k.startswith(("HS", "A_", "F_", "G_", "N_", "S_"))}

    for ccmed_path in sorted(ccmed_files):
        stem = ccmed_path.stem  # e.g. "3_NF_A_1"

        # Find all crosswalk prefixes that match this file
        matching_exercises = []
        for prefix, exercises in crosswalk.items():
            if ccmed_stem_matches_prefix(stem, prefix):
                matching_exercises.extend(exercises)

        if not matching_exercises:
            skipped_count += 1
            continue

        # Load CCMed file
        with open(ccmed_path) as f:
            data = json.load(f)

        # Build enriched khan_exercises list
        khan_exercises = []
        for ex in matching_exercises:
            node_id = ex["node_id"]
            entry = {
                "node_id": node_id,
                "title": ex["title"],
                "description": ex.get("description", ""),
                "topic_path": ex.get("topic_path", []),
                "item_count": ex.get("item_count", 0),
                "template_file": ex.get("template_file", f"perseus_templates/{node_id}.json"),
                "sample_question": get_sample_question(node_id),
                "widget_types": get_widget_types(node_id),
                "mastery_model": get_mastery_model(node_id)
            }
            khan_exercises.append(entry)

        data["khan_exercises"] = khan_exercises

        with open(ccmed_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  {stem}: injected {len(khan_exercises)} exercises")
        injected_count += 1
        total_exercises_injected += len(khan_exercises)

    # Create stub L_ files for Grammar exercises (CCMed has no L_ files yet)
    created_stubs = 0
    for prefix, exercises in sorted(ela_lang_prefixes.items()):
        # prefix like "1_L", "2_L", "K_L" -> file "L_1.json", "L_2.json", "L_K.json"
        parts = prefix.split("_", 1)
        grade, domain = parts[0], parts[1]
        stub_name = f"L_{grade}.json"
        stub_path = CCMED_DIR / stub_name
        if stub_path.exists():
            # Already exists, update it
            with open(stub_path) as f:
                data = json.load(f)
        else:
            data = {"problems": [], "tasks": [], "node_id": f"L_{grade}"}

        khan_exercises = []
        for ex in exercises:
            node_id = ex["node_id"]
            entry = {
                "node_id": node_id,
                "title": ex["title"],
                "description": ex.get("description", ""),
                "topic_path": ex.get("topic_path", []),
                "item_count": ex.get("item_count", 0),
                "template_file": ex.get("template_file", f"perseus_templates/{node_id}.json"),
                "sample_question": get_sample_question(node_id),
                "widget_types": get_widget_types(node_id),
                "mastery_model": get_mastery_model(node_id)
            }
            khan_exercises.append(entry)

        data["khan_exercises"] = khan_exercises
        with open(stub_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  {stub_name} (stub): injected {len(khan_exercises)} exercises")
        created_stubs += 1
        total_exercises_injected += len(khan_exercises)

    print(f"\n{'='*50}")
    print(f"Injected into {injected_count} existing CCMed files")
    print(f"Created {created_stubs} new L_ stub files")
    print(f"Total exercise refs injected: {total_exercises_injected}")
    print(f"No match: {skipped_count} files")


if __name__ == "__main__":
    main()
