import sys
import json
import re
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.practice_gen.pipeline import run
import re
from app.practice_gen.registry import BINDINGS

def check_for_leaked_answer(problem):
    # If the format is meant to show the answer and ask if it's correct, ignore
    fmt = problem.get('format', '')
    if fmt in ['error_detect', 'true_false'] or '_set_' in fmt or fmt.startswith('set_') or fmt.endswith('_set'):
        return False
        
    prompt = problem.get('question_text', '') or problem.get('stem', '')
    answer = problem.get('correct_answer', '')
    
    if isinstance(answer, dict):
        answer = answer.get('correct_value', '')
        
    if answer != '':
        ans_str = str(answer)
        # Use word boundaries so "20" doesn't match inside "120"
        # Also escape the answer string just in case it contains regex special chars
        pattern = r'\b' + re.escape(ans_str) + r'\b'
        
        if re.search(pattern, prompt):
            # If the prompt contains the answer string exactly as a full word, and it's not a generic number like 1
            if isinstance(answer, int) and answer > 10:
                return True
            elif isinstance(answer, str) and len(answer) > 2:
                # Still allow 'True' or 'False' to pass if the question is 'True or false?'
                if answer in ['True', 'False', 'true', 'false']:
                    return False
                return True
    return False

def check_for_broken_interpolation(problem):
    broken_strs = []
    
    def search_strings(obj):
        if isinstance(obj, str):
            if "NaN" in obj or "undefined" in obj or "null" in obj or "None" in obj:
                broken_strs.append(obj)
            # Check for un-interpolated variables like {something}
            # Ignore if it's a JSON string
            if obj.startswith('{"') and obj.endswith('}'):
                return
            if re.search(r'\{[a-zA-Z0-9_]+\}', obj):
                broken_strs.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                search_strings(v)
        elif isinstance(obj, list):
            for v in obj:
                search_strings(v)
    
    search_strings(problem)
    return len(broken_strs) > 0, broken_strs

def check_for_visual_payload(problem):
    is_visual = problem.get('is_visual', False)
    if is_visual:
        vp = problem.get('visual_params')
        if not vp or not isinstance(vp, dict) or len(vp) == 0:
            return True, "Missing or empty visual_params"
    return False, ""

def main():
    nodes = [n for n in BINDINGS.keys() if n.startswith("mat_g2_") or n.startswith("mat_g3_")]
    total = 0
    failures = 0
    
    print(f"Auditing {len(nodes)} nodes for Grade 2 and 3...")
    
    for node_id in nodes:
        grade = 2 if node_id.startswith("mat_g2_") else 3
        for difficulty in [0.0, 0.5, 1.0]:
            for i in range(2): 
                total += 1
                try:
                    problem = run(
                        node_id=node_id,
                        student_grade=grade,
                        difficulty_profile={"scalar": difficulty},
                        seed=i
                    )
                    
                    issues = []
                    
                    is_broken, broken_strs = check_for_broken_interpolation(problem)
                    if is_broken:
                        issues.append(f"Interpolation ({broken_strs[0]})")
                        
                    if check_for_leaked_answer(problem):
                        issues.append("Leaked Answer")
                        
                    vis_error, vis_msg = check_for_visual_payload(problem)
                    if vis_error:
                        issues.append(f"Visual Error: {vis_msg}")
                        
                    if issues:
                        print(f"FAIL [{', '.join(issues)}]: {node_id} (diff={difficulty}, seed={i})")
                        failures += 1
                        continue
                    
                except Exception as e:
                    print(f"ERROR: {node_id} (diff={difficulty}, seed={i}) -> {e}")
                    failures += 1
    
    print(f"\\nAudit Complete. Total: {total}, Failures: {failures}")
    pass_rate = ((total - failures) / total) * 100 if total > 0 else 0
    print(f"Pass Rate: {pass_rate:.2f}%")

if __name__ == "__main__":
    main()
