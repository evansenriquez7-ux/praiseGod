import json
import random
import sys
sys.path.insert(0, "/Users/enrichmentcap/Documents/antigravity/ccmed")

from backend.app.practice_gen.pipeline import run

for i in range(3):
    skeleton = run(
        node_id="mat_g3_na_q2_5",
        student_grade=3,
        seed=random.randint(1000, 99999),
        experience="standard"
    )
    print(f"--- Question {i+1} ---")
    print("Format:", skeleton.get("format"))
    print("Question Text:", skeleton.get("question_text"))
    print("Correct Answer:", skeleton.get("correct_answer"))
    print("DNA used:", skeleton.get("spine_id", "none").split("_")[0])

