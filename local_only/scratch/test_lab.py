import json
import random
import sys
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")

from backend.app.services.orchestrator import PracticeOrchestrator

# Simulate Matatag Lab passing max sliders
# max_difference scalar = 1.0
# regrouping = "double"
# number_difficulty scalar = 1.0
parsed_axes = {
    "max_difference": 1.0, 
    "regrouping": "double",
    "number_difficulty": 1.0
}

# The Lab calls PracticeOrchestrator directly with these parsed_axes
for i in range(3):
    prob = PracticeOrchestrator.generate_problem(
        node_id="mat_g2_na_q2_5", # subtraction
        grade=3,
        seed=random.randint(1, 100000),
        difficulty_profile=parsed_axes,
        formatter="number_bond"
    )
    print(f"--- Output {i+1} ---")
    print(json.dumps(prob.dict(), indent=2))
