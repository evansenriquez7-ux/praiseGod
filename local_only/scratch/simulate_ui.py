import sys
import json
import random
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")

# Mock the database call to prevent crash, since we don't need real DB for get_matatag_lab_config
from backend.app.database import get_db
# Actually, get_matatag_lab_config does NOT use the database!
# Wait, it does NOT use DB! Let's import it directly.

from backend.app.routes.matatag_router import get_matatag_lab_config
from backend.app.practice_gen.pipeline import run

try:
    # 1. Fetch exactly what the UI sees
    config = get_matatag_lab_config("mat_g3_na_q2_5")
    
    print("=== UI CONFIGURATION ===")
    print(json.dumps(config, indent=2))
    
    # 2. Simulate the user selecting options from the UI
    # For each difficulty dimension, pick the maximum option (which is what the user did)
    selected_axes = {}
    for dim in config.get("difficulty_dimensions", []):
        options = dim.get("options", [])
        if options:
            # Pick the last option (max difficulty)
            max_opt = options[-1]
            if dim["dim_type"] == "continuous":
                selected_axes[dim["name"]] = max_opt["scalar"]
            else:
                selected_axes[dim["name"]] = max_opt["level"]
                
    # Pick a random contextual variant if available
    for var in config.get("contextual_variants", []):
        options = var.get("options", [])
        if options:
            selected_axes[var["name"]] = options[0]
            
    print("\n=== SIMULATED UI SELECTIONS ===")
    print(json.dumps(selected_axes, indent=2))
    
    # 3. Generate problem exactly as it would be processed through the pipeline
    print("\n=== GENERATING PROBLEM ===")
    skeleton = run(
        node_id="mat_g3_na_q2_5",
        student_grade=3,
        seed=random.randint(1000, 99999),
        difficulty_profile=selected_axes,
        experience="standard"
    )
    
    print("\n--- Question Output ---")
    print("Format:", skeleton.get("format"))
    print("Question Text:", skeleton.get("question_text"))
    print("Correct Answer:", skeleton.get("correct_answer"))
    print("DNA used:", skeleton.get("spine_id", "none").split("_")[0])

except Exception as e:
    import traceback
    traceback.print_exc()
