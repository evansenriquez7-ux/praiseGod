from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")
from backend.app.database import SessionLocal
from backend.app import models

db = SessionLocal()
cfg = db.query(models.CompetencyConfiguration).filter_by(node_id="mat_g3_na_q2_5").first()
if cfg:
    import json
    print(json.dumps({
        "allowed_formatters": cfg.allowed_formatters,
        "allowed_difficulties": cfg.allowed_difficulties,
        "allowed_contexts": cfg.allowed_contexts
    }, indent=2))
else:
    print("No custom config in DB.")
