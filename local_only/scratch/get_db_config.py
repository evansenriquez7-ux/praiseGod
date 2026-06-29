from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")
from backend.app.database import SessionLocal
from backend.app import models

db = SessionLocal()
cfg = db.query(models.CompetencyConfiguration).filter_by(node_id="mat_g3_na_q2_5").first()
if cfg:
    print("Formatters:", cfg.allowed_formatters)
    print("Difficulties:", cfg.allowed_difficulties)
    print("Contexts:", cfg.allowed_contexts)
else:
    print("No custom config in DB.")
