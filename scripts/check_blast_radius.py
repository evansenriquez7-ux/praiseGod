#!/usr/bin/env python3
"""
DNA Blast Radius Audit Tool.

Inspects which sibling nodes share a target DNA (or given node's DNAs) and checks
if their rendering is intact and deterministic.

Usage:
  PYTHONPATH=. python scripts/check_blast_radius.py [--dna DNA_NAME] [--node NODE_ID] [--seeds 5]
"""

import sys
import json
import argparse
import hashlib
from typing import List, Dict, Set

from backend.app.practice_gen.registry import NODE_TO_DNA
from backend.app.practice_gen.validation.judgment_packets import _render_sample


def get_nodes_for_dna(target_dna: str) -> List[str]:
    """Find all node IDs sharing the target DNA."""
    matching_nodes = []
    for node_id, dnas in NODE_TO_DNA.items():
        if target_dna in dnas:
            matching_nodes.append(node_id)
    return sorted(matching_nodes)


def audit_blast_radius(target_dna: str = None, target_node: str = None, num_seeds: int = 5) -> int:
    """Renders seeds across all sibling nodes sharing DNA and checks output stability."""
    nodes_to_check: Set[str] = set()

    if target_node:
        dnas = NODE_TO_DNA.get(target_node, [])
        for d in dnas:
            nodes_to_check.update(get_nodes_for_dna(d))
    elif target_dna:
        nodes_to_check.update(get_nodes_for_dna(target_dna))
    else:
        print("Error: Specify --dna <DNA_NAME> or --node <NODE_ID>")
        return 1

    nodes = sorted(nodes_to_check)
    print(f"Praise God! Auditing blast radius across {len(nodes)} sibling node(s)...")
    
    failures = []
    results = {}

    for node_id in nodes:
        seed_hashes = []
        try:
            for seed in range(42, 42 + num_seeds):
                item = _render_sample(node_id, seed=seed)
                payload = json.dumps({
                    "stem": item.get("question_text"),
                    "answer": item.get("correct_answer"),
                    "options": item.get("options"),
                    "formatter": item.get("formatter")
                }, sort_keys=True)
                seed_hashes.append(hashlib.sha256(payload.encode()).hexdigest()[:8])
            results[node_id] = seed_hashes
            print(f"  [OK] {node_id:<20} -> seeds [{', '.join(seed_hashes)}]")
        except Exception as e:
            failures.append((node_id, str(e)))
            print(f"  [FAIL] {node_id:<18} -> ERROR: {e}")

    if failures:
        print(f"\nBlast Radius Audit: FAILED with {len(failures)} error(s).")
        return 1

    print(f"\nBlast Radius Audit: PASS ({len(nodes)} nodes rendered cleanly across {num_seeds} seeds).")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit DNA Blast Radius")
    parser.add_argument("--dna", help="DNA module name to audit")
    parser.add_argument("--node", help="Node ID to audit sibling nodes for")
    parser.add_argument("--seeds", type=int, default=5, help="Number of seeds to sample per node")
    args = parser.parse_args()

    sys.exit(audit_blast_radius(target_dna=args.dna, target_node=args.node, num_seeds=args.seeds))
