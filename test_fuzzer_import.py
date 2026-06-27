import sys
import json
from backend.app.practice_gen.registry import get_all_node_ids
from backend.app.routes.matatag_router import get_matatag_lab_config

node_ids = get_all_node_ids()
print(f"Total nodes: {len(node_ids)}")
if node_ids:
    config = get_matatag_lab_config(node_ids[0])
    print(json.dumps(config, indent=2))
