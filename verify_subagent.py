import os
import sys
# Mock the dependencies to focus on verifying the subagent call
sys.path.append(os.path.abspath("backend"))

# Mock environment
os.environ["GEMINI_API_KEY"] = "mock_key"

from app.subagents import socratic_tutor_subagent

# Mock data
chat_history = [{"role": "user", "content": "Hello"}]
try:
    result = socratic_tutor_subagent(
        skill_id="MATH.3.1",
        stem="What is 2+2?",
        correct_answer="4",
        selected_answer="5",
        trap_name="none",
        chat_history=chat_history,
        language="en",
        student_interest="math",
        student_age=8,
        student_grade=3
    )
    print("Result:", result)
except Exception as e:
    print("Error:", e)
