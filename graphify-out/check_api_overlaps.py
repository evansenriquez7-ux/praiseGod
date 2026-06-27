import sys
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")

from backend.app.routes.matatag_router import get_matatag_lab_config
from backend.app.practice_gen.registry import get_all_node_ids
import json

def check_overlaps():
    node_ids = get_all_node_ids()
    for node_id in node_ids:
        try:
            config = get_matatag_lab_config(node_id)
            for dim in config["difficulty_dimensions"]:
                if dim["dim_type"] == "continuous":
                    values = [opt["value"] for opt in dim["options"]]
                    if len(values) != len(set(values)):
                        print(f"Overlap in {node_id} ({dim['name']}): {values}")
                    else:
                        # Print all anyway just to see!
                        pass
        except Exception as e:
            pass

if __name__ == "__main__":
    check_overlaps()
