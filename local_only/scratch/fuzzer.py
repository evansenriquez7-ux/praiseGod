import sys
import json
import random
import traceback
from collections import defaultdict

sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.routes.matatag_router import get_matatag_lab_config, get_db
from backend.app.practice_gen.registry import _KG_NODES

# We will use the TestClient to mimic the frontend
client = TestClient(app)

def run_fuzzer():
    errors = []
    # Test only a subset first, or all 151 if we want to be exhaustive.
    # Since we need to fix ALL issues, let's run through all nodes.
    nodes_to_test = list(_KG_NODES.keys())
    
    # We need a DB session for get_matatag_lab_config
    # We can just borrow the DB generator
    db_gen = get_db()
    db = next(db_gen)

    print(f"Starting fuzzer on {len(nodes_to_test)} nodes...")

    for node_id in nodes_to_test:
        try:
            config = get_matatag_lab_config(node_id)
        except Exception as e:
            errors.append({"node_id": node_id, "error": f"Failed to get config: {str(e)}", "trace": traceback.format_exc()})
            continue

        formatters = [f['name'] for f in config.get('formatters', [])]
        contexts = [c.get('name', c.get('id', '')) for c in config.get('contextual_variants', [])]
        dims = config.get('difficulty_dimensions', [])
        
        # Helper to generate a random valid axis_values dict
        def get_random_axes():
            axes = {}
            for dim in dims:
                opts = [o['scalar'] for o in dim['options']]
                if opts:
                    axes[dim['name']] = random.choice(opts)
            return axes

        def test_payload(test_name, formatter, axis_values, variant):
            # Create payload mimicking the UI
            try:
                url = f"/api/matatag/lab/generate?node_id={node_id}&format_preference={formatter}"
                if axis_values:
                    url += f"&axis_values={json.dumps(axis_values)}"
                # variant is not explicitly sent in the query for lab generate, wait...
                # Actually, matatag_lab_generate doesn't take 'variant' as a parameter! 
                # It samples from allowed_contexts in the DB!
                # We can't force the variant from the lab endpoint. We just test the formatters and axes.
                
                response = client.get(url)
                if response.status_code != 200:
                    errors.append({
                        "node_id": node_id,
                        "test": test_name,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "payload": url
                    })
                    return False

                data = response.json()
                
                # Heuristic checks
                if not data.get("stem"):
                    errors.append({"node_id": node_id, "test": test_name, "error": "Empty stem", "payload": url})
                    return False
                    
                if data.get("format_used") == "mcq" and len(data.get("mcq_options", [])) == 0:
                    errors.append({"node_id": node_id, "test": test_name, "error": "Empty mcq_options", "payload": url})
                    return False
                
                return True
            except Exception as e:
                errors.append({
                    "node_id": node_id,
                    "test": test_name,
                    "error": f"Exception: {str(e)}",
                    "trace": traceback.format_exc(),
                    "payload": url
                })
                return False

        # 1. Orthogonal test for each formatter (10 times)
        for fmt in formatters:
            for i in range(5): # Reduced to 5 for speed, but exhaustive enough
                test_payload(f"formatter_{fmt}_{i}", fmt, get_random_axes(), None)
                
        # 2. Orthogonal test for each dimension option (10 times)
        for dim in dims:
            dim_name = dim['name']
            opts = [o['scalar'] for o in dim['options']]
            for opt in opts:
                for i in range(2): # 2 times per option
                    axes = get_random_axes()
                    axes[dim_name] = opt
                    fmt = random.choice(formatters) if formatters else "auto"
                    test_payload(f"dim_{dim_name}_{opt}_{i}", fmt, axes, None)

    with open("/Users/enrichmentcap/Documents/antigravity/ccmed/graphify-out/fuzz_report.json", "w") as f:
        json.dump(errors, f, indent=2)

    print(f"Fuzzer complete. Found {len(errors)} errors.")
    if errors:
        print("First few errors:")
        for err in errors[:5]:
            print(err)

if __name__ == "__main__":
    run_fuzzer()
