import sys
import os
import json
import random
import traceback

# Add parent directory to path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import SessionLocal
from backend.app.models import SkillNode
from backend.app import models
from backend.app import sympy_skeletons
from backend.app import subagents
import re

def check_deterministic_constraints(question_data: dict, grade: str) -> tuple[bool, str]:
    if grade != "K" and grade != 0 and grade != "0":
        return True, "No deterministic constraints for this grade."
        
    stem = question_data.get("stem", "")
    options = question_data.get("options", {})
    
    # 1. Word count & Sentence count
    # Approximate sentences by counting periods, question marks, exclamation points
    sentences = [s for s in re.split(r'[.!?]+', stem) if s.strip()]
    if len(sentences) > 2:
        return False, f"Too many sentences ({len(sentences)} > 2)."
        
    words = [w for w in re.split(r'\W+', stem) if w.strip()]
    if len(words) > 20:
        return False, f"Too many words ({len(words)} > 20)."
        
    # 2. Banned words
    banned_words = ["evaluate", "simplify", "expression", "equivalent", "determine", "algebraic", "multiplication", "division", "ratio", "proportional", "x", "y", "$"]
    
    text_to_check = stem.lower()
    for k, v in options.items():
        text_to_check += " " + str(v.get("value", "")).lower()
        
    for banned in banned_words:
        if len(banned) == 1:
            if re.search(rf'\b{re.escape(banned)}\b', text_to_check):
                return False, f"Contains banned variable/symbol '{banned}'."
        else:
            if banned in text_to_check:
                return False, f"Contains banned word '{banned}'."
                
    return True, "Passed deterministic constraints."

def is_leaf_standard(node_id: str) -> bool:
    """
    Returns True if the node is a specific leaf standard, not a parent category.
    Parent categories typically end with capital letters (e.g. K.CC.A, HSG-CO.A).
    """
    if node_id in ["K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "HS"]:
        return False
        
    dot_count = node_id.count('.')
    dash_count = node_id.count('-')
    
    if dot_count < 1 and dash_count < 1:
        return False
        
    last_char = node_id[-1]
    if last_char.isupper() and not last_char.isdigit():
        return False
        
    return True

def call_reviewer(node_id: str, description: str, grade: str, question: dict) -> dict:
    """
    Invokes Gemini to act as an independent Expert Curriculum Reviewer.
    Evaluates grade appropriateness, description match, and answer correctness.
    """
    stem = question.get("stem") or question.get("stem_template", "")
    options = question.get("options", {})
    correct_key = question.get("correct_key", "")
    correct_answer = question.get("correct_answer", "")
    math_expression = question.get("math_expression", "")
    
    # Format options for the prompt
    formatted_opts = ""
    for k, v in options.items():
        val = v.get("value") or v.get("text") or str(v)
        trap = v.get("trap_name") or ""
        trap_info = f" (Trap: {trap})" if trap else ""
        formatted_opts += f"  {k}) {val}{trap_info}\n"
        
    prompt = f"""
You are an expert K-12 Curriculum Auditor. You are auditing a practice problem generated for a student.

Standard Node ID: {node_id}
Description: {description}
Target Grade Level: {grade}

Generated Question Context:
- Math Expression / Domain: {math_expression}
- Question Stem: "{stem}"
- Options:
{formatted_opts}
- Correct Option Key: {correct_key}
- Correct Answer Expected: "{correct_answer}"

Please critically evaluate:
1. **Grade Appropriateness**:
   - For Kindergarten (Grade 0 / K):
     - **Mathematical bounds**: The math must be single-digit numbers exclusively between **0 and 10** for general arithmetic.
     - **Adding/subtracting limits**: Addition and subtraction must be **within 5** (inputs <= 5, sum <= 5, subtraction result >= 0, starting number <= 5).
     - **Counting sequences**: Can go up to **20** (e.g. "What comes after 18?").
     - **Counting by 10s**: Can go up to **90**.
     - **STRICT BANS**: Absolutely **NO algebra**, **NO variables** (like $x$ or $y$), **NO multiplication**, **NO division**, **NO fraction operators**, **NO negative numbers**.
     - **Text & Vocabulary bounds**: The reading/text of the question stem must be extremely short—**1 to 2 simple sentences** and **at most 15 to 20 words** (strictly max 20 words). It must use only **ultra-simple high-frequency CVC sight words** suitable for a 5-year-old (like "cat", "dog", "run", "ball", "blocks", "apples", "cookies").
     - **BANNED WORDS**: Absolutely **NO advanced words** like "evaluate", "simplify", "expression", "equivalent", "determine", "algebraic", "multiplication", "division", "ratio", "proportional".
     If ANY of these constraints are violated, you MUST set "is_grade_appropriate" to false and "overall_pass" to false.

   - For Grade 1: The vocabulary must be ultra-simple sight words. Reading passages must be 2-3 simple sentences (max 20-30 words). Math range: 0-20.
   - For Elementary (2-5): Simple paragraphs, multi-digit arithmetic, basic fractions.
   - For Middle/HS: High school level complexity (algebra, reading comprehension).
   Is this problem's difficulty, numbers, and language suitable for Grade {grade}?
   
2. **Description Match**:
   Does this question actually assess the skill described in the standard? ("{description}")

3. **Correctness & Distractors**:
   Is the correct answer mathematically or textually correct and unambiguous? Are the traps plausible and well-engineered?

Output a clean JSON object (no markdown formatting, no ```json tags) with this schema:
{{
  "is_grade_appropriate": true/false,
  "grade_comments": "detailed explanation of why or why not, noting exact sentence counts, word counts, vocabulary complexity, math limits, and banned concepts",
  "does_match_description": true/false,
  "description_comments": "detailed explanation of why or why not",
  "is_correct": true/false,
  "correctness_comments": "detailed explanation of why or why not",
  "overall_pass": true/false
}}
"""
    response = subagents.call_gemini_cli(prompt, temperature=0.0)
    
    response_clean = response.strip()
    if response_clean.startswith("```json"):
        response_clean = response_clean[7:]
    if response_clean.endswith("```"):
        response_clean = response_clean[:-3]
    response_clean = response_clean.strip()
    
    try:
        return json.loads(response_clean)
    except Exception as e:
        print(f"Failed to parse reviewer response: {e}. Raw response: {response}")
        return {
            "is_grade_appropriate": False,
            "grade_comments": "Reviewer failed to output valid JSON: " + str(e),
            "does_match_description": False,
            "description_comments": "Reviewer failed to output valid JSON",
            "is_correct": False,
            "correctness_comments": "Reviewer failed to output valid JSON",
            "overall_pass": False
        }

def main():
    db = SessionLocal()
    
    # Get all K Math leaf nodes
    nodes = db.query(models.SkillNode).filter(
        models.SkillNode.grade_level.in_(["0", "K"]), 
        models.SkillNode.subject.like("%Math%")
    ).all()
    
    leaf_nodes = [n for n in nodes if is_leaf_standard(n.id)]
    
    print(f"Starting targeted audit of ALL {len(leaf_nodes)} Kindergarten Math leaf standards...")
    
    audit_results = []
    
    for i, node in enumerate(leaf_nodes, 1):
        print(f"\n--- Run {i} / {len(leaf_nodes)}: Node {node.id} ---")
        try:
            # Generate skeleton
            seed = random.randint(1, 10000)
            skel = sympy_skeletons.get_question_skeleton(node.id, seed=seed, grade_level=0)
            
            # Narrate
            narrative = subagents.narrate_question_subagent(
                stem_template=skel["stem_template"],
                math_expression=skel["math_expression"],
                options=skel["options"],
                student_age=5,
                student_grade=0,
                student_interest="animals", # some generic K interest
                language="English"
            )
            
            question_data = {
                "stem": narrative["stem"],
                "options": narrative["options"],
                "correct_key": skel["correct_key"],
                "correct_answer": skel["correct_answer"],
                "math_expression": node.id
            }
            
            print(f"Generated Question for {node.id}: '{narrative['stem'][:60]}...'")
            
            # Review
            review = call_reviewer(node.id, node.description, "K", question_data)
            
            # Apply deterministic Python checks
            det_pass, det_comments = check_deterministic_constraints(question_data, "K")
            if not det_pass:
                review["overall_pass"] = False
                review["is_grade_appropriate"] = False
                review["grade_comments"] = f"🔴 [DETERMINISTIC FAIL: {det_comments}] {review.get('grade_comments', '')}"
            
            audit_results.append({
                "grade": "K",
                "subject": "Math",
                "node_id": node.id,
                "description": node.description,
                "stem": narrative["stem"],
                "options": question_data["options"],
                "correct_key": question_data["correct_key"],
                "correct_answer": question_data["correct_answer"],
                "review": review
            })
            print(f"Node {node.id} audit completed. Pass: {review['overall_pass']}")
            
        except Exception as e:
            print(f"ERROR on Node {node.id}: {e}")
            import traceback
            traceback.print_exc()
            
    db.close()
    
    # Write report
    report_path = os.path.join(os.path.dirname(__file__), "..", "data", "research", "generation_alignment_report.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w") as f:
        f.write("# Comprehensive Kindergarten Math Audit Report\n\n")
        f.write(f"This report presents a targeted audit of ALL {len(leaf_nodes)} math problems generated ")
        f.write("for a Kindergarten student across all Math standards.\n\n")
        
        f.write("## Executive Summary\n\n")
        
        total_audits = len(audit_results)
        passed_audits = sum(1 for r in audit_results if r["review"]["overall_pass"])
        pass_rate = (passed_audits / total_audits) * 100 if total_audits > 0 else 0
        
        f.write(f"- **Total Nodes Audited**: {total_audits}\n")
        f.write(f"- **Passed Reviews**: {passed_audits}\n")
        f.write(f"- **Pass Rate**: {pass_rate:.1f}%\n\n")
        
        f.write("### Summary Table\n\n")
        f.write("| Run | Node ID | Stem Preview | Grade Appropriate? | Description Match? | Correct? | Overall Pass |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(audit_results, 1):
            rev = r["review"]
            f.write(f"| {i} | {r['node_id']} | {r['stem'][:40]}... | "
                    f"{'✅ Yes' if rev['is_grade_appropriate'] else '❌ No'} | "
                    f"{'✅ Yes' if rev['does_match_description'] else '❌ No'} | "
                    f"{'✅ Yes' if rev['is_correct'] else '❌ No'} | "
                    f"{'🟢 PASS' if rev['overall_pass'] else '🔴 FAIL'} |\n")
                    
        f.write("\n---\n\n")
        f.write("## Detailed Reviews\n\n")
        
        for i, r in enumerate(audit_results, 1):
            rev = r["review"]
            f.write(f"### Node {r['node_id']}\n\n")
            f.write(f"**Standard Description**: {r['description']}\n\n")
            f.write("**Generated Question Stem**:\n")
            f.write(f"> {r['stem'].replace(chr(10), chr(10) + '> ')}\n\n")
            
            f.write("**Options**:\n")
            for k, v in r["options"].items():
                val = v.get("value") or v.get("text") or str(v)
                trap = v.get("trap_name") or ""
                trap_info = f" *(Trap: {trap})*" if trap else ""
                f.write(f"- **{k}**: {val}{trap_info}\n")
            f.write(f"\n- **Correct Answer**: {r['correct_key']} ({r['correct_answer']})\n\n")
            
            f.write("#### Reviewer Feedback\n\n")
            f.write(f"- **Grade Appropriate**: {'✅ Yes' if rev['is_grade_appropriate'] else '❌ No'}\n")
            f.write(f"  *Comments*: {rev['grade_comments']}\n")
            f.write(f"- **Description Match**: {'✅ Yes' if rev['does_match_description'] else '❌ No'}\n")
            f.write(f"  *Comments*: {rev['description_comments']}\n")
            f.write(f"- **Correct & Unambiguous**: {'✅ Yes' if rev['is_correct'] else '❌ No'}\n")
            f.write(f"  *Comments*: {rev['correctness_comments']}\n")
            f.write(f"- **Overall Verdict**: **{'🟢 PASS' if rev['overall_pass'] else '🔴 FAIL'}**\n\n")
            f.write("---\n\n")
            
    print(f"\nAudit completed! Report successfully written to {report_path}")
    print(f"Passed {passed_audits} out of {total_audits} audited nodes ({pass_rate:.1f}% pass rate).")

if __name__ == "__main__":
    main()
