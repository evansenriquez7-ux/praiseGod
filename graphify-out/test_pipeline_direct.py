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
        
    axis_values_dict = {}
    if cfg.allowed_difficulties:
        for k, v in cfg.allowed_difficulties.items():
            if v: axis_values_dict[k] = max(v) if isinstance(v[0], (int, float)) else v[-1]
                
    if cfg.allowed_contexts:
        for k, v in cfg.allowed_contexts.items():
            if v: axis_values_dict[k] = v[0] 
            
    print("=== Matatag Lab Output (10 Questions) ===")
    for i in range(10):
        try:
            lab_res = run(
                node_id=node_id,
                student_grade=3,
                difficulty_profile=axis_values_dict,
                seed=1000 + i,
                allowed_formatters=cfg.allowed_formatters
            )
            print(f"{i+1}. {lab_res.get('question_text')}")
        except Exception as e:
            print(f"Error in Lab Generate: {e}")
        
    print("\n=== Student Portal Output (10 Questions) ===")
    for i in range(10):
        try:
            portal_res = run(
                node_id=node_id,
                student_grade=3,
                seed=2000 + i,
                allowed_formatters=cfg.allowed_formatters,
                allowed_difficulties=cfg.allowed_difficulties,
                allowed_contexts=cfg.allowed_contexts
            )
            print(f"{i+1}. {portal_res.get('question_text')}")
        except Exception as e:
            print(f"Error in Portal Generate: {e}")

if __name__ == "__main__":
    main()
