import json
import random
import sys
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")

from backend.app.services.orchestrator import PracticeOrchestrator

for i in range(3):
    prob = PracticeOrchestrator.generate_problem(
        node_id="mat_g3_na_q2_5", 
        grade=3,
        seed=random.randint(1, 100000)
    )
    # Handle both pydantic v1 and v2 depending on the version
    try:
        data = prob.model_dump()
    except AttributeError:
        data = prob.dict()
    print(f"--- Output {i+1} ---")
    print(json.dumps(data, indent=2))
