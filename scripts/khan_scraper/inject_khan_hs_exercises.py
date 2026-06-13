#!/usr/bin/env python3
"""
Inject Khan Academy HS Math exercises into CCMed standard files.

Takes the scraped exercise data from khan_hs_ccmed_mapping.json and injects
a 'khan_exercises' array into each matching by_standard/ JSON file.

Handles:
- Direct matches (A_SSE_A_1 -> HSA.SSE.A.1)
- Sub-standard inheritance (A_SSE_A_1a inherits from A_SSE_A_1)
- Parent domain aggregation (A_REI gets union of all A_REI_* exercises)
- Deduplication of exercise URLs

Usage:
    python inject_khan_hs_exercises.py              # Full injection
    python inject_khan_hs_exercises.py --dry-run    # Preview only
    python inject_khan_hs_exercises.py --domain A   # Only Algebra files
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
BY_STANDARD_DIR = Path(__file__).parent.parent.parent / "data" / "processed" / "by_standard"

# Load mapping
MAPPING_FILE = DATA_DIR / "khan_hs_ccmed_mapping.json"


def log(msg):
    from datetime import datetime
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def load_mapping():
    """Load the KA -> CCMed mapping."""
    with open(MAPPING_FILE) as f:
        return json.load(f)


def find_parent_code(file_code, mapping):
    """
    For a sub-standard file (e.g., A_SSE_A_1a), find its parent standard
    that has exercises in the mapping.
    """
    # Strategy 1: Remove trailing lowercase letter
    if file_code[-1].islower() and len(file_code) > 3:
        parent = file_code[:-1]
        if parent in mapping and len(mapping[parent].get("exercises", [])) > 0:
            return parent
    
    # Strategy 2: Remove last _X component (e.g., A_REI_B_4_a -> A_REI_B_4)
    parts = file_code.rsplit("_", 1)
    while len(parts) == 2 and parts[0]:
        parent = parts[0]
        if parent in mapping and len(mapping[parent].get("exercises", [])) > 0:
            return parent
        parts = parent.rsplit("_", 1)
    
    return None


def aggregate_domain_exercises(domain_code, mapping, by_standard_dir):
    """
    For a top-level domain file (e.g., A_REI), collect all exercises
    from its child standards.
    """
    exercises = []
    seen_urls = set()
    
    prefix = domain_code + "_"
    for ccmed_code, data in mapping.items():
        if ccmed_code.startswith(prefix) or ccmed_code == domain_code:
            for ex in data.get("exercises", []):
                if ex["url"] not in seen_urls:
                    seen_urls.add(ex["url"])
                    exercises.append(ex)
    
    return exercises


def build_injection_plan(mapping, by_standard_dir, domain_filter=None):
    """
    Build the injection plan: which files get which exercises.
    Returns dict of {file_stem: [exercises]}
    """
    plan = {}
    hs_prefixes = ["A_", "F_", "G_", "N_", "S_"]
    
    # Get all HS CCMed files
    for filepath in sorted(by_standard_dir.glob("*.json")):
        file_code = filepath.stem
        
        # Only HS files
        if not any(file_code.startswith(p) for p in hs_prefixes):
            continue
        
        # Optional domain filter
        if domain_filter and not file_code.startswith(domain_filter + "_") and file_code != domain_filter:
            continue
        
        exercises = []
        source = "none"
        
        # Strategy 1: Direct match
        if file_code in mapping:
            exercises = mapping[file_code].get("exercises", [])
            source = "direct"
        
        # Strategy 2: Inheritance from parent
        if not exercises:
            parent = find_parent_code(file_code, mapping)
            if parent:
                exercises = mapping[parent].get("exercises", [])
                source = f"inherited:{parent}"
        
        # Strategy 3: Domain aggregation (for top-level like A_REI, G_GMD)
        if not exercises and file_code.count("_") <= 1:
            exercises = aggregate_domain_exercises(file_code, mapping, by_standard_dir)
            if exercises:
                source = "aggregated"
        
        if exercises:
            # Deduplicate
            seen = set()
            unique_exercises = []
            for ex in exercises:
                if ex["url"] not in seen:
                    seen.add(ex["url"])
                    unique_exercises.append(ex)
            plan[file_code] = {
                "exercises": unique_exercises,
                "source": source,
                "filepath": str(filepath)
            }
    
    return plan


def inject_exercises(plan, dry_run=False):
    """Inject exercises into CCMed JSON files."""
    injected = 0
    skipped = 0
    
    for file_code, data in sorted(plan.items()):
        filepath = Path(data["filepath"])
        exercises = data["exercises"]
        source = data["source"]
        
        if not exercises:
            skipped += 1
            continue
        
        if dry_run:
            log(f"  [DRY] {file_code}: {len(exercises)} exercises ({source})")
            injected += 1
            continue
        
        # Load existing file
        with open(filepath) as f:
            file_data = json.load(f)
        
        # Inject khan_exercises array
        file_data["khan_exercises"] = [
            {
                "title": ex["title"],
                "url": ex["url"],
                "source": "khan_academy_ccss"
            }
            for ex in exercises
        ]
        
        # Write back
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(file_data, f, indent=2, ensure_ascii=False)
        
        injected += 1
    
    return injected, skipped


def main():
    dry_run = "--dry-run" in sys.argv
    domain_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == "--domain" and i + 1 < len(sys.argv):
            domain_filter = sys.argv[i + 1].upper()
    
    log("=" * 60)
    log("Khan Academy HS Math -> CCMed Injection")
    log(f"Mode: {'DRY RUN' if dry_run else 'LIVE INJECTION'}")
    if domain_filter:
        log(f"Domain filter: {domain_filter}_*")
    log(f"Mapping file: {MAPPING_FILE}")
    log(f"Target dir: {BY_STANDARD_DIR}")
    log("=" * 60)
    
    # Verify paths
    if not MAPPING_FILE.exists():
        log(f"ERROR: Mapping file not found: {MAPPING_FILE}")
        log("Run scrape_khan_hs_math.py first!")
        sys.exit(1)
    
    if not BY_STANDARD_DIR.exists():
        log(f"ERROR: by_standard directory not found: {BY_STANDARD_DIR}")
        sys.exit(1)
    
    # Load mapping
    mapping = load_mapping()
    log(f"Loaded {len(mapping)} KA standard mappings")
    
    # Build injection plan
    plan = build_injection_plan(mapping, BY_STANDARD_DIR, domain_filter)
    log(f"Injection plan: {len(plan)} files to update")
    
    # Show plan summary
    by_source = defaultdict(int)
    total_exercises = 0
    for data in plan.values():
        by_source[data["source"].split(":")[0]] += 1
        total_exercises += len(data["exercises"])
    
    log(f"\nPlan breakdown:")
    for source, count in sorted(by_source.items()):
        log(f"  {source}: {count} files")
    log(f"  Total exercises to inject: {total_exercises}")
    
    # Execute injection
    log(f"\n{'='*60}")
    log(f"{'DRY RUN - NO FILES MODIFIED' if dry_run else 'INJECTING...'}")
    log(f"{'='*60}")
    
    injected, skipped = inject_exercises(plan, dry_run=dry_run)
    
    log(f"\n{'='*60}")
    log(f"COMPLETE")
    log(f"  Files {'would be ' if dry_run else ''}updated: {injected}")
    log(f"  Files skipped (no exercises): {skipped}")
    log(f"{'='*60}")


if __name__ == "__main__":
    main()
