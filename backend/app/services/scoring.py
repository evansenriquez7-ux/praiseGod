import math
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
from typing import Any

def validate_math_answer(expected: Any, student_ans: str) -> bool:
    """
    Deterministic validation using SymPy solver.
    Verifies if the student_ans is mathematically equivalent to expected.
    """
    try:
        expr_solved = parse_expr(str(expected))
        ans_solved = parse_expr(str(student_ans))
        return sp.simplify(expr_solved - ans_solved) == 0
    except Exception:
        return str(expected).strip() == str(student_ans).strip()

def update_elo(student_elo: float, skill_elo: float, is_correct: bool, k_factor: float = 32.0):
    """
    Standard Elo update matchmaking formula.
    Adjusts student ELO and skill/question ELO based on performance.
    """
    expected_student = 1.0 / (1.0 + math.pow(10.0, (skill_elo - student_elo) / 400.0))
    actual_student = 1.0 if is_correct else 0.0
    
    new_student_elo = student_elo + k_factor * (actual_student - expected_student)
    
    # Skill difficulty increases on student failure, decreases on success
    expected_skill = 1.0 - expected_student
    actual_skill = 0.0 if is_correct else 1.0
    new_skill_elo = skill_elo + k_factor * (actual_skill - expected_skill)
    
    return round(new_student_elo, 1), round(new_skill_elo, 1)
