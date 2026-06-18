
import os
import sys

# Add backend/app to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend', 'app'))

try:
    from backend.app.practice_gen import registry
    ids = registry.get_all_node_ids()
    print(f"Success! Found {len(ids)} nodes.")
    for i in range(min(5, len(ids))):
        print(f"  - {ids[i]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
