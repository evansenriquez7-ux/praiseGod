import os
import json
import random
from dotenv import load_dotenv
import sys

sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")
load_dotenv()

from backend.app.database import SessionLocal
from backend.app import models
from backend.app.practice_gen.pipeline import run

def main():
    db = SessionLocal()
    node_id = "mat_g3_na_q2_5"
    
    cfg = db.query(models.CompetencyConfiguration).filter_by(node_id=node_id).first()
    if not cfg:
        print(f"No configuration found in DB for {node_id}")
        return
        
    print("=== UI Settings Saved in DB ===")
    print("Formatters:", cfg.allowed_formatters)
    print("Difficulties:", cfg.allowed_difficulties)
    print("Contexts:", cfg.allowed_contexts)
    
    # --- LAB SIMULATION ---
    # In the lab UI, the user selects ONE option per axis. We pick the max value.
    axis_values_dict = {}
    if cfg.allowed_difficulties:
        for k, v in cfg.allowed_difficulties.items():
            if v: axis_values_dict[k] = max(v) if isinstance(v[0], (int, float)) else v[-1]
                
    if cfg.allowed_contexts:
        for k, v in cfg.allowed_contexts.items():
            if v: axis_values_dict[k] = v[0] 
            
    print("\n=== Matatag Lab Output (Simulating UI Request) ===")
    print("Sending axis_values:", json.dumps(axis_values_dict))
    
    try:
        lab_res = run(
            node_id=node_id,
            student_grade=3,
            difficulty_profile=axis_values_dict,
            seed=12345,
            allowed_formatters=cfg.allowed_formatters # If the user selected true_false, we pass it! Wait, in lab generate, the formatter is passed as format_preference! If format_preference is "auto", it allows everything in the DB or everything the node supports?
        )
        # Actually, in matatag_lab_generate:
        # allowed_fmt = None 
        # format_preference="auto" means allowed_fmt = None!
        # Let's pass allowed_fmt = None to simulate the lab endpoint when auto is used. Or if the user selected true_false, they probably mean it.
        # But wait, we'll just print the output!
        print("Format:", lab_res.get("format"))
        print("Question:", lab_res.get("question_text"))
    except Exception as e:
        print(f"Error in Lab Generate: {e}")
        
    # --- PORTAL SIMULATION ---
    print("\n=== Student Portal Output (Simulating API Request) ===")
    # The portal passes allowed_formatters, allowed_difficulties, and allowed_contexts directly to run()
    try:
        portal_res = run(
            node_id=node_id,
            student_grade=3,
            seed=54321,
            allowed_formatters=cfg.allowed_formatters,
            allowed_difficulties=cfg.allowed_difficulties,
            allowed_contexts=cfg.allowed_contexts
        )
        print("Format:", portal_res.get("format"))
        print("Question:", portal_res.get("question_text"))
    except Exception as e:
        print(f"Error in Portal Generate: {e}")

if __name__ == "__main__":
    main()
