import os
import json
import random
from dotenv import load_dotenv
import sys

sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")

load_dotenv()

from backend.app.database import SessionLocal
from backend.app import models
from backend.app.routes.matatag_router import matatag_lab_generate
from backend.app.routes.practice_router import get_practice_question_batch

def main():
    db = SessionLocal()
    node_id = "mat_g3_na_q2_5"
    student_id = 1  # Assuming a student exists
    
    cfg = db.query(models.CompetencyConfiguration).filter_by(node_id=node_id).first()
    if not cfg:
        print(f"No configuration found in DB for {node_id}")
        return
        
    print("=== UI Settings Saved in DB ===")
    print("Formatters:", cfg.allowed_formatters)
    print("Difficulties:", cfg.allowed_difficulties)
    print("Contexts:", cfg.allowed_contexts)
    
    # Simulate UI sending axis_values
    # In the lab UI, the user selects ONE option per axis. We'll pick the maximum value allowed.
    axis_values_dict = {}
    
    if cfg.allowed_difficulties:
        for k, v in cfg.allowed_difficulties.items():
            if v:
                axis_values_dict[k] = max(v) if isinstance(v[0], (int, float)) else v[-1]
                
    if cfg.allowed_contexts:
        for k, v in cfg.allowed_contexts.items():
            if v:
                axis_values_dict[k] = v[0] # Pick the first allowed context
                
    print("\n=== Matatag Lab Output (Simulating UI Request) ===")
    axis_values_json = json.dumps(axis_values_dict)
    print("Sending axis_values:", axis_values_json)
    
    try:
        lab_res = matatag_lab_generate(
            node_id=node_id,
            axis_values=axis_values_json,
            format_preference="auto"
        )
        print("Format:", lab_res.get("format"))
        print("Question:", lab_res.get("question_text"))
        print("Answer:", lab_res.get("correct_answer"))
    except Exception as e:
        print(f"Error in Lab Generate: {e}")
        
    print("\n=== Student Portal Output (Simulating API Request) ===")
    try:
        # Note: we need a valid student_id. We'll just mock the student query if it fails.
        portal_res = get_practice_question_batch(
            student_id=1,
            count=1,
            subject="Matatag",
            subdomain=node_id,
            db=db
        )
        if portal_res:
            q = portal_res[0]
            print("Format:", q.question_mode)
            print("Question:", q.stem)
            
            # Print options for MCQ/TF
            if q.options:
                for opt in q.options:
                    print(f"  {opt.key}: {opt.text}")
        else:
            print("No questions returned.")
    except Exception as e:
        print(f"Error in Portal Generate: {e}")

if __name__ == "__main__":
    main()
