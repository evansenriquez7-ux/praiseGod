import sys
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")

import random
from backend.app.practice_gen.pipeline import run

def test_mat_g3_na_q2_5():
    # Easiest profile: max_difference is 0.0, number_difficulty is 0.0
    dp_easiest = {
        "max_difference": 0.0,
        "number_difficulty": 0.0
    }
    
    # Hardest profile: max_difference is 1.0, number_difficulty is 1.0
    dp_hardest = {
        "max_difference": 1.0,
        "number_difficulty": 1.0
    }

    import json
    print("--- EASIEST PROFILE (Grade 3, 0th Percentile) ---")
    try:
        res1 = run("mat_g3_na_q2_5", student_grade=3, difficulty_profile=dp_easiest, formatter="true_false")
        print(json.dumps(res1, indent=2))
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- HARDEST PROFILE (Grade 3, 100th Percentile) ---")
    try:
        res2 = run("mat_g3_na_q2_5", student_grade=3, difficulty_profile=dp_hardest, formatter="true_false")
        print(json.dumps(res2, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mat_g3_na_q2_5()
