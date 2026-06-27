import asyncio
from backend.app.practice_gen.pipeline import run
import json

problem = run("mat_g1_dp_q3_0", student_grade=1, seed=123, formatter="pictograph_read")
print(json.dumps(problem, indent=2))
