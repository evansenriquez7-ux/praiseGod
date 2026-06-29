import sys
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")
import json
from backend.app.routes.matatag_router import matatag_lab_generate

for i in range(3):
    try:
        res = matatag_lab_generate(
            node_id="mat_g3_na_q2_5",
            format_preference="auto"
        )
        print(f"--- Q{i+1} ---")
        if isinstance(res, dict):
            print("Question:", res.get("question_text"))
            print("Format:", res.get("format"))
        else:
            print(res)
    except Exception as e:
        print(f"Error: {e}")
