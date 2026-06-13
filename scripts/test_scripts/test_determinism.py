import sys
from backend.app.sympy_skeletons import get_question_skeleton
from backend.app.database import SessionLocal
import backend.app.models as models

skill_id = "3.OA.A.3"
seed = 12345
grade_level = 3

skel1 = get_question_skeleton(skill_id, seed=seed, grade_level=grade_level)
skel2 = get_question_skeleton(skill_id, seed=seed, grade_level=grade_level)

for key in ["A", "B", "C", "D"]:
    if skel1["options"][key]["value"] != skel2["options"][key]["value"]:
        print("MISMATCH!", key, skel1["options"][key]["value"], skel2["options"][key]["value"])
        sys.exit(1)

print("Determinism is working perfectly.")
