import json
import sys
from registry import REGISTRY
from compatibility import COMPATIBILITY, VARIANTS_BY_DNA

with open("../../../data/knowledge_graph_g1_3.json", "r") as f:
    kg = json.load(f)

nodes = kg.get("nodes", {})

output_lines = []
for node_id, node_data in nodes.items():
    if node_id.startswith("mat_g2") or node_id.startswith("mat_g3"):
        text = node_data.get("competency", "")
        mapping = REGISTRY.get(node_id)
        if mapping:
            dna = mapping.get("dna")
            visual = mapping.get("visual")
            
            is_compat = visual in COMPATIBILITY.get(dna, [])
            variants = list(VARIANTS_BY_DNA.get(dna, {}).keys())
            
            output_lines.append(f"[{node_id}] {text}")
            output_lines.append(f"  -> DNA: {dna}, VISUAL: {visual} (Compat: {is_compat}) | VARIANTS: {variants}")

with open("../../../nodes_evaluation.txt", "w") as f:
    f.write("\n".join(output_lines))
