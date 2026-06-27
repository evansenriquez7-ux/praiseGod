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
        node_id="mat_g3_na_q2_4", # subtraction up to 10000
        grade=3,
        seed=random.randint(1, 100000),
        difficulty_profile=parsed_axes
    )
    print(f"--- Output {i+1} ---")
    print(json.dumps(prob.model_dump(), indent=2))
