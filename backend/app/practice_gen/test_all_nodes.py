import sys
import json
from registry import REGISTRY, NODE_TO_DNA, BINDINGS
from schemas.visuals import VisualSchemaRegistry
from dna.base import BaseDNA

import importlib
import pkgutil
import dna.na
import dna.mg
import dna.dp

def load_all_dnas():
    dnas = {}
    for package in [dna.na, dna.mg, dna.dp]:
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            mod = importlib.import_module(f"{package.__name__}.{module_name}")
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseDNA) and attr is not BaseDNA:
                    instance = attr()
                    dnas[instance.concept] = instance
    return dnas

dnas = load_all_dnas()

with open("../../../data/knowledge_graph_g1_3.json", "r") as f:
    kg = json.load(f)

nodes = kg.get("nodes", {})
issues = []

for node_id, node_data in nodes.items():
    if not (node_id.startswith("mat_g1") or node_id.startswith("mat_g2") or node_id.startswith("mat_g3")):
        continue
    
    mapping = BINDINGS.get(node_id)
    if not mapping:
        continue
    
    dna_name = mapping.get("dna")
    visual_name = mapping.get("visual")
    
    if dna_name not in dnas:
        issues.append(f"[{node_id}] DNA '{dna_name}' not found.")
        continue
        
    dna_instance = dnas[dna_name]
    
    # Check difficulty dimensions
    axes = dna_instance.difficulty_axes
    if not axes:
        issues.append(f"[{node_id}] DNA '{dna_name}' has NO difficulty dimensions.")
    
    # Try generating a problem
    try:
        problem = dna_instance.generate_problem({"difficulty_scalar": 0.5})
        if problem.visual and problem.visual.formatter:
            schema_class = VisualSchemaRegistry.get_schema(problem.visual.formatter)
            if schema_class:
                try:
                    schema_class(**problem.visual.data)
                except Exception as e:
                    issues.append(f"[{node_id}] Formatter '{problem.visual.formatter}' validation failed: {str(e)}")
            
            # Check interactivity if directed
            directions = problem.directions.lower() if problem.directions else ""
            if "shade" in directions or "set" in directions or "place" in directions or "draw" in directions or "build" in directions:
                # Check if it is interactive
                data = problem.visual.data
                if problem.visual.formatter == "ClockSet" and data.get("interaction_mode") != "set":
                    issues.append(f"[{node_id}] ClockSet is not interactive but directions say: {directions}")
                if problem.visual.formatter == "PesoMoney" and not data.get("is_interactive"):
                    issues.append(f"[{node_id}] PesoMoney is not interactive but directions say: {directions}")
    except Exception as e:
        issues.append(f"[{node_id}] Error generating problem: {str(e)}")

with open("test_results.txt", "w") as f:
    f.write("\n".join(issues))

print(f"Found {len(issues)} issues.")
