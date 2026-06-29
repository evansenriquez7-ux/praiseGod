import json
import random
import sys
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")

from backend.app.services.orchestrator import PracticeOrchestrator

parsed_axes = {
    "max_difference": 1.0, 
    "regrouping": "double",
    "number_difficulty": 1.0
}

for i in range(3):
    prob = PracticeOrchestrator.generate_problem(
        node_id="mat_g3_na_q2_5", 
        grade=3,
        seed=random.randint(1, 100000),
        formatter="true_false",
        difficulty_profile=parsed_axes
    )
    try:
        data = prob.model_dump()
    except AttributeError:
        data = prob.dict()
    print(f"--- Output {i+1} ---")
    print(json.dumps(data, indent=2))
